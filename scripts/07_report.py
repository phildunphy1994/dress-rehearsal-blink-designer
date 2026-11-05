#!/usr/bin/env python3
"""07_report.py — compute the pre-registered metrics (PRD §2.4, §6.3, §6.4) from the recorded outputs and write
outputs/metrics.json + outputs/metrics.md. The narrative run report and discussion pack cite these numbers; they are
never edited by hand here.

Inputs (all produced earlier in the pipeline):
  outputs/violations.csv            (05_svg.py check-all, test phase)
  outputs/traceability_test.csv     (04_generate.py --validate --phase test)
  outputs/blind_test_scores.csv     (judges; judge_type = human | claude)
  outputs/blind/KEY.json            (A/B key, for 'correct')
  outputs/held_out_check.json       (held-out drawing check, PRD §6.4)
  outputs/rule_library_v2.json
"""
import csv, json, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def read_csv(p):
    return list(csv.DictReader(open(p))) if p.exists() else []


def main():
    m = {}
    # --- constraint violations (test briefs)
    v = read_csv(OUT / "violations.csv")
    per_design = defaultdict(int); briefs = set()
    for r in v:
        briefs.add(r["brief"]); per_design[(r["brief"], r["arm"])] += int(r["violated"])
    arms = {"baseline": [], "learned": []}
    for (b, a), n in per_design.items(): arms[a].append(n)
    m["violations"] = {"per_design": {f"{b}/{a}": n for (b, a), n in sorted(per_design.items())},
                       "mean_baseline": statistics.mean(arms["baseline"]) if arms["baseline"] else None,
                       "mean_learned": statistics.mean(arms["learned"]) if arms["learned"] else None}
    if arms["baseline"] and arms["learned"]:
        m["violations"]["learned_minus_baseline"] = m["violations"]["mean_learned"] - m["violations"]["mean_baseline"]
        m["violations"]["pass"] = m["violations"]["learned_minus_baseline"] <= -2.0
    # --- traceability
    t = read_csv(OUT / "traceability_test.csv")
    learned = [r for r in t if r["arm"] == "learned" and r["status"] == "valid"]
    if learned:
        maj = sum(int(r["major_decisions"]) for r in learned); cit = sum(int(r["major_citing_rule"]) for r in learned)
        allc = sum(int(r["rule_citations"]) for r in learned); real = sum(int(r["citations_to_real_rules"]) for r in learned)
        m["traceability"] = {"major_decisions": maj, "major_citing_rule": cit, "share_major_cited": round(cit / maj, 3) if maj else None,
                             "citations": allc, "citations_to_real_rules": real, "share_real": round(real / allc, 3) if allc else None,
                             "pass": (maj > 0 and cit / maj >= 0.8) and (allc > 0 and real == allc)}
    # --- blind test
    key = json.loads((OUT / "blind" / "KEY.json").read_text()) if (OUT / "blind" / "KEY.json").exists() else None
    s = read_csv(OUT / "blind_test_scores.csv")
    lib = json.loads((OUT / "rule_library_v2.json").read_text()) if (OUT / "rule_library_v2.json").exists() else None
    rule_ids = {r["id"] for r in lib["rules"]} if lib else set()
    blind = {}
    for jtype in ("human", "claude"):
        rows = [r for r in s if r["judge_type"] == jtype]
        if not rows: continue
        by_judge = defaultdict(list)
        for r in rows:
            correct = int(r["correct"]) if r["correct"] not in ("", None) else int(key["briefs"][r["brief"]][r["picked"]] == "learned")
            by_judge[r["judge_id"]].append((r["brief"], correct, int(r["confidence"]), r["reason_maps_to_rule_id_or_null"]))
        acc = {j: sum(c for _, c, _, _ in L) / len(L) for j, L in by_judge.items()}
        n_briefs = len({r["brief"] for r in rows})
        picks_learned_per_brief = {b: statistics.mean([c for j, L in by_judge.items() for bb, c, _, _ in L if bb == b]) for b in {r["brief"] for r in rows}}
        cw = sum(c * conf for L in by_judge.values() for _, c, conf, _ in L) / max(1, sum(conf for L in by_judge.values() for _, _, conf, _ in L))
        reasons_real = sum(1 for L in by_judge.values() for _, _, _, rid in L if rid and rid.strip().upper() in rule_ids)
        n_reasons = sum(len(L) for L in by_judge.values())
        mean_correct_briefs = statistics.mean(acc.values()) * n_briefs if acc else None
        blind[jtype] = {"judges": sorted(by_judge), "accuracy_per_judge": acc, "mean_correct_of_3": round(mean_correct_briefs, 2) if mean_correct_briefs is not None else None,
                        "learned_picked_share_per_brief": picks_learned_per_brief, "confidence_weighted": round(cw, 3),
                        "reasons_mapping_to_real_rule": f"{reasons_real}/{n_reasons}",
                        "pass_identification": mean_correct_briefs is not None and mean_correct_briefs >= 2.0,
                        "pass_confidence_weighted": cw >= 0.60, "pass_reason_quality": reasons_real >= 2}
    m["blind"] = blind
    # --- held-out drawing check
    ho = OUT / "held_out_check.json"
    if ho.exists():
        h = json.loads(ho.read_text()); m["held_out"] = h.get("summary", h)
    # --- verdict (PRD §2.4): constraint criterion + HUMAN blind criterion. Claude judges are supplementary only.
    cpass = m.get("violations", {}).get("pass")
    hb = blind.get("human")
    bpass = hb["pass_identification"] if hb else None
    if cpass is None or bpass is None:
        if cpass is False and bpass is None:
            verdict = "PARTIAL PASS AT BEST — constraint criterion failed (floor effect: both arms 0 violations); human blind test not yet recorded"
        else:
            verdict = "INCOMPLETE — " + ("constraint metric missing; " if cpass is None else "") + ("human blind test not yet recorded; " if bpass is None else "")
        if bpass is None and blind.get("claude"):
            verdict += f"; supplementary Claude-judge identification {'passes' if blind['claude']['pass_identification'] else 'fails'} (cannot substitute for the human result)"
    elif cpass and bpass: verdict = "PASS"
    elif cpass or bpass: verdict = "PARTIAL PASS — " + ("blind criterion failed" if cpass else "constraint criterion failed (floor effect: both arms 0 violations)")
    else: verdict = "FAIL"
    if hb and len(hb["judges"]) < 2:
        verdict += f" — PROVISIONAL: {len(hb['judges'])} human judge recorded, PRD §6.1 minimum is 2"
    m["verdict"] = verdict
    (OUT / "metrics.json").write_text(json.dumps(m, indent=1))
    # markdown
    L = ["# Metrics (computed by scripts/07_report.py)", "", f"**Verdict (PRD §2.4):** {verdict}", ""]
    if "violations" in m and m["violations"]["mean_baseline"] is not None:
        L += ["## Constraint violations (test briefs, PRD §5.4; max 8 per design)", "", "| design | violations |", "|---|---|"]
        L += [f"| {k} | {n} |" for k, n in m["violations"]["per_design"].items()]
        L += ["", f"Mean baseline: {m['violations']['mean_baseline']:.2f} · mean learned: {m['violations']['mean_learned']:.2f} · learned − baseline: {m['violations']['learned_minus_baseline']:+.2f} · pass (≤ −2.0): **{m['violations']['pass']}**", ""]
    if "traceability" in m:
        tr = m["traceability"]
        L += ["## Rule traceability (learned arm, test briefs)", "", f"- Major decisions citing a rule: {tr['major_citing_rule']}/{tr['major_decisions']} = {tr['share_major_cited']} (pass ≥ 0.80)",
              f"- Citations to real library rules: {tr['citations_to_real_rules']}/{tr['citations']} = {tr['share_real']} (pass = 1.00)", f"- Pass: **{tr['pass']}**", ""]
    for jtype, b in blind.items():
        L += [f"## Blind test — {jtype} judges ({'PRIMARY' if jtype == 'human' else 'SUPPLEMENTARY, cannot overturn the human result'})", "",
              f"- Judges: {', '.join(b['judges'])}", f"- Accuracy per judge: {b['accuracy_per_judge']}", f"- Mean correct picks of 3: {b['mean_correct_of_3']} (pass ≥ 2)",
              f"- Learned picked, share per brief: {b['learned_picked_share_per_brief']}", f"- Confidence-weighted score: {b['confidence_weighted']} (pass ≥ 0.60)",
              f"- Reasons mapping to a real rule: {b['reasons_mapping_to_real_rule']} (pass ≥ 2 of 3)", ""]
    if "held_out" in m:
        L += ["## Held-out drawing check (PRD §6.4)", "", "```json", json.dumps(m["held_out"], indent=1), "```", ""]
    (OUT / "metrics.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
