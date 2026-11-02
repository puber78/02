"""Verify mapping/crop: compare each rectified capture with its expected display crop.

content_match = zero-normalised cross-correlation on 192x192 grayscale thumbnails.
High values mean the photo really shows the queued asset and the crop is aligned.

Usage
-----
  python ops/tools/content_match.py --run manifests/EXAM02_captures/<run> \
      [--queue captures/kit/queue_main_s1.json]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def imread_u(path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def thumb(img, size=192):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, (size, size), interpolation=cv2.INTER_AREA)
    g = g.astype(np.float32)
    g -= g.mean()
    sd = g.std()
    return g / sd if sd > 0 else g


def ncc(a, b):
    return float((a * b).mean())


def load_items(path: Path) -> dict[int, dict]:
    data = json.loads(path.read_text("utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    if isinstance(items, dict):
        return {int(k): v for k, v in items.items()}
    return {int(it["seq"]): it for it in items}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--queue", default=None)
    args = ap.parse_args()

    run = (ROOT / args.run).resolve()
    qc = {r["seq"]: r for r in json.loads((run / "qc.json").read_text("utf-8"))}
    qpath = Path(args.queue) if args.queue else ROOT / "captures" / "kit" / "queue_tech.json"
    items = load_items(qpath if qpath.is_absolute() else ROOT / qpath)

    rows = []
    for seq, rec in sorted(qc.items()):
        it = items.get(int(seq))
        if it is None or not rec.get("rectified"):
            rows.append({"seq": seq, "content_match": None, "note": "missing"})
            continue
        cap = imread_u(ROOT / rec["rectified"])
        disp = imread_u(ROOT / it["file_relpath"])
        if cap is None or disp is None:
            rows.append({"seq": seq, "content_match": None, "note": "missing"})
            continue
        g = it.get("geometry") or {
            "content_x": 0, "content_y": 0, "content_w": disp.shape[1], "content_h": disp.shape[0]
        }
        crop = disp[g["content_y"] : g["content_y"] + g["content_h"],
                    g["content_x"] : g["content_x"] + g["content_w"]]
        rows.append(
            {
                "seq": seq,
                "label": rec.get("label"),
                "content_match": round(ncc(thumb(cap), thumb(crop)), 4),
                "cap_size": f"{cap.shape[1]}x{cap.shape[0]}",
                "crop_size": f"{crop.shape[1]}x{crop.shape[0]}",
            }
        )

    df = pd.DataFrame(rows).sort_values("content_match")
    print(df.to_string(index=False))
    valid = df.dropna(subset=["content_match"])
    print("\nmin/median:", valid.content_match.min(), valid.content_match.median(), "n =", len(valid))
    out = run / "content_match.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("written", out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
