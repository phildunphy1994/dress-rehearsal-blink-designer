#!/usr/bin/env python3
"""tiles.py — cut a master drawing into full-resolution tiles so small lettering (dimensions, notes)
is legible to a vision model. Used only by the transcription pre-step; the PRD extraction call itself
receives the single 1568-px resized sheet (PRD §7.2).

Usage: python3 scripts/tiles.py corpus_a/07_fireplace_elevations.tif --cols 4 --rows 3 [--out DIR]
Writes DIR/r{row}c{col}.png (each ≤1568 px on the longest edge, 8% overlap) and DIR/index.json.
"""
import argparse, json
from pathlib import Path
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
MAX_EDGE = 1568


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tif")
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--rows", type=int, default=3)
    ap.add_argument("--overlap", type=float, default=0.08)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    src = Path(a.tif)
    out = Path(a.out) if a.out else src.parent / "tiles" / src.stem
    out.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im.load()
        if im.mode not in ("RGB", "L"):
            im = im.convert("L" if im.mode == "1" else "RGB")
        W, H = im.size
        tw, th = W / a.cols, H / a.rows
        ox, oy = tw * a.overlap, th * a.overlap
        index = {"source": str(src), "size": [W, H], "cols": a.cols, "rows": a.rows, "tiles": []}
        for r in range(a.rows):
            for c in range(a.cols):
                x0 = max(0, int(c * tw - ox)); y0 = max(0, int(r * th - oy))
                x1 = min(W, int((c + 1) * tw + ox)); y1 = min(H, int((r + 1) * th + oy))
                tile = im.crop((x0, y0, x1, y1))
                s = min(1.0, MAX_EDGE / max(tile.size))
                if s < 1.0:
                    tile = tile.resize((round(tile.size[0] * s), round(tile.size[1] * s)), Image.LANCZOS)
                name = f"r{r}c{c}.png"
                tile.save(out / name, optimize=True)
                index["tiles"].append({"file": name, "box_px": [x0, y0, x1, y1], "scale": round(s, 3)})
        json.dump(index, open(out / "index.json", "w"), indent=1)
    print(f"wrote {a.rows*a.cols} tiles to {out}")


if __name__ == "__main__":
    main()
