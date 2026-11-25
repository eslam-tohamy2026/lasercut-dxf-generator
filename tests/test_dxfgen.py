"""Tests for the LaserCut DXF Generator.

Run with:  .venv/bin/python tests/test_dxfgen.py
(also works under pytest: .venv/bin/python -m pytest tests/ -q)
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dxfgen.dxf import DxfDocument  # noqa: E402
from dxfgen.geometry import (  # noqa: E402
    box_mating_check,
    box_panels,
    bracket_outline,
    gear_outline,
)


def _bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def test_box_panels():
    panels = box_panels(100, 80, 60, 3)
    assert set(panels) == {"bottom", "front", "back", "left", "right", "top"}
    # each panel outline is a single closed polyline with many vertices
    for name, pts in panels.items():
        assert len(pts) >= 20, (name, len(pts))
    # bounding boxes are exactly the nominal face sizes (tabs flush)
    bb = _bbox(panels["bottom"])
    assert all(abs(a - b) < 1e-9 for a, b in zip(bb, (0.0, 0.0, 100.0, 80.0))), bb
    assert _bbox(panels["front"])[2] - _bbox(panels["front"])[0] == 100.0
    assert _bbox(panels["front"])[3] - _bbox(panels["front"])[1] == 60.0
    assert _bbox(panels["left"])[2] - _bbox(panels["left"])[0] == 80.0
    assert _bbox(panels["left"])[3] - _bbox(panels["left"])[1] == 60.0


def test_box_mating():
    assert box_mating_check(100, 80, 60, 3)
    assert box_mating_check(100, 80, 60, 3, kerf=0.2)
    assert box_mating_check(200, 150, 90, 5, kerf=0.15)
    assert box_mating_check(50, 50, 50, 3)
    assert box_mating_check(120, 90, 45, 4, kerf=0.3)


def test_box_kerf_changes_widths():
    # kerf widens tabs and narrows slots: segment boundaries must move
    from dxfgen.geometry import _edge_segments
    _, b0 = _edge_segments(100, 3, 0.0)
    _, b1 = _edge_segments(100, 3, 0.2)
    assert any(abs(a - b) > 1e-9 for a, b in zip(b0, b1))
    assert b1[0] == b0[0] and b1[-1] == b0[-1]  # edge length preserved


def test_box_validation():
    for bad in [dict(length=0, width=80, height=60, thickness=3),
                dict(length=100, width=80, height=60, thickness=40),
                dict(length=100, width=80, height=60, thickness=3, kerf=-0.1)]:
        try:
            box_panels(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def test_gear_diameters():
    outline, (bx, by, br) = gear_outline(2, 20, 8)
    assert (bx, by) == (0.0, 0.0) and br == 4.0
    radii = [math.hypot(x, y) for x, y in outline]
    assert abs(max(radii) - 22.0) < 0.01, max(radii)  # tip dia 44
    assert abs(min(radii) - 17.5) < 0.05, min(radii)  # root dia 35
    # pitch circle: flank points must pass near r=20
    near_pitch = [r for r in radii if abs(r - 20.0) < 0.5]
    assert len(near_pitch) >= 20
    # one tip arc per tooth: at least 20 points at (near) tip radius
    at_tip = [r for r in radii if abs(r - 22.0) < 0.01]
    assert len(at_tip) >= 20, len(at_tip)
    # outline is closed: the wrap segment (last -> first point) is one
    # root-arc step, ~1.1 mm here; the DXF marks the polyline closed.
    assert math.hypot(outline[0][0] - outline[-1][0],
                      outline[0][1] - outline[-1][1]) < 2.0


def test_gear_validation():
    for bad in [dict(module=2, teeth=5, bore=8),
                dict(module=2, teeth=20, bore=40),
                dict(module=0, teeth=20, bore=8),
                dict(module=2, teeth=20, bore=-1)]:
        try:
            gear_outline(**bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"expected ValueError for {bad}")


def test_gear_tooth_narrows_to_tip():
    """Engineering check: a real involute tooth is widest at the root
    and narrowest at the tip. Fold every outline point into the tooth
    centred at angle 0 and measure the angular half-width at the tip,
    pitch and base circles, against values re-derived here from the
    involute formula (independent of the generator code)."""
    module, teeth = 2, 20
    outline, _ = gear_outline(module, teeth, 8)
    r_pitch = module * teeth / 2.0
    r_base = r_pitch * math.cos(math.radians(20.0))
    r_tip = r_pitch + module
    half_tooth = math.pi / (2.0 * teeth)
    inv = lambda a: math.tan(a) - a
    inv_alpha = inv(math.radians(20.0))
    exp_tip = abs(-half_tooth + inv(math.acos(r_base / r_tip)) - inv_alpha)
    exp_root = abs(-half_tooth - inv_alpha)
    step = 2.0 * math.pi / teeth
    folded = []
    for x, y in outline:
        r = math.hypot(x, y)
        a = math.atan2(y, x)
        a = (a + step / 2) % step - step / 2
        folded.append((r, a))
    tip = max(abs(a) for r, a in folded if r > 21.95)  # tip arc only
    pitch = max(abs(a) for r, a in folded if 19.5 < r < 20.5)
    root = max(abs(a) for r, a in folded if 18.7 < r < 18.9)
    assert abs(tip - exp_tip) < 0.01, (tip, exp_tip)
    assert abs(pitch - half_tooth) < 0.01, (pitch, half_tooth)
    assert abs(root - exp_root) < 0.01, (root, exp_root)
    assert tip < pitch < root


def test_gear_small_and_large():
    outline, _ = gear_outline(3, 6, 0)
    radii = [math.hypot(x, y) for x, y in outline]
    assert abs(max(radii) - 12.0) < 0.01  # tip dia = 3*(6+2) = 24
    outline, _ = gear_outline(1, 60, 5)
    radii = [math.hypot(x, y) for x, y in outline]
    assert abs(max(radii) - 31.0) < 0.01  # tip dia = 1*(60+2) = 62


def test_bracket():
    outline, holes = bracket_outline(60, 40, 5, 5, 10)
    assert _bbox(outline) == (0.0, 0.0, 60.0, 40.0)
    assert len(holes) == 4
    assert holes[0] == (10.0, 10.0, 2.5)
    assert holes[1] == (50.0, 10.0, 2.5)
    assert holes[2] == (50.0, 30.0, 2.5)
    assert holes[3] == (10.0, 30.0, 2.5)
    # rounded corners: outline points exist strictly inside the bbox corners
    assert any(0 < x < 5 and 0 < y < 5 for x, y in outline)
    try:
        bracket_outline(60, 40, 30, 5, 10)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for huge corner radius")


def test_dxf_roundtrip():
    import ezdxf
    doc = DxfDocument()
    outline, (_, _, br) = gear_outline(2, 20, 8)
    doc.add_polyline(outline)
    doc.add_circle(0, 0, br)
    path = "/tmp/dxfgen-test-roundtrip.dxf"
    doc.write(path)
    msp = ezdxf.readfile(path).modelspace()
    types = [e.dxftype() for e in msp]
    assert types.count("LWPOLYLINE") == 1, types
    assert types.count("CIRCLE") == 1, types
    pl = next(e for e in msp if e.dxftype() == "LWPOLYLINE")
    assert pl.closed
    assert len(list(pl.vertices())) == len(outline)


TESTS = [v for k, v in sorted(globals().items())
         if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    failed = 0
    for fn in TESTS:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
        else:
            print(f"ok   {fn.__name__}")
    print(f"{len(TESTS) - failed}/{len(TESTS)} tests passed")
    raise SystemExit(1 if failed else 0)
