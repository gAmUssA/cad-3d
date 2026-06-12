# cad-3d — CadQuery project notes

Parametric code-CAD with [CadQuery](https://cadquery.readthedocs.io/en/latest/). Python 3.12 (pinned — CadQuery's OCP wheels lag latest Python), uv-managed.

## Commands

```bash
uv run garmin_station.py          # build + export STL/STEP to out/
MOCKUP=1 uv run garmin_station.py # also export device stand-ins for renders
uv run main.py                    # starter model (parametric mounting plate)
cq-editor garmin_station.py       # live preview GUI (uv tool, Python 3.12), F5 = re-render
```

`out/` and `reference/` are gitignored. Exports are build artifacts — models are code.

## Visual verification loop (IMPORTANT — always do this)

Never trust booleans blind: render the STL and LOOK at it after every geometry change.
vtk ships as a cadquery dependency — offscreen render pattern:

```python
# uv run - <<'EOF' ... render out/foo.stl from 2-3 camera angles to PNGs
reader = vtk.vtkSTLReader(); ... win.SetOffScreenRendering(1) ...
```

Then Read the PNGs. This loop caught every real bug in this project (broken backrest,
misplaced arch, through-cuts). Multi-actor renders (body + logo + ghosted device
mockups in different colors) are how design intent gets communicated to the user.

## CadQuery gotchas learned here (the hard way)

- **Point arrays**: it's `.rarray(xSpacing, ySpacing, nx, ny)`, not `rectArray`.
- **Leaning geometry must be positive geometry.** Cutting a leaned slab through a
  vertical panel eats the panel's top (the slab walks backward as z rises). Build
  leaning backrests/cradles as rotated solids and union them; a leaning panel of
  height h needs `h*tan(lean) + thickness/cos(lean)` of horizontal footprint.
- **Workplane("XZ") extrudes toward -Y.** `.extrude(d)` spans y∈[-d, 0]; translate
  by `cy + d/2` to center at cy. Text on XZ reads correctly viewed from -Y (front).
- **Limit cut depths.** `.extrude(60, both=True)` on a cutter punches through
  everything behind the target (e.g. arch inner hole through the backrest).
- **Fillets are fragile (OCC).** Fillet each part BEFORE union/cuts; wrap risky
  top-edge fillets in try/except (see `soften()` in garmin_station.py). `|Z` edge
  fillets are safe; `.faces(">Z").edges().fillet()` fails on tiny/tangent edges.
- **Text**: `Workplane("XZ", origin=(x, face_y, z)).text(s, size, -depth)` engraves
  into a front face at y=face_y. Get text extents via `.val().BoundingBox()` (used
  to position the delta triangle over the N).
- **Multi-color printing**: make the accent (logo) its own solid, cut it from the
  body (zero clearance — parts are sliced together, not assembled), export two STLs.
  In Bambu Studio: import body, Add Part → logo, assign filament per part.

## garmin_station.py — current state

Desk dock for the user's devices, composition modeled on MakerWorld 2643039
("Garmin Station" by Bobalong) — **studied, not remixed**: that model's license
forbids derivatives, so this is an original build from verified device specs.
`reference/` holds the downloaded 3mf + photos for measuring — NEVER commit or
redistribute it (gitignored).

Verified device dims (Garmin spec sheets / BikeRadar):
- Edge 1050: 60.2 × 118.5 × 16.3 mm, 161 g — leans landscape against back panel
- Varia RCT715: 106.5 × 42.0 × 31.9 mm, 147 g — vertical front-left holster
- HRM 600 module: 68.0 × 31.6 × 10.0 mm — rests on angled front-center shelf;
  strap drapes over the stadium arch front-right

Design language: R14 plinth / R8 towers / `soften()` crowns / 1.5 chamfer on base.
`LABEL`/`LOGO_DEPTH` control the flush two-color GARMIN+delta inlay on the pedestal.
Clearance `CLEAR = 0.8` per side is spec-derived, **not yet test-fitted** — user was
advised to print a fit-test section first; expect a tuning request ("Varia pocket
snug by X mm" → bump CLEAR or per-pocket dims).

Open ideas the user hasn't decided on:
- Arch reads as "O"; original is more open-"U" (2-line change if wanted)
- HRM pod could clip via strap-connector studs instead of resting — needs caliper
  measurements of the HRM 600 click connector from the user
