"""EXAM03 step 3 -- score the digital test families with every frozen candidate.

Uses the variant manifest produced by ``scripts/make_digital_variants.py`` and the
frozen checkpoints in ``models/hf_cache`` (offline).  Each (source, family, model)
inference is a row; failures are recorded explicitly and never imputed.  Row building
goes through ``proxy_selection.scoring.score_rows`` so the schema is identical to the
physical side (DEC-0008 allows source-parented digital samples).

Outputs (``scores/EXAM03/<run_id>/``):
  digital_scores.parquet   one row per (sample, model), schema-valid
  digital_metrics.json     per (family, model) AUC with 95% CI, coverage, failures

Usage:
    python scripts/score_digital.py --families clean display F1_jpeg F2_scale F3_blur F4_color
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proxy_selection.adapters.hf_classifier import HFClassifierAdapter  # noqa: E402
from proxy_selection.contracts.ids import mint_sample_id  # noqa: E402
from proxy_selection.io import Ledger, write_json, write_parquet  # noqa: E402
from proxy_selection.metrics.auc import roc_auc, roc_auc_ci_normal  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402
from proxy_selection.scoring import score_rows  # noqa: E402

SCORES = ROOT / "scores"
DEFAULT_FAMILIES = ("clean", "display", "F1_jpeg", "F2_scale", "F3_blur", "F4_color")


def latest_variant_manifest() -> Path:
    cands = sorted((ROOT / "manifests" / "EXAM03").glob("run_*/digital_variants.parquet"),
                   key=lambda p: p.stat().st_mtime)
    if not cands:
        raise FileNotFoundError("no digital_variants.parquet; run make_digital_variants.py first")
    return cands[-1]


def load_registry() -> list[dict]:
    return json.loads((ROOT / "models" / "registry.json").read_text(encoding="utf-8"))["candidates"]


def forced_batch_sizes() -> dict[str, int]:
    """Read the latest detector audit and honour any batch-1 pinning."""
    cands = sorted((ROOT / "manifests" / "EXAM03").glob("run_*/detector_audit.json"),
                   key=lambda p: p.stat().st_mtime)
    if not cands:
        return {}
    data = json.loads(cands[-1].read_text(encoding="utf-8"))
    return {c["model_key"]: int(c.get("forced_batch_size", 16)) for c in data["candidates"]}


def build_samples(sub: pd.DataFrame, fam: str) -> list[dict]:
    out = []
    for r in sub.to_dict("records"):
        params = r.get("params") or {}
        if isinstance(params, str):
            params = json.loads(params)
        if not isinstance(params, dict):
            params = {}
        dsp = params.get("display_asset_id")
        parent_key = dsp or r["source_id"]
        parent_kind = "display_asset" if dsp else "source"
        sid = mint_sample_id(branch="digital", transform_id=f"digital_{fam}",
                             parent_key=parent_key, parent_kind=parent_kind)
        out.append({
            "sample_id": sid,
            "source_id": r["source_id"],
            "split_role": r["role"],
            "environment_id": "digital_reference",
            "image_branch": "digital",
            "file_path": str(ROOT / r["path"]),
            "label": int(r["label"]),
            "family": fam,
            "display_asset_id": dsp,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", default=None)
    ap.add_argument("--families", nargs="*", default=list(DEFAULT_FAMILIES))
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--out-exam", default="EXAM03",
                    help="scores/<exam>/<run_id> becomes the output dir (EXAM04 reuses this scorer for T_pilot)")
    args = ap.parse_args()

    manifest_path = Path(args.variants) if args.variants else latest_variant_manifest()
    df = pd.read_parquet(manifest_path)
    df = df[df.family.isin(args.families)].copy()
    families = [f for f in args.families if f in set(df.family)]
    print(f"manifest: {manifest_path}  rows={len(df)}  families={families}", flush=True)

    forced = forced_batch_sizes()
    cands = load_registry()
    if args.models:
        cands = [c for c in cands if c["model_key"] in set(args.models)]

    log = RunLogger.start(ROOT, note="EXAM03 digital scoring")
    ledger = Ledger(ROOT / "ops")
    out_dir = SCORES / args.out_exam / log.run_id

    all_rows: list[dict] = []
    sample_rows: list[dict] = []
    metrics: list[dict] = []

    for fam in families:
        sub = df[df.family == fam].reset_index(drop=True)
        if fam == "display":
            # D_sel was never shown: its "display" baseline is the clean file, so only the
            # C_pool display assets carry information.
            sub = sub[sub.role == "C_pool"].reset_index(drop=True)
        samples = build_samples(sub, fam)
        sample_rows.extend({"sample_id": s["sample_id"], "source_id": s["source_id"],
                            "family": fam, "role": s["split_role"], "label": s["label"],
                            "display_asset_id": s.get("display_asset_id")} for s in samples)
        print(f"[{fam}] n={len(samples)}", flush=True)

        for cand in cands:
            t1 = time.time()
            bs = forced.get(cand["model_key"], 16)
            ad = HFClassifierAdapter(
                repo=cand["repo"], revision=cand["revision"],
                cache_dir=str(ROOT / "models" / "hf_cache"),
                ai_label_override=cand.get("ai_label"), batch_size=bs,
            )
            ad.load()
            rows = score_rows(ad, samples, run_id=log.run_id,
                              transform_id=f"digital_{fam}", is_fixture=False)
            all_rows.extend(rows)
            del ad
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:  # noqa: BLE001
                pass

            lab = {s["sample_id"]: s["label"] for s in samples}
            part = pd.DataFrame(rows)
            part["label"] = part["sample_id"].map(lab)
            good = part[(part.status == "ok") & part.raw_score.notna()]
            auc = ci_lo = ci_hi = None
            if good.label.nunique() == 2 and len(good) >= 20:
                auc = float(roc_auc(good.label.tolist(), good.raw_score.tolist()))
                try:
                    ci_lo, ci_hi = roc_auc_ci_normal(good.label.tolist(), good.raw_score.tolist())
                    ci_lo, ci_hi = float(ci_lo), float(ci_hi)
                except Exception:  # noqa: BLE001
                    ci_lo = ci_hi = None
            metrics.append({
                "family": fam, "model_key": cand["model_key"], "auc": auc,
                "auc_ci_lo": ci_lo, "auc_ci_hi": ci_hi,
                "n": int(len(part)), "n_ok": int(len(good)),
                "n_failed": int(len(part) - len(good)),
                "elapsed_s": round(time.time() - t1, 1),
            })
            print(f"  {cand['model_key']:16s} auc={None if auc is None else round(auc, 4)} "
                  f"failed={len(part) - len(good)} {time.time() - t1:.1f}s", flush=True)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_parquet(out_dir / "digital_scores.parquet", all_rows, "scores",
                  ledger=ledger, run_id=log.run_id)
    # sample -> (family, role, label) map; plain parquet (not a contract table)
    pd.DataFrame(sample_rows).to_parquet(out_dir / "digital_samples.parquet", index=False)
    write_json(out_dir / "digital_metrics.json",
               {"run_id": log.run_id, "manifest": str(manifest_path.relative_to(ROOT)),
                "families": families, "metrics": metrics},
               ledger=ledger, run_id=log.run_id, kind="manifest")

    total_failed = sum(m["n_failed"] for m in metrics)
    log.finish("PASS" if total_failed == 0 else "PARTIAL", n_rows=len(all_rows), failed=total_failed)
    print(f"written {out_dir/'digital_scores.parquet'} rows={len(all_rows)} failed={total_failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
