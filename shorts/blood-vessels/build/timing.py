import bpy, os, sys, time
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(__file__), "vessels.blend"))
sc = bpy.context.scene
sc.render.resolution_percentage = int(sys.argv[1])
sc.frame_start, sc.frame_end = int(sys.argv[2]), int(sys.argv[3])
sc.render.filepath = os.path.join(os.path.dirname(__file__), "prev", "t_####")
t = time.time(); bpy.ops.render.render(animation=True)
print("PER FRAME", (time.time() - t) / (sc.frame_end - sc.frame_start + 1))
