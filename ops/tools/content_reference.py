"""Content-referenced QC calibration: compare each capture against its display asset.

Both images are resampled to 1280x720 before measuring, so Laplacian variance and
pixel clipping are resolution-independent and directly comparable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REF = (1280, 720)
CLIP_LEVEL = 250.0


def imread(path: Path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def metrics(img) -> tuple[float, float]:
    img = cv2.resize(img, REF, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clip = float((gray >= CLIP_LEVEL).mean())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return clip, blur


def main(session: str, run_dir: str, queue: str) -> int:
    q = json.loads((ROOT / queue).read_text(encoding="utf-8"))["items"]
    vals = list(q.values()) if isinstance(q, dict) else q
    assets = {int(x["seq"]): ROOT / x["file_relpath"] for x in vals}
    rows = json.loads((ROOT / run_dir / "qc.json").read_text(encoding="utf-8"))
    out = []
    for r in rows:
        if not r.get("rectified"):
            continue
        rec = imread(ROOT / r["rectified"])
        asset = imread(assets[int(r["seq"])])
        pc, pl = metrics(rec)
        ac, al = metrics(asset)
        out.append(
            {
                "seq": int(r["seq"]),
                "qc_status": r["qc_status"],
                "failure_code": r["failure_code"],
                "photo_clip": pc,
                "asset_clip": ac,
                "clip_excess": pc - ac,
                "photo_blur": pl,
                "asset_blur": al,
                "sharp_ratio": (pl / al) if al > 0 else None,
            }
        )
    dest = ROOT / "manifests" / "content_reference" / f"{session}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    ratios = sorted(x["sharp_ratio"] for x in out if x["sharp_ratio"] is not None)
    exc = sorted(x["clip_excess"] for x in out)
    print(
        f"{session}: n={len(out)} sharp_ratio p5/p50={ratios[int(len(ratios)*0.05)]:.2f}/"
        f"{ratios[len(ratios)//2]:.2f} min={ratios[0]:.2f} | clip_excess p50={exc[len(exc)//2]:.3f} "
        f"p95={exc[int(len(exc)*0.95)]:.3f} max={exc[-1]:.3f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2], sys.argv[3]))
