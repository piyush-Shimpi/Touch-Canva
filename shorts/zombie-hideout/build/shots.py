# exec'd by diorama.py (shares its globals). Characters per beat + cameras.
# Local timeline: hook S01 = frames 1..45 (pre-roll from -30 for the loop lead-in).


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


def strip(arm, act, start, scale=1.0, repeat=1.0, clip=None):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    tr = ad.nla_tracks.new()
    st = tr.strips.new(act.name, int(start), act)
    try:
        st.action_slot = act.slots[0]
    except (AttributeError, IndexError):
        pass
    if clip:
        st.action_frame_start, st.action_frame_end = clip
    st.scale = scale
    st.repeat = repeat
    st.extrapolation = "NOTHING"
    return st


def act(arm, act_, f0, f1, clip=None, speed=1.0, offset=0):
    """play act_ (optionally a clip range) from frame f0 to f1, looping, at speed; nothing outside"""
    c0, c1 = clip or tuple(act_.frame_range)
    scale = 1.0 / speed
    seg = (c1 - c0) * scale
    st = strip(arm, act_, f0 - offset, scale, max(1.0, (f1 - f0 + offset + 2) / seg), clip=(c0, c1))
    return st


def cam(name, lens, fstop=None, focus=None):
    c = link(bpy.data.objects.new(name, bpy.data.cameras.new(name)))
    c.data.lens, c.data.sensor_fit, c.data.sensor_height = lens, "VERTICAL", 24
    c.data.clip_start = 0.05
    if fstop:
        c.data.dof.use_dof, c.data.dof.aperture_fstop = True, fstop
        c.data.dof.focus_object = focus
    return c


def ck(c, f, loc, tgt, lens=None):
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_euler", frame=f)
    if lens:
        c.data.lens = lens
        c.data.keyframe_insert("lens", frame=f)


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


FACE_PX, FACE_NX = math.radians(90), math.radians(-90)   # Mixamo faces -y; +90 deg about z -> faces +x

# ---------------------------------------------------------------- S01 hook: the horde at the pool, Remy hiding behind the falls
# lead zombie screams at the water on frame 1 (clip runs from its big inhale)
lead_r, lead_a = clone(z_root, zom, zmeshes, "ZLead")
lead_r.location = (-2.85, 1.0, BANK_Z)
lead_r.rotation_euler.z = FACE_PX + 0.15
strip(lead_a, A["scream"], -28, 1.0, 3.0)
horde = []
for i, (x, y, kind) in enumerate(((-3.6, 1.7, "g"), (-4.2, 0.6, "z"), (-4.7, 2.5, "g"), (-5.3, 1.2, "z"),
                                  (-3.9, 3.4, "z"), (-5.9, 2.9, "g"))):
    r_, a_ = clone(g_root, girl, gmeshes, f"H{i}") if kind == "g" else clone(z_root, zom, zmeshes, f"H{i}")
    r_.location = (x + random.uniform(-0.15, 0.15), y, BANK_Z)
    r_.rotation_euler.z = FACE_PX + random.uniform(-0.35, 0.35)
    if kind == "g":
        st_ = strip(a_, A["gidle"], -60 + random.randint(0, 40), 1.0, 12.0)
    else:
        st_ = strip(a_, A["attack"], -60 + random.randint(0, 40), 1.25, 8.0)
    seg = (st_.action_frame_end - st_.action_frame_start) * st_.scale
    st_.repeat = (713 - st_.frame_start) / seg            # same timing as the hook render, just runs to the walk-off
    act(a_, A["zrun"], 713, 860, speed=0.45, offset=(i * 5) % 13)
    horde.append(r_)
for o in (z_root, g_root):
    o.location = (0, 80, 0)

# Remy pressed against the room wall, cowering, eyes on the doorway
remy_root.location = (1.05, 0.75, ROOM[2])
remy_root.rotation_euler.z = FACE_NX + 0.35
act(remy, A["terrified"], -40, 45.6, clip=(20, 70), speed=0.62)
act(remy, A["terrified"], 46, 104, clip=(24, 62), speed=0.6)

c1 = cam("Cam_S01", 25)
for f, k in ((-30, 0.0), (45, 1.0)):
    kk = sm(k)
    ck(c1, f, Vector((-0.85 + 0.05 * kk, -15.2 + 3.0 * kk, 1.1 - 0.1 * kk)), Vector((-0.85 + 0.05 * kk, 0.0, 1.0 - 0.1 * kk)))
sc.camera = c1
sc.frame_start, sc.frame_end = 1, 45

# ---------------------------------------------------------------- S02: over Remy's shoulder, out through the falling water
c2 = cam("Cam_S02", 18)
for f, k in ((46, 0.0), (103, 1.0)):
    kk = sm(k)
    ck(c2, f, Vector((2.25 - 0.3 * kk, 1.2, 1.25)), Vector((-1.8, 0.7, 0.9 - 0.05 * kk)))
# Remy shifts to the doorway side for S02 (cut hides the jump)
for f, loc, rz in ((45, (1.05, 0.75, ROOM[2]), FACE_NX + 0.35), (45.6, (0.62, 1.05, ROOM[2]), FACE_PX + 0.45)):
    remy_root.location, remy_root.rotation_euler.z = loc, rz
    remy_root.keyframe_insert("location", frame=f)
    remy_root.keyframe_insert("rotation_euler", frame=f)
for fc in iter_fcurves(remy_root.animation_data.action):
    for kp in fc.keyframe_points:
        kp.interpolation = "CONSTANT"
sc.frame_end = 103

# ==================================================================== FULL TIMELINE (local frame == output frame)
# S03 104-150 zombie listens | S04 151-205 sound rings swallowed | S05 206-262 cold pool BRRR | S06 263-310 digging
# S07 311-360 walk in stream | S08 361-404 feet close | S09 405-450 swim | S10 451-490 climb in | S11 491-540 fire smoke
# S12 541-590 smoke into falls | S13 591-655 night glow | S14 656-712 PEAK | S15 713-756 walk past
# S16 757-805 falls shrinking | S17 806-852 Remy worried -> loops to S01
END = 855
sc.frame_end = END


def keyloc(ob, f, loc, rz=None):
    """hard cut of an object's placement at a shot start (subframe .6 so motion blur doesn't ghost)"""
    ob.location = loc
    ob.keyframe_insert("location", frame=f)
    if rz is not None:
        ob.rotation_euler.z = rz
        ob.keyframe_insert("rotation_euler", frame=f)


def constant(ob):
    if ob.animation_data and ob.animation_data.action:
        for fc in iter_fcurves(ob.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"


def inplace(action, bone="mixamorig:Hips"):
    """remove the forward drift from a root-motion cycle so it can loop; returns drift per frame (bone space)"""
    from lib_assets import iter_fcurves as itf
    best = None
    for fc in itf(action):
        if fc.data_path == f'pose.bones["{bone}"].location' and len(fc.keyframe_points) > 2:
            k = fc.keyframe_points
            d = k[-1].co.y - k[0].co.y
            if best is None or abs(d) > abs(best[1]):
                best = (fc, d)
    fc, d = best
    k = fc.keyframe_points
    f0, f1 = k[0].co.x, k[-1].co.x
    for kp in k:
        u = (kp.co.x - f0) / (f1 - f0)
        kp.co.y -= d * u
        kp.handle_left.y -= d * u
        kp.handle_right.y -= d * u
    return d / (f1 - f0)


def hips_speed(arm, action):
    """world metres per frame the clip's hips travel (measured before making it in-place)"""
    ad = arm.animation_data or arm.animation_data_create()
    old = ad.action
    set_action(arm, action)
    f0, f1 = map(int, action.frame_range)
    sc.frame_set(f0)
    a = (arm.matrix_world @ arm.pose.bones["mixamorig:Hips"].head).copy()
    sc.frame_set(f1)
    b = (arm.matrix_world @ arm.pose.bones["mixamorig:Hips"].head).copy()
    ad.action = old
    return (b - a).length / (f1 - f0)


WALK_V = hips_speed(remy, A["walk"])
inplace(A["walk"])
ZRUN_V = 0.035                                          # slowed war-zombie run used as a shamble

# ---------------------------------------------------------------- Remy placements per shot
RP = [  # frame, location, facing
    (103.6, (-1.2, 0.9, -0.95), FACE_PX),               # S03/S04: underwater? no: placeholder (hidden) - set below
]
keyloc(remy_root, 103.6, (0.95, 0.75, ROOM[2]), FACE_NX + 0.3)       # S03-S04: in the room (cowering, out of view in S03)
act(remy, A["terrified"], 104, 206, clip=(24, 62), speed=0.6)
# S05 cold pool: chest-deep at the plunge pool's near side, treading (swim clip, slowed), shivering
keyloc(remy_root, 205.6, (-1.3, 0.8, -0.85), FACE_PX)
act(remy, A["swim"], 206, 263, speed=0.45)
shiver = remy_root
# S06 digging into the rock (faces +x into the cliff, inside the doorway)
keyloc(remy_root, 262.6, (0.85, 0.85, ROOM[2]), FACE_PX)
act(remy, A["dig"], 263, 311, speed=1.15, offset=20)
# S07-S08 walking IN the stream on the cliff top (+x direction, away from the lip)
for f in range(311, 405):
    remy_root.location = (0.25 + WALK_V * 0.8 * (f - 311), 1.2, CLIFF_TOP - 0.02)
    remy_root.keyframe_insert("location", frame=f)
remy_root.rotation_euler.z = FACE_PX
remy_root.keyframe_insert("rotation_euler", frame=311)
act(remy, A["walk"], 311, 405, speed=0.8)
# S09 swimming underwater across the pool toward the falls (root motion clip, played once)
for f, x in ((404.6, -2.3), (450, -2.3)):
    keyloc(remy_root, f, (x, 1.0, -1.15), FACE_PX)
act(remy, A["swim"], 405, 451, speed=1.6)
# S10 surfaces behind the falls and climbs up into the doorway
keyloc(remy_root, 450.6, (-0.55, 1.0, -0.42), FACE_PX)
act(remy, A["swim_edge"], 451, 491, clip=(60, 151), speed=2.2)
# S11-S12 sitting by the fire
keyloc(remy_root, 490.6, (1.25, 0.95, ROOM[2] - 0.32), FACE_PX + 0.5)
act(remy, A["kneel"], 491, 591, clip=(60, 160), speed=0.8)
# S13 night: sitting, fire glowing
keyloc(remy_root, 590.6, (1.25, 0.95, ROOM[2] - 0.32), FACE_PX + 0.5)
act(remy, A["kneel"], 591, 656, clip=(60, 160), speed=0.8, offset=30)
# S14 peak: frozen behind the curtain, terrified
keyloc(remy_root, 655.6, (0.55, 1.2, ROOM[2]), FACE_NX)
act(remy, A["terrified"], 656, 757, clip=(20, 60), speed=0.5)
# S16-S17 the waterfall thins; he steps back from the doorway
keyloc(remy_root, 756.6, (0.62, 1.05, ROOM[2]), FACE_PX + 0.45)
act(remy, A["terrified"], 757, 853, clip=(30, 70), speed=0.5)
constant(remy_root)
# S07/S08 walk keys must stay linear (they were inserted per frame anyway)

# ---------------------------------------------------------------- horde: hidden while Remy works, back for the peak
# lead zombie: S01 scream; S14 walks to the pool edge and screams at the falls; S15 turns away
for f, loc, rz in ((-60, (-2.85, 1.0, BANK_Z), FACE_PX + 0.15), (655.6, (-3.6, 0.9, BANK_Z), FACE_PX), (690, (-2.75, 0.9, BANK_Z), FACE_PX),
                   (712.6, (-2.8, 0.9, BANK_Z), FACE_NX), (757, (-4.4, 0.9, BANK_Z), FACE_NX)):
    keyloc(lead_r, f, loc, rz)
act(lead_a, A["attack"], 46, 104, speed=0.8)
act(lead_a, A["scream"], 104, 151, clip=(1, 60), speed=0.8)
act(lead_a, A["gidle"], 151, 656, speed=1.0)
act(lead_a, A["zrun"], 656, 690, speed=0.45)
act(lead_a, A["scream"], 690, 713, clip=(1, 60), speed=1.1)
act(lead_a, A["zrun"], 713, 760, speed=0.45)
# horde walks past (S15): everyone shambles off to the left
for r_ in horde:
    x0 = r_.location.x
    keyloc(r_, 712.6, (x0, r_.location.y, BANK_Z), FACE_NX + random.uniform(-0.3, 0.3))
    keyloc(r_, 757, (x0 - 1.6, r_.location.y, BANK_Z))

# ---------------------------------------------------------------- props per beat
# sound rings (S04): pale rings expand from Remy and die inside the falling water
ring_m = mat("Ring", "#9fe8ff", 0.4, **{"Emission Color": srgb("#9fe8ff"), "Emission Strength": 4.0,
                                         "Alpha": 0.7})
rings = []
for i in range(4):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.3, minor_radius=0.02, location=(0.95, 0.75, ROOM[2] + 1.45),
                                     rotation=(0, math.radians(90), 0))
    rg = bpy.context.active_object
    rg.name = f"SoundRing{i}"
    rg.data.materials.append(ring_m)
    f0 = 151 + i * 12
    for f, s_ in ((f0, 0.3), (f0 + 26, 3.2)):
        rg.scale = (s_, s_, s_)
        rg.keyframe_insert("scale", frame=f)
    key_hide(rg, ((-60, True), (f0, False), (f0 + 26, True)))
    rings.append(rg)

# dig progress (S06): rock fill slabs in the room vanish one by one
fills = []
for i, (fx0, fx1) in enumerate(((0.35, 1.0), (1.0, 1.65), (1.65, ROOM[1]))):
    fb = box(f"RoomFill{i}", fx0, fx1, ROOM[2], ROOM[3], y0=0.0, y1=ROOM_D, material=rock)
    t_off = 275 + i * 12
    key_hide(fb, ((-60, True), (262.6, False), (t_off, True)))
    fills.append(fb)
# the room's contents only exist once it's dug
room_props = [o for o in bpy.data.objects if o.name.startswith(("Flame", "Cylinder", "Cube", "Barrel_01_inst"))]
for o in room_props:
    key_hide(o, ((-60, False), (262.6, True), (311, False)))

# smoke (S11-S12): grey puffs up the vent and out into the falling water, where they vanish
smoke_m = mat("Smoke", "#d8d4cc", 0.9, **{"Alpha": 0.85})
path = [(1.75, 0.92, ROOM[2] + 0.45), (1.75, 0.92, ROOM[3] - 0.05), (1.75, 0.92, 2.79), (0.6, 0.92, 2.79),
        (-0.05, 0.92, 2.79), (-0.35, 0.92, 2.6)]
for i in range(9):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.12, location=path[0])
    sp = bpy.context.active_object
    sp.name = f"Smoke{i}"
    sp.data.materials.append(smoke_m)
    f0 = 491 + i * 10
    for k, p in enumerate(path):
        sp.location = p
        sp.keyframe_insert("location", frame=f0 + k * 9)
        g = 0.8 + 0.25 * k if k < len(path) - 1 else 0.15
        sp.scale = (g, g, g)
        sp.keyframe_insert("scale", frame=f0 + k * 9)
    key_hide(sp, ((-60, True), (f0, False), (f0 + 9 * (len(path) - 1), True)))

# night (S13): sky down, cold moon key, fire up; back to day after
bg = sc.world.node_tree.nodes["Background"]
for f, s_, e_, fe in ((590, 1.15, 4.6, 140), (590.6, 0.04, 0.35, 260), (655.6, 0.04, 0.35, 260), (656, 1.15, 4.6, 140)):
    bg.inputs["Strength"].default_value = s_
    bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
    sun.data.energy = e_
    sun.data.keyframe_insert("energy", frame=f)
for f, c_ in ((590, (1.0, 0.95, 0.86)), (590.6, (0.55, 0.65, 1.0)), (655.6, (0.55, 0.65, 1.0)), (656, (1.0, 0.95, 0.86))):
    sun.data.color = c_
    sun.data.keyframe_insert("color", frame=f)
constant(sun.data) if False else None
for idb in (sc.world.node_tree, sun.data):
    if idb.animation_data and idb.animation_data.action:
        for fc in iter_fcurves(idb.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "CONSTANT"

# falls shrinking (S16-S17): thinner, narrower curtain; foam fades
for f, th, wy in ((757, 0.24, 1.0), (840, 0.05, 0.35)):
    sol.thickness = th
    sol.keyframe_insert("thickness", frame=f)
    wfall.scale = (1, wy, 1)
    wfall.keyframe_insert("scale", frame=f)
for o in bpy.data.objects:
    if o.name.startswith("Foam"):
        for f, s_ in ((757, 1.0), (840, 0.35)):
            o.scale.z = 0.32 * s_
            o.keyframe_insert("scale", index=2, frame=f)

# ---------------------------------------------------------------- cameras
def camshot(name, lens, f0, f1, p0, p1, t0, t1, fstop=None, focus=None):
    c = cam(name, lens, fstop, focus)
    for f, k in ((f0, 0.0), (f1, 1.0)):
        kk = sm(k)
        ck(c, f, Vector(p0).lerp(Vector(p1), kk), Vector(t0).lerp(Vector(t1), kk))
    return c


camshot("Cam_S03", 45, 104, 150, (-1.6, -2.2, 1.5), (-1.75, -1.7, 1.45), (-2.85, 1.0, 1.55), (-2.85, 1.0, 1.6))
camshot("Cam_S04", 26, 151, 205, (-0.2, -13.0, 1.2), (-0.1, -12.2, 1.2), (-0.2, 0.0, 1.0), (-0.1, 0.0, 1.05))
camshot("Cam_S05", 30, 206, 262, (-1.0, -3.6, 0.1), (-0.9, -3.1, 0.05), (-0.95, 0.8, -0.35), (-0.9, 0.8, -0.3))
camshot("Cam_S06", 28, 263, 310, (0.95, -4.2, 1.35), (1.05, -3.8, 1.3), (0.95, 0.8, 1.2), (1.05, 0.8, 1.2))
c7, c8 = cam("Cam_S07", 26), cam("Cam_S08", 30)
for f in range(311, 405):
    sc.frame_set(f)
    hp_ = remy.matrix_world @ remy.pose.bones["mixamorig:Hips"].head
    if f <= 360:      # S07: medium-wide from the front-left, waterfall lip in the corner
        ck(c7, f, hp_ + Vector((-0.9, -4.6, 0.55)), hp_ + Vector((-0.4, 0, -0.2)))
    else:             # S08: low, at the water line, feet splashing past
        ck(c8, f, Vector((hp_.x + 0.9, -1.1, CLIFF_TOP + 0.12)), Vector((hp_.x, 1.2, CLIFF_TOP + 0.25)))
camshot("Cam_S09", 28, 405, 450, (-1.8, -5.0, -0.5), (-1.3, -4.8, -0.45), (-1.8, 1.0, -0.6), (-1.2, 1.0, -0.55))
camshot("Cam_S10", 30, 451, 490, (0.2, -3.6, 0.6), (0.3, -3.3, 0.7), (-0.1, 1.0, 0.35), (0.1, 1.0, 0.55))
camshot("Cam_S11", 30, 491, 540, (1.3, -3.4, 1.6), (1.3, -3.0, 1.9), (1.5, 0.9, 1.3), (1.4, 0.9, 1.9))
camshot("Cam_S12", 32, 541, 590, (0.6, -3.4, 2.75), (0.3, -3.2, 2.75), (0.4, 0.9, 2.7), (-0.1, 0.9, 2.65))
camshot("Cam_S13", 26, 591, 655, (-0.6, -14.0, 1.1), (-0.6, -12.8, 1.0), (-0.6, 0.0, 1.0), (-0.6, 0.0, 0.95))
camshot("Cam_S14", 24, 656, 712, (-4.1, -1.9, 1.4), (-3.8, -1.4, 1.45), (-1.9, 0.95, 1.3), (-1.85, 0.95, 1.4))
camshot("Cam_S15", 26, 713, 756, (-1.4, -13.5, 1.2), (-1.8, -13.0, 1.2), (-1.4, 0.0, 1.0), (-1.8, 0.0, 1.0))
camshot("Cam_S16", 26, 757, 805, (-0.6, -12.0, 2.2), (-0.5, -10.5, 2.0), (-0.4, 0.0, 2.0), (-0.3, 0.0, 1.6))
camshot("Cam_S17", 18, 806, 855, (2.25, 1.2, 1.25), (1.95, 1.2, 1.25), (-1.8, 0.7, 0.9), (-1.8, 0.7, 0.85))

# shovel for the digging beat (S06): shaft from the right hand through the left, keyed per frame
handle_m = mat("ShovelWood", "#a8794a", 0.6)
blade_m = mat("ShovelBlade", "#7d858c", 0.35, Metallic=1.0)
shovel = link(bpy.data.objects.new("Shovel", None))
bpy.ops.mesh.primitive_cylinder_add(radius=0.016, depth=1.05, location=(0, 0, 0))
hd = bpy.context.active_object
hd.data.materials.append(handle_m)
hd.parent = shovel
hd.location = (0, 0, -0.38)
bl = box("Blade", -0.1, 0.1, -1.13, -0.87, y0=-0.01, y1=0.01, material=blade_m, parent=shovel)
rh, lh = remy.pose.bones["mixamorig:RightHand"], remy.pose.bones["mixamorig:LeftHand"]
for f in range(263, 311):
    sc.frame_set(f)
    pr, pl = remy.matrix_world @ rh.head, remy.matrix_world @ lh.head
    d = pl - pr
    if d.length < 0.05:
        d = Vector((0.3, 0, -1))
    d.normalize()
    shovel.location = pr + d * 0.1
    shovel.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    shovel.keyframe_insert("location", frame=f)
    shovel.keyframe_insert("rotation_euler", frame=f)
for o in (hd, bl):
    key_hide(o, ((-60, True), (262.6, False), (310.6, True)))
