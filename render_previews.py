"""Render PNG previews from the example DXF files (via ezdxf).

Run with:  .venv/bin/python render_previews.py
Writes one .png next to each .dxf in examples/.

The previews are presentation drawings, not the cut files: each part
is filled lightly so it reads as a solid piece, panels are labelled
with their name and size, and the key dimensions are printed under
the drawing. The geometry itself is read straight from the DXF, so
what you see is exactly what the file contains — including the
25 mm gaps between the box panels: the six panels are six separate
closed outlines, nothing is joined or touching.
"""

from __future__ import annotations

import os

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

INK = "#1f2937"        # dark slate outline
FILL = "#dbe7f3"       # pale steel-blue fill for cut parts
HOLE_FILL = "#ffffff"  # holes read as holes
LABEL = "#475569"      # slate grey for labels
TITLE = "#1f2937"


def _entities(path: str):
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    polys = [[(float(v[0]), float(v[1])) for v in e.vertices()]
             for e in msp if e.dxftype() == "LWPOLYLINE"]
    circles = [(e.dxf.center.x, e.dxf.center.y, e.dxf.radius)
               for e in msp if e.dxftype() == "CIRCLE"]
    return polys, circles


def _new_fig(min_x: float, min_y: float, width_mm: float,
             height_mm: float, title: str, caption: str):
    """Figure sized to the drawing, with room for a title on top
    and a caption underneath. Returns (fig, ax)."""
    label_room = max(height_mm * 0.22, 12.0)  # mm below the drawing
    title_room = max(height_mm * 0.12, 8.0)   # mm above the drawing
    total_h = height_mm + label_room + title_room
    fig_w = max(width_mm / 90.0, 4.0)
    fig_h = fig_w * total_h / width_mm
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(min_x - width_mm * 0.02, min_x + width_mm * 1.02)
    ax.set_ylim(min_y - label_room, min_y + height_mm + title_room)
    ax.set_title(title, fontsize=13, color=TITLE, pad=16)
    ax.text(min_x + width_mm / 2.0, min_y - label_room * 0.42, caption,
            ha="center", va="center", fontsize=11, color=LABEL)
    return fig, ax


def _draw_poly(ax, pts, fill=FILL):
    ax.add_patch(Polygon(pts, closed=True, fill=True,
                         facecolor=fill, edgecolor=INK, linewidth=1.4,
                         joinstyle="miter"))
    xs = [p[0] for p in pts] + [pts[0][0]]
    ys = [p[1] for p in pts] + [pts[0][1]]
    ax.plot(xs, ys, color=INK, linewidth=1.4, solid_joinstyle="miter")


def _draw_circle(ax, cx, cy, r):
    ax.add_patch(Circle((cx, cy), r, fill=True, facecolor=HOLE_FILL,
                        edgecolor=INK, linewidth=1.4))


def render_box(path: str, out: str) -> None:
    polys, _ = _entities(path)
    # layout order is the panel order: bottom, front, back, left,
    # right, top — sort by left edge to recover it from the file.
    polys.sort(key=lambda p: min(x for x, _ in p))
    names = [("bottom", "100×80"), ("front", "100×60"),
             ("back", "100×60"), ("left", "80×60"),
             ("right", "80×60"), ("top", "100×80")]
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    # The drawing is very wide and short, so give the labels their
    # own band below the panels: one line per panel ("bottom · 100×80")
    # at the top of the band, the caption at the bottom of it.
    label_room = 34.0
    title_room = 10.0
    total_h = height + label_room + title_room
    # Wide figure on purpose: at 90 mm per inch a readable 9.5 pt
    # label would be ~100 mm wide in drawing units and neighbouring
    # labels would collide. At 45 mm per inch the same label is
    # ~50 mm wide and sits neatly under its own panel.
    fig_w = max(width / 45.0, 4.0)
    fig_h = fig_w * total_h / width
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(min(xs) - width * 0.02, max(xs) + width * 0.02)
    ax.set_ylim(min(ys) - label_room, max(ys) + title_room)
    ax.set_title("Finger-joint box  ·  100 × 80 × 60 mm  ·  3 mm material",
                 fontsize=13, color=TITLE, pad=16)
    ax.text(min(xs) + width / 2.0, min(ys) - label_room + 4.0,
            "Six separate panels, 25 mm apart — each one a closed outline.",
            ha="center", va="bottom", fontsize=10.5, color=LABEL)
    for (name, size), pts in zip(names, polys):
        _draw_poly(ax, pts)
        cx = (min(x for x, _ in pts) + max(x for x, _ in pts)) / 2.0
        ax.text(cx, min(ys) - 5.0, f"{name} · {size}", ha="center",
                va="top", fontsize=9.5, color=LABEL)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def render_gear(path: str, out: str) -> None:
    polys, circles = _entities(path)
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    fig, ax = _new_fig(min(xs), min(ys), width, height,
                       "Involute spur gear  ·  module 2  ·  20 teeth",
                       "Tip Ø 44 mm  ·  pitch Ø 40 mm  ·  root Ø 35 mm  ·  "
                       "bore Ø 8 mm  ·  20° pressure angle")
    for pts in polys:
        _draw_poly(ax, pts)
    for cx, cy, r in circles:
        _draw_circle(ax, cx, cy, r)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def render_bracket(path: str, out: str) -> None:
    polys, circles = _entities(path)
    xs = [x for p in polys for x, _ in p]
    ys = [y for p in polys for _, y in p]
    width, height = max(xs) - min(xs), max(ys) - min(ys)
    fig, ax = _new_fig(min(xs), min(ys), width, height,
                       "Mounting bracket  ·  60 × 40 mm",
                       "4 holes Ø 5 mm  ·  corner radius 5 mm")
    for pts in polys:
        _draw_poly(ax, pts)
    for cx, cy, r in circles:
        _draw_circle(ax, cx, cy, r)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    examples = os.path.join(HERE, "examples")
    render_box(os.path.join(examples, "box_100x80x60_t3.dxf"),
               os.path.join(examples, "box_100x80x60_t3.png"))
    render_gear(os.path.join(examples, "gear_m2_z20.dxf"),
                os.path.join(examples, "gear_m2_z20.png"))
    render_bracket(os.path.join(examples, "bracket_60x40.dxf"),
                   os.path.join(examples, "bracket_60x40.png"))


if __name__ == "__main__":
    main()
