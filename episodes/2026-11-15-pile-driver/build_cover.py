# Pile-driver cover: a separate hero render of the WHOLE rig / hammer (playbook Cover section), not a frame from the video's framing.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), own camera + key light, at the moment the blast throws
# the ram up. No labels, captions or arrows.
#   A: the hammer on top of the pile from below, leads rising into the sky, ram flying out of the cylinder, blast glow + exhaust.  "IT LIFTS / ITSELF?!"
#   B: the cut hammer up close: fire in the gap, ram thrown up out of the yellow cylinder.                                            "DIESEL / INSIDE?!"
#   C: the finished tower standing on its piles in the cut ground, the rig firing on the next pile.                                   "WHAT HOLDS / IT UP?!"
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
scene, cam, TGT, cam_d, C, FPS, HZ = G["scene"], G["cam"], G["TGT"], G["cam_d"], G["C"], G["FPS"], G["HZ"]
t = G["T_THROW"] + 0.55 if OPT != "C" else G["CTA_B"][2] + 0.12
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
for o in bpy.data.objects:   # nothing from the explainer layer
    if o.name.startswith(("ArrowUp", "ArrowDown", "GhostPile", "GhostTower")):
        o.animation_data_clear(); o.hide_render = True
z = HZ(t)
def steady_bsdf(mat, strength):
    nt = bpy.data.materials[mat].node_tree
    if nt.animation_data: nt.animation_data_clear()
    nt.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = strength
steady_bsdf("Ram", 0.0); steady_bsdf("Leads", 0.0); steady_bsdf("Helmet", 0.0); steady_bsdf("Cushion", 0.0)
fn = bpy.data.materials["Fire"].node_tree
if fn.animation_data: fn.animation_data_clear()
for n in fn.nodes:
    if n.type == "EMISSION": n.inputs["Strength"].default_value = 2.2; n.inputs["Color"].default_value = (1.0, 0.36, 0.05, 1)
    if n.type == "MIX_SHADER": n.inputs[0].default_value = 1.0
bl = bpy.data.lights["BlastLight"]; bl.animation_data_clear(); bl.energy = 900.0
if OPT == "A":
    cam.location = (4.5, -9.5, z - 3.0); TGT.location = (0.0, 0.0, z + 5.0); cam_d.lens = 17
elif OPT == "B":
    cam.location = (1.8, -7.8, z + 4.4); TGT.location = (0.0, 0.0, z + 4.2); cam_d.lens = 24
else:
    cam.location = (-1.0, -52.0, 10.0); TGT.location = (-2.0, 0.0, 6.0); cam_d.lens = 22
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.0; key.color = (1.0, 0.90, 0.78)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(70), 0, math.radians(-30))
fl = bpy.data.objects.get("SectionFill")
if fl:
    fl.data.animation_data_clear(); fl.data.energy = 2500.0 * min(1.0, ((cam.location - TGT.location).length / 45.0) ** 2) + 40
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
