# 主批采集 QC：s1（100 张，最终）

- 导入 run：`run_20261030T113014Z_082d2ef7`（DEC-0005 重导，100 文件 / 100 导入 / **100 通过 / 0 失败**）
- 首版 run：`run_20261030T083055Z_0033e829`（99 通过 / 1 EXPOSURE，保留备查）
- 队列：`captures/kit/queue_main_s1.json`；进度：`queue_main_s1_progress.json`（100/100 shot）
- 状态：**通过**；DEC-0005 后 100 帧全部进入分析，无排除样本。

## 1. 结果

| 指标 | 实测 | 判断 |
|---|---:|---|
| 文件 / 导入 / 缺失 | 100 / 100 / 0 | 通过 |
| QC 通过 | 100 / 100（DEC-0005 口径） | 通过 |
| 映射（seq→照片） | 100/100，内容一致性 NCC 中位 **0.9657**（最低 0.8136，seq 68） | 通过 |
| ORB 内点 | 中位 **920**（99–1305）；good matches 中位 1195 | 通过 |
| 屏幕占画面（可见） | 中位 **0.666**，范围 0.640–0.700；投影四角全部在画面内 | 通过（目标带 0.65–0.70） |
| 角点偏差 | 中位 **0.59°**，最大 2.90° | 优秀 |
| 清晰度（Laplacian） | 最低 **72.0**（seq 16），中位 811（阈值 60） | 通过，seq 16 为边界样本 |
| 平均亮度 | 59.7–161.9（阈值 25–235） | 通过 |
| 高光裁剪 | 最大 4.8%（阈值 5%） | 通过 |
| 失败 | 无。seq 51 原判 `EXPOSURE`（高光 7.2%），内容为白墙；内容参照复核 `clip_excess=0.014` ≤ 0.05 → 改判通过 | DEC-0005 |

补拍的 seq 97–100 与其余 96 张一致性检查：亮度中位 120.7 vs 122.6、NCC 0.972 vs 0.966、
清晰度中位 691 vs 828，无系统性漂移；取景 0.682–0.700，比前 96 张（0.640–0.697）略近，
仍在目标带内。

## 2. 指标语义更正（重要，已修复）

复核发现导入器写的 `screen_coverage` 实际是**显示侧内容矩形 / 画布面积**（4:3 内容放 16:9
画布 = 0.5625），与照片取景无关，之前被误引用为"屏幕占画面比例"。

- 已新增 `ops/tools/screen_geometry.py`，从显示资产与原始照片重新估计单应，输出：
  `screen_area_fraction`（投影四边形/照片，可 >1 表示被裁）、`screen_visible_fraction`
  （四边形∩画面/照片）、`content_rect_frac`（显示侧布局常数）、`corner_dev_deg`。
- s1 重算结果：`screen_area_fraction` 与 `screen_visible_fraction` 完全相等
  （0.640–0.700，中位 0.666）→ 四角完整、无裁切，**0.666 是可引用的取景值**。
- 旧 `qc.json` 已归档到 `ops/archive/qc_run_20261030T083055Z_0033e829_before_geometry_fix_*.json`，
  回填了上述三项指标；`import_captures.py` 已同步修正，s2 起直接记录正确语义。

## 3. 需要记录的两点（不阻塞）

1. **清晰度边界样本 seq 16 = 72.0**（阈值 60）。按规则通过，但在 EXAM02 中做
   "含/不含 seq 16" 的敏感性对照。
2. **段内取景漂移 0.640–0.700（约 9%）**，说明拍摄过程中距离仍有轻微变化（未用支架时正常）。
   不影响可比性（每张都单独配准并矫正），但应写入限制条件；s2 起建议固定手机。

## 4. 失败与排除

- seq 51（原判 `EXPOSURE`，高光 7.2%，内容为白墙）：DEC-0005 改为内容参照口径后
  `clip_excess=0.014`，**改判通过**；首版排除结果仍保留在归档 run 中，供双口径对照。

## 5. 工程修复（留痕）

- 导入器排序改为文件名时间（`_file_time_key`）：Explorer/MTP 复制会重写 mtime 且顺序相反，
  按 mtime 排序曾导致 46 张 `REGISTRATION_FAILED`（seq→照片整体反转）。
- 新增 `--allow-missing`：缺帧记 `MISSING_CAPTURE` 继续，不中断整段。
- 窗口内匹配失败时回退到全局未用文件，按 content match 兜底（≥18 匹配才接受）。
- `ops/tools/geometry_diagnostics.py`、`ops/tools/screen_geometry.py`、`ops/tools/content_match.py`
  均支持 `--run/--queue`，可直接用于 s2–s10。
- s10 进度里 3 条"仅浏览"标记（seq 901–903，08:27Z 记录、无照片）已重置为 pending，
  备份 `ops/archive/queue_main_s10_progress_before_reset_20261030.json`。

## 6. 口径变更（DEC-0005，2026-10-30）

- 曝光门限改为 `clip_excess = clip_high(photo) − clip_high(asset) ≤ 0.05`；
  该段重导 `run_20261030T113014Z_082d2ef7` 结果为 100/100。
- 重评分 `scores/EXAM02/run_20261030T113412Z_de5c9c99`（600 行，0 失败）：
  swinv2 0.8748、siglip 0.8692、swin_sdxl 0.7632、convnext 0.5940、vit 0.4712、resnet 0.4342。
- 旧评分（99 帧）保留在 `scores/EXAM02/run_*`，用于 v1/v2 对照。
