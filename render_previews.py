"""Render PNG previews from the example DXF files (via ezdxf).

Run with:  .venv/bin/python render_previews.py
Writes one .png next to each .dxf in examples/.
"""

from __future__ import annotations

import math
import os

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def render(path: str, out: str) -> None:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    for e in msp:
        if e.dxftype() == "LWPOLYLINE":
            pts = [(float(v[0]), float(v[1])) for v in e.vertices()]
            pts.append(pts[0])
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            ax.plot(xs, ys, color="#1a1a1a", linewidth=1.2)
        elif e.dxftype() == "CIRCLE":
            c = e.dxf.center
            r = e.dxf.radius
            circ = plt.Circle((c.x, c.y), r, fill=False,
                              color="#1a1a1a", linewidth=1.2)
            ax.add_patch(circ)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.margins(0.05)
    fig.tight_layout(pad=0.2)
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"wrote {out}")


def main() -> None:
    for name in ("box_100x80x60_t3.dxf", "gear_m2_z20.dxf",
                 "bracket_60x40.dxf"):
        src = os.path.join(HERE, "examples", name)
        dst = os.path.splitext(src)[0] + ".png"
        render(src, dst)


if __name__ == "__main__":
    main()
