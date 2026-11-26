"""Hook test (S01 + S02, frames 1-72): Remy sprints at a low camera down an empty sunny boulevard,
a War Zombie lunges behind him and its hand closes on air just behind his heel.
Run: /opt/bvenv/bin/python build/hook_scene.py   -> build/hook.blend"""
import math
import os
import sys

import bpy  # noqa: I001
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib_assets import (ANIM, bake_mix, iter_fcurves, LIB, append_polyhaven, degore, foot_speed, hdri_world, import_character,  # noqa: E402
                        link, load_action, nla, polyhaven_material, srgb)

FPS = 30
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, 99

# ---------------------------------------------------------------- world + ground
w, wmap = hdri_world("wide_street_01", 1.15, rot_deg=float(os.environ.get("HDRI_ROT", "-47")))
asph = polyhaven_material("asphalt_02")
gme = bpy.data.meshes.new("Road")
import bmesh  # noqa: E402
SHOW_PACK = os.environ.get("PACK") == "1"   # he only packs the backpack in step two
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=150)
uv = bm.loops.layers.uv.new("UVMap")
for f in bm.faces:
    for lp in f.loops:
        lp[uv].uv = (lp.vert.co.x / 4.0, lp.vert.co.y / 4.0)
bm.to_mesh(gme)
bm.free()
gme.materials.append(asph)
road = link(bpy.data.objects.new("Road", gme))
# crosswalk stripes (the hook happens on a zebra crossing)
paint = bpy.data.materials.new("Paint")
pb_ = next(n for n in paint.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
pb_.inputs["Base Color"].default_value = srgb("#e9e6dc")
pb_.inputs["Roughness"].default_value = 0.75
for k in range(9):
    sm = bpy.data.meshes.new("Stripe")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)
    bmesh.ops.scale(bm, vec=(0.25, 1.6, 1), verts=bm.verts)
    bm.to_mesh(sm)
    bm.free()
    sm.materials.append(paint)
    st = link(bpy.data.objects.new("Stripe", sm))
    st.location = (-4.0 + k * 1.0, -8.0, 0.004)

# ---------------------------------------------------------------- props (parallax + abandoned-city feel)
def place(objs, loc, rot=0.0, scale=1.0):
    roots = [o for o in objs if o.parent is None]
    for o in objs:
        sc.collection.objects.link(o)
    for o in roots:
        o.location = Vector(loc) + o.location
        o.rotation_euler.z += math.radians(rot)
        o.scale = tuple(s * scale for s in o.scale)
    return objs


def ph(folder, loc, rot=0.0, scale=1.0):
    objs, _ = append_polyhaven(folder)
    return place(objs, loc, rot, scale)


ph("concrete_road_barrier", (2.6, -2.0, 0), 80)
ph("concrete_road_barrier", (2.9, -6.5, 0), 100)
ph("metal_trash_can", (-2.4, -12.0, 0), 20)
ph("covered_car", (-3.4, 3.0, 0), 25)
for y in (-20, -4, 12):
    ph("street_lamp_01", (4.6, y, 0), 180)
ph("utility_box_02", (-4.4, -16.0, 0), 90)

# ---------------------------------------------------------------- Remy (hero)
remy_root, remy, remy_meshes, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "Remy")
run = load_action(os.path.join(ANIM, "action", "running_fast.fbx"))
cyc = run.frame_range[1] - run.frame_range[0]
v_run = foot_speed(remy, run, *run.frame_range)
print("run cycle", cyc, "frames; foot speed m/frame", round(v_run, 4))
v_run = v_run * 1.15                                        # planted-foot average underestimates slightly
nla(remy, [dict(action=run, start=-30, repeat=8)])
# orange backpack (hero colour)
bpm_ = bpy.data.materials.new("Backpack")
b = next(n for n in bpm_.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
b.inputs["Base Color"].default_value = srgb("#ff7a1a")
b.inputs["Roughness"].default_value = 0.55
bpy.ops.mesh.primitive_cube_add(size=1)
pack = bpy.context.active_object
pack.name = "Backpack"
pack.scale = (0.32, 0.16, 0.42)
bev = pack.modifiers.new("bev", "BEVEL")
bev.width, bev.segments = 0.06, 4
pack.modifiers.new("sub", "SUBSURF").levels = 2
pack.data.materials.append(bpm_)
for p in pack.data.polygons:
    p.use_smooth = True
sc.frame_set(1)
bpy.context.view_layer.update()
sp2 = remy.pose.bones["mixamorig:Spine2"]
anchor = remy.matrix_world @ sp2.head
fwd = (remy.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()   # armature +Z (Mixamo front) in world
print("remy front axis", tuple(round(x, 2) for x in fwd))
pack.location = anchor + Vector((0, 0.16, -0.10))
pack.scale = (0.30, 0.15, 0.40)
bpy.context.view_layer.update()
mw = pack.matrix_world.copy()
pack.parent = remy
pack.parent_type = "BONE"
pack.parent_bone = "mixamorig:Spine2"
bpy.context.view_layer.update()
pack.matrix_world = mw

if not SHOW_PACK:
    bpy.data.objects.remove(pack, do_unlink=True)

# Remy runs towards -Y
Y0 = 0.0
for f in (1, 99):
    remy_root.location = (0.0, Y0 - v_run * (f - 1), 0.0)
    remy_root.keyframe_insert("location", frame=f)
for fc in iter_fcurves(remy_root.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = "LINEAR"

# ---------------------------------------------------------------- War Zombie (lunger)
z_root, zom, z_meshes, z_run = import_character(os.path.join(ANIM, "zombie", "zombie_run_warzombie.fbx"), 1.85, "WarZombie")
degore({s.material for o in z_meshes for s in o.material_slots})
z_atk = load_action(os.path.join(ANIM, "zombie", "zombie_attack.fbx"))
z_run.use_fake_user = True
# the attack clip's downward grab is the lunge: grab pose on frame 1, blending back into the run by frame 14
LUNGE_AT = 58                                              # attack-clip frame with the hand lowest
r0, r1 = z_run.frame_range
zbake = bake_mix(zom, [(z_run, lambda f: r0 + (f - 1) % (r1 - r0)), (z_atk, lambda f: min(LUNGE_AT + (f - 1) * 0.5, 64))],
                 lambda f: 1.0 - (f - 4) / 10.0 if f > 4 else 1.0, 1, 99, "WarZombie_hook")
# zombie chases slightly to Remy's right, a bit slower, so the gap opens after the miss
GAP0 = 0.62
for f, gap in ((1, GAP0), (12, GAP0 + 0.15), (40, GAP0 + 1.4), (99, GAP0 + 4.6)):
    z_root.location = (0.50, Y0 + gap - v_run * (f - 1), 0.0)
    z_root.keyframe_insert("location", frame=f)

# ---------------------------------------------------------------- camera: low, rushing backward ahead of Remy
cam = link(bpy.data.objects.new("Cam_S01", bpy.data.cameras.new("Cam_S01")))
cam.data.lens, cam.data.sensor_fit, cam.data.sensor_height = 22, "VERTICAL", 24
cam.data.clip_start = 0.02
for f in range(1, 100):
    rl = Vector((0.0, Y0 - v_run * (f - 1), 0.0))
    if f <= 39:                       # S01: low, close, slight shake
        k = (f - 1) / 38
        loc = rl + Vector((0.85 - 0.15 * k, -2.15 - 0.4 * k, 0.48)) + Vector((0.012 * math.sin(f * 2.1), 0, 0.01 * math.sin(f * 3.3)))
        tgt = rl + Vector((0.12, 0.45, 0.78))
    else:                             # S02: CU over his shoulder region, handheld, looking back past him
        loc = rl + Vector((0.55, -1.05, 1.55)) + Vector((0.01 * math.sin(f * 2.7), 0, 0.008 * math.sin(f * 3.9)))
        tgt = rl + Vector((-0.1, 0.4, 1.45))
    cam.location = loc
    cam.rotation_euler = (tgt - loc).to_track_quat("-Z", "Y").to_euler()
    cam.keyframe_insert("location", frame=f)
    cam.keyframe_insert("rotation_euler", frame=f)
sc.camera = cam

# front key so faces/zombie aren't silhouettes against the bright street
key = link(bpy.data.objects.new("FrontKey", bpy.data.lights.new("FrontKey", "SUN")))
key.data.energy, key.data.angle = 2.2, math.radians(4)
key.rotation_euler = (math.radians(62), 0, math.radians(200))

# ---------------------------------------------------------------- render
r = sc.render
r.engine = "CYCLES"
sc.cycles.device = "CPU"
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
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "hook.blend"))
print("saved hook.blend")
