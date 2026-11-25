"""Minimal DXF R2000 (AC1015) ASCII writer.

Standard library only. Writes closed LWPOLYLINE entities and CIRCLE
entities on layer "0", in millimetres. The output is readable by
LightBurn, LaserCAD, AutoCAD and ezdxf. (R2000 is used because the
LWPOLYLINE entity type requires it; R12 only has POLYLINE/VERTEX.)
"""

from __future__ import annotations


def _fmt(value: float) -> str:
    """Format a coordinate with 3 decimals, avoiding -0.000."""
    if abs(value) < 0.0005:
        value = 0.0
    return f"{value:.3f}"


def _pair(code: int, value: str) -> list[str]:
    return [str(code), value]


class DxfDocument:
    """A tiny DXF R12 document: polylines + circles only."""

    def __init__(self) -> None:
        self._polylines: list[list[tuple[float, float]]] = []
        self._circles: list[tuple[float, float, float]] = []

    def add_polyline(self, points: list[tuple[float, float]]) -> None:
        """Add a closed polyline. Needs at least 3 points."""
        if len(points) < 3:
            raise ValueError("a polyline needs at least 3 points")
        self._polylines.append([(float(x), float(y)) for x, y in points])

    def add_circle(self, cx: float, cy: float, radius: float) -> None:
        """Add a circle entity."""
        if radius <= 0:
            raise ValueError("circle radius must be positive")
        self._circles.append((float(cx), float(cy), float(radius)))

    @property
    def entity_count(self) -> int:
        return len(self._polylines) + len(self._circles)

    def bounds(self) -> tuple[float, float, float, float]:
        """(min_x, min_y, max_x, max_y) over all entities."""
        xs: list[float] = []
        ys: list[float] = []
        for pts in self._polylines:
            for x, y in pts:
                xs.append(x)
                ys.append(y)
        for cx, cy, r in self._circles:
            xs.extend([cx - r, cx + r])
            ys.extend([cy - r, cy + r])
        if not xs:
            return (0.0, 0.0, 0.0, 0.0)
        return (min(xs), min(ys), max(xs), max(ys))

    def to_string(self) -> str:
        out: list[str] = []
        out += _pair(0, "SECTION")
        out += _pair(2, "HEADER")
        out += _pair(9, "$ACADVER")
        out += _pair(1, "AC1015")
        out += _pair(0, "ENDSEC")

        # --- TABLES: one linetype, layer 0, one text style, active VPORT.
        out += _pair(0, "SECTION")
        out += _pair(2, "TABLES")
        out += _pair(0, "TABLE")
        out += _pair(2, "VPORT")
        out += _pair(70, "1")
        out += _pair(0, "VPORT")
        out += _pair(2, "*ACTIVE")
        out += _pair(70, "0")
        out += _pair(10, "0.0")
        out += _pair(20, "0.0")
        out += _pair(11, "1.0")
        out += _pair(21, "1.0")
        out += _pair(12, "0.0")
        out += _pair(22, "0.0")
        out += _pair(13, "0.0")
        out += _pair(23, "0.0")
        out += _pair(14, "1.0")
        out += _pair(24, "1.0")
        out += _pair(15, "0.0")
        out += _pair(25, "0.0")
        out += _pair(16, "0.0")
        out += _pair(26, "0.0")
        out += _pair(36, "1.0")
        out += _pair(17, "0.0")
        out += _pair(27, "0.0")
        out += _pair(37, "0.0")
        out += _pair(40, "297.0")
        out += _pair(41, "1.0")
        out += _pair(42, "50.0")
        out += _pair(43, "0.0")
        out += _pair(44, "0.0")
        out += _pair(50, "0.0")
        out += _pair(51, "0.0")
        out += _pair(71, "0")
        out += _pair(72, "100")
        out += _pair(73, "1")
        out += _pair(74, "3")
        out += _pair(75, "0")
        out += _pair(76, "0")
        out += _pair(77, "0")
        out += _pair(78, "0")
        out += _pair(0, "ENDTAB")
        out += _pair(0, "TABLE")
        out += _pair(2, "LTYPE")
        out += _pair(70, "1")
        out += _pair(0, "LTYPE")
        out += _pair(2, "Continuous")
        out += _pair(70, "0")
        out += _pair(3, "Solid line")
        out += _pair(72, "65")
        out += _pair(73, "0")
        out += _pair(40, "0.0")
        out += _pair(0, "ENDTAB")
        out += _pair(0, "TABLE")
        out += _pair(2, "LAYER")
        out += _pair(70, "1")
        out += _pair(0, "LAYER")
        out += _pair(2, "0")
        out += _pair(70, "0")
        out += _pair(62, "7")
        out += _pair(6, "Continuous")
        out += _pair(0, "ENDTAB")
        out += _pair(0, "TABLE")
        out += _pair(2, "STYLE")
        out += _pair(70, "1")
        out += _pair(0, "STYLE")
        out += _pair(2, "STANDARD")
        out += _pair(70, "0")
        out += _pair(40, "0.0")
        out += _pair(41, "1.0")
        out += _pair(50, "0.0")
        out += _pair(71, "0")
        out += _pair(42, "2.5")
        out += _pair(3, "txt")
        out += _pair(4, "")
        out += _pair(0, "ENDTAB")
        out += _pair(0, "ENDSEC")

        out += _pair(0, "SECTION")
        out += _pair(2, "BLOCKS")
        out += _pair(0, "ENDSEC")

        out += _pair(0, "SECTION")
        out += _pair(2, "ENTITIES")
        for pts in self._polylines:
            out += _pair(0, "LWPOLYLINE")
            out += _pair(8, "0")
            out += _pair(100, "AcDbEntity")
            out += _pair(100, "AcDbPolyline")
            out += _pair(90, str(len(pts)))
            out += _pair(70, "1")  # closed
            for x, y in pts:
                out += _pair(10, _fmt(x))
                out += _pair(20, _fmt(y))
        for cx, cy, r in self._circles:
            out += _pair(0, "CIRCLE")
            out += _pair(8, "0")
            out += _pair(100, "AcDbEntity")
            out += _pair(100, "AcDbCircle")
            out += _pair(10, _fmt(cx))
            out += _pair(20, _fmt(cy))
            out += _pair(30, "0.0")
            out += _pair(40, _fmt(r))
        out += _pair(0, "ENDSEC")
        out += _pair(0, "EOF")
        return "\n".join(out) + "\n"

    def write(self, path: str) -> None:
        with open(path, "w", encoding="ascii") as fh:
            fh.write(self.to_string())
