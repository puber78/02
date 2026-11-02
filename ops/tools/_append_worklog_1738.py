from pathlib import Path

p = Path("ops/logs/WORKLOG.md")
sec = """
## 2026-10-30 17:42 - 隐私源影响面排查

- 全 10 个 session 队列扫描：src_f96db601820f5e47bee1264d 仅出现在 s3 的 219（原始）与 272（重复），其余 session 无该源。
- 结论：若排除，影响面仅限 s3，C_pool 200->199、重复对 100->99。
- s3 当前有效：93 通过 + 补拍 4 张中 3 张合格（277/210/214）、1 张仍超曝光（212）；缺 219/272（隐私待定）、239。
"""
p.write_text(p.read_text("utf-8") + sec, encoding="utf-8")
print("ok")
