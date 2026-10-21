"""7 measurements from a photo using OpenCV only (no AI API, no network)."""
from __future__ import annotations

import cv2
import numpy as np

MAX_SIDE = 768  # fixed analysis size: fast, and makes grain/noise comparable


def decode(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Not a readable image")
    h, w = img.shape[:2]
    scale = MAX_SIDE / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def _noise_sigma(gray: np.ndarray) -> float:
    """Immerkaer fast noise estimate (std-dev in 0-255 units).

    Unlike Laplacian variance, this ignores real edges, so a sharp photo is not
    mistaken for a noisy one and a blurry photo is not mistaken for a grainy one.
    """
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], dtype=np.float32)
    conv = cv2.filter2D(gray.astype(np.float32), -1, k)
    h, w = gray.shape
    return float(np.sqrt(np.pi / 2) * np.abs(conv[1:-1, 1:-1]).sum() / (6.0 * (w - 2) * (h - 2)))


def measure(data: bytes) -> dict:
    img = decode(data)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b, g, r = cv2.split(img)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    mean_l = float(gray.mean())
    std_l = float(gray.std())
    p5, p10, p90, p95 = (float(np.percentile(gray, p)) for p in (5, 10, 90, 95))
    sat_mean = float(hsv[:, :, 1].mean())
    warm_raw = (float(r.mean()) - float(b.mean())) / 1.5
    noise = _noise_sigma(gray)

    values = {  # the 7 table parameters, as measured on the photo
        "exposure": (mean_l - 128) / 1.28,
        "contrast": (std_l - 50) * 1.8,
        "highlights": p90 - 190,
        "shadows": p10 - 50,
        "saturation": sat_mean - 90,
        "warmth": warm_raw,
        "grain": noise * 12,           # sigma 0->0, ~3 (visible grain)->36, ~8->96
    }
    values = {k: int(np.clip(v, 0 if k == "grain" else -100, 100)) for k, v in values.items()}

    extras = {  # helpers for style matching, not part of the 7
        "sat_mean": round(sat_mean, 1),
        "p5": round(p5, 1), "p95": round(p95, 1),
        "dark_ratio": round(float((gray < 40).mean()), 3),
        "bright_ratio": round(float((gray > 215).mean()), 3),
        "noise_sigma": round(noise, 2),
    }
    return {"values": values, "extras": extras, "size": list(img.shape[1::-1])}
