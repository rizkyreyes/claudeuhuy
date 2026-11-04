# Dam-Construction cover: a separate hero render of the WHOLE dam (playbook Cover section), not a frame from the video.
# Same wedge profile as build_scene.py, but uncut: a full arched wall across a canyon heightfield, with a crest road and two intake towers.
#   A: daylight, high three-quarter view from downstream: full lake behind, bone-dry riverbed in front, the river pouring out of a tunnel in the wall ("WHERE DID THE RIVER GO?!")
#   B: dusk, low view from the riverbed looking up: the whole wall glowing hot with bright cracks ("125 YEARS TO COOL?!")
# 1 unit = 1 m of the illustrative model. River flows +x -> -x. The title goes in the sky above the dam (y 245-535).
# Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, bmesh, math, os, sys, random
from mathutils import Vector, noise

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT = arg("--opt", "A")
scene = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
random.seed(12)

# ---------- layout ----------
Z_BED, Z_LAKE, Z_CREST, Z_RIM = 0.0, 24.0, 26.0, 31.0
SPAN = 17.0                                       # dam half length (its ends are buried in the canyon walls)
ARCH = 5.0                                        # the wall bows upstream by this much at the centre
def arch(y): return ARCH * (1 - min(1.0, (y / SPAN) ** 2))
def face_up_x(z): return 4.0 + (z + 4.0) * (2.5 - 4.0) / 30.0     # build_scene.py profile
def face_dn_x(z): return -18.0 + (z + 4.0) * (0.7 + 18.0) / 30.0
def half_width(x): return (12.0 + (-x * 0.06 if x < 0 else x * 0.10)) * (1.0 if x < 230 else max(0.0, 1 - (x - 230) / 45.0))
def centre(x): return 0.0 if x < 12 else 11.0 * math.sin((x - 12) / 38.0)
def smooth(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def height(x, y):
    d = abs(y - centre(x)) - half_width(x) + 1.6 * noise.noise(Vector((x * 0.07, y * 0.07, 3.1)))
    n = noise.noise(Vector((x * 0.035, y * 0.035, 0.7)))
    if d <= 0: return Z_BED + 0.12 * noise.noise(Vector((x * 0.3, y * 0.3, 1.3)))
    # steep walls with a few ledges, then a rolling plateau
    w = smooth(d / 7.0); ledge = 0.9 * math.sin(d * 1.3) * (1 - w) * w * 4
    return Z_BED + (Z_RIM + 2.2 * n) * w + ledge + 0.7 * noise.noise(Vector((x * 0.22, y * 0.22, 5.0))) * w

# ---------- materials ----------
def mat(name, rgb, rough=0.5, metallic=0.0, emit=None, emit_s=0.0):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metallic
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = emit_s
    return m, m.node_tree, b
def terrain_mat():
    """Layered canyon rock (as in the video) above, sun-baked cracked mud on the dry riverbed."""
    m, nt, b = mat("Terrain", (0.4, 0.3, 0.2), 0.92); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = 0.12; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 4
    L.new(g.outputs["Position"], wv.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].color = (0.20, 0.10, 0.055, 1); e[1].color = (0.50, 0.30, 0.17, 1); e[0].position = 0.25; e[1].position = 0.85
    L.new(wv.outputs["Fac"], ramp.inputs[0])
    # cracked mud: Voronoi cell edges
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 1.0
    L.new(g.outputs["Position"], vo.inputs["Vector"])
    ck = nt.nodes.new("ShaderNodeMapRange"); ck.inputs[1].default_value = 0.015; ck.inputs[2].default_value = 0.07
    L.new(vo.outputs["Distance"], ck.inputs[0])
    mud = nt.nodes.new("ShaderNodeMix"); mud.data_type = "RGBA"; L.new(ck.outputs[0], mud.inputs["Factor"])
    mud.inputs[6].default_value = (0.05, 0.035, 0.025, 1); mud.inputs[7].default_value = (0.62, 0.47, 0.30, 1)
    sz = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], sz.inputs[0])
    hz = nt.nodes.new("ShaderNodeMapRange"); hz.inputs[1].default_value = 0.35; hz.inputs[2].default_value = 1.1
    L.new(sz.outputs["Z"], hz.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(hz.outputs[0], mx.inputs["Factor"])
    L.new(mud.outputs[2], mx.inputs[6]); L.new(ramp.outputs[0], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 1.6; n2.inputs["Detail"].default_value = 8
    L.new(g.outputs["Position"], n2.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(n2.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def joint_factor(nt, g):
    """1 on the horizontal lift lines and vertical block joints of the wall, 0 elsewhere."""
    L = nt.links; s = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], s.inputs[0])
    def lines(out, period, width):
        d = nt.nodes.new("ShaderNodeMath"); d.operation = "FRACT"
        dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = period
        L.new(out, dv.inputs[0]); L.new(dv.outputs[0], d.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = width / period
        L.new(d.outputs[0], lt.inputs[0]); return lt.outputs[0]
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    L.new(lines(s.outputs["Z"], 3.0, 0.09), mx.inputs[0]); L.new(lines(s.outputs["Y"], 4.5, 0.09), mx.inputs[1])
    return mx.outputs[0]
def concrete_mat():
    m, nt, b = mat("Concrete", (0.62, 0.60, 0.56), 0.82); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.25, 1.1, 0.06)   # long vertical water stains
    L.new(g.outputs["Position"], mp.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 1.4; n.inputs["Detail"].default_value = 7
    L.new(mp.outputs[0], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].color = (0.30, 0.285, 0.26, 1); e[1].color = (0.74, 0.72, 0.68, 1); e[0].position = 0.34; e[1].position = 0.62
    L.new(n.outputs["Fac"], ramp.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(joint_factor(nt, g), mx.inputs["Factor"])
    L.new(ramp.outputs[0], mx.inputs[6]); mx.inputs[7].default_value = (0.13, 0.125, 0.115, 1); L.new(mx.outputs[2], b.inputs["Base Color"])
    return m
def hot_mat():
    """Fresh one-pour concrete: glows from inside, hottest low down, dark crust patches, hairline cracks."""
    m, nt, b = mat("HotConcrete", (0.25, 0.09, 0.04), 0.7); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.22; n.inputs["Detail"].default_value = 7
    L.new(g.outputs["Position"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].color = (0.62, 0.075, 0.012, 1); e[1].color = (1.0, 0.30, 0.035, 1); e[0].position = 0.36; e[1].position = 0.66
    L.new(n.outputs["Fac"], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Emission Color"])
    s = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], s.inputs[0])
    hz = nt.nodes.new("ShaderNodeMapRange"); hz.inputs[1].default_value = 0.0; hz.inputs[2].default_value = 26.0; hz.inputs[3].default_value = 0.72; hz.inputs[4].default_value = 0.4
    L.new(s.outputs["Z"], hz.inputs[0])
    jf = nt.nodes.new("ShaderNodeMapRange"); jf.inputs[3].default_value = 1.0; jf.inputs[4].default_value = 0.72; L.new(joint_factor(nt, g), jf.inputs[0])
    k = nt.nodes.new("ShaderNodeMath"); k.operation = "MULTIPLY"; L.new(hz.outputs[0], k.inputs[0]); L.new(jf.outputs[0], k.inputs[1])
    L.new(k.outputs[0], b.inputs["Emission Strength"])
    return m
def water_mat():
    m, nt, b = mat("Lake", (0.015, 0.14, 0.24), 0.06); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 1.1; n.inputs["Detail"].default_value = 6
    L.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def rush_mat():
    """Whitewater: blue-white streaks along the flow, a little emission so it reads at phone size."""
    m, nt, b = mat("Rush", (0.5, 0.8, 0.92), 0.18, emit=(0.32, 0.72, 0.95), emit_s=0.35); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.9; n.inputs["Detail"].default_value = 6
    L.new(g.outputs["Position"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].color = (0.03, 0.26, 0.46, 1); e[1].color = (0.75, 0.93, 1.0, 1); e[0].position = 0.42; e[1].position = 0.72
    L.new(n.outputs["Fac"], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Base Color"])
    return m
M_TERRAIN, M_WATER, M_RUSH = terrain_mat(), water_mat(), rush_mat()
M_DAM = concrete_mat() if OPT == "A" else hot_mat()
M_TRIM, _, _ = mat("Trim", (0.70, 0.68, 0.63) if OPT == "A" else (0.05, 0.05, 0.055), 0.65)
M_HOLE, _, _ = mat("TunnelDark", (0.004, 0.004, 0.005), 0.9)
M_CRACK, _, _ = mat("Crack", (0.1, 0.02, 0.01), 0.6, emit=(1.0, 0.5, 0.1), emit_s=5.0)

# ---------- geometry helpers ----------
def obj_from(name, verts, faces, m, smooth_faces=True):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    if smooth_faces:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); scene.collection.objects.link(o); me.materials.append(m); return o
def grid(xs, ys, fn):
    v = [fn(x, y) for x in xs for y in ys]; nx, ny = len(xs), len(ys)
    f = [(i * ny + j, i * ny + j + 1, (i + 1) * ny + j + 1, (i + 1) * ny + j) for i in range(nx - 1) for j in range(ny - 1)]
    return v, f
def frange(a, b, st):
    n = int(round((b - a) / st)); return [a + (b - a) * i / n for i in range(n + 1)]
def box(name, a, b, m):
    x0, y0, z0 = a; x1, y1, z1 = b
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return obj_from(name, v, [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], m, False)
def cylinder(name, r, a, b, m, segs=40, cap=True):
    a, b = Vector(a), Vector(b); ax = (b - a).normalized()
    u = ax.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-4 else Vector((1, 0, 0)); w = ax.cross(u)
    v = []
    for p in (a, b):
        for i in range(segs):
            t = 2 * math.pi * i / segs; v.append(tuple(p + r * (math.cos(t) * u + math.sin(t) * w)))
    f = [(i, (i + 1) % segs, segs + (i + 1) % segs, segs + i) for i in range(segs)]
    if cap: f += [tuple(reversed(range(segs))), tuple(range(segs, 2 * segs))]
    return obj_from(name, v, f, m)

# ---------- canyon ----------
xs, ys = frange(-170, 330, 1.0), sorted(set(frange(-120, -32, 2.0) + frange(-32, 32, 0.4) + frange(32, 120, 2.0)))
v, f = grid(xs, ys, lambda x, y: (x, y, height(x, y)))
obj_from("Canyon", v, f, M_TERRAIN)
# desert to the horizon, under the plateau edge
D = 3000.0; XL, XH, YL, YH = -168.0, 328.0, -118.0, 118.0
obj_from("Desert", [(-D, -D, 28.5), (D, -D, 28.5), (D, D, 28.5), (-D, D, 28.5), (XL, YL, 28.5), (XH, YL, 28.5), (XH, YH, 28.5), (XL, YH, 28.5)],
         [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], M_TERRAIN, False)

# ---------- the dam: arched wedge, whole and uncut ----------
Y_ST = frange(-SPAN, SPAN, 0.5)
PROFILE = [(face_up_x(-2.0), -2.0), (face_up_x(Z_CREST), Z_CREST), (face_dn_x(Z_CREST), Z_CREST)] + [(face_dn_x(z), z) for z in frange(Z_CREST - 2, -2.0, 2.0)]
dv, df = [], []; n_p = len(PROFILE)
for y in Y_ST:
    for (x, z) in PROFILE: dv.append((x + arch(y), y, z))
for j in range(len(Y_ST) - 1):
    for i in range(n_p):
        i2 = (i + 1) % n_p; df.append((j * n_p + i, j * n_p + i2, (j + 1) * n_p + i2, (j + 1) * n_p + i))
obj_from("Dam", dv, df, M_DAM, False)
# crest road + parapets, following the arch
def strip(name, x0, x1, z0, z1, m):
    v, f = [], []
    for y in Y_ST: v += [(x0 + arch(y), y, z0), (x1 + arch(y), y, z0), (x1 + arch(y), y, z1), (x0 + arch(y), y, z1)]
    for j in range(len(Y_ST) - 1):
        for i in range(4):
            i2 = (i + 1) % 4; f.append((j * 4 + i, j * 4 + i2, (j + 1) * 4 + i2, (j + 1) * 4 + i))
    return obj_from(name, v, f, m, False)
strip("ParapetUp", 2.25, 2.55, Z_CREST, Z_CREST + 0.8, M_TRIM); strip("ParapetDn", 0.65, 0.95, Z_CREST, Z_CREST + 0.8, M_TRIM)
# two intake towers in the lake, just upstream of the wall
for y in (-7.5, 7.5):
    x = 8.0 + arch(y)
    cylinder(f"Tower{y:+.0f}", 1.5, (x, y, Z_BED), (x, y, Z_CREST + 3.6), M_TRIM)
    cylinder(f"TowerCap{y:+.0f}", 1.85, (x, y, Z_CREST + 3.6), (x, y, Z_CREST + 4.1), M_TRIM)

# ---------- lake (A shows it over the crest; opaque, so its bed needs nothing) ----------
lake_ys = frange(-110, 110, 1.0)
lv, lf = [], []
for y in lake_ys:
    x0 = 1.8 + arch(y) if abs(y) < SPAN else 1.8
    lv += [(x0, y, Z_LAKE), (420.0, y, Z_LAKE)]
for j in range(len(lake_ys) - 1): lf.append((j * 2, j * 2 + 1, j * 2 + 3, j * 2 + 2))
obj_from("Lake", lv, lf, M_WATER)

# ---------- option details ----------
if OPT == "A":
    # the river's new route: a concrete tunnel portal in the right-hand wall, whitewater running out across the dry bed
    X_T = -15.5; yw = -half_width(X_T) - 1.0; ZT = 5.6; R_T = 3.8
    DX, DY = -0.76, 0.65                          # the tube faces downstream and out of the wall, so its mouth reads from the camera
    tube = lambda k, z=ZT: (X_T + DX * k, yw + DY * k, z)
    cylinder("PortalRing", R_T + 0.9, tube(2.4), tube(-6.0), M_TRIM)
    cylinder("PortalHole", R_T, tube(2.5), tube(-6.0), M_HOLE)
    # stream centre line: out of the mouth, down to the bed, then away towards the camera along the bed
    path = []
    for i in range(14):
        p = i / 13; path.append((*tube(2.6 + p * 9.0)[:2], ZT - R_T + 0.5 - (ZT - R_T + 0.35) * p * p))
    x1, y1 = path[-1][:2]
    for i in range(1, 30):
        p = i / 29; path.append((x1 - 62 * p, y1 + 3.0 * math.sin(p * 2.6) - 1.0 * p, 0.14))
    rv, rf = [], []
    for k, (px, py, pz) in enumerate(path):
        a = path[max(0, k - 1)]; b = path[min(len(path) - 1, k + 1)]
        tx, ty = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, ty) or 1.0; nx, ny = -ty / L, tx / L
        hw = 2.6 + 1.6 * min(1.0, k / 16.0)
        for s in (-1, -0.5, 0, 0.5, 1):
            rv.append((px + nx * hw * s, py + ny * hw * s, pz + 0.18 * (1 - s * s) + 0.1 * noise.noise(Vector((px * 0.5, py * 0.5, s)))))
    for k in range(len(path) - 1):
        for s in range(4): rf.append((k * 5 + s, k * 5 + s + 1, (k + 1) * 5 + s + 1, (k + 1) * 5 + s))
    obj_from("Rush", rv, rf, M_RUSH)
    # a few boulders left stranded on the dry bed
    for i in range(16):
        x, y = random.uniform(-58, -19), random.uniform(1, 12); r = random.uniform(0.35, 1.0)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, y, r * 0.3))
        o = bpy.context.object; o.scale = (1, random.uniform(0.7, 1.2), random.uniform(0.5, 0.8)); o.data.materials.append(M_TERRAIN)
else:
    # big jagged cracks down the downstream face, as glowing ribbons just proud of the surface
    def crack(y0, z0, z1, wander, w0):
        pts, y, z = [], y0, z0
        n = 12
        for i in range(n + 1):
            pts.append((y, z)); z += (z1 - z0) / n; y += random.uniform(-wander, wander)
        v, f = [], []
        for k, (y, z) in enumerate(pts):
            hw = w0 * (1 - 0.8 * k / n) * random.uniform(0.7, 1.2)
            for s in (-1, 1):
                yy = y + s * hw; v.append((face_dn_x(z) + arch(yy) - 0.1, yy, z))
        for k in range(n): f.append((k * 2, k * 2 + 1, k * 2 + 3, k * 2 + 2))
        obj_from("Crack", v, f, M_CRACK, False)
    for y0, z0, z1, wander, w0 in ((-6.5, 25.5, 2.0, 1.1, 0.26), (5.0, 25.5, 6.0, 1.1, 0.24), (-0.8, 15.0, 0.2, 1.0, 0.22), (10.5, 19.0, 3.0, 0.9, 0.2), (-11.5, 18.0, 4.0, 0.8, 0.18)):
        crack(y0, z0, z1, wander, w0)

# ---------- world: gradient sky, only seen by the camera; soft ambient for the rest ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
tc = wn.new("ShaderNodeTexCoord"); sz = wn.new("ShaderNodeSeparateXYZ"); wl.new(tc.outputs["Generated"], sz.inputs[0])
ramp = wn.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements; e[0].position = 0.0; e[1].position = 0.34
if OPT == "A": e[0].color = (0.55, 0.72, 0.92, 1); e[1].color = (0.075, 0.24, 0.56, 1)
else: e[0].color = (0.11, 0.06, 0.10, 1); e[1].color = (0.006, 0.012, 0.03, 1)
wl.new(sz.outputs["Z"], ramp.inputs[0]); wl.new(ramp.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.58, 0.70, 0.88, 1) if OPT == "A" else (0.2, 0.25, 0.4, 1)
amb.inputs["Strength"].default_value = 0.42 if OPT == "A" else 0.05
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader"); wl.new(lp.outputs["Is Camera Ray"], mixw.inputs[0])
wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])

# ---------- camera ----------
if OPT == "A":
    TGT, AZ, EL, DIST, LENS = Vector((-3.0, 0.0, 16.5)), 9.0, 18.0, 94.0, 50.0
else:
    TGT, AZ, EL, DIST, LENS = Vector((-3.0, 0.0, 16.5)), -7.0, 4.0, 62.0, 34.0
az, el = math.radians(AZ), math.radians(EL)
cd = bpy.data.cameras.new("Cam"); cd.lens = LENS; cd.sensor_fit = "VERTICAL"; cd.sensor_height = 36.0; cd.clip_end = 8000
cam = bpy.data.objects.new("Cam", cd); scene.collection.objects.link(cam); scene.camera = cam
cam.location = TGT + DIST * Vector((-math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
if OPT == "B": cam.location.z = max(cam.location.z, 3.0)
t = bpy.data.objects.new("T", None); scene.collection.objects.link(t); t.location = TGT
tc_ = cam.constraints.new("TRACK_TO"); tc_.target = t; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"

# ---------- lights ----------
def sun(name, rot, power, rgb, angle=3):
    d = bpy.data.lights.new(name, "SUN"); d.energy = power; d.color = rgb; d.angle = math.radians(angle)
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.rotation_euler = [math.radians(a) for a in rot]
def point(name, loc, power, rgb, r=3.0):
    d = bpy.data.lights.new(name, "POINT"); d.energy = power; d.color = rgb; d.shadow_soft_size = r
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
if OPT == "A":
    sun("Sun", (52, 0, -62), 3.4, (1.0, 0.93, 0.82))
else:
    sun("Moon", (60, 0, 50), 0.12, (0.5, 0.62, 1.0))
    for loc, pw in (((-16, -14, 8), 4200), ((-16, 14, 8), 4200), ((-20, 0, 14), 4800), ((-30, 0, 3), 900)):
        point("Heat", loc, pw, (1.0, 0.34, 0.09))

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
