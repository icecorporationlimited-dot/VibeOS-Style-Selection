"""Check accuracy on YOUR photos.  Layout:  samples/<style>/*.jpg
style folder names: baddie moody film clean golden mono   (editor keys)

    python calibrate.py samples        -> accuracy + confusion + each miss
Tune styles.PROFILES until the misses make sense, then redeploy.
"""
import sys, pathlib, collections
from analyzer import measure
from styles import classify

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "samples")
conf = collections.defaultdict(collections.Counter)
ok = n = 0
for d in sorted(p for p in root.iterdir() if p.is_dir()):
    for f in d.glob("*"):
        if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        m = measure(f.read_bytes())
        r = classify(m["values"], m["extras"])
        conf[d.name][r["style"]] += 1
        n += 1; ok += r["style"] == d.name
        if r["style"] != d.name:
            print(f"MISS {d.name}/{f.name} -> {r['style']} {r['style_scores']} {m['values']}")
print(f"\naccuracy {ok}/{n}")
for k, v in conf.items():
    print(f"{k:8s}", dict(v))
