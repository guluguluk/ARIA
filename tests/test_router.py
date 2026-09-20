import unittest
import sys
from pathlib import Path

# Ensure src directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from router import route_command, aria_tool_phrases

class TestRouter(unittest.TestCase):
    def test_normal_question_returns_gemini(self):
        command = "What is the capital of France?"
        self.assertEqual(route_command(command), "GEMINI")

    def test_coding_request_returns_gemini(self):
        command = "Write a python function to calculate factorial"
        self.assertEqual(route_command(command), "GEMINI")

    def test_current_info_request_returns_gemini(self):
        command = "What are the latest space discoveries?"
        self.assertEqual(route_command(command), "GEMINI")

    def test_aria_tool_phrase_returns_aria_tool(self):
        # Temporarily configure a tool phrase for testing
        original_phrases = aria_tool_phrases.copy()
        try:
            aria_tool_phrases.clear()
            aria_tool_phrases.append("open browser")
            
            command = "Please open browser now"
            self.assertEqual(route_command(command), "ARIA_TOOL")
        finally:
            aria_tool_phrases.clear()
            aria_tool_phrases.extend(original_phrases)

    def test_unmatched_phrase_returns_gemini(self):
        original_phrases = aria_tool_phrases.copy()
        try:
            aria_tool_phrases.clear()
            aria_tool_phrases.append("open browser")
            
            command = "tell me a joke"
            self.assertEqual(route_command(command), "GEMINI")
        finally:
            aria_tool_phrases.clear()
            aria_tool_phrases.extend(original_phrases)

if __name__ == "__main__":
    unittest.main()
