"""Outdoor sets, one blend each (SET env):
  pack      S08 local 1-45    water jugs drop into the orange backpack (top-down macro)
  road      S09 local 1-48    Remy jogs a countryside road, horde far behind
  mountain  S11 1-33 climb past the QORVEX LAB trail sign | S13 60-83 summit, sees it | S14 100-126 zombie climbing, whip pan
Run: SET=pack /opt/bvenv/bin/python build/outdoor_scene.py  -> build/<set>.blend"""
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib_assets import (ANIM, LIB, append_polyhaven, bake_mix, degore, foot_speed, hdri_world, import_character,  # noqa: E402
                        iter_fcurves, key_hide, link, load_action, polyhaven_material, srgb)

SET = os.environ.get("SET", "pack")
random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30


def mat(name, color, rough=0.5, **kw):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = srgb(color)
    b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m


def ground(size, material, uv_scale=4.0, name="Ground"):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x / uv_scale, lp.vert.co.y / uv_scale)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    return link(bpy.data.objects.new(name, me))


def cam(name, lens):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens, c.data.sensor_fit, c.data.sensor_height = lens, "VERTICAL", 24
    c.data.clip_start = 0.01
    return c


def ck(c, f, loc, tgt, roll=0.0):
    c.location = loc
    q = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y")
    if roll:
        q = q @ Quaternion((0, 0, 1), roll)
    c.rotation_euler = q.to_euler()
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_euler", frame=f)


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def place(objs, loc, rot=0.0, scale=1.0):
    for o in objs:
        sc.collection.objects.link(o)
    for o in [o for o in objs if o.parent is None]:
        o.location = Vector(loc) + o.location
        o.rotation_euler.z += math.radians(rot)
        o.scale = tuple(s * scale for s in o.scale)
    return objs


_PROTO = {}


def instance(folder, loc, rot=0.0, scale=1.0):
    """Poly Haven model appended once into a hidden collection, placed as lightweight collection instances"""
    if folder not in _PROTO:
        objs, _ = append_polyhaven(folder)
        coll = bpy.data.collections.new("proto_" + folder)
        for o in objs:
            coll.objects.link(o)
        _PROTO[folder] = coll
    e = link(bpy.data.objects.new(folder + "_inst", None))
    e.instance_type = "COLLECTION"
    e.instance_collection = _PROTO[folder]
    e.location = loc
    e.rotation_euler.z = math.radians(rot)
    e.scale = (scale,) * 3
    return e


def backpack(name="Backpack", open_top=False, size=1.0):
    """rounded orange hiking pack: body + front pocket + top flap + 2 straps"""
    orange = mat("PackOrange", "#ff7a1a", 0.6)
    dark = mat("PackDark", "#2a2d33", 0.7)
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1)
    body = bpy.context.active_object
    body.scale = (0.34, 0.24, 0.48)
    if open_top:
        bm = bmesh.new()
        bm.from_mesh(body.data)
        top = [f for f in bm.faces if f.normal.z > 0.9]
        bmesh.ops.delete(bm, geom=top, context="FACES")
        bm.to_mesh(body.data)
        bm.free()
        body.modifiers.new("sol", "SOLIDIFY").thickness = 0.03
    bev = body.modifiers.new("bev", "BEVEL")
    bev.width, bev.segments = 0.07, 3
    body.modifiers.new("sub", "SUBSURF").levels = 2
    body.data.materials.append(orange)
    if open_top:
        body.data.materials.append(dark)
        body.modifiers["sol"].material_offset = 1
    parts.append(body)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.115, -0.08))
    pocket = bpy.context.active_object
    pocket.scale = (0.22, 0.05, 0.18)
    pocket.modifiers.new("bev", "BEVEL").width = 0.2
    pocket.modifiers.new("sub", "SUBSURF").levels = 2
    pocket.data.materials.append(orange)
    parts.append(pocket)
    for x in (-0.09, 0.09):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, 0.11, 0.0))
        st = bpy.context.active_object
        st.scale = (0.035, 0.02, 0.4)
        st.data.materials.append(dark)
        parts.append(st)
    for p in parts:
        for poly in p.data.polygons:
            poly.use_smooth = True
    root = link(bpy.data.objects.new(name, None))
    for p in parts:
        p.parent = root
    root.scale = (size,) * 3
    return root


def jug(name):
    """1-gallon water jug: rounded box body, neck, cap, handle"""
    plastic = bpy.data.materials.get("Jug") or mat("Jug", "#e8f2f8", 0.18, **{"Transmission Weight": 0.65, "IOR": 1.45})
    cap = bpy.data.materials.get("Cap") or mat("Cap", "#1d6fd8", 0.4)
    parts = []
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.14))
    b = bpy.context.active_object
    b.scale = (0.16, 0.16, 0.26)
    b.modifiers.new("bev", "BEVEL").width = 0.3
    b.modifiers.new("sub", "SUBSURF").levels = 2
    b.data.materials.append(plastic)
    parts.append(b)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.024, depth=0.05, location=(0.035, 0, 0.29))
    n = bpy.context.active_object
    n.data.materials.append(plastic)
    parts.append(n)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.028, depth=0.025, location=(0.035, 0, 0.322))
    c = bpy.context.active_object
    c.data.materials.append(cap)
    parts.append(c)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.012, location=(-0.04, 0, 0.27),
                                     rotation=(math.radians(90), 0, 0))
    h = bpy.context.active_object
    h.data.materials.append(plastic)
    parts.append(h)
    for p in parts:
        for poly in p.data.polygons:
            poly.use_smooth = True
    root = link(bpy.data.objects.new(name, None))
    for p in parts:
        p.parent = root
    return root


def attach_to_spine(ob, arm, offset):
    sc.frame_set(1)
    bpy.context.view_layer.update()
    sp2 = arm.pose.bones["mixamorig:Spine2"]
    anchor = arm.matrix_world @ sp2.head
    ob.location = anchor + Vector(offset)
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = "mixamorig:Spine2"
    bpy.context.view_layer.update()
    ob.matrix_world = mw


def remy_running(action_file, f0, f1, speed_scale=1.0, name="Remy"):
    root, arm, meshes, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, name)
    run = load_action(os.path.join(ANIM, "action", action_file))
    v = foot_speed(arm, run, *run.frame_range) * 1.15 * speed_scale
    a, b = run.frame_range
    bake_mix(arm, [(run, lambda f: a + (f * speed_scale) % (b - a)), (run, lambda f: a + (f * speed_scale) % (b - a))],
             lambda f: 0.0, f0, f1, name + "_run")
    return root, arm, meshes, v


def common_render(samples=24, transform="AgX", look="AgX - Medium High Contrast"):
    r = sc.render
    r.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.05
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    r.use_motion_blur = True
    r.motion_blur_shutter = 0.5
    r.resolution_x, r.resolution_y = 1080, 1920
    r.use_persistent_data = True
    sc.view_settings.view_transform = transform
    try:
        sc.view_settings.look = look
    except TypeError:
        pass


# ======================================================================== PACK (S08)
if SET == "pack":
    sc.frame_start, sc.frame_end = 1, 45
    hdri_world("wide_street_01", 1.0, -47)
    ground(30, polyhaven_material("asphalt_02"), 2.0)
    pk = backpack(open_top=True)
    pk.location = (0, 0, 0.22)
    pk.rotation_euler = (math.radians(-12), 0, math.radians(12))
    drops = []
    for i, (x, t0) in enumerate(((-0.075, 4), (0.08, 15), (0.0, 26))):
        j = jug(f"Jug{i}")
        j.scale = (0.95,) * 3
        land = Vector((x, 0.0, 0.17 + 0.07 * i))
        for f in range(1, 46):
            u = f - t0
            if u < 0:
                p, rz = land + Vector((0, 0, 3.0)), 0.0
            elif u < 9:                                   # fall with gravity, slight spin
                k = u / 9
                p, rz = land + Vector((0, 0, 3.0 * (1 - k * k))), 0.6 * (1 - k)
            else:                                         # bounce settle
                w = u - 9
                p, rz = land + Vector((0, 0, 0.06 * abs(math.sin(w * 0.9)) * math.exp(-w * 0.45))), 0.0
            j.location = p
            j.rotation_euler = (0.08 * math.sin(f * 0.7 + i), 0, rz + i * 0.4)
            j.keyframe_insert("location", frame=f)
            j.keyframe_insert("rotation_euler", frame=f)
        drops.append(j)
    c8 = cam("Cam_S08", 30)
    for f in range(1, 46):
        k = sm((f - 1) / 44)
        ck(c8, f, Vector((0.05, -0.75 + 0.15 * k, 1.25 - 0.25 * k)), Vector((0, 0.02, 0.22)), roll=0.1 * k)
    sc.camera = c8
    sun = link(bpy.data.objects.new("Key", bpy.data.lights.new("Key", "SUN")))
    sun.data.energy, sun.data.angle = 2.0, math.radians(3)
    sun.rotation_euler = (math.radians(35), 0, math.radians(200))
    common_render(28)

# ======================================================================== ROAD (S09)
elif SET == "road":
    sc.frame_start, sc.frame_end = 1, 48
    hdri_world("lilienstein", 1.6, 0)
    grass = polyhaven_material("aerial_grass_rock")
    ground(400, grass, 6.0, "Fields").location.z = -0.02
    road = ground(1, polyhaven_material("asphalt_02"), 0.25, "Road")
    road.scale = (7.0, 300, 1)
    for fc in road.data.uv_layers[0].data:
        fc.uv = (fc.uv.x * 7.0, fc.uv.y * 300)
    line = ground(1, mat("Line", "#f2d34a", 0.6), 1.0, "CenterLine")
    line.scale = (0.12, 300, 1)
    line.location.z = 0.004
    rroot, remy, _, v = remy_running("running.fbx", -10, 60, 1.0)
    pk = backpack(size=0.72)
    attach_to_spine(pk, remy, (0, 0.15, -0.12))
    for f in (-10, 60):
        rroot.location = (-1.6, -v * f, 0)
        rroot.keyframe_insert("location", frame=f)
    for fc in iter_fcurves(rroot.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    # a few zombies far behind on the road
    zr, zarm, zmeshes, zrun = import_character(os.path.join(ANIM, "zombie", "zombie_run_warzombie.fbx"), 1.85, "Z0")
    degore({s.material for o in zmeshes for s in o.material_slots})
    zr.location = (-0.8, 22, 0)
    gr, garm, gmeshes, _ = import_character(os.path.join(ANIM, "zombie", "zombie_idle_zombiegirl.fbx"), 1.72, "Z1")
    degore({s.material for o in gmeshes for s in o.material_slots})
    garm.animation_data.action = zrun
    try:
        garm.animation_data.action_slot = zrun.slots[0]
    except (AttributeError, IndexError):
        pass
    for o, x0, y0 in ((zr, -0.8, 24), (gr, 1.4, 27)):
        for f in (-10, 60):
            o.location = (x0, y0 - v * 0.8 * f, 0)
            o.keyframe_insert("location", frame=f)
    # roadside fence posts + trees for parallax
    for k in range(14):
        instance("tree_small_02", (random.choice((-1, 1)) * random.uniform(6.5, 14), 30 - k * 9 + random.uniform(-2, 2), 0),
                 random.uniform(0, 360), random.uniform(0.9, 1.4))
    c9 = cam("Cam_S09", 32)
    for f in range(1, 49):
        y = -v * f
        ck(c9, f, Vector((-3.6, y - 2.6, 1.25)) + Vector((0, 0, 0.015 * math.sin(f * 2.2))),
           Vector((-1.4, y + 0.6, 1.1)))
    sc.camera = c9
    common_render(24)

# ======================================================================== MOUNTAIN (S11, S13, S14)
else:
    sc.frame_start, sc.frame_end = 1, 126
    hdri_world("kloofendal_48d_partly_cloudy_puresky", 1.1, 0)
    sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
    sun.data.energy, sun.data.angle = 3.2, math.radians(2)
    sun.rotation_euler = (math.radians(55), 0, math.radians(150))
    SLOPE = math.radians(16)
    rock = polyhaven_material("aerial_grass_rock")
    me = bpy.data.meshes.new("Slope")
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=80, y_segments=120, size=1)
    bmesh.ops.scale(bm, vec=(120, 240, 1), verts=bm.verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for v_ in bm.verts:                                       # slope rising towards -Y with rolling bumps
        x, y = v_.co.x, v_.co.y
        v_.co.z = -y * math.tan(SLOPE) + 1.2 * math.sin(x * 0.11) * math.cos(y * 0.07) + 0.6 * math.sin(x * 0.31 + y * 0.23)
        v_.co.z += 0.02 * abs(x) ** 1.4 * 0.2
    for f in bm.faces:
        f.smooth = True
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x / 5, lp.vert.co.y / 5)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(rock)
    slope = link(bpy.data.objects.new("Slope", me))
    from mathutils.bvhtree import BVHTree  # noqa: E402
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(slope, dg)

    def hz(x, y):
        hit = bvh.ray_cast(Vector((x, y, 500)), Vector((0, 0, -1)))[0]
        return hit.z if hit else 0.0

    # scatter rocks, firs and cliffs
    for k in range(10):
        x, y = random.uniform(-18, 18), random.uniform(-60, 30)
        if abs(x) < 2.5:
            x += 4 * (1 if x >= 0 else -1)
        if -34 < y < -12 and abs(x) < 10:
            x = 13 * (1 if x >= 0 else -1)
        instance("boulder_01", (x, y, hz(x, y) - 0.2), random.uniform(0, 360), random.uniform(0.8, 2.2))
    for k in range(26):
        x, y = random.choice((-1, 1)) * random.uniform(11, 40), random.uniform(-80, 40)
        if not (-40 < y < 20):
            instance("rock_moss_set_02", (x, y, hz(x, y) - 0.1), random.uniform(0, 360), random.uniform(1.0, 1.8))
    for x, y, s_ in ((-60, -90, 6), (55, -100, 7)):
        instance("namaqualand_cliff_02", (x, y, hz(x, y) - 1), random.uniform(0, 360), s_)
    # trail sign with the channel name
    wood = mat("Wood", "#7a5232", 0.8)
    bpy.ops.mesh.primitive_cube_add(size=1)
    post = bpy.context.active_object
    post.scale = (0.1, 0.1, 1.6)
    post.data.materials.append(wood)
    bpy.ops.mesh.primitive_cube_add(size=1)
    board = bpy.context.active_object
    board.scale = (1.3, 0.06, 0.38)
    board.location = (0.35, -0.04, 0.55)
    board.data.materials.append(wood)
    bpy.ops.object.text_add()
    txt = bpy.context.active_object
    txt.data.body = "QORVEX LAB"
    txt.data.align_x, txt.data.align_y = "CENTER", "CENTER"
    txt.data.size = 0.2
    txt.data.extrude = 0.01
    txt.data.materials.append(mat("SignText", "#f4ecd8", 0.6))
    txt.rotation_euler = (math.radians(90), 0, 0)
    txt.location = (0.35, -0.08, 0.55)
    sign = link(bpy.data.objects.new("Sign", None))
    for o in (post, board, txt):
        o.parent = sign
    SX, SY = 1.6, -8.0
    sign.location = (SX, SY, hz(SX, SY) + 0.75)
    sign.rotation_euler.z = math.radians(-20)

    # Remy climbing (S11) then at the summit spot (S13)
    rroot, remy, _, v = remy_running("running.fbx", -10, 40, 0.8)
    pk = backpack(size=0.72)
    attach_to_spine(pk, remy, (0, 0.15, -0.12))
    terr = load_action(os.path.join(ANIM, "reactions", "terrified_leonard.fbx"), ("mixamorig9:", "mixamorig:"))
    # summit: frames 50-90, from a standing look-back into the flinch (terrified clip 1 -> 70)
    r_a, r_b = 1, 22
    run_act = bpy.data.actions["running"]
    bake2 = bake_mix(remy, [(run_act, lambda f: r_a + (f * 0.8) % (r_b - r_a)), (terr, lambda f: 1 + max(0, f - 56) * 2.2)],
                     lambda f: 0.0 if f < 50 else 1.0, -10, 90, "Remy_mtn")
    path = []
    for f in range(-10, 41):
        y = 6.0 - v * 0.75 * (f + 10)
        path.append((f, Vector((0.3, y, hz(0.3, y)))))
    for f, p in path:
        rroot.location = p
        rroot.keyframe_insert("location", frame=f)
    SUM = Vector((0.0, -22.0, hz(0.0, -22.0)))
    rroot.location = SUM
    rroot.rotation_euler.z = math.radians(160)               # turned back towards the valley
    rroot.keyframe_insert("location", frame=50)
    rroot.keyframe_insert("rotation_euler", frame=50)
    rroot.rotation_euler.z = 0
    rroot.keyframe_insert("rotation_euler", frame=41)
    for fc in iter_fcurves(rroot.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT" if kp.co[0] in (41, 50) else "LINEAR"

    # zombie trudging up the trail far below (S14)
    zr, zarm, zmeshes, zrun = import_character(os.path.join(ANIM, "zombie", "zombie_run_warzombie.fbx"), 1.85, "Climber")
    degore({s.material for o in zmeshes for s in o.material_slots})
    nla_ad = zarm.animation_data
    a0, a1 = zrun.frame_range
    bake_mix(zarm, [(zrun, lambda f: a0 + (f * 0.45) % (a1 - a0)), (zrun, lambda f: a0 + (f * 0.45) % (a1 - a0))],
             lambda f: 0.0, 95, 130, "Climber_slow")
    for f in (95, 130):
        y = 14.0 - 0.03 * (f - 95)
        zr.location = (0.6, y, hz(0.6, y))
        zr.keyframe_insert("location", frame=f)
    for fc in iter_fcurves(zr.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    c11 = cam("Cam_S11", 26)                                  # wide, low, Remy climbs past the sign
    for f in range(1, 34):
        y = 6.0 - v * 0.75 * (f + 10)
        p = Vector((0.3, y, hz(0.3, y)))
        cx, cy = p.x + 2.6, p.y - 4.2
        ck(c11, f, Vector((cx, cy, hz(cx, cy) + 1.25)), p + Vector((-0.6, 0.6, 1.2)))
    c13 = cam("Cam_S13", 40)                                  # CU at the summit, looking past him down the valley
    for f in range(56, 86):
        k = sm((f - 56) / 29)
        cx, cy = SUM.x + 1.2 - 0.15 * k, SUM.y - 2.4 + 0.3 * k
        ck(c13, f, Vector((cx, cy, hz(cx, cy) + 1.9)), SUM + Vector((-0.75, 2.6, 0.75)))
    c14 = cam("Cam_S14", 50)                                  # low angle down the trail at the climber, then whip pan
    for f in range(98, 128):
        zp = Vector((0.6, 14.0 - 0.03 * (f - 95), hz(0.6, 14.0 - 0.03 * (f - 95))))
        base = Vector((zp.x - 0.4, zp.y - 3.5, hz(zp.x - 0.4, zp.y - 3.5) + 0.6))
        tgt = zp + Vector((0, 0, 1.0))
        w = max(0.0, (f - 119) / 8) ** 2
        if w:
            tgt = tgt + Vector((9.0 * w, -2.0 * w, 1.2 * w))
        ck(c14, f, base, tgt)
    sc.camera = c11
    common_render(24)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{SET}.blend"))
print("saved", SET)
