"""Patch vessels.blend in place: hide the Vessels curve from S5 (frame 451) on (same as build_scene.py)."""
import bpy, os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vessels.blend")
bpy.ops.wm.open_mainfile(filepath=p)
v = bpy.data.objects["Vessels"]
for f, h in ((1, False), (451, True)):
    v.hide_render = h
    v.keyframe_insert("hide_render", frame=f)
bpy.ops.wm.save_mainfile(filepath=p)
print("PATCHED")
