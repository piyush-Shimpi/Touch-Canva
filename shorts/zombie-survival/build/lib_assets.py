"""Shared helpers for the zombie short: Mixamo characters/actions, Poly Haven props, gore-free zombie skin."""
import math
import os

import bpy  # noqa: I001
from mathutils import Vector

LIB = os.environ.get("MIXAMO_LIB", "/home/user/mixamo-library")
ANIM = os.path.join(LIB, "animations")
ENV = os.path.join(LIB, "environments")


def sc():
    return bpy.context.scene


def link(ob, parent=None):
    sc().collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


def _new_objects(fn):
    before = set(bpy.data.objects)
    fn()
    return [o for o in bpy.data.objects if o not in before]


def set_action(arm, act):
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = act
    try:
        if act.slots and ad.action_slot is None:
            ad.action_slot = act.slots[0]
    except AttributeError:
        pass


def load_action(path, rename_prefix=None):
    """import an animation FBX, keep only its action (optionally rename bone prefix, e.g. mixamorig9: -> mixamorig:)"""
    before = set(bpy.data.actions)
    new = _new_objects(lambda: bpy.ops.import_scene.fbx(filepath=path))
    acts = [a for a in bpy.data.actions if a not in before]
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    act = acts[0]
    act.name = os.path.splitext(os.path.basename(path))[0]
    act.use_fake_user = True
    if rename_prefix:
        old, new_ = rename_prefix
        for fc in iter_fcurves(act):
            fc.data_path = fc.data_path.replace(old, new_)
        for grp in getattr(act, "groups", []):
            grp.name = grp.name.replace(old, new_)
    return act


def iter_fcurves(act):
    try:
        for lay in act.layers:
            for strip in lay.strips:
                for cb in strip.channelbags:
                    yield from cb.fcurves
    except AttributeError:
        yield from act.fcurves


def import_character(path, height=1.8, name=None):
    """returns (root_empty, armature, meshes); character normalised to `height` m in rest pose, feet at z=0"""
    new = _new_objects(lambda: bpy.ops.import_scene.fbx(filepath=path))
    arm = next(o for o in new if o.type == "ARMATURE")
    meshes = [o for o in new if o.type == "MESH"]
    root = link(bpy.data.objects.new((name or arm.name) + "_root", None))
    arm.parent = root
    act = arm.animation_data.action if arm.animation_data else None
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    zmin, zmax = min(p.z for p in pts), max(p.z for p in pts)
    s = height / (zmax - zmin)
    root.scale = (s, s, s)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    arm.location.z -= min(p.z for p in pts) / s
    arm.data.pose_position = "POSE"
    if name:
        arm.name = name
    bpy.context.view_layer.update()
    return root, arm, meshes, act


def nla(arm, clips):
    """clips: list of dict(action, start, a0, a1, repeat=1, blend='REPLACE', influence=[(frame, val), ...])
    each clip gets its own track (later tracks override earlier ones)"""
    ad = arm.animation_data or arm.animation_data_create()
    ad.action = None
    strips = []
    for i, c in enumerate(clips):
        tr = ad.nla_tracks.new()
        tr.name = f"{c['action'].name}_{i}"
        st = tr.strips.new(tr.name, int(c["start"]), c["action"])
        try:
            if c["action"].slots:
                st.action_slot = c["action"].slots[0]
        except AttributeError:
            pass
        st.action_frame_start, st.action_frame_end = c.get("a0", st.action_frame_start), c.get("a1", st.action_frame_end)
        st.repeat = c.get("repeat", 1.0)
        st.scale = c.get("scale", 1.0)
        st.blend_type = c.get("blend", "REPLACE")
        st.extrapolation = c.get("extrap", "HOLD_FORWARD" if i == 0 else "NOTHING")
        st.use_auto_blend = False
        if c.get("influence"):
            st.use_animated_influence = True
            for f, v in c["influence"]:
                st.influence = v
                st.keyframe_insert("influence", frame=f)
        strips.append(st)
    return strips


def degore(materials):
    """push saturated red (blood) areas of the zombie textures to dark olive grime; slight cold-green skin tint"""
    for m in materials:
        if not m or not m.use_nodes:
            continue
        t = m.node_tree
        bsdf = next((n for n in t.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if not bsdf or not bsdf.inputs["Base Color"].links:
            continue
        src = bsdf.inputs["Base Color"].links[0].from_socket
        sep = t.nodes.new("ShaderNodeSeparateColor")
        sep.mode = "HSV"
        t.links.new(src, sep.inputs[0])
        # redness = hue near 0/1
        h1 = t.nodes.new("ShaderNodeMath"); h1.operation = "PINGPONG"; h1.inputs[1].default_value = 0.5
        t.links.new(sep.outputs[0], h1.inputs[0])             # 0 at red, 0.5 at cyan
        red = t.nodes.new("ShaderNodeMapRange")
        red.inputs[1].default_value, red.inputs[2].default_value = 0.10, 0.03
        t.links.new(h1.outputs[0], red.inputs[0])
        sat = t.nodes.new("ShaderNodeMapRange")
        sat.inputs[1].default_value, sat.inputs[2].default_value = 0.30, 0.55
        t.links.new(sep.outputs[1], sat.inputs[0])
        mask = t.nodes.new("ShaderNodeMath"); mask.operation = "MULTIPLY"
        t.links.new(red.outputs[0], mask.inputs[0]); t.links.new(sat.outputs[0], mask.inputs[1])
        grime = t.nodes.new("ShaderNodeHueSaturation")
        grime.inputs["Hue"].default_value, grime.inputs["Saturation"].default_value = 0.72, 0.35
        grime.inputs["Value"].default_value = 0.55
        t.links.new(src, grime.inputs["Color"])
        mix = t.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
        t.links.new(mask.outputs[0], mix.inputs["Factor"])
        t.links.new(src, mix.inputs["A"]); t.links.new(grime.outputs[0], mix.inputs["B"])
        tint = t.nodes.new("ShaderNodeHueSaturation")       # sickly, slightly green-grey overall
        tint.inputs["Hue"].default_value, tint.inputs["Saturation"].default_value = 0.53, 0.75
        t.links.new(mix.outputs["Result"], tint.inputs["Color"])
        t.links.new(tint.outputs[0], bsdf.inputs["Base Color"])
        # wet blood is glossy: kill the gloss in the same mask
        if not bsdf.inputs["Roughness"].links:
            bsdf.inputs["Roughness"].default_value = max(bsdf.inputs["Roughness"].default_value, 0.6)


def append_polyhaven(folder, kind="models"):
    """append every object of a Poly Haven .blend; returns the new objects (unlinked to the scene)"""
    d = os.path.join(ENV, kind, folder)
    path = os.path.join(d, f"{folder}_1k.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = list(src.objects)
        dst.materials = list(src.materials)
    for img in bpy.data.images:
        fp = img.filepath
        if fp.startswith("//") and not os.path.exists(bpy.path.abspath(fp)):
            cand = os.path.join(d, fp[2:])
            if os.path.exists(cand):
                img.filepath = cand
    return [o for o in dst.objects if o is not None], [m for m in dst.materials if m is not None]


def polyhaven_material(folder):
    _, mats = append_polyhaven(folder, "textures")
    return mats[0]


def import_glb(path):
    return _new_objects(lambda: bpy.ops.import_scene.gltf(filepath=path))


def hdri_world(name, strength=1.0, rot_deg=0.0):
    w = bpy.data.worlds.new("World")
    sc().world = w
    t = w.node_tree
    t.nodes.clear()
    tc = t.nodes.new("ShaderNodeTexCoord")
    mp = t.nodes.new("ShaderNodeMapping")
    mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot_deg))
    env = t.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(ENV, "hdri", f"{name}_2k.hdr"))
    bg = t.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = strength
    out = t.nodes.new("ShaderNodeOutputWorld")
    t.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    t.links.new(mp.outputs[0], env.inputs[0])
    t.links.new(env.outputs[0], bg.inputs[0])
    t.links.new(bg.outputs[0], out.inputs[0])
    return w, mp


def foot_speed(arm, action, f0, f1, foot="mixamorig:LeftFoot"):
    """ground speed (m per frame) implied by an in-place cycle: backward foot speed while planted"""
    set_action(arm, action)
    pb = arm.pose.bones[foot]
    pos = []
    for f in range(int(f0), int(f1) + 1):
        sc().frame_set(f)
        pos.append((arm.matrix_world @ pb.head).copy())
    zmin = min(p.z for p in pos)
    v = [abs(pos[i + 1].y - pos[i].y) for i in range(len(pos) - 1) if pos[i].z < zmin + 0.04]
    arm.animation_data.action = None
    return sum(v) / max(1, len(v))


def bake_mix(arm, layers, weight, f0, f1, name="baked"):
    """bake a blend of two clips into one action.
    layers = [(action_a, time_fn_a), (action_b, time_fn_b)]; weight(f) in 0..1 picks b over a.
    time_fn maps scene frame -> action frame (float)."""
    (act_a, ta), (act_b, tb) = layers
    pbs = list(arm.pose.bones)
    ad = arm.animation_data or arm.animation_data_create()
    for t in ad.nla_tracks[:]:
        ad.nla_tracks.remove(t)

    def sample(act, t):
        set_action(arm, act)
        fi = math.floor(t)
        sc().frame_set(int(fi), subframe=t - fi)
        return {p.name: (p.rotation_quaternion.copy(), p.location.copy()) for p in pbs}

    poses = {}
    for f in range(f0, f1 + 1):
        a = sample(act_a, ta(f))
        b = sample(act_b, tb(f))
        w_ = max(0.0, min(1.0, weight(f)))
        poses[f] = {n: (a[n][0].slerp(b[n][0], w_), a[n][1].lerp(b[n][1], w_)) for n in a}
    out = bpy.data.actions.new(name)
    set_action(arm, out)
    for p in pbs:
        p.rotation_mode = "QUATERNION"
    for f, pose in poses.items():
        for p in pbs:
            q, l = pose[p.name]
            p.rotation_quaternion = q
            p.location = l
            p.keyframe_insert("rotation_quaternion", frame=f)
            p.keyframe_insert("location", frame=f)
    return out
