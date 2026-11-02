"""RESULT02 audit: roles, overlap, queues, capture attempts, cost ledger.

Reads the pool manifest (sources/splits/display_assets), every capture import run
and the capture kit queues, then writes:

  manifests/EXAM02/result02_audit.json   machine-readable audit
  manifests/EXAM02_attempts.csv          one row per import attempt per session
  manifests/EXAM02_cost_ledger.csv       per-session attempts and wall-clock span

No numbers are invented: everything is recomputed from files on disk.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def load_pool_manifest() -> Path:
    runs = sorted((PROJECT_ROOT / "manifests" / "EXAM02").glob("run_*"),
                  key=lambda p: (p / "sources.parquet").stat().st_mtime)
    runs = [r for r in runs if (r / "sources.parquet").exists()]
    if not runs:
        raise SystemExit("no EXAM02 pool manifest run found")
    return runs[-1]


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def roles_audit(run: Path) -> dict:
    src = pd.read_parquet(run / "sources.parquet")
    splits = pd.read_parquet(run / "splits.parquet")
    disp = pd.read_parquet(run / "display_assets.parquet")
    src = src.merge(splits[["source_id", "split_role"]], on="source_id", how="left")

    role_counts = Counter(src["split_role"])
    role_label = {r: Counter(src.loc[src.split_role == r, "label"]) for r in role_counts}
    role_gen = {r: Counter(src.loc[src.split_role == r, "generator_id"]) for r in role_counts}

    groups_by_role = defaultdict(set)
    for role, grp in zip(src["split_role"], src["split_group_id"]):
        groups_by_role[role].add(grp)
    roles = sorted(groups_by_role)
    overlaps = {}
    for i, a in enumerate(roles):
        for b in roles[i + 1:]:
            overlaps[f"{a}|{b}"] = len(groups_by_role[a] & groups_by_role[b])

    prov_ok = int(src["provenance_uri"].notna().sum())
    lic_ok = int(src["license_id"].notna().sum())
    lic_ev_ok = int(src["license_evidence_sha256"].notna().sum())
    label_ev_ok = int(src["label_evidence_sha256"].notna().sum())
    disp_ids = set(disp["source_id"])
    missing_display = [s for s in src["source_id"] if s not in disp_ids]
    dims = Counter(zip(disp["width"], disp["height"]))
    color = Counter(disp["color_space"])

    return {
        "pool_run": run.name,
        "n_sources": int(len(src)),
        "role_counts": dict(role_counts),
        "role_label_counts": {r: dict(c) for r, c in role_label.items()},
        "role_generator_counts": {r: {str(k): v for k, v in c.items()} for r, c in role_gen.items()},
        "split_group_overlap": overlaps,
        "split_group_overlap_total": int(sum(overlaps.values())),
        "provenance_uri_coverage": prov_ok / len(src),
        "license_id_coverage": lic_ok / len(src),
        "license_evidence_coverage": lic_ev_ok / len(src),
        "label_evidence_coverage": label_ev_ok / len(src),
        "n_display_assets": int(len(disp)),
        "sources_without_display": len(missing_display),
        "display_dimensions": {f"{w}x{h}": n for (w, h), n in dims.items()},
        "display_color_spaces": dict(color),
        "duplicate_split_group_ids": int(len(src) - src["split_group_id"].nunique()),
        "duplicate_source_ids": int(len(src) - src["source_id"].nunique()),
    }


def queue_audit() -> dict:
    sessions = [f"main_s{i}" for i in range(1, 11)]
    out = {}
    total = 0
    repeats = 0
    seqs_all = []
    for s in sessions:
        q = json.loads((PROJECT_ROOT / "captures" / "kit" / f"queue_{s}.json").read_text(encoding="utf-8"))
        items = q["items"] if isinstance(q, dict) else q
        seqs = [int(i["seq"]) for i in items]
        rep = sum(1 for i in items if i.get("repeat_of_source_id"))
        ex = json.loads((PROJECT_ROOT / "data" / "EXCLUSIONS.json").read_text(encoding="utf-8"))
        n_ex = sum(1 for e in ex.get("exclusions", []) if str(e.get("session")) == s)
        out[s] = {"n_items": len(items), "seq_min": min(seqs), "seq_max": max(seqs),
                  "n_repeats": rep, "n_excluded": n_ex,
                  "roles": dict(Counter(i.get("role") for i in items))}
        total += len(items)
        repeats += rep
        seqs_all.extend(seqs)
    return {"sessions": out, "n_items_total": total, "n_repeats_total": repeats,
            "seq_min": min(seqs_all), "seq_max": max(seqs_all),
            "n_unique_seq": len(set(seqs_all))}


def attempts_audit() -> dict:
    runs = [r for r in (PROJECT_ROOT / "manifests" / "EXAM02_captures").glob("run_*")
            if (r / "import_summary.json").exists()]
    runs.sort(key=lambda p: (p / "import_summary.json").stat().st_mtime)
    rows = []
    by_session = defaultdict(list)
    for r in runs:
        f = r / "import_summary.json"
        if not f.exists():
            continue
        s = json.loads(f.read_text(encoding="utf-8"))
        qc_path = r / "qc.json"
        qc = json.loads(qc_path.read_text(encoding="utf-8")) if qc_path.exists() else []
        failed_seqs = sorted(int(x["seq"]) for x in qc if x.get("qc_status") != "passed")
        by_session[s.get("session")].append({
            "run": r.name,
            "started_at": s.get("started_at") or s.get("created_at"),
            "expected": s.get("expected"),
            "passed": s.get("passed"),
            "failed": s.get("failed"),
            "failure_codes": s.get("failure_codes", {}),
            "failed_seqs": failed_seqs,
        })
        rows.append([r.name, s.get("session"), s.get("expected"), s.get("passed"),
                     s.get("failed"), json.dumps(s.get("failure_codes", {}), ensure_ascii=False),
                     ";".join(str(x) for x in failed_seqs)])
    out = {}
    for sess, items in by_session.items():
        final = items[-1]
        ever_failed = sorted({q for it in items for q in it["failed_seqs"]})
        out[sess] = {"n_import_attempts": len(items), "final": final,
                     "ever_failed_seqs": ever_failed, "attempts": items}
    return {"by_session": out, "csv_rows": rows}


def retake_audit() -> dict:
    incoming = PROJECT_ROOT / "captures" / "incoming"
    out = {}
    for d in sorted(p for p in incoming.iterdir() if p.is_dir()):
        imgs = [p for p in d.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
        if imgs:
            times = sorted(_ts(datetime.fromtimestamp(p.stat().st_mtime).astimezone().isoformat()) for p in imgs)
            out[d.name] = {"n_files": len(imgs),
                           "first_mtime": times[0].isoformat(),
                           "last_mtime": times[-1].isoformat()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    pool_run = load_pool_manifest()
    audit = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "roles": roles_audit(pool_run),
        "queues": queue_audit(),
        "attempts": {k: v for k, v in attempts_audit()["by_session"].items()},
        "retake_dirs": retake_audit(),
    }

    if args.write:
        out_dir = PROJECT_ROOT / "manifests" / "EXAM02"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "result02_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        rows = attempts_audit()["csv_rows"]
        with (out_dir / "EXAM02_attempts.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["run", "session", "expected", "passed", "failed", "failure_codes", "failed_seqs"])
            w.writerows(rows)
        print("written", out_dir / "result02_audit.json")

    r = audit["roles"]
    print("roles", r["role_counts"], "overlap", r["split_group_overlap_total"])
    print("coverage prov/lic/lic_ev/label_ev",
          round(r["provenance_uri_coverage"], 4), round(r["license_id_coverage"], 4),
          round(r["license_evidence_coverage"], 4), round(r["label_evidence_coverage"], 4))
    print("display", r["n_display_assets"], r["display_dimensions"], "missing", r["sources_without_display"])
    print("queue", audit["queues"]["n_items_total"], "repeats", audit["queues"]["n_repeats_total"])
    for sess, v in audit["attempts"].items():
        print(sess, "attempts", v["n_import_attempts"], "final pass", v["final"]["passed"],
              "ever_failed", len(v["ever_failed_seqs"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
