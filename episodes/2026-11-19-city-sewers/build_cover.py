# City-sewers cover: a separate hero render (playbook Cover section), not a frame of the video's framing. Re-uses the model of
# build_scene.py (exec'd with COVER=1, no timeline export) at a chosen moment, with its own camera + key light. No labels, captions, arrows
# from the typography (the gold route / cyan slope arrows are part of the 3D model).
#   A: the house cut open, the gold route from the toilet down the stack, along the tilted lateral into the main under the street.  "WHERE DOES / IT GO?!"
#   B: the street cut along its main: houses on top, the main tilting downhill with the flow, slope arrows.                         "IT ALL ROLLS / DOWNHILL?!"
#   C: the lift station: wet well full of sewage, the pump lit, the force main pushing it up to a higher manhole.                    "PUMPED / UPHILL?!"
# Subject fills the 3:4 crop (y 240-1680); the title goes in the sky at the top.
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
T = {"A": C["sewer"] + 0.1, "B": C["tilts"] + 0.6, "C": C["pushes"] + 1.3}[OPT]
scene.frame_set(int(round(T * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
if OPT == "A":
    cam.location = (-11.0, -12.5, 0.2); TGT.location = (2.5, 0.0, -2.2); cam_d.lens = 20
    for nm in ("SlugAMesh",): bpy.data.objects[nm].animation_data_clear(); bpy.data.objects[nm].hide_render = True
elif OPT == "B":
    cam.location = (104.0, -12.0, 0.2); TGT.location = (120.0, 0.0, -3.2); cam_d.lens = 22
else:
    cam.location = (183.5, -15.0, -0.5); TGT.location = (191.5, 0.0, -4.6); cam_d.lens = 24
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.2; key.color = (1.0, 0.95, 0.9)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(60), 0, math.radians(-40))
fl = bpy.data.objects.get("SectionFill")
if fl:
    fl.data.animation_data_clear(); fl.data.energy = max(150.0, 1500.0 * min(1.6, ((cam.location - TGT.location).length / 45.0) ** 2))
try: scene.view_settings.look = "AgX - Punchy"
except Exception: pass
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
