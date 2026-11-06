# Canal-locks cover: a separate hero render of the WHOLE lock flight (playbook Cover section), not a frame from the video.
# Re-uses the model of build_scene.py (exec'd with COVER=1, no timeline export) with the near wall put back (uncut), frozen at one pose
# (chambers stepped 5 / 10 / 15, the ship on the top step at lake level), with its own camera + key light. No labels, captions or arrows.
#   A: high three-quarter view from the front, the ship big on the top step, the lower steps falling away to the left;
#      the chamber water glows faintly cyan so the three water levels read as steps. Title "85 FT UPHILL / NO PUMPS?!"
#   B: from above the lake, behind the ship, looking down the staircase of chambers to the sea. Title "SHIPS CLIMB / STAIRS?!"
# The subject fills the 3:4 crop (y 240-1680); the title goes in the sky at the top.
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
t = C["floating"] - 0.2                       # chambers at 5 / 10 / 15, ship on the top step, gates closed
scene.frame_set(int(round(t * FPS)) + 1)
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
COV = G["COVER"]; COV.animation_data_clear(); COV.location = (0, 0, 0)
for o in [COV] + list(COV.children_recursive):   # put the near wall back: the subject is shown whole, uncut
    o.animation_data_clear(); o.hide_render = False; o.hide_viewport = False
for o in list(bpy.data.objects):          # no helper geometry from the video
    if o.name.startswith(("Bar", "Line85", "Tick", "Gap", "Cable", "Fill", "Drain", "Save", "BasinRig", "Basin")) or o == G["SHIP2"] or o.parent == G["SHIP2"]:
        o.animation_data_clear(); o.hide_render = True
for k in range(3):
    b = G["WM"][k][1]; b.id_data.animation_data_clear()
    b.inputs["Emission Strength"].default_value = 0.35 if OPT == "A" else 0.2
if OPT == "A":
    cam.location = (52.0, -40.0, 62.0); TGT.location = (88.0, 0.0, 8.0); cam_d.lens = 28
else:
    cam.location = (142.0, 14.0, 72.0); TGT.location = (56.0, -2.0, 0.0); cam_d.lens = 28
key = bpy.data.lights.new("CoverKey", "SUN"); key.energy = 1.6; key.color = (1.0, 0.93, 0.82)
ko = bpy.data.objects.new("CoverKey", key); scene.collection.objects.link(ko); ko.rotation_euler = (math.radians(55), 0, math.radians(-40))
r = scene.render
r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128"))
out = os.path.abspath(arg("--out", os.path.join(HERE_C, "cover", f"hero_{OPT}.png")))
os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
