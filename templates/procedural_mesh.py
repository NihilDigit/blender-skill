"""Procedural mesh — a torus knot built from raw vertex/face math.

Demonstrates building geometry without `bpy.ops`, which is essential
in headless mode where viewport context is unreliable.
"""
import math
import blendr_helpers as bh


def torus_knot(p=2, q=3, R=2.0, r=0.6, n_seg=200, n_tube=24):
    verts, faces = [], []
    for i in range(n_seg):
        t = 2 * math.pi * i / n_seg
        # Centre curve point on the (p, q) torus knot
        cx = (R + math.cos(q * t)) * math.cos(p * t)
        cy = (R + math.cos(q * t)) * math.sin(p * t)
        cz = math.sin(q * t)
        # Approximate tangent for tube frame
        dt = 1e-3
        tn = t + dt
        nx = (R + math.cos(q * tn)) * math.cos(p * tn) - cx
        ny = (R + math.cos(q * tn)) * math.sin(p * tn) - cy
        nz = math.sin(q * tn) - cz
        ln = math.sqrt(nx * nx + ny * ny + nz * nz) or 1
        tx, ty, tz = nx / ln, ny / ln, nz / ln
        # Pick an arbitrary normal then orthogonalise
        ux, uy, uz = -ty, tx, 0
        un = math.sqrt(ux * ux + uy * uy + uz * uz) or 1
        ux, uy, uz = ux / un, uy / un, uz / un
        # Bitangent = tangent × up
        vx = ty * uz - tz * uy
        vy = tz * ux - tx * uz
        vz = tx * uy - ty * ux
        for j in range(n_tube):
            a = 2 * math.pi * j / n_tube
            ca, sa = math.cos(a), math.sin(a)
            verts.append((
                cx + r * (ca * ux + sa * vx),
                cy + r * (ca * uy + sa * vy),
                cz + r * (ca * uz + sa * vz),
            ))
    for i in range(n_seg):
        for j in range(n_tube):
            a = i * n_tube + j
            b = i * n_tube + (j + 1) % n_tube
            c = ((i + 1) % n_seg) * n_tube + (j + 1) % n_tube
            d = ((i + 1) % n_seg) * n_tube + j
            faces.append((a, b, c, d))
    return verts, faces


bh.empty_scene()
verts, faces = torus_knot()
knot = bh.mesh_from_pydata("TorusKnot", verts, faces=faces)

mat = bh.principled("Bronze", base_color=(0.78, 0.45, 0.20, 1.0),
                    metallic=0.9, roughness=0.25)
bh.assign_material(knot, mat)

bh.plane(name="Floor", size=20).location = (0, 0, -1.5)
bh.add_camera(location=(6, -6, 4), look_at=(0, 0, 0))
bh.three_point_light()
bh.set_world_color((0.04, 0.04, 0.05))
