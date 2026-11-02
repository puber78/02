"""Append-only pipeline event ledger (``ops/logs/EVENTS.jsonl``).

Every pipeline stage appends one JSON line, so the run history can be
reconstructed mechanically instead of being retyped into prose.  The file is
append-only by construction: :func:`log_event` only ever opens it in ``"a"``
mode, and nothing in this module rewrites or truncates it.

A logging failure must never take down a computation, so callers are expected
to wrap :func:`log_event` in ``try/except`` (the pipeline hooks do).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "ops" / "logs" / "EVENTS.jsonl"


def log_event(
    stage: str,
    title: str,
    detail: str = "",
    run_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Append one event record and return it.

    ``stage`` is a short machine key (``import``, ``qc``, ``score``, ...);
    ``title`` is a human-readable one-liner; ``detail`` carries the numbers.
    """
    rec: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stage": stage,
        "title": title,
        "detail": detail,
        "run_id": run_id,
    }
    if extra:
        rec["extra"] = extra
    target = Path(path) if path is not None else LEDGER
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    return rec


def read_events(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Read the ledger; malformed lines are skipped, never repaired in place."""
    target = Path(path) if path is not None else LEDGER
    if not target.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    for line in target.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows
