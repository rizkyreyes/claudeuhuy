# Fridge-Cold-3D: how a fridge makes cold (it moves heat out). Studio cutaway in Blender Cycles. Every cue is a word in the VO.
# Top-freezer fridge cut in half at y = 0 (camera side, -y). Depth runs along x: doors at x -0.42, back wall at x +0.36, condenser on the back at x 0.40.
# The near half (y < 0) slides away on "cut ... open". The sealed refrigerant loop: compressor (machine compartment, bottom rear) -> discharge line ->
# condenser (back) -> capillary tube (inside the back wall, on the cut face) -> evaporator (freezer, back) -> suction line (back wall) -> compressor.
# Refrigerant "packets" (small glowing beads) circulate along that loop; their colour is baked per frame (red hot gas -> gold liquid -> cyan cold).
# Also: evaporator fan, damper flap in the divider, thermostat, defrost heater, frost on the coils, drain tube, drain pan under the fridge.
# No people, no brands. Sizes are illustrative, none are spoken.
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
DUR = round(WORDS[-1]["end"] + VO + 0.8, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(11)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
C = {}
for name, word in [("how", "how"), ("fridge", "fridge"), ("cold", "cold"), ("heres", "here's"), ("twist", "twist"), ("doesnt", "doesn't"), ("moves", "moves"),
                   ("heat", "heat"), ("out", "out"), ("lets", "let's"), ("cut", "cut"), ("open", "open"), ("hidden", "hidden"), ("walls", "walls"), ("sealed", "sealed"),
                   ("loop", "loop"), ("tubing", "tubing"), ("filled", "filled"), ("refrigerant", "refrigerant"), ("fluid", "fluid"), ("boils", "boils"), ("low", "low"),
                   ("temperatures", "temperatures"), ("bottom", "bottom"), ("sits", "sits"), ("compressor", "compressor"), ("squeezes", "squeezes"), ("gas", "gas"),
                   ("squeezing", "squeezing"), ("hot", "hot"), ("hot2", "hot"), ("flows", "flows"), ("coils", "coils"), ("back", "back"), ("condenser", "condenser"),
                   ("there", "there"), ("dumps", "dumps"), ("heat2", "heat"), ("kitchen", "kitchen"), ("turns", "turns"), ("liquid", "liquid"), ("thats", "that's"),
                   ("back2", "back"), ("warm", "warm"), ("next", "next"), ("liquid2", "liquid"), ("forced", "forced"), ("thin", "thin"), ("tube", "tube"), ("past", "past"),
                   ("pressure", "pressure"), ("drops", "drops"), ("low2", "low"), ("boil", "boil"), ("colder", "colder"), ("so", "so"), ("freezer", "freezer"),
                   ("inside", "inside"), ("evaporator", "evaporator"), ("coils2", "coils"), ("refrigerant2", "refrigerant"), ("boils2", "boils"), ("below", "below"),
                   ("freezing", "freezing"), ("boiling", "boiling"), ("soaks", "soaks"), ("heat3", "heat"), ("pulls", "pulls"), ("warmth", "warmth"), ("air", "air"),
                   ("fan", "fan"), ("blows", "blows"), ("cold2", "cold"), ("around", "around"), ("small", "small"), ("flap", "flap"), ("down", "down"), ("fridge2", "fridge"),
                   ("gas2", "gas"), ("heads", "heads"), ("back3", "back"), ("compressor2", "compressor"), ("loop2", "loop"), ("starts", "starts"), ("again", "again"),
                   ("thermostat", "thermostat"), ("switches", "switches"), ("on", "on"), ("off", "off"), ("one", "one"), ("hidden2", "hidden"), ("trick", "trick"),
                   ("frost", "frost"), ("builds", "builds"), ("cold3", "cold"), ("coils3", "coils"), ("heater", "heater"), ("melts", "melts"), ("now", "now"),
                   ("water", "water"), ("drains", "drains"), ("pan", "pan"), ("under", "under"), ("fridge3", "fridge"), ("where", "where"), ("warmth2", "warmth"),
                   ("dries", "dries"), ("so2", "so"), ("fridge4", "fridge"), ("heat4", "heat"), ("pump", "pump"), ("pushing", "pushing"), ("heat5", "heat"),
                   ("day", "day"), ("did", "did"), ("know", "know"), ("back4", "back"), ("heater2", "heater"), ("tell", "tell"), ("comments", "comments"),
                   ("if", "if"), ("useful", "useful"), ("follow", "follow")]:
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
        if t1 < DUR: vis(obj, F(t1), True)
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
def bake_fn(owner, path, index, fn): return bake(owner, path, index, [fn(t) for t in TS])
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("Fridge")
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
GOLD, CYAN, RED, ORANGE = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12), (1.0, 0.38, 0.08)
M_SKIN, _ = mat("Enamel", (0.80, 0.81, 0.82), 0.25, 0.0)
M_LINER, _ = mat("Liner", (0.70, 0.73, 0.76), 0.35, 0.0)
M_FOAM, _ = mat("Foam", (0.85, 0.70, 0.32), 0.9, 0.0, GOLD, 60)
M_GASKET, _ = mat("Gasket", (0.05, 0.05, 0.05), 0.6)
M_HANDLE, _ = mat("Handle", (0.55, 0.57, 0.60), 0.2, 1.0)
M_GLASS, _ = mat("ShelfGlass", (0.75, 0.88, 0.92), 0.05, 0.0)
M_COPPER, B_COPPER = mat("Copper", (0.78, 0.40, 0.20), 0.3, 1.0, GOLD)
M_COND, B_COND = mat("CondenserBlack", (0.03, 0.03, 0.03), 0.45, 0.6, ORANGE)
M_CAP, B_CAP = mat("Capillary", (0.85, 0.48, 0.24), 0.25, 1.0, GOLD)
M_EVAP, B_EVAP = mat("EvaporatorAlu", (0.62, 0.66, 0.70), 0.3, 1.0, CYAN)
M_SUCT, B_SUCT = mat("SuctionLine", (0.78, 0.40, 0.20), 0.3, 1.0, CYAN)
M_COMP, B_COMP = mat("CompressorShell", (0.07, 0.07, 0.08), 0.35, 0.6, RED)
M_RUBBER, _ = mat("Rubber", (0.02, 0.02, 0.02), 0.8)
M_WIRE, _ = mat("CondWire", (0.07, 0.07, 0.07), 0.5, 0.6)
M_FAN, B_FAN = mat("Fan", (0.12, 0.13, 0.15), 0.5, 0.0, CYAN)
M_FLAP, B_FLAP = mat("Flap", (0.85, 0.86, 0.88), 0.4, 0.0, CYAN)
M_THERMO, B_THERMO = mat("Thermostat", (0.88, 0.89, 0.90), 0.35, 0.0, CYAN)
M_HEATER, B_HEATER = mat("DefrostHeater", (0.25, 0.08, 0.06), 0.4, 0.5, RED)
M_FROST, _ = mat("Frost", (0.92, 0.96, 1.0), 0.75, 0.0, CYAN, 90)
M_WATER, B_WATER = mat("Water", (0.15, 0.45, 0.75), 0.05, 0.0, CYAN); B_WATER.inputs["Emission Strength"].default_value = 0.6
M_PAN, _ = mat("DrainPan", (0.15, 0.15, 0.16), 0.6)
M_STEAM, B_STEAM = mat("Steam", (0.9, 0.92, 0.95), 0.9, 0.0, (1, 1, 1)); B_STEAM.inputs["Emission Strength"].default_value = 1.5
M_AIR, B_AIR = mat("AirArrow", (0.25, 0.9, 1.0), 0.3, 0.0, CYAN); B_AIR.inputs["Emission Strength"].default_value = 5.0
M_HEATA, B_HEATA = mat("HeatArrow", (1.0, 0.38, 0.08), 0.3, 0.0, ORANGE); B_HEATA.inputs["Emission Strength"].default_value = 6.0
M_TRACE, B_TRACE = mat("LoopTrace", (1.0, 0.70, 0.22), 0.4, 0.0, GOLD); B_TRACE.inputs["Emission Strength"].default_value = 7.0
M_GROUND, _ = mat("Floor", (0.06, 0.06, 0.065), 0.55, 0.0, GOLD, 8)
M_WALLBG, _ = mat("BackdropWall", (0.05, 0.06, 0.075), 0.8)
# food (generic, no labels)
M_MILK, _ = mat("Carton", (0.85, 0.85, 0.80), 0.6)
M_JUICE, _ = mat("JuiceBottle", (0.95, 0.55, 0.08), 0.15)
M_APPLE, _ = mat("Apple", (0.70, 0.06, 0.05), 0.35)
M_LEMON, _ = mat("Lemon", (0.95, 0.80, 0.10), 0.5)
M_JAR, _ = mat("Jar", (0.30, 0.55, 0.20), 0.2)
M_LID, _ = mat("Lid", (0.75, 0.15, 0.12), 0.4, 0.6)
M_CHEESE, _ = mat("Cheese", (0.95, 0.75, 0.25), 0.6)
M_LETTUCE, _ = mat("Greens", (0.25, 0.60, 0.15), 0.6)
M_FROZEN, _ = mat("FrozenBox", (0.20, 0.35, 0.70), 0.5)
M_ICE, _ = mat("Ice", (0.80, 0.92, 1.0), 0.1)
M_DRAWER, _ = mat("Drawer", (0.80, 0.90, 0.95), 0.1)
# refrigerant beads: colour from the object's colour (R channel = heat 0..1) through a ramp cyan -> gold -> red
M_BEAD = bpy.data.materials.new("RefrigerantBead")
try: M_BEAD.use_nodes = True
except Exception: pass
_nt = M_BEAD.node_tree; _b = next(n for n in _nt.nodes if n.type == "BSDF_PRINCIPLED")
_oi = _nt.nodes.new("ShaderNodeObjectInfo"); _sep = _nt.nodes.new("ShaderNodeSeparateColor"); _rp = _nt.nodes.new("ShaderNodeValToRGB")
_nt.links.new(_oi.outputs["Color"], _sep.inputs[0]); _nt.links.new(_sep.outputs[0], _rp.inputs[0])
_e = _rp.color_ramp.elements; _e[0].color = (*CYAN, 1); _e[1].color = (1.0, 0.22, 0.06, 1); _e.new(0.5).color = (*GOLD, 1)
_nt.links.new(_rp.outputs[0], _b.inputs["Base Color"]); _nt.links.new(_rp.outputs[0], _b.inputs["Emission Color"])
_b.inputs["Emission Strength"].default_value = 6.0; _b.inputs["Roughness"].default_value = 0.3

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
def add_cyl(bm, r, depth, axis, center, seg=24, mi=0, r2=None):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth); vs = res["verts"]
    if axis == "X": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    if axis == "Y": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, verts=vs, vec=center)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def cyl(name, r, depth, axis, center, m_, parent=None, seg=24):
    bm = bmesh.new(); add_cyl(bm, r, depth, axis, center, seg); return mesh_obj(name, bm, m_, parent)
def add_sphere(bm, r, center, mi=0, seg=16):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r); vs = res["verts"]
    bmesh.ops.translate(bm, verts=vs, vec=center)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def sphere(name, r, center, m_, parent=None, seg=16):
    bm = bmesh.new(); add_sphere(bm, r, center, 0, seg); o = mesh_obj(name, bm, m_, parent)
    for p in o.data.polygons: p.use_smooth = True
    return o
def add_bar(bm, p0, p1, w, mi=0):
    """Square bar between two points."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
    M = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Diagonal((w, w, L, 1))
    bmesh.ops.transform(bm, matrix=M, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
def empty(name, loc=(0, 0, 0), parent=None):
    o = bpy.data.objects.new(name, None); CL.objects.link(o); o.location = loc
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o
def tube(name, pts, r, m_, parent=None):
    """Poly curve with a round bevel through the points (world coords)."""
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p_, q in zip(sp.points, pts): p_.co = (*q, 1)
    try: cu.bevel_factor_mapping_end = "SPLINE"
    except Exception: pass
    o = bpy.data.objects.new(name, cu); CL.objects.link(o); cu.materials.append(m_)
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o

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
class Path:
    """Polyline with arc-length lookup: at(s) -> (position, unit direction)."""
    def __init__(self, pts):
        self.p = [Vector(q) for q in pts]; self.cum = [0.0]
        for a, b in zip(self.p, self.p[1:]): self.cum.append(self.cum[-1] + (b - a).length)
        self.L = self.cum[-1]
    def at(self, s):
        s = max(0.0, min(self.L, s))
        for i in range(len(self.p) - 1):
            if s <= self.cum[i + 1] + 1e-9:
                seg = self.cum[i + 1] - self.cum[i]; u = (s - self.cum[i]) / seg if seg > 0 else 0.0
                d = (self.p[i + 1] - self.p[i]); return self.p[i] + d * u, (d.normalized() if d.length > 0 else Vector((1, 0, 0)))
        return self.p[-1], (self.p[-1] - self.p[-2]).normalized()

# ---------- layout (metres) ----------
X0, X1 = -0.36, 0.36          # cabinet depth (front .. back)
YS = 0.40                     # half width (cabinet y -0.40 .. 0.40), cut plane y = 0
ZB, ZT = 0.06, 1.82           # cabinet bottom / top
ZM0, ZM1 = 1.22, 1.29         # divider (mullion) between fridge (below) and freezer (above)
NX, NZ = 0.10, 0.36           # machine-compartment notch: x > NX, z < NZ (bottom rear)
T_CUT0, T_CUT1 = C["cut"] - 0.05, C["open"] + 0.55

# ---------- studio ----------
box("Floor", -8, 8, -8, 8, -0.2, 0.0, M_GROUND)
box("Backdrop", -8, 8, 3.5, 3.7, 0.0, 8.0, M_WALLBG)

# ---------- cabinet: far half (stays) with foam cut faces, near half (slides away) ----------
WALLS = [  # (name, x0, x1, z0, z1, y_far_side?) wall slabs; each exists in both halves (y 0..YS and -YS..0)
    ("Bottom", X0, NX, ZB, 0.11), ("NotchWall", NX, NX + 0.05, ZB, NZ), ("NotchCeil", NX, X1, NZ - 0.05, NZ), ("Back", 0.31, X1, NZ - 0.05, ZT),
    ("Top", X0, X1, 1.77, ZT), ("FrontFrameLow", X0, X0 + 0.05, ZB, 0.11), ("FrontFrameMid", X0, X0 + 0.05, ZM0, ZM1),
]
FOAM_T = 0.006
NEAR = empty("NearHalf")
for nm, x0, x1, z0, z1 in WALLS:
    box(f"{nm}Far", x0, x1, 0.0, 0.35, z0, z1, M_SKIN)
    if (x1 - x0) > 2 * FOAM_T and (z1 - z0) > 2 * FOAM_T:
        box(f"{nm}Foam", x0 + FOAM_T, x1 - FOAM_T, -0.0015, 0.0005, z0 + FOAM_T, z1 - FOAM_T, M_FOAM)
    box(f"{nm}Near", x0, x1, -0.35, 0.0, z0, z1, M_SKIN, NEAR)
# divider (mullion) with the damper opening at x 0.12..0.26, y 0.10..0.28 (far half only)
for nm, (x0, x1, y0, y1) in (("A", (-0.31, 0.12, 0.0, 0.35)), ("B", (0.26, 0.31, 0.0, 0.35)), ("C", (0.12, 0.26, 0.0, 0.10)), ("D", (0.12, 0.26, 0.28, 0.35))):
    box(f"Mullion{nm}", x0, x1, y0, y1, ZM0, ZM1, M_SKIN)
box("MullionFoam", -0.31 + FOAM_T, 0.31 - FOAM_T, -0.0015, 0.0005, ZM0 + FOAM_T, ZM1 - FOAM_T, M_FOAM)
box("MullionNear", -0.31, 0.31, -0.35, 0.0, ZM0, ZM1, M_SKIN, NEAR)
# side walls
box("SideFar", X0, X1, 0.35, YS, ZB, ZT, M_SKIN)
box("SideNear", X0, X1, -YS, -0.35, ZB, ZT, M_SKIN, NEAR)
box("LinerSide", -0.31, 0.31, 0.345, 0.35, 0.11, 1.77, M_LINER)
# doors (front, x -0.42 .. -0.36), split at the cut
for half, (y0, y1), par in (("Far", (0.0, YS), None), ("Near", (-YS, 0.0), NEAR)):
    box(f"FridgeDoor{half}", -0.42, X0, y0, y1, ZB + 0.01, 1.255, M_SKIN, par)
    box(f"FreezerDoor{half}", -0.42, X0, y0, y1, 1.275, ZT, M_SKIN, par)
    box(f"GasketLo{half}", X0 - 0.006, X0 - 0.0005, y0 * 0.97, y1 * 0.97, ZB + 0.02, 1.245, M_GASKET, par)
    box(f"GasketHi{half}", X0 - 0.006, X0 - 0.0005, y0 * 0.97, y1 * 0.97, 1.285, ZT - 0.01, M_GASKET, par)
for nm, (y0, y1), par in (("Far", (0.0, YS), None),):
    box("DoorFoamLo", -0.42 + FOAM_T, X0 - FOAM_T, -0.0015, 0.0005, ZB + 0.01 + FOAM_T, 1.255 - FOAM_T, M_FOAM)
    box("DoorFoamHi", -0.42 + FOAM_T, X0 - FOAM_T, -0.0015, 0.0005, 1.275 + FOAM_T, ZT - FOAM_T, M_FOAM)
for nm, z0, z1 in (("Lo", 0.80, 1.12), ("Hi", 1.36, 1.62)):
    bm = bmesh.new(); add_box(bm, -0.46, -0.44, -0.33, -0.31, z0, z1); add_bar(bm, (-0.42, -0.32, z0 + 0.02), (-0.45, -0.32, z0 + 0.02), 0.02)
    add_bar(bm, (-0.42, -0.32, z1 - 0.02), (-0.45, -0.32, z1 - 0.02), 0.02); mesh_obj(f"Handle{nm}", bm, M_HANDLE, NEAR)
# interior liner on the back wall, floor and ceilings (far half)
box("LinerBack", 0.305, 0.31, 0.0, 0.345, NZ, 1.77, M_LINER)
box("LinerFloor", X0 + 0.05, NX, 0.0, 0.345, 0.11, 0.115, M_LINER)
# shelves, drawer and food (far half, y 0.02 .. 0.33)
for z in (0.50, 0.86):
    box(f"Shelf{z}", -0.30, 0.30, 0.01, 0.345, z, z + 0.008, M_GLASS)
box("DrawerFront", -0.30, -0.29, 0.02, 0.33, 0.12, 0.33, M_DRAWER)
box("DrawerBack", 0.08, 0.09, 0.02, 0.33, 0.12, 0.33, M_DRAWER)
box("DrawerLid", -0.30, 0.09, 0.02, 0.33, 0.34, 0.348, M_GLASS)
for k, (x, y) in enumerate(((-0.20, 0.10), (-0.08, 0.22), (0.02, 0.12))):
    sphere(f"Greens{k}", 0.07, (x, y, 0.20), M_LETTUCE)
box("Carton", -0.24, -0.15, 0.06, 0.15, 0.508, 0.76, M_MILK)
bm = bmesh.new(); add_cyl(bm, 0.035, 0.24, "Z", (-0.05, 0.12, 0.63), 20); add_cyl(bm, 0.015, 0.06, "Z", (-0.05, 0.12, 0.78), 12); mesh_obj("Bottle", bm, M_JUICE)
for k, (x, y) in enumerate(((0.10, 0.08), (0.17, 0.20), (0.08, 0.26))):
    sphere(f"Apple{k}", 0.04, (x, y, 0.548), M_APPLE)
sphere("Lemon", 0.035, (0.22, 0.10, 0.544), M_LEMON)
for k, (x, y) in enumerate(((-0.20, 0.12), (-0.05, 0.25))):
    cyl(f"Jar{k}", 0.045, 0.12, "Z", (x, y, 0.928), M_JAR); cyl(f"JarLid{k}", 0.047, 0.02, "Z", (x, y, 0.998), M_LID)
box("Cheese", 0.05, 0.17, 0.06, 0.16, 0.868, 0.93, M_CHEESE)
box("FrozenBoxA", -0.27, -0.06, 0.05, 0.30, 1.295, 1.38, M_FROZEN)
box("FrozenBoxB", -0.25, -0.08, 0.08, 0.27, 1.38, 1.44, (mat("FrozenBox2", (0.75, 0.25, 0.20), 0.5)[0]))
bm = bmesh.new(); add_box(bm, -0.26, 0.02, 0.05, 0.20, 1.60, 1.62)
for i in range(4):
    for j in range(2): add_box(bm, -0.24 + i * 0.065, -0.20 + i * 0.065, 0.07 + j * 0.065, 0.11 + j * 0.065, 1.62, 1.66)
mesh_obj("IceTray", bm, M_ICE)

# ---------- the sealed loop ----------
COMP_C = Vector((0.24, 0.22, 0.0))
bm = bmesh.new(); add_cyl(bm, 0.085, 0.13, "Z", (COMP_C.x, COMP_C.y, 0.145), 32); add_sphere(bm, 0.085, (COMP_C.x, COMP_C.y, 0.21), 0, 32)
COMP = mesh_obj("Compressor", bm, M_COMP)
for p in COMP.data.polygons: p.use_smooth = True
SQZ = lambda t: 1.0 - 0.06 * math.sin(math.pi * lin((t - C["squeezes"]) / 0.5)) - 0.06 * math.sin(math.pi * lin((t - C["squeezing"]) / 0.5))
COMP.location = (COMP_C.x, COMP_C.y, 0.06)
for v in COMP.data.vertices: v.co -= Vector((COMP_C.x, COMP_C.y, 0.06))
for ax in (0, 1): bake_fn(COMP, "scale", ax, lambda t: 2.0 - SQZ(t))
bake_fn(COMP, "scale", 2, SQZ)
for k, (dx, dy) in enumerate(((-0.06, -0.06), (0.06, -0.06), (-0.06, 0.06), (0.06, 0.06))):
    cyl(f"CompFoot{k}", 0.018, 0.02, "Z", (COMP_C.x + dx, COMP_C.y + dy, 0.07), M_RUBBER)
box("CompBase", 0.13, 0.35, 0.10, 0.34, 0.06, 0.068, M_WIRE)
# condenser on the back: 13 horizontal runs across the full width (outside the cabinet), black steel wires as rungs
CZ = [1.66 - 0.10 * k for k in range(13)]
CX = 0.40
cond_pts = []
for k, z in enumerate(CZ):
    a, b = (0.34, -0.34) if k % 2 == 0 else (-0.34, 0.34)
    cond_pts += [(CX, a, z), (CX, b, z)]
bm = bmesh.new()
for yw in [-0.30 + 0.05 * i for i in range(13)]:
    add_bar(bm, (CX + 0.012, yw, CZ[-1] - 0.03), (CX + 0.012, yw, CZ[0] + 0.03), 0.004)
mesh_obj("CondenserWires", bm, M_WIRE)
EZ = [1.38 + 0.07 * k for k in range(5)]
EX = 0.25
evap_pts = []
for k, z in enumerate(EZ):
    a, b = (0.02, 0.32) if k % 2 == 0 else (0.32, 0.02)
    evap_pts += [(EX, a, z), (EX, b, z)]
SEG = {
    "comp_in": [(0.24, 0.22, 0.14), (0.24, 0.22, 0.20), (0.325, 0.22, 0.20)],
    "discharge": [(0.325, 0.22, 0.20), (CX, 0.22, 0.20), (CX, 0.37, 0.20), (CX, 0.37, 1.66), (CX, 0.34, 1.66)],
    "condenser": cond_pts,
    "capillary": [cond_pts[-1], (CX, -0.34, 0.40), (CX, 0.0, 0.40), (0.322, 0.0, 0.40), (0.322, 0.0, 1.38), (EX, 0.02, 1.38)],
    "evaporator": evap_pts,
    "suction": [evap_pts[-1], (EX, 0.32, 1.72), (EX, 0.0, 1.72), (0.346, 0.0, 1.72), (0.346, 0.0, 0.31), (0.30, 0.12, 0.20), (0.27, 0.19, 0.16), (0.24, 0.22, 0.14)],
}
ORDER = ["comp_in", "discharge", "condenser", "capillary", "evaporator", "suction"]
LOOP_PTS = []
for k in ORDER:
    pts = SEG[k] if not LOOP_PTS else SEG[k][1:]
    LOOP_PTS += pts
LOOP = Path(LOOP_PTS)
BOUND = {}; acc = 0.0
for k in ORDER:
    p_ = Path(SEG[k]); BOUND[k] = (acc, acc + p_.L); acc += p_.L
print("LOOP length", round(LOOP.L, 2), {k: (round(a, 2), round(b, 2)) for k, (a, b) in BOUND.items()})
T_DISCH = tube("DischargeLine", SEG["discharge"], 0.009, M_COPPER)
T_COND = tube("CondenserCoil", SEG["condenser"], 0.008, M_COND)
T_CAP = tube("CapillaryTube", SEG["capillary"], 0.0045, M_CAP)
T_EVAP = tube("EvaporatorCoil", SEG["evaporator"], 0.009, M_EVAP)
T_SUCT = tube("SuctionLine", SEG["suction"], 0.010, M_SUCT)
bm = bmesh.new()
for i in range(11):
    y = 0.025 + 0.029 * i; add_box(bm, EX - 0.018, EX + 0.018, y - 0.0015, y + 0.0015, EZ[0] - 0.03, EZ[-1] + 0.03)
mesh_obj("EvaporatorFins", bm, M_EVAP)
# gold tracer that draws the whole loop on "one sealed loop of tubing"
TRACE = tube("LoopTrace", LOOP_PTS, 0.016, M_TRACE)
T_TR0, T_TR1 = C["sealed"] - 0.1, C["filled"] - 0.1
windows(TRACE, [(T_TR0, C["fluid"])])
def _trace_end(t): return lin((t - T_TR0) / (T_TR1 - T_TR0))
for fr in range(F(T_TR0) - 1, F(T_TR1) + 2):
    TRACE.data.bevel_factor_end = max(0.0, _trace_end((fr - 1) / FPS)); TRACE.data.keyframe_insert("bevel_factor_end", frame=fr)
glow(B_TRACE, [(0, 7.0), (C["filled"] - 0.1, 7.0), (C["fluid"], 0.0)])

# refrigerant beads circulating; flow pauses while the thermostat has the compressor off
T_OFF0, T_OFF1 = C["off"] + 0.05, C["off"] + 0.85
SPEED = 0.85                                               # m/s along the loop
def speed(t):
    if t < C["filled"] - 0.3: return 0.0
    v = SPEED * min(1.0, (t - (C["filled"] - 0.3)) / 0.8)
    if T_OFF0 <= t < T_OFF1: v *= max(0.0, 1 - ease((t - T_OFF0) / 0.25)) if t < T_OFF0 + 0.25 else (0.0 if t < T_OFF1 - 0.3 else ease((t - (T_OFF1 - 0.3)) / 0.3))
    return v
PHASE = [0.0]
for t in TS[1:]: PHASE.append(PHASE[-1] + speed(t) / FPS)
def heat_at(s):
    a, b = BOUND["condenser"]; c0, c1 = BOUND["capillary"]; e0, e1 = BOUND["evaporator"]; s0, s1 = BOUND["suction"]
    if s < a: return 1.0
    if s < b: return 1.0 - 0.45 * (s - a) / (b - a)
    if s < c1: u = (s - c0) / (c1 - c0); return 0.55 - 0.05 * u if u < 0.8 else 0.5 - 0.48 * ease((u - 0.8) / 0.2)
    if s < e1: return 0.02
    if s < s1 - 0.15: return 0.12
    return 1.0
N_BEAD = 80
BEADS = []
bm = bmesh.new(); add_sphere(bm, 0.013, (0, 0, 0), 0, 12); BEAD_ME = bpy.data.meshes.new("BeadMesh"); bm.to_mesh(BEAD_ME); bm.free(); BEAD_ME.materials.append(M_BEAD)
for p in BEAD_ME.polygons: p.use_smooth = True
for k in range(N_BEAD):
    o = bpy.data.objects.new(f"Bead{k:02d}", BEAD_ME); CL.objects.link(o); BEADS.append(o)
    s_of = lambda i, k=k: (PHASE[i] + k * LOOP.L / N_BEAD) % LOOP.L
    pos = [LOOP.at(s_of(i))[0] for i in range(FRAMES)]
    for ax in range(3): bake(o, "location", ax, [p_[ax] for p_ in pos])
    bake(o, "color", 0, [heat_at(s_of(i)) for i in range(FRAMES)])
    o.color = (0, 0, 0, 1)
    bake(o, "scale", 0, [min(1.0, max(0.02, (t - (C["filled"] - 0.4)) / 0.4)) for t in TS])
    for ax in (1, 2): bake(o, "scale", ax, [min(1.0, max(0.02, (t - (C["filled"] - 0.4)) / 0.4)) for t in TS])
    windows(o, [(C["filled"] - 0.4, DUR)])

# ---------- freezer parts: fan, damper flap, thermostat, defrost heater, trough, drain tube, pan ----------
FAN_C = Vector((0.17, 0.17, 1.705))
FAN = empty("Fan", FAN_C)
bm = bmesh.new(); add_cyl(bm, 0.018, 0.03, "X", (0, 0, 0), 16)
for i in range(5):
    a = 2 * math.pi * i / 5; d = Vector((0, math.cos(a), math.sin(a)))
    add_bar(bm, d * 0.012, d * 0.052, 0.022)
blades = mesh_obj("FanBlades", bm, M_FAN, FAN)
bm = bmesh.new()
for i in range(16):
    a0, a1 = 2 * math.pi * i / 16, 2 * math.pi * (i + 1) / 16
    add_bar(bm, (FAN_C.x + 0.01, FAN_C.y + 0.058 * math.cos(a0), FAN_C.z + 0.058 * math.sin(a0)), (FAN_C.x + 0.01, FAN_C.y + 0.058 * math.cos(a1), FAN_C.z + 0.058 * math.sin(a1)), 0.006)
mesh_obj("FanShroud", bm, M_FAN)
FAN_ON = lambda t: 0.0 if (t < C["filled"] or T_OFF0 + 0.1 <= t < T_OFF1) else 1.0
FAN_ANG = [0.0]
for t in TS[1:]: FAN_ANG.append(FAN_ANG[-1] + (14.0 if FAN_ON(t) else 0.0) / FPS)
bake(FAN, "rotation_euler", 0, FAN_ANG)
FLAP = empty("Flap", (0.26, 0.19, ZM0))
box("FlapPlate", -0.14, 0.0, -0.085, 0.085, 0.0, 0.008, M_FLAP, FLAP)
FLAP_ANG = PW([(0, 0.0), (C["flap"] - 0.1, 0.0), (C["flap"] + 0.5, -1.05), (C["gas2"] + 0.5, -1.05), (C["gas2"] + 1.0, -0.35)])
bake_fn(FLAP, "rotation_euler", 1, lambda t: -FLAP_ANG(t))
THERMO = empty("Thermostat", (-0.05, 0.30, ZM0))
box("ThermoBox", -0.07, 0.07, -0.04, 0.04, -0.06, 0.0, M_THERMO, THERMO)
cyl("ThermoDial", 0.025, 0.012, "Y", (-0.05, 0.255, ZM0 - 0.03), M_HANDLE)
HEATER = tube("DefrostHeater", [(EX, 0.01, 1.335), (EX, 0.33, 1.335)], 0.006, M_HEATER)
box("DrainTrough", EX - 0.05, EX + 0.06, 0.0, 0.34, 1.300, 1.308, M_LINER)
DRAIN = [(EX + 0.03, 0.06, 1.30), (0.334, 0.0, 1.29), (0.334, 0.0, 0.33), (0.30, 0.03, 0.18), (0.25, 0.07, 0.12)]
tube("DrainTube", DRAIN, 0.008, mat("DrainHose", (0.85, 0.85, 0.82), 0.5)[0])
PAN = (0.15, 0.34, 0.015, 0.13)
bm = bmesh.new(); add_box(bm, PAN[0], PAN[1], PAN[2], PAN[3], 0.068, 0.072)
for (x0, x1, y0, y1) in ((PAN[0], PAN[1], PAN[2], PAN[2] + 0.004), (PAN[0], PAN[1], PAN[3] - 0.004, PAN[3]), (PAN[0], PAN[0] + 0.004, PAN[2], PAN[3]), (PAN[1] - 0.004, PAN[1], PAN[2], PAN[3])):
    add_box(bm, x0, x1, y0, y1, 0.068, 0.11)
mesh_obj("DrainPan", bm, M_PAN)
PANW = box("PanWater", PAN[0] + 0.005, PAN[1] - 0.005, PAN[2] + 0.005, PAN[3] - 0.005, 0.0, 1.0, M_WATER); PANW.location.z = 0.072
T_DROP0 = C["drains"] - 0.1
WATER_H = PW([(0, 0.0), (T_DROP0 + 0.6, 0.0), (C["pan"] + 0.6, 0.026), (C["dries"] - 0.1, 0.026), (C["so2"] + 0.2, 0.0)])
bake_fn(PANW, "scale", 2, lambda t: max(0.0005, WATER_H(t)))
windows(PANW, [(T_DROP0 + 0.6, C["so2"] + 0.25)])

# frost: white sleeves on each evaporator run, grow on "frost builds up", melt on "heater melts it"
FROST_S = PW([(0, 0.3), (C["frost"] - 0.1, 0.3), (C["coils3"] + 0.3, 1.0), (C["melts"] - 0.1, 1.0), (C["now"] + 0.5, 0.3)])
for k, z in enumerate(EZ):
    o = empty(f"Frost{k}", (EX, 0.17, z))
    bm = bmesh.new(); add_cyl(bm, 0.03, 0.31, "Y", (0, 0, 0), 14)
    for f_ in range(9): add_sphere(bm, 0.018, (random.uniform(-0.01, 0.01), -0.14 + f_ * 0.035, random.uniform(0.012, 0.02)), 0, 8)
    fr_ = mesh_obj(f"FrostMesh{k}", bm, M_FROST, o)
    windows(o, [(C["frost"] - 0.1, C["now"] + 0.55)])
    for ax in (0, 2): bake_fn(o, "scale", ax, FROST_S)
glow(B_HEATER, [(0, 0), (C["heater"] - 0.15, 0), (C["heater"] + 0.2, 9.0), (C["now"] + 0.6, 9.0), (C["water"] + 0.4, 0)])
# meltwater drops run down the drain tube into the pan
DPATH = Path(DRAIN)
for k in range(4):
    o = sphere(f"Drop{k}", 0.012, (0, 0, 0), M_WATER, seg=10)
    t0 = T_DROP0 + 0.28 * k
    pos = [DPATH.at(DPATH.L * lin((t - t0) / 1.1))[0] for t in TS]
    for ax in range(3): bake(o, "location", ax, [p_[ax] for p_ in pos])
    windows(o, [(t0, t0 + 1.1)])
# steam wisps rise off the pan while the warmth dries it
for k in range(5):
    o = sphere(f"Steam{k}", 0.022, (0, 0, 0), M_STEAM, seg=10)
    x0, y0 = PAN[0] + 0.03 + 0.035 * k, 0.04 + 0.015 * (k % 3)
    def st(t, k=k): return ((t - C["where"]) / 1.4 + k / 5.0) % 1.0
    bake_fn(o, "location", 0, lambda t, x0=x0: x0); bake_fn(o, "location", 1, lambda t, y0=y0: y0)
    bake_fn(o, "location", 2, lambda t, k=k: 0.10 + 0.22 * st(t))
    for ax in range(3): bake_fn(o, "scale", ax, lambda t, k=k: max(0.05, math.sin(math.pi * st(t))) * (0.7 + 0.6 * st(t)))
    windows(o, [(C["where"], C["so2"] + 0.3)])

# ---------- arrows (air = cyan, heat = orange) ----------
def arrow_mesh(name, m_, L=0.10, r=0.010):
    bm = bmesh.new(); add_cyl(bm, r, L * 0.65, "X", (L * 0.325, 0, 0), 12); add_cyl(bm, r * 2.4, L * 0.35, "X", (L * 0.825, 0, 0), 14, r2=0.0)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m_); return me
AIR_ME, HEAT_ME, HEAT_BIG = arrow_mesh("AirArrowMesh", M_AIR), arrow_mesh("HeatArrowMesh", M_HEATA), arrow_mesh("HeatArrowBig", M_HEATA, 0.22, 0.02)
def flow_arrows(name, me, pts, n, period, wins):
    """n arrows cycling along a path during the windows; they fade in/out by scale at the ends."""
    P_ = Path(pts); out = []
    for k in range(n):
        o = bpy.data.objects.new(f"{name}{k}", me); CL.objects.link(o); out.append(o)
        u = lambda t, k=k: ((t - wins[0][0]) / period + k / n) % 1.0
        pos = [P_.at(P_.L * u(t)) for t in TS]
        for ax in range(3): bake(o, "location", ax, [p_[0][ax] for p_ in pos])
        eul = [Vector((1, 0, 0)).rotation_difference(p_[1]).to_euler() for p_ in pos]
        for ax in range(3): bake(o, "rotation_euler", ax, [e[ax] for e in eul])
        sc = [max(0.05, min(1.0, 4 * min(u(t), 1 - u(t)))) for t in TS]
        for ax in range(3): bake(o, "scale", ax, sc)
        windows(o, wins)
    return out
HEAT_OUT_WINS = [(C["moves"] - 0.1, C["lets"] - 0.1), (C["dumps"] - 0.1, C["next"] - 0.2), (C["pump"] - 0.3, C["end"])]
for j, z in enumerate((0.62, 0.98, 1.34)):
    flow_arrows(f"HeatOut{j}_", HEAT_BIG, [(0.44, 0.08 - 0.08 * j, z), (0.62, 0.08 - 0.08 * j, z + 0.05), (0.80, 0.08 - 0.08 * j, z + 0.14)], 2, 1.3, HEAT_OUT_WINS)
# warmth from the food into the cold coils (freezer)
for j, (y, z) in enumerate(((0.10, 1.47), (0.22, 1.56), (0.16, 1.66))):
    flow_arrows(f"HeatIn{j}_", HEAT_ME, [(-0.18, y, z), (0.0, y, z), (0.20, y, z - 0.01)], 2, 1.2, [(C["soaks"] - 0.1, C["fan"] - 0.1)])
# cold air from the fan forward through the freezer, and down through the flap into the fridge
FZ_LOOP = [(0.12, 0.17, 1.72), (-0.24, 0.17, 1.72), (-0.27, 0.17, 1.55), (-0.10, 0.17, 1.50), (0.10, 0.17, 1.47)]
flow_arrows("AirFz", AIR_ME, FZ_LOOP, 4, 2.2, [(C["fan"] - 0.1, C["gas2"] + 0.4)])
FLAP_PATH = [(0.20, 0.19, 1.45), (0.19, 0.19, 1.20), (0.12, 0.19, 1.06), (-0.10, 0.19, 1.02), (-0.24, 0.19, 0.95)]
flow_arrows("AirFr", AIR_ME, FLAP_PATH, 3, 1.6, [(C["flap"] + 0.3, C["gas2"] + 0.4)])

# ---------- glows on the parts, on their words ----------
glow(B_COMP, [(0, 0), (C["compressor"] - 0.15, 0), (C["compressor"] + 0.2, 0.6), (C["squeezing"], 0.6), (C["hot"], 1.4), (C["hot2"] + 0.4, 1.4), (C["flows"] + 0.4, 0),
              (C["compressor2"] - 0.15, 0), (C["compressor2"] + 0.2, 0.8), (C["thermostat"], 0.8), (T_OFF0, 0.8), (T_OFF0 + 0.1, 0.0), (T_OFF1 - 0.2, 0.0), (T_OFF1, 0.8),
              (C["one"] - 0.2, 0.8), (C["one"] + 0.3, 0)])
glow(B_COND, [(0, 0), (C["moves"] - 0.1, 0), (C["moves"] + 0.3, 2.5), (C["lets"] - 0.1, 2.5), (C["lets"] + 0.2, 0), (C["coils"] - 0.2, 0), (C["coils"] + 0.2, 3.0),
              (C["warm"] + 0.3, 3.0), (C["next"] + 0.1, 0), (C["pump"] - 0.3, 0), (C["pump"] + 0.1, 3.5), (C["end"], 3.5)])
glow(B_CAP, [(0, 0), (C["thin"] - 0.2, 0), (C["thin"] + 0.1, 6.0), (C["colder"] + 0.3, 6.0), (C["so"] + 0.3, 0)])
glow(B_EVAP, [(0, 0), (C["evaporator"] - 0.2, 0), (C["evaporator"] + 0.2, 2.2), (C["fan"] - 0.2, 2.2), (C["fan"] + 0.3, 0.8), (C["gas2"], 0), (C["pump"] - 0.3, 0), (C["pump"] + 0.1, 3.0), (C["did"], 3.0), (C["did"] + 0.4, 0)])
glow(B_SUCT, [(0, 0), (C["gas2"] - 0.1, 0), (C["gas2"] + 0.2, 2.5), (C["again"] + 0.3, 2.5), (C["thermostat"] - 0.2, 0)])
glow(B_FAN, [(0, 0), (C["fan"] - 0.1, 0), (C["fan"] + 0.2, 3.0), (C["around"] + 0.2, 3.0), (C["around"] + 0.6, 0)])
glow(B_FLAP, [(0, 0), (C["flap"] - 0.1, 0), (C["flap"] + 0.2, 3.0), (C["fridge2"] + 0.3, 3.0), (C["gas2"] + 0.2, 0)])
glow(B_THERMO, [(0, 0), (C["thermostat"] - 0.1, 0), (C["thermostat"] + 0.2, 4.0), (C["one"] - 0.2, 4.0), (C["one"] + 0.2, 0)])

# ---------- near half slides away on "cut it open" ----------
bake_fn(NEAR, "location", 1, lambda t: -2.6 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)))
bake_fn(NEAR, "location", 2, lambda t: 0.25 * math.sin(math.pi * lin((t - T_CUT0) / (T_CUT1 - T_CUT0))))
windows(NEAR, [(0, T_CUT1 + 0.05)])

# ---------- camera ----------
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36.0
cam_d.dof.use_dof = False
cam_d.clip_start = 0.02; cam_d.clip_end = 100
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-2.0, -4.2, 1.55), (0.0, 0.0, 0.98), 40),
    (C["heres"], (-1.6, -3.4, 1.45), (0.0, 0.0, 0.96), 40),
    (C["moves"] - 0.15, (2.5, -2.9, 1.35), (0.25, 0.0, 0.98), 32, "cut"),
    (C["lets"] - 0.1, (0.45, -3.3, 1.05), (0.0, 0.1, 0.95), 34, "cut"),
    (C["hidden"] - 0.1, (0.75, -2.85, 1.05), (0.05, 0.15, 0.95), 34),
    (C["temperatures"], (0.8, -2.7, 1.0), (0.05, 0.15, 0.95), 34),
    (C["bottom"] - 0.15, (0.02, -0.72, 0.30), (0.24, 0.18, 0.17), 30, "cut"),
    (C["hot"] + 0.2, (0.10, -0.85, 0.36), (0.26, 0.18, 0.19), 30),
    (C["hot2"] - 0.25, (2.0, -1.8, 1.25), (0.38, 0.05, 1.02), 30, "cut"),
    (C["thats"] - 0.1, (2.4, -2.2, 1.30), (0.38, 0.05, 1.0), 30),
    (C["next"] - 0.15, (0.05, -0.85, 0.55), (0.33, 0.0, 0.62), 32, "cut"),
    (C["pressure"], (0.05, -0.85, 1.15), (0.31, 0.0, 1.25), 32),
    (C["so"] - 0.15, (-0.15, -1.35, 1.58), (0.14, 0.17, 1.52), 30, "cut"),
    (C["soaks"], (-0.10, -1.25, 1.56), (0.10, 0.17, 1.52), 30),
    (C["fan"] - 0.15, (-0.40, -2.0, 1.42), (0.03, 0.17, 1.32), 32, "cut"),
    (C["gas2"] - 0.15, (0.8, -2.9, 1.05), (0.05, 0.15, 0.95), 34, "cut"),
    (C["thermostat"] - 0.1, (0.55, -2.55, 0.95), (0.05, 0.15, 0.85), 34),
    (C["one"] - 0.15, (0.0, -1.05, 1.52), (0.20, 0.17, 1.49), 32, "cut"),
    (C["water"] - 0.15, (0.05, -1.30, 0.95), (0.31, 0.05, 0.85), 30, "cut"),
    (C["pan"] - 0.3, (0.05, -0.95, 0.40), (0.25, 0.08, 0.15), 30),
    (C["so2"] - 0.15, (2.0, -2.45, 1.4), (0.18, 0.05, 0.98), 34, "cut"),
    (C["did"] - 0.1, (1.55, -1.05, 1.15), (0.40, 0.05, 1.05), 30, "cut"),
    (C["end"], (2.3, -1.9, 1.3), (0.35, 0.05, 1.02), 30),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]; u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0     # every shot keeps drifting to the next key
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.006 * math.sin(t * 0.7), 0.0, 0.004 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
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
gr = wn.new("ShaderNodeValToRGB"); e = gr.color_ramp.elements; e[0].color = (0.006, 0.010, 0.018, 1); e[1].color = (0.05, 0.075, 0.11, 1)
wl.new(grad.outputs["Fac"], gr.inputs[0])
bg_dark = wn.new("ShaderNodeBackground"); wl.new(gr.outputs[0], bg_dark.inputs["Color"])
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.12
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_ref.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
def target(name, loc):
    o = bpy.data.objects.new(name, None); scene.collection.objects.link(o); o.location = loc; return o
def area(name, loc, size, power, rgb=(1, 1, 1), target_=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target_; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
def point(name, loc, power, rgb, radius=0.05):
    d = bpy.data.lights.new(name, "POINT"); d.energy = power; d.color = rgb; d.shadow_soft_size = radius
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; return o, d
LT = target("LT_Fridge", (0.0, 0.1, 0.95))
area("Key", (-2.2, -2.6, 2.6), 1.6, 260, (1.0, 0.93, 0.84), LT)
area("Fill", (1.6, -2.8, 1.0), 1.6, 90, (0.75, 0.85, 1.0), LT)
area("Rim", (2.4, 1.6, 2.4), 1.2, 220, (0.8, 0.88, 1.0), LT)
area("BackKey", (2.2, -0.6, 1.4), 1.0, 70, (1.0, 0.92, 0.85), target("LT_Back", (0.4, 0.0, 1.0)))
_, LAMP = point("FridgeLamp", (-0.05, 0.22, 1.12), 0.0, (1.0, 0.93, 0.8), 0.04)
_, FZL = point("FreezerLamp", (-0.05, 0.20, 1.70), 0.0, (0.8, 0.9, 1.0), 0.04)
for lamp_d, pw in ((LAMP, 6.0), (FZL, 2.5)):
    lamp_d.energy = 0.0; lamp_d.keyframe_insert("energy", frame=F(C["cut"]))
    lamp_d.energy = pw; lamp_d.keyframe_insert("energy", frame=F(C["open"] + 0.3))
area("CamFill", (0, 0, 0), 0.5, 3, (1.0, 0.96, 0.9), TGT).parent = cam

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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4
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
def mid(seg, u): P_ = Path(SEG[seg]); return P_.at(P_.L * u)[0]
ANCH = {
    "fridge": lambda t: Vector((-0.42, -0.2, 1.5)),
    "back": lambda t: Vector((CX, -0.1, 1.2)),
    "loop": lambda t: Vector((0.346, 0.0, 1.0)),
    "refrigerant": lambda t: mid("suction", 0.55) + Vector((0, -0.01, 0)),
    "compressor": lambda t: Vector((COMP_C.x - 0.06, COMP_C.y - 0.08, 0.24)),
    "condenser": lambda t: Vector((CX, -0.20, 1.21)),
    "capillary": lambda t: Vector((0.322, 0.0, 0.60 + 0.63 * ease((t - (C["next"] - 0.15)) / (C["pressure"] - C["next"] + 0.15)))),
    "evaporator": lambda t: Vector((EX, 0.02, 1.52)),
    "fan": lambda t: FAN_C + Vector((-0.02, -0.06, 0.0)),
    "flap": lambda t: Vector((0.19, 0.12, ZM0 - 0.02)),
    "thermostat": lambda t: Vector((-0.05, 0.26, ZM0 - 0.05)),
    "heater": lambda t: Vector((EX, 0.03, 1.335)),
    "frost": lambda t: Vector((EX - 0.03, 0.05, EZ[2])),
    "drain": lambda t: DPATH.at(DPATH.L * lin((t - T_DROP0) / 1.1))[0],
    "pan": lambda t: Vector(((PAN[0] + PAN[1]) / 2 - 0.05, PAN[2], 0.10)),
}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        w = a(tt)
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"cut": [round(T_CUT0, 3), round(T_CUT1, 3)], "trace": [round(T_TR0, 3), round(T_TR1, 3)], "flow_start": round(C["filled"] - 0.3, 3),
          "off": [round(T_OFF0, 3), round(T_OFF1, 3)], "flap": round(C["flap"] - 0.1, 3), "fan": round(C["fan"] - 0.1, 3),
          "frost": round(C["frost"] - 0.1, 3), "heater": round(C["heater"] - 0.15, 3), "drops": [round(T_DROP0 + 0.28 * k + 1.1, 3) for k in range(4)],
          "steam": round(C["where"], 3), "loop_length_m": round(LOOP.L, 2), "cta": round(C["did"] - 0.1, 3)}
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
