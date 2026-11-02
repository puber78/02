# RESULT03｜数字代理与冻结检测器基线（EXAM03）

- 运行日期：2026-11-02
- 依赖：EXAM01（接口契约）、EXAM02（来源与角色）
- 交付路径：`reports/RESULT03.md`、`scores/EXAM03/digital.parquet`（= `run_20261102T065427Z_1e0c09aa` 的逐字节副本）、`selections/EXAM03/digital_choices.jsonl`、`manifests/EXAM03/run_20261102T070827Z_e68732a4/exam03_summary.json`
- 结论范围：**只报告数字侧矩阵、规则与冻结选择**；不写真实优劣、不写"代理失效"。

---

## 1. 目标问题

数字评测会选择谁？这个选择程序是否明确且可复算？本阶段冻结数字测试族与选择规则，
在 C_pool 上做选择、在 D_sel 上做数字留出检查，**不读取任何 T_pilot 分数**。

## 2. 候选与工程验收（6/6）

`ops/tools/detector_audit.py`，run `run_20261102T070900Z_f764e46c`，报告
`reports/EXAM03_detector_audit.md`。

| 模型 | 架构 | 参数量 | 预处理 | ai_index | 批 Δ | 固定批 | 批1 Δ | 确定性 Δ | 失败码 |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| swin_sdxl | Swin | 86,745,274 | ViTImageProcessor 224 | 0 | 1.79e-07 | 16 | 0 | 0 | MODEL_ERROR |
| siglip_ai_human | SigLIP | 92,885,762 | SiglipImageProcessor 224 | 0 | 3.79e-06 | 16 | 0 | 0 | MODEL_ERROR |
| convnext_ai | ConvNeXt | 27,821,666 | ConvNextImageProcessor 224 | 0 | 8.94e-06 | 16 | 0 | 0 | MODEL_ERROR |
| resnet_ai | ResNet | 23,512,130 | ConvNextImageProcessor 224 | 0 | **1.81e-03** | **1** | 0 | 0 | MODEL_ERROR |
| swinv2_deploy | SwinV2 | 195,206,006 | ViTImageProcessor 256 | 0 | 1.00e-09 | 16 | 0 | 0 | MODEL_ERROR |
| vit_ai_real | ViT | 85,800,194 | ViTImageProcessor 224 | 1 | **2.56e-04** | **1** | 0 | 0 | MODEL_ERROR |

- 6 个候选全部有真实前向证据；官方预处理哈希 6/6；损坏图均显式 `MODEL_ERROR`。
- resnet / vit 的批间差来自 fp32 累加顺序：**固定批=1 后两次推理完全一致**，按
  DEC-0007 保留而不淘汰；数字与物理两侧都用 `forced_batch_size`。
- vit 的夹具方向均值反了（4 张/类）：方向由 `config.id2label` + registry 覆盖结构性命定
  （`ai_index=1`），夹具均值只作诊断，**不翻转分数、不据此淘汰**。
- 数字 AUC 高低不参与接受判定（大纲要求）。

## 3. 数字测试族（4 族，参数冻结）

`protocols/digital_families.yaml` v2（2026-11-02T06:39Z 冻结，`FROZEN_FOR_EXAM03`）：

| 族 | 类型 | 参数 |
| --- | --- | --- |
| F1_jpeg | 编码 | JPEG q=75，4:2:0 |
| F2_scale | 尺度/重采样 | 下采样 0.5（BILINEAR）再上采样回原尺寸（BILINEAR） |
| F3_blur | 模糊 | 高斯，σ=0.8 |
| F4_color | 颜色 | 饱和度 ×1.2、亮度 ×0.95、对比度 ×1.05（依次施加） |

基线：`clean`（原始下载文件）与 `display`（实际 2560×1440 上屏资产；D_sel 从未上屏，
其 display 基线等于 clean，已文档化且不重复计入族汇总）。

变体生成 run `run_20261102T064400Z_a8274b7f`：`data/digital/{F1_jpeg,F2_scale,F3_blur,F4_color}/`
共 4200 行（1400 源 × 3 族 + 1400 clean + 1400 display）。初版误用参数（jpeg55/σ1.0/gamma0.9）
生成的目录**保留未删**，在 manifest 中标为 superseded，不进入任何结果（DEC-0007 §2.3）。

## 4. 数字表现矩阵

评分 run `run_20261102T065427Z_1e0c09aa`（22,200 行）；provider 断言：每条
(sample × model × family) 都有分数或显式失败，**0 未解决失败**。

### 4.1 C_pool（选择池，n=200/族）

| 模型 | F1 | F2 | F3 | F4 | 等权 S_dig | 最差族 | clean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **swinv2_deploy** | 0.8747 | 0.8714 | 0.9278 | 0.9388 | **0.9032** | **0.8714** | **0.9435** |
| siglip_ai_human | 0.9007 | 0.8492 | 0.8785 | 0.8846 | 0.8782 | 0.8492 | 0.8874 |
| swin_sdxl | 0.8104 | 0.8302 | 0.8551 | 0.8722 | 0.8420 | 0.8104 | 0.8687 |
| convnext_ai | 0.5451 | 0.6479 | 0.5843 | 0.5195 | 0.5742 | 0.5195 | 0.5153 |
| vit_ai_real | 0.4789 | 0.4936 | 0.4830 | 0.4650 | 0.4801 | 0.4650 | 0.4755 |
| resnet_ai | 0.3680 | 0.2955 | 0.3357 | 0.3745 | 0.3434 | 0.2955 | 0.3727 |

### 4.2 D_sel（数字留出，从未上屏，n=500/族）

| 模型 | F1 | F2 | F3 | F4 | 等权 S_dig |
| --- | ---: | ---: | ---: | ---: | ---: |
| swinv2_deploy | 0.9090 | 0.8929 | 0.9446 | 0.9573 | **0.9260** |
| siglip_ai_human | 0.9129 | 0.8694 | 0.8890 | 0.8940 | 0.8913 |
| swin_sdxl | 0.7756 | 0.8047 | 0.8295 | 0.8582 | 0.8170 |
| convnext_ai | 0.6551 | 0.7274 | 0.6734 | 0.6164 | 0.6681 |
| vit_ai_real | 0.4385 | 0.4483 | 0.4402 | 0.4230 | 0.4375 |
| resnet_ai | 0.3635 | 0.3138 | 0.3462 | 0.3816 | 0.3513 |

### 4.3 读法

- 数字族之间**会给出不同排序**：C_pool 上 F1（JPEG）把 siglip（0.9007）排在 swinv2
  （0.8747）之上，而 F2/F3/F4 把 swinv2 排第一。族内极差：convnext 0.128、swinv2 0.067、
  sdxl 0.062、siglip 0.052、vit 0.029、resnet 0.079。
- `clean` 单族会把 swinv2 高估（0.9435 vs 等权 0.9032）：**只看原图会高估 JPEG 抗性最好者**，
  这正是"数字加权≠单族"的实证（夹具 F-3）。
- 三个弱/反向候选在四族上一致低于 0.5，`S_dig` 与单族都不改变其位置。

## 5. 规则与冻结选择

`protocols/selectors.yaml` v2（2026-11-02T06:45Z 冻结）。平局规则：分数降序后按
`model_key` 字典序（与物理性能无关，在看 T 之前固定）。

| 规则 | 定义 | 选中 |
| --- | --- | --- |
| **S_dig（主）** | C_pool 上 F1–F4 AUC 等权平均 | **swinv2_deploy** |
| S_worst | 最大化最差族 AUC | swinv2_deploy |
| S_clean | 仅 clean 的 AUC | swinv2_deploy |
| S_rand | 均匀随机（种子 20261026，负对照） | swin_sdxl |

- 主规则与两个预定辅助规则一致；负对照不同——说明该选择不是"任何规则都能选中"。
- 选择记录（append-only）：`selections/EXAM03/digital_choices.jsonl`，两次独立重算
  （`build_exam03.py` 重跑）给出**逐字段相同**的选择（determinism 证据，见 §7 cond3）。
- 选择理由：等权族平均在 F1 的单族偏差上做了折中，且 worst-case 与 clean 两个辅助口径
  给出同一答案，故该选择对族选择不敏感（在 4 个候选内部）。

## 6. D_sel 数字留出

主规则选中的 swinv2 在 D_sel 上仍第一（0.9260），siglip 第二（0.8913）。
**这不能作为"选择正确"的证据**：D_sel 与 C_pool 同属数字材料，只说明该选择在数字分布上
不是过拟合 C_pool 的产物；真实优劣必须等 EXAM04/05 的实拍留出。

## 7. 验收硬条件与夹具

`ops/tools/exam03_acceptance.py` → `manifests/EXAM03/run_20261102T071041Z_*/exam03_acceptance.json`。

| 条件 | 结果 |
| --- | --- |
| 1. ≥4 候选真实运行、3–4 族执行、预处理核查 100% | ✅ 6 候选 / 6 族 / 1.0 |
| 2. 每个 sample×model×variant 有分数或显式失败，完整性 100% | ✅ 22,200/22,200，未解决失败 0 |
| 3. 变换像素可复现、选择与平局一致率 100% | ✅ 4 族各抽 10 源重算，PNG 字节与 manifest sha256 全等；规则两次重算同选 |
| 4. T_pilot 访问 0；冻结字段完整 | ✅ T_pilot 计分行 0；families/models/choices 齐全 |

夹具（大纲工作项 6）：

| 夹具 | 结果 |
| --- | --- |
| F-1 同模型同输入两次 → 选择差恒为 0 | ✅ |
| F-2 单调映射保持 AUC（<1e-12） | ✅ |
| F-3 族等权平均 ≠ 拼接 pooled AUC | ✅ 0.9928 vs 0.9820（示例） |
| F-4 缺失不补分（dropna 后计数正确） | ✅ |

## 8. 偏离与限制（全部留痕）

| 编号 | 事项 | 处理 |
| --- | --- | --- |
| D-R03-1 | **PREDICTION03 未在评分前落盘**，本文件为事后补记 | 在 `predictions/PREDICTION03.yaml` 顶部显式标注 `RETROSPECTIVE_RECORD` 与披露段；规则/族参数确在评分前冻结（文件 mtime + DEC-0007） |
| D-R03-2 | `display` 族样本一度以 `src_` 为父键 | DEC-0008 扩展契约；仅 display 族重跑（`run_20261102T070602Z_0445ee9b`）并按字节归档旧 parquet 后合并，display AUC 不变（同分数、仅父键修正） |
| D-R03-3 | 初版族参数（jpeg55/σ1.0/gamma0.9）曾用于生成 | 目录保留、标 superseded、不进入结果；v2 参数与生成器 `PARAMS` 逐字一致 |
| D-R03-4 | resnet/vit 批间差超容差 | 固定批=1、验证批1确定性（DEC-0007）；物理侧历史分数仍为 batch16，量级 1e-3，写入限制 |
| L1 | D_sel 只在数字侧留出，不能替代实拍 | 真实优劣留给 EXAM04/05 |
| L2 | 6 个候选均来自公开 HF 检查点，生态代表性有限 | EXAM04 讨论 |
| L3 | F1–F4 强度为单点取值，未做强度扫描 | 本阶段按大纲"具体强度由技术范围确定"固定；扫描属 EXAM06 解释边界 |

## 9. 复现

```powershell
.venv\Scripts\python.exe ops\tools\detector_audit.py
.venv\Scripts\python.exe scripts\make_digital_variants.py
.venv\Scripts\python.exe scripts\score_digital.py --families clean display F1_jpeg F2_scale F3_blur F4_color
.venv\Scripts\python.exe scripts\build_exam03.py
.venv\Scripts\python.exe ops\tools\exam03_acceptance.py
```

## 10. 论文用途

- 表：候选审计（§2）、数字族矩阵（§4.1/4.2）、规则与选择（§5）。
- 图：族×模型 AUC 热图；族内排序翻转（F1 vs F3）示例。
- 文字定位：**数字基线**——"数字材料上谁更强、规则选谁"；不得写"代理失效"或真实优劣。
  真实落差的估计在 EXAM05，需与 EXAM02 的实拍 AUC 做同源配对。
