"""Command-line interface for the LaserCut DXF Generator.

Examples:
    python -m dxfgen box --length 100 --width 80 --height 60 \\
        --thickness 3 --output box.dxf
    python -m dxfgen gear --module 2 --teeth 20 --bore 8 \\
        --output gear.dxf
    python -m dxfgen bracket --width 60 --height 40 --corner-radius 5 \\
        --hole-dia 5 --hole-margin 10 --output bracket.dxf
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .dxf import DxfDocument
from .geometry import box_panels, bracket_outline, gear_outline


def _report(doc: DxfDocument, path: str) -> None:
    min_x, min_y, max_x, max_y = doc.bounds()
    print(f"wrote {path}")
    print(f"entities: {doc.entity_count}")
    print(f"size: {max_x - min_x:.2f} x {max_y - min_y:.2f} mm "
          f"({min_x:.2f},{min_y:.2f}) to ({max_x:.2f},{max_y:.2f})")


def _cmd_box(args: argparse.Namespace) -> int:
    panels = box_panels(args.length, args.width, args.height,
                        args.thickness, kerf=args.kerf)
    doc = DxfDocument()
    for name in ("bottom", "front", "back", "left", "right", "top"):
        doc.add_polyline(panels[name])
    doc.write(args.output)
    print(f"box {args.length} x {args.width} x {args.height} mm, "
          f"thickness {args.thickness} mm, kerf {args.kerf} mm")
    _report(doc, args.output)
    return 0


def _cmd_gear(args: argparse.Namespace) -> int:
    outline, (bx, by, br) = gear_outline(
        args.module, args.teeth, args.bore,
        pressure_angle_deg=args.pressure_angle)
    doc = DxfDocument()
    doc.add_polyline(outline)
    if br > 0:
        doc.add_circle(bx, by, br)
    doc.write(args.output)
    print(f"spur gear: module {args.module}, {args.teeth} teeth, "
          f"pitch dia {args.module * args.teeth:.2f} mm, "
          f"tip dia {args.module * (args.teeth + 2):.2f} mm, "
          f"bore {args.bore} mm")
    _report(doc, args.output)
    return 0


def _cmd_bracket(args: argparse.Namespace) -> int:
    outline, holes = bracket_outline(
        args.width, args.height, args.corner_radius,
        args.hole_dia, args.hole_margin)
    doc = DxfDocument()
    doc.add_polyline(outline)
    for cx, cy, r in holes:
        doc.add_circle(cx, cy, r)
    doc.write(args.output)
    print(f"bracket {args.width} x {args.height} mm, "
          f"corner radius {args.corner_radius} mm, "
          f"{len(holes)} holes dia {args.hole_dia} mm")
    _report(doc, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dxfgen",
        description="Generate ready-to-cut DXF files for laser "
                    "cutting & CNC. Pure Python, zero dependencies.")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("box", help="finger-joint box (6 panels)")
    p.add_argument("--length", type=float, required=True,
                   help="outer length in mm")
    p.add_argument("--width", type=float, required=True,
                   help="outer width in mm")
    p.add_argument("--height", type=float, required=True,
                   help="outer height in mm")
    p.add_argument("--thickness", type=float, required=True,
                   help="material thickness in mm")
    p.add_argument("--kerf", type=float, default=0.0,
                   help="laser kerf in mm (default 0); widens tabs and "
                        "narrows slots so the finished joint fits exactly")
    p.add_argument("--output", required=True, help="output .dxf file")
    p.set_defaults(func=_cmd_box)

    p = sub.add_parser("gear", help="involute spur gear")
    p.add_argument("--module", type=float, required=True,
                   help="gear module in mm")
    p.add_argument("--teeth", type=int, required=True,
                   help="number of teeth (>= 6)")
    p.add_argument("--bore", type=float, required=True,
                   help="centre bore diameter in mm (0 for none)")
    p.add_argument("--pressure-angle", type=float, default=20.0,
                   help="pressure angle in degrees (default 20)")
    p.add_argument("--output", required=True, help="output .dxf file")
    p.set_defaults(func=_cmd_gear)

    p = sub.add_parser("bracket", help="mounting plate with 4 holes")
    p.add_argument("--width", type=float, required=True,
                   help="plate width in mm")
    p.add_argument("--height", type=float, required=True,
                   help="plate height in mm")
    p.add_argument("--corner-radius", type=float, required=True,
                   help="rounded corner radius in mm")
    p.add_argument("--hole-dia", type=float, required=True,
                   help="hole diameter in mm")
    p.add_argument("--hole-margin", type=float, required=True,
                   help="distance from each edge to the hole centres in mm")
    p.add_argument("--output", required=True, help="output .dxf file")
    p.set_defaults(func=_cmd_bracket)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
