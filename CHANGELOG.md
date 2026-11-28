# Changelog

## 2.0.0 — 2026-11-28

- Box layout: panels are now 25 mm apart by default (was 10 mm), so the
  six panels are unmistakably six separate closed outlines in the file
  and in every preview. Panel spacing is adjustable with `--gap`.
- Open-top box: `--open` builds a five-panel box with no lid and
  straight top edges on the side panels.
- Finger control: `--fingers N` fixes the finger count on every
  jointed edge (odd, >= 3); the automatic count is unchanged otherwise.
- Inches: `--units in` accepts dimensions in inches on every command;
  files are still written in millimetres.
- SVG output: `--format svg`, or just name the output file `.svg`.
  Same geometry as the DXF, with the y axis flipped so it is not a
  mirror image.
- DXF header now declares millimetres (`$INSUNITS = 4`,
  `$MEASUREMENT = 1`) plus the file extents, so CAD and laser software
  open the file at the right scale instead of guessing.
- Gear pressure angle is validated (10–30°; standard 14.5, 20, 25) —
  meaningless angles used to write a file with nonsense geometry.
- CLI errors are one-line messages with exit code 2: a missing output
  folder no longer dumps a Python traceback.
- Previews re-rendered: labelled, filled, high resolution, with the
  key dimensions printed on each image.
- README: honest comparison with boxes.py and MakerCase, and a note
  that the box panels are separate closed outlines.
- Test suite grew from 10 to 21 checks, including the new options,
  the SVG writer and the DXF header.

## 1.0.0 — 2026-11-25

- Finger-joint box generator: 6 panels, complementary joints, exact outer size, kerf compensation.
- True involute spur gear generator: 20° pressure angle, correct pitch/root/tip diameters, centre bore.
- Mounting bracket generator: rounded corners, 4 holes.
- Pure Python, zero dependencies; DXF R2000 output readable by LightBurn, LaserCAD and AutoCAD.
- Example DXFs + PNG previews in `examples/`, all verified by an independent ezdxf round-trip check.
- Test suite (`tests/test_dxfgen.py`, 10 checks) including an independent re-derivation of the involute tooth geometry.
