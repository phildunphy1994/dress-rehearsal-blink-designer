#!/usr/bin/env python3
"""01_collect.py — Collect Corpus A (HABS Robie House, Library of Congress) with a per-item rights log.

What it does (PRD §1.1, §7.3):
  * downloads the master TIFF of each of the 25 measured drawings and the 1024-px JPEG of each of the 9
    photographs, untouched, into corpus_a/ (originals) — file names {sp:02d}_{slug}.{ext}
  * fetches each item's rights advisory from its own Library of Congress resource page (JSON API) and
    records it verbatim
  * resizes every image to at most 1568 px on the longest edge into corpus_a/resized/ (PNG) and records
    original and resized pixel dimensions
  * writes data/provenance_rights.csv and appends to data/run_log.csv
  * never opens, displays or analyses any image; the split in data/splits.json is untouched

Usage: python3 scripts/01_collect.py [--skip-download]
"""
import argparse, csv, hashlib, io, json, re, sys, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
RES = json.load(open(ROOT / "data" / "loc_resources.json"))
UA = "dress-rehearsal-blink-designer/0.1 (research; contact via repository)"
MAX_EDGE = 1568


def slugify(title: str) -> str:
    t = re.sub(r"^\d+-\d+\.\s*", "", title)
    t = re.sub(r"^\d+\.\s*", "", t)
    t = re.sub(r"Historic American Buildings Survey\s*", "", t)
    t = re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")
    return t[:60]


def fetch(url: str, binary=True, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                return data if binary else data.decode("utf-8")
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"fetch failed for {url}: {last}")


def item_rights(resource_url: str) -> dict:
    """Fetch the rights fields shown on this item's own LOC page."""
    url = resource_url + ("&" if "?" in resource_url else "?") + "fo=json&at=item.rights_advisory,item.rights_information,item.title,item.id"
    txt = fetch(url, binary=False)
    return json.loads(txt)


def resize_to(path_in: Path, path_out: Path):
    with Image.open(path_in) as im:
        im.load()
        w, h = im.size
        mode = im.mode
        if mode not in ("RGB", "L"):
            im = im.convert("L" if mode == "1" else "RGB")
        scale = min(1.0, MAX_EDGE / max(w, h))
        if scale < 1.0:
            im = im.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        path_out.parent.mkdir(parents=True, exist_ok=True)
        im.save(path_out, format="PNG", optimize=True)
        return (w, h), im.size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true", help="reuse files already in corpus_a/")
    args = ap.parse_args()
    corpus = ROOT / "corpus_a"
    corpus.mkdir(exist_ok=True)
    rows = []
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    splits = json.load(open(ROOT / "data" / "splits.json"))
    split_of = {}
    for k in ("learning", "iteration", "test"):
        for s in splits[k]:
            split_of[s["sp"]] = k

    items = []
    for s in RES["sheets"]:
        n = s["sp"]
        items.append({
            "kind": "drawing", "sp": n, "title": s["title"],
            "sheet_id": f"hhh.il0039.sheet.{n:05d}",
            "resource_url": f"{RES['sheet_resource_base']}{n}",
            "file_url": RES["sheet_file_patterns"]["master_tif"].format(n=n),
            "ext": "tif", "split": split_of[n], "type_from_title": s["type_from_title"], "origin": "HABS measured drawing (U.S. Government work)",
        })
    for p in RES["photos"]:
        items.append({
            "kind": "photograph", "sp": p["sp"], "title": p["title"],
            "sheet_id": f"hhh.il0039.photos.{p['id']}",
            "resource_url": f"{RES['photo_resource_base']}{p['sp']}",
            "file_url": RES["photo_file_patterns"]["jpeg_1024"].format(id=p["id"]),
            "ext": "jpg", "split": "photograph (corroboration only; not split)", "type_from_title": "photograph", "origin": p["origin"],
        })

    for it in items:
        prefix = "" if it["kind"] == "drawing" else "photo_"
        fname = f"{prefix}{it['sp']:02d}_{slugify(it['title'])}.{it['ext']}"
        raw_path = corpus / fname
        if not raw_path.exists() or not args.skip_download:
            data = fetch(it["file_url"])
            raw_path.write_bytes(data)
            time.sleep(0.5)
        data = raw_path.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        rights = item_rights(it["resource_url"])
        time.sleep(0.5)
        advisory = rights.get("item.rights_advisory") or ""
        info = rights.get("item.rights_information") or ""
        page_title = rights.get("item.title") or ""
        # Decision rule (PRD §1.1): include only if the advisory says no known restrictions AND the item is a
        # U.S. Government image. Photocopies of published plates are "images copied from other sources" → excluded.
        copied_from_other_source = "photocopy" in it["title"].lower()
        if "No known restrictions" in advisory and not copied_from_other_source:
            decision, reason = "include", "U.S. Government image; advisory: no known restrictions"
        elif copied_from_other_source:
            decision, reason = "exclude", "Photocopy of a 1911 published plate: 'images copied from other sources may be restricted' — status unclear, excluded (PRD §1.1)"
        else:
            decision, reason = "exclude", "rights advisory unclear"
        (orig_w, orig_h), (rw, rh) = resize_to(raw_path, corpus / "resized" / (Path(fname).stem + ".png"))
        rows.append({
            "kind": it["kind"], "sp": it["sp"], "sheet_id": it["sheet_id"], "title_catalogue": it["title"],
            "title_on_item_page": page_title, "drawing_type_from_title": it["type_from_title"], "split": it["split"],
            "source_url": it["resource_url"], "file_url": it["file_url"], "file": f"corpus_a/{fname}",
            "resized_file": f"corpus_a/resized/{Path(fname).stem}.png", "sha256": sha, "bytes": len(data),
            "orig_px": f"{orig_w}x{orig_h}", "resized_px": f"{rw}x{rh}",
            "rights_advisory_verbatim": advisory, "rights_information_verbatim": info, "origin": it["origin"],
            "decision": decision, "decision_reason": reason,
            "dimensions_transcribed": "see data/transcriptions/<sheet_id>.json (filled by the transcription pass; test-set sheets only at the held-out check)",
            "collected_at": now,
        })
        print(f"{decision:7s} {it['kind']:10s} sp={it['sp']:2d} {fname}  {orig_w}x{orig_h} -> {rw}x{rh}")

    out = ROOT / "data" / "provenance_rights.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    usable = [r for r in rows if r["kind"] == "drawing" and r["decision"] == "include"]
    print(f"\nusable drawings: {len(usable)} / 25 ; excluded photographs: {sum(1 for r in rows if r['kind']=='photograph' and r['decision']=='exclude')}")
    if len(usable) < 15:
        print("STOP CONDITION: fewer than 15 usable drawings (PRD §1.1)"); sys.exit(2)
    log = ROOT / "data" / "run_log.csv"
    new = not log.exists()
    with open(log, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["timestamp", "stage", "model", "input_tokens", "output_tokens", "notes"])
        w.writerow([now, "01_collect", "none (no model call)", 0, 0, f"{len(rows)} items collected; {len(usable)} usable drawings"])


if __name__ == "__main__":
    main()
