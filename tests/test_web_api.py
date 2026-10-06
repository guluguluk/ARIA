"""Tests for the local FastAPI web boundary."""

import sys
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi.testclient import TestClient

import aria
import web_api


class TestWebApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(web_api.app)

    def make_core(self, response="ARIA response"):
        core = SimpleNamespace(conversation=[])
        core.process_command = Mock(return_value=response)
        return core

    def test_health_and_static_ui_do_not_load_core(self):
        with patch.object(web_api, "_load_core", side_effect=AssertionError):
            health = self.client.get("/api/health")
            page = self.client.get("/")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok"})
        self.assertEqual(page.status_code, 200)
        self.assertIn("ARIA | Chat", page.text)
        self.assertEqual(self.client.get("/app.js").status_code, 200)

    def test_valid_request_uses_existing_core_and_records_complete_turn(self):
        core = self.make_core("Hello from ARIA")

        with patch.object(web_api, "_load_core", return_value=core):
            response = self.client.post("/api/chat", json={"message": "Hello"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "Hello from ARIA"})
        core.process_command.assert_called_once_with("Hello")
        self.assertEqual(
            core.conversation,
            [
                {"role": "user", "message": "Hello"},
                {"role": "aria", "message": "Hello from ARIA"},
            ],
        )

    def test_exit_and_quit_cannot_reach_core(self):
        core = self.make_core()

        with patch.object(web_api, "_load_core", return_value=core):
            for command in ("exit", "quit", " EXIT "):
                with self.subTest(command=command):
                    response = self.client.post(
                        "/api/chat", json={"message": command}
                    )
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(
                        response.json()["error"]["code"], "command_unavailable"
                    )

        core.process_command.assert_not_called()
        self.assertEqual(core.conversation, [])

    def test_missing_gemini_configuration_is_sanitized(self):
        with patch.object(
            web_api.importlib,
            "import_module",
            side_effect=ValueError(
                "GEMINI_API_KEY was not found. Add it to src/.env."
            ),
        ):
            self.assertEqual(self.client.get("/api/health").status_code, 200)
            self.assertEqual(self.client.get("/").status_code, 200)
            response = self.client.post(
                "/api/chat", json={"message": "Tell me a joke"}
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["error"]["code"], "backend_not_configured"
        )
        self.assertNotIn("GEMINI_API_KEY", response.text)
        self.assertNotIn(".env", response.text)
        self.assertNotIn("Users", response.text)

    def test_invalid_requests_have_safe_validation_responses(self):
        oversized_message = "private-message-marker " * 300

        for payload in ({"message": "   "}, {"message": oversized_message}, {}):
            with self.subTest(payload=tuple(payload)):
                response = self.client.post("/api/chat", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(
                    response.json()["error"]["code"], "invalid_request"
                )
                self.assertNotIn("private-message-marker", response.text)

    def test_temporary_gemini_failure_is_a_safe_503(self):
        core = self.make_core(
            "Gemini is temporarily unavailable right now. Please try again."
        )

        with (
            patch.object(web_api, "_load_core", return_value=core),
            patch.object(web_api, "_is_temporary_gemini_failure", return_value=True),
        ):
            response = self.client.post("/api/chat", json={"message": "Hello"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "gemini_unavailable")
        self.assertNotIn("SDK", response.text)
        self.assertNotIn("traceback", response.text.lower())

    def test_concurrent_requests_are_serialized_as_whole_turns(self):
        active_calls = 0
        maximum_active_calls = 0
        state_guard = threading.Lock()

        def process_command(message):
            nonlocal active_calls, maximum_active_calls
            with state_guard:
                active_calls += 1
                maximum_active_calls = max(maximum_active_calls, active_calls)
            time.sleep(0.03)
            with state_guard:
                active_calls -= 1
            return f"reply to {message}"

        core = SimpleNamespace(conversation=[], process_command=process_command)
        with ThreadPoolExecutor(max_workers=2) as executor:
            first = executor.submit(web_api._process_turn, core, "first")
            second = executor.submit(web_api._process_turn, core, "second")

        self.assertEqual(
            {first.result(), second.result()},
            {"reply to first", "reply to second"},
        )
        self.assertEqual(maximum_active_calls, 1)
        self.assertEqual(
            [entry["role"] for entry in core.conversation],
            ["user", "aria", "user", "aria"],
        )

    def test_core_exception_does_not_leak_details_or_leave_partial_turn(self):
        core = self.make_core()
        core.process_command.side_effect = RuntimeError(
            "C:\\private\\path\\secret-internal-detail"
        )
        client = TestClient(web_api.app, raise_server_exceptions=False)

        with patch.object(web_api, "_load_core", return_value=core):
            response = client.post("/api/chat", json={"message": "Hello"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["error"]["code"], "internal_error"
        )
        self.assertIn("ARIA could not complete this request", response.text)
        self.assertNotIn("private", response.text)
        self.assertNotIn("secret-internal-detail", response.text)
        self.assertEqual(core.conversation, [])

    def test_calculator_request_returns_result_via_api(self):
        aria.conversation = []
        with (
            patch.object(web_api, "_load_core", return_value=aria),
            patch.object(aria, "ask_gemini", return_value="unused") as ask_gemini,
        ):
            response = self.client.post(
                "/api/chat", json={"message": "calculate 12 * (3 + 4)"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "84"})
        ask_gemini.assert_not_called()

    def test_invalid_calculator_request_returns_controlled_error_via_api(self):
        aria.conversation = []
        with (
            patch.object(web_api, "_load_core", return_value=aria),
            patch.object(aria, "ask_gemini", return_value="unused") as ask_gemini,
        ):
            response = self.client.post(
                "/api/chat", json={"message": "calculate import os"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"reply": "Tool execution failed: Invalid mathematical expression."},
        )
        ask_gemini.assert_not_called()

    def test_ordinary_api_request_uses_gemini_path(self):
        aria.conversation = []
        with (
            patch.object(web_api, "_load_core", return_value=aria),
            patch.object(aria, "ask_gemini", return_value="Gemini answer") as ask_gemini,
        ):
            response = self.client.post(
                "/api/chat", json={"message": "Tell me a short joke"}
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"reply": "Gemini answer"})
        ask_gemini.assert_called_once()


if __name__ == "__main__":
    unittest.main()