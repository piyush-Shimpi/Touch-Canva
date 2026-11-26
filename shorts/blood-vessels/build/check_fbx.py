import bpy, os
bpy.ops.wm.read_factory_settings(use_empty=True)
A = os.path.join(os.path.dirname(__file__), "..", "assets")
for f in ("Remy.fbx", "Battlecry.fbx"):
    before = set(bpy.data.objects)
    r = bpy.ops.import_scene.fbx(filepath=os.path.join(A, f))
    new = [o for o in bpy.data.objects if o not in before]
    print("==", f, r, [(o.name, o.type) for o in new])
    for o in new:
        if o.type == "ARMATURE":
            print(" bones", len(o.data.bones), [b.name for b in o.data.bones][:12])
            ad = o.animation_data
            print(" action", ad.action.name if ad and ad.action else None, ad.action.frame_range[:] if ad and ad.action else None)
        if o.type == "MESH":
            print(" mesh", o.name, len(o.data.vertices), [m.name for m in o.data.materials], o.dimensions[:])
print("images", [(i.name, i.size[:], i.packed_file is not None, i.filepath) for i in bpy.data.images])
