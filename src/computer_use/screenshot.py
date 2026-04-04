"""Cross-platform screenshot capture using Pillow."""

import base64
import io
import sys

from PIL import Image, ImageGrab


def _jpeg_from_pil(img: Image.Image) -> bytes:
    """Convert PIL image to JPEG bytes. Converts RGBA to RGB if needed."""
    if img.mode == "RGBA":
        img = img.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def capture_screen() -> bytes:
    """Capture the primary display and return JPEG bytes."""
    if sys.platform == "darwin":
        import subprocess

        try:
            proc = subprocess.run(
                ["screencapture", "-x", "-t", "jpg", "-"],
                capture_output=True,
                check=True,
            )
            # Even with exit 0, screencapture can return 0 bytes on permission/display issues
            if len(proc.stdout) > 1000:
                return proc.stdout
        except subprocess.CalledProcessError:
            pass

    # Windows / Linux, or macOS fallback: use PIL ImageGrab
    img: Image.Image = ImageGrab.grab()
    return _jpeg_from_pil(img)


def capture_screen_base64() -> str:
    """Capture screen and return base64-encoded JPEG string (no data URI prefix)."""
    jpeg_bytes = capture_screen()
    return base64.b64encode(jpeg_bytes).decode("utf-8")


def capture_screen_pil() -> Image.Image:
    """Capture screen and return a PIL Image object."""
    if sys.platform == "darwin":
        import subprocess

        try:
            proc = subprocess.run(
                ["screencapture", "-x", "-t", "jpg", "-"],
                capture_output=True,
                check=True,
            )
            if len(proc.stdout) > 1000:
                buf = io.BytesIO(proc.stdout)
                return Image.open(buf)
        except subprocess.CalledProcessError:
            pass

    return ImageGrab.grab()
