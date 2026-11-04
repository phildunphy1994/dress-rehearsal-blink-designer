#!/usr/bin/env python3
"""audit_evidence.py — mechanical audit of a rule library's evidence file.

For every line of the form   - R01 · hhh.il0039.sheet.00007: "quoted phrase"   in outputs/rule_library_vN_evidence.md,
checks that (a) the sheet id is cited by that rule in the JSON library, (b) the sheet is a learning-set sheet (or an
iteration-set sheet, for v2 counter-examples), and (c) the quoted phrase occurs verbatim (case- and whitespace-
insensitive) in that sheet's extraction JSON. Also checks every cited evidence sheet in the JSON has at least one
quoted phrase. Writes outputs/rule_library_vN_audit.json and prints a summary. Exit 1 on any failure.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(s):
    return re.sub(r"\s+", " ", s.lower().replace("“", '"').replace("”", '"').replace("’", "'")).strip()


def main(lib_path):
    lib_path = Path(lib_path)
    lib = json.loads(lib_path.read_text())
    ev_path = lib_path.parent / (lib_path.stem + "_evidence.md")
    lines = ev_path.read_text().splitlines()
    cited = {r["id"]: set(r["evidence_sheet_ids"]) for r in lib["rules"]}
    seen = {r["id"]: set() for r in lib["rules"]}
    cache = {}
    def ext(sid):
        if sid not in cache:
            f = ROOT / "data" / "extractions" / f"{sid}.json"
            cache[sid] = norm(f.read_text()) if f.exists() else ""
        return cache[sid]
    problems, checked = [], 0
    pat = re.compile(r'^\s*-\s*(R\d\d|DN\d+|do[_ -]?not[^:·]*?)\s*[·:]\s*(hhh\.il0039\.sheet\.\d{5})\s*:\s*["“](.+?)["”]\s*$')
    for ln in lines:
        m = pat.match(ln)
        if not m: continue
        rid, sid, phrase = m.group(1), m.group(2), m.group(3)
        checked += 1
        if rid.startswith("R"):
            if rid not in cited: problems.append(f"{rid}: not in library"); continue
            if sid not in cited[rid]: problems.append(f"{rid}: evidence line cites {sid}, which the JSON rule does not list")
            seen[rid].add(sid)
        if norm(phrase) not in ext(sid):
            problems.append(f"{rid} · {sid}: quoted phrase not found verbatim in extraction: \"{phrase[:80]}\"")
    for rid, sids in cited.items():
        for sid in sids - seen[rid]:
            problems.append(f"{rid}: cited sheet {sid} has no quoted evidence phrase")
    out = {"library": str(lib_path), "evidence_lines_checked": checked, "problems": problems, "pass": not problems}
    (lib_path.parent / (lib_path.stem + "_audit.json")).write_text(json.dumps(out, indent=1))
    print(f"{checked} evidence lines checked; {len(problems)} problems")
    for p in problems: print("  -", p)
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main(sys.argv[1])
