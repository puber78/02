"""Score a physical capture session with the frozen candidate set.

Reads a completed import run (qc.json + captures.parquet), builds physical
samples, runs the same unlabeled adapters used for digital scoring, and reports
per-model AUC on this session (engineering check; a 20-image technical session is
not a scientific estimate).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
os.environ.setdefault("HF_HOME", str(ROOT / "models" / "hf_home"))
os.environ.setdefault("HF_HUB_CACHE", str(ROOT / "models" / "hf_home" / "hub"))
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from proxy_selection.adapters.hf_classifier import HFClassifierAdapter  # noqa: E402
from proxy_selection.config import SCORES  # noqa: E402
from proxy_selection.contracts.ids import mint_sample_id  # noqa: E402
from proxy_selection.io import Ledger, write_json, write_parquet  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402
from proxy_selection.scoring import compute_auc_table, coverage_report, score_rows  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--import-run", required=True, help="manifests/EXAM02_captures/<run_id>")
    ap.add_argument("--session", default=None, help="defaults to the import run session")
    ap.add_argument("--environment", default="e1_r27qa_k80")
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()

    import torch

    torch.manual_seed(20261026)
    log = RunLogger.start(ROOT, note=f"score physical {args.session}")
    ledger = Ledger(ROOT / "ops")
    run_dir = ROOT / args.import_run if not Path(args.import_run).is_absolute() else Path(args.import_run)
    qc = json.loads((run_dir / "qc.json").read_text("utf-8"))
    if args.session is None:
        meta_path = run_dir / "import_summary.json"
        meta = json.loads(meta_path.read_text("utf-8")) if meta_path.exists() else {}
        args.session = meta.get("session") or "tech"

    samples = []
    for rec in qc:
        if rec["qc_status"] != "passed" or not rec.get("rectified"):
            continue
        samples.append(
            {
                "sample_id": mint_sample_id(
                    branch="physical", transform_id="rectified", parent_key=rec["capture_id"]
                ),
                "source_id": rec["source_id"],
                "split_role": rec.get("role") or "TECH",
                "environment_id": args.environment,
                "image_branch": "physical",
                "file_path": str(ROOT / rec["rectified"]),
                "label": int(rec["label"]),
                "seq": rec["seq"],
            }
        )
    print(f"samples: {len(samples)}  (real={sum(1 for s in samples if s['label']==0)}, "
          f"ai={sum(1 for s in samples if s['label']==1)})")

    registry = json.loads((ROOT / "models" / "registry.json").read_text("utf-8"))["candidates"]
    wanted = set(args.models) if args.models else None
    all_rows, audits = [], []
    for cand in registry:
        if wanted and cand["model_key"] not in wanted:
            continue
        adapter = HFClassifierAdapter(
            repo=cand["repo"],
            revision=cand["revision"],
            cache_dir=str(ROOT / "models" / "hf_cache"),
            ai_label_override=cand.get("ai_label"),
            batch_size=int(cand.get("batch_size", 16)),
        )
        adapter.load()
        rows = score_rows(adapter, samples, run_id=log.run_id, transform_id="rectified", is_fixture=False)
        all_rows.extend(rows)
        df = pd.DataFrame(rows)
        df["label"] = df["sample_id"].map({s["sample_id"]: s["label"] for s in samples})
        aucs = compute_auc_table(df)
        audits.append(
            {
                "model_key": cand["model_key"],
                "model_id": adapter.model_id,
                "n": int((df["status"] == "ok").sum()),
                "failed": int((df["status"] != "ok").sum()),
                "auc": None if aucs.empty else float(aucs["auc"].iloc[0]),
            }
        )
        print(f"  {cand['model_key']:16s} auc={audits[-1]['auc']} failed={audits[-1]['failed']}", flush=True)
        del adapter
        torch.cuda.empty_cache()

    out_dir = SCORES / "EXAM02" / log.run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    write_parquet(out_dir / f"{args.session}_physical_scores.parquet", all_rows, "scores",
                  ledger=ledger, run_id=log.run_id)
    summary = {
        "run_id": log.run_id,
        "session": args.session,
        "import_run": run_dir.name,
        "environment": args.environment,
        "n_samples": len(samples),
        "coverage": coverage_report(pd.DataFrame(all_rows), expected_units=len(samples) * len(audits)),
        "models": audits,
        "note": (
            f"Session-level engineering check on n={len(samples)} captures. "
            "Not a scientific estimate by itself; the pre-registered EXAM02 analysis "
            "pools all sessions and reports bootstrap intervals."
        ),
    }
    write_json(out_dir / "physical_metrics.json", summary, ledger=ledger, run_id=log.run_id)
    try:  # ledger hook: logging must never break the pipeline
        from proxy_selection.events import log_event

        log_event(
            "score",
            f"{args.session} 物理评分",
            detail="; ".join(f"{a['model_key']}={a['auc']:.4f}" for a in audits if a["auc"] is not None),
            run_id=log.run_id,
            extra={"n_samples": len(samples), "import_run": run_dir.name},
        )
    except Exception:  # noqa: BLE001 - never fail scoring over logging
        pass
    log.finish("PASS")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
