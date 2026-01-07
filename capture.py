"""Screenshot capture utilities for Multichart v4."""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from chrome import ChromeCDP
from config import CROP_H, CROP_W, CROP_X, CROP_Y


def capture_retina_png(chrome: ChromeCDP, target_id: str, output_path: str) -> str:
    """Capture a PNG screenshot and apply the configured crop."""
    encoded = chrome.capture_screenshot_sync(target_id)
    raw = base64.b64decode(encoded)
    image = Image.open(BytesIO(raw))
    cropped = image.crop((CROP_X, CROP_Y, CROP_X + CROP_W, CROP_Y + CROP_H))

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    cropped.save(destination, format="PNG")
    return str(destination)
