# Suspension-bridge-p2 cover: a separate hero render of the WHOLE subject (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), frozen at a chosen moment, own camera + key light.
# No labels, captions, arrows or ghosts from the video.
#   A: low from the water under the finished deck: the road hanging on its suspender ropes, nothing under the span. "HANGING / ON ROPES?!"
#   B: the gantry crane on the main cables lifting a deck section off the barge, mid-air.  "ROAD LIFTED / FROM A BOAT?!"
#   C: wide three-quarter of the whole bridge mid-build: deck sections growing out from both towers, gaps in the middle. "HALF / A ROAD?!"
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
LX, T_L0, T_L1, T_MO = G["LX"], G["T_L0"], G["T_L1"], G["T_MO"]
t = {"A": 1.0, "B": T_L0 + 0.55 * (T_L1 - T_L0), "C": T_MO + 1.6}[OPT]
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
for o in bpy.data.objects:
    if o.name.startswith(("Ghost", "SafetyNet", "NetPost")): o.animation_data_clear(); o.hide_render = True
for m in ("HeroCar",):
    b = bpy.data.materials[m].node_tree.nodes["Principled BSDF"]; b.inputs["Emission Strength"].driver_remove("default_value")
    if b.id_data.animation_data: b.id_data.animation_data_clear()
    b.inputs["Emission Strength"].default_value = 0.0
if OPT == "A":
    cam.location = (-14.0, -40.0, 3.0); TGT.location = (-24.0, 0.0, 34.0); cam_d.lens = 16
elif OPT == "B":
    cam.location = (LX + 10.0, -32.0, 16.0); TGT.location = (LX, 0.0, 30.0); cam_d.lens = 16
else:
    cam.location = (40.0, -105.0, 78.0); TGT.location = (0.0, 0.0, 26.0); cam_d.lens = 17
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.4; key.color = (1.0, 0.93, 0.82)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(55), 0, math.radians(-40))
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
