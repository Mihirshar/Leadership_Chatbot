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
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

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
    try:
        loop = asyncio.new_event_loop()
        audio = loop.run_until_complete(_edge_synthesize_async(text, voice))
        loop.close()
        if audio:
            logger.info("Edge TTS: %d bytes, voice=%s", len(audio), voice)
        return audio or None
    except Exception as exc:
        logger.error("Edge TTS failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ElevenLabs  (PREMIUM — needs API key, supports voice cloning)
# ═══════════════════════════════════════════════════════════════════════════

ELEVENLABS_API = "https://api.elevenlabs.io/v1"
VOICE_CACHE = Path("config/voice_ids.json")


def _eleven_key() -> str:
    return os.environ.get("ELEVENLABS_API_KEY", "")


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
    # Tier 1: ElevenLabs cloned voice
    if elevenlabs_available():
        vid = _ensure_eleven_voice(leader_config)
        if vid:
            audio = eleven_synthesize(text, vid)
            if audio:
                return audio

    # Tier 2: Edge TTS (free)
    edge_voice = leader_config.get("voice_id", "")
    if edge_voice:
        audio = edge_synthesize(text, edge_voice)
        if audio:
            return audio

    # Tier 3: None → JS speechSynthesis fallback in browser
    return None
