"""Multi-tier TTS voice client.

Priority chain (automatic fallback):
  1. ElevenLabs  — cloned voice from audio samples  (needs ELEVENLABS_API_KEY)
  2. Edge TTS    — free Microsoft Neural voices      (always available, $0)
  3. None        — caller falls back to browser speechSynthesis

Each leader YAML has two voice-related fields:
  voice_id:     Microsoft Neural voice name (e.g. "en-IN-PrabhatNeural")
                Used by Edge TTS — always free.
  voice_sample: path to an audio clip for ElevenLabs cloning (optional).
"""

import asyncio
import io
import json
import logging
import os
import base64
import streamlit as st
import fal_client
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

EDGE_FALLBACK_VOICES = (
    "en-IN-PrabhatNeural",
    "en-US-GuyNeural",
)

# ═══════════════════════════════════════════════════════════════════════════
# Edge TTS  (FREE — no API key required)
# ═══════════════════════════════════════════════════════════════════════════

def _edge_tts_available() -> bool:
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


async def _edge_synthesize_async(text: str, voice: str) -> bytes:
    import edge_tts
    communicate = edge_tts.Communicate(text[:3000], voice)
    buf = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf.write(chunk["data"])
    return buf.getvalue()


def edge_synthesize(text: str, voice: str) -> bytes | None:
    """Synthesize speech using free Microsoft Edge Neural TTS.

    Returns MP3 bytes, or None on failure.
    """
    if not _edge_tts_available():
        logger.warning("edge-tts not installed — pip install edge-tts")
        return None
    clean_text = (text or "").strip()
    if not clean_text:
        return None

    # Try requested voice first, then known-good fallbacks.
    candidates = [voice] if voice else []
    candidates.extend(v for v in EDGE_FALLBACK_VOICES if v and v != voice)

    for candidate in candidates:
        loop = asyncio.new_event_loop()
        try:
            audio = loop.run_until_complete(_edge_synthesize_async(clean_text, candidate))
            if audio:
                logger.info("Edge TTS: %d bytes, voice=%s", len(audio), candidate)
                return audio
        except Exception as exc:
            logger.warning("Edge TTS failed for voice %s: %s", candidate, exc)
        finally:
            loop.close()
    return None


# ═══════════════════════════════════════════════════════════════════════════
# ElevenLabs  (PREMIUM — needs API key, supports voice cloning)
# ═══════════════════════════════════════════════════════════════════════════

ELEVENLABS_API = "https://api.elevenlabs.io/v1"
VOICE_CACHE = Path("config/voice_ids.json")


def _eleven_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not key and "ELEVENLABS_API_KEY" in st.secrets:
        key = st.secrets["ELEVENLABS_API_KEY"]
    return key


def elevenlabs_available() -> bool:
    return bool(_eleven_key())


def _eleven_headers() -> dict:
    return {"xi-api-key": _eleven_key()}


def _load_cache() -> dict:
    if VOICE_CACHE.exists():
        return json.loads(VOICE_CACHE.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    VOICE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    VOICE_CACHE.write_text(json.dumps(cache, indent=2))


def get_eleven_voice_id(leader_id: str) -> str | None:
    return _load_cache().get(leader_id)


def clone_voice(leader_id: str, name: str, sample_path: str) -> str | None:
    """Upload audio sample to ElevenLabs Instant Voice Cloning (one-time)."""
    if not elevenlabs_available():
        return None
    p = Path(sample_path)
    if not p.exists():
        logger.error("Voice sample not found: %s", sample_path)
        return None
    try:
        with open(p, "rb") as f:
            resp = requests.post(
                f"{ELEVENLABS_API}/voices/add",
                headers=_eleven_headers(),
                data={"name": f"EXL-{name}", "description": f"Cloned voice for {name}"},
                files={"files": (p.name, f, "audio/mpeg")},
                timeout=60,
            )
        resp.raise_for_status()
        vid = resp.json().get("voice_id")
        if vid:
            cache = _load_cache()
            cache[leader_id] = vid
            _save_cache(cache)
            logger.info("Cloned voice for %s → %s", name, vid)
        return vid
    except Exception as exc:
        logger.error("Voice cloning failed for %s: %s", name, exc)
        return None


def eleven_synthesize(
    text: str,
    voice_id: str,
    model: str = "eleven_flash_v2_5",
) -> bytes | None:
    """TTS via ElevenLabs. Returns MP3 bytes or None."""
    if not elevenlabs_available():
        return None
    try:
        resp = requests.post(
            f"{ELEVENLABS_API}/text-to-speech/{voice_id}",
            headers={**_eleven_headers(), "Content-Type": "application/json"},
            json={
                "text": text[:2500],
                "model_id": model,
                "voice_settings": {"stability": 0.55, "similarity_boost": 0.80, "style": 0.3},
            },
            timeout=30,
            stream=True,
        )
        resp.raise_for_status()
        buf = io.BytesIO()
        for chunk in resp.iter_content(chunk_size=4096):
            buf.write(chunk)
        audio = buf.getvalue()
        logger.info("ElevenLabs: %d bytes, voice=%s", len(audio), voice_id)
        return audio
    except Exception as exc:
        logger.error("ElevenLabs TTS failed: %s", exc)
        return None


def _ensure_eleven_voice(leader_config: dict) -> str | None:
    # Priority: explicit eleven_voice_id in YAML → cached clone → clone from sample
    explicit = leader_config.get("eleven_voice_id", "")
    if explicit:
        return explicit

    lid = leader_config["id"]
    vid = get_eleven_voice_id(lid)
    if vid:
        return vid

    sample = leader_config.get("voice_sample", "")
    if sample and Path(sample).exists():
        return clone_voice(lid, leader_config["name"], sample)
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Unified API  — caller uses these two functions
# ═══════════════════════════════════════════════════════════════════════════

def synthesize_for_leader(leader_config: dict, text: str) -> bytes | None:
    """Generate TTS audio for a leader's reply.

    Tries ElevenLabs (cloned voice) first, then Edge TTS (free neural voice).
    Returns MP3 bytes or None (caller should fall back to browser TTS).
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return None

    # Tier 1: ElevenLabs cloned voice
    if elevenlabs_available():
        vid = _ensure_eleven_voice(leader_config)
        if vid:
            audio = eleven_synthesize(clean_text, vid)
            if audio:
                return audio

    # Tier 2: Edge TTS (free)
    edge_voice = leader_config.get("voice_id", "")
    if edge_voice:
        audio = edge_synthesize(clean_text, edge_voice)
        if audio:
            return audio

    # Tier 3: None → JS speechSynthesis fallback in browser
    return None


# ═══════════════════════════════════════════════════════════════════════════
# Fal.ai (Lip Sync Video Generation)
# ═══════════════════════════════════════════════════════════════════════════

def _fal_key() -> str:
    key = os.environ.get("FAL_KEY", "")
    if not key and "FAL_KEY" in st.secrets:
        key = st.secrets["FAL_KEY"]
    return key


def fal_available() -> bool:
    return bool(_fal_key())


def generate_lip_sync(audio_bytes: bytes, image_path: str) -> str | None:
    """Generate a lip-sync video using Fal.ai (audio-driven).

    Returns the URL of the generated video or None if failed/unavailable.
    """
    if not fal_available():
        return None

    # Check if image exists
    if not Path(image_path).exists():
        logger.warning(f"Lip-sync skipped: Image not found at {image_path}")
        return None

    try:
        # Set API key for this call
        os.environ["FAL_KEY"] = _fal_key()

        # Prepare data URIs
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        audio_url = f"data:audio/mpeg;base64,{audio_b64}"

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # Detect mime type roughly from extension
        ext = Path(image_path).suffix.lower().replace(".", "")
        if ext == "jpg": ext = "jpeg"
        image_url = f"data:image/{ext};base64,{img_b64}"

        # Submit to Fal.ai (using sadtalker model which is cost-effective)
        # We can switch to fal-ai/kling-video/v1/audio-driven for higher quality if needed
        handler = fal_client.submit(
            "fal-ai/sadtalker",
            arguments={
                "source_image_url": image_url,
                "driven_audio_url": audio_url,
            }
        )

        # Wait for result
        result = handler.get()

        if result and "video" in result and "url" in result["video"]:
            video_url = result["video"]["url"]
            logger.info(f"Fal.ai lip-sync generated: {video_url}")
            return video_url

    except Exception as e:
        logger.error(f"Fal.ai lip-sync failed: {e}")
        return None

    return None
