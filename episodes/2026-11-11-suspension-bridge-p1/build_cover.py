# Suspension-bridge-p1 cover: a separate hero render of the WHOLE subject (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), frozen at a chosen moment, own camera + key light.
# No labels, captions or arrows from the video, no ghost deck.
#   A: low from the water below the left tower: towers + the two finished main cables, no road. Title "27,572 WIRES / IN ONE CABLE?!"
#   B: high on the catwalk: the spinning wheel mid-span over the sea, the glowing live wire behind it. Title "SPUN IN / THE SKY?!"
#   C: wide three-quarter of the whole bridge: anchorages, towers, cables, catwalks, no deck. Title "A BRIDGE / WITH NO ROAD?!"
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
CY, TX, TH, cable_z = G["CY"], G["TX"], G["TH"], G["cable_z"]
t = (C["wheel"] + 2.4) if OPT == "B" else (C["but"] + 0.15)
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
for o in bpy.data.objects:
    if o.name.startswith(("GhostDeck", "PullArrow")): o.animation_data_clear(); o.hide_render = True
    if OPT == "A" and o.name.startswith(("Walk", "Rail")): o.animation_data_clear(); o.hide_render = True
if OPT == "A":
    cam.location = (-34.0, -44.0, 3.0); TGT.location = (-50.0, 0.0, 44.0); cam_d.lens = 16
elif OPT == "B":
    W = G["WHEELS"][0][0]; p = W.matrix_world.translation.copy()
    cam.location = (p.x + 7.0, p.y - 9.0, p.z + 9.0); TGT.location = (p.x - 3.0, p.y, p.z - 1.0); cam_d.lens = 26
else:
    cam.location = (95.0, -150.0, 26.0); TGT.location = (-5.0, 0.0, 34.0); cam_d.lens = 22
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.4; key.color = (1.0, 0.93, 0.82)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(55), 0, math.radians(-40))
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
