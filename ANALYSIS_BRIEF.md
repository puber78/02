# Analysis brief — please review this study

This file is written so an outside analyst (human or model) can review the
project without reading all 1,600 files. Everything below is reproducible from
this repository; a `MANIFEST.sha256` covers every file.

## 1. Research question

Digital benchmarks rank AI-image detectors. Real deployments see **photographed
screens** (phone → display), which adds a channel: render, resample (moiré),
optics, sensor/ISP, JPEG, glare, colour shift. Two questions:

- **Q1 (measurement):** how much discriminative power (AUC) is lost when the same
  source images are captured physically, per detector?
- **Q2 (decision):** can digital measurements be used to *choose* a detector for
  physical deployment, and how much does a wrong choice cost?

## 2. Design as executed

- **6 frozen detectors**, no training: `swinv2_deploy` (SwinV2), `siglip_ai_human`
  (SigLIP), `swin_sdxl` (SwinV2-SDXL), `convnext_ai`, `resnet_ai`, `vit_ai_real`.
  Direction is defined by each model card's `id2label`; two cards declare
  inverted polarity (DEC-0011), so scores are orientation-corrected before AUC.
- **Three data roles** (`protocols/data_roles.yaml`):
  `C_pool` 200 sources (selection only), `T_pilot` 700 sources (evaluation only),
  `D_sel` 500 sources (digital-only, never displayed). Split groups are 1:1 with
  sources, so source-level bootstrap = planned split-group bootstrap.
- **Physical panel:** 998 frames, 10 sessions × 100, one device (Redmi K80),
  one 27" 1440p display, 45 cm, indoor light. 2 frames excluded for privacy
  (documented, not deleted). QC: ORB/SIFT registration, content NCC, geometry,
  sharpness (absolute + content-referenced), exposure (content-referenced clip
  excess), duplicate detection. Thresholds in `protocols/` and DEC-0005/0006.
- **Digital families** (`protocols/digital_families.yaml`, frozen before EXAM03):
  clean, F1 JPEG q75, F2 0.5× rescale, F3 Gaussian blur σ0.8, F4 colour jitter.
- **Selection rule (frozen):** `S_dig` = equal-weight mean AUC over 5 families,
  argmax over models; `S_worst`, `S_clean`, `S_rand` as secondaries.
- **Pre-registration:** `predictions/PREDICTION05.yaml` fixes b=40 (primary),
  δ=0.01, 200 replays, 2000 joint bootstrap, seed 20261026, and the conditions
  under which a null may be reported.

## 3. Key results

**EXAM04 (paired, T_pilot, 700 sources):** all detectors lose AUC under physical
capture except `swin_sdxl` (flat); Δ ranges −0.017 to −0.069. Family-level
decomposition shows the loss is *not* uniform: F3 blur and F4 colour dominate for
SwinV2 (−0.046, −0.059), while SigLIP loses on every family (−0.033 to −0.072).

**Headroom correction:** normalising Δ by (1 − AUC_digital) reverses the naive
reading "weak models suffer more": swinv2 −27.6%, siglip −45.5%, convnext −14.6%,
resnet −18.4%, vit −3.7%. The absolute ordering was a ceiling effect.

**EXAM05 (decision loss):** at b=40 the digital rule and a same-budget physical
rule agree on `swinv2_deploy`; regret +0.0031, 95% CI [−0.1215, +0.1215],
P(regret>0)=0.175; joint bootstrap CI [−0.1224, +0.1193]. Underpowered (L05-1):
the CI is 12× wider than δ. Failure mode: 40% of b=40 replays flip between
swinv2/siglip/sdxl; when wrong, mean loss 0.0305; catastrophic picks (AUC≈0.55
models) never happen at b≥40.

**Derived finding (F11):** selection noise at small budgets exceeds the true gap
between candidates (0.0445 between swinv2 and siglip), so "collect a few dozen
photos and pick the best" is not a reliable protocol — this is a sample-size
question, not a proxy-validity question.

## 4. Known weaknesses (please attack these)

1. **No blinding of the analyst.** Selection and analysis plan were frozen before
   the physical scores existed (B1, B2 in DEC-0010), but the analyst had already
   seen frame-level QC and pooled AUCs (B3 fails). Consequences are bounded but
   real: post-hoc choice of robustness checks, narrative framing.
2. **One device, one room, one display.** Generalisation to other capture chains
   is untested (`EXAM08` planned, currently shrunk).
3. **6 detectors, 3 of them near-chance physically.** Ranking claims are driven by
   the top-3; the bottom-3 contribute little information.
4. **No image-level replication within source** except 99 repeat frames, where
   |Δ| median ≤0.015 but the tail reaches 0.98 for at least one model — repeats
   are not exchangeable for some detectors.
5. **Moiré is uncontrolled**, not measured per frame (only indirectly via NCC and
   sharpness).

## 5. Where the project is stuck / what would help most

The original motivation for a "selection" paper collapsed with EXAM05 (no
detectable decision loss at realistic budgets). Two candidate pivots:

- **P1 — mechanism + remedy:** attribute the loss to channel segments (blur,
  resample, JPEG, colour, moiré), then test training-free remedies (test-time
  augmentation, small physical calibration set, restoration preprocessing) and
  report how many calibration frames are needed for a given AUC recovery.
- **P2 — protocol/benchmark paper:** publish the panel, the QC gates, the
  orientation-convention pitfall, and the sample-size curve for selection.

## 6. Questions for the reviewer

1. Is P1 novel enough for a top-tier venue, given TTA/calibration are known
   techniques? What is the minimal experiment that would make it a *method*
   contribution rather than an application note?
2. Which of the five weaknesses is fatal for a Q1 journal, and which can be
   handled by limitation statements?
3. Given 998 frames and 6 detectors, which additional analyses are cheap and
   would materially raise credibility (e.g. per-source random effects,
   decomposition of AUC into within/between-source components, power analysis)?
4. Is the "headroom normalisation" argument sound, or is it a post-hoc rescue?
5. If you were reviewing this for *IEEE TIFS / Pattern Recognition / CVIU*, what
   would you reject it for, in one sentence?

## 7. File map for a quick read

| Topic | File |
| --- | --- |
| Claim ledger (10 findings, strength, threats) | `reports/FINDINGS.md` |
| Physical panel result | `reports/RESULT02.md` |
| Digital families + frozen selection | `reports/RESULT03.md` |
| Same-source pairing | `reports/RESULT04.md` |
| Selection-loss replay | `reports/RESULT05.md` |
| Methodological decisions | `ops/decisions/DEC-0001..0011` |
| Pre-registrations | `predictions/PREDICTION01..05` |
| QC + import code | `scripts/import_captures.py`, `ops/tools/qc_summary.py` |
| Analysis code | `ops/tools/build_exam04.py`, `ops/tools/exam05_replay.py` |
| Event ledger | `ops/logs/EVENTS.jsonl` |

## 8. Reproduction contract

Every table in `reports/` is generated by a script under `ops/tools/` or
`scripts/`; every run writes `ops/logs/run_<id>.jsonl` and a `manifests/<EXAM>/run_<id>/`
directory. If a number is not traceable to a `run_id`, treat it as unreviewed.
