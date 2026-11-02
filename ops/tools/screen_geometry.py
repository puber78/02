"""Recompute true screen-framing geometry for an import run and (optionally) patch qc.json.

Why
---
Until 2026-10-30 `scripts/import_captures.py` stored in ``screen_coverage`` the area of the
display-side content rectangle divided by the canvas area.  That is a layout constant of the
display asset (0.5625 for a 4:3 content rect in a 16:9 canvas), not a property of the photo,
and it must never be quoted as capture framing.  This tool recomputes, per capture, from the
display asset and the original photo:

  screen_area_fraction     projected screen quad / photo area (can exceed 1 -> screen cut off)
  screen_visible_fraction  (quad INTERSECT frame) / photo area  (honest framing number)
  content_rect_frac        content rect / canvas (layout constant, kept for traceability)
  corner_dev_deg           max deviation of projected corners from 90 deg

It writes ``screen_geometry.json`` next to qc.json and, with ``--patch-qc``, archives the old
qc.json to ops/archive/ and rewrites the metrics in place (same capture_ids, no re-import).

Usage
-----
  python ops/tools/screen_geometry.py --run manifests/EXAM02_captures/<run> --patch-qc
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def imread_u(path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def orb(gray):
    return cv2.ORB_create(nfeatures=5000, fastThreshold=12).detectAndCompute(gray, None)


def homography(disp, photo):
    g1 = cv2.cvtColor(disp, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    k1, d1 = orb(g1)
    k2, d2 = orb(g2)
    if d1 is None or d2 is None or len(d1) < 8 or len(d2) < 8:
        return None, 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = bf.knnMatch(d1, d2, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
    if len(good) < 8:
        return None, len(good)
    src = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    return H, int(mask.sum()) if mask is not None else 0


def corner_angles(quad):
    angs = []
    for i in range(4):
        a, b, c = quad[(i - 1) % 4], quad[i], quad[(i + 1) % 4]
        v1, v2 = a - b, c - b
        cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        angs.append(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
    return max(abs(a - 90.0) for a in angs)


def load_items(path: Path) -> dict[int, dict]:
    data = json.loads(path.read_text("utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    if isinstance(items, dict):
        return {int(k): v for k, v in items.items()}
    return {int(it["seq"]): it for it in items}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--queue", default=None, help="defaults to captures/kit/queue_<session>.json")
    ap.add_argument("--out", default=None)
    ap.add_argument("--patch-qc", action="store_true")
    args = ap.parse_args()

    run = (ROOT / args.run).resolve()
    qc = json.loads((run / "qc.json").read_text("utf-8"))
    summary = json.loads((run / "import_summary.json").read_text("utf-8"))
    session = summary["session"]
    qpath = Path(args.queue) if args.queue else ROOT / "captures" / "kit" / f"queue_{session}.json"
    items = load_items(qpath)

    rows, missing = [], []
    for rec in qc:
        seq = int(rec["seq"])
        if not rec.get("file"):
            missing.append(seq)
            continue
        it = items.get(seq)
        if it is None:
            missing.append(seq)
            continue
        disp = imread_u(ROOT / it["file_relpath"])
        photo = imread_u(ROOT / rec["file"])
        if disp is None or photo is None:
            missing.append(seq)
            continue
        H, inl = homography(disp, photo)
        if H is None:
            missing.append(seq)
            continue
        ph, pw = photo.shape[:2]
        ch, cw = disp.shape[:2]
        geom = it.get("geometry") or {"content_x": 0, "content_y": 0, "content_w": cw, "content_h": ch}
        corners = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]]).reshape(-1, 1, 2)
        quad = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
        quad_area = float(abs(cv2.contourArea(quad.astype(np.float32))))
        rect = np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]])
        inter_area, _ = cv2.intersectConvexConvex(quad, rect)
        rows.append(
            {
                "seq": seq,
                "capture_id": rec.get("capture_id"),
                "screen_area_fraction": round(quad_area / (pw * ph), 4),
                "screen_visible_fraction": round(float(inter_area) / (pw * ph), 4),
                "content_rect_frac": round(float(geom["content_w"] * geom["content_h"]) / (cw * ch), 4),
                "corner_dev_deg": round(float(corner_angles(quad)), 2),
                "inliers": inl,
                "photo_w": pw,
                "photo_h": ph,
                "quad_min_x": round(float(quad[:, 0].min()), 1),
                "quad_max_x": round(float(quad[:, 0].max()), 1),
                "quad_min_y": round(float(quad[:, 1].min()), 1),
                "quad_max_y": round(float(quad[:, 1].max()), 1),
            }
        )

    df = pd.DataFrame(rows).sort_values("seq")
    out = Path(args.out) if args.out else run / "screen_geometry.json"
    out = out if out.is_absolute() else ROOT / out
    out.write_text(df.to_json(orient="records", indent=2, force_ascii=False), encoding="utf-8")

    print(df[["seq", "screen_area_fraction", "screen_visible_fraction",
              "content_rect_frac", "corner_dev_deg"]].head(8).to_string(index=False))
    print(
        f"\nrows {len(df)} | missing {missing}\n"
        f"area     min {df.screen_area_fraction.min():.3f} median {df.screen_area_fraction.median():.3f} "
        f"max {df.screen_area_fraction.max():.3f}\n"
        f"visible  min {df.screen_visible_fraction.min():.3f} median {df.screen_visible_fraction.median():.3f} "
        f"max {df.screen_visible_fraction.max():.3f}\n"
        f"content  {sorted(df.content_rect_frac.unique())}\n"
        f"corner   median {df.corner_dev_deg.median():.2f} max {df.corner_dev_deg.max():.2f}"
    )

    if args.patch_qc:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        arch = ROOT / "ops" / "archive" / f"qc_{run.name}_before_geometry_fix_{stamp}.json"
        arch.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(run / "qc.json", arch)
        by_seq = {int(r["seq"]): r for r in rows}
        for rec in qc:
            r = by_seq.get(int(rec["seq"]))
            if r is None:
                continue
            rec["screen_area_fraction"] = r["screen_area_fraction"]
            rec["screen_visible_fraction"] = r["screen_visible_fraction"]
            rec["content_rect_frac"] = r["content_rect_frac"]
            rec["corner_dev_deg"] = r["corner_dev_deg"]
            rec["screen_coverage"] = r["screen_visible_fraction"]
        (run / "qc.json").write_text(json.dumps(qc, indent=2, ensure_ascii=False), encoding="utf-8")
        print("archived old qc.json ->", arch.relative_to(ROOT))
        print("patched", run.name, "/qc.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
