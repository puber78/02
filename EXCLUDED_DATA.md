# Excluded data (and how to regenerate it)

This repository contains code, records and derived tables. The following
binaries are **deliberately not committed** because of size or third-party
rights. Sizes are as of 2026-11-02.

| Path | Size | Why excluded | How to regenerate |
| --- | ---: | --- | --- |
| `data/physical/**` (raw JPEG + 1440px rectified PNG) | 10.6 GB | contains third-party imagery and a private room; also mostly duplicated by retakes | re-run the capture protocol (`captures/kit/`, `protocols/`), or request from authors |
| `data/display/**` (rendered 2560×1440 panels) | 2.6 GB | deterministic render of source images | `scripts/build_capture_kit.py` + `scripts/make_digital_variants.py` |
| `data/digital/**`, `data/digital_t/**` | 3.4 GB | deterministic degradation of source images | `scripts/make_digital_variants.py --roles <role>` |
| `models/datasets/*.parquet` (COCO / ELSA shards) | 2.3 GB | redistributing source corpora is not permitted | `scripts/fetch_technical_samples.py` (HF endpoints) |
| `models/hf_cache/**` (detector weights) | 3.0 GB | public checkpoints, pinned revisions in `models/registry.json` | `HF_ENDPOINT=https://hf-mirror.com python scripts/score_*.py` (auto-download) |
| `ops/archive/**` (superseded runs, pre-fix backups) | 752 MB | audit history, not needed to reproduce results | kept locally; index in `ops/archive/README.md` |

Included instead:

- `data/thumbs/` — 998 × 384px JPEG of the **rectified, analysed** frames. Enough
  to check framing, moiré, glare and content identity; not enough to re-score.
- `manifests/` — per-frame QC rows (registration inliers, NCC, geometry,
  blur, luma, clip excess) so all QC-based claims are checkable.
- `scores/` — per-image detector outputs for every stage (parquet + metric tables).

## Privacy

Two items were excluded from the panel by the data owner before shooting
(recorded in `data/EXCLUSIONS.json`), and two frames were later dropped as
privacy-sensitive substitutes. No faces, plates or documents from the private
room appear in the included thumbnails beyond what is already on screen in the
third-party images.
