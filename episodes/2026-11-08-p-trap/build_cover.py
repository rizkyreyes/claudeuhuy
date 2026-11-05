# P-Trap cover: a separate hero render of the WHOLE sink drain (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export) with the front halves put back (uncut), frozen at one pose,
# with its own camera + light. No labels, captions or arrows.
#   A: the whole sink + P-trap from the front left, faucet running into the drain, strong key light on the white U-bend.
#      Title "ALWAYS FULL / OF WATER?!"
#   B: the J-bend unscrewed and lowered (slip nuts loose), seen steeply from above into its open end: the standing water sits inside it,
#      glowing. Title "THIS WATER / NEVER LEAVES?!"
# The subject fills the 3:4 crop (y 240-1680); the title goes in the dark area at the top.
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
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
t = (C["ptrap"] + 0.2) if OPT == "A" else (C["there"] + 0.25)
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
JB = G["JB"]; jz, jy = JB.location.z, JB.location.y
for o in G["cover"]:                       # put the front halves back: the subject is shown whole, uncut
    o.animation_data_clear(); o.hide_render = False; o.hide_viewport = False
    o.location = (0, jy, jz) if o.name in ("CoverJB", "CoverNut1", "CoverNut2") else (0, 0, 0)
for o in list(bpy.data.objects):          # no helper geometry from the video
    if o.name.startswith(("Br", "BanX", "Gas", "Air", "Rush", "SRush", "Refill")): o.animation_data_clear(); o.hide_render = True
if OPT == "A":
    cam.location = (-11.0, -24.0, 15.0); TGT.location = (0.8, 0.0, 14.0); cam_d.lens = 30
else:
    cam.location = (-4.0, -8.5, 19.0 + jz); TGT.location = (0.2, -1.0, 9.4 + jz); cam_d.lens = 30
    for o in G["WAT"]: o.hide_render = o.name != "Water0"
    G["B_RING"].inputs["Emission Strength"].default_value = 3.0
    G["M_WATER"].node_tree.animation_data_clear(); G["WGLOW"].outputs[0].default_value = 1.8; G["REDV"].outputs[0].default_value = 0.0
key = bpy.data.lights.new("CoverKey", "AREA"); key.size = 10.0; key.energy = 4000 if OPT == "A" else 2500
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.location = (-16.0, -22.0, 34.0)
c_ = ko.constraints.new("TRACK_TO"); c_.target = TGT; c_.track_axis = "TRACK_NEGATIVE_Z"; c_.up_axis = "UP_Y"
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
