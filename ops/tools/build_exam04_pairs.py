"""Build the EXAM04 same-source pairs: digital score and physical score for the
same (source, model).

Design (protocols/confirmatory.yaml):
  * T_pilot sources -> digital families F1_jpeg, F2_scale, F3_blur, F4_color
  * C_pool  sources -> digital `clean` (their display asset is a 2560x1440
    upscale that was never the selection basis; `clean` is the source the
    physical display was rendered from)
  * physical score -> the frozen detector score of the *captured photograph*
    of that source (EXAM02), orientation already applied by the scorer.

Outputs
  manifests/EXAM04/<run>/pairs.parquet    one row per (capture, model, family)
  manifests/EXAM04/<run>/manifest.json    coverage + provenance

Nothing is imputed: a missing digital or physical score leaves the pair out and
is counted in the manifest.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

import pandas as pd

from proxy_selection.config import PROJECT_ROOT

RUNS = PROJECT_ROOT / "manifests" / "EXAM04"
CAPTURES = PROJECT_ROOT / "manifests" / "EXAM02" / "EXAM02_captures_1000.parquet"
DIGITAL_SCORES = PROJECT_ROOT / "scores" / "EXAM03" / "run_20261102T065427Z_1e0c09aa" / "digital_scores.parquet"
DIGITAL_SAMPLES = PROJECT_ROOT / "scores" / "EXAM03" / "run_20261102T065427Z_1e0c09aa" / "digital_samples.parquet"
# EXAM04 adds the T_pilot digital families (scored after the EXAM03 selection was
# frozen, DEC-0007/DEC-0008: selection never saw T_pilot).
DIGITAL_T = PROJECT_ROOT / "scores" / "EXAM04" / "run_20261102T071316Z_13a6975a"

MODEL_KEYS = ["swinv2_deploy", "siglip_ai_human", "swin_sdxl", "convnext_ai", "resnet_ai", "vit_ai_real"]

ROLE_FAMILIES = {
    "T_pilot": ["F1_jpeg", "F2_scale", "F3_blur", "F4_color"],
    "C_pool": ["clean"],
}


def model_id_to_key() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in (PROJECT_ROOT / "scores" / "EXAM02").glob("run_*/physical_metrics.json"):
        m = json.loads(p.read_text(encoding="utf-8"))
        for r in m.get("models", []):
            if r.get("model_id") and r.get("model_key"):
                out[r["model_id"]] = r["model_key"]
    if not out:
        reg = json.loads((PROJECT_ROOT / "models" / "registry.json").read_text(encoding="utf-8"))
        out = {c.get("model_id"): c["model_key"] for c in reg["candidates"] if c.get("model_id")}
    return out


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    out = RUNS / run_id
    out.mkdir(parents=True, exist_ok=True)

    caps = pd.read_parquet(CAPTURES)
    caps = caps[caps["in_analysis"] & ~caps["is_repeat"].astype(bool)].copy()

    mid2key = model_id_to_key()
    frames = []
    for base in (DIGITAL_SCORES.parent, DIGITAL_T):
        dig = pd.read_parquet(base / "digital_scores.parquet")
        smp = pd.read_parquet(base / "digital_samples.parquet")
        dig = dig.merge(smp[["sample_id", "source_id", "family"]], on="sample_id", how="left", suffixes=("", "_s"))
        frames.append(dig)
    dig = pd.concat(frames, ignore_index=True)
    dig["model_key"] = dig["model_id"].map(mid2key)
    if dig["model_key"].isna().any():
        unknown = sorted(dig.loc[dig["model_key"].isna(), "model_id"].unique())
        raise SystemExit(f"unmapped model ids: {unknown}")
    dig = dig[dig["status"] == "ok"] if "status" in dig else dig
    dig = dig[["source_id", "family", "model_key", "raw_score"]].dropna()
    dig = dig.rename(columns={"raw_score": "digital_score"})
    dig = dig.drop_duplicates(["source_id", "family", "model_key"])

    rows: list[dict] = []
    missing_digital = 0
    for rec in caps.to_dict("records"):
        fams = ROLE_FAMILIES.get(rec["role"], [])
        for fam in fams:
            sub = dig[(dig["source_id"] == rec["source_id"]) & (dig["family"] == fam)]
            if sub.empty:
                missing_digital += 1
                continue
            for mk in MODEL_KEYS:
                drow = sub[sub["model_key"] == mk]
                if drow.empty:
                    missing_digital += 1
                    continue
                phys = rec.get(mk)
                if phys is None or pd.isna(phys):
                    continue
                rows.append({
                    "capture_id": rec["capture_id"],
                    "sample_id": rec["sample_id"],
                    "source_id": rec["source_id"],
                    "session": rec["session"],
                    "seq": int(rec["seq"]),
                    "role": rec["role"],
                    "label": int(rec["label"]),
                    "family": fam,
                    "model_key": mk,
                    "digital_score": float(drow["digital_score"].iloc[0]),
                    "physical_score": float(phys),
                    "content_ncc": float(rec["content_ncc"]) if pd.notna(rec["content_ncc"]) else None,
                    "inliers": float(rec["inliers"]) if pd.notna(rec["inliers"]) else None,
                })

    df = pd.DataFrame(rows)
    df.to_parquet(out / "pairs.parquet", index=False)

    def sha(p) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    manifest = {
        "run_id": run_id,
        "inputs": {
            "captures": {"path": str(CAPTURES.relative_to(PROJECT_ROOT)), "sha256": sha(CAPTURES)},
            "digital_scores": {"path": str(DIGITAL_SCORES.relative_to(PROJECT_ROOT)), "sha256": sha(DIGITAL_SCORES)},
            "digital_samples": {"path": str(DIGITAL_SAMPLES.relative_to(PROJECT_ROOT)), "sha256": sha(DIGITAL_SAMPLES)},
        },
        "design": {
            "role_families": ROLE_FAMILIES,
            "models": MODEL_KEYS,
            "physical": "EXAM02 captured frame score per model (orientation applied)",
            "digital": "EXAM03 family score of the same source",
            "repeats": "excluded from pairs; used only for the repeat-consistency analysis in EXAM04",
        },
        "n_captures": int(len(caps)),
        "n_pairs": int(len(df)),
        "n_unique_sources": int(df["source_id"].nunique()) if len(df) else 0,
        "missing_digital_pairs": int(missing_digital),
        "by_role": {k: int(v) for k, v in df.groupby("role").size().items()} if len(df) else {},
        "by_family": {k: int(v) for k, v in df.groupby("family").size().items()} if len(df) else {},
        "n_sources_by_role": {k: int(df[df["role"] == k]["source_id"].nunique()) for k in df["role"].unique()}
        if len(df) else {},
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
