import os
import time
import base64
import logging
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

DID_API_URL = "https://api.d-id.com"

_uploaded_image_cache: dict[str, str] = {}


def _get_headers() -> dict:
    api_key = os.environ.get("DID_API_KEY", "")
    if not api_key:
        raise ValueError("DID_API_KEY not set.")
    return {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }


def is_available() -> bool:
    return bool(os.environ.get("DID_API_KEY", ""))


def upload_image(image_path: str) -> str | None:
    """Upload a local image to D-ID and return its hosted URL.
    Results are cached so each image is uploaded only once per session."""
    if image_path in _uploaded_image_cache:
        return _uploaded_image_cache[image_path]

    api_key = os.environ.get("DID_API_KEY", "")
    if not api_key:
        return None

    p = Path(image_path)
    if not p.exists():
        logger.warning("Image file not found: %s", image_path)
        return None

    try:
        headers = {"Authorization": f"Basic {api_key}"}
        with open(p, "rb") as f:
            resp = requests.post(
                f"{DID_API_URL}/images",
                headers=headers,
                files={"image": (p.name, f, "image/png")},
                timeout=30,
            )
        resp.raise_for_status()
        url = resp.json().get("url")
        if url:
            _uploaded_image_cache[image_path] = url
            logger.info("Uploaded %s → %s", image_path, url)
        return url
    except Exception as e:
        logger.error("D-ID image upload failed: %s", e)
        return None


def create_talk(source_url: str, text: str, voice_id: str = "en-IN-PrabhatNeural") -> str | None:
    """Create a D-ID talk video. Returns the talk ID."""
    try:
        payload = {
            "source_url": source_url,
            "script": {
                "type": "text",
                "input": text,
                "provider": {
                    "type": "microsoft",
                    "voice_id": voice_id,
                },
            },
        }
        resp = requests.post(
            f"{DID_API_URL}/talks",
            json=payload,
            headers=_get_headers(),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        talk_id = data.get("id")
        logger.info("D-ID talk created: %s (status: %s)", talk_id, data.get("status"))
        return talk_id
    except Exception as e:
        logger.error("D-ID create_talk failed: %s", e)
        return None


def poll_talk(talk_id: str, timeout: int = 60) -> str | None:
    """Poll a talk until done. Returns the result MP4 URL or None on timeout."""
    headers = _get_headers()
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            resp = requests.get(
                f"{DID_API_URL}/talks/{talk_id}",
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status")

            if status == "done":
                result_url = data.get("result_url")
                logger.info("D-ID talk %s done: %s", talk_id, result_url)
                return result_url
            elif status in ("error", "rejected"):
                logger.error("D-ID talk %s failed: %s", talk_id, data)
                return None

            time.sleep(2)
        except Exception as e:
            logger.error("D-ID poll error: %s", e)
            time.sleep(2)

    logger.warning("D-ID talk %s timed out after %ds", talk_id, timeout)
    return None


def generate_talking_video(
    image_path: str,
    text: str,
    voice_id: str = "en-IN-PrabhatNeural",
) -> str | None:
    """End-to-end: upload image → create talk → poll → return MP4 URL."""
    if not is_available():
        return None

    source_url = upload_image(image_path)
    if not source_url:
        return None

    # Trim text to ~500 chars to keep video short and generation fast
    if len(text) > 500:
        text = text[:497] + "..."

    talk_id = create_talk(source_url, text, voice_id)
    if not talk_id:
        return None

    return poll_talk(talk_id)
