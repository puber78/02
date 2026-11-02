"""Assemble the EXAM02 pooled capture table (one row per capture, six model scores).

Inputs (all on disk, nothing invented):
  * final import run per session  -> captures.parquet + qc.json
  * queue_<session>.json          -> seq -> role/label/source/repeat
  * final score run per session   -> <session>_physical_scores.parquet

``sample_id`` is a deterministic mint of (branch, transform, capture_id), so the
score rows are re-keyed onto captures without guessing.

Outputs:
  manifests/EXAM02/EXAM02_captures_1000.parquet
  manifests/EXAM02/EXAM02_captures_1000.csv
  manifests/EXAM02/EXAM02_dataset_summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from proxy_selection.contracts.ids import mint_sample_id  # noqa: E402

CAPTURES = PROJECT_ROOT / "manifests" / "EXAM02_captures"
SCORES = PROJECT_ROOT / "scores" / "EXAM02"

MODEL_KEYS = ["swinv2_deploy", "siglip_ai_human", "swin_sdxl",
              "convnext_ai", "resnet_ai", "vit_ai_real"]


def latest_run_per_session() -> dict[str, Path]:
    out: dict[str, Path] = {}
    runs = [r for r in CAPTURES.glob("run_*") if (r / "import_summary.json").exists()]
    for r in sorted(runs, key=lambda p: (p / "import_summary.json").stat().st_mtime):
        s = json.loads((r / "import_summary.json").read_text(encoding="utf-8"))
        sess = s.get("session")
        if sess:
            out[sess] = r
    return out


def score_run_for(session: str) -> Path | None:
    cands = []
    for d in SCORES.glob("run_*"):
        p = d / f"{session}_physical_scores.parquet"
        if p.exists():
            cands.append((p.stat().st_mtime, d))
    return sorted(cands)[-1][1] if cands else None


def registry() -> dict[str, str]:
    """model_id -> model_key, recovered from any physical_metrics.json (they carry both)."""
    out: dict[str, str] = {}
    for p in SCORES.glob("run_*/physical_metrics.json"):
        m = json.loads(p.read_text(encoding="utf-8"))
        for r in m.get("models", []):
            if r.get("model_id") and r.get("model_key"):
                out[r["model_id"]] = r["model_key"]
    if not out:
        reg = json.loads((PROJECT_ROOT / "models" / "registry.json").read_text(encoding="utf-8"))
        out = {c.get("model_id"): c["model_key"] for c in reg["candidates"] if c.get("model_id")}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    mid2key = registry()
    rows = []
    per_session = {}
    for session, run in sorted(latest_run_per_session().items()):
        if not session.startswith("main_s"):
            continue
        cap = pd.read_parquet(run / "captures.parquet")
        qc = {int(r["seq"]): r for r in json.loads((run / "qc.json").read_text(encoding="utf-8"))}
        queue = json.loads((PROJECT_ROOT / "captures" / "kit" / f"queue_{session}.json").read_text(encoding="utf-8"))
        items = queue["items"] if isinstance(queue, dict) else queue
        by_seq = {int(i["seq"]): i for i in items}

        sd = score_run_for(session)
        score_by_capture: dict[str, dict] = {}
        if sd is not None:
            sc = pd.read_parquet(sd / f"{session}_physical_scores.parquet")
            sc = sc[sc["status"] == "ok"]
            for r in sc.to_dict("records"):
                key = mid2key.get(r["model_id"], r["model_id"])
                score_by_capture.setdefault(r["sample_id"], {})[key] = float(r["raw_score"])

        n_rows = 0
        for row in cap.to_dict("records"):
            seq = int(row["attempt_index"])
            it = by_seq.get(seq, {})
            q = qc.get(seq, {})
            sid = mint_sample_id(branch="physical", transform_id="rectified", parent_key=row["capture_id"])
            rec = {
                "session": session,
                "seq": seq,
                "capture_id": row["capture_id"],
                "sample_id": sid,
                "source_id": it.get("source_id"),
                "role": it.get("role"),
                "label": int(it["label"]) if it.get("label") is not None else None,
                "is_repeat": bool(row.get("is_planned_repeat")),
                "repeat_of_source_id": it.get("repeat_of_source_id"),
                "display_asset_id": row.get("display_asset_id"),
                "captured_at": row.get("captured_at"),
                "device_id": row.get("device_id"),
                "qc_status": row.get("qc_status"),
                "failure_code": row.get("failure_code"),
                "content_ncc": q.get("content_ncc"),
                "inliers": q.get("inliers"),
                "blur_laplacian_var": q.get("blur_laplacian_var"),
                "blur_ratio_720": q.get("blur_ratio_720"),
                "sharp_escape_used": q.get("sharp_escape_used"),
                "mean_luma": q.get("mean_luma"),
                "clip_high_fraction": q.get("clip_high_fraction"),
                "clip_excess": q.get("clip_excess"),
                "screen_visible_fraction": q.get("screen_visible_fraction"),
                "corner_dev_deg": q.get("corner_dev_deg"),
                "clip_low_fraction": q.get("clip_low_fraction"),
            }
            sc = score_by_capture.get(sid, {})
            for k in MODEL_KEYS:
                rec[k] = sc.get(k)
            n_rows += 1
            rows.append(rec)
        per_session[session] = {"import_run": run.name, "score_run": sd.name if sd else None,
                                "n_captures": n_rows, "n_scored": sum(1 for r in rows[-n_rows:] if r[MODEL_KEYS[0]] is not None)}

    df = pd.DataFrame(rows)
    df["in_analysis"] = df["qc_status"].eq("passed")

    summary = {
        "n_captures": int(len(df)),
        "n_analysis": int(df["in_analysis"].sum()),
        "by_status": dict(Counter(df["qc_status"])),
        "by_role": dict(Counter(df["role"])),
        "by_label": {str(k): int(v) for k, v in Counter(df["label"]).items()},
        "n_repeats": int(df["is_repeat"].sum()),
        "n_missing_scores": int(df[MODEL_KEYS[0]].isna().sum()),
        "sessions": per_session,
        "model_keys": MODEL_KEYS,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2)[:1500])

    if args.write:
        out = PROJECT_ROOT / "manifests" / "EXAM02"
        out.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out / "EXAM02_captures_1000.parquet", index=False)
        df.to_csv(out / "EXAM02_captures_1000.csv", index=False, encoding="utf-8")
        (out / "EXAM02_dataset_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print("written", out / "EXAM02_captures_1000.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

