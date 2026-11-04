#!/usr/bin/env python3
"""09_merge_human_judges.py — merge human judge submissions (exported from the judging page's database as JSON)
into outputs/blind_test_scores.csv, then recompute metrics.

Input: data/human_submissions.json — a list of submission documents of the form written by the judging page:
  {"name": "...", "seen_rules": "no"|"yes", "answers": {"test_a": {"picked": "A"|"B", "confidence": 1-5, "reason": "..."}, ...},
   "submitted_at": "...", "judge_type": "human"}
(or a dict mapping doc id → document). Each judge gets judge_id H1, H2, … in submission order; `correct` is computed
from outputs/blind/KEY.json; `reason_maps_to_rule_id_or_null` is left empty for the orchestrator to fill by reading
each reason against the rule library (then re-run scripts/07_report.py). Existing human rows are not duplicated
(matched on judge name + brief). The first score stands (PRD §6.5): a second submission by the same judge is ignored.
"""
import csv, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(path="data/human_submissions.json"):
    raw = json.loads((ROOT / path).read_text())
    subs = list(raw.values()) if isinstance(raw, dict) else raw
    subs = sorted(subs, key=lambda d: d.get("submitted_at", ""))
    key = json.loads((ROOT / "outputs" / "blind" / "KEY.json").read_text())
    scores = ROOT / "outputs" / "blind_test_scores.csv"
    rows = list(csv.DictReader(open(scores)))
    seen = {(r["judge_id"], r["brief"]) for r in rows}
    names = {}
    added = 0
    for d in subs:
        name = d.get("name", "").strip() or "anonymous"
        if name not in names: names[name] = f"H{len(names) + 1}"
        jid = names[name]
        for brief, a in d["answers"].items():
            if (jid, brief) in seen: continue
            correct = int(key["briefs"][brief][a["picked"]] == "learned")
            rows.append({"judge_id": jid, "judge_type": "human", "brief": brief, "picked": a["picked"], "correct": correct,
                         "confidence": a["confidence"], "reason": a["reason"].replace("\n", " "), "reason_maps_to_rule_id_or_null": ""})
            seen.add((jid, brief)); added += 1
    with open(scores, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["judge_id", "judge_type", "brief", "picked", "correct", "confidence", "reason", "reason_maps_to_rule_id_or_null"])
        w.writeheader(); w.writerows(rows)
    independence = {names[d.get("name", "").strip() or "anonymous"]: d.get("seen_rules") for d in subs}
    (ROOT / "outputs" / "human_judges.json").write_text(json.dumps({"judge_ids": names, "seen_rules_or_specs_before": independence}, indent=1))
    print(f"added {added} human rows for judges {names}; independence: {independence}")
    print("next: fill reason_maps_to_rule_id_or_null for the human rows, then run python3 scripts/07_report.py")


if __name__ == "__main__":
    main(*sys.argv[1:])
