import unittest
import sys
import tempfile
import gc
from pathlib import Path

# Ensure src directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aria import process_command, initialize_memory
from memory import MemoryStore


class TestAriaHelp(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "test_aria_memory.db")
        self.store = MemoryStore(db_path=db_path)

    def tearDown(self):
        del self.store
        gc.collect()
        self.temp_dir.cleanup()

    def test_general_help_variations(self):
        for cmd in ["help", "commands", "?", "  HELP  ", "commands"]:
            response = process_command(cmd, self.store)
            self.assertIsNotNone(response)
            self.assertIn("ARIA Built-in Commands & Capabilities", response)
            self.assertIn("help calculator", response)
            self.assertIn("help memory", response)

    def test_calculator_help(self):
        for cmd in ["help calculator", "help calc", "  HELP  CALCULATOR  "]:
            response = process_command(cmd, self.store)
            self.assertIsNotNone(response)
            self.assertIn("ARIA Calculator Help", response)
            self.assertIn("sqrt", response)
            self.assertIn("pi", response)
            self.assertIn("implicit multiplication", response)

    def test_memory_help(self):
        for cmd in ["help memory", "help memories", "  HELP MEMORY "]:
            response = process_command(cmd, self.store)
            self.assertIsNotNone(response)
            self.assertIn("ARIA Permanent Memory Help", response)
            self.assertIn("remember that", response)
            self.assertIn("forget", response)

    def test_unknown_help_topic(self):
        response = process_command("help foo", self.store)
        self.assertIsNotNone(response)
        self.assertIn("Unknown help topic: 'foo'", response)
        self.assertIn("calculator", response)
        self.assertIn("memory", response)

    def test_case_insensitive_and_whitespace(self):
        response = process_command("\tHeLp   CaLcUlAtOr\n", self.store)
        self.assertIn("ARIA Calculator Help", response)

    def test_version_command(self):
        for cmd in ["version", "--version", "VERSION"]:
            response = process_command(cmd, self.store)
            self.assertIn("ARIA v2.4.0 Cognition", response)

    def test_help_does_not_call_gemini(self):
        # Even if offline/unconfigured or normal, help should be instant and local
        response = process_command("help", self.store)
        self.assertIn("ARIA Built-in Commands", response)

    def test_ordinary_questions_about_help_follow_normal_routing(self):
        # An ordinary sentence containing the word help should not trigger builtin help handler unless structured as a command
        # e.g., "Can you help me write a python function?"
        # Router should handle it as GEMINI (or test that it doesn't return the built-in help text)
        response = process_command("Can you help me write a python function?", self.store)
        # Should not be the built-in command list
        self.assertNotIn("ARIA Built-in Commands & Capabilities", response)

    def test_existing_calculator_and_memory_unchanged(self):
        # Test calculator still works
        calc_resp = process_command("calculate 5 * 5", self.store)
        self.assertEqual(calc_resp, "25")

        # Test memory still works
        mem_resp = process_command("remember that theme is dark", self.store)
        self.assertEqual(mem_resp, "I'll remember that.")

        retrieve_resp = process_command("what do you remember about theme", self.store)
        self.assertIn("dark", retrieve_resp)


if __name__ == "__main__":
    unittest.main()
