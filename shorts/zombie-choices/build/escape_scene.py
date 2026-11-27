"""Part 2 escape (S13, S14): reuses part 1's road set (Remy + orange backpack, zombies behind) with new cameras.
S13 local 1-48: low front tracking, he runs at the camera | S14 local 5-58: over-the-shoulder look back.
Run: /opt/bvenv/bin/python build/escape_scene.py -> build/escape.blend"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "zombie-survival", "build", "outdoor_scene.py")
os.environ["SET"] = "road"
code = open(SRC).read().replace('bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, f"{SET}.blend"))', "")
code = code.replace('HERE = os.path.dirname(os.path.abspath(__file__))', f'HERE = {os.path.dirname(SRC)!r}')
exec(compile(code, SRC, "exec"))
from mathutils import Quaternion, Vector  # noqa: E402

for f in range(5, 61):                                   # look back over his right shoulder (S14)
    k = max(0.0, min(1.0, (f - 12) / 10)) * (1 - max(0.0, min(1.0, (f - 50) / 8)))
    k = k * k * (3 - 2 * k)
    sc.frame_set(f)
    for bn, ang in (("mixamorig:Neck", -0.5), ("mixamorig:Head", -0.65), ("mixamorig:Spine2", -0.2)):
        pb = remy.pose.bones[bn]
        pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion((0, 1, 0), ang * k)
        pb.keyframe_insert("rotation_quaternion", frame=f)
c13 = cam("Cam_S13", 26)
for f in range(1, 49):
    y = -v * f
    ck(c13, f, Vector((-1.3, y - 3.4, 0.55)) + Vector((0.01 * math.sin(f * 2.3), 0, 0.008 * math.sin(f * 3.1))),
       Vector((-1.5, y + 0.8, 1.15)))
c14 = cam("Cam_S14", 32)
for f in range(5, 59):
    y = -v * f
    ck(c14, f, Vector((-1.25, y - 1.45, 1.6)) + Vector((0.006 * math.sin(f * 2.7), 0, 0)), Vector((-1.62, y, 1.42)))
sc.frame_start, sc.frame_end = 1, 60
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)) if False else
                            "/home/user/Touch-Canva/shorts/zombie-choices/build", "escape.blend"))
print("saved escape.blend")
