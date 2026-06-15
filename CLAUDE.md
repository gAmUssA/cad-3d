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
- **`.spline()` defaults to `includeCurrent=False`** — it does NOT connect from
  the current point, silently leaving a wire gap → `DisconnectedWire` at close().
  Always pass `includeCurrent=True` when chaining. Also: a spline ending exactly
  on the wire's start point makes `close()` emit a zero-length edge (OCC fail) —
  stop one point short and let close() draw the final segment.
- **Global `edges().fillet()` can SEGFAULT, not raise.** After an intersect that
  mixes straight and curved faces (e.g. macbook_claw's width-shaper), a whole-body
  fillet exits 139 — try/except is no protection. Fillet the slab's `|X` profile
  edges BEFORE the intersect (full-width edges are safe), round the sculpting
  tool's own edges, and only attempt narrow BoxSelector fillets after. Bisect
  crashes with a step-by-step script using flushed prints.

## garmin_station.py — current state (V3, monolith)

Desk dock for the user's devices, composition adapted from the "Garmin Station
V2" reference STL (`reference/garmin_station_v2.stl`, MakerWorld/Bobalong) —
**studied, not remixed**: that license forbids derivatives, so this is an
original build sized for our devices. `reference/` holds the downloaded
3mf/STL + photos for measuring — NEVER commit or redistribute it (gitignored).
Reference was measured by vtkOBBTree ray-casting (heightfields + fine scans):
180×60×90 block, Edge slot 20.25 wide/40 deep walls ~2.5, U-notch 57×28 R~14,
deck ramp 40→50 (~29°), wells to z=5, corners R~5, logo engraved on the ramp.

V3 composition (one billet block, 181×64×86, no towers/arch):
- Edge 1050 (60.2×118.5×16.3): landscape in full-width back slot, sunk 30,
  U-notch 70×18 R15 in the display wall (screen reveal + thumb grip); USB-C
  exits sideways along the open slot — no cable holes
- Varia RCT715 (42×31.9 cross): vertical well front-left, sunk ~41 at front
  rim, R12 thumb scoop dips the rim for extraction
- HRM 600 pod (68×31.6×10): stands on long edge in slim slot center, +8 mm
  end play for strap connectors; strap coils into 34×30 stash pit right
- GARMIN+delta flush two-color inlay on the 28° ramp: text built on XY,
  `rotate((0,0,0),(1,0,0), ramp_a)` then translate (`LABEL`/`LOGO_DEPTH`)

Body is a YZ profile polyline extruded along X (front face → ramp → wall →
back), then slot/notch/wells cut — much more robust than box unions.

Clearance `CLEAR = 0.8` per side is spec-derived, **not yet test-fitted** —
expect a tuning request ("Varia pocket snug by X mm" → bump CLEAR or dims).

### garmin_station_v4.py — band-holster variant (separate file, same language)

User-requested remap, now a 4-DEVICE dock (~203×70×86). Front row L→R:
Varia UT800 well, Varia RCT715 well, center gap (GARMIN logo + HRM U-notch
on x=0), Edge 1050 PORTRAIT tower well (floor 8, sunk ~38, buries bottom
USB-C — display perch, not a charging dock). Back full-width slot = HRM
band holster (strap stuffs in, pod stands behind the notch ~flush,
`BAND_W=20`). Both bike lights + Edge + strap dock at once.
- UT800 (96.6×33.5×29.7, but **44.7 deep with its quarter-turn mount
  flange**): well sized to the BODY + a front-wall relief notch
  (`UT_RELIEF_*`) that ASSUMES the tab faces forward (front is open, can't
  break the holster or add width). If the tab is on a side/back, move it.
- Lights grouped left of the gap (`GAP_WELL` between them); Edge right.
- Per-axis clearances dialed from prints (print 2 = "almost perfect"):
  `EDGE_CLEAR_W=3.0` (width still snug at 1.0 → +2/side), `EDGE_CLEAR=1.0`
  (thickness; mount groove handles the boss), `VARIA_BACK=3.0` (extra depth
  behind the RCT715 — front-aligned so the GAP_SLOT wall is unchanged, block
  just gets deeper), `UT_CLEAR_W=0.4` (UT800 ran loose at 0.8/side → snug).
  Print 3: bumped Edge W/D to 3.0/2.5 + lead-in → swam (too loose). Print 4:
  back to snug `EDGE_CLEAR_W=1.2`/`EDGE_CLEAR=1.0` (lead-in eases entry, walls
  grip) — "almost perfect". Print 5: `R_EDGE_WELL=7→8.5` so the device's
  rounded corners nest and it seats fully (corners were riding up). ~203×72×86.
- Edge niche = `cut_edge_well(body, cx, cy, floor_z, rim_z)` helper: well +
  rear mount groove + **`LEADIN=4.0` curved bellmouth lead-in** (funnel box
  flared by LEADIN/side, bottom FILLETED to nominal → concave sweep, not a
  flat 45°; cut from the rim down). Learned from `out/Garmin_Edge_1040_Solar
  .stl` (a quarter-turn side-rail cradle whose rail tops sweep in ~10mm).
  Affects entry only, not the seated fit.
- **Edge holder = CLAW (chosen after A/B print test).** The friction WELL
  (`cut_edge_well`, `edge_fit_test`) is kept as dead code for reference but no
  longer used; the user's print verdict: claw "fits perfectly", friction well
  "too tight in width and depth — the rear hump doesn't fit".
  - `cut_edge_claw(body, cx, cy, floor_z, rim_z, front_y)` — the dock's Edge
    holder. Rounded cavity (`EDGE_EDGE_R + EDGE_CLAW_CL` corner) CUPS the
    device's rounded side edges over a flat back datum; rear hump relief
    (`EDGE_MOUNT_*`) full height; **open front** (claws at the corners, window
    out to `front_y`) — the open front is WHY it fits where the closed well
    didn't (the hump sits in the relief without box over-constraint); bellmouth
    lead-in. `station()` calls it with `front_y=y_front`.
  - `edge_claw_test(test_h=55)` → `..._edgeclaw.stl`: coupon using the SAME
    helper, so fit is identical. 55mm (≈+1cm over the 45mm that fit perfectly).
  - **Dock vs coupon claw shape differs (fit identical):** in the dock the
    front runs ~14mm to the deck face, so the claws are deep corner POSTS, not
    thin lips.
  - **Raised cradle collar** (`EDGE_RISE`): a collar unioned around the Edge
    from `DECK_F` up to `edge_rim` lifts the grip above the deck (cantilever
    ~70→~45mm). Collar = `rect(ew_x+2*WALL_SIDE, ew_y+2*WALL_SIDE)` so its outer
    wall is FLUSH with the block (else a ~1mm sliver). `edge_rim` is CAPPED at
    `DECK_B+NOTCH_ABOVE-1` (just under the HRM notch) — rising past the notch
    rams it and leaves jagged thin slivers (print-5 artifact, now fixed). More
    grip would need a narrower `NOTCH_W` or the Edge moved right.
  - Verify after edits: `vtkFeatureEdges` boundary+nonmanifold == 0 (watertight)
    and OBBTree wall-thickness probe ~5-6mm (no thin fins).
  - `EDGE_EDGE_R=3.5` still a GUESS — caliper the real side-edge radius.
  The full dock AND the `edge_fit_test()` coupon both call it, so the coupon's
  fit is byte-identical — print the small coupon (`garmin_station_v4_edgetest
  .stl`, ~76×36×45) to dial in the slide-in, then the dock inherits it.
  Scratching on FDM is layer lines/Z-seam, not the fillet; the lead-in funnel
  is the real fix for catch-on-insertion.

**Print-1 fit fixes (the layout now centers the device GAP on x=0, not the
block — wells flank `±half_gap`, outer walls/outline are intentionally
asymmetric since the devices differ in width):**
- Edge was snug & scratched going in but slid clean UPSIDE-DOWN → it was the
  rear quarter-turn mount boss catching the back wall, not the body fit. Fix:
  keep clearance modest (`EDGE_CLEAR=1.0`) + cut a relief groove down the
  well's back wall (`EDGE_MOUNT_W/D`), stopping short of the holster. Bigger
  `R_EDGE_WELL=7` too. If it still binds, widen/deepen the groove first.
- Varia↔holster wall was 1.6 mm (thin) → `GAP_SLOT=5.0`. Varia clearance left
  at 0.8 (user said snug is fine).
- HRM notch/pod/logo now all on x=0 = gap center (was at part-center, ~9 mm
  off the gap toward the Edge). `logo_cx=0`; gap (±half_gap) is wider than the
  glyph run so no overhang. Band slot centered on `x_mid`, notch on 0.
**Gotchas**: a body-centered logo would overhang the Edge well cut (floating
inlay fragments) — verify glyph fits within the gap. Groove `|Z` fillet must
be < EDGE_MOUNT_D/2 or opposing fillets collide (OCC fail). Check centering &
clearances numerically (STL bbox / OBBTree probe) after layout changes.

### macbook_claw.py — OpenClaws-style clamshell holder

Claw clip that keeps a MacBook lid cracked open (GAP=20) so the lid sensor
never sleeps it. **Hand that clasps the clamshell.** Build order matters:
1. YZ profile (spline back, waisted stem) extruded to WIDTH; functional
   faces stay flat (stem inner, shelf, finger underside).
2. Inner foot corner = concave `HUG_R` arc matching the base's curved
   bottom edge, so it hugs the laptop instead of point-touching.
3. Intersect with an XZ width-shaper prism (wide heel, waist, spread
   knuckles). NO global fillet after this (OCC segfaults — see gotcha).
4. `heel_trim`: cut the under-base heel back to the pinky (-x) half so the
   thumb is the under-base grip on its own (+x) side — a real clasp/pincer.
   Cut BEFORE the thumb union or it eats the thumb.
5. Thumb = `THUMB` waypoints (x,y,z,r) lerp-densified to ~0.7mm spacing,
   each a `sphere(r)` unioned → smooth tapered capsule wrapping the side
   and pressing under the base. Sphere-chain is OCC-safe where a 3D sweep
   + fillet is crash roulette. **A thin + long + uniform-radius chain reads
   as a WORM** — make it short, THICK (r 3.5–5.8), and bury the first 1–2
   spheres in the palm as a thenar web so there's no detached neck. Export
   STL at `tolerance=0.02` (default 0.1 facets the spheres into visible
   "ribs" — the other half of the worm look).
6. `SLOT_XS` wedge slots + per-`FINGERS` tip trims → 4 fingers, middle
   longest, pinky shortest.
Fit params `BASE_T`/`LID_T`/`HUG_R` (defaults MBP 14: 9.6/6.0/5.0; Air ≈
7.6/4.4 + larger HUG_R — Air bottoms taper) — user should caliper-check.
Print LYING ON THE PINKY SIDE (-x face down, thumb up); thumb underside is a
horizontal-cylinder overhang — TPU 95A bridges it, PETG wants light support.
Mockup slabs approximate the lid as parallel (real lid angles to the hinge).

Open ideas the user hasn't decided on:
- HRM pod only sinks ~13-16; could clip via strap-connector studs instead —
  needs caliper measurements of the HRM 600 click connector from the user
- Block is chunky (~480 cm³ envelope); could shell/pocket the underside if
  print weight/material matters
