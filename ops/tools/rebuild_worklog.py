"""重建 WORKLOG 主档 + 追加 EXAM05 章节。

背景：2026-11-02 14:28 的一次写入把根目录 WORKLOG.md 截断为 3 个残段（19/20/39），
而运维版 ops/WORKLOG.md 也是部分内容。为满足"任何输出必须留痕、不得删除"的要求：

1. 先把两份残存文件复制到 ops/archive/（带时间戳），原文件不被删除（仅改名为 .superseded）；
2. 以 ops/logs/EVENTS.jsonl（append-only，94 条）为主干重建时间线；
3. 把两份残存分节原文完整附在文末，标注来源；
4. 追加 EXAM05 章节（本次分析）。
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "ops/archive"
EVENTS = ROOT / "ops/logs/EVENTS.jsonl"
ROOT_WL = ROOT / "WORKLOG.md"
OPS_WL = ROOT / "ops/WORKLOG.md"

EXAM05 = """
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
"""

INCIDENT = """
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
"""


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    root_text = ROOT_WL.read_text(encoding="utf-8") if ROOT_WL.exists() else ""
    ops_text = OPS_WL.read_text(encoding="utf-8") if OPS_WL.exists() else ""
    shutil.copy2(ROOT_WL, ARCHIVE / f"WORKLOG_fragment_root_{stamp}.md")
    if OPS_WL.exists():
        shutil.copy2(OPS_WL, ARCHIVE / f"WORKLOG_fragment_ops_{stamp}.md")

    events = [json.loads(x) for x in EVENTS.read_text(encoding="utf-8").splitlines() if x.strip()]
    memory = [json.loads(x) for x in (ROOT / "ops/memory/JOURNAL.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    reports = sorted(p.name for p in (ROOT / "reports").glob("*.md"))

    out = []
    out.append("# WORKLOG（重建主档）")
    out.append("")
    out.append(f"重建时间：{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    out.append("")
    out.append("> 本文件在 2026-11-02 重建：原 `WORKLOG.md` 被一次覆盖写截断为 3 个残段。")
    out.append("> 原始事实来源：`ops/logs/EVENTS.jsonl`（append-only，逐事件）、`ops/memory/JOURNAL.jsonl`（哈希链记忆）、")
    out.append("> 每个 run 的 `ops/logs/run_*.jsonl`、`reports/*.md`、`manifests/**`、`scores/**`。")
    out.append("> 两份残存分节原文完整附于 §C，原件另存 `ops/archive/WORKLOG_fragment_*.md`。")
    out.append("")
    out.append("## §A 事件时间线（来自 EVENTS.jsonl）")
    out.append("")
    out.append(f"共 {len(events)} 条事件。")
    out.append("")
    for e in events:
        ts = e.get("ts", "")
        stage = e.get("stage", "")
        title = e.get("title", "")
        detail = (e.get("detail") or "").replace("\n", " ")
        run = e.get("run_id", "")
        line = f"- `{ts}` **[{stage}]** {title}"
        if detail:
            line += f" —— {detail}"
        if run:
            line += f"（{run}）"
        out.append(line)
    out.append("")
    out.append("## §B 阶段性结果索引")
    out.append("")
    out.append("| 报告 | 文件 |")
    out.append("| --- | --- |")
    for r in reports:
        out.append(f"| {r} | `reports/{r}` |")
    out.append("")
    out.append(f"记忆日志：{len(memory)} 条（`ops/memory/JOURNAL.jsonl`，哈希链）。")
    out.append("")
    out.append("## §C 残存分节原文")
    out.append("")
    out.append("### C.1 根 WORKLOG.md 残段（重建前）")
    out.append("")
    out.append(root_text.strip() or "（空）")
    out.append("")
    out.append("### C.2 ops/WORKLOG.md 残段（重建前）")
    out.append("")
    out.append(ops_text.strip() or "（空）")
    out.append(EXAM05)
    out.append(INCIDENT)
    ROOT_WL.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"rebuilt WORKLOG.md with {len(events)} events, {len(memory)} memory entries, {len(reports)} reports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
