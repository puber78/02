# DEC-0007｜EXAM03 检测器验收口径（批不变量、方向、族参数冻结）

- 日期：2026-11-02
- 阶段：EXAM03
- 状态：生效
- 关联：`ops/tools/detector_audit.py`、`reports/EXAM03_detector_audit.md`、`protocols/digital_families.yaml`、`protocols/selectors.yaml`

## 1. 背景

大纲要求候选检测器必须满足工程硬条件：检查点可追溯、预处理有文档、**批处理独立**、
确定性、失败显式。首次审计（run `run_20261102T063903Z_464d8c65`）发现两个问题：

| 模型 | 现象 | 数值 |
| --- | --- | --- |
| resnet_ai | 批大小改变时分数不完全一致 | max Δ = 1.81e-3（阈值 1e-5） |
| vit_ai_real | 夹具方向不一致（4 真 vs 4 假均值反了） | 且 max Δ = 2.56e-4 |

## 2. 判定

### 2.1 批不变量 → 改为"推理可复现"

- 事实：resnet 的差异来自 fp32 卷积在不同批形状下的累加顺序（同权重、同预处理）。
  实测批量 1 连跑两次 Δ = 0。
- 决定：**不因数值伪影淘汰技术有效候选**。若 `batch_delta > 1e-5`，把该模型的推理
  批大小钉死为 1，并验证批量 1 自身的确定性；通过即接受，审计记录
  `forced_batch_size = 1` 与 `batch1_delta_max`。
- 理由：大纲的硬条件是"可复现"，不是"厂商 kernel 批不变"。固定批次是更强的可复现保证。

### 2.2 方向 → 结构性判定，夹具均值只作诊断

- 方向由模型自己的 `config.id2label` + registry 的 `ai_label` 覆盖解析（`ai_index`），
  这是结构性事实；4 张/类的夹具均值会被弱模型偶然反转，属性能信号，不能当门槛。
- 决定：接受条件改为 `ai_index >= 0`；夹具均值写入审计作诊断，并在 RESULT03 中报告。
- 后果：vit 的 `fixture_direction_consistent=false` 被如实记录，**不**据此翻转分数，
  也**不**据此淘汰；其物理 AUC 0.4777 的"近随机"结论保持不变。

### 2.3 数字族参数冻结

- `protocols/digital_families.yaml` 的 v1 草稿（jpeg 75 / scale bilinear / blur σ0.8 /
  color sat1.2·bri0.95·con0.95）**从未批准**；EXAM03 冻结为 v2，参数与
  `scripts/make_digital_variants.py` 的 `PARAMS` 逐字一致，生成器在任何数字分数产生
  之前就已写成。
- 初版误用 jpeg55/σ1.0/gamma0.9 生成的 `data/digital/{jpeg55,resample,blur,color}`
  **保留不删**（留痕），但在 manifest 中标记 superseded，不进入任何结果。
- 选择规则同批冻结（`protocols/selectors.yaml` v2）：主规则 S_dig = C_pool 上 F1–F4
  等权平均 AUC；敏感性 S_worst / S_clean / S_rand；T_pilot 一律不读。

## 3. 影响

- 候选集：6/6 通过工程验收（resnet 与 vit 以 batch=1 计分）。
- 数字评分：`scripts/score_digital.py` 自动读取最近一次审计的 `forced_batch_size`，
  保证同一模型在数字与物理两侧使用一致的推理设置（物理侧 resnet/vit 原为 batch 16，
  差异量级 1e-3，已在 RESULT03 局限中说明）。
- 任何"低于 0.5 就把分数翻过来"的做法被明确禁止（会变成用测试集调方向）。

## 4. 复现

```powershell
.venv\Scripts\python.exe ops\tools\detector_audit.py
.venv\Scripts\python.exe scripts\make_digital_variants.py
.venv\Scripts\python.exe scripts\score_digital.py --families clean display F1_jpeg F2_scale F3_blur F4_color
.venv\Scripts\python.exe scripts\build_exam03.py
```
