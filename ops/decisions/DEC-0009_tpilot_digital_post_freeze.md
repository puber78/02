# DEC-0009｜T_pilot 数字族在 EXAM03 冻结之后补算

- 日期：2026-11-02
- 状态：已执行（记录性决策）
- 关联：DEC-0007（检测器验收与固定批）、EXAM03 选择、EXAM04 配对

## 背景

EXAM03 只对 C_pool（200）与 D_sel（500）生成并评分数字族（clean/display/F1–F4），
T_pilot（700）**没有任何数字分数**。原因是 EXAM03 的规则选择不得读取 T_pilot，
当时把"不读"实现成了"不算"。

EXAM04 需要**同源配对**：同一个源的数字分与实拍分。若没有 T_pilot 的数字分，
配对只能在 C_pool（选择池）上做，而这正是选择所用池，不能作为确证估计。

## 决策

在 **EXAM03 选择与选择规则已冻结、`selections/EXAM03/digital_choices.jsonl` 已落盘之后**，
为 T_pilot 的 700 个源生成同一套数字族（clean + F1–F4）并评分：

- 生成：`scripts/make_digital_variants.py --roles T_pilot --out-root data/digital_t`
  （参数与 EXAM03 完全一致，见 `protocols/digital_families.yaml` v2_frozen），
  manifest `manifests/EXAM03/run_20261102T071151Z_397108f4/digital_variants.parquet`。
- 评分：`scripts/score_digital.py --variants ... --families clean F1_jpeg F2_scale F3_blur F4_color --out-exam EXAM04`
  → `scores/EXAM04/run_20261102T071316Z_13a6975a/`（21,000 行，0 失败）。

## 为什么这不破坏选择

1. 选择规则、族参数、平局规则在 T_pilot 数字产生之前已冻结（文件 mtime + 本决策）。
2. 选择程序（`build_exam03.py`）从不读取 T_pilot；本次补算的输出目录为 `scores/EXAM04/`，
   与 EXAM03 的 run 分离，选择日志 append-only 未回写。
3. 本决策只增加**评估侧**材料；任何"改选"都没有发生。

## 偏离与披露

- 论文中须写明：T_pilot 数字分数在冻结后产生，属"评估侧补算"，不是注册时的原计划。
- 该补算不改变 EXAM03 的任何结论，也不改变 RESULT03 的数字矩阵。

## 影响

EXAM04 因此可以做 899 源 × 全族同源配对（缺失 0），主结果脱离选择池。
