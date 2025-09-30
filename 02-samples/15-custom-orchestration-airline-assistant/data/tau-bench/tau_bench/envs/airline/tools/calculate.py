# Copyright Sierra

import ast
import operator
from typing import Any, Dict
from tau_bench.envs.tool import Tool


class Calculate(Tool):
    @staticmethod
    def _safe_eval(expression: str) -> float:
        """Safely evaluate mathematical expressions using AST."""
        # Supported operations
        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        def _eval(node):
            if isinstance(node, ast.Constant):  # Numbers
                return node.value
            elif isinstance(node, ast.BinOp):  # Binary operations
                return ops[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):  # Unary operations
                return ops[type(node.op)](_eval(node.operand))
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")
        
        try:
            tree = ast.parse(expression, mode='eval')
            return _eval(tree.body)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")
    
    @staticmethod
    def invoke(data: Dict[str, Any], expression: str) -> str:
        if not all(char in "0123456789+-*/(). " for char in expression):
            return "Error: invalid characters in expression"
        try:
            result = Calculate._safe_eval(expression)
            return str(round(float(result), 2))
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "calculate",
                "description": "Calculate the result of a mathematical expression.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "The mathematical expression to calculate, such as '2 + 2'. The expression can contain numbers, operators (+, -, *, /), parentheses, and spaces.",
                        },
                    },
                    "required": ["expression"],
                },
            },
        }
