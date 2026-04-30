"""blendr_helpers — common bpy patterns.

Designed for headless use. Avoids `bpy.ops.*` operators that need a 3D
viewport context. Prefers low-level `bpy.data.*` constructors that work
unconditionally in `-b` (background) mode.

Import in user scripts:
    import blendr_helpers as bh
"""
import math
import bpy
from mathutils import Vector


# ---------------------------------------------------------------- scene

def empty_scene():
    """Wipe everything and return the active scene. Use as the first call."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


# ---------------------------------------------------------------- camera

def add_camera(name="Cam", location=(4.5, -4.5, 3.5), look_at=(0, 0, 0),
               focal_length_mm=50.0, set_active=True):
    """Add a camera at `location` aimed at `look_at`."""
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = focal_length_mm
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = location
    _aim(cam_obj, look_at)
    bpy.context.scene.collection.objects.link(cam_obj)
    if set_active:
        bpy.context.scene.camera = cam_obj
    return cam_obj


def _aim(obj, target):
    """Rotate `obj` so its -Z axis points at `target`. Cameras shoot down -Z."""
    direction = Vector(target) - Vector(obj.location)
    rot = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = rot.to_euler()


# ---------------------------------------------------------------- lighting

def three_point_light(key_energy=5.0, fill_energy=2.0, rim_energy=4.0):
    """Classic 3-point lighting rig: key (sun), fill (area), rim (area)."""
    key = bpy.data.lights.new("Key", type="SUN")
    key.energy = key_energy
    key_obj = bpy.data.objects.new("Key", key)
    key_obj.rotation_euler = (math.radians(40), math.radians(15), math.radians(45))
    bpy.context.scene.collection.objects.link(key_obj)

    fill = bpy.data.lights.new("Fill", type="AREA")
    fill.energy = fill_energy * 100
    fill.size = 5.0
    fill_obj = bpy.data.objects.new("Fill", fill)
    fill_obj.location = (-4, -3, 2)
    _aim(fill_obj, (0, 0, 0))
    bpy.context.scene.collection.objects.link(fill_obj)

    rim = bpy.data.lights.new("Rim", type="AREA")
    rim.energy = rim_energy * 100
    rim.size = 3.0
    rim_obj = bpy.data.objects.new("Rim", rim)
    rim_obj.location = (3, 4, 4)
    _aim(rim_obj, (0, 0, 0))
    bpy.context.scene.collection.objects.link(rim_obj)
    return key_obj, fill_obj, rim_obj


def add_sun(energy=5.0, rotation=(0.6, 0.2, 0.4)):
    sun = bpy.data.lights.new("Sun", type="SUN")
    sun.energy = energy
    obj = bpy.data.objects.new("Sun", sun)
    obj.rotation_euler = rotation
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------- materials

def principled(name, base_color=(0.8, 0.8, 0.8, 1.0), metallic=0.0,
               roughness=0.5, emission_color=None, emission_strength=0.0):
    """Create a Principled BSDF material. Suppresses 5.1+ use_nodes deprecation."""
    import warnings
    mat = bpy.data.materials.new(name)
    if not mat.node_tree or not mat.node_tree.nodes.get("Principled BSDF"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mat.use_nodes = True  # ensures Principled BSDF node exists
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission_color is not None:
        bsdf.inputs["Emission Color"].default_value = emission_color
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def assign_material(obj, mat):
    """Append `mat` to `obj`'s mesh."""
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


# ---------------------------------------------------------------- meshes

def mesh_from_pydata(name, verts, edges=None, faces=None, location=(0, 0, 0)):
    """Build a mesh object from raw vertex / face lists. No operator context needed."""
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, edges or [], faces or [])
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    bpy.context.scene.collection.objects.link(obj)
    return obj


def cube(name="Cube", size=1.0, location=(0, 0, 0)):
    s = size
    verts = [
        (-s, -s, -s), ( s, -s, -s), ( s,  s, -s), (-s,  s, -s),
        (-s, -s,  s), ( s, -s,  s), ( s,  s,  s), (-s,  s,  s),
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5),
        (0, 4, 5, 1), (1, 5, 6, 2),
        (2, 6, 7, 3), (3, 7, 4, 0),
    ]
    return mesh_from_pydata(name, verts, faces=faces, location=location)


def plane(name="Plane", size=10.0, location=(0, 0, 0)):
    s = size / 2
    verts = [(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)]
    return mesh_from_pydata(name, verts, faces=[(0, 1, 2, 3)], location=location)


# ---------------------------------------------------------------- export

def export_glb(filepath, only_selected=False):
    """Export the scene (or selection) to GLB."""
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        use_selection=only_selected,
    )
    return filepath


# ---------------------------------------------------------------- world

def set_world_color(color=(0.05, 0.05, 0.05), strength=1.0):
    """Set a flat background color via the World shader."""
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (*color, 1.0)
        bg.inputs["Strength"].default_value = strength
