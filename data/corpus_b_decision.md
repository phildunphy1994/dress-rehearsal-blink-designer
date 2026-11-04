# Corpus B (Structured3D, Hugging Face compressed copy) — decision: SKIPPED

Recorded 2026-11-04 (T0 + ~1 h).

- At T0 the session's network policy denied `huggingface.co` outright (CONNECT 403 from the egress proxy), so
  the dataset page could not even be opened from the session. The user later opened all hosts, but the dataset is
  **access-gated**: it requires a logged-in Hugging Face account to accept the Structured3D terms of use
  (non-commercial research only, no redistribution, citation required, governed by PRC law). No Hugging Face
  credentials exist in this session, and the PRD forbids depending on this approval (§1.2: "If access is not granted
  within 2 hours of starting, skip Corpus B entirely").
- Consequence (PRD §3.2): the **contrast pass was not run**. The rule library is therefore untested against a
  generic control set; `generic_rules_removed` is empty and the run report says so. Generic-practice rules were
  instead screened by the aggregation prompt's own rule ("a rule that could describe any well-designed room is not a
  rule for this library") and by the executor's audit of each rule against its cited sheets.
- `data/corpus_b_subset.csv` is left with a header only.
