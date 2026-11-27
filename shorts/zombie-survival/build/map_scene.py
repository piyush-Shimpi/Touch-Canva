"""Tabletop 3D US outbreak map (S03, S04, S10, S12) -> build/map.blend
Local timeline: S03 1-63 | S04 64-144 | S10 200-247 | S12 300-344"""
import json
import math
import os
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib_assets import hdri_world, link, srgb  # noqa: E402

A = os.path.join(HERE, "..", "assets")
M = json.load(open(os.path.join(A, "map_meta.json")))
MW = 4.8
MH = MW * M["H"] / M["W"]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
sc.frame_start, sc.frame_end = 1, 344
hdri_world("studio_small_09", 0.45)


def ll(lon, lat, z=0.0):
    x = ((lon - M["lon0"]) / (M["lon1"] - M["lon0"]) - 0.5) * MW
    y = (0.5 - (M["lat1"] - lat) / (M["lat1"] - M["lat0"])) * MH
    return Vector((x, y, z))


def plane(name, w, h, z, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm, vec=(w, h, 1), verts=bm.verts)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x / w + 0.5, lp.vert.co.y / h + 0.5)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = link(bpy.data.objects.new(name, me))
    ob.location.z = z
    return ob


def img(name, noncolor=False):
    im = bpy.data.images.load(os.path.join(A, name))
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


# ---------------- table + ocean slab
tbl = bpy.data.materials.new("Table")
tb = next(n for n in tbl.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
tb.inputs["Base Color"].default_value = srgb("#7f97ab")
tb.inputs["Roughness"].default_value = 0.4
plane("Table", 40, 40, -0.06, tbl)
base_img, time_img, land_img = img("map_base.png"), img("map_time.png", True), img("map_land.png", True)

ocean = bpy.data.materials.new("MapBase")
t = ocean.node_tree
ob_ = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
tx = t.nodes.new("ShaderNodeTexImage")
tx.image = base_img
t.links.new(tx.outputs["Color"], ob_.inputs["Base Color"])
ob_.inputs["Roughness"].default_value = 0.5
plane("MapBase", MW, MH, 0.0, ocean)

# ---------------- raised land layer with the infection shader
lm = bpy.data.materials.new("Land")
t = lm.node_tree
t.nodes.clear()
out = t.nodes.new("ShaderNodeOutputMaterial")
bsdf = t.nodes.new("ShaderNodeBsdfPrincipled")
txb = t.nodes.new("ShaderNodeTexImage"); txb.image = base_img
txt = t.nodes.new("ShaderNodeTexImage"); txt.image = time_img; txt.interpolation = "Linear"
txl = t.nodes.new("ShaderNodeTexImage"); txl.image = land_img
tcur = t.nodes.new("ShaderNodeValue"); tcur.name = "TCUR"
safe = t.nodes.new("ShaderNodeValue"); safe.name = "SAFE"
sub = t.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"             # how long ago it arrived
t.links.new(tcur.outputs[0], sub.inputs[0]); t.links.new(txt.outputs["Color"], sub.inputs[1])
inf = t.nodes.new("ShaderNodeMapRange"); inf.inputs[1].default_value, inf.inputs[2].default_value = 0.0, 0.012
t.links.new(sub.outputs[0], inf.inputs[0])                                  # 0 healthy .. 1 infected
front = t.nodes.new("ShaderNodeMapRange")                                   # glowing advancing edge
front.inputs[1].default_value, front.inputs[2].default_value = 0.0, 0.035
front.inputs[3].default_value, front.inputs[4].default_value = 1.0, 0.0
t.links.new(sub.outputs[0], front.inputs[0])
fm = t.nodes.new("ShaderNodeMath"); fm.operation = "MULTIPLY"
t.links.new(front.outputs[0], fm.inputs[0]); t.links.new(inf.outputs[0], fm.inputs[1])
red = t.nodes.new("ShaderNodeMix"); red.data_type = "RGBA"
red.inputs["B"].default_value = srgb("#d40d14")
t.links.new(inf.outputs[0], red.inputs["Factor"]); t.links.new(txb.outputs["Color"], red.inputs["A"])
gbase = t.nodes.new("ShaderNodeMix"); gbase.data_type = "RGBA"
gbase.inputs["B"].default_value = srgb("#19c94f")
t.links.new(red.outputs["Result"], gbase.inputs["A"])
t.links.new(gbase.outputs["Result"], bsdf.inputs["Base Color"])
bsdf.inputs["Roughness"].default_value = 0.45
# emission: infected areas glow red, the front glows orange, the surviving pocket glows green at the end
e_red = t.nodes.new("ShaderNodeMath"); e_red.operation = "MULTIPLY"; e_red.inputs[1].default_value = 0.6
t.links.new(inf.outputs[0], e_red.inputs[0])
c_red = t.nodes.new("ShaderNodeMix"); c_red.data_type = "RGBA"
c_red.inputs["A"].default_value = srgb("#ff1e24"); c_red.inputs["B"].default_value = srgb("#ffb21e")
t.links.new(fm.outputs[0], c_red.inputs["Factor"])
healthy = t.nodes.new("ShaderNodeMath"); healthy.operation = "SUBTRACT"; healthy.inputs[0].default_value = 1.0
t.links.new(inf.outputs[0], healthy.inputs[1])
g = t.nodes.new("ShaderNodeMath"); g.operation = "MULTIPLY"
t.links.new(healthy.outputs[0], g.inputs[0]); t.links.new(safe.outputs[0], g.inputs[1])
c_all = t.nodes.new("ShaderNodeMix"); c_all.data_type = "RGBA"
c_all.inputs["B"].default_value = srgb("#2bff6a")
t.links.new(g.outputs[0], c_all.inputs["Factor"]); t.links.new(g.outputs[0], gbase.inputs["Factor"]); t.links.new(c_red.outputs["Result"], c_all.inputs["A"])
e_sum = t.nodes.new("ShaderNodeMath"); e_sum.operation = "ADD"
t.links.new(e_red.outputs[0], e_sum.inputs[0])
e_f = t.nodes.new("ShaderNodeMath"); e_f.operation = "MULTIPLY"; e_f.inputs[1].default_value = 3.0
t.links.new(fm.outputs[0], e_f.inputs[0])
e_sum2 = t.nodes.new("ShaderNodeMath"); e_sum2.operation = "ADD"
t.links.new(e_sum.outputs[0], e_sum2.inputs[0]); t.links.new(e_f.outputs[0], e_sum2.inputs[1])
e_g = t.nodes.new("ShaderNodeMath"); e_g.operation = "MULTIPLY"; e_g.inputs[1].default_value = 1.2
t.links.new(g.outputs[0], e_g.inputs[0])
t.links.new(e_g.outputs[0], e_sum.inputs[1])
t.links.new(c_all.outputs["Result"], bsdf.inputs["Emission Color"])
t.links.new(e_sum2.outputs[0], bsdf.inputs["Emission Strength"])
t.links.new(txl.outputs["Color"], bsdf.inputs["Alpha"])
t.links.new(bsdf.outputs[0], out.inputs["Surface"])
land = plane("Land", MW, MH, 0.025, lm)
sol = land.modifiers.new("solid", "SOLIDIFY")          # thin slab so the land casts a little shadow
sol.thickness = 0.02


def key_val(node, pairs, interp="BEZIER"):
    for f, v in pairs:
        node.outputs[0].default_value = v
        node.outputs[0].keyframe_insert("default_value", frame=f)


key_val(tcur, [(1, -0.05), (66, -0.05), (100, 0.06), (144, 0.13),          # S03 calm, S04 cities bloom
               (200, 0.33), (247, 0.40),                                    # S10 most of the country red
               (300, 0.55), (318, 0.80), (344, 0.815)])                     # S12 everything but the Rockies
key_val(safe, [(1, 0.0), (317, 0.0), (319, 1.0), (330, 0.7), (338, 1.0), (344, 0.8)])

# ---------------- city glow dots (a few big metros) and the route
spark = bpy.data.materials.new("CityGlow")
sb = next(n for n in spark.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
sb.inputs["Base Color"].default_value = (1, 1, 1, 1)
sb.inputs["Emission Color"].default_value = srgb("#fff2d0")
sb.inputs["Emission Strength"].default_value = 6
for lon, lat in ((-74.0, 40.7), (-118.2, 34.05), (-87.6, 41.9), (-96.8, 32.8), (-95.4, 29.8), (-122.4, 37.77),
                 (-71.06, 42.36), (-84.4, 33.75), (-80.2, 25.8), (-122.33, 47.6), (-104.99, 39.74), (-112.07, 33.45)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.022, location=ll(lon, lat, 0.06), segments=12, ring_count=6)
    s_ = bpy.context.active_object
    s_.data.materials.append(spark)

route_pts = []
A_, B_ = (-87.6, 41.9), (-111.6, 46.3)
for i in range(41):
    k = i / 40
    p = ll(A_[0] + (B_[0] - A_[0]) * k, A_[1] + (B_[1] - A_[1]) * k + 1.8 * math.sin(math.pi * k), 0.07 + 0.25 * math.sin(math.pi * k))
    route_pts.append(p)
rc = bpy.data.curves.new("Route", "CURVE")
rc.dimensions = "3D"
rc.bevel_depth, rc.bevel_resolution = 0.018, 3
rc.bevel_factor_mapping_end = "SPLINE"
sp = rc.splines.new("POLY")
sp.points.add(len(route_pts) - 1)
for pt, p in zip(sp.points, route_pts):
    pt.co = (p.x, p.y, p.z, 1)
rm = bpy.data.materials.new("Route")
rb = next(n for n in rm.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
rb.inputs["Base Color"].default_value = srgb("#ff7a1a")
rb.inputs["Emission Color"].default_value = srgb("#ff8a2a")
rb.inputs["Emission Strength"].default_value = 5
rc.materials.append(rm)
route = link(bpy.data.objects.new("Route", rc))
for f, v in ((1, 0.0), (204, 0.0), (236, 1.0)):
    rc.bevel_factor_end = v
    rc.keyframe_insert("bevel_factor_end", frame=f)
# pin at the destination
pin_m = bpy.data.materials.new("Pin")
pnb = next(n for n in pin_m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
pnb.inputs["Base Color"].default_value = srgb("#2bff6a")
pnb.inputs["Emission Color"].default_value = srgb("#2bff6a")
pnb.inputs["Emission Strength"].default_value = 5
bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.014, location=ll(*B_, 0.07))
pin = bpy.context.active_object
pin.data.materials.append(pin_m)
for f, s_ in ((1, 0.01), (232, 0.01), (240, 1.2), (246, 1.0)):
    pin.scale = (s_,) * 3
    pin.keyframe_insert("scale", frame=f)

# ---------------- cameras
def cam(name, lens):
    c = bpy.data.cameras.new(name)
    c.lens, c.sensor_fit, c.sensor_height = lens, "VERTICAL", 24
    c.clip_start = 0.01
    return link(bpy.data.objects.new(name, c))


def ck(c, f, loc, tgt):
    c.location = loc
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    c.keyframe_insert("location", frame=f)
    c.keyframe_insert("rotation_euler", frame=f)


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


C = ll(-96, 38.5)
c3 = cam("Cam_S03", 30)                                     # top-down push-in
for f in range(1, 64, 2):
    k = ease((f - 1) / 62)
    ck(c3, f, C + Vector((0, -0.6, 7.2 - 2.4 * k)), C + Vector((0, 0.05, 0)))
c4 = cam("Cam_S04", 28)                                     # 3/4 orbit while the cities bloom
for f in range(64, 145, 2):
    k = ease((f - 64) / 80)
    a = math.radians(-35 + 25 * k)
    ck(c4, f, C + Vector((3.6 * math.sin(a), -3.6 * math.cos(a), 2.6)), C + Vector((0.2, 0.3, 0)))
c10 = cam("Cam_S10", 30)                                    # follows the route to the Rockies
for f in range(200, 248, 2):
    k = ease((f - 200) / 47)
    tgt = ll(-87.6 + (-111.6 + 87.6) * k, 41.9 + (46.3 - 41.9) * k)
    ck(c10, f, tgt + Vector((0.5, -4.6 + 0.6 * k, 4.4 - 0.6 * k)), tgt + Vector((0, 0.2, 0)))
c12 = cam("Cam_S12", 24)                                    # whole country, then the hit on the Rockies
for f in range(300, 345):
    if f < 318:
        k = ease((f - 300) / 18)
        loc, tgt = C + Vector((0, -6.6 + 0.6 * k, 5.6 - 0.4 * k)), C + Vector((0, 0.35, 0))
    elif f <= 320:                                          # 3-frame hit freeze
        k = 1.0
        loc, tgt = C + Vector((0, -6.0, 5.2)), C + Vector((0, 0.35, 0))
    else:                                                   # push in on the green pocket
        k = ease((f - 320) / 16)
        R_ = ll(*B_)
        loc = (C + Vector((0, -6.0, 5.2))).lerp(R_ + Vector((0.2, -2.9, 2.6)), k)
        tgt = (C + Vector((0, 0.35, 0))).lerp(R_ + Vector((0, 0.45, 0)), k)
    ck(c12, f, loc, tgt)
# white hit-flash card in front of S12 camera
fl = bpy.data.materials.new("Flash")
fl.node_tree.nodes.clear()
fo = fl.node_tree.nodes.new("ShaderNodeOutputMaterial")
fe = fl.node_tree.nodes.new("ShaderNodeEmission")
fe.inputs["Strength"].default_value = 0.0
fl.node_tree.links.new(fe.outputs[0], fo.inputs["Surface"])
fcard = plane("FlashCard", 0.4, 0.6, 0, fl)
fcard.parent = c12
fcard.location = (0, 0, -0.05)
for f, v in ((300, 0.0), (318, 0.0), (319, 18.0), (321, 0.0)):
    fe.inputs["Strength"].default_value = v
    fe.inputs["Strength"].keyframe_insert("default_value", frame=f)
fcard.visible_shadow = False
for f, h in ((1, True), (319, False), (321, True)):
    fcard.hide_render = h
    fcard.keyframe_insert("hide_render", frame=f)

sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy, sun.data.angle = 3.0, math.radians(8)
sun.rotation_euler = (math.radians(40), 0, math.radians(30))
sc.camera = c3
for c, f in ((c3, 1), (c4, 64), (c10, 200), (c12, 300)):
    sc.timeline_markers.new(c.name, frame=f).camera = c
r = sc.render
r.engine = "CYCLES"
sc.cycles.samples = 16
sc.cycles.use_denoising = True
r.use_motion_blur = True
r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "Medium High Contrast"
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "map.blend"))
print("saved map.blend")
