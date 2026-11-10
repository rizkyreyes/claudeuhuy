# Nuclear-plant cover: a separate hero render of the WHOLE plant (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), frozen at t = 1 s (containment closed), own camera +
# key light. No labels, captions, flow dots or bubbles. The paradox cue is the white vapor plume over the cooling tower: the plant is a kettle.
#   A: worm's-eye from the grass: the dome close on the left, the cooling tower and its plume towering on the right.  "A GIANT / KETTLE?!"
#   B: aerial three-quarter: dome, turbine hall, power line and the steaming tower in one frame.                          "IT JUST / BOILS WATER?!"
#   C: low golden-hour light over the plant, long shadows, the plume lit warm against a deep sky.                          "URANIUM / KETTLE?!"
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
scene, cam, TGT, cam_d, FPS = G["scene"], G["cam"], G["TGT"], G["cam_d"], G["FPS"]
scene.frame_set(int(round(1.0 * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
NEAR = G["NEAR"]; NEAR.animation_data_clear(); NEAR.location = (0, 0, 0)
for o in [NEAR] + list(NEAR.children_recursive):
    if o.animation_data: o.animation_data_clear()
    o.hide_render = False
for o in bpy.data.objects:
    if o.name.startswith(("Dot", "Bubble", "Neutron")): o.animation_data_clear(); o.hide_render = True
if OPT == "A":
    cam.location = (-8.0, -66.0, 1.2); TGT.location = (40.0, 10.0, 50.0); cam_d.lens = 16
elif OPT == "B":
    cam.location = (-38.0, -52.0, 34.0); TGT.location = (34.0, 10.0, 25.0); cam_d.lens = 21
else:
    cam.location = (22.0, -84.0, 5.0); TGT.location = (40.0, 8.0, 52.0); cam_d.lens = 19
for o in bpy.data.objects:   # no tree between the camera and the plant
    if o.name.startswith("YardTree") or (o.name.startswith("Tree") and o.matrix_world.translation.y < 0): o.hide_render = True
for o in bpy.data.objects:
    if o.name.startswith("House"): o.hide_render = True
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.0; key.color = (1.0, 0.90, 0.78)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(62), 0, math.radians(-50))
if OPT == "C":   # golden hour: low warm sun, dimmer cooler sky
    sun = bpy.data.objects["Sun"]; sun.rotation_euler = (math.radians(80), math.radians(-10), math.radians(-70)); sun.data.energy = 4.0; sun.data.color = (1.0, 0.68, 0.40)
    key.energy = 0.0
    try:
        sky = next(n for n in scene.world.node_tree.nodes if n.type == "TEX_SKY"); sky.sun_elevation = math.radians(6); sky.sun_rotation = math.radians(250)
    except Exception: pass
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
