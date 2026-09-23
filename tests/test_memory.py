"""
Unit tests for ARIA Permanent Memory architecture.
"""

import unittest
import tempfile
import time
import sys
import gc
from pathlib import Path

# Ensure src directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from memory.store import MemoryStore

class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        # Use a temporary file for isolated testing with configurable database path
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test_aria_memory.db")
        self.store = MemoryStore(db_path=self.db_path)

    def tearDown(self):
        # Force garbage collection to ensure sqlite connections are released on Windows
        del self.store
        gc.collect()
        self.temp_dir.cleanup()

    def test_store_and_get_memory(self):
        self.store.store_memory("favorite_language", "Python")
        val = self.store.get_memory("favorite_language")
        self.assertEqual(val, "Python")

    def test_get_nonexistent_memory(self):
        val = self.store.get_memory("does_not_exist")
        self.assertIsNone(val)

    def test_update_memory_and_timestamp(self):
        self.store.store_memory("theme", "dark")
        initial_val = self.store.get_memory("theme")
        self.assertEqual(initial_val, "dark")

        # Small delay to ensure timestamp difference capability
        time.sleep(0.01)

        success = self.store.update_memory("theme", "light")
        self.assertTrue(success)
        self.assertEqual(self.store.get_memory("theme"), "light")

    def test_update_nonexistent_memory(self):
        success = self.store.update_memory("ghost_key", "value")
        self.assertFalse(success)

    def test_delete_memory(self):
        self.store.store_memory("temp_key", "temp_value")
        self.assertTrue(self.store.delete_memory("temp_key"))
        self.assertIsNone(self.store.get_memory("temp_key"))

    def test_delete_nonexistent_memory(self):
        self.assertFalse(self.store.delete_memory("missing_key"))

    def test_list_memories(self):
        self.store.store_memory("key_1", "val_1")
        self.store.store_memory("key_2", "val_2")

        mems = self.store.list_memories()
        self.assertEqual(mems, {
            "key_2": "val_2",
            "key_1": "val_1"
        })

    def test_clear_all_safety_guard(self):
        self.store.store_memory("key_1", "val_1")
        
        # Without confirm=True, should raise PermissionError
        with self.assertRaises(PermissionError):
            self.store.clear_all()

        # With confirm=True, should succeed
        self.store.clear_all(confirm=True)
        self.assertEqual(len(self.store.list_memories()), 0)

    def test_invalid_inputs_raised(self):
        with self.assertRaises(ValueError):
            self.store.store_memory("", "content")

        with self.assertRaises(ValueError):
            self.store.store_memory(None, "content")

        with self.assertRaises(ValueError):
            self.store.store_memory("key", None)

if __name__ == "__main__":
    unittest.main()
