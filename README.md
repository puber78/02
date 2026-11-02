# Physical-Recapture Proxy Selection — research repository

A fully pre-registered, attempt-logged study of **what happens to AI-image
detectors when their inputs are photographed off a screen**, and of whether
digital-domain measurements can stand in for physical ones.

> **Status:** experiments EXAM01–EXAM05 complete; mechanism-attribution stage
> (E1/E2) is next. This repository is the *analysis* bundle: code, protocols,
> pre-registrations, per-run manifests, scores, decisions, logs and 384px
> thumbnails. Raw photos, rendered display assets, model weights and source
> shards are excluded (see `EXCLUDED_DATA.md`).

## What was done

| Stage | Question | Result |
| --- | --- | --- |
| EXAM01 | Is the scoring contract reproducible? | 6 frozen detectors, 480 rows, AUC gaps < 1e-6 on replay |
| EXAM02 | Collect a physical panel | **998 analysed frames** (10 sessions × 100), 2 frames excluded for privacy, 19/20 and 20/20 QC batches |
| EXAM03 | Digital baseline + frozen selection rule | S_dig ranking over clean+4 degradation families; `swinv2_deploy` selected (0.9032) |
| EXAM04 | Same-source digital→physical pairing | 899 sources / 17,994 pairs; **every detector loses AUC** except one flat model |
| EXAM05 | Does digital selection cost anything at budget *b*? | **Negative** at b=40: regret +0.0031, 95% CI [−0.12, +0.12]; underpowered (L05-1) |

Headline paired deltas (T_pilot, 700 sources, direction-corrected):

| detector | digital AUC | physical AUC | Δ [95% CI] |
| --- | ---: | ---: | --- |
| swinv2_deploy | 0.9168 | 0.8938 | −0.0230 [−0.054, −0.020] |
| siglip_ai_human | 0.8974 | 0.8507 | −0.0467 [−0.072, −0.040] |
| swin_sdxl | 0.7631 | 0.7726 | +0.0095 (CI spans 0) |
| convnext_ai | 0.6141 | 0.5577 | −0.0564 [−0.080, −0.045] |
| resnet_ai | 0.6228 | 0.5535 | −0.0692 [−0.165, −0.106] |
| vit_ai_real | 0.5422 | 0.5253 | −0.0169 [−0.036, 0.000] |

## Repository map

```
protocols/        scope, data roles, parameters, selectors, digital families (frozen)
predictions/      PREDICTION01..05 + amendments (pre-registrations, timestamps)
ops/decisions/    DEC-0001..0011 (every methodological change, with rationale)
src/              library: contracts, metrics (AUC/selection/attainable), adapters, scoring
scripts/          one script per stage (fetch, build kit, import, score, assemble)
ops/tools/        analysis + QC + audit + reporting utilities
tests/            82 unit tests (contracts, metrics, import alignment, logging)
reports/          RESULT01..05, FINDINGS.md (claim ledger), QC reports
manifests/        per-run JSON/CSV/parquet: queues, QC rows, pairs, audit, cost ledger
scores/           per-run score parquet + metric tables
data/thumbs/      998 × 384px rectified thumbnails (visual verification only)
ops/logs/         EVENTS.jsonl (append-only ledger) + per-run jsonl
ops/memory/       append-only hash-chained project journal
WORKLOG.md        narrative log (append-only)
```

## Reproduce

```bash
python -m venv .venv && . .venv/Scripts/activate     # Windows
pip install -r requirements.txt                      # torch, transformers, opencv, pyarrow
pytest -q                                            # 82 passed
python ops/tools/build_exam04.py                     # EXAM04 tables from manifests
python ops/tools/exam05_replay.py                    # EXAM05 replay (uses scores/*.parquet)
```

All numbers are computed from files in this repository; no notebook state, no
manual edits. Every artefact carries a `run_id` that appears in `ops/logs/`.

## Data availability

- Source images: COCO (CC-BY 4.0 subset) and ELSA1M (research licence) — IDs and
  licences recorded in `manifests/EXAM02/run_*/sources.parquet`.
- Physical captures: **not redistributed** (they show third-party content and a
  private room). 384px thumbnails are included for verification; raw JPEGs and
  1440px rectified crops are available from the authors on reasonable request.
- Model weights: public Hugging Face checkpoints; exact revisions pinned in
  `manifests/EXAM01/` and `models/registry.json`.

## Licence

Code: MIT (`LICENSE`). Derived tables and reports: CC-BY-4.0. Third-party image
rights remain with their owners (`NOTICE`).

## 中文摘要

本项目研究“AI 生成图像检测器在屏幕翻拍后是否失效、以及数字域测量能否替代实拍”。
已完成九个阶段中的前五个：998 帧实拍面板、6 个冻结检测器、数字四族退化、
同源配对（899 源 / 17,994 对）。核心结论：所有检测器在物理域都有 1.7–6.9 个
百分点的 AUC 下降，唯 sdxl 持平；"数字选型会选错模型"在 40 张预算下**不成立**
（regret +0.0031，CI 宽 ±0.12，属欠功效）。下一步做信道机制归因。

## 工作区说明（原 README 保留）

本目录是**新增**工作区，不修改执行包中的任何原始文件（原始 56 个文件的 SHA-256
已登记并与 `migration/迁移清单.json` 逐项核对一致，见 `ops/logs/06_input_verify.log`）。

| 路径 | 用途 |
|---|---|
| `protocols/` | 冻结的范围、数据角色、数字族、选择规则、容差、先导与确认合同（YAML） |
| `manifests/` | 来源/关系/显示/队列/分数清单（parquet）与模型注册表 |
| `scores/EXAMxx/<run_id>/` | 逐图分数（schema 见 `contracts/schema.py`） |
| `selections/EXAMxx/` | 选择日志（追加写入） |
| `results/RESULTxx.json`、`reports/RESULTxx.md` | 阶段结果记录与报告 |
| `src/proxy_selection/` | 研究代码（契约、指标、选择、适配器、日志） |
