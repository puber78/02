"""Geometry/glare diagnostics on raw physical captures (any session).

For each capture: re-estimate the screen homography, map the display canvas
corners into the photo, and report
  * screen_area_fraction : screen quad area / photo area (framing)
  * max_corner_dev_deg   : deviation of the projected quad's corners from 90 deg
  * glare_fraction       : fraction of content pixels with luma > 235 (washout)
  * p99_luma             : 99th percentile luma inside the content

Usage
-----
  python ops/tools/geometry_diagnostics.py --run manifests/EXAM02_captures/<run> \
      [--queue captures/kit/queue_main_s1.json] [--out <run>/geometry_diagnostics.json]
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


def orb(gray):
    return cv2.ORB_create(nfeatures=5000, fastThreshold=12).detectAndCompute(gray, None)


def homography(disp, photo):
    g1, g2 = cv2.cvtColor(disp, cv2.COLOR_BGR2GRAY), cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    k1, d1 = orb(g1)
    k2, d2 = orb(g2)
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


def load_queue(path: Path) -> dict[int, dict]:
    data = json.loads(path.read_text("utf-8"))
    items = data["items"] if isinstance(data, dict) else data
    if isinstance(items, dict):
        return {int(k): v for k, v in items.items()}
    return {int(it["seq"]): it for it in items}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="manifests/EXAM02_captures/<run_id>")
    ap.add_argument("--queue", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    run = (ROOT / args.run).resolve()
    qc = json.loads((run / "qc.json").read_text("utf-8"))
    qpath = Path(args.queue) if args.queue else ROOT / "captures" / "kit" / "queue_tech.json"
    queue = load_queue(qpath if qpath.is_absolute() else ROOT / qpath)

    rows = []
    for rec in qc:
        if not rec.get("file"):
            continue
        it = queue.get(int(rec["seq"]))
        if it is None:
            continue
        disp = imread_u(ROOT / it["file_relpath"])
        photo = imread_u(ROOT / rec["file"])
        if disp is None or photo is None:
            continue
        H, inl = homography(disp, photo)
        if H is None:
            continue
        h, w = photo.shape[:2]
        corners = np.float32(
            [[0, 0], [disp.shape[1], 0], [disp.shape[1], disp.shape[0]], [0, disp.shape[0]]]
        ).reshape(-1, 1, 2)
        proj = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
        area = 0.5 * abs(
            np.dot(proj[:, 0], np.roll(proj[:, 1], 1)) - np.dot(proj[:, 1], np.roll(proj[:, 0], 1))
        )
        warped = cv2.warpPerspective(photo, np.linalg.inv(H), (disp.shape[1], disp.shape[0]))
        g = it.get("geometry") or {
            "content_x": 0, "content_y": 0, "content_w": disp.shape[1], "content_h": disp.shape[0]
        }
        crop = warped[g["content_y"] : g["content_y"] + g["content_h"],
                      g["content_x"] : g["content_x"] + g["content_w"]]
        luma = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        rows.append(
            {
                "seq": rec["seq"],
                "screen_area_fraction": round(float(area / (w * h)), 3),
                "max_corner_dev_deg": round(float(corner_angles(proj)), 1),
                "glare_fraction_gt235": round(float((luma > 235).mean()), 4),
                "p99_luma": int(np.percentile(luma, 99)),
                "inliers": inl,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        print("no rows")
        return 1
    print(df.to_string(index=False))
    print(
        "\nmean screen area:", round(df.screen_area_fraction.mean(), 3),
        "| median corner dev:", round(df.max_corner_dev_deg.median(), 1),
        "| median glare:", round(df.glare_fraction_gt235.median(), 4),
        "| area min/max:", df.screen_area_fraction.min(), df.screen_area_fraction.max(),
    )
    out = Path(args.out) if args.out else run / "geometry_diagnostics.json"
    out = out if out.is_absolute() else ROOT / out
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("written", out.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
