"""Command-line interface for the LaserCut DXF Generator.

Examples:
    python -m dxfgen box --length 100 --width 80 --height 60 \\
        --thickness 3 --output box.dxf
    python -m dxfgen box --length 4 --width 3 --height 2.5 \\
        --thickness 0.125 --units in --output box.dxf
    python -m dxfgen gear --module 2 --teeth 20 --bore 8 \\
        --output gear.dxf
    python -m dxfgen gear --module 2 --teeth 20 --bore 8 \\
        --output gear.svg
    python -m dxfgen bracket --width 60 --height 40 --corner-radius 5 \\
        --hole-dia 5 --hole-margin 10 --output bracket.dxf
"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__
from .dxf import DxfDocument
from .geometry import box_panels, bracket_outline, gear_outline
from .svg import SvgDocument

MM_PER_INCH = 25.4
BOX_PANEL_ORDER = ("bottom", "front", "back", "left", "right", "top")


def _to_mm(value: float, units: str) -> float:
    """Convert a user-supplied length to millimetres."""
    if units == "in":
        return value * MM_PER_INCH
    if units != "mm":
        raise ValueError(f"unknown units {units!r} (use mm or in)")
    return value


def _resolve_format(output: str, fmt: str | None) -> str:
    """Output format: explicit --format wins, otherwise the file
    extension decides (.svg -> SVG, anything else -> DXF)."""
    if fmt is not None:
        return fmt
    if os.path.splitext(output)[1].lower() == ".svg":
        return "svg"
    return "dxf"


def _emit(polylines: list[list[tuple[float, float]]],
          circles: list[tuple[float, float, float]],
          output: str, fmt: str) -> DxfDocument | SvgDocument:
    """Write the geometry as DXF or SVG and print the summary."""
    if fmt == "svg":
        doc: DxfDocument | SvgDocument = SvgDocument()
    elif fmt == "dxf":
        doc = DxfDocument()
    else:
        raise ValueError(f"unknown format {fmt!r} (use dxf or svg)")
    for pts in polylines:
        doc.add_polyline(pts)
    for cx, cy, r in circles:
        doc.add_circle(cx, cy, r)
    doc.write(output)
    min_x, min_y, max_x, max_y = doc.bounds()
    print(f"wrote {output} ({fmt.upper()})")
    print(f"entities: {doc.entity_count}")
    print(f"size: {max_x - min_x:.2f} x {max_y - min_y:.2f} mm "
          f"({min_x:.2f},{min_y:.2f}) to ({max_x:.2f},{max_y:.2f})")
    return doc


def _add_common(p: argparse.ArgumentParser) -> None:
    """Options shared by every generator subcommand."""
    p.add_argument("--units", choices=("mm", "in"), default="mm",
                   help="units for every length you pass in "
                        "(default mm); the file itself is always "
                        "written in millimetres")
    p.add_argument("--format", choices=("dxf", "svg"), default=None,
                   help="output format (default: taken from the "
                        "output file extension, .svg for SVG, "
                        "otherwise DXF)")
    p.add_argument("--output", required=True,
                   help="output file (.dxf or .svg)")


def _cmd_box(args: argparse.Namespace) -> int:
    length = _to_mm(args.length, args.units)
    width = _to_mm(args.width, args.units)
    height = _to_mm(args.height, args.units)
    thickness = _to_mm(args.thickness, args.units)
    kerf = _to_mm(args.kerf, args.units)
    # the default gap is 25 mm whatever the input units are; an
    # explicit --gap is in the input units like every other length
    gap = 25.0 if args.gap is None else _to_mm(args.gap, args.units)
    panels = box_panels(length, width, height, thickness, kerf=kerf,
                        gap=gap, fingers=args.fingers,
                        open_top=args.open)
    order = BOX_PANEL_ORDER if not args.open else BOX_PANEL_ORDER[:5]
    fmt = _resolve_format(args.output, args.format)
    _emit([panels[name] for name in order], [], args.output, fmt)
    style = "open-top" if args.open else "closed"
    print(f"box {length:g} x {width:g} x {height:g} mm ({style}), "
          f"thickness {thickness:g} mm, kerf {kerf:g} mm, "
          f"panel gap {gap:g} mm")
    if args.units == "in":
        print(f"(entered in inches: {args.length:g} x {args.width:g} x "
              f"{args.height:g} in, {args.thickness:g} in material)")
    return 0


def _cmd_gear(args: argparse.Namespace) -> int:
    module = _to_mm(args.module, args.units)
    bore = _to_mm(args.bore, args.units)
    outline, (bx, by, br) = gear_outline(
        module, args.teeth, bore,
        pressure_angle_deg=args.pressure_angle)
    fmt = _resolve_format(args.output, args.format)
    _emit([outline], [(bx, by, br)] if br > 0 else [], args.output, fmt)
    print(f"spur gear: module {module:g}, {args.teeth} teeth, "
          f"pitch dia {module * args.teeth:.2f} mm, "
          f"tip dia {module * (args.teeth + 2):.2f} mm, "
          f"bore {bore:g} mm")
    if args.units == "in":
        print(f"(entered in inches: module {args.module:g} in, "
              f"bore {args.bore:g} in)")
    return 0


def _cmd_bracket(args: argparse.Namespace) -> int:
    width = _to_mm(args.width, args.units)
    height = _to_mm(args.height, args.units)
    corner_radius = _to_mm(args.corner_radius, args.units)
    hole_dia = _to_mm(args.hole_dia, args.units)
    hole_margin = _to_mm(args.hole_margin, args.units)
    outline, holes = bracket_outline(
        width, height, corner_radius, hole_dia, hole_margin)
    fmt = _resolve_format(args.output, args.format)
    _emit([outline], holes, args.output, fmt)
    print(f"bracket {width:g} x {height:g} mm, "
          f"corner radius {corner_radius:g} mm, "
          f"{len(holes)} holes dia {hole_dia:g} mm")
    if args.units == "in":
        print(f"(entered in inches: {args.width:g} x {args.height:g} in)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dxfgen",
        description="Generate ready-to-cut DXF/SVG files for laser "
                    "cutting & CNC. Pure Python, zero dependencies.")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("box", help="finger-joint box (6 panels)")
    p.add_argument("--length", type=float, required=True,
                   help="outer length")
    p.add_argument("--width", type=float, required=True,
                   help="outer width")
    p.add_argument("--height", type=float, required=True,
                   help="outer height")
    p.add_argument("--thickness", type=float, required=True,
                   help="material thickness")
    p.add_argument("--kerf", type=float, default=0.0,
                   help="laser kerf (default 0); widens tabs and "
                        "narrows slots so the finished joint fits exactly")
    p.add_argument("--gap", type=float, default=None,
                   help="space between panels in the flat layout "
                        "(default 25 mm); use a smaller value to save "
                        "material, 0 to pack the panels edge to edge")
    p.add_argument("--fingers", type=int, default=None,
                   help="finger count per jointed edge (odd, >= 3); "
                        "by default the count is picked automatically "
                        "from the edge length and thickness")
    p.add_argument("--open", action="store_true",
                   help="open-top box: no lid, and the top edge of "
                        "each side panel is straight")
    _add_common(p)
    p.set_defaults(func=_cmd_box)

    p = sub.add_parser("gear", help="involute spur gear")
    p.add_argument("--module", type=float, required=True,
                   help="gear module (pitch diameter = module x teeth)")
    p.add_argument("--teeth", type=int, required=True,
                   help="number of teeth (>= 6)")
    p.add_argument("--bore", type=float, required=True,
                   help="centre bore diameter (0 for none)")
    p.add_argument("--pressure-angle", type=float, default=20.0,
                   help="pressure angle in degrees, 10-30 (default 20; "
                        "standard values are 14.5, 20 and 25)")
    _add_common(p)
    p.set_defaults(func=_cmd_gear)

    p = sub.add_parser("bracket", help="mounting plate with 4 holes")
    p.add_argument("--width", type=float, required=True,
                   help="plate width")
    p.add_argument("--height", type=float, required=True,
                   help="plate height")
    p.add_argument("--corner-radius", type=float, required=True,
                   help="rounded corner radius")
    p.add_argument("--hole-dia", type=float, required=True,
                   help="hole diameter")
    p.add_argument("--hole-margin", type=float, required=True,
                   help="distance from each edge to the hole centres")
    _add_common(p)
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
    except OSError as exc:
        # e.g. the output folder does not exist, or is not writable:
        # a plain message, not a traceback.
        print(f"error: cannot write output file: {exc.strerror or exc}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
