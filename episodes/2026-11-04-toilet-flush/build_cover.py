# Toilet-Flush cover: a separate hero render of the WHOLE toilet (playbook Cover section), not a frame from the video.
# The video's model is a side profile cut in half, so this is its own smooth model: lofted bowl, seat, raised lid, tank, chrome handle.
#   A: seen from the front right, high enough to look into the bowl, water spiralling down a vortex ("IT SUCKS?!")
#   B: seen from the front left, water glowing right up to the rim ("IT OVERFLOW?!")
# 1 unit = 10 cm. The toilet sits in the lower part of the frame; the title goes in the dark area above it (y 215-595).
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
def mat(name, rgb, rough=0.4, metallic=0.0, coat=0.0, emit=None, emit_s=0.0, trans=0.0):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = trans
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_s
    return m
M_PORC = mat("Porcelain", (0.86, 0.87, 0.89), 0.12, coat=0.6)
M_SEAT = mat("Seat", (0.90, 0.90, 0.91), 0.22, coat=0.3)
M_CHROME = mat("Chrome", (0.86, 0.88, 0.91), 0.1, metallic=1.0)
def water_mat():
    # colour comes from the mesh: deep blue in the throat, bright cyan along the spiral ridges
    m = mat("Water", (0.02, 0.2, 0.8), 0.04, coat=1.0, emit=(0.02, 0.25, 1.0), emit_s=0.75 if OPT == "A" else 1.0)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"
    nt.links.new(at.outputs["Color"], b.inputs["Base Color"]); nt.links.new(at.outputs["Color"], b.inputs["Emission Color"])
    return m
M_WATER = water_mat()
M_WALL = mat("Wall", (0.045, 0.06, 0.085), 0.55)

def floor_mat():
    m = mat("Floor", (0.05, 0.06, 0.08), 0.25)
    nt = m.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tc, ck = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeTexChecker")
    ck.inputs["Scale"].default_value = 0.22
    ck.inputs["Color1"].default_value = (0.055, 0.065, 0.085, 1); ck.inputs["Color2"].default_value = (0.03, 0.038, 0.05, 1)
    nt.links.new(tc.outputs["Object"], ck.inputs["Vector"]); nt.links.new(ck.outputs["Color"], b.inputs["Base Color"])
    return m

# ---------- geometry helpers ----------
def obj_from(name, bm, m, smooth=True, subsurf=0):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); me.materials.append(m)
    if subsurf:
        s = o.modifiers.new("sub", "SUBSURF"); s.levels = s.render_levels = subsurf
    return o

def egg(a, bf, bb, th):
    # an elongated toilet outline: wider toward the back, long toward the front (-y)
    s, c = math.sin(th), math.cos(th)
    return a * c, (bb if s > 0 else bf) * s

SEG = 72
def loft(name, rings, m, subsurf=2, cap_end=True):
    # rings = [(z, a, bf, bb), ...]
    bm = bmesh.new(); last = None; first = None
    for z, a, bf, bb in rings:
        cur = []
        for i in range(SEG):
            x, y = egg(a, bf, bb, 2 * math.pi * i / SEG)
            cur.append(bm.verts.new((x, y, z)))
        if last:
            for i in range(SEG):
                bm.faces.new((last[i], last[(i + 1) % SEG], cur[(i + 1) % SEG], cur[i]))
        else: first = cur
        last = cur
    if cap_end: bm.faces.new(last)
    bm.faces.new(list(reversed(first)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from(name, bm, m, True, subsurf)

def rbox(name, x0, x1, y0, y1, z0, z1, m, bevel=0.22):
    bm = bmesh.new()
    v = [bm.verts.new((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
        bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = obj_from(name, bm, m, True)
    b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 6; b.limit_method = "ANGLE"
    w = o.modifiers.new("wn", "WEIGHTED_NORMAL") if False else None
    return o

# ---------- bowl: outer wall up to the rim, then down the inside ----------
INNER = [(4.02, 1.62, 2.48, 1.60), (3.86, 1.56, 2.40, 1.54), (3.40, 1.34, 2.08, 1.30), (2.90, 1.02, 1.58, 0.98), (2.45, 0.66, 1.02, 0.62), (2.15, 0.34, 0.50, 0.32)]
loft("Bowl", [(0.0, 1.22, 1.78, 1.70), (0.12, 1.20, 1.74, 1.68), (0.45, 1.08, 1.52, 1.50), (1.30, 1.05, 1.42, 1.28), (2.30, 1.34, 1.94, 1.46),
              (3.20, 1.74, 2.58, 1.78), (3.82, 1.92, 2.86, 1.92), (4.06, 1.90, 2.84, 1.90), (4.10, 1.78, 2.68, 1.76)] + INNER, M_PORC)

def inner_at(z):
    # interpolate the inside outline at height z, so the water meets the wall
    for (z1, a1, f1, b1), (z0, a0, f0, b0) in zip(INNER, INNER[1:]):
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            return a0 + (a1 - a0) * t, f0 + (f1 - f0) * t, b0 + (b1 - b0) * t
    return INNER[-1][1:]

# ---------- water ----------
LEVEL = 3.05 if OPT == "A" else 3.92
A, BF, BB = inner_at(LEVEL)
RN = 40
bm = bmesh.new(); rings = []; shade = {}
DEEP, BRIGHT = Vector((0.004, 0.05, 0.42)), Vector((0.12, 0.72, 1.0))
for j in range(RN + 1):
    r = 0.02 + 0.98 * j / RN; cur = []
    for i in range(SEG):
        th = 2 * math.pi * i / SEG; x, y = egg(A * r, BF * r, BB * r, th)
        if OPT == "A":
            # the vortex: the surface dips toward the middle, spiral ridges wind into it
            z = LEVEL - 0.85 * (1 - r) ** 2.6 + 0.09 * r * (1 - r) * 4 * math.sin(3 * th + 11 * r)
            k = (0.5 + 0.5 * math.sin(3 * th + 11 * r)) ** 3 * min(1.0, r * 1.6)
        else:
            z = LEVEL + 0.012 * math.sin(5 * th + 16 * r)
            k = 0.35 + 0.3 * r + 0.2 * math.sin(5 * th + 16 * r)
        v = bm.verts.new((x, y, z)); shade[v] = k; cur.append(v)
    rings.append(cur)
for a_, b_ in zip(rings, rings[1:]):
    for i in range(SEG):
        bm.faces.new((a_[i], a_[(i + 1) % SEG], b_[(i + 1) % SEG], b_[i]))
bm.faces.new(rings[0])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if f.normal.z < 0: f.normal_flip()
col = bm.loops.layers.color.new("Col")
for f in bm.faces:
    for l in f.loops:
        c = DEEP.lerp(BRIGHT, max(0.0, min(1.0, shade[l.vert]))); l[col] = (c.x, c.y, c.z, 1)
obj_from("Water", bm, M_WATER, True)

# ---------- seat: a flat ring on the rim ----------
bm = bmesh.new(); XS = [(math.cos(2 * math.pi * k / 12), math.sin(2 * math.pi * k / 12)) for k in range(12)]; rings = []
for i in range(SEG):
    th = 2 * math.pi * i / SEG
    px, py = egg(1.72, 2.60, 1.70, th)
    n = Vector((px / 1.72, py / (2.60 if math.sin(th) <= 0 else 1.70), 0)).normalized()
    rings.append([bm.verts.new((px + n.x * u * 0.44, py + n.y * u * 0.44, 4.26 + v * 0.13)) for u, v in XS])
for i in range(SEG):
    a_, b_ = rings[i], rings[(i + 1) % SEG]
    for k in range(12):
        bm.faces.new((a_[k], a_[(k + 1) % 12], b_[(k + 1) % 12], b_[k]))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
obj_from("Seat", bm, M_SEAT, True)

# ---------- lid, raised against the tank (hinge at y 1.72) ----------
lid = loft("Lid", [(-0.10, 1.74, 2.62, 1.70), (-0.05, 2.00, 2.92, 1.98), (0.05, 2.02, 2.94, 2.00), (0.13, 1.84, 2.72, 1.80)], M_SEAT)
HY = 1.76
for v in lid.data.vertices:
    v.co.y -= HY                                  # the hinge edge becomes the origin
    v.co.y *= 0.82; v.co.x *= 0.94                # shorter than the seat, so the tank still shows above it
lid.location = (0, HY, 4.42); lid.rotation_euler = (math.radians(-93), 0, 0)
lid.location.y = HY + 0.06

# ---------- back of the bowl, tank, lid of the tank, handle ----------
rbox("Neck", -1.28, 1.28, 1.20, 2.40, 3.50, 4.28, M_PORC, 0.2)
rbox("Tank", -2.12, 2.12, 2.08, 3.58, 4.20, 7.55, M_PORC, 0.2)
rbox("TankLid", -2.22, 2.22, 1.98, 3.68, 7.55, 7.92, M_PORC, 0.13)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=0.24, radius2=0.24, depth=0.14)
hb = obj_from("HandleBase", bm, M_CHROME, True); hb.location = (-1.72, 2.08, 6.85); hb.rotation_euler = (math.radians(90), 0, 0)
rbox("HandleBar", -1.95, -1.25, 1.97, 2.06, 6.78, 6.90, M_CHROME, 0.04)
# two bolt caps at the hinge
for sx in (-1, 1):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.2, radius2=0.2, depth=0.3)
    c = obj_from("Hinge", bm, M_SEAT, True); c.location = (sx * 0.95, 1.88, 4.34); c.rotation_euler = (0, math.radians(90), 0)

# ---------- room ----------
fl = floor_mat()
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60); f = obj_from("Floor", bm, fl, False)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=60); w = obj_from("Wall", bm, M_WALL, False)
w.rotation_euler = (math.radians(90), 0, 0); w.location = (0, 3.75, 0)

world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs["Color"].default_value = (0.012, 0.018, 0.03, 1); bg.inputs["Strength"].default_value = 1.0

# ---------- camera: frame 14 units tall, the toilet in the lower 2/3 ----------
AZ, EL = (28, 26) if OPT == "A" else (-24, 17)
TGT = Vector((0.0, 0.6, 5.3 if OPT == "A" else 5.6))
LENS, FRAME_H = 62.0, (16.2 if OPT == "A" else 15.4)
d = LENS * FRAME_H / 36.0
az, el = math.radians(AZ), math.radians(EL)
cd = bpy.data.cameras.new("Cam"); cd.lens = LENS; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 36.0
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = TGT + d * Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
t = bpy.data.objects.new("T", None); scene.collection.objects.link(t); t.location = TGT
tc = cam.constraints.new("TRACK_TO"); tc.target = t; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"

# ---------- lights ----------
def area(name, loc, size, power, rgb=(1, 1, 1)):
    l = bpy.data.lights.new(name, "AREA"); l.size = size; l.energy = power; l.color = rgb
    o = bpy.data.objects.new(name, l); scene.collection.objects.link(o); o.location = loc
    c = o.constraints.new("TRACK_TO"); c.target = t; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
area("Key", (-9, -11, 13), 9, 1500, (1.0, 0.95, 0.88))
area("Fill", (10, -12, 4), 10, 420, (0.72, 0.84, 1.0))
area("Rim", (6, 1, 14), 5, 500, (0.75, 0.88, 1.0))
area("WallWash", (0, -2, -0.3), 7, 90, (0.25, 0.5, 1.0))
gl = bpy.data.lights.new("BowlGlow", "POINT"); gl.color = (0.15, 0.6, 1.0); gl.energy = 6 if OPT == "A" else 10; gl.shadow_soft_size = 0.5
g = bpy.data.objects.new("BowlGlow", gl); scene.collection.objects.link(g); g.location = (0, -0.3, 4.1 if OPT == "A" else 4.75)

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
