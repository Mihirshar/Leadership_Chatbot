"""Gemini Live API client — real-time voice conversation with leader avatars.

Uses the native-audio model to generate natural speech responses.
Returns both text (transcription/fallback) and a WAV audio file for
downstream lip-sync video generation.
"""

import asyncio
import logging
import os
import threading
import wave
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

LIVE_MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
RECEIVE_SAMPLE_RATE = 24000
AUDIO_DIR = Path("assets/audio")


def _get_client() -> genai.Client:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not set.")
    return genai.Client(api_key=api_key, http_options={"api_version": "v1beta"})


def _save_wav(pcm_data: bytes, path: str) -> None:
    """Write raw 16-bit mono PCM to a standard WAV file."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RECEIVE_SAMPLE_RATE)
        wf.writeframes(pcm_data)


async def _live_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str,
    voice_name: str = "Puck",
) -> tuple[str, str | None]:
    """Open a Gemini Live session, send context + user message, collect audio."""

    client = _get_client()

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_name,
                )
            )
        ),
        system_instruction=system_prompt,
    )

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    audio_chunks: list[bytes] = []
    text_parts: list[str] = []

    async with client.aio.live.connect(model=LIVE_MODEL, config=config) as session:
        turns: list[types.Content] = []
        for msg in conversation_history:
            role = "model" if msg["role"] == "assistant" else "user"
            turns.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )
        turns.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)],
            )
        )

        await session.send_client_content(turns=turns, turn_complete=True)

        turn = session.receive()
        async for response in turn:
            if data := response.data:
                audio_chunks.append(data)
            if text := response.text:
                text_parts.append(text)

    audio_path = None
    if audio_chunks:
        pcm_data = b"".join(audio_chunks)
        audio_path = str(AUDIO_DIR / "last_response.wav")
        _save_wav(pcm_data, audio_path)
        logger.info("Audio saved: %d bytes → %s", len(pcm_data), audio_path)

    full_text = "".join(text_parts)
    return full_text, audio_path


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """Send recorded audio to Gemini for transcription."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return ""
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                        types.Part.from_text(
                            text="Transcribe this audio exactly. Return only the transcription, nothing else."
                        ),
                    ]
                )
            ],
        )
        return (response.text or "").strip()
    except Exception as exc:
        logger.error("Audio transcription failed: %s", exc)
        return ""


def get_live_response(
    system_prompt: str,
    conversation_history: list,
    user_message: str,
    voice_name: str = "Puck",
) -> tuple[str, str | None]:
    """Synchronous wrapper safe for Streamlit's threading model.

    Returns (text_response, wav_audio_path).
    text_response may be empty if transcription is unavailable — the caller
    should fall back to the regular text model in that case.
    """
    result: tuple[str, str | None] = ("", None)
    error: list[BaseException | None] = [None]

    def _run():
        nonlocal result
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                _live_response(
                    system_prompt, conversation_history, user_message, voice_name
                )
            )
            loop.close()
        except Exception as exc:
            error[0] = exc

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=20)

    if error[0]:
        logger.error("Gemini Live API failed: %s", error[0])
    return result
