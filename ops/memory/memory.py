"""Append-only project memory journal with a hash chain.

Why
---
Long research projects outlive any single conversation context.  This module keeps
a durable, *append-only* record of every action, decision and result, so a later
session can search it instead of guessing.  Entries are never edited or deleted;
each one carries the SHA-256 of the previous entry, so any silent modification or
deletion is detectable by ``verify``.

Layout
------
  ops/memory/JOURNAL.jsonl   one canonical JSON object per line, append-only
  ops/memory/HEAD.json       count + last hash (a pointer, rewritten atomically)
  ops/memory/README.md       protocol (how and when to use it)

Entry
-----
  {id, ts, type, title, body, tags, refs, source, prev, hash}

  type   : action | decision | result | finding | environment | plan | incident
  refs   : message refs (mNNNNN) or file paths that anchor the entry
  source : who wrote it ("agent", "worklog:<sha8>", "backfill")

CLI
---
  python ops/memory/memory.py add --type decision --title "..." --body "..." [--tags a,b] [--refs m0123]
  python ops/memory/memory.py search "query" [--type result] [--limit 8]
  python ops/memory/memory.py verify
  python ops/memory/memory.py tail 5
  python ops/memory/memory.py sync-worklog
  python ops/memory/memory.py stats
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEM_DIR = ROOT / "ops" / "memory"
JOURNAL = MEM_DIR / "JOURNAL.jsonl"
HEAD = MEM_DIR / "HEAD.json"

GENESIS = "0" * 64


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(entry: dict) -> str:
    payload = {k: v for k, v in entry.items() if k != "hash"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def entry_hash(entry: dict) -> str:
    return hashlib.sha256(canonical(entry).encode("utf-8")).hexdigest()


def read_entries() -> list[dict]:
    if not JOURNAL.exists():
        return []
    out = []
    with JOURNAL.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_head() -> dict:
    if HEAD.exists():
        return json.loads(HEAD.read_text("utf-8"))
    return {"count": 0, "last_hash": GENESIS}


def _write_head(entries: list[dict]) -> None:
    head = {
        "count": len(entries),
        "last_hash": entries[-1]["hash"] if entries else GENESIS,
        "updated": _now(),
    }
    tmp = HEAD.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(head, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, HEAD)


def verify(quiet: bool = False) -> bool:
    entries = read_entries()
    prev = GENESIS
    for i, e in enumerate(entries):
        if e.get("prev") != prev:
            print(f"CHAIN BREAK at index {i} (id={e.get('id')}): prev mismatch")
            return False
        if entry_hash(e) != e.get("hash"):
            print(f"TAMPERED entry at index {i} (id={e.get('id')}): hash mismatch")
            return False
        prev = e["hash"]
    head = read_head()
    if head.get("count") != len(entries) or head.get("last_hash") != prev:
        print(f"HEAD MISMATCH: head={head.get('count')}/{head.get('last_hash','')[:12]} "
              f"journal={len(entries)}/{prev[:12]}")
        return False
    if not quiet:
        print(f"OK: {len(entries)} entries, chain intact, head {prev[:12]}…")
    return True


def append(
    type_: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    refs: list[str] | None = None,
    source: str = "agent",
    meta: dict | None = None,
) -> dict:
    entries = read_entries()
    prev = entries[-1]["hash"] if entries else GENESIS
    entry = {
        "id": f"{len(entries) + 1:05d}",
        "ts": _now(),
        "type": type_,
        "title": title.strip(),
        "body": body.strip(),
        "tags": tags or [],
        "refs": refs or [],
        "source": source,
        "prev": prev,
    }
    if meta:
        entry["meta"] = meta
    entry["hash"] = entry_hash(entry)
    MEM_DIR.mkdir(parents=True, exist_ok=True)
    with JOURNAL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    _write_head(entries + [entry])
    return entry


_TOKEN = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]+", re.I)


def _tokens(text: str) -> set[str]:
    out = set()
    for t in _TOKEN.findall(text.lower()):
        if len(t) > 1:
            out.add(t)
        if re.match(r"[\u4e00-\u9fff]", t):  # CJK: also index bigrams
            out.update(t[i : i + 2] for i in range(len(t) - 1))
    return out


def search(query: str, type_: str | None = None, limit: int = 8, since: str | None = None) -> list[tuple[float, dict]]:
    q = _tokens(query)
    if not q:
        return []
    scored = []
    for e in read_entries():
        if type_ and e.get("type") != type_:
            continue
        if since and e.get("ts", "") < since:
            continue
        hay = " ".join(
            [e.get("title", ""), e.get("body", ""), " ".join(e.get("tags", [])),
             " ".join(e.get("refs", []))]
        )
        doc = _tokens(hay)
        if not doc:
            continue
        overlap = len(q & doc)
        if not overlap:
            continue
        score = overlap / (len(q) ** 0.5) * (1.0 + 0.15 * min(overlap, 5))
        # exact phrase bonus
        if query.lower() in hay.lower():
            score *= 1.5
        scored.append((score, e))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:limit]


def sync_worklog(worklog: Path | None = None) -> int:
    """Append one entry per WORKLOG section that is not yet in the journal."""
    worklog = worklog or (ROOT / "ops" / "logs" / "WORKLOG.md")
    text = worklog.read_text("utf-8")
    existing = {e.get("meta", {}).get("worklog_sha") for e in read_entries()}
    sections = re.split(r"(?m)^## ", text)
    added = 0
    for sec in sections[1:]:
        head, _, body = sec.partition("\n")
        sha = hashlib.sha256(sec.encode("utf-8")).hexdigest()[:16]
        if sha in existing:
            continue
        append(
            "action",
            head.strip(),
            body.strip(),
            tags=["worklog"],
            source=f"worklog:{sha}",
            meta={"worklog_sha": sha},
        )
        added += 1
    return added


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--type", required=True)
    a.add_argument("--title", required=True)
    a.add_argument("--body", required=True)
    a.add_argument("--tags", default="")
    a.add_argument("--refs", default="")
    a.add_argument("--source", default="agent")

    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--type", default=None)
    s.add_argument("--limit", type=int, default=8)
    s.add_argument("--since", default=None)

    sub.add_parser("verify")
    sub.add_parser("stats")
    sub.add_parser("sync-worklog")
    t = sub.add_parser("tail")
    t.add_argument("n", type=int, default=5)

    args = ap.parse_args(argv)
    if args.cmd == "add":
        e = append(args.type, args.title, args.body,
                   [x.strip() for x in args.tags.split(",") if x.strip()],
                   [x.strip() for x in args.refs.split(",") if x.strip()],
                   source=args.source)
        print(f"appended {e['id']} ({e['type']}) {e['title']}")
    elif args.cmd == "search":
        hits = search(args.query, args.type, args.limit, args.since)
        if not hits:
            print("no match")
            return 0
        for score, e in hits:
            print(f"\n[{e['id']}] {e['ts']}  {e['type']}  score={score:.2f}  {e['title']}")
            body = e["body"]
            print("    " + body.replace("\n", "\n    ")[:1200])
    elif args.cmd == "verify":
        return 0 if verify() else 1
    elif args.cmd == "stats":
        entries = read_entries()
        from collections import Counter
        print(f"entries={len(entries)}")
        print(Counter(e["type"] for e in entries).most_common())
        if entries:
            print("first:", entries[0]["ts"], entries[0]["title"])
            print("last :", entries[-1]["ts"], entries[-1]["title"])
    elif args.cmd == "sync-worklog":
        n = sync_worklog()
        print(f"appended {n} worklog section(s)")
    elif args.cmd == "tail":
        for e in read_entries()[-args.n:]:
            print(f"[{e['id']}] {e['ts']} {e['type']} {e['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
