# cad-3d

Parametric, code-first CAD with [CadQuery](https://cadquery.readthedocs.io/en/latest/) — desk accessories modeled in Python, not clicked in a GUI. Every model is a script: edit the parameters at the top, re-run, re-export STL/STEP.

> **Models are code; exports are build artifacts.** `out/` (generated STL/STEP) and `reference/` (downloaded models used only for measuring) are gitignored.

## Models

| Script | What it is |
| --- | --- |
| [`garmin_station.py`](garmin_station.py) | **Garmin desk dock (V3)** — one billet block holding an Edge 1050 (landscape in a back slot), a Varia RCT715, and an HRM 600 pod, with a flush two-color GARMIN inlay. Composition studied from the "Garmin Station V2" reference, rebuilt original for these devices. |
| [`garmin_station_v4.py`](garmin_station_v4.py) | **Garmin band-holster dock (V4)** — a 4-device variant: Varia UT800 + RCT715 lights grouped left, Edge 1050 towering portrait on the right, and the back slot reworked into an HRM 600 **band holster** with the pod showing through a centered U-notch. Also exports standalone **fit-test coupons** for the Edge niche (friction-well and claw styles) so you can dial the fit on a small fast print. |
| [`macbook_claw.py`](macbook_claw.py) | **MacBook clamshell holder** — a hand-shaped claw that wedges the lid cracked open (~20 mm) so the lid-closed sensor never sleeps the machine. Four fingers over the lid, a thumb clasping under the base. |
| [`main.py`](main.py) | Starter model — a parametric mounting plate (rounded corners, 4× M4 counterbores). Good first thing to run. |

### Devices (verified dimensions)

| Device | Dimensions (mm) | Role |
| --- | --- | --- |
| Garmin Edge 1050 | 60.2 × 118.5 × 16.3 | bike computer |
| Varia RCT715 | 106.5 × 42.0 × 31.9 | rear radar/taillight |
| Varia UT800 | 96.6 × 33.5 × 29.7 (44.7 deep w/ mount flange) | front headlight |
| HRM 600 | 68.0 × 31.6 × 10.0 | heart-rate pod + strap |

## Quick start

```bash
uv run garmin_station_v4.py          # build + export STL/STEP to out/
MOCKUP=1 uv run garmin_station_v4.py # also export ghost device stand-ins for renders
uv run garmin_station.py             # the V3 dock
uv run macbook_claw.py               # the MacBook claw
uv run main.py                       # starter mounting plate
```

Each run writes to `out/`:

- `*_body.stl` + `*_logo.stl` — two-body pair for multi-color printing
- `*.stl` — single-color merged fallback
- `*.step` — lossless CAD interchange
- `garmin_station_v4_edgetest.stl` / `_edgeclaw.stl` — small Edge-niche fit coupons

## Multi-color logo (Bambu Studio)

The GARMIN wordmark is a separate solid cut from the body at zero clearance (sliced together, not assembled):

1. Import `garmin_station_v4_body.stl`.
2. Right-click → **Add Part** → `garmin_station_v4_logo.stl` (keeps it in the same coordinate frame).
3. Assign a filament per part (dark body, light logo).

## Live editing & verification

- **CQ-editor** for live preview: `cq-editor garmin_station_v4.py` (F5 re-renders; the scripts expose `show_object` hooks).
- The repo's working loop is **render-and-look**: after any geometry change, offscreen-render the STL from a few angles (via the `vtk` that ships with CadQuery) and inspect the PNGs. This catches broken booleans that bounding boxes miss — see [`CLAUDE.md`](CLAUDE.md) for the pattern and the hard-won OCC gotchas.

## Stack

- Python **3.12** (pinned in `.python-version` — CadQuery's OCP wheels lag the latest Python)
- [uv](https://docs.astral.sh/uv/) for env + deps (`uv add <pkg>` to extend)

## Notes on reference models

`reference/` holds third-party models downloaded only for **measuring** — they are never committed or redistributed (some carry no-derivatives licenses). The designs here are original builds sized from device specs, studied from references rather than remixed.
