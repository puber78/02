import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "captures" / "kit"
for name in ["queue_tech_progress.json", "queue_main_s1_progress.json"]:
    p = KIT / name
    if not p.exists():
        print(name, "MISSING")
        continue
    d = json.loads(p.read_text("utf-8"))
    items = d.get("items", {})
    c = Counter(v.get("status") for v in items.values())
    seqs = sorted(int(k) for k in items)
    print(name, "| session:", d.get("session"), "| started:", d.get("started_at"), "| marked:", dict(c))
    print("   seq range:", (seqs[0], seqs[-1]) if seqs else None, "| last:", items.get(str(seqs[-1])) if seqs else None)
