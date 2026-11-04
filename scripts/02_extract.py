#!/usr/bin/env python3
"""02_extract.py — prepare and validate the per-drawing extraction stage (PRD §3.1).

The model step is run IN-SESSION by the session model (Fable) — no API key, no SDK — one drawing per
request, using prompts/transcribe_v1.txt then prompts/extract_v1.txt verbatim. This script:

  --prepare   writes the exact prompt text for each sheet to data/extraction_prompts/<sheet_id>.{transcribe,extract}.txt
              (the extract prompt is finalised after the transcription exists) and tiles each sheet for legibility
  --validate  validates data/transcriptions/<sheet_id>.json and data/extractions/<sheet_id>.json against the schemas,
              enforces the leakage guard (no test-set sheet may have an extraction before the held-out phase),
              and writes data/extraction_validation.json
  --phase     'learning', 'iteration' or 'test' (test only allowed with --held-out-check)

Retry policy (PRD §3.1): a response that fails validation is retried once; a second failure is flagged for manual
review in data/extraction_validation.json and must not be silently repaired.
"""
import argparse, csv, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SPLITS = json.load(open(ROOT / "data" / "splits.json"))
PROV = {r["sheet_id"]: r for r in csv.DictReader(open(ROOT / "data" / "provenance_rights.csv"))}
T_SCHEMA = json.load(open(ROOT / "schema" / "transcription_schema.json"))
E_SCHEMA = json.load(open(ROOT / "schema" / "extraction_schema.json"))


ONLY_SHEET = None


def sheets_in(phase, apply_filter=True):
    ids = [s["sheet_id"] for s in SPLITS[phase]]
    if ONLY_SHEET and apply_filter:
        assert ONLY_SHEET in ids, f"{ONLY_SHEET} is not in the {phase} set"
        ids = [ONLY_SHEET]
    return ids


def prepare(phase):
    pdir = ROOT / "data" / "extraction_prompts"; pdir.mkdir(exist_ok=True)
    t_tmpl = open(ROOT / "prompts" / "transcribe_v1.txt").read()
    e_tmpl = open(ROOT / "prompts" / "extract_v1.txt").read()
    for sid in sheets_in(phase):
        row = PROV[sid]
        (pdir / f"{sid}.transcribe.txt").write_text(t_tmpl.replace("{sheet_id}", sid))
        tpath = ROOT / "data" / "transcriptions" / f"{sid}.json"
        trans = tpath.read_text() if tpath.exists() else "(transcription not yet available — run the transcription pass first)"
        (pdir / f"{sid}.extract.txt").write_text(e_tmpl.replace("{sheet_id}", sid).replace("{transcribed_dimensions}", trans))
        tif = ROOT / row["file"]
        tiles = ROOT / "corpus_a" / "tiles" / tif.stem
        if not (tiles / "index.json").exists():
            subprocess.run([sys.executable, str(ROOT / "scripts" / "tiles.py"), str(tif), "--cols", "4", "--rows", "3"], check=True)
        print("prepared", sid, row["file"])


def validate(phase, held_out_check=False):
    report = {"validated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "phase": phase, "sheets": {}}
    # Leakage guard
    test_ids = set(sheets_in("test", apply_filter=False))
    for d in ("transcriptions", "extractions"):
        for f in (ROOT / "data" / d).glob("*.json"):
            if f.name.endswith(".meta.json"):
                continue
            if f.stem in test_ids and not held_out_check:
                report.setdefault("LEAKAGE", []).append(f"{d}/{f.name} exists for a TEST-set sheet before the held-out phase")
    ok_all = True
    for sid in sheets_in(phase):
        entry = {"transcription": "missing", "extraction": "missing", "errors": []}
        for kind, schema in (("transcriptions", T_SCHEMA), ("extractions", E_SCHEMA)):
            f = ROOT / "data" / kind / f"{sid}.json"
            key = kind[:-1]
            if not f.exists():
                continue
            try:
                obj = json.loads(f.read_text())
                jsonschema.validate(obj, schema)
                if obj.get("sheet_id") != sid:
                    raise ValueError(f"sheet_id mismatch: {obj.get('sheet_id')} != {sid}")
                entry[key] = "valid"
            except Exception as e:  # noqa
                entry[key] = "INVALID"
                entry["errors"].append(f"{key}: {str(e)[:300]}")
                ok_all = False
        meta = ROOT / "data" / "extractions" / f"{sid}.meta.json"
        if meta.exists():
            m = json.loads(meta.read_text())
            entry["attempts"] = m.get("attempts"); entry["model"] = m.get("model"); entry["flagged_for_manual_review"] = m.get("flagged_for_manual_review", False)
        report["sheets"][sid] = entry
    (ROOT / "data" / "extraction_validation.json").write_text(json.dumps(report, indent=1))
    for sid, e in report["sheets"].items():
        print(f"{sid}: transcription={e['transcription']} extraction={e['extraction']} {'; '.join(e['errors'])}")
    if "LEAKAGE" in report:
        print("LEAKAGE DETECTED:", report["LEAKAGE"]); sys.exit(3)
    return ok_all


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["learning", "iteration", "test"], required=True)
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--held-out-check", action="store_true")
    ap.add_argument("--sheet", default=None, help="limit to one sheet_id, e.g. hhh.il0039.sheet.00007")
    a = ap.parse_args()
    ONLY_SHEET = a.sheet
    if a.phase == "test" and not a.held_out_check:
        print("Refusing: test-set sheets may only be processed with --held-out-check at the final evaluation."); sys.exit(4)
    (ROOT / "data" / "transcriptions").mkdir(exist_ok=True)
    (ROOT / "data" / "extractions").mkdir(exist_ok=True)
    if a.prepare:
        prepare(a.phase)
    if a.validate:
        sys.exit(0 if validate(a.phase, a.held_out_check) else 1)
