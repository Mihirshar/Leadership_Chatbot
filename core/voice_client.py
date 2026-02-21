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
import time
import streamlit as st
from pathlib import Path

import requests

try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False

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
                "voice_settings": {
                    "stability": 0.60,
                    "similarity_boost": 0.85,
                    "style": 0.25,
                    "speed": 0.85,
                },
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


USER_VOICE = "en-US-ChristopherNeural"


def synthesize_user_text(text: str) -> bytes | None:
    """Generate TTS audio for the user's question.

    Uses Edge TTS with a clear, neutral English voice.
    Returns MP3 bytes or None.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return None
    return edge_synthesize(clean_text, USER_VOICE)


# ═══════════════════════════════════════════════════════════════════════════
# FAL.AI (Lip Sync Video Generation via SadTalker)
# ═══════════════════════════════════════════════════════════════════════════

def _fal_key() -> str:
    key = os.environ.get("FAL_KEY", "")
    if not key and "FAL_KEY" in st.secrets:
        key = st.secrets["FAL_KEY"]
    return key


def fal_available() -> bool:
    """Check if FAL.AI lip-sync is available."""
    return FAL_AVAILABLE and bool(_fal_key())


def _did_key() -> str:
    key = os.environ.get("D_ID_API_KEY", "")
    if not key:
        key = os.environ.get("DID_API_KEY", "")
    if not key and "D_ID_API_KEY" in st.secrets:
        key = st.secrets["D_ID_API_KEY"]
    if not key and "DID_API_KEY" in st.secrets:
        key = st.secrets["DID_API_KEY"]
    return key


def did_available() -> bool:
    return bool(_did_key())


def _did_auth() -> tuple[str, str]:
    # D-ID uses Basic Auth with the API key as username.
    return (_did_key(), "")


def _did_upload_image(image_path: str) -> str | None:
    if not Path(image_path).exists():
        logger.warning("D-ID image upload skipped: image not found at %s", image_path)
        return None
    ext = Path(image_path).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        logger.warning("D-ID image upload skipped: unsupported image type %s", ext)
        return None
    mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"
    with open(image_path, "rb") as f:
        files = {"image": (Path(image_path).name, f, mime)}
        resp = requests.post(
            "https://api.d-id.com/images",
            files=files,
            auth=_did_auth(),
            timeout=60,
        )
    resp.raise_for_status()
    return resp.json().get("url")


def _did_upload_audio(audio_bytes: bytes) -> str | None:
    if not audio_bytes:
        return None
    files = {"audio": ("audio.mp3", audio_bytes, "audio/mpeg")}
    resp = requests.post(
        "https://api.d-id.com/audios",
        files=files,
        auth=_did_auth(),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("url")


def _did_create_talk(image_url: str, audio_url: str) -> str | None:
    payload = {
        "source_url": image_url,
        "script": {"type": "audio", "audio_url": audio_url},
    }
    resp = requests.post(
        "https://api.d-id.com/talks",
        json=payload,
        auth=_did_auth(),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json().get("id")


def _did_poll_talk(talk_id: str, timeout_s: int = 120) -> str | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        resp = requests.get(
            f"https://api.d-id.com/talks/{talk_id}",
            auth=_did_auth(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status")
        if status == "done":
            return data.get("result_url")
        if status in {"error", "rejected"}:
            logger.error("D-ID talk failed: %s", data)
            return None
        time.sleep(1.5)
    logger.warning("D-ID talk timed out after %ss", timeout_s)
    return None


def _generate_lip_sync_did(audio_bytes: bytes, image_path: str) -> str | None:
    if not did_available():
        return None
    if not Path(image_path).exists():
        logger.warning("D-ID lip-sync skipped: image not found at %s", image_path)
        return None
    try:
        logger.info("Uploading image/audio to D-ID...")
        image_url = _did_upload_image(image_path)
        audio_url = _did_upload_audio(audio_bytes)
        if not image_url or not audio_url:
            return None
        logger.info("Creating D-ID talk...")
        talk_id = _did_create_talk(image_url, audio_url)
        if not talk_id:
            return None
        logger.info("Polling D-ID talk status...")
        return _did_poll_talk(talk_id)
    except Exception as e:
        logger.error("D-ID lip-sync failed: %s", e)
        return None


def _fal_preset() -> str:
    preset = os.environ.get("FAL_PRESET", "").strip().lower()
    if not preset and "FAL_PRESET" in st.secrets:
        preset = str(st.secrets["FAL_PRESET"]).strip().lower()
    if preset not in {"fast", "balanced", "quality"}:
        preset = "balanced"
    return preset


def _generate_lip_sync_fal(audio_bytes: bytes, image_path: str) -> str | None:
    """Generate a lip-sync video using FAL.AI's SadTalker model.

    Returns the URL of the generated video or None if failed/unavailable.
    """
    if not fal_available():
        return None

    if not Path(image_path).exists():
        logger.warning(f"Lip-sync skipped: Image not found at {image_path}")
        return None

    try:
        os.environ["FAL_KEY"] = _fal_key()

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        audio_uri = f"data:audio/mpeg;base64,{audio_b64}"

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        image_uri = f"data:image/{ext};base64,{img_b64}"

        preset = _fal_preset()
        avatar_mode = os.environ.get("FAL_AVATAR_MODE", "true").strip().lower()
        if avatar_mode in {"1", "true", "yes"}:
            preprocess = "full"
            still_mode = True
        else:
            preprocess = "crop"
            still_mode = False

        if preset == "fast":
            face_enhancer = None
            face_model_resolution = "256"
            expression_scale = 1.0
        elif preset == "quality":
            face_enhancer = "gfpgan"
            face_model_resolution = "512"
            expression_scale = 1.2
        else:
            face_enhancer = None
            face_model_resolution = "256"
            expression_scale = 1.1

        logger.info(
            "Submitting lip-sync job to FAL.AI (SadTalker) preset=%s, preprocess=%s",
            preset,
            preprocess,
        )

        result = fal_client.subscribe(
            "fal-ai/sadtalker",
            arguments={
                "source_image_url": image_uri,
                "driven_audio_url": audio_uri,
                "face_enhancer": face_enhancer,
                "preprocess": preprocess,
                "still_mode": still_mode,
                "expression_scale": expression_scale,
                "face_model_resolution": face_model_resolution,
            },
            with_logs=False,
        )

        if result and "video" in result:
            video_url = result["video"]["url"]
            logger.info(f"FAL.AI lip-sync generated: {video_url}")
            return video_url

    except Exception as e:
        logger.error(f"FAL.AI lip-sync failed: {e}")
        return None

    return None


def lipsync_available() -> bool:
    available = fal_available()
    if available:
        logger.info("Lip-sync provider: FAL.AI")
    else:
        logger.info("Lip-sync provider: none")
    return available


def generate_lip_sync(audio_bytes: bytes, image_path: str) -> str | None:
    """Generate a lip-sync video using FAL.AI only."""
    return _generate_lip_sync_fal(audio_bytes, image_path)
