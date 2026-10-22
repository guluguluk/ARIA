"""
Unit tests for ARIA v2.5.0 Diagnostics feature.
"""

import unittest
import sys
import tempfile
import gc
from pathlib import Path

# Ensure src directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aria import process_command, build_diagnostics_report
from memory import MemoryStore
from tools.registry import registry


class TestDiagnostics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "test_diagnostics.db")
        self.store = MemoryStore(db_path=db_path)

    def tearDown(self):
        del self.store
        gc.collect()
        self.temp_dir.cleanup()

    def test_diagnostics_command_aliases_and_casing(self):
        for cmd in ["diagnostics", "diagnostic", "  DIAGNOSTICS  ", "\tdiagnostic\n"]:
            response = process_command(cmd, self.store)
            self.assertIsNotNone(response)
            self.assertIn("ARIA System Diagnostics & Health:", response)
            self.assertIn("ARIA v2.5.0 Diagnostics", response)

    def test_memory_count_in_diagnostics(self):
        # Initially 0 memories
        resp_0 = process_command("diagnostics", self.store)
        self.assertIn("0 stored memories", resp_0)

        # Store memories
        self.store.store_memory("key1", "value1")
        self.store.store_memory("key2", "value2")

        resp_2 = process_command("diagnostics", self.store)
        self.assertIn("2 stored memories", resp_2)

    def test_dynamic_tool_count_in_diagnostics(self):
        resp = process_command("diagnostics", self.store)
        tool_count = len(registry.list_tools())
        self.assertIn(f"{tool_count} registered tools", resp)

    def test_backend_status_reporting(self):
        resp = process_command("diagnostics", self.store)
        # Should report either configured or not configured without exposing secret key
        self.assertTrue(
            "Configured" in resp or "Not configured" in resp
        )
        self.assertNotIn("GEMINI_API_KEY", resp) # ensure raw key value is never exposed

    def test_unavailable_store_graceful_handling(self):
        # Pass store=None or a closed/broken store scenario if applicable
        resp = build_diagnostics_report(store=None)
        self.assertIn("ARIA System Diagnostics & Health:", resp)
        self.assertTrue("Inactive" in resp or "Unavailable" in resp)

    def test_help_diagnostics(self):
        for cmd in ["help diagnostics", "help diagnostic", "  HELP  DIAGNOSTICS  "]:
            response = process_command(cmd, self.store)
            self.assertIsNotNone(response)
            self.assertIn("ARIA Diagnostics Help", response)
            self.assertIn("diagnostics", response)

    def test_general_help_includes_diagnostics(self):
        response = process_command("help", self.store)
        self.assertIn("diagnostics, diagnostic", response)
        self.assertIn("help diagnostics", response)

    def test_unknown_help_topic_includes_diagnostics(self):
        response = process_command("help unknown_topic", self.store)
        self.assertIn("diagnostics", response)
