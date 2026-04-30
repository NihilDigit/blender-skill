"""Hello, Blender — a single coloured cube. The minimum viable scene."""
import blendr_helpers as bh

bh.empty_scene()
cube = bh.cube("HelloCube")
mat = bh.principled("Red", base_color=(0.85, 0.15, 0.15, 1.0), roughness=0.4)
bh.assign_material(cube, mat)

bh.add_camera(location=(4.5, -4.5, 3.5), look_at=(0, 0, 0))
bh.add_sun(energy=4.0)
bh.set_world_color(color=(0.06, 0.07, 0.09))

# blendr_finalize will auto-save .blend and render preview.png
