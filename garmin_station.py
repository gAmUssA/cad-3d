"""Garmin Station — desk dock for Edge 1050 + Varia RCT715 + HRM 600.

Original parametric design following the *composition* of MakerWorld's
"Garmin Station" (Bobalong, 2643039 — RTL515/Edge 530/HRM Pro sized, and
license-restricted against remixing): Edge leaning landscape across the
back like a dashboard, Varia standing in a holster on the left, HRM pod
displayed front-center with its strap draped over an arch on the right.

Device dimensions (verified against Garmin spec sheets / reviews):

  Garmin Edge 1050   60.2 x 118.5 x 16.3 mm   161 g
  Varia RCT715      106.5 x  42.0 x  31.9 mm   147 g
  HRM 600 module      68.0 x  31.6 x  10.0 mm   61 g (with strap)

All dimensions are parameters — owning the model beats remixing one.
"""

from pathlib import Path

import cadquery as cq

# --- devices (mm) -------------------------------------------------------------
EDGE_W, EDGE_H, EDGE_T = 60.2, 118.5, 16.3     # Edge 1050 (landscape at the back)
VARIA_W, VARIA_H, VARIA_T = 42.0, 106.5, 31.9  # RCT715, stands vertical
HRM_W, HRM_H, HRM_T = 68.0, 31.6, 10.0         # HRM 600 module, rests on shelf

CLEAR = 0.8          # per-side pocket clearance (bump to 1.2 for a cased Edge)

# --- station ------------------------------------------------------------------
WALL = 4.0
BASE_T = 8.0
FILLET = 5.0
EDGE_LEAN = 15.0     # Edge dashboard lean, degrees from vertical
EDGE_LIP = 14.0      # front lip holding the Edge's bottom edge
VARIA_DEPTH = 50.0   # Varia sink depth (original used ~45-50)
SHELF_LEAN = 20.0    # HRM display shelf lean
CABLE_W = 13.0       # USB-C plug clearance

# pocket cross-sections
ep_l, ep_t = EDGE_H + 2 * CLEAR, EDGE_T + 2 * CLEAR    # Edge landscape: 118.5 long
vp_w, vp_t = VARIA_W + 2 * CLEAR, VARIA_T + 2 * CLEAR
hp_w, hp_t = HRM_W + 2 * CLEAR, HRM_T + 3.0

# layout: base plate, front row (Varia | HRM shelf | strap arch), Edge at back
varia_block_w = vp_w + 2 * WALL                # 51.6
varia_block_d = vp_t + 2 * WALL                # 41.5
varia_block_h = VARIA_DEPTH + 5.0

shelf_w = hp_w + 2 * WALL                      # 77.6
shelf_d = 20.0
shelf_h = 26.0                                 # pedestal under the pod

arch_w = 42.0                                  # strap drape arch
arch_h = 58.0
arch_bar = 9.0                                 # bar thickness of the loop
arch_d = 9.0

edge_slot_l = ep_l                             # 120.1 groove across the back
edge_back_h = 38.0                             # backrest panel height

GAP = 10.0
base_l = varia_block_w + GAP + shelf_w + GAP + arch_w + 2 * WALL   # ~205
base_d = varia_block_d + 10.0 + (ep_t + 2 * WALL) + 4.0
base_front = None  # computed below


def station() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(base_l, base_d, BASE_T, centered=(True, True, False))
        .edges("|Z")
        .fillet(FILLET)
    )
    result = base

    y_front = -base_d / 2                       # front edge
    y_back = base_d / 2

    # zone centers along X (left -> right: Varia, HRM shelf, arch)
    varia_cx = -base_l / 2 + WALL + varia_block_w / 2
    shelf_cx = varia_cx + varia_block_w / 2 + GAP + shelf_w / 2
    arch_cx = shelf_cx + shelf_w / 2 + GAP + arch_w / 2

    # front row sits against the front edge
    varia_cy = y_front + WALL + varia_block_d / 2 - 2
    shelf_cy = y_front + shelf_d / 2 + 2
    arch_cy = y_front + arch_d / 2 + 4

    # --- Edge 1050 dashboard channel across the back ----------------------------
    # Built as positive geometry (leaned backrest + lip + end stops) — a
    # vertical panel with a leaned groove cut through it loses its top, since
    # the leaning slab walks backwards through the panel as z rises.
    #
    # The leaning backrest needs ~19 mm of horizontal run behind the channel
    # (height * tan(lean) + slab thickness), so the channel sits forward of the
    # back edge, and right-aligned so its left end clears the Varia holster.
    backrest_run = (edge_back_h + 6) * 0.27 + (WALL + 1) / 0.97 + 1  # tan/cos(15deg)
    groove_cy = y_back - 1 - backrest_run - ep_t / 2
    edge_ch_cx = base_l / 2 - WALL - edge_slot_l / 2 - WALL

    backrest = (
        cq.Workplane("XY")
        .box(edge_slot_l + 2 * WALL, WALL + 1, edge_back_h + 6, centered=(True, True, False))
        .rotate((0, 0, 0), (1, 0, 0), -EDGE_LEAN)
        .translate((edge_ch_cx, groove_cy + ep_t / 2 + (WALL + 1) / 2, BASE_T))
    )
    lip = (
        cq.Workplane("XY")
        .center(edge_ch_cx, groove_cy - ep_t / 2 - WALL / 2)
        .box(edge_slot_l + 2 * WALL, WALL, EDGE_LIP, centered=(True, True, False))
        .translate((0, 0, BASE_T))
    )
    result = result.union(backrest).union(lip)

    # end stops so the Edge can't slide sideways out of the channel
    for sx in (-1, 1):
        stop = (
            cq.Workplane("XY")
            .center(edge_ch_cx + sx * (edge_slot_l / 2 + WALL / 2), groove_cy)
            .box(WALL, ep_t + WALL, EDGE_LIP, centered=(True, True, False))
            .translate((0, 0, BASE_T))
        )
        result = result.union(stop)

    # USB-C slot through the lip and base under the channel
    cable = (
        cq.Workplane("XY")
        .center(edge_ch_cx, groove_cy - ep_t / 2 - WALL - 2)
        .box(CABLE_W, ep_t + WALL + 4, BASE_T + 6, centered=(True, False, False))
    )
    result = result.cut(cable)

    # --- Varia RCT715 holster (front left) --------------------------------------
    holster = (
        cq.Workplane("XY")
        .center(varia_cx, varia_cy)
        .box(varia_block_w, varia_block_d, varia_block_h, centered=(True, True, False))
        .translate((0, 0, BASE_T))
        .edges("|Z")
        .fillet(FILLET)
    )
    result = result.union(holster)

    bore = (
        cq.Workplane("XY")
        .center(varia_cx, varia_cy)
        .rect(vp_w, vp_t)
        .extrude(VARIA_DEPTH)
        .edges("|Z")
        .fillet(6.0)
        .translate((0, 0, BASE_T + varia_block_h - VARIA_DEPTH))
    )
    result = result.cut(bore)

    grab = (
        cq.Workplane("XY")
        .center(varia_cx, varia_cy - varia_block_d)
        .box(24, varia_block_d, varia_block_h, centered=(True, False, False))
        .translate((0, 0, BASE_T + 14.0))
    )
    result = result.cut(grab)

    drop = (
        cq.Workplane("XY")
        .center(varia_cx, varia_cy)
        .circle(CABLE_W / 2)
        .extrude(BASE_T + varia_block_h)
    )
    result = result.cut(drop)

    # --- HRM 600 display shelf (front center) -----------------------------------
    pedestal = (
        cq.Workplane("XY")
        .center(shelf_cx, shelf_cy)
        .box(shelf_w, shelf_d, shelf_h, centered=(True, True, False))
        .translate((0, 0, BASE_T))
        .edges("|Z")
        .fillet(3.0)
    )
    result = result.union(pedestal)

    # angled tray on top: pod lies long-axis horizontal, leaning back
    tray_pocket = (
        cq.Workplane("XY")
        .box(hp_w, hp_t, HRM_H + 20, centered=(True, True, False))
        .rotate((0, 0, 0), (1, 0, 0), -SHELF_LEAN)
        .translate((shelf_cx, shelf_cy, BASE_T + shelf_h - 8.0))
    )
    result = result.cut(tray_pocket)

    # --- strap arch (front right) ------------------------------------------------
    # XZ workplane extrudes toward -Y: outer spans y in [-arch_d, 0], so shift
    # by arch_cy + arch_d/2 to center the loop at arch_cy
    arch_outer = (
        cq.Workplane("XZ")
        .center(arch_cx, (BASE_T + arch_h) / 2 + 1)
        .rect(arch_w, arch_h + 2)
        .extrude(arch_d)
        .edges("|Y")
        .fillet(8.0)
        .translate((0, arch_cy + arch_d / 2, 0))
    )
    # inner cut limited to the arch's own depth — a through-everything extrude
    # would punch a hole in whatever sits behind the arch
    arch_inner = (
        cq.Workplane("XZ")
        .center(arch_cx, (BASE_T + arch_h) / 2 + 4)
        .rect(arch_w - 2 * arch_bar, arch_h - 2 * arch_bar)
        .extrude(arch_d + 4)
        .edges("|Y")
        .fillet(5.0)
        .translate((0, arch_cy + arch_d / 2 + 2, 0))
    )
    result = result.union(arch_outer).cut(arch_inner)

    return result


if __name__ == "__main__":
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)

    model = station()
    cq.exporters.export(model, str(out / "garmin_station.stl"))
    cq.exporters.export(model, str(out / "garmin_station.step"))

    bb = model.val().BoundingBox()
    print(f"exported garmin_station.stl/.step to {out}/")
    print(f"footprint: {bb.xlen:.1f} x {bb.ylen:.1f} mm, height {bb.zlen:.1f} mm")
