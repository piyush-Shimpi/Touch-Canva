"""Full animation render: render.py <percent> <samples> [start end] -> frames/f_####.png"""
import bpy, os, sys
a = sys.argv[1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(__file__), os.environ.get("BLEND", "hook.blend")))
sc = bpy.context.scene
sc.render.resolution_percentage = int(a[0])
sc.cycles.samples = int(a[1])
if len(a) > 3:
    sc.frame_start, sc.frame_end = int(a[2]), int(a[3])
sc.render.use_overwrite = False          # resumable
sc.render.filepath = os.path.join(os.path.dirname(__file__), "..", "frames", "f_####")
bpy.ops.render.render(animation=True)
print("RENDER DONE", flush=True)
