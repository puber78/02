"""Event ledger is append-only and never repairs the file in place."""

from __future__ import annotations

from proxy_selection.events import log_event, read_events


def test_log_event_appends_two_records(tmp_path):
    p = tmp_path / "EVENTS.jsonl"
    log_event("import", "a", detail="x", run_id="run_1", path=p)
    log_event("score", "b", detail="y", path=p)
    rows = read_events(p)
    assert [r["stage"] for r in rows] == ["import", "score"]
    assert rows[0]["run_id"] == "run_1"
    assert rows[1]["run_id"] is None


def test_read_events_skips_malformed_lines(tmp_path):
    p = tmp_path / "EVENTS.jsonl"
    p.write_text('{"ts": "t", "stage": "ok"}\nnot json\n', encoding="utf-8")
    rows = read_events(p)
    assert len(rows) == 1
    assert rows[0]["stage"] == "ok"


def test_log_event_is_pure_append(tmp_path):
    p = tmp_path / "EVENTS.jsonl"
    log_event("import", "first", path=p)
    before = p.read_text("utf-8")
    log_event("import", "second", path=p)
    after = p.read_text("utf-8")
    assert after.startswith(before)
    assert len(after.splitlines()) == 2
