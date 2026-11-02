"""Assemble a GitHub-ready bundle of the project (code, records, derived data).

Copies a curated subset into ``dist/github_repo`` — everything that is text or
small tabular, plus 384px thumbnails of the 998 analysed captures. Large
binaries (raw photos, rendered display assets, model shards, model cache) are
excluded on purpose and documented in ``EXCLUDED_DATA.md``.

Run:  python ops/tools/build_github_bundle.py [--thumbs-only] [--force]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "dist" / "github_repo"

# (source relative path, include globs or None for all files, max size MB)
INCLUDE = [
    ("src", None, 5),
    ("scripts", None, 5),
    ("tests", None, 5),
    ("tools", None, 5),
    ("ops/tools", None, 5),
    ("ops/memory", ["*.py", "*.md", "*.jsonl", "*.json"], 5),
    ("ops/decisions", None, 5),
    ("ops/logs", ["*.jsonl", "*.md"], 5),
    ("ops/manifests", None, 5),
    ("protocols", None, 5),
    ("predictions", None, 5),
    ("reports", None, 5),
    ("selections", None, 5),
    ("captures/kit", ["*.json", "*.bat", "*.md", "*.txt"], 2),
    ("manifests", None, 5),
    ("scores", ["*.parquet", "*.csv", "*.json", "*.md", "*.txt"], 5),
    ("data/raw/sources", ["*.csv", "*.json", "*.md"], 2),
]

TOP_FILES = [
    "README.md",
    "WORKLOG.md",
    "NEXT_ACTIONS.md",
    "INTERFACE_CONTRACT.md",
    "AGENTS.md",
    "EXCLUDED_DATA.md",
    "ANALYSIS_BRIEF.md",
    "CITATION.cff",
    "LICENSE",
    "NOTICE",
]

THUMB_WIDTH = 384
THUMB_QUALITY = 82


def sha256_file(p: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def copy_tree(rel: str, globs: list[str] | None, max_mb: float, rows: list[dict]) -> int:
    src = PROJECT_ROOT / rel
    if not src.exists():
        print(f"  skip missing dir: {rel}")
        return 0
    n = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if globs is not None and not any(f.match(g) for g in globs):
            continue
        size_mb = f.stat().st_size / (1024 * 1024)
        if size_mb > max_mb:
            continue
        dst = OUT / f.relative_to(PROJECT_ROOT)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        rows.append({"path": str(dst.relative_to(OUT)).replace("\\", "/"), "bytes": dst.stat().st_size})
        n += 1
    return n


def build_thumbs(rows: list[dict]) -> int:
    import cv2

    parquet = PROJECT_ROOT / "manifests/EXAM02/EXAM02_captures_1000.parquet"
    table = pq.read_table(parquet).to_pandas()
    out_dir = OUT / "data/thumbs"
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for _, r in table.iterrows():
        src = PROJECT_ROOT / "data/physical" / r["session"] / f"{r['capture_id']}.png"
        if not src.exists():
            print(f"  missing rectified: {src}")
            continue
        buf = np.fromfile(str(src), dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        if img is None:
            continue
        scale = THUMB_WIDTH / img.shape[1]
        small = cv2.resize(img, (THUMB_WIDTH, int(round(img.shape[0] * scale))), interpolation=cv2.INTER_AREA)
        ok, enc = cv2.imencode(".jpg", small, [int(cv2.IMWRITE_JPEG_QUALITY), THUMB_QUALITY])
        if not ok:
            continue
        dst = out_dir / f"{r['capture_id']}.jpg"
        dst.write_bytes(enc.tobytes())
        rows.append({"path": str(dst.relative_to(OUT)).replace("\\", "/"), "bytes": dst.stat().st_size})
        n += 1
    return n


def write_manifest(rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda d: d["path"])
    with (OUT / "MANIFEST.sha256").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            digest = sha256_file(OUT / r["path"])
            fh.write(f"{digest}  {r['path']}\n")
    with (OUT / "MANIFEST.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "bytes"])
        w.writeheader()
        w.writerows(rows)
    total = sum(r["bytes"] for r in rows)
    print(f"  manifest: {len(rows)} files, {total / (1024 * 1024):.1f} MB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--thumbs-only", action="store_true")
    ap.add_argument("--force", action="store_true", help="delete existing dist/github_repo first")
    args = ap.parse_args()

    if args.force and OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    if not args.thumbs_only:
        for rel, globs, max_mb in INCLUDE:
            n = copy_tree(rel, globs, max_mb, rows)
            print(f"  {rel}: {n} files")
        for name in TOP_FILES:
            src = PROJECT_ROOT / name
            if not src.exists():
                print(f"  skip missing file: {name}")
                continue
            dst = OUT / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            rows.append({"path": name, "bytes": dst.stat().st_size})

    n = build_thumbs(rows)
    print(f"  thumbs: {n} files")
    write_manifest(rows)
    print(f"done -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
