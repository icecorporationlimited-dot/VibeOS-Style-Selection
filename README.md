# VIBEOS Automatic Photo Style Tagger

This service analyzes a photo's measurable image properties and selects one internal editing style.
It does not display styles to users, edit images, store uploads, or return alternate previews. The
VIBEOS backend passes the chosen style into its adaptive photo renderer and delivers only one final image.

## Deploy to Render
1. Push this folder to a separate GitHub repository, or deploy it as a service from your existing repository.
2. Use `render.tagger.yaml` as the Blueprint.
3. Render generates `TAGGER_API_KEY`. Copy that exact value into the main VIBEOS web service and the
   VIBEOS photo worker as `TAGGER_API_KEY`.
4. Set `TAGGER_URL` on both VIBEOS services to the tagger's public HTTPS base URL (without a trailing slash).

## Endpoints
- `GET /` — health check
- `POST /analyze` — multipart field `file`, header `X-API-Key` required
- `POST /analyze/batch` — repeated multipart `files`, maximum 12 images
- `POST /analyze/url` — JSON `{"url":"https://..."}`, header `X-API-Key` required

The service measures exposure, contrast, highlights, shadows, saturation, warmth and estimated noise.
A rules-based ranker returns one style, confidence, a runner-up and a bounded edit plan. It uses OpenCV
and NumPy, has no Groq/LLM dependency, and is stateless. If the service is unavailable, the main editor
falls back to its built-in pixel-based style selection.

## Local run
```bash
pip install -r requirements.txt
export TAGGER_API_KEY='replace-with-a-long-random-secret'
uvicorn app:app --host 0.0.0.0 --port 10000
```

The numeric profile ranges are initial tuning values; validate with a diverse, permissioned test set.
