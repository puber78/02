# WORKLOG（重建主档）

重建时间：2026-11-02T09:50:01Z

> 本文件在 2026-11-02 重建：原 `WORKLOG.md` 被一次覆盖写截断为 3 个残段。
> 原始事实来源：`ops/logs/EVENTS.jsonl`（append-only，逐事件）、`ops/memory/JOURNAL.jsonl`（哈希链记忆）、
> 每个 run 的 `ops/logs/run_*.jsonl`、`reports/*.md`、`manifests/**`、`scores/**`。
> 两份残存分节原文完整附于 §C，原件另存 `ops/archive/WORKLOG_fragment_*.md`。

## §A 事件时间线（来自 EVENTS.jsonl）

共 94 条事件。

- `2026-10-30T09:03:59Z` **[import]** tech 导入 —— files=20 imported=20 missing=None passed=20 failed=0（run_20261028T022131Z_0b40bc66）
- `2026-10-30T09:03:59Z` **[import]** tech 导入 —— files=20 imported=20 missing=None passed=18 failed=2（run_20261028T025632Z_7223a293）
- `2026-10-30T09:03:59Z` **[import]** main_s1 导入 —— files=96 imported=47 missing=53 passed=1 failed=99（run_20261030T081258Z_ec34e6f8）
- `2026-10-30T09:03:59Z` **[import]** main_s1 导入 —— files=96 imported=96 missing=4 passed=95 failed=5（run_20261030T081422Z_6f6b57a6）
- `2026-10-30T09:03:59Z` **[import]** main_s1 导入 —— files=96 imported=96 missing=0 passed=95 failed=1（run_20261030T081959Z_b7601c42）
- `2026-10-30T09:03:59Z` **[import]** main_s1 导入 —— files=100 imported=100 missing=0 passed=99 failed=1（run_20261030T083055Z_0033e829）
- `2026-10-30T09:03:59Z` **[import]** main_s2 导入 —— files=100 imported=100 missing=0 passed=99 failed=1（run_20261030T085838Z_01f75510）
- `2026-10-30T09:03:59Z` **[score]** tech 物理评分 —— swin_sdxl=0.8800; siglip_ai_human=0.8800; convnext_ai=0.2400; resnet_ai=0.2850; swinv2_deploy=0.8200; vit_ai_real=0.4200（run_20261028T022403Z_b3e0232d）
- `2026-10-30T09:03:59Z` **[score]** tech 物理评分 —— swin_sdxl=0.8625; siglip_ai_human=0.8750; convnext_ai=0.2750; resnet_ai=0.3750; swinv2_deploy=0.8375; vit_ai_real=0.4500（run_20261028T025735Z_52d7c46c）
- `2026-10-30T09:03:59Z` **[score]** main_s1 物理评分 —— swin_sdxl=0.7604; siglip_ai_human=0.8669; convnext_ai=0.6041; resnet_ai=0.4392; swinv2_deploy=0.8739; vit_ai_real=0.4665（run_20261030T083849Z_b52e307a）
- `2026-10-30T09:03:59Z` **[score]** main_s2 物理评分 —— swin_sdxl=0.8016; siglip_ai_human=0.8188; convnext_ai=0.4473; resnet_ai=0.4245; swinv2_deploy=0.9233; vit_ai_real=0.4155（run_20261030T090141Z_40d93bb3）
- `2026-10-30T09:04:21Z` **[qc]** 主批 QC 汇总 —— main_s1 99/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931
- `2026-10-30T09:17:48Z` **[import]** main_s3 导入 —— files=100 imported=99 missing=1 passed=29 failed=71（run_20261030T091627Z_6ee6ac79）
- `2026-10-30T09:23:30Z` **[import]** main_s3 导入 —— files=100 imported=98 missing=2 passed=93 failed=7（run_20261030T092220Z_acb3a319）
- `2026-10-30T09:24:51Z` **[import]** s3 首次导入（贪心对齐 bug，已归档） —— files=100 imported=99 passed=29 failed=71 (67 REGISTRATION_FAILED)（run_20261030T091627Z_6ee6ac79）
- `2026-10-30T09:24:56Z` **[qc]** 主批 QC 汇总 —— main_s1 99/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 93/100 pass, visible=0.6635
- `2026-10-30T09:49:46Z` **[import]** main_s3 导入 —— files=100 imported=98 missing=0 passed=98 failed=0（run_20261030T094833Z_122b06d8）
- `2026-10-30T09:51:00Z` **[qc]** 主批 QC 汇总 —— main_s1 99/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633
- `2026-10-30T09:52:05Z` **[score]** main_s3 物理评分 —— swin_sdxl=0.6808; siglip_ai_human=0.8079; convnext_ai=0.4417; resnet_ai=0.3125; swinv2_deploy=0.8671; vit_ai_real=0.4650（run_20261030T095115Z_29b8b048）
- `2026-10-30T09:56:36Z` **[import]** main_s4 导入 —— files=100 imported=99 missing=0 passed=99 failed=0（run_20261030T095524Z_44d0a556）
- `2026-10-30T10:00:35Z` **[import]** main_s4 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T095924Z_5b0d6491）
- `2026-10-30T10:01:19Z` **[qc]** 主批 QC 汇总 —— main_s1 99/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573
- `2026-10-30T10:03:15Z` **[score]** main_s4 物理评分 —— swin_sdxl=0.8363; siglip_ai_human=0.8587; convnext_ai=0.4750; resnet_ai=0.3493; swinv2_deploy=0.9216; vit_ai_real=0.4834（run_20261030T100225Z_9f73cff8）
- `2026-10-30T10:04:05Z` **[qc]** 主批 QC 汇总 —— main_s1 99/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573
- `2026-10-30T10:04:12Z` **[result]** s4 主批验收与评分 —— main_s4 100/100 passed, 0 fail, 0 excluded; NCC median 0.9653 min 0.8255(seq363 content-driven); inliers median 993 min 22(seq304 low-texture); 600/600 scoring rows; AUC swinv2 0.9216 siglip 0.8587 swin_sdxl 0.8363 vit 0.4834 convnext 0.4750 resnet 0.3493; progress seq400 patched with photo evidence（run_20261030T100225Z_9f73cff8）
- `2026-10-30T11:09:21Z` **[import]** main_s5 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T110801Z_b83753d9）
- `2026-10-30T11:11:48Z` **[score]** main_s5 物理评分 —— swin_sdxl=0.8005; siglip_ai_human=0.7965; convnext_ai=0.5982; resnet_ai=0.4036; swinv2_deploy=0.8826; vit_ai_real=0.5641（run_20261030T111057Z_9eab6f60）
- `2026-10-30T11:12:51Z` **[score]** main_s5 物理评分 —— swin_sdxl=0.8005; siglip_ai_human=0.7965; convnext_ai=0.5982; resnet_ai=0.4036; swinv2_deploy=0.8826; vit_ai_real=0.5641（run_20261030T111202Z_27313cb3）
- `2026-10-30T11:13:15Z` **[qc]** 主批 QC 汇总 —— main_s1 99/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654
- `2026-10-30T11:13:16Z` **[result]** s5 主批验收与评分 —— main_s5 100/100 passed; NCC median 0.9602 min 0.8236(seq445); inliers median 802 min 176; visibility 0.621-0.666; blur median 285 (content-smoothness, sharpness-ratio 2.27 vs s4 2.76); 600/600 rows; AUC swinv2 0.8826 swin_sdxl 0.8005 siglip 0.7965 convnext 0.5982 vit 0.5641 resnet 0.4036（run_20261030T111202Z_27313cb3）
- `2026-10-30T11:25:14Z` **[import]** main_s6 导入 —— files=100 imported=100 missing=0 passed=90 failed=10（run_20261030T112402Z_0380d911）
- `2026-10-30T11:29:59Z` **[import]** main_s6 导入 —— files=100 imported=100 missing=0 passed=98 failed=2（run_20261030T112845Z_0326018a）
- `2026-10-30T11:31:29Z` **[import]** main_s1 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T113014Z_082d2ef7）
- `2026-10-30T11:32:07Z` **[exam02]** DEC-0005 exposure gate v2; s6 98/100, s1 100/100 —— clip_excess<=0.05; retake seq 579,584 of s6（run_20261030T112845Z_0326018a）
- `2026-10-30T11:32:49Z` **[score]** tech 物理评分 —— swin_sdxl=0.8250; siglip_ai_human=0.8621; convnext_ai=0.5508; resnet_ai=0.4092; swinv2_deploy=0.8854; vit_ai_real=0.4579（run_20261030T113159Z_320f9325）
- `2026-10-30T11:34:07Z` **[score]** main_s6 物理评分 —— swin_sdxl=0.8250; siglip_ai_human=0.8621; convnext_ai=0.5508; resnet_ai=0.4092; swinv2_deploy=0.8854; vit_ai_real=0.4579（run_20261030T113319Z_e69e58b6）
- `2026-10-30T11:35:02Z` **[score]** main_s1 物理评分 —— swin_sdxl=0.7632; siglip_ai_human=0.8692; convnext_ai=0.5940; resnet_ai=0.4342; swinv2_deploy=0.8748; vit_ai_real=0.4712（run_20261030T113412Z_de5c9c99）
- `2026-10-30T11:35:45Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 98/100 pass, visible=0.6522
- `2026-10-30T11:36:03Z` **[exam02]** s6 scored 98 frames (588 rows) —— swinv2 0.8854 siglip 0.8621 sdxl 0.8250; run_20261030T113319Z_e69e58b6（run_20261030T112845Z_0326018a）
- `2026-10-30T11:36:03Z` **[exam02]** s1 re-scored 100 frames after DEC-0005 —— swinv2 0.8748 siglip 0.8692 sdxl 0.7632（run_20261030T113014Z_082d2ef7）
- `2026-10-30T11:42:43Z` **[import]** main_s6 导入 —— files=100 imported=100 missing=0 passed=99 failed=1（run_20261030T114127Z_1813e751）
- `2026-10-30T11:51:56Z` **[import]** main_s6 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T115038Z_383dbb63）
- `2026-10-30T11:52:55Z` **[score]** main_s6 物理评分 —— swin_sdxl=0.8279; siglip_ai_human=0.8611; convnext_ai=0.5466; resnet_ai=0.4134; swinv2_deploy=0.8872; vit_ai_real=0.4426（run_20261030T115204Z_74682f0b）
- `2026-10-30T11:53:13Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522
- `2026-10-30T11:53:13Z` **[exam02]** s6 100/100 after second retake —— run_20261030T115038Z_383dbb63; score run_20261030T115204Z_74682f0b swinv2 0.8872（run_20261030T115038Z_383dbb63）
- `2026-10-30T11:56:11Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522
- `2026-10-30T11:56:23Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522
- `2026-10-30T11:57:49Z` **[import]** main_s6 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T115641Z_95e0c122）
- `2026-10-30T12:26:52Z` **[import]** main_s7 导入 —— files=100 imported=100 missing=0 passed=98 failed=2（run_20261030T122524Z_f4c79344）
- `2026-10-30T12:27:18Z` **[exam02]** s7 imported 98/100; 2 exposure retakes; 8 duplicate copies archived —— run_20261030T122524Z_f4c79344; 605 (excess 7.6pp), 643 (9.9pp)（run_20261030T122524Z_f4c79344）
- `2026-10-30T13:03:36Z` **[import]** main_s7 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T130221Z_daa0fe63）
- `2026-10-30T13:04:48Z` **[score]** main_s7 物理评分 —— swin_sdxl=0.7563; siglip_ai_human=0.8375; convnext_ai=0.5270; resnet_ai=0.4922; swinv2_deploy=0.9208; vit_ai_real=0.5470（run_20261030T130357Z_04a112aa）
- `2026-10-30T13:04:54Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65
- `2026-10-30T13:05:05Z` **[exam02]** s7 100/100 final —— run_20261030T130221Z_daa0fe63; scores run_20261030T130357Z_04a112aa swinv2 0.9208（run_20261030T130221Z_daa0fe63）
- `2026-10-30T13:09:03Z` **[import]** main_s8 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T130747Z_58dd6ff2）
- `2026-10-30T13:10:03Z` **[score]** main_s8 物理评分 —— swin_sdxl=0.8211; siglip_ai_human=0.8683; convnext_ai=0.5314; resnet_ai=0.4158; swinv2_deploy=0.8892; vit_ai_real=0.4718（run_20261030T130911Z_bfef8a42）
- `2026-10-30T13:10:09Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65; main_s8 100/100 pass, visible=0.6462
- `2026-10-30T13:10:18Z` **[exam02]** s8 100/100 first pass —— run_20261030T130747Z_58dd6ff2; scores run_20261030T130911Z_bfef8a42 swinv2 0.8892（run_20261030T130747Z_58dd6ff2）
- `2026-10-30T13:14:35Z` **[import]** main_s9 导入 —— files=100 imported=99 missing=0 passed=98 failed=1（run_20261030T131316Z_e05cbebc）
- `2026-10-30T13:16:46Z` **[import]** main_s9 导入 —— files=100 imported=99 missing=0 passed=98 failed=1（run_20261030T131528Z_0019e6a2）
- `2026-10-30T13:18:15Z` **[import]** main_s9 导入 —— files=100 imported=100 missing=0 passed=99 failed=1（run_20261030T131658Z_e9bd245b）
- `2026-10-30T13:18:31Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65; main_s8 100/100 pass, visible=0.6462; main_s9 99/100 pass, visible=0.6477
- `2026-10-30T13:18:43Z` **[exam02]** s9 99/100, 1 exposure retake —— run_20261030T131658Z_e9bd245b; 858 EXPOSURE excess 0.064; seq900 progress entry reconstructed from photo（run_20261030T131658Z_e9bd245b）
- `2026-10-30T13:25:18Z` **[import]** main_s9 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261030T132356Z_ed6969fb）
- `2026-10-30T13:25:25Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65; main_s8 100/100 pass, visible=0.6462; main_s9 100/100 pass, visible=0.6477
- `2026-10-30T13:25:26Z` **[exam02]** s9 100/100 after retake —— run_20261030T132356Z_ed6969fb; 858 retake excess -0.085; 100 pass（run_20261030T132356Z_ed6969fb）
- `2026-10-30T13:26:27Z` **[score]** main_s9 物理评分 —— swin_sdxl=0.8063; siglip_ai_human=0.8231; convnext_ai=0.6575; resnet_ai=0.5554; swinv2_deploy=0.9020; vit_ai_real=0.4050（run_20261030T132528Z_eec2b936）
- `2026-10-30T13:28:52Z` **[import]** main_s10 导入 —— files=100 imported=99 missing=0 passed=97 failed=2（run_20261030T132736Z_27640268）
- `2026-10-30T13:30:23Z` **[import]** main_s10 导入 —— files=100 imported=100 missing=0 passed=98 failed=2（run_20261030T132908Z_230a35e5）
- `2026-10-30T13:30:46Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s10 98/100 pass, visible=0.6352; main_s2 99/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65; main_s8 100/100 pass, visible=0.6462; main_s9 100/100 pass, visible=0.6477
- `2026-10-30T13:30:47Z` **[exam02]** s10 98/100, 2 exposure retakes —— run_20261030T132932Z_4a0ffc04? check; 963 excess 0.109, 996 excess 0.068
- `2026-10-30T13:31:00Z` **[exam02]** s10 98/100, 2 exposure retakes —— run_20261030T132908Z_230a35e5; 963 excess 0.109, 996 excess 0.068; seq1000 progress entry reconstructed from photo（run_20261030T132908Z_230a35e5）
- `2026-11-02T06:10:11Z` **[import]** main_s10 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261102T060856Z_fae6174b）
- `2026-11-02T06:11:50Z` **[score]** main_s10 物理评分 —— swin_sdxl=0.7360; siglip_ai_human=0.8506; convnext_ai=0.5853; resnet_ai=0.3890; swinv2_deploy=0.8750; vit_ai_real=0.4659（run_20261102T061026Z_73fb77c5）
- `2026-11-02T06:17:33Z` **[import]** main_s2 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261102T061617Z_de8a919d）
- `2026-11-02T06:18:40Z` **[score]** main_s2 物理评分 —— swin_sdxl=0.7959; siglip_ai_human=0.8155; convnext_ai=0.4546; resnet_ai=0.4234; swinv2_deploy=0.9232; vit_ai_real=0.4250（run_20261102T061748Z_09a1077d）
- `2026-11-02T06:18:50Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s10 100/100 pass, visible=0.6352; main_s2 100/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65; main_s8 100/100 pass, visible=0.6462; main_s9 100/100 pass, visible=0.6477
- `2026-11-02T06:20:45Z` **[import]** main_s6 导入 —— files=100 imported=100 missing=0 passed=100 failed=0（run_20261102T061931Z_1160f3f0）
- `2026-11-02T06:21:45Z` **[score]** main_s6 物理评分 —— swin_sdxl=0.8279; siglip_ai_human=0.8611; convnext_ai=0.5466; resnet_ai=0.4134; swinv2_deploy=0.8872; vit_ai_real=0.4426（run_20261102T062055Z_16f60b1d）
- `2026-11-02T06:24:41Z` **[import]** tech 导入 —— files=20 imported=20 missing=0 passed=19 failed=1（run_20261102T062425Z_b4159b3e）
- `2026-11-02T06:25:13Z` **[score]** tech 物理评分 —— swin_sdxl=0.8444; siglip_ai_human=0.8667; convnext_ai=0.2889; resnet_ai=0.3444; swinv2_deploy=0.7778; vit_ai_real=0.4778（run_20261102T062452Z_ed533f65）
- `2026-11-02T06:27:53Z` **[import]** main_s10 retake merged (963,996) —— run_20261102T060856Z_fae6174b 100/100（run_20261102T060856Z_fae6174b）
- `2026-11-02T06:27:53Z` **[score]** main_s10 rescored —— 600 rows, 0 failed（run_20261102T061026Z_73fb77c5）
- `2026-11-02T06:27:53Z` **[qc]** tech re-import under v2 gates —— 20 attempts, 19 passed, 1 BLUR（run_20261102T062425Z_b4159b3e）
- `2026-11-02T06:27:53Z` **[score]** tech pilot rescored —— 114 rows, 0 failed（run_20261102T062452Z_ed533f65）
- `2026-11-02T06:27:53Z` **[analysis]** EXAM02 dataset assembled —— 998 captures, 998 in_analysis, 0 missing scores
- `2026-11-02T06:27:53Z` **[report]** RESULT02 written —— reports/RESULT02.md
- `2026-11-02T06:28:13Z` **[qc]** 主批 QC 汇总 —— main_s1 100/100 pass, visible=0.6663; main_s10 100/100 pass, visible=0.6352; main_s2 100/100 pass, visible=0.6931; main_s3 98/100 pass, visible=0.6633; main_s4 100/100 pass, visible=0.6573; main_s5 100/100 pass, visible=0.654; main_s6 100/100 pass, visible=0.6522; main_s7 100/100 pass, visible=0.65; main_s8 100/100 pass, visible=0.6462; main_s9 100/100 pass, visible=0.6477
- `2026-11-02T07:24:09Z` **[exam04]** EXAM04 same-source pairing complete —— 899 sources, 17994 pairs, 0 missing; swinv2 digital 0.9236 -> physical 0.8938 (delta -0.0297 [-0.0468,-0.0132]); siglip -0.0518; resnet +0.0659（run_20261102T072215Z_e00f6ab5）
- `2026-11-02T07:24:09Z` **[score]** T_pilot digital families scored (post-freeze) —— 21000 rows, 0 failed; clean+F1-F4 x 700 T_pilot sources; used only for EXAM04 evaluation（run_20261102T071316Z_13a6975a）
- `2026-11-02T07:26:22Z` **[exam04]** EXAM04 packaging: PREDICTION04, DEC-0009/0010, cost ledger —— PREDICTION04 marked RETROSPECTIVE_RECORD; DEC-0009 T_pilot digital post-freeze; DEC-0010 blind-side disclosure; cost_ledger.json 998 frames/29 runs/138 failures（run_20261102T072215Z_e00f6ab5）
- `2026-11-02T07:33:47Z` **[exam04]** Blind-side analysis revised: procedure+plan blind, analyst not blind —— Three-element adjudication: B1 selection program blind (frozen 06:39/06:45, T_pilot digital generated 07:11), B2 analysis plan blind (pilot_analysis.yaml created 2026-10-26T16:27 before first capture), B3 analyst NOT blind (EXAM02 QC+AUC preceded). Family-level robustness: siglip all-negative, resnet all-positive, sdxl mixed, swinv2 negative driven by F3/F4. DEC-0010 amended; RESULT04 8.0 updated.（run_20261102T072215Z_e00f6ab5）
- `2026-11-02T09:23:45Z` **[exam04]** Orientation convention corrected: all candidates drop under declared-label orientation —— resnet_ai/vit_ai_real have inverted output vs declared id2label (digital AUC 0.345/0.458). Under corrected orientation: swinv2 -0.0230 [-0.0544,-0.0200], siglip -0.0467, sdxl +0.0095 (CI crosses 0), convnext -0.0564, resnet -0.0692, vit -0.0169. Previous 'weak models rise' claim retracted; DEC-0011 written; RESULT04 2/3 and FINDINGS F01 updated.（run_20261102T072215Z_e00f6ab5）
- `2026-11-02T09:49:08Z` **[exam05]** EXAM05 replay: no detectable selection loss at b=40, CI +-0.12 —— Pre-registered PREDICTION05 (2026-11-02T09:50Z) then ran 200 replays/budget with joint bootstrap. b=40 mean regret +0.0031 (replay) / -0.0033 (joint), 95% CI [-0.122,+0.119]; P(regret>0)=0.175. b=80 CI [-0.078,+0.045]. Full-pool both rules pick swinv2_deploy. Falsification condition 'b=80 CI wider than +-0.05' triggered -> L05-1 underpowered. Decision sensitivity (declared orientation) unchanged.（run_20261102T094759Z_04fc8209）

## §B 阶段性结果索引

| 报告 | 文件 |
| --- | --- |
| EXAM02_main_qc.md | `reports/EXAM02_main_qc.md` |
| EXAM02_s10_qc.md | `reports/EXAM02_s10_qc.md` |
| EXAM02_s1_qc.md | `reports/EXAM02_s1_qc.md` |
| EXAM02_s3_qc.md | `reports/EXAM02_s3_qc.md` |
| EXAM02_s4_qc.md | `reports/EXAM02_s4_qc.md` |
| EXAM02_s5_qc.md | `reports/EXAM02_s5_qc.md` |
| EXAM02_s6_qc.md | `reports/EXAM02_s6_qc.md` |
| EXAM02_s7_qc.md | `reports/EXAM02_s7_qc.md` |
| EXAM02_s8_qc.md | `reports/EXAM02_s8_qc.md` |
| EXAM02_s9_qc.md | `reports/EXAM02_s9_qc.md` |
| EXAM02_tech_qc.md | `reports/EXAM02_tech_qc.md` |
| EXAM03_detector_audit.md | `reports/EXAM03_detector_audit.md` |
| FINDINGS.md | `reports/FINDINGS.md` |
| INTERFACE_CONTRACT.md | `reports/INTERFACE_CONTRACT.md` |
| RESULT01.md | `reports/RESULT01.md` |
| RESULT02.md | `reports/RESULT02.md` |
| RESULT03.md | `reports/RESULT03.md` |
| RESULT04.md | `reports/RESULT04.md` |
| RESULT05.md | `reports/RESULT05.md` |

记忆日志：73 条（`ops/memory/JOURNAL.jsonl`，哈希链）。

## §C 残存分节原文

### C.1 根 WORKLOG.md 残段（重建前）

## 19. s4 主批：导入、进度补记、QC、评分

- 时间：2026-10-30 17:58–18:05（Asia/Shanghai）。
- 到达：captures/incoming/main_s4/ 100 个 JPEG，17:32:48–17:37:09，4096×3072。
- 首次导入：expected 99（progress 缺 seq 400）→ 99/99 通过、文件 100 多一张。
  - 逐张内容匹配确认末三张 = seq 398/399/400（1064/1232/1153 好匹配），说明只是查看器未再按空格推进。
  - 备份 queue_main_s4_progress.json.bak_progress_fix，补写 seq 400 的 shot 记录并注明依据；
    重导 expected 100 → **100/100 通过、0 失败、0 排除**（run 
un_20261030T095924Z_5b0d6491）。
- QC：NCC 中位 0.9653、最低 0.8255（seq 363，石砌钟楼+天空渐变，邻张 0.964、内点 1139，判定内容属性）；
  内点中位 993、最低 22（seq 304 低纹理）；摆位 0.644–0.688（中位 0.657）；角点中位 0.48°、最大 3.24°；
  清晰度最低 153.9、中位 731.8；高光最高 3.5%（336/360/397）。
- 评分：scores/EXAM02/run_20261030T100225Z_9f73cff8，600 行、0 失败；
  AUC swinv2 0.9216、siglip 0.8587、swin_sdxl 0.8363、vit 0.4834、convnext 0.4750、resnet 0.3493。
  注意：--models 是模型键过滤器，误传 registry 路径导致空行集并触发 coverage_report 崩溃；
  已为 coverage_report 增加空表分支 + 回归测试（82 项测试通过）。
- 产物：
eports/EXAM02_s4_qc.md、总表更新（新增 s4 行）、事件账本 1 条、记忆条目 1 条。
- 结论：s4 是首段零瑕疵；s5 起提示"末张后多按一次空格"。


## 20. s5 主批：导入、清晰度专项复核、评分

- 时间：2026-10-30 19:07–19:14（Asia/Shanghai）。
- 到达：`captures/incoming/main_s5/` 100 个 JPEG，18:58:14–19:03:20；progress 100/100。
- 导入：**100/100 通过、0 失败**（run `run_20261030T110801Z_b83753d9`）。
- QC：NCC 中位 0.9602、最低 0.8236（seq 445，邻张 0.977/0.938，非错位）；内点中位 802、最低 176；
  可见面积 0.621–0.666；角点中位 0.78°、最大 2.86°；高光最高 0.57%。
- **清晰度异常复核**：Laplacian 中位 285（s1–s4 为 600–1200），26 张 <200。
  - 亮度-清晰度相关 0.21 → 非“内容暗”；
  - 矫正图/资产 Laplacian 比值：s5 2.27 vs s4 2.76（低 18%），与 2.8 倍原始落差不成比例；
  - 人工放大 seq 417/428 原图，像素栅格与细节可辨，无拖影。
  → 判定内容高频少，接受；今后每段固定报告该比值，并在汇总中按会话/内容难度分层。
- 评分：`scores/EXAM02/run_20261030T111202Z_27313cb3`，600 行 0 失败；
  AUC swinv2 0.8826、swin_sdxl 0.8005、siglip 0.7965、convnext 0.5982、vit 0.5641、resnet 0.4036。
  后三名向 0.5 收敛（convnext 0.44→0.60、vit 0.47→0.56、resnet 0.27→0.40），列为“内容难度”待分层检验。
  同参数重跑一次（`run_20261030T111057Z_9eab6f60`）AUC 逐位一致，确认确定性，两份均保留。
- 产物：`reports/EXAM02_s5_qc.md`、总表更新、事件账本 1 条、记忆 00058–00059。

## 39. EXAM02 收尾：技术批重导、装配表与 RESULT02

- 时间：2026-11-02 14:08–14:30（Asia/Shanghai）。
- s10 补拍合并：
un_20261102T060856Z_fae6174b **100/100**；评分 
un_20261102T061026Z_73fb77c5（600 行 0 失败）。
- 技术批按 DEC-0005/0006 重导 
un_20261102T062425Z_b4159b3e：20 次尝试、**19 通过、1 BLUR**（seq 15，Laplacian 36.5）；
  重评 
un_20261102T062452Z_ed533f65：114 行 0 失败。
- 装配：ops/tools/build_exam02_dataset.py --write → manifests/EXAM02/EXAM02_captures_1000.parquet
  **998 行 × 32 列、998 分析帧、0 缺分数**；角色 C_pool 218 / T_pilot 780，重复 99。
- 池化 AUC（源聚类 bootstrap 2000 次）：swinv2 0.8914 [0.875, 0.908]、siglip 0.8413 [0.821, 0.863]、
  sdxl 0.7813 [0.757, 0.806]、convnext 0.5424、vit 0.4777、resnet 0.4185。
- 重复一致性：99 对；中位 |Δ| ≤ 0.015，但 swinv2 9 对、siglip 3 对、sdxl 5 对 |Δ| > 0.3；
  用原始 rectified 图直接重跑确认 swinv2 0.0047 vs 0.9128 属真实不稳定，不是映射错误。
- 修复：score_physical.py 的 split_role 硬编码 TECH → 取队列 role（历史 score parquet 该列不作分析依据）。
- 报告：
eports/RESULT02.md（15 节，含四硬条件判定、D1–D6 偏离、局限、复现命令）。
- 结论：EXAM02 完成；998 帧全部通过冻结 QC；工程硬条件 1/2/4 明确通过，条件 3 按"进入主研究帧 100% 通过"口径通过并明示另一种读法。
- 下一步：EXAM03（D_sel 500 数字评分、候选验收与冻结）。

### C.2 ops/WORKLOG.md 残段（重建前）

﻿
---

## 2026-10-30（续）s6 导入与曝光门限修订（DEC-0005）

### s6 首次导入
- `run_20261030T112402Z_0380d911`：100 文件，**90 通过 / 10 失败**（8 EXPOSURE、2 BLUR）。
- 逐张复看：8 张 EXPOSURE 的内容本身是纯白（如 NOTICE 标牌），属内容亮度而非拍摄眩光；
  2 张 BLUR（seq 579 Laplacian 57.3、584 43.7）为真失焦。

### 标定与修订
- 新增 `ops/tools/content_reference.py`：把矫正图与显示资产统一缩到 1280×720，
  计算 `clip_excess`（照片高光比例 − 资产高光比例）与 `sharp_ratio`。
- 全会话重算后写 `manifests/content_reference/*.json`；交叉表见
  `reports/EXAM02_s6_qc.md`。
- 决策 `ops/decisions/DEC-0005_exposure_gate_v2.md`：曝光改用
  `clip_excess ≤ 0.05`，清晰度保持 Laplacian ≥ 60 不变。
- `scripts/import_captures.py` 实现该门限（`CLIP_MAX`、`CLIP_EXCESS_MAX`），
  并在 qc 行写入 `clip_asset_fraction`、`clip_excess`。

### 重导
- s6：`run_20261030T112845Z_0326018a` → **98 通过 / 2 BLUR**（579、584）。
- s1：`run_20261030T113014Z_082d2ef7` → **100 通过 / 0 失败**（seq 51 的 excess 0.014）。
- 旧运行目录全部保留，报告同时披露 v1/v2 两套口径。

### 待办
- s6 评分（98 帧）、s1 评分重跑（600 行）。
- 用户补拍 s6 的 579、584 后合并重导。

### s6 评分与报告
- 评分 `scores/EXAM02/run_20261030T113319Z_e69e58b6`（98 帧 / 588 行 / 0 失败）：
  swinv2 0.8854、siglip 0.8621、swin_sdxl 0.8250、convnext 0.5508、vit 0.4579、resnet 0.4092。
- s1 重评分 `run_20261030T113412Z_de5c9c99`（100 帧 / 600 行）：
  swinv2 0.8748、siglip 0.8692、swin_sdxl 0.7632、convnext 0.5940、vit 0.4712、resnet 0.4342。
- 修复 `score_physical.py` 的 session 标签（此前恒为 tech）：现在从导入 run 的
  `import_summary.json` 读取。
- 报告 `reports/EXAM02_s6_qc.md`；汇总表重生成（`reports/EXAM02_main_qc.md`、`manifests/EXAM02_qc_summary.csv`）。
- 补拍工具 `captures/kit/run_main_s6_retake.bat`（579、584）。

### s6 收尾（100/100）
- 第二轮 584 补拍（曝光 −0.3 EV）后：`clip_excess` 由 0.064 降到 −0.010，清晰度 348.2。
- 终版导入 `run_20261030T115038Z_383dbb63`：**100 通过 / 0 失败**。
- 终版评分 `run_20261030T115204Z_74682f0b`（600 行 / 0 失败）：
  swinv2 0.8872、siglip 0.8611、swin_sdxl 0.8279、convnext 0.5466、vit 0.4426、resnet 0.4134。
- 报告 `reports/EXAM02_s6_qc.md` 更新为终版；汇总表重生成。

### NCC 回填与导入器补强
- 新增 `ops/tools/backfill_content_ncc.py`：重算矫正图与资产的 NCC 并写回 `qc.json`，
  原文件备份到 `ops/archive/qc_*_before_ncc_backfill.json`；16 个 run 已回填。
- `qc_summary.py` 改为优先读 `qc.json` 的 `content_ncc`（旧 `content_match.json` 兜底）。
- `import_captures.py` 直接计算 `content_ncc`（256×144 灰度 NCC），后续会话无需回填。
- 汇总表重生成：6 段、598 张导入、597 张通过；s1 0.9657、s2 0.9663、s3 0.9662、
  s4 0.9652、s5 0.9605、s6 0.9665。
- 82 项测试通过。

## 2026-10-30 20:25 s7 导入

- 收到 108 个文件：100 张 + 8 个 "- 副本" 重复拷贝（已移到 `captures/incoming/main_s7_duplicates/`，附 README，未删除）。
- 导入 `run_20261030T122524Z_f4c79344`：**98 通过 / 2 EXPOSURE**（seq 605 excess 7.6pp、643 excess 9.9pp）。
- 指标：NCC 中位 0.9673（最低 0.7927 → 643 过曝所致）；内点中位 1037（最低 124）；
  取景 0.639–0.704（中位 0.650）；角点中位 0.63°（最大 4.86°）；清晰度最低 65.8。
- 补拍工具 `captures/kit/run_main_s7_retake.bat`（605、643，−0.3 EV）。

### s7 收尾（100/100）
- 补拍 605（excess 0.076→0.028）、643（0.099→0.017）后，导入 `run_20261030T130221Z_daa0fe63`：**100/100**。
- 终版评分 `run_20261030T130357Z_04a112aa`（600 行 / 0 失败）：
  swinv2 0.9208、siglip 0.8375、swin_sdxl 0.7563、vit 0.5470、convnext 0.5270、resnet 0.4922。
- 643 的 NCC 0.754 为强摩尔纹（清晰度 1738 全批最高），内点 977、目视一致，非错位。
- 报告 `reports/EXAM02_s7_qc.md`；汇总表已含 s7。

### s8（一次通过）
- 导入 `run_20261030T130747Z_58dd6ff2`：**100/100**，无补拍。
- 指标：NCC 中位 0.9676（最低 0.8482 → seq 707 低纹理）、内点中位 1047（最低 253）、
  取景 0.635–0.675、角点中位 0.81°、清晰度最低 74.9。
- 评分 `run_20261030T130911Z_bfef8a42`（600 行 / 0 失败）：
  swinv2 0.8892、siglip 0.8683、swin_sdxl 0.8211、convnext 0.5314、vit 0.4718、resnet 0.4158。
- 报告 `reports/EXAM02_s8_qc.md`。

### s9（99 通过，1 待补拍）
- 导入 `run_20261030T131658Z_e9bd245b`：100/100 导入，**99 通过 / 1 EXPOSURE（seq 858）**。
- 指标：NCC 中位 0.9655（最低 0.8099）、内点中位 1067（最低 375）、取景 0.637–0.666、
  角点中位 0.73°、清晰度最低 107.5。
- seq 858：白纸内容 + 整体偏亮（亮度 169），`clip_excess` 6.4% > 5%；清晰度 782、NCC 0.974、内点 1183 → 只需补拍 1 张（曝光下调一格）。
- 进度文件缺 seq 900 条目：按 `IMG_20261030_204134.jpg` 与资产匹配 658 内点判定为第 100 张，补记并备份原文件。
- 报告 `reports/EXAM02_s9_qc.md`；补拍 `captures/kit/run_main_s9_retake.bat`。

### s9 收尾（100/100）
- 补拍 858（`IMG_20261030_212137.jpg`）后重导 `run_20261030T132356Z_ed6969fb`：**100/100**；858 高光 3.8%、超出 −8.5%、清晰度 563。
- 评分 `run_20261030T132528Z_eec2b936`：600 行 0 失败；AUC swinv2 0.9020、siglip 0.8231、sdxl 0.8063、convnext 0.6575、resnet 0.5554、vit 0.4050。
- 报告 `reports/EXAM02_s9_qc.md` 更新为终版；QC 汇总已重生成。
- **主批累计：s1–s9 共 900 张，900 张通过；技术批 20 张（18 通过）。**
- 下一段：s10（seq 901–1000，最后 100 张）。

### s10（98 通过，2 待补拍）
- 导入 `run_20261030T132908Z_230a35e5`：100 文件 / **98 通过 / 2 EXPOSURE**（963 雪景 +10.9%、996 白衣 +6.8%）。
- 其余指标：NCC 中位 0.9668（最低 0.7525，seq 931 低纹理）、内点中位 1089、取景 0.621–0.656、清晰度最低 65.0、亮度 46.4–164.8。
- 进度缺 seq 1000：按 `IMG_20261030_204601.jpg` 与资产 912 内点判定为第 100 张，补记并备份。
- 报告 `reports/EXAM02_s10_qc.md`；补拍 `captures/kit/run_main_s10_retake.bat`（963,996）。

## 2026-11-02｜EXAM02 收尾、EXAM03、EXAM04

### EXAM02 → RESULT02（998 帧）
- s10 补拍 963/996 后 100/100；全批 s1–s10 共 1000 张、998 有效 + 2 张隐私排除（DEC 记录）。
- 装配 `manifests/EXAM02/EXAM02_captures_1000.parquet`（998×32，998 in_analysis，0 缺分数）。
- 池化 AUC：swinv2 0.8914 [0.8753,0.9084]、siglip 0.8413、sdxl 0.7813、convnext 0.5424、vit 0.4777、resnet 0.4185。
- 重复 99 对：中位 |Δ|≤0.015，重尾存在（swinv2 9 对 >0.3）。报告 `reports/RESULT02.md`。

### EXAM03 → RESULT03（数字基线）
- 候选审计 6/6（DEC-0007：批间差用固定批 1 处理，resnet/vit 保留）；数字族 v2 冻结（q75/0.5/σ0.8/颜色）。
- 数字矩阵 C_pool：S_dig swinv2 0.9032、siglip 0.8782、sdxl 0.8420、convnext 0.5742、vit 0.4801、resnet 0.3434。
- 选择冻结：S_dig/S_worst/S_clean 均选 swinv2_deploy；S_rand 选 swin_sdxl；两次重算逐字段一致。
- 验收 4 条全过 + 夹具 4/4；报告 `reports/RESULT03.md`。

### EXAM04 → RESULT04（同源配对，核心结果）
- T_pilot 数字族在 EXAM03 冻结后补算（21,000 行 0 失败，DEC-0009）；配对 899 源 / 17,994 对 / 缺失 0。
- **主结果**（700 源、四族等权、源级配对 bootstrap 2000，种子 20261026）：
  - swinv2：0.9236 → 0.8938，Δ **−0.0297** [−0.0468,−0.0132]
  - siglip：0.9025 → 0.8507，Δ **−0.0518** [−0.0664,−0.0375]
  - sdxl：0.7796 → 0.7726，Δ −0.0070（含 0）
  - convnext：0.6123 → 0.5577，Δ **−0.0546**
  - resnet：0.3453 → 0.4112，Δ **+0.0659** [+0.0481,+0.0844]
  - vit：0.4577 → 0.4747，Δ +0.0169（含 0）
- 会话（批次）效应：同模型跨 10 段 AUC 极差 9.6–20.9 点，大于同源落差。
- 重复重尾：swinv2 9/99 对 |Δ|>0.3，最大 0.919。
- 报告 `reports/RESULT04.md`；台账 `manifests/EXAM04/run_20261102T072215Z_e00f6ab5/`。

## 40. EXAM05 先导主问题：数字选型是否造成实质损失

- 时间：2026-11-02 17:45–17:56（Asia/Shanghai）。
- 用户指令（m05164）："你先按最严谨的方法跑一下EXAM05吧，记得结论留痕"。
- 预注册：`predictions/PREDICTION05.yaml` 于 2026-11-02T09:50Z 写定（在任何重放计算之前），
  固定主预算 b=40、辅助 20/80、δ=0.01、200 次重放、2000 次联合 bootstrap、种子 20261026，
  并写明三种允许的结论语句与否证条件。
- 代码：`ops/tools/exam05_replay.py`（新增，约 300 行；含 AUC tie 校正、外层重放、联合推断）。
  两次实现修正：`parents[1]→parents[2]` 的工程根定位；`RunLog→RunLogger.start` 接口对齐；
  C_pool 源与物理表取交集（1 源因隐私替换被排除）。
- 运行：`run_20261102T094759Z_04fc8209`（exit 0）。
- 设计与权限：校准池 C_pool **199 源**，评价池 T_pilot **700 源**，D_sel 不参与；
  数字分数取 EXAM03/EXAM04 的 clean+F1–F4；物理分数取 EXAM02 装配表源级均值。
  方向按 DEC-0011：主口径方向校正（resnet/vit 翻转），敏感性用声明方向。

### 结果

| 预算 | regret 均值 | 95% 重放 CI | P(regret>0) | 数字选中 swinv2 |
| --- | ---: | --- | ---: | ---: |
| b=20 | +0.0042 | [−0.1215, +0.1215] | 0.155 | 107/200 |
| **b=40** | **+0.0031** | **[−0.1215, +0.1215]** | **0.175** | **120/200** |
| b=80 | −0.0009 | [−0.0781, +0.0445] | 0.065 | 161/200 |

- 联合推断（重抽 C_b 与 T_pilot，2000 次）：均值 **−0.0033**，95% CI **[−0.1224, +0.1193]**，
  P(regret>0)=0.114。
- 全池（b=199）时数字规则与真实直接规则**同时选中 swinv2_deploy**。
- 失败模式：b=40 时 40% 的重放在 swinv2/siglip/sdxl 之间摇摆；选错时平均 regret +0.0305；
  灾难性错选（convnext/resnet/vit）在 b≥40 为 0 次。
- 敏感性（声明方向、不校正）：结论不变（均值 +0.0031，CI 同宽）。

### 判定

`verdict = INDISTINGUISHABLE_OR_NO_EVIDENCE`。按 PREDICTION05 的事前规则：
没有证据表明数字选型造成超过 δ=0.01 的物理 AUC 损失，但 CI 宽达 ±0.12，**不能排除**该量级的损失；
b=80 时 CI 为 [−0.078, +0.045]，仍宽于 ±0.05 → 触发否证条件，记为 **L05-1 欠功效**。

### 局限

- L05-1：C_pool 仅 199 源，b≤80 时选择噪声与模型间真实差（0.045）同量级。
- L05-2：6 个候选中 3 个物理 AUC≈0.55，实际竞争只在 3 个之间。
- L05-3：C_pool 与 T_pilot 同设备、同会话族，未覆盖外部成分。
- L05-4：非盲（DEC-0010）。

### 对论文的含义

- 原设想的动机"按数字选型会选错模型、造成实质损失"**不成立**，不能作为方法论文开场。
- 可替换的准确动机：数字排名在冠军层稳定，代价发生在亚军层；且 b=40 的估计噪声（±0.12）
  远大于模型间真实差，说明"用 40 张校准选最优模型"本身不可靠。
- 这直接支持后续 E3/E4（TTA/校准能否降低低预算选择方差），并写入 `reports/FINDINGS.md` F07。

### 产物

`reports/RESULT05.md`、`manifests/EXAM05/run_20261102T094759Z_04fc8209/{summary.json,
per_replay_primary_direction_corrected.csv, per_replay_sensitivity_declared.csv, selection_freq.csv}`、
`ops/logs/run_20261102T094759Z_04fc8209.jsonl`、`ops/logs/EVENTS.jsonl` 第 94 条。


## 41. 日志完整性事件：WORKLOG 被截断与重建

- 发现时间：2026-11-02 17:47（EXAM05 收尾、准备追加日志时）。
- 现象：根 `WORKLOG.md` 仅剩 3 个分节（19、20、39），`ops/WORKLOG.md`（18 个标题）为另一份部分副本；
  两份都不是完整历史。原因推断：某次以写模式覆盖（而非追加）导致根文件被截断。
- 影响：**正文日志丢失了约 §1–§18、§21–§38 的叙述**；但原始事实未丢失——
  ①`ops/logs/EVENTS.jsonl` 有 94 条事件（append-only，含 run_id/stage/title/detail）；
  ②`ops/memory/JOURNAL.jsonl` 有 73 条哈希链记忆；③每个 run 的 `ops/logs/run_*.jsonl`；
  ④`reports/RESULT01–05`、`manifests/**`、`scores/**` 全部保留。
- 处置（不删除任何原件）：
  1. 两份残存文件复制到 `ops/archive/WORKLOG_fragment_*.md`；
  2. 本文件重建：以 EVENTS 为时间线主干，附残存分节原文与本轮 EXAM05 章节；
  3. 今后 WORKLOG 只允许**追加**（append），并在 runner 中改为 `open(..., "a")`。
- 教训：日志"写了"不等于"留住了"；append-only 必须由代码保证，不能靠自觉。


### §42 2026-11-02｜EXAM05 预注册时间戳口径更正

- 发现：PREDICTION05.yaml 头部手写 rozen_at 09:50Z，文件 mtime 实为 **09:46:58Z**；run id 内嵌首次计算 **09:47:59Z**。
- 处置：新增 predictions/PREDICTION05_amend_0001.yaml（不改预注册正文）；
eports/RESULT05.md §1 引用改为 mtime 并注明 amend；EVENTS 追加一条。
- 结论影响：无（内容一字未动；预注册仍早于计算 61 秒）。
- 附带：本文件重建自 EVENTS（§41 事故），此后只允许 append。
