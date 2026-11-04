# Oil-Rig-Legs cover: a separate hero render of the WHOLE platform (playbook Cover section), not a frame from the video.
# Re-uses the platform model of build_scene.py (exec'd with COVER=1, no timeline export), frozen at one pose, with its own camera + light.
#   A: the finished fixed platform (deck on the jacket, crane ship gone) in the cut ocean, low 3/4 view from the front left, legs running all the way
#      down to the seabed and the piles deep in the mud; warm low sun. Title "WHAT HOLDS / IT UP?!"
#   B: the jacket mid-upend, half underwater at a steep angle with the barge behind it, seen from just above the waves.
#      (cyan = the flooded lower legs). Title "IT FLIPS / UPRIGHT?!"
# The subject fills the 3:4 crop (y 240-1680); the title goes in the sky at the top. No labels, captions or arrows.
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, math, os, sys
from mathutils import Vector
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT, DEV = arg("--opt", "A"), arg("--cycles-device", "OPTIX")
if DEV.upper() == "CPU": sys.argv.append("--cpu")
os.environ["COVER"] = "1"
HERE_C = os.path.dirname(os.path.abspath(__file__))
G = {"__file__": os.path.join(HERE_C, "build_scene.py"), "__name__": "__cover__"}
exec(compile(open(G["__file__"], encoding="utf-8").read(), G["__file__"], "exec"), G)
scene, cam, TGT, cam_d = G["scene"], G["cam"], G["TGT"], G["cam_d"]
C, FPS = G["C"], G["FPS"]
t = (C["fixed"] + 0.3) if OPT == "A" else (C["swings"] + 0.15)
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
D, JY = G["D"], G["JY"]
if OPT == "A":
    cam.location = (-62.0, -118.0, 26.0); TGT.location = (0.0, JY, 47.0); cam_d.lens = 30
    for o in G["STREAKS"]:   # no wave streaks on the cover
        o.animation_data_clear(); o.hide_render = True
    sun = bpy.data.objects["Sun"]; sun.rotation_euler = (math.radians(68), math.radians(-12), math.radians(-40)); sun.data.color = (1.0, 0.82, 0.62)
else:
    cam.location = (-74.0, -78.0, D + 10.0); TGT.location = (-26.0, JY, D - 4.0); cam_d.lens = 28
for o in list(bpy.data.objects):     # nothing from the typography helpers
    if o.name.startswith(("Buoy_", "Pull_", "LevelLine", "DepthBracket", "Br_")): o.animation_data_clear(); o.hide_render = True
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
