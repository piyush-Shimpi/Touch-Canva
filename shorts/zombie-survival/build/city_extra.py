# exec'd at the end of city_scene.py (shares its namespace): crowd S05, car + escape S06, scream ECU S07
from lib_assets import import_glb, key_hide  # noqa: E402,F401


def clone_character(root, arm, meshes, name):
    r2 = link(bpy.data.objects.new(name + "_root", None))
    r2.scale = root.scale
    a2 = arm.copy()
    a2.animation_data_clear()
    link(a2, r2)
    a2.matrix_parent_inverse = arm.matrix_parent_inverse.copy()
    for m in meshes:
        m2 = m.copy()
        link(m2, a2)
        m2.matrix_parent_inverse = m.matrix_parent_inverse.copy()
        for md in m2.modifiers:
            if md.type == "ARMATURE":
                md.object = a2
    return r2, a2


def loop_clip(arm, action, offset, scale=1.0):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    tr = ad.nla_tracks.new()
    a0, a1 = action.frame_range
    st = tr.strips.new(action.name, int(-400 + offset), action)
    try:
        st.action_slot = action.slots[0]
    except (AttributeError, IndexError):
        pass
    st.repeat = 1000.0 / max(1.0, a1 - a0)
    st.scale = scale
    st.extrapolation = "HOLD"


key_hide(zom, ((1, False), (100, True)))
for m in z_meshes:
    key_hide(m, ((1, False), (100, True)))

# ---------------------------------------------------------------- crowd (S05) + background horde (S06)
import random  # noqa: E402
random.seed(5)
cop_root, cop, cop_meshes, cop_walk = import_character(os.path.join(ANIM, "zombie", "zombie_walk_copzombie.fbx"), 1.85, "CopZombie")
degore({s.material for o in cop_meshes for s in o.material_slots})
girl_root, girl, girl_meshes, girl_idle = import_character(os.path.join(ANIM, "zombie", "zombie_idle_zombiegirl.fbx"), 1.72, "ZombieGirl")
degore({s.material for o in girl_meshes for s in o.material_slots})
v_walk = 0.062                                                # ~0.8 m/s shamble (in-place clip has no planted-foot drift to measure)
print("zombie walk speed m/frame", round(v_walk, 4))
YC = -96.0                                                    # crowd front line at frame 200
crowd = []
spots = []
for i in range(28):
    for _ in range(200):
        x, y = random.uniform(-5.0, 5.0), YC + random.uniform(0, 12) + abs(random.gauss(0, 2))
        if all((x - a) ** 2 + (y - b) ** 2 > 1.1 for a, b in spots):
            break
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    kind = ("cop", "girl", "war")[i % 3]
    # the cop-zombie "walk" FBX is a static T-pose, so the horde jogs with the War Zombie run (slowed)
    if kind == "girl" and i % 2:
        r2, a2 = clone_character(girl_root, girl, girl_meshes, f"Crowd{i}")
        loop_clip(a2, girl_idle, random.uniform(0, 100))
        moving = False
    else:
        src = {"cop": (cop_root, cop, cop_meshes), "girl": (girl_root, girl, girl_meshes), "war": (z_root, zom, z_meshes)}[kind]
        r2, a2 = clone_character(*src, f"Crowd{i}")
        loop_clip(a2, z_run, random.uniform(0, 40), scale=1.7)
        moving = True
    s_ = random.uniform(0.94, 1.06)
    r2.scale = tuple(c * s_ for c in r2.scale)
    yaw = random.uniform(-0.25, 0.25)
    r2.rotation_euler.z = yaw
    sp = v_walk * random.uniform(0.85, 1.1) if moving else 0.0
    for f in (150, 300):
        r2.location = (x + math.sin(yaw) * sp * (f - 200), y - math.cos(yaw) * sp * (f - 200), 0)
        r2.keyframe_insert("location", frame=f)
    for fc in iter_fcurves(r2.animation_data.action):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"
    key_hide(r2, ((-40, True), (150, False)))
    crowd.append(r2)
# originals live elsewhere (they are only templates)
for ob in (cop_root, girl_root):
    ob.location = (60, 60, 0)

# ---------------------------------------------------------------- abandoned car (S06/S07)
car_objs = import_glb(os.path.join(LIB, "environments", "vehicles", "oldsmobile_sedan.glb"))
car_root = link(bpy.data.objects.new("Car", None))
for o in car_objs:
    if o.parent is None:
        o.parent = car_root
bpy.context.view_layer.update()
pts = [o.matrix_world @ Vector(c) for o in car_objs if o.type == "MESH" for c in o.bound_box]
lo = Vector([min(p[i] for p in pts) for i in range(3)])
hi = Vector([max(p[i] for p in pts) for i in range(3)])
length = max(hi.x - lo.x, hi.y - lo.y)
car_root.scale = (5.0 / length,) * 3
car_root.location = (2.4, YB - 3.2, -lo.z * 5.0 / length)
car_root.rotation_euler.z = math.radians(28 + (90 if hi.x - lo.x > hi.y - lo.y else 0))
print("car length", round(length, 2))

# ---------------------------------------------------------------- scream zombie by the car (S07)
scr_act = load_action(os.path.join(ANIM, "zombie", "zombie_scream_skeletonzombie.fbx"))
sr_root, sr_arm = clone_character(cop_root, cop, cop_meshes, "Screamer")
nla(sr_arm, [dict(action=scr_act, start=300, extrap="HOLD")])
sr_root.location = (1.3, YB - 6.0, 0)
sr_root.rotation_euler.z = math.radians(-115)                # faces the road / camera side

# ---------------------------------------------------------------- cameras S05-S07
def cam_obj(name, lens):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens, c.data.sensor_fit, c.data.sensor_height = lens, "VERTICAL", 24
    c.data.clip_start = 0.02
    return c


def ck(c, f, loc, tgt):
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_euler", frame=f)


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


c5 = cam_obj("Cam_S05", 24)
for f in range(200, 248):
    k = sm((f - 200) / 47)
    yc = YC + 4 - v_walk * (f - 200)
    ck(c5, f, Vector((1.8 - 0.9 * k, yc - 10.0 + 4.6 * k, 6.0 - 4.7 * k)), Vector((0.0, yc + 2.5, 1.2 + 0.25 * k)))
c6 = cam_obj("Cam_S06", 28)
for f in range(258, 300):
    y = YB - v_run * (f - 259)
    ck(c6, f, Vector((-3.3, y - 1.2, 0.95)) + Vector((0, 0, 0.02 * math.sin(f * 2.3))), Vector((0.5, y - 0.15, 1.0)))
c7 = cam_obj("Cam_S07", 40)
bpy.context.view_layer.update()
for f in range(308, 344):
    k = sm((f - 308) / 34)
    sc.frame_set(f)
    head = sr_arm.matrix_world @ sr_arm.pose.bones["mixamorig:Head"].head
    fwd = Vector((math.cos(math.radians(-115 - 90)), math.sin(math.radians(-115 - 90)), 0))
    ck(c7, f, head + fwd * (1.05 - 0.2 * k) + Vector((0.05, 0, 0.04)), head + Vector((0, 0, -0.11)))
print("city extras: crowd", len(crowd))
