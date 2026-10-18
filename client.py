"""Drop into VIBEOS-Backend. Calls the tagger service; never raises.

    from tagger_client import tag_photo
    tag = tag_photo(image_bytes)          # None if service is down -> use old path
    if tag: style = tag["style"]; edit = tag["edit"]

Env: TAGGER_URL (e.g. https://vibeos-tagger.onrender.com), TAGGER_API_KEY
"""
import logging
import os

import httpx

logger = logging.getLogger(__name__)
_URL = os.environ.get("TAGGER_URL", "").rstrip("/")
_KEY = os.environ.get("TAGGER_API_KEY", "")


def tag_photo(image_bytes: bytes, timeout: float = 20.0) -> dict | None:
    if not _URL:
        return None
    try:
        r = httpx.post(f"{_URL}/analyze", headers={"X-API-Key": _KEY},
                       files={"file": ("photo.jpg", image_bytes, "image/jpeg")}, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        logger.warning("tagger unavailable, falling back", exc_info=True)
        return None


def tag_batch(photos: list[bytes], timeout: float = 60.0) -> list[dict | None]:
    """photos -> list of results in the same order (None where it failed)."""
    if not _URL or not photos:
        return [None] * len(photos)
    try:
        r = httpx.post(f"{_URL}/analyze/batch", headers={"X-API-Key": _KEY},
                       files=[("files", (f"p{i}.jpg", b, "image/jpeg")) for i, b in enumerate(photos)],
                       timeout=timeout)
        r.raise_for_status()
        return [x if x.get("ok") else None for x in r.json()["results"]]
    except Exception:
        logger.warning("tagger batch unavailable", exc_info=True)
        return [None] * len(photos)
