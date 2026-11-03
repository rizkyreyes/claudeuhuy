# Water-Heater cover: a separate hero render of the WHOLE heater (playbook Cover section), not a frame from the video.
# Same generic gas tank heater as build_scene.py, uncut: jacket, draft hood + vent, cold/hot pipes, T&P valve + discharge, drain valve, gas control.
#   A: seen from the front right, the anode rod pulled halfway out of the top, eaten away, red-hot pits ("A ROD THAT ROTS / ON PURPOSE?!")
#   B: seen low from the front left, rust streaks running down the jacket from the drain valve, burner glowing under the access panel
#      ("IS IT ROTTING / INSIDE?!")
# 1 unit = 10 cm. The heater sits in the lower part of the frame; the title goes in the dark area above it (y 215-595).
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, bmesh, math, os, random, sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT = arg("--opt", "A")
scene = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
random.seed(5)

def mat(name, rgb, rough=0.4, metallic=0.0, coat=0.0, emit=None, emit_s=0.0):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic; b.inputs["Coat Weight"].default_value = coat
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = emit_s
    return m
def masked(name, base, spot, scale, thr, rough, metallic, emit=None, emit_s=0.0, zfade=None):
    """base colour with noise spots (rust / pits); zfade=(z0, z1) keeps spots below z1 (streaks)."""
    m = mat(name, base, rough, metallic); nt = m.node_tree; N, L = nt.nodes, nt.links
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping")
    if zfade: mp.inputs["Scale"].default_value = (1.0, 1.0, 0.18)       # stretched noise = vertical streaks
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 8
    L.new(mp.outputs[0], nz.inputs["Vector"])
    fac = nz.outputs["Fac"]
    if zfade:
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
        mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = zfade[0]; mr.inputs[2].default_value = zfade[1]
        mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = -0.4; L.new(sep.outputs["Z"], mr.inputs[0])
        ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(fac, ad.inputs[0]); L.new(mr.outputs[0], ad.inputs[1]); fac = ad.outputs[0]
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = thr; L.new(fac, gt.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(gt.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (*base, 1); mx.inputs[7].default_value = (*spot, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"])
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = emit_s
        L.new(gt.outputs[0], em.inputs[0]); L.new(em.outputs[0], b.inputs["Emission Strength"])
    return m

if OPT == "B":
    M_JACKET = masked("JacketRust", (0.80, 0.81, 0.80), (0.38, 0.12, 0.03), 2.6, 0.50, 0.32, 0.0, zfade=(0.3, 10.0))
else:
    M_JACKET = mat("Jacket", (0.80, 0.81, 0.80), 0.3, coat=0.4)
M_STEEL = mat("Steel", (0.55, 0.56, 0.58), 0.35, 0.9)
M_COPPER = mat("Copper", (0.86, 0.46, 0.27), 0.28, 1.0)
M_BRASS = mat("Brass", (0.86, 0.66, 0.30), 0.3, 1.0)
M_DARK = mat("Dark", (0.06, 0.06, 0.07), 0.5, 0.3)
M_KNOB = mat("Knob", (0.75, 0.10, 0.08), 0.4)
M_BLUE = mat("ColdBand", (0.10, 0.35, 0.95), 0.4)
M_RED = mat("HotBand", (0.90, 0.12, 0.08), 0.4)
M_ANODE = masked("Anode", (0.30, 0.31, 0.34), (0.45, 0.16, 0.06), 6.0, 0.47, 0.6, 0.15, emit=(1.0, 0.2, 0.08), emit_s=1.8)
M_CORE = mat("Core", (0.4, 0.41, 0.43), 0.4, 1.0)
M_FLAKE = mat("Flake", (0.45, 0.18, 0.08), 0.7, 0.0, emit=(1.0, 0.25, 0.08), emit_s=1.5)
M_GLOW = mat("BurnerGlow", (1.0, 0.45, 0.1), 0.5, 0.0, emit=(1.0, 0.42, 0.1), emit_s=5.0)
M_PUDDLE = mat("Puddle", (0.25, 0.09, 0.03), 0.05, 0.0, coat=1.0)
M_WALL = mat("Wall", (0.045, 0.06, 0.085), 0.55)
M_FLOOR = mat("Floor", (0.05, 0.06, 0.08), 0.3)

def obj_from(name, bm, m, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); me.materials.append(m); return o
def lathe(name, prof, m, seg=72):
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a, b in zip(vs, vs[1:]): bm.edges.new((a, b))
    bmesh.ops.spin(bm, geom=list(bm.verts) + list(bm.edges), cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=seg, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from(name, bm, m)
def cyl(name, r, depth, loc, m, rot=(0, 0, 0), seg=32):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth)
    o = obj_from(name, bm, m, seg > 8); o.location = loc; o.rotation_euler = rot; return o
def box(name, x0, x1, y0, y1, z0, z1, m):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    o = obj_from(name, bm, m, False); o.scale = (x1 - x0, y1 - y0, z1 - z0); o.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.03; bv.segments = 2; return o
RJ, ZT = 2.68, 13.2
# jacket: rounded top edge, bottom ring
lathe("Jacket", [(0.001, ZT), (0.6, ZT), (2.45, ZT - 0.02), (2.62, ZT - 0.1), (RJ, ZT - 0.3), (RJ, 0.25), (RJ - 0.04, 0.0), (0.001, 0.0)], M_JACKET)
lathe("Hood", [(0.62, 18.6), (0.70, 18.6), (0.70, 14.95), (1.08, 14.45), (1.08, 14.05), (0.95, 14.05), (0.95, 14.40), (0.62, 14.9), (0.62, 18.6)], M_STEEL)
cyl("FlueCollar", 0.5, 0.9, (0, 0, ZT + 0.45), M_STEEL)
for k in range(3):
    a = math.radians(30 + 120 * k); cyl(f"Leg{k}", 0.04, 0.9, (0.95 * math.cos(a), 0.95 * math.sin(a), ZT + 0.45), M_STEEL, seg=8)
ZP = 15.6
for nm, x, band in (("Cold", -1.5, M_BLUE), ("Hot", 1.6, M_RED)):
    cyl(f"{nm}Riser", 0.21, ZP - ZT + 0.2, (x, 0.0, (ZT + ZP) / 2), M_COPPER)
    cyl(f"{nm}Band", 0.245, 0.35, (x, 0.0, 14.3), band)
    cyl(f"{nm}Run", 0.21, 4.7, (x, 2.35, ZP), M_COPPER, rot=(math.radians(90), 0, 0))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.215); o = obj_from(f"{nm}Elbow", bm, M_COPPER); o.location = (x, 0, ZP)
ZTP = 11.55
cyl("TPBody", 0.2, 0.62, (RJ + 0.31, 0.0, ZTP), M_BRASS, rot=(0, math.radians(90), 0))
cyl("TPCap", 0.15, 0.4, (RJ + 0.38, 0.0, ZTP + 0.38), M_BRASS)
box("TPLever", RJ + 0.3, RJ + 1.0, -0.04, 0.04, ZTP + 0.6, ZTP + 0.68, M_BRASS)
cyl("Discharge", 0.14, ZTP - 0.9, (RJ + 0.75, 0.0, (ZTP + 0.9) / 2), M_COPPER)
cyl("DischargeH", 0.14, 0.5, (RJ + 0.5, 0.0, ZTP), M_COPPER, rot=(0, math.radians(90), 0))
# front fittings (front = -Y)
box("GasControl", -0.55, 0.55, -RJ - 0.55, -RJ + 0.2, 2.2, 3.1, M_DARK)
cyl("GasKnob", 0.2, 0.15, (0.0, -RJ - 0.62, 2.75), M_KNOB, rot=(math.radians(90), 0, 0))
cyl("GasPipe", 0.08, 2.4, (0.75, -RJ - 0.3, 1.2), M_DARK)
box("AccessPanel", -0.8, 0.8, -RJ - 0.05, -RJ + 0.1, 0.35, 1.15, M_DARK)
box("Plate", -0.7, 0.7, -RJ - 0.04, -RJ + 0.1, 6.8, 8.6, M_STEEL)
cyl("DrainValve", 0.16, 0.6, (-1.2, -RJ - 0.25, 1.5), M_BRASS, rot=(math.radians(90), 0, 0))
cyl("DrainSpout", 0.11, 0.45, (-1.2, -RJ - 0.5, 1.2), M_BRASS)
if OPT == "B":
    box("PanelGlow", -0.7, 0.7, -RJ - 0.07, -RJ + 0.05, 0.42, 0.52, M_GLOW)      # burner light leaking under the panel
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=1.0)
    p = obj_from("Puddle", bm, M_PUDDLE, False); p.scale = (2.2, 1.1, 1); p.location = (-1.0, -RJ - 1.2, 0.005)
# anode rod (option A): pulled halfway out of its port, eaten away
if OPT == "A":
    XA, YA, LIFT = 0.15, -1.75, 7.0
    rod = cyl("Anode", 0.3, 9.2, (XA, YA, 3.1 + LIFT + 4.6), M_ANODE, seg=36)
    bm = rod.data; 
    for v in rod.data.vertices:                                    # uneven, eaten profile
        k = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(v.co.z * 2.3 + 1.0)) * (0.6 + 0.4 * math.sin(v.co.z * 5.1))
        v.co.x *= k; v.co.y *= k
    cyl("Core", 0.04, 9.6, (XA, YA, 3.1 + LIFT + 4.6), M_CORE, seg=10)
    cyl("Hex", 0.4, 0.36, (XA, YA, 3.1 + LIFT + 9.4), M_STEEL, seg=6)
    cyl("Port", 0.42, 0.12, (XA, YA, ZT + 0.03), M_DARK)
    for k in range(14):
        z = ZT + 0.3 + random.uniform(0, 3.5)
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.05, 0.11))
        f = obj_from(f"Flake{k}", bm, M_FLAKE, False); f.location = (XA + random.uniform(-0.6, 0.6), YA + random.uniform(-0.4, 0.3), z)
        f.scale = (1.0, 0.4, 1.0); f.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), 0)
    gl = bpy.data.lights.new("PitGlow", "POINT"); gl.color = (1.0, 0.3, 0.1); gl.energy = 60; gl.shadow_soft_size = 1.0
    g = bpy.data.objects.new("PitGlow", gl); scene.collection.objects.link(g); g.location = (XA, YA - 1.0, ZT + 4.0)
else:
    gl = bpy.data.lights.new("BurnerGlow", "POINT"); gl.color = (1.0, 0.45, 0.12); gl.energy = 40; gl.shadow_soft_size = 0.4
    g = bpy.data.objects.new("BurnerGlow", gl); scene.collection.objects.link(g); g.location = (0, -RJ - 0.6, 0.45)

# room
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60); obj_from("Floor", bm, M_FLOOR, False)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60); w = obj_from("Wall", bm, M_WALL, False)
w.rotation_euler = (math.radians(90), 0, 0); w.location = (0, 4.7, 0)
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.012, 0.018, 0.03, 1); bg.inputs["Strength"].default_value = 1.0

# camera
AZ, EL = (24, 12) if OPT == "A" else (-26, 4)
TGT = Vector((0.4, 0.0, 12.2))
LENS, FRAME_H = 55.0, 33.5
d = LENS * FRAME_H / 36.0
az, el = math.radians(AZ), math.radians(EL)
cd = bpy.data.cameras.new("Cam"); cd.lens = LENS; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 36.0
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = TGT + d * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
t = bpy.data.objects.new("T", None); scene.collection.objects.link(t); t.location = TGT
tc = cam.constraints.new("TRACK_TO"); tc.target = t; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
def area(name, loc, size, power, rgb=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = rgb
    o = bpy.data.objects.new(name, l); scene.collection.objects.link(o); o.location = loc
    c = o.constraints.new("TRACK_TO"); c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
area("Key", (-12, -14, 22), 10, 2600, (1.0, 0.95, 0.88))
area("Fill", (13, -14, 7), 10, 700, (0.72, 0.84, 1.0))
area("Rim", (7, 3, 22), 6, 900, (0.75, 0.88, 1.0))
area("WallWash", (0, -1, 0.2), 8, 120, (0.25, 0.5, 1.0))

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
