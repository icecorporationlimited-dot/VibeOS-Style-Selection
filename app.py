"""VibeOS Tagger: photo in -> 7 measurements + style tag + edit values out.

Run:  uvicorn app:app --host 0.0.0.0 --port $PORT
No Groq / no AI API. Pure OpenCV, stateless, no DB.
"""
from __future__ import annotations

import asyncio
import hmac
import os
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from pydantic import BaseModel

from analyzer import measure
from styles import classify

API_KEY = os.environ.get("TAGGER_API_KEY", "")      # set it; backend sends it as X-API-Key
MAX_BYTES = int(os.environ.get("TAGGER_MAX_MB", "15")) * 1024 * 1024
MAX_BATCH = 12
pool = ThreadPoolExecutor(max_workers=int(os.environ.get("TAGGER_WORKERS", "2")))

app = FastAPI(title="VibeOS Tagger")


def auth(x_api_key: str = Header(default="")):
    if API_KEY and not hmac.compare_digest(x_api_key, API_KEY):
        raise HTTPException(401, "bad api key")


def analyze_bytes(data: bytes) -> dict:
    if len(data) > MAX_BYTES:
        raise ValueError("image too large")
    m = measure(data)
    return {"values": m["values"], "size": m["size"], **classify(m["values"], m["extras"])}


async def _run(data: bytes) -> dict:
    try:
        return await asyncio.get_running_loop().run_in_executor(pool, analyze_bytes, data)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.api_route("/", methods=["GET", "HEAD"])
def health():
    return {"ok": True, "service": "vibeos-tagger"}


@app.post("/analyze", dependencies=[Depends(auth)])
async def analyze(file: UploadFile = File(...)):
    """One photo (multipart field `file`)."""
    return await _run(await file.read())


@app.post("/analyze/batch", dependencies=[Depends(auth)])
async def analyze_batch(files: list[UploadFile] = File(...)):
    """Up to 12 photos (multipart field `files`, repeated). Order is preserved."""
    if len(files) > MAX_BATCH:
        raise HTTPException(400, f"max {MAX_BATCH} files")
    out = []
    for f in files:
        try:
            out.append({"name": f.filename, "ok": True, **await _run(await f.read())})
        except HTTPException as exc:
            out.append({"name": f.filename, "ok": False, "error": exc.detail})
    return {"results": out}


class UrlBody(BaseModel):
    url: str


@app.post("/analyze/url", dependencies=[Depends(auth)])
async def analyze_url(body: UrlBody):
    """Photo by public URL (e.g. blob/storage link)."""
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(400, "url must be http(s)")
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as c:
        r = await c.get(body.url)
    if r.status_code != 200:
        raise HTTPException(400, f"fetch failed {r.status_code}")
    return await _run(r.content)
