"""Google Gemini Live CLI Test - Use headset (no echo cancellation)
Setup: export GOOGLE_API_KEY=your-key
"""

import asyncio
import os

from strands.experimental.bidi.agent import BidiAgent
from strands.experimental.bidi.io.audio import BidiAudioIO
from strands.experimental.bidi.io.text import BidiTextIO
from strands.experimental.bidi.models.gemini_live import BidiGeminiLiveModel
from strands_tools import calculator


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