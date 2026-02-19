"""Wav2Lip lip-sync client — generates talking avatar videos locally on GPU.

Requires:  pip install lipsync torch torchvision
Weights:   auto-downloaded from HuggingFace on first run (~400 MB).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

WEIGHTS_DIR = Path("weights")
VIDEOS_DIR = Path("assets/videos")
WAV2LIP_URL = (
    "https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip.pth"
)

_lip = None


def _ensure_dirs():
    WEIGHTS_DIR.mkdir(exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)


def _download_weights() -> str:
    model_path = WEIGHTS_DIR / "wav2lip.pth"
    if model_path.exists():
        return str(model_path)
    _ensure_dirs()
    logger.info("Downloading Wav2Lip model weights …")
    import urllib.request

    urllib.request.urlretrieve(WAV2LIP_URL, str(model_path))
    logger.info("Model saved → %s", model_path)
    return str(model_path)


def _get_lip():
    """Lazy-init the LipSync model (heavy — loaded only once per process)."""
    global _lip
    if _lip is not None:
        return _lip

    from lipsync import LipSync

    checkpoint = _download_weights()
    _lip = LipSync(
        model="wav2lip",
        checkpoint_path=checkpoint,
        device="cuda",
        nosmooth=True,
    )
    return _lip


def is_available() -> bool:
    try:
        import lipsync  # noqa: F401
        return True
    except ImportError:
        return False


def generate_talking_video(image_path: str, audio_path: str) -> str | None:
    """Image + WAV audio → lip-synced MP4 (local path). None on failure."""
    if not is_available():
        logger.warning("lipsync package not installed — pip install lipsync")
        return None

    _ensure_dirs()
    stem = Path(image_path).stem
    output = str(VIDEOS_DIR / f"{stem}_talk.mp4")

    try:
        lip = _get_lip()
        lip.sync(image_path, audio_path, output)
        out_path = Path(output)
        if out_path.exists() and out_path.stat().st_size > 0:
            logger.info("Lip-sync video → %s", output)
            return output
        logger.warning("Wav2Lip produced empty output")
    except Exception as e:
        logger.error("Wav2Lip generation failed: %s", e)

    return None
