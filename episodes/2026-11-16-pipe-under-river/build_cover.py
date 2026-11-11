# Pipe-under-river cover: a separate hero render of the WHOLE crossing (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export), own camera + key light.
# No labels, captions, arrows, rings or other explainer layers.
#   A: the crossing as a cut block from above-left: river, banks, the gas main arcing under the riverbed, glowing.   "THEY DRILLED / UNDER IT?!"
#   B: straight-on section: a boat on the river, the glowing pipe far below the riverbed.                           "A PIPE / UNDER THIS?!"
#   C: the drill rig on the bank, its rod diving down under the river, the drill head glowing mid-way.              "IT STEERS / UNDERGROUND?!"
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
t = C["boats"] + 0.5 if OPT != "C" else C["under2"] + 0.2
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
for o in bpy.data.objects:   # nothing from the explainer layer
    if o.name.startswith(("Ring", "LocatorMark", "PushArrows", "StraightArrow", "WallArrows", "FracCrack", "Plume", "Cloud", "Chunk", "MudDot",
                          "Cutting", "Weld", "OtherPipe", "Route", "StraightLine", "GhostPipe", "Trench", "SpoilHeap", "Demo")):
        o.animation_data_clear(); o.hide_render = True
def steady(mat, strength, rgb=None):
    nt = bpy.data.materials[mat].node_tree
    if nt.animation_data: nt.animation_data_clear()
    b = nt.nodes["Principled BSDF"]; b.inputs["Emission Strength"].default_value = strength
    if rgb: b.inputs["Emission Color"].default_value = (*rgb, 1)
steady("GasPipe", 1.2 if OPT != "C" else 0.0, (1.0, 0.70, 0.15))
steady("Bit", 2.0 if OPT == "C" else 0.0, (1.0, 0.62, 0.15))
steady("Sonde", 1.5 if OPT == "C" else 0.0)
steady("Rod", 0.0)
if OPT == "A":
    cam.location = (-34.0, -36.0, 16.0); TGT.location = (0.0, 6.0, -8.0); cam_d.lens = 20
elif OPT == "B":
    b = bpy.data.objects["BoatA"]; b.animation_data_clear(); b.location = (-1.0, 7.0, -0.45); b.scale = (2.4, 2.4, 2.4); b.rotation_euler = (0, 0, math.radians(90))
    cam.location = (2.0, -19.0, 0.5); TGT.location = (0.0, 4.0, -6.5); cam_d.lens = 20
else:
    hp = bpy.data.objects["HeadPivot"]; hp.scale = (2.5, 2.5, 2.5)
    cam.location = (-82.0, -26.0, 10.0); TGT.location = (-44.0, 0.0, -3.0); cam_d.lens = 22
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.0; key.color = (1.0, 0.90, 0.78)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(70), 0, math.radians(-30))
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
