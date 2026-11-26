"""Blood Vessels - ~28 s vertical explainer built with bpy + the Mixamo character Remy.

Run:  /opt/bvenv/bin/python build/build_scene.py      (writes build/vessels.blend)
Assets (not committed, Mixamo licence): assets/Battlecry.fbx (Remy + "Standing Taunt Battlecry").
Earth texture: build/earth_texture.py (Natural Earth, public domain).

Shots (30 fps, 840 frames)
  S1   1-120  Remy on grass; his blood vessels glow through his skin (x-ray)
  S2 121-255  the vessel network slides out and stands beside him
  S3 256-341  Remy reacts (Battlecry animation)
  S4 342-450  vessel figure collapses into a tangle; one strand shoots out
  S5 451-600  the line races across the land (counter in captions)
  S6 601-840  globe: the line wraps the Earth ~2.5 times
"""
import math
import os
import random

import bpy  # noqa: I001  (bpy first: the pip module registers bmesh/mathutils)
import bmesh
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
random.seed(11)
FPS = 30
S1, S2, S3, S4, S5, S6 = (1, 120), (121, 255), (256, 341), (342, 450), (451, 600), (601, 840)
P = "mixamorig:"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, S6[1]
col = sc.collection


def srgb(*c):
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def hexc(h):
    h = h.lstrip("#")
    return srgb(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))


def ease(a, b, f, f0, f1):
    t = max(0.0, min(1.0, (f - f0) / (f1 - f0)))
    t = t * t * (3 - 2 * t)
    return a + (b - a) * t


def link(ob, parent=None):
    col.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def principled(name, color, rough=0.5, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = hexc(color) if isinstance(color, str) else color
    b.inputs["Roughness"].default_value = rough
    if emission:
        b.inputs["Emission Color"].default_value = hexc(emission)
        b.inputs["Emission Strength"].default_value = strength
    return m, b


def key(ob, path, f, val=None):
    if val is not None:
        setattr(ob, path, val)
    ob.keyframe_insert(path, frame=f)


# ================================================================ world + ground
world = bpy.data.worlds.new("Sky")
sc.world = world
nt = world.node_tree
nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord")
sep = nt.nodes.new("ShaderNodeSeparateXYZ")
nt.links.new(tc.outputs["Generated"], sep.inputs[0])
ramp = nt.nodes.new("ShaderNodeValToRGB")
nt.links.new(sep.outputs[2], ramp.inputs[0])
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.0, hexc("#d9ecfb")
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.45, hexc("#2f86e8")
bg = nt.nodes.new("ShaderNodeBackground")
bg.inputs["Strength"].default_value = 1.0
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
nt.links.new(bg.outputs[0], nt.nodes.new("ShaderNodeOutputWorld").inputs[0])

sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy, sun.data.angle = 4.0, math.radians(2.5)
sun.rotation_euler = (math.radians(42), math.radians(-18), math.radians(-30))

gm = bpy.data.materials.new("Grass")
g = gm.node_tree
gb = next(n for n in g.nodes if n.type == "BSDF_PRINCIPLED")
gco = g.nodes.new("ShaderNodeTexCoord")
gnz = g.nodes.new("ShaderNodeTexNoise")
gnz.inputs["Scale"].default_value, gnz.inputs["Detail"].default_value = 0.35, 8
g.links.new(gco.outputs["Object"], gnz.inputs["Vector"])
gnz2 = g.nodes.new("ShaderNodeTexNoise")
gnz2.inputs["Scale"].default_value, gnz2.inputs["Detail"].default_value = 18, 4
g.links.new(gco.outputs["Object"], gnz2.inputs["Vector"])
gr = g.nodes.new("ShaderNodeValToRGB")
gr.color_ramp.elements[0].color, gr.color_ramp.elements[1].color = hexc("#3f7d2a"), hexc("#7fb04a")
gr.color_ramp.elements[0].position, gr.color_ramp.elements[1].position = 0.35, 0.7
gmix = g.nodes.new("ShaderNodeMath")
gmix.operation = "MULTIPLY_ADD"
gmix.inputs[1].default_value, gmix.inputs[2].default_value = 0.35, 0.0
g.links.new(gnz2.outputs["Fac"], gmix.inputs[0])
gadd = g.nodes.new("ShaderNodeMath")
gadd.operation = "ADD"
g.links.new(gnz.outputs["Fac"], gadd.inputs[0])
g.links.new(gmix.outputs[0], gadd.inputs[1])
gsub = g.nodes.new("ShaderNodeMath")
gsub.operation = "SUBTRACT"
gsub.inputs[1].default_value = 0.17
g.links.new(gadd.outputs[0], gsub.inputs[0])
g.links.new(gsub.outputs[0], gr.inputs[0])
g.links.new(gr.outputs["Color"], gb.inputs["Base Color"])
gb.inputs["Roughness"].default_value = 0.9
gbump = g.nodes.new("ShaderNodeBump")
gbump.inputs["Strength"].default_value = 0.25
g.links.new(gnz2.outputs["Fac"], gbump.inputs["Height"])
g.links.new(gbump.outputs["Normal"], gb.inputs["Normal"])
gme = bpy.data.meshes.new("Ground")
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4500)
bm.to_mesh(gme)
bm.free()
gme.materials.append(gm)
ground = link(bpy.data.objects.new("Ground", gme))
ground.visible_shadow = False

# ================================================================ Remy
bpy.ops.import_scene.fbx(filepath=os.path.join(ASSETS, "Battlecry.fbx"))
arm = next(o for o in sc.objects if o.type == "ARMATURE")
remy_meshes = [o for o in sc.objects if o.type == "MESH" and o.parent == arm]
body = next(o for o in remy_meshes if o.name.startswith("Body"))
root = link(bpy.data.objects.new("RemyRoot", None))
arm.parent = root
battle = arm.animation_data.action
arm.animation_data.action = None
pb = {b.name: b for b in arm.pose.bones}
for b in arm.pose.bones:
    b.rotation_mode = "QUATERNION"
    b.rotation_quaternion = (1, 0, 0, 0)
    b.location = (0, 0, 0)
bpy.context.view_layer.update()


def bone_world(name, tail=False):
    b = pb[P + name]
    return arm.matrix_world @ (b.tail if tail else b.head)


def rotate_bone_world(name, axis_world, angle):
    """Rotate a pose bone about a world axis through its head (keeps children attached)."""
    b = pb[P + name]
    aw = arm.matrix_world.to_3x3().normalized()
    axis = (aw.inverted() @ Vector(axis_world)).normalized()
    R = Matrix.Rotation(angle, 4, axis)
    h = b.head.copy()
    b.matrix = Matrix.Translation(h) @ R @ Matrix.Translation(-h) @ b.matrix
    bpy.context.view_layer.update()


def evaluated_world_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    vs = [ob.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return vs, polys


# normalise height to 1.80 m, feet on the ground (rest pose)
vs, _ = evaluated_world_verts(body)
zmin, zmax = min(v.z for v in vs), max(v.z for v in vs)
s = 1.80 / (zmax - zmin)
root.scale = (s, s, s)
bpy.context.view_layer.update()
vs, _ = evaluated_world_verts(body)
root.location.z -= min(v.z for v in vs)
bpy.context.view_layer.update()
print("Remy height scale", s)

# ---------- A-pose (arms ~62 deg down from the T-pose) and keyed idle
DOWN = Vector((0, 0, -1))


def arm_down(side, sign):
    sh = bone_world(f"{side}Arm")
    el = bone_world(f"{side}ForeArm")
    d = (el - sh).normalized()
    target = (d * math.cos(math.radians(62)) + DOWN * math.sin(math.radians(62))).normalized()
    axis = d.cross(target).normalized()
    rotate_bone_world(f"{side}Arm", axis, d.angle(target))
    # slight elbow bend, forearm swings forward (-Y is his front)
    el = bone_world(f"{side}ForeArm")
    wr = bone_world(f"{side}Hand")
    f = (wr - el).normalized()
    ax2 = f.cross(Vector((0, -1, 0))).normalized()
    rotate_bone_world(f"{side}ForeArm", ax2, math.radians(12))


arm_down("Left", 1)
arm_down("Right", -1)
APOSE = {n: b.rotation_quaternion.copy() for n, b in pb.items()}
IDLE_BONES = ["Spine1", "Spine2", "Neck", "Head", "LeftArm", "RightArm"]
for f in list(range(1, S3[0], 3)) + [S3[0] - 1]:
    for n in IDLE_BONES:
        pb[P + n].rotation_quaternion = APOSE[P + n]
    bpy.context.view_layer.update()
    br = math.sin(f / FPS * 2 * math.pi / 3.6)
    rotate_bone_world("Spine1", (1, 0, 0), -0.012 * br)
    rotate_bone_world("Spine2", (1, 0, 0), -0.015 * br)
    look = ease(0, 1, f, 175, 205)                       # turns to look at the vessel figure
    surprise = ease(0, 1, f, 205, 215) * (1 - ease(0, 1, f, 225, 250))
    rotate_bone_world("Neck", (0, 0, 1), 0.25 * look)
    rotate_bone_world("Head", (0, 0, 1), 0.35 * look + 0.04 * math.sin(f / 23))
    rotate_bone_world("Head", (1, 0, 0), -0.06 * surprise)
    rotate_bone_world("LeftArm", (0, 1, 0), 0.03 * br)
    rotate_bone_world("RightArm", (0, 1, 0), -0.03 * br)
    for n in IDLE_BONES:
        pb[P + n].keyframe_insert("rotation_quaternion", frame=f)
for n, b in pb.items():
    if n.replace(P, "") not in IDLE_BONES:
        b.keyframe_insert("rotation_quaternion", frame=1)
    b.keyframe_insert("location", frame=1)
apose_act = arm.animation_data.action
apose_act.name = "Remy_Apose_Idle"
arm.animation_data.action = None
ad = arm.animation_data
t1 = ad.nla_tracks.new()
t1.name = "Idle"
st1 = t1.strips.new("Idle", 1, apose_act)
st1.extrapolation = "HOLD"
t2 = ad.nla_tracks.new()
t2.name = "Battlecry"
st2 = t2.strips.new("Battlecry", S3[0], battle)
st2.extrapolation = "HOLD_FORWARD"
st2.blend_type = "REPLACE"
sc.frame_set(1)
bpy.context.view_layer.update()

# ================================================================ x-ray materials on Remy
XR_KEYS = [(1, 0.0), (55, 0.0), (95, 0.78), (S2[0] + 55, 0.78), (S2[0] + 105, 0.0)]
for m in {s.material for o in remy_meshes for s in o.material_slots if s.material}:
    t = m.node_tree
    out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    tr = t.nodes.new("ShaderNodeBsdfTransparent")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value, em.inputs["Strength"].default_value = hexc("#bfe4ff"), 0.35
    lw = t.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    ghost = t.nodes.new("ShaderNodeMixShader")       # transparent body with a pale rim
    t.links.new(lw.outputs["Facing"], ghost.inputs[0])
    t.links.new(tr.outputs[0], ghost.inputs[1])
    t.links.new(em.outputs[0], ghost.inputs[2])
    mix = t.nodes.new("ShaderNodeMixShader")
    v = t.nodes.new("ShaderNodeValue")
    v.name = "XRAY"
    t.links.new(v.outputs[0], mix.inputs[0])
    t.links.new(src, mix.inputs[1])
    t.links.new(ghost.outputs[0], mix.inputs[2])
    t.links.new(mix.outputs[0], out.inputs["Surface"])
    for f, val in XR_KEYS:
        v.outputs[0].default_value = val
        v.outputs[0].keyframe_insert("default_value", frame=f)

# ================================================================ vessel network (grown inside the body)
sc.frame_set(1)
bpy.context.view_layer.update()
bverts, bpolys = evaluated_world_verts(body)
bvh = BVHTree.FromPolygons(bverts, bpolys)
CB = Vector((0.0, 0.0, 1.0))                     # vessel object origin (body centre, then moved)


def inside_fix(p, depth):
    loc, nrm, _, dist = bvh.find_nearest(p)
    if loc is None:
        return p
    out = (p - loc).dot(nrm) > 0
    if out or dist < depth * 0.5:
        return loc - nrm * depth
    return p


def shell(p, depth):
    loc, nrm, _, _ = bvh.find_nearest(p)
    return loc - nrm * depth if loc is not None else p


def chain_pts(names, step=0.015):
    pts = [bone_world(n) for n in names]
    out = []
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b - a).length / step))
        out += [a.lerp(b, i / n) for i in range(n)]
    out.append(pts[-1])
    return out


CHAINS = [["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head"]]
for sd in ("Left", "Right"):
    CHAINS.append(["Spine2", f"{sd}Shoulder", f"{sd}Arm", f"{sd}ForeArm", f"{sd}Hand", f"{sd}HandMiddle1",
                   f"{sd}HandMiddle2", f"{sd}HandMiddle3"])
    CHAINS.append(["Hips", f"{sd}UpLeg", f"{sd}Leg", f"{sd}Foot", f"{sd}ToeBase"])
splines = []          # list of (points[], radii[])
trunk_pts = []
for ch in CHAINS:
    base = chain_pts(ch)
    for off, rad in ((0.012, 0.0034), (-0.012, 0.0029)):
        pts, rads = [], []
        for i, p in enumerate(base):
            q = p + Vector((off, off * 0.5, 0)) + Vector([random.uniform(-0.002, 0.002) for _ in range(3)])
            q = inside_fix(q, 0.02)
            pts.append(q)
            rads.append(rad * (1.6 if ch[0] == "Hips" and ch[1] == "Spine" else 1.0))
        splines.append((pts, rads))
        trunk_pts += pts


def rnd_unit():
    v = Vector([random.gauss(0, 1) for _ in range(3)])
    return v.normalized()


def grow(p, d, n, r0, depth_lvl):
    pts, rads = [p], [r0]
    for i in range(n):
        d = (d + rnd_unit() * 0.55).normalized()
        q = pts[-1] + d * random.uniform(0.012, 0.02)
        q = shell(q, random.uniform(0.004, 0.012)) if i > 1 else inside_fix(q, 0.015)
        d = (q - pts[-1]).normalized() if (q - pts[-1]).length > 1e-5 else d
        pts.append(q)
        rads.append(max(0.0005, r0 * (1 - (i + 1) / (n + 1)) ** 0.8))
        if depth_lvl < 2 and random.random() < 0.12:
            grow(q, (d + rnd_unit()).normalized(), int(n * 0.55), rads[-1] * 0.8, depth_lvl + 1)
    splines.append((pts, rads))


for k in range(1150):
    p = random.choice(trunk_pts)
    grow(p, rnd_unit(), random.randint(8, 24), random.uniform(0.0011, 0.0019), 0)
cu = bpy.data.curves.new("Vessels", "CURVE")
cu.dimensions = "3D"
cu.bevel_depth, cu.bevel_resolution = 1.0, 1
cu.use_fill_caps = True
npts = 0
for pts, rads in splines:
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for pt, p, r in zip(sp.points, pts, rads):
        q = p - CB
        pt.co = (q.x, q.y, q.z, 1.0)
        pt.radius = r
    npts += len(pts)
vmat, vb = principled("Blood", "#b5121b", rough=0.35, emission="#ff2a2a", strength=0.15)
vb.inputs["Subsurface Weight"].default_value = 0.2
vb.inputs["Coat Weight"].default_value = 0.4
vfade = vmat.node_tree.nodes.new("ShaderNodeValue")
vfade.name = "VFADE"
vtr = vmat.node_tree.nodes.new("ShaderNodeBsdfTransparent")
vmix = vmat.node_tree.nodes.new("ShaderNodeMixShader")
vout = next(n for n in vmat.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
vmat.node_tree.links.new(vfade.outputs[0], vmix.inputs[0])
vmat.node_tree.links.new(vtr.outputs[0], vmix.inputs[1])
vmat.node_tree.links.new(vb.outputs[0], vmix.inputs[2])
vmat.node_tree.links.new(vmix.outputs[0], vout.inputs["Surface"])
for f, val in ((1, 0.0), (60, 0.0), (95, 1.0)):
    vfade.outputs[0].default_value = val
    vfade.outputs[0].keyframe_insert("default_value", frame=f)
cu.materials.append(vmat)
vessels = link(bpy.data.objects.new("Vessels", cu))
vessels.location = CB
print("vessel splines", len(splines), "points", npts)

# tangle shape key: every strand becomes a random walk inside a ball
vessels.shape_key_add(name="Basis", from_mix=False)
tk = vessels.shape_key_add(name="Tangle", from_mix=False)
R = 0.26
i = 0
for pts, _ in splines:
    c = rnd_unit() * random.uniform(0, R * 0.8)
    d = rnd_unit()
    for j in range(len(pts)):
        if j:
            d = (d + rnd_unit() * 0.35).normalized()
            c = c + d * 0.016
            if c.length > R:
                c = c.normalized() * (2 * R - c.length)
                d = (d - 2 * d.dot(c.normalized()) * c.normalized()).normalized()
        tk.data[i].co = c
        i += 1
VX = Vector((0.95, 0.0, 1.0))                     # where the vessel figure stands
for f, loc in ((1, CB), (S2[0] + 30, CB), (S2[0] + 95, VX)):
    key(vessels, "location", f, loc)
for f in range(S2[0] + 30, S2[0] + 96, 3):        # little wobble while it slides out
    k = ease(0, 1, f, S2[0] + 30, S2[0] + 95)
    vessels.rotation_euler = (0, 0, 0.25 * math.sin(k * math.pi))
    key(vessels, "rotation_euler", f)
for f, v in ((1, 0.0), (S4[0] + 3, 0.0), (S4[0] + 53, 1.0)):
    tk.value = v
    tk.keyframe_insert("value", frame=f)
for f, sc_ in ((1, 1.0), (S4[0] + 55, 1.0), (S4[1], 0.12), (S4[1] + 1, 0.0)):
    key(vessels, "scale", f, (sc_,) * 3)
for f in range(S4[0], S4[1] + 1, 2):              # tangle spins as it unravels
    vessels.rotation_euler = (0.0, 0.0, ease(0, 1, f, S4[0], S4[1]) * 6.0)
    key(vessels, "rotation_euler", f)

# ================================================================ the single long line (ground run)
line_pts = []
for j in range(25):                                # arc from the tangle down to the ground
    t = j / 24
    line_pts.append(Vector((VX.x + 1.1 * t, 0.0, VX.z * (1 - t) ** 2 + 0.025 * t)))
x = VX.x + 1.1
while x < 3600:
    x += 1.5
    line_pts.append(Vector((x, 5.0 * math.sin((x - 2) / 140) * min(1, (x - 2) / 60), 0.025)))
lengths = [0.0]
for a, b in zip(line_pts, line_pts[1:]):
    lengths.append(lengths[-1] + (b - a).length)
LTOT = lengths[-1]
lc = bpy.data.curves.new("Line", "CURVE")
lc.dimensions = "3D"
lc.bevel_depth, lc.bevel_resolution = 0.03, 3
lc.use_fill_caps = True
lc.bevel_factor_mapping_end = "SPLINE"
sp = lc.splines.new("POLY")
sp.points.add(len(line_pts) - 1)
for pt, p in zip(sp.points, line_pts):
    pt.co = (p.x, p.y, p.z, 1.0)
lmat, _ = principled("LineGlow", "#c8101a", 0.3, emission="#ff2030", strength=1.5)
lc.materials.append(lmat)
line = link(bpy.data.objects.new("Line", lc))


def arc_point(s_):
    s_ = max(0.0, min(LTOT, s_))
    lo, hi = 0, len(lengths) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if lengths[mid] < s_:
            lo = mid
        else:
            hi = mid
    seg = lengths[hi] - lengths[lo]
    return line_pts[lo].lerp(line_pts[hi], 0 if seg == 0 else (s_ - lengths[lo]) / seg)


def tip_s(f):
    if f < S4[0] + 55:
        return 0.0
    if f <= S4[1]:
        return 25.0 * ((f - S4[0] - 55) / (S4[1] - S4[0] - 55)) ** 2
    return 25.0 + 3400.0 * ((f - S4[1]) / (S5[1] - S4[1])) ** 2.4


for f in range(1, S5[1] + 2):
    lc.bevel_factor_end = tip_s(f) / LTOT
    lc.keyframe_insert("bevel_factor_end", frame=f)
for f, h in ((1, True), (S4[0] + 54, False), (S5[1] + 1, True)):
    line.hide_render = h
    line.keyframe_insert("hide_render", frame=f)
# vessels are behind the camera from S5 on; leaving them in makes Cycles stall at frame 451
for f, h in ((1, False), (S5[0], True)):
    vessels.hide_render = h
    vessels.keyframe_insert("hide_render", frame=f)

# trees along the run (linked duplicates)
leaf, _ = principled("Leaf", "#2f6b2a", 0.8)
leaf2, _ = principled("Leaf2", "#4c8a2e", 0.8)
bark, _ = principled("Bark", "#5b3d25", 0.9)


def tree_mesh(name, kind):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.12, radius2=0.09, depth=1.2,
                          matrix=Matrix.Translation((0, 0, 0.6)))
    nt_ = len(bm.faces)
    if kind == 0:
        for z, r in ((1.6, 1.4), (2.6, 1.1), (3.5, 0.7)):
            bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r, radius2=0.0, depth=1.6,
                                  matrix=Matrix.Translation((0, 0, z)))
    else:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.3, matrix=Matrix.Translation((0, 0, 2.3)))
    for k, fc in enumerate(bm.faces):
        fc.material_index = 0 if k < nt_ else 1
        fc.smooth = kind == 1
    bm.to_mesh(me)
    bm.free()
    me.materials.append(bark)
    me.materials.append(leaf if kind == 0 else leaf2)
    return me


tmeshes = [tree_mesh("Pine", 0), tree_mesh("Oak", 1)]
for k in range(1400):
    xx = random.uniform(12, 3500)
    side = random.choice((-1, 1))
    yy = 5.0 * math.sin((xx - 2) / 140) + side * random.uniform(5, 70) ** 1.0
    t = link(bpy.data.objects.new(f"Tree_{k}", random.choice(tmeshes)))
    t.location = (xx, yy, 0)
    sz = random.uniform(0.8, 1.6)
    t.scale = (sz, sz, sz * random.uniform(0.9, 1.3))
    t.rotation_euler.z = random.uniform(0, 6.28)

# ================================================================ globe (high above everything)
G = Vector((0.0, 0.0, 20000.0))
RE = 10.0
globe_rig = link(bpy.data.objects.new("GlobeRig", None))
globe_rig.location = G
globe_rig.rotation_euler = (math.radians(18), 0, 0)
gmat = bpy.data.materials.new("Earth")
t = gmat.node_tree
eb = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
img = bpy.data.images.load(os.path.join(ASSETS, "textures", "earth.png"))
img.pack()
tex = t.nodes.new("ShaderNodeTexImage")
tex.image = img
mimg = bpy.data.images.load(os.path.join(ASSETS, "textures", "landmask.png"))
mimg.pack()
mimg.colorspace_settings.name = "Non-Color"
mtex = t.nodes.new("ShaderNodeTexImage")
mtex.image = mimg
uvn = t.nodes.new("ShaderNodeUVMap")
t.links.new(uvn.outputs[0], tex.inputs[0])
t.links.new(uvn.outputs[0], mtex.inputs[0])
t.links.new(tex.outputs["Color"], eb.inputs["Base Color"])
rr = t.nodes.new("ShaderNodeMapRange")                  # oceans glossy, land rough
rr.inputs[3].default_value, rr.inputs[4].default_value = 0.25, 0.85
t.links.new(mtex.outputs["Color"], rr.inputs[0])
t.links.new(rr.outputs[0], eb.inputs["Roughness"])
me = bpy.data.meshes.new("Earth")
bm = bmesh.new()
bm.loops.layers.uv.new("UVMap")
bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=64, radius=RE, calc_uvs=True)
for fc in bm.faces:
    fc.smooth = True
bm.to_mesh(me)
bm.free()
me.materials.append(gmat)
earth = link(bpy.data.objects.new("Earth", me), globe_rig)
# clouds
cmat = bpy.data.materials.new("Clouds")
t = cmat.node_tree
cb_ = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
cnz = t.nodes.new("ShaderNodeTexNoise")
cnz.inputs["Scale"].default_value, cnz.inputs["Detail"].default_value = 2.2, 10
cnz.inputs["Roughness"].default_value = 0.62
ccr = t.nodes.new("ShaderNodeMapRange")
ccr.inputs[1].default_value, ccr.inputs[2].default_value = 0.6, 0.78
ccr.inputs[4].default_value = 0.8
t.links.new(cnz.outputs["Fac"], ccr.inputs[0])
cb_.inputs["Base Color"].default_value = (1, 1, 1, 1)
t.links.new(ccr.outputs[0], cb_.inputs["Alpha"])
cme = bpy.data.meshes.new("Clouds")
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=RE * 1.012)
for fc in bm.faces:
    fc.smooth = True
bm.to_mesh(cme)
bm.free()
cme.materials.append(cmat)
clouds = link(bpy.data.objects.new("Clouds", cme), globe_rig)
# atmosphere rim
amat = bpy.data.materials.new("Atmo")
t = amat.node_tree
t.nodes.clear()
aout = t.nodes.new("ShaderNodeOutputMaterial")
alw = t.nodes.new("ShaderNodeLayerWeight")
alw.inputs["Blend"].default_value = 0.25
apow = t.nodes.new("ShaderNodeMath")
apow.operation = "POWER"
apow.inputs[1].default_value = 2.5
t.links.new(alw.outputs["Facing"], apow.inputs[0])
aem = t.nodes.new("ShaderNodeEmission")
aem.inputs["Color"].default_value, aem.inputs["Strength"].default_value = hexc("#6fb6ff"), 2.5
atr = t.nodes.new("ShaderNodeBsdfTransparent")
amx = t.nodes.new("ShaderNodeMixShader")
t.links.new(apow.outputs[0], amx.inputs[0])
t.links.new(atr.outputs[0], amx.inputs[1])
t.links.new(aem.outputs[0], amx.inputs[2])
t.links.new(amx.outputs[0], aout.inputs["Surface"])
ame = bpy.data.meshes.new("Atmo")
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=96, v_segments=48, radius=RE * 1.045)
for fc in bm.faces:
    fc.smooth = True
bm.to_mesh(ame)
bm.free()
ame.materials.append(amat)
atmo = link(bpy.data.objects.new("Atmo", ame), globe_rig)
atmo.visible_shadow = False
# star dome
smat = bpy.data.materials.new("Stars")
t = smat.node_tree
t.nodes.clear()
sout = t.nodes.new("ShaderNodeOutputMaterial")
sco = t.nodes.new("ShaderNodeTexCoord")
vor = t.nodes.new("ShaderNodeTexVoronoi")
vor.inputs["Scale"].default_value = 220
t.links.new(sco.outputs["Object"], vor.inputs["Vector"])
smr = t.nodes.new("ShaderNodeMapRange")
smr.inputs[1].default_value, smr.inputs[2].default_value = 0.06, 0.0
t.links.new(vor.outputs["Distance"], smr.inputs[0])
spw = t.nodes.new("ShaderNodeMath")
spw.operation = "POWER"
spw.inputs[1].default_value = 6
t.links.new(smr.outputs[0], spw.inputs[0])
sem = t.nodes.new("ShaderNodeEmission")
sem.inputs["Strength"].default_value = 3.0
t.links.new(spw.outputs[0], sem.inputs["Strength"])
sbg = t.nodes.new("ShaderNodeEmission")
sbg.inputs["Color"].default_value, sbg.inputs["Strength"].default_value = hexc("#03050d"), 1.0
sadd = t.nodes.new("ShaderNodeAddShader")
t.links.new(sem.outputs[0], sadd.inputs[0])
t.links.new(sbg.outputs[0], sadd.inputs[1])
t.links.new(sadd.outputs[0], sout.inputs["Surface"])
sme = bpy.data.meshes.new("Stars")
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=600)
bm.to_mesh(sme)
bm.free()
sme.materials.append(smat)
stars = link(bpy.data.objects.new("Stars", sme))
stars.location = G
stars.visible_shadow = False
# the wrapping line: 2.5 great-circle loops whose plane slowly precesses
wrap_pts = []
NW = 1400
tilt = math.radians(62)
for j in range(NW + 1):
    tt = j / NW
    th = tt * 2.5 * 2 * math.pi
    phi = tt * 1.1
    n = Vector((math.sin(tilt) * math.cos(phi), math.sin(tilt) * math.sin(phi), math.cos(tilt)))
    u = n.cross(Vector((0, 0, 1))).normalized()
    v = n.cross(u).normalized()
    wrap_pts.append((u * math.cos(th - 1.9) + v * math.sin(th - 1.9)) * RE * 1.006)
wc = bpy.data.curves.new("Wrap", "CURVE")
wc.dimensions = "3D"
wc.bevel_depth, wc.bevel_resolution = 0.045, 2
wc.use_fill_caps = True
wc.bevel_factor_mapping_end = "SPLINE"
sp = wc.splines.new("POLY")
sp.points.add(len(wrap_pts) - 1)
for pt, p in zip(sp.points, wrap_pts):
    pt.co = (p.x, p.y, p.z, 1.0)
wmat, wb = principled("WrapLine", "#d0121e", 0.3, emission="#ff1f2a", strength=2.5)
wc.materials.append(wmat)
wrap = link(bpy.data.objects.new("Wrap", wc), globe_rig)
W0, W1 = S6[0] + 40, S6[0] + 200
for f in range(S6[0], S6[1] + 1, 2):
    k = max(0.0, min(1.0, (f - W0) / (W1 - W0)))
    wc.bevel_factor_end = 0.002 + 0.998 * (k * k * (3 - 2 * k) * 0.25 + k * 0.75)
    wc.keyframe_insert("bevel_factor_end", frame=f)
    globe_rig.rotation_euler = (math.radians(18), 0, -0.55 + 0.75 * (f - S6[0]) / (S6[1] - S6[0]))
    globe_rig.keyframe_insert("rotation_euler", frame=f)
    clouds.rotation_euler = (0, 0, 0.12 * (f - S6[0]) / (S6[1] - S6[0]))
    clouds.keyframe_insert("rotation_euler", frame=f)

# ================================================================ cameras + cuts
def camera(name, lens=35, fstop=None, focus=None):
    c = bpy.data.cameras.new(name)
    c.lens, c.sensor_fit, c.sensor_width = lens, "VERTICAL", 36
    c.sensor_height = 36
    c.clip_start, c.clip_end = 0.01, 5000
    if fstop:
        c.dof.use_dof, c.dof.aperture_fstop = True, fstop
        if focus is not None:
            c.dof.focus_object = focus
    return link(bpy.data.objects.new(name, c))


def look(ob, loc, target):
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def cam_key(ob, f, loc, target):
    look(ob, loc, target)
    ob.keyframe_insert("location", frame=f)
    ob.keyframe_insert("rotation_euler", frame=f)


focus_body = link(bpy.data.objects.new("FocusBody", None))
focus_body.location = (0, 0, 1.2)
c1 = camera("Cam_S1", 40, 2.8, focus_body)
for f in range(S1[0], S1[1] + 1, 4):
    k = (f - S1[0]) / (S1[1] - S1[0])
    cam_key(c1, f, (0.35 - 0.15 * k, -3.6 + 0.7 * k, 1.05 + 0.05 * k), (0.0, 0.0, 1.0 + 0.05 * k))
focus_mid = link(bpy.data.objects.new("FocusMid", None))
focus_mid.location = (0.45, 0, 1.0)
c2 = camera("Cam_S2", 32, 4, focus_mid)
for f in range(S2[0], S2[1] + 1, 4):
    k = (f - S2[0]) / (S2[1] - S2[0])
    cam_key(c2, f, (0.25 + 0.3 * k, -4.3 + 0.3 * k, 1.0), (0.2 + 0.3 * ease(0, 1, f, S2[0] + 25, S2[0] + 100), 0, 0.95))
c3 = camera("Cam_S3", 30, 4, focus_mid)
for f in range(S3[0], S3[1] + 1, 4):
    k = (f - S3[0]) / (S3[1] - S3[0])
    cam_key(c3, f, (-1.2 + 0.25 * k, -3.2 + 0.25 * k, 0.75), (0.35, 0, 0.95))
c4 = camera("Cam_S4", 32, 5.6, vessels)
for f in range(S4[0], S4[1] + 1, 2):
    tip = arc_point(tip_s(f))
    k = ease(0, 1, f, S4[0] + 55, S4[1])
    tgt = VX.lerp(tip + Vector((0, 0, 0.2)), k)
    cam_key(c4, f, (0.15 + 1.6 * k, -2.6 - 1.2 * k, 1.1 - 0.35 * k), tgt)
c5 = camera("Cam_S5", 28)
for f in range(S5[0], S5[1] + 1):
    s_ = tip_s(f)
    spd = tip_s(f + 1) - s_
    tip = arc_point(s_)
    back = arc_point(s_ - 2.2 - spd * 2.5)
    h = 0.35 + spd * 0.35
    cam_key(c5, f, back + Vector((0, -0.45 - spd * 0.05, h)), tip + Vector((0, 0, 0.1)))
c6 = camera("Cam_S6", 50)
for f in range(S6[0], S6[1] + 1, 4):
    k = ease(0, 1, f, S6[0], S6[1])
    cam_key(c6, f, G + Vector((0, -58 + 9 * k, 4 - 2 * k)), G + Vector((0, 0, 0.5)))
for c, (a, _) in ((c1, S1), (c2, S2), (c3, S3), (c4, S4), (c5, S5), (c6, S6)):
    m = sc.timeline_markers.new(c.name, frame=a)
    m.camera = c
sc.camera = c1

# ================================================================ render settings
r = sc.render
r.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 12
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.06
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3
sc.cycles.diffuse_bounces, sc.cycles.glossy_bounces = 2, 2
sc.cycles.transmission_bounces, sc.cycles.transparent_max_bounces = 1, 8
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
r.use_motion_blur = True
r.motion_blur_shutter = 0.4
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.use_persistent_data = True
r.image_settings.file_format = "PNG"
r.filepath = os.path.join(HERE, "..", "frames", "f_####")
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Punchy"
except TypeError as e:
    print("look", e)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "vessels.blend"))
print("saved; objects", len(sc.objects))
