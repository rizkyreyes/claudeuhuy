# Septic-Tank-3D: a buried septic tank + drainfield in a yard cross-section, Blender Cycles. Every cue is a word in the VO.
# Set A (origin): yard section cut at y = 0 (house, inlet pipe, concrete tank with baffle and T outlet, drainfield trenches,
#   groundwater), sludge / clear liquid / scum layers, sorting particles, bacteria, flow pulses, drips, a pump truck.
# Set B (x = 2000): an 1860s masonry tank diorama (cottage, clay pipe, sealed lid that opens, almost no solids inside).
# Layer heights, particles, pulses, drips, the truck and the lids are baked per frame. Sizes are illustrative, none are spoken.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 0.75, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(28)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]).startswith(norm(word)):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
C = {}
for name, word in [("why", "why"), ("septic", "septic"), ("tank", "tank"), ("fill", "fill"), ("up", "up"), ("because", "because"),
                   ("already", "already"), ("full", "full"), ("lets", "let's"), ("cut", "cut"), ("open", "open"),
                   ("wastewater", "wastewater"), ("house", "house"), ("runs", "runs"), ("buried", "buried"), ("tank2", "tank"),
                   ("baffle", "baffle"), ("turns", "turns"), ("flow", "flow"), ("downward", "downward"), ("churn", "churn"),
                   ("then", "then"), ("sits", "sits"), ("gravity", "gravity"), ("sorts", "sorts"), ("heavy", "heavy"),
                   ("solids", "solids"), ("sink", "sink"), ("bottom", "bottom"), ("sludge", "sludge"), ("grease", "grease"),
                   ("oils", "oils"), ("float", "float"), ("top", "top"), ("scum", "scum"), ("between", "between"),
                   ("layer", "layer"), ("clear", "clear"), ("liquid", "liquid"), ("bacteria", "bacteria"), ("oxygen", "oxygen"),
                   ("slowly", "slowly"), ("break", "break"), ("solids2", "solids"), ("now", "now"), ("trick", "trick"),
                   ("liquid2", "liquid"), ("always", "always"), ("sits2", "sits"), ("outlet", "outlet"), ("pipe", "pipe"),
                   ("so", "so"), ("every", "every"), ("gallon", "gallon"), ("flows", "flows"), ("in", "in"), ("pushes", "pushes"),
                   ("gallon2", "gallon"), ("out", "out"), ("tshaped", "t-shaped"), ("outlet2", "outlet"), ("draws", "draws"),
                   ("middle", "middle"), ("scum2", "scum"), ("sludge2", "sludge"), ("stay", "stay"), ("behind", "behind"),
                   ("that", "that"), ("liquid3", "liquid"), ("drainfield", "drainfield"), ("perforated", "perforated"),
                   ("pipes", "pipes"), ("laid", "laid"), ("gravel", "gravel"), ("trenches", "trenches"), ("lawn", "lawn"),
                   ("trickles", "trickles"), ("soil", "soil"), ("soil2", "soil"), ("cleaning", "cleaning"),
                   ("filtering", "filtering"), ("germs", "germs"), ("groundwater", "groundwater"), ("but", "but"),
                   ("bacteria2", "bacteria"), ("eat", "eat"), ("everything", "everything"), ("sludge3", "sludge"),
                   ("slowly2", "slowly"), ("builds", "builds"), ("three", "three"), ("five", "five"), ("years", "years"),
                   ("truck", "truck"), ("pumps", "pumps"), ("around", "around"), ("y1860", "1860"), ("frenchman", "frenchman"),
                   ("mouras", "mouras"), ("waste", "waste"), ("sealed", "sealed"), ("years2", "years"), ("opened", "opened"),
                   ("almost", "almost"), ("free", "free"), ("solids3", "solids"), ("is", "is"), ("home", "home"),
                   ("septic2", "septic"), ("sewer", "sewer"), ("tell", "tell"), ("comments", "comments")]:
    C[name] = TA(word)
C["end"] = DUR

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
prefs = bpy.context.preferences.edit
def key(owner, path, frame, value=None, interp="BEZIER", index=-1):
    prefs.keyframe_new_interpolation_type = interp
    if value is not None:
        if index >= 0: getattr(owner, path)[index] = value
        else: setattr(owner, path, value)
    owner.keyframe_insert(path, frame=frame, index=index)
def vis(obj, frame, hidden):
    for o in [obj] + list(obj.children_recursive):
        key(o, "hide_render", frame, hidden, "CONSTANT"); key(o, "hide_viewport", frame, hidden, "CONSTANT")
def windows(obj, wins):
    """Visible only inside the given (t0, t1) windows."""
    vis(obj, 1, True)
    for t0, t1 in wins: vis(obj, F(t0), False); vis(obj, F(t1), True)
def fcurve(owner, path, index):
    owner.keyframe_insert(path, index=index, frame=1)
    ad = owner.animation_data; act = ad.action
    try: fcs = act.fcurves
    except AttributeError:
        from bpy_extras import anim_utils
        fcs = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot).fcurves
    return fcs.find(path, index=index)
def bake(owner, path, index, values):
    """values[f-1] for every frame, linear (fast path: foreach_set instead of keyframe_insert)."""
    fc = fcurve(owner, path, index)
    fc.keyframe_points.clear(); fc.keyframe_points.add(len(values))
    co = []
    for i, v in enumerate(values): co += [i + 1, v]
    fc.keyframe_points.foreach_set("co", co)
    fc.keyframe_points.foreach_set("interpolation", [1] * len(values))      # LINEAR
    fc.update(); return fc
def bake_vec(owner, path, vecs):
    for ax in range(3): bake(owner, path, ax, [v[ax] for v in vecs])
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("SepticTank")
TS = [(fr - 1) / FPS for fr in range(1, FRAMES + 1)]

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
def mat(name, rgb, rough=0.4, metallic=0.0, emit_rgb=(1.0, 0.74, 0.27), noise=0.0):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise; nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough * 0.7; mr.inputs[4].default_value = rough * 1.4
        nt.links.new(n.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
def strata_mat(name, bands, scale=2.5, wobble=0.35):
    """Ground coloured by world height: bands = [(z, rgb), ...] low to high, with noise so the layers read as soil, not paint."""
    m, nt, b = new_mat(name)
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = wobble
    nt.links.new(nz.outputs["Fac"], add.inputs[0]); nt.links.new(sep.outputs["Z"], add.inputs[2])
    z0, z1 = bands[0][0], bands[-1][0]
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = z0; mr.inputs[2].default_value = z1
    nt.links.new(add.outputs[0], mr.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (*bands[0][1], 1); el[1].position = 1.0; el[1].color = (*bands[-1][1], 1)
    for z, rgb in bands[1:-1]:
        e = el.new((z - z0) / (z1 - z0)); e.color = (*rgb, 1)
    ramp.color_ramp.interpolation = "EASE"
    nt.links.new(mr.outputs[0], ramp.inputs[0])
    hue = nt.nodes.new("ShaderNodeMixRGB"); hue.blend_type = "MULTIPLY"; hue.inputs[0].default_value = 0.35
    nt.links.new(ramp.outputs[0], hue.inputs[1]); nt.links.new(nz.outputs["Color"], hue.inputs[2])
    nt.links.new(hue.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.92
    b.inputs["Emission Color"].default_value = (0.25, 0.9, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
def pebble_mat(name, c0, c1, scale=14.0):
    """Gravel / masonry look: Voronoi cells shaded between two greys."""
    m, nt, b = new_mat(name)
    tc = nt.nodes.new("ShaderNodeTexCoord"); vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].color = (*c0, 1); el[1].color = (*c1, 1)
    nt.links.new(vo.outputs["Distance"], ramp.inputs[0]); nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Emission Color"].default_value = (1.0, 0.74, 0.27, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
GOLD, CYAN, RED, GREEN = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12), (0.35, 1.0, 0.35)
M_GROUND, B_GROUND = strata_mat("Ground", [(-8.0, (0.05, 0.045, 0.04)), (-6.0, (0.12, 0.10, 0.08)), (-3.5, (0.24, 0.18, 0.12)),
                                           (-1.2, (0.30, 0.22, 0.14)), (-0.5, (0.17, 0.12, 0.08)), (-0.06, (0.13, 0.09, 0.06))], 1.8, 0.3)
M_LAWN, _ = mat("Lawn", (0.10, 0.30, 0.06), 0.85, 0.0, GOLD, 30)
M_CONC, B_CONC = mat("Concrete", (0.50, 0.50, 0.48), 0.85, 0.0, GOLD, 25)
M_WALLF, B_WALLF = mat("TankFrontWall", (0.50, 0.50, 0.48), 0.85, 0.0, CYAN, 25)
M_LIQ, B_LIQ = mat("ClearLiquid", (0.16, 0.12, 0.06), 0.35, 0.0, CYAN)
M_SLUDGE, B_SLUDGE = mat("Sludge", (0.11, 0.065, 0.03), 0.7, 0.0, GOLD, 18)
M_SCUM, B_SCUM = mat("Scum", (0.62, 0.50, 0.24), 0.6, 0.0, GOLD, 22)
M_PVC, B_PVC = mat("PVC", (0.78, 0.80, 0.82), 0.35, 0.0, GOLD)
M_TEE, B_TEE = mat("OutletTee", (0.78, 0.80, 0.82), 0.35, 0.0, GOLD)
M_BAFFLE, B_BAFFLE = mat("Baffle", (0.58, 0.58, 0.56), 0.8, 0.0, GOLD, 25)
M_DPIPE, B_DPIPE = mat("DrainPipe", (0.85, 0.85, 0.82), 0.4, 0.0, GOLD)
M_HOLE, _ = mat("Holes", (0.01, 0.01, 0.01), 0.8)
M_GRAVEL, B_GRAVEL = pebble_mat("Gravel", (0.20, 0.20, 0.21), (0.58, 0.57, 0.55), 16.0)
M_GW, B_GW = mat("Groundwater", (0.05, 0.22, 0.38), 0.2, 0.0, CYAN); B_GW.inputs["Emission Strength"].default_value = 0.15
M_LEVEL, B_LEVEL = mat("LevelLine", CYAN, 0.4, 0.0, CYAN)
M_IN, B_IN = mat("PulseIn", GOLD, 0.4, 0.0, GOLD); B_IN.inputs["Emission Strength"].default_value = 4.0
M_OUT, B_OUT = mat("PulseOut", CYAN, 0.4, 0.0, CYAN); B_OUT.inputs["Emission Strength"].default_value = 4.0
M_SOLID, _ = mat("SinkingSolids", (0.16, 0.09, 0.04), 0.7)
M_FAT, B_FAT = mat("RisingGrease", (0.85, 0.68, 0.30), 0.5, 0.0, GOLD); B_FAT.inputs["Emission Strength"].default_value = 0.3
M_BUG, B_BUG = mat("Bacteria", GREEN, 0.5, 0.0, GREEN); B_BUG.inputs["Emission Strength"].default_value = 3.0
M_GERM, B_GERM = mat("Germs", RED, 0.5, 0.0, RED); B_GERM.inputs["Emission Strength"].default_value = 3.0
M_ARROW, B_ARROW = mat("ArrowMiddle", CYAN, 0.4, 0.0, CYAN); B_ARROW.inputs["Emission Strength"].default_value = 4.0
M_WALL, _ = mat("HouseWall", (0.72, 0.68, 0.60), 0.8, 0.0, GOLD, 10)
M_ROOF, _ = mat("Roof", (0.22, 0.12, 0.10), 0.7)
M_WIN, B_WIN = mat("Windows", (0.9, 0.8, 0.5), 0.4, 0.0, (1.0, 0.85, 0.55)); B_WIN.inputs["Emission Strength"].default_value = 2.0
M_RISER, _ = mat("RiserLid", (0.12, 0.30, 0.12), 0.6)
M_TRUCK, B_TRUCK = mat("TruckTank", (0.80, 0.82, 0.85), 0.25, 0.9, GOLD)
M_CAB, _ = mat("TruckCab", (0.85, 0.30, 0.08), 0.4, 0.2)
M_TYRE, _ = mat("Tyres", (0.02, 0.02, 0.02), 0.8)
M_HOSE, B_HOSE = mat("Hose", (0.05, 0.05, 0.05), 0.5, 0.0, GOLD)
# Set B
M_STONE, B_STONE = pebble_mat("Masonry", (0.30, 0.26, 0.20), (0.62, 0.55, 0.44), 6.0)
M_CLAYP, _ = mat("ClayPipe", (0.55, 0.26, 0.13), 0.7)
M_OLDW, _ = mat("OldWater", (0.04, 0.12, 0.13), 0.08); _.inputs["Coat Weight"].default_value = 0.6
M_OLDS, B_OLDS = mat("OldSludge", (0.11, 0.065, 0.03), 0.7, 0.0, GOLD)
M_LID, B_LID = pebble_mat("OldLid", (0.32, 0.28, 0.22), (0.60, 0.53, 0.42), 5.0)

# ---------- geometry helpers ----------
def mesh_obj(name, bm, mats, parent=None, link=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (mats if isinstance(mats, (list, tuple)) else [mats]):
        if m_: me.materials.append(m_)
    o = bpy.data.objects.new(name, me)
    if link: CL.objects.link(o)
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o
def add_box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
    bmesh.ops.scale(bm, verts=vs, vec=(x1 - x0, y1 - y0, z1 - z0))
    bmesh.ops.translate(bm, verts=vs, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def box(name, x0, x1, y0, y1, z0, z1, m_, parent=None):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1); return mesh_obj(name, bm, m_, parent)
def add_cyl(bm, r, depth, axis, center, seg=32, mi=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=depth); vs = res["verts"]
    if axis == "X": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    if axis == "Y": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, verts=vs, vec=center)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def add_prism_y(bm, poly, y0, y1, mi=0):
    """Extrude a polygon given in (x, z) between y0 and y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y1, z)) for x, z in poly]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(poly)
    for i in range(n): fs.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def bevel_mod(o, w=0.01, seg=2):
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = w; bv.segments = seg; bv.limit_method = "ANGLE"
def curve_obj(name, pts, depth, m_, res=3, link=True):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    if m_: cu.materials.append(m_)
    o = bpy.data.objects.new(name, cu)
    if link: CL.objects.link(o)
    return o
def sphere_mesh(name, r, m_, sub=2):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(m_); return me

# ---------- easing, piecewise curves, paths ----------
def ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def lin(p): return max(0.0, min(1.0, p))
def PW(keys):
    """Piecewise eased curve through (t, value) keys."""
    def f(t):
        if t <= keys[0][0]: return keys[0][1]
        for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
            if t <= t1: return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0)) if t1 > t0 else v1
        return keys[-1][1]
    return f
def path_fn(pts):
    """Point at arc-length fraction u (0..1) along a polyline."""
    P = [Vector(p) for p in pts]; L = [0.0]
    for a, b in zip(P, P[1:]): L.append(L[-1] + (b - a).length)
    def at(u):
        s = max(0.0, min(1.0, u)) * L[-1]
        for i in range(len(P) - 1):
            if s <= L[i + 1] or i == len(P) - 2:
                seg = max(1e-6, L[i + 1] - L[i]); return P[i].lerp(P[i + 1], (s - L[i]) / seg)
    return at, L[-1]

# ---------- Set A: yard section ----------
GX0, GX1, GY1, GZ0 = -18.0, 28.0, 9.0, -8.0
Z_GW = -6.2                                   # groundwater table
TX0, TX1, TZ0, TZ1, TW = -2.4, 2.4, -3.0, -0.45, 0.15     # tank outer box (x, z) and wall thickness
IX0, IX1, IZ0, IZ1, TY1 = TX0 + TW, TX1 - TW, TZ0 + TW, TZ1 - TW, 2.2   # inner cavity; tank depth into the section
Z_IN, Z_OUT, R_P = -0.72, -0.85, 0.11         # inlet pipe centre, outlet pipe centre, pipe radius
Z_L = Z_OUT - R_P                             # liquid level = outlet invert
DX0, DX1 = 9.0, 25.0                          # drainfield
ZT0, ZT1 = -1.9, -0.6                         # trench bottom / top (gravel)
Z_DP = -1.05                                  # drain pipe centre
TRENCH_Y = [(0.0, 0.45, 0.0), (2.0, 2.9, 2.45), (4.0, 4.9, 4.45)]   # (y0, y1, pipe y) — the first trench is cut through its middle
ZL = -0.06                                    # top of the soil under the lawn
# ground blocks (left of the tank, under it, cover above it, between tank and drainfield, under/around the drainfield)
for nm, (x0, x1, z0, z1) in {"L": (GX0, TX0, Z_GW, ZL), "U": (TX0, TX1, Z_GW, TZ0), "Cov": (TX0, TX1, TZ1, ZL),
                             "M": (TX1, DX0, Z_GW, ZL), "DU": (DX0, DX1, Z_GW, ZT0), "R": (DX1, GX1, Z_GW, ZL)}.items():
    box(f"Ground_{nm}", x0, x1, 0.0, GY1, z0, z1, M_GROUND)
# trench layer in the drainfield: gravel strips with soil strips between. The lower half (up to the pipe centre) stays,
# the upper half rides on the lid, so the lifted lid shows the pipes lying in their gravel beds.
LID = bpy.data.objects.new("DrainfieldLid", None); CL.objects.link(LID)
Z_GB = Z_DP + 0.02
def trench_layer(tag, z0, z1, parent=None):
    ys = [0.0]
    for y0, y1, _ in TRENCH_Y:
        if y0 > ys[-1]: box(f"TrenchSoil{tag}_{y0}", DX0, DX1, ys[-1], y0, z0, z1, M_GROUND, parent)
        box(f"Gravel{tag}_{y0}", DX0, DX1, y0, y1, z0, z1, M_GRAVEL, parent); ys.append(y1)
    box(f"TrenchSoil{tag}_back", DX0, DX1, ys[-1], GY1, z0, z1, M_GROUND, parent)
trench_layer("Lo", ZT0, Z_GB); trench_layer("Hi", Z_GB, ZT1, LID)
GW = box("Groundwater", GX0, GX1, -0.02, GY1, GZ0, Z_GW, M_GW)
box("Lawn", GX0, DX0, 0.0, GY1, ZL, 0.0, M_LAWN); box("LawnR", DX1, GX1, 0.0, GY1, ZL, 0.0, M_LAWN)
# drainfield lid (topsoil + lawn over the trenches) lifts away on "drainfield" and drops back on "lawn"
box("LidTopsoil", DX0, DX1, 0.0, GY1, ZT1, ZL, M_GROUND, LID); box("LidLawn", DX0, DX1, 0.0, GY1, ZL, 0.0, M_LAWN, LID)
T_LU0, T_LD0 = C["drainfield"] - 0.1, C["lawn"] - 0.05
lid_z = PW([(0, 0), (T_LU0, 0), (T_LU0 + 0.8, 14.0), (T_LD0, 14.0), (T_LD0 + 0.6, 0)])     # flies up out of frame, drops back on "lawn"
lid_y = PW([(0, 0), (T_LU0, 0), (T_LU0 + 0.8, 4.0), (T_LD0, 4.0), (T_LD0 + 0.6, 0)])
bake(LID, "location", 2, [lid_z(t) for t in TS]); bake(LID, "location", 1, [lid_y(t) for t in TS])
# house (generic, no people) with a lit window
box("House", -15.0, -8.5, 0.8, 7.0, 0.0, 3.0, M_WALL)
bm = bmesh.new(); add_prism_y(bm, [(-15.4, 3.0), (-8.1, 3.0), (-11.75, 5.0)], 0.6, 7.2); mesh_obj("Roof", bm, M_ROOF)
box("Window", -12.6, -10.8, 0.76, 0.8, 1.2, 2.3, M_WIN); box("Door", -9.9, -9.0, 0.76, 0.8, 0.0, 2.1, M_ROOF)

# ---------- tank (concrete, cut at y = 0) ----------
bm = bmesh.new()
add_box(bm, TX0, TX1, 0.0, TY1, TZ0, IZ0)                      # floor
add_box(bm, TX0, TX1, 0.0, TY1, IZ1, TZ1)                      # lid
add_box(bm, TX0, IX0, 0.0, TY1, IZ0, IZ1); add_box(bm, IX1, TX1, 0.0, TY1, IZ0, IZ1)   # end walls
add_box(bm, TX0, TX1, TY1 - TW, TY1, IZ0, IZ1)                 # back wall
TANK = mesh_obj("Tank", bm, M_CONC); bevel_mod(TANK, 0.01, 1)
# access risers to the lawn (green lids)
RISERS = [(-1.3, 1.1), (1.3, 1.1)]
for i, (rx, ry) in enumerate(RISERS):
    bm = bmesh.new(); add_cyl(bm, 0.32, -TZ1 + 0.02, "Z", (rx, ry, (TZ1 + 0.02) / 2), 32); mesh_obj(f"Riser{i}", bm, M_CONC)
    bm = bmesh.new(); add_cyl(bm, 0.36, 0.05, "Z", (rx, ry, 0.045), 32); mesh_obj(f"RiserLid{i}", bm, M_RISER)
# front wall: closed in the hook, lifts away on "open"
FRONT = box("TankFrontWall", TX0, TX1, -0.16, 0.0, TZ0, TZ1, M_WALLF); bevel_mod(FRONT, 0.01, 1)
T_OPEN = C["open"]
key(FRONT, "location", F(T_OPEN - 0.05), (0, 0, 0)); key(FRONT, "location", F(T_OPEN + 0.8), (0.6, -1.6, -9.0))          # drops down out of frame
key(FRONT, "rotation_euler", F(T_OPEN - 0.05), (0, 0, 0)); key(FRONT, "rotation_euler", F(T_OPEN + 0.8), (0, 0, math.radians(6)))
vis(FRONT, 1, False); vis(FRONT, F(T_OPEN + 0.85), True)
# inlet baffle (concrete plate) and T outlet
X_BAF, X_TEE = IX0 + 0.42, IX1 - 0.25
BAFFLE = box("InletBaffle", X_BAF - 0.035, X_BAF + 0.035, 0.0, TY1 - TW, Z_IN - 0.95, IZ1, M_BAFFLE)
Z_TEE0 = -1.62
TEE = curve_obj("OutletTee", [(X_TEE, 0.0, IZ1 - 0.02), (X_TEE, 0.0, Z_TEE0)], 0.1, M_TEE)
TEE_ARM = curve_obj("OutletTeeArm", [(X_TEE, 0.0, Z_OUT), (TX1 + 0.05, 0.0, Z_OUT)], R_P, M_TEE)
# pipes: house -> inlet (slopes down), outlet -> drainfield header -> trench pipes
P_INLET = [(-8.6, 0.0, -0.18), (TX0 - 0.02, 0.0, Z_IN), (IX0 + 0.12, 0.0, Z_IN)]
INLET = curve_obj("InletPipe", P_INLET, R_P, M_PVC)
P_OUTLET = [(TX1 + 0.05, 0.0, Z_OUT), (DX0 + 0.35, 0.0, Z_DP)]
OUTLET = curve_obj("OutletPipe", P_OUTLET, R_P, M_PVC)
HEADER = curve_obj("DrainHeader", [(DX0 + 0.35, 0.0, Z_DP), (DX0 + 0.35, TRENCH_Y[-1][2], Z_DP)], R_P, M_DPIPE)
DPIPES = []
for i, (_, _, py) in enumerate(TRENCH_Y):
    DPIPES.append(curve_obj(f"DrainPipe{i}", [(DX0 + 0.35, py, Z_DP), (DX1 - 0.4, py, Z_DP)], R_P, M_DPIPE))
HOLE_X = [DX0 + 1.0 + 0.9 * k for k in range(int((DX1 - DX0 - 1.6) / 0.9))]
bm = bmesh.new()
for hx in HOLE_X: add_cyl(bm, 0.035, 0.02, "Y", (hx, -R_P + 0.005, Z_DP - 0.05), 12)
mesh_obj("Perforations", bm, M_HOLE)

# ---------- liquid layers ----------
LIQ = box("ClearLiquid", IX0, IX1, 0.0, TY1 - TW, IZ0, Z_L, M_LIQ)
# sludge: origin on the floor, height = scale z; scum: origin at the top, thickness = scale z (grows down)
SLUDGE = box("Sludge", IX0, IX1, -0.012, TY1 - TW - 0.01, 0.0, 1.0, M_SLUDGE); SLUDGE.location = (0, 0, IZ0)
SCUM = box("Scum", IX0, IX1, -0.012, TY1 - TW - 0.01, -1.0, 0.0, M_SCUM); SCUM.location = (0, 0, Z_L + 0.035)
T_SL1 = C["sludge"] + 0.4
SL = PW([(0, 0.10), (C["sorts"], 0.10), (T_SL1, 0.42), (C["break"], 0.42), (C["solids2"] + 0.6, 0.35), (C["sludge3"], 0.35),
         (C["builds"] + 1.0, 1.02), (C["pumps"] + 0.1, 1.02), (C["around"] - 0.25, 0.08)])
SC = PW([(0, 0.04), (C["float"], 0.04), (C["scum"] + 0.4, 0.22), (C["sludge3"], 0.22), (C["builds"] + 1.0, 0.36),
         (C["pumps"] + 0.1, 0.36), (C["around"] - 0.25, 0.04)])
bake(SLUDGE, "scale", 2, [SL(t) for t in TS]); bake(SCUM, "scale", 2, [SC(t) for t in TS])
# the liquid is murky before gravity sorts it, clear (dark teal) after
bc = B_LIQ.inputs["Base Color"]
key(bc, "default_value", F(C["sorts"]), (0.16, 0.12, 0.06, 1)); key(bc, "default_value", F(C["clear"] + 0.3), (0.035, 0.16, 0.18, 1))
# level line at the outlet invert (thin glowing bar on the cut face)
LEVEL = box("LevelLine", IX0 - 0.05, TX1 + 0.6, -0.03, -0.015, Z_L - 0.012, Z_L + 0.012, M_LEVEL)
# the hook flashes the level on the closed front wall
HOOK_LINE = box("HookLevelLine", TX0 - 0.1, TX1 + 0.1, -0.19, -0.17, Z_L - 0.02, Z_L + 0.02, M_LEVEL, FRONT)
vis(HOOK_LINE, 1, False); vis(HOOK_LINE, F(T_OPEN + 0.85), True)

# ---------- sorting particles, bacteria, middle arrow ----------
ME_SOLID, ME_FAT = sphere_mesh("SolidBit", 0.06, M_SOLID, 1), sphere_mesh("FatBit", 0.055, M_FAT, 1)
T_SO0, T_SO1 = C["then"] - 0.2, C["between"]
for i in range(28):
    o = bpy.data.objects.new(f"Solid{i}", ME_SOLID); CL.objects.link(o)
    o.scale = (random.uniform(0.7, 1.5),) * 3
    x0, z0 = random.uniform(IX0 + 0.6, IX1 - 0.4), random.uniform(IZ0 + 0.6, Z_L - 0.3)
    d0 = C["sink"] - 0.6 + random.uniform(-0.3, 0.6); d1 = d0 + random.uniform(1.0, 1.6)
    pz = [z0 + 0.04 * math.sin(t * 2 + i) if t < d0 else z0 + (IZ0 + SL(d1) * 0.9 - z0) * ease((t - d0) / (d1 - d0)) for t in TS]
    bake(o, "location", 2, pz); o.location[0] = x0; o.location[1] = -0.07
    windows(o, [(T_SO0, T_SO1)])
for i in range(18):
    o = bpy.data.objects.new(f"Fat{i}", ME_FAT); CL.objects.link(o)
    o.scale = (random.uniform(0.7, 1.4),) * 3
    x0, z0 = random.uniform(IX0 + 0.6, IX1 - 0.4), random.uniform(IZ0 + 0.7, Z_L - 0.35)
    d0 = C["grease"] - 0.3 + random.uniform(-0.2, 0.5); d1 = d0 + random.uniform(0.9, 1.4)
    zt = Z_L - 0.06
    pz = [z0 + 0.04 * math.sin(t * 2.3 + i) if t < d0 else z0 + (zt - z0) * ease((t - d0) / (d1 - d0)) for t in TS]
    bake(o, "location", 2, pz); o.location[0] = x0; o.location[1] = -0.07
    windows(o, [(T_SO0, T_SO1)])
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.05); ME_BUG = bpy.data.meshes.new("Bug"); bm.to_mesh(ME_BUG); bm.free()
ME_BUG.materials.append(M_BUG)
T_BU0, T_BU1 = C["bacteria"] - 0.15, C["now"] - 0.1
for i in range(22):
    o = bpy.data.objects.new(f"Bacterium{i}", ME_BUG); CL.objects.link(o)
    o.scale = (2.0, 1.0, 1.0); o.rotation_euler = (0, random.uniform(-0.6, 0.6), random.uniform(0, 3))
    x0, z0 = random.uniform(IX0 + 0.3, IX1 - 0.3), IZ0 + random.uniform(0.25, 0.75)
    ph, sp = random.uniform(0, 6), random.uniform(1.5, 2.6)
    bake(o, "location", 0, [x0 + 0.12 * math.sin(t * sp + ph) for t in TS]); bake(o, "location", 2, [z0 + 0.06 * math.sin(t * sp * 1.3 + ph) for t in TS])
    bake(o, "rotation_euler", 1, [0.5 * math.sin(t * sp + ph) for t in TS]); o.location[1] = -0.06
    windows(o, [(T_BU0, T_BU1)])
    key(o, "scale", F(T_BU0), (0.01, 0.01, 0.01)); key(o, "scale", F(T_BU0 + 0.4), (2.0, 1.0, 1.0))
# cyan arrow: the tee draws from the middle layer
bm = bmesh.new(); add_cyl(bm, 0.035, 0.55, "X", (0.275, 0, 0), 16)
res = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.1, radius2=0.0, depth=0.22); vs = res["verts"]
bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y")); bmesh.ops.translate(bm, verts=vs, vec=(0.66, 0, 0))
ME_ARW = bpy.data.meshes.new("ArrowMesh"); bm.to_mesh(ME_ARW); bm.free(); ME_ARW.materials.append(M_ARROW)
T_AR0, T_AR1 = C["draws"] - 0.1, C["that"] - 0.1
for i in range(3):
    o = bpy.data.objects.new(f"MiddleArrow{i}", ME_ARW); CL.objects.link(o)
    ph = i / 3
    bake(o, "location", 0, [X_TEE - 1.5 + 0.55 * (((t * 0.9) + ph) % 1.0) for t in TS])
    o.location[1] = -0.08; o.location[2] = Z_TEE0 - 0.06 + 0.0 * i
    o.rotation_euler = (0, math.radians(-12), 0)
    windows(o, [(T_AR0, T_AR1)])

# ---------- flow pulses (in = gold along the inlet, out = cyan along the outlet into the trench pipe) ----------
P_IN = [(-8.6, -0.15, -0.18), (TX0 - 0.02, -0.15, Z_IN), ((IX0 + X_BAF) / 2, -0.15, Z_IN), ((IX0 + X_BAF) / 2, -0.15, Z_IN - 0.85)]
P_OUT = [(X_TEE, -0.15, Z_TEE0 + 0.05), (X_TEE, -0.15, Z_OUT), (TX1 + 0.05, -0.15, Z_OUT), (DX0 + 0.35, -0.15, Z_DP), (DX1 - 0.5, -0.15, Z_DP)]
at_in, L_in = path_fn(P_IN); at_out, L_out = path_fn(P_OUT)
ME_PIN, ME_POUT = sphere_mesh("PulseInMesh", 0.075, M_IN), sphere_mesh("PulseOutMesh", 0.075, M_OUT)
W_IN = [(0.0, C["lets"]), (C["wastewater"] - 0.3, C["then"]), (C["so"], C["tshaped"]), (C["is"] - 0.1, DUR + 1)]
W_OUT = [(C["so"], C["trickles"]), (C["is"] - 0.1, DUR + 1)]
for i in range(9):
    o = bpy.data.objects.new(f"PulseIn{i}", ME_PIN); CL.objects.link(o)
    pts = [at_in(((t * 2.6 / L_in) + i / 9) % 1.0) for t in TS]
    pts = [p + Vector((0, 0.45, 0)) if (p.x > TX0 and t < T_OPEN + 0.3) else p for p, t in zip(pts, TS)]   # inside the closed tank: hidden behind the wall
    bake_vec(o, "location", pts); windows(o, W_IN)
for i in range(16):
    o = bpy.data.objects.new(f"PulseOut{i}", ME_POUT); CL.objects.link(o)
    bake_vec(o, "location", [at_out(((t * 3.2 / L_out) + i / 16) % 1.0) for t in TS]); windows(o, W_OUT)
# one gallon in, one gallon out (big blobs)
G_IN0, G_OUT0 = C["flows"] - 0.4, C["pushes"]
GIN = bpy.data.objects.new("GallonIn", sphere_mesh("GallonInMesh", 0.2, M_IN)); CL.objects.link(GIN)
bake_vec(GIN, "location", [at_in(lin((t - G_IN0) / 1.3)) for t in TS]); windows(GIN, [(G_IN0, G_IN0 + 1.35)])
GOUT = bpy.data.objects.new("GallonOut", sphere_mesh("GallonOutMesh", 0.2, M_OUT)); CL.objects.link(GOUT)
at_out3, _ = path_fn(P_OUT[:4])
bake_vec(GOUT, "location", [at_out3(ease((t - G_OUT0) / 1.6)) for t in TS]); windows(GOUT, [(G_OUT0, G_OUT0 + 1.65)])

# ---------- drainfield drips: clean water to the groundwater, germs stopped in the soil ----------
ME_DROP, ME_GERM = sphere_mesh("DropMesh", 0.05, M_OUT, 1), sphere_mesh("GermMesh", 0.045, M_GERM, 1)
T_DR0, T_DR1 = C["trickles"] - 0.25, C["but"] - 0.05
for i in range(30):
    o = bpy.data.objects.new(f"Drop{i}", ME_DROP); CL.objects.link(o)
    hx = random.choice(HOLE_X) + random.uniform(-0.25, 0.25); per, ph = random.uniform(2.2, 3.0), random.random()
    zs = []
    for t in TS:
        u = ((t / per) + ph) % 1.0; zs.append(Z_DP - 0.12 - (Z_DP - 0.12 - Z_GW - 0.1) * u)
    bake(o, "location", 2, zs); o.location[0] = hx; o.location[1] = -0.07
    windows(o, [(T_DR0, T_DR1)])
for i in range(16):
    o = bpy.data.objects.new(f"Germ{i}", ME_GERM); CL.objects.link(o)
    hx = random.choice(HOLE_X) + random.uniform(-0.3, 0.3); per, ph = random.uniform(1.8, 2.4), random.random()
    zstop = random.uniform(-3.4, -2.3); zs, sc = [], []
    for t in TS:
        u = ((t / per) + ph) % 1.0; z = Z_DP - 0.12 - (Z_DP - 0.12 - zstop) * min(1.0, u / 0.6)
        zs.append(z); sc.append(1.0 if u < 0.6 else max(0.0, 1.0 - (u - 0.6) / 0.25))
    bake(o, "location", 2, zs); o.location[0] = hx; o.location[1] = -0.075
    for ax in range(3): bake(o, "scale", ax, sc)
    windows(o, [(C["germs"] - 0.6, T_DR1)])

# ---------- pump truck (drives in on "truck", hose into the riser on "pumps") ----------
TRK = bpy.data.objects.new("PumpTruck", None); CL.objects.link(TRK)
box("TruckChassis", -2.6, 2.6, -0.85, 0.85, 0.5, 0.75, M_TYRE, TRK)
box("TruckCab", 1.4, 2.7, -0.85, 0.85, 0.75, 2.2, M_CAB, TRK); box("TruckGlass", 2.69, 2.72, -0.7, 0.7, 1.45, 2.05, M_WIN, TRK)
bm = bmesh.new(); add_cyl(bm, 0.8, 3.6, "X", (-0.6, 0, 1.55), 40); TTANK = mesh_obj("TruckTank", bm, M_TRUCK, TRK)
for wx in (-1.8, -0.9, 1.9):
    for wy in (-0.86, 0.86):
        bm = bmesh.new(); add_cyl(bm, 0.45, 0.32, "Y", (wx, wy, 0.45), 24); mesh_obj(f"Wheel{wx}{wy}", bm, M_TYRE, TRK)
X_TRK1 = -4.8
trk_x = PW([(0, -30.0), (C["three"] - 0.5, -30.0), (C["truck"] + 0.2, X_TRK1)])
bake(TRK, "location", 0, [trk_x(t) for t in TS]); TRK.location[1] = 2.6
windows(TRK, [(C["three"] - 0.55, C["around"] - 0.15)])
HOSE = curve_obj("Hose", [(X_TRK1 - 2.3, 2.6, 1.2), (X_TRK1 - 2.6, 2.0, 0.4), (-2.2, 1.4, 0.25), (RISERS[0][0], RISERS[0][1], 0.2),
                          (RISERS[0][0], RISERS[0][1], IZ0 + 0.3)], 0.07, M_HOSE)
windows(HOSE, [(C["truck"] + 0.2, C["around"] - 0.15)])
vis_lid = bpy.data.objects["RiserLid0"]; windows(vis_lid, [(0, C["truck"] + 0.2), (C["around"] - 0.15, DUR + 1)])

# ---------- Set B: 1860s masonry tank (x offset 2000) ----------
OX = 2000.0
BX0, BX1, BZ0, BZ1, BW = OX - 1.9, OX + 1.9, -2.7, -0.7, 0.28
for nm, (x0, x1, z0, z1) in {"L": (OX - 16, BX0, -6.0, ZL), "U": (BX0, BX1, -6.0, BZ0), "R": (BX1, OX + 16, -6.0, ZL)}.items():
    box(f"B_Ground_{nm}", x0, x1, 0.0, GY1, z0, z1, M_GROUND)
box("B_LawnL", OX - 16, BX0, 0.0, GY1, ZL, 0.0, M_LAWN); box("B_LawnR", BX1, OX + 16, 0.0, GY1, ZL, 0.0, M_LAWN)
bm = bmesh.new()
add_box(bm, BX0, BX1, 0.0, 2.0, BZ0, BZ0 + BW); add_box(bm, BX0, BX0 + BW, 0.0, 2.0, BZ0, BZ1); add_box(bm, BX1 - BW, BX1, 0.0, 2.0, BZ0, BZ1)
add_box(bm, BX0, BX1, 2.0 - BW, 2.0, BZ0, BZ1)
mesh_obj("B_MasonryTank", bm, M_STONE)
OLDW = box("B_Water", BX0 + BW, BX1 - BW, 0.0, 2.0 - BW, BZ0 + BW, BZ1 - 0.25, M_OLDW)
OLDS = box("B_Sludge", BX0 + BW, BX1 - BW, -0.012, 2.0 - BW, BZ0 + BW, BZ0 + BW + 0.05, M_OLDS)
# sealed stone lid: hinge on the left edge, opens on "opened"
HINGE = bpy.data.objects.new("B_LidHinge", None); CL.objects.link(HINGE); HINGE.location = (BX0, 0, BZ1 + 0.25)
box("B_Lid", 0.0, BX1 - BX0, -0.02, 2.0, -0.25, 0.0, M_LID, HINGE)
key(HINGE, "rotation_euler", F(C["opened"] - 0.1), (0, 0, 0)); key(HINGE, "rotation_euler", F(C["opened"] + 0.9), (0, math.radians(-62), 0))
box("B_CoverSoil", 0.0, BX1 - BX0, 0.0, GY1, 0.0, ZL - (BZ1 + 0.25), M_GROUND, HINGE)
box("B_CoverLawn", 0.0, BX1 - BX0, 0.0, GY1, ZL - (BZ1 + 0.25), -(BZ1 + 0.25), M_LAWN, HINGE)
box("B_Cottage", OX - 11.5, OX - 6.5, 0.8, 6.0, 0.0, 2.6, M_STONE)
bm = bmesh.new(); add_prism_y(bm, [(OX - 11.9, 2.6), (OX - 6.1, 2.6), (OX - 9.0, 4.3)], 0.6, 6.2); mesh_obj("B_CottageRoof", bm, M_ROOF)
box("B_CottageWindow", OX - 9.8, OX - 8.6, 0.76, 0.8, 1.0, 1.9, M_WIN)
curve_obj("B_ClayPipe", [(OX - 7.0, 0.0, -0.2), (BX0 - 0.02, 0.0, BZ1 - 0.35), (BX0 + BW + 0.15, 0.0, BZ1 - 0.35)], 0.12, M_CLAYP)

# ---------- highlights ----------
def pulse(bsdf, t0, peak=2.5, hold=0.9, rgb=None):
    s = bsdf.inputs["Emission Strength"]
    if rgb: bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
    key(s, "default_value", F(t0 - 0.15), 0.0); key(s, "default_value", F(t0 + 0.12), peak)
    key(s, "default_value", F(t0 + hold), peak * 0.6); key(s, "default_value", F(t0 + hold + 0.5), 0.0)
def hold_glow(bsdf, t0, t1, peak, base=0.0):
    s = bsdf.inputs["Emission Strength"]
    key(s, "default_value", F(t0 - 0.15), base); key(s, "default_value", F(t0 + 0.15), peak)
    key(s, "default_value", F(t1), peak); key(s, "default_value", F(t1 + 0.4), base)
s = B_LEVEL.inputs["Emission Strength"]
for t0, t1 in [(C["full"] - 0.1, C["lets"]), (C["liquid2"], C["every"])]:
    key(s, "default_value", F(t0 - 0.12), 0.0); key(s, "default_value", F(t0 + 0.1), 6.0); key(s, "default_value", F(t1), 6.0); key(s, "default_value", F(t1 + 0.3), 0.0)
windows(LEVEL, [(C["liquid2"] - 0.15, C["every"] + 0.35)])
hold_glow(B_BAFFLE, C["baffle"], C["then"] - 0.2, 1.2)
hold_glow(B_SLUDGE, C["sludge"], C["grease"] - 0.1, 0.5)
hold_glow(B_SCUM, C["scum"], C["between"] + 0.2, 0.6)
s = B_LIQ.inputs["Emission Strength"]; B_LIQ.inputs["Emission Color"].default_value = (*CYAN, 1)
key(s, "default_value", F(C["clear"] - 0.15), 0.0); key(s, "default_value", F(C["clear"] + 0.15), 0.35); key(s, "default_value", F(C["bacteria"]), 0.0)
hold_glow(B_TEE, C["tshaped"], C["middle"] + 0.4, 1.4)
pulse(B_SCUM, C["stay"] - 0.1, 0.9, 0.7, RED); pulse(B_SLUDGE, C["stay"] - 0.1, 0.9, 0.7, RED)
hold_glow(B_DPIPE, C["perforated"], C["laid"] + 0.3, 1.2)
hold_glow(B_GRAVEL, C["gravel"], C["lawn"] + 0.2, 0.5)
hold_glow(B_GW, C["groundwater"], C["but"] + 0.3, 1.5, 0.15)
pulse(B_SLUDGE, C["builds"], 0.7, 1.6, GOLD)
hold_glow(B_HOSE, C["pumps"] + 0.1, C["around"] - 0.25, 1.0)
hold_glow(B_LID, C["sealed"], C["years2"] + 0.2, 0.6)
hold_glow(B_OLDS, C["almost"], C["is"], 2.5)

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 35
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 11; cam_d.dof.focus_object = TGT
cam_d.clip_start = 0.05; cam_d.clip_end = 400
DXM = (DX0 + DX1) / 2
SHOTS = [  # (time, cam, target, lens[, "cut"])
    (0.0, (-2.0, -9.0, 2.4), (-1.0, 0.0, -1.8), 22),
    (C["full"], (-0.3, -8.0, 0.8), (0.0, 0.0, -2.0), 24),
    (C["lets"], (0.2, -8.6, 1.2), (0.0, 0.0, -2.1), 26),
    (C["wastewater"], (-4.2, -8.8, 1.6), (-3.2, 0.0, -1.1), 24),
    (C["buried"] - 0.3, (-1.2, -9.2, 1.0), (-0.9, 0.0, -1.7), 24),  # whole tank on "buried tank"
    (C["baffle"] - 0.2, (-1.4, -4.6, -0.4), (-1.6, 0.0, -1.3), 28),
    (C["then"], (0.0, -7.6, -0.4), (0.0, 0.0, -2.2), 26),
    (C["bacteria"] - 0.2, (0.3, -5.6, -1.7), (0.2, 0.0, -2.2), 30),
    (C["now"], (0.6, -7.2, -0.2), (0.6, 0.0, -1.7), 26),
    (C["liquid2"], (1.6, -4.6, -0.2), (1.8, 0.0, -1.3), 28),
    (C["so"], (0.4, -8.4, -0.2), (0.4, 0.0, -1.9), 24),
    (C["tshaped"] - 0.2, (1.3, -4.2, -0.8), (1.6, 0.0, -1.55), 28),
    (C["that"], (5.6, -12.0, 2.0), (6.0, 0.0, -1.6), 22),
    (C["drainfield"] - 0.1, (DXM - 1.0, -6.0, 10.5), (DXM + 0.5, 2.6, -1.2), 20),
    (C["lawn"] + 0.2, (DXM - 1.5, -6.5, 9.8), (DXM + 0.5, 2.4, -1.2), 20),
    (C["trickles"] - 0.25, (DXM - 2.0, -8.6, -1.8), (DXM - 2.0, 0.0, -3.6), 24),
    (C["groundwater"] - 0.3, (DXM - 2.0, -9.4, -2.6), (DXM - 2.0, 0.0, -4.4), 24),
    (C["but"] - 0.05, (0.0, -8.4, -0.4), (0.0, 0.0, -1.9), 26, "cut"),
    (C["three"] - 0.4, (-3.2, -11.0, 3.4), (-2.4, 1.6, -1.0), 24),
    (C["pumps"] + 0.4, (-3.0, -10.6, 3.2), (-2.2, 1.6, -1.2), 24),
    (C["around"] - 0.15, (OX - 3.5, -11.0, 1.8), (OX - 3.0, 0.0, -1.2), 24, "cut"),
    (C["sealed"] - 0.2, (OX - 0.6, -8.4, 0.8), (OX, 0.0, -1.5), 26),
    (C["opened"], (OX, -7.4, 0.2), (OX, 0.0, -1.8), 26),
    (C["is"] - 0.1, (1.5, -9.5, 1.2), (2.0, 0.0, -1.8), 22, "cut"),
    (C["end"], (1.5, -11.0, 1.8), (2.0, 0.0, -1.8), 22),
]
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = Vector(SHOTS[k][1]), Vector(SHOTS[k][2]), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t1 = SHOTS[k + 1][0]; tr = 0.7 if (t1 - SHOTS[k][0]) > 1.4 else (t1 - SHOTS[k][0]) * 0.5
        if t > t1 - tr:
            u = ease((t - (t1 - tr)) / tr)
            l0, g0, n0 = l0.lerp(Vector(SHOTS[k + 1][1]), u), g0.lerp(Vector(SHOTS[k + 1][2]), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.06 * math.sin(t * 0.7), 0.0, 0.04 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()

# ---------- world + lights: dark studio ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
for n in list(wn):
    if n.type == "BACKGROUND": wn.remove(n)
wout = next(n for n in wn if n.type == "OUTPUT_WORLD")
grad_tc = wn.new("ShaderNodeTexCoord"); grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
wl.new(grad_tc.outputs["Window"], grad.inputs["Vector"])
gr = wn.new("ShaderNodeValToRGB"); e = gr.color_ramp.elements; e[0].color = (0.004, 0.006, 0.009, 1); e[1].color = (0.03, 0.045, 0.06, 1)
wl.new(grad.outputs["Fac"], gr.inputs[0])
bg_dark = wn.new("ShaderNodeBackground"); wl.new(gr.outputs[0], bg_dark.inputs["Color"])
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.12
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_ref.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
def area(name, loc, size, power, rgb=(1, 1, 1), target=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
def target(name, loc):
    o = bpy.data.objects.new(name, None); scene.collection.objects.link(o); o.location = loc; return o
LT_T, LT_D, LT_B = target("LightTargetTank", (0, 0, -1.6)), target("LightTargetDrain", (DXM, 0, -2.5)), target("LightTargetB", (OX, 0, -1.4))
area("KeyTank", (-5.0, -10.0, 6.0), 6.0, 1150, (1.0, 0.95, 0.88), LT_T)
area("FillTank", (4.0, -8.0, -3.0), 5.0, 500, (0.80, 0.88, 1.0), LT_T)
area("RimYard", (-6.0, 8.0, 8.0), 8.0, 1200, (0.70, 0.82, 1.0), LT_T)
area("HouseKey", (-12.0, -9.0, 7.0), 6.0, 900, (1.0, 0.93, 0.85), target("LightTargetHouse", (-11.0, 2.0, 1.5)))
area("KeyDrain", (DXM - 4.0, -11.0, 6.0), 9.0, 2600, (1.0, 0.95, 0.88), LT_D)
area("FillDrain", (DXM + 6.0, -9.0, -5.0), 7.0, 900, (0.75, 0.85, 1.0), LT_D)
area("KeyB", (OX - 5.0, -9.0, 5.0), 6.0, 1500, (1.0, 0.82, 0.60), LT_B)
area("FillB", (OX + 5.0, -7.0, -2.0), 5.0, 400, (0.75, 0.85, 1.0), LT_B)
area("CamFill", (0, 0, 0), 2.5, 60, (1.0, 0.96, 0.9), TGT).parent = cam

# ---------- render settings ----------
r = scene.render; r.engine = "CYCLES"
use_gpu = False
if "--cpu" not in ARGS:
    cp = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA"):
        try:
            cp.compute_device_type = dev; cp.get_devices()
            if any(d.type == dev for d in cp.devices): use_gpu = True; break
        except Exception: continue
    if use_gpu:
        for d in cp.devices: d.use = d.type == cp.compute_device_type
scene.cycles.device = "GPU" if use_gpu else "CPU"
print("Cycles device:", scene.cycles.device)
scene.cycles.samples = int(arg("--samples", "24")); scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = 0.03
scene.cycles.use_denoising = True
try: scene.cycles.denoiser = "OPTIX" if use_gpu else "OPENIMAGEDENOISE"
except Exception: pass
scene.cycles.max_bounces = 8; scene.cycles.transmission_bounces = 6
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = False
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
prefs.keyframe_new_interpolation_type = "BEZIER"

# ---------- export cues, events and projected anchors for the typography ----------
ZM = (IZ0 + Z_L) / 2
ANCH = {"tank": (None, Vector((0.0, 0.0, TZ1 + 0.1))), "inlet": (None, Vector((-5.0, -0.1, (Z_IN - 0.18) / 2 - 0.15))),
        "baffle": (None, Vector((X_BAF, 0.0, Z_IN - 0.6))), "sludge": (SLUDGE, Vector((0.9, 0.0, 0.5))),
        "scum": (SCUM, Vector((-0.6, 0.0, -0.5))), "clear": (None, Vector((-0.4, 0.0, ZM + 0.2))),
        "bacteria": (None, Vector((-0.6, 0.0, IZ0 + 0.5))), "level": (None, Vector((TX1 + 0.4, 0.0, Z_L))),
        "tee": (None, Vector((X_TEE, 0.0, Z_TEE0 + 0.15))), "outlet": (None, Vector((TX1 + 1.5, 0.0, Z_OUT - 0.04))),
        "drainpipe": (None, Vector((DXM + 2.0, TRENCH_Y[1][2], Z_DP))), "gravel": (None, Vector((DXM - 3.0, TRENCH_Y[2][2], ZT1))),
        "trench_front": (None, Vector((DXM - 4.0, 0.0, ZT0 + 0.3))), "soil": (None, Vector((DXM - 4.0, 0.0, -3.0))),
        "groundwater": (None, Vector((DXM - 4.0, 0.0, Z_GW - 0.6))), "truck": (TRK, Vector((-0.6, -0.8, 2.3))),
        "hose": (None, Vector((RISERS[0][0], RISERS[0][1], 0.3))), "old_lid": (None, Vector((OX + 0.6, 0.0, BZ1 + 0.15))),
        "old_solids": (None, Vector((OX + 0.5, 0.0, BZ0 + BW + 0.05))), "house": (None, Vector((-11.75, 0.8, 2.2)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, (ob, local) in ANCH.items():
        w = local if ob is None else ob.matrix_world @ local
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)])
events = {"open": round(T_OPEN + 0.1, 3), "gallon_in": round(G_IN0, 3), "gallon_out": round(G_OUT0, 3),
          "lid_up": round(T_LU0, 3), "lid_down": round(T_LD0, 3), "truck_in": round(C["three"] - 0.5, 3), "truck_stop": round(C["truck"] + 0.2, 3),
          "pump": [round(C["pumps"] + 0.1, 3), round(C["around"] - 0.25, 3)], "old_lid": round(C["opened"] - 0.1, 3),
          "set_b": [round(C["around"] - 0.15, 3), round(C["is"] - 0.1, 3)], "flow_in": W_IN, "flow_out": W_OUT,
          "drips": [round(T_DR0, 3), round(T_DR1, 3)], "sludge_up": [round(C["sludge3"], 3), round(C["builds"] + 1.0, 3)]}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS", events, "DUR", DUR, "FRAMES", FRAMES)

save = arg("--save")
if save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))
out = arg("--out", os.path.join(HERE, "checks"))
if "--stills" in ARGS:
    os.makedirs(out, exist_ok=True)
    r.resolution_percentage = int(arg("--pct", "25"))
    import time
    for fr in [int(x) for x in arg("--stills").split(",")]:
        scene.frame_set(fr); r.filepath = os.path.join(out, f"still_{fr:04d}.png")
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("STILL", fr, round(time.time() - t0, 1))
if "--anim" in ARGS:
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
