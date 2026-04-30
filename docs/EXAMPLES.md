# Example scripts

## A. Procedural skull (low-poly)

```python
import math
import blendr_helpers as bh
from mathutils import Vector

bh.empty_scene()

# Cranium: deformed UV sphere
verts, faces = [], []
n_lat, n_lon = 16, 24
for i in range(n_lat + 1):
    phi = math.pi * i / n_lat
    for j in range(n_lon):
        theta = 2 * math.pi * j / n_lon
        # Squash front-to-back, stretch top-to-bottom
        x = 1.2 * math.sin(phi) * math.cos(theta)
        y = 0.95 * math.sin(phi) * math.sin(theta)
        z = 1.4 * math.cos(phi)
        # Bulge the back
        if y < 0:
            y *= 1.15
        verts.append((x, y, z))

for i in range(n_lat):
    for j in range(n_lon):
        a = i * n_lon + j
        b = i * n_lon + (j + 1) % n_lon
        c = (i + 1) * n_lon + (j + 1) % n_lon
        d = (i + 1) * n_lon + j
        faces.append((a, b, c, d))

skull = bh.mesh_from_pydata("Skull", verts, faces=faces)
mat = bh.principled("Bone", base_color=(0.92, 0.88, 0.78, 1.0), roughness=0.55)
bh.assign_material(skull, mat)

bh.add_camera(location=(3.5, -3.5, 1.5), look_at=(0, 0, 0.2))
bh.three_point_light()
bh.set_world_color((0.04, 0.04, 0.05))
```

## B. Architectural massing study

```python
import blendr_helpers as bh

bh.empty_scene()

# Ground
ground = bh.plane("Ground", size=40)
bh.assign_material(ground, bh.principled("Tarmac",
    base_color=(0.13, 0.13, 0.14, 1.0), roughness=0.95))

# Three buildings of varying heights
heights = [(0.0, 4.0), (3.0, 6.5), (6.0, 3.5)]
for x, h in heights:
    b = bh.cube("Building")
    b.scale = (1.5, 1.5, h / 2)
    b.location = (x, 0, h / 2)
    bh.assign_material(b, bh.principled("Concrete",
        base_color=(0.65, 0.62, 0.58, 1.0), roughness=0.7))

bh.add_camera(location=(8, -10, 5), look_at=(3, 0, 2.5), focal_length_mm=35)
bh.three_point_light(key_energy=4.0)
bh.set_world_color((0.55, 0.65, 0.75), strength=0.5)  # sky-ish
```

Run with `blendr sheet <script.py>` for a useful 4-angle overview.

## C. Export a model for the web (GLB)

```python
import os, sys
import blendr_helpers as bh
import blendr_runtime

# Pick output: arg after `--`, else default
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_glb = argv[0] if argv else os.path.join(blendr_runtime.state.out_dir, "model.glb")

bh.empty_scene()
cube = bh.cube("Hero")
mat = bh.principled("HeroMat", base_color=(0.2, 0.55, 0.85, 1.0),
                    metallic=0.3, roughness=0.4)
bh.assign_material(cube, mat)

bh.add_camera(location=(4, -4, 3), look_at=(0, 0, 0))
bh.add_sun()

bh.export_glb(out_glb)
print(f"GLB → {out_glb}")
```

```bash
blendr run script.py -- /path/to/output.glb
```

## D. Final beauty render

```python
import bpy
import blendr_helpers as bh

bh.empty_scene()
# ... build scene ...

# Override the runtime's preview defaults for a quality render
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 256          # bump from 16 → 256
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.cycles.use_denoising = True
```

Or via env vars:

```bash
BLENDR_SAMPLES=256 BLENDR_RES=1920x1080 blendr run script.py
```

## E. Just inspect an existing .blend

```bash
blendr inspect /path/to/file.blend
```

## F. Open the latest iter in the GUI

```bash
ls -t ~/blender-work/iters | head -1                # see most recent
blendr open <that-iter-name>
```
