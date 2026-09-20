"""
Safe demonstration tools for ARIA architecture.
Includes status, session info, echo, and safe calculator operations.
"""

import ast
import operator
from typing import Dict, Any, Union
from .registry import ToolRegistry

def get_aria_status() -> str:
    """Return ARIA's current operational status."""
    return "ARIA systems operational. Core router and tool engine ready."

def get_current_session_info() -> Dict[str, str]:
    """Return safe, non-sensitive session metadata."""
    return {
        "assistant_name": "ARIA",
        "mode": "Online-First",
        "primary_backend": "Google Gemini 3.5 Flash-Lite",
        "status": "Active"
    }

def echo_tool(text: str, max_length: int = 500) -> str:
    """Echo input text up to a safe maximum length."""
    if not isinstance(text, str):
        raise TypeError("Input 'text' must be a string.")
    
    trimmed = text.strip()
    if len(trimmed) > max_length:
        return trimmed[:max_length] + "... (truncated)"
    return trimmed

# Supported math operators for safe calculator
_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _eval_expr(node: ast.AST) -> Union[int, float]:
    """Recursively evaluates AST nodes safely without using dangerous eval()."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_expr(node.left)
        right = _eval_expr(node.right)
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division by zero is not allowed.")
        return _OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_expr(node.operand)
        op_type = type(node.op)
        if op_type not in _OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _OPERATORS[op_type](operand)
    else:
        raise ValueError("Unsupported expression structure.")

def calculator_tool(expression: str) -> Union[int, float]:
    """Safely calculate a basic math expression using AST parsing."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression must be a non-empty string.")

    try:
        parsed = ast.parse(expression.strip(), mode='eval')
        return _eval_expr(parsed.body)
    except (SyntaxError, MemoryError):
        raise ValueError("Invalid mathematical expression.")


def register_basic_tools(registry_instance: ToolRegistry) -> None:
    """Register all default demonstration tools into a registry instance."""
    registry_instance.register("get_aria_status", "Returns ARIA's current operational status.", get_aria_status)
    registry_instance.register("get_current_session_info", "Returns safe non-sensitive session info.", get_current_session_info)
    registry_instance.register("echo_tool", "Echoes input text safely with length limiting.", echo_tool)
    registry_instance.register("calculator_tool", "Safely calculates basic math expressions.", calculator_tool)
