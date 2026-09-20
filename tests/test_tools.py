"""
Unit tests for ARIA tool architecture (Registry, Dispatcher, and Basic Tools).
"""

import unittest
import sys
from pathlib import Path

# Ensure src directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tools.registry import ToolRegistry
from tools.dispatcher import ToolDispatcher
from tools.basic import (
    get_aria_status,
    get_current_session_info,
    echo_tool,
    calculator_tool,
    register_basic_tools
)

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()

    def test_tool_registration_and_lookup(self):
        def dummy_func():
            return "ok"

        self.registry.register("test_tool", "A test description", dummy_func)
        tool_info = self.registry.get("test_tool")
        
        self.assertEqual(tool_info["name"], "test_tool")
        self.assertEqual(tool_info["description"], "A test description")
        self.assertEqual(tool_info["func"](), "ok")

    def test_duplicate_registration_rejected(self):
        def dummy_func():
            return "ok"

        self.registry.register("tool_a", "desc", dummy_func)
        with self.assertRaises(ValueError):
            self.registry.register("TOOL_A", "duplicate desc", dummy_func)

    def test_invalid_definitions_rejected(self):
        def dummy_func():
            return "ok"

        # Empty name
        with self.assertRaises(ValueError):
            self.registry.register("", "desc", dummy_func)

        # Invalid name type
        with self.assertRaises(ValueError):
            self.registry.register(None, "desc", dummy_func)

        # Invalid description
        with self.assertRaises(ValueError):
            self.registry.register("tool_b", "", dummy_func)

        # Non-callable function
        with self.assertRaises(ValueError):
            self.registry.register("tool_c", "desc", "not_a_function")

    def test_tool_listing(self):
        self.registry.register("tool_1", "Desc 1", lambda: None)
        self.registry.register("tool_2", "Desc 2", lambda: None)
        
        listings = self.registry.list_tools()
        self.assertEqual(listings, {
            "tool_1": "Desc 1",
            "tool_2": "Desc 2"
        })

    def test_clear_registry(self):
        self.registry.register("tool_1", "Desc 1", lambda: None)
        self.registry.clear()
        self.assertEqual(len(self.registry.list_tools()), 0)


class TestToolDispatcher(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.dispatcher = ToolDispatcher(self.registry)

    def test_successful_execution(self):
        self.registry.register("add_two", "Adds two numbers", lambda a, b: a + b)
        response = self.dispatcher.dispatch("add_two", {"a": 3, "b": 5})

        self.assertTrue(response["success"])
        self.assertEqual(response["tool"], "add_two")
        self.assertEqual(response["result"], 8)
        self.assertIsNone(response["error"])

    def test_unknown_tool_handling(self):
        response = self.dispatcher.dispatch("nonexistent_tool", {})
        
        self.assertFalse(response["success"])
        self.assertEqual(response["tool"], "nonexistent_tool")
        self.assertIsNone(response["result"])
        self.assertIn("not found", response["error"].lower())

    def test_invalid_arguments_handling(self):
        self.registry.register("greet", "Says hello", lambda name: f"Hello {name}")
        # Missing required argument 'name'
        response = self.dispatcher.dispatch("greet", {})

        self.assertFalse(response["success"])
        self.assertEqual(response["tool"], "greet")
        self.assertIsNone(response["result"])
        self.assertIsNotNone(response["error"])

    def test_runtime_error_handling(self):
        def bad_tool():
            raise RuntimeError("Database connection failed")

        self.registry.register("fail_tool", "Fails", bad_tool)
        response = self.dispatcher.dispatch("fail_tool", {})

        self.assertFalse(response["success"])
        self.assertEqual(response["tool"], "fail_tool")
        self.assertIsNone(response["result"])
        self.assertIn("Tool execution failed", response["error"])


class TestBasicTools(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        register_basic_tools(self.registry)
        self.dispatcher = ToolDispatcher(self.registry)

    def test_get_aria_status(self):
        res = self.dispatcher.dispatch("get_aria_status")
        self.assertTrue(res["success"])
        self.assertIn("operational", res["result"])

    def test_get_current_session_info(self):
        res = self.dispatcher.dispatch("get_current_session_info")
        self.assertTrue(res["success"])
        self.assertEqual(res["result"]["assistant_name"], "ARIA")
        self.assertEqual(res["result"]["mode"], "Online-First")

    def test_echo_tool_valid(self):
        res = self.dispatcher.dispatch("echo_tool", {"text": "Hello ARIA"})
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], "Hello ARIA")

    def test_echo_tool_truncation(self):
        long_text = "A" * 600
        res = self.dispatcher.dispatch("echo_tool", {"text": long_text, "max_length": 10})
        self.assertTrue(res["success"])
        self.assertTrue(res["result"].endswith("... (truncated)"))
        self.assertEqual(len(res["result"]), 25) # 10 chars + "... (truncated)" (15 chars) = 25

    def test_calculator_tool_valid(self):
        res = self.dispatcher.dispatch("calculator_tool", {"expression": "2 + 3 * 4"})
        self.assertTrue(res["success"])
        self.assertEqual(res["result"], 14)

    def test_calculator_tool_division_by_zero(self):
        res = self.dispatcher.dispatch("calculator_tool", {"expression": "10 / 0"})
        self.assertFalse(res["success"])
        self.assertIn("Division by zero", res["error"])

    def test_calculator_tool_invalid_syntax(self):
        res = self.dispatcher.dispatch("calculator_tool", {"expression": "import os"})
        self.assertFalse(res["success"])
        self.assertIn("Invalid mathematical expression", res["error"])


if __name__ == "__main__":
    unittest.main()
