# EXAM03 检测器验收审计

- run: `run_20261102T070900Z_f764e46c`
- 夹具: TECH 数字图，每类 4 张（共 8）
- 批独立容差: 1e-05；确定性容差: 1e-06
- 接受: 6/6

| 模型 | 架构 | 参数量 | 预处理 | ai_index | 批 Δ | 固定批 | 批1 Δ | 确定性 Δ | 损坏图失败码 | 夹具方向 | 接受 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| swin_sdxl | ['SwinForImageClassification'] | 86,745,274 | ViTImageProcessor 224 | 0 | 1.79e-07 | 16 | 0.00e+00 | 0.00e+00 | MODEL_ERROR | ok | ✅ |
| siglip_ai_human | ['SiglipForImageClassification'] | 92,885,762 | SiglipImageProcessor 224 | 0 | 3.79e-06 | 16 | 0.00e+00 | 0.00e+00 | MODEL_ERROR | ok | ✅ |
| convnext_ai | ['ConvNextForImageClassification'] | 27,821,666 | ConvNextImageProcessor 224 | 0 | 8.94e-06 | 16 | 0.00e+00 | 0.00e+00 | MODEL_ERROR | ok | ✅ |
| resnet_ai | ['ResNetForImageClassification'] | 23,512,130 | ConvNextImageProcessor 224 | 0 | 1.81e-03 | 1 | 0.00e+00 | 0.00e+00 | MODEL_ERROR | ok | ✅ |
| swinv2_deploy | ['Swinv2ForImageClassification'] | 195,206,006 | ViTImageProcessor 256 | 0 | 1.00e-09 | 16 | 0.00e+00 | 0.00e+00 | MODEL_ERROR | ok | ✅ |
| vit_ai_real | ['ViTForImageClassification'] | 85,800,194 | ViTImageProcessor 224 | 1 | 2.56e-04 | 1 | 0.00e+00 | 0.00e+00 | MODEL_ERROR | REVERSED | ✅ |


## 判定口径

- 接受条件（DEC-0007）：检查点哈希可得 + 官方预处理可读 + **推理可复现** + 损坏图显式失败 + `ai_index >= 0`。
  - 可复现 = 原批大小确定性 Δ ≤ 容差，**或** 批大小钉死为 1 后两次推理完全一致（`固定批` 列）。
  - 批间 Δ 超容差是 fp32 累加顺序问题，不据此淘汰技术有效候选；数字/物理两侧都按 `forced_batch_size` 推理。
- 方向来自模型自身 `config.id2label` 与 registry 的 `ai_label` 覆盖（结构性），夹具均值只作诊断：
  弱模型在 4 张/类夹具上均值反转属性能信号，不用于翻转分数、也不用于淘汰。
- 数字 AUC 高低**不**参与接受判定（大纲禁止按表现排除技术有效候选）。
