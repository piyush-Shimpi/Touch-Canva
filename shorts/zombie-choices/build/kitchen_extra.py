# exec'd at the end of house_scene.py (shares its namespace)
# Local timeline: S03 barricade 200-242 | S04 fridge empties 260-309 | S05 weak on the floor 320-367
#                 S06 hand ECU 380-421 | S10 jug slams 440-484 | S11 filling jugs 500-541 | S12 PEAK 560-601
DIG = os.path.join(ANIM, "action")


def descendants(ob):
    out = [ob]
    for c in ob.children:
        out += descendants(c)
    return out


def show_only(root, pairs):
    """hide/show a whole character (meshes too; hiding the root empty alone does nothing)"""
    for o in descendants(root):
        key_hide(o, pairs)


def clone_character(root, arm, meshes, name):
    r2 = link(bpy.data.objects.new(name + "_root", None))
    r2.scale = root.scale
    a2 = arm.copy()
    a2.animation_data_clear()
    link(a2, r2)
    a2.matrix_parent_inverse = arm.matrix_parent_inverse.copy()
    for m in meshes:
        m2 = m.copy()
        m2.animation_data_clear()                         # don't share the original's hide keys
        link(m2, a2)
        m2.matrix_parent_inverse = m.matrix_parent_inverse.copy()
        for md in m2.modifiers:
            if md.type == "ARMATURE":
                md.object = a2
    return r2, a2


def fridge(name, open_door=False):
    white = mat("FridgeWhite", "#eef1f3", 0.25)
    inner = mat("FridgeInner", "#f7fbff", 0.35)
    root = link(bpy.data.objects.new(name, None))
    if not open_door:
        local_box(name + "_body", (0.72, 0.68, 1.75), (0, 0, 0.875), white, root, 0.02)
    if open_door:                                           # hollow shell so the shelves are visible
        local_box(name + "_back", (0.72, 0.04, 1.75), (0, 0.32, 0.875), inner, root)
        for sx in (-0.34, 0.34):
            local_box(name + "_side", (0.04, 0.68, 1.75), (sx, 0, 0.875), white, root, 0.005)
        for zz in (0.02, 1.73):
            local_box(name + "_cap", (0.72, 0.68, 0.04), (0, 0, zz), white, root, 0.005)
        fl_ = link(bpy.data.objects.new(name + "_light", bpy.data.lights.new(name + "_light", "POINT")), root)
        fl_.data.energy, fl_.data.color, fl_.data.shadow_soft_size = 25, (0.9, 0.97, 1.0), 0.1
        fl_.location = (0, -0.05, 1.55)
        for z in (0.45, 0.85, 1.25):
            local_box(name + "_shelf", (0.62, 0.5, 0.012), (0, -0.08, z), mat("Glass", "#d8ecf4", 0.05,
                      **{"Transmission Weight": 0.8}), root)
        local_box(name + "_door", (0.04, 0.70, 1.72), (-0.37, -0.70, 0.875), white, root, 0.01)   # swung fully open
    else:
        local_box(name + "_door", (0.7, 0.04, 1.72), (0, -0.35, 0.875), white, root, 0.01)
        local_box(name + "_handle", (0.03, 0.04, 0.5), (0.28, -0.39, 1.2), steel, root)
    return root


def jug(name, fill=None):
    plastic = bpy.data.materials.get("Jug") or mat("Jug", "#e8f2f8", 0.18, **{"Transmission Weight": 0.65, "IOR": 1.45})
    cap = bpy.data.materials.get("Cap") or mat("Cap", "#1d6fd8", 0.4)
    root = link(bpy.data.objects.new(name, None))
    b = local_box(name + "_body", (0.16, 0.16, 0.26), (0, 0, 0.14), plastic, root)
    b.modifiers.new("bev", "BEVEL").width = 0.035
    b.modifiers.new("sub", "SUBSURF").levels = 2
    bpy.ops.mesh.primitive_cylinder_add(radius=0.024, depth=0.05, location=(0.035, 0, 0.29))
    n = bpy.context.active_object
    n.data.materials.append(plastic)
    n.parent = root
    bpy.ops.mesh.primitive_cylinder_add(radius=0.028, depth=0.025, location=(0.035, 0, 0.322))
    c = bpy.context.active_object
    c.data.materials.append(cap)
    c.parent = root
    bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.012, location=(-0.04, 0, 0.27),
                                     rotation=(math.radians(90), 0, 0))
    h = bpy.context.active_object
    h.data.materials.append(plastic)
    h.parent = root
    water = None
    if fill is not None:
        wm = bpy.data.materials.get("Water") or mat("Water", "#3aa0ff", 0.05, **{"Transmission Weight": 0.6,
                                                                               "Emission Color": srgb("#2d8cff"),
                                                                               "Emission Strength": 0.4})
        water = local_box(name + "_water", (0.14, 0.14, 0.24), (0, 0, 0.0), wm, root)
    return root, water


# ---------------------------------------------------------------- hallway Remy only exists in S01/S02
show_only(remy_root, ((-60, False), (100, True)))
show_only(z_root, ((-60, False), (100, True)))
# door rattles shut against the barricade between the hook and the peak
for f in range(100, 540):
    a = -math.radians(2.0 * abs(math.sin(f * 1.3))) if f % 23 < 4 else 0.0
    hinge.rotation_euler = (0, 0, a)
    hinge.keyframe_insert("rotation_euler", frame=f)
for lk in links_:
    key_hide(lk, ((-60, False), (562, True)))          # chain snaps at the peak

# ---------------------------------------------------------------- S03 barricade: fridge slides against the front door
bar = fridge("BarricadeFridge")
for f, x, y, rz in ((200, -1.05, -0.9, 0.5), (214, -0.3, -0.55, 0.15), (222, 0.0, -0.45, 0.0), (559, 0.0, -0.45, 0.0)):
    bar.location = (x, y, 0)
    bar.rotation_euler = (0, 0, rz)
    bar.keyframe_insert("location", frame=f)
    bar.keyframe_insert("rotation_euler", frame=f)
for f, rx, y in ((560, 0.0, -0.45), (566, math.radians(-60), -0.9), (572, math.radians(-90), -1.25)):   # knocked over at the peak
    bar.rotation_euler = (rx, 0, 0)
    bar.location = (0.0, y, 0)
    bar.keyframe_insert("rotation_euler", frame=f)
    bar.keyframe_insert("location", frame=f)
show_only(bar, ((-60, True), (190, False)))

r1_root, r1, _, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "RemyBar")
bake_mix(r1, [(terr, lambda f: 6 + (f - 190) * 0.25), (terr, lambda f: 6 + (f - 190) * 0.25)], lambda f: 0.0, 190, 250, "RemyBar")
r1_root.rotation_euler.z = math.radians(150)
for f, x, y in ((200, -1.5, -1.25), (222, -0.75, -0.85), (250, -0.85, -1.0)):
    r1_root.location = (x, y, 0)
    r1_root.keyframe_insert("location", frame=f)
show_only(r1_root, ((-60, True), (190, False), (250, True)))

# ---------------------------------------------------------------- kitchen (separate room at x = KX)
KX = 12.0
kf = box("KFloor", (4.0, 4.0, 0.05), (KX, -2.0, -0.025), floor_m)
tile = mat("Tile", "#e9e4da", 0.3)
for name, size, loc in (("KWallBack", (4.0, 0.12, 2.7), (KX, 0.06, 1.35)), ("KWallL", (0.12, 4.0, 2.7), (KX - 2.0, -2.0, 1.35)),
                        ("KWallR", (0.12, 4.0, 2.7), (KX + 2.0, -2.0, 1.35))):
    w_ = box(name, size, loc, plaster)
    uv_box(w_, 1.5)
box("KCeil", (4.0, 4.0, 0.05), (KX, -2.0, 2.725), mat("KCeiling", "#f3efe8", 0.8))
wood_c = mat("Cabinet", "#3c6e8f", 0.45)
counter_top = mat("CounterTop", "#e6e1d6", 0.3)
box("Counter", (2.6, 0.62, 0.88), (KX + 0.4, -0.31, 0.44), wood_c, 0.01)
box("CounterTop", (2.7, 0.66, 0.04), (KX + 0.4, -0.33, 0.9), counter_top, 0.005)
box("Backsplash", (2.7, 0.02, 0.6), (KX + 0.4, -0.01, 1.22), tile)
box("Sink", (0.6, 0.42, 0.05), (KX + 0.9, -0.33, 0.905), mat("SinkSteel", "#b8bec6", 0.15, Metallic=1.0))
box("SinkHole", (0.52, 0.34, 0.02), (KX + 0.9, -0.33, 0.925), mat("SinkDark", "#30353b", 0.3, Metallic=1.0))
bpy.ops.mesh.primitive_cylinder_add(radius=0.014, depth=0.32, location=(KX + 0.9, -0.08, 1.07))
fau = bpy.context.active_object
fau.data.materials.append(steel)
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.2, location=(KX + 0.9, -0.17, 1.22), rotation=(math.radians(90), 0, 0))
spout = bpy.context.active_object
spout.data.materials.append(steel)
kwin = box("KWindow", (1.0, 0.02, 0.8), (KX + 0.9, 0.0, 1.75), win)
kfill = link(bpy.data.objects.new("KFill", bpy.data.lights.new("KFill", "AREA")))
kfill.data.size, kfill.data.energy, kfill.data.color = 2.2, 300, (1.0, 0.9, 0.78)
kfill.location = (KX, -1.8, 2.65)
kfill.rotation_euler = (math.radians(180), 0, 0)
kfr = fridge("KitchenFridge", open_door=True)
kfr.location = (KX - 1.45, -0.4, 0)
# food on the shelves, vanishing over S04 (time-lapse of ~3 days)
food_cols = ["#e2412f", "#f2b632", "#4caf50", "#ffffff", "#8e5a2b", "#ff8a3d", "#2f7de1", "#c2185b"]
items = []
for zi, z in enumerate((0.47, 0.87, 1.27)):
    for i in range(6):
        c_ = food_cols[(zi * 6 + i) % len(food_cols)]
        if (zi + i) % 3 == 0:
            bpy.ops.mesh.primitive_cylinder_add(radius=0.035, depth=random.uniform(0.12, 0.22))
        else:
            bpy.ops.mesh.primitive_cube_add(size=1)
            bpy.context.active_object.scale = (random.uniform(0.06, 0.1), random.uniform(0.05, 0.09), random.uniform(0.08, 0.18))
        it = bpy.context.active_object
        it.data.materials.append(mat(f"Food{zi}{i}", c_, 0.5))
        it.parent = kfr
        it.location = (-0.24 + i * 0.095, -0.12 + 0.05 * (i % 2), z + it.dimensions.z / 2 + 0.008)
        items.append(it)
random.shuffle(items)
for k_, it in enumerate(items):
    gone = 268 + int(k_ * 36 / len(items))
    key_hide(it, ((-60, False), (gone, True)))

# S05/S06: Remy weak on the kitchen floor (kneeling clip, slowed right down)
dig_seed = load_action(os.path.join(DIG, "dig_and_plant_seeds.fbx"), ("mixamorig9:", "mixamorig:"))
r2_root, r2, _, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "RemyWeak")
bake_mix(r2, [(dig_seed, lambda f: 52 + (f - 315) * 0.12), (dig_seed, lambda f: 52 + (f - 315) * 0.12)], lambda f: 0.0, 315, 425, "RemyWeak")
r2_root.location = (KX - 0.5, -1.35, 0)
r2_root.rotation_euler.z = math.radians(200)
show_only(r2_root, ((-60, True), (315, False), (425, True)))

# S10/S11: water jug slams onto the counter, then Remy fills jugs at the sink
j1, _ = jug("SlamJug")
for f in range(436, 486):
    u = f - 442
    if u < 0:
        z, rx = 2.2, 0.4
    elif u < 6:
        z, rx = 0.92 + (2.2 - 0.92) * (1 - (u / 6) ** 2), 0.4 * (1 - u / 6)
    else:
        z, rx = 0.92 + 0.04 * abs(math.sin((u - 6) * 0.9)) * math.exp(-(u - 6) * 0.5), 0.0
    j1.location = (KX + 0.1, -0.35, z)
    j1.rotation_euler = (rx, 0, 0.3)
    j1.keyframe_insert("location", frame=f)
    j1.keyframe_insert("rotation_euler", frame=f)
show_only(j1, ((-60, True), (436, False), (490, True)))
j2, w2 = jug("FillJug", fill=True)
j2.location = (KX + 0.92, -0.3, 0.93)
for f, h in ((500, 0.05), (541, 0.95)):
    w2.scale = (1, 1, h)
    w2.location = (0, 0, 0.012 + 0.12 * h)
    w2.keyframe_insert("scale", frame=f)
    w2.keyframe_insert("location", frame=f)
wm_ = bpy.data.materials["Water"]
bpy.ops.mesh.primitive_cylinder_add(radius=0.007, depth=0.22, location=(KX + 0.9, -0.24, 1.15))
stream = bpy.context.active_object
stream.data.materials.append(wm_)
show_only(j2, ((-60, True), (495, False), (545, True)))
key_hide(stream, ((-60, True), (498, False), (545, True)))
r3_root, r3, _, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "RemySink")
bake_mix(r3, [(terr, lambda f: 3 + (f - 495) * 0.12), (terr, lambda f: 3 + (f - 495) * 0.12)], lambda f: 0.0, 495, 545, "RemySink")
sc.frame_set(500)
bpy.context.view_layer.update()
for f in range(495, 546):                                # arms forward over the sink (holding the jug), head down at it
    sc.frame_set(f)
    for side, s_ in (("Left", 1), ("Right", -1)):
        b_ = r3.pose.bones[f"mixamorig:{side}Arm"]
        b_.rotation_quaternion = b_.rotation_quaternion @ Quaternion((1, 0, 0), 0.9)
        b_.keyframe_insert("rotation_quaternion", frame=f)
    hb = r3.pose.bones["mixamorig:Head"]
    hb.rotation_quaternion = hb.rotation_quaternion @ Quaternion((1, 0, 0), 0.35)
    hb.keyframe_insert("rotation_quaternion", frame=f)
r3_root.location = (KX + 0.9, -0.92, 0)
r3_root.rotation_euler.z = math.radians(180)
show_only(r3_root, ((-60, True), (495, False), (545, True)))

# ---------------------------------------------------------------- S12 PEAK: zombies pour in through the burst door
zr_t = []
for i, (dx, delay) in enumerate(((0.0, 2), (-0.45, 7), (0.4, 11))):
    r_, a_ = clone_character(z_root, zom, z_meshes, f"Rush{i}")
    ad = a_.animation_data_create()
    tr = ad.nla_tracks.new()
    st = tr.strips.new("run", 540, z_run)
    try:
        st.action_slot = z_run.slots[0]
    except (AttributeError, IndexError):
        pass
    st.repeat = 4.0
    st.scale = 0.8
    for f in (560 + delay, 601):
        r_.location = (dx, 1.6 - 0.16 * (f - 560 - delay), 0)
        r_.keyframe_insert("location", frame=f)
    r_.location = (dx, 1.6, 0)
    r_.keyframe_insert("location", frame=540)
    show_only(r_, ((-60, True), (558, False), (605, True)))
# hit-flash card for the peak camera (added with the cameras below)

# ---------------------------------------------------------------- cameras S03-S12
def cam_seq(name, lens, frames, fn, fstop=None, focus_ob=None):
    c = cam(name, lens, fstop)
    if focus_ob:
        c.data.dof.focus_object = focus_ob
    for f in frames:
        loc, tgt = fn(f)
        ck(c, f, loc, tgt)
    return c


def sm(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


cam_seq("Cam_S03", 24, range(200, 243), lambda f: (
    Vector((0.7, -3.6, 1.35)), Vector((-0.35 - 2.5 * max(0.0, (206 - f) / 6) ** 2, -0.5, 1.0))))
cam_seq("Cam_S04", 30, range(260, 310), lambda f: (
    Vector((KX - 1.45 + 0.05, -1.55 + 0.25 * sm((f - 260) / 49), 1.05)), Vector((KX - 1.45, -0.3, 0.88))))
cam_seq("Cam_S05", 24, range(320, 368), lambda f: (
    Vector((KX - 0.3, -1.75, 2.55 - 0.35 * sm((f - 320) / 47))), Vector((KX - 0.55, -1.3, 0.0))))
focus_h = link(bpy.data.objects.new("FocusHand", None))


def s06(f):
    sc.frame_set(f)
    hand = r2.matrix_world @ r2.pose.bones["mixamorig:RightHand"].head
    focus_h.location = hand
    focus_h.keyframe_insert("location", frame=f)
    return hand + Vector((0.35, -0.45, 0.25)), hand


cam_seq("Cam_S06", 45, range(380, 422), s06, 2.0, focus_h)
cam_seq("Cam_S10", 35, range(440, 485), lambda f: (
    Vector((KX + 0.1, -0.35, 0.95)) + Vector((0.6, -1.6, 0.5)) * (1 - 0.8 * sm((f - 440) / 6)), Vector((KX + 0.1, -0.35, 1.05))))
cam_seq("Cam_S11", 32, range(500, 542), lambda f: (
    Vector((KX + 1.7 - 0.15 * sm((f - 500) / 41), -1.35, 1.45)), Vector((KX + 0.95, -0.4, 1.05))))
c12 = cam_seq("Cam_S12", 20, range(556, 602), lambda f: (
    Vector((0.35, -3.9, 0.45)) + Vector((0.015 * math.sin(f * 3.1), 0, 0.012 * math.sin(f * 2.3))) * (3 if 560 <= f < 566 else 1),
    Vector((0.0, 0.0, 1.15))))
fl = bpy.data.materials.new("Flash")
fl.node_tree.nodes.clear()
fo = fl.node_tree.nodes.new("ShaderNodeOutputMaterial")
fe = fl.node_tree.nodes.new("ShaderNodeEmission")
fe.inputs["Strength"].default_value = 16.0
fl.node_tree.links.new(fe.outputs[0], fo.inputs["Surface"])
fcard = local_box("FlashCard", (0.4, 0.6, 0.001), (0, 0, -0.05), fl, c12)
key_hide(fcard, ((-60, True), (561, False), (563, True)))
for hit_f in (560,):                                     # splinters burst again at the peak
    for i in range(18):
        bpy.ops.mesh.primitive_cube_add(size=1)
        sp = bpy.context.active_object
        sp.scale = (random.uniform(0.005, 0.012), random.uniform(0.03, 0.08), random.uniform(0.005, 0.012))
        sp.data.materials.append(wood)
        p0 = Vector((DW / 2 - 0.02, -0.05, random.uniform(0.8, 1.7)))
        v = Vector((random.uniform(-0.8, 0.5), random.uniform(-3.0, -1.2), random.uniform(0.2, 1.8))) / FPS
        for f in range(hit_f - 1, hit_f + 30):
            u = f - hit_f
            p = p0 if u < 0 else p0 + v * u + Vector((0, 0, -0.5 * 9.8 * (u / FPS) ** 2))
            p.z = max(p.z, 0.005)
            sp.location = p
            sp.keyframe_insert("location", frame=f)
        key_hide(sp, ((-60, True), (hit_f, False), (hit_f + 32, True)))
print("kitchen extras done")
