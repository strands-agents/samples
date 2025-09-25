from __future__ import annotations

"""
listen: Background speech listener and Whisper transcriber tool with trigger keyword and auto mode functionality

Features
- Start/stop a background listener that captures audio from a microphone or virtual cable (VAC)
- Voice activation detection (simple energy threshold; optional WebRTC VAD if installed)
- Segments speech by pauses and transcribes each segment using OpenAI Whisper
- Saves raw WAV segments and a transcripts.jsonl log
- Query status and recent transcripts, list input devices
- Trigger keyword functionality: automatically call use_agent when keyword is detected
- Auto stealth mode: triggers agent on long text (50+ chars) without speaking out loud

Dependencies
- openai-whisper (installed as "whisper")
- sounddevice (recommended) or raise a helpful error if missing
- Optional: webrtcvad for higher-quality VAD (falls back to energy threshold)

Usage (as a Strands tool)
- listen(action="list_devices")
- listen(action="start", model_name="base", device_name="BlackHole", trigger_keyword="hey research", agent=agent)
- listen(action="start", model_name="base", auto_mode=True, length_threshold=50, agent=agent)  # Stealth mode
- listen(action="status")
- listen(action="get_transcripts", limit=10)
- listen(action="stop")
"""

import os
import io
import time
import json
import wave
import queue
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

import numpy as np

try:
    import sounddevice as sd  # type: ignore
except Exception:  # pragma: no cover
    sd = None

try:
    import webrtcvad  # type: ignore
except Exception:  # pragma: no cover
    webrtcvad = None

try:
    import whisper  # type: ignore
except Exception as e:  # pragma: no cover
    whisper = None

from strands import tool

# -------------------------
# Module-level state
# -------------------------
STATE: Dict[str, Any] = {
    "running": False,
    "start_time": None,
    "threads": {},
    "stop_event": None,
    "audio_queue": None,
    "segment_queue": None,
    "transcript_log": [],  # last N transcripts
    "transcript_count": 0,
    "save_dir": None,
    "log_path": None,
    "model_name": None,
    "device_name": None,
    "sample_rate": 16000,
    "channels": 1,
    "energy_threshold": 0.01,
    "pause_duration": 0.8,
    "use_vad": True,
    "trigger_keyword": None,
    "agent": None,
    "auto_mode": False,
    "length_threshold": 50,
}

MAX_MEMORY_TRANSCRIPTS = 50

logger = logging.getLogger(__name__)


def _now_ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S.%fZ")


def _ensure_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _find_input_device(name_substr: Optional[str]) -> Optional[int]:
    if sd is None:
        return None
    try:
        devices = sd.query_devices()
    except Exception:
        return None

    chosen = None
    if name_substr:
        for i, d in enumerate(devices):
            if (
                d.get("max_input_channels", d.get("maxInputChannels", 0)) > 0
                and name_substr.lower() in str(d.get("name", "")).lower()
            ):
                chosen = i
                break
    if chosen is None:
        # pick default input device if available
        default = sd.default.device
        if isinstance(default, (list, tuple)):
            in_index = default[0]
        else:
            in_index = default
        try:
            info = sd.query_devices(in_index)
            if info.get("max_input_channels", info.get("maxInputChannels", 0)) > 0:
                chosen = in_index
        except Exception:
            # fallback: any device with input
            for i, d in enumerate(devices):
                if d.get("max_input_channels", d.get("maxInputChannels", 0)) > 0:
                    chosen = i
                    break
    return chosen


def _rms(a: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(a), dtype=np.float64))) if a.size else 0.0


def _write_wav(path: str, data: np.ndarray, sample_rate: int) -> None:
    # Ensure int16 PCM
    if data.dtype != np.int16:
        # clamp and convert
        clipped = np.clip(data, -1.0, 1.0)
        data16 = (clipped * 32767.0).astype(np.int16)
    else:
        data16 = data
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(data16.tobytes())


def _transcriber_worker(stop_event: threading.Event) -> None:
    model_name = STATE["model_name"]
    save_dir = STATE["save_dir"]
    log_path = STATE["log_path"]
    sample_rate = STATE["sample_rate"]
    trigger_keyword = STATE.get("trigger_keyword")
    agent = STATE.get("agent")

    if whisper is None:
        # Cannot run transcriptions
        return

    try:
        model = whisper.load_model(model_name or "base")
    except Exception:
        model = whisper.load_model("base")

    while not stop_event.is_set():
        try:
            item = STATE["segment_queue"].get(timeout=0.2)
        except queue.Empty:
            continue
        if item is None:
            break
        segment_audio: np.ndarray = item["audio"]  # float32 or int16 mono
        seg_started: str = item["started"]
        language: Optional[str] = item.get("language")

        # Persist WAV
        fname = f"segment_{seg_started}_{_now_ts()}.wav"
        wav_path = os.path.join(save_dir, fname)
        _write_wav(wav_path, segment_audio, sample_rate)

        # Transcribe
        try:
            result = model.transcribe(wav_path, language=language)
            text = (result or {}).get("text", "").strip()
        except Exception as e:
            text = f"[transcription_error] {e}"

        record = {
            "timestamp": _now_ts(),
            "wav_path": wav_path,
            "text": text,
        }
        # Append to memory
        STATE["transcript_log"].append(record)
        STATE["transcript_log"] = STATE["transcript_log"][-MAX_MEMORY_TRANSCRIPTS:]
        STATE["transcript_count"] += 1

        # Append to JSONL
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # Unified processing: Check for trigger keyword first, then auto mode
        # This allows hybrid behavior: auto mode + trigger keyword override
        trigger_detected = (
            trigger_keyword
            and agent
            and text
            and not text.startswith("[transcription_error]")
            and trigger_keyword.lower() in text.lower()
        )

        auto_mode_triggered = (
            STATE.get("auto_mode", False)
            and agent
            and text
            and not text.startswith("[transcription_error]")
            and not text.startswith(
                "[AGENT_RESPONSE]"
            )  # Don't trigger on agent's own responses
            and len(text.strip()) >= STATE.get("length_threshold", 50)
        )

        # Process if either condition is met
        if trigger_detected or auto_mode_triggered:
            try:
                # Determine mode based on trigger keyword presence
                is_speaking_mode = trigger_detected
                mode_description = (
                    "🎯 TRIGGER KEYWORD" if is_speaking_mode else "🔍 AUTO STEALTH"
                )

                logger.info(
                    f"{mode_description} activated for: '{text[:100]}{'...' if len(text) > 100 else ''}'"
                )

                # Build context from previous transcriptions
                context_transcripts = []
                recent_transcripts = STATE["transcript_log"][
                    -20:
                ]  # Last 20 for context

                for transcript in recent_transcripts:
                    transcript_text = transcript.get("text", "")
                    timestamp = transcript.get("timestamp", "")

                    if transcript_text.startswith("[AGENT_RESPONSE]"):
                        clean_response = transcript_text.replace(
                            "[AGENT_RESPONSE] ", ""
                        )
                        context_transcripts.append(
                            f"[{timestamp}] AGENT: {clean_response}"
                        )
                    elif transcript_text.startswith("[AGENT_AUTO_MONITOR]"):
                        clean_response = transcript_text.replace(
                            "[AGENT_AUTO_MONITOR] ", ""
                        )
                        context_transcripts.append(
                            f"[{timestamp}] AGENT_MONITOR: {clean_response}"
                        )
                    elif len(transcript_text) > 0:
                        context_transcripts.append(
                            f"[{timestamp}] USER: {transcript_text}"
                        )

                # Build conversation context
                conversation_context = ""
                if context_transcripts:
                    conversation_context = (
                        f"\n\nRECENT CONVERSATION CONTEXT:\n"
                        + "\n".join(context_transcripts[-10:])
                    )

                if is_speaking_mode:
                    # TRIGGER KEYWORD MODE - Agent should participate actively
                    # Extract the part after the trigger keyword as the prompt
                    text_lower = text.lower()
                    keyword_lower = trigger_keyword.lower()
                    keyword_index = text_lower.find(keyword_lower)

                    if keyword_index != -1:
                        prompt_text = text[
                            keyword_index + len(trigger_keyword) :
                        ].strip()
                        if not prompt_text:
                            prompt_text = "I'm listening, how can I help you?"
                    else:
                        prompt_text = text

                    logger.info(f"📝 Extracted prompt: '{prompt_text}'")

                    # Speaking mode system prompt - agent can use speak tool
                    system_prompt = (
                        agent.system_prompt + f"\n\n=== VOICE INTERACTION MODE ===\n"
                        f"You are responding to voice input triggered by '{trigger_keyword}'.\n"
                        f"User said: '{text}'\n"
                        f"Extracted command: '{prompt_text}'\n\n"
                        f"ACTIVE PARTICIPATION MODE:\n"
                        f"- You are now ACTIVELY PARTICIPATING in the conversation\n"
                        f"- Use the 'speak' tool to provide audio responses when appropriate\n"
                        f"- Keep responses concise and conversational (voice-friendly)\n"
                        f"- You can see your own previous responses in the conversation context\n"
                        f"- If you detect this input is an echo of your own speech, acknowledge briefly\n"
                        f"- Focus on the current user request: '{prompt_text}'\n"
                        f"- Be helpful and engage naturally with the user"
                        + conversation_context
                    )

                    prompt_for_agent = prompt_text
                    log_marker = "[AGENT_RESPONSE]"

                else:
                    # AUTO STEALTH MODE - Agent observes but can be triggered to speak by keyword
                    system_prompt = (
                        agent.system_prompt
                        + f"\n\n=== AUTO STEALTH MONITORING MODE ===\n"
                        f"You are in stealth monitoring mode - passively observing speech.\n"
                        f"User said: '{text}'\n\n"
                        f"STEALTH MODE BEHAVIOR:\n"
                        f"- You are LISTENING and LEARNING, not actively participating\n"
                        f"- DO NOT use 'speak' tool unless absolutely critical/emergency\n"
                        f"- Only respond mentally/internally - no audio output\n"
                        f"- You are building context and understanding\n"
                        f"- Only break stealth if you need to answer\n"
                        f"- Process information silently and store insights\n"
                        f"- Keep any responses extremely brief and internal\n"
                        f"- Your role is observer, not participant\n"
                        f"- Less talking, more listening and learning\n"
                        f"- Avoid interrupting natural conversation flow\n"
                        f"- REMEMBER: If someone says '{trigger_keyword}' or similar, you can participate actively. You should be actively seeking to speak but not breaking the stealth often."
                        + conversation_context
                    )

                    prompt_for_agent = (
                        f"Process this overheard speech silently (stealth mode): {text}"
                    )
                    log_marker = "[AGENT_AUTO_MONITOR]"

                # Call use_agent with the appropriate system prompt
                response = agent.tool.use_agent(
                    prompt=prompt_for_agent,
                    system_prompt=system_prompt,
                    record_direct_tool_call=False,
                    agent=agent,
                )

                logger.info(f"🤖 Agent response ({mode_description}): {response}")

                # Log the agent response with appropriate marker
                agent_record = {
                    "timestamp": _now_ts(),
                    "wav_path": None,
                    "text": f"{log_marker} {response.get('content', [{}])[0].get('text', 'No response')}",
                    "original_transcript": text,
                    "mode": "speaking" if is_speaking_mode else "auto_stealth",
                }

                if is_speaking_mode:
                    agent_record["trigger_prompt"] = prompt_for_agent

                STATE["transcript_log"].append(agent_record)
                STATE["transcript_log"] = STATE["transcript_log"][
                    -MAX_MEMORY_TRANSCRIPTS:
                ]

                # Also append to JSONL
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(agent_record, ensure_ascii=False) + "\n")
                except Exception:
                    pass

            except Exception as processing_error:
                logger.error(f"❌ Error processing agent trigger: {processing_error}")

        STATE["segment_queue"].task_done()


def _segmenter_worker(stop_event: threading.Event) -> None:
    """Consumes raw audio frames and emits voiced segments to the transcriber."""
    sr = STATE["sample_rate"]
    energy_th = float(STATE["energy_threshold"])
    pause_dur = float(STATE["pause_duration"])
    use_vad = bool(STATE["use_vad"]) and (webrtcvad is not None)

    vad = None
    if use_vad and webrtcvad is not None:
        vad = webrtcvad.Vad(2)  # 0-3, 2 is moderately aggressive

    current: List[np.ndarray] = []
    speaking = False
    last_voice_time = 0.0
    seg_start_ts = None

    # For VAD framing: 20 ms frames at 16 kHz => 320 samples
    frame_len = int(0.02 * sr)
    frame_buf = np.empty((0,), dtype=np.float32)

    while not stop_event.is_set():
        try:
            chunk = STATE["audio_queue"].get(timeout=0.2)  # float32 mono
        except queue.Empty:
            # check for pause timeout on idle
            if speaking and (time.time() - last_voice_time) >= pause_dur and current:
                # finalize segment
                seg = (
                    np.concatenate(current, axis=0)
                    if len(current)
                    else np.empty((0,), dtype=np.float32)
                )
                STATE["segment_queue"].put(
                    {"audio": seg, "started": seg_start_ts, "language": None}
                )
                current.clear()
                speaking = False
                seg_start_ts = None
            continue

        if chunk is None:
            break

        # accumulate into 20ms frames for VAD
        frame_buf = np.concatenate([frame_buf, chunk.astype(np.float32)])

        while frame_buf.shape[0] >= frame_len:
            frame = frame_buf[:frame_len]
            frame_buf = frame_buf[frame_len:]

            is_voiced = False
            if vad is not None:
                # VAD expects 16-bit PCM bytes
                fbytes = (
                    (np.clip(frame, -1.0, 1.0) * 32767.0).astype(np.int16).tobytes()
                )
                try:
                    is_voiced = vad.is_speech(fbytes, STATE["sample_rate"])
                except Exception:
                    is_voiced = False
            else:
                # Energy-based detection
                is_voiced = _rms(frame) >= energy_th

            if is_voiced:
                if not speaking:
                    seg_start_ts = _now_ts()
                speaking = True
                last_voice_time = time.time()
                current.append(frame)
            else:
                if speaking:
                    # still collecting but check pause timeout below
                    current.append(frame)
                # non-voiced frame: if in pause long enough, finalize later

        # if enough pause after last_voice_time, close the segment
        if speaking and (time.time() - last_voice_time) >= pause_dur and current:
            seg = (
                np.concatenate(current, axis=0)
                if len(current)
                else np.empty((0,), dtype=np.float32)
            )
            STATE["segment_queue"].put(
                {"audio": seg, "started": seg_start_ts, "language": None}
            )
            current.clear()
            speaking = False
            seg_start_ts = None

        STATE["audio_queue"].task_done()


def _audio_callback(indata, frames, time_info, status):  # sd.InputStream callback
    if status:
        # Non-fatal stream status
        pass
    # Convert to mono float32
    data = indata
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    else:
        data = data.reshape(-1)
    STATE["audio_queue"].put_nowait(data.astype(np.float32))


def _start_listener(
    model_name: str,
    device_name: Optional[str],
    save_dir: str,
    sample_rate: int,
    channels: int,
    energy_threshold: float,
    pause_duration: float,
    use_vad: bool,
    trigger_keyword: Optional[str] = None,
    agent: Optional[Any] = None,
    auto_mode: bool = False,
    length_threshold: int = 50,
) -> Dict[str, Any]:
    if sd is None:
        return {
            "status": "error",
            "content": [
                {
                    "text": "sounddevice is not installed. Please `pip install sounddevice` (and optionally `pip install webrtcvad`)."
                }
            ],
        }
    if whisper is None:
        return {
            "status": "error",
            "content": [
                {
                    "text": "openai-whisper is not available. Ensure 'openai-whisper' is installed."
                }
            ],
        }

    _ensure_dirs(save_dir)
    log_path = os.path.join(save_dir, "transcripts.jsonl")

    device_index = _find_input_device(device_name)
    if device_index is None:
        return {
            "status": "error",
            "content": [
                {
                    "text": f"Unable to find a suitable input device (searched for: {device_name or 'default'})."
                }
            ],
        }

    stop_event = threading.Event()
    STATE.update(
        {
            "running": True,
            "start_time": time.time(),
            "threads": {},
            "stop_event": stop_event,
            "audio_queue": queue.Queue(maxsize=100),
            "segment_queue": queue.Queue(maxsize=50),
            "save_dir": save_dir,
            "log_path": log_path,
            "model_name": model_name,
            "device_name": device_name,
            "sample_rate": int(sample_rate),
            "channels": int(channels),
            "energy_threshold": float(energy_threshold),
            "pause_duration": float(pause_duration),
            "use_vad": bool(use_vad),
            "trigger_keyword": trigger_keyword,
            "agent": agent,
            "auto_mode": bool(auto_mode),
            "length_threshold": int(length_threshold),
        }
    )

    # Start worker threads
    seg_thread = threading.Thread(
        target=_segmenter_worker, args=(stop_event,), daemon=True
    )
    tx_thread = threading.Thread(
        target=_transcriber_worker, args=(stop_event,), daemon=True
    )
    seg_thread.start()
    tx_thread.start()

    # Start audio stream in its own thread context
    def stream_thread():
        try:
            with sd.InputStream(
                device=device_index,
                samplerate=STATE["sample_rate"],
                channels=STATE["channels"],
                dtype="float32",
                blocksize=0,
                callback=_audio_callback,
            ):
                while not stop_event.is_set():
                    time.sleep(0.1)
        except Exception:
            # If stream fails, signal stop
            stop_event.set()

    a_thread = threading.Thread(target=stream_thread, daemon=True)
    a_thread.start()

    STATE["threads"] = {
        "audio": a_thread,
        "segmenter": seg_thread,
        "transcriber": tx_thread,
    }

    return {
        "status": "success",
        "content": [
            {
                "text": f"Listening started (model={model_name}, device_index={device_index}, device='{device_name or 'default'}'{', trigger_keyword=' + trigger_keyword if trigger_keyword else ''}{', auto_mode=ON (stealth)' if auto_mode else ''}). Saving to: {save_dir}"
            }
        ],
    }


def _stop_listener() -> Dict[str, Any]:
    if not STATE.get("running"):
        return {"status": "success", "content": [{"text": "Listener already stopped."}]}

    stop_event: threading.Event = STATE.get("stop_event")
    if stop_event is not None:
        stop_event.set()

    # Drain queues and signal termination
    aq: queue.Queue = STATE.get("audio_queue")
    sq: queue.Queue = STATE.get("segment_queue")
    if aq:
        try:
            aq.put_nowait(None)
        except Exception:
            pass
    if sq:
        try:
            sq.put_nowait(None)
        except Exception:
            pass

    # Join threads briefly
    for t in (STATE.get("threads") or {}).values():
        if isinstance(t, threading.Thread):
            t.join(timeout=2.0)

    STATE.update(
        {
            "running": False,
            "threads": {},
            "stop_event": None,
            "audio_queue": None,
            "segment_queue": None,
        }
    )

    return {"status": "success", "content": [{"text": "Listening stopped."}]}


def _status() -> Dict[str, Any]:
    running = STATE.get("running", False)
    info = {
        "running": running,
        "model_name": STATE.get("model_name"),
        "device_name": STATE.get("device_name"),
        "save_dir": STATE.get("save_dir"),
        "sample_rate": STATE.get("sample_rate"),
        "channels": STATE.get("channels"),
        "energy_threshold": STATE.get("energy_threshold"),
        "pause_duration": STATE.get("pause_duration"),
        "use_vad": bool(STATE.get("use_vad")) and (webrtcvad is not None),
        "trigger_keyword": STATE.get("trigger_keyword"),
        "trigger_enabled": bool(STATE.get("trigger_keyword"))
        and bool(STATE.get("agent")),
        "auto_mode": STATE.get("auto_mode", False),
        "length_threshold": STATE.get("length_threshold", 50),
        "auto_mode_enabled": bool(STATE.get("auto_mode", False))
        and bool(STATE.get("agent")),
        "transcript_count": STATE.get("transcript_count", 0),
        "uptime_sec": (
            (time.time() - STATE.get("start_time", time.time())) if running else 0
        ),
    }
    return {"status": "success", "content": [{"text": json.dumps(info)}]}


def _list_devices() -> Dict[str, Any]:
    if sd is None:
        return {
            "status": "error",
            "content": [
                {
                    "text": "sounddevice is not installed. Please `pip install sounddevice`."
                }
            ],
        }
    try:
        devices = sd.query_devices()
    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"Could not query devices: {e}"}],
        }

    inputs = []
    for i, d in enumerate(devices):
        max_in = d.get("max_input_channels", d.get("maxInputChannels", 0))
        if max_in and max_in > 0:
            inputs.append(
                {
                    "index": i,
                    "name": str(d.get("name", "")),
                    "max_input_channels": int(max_in),
                    "default_samplerate": d.get(
                        "default_samplerate", d.get("defaultSampleRate")
                    ),
                }
            )
    return {
        "status": "success",
        "content": [{"text": json.dumps(inputs, ensure_ascii=False)}],
    }


def _get_transcripts(limit: int = 10) -> Dict[str, Any]:
    limit = max(1, min(int(limit), MAX_MEMORY_TRANSCRIPTS))
    items = list(STATE.get("transcript_log", []))[-limit:]
    return {
        "status": "success",
        "content": [{"text": json.dumps(items, ensure_ascii=False)}],
    }


@tool
def listen(
    action: str = "status",
    model_name: str = "base",
    device_name: Optional[str] = None,
    save_dir: str = "./.listen",
    sample_rate: int = 16000,
    channels: int = 1,
    energy_threshold: float = 0.01,
    pause_duration: float = 0.8,
    use_vad: bool = True,
    transcripts_limit: int = 10,
    trigger_keyword: Optional[str] = None,
    agent: Optional[Any] = None,
    auto_mode: bool = False,
    length_threshold: int = 50,
) -> Dict[str, Any]:
    """Background speech listener that segments and transcribes audio with Whisper.

    Args:
        action: One of ["start", "stop", "status", "list_devices", "get_transcripts"].
        model_name: Whisper model name (tiny, base, small, medium, large, etc.).
        device_name: Optional substring of input device name (e.g., "BlackHole"). Defaults to system default input.
        save_dir: Directory to store WAV segments and transcripts.jsonl.
        sample_rate: Recording sample rate. Whisper works well with 16k.
        channels: Number of channels to record (1 recommended).
        energy_threshold: Energy threshold for simple VAD if WebRTC VAD is not available.
        pause_duration: Seconds of silence to consider the segment finished.
        use_vad: If True and webrtcvad is installed, use it; otherwise fallback to energy threshold.
        transcripts_limit: For get_transcripts, how many recent items to return (max 50).
        trigger_keyword: Optional trigger keyword to activate use_agent (e.g., "hey research agent").
        agent: Parent agent instance for trigger functionality.
        auto_mode: Enable auto stealth mode - triggers agent on long text (50+ chars) without speaking.
        length_threshold: Character threshold for auto mode trigger (default: 50).

    Returns: Dict with status and content text.
    """
    action = (action or "status").lower()

    if action == "start":
        return _start_listener(
            model_name=model_name,
            device_name=device_name,
            save_dir=save_dir,
            sample_rate=sample_rate,
            channels=channels,
            energy_threshold=energy_threshold,
            pause_duration=pause_duration,
            use_vad=use_vad,
            trigger_keyword=trigger_keyword,
            agent=agent,
            auto_mode=auto_mode,
            length_threshold=length_threshold,
        )
    elif action == "stop":
        return _stop_listener()
    elif action == "status":
        return _status()
    elif action == "list_devices":
        return _list_devices()
    elif action == "get_transcripts":
        return _get_transcripts(limit=transcripts_limit)
    else:
        return {"status": "error", "content": [{"text": f"Unknown action: {action}"}]}
