"""Table -> style rules. Edit RANGES / PROFILES to tune; no other file needs to change."""
from __future__ import annotations

# (table name, editor.py style key). Soft Film maps to "film"; Mono has no editor
# style yet -> add "mono" to editor.STYLES or change the key below (e.g. "moody").
STYLES = {
    "y2k":      ("Y2K / Digicam Flash", "baddie"),
    "moody":    ("Cinematic Moody", "moody"),
    "film":     ("Soft Film / Vintage", "film"),
    "clean":    ("Clean Editorial", "clean"),
    "golden":   ("Golden Hour Glow", "golden"),
    "mono":     ("Monochrome / B&W", "mono"),
}

# The table, exactly: edit ranges to APPLY per style. exposure is in EV stops.
RANGES = {
    "y2k":    dict(exposure=(0.1, 0.5),  contrast=(10, 25), highlights=(-20, 0),  shadows=(-5, 10),  saturation=(0, 10),   warmth=(-3, 5),  grain=(10, 22)),
    "moody":  dict(exposure=(-0.2, 0.2), contrast=(15, 30), highlights=(-30, -10), shadows=(-15, 5), saturation=(-10, 5),  warmth=(-5, 3),  grain=(3, 10)),
    "film":   dict(exposure=(0.1, 0.4),  contrast=(-10, 5), highlights=(-35, -15), shadows=(10, 25), saturation=(-15, 0),  warmth=(5, 15),  grain=(8, 18)),
    "clean":  dict(exposure=(0.1, 0.4),  contrast=(5, 15),  highlights=(-35, -15), shadows=(10, 25), saturation=(-5, 5),   warmth=(-3, 5),  grain=(0, 5)),
    "golden": dict(exposure=(0.1, 0.5),  contrast=(-5, 10), highlights=(-25, -5),  shadows=(5, 20),  saturation=(5, 15),   warmth=(10, 25), grain=(0, 8)),
    "mono":   dict(exposure=(-0.1, 0.3), contrast=(20, 35), highlights=(-30, -10), shadows=(-10, 10), saturation=(-100, -100), warmth=(0, 0), grain=(5, 15)),
}

# What each style looks like in a photo that SUITS it, in measured units.
# feature: (zero_below, full_from, full_to, zero_above, weight)  -> trapezoid.
PROFILES = {
    "mono":   dict(sat_mean=(-1, 0, 14, 30, 6), contrast=(-10, 10, 70, 100, 1)),
    "golden": dict(warmth=(5, 18, 80, 100, 8), saturation=(-15, 0, 60, 90, 2),
                   exposure=(-40, -15, 35, 60, 1), highlights=(-45, -25, 30, 60, 1)),
    "moody":  dict(exposure=(-80, -50, -12, 8, 3), shadows=(-60, -45, -8, 12, 3),
                   contrast=(-5, 15, 60, 90, 2), saturation=(-70, -45, 5, 35, 1),
                   warmth=(-40, -25, 8, 25, 1)),
    "y2k":    dict(contrast=(15, 35, 100, 120, 3), shadows=(-70, -45, -10, 8, 2),
                   highlights=(-15, 5, 60, 90, 2), grain=(8, 20, 70, 100, 3),
                   saturation=(-10, 5, 50, 80, 1)),
    "film":   dict(contrast=(-60, -35, 5, 25, 3), shadows=(-15, 0, 30, 50, 2),
                   saturation=(-60, -35, 0, 25, 2), warmth=(-2, 5, 25, 45, 2),
                   grain=(4, 12, 45, 70, 2)),
    "clean":  dict(exposure=(-10, 5, 45, 70, 3), contrast=(-40, -15, 25, 50, 2),
                   saturation=(-60, -35, 5, 30, 2), warmth=(-25, -8, 12, 30, 2),
                   grain=(-1, 0, 14, 30, 2), shadows=(-10, 5, 40, 60, 1)),
}

NATURAL = "natural"       # fallback when nothing fits well (exists in editor.STYLES)
MIN_SCORE = 45            # best style below this -> natural
MIN_MARGIN = 4            # best vs runner-up closer than this -> low confidence


def _trap(x, a, b, c, d):
    if x <= a or x >= d:
        return 0.0
    if b <= x <= c:
        return 1.0
    return (x - a) / (b - a) if x < b else (d - x) / (d - c)


def score_styles(values: dict, extras: dict) -> dict:
    feats = {**values, **extras}
    out = {}
    for key, prof in PROFILES.items():
        tot = w = 0.0
        for f, (a, b, c, d, wt) in prof.items():
            tot += wt * _trap(feats[f], a, b, c, d)
            w += wt
        out[key] = round(100 * tot / w, 1)
    return out


def _pick(lo, hi, t):
    return lo + (hi - lo) * max(0.0, min(1.0, t))


def edit_plan(key: str, values: dict) -> dict:
    """Table range -> one concrete number per parameter, nudged by what the photo needs."""
    R = RANGES[key]
    dark = (-values["exposure"] + 20) / 60           # 0 bright .. 1 dark
    flat = (-values["contrast"] + 20) / 60           # 0 punchy .. 1 flat
    hot = (values["highlights"] + 20) / 40           # 0 safe .. 1 bright highlights
    murky = (-values["shadows"] + 10) / 40           # 0 open .. 1 crushed
    plan = {
        "exposure": _pick(*R["exposure"], dark),
        "contrast": _pick(*R["contrast"], flat),
        "highlights": _pick(*R["highlights"][::-1], hot),   # brighter highlights -> pull harder
        "shadows": _pick(*R["shadows"], murky),
        "saturation": _pick(*R["saturation"], 0.5 - values["saturation"] / 80),
        "warmth": _pick(*R["warmth"], 0.5 - values["warmth"] / 60),
        "grain": _pick(*R["grain"][::-1], values["grain"] / 40),  # already grainy -> add less
    }
    return {k: round(v, 2) if k == "exposure" else int(round(v)) for k, v in plan.items()}


def classify(values: dict, extras: dict) -> dict:
    scores = score_styles(values, extras)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (best, s1), (second, s2) = ranked[0], ranked[1]
    margin = s1 - s2
    fallback = s1 < MIN_SCORE
    key = NATURAL if fallback else best
    confidence = int(max(0, min(100, s1 * 0.6 + min(margin, 25) * 1.6)))
    res = {
        "style": STYLES[key][1] if key in STYLES else NATURAL,
        "style_label": STYLES[key][0] if key in STYLES else "Natural (no strong match)",
        "style_confidence": confidence if not fallback else min(confidence, 40),
        "low_confidence": fallback or margin < MIN_MARGIN,
        "runner_up": STYLES[second][1],
        "style_scores": {STYLES[k][1]: v for k, v in scores.items()},
    }
    if not fallback:
        res["edit"] = edit_plan(key, values)
    return res
