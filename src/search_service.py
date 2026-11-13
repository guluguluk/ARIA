"""Cached, budget-aware Exa search service, independent of ARIA routing."""

import json
import os
import sqlite3
import threading
from concurrent.futures import Future
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from exa_provider import ExaProvider, ExaSearchError, ProviderResponse, SearchResult


class SearchUnavailableError(Exception):
    """Live search is unavailable and no acceptable cached results exist."""


class SearchBudgetExceeded(SearchUnavailableError):
    """Configured monthly budget has been reached."""


@dataclass(frozen=True)
class SearchResponse:
    results: tuple[SearchResult, ...]
    cached: bool
    stale: bool = False
    cost_usd: float | None = None


class SearchService:
    def __init__(
        self,
        provider: Any = None,
        *,
        db_path: str | None = None,
        monthly_budget_usd: float | None = None,
        cache_ttl_seconds: int = 3600,
        stale_if_error_seconds: int = 7 * 24 * 3600,
    ):
        self.provider = provider
        self.db_path = db_path or os.getenv(
            "EXA_SEARCH_DB", str(Path(__file__).resolve().parent.parent / "aria_search.db")
        )
        configured_budget = os.getenv("EXA_MONTHLY_BUDGET_USD")
        if monthly_budget_usd is None and configured_budget:
            try:
                monthly_budget_usd = float(configured_budget)
            except ValueError as error:
                raise ValueError("EXA_MONTHLY_BUDGET_USD must be a number") from error
        if monthly_budget_usd is not None and monthly_budget_usd < 0:
            raise ValueError("monthly_budget_usd must be non-negative")
        self.monthly_budget_usd = monthly_budget_usd
        self.cache_ttl_seconds = cache_ttl_seconds
        self.stale_if_error_seconds = stale_if_error_seconds
        self._lock = threading.RLock()
        self._inflight: dict[tuple[str, str, int | None, int], Future] = {}
        self._init_db()

    def search(
        self,
        query: str,
        *,
        mode: str = "economical",
        crawl_max_age_hours: int | None = None,
        num_results: int = 5,
    ) -> SearchResponse:
        query = " ".join(query.split())
        if not query:
            raise ValueError("query must not be empty")
        if mode not in {"economical", "freshness"}:
            raise ValueError("mode must be 'economical' or 'freshness'")
        count = min(max(int(num_results), 1), 5)
        key = (query.casefold(), mode, crawl_max_age_hours, count)
        cached = self._get_cache(key, max_age=self.cache_ttl_seconds)
        if cached is not None:
            return SearchResponse(cached.results[:count], True, False, cached.cost_usd)

        # Concurrent equal requests wait for the owner, then read its cache.
        while True:
            with self._lock:
                future = self._inflight.get(key)
                if future is None:
                    future = Future()
                    self._inflight[key] = future
                    owner = True
                else:
                    owner = False
            if owner:
                break
            return future.result()

        try:
            if self.provider is None:
                try:
                    self.provider = ExaProvider()
                except (ValueError, RuntimeError) as error:
                    response = self._fallback_or_raise(key, error)
                    future.set_result(response)
                    return response
            if self._budget_reached():
                error = SearchBudgetExceeded("Monthly Exa search budget has been reached")
                response = self._fallback_or_raise(key, error)
                future.set_result(response)
                return response
            try:
                provider_response = self.provider.search(
                    query, mode=mode, num_results=count,
                    crawl_max_age_hours=crawl_max_age_hours,
                )
                if not isinstance(provider_response, ProviderResponse):
                    raise ExaSearchError("Exa returned an invalid search response")
                if (not isinstance(provider_response.results, tuple)
                        or any(not isinstance(item, SearchResult) for item in provider_response.results)):
                    raise ExaSearchError("Exa returned invalid search results")
            except ExaSearchError as error:
                response = self._fallback_or_raise(key, error)
                future.set_result(response)
                return response
            response = SearchResponse(
                tuple(provider_response.results[:count]), False, False,
                provider_response.cost_usd,
            )
            self._store_success(key, response)
            future.set_result(response)
            return response
        except Exception as error:
            if not future.done():
                future.set_exception(error)
            raise
        finally:
            with self._lock:
                self._inflight.pop(key, None)

    def monthly_usage(self, month: str | None = None) -> dict[str, float | int | str]:
        month = month or datetime.now(timezone.utc).strftime("%Y-%m")
        start, end = _month_bounds(month)
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT COUNT(*) AS requests, COALESCE(SUM(cost_usd), 0) AS cost, "
                "SUM(CASE WHEN cost_usd IS NULL THEN 1 ELSE 0 END) AS unknown_cost_requests "
                "FROM exa_usage WHERE created_at >= ? AND created_at < ?",
                (start, end),
            ).fetchone()
        return {"month": month, "requests": row["requests"], "cost_usd": row["cost"],
                "unknown_cost_requests": row["unknown_cost_requests"] or 0}

    def _fallback_or_raise(self, key, cause):
        stale = self._get_cache(key, max_age=self.stale_if_error_seconds)
        if stale is not None:
            return SearchResponse(stale.results, True, True, stale.cost_usd)
        if isinstance(cause, SearchBudgetExceeded):
            raise cause
        raise SearchUnavailableError("Live search is unavailable") from cause

    def _budget_reached(self) -> bool:
        if self.monthly_budget_usd is None:
            return False
        usage = self.monthly_usage()
        return (usage["unknown_cost_requests"] > 0
                or float(usage["cost_usd"]) >= self.monthly_budget_usd)

    def _connect(self):
        connection = sqlite3.connect(self.db_path, timeout=30)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self):
        path = Path(self.db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection, connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS exa_cache (
                query_key TEXT NOT NULL, mode TEXT NOT NULL, crawl_max_age_hours INTEGER,
                result_count INTEGER NOT NULL, results_json TEXT NOT NULL,
                cost_usd REAL, created_at TEXT NOT NULL,
                PRIMARY KEY(query_key, mode, crawl_max_age_hours, result_count))""")
            connection.execute("""CREATE TABLE IF NOT EXISTS exa_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT, query_key TEXT NOT NULL,
                mode TEXT NOT NULL, result_count INTEGER NOT NULL,
                cost_usd REAL, created_at TEXT NOT NULL)""")

    def _get_cache(self, key, max_age):
        now = datetime.now(timezone.utc)
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT results_json, cost_usd, created_at FROM exa_cache "
                "WHERE query_key=? AND mode=? AND crawl_max_age_hours IS ? AND result_count=?",
                (key[0], key[1], key[2], key[3]),
            ).fetchone()
        if row is None:
            return None
        created = datetime.fromisoformat(row["created_at"])
        if now - created > timedelta(seconds=max_age):
            return None
        return SearchResponse(
            tuple(SearchResult(**{**item, "highlights": tuple(item["highlights"])})
                  for item in json.loads(row["results_json"])),
            True, False, row["cost_usd"],
        )

    def _store_success(self, key, response):
        now = datetime.now(timezone.utc).isoformat()
        serialized = json.dumps([
            {**asdict(item), "highlights": list(item.highlights)}
            for item in response.results
        ])
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "INSERT OR REPLACE INTO exa_cache "
                "(query_key, mode, crawl_max_age_hours, result_count, results_json, cost_usd, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (key[0], key[1], key[2], key[3], serialized, response.cost_usd, now),
            )
            connection.execute(
                "INSERT INTO exa_usage (query_key, mode, result_count, cost_usd, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (key[0], key[1], len(response.results), response.cost_usd, now),
            )


def _month_bounds(month: str) -> tuple[str, str]:
    try:
        start = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
    except ValueError as error:
        raise ValueError("month must use YYYY-MM format") from error
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start.isoformat(), end.isoformat()
