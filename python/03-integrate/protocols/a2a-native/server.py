import ast
import operator

from strands import Agent, tool

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    """Evaluate an arithmetic AST node, rejecting anything that is not arithmetic."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        base, exponent = _eval(node.left), _eval(node.right)
        if abs(exponent) > 64:
            raise ValueError(f"exponent too large: {exponent}")
        return base**exponent
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


@tool
def calculator(expression: str) -> str:
    """Evaluate a numeric arithmetic expression using + - * / ** and parentheses.

    Functions, names, and comparisons are not supported; ** exponents are capped.

    Args:
        expression: The arithmetic expression to evaluate.
    """
    return str(_eval(ast.parse(expression, mode="eval").body))

from strands.multiagent.a2a import A2AServer

# Create a Strands agent with calculator tool
strands_agent = Agent(
    name="Calculator Agent",
    description="A calculator agent that can perform basic arithmetic operations.",
    tools=[calculator],
    callback_handler=None,
)

# Create A2A server
a2a_server = A2AServer(agent=strands_agent)

# Start the server
a2a_server.serve()
