"""Part 2 backyard set (golden hour): S07 Remy digging with a shovel (local 1-42), S08 shovel-blade ECU (60-95),
S09 crane up: tiny hole, zombies at the fence (110-160).  -> build/yard.blend"""
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "zombie-survival", "build"))
from lib_assets import (ANIM, LIB, append_polyhaven, bake_mix, degore, hdri_world, import_character,  # noqa: E402
                        iter_fcurves, key_hide, link, load_action, polyhaven_material, srgb)

random.seed(8)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, 160


def mat(name, color, rough=0.5, **kw):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = srgb(color)
    b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m


def local_box(name, size, center, material, parent=None, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(center) @ Matrix.Diagonal((*size, 1.0)))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    o = link(bpy.data.objects.new(name, me), parent)
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL")
        bv.width, bv.segments = bevel, 2
    return o


def cam(name, lens, fstop=None, focus=None):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens, c.data.sensor_fit, c.data.sensor_height = lens, "VERTICAL", 24
    c.data.clip_start = 0.01
    if fstop:
        c.data.dof.use_dof, c.data.dof.aperture_fstop = True, fstop
        c.data.dof.focus_object = focus
    return c


def ck(c, f, loc, tgt):
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_euler", frame=f)


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# golden hour
hdri_world("umhlanga_sunrise", 1.2, 40)
sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy, sun.data.angle, sun.data.color = 4.0, math.radians(1.5), (1.0, 0.8, 0.55)
sun.rotation_euler = (math.radians(68), 0, math.radians(-35))

# lawn, back wall of the house, fence
me = bpy.data.meshes.new("Lawn")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=40)
uv = bm.loops.layers.uv.new("UVMap")
for f_ in bm.faces:
    for lp in f_.loops:
        lp[uv].uv = (lp.vert.co.x / 4, lp.vert.co.y / 4)
bm.to_mesh(me)
bm.free()
me.materials.append(polyhaven_material("aerial_grass_rock"))
link(bpy.data.objects.new("Lawn", me))
plaster = polyhaven_material("painted_plaster_wall")
local_box("HouseBack", (12, 0.3, 3.2), (0, -3.2, 1.6), plaster)
local_box("BackDoor", (0.92, 0.06, 2.05), (1.6, -3.04, 1.03), mat("DoorBlue", "#2f5a8a", 0.4))
for i in range(-3, 4):                                    # chain-link fence across the back of the yard
    fobjs, _ = append_polyhaven("modular_chainlink_fence")
    for o in fobjs:
        sc.collection.objects.link(o)
    for o in [o for o in fobjs if o.parent is None]:
        o.location = Vector((i * 2.5, 5.0, 0)) + o.location
print("fence pieces placed")

# the hole + dirt pile (grows a little: it is hard going)
dirt = mat("Dirt", "#5a3d27", 0.95)
hole_m = mat("HoleDark", "#2a1b12", 1.0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=0.02, location=(0.55, 0.9, 0.006))
hole = bpy.context.active_object
hole.data.materials.append(hole_m)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(1.25, 0.95, -0.12), segments=24, ring_count=12)
pile = bpy.context.active_object
pile.scale = (1.1, 0.9, 0.45)
pile.data.materials.append(dirt)
for p in pile.data.polygons:
    p.use_smooth = True
for f, s_ in ((1, 0.8), (160, 1.0)):
    hole.scale = (s_, s_, 1)
    hole.keyframe_insert("scale", frame=f)

# Remy digging (mocap) + a shovel in his right hand
remy_root, remy, _, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "Remy")
dig = load_action(os.path.join(ANIM, "action", "digging.fbx"), ("mixamorig9:", "mixamorig:"))
a0, a1 = dig.frame_range
bake_mix(remy, [(dig, lambda f: a0 + (f * 1.15 + 20) % (a1 - a0)), (dig, lambda f: a0 + (f * 1.15 + 20) % (a1 - a0))],
         lambda f: 0.0, 1, 160, "Remy_dig")
remy_root.location = (0.55, 0.35, 0)
remy_root.rotation_euler.z = math.radians(180)            # faces +y, digging towards the fence
handle_m = mat("ShovelWood", "#a8794a", 0.6)
blade_m = mat("ShovelBlade", "#7d858c", 0.35, Metallic=1.0)
shovel = link(bpy.data.objects.new("Shovel", None))
bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=1.05, location=(0, 0, 0))
hd = bpy.context.active_object
hd.data.materials.append(handle_m)
hd.parent = shovel
hd.location = (0, 0, -0.38)
bl = local_box("Blade", (0.2, 0.02, 0.26), (0, 0, -1.0), blade_m, shovel, 0.006)
sc.frame_set(1)
bpy.context.view_layer.update()
rh = remy.pose.bones["mixamorig:RightHand"]
lh = remy.pose.bones["mixamorig:LeftHand"]
# shovel shaft runs from the right hand through the left hand and down to the blade: keyed per frame
for f in range(1, 161):
    sc.frame_set(f)
    pr = remy.matrix_world @ rh.head
    pl = remy.matrix_world @ lh.head
    d = (pl - pr)
    if d.length < 0.05:
        d = Vector((0, 0.3, -1))
    d.normalize()
    shovel.location = pr + d * 0.1
    shovel.rotation_euler = (-d).to_track_quat("Z", "Y").to_euler()
    shovel.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    shovel.keyframe_insert("location", frame=f)
    shovel.keyframe_insert("rotation_euler", frame=f)

# zombies at the fence (S09): pressing on the chain-link, one reaching over
z_root, zom, zmeshes, zrun = import_character(os.path.join(ANIM, "zombie", "zombie_run_warzombie.fbx"), 1.85, "FenceZ")
degore({s.material for o in zmeshes for s in o.material_slots})
atk = load_action(os.path.join(ANIM, "zombie", "zombie_attack.fbx"))
g_root, girl, gmeshes, gidle = import_character(os.path.join(ANIM, "zombie", "zombie_idle_zombiegirl.fbx"), 1.72, "FenceG")
degore({s.material for o in gmeshes for s in o.material_slots})


def clone(root, arm, meshes, name):
    r2 = link(bpy.data.objects.new(name + "_root", None))
    r2.scale = root.scale
    a2 = arm.copy()
    a2.animation_data_clear()
    link(a2, r2)
    a2.matrix_parent_inverse = arm.matrix_parent_inverse.copy()
    for m in meshes:
        m2 = m.copy()
        m2.animation_data_clear()
        link(m2, a2)
        m2.matrix_parent_inverse = m.matrix_parent_inverse.copy()
        for md in m2.modifiers:
            if md.type == "ARMATURE":
                md.object = a2
    return r2, a2


def loop(arm, act, offset, scale=1.0):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    tr = ad.nla_tracks.new()
    st = tr.strips.new(act.name, int(-200 + offset), act)
    try:
        st.action_slot = act.slots[0]
    except (AttributeError, IndexError):
        pass
    st.repeat = 400.0 / max(1.0, act.frame_range[1] - act.frame_range[0])
    st.scale = scale


spots = [(-3.0, "z"), (-1.6, "g"), (-0.4, "z"), (0.9, "g"), (2.1, "z"), (3.3, "g")]
for i, (x, kind) in enumerate(spots):
    r_, a_ = clone(z_root, zom, zmeshes, f"FZ{i}") if kind == "z" else clone(g_root, girl, gmeshes, f"FG{i}")
    loop(a_, atk if i % 2 == 0 else gidle, random.uniform(0, 60), 1.0)
    r_.location = (x + random.uniform(-0.2, 0.2), 5.35, 0)
    r_.rotation_euler.z = math.radians(random.uniform(-15, 15))    # facing -y, into the yard
for o in (z_root, g_root):
    o.location = (0, 60, 0)

# cameras
focus = link(bpy.data.objects.new("FocusRemy", None))
c7 = cam("Cam_S07", 30, 4.0, focus)                        # medium, low, tracking past him: fence + sky behind
for f in range(1, 43):
    sc.frame_set(f)
    hip = remy.matrix_world @ remy.pose.bones["mixamorig:Hips"].head
    focus.location = hip
    focus.keyframe_insert("location", frame=f)
    k = sm((f - 1) / 41)
    ck(c7, f, hip + Vector((1.9 - 0.5 * k, -1.7 + 0.2 * k, 0.05)), hip + Vector((-0.2, 0.4, 0.15)))
c8 = cam("Cam_S08", 35)                                    # ECU: blade into hard dirt
for f in range(118, 154):
    sc.frame_set(f)
    tip = shovel.matrix_world @ Vector((0, 0, -1.1))
    hc = Vector((0.55, 0.9, 0.05))
    ck(c8, f, hc + Vector((0.75, -0.95, 0.42)), hc.lerp(tip, 0.25) + Vector((0, 0, 0.12)))
c9 = cam("Cam_S09", 24)                                    # crane up: tiny hole, fence full of zombies
for f in range(110, 161):
    k = sm((f - 110) / 50)
    ck(c9, f, Vector((0.2, -1.6 - 1.2 * k, 2.2 + 4.0 * k)), Vector((0.5, 2.2 + 0.8 * k, 0.2)))
sc.camera = c7

r = sc.render
r.engine = "CYCLES"
sc.cycles.samples = 24
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
r.use_motion_blur = True
r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920
r.use_persistent_data = True
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "yard.blend"))
print("saved yard.blend")
