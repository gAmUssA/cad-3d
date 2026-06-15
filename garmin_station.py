"""Garmin Station — desk dock for Edge 1050 + Varia RCT715 + HRM 600.

V3: monolithic "valet tray" composition adapted from the Garmin Station V2
reference STL (reference/garmin_station_v2.stl — studied, not remixed: the
MakerWorld license forbids derivatives, so this is an original build sized
for our devices from verified specs). The V2 reads as one billet block:

  - deep full-width slot across the back: the Edge drops in landscape,
    a U-notch in the display wall reveals the screen + gives thumb grip
  - front deck ramps up toward the slot wall, GARMIN inlay on the ramp
  - devices live in wells sunk into the deck, no towers, no arch

Reference proportions (measured off the STL by ray-casting): 180x60x90,
slot 20.25 wide / 40 deep with 2.5 walls, notch 57 wide / 28 deep R~14,
deck 40->50 ramp (~29 deg), wells to z=5, corners R~5.

Device dimensions (verified against Garmin spec sheets / reviews):

  Garmin Edge 1050   60.2 x 118.5 x 16.3 mm   161 g
  Varia RCT715      106.5 x  42.0 x  31.9 mm   147 g
  HRM 600 module     68.0 x  31.6 x  10.0 mm

Mapping: Edge landscape in the back slot (sunk 30, screen shows above the
rim and through the notch); Varia stands in a deep well front-left (thumb
scoop on the rim for extraction); HRM 600 pod stands on its long edge in a
slim slot center (lengthened so the strap connectors clear; strap coils
into the stash pit on the right). Edge USB-C exits sideways along the open
slot, Varia's port flap faces up — no cable holes needed.

Exports (out/):
  garmin_station_body.stl  station with a 1 mm logo pocket   } import both into
  garmin_station_logo.stl  flush GARMIN text + delta inlay   } Bambu Studio as
                                                               one object, assign
                                                               a color per part
  garmin_station.stl       single-color merged fallback
  garmin_station.step      lossless CAD interchange

All dimensions are parameters — owning the model beats remixing one.
"""

import math
from pathlib import Path

import cadquery as cq

# --- devices (mm) -------------------------------------------------------------
EDGE_W, EDGE_H, EDGE_T = 60.2, 118.5, 16.3     # Edge 1050 (landscape in slot)
VARIA_W, VARIA_H, VARIA_T = 42.0, 106.5, 31.9  # RCT715, stands vertical
HRM_W, HRM_H, HRM_T = 68.0, 31.6, 10.0         # HRM 600 module, stands on edge

CLEAR = 0.8          # per-side pocket clearance (bump to 1.2 for a cased Edge)

# --- station ------------------------------------------------------------------
DECK_F = 46.0        # deck height at the front face
DECK_DROP = 10.0     # deck rises this much front -> back (the ramp)
EDGE_SINK = 30.0     # how deep the Edge sits below the slot rim
FLAT_FRONT = 14.0    # flat deck strip before the ramp
SHELF_BACK = 7.0     # flat shelf between ramp top and slot wall

WALL_FRONT = 4.5     # deck front wall (front face -> Varia well)
WALL_SIDE = 5.0      # outer side walls flanking the wells
SLOT_WALL_F = 3.5    # Edge slot front (display) wall
SLOT_WALL_R = 3.0    # Edge slot rear wall
SLOT_END = 4.0       # slot end walls
GAP_WELL = 8.0       # x gap between deck wells
GAP_SLOT = 1.6       # y gap between wells and the slot wall

NOTCH_W = 70.0       # U-notch in the display wall (screen reveal + thumb)
NOTCH_R = 15.0
NOTCH_ABOVE = 12.0   # notch bottom sits this far above the slot floor

WELL_FLOOR = 5.0     # Varia well floor (drives total sink ~41 at the rim)
HRM_SINK = 16.0      # HRM slot depth below the back shelf
HRM_END_PLAY = 8.0   # extra slot length so the strap connectors clear
PIT_W, PIT_D = 34.0, 30.0  # strap stash pit plan size
PIT_FLOOR = 10.0
SCOOP_R = 12.0       # thumb scoop on the Varia well front rim
SCOOP_DIP = 8.0

# design language (from the reference): one block, small radii, soft tops
R_CORNER = 5.0       # outer vertical corners
R_FRONT = 3.0        # front top edge
R_WELL = 6.0         # Varia well corners
SOFT = 1.0           # rim/top-edge fillet
CHAMFER = 1.0        # bottom perimeter (elephant-foot relief)
LABEL = "GARMIN"     # inlaid on the deck ramp ("" to disable)
LOGO_DEPTH = 1.0     # inlay depth — printed as a separate body for color swap
LOGO_SIZE = 8.0

# --- derived ------------------------------------------------------------------
DECK_B = DECK_F + DECK_DROP          # deck at the slot wall = slot floor
H = DECK_B + EDGE_SINK               # rim height
slot_w = EDGE_T + 2 * CLEAR

vw_x, vw_y = VARIA_W + 2 * CLEAR, VARIA_T + 2 * CLEAR
hrm_l, hrm_w = HRM_W + 2 * CLEAR + HRM_END_PLAY, HRM_T + 2 * CLEAR

deck_zone = WALL_FRONT + vw_y + GAP_SLOT             # y depth of the deck
base_d = deck_zone + SLOT_WALL_F + slot_w + SLOT_WALL_R
base_l = WALL_SIDE + vw_x + GAP_WELL + hrm_l + GAP_WELL + PIT_W + WALL_SIDE

y_front = -base_d / 2
y_wall = y_front + deck_zone                         # slot display wall front
slot_cy = y_wall + SLOT_WALL_F + slot_w / 2

varia_cx = -base_l / 2 + WALL_SIDE + vw_x / 2
varia_cy = y_front + WALL_FRONT + vw_y / 2
hrm_cx = varia_cx + vw_x / 2 + GAP_WELL + hrm_l / 2
hrm_cy = y_wall - GAP_SLOT - hrm_w / 2
pit_cx = hrm_cx + hrm_l / 2 + GAP_WELL + PIT_W / 2
pit_cy = varia_cy

ramp_run = deck_zone - FLAT_FRONT - SHELF_BACK
ramp_a = math.degrees(math.atan2(DECK_DROP, ramp_run))  # ~28 deg

# logo center on the ramp, aligned with the HRM slot
logo_cx = hrm_cx
logo_cy = y_front + FLAT_FRONT + 0.32 * ramp_run
logo_cz = DECK_F + (logo_cy - (y_front + FLAT_FRONT)) * DECK_DROP / ramp_run


def soften(part: cq.Workplane, r: float = SOFT) -> cq.Workplane:
    """Fillet a part's top edges; skip silently if OCC can't (tiny edges)."""
    try:
        return part.faces(">Z").edges().fillet(r)
    except Exception:
        return part


def logo() -> cq.Workplane | None:
    """GARMIN wordmark + delta triangle, flush 1 mm inlay on the deck ramp.

    Built flat on XY (extruded down), then tilted to the ramp angle and
    translated so the glyph top faces lie in the ramp surface. The solid
    also cuts its own pocket in the body — body + logo print together as
    one multi-color object (zero clearance, sliced together).
    """
    if not LABEL:
        return None
    txt = cq.Workplane("XY").text(LABEL, LOGO_SIZE, -LOGO_DEPTH, font="Helvetica", kind="bold")
    bb = txt.val().BoundingBox()
    # delta triangle sitting above the last letter
    tri_cx = bb.xmax - 2.6
    tri_base = bb.ymax + 1.6
    tri = (
        cq.Workplane("XY")
        .polyline([(tri_cx - 2.6, tri_base), (tri_cx + 2.6, tri_base), (tri_cx, tri_base + 4.0)])
        .close()
        .extrude(-LOGO_DEPTH)
    )
    return (
        txt.union(tri)
        # Rx(+ramp_a): +Y leans up the ramp, -Z extrusion points into the deck
        .rotate((0, 0, 0), (1, 0, 0), ramp_a)
        .translate((logo_cx, logo_cy, logo_cz))
    )


def station() -> cq.Workplane:
    """Monolith body: profile extruded along X, slot + wells cut in."""
    y_back = base_d / 2
    # YZ cross-section: front face, flat strip, ramp, shelf, full-height back
    profile = [
        (y_front, 0),
        (y_front, DECK_F),
        (y_front + FLAT_FRONT, DECK_F),
        (y_front + FLAT_FRONT + ramp_run, DECK_B),
        (y_wall, DECK_B),
        (y_wall, H),
        (y_back, H),
        (y_back, 0),
    ]
    result = (
        cq.Workplane("YZ")
        .polyline(profile)
        .close()
        .extrude(base_l)
        .translate((-base_l / 2, 0, 0))
        .edges("|Z")
        .fillet(R_CORNER)
    )
    # front top edge + ramp creases, before any cuts land on them
    result = result.faces("<Y").edges(">Z").fillet(R_FRONT)
    try:
        result = result.edges(
            cq.selectors.NearestToPointSelector((0, y_front + FLAT_FRONT, DECK_F))
        ).fillet(2.0)
    except Exception:
        pass

    # --- Edge 1050 slot across the back ----------------------------------------
    slot = (
        cq.Workplane("XY")
        .center(0, slot_cy)
        .rect(base_l - 2 * SLOT_END, slot_w)
        .extrude(H - DECK_B + 5)
        .edges("|Z")
        .fillet(3.0)
        .translate((0, 0, DECK_B))
    )
    result = result.cut(slot)

    # U-notch through the display wall only — extrude is depth-limited so it
    # can't punch the rear wall (through-cut gotcha)
    notch_z0 = DECK_B + NOTCH_ABOVE
    notch = (
        cq.Workplane("XZ", origin=(0, y_wall - 2, 0))
        .center(0, (notch_z0 + H + 10) / 2)
        .rect(NOTCH_W, H + 10 - notch_z0)
        .extrude(-(SLOT_WALL_F + 8))
        .edges("|Y and <Z")
        .fillet(NOTCH_R)
    )
    result = result.cut(notch)

    # --- Varia RCT715 well (front left) -----------------------------------------
    varia_well = (
        cq.Workplane("XY")
        .center(varia_cx, varia_cy)
        .rect(vw_x, vw_y)
        .extrude(H)
        .edges("|Z")
        .fillet(R_WELL)
        .translate((0, 0, WELL_FLOOR))
    )
    result = result.cut(varia_well)

    # thumb scoop dipping the well's front rim (echoes the big notch)
    scoop = (
        cq.Workplane("XZ", origin=(varia_cx, y_front - 2, 0))
        .center(0, DECK_F + SCOOP_R - SCOOP_DIP)
        .circle(SCOOP_R)
        .extrude(-(WALL_FRONT + SCOOP_R))
    )
    result = result.cut(scoop)

    # --- HRM 600 slot (center, parallel to the Edge slot) -----------------------
    hrm_slot = (
        cq.Workplane("XY")
        .center(hrm_cx, hrm_cy)
        .rect(hrm_l, hrm_w)
        .extrude(H)
        .edges("|Z")
        .fillet(3.0)
        .translate((0, 0, DECK_B - HRM_SINK))
    )
    result = result.cut(hrm_slot)

    # --- strap stash pit (right) -------------------------------------------------
    pit = (
        cq.Workplane("XY")
        .center(pit_cx, pit_cy)
        .rect(PIT_W, PIT_D)
        .extrude(H)
        .edges("|Z")
        .fillet(8.0)
        .translate((0, 0, PIT_FLOOR))
    )
    result = result.cut(pit)

    # soften rims/wall tops, relieve the bottom edge
    result = soften(result)
    try:
        result = result.edges("<Z").chamfer(CHAMFER)
    except Exception:
        pass

    # logo pocket — the logo solid cuts its own seat (flush inlay)
    lg = logo()
    if lg is not None:
        result = result.cut(lg)

    return result


def device_mockups() -> dict[str, cq.Workplane]:
    """Simplified device stand-ins, positioned in their resting spots.
    For visualization renders only — never exported for printing."""
    edge = (
        cq.Workplane("XY")
        .box(EDGE_H, EDGE_T, EDGE_W, centered=(True, True, False))
        .edges("|Y")
        .fillet(8.0)
        .translate((0, slot_cy, DECK_B + 0.5))
    )
    varia = (
        cq.Workplane("XY")
        .box(VARIA_W, VARIA_T, VARIA_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(10.0)
        .translate((varia_cx, varia_cy, WELL_FLOOR + 0.5))
    )
    pod = (
        cq.Workplane("XY")
        .box(HRM_W, HRM_T, HRM_H, centered=(True, True, False))
        .edges("|Y")
        .fillet(4.0)
        .translate((hrm_cx, hrm_cy, DECK_B - HRM_SINK + 0.5))
    )
    return {"edge": edge, "varia": varia, "pod": pod}


if "show_object" in globals():
    # CQ-editor live preview: open this file in cq-editor, hit Render (F5)
    show_object(station(), name="garmin_station")  # noqa: F821
    lg = logo()
    if lg is not None:
        show_object(lg, name="logo", options={"color": "white"})  # noqa: F821

if __name__ == "__main__":
    import os

    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)

    body = station()
    lg = logo()
    cq.exporters.export(body, str(out / "garmin_station_body.stl"))
    if lg is not None:
        cq.exporters.export(lg, str(out / "garmin_station_logo.stl"))
        merged = body.union(lg)
    else:
        merged = body
    cq.exporters.export(merged, str(out / "garmin_station.stl"))
    cq.exporters.export(merged, str(out / "garmin_station.step"))

    if os.environ.get("MOCKUP"):
        for name, solid in device_mockups().items():
            cq.exporters.export(solid, str(out / f"mock_{name}.stl"))
        print("mockup device STLs exported")

    bb = merged.val().BoundingBox()
    print(f"exported body/logo/merged STL + STEP to {out}/")
    print(f"footprint: {bb.xlen:.1f} x {bb.ylen:.1f} mm, height {bb.zlen:.1f} mm")
