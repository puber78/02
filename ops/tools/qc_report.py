import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
runs = sorted((ROOT / "manifests" / "EXAM02_captures").glob("run_*"), key=lambda p: p.stat().st_mtime)
run = runs[-1]
qc = json.loads((run / "qc.json").read_text("utf-8"))
df = pd.DataFrame(qc)
pd.set_option("display.width", 200)
cols = ["seq", "label", "is_repeat", "qc_status", "inliers", "inlier_ratio",
        "blur_laplacian_var", "mean_luma", "screen_coverage", "clip_high_fraction"]
print("run:", run.name, "n:", len(df))
print(df[cols].to_string(index=False))
print("\nsummary:")
print(df[["inliers", "inlier_ratio", "blur_laplacian_var", "mean_luma",
          "screen_coverage", "clip_high_fraction"]].describe().round(4).to_string())
