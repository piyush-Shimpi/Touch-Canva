"""Penny Drop - a 25 s vertical explainer short, built entirely with bpy.

Run:  /opt/bvenv/bin/python build/build_scene.py          (writes build/penny.blend)
Uses the blender-stylized-npr skill (toon_setup.py) for the cel look + outlines.
Shots (30 fps, 750 frames):
  S1   1-98   rooftop: a finger pushes a penny off the ledge
  S2  99-240  "like a bullet": penny streaks down the facade
  S3 241-435  penny flips and flutters in the air
  S4 436-570  wide: penny drifting slowly past the tower (~40 km/h)
  S5 571-750  street: penny bonks a guy on the head, stars
"""
import math
import os
import random
import sys

import bpy  # noqa: I001  (bpy first: the pip module registers bmesh/mathutils)
import bmesh
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".claude", "skills"))
sys.path.insert(0, os.path.join(SKILLS, "blender-stylized-npr", "scripts"))
import toon_setup  # noqa: E402

random.seed(7)
FPS = 30
S1, S2, S3, S4, S5 = (1, 98), (99, 240), (241, 435), (436, 570), (571, 750)
H = 120.0          # tower height (m)
HALF = 9.0         # tower half width
PARAPET_Z = H + 0.9
PENNY_R, PENNY_T = 0.009525, 0.00152

# ---------------------------------------------------------------- reset
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, 750
col = sc.collection


def srgb(*c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def hexc(h):
    h = h.lstrip("#")
    return srgb(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))


MATS = {}


def mat(name, color, rough=0.5):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = hexc(color) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    MATS[name] = m
    return m


def facade_mat(name, wall, glass="#8fc4ec", roof="#6d6a75", win=(1.3, 1.9)):
    """Window grid in world space (x+y, z) via Brick Texture; roofs get a flat color."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(sep.outputs[0], add.inputs[0])
    nt.links.new(sep.outputs[1], add.inputs[1])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(add.outputs[0], comb.inputs[0])
    nt.links.new(sep.outputs[2], comb.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset, br.squash = 0.0, 1.0
    nt.links.new(comb.outputs[0], br.inputs["Vector"])
    br.inputs["Color1"].default_value = hexc(glass)
    br.inputs["Color2"].default_value = hexc(glass)
    br.inputs["Mortar"].default_value = hexc(wall)
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Mortar Size"].default_value = 0.45
    br.inputs["Mortar Smooth"].default_value = 0.0
    br.inputs["Brick Width"].default_value = win[0]
    br.inputs["Row Height"].default_value = win[1]
    # roof mask: |normal.z| > 0.5
    sn = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sn.inputs[0])
    ab = nt.nodes.new("ShaderNodeMath")
    ab.operation = "ABSOLUTE"
    nt.links.new(sn.outputs[2], ab.inputs[0])
    gt = nt.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    nt.links.new(ab.outputs[0], gt.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(gt.outputs[0], mix.inputs["Factor"])
    nt.links.new(br.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = hexc(roof)
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    return m


def link(ob, parent=None):
    col.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def box(name, size, loc, material, parent=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = link(bpy.data.objects.new(name, me), parent)
    ob.location = loc
    return ob


def sphere(name, r, loc, material, parent=None, scale=(1, 1, 1), seg=32):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = link(bpy.data.objects.new(name, me), parent)
    ob.location, ob.scale = loc, scale
    return ob


def cyl(name, r, depth, loc, material, parent=None, rot=(0, 0, 0), seg=32, smooth=True, r2=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth)
    if smooth:
        for f in bm.faces:
            f.smooth = len(f.verts) == 4
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = link(bpy.data.objects.new(name, me), parent)
    ob.location, ob.rotation_euler = loc, rot
    return ob


def empty(name, loc=(0, 0, 0), parent=None):
    ob = link(bpy.data.objects.new(name, None), parent)
    ob.location = loc
    return ob


def key(ob, path, f, val=None):
    if val is not None:
        setattr(ob, path, val)
    ob.keyframe_insert(path, frame=f)


def visible_only(obs, rng):
    """hide_render keyed so these objects exist only inside frame range rng."""
    for ob in obs:
        for f, h in ((1, True), (rng[0], False), (rng[1] + 1, True)):
            if f < 1:
                continue
            ob.hide_render = h
            ob.keyframe_insert("hide_render", frame=f)
        if rng[0] == 1:
            ob.hide_render = False
            ob.keyframe_insert("hide_render", frame=1)


def descendants(ob):
    out = [ob]
    for c in ob.children:
        out += descendants(c)
    return out


# ---------------------------------------------------------------- world: vertical sky gradient
world = bpy.data.worlds.new("Sky")
sc.world = world
nt = world.node_tree
nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(sep.outputs[2], ramp.inputs[0])
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, hexc("#fde2c4")
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.55, hexc("#3f8fe0")
e = ramp.color_ramp.elements.new(0.12)
e.color = hexc("#bfe0f7")
bg = nt.nodes.new("ShaderNodeBackground")
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(bg.outputs[0], out.inputs[0])

# ---------------------------------------------------------------- city
city = empty("City")
asphalt = mat("Asphalt", "#4a4c57")
sidewalk = mat("Sidewalk", "#c9c3b8")
lane = mat("Lane", "#f5d547")
box("Ground", (3000, 3000, 0.2), (0, 0, -0.1), asphalt, city)
walls = ["#e8d6b5", "#d98b6a", "#7fb7b0", "#b9b2c9", "#f0c27a", "#9fb5cc", "#e3a3a0"]
fac = [facade_mat(f"Facade_{i}", w) for i, w in enumerate(walls)]
tower_mat = facade_mat("Facade_Tower", "#efe7d8", glass="#7ab6e6", roof="#8a8494", win=(1.4, 2.0))
PITCH, ROAD = 34.0, 12.0
blocks = []
for ix in range(-9, 10):
    for iy in range(-9, 10):
        cx, cy = ix * PITCH, iy * PITCH
        foot = PITCH - ROAD
        box(f"Walk_{ix}_{iy}", (foot + 4, foot + 4, 0.25), (cx, cy, 0.125), sidewalk, city)
        if ix == 0 and iy == 0:
            continue
        d = math.hypot(ix, iy)
        h = random.uniform(18, 70) * (1.0 + 0.5 * math.exp(-d / 3))
        n = random.choice([1, 1, 2])
        for k in range(n):
            w = foot / n - (1.5 if n > 1 else 0)
            ox = (k - (n - 1) / 2) * (foot / n)
            hh = h * random.uniform(0.6, 1.0)
            b = box(f"Bld_{ix}_{iy}_{k}", (w, foot - 2, hh), (cx + ox, cy, hh / 2), random.choice(fac), city)
            blocks.append(b)
# lane dashes on the road in front of the tower
for i in range(-12, 13):
    box(f"Dash_{i}", (2.5, 0.25, 0.03), (i * 6, -PITCH / 2, 0.02), lane, city)
# hero tower
tower = box("Tower", (2 * HALF, 2 * HALF, H), (0, 0, H / 2), tower_mat, city)
trim = mat("Trim", "#c9b38a")
box("Crown", (2 * HALF + 0.6, 2 * HALF + 0.6, 1.2), (0, 0, H - 0.6), trim, city)
roof = mat("Roof", "#8d8797")
box("RoofDeck", (2 * HALF - 0.2, 2 * HALF - 0.2, 0.1), (0, 0, H + 0.05), roof, city)
parapet = mat("Parapet", "#d8cbb0")
for nm, sz, lc in (("ParN", (2 * HALF, 0.4, 0.9), (0, HALF - 0.2, H + 0.45)),
                   ("ParS", (2 * HALF, 0.4, 0.9), (0, -HALF + 0.2, H + 0.45)),
                   ("ParE", (0.4, 2 * HALF, 0.9), (HALF - 0.2, 0, H + 0.45)),
                   ("ParW", (0.4, 2 * HALF, 0.9), (-HALF + 0.2, 0, H + 0.45))):
    box(nm, sz, lc, parapet, city)
box("AC_Unit", (2.0, 1.4, 1.2), (3.0, 2.0, H + 0.7), mat("Metal", "#a7b0ba"), city)
cyl("Antenna", 0.15, 14, (-4, 3, H + 7), mat("Red", "#d94b3d"), city)

# ---------------------------------------------------------------- penny factory
copper = mat("Copper", "#c46a3a", 0.3)
copper_dark = mat("CopperDark", "#8f4524", 0.3)


def penny(name, scale=1.0):
    root = empty(name)
    root.scale = (scale,) * 3
    body = cyl(name + "_Body", PENNY_R, PENNY_T, (0, 0, 0), copper, root, seg=64)
    rim_me = bpy.data.meshes.new(name + "_Rim")
    bm = bmesh.new()
    for z in (PENNY_T / 2, -PENNY_T / 2):
        r = bmesh.ops.create_circle(bm, cap_ends=False, segments=64, radius=PENNY_R * 0.86)
        e = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[-64:])
        for v in [x for x in e["geom"] if isinstance(x, bmesh.types.BMVert)]:
            v.co *= 0.93
        for v in bm.verts[-128:]:
            v.co.z = z + (0.00008 if z > 0 else -0.00008)
        del r
    bm.to_mesh(rim_me)
    bm.free()
    rim_me.materials.append(copper_dark)
    link(bpy.data.objects.new(name + "_Ring", rim_me), root)
    # big "1" on both faces
    cu = bpy.data.curves.new(name + "_OneTxt", "FONT")
    cu.body, cu.align_x, cu.align_y = "1", "CENTER", "CENTER"
    cu.size, cu.extrude = PENNY_R * 1.1, 0.00012
    tmp = bpy.data.objects.new("tmp", cu)
    col.objects.link(tmp)
    bpy.context.view_layer.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    bpy.data.objects.remove(tmp)
    me.materials.clear()
    me.materials.append(copper_dark)
    for side, z, ry in (("F", PENNY_T / 2, 0), ("B", -PENNY_T / 2, math.pi)):
        o = link(bpy.data.objects.new(f"{name}_One{side}", me), root)
        o.location, o.rotation_euler = (0, 0, z), (0, ry, 0)
    return root, body


# ---------------------------------------------------------------- shot cameras
def camera(name, lens=24, fstop=None, focus=None):
    c = bpy.data.cameras.new(name)
    c.lens, c.sensor_fit, c.sensor_width = lens, "HORIZONTAL", 24
    c.clip_start, c.clip_end = 0.005, 4000
    if fstop:
        c.dof.use_dof, c.dof.aperture_fstop = True, fstop
        if focus is not None:
            c.dof.focus_object = focus
    ob = link(bpy.data.objects.new(name, c))
    return ob


def look(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def cam_key(ob, f, loc, target, roll=0.0):
    ob.location = loc
    look(ob, target)
    ob.rotation_euler.rotate_axis("Z", roll)
    ob.keyframe_insert("location", frame=f)
    ob.keyframe_insert("rotation_euler", frame=f)


# ================================================================= S1 rooftop
p1, p1body = penny("P1")
P1POS = {}
edge_y = -HALF                        # outer face of parapet
start = Vector((0.0, -HALF + 0.12, PARAPET_Z + PENNY_T / 2))
skin = mat("Skin", "#f2b48c")
nail = mat("Nail", "#f7d6c8")
finger = empty("Finger")
fseg = cyl("Finger_Seg", 0.0085, 0.085, (0, 0.0425, 0), skin, finger, rot=(math.pi / 2, 0, 0))
sphere("Finger_Tip", 0.0085, (0, 0, 0), skin, finger)
sphere("Finger_Knuckle", 0.0095, (0, 0.085, 0), skin, finger)
sphere("Finger_Nail", 0.0062, (0, 0.004, 0.0045), nail, finger, scale=(1, 1.1, 0.35))
fz = PARAPET_Z + 0.0095
for f in range(1, S1[1] + 1):
    # finger slides in 20-55, pushes 55-78, retracts after
    if f < 20:
        fy = start.y + 0.16
    elif f < 55:
        t = (f - 20) / 35
        fy = start.y + 0.16 - (0.16 - PENNY_R - 0.009) * (1 - (1 - t) ** 3)
    elif f < 80:
        t = (f - 55) / 25
        fy = start.y + PENNY_R + 0.009 - (0.12 + 0.02) * (t * t * (3 - 2 * t))
    else:
        t = min(1, (f - 80) / 25)
        fy = start.y + PENNY_R + 0.009 - 0.14 + 0.1 * t
    finger.location = (0.004, fy, fz)
    finger.rotation_euler = (math.radians(-12), 0, 0)
    key(finger, "location", f)
    key(finger, "rotation_euler", f)
    # penny
    tip_y = fy - 0.009
    py = min(start.y, tip_y - PENNY_R)
    loc, rot = Vector((0, py, start.z)), Euler((0, 0, 0))
    over = (edge_y - (py - PENNY_R))       # how far the penny overhangs (m)
    if f >= 76:
        tf = (f - 76) / FPS
        loc = Vector((0, edge_y - PENNY_R - 0.02 * tf * FPS / 10, start.z - 0.5 * 9.81 * tf * tf))
        rot = Euler((-min(math.pi * 0.5, tf * 9.0) - tf * 6, 0, tf * 2))
    elif over > PENNY_R * 0.7:
        rot = Euler((-min(0.6, (over - PENNY_R * 0.7) * 60), 0, 0))
    p1.location, p1.rotation_euler = loc, rot
    P1POS[f] = loc.copy()
    key(p1, "location", f)
    key(p1, "rotation_euler", f)
visible_only(descendants(p1) + descendants(finger), S1)
cam1 = camera("Cam_S1", lens=24, fstop=5.6, focus=p1)
for f in range(1, S1[1] + 1):
    t = f / S1[1]
    pp = P1POS[min(f, 94)]
    tgt = pp + Vector((0.0, -0.01, 0.004))
    cl = Vector((pp.x - 0.10 + 0.015 * t, -HALF - 0.07, max(pp.z, PARAPET_Z - 0.25) + 0.035))
    cam_key(cam1, f, cl, tgt)

# ================================================================= S2 "like a bullet"
p2, _ = penny("P2")
p2b = p2
cam2 = camera("Cam_S2", lens=28, fstop=4, focus=p2)
fy2 = -HALF - 6.0
for f in range(S2[0], S2[1] + 1):
    t = (f - S2[0]) / FPS
    z = 116 - (6 * t + 3.2 * t * t)          # starts fast, keeps accelerating
    jitter = 0.003 * math.sin(f * 2.3)
    p2.location = (jitter, fy2, z)
    p2.rotation_euler = (math.pi / 2, 0, t * 11)   # edge-down, spinning about the fall axis
    key(p2, "location", f)
    key(p2, "rotation_euler", f)
    cl = Vector((0.03 + 0.008 * math.sin(f * 0.7), fy2 - 0.12, z - 0.03))
    cam_key(cam2, f, cl, cl + (Vector((jitter, fy2, z - 0.006)) - cl) * 6)
visible_only(descendants(p2), S2)
# speed streaks along the fall path
streak = mat("Streak", "#ffffff")
for i in range(260):
    z = random.uniform(10, 118)
    x = random.uniform(-0.35, 0.35)
    y = fy2 + random.uniform(-0.1, 1.2)
    if abs(x) < 0.03 and abs(y - fy2) < 0.05:
        continue
    s = cyl(f"Streak_{i}", 0.0012, random.uniform(0.6, 1.6), (x, y, z), streak, seg=6, smooth=False)
    visible_only([s], S2)

# ================================================================= S3 flip & flutter
p3, _ = penny("P3")
cam3 = camera("Cam_S3", lens=35, fstop=4, focus=p3)
fy3 = -HALF - 2.6
for f in range(S3[0], S3[1] + 1):
    t = (f - S3[0]) / FPS
    vz = 11.0 + 5.0 * math.exp(-t * 1.2)            # slowing to terminal velocity
    z = 100 - (11.0 * t + 5.0 / 1.2 * (1 - math.exp(-t * 1.2)))
    x = 0.035 * math.sin(t * 3.1) + 0.015 * math.sin(t * 7.3)
    y = fy3 + 0.02 * math.cos(t * 2.4)
    p3.location = (x, y, z)
    p3.rotation_euler = (t * 7.5 + 0.6 * math.sin(t * 2), 0.5 * math.sin(t * 1.7), t * 1.3)
    key(p3, "location", f)
    key(p3, "rotation_euler", f)
    orbit = 0.25 * t
    cl = Vector((0.11 * math.sin(orbit) + 0.02, fy3 - 0.11 * math.cos(orbit), z - 0.02))
    cam_key(cam3, f, cl, (x * 0.6, y, z + 0.004))
visible_only(descendants(p3), S3)
air = mat("Air", "#eaf6ff")
for i in range(140):
    z = random.uniform(20, 102)
    x = random.uniform(-0.25, 0.3)
    y = fy3 + random.uniform(-0.05, 0.35)
    if abs(x) < 0.04 and abs(y - fy3) < 0.06:
        continue
    s = cyl(f"Air_{i}", 0.0006, random.uniform(0.15, 0.5), (x, y, z), air, seg=5, smooth=False)
    visible_only([s], S3)

# ================================================================= S4 wide drift (cheated scale)
p4, _ = penny("P4", scale=55)
cam4 = camera("Cam_S4", lens=40)
fy4 = -HALF - 4.5
for f in range(S4[0], S4[1] + 1):
    t = (f - S4[0]) / FPS
    z = 78 - 11.1 * t * 0.55          # slowed for readability (screen-time cheat)
    x = 1.4 * math.sin(t * 1.6)
    p4.location = (x, fy4 + 0.4 * math.sin(t * 1.1), z)
    p4.rotation_euler = (1.2 * math.sin(t * 1.6 + 1.2) + t * 0.7, 0.4 * math.sin(t * 1.3), t * 0.9)
    key(p4, "location", f)
    key(p4, "rotation_euler", f)
    cam_key(cam4, f, (26.0 - 1.5 * t, -HALF - 30, z + 3.0), (x * 0.5 + 2.0, fy4, z - 1.0))
visible_only(descendants(p4), S4)

# ================================================================= S5 street bonk
shirt = mat("Shirt", "#e2533c")
pants = mat("Pants", "#2f4c7c")
shoe = mat("Shoe", "#2b2b33")
hair = mat("Hair", "#5a3826")
white = mat("EyeWhite", "#ffffff")
black = mat("Pupil", "#151515")
mouth_m = mat("Mouth", "#7a2630")
GUY = Vector((0.0, -HALF - 5.0, 0.25))
guy = empty("Guy", GUY)
hips = empty("Guy_Hips", (0, 0, 0.0), guy)
for sx in (-1, 1):
    cyl(f"Leg_{sx}", 0.075, 0.82, (0.1 * sx, 0, 0.41), pants, hips)
    sphere(f"Shoe_{sx}", 0.08, (0.1 * sx, -0.05, 0.04), shoe, hips, scale=(1, 1.6, 0.6))
torso = sphere("Torso", 0.24, (0, 0, 1.12), shirt, hips, scale=(1.0, 0.72, 1.35))
neck = empty("Guy_Neck", (0, 0, 1.43), hips)
cyl("Neck", 0.055, 0.12, (0, 0, 0.03), skin, neck)
head = empty("Guy_Head", (0, 0, 0.1), neck)
sphere("Head", 0.17, (0, 0, 0.14), skin, head, scale=(1, 1, 1.08))
sphere("Hair", 0.178, (0, 0.025, 0.19), hair, head, scale=(1.02, 1.0, 0.9))
sphere("Nose", 0.03, (0, -0.17, 0.12), skin, head)
for sx in (-1, 1):
    sphere(f"Ear_{sx}", 0.035, (0.168 * sx, 0, 0.13), skin, head, scale=(0.5, 1, 1.2))
eyes, pupils = [], []
for sx in (-1, 1):
    ew = sphere(f"Eye_{sx}", 0.038, (0.062 * sx, -0.145, 0.18), white, head)
    eyes.append(ew)
    pupils.append(sphere(f"Pupil_{sx}", 0.018, (0.0, -0.032, 0.006), black, ew))
mouth = cyl("Mouth", 0.03, 0.02, (0, -0.158, 0.05), mouth_m, head, rot=(math.pi / 2 - 0.2, 0, 0), smooth=False)
arms = {}
for sx in (-1, 1):
    sh = empty(f"Shoulder_{sx}", (0.24 * sx, 0, 1.33), hips)
    cyl(f"Arm_{sx}", 0.055, 0.62, (0, 0, -0.31), shirt if sx else skin, sh)
    sphere(f"Hand_{sx}", 0.06, (0, 0, -0.64), skin, sh)
    sh.rotation_euler = (0, 0.12 * sx, 0)
    arms[sx] = sh
p5, _ = penny("P5", scale=6.0)
HIT = 618
head_top = GUY + Vector((0, 0, 1.43 + 0.1 + 0.33))
bounce_v = Vector((0.9, -0.6, 2.4))
land_z = 0.25 + PENNY_T * 2
for f in range(S5[0], S5[1] + 1):
    t = (f - HIT) / FPS
    if f <= HIT:
        loc = head_top + Vector((0, 0, -11.1 * t))
        rot = Euler((f * 0.35, 0.3, f * 0.11))
    else:
        loc = head_top + bounce_v * t + Vector((0, 0, -0.5 * 9.81 * t * t))
        rot = Euler((HIT * 0.35 + t * 25, 0.3 + t * 4, HIT * 0.11))
        if loc.z < land_z:                              # settle on the sidewalk
            tl = (2.4 + math.sqrt(2.4 ** 2 + 2 * 9.81 * (head_top.z - land_z))) / 9.81
            loc = head_top + bounce_v * tl + Vector((0, 0, -0.5 * 9.81 * tl * tl))
            loc.z = land_z
            loc.x += 0.25 * (1 - math.exp(-(t - tl) * 4))
            rot = Euler((0, 0, HIT * 0.11 + 2.0 * (1 - math.exp(-(t - tl) * 3))))
    p5.location, p5.rotation_euler = loc, rot
    key(p5, "location", f)
    key(p5, "rotation_euler", f)
visible_only(descendants(p5), S5)


def ease(a, b, f, f0, f1):
    t = max(0.0, min(1.0, (f - f0) / (f1 - f0)))
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t


for f in range(S5[0], S5[1] + 1, 1):
    # look up -> bonk squash -> dizzy wobble; right arm rubs head
    pitch = ease(0, -0.42, f, S5[0], S5[0] + 25)
    if f >= HIT:
        pitch = ease(-0.42, 0.28, f, HIT, HIT + 4)
        pitch = ease(pitch, 0.05, f, HIT + 6, HIT + 22)
    wob = 0.0 if f < HIT + 20 else 0.12 * math.sin((f - HIT) * 0.25) * math.exp(-(f - HIT - 20) / 120)
    neck.rotation_euler = (pitch, 0, wob)
    key(neck, "rotation_euler", f)
    sq = 1.0
    if HIT <= f <= HIT + 14:
        sq = 1 - 0.16 * math.sin(math.pi * (f - HIT) / 14) * math.exp(-(f - HIT) / 10)
    guy.scale = (1 + (1 - sq) * 0.6, 1 + (1 - sq) * 0.6, sq)
    key(guy, "scale", f)
    hips.rotation_euler = (0, wob * 0.5, 0)
    key(hips, "rotation_euler", f)
    blink = 1.0
    if HIT <= f < HIT + 40:
        blink = 0.12
    for pu in pupils:
        pu.scale = (1, 1, 1) if f < HIT else (1.15, 1.15, 1.15)
        key(pu, "scale", f)
    for ew in eyes:
        ew.scale = (1, 1, blink)
        key(ew, "scale", f)
    mouth.scale = (1, 1, 1) if f < HIT else (1.5, 1, ease(1.0, 1.8, f, HIT, HIT + 6))
    key(mouth, "scale", f)
    ra = arms[1]
    lift = ease(0, 1, f, HIT + 18, HIT + 34) * (1 - ease(0, 1, f, HIT + 110, HIT + 125))
    rub = 0.12 * math.sin((f - HIT) * 0.6) * lift
    ra.rotation_euler = (-0.25 * lift, 0.12 + 2.75 * lift + rub, 0)
    key(ra, "rotation_euler", f)
# dizzy stars
star_m = mat("Star", "#ffd23f")


def star(name, r=0.05):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = []
    for i in range(10):
        a = i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        vs.append(bm.verts.new((rr * math.sin(a), 0, rr * math.cos(a))))
    f = bm.faces.new(vs)
    bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in bm.verts[10:]:
        v.co.y += 0.02
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(star_m)
    return link(bpy.data.objects.new(name, me))


ring = empty("StarRing", parent=head)
ring.location = (0, 0, 0.38)
stars = []
for i in range(4):
    s = star(f"Star_{i}")
    s.parent = ring
    a = i * math.pi / 2
    s.location = (0.24 * math.cos(a), 0.24 * math.sin(a), 0.02 * math.sin(a * 2))
    stars.append(s)
for f in range(S5[0], S5[1] + 1):
    k = ease(0, 1, f, HIT + 2, HIT + 10)
    ring.rotation_euler = (0, 0, (f - HIT) * 0.18)
    ring.scale = (k, k, k) if k > 0 else (0.001,) * 3
    key(ring, "rotation_euler", f)
    key(ring, "scale", f)
    for s in stars:
        s.rotation_euler = (0, (f - HIT) * 0.3, -(f - HIT) * 0.18)
        key(s, "rotation_euler", f)
visible_only(stars, (HIT + 2, S5[1]))
cam5 = camera("Cam_S5", lens=26, fstop=5.6, focus=head)
for f in range(S5[0], S5[1] + 1, 2):
    t = (f - S5[0]) / (S5[1] - S5[0])
    shake = 0.0 if not (HIT <= f <= HIT + 12) else 0.012 * math.sin((f - HIT) * 3.1) * (1 - (f - HIT) / 12)
    zoom = ease(0, 1, f, HIT - 40, HIT + 10)
    cl = GUY + Vector((1.25 - 0.35 * zoom, -2.4 + 0.75 * zoom, 0.85 + shake))
    tgt = GUY + Vector((0, 0, 1.55 + 0.35 * (1 - zoom) + shake))
    cam_key(cam5, f, cl, tgt)

# ---------------------------------------------------------------- camera cuts
for c, (a, _) in ((cam1, S1), (cam2, S2), (cam3, S3), (cam4, S4), (cam5, S5)):
    m = sc.timeline_markers.new(c.name, frame=a)
    m.camera = c
sc.camera = cam1

# ---------------------------------------------------------------- toon look (blender-stylized-npr skill)
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
col.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(8), math.radians(-38))


def meshes(pred):
    return [o.name for o in sc.objects if o.type == "MESH" and pred(o)]


is_penny = lambda o: o.name.startswith(("P1_", "P2_", "P3_", "P4_", "P5_"))  # noqa: E731
is_city = lambda o: o.name in {x.name for x in descendants(city)}  # noqa: E731
is_fx = lambda o: o.name.startswith(("Streak_", "Air_"))  # noqa: E731
common = dict(bands=3, shadow_tint=(0.62, 0.58, 0.82), light="Sun", softness=0.03)
# toon_setup rebuilds its shared NPR_Toon group on every call and that drops the links made by
# earlier calls, so apply it ONCE to every mesh, then tune per-material inputs and add outlines here.
print(toon_setup.run(objects=meshes(lambda o: True), outline=0.0, rim=0.0, **common)["lighting"])
TUNE = {"Copper": dict(Specular=0.35, Rim=0.5), "CopperDark": dict(Specular=0.2),
        "Skin": dict(Rim=0.35), "Shirt": dict(Rim=0.35), "Pants": dict(Rim=0.3), "Hair": dict(Rim=0.3, Specular=0.25),
        "Star": dict(Rim=0.4), "EyeWhite": dict(Specular=0.3), "Pupil": dict(Specular=0.5)}
for mname, vals in TUNE.items():
    gn = bpy.data.materials[mname].node_tree.nodes.get("NPR_toon")
    for k, v in vals.items():
        gn.inputs[k].default_value = v


def add_outline(o, thickness, color=(0.05, 0.04, 0.06)):
    om = toon_setup._outline_material(color)
    if o.data.materials.find(om.name) < 0:
        o.data.materials.append(om)
    md = o.modifiers.new("NPR_Outline", "SOLIDIFY")
    md.thickness, md.offset = thickness, 1.0
    md.use_flip_normals, md.use_rim, md.use_quality_normals = True, False, True
    md.material_offset = o.data.materials.find(om.name)


for o in sc.objects:
    if o.type != "MESH" or is_city(o) or is_fx(o):
        continue
    if is_penny(o):
        if o.name.endswith("_Body"):
            add_outline(o, 0.0004)
    elif o.name.startswith("Finger"):
        add_outline(o, 0.0008)
    elif o.name.startswith(("Pupil", "Mouth")):
        continue
    else:
        add_outline(o, 0.008)
# streaks: semi-transparent white
for m in (streak, air):
    gn = m.node_tree.nodes.get("NPR_toon")
    tr = m.node_tree.nodes.new("ShaderNodeBsdfTransparent")
    mx = m.node_tree.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = 0.45
    outn = next(n for n in m.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
    m.node_tree.links.new(tr.outputs[0], mx.inputs[1])
    m.node_tree.links.new(gn.outputs[0], mx.inputs[2])
    m.node_tree.links.new(mx.outputs[0], outn.inputs["Surface"])

# ---------------------------------------------------------------- render settings
r = sc.render
r.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 14
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 1
sc.cycles.diffuse_bounces = sc.cycles.glossy_bounces = 0
sc.cycles.transmission_bounces = sc.cycles.volume_bounces = 0
sc.cycles.transparent_max_bounces = 8
r.use_motion_blur = True
r.motion_blur_shutter = 0.45
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.use_persistent_data = True
r.image_settings.file_format = "PNG"
r.filepath = os.path.join(HERE, "..", "frames", "f_####")
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "penny.blend"))
print("objects", len(sc.objects), "meshes", len(bpy.data.meshes), "saved")
