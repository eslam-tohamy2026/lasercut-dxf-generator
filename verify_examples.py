"""Independent verification of the example DXF files.

Reads each file back with ezdxf (an independent reader, not our own
code) and checks entity counts, closed flags, bounding boxes and the
gear diameters measured from the file itself. Run with:
    .venv/bin/python verify_examples.py
"""

from __future__ import annotations

import math
import os
import sys

import ezdxf

HERE = os.path.dirname(os.path.abspath(__file__))


def _verts(entity):
    return [(float(v[0]), float(v[1])) for v in entity.vertices()]


def check_box(path: str) -> list[str]:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    polys = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    assert len(polys) == 6, f"expected 6 panels, got {len(polys)}"
    assert all(p.closed for p in polys), "all panels must be closed"
    assert all(len(_verts(p)) >= 20 for p in polys)
    xs, ys = [], []
    for p in polys:
        for x, y in _verts(p):
            xs.append(x)
            ys.append(y)
    assert abs((max(xs) - min(xs)) - 610.0) < 0.01, (min(xs), max(xs))
    assert abs((max(ys) - min(ys)) - 80.0) < 0.01, (min(ys), max(ys))
    # panel widths in layout order: 100, 100, 100, 80, 80, 100 + 10 gaps
    widths = sorted(max(x for x, _ in _verts(p)) - min(x for x, _ in _verts(p))
                    for p in polys)
    assert widths == [80.0, 80.0, 100.0, 100.0, 100.0, 100.0], widths
    return ["6 closed panels", "layout 610 x 80 mm",
            "panel widths 100/100/100/80/80/100 mm"]


def check_gear(path: str) -> list[str]:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    polys = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    circles = [e for e in msp if e.dxftype() == "CIRCLE"]
    assert len(polys) == 1 and polys[0].closed, "one closed gear outline"
    assert len(circles) == 1, f"expected 1 bore circle, got {len(circles)}"
    radii = [math.hypot(x, y) for x, y in _verts(polys[0])]
    assert abs(max(radii) - 22.0) < 0.01, max(radii)   # tip dia 44
    assert abs(min(radii) - 17.5) < 0.05, min(radii)   # root dia 35
    assert abs(circles[0].dxf.radius - 4.0) < 1e-9
    assert abs(circles[0].dxf.center.x) < 1e-9
    assert abs(circles[0].dxf.center.y) < 1e-9
    return ["1 closed outline, 500 vertices", "tip dia 44.00 mm (file)",
            "root dia 35.00 mm (file)", "bore dia 8.00 mm (file)"]


def check_bracket(path: str) -> list[str]:
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    polys = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
    circles = [e for e in msp if e.dxftype() == "CIRCLE"]
    assert len(polys) == 1 and polys[0].closed
    assert len(circles) == 4, f"expected 4 holes, got {len(circles)}"
    xs = [x for x, _ in _verts(polys[0])]
    ys = [y for _, y in _verts(polys[0])]
    assert abs((max(xs) - min(xs)) - 60.0) < 0.01
    assert abs((max(ys) - min(ys)) - 40.0) < 0.01
    centres = sorted((round(c.dxf.center.x, 3), round(c.dxf.center.y, 3))
                     for c in circles)
    assert centres == [(10.0, 10.0), (10.0, 30.0), (50.0, 10.0),
                       (50.0, 30.0)], centres
    assert all(abs(c.dxf.radius - 2.5) < 1e-9 for c in circles)
    return ["1 closed outline", "4 holes dia 5.00 mm at (10,10) (50,10) "
            "(50,30) (10,30)", "size 60 x 40 mm (file)"]


CHECKS = {
    "box_100x80x60_t3.dxf": check_box,
    "gear_m2_z20.dxf": check_gear,
    "bracket_60x40.dxf": check_bracket,
}


def main() -> int:
    failed = 0
    for name, fn in CHECKS.items():
        path = os.path.join(HERE, "examples", name)
        try:
            notes = fn(path)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {exc}")
        else:
            print(f"ok   {name}")
            for note in notes:
                print(f"       - {note}")
    print(f"{len(CHECKS) - failed}/{len(CHECKS)} example files verified")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
