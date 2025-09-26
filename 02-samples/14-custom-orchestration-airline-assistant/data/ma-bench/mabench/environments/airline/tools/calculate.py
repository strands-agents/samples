"""Adapted from τ-bench https://arxiv.org/abs/2406.12045"""

import ast
import operator

from strands import tool
from mabench.environments.airline.data import load_data

# Safe operators for mathematical expressions
OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}

def safe_eval(node):
    """Safely evaluate mathematical expressions using AST."""
    if isinstance(node, ast.Constant):  # numbers
        return node.value
    elif isinstance(node, ast.BinOp):  # binary operations
        return OPS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # unary operations
        return OPS[type(node.op)](safe_eval(node.operand))
    else:
        raise ValueError(f"Unsupported operation: {type(node)}")

@tool
def calculate(expression: str) -> str:
    """
    Calculate the result of a mathematical expression.

    Args:
        expression: The mathematical expression to calculate, such as '2 + 2'.
                   The expression can contain numbers, operators (+, -, *, /),
                   parentheses, and spaces.

    Returns:
        The calculated result as a string, rounded to 2 decimal places,
        or an error message.
    """
    if not all(char in "0123456789+-*/(). " for char in expression):
        return "Error: invalid characters in expression"
    try:
        tree = ast.parse(expression, mode='eval')
        result = safe_eval(tree.body)
        return str(round(float(result), 2))
    except Exception as e:
        return f"Error: {e}"
