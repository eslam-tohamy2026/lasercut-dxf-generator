# LaserCut DXF Generator

Generate ready-to-cut DXF files for laser cutting & CNC: finger-joint boxes, involute spur gears, brackets. Pure Python, zero dependencies.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Version 2.0.0](https://img.shields.io/badge/version-2.0.0-green.svg)]()

> A zero-dependency Python CLI that generates finger-joint boxes, true involute spur gears and brackets as ready-to-cut DXF or SVG files, with kerf compensation. No install, no account, no internet needed — it runs offline from a single folder.

![Finger-joint box panels](examples/box_100x80x60_t3.png)
![Involute spur gear, module 2, 20 teeth](examples/gear_m2_z20.png)
![Mounting bracket with 4 holes](examples/bracket_60x40.png)

## Download a ready-made DXF — no install needed

Just want to cut something right now? Download a finished file and open it in LightBurn, LaserCAD or AutoCAD:

- [box_100x80x60_t3.dxf](examples/box_100x80x60_t3.dxf) — finger-joint box 100 × 80 × 60 mm, 3 mm material
- [gear_m2_z20.dxf](examples/gear_m2_z20.dxf) — involute spur gear, module 2, 20 teeth, 8 mm bore
- [bracket_60x40.dxf](examples/bracket_60x40.dxf) — mounting bracket 60 × 40 mm, 4 holes Ø 5 mm

## Quickstart

```bash
git clone https://github.com/eslam-tohamy2026/lasercut-dxf-generator.git
cd lasercut-dxf-generator
python -m dxfgen box --length 100 --width 80 --height 60 --thickness 3 --output box.dxf
python -m dxfgen gear --module 2 --teeth 20 --bore 8 --output gear.dxf
```

No dependencies, no build step, no install. Python 3.9 or newer is all you need.

## Features

- **Finger-joint box** — six panels laid out flat in one file, 25 mm apart, each one a separate closed outline (nothing is joined in the file). Joints that actually fit: every shared edge is complementary (tab meets slot), and the finished box measures exactly the size you asked for. Open-top version with `--open`, your own finger count with `--fingers`, panel spacing with `--gap`.
- **True involute spur gear** — real involute flanks (20° pressure angle, 14.5° and 25° also supported), correct pitch, root and tip diameters, centre bore. Not a circle with bumps.
- **Mounting bracket** — rounded-corner plate with four evenly spaced holes.
- **Kerf compensation** — the laser burns away a thin line of material while cutting. Pass `--kerf` and the tool widens the tabs and narrows the slots by exactly that amount, so the finished joint fits first time instead of rattling loose.
- **Millimetres or inches** — pass `--units in` and give dimensions in inches; the file is still written in millimetres, so it opens at the right size everywhere.
- **DXF or SVG output** — DXF R2000 (AC1015) with the header declaring millimetres (`$INSUNITS = 4`), or SVG for Inkscape and other vector workflows. Use `--format svg` or just name the file `.svg`.
- **Clean DXF output** — closed polylines on layer 0, millimetres. Opens in LightBurn, LaserCAD, AutoCAD, LibreCAD and FreeCAD.
- **Verified output** — every example file is read back and checked automatically (see `verify_examples.py`); the test suite re-derives the gear geometry from the involute formula independently.

## Usage

### Box

```bash
python -m dxfgen box --length 100 --width 80 --height 60 --thickness 3 --output box.dxf
```

| Option | Meaning |
|---|---|
| `--length` | Outer length |
| `--width` | Outer width |
| `--height` | Outer height |
| `--thickness` | Material thickness |
| `--kerf` | Laser kerf (default 0) |
| `--gap` | Space between panels in the flat layout (default 25 mm); smaller saves material, 0 packs panels edge to edge |
| `--fingers` | Finger count per jointed edge (odd, ≥ 3); by default the count is picked automatically from the edge length and thickness |
| `--open` | Open-top box: no lid, and the top edge of each side panel is straight |
| `--units` | `mm` (default) or `in` — the units your numbers are in |
| `--format` | `dxf` (default) or `svg`; if omitted, the output file extension decides |
| `--output` | Output file (`.dxf` or `.svg`) |

Finger count per edge is chosen automatically (target finger width is max(3× thickness, 10 mm), always an odd count so the pattern starts and ends with a tab). Pass `--fingers` when you want a specific count — for example `--fingers 5` on every edge.

The six panels are laid out in one row, 25 mm apart, in this order: bottom, front, back, left, right, top. Each panel is its own closed outline in the file, so in LightBurn or CAD you can move, delete or re-nest them independently — nothing is joined or touching. With `--open` there are five panels and no lid.

More box examples — inches, and an open-top tray:

```bash
python -m dxfgen box --length 4 --width 3 --height 2.5 --thickness 0.125 --units in --output box.dxf
python -m dxfgen box --length 100 --width 80 --height 60 --thickness 3 --open --output tray.dxf
```

### Gear

```bash
python -m dxfgen gear --module 2 --teeth 20 --bore 8 --output gear.dxf
```

| Option | Meaning |
|---|---|
| `--module` | Gear module (pitch diameter = module × teeth) |
| `--teeth` | Number of teeth (≥ 6) |
| `--bore` | Centre bore diameter (0 for none) |
| `--pressure-angle` | Pressure angle in degrees, 10–30 (default 20; standard values are 14.5, 20 and 25) |
| `--units` | `mm` (default) or `in` |
| `--format` | `dxf` (default) or `svg` |
| `--output` | Output file (`.dxf` or `.svg`) |

Tip diameter = module × (teeth + 2), root diameter = module × (teeth − 2.5).

### Bracket

```bash
python -m dxfgen bracket --width 60 --height 40 --corner-radius 5 --hole-dia 5 --hole-margin 10 --output bracket.dxf
```

| Option | Meaning |
|---|---|
| `--width` | Plate width |
| `--height` | Plate height |
| `--corner-radius` | Rounded corner radius |
| `--hole-dia` | Hole diameter |
| `--hole-margin` | Distance from each edge to the hole centres |
| `--units` | `mm` (default) or `in` |
| `--format` | `dxf` (default) or `svg` |
| `--output` | Output file (`.dxf` or `.svg`) |

Run `python -m dxfgen --help` or `python -m dxfgen <command> --help` for the full options.

## How this compares with boxes.py and MakerCase

Two excellent tools already exist, and this one does not try to replace them — it covers the cases they make awkward:

| | This tool | boxes.py | MakerCase |
|---|---|---|---|
| Box styles | Closed or open-top finger-joint box | 120+ generators: lids, trays, dividers, living hinges, racks, Gridfinity… | Simple, polygon, rounded, divider, hinged, curved boxes |
| Other parts | Involute spur gear, mounting bracket | Gears, pulleys, NEMA mounts, knobs and more | Boxes only |
| Runs | Offline CLI, zero dependencies | Web app, Docker, or local install | Web app (needs internet) |
| Output | DXF (with mm declared in the header) or SVG, straight into LightBurn | SVG natively; DXF needs the external pstoedit helper | SVG, DXF, PDF, 3MF |
| Units | mm or inches (`--units in`) | mm (convert inches yourself) | mm or inches |
| Finger control | Automatic, or your exact count (`--fingers`) | Finger size in settings | Fixed finger widths |
| Preview | Labelled PNGs of the exact files (see above) | Web preview | Live 3D preview |

Pick **boxes.py** when you need a special box — a sliding lid, a living hinge, a tray insert. Pick **MakerCase** when you want to see a 3D preview before cutting. Pick **this tool** when you want a file from the command line with nothing to install, in inches if that is how you work, as DXF that opens at the right scale, or when you also need a gear or a bracket from the same tool.

## Kerf, in plain language

A laser doesn't cut a zero-width line — it burns away a strip of material about as wide as the beam (the *kerf*, typically 0.1–0.3 mm depending on the machine and material). If you cut a tab and a slot at exactly the same drawn size, the finished tab comes out thinner and the slot comes out wider, so the joint is loose. This tool compensates: with `--kerf 0.2`, tabs are drawn 0.2 mm wider and slots 0.2 mm narrower, so after the laser takes its share both come out at exactly the size you asked for. Measure your machine's kerf once (cut a 20 mm square and measure it) and reuse the number.

## Need a custom part designed for production?

Hire me on Fiverr: https://www.fiverr.com/eslam_engineer — SolidWorks 3D modelling, PDF/sketch → AutoCAD DWG & DXF, CNC/laser-cut files ready for production, Excel VBA automation.

## Contributing

Found a problem or want another generator? Open an issue with the command you ran and the measurements you expected. Pull requests are welcome — please add a test for new geometry and run the suite first:

```bash
.venv/bin/python tests/test_dxfgen.py   # 21 checks, all must pass
.venv/bin/python verify_examples.py    # independent ezdxf round-trip check
```

## Licence

MIT — see [LICENSE](LICENSE). Free for personal and commercial use.
