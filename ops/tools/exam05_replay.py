"""EXAM05 — 先导主问题：数字选型是否造成实质损失。

严格按 `predictions/PREDICTION05.yaml` 的预注册方案实现：

- 校准池：C_pool（200 源），数字族 clean + F1_jpeg + F2_scale + F3_blur + F4_color。
- 评价池：T_pilot（700 源），只用其物理 AUC。
- 规则：
    * 数字规则 = argmax_m S_dig(m)，S_dig = 5 个族 AUC 的等权平均（冻结定义）。
    * 真实直接规则 = argmax_m 物理 AUC。
- 预算 b ∈ {20, 40, 80}，b=40 为主。
- 外层重放：每个预算 200 次，C_pool 内无放回抽样，种子 20261026 + b。
- 评价不确定性：T_pilot 源级 bootstrap 2000 次。
- 联合推断：同时重抽 C_b（有放回）与 T_pilot（有放回），重跑选择，得到 regret 联合分布。
- 方向：DEC-0011。主口径 = 方向校正（校正方向在 C_pool 数字 clean 上确定，不读物理）；
  敏感性 = 声明方向（不校正）。

输出（全部归档，不覆盖）：
    manifests/EXAM05/run_<ts>_<hash>/summary.json
    manifests/EXAM05/run_<ts>_<hash>/per_replay.csv
    manifests/EXAM05/run_<ts>_<hash>/selection_freq.csv
    ops/logs/exam05_<run_id>.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from proxy_selection.io import write_json  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402

DIGITAL_EXAMS = {
    "EXAM03": PROJECT_ROOT / "scores/EXAM03/run_20261102T065427Z_1e0c09aa",
    "EXAM04": PROJECT_ROOT / "scores/EXAM04/run_20261102T071316Z_13a6975a",
}
PHYSICAL_PARQUET = PROJECT_ROOT / "manifests/EXAM02/EXAM02_captures_1000.parquet"
PHYS_METRICS = PROJECT_ROOT / "scores/EXAM02/run_20261102T062452Z_ed533f65/physical_metrics.json"

FAMILIES = ["clean", "F1_jpeg", "F2_scale", "F3_blur", "F4_color"]
MODEL_KEYS = ["swinv2_deploy", "siglip_ai_human", "swin_sdxl", "convnext_ai", "resnet_ai", "vit_ai_real"]
BUDGETS = [20, 40, 80]
MAIN_BUDGET = 40
REPLAYS = 200
JOINT_ITERS = 2000
SEED = 20261026
DELTA = 0.01


def auc(y: np.ndarray, s: np.ndarray) -> float:
    """Mann–Whitney AUC with tie correction."""
    y = np.asarray(y).astype(int)
    s = np.asarray(s, dtype=float)
    if len(s) == 0 or y.sum() == 0 or (y == 0).sum() == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    sorted_s = s[order]
    ranks = np.empty(len(s), dtype=float)
    i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and sorted_s[j + 1] == sorted_s[i]:
            j += 1
        ranks[i : j + 1] = (i + j + 2) / 2.0
        i = j + 1
    rank = np.empty(len(s), dtype=float)
    rank[order] = ranks
    n1 = int(y.sum())
    n0 = int(len(y) - n1)
    return float((rank[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def load_digital() -> tuple[pd.DataFrame, dict[str, str]]:
    frames = []
    for exam, d in DIGITAL_EXAMS.items():
        samples = pd.read_parquet(d / "digital_samples.parquet")
        scores = pd.read_parquet(d / "digital_scores.parquet")
        scores = scores[scores["status"] == "ok"]
        df = scores.merge(samples[["sample_id", "role", "family", "label"]], on="sample_id", how="left")
        df["exam"] = exam
        frames.append(df)
    dig = pd.concat(frames, ignore_index=True)

    metrics = json.loads(PHYS_METRICS.read_text(encoding="utf-8"))
    id2key = {m["model_id"]: m["model_key"] for m in metrics["models"]}
    dig["model_key"] = dig["model_id"].map(id2key)
    missing = dig[dig["model_key"].isna()]["model_id"].unique().tolist()
    if missing:
        raise SystemExit(f"unmapped model ids: {missing}")
    return dig, id2key


def load_physical() -> pd.DataFrame:
    phys = pd.read_parquet(PHYSICAL_PARQUET)
    phys = phys[phys["in_analysis"].astype(bool)]
    cols = ["source_id", "role", "label"] + MODEL_KEYS
    out = phys[cols].copy()
    # 重复拍摄：同一 source 多次时取均值（源级配对单位）
    agg = {"role": "first", "label": "first"}
    agg.update({k: "mean" for k in MODEL_KEYS})
    return out.groupby("source_id", as_index=False).agg(agg)


def build_arrays(dig: pd.DataFrame, role: str, keep: set[str]) -> tuple[list[str], np.ndarray, dict[str, np.ndarray]]:
    sub = dig[(dig["role"] == role) & (dig["family"].isin(FAMILIES)) & (dig["source_id"].isin(keep))]
    srcs = sorted(sub["source_id"].unique())
    idx = {s: i for i, s in enumerate(srcs)}
    labels = np.zeros(len(srcs), dtype=int)
    for s, lab in sub.groupby("source_id")["label"].first().items():
        labels[idx[s]] = int(lab)
    arr = {}
    for m in MODEL_KEYS:
        a = np.full((len(srcs), len(FAMILIES)), np.nan)
        sm = sub[sub["model_key"] == m]
        for s, fam, sc in zip(sm["source_id"], sm["family"], sm["raw_score"]):
            a[idx[s], FAMILIES.index(fam)] = sc
        arr[m] = a
    return srcs, labels, arr


def oriented(arr: dict[str, np.ndarray], direction: dict[str, int]) -> dict[str, np.ndarray]:
    return {m: (a if direction[m] > 0 else 1.0 - a) for m, a in arr.items()}


def calibrate_direction(dig_c: dict[str, np.ndarray], y: np.ndarray) -> dict[str, int]:
    """只用 C_pool 的数字 clean 分数确定方向（不读物理）。"""
    direction = {}
    for m in MODEL_KEYS:
        a = auc(y, dig_c[m][:, FAMILIES.index("clean")])
        direction[m] = 1 if a >= 0.5 else -1
    return direction


def s_dig_on(idx: np.ndarray, dc: dict[str, np.ndarray], y: np.ndarray) -> dict[str, float]:
    out = {}
    for m in MODEL_KEYS:
        vals = [auc(y[idx], dc[m][idx, f]) for f in range(len(FAMILIES))]
        out[m] = float(np.nanmean(vals))
    return out


def s_phys_on(idx: np.ndarray, pc: dict[str, np.ndarray], y: np.ndarray) -> dict[str, float]:
    return {m: auc(y[idx], pc[m][idx]) for m in MODEL_KEYS}


def pick(scores: dict[str, float]) -> str:
    # 平局按 model_key 字母序，确定性
    return max(MODEL_KEYS, key=lambda k: (scores[k], [-ord(c) for c in k]))


def pick_tie(scores: dict[str, float]) -> str:
    best = max(scores.values())
    return sorted([m for m in MODEL_KEYS if abs(scores[m] - best) < 1e-12])[0]


def summarize(replays: pd.DataFrame, eval_auc: dict[str, float], budget: int) -> dict:
    regrets = replays["regret_phys"].to_numpy()
    mean = float(np.mean(regrets))
    ci = [float(np.percentile(regrets, 2.5)), float(np.percentile(regrets, 97.5))]
    return {
        "budget": budget,
        "n_replays": int(len(replays)),
        "mean_regret": mean,
        "median_regret": float(np.median(regrets)),
        "ci95_replay_percentile": ci,
        "p_regret_positive": float(np.mean(regrets > 0)),
        "p_regret_above_delta": float(np.mean(regrets > DELTA)),
        "p_digital_better": float(np.mean(regrets < 0)),
        "mean_eval_auc_digital_choice": float(replays["eval_digital"].mean()),
        "mean_eval_auc_real_choice": float(replays["eval_real"].mean()),
        "digital_choice_count": replays["digital_choice"].value_counts().to_dict(),
        "real_choice_count": replays["real_choice"].value_counts().to_dict(),
        "n_distinct_digital_choice": int(replays["digital_choice"].nunique()),
        "n_distinct_real_choice": int(replays["real_choice"].nunique()),
        "eval_auc_T_pilot": eval_auc,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--replays", type=int, default=REPLAYS)
    ap.add_argument("--joint-iters", type=int, default=JOINT_ITERS)
    args = ap.parse_args()

    run_id = f"run_{pd.Timestamp.now('UTC').strftime('%Y%m%dT%H%M%SZ')}_{uuid.uuid4().hex[:8]}"
    out = Path(args.out_dir) if args.out_dir else (PROJECT_ROOT / "manifests/EXAM05" / run_id)
    out.mkdir(parents=True, exist_ok=True)
    log_path = PROJECT_ROOT / "ops/logs" / f"exam05_{run_id}.jsonl"
    rl = RunLogger.start(PROJECT_ROOT / "ops/logs", note=f"exam05 replay {run_id}")

    dig, id2key = load_digital()
    phys = load_physical()

    phys_c = phys[phys["role"] == "C_pool"].set_index("source_id")
    phys_t = phys[phys["role"] == "T_pilot"].set_index("source_id")
    c_keep = set(dig[dig["role"] == "C_pool"]["source_id"]) & set(phys_c.index)
    t_keep = set(dig[dig["role"] == "T_pilot"]["source_id"]) & set(phys_t.index)
    c_srcs, y_c, d_c = build_arrays(dig, "C_pool", c_keep)
    t_srcs, y_t, d_t = build_arrays(dig, "T_pilot", t_keep)
    rl_unused = None
    p_c = {m: phys_c.reindex(c_srcs)[m].to_numpy(float) for m in MODEL_KEYS}
    p_t = {m: phys_t.reindex(t_srcs)[m].to_numpy(float) for m in MODEL_KEYS}
    dropped_c = sorted(set(dig[dig["role"] == "C_pool"]["source_id"]) - c_keep)
    dropped_t = sorted(set(dig[dig["role"] == "T_pilot"]["source_id"]) - t_keep)

    rl.event("data", c_pool=len(c_srcs), t_pilot=len(t_srcs), families=FAMILIES,
           c_label_counts={int(k): int(v) for k, v in zip(*np.unique(y_c, return_counts=True))},
           t_label_counts={int(k): int(v) for k, v in zip(*np.unique(y_t, return_counts=True))},
           dropped_c_pool=dropped_c, dropped_t_pilot_count=len(dropped_t))

    results = {"run_id": run_id, "delta": DELTA, "main_budget": MAIN_BUDGET,
               "families": FAMILIES, "model_keys": MODEL_KEYS,
               "c_pool_n": len(c_srcs), "t_pilot_n": len(t_srcs), "seed": SEED}
    rng_master = np.random.default_rng(SEED)

    for label, do_dir in (("primary_direction_corrected", True), ("sensitivity_declared", False)):
        direction = calibrate_direction(d_c, y_c) if do_dir else {m: 1 for m in MODEL_KEYS}
        dco = oriented(d_c, direction)
        pco = oriented(p_c, direction)
        pto = oriented(p_t, direction)

        # 评价池点估计（固定 T_pilot 全池）
        eval_auc = {m: auc(y_t, pto[m]) for m in MODEL_KEYS}
        # 评价池源级 bootstrap 分布
        boot_eval = {m: [] for m in MODEL_KEYS}
        rng_eval = np.random.default_rng(SEED + 7)
        for _ in range(args.joint_iters):
            idx = rng_eval.integers(0, len(t_srcs), len(t_srcs))
            for m in MODEL_KEYS:
                boot_eval[m].append(auc(y_t[idx], pto[m][idx]))

        block = {"direction": direction, "eval_auc_T_pilot": eval_auc,
                 "eval_auc_T_pilot_ci": {m: [float(np.percentile(boot_eval[m], 2.5)),
                                             float(np.percentile(boot_eval[m], 97.5))] for m in MODEL_KEYS}}

        # 全池（b=200）参考选择
        full_dig = s_dig_on(np.arange(len(c_srcs)), dco, y_c)
        full_real = s_phys_on(np.arange(len(c_srcs)), pco, y_c)
        block["full_pool"] = {"s_dig": full_dig, "s_phys": full_real,
                              "digital_choice": pick_tie(full_dig), "real_choice": pick_tie(full_real)}

        frames = []
        for b in BUDGETS:
            rng = np.random.default_rng(SEED + b)
            recs = []
            for r in range(args.replays):
                idx = rng.choice(len(c_srcs), size=b, replace=False)
                sd = s_dig_on(idx, dco, y_c)
                sp = s_phys_on(idx, pco, y_c)
                dc_choice = pick_tie(sd)
                rl_choice = pick_tie(sp)
                recs.append({
                    "budget": b, "replay": r,
                    "digital_choice": dc_choice, "real_choice": rl_choice,
                    "eval_digital": eval_auc[dc_choice], "eval_real": eval_auc[rl_choice],
                    "regret_phys": eval_auc[rl_choice] - eval_auc[dc_choice],
                    "regret_vs_oracle": max(eval_auc.values()) - eval_auc[dc_choice],
                    "rank_digital_choice": int(sorted(eval_auc.values(), reverse=True).index(eval_auc[dc_choice]) + 1),
                })
            rep = pd.DataFrame(recs)
            frames.append(rep)
            block[f"budget_{b}"] = summarize(rep, eval_auc, b)
            rl.event("replay_done", budget=b, replays=len(rep),
                   mean_regret=block[f"budget_{b}"]["mean_regret"],
                   p_positive=block[f"budget_{b}"]["p_regret_positive"])

        allrep = pd.concat(frames, ignore_index=True)
        allrep.to_csv(out / f"per_replay_{label}.csv", index=False)

        # 联合推断（主预算）
        rng_j = np.random.default_rng(SEED + 1000)
        joint = []
        for it in range(args.joint_iters):
            ci = rng_j.integers(0, len(c_srcs), MAIN_BUDGET)
            ti = rng_j.integers(0, len(t_srcs), len(t_srcs))
            sd = s_dig_on(ci, dco, y_c)
            sp = s_phys_on(ci, pco, y_c)
            a = {m: auc(y_t[ti], pto[m][ti]) for m in MODEL_KEYS}
            joint.append(a[pick_tie(sp)] - a[pick_tie(sd)])
        joint = np.array(joint)
        block["joint_b40"] = {
            "mean_regret": float(joint.mean()),
            "ci95": [float(np.percentile(joint, 2.5)), float(np.percentile(joint, 97.5))],
            "p_regret_positive": float((joint > 0).mean()),
            "p_above_delta": float((joint > DELTA).mean()),
            "n_iters": args.joint_iters,
        }
        results[label] = block

    # 结论判读（按 PREDICTION05 事前规则）
    prim = results["primary_direction_corrected"]
    j = prim["joint_b40"]
    lo, hi = j["ci95"]
    if lo > DELTA:
        verdict = "DIGITAL_RULE_LOSES_ABOVE_DELTA"
    elif hi < -DELTA:
        verdict = "DIGITAL_RULE_BETTER_ABOVE_DELTA"
    elif lo > 0:
        verdict = "DIGITAL_RULE_LOSES_BELOW_DELTA"
    else:
        verdict = "INDISTINGUISHABLE_OR_NO_EVIDENCE"
    results["verdict"] = verdict
    results["verdict_rule"] = "联合 95% CI 对 [−δ, δ] 与 0 的相对位置；见 PREDICTION05 判读规则"

    write_json(out / "summary.json", results)
    pd.DataFrame([{"budget": b, "model_key": m, "count": c}
                  for b in BUDGETS
                  for m, c in prim[f"budget_{b}"]["digital_choice_count"].items()]
                 ).to_csv(out / "selection_freq.csv", index=False)
    rl.event("summary_written", verdict=verdict, out_dir=str(out))
    rl.finish("PASS")
    print(json.dumps({"run_id": run_id, "verdict": verdict,
                      "budget_40": prim["budget_40"], "joint_b40": j}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


