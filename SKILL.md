---
name: blender-skill
description: Drive Blender headlessly to build 3D scenes, render previews, and export models (GLB/FBX/etc). Use whenever the user asks to make, edit, render, or inspect 3D content with Blender — phrases like "用 blender 做...", "渲染这个...", "build a 3D model", "make a turntable of X", "export to GLB", "show me a contact sheet of...". Closes the human-in-the-loop gap by auto-rendering a preview PNG after each script run, which the model reads back inline to see what it just made.
---

# blender-skill

A headless Blender workflow optimised for AI agents. Every script run produces three artifacts in a versioned `iter_NNNN_<slug>/` directory: the Python script that built the scene, a `scene.blend` file the user can inspect in the GUI, and a `preview.png` that the agent reads back to verify its work.

## When to use this skill

Trigger on:
- "用 blender ..." / "Blender 里 ..." / "render ... in Blender"
- 3D-modelling requests: "make a 3D X", "build a procedural Y", "show me a model of Z"
- Render requests: "render that", "give me a preview", "show me the front/side/top"
- Export requests: "export to GLB / FBX / OBJ", "make a glTF for the web"
- Animation: "turntable of X", "rotate around X 360°"

Do **not** trigger for: 2D image editing, raster compositing, video editing (use a different tool).

## Quick start

```bash
# 1) Health check
blendr doctor

# 2) Run a template scene
blendr new hello --name first-cube
blendr run ~/blender-work/iters/iter_0001_first-cube/script.py

# 3) Read the preview back into the conversation
# Use the Read tool on iters/iter_NNNN_*/preview.png
```

## The HITL loop (this is the core workflow)

```
1. Write a Python script that builds a scene using blendr_helpers
2. blendr run <script.py>             → writes scene.blend + preview.png
3. Read tool on preview.png            → image enters model context
4. Self-check: is geometry / framing / lighting right?
5. If wrong: edit script → goto 2.   If right: report to user with image
6. User says "tweak X" → edit → goto 2
```

Each iteration takes ~1.5–3 seconds (CYCLES + CPU + 16 samples + 512²) — fast enough to feel interactive even though Blender cold-starts each time.

For complex shapes, prefer `blendr sheet <script>` which renders 4 angles (front/right/top/iso) into a 2×2 contact sheet — much better for catching bad geometry than a single view.

## Writing scripts

Always start with:

```python
import blendr_helpers as bh

bh.empty_scene()  # wipes default cube/light/camera
```

Then build using the helper API (geometry, materials, camera, lighting). The runtime auto-saves the `.blend` and renders the preview after your script finishes; you do **not** need to call `bpy.ops.render.render` yourself.

### The cardinal rule for headless Blender

**Use `bpy.data.*` constructors, NOT `bpy.ops.mesh.primitive_*`.**

In headless mode (`blender -b`), `bpy.context` lacks an active 3D viewport. Most operators need a viewport context and will fail or silently do nothing. The `bpy.data.*` API works unconditionally:

```python
# Bad — needs viewport context, fragile in -b mode
bpy.ops.mesh.primitive_cube_add(size=2.0, location=(0, 0, 0))

# Good — works anywhere
mesh = bpy.data.meshes.new("CubeMesh")
mesh.from_pydata(verts, [], faces)
obj = bpy.data.objects.new("Cube", mesh)
bpy.context.scene.collection.objects.link(obj)
```

`blendr_helpers` wraps the common cases (`bh.cube`, `bh.plane`, `bh.mesh_from_pydata`, `bh.principled`, `bh.add_camera`, `bh.three_point_light`, `bh.export_glb`, ...). When you need something it doesn't cover, fall back to direct `bpy.data` calls — see `docs/PITFALLS.md`.

### Render engine

The runtime forces **CYCLES + CPU** for previews because EEVEE and Workbench require an OpenGL context, which is unreliable in pure-headless environments. CYCLES at 16 samples 512² is fast (~1s) and produces real lighting / shadows / reflections.

If you want a final beauty render, set `BLENDR_SAMPLES=512 BLENDR_RES=1920x1080` for that run, or pass `--samples 512 --res 1920x1080`.

## CLI reference

```
blendr run <script.py>         run script + auto preview (default mode)
blendr render <script.py>      same as run, force preview
blendr sheet <script.py>       4-view 2x2 contact sheet
blendr turntable <script.py>   16-frame orbital sequence (in iter dir)
blendr inspect <.blend>        print scene summary (objects, polys, camera)
blendr open <iter|.blend>      open in Blender GUI (when user wants to look hands-on)
blendr promote <iter> <name>   copy iter to projects/<name> (won't be pruned)
blendr prune [--keep 50]       trash old iters (uses trash-put if available)
blendr du                      disk usage by sub-directory
blendr templates               list bundled templates
blendr new <template>          copy template to a fresh iter
blendr doctor                  health check
```

Common flags:
- `--name <slug>` — name the iter directory
- `--samples N` — override CYCLES samples (default 16)
- `--res WxH` — override preview resolution (default 512x512)
- `-- args...` — pass extra args to the user script via `sys.argv`

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `BLENDER_BIN` | `which blender` | Path to blender executable |
| `BLENDER_WORK_DIR` | `~/blender-work` | Where iters/projects/renders live |
| `BLENDR_KEEP` | `50` | Iter count threshold before auto-prune |

## Workflow patterns

### Iterate on a single scene
```
blendr new hello --name skull-v1     → creates iter_0001_skull-v1/script.py
# edit script
blendr run iters/iter_0001_skull-v1/script.py
# Read preview.png → critique → edit → run again (creates iter_0002_*)
```

### Promote a finalised iter
```
blendr promote 42 my-character        → copies iter_0042 to projects/my-character
```

### Inspect what's in a .blend
```
blendr inspect projects/my-character/scene.blend
```

### Hand the file off to the human for GUI tweaking
```
blendr open 42                        → opens iter_0042/scene.blend in Blender
```

## Self-check loop (for the agent)

After every render, **always Read the preview.png** before reporting back to the user. Cross-check:
1. Are all objects you created visible in frame?
2. Materials look like what you intended (color/metallic/roughness)?
3. Lighting reasonable (no pitch-black or blown-out)?
4. Camera angle reveals the subject (not just the back of an object)?

If anything looks off, edit the script and run again. Only show the user when you're confident the result matches their request.

For complex models, escalate to `blendr sheet` (4 angles) to verify geometry from all sides.

## Pitfalls

- **Operators silently fail in -b mode** when they need viewport context. Use `bpy.data.*` constructors.
- **`bh.empty_scene()` resets render engine to EEVEE** (it's `bpy.ops.wm.read_factory_settings(use_empty=True)` under the hood). The runtime forces it back to CYCLES before previewing, but if the user script does its own render, they need to set engine themselves.
- **CYCLES on CPU is slow at high samples**. For previews, keep samples at 16–64. For final renders, expect minutes per frame at 512+ samples.
- **`Material.use_nodes = True` is deprecated** in 5.1+ but still required to ensure the Principled BSDF node exists. `bh.principled()` suppresses the warning.
- **Pure-headless rendering on systems without a display server** can break EEVEE/Workbench because they need OpenGL. Always use CYCLES + CPU there. The runtime defaults to this.

See `docs/PITFALLS.md` for more.

## Output convention

Each `blendr run` creates:
```
$BLENDER_WORK_DIR/iters/iter_NNNN_<slug>/
├── script.py        copy of the script that produced this iter
├── scene.blend      saved Blender file
└── preview.png      auto-rendered preview (or preview_sheet.png in sheet mode)
```

Old iters are auto-pruned when the count exceeds `BLENDR_KEEP` (default 50), pushed to `trash-put` so they're recoverable.
