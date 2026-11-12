# Lightning-rod cover: a separate hero render of the WHOLE house with its lightning protection (playbook Cover section), not a frame of the
# video's framing. Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), own camera + key light, at the storm strike:
# the bolt on the ridge rod, the current glowing gold down both cables into the ground rods, the windows still lit. No labels, captions, arrows.
#   A: the whole house + cut lawn block, bolt on the ridge, both cables + ground rods glowing, warm windows.   "HIT BY LIGHTNING / STILL FINE?!"
#   B: low close-up on the ridge rod taking the bolt, the glow running down the rake.                        "IT DOESN'T / PULL IT IN?!"
#   C: the front corner with the cut soil: glowing cable diving into the ground rod, the bolt behind.        "WHERE DOES / IT GO?!"
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
t = C["vanishes"] - 0.1
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
def show(o, on=True):
    o.animation_data_clear(); o.hide_render = not on; o.hide_viewport = not on
for o in bpy.data.objects:
    if o.name.startswith("BoltStorm"): show(o, True)
    elif o.name.startswith(("Bolt", "Ring", "RoofArc", "DemoSpark", "Spill", "Red", "PulseRoad", "PulseBends", "GlowHook", "BondGlow", "SharpCorner")): show(o, False)
    elif o.name.startswith(("StormL", "StormR")):
        show(o, True); cu = o.data
        if cu.animation_data: cu.animation_data_clear()
        cu.bevel_factor_start = 0.0; cu.bevel_factor_end = 1.0
    elif o.name in ("FrontWall", "CableL", "CableR", "RidgeConductor", "Bond", "GroundRodL", "GroundRodR", "ClampL", "ClampR") or o.name.startswith(("AirTerminal", "FrontOpening", "FrontTrim")):
        o.hide_render = False
for cu in ("CableL", "CableR", "RidgeConductor", "Bond"):
    c_ = bpy.data.curves[cu]
    if c_.animation_data: c_.animation_data_clear()
    c_.bevel_factor_start, c_.bevel_factor_end = 0.0, 1.0
def steady(mat, strength):
    m = bpy.data.materials[mat]; nt = m.node_tree
    if nt.animation_data: nt.animation_data_clear()
    for n in nt.nodes:
        if n.type == "BSDF_PRINCIPLED": n.inputs["Emission Strength"].default_value = strength
        if n.type == "EMISSION": n.inputs["Strength"].default_value = strength
steady("GroundRod", 3.0); steady("Copper", 0.0); steady("Cloud", 0.35); steady("Wood", 0.0)
for k in range(4): steady(f"AirTerminal{k}Mat", 0.0)
steady("AirTerminal1Mat", 6.0)
for L_, e_ in (("StrikeLight", 2500.0), ("FlashSun", 2.0), ("FireLight", 0.0), ("SparkLight", 0.0)):
    l = bpy.data.lights[L_]; l.animation_data_clear(); l.energy = e_
bpy.data.objects["StrikeLight"].animation_data_clear()
bpy.data.objects["StrikeLight"].location = (G["R_X"][1], -1.5, G["ZR"] + 2.0)
wbg = next(n for n in scene.world.node_tree.nodes if n.type == "BACKGROUND")
if scene.world.node_tree.animation_data: scene.world.node_tree.animation_data_clear()
wbg.inputs["Strength"].default_value = 1.6
try: scene.view_settings.look = "AgX - Punchy"
except Exception: pass
if OPT == "A":
    cam.location = (-8.0, -21.0, 2.6); TGT.location = (-0.5, 0.0, 5.6); cam_d.lens = 24
elif OPT == "B":
    cam.location = (-12.5, -6.5, 12.0); TGT.location = (-2.5, 0.0, 10.0); cam_d.lens = 26
else:
    cam.location = (-12.5, -14.5, 3.6); TGT.location = (-6.0, -4.0, 3.2); cam_d.lens = 20
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 0.8; key.color = (0.85, 0.9, 1.0)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(65), 0, math.radians(-35))
fl = bpy.data.objects.get("SectionFill")
if fl:
    fl.data.animation_data_clear(); fl.data.energy = 1800.0 * min(1.0, ((cam.location - TGT.location).length / 45.0) ** 2) + 40
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
