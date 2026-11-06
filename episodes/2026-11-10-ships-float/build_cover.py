# Ships-float cover: a separate hero render of the WHOLE ship (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), frozen loaded at its waterline (draft 5) with the
# near half put back (uncut ship), its own camera + key light. No labels, captions or arrows.
#   A: low from the water at the bow quarter, the loaded steel ship towering over the camera. Title "SOLID STEEL / STILL FLOATS?!"
#   B: over-under: the sea is cut in front of the (uncut) ship, so the hull below the waterline shows through the water section,
#      how deep it sits. Title "HOW IS THIS / NOT SINKING?!"
#   C: over-under, wider and deeper: the ship floating above, a small solid steel block (drawn 2x) lying on the sea bed below it.
#      Title "THIS FLOATS" (top) / "THIS SINKS?!" (bottom, by the block)
# The subject fills the 3:4 crop (y 240-1680); the title goes in the sky at the top.
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B|C --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, math, os, sys
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT, DEV = arg("--opt", "A"), arg("--cycles-device", "OPTIX")
if DEV.upper() == "CPU": sys.argv.append("--cpu")
os.environ["COVER"] = "1"
HERE_C = os.path.dirname(os.path.abspath(__file__))
G = {"__file__": os.path.join(HERE_C, "build_scene.py"), "__name__": "__cover__"}
exec(compile(open(G["__file__"], encoding="utf-8").read(), G["__file__"], "exec"), G)
scene, cam, TGT, cam_d, C, FPS = G["scene"], G["cam"], G["TGT"], G["cam_d"], G["C"], G["FPS"]
t = C["tell"] + 2.0                        # CTA: loaded, draft 5, no flooding, no ballast, nothing pitched
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
COV = G["COVER"]; COV.animation_data_clear(); COV.location = (0, 0, 0)
for o in [COV] + list(COV.children_recursive):   # put the near half back: the ship is shown whole, uncut
    o.animation_data_clear(); o.hide_render = False; o.hide_viewport = False
NEAR = G["NEAR"]
for o in [NEAR] + list(NEAR.children_recursive):
    o.animation_data_clear(); o.hide_render = OPT != "A"; o.location = (0, 0, 0) if o == NEAR else o.location
G["AIR_FAC"].default_value = 0.0
for o in (G["AIRV"], G["DISPV"], G["MOTES"], G["GHB"], G["FLAT"], G["LL"]):
    o.animation_data_clear(); o.hide_render = True
    for c in o.children_recursive: c.animation_data_clear(); c.hide_render = True
for o in bpy.data.objects:                  # no arrows from the video
    if "Weight" in o.name or "Buoy" in o.name: o.animation_data_clear(); o.hide_render = True
B = G["BLOCK"]; B.animation_data_clear(); B.hide_render = OPT != "C"
B.location = (-3.0, 3.0, G["SEA_Z0"] + 2.4); B.scale = (2.0, 2.0, 2.0); B.rotation_euler = (0, 0, math.radians(20))
if OPT == "A":
    cam.location = (27.0, -21.0, 2.2); TGT.location = (2.0, 0.0, 6.5); cam_d.lens = 22
elif OPT == "B":
    cam.location = (14.0, -33.0, -1.0); TGT.location = (2.0, 0.0, 0.5); cam_d.lens = 22
else:
    cam.location = (12.0, -40.0, -4.0); TGT.location = (0.0, 0.0, -7.0); cam_d.lens = 22
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.6; key.color = (1.0, 0.93, 0.82)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(55), 0, math.radians(-40))
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
