"""
main.py
Speech-to-speech assistant demo using Strands, Bedrock, and FastRTC.
"""
import logging
from strands import Agent
from strands.models import BedrockModel
from fastrtc import (
    get_stt_model, # moonshine/base or moonshine/tiny
    get_tts_model, #kokoro
    Stream,
    ReplyOnPause,
    KokoroTTSOptions,
)

# Configure logging
logging.getLogger("strands").setLevel(logging.INFO)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

# System prompt for agent
system_prompt = """
You are a helpful assistant named Olaf, answering questions from the user.
- Be clear, concise, and specific in your answers.
- If you don't know the answer, say "I don't know".
- If you don't have the information you need to answer a question, say "I don't know".
"""

# Initialize models
stt_model = get_stt_model()  # Speech-to-text model
tts_model = get_tts_model(model="kokoro")  # Text-to-speech model

# Configure the TTS model options
# KokoroTTSOptions allows you to set the voice, speed, and language

tts_options = KokoroTTSOptions(
    voice="af_heart",
    speed=1.0,
    lang="en-us"
)

def process_response(audio):
    """
    Process audio input and generate LLM response with TTS.

    Args:
        audio (bytes): Audio input data.
    Yields:
        bytes: Audio chunks of the TTS response.
    """
    # Convert speech to text using STT model
    text = stt_model.stt(audio)
    if not text.strip():
        return

    # Get response from agent (LLM)
    response = agent(text)
    # Extract the content string from AgentResult
    response_content = getattr(response, "content", str(response))

    # Convert response to audio using TTS model
    for audio_chunk in tts_model.stream_tts_sync(response_content or "", options=tts_options):
        # Yield the audio chunk
        yield audio_chunk

# BedrockModel is used to access Anthropic Claude 3.5 Haiku via AWS Bedrock
bedrock_model = BedrockModel(
    model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    region_name='us-west-2',
    temperature=0.3,
)

# Agent wraps the LLM and system prompt
agent = Agent(model=bedrock_model, system_prompt=system_prompt)

# Stream handles the audio input/output and UI
stream = Stream(
    handler=ReplyOnPause(process_response, input_sample_rate=16000),
    additional_outputs_handler=lambda a, b: b,  # Pass-through handler for additional outputs
    modality="audio",
    mode="send-receive",
    ui_args={
        "pulse_color": "rgb(255, 255, 255)",
        "icon_button_color": "rgb(255, 255, 255)",
        "title": "🔊 Audio Assistant",
    },
)

if __name__ == "__main__":
    # Launch the UI on port 7860
    stream.ui.launch(server_port=7860)