# Changelog

## 1.0.0 — 2026-11-25

- Finger-joint box generator: 6 panels, complementary joints, exact outer size, kerf compensation.
- True involute spur gear generator: 20° pressure angle, correct pitch/root/tip diameters, centre bore.
- Mounting bracket generator: rounded corners, 4 holes.
- Pure Python, zero dependencies; DXF R2000 output readable by LightBurn, LaserCAD and AutoCAD.
- Example DXFs + PNG previews in `examples/`, all verified by an independent ezdxf round-trip check.
- Test suite (`tests/test_dxfgen.py`, 10 checks) including an independent re-derivation of the involute tooth geometry.
