"""Blood Vessels v2 - 21.9 s looping vertical short built with bpy + the Mixamo character Remy.

Run:  /opt/bvenv/bin/python build/build_scene.py      (writes build/vessels.blend)
Assets (not committed, Mixamo licence): assets/Battlecry.fbx (Remy).
Earth texture: build/earth_texture.py (Natural Earth, public domain).

Shots (30 fps, 657 frames = 21.9 s, last frame flows back into frame 1)
  A    1-21   full standing Remy, whip-zoom into his outstretched forearm        "INSIDE YOU"
  B   22-90   forearm close-up: laser slice, cross-section window, pulsing vessels
  C   91-138  camera dives into the vessel network inside the window
  D  139-229  whip back out to full Remy; his whole vessel network extracts      "HOW LONG?"
  E  230-260  the network balls up and one long line shoots out
  F  261-383  the line races across the land (km counter in captions)
  G  384-617  globe: the line wraps the Earth 2.5 times, heartbeat pulse, rush in
  H  618-657  "All packed inside... you." dive back down to the frame-1 shot
"""
import math
import os
import random

import bpy  # noqa: I001  (bpy first: the pip module registers bmesh/mathutils)
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
random.seed(11)
FPS = 30
END = 657
A, B, C, D, E, F, G, H = (1, 21), (22, 90), (91, 138), (139, 229), (230, 260), (261, 383), (384, 617), (618, 657)
P = "mixamorig:"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, END
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


def clamp01(x):
    return max(0.0, min(1.0, x))


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


def key_hide(ob, pairs):
    """pairs of (frame, hidden); never scale an object to 0 (Cycles stalls on degenerate BVH)"""
    for f, h in pairs:
        ob.hide_render = h
        ob.keyframe_insert("hide_render", frame=f)
    if ob.animation_data and ob.animation_data.action:
        for fc in iter_fcurves(ob.animation_data.action):
            if fc.data_path == "hide_render":
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"


def iter_fcurves(act):
    try:
        for lay in act.layers:
            for strip in lay.strips:
                for cb in strip.channelbags:
                    yield from cb.fcurves
    except AttributeError:
        yield from act.fcurves


def heartbeat(f):
    """lub-dub pulse, ~72 bpm, 0..1"""
    ph = (f / FPS * 1.2) % 1.0
    return math.exp(-((ph - 0.05) / 0.045) ** 2) + 0.6 * math.exp(-((ph - 0.25) / 0.05) ** 2)


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


def aim_bone(name, child, target_dir):
    a, c = bone_world(name), bone_world(child)
    d = (c - a).normalized()
    t = Vector(target_dir).normalized()
    if d.angle(t) > 1e-4:
        rotate_bone_world(name, d.cross(t).normalized(), d.angle(t))


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

# ---------- pose: left arm relaxed down, right arm held straight out (forearm toward the camera side)
DOWN = Vector((0, 0, -1))
RS = 1.0 if bone_world("RightArm").x > 0 else -1.0          # which world-x side his right arm is on
el = bone_world("LeftForeArm")
d = (el - bone_world("LeftArm")).normalized()
aim_bone("LeftArm", "LeftForeArm", d * math.cos(math.radians(62)) + DOWN * math.sin(math.radians(62)))
f_ = (bone_world("LeftHand") - bone_world("LeftForeArm")).normalized()
rotate_bone_world("LeftForeArm", f_.cross(Vector((0, -1, 0))).normalized(), math.radians(12))
OUT = Vector((0.78 * RS, -0.55, -0.16)).normalized()
aim_bone("RightArm", "RightForeArm", OUT)
aim_bone("RightForeArm", "RightHand", (OUT + Vector((0, -0.05, 0.10))).normalized())
# palm up-ish: twist the forearm about its own axis
fa = (bone_world("RightHand") - bone_world("RightForeArm")).normalized()
rotate_bone_world("RightForeArm", fa, math.radians(-70) * RS)
aim_bone("RightHand", "RightHandMiddle1", (fa + Vector((0, 0, -0.05))).normalized())
POSE = {n: b.rotation_quaternion.copy() for n, b in pb.items()}
IDLE = ["Spine1", "Spine2", "Neck", "Head", "LeftArm", "RightArm"]
BREATH = END / FPS / 6                                     # 6 whole breaths per loop -> seamless
for f in list(range(1, END + 1, 3)) + [END]:
    for n in IDLE:
        pb[P + n].rotation_quaternion = POSE[P + n]
    bpy.context.view_layer.update()
    br = math.sin(f / FPS * 2 * math.pi / BREATH)
    rotate_bone_world("Spine1", (1, 0, 0), -0.010 * br)
    rotate_bone_world("Spine2", (1, 0, 0), -0.012 * br)
    look = ease(0, 1, f, 160, 185) * (1 - ease(0, 1, f, 300, 330))   # glances at his extracted vessels
    rotate_bone_world("Neck", (0, 0, 1), 0.22 * look * RS * -1)
    rotate_bone_world("Head", (0, 0, 1), 0.3 * look * RS * -1)
    rotate_bone_world("Head", (1, 0, 0), -0.05 * ease(0, 1, f, 175, 190) * (1 - ease(0, 1, f, 205, 240)))
    rotate_bone_world("LeftArm", (0, 1, 0), 0.025 * br)
    for n in IDLE:
        pb[P + n].keyframe_insert("rotation_quaternion", frame=f)
for n, b in pb.items():
    if n.replace(P, "") not in IDLE:
        b.keyframe_insert("rotation_quaternion", frame=1)
    b.keyframe_insert("location", frame=1)
sc.frame_set(1)
bpy.context.view_layer.update()
print("right arm side", RS)

# ================================================================ Remy shader hooks: x-ray + forearm cut window
cut_box = link(bpy.data.objects.new("CutBox", None))
cut_box.empty_display_type = "CUBE"
XR_KEYS = [(1, 0.0), (D[0] + 12, 0.0), (D[0] + 22, 0.55), (D[0] + 62, 0.55), (D[0] + 80, 0.0)]
for m in {s.material for o in remy_meshes for s in o.material_slots if s.material}:
    t = m.node_tree
    out = next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_socket
    tr = t.nodes.new("ShaderNodeBsdfTransparent")
    em = t.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value, em.inputs["Strength"].default_value = hexc("#bfe4ff"), 0.35
    lw = t.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    ghost = t.nodes.new("ShaderNodeMixShader")
    t.links.new(lw.outputs["Facing"], ghost.inputs[0])
    t.links.new(tr.outputs[0], ghost.inputs[1])
    t.links.new(em.outputs[0], ghost.inputs[2])
    mix = t.nodes.new("ShaderNodeMixShader")
    v = t.nodes.new("ShaderNodeValue")
    v.name = "XRAY"
    t.links.new(v.outputs[0], mix.inputs[0])
    t.links.new(src, mix.inputs[1])
    t.links.new(ghost.outputs[0], mix.inputs[2])
    for f, val in XR_KEYS:
        v.outputs[0].default_value = val
        v.outputs[0].keyframe_insert("default_value", frame=f)
    # cut mask: inside the CutBox empty (|x|,|y|,|z| < 1) and CUT > 0 -> transparent
    tco = t.nodes.new("ShaderNodeTexCoord")
    tco.object = cut_box
    vab = t.nodes.new("ShaderNodeVectorMath")
    vab.operation = "ABSOLUTE"
    t.links.new(tco.outputs["Object"], vab.inputs[0])
    sxyz = t.nodes.new("ShaderNodeSeparateXYZ")
    t.links.new(vab.outputs[0], sxyz.inputs[0])
    m1 = t.nodes.new("ShaderNodeMath")
    m1.operation = "MAXIMUM"
    t.links.new(sxyz.outputs[0], m1.inputs[0])
    t.links.new(sxyz.outputs[1], m1.inputs[1])
    m2 = t.nodes.new("ShaderNodeMath")
    m2.operation = "MAXIMUM"
    t.links.new(m1.outputs[0], m2.inputs[0])
    t.links.new(sxyz.outputs[2], m2.inputs[1])
    lt = t.nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = 1.0
    t.links.new(m2.outputs[0], lt.inputs[0])
    cutv = t.nodes.new("ShaderNodeValue")
    cutv.name = "CUT"
    mm = t.nodes.new("ShaderNodeMath")
    mm.operation = "MULTIPLY"
    t.links.new(lt.outputs[0], mm.inputs[0])
    t.links.new(cutv.outputs[0], mm.inputs[1])
    tr2 = t.nodes.new("ShaderNodeBsdfTransparent")
    mix2 = t.nodes.new("ShaderNodeMixShader")
    t.links.new(mm.outputs[0], mix2.inputs[0])
    t.links.new(mix.outputs[0], mix2.inputs[1])
    t.links.new(tr2.outputs[0], mix2.inputs[2])
    t.links.new(mix2.outputs[0], out.inputs["Surface"])
    for f, val in ((1, 0.0), (B[0], 1.0), (D[0], 0.0)):
        cutv.outputs[0].default_value = val
        cutv.outputs[0].keyframe_insert("default_value", frame=f)
        for fc in iter_fcurves(t.animation_data.action):
            if 'nodes["CUT"]' in fc.data_path:
                for kp in fc.keyframe_points:
                    kp.interpolation = "CONSTANT"

# ================================================================ forearm cross-section (shots A-C)
bverts, bpolys = evaluated_world_verts(body)
bvh_body = BVHTree.FromPolygons(bverts, bpolys)
EL, WR = bone_world("RightForeArm"), bone_world("RightHand")
u = (WR - EL).normalized()
LF = (WR - EL).length
n0 = Vector((0.0, -1.0, 0.75))
nv = (n0 - u * n0.dot(u)).normalized()                   # towards the close-up camera
wv = u.cross(nv).normalized()


def thickness(p, d):
    """distance from p to the skin along +d and -d (rays fired from outside)"""
    a = bvh_body.ray_cast(p + d * 0.3, -d, 0.6)[0]
    b = bvh_body.ray_cast(p - d * 0.3, d, 0.6)[0]
    return a, b


mid = EL + u * (LF * 0.5)
pa, pb_ = thickness(mid, nv)
qa, qb = thickness(mid, wv)
ctr = mid
if pa and pb_:
    ctr = ctr + nv * (((pa - mid).dot(nv) + (pb_ - mid).dot(nv)) / 2)
if qa and qb:
    ctr = ctr + wv * (((qa - mid).dot(wv) + (qb - mid).dot(wv)) / 2)
RN = ((pa - pb_).length / 2) if (pa and pb_) else 0.04
RW = ((qa - qb).length / 2) if (qa and qb) else 0.04
AX0 = ctr - u * (LF * 0.5)                                # arm axis start (elbow end)
S0, S1 = 0.17 * LF, 0.80 * LF                             # window span along the forearm
HW = 0.74 * RW                                            # window half width
WC = AX0 + u * ((S0 + S1) / 2)                            # window centre on the axis
print("forearm R", round(RN, 4), round(RW, 4), "len", round(LF, 3))

ROT = Matrix((u, wv, nv)).transposed()                    # columns u, w, n


def place_world(ob, M):
    """parent ob to the right forearm bone keeping world matrix M"""
    ob.parent = arm
    ob.parent_type = "BONE"
    ob.parent_bone = P + "RightForeArm"
    bpy.context.view_layer.update()
    bm_ = pb[P + "RightForeArm"]
    par = arm.matrix_world @ bm_.matrix @ Matrix.Translation((0, bm_.length, 0))
    ob.matrix_parent_inverse = par.inverted()
    ob.matrix_basis = M


place_world(cut_box, Matrix.Translation(WC) @ ROT.to_4x4() @ Matrix.Diagonal(((S1 - S0) / 2, HW, RN * 1.7, 1)))
# window opens like a slit peeling back: y scale 0.04 -> 1
cut_box.keyframe_insert("scale", frame=1)
full_sy = cut_box.scale.y
for f, k in ((1, 0.04), (B[0] + 9, 0.04), (B[0] + 20, 1.0)):
    cut_box.scale.y = full_sy * k
    cut_box.keyframe_insert("scale", frame=f)


def sec_pt(s_, ang, rad_scale=1.0):
    """point on an elliptical tube around the arm axis; ang=0 faces the camera (n)"""
    return AX0 + u * s_ + (nv * math.cos(ang) * RN + wv * math.sin(ang) * RW) * rad_scale


# trough: elliptical tube open towards the camera + end caps
ANG0 = math.radians(48)
NS, NA = 24, 28
tm = bpy.data.meshes.new("Trough")
bm = bmesh.new()
grid = []
for i in range(NS + 1):
    s_ = S0 - 0.004 + (S1 - S0 + 0.008) * i / NS
    row = []
    for j in range(NA + 1):
        ang = ANG0 + (2 * math.pi - 2 * ANG0) * j / NA
        row.append(bm.verts.new(sec_pt(s_, ang, 0.93)))
    grid.append(row)
for i in range(NS):
    for j in range(NA):
        bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
for i in (0, NS):
    c_ = bm.verts.new(AX0 + u * (S0 - 0.004 + (S1 - S0 + 0.008) * i / NS) + nv * RN * 0.62)
    for j in range(NA):
        bm.faces.new((c_, grid[i][j], grid[i][j + 1]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for fc in bm.faces:
    fc.smooth = True
bm.to_mesh(tm)
bm.free()
flesh = bpy.data.materials.new("Flesh")
t = flesh.node_tree
fb = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
fco = t.nodes.new("ShaderNodeTexCoord")
fwave = t.nodes.new("ShaderNodeTexWave")                  # muscle fibres along the arm
fwave.inputs["Scale"].default_value, fwave.inputs["Distortion"].default_value = 60, 4
t.links.new(fco.outputs["Generated"], fwave.inputs["Vector"])
framp = t.nodes.new("ShaderNodeValToRGB")
framp.color_ramp.elements[0].color, framp.color_ramp.elements[1].color = hexc("#5a0d14"), hexc("#a3222e")
t.links.new(fwave.outputs["Fac"], framp.inputs[0])
t.links.new(framp.outputs["Color"], fb.inputs["Base Color"])
fb.inputs["Roughness"].default_value = 0.35
fb.inputs["Coat Weight"].default_value = 0.5
fb.inputs["Emission Color"].default_value = hexc("#3a0508")
fb.inputs["Emission Strength"].default_value = 0.6
tm.materials.append(flesh)
trough = link(bpy.data.objects.new("Trough", tm))
place_world(trough, Matrix.Identity(4))
trough.matrix_basis = Matrix.Identity(4)

# glowing laser cut outline on the skin surface
rim_pts = []
corners = [(S0, -HW), (S1, -HW), (S1, HW), (S0, HW), (S0, -HW)]
for (sa, wa), (sb, wb) in zip(corners, corners[1:]):
    n_ = max(2, int(((sb - sa) ** 2 + (wb - wa) ** 2) ** 0.5 / 0.002))
    for i in range(n_):
        k = i / n_
        p0 = AX0 + u * (sa + (sb - sa) * k) + wv * (wa + (wb - wa) * k)
        hit = bvh_body.ray_cast(p0 + nv * 0.3, -nv, 0.6)[0]
        rim_pts.append((hit if hit else p0 + nv * RN) + nv * 0.0006)
rim_pts.append(rim_pts[0])
rc = bpy.data.curves.new("CutRim", "CURVE")
rc.dimensions = "3D"
rc.bevel_depth, rc.bevel_resolution = 0.0007, 2
rc.bevel_factor_mapping_end = "SPLINE"
sp = rc.splines.new("POLY")
sp.points.add(len(rim_pts) - 1)
for pt, p in zip(sp.points, rim_pts):
    pt.co = (p.x, p.y, p.z, 1.0)
rimm, _ = principled("Laser", "#7ff0ff", 0.2, emission="#38e8ff", strength=6)
rc.materials.append(rimm)
rim = link(bpy.data.objects.new("CutRim", rc))
place_world(rim, Matrix.Identity(4))
for f, v_ in ((1, 0.0), (B[0], 0.0), (B[0] + 10, 1.0)):
    rc.bevel_factor_end = v_
    rc.keyframe_insert("bevel_factor_end", frame=f)
# rim glow cools after the cut
for f, v_ in ((B[0] + 10, 6.0), (B[0] + 30, 2.5)):
    rimm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = v_
    rimm.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
# laser spark riding the cut
spark_m, _ = principled("Spark", "#ffffff", 0.2, emission="#d8fdff", strength=40)
sme_ = bpy.data.meshes.new("Spark")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.0035)
bm.to_mesh(sme_)
bm.free()
sme_.materials.append(spark_m)
spark = link(bpy.data.objects.new("Spark", sme_))
key_hide(spark, ((1, True), (B[0], False), (B[0] + 11, True)))
cum = [0.0]
for a_, b_ in zip(rim_pts, rim_pts[1:]):
    cum.append(cum[-1] + (b_ - a_).length)
for f in range(B[0], B[0] + 11):
    target = cum[-1] * clamp01((f - B[0]) / 10)
    i = next(i for i, c in enumerate(cum) if c >= target - 1e-9)
    key(spark, "location", f, rim_pts[i] + nv * 0.001)

# dense glowing arteries (red) and veins (blue) inside the window
art_m, art_b = principled("ArmArtery", "#c3101c", 0.3, emission="#ff2633", strength=2.0)
vein_m, vein_b = principled("ArmVein", "#1b3fb8", 0.3, emission="#2f6bff", strength=1.6)
for f in range(1, D[0] + 1, 2):
    hb = heartbeat(f)
    art_b.inputs["Emission Strength"].default_value = 1.4 + 3.2 * hb
    art_b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
    vein_b.inputs["Emission Strength"].default_value = 1.1 + 1.6 * hb
    vein_b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
ac = bpy.data.curves.new("ArmVessels", "CURVE")
ac.dimensions = "3D"
ac.bevel_depth, ac.bevel_resolution = 1.0, 2
ac.use_fill_caps = True
ac.materials.append(art_m)
ac.materials.append(vein_m)


def arm_vessel(kind, ang, rr, rad, s_a=None, s_b=None, wob=0.08):
    s_a = S0 - 0.01 if s_a is None else s_a
    s_b = S1 + 0.01 if s_b is None else s_b
    n_ = max(4, int((s_b - s_a) / 0.004))
    sp_ = ac.splines.new("POLY")
    sp_.points.add(n_)
    ph = random.uniform(0, 6.28)
    for i, pt in enumerate(sp_.points):
        k = i / n_
        a_ = ang + wob * math.sin(ph + k * random.uniform(5, 9))
        r_ = rr + 0.05 * math.sin(ph * 2 + k * 7)
        p = sec_pt(s_a + (s_b - s_a) * k, a_, r_)
        pt.co = (p.x, p.y, p.z, 1.0)
        pt.radius = rad * (1 - 0.25 * k)
    sp_.material_index = kind
    sp_.use_smooth = True


# big paired trunks (radial/ulnar artery + veins), then a dense mesh of smaller ones
for ang, kind, rad in ((2.3, 0, 0.0034), (2.55, 1, 0.0038), (3.9, 0, 0.0032), (3.65, 1, 0.0036),
                       (3.14, 0, 0.0026), (2.95, 1, 0.003)):
    arm_vessel(kind, ang, 0.55, rad)
for k in range(70):
    arm_vessel(k % 2, random.uniform(1.0, 5.3), random.uniform(0.25, 0.85), random.uniform(0.0007, 0.0018),
               wob=0.25)
for k in range(90):                                          # short capillary loops
    s_a = random.uniform(S0, S1 - 0.02)
    arm_vessel(random.choice((0, 0, 1)), random.uniform(0.9, 5.4), random.uniform(0.3, 0.9),
               random.uniform(0.0004, 0.0008), s_a, s_a + random.uniform(0.015, 0.05), wob=0.6)
arm_ves = link(bpy.data.objects.new("ArmVessels", ac))
place_world(arm_ves, Matrix.Identity(4))
for ob in (trough, rim, arm_ves):
    key_hide(ob, ((1, True), (B[0], False), (D[0], True)))
# small soft key light that only lives for the close-ups
kl = link(bpy.data.objects.new("CloseLight", bpy.data.lights.new("CloseLight", "AREA")))
kl.data.size, kl.data.color = 0.25, (1.0, 0.95, 0.9)
kl.location = WC + nv * 0.45 + wv * 0.15 - u * 0.1
kl.rotation_euler = (WC - kl.location).to_track_quat("-Z", "Y").to_euler()
for f, en in ((1, 0.0), (A[1] - 6, 0.0), (A[1], 6.0), (C[1], 6.0), (D[0], 0.0)):
    kl.data.energy = en
    kl.data.keyframe_insert("energy", frame=f)

# ================================================================ full-body vessel network
# grown against body + clothing: Remy's body mesh has no skin under the shirt/shorts, which left the
# torso and upper thighs sparse (the "thigh gap") when only the body surface was used.
sc.frame_set(1)
bpy.context.view_layer.update()
allv, allp = [], []
for o in remy_meshes:
    if o.name.split(".")[0] in ("Body", "Tops", "Bottoms", "Shoes"):
        vs_, ps_ = evaluated_world_verts(o)
        off = len(allv)
        allv += vs_
        allp += [tuple(i + off for i in p) for p in ps_]
bvh = BVHTree.FromPolygons(allv, allp)
CB = Vector((0.0, 0.0, 1.0))


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
splines = []
trunk_pts, leg_top = [], []
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
        if "UpLeg" in ch[1]:
            leg_top += pts[: len(pts) // 2]                 # hips -> knees


def rnd_unit():
    return Vector([random.gauss(0, 1) for _ in range(3)]).normalized()


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


for k in range(1250):
    grow(random.choice(trunk_pts), rnd_unit(), random.randint(8, 24), random.uniform(0.0011, 0.0019), 0)
for k in range(260):                                       # extra coverage for hips/thighs
    grow(random.choice(leg_top), rnd_unit(), random.randint(10, 26), random.uniform(0.0012, 0.0019), 0)
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
vmat, vb = principled("Blood", "#b5121b", rough=0.35, emission="#ff2a2a", strength=0.35)
vb.inputs["Subsurface Weight"].default_value = 0.2
vb.inputs["Coat Weight"].default_value = 0.4
cu.materials.append(vmat)
vessels = link(bpy.data.objects.new("Vessels", cu))
vessels.location = CB
print("vessel splines", len(splines), "points", npts)

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
VX = Vector((-1.3 * RS, 0.0, 1.0))                         # stands on his free (left) side
X0 = D[0] + 10                                             # extraction starts
for f, loc in ((1, CB), (X0, CB), (X0 + 50, VX)):
    key(vessels, "location", f, loc)
for f in range(X0, X0 + 51, 3):
    k = ease(0, 1, f, X0, X0 + 50)
    vessels.rotation_euler = (0, 0, 0.25 * math.sin(k * math.pi))
    key(vessels, "rotation_euler", f)
for f, v in ((1, 0.0), (E[0], 0.0), (E[0] + 16, 1.0)):
    tk.value = v
    tk.keyframe_insert("value", frame=f)
for f, sc_ in ((1, 1.0), (E[0] + 6, 1.0), (E[1], 0.15)):
    key(vessels, "scale", f, (sc_,) * 3)
for f in range(E[0], E[1] + 1, 2):
    vessels.rotation_euler = (0.0, 0.0, ease(0, 1, f, E[0], E[1]) * 6.0)
    key(vessels, "rotation_euler", f)
key_hide(vessels, ((1, True), (D[0], False), (F[0], True)))

# ================================================================ the single long line (ground run)
DIRX = -RS                                                  # race away from Remy
line_pts = []
for j in range(25):
    t_ = j / 24
    line_pts.append(Vector((VX.x + DIRX * 1.1 * t_, 0.0, VX.z * (1 - t_) ** 2 + 0.025 * t_)))
x = 1.1
while x < 3600:
    x += 1.5
    line_pts.append(Vector((VX.x + DIRX * x, 5.0 * math.sin((x - 2) / 140) * min(1, (x - 2) / 60), 0.025)))
lengths = [0.0]
for a_, b_ in zip(line_pts, line_pts[1:]):
    lengths.append(lengths[-1] + (b_ - a_).length)
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
        mid_ = (lo + hi) // 2
        if lengths[mid_] < s_:
            lo = mid_
        else:
            hi = mid_
    seg = lengths[hi] - lengths[lo]
    return line_pts[lo].lerp(line_pts[hi], 0 if seg == 0 else (s_ - lengths[lo]) / seg)


L0 = E[0] + 6


def tip_s(f):
    if f < L0:
        return 0.0
    if f <= E[1]:
        return 25.0 * ((f - L0) / (E[1] - L0)) ** 2
    return 25.0 + 3400.0 * ((f - E[1]) / (F[1] - E[1])) ** 2.4


for f in range(1, F[1] + 2):
    lc.bevel_factor_end = tip_s(f) / LTOT
    lc.keyframe_insert("bevel_factor_end", frame=f)
key_hide(line, ((1, True), (L0, False), (G[0], True)))

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
    t.location = (VX.x + DIRX * xx, yy, 0)
    sz = random.uniform(0.8, 1.6)
    t.scale = (sz, sz, sz * random.uniform(0.9, 1.3))
    t.rotation_euler.z = random.uniform(0, 6.28)

# ================================================================ globe (high above everything)
GC = Vector((0.0, 0.0, 20000.0))
RE = 10.0
globe_rig = link(bpy.data.objects.new("GlobeRig", None))
globe_rig.location = GC
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
stars.location = GC
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
W0, W1 = G[0] + 8, G[0] + 97                               # wrap draws 13.0 s -> 16.0 s
for f in range(G[0], G[1] + 1, 2):
    k = clamp01((f - W0) / (W1 - W0))
    wc.bevel_factor_end = 0.002 + 0.998 * (k * k * (3 - 2 * k) * 0.25 + k * 0.75)
    wc.keyframe_insert("bevel_factor_end", frame=f)
    globe_rig.rotation_euler = (math.radians(18), 0, -0.55 + 0.85 * (f - G[0]) / (G[1] - G[0]))
    globe_rig.keyframe_insert("rotation_euler", frame=f)
    clouds.rotation_euler = (0, 0, 0.12 * (f - G[0]) / (G[1] - G[0]))
    clouds.keyframe_insert("rotation_euler", frame=f)
for f in range(G[0], G[1] + 1, 1):                         # heartbeat glow once the wrap is done
    hb = heartbeat(f) * ease(0, 1, f, W1, W1 + 10)
    wb.inputs["Emission Strength"].default_value = 2.5 + 7.0 * hb
    wb.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)


# ================================================================ cameras + cuts
def camera(name, lens=35, fstop=None, focus=None):
    c = bpy.data.cameras.new(name)
    c.lens, c.sensor_fit, c.sensor_width = lens, "VERTICAL", 36
    c.sensor_height = 36
    c.clip_start, c.clip_end = 0.002, 5000
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


def out_cubic(t):
    t = clamp01(t)
    return 1 - (1 - t) ** 3


def in_out(t):
    t = clamp01(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# loop pose: full standing Remy (also the very last frame)
P0, T0 = Vector((-0.15 * RS, -4.2, 1.05)), Vector((-0.2 * RS, 0.0, 1.0))
PE, TE = WC + nv * 0.26 - u * 0.02, WC                     # forearm close-up
cA = camera("Cam_A", 40)
for f in range(A[0], A[1] + 2):
    k = out_cubic((f - A[0]) / (A[1] - A[0] + 1))          # moving at full speed on frame 1: no static pause
    kk = in_out((f - A[0]) / (A[1] - A[0] + 1))
    cam_key(cA, f, P0.lerp(PE, k), T0.lerp(TE, kk))
    cA.data.lens = 40 - 8 * k
    cA.data.keyframe_insert("lens", frame=f)
cB = camera("Cam_B", 32)
for f in range(B[0], B[1] + 1, 2):
    k = (f - B[0]) / (B[1] - B[0])
    cam_key(cB, f, WC + nv * (0.26 - 0.08 * k) + wv * 0.03 * math.sin(k * 2) - u * 0.02, WC + u * 0.01 * k)
cC = camera("Cam_C", 22)                                    # dive into the vessels, then fly along them
for f in range(C[0], C[1] + 1):
    k = in_out((f - C[0]) / (C[1] - C[0]))
    p0, p1, p2 = WC + nv * 0.18, WC + nv * 0.05 - u * 0.02, WC + nv * RN * 0.55 + u * 0.01
    q0, q1, q2 = WC, WC + u * 0.01, WC - nv * RN * 0.5 + u * 0.035
    if k < 0.6:
        kk = k / 0.6
        loc, tgt = p0.lerp(p1, kk), q0.lerp(q1, kk)
    else:
        kk = (k - 0.6) / 0.4
        loc, tgt = p1.lerp(p2, kk), q1.lerp(q2, kk)
    cam_key(cC, f, loc, tgt)
focus_mid = link(bpy.data.objects.new("FocusMid", None))
focus_mid.location = (VX.x * 0.5, 0, 1.0)
PW, TW = Vector((VX.x * 0.45, -4.6, 1.05)), Vector((VX.x * 0.45, 0, 0.98))   # wide: Remy + extracted vessels
cD = camera("Cam_D", 30, 5.6, focus_mid)
for f in range(D[0], D[1] + 1):
    k = out_cubic((f - D[0]) / 12)                         # whip back out
    kt = out_cubic((f - D[0]) / 5)
    cam_key(cD, f, PE.lerp(PW, k) + Vector((0, 0.15 * (f - D[0]) / (D[1] - D[0]), 0)), TE.lerp(TW, kt))
cE = camera("Cam_E", 32, 5.6, vessels)
for f in range(E[0], E[1] + 1, 2):
    tip = arc_point(tip_s(f))
    k = ease(0, 1, f, L0, E[1])
    tgt = VX.lerp(tip + Vector((0, 0, 0.2)), k)
    cam_key(cE, f, (VX.x + DIRX * (-0.8 + 1.6 * k), -2.6 - 1.2 * k, 1.1 - 0.35 * k), tgt)
cF = camera("Cam_F", 28)
for f in range(F[0], F[1] + 1):
    s_ = tip_s(f)
    spd = tip_s(f + 1) - s_
    tip = arc_point(s_)
    back = arc_point(s_ - 2.2 - spd * 2.5)
    h = 0.35 + spd * 0.35
    cam_key(cF, f, back + Vector((0, -0.45 - spd * 0.05, h)), tip + Vector((0, 0, 0.1)))
cG = camera("Cam_G", 50)
for f in range(G[0], G[1] + 1):
    if f < G[0] + 16:
        dist = 22 + 24 * out_cubic((f - G[0]) / 16)         # whip out from the surface
    elif f < W1:
        dist = 46 + 4 * (f - G[0] - 16) / (W1 - G[0] - 16)
    elif f < G[1] - 11:
        dist = 50 + 6 * (f - W1) / (G[1] - 11 - W1)
    else:
        dist = 56 - 44 * ((f - (G[1] - 11)) / 11) ** 2      # rush back into the planet
    cam_key(cG, f, GC + Vector((0, -dist, 0.07 * dist)), GC + Vector((0, 0, 0.5)))
cH = camera("Cam_H", 40)                                    # dive down from the sky to the loop pose
for f in range(H[0], H[1] + 1):
    k = (f - H[0]) / (H[1] - H[0])
    off = (1 - k) ** 3
    loc = P0 + Vector((0.0, -9.0, 26.0)) * off
    tgt = T0 + Vector((0, 0, -0.6)) * off
    cam_key(cH, f, loc, tgt)
for c, (a_, _) in ((cA, A), (cB, B), (cC, C), (cD, D), (cE, E), (cF, F), (cG, G), (cH, H)):
    m = sc.timeline_markers.new(c.name, frame=a_)
    m.camera = c
sc.camera = cA

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
r.motion_blur_shutter = 0.5
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
