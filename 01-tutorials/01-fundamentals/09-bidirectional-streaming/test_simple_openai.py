"""OpenAI Realtime CLI Test - Use headset (no echo cancellation)
Setup: export OPENAI_API_KEY=your-key
"""

import asyncio

from strands.experimental.bidi.agent import BidiAgent
from strands.experimental.bidi.io.audio import BidiAudioIO
from strands.experimental.bidi.io.text import BidiTextIO
from strands.experimental.bidi.models.openai_realtime import BidiOpenAIRealtimeModel
from strands_tools import calculator


async def main():
    audio_config={"input_sample_rate": 24000, "output_sample_rate": 24000}
    audio_io = BidiAudioIO(audio_config=audio_config)
    text_io = BidiTextIO()

    model = BidiOpenAIRealtimeModel()

    agent = BidiAgent(model=model, tools=[calculator])
    print("OpenAI Realtime - Try: 'What is 25 times 8?'")
    await agent.run(inputs=[audio_io.input()], outputs=[audio_io.output(), text_io.output()])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEnded")
    except Exception as e:
        print(f"Error: {e}")