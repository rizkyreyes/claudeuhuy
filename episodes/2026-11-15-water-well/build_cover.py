# Water-well cover: a separate hero render of the WHOLE well (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), frozen when everything is installed (casing, screen,
# grout, pump, pressure tank), own camera + key light. No labels, captions, counters, bars or rain from the video.
#   A: the yard as a cut block from above-left: lawn, house, and the well running 140 ft down the cut face.    "140 FEET / DOWN?!"
#   B: down at the bottom: the glowing pump inside the slotted screen, cyan water rising up the pipe.        "IT PUSHES / UP?!"
#   C: from the lawn: the well cap and the casing dropping into the ground, house behind.                   "WATER FROM / YOUR YARD?!"
# Subject fills the 3:4 crop (y 240-1680); the title goes in the sky / soil at the top.
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
t = C["more"] + 0.6
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
for o in bpy.data.objects:   # nothing from the explainer layer
    if o.name.startswith(("Rain", "Dirt", "Puddle", "DepthBar", "DepthTop", "SuctionLimit", "Brk", "AirArrow", "InDot", "Grain", "Chunk", "FlowHouse")):
        o.animation_data_clear(); o.hide_render = True
# the pump running: steady gold glow, pipe glowing cyan
for m in ("Pump", "DropPipe"):
    nt = bpy.data.materials[m].node_tree
    if nt.animation_data: nt.animation_data_clear()
bpy.data.materials["Pump"].node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (1.0, 0.62, 0.15, 1)
bpy.data.materials["Pump"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.8 if OPT != "C" else 0.0
bpy.data.materials["Pump"].node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.75, 0.48, 0.12, 1)
bpy.data.materials["DropPipe"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.6 if OPT != "C" else 0.0
if OPT == "A":
    cam.location = (-11.0, -24.0, 6.0); TGT.location = (3.5, 3.0, -15.0); cam_d.lens = 20
elif OPT == "B":
    cam.location = (1.8, -6.2, -31.5); TGT.location = (0.0, 0.0, -33.8); cam_d.lens = 20
else:
    cam.location = (-2.6, -8.5, -1.0); TGT.location = (0.6, 0.0, -5.0); cam_d.lens = 18
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.0; key.color = (1.0, 0.90, 0.78)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(70), 0, math.radians(-30))
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
