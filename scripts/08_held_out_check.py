#!/usr/bin/env python3
"""08_held_out_check.py — held-out drawing check (PRD §6.4): are the frozen v2 rules visible in the 7 test-set
drawings that were never used for extraction, iteration or generation?

  --prepare     writes data/held_out_prompts/<sheet_id>.txt (prompts/held_out_check_v1.txt with the frozen library
                embedded) and tiles each test sheet. Model step: one fresh subagent per sheet answers the prompt
                from the sheet's image(s) and writes data/held_out/<sheet_id>.json.
  --summarise   validates the answers and writes outputs/held_out_check.json: per-rule counts of supported /
                contradicted / not_assessable across the 7 drawings, and the share of rules supported by ≥1
                held-out drawing and by ≥2.
Guard: refuses to run unless outputs/rule_library_v2.json exists and outputs/designs/test_*/ specs exist (i.e. the
library is frozen and test generation is done), so the test drawings are opened only at the final evaluation.
"""
import argparse, json, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPLITS = json.load(open(ROOT / "data" / "splits.json"))
TEST = [s["sheet_id"] for s in SPLITS["test"]]


def guard():
    lib = ROOT / "outputs" / "rule_library_v2.json"
    specs = list((ROOT / "outputs" / "designs").glob("test_*/*/spec.json"))
    if not lib.exists() or len(specs) < 6:
        print("Refusing: rule library v2 must be frozen and all 6 test designs generated before any test sheet is opened."); sys.exit(4)
    return json.loads(lib.read_text())


def prepare():
    lib = guard()
    import csv
    prov = {r["sheet_id"]: r for r in csv.DictReader(open(ROOT / "data" / "provenance_rights.csv"))}
    tmpl = (ROOT / "prompts" / "held_out_check_v1.txt").read_text()
    md = (ROOT / "outputs" / "rule_library_v2.md").read_text()
    d = ROOT / "data" / "held_out_prompts"; d.mkdir(exist_ok=True); (ROOT / "data" / "held_out").mkdir(exist_ok=True)
    for sid in TEST:
        (d / f"{sid}.txt").write_text(tmpl.replace("{sheet_id}", sid).replace("{rule_library}", md))
        tif = ROOT / prov[sid]["file"]
        tiles = ROOT / "corpus_a" / "tiles" / tif.stem
        if not (tiles / "index.json").exists():
            subprocess.run([sys.executable, str(ROOT / "scripts" / "tiles.py"), str(tif), "--cols", "4", "--rows", "3"], check=True)
        print("prepared", sid, prov[sid]["file"])


def summarise():
    lib = guard()
    ids = [r["id"] for r in lib["rules"]]
    per_rule = {i: Counter() for i in ids}; per_sheet = {}; dn = defaultdict(Counter)
    for sid in TEST:
        f = ROOT / "data" / "held_out" / f"{sid}.json"
        if not f.exists(): print("MISSING", f); continue
        a = json.loads(f.read_text())
        assert a["sheet_id"] == sid
        per_sheet[sid] = {r["id"]: r["verdict"] for r in a["rules"]}
        for r in a["rules"]:
            if r["id"] in per_rule: per_rule[r["id"]][r["verdict"]] += 1
        for d_ in a.get("do_not_list", []): dn[d_["index"]][d_["verdict"]] += 1
    supported_ge1 = [i for i in ids if per_rule[i]["supported"] >= 1]
    supported_ge2 = [i for i in ids if per_rule[i]["supported"] >= 2]
    contradicted = [i for i in ids if per_rule[i]["contradicted"] >= 1]
    net_supported = [i for i in ids if per_rule[i]["supported"] > per_rule[i]["contradicted"]]
    out = {"sheets_checked": len(per_sheet), "rules": len(ids),
           "summary": {"share_rules_supported_by_ge1_held_out_drawing": round(len(supported_ge1) / len(ids), 3),
                       "share_rules_supported_by_ge2": round(len(supported_ge2) / len(ids), 3),
                       "share_rules_contradicted_by_ge1": round(len(contradicted) / len(ids), 3),
                       "share_rules_net_supported": round(len(net_supported) / len(ids), 3),
                       "supported_ge1": supported_ge1, "contradicted": contradicted},
           "per_rule": {i: dict(c) for i, c in per_rule.items()}, "do_not_list": {k: dict(v) for k, v in dn.items()}, "per_sheet": per_sheet}
    (ROOT / "outputs" / "held_out_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out["summary"], indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--prepare", action="store_true"); ap.add_argument("--summarise", action="store_true")
    a = ap.parse_args()
    if a.prepare: prepare()
    if a.summarise: summarise()
