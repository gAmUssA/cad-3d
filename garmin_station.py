"""Garmin Station — desk dock for Garmin Edge 1050 + Varia RCT715.

Original parametric design inspired by the *concept* of MakerWorld's
"Garmin Station" (Bobalong, model 2643039 — RTL515/Edge 530 sized, and
license-restricted against remixing), built from scratch for:

  Garmin Edge 1050   60.2 x 118.5 x 16.3 mm  (garmin.com / bikeradar)
  Varia RCT715      106.5 x  42.0 x  31.9 mm  (garmin.com / bikeradar)

Layout: angled cradle on the left presents the Edge screen-up at a
readable lean; a vertical holster on the right keeps the Varia upright.
Both pockets have through-the-base cable slots so chargers can stay
plugged in (both devices are USB-C).

All dimensions are parameters — owning the model beats remixing one.
"""

from pathlib import Path

import cadquery as cq

# --- devices (mm) -------------------------------------------------------------
EDGE_W, EDGE_H, EDGE_T = 60.2, 118.5, 16.3     # Edge 1050: width, height, thickness
VARIA_W, VARIA_H, VARIA_T = 42.0, 106.5, 31.9  # RCT715: width, height, thickness

CLEAR = 0.8          # per-side pocket clearance (snug; bump to 1.2 for a case)

# --- station ------------------------------------------------------------------
# Pocket depths and footprint proportions taken from measuring the original
# RTL515/Edge-530 station's mesh (~45-50 mm deep pockets, 60 mm deep base):
# deep pockets matter — these devices are heavier than the originals
# (Edge 1050: 161 g, RCT715: 147 g).
WALL = 4.0           # min wall around pockets
BASE_T = 8.0         # base slab thickness
GAP = 12.0           # space between the two docks
EDGE_LEAN = 20.0     # degrees from vertical, leaning back
EDGE_DEPTH = 44.0    # vertical sink of the Edge into its cradle
VARIA_DEPTH = 50.0   # how far the Varia sinks into its holster
CABLE_W = 13.0       # USB-C plug body clearance
FILLET = 5.0

# pocket cross-sections (device + clearance)
ep_w, ep_t = EDGE_W + 2 * CLEAR, EDGE_T + 2 * CLEAR
vp_w, vp_t = VARIA_W + 2 * CLEAR, VARIA_T + 2 * CLEAR

# dock blocks
edge_block_w = ep_w + 2 * WALL
edge_block_d = 46.0                          # front-to-back footprint of the cradle block
edge_block_h = 46.0
varia_block_w = vp_w + 2 * WALL
varia_block_d = vp_t + 2 * WALL
varia_block_h = VARIA_DEPTH + 5.0            # pocket depth + floor

EDGE_POCKET_Y = -6.0                         # shift pocket forward so its leaned top
                                             # stays inside the block's back wall

base_l = edge_block_w + GAP + varia_block_w + 2 * WALL
base_d = 58.0                                # original's deep base: stability for the
                                             # tall Edge 1050 leaning back


def station() -> cq.Workplane:
    # base slab, rounded
    result = (
        cq.Workplane("XY")
        .box(base_l, base_d, BASE_T, centered=(True, True, False))
        .edges("|Z")
        .fillet(FILLET)
    )

    # block centers along X
    edge_cx = -base_l / 2 + WALL + edge_block_w / 2
    varia_cx = base_l / 2 - WALL - varia_block_w / 2

    # --- Edge 1050 cradle ------------------------------------------------------
    block = (
        cq.Workplane("XY")
        .center(edge_cx, 0)
        .box(edge_block_w, edge_block_d, edge_block_h, centered=(True, True, False))
        .translate((0, 0, BASE_T))
        .edges("|Z")
        .fillet(FILLET)
    )
    result = result.union(block)

    # angled pocket: a slab the size of the device, leaned back EDGE_LEAN deg,
    # sunk EDGE_DEPTH into the block (measured along the device body)
    pocket = (
        cq.Workplane("XY")
        .box(ep_w, ep_t, EDGE_H + 40, centered=(True, True, False))
        .rotate((0, 0, 0), (1, 0, 0), -EDGE_LEAN)
        .translate((edge_cx, EDGE_POCKET_Y, BASE_T + edge_block_h - EDGE_DEPTH))
    )
    result = result.cut(pocket)

    # screen window: drop the front wall of the cradle to a 12 mm lip so the
    # display stays visible/grabbable. Must stop short of the back wall — it
    # extends only just past the pocket's front face (which leans back with
    # the device), leaving the tall backrest intact.
    window_len = base_d / 2 + EDGE_POCKET_Y + ep_t / 2 + 1
    window = (
        cq.Workplane("XY")
        .center(edge_cx, -base_d / 2)
        .box(ep_w - 10, window_len, edge_block_h, centered=(True, False, False))
        .translate((0, 0, BASE_T + 12.0))
    )
    result = result.cut(window)

    # cable slot: from under the pocket floor, down through the base and out
    # the front, so a USB-C plug can live in the cradle permanently
    cable = (
        cq.Workplane("XY")
        .center(edge_cx, EDGE_POCKET_Y - base_d / 2)
        .box(CABLE_W, base_d / 2 + 8, BASE_T + 14, centered=(True, False, False))
    )
    result = result.cut(cable)

    # --- Varia RCT715 holster ----------------------------------------------------
    holster = (
        cq.Workplane("XY")
        .center(varia_cx, 0)
        .box(varia_block_w, varia_block_d, varia_block_h, centered=(True, True, False))
        .translate((0, 0, BASE_T))
        .edges("|Z")
        .fillet(FILLET)
    )
    result = result.union(holster)

    # vertical pocket (rounded rect bore), floor left at the bottom
    bore = (
        cq.Workplane("XY")
        .center(varia_cx, 0)
        .rect(vp_w, vp_t)
        .extrude(VARIA_DEPTH)
        .edges("|Z")
        .fillet(6.0)
        .translate((0, 0, BASE_T + varia_block_h - VARIA_DEPTH))
    )
    result = result.cut(bore)

    # front grab window so the Varia can be pinched out
    grab = (
        cq.Workplane("XY")
        .center(varia_cx, -base_d / 2)
        .box(24, base_d / 2, varia_block_h, centered=(True, False, False))
        .translate((0, 0, BASE_T + 14.0))
    )
    result = result.cut(grab)

    # cable hole through the holster floor and base
    drop = (
        cq.Workplane("XY")
        .center(varia_cx, 0)
        .circle(CABLE_W / 2)
        .extrude(BASE_T + varia_block_h)
    )
    result = result.cut(drop)

    return result


if __name__ == "__main__":
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)

    model = station()
    cq.exporters.export(model, str(out / "garmin_station.stl"))
    cq.exporters.export(model, str(out / "garmin_station.step"))
    cq.exporters.export(
        model, str(out / "garmin_station.svg"),
        opt={"projectionDir": (1, -1, 0.6), "showHidden": False},
    )

    bb = model.val().BoundingBox()
    print(f"exported garmin_station.stl/.step/.svg to {out}/")
    print(f"footprint: {bb.xlen:.1f} x {bb.ylen:.1f} mm, height {bb.zlen:.1f} mm")
