"""Zombie Part 3: hideout behind a waterfall. Cut-away "ant farm" diorama (everything in front of y=0 removed).
x: left bank (zombies) -> pool -> waterfall at x~-0.2 -> cliff with carved room (x 0.35..2.6) ; z up ; camera looks +y.
Saves build/hideout.blend. Shots/cameras are added by shots.py (exec'd at the end)."""
import math
import os
import random
import sys

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "zombie-survival", "build"))
from lib_assets import (ANIM, LIB, append_polyhaven, bake_mix, degore, hdri_world, import_character,  # noqa: E402
                        iter_fcurves, key_hide, link, load_action, polyhaven_material, set_action, srgb)

random.seed(3)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = 30
D = 7.0                     # depth of the diorama (y 0..D)
POOL_X0, POOL_BED = -2.6, -1.3
ROOM = (0.35, 2.3, 0.3, 2.45)   # x0, x1, z0(floor), z1(ceiling)
ROOM_D = 1.8                # room depth in y
CLIFF_TOP, BANK_Z = 4.2, 0.18


def mat(name, color, rough=0.5, **kw):
    m = bpy.data.materials.new(name)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = srgb(color)
    b.inputs["Roughness"].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    return m


def box(name, x0, x1, z0, z1, y0=0.0, y1=D, material=None, parent=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(c) @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)))
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:                                     # box-project UVs at 1 unit = 1 m / 2
        n = f.normal
        for lp in f.loops:
            co = lp.vert.co
            if abs(n.z) > 0.5:
                lp[uv].uv = (co.x / 2, co.y / 2)
            elif abs(n.y) > 0.5:
                lp[uv].uv = (co.x / 2, co.z / 2)
            else:
                lp[uv].uv = (co.y / 2, co.z / 2)
    bm.to_mesh(me)
    bm.free()
    if material:
        me.materials.append(material)
    return link(bpy.data.objects.new(name, me), parent)


def linearize(idb):
    ad = idb.animation_data
    if ad and ad.action:
        for fc in iter_fcurves(ad.action):
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"


def soil_material(name, base, dark, stones=True):
    """cut-face soil: layered noise + strata + pebbles (object coords, so faces line up)"""
    m = bpy.data.materials.new(name)
    t = m.node_tree
    b = next(n for n in t.nodes if n.type == "BSDF_PRINCIPLED")
    tc = t.nodes.new("ShaderNodeTexCoord")
    nz = t.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.6
    nz.inputs["Detail"].default_value = 10.0
    t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    st = t.nodes.new("ShaderNodeTexWave")                 # horizontal strata
    st.wave_type = "BANDS"
    st.bands_direction = "Z"
    st.inputs["Scale"].default_value = 0.9
    st.inputs["Distortion"].default_value = 14.0
    t.links.new(tc.outputs["Object"], st.inputs["Vector"])
    mx = t.nodes.new("ShaderNodeMix")
    mx.data_type = "FLOAT"
    mx.inputs["Factor"].default_value = 0.12
    t.links.new(nz.outputs["Fac"], mx.inputs["A"])
    t.links.new(st.outputs["Fac"], mx.inputs["B"])
    ramp = t.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = srgb(dark)
    ramp.color_ramp.elements[1].color = srgb(base)
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.7
    t.links.new(mx.outputs["Result"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if stones:
        vo = t.nodes.new("ShaderNodeTexVoronoi")
        vo.inputs["Scale"].default_value = 7.0
        t.links.new(tc.outputs["Object"], vo.inputs["Vector"])
        th = t.nodes.new("ShaderNodeMath")
        th.operation = "LESS_THAN"
        th.inputs[1].default_value = 0.07
        t.links.new(vo.outputs["Distance"], th.inputs[0])
        mx2 = t.nodes.new("ShaderNodeMix")
        mx2.data_type = "RGBA"
        mx2.inputs["B"].default_value = srgb("#8b8378")
        t.links.new(th.outputs[0], mx2.inputs["Factor"])
        t.links.new(col, mx2.inputs["A"])
        col = mx2.outputs["Result"]
    t.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    bump = t.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    t.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    t.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ---------------------------------------------------------------- world: bright, slightly stylised daylight
world, wmap = hdri_world("kloofendal_48d_partly_cloudy_puresky", 1.15, 120)
sun = link(bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")))
sun.data.energy, sun.data.angle, sun.data.color = 4.6, math.radians(2), (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(52), math.radians(-18), math.radians(-28))

soil = soil_material("Soil", "#b4612f", "#5e2f17")
rock = soil_material("CliffRock", "#9a7b62", "#4d3a2c")
grass = polyhaven_material("aerial_grass_rock")
bed_m = polyhaven_material("coast_sand_rocks_02")
forest = polyhaven_material("forrest_ground_01")

# ---------------------------------------------------------------- ground masses (cut faces at y=0)
box("BankSoil", -9.0, POOL_X0, -9.0, BANK_Z - 0.06, material=soil)
box("BankTop", -9.0, POOL_X0, BANK_Z - 0.06, BANK_Z, material=forest)
box("PoolBedSoil", POOL_X0, 0.0, -9.0, POOL_BED - 0.08, material=soil)
box("PoolBed", POOL_X0, 0.0, POOL_BED - 0.08, POOL_BED, material=bed_m)
x0, x1, z0, z1 = ROOM
box("CliffBase", 0.0, 9.0, -9.0, z0, material=rock)
box("CliffAboveRoom", 0.0, 9.0, z1, CLIFF_TOP - 0.06, material=rock)
box("CliffTop", 0.0, 9.0, CLIFF_TOP - 0.06, CLIFF_TOP, material=grass)
box("CliffRightOfRoom", x1, 9.0, z0, z1, material=rock)
box("EntranceLintel", 0.0, x0, 1.45, z1, material=rock)          # low doorway behind the falls
box("RoomBack", x0, x1, z0, z1, y0=ROOM_D, material=rock)
box("RoomFloor", x0, x1, z0 - 0.02, z0 + 0.02, y1=ROOM_D, material=mat("PackedDirt", "#6b4426", 0.95))

# pool water: cut face visible, slightly murky blue, rippling surface
water = mat("PoolWater", "#2c8fc4", 0.06, **{"Transmission Weight": 0.85, "IOR": 1.33})
wb = next(n for n in water.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
wt = water.node_tree
wn = wt.nodes.new("ShaderNodeTexNoise")
wn.noise_dimensions = "4D"
wn.inputs["Scale"].default_value = 6.0
wbump = wt.nodes.new("ShaderNodeBump")
wbump.inputs["Strength"].default_value = 0.15
wt.links.new(wn.outputs["Fac"], wbump.inputs["Height"])
wt.links.new(wbump.outputs["Normal"], wb.inputs["Normal"])
wn.inputs["W"].default_value = 0.0
wn.inputs["W"].keyframe_insert("default_value", frame=-60)
wn.inputs["W"].default_value = 30.0
wn.inputs["W"].keyframe_insert("default_value", frame=1200)
wb.inputs["Emission Color"].default_value = srgb("#1f6f9e")
wb.inputs["Emission Strength"].default_value = 0.12
box("PoolWater", POOL_X0, -0.02, POOL_BED, 0.0, material=water)
linearize(water.node_tree)

# ---------------------------------------------------------------- the waterfall: a curved sheet of streaking white water
wf_m = bpy.data.materials.new("Waterfall")
t = wf_m.node_tree
t.nodes.clear()
out = t.nodes.new("ShaderNodeOutputMaterial")
pr = t.nodes.new("ShaderNodeBsdfPrincipled")
pr.inputs["Base Color"].default_value = srgb("#e9f6ff")
pr.inputs["Roughness"].default_value = 0.15
pr.inputs["Transmission Weight"].default_value = 0.55
pr.inputs["IOR"].default_value = 1.33
tc = t.nodes.new("ShaderNodeTexCoord")
mp = t.nodes.new("ShaderNodeMapping")
mp.inputs["Scale"].default_value = (6.0, 6.0, 0.6)            # long vertical streaks
t.links.new(tc.outputs["Object"], mp.inputs["Vector"])
for f, zoff in ((-60, 0.0), (1200, 210.0)):                   # streaks rush downward
    mp.inputs["Location"].default_value = (0, 0, zoff)
    mp.inputs["Location"].keyframe_insert("default_value", frame=f)
nz = t.nodes.new("ShaderNodeTexNoise")
nz.inputs["Scale"].default_value = 2.5
nz.inputs["Detail"].default_value = 6.0
t.links.new(mp.outputs[0], nz.inputs["Vector"])
ramp = t.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.42
ramp.color_ramp.elements[1].position = 0.62
t.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
tr = t.nodes.new("ShaderNodeBsdfTransparent")
tr.inputs["Color"].default_value = (0.75, 0.9, 1.0, 1)
mix = t.nodes.new("ShaderNodeMixShader")
mx_f = t.nodes.new("ShaderNodeMath")
mx_f.operation = "MULTIPLY_ADD"
mx_f.inputs[1].default_value = 0.6
mx_f.inputs[2].default_value = 0.18
t.links.new(ramp.outputs["Color"], mx_f.inputs[0])
t.links.new(mx_f.outputs[0], mix.inputs["Fac"])
t.links.new(tr.outputs[0], mix.inputs[1])
t.links.new(pr.outputs[0], mix.inputs[2])
em = t.nodes.new("ShaderNodeEmission")                         # keeps the foam bright in shade
em.inputs["Strength"].default_value = 0.35
t.links.new(ramp.outputs["Color"], em.inputs["Color"])
add = t.nodes.new("ShaderNodeAddShader")
t.links.new(mix.outputs[0], add.inputs[0])
t.links.new(em.outputs[0], add.inputs[1])
t.links.new(add.outputs[0], out.inputs["Surface"])
linearize(wf_m.node_tree)

me = bpy.data.meshes.new("Waterfall")
bm = bmesh.new()
NZ, NY = 24, 6
verts = []
for iz in range(NZ + 1):
    z = CLIFF_TOP + 0.05 - (CLIFF_TOP + 0.05) * iz / NZ
    u = iz / NZ
    x = -0.05 - 0.38 * math.sin(u * math.pi * 0.5) ** 0.7      # leaves the lip, arcs outward
    row = []
    for iy in range(NY + 1):
        y = 0.0 + 3.2 * iy / NY
        row.append(bm.verts.new((x, y, z)))
    verts.append(row)
for iz in range(NZ):
    for iy in range(NY):
        bm.faces.new((verts[iz][iy], verts[iz][iy + 1], verts[iz + 1][iy + 1], verts[iz + 1][iy]))
bm.to_mesh(me)
bm.free()
wfall = link(bpy.data.objects.new("Waterfall", me))
me.materials.append(wf_m)
sol = wfall.modifiers.new("thick", "SOLIDIFY")
sol.thickness = 0.24
for p in me.polygons:
    p.use_smooth = True

# foam + mist at the plunge point (noisy white blobs, gently churning)
foam_m = mat("Foam", "#ffffff", 0.6, **{"Emission Color": srgb("#ffffff"), "Emission Strength": 0.25})
for i in range(9):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.28,
                                          location=(-0.45 + random.uniform(-0.35, 0.3), random.uniform(0.1, 3.0), 0.02))
    fo = bpy.context.active_object
    fo.name = f"Foam{i}"
    fo.scale = (random.uniform(0.9, 1.5), random.uniform(0.9, 1.5), 0.32)
    fo.data.materials.append(foam_m)
    dm = fo.modifiers.new("d", "DISPLACE")
    tx = bpy.data.textures.new(f"foamtex{i}", "CLOUDS")
    tx.noise_scale = 0.18
    dm.texture, dm.strength = tx, 0.12
    for f, s in ((-60, 0.9), (1200, 1.15)):
        fo.rotation_euler = (0, 0, s * 40 * (1 if i % 2 else -1))
        fo.keyframe_insert("rotation_euler", frame=f)

# ---------------------------------------------------------------- dressing: trees on top, rocks at the pool, room props
_PH = {}


def place_ph(folder, loc, scale=1.0, rotz=None):
    """Poly Haven model as a collection instance (appended once -> low memory)"""
    if folder not in _PH:
        objs, _ = append_polyhaven(folder)
        col = bpy.data.collections.new("PH_" + folder)
        for o in objs:
            col.objects.link(o)
        _PH[folder] = col
    inst = link(bpy.data.objects.new(f"{folder}_inst", None))
    inst.instance_type, inst.instance_collection = "COLLECTION", _PH[folder]
    inst.location = loc
    inst.scale = (scale, scale, scale)
    inst.rotation_euler.z = random.uniform(0, 6.28) if rotz is None else rotz
    return [inst]


for loc, sc_ in (((1.4, 5.2, CLIFF_TOP), 0.9), ((3.4, 4.6, CLIFF_TOP), 1.05), ((-4.2, 5.4, BANK_Z), 1.0),
                 ((-5.8, 4.4, BANK_Z), 0.85)):
    place_ph("fir_sapling_medium", loc, sc_ * 0.62)
place_ph("tree_small_02", (2.0, 6.2, CLIFF_TOP), 0.6)
# stream on the cliff top feeding the falls
box("Stream", -0.05, 3.0, CLIFF_TOP - 0.03, CLIFF_TOP + 0.04, y0=0.0, y1=3.2, material=water)
place_ph("rock_moss_set_02", (-3.0, 2.6, BANK_Z - 0.05), 0.6)
place_ph("boulder_01", (-0.9, 3.4, POOL_BED + 0.2), 0.7)
mud_rock = place_ph("boulder_01", (-3.05, 0.75, BANK_Z - 0.1), 0.45, rotz=0.4)[0]
mud_rock.name = "MudRock"

# THE MISTAKE: one muddy footprint on the bank rock, pointing at the falls (pinned-comment bait)
fp_m = mat("MudPrint", "#3b2414", 1.0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.012, location=(-2.92, 0.55, BANK_Z + 0.14))
fpr = bpy.context.active_object
fpr.name = "Footprint"
fpr.scale = (1.9, 0.75, 1)
fpr.rotation_euler = (0.18, 0, 0.1)
fpr.data.materials.append(fp_m)

# room: campfire, bedroll, barrel, water jug
fire_m = mat("Fire", "#ff6a10", 0.5, **{"Emission Color": srgb("#ff5a08"), "Emission Strength": 2.5})
bpy.ops.mesh.primitive_cone_add(radius1=0.13, depth=0.32, location=(1.75, 0.9, ROOM[2] + 0.18))
flame = bpy.context.active_object
flame.name = "Flame"
flame.data.materials.append(fire_m)
for f in range(-60, 1201, 3):
    flame.scale = (1 + 0.15 * math.sin(f * 1.7), 1 + 0.15 * math.sin(f * 2.3), 1 + 0.25 * math.sin(f * 1.3))
    flame.keyframe_insert("scale", frame=f)
for i in range(5):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.4, location=(1.75, 0.9, ROOM[2] + 0.04),
                                        rotation=(math.radians(90), 0, i * 0.63))
    bpy.context.active_object.data.materials.append(mat("Log", "#4a2e19", 0.9))
fire = link(bpy.data.objects.new("FireLight", bpy.data.lights.new("FireLight", "POINT")))
fire.data.energy, fire.data.color, fire.data.shadow_soft_size = 140, (1.0, 0.55, 0.22), 0.15
fire.location = (1.75, 0.75, ROOM[2] + 0.55)
for f in range(-60, 1201, 2):
    fire.data.energy = 140 * (1 + 0.18 * math.sin(f * 1.9) + 0.1 * math.sin(f * 3.7))
    fire.data.keyframe_insert("energy", frame=f)
bpy.ops.mesh.primitive_cube_add(size=1, location=(2.0, 1.25, ROOM[2] + 0.06))
bed = bpy.context.active_object
bed.scale = (0.45, 1.0, 0.1)
bed.data.materials.append(mat("Bedroll", "#5d6b3a", 0.9))
place_ph("Barrel_01", (2.05, 1.6, ROOM[2]), 0.5)

# smoke vent (used in the SMOKE TRAP beat): a thin pipe from the ceiling, out under the falls
vent_m = mat("VentHole", "#24160c", 1.0)
box("SmokeVent", 1.68, 1.81, ROOM[3], 2.85, y0=0.85, y1=1.0, material=vent_m)
box("SmokeVentOut", -0.02, 1.81, 2.72, 2.85, y0=0.85, y1=1.0, material=vent_m)

# ---------------------------------------------------------------- characters
remy_root, remy, remy_meshes, _ = import_character(os.path.join(LIB, "characters", "remy.fbx"), 1.80, "Remy")
z_root, zom, zmeshes, zrun = import_character(os.path.join(ANIM, "zombie", "zombie_run_warzombie.fbx"), 1.85, "Zed")
degore({s.material for o in zmeshes for s in o.material_slots})
g_root, girl, gmeshes, gidle = import_character(os.path.join(ANIM, "zombie", "zombie_idle_zombiegirl.fbx"), 1.72, "ZGirl")
degore({s.material for o in gmeshes for s in o.material_slots})
R = ("mixamorig9:", "mixamorig:")
A = {}
for name, path in (("terrified", "reactions/terrified_leonard.fbx"), ("dig", "action/digging.fbx"),
                   ("swim", "action/swimming.fbx"), ("swim_edge", "action/swimming_to_edge.fbx"),
                   ("crawl", "action/crawl_low.fbx"), ("sit", "daily/sitting_idle.fbx"),
                   ("walk", "action/strut_walking_leonard.fbx"), ("kneel", "action/dig_and_plant_seeds.fbx"), ("shock", "reactions/shocked_step_back.fbx"),
                   ("scream", "zombie/zombie_scream_skeletonzombie.fbx"), ("attack", "zombie/zombie_attack.fbx")):
    A[name] = load_action(os.path.join(ANIM, path), R)
A["zrun"], A["gidle"] = zrun, gidle
for a_ in A.values():                       # some exports carry object-level transform keys: they knock the rig over
    for lay in a_.layers:
        for st_ in lay.strips:
            for cb in st_.channelbags:
                for fc in [fc for fc in cb.fcurves if not fc.data_path.startswith("pose.")]:
                    cb.fcurves.remove(fc)

exec(open(os.path.join(HERE, "shots.py")).read())

r = sc.render
r.engine = "CYCLES"
sc.cycles.samples = 16
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 6
sc.cycles.transmission_bounces = 6
sc.cycles.transparent_max_bounces = 12
r.use_motion_blur = True
r.motion_blur_shutter = 0.5
r.resolution_x, r.resolution_y = 1080, 1920
r.use_persistent_data = True
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except TypeError:
    pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "hideout.blend"))
print("saved hideout.blend")
