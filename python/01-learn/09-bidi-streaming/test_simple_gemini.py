"""Google Gemini Live CLI Test - Use headset (no echo cancellation)
Setup: export GOOGLE_API_KEY=your-key
"""

import ast
import operator

import asyncio
import os

from strands.experimental.bidi.agent import BidiAgent
from strands import tool
from strands.experimental.bidi.io.audio import BidiAudioIO
from strands.experimental.bidi.io.text import BidiTextIO
from strands.experimental.bidi.models.gemini_live import BidiGeminiLiveModel

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

async def main():
    audio_config={"input_sample_rate": 16000, "output_sample_rate": 24000}
    audio_io = BidiAudioIO(audio_config=audio_config)
    text_io = BidiTextIO()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY required")

    model = BidiGeminiLiveModel(client_config={"api_key": api_key})

    agent = BidiAgent(model=model, tools=[calculator])
    print("Gemini Live - Try: 'What is 25 times 8?'")
    await agent.run(inputs=[audio_io.input()], outputs=[audio_io.output(), text_io.output()])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEnded")
    except Exception as e:
        print(f"Error: {e}")