"""Tests for Gemini response handling in the model layer."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from google.genai.errors import ClientError, ServerError

import models


class TestGeminiModel(unittest.TestCase):
    @patch("models.client.models.generate_content")
    def test_successful_response_is_returned(self, generate_content):
        generate_content.return_value = SimpleNamespace(text="Gemini response")

        response = models.ask_gemini("Hello")

        self.assertEqual(response, "Gemini response")
        generate_content.assert_called_once_with(
            model="gemini-3.5-flash-lite",
            contents="Hello",
        )

    @patch("models.client.models.generate_content")
    def test_live_search_enables_google_search_grounding(self, generate_content):
        generate_content.return_value = SimpleNamespace(text="Recent results")

        response = models.ask_gemini("Tell me the latest news", use_search=True)

        self.assertEqual(response, "Recent results")
        call = generate_content.call_args
        self.assertEqual(call.kwargs["model"], "gemini-3.5-flash-lite")
        config = call.kwargs["config"].model_dump(exclude_none=True, by_alias=True)
        self.assertEqual(config["tools"], [{"googleSearch": {}}])

    @patch("models.client.models.generate_content")
    def test_service_unavailable_returns_controlled_response(self, generate_content):
        generate_content.side_effect = ServerError(
            503,
            {"error": {"message": "high demand", "status": "UNAVAILABLE"}},
        )

        response = models.ask_gemini("Hello")

        self.assertEqual(response, models.TEMPORARY_GEMINI_ERROR_RESPONSE)
        self.assertNotIn("high demand", response)
        self.assertNotIn("Traceback", response)

    @patch("models.client.models.generate_content")
    def test_rate_limit_returns_controlled_response(self, generate_content):
        generate_content.side_effect = ClientError(
            429,
            {"error": {"message": "quota details", "status": "RESOURCE_EXHAUSTED"}},
        )

        self.assertEqual(
            models.ask_gemini("Hello"),
            models.TEMPORARY_GEMINI_ERROR_RESPONSE,
        )

    @patch("models.logger.warning")
    @patch("models.client.models.generate_content")
    def test_search_rate_limit_is_logged_for_diagnosis(self, generate_content, warning):
        generate_content.side_effect = ClientError(
            429,
            {"error": {"message": "search quota exhausted", "status": "RESOURCE_EXHAUSTED"}},
        )

        self.assertEqual(
            models.ask_gemini("Tell me the latest news", use_search=True),
            models.SEARCH_QUOTA_ERROR_RESPONSE,
        )
        warning.assert_called_once()
        self.assertEqual(warning.call_args.args[1], 429)

    @patch("models.client.models.generate_content")
    def test_non_temporary_api_error_is_not_suppressed(self, generate_content):
        error = ClientError(400, {"error": {"message": "invalid request"}})
        generate_content.side_effect = error

        with self.assertRaises(ClientError) as raised:
            models.ask_gemini("Hello")

        self.assertIs(raised.exception, error)


if __name__ == "__main__":
    unittest.main()
