"""Standalone Exa provider and search service tests."""

import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from exa_provider import ExaProvider, ExaSearchError, ProviderResponse, SearchResult
from search_service import SearchBudgetExceeded, SearchService, SearchUnavailableError


class FakeProvider:
    def __init__(self, response=None, error=None, delay=0):
        self.response = response or ProviderResponse((SearchResult(
            "Example", "https://example.com", "2026-11-10", ("Useful excerpt",)
        ),), 0.25)
        self.error = error
        self.delay = delay
        self.calls = []

    def search(self, query, **kwargs):
        self.calls.append((query, kwargs))
        if self.delay:
            time.sleep(self.delay)
        if self.error:
            raise self.error
        return self.response


class TestExaProvider(unittest.TestCase):
    def test_maps_results_limits_to_five_and_selects_modes(self):
        client = SimpleNamespace(search=lambda query, **kwargs: SimpleNamespace(
            results=[SimpleNamespace(title=str(i), url=f"https://e.test/{i}",
                                     published_date="2026-11-10", highlights=["h"])
                     for i in range(8)],
            cost_dollars=SimpleNamespace(total=0.1),
        ))
        provider = ExaProvider(api_key="secret", client=client)
        result = provider.search("test", mode="economical", num_results=30)
        self.assertEqual(len(result.results), 5)
        self.assertEqual(result.results[0].published_date, "2026-11-10")
        self.assertEqual(result.cost_usd, 0.1)

    def test_missing_api_key_is_reported_without_sdk_import(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "EXA_API_KEY"):
                ExaProvider()

    def test_invalid_response_is_rejected_but_empty_results_are_valid(self):
        invalid_provider = ExaProvider(
            api_key="test-token",
            client=SimpleNamespace(search=lambda query, **kwargs: None),
        )
        with self.assertRaises(ExaSearchError):
            invalid_provider.search("invalid response")

        empty_provider = ExaProvider(
            api_key="test-token",
            client=SimpleNamespace(search=lambda query, **kwargs: SimpleNamespace(results=[])),
        )
        self.assertEqual(empty_provider.search("no matches").results, ())

    def test_all_invalid_result_items_are_rejected(self):
        provider = ExaProvider(
            api_key="test-token",
            client=SimpleNamespace(search=lambda query, **kwargs: SimpleNamespace(
                results=[SimpleNamespace(title="Missing URL", url=None)]
            )),
        )
        with self.assertRaises(ExaSearchError):
            provider.search("malformed result")


class TestSearchService(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def service(self, provider, **kwargs):
        return SearchService(
            provider,
            db_path=str(Path(self.temp_dir.name) / "search.sqlite3"),
            **kwargs,
        )

    def test_successful_search_tracks_monthly_usage(self):
        provider = FakeProvider()
        service = self.service(provider)
        result = service.search("latest example")
        self.assertEqual(result.results[0].url, "https://example.com")
        self.assertFalse(result.cached)
        self.assertEqual(service.monthly_usage()["requests"], 1)
        self.assertAlmostEqual(service.monthly_usage()["cost_usd"], 0.25)
        self.assertEqual(provider.calls[0][1]["num_results"], 5)

    def test_cache_avoids_duplicate_provider_request(self):
        provider = FakeProvider()
        service = self.service(provider)
        first = service.search("same query")
        second = service.search("  SAME   query ")
        self.assertFalse(first.cached)
        self.assertTrue(second.cached)
        self.assertEqual(len(provider.calls), 1)

    def test_invalid_response_is_not_cached_or_counted_as_usage(self):
        calls = []
        provider = ExaProvider(
            api_key="test-token",
            client=SimpleNamespace(search=lambda query, **kwargs: calls.append(query) or None),
        )
        service = self.service(provider)
        for _ in range(2):
            with self.assertRaises(SearchUnavailableError):
                service.search("malformed response")
        self.assertEqual(len(calls), 2)
        self.assertEqual(service.monthly_usage()["requests"], 0)

    def test_legitimate_empty_search_is_cached_as_success(self):
        calls = []
        provider = ExaProvider(
            api_key="test-token",
            client=SimpleNamespace(search=lambda query, **kwargs: calls.append(query)
                                   or SimpleNamespace(results=[])),
        )
        service = self.service(provider)
        first = service.search("no matches")
        second = service.search("no matches")
        self.assertEqual(first.results, ())
        self.assertFalse(first.cached)
        self.assertTrue(second.cached)
        self.assertEqual(len(calls), 1)
        self.assertEqual(service.monthly_usage()["requests"], 1)

    def test_concurrent_duplicate_queries_are_coalesced(self):
        provider = FakeProvider(delay=0.1)
        service = self.service(provider)
        results = []
        threads = [threading.Thread(target=lambda: results.append(service.search("same")))
                   for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(results), 5)
        self.assertEqual(len(provider.calls), 1)

    def test_provider_error_uses_stale_cache_then_unavailable(self):
        provider = FakeProvider()
        service = self.service(provider, cache_ttl_seconds=0, stale_if_error_seconds=60)
        service.search("cached")
        provider.error = ExaSearchError("unauthorized", 401)
        fallback = service.search("cached")
        self.assertTrue(fallback.cached)
        self.assertTrue(fallback.stale)
        with self.assertRaises(SearchUnavailableError):
            service.search("uncached")
        self.assertEqual(len(provider.calls), 3)

    def test_budget_blocks_paid_search_and_serves_valid_cache(self):
        provider = FakeProvider()
        service = self.service(provider, monthly_budget_usd=0.25)
        service.search("cached")
        self.assertTrue(service.search("cached").cached)
        with self.assertRaises(SearchBudgetExceeded):
            service.search("new query")
        self.assertEqual(len(provider.calls), 1)

    def test_unknown_cost_fails_closed_when_budget_is_configured(self):
        provider = FakeProvider(response=ProviderResponse((SearchResult(
            "Example", "https://example.com"
        ),), None))
        service = self.service(provider, monthly_budget_usd=10)
        service.search("first")
        with self.assertRaises(SearchBudgetExceeded):
            service.search("second")
        self.assertEqual(len(provider.calls), 1)

    def test_missing_api_key_reports_unavailable_without_failing_startup(self):
        with patch.dict(os.environ, {}, clear=True):
            service = SearchService(db_path=str(Path(self.temp_dir.name) / "missing.sqlite"))
            with self.assertRaises(SearchUnavailableError):
                service.search("query")

    def test_billing_auth_and_quota_errors_are_not_retried(self):
        for status_code in (401, 402, 429):
            with self.subTest(status_code=status_code):
                provider = FakeProvider(error=ExaSearchError("provider error", status_code))
                service = self.service(provider)
                with self.assertRaises(SearchUnavailableError):
                    service.search("query")
                self.assertEqual(len(provider.calls), 1)

    def test_crawl_freshness_is_separate_from_publication_date(self):
        calls = []
        client = SimpleNamespace(search=lambda query, **kwargs: calls.append(kwargs) or
                                 SimpleNamespace(results=[], cost_dollars=None))
        provider = ExaProvider(api_key="secret", client=client)
        provider.search("recent story", mode="freshness", crawl_max_age_hours=12)
        self.assertEqual(calls[0]["type"], "auto")
        self.assertEqual(calls[0]["contents"]["max_age_hours"], 12)
        self.assertNotIn("start_published_date", calls[0])


if __name__ == "__main__":
    unittest.main()
