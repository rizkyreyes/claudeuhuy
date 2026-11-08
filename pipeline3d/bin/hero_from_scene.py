# Hero cover render for older episodes without build_cover.py: builds the episode scene (build_scene.py, stopped before the
# timeline export so timeline.json is untouched), freezes it at --frame, puts in its own camera, hides helpers, renders one PNG.
#   blender -b -y -P hero_from_scene.py -- --ep <episode dir> --frame N [--cam x,y,z --tgt x,y,z --lens L] [--hide a,b] [--orbit deg --dist f --up dz]
#        --pct 25 --samples 16 --out file.png [--cpu]
import bpy, math, os, sys
from mathutils import Vector
A = sys.argv[sys.argv.index("--") + 1:]
arg = lambda n, d=None: A[A.index(n) + 1] if n in A else d
EP = os.path.abspath(arg("--ep")); src = os.path.join(EP, "build_scene.py")
code = open(src, encoding="utf-8").read()
code = code[:code.index("# ---------- export cues")]
sys.argv = [sys.argv[0], "--"] + (["--cpu"] if "--cpu" in A else [])
G = {"__file__": src, "__name__": "__hero__"}
exec(compile(code, src, "exec"), G)
scene, cam, TGT, cam_d = G["scene"], G["cam"], G["TGT"], G["cam_d"]
scene.frame_set(int(arg("--frame", "1")))
c0, t0 = cam.matrix_world.translation.copy(), TGT.matrix_world.translation.copy()
print("VIDEO_CAM", tuple(round(v, 2) for v in c0), "TGT", tuple(round(v, 2) for v in t0), "LENS", round(cam_d.lens, 1))
for o in (cam, TGT): o.animation_data_clear()
cam_d.animation_data_clear()
for o in (cam, TGT):
    o.parent = None
    o.constraints.clear() if o is TGT else None
cam.location, TGT.location = c0, t0
if arg("--cam"): cam.location = Vector([float(v) for v in arg("--cam").split(",")])
if arg("--tgt"): TGT.location = Vector([float(v) for v in arg("--tgt").split(",")])
if arg("--orbit") or arg("--dist") or arg("--up"):
    d = cam.location - TGT.location
    d.rotate(__import__("mathutils").Euler((0, 0, math.radians(float(arg("--orbit", "0"))))))
    d *= float(arg("--dist", "1")); d.z += float(arg("--up", "0"))
    cam.location = TGT.location + d
if arg("--lens"): cam_d.lens = float(arg("--lens"))
for key in [k for k in arg("--hide", "").split(",") if k]:
    for o in bpy.data.objects:
        if key.lower() in o.name.lower(): o.animation_data_clear(); o.hide_render = True
print("HERO_CAM", tuple(round(v, 2) for v in cam.location), "TGT", tuple(round(v, 2) for v in TGT.location), "LENS", cam_d.lens)
if arg("--sun"):
    e, az, el = [float(v) for v in arg("--sun").split(",")]
    L = bpy.data.lights.new("HeroSun", "SUN"); L.energy = e; L.color = (1.0, 0.88, 0.72); L.angle = math.radians(2)
    lo = bpy.data.objects.new("HeroSun", L); scene.collection.objects.link(lo); lo.rotation_euler = (math.radians(90 - el), 0, math.radians(az))
if arg("--dof"):
    cam_d.dof.use_dof = True; cam_d.dof.focus_object = TGT; cam_d.dof.aperture_fstop = float(arg("--dof"))
r = scene.render; r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "25"))
scene.cycles.samples = int(arg("--samples", "16"))
r.filepath = os.path.abspath(arg("--out")); bpy.ops.render.render(write_still=True); print("HERO", r.filepath)
