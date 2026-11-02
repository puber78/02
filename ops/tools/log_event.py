"""Command-line access to the append-only pipeline event ledger.

Usage
-----
python ops/tools/log_event.py add --stage qc --title "..." --detail "..." [--run run_id]
python ops/tools/log_event.py backfill      # scan existing artifacts, add missing events
python ops/tools/log_event.py list [--tail N]

The ledger is ``ops/logs/EVENTS.jsonl`` (append-only).  ``backfill`` is
idempotent: it keys on ``run_id`` + ``stage`` and never rewrites a line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from proxy_selection.events import LEDGER, log_event, read_events  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text("utf-8"))


def _existing() -> set:
    return {(e.get("stage"), e.get("run_id")) for e in read_events()}


def backfill() -> int:
    seen = _existing()
    added = 0

    for summary_path in sorted((ROOT / "manifests" / "EXAM02_captures").glob("*/import_summary.json")):
        s = read_json(summary_path)
        run_id = summary_path.parent.name
        if ("import", run_id) in seen:
            continue
        log_event(
            "import",
            f"{s.get('session')} 导入",
            detail=(
                f"files={s.get('files')} imported={s.get('imported')} missing={s.get('missing')} "
                f"passed={s.get('passed')} failed={s.get('failed')}"
            ),
            run_id=run_id,
            extra={"failure_codes": s.get("failure_codes") or {}},
        )
        seen.add(("import", run_id))
        added += 1

    for metrics_path in sorted((ROOT / "scores" / "EXAM02").glob("*/physical_metrics.json")):
        m = read_json(metrics_path)
        run_id = metrics_path.parent.name
        if ("score", run_id) in seen:
            continue
        parts = [f"{a['model_key']}={a['auc']:.4f}" for a in m.get("models", []) if a.get("auc") is not None]
        log_event(
            "score",
            f"{m.get('session')} 物理评分",
            detail="; ".join(parts),
            run_id=run_id,
            extra={"n_samples": m.get("n_samples"), "import_run": m.get("import_run")},
        )
        seen.add(("score", run_id))
        added += 1
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--stage", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--detail", default="")
    a.add_argument("--run", default=None)

    sub.add_parser("backfill")

    lst = sub.add_parser("list")
    lst.add_argument("--tail", type=int, default=10)

    args = ap.parse_args()
    if args.cmd == "add":
        rec = log_event(args.stage, args.title, args.detail, args.run)
        print(json.dumps(rec, ensure_ascii=False))
        return 0
    if args.cmd == "backfill":
        n = backfill()
        print(f"backfilled {n} event(s); ledger={LEDGER}")
        return 0
    rows = read_events()
    for e in rows[-args.tail:]:
        print(f"{e['ts']}  {e['stage']:10s} {(e.get('run_id') or '-'):32s} {e['title']}  {e['detail']}")
    print(f"({len(rows)} events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
