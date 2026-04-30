"""PBR material showcase — five spheres with different roughness / metallic values."""
import math
import blendr_helpers as bh


def uv_sphere(name, radius=1.0, n_lat=24, n_lon=32):
    verts, faces = [], []
    # Top pole
    verts.append((0, 0, radius))
    for i in range(1, n_lat):
        phi = math.pi * i / n_lat
        for j in range(n_lon):
            theta = 2 * math.pi * j / n_lon
            verts.append((
                radius * math.sin(phi) * math.cos(theta),
                radius * math.sin(phi) * math.sin(theta),
                radius * math.cos(phi),
            ))
    verts.append((0, 0, -radius))
    bottom = len(verts) - 1
    for j in range(n_lon):
        faces.append((0, 1 + j, 1 + (j + 1) % n_lon))
    for i in range(n_lat - 2):
        for j in range(n_lon):
            a = 1 + i * n_lon + j
            b = 1 + i * n_lon + (j + 1) % n_lon
            c = 1 + (i + 1) * n_lon + (j + 1) % n_lon
            d = 1 + (i + 1) * n_lon + j
            faces.append((a, b, c, d))
    for j in range(n_lon):
        a = 1 + (n_lat - 2) * n_lon + j
        b = 1 + (n_lat - 2) * n_lon + (j + 1) % n_lon
        faces.append((bottom, b, a))
    return bh.mesh_from_pydata(name, verts, faces=faces)


bh.empty_scene()
bh.plane(name="Floor", size=30).location = (0, 0, -1.0)

# Five spheres, roughness from 0 → 1 left to right, all metallic
for i, rough in enumerate([0.0, 0.25, 0.5, 0.75, 1.0]):
    s = uv_sphere(f"Sphere_{i}")
    s.location = (i * 2.5 - 5, 0, 0)
    mat = bh.principled(f"Mat_{i}", base_color=(0.85, 0.65, 0.10, 1.0),
                        metallic=1.0, roughness=rough)
    bh.assign_material(s, mat)

bh.add_camera(location=(0, -16, 4), look_at=(0, 0, 0), focal_length_mm=35.0)
bh.three_point_light()
bh.set_world_color((0.07, 0.07, 0.09))
