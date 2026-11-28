"""Geometry generators: finger-joint box, involute spur gear, bracket.

All dimensions in millimetres. Every generator returns closed outlines
as lists of (x, y) points plus any circles, ready for the DXF writer.
All geometry is derived from first principles in this module.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _dedup(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Drop consecutive duplicate points (within 1e-9)."""
    out: list[tuple[float, float]] = []
    for pt in points:
        if not out or math.hypot(pt[0] - out[-1][0], pt[1] - out[-1][1]) > 1e-9:
            out.append(pt)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0],
                                   out[0][1] - out[-1][1]) <= 1e-9:
        out.pop()
    return out


def _arc(cx: float, cy: float, r: float, a0: float, a1: float,
         n: int) -> list[tuple[float, float]]:
    """Points along a circular arc from angle a0 to a1 (radians)."""
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n),
             cy + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


# ---------------------------------------------------------------------------
# finger-joint box
# ---------------------------------------------------------------------------

def finger_count(edge_length: float, thickness: float,
                 fingers: int | None = None) -> int:
    """Number of segments (odd, >= 3) for one finger-jointed edge.

    By default the count is picked automatically: target finger width
    is max(3 * thickness, 10 mm), forced odd so a tab-side edge starts
    and ends with a tab. Pass ``fingers`` to choose the count yourself
    (it must be odd and >= 3, and every finger must stay at least 2x
    the thickness wide, or the joint would be too fragile to cut).
    """
    if fingers is not None:
        if fingers < 3 or fingers % 2 == 0:
            raise ValueError(
                f"fingers must be an odd number >= 3, got {fingers}")
        if edge_length / fingers < 2.0 * thickness:
            raise ValueError(
                f"{fingers} fingers on a {edge_length:g} mm edge would "
                f"make fingers {edge_length / fingers:.2f} mm wide, "
                f"narrower than 2x the {thickness:g} mm thickness")
        return fingers
    target = max(3.0 * thickness, 10.0)
    n = int(edge_length // target)
    if n < 3:
        n = 3
    if n % 2 == 0:
        n += 1
    # keep every finger at least 2x the thickness wide
    while n > 3 and edge_length / n < 2.0 * thickness:
        n -= 2
    return n


def _edge_segments(edge_length: float, thickness: float,
                   kerf: float, fingers: int | None = None
                   ) -> tuple[list[bool], list[float]]:
    """Finger pattern for one edge.

    Returns (is_tab_per_segment, boundary_positions). Segment i spans
    boundaries[i] .. boundaries[i+1]. Tabs are widened by the kerf and
    slots narrowed by it, so the finished joint fits exactly; the two
    end boundaries stay fixed so the edge length is preserved.
    """
    n = finger_count(edge_length, thickness, fingers)
    w = edge_length / n
    if kerf < 0:
        raise ValueError("kerf must be >= 0")
    if kerf >= w:
        raise ValueError(
            f"kerf {kerf} mm is too large for finger width {w:.2f} mm")
    bounds = [i * w for i in range(n + 1)]
    bounds[0] = 0.0
    bounds[-1] = edge_length  # exact endpoints: no float drift
    for i in range(1, n):
        # boundary i separates segment i-1 (tab if i-1 even) and i.
        # A tab side of the boundary moves it towards the slot side.
        if (i - 1) % 2 == 0:  # left segment is a tab: widen it
            bounds[i] += kerf / 2.0
        else:  # left segment is a slot: narrow it
            bounds[i] -= kerf / 2.0
    is_tab = [(i % 2 == 0) for i in range(n)]
    return is_tab, bounds


def _panel_outline(width: float, height: float, thickness: float,
                   kerf: float, tab_edges: set[str],
                   flat_edges: frozenset[str] = frozenset(),
                   fingers: int | None = None
                   ) -> list[tuple[float, float]]:
    """Closed outline of one rectangular panel with finger joints.

    tab_edges names the edges whose even segments are tabs
    ("bottom", "right", "top", "left"); the other edges are the
    complementary slot side. Tabs sit flush on the nominal rectangle;
    slots recede inward by the material thickness. Edges named in
    flat_edges are drawn straight, with no fingers at all (used for
    the open top edge of an open box). ``fingers`` fixes the finger
    count on every jointed edge; by default it is chosen
    automatically from the edge length and thickness.
    """
    pts: list[tuple[float, float]] = []

    def edge(length: float, name: str):
        is_tab, bounds = _edge_segments(length, thickness, kerf, fingers)
        if name not in tab_edges:
            is_tab = [not t for t in is_tab]
        return is_tab, bounds

    # bottom edge: (0,0) -> (width,0), inward is +y
    if "bottom" in flat_edges:
        pts.append((0.0, 0.0))
        pts.append((width, 0.0))
    else:
        is_tab, b = edge(width, "bottom")
        for i, tab in enumerate(is_tab):
            x0, x1 = b[i], b[i + 1]
            if tab:
                pts.append((x0, 0.0))
                pts.append((x1, 0.0))
            else:
                pts.append((x0, 0.0))
                pts.append((x0, thickness))
                pts.append((x1, thickness))
                pts.append((x1, 0.0))
    # right edge: (width,0) -> (width,height), inward is -x
    if "right" in flat_edges:
        pts.append((width, 0.0))
        pts.append((width, height))
    else:
        is_tab, b = edge(height, "right")
        for i, tab in enumerate(is_tab):
            y0, y1 = b[i], b[i + 1]
            if tab:
                pts.append((width, y0))
                pts.append((width, y1))
            else:
                pts.append((width, y0))
                pts.append((width - thickness, y0))
                pts.append((width - thickness, y1))
                pts.append((width, y1))
    # top edge: (width,height) -> (0,height), inward is -y
    if "top" in flat_edges:
        pts.append((width, height))
        pts.append((0.0, height))
    else:
        is_tab, b = edge(width, "top")
        for i, tab in enumerate(is_tab):
            x0, x1 = b[i], b[i + 1]
            if tab:
                pts.append((width - x0, height))
                pts.append((width - x1, height))
            else:
                pts.append((width - x0, height))
                pts.append((width - x0, height - thickness))
                pts.append((width - x1, height - thickness))
                pts.append((width - x1, height))
    # left edge: (0,height) -> (0,0), inward is +x
    if "left" in flat_edges:
        pts.append((0.0, height))
        pts.append((0.0, 0.0))
    else:
        is_tab, b = edge(height, "left")
        for i, tab in enumerate(is_tab):
            y0, y1 = b[i], b[i + 1]
            if tab:
                pts.append((0.0, height - y0))
                pts.append((0.0, height - y1))
            else:
                pts.append((0.0, height - y0))
                pts.append((thickness, height - y0))
                pts.append((thickness, height - y1))
                pts.append((0.0, height - y1))
    return _dedup(pts)


# Which edges are the tab side for each panel. Every shared edge has
# exactly one tab side and one slot side, so all joints are complementary.
_PANEL_TABS: dict[str, set[str]] = {
    "bottom": {"bottom", "right", "top", "left"},
    "top": {"bottom", "right", "top", "left"},
    "front": {"left", "right"},
    "back": {"left", "right"},
    "left": set(),
    "right": set(),
}


def box_panels(length: float, width: float, height: float,
               thickness: float, kerf: float = 0.0,
               gap: float = 25.0, fingers: int | None = None,
               open_top: bool = False
               ) -> dict[str, list[tuple[float, float]]]:
    """Six finger-jointed panels of a closed box, laid out flat.

    Outer box size is exactly length x width x height. Panels are
    returned in panel-local coordinates translated into one row with
    ``gap`` mm between panels, so each panel is a clearly separate
    closed outline in the file — nothing is joined or touching.
    Keys: bottom, front, back, left, right, top.

    With ``open_top`` the box has no lid: five panels are returned
    (no "top" key) and the top edge of each side panel is straight
    instead of finger-jointed. ``fingers`` fixes the finger count on
    every jointed edge (odd, >= 3); by default it is chosen
    automatically from the edge length and thickness.
    """
    for name, value in (("length", length), ("width", width),
                        ("height", height), ("thickness", thickness)):
        if value <= 0:
            raise ValueError(f"{name} must be positive")
    if thickness >= min(length, width, height) / 2.0:
        raise ValueError("thickness is too large for the box size")
    if kerf < 0:
        raise ValueError("kerf must be >= 0")
    if gap < 0:
        raise ValueError("gap must be >= 0")

    sizes: dict[str, tuple[float, float]] = {
        "bottom": (length, width),
        "front": (length, height),
        "back": (length, height),
        "left": (width, height),
        "right": (width, height),
        "top": (length, width),
    }
    # Edges drawn straight instead of finger-jointed. Only the open
    # top edges of the side panels; every other edge keeps its joint.
    flat: dict[str, frozenset[str]] = {
        name: frozenset({"top"}) if open_top else frozenset()
        for name in ("front", "back", "left", "right")
    }
    names = ("bottom", "front", "back", "left", "right", "top")
    if open_top:
        names = ("bottom", "front", "back", "left", "right")
    panels: dict[str, list[tuple[float, float]]] = {}
    x = 0.0
    for name in names:
        w, h = sizes[name]
        outline = _panel_outline(w, h, thickness, kerf, _PANEL_TABS[name],
                                 flat_edges=flat.get(name, frozenset()),
                                 fingers=fingers)
        panels[name] = [(px + x, py) for px, py in outline]
        x += w + gap
    return panels


def box_mating_check(length: float, width: float, height: float,
                     thickness: float, kerf: float = 0.0,
                     fingers: int | None = None,
                     open_top: bool = False) -> bool:
    """Verify every shared box edge is complementary.

    For each pair of mating edges the segment widths must match and the
    tab/slot pattern must be exactly opposite.
    """
    sizes: dict[str, tuple[float, float]] = {
        "bottom": (length, width), "front": (length, height),
        "back": (length, height), "left": (width, height),
        "right": (width, height), "top": (length, width),
    }
    # (panel A, edge A, panel B, edge B, shared edge length)
    pairs = [
        ("bottom", "top", "front", "bottom", length),
        ("bottom", "bottom", "back", "bottom", length),
        ("bottom", "left", "left", "bottom", width),
        ("bottom", "right", "right", "bottom", width),
        ("top", "top", "front", "top", length),
        ("top", "bottom", "back", "top", length),
        ("top", "left", "left", "top", width),
        ("top", "right", "right", "top", width),
        ("front", "left", "left", "front", height),
        ("front", "right", "right", "front", height),
        ("back", "left", "left", "back", height),
        ("back", "right", "right", "back", height),
    ]
    for pa, ea, pb, eb, edge_len in pairs:
        if open_top and ("top" in (pa, pb)):
            continue  # no lid: nothing mates with a top panel
        ta, ba = _edge_segments(edge_len, thickness, kerf, fingers)
        tb, bb = _edge_segments(edge_len, thickness, kerf, fingers)
        if ea not in _PANEL_TABS[pa]:
            ta = [not t for t in ta]
        if eb not in _PANEL_TABS[pb]:
            tb = [not t for t in tb]
        if len(ta) != len(tb):
            return False
        for i, (a, b_) in enumerate(zip(ta, tb)):
            if a == b_:
                return False
            if abs((ba[i + 1] - ba[i]) - (bb[i + 1] - bb[i])) > 1e-9:
                return False
    return True


# ---------------------------------------------------------------------------
# involute spur gear
# ---------------------------------------------------------------------------

def _inv(angle: float) -> float:
    """Involute function inv(a) = tan(a) - a."""
    return math.tan(angle) - angle


def gear_outline(module: float, teeth: int, bore: float,
                 pressure_angle_deg: float = 20.0
                 ) -> tuple[list[tuple[float, float]], tuple[float, float, float]]:
    """True involute spur gear outline + bore circle.

    Returns (outline_points, (bore_cx, bore_cy, bore_radius)).
    The gear is centred on (0, 0). Pitch diameter = module * teeth,
    tip diameter = module * (teeth + 2), root diameter =
    module * (teeth - 2.5). Flanks are sampled involutes; below the
    base circle the flank continues as a radial line to the root.
    """
    if module <= 0:
        raise ValueError("module must be positive")
    if teeth < 6:
        raise ValueError("teeth must be at least 6")
    if bore < 0:
        raise ValueError("bore must be >= 0")
    if not 10.0 <= pressure_angle_deg <= 30.0:
        raise ValueError(
            "pressure angle must be between 10 and 30 degrees "
            "(standard values are 14.5, 20 and 25)")
    alpha = math.radians(pressure_angle_deg)
    r_pitch = module * teeth / 2.0
    r_base = r_pitch * math.cos(alpha)
    r_tip = r_pitch + module
    r_root = r_pitch - 1.25 * module
    if r_root <= 0:
        raise ValueError("module/teeth combination gives no root circle")
    if bore / 2.0 >= r_root:
        raise ValueError("bore is too large for the root circle")

    half_tooth = math.pi / (2.0 * teeth)  # half tooth angle at pitch circle
    inv_alpha = _inv(alpha)

    def flank_angle(radius: float, right: bool) -> float:
        """Polar angle of the flank point at the given radius.

        The involute unwinds so the tooth narrows towards the tip:
        |angle| grows towards the root and shrinks towards the tip.
        At the pitch radius the flank sits exactly at half the tooth
        thickness (+/- half_tooth).
        """
        a_rho = math.acos(min(1.0, r_base / radius))
        if right:
            return -half_tooth + _inv(a_rho) - inv_alpha
        return half_tooth - _inv(a_rho) + inv_alpha

    def flank_points(right: bool, upward: bool) -> list[tuple[float, float]]:
        r0 = max(r_root, r_base)
        n = 8
        radii = [r0 + (r_tip - r0) * i / n for i in range(n + 1)]
        pts = []
        for rho in radii:
            ang = flank_angle(rho, right)
            pts.append((rho * math.cos(ang), rho * math.sin(ang)))
        if r_root < r_base:
            # radial line from the root circle up to the base circle
            ang0 = flank_angle(r_base, right)
            pts.insert(0, (r_root * math.cos(ang0), r_root * math.sin(ang0)))
        return pts if upward else list(reversed(pts))

    def root_arc(a_from: float, a_to: float) -> list[tuple[float, float]]:
        # short arc along the root circle (a_to > a_from, small sweep)
        n = 3
        return [(r_root * math.cos(a_from + (a_to - a_from) * i / n),
                 r_root * math.sin(a_from + (a_to - a_from) * i / n))
                for i in range(n + 1)]

    def tip_arc(a_from: float, a_to: float) -> list[tuple[float, float]]:
        n = 4
        return [(r_tip * math.cos(a_from + (a_to - a_from) * i / n),
                 r_tip * math.sin(a_from + (a_to - a_from) * i / n))
                for i in range(n + 1)]

    outline: list[tuple[float, float]] = []
    step = 2.0 * math.pi / teeth
    # flank angles at the root (tooth-0 frame)
    a_r_root = flank_angle(max(r_root, r_base), right=True)
    a_l_root = flank_angle(max(r_root, r_base), right=False)
    if r_root < r_base:
        a_r_root = flank_angle(r_base, right=True)
        a_l_root = flank_angle(r_base, right=False)
    a_r_tip = flank_angle(r_tip, right=True)
    a_l_tip = flank_angle(r_tip, right=False)
    for i in range(teeth):
        c = math.cos(i * step)
        s = math.sin(i * step)

        def rot(pt: tuple[float, float]) -> tuple[float, float]:
            return (pt[0] * c - pt[1] * s, pt[0] * s + pt[1] * c)

        right_up = flank_points(right=True, upward=True)
        left_down = flank_points(right=False, upward=False)
        if i == 0:
            # first tooth: start the outline at its right-flank root
            outline.extend(rot(p) for p in right_up)
        else:
            # root arc between teeth, in absolute angles (no rotation)
            arc = root_arc(a_l_root + (i - 1) * step, a_r_root + i * step)
            outline.extend(arc[1:])
            outline.extend(rot(p) for p in right_up[1:])
        # tip arc: right tip -> left tip
        arc = tip_arc(a_r_tip, a_l_tip)
        outline.extend(rot(p) for p in arc[1:])
        # left flank down
        outline.extend(rot(p) for p in left_down[1:])
    # close the root gap between the last tooth and the first
    closing = root_arc(a_l_root + (teeth - 1) * step, a_r_root + 2.0 * math.pi)
    outline.extend(closing[1:])  # last point duplicates the first; _dedup drops it
    return _dedup(outline), (0.0, 0.0, bore / 2.0)


# ---------------------------------------------------------------------------
# bracket (mounting plate with rounded corners and holes)
# ---------------------------------------------------------------------------

def bracket_outline(width: float, height: float, corner_radius: float,
                    hole_diameter: float, hole_margin: float
                    ) -> tuple[list[tuple[float, float]],
                               list[tuple[float, float, float]]]:
    """Rounded-rectangle plate + 4 mounting holes.

    Returns (outline_points, [(cx, cy, radius), ...]).
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if corner_radius <= 0 or corner_radius > min(width, height) / 2.0:
        raise ValueError("corner_radius must be in (0, min(w,h)/2]")
    if hole_diameter <= 0:
        raise ValueError("hole_diameter must be positive")
    if hole_margin - hole_diameter / 2.0 < 1.0:
        raise ValueError("holes must sit at least 1 mm inside the edges")
    if hole_margin + hole_diameter / 2.0 > min(width, height) / 2.0:
        raise ValueError("holes do not fit inside the plate")

    r = corner_radius
    pts: list[tuple[float, float]] = []
    # bottom edge, then corners counter-clockwise
    pts.append((r, 0.0))
    pts.append((width - r, 0.0))
    pts.extend(_arc(width - r, r, r, -math.pi / 2, 0.0, 8)[1:])
    pts.append((width, height - r))
    pts.extend(_arc(width - r, height - r, r, 0.0, math.pi / 2, 8)[1:])
    pts.append((r, height))
    pts.extend(_arc(r, height - r, r, math.pi / 2, math.pi, 8)[1:])
    pts.append((0.0, r))
    pts.extend(_arc(r, r, r, math.pi, 3 * math.pi / 2, 8)[1:])
    outline = _dedup(pts)
    hr = hole_diameter / 2.0
    holes = [
        (hole_margin, hole_margin, hr),
        (width - hole_margin, hole_margin, hr),
        (width - hole_margin, height - hole_margin, hr),
        (hole_margin, height - hole_margin, hr),
    ]
    return outline, holes
