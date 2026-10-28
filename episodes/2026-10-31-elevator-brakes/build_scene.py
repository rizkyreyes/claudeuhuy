# Elevator-Brakes-3D: why elevators don't fall, a traction-elevator shaft cutaway in a dark studio, Blender Cycles. Every cue is a word in the VO.
# Set A (origin): shaft cut open at the front (y < -1.3): car on two guide rails, 3 hoist ropes over the traction sheave to a counterweight,
#   machine on top (sheave, motor, drum brake with springs + electromagnet), overspeed governor with its own rope loop, lever + safety
#   wedges on the car, spring buffer (car) and oil buffer (counterweight) in the pit.
# Set B (x = 2000): an 1854-style hoisting platform between two toothed wooden posts, wagon spring on top, rope cut -> spring catches the teeth.
# No people anywhere (the 1854 platform rides empty; Otis appears only as a name on screen). Sizes are illustrative, none are spoken.
# Car height, counterweight, ropes, governor, lever, wedges, sparks, buffers and the platform are baked per frame.
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
random.seed(31)

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
for name, word in [("what", "what"), ("stops", "stops"), ("elevator", "elevator"), ("falling", "falling"), ("lets", "let's"),
                   ("cut", "cut"), ("open", "open"), ("car", "car"), ("hangs", "hangs"), ("three", "three"), ("steel", "steel"),
                   ("ropes", "ropes"), ("together", "together"), ("stronger", "stronger"), ("load", "load"), ("heavy", "heavy"),
                   ("counterweight", "counterweight"), ("balances", "balances"), ("motor", "motor"), ("lifts", "lifts"),
                   ("difference", "difference"), ("up", "up"), ("top", "top"), ("motor2", "motor"), ("brake", "brake"),
                   ("backwards", "backwards"), ("springs", "springs"), ("squeeze", "squeeze"), ("shut", "shut"),
                   ("electricity", "electricity"), ("pulls", "pulls"), ("open2", "open"), ("so", "so"), ("power", "power"),
                   ("out", "out"), ("brake2", "brake"), ("clamps", "clamps"), ("itself", "itself"), ("but", "but"),
                   ("every", "every"), ("rope", "rope"), ("snapped", "snapped"), ("heres", "here's"), ("clever", "clever"),
                   ("second", "second"), ("thinner", "thinner"), ("loops", "loops"), ("car2", "car"), ("wheel", "wheel"),
                   ("called", "called"), ("governor", "governor"), ("inside", "inside"), ("spinning", "spinning"),
                   ("weights", "weights"), ("spin", "spin"), ("fast", "fast"), ("fly", "fly"), ("outward", "outward"),
                   ("catch", "catch"), ("lock", "lock"), ("thin", "thin"), ("rope2", "rope"), ("stops2", "stops"),
                   ("car3", "car"), ("keeps", "keeps"), ("dropping", "dropping"), ("yanks", "yanks"), ("lever", "lever"),
                   ("that", "that"), ("lever2", "lever"), ("jams", "jams"), ("steel2", "steel"), ("wedges", "wedges"),
                   ("guide", "guide"), ("rails", "rails"), ("both", "both"), ("own", "own"), ("weight", "weight"),
                   ("drives", "drives"), ("tighter", "tighter"), ("car4", "car"), ("grinds", "grinds"), ("stop", "stop"),
                   ("no", "no"), ("needed", "needed"), ("still", "still"), ("enough", "enough"), ("bottom", "bottom"),
                   ("shaft2", "shaft"), ("buffers", "buffers"), ("springs2", "springs"), ("oil", "oil"), ("pistons", "pistons"),
                   ("catch2", "catch"), ("this", "this"), ("idea", "idea"), ("y1854", "1854"), ("new", "new"), ("york", "york"),
                   ("mechanic", "mechanic"), ("elisha", "elisha"), ("otis", "otis"), ("rode", "rode"), ("platform", "platform"),
                   ("crowd", "crowd"), ("cut2", "cut"), ("held", "held"), ("do", "do"), ("trust", "trust"),
                   ("elevator2", "elevator"), ("stairs", "stairs"), ("tell", "tell"), ("comments", "comments")]:
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
    for t0, t1 in wins:
        if t0 <= 0: vis(obj, 1, False)
        else: vis(obj, F(t0), False)
        vis(obj, F(t1), True)
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
CL = coll("ElevatorShaft")
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
def glow(bsdf, keys):
    """Emission strength keys [(t, value), ...] (linear between them)."""
    inp = bsdf.inputs["Emission Strength"]
    for t, v in keys:
        inp.default_value = v; inp.keyframe_insert("default_value", frame=F(t))
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
M_CONC, _ = mat("ShaftConcrete", (0.17, 0.17, 0.17), 0.9, 0.0, GOLD, 18)
M_CUT, _ = mat("CutFace", (0.40, 0.38, 0.35), 0.85, 0.0, GOLD, 30)
M_FRONT, _ = mat("FrontWall", (0.30, 0.30, 0.30), 0.88, 0.0, GOLD, 18)
M_LDOOR, _ = mat("LandingDoor", (0.55, 0.57, 0.60), 0.3, 0.85)
M_SILL, _ = mat("Sill", (0.62, 0.62, 0.60), 0.35, 0.9)
M_RAIL, B_RAIL = mat("GuideRail", (0.42, 0.44, 0.47), 0.3, 0.9, GOLD)
M_BRKT, _ = mat("Bracket", (0.20, 0.21, 0.22), 0.5, 0.7)
M_CAB, _ = mat("CabWall", (0.70, 0.71, 0.73), 0.25, 0.9)
M_CABIN, _ = mat("CabInterior", (0.62, 0.52, 0.40), 0.45, 0.0)
M_CFLOOR, _ = mat("CabFloor", (0.10, 0.10, 0.11), 0.6)
M_CLIGHT, B_CLIGHT = mat("CabLight", (1.0, 0.92, 0.78), 0.4, 0.0, (1.0, 0.90, 0.72)); B_CLIGHT.inputs["Emission Strength"].default_value = 6.0
M_FRAME, _ = mat("CarFrame", (0.08, 0.20, 0.36), 0.45, 0.6)
M_ROPE, B_ROPE = mat("HoistRope", (0.55, 0.56, 0.58), 0.35, 1.0, GOLD)
M_STUB, B_STUB = mat("BrokenRope", (0.55, 0.56, 0.58), 0.35, 1.0, RED)
M_CW, B_CW = mat("Counterweight", (0.30, 0.31, 0.33), 0.5, 0.8, GOLD)
M_CWF, _ = mat("CwFrame", (0.08, 0.20, 0.36), 0.45, 0.6)
M_SHEAVE, _ = mat("Sheave", (0.25, 0.27, 0.30), 0.35, 0.9)
M_SPOKE, _ = mat("SheaveMark", (0.85, 0.62, 0.18), 0.4, 0.3)
M_MOTOR, B_MOTOR = mat("Motor", (0.12, 0.30, 0.48), 0.4, 0.5, GOLD)
M_DRUM, _ = mat("BrakeDrum", (0.62, 0.64, 0.66), 0.25, 1.0)
M_ARM, _ = mat("BrakeArm", (0.10, 0.11, 0.12), 0.5, 0.6)
M_PAD, B_PAD = mat("BrakePad", (0.25, 0.18, 0.12), 0.8, 0.0, GOLD)
M_SPRING, B_SPRING = mat("BrakeSpring", (0.75, 0.55, 0.15), 0.35, 0.9, GOLD)
M_MAG, B_MAG = mat("Electromagnet", (0.30, 0.10, 0.08), 0.4, 0.4, CYAN)
M_COPPER, _ = mat("Copper", (0.80, 0.42, 0.20), 0.35, 1.0)
M_BED, _ = mat("Bedplate", (0.16, 0.17, 0.18), 0.5, 0.6)
M_GOV, B_GOV = mat("Governor", (0.62, 0.64, 0.66), 0.3, 1.0, RED)
M_FLY, B_FLY = mat("Flyweights", (0.85, 0.62, 0.18), 0.35, 0.8, RED)
M_GROPE, B_GROPE = mat("GovernorRope", (0.78, 0.80, 0.82), 0.4, 0.8, CYAN)
M_LEVER, B_LEVER = mat("SafetyLever", (0.85, 0.62, 0.18), 0.35, 0.8, GOLD)
M_WEDGE, B_WEDGE = mat("SafetyWedge", (0.70, 0.71, 0.73), 0.25, 1.0, (1.0, 0.45, 0.15))
M_HOUS, _ = mat("SafetyHousing", (0.12, 0.13, 0.14), 0.45, 0.7)
M_SPARK, B_SPARK = mat("Sparks", (1.0, 0.7, 0.3), 0.4, 0.0, (1.0, 0.62, 0.22)); B_SPARK.inputs["Emission Strength"].default_value = 30.0
M_BSPRING, B_BSPRING = mat("BufferSpring", (0.75, 0.55, 0.15), 0.35, 0.9, GOLD)
M_OIL, B_OIL = mat("OilBuffer", (0.12, 0.30, 0.48), 0.35, 0.6, CYAN)
M_PISTON, _ = mat("Piston", (0.85, 0.86, 0.88), 0.15, 1.0)
M_PIT, _ = mat("PitFloor", (0.12, 0.12, 0.12), 0.9, 0.0, GOLD, 20)
# Set B
M_WOOD, _ = mat("OldWood", (0.36, 0.22, 0.11), 0.75, 0.0, GOLD, 8)
M_DARKW, _ = mat("FloorWood", (0.13, 0.08, 0.05), 0.7, 0.0, GOLD, 6)
M_IRON, B_IRON = mat("OldIron", (0.20, 0.20, 0.21), 0.55, 0.8, GOLD)
M_LEAF, B_LEAF = mat("WagonSpring", (0.22, 0.22, 0.23), 0.4, 0.9, GOLD)
M_HEMP, B_HEMP = mat("HempRope", (0.62, 0.50, 0.30), 0.85, 0.0, RED)

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
    (x0, x1), (y0, y1), (z0, z1) = sorted((x0, x1)), sorted((y0, y1)), sorted((z0, z1))
    r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
    bmesh.ops.scale(bm, verts=vs, vec=(x1 - x0, y1 - y0, z1 - z0))
    bmesh.ops.translate(bm, verts=vs, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def box(name, x0, x1, y0, y1, z0, z1, m_, parent=None):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1); return mesh_obj(name, bm, m_, parent)
def add_cyl(bm, r, depth, axis, center, seg=32, mi=0, r2=None):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth); vs = res["verts"]
    if axis == "X": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    if axis == "Y": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, verts=vs, vec=center)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def cyl(name, r, depth, axis, center, m_, parent=None, seg=32):
    bm = bmesh.new(); add_cyl(bm, r, depth, axis, center, seg); return mesh_obj(name, bm, m_, parent)
def add_prism_x(bm, poly, x0, x1, mi=0):
    """Extrude a polygon given in (y, z) between x0 and x1."""
    a = [bm.verts.new((x0, y, z)) for y, z in poly]; b = [bm.verts.new((x1, y, z)) for y, z in poly]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(poly)
    for i in range(n): fs.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def bevel_mod(o, w=0.01, seg=2):
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = w; bv.segments = seg; bv.limit_method = "ANGLE"
def curve_obj(name, pts, depth, m_, res=3, link=True, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    if m_: cu.materials.append(m_)
    o = bpy.data.objects.new(name, cu)
    if link: CL.objects.link(o)
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o
def arc_pts(cx, cy, cz, r, a0, a1, n=40):
    """Points on a circle in the x-z plane (angles in degrees, 0 = +x, 90 = +z)."""
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), cy, cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
def helix_pts(p0, p1, r, turns, axis="Z", n_per=16):
    pts = []; N = int(turns * n_per)
    for k in range(N + 1):
        u = k / N; a = 2 * math.pi * turns * u
        if axis == "Z": pts.append((p0[0] + r * math.cos(a), p0[1] + r * math.sin(a), p0[2] + (p1[2] - p0[2]) * u))
        else: pts.append((p0[0] + (p1[0] - p0[0]) * u, p0[1] + r * math.sin(a), p0[2] + r * math.cos(a)))
    return pts
def rope_obj(name, r, m_, x, y):
    """Unit rope hanging DOWN from its origin (z 0 .. -1): scale z = length."""
    bm = bmesh.new(); add_cyl(bm, r, 1.0, "Z", (0, 0, -0.5), 12); o = mesh_obj(name, bm, m_); o.location = (x, y, 0); return o
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); CL.objects.link(o); o.location = loc
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o

# ---------- easing, piecewise curves ----------
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

# ---------- layout ----------
WX0, WX1, WY0, WY1 = -2.4, 3.1, -1.3, 1.3          # shaft inner box (front open at y = -1.3)
WT = 0.3                                           # wall thickness
ZP = -1.6                                          # pit floor
Z_SLAB = 26.2                                      # machine-room floor
FLOOR_H = 3.2
RX = 1.17                                          # guide-rail blade centre |x|
SX, SZ, SR = 1.15, 27.8, 1.15                      # traction sheave centre (x, z) and rope radius
CWX, CWH = 2.3, 2.4                                # counterweight centre x and height
ROPE_Y = [-0.2, 0.0, 0.2]
K_CW = 23.0                                        # car z + counterweight z (ropes keep a fixed length)
GX, GY, GZ, RG = -1.75, -0.35, 26.9, 0.32          # governor sheave
GPZ = ZP + 0.6                                     # governor tension pulley centre z
OX = 2000.0                                        # Set B offset

# ---------- motion: car height (car floor z) ----------
T_SNAP = C["snapped"]
T_SLOW, T_FAST0, T_FAST1, T_LOCK, T_CREEP = C["heres"], C["spin"], C["fly"], C["lock"], C["thin"]
T_WEDGE = C["jams"] + 0.3                          # wedges touch the rails
T_STOP = C["stop"] + 0.2
T_PIT = C["still"] - 0.08                          # hard cut to the pit
T_LAND = C["catch2"] + 0.05
T_B0, T_B1 = C["this"] - 0.1, C["do"] - 0.1        # Set B window
T_CTA = T_B1
BR_OPEN = [(C["counterweight"] + 0.1, C["difference"] + 0.6), (C["pulls"], C["out"] + 0.1)]     # brake released (magnet on)
z_normal = PW([(0, 12.0), (C["balances"] - 0.2, 12.0), (C["difference"] + 0.5, 16.0),
               (C["pulls"] + 0.15, 16.0), (C["out"] + 0.1, 17.1)])
def v_fall(t):
    """Downward speed after the ropes snap: a short real drop, then the explainer runs in slow motion."""
    if t < T_SLOW: return 2.5 * (t - T_SNAP)
    if t < T_FAST0: return 0.25
    if t < T_FAST1: return 0.25 + 0.45 * ease((t - T_FAST0) / (T_FAST1 - T_FAST0))
    if t < T_LOCK: return 0.70
    if t < T_CREEP: return 0.70 + (0.06 - 0.70) * ease((t - T_LOCK) / (T_CREEP - T_LOCK))
    if t < T_WEDGE: return 0.06
    return 0.06 * (1 - lin((t - T_WEDGE) / (T_STOP - T_WEDGE)))
CAR_Z, CW_Z, V_CAR = [], [], []
zf = z_normal(T_SNAP)
for i, t in enumerate(TS):
    if t < T_SNAP: z = z_normal(t)
    elif t < T_PIT: zf -= v_fall(t) / FPS; z = zf
    elif t < T_B0:
        z = -0.45 + 0.5 * (T_LAND - t) if t < T_LAND else -0.45 - 0.25 * ease((t - T_LAND) / 0.5)
    elif t < T_CTA: z = -0.7
    else: z = 9.0 + 1.5 * lin((t - T_CTA) / (DUR - T_CTA))
    CAR_Z.append(z)
for i, t in enumerate(TS):
    if t < T_SNAP or t >= T_CTA: CW_Z.append(K_CW - CAR_Z[i])
    else:
        z0 = K_CW - z_normal(T_SNAP); z = z0 - 0.5 * 9.81 * (t - T_SNAP) ** 2
        CW_Z.append(max(-0.6, z))
for i in range(FRAMES): V_CAR.append(0.0 if i == 0 else (CAR_Z[i] - CAR_Z[i - 1]) * FPS)
Z_LOCK = CAR_Z[F(T_LOCK) - 1]
def car_z(t): return CAR_Z[max(0, min(FRAMES - 1, int(round(t * FPS))))]

# ---------- Set A: shaft ----------
box("BackWall", WX0 - WT, WX1 + WT, WY1, WY1 + WT, ZP - 0.3, Z_SLAB + 4.3, M_CONC)
box("WallL", WX0 - WT, WX0, WY0, WY1, ZP - 0.3, Z_SLAB + 4.3, M_CONC)
box("WallR", WX1, WX1 + WT, WY0, WY1, ZP - 0.3, Z_SLAB + 4.3, M_CONC)
box("CutFaceL", WX0 - WT, WX0, WY0 - 0.01, WY0, ZP - 0.3, Z_SLAB + 4.3, M_CUT)
box("CutFaceR", WX1, WX1 + WT, WY0 - 0.01, WY0, ZP - 0.3, Z_SLAB + 4.3, M_CUT)
box("PitFloor", WX0 - WT, WX1 + WT, WY0, WY1 + WT, ZP - 0.3, ZP, M_PIT)
box("Foundation", WX0 - WT - 0.6, WX1 + WT + 0.6, WY0, WY1 + WT + 0.3, ZP - 5.0, ZP - 0.3, M_CONC)
box("FoundationCut", WX0 - WT - 0.6, WX1 + WT + 0.6, WY0 - 0.01, WY0, ZP - 5.0, ZP - 0.3, M_CUT)
box("Roof", WX0 - WT, WX1 + WT, WY0, WY1 + WT, Z_SLAB + 4.3, Z_SLAB + 4.6, M_CONC)
# machine-room floor, with slots where the ropes pass (car side x 0, counterweight side x 2.3, governor x -1.43 / -2.07)
gaps = [(GX - RG - 0.09, GX - RG + 0.09), (GX + RG - 0.09, GX + RG + 0.09), (-0.12, 0.12), (CWX - 0.12, CWX + 0.12)]
xs = [WX0] + [v for g in gaps for v in g] + [WX1]
for k in range(0, len(xs), 2):
    box(f"MachineSlab{k}", xs[k], xs[k + 1], WY0, WY1, Z_SLAB - 0.4, Z_SLAB, M_CONC)
    box(f"MachineSlabCut{k}", xs[k], xs[k + 1], WY0 - 0.01, WY0, Z_SLAB - 0.4, Z_SLAB, M_CUT)
# landings: door + sill on the back wall every floor (speed reference while the car moves)
for k in range(8):
    z = k * FLOOR_H
    box(f"LandingDoor{k}", -0.55, 0.55, WY1 - 0.04, WY1, z, z + 2.1, M_LDOOR)
    box(f"LandingSill{k}", -0.7, 0.7, WY1 - 0.12, WY1, z - 0.05, z, M_SILL)
    for x0, x1 in ((WX0 - WT, WX0), (WX1, WX1 + WT)): box(f"FloorBand{k}_{x0:.1f}", x0, x1, WY0 - 0.012, WY0 - 0.01, z - 0.25, z, M_CONC)
# guide rails (car) with brackets to the back wall, counterweight rails
for s in (-1, 1):
    bm = bmesh.new()
    add_box(bm, s * (RX - 0.07), s * (RX + 0.07), -0.025, 0.025, ZP + 0.1, Z_SLAB - 0.4)           # blade
    add_box(bm, s * (RX + 0.07), s * (RX + 0.13), -0.14, 0.14, ZP + 0.1, Z_SLAB - 0.4)              # flange
    o = mesh_obj(f"GuideRail{'LR'[s > 0]}", bm, M_RAIL)
    for k in range(10):
        z = ZP + 1.0 + k * 2.8
        box(f"RailBracket{'LR'[s > 0]}{k}", s * (RX + 0.07), s * (RX + 0.15), 0.14, WY1, z, z + 0.12, M_BRKT)
for x in (CWX - 0.45, CWX + 0.45):
    box(f"CwRail{x:.2f}", x - 0.03, x + 0.03, -0.06, 0.06, ZP + 0.1, Z_SLAB - 0.4, M_RAIL)
    for k in range(10):
        z = ZP + 1.4 + k * 2.8; box(f"CwRailBracket{x:.2f}_{k}", x - 0.04, x + 0.04, 0.06, WY1, z, z + 0.1, M_BRKT)
# front wall (hook only): drops on "open"
FRONT = box("FrontWall", WX0 - WT, WX1 + WT, WY0 - 0.32, WY0 - 0.02, ZP - 0.3, Z_SLAB + 4.6, M_FRONT)
for k in range(8):
    z = k * FLOOR_H; box(f"FrontDoor{k}", -0.55, 0.55, WY0 - 0.36, WY0 - 0.32, z, z + 2.1, M_LDOOR, FRONT)
    box(f"FrontFrame{k}", -0.65, 0.65, WY0 - 0.35, WY0 - 0.33, z - 0.02, z + 2.2, M_SILL, FRONT)
T_OPEN = C["open"]
key(FRONT, "location", F(T_OPEN - 0.05), (0, 0, 0)); key(FRONT, "location", F(T_OPEN + 0.8), (0.0, -2.0, -45.0))
vis(FRONT, 1, False); vis(FRONT, F(T_OPEN + 0.85), True)

# ---------- car (origin = car floor centre) ----------
CAR = empty("Car")
box("CabFloor", -0.9, 0.9, -0.7, 0.7, -0.08, 0.0, M_CFLOOR, CAR)
box("CabRoof", -0.9, 0.9, -0.7, 0.7, 2.3, 2.4, M_CAB, CAR)
box("CabBack", -0.9, 0.9, 0.62, 0.7, 0.0, 2.3, M_CABIN, CAR)
box("CabSideL", -0.9, -0.82, -0.7, 0.7, 0.0, 2.3, M_CABIN, CAR)
box("CabSideR", 0.82, 0.9, -0.7, 0.7, 0.0, 2.3, M_CABIN, CAR)
box("CabEdgeL", -0.9, -0.82, -0.72, -0.7, 0.0, 2.3, M_CAB, CAR); box("CabEdgeR", 0.82, 0.9, -0.72, -0.7, 0.0, 2.3, M_CAB, CAR)
box("CabEdgeTop", -0.9, 0.9, -0.72, -0.7, 2.2, 2.4, M_CAB, CAR)
box("CabLight", -0.5, 0.5, -0.3, 0.3, 2.27, 2.3, M_CLIGHT, CAR)
curve_obj("Handrail", [(-0.7, 0.55, 0.95), (0.7, 0.55, 0.95)], 0.018, M_CAB, parent=CAR)
for s in (-1, 1):
    box(f"Stile{s}", s * 0.94 - 0.04, s * 0.94 + 0.04, -0.06, 0.06, -0.25, 2.75, M_FRAME, CAR)
    for z0, z1 in ((2.58, 2.78), (-0.22, -0.02)):                                    # guide shoes hugging the rail blade
        for y0, y1 in ((-0.08, -0.035), (0.035, 0.08)):
            box(f"GuideShoe{s}{z0}{y0}", s * (RX - 0.09), s * (RX + 0.04), y0, y1, z0, z1, M_HOUS, CAR)
        box(f"GuideShoeBack{s}{z0}", s * 0.98, s * (RX - 0.09), -0.08, 0.08, z0, z1, M_HOUS, CAR)
box("Crosshead", -1.02, 1.02, -0.25, 0.25, 2.6, 2.8, M_FRAME, CAR)
box("HitchPlate", -0.2, 0.2, -0.28, 0.28, 2.8, 2.86, M_BRKT, CAR)
box("SafetyPlank", -1.02, 1.02, -0.15, 0.15, -0.25, -0.08, M_FRAME, CAR)
LINK = curve_obj("SafetyLinkage", [(-1.0, -0.2, -0.3), (1.0, -0.2, -0.3)], 0.018, M_LEVER, parent=CAR)
# safety gear: housing + a steel wedge on each side of each rail blade (front ones face the camera)
WEDGES = []
for s in (-1, 1):
    box(f"SafetyHousing{s}", s * (RX - 0.12), s * (RX + 0.05), -0.24, -0.13, -0.62, -0.25, M_HOUS, CAR)
    box(f"SafetyHousingB{s}", s * (RX - 0.12), s * (RX + 0.05), 0.13, 0.24, -0.62, -0.25, M_HOUS, CAR)
    box(f"SafetyHousingTop{s}", s * 0.98, s * (RX + 0.05), -0.24, 0.24, -0.29, -0.25, M_HOUS, CAR)
    for side in (-1, 1):
        W = empty(f"WedgeRest{s}{side}", (0, 0, 0), CAR)
        bm = bmesh.new()
        # tapered wedge in (y, z): thick at the bottom, its flat face toward the blade
        yb = side * 0.06
        add_prism_x(bm, [(yb, -0.56), (yb + side * 0.075, -0.56), (yb + side * 0.035, -0.34), (yb, -0.34)], s * (RX - 0.07), s * (RX + 0.05))
        mesh_obj(f"Wedge{s}{side}", bm, M_WEDGE, W); WEDGES.append((W, side))
# lever on the car's left, pulled by the governor rope
LEV_P = Vector((-1.02, GY - 0.03, -0.15)); LEV_L = 0.41
box("LeverBracket", -1.06, -0.98, GY - 0.01, -0.06, -0.21, -0.09, M_FRAME, CAR)
LEVER = empty("LeverPivot", LEV_P, CAR)
box("Lever", -LEV_L - 0.03, 0.02, -0.025, 0.025, -0.025, 0.025, M_LEVER, LEVER)
cyl("LeverEye", 0.035, 0.06, "Y", (-LEV_L, 0, 0), M_LEVER, LEVER, 16)
curve_obj("PullRod", [(-1.10, GY - 0.03, -0.17), (-1.12, -0.2, -0.3)], 0.012, M_LEVER, parent=CAR)
bake(CAR, "location", 2, CAR_Z)
T_YANK = C["yanks"]
lev_a = PW([(0, 0), (T_YANK - 0.05, 0), (T_YANK + 0.45, math.radians(32)), (T_PIT - 0.01, math.radians(32)), (T_PIT, 0)])
LEV_A = [lev_a(t) for t in TS]
bake(LEVER, "rotation_euler", 1, [-a for a in LEV_A])    # -Y rotation lifts the -x end
# wedges: rise + close onto the blade between "jams" and contact, released for the pit and the CTA
w_rise = PW([(0, 0), (C["jams"] - 0.05, 0), (T_WEDGE, 1.0), (T_PIT - 0.01, 1.0), (T_PIT, 0)])
W_U = [w_rise(t) for t in TS]
for W, side in WEDGES:
    bake(W, "location", 2, [0.07 * u for u in W_U])
    bake(W, "location", 1, [-side * 0.032 * u for u in W_U])
glow(B_WEDGE, [(0, 0), (T_WEDGE - 0.1, 0), (T_WEDGE + 0.1, 6.0), (C["own"], 3.0), (C["tighter"], 8.0), (T_STOP, 4.0), (T_PIT - 0.02, 2.0), (T_PIT, 0)])
glow(B_LEVER, [(0, 0), (T_YANK - 0.1, 0), (T_YANK + 0.1, 5.0), (C["jams"], 3.0), (T_WEDGE + 0.6, 0.6), (T_PIT, 0)])
glow(B_RAIL, [(0, 0), (C["guide"] - 0.05, 0), (C["guide"] + 0.15, 1.2), (C["both"] + 0.6, 0.3), (T_PIT, 0)])

# ---------- counterweight ----------
CW = empty("Counterweight")
box("CwFrameL", CWX - 0.4, CWX - 0.34, -0.3, 0.3, 0.0, CWH, M_CWF, CW); box("CwFrameR", CWX + 0.34, CWX + 0.4, -0.3, 0.3, 0.0, CWH, M_CWF, CW)
box("CwTop", CWX - 0.4, CWX + 0.4, -0.3, 0.3, CWH - 0.12, CWH, M_CWF, CW); box("CwBottom", CWX - 0.4, CWX + 0.4, -0.3, 0.3, 0.0, 0.12, M_CWF, CW)
for k in range(9):
    z = 0.14 + k * 0.235; box(f"CwPlate{k}", CWX - 0.34, CWX + 0.34, -0.26, 0.26, z, z + 0.22, M_CW, CW)
box("CwHitch", CWX - 0.2, CWX + 0.2, -0.28, 0.28, CWH, CWH + 0.08, M_BRKT, CW)
bake(CW, "location", 2, CW_Z)
glow(B_CW, [(0, 0), (C["counterweight"] - 0.1, 0), (C["counterweight"] + 0.15, 1.6), (C["difference"] + 0.4, 0.4), (C["up"], 0)])

# ---------- hoist ropes: 3 on the car side, 3 on the counterweight side, arcs over the sheave ----------
CAR_ROPES, CW_ROPES, ARCS = [], [], []
for y in ROPE_Y:
    r = rope_obj(f"HoistRopeCar{y}", 0.03, M_ROPE, SX - SR, y); r.location.z = SZ; CAR_ROPES.append(r)
    r = rope_obj(f"HoistRopeCw{y}", 0.03, M_ROPE, SX + SR, y); r.location.z = SZ; CW_ROPES.append(r)
    ARCS.append(curve_obj(f"HoistRopeArc{y}", arc_pts(SX, y, SZ, SR, 0, 180), 0.03, M_ROPE))
for r in CAR_ROPES: bake(r, "scale", 2, [SZ - (z + 2.86) for z in CAR_Z])
for r in CW_ROPES: bake(r, "scale", 2, [max(0.1, SZ - (z + CWH + 0.08)) for z in CW_Z])
for o in CAR_ROPES + CW_ROPES + ARCS: windows(o, [(0, T_SNAP), (T_CTA, DUR + 1)])
glow(B_ROPE, [(0, 0), (C["three"] - 0.1, 0), (C["three"] + 0.15, 3.0), (C["load"] + 0.4, 0.8), (C["heavy"], 0)])
glow(B_STUB, [(0, 0), (C["every"], 0), (C["every"] + 0.3, 3.0), (T_SNAP + 0.3, 6.0), (C["clever"], 1.2), (T_PIT, 0.3)])
# broken ends: stubs on the car's crosshead and loose ends hanging from the sheave
STUBS = []
for k, y in enumerate(ROPE_Y):
    a = math.radians(-12 + 12 * k)
    pts = [(0, y, 2.86), (0.25 * math.sin(a) + 0.04 * k, y, 2.86 + 0.5), (0.4 * math.sin(a) - 0.1, y - 0.05, 2.86 + 0.75 + 0.15 * k)]
    STUBS.append(curve_obj(f"RopeStubCar{k}", pts, 0.022, M_STUB, parent=CAR))
    STUBS.append(curve_obj(f"RopeEndSheave{k}", [(SX - SR, y, SZ)] + [(SX - SR - 0.05 * j * j, y, SZ - 0.45 * j) for j in range(1, 4)], 0.022, M_STUB))
    STUBS.append(curve_obj(f"RopeArcBroken{k}", arc_pts(SX, y, SZ, SR, 0, 180), 0.022, M_STUB))
for o in STUBS: windows(o, [(T_SNAP, T_CTA)])

# ---------- machine: bedplate, traction sheave, motor, drum brake ----------
box("Bedplate", 0.25, 2.05, -0.95, 1.25, Z_SLAB, Z_SLAB + 0.3, M_BED)
box("SheaveStand", SX - 0.12, SX + 0.12, 0.35, 0.55, Z_SLAB + 0.3, SZ, M_BED)
SHEAVE = empty("SheaveSpin", (SX, 0, SZ))
cyl("Sheave", SR - 0.03, 0.6, "Y", (0, 0, 0), M_SHEAVE, SHEAVE, 64)
for y in ROPE_Y:
    for s in (-1, 1): cyl(f"SheaveRib{y}{s}", SR + 0.02, 0.02, "Y", (0, y + s * 0.07, 0), M_SHEAVE, SHEAVE, 64)
for k in range(6):
    a = k * math.pi / 3
    o = box(f"SheaveMark{k}", -0.05, 0.05, -0.32, -0.30, 0.3, 0.95, M_SPOKE, SHEAVE); o.rotation_euler = (0, a, 0)
cyl("Axle", 0.09, 2.2, "Y", (SX, 0.15, SZ), M_DRUM)
cyl("Motor", 0.55, 0.8, "Y", (SX, 0.85, SZ), M_MOTOR); cyl("MotorCap", 0.45, 0.1, "Y", (SX, 1.3, SZ), M_BED)
box("MotorFoot", SX - 0.45, SX + 0.45, 0.45, 1.25, Z_SLAB + 0.3, SZ - 0.4, M_MOTOR)
DRUM = empty("DrumSpin", (SX, 0, SZ))
cyl("BrakeDrum", 0.45, 0.28, "Y", (0, -0.6, 0), M_DRUM, DRUM, 64)
for k in range(4):
    o = box(f"DrumMark{k}", -0.03, 0.03, -0.75, -0.74, 0.12, 0.38, M_SPOKE, DRUM); o.rotation_euler = (0, k * math.pi / 2, 0)
ARMS = []
Z_PIV = SZ - 0.8
for s in (-1, 1):
    A_ = empty(f"BrakeArmPivot{s}", (SX + s * 0.54, -0.6, Z_PIV))
    box(f"BrakeArm{s}", -0.04, 0.04, -0.09, 0.09, 0.0, 1.95, M_ARM, A_)
    box(f"BrakePad{s}", -s * 0.09, -s * 0.04, -0.13, 0.13, 0.45, 1.15, M_PAD, A_)       # inner face on the drum (r 0.45)
    cyl(f"BrakePivotPin{s}", 0.05, 0.24, "Y", (0, 0, 0), M_DRUM, A_, 16)
    box(f"BrakeArmFoot{s}", -0.1, 0.1, -0.12, 0.12, -0.2, -0.04, M_BED, A_)
    ARMS.append((A_, s))
SPR_Z = Z_PIV + 1.55
SPRING = empty("BrakeSpringPivot", (SX, -0.6, SPR_Z))
curve_obj("BrakeSpringCoil", helix_pts((-0.5, 0, 0), (0.5, 0, 0), 0.07, 9, "X", 14), 0.014, M_SPRING, parent=SPRING)
curve_obj("BrakeSpringRod", [(-0.5, 0, 0), (0.5, 0, 0)], 0.012, M_DRUM, parent=SPRING)
MAG = box("Electromagnet", SX - 0.24, SX + 0.24, -0.72, -0.48, Z_PIV + 1.72, Z_PIV + 1.95, M_MAG)
cyl("MagCoil", 0.08, 0.3, "Y", (SX, -0.74, Z_PIV + 1.835), M_COPPER, None, 24)
curve_obj("MagCable", [(SX, -0.6, Z_PIV + 1.95), (SX + 0.2, -0.6, Z_PIV + 2.3), (SX + 1.1, -0.2, Z_PIV + 2.5), (SX + 1.6, 0.9, Z_PIV + 2.4)], 0.02, M_BED)
def brake_open(t):
    u = 0.0
    for t0, t1 in BR_OPEN:
        if t0 <= t <= t1 + 0.12: u = max(u, ease((t - t0) / 0.25) * (1 - ease((t - t1) / 0.1)))
    return u
BRK = [brake_open(t) for t in TS]
A_OPEN = math.radians(4.0)
for A_, s in ARMS: bake(A_, "rotation_euler", 1, [s * A_OPEN * u for u in BRK])
bake(SPRING, "scale", 0, [1.0 + 2 * 1.55 * math.sin(A_OPEN) * u for u in BRK])
mag_keys = [(0, 0)]
for t0, t1 in BR_OPEN: mag_keys += [(t0 - 0.05, 0), (t0 + 0.05, 5.0), (t1, 5.0), (t1 + 0.06, 0)]
glow(B_MAG, mag_keys)
glow(B_SPRING, [(0, 0), (C["springs"] - 0.1, 0), (C["springs"] + 0.15, 3.0), (C["shut"] + 0.5, 1.0), (C["electricity"], 0),
                (C["clamps"] - 0.05, 0), (C["clamps"] + 0.1, 3.0), (C["but"] - 0.1, 0.5), (C["but"], 0)])
glow(B_PAD, [(0, 0), (C["out"] + 0.05, 0), (C["out"] + 0.15, 4.0), (C["itself"] + 0.4, 1.0), (C["but"], 0)])
glow(B_MOTOR, [(0, 0), (C["motor"] - 0.1, 0), (C["motor"] + 0.1, 1.2), (C["difference"] + 0.4, 0)])
# sheave + drum turn with the rope (car speed / radius) until the ropes break
ang, SHEAVE_A = 0.0, []
for i, t in enumerate(TS):
    if t < T_SNAP: ang += V_CAR[i] / SR / FPS
    SHEAVE_A.append(ang)
bake(SHEAVE, "rotation_euler", 1, SHEAVE_A); bake(DRUM, "rotation_euler", 1, SHEAVE_A)

# ---------- overspeed governor: sheave with flyweights + pawl, its own rope loop to a tension pulley in the pit ----------
box("GovernorStand", GX - 0.35, GX + 0.35, GY + 0.06, GY + 0.16, Z_SLAB, GZ + 0.1, M_BED)
GOV = empty("GovernorSpin", (GX, GY, GZ))
cyl("GovernorSheave", RG - 0.01, 0.08, "Y", (0, 0, 0), M_GOV, GOV, 48)
cyl("GovernorHub", 0.05, 0.12, "Y", (0, 0, 0), M_DRUM, GOV, 16)
for k in range(4):
    o = box(f"GovernorSpoke{k}", -0.015, 0.015, -0.05, -0.045, 0.05, RG - 0.04, M_DRUM, GOV); o.rotation_euler = (0, k * math.pi / 2 + math.pi / 4, 0)
for k in range(12):                                       # ratchet teeth on the rim face
    o = empty(f"GovToothRot{k}", (0, 0, 0), GOV); o.rotation_euler = (0, k * math.pi / 6, 0)
    bm = bmesh.new(); add_prism_x(bm, [(-0.065, RG - 0.06), (-0.04, RG - 0.06), (-0.04, RG - 0.01)], -0.02, 0.02); mesh_obj(f"GovTooth{k}", bm, M_DRUM, o)
FLY = []
for s in (-1, 1):
    o = empty(f"FlyweightSlide{s}", (s * 0.12, -0.06, 0.0), GOV)
    box(f"Flyweight{s}", -0.055, 0.055, -0.025, 0.025, -0.035, 0.035, M_FLY, o); FLY.append((o, s))
PAWL = empty("PawlPivot", (GX + 0.26, GY - 0.07, GZ + 0.36))
box("Pawl", -0.2, 0.0, -0.015, 0.015, -0.02, 0.02, M_LEVER, PAWL)
cyl("PawlPin", 0.025, 0.06, "Y", (GX + 0.26, GY - 0.05, GZ + 0.36), M_DRUM)
# governor angle follows the rope = the car (shown 2x so the spin reads), frozen once it locks
ga, GOV_A = 0.0, []
for i, t in enumerate(TS):
    if t < T_LOCK and t < T_PIT: ga += 2.0 * V_CAR[i] / RG / FPS
    GOV_A.append(ga)
bake(GOV, "rotation_euler", 1, GOV_A)
fly_out = PW([(0, 0), (C["fly"] - 0.05, 0), (C["outward"] + 0.2, 0.075), (T_PIT - 0.01, 0.075), (T_PIT, 0)])
for o, s in FLY: bake(o, "location", 0, [s * (0.12 + fly_out(t)) for t in TS])
pawl_a = PW([(0, math.radians(-25)), (C["catch"] - 0.05, math.radians(-25)), (C["catch"] + 0.15, math.radians(18)),
             (T_PIT - 0.01, math.radians(18)), (T_PIT, math.radians(-25))])
bake(PAWL, "rotation_euler", 1, [pawl_a(t) for t in TS])
glow(B_FLY, [(0, 0), (C["spin"] - 0.1, 0), (C["fast"], 2.0), (C["fly"], 5.0), (C["lock"] + 0.6, 2.0), (C["thin"] + 0.6, 0.4)])
glow(B_GOV, [(0, 0), (C["lock"] - 0.05, 0), (C["lock"] + 0.1, 2.5), (C["thin"] + 0.8, 0.3), (T_PIT, 0)])
# tension pulley in the pit
GTP = empty("GovPulleySpin", (GX, GY, GPZ))
cyl("GovTensionPulley", RG - 0.01, 0.08, "Y", (0, 0, 0), M_GOV, GTP, 48)
box("GovPulleyWeight", -0.12, 0.12, -0.05, 0.05, -0.55, -0.25, M_BED, GTP)
bake(GTP, "rotation_euler", 1, GOV_A)
box("GovPulleyPost", GX - 0.04, GX + 0.04, GY + 0.05, GY + 0.12, ZP, GPZ, M_BED)
# governor rope: arcs + far side static; car side split at the lever eye (moves with the car)
curve_obj("GovRopeTop", arc_pts(GX, GY, GZ, RG, 0, 180, 30), 0.012, M_GROPE)
curve_obj("GovRopeBottom", arc_pts(GX, GY, GPZ, RG, 180, 360, 30), 0.012, M_GROPE)
curve_obj("GovRopeFar", [(GX - RG, GY, GZ), (GX - RG, GY, GPZ)], 0.012, M_GROPE)
G_UP = rope_obj("GovRopeCarUp", 0.012, M_GROPE, GX + RG, GY); G_UP.location.z = GZ
G_DN = rope_obj("GovRopeCarDown", 0.012, M_GROPE, GX + RG, GY)
EYE_Z = [z + LEV_P.z + LEV_L * math.sin(a) for z, a in zip(CAR_Z, LEV_A)]
bake(G_UP, "scale", 2, [max(0.05, GZ - ez) for ez in EYE_Z])
bake(G_DN, "location", 2, EYE_Z); bake(G_DN, "scale", 2, [max(0.05, ez - GPZ) for ez in EYE_Z])
glow(B_GROPE, [(0, 0), (C["second"] - 0.1, 0), (C["thinner"], 3.0), (C["governor"] + 0.4, 1.0), (C["thin"] - 0.1, 1.0),
               (C["thin"] + 0.1, 3.0), (C["yanks"] + 0.6, 1.0), (T_PIT, 0)])

# ---------- pit buffers: spring (under the car), oil (under the counterweight) ----------
box("BufferBaseCar", -0.3, 0.3, -0.3, 0.3, ZP, ZP + 0.08, M_BED)
BSPR = empty("BufferSpringScale", (0, 0, ZP + 0.08))
curve_obj("BufferSpringCoil", helix_pts((0, 0, 0), (0, 0, 0.75), 0.2, 6, "Z", 20), 0.035, M_BSPRING, parent=BSPR)
box("BufferSpringCap", -0.24, 0.24, -0.24, 0.24, 0.75, 0.82, M_BED, BSPR)
spr_s = [1.0 if t < T_LAND or t >= T_B0 else 1.0 - 0.33 * ease((t - T_LAND) / 0.5) for t in TS]
bake(BSPR, "scale", 2, spr_s)
glow(B_BSPRING, [(0, 0), (C["springs2"] - 0.1, 0), (C["springs2"] + 0.1, 2.5), (C["oil"], 0.6), (T_LAND, 0.6), (T_LAND + 0.1, 4.0), (T_LAND + 0.8, 1.0)])
cyl("OilCylinder", 0.17, 0.8, "Z", (CWX, 0, ZP + 0.4), M_OIL)
PIST = empty("OilPiston", (CWX, 0, 0))
cyl("PistonRod", 0.07, 0.8, "Z", (0, 0, -0.4), M_PISTON, PIST, 20); cyl("PistonCap", 0.15, 0.06, "Z", (0, 0, -0.03), M_BED, PIST, 24)
bake(PIST, "location", 2, [min(ZP + 1.4, cz) for cz in CW_Z])
glow(B_OIL, [(0, 0), (C["oil"] - 0.1, 0), (C["oil"] + 0.1, 2.0), (C["catch2"], 0.5), (T_B0, 0)])

# ---------- sparks while the wedges grind on the rails ----------
SPARKS = []
me_sp = bpy.data.meshes.new("SparkMesh"); bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.014); bm.to_mesh(me_sp); bm.free()
me_sp.materials.append(M_SPARK)
N_SP, LIFE = 48, 0.42
rng = random.Random(7)
for k in range(N_SP):
    o = bpy.data.objects.new(f"Spark{k}", me_sp); CL.objects.link(o)
    side = -1 if k % 2 else 1
    vel = Vector((side * rng.uniform(0.1, 0.9), rng.uniform(-1.4, -0.3), rng.uniform(-0.2, 1.6)))
    SPARKS.append((o, side, vel, rng.uniform(0, LIFE)))
for o, side, vel, ph in SPARKS:
    locs, scl = [], []
    for i, t in enumerate(TS):
        on = T_WEDGE <= t < T_STOP + 0.3
        tb = t - ((t - T_WEDGE - ph) % LIFE) if on else t
        age = t - tb
        zc = car_z(tb) - 0.5
        p = Vector((side * (RX - 0.01), -0.06, zc)) + vel * age + Vector((0, 0, -4.9 * age * age))
        locs.append(p); scl.append(1.0 if on and tb >= T_WEDGE and age < LIFE * 0.95 else 0.0)
    bake_vec(o, "location", locs)
    for ax in range(3): bake(o, "scale", ax, scl)

# ---------- Set B: 1854-style hoisting platform (x = 2000) ----------
box("B_Floor", OX - 18, OX + 18, -16, 7, -0.25, 0.0, M_DARKW)
box("B_BackWall", OX - 18, OX + 18, 4.0, 4.3, 0.0, 26.0, M_DARKW)
PH = 9.6
for s in (-1, 1):
    box(f"B_Post{s}", OX + s * 1.05, OX + s * 1.27, -0.13, 0.13, 0.0, PH, M_WOOD)
    bm = bmesh.new()
    for k in range(30):                                   # saw teeth on the inner face: flat top, sloped below
        z = 0.6 + k * 0.29
        a = [bm.verts.new((OX + s * 1.05, y, z)) for y in (-0.1, 0.1)]
        b = [bm.verts.new((OX + s * 0.96, y, z)) for y in (-0.1, 0.1)]
        c = [bm.verts.new((OX + s * 1.05, y, z - 0.22)) for y in (-0.1, 0.1)]
        fs = [bm.faces.new((a[0], a[1], b[1], b[0])), bm.faces.new((b[0], b[1], c[1], c[0])), bm.faces.new((a[0], b[0], c[0])),
              bm.faces.new((a[1], c[1], b[1])), bm.faces.new((a[0], c[0], c[1], a[1]))]
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    mesh_obj(f"B_Ratchet{s}", bm, M_IRON)
box("B_TopBeam", OX - 1.5, OX + 1.5, -0.16, 0.16, PH, PH + 0.3, M_WOOD)
cyl("B_TopPulley", 0.22, 0.12, "Y", (OX, -0.22, PH - 0.05), M_IRON)
PLAT = empty("B_Platform", (OX, 0, 0))
box("B_Deck", -0.94, 0.94, -0.85, 0.85, 0.0, 0.12, M_WOOD, PLAT)
for s in (-1, 1):
    box(f"B_PlatPost{s}", s * 0.86 - 0.05, s * 0.86 + 0.05, -0.06, 0.06, 0.12, 1.62, M_WOOD, PLAT)
    box(f"B_PlatRail{s}", -0.9, 0.9, s * 0.8 - 0.025, s * 0.8 + 0.025, 0.95, 1.0, M_WOOD, PLAT)
box("B_CrossBar", -0.92, 0.92, -0.08, 0.08, 1.5, 1.62, M_WOOD, PLAT)
LEAF = empty("B_WagonSpring", (0, 0, 1.62), PLAT)
for j in range(3):                                        # three stacked leaves, bowed up in the middle
    curve_obj(f"B_Leaf{j}", [(0.92 * (u / 10) * (1 - 0.08 * j), -0.0, 0.32 * (1 - (u / 10) ** 2) - 0.04 * j) for u in range(-10, 11)],
              0.022, M_LEAF, parent=LEAF)
for s in (-1, 1): box(f"B_LeafTip{s}", s * 0.9 - 0.05, s * 0.9 + 0.05, -0.05, 0.05, -0.04, 0.04, M_IRON, LEAF)
B_ROPE = rope_obj("B_Rope", 0.028, M_HEMP, OX, 0.0); B_ROPE.location.z = PH - 0.27
B_STUBR = curve_obj("B_RopeStub", [(0, 0, 1.94), (0.05, 0, 2.3), (0.15, -0.02, 2.55)], 0.028, M_HEMP, parent=PLAT)
T_RISE0, T_RISE1, T_CUTB = C["new"], C["crowd"] + 0.2, C["cut2"] + 0.2
plat_z = [0.3 if t < T_RISE0 else 0.3 + 4.7 * ease((t - T_RISE0) / (T_RISE1 - T_RISE0)) if t < T_CUTB
          else 5.0 - 0.14 * ease((t - T_CUTB) / 0.12) for t in TS]
bake(PLAT, "location", 2, plat_z)
bake(LEAF, "scale", 0, [0.9 if t < T_CUTB else 0.9 + 0.17 * ease((t - T_CUTB) / 0.08) for t in TS])
bake(B_ROPE, "scale", 2, [max(0.3, (PH - 0.27) - (pz + 1.94)) if t < T_CUTB else max(0.3, (PH - 0.27) - (5.0 + 1.94) - 4.0 * lin((t - T_CUTB) / 0.35)) * 1.0
                          for t, pz in zip(TS, plat_z)])
windows(B_STUBR, [(T_CUTB, DUR + 1)])
glow(B_HEMP, [(0, 0), (C["cut2"] - 0.3, 0), (T_CUTB, 4.0), (C["held"] + 0.4, 0.6)])
glow(B_LEAF, [(0, 0), (T_CUTB, 0), (T_CUTB + 0.1, 4.0), (C["held"] + 0.6, 1.0)])
glow(B_IRON, [(0, 0), (T_CUTB, 0), (T_CUTB + 0.1, 2.0), (C["held"] + 0.6, 0.4)])

# ---------- camera ----------
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36.0
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 11; cam_d.dof.focus_object = TGT
cam_d.clip_start = 0.05; cam_d.clip_end = 400
CZ = lambda dz: (lambda t: car_z(t) + dz)           # height that follows the car
PZ = lambda dz: (lambda t: plat_z[max(0, min(FRAMES - 1, int(round(t * FPS))))] + dz)
SHOTS = [  # (time, cam(x, y, z), target(x, y, z), lens[, "cut"]); a z may be a function of t (follows the car / platform)
    (0.0, (-4.0, -15.0, 9.0), (0.4, 0.0, 12.5), 22),
    (C["lets"], (-3.2, -12.5, 10.5), (0.4, 0.0, 13.0), 22),
    (C["car"] - 0.1, (-2.6, -9.5, 15.6), (0.3, 0.0, 14.4), 24),
    (C["three"] - 0.3, (-3.4, -4.2, 16.4), (0.0, 0.0, 15.5), 28),
    (C["counterweight"] - 0.4, (0.6, -13.0, 14.5), (1.0, 0.0, 13.5), 22),
    (C["up"] - 0.1, (-0.8, -6.2, 29.2), (1.15, -0.3, 27.7), 26),
    (C["brake"] - 0.2, (0.3, -3.6, 28.5), (1.15, -0.6, 27.9), 30),
    (C["but"] - 0.05, (-3.2, -7.0, 20.4), (0.0, 0.0, 19.6), 26, "cut"),
    (C["heres"] - 0.05, (-4.5, -11.5, 22.0), (-1.0, 0.0, 21.0), 24, "cut"),
    (C["governor"] - 0.4, (-1.75, -2.6, 26.95), (-1.75, -0.35, 26.9), 34),
    (C["thin"] - 0.05, (-3.0, -3.6, CZ(0.5)), (-1.2, 0.0, CZ(-0.05)), 28, "cut"),
    (C["jams"] - 0.15, (-1.95, -1.75, CZ(-0.1)), (-1.15, -0.05, CZ(-0.42)), 34),
    (C["both"] - 0.1, (0.15, -5.2, CZ(0.6)), (0.15, 0.0, CZ(0.2)), 26),
    (C["car4"] - 0.1, (-0.6, -3.6, CZ(0.1)), (-0.4, 0.0, CZ(-0.3)), 26),
    (T_PIT, (0.8, -7.4, 1.8), (0.9, 0.0, 0.2), 24, "cut"),
    (C["oil"] - 0.2, (1.6, -6.4, 1.2), (1.3, 0.0, -0.1), 26),
    (T_B0, (OX - 4.0, -10.5, 4.0), (OX, 0.0, 4.4), 26, "cut"),
    (C["new"], (OX - 3.6, -8.5, PZ(2.4)), (OX, 0.0, PZ(1.2)), 24),
    (C["cut2"] - 0.4, (OX - 2.4, -3.6, PZ(2.3)), (OX - 0.7, 0.0, PZ(1.65)), 28),
    (C["held"] + 0.1, (OX - 3.2, -5.0, PZ(2.5)), (OX - 0.3, 0.0, PZ(1.4)), 26),
    (T_CTA, (-2.0, -9.5, 13.0), (0.4, 0.0, 11.8), 24, "cut"),
    (C["end"], (-2.6, -12.5, 13.5), (0.4, 0.0, 11.8), 24),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t1 = SHOTS[k + 1][0]; tr = 0.7 if (t1 - SHOTS[k][0]) > 1.4 else (t1 - SHOTS[k][0]) * 0.5
        if t > t1 - tr:
            u = ease((t - (t1 - tr)) / tr)
            l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.05 * math.sin(t * 0.7), 0.0, 0.03 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
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
for k, z in enumerate((3.0, 11.0, 19.0)):
    area(f"KeyShaft{k}", (-6.0, -11.0, z + 3.0), 7.0, 1100, (1.0, 0.95, 0.88), target(f"LT_Shaft{k}", (0.3, 0.0, z)))
    area(f"FillShaft{k}", (7.0, -9.0, z - 1.0), 6.0, 500, (0.78, 0.86, 1.0), target(f"LT_ShaftF{k}", (0.3, 0.0, z)))
LT_M = target("LT_Machine", (0.6, 0.0, 27.6))
KEY_M = area("KeyMachine", (-3.5, -7.0, 31.5), 5.0, 900, (1.0, 0.95, 0.88), LT_M)
FILL_M = area("FillMachine", (4.5, -6.0, 26.5), 4.0, 300, (0.78, 0.86, 1.0), LT_M)
T_OUT = C["out"] + 0.05
for L_, p in ((KEY_M, 900), (FILL_M, 300)):            # the power cut: the machine room dims, back on at the hard cut
    for t, v in ((0, p), (T_OUT - 0.02, p), (T_OUT + 0.08, p * 0.3), (C["but"] - 0.1, p * 0.3), (C["but"] - 0.05, p)):
        L_.data.energy = v; L_.data.keyframe_insert("energy", frame=F(t))
area("KeyPit", (-3.5, -6.5, 3.0), 5.0, 700, (1.0, 0.95, 0.88), target("LT_Pit", (0.8, 0.0, -0.8)))
area("RimShaft", (0.3, 0.6, Z_SLAB - 1.0), 3.0, 600, (0.70, 0.82, 1.0), target("LT_Down", (0.3, 0.0, 10.0)))
LT_B = target("LT_B", (OX, 0.0, 4.0))
area("KeyB", (OX - 5.0, -9.0, 8.0), 6.0, 1600, (1.0, 0.82, 0.60), LT_B)
area("FillB", (OX + 5.0, -7.0, 2.0), 5.0, 450, (0.75, 0.85, 1.0), LT_B)
area("RimB", (OX + 1.0, 3.5, 10.0), 4.0, 700, (1.0, 0.85, 0.6), LT_B)
area("CamFill", (0, 0, 0), 2.5, 50, (1.0, 0.96, 0.9), TGT).parent = cam

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
ANCH = {"car": (CAR, Vector((-0.5, -0.7, 1.6))), "ropes": (CAR, Vector((0.0, -0.2, 3.6))),
        "counterweight": (CW, Vector((CWX, -0.3, 1.5))), "motor": (None, Vector((SX + 0.55, 0.9, SZ + 0.3))),
        "brake": (None, Vector((SX - 0.52, -0.72, SZ - 0.2))), "springs": (None, Vector((SX - 0.3, -0.68, SPR_Z))),
        "magnet": (None, Vector((SX + 0.2, -0.72, Z_PIV + 1.84))), "sheave": (None, Vector((SX + 0.9, -0.3, SZ + 0.6))),
        "governor": (None, Vector((GX - 0.2, GY - 0.05, GZ + 0.2))), "flyweight": (None, Vector((GX + 0.17, GY - 0.09, GZ))),
        "gov_rope": (lambda fr: Vector((GX + RG, GY, (GZ + EYE_Z[fr - 1]) / 2))), "gov_rope_low": (lambda fr: Vector((GX + RG, GY, EYE_Z[fr - 1] + 1.2))),
        "lever": (CAR, Vector((-1.3, GY - 0.03, -0.12))), "wedge": (CAR, Vector((-RX - 0.0, -0.1, -0.42))),
        "wedge_r": (CAR, Vector((RX, -0.1, -0.42))), "rail": (CAR, Vector((-RX, -0.03, 0.2))),
        "spring_buffer": (None, Vector((0.0, -0.22, ZP + 0.45))), "oil_buffer": (None, Vector((CWX, -0.18, ZP + 0.45))),
        "b_ratchet": (None, Vector((OX - 0.99, -0.1, 7.6))), "b_spring": (PLAT, Vector((0.45, -0.05, 1.86))),
        "b_platform": (PLAT, Vector((0.3, -0.85, 0.08))), "b_rope": (None, Vector((OX, 0.0, 8.2)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, a in ANCH.items():
        if callable(a): w = a(fr)
        else: ob, local = a; w = local if ob is None else ob.matrix_world @ local
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"open": round(T_OPEN + 0.1, 3), "car_up": [round(C["balances"] - 0.2, 3), round(C["difference"] + 0.5, 3)],
          "brake_open": [round(t0, 3) for t0, _ in BR_OPEN], "brake_close": [round(t1, 3) for _, t1 in BR_OPEN],
          "car_up2": [round(C["pulls"] + 0.15, 3), round(C["out"] + 0.1, 3)], "power_out": round(T_OUT, 3),
          "snap": round(T_SNAP, 3), "cw_land": round(T_SNAP + math.sqrt(2 * (K_CW - z_normal(T_SNAP) + 0.6) / 9.81), 3),
          "gov_fast": [round(T_FAST0, 3), round(T_LOCK, 3)], "fly_out": round(C["fly"], 3), "pawl": round(C["catch"] + 0.1, 3),
          "lock": round(T_LOCK, 3), "yank": round(T_YANK, 3), "wedge": round(T_WEDGE, 3), "grind": [round(T_WEDGE, 3), round(T_STOP, 3)],
          "pit": round(T_PIT, 3), "land": round(T_LAND, 3), "set_b": [round(T_B0, 3), round(T_B1, 3)],
          "rise": [round(T_RISE0, 3), round(T_RISE1, 3)], "cut_b": round(T_CUTB, 3), "cta": round(T_CTA, 3)}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS", events, "DUR", DUR, "FRAMES", FRAMES)
print("CAR_Z at lock / stop", round(Z_LOCK, 2), round(car_z(T_STOP), 2))

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
