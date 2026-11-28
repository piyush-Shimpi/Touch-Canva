import bpy, sys
a=sys.argv[sys.argv.index("--")+1:]
bpy.ops.wm.open_mainfile(filepath="hideout.blend")
sc=bpy.context.scene; sc.render.resolution_percentage=int(a[0]); sc.cycles.samples=int(a[1])
for spec in a[2:]:
    cam,f=spec.split(":"); sc.camera=bpy.data.objects[cam]; sc.frame_set(int(f))
    sc.render.filepath=f"prev/{cam}_{f}.png"; bpy.ops.render.render(write_still=True)
