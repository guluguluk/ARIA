"""
Tool Dispatcher module for ARIA.
Executes registered tools safely with validated arguments and standardized output.
"""

from typing import Any, Dict, Optional
from .registry import ToolRegistry

class ToolDispatcher:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def dispatch(self, tool_name: str, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a registered tool by name with kwargs.
        Returns a structured result dictionary and catches runtime errors safely.
        """
        if kwargs is None:
            kwargs = {}

        if not isinstance(kwargs, dict):
            return {
                "success": False,
                "tool": tool_name if isinstance(tool_name, str) else "unknown",
                "result": None,
                "error": "Tool arguments must be provided as a dictionary/keyword arguments."
            }

        try:
            tool_info = self.registry.get(tool_name)
        except KeyError as e:
            return {
                "success": False,
                "tool": str(tool_name),
                "result": None,
                "error": str(e).strip("'")
            }

        func = tool_info["func"]

        try:
            result = func(**kwargs)
            return {
                "success": True,
                "tool": tool_info["name"],
                "result": result,
                "error": None
            }
        except TypeError as e:
            # Typically invalid arguments passed to tool function
            return {
                "success": False,
                "tool": tool_info["name"],
                "result": None,
                "error": f"Invalid arguments for tool '{tool_info['name']}': {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "tool": tool_info["name"],
                "result": None,
                "error": f"Tool execution failed: {str(e)}"
            }

from .registry import registry
dispatcher = ToolDispatcher(registry)
