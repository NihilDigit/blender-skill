"""blendr runtime — runs INSIDE Blender's Python.

Loaded by blendr's prelude before the user script. Provides:
  - sensible scene defaults (CYCLES + CPU + low samples for fast preview)
  - finalize() called after the user script: saves .blend + renders preview
  - small state object so user scripts can opt into specific behavior

Env vars set by the blendr CLI wrapper:
  BLENDR_OUT_DIR    target dir for scene.blend / preview.png
  BLENDR_OUT_BLEND  full path to scene.blend
  BLENDR_OUT_PNG    full path to preview.png
  BLENDR_PREVIEW    "auto" | "skip" | "sheet" | "turntable"
  BLENDR_SAMPLES    cycles samples (default 16)
  BLENDR_RES        "WxH" preview resolution (default 512x512)
"""
import os
import sys
import time
import bpy


class _State:
    out_dir = os.environ.get("BLENDR_OUT_DIR", "/tmp/blendr-out")
    out_blend = os.environ.get("BLENDR_OUT_BLEND", os.path.join(out_dir, "scene.blend"))
    out_png = os.environ.get("BLENDR_OUT_PNG", os.path.join(out_dir, "preview.png"))
    preview = os.environ.get("BLENDR_PREVIEW", "auto")
    samples = int(os.environ.get("BLENDR_SAMPLES", "16"))
    res_w, res_h = (int(x) for x in os.environ.get("BLENDR_RES", "512x512").split("x"))
    skip_preview = False
    skip_save = False
    user_rendered = False


state = _State()


def configure_preview_engine(scene=None):
    """Apply CYCLES+CPU defaults. Idempotent — user scripts may override."""
    scene = scene or bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = state.samples
    scene.render.resolution_x = state.res_w
    scene.render.resolution_y = state.res_h
    scene.render.image_settings.file_format = "PNG"


def ensure_camera(scene=None):
    """If scene has no camera, add a sensible default 3/4 view camera."""
    scene = scene or bpy.context.scene
    if scene.camera:
        return scene.camera
    cam_data = bpy.data.cameras.new("BlendrCam")
    cam_obj = bpy.data.objects.new("BlendrCam", cam_data)
    cam_obj.location = (4.5, -4.5, 3.5)
    cam_obj.rotation_euler = (1.05, 0, 0.785)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    return cam_obj


def ensure_light(scene=None):
    """If scene has no lights, add a sun + fill area light."""
    scene = scene or bpy.context.scene
    has_light = any(o.type == "LIGHT" for o in scene.objects)
    if has_light:
        return
    sun_data = bpy.data.lights.new("BlendrSun", type="SUN")
    sun_data.energy = 4.0
    sun_obj = bpy.data.objects.new("BlendrSun", sun_data)
    sun_obj.rotation_euler = (0.6, 0.2, 0.4)
    scene.collection.objects.link(sun_obj)


def render_preview(path=None):
    """Render a single PNG preview to `path` (default: state.out_png)."""
    path = path or state.out_png
    os.makedirs(os.path.dirname(path), exist_ok=True)
    scene = bpy.context.scene
    configure_preview_engine(scene)
    ensure_camera(scene)
    ensure_light(scene)
    scene.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t0
    state.user_rendered = True
    return path, dt


def save_blend(path=None):
    """Save the .blend to `path` (default: state.out_blend)."""
    path = path or state.out_blend
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path


def _scene_summary():
    scene = bpy.context.scene
    objs = list(scene.objects)
    by_type = {}
    polys = 0
    for o in objs:
        by_type[o.type] = by_type.get(o.type, 0) + 1
        if o.type == "MESH":
            polys += len(o.data.polygons)
    return {
        "objects": len(objs),
        "by_type": by_type,
        "polys": polys,
        "user_engine": scene.render.engine,
        "preview_engine": "CYCLES (forced)",
        "camera": scene.camera.name if scene.camera else None,
    }


def finalize():
    """Called by blendr prelude after user script finishes.

    Saves .blend and renders preview unless the user opted out via
    blendr_runtime.state.skip_save / skip_preview.
    """
    summary = _scene_summary()
    print("[blendr] scene:", summary)

    if not state.skip_save:
        path = save_blend()
        print(f"[blendr] saved blend: {path}")

    if state.preview == "skip" or state.skip_preview:
        print("[blendr] preview skipped")
        return

    if state.preview == "auto":
        path, dt = render_preview()
        size = os.path.getsize(path) if os.path.exists(path) else -1
        print(f"[blendr] rendered preview: {path} ({size} bytes, {dt:.2f}s)")
    elif state.preview == "sheet":
        # 2x2 contact sheet: front / right / top / iso
        from blendr_preview import render_sheet
        out = render_sheet(state.out_dir)
        print(f"[blendr] rendered sheet: {out}")
    elif state.preview == "turntable":
        from blendr_preview import render_turntable
        out = render_turntable(state.out_dir, frames=16)
        print(f"[blendr] rendered turntable: {out}")
