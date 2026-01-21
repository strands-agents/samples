"""AWS Nova Sonic CLI Test - Use headset to avoid feedback (no echo cancellation)"""

import asyncio

from strands.experimental.bidi.agent import BidiAgent
from strands.experimental.bidi.io.audio import BidiAudioIO
from strands.experimental.bidi.io.text import BidiTextIO
from strands.experimental.bidi.models.nova_sonic import BidiNovaSonicModel
from strands_tools import calculator


async def main():
    audio_config = {}
    audio_io = BidiAudioIO(audio_config=audio_config)
    text_io = BidiTextIO()

    model = BidiNovaSonicModel(
        region="us-east-1",
        model_id="amazon.nova-2-sonic-v1:0",
        provider_config={
            "audio": {"input_sample_rate": 16000, "output_sample_rate": 16000, "voice": "matthew"},
            "turn_detection": {
                "endpointingSensitivity": "HIGH" # HIGH, MEDIUM, LOW
            }
        },
        tools=[calculator],
    )

    agent = BidiAgent(model=model, tools=[calculator])
    print("Nova Sonic - Try: 'What is 25 times 8?'")
    await agent.run(inputs=[audio_io.input()], outputs=[audio_io.output(), text_io.output()])


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEnded")
    except Exception as e:
        print(f"Error: {e}")