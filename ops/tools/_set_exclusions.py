import json
from datetime import datetime, timezone
from pathlib import Path

root = Path(".").resolve()
now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

ex_path = root / "data" / "EXCLUSIONS.json"
ex_path.write_text(
    json.dumps(
        {
            "created_at": now,
            "policy": "An excluded source is removed from every session and role; the queue item stays in the manifest as qc_status=excluded with failure_code=EXCLUDED_PRIVACY so denominators are auditable.",
            "exclusions": [
                {
                    "source_id": "src_f96db601820f5e47bee1264d",
                    "reason": "privacy: user asked to remove this image from the study (its display asset is dsp_cd5d09eb6eca56c7bf63a951)",
                    "scope": ["main_s3:219", "main_s3:272"],
                    "decided_by": "user",
                    "decision_ref": "DEC-0004",
                    "decided_at": now,
                }
            ],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

dec = root / "ops" / "protocols" / "DECISIONS.md"
text = dec.read_text("utf-8")
entry = f"""
## DEC-0004 - 隐私源整源排除（2026-10-30）

- 决定：源 `src_f96db601820f5e47bee1264d`（显示资产 `dsp_cd5d09eb6eca56c7bf63a951`）从研究中整源排除。
- 范围：`main_s3:219`（原始）与 `main_s3:272`（重复）；全 10 个 session 扫描确认该源仅出现在这两处。
- 理由：用户指出该图涉隐私并要求移除；**不采用替代照片**（内容与队列不符等于伪造该 seq 的采集记录）。
- 实现：`data/EXCLUSIONS.json`；导入时写成 `qc_status=excluded / failure_code=EXCLUDED_PRIVACY`，不写入 capture 记录与 rectified 图。
- 影响：s3 有效队列 98；C_pool 200 -> 199；设计重复对 100 -> 99（该源为其中一对）。分析分母以 98 为准并在论文 Methods 中披露。
- 批准：用户（2026-10-30，选择 A）。
"""
dec.write_text(text + entry, encoding="utf-8")
print("exclusions + decision written", now)
