# Metrics (computed by scripts/07_report.py)

**Verdict (PRD §2.4):** PARTIAL PASS — constraint criterion failed (floor effect: both arms 0 violations) — PROVISIONAL: 1 human judge recorded, PRD §6.1 minimum is 2

## Constraint violations (test briefs, PRD §5.4; max 8 per design)

| design | violations |
|---|---|
| test_a/baseline | 0 |
| test_a/learned | 0 |
| test_b/baseline | 0 |
| test_b/learned | 0 |
| test_c/baseline | 0 |
| test_c/learned | 0 |

Mean baseline: 0.00 · mean learned: 0.00 · learned − baseline: +0.00 · pass (≤ −2.0): **False**

## Rule traceability (learned arm, test briefs)

- Major decisions citing a rule: 46/46 = 1.0 (pass ≥ 0.80)
- Citations to real library rules: 272/272 = 1.0 (pass = 1.00)
- Pass: **True**

## Blind test — human judges (PRIMARY)

- Judges: H1
- Accuracy per judge: {'H1': 1.0}
- Mean correct picks of 3: 3.0 (pass ≥ 2)
- Learned picked, share per brief: {'test_a': 1, 'test_b': 1, 'test_c': 1}
- Confidence-weighted score: 1.0 (pass ≥ 0.60)
- Reasons mapping to a real rule: 1/3 (pass ≥ 2 of 3)

## Blind test — claude judges (SUPPLEMENTARY, cannot overturn the human result)

- Judges: CJ1, CJ2, CJ3
- Accuracy per judge: {'CJ1': 1.0, 'CJ2': 1.0, 'CJ3': 1.0}
- Mean correct picks of 3: 3.0 (pass ≥ 2)
- Learned picked, share per brief: {'test_a': 1, 'test_b': 1, 'test_c': 1}
- Confidence-weighted score: 1.0 (pass ≥ 0.60)
- Reasons mapping to a real rule: 9/9 (pass ≥ 2 of 3)

## Held-out drawing check (PRD §6.4)

```json
{
 "share_rules_supported_by_ge1_held_out_drawing": 0.933,
 "share_rules_supported_by_ge2": 0.933,
 "share_rules_contradicted_by_ge1": 0.067,
 "share_rules_net_supported": 0.933,
 "supported_ge1": [
  "R01",
  "R02",
  "R03",
  "R04",
  "R05",
  "R06",
  "R07",
  "R08",
  "R09",
  "R10",
  "R11",
  "R12",
  "R13",
  "R14"
 ],
 "contradicted": [
  "R14"
 ]
}
```
