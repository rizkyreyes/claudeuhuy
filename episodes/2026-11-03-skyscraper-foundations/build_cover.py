# Skyscraper cover: a separate hero render of the WHOLE tower and what it stands on (playbook Cover section), not a frame from the video.
# A diorama floating in a dark studio: glass tower with lit windows on a concrete raft, the ground cut open in front so the piles show.
#   A: tower and piles from the left, a low view that makes the tower tall ("WHY DOESN'T IT SINK?!")
#   B: from the right and higher, the piles glowing gold in the dark soil ("WHAT'S UNDER IT?!")
# The tower runs up behind the title band; the piles fill the lower half.
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT = arg("--opt", "A")
scene = bpy.context.scene
random.seed(7)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)

# ---------- materials ----------
def mat(name, rgb, rough=0.4, metallic=0.0, coat=0.0, emit=None, emit_s=0.0):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_s
    return m
GOLD = (1.0, 0.68, 0.2)
M_FRAME = mat("Frame", (0.20, 0.23, 0.28), 0.35, metallic=0.7)
M_GLASS = mat("Glass", (0.13, 0.27, 0.42), 0.1, metallic=0.2, coat=1.0)
M_LIT = mat("Lit", (0.9, 0.75, 0.5), 0.3, emit=(1.0, 0.78, 0.46), emit_s=1.3)
M_CONC = mat("Concrete", (0.62, 0.62, 0.60), 0.7)
M_PILE = mat("Pile", (0.82, 0.78, 0.68), 0.5, emit=GOLD, emit_s=0.0 if OPT == "A" else 0.3)
M_GRASS = mat("Grass", (0.10, 0.22, 0.07), 0.9)
M_TOP = mat("Topsoil", (0.20, 0.12, 0.06), 0.9)
M_CLAY = mat("Clay", (0.36, 0.25, 0.14), 0.9)
M_SAND = mat("Sand", (0.50, 0.40, 0.25), 0.9)
M_ROCK = mat("Rock", (0.20, 0.22, 0.25), 0.8)

# ---------- geometry helpers ----------
def obj_from(name, bm, m, smooth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); me.materials.append(m)
    return o

def add_box(bm, x0, x1, y0, y1, z0, z1):
    v = [bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in f])

def box(name, x0, x1, y0, y1, z0, z1, m, bevel=0.0):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from(name, bm, m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3; b.limit_method = "ANGLE"
    return o

# ---------- the tower: setback stages of curtain wall, each pane its own quad just proud of a dark frame ----------
def stage(name, hw, z0, z1, floors):
    # frame core, then panes on all four sides
    box(name + "Core", -hw, hw, -hw, hw, z0, z1, M_FRAME)
    cols = max(3, int(round(2 * hw / 0.62))); dz = (z1 - z0) / floors; dx = 2 * hw / cols
    gl, li = bmesh.new(), bmesh.new()
    for side in range(4):
        for fl in range(floors):
            for c in range(cols):
                a0, a1 = -hw + (c + 0.08) * dx, -hw + (c + 0.92) * dx
                z_0, z_1 = z0 + (fl + 0.1) * dz, z0 + (fl + 0.9) * dz
                bm = li if random.random() < 0.09 else gl
                q = hw + 0.012
                if side == 0: pts = [(a0, -q, z_0), (a1, -q, z_0), (a1, -q, z_1), (a0, -q, z_1)]
                elif side == 1: pts = [(q, a0, z_0), (q, a1, z_0), (q, a1, z_1), (q, a0, z_1)]
                elif side == 2: pts = [(a1, q, z_0), (a0, q, z_0), (a0, q, z_1), (a1, q, z_1)]
                else: pts = [(-q, a1, z_0), (-q, a0, z_0), (-q, a0, z_1), (-q, a1, z_1)]
                bm.faces.new([bm.verts.new(p) for p in pts])
    obj_from(name + "Glass", gl, M_GLASS); obj_from(name + "Lit", li, M_LIT)
stage("S1", 2.6, 0.7, 11.0, 30)
stage("S2", 2.05, 11.0, 17.0, 18)
stage("S3", 1.45, 17.0, 21.0, 12)
box("Crown", -0.95, 0.95, -0.95, 0.95, 21.0, 21.7, M_FRAME)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.09, radius2=0.015, depth=2.6)
s = obj_from("Spire", bm, M_FRAME, True); s.location = (0, 0, 23.0)
box("Podium", -3.1, 3.1, -3.1, 3.1, 0.0, 0.7, M_CONC)

# ---------- the ground: a thin surface all round, soil only behind the cut at y 0.2, so the raft and piles stand free in front ----------
W, BACK, FRONT = 9.0, 7.0, -7.0
box("Grass", -W, W, FRONT, BACK, -0.14, 0.0, M_GRASS)
box("Topsoil", -W, W, FRONT, BACK, -0.75, -0.14, M_TOP)
LAYERS = ((-0.75, -5.2, M_CLAY), (-5.2, -11.0, M_SAND), (-11.0, -16.0, M_ROCK))
for i, (z1, z0, m) in enumerate(LAYERS):
    box("Soil%d" % i, -W, W, 0.2, BACK, z0, z1, m)
box("Raft", -3.5, 3.5, -3.5, 3.5, -2.1, -0.75, M_CONC, 0.03)
# the piles: a square grid under the raft, tips reaching into the rock
for ix in range(-3, 4):
    for iy in range(-3, 1):
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.3, radius2=0.3, depth=10.0)
        p = obj_from("Pile", bm, M_PILE, True); p.location = (ix * 1.02, iy * 1.02 - 0.15, -7.1)

# ---------- world ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.008, 0.013, 0.024, 1); bg.inputs["Strength"].default_value = 1.0

# ---------- camera ----------
AZ, EL = (-30, 7) if OPT == "A" else (30, 19)
TGT = Vector((0.0, 0.0, 1.5))
LENS, FRAME_H = 70.0, 50.0
d = LENS * FRAME_H / 36.0
az, el = math.radians(AZ), math.radians(EL)
cd = bpy.data.cameras.new("Cam"); cd.lens = LENS; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 36.0; cd.clip_end = 2000
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = TGT + d * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
t = bpy.data.objects.new("T", None); scene.collection.objects.link(t); t.location = TGT
tc = cam.constraints.new("TRACK_TO"); tc.target = t; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

# ---------- lights ----------
def area(name, loc, size, power, rgb=(1, 1, 1), tgt=None):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = rgb
    o = bpy.data.objects.new(name, l); scene.collection.objects.link(o); o.location = loc
    c = o.constraints.new("TRACK_TO"); c.target = tgt or t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
    return o
def lt(loc):
    o = bpy.data.objects.new("LT", None); scene.collection.objects.link(o); o.location = loc; return o
area("Key", (-22, -34, 34), 22, 9000, (1.0, 0.94, 0.86))
area("Fill", (32, -30, 10), 22, 2600, (0.72, 0.84, 1.0))
area("Rim", (18, 26, 36), 12, 3500, (0.7, 0.85, 1.0))
area("Piles", (0, -18, -9), 12, 2600, (1.0, 0.86, 0.66), lt((0, 0, -8)))

# ---------- render ----------
r = scene.render; r.engine = "CYCLES"
dev = arg("--cycles-device", "CPU")
if dev != "CPU":
    cp = bpy.context.preferences.addons["cycles"].preferences
    cp.compute_device_type = dev; cp.get_devices()
    for x in cp.devices: x.use = x.type == dev
    scene.cycles.device = "GPU"
scene.cycles.samples = int(arg("--samples", "64")); scene.cycles.use_denoising = True
try: scene.cycles.denoiser = "OPTIX" if dev == "OPTIX" else "OPENIMAGEDENOISE"
except Exception: pass
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, int(arg("--pct", "100"))
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
out = arg("--out", "cover/hero_%s.png" % OPT)
r.filepath = out if os.path.isabs(out) else os.path.join(os.getcwd(), out)
bpy.ops.render.render(write_still=True)
print("SAVED", r.filepath)
