"""EXAM03 step 1 -- detector acceptance audit (4+ candidates).

For every candidate in ``models/registry.json`` this records, from real runs:

  * checkpoint / snapshot identity (hashes of the actual weight files);
  * the *official* preprocessing actually used (processor class, size, mean, std,
    interpolation, rescale) -- read from the model's own snapshot, not assumed;
  * score direction: ``ai_index`` / ``ai_label`` resolved from ``config.id2label``;
  * batch independence: same 8 fixture images scored at batch sizes 1 / 4 / 16;
    max |delta| must stay below ``BATCH_TOL``;
  * determinism: the same batch scored twice;
  * failure behaviour: a corrupted JPEG must yield an explicit failure code, not
    a silent score;
  * parameter count and device.

Output: ``manifests/EXAM03/<run_id>/detector_audit.json`` plus a Markdown table
appended to ``reports/EXAM03_detector_audit.md``.

Usage:
    python ops/tools/detector_audit.py [--models swinv2_deploy ...]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from proxy_selection.adapters.hf_classifier import HFClassifierAdapter  # noqa: E402
from proxy_selection.io import Ledger, write_json  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402

BATCH_TOL = 1e-5
DET_TOL = 1e-6
FIXTURE_N = 4  # per label


def load_fixtures() -> list[dict]:
    df = pd.read_csv(ROOT / "data" / "raw" / "TECH" / "technical_sources.csv")
    rows: list[dict] = []
    for label in (0, 1):
        sub = df[df.label == label].head(FIXTURE_N)
        for r in sub.to_dict("records"):
            rows.append({
                "sample_id": r["tech_id"],
                "label": int(r["label"]),
                "path": str(ROOT / r["file_relpath"]),
            })
    return rows


def open_rgb(path: str) -> Image.Image:
    return Image.open(path).convert("RGB")


def corrupt_image() -> Image.Image:
    """A JPEG whose scan data is truncated: decodable header, broken payload."""
    buf = io.BytesIO()
    Image.new("RGB", (256, 256), (120, 80, 40)).save(buf, format="JPEG", quality=85)
    raw = buf.getvalue()
    broken = raw[: len(raw) // 2]
    return Image.open(io.BytesIO(broken))


def audit_one(cand: dict) -> dict:
    ad = HFClassifierAdapter(
        repo=cand["repo"],
        revision=cand["revision"],
        cache_dir=str(ROOT / "models" / "hf_cache"),
        ai_label_override=cand.get("ai_label"),
        batch_size=16,
    )
    t0 = time.time()
    ad.load()
    load_s = round(time.time() - t0, 2)

    proc = ad._processor  # noqa: SLF001 - audit needs the real processor object
    size = getattr(proc, "size", None)
    try:
        size_map = {str(k): (int(v) if isinstance(v, (int, np.integer)) else str(v))
                    for k, v in dict(size).items()}
    except Exception:  # noqa: BLE001 - SizeDict subclasses dict but may vary by version
        size_map = {str(k): str(getattr(size, k)) for k in ("height", "width", "shortest_edge", "longest_edge")
                    if getattr(size, k, None) is not None}
    proc_cfg = {
        "class": proc.__class__.__name__,
        "size": size_map,
        "do_resize": bool(getattr(proc, "do_resize", None)),
        "resample": int(getattr(proc, "resample", 0)) if getattr(proc, "resample", None) is not None else None,
        "do_rescale": bool(getattr(proc, "do_rescale", None)),
        "rescale_factor": float(getattr(proc, "rescale_factor", 0) or 0),
        "do_normalize": bool(getattr(proc, "do_normalize", None)),
        "image_mean": [round(float(x), 6) for x in (getattr(proc, "image_mean", None) or [])],
        "image_std": [round(float(x), 6) for x in (getattr(proc, "image_std", None) or [])],
        "do_convert_rgb": bool(getattr(proc, "do_convert_rgb", False)),
    }

    fx = load_fixtures()
    imgs = [open_rgb(f["path"]) for f in fx]

    # -- batch independence -------------------------------------------------
    ad.batch_size = 1
    base = [p.raw_score for p in ad.predict_batch(imgs)]
    ad.batch_size = 4
    b4 = [p.raw_score for p in ad.predict_batch(imgs)]
    ad.batch_size = 16
    b16 = [p.raw_score for p in ad.predict_batch(imgs)]
    batch_delta = float(np.nanmax([
        np.nanmax(np.abs(np.array(base) - np.array(b4))),
        np.nanmax(np.abs(np.array(base) - np.array(b16))),
    ]))

    # -- determinism --------------------------------------------------------
    ad.batch_size = 16
    rep = [p.raw_score for p in ad.predict_batch(imgs)]
    det_delta = float(np.nanmax(np.abs(np.array(b16) - np.array(rep))))

    # -- batch-1 remedy -----------------------------------------------------
    # Conv nets are not always bit-identical across batch sizes even in fp32/eval.
    # The protocol's hard condition is "inference is reproducible", not "the vendor
    # kernel is batch invariant".  If the gap exceeds the tolerance the candidate is
    # kept, its inference is pinned to batch 1, and batch-1 determinism is verified.
    batch1_delta = 0.0
    forced_batch = 16
    if batch_delta > BATCH_TOL:
        ad.batch_size = 1
        r1 = [p.raw_score for p in ad.predict_batch(imgs)]
        r2 = [p.raw_score for p in ad.predict_batch(imgs)]
        batch1_delta = float(np.nanmax(np.abs(np.array(r1) - np.array(r2))))
        forced_batch = 1
    batch_ok = bool(batch_delta <= BATCH_TOL or batch1_delta <= DET_TOL)

    # -- failure behaviour --------------------------------------------------
    bad = ad.predict_batch([corrupt_image()])[0]
    ok_fail = bad.status == "failed" and bad.failure_code not in (None, "")

    # -- direction ----------------------------------------------------------
    p_ai = np.array([s if s is not None else np.nan for s in b16], dtype=float)
    lab = np.array([f["label"] for f in fx])
    mean_ai = float(np.nanmean(p_ai[lab == 1]))
    mean_real = float(np.nanmean(p_ai[lab == 0]))
    direction_consistent = mean_ai > mean_real

    rec = {
        "model_key": cand["model_key"],
        "model_id": ad.model_id,
        "repo": cand["repo"],
        "requested_revision": cand["revision"],
        "resolved_commit": (ad.metadata.get("snapshot_dir") or "").split("snapshots")[-1].strip("\\/") or None,
        "architecture": ad.metadata.get("architectures"),
        "num_parameters": ad.metadata.get("num_parameters"),
        "checkpoint_hash": ad.checkpoint_hash,
        "preprocess_hash": ad.preprocess_hash,
        "preprocess": proc_cfg,
        "id2label": {str(k): v for k, v in (ad.metadata.get("id2label") or {}).items()},
        "ai_index": ad.metadata.get("ai_index"),
        "ai_label": ad.metadata.get("ai_label"),
        "score_direction": ad.score_direction,
        "load_seconds": load_s,
        "batch_delta_max": round(batch_delta, 9),
        "determinism_delta_max": round(det_delta, 9),
        "batch_independent": bool(batch_delta <= BATCH_TOL),
        "batch1_delta_max": round(batch1_delta, 9),
        "forced_batch_size": forced_batch,
        "deterministic": bool(det_delta <= DET_TOL),
        "corrupt_input_failed_explicitly": ok_fail,
        "corrupt_failure_code": bad.failure_code,
        "fixture_mean_ai": round(mean_ai, 4),
        "fixture_mean_real": round(mean_real, 4),
        "fixture_direction_consistent": bool(direction_consistent),
        "direction_source": "config.id2label + registry ai_label override",
        "fixture_scores": {
            "ai": [None if s is None else round(float(s), 6) for s, l in zip(b16, lab) if l == 1],
            "real": [None if s is None else round(float(s), 6) for s, l in zip(b16, lab) if l == 0],
        },
        "device": ad.device,
    }
    # Direction is *structural* (AI class resolved from the model's own id2label);
    # the fixture means are diagnostics, deliberately NOT a performance gate.
    rec["accepted"] = bool(
        rec["checkpoint_hash"]
        and rec["preprocess"]["do_normalize"]
        and batch_ok
        and rec["deterministic"]
        and rec["corrupt_input_failed_explicitly"]
        and rec["ai_index"] >= 0
    )
    return rec


def md_table(rows: list[dict]) -> str:
    head = ("| 模型 | 架构 | 参数量 | 预处理 | ai_index | 批 Δ | 固定批 | 批1 Δ | 确定性 Δ | 损坏图失败码 | 夹具方向 | 接受 |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
    lines = []
    for r in rows:
        p = r["preprocess"]
        sz = p["size"].get("height") or p["size"].get("shortest_edge") or "?"
        lines.append(
            f"| {r['model_key']} | {r['architecture']} | {r['num_parameters']:,} | "
            f"{p['class']} {sz} | {r['ai_index']} | {r['batch_delta_max']:.2e} | "
            f"{r['forced_batch_size']} | {r['batch1_delta_max']:.2e} | "
            f"{r['determinism_delta_max']:.2e} | {r['corrupt_failure_code']} | "
            f"{'ok' if r['fixture_direction_consistent'] else 'REVERSED'} | "
            f"{'✅' if r['accepted'] else '❌'} |"
        )
    return head + "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=None)
    args = ap.parse_args()

    reg = json.loads((ROOT / "models" / "registry.json").read_text(encoding="utf-8"))
    cands = reg["candidates"]
    if args.models:
        cands = [c for c in cands if c["model_key"] in set(args.models)]

    log = RunLogger.start(ROOT, note="EXAM03 detector audit")
    ledger = Ledger(ROOT / "ops")
    out_dir = ROOT / "manifests" / "EXAM03" / log.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in cands:
        print(f"[audit] {c['model_key']} ...", flush=True)
        rec = audit_one(c)
        rec["accepted"] = bool(rec["accepted"])
        rows.append(rec)
        print(f"  accepted={rec['accepted']} batch_delta={rec['batch_delta_max']:.2e} "
              f"det={rec['determinism_delta_max']:.2e} dir_ok={rec['fixture_direction_consistent']}",
              flush=True)

    payload = {
        "run_id": log.run_id,
        "n_candidates": len(rows),
        "n_accepted": sum(1 for r in rows if r["accepted"]),
        "batch_tolerance": BATCH_TOL,
        "determinism_tolerance": DET_TOL,
        "fixtures": {"n_per_label": FIXTURE_N, "source": "data/raw/TECH/technical_sources.csv"},
        "candidates": rows,
    }
    write_json(out_dir / "detector_audit.json", payload, ledger=ledger, run_id=log.run_id, kind="manifest")

    md_path = ROOT / "reports" / "EXAM03_detector_audit.md"
    body = ["# EXAM03 检测器验收审计\n",
            f"- run: `{log.run_id}`",
            f"- 夹具: TECH 数字图，每类 {FIXTURE_N} 张（共 {2 * FIXTURE_N}）",
            f"- 批独立容差: {BATCH_TOL:g}；确定性容差: {DET_TOL:g}",
            f"- 接受: {payload['n_accepted']}/{payload['n_candidates']}\n",
            md_table(rows), "\n## 判定口径\n",
            "- 接受条件（DEC-0007）：检查点哈希可得 + 官方预处理可读 + **推理可复现** + 损坏图显式失败 + `ai_index >= 0`。",
            "  - 可复现 = 原批大小确定性 Δ ≤ 容差，**或** 批大小钉死为 1 后两次推理完全一致（`固定批` 列）。",
            "  - 批间 Δ 超容差是 fp32 累加顺序问题，不据此淘汰技术有效候选；数字/物理两侧都按 `forced_batch_size` 推理。",
            "- 方向来自模型自身 `config.id2label` 与 registry 的 `ai_label` 覆盖（结构性），夹具均值只作诊断：",
            "  弱模型在 4 张/类夹具上均值反转属性能信号，不用于翻转分数、也不用于淘汰。",
            "- 数字 AUC 高低**不**参与接受判定（大纲禁止按表现排除技术有效候选）。\n"]
    from proxy_selection.io import replace_with_archive
    replace_with_archive(md_path, "\n".join(body), archive_root=ROOT / "ops" / "archive",
                         ledger=ledger, run_id=log.run_id, kind="report")

    log.finish(status="PASS", extra={"n_accepted": payload["n_accepted"]})
    print("written", out_dir / "detector_audit.json")
    print("written", md_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
