# VibeOS Tagger (no Groq, OpenCV only)

Photo in -> 7 values + style tag + edit values out. Separate Render service, backend pe load nahi.

## Deploy
1. Is folder ko alag repo/service banao (`render.tagger.yaml`), env `TAGGER_API_KEY` set karo.
2. Link: `https://<service>.onrender.com`

## API (header `X-API-Key`)
- `POST /analyze`        form-data `file`
- `POST /analyze/batch`  form-data `files` x N (max 12)
- `POST /analyze/url`    json `{"url": "https://..."}`

Response: `values` (7 measured), `style` (editor key), `style_label`, `style_confidence`,
`low_confidence`, `runner_up`, `style_scores`, `edit` (table range se concrete values).

## Backend me kahan lagana
Shortlist ke BAAD, editor se pehle (sirf 3 photos analyze hongi):
`client.py` ko backend me `tagger_client.py` naam se copy karo, env `TAGGER_URL`, `TAGGER_API_KEY`.
`tag = tag_photo(bytes)`; `None` aaye to purana flow chalao.

## Tuning
`python calibrate.py samples` (folders: baddie moody film clean golden mono). Rules `styles.py` me.
