import operator
from typing import Literal

from strands import Agent, tool
from strands.multiagent.a2a import A2AServer

_OPS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "**": operator.pow,
}


@tool
def calculator(a: float, b: float, op: Literal["+", "-", "*", "/", "**"]) -> float:
    """Apply an arithmetic operator to two numbers.

    Args:
        a: Left operand.
        b: Right operand.
        op: One of "+", "-", "*", "/", "**".
    """
    return _OPS[op](a, b)


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
