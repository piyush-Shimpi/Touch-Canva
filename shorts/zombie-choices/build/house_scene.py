"""Part 2 house set. Hook test = S01 (local 1-39) door bursts on its chain, zombie arm thrusts through the gap;
S02 (local 40-81) Remy backs away and looks around, deciding.
Run: /opt/bvenv/bin/python build/house_scene.py  -> build/house.blend"""
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "zombie-survival", "build"))
from lib_assets import (ANIM, LIB, bake_mix, degore, hdri_world, import_character, iter_fcurves,  # noqa: E402
                        key_hide, link, load_action, polyhaven_material, srgb)

random.seed(21)
FPS = 30
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = -41, 610


def mat(name, color, rough=0.5, **kw):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = srgb(color)
    b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m


def box(name, size, loc, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bv = o.modifiers.new("bev", "BEVEL")
        bv.width, bv.segments = bevel, 2
    o.data.materials.append(material)
    return o


def uv_box(o, scale=1.0):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        for lp in f.loops:
            c = lp.vert.co
            lp[uv].uv = ((c.x if abs(n.x) < 0.5 else c.y) / scale, (c.z if abs(n.z) < 0.5 else c.y) / scale)
    bm.to_mesh(o.data)
    bm.free()


# ---------------------------------------------------------------- world: golden hour outside the door
hdri_world("umhlanga_sunrise", 1.3, 160)
sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy, sun.data.angle, sun.data.color = 4.5, math.radians(1.5), (1.0, 0.78, 0.5)
sun.rotation_euler = (math.radians(72), 0, math.radians(185))    # low sun shining in through the door gap

# ---------------------------------------------------------------- hallway: door wall at y=0, room towards -y
plaster = polyhaven_material("painted_plaster_wall")
floor_m = mat("FloorWood", "#9a6b43", 0.45)
t = floor_m.node_tree
fb = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
wave = t.nodes.new("ShaderNodeTexWave")
wave.inputs["Scale"].default_value, wave.inputs["Distortion"].default_value = 3.0, 6.0
tc = t.nodes.new("ShaderNodeTexCoord")
mp = t.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (1.0, 6.0, 1.0)
t.links.new(tc.outputs["Object"], mp.inputs[0])
t.links.new(mp.outputs[0], wave.inputs["Vector"])
ramp = t.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = srgb("#7a5032"), srgb("#b8875a")
t.links.new(wave.outputs["Fac"], ramp.inputs[0])
t.links.new(ramp.outputs["Color"], fb.inputs["Base Color"])
W, D, Hh = 3.2, 5.0, 2.7
floor = box("Floor", (W, D, 0.05), (0, -D / 2, -0.025), floor_m)
ceil = box("Ceiling", (W, D, 0.05), (0, -D / 2, Hh + 0.025), mat("Ceiling", "#f3efe8", 0.8))
DW, DH = 0.92, 2.06                                   # door opening
for name, sx, cx in (("WallL", (W - DW) / 2, -(W + DW) / 4), ("WallR", (W - DW) / 2, (W + DW) / 4)):
    w = box(name, (sx, 0.14, Hh), (cx, 0.07, Hh / 2), plaster)
    uv_box(w, 1.5)
w = box("WallTop", (DW, 0.14, Hh - DH), (0, 0.07, DH + (Hh - DH) / 2), plaster)
uv_box(w, 1.5)
for name, x in (("SideL", -W / 2), ("SideR", W / 2)):
    w = box(name, (0.1, D, Hh), (x, -D / 2, Hh / 2), plaster)
    uv_box(w, 1.5)
# window on the right wall, bright sky behind (keeps the hallway readable)
win = bpy.data.materials.new("WindowGlow")
win.node_tree.nodes.clear()
wo = win.node_tree.nodes.new("ShaderNodeOutputMaterial")
we = win.node_tree.nodes.new("ShaderNodeEmission")
we.inputs["Color"].default_value, we.inputs["Strength"].default_value = srgb("#ffd9a8"), 3.0
win.node_tree.links.new(we.outputs[0], wo.inputs[0])
box("Window", (0.02, 1.1, 1.2), (W / 2 - 0.06, -2.4, 1.45), win)
trim = mat("Trim", "#f6f1e7", 0.5)
for x in (-DW / 2 - 0.05, DW / 2 + 0.05):
    box("Jamb", (0.09, 0.18, DH + 0.06), (x, 0.0, DH / 2), trim, 0.01)
box("Head", (DW + 0.2, 0.18, 0.09), (0, 0.0, DH + 0.04), trim, 0.01)
# warm interior fill
fill = link(bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "AREA")))
fill.data.size, fill.data.energy, fill.data.color = 2.5, 260, (1.0, 0.86, 0.7)
fill.location = (0.2, -2.6, Hh - 0.05)
fill.rotation_euler = (0, 0, 0)
fill.rotation_euler = (math.radians(180), 0, 0)

# ---------------------------------------------------------------- the door (hinge on the left, opens inward on a chain)
door_m = mat("DoorBlue", "#2f5a8a", 0.4)
brass = mat("Brass", "#c9a14a", 0.25, Metallic=1.0)
steel = mat("Steel", "#c8ccd2", 0.2, Metallic=1.0)
hinge = link(bpy.data.objects.new("DoorHinge", None))
hinge.location = (-DW / 2 + 0.01, -0.02, 0)


def local_box(name, size, center, material, parent, bevel=0.0):
    """box mesh built directly in the parent's space (no operators, no parent-inverse surprises)"""
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


slab = local_box("DoorSlab", (DW - 0.03, 0.045, DH - 0.02), (DW / 2 - 0.015, 0, DH / 2), door_m, hinge, 0.006)
for zc in (0.55, 1.45):                                 # raised panels on the inside face
    local_box("Panel", (0.58, 0.012, 0.66), (DW / 2 - 0.015, -0.028, zc), door_m, hinge, 0.004)
knob = bpy.ops.mesh.primitive_uv_sphere_add(radius=0.032, location=(0, 0, 0))
knob = bpy.context.active_object
knob.data.materials.append(brass)
knob.parent = hinge
knob.location = (DW - 0.1, -0.06, 1.0)
knob.matrix_parent_inverse.identity()
# chain: anchor on the door edge, plate on the jamb
links_ = []
for i in range(9):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.011, minor_radius=0.0028, location=(0, 0, 0))
    lk = bpy.context.active_object
    lk.data.materials.append(steel)
    links_.append(lk)
CH_Z = 1.42


def door_angle(f):
    """0 = closed. Bursts to the chain limit on frame 1 with overshoot; second slam around frame 22"""
    if f >= 560:                                      # PEAK: chain snaps, door flies open
        u = f - 560
        return -math.radians(min(100.0, 18.0 + 82.0 * (1 - math.exp(-u * 0.7))) + (6.0 * math.exp(-u * 0.25) * math.sin(u * 1.4) if u > 4 else 0))
    if f < -6:
        return math.radians(1.0 * abs(math.sin(f * 1.7)))
    if f < 1:
        return math.radians(2.5 * abs(math.sin(f * 2.3)))
    base = 18.0
    for hit in (1, 22, 44, 63):
        if f >= hit:
            u = f - hit
            base = 18.0 + 5.0 * math.exp(-u * 0.45) * math.cos(u * 1.9)
    return -math.radians(base)


for f in list(range(-41, 100)) + list(range(540, 611)):
    a = door_angle(f)
    hinge.rotation_euler = (0, 0, a)
    hinge.keyframe_insert("rotation_euler", frame=f)
    # chain endpoints in world space
    edge = Vector((-DW / 2 + 0.01, -0.02, 0)) + Matrix.Rotation(a, 3, "Z") @ Vector((DW - 0.06, -0.03, CH_Z))
    plate = Vector((DW / 2 + 0.04, -0.09, CH_Z + 0.01))
    span = (plate - edge).length
    sag = max(0.0, 0.16 - span) * 0.5
    for i, lk in enumerate(links_):
        k = (i + 0.5) / len(links_)
        p = edge.lerp(plate, k) + Vector((0, 0, -sag * 4 * k * (1 - k)))
        lk.location = p
        lk.rotation_euler = (math.radians(90 if i % 2 else 0), 0, math.atan2((plate - edge).y, (plate - edge).x))
        lk.keyframe_insert("location", frame=f)
        lk.keyframe_insert("rotation_euler", frame=f)

# splinters off the latch side on each slam
wood = mat("Splinter", "#d8b88a", 0.7)
for hit in (1, 22):
    for i in range(14):
        bpy.ops.mesh.primitive_cube_add(size=1)
        sp = bpy.context.active_object
        sp.scale = (random.uniform(0.004, 0.01), random.uniform(0.02, 0.06), random.uniform(0.004, 0.01))
        sp.data.materials.append(wood)
        p0 = Vector((DW / 2 - 0.02, -0.05, random.uniform(0.9, 1.6)))
        v = Vector((random.uniform(-0.6, 0.4), random.uniform(-2.2, -0.8), random.uniform(0.2, 1.6))) / FPS
        spin = Vector([random.uniform(-0.6, 0.6) for _ in range(3)])
        for f in range(hit - 1, hit + 26):
            u = f - hit
            if u < 0:
                p = p0
            else:
                p = p0 + v * u + Vector((0, 0, -0.5 * 9.8 * (u / FPS) ** 2))
                p.z = max(p.z, 0.005)
            sp.location = p
            sp.rotation_euler = spin * max(0, u)
            sp.keyframe_insert("location", frame=f)
            sp.keyframe_insert("rotation_euler", frame=f)
        key_hide(sp, ((-30, True), (hit, False)))

# ---------------------------------------------------------------- zombie outside, right arm thrusting through the gap
z_root, zom, z_meshes, z_run = import_character(os.path.join(ANIM, "zombie", "zombie_run_warzombie.fbx"), 1.85, "DoorZombie")
degore({s.material for o in z_meshes for s in o.material_slots})
z_root.location = (DW / 2 - 0.26, 0.40, 0)               # behind the door; its LEFT arm is on the latch side
z_root.rotation_euler.z = 0.0                           # faces -y, into the house
r0, r1 = z_run.frame_range
bake_mix(zom, [(z_run, lambda f: r0 + (f * 0.6) % (r1 - r0)), (z_run, lambda f: r0 + (f * 0.6) % (r1 - r0))],
         lambda f: 0.0, -41, 81, "DoorZombie_base")
pb = zom.pose.bones


def rotate_bone_world(arm, name, axis_world, angle):
    b = arm.pose.bones[name]
    aw = arm.matrix_world.to_3x3().normalized()
    axis = (aw.inverted() @ Vector(axis_world)).normalized()
    R = Matrix.Rotation(angle, 4, axis)
    h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()


def aim(arm, bone, child, target):
    a = arm.matrix_world @ arm.pose.bones[bone].head
    c = arm.matrix_world @ arm.pose.bones[child].head
    d, t_ = (c - a).normalized(), (Vector(target) - a).normalized()
    if d.angle(t_) > 1e-3:
        rotate_bone_world(arm, bone, d.cross(t_).normalized(), d.angle(t_))


GAP = Vector((DW / 2 - 0.02, -0.12, 1.3))             # just inside the chain gap
for f in range(-41, 82):
    sc.frame_set(f)
    # thrust: hand rockets through the gap on frame 1, claws and gropes after
    if f < 1:
        reach = 0.0
    else:
        u = f - 1
        reach = min(1.0, 0.35 + u / 3.0) * (0.85 + 0.15 * math.sin(u * 0.9))
    grope = Vector((0.06 * math.sin(f * 0.55), 0, 0.07 * math.sin(f * 0.83 + 1)))
    tgt = GAP + Vector((0.12 * reach, -0.62 * reach, -0.04)) + grope * reach
    # other arm stays behind the door (pressed on the outside face), never through the slab
    sh = zom.matrix_world @ pb["mixamorig:RightArm"].head
    aim(zom, "mixamorig:RightArm", "mixamorig:RightForeArm", sh + Vector((-0.15, 0.25, -0.45)))
    aim(zom, "mixamorig:RightForeArm", "mixamorig:RightHand", sh + Vector((-0.1, 0.12, -0.75)))
    aim(zom, "mixamorig:LeftArm", "mixamorig:LeftForeArm", tgt + Vector((0, 0.12, 0.05)))
    aim(zom, "mixamorig:LeftForeArm", "mixamorig:LeftHand", tgt)
    # fingers claw open/closed
    for fi in ("Index", "Middle", "Ring", "Pinky"):
        for j in (1, 2):
            n = f"mixamorig:LeftHand{fi}{j}"
            if n in pb:
                pb[n].rotation_quaternion = Quaternion((1, 0, 0), 0.35 + 0.35 * math.sin(f * 0.7 + j))
    for b in pb:
        b.keyframe_insert("rotation_quaternion", frame=f)

# ---------------------------------------------------------------- Remy: flinches back from the door, then looks around
remy_root, remy, remy_meshes, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "Remy")
terr = load_action(os.path.join(ANIM, "reactions", "terrified_leonard.fbx"), ("mixamorig9:", "mixamorig:"))
# flinch on the burst, then straightens up (clip played back) while deciding
bake_mix(remy, [(terr, lambda f: 14 + max(0, f) * 1.1 if f < 40 else max(20.0, 58 - (f - 40) * 0.9)),
                (terr, lambda f: 14 + max(0, f) * 1.1 if f < 40 else max(20.0, 58 - (f - 40) * 0.9))],
         lambda f: 0.0, -41, 81, "Remy_flinch")
for f in range(40, 82):                                  # S02: glances left, right (deciding)
    sc.frame_set(f)
    look = 0.45 * math.sin((f - 40) / 41 * math.pi * 2.0) * min(1, (f - 40) / 6)
    for bn, k in (("mixamorig:Neck", 0.4), ("mixamorig:Head", 0.6)):
        b = remy.pose.bones[bn]
        b.rotation_quaternion = b.rotation_quaternion @ Quaternion((0, 1, 0), look * k)
        b.keyframe_insert("rotation_quaternion", frame=f)
remy_root.rotation_euler.z = math.radians(180)           # faces the door (+y)
for f, y in ((-41, -1.15), (1, -1.15), (10, -1.55), (30, -1.85), (81, -2.0)):   # stumbles back on the burst
    remy_root.location = (-0.85, y, 0)
    remy_root.keyframe_insert("location", frame=f)

# ---------------------------------------------------------------- cameras
def cam(name, lens, fstop=None):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens, c.data.sensor_fit, c.data.sensor_height = lens, "VERTICAL", 24
    c.data.clip_start = 0.02
    if fstop:
        c.data.dof.use_dof, c.data.dof.aperture_fstop = True, fstop
    return c


def ck(c, f, loc, tgt):
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_euler", frame=f)


c1 = cam("Cam_S01", 21)                                    # low, Remy's shoulder in the foreground, the door bursting
for f in range(-41, 41):
    shake = Vector((0.012 * math.sin(f * 2.9), 0, 0.01 * math.sin(f * 3.7))) * (2.5 if f in range(1, 6) or f in range(22, 26) else 1.0)
    k = max(0, min(1, (f - 1) / 38))
    tgt = Vector((0.22, -0.15, 1.3))
    if f < -24:                                         # S15: arrives on a whip pan
        w_ = ((-24 - f) / 17) ** 2
        tgt = tgt + Vector((-6.0 * w_, -1.5 * w_, 1.2 * w_))
    ck(c1, f, Vector((0.95 - 0.05 * k, -1.25 + 0.1 * k, 1.0)) + shake, tgt)
focus = link(bpy.data.objects.new("FocusRemy", None))
c2 = cam("Cam_S02", 32, 2.8)                               # MCU of Remy deciding, door + arm soft behind him
c2.data.dof.focus_object = focus
for f in range(40, 82):
    sc.frame_set(f)
    head = remy.matrix_world @ remy.pose.bones["mixamorig:Head"].head
    focus.location = head
    focus.keyframe_insert("location", frame=f)
    k = (f - 40) / 41
    ck(c2, f, head + Vector((0.6 - 0.08 * k, 1.05 - 0.15 * k, -0.18)) + Vector((0.006 * math.sin(f * 2.6), 0, 0)), head + Vector((0.0, 0.0, -0.12)))
sc.camera = c1

# ---------------------------------------------------------------- render
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
exec(open(os.path.join(HERE, "kitchen_extra.py")).read())
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "house.blend"))
print("saved house.blend")
