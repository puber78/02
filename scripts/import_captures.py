"""Import, register and QC the physical captures of one session.

Mapping strategy
----------------
The photographer shoots strictly in queue order; extra files are retakes.  Each
capture is matched against its *expected* display asset with ORB features and a
small look-ahead (1-2 extra files), so a retake cannot shift the whole session.
Every assignment is verified by a homography with RANSAC inlier counting; a low
inlier ratio is recorded as an explicit QC failure rather than silently kept.

Registration
------------
The homography maps the 2560x1440 display canvas onto the photo; the photo is
warped to the canvas, then cropped to the stored content rectangle.  This is the
frozen physical branch input; the un-warped photo is kept as raw evidence.

Outputs
-------
  data/raw/captures/<session>/<capture_id>.jpg       original bytes (copied)
  data/physical/<session>/<capture_id>.png           rectified content crop
  manifests/EXAM02_captures/<run>/captures.parquet   schema-valid capture rows
  manifests/EXAM02_captures/<run>/qc.json            per-capture QC metrics
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

from proxy_selection.contracts.ids import new_capture_id  # noqa: E402
from proxy_selection.hashing import sha256_bytes, sha256_file  # noqa: E402
from proxy_selection.io import Ledger, write_new, write_parquet  # noqa: E402
from proxy_selection.runlog import RunLogger  # noqa: E402

def imread_u(path) -> "np.ndarray | None":
    """OpenCV cannot open non-ASCII paths on Windows; decode from bytes instead."""
    try:
        data = np.fromfile(str(path), dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_u(path, img) -> bool:
    ext = Path(path).suffix or ".png"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        return False
    buf.tofile(str(path))
    return True


MIN_MATCHES = 18
MIN_INLIER_RATIO = 0.25
#: Penalty (in ORB "good matches") for leaving one queue item or one photo
#: unpaired during the global alignment.  A correct pair scores in the
#: hundreds, a wrong pair a few dozen, so this keeps gaps cheap but wrong
#: pairings expensive.
ALIGN_GAP_PENALTY = 25.0


def align_photos(items, files, score_pair, band: int = 4, gap_pen: float = ALIGN_GAP_PENALTY) -> dict[int, int]:
    """Global monotone (Needleman-Wunsch) alignment of queue items to photos.

    Returns ``{item_index: photo_index}``.  ``score_pair(i, k)`` returns a
    similarity score for item ``i`` and photo ``k``.  Items and photos may be
    skipped independently (each skip costs ``gap_pen``), and a pair is only
    allowed when ``abs(k - i) <= band``.  This keeps a single skipped capture
    or a duplicate shot local instead of shifting every later pair.
    """
    n, m = len(items), len(files)
    neg = float("-inf")
    dp = [[neg] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[str, int, int] | None]] = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(n + 1):
        row = dp[i]
        for k in range(m + 1):
            cur = row[k]
            if cur == neg:
                continue
            if i < n and k < m and abs(k - i) <= band:
                v = cur + score_pair(i, k)
                if v > dp[i + 1][k + 1]:
                    dp[i + 1][k + 1] = v
                    back[i + 1][k + 1] = ("match", i, k)
            if i < n:
                v = cur - gap_pen
                if v > dp[i + 1][k]:
                    dp[i + 1][k] = v
                    back[i + 1][k] = ("skip_item", i, k)
            if k < m:
                v = cur - gap_pen
                if v > dp[i][k + 1]:
                    dp[i][k + 1] = v
                    back[i][k + 1] = ("skip_photo", i, k)
    if dp[n][m] == neg:
        return {}
    assignment: dict[int, int] = {}
    i, k = n, m
    while i > 0 or k > 0:
        step = back[i][k]
        if step is None:
            break
        kind, pi, pk = step
        if kind == "match":
            assignment[pi] = pk
        i, k = pi, pk
    return assignment

BLUR_MIN = 60.0
MEAN_MIN, MEAN_MAX = 25.0, 235.0
# Exposure gate v2 (DEC-0005): saturation is judged against the display asset, because
# bright content (white signs, skies) saturates by itself. Only capture-induced extra
# saturation counts.
CLIP_MAX = 0.05
CLIP_EXCESS_MAX = 0.05
# Sharpness gate v2 (DEC-0006): an absolute Laplacian floor measures the CONTENT's
# high-frequency energy as much as the focus (a dark or smooth scene can sit at 40-60
# while being perfectly sharp).  A capture therefore also passes when it keeps at
# least SHARP_RATIO_MIN of the display asset's high-frequency energy, measured after
# resizing both to 1280x720 -- and only when registration and content agreement are
# themselves strong, so a wrong/blank frame cannot be rescued by this escape.
BLUR_RATIO_MIN = 0.5
BLUR_ESCAPE_MIN_NCC = 0.90
BLUR_ESCAPE_MIN_INLIERS = 200


def orb_features(gray: np.ndarray, n: int = 5000) -> tuple[list, np.ndarray]:
    orb = cv2.ORB_create(nfeatures=n, fastThreshold=12)
    kp, des = orb.detectAndCompute(gray, None)
    return kp, des


def match_count(des_a: np.ndarray | None, des_b: np.ndarray | None) -> int:
    if des_a is None or des_b is None or len(des_a) < 2 or len(des_b) < 2:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = bf.knnMatch(des_a, des_b, k=2)
    good = 0
    for p in pairs:
        if len(p) == 2 and p[0].distance < 0.75 * p[1].distance:
            good += 1
    return good


def register(display: np.ndarray, photo: np.ndarray) -> dict:
    g1 = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    kp1, d1 = orb_features(g1)
    kp2, d2 = orb_features(g2)
    if d1 is None or d2 is None or len(d1) < 8 or len(d2) < 8:
        return {"ok": False, "reason": "too_few_features", "good": 0, "inliers": 0}
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    pairs = bf.knnMatch(d1, d2, k=2)
    good = [p[0] for p in pairs if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
    if len(good) < MIN_MATCHES:
        return {"ok": False, "reason": "too_few_matches", "good": len(good), "inliers": 0}
    src = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    if H is None or mask is None:
        return {"ok": False, "reason": "homography_failed", "good": len(good), "inliers": 0}
    inliers = int(mask.sum())
    ratio = inliers / max(1, len(good))
    return {
        "ok": inliers >= MIN_MATCHES and ratio >= MIN_INLIER_RATIO,
        "reason": "" if inliers >= MIN_MATCHES and ratio >= MIN_INLIER_RATIO else "low_inlier_ratio",
        "good": len(good),
        "inliers": inliers,
        "inlier_ratio": ratio,
        "H": H,
    }


def _content_ncc(rect: np.ndarray, ref: np.ndarray, w: int = 256, h: int = 144) -> float:
    """Grayscale NCC between the rectified capture and the asset it should show."""
    a = cv2.resize(cv2.cvtColor(rect, cv2.COLOR_BGR2GRAY), (w, h), interpolation=cv2.INTER_AREA)
    b = cv2.resize(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY), (w, h), interpolation=cv2.INTER_AREA)
    x = a.astype(np.float64).ravel()
    y = b.astype(np.float64).ravel()
    x -= x.mean()
    y -= y.mean()
    denom = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float("nan") if denom == 0 else float(np.dot(x, y) / denom)


def _sharpness_at_720(img: np.ndarray) -> float:
    g = cv2.cvtColor(cv2.resize(img, (1280, 720), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def qc_metrics(rect: np.ndarray, asset: np.ndarray | None = None) -> dict:
    gray = cv2.cvtColor(rect, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean = float(gray.mean())
    clipped_hi = float((gray >= 250).mean())
    clipped_lo = float((gray <= 5).mean())
    asset_clip = None
    excess = None
    asset_blur = None
    blur_ratio = None
    if asset is not None:
        h, w = gray.shape[:2]
        if asset.shape[0] >= h and asset.shape[1] >= w:
            ref = asset[:h, :w]
        else:
            ref = cv2.resize(asset, (w, h))
        asset_clip = float((cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY) >= 250).mean())
        excess = clipped_hi - asset_clip
        exposure_ok = MEAN_MIN <= mean <= MEAN_MAX and excess <= CLIP_EXCESS_MAX
        asset_blur = _sharpness_at_720(asset)
        blur_ratio = _sharpness_at_720(rect) / max(asset_blur, 1e-6)
    else:
        exposure_ok = MEAN_MIN <= mean <= MEAN_MAX and clipped_hi < CLIP_MAX
    return {
        "blur_laplacian_var": blur,
        "mean_luma": mean,
        "clip_high_fraction": clipped_hi,
        "clip_low_fraction": clipped_lo,
        "clip_asset_fraction": asset_clip,
        "clip_excess": excess,
        "asset_blur_720": asset_blur,
        "blur_ratio_720": blur_ratio,
        "sharp": blur >= BLUR_MIN,
        "exposure_ok": exposure_ok,
    }


def screen_geometry(photo_shape: tuple[int, int], H: np.ndarray, geom: dict, canvas: tuple[int, int]) -> dict:
    """True framing geometry (replaces the earlier mislabelled ``screen_coverage``).

    * ``screen_area_fraction``    projected screen-quad area / photo area.  Can exceed 1
      when the screen is physically cut off by the frame -- that is the diagnostic value.
    * ``screen_visible_fraction`` area of (quad INTERSECT photo) / photo area, i.e. how much
      of the photograph the screen really occupies.  This is the honest framing number.
    * ``content_rect_frac``       content-rect area / display-canvas area.  A layout constant
      of the display asset (e.g. 0.5625 for 4:3 content in a 16:9 canvas); it says nothing
      about the photograph and must never be reported as capture coverage.
    """
    ph, pw = photo_shape[:2]
    ch, cw = canvas[1], canvas[0]
    corners = np.float32([[0, 0], [cw, 0], [cw, ch], [0, ch]]).reshape(-1, 1, 2)
    quad = cv2.perspectiveTransform(corners, H).reshape(-1, 2)
    quad_area = float(abs(cv2.contourArea(quad.astype(np.float32))))
    photo_rect = np.float32([[0, 0], [pw, 0], [pw, ph], [0, ph]])
    inter_area, _ = cv2.intersectConvexConvex(quad, photo_rect)
    angs = []
    for i in range(4):
        a, b, c = quad[(i - 1) % 4], quad[i], quad[(i + 1) % 4]
        v1, v2 = a - b, c - b
        cosang = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)
        angs.append(np.degrees(np.arccos(np.clip(cosang, -1, 1))))
    return {
        "screen_area_fraction": round(quad_area / (pw * ph), 4),
        "screen_visible_fraction": round(float(inter_area) / (pw * ph), 4),
        "content_rect_frac": round(float(geom["content_w"] * geom["content_h"]) / (cw * ch), 4),
        "corner_dev_deg": round(float(max(abs(a - 90.0) for a in angs)), 2),
    }


def poly_area(poly: np.ndarray) -> float:
    return float(abs(cv2.contourArea(poly.astype(np.float32))))


_NAME_TIME = re.compile(r"(\d{8})[_\-](\d{6})")


def _file_time_key(p: Path) -> tuple[str, str]:
    """Order photos by the capture time encoded in the filename, then by name.

    Never by mtime: a copy operation (MTP/Explorer) may rewrite mtimes in reverse
    order, which silently reverses the queue and destroys the seq -> photo mapping.
    """
    m = _NAME_TIME.search(p.name)
    if m:
        return (m.group(1) + m.group(2), p.name)
    return (p.stat().st_mtime_ns.__str__(), p.name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", required=True)
    ap.add_argument("--incoming", required=True)
    ap.add_argument("--queue", default=None)
    ap.add_argument("--device-id", default="redmi_k80")
    ap.add_argument("--lookahead", type=int, default=2)
    ap.add_argument("--allow-missing", action="store_true", help="continue when photos are missing; records MISSING_CAPTURE rows")
    ap.add_argument("--pin", default=None, help="JSON {seq: photo path} forcing a retaken photo onto a queue item")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    pins: dict[int, str] = {}
    if args.pin:
        pins = {int(k): v for k, v in json.loads(Path(args.pin).read_text("utf-8")).items()}

    log = RunLogger.start(ROOT, note=f"import captures {args.session}")
    ledger = Ledger(ROOT / "ops")
    queue_path = Path(args.queue) if args.queue else ROOT / "captures" / "kit" / f"queue_{args.session}.json"
    queue = json.loads(queue_path.read_text("utf-8"))
    items = [it for it in queue["items"]]
    progress_path = queue_path.with_name(queue_path.stem + "_progress.json")
    progress = json.loads(progress_path.read_text("utf-8")) if progress_path.exists() else {"items": {}}
    status = {int(k): v.get("status") for k, v in progress.get("items", {}).items()}
    expected = [it for it in items if status.get(it["seq"]) == "shot"]
    skipped = [it["seq"] for it in items if status.get(it["seq"]) == "skipped"]

    # --- exclusions: user-approved, recorded in data/EXCLUSIONS.json ----------
    # An excluded queue item is NOT a missing capture: it stays in the manifest as
    # ``excluded`` with an auditable code, so downstream analyses can drop it
    # without silently changing the denominators.
    excl_path = ROOT / "data" / "EXCLUSIONS.json"
    exclusions: dict[tuple[str, int], dict] = {}
    if excl_path.exists():
        for e in json.loads(excl_path.read_text("utf-8")).get("exclusions", []):
            for sc in e.get("scope", []):
                sess, seq = str(sc).split(":")
                exclusions[(sess, int(seq))] = e
    excluded_items = [it for it in expected if (args.session, int(it["seq"])) in exclusions]
    expected = [it for it in expected if (args.session, int(it["seq"])) not in exclusions]
    if excluded_items:
        log.event("exclusions", n=len(excluded_items), seqs=sorted(int(it["seq"]) for it in excluded_items))
    if not expected:
        print("no items marked as shot in the progress file")
        return 2

    incoming = Path(args.incoming)
    files = sorted(
        [p for p in incoming.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".heic", ".png"}],
        key=_file_time_key,
    )
    log.event("incoming", n_files=len(files), n_expected=len(expected), skipped=skipped)
    if len(files) < len(expected) and not args.allow_missing:
        print(f"FAIL: {len(files)} files for {len(expected)} expected shots")
        log.finish("FAIL", reason="too_few_files")
        return 3

    # --- global monotone alignment -------------------------------------------
    # A per-item nearest-window search loses sync for good as soon as the
    # operator skips one queue item: every later photo is attached to the
    # previous item and registration fails all the way to the end.  Align the
    # whole sequence once, so a skipped item or a duplicate photo stays local.
    align_orb = cv2.ORB_create(nfeatures=1500, fastThreshold=12)
    align_photo: dict[int, "np.ndarray | None"] = {}
    align_disp: dict[str, "np.ndarray | None"] = {}

    def _align_des(img: np.ndarray):
        _, des = align_orb.detectAndCompute(img, None)
        return des

    def photo_des_align(k: int):
        if k not in align_photo:
            img = imread_u(files[k])
            align_photo[k] = None if img is None else _align_des(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        return align_photo[k]

    def disp_des_align(it: dict):
        key = it["display_asset_id"]
        if key not in align_disp:
            img = imread_u(ROOT / it["file_relpath"])
            align_disp[key] = None if img is None else _align_des(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        return align_disp[key]

    score_cache: dict[tuple[int, int], float] = {}

    # Items supplied from a retake folder (``--pin``) and excluded items are kept
    # out of the sequence alignment: their photos are extra files that would
    # otherwise steal the best match from the item they really belong to.
    pinned_items = [it for it in expected if int(it["seq"]) in pins]
    align_items = [it for it in expected if int(it["seq"]) not in pins]
    align_pos = {int(it["seq"]): i for i, it in enumerate(align_items)}

    def score_pair(i: int, k: int) -> float:
        key = (i, k)
        if key not in score_cache:
            score_cache[key] = float(match_count(disp_des_align(align_items[i]), photo_des_align(k)))
        return score_cache[key]

    assignment = align_photos(
        align_items,
        files,
        score_pair,
        band=max(4, args.lookahead + 2, len(files) - len(align_items) + 2),
        gap_pen=ALIGN_GAP_PENALTY,
    )
    log.event("alignment", matched=len(assignment), items=len(align_items), files=len(files))

    display_cache: dict[str, tuple[np.ndarray, np.ndarray | None]] = {}
    capture_rows, qc_rows = [], []

    for it in expected:
        disp = imread_u(ROOT / it["file_relpath"])
        if disp is None:
            raise FileNotFoundError(it["file_relpath"])
        if it["display_asset_id"] not in display_cache:
            g = cv2.cvtColor(disp, cv2.COLOR_BGR2GRAY)
            _, des = orb_features(g)
            display_cache[it["display_asset_id"]] = (disp, des)

        k = assignment.get(align_pos.get(int(it["seq"]), -1))
        pin_path = pins.get(int(it["seq"]))
        if pin_path is not None:
            src_file: Path | None = Path(pin_path)
        else:
            src_file = files[k] if k is not None else None
        photo = imread_u(src_file) if src_file is not None else None
        if photo is None:
            qc_rows.append(
                {
                    "seq": it["seq"],
                    "capture_id": None,
                    "source_id": it["source_id"],
                    "role": it["role"],
                    "label": it["label"],
                    "is_repeat": bool(it.get("is_repeat", False)),
                    "file": None,
                    "rectified": None,
                    "qc_status": "failed",
                    "failure_code": "MISSING_CAPTURE",
                }
            )
            continue
        reg = register(disp, photo)
        capture_id = new_capture_id()
        raw_digest = sha256_file(src_file)

        qc_status, failure_code = "pending", None
        rect_path = None
        qc = {"good_matches": reg.get("good"), "inliers": reg.get("inliers"),
              "inlier_ratio": reg.get("inlier_ratio")}
        if not reg["ok"]:
            qc_status, failure_code = "failed", "REGISTRATION_FAILED"
        else:
            # H maps display coordinates -> photo coordinates; invert to rectify
            H_inv = np.linalg.inv(reg["H"])
            warped = cv2.warpPerspective(photo, H_inv, (disp.shape[1], disp.shape[0]))
            # geometry shipped with the queue item (content rect inside the canvas)
            geom = it.get("geometry") or {
                "content_x": 0, "content_y": 0, "content_w": disp.shape[1], "content_h": disp.shape[0]
            }
            x, y, w, h = geom["content_x"], geom["content_y"], geom["content_w"], geom["content_h"]
            rect = warped[y : y + h, x : x + w]
            ref_crop = disp[y : y + h, x : x + w]
            qc.update(qc_metrics(rect, ref_crop))
            qc["content_ncc"] = round(_content_ncc(rect, ref_crop), 6)
            geo = screen_geometry(photo.shape, reg["H"], geom, (disp.shape[1], disp.shape[0]))
            qc.update(geo)
            # ``screen_coverage`` keeps its historical name but now means the visible
            # framing fraction (screen_visible_fraction); before 2026-10-30 it wrongly held
            # the display-side content-rect fraction, see reports/EXAM02_s1_qc.md.
            qc["screen_coverage"] = geo["screen_visible_fraction"]
            sharp_escape = (
                not qc["sharp"]
                and (qc.get("blur_ratio_720") or 0.0) >= BLUR_RATIO_MIN
                and (qc.get("content_ncc") or 0.0) >= BLUR_ESCAPE_MIN_NCC
                and (qc.get("inliers") or 0) >= BLUR_ESCAPE_MIN_INLIERS
            )
            qc["sharp_escape_used"] = bool(sharp_escape)
            if not qc["sharp"] and not sharp_escape:
                qc_status, failure_code = "failed", "BLUR"
            elif not qc["exposure_ok"]:
                qc_status, failure_code = "failed", "EXPOSURE"
            else:
                qc_status = "passed"
            if not args.dry_run:
                out = ROOT / "data" / "physical" / args.session / f"{capture_id}.png"
                out.parent.mkdir(parents=True, exist_ok=True)
                imwrite_u(out, rect)
                rect_path = str(out.relative_to(ROOT)).replace("\\", "/")
                ledger.record_artifact(out, kind="physical_rectified", run_id=log.run_id)

        if not args.dry_run:
            raw_dir = ROOT / "data" / "raw" / "captures" / args.session
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_dest = raw_dir / f"{capture_id}{src_file.suffix.lower()}"
            shutil.copy2(src_file, raw_dest)
            ledger.record_artifact(raw_dest, kind="capture_original", run_id=log.run_id)

        capture_rows.append(
            {
                "capture_id": capture_id,
                "display_asset_id": it["display_asset_id"],
                "session_id": args.session,
                "attempt_index": int(it["seq"]),
                "is_planned_repeat": bool(it.get("is_repeat", False)),
                "capture_file_sha256": raw_digest,
                "device_id": args.device_id,
                "qc_status": qc_status,
                "failure_code": failure_code,
                "captured_at": datetime.fromtimestamp(src_file.stat().st_mtime, tz=timezone.utc).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "run_id": log.run_id,
            }
        )
        qc_rows.append(
            {
                "seq": it["seq"],
                "capture_id": capture_id,
                "source_id": it["source_id"],
                "role": it["role"],
                "label": it["label"],
                "is_repeat": bool(it.get("is_repeat", False)),
                "file": str(src_file),
                "rectified": rect_path,
                "qc_status": qc_status,
                "failure_code": failure_code,
                **{k2: v for k2, v in qc.items() if not isinstance(v, np.ndarray)},
            }
        )

    for it in excluded_items:
        e = exclusions[(args.session, int(it["seq"]))]
        qc_rows.append(
            {
                "seq": it["seq"],
                "capture_id": None,
                "source_id": it["source_id"],
                "role": it["role"],
                "label": it["label"],
                "is_repeat": bool(it.get("is_repeat", False)),
                "file": None,
                "rectified": None,
                "qc_status": "excluded",
                "failure_code": "EXCLUDED_PRIVACY",
                "exclusion_reason": e.get("reason"),
                "exclusion_ref": e.get("decision_ref"),
            }
        )
    qc_rows.sort(key=lambda r: int(r["seq"]))

    outdir = ROOT / "manifests" / "EXAM02_captures" / log.run_id
    outdir.mkdir(parents=True, exist_ok=True)
    if capture_rows and not args.dry_run:
        write_parquet(outdir / "captures.parquet", capture_rows, "captures", ledger=ledger, run_id=log.run_id)
    write_new(outdir / "qc.json", json.dumps(qc_rows, ensure_ascii=False, indent=2), kind="qc")
    summary = {
        "session": args.session,
        "expected": len(expected),
        "files": len(files),
        "imported": len(capture_rows),
        "missing": sum(1 for r in qc_rows if r["failure_code"] == "MISSING_CAPTURE"),
        "passed": sum(1 for r in qc_rows if r["qc_status"] == "passed"),
        "failed": sum(1 for r in qc_rows if r["qc_status"] == "failed"),
        "excluded": sum(1 for r in qc_rows if r["qc_status"] == "excluded"),
        "pinned": {int(k): str(v) for k, v in pins.items()},
        "failure_codes": pd.Series([r["failure_code"] for r in qc_rows if r["failure_code"]]).value_counts().to_dict(),
        "skipped": skipped,
        "dry_run": args.dry_run,
    }
    write_new(outdir / "import_summary.json", json.dumps(summary, ensure_ascii=False, indent=2), kind="import_summary")
    try:  # ledger hook: logging must never break the pipeline
        from proxy_selection.events import log_event

        log_event(
            "import",
            f"{args.session} 导入",
            detail=(
                f"files={summary['files']} imported={summary['imported']} "
                f"missing={summary['missing']} passed={summary['passed']} failed={summary['failed']}"
            ),
            run_id=log.run_id,
            extra={"failure_codes": summary["failure_codes"]},
        )
    except Exception:  # noqa: BLE001 - never fail an import over logging
        pass
    log.finish("PASS" if summary["failed"] == 0 else "PARTIAL", **{k: v for k, v in summary.items() if k != "skipped"})
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["imported"] == len(expected):
        return 0
    if args.allow_missing and summary["imported"] + summary["missing"] == len(expected):
        return 0
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
