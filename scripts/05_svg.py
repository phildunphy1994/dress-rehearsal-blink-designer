#!/usr/bin/env python3
"""05_svg.py — render plan / elevation / palette SVGs from spec.json and run the PRD §5.4 violation checklist.

Standard library only (no svgwrite). Both arms use this identical code path. The renderer never prints the
arm name or rule ids on a drawing, so SVGs are safe for the blind judge pack.

Usage:
  python3 scripts/05_svg.py render  outputs/designs/test_a/learned/spec.json
  python3 scripts/05_svg.py check   outputs/designs/test_a/learned/spec.json [--append-csv]
  python3 scripts/05_svg.py check-all                      # every outputs/designs/*/*/spec.json → outputs/violations.csv
"""
import argparse, csv, json, math, re, sys
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
S = 100.0  # px per metre (1 m = 100 px). Scale bar drawn on every plan.
BRIEFS = json.load(open(ROOT / "briefs" / "briefs.json"))["briefs"]
SPEC_SCHEMA = json.load(open(ROOT / "schema" / "spec_schema.json"))

FONT = "font-family='Helvetica, Arial, sans-serif'"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def f2(x):
    return f"{x:.2f}"


# ----------------------------------------------------------------------------- geometry helpers
def wall_len(room, wall):
    return room["length_m"] if wall in ("north", "south") else room["width_m"]


def opening_span(room, op):
    """Return the opening as a segment in room coordinates: (x0,y0,x1,y1) along its wall, plus the inward normal."""
    L, W = room["length_m"], room["width_m"]
    o, w = op["offset_m"], op["width_m"]
    if op["wall"] == "north":   # left end = west
        return (o, W, o + w, W), (0, -1)
    if op["wall"] == "south":   # left end = east
        return (L - o - w, 0, L - o, 0), (0, 1)
    if op["wall"] == "west":    # left end = south
        return (0, o, 0, o + w), (1, 0)
    return (L, W - o - w, L, W - o), (-1, 0)   # east: left end = north


def opening_centre(room, op):
    (x0, y0, x1, y1), n = opening_span(room, op)
    return ((x0 + x1) / 2, (y0 + y1) / 2), n


def furn_rect(f):
    return (f["x_m"], f["y_m"], f["x_m"] + f["length_m"], f["y_m"] + f["depth_m"])


def rect_overlap_area(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0])
    dy = min(a[3], b[3]) - max(a[1], b[1])
    return dx * dy if dx > 0 and dy > 0 else 0.0


def point_rect_dist(px, py, r):
    dx = max(r[0] - px, 0, px - r[2])
    dy = max(r[1] - py, 0, py - r[3])
    return math.hypot(dx, dy)


def seg_points(p, q, step=0.05):
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(1, int(d / step))
    return [(p[0] + (q[0] - p[0]) * i / n, p[1] + (q[1] - p[1]) * i / n) for i in range(n + 1)]


def poly_area(poly):
    a = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def solid(f):
    return not f.get("allow_overlap", False) and not ({"rug", "lighting"} & set(f["functions"]))


def swing_rect(room, op):
    """Square of side width_m inside the room in front of a door (conservative swing/clearance zone)."""
    (x0, y0, x1, y1), (nx, ny) = opening_span(room, op)
    w = op["width_m"]
    if nx == 0:
        return (min(x0, x1), min(y0, y0 + ny * w), max(x0, x1), max(y0, y0 + ny * w))
    return (min(x0, x0 + nx * w), min(y0, y1), max(x0, x0 + nx * w), max(y0, y1))


# ----------------------------------------------------------------------------- plan
def render_plan(spec):
    room = spec["room"]; L, W, t = room["length_m"], room["width_m"], room["wall_thickness_m"]
    M = 1.6  # margin in metres for dimension strings
    cw, ch = (L + 2 * M + 2 * t) * S, (W + 2 * M + 2 * t) * S + 150
    ox, oy = (M + t) * S, (M + t) * S

    def X(x): return ox + x * S
    def Y(y): return oy + (W - y) * S

    def outside_label(x0, y0, x1, y1, nx, ny, text, col):
        # label placed just outside the wall (beyond the wall thickness), never inside the room
        if ny != 0:
            ty = Y(y0) - t * S - 6 if ny < 0 else Y(y0) + t * S + 14
            return f"<text x='{X((x0 + x1) / 2)}' y='{ty}' text-anchor='middle' font-size='11' fill='{col}'>{text}</text>"
        tx = X(x0) - t * S - 6 if nx > 0 else X(x0) + t * S + 6
        return f"<text transform='translate({tx},{Y((y0 + y1) / 2)}) rotate(-90)' text-anchor='middle' font-size='11' fill='{col}'>{text}</text>"

    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{cw:.0f}' height='{ch:.0f}' viewBox='0 0 {cw:.0f} {ch:.0f}' {FONT} font-size='12'>",
           "<rect width='100%' height='100%' fill='white'/>",
           "<defs><pattern id='hatch' width='8' height='8' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'><line x1='0' y1='0' x2='0' y2='8' stroke='#777' stroke-width='1'/></pattern>"
           "<marker id='arrow' markerWidth='8' markerHeight='8' refX='6' refY='3' orient='auto'><path d='M0,0 L6,3 L0,6 z' fill='#1f5fbf'/></marker></defs>"]
    # walls (outer rect minus interior)
    out.append(f"<path fill-rule='evenodd' fill='#555' d='M{X(-t)},{Y(W + t)} h{(L + 2 * t) * S} v{(W + 2 * t) * S} h{-(L + 2 * t) * S} z "
               f"M{X(0)},{Y(W)} h{L * S} v{W * S} h{-L * S} z'/>")
    # zones / ceiling zones / level changes
    for z in spec.get("zones", []) or []:
        pts = " ".join(f"{X(x)},{Y(y)}" for x, y in z["polygon"])
        cx = sum(p[0] for p in z["polygon"]) / len(z["polygon"]); cy = sum(p[1] for p in z["polygon"]) / len(z["polygon"])
        out.append(f"<polygon points='{pts}' fill='#f3f6fb' stroke='#8aa' stroke-dasharray='6 4'/>"
                   f"<text x='{X(cx)}' y='{Y(cy) - 4}' fill='#577' font-size='11' text-anchor='middle' font-style='italic'>zone: {esc(z['name'])}</text>")
    for z in spec.get("level_changes", []) or []:
        pts = " ".join(f"{X(x)},{Y(y)}" for x, y in z["polygon"])
        cx = sum(p[0] for p in z["polygon"]) / len(z["polygon"]); cy = sum(p[1] for p in z["polygon"]) / len(z["polygon"])
        out.append(f"<polygon points='{pts}' fill='#e9e4d8' stroke='#8a7' stroke-width='1.5'/>"
                   f"<text x='{X(cx)}' y='{Y(cy) + 14}' fill='#564' font-size='11' text-anchor='middle'>level {z['delta_m']:+.2f} m — {esc(z['name'])}</text>")
    for z in spec.get("ceiling_zones", []) or []:
        pts = " ".join(f"{X(x)},{Y(y)}" for x, y in z["polygon"])
        cx = sum(p[0] for p in z["polygon"]) / len(z["polygon"]); cy = sum(p[1] for p in z["polygon"]) / len(z["polygon"])
        out.append(f"<polygon points='{pts}' fill='none' stroke='#b58' stroke-dasharray='2 4' stroke-width='1.5'/>"
                   f"<text x='{X(cx)}' y='{Y(cy) + 28}' fill='#b58' font-size='11' text-anchor='middle'>ceiling {f2(z['height_m'])} m — {esc(z['name'])}</text>")
    # openings
    for op in spec["openings"]:
        (x0, y0, x1, y1), (nx, ny) = opening_span(room, op)
        horiz = (ny != 0)
        # cut the wall
        if horiz:
            out.append(f"<rect x='{X(x0)}' y='{Y(y0) - (t * S if ny < 0 else 0)}' width='{(x1 - x0) * S}' height='{t * S}' fill='white'/>")
        else:
            out.append(f"<rect x='{X(x0) - (t * S if nx > 0 else 0)}' y='{Y(y1)}' width='{t * S}' height='{(y1 - y0) * S}' fill='white'/>")
        label = f"{esc(op['label'])} {f2(op['width_m'])} m"
        if op["type"] == "window":
            # glazing line in wall centre + sill note
            if horiz:
                yy = Y(y0) - (t * S / 2 if ny < 0 else -t * S / 2)
                out.append(f"<line x1='{X(x0)}' y1='{yy}' x2='{X(x1)}' y2='{yy}' stroke='#1a7' stroke-width='3'/>")
                ty = Y(y0) - t * S - 6 if ny < 0 else Y(y0) + t * S + 14
                out.append(f"<text x='{X((x0 + x1) / 2)}' y='{ty}' text-anchor='middle' font-size='11' fill='#1a7'>{label} (sill {f2(op['sill_m'])}, h {f2(op['height_m'])})</text>")
            else:
                xx = X(x0) - (t * S / 2 if nx > 0 else -t * S / 2)
                out.append(f"<line x1='{xx}' y1='{Y(y0)}' x2='{xx}' y2='{Y(y1)}' stroke='#1a7' stroke-width='3'/>")
                tx = X(x0) - t * S - 6 if nx > 0 else X(x0) + t * S + 6
                out.append(f"<text transform='translate({tx},{Y((y0 + y1) / 2)}) rotate(-90)' text-anchor='middle' font-size='11' fill='#1a7'>{label} (sill {f2(op['sill_m'])}, h {f2(op['height_m'])})</text>")
        elif op["type"] == "door":
            w = op["width_m"]; hinge = op.get("hinge", "left"); swing = op.get("swing", "in")
            # hinge point: left end as seen from inside
            hx, hy = (x0, y0) if (horiz and ny < 0) or (not horiz and nx > 0) else (x1, y1)
            if hinge == "right":
                hx, hy = (x1, y1) if (hx, hy) == (x0, y0) else (x0, y0)
            if swing in ("in", "out"):
                sgn = 1 if swing == "in" else -1
                ex, ey = hx + nx * w * sgn, hy + ny * w * sgn
                out.append(f"<line x1='{X(hx)}' y1='{Y(hy)}' x2='{X(ex)}' y2='{Y(ey)}' stroke='#c33' stroke-width='3'/>")
                # arc from leaf end to the other jamb
                ox2, oy2 = (x1, y1) if (hx, hy) == (x0, y0) else (x0, y0)
                sweep = 1
                out.append(f"<path d='M{X(ex)},{Y(ey)} A{w * S},{w * S} 0 0 {sweep} {X(ox2)},{Y(oy2)}' fill='none' stroke='#c33' stroke-dasharray='3 3'/>")
                out.append(f"<path d='M{X(ex)},{Y(ey)} A{w * S},{w * S} 0 0 {1 - sweep} {X(ox2)},{Y(oy2)}' fill='none' stroke='#c33' stroke-dasharray='3 3' opacity='0.35'/>")
            else:
                out.append(f"<line x1='{X(x0)}' y1='{Y(y0)}' x2='{X(x1)}' y2='{Y(y1)}' stroke='#c33' stroke-width='3' stroke-dasharray='6 3'/>")
            out.append(outside_label(x0, y0, x1, y1, nx, ny, f"{label} (h {f2(op['height_m'])})", '#c33'))
        else:
            out.append(f"<line x1='{X(x0)}' y1='{Y(y0)}' x2='{X(x1)}' y2='{Y(y1)}' stroke='#888' stroke-dasharray='8 4' stroke-width='2'/>")
            out.append(outside_label(x0, y0, x1, y1, nx, ny, f"{label} (h {f2(op['height_m'])})", '#666'))
    # furniture
    for f in spec["furniture"]:
        x0, y0, x1, y1 = furn_rect(f)
        fill = "url(#hatch)" if f["built_in"] else ("#fff8e6" if solid(f) else "none")
        stroke = "#333" if solid(f) else "#999"
        dash = "" if solid(f) else " stroke-dasharray='4 3'"
        out.append(f"<rect x='{X(x0)}' y='{Y(y1)}' width='{(x1 - x0) * S}' height='{(y1 - y0) * S}' fill='{fill}' stroke='{stroke}' stroke-width='1.5'{dash}/>")
        if f["built_in"]:
            out.append(f"<rect x='{X(x0)}' y='{Y(y1)}' width='{(x1 - x0) * S}' height='{(y1 - y0) * S}' fill='white' fill-opacity='0.55' stroke='none'/>")
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        seats = f" · {f['seats']} seats" if f.get("seats") else ""
        name = f["item"] if len(f["item"]) <= 30 else f["item"][:28].rstrip() + "…"
        bi = "built-in " if f["built_in"] and "built" not in name.lower() else ""
        l1, l2 = f"{esc(bi + name)}{seats}", f"{f2(f['length_m'])} × {f2(f['depth_m'])} m"
        if (x1 - x0) * S < 75 and (y1 - y0) > (x1 - x0):   # narrow item: rotate the label
            out.append(f"<g transform='translate({X(cx)},{Y(cy)}) rotate(-90)'><text x='0' y='-2' text-anchor='middle' font-size='10' fill='#222'>{l1}</text>"
                       f"<text x='0' y='10' text-anchor='middle' font-size='9.5' fill='#444'>{l2}</text></g>")
        elif not solid(f):   # rugs, pendants: label at the top edge so it does not collide with what sits under it
            out.append(f"<text x='{X(cx)}' y='{Y(y1) - 3}' text-anchor='middle' font-size='9.5' fill='#777'>{l1} · {l2}</text>")
        else:
            out.append(f"<text x='{X(cx)}' y='{Y(cy) - 2}' text-anchor='middle' font-size='10.5' fill='#222'>{l1}</text>"
                       f"<text x='{X(cx)}' y='{Y(cy) + 11}' text-anchor='middle' font-size='10' fill='#444'>{l2}</text>")
    # circulation
    path = spec["circulation"]["path"]
    pts = " ".join(f"{X(x)},{Y(y)}" for x, y in path)
    out.append(f"<polyline points='{pts}' fill='none' stroke='#1f5fbf' stroke-width='2' stroke-dasharray='10 6' marker-end='url(#arrow)'/>")
    mid = path[len(path) // 2]
    out.append(f"<text x='{X(mid[0]) + 6}' y='{Y(mid[1]) - 6}' font-size='11' fill='#1f5fbf'>circulation — min clear {f2(spec['circulation']['min_clear_width_m'])} m</text>")
    # overall dimension lines
    dy = Y(W + t) - 40
    out.append(f"<line x1='{X(0)}' y1='{dy}' x2='{X(L)}' y2='{dy}' stroke='#000'/><line x1='{X(0)}' y1='{dy - 6}' x2='{X(0)}' y2='{dy + 6}' stroke='#000'/><line x1='{X(L)}' y1='{dy - 6}' x2='{X(L)}' y2='{dy + 6}' stroke='#000'/>"
               f"<text x='{X(L / 2)}' y='{dy - 8}' text-anchor='middle' font-size='13' font-weight='bold'>{f2(L)} m</text>")
    dx = X(-t) - 40
    out.append(f"<line x1='{dx}' y1='{Y(0)}' x2='{dx}' y2='{Y(W)}' stroke='#000'/><line x1='{dx - 6}' y1='{Y(0)}' x2='{dx + 6}' y2='{Y(0)}' stroke='#000'/><line x1='{dx - 6}' y1='{Y(W)}' x2='{dx + 6}' y2='{Y(W)}' stroke='#000'/>"
               f"<text transform='translate({dx - 10},{Y(W / 2)}) rotate(-90)' text-anchor='middle' font-size='13' font-weight='bold'>{f2(W)} m</text>")
    # title block, scale bar, north arrow
    by = ch - 120
    out.append(f"<rect x='10' y='{by}' width='{cw - 20}' height='110' fill='none' stroke='#000'/>"
               f"<text x='20' y='{by + 22}' font-size='15' font-weight='bold'>PLAN — {esc(spec['title'])}</text>"
               f"<text x='20' y='{by + 42}' font-size='12'>Room {f2(L)} m × {f2(W)} m (interior clear) · ceiling {f2(room['ceiling_height_m'])} m · wall thickness {f2(t)} m</text>"
               f"<text x='20' y='{by + 60}' font-size='12'>Scale: 1 m = {S:.0f} px (1:50 when printed at 50 px per 25 mm). Dimensions in metres. Hatched = built-in. Dashed blue = circulation path.</text>"
               f"<line x1='20' y1='{by + 85}' x2='{20 + S}' y2='{by + 85}' stroke='#000' stroke-width='4'/><text x='{20 + S + 8}' y='{by + 89}' font-size='12'>1 m scale bar</text>"
               f"<g transform='translate({cw - 60},{by + 55})'><line x1='0' y1='30' x2='0' y2='-30' stroke='#000' marker-end='url(#arrow)'/><text x='-4' y='-36' font-size='12' font-weight='bold'>N</text></g>")
    out.append("</svg>")
    return "\n".join(out)


# ----------------------------------------------------------------------------- elevation
def render_elevation(spec):
    room = spec["room"]; el = spec["elevation"]
    Lw, H = wall_len(room, el["wall"]), room["ceiling_height_m"]
    M = 1.4
    cw, ch = (Lw + 2 * M) * S, (H + 2 * M) * S + 110  # top margin M also holds stacked labels for thin elements
    ox, oy = M * S, M * S

    def X(x): return ox + x * S
    def Z(z): return oy + (H - z) * S

    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{cw:.0f}' height='{ch:.0f}' viewBox='0 0 {cw:.0f} {ch:.0f}' {FONT} font-size='12'>",
           "<rect width='100%' height='100%' fill='white'/>",
           f"<rect x='{X(0)}' y='{Z(H)}' width='{Lw * S}' height='{H * S}' fill='#fbfaf7' stroke='#000' stroke-width='2'/>",
           f"<line x1='{X(0) - 20}' y1='{Z(0)}' x2='{X(Lw) + 20}' y2='{Z(0)}' stroke='#000' stroke-width='3'/>",
           f"<text x='{X(Lw) + 26}' y='{Z(0) + 4}' font-size='12'>FFL 0.00 m</text>",
           f"<text x='{X(Lw) + 26}' y='{Z(H) + 4}' font-size='12'>ceiling {f2(H)} m</text>"]
    # openings on this wall (same source of truth as the plan)
    for op in spec["openings"]:
        if op["wall"] != el["wall"]:
            continue
        x0 = op["offset_m"]; w = op["width_m"]; z0 = op["sill_m"]; h = op["height_m"]
        col = {"window": "#1a7", "door": "#c33", "opening": "#888"}[op["type"]]
        out.append(f"<rect x='{X(x0)}' y='{Z(z0 + h)}' width='{w * S}' height='{h * S}' fill='#e8f6f0' fill-opacity='0.6' stroke='{col}' stroke-width='2'/>"
                   f"<text x='{X(x0 + w / 2)}' y='{Z(z0 + h) - 4}' text-anchor='middle' font-size='11' fill='{col}'>{esc(op['label'])} {f2(w)} × {f2(h)} m, sill {f2(z0)}</text>")
    small_k = 0
    for e in sorted(el["elements"], key=lambda e: -e["width_m"] * e["height_m"]):   # big first so small ones draw on top
        fill = e.get("hex", "#ddd")
        out.append(f"<rect x='{X(e['x_m'])}' y='{Z(e['z_m'] + e['height_m'])}' width='{e['width_m'] * S}' height='{e['height_m'] * S}' fill='{fill}' fill-opacity='0.75' stroke='#222' stroke-width='1.5'/>")
        cx = e["x_m"] + e["width_m"] / 2
        txt = f"{esc(e['label'])} — {esc(e['material'])} — {f2(e['width_m'])} w × {f2(e['height_m'])} h, top {f2(e['z_m'] + e['height_m'])} m"
        if e["height_m"] * S >= 44 and e["width_m"] * S >= 120:
            top = Z(e["z_m"] + e["height_m"])
            out.append(f"<text x='{X(e['x_m']) + 4}' y='{top + 13}' font-size='10.5' fill='#111'>{esc(e['label'])} — {esc(e['material'])}</text>"
                       f"<text x='{X(e['x_m']) + 4}' y='{top + 25}' font-size='9.5' fill='#333'>{f2(e['width_m'])} w × {f2(e['height_m'])} h, top at {f2(e['z_m'] + e['height_m'])} m</text>")
        else:
            # thin or narrow element: label in the margin above the wall with a leader line, staggered to avoid collisions
            ly = Z(H) - 48 - 13 * (small_k % 4); small_k += 1
            out.append(f"<line x1='{X(cx)}' y1='{Z(e['z_m'] + e['height_m'])}' x2='{X(cx)}' y2='{ly + 3}' stroke='#777' stroke-width='0.8' stroke-dasharray='2 2'/>"
                       f"<text x='{X(cx)}' y='{ly}' text-anchor='middle' font-size='9.5' fill='#111'>{txt}</text>")
    for d in el.get("datum_lines", []) or []:
        out.append(f"<line x1='{X(0)}' y1='{Z(d['z_m'])}' x2='{X(Lw)}' y2='{Z(d['z_m'])}' stroke='#b58' stroke-dasharray='4 4'/>"
                   f"<text x='{X(0) - 6}' y='{Z(d['z_m']) + 4}' text-anchor='end' font-size='10.5' fill='#b58'>{esc(d['label'])} {f2(d['z_m'])} m</text>")
    # height dimension line
    dx = X(0) - 50
    out.append(f"<line x1='{dx}' y1='{Z(0)}' x2='{dx}' y2='{Z(H)}' stroke='#000'/><line x1='{dx - 6}' y1='{Z(0)}' x2='{dx + 6}' y2='{Z(0)}' stroke='#000'/><line x1='{dx - 6}' y1='{Z(H)}' x2='{dx + 6}' y2='{Z(H)}' stroke='#000'/>"
               f"<text transform='translate({dx - 10},{Z(H / 2)}) rotate(-90)' text-anchor='middle' font-size='13' font-weight='bold'>{f2(H)} m</text>")
    dy = Z(0) + 36   # wall-length dimension below the floor line (the margin above holds stacked labels)
    out.append(f"<line x1='{X(0)}' y1='{dy}' x2='{X(Lw)}' y2='{dy}' stroke='#000'/><line x1='{X(0)}' y1='{dy - 6}' x2='{X(0)}' y2='{dy + 6}' stroke='#000'/><line x1='{X(Lw)}' y1='{dy - 6}' x2='{X(Lw)}' y2='{dy + 6}' stroke='#000'/>"
               f"<text x='{X(Lw / 2)}' y='{dy + 18}' text-anchor='middle' font-size='13' font-weight='bold'>{f2(Lw)} m</text>")
    by = ch - 90
    out.append(f"<rect x='10' y='{by}' width='{cw - 20}' height='80' fill='none' stroke='#000'/>"
               f"<text x='20' y='{by + 22}' font-size='15' font-weight='bold'>ELEVATION — {esc(el['title'])} ({el['wall']} wall)</text>"
               f"<text x='20' y='{by + 42}' font-size='12'>Wall length {f2(Lw)} m · ceiling {f2(H)} m · heights in metres above FFL · materials labelled on the drawing</text>"
               f"<line x1='20' y1='{by + 62}' x2='{20 + S}' y2='{by + 62}' stroke='#000' stroke-width='4'/><text x='{20 + S + 8}' y='{by + 66}' font-size='12'>1 m scale bar · 1 m = {S:.0f} px</text>")
    out.append("</svg>")
    return "\n".join(out)


# ----------------------------------------------------------------------------- palette
def render_palette(spec):
    pal = spec["palette"]; n = len(pal); cols = 2 if n > 4 else 1
    rows = math.ceil(n / cols); cw, rh = 520, 128
    W, H = cols * cw + 20, rows * rh + 80
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}' {FONT} font-size='12'>",
           "<rect width='100%' height='100%' fill='white'/>",
           f"<text x='16' y='30' font-size='16' font-weight='bold'>PALETTE BOARD — {esc(spec['title'])}</text>",
           f"<text x='16' y='48' font-size='11' fill='#444'>Floor finish: {esc(spec['room'].get('floor_finish', 'see swatches'))}</text>"]
    for i, p in enumerate(pal):
        c, r = i % cols, i // cols
        x, y = 16 + c * cw, 64 + r * rh
        out.append(f"<rect x='{x}' y='{y}' width='110' height='110' fill='{p['hex']}' stroke='#222'/>"
                   f"<text x='{x + 124}' y='{y + 18}' font-size='13' font-weight='bold'>{esc(p['name'])} <tspan font-weight='normal' fill='#555'>{esc(p['hex'].upper())}</tspan> <tspan font-size='10' fill='#777'>({esc(p['role'])})</tspan></text>"
                   f"<text x='{x + 124}' y='{y + 40}' font-size='12'>Material: {esc(p['material'])}</text>"
                   f"<text x='{x + 124}' y='{y + 58}' font-size='12'>Finish: {esc(p['finish'])}</text>"
                   f"<text x='{x + 124}' y='{y + 76}' font-size='12'>Used: {esc(p['where'][:70])}</text>")
    out.append("</svg>")
    return "\n".join(out)


def render(spec_path: Path):
    spec = json.loads(spec_path.read_text())
    jsonschema.validate(spec, SPEC_SCHEMA)
    d = spec_path.parent
    (d / "plan.svg").write_text(render_plan(spec))
    (d / "elevation.svg").write_text(render_elevation(spec))
    (d / "palette.svg").write_text(render_palette(spec))
    print("rendered", d / "plan.svg", d / "elevation.svg", d / "palette.svg")


# ----------------------------------------------------------------------------- checks (PRD §5.4)
def check(spec_path: Path, brief_id=None):
    spec = json.loads(spec_path.read_text())
    schema_ok, schema_err = True, ""
    try:
        jsonschema.validate(spec, SPEC_SCHEMA)
    except Exception as e:  # noqa
        schema_ok, schema_err = False, str(e)[:200]
    brief = BRIEFS[brief_id or spec["brief_id"]]
    room = spec["room"]; L, W, H = room["length_m"], room["width_m"], room["ceiling_height_m"]
    furn = spec["furniture"]; solids = [f for f in furn if solid(f)]
    results = []

    def rec(cid, name, fails):
        results.append({"check_id": cid, "check": name, "violated": int(bool(fails)), "notes": "; ".join(fails) if fails else "ok"})

    # 1 room dimensions
    fails = []
    if abs(L - brief["length_m"]) > 0.05: fails.append(f"length {L} vs brief {brief['length_m']}")
    if abs(W - brief["width_m"]) > 0.05: fails.append(f"width {W} vs brief {brief['width_m']}")
    rec(1, "room dimensions match brief (±0.05 m)", fails)
    # 2 ceiling
    fails = [] if abs(H - brief["ceiling_height_m"]) <= 0.011 else [f"ceiling {H} vs brief {brief['ceiling_height_m']}"]
    rec(2, "ceiling height matches brief", fails)
    # 3 openings
    fails = []
    def walls_of(cls):
        return {"long": ["north", "south"], "short": ["west", "east"], "any": ["north", "south", "west", "east"]}[cls]
    for req in brief["required_openings"]:
        if req["type"] == "window":
            ok = False
            for wname in walls_of(req.get("wall_class", "any")):
                tot = sum(o["width_m"] for o in spec["openings"] if o["type"] == "window" and o["wall"] == wname)
                if tot > 0 and tot >= req.get("min_fraction_of_wall", 0) * wall_len(room, wname) - 0.001:
                    ok = True
            if not ok: fails.append(f"missing {req['label']}")
        elif req["type"] == "door":
            cands = [o for o in spec["openings"] if o["type"] == "door" and o["role"] == req["role"]]
            if "wall_class" in req: cands = [o for o in cands if o["wall"] in walls_of(req["wall_class"])]
            cands = [o for o in cands if req["min_width_m"] - 0.001 <= o["width_m"] <= req["max_width_m"] + 0.001]
            if not cands: fails.append(f"missing {req['label']} ({req['min_width_m']}–{req['max_width_m']} m)")
        elif req["type"] == "any":
            others = [o for o in spec["openings"] if o["role"] != "kitchen"]
            if not others: fails.append(f"missing {req['label']}")
    for o in spec["openings"]:
        wl = wall_len(room, o["wall"])
        if o["offset_m"] + o["width_m"] > wl + 0.001: fails.append(f"{o['id']} exceeds its wall ({o['offset_m']}+{o['width_m']} > {wl})")
        if o["sill_m"] + o["height_m"] > H + 0.001: fails.append(f"{o['id']} taller than ceiling")
        if o["type"] == "door" and not (1.9 <= o["height_m"] <= 2.4 + 0.001): fails.append(f"{o['id']} implausible door height {o['height_m']}")
        if o["type"] == "door" and o["sill_m"] > 0.02: fails.append(f"{o['id']} door has a sill")
    for i, a in enumerate(spec["openings"]):
        for b in spec["openings"][i + 1:]:
            if a["wall"] == b["wall"] and min(a["offset_m"] + a["width_m"], b["offset_m"] + b["width_m"]) - max(a["offset_m"], b["offset_m"]) > 0.001:
                fails.append(f"openings {a['id']} and {b['id']} overlap on the {a['wall']} wall")
    rec(3, "required openings present, positioned, plausible", fails)
    # 4 functions
    fails = []; fn = brief["functions"]
    def has(tag): return [f for f in furn if tag in f["functions"]]
    if "seats_min" in fn:
        seats = sum(f.get("seats", 0) for f in furn if {"seating", "dining_seating"} & set(f["functions"]))
        if seats < fn["seats_min"]: fails.append(f"seats {seats} < {fn['seats_min']}")
    if "dining_seats_min" in fn:
        seats = sum(f.get("seats", 0) for f in has("dining_seating"))
        if seats < fn["dining_seats_min"]: fails.append(f"dining seats {seats} < {fn['dining_seats_min']}")
        if not has("dining_table"): fails.append("no dining table")
    if fn.get("fireplace") and not (has("fireplace") or has("hearth")): fails.append("no fireplace/hearth element")
    if fn.get("entry_element_required"):
        ents = has("entry_element") + has("screen")
        ents += [z for z in (spec.get("level_changes") or []) + (spec.get("ceiling_zones") or []) if "entr" in (z["name"] + z.get("description", "")).lower()]
        if not ents: fails.append("no named entry element (vestibule/screen/built-in/step/ceiling change)")
    if "entry_to_seating_min_m" in fn:
        doors = [o for o in spec["openings"] if o["type"] == "door" and o["role"] == "entry"]
        seats = [f for f in furn if {"seating", "dining_seating"} & set(f["functions"])]
        if doors and seats:
            (cx, cy), _ = opening_centre(room, doors[0])
            dmin = min(point_rect_dist(cx, cy, furn_rect(f)) for f in seats)
            if dmin < fn["entry_to_seating_min_m"] - 0.001: fails.append(f"entry door {dmin:.2f} m from nearest seating (< {fn['entry_to_seating_min_m']})")
        elif not doors: fails.append("no entry door to measure from")
    if fn.get("built_in_seating_or_sideboard"):
        if not [f for f in furn if f["built_in"] and {"seating", "dining_seating", "sideboard"} & set(f["functions"])]: fails.append("no built-in seating or sideboard")
    if fn.get("built_in_desk_and_shelving_same_wall"):
        def touching_walls(f):
            x0, y0, x1, y1 = furn_rect(f); ws = set()
            if y0 <= 0.05: ws.add("south")
            if y1 >= W - 0.05: ws.add("north")
            if x0 <= 0.05: ws.add("west")
            if x1 >= L - 0.05: ws.add("east")
            return ws
        desks = [f for f in has("desk") if f["built_in"]]; shelves = [f for f in has("shelving") if f["built_in"]]
        same = any(touching_walls(d) & touching_walls(s) for d in desks for s in shelves)
        if not (desks and shelves and same): fails.append("built-in desk and built-in shelving not both present on the same wall")
    if fn.get("bed") and not has("bed"): fails.append("no bed/daybed")
    if fn.get("storage_without_freestanding_wardrobe"):
        if not [f for f in furn if {"storage", "wardrobe", "shelving", "sideboard"} & set(f["functions"])]: fails.append("no storage item")
        if [f for f in has("wardrobe") if not f["built_in"]]: fails.append("freestanding wardrobe present")
    if "zones_min" in fn and len(spec.get("zones") or []) < fn["zones_min"]: fails.append(f"fewer than {fn['zones_min']} zones defined")
    if fn.get("no_full_partition"):
        for f in has("partition") + has("screen"):
            if f["depth_m"] >= W - 0.1 or f["length_m"] >= L - 0.1: fails.append(f"{f['id']} spans the full room")
    if fn.get("level_or_ceiling_change"):
        zs = [z for z in (spec.get("level_changes") or []) + (spec.get("ceiling_zones") or []) if poly_area(z["polygon"]) > 0.05]
        if not zs: fails.append("no level or ceiling change located on the plan")
    rec(4, "required functions served", fails)
    # 5 circulation and door swings
    fails = []; circ = spec["circulation"]; path = circ["path"]; need = brief["circulation"]["min_clear_width_m"]
    pts = []
    for p, q in zip(path, path[1:]): pts += seg_points(p, q)
    min_clear, worst = 99, None
    spans = [opening_span(room, o)[0] for o in spec["openings"] if o["type"] in ("door", "opening")]

    def wall_clear(px, py):
        # distance to each wall, except where the perpendicular foot lies inside a door/opening span (the wall is
        # open there): then the lateral distance to the nearer jamb is used instead.
        best = 99.0
        for wall, d, foot in (("west", px, (0.0, py)), ("east", L - px, (L, py)), ("south", py, (px, 0.0)), ("north", W - py, (px, W))):
            for (x0, y0, x1, y1) in spans:
                if wall in ("west", "east") and abs(x0 - foot[0]) < 1e-6 and min(y0, y1) <= py <= max(y0, y1):
                    d = min(abs(py - y0), abs(py - y1)) + 0.45; break   # inside the opening: clearance is to the jambs
                if wall in ("south", "north") and abs(y0 - foot[1]) < 1e-6 and min(x0, x1) <= px <= max(x0, x1):
                    d = min(abs(px - x0), abs(px - x1)) + 0.45; break
            best = min(best, d)
        return best

    for (px, py) in pts:
        if not (-0.001 <= px <= L + 0.001 and -0.001 <= py <= W + 0.001):
            fails.append(f"path leaves the room at ({px:.2f},{py:.2f})"); break
        c = wall_clear(px, py)
        for f in solids:
            c = min(c, point_rect_dist(px, py, furn_rect(f)))
        if 2 * c < min_clear: min_clear, worst = 2 * c, (px, py)
    if min_clear < need - 0.01: fails.append(f"clear width along path {min_clear:.2f} m < {need} (worst at {worst[0]:.2f},{worst[1]:.2f})")
    if circ["min_clear_width_m"] < need - 0.001: fails.append(f"stated min clear width {circ['min_clear_width_m']} < {need}")
    def near_rects(rects, tol=0.8):
        return any(point_rect_dist(px, py, r) <= tol for (px, py) in pts for r in rects)
    for tgt in brief["circulation"]["targets"]:
        ok = True
        if tgt in ("entry", "kitchen"):
            ds = [o for o in spec["openings"] if o["type"] == "door" and o["role"] == tgt]
            ok = bool(ds) and any(math.hypot(px - opening_centre(room, d)[0][0], py - opening_centre(room, d)[0][1]) <= 0.9 for d in ds for (px, py) in pts)
        elif tgt == "second_opening":
            os_ = [o for o in spec["openings"] if o["role"] != "kitchen"]
            ok = bool(os_) and any(math.hypot(px - opening_centre(room, o)[0][0], py - opening_centre(room, o)[0][1]) <= 1.0 for o in os_ for (px, py) in pts)
        elif tgt == "seating": ok = near_rects([furn_rect(f) for f in furn if {"seating", "dining_seating"} & set(f["functions"])])
        elif tgt == "fireplace": ok = near_rects([furn_rect(f) for f in has("fireplace") + has("hearth")], 1.0)
        elif tgt == "dining_table": ok = near_rects([furn_rect(f) for f in has("dining_table")], 1.5)   # chairs may sit between path and table
        elif tgt == "desk": ok = near_rects([furn_rect(f) for f in has("desk")])
        elif tgt == "bed": ok = near_rects([furn_rect(f) for f in has("bed")])
        elif tgt == "west_end": ok = any(px <= 0.8 for (px, py) in pts)
        elif tgt == "east_end": ok = any(px >= L - 0.8 for (px, py) in pts)
        if not ok: fails.append(f"path does not reach {tgt}")
    for o in spec["openings"]:
        if o["type"] != "door": continue
        sw = swing_rect(room, o)
        for f in solids:
            if rect_overlap_area(sw, furn_rect(f)) > 0.01: fails.append(f"{f['id']} ({f['item']}) blocks door {o['id']} swing/clearance")
    rec(5, "circulation ≥ 0.90 m clear; nothing in door swings", fails)
    # 6 fit and overlap
    fails = []
    for f in furn:
        x0, y0, x1, y1 = furn_rect(f)
        if x0 < -0.001 or y0 < -0.001 or x1 > L + 0.001 or y1 > W + 0.001: fails.append(f"{f['id']} outside room")
        if f["length_m"] > L + 0.001 or f["depth_m"] > W + 0.001 or f["height_m"] > H + 0.001: fails.append(f"{f['id']} exceeds room in a dimension")
    for i, a in enumerate(solids):
        for b in solids[i + 1:]:
            if rect_overlap_area(furn_rect(a), furn_rect(b)) > 0.005: fails.append(f"{a['id']} overlaps {b['id']}")
    rec(6, "furniture fits, no overlaps", fails)
    # 7 materials (brief must / must-not; do-not list of the rule library is checked manually, see outputs/manual_checks.json)
    fails = []; mats = brief["materials"]
    texts = [p["where"] + " " + p["material"] + " " + p["finish"] + " " + p["name"] for p in spec["palette"]]
    texts += [f["material"] + " " + f["finish"] + " " + f["item"] for f in furn] + [e["material"] + " " + e["label"] for e in spec["elevation"]["elements"]]
    md = (spec_path.parent / "spec.md").read_text().lower() if (spec_path.parent / "spec.md").exists() else ""
    if mats.get("must_floor_finish"):
        if not (room.get("floor_finish") or any("floor" in p["where"].lower() for p in spec["palette"])): fails.append("floor finish not named in palette/room")
    blob = (" ".join(texts) + " " + md).lower()
    neg = re.compile(r"\b(no|not|never|without|avoid(?:s|ed|ing)?|free of|rather than|instead of|non)[\s-]+(?:[\w-]+\s+){0,3}[\w-]*$")
    for term in mats["must_not_terms"]:
        hits = [m.start() for m in re.finditer(re.escape(term), blob)]
        real = [h for h in hits if not neg.search(blob[max(0, h - 40):h])]
        if real: fails.append(f"forbidden material term present: '{term}' ({len(real)} non-negated mention(s))")
    manual = ROOT / "outputs" / "manual_checks.json"
    if manual.exists():
        m = json.loads(manual.read_text()).get(f"{spec['brief_id']}/{spec['arm']}", {})
        for v in m.get("do_not_list_violations", []): fails.append(f"do-not list: {v}")
    rec(7, "palette/materials respect must and must-not lists (and the do-not list in the learned arm)", fails)
    # 8 SVG ↔ spec and spec.md ↔ spec.json consistency
    fails = []
    svg = (spec_path.parent / "plan.svg").read_text() if (spec_path.parent / "plan.svg").exists() else ""
    if not svg: fails.append("plan.svg missing")
    else:
        for s_ in (f2(L), f2(W)):
            if f"{s_} m" not in svg: fails.append(f"room dimension {s_} not on plan")
        for f in furn:
            if f"{f2(f['length_m'])} × {f2(f['depth_m'])} m" not in svg: fails.append(f"{f['id']} footprint not on plan")
        for o in spec["openings"]:
            if f"{f2(o['width_m'])} m" not in svg: fails.append(f"{o['id']} width not on plan")
    if md:
        for s_ in (f2(L), f2(W), f2(H)):
            if s_ not in md: fails.append(f"{s_} m not stated in spec.md")
        missing = [f["id"] for f in furn if f2(f["length_m"]) not in md or f2(f["depth_m"]) not in md]
        if missing: fails.append(f"furniture dimensions not in spec.md: {', '.join(missing[:6])}")
        for p in spec["palette"]:
            if p["hex"].lower() not in md: fails.append(f"palette {p['hex']} not in spec.md")
    else:
        fails.append("spec.md missing")
    rec(8, "SVG and spec.md dimensions match spec.json", fails)
    summary = {"brief": spec["brief_id"], "arm": spec["arm"], "schema_valid": schema_ok, "schema_error": schema_err,
               "violations": sum(r["violated"] for r in results), "checks": results}
    (spec_path.parent / "check_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def write_violations_csv(summaries):
    out = ROOT / "outputs" / "violations.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["brief", "arm", "check_id", "violated", "notes"])
        for s in summaries:
            for r in s["checks"]:
                w.writerow([s["brief"], s["arm"], r["check_id"], r["violated"], r["notes"]])
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "check", "check-all", "render-all"])
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--phase", default="test", help="for check-all: test or iteration")
    a = ap.parse_args()
    if a.cmd == "render":
        render(Path(a.spec))
    elif a.cmd == "check":
        s = check(Path(a.spec)); print(json.dumps(s, indent=1))
    else:
        specs = sorted((ROOT / "outputs" / "designs").glob("*/*/spec.json"))
        specs = [p for p in specs if (BRIEFS[p.parent.parent.name]["phase"] == a.phase)]
        if a.cmd == "render-all":
            for p in specs: render(p)
        else:
            sums = [check(p) for p in specs]
            for s in sums: print(f"{s['brief']:14s} {s['arm']:9s} violations={s['violations']}  " + "  ".join(f"c{r['check_id']}={'X' if r['violated'] else '.'}" for r in s["checks"]))
            write_violations_csv(sums)
