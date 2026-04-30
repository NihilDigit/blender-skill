"""blendr_preview — multi-angle / animation preview utilities.

Runs inside Blender. Used by blendr_runtime.finalize() when BLENDR_PREVIEW
is set to "sheet" or "turntable", and from the blendr CLI directly.
"""
import os
import math
import struct
import zlib
import bpy

from blendr_runtime import state, configure_preview_engine, ensure_camera, ensure_light


# ---------------------------------------------------------------- 2x2 contact sheet

VIEWS = {
    "front":  {"loc": (0, -6, 1.5),    "look": (0, 0, 1)},
    "right":  {"loc": (6, 0, 1.5),     "look": (0, 0, 1)},
    "top":    {"loc": (0, 0, 8),       "look": (0, 0, 0)},
    "iso":    {"loc": (4.5, -4.5, 4),  "look": (0, 0, 0.5)},
}


def _aim(obj, target):
    from mathutils import Vector
    direction = Vector(target) - Vector(obj.location)
    rot = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = rot.to_euler()


def _temp_camera(loc, look):
    cam_data = bpy.data.cameras.new("ShotCam")
    cam_obj = bpy.data.objects.new("ShotCam", cam_data)
    cam_obj.location = loc
    _aim(cam_obj, look)
    bpy.context.scene.collection.objects.link(cam_obj)
    return cam_obj


def render_sheet(out_dir, tile=256):
    """Render front/right/top/iso views, then stitch into a 2x2 PNG."""
    scene = bpy.context.scene
    configure_preview_engine(scene)
    ensure_light(scene)

    original_cam = scene.camera
    original_w, original_h = scene.render.resolution_x, scene.render.resolution_y
    scene.render.resolution_x = tile
    scene.render.resolution_y = tile

    tiles = {}
    for label, view in VIEWS.items():
        cam = _temp_camera(view["loc"], view["look"])
        scene.camera = cam
        path = os.path.join(out_dir, f"_view_{label}.png")
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        tiles[label] = path
        bpy.data.objects.remove(cam, do_unlink=True)

    scene.camera = original_cam
    scene.render.resolution_x = original_w
    scene.render.resolution_y = original_h

    out = os.path.join(out_dir, "preview_sheet.png")
    _stitch_2x2(tiles["front"], tiles["right"], tiles["top"], tiles["iso"], out)
    for p in tiles.values():
        try:
            os.remove(p)
        except OSError:
            pass
    return out


def _stitch_2x2(tl_path, tr_path, bl_path, br_path, out):
    """Stitch four equal-sized PNGs into a 2x2 PNG using numpy.

    Blender stores image pixels as a flat RGBA float array, bottom-up.
    Reshape to (h, w, 4), then assemble into the 2x2 grid.
    """
    import numpy as np

    def _load(path):
        img = bpy.data.images.load(path, check_existing=False)
        w, h = img.size
        # img.pixels is a flat array; foreach_get is the fast bulk read.
        buf = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(buf)
        bpy.data.images.remove(img)
        return buf.reshape(h, w, 4)  # bottom-up rows

    tl = _load(tl_path); tr = _load(tr_path)
    bl = _load(bl_path); br = _load(br_path)
    h, w = tl.shape[:2]
    sh, sw = h * 2, w * 2

    grid = np.empty((sh, sw, 4), dtype=np.float32)
    # bottom-up layout: rows 0..h-1 = bottom row of grid, h..2h-1 = top row
    grid[0:h,     0:w]   = bl
    grid[0:h,     w:sw]  = br
    grid[h:sh,    0:w]   = tl
    grid[h:sh,    w:sw]  = tr

    combined = bpy.data.images.new("sheet", width=sw, height=sh, alpha=True)
    combined.pixels.foreach_set(grid.ravel())
    combined.filepath_raw = out
    combined.file_format = "PNG"
    combined.save()
    bpy.data.images.remove(combined)
    return out


# ---------------------------------------------------------------- turntable

def render_turntable(out_dir, frames=16, radius=6.0, height=2.5, tile=256):
    """Render N frames orbiting the origin. Returns the directory; user runs
    `convert` separately to make the GIF (we don't bundle imagemagick)."""
    scene = bpy.context.scene
    configure_preview_engine(scene)
    ensure_light(scene)

    original_cam = scene.camera
    original_w, original_h = scene.render.resolution_x, scene.render.resolution_y
    scene.render.resolution_x = tile
    scene.render.resolution_y = tile

    tt_dir = os.path.join(out_dir, "turntable")
    os.makedirs(tt_dir, exist_ok=True)

    for i in range(frames):
        angle = 2 * math.pi * i / frames
        loc = (math.cos(angle) * radius, math.sin(angle) * radius, height)
        cam = _temp_camera(loc, (0, 0, 0.5))
        scene.camera = cam
        scene.render.filepath = os.path.join(tt_dir, f"frame_{i:03d}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)

    scene.camera = original_cam
    scene.render.resolution_x = original_w
    scene.render.resolution_y = original_h
    return tt_dir
