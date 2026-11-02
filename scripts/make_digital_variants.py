"""EXAM03 step 2 -- build the digital test families for C_pool + D_sel.

For every source in ``C_pool`` (200) and ``D_sel`` (500) this produces, deterministically:

  clean      originally downloaded file (referenced, not copied)
  display    the actual PNG asset that was / would be shown on screen (referenced)
  jpeg55     JPEG re-encode at quality 55 (subsampling 4:2:0), decoded back to PNG
  resample   downscale to 50% with Lanczos, then back to original size
  blur       Gaussian blur, radius 1.0 px at original resolution
  color      gamma 0.9 + saturation x1.15

Intensities are fixed in ``ops/protocols/study_protocol.yaml`` (digital families) and
were chosen *before* seeing any model scores.  Every generated file is hashed and
recorded; re-runs reuse an existing file only if its SHA-256 matches.

Usage:
    python scripts/make_digital_variants.py [--families jpeg55 resample blur color]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proxy_selection.io import Ledger, write_json, write_parquet  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402
from proxy_selection.hashing import sha256_bytes, sha256_file  # noqa: E402

EXAM02_RUN = "run_20261027T005511Z_2177a59d"
# Exactly the parameters frozen in protocols/digital_families.yaml (F1-F4).
FAMILIES = ("F1_jpeg", "F2_scale", "F3_blur", "F4_color")
PARAMS = {
    "F1_jpeg": {"format": "jpeg", "quality": 75, "subsampling": "4:2:0"},
    "F2_scale": {"downscale": 0.5, "upsample": "bilinear", "output_size": "original"},
    "F3_blur": {"kernel": "gaussian", "sigma": 0.8},
    "F4_color": {"saturation": 1.2, "brightness": 0.95, "contrast": 1.05},
}


def source_path(prov: str) -> Path:
    if prov.startswith("detection-datasets/coco#"):
        rid = int(prov.split("#", 1)[1])
        return ROOT / "data" / "raw" / "sources" / "pool_photo" / f"coco_{rid:012d}.png"
    if prov.startswith("elsaEU/ELSA1M_track1#"):
        rid = prov.split("#", 1)[1]
        return ROOT / "data" / "raw" / "sources" / "pool_ai" / f"elsa_{rid}.png"
    raise ValueError(f"unmapped provenance: {prov}")


def apply_family(img: Image.Image, family: str) -> Image.Image:
    if family == "F1_jpeg":
        import io
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=PARAMS[family]["quality"], subsampling=2)
        buf.seek(0)
        return Image.open(buf).convert("RGB")
    if family == "F2_scale":
        f = PARAMS[family]["downscale"]
        w, h = img.size
        small = img.resize((max(1, int(round(w * f))), max(1, int(round(h * f)))), Image.BILINEAR)
        return small.resize((w, h), Image.BILINEAR)
    if family == "F3_blur":
        from PIL import ImageFilter
        return img.filter(ImageFilter.GaussianBlur(radius=PARAMS[family]["sigma"]))
    if family == "F4_color":
        from PIL import ImageEnhance
        out = ImageEnhance.Brightness(img).enhance(PARAMS[family]["brightness"])
        out = ImageEnhance.Contrast(out).enhance(PARAMS[family]["contrast"])
        out = ImageEnhance.Color(out).enhance(PARAMS[family]["saturation"])
        return out
    raise ValueError(family)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="*", default=list(FAMILIES))
    ap.add_argument("--roles", nargs="*", default=["C_pool", "D_sel"],
                    help="split roles to include; EXAM04 uses T_pilot (never used for selection)")
    ap.add_argument("--out-root", default="data/digital",
                    help="directory root for generated families (kept apart per role set)")
    args = ap.parse_args()

    log = RunLogger.start(ROOT, note="EXAM03 digital variants")
    ledger = Ledger(ROOT / "ops")
    out_dir = ROOT / "manifests" / "EXAM03" / log.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    src = pd.read_parquet(ROOT / "manifests" / "EXAM02" / EXAM02_RUN / "sources.parquet")
    spl = pd.read_parquet(ROOT / "manifests" / "EXAM02" / EXAM02_RUN / "splits.parquet")
    dis = pd.read_parquet(ROOT / "manifests" / "EXAM02" / EXAM02_RUN / "display_assets.parquet")
    m = src.merge(spl, on="source_id").merge(dis, on="source_id")
    m = m[m.split_role.isin(args.roles)].copy()
    if m.empty:
        raise SystemExit(f"no sources for roles {args.roles}")
    print(f"sources: {len(m)} ({m.split_role.value_counts().to_dict()})", flush=True)

    rows: list[dict] = []
    t0 = time.time()
    for i, r in enumerate(m.to_dict("records")):
        raw = source_path(r["provenance_uri"])
        if not raw.exists():
            raise FileNotFoundError(raw)
        if sha256_file(raw) != r["original_file_sha256"]:
            raise RuntimeError(f"source hash mismatch: {raw}")
        disp = ROOT / "data" / "display" / r["split_role"] / f"{r['display_asset_id']}.png"
        if not disp.exists():
            # D_sel was never shown on screen: its native-resolution asset *is* the
            # source file, so the "display" baseline degenerates to the clean source.
            if r["split_role"] == "D_sel":
                disp = raw
            else:
                raise FileNotFoundError(disp)

        rows.append({
            "source_id": r["source_id"], "role": r["split_role"], "label": int(r["label"]),
            "family": "clean", "path": str(raw.relative_to(ROOT)).replace("\\", "/"),
            "sha256": r["original_file_sha256"], "width": None, "height": None, "params": "{}",
        })
        rows.append({
            "source_id": r["source_id"], "role": r["split_role"], "label": int(r["label"]),
            "family": "display", "path": str(disp.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256_file(disp), "width": int(r["width"]), "height": int(r["height"]),
            "params": json.dumps({"display_asset_id": r["display_asset_id"]}, sort_keys=True),
        })

        img = Image.open(raw).convert("RGB")
        for fam in args.families:
            out = ROOT / args.out_root / fam / f"{r['source_id']}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            if out.exists():
                rec_sha = sha256_file(out)
                digest = rec_sha
            else:
                v = apply_family(img, fam)
                tmp = out.with_suffix(".tmp.png")
                v.save(tmp, format="PNG", optimize=False, compress_level=3)
                data = tmp.read_bytes()
                digest = sha256_bytes(data)
                tmp.replace(out)
            rows.append({
                "source_id": r["source_id"], "role": r["split_role"], "label": int(r["label"]),
                "family": fam, "path": str(out.relative_to(ROOT)).replace("\\", "/"),
                "sha256": digest, "width": img.width, "height": img.height,
                "params": json.dumps(PARAMS[fam], sort_keys=True),
            })
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(m)} sources, {time.time() - t0:.1f}s", flush=True)

    df = pd.DataFrame(rows)
    out_parquet = out_dir / "digital_variants.parquet"
    df.to_parquet(out_parquet, index=False)
    ledger.record_artifact(out_parquet, kind="manifest", run_id=log.run_id,
                           note="EXAM03 digital variants (clean/display reference existing files)")
    summary = {
        "run_id": log.run_id,
        "exam02_run": EXAM02_RUN,
        "n_sources": int(m.shape[0]),
        "by_role": {k: int(v) for k, v in m.split_role.value_counts().items()},
        "families": {"clean": {}, "display": {}, **{f: PARAMS[f] for f in args.families}},
        "n_rows": int(df.shape[0]),
        "by_family": {k: int(v) for k, v in df.family.value_counts().items()},
        "elapsed_s": round(time.time() - t0, 1),
        "note": "clean/display rows reference existing files; generated families are written once and reused if the hash matches.",
    }
    write_json(out_dir / "digital_variants_summary.json", summary, ledger=ledger, run_id=log.run_id, kind="manifest")
    log.finish("PASS", n_rows=len(rows))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
