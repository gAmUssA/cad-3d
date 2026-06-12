"""Garmin Station — desk dock for Edge 1050 + Varia RCT715 + HRM 600.

Original parametric design following the *composition* of MakerWorld's
"Garmin Station" (Bobalong, 2643039 — RTL515/Edge 530/HRM Pro sized, and
license-restricted against remixing): Edge leaning landscape across the
back like a dashboard, Varia standing in a holster on the left, HRM 600
pod displayed on the front-center shelf, strap draped over the arch on
the right.

Device dimensions (verified against Garmin spec sheets / reviews):

  Garmin Edge 1050   60.2 x 118.5 x 16.3 mm   161 g
  Varia RCT715      106.5 x  42.0 x  31.9 mm   147 g
  HRM 600 module      68.0 x  31.6 x  10.0 mm   61 g (with strap)

Exports (out/):
  garmin_station_body.stl  station with a 1 mm logo pocket   } import both into
  garmin_station_logo.stl  flush GARMIN text + delta inlay   } Bambu Studio as
                                                               one object, assign
                                                               a color per part
  garmin_station.stl       single-color merged fallback
  garmin_station.step      lossless CAD interchange

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
EDGE_LEAN = 15.0     # Edge dashboard lean, degrees from vertical
EDGE_LIP = 14.0      # front lip holding the Edge's bottom edge
VARIA_DEPTH = 50.0   # Varia sink depth (original used ~45-50)
SHELF_LEAN = 20.0    # HRM display shelf lean
CABLE_W = 13.0       # USB-C plug clearance

# design language: one radius family + softened top edges everywhere, so the
# towers read as one product instead of boolean'd boxes
R_BASE = 14.0        # base plinth corner radius
R_TOWER = 8.0        # tower vertical-corner radius
SOFT = 2.0           # top-edge (crown) fillet on every tower
CHAMFER = 1.5        # base top-perimeter chamfer
LABEL = "GARMIN"     # inlaid on the pedestal face ("" to disable)
LOGO_DEPTH = 1.0     # inlay depth — printed as a separate body for color swap

# pocket cross-sections
ep_l, ep_t = EDGE_H + 2 * CLEAR, EDGE_T + 2 * CLEAR    # Edge landscape: 120 long
vp_w, vp_t = VARIA_W + 2 * CLEAR, VARIA_T + 2 * CLEAR
hp_w, hp_t = HRM_W + 2 * CLEAR, HRM_T + 3.0

# blocks
varia_block_w = vp_w + 2 * WALL
varia_block_d = vp_t + 2 * WALL
varia_block_h = VARIA_DEPTH + 5.0

shelf_w = hp_w + 2 * WALL
shelf_d = 20.0
shelf_h = 26.0

arch_w = 42.0
arch_h = 58.0
arch_bar = 9.0
arch_d = 9.0

edge_slot_l = ep_l
edge_back_h = 38.0

# --- layout (module level so the logo + mockups share it) ----------------------
GAP = 10.0
base_l = varia_block_w + GAP + shelf_w + GAP + arch_w + 2 * WALL
base_d = varia_block_d + 10.0 + (ep_t + 2 * WALL) + 4.0

y_front = -base_d / 2
y_back = base_d / 2

varia_cx = -base_l / 2 + WALL + varia_block_w / 2
shelf_cx = varia_cx + varia_block_w / 2 + GAP + shelf_w / 2
arch_cx = shelf_cx + shelf_w / 2 + GAP + arch_w / 2

varia_cy = y_front + WALL + varia_block_d / 2 - 2
shelf_cy = y_front + shelf_d / 2 + 2
arch_cy = y_front + arch_d / 2 + 4

# leaning backrest needs horizontal run = height*tan(lean) + slab thickness
backrest_run = (edge_back_h + 6) * 0.27 + (WALL + 1) / 0.97 + 1
groove_cy = y_back - 1 - backrest_run - ep_t / 2
edge_ch_cx = base_l / 2 - WALL - edge_slot_l / 2 - WALL

ped_front_y = shelf_cy - shelf_d / 2            # pedestal front face (logo plane)


def soften(part: cq.Workplane, r: float = SOFT) -> cq.Workplane:
    """Fillet a part's top edges; skip silently if OCC can't (tiny edges)."""
    try:
        return part.faces(">Z").edges().fillet(r)
    except Exception:
        return part


def logo() -> cq.Workplane | None:
    """GARMIN wordmark + delta triangle over the N, as a flush 1 mm inlay.

    Returned solid is also used to cut its own pocket in the pedestal, so
    body + logo print together as one multi-color object (zero clearance —
    they're sliced together, not assembled).
    """
    if not LABEL:
        return None
    txt = (
        cq.Workplane("XZ", origin=(shelf_cx, ped_front_y, BASE_T + shelf_h / 2 - 2))
        .text(LABEL, 8, -LOGO_DEPTH, font="Helvetica", kind="bold")
    )
    bb = txt.val().BoundingBox()
    # delta triangle sitting above the last letter
    tri_cx = bb.xmax - 2.6
    tri_base = bb.zmax + 1.6
    tri = (
        cq.Workplane("XZ", origin=(0, ped_front_y, 0))
        .polyline([(tri_cx - 2.6, tri_base), (tri_cx + 2.6, tri_base), (tri_cx, tri_base + 4.0)])
        .close()
        .extrude(-LOGO_DEPTH)
    )
    return txt.union(tri)


def station() -> cq.Workplane:
    """Station body. Logo pocket is cut at the end (see logo())."""
    result = (
        cq.Workplane("XY")
        .box(base_l, base_d, BASE_T, centered=(True, True, False))
        .edges("|Z")
        .fillet(R_BASE)
        .faces(">Z")
        .chamfer(CHAMFER)
    )

    # --- Edge 1050 dashboard channel across the back ----------------------------
    # Positive geometry (leaned backrest + lip + end stops) — a vertical panel
    # with a leaned groove cut through it loses its top, since the leaning slab
    # walks backwards through the panel as z rises.
    backrest = (
        cq.Workplane("XY")
        .box(edge_slot_l + 2 * WALL, WALL + 1, edge_back_h + 6, centered=(True, True, False))
        .edges("|Y and >Z")
        .fillet(R_TOWER)
        .faces(">Z")
        .edges()
        .fillet(1.8)
        .rotate((0, 0, 0), (1, 0, 0), -EDGE_LEAN)
        .translate((edge_ch_cx, groove_cy + ep_t / 2 + (WALL + 1) / 2, BASE_T))
    )
    lip = soften(
        cq.Workplane("XY")
        .center(edge_ch_cx, groove_cy - ep_t / 2 - WALL / 2)
        .box(edge_slot_l + 2 * WALL, WALL, EDGE_LIP, centered=(True, True, False))
        .translate((0, 0, BASE_T)),
        1.5,
    )
    result = result.union(backrest).union(lip)

    for sx in (-1, 1):  # end stops so the Edge can't slide sideways
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
    holster = soften(
        cq.Workplane("XY")
        .center(varia_cx, varia_cy)
        .box(varia_block_w, varia_block_d, varia_block_h, centered=(True, True, False))
        .translate((0, 0, BASE_T))
        .edges("|Z")
        .fillet(R_TOWER)
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
    pedestal = soften(
        cq.Workplane("XY")
        .center(shelf_cx, shelf_cy)
        .box(shelf_w, shelf_d, shelf_h, centered=(True, True, False))
        .translate((0, 0, BASE_T))
        .edges("|Z")
        .fillet(6.0)
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
    # Stadium profile: outer corners at half the loop width read as a handle.
    # XZ workplane extrudes toward -Y: outer spans y in [-arch_d, 0], so shift
    # by arch_cy + arch_d/2 to center the loop at arch_cy.
    arch = (
        cq.Workplane("XZ")
        .center(arch_cx, (BASE_T + arch_h) / 2 + 1)
        .rect(arch_w, arch_h + 2)
        .extrude(arch_d)
        .edges("|Y")
        .fillet(arch_w / 2 - 0.1)
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
        .fillet((arch_w - 2 * arch_bar) / 2 - 0.1)
        .translate((0, arch_cy + arch_d / 2 + 2, 0))
    )
    arch = arch.cut(arch_inner)
    try:
        arch = arch.edges().fillet(1.2)
    except Exception:
        pass
    result = result.union(arch)

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
        .rotate((0, 0, 0), (1, 0, 0), -EDGE_LEAN)
        .translate((edge_ch_cx, groove_cy, BASE_T + 0.5))
    )
    varia = (
        cq.Workplane("XY")
        .box(VARIA_W, VARIA_T, VARIA_H, centered=(True, True, False))
        .edges("|Z")
        .fillet(10.0)
        .translate((varia_cx, varia_cy, BASE_T + varia_block_h - VARIA_DEPTH + 0.5))
    )
    pod = (
        cq.Workplane("XY")
        .box(HRM_W, HRM_T, HRM_H, centered=(True, True, False))
        .edges("|Y")
        .fillet(4.0)
        .rotate((0, 0, 0), (1, 0, 0), -SHELF_LEAN)
        .translate((shelf_cx, shelf_cy, BASE_T + shelf_h - 7.0))
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
