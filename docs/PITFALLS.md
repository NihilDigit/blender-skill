# Pitfalls when scripting Blender headlessly

## Context: why bpy.ops is dangerous in `-b` mode

Most `bpy.ops.*` operators read state from `bpy.context`. In a 3D viewport, that context is rich (active object, selected objects, active area, screen, region). In headless mode (`blender -b`), `bpy.context.area` and `bpy.context.screen` are typically `None`, which means many operators either fail with cryptic errors or silently do nothing.

**Rule of thumb**: prefer `bpy.data.*` constructors and direct property assignment. Use `bpy.ops.*` only when there's no `bpy.data` equivalent (e.g., `bpy.ops.export_scene.gltf`, `bpy.ops.render.render`, `bpy.ops.wm.save_as_mainfile`).

If you must call an operator that needs context, override it explicitly:

```python
override = bpy.context.copy()
override["selected_objects"] = [my_obj]
override["active_object"] = my_obj
with bpy.context.temp_override(**override):
    bpy.ops.object.modifier_add(type="SUBSURF")
```

## Render engine selection in headless

| Engine | Headless reliability | Notes |
|---|---|---|
| `CYCLES` + CPU | ✅ rock solid | Slowest per sample but always works. Default for blendr previews. |
| `CYCLES` + GPU (CUDA/OPTIX) | ⚠️ varies | Needs GPU + drivers correctly exposed. Can crash on shader compile in weird envs. |
| `BLENDER_EEVEE` (EEVEE Next) | ❌ often breaks | Needs OpenGL context. Tends to crash with EGL errors on systems without display server. |
| `BLENDER_WORKBENCH` | ❌ often breaks | Same — needs OpenGL. |

Set per-script if you want a different engine:

```python
import bpy
bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.device = "CPU"  # or "GPU" if you know it works
bpy.context.scene.cycles.samples = 128   # quality vs. speed
```

## `read_factory_settings(use_empty=True)` resets engine

`blendr_helpers.empty_scene()` (and any direct call to `bpy.ops.wm.read_factory_settings`) resets the scene to factory defaults, which means `scene.render.engine = "BLENDER_EEVEE"` again. The blendr runtime forces CYCLES back before the preview render, but if you call `bpy.ops.render.render` yourself, set the engine first.

## Material nodes / Principled BSDF

In Blender 5.1+, `Material.use_nodes` is deprecated and slated for removal in 6.0. New materials get a node tree by default — but the tree is empty. To get the standard "Principled BSDF + Material Output" node setup, you currently still need to call `mat.use_nodes = True` (which triggers the deprecation warning). `blendr_helpers.principled()` suppresses the warning.

When 6.0 lands, the helper will need updating to use the new API.

## Bundled Python is locked

Blender ships its own Python interpreter (3.14.x in 5.1.1). Scripts run with `--python` use that interpreter, not your system Python. Available stdlib modules are determined by Blender's bundled Python; **you cannot pip install** into Blender's Python without write access to its install dir.

What is available out of the box:
- numpy (2.4+)
- mathutils (Blender's vector math)
- bmesh (low-level mesh editing)
- Standard library

If you need a third-party package, install it into Blender's Python (`/usr/lib/blender/python/bin/python -m pip install foo`) — not recommended unless you really need it. Better: pre-process data with system Python, write to disk, read in Blender.

## File path pitfalls

- `scene.render.filepath` can use `//` to mean "relative to the .blend file". In headless scripts it's safer to use absolute paths.
- `bpy.ops.wm.save_as_mainfile(filepath=...)` requires an absolute path; relative paths are interpreted relative to the current `.blend`, which may not exist yet.
- `#` characters in `render.filepath` get replaced by frame numbers (e.g., `frame_####.png` → `frame_0001.png`). If you want a literal `#`, that's not possible — use a different delimiter.

## Memory and process lifecycle

Each `blendr run` cold-starts Blender. Startup costs ~0.3–0.5s. There is no warm process reuse. If you're doing dozens of iterations per minute, expect that startup overhead to dominate. For high-frequency work, consider opening Blender once and using the official Blender MCP server addon.

## `bpy.context.scene` after `read_factory_settings`

After `bpy.ops.wm.read_factory_settings(use_empty=True)`, `bpy.context.scene` is a *new* scene object — old references are stale. Always re-fetch:

```python
import blendr_helpers as bh

bh.empty_scene()
scene = bpy.context.scene  # fresh reference
# ...
```

## Frame range vs single render

`bpy.ops.render.render(write_still=True)` renders the current frame as an image. `bpy.ops.render.render(animation=True)` renders the frame range as a sequence. Don't mix them up — `animation=True` with `write_still=True` is undefined.

## blendr-specific: don't fight the runtime

The runtime hooks the very end of your script via a separate `--python` invocation that calls `blendr_runtime.finalize()`. Don't `sys.exit()` from your script unless you really mean to skip finalisation. To opt out of preview/save selectively, mutate state:

```python
import blendr_runtime
blendr_runtime.state.skip_preview = True   # save .blend but no PNG
blendr_runtime.state.skip_save = True      # render PNG but no .blend
```
