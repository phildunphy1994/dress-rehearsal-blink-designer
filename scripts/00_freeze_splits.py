#!/usr/bin/env python3
"""Freeze the Corpus A learning / iteration / test split BEFORE any drawing is opened (PRD §1.1, §2.3).

Inputs : data/loc_resources.json (sheet numbers and catalogue titles only — no image content is used)
Output : data/splits.json

Procedure (deterministic, pre-registered):
  1. Sheets are grouped into CONTENT GROUPS so that the two HABS drawing sets that document the same
     subject (e.g. "1-2 First floor plan" and "3-1 First floor plan") always land in the same split.
     Otherwise a test-set drawing could be a near-duplicate of a learning-set drawing and the held-out
     check (PRD §6.4) would be inflated. Grouping uses catalogue titles only.
  2. Groups are stratified by drawing type (plans / elevations+sections / details / furniture / title).
  3. Within each stratum the groups are shuffled with a fixed seed, then assigned greedily to the split
     with the largest remaining deficit against the target sheet counts (12 / 6 / 7).
Re-running this script with the same inputs reproduces the same split. The split is frozen once
written; the script refuses to overwrite an existing data/splits.json unless --force is given.
"""
import argparse, json, random, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261104
TARGETS = {"learning": 12, "iteration": 6, "test": 7}

# Content groups (sheet numbers = ?sp= values). Built from catalogue titles only.
GROUPS = {
    "G01_title_location_plan": [1],
    "G02_first_floor_plans": [2, 16],
    "G03_second_main_floor_plans": [3, 17],
    "G04_third_floor_plans": [4, 18],
    "G05_south_elevation_long_section": [5, 19],
    "G06_north_east_west_elevations": [6, 20, 21],
    "G07_section_3_7": [22],
    "G08_section_3_8": [23],
    "G09_fireplace_elevations": [7],
    "G10_first_floor_window_pattern_second_floor_window_details": [8],
    "G11_main_floor_windows": [9],
    "G12_living_room_environmental_provisions": [10],
    "G13_front_detail": [24],
    "G14_window_detail": [25],
    "G15_furniture_dresser_headboard_footboard": [11],
    "G16_furniture_lr_chair_stool_dr_chair_andirons": [12],
    "G17_furniture_straight_back_chair": [13],
    "G18_furniture_side_chair": [14],
    "G19_dining_table_corner_post_ends": [15],
}
STRATA = [
    ("plans", ["G02_first_floor_plans", "G03_second_main_floor_plans", "G04_third_floor_plans"]),
    ("elevations_sections", ["G05_south_elevation_long_section", "G06_north_east_west_elevations", "G07_section_3_7", "G08_section_3_8"]),
    ("details", ["G09_fireplace_elevations", "G10_first_floor_window_pattern_second_floor_window_details", "G11_main_floor_windows",
                 "G12_living_room_environmental_provisions", "G13_front_detail", "G14_window_detail"]),
    ("furniture", ["G15_furniture_dresser_headboard_footboard", "G16_furniture_lr_chair_stool_dr_chair_andirons",
                   "G17_furniture_straight_back_chair", "G18_furniture_side_chair", "G19_dining_table_corner_post_ends"]),
    ("title", ["G01_title_location_plan"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    out = ROOT / "data" / "splits.json"
    if out.exists() and not args.force:
        print(f"REFUSING to overwrite frozen split at {out}. Use --force only for a new, labelled experiment.")
        sys.exit(1)
    res = json.load(open(ROOT / "data" / "loc_resources.json"))
    titles = {s["sp"]: s["title"] for s in res["sheets"]}
    assert sorted(n for g in GROUPS.values() for n in g) == list(range(1, 26)), "groups must cover sheets 1..25 exactly once"

    rng = random.Random(SEED)
    assign = {k: [] for k in TARGETS}
    order_log = []
    for stratum, groups in STRATA:
        groups = list(groups)
        rng.shuffle(groups)
        for g in groups:
            deficits = {k: (TARGETS[k] - len(assign[k])) / TARGETS[k] for k in TARGETS}
            target = max(deficits, key=lambda k: (deficits[k], -["learning", "iteration", "test"].index(k)))
            assign[target].extend(GROUPS[g])
            order_log.append({"stratum": stratum, "group": g, "sheets": GROUPS[g], "assigned_to": target})
    for k in assign:
        assign[k].sort()
    sheet_id = lambda n: f"hhh.il0039.sheet.{n:05d}"
    splits = {
        "frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "frozen_before_any_drawing_was_opened": True,
        "seed": SEED,
        "targets": TARGETS,
        "actual_counts": {k: len(v) for k, v in assign.items()},
        "procedure": __doc__.strip(),
        "groups": GROUPS,
        "assignment_order": order_log,
        "learning": [{"sp": n, "sheet_id": sheet_id(n), "title": titles[n]} for n in assign["learning"]],
        "iteration": [{"sp": n, "sheet_id": sheet_id(n), "title": titles[n]} for n in assign["iteration"]],
        "test": [{"sp": n, "sheet_id": sheet_id(n), "title": titles[n]} for n in assign["test"]],
        "photographs": "Not split. Photographs are corroboration only (PRD §1.1); the three 1911 Wasmuth photocopies are excluded on rights grounds (see data/provenance_rights.csv).",
        "leakage_rule": "No test-set sheet may be opened, transcribed, extracted or otherwise used before the final evaluation (PRD §2.3). Violations are recorded as leakage and the evaluation is discarded.",
    }
    json.dump(splits, open(out, "w"), indent=2)
    print(json.dumps({k: assign[k] for k in assign}, indent=0))
    print("counts", splits["actual_counts"])


if __name__ == "__main__":
    main()
