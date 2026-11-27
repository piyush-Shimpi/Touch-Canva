"""prevshots.py <blend> <pct> cam:frame ... -> prev/s_<cam>_<frame>.png"""
import bpy, os, sys, time
a = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
sc.render.resolution_percentage = int(a[1])
for spec in a[2:]:
    cam, f = spec.split(":")
    sc.camera = bpy.data.objects[cam]; sc.frame_set(int(f))
    sc.render.filepath = os.path.abspath(f"prev/s_{cam}_{f}.png"); t = time.time()
    bpy.ops.render.render(write_still=True); print("frame", cam, f, round(time.time() - t, 1), flush=True)
