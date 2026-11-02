# DEC-0008｜数字样本父键契约扩展（clean/生成族父为 source）

- 日期：2026-11-02
- 阶段：EXAM03
- 状态：生效
- 关联：`src/proxy_selection/contracts/ids.py`、`scripts/score_digital.py`、`reports/INTERFACE_CONTRACT.md`

## 1. 问题

`mint_sample_id(branch="digital", ...)` 原契约规定父键必须是 `dsp_*`（display asset）。
EXAM03 的数字族有三类父对象：

| 族 | 父对象 | 前缀 |
| --- | --- | --- |
| `display` | 上屏资产（2560×1440） | `dsp_` |
| `clean` | 下载得到的原始源图 | `src_` |
| `F1–F4` | 原始源图（在 clean 上施加变换） | `src_` |

若把 clean/F1–F4 的父键强行写成某个 `dsp_`，等于伪造父链：数字变体并非从上屏图派生，
其像素与上屏图在分辨率、重采样、颜色管理上都不同。首次运行因此抛
`IdError: expected display_asset id (dsp_*), got 'src_...'`。

## 2. 决定

- `mint_sample_id` 增加可选 `parent_kind`：
  - `physical` → 只允许 `capture`（不变）；
  - `digital` → 允许 `display_asset`（默认，保持旧哈希）或显式 `source`。
- 摘要仍为 `UUIDv5(branch, transform_id, parent)`，不加入 `parent_kind`：
  三类前缀互斥，父键字符串本身已唯一确定族，加入反而破坏既有 id 的稳定性。
- `score_digital.py`：`display` 族传 `parent_kind="display_asset"`，其余传 `"source"`。
- `reports/INTERFACE_CONTRACT.md` 的 sample 行同步注明（原地修订，属维护文档）。

## 3. 为什么不另造假 display asset

为 clean 图伪造 `dsp_` 会污染"上屏资产"这一物理含义，并让 EXAM02 的
`display_asset_id → capture` 关联出现无法解释的孤儿。宁可扩展契约，也不制造假父链。

## 4. 影响与验证

- 既有 physical 样本 id 与 display 族数字样本 id 均不变（默认路径哈希不变）。
- `pytest` 82 项通过（新增/既有 id 测试全部通过）。
- 数字评分重新运行后，`digital_scores.parquet` 的 `sample_id` 能按父键回溯到
  `source_id`（clean/生成族）或 `display_asset_id`（display 族）。

## 5. 复现

```powershell
.venv\Scripts\python.exe scripts\score_digital.py --families clean display F1_jpeg F2_scale F3_blur F4_color
.venv\Scripts\python.exe scripts\build_exam03.py
```
