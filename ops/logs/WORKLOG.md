# WORKLOG — 数字代理选型（DeepSeek Harness 执行）

> 规则：只追加，不删除。每个条目带时间戳（Asia/Shanghai）、命令证据文件、产物哈希登记位置。
> 原始执行包文件永不修改；所有派生结果写在本目录所属的 `proxy-selection-research/` 下。

## 2026-10-26 16:17 — 开工：读取执行包

- 读取：README、DeepSeek_Harness_执行说明、首轮启动指令、主大纲（721 行）、九阶段一览、迁移说明、来源与交付范围、验收参数、EXAM01 工作卡、PREDICTION01、RESULT01 模板、切口 v2 原文。
- 结论：本轮按工作卡与首轮指令只启动 EXAM01 的获准工作；EXAM02—09 依赖人工实拍与负责人批准，按阶段推进。

## 2026-10-26 16:19 — 环境审计（实际测量，非假设）

| 项 | 实测结果 | 证据 |
|---|---|---|
| OS / Python | Windows，Python 3.11.9（另装 3.13，未使用） | `ops/logs/00_venv_create.log` |
| GPU | NVIDIA GeForce RTX 4060 Laptop，8 GB，驱动 616.92 / CUDA UMD 13.4 | `nvidia-smi` 输出（见下） |
| 磁盘 | C: 178.2 GB 可用 / 451.2 GB（D: 177.4 GB 可用） | `[System.IO.DriveInfo]` |
| 系统 TLS | schannel 失败（SEC_E_NO_CREDENTIALS），PowerShell/curl 无法 HTTPS | `pwsh` 诊断 |
| Python TLS | 正常（OpenSSL），PyPI / download.pytorch.org / github / hf-mirror 可达 | 实测 200 |
| huggingface.co | 直连超时；镜像 `hf-mirror.com` 可达（需 User-Agent） | 实测 200 |
| 原始包完整性 | 56 个文件，全部与 `migration/迁移清单.json` 记录一致 | `ops/logs/06_input_verify.log` |

GPU 原始输出（节选）：

```
NVIDIA-SMI 616.92   Driver Version: 616.92   CUDA Version: 13.4
NVIDIA GeForce RTX 4060 Laptop GPU, 8188 MiB, 49C, 6W / 72W
```

## 2026-10-26 16:20 — 建立留痕工作区

新建 `proxy-selection-research/`（与执行包同级，位于包内），包含：

```
ops/{logs,manifests,archive,decisions,tools}   # 日志、哈希清单、归档、决策记录、工具
protocols/  manifests/  predictions/  scores/  selections/  metrics/  results/  reports/
src/proxy_selection/  tests/  paper/  data/{raw,processed}  models/  tmp/
```

- 输入哈希清单：`ops/manifests/inputs_sha256.csv`（56 行，SHA-256）。
- 覆盖保护：所有写入经 `proxy_selection.io.write_new`，已存在即拒绝；替换必须先归档到 `ops/archive/`。
- 每阶段日志：`ops/logs/runs/<run_id>.jsonl`；命令台账：`ops/logs/command_ledger.csv`。

## 2026-10-26 16:21 — 环境安装（含一次失败与修复）

- 首次 `pip install torch` 在 2.5 GB 轮子下载处停滞（13 分钟仅 6 MB），已终止并保留日志 `ops/logs/01_pip_install.log`。
- 修复：改用 `ops/tools/download_wheels.py` 以 HTTP Range 分块下载 + zip 完整性校验，再本地 `pip install`。下载日志 `ops/logs/02_torch_download.log`、`03_torchvision_download.log`。
- 该失败与修复过程本身作为工程留痕保留，不删除。


## 2026-10-26 17:05 — EXAM01 完成（工程 PASS）

- 环境：torch 2.6.0+cu124 / CUDA 12.4 / RTX 4060；transformers 5.20.2；pandas 3.1.0；numpy 2.4.6。证据 `ops/logs/08_env_check.log`、`ops/manifests/pip_freeze.txt`。
- 单元测试：68 passed / 0 failed（首轮 `ops/logs/09_pytest_exam01.log`，复核 `ops/logs/18_pytest_confirm.log`）。
- 技术样本：80 张（40 COCO 真实摄影 + 40 ELSA1M 扩散生成），provenance 覆盖率 100%，内容哈希 100% 一致（`data/raw/TECH/`）。
- 真实链：6 个公开检查点 × 80 图 = 480 行评分，失败 0；产出 `scores/EXAM01/run_20261026T090345Z_acb8682b/`。
- 重复推理：固定批次下 6/6 模型最大差 = 0.0（容差 1e-6+1e-5|s2|）。
- 结果：`results/RESULT01.json`、`reports/RESULT01.md`、`reports/INTERFACE_CONTRACT.md`；五条硬条件全部 PASS。
- 技术样本 AUC（仅审计）：swinv2 0.921 / siglip 0.849 / swin_sdxl 0.827 / vit 0.524 / convnext 0.508 / resnet 0.312（方向可疑，已标记）。
- 决策记录：`ops/decisions/DEC-0001_exam01.md`。

### 当前阻塞（EXAM02）

EXAM02 要求 20 次技术捕获（含 ≥4 次重复）与 240 组先导实拍，必须由人工用相机/手机拍摄屏幕显示文件。
本环境无相机、无屏幕采集权限，**未执行任何伪造或模拟拍摄**。需人工采集路线决定后才能继续 EXAM02 的物理分支。

### 未批准事项

δ=ε=0.01、b=40、200 次重放、2000 次 bootstrap 仍为 `DRAFT_UNAPPROVED`；`approved_by` 为空。

## 2026-10-26 18:00 — EXAM02 准备完成（等待人工实拍）

负责人选择 **A 路线：人工实拍**。目标环境与设备已登记：

- 主环境 e1：R27qa 2560×1440 显示器 + Redmi K80；备选 e2（仅 EXAM08 外部面板）：华硕天选四 NE156FHM-NX6 1920×1080 + Redmi K90。
- 室内顶灯、JPEG 原生输出、固定 45 cm 垂直拍摄（详见 `captures/kit/capture_protocol.md`）。

已实际完成（非计划）：

1. 源池：440 个来源组 —— 220 真实摄影（COCO）+ 220 扩散生成（ELSA1M, SD 2.1）。
   分配：C_pool 80（40+40）、T_pilot 160（80+80）、D_sel 200（100+100，仅数字）。
   依据文件：`manifests/EXAM02/run_20261026T095*/sources.parquet` 等。
2. 显示资产：256 个 2560×1440 PNG（C_pool 80 + T_pilot 160 + TECH 16），内容矩形已登记。
3. 拍摄队列：技术批 20（16 唯一 + 4 重复）、主批 264（240 唯一 + 24 预定重复），分 4 段各 66。
   队列校验通过：文件齐全、类别平衡、重复项可追溯、序号唯一（`ops/logs/53_verify_kit.log`）。
4. 采集工具：全屏显示程序 `tools/capture_viewer.py`（断点续拍、进度 JSON）、一键启动 `captures/kit/run_*.bat`。
5. 导入工具：`scripts/import_captures.py` —— ORB+单应配准、内容矩形裁剪、模糊/曝光 QC、显式失败码；
   合成图单测已验证配准能恢复透视（`tests/test_registration.py`，73 项测试全部通过）。
6. 决策记录：`ops/decisions/DEC-0002_exam02_capture_design.md`。

**当前状态**：EXAM02 工程侧就绪，物理侧等待人工拍摄技术批 20 张。
未拍任何照片，未把模拟图当作实拍数据。EXAM04 及以后的真实翻拍结论在收到照片前一律为空。

## 2026-10-27 09:10 — 规模决策：240 → 1000（负责人决定）

- 负责人询问"200 多张是否太少、1000 张是否更稳"。做了**基于实测的精度分析**
  （`docs/precision_memo.md`、`metrics/EXAM02_precision/`）：
  - 240 张（T 160）：强模型对成对 AUC 差 95% 半宽约 ±0.10–0.13；
  - 1000 张（每类 500）：约 ±0.04–0.05；
  - 要到 ±0.01 需每类约 8 千–1.3 万张，人工不可行；δ=0.01 只能作实质意义阈值。
  - 先导的职责是筛出**大而具体**的错选，确认阶段再用新来源买精度。
- 负责人选择 **1000 张方案**：C_pool 200、T_pilot 700、预定重复 100；D_sel 500（仅数字）。
- 已重建：源池 1400 组（700 真实摄影 + 700 SD2.1 生成），显示资产 900 张 2560×1440（2.6 GB），
  主批队列 10 段 × 100 张，重复 100 个，队列校验通过（`ops/logs/68_verify_kit_1000.log`）。
- 决策记录：`ops/decisions/DEC-0003_scale_1000.md`。
- 仍未解决：生成器单一（SD 2.1）；跨生成器泛化留给 EXAM08 外部面板。

## 2026-10-28 10:20 — 技术批 20 张实拍 + 全链路验证

- 负责人拍完技术批（20 张，10 真实/10 生成/4 重复），照片已复制到 `captures/incoming/tech/`。
- 修复两处工程问题（失败记录均保留）：
  1. `captures/incoming/` 目录此前未创建 → 已创建 tech + main_s1..s10，并加一键打开脚本。
  2. OpenCV 在中文路径下 `imread` 失败 → 改为 `np.fromfile + imdecode`；captures 表
     `failure_code` 允许 null（成功行）。
- 导入结果：20/20，QC 全部通过；ORB 内点 163–1634、内点率 0.71–0.84；内容一致性 NCC 中位 0.88。
- 物理分支评分：6 模型 × 20 图，失败 0；AUC（仅工程检查）0.88/0.88/0.82/0.42/0.29/0.24。
- 几何诊断：屏幕占画面面积 0.60（协议期望 0.7–0.75）、角点偏差中位 3.6°、下半部比上半部暗约 39 灰阶。
- 结论：链路真实跑通；主批前建议调整摆位（靠近、抬高到屏幕中心、减少顶灯高光），
  先拍 1 张测试图复核，再重拍技术批 20 张，然后开始 1000 张主批。
- 报告：`reports/EXAM02_tech_qc.md`；诊断：`manifests/EXAM02_captures/run_20261028T022131Z_0b40bc66/`。
- main_s1 的 3 次"仅浏览"记录已归档到 `ops/archive/kit_progress/` 并重置进度。

## 2026-10-28 10:56 — 技术批重拍（第二版）验收

- 负责人按建议重拍 20 张；旧 20 张已归档到 `ops/archive/tech_batch1_*`，未删除。
- 导入 run `run_20261028T025632Z_7223a293`：20 张，**18 通过 / 2 模糊**（seq 15、17，Laplacian 36.5 / 44.0）。
- 摆位改善：屏幕占画面面积 **0.874**（第一版 0.599）；角点偏差中位 3.0°；NCC 中位约 0.93（第一版 0.88）；
  眩光占比中位 0.8%（第一版 1.3%）。
- 物理分支评分：6 模型 × 18 图，失败 0；AUC 0.86/0.88/0.84/0.45/0.38/0.28（仅工程检查）。
- 两个待修正：自动对焦不稳（2/20 失焦）→ 需 AF/AE 锁定；20 张内屏幕面积 0.78→1.00 单调上升
  → 手机在移动，必须物理固定。
- 决定：以第二版摆位作为主批设置；先拍 **s1（100 张）** 做规模 QC（面积漂移 ≤2%、失焦率、配准率），
  通过后再继续 s2–s10，避免 1000 张返工。
- 报告更新：`reports/EXAM02_tech_qc.md`。

## 2026-10-30 16:21 — 主批 s1 导入与规模 QC

- 用户把 s1 照片复制到 `captures/incoming/main_s1/`，实测 96 个文件（应 100）。
- 发现并修复三个工程问题（全部留痕）：
  1. **文件排序 bug**：导入器按 mtime 排序，Explorer 复制会重写 mtime 且顺序颠倒，
     导致 seq→照片映射整体反转（46 张 REGISTRATION_FAILED）。改为按文件名内嵌时间排序
     （`_file_time_key`），永不用 mtime 决定拍摄顺序。
  2. 补 `re` 缺失导入；`--allow-missing` 选项；缺帧记为 `MISSING_CAPTURE` 而非中断；
     窗口内匹配失败时回退到全局未用文件按 content match 兜底（≥18 匹配才接受）。
  3. `ops/tools/geometry_diagnostics.py`、`ops/tools/content_match.py` 改为带 --run/--queue
     参数并兼容新旧队列格式，可对任意 session 复用。
- 导入 run `run_20261030T081422Z_6f6b57a6`（最终 run 见 manifest）：
  - 96/96 映射；95 通过；1 张 EXPOSURE（seq 51，高光裁剪 7.2% > 5%，内容为白墙）。
  - 内容一致性 NCC：中位 **0.966**，最低 0.81 → 映射正确。
  - ORB 内点：中位 **933**（范围 99–1305）；角点偏差中位 **0.6°**。
  - 取景：屏幕宽占画面 **93%**（四角 95–3937 px / 4096），完整可见。
- 纠正一个此前的测量错误：技术批第二版报告的 `screen_area_fraction=0.874` 是单应矩阵外推
  所致（投影四角超出照片边界 -188…4293 px，实际屏幕左右各被裁掉约 9%）。
  16:9 屏幕在 4:3 照片中的面积上限是 0.75，s1 的 0.664 才是正确取景；**不需要再靠近**。
- 缺失 4 张（seq 97–100）：已把进度 97–100 重置为 pending（备份
  `ops/archive/queue_main_s1_progress_before_refill_20261030.json`），重开 run_main_s1.bat
  会从 97/100 继续；补拍后重新导入。

## 2026-10-30 16:38 — s1 最终验收（100/100）与几何指标更正

- 用户补齐 seq 97–100；重导 run `run_20261030T083055Z_0033e829`：100 文件、100 导入、
  **99 通过 / 1 EXPOSURE**（seq 51，高光 7.2%，白墙）。
- 映射：内容一致性 NCC 中位 0.9657（最低 0.8136）；ORB 内点中位 920（99–1305）。
- 取景：可见占画面 0.640–0.700、中位 0.666，投影四角全在画面内；角点偏差中位 0.59°（最大 2.90°）。
- 清晰度：最低 72.0（seq 16，阈值 60，边界样本）；亮度 59.7–161.9；高光最大 4.8%。
- **发现并更正指标语义错误**：`screen_coverage` 原先等于内容矩形/画布（0.5625 之类），
  与照片无关。新增 `ops/tools/screen_geometry.py` 重算 `screen_area_fraction` /
  `screen_visible_fraction` / `content_rect_frac` / `corner_dev_deg`；旧 qc.json 已归档，
  回填三项指标；`import_captures.py` 同步修正，s2 起直接记录正确值。
- 技术批第二版同步重算：可见占画面中位 0.801（0.755–0.864），证实此前 0.874 是未裁剪的
  外推值；报告已加更正节。
- s10 进度 3 条"仅浏览"标记（901–903）重置为 pending，备份
  `ops/archive/queue_main_s10_progress_before_reset_20261030.json`。
- 报告：`reports/EXAM02_s1_qc.md`（重写为最终版）、`reports/EXAM02_tech_qc.md`（新增 E 节）。
- 下一步：负责人拍 s2（100 张），固定手机 + AF/AE 锁定。

## 2026-10-30 16:45 — s1 物理分支评分（工程检查）

- `scripts/score_physical.py --import-run run_20261030T083055Z_0033e829 --session main_s1` →
  run `run_20261030T083849Z_b52e307a`：99 样本 × 6 模型 = 594 行，失败 0，覆盖率 1.0。
- AUC（n=99，工程检查，不是科学估计）：swinv2 0.874、siglip 0.867、swin_sdxl 0.760、
  convnext 0.604、vit 0.467、resnet 0.439。
- 早期信号：swin_sdxl 在数字分支是 0.921（EXAM01 技术批），到实拍降到 0.760；
  siglip 较稳（0.849→0.867）。方向与"物理链路削弱高频检测器"一致，但 n=99、区间很宽，
  不作结论，等 1000 张汇总。
- 产物：`scores/EXAM02/run_20261030T083849Z_b52e307a/`（parquet + physical_metrics.json）；
  日志 `ops/logs/score_main_s1.log`。
- 顺带修正 `score_physical.py` 的 note 文案（原先硬编码"20 images"），旧 json 已归档到
  `ops/archive/physical_metrics_main_s1_before_note_fix.json`。

## 2026-10-30 17:02 — s2 导入、QC 与评分

- `import_captures.py --session main_s2` → run `run_20261030T085838Z_01f75510`：
  100 文件、100 导入、**99 通过 / 1 BLUR**（seq 197，Laplacian 51.2、亮度 52.2，暗且失焦）。
- 映射：NCC 中位 0.9664（最低 0.8948，seq 108）；ORB 内点中位 846（141–1139）。
- 取景：可见占画面 **0.662–0.702，中位 0.693**（s1 为 0.666，段间漂移 +4%）；
  角点偏差中位 1.11°（最大 5.42°，s1 为 0.59°）；清晰度最低 118.6（除失败样本）；亮度 59.9–189.7。
- 补 `corner_dev_deg` 到导入器与 screen_geometry 工具，s1/s2 两份 qc.json 已回填
  （旧文件归档 `ops/archive/qc_*_before_geometry_fix_20261030T09*.json`）。
- 新增 `ops/tools/qc_summary.py`：汇总 s1–s10 的 QC 表 → `reports/EXAM02_main_qc.md`
  与 `manifests/EXAM02_qc_summary.csv`（带自动标记：缺帧/失败/取景越界/清晰度贴阈值/内容匹配弱）。
- 评分 `score_physical.py --session main_s2` → run `run_20261030T090141Z_40d93bb3`：
  99 样本 × 6 模型 = 594 行，失败 0。AUC：swinv2 0.923、siglip 0.819、swin 0.802、
  convnext 0.447、resnet 0.424、vit 0.416。
- 两段合并（n=198）早期信号：swinv2 ≈0.90、siglip ≈0.84、swin ≈0.78，其余低于 0.5；
  与数字分支相比，弱模型在实拍下进一步退化。仍属工程观察，不作结论。
- 75 项测试通过。

## 2026-10-30 17:06 — 日志基础设施：自动事件账本

- 新增 `src/proxy_selection/events.py`（append-only，只以 "a" 模式打开）。
- 新增 `ops/logs/EVENTS.jsonl`：每步一行 `{ts,stage,title,detail,run_id,extra}`，可机器重建。
- 三个入口自动落账：`import_captures.py`（导入）、`score_physical.py`（评分）、
  `qc_summary.py`（QC 汇总）；钩子全部 try/except 包裹，日志失败不得影响计算。
- `ops/tools/log_event.py`：`add` / `backfill` / `list`；backfill 幂等，按 (stage,run_id) 去重。
- 已回填 11 条历史事件（tech 两批、s1、s2 的导入与评分），当前 12 条。
- 新增 3 项事件账本测试；共 **78 项通过**。

## 2026-10-30 17:32 — s3 导入、对齐 bug 与修复

- s3 到达：100 个文件、进度 100/100 shot。
- 首次导入 `run_20261030T091627Z_6ee6ac79`：**29 通过 / 71 失败**（67 REGISTRATION_FAILED）。
  按内容重识别发现只有 15 张真正错位：照片 18–28 实际显示 seq 220–230（**seq 219 被跳过**），
  而旧导入器的"最近邻窗口贪心"从 219 起整体错位一位并**一路错到底**。
- 修复：`import_captures.py` 改为**全局单调对齐**（Needleman-Wunsch，`align_photos`，
  项目/照片可各自跳过，band 自适应，gap 罚 25 good-matches）。新增 3 项对齐测试。
- 新增 `--pin`（按 seq 强制指定补拍照片）与查看器 `--seqs`（只显示指定 seq，用于补拍）。
- 重导 `run_20261030T092220Z_acb3a319`：98 导入、**93 通过**、4 EXPOSURE、2 MISSING、1 REGISTRATION_FAILED。
  - MISSING：seq 219、272（确实没拍）
  - REGISTRATION_FAILED：seq 277（good 21 / inliers 10）
  - EXPOSURE：210、212、214、239（高光裁切 5.8–6.1%）
- 坏 run 已整体归档到 `ops/archive/exam02_s3_bad_alignment_20261030T0920/`（含 WHY.txt），未删除。
- 生成补拍批 `captures/kit/run_main_s3_retake.bat`（--seqs 219,272,277,210,212,214,239）。
- 81 项测试通过。

## 2026-10-30 17:38 - s3 补拍第一批（4 张）与隐私处理决策

- main_s3_retake 收到 4 张（17:27 拍摄），按 SIFT 内容匹配：172741->277、172744->210、172746->212、172750->214。
  - 219、272、239 未到。
- 质检：277 blur 338 / clip 0.7%；210 blur 487 / clip 1.2%；214 blur 487 / clip 1.7%（均合格）；
  212 clip 5.76% 仍超 5% 阈值，需再拍。
- 219 与 272 是同一源（src_f96db601820f5e47bee1264d）的原始与重复；用户口径为两张涉隐私已替换。
  替代图不能顶替：内容与队列不一致等于伪造该 seq。处理方案 = 整源排除 + EXCLUSIONS.json + 偏离记录（待确认）。
- 生成 run_main_s3_retake_b.bat（--seqs 212,239）。
- 记忆库 46 条。

## 2026-10-30 17:42 - 隐私源影响面排查

- 全 10 个 session 队列扫描：src_f96db601820f5e47bee1264d 仅出现在 s3 的 219（原始）与 272（重复），其余 session 无该源。
- 结论：若排除，影响面仅限 s3，C_pool 200->199、重复对 100->99。
- s3 当前有效：93 通过 + 补拍 4 张中 3 张合格（277/210/214）、1 张仍超曝光（212）；缺 219/272（隐私待定）、239。

## 2026-10-30 18:05 - s3 完成：补拍、隐私排除、重导与评分

- 用户选 A（隐私整源排除）；补拍 7 张到位（实际到 5 张有效：210/212/214/239/277；219/272 排除）。
- 新增 `data/EXCLUSIONS.json` 与 `ops/decisions/DEC-0004_privacy_exclusion.md`；
  `import_captures.py` 支持 `--exclusions` 与 `--pin`，排除项写 `excluded` 行。
- 重导 `run_20261030T094833Z_122b06d8`：100 文件 / 98 有效 / **98 通过 / 0 失败 / 2 排除**。
- 指标：NCC 中位 0.9657（min 0.8727 seq265）；内点中位 859（min 20 seq277）；
  取景 0.663（0.631-0.688）；角点 0.41°（max 2.03）；清晰度 min 97.5（seq220）；高光 max 4.0%（seq206）。
- 评分 `run_20261030T095115Z_29b8b048`：588 行 0 失败；AUC swinv2 0.867、siglip 0.808、swin_sdxl 0.681、
  vit 0.465、convnext 0.442、resnet 0.313（n=98，工程核对）。
- 报告 `reports/EXAM02_s3_qc.md`；qc_summary 增加 excluded 列；81 项测试通过。
- 下一段：s4。
