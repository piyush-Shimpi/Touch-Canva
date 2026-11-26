import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
H = os.path.dirname(__file__)
bpy.ops.import_scene.fbx(filepath=os.path.join(H, "..", "assets", "Battlecry.fbx"))
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == "ARMATURE")
print("arm scale", arm.scale[:], "loc", arm.location[:], "rot", arm.rotation_euler[:])
cam = bpy.data.objects.new("C", bpy.data.cameras.new("C")); sc.collection.objects.link(cam)
cam.location = (0, -4.2, 1.0); cam.rotation_euler = (1.5708, 0, 0); sc.camera = cam
l = bpy.data.objects.new("S", bpy.data.lights.new("S", "SUN")); sc.collection.objects.link(l); l.rotation_euler = (0.8, 0.2, 0.5); l.data.energy = 4
sc.world = bpy.data.worlds.new("W"); sc.world.color = (0.5, 0.6, 0.8)
sc.render.engine = "CYCLES"; sc.cycles.samples = 8; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 270, 480
os.makedirs(os.path.join(H, "prev"), exist_ok=True)
for f in (1, 15, 30, 45, 60, 75, 86):
    sc.frame_set(f)
    if f == 1:
        b = [o for o in sc.objects if o.type == "MESH"]
        import mathutils
        print("Body bbox z", min((o.matrix_world @ mathutils.Vector(c)).z for o in b for c in o.bound_box), max((o.matrix_world @ mathutils.Vector(c)).z for o in b for c in o.bound_box))
    sc.render.filepath = os.path.join(H, "prev", f"a_{f:03d}.png")
    bpy.ops.render.render(write_still=True)
