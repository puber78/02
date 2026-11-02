import json
from pathlib import Path

root = Path(".").resolve()
retake = root / "captures" / "incoming" / "main_s3_retake"
pins = {
    "210": str(retake / "IMG_20261030_172744.jpg"),
    "212": str(retake / "IMG_20261030_174008.jpg"),
    "214": str(retake / "IMG_20261030_172750.jpg"),
    "239": str(retake / "IMG_20261030_174017.jpg"),
    "277": str(retake / "IMG_20261030_172741.jpg"),
}
out = root / "captures" / "kit" / "pins_main_s3.json"
out.write_text(json.dumps(pins, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(out)
