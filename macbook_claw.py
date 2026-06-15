"""MacBook claw — clamshell holder that keeps the lid cracked open.

Original build inspired by "The OpenClaws" product photo (keep your agents
running 24/7): a hand-shaped clip that perches on the laptop's side edge,
holding the lid open by GAP so the lid-closed sensor never trips.

Mechanics (side profile, laptop to the right / +y inward):

         ___
       /  fff   three fingers curl over the lid top
      |  ==     lid edge rests on a small shelf
      |  |      stem runs down the side, spanning the gap
      |__|__    foot bar tucks under the base; lid spring force
                presses the shelf down -> foot reacts under the base

Hand anatomy: four fingers of differing length curl over the lid, a thumb
(dense sphere-chain capsule) wraps around the palm side and presses under
the base, and the palm heel reaches under the base only on the pinky half —
the way a real hand clasps an edge. Functional faces stay flat.

Print LYING ON THE PINKY SIDE (-x face down, thumb up) — layers run along
the profile plane (strongest for the finger load). The thumb's underside is
a horizontal-cylinder overhang: TPU 95A bridges it fine (and is the right
material — the real product is soft); in PETG give it a touch of support.

Fit parameters — measure YOUR MacBook side edge with calipers:
  BASE_T  base slab thickness at the side (MBP 14 ~ 9.6)
  LID_T   lid thickness at the side       (MBP 14 ~ 6.0)
Defaults are MacBook Pro 14. For an Air try BASE_T=7.6, LID_T=4.4.

Exports (out/): macbook_claw.stl / .step

All dimensions are parameters — owning the model beats remixing one.
"""

from pathlib import Path

import cadquery as cq

# --- laptop fit (mm) -----------------------------------------------------------
BASE_T = 9.6         # base slab thickness at the side edge
LID_T = 6.0          # lid thickness at the side edge
GAP = 20.0           # how far the claw holds the lid open (at the claw)
LID_CL = 0.8         # lid slot clearance
HUG_R = 5.0          # bottom-edge radius of the base — the foot's inner
                     # corner is a matching concave arc that hugs it (MBP 14
                     # ~5; go a touch bigger if unsure, smaller digs corners)

# --- claw ----------------------------------------------------------------------
WIDTH = 22.0         # overall width (across the four fingers)
STEM_T = 8.0         # stem thickness (outside the laptop side)
FOOT_T = 5.0         # palm-heel thickness (under the base)
FOOT_REACH = 9.0     # heel reach under the base (the thumb reaches deeper)
TAIL = 6.0           # heel tail past the stem
SHELF_REACH = 7.0    # lid-rest shelf protrusion
SHELF_T = 3.0
FINGER_REACH = 15.5  # longest finger (middle) over the lid top
FINGER_T = 3.5       # finger thickness at the tip

# four fingers: (center x, tip reach) — index by the thumb (+x), then
# middle, ring, pinky; slots between them at +/-5.5 and 0
FINGERS = ((8.25, 14.0), (2.75, 15.8), (-2.75, 14.5), (-8.25, 12.0))
SLOT_XS = (-5.5, 0.0, 5.5)

# thumb: short, THICK, webbed digit — chain of overlapping spheres
# (x, y, z, r). First points sit buried in the palm (thenar muscle, no thin
# neck), it bends once at the knuckle and presses a broad pad under the base.
# Thick + short + rooted reads as a thumb; thin + long + uniform = a worm.
# A sphere chain is OCC-safe where a 3D sweep + fillets is crash roulette.
THUMB = (
    (4.5, 1.5, 8.5, 5.8),   # thenar root, buried deep in the palm mass
    (8.0, -1.5, 6.5, 5.2),  # thenar web / thumb base
    (10.8, -2.6, 3.2, 4.6), # proximal — thick
    (12.3, -2.0, 0.2, 4.2), # knuckle, starting to turn under
    (12.1, 1.2, -1.4, 4.0), # rolling under the base
    (10.8, 4.0, -1.8, 3.9), # broad pad pressing up under the base
    (9.7, 6.0, -1.7, 3.7),  # pad tip
)

R_PROFILE = 1.2      # profile corner fillet
R_SIDE = 1.0         # side-face perimeter fillet
R_FINGER = 1.4       # finger slot / tip rounding

# --- derived ---------------------------------------------------------------------
lid_bot = BASE_T + GAP               # lid underside at the claw
lid_top = lid_bot + LID_T + LID_CL   # finger underside
shelf_z = lid_bot - SHELF_T


def claw() -> cq.Workplane:
    """One claw: organic profile in YZ (y inward, z up), extruded across X,
    then sculpted by a width-shaper prism (waisted stem, spread knuckles),
    knuckle bumps, and tapered finger slots. Functional faces stay flat:
    foot top, stem inner, shelf, finger underside."""
    result = (
        cq.Workplane("YZ")
        .moveTo(-7.0 - TAIL, 0)
        .lineTo(-7.0 - TAIL, -FOOT_T)
        .lineTo(FOOT_REACH, -FOOT_T)             # foot bar under the base
        .lineTo(FOOT_REACH, 0)
        .lineTo(HUG_R, 0)                        # base bottom plane
        .threePointArc(                          # concave arc hugging the
            (HUG_R * 0.2929, HUG_R * 0.2929),    # base's curved bottom edge
            (0, HUG_R),
        )
        .lineTo(0, shelf_z)                      # stem inner face (side + gap)
        .lineTo(SHELF_REACH, shelf_z)
        .lineTo(SHELF_REACH, lid_bot)            # lid-rest shelf
        .lineTo(0, lid_bot)
        .lineTo(0, lid_top)                      # lid edge sits against this
        .lineTo(FINGER_REACH + 0.5, lid_top)     # finger underside on the lid
        .lineTo(FINGER_REACH + 0.5, lid_top + 3.0)
        .threePointArc(                          # dome up over the knuckles
            (8.0, lid_top + 10.7), (0.0, lid_top + 13.7)
        )
        .spline(                                 # back of hand -> waisted stem
            [
                (-6.0, lid_top + 12.7),
                (-9.3, lid_top + 7.2),
                (-6.8, 24.0),
                (-7.0, 0.0),
            ],
            includeCurrent=True,
        )
        .close()
        .extrude(WIDTH)
        .translate((-WIDTH / 2, 0, 0))
    )

    # profile fillet on the full-width slab — BEFORE the intersect, while
    # every |X edge still spans the part (post-intersect they end on the
    # sculpted side faces and OCC refuses)
    for r in (R_PROFILE, 0.8):
        try:
            result = result.edges("|X").fillet(r)
            break
        except Exception:
            continue

    # width-shaper: wide foot, waisted stem, spread knuckles, tapered crown.
    # Intersecting replaces the slab sides with a sculpted silhouette.
    zb, zt1, zt2, zt3 = -FOOT_T - 1, lid_top + 4, lid_top + 13, lid_top + 18
    shaper = (
        cq.Workplane("XZ", origin=(0, 18, 0))
        .moveTo(-12.0, zb)
        .lineTo(12.0, zb)
        .spline([(11.6, 1.5), (8.2, 16.0), (11.2, zt1), (9.6, zt2), (8.0, zt3)], includeCurrent=True)
        .lineTo(-8.0, zt3)
        .spline([(-9.6, zt2), (-11.2, zt1), (-8.2, 16.0), (-11.6, 1.5)], includeCurrent=True)
        .close()  # short straight hop to the start — a spline ending exactly
        # on the start point makes close() emit a zero-length edge (OCC fail)
        .extrude(34)
    )
    try:
        shaper = shaper.edges("|Y").fillet(3.0)
    except Exception:
        pass
    result = result.intersect(shaper)
    # NOTE: no global edges().fillet() after this point — on this mixed
    # straight/curved geometry OCC SEGFAULTS (exit 139) rather than raising,
    # so try/except is no protection. The shaper's |Y rounding + the slab's
    # profile fillet carry the soft look.

    # the heel only reaches under the base on the pinky half — the thumb is
    # the under-base grip on its own side, like a real clasp (cut BEFORE the
    # thumb union so the thumb itself survives)
    heel_trim = (
        cq.Workplane("XY")
        .center(10.5, 6.5)
        .box(13.0, 13.0, FOOT_T + 1.0, centered=(True, True, False))
        .translate((0, 0, -FOOT_T - 0.5))
    )
    result = result.cut(heel_trim)

    # thumb wrapping around the palm side and under the base — the sparse
    # waypoint spheres are lerp-densified into a smooth tapered capsule
    beads = []
    for (x0, y0, z0, r0), (x1, y1, z1, r1) in zip(THUMB, THUMB[1:]):
        d = ((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2) ** 0.5
        n = max(1, int(d / 0.7))
        for i in range(n):
            t = i / n
            beads.append(
                (x0 + t * (x1 - x0), y0 + t * (y1 - y0),
                 z0 + t * (z1 - z0), r0 + t * (r1 - r0))
            )
    beads.append(THUMB[-1])
    for tx, ty, tz, tr in beads:
        result = result.union(
            cq.Workplane("XY").sphere(tr).translate((tx, ty, tz))
        )

    # tapered finger slots — narrow at the wrist, wide at the tips, full
    # depth over the knuckle dome so the four prongs read as fingers
    for sx in SLOT_XS:
        slot = (
            cq.Workplane("XY")
            .polyline(
                [
                    (sx - 0.5, -12.0), (sx + 0.5, -12.0),
                    (sx + 1.0, 17.0), (sx - 1.0, 17.0),
                ]
            )
            .close()
            .extrude(26)
            .translate((0, 0, lid_top - 0.5))
        )
        result = result.cut(slot)

    # individual finger lengths — trim each tip back (middle longest,
    # pinky shortest); cutters stay above lid_top so shelf/heel are safe
    for cx, tip in FINGERS:
        if tip >= FINGER_REACH + 0.5:
            continue
        trim = (
            cq.Workplane("XY")
            .center(cx, tip + 4.0)
            .box(5.9, 8.0, 26, centered=(True, True, False))
            .translate((0, 0, lid_top - 0.5))
        )
        result = result.cut(trim)

    # round the slot walls and finger tips (best effort, shrinking radius)
    for r in (R_FINGER, 1.0, 0.7):
        try:
            result = result.edges(
                cq.selectors.BoxSelector(
                    (-WIDTH / 2 - 1, -1.0, lid_top - 1), (WIDTH / 2 + 1, 18.0, 70.0)
                )
            ).fillet(r)
            break
        except Exception:
            continue

    return result


def laptop_mockup() -> dict[str, cq.Workplane]:
    """Ghost MacBook side-edge section (lid drawn parallel at the gap —
    real lid is slightly angled toward the hinge). Renders only."""
    base = (
        cq.Workplane("XY")
        .box(140, 90, BASE_T, centered=(True, False, False))
        .edges("|Z").fillet(8)
        .edges("<Z").fillet(HUG_R - 0.3)   # the curved bottom edge the foot hugs
        .translate((0, 0, 0))
    )
    lid = (
        cq.Workplane("XY")
        .box(140, 90, LID_T, centered=(True, False, False))
        .edges("|Z").fillet(8)
        .translate((0, 0, lid_bot))
    )
    return {"base": base, "lid": lid}


if "show_object" in globals():
    # CQ-editor live preview: open this file in cq-editor, hit Render (F5)
    show_object(claw(), name="macbook_claw")  # noqa: F821

if __name__ == "__main__":
    import os

    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)

    solid = claw()
    # fine tessellation — the thumb is sphere-union curves; the default 0.1mm
    # linear tolerance facets them coarsely and they read "ribbed/worm-like"
    cq.exporters.export(solid, str(out / "macbook_claw.stl"),
                        tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(solid, str(out / "macbook_claw.step"))

    if os.environ.get("MOCKUP"):
        for name, part in laptop_mockup().items():
            cq.exporters.export(part, str(out / f"mock_claw_{name}.stl"))
        print("laptop mockup STLs exported")

    bb = solid.val().BoundingBox()
    print(f"exported STL + STEP to {out}/")
    print(f"claw: {bb.xlen:.1f} wide x {bb.ylen:.1f} deep x {bb.zlen:.1f} tall")
