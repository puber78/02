"""Aggregate per-session QC for the main capture batch (s1..s10) into one table.

Scans manifests/EXAM02_captures/*/import_summary.json, keeps the latest import run per
session, and reports the numbers the protocol cares about:

  files/expected, passed, failures, mapping NCC, ORB inliers,
  visible screen fraction (median and range), corner deviation, blur floor, luma range

Outputs
-------
  reports/EXAM02_main_qc.md        human-readable table + flags
  manifests/EXAM02_qc_summary.csv  one row per session (machine-readable)

Usage
-----
  python ops/tools/qc_summary.py            # all sessions found
  python ops/tools/qc_summary.py --require 10
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CAPTURES = ROOT / "manifests" / "EXAM02_captures"


def latest_runs() -> dict[str, Path]:
    best: dict[str, Path] = {}
    for d in CAPTURES.iterdir():
        if not d.is_dir():
            continue
        f = d / "import_summary.json"
        if not f.exists():
            continue
        s = json.loads(f.read_text("utf-8"))["session"]
        if not s.startswith("main_s"):
            continue
        if s not in best or d.name > best[s].name:
            best[s] = d
    return best


def session_row(run: Path) -> dict:
    summary = json.loads((run / "import_summary.json").read_text("utf-8"))
    qc = json.loads((run / "qc.json").read_text("utf-8"))
    passed = [r for r in qc if r["qc_status"] == "passed"]
    excluded = [r for r in qc if r["qc_status"] == "excluded"]
    fails = [(r["seq"], r["failure_code"]) for r in qc if r["qc_status"] not in ("passed", "excluded")]
    ncc = [r["content_ncc"] for r in qc if r.get("content_ncc") is not None]
    if not ncc:
        cm_path = run / "content_match.json"
        ncc = [c["content_match"] for c in json.loads(cm_path.read_text("utf-8"))
               if c.get("content_match") is not None] if cm_path.exists() else []

    def col(k):
        return [r[k] for r in passed if r.get(k) is not None]

    vis = col("screen_visible_fraction") or col("screen_coverage")
    row = {
        "session": summary["session"],
        "run": run.name,
        "files": summary["files"],
        "expected": summary["expected"],
        "imported": summary["imported"],
        "missing": summary["missing"],
        "excluded": summary.get("excluded", 0),
        "passed": len(passed),
        "fails": ";".join(f"{s}:{c}" for s, c in fails) or "",
        "ncc_median": round(float(np.median(ncc)), 4) if ncc else None,
        "ncc_min": round(float(np.min(ncc)), 4) if ncc else None,
        "inliers_median": int(np.median(col("inliers"))) if col("inliers") else None,
        "visible_median": round(float(np.median(vis)), 4) if vis else None,
        "visible_min": round(float(np.min(vis)), 4) if vis else None,
        "visible_max": round(float(np.max(vis)), 4) if vis else None,
        "corner_median": round(float(np.median(col("corner_dev_deg"))), 2) if col("corner_dev_deg") else None,
        "corner_max": round(float(np.max(col("corner_dev_deg"))), 2) if col("corner_dev_deg") else None,
        "blur_min": round(float(np.min(col("blur_laplacian_var"))), 1) if col("blur_laplacian_var") else None,
        "luma_min": round(float(np.min(col("mean_luma"))), 1) if col("mean_luma") else None,
        "luma_max": round(float(np.max(col("mean_luma"))), 1) if col("mean_luma") else None,
        "clip_max": round(float(np.max(col("clip_high_fraction"))), 4) if col("clip_high_fraction") else None,
    }
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require", type=int, default=0, help="expected number of sessions")
    args = ap.parse_args()

    runs = latest_runs()
    rows = [session_row(runs[s]) for s in sorted(runs)]
    df = pd.DataFrame(rows)
    if df.empty:
        print("no main_s* import runs found")
        return 1

    total_pass = int(df["passed"].sum())
    total_exp = int(df["imported"].sum())
    flags = []
    for _, r in df.iterrows():
        if r["missing"]:
            flags.append(f"{r['session']}: missing {int(r['missing'])} capture(s)")
        if r["fails"]:
            flags.append(f"{r['session']}: {r['fails']}")
        if r["visible_min"] is not None and (r["visible_min"] < 0.62 or r["visible_max"] > 0.72):
            flags.append(f"{r['session']}: framing out of 0.62-0.72 ({r['visible_min']}-{r['visible_max']})")
        if r["corner_max"] is not None and r["corner_max"] > 6.0:
            flags.append(f"{r['session']}: corner deviation {r['corner_max']} deg")
        if r["blur_min"] is not None and r["blur_min"] < 80:
            flags.append(f"{r['session']}: blur floor {r['blur_min']} close to threshold 60")
        if r["ncc_min"] is not None and r["ncc_min"] < 0.85:
            flags.append(f"{r['session']}: weak content match {r['ncc_min']} (check mapping)")

    drift = ""
    if len(df) > 1:
        drift = (f"between-session framing drift: median {df.visible_median.min():.3f}-"
                 f"{df.visible_median.max():.3f}")

    lines = [
        "# 主批采集 QC 汇总（s1–s10）",
        "",
        f"- 生成时间：{pd.Timestamp.now(tz='Asia/Shanghai').strftime('%Y-%m-%d %H:%M')}（Asia/Shanghai）",
        f"- 会话数：**{len(df)}**；累计导入 **{total_exp}** 张，通过 **{total_pass}** 张",
        f"- 说明：每段取最新一次导入 run；失败样本按预注册规则排除并记录，不补分。",
        "",
        "| 段 | run | 文件/期望 | 通过 | 排除 | 失败 | NCC 中位(最低) | 内点中位 | 可见占画面 中位[min–max] | 角点偏差 中位/最大 | 清晰度最低 | 亮度范围 |",
        "|---|---|---:|---:|---:|---|---:|---:|---|---:|---:|---|",
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| {r['session']} | `{r['run']}` | {int(r['files'])}/{int(r['expected'])} | {int(r['passed'])} | "
            f"{int(r['excluded'])} | {r['fails'] or '—'} | {r['ncc_median']} ({r['ncc_min']}) | {r['inliers_median']} | "
            f"{r['visible_median']:.3f} [{r['visible_min']:.3f}–{r['visible_max']:.3f}] | "
            f"{r['corner_median']}° / {r['corner_max']}° | {r['blur_min']} | {r['luma_min']}–{r['luma_max']} |"
        )
    lines += ["", "## 标记", ""]
    lines += [f"- {f}" for f in flags] if flags else ["- 无异常"]
    if drift:
        lines.append(f"- {drift}")
    lines += [
        "",
        "> `screen_visible_fraction` = 投影屏幕四边形与画面交集 / 照片面积，是真实取景比例；",
        "> 早期版本的 `screen_coverage` 记录的是显示侧内容矩形占画布比例，已于 2026-10-30 更正。",
        "",
    ]
    out_md = ROOT / "reports" / "EXAM02_main_qc.md"
    out_md.write_text("\n".join(lines), encoding="utf-8")
    out_csv = ROOT / "manifests" / "EXAM02_qc_summary.csv"
    df.to_csv(out_csv, index=False, encoding="utf-8")

    print(df[["session", "files", "passed", "fails", "ncc_median", "visible_median", "blur_min"]].to_string(index=False))
    print("\nflags:")
    for f in flags:
        print(" -", f)
    print("\nwritten", out_md.relative_to(ROOT), "and", out_csv.relative_to(ROOT))
    try:  # ledger hook: logging must never break the tool
        sys.path.insert(0, str(ROOT / "src"))
        from proxy_selection.events import log_event

        log_event(
            "qc",
            "主批 QC 汇总",
            detail="; ".join(
                f"{r.session} {r.passed}/{r.files} pass, visible={r.visible_median}" for r in df.itertuples()
            ),
            extra={"sessions": int(len(df)), "flags": int(len(flags))},
        )
    except Exception:  # noqa: BLE001 - never fail the report over logging
        pass
    if args.require and len(df) < args.require:
        print(f"NOTE: only {len(df)}/{args.require} sessions present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
