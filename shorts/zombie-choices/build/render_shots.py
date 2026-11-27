"""render_shots.py -- <blend> <pct> <samples> CAM:LOCAL0:LOCAL1:OUT0 ...
Renders each shot's local frame range with its camera into frames/f_<OUT>.png (skips existing -> resumable)."""
import bpy, os, sys, time
a = sys.argv[sys.argv.index("--") + 1:]
blend, pct, spp = a[0], int(a[1]), int(a[2])
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), blend))
sc = bpy.context.scene
sc.render.resolution_percentage = pct
sc.cycles.samples = spp
sc.view_settings.exposure = float(os.environ.get("EXPOSURE", sc.view_settings.exposure))
sc.timeline_markers.clear()
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frames")
for spec in a[3:]:
    cam, l0, l1, o0 = spec.split(":")
    sc.camera = bpy.data.objects[cam]
    for i, f in enumerate(range(int(l0), int(l1) + 1)):
        p = os.path.join(out, f"f_{int(o0) + i:04d}.png")
        if os.path.exists(p):
            continue
        t = time.time()
        sc.frame_set(f)
        sc.render.filepath = p + ".tmp.png"
        bpy.ops.render.render(write_still=True)
        os.replace(p + ".tmp.png", p)
        print(f"SHOT {cam} local {f} -> {os.path.basename(p)} {time.time() - t:.1f}s", flush=True)
print("BLEND DONE", blend, flush=True)
