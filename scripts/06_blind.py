#!/usr/bin/env python3
"""06_blind.py — build the blind judge pack for the TEST briefs (PRD §6.1).

For each test brief: a recorded coin flip assigns the baseline and learned diagram sets to "Set A" / "Set B";
the three SVGs (plan, elevation, palette) are copied with filenames and metadata stripped and rasterised to PNG;
the written specs are NOT included. The pack shows: the judge task verbatim (prompts/judge_v1.txt), a one-line
style description derived only from the rule library's signature moves (no designer or project names), the brief
text, and the two diagram sets. The A/B key is written to outputs/blind/KEY.json — judges must not see it.

Usage: python3 scripts/06_blind.py --library outputs/rule_library_v2.json --seed 20261106
"""
import argparse, json, random, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = json.load(open(ROOT / "briefs" / "briefs.json"))["briefs"]


def strip_svg(txt: str) -> str:
    txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)
    txt = re.sub(r"<metadata>.*?</metadata>", "", txt, flags=re.S)
    txt = re.sub(r"(?i)baseline|learned|rule library|R\d\d\b", "", txt)   # belt and braces; the renderer never writes these
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--library", default="outputs/rule_library_v2.json")
    ap.add_argument("--seed", type=int, required=True, help="recorded seed for the per-brief coin flips")
    ap.add_argument("--style-line", default=None, help="override the auto-derived one-line style description")
    a = ap.parse_args()
    lib = json.loads((ROOT / a.library).read_text())
    rng = random.Random(a.seed)
    blind = ROOT / "outputs" / "blind"
    if blind.exists():
        print("outputs/blind already exists — refusing to rebuild (PRD §6.5: no re-judging). Delete it manually only for a new labelled experiment."); sys.exit(1)
    blind.mkdir(parents=True)
    style = a.style_line or ("A body of work whose signature moves are: " + "; ".join(m.rstrip(".") for m in lib["signature_moves"]) + ".")
    style = re.sub(r"(?i)frank\s+lloyd\s+wright|wright|robie|prairie|habs|chicago", "[withheld]", style)
    key = {"built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "seed": a.seed, "style_line": style, "briefs": {}}
    pack = ["# Blind judge pack — TEST briefs", "", "## Judge task (verbatim)", "",
            (ROOT / "prompts" / "judge_v1.txt").read_text().replace("{style_line}", style), "",
            "Record one CSV row per pair: `brief,picked,confidence,reason` (picked = A or B; confidence 1–5; reason in quotes).", ""]
    for bid, b in BRIEFS.items():
        if b["phase"] != "test": continue
        flip = rng.random()
        a_arm, b_arm = ("learned", "baseline") if flip < 0.5 else ("baseline", "learned")
        key["briefs"][bid] = {"coin": round(flip, 6), "A": a_arm, "B": b_arm}
        pack += [f"## Pair — {bid}", "", "### Brief", "", (ROOT / "briefs" / f"{bid}.md").read_text(), ""]
        for letter, arm in (("A", a_arm), ("B", b_arm)):
            src = ROOT / "outputs" / "designs" / bid / arm
            dst = blind / bid / f"set_{letter}"; dst.mkdir(parents=True)
            svgs = []
            for name in ("plan", "elevation", "palette"):
                s = src / f"{name}.svg"
                if not s.exists(): print("MISSING", s); sys.exit(1)
                (dst / f"{name}.svg").write_text(strip_svg(s.read_text())); svgs.append(str(dst / f"{name}.svg"))
            subprocess.run(["node", str(ROOT / "scripts" / "svg2png.js"), str(dst)] + svgs, check=True, capture_output=True)
            pack += [f"### Set {letter}", "", f"![plan]({bid}/set_{letter}/plan.png)", "", f"![elevation]({bid}/set_{letter}/elevation.png)", "", f"![palette]({bid}/set_{letter}/palette.png)", ""]
    (blind / "judge_pack.md").write_text("\n".join(pack))
    (blind / "KEY.json").write_text(json.dumps(key, indent=1))
    scores = ROOT / "outputs" / "blind_test_scores.csv"
    if not scores.exists():
        scores.write_text("judge_id,judge_type,brief,picked,correct,confidence,reason,reason_maps_to_rule_id_or_null\n")
    print("wrote", blind / "judge_pack.md", "and", blind / "KEY.json", "(do not show the key to judges)")
    print(json.dumps(key["briefs"], indent=1))


if __name__ == "__main__":
    main()
