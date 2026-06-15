"""Garmin Station V4 — band-holster, 4-device dock (V3 monolith language).

Same billet-block language as garmin_station.py (V3). Front row, left to
right: the two Varia lights grouped, then the centered HRM window, then the
Edge tower:

  - Varia UT800 (front headlight): deep well far left, stands vertical
  - Varia RCT715 (rear radar/taillight): deep well, stands vertical
  - center gap: GARMIN inlay on the ramp + the HRM U-notch, all on x=0
  - Edge 1050: PORTRAIT tower well on the right (display perch — towering
    buries its bottom USB-C, so not a charging dock)
  - back full-width slot = HRM 600 BAND holster: strap stuffs along the
    channel, pod (31.6 tall) stands behind the notch ~flush with the rim

Both bike lights + the Edge + the HRM strap all dock at once (~203 mm wide).

Device dimensions (verified against Garmin spec sheets / reviews):

  Garmin Edge 1050   60.2 x 118.5 x 16.3 mm   161 g
  Varia RCT715      106.5 x  42.0 x  31.9 mm   147 g
  Varia UT800        96.6 x  33.5 x  29.7 mm   (44.7 deep incl. mount flange)
  HRM 600 module     68.0 x  31.6 x  10.0 mm

Exports (out/):
  garmin_station_v4_body.stl / _logo.stl   two-color pair for Bambu Studio
  garmin_station_v4.stl / .step            merged fallback + CAD interchange

All dimensions are parameters — owning the model beats remixing one.
"""

import math
from pathlib import Path

import cadquery as cq

# --- devices (mm) -------------------------------------------------------------
EDGE_W, EDGE_H, EDGE_T = 60.2, 118.5, 16.3     # Edge 1050 (16.3 = thin edge spec)
EDGE_DEPTH = 18.8    # MEASURED body depth front->back before the quarter-turn
                     # connector: the back domes/humps to 18.8 (spec 16.3 is the
                     # thin edge). This drives the claw cavity depth, NOT 16.3 —
                     # using 16.3 made the cavity too shallow and the hump scraped.
VARIA_W, VARIA_H, VARIA_T = 42.0, 106.5, 31.9  # RCT715, stands vertical
UT_W, UT_H, UT_T = 33.5, 96.6, 29.7            # Varia UT800, stands vertical
UT_FLANGE = 44.7                               # depth incl. mount flange (tab)
HRM_W, HRM_H, HRM_T = 68.0, 31.6, 10.0         # HRM 600 module, in band slot

CLEAR = 0.8          # general per-side pocket clearance
VARIA_BACK = 3.0     # extra depth behind the RCT715 (back was tight)
UT_CLEAR_W = 0.4     # UT800 width (x) — was 0.8/side, ran loose; snug it up

# --- station ------------------------------------------------------------------
DECK_F = 46.0        # deck height at the front face
DECK_DROP = 10.0     # deck rises this much front -> back (the ramp)
SLOT_DEPTH = 30.0    # band slot depth below the rim (pod 31.6 ~ flush)
BAND_W = 20.0        # band slot width — fabric strap + pod stuff in loosely
FLAT_FRONT = 14.0    # flat deck strip before the ramp
SHELF_BACK = 7.0     # flat shelf between ramp top and slot wall

WALL_FRONT = 4.5     # deck front wall (front face -> Varia well)
WALL_SIDE = 5.0      # outer side walls flanking the wells
SLOT_WALL_F = 3.5    # band slot front (display) wall
SLOT_WALL_R = 3.0    # band slot rear wall
SLOT_END = 4.0       # slot end walls
CENTER_GAP = 46.0    # deck between RCT715 and Edge — the logo/notch band
GAP_WELL = 6.0       # gap between the two Varia light wells (UT800 | RCT715)
GAP_SLOT = 5.0       # y gap (wall) between wells and the slot — was 1.6, too
                     # thin between the Varia back and the HRM holster

NOTCH_W = 70.0       # U-notch in the display wall (pod reveal + thumb)
NOTCH_R = 15.0
NOTCH_ABOVE = 12.0   # notch bottom sits this far above the slot floor

WELL_FLOOR = 5.0     # Varia well floor (drives total sink ~41 at the rim)
EDGE_FLOOR = 8.0     # Edge tower well floor (sink ~38 at the front rim)
EDGE_RISE = 11.0     # Edge cradle rises this far above the deck shelf for a
                     # taller grip (less tower cantilever). CAPPED just under
                     # the HRM notch (DECK_B+NOTCH_ABOVE): rising past it makes
                     # the cradle ram the notch → jagged slivers. The rear relief
                     # still continues up the raised wall so the quarter-turn
                     # mount boss nests in it. (More grip needs a narrower notch
                     # or the Edge moved right — both change the layout.)
UT_FLOOR = 5.0       # UT800 well floor
EDGE_MOUNT_W = 32.0  # relief groove for the Edge's rear quarter-turn mount
EDGE_MOUNT_D = 8.0   # groove depth into the back wall — the connector boss
                     # protrudes past the 18.8 back, so the relief must clear it
LEADIN = 2.0         # lead-in at the Edge niche mouth — a small flat CHAMFER
                     # (was a 4mm concave bellmouth, which scalloped the wall
                     # tops into notch-like dips). Now leaves flat, ironable wall
                     # tops with a tidy bevel inside for easy entry.
# UT800's quarter-turn mount flange (29.7 body -> 44.7) is ASSUMED to face
# FORWARD: a notch through the well's front wall homes the tab + serves as
# the extraction grip. The front is open, so this can't break the holster or
# add width. If the tab is actually on a side/back, move this relief.
UT_RELIEF_W = 20.0   # front flange-relief notch width
UT_RELIEF_H = 50.0   # notch height up from the floor
SCOOP_R = 12.0       # thumb scoop on the Varia well front rim
SCOOP_DIP = 8.0

# Claw-style Edge holder (alt to the friction well, learned from the Skådis
# Garmin holder): a C-channel that CUPS the device's rounded side edges with
# two front claws over a flat back datum — registers + clips, not 4-wall
# friction. Screen open in front; slide the Edge in from the top.
EDGE_EDGE_R = 3.5    # Edge 1050 rounded side-edge radius — CALIPER THIS
EDGE_CLAW_CL = 0.4   # WIDTH cup clearance (snug — wraps the side edges, "fits perfectly")
EDGE_CLAW_CL_D = 0.7 # DEPTH clearance — looser than width, so the humped/domed
                     # back (18.8 at the hump) clears the back wall and won't scrape
CLAW_W = 7.0         # front claw span/side (covers the corner + ~3mm onto front)

# design language (from the reference): one block, small radii, soft tops
R_CORNER = 5.0       # outer vertical corners
R_FRONT = 3.0        # front top edge
R_WELL = 6.0         # Varia well corners
R_EDGE_WELL = 8.5    # Edge well corners — matched to the device's rounded
                     # corners so they nest and it seats fully (was 7: corners
                     # rode up). Near max for the 18.3 slot (8.5+8.5 < 18.3).
SOFT = 1.0           # rim/top-edge fillet
CHAMFER = 1.0        # bottom perimeter (elephant-foot relief)
LABEL = "GARMIN"     # inlaid on the deck ramp ("" to disable)
LOGO_DEPTH = 1.0     # inlay depth — printed as a separate body for color swap
LOGO_SIZE = 8.0

# --- derived ------------------------------------------------------------------
DECK_B = DECK_F + DECK_DROP          # deck at the slot wall = slot floor
H = DECK_B + SLOT_DEPTH              # rim height

# front-aligned wells: extra VARIA_BACK depth lands behind the device (the
# well front stays at WALL_FRONT), so the GAP_SLOT wall to the holster is
# unchanged — the whole block just gets a few mm deeper
vw_x, vw_y = VARIA_W + 2 * CLEAR, VARIA_T + 2 * CLEAR + VARIA_BACK
ut_x, ut_y = UT_W + 2 * UT_CLEAR_W, UT_T + 2 * CLEAR
# Edge envelope = the claw cavity (width snug, depth clears the humped back),
# so the collar wraps it with clean WALL_SIDE walls
ew_x, ew_y = EDGE_W + 2 * EDGE_CLAW_CL, EDGE_DEPTH + 2 * EDGE_CLAW_CL_D

deck_zone = WALL_FRONT + max(vw_y, ut_y) + GAP_SLOT  # y depth of the deck
base_d = deck_zone + SLOT_WALL_F + BAND_W + SLOT_WALL_R

# CENTER_GAP (between RCT715 and Edge) is centered on x=0, so the HRM notch,
# the pod, and the GARMIN logo all sit on the part centerline. The UT800 +
# RCT715 lights are grouped to the left of the gap, the Edge to the right.
# Devices differ in width, so the outer walls — and the block outline — are
# intentionally asymmetric; a centered HRM window beats a symmetric outline.
half_gap = CENTER_GAP / 2
edge_cx = half_gap + ew_x / 2                        # Edge, right of the gap
varia_cx = -(half_gap + vw_x / 2)                    # RCT715, left of the gap
ut_cx = varia_cx - vw_x / 2 - GAP_WELL - ut_x / 2    # UT800, far left
x_left = ut_cx - ut_x / 2 - WALL_SIDE
x_right = edge_cx + ew_x / 2 + WALL_SIDE
base_l = x_right - x_left
x_mid = (x_left + x_right) / 2                        # block centroid (≠ 0)

y_front = -base_d / 2
y_wall = y_front + deck_zone                          # slot display wall front
slot_cy = y_wall + SLOT_WALL_F + BAND_W / 2

# lights front-aligned (fronts at WALL_FRONT); Edge centered in the deck
varia_cy = y_front + WALL_FRONT + vw_y / 2
ut_cy = y_front + WALL_FRONT + ut_y / 2
edge_cy = y_front + deck_zone / 2

ramp_run = deck_zone - FLAT_FRONT - SHELF_BACK
ramp_a = math.degrees(math.atan2(DECK_DROP, ramp_run))  # ~28 deg

# logo on the centerline (x=0) = gap center = notch center; gap (±half_gap)
# is wider than the glyph run, so no overhang onto the well cuts
logo_cx = 0.0
logo_cy = y_front + FLAT_FRONT + 0.42 * ramp_run
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


def cut_edge_well(body: cq.Workplane, cx: float, cy: float,
                  floor_z: float, rim_z: float) -> cq.Workplane:
    """Edge 1050 portrait niche: well + rear mount-boss relief groove + a
    mouth lead-in chamfer. Shared by the full dock and the fit-test coupon so
    the fit is byte-identical — tune the coupon, the dock inherits it."""
    depth = rim_z - floor_z
    well = (
        cq.Workplane("XY").center(cx, cy)
        .rect(ew_x, ew_y).extrude(depth + 5)
        .edges("|Z").fillet(R_EDGE_WELL)
        .translate((0, 0, floor_z))
    )
    body = body.cut(well)

    # rear quarter-turn mount-boss relief groove (stops short of the holster)
    back_y = cy + ew_y / 2
    groove = (
        cq.Workplane("XY").center(cx, back_y + EDGE_MOUNT_D / 2 - 0.5)
        .rect(EDGE_MOUNT_W, EDGE_MOUNT_D + 1.0).extrude(depth)
        .edges("|Z").fillet(2.0)   # < EDGE_MOUNT_D/2 or opposing fillets collide
        .translate((0, 0, floor_z))
    )
    body = body.cut(groove)

    # curved bellmouth lead-in at the mouth: a box flared by LEADIN/side, its
    # bottom FILLETED back to nominal (concave sweep, not a flat 45°), cut from
    # the rim down — strong self-guide, soft touch (1040-holder style)
    funnel = (
        cq.Workplane("XY").center(cx, cy)
        .rect(ew_x + 2 * LEADIN, ew_y + 2 * LEADIN).extrude(LEADIN + 2)
        .edges("<Z").fillet(LEADIN * 0.99)
        .translate((0, 0, rim_z - LEADIN))
    )
    body = body.cut(funnel)
    return body


def cut_edge_claw(body: cq.Workplane, cx: float, cy: float,
                  floor_z: float, rim_z: float, front_y: float) -> cq.Workplane:
    """Edge 1050 CLAW cradle (chosen over the friction well after print tests).
    Cups the device's rounded side edges in a snug rounded cavity over a flat
    back datum, with the back hump relieved full-height and the FRONT OPEN
    (claws at the corners) out to `front_y`. The open front is what lets the
    rear quarter-turn hump sit in the relief without the closed-box
    over-constraint that made the friction well reject the device. Shared by
    the dock and the claw coupon so the fit is identical.

    `front_y` = the exterior face the front window opens out to (dock: y_front;
    coupon: its own front face)."""
    cw_x = EDGE_W + 2 * EDGE_CLAW_CL          # snug WIDTH cup
    cw_y = EDGE_DEPTH + 2 * EDGE_CLAW_CL_D    # DEPTH from the real 18.8 humped back
    Rc = EDGE_EDGE_R + EDGE_CLAW_CL           # cavity corner matches the edge
    depth = rim_z - floor_z

    cav = (
        cq.Workplane("XY").center(cx, cy).rect(cw_x, cw_y).extrude(depth + 5)
        .edges("|Z").fillet(Rc).translate((0, 0, floor_z))
    )
    body = body.cut(cav)

    # open front window — remove the front centre out to front_y, leaving two
    # corner claws that cup the rounded edges and overhang the front face
    open_w = cw_x - 2 * CLAW_W
    y_in = cy - cw_y / 2                       # cavity front
    y0 = front_y - 2
    win_len = (y_in + 1) - y0
    window = (
        cq.Workplane("XY").center(cx, (y0 + y_in + 1) / 2)
        .rect(open_w, win_len).extrude(depth + 5)
        .translate((0, 0, floor_z))
    )
    r_win = min(3.0, win_len / 2 - 0.6)        # avoid opposing-fillet collision
    if r_win > 0.4:
        try:
            window = window.edges("|Z").fillet(r_win)
        except Exception:
            pass
    body = body.cut(window)

    # rear quarter-turn hump relief in the back datum (full height)
    back_y = cy + cw_y / 2
    relief = (
        cq.Workplane("XY").center(cx, back_y + EDGE_MOUNT_D / 2 - 0.5)
        .rect(EDGE_MOUNT_W, EDGE_MOUNT_D + 1.0).extrude(depth)
        .edges("|Z").fillet(2.0).translate((0, 0, floor_z))
    )
    body = body.cut(relief)

    # small flat lead-in chamfer at the rim — leaves the wall tops FLAT (clean
    # + ironable) with just a tidy bevel inside, instead of the big concave
    # bellmouth that scalloped the tops into notch-like dips
    funnel = (
        cq.Workplane("XY").center(cx, cy)
        .rect(cw_x + 2 * LEADIN, cw_y + 2 * LEADIN).extrude(LEADIN + 2)
        .edges("<Z").chamfer(LEADIN * 0.99).translate((0, 0, rim_z - LEADIN))
    )
    body = body.cut(funnel)
    return body


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
        .translate((x_left, 0, 0))
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

    # --- HRM band slot across the back -------------------------------------------
    # full-width holster spans the (asymmetric) block, centered on x_mid; the
    # pod itself sits at the centered notch (x=0)
    slot = (
        cq.Workplane("XY")
        .center(x_mid, slot_cy)
        .rect(base_l - 2 * SLOT_END, BAND_W)
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

    # --- Varia UT800 well (front, far left) -------------------------------------
    ut_well = (
        cq.Workplane("XY")
        .center(ut_cx, ut_cy)
        .rect(ut_x, ut_y)
        .extrude(H)
        .edges("|Z")
        .fillet(R_WELL)
        .translate((0, 0, UT_FLOOR))
    )
    result = result.cut(ut_well)

    # front flange-relief notch: homes the forward-facing mount tab and gives
    # a finger grip; cuts from the front face into the well's front
    ut_front = ut_cy - ut_y / 2
    ut_relief = (
        cq.Workplane("XY")
        .center(ut_cx, (y_front + ut_front) / 2)
        .rect(UT_RELIEF_W, (ut_front + 3.0) - (y_front - 3.0))
        .extrude(UT_RELIEF_H)
        .edges("|Z")
        .fillet(5.0)
        .translate((0, 0, UT_FLOOR))
    )
    result = result.cut(ut_relief)

    # --- Edge 1050 claw cradle (right): cup + back datum/relief + open front -----
    # raised collar so the cradle grips ABOVE the deck (taller tower support);
    # cut_edge_claw then carves the cup/window/relief up through it, so the rear
    # mount-boss relief continues up the raised back wall (mount nests in it)
    # cap the rim just under the notch so the cradle never rams it
    edge_rim = min(DECK_B + EDGE_RISE, DECK_B + NOTCH_ABOVE - 1.0)
    # collar spans the full Edge envelope + side walls so its outer wall is
    # FLUSH with the block edge (no sliver); ~5.8mm walls all round
    collar = (
        cq.Workplane("XY").center(edge_cx, edge_cy)
        .rect(ew_x + 2 * WALL_SIDE, ew_y + 2 * WALL_SIDE).extrude(edge_rim - DECK_F)
        .edges("|Z").fillet(R_CORNER)
        .translate((0, 0, DECK_F))
    )
    result = result.union(collar)
    result = cut_edge_claw(result, edge_cx, edge_cy, EDGE_FLOOR, edge_rim, y_front)

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
        .box(EDGE_W, EDGE_DEPTH, EDGE_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(8.0)
        .translate((edge_cx, edge_cy, EDGE_FLOOR + 0.5))
    )
    varia = (
        cq.Workplane("XY")
        .box(VARIA_W, VARIA_T, VARIA_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(10.0)
        .translate((varia_cx, varia_cy, WELL_FLOOR + 0.5))
    )
    ut = (
        cq.Workplane("XY")
        .box(UT_W, UT_T, UT_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(9.0)
        .translate((ut_cx, ut_cy, UT_FLOOR + 0.5))
    )
    pod = (
        cq.Workplane("XY")
        .box(HRM_W, HRM_T, HRM_H, centered=(True, True, False))
        .edges("|Y")
        .fillet(4.0)
        .translate((0, slot_cy, DECK_B + 0.5))
    )
    return {"edge": edge, "varia": varia, "ut": ut, "pod": pod}


def edge_fit_test() -> cq.Workplane:
    """Small standalone coupon: just the Edge 1050 niche in a minimal block,
    shorter than the full tower, for a fast print to dial in the fit + lead-in
    before committing the big dock. Uses cut_edge_well() so the cross-section,
    clearances, mount groove, and lead-in are identical to the real well."""
    TEST_H = 45.0        # well only this deep — enough to feel the slide-in
    FLOOR = 4.0
    depth = ew_y + WALL_FRONT + EDGE_MOUNT_D + 4.0   # front wall + back wall
    cy_block = (EDGE_MOUNT_D + 4.0 - WALL_FRONT) / 2  # so the well sits at y=0
    block = (
        cq.Workplane("XY")
        .box(ew_x + 2 * WALL_SIDE, depth, TEST_H, centered=(True, True, False))
        .translate((0, cy_block, 0))
        .edges("|Z").fillet(R_CORNER)
    )
    try:
        block = block.edges("<Z").chamfer(CHAMFER)
    except Exception:
        pass
    return cut_edge_well(block, 0.0, 0.0, FLOOR, TEST_H)


def edge_claw_test(test_h: float = 55.0) -> cq.Workplane:
    """Claw-style Edge holder coupon (the chosen design). A minimal block with
    the Edge claw cut by the SAME cut_edge_claw() the dock uses, so the coupon
    fit is identical to the dock. `test_h` is the channel height — bumped to 55
    (≈+1cm) after the 45mm print fit perfectly and wanted a bit more grip."""
    cw_x = EDGE_W + 2 * EDGE_CLAW_CL
    cw_y = EDGE_DEPTH + 2 * EDGE_CLAW_CL_D
    SIDE, BACK, FRONT = 3.0, 3.0, 3.0
    FLOOR = 4.0
    block = (
        cq.Workplane("XY")
        .box(cw_x + 2 * SIDE, cw_y + BACK + FRONT, test_h, centered=(True, True, False))
        .edges("|Z").fillet(R_CORNER)
    )
    try:
        block = block.edges("<Z").chamfer(CHAMFER)
    except Exception:
        pass
    # cavity centred at origin; coupon front face at -(cw_y/2 + FRONT)
    return cut_edge_claw(block, 0.0, 0.0, FLOOR, test_h, -(cw_y / 2 + FRONT))


if "show_object" in globals():
    # CQ-editor live preview: open this file in cq-editor, hit Render (F5)
    show_object(station(), name="garmin_station_v4")  # noqa: F821
    lg = logo()
    if lg is not None:
        show_object(lg, name="logo", options={"color": "white"})  # noqa: F821

if __name__ == "__main__":
    import os

    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)

    body = station()
    lg = logo()
    cq.exporters.export(body, str(out / "garmin_station_v4_body.stl"))
    if lg is not None:
        cq.exporters.export(lg, str(out / "garmin_station_v4_logo.stl"))
        merged = body.union(lg)
    else:
        merged = body
    cq.exporters.export(merged, str(out / "garmin_station_v4.stl"))
    cq.exporters.export(merged, str(out / "garmin_station_v4.step"))

    # standalone Edge claw coupon — print this alone to verify the slide-in fit,
    # then the full dock inherits the same fit (shared cut_edge_claw)
    claw = edge_claw_test()
    cq.exporters.export(claw, str(out / "garmin_station_v4_edgeclaw.stl"))
    cb = claw.val().BoundingBox()
    print(f"edge claw coupon: {cb.xlen:.1f} x {cb.ylen:.1f} x {cb.zlen:.1f} mm")

    if os.environ.get("MOCKUP"):
        for name, solid in device_mockups().items():
            cq.exporters.export(solid, str(out / f"mock_v4_{name}.stl"))
        print("mockup device STLs exported")

    bb = merged.val().BoundingBox()
    print(f"exported body/logo/merged STL + STEP to {out}/")
    print(f"footprint: {bb.xlen:.1f} x {bb.ylen:.1f} mm, height {bb.zlen:.1f} mm")
