"""Thin Exa SDK adapter. This module has no dependency on ARIA or Gemini."""

import os
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Any
from urllib.parse import urlsplit


class ExaSearchError(Exception):
    """Sanitized provider failure, with an optional HTTP status code."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    published_date: str | None = None
    highlights: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderResponse:
    results: tuple[SearchResult, ...]
    cost_usd: float | None = None


class ExaProvider:
    """Exa search adapter using backend-only ``EXA_API_KEY`` configuration."""

    def __init__(self, api_key: str | None = None, client: Any = None):
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        if not self.api_key:
            raise ValueError("EXA_API_KEY is not configured")
        if client is None:
            try:
                from exa_py import Exa
            except ImportError as error:
                raise RuntimeError("exa-py is required to use Exa search") from error
            client = Exa(api_key=self.api_key)
        self.client = client

    def search(
        self,
        query: str,
        *,
        mode: str = "economical",
        num_results: int = 5,
        crawl_max_age_hours: int | None = None,
    ) -> ProviderResponse:
        if mode not in {"economical", "freshness"}:
            raise ValueError("mode must be 'economical' or 'freshness'")
        options: dict[str, Any] = {
            "type": "lite" if mode == "economical" else "auto",
            "num_results": min(max(int(num_results), 1), 5),
            "contents": {"highlights": True},
        }
        # Crawl freshness controls extraction freshness; publication date remains
        # the result's independent published_date metadata.
        if crawl_max_age_hours is not None:
            if crawl_max_age_hours < 0:
                raise ValueError("crawl_max_age_hours must be non-negative")
            options["contents"]["max_age_hours"] = crawl_max_age_hours

        try:
            response = self.client.search(query, **options)
        except Exception as error:
            status_code = getattr(error, "status_code", None) or getattr(error, "code", None)
            # Deliberately do not retry: auth, billing, quota and transport errors
            # are handled by the search service's cache/fallback policy.
            raise ExaSearchError("Exa search request failed", status_code) from error

        raw_results = _field(response, "results")
        if not isinstance(raw_results, Sequence) or isinstance(raw_results, (str, bytes)):
            raise ExaSearchError("Exa returned an invalid search response")

        results = []
        invalid_items = 0
        for item in raw_results:
            url = _field(item, "url")
            if not isinstance(url, str) or not _valid_http_url(url):
                invalid_items += 1
                continue
            title = _field(item, "title")
            published_date = _field(item, "published_date") or _field(item, "publishedDate")
            highlights = _field(item, "highlights")
            if (title is not None and not isinstance(title, str)) or (
                published_date is not None and not isinstance(published_date, str)
            ):
                invalid_items += 1
                continue
            if highlights is None:
                highlights = ()
            if isinstance(highlights, str):
                highlights = (highlights,)
            if not isinstance(highlights, Sequence) or isinstance(highlights, (bytes, bytearray)):
                invalid_items += 1
                continue
            if any(not isinstance(value, str) for value in highlights):
                invalid_items += 1
                continue
            results.append(SearchResult(
                title=title or url,
                url=url,
                published_date=published_date,
                highlights=tuple(value for value in highlights if value),
            ))
        if raw_results and invalid_items == len(raw_results):
            raise ExaSearchError("Exa returned invalid search results")

        cost = _field(response, "cost_dollars")
        if cost is None:
            cost = _field(response, "costDollars")
        if isinstance(cost, dict):
            cost = cost.get("total")
        elif cost is not None and not isinstance(cost, (int, float)):
            cost = _field(cost, "total")
        try:
            cost = float(cost) if cost is not None else None
        except (TypeError, ValueError):
            raise ExaSearchError("Exa returned an invalid search cost") from None
        if cost is not None and (cost < 0 or cost != cost or cost == float("inf")):
            raise ExaSearchError("Exa returned an invalid search cost")
        return ProviderResponse(tuple(results[:5]), cost)


def _field(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _valid_http_url(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False
