"""Render chosen frames at reduced size: preview.py <percent> <frame> [frame...] -> build/prev/p_<frame>.png"""
import bpy, os, sys, time
a = sys.argv[1:]
pct, frames = int(a[0]), [int(x) for x in a[1:]]
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(__file__), "penny.blend"))
sc = bpy.context.scene
sc.render.resolution_percentage = pct
os.makedirs(os.path.join(os.path.dirname(__file__), "prev"), exist_ok=True)
for f in frames:
    t = time.time()
    sc.frame_set(f)
    sc.render.filepath = os.path.join(os.path.dirname(__file__), "prev", f"p_{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"frame {f} {time.time()-t:.1f}s", flush=True)
