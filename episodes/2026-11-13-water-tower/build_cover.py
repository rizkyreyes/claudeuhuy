# Water-tower cover: a separate hero render of the WHOLE water tower (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), frozen at a chosen moment, near half put back
# (whole, uncut), own camera + key light. No labels, captions, arrows, gauges or bars from the video.
#   A: low from the street, the tank high overhead against the sky, houses tiny at the bottom.   "WHY SO / HIGH?!"
#   B: the town at night, the tower standing over the dark houses with the street lamps on.     "NO PUMP / NEEDED?!"
#   C: from above the rooftops at the tower's height: the tank towering over the whole town.     "HEIGHT IS / PRESSURE?!"
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
t = {"A": 1.0, "B": C["nobody"] + 0.6, "C": 1.0}[OPT]
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
# whole tower: near half back in place and visible
NEAR = G["NEAR"]; NEAR.animation_data_clear(); NEAR.location = (0, 0, 0)
for o in NEAR.children_recursive:
    if o.animation_data: o.animation_data_clear()
    o.hide_render = False
for o in bpy.data.objects:
    if o.name.startswith(("Arr", "GravityArrow", "HeightBar", "Spill", "LevelBox", "Cut")): o.animation_data_clear(); o.hide_render = True
if OPT == "A":
    cam.location = (10.0, -26.0, 1.6); TGT.location = (0.0, 0.0, 30.0); cam_d.lens = 15
elif OPT == "B":
    cam.location = (18.0, -44.0, 4.0); TGT.location = (1.0, 0.0, 22.0); cam_d.lens = 17
else:
    cam.location = (30.0, -40.0, 24.0); TGT.location = (0.0, 0.0, 23.0); cam_d.lens = 20
for o in bpy.data.objects:   # no tree between the camera and the tower
    if o.name.startswith(("Crown", "Trunk")) and (o.matrix_world.translation.y < 0 or o.name.startswith("Crown") and min(v.co.y for v in o.data.vertices) < 0): o.hide_render = True
if OPT == "B":
    w = bpy.data.materials["Window"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]; bpy.data.materials["Window"].node_tree.animation_data_clear(); w.default_value = 2.0
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.2 if OPT != "B" else 0.0; key.color = (1.0, 0.90, 0.78)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(62), 0, math.radians(-50))
if OPT == "B":   # moonlit rim on the tank so it reads against the night sky
    rim = bpy.data.lights.new("CoverRim", "AREA"); rim.energy = 40000; rim.size = 20; rim.color = (0.55, 0.75, 1.0)
    ro = bpy.data.objects.new("CoverRim", rim); scene.collection.objects.link(ro); ro.location = (-30, 30, 60); ro.rotation_euler = (math.radians(-40), math.radians(-30), 0)
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
