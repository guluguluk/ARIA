"""Tests for ARIA's declared runtime capabilities and local answers."""

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from capabilities import answer_capability_question, build_runtime_capability_context


class TestRuntimeCapabilities(unittest.TestCase):
    def test_capability_context_distinguishes_api_from_live_retrieval(self):
        context = build_runtime_capability_context()

        self.assertIn("Gemini API", context)
        self.assertIn("does not provide general web access", context)
        self.assertIn("Live web search: unavailable", context)
        self.assertIn("Live news/current-event retrieval: unavailable", context)
        self.assertIn("knowledge cutoff is not verified", context)
        self.assertIn("Local calculator: available", context)
        self.assertIn("SQLite", context)
        self.assertIn("host system clock", context)
        self.assertIn("not supplied to Gemini", context)
        self.assertIn("do not guess a timestamp", context)
        self.assertNotIn("API key", context)

    def test_direct_realtime_capability_questions_get_truthful_local_answer(self):
        for question in (
            "Are you up to date?",
            "Do you have real-time information?",
            "Are you aware of real time information?",
        ):
            with self.subTest(question=question):
                answer = answer_capability_question(question)
                self.assertIn("no live web search", answer)
                self.assertIn("may be out of date", answer)

    def test_direct_date_questions_name_host_clock_and_timezone(self):
        now = datetime(2026, 10, 3, 12, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))

        answer = answer_capability_question("How do you know today's date?", now)

        self.assertIn("2026-10-03", answer)
        self.assertIn("host system clock", answer)
        self.assertIn("UTC+05:30", answer)
        self.assertIn("not supplied by Gemini", answer)

    def test_explicit_news_requests_are_not_answered_as_retrieved_facts(self):
        for question in (
            "What's today's news?",
            "Yesterday's international news",
            "What happened yesterday in India?",
            "What happened yesterday in India and internationally?",
            "Give me yesterday's international and India news.",
        ):
            with self.subTest(question=question):
                answer = answer_capability_question(question)
                self.assertIn("cannot verify current events", answer)
                self.assertIn("no live web or news retrieval", answer)

    def test_unrelated_questions_are_not_intercepted(self):
        self.assertIsNone(answer_capability_question("Explain photosynthesis."))
        self.assertIsNone(answer_capability_question("What is Gemini?"))


if __name__ == "__main__":
    unittest.main()
