"""Import/export GLB — build a small scene and export to GLB for web/3D viewers.

Reads optional argv after `--`:
  blendr run import_export_glb.py -- /path/to/output.glb
"""
import os
import sys
import blendr_helpers as bh
import blendr_runtime

# Pick output path: arg after `--`, else env-derived
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_glb = argv[0] if argv else os.path.join(blendr_runtime.state.out_dir, "scene.glb")

bh.empty_scene()
ground = bh.plane(name="Ground", size=10)
ground_mat = bh.principled("Ground", base_color=(0.20, 0.22, 0.25, 1.0), roughness=0.9)
bh.assign_material(ground, ground_mat)

cube = bh.cube("Cube")
cube.location = (0, 0, 1)
cube_mat = bh.principled("Cube", base_color=(0.20, 0.55, 0.85, 1.0),
                         metallic=0.3, roughness=0.4)
bh.assign_material(cube, cube_mat)

bh.add_camera(location=(5, -5, 4), look_at=(0, 0, 1))
bh.three_point_light()

# Export. The runtime will still save the .blend and render a preview.
bh.export_glb(out_glb)
print(f"[template] exported GLB: {out_glb}")
