"""Backfill ``content_ncc`` into an import run's qc.json (append-only provenance kept).

The importer used to record content NCC only through the ad-hoc content_match tool,
so runs imported after 2026-10-30 lost the column (NaN in the summary table).  This
tool recomputes NCC between each rectified capture and the display asset it should
show, writes it into ``qc.json``, and keeps a byte-identical backup of the original
file under ``ops/archive/``.

Usage:
    python ops/tools/backfill_content_ncc.py --run manifests/EXAM02_captures/<run_id>
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

REF_W, REF_H = 256, 144


def imread_u(path: Path) -> np.ndarray | None:
    if not path.exists():
        return None
    buf = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def ncc(a: np.ndarray, b: np.ndarray) -> float:
    ga = cv2.resize(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (REF_W, REF_H), interpolation=cv2.INTER_AREA)
    gb = cv2.resize(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), (REF_W, REF_H), interpolation=cv2.INTER_AREA)
    x = ga.astype(np.float64).ravel()
    y = gb.astype(np.float64).ravel()
    x = x - x.mean()
    y = y - y.mean()
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    if denom == 0:
        return float("nan")
    return float(np.dot(x, y) / denom)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    run_dir = Path(args.run)
    if not run_dir.is_absolute():
        run_dir = ROOT / run_dir
    qc_path = run_dir / "qc.json"
    rows = json.loads(qc_path.read_text(encoding="utf-8"))

    summary = json.loads((run_dir / "import_summary.json").read_text(encoding="utf-8"))
    session = summary["session"]
    queue_path = ROOT / "captures" / "kit" / f"queue_{session}.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    items = queue["items"] if isinstance(queue, dict) else queue
    by_seq = {int(i["seq"]): i for i in items}

    filled = 0
    for row in rows:
        if row.get("content_ncc") is not None:
            continue
        if not row.get("rectified"):
            continue
        it = by_seq.get(int(row["seq"]))
        if not it:
            continue
        rect = imread_u(ROOT / row["rectified"])
        asset = imread_u(ROOT / it["file_relpath"])
        if rect is None or asset is None:
            continue
        geoms = it.get("geometry") or {}
        x, y = geoms.get("content_x", 0), geoms.get("content_y", 0)
        w, h = geoms.get("content_w", asset.shape[1]), geoms.get("content_h", asset.shape[0])
        ref = asset[y : y + h, x : x + w]
        row["content_ncc"] = round(ncc(rect, ref), 6)
        filled += 1

    archive = ROOT / "ops" / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    backup = archive / f"qc_{run_dir.name}_before_ncc_backfill.json"
    if not backup.exists():
        shutil.copy2(qc_path, backup)
    qc_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"run": run_dir.name, "session": session, "filled": filled, "backup": str(backup.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
