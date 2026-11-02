"""EXAM04 analysis: same-source digital-vs-physical pairing, session structure and
repeat consistency.

Inputs
  manifests/EXAM04/<run>/pairs.parquet      (build_exam04_pairs.py)
  manifests/EXAM02/EXAM02_captures_1000.parquet  (repeat rows + QC covariates)

Outputs
  manifests/EXAM04/<run>/exam04_summary.json
  manifests/EXAM04/<run>/exam04_family_table.csv
  manifests/EXAM04/<run>/exam04_model_table.csv
  manifests/EXAM04/<run>/exam04_session_table.csv
  manifests/EXAM04/<run>/exam04_repeat_table.csv

Statistics
  * AUC per (model, family) on the paired sources, digital and physical.
  * Delta = AUC_physical - AUC_digital, paired bootstrap over sources (2000 reps,
    seed 20261026); for the equal-weight family mean the four family AUCs are
    recomputed inside every bootstrap replicate so the family correlation is kept.
  * Repeats: |score difference| and label-decision flips against the first capture
    of the same source.
Nothing is imputed; any missing pair is dropped and counted.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from proxy_selection.config import PROJECT_ROOT
from proxy_selection.metrics.auc import roc_auc

EXAM04 = PROJECT_ROOT / "manifests" / "EXAM04"
CAPTURES = PROJECT_ROOT / "manifests" / "EXAM02" / "EXAM02_captures_1000.parquet"
MODELS = ["swinv2_deploy", "siglip_ai_human", "swin_sdxl", "convnext_ai", "resnet_ai", "vit_ai_real"]
FAMILIES = ["F1_jpeg", "F2_scale", "F3_blur", "F4_color"]
N_BOOT = 2000
SEED = 20261026


def latest_pairs() -> tuple[Path, pd.DataFrame]:
    cands = sorted(EXAM04.glob("run_*/pairs.parquet"), key=lambda p: p.stat().st_mtime)
    if not cands:
        raise SystemExit("no pairs.parquet; run build_exam04_pairs.py first")
    p = cands[-1]
    return p.parent, pd.read_parquet(p)


def auc_or_nan(y: np.ndarray, s: np.ndarray) -> float:
    if len(np.unique(y)) < 2:
        return float("nan")
    return float(roc_auc(y.tolist(), s.tolist()))


def paired_bootstrap_mean_delta(sub: pd.DataFrame, n_boot: int = N_BOOT, seed: int = SEED) -> dict:
    """Equal-weight mean over families of (AUC_phys - AUC_dig), paired by source."""
    piv = {}
    for fam in FAMILIES:
        part = sub[sub["family"] == fam]
        if part.empty:
            continue
        piv[fam] = part.set_index("source_id")[["label", "digital_score", "physical_score"]]
    if not piv:
        return {"delta_mean": None, "ci_low": None, "ci_high": None, "n_sources": 0, "n_boot_used": 0}
    sources = sorted(set().union(*[set(v.index) for v in piv.values()]))
    frames = {}
    for fam, v in piv.items():
        frames[fam] = v.reindex(sources)
    labels = {fam: frames[fam]["label"].to_numpy() for fam in frames}
    dig = {fam: frames[fam]["digital_score"].to_numpy(dtype=float) for fam in frames}
    phy = {fam: frames[fam]["physical_score"].to_numpy(dtype=float) for fam in frames}

    def mean_delta(idx: np.ndarray) -> float:
        ds = []
        for fam in frames:
            y = labels[fam][idx]
            if len(np.unique(y)) < 2:
                continue
            ds.append(auc_or_nan(y, phy[fam][idx]) - auc_or_nan(y, dig[fam][idx]))
        return float(np.mean(ds)) if ds else float("nan")

    rng = np.random.default_rng(seed)
    n = len(sources)
    point = mean_delta(np.arange(n))
    boots = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        boots[i] = mean_delta(rng.integers(0, n, n))
    ok = boots[~np.isnan(boots)]
    return {
        "delta_mean": point,
        "ci_low": float(np.percentile(ok, 2.5)) if len(ok) else None,
        "ci_high": float(np.percentile(ok, 97.5)) if len(ok) else None,
        "n_sources": n,
        "n_boot_used": int(len(ok)),
        "n_boot_skipped": int(n_boot - len(ok)),
    }


def main() -> int:
    pairs_dir, pairs = latest_pairs()
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex[:8]
    out = EXAM04 / run_id
    out.mkdir(parents=True, exist_ok=True)

    fam_table: list[dict] = []
    for model in MODELS:
        for fam in FAMILIES + ["clean"]:
            part = pairs[(pairs["model_key"] == model) & (pairs["family"] == fam)]
            if part.empty:
                continue
            y = part["label"].to_numpy()
            d = part["digital_score"].to_numpy(dtype=float)
            p = part["physical_score"].to_numpy(dtype=float)
            boot = paired_bootstrap_mean_delta(part) if fam in FAMILIES else None
            fam_table.append({
                "model_key": model, "family": fam, "role": part["role"].iloc[0],
                "n_sources": int(part["source_id"].nunique()),
                "auc_digital": auc_or_nan(y, d), "auc_physical": auc_or_nan(y, p),
                "delta": (auc_or_nan(y, p) - auc_or_nan(y, d)),
                "delta_ci_low": (boot or {}).get("ci_low"),
                "delta_ci_high": (boot or {}).get("ci_high"),
                "n_boot_used": (boot or {}).get("n_boot_used"),
                "score_pearson": float(np.corrcoef(d, p)[0, 1]) if len(part) > 2 else None,
            })
    fam_df = pd.DataFrame(fam_table)
    fam_df.to_csv(out / "exam04_family_table.csv", index=False, encoding="utf-8")

    model_table: list[dict] = []
    for model in MODELS:
        sub = pairs[(pairs["model_key"] == model) & (pairs["family"].isin(FAMILIES))]
        if sub.empty:
            continue
        boot = paired_bootstrap_mean_delta(sub)
        per_fam = fam_df[(fam_df["model_key"] == model) & (fam_df["family"].isin(FAMILIES))]
        model_table.append({
            "model_key": model,
            "n_sources": boot["n_sources"],
            "auc_digital_mean": float(per_fam["auc_digital"].mean()),
            "auc_physical_mean": float(per_fam["auc_physical"].mean()),
            "delta_mean": boot["delta_mean"],
            "delta_ci_low": boot["ci_low"],
            "delta_ci_high": boot["ci_high"],
            "delta_family_min": float(per_fam["delta"].min()),
            "delta_family_max": float(per_fam["delta"].max()),
            "n_boot_used": boot["n_boot_used"],
            "n_boot_skipped": boot["n_boot_skipped"],
        })
    model_df = pd.DataFrame(model_table)
    model_df.to_csv(out / "exam04_model_table.csv", index=False, encoding="utf-8")

    # session structure: physical AUC per session and the paired digital reference
    sess_table: list[dict] = []
    for model in MODELS:
        for sess, part in pairs[pairs["model_key"] == model].groupby("session"):
            fams = part[part["family"].isin(FAMILIES)]
            if fams.empty:
                continue
            y = fams["label"].to_numpy()
            sess_table.append({
                "model_key": model, "session": sess, "n_sources": int(fams["source_id"].nunique()),
                "auc_physical": auc_or_nan(y, fams["physical_score"].to_numpy(dtype=float)),
                "auc_digital": auc_or_nan(y, fams["digital_score"].to_numpy(dtype=float)),
            })
    sess_df = pd.DataFrame(sess_table)
    sess_df.to_csv(out / "exam04_session_table.csv", index=False, encoding="utf-8")

    # repeat consistency (same source captured twice in EXAM02)
    caps = pd.read_parquet(CAPTURES)
    rep = caps[caps["is_repeat"].astype(bool)].copy()
    base = caps[~caps["is_repeat"].astype(bool)].set_index(["source_id"]) 
    rep_table: list[dict] = []
    for model in MODELS:
        rows = []
        for r in rep.to_dict("records"):
            bid = r.get("repeat_of_source_id")
            if bid not in base.index:
                continue
            b = base.loc[bid]
            if isinstance(b, pd.DataFrame):
                b = b.iloc[0]
            a, c = float(r[model]), float(b[model])
            rows.append({"src": bid, "a": a, "c": c, "absdiff": abs(a - c)})
        if not rows:
            continue
        dd = pd.DataFrame(rows)
        rep_table.append({
            "model_key": model, "n_repeats": int(len(dd)),
            "median_absdiff": float(dd["absdiff"].median()),
            "p90_absdiff": float(dd["absdiff"].quantile(0.9)),
            "max_absdiff": float(dd["absdiff"].max()),
            "n_over_0_3": int((dd["absdiff"] > 0.3).sum()),
        })
    rep_df = pd.DataFrame(rep_table)
    rep_df.to_csv(out / "exam04_repeat_table.csv", index=False, encoding="utf-8")

    summary = {
        "run_id": run_id,
        "pairs_dir": str(pairs_dir.relative_to(PROJECT_ROOT)),
        "n_pairs": int(len(pairs)),
        "n_sources": int(pairs["source_id"].nunique()),
        "n_bootstrap": N_BOOT,
        "seed": SEED,
        "models": MODELS,
        "families": FAMILIES,
        "model_table": model_table,
        "sessions": {k: float(v) for k, v in
                     sess_df[sess_df["model_key"] == "swinv2_deploy"].set_index("session")["auc_physical"].items()},
        "notes": [
            "T_pilot digital scores were produced after the EXAM03 selection was frozen (DEC-0007); selection never read T_pilot.",
            "clean (C_pool) is reported for completeness but is the selection pool, so it is not the confirmatory estimate.",
            "Delta > 0 means the physical AUC is higher than the digital AUC on the identical sources.",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (out / "exam04_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("run_id", "n_pairs", "n_sources")}, ensure_ascii=False))
    print(model_df.to_string(index=False))
    print(rep_df.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
