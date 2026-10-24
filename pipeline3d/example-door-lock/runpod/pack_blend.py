# Make a self-contained, final-quality .blend for the cloud render.
# Usage: blender -b lock.blend -P pack_blend.py -- <out.blend> [samples]
import bpy, sys
argv = sys.argv[sys.argv.index("--") + 1:]
out, samples = argv[0], int(argv[1]) if len(argv) > 1 else 64
s = bpy.context.scene
s.render.resolution_percentage = 100
s.cycles.samples = samples
s.cycles.device = "GPU"
s.render.use_persistent_data = True
s.render.use_motion_blur = True
s.render.image_settings.file_format = "PNG"
bpy.ops.file.pack_all()
missing = [i.name for i in bpy.data.images if i.source == "FILE" and not i.packed_file]
print("PACKED", [i.name for i in bpy.data.images if i.packed_file], "MISSING", missing)
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True)
print("SAVED", out, "frames", s.frame_start, s.frame_end, "samples", samples)
