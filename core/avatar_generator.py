"""
Generate a stylised AI avatar from a user's photo.

Uses Gemini 2.5 Flash Image (google-genai SDK) as the primary method,
with a Pillow-based artistic filter as a fast offline fallback.
"""

import io
import os
import logging
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw

log = logging.getLogger(__name__)

AVATAR_PROMPT = """\
Transform the provided input photo into a high-quality stylized digital avatar \
while preserving the person's core facial identity.

Identity Preservation Rules:
- Maintain accurate facial structure, eye spacing, nose shape, and mouth shape
- Keep hairstyle and hairline recognizable
- Preserve skin tone naturally (do NOT lighten or darken unnaturally)
- Do NOT change gender, age group, or ethnicity
- Remove temporary blemishes only (pimples, shine), but keep natural skin texture

Style Requirements:
- Style: modern premium 3D semi-realistic avatar
- Vibe: friendly, confident, professional, visually appealing
- Lighting: soft cinematic studio lighting
- Background: clean gradient or subtle tech background
- Expression: slight natural smile, approachable
- Framing: centered head and shoulders portrait
- Quality: ultra sharp, high detail, commercial quality

Enhancements (allowed):
- improve lighting and clarity
- smooth minor skin imperfections
- slightly enhance eyes for liveliness
- clean up flyaway hair

Strict Safety Rules:
- no exaggeration or caricature
- no extreme beautification
- no race or skin tone alteration
- no extra limbs or distorted anatomy
- no text, watermark, or logo

Output a single polished avatar image suitable for use in an interactive AI booth experience.\
"""


def _gemini_generate(photo_bytes: bytes) -> bytes | None:
    """Attempt avatar generation via Gemini 2.5 Flash Image model."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        log.warning("GOOGLE_API_KEY not set — skipping Gemini avatar generation")
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        upload_image = types.Part.from_bytes(
            data=photo_bytes,
            mime_type="image/png",
        )

        log.info("Calling Gemini 2.5 Flash image generation…")
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[AVATAR_PROMPT, upload_image],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        if not response.candidates:
            log.warning("Gemini returned no candidates")
            return None

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                log.info("Gemini avatar generated successfully (%d bytes)", len(part.inline_data.data))
                return part.inline_data.data

        log.warning("Gemini response had no image parts")

    except Exception as exc:
        log.error("Gemini avatar generation failed: %s", exc)

    return None


def _pillow_stylise(photo_bytes: bytes) -> bytes:
    """
    Offline fallback: create a stylised avatar using Pillow filters.
    Applies a dark cinematic colour grade with an orange accent glow.
    """
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    size = 512
    img = img.resize((size, size), Image.LANCZOS)

    rgb = img.convert("RGB")

    rgb = ImageEnhance.Contrast(rgb).enhance(1.3)
    rgb = ImageEnhance.Color(rgb).enhance(0.75)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.85)

    tint = Image.new("RGB", (size, size), (12, 8, 22))
    rgb = Image.blend(rgb, tint, alpha=0.25)

    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse([0, 0, size, size], fill=255)

    edges = rgb.filter(ImageFilter.FIND_EDGES)
    edges = ImageEnhance.Brightness(edges).enhance(0.4)
    glow_tint = Image.new("RGB", (size, size), (242, 101, 34))
    glow = Image.blend(edges, glow_tint, alpha=0.6)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=6))

    final_rgb = Image.composite(rgb, glow, mask)
    vignette = Image.new("L", (size, size), 0)
    vd = ImageDraw.Draw(vignette)
    for i in range(size // 2):
        alpha = int(255 * (i / (size // 2)) ** 1.8)
        vd.ellipse(
            [size // 2 - i, size // 2 - i, size // 2 + i, size // 2 + i],
            fill=alpha,
        )
    final_rgb.putalpha(vignette)

    bg = Image.new("RGBA", (size, size), (6, 6, 11, 255))
    bg.paste(final_rgb, (0, 0), final_rgb)

    ring = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for t in range(4):
        offset = t
        opacity = max(60 - t * 15, 10)
        rd.ellipse(
            [offset, offset, size - 1 - offset, size - 1 - offset],
            outline=(242, 101, 34, opacity),
        )
    bg = Image.alpha_composite(bg, ring)

    out = io.BytesIO()
    bg.convert("RGB").save(out, format="PNG", quality=95)
    return out.getvalue()


def generate_avatar(photo_bytes: bytes) -> tuple[bytes, str]:
    """
    Generate a stylised avatar from a raw photo.

    Returns (image_bytes, method) where method is 'gemini' or 'stylised'.
    """
    ai_result = _gemini_generate(photo_bytes)
    if ai_result:
        return ai_result, "gemini"

    return _pillow_stylise(photo_bytes), "stylised"


def save_avatar(avatar_bytes: bytes, name: str) -> str:
    """Save avatar bytes to disk and return the file path."""
    safe = "".join(c if c.isalnum() else "_" for c in name.strip().lower()) or "visitor"
    out_dir = Path("assets/visitors")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{safe}_avatar.png"
    path.write_bytes(avatar_bytes)
    return str(path)
