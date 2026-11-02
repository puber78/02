"""Lighting uniformity check on the rectified technical captures."""
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def imread_u(path):
    data = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


run = sorted((ROOT / "manifests" / "EXAM02_captures").glob("run_*"), key=lambda p: p.stat().st_mtime)[-1]
qc = json.loads((run / "qc.json").read_text("utf-8"))
rows = []
for rec in qc:
    img = imread_u(ROOT / rec["rectified"])
    if img is None:
        continue
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = g.shape
    left, right = g[:, : w // 2].mean(), g[:, w // 2 :].mean()
    top, bottom = g[: h // 2].mean(), g[h // 2 :].mean()
    rows.append({
        "seq": rec["seq"],
        "left_mean": round(float(left), 1),
        "right_mean": round(float(right), 1),
        "right_minus_left": round(float(right - left), 1),
        "bottom_minus_top": round(float(bottom - top), 1),
        "std": round(float(g.std()), 1),
    })
df = pd.DataFrame(rows)
print(df.to_string(index=False))
print("\nmedian right-left:", df.right_minus_left.median(), "| median bottom-top:", df.bottom_minus_top.median())
