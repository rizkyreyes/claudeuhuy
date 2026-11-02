# Fridge cover: a separate hero render of the WHOLE closed fridge (playbook Cover section), not a frame from the video.
#   A: from the front, cool light on the doors, hot orange glow on the wall behind it ("IT DOESN'T MAKE COLD?!")
#   B: from behind at an angle, the coils on the back glowing hot, heat rising off them ("YOUR FRIDGE IS A HEATER?!")
# 1 unit = 10 cm. The fridge sits in the lower part of the frame; the title goes in the dark area above it (y 215-595).
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, bmesh, math, os, sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT = arg("--opt", "A")
scene = bpy.context.scene
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
HOT = (1.0, 0.33, 0.05)
M_BODY = mat("Body", (0.83, 0.84, 0.86), 0.28, coat=0.5)
M_GASKET = mat("Gasket", (0.05, 0.05, 0.055), 0.6)
M_CHROME = mat("Chrome", (0.86, 0.88, 0.91), 0.12, metallic=1.0)
M_FOOT = mat("Foot", (0.03, 0.03, 0.035), 0.5)
M_BACK = mat("BackPanel", (0.10, 0.10, 0.11), 0.6)
M_COIL = mat("Coil", (0.9, 0.35, 0.1), 0.3, metallic=0.4, emit=HOT, emit_s=9.0)
M_WIRE = mat("Wire", (0.12, 0.07, 0.05), 0.4, emit=HOT, emit_s=1.4)
M_HEAT = mat("Heat", HOT, 0.5, emit=HOT, emit_s=5.0)
M_COMP = mat("Compressor", (0.03, 0.03, 0.035), 0.3, metallic=0.4)
M_WALL = mat("Wall", (0.06, 0.07, 0.09), 0.6)

def floor_mat():
    m = mat("Floor", (0.05, 0.06, 0.08), 0.28)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc, ck = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 0.13
    ck.inputs["Color1"].default_value = (0.055, 0.065, 0.085, 1); ck.inputs["Color2"].default_value = (0.03, 0.038, 0.05, 1)
    nt.links.new(tc.outputs["Object"], ck.inputs["Vector"]); nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    return m

# ---------- geometry helpers ----------
def obj_from(name, bm, m, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); me.materials.append(m)
    return o

def rbox(name, x0, x1, y0, y1, z0, z1, m, bevel=0.2):
    bm = bmesh.new()
    v = [bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from(name, bm, m, True)
    b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 6; b.limit_method = "ANGLE"
    return o

def tube(name, pts, r, m, seg=12):
    # a round tube along a polyline, via a curve so bends stay smooth
    c = bpy.data.curves.new(name, "CURVE"); c.dimensions = "3D"; c.bevel_depth = r; c.bevel_resolution = 3
    s = c.splines.new("POLY"); s.points.add(len(pts) - 1)
    for p, q in zip(s.points, pts): p.co = (*q, 1)
    o = bpy.data.objects.new(name, c); scene.collection.objects.link(o); c.materials.append(m)
    return o

# ---------- the fridge: faces -y; back at y 3.2 ----------
rbox("Cabinet", -3.5, 3.5, -3.1, 3.2, 0.8, 17.3, M_BODY, 0.18)
rbox("GasketFreezer", -3.42, 3.42, -3.22, -3.05, 12.55, 17.15, M_GASKET, 0.05)
rbox("GasketFridge", -3.42, 3.42, -3.22, -3.05, 0.95, 12.3, M_GASKET, 0.05)
rbox("DoorFreezer", -3.5, 3.5, -3.75, -3.2, 12.6, 17.3, M_BODY, 0.2)
rbox("DoorFridge", -3.5, 3.5, -3.75, -3.2, 0.95, 12.25, M_BODY, 0.2)
for name, z0, z1 in (("HandleTop", 13.0, 15.6), ("HandleLow", 8.0, 11.8)):
    rbox(name, 2.72, 3.0, -4.12, -3.95, z0, z1, M_CHROME, 0.06)
    rbox(name + "A", 2.76, 2.96, -4.0, -3.72, z0 + 0.12, z0 + 0.42, M_CHROME, 0.04)
    rbox(name + "B", 2.76, 2.96, -4.0, -3.72, z1 - 0.42, z1 - 0.12, M_CHROME, 0.04)
rbox("Plinth", -3.4, 3.4, -3.1, 3.1, 0.4, 0.9, M_FOOT, 0.05)
for sx in (-1, 1):
    for sy in (-1, 1):
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.32, radius2=0.26, depth=0.42)
        f = obj_from("Foot", bm, M_FOOT, True); f.location = (sx * 2.9, sy * 2.6, 0.21)

# ---------- the back: dark panel, a hot serpentine coil on steel wires, the compressor ----------
rbox("BackPanel", -3.2, 3.2, 3.18, 3.26, 3.2, 16.8, M_BACK, 0.02)
Y_C = 3.62
pts = []; rows = 13
for i in range(rows):
    z = 4.2 + 12.0 * i / (rows - 1); xa, xb = (-2.7, 2.7) if i % 2 == 0 else (2.7, -2.7)
    pts += [(xa, Y_C, z), (xb, Y_C, z)]
tube("Coil", pts, 0.085, M_COIL)
for k in range(15):
    x = -2.6 + 5.2 * k / 14
    tube("Wire%d" % k, [(x, Y_C + 0.11, 3.9), (x, Y_C + 0.11, 16.5)], 0.028, M_WIRE)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=1.25)
c = obj_from("Compressor", bm, M_COMP, True); c.location = (0.9, 3.0, 1.9); c.scale = (1.0, 0.82, 0.85)

# ---------- heat rising off the back (B only) ----------
if OPT == "B":
    for k, (x0, y0, z0, ph) in enumerate(((-2.2, 1.6, 17.9, 0.0), (0.0, 1.9, 18.1, 1.6), (2.2, 1.6, 17.9, 3.0))):
        pts = []
        for i in range(40):
            u = i / 39
            pts.append((x0 + 0.34 * math.sin(ph + u * 9), y0 + 0.5 * u, z0 + 3.4 * u))
        tube("HeatA%d" % k, pts, 0.07 * 1.4, M_HEAT)

# ---------- room ----------
fl = floor_mat()
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=120); obj_from("Floor", bm, fl, False)
if OPT == "A":
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=120); w = obj_from("Wall", bm, M_WALL, False)
    w.rotation_euler = (math.radians(90), 0, 0); w.location = (0, 6.2, 0)
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.012, 0.018, 0.03, 1); bg.inputs["Strength"].default_value = 1.0

# ---------- camera: frame tall enough that the fridge fills y 620-1660 ----------
AZ, EL = (27, 9) if OPT == "A" else (146, 12)
TGT = Vector((0.0, 0.0, 12.2))
LENS, FRAME_H = 62.0, 34.0
d = LENS * FRAME_H / 36.0
az, el = math.radians(AZ), math.radians(EL)
cd = bpy.data.cameras.new("Cam"); cd.lens = LENS; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 36.0
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
def spot_target(loc):
    o = bpy.data.objects.new("LT", None); scene.collection.objects.link(o); o.location = loc; return o
if OPT == "A":
    area("Key", (-14, -22, 24), 16, 3600, (0.82, 0.92, 1.0))
    area("Fill", (22, -22, 8), 14, 700, (0.7, 0.84, 1.0))
    # the heat: hidden behind the fridge, it lights the wall around the silhouette
    for x, z, p in ((-2.2, 7, 1500), (2.2, 7, 1500), (-2.2, 13, 1700), (2.2, 13, 1700), (0, 16.8, 2200)):
        area("Halo", (x, 3.9, z), 3.6, p, HOT, spot_target((x * 2.2, 6.2, z + 1.5)))
else:
    area("Key", (-12, 24, 26), 14, 1700, (1.0, 0.9, 0.8))
    area("Fill", (22, -6, 12), 14, 500, (0.7, 0.84, 1.0))
    gl = bpy.data.lights.new("CoilGlow", "POINT"); gl.color = HOT; gl.energy = 1700; gl.shadow_soft_size = 3.0
    g = bpy.data.objects.new("CoilGlow", gl); scene.collection.objects.link(g); g.location = (0.5, 6.0, 10.0)

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
