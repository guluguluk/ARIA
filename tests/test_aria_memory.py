"""Integration tests for ARIA Core permanent-memory commands."""

import sys
import tempfile
import unittest
import gc
import io
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from google.genai.errors import ServerError

import aria
from memory import MemoryStore


class TestAriaMemoryCommands(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = str(Path(self.temp_dir.name) / "test_aria_memory.db")
        self.store = MemoryStore(db_path=db_path)

    def tearDown(self):
        del self.store
        gc.collect()
        self.temp_dir.cleanup()

    def test_remember_command_stores_memory(self):
        response = aria.process_command(
            "remember that my favorite game is RDR2", self.store
        )

        self.assertEqual(response, "I'll remember that.")
        self.assertEqual(self.store.get_memory("my favorite game"), "RDR2")

    def test_remember_command_updates_existing_key(self):
        aria.process_command("remember that favorite_game is RDR2", self.store)

        response = aria.process_command(
            "remember that favorite_game is Minecraft", self.store
        )

        self.assertEqual(response, "I'll remember that.")
        self.assertEqual(self.store.list_memories(), {"favorite_game": "Minecraft"})

    def test_retrieve_command_returns_stored_memory(self):
        self.store.store_memory("my favorite game", "RDR2")

        response = aria.process_command(
            "what do you remember about my favorite game?", self.store
        )

        self.assertEqual(response, "I remember that my favorite game is RDR2.")

    def test_retrieve_exact_underscore_key(self):
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command(
            "what do you remember about favorite_game", self.store
        )

        self.assertEqual(response, "I remember that favorite_game is RDR2.")

    def test_retrieve_space_and_underscore_equivalents(self):
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command(
            "what do you remember about favorite game", self.store
        )

        self.assertEqual(response, "I remember that favorite game is RDR2.")

    def test_retrieve_without_my_prefix(self):
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command(
            "what do you remember about my favorite game?", self.store
        )

        self.assertEqual(response, "I remember that my favorite game is RDR2.")

    def test_retrieve_key_is_case_insensitive(self):
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command(
            "WHAT DO YOU REMEMBER ABOUT FAVORITE GAME?", self.store
        )

        self.assertEqual(response, "I remember that favorite game is RDR2.")

    def test_unrelated_keys_remain_separate(self):
        self.store.store_memory("favorite_game", "RDR2")
        self.store.store_memory("favorite_color", "blue")

        response = aria.process_command(
            "what do you remember about favorite color", self.store
        )

        self.assertEqual(response, "I remember that favorite color is blue.")

    def test_forget_uses_key_equivalents(self):
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command("forget my favorite game", self.store)

        self.assertEqual(response, "I forgot that memory.")
        self.assertIsNone(self.store.get_memory("favorite_game"))

    def test_forget_command_removes_memory(self):
        self.store.store_memory("my favorite game", "RDR2")

        response = aria.process_command("forget my favorite game", self.store)

        self.assertEqual(response, "I forgot that memory.")
        self.assertIsNone(self.store.get_memory("my favorite game"))

    def test_forget_equivalent_key_form(self):
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command("forget my favorite game", self.store)

        self.assertEqual(response, "I forgot that memory.")
        self.assertEqual(self.store.list_memories(), {})

    def test_forget_missing_memory_is_clear(self):
        response = aria.process_command("forget unknown_key", self.store)

        self.assertEqual(response, "I don't have a memory for unknown_key.")

    def test_list_command_returns_stored_memories(self):
        self.store.store_memory("favorite_language", "Python")
        self.store.store_memory("favorite_game", "RDR2")

        response = aria.process_command("what do you remember", self.store)

        self.assertEqual(
            response,
            "I remember:\n- favorite_game: RDR2\n- favorite_language: Python",
        )

    def test_malformed_remember_commands_are_deterministic(self):
        self.assertEqual(
            aria.process_command("remember", self.store),
            "Please use: remember that <key> is <content>.",
        )
        self.assertEqual(
            aria.process_command("remember that", self.store),
            "Please use: remember that <key> is <content>.",
        )
        self.assertEqual(
            aria.process_command("remember that favorite_game is", self.store),
            "Please provide memory content after 'is'.",
        )

    def test_malformed_forget_command_is_deterministic(self):
        self.assertEqual(
            aria.process_command("forget", self.store),
            "Please provide a memory key after 'forget'.",
        )

    @patch("aria.ask_gemini", return_value="Quantum entanglement explained.")
    def test_normal_conversation_does_not_store_memory(self, _mock_ask_gemini):
        response = aria.process_command("Explain quantum entanglement.", self.store)

        self.assertEqual(response, "Quantum entanglement explained.")
        self.assertEqual(self.store.list_memories(), {})

    @patch("models.client.models.generate_content")
    def test_gemini_failure_returns_safe_response(self, generate_content):
        generate_content.side_effect = ServerError(
            503,
            {
                "error": {
                    "message": "high demand at C:\\private\\path; API key=secret",
                    "status": "UNAVAILABLE",
                }
            },
        )

        response = aria.process_command("Explain quantum entanglement.", self.store)

        self.assertEqual(
            response,
            "Gemini is temporarily unavailable right now. Please try again.",
        )
        self.assertNotIn("Traceback", response)
        self.assertNotIn("secret", response)
        self.assertNotIn("C:\\private\\path", response)

    @patch("models.client.models.generate_content")
    @patch("aria.initialize_memory")
    @patch("builtins.input", side_effect=["Explain quantum entanglement.", "status", "exit"])
    def test_main_continues_after_gemini_failure(
        self, _mock_input, _mock_initialize_memory, generate_content
    ):
        generate_content.side_effect = ServerError(
            503,
            {"error": {"message": "internal SDK details", "status": "UNAVAILABLE"}},
        )
        output = io.StringIO()
        conversation_length = len(aria.conversation)
        self.addCleanup(aria.conversation.__delitem__, slice(conversation_length, None))

        with redirect_stdout(output):
            aria.main()

        displayed = output.getvalue()
        self.assertIn("Gemini is temporarily unavailable right now.", displayed)
        self.assertIn("All systems are operational.", displayed)
        self.assertIn("Goodbye!", displayed)
        self.assertNotIn("Traceback", displayed)
        self.assertNotIn("internal SDK details", displayed)
        generate_content.assert_called_once()

    @patch("aria.ask_gemini", return_value="That is not an explicit memory command.")
    def test_ambiguous_commands_do_not_modify_memory(self, _mock_ask_gemini):
        response = aria.process_command(
            "Please remember my favorite game is RDR2", self.store
        )

        self.assertEqual(response, "That is not an explicit memory command.")
        self.assertEqual(self.store.list_memories(), {})

    @patch("aria.ask_gemini", return_value="Quantum entanglement explained.")
    def test_normal_remember_sentence_does_not_modify_memory(self, _mock_ask_gemini):
        response = aria.process_command(
            "Please remember to explain quantum entanglement later.", self.store
        )

        self.assertEqual(response, "Quantum entanglement explained.")
        self.assertEqual(self.store.list_memories(), {})


if __name__ == "__main__":
    unittest.main()