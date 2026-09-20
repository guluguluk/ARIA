"""
Tool Registry module for ARIA.
Manages tool definitions, validation, and retrieval without executing them.
"""

from typing import Callable, Dict, Any

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, description: str, func: Callable[..., Any]) -> None:
        """
        Register a tool with a unique name, description, and executable function.
        Rejects duplicates and invalid definitions.
        """
        if not name or not isinstance(name, str):
            raise ValueError("Tool name must be a non-empty string.")
        
        cleaned_name = name.strip().lower()
        
        if cleaned_name in self._tools:
            raise ValueError(f"Tool '{cleaned_name}' is already registered.")
        
        if not description or not isinstance(description, str):
            raise ValueError(f"Tool '{name}' must have a valid string description.")
        
        if not callable(func):
            raise ValueError(f"Tool '{name}' function must be callable.")

        self._tools[cleaned_name] = {
            "name": cleaned_name,
            "description": description.strip(),
            "func": func
        }

    def get(self, name: str) -> Dict[str, Any]:
        """
        Retrieve a registered tool definition by name.
        Raises KeyError if the tool does not exist.
        """
        if not name or not isinstance(name, str):
            raise KeyError(f"Invalid tool name: {name}")
        
        cleaned_name = name.strip().lower()
        if cleaned_name not in self._tools:
            raise KeyError(f"Tool '{cleaned_name}' not found in registry.")
        
        return self._tools[cleaned_name]

    def list_tools(self) -> Dict[str, str]:
        """
        Return a dictionary mapping tool names to their descriptions.
        """
        return {name: info["description"] for name, info in self._tools.items()}

    def clear(self) -> None:
        """
        Clear all registered tools (primarily for testing).
        """
        self._tools.clear()


# Global tool registry instance
registry = ToolRegistry()
