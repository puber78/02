"""EXAM03 step 4 -- per-family AUCs, frozen digital selection, and the freeze record.

Reads the digital score parquet plus the sample map written by ``score_digital.py``,
computes AUC per (role, family, model) with a normal-approximation 95% interval,
evaluates the four pre-registered digital rules on ``C_pool`` only, and writes:

  manifests/EXAM03/<run_id>/exam03_family_aucs.csv
  manifests/EXAM03/<run_id>/exam03_summary.json
  selections/EXAM03/digital_choices.jsonl        (append-only)

No physical data is read here.  D_sel is used only as a *digital* hold-out.

Usage:
    python scripts/build_exam03.py [--scores-run run_...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proxy_selection.io import Ledger, write_json  # noqa: E402
from proxy_selection.metrics.auc import roc_auc, roc_auc_ci_normal  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402

FAMILIES = ["F1_jpeg", "F2_scale", "F3_blur", "F4_color"]
RANDOM_SEED = 20261026


def latest_scores_run() -> Path:
    cands = sorted((ROOT / "scores" / "EXAM03").glob("run_*/digital_scores.parquet"),
                   key=lambda p: p.stat().st_mtime)
    if not cands:
        raise FileNotFoundError("no digital_scores.parquet")
    return cands[-1].parent


def model_key_map() -> dict[str, str]:
    """model_id -> registry model_key, resolved from the latest detector audit."""
    cands = sorted((ROOT / "manifests" / "EXAM03").glob("run_*/detector_audit.json"),
                   key=lambda p: p.stat().st_mtime)
    if not cands:
        raise FileNotFoundError("no detector_audit.json")
    data = json.loads(cands[-1].read_text(encoding="utf-8"))
    return {c["model_id"]: c["model_key"] for c in data["candidates"]}


def auc_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (role, fam, model), g in df.groupby(["role", "family", "model_key"]):
        good = g[(g.status == "ok") & g.raw_score.notna()]
        if good.label.nunique() != 2 or len(good) < 20:
            continue
        auc = float(roc_auc(good.label.tolist(), good.raw_score.tolist()))
        lo = hi = None
        try:
            lo, hi = roc_auc_ci_normal(good.label.tolist(), good.raw_score.tolist())
        except Exception:  # noqa: BLE001
            pass
        rows.append({"role": role, "family": fam, "model_key": model, "auc": auc,
                     "ci_lo": None if lo is None else float(lo),
                     "ci_hi": None if hi is None else float(hi),
                     "n": int(len(good))})
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores-run", default=None)
    args = ap.parse_args()

    run_dir = Path(args.scores_run) if args.scores_run else latest_scores_run()
    scores = pd.read_parquet(run_dir / "digital_scores.parquet")
    samples = pd.read_parquet(run_dir / "digital_samples.parquet")
    scores = scores.merge(samples[["sample_id", "family", "role", "label"]],
                          on="sample_id", how="left", validate="many_to_one")
    if scores["family"].isna().any():
        raise RuntimeError("unmapped sample_id in digital_scores.parquet")

    mmap = model_key_map()
    scores["model_key"] = scores["model_id"].map(mmap)
    if scores["model_key"].isna().any():
        raise RuntimeError("unmapped model_id (audit/registry mismatch)")

    log = RunLogger.start(ROOT, note="EXAM03 digital selection + freeze")
    ledger = Ledger(ROOT / "ops")
    out_dir = ROOT / "manifests" / "EXAM03" / log.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    tab = auc_table(scores)
    tab.to_csv(out_dir / "exam03_family_aucs.csv", index=False)

    models = sorted(scores.model_key.unique())
    cp = tab[tab.role == "C_pool"]
    wide = cp.pivot_table(index="model_key", columns="family", values="auc")
    for f in FAMILIES:
        if f not in wide.columns:
            raise RuntimeError(f"missing family {f} in C_pool AUC table")

    scores_by_model = {}
    for m in models:
        row = wide.loc[m]
        fam_aucs = {f: float(row[f]) for f in FAMILIES}
        scores_by_model[m] = {
            "family_aucs": fam_aucs,
            "s_dig": float(np.mean([fam_aucs[f] for f in FAMILIES])),
            "s_worst": float(min(fam_aucs.values())),
            "s_clean": float(row["clean"]) if "clean" in wide.columns else None,
        }

    def pick(key: str) -> str:
        # tie-break: higher score, then model_key lexicographic (frozen, physical-blind)
        return sorted(models, key=lambda m: (-(scores_by_model[m][key]
                                               if scores_by_model[m][key] is not None else -1), m))[0]

    rng = np.random.default_rng(RANDOM_SEED)
    rand_pick = str(rng.choice(models))
    choices = {
        "S_dig": {"chosen": pick("s_dig"), "criterion": "equal-weight mean of F1-F4 AUC on C_pool"},
        "S_worst": {"chosen": pick("s_worst"), "criterion": "maximin over F1-F4 AUC on C_pool"},
        "S_clean": {"chosen": pick("s_clean"), "criterion": "clean-only AUC on C_pool"},
        "S_rand": {"chosen": rand_pick, "criterion": f"uniform random, seed {RANDOM_SEED}"},
    }

    ds = tab[tab.role == "D_sel"].pivot_table(index="model_key", columns="family", values="auc")
    holdout = {}
    for m in models:
        if m not in ds.index:
            continue
        fam = {f: float(ds.loc[m, f]) for f in FAMILIES if f in ds.columns}
        holdout[m] = {"family_aucs": fam,
                      "s_dig": float(np.mean(list(fam.values()))) if fam else None}

    summary = {
        "run_id": log.run_id,
        "digital_scores_run": run_dir.name,
        "n_sources": int(scores[["source_id"]].drop_duplicates().shape[0]),
        "families": FAMILIES,
        "models": models,
        "c_pool": {m: scores_by_model[m] for m in models},
        "d_sel": holdout,
        "choices": choices,
        "frozen": True,
        "note": ("Rules were evaluated on C_pool only; T_pilot was not read. "
                 "D_sel is a digital hold-out, not used to pick."),
    }
    write_json(out_dir / "exam03_summary.json", summary, ledger=ledger, run_id=log.run_id,
               kind="manifest")

    sel_dir = ROOT / "selections" / "EXAM03"
    sel_dir.mkdir(parents=True, exist_ok=True)
    with (sel_dir / "digital_choices.jsonl").open("a", encoding="utf-8") as fh:
        for rule, rec in choices.items():
            fh.write(json.dumps({
                "written_at": log.run_id,
                "rule": rule,
                "chosen_model": rec["chosen"],
                "criterion": rec["criterion"],
                "s_dig": scores_by_model[rec["chosen"]]["s_dig"],
                "family_aucs": scores_by_model[rec["chosen"]]["family_aucs"],
                "scores_run": run_dir.name,
            }, ensure_ascii=False) + "\n")

    print(wide.round(4).to_string())
    print()
    for rule, rec in choices.items():
        print(f"{rule:9s} -> {rec['chosen']}")
    print("D_sel hold-out:")
    for m, rec in sorted(holdout.items(), key=lambda kv: -(kv[1]["s_dig"] or 0)):
        print(f"  {m:16s} s_dig={rec['s_dig']:.4f}")
    log.finish("PASS", chosen=choices["S_dig"]["chosen"])
    print("written", out_dir / "exam03_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
