# DEC-0004 - 隐私源整源排除

- 日期：2026-10-30
- 状态：已批准（用户选择 A）
- 决策人：用户；记录人：agent

## 决定

源 `src_f96db601820f5e47bee1264d`（显示资产 `dsp_cd5d09eb6eca56c7bf63a951`）从研究中**整源排除**。

## 范围

- `main_s3:219`（该源的原始采集）
- `main_s3:272`（该源的重复采集，`is_repeat=true`）
- 对全部 10 个 session 队列扫描确认：该源只出现在上述两处。

## 理由

用户指出该图涉隐私并要求移除。**不采用替代照片**：替代图的内容与队列指定的显示资产不一致，配准要么失败、要么"成功但内容不符"，等于伪造该 seq 的采集记录，会破坏可追溯性与可复现性。

## 实现

- 排除清单：`data/EXCLUSIONS.json`（本文件为审计口径）。
- 导入器：`scripts/import_captures.py` 读取排除清单，把命中的 seq 写成 `qc_status=excluded`、`failure_code=EXCLUDED_PRIVACY`，不写 capture 记录、不生成 rectified 图。
- 下游分析按 `qc_status != excluded` 过滤，分母以有效队列为准。

## 影响

- s3 有效队列 **98**（原 100）。
- C_pool：200 -> 199。
- 设计重复对：100 -> 99（该源恰为其一）。
- 论文 Methods 与 Limitations 需披露该排除及分母。

## 相关

- `reports/EXAM02_s3_qc.md`
- `ops/logs/WORKLOG.md`（2026-10-30 17:38、17:42、17:50 各节）
