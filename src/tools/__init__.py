"""
ARIA Tool Architecture package.
Provides tool registration, dispatcher execution, and safe demonstration tools.
"""

from .registry import ToolRegistry, registry
from .dispatcher import ToolDispatcher, dispatcher
from .basic import register_basic_tools

# Automatically register default safe demonstration tools on package import
register_basic_tools(registry)
