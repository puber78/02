# 项目记忆系统（append-only）

## 规则

1. **只追加，不修改、不删除。** `JOURNAL.jsonl` 只允许 `append`。任何"整理"都只能新增
   一条更正条目，并引用被更正条目的 id。
2. **每条记录带哈希链。** 每条记录的 `hash = sha256(上一条 hash + 本条规范化 JSON)`；
   `HEAD.json` 保存条数与链头。任何悄悄改动或删除都会被 `verify` 发现。
3. **上下文缺失时先查记忆。** 新会话/长任务开始时：
   `python ops/memory/memory.py search "<关键词>"`
   有相关条目先读条目与它引用的文件；没有相关条目再扩展检索范围（报告 → 日志 → 数据）。
4. **定期写入。** 每个阶段结束、每次导入/评分/决策之后追加条目；`sync-worklog` 会把
   `ops/logs/WORKLOG.md` 里尚未入库的小节自动补进来（按小节哈希去重，可反复运行）。

## 命令

```bash
cd proxy-selection-research

# 追加（永远成功，不覆盖）
python ops/memory/memory.py add --type result --title "s1 导入完成" \
  --body "100/100，99 通过，1 EXPOSURE……" --tags s1,qc --refs run_20261030T083055Z_0033e829

# 检索（打分：标题+正文+标签+引用，中文按二元组）
python ops/memory/memory.py search "s1 取景 0.664"
python ops/memory/memory.py search "AUC" --type result --limit 5

# 完整性校验（被改过会指出第一条断链）
python ops/memory/memory.py verify

# 最近条目 / 统计
python ops/memory/memory.py tail 10
python ops/memory/memory.py stats

# 把 WORKLOG 新增小节同步进来
python ops/memory/memory.py sync-worklog
```

## 条目类型

`action`（做了什么）、`decision`（为什么这样定）、`result`（测到了什么数）、
`finding`（结论/教训）、`environment`（环境与配置事实）、`plan`（下一步）、
`incident`（故障与修复）。

## 与文件系统的关系

- 记忆条目是**索引与结论**，不是数据本体；数值与产物仍以仓库文件为准（路径写在 `refs`）。
- 大文件（照片、权重、parquet）不入库，只记 SHA-256 或路径。
- 本目录不参与任何训练/评分流程，删除会破坏哈希链，禁止。
