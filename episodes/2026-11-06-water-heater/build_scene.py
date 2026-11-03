# Water-Heater-3D: how a tank water heater works (gas, glass-lined steel tank). Studio cutaway in Blender Cycles. Every cue is a word in the VO.
# One set: a generic gas storage water heater cut in half through its centre (the cut face looks at -Y): sheet-steel jacket, foam,
#   steel tank with a glass lining, water (colour = temperature), flue through the middle with a twisted baffle, burner + flames under the tank,
#   cold inlet + plastic dip tube, hot outlet, magnesium anode rod, sediment layer, drain valve, T&P relief valve + discharge pipe, gas control.
#   Standing on a cut concrete floor in front of a block wall. Electric elements appear only for the "electric heater" line.
# A front cover (the uncut front half of the jacket) is in place for the hook and slides away on "cut".
# No people, no brand. Sizes are illustrative (1 unit = 10 cm; the anode rod is drawn thicker than real so it reads on a phone).
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
random.seed(13)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')

CUES = [("metal", "metal"), ("rod", "rod"), ("rots", "rots"), ("purpose", "purpose"), ("lets", "let's"), ("cut", "cut"), ("open", "open"),
        ("steel", "steel"), ("glass", "glass"), ("foam", "foam"), ("cold", "cold"), ("top", "top"), ("dip", "dip"), ("bottom", "bottom"),
        ("under", "under"), ("burner", "burner"), ("fires", "fires"), ("exhaust", "exhaust"), ("climbs", "climbs"), ("flue", "flue"),
        ("middle", "middle"), ("baffle", "baffle"), ("slows", "slows"), ("heat", "heat"), ("soaks", "soaks"), ("electric", "electric"),
        ("elements", "elements"), ("hotw", "hot"), ("lighter", "lighter"), ("rises", "rises"), ("hottest", "hottest"), ("top2", "top"),
        ("pipe2", "pipe"), ("pulls", "pulls"), ("open2", "open"), ("faucet", "faucet"), ("cold2", "cold"), ("below", "below"),
        ("always", "always"), ("full", "full"), ("now", "now"), ("rod2", "rod"), ("anode", "anode"), ("magnesium", "magnesium"),
        ("hot3", "hot"), ("eats", "eats"), ("magnesium2", "magnesium"), ("first", "first"), ("corrodes", "corrodes"), ("steel2", "steel"),
        ("doesnt", "doesn't"), ("once", "once"), ("used", "used"), ("rust", "rust"), ("sediment", "sediment"), ("minerals", "minerals"),
        ("settle", "settle"), ("trap", "trap"), ("underneath", "underneath"), ("pops", "pops"), ("rumbles", "rumbles"),
        ("flushing", "flushing"), ("washes", "washes"), ("up", "up"), ("safety", "safety"), ("valve", "valve"), ("opens", "opens"),
        ("hundred", "hundred"), ("fifty", "fifty"), ("psi", "psi"), ("two", "two"), ("ten", "ten"), ("degrees", "degrees"),
        ("have", "have"), ("flushed", "flushed"), ("tell", "tell"), ("comments", "comments"), ("next", "next"), ("oil", "oil"),
        ("follow", "follow")]
C = {}
for name, word in CUES: C[name] = TA(word)
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
TS = [(fr - 1) / FPS for fr in range(1, FRAMES + 1)]
def bake_fn(owner, path, index, fn): return bake(owner, path, index, [fn(t) for t in TS])
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("WaterHeater")

# ---------- easing ----------
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
def drop(t, t0, h=8.0, d=0.55):
    """Vertical offset of a piece dropped in at t0 (starts h above, lands with a tiny bounce)."""
    p = (t - t0) / d
    if p <= 0: return h
    if p >= 1: return 0.0 if t > t0 + d + 0.25 else 0.10 * math.sin(math.pi * (t - t0 - d) / 0.25)
    pp = lin(p); return h * (1 - pp * pp)
def pop(t, t0, d=0.25):
    """0 -> 1.12 -> 1 scale pop."""
    p = (t - t0) / d
    if p <= 0: return 0.0
    if p >= 1.6: return 1.0
    if p <= 1: return 1.12 * ease(p)
    return 1.12 - 0.12 * ease((p - 1) / 0.6)

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
def mat(name, rgb, rough=0.4, metallic=0.0, emit_rgb=(1.0, 0.74, 0.27), noise=0.0, alpha=1.0):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise; nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough * 0.7; mr.inputs[4].default_value = rough * 1.4
        nt.links.new(n.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    if alpha < 1.0: b.inputs["Alpha"].default_value = alpha
    return m, b
def glow(bsdf, keys):
    """Emission strength keys [(t, value), ...]."""
    inp = bsdf.inputs["Emission Strength"]
    for t, v in keys:
        inp.default_value = v; inp.keyframe_insert("default_value", frame=F(t))
def pulse(t0, peak, base=0.0, up=0.15, hold=0.5, down=0.6): return [(t0 - 0.01, base), (t0 + up, peak), (t0 + up + hold, peak), (t0 + up + hold + down, base)]
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
def cut_front(bm, y_cut, fill=True):
    """Keep only the part with y >= y_cut (the cutaway plane), cap the cut."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    res = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, y_cut, 0), plane_no=(0, 1, 0), clear_inner=True)
    if fill:
        open_edges = [e for e in bm.edges if len(e.link_faces) < 2]      # the cut opening (geom_cut misses edges that already lay on the plane)
        if open_edges: bmesh.ops.edgeloop_fill(bm, edges=open_edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def half_cyl(name, r, x, y_center, y_cut, z0, z1, m_, parent=None, seg=32):
    """Vertical cylinder cut at the cutaway plane (origin at the cylinder axis, z0 local bottom)."""
    bm = bmesh.new(); add_cyl(bm, r, z1 - z0, "Z", (0, 0, (z0 + z1) / 2), seg)
    cut_front(bm, y_cut - y_center)
    o = mesh_obj(name, bm, m_, parent); o.location = (x, y_center, 0); return o
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
def add_arrow(bm, base, direction, length, width, y=0.0, mi=0):
    """Flat arrow in the XZ plane (facing -Y) from base along a 2D direction (dx, dz)."""
    d = Vector((direction[0], 0, direction[1])).normalized(); n = Vector((-d.z, 0, d.x))
    b0 = Vector((base[0], y, base[1])); hl = min(length * 0.45, width * 1.8)
    tip = b0 + d * length; neck = b0 + d * (length - hl)
    th = 0.12 * width
    pts = [b0 + n * width * 0.28, neck + n * width * 0.28, neck + n * width * 0.7, tip, neck - n * width * 0.7, neck - n * width * 0.28, b0 - n * width * 0.28]
    front = [bm.verts.new(p + Vector((0, -th, 0))) for p in pts]; back = [bm.verts.new(p + Vector((0, th, 0))) for p in pts]
    # shaft quad + head triangle on both sides, then side walls
    for vs in (front, back):
        f1 = bm.faces.new([vs[0], vs[1], vs[5], vs[6]]); f2 = bm.faces.new([vs[2], vs[3], vs[4]])
        f1.material_index = f2.material_index = mi
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        if (i, j) in ((1, 2), (4, 5)): continue
        try: bm.faces.new([front[i], front[j], back[j], back[i]]).material_index = mi
        except ValueError: pass


def tiles(name, rgb1, rgb2, scale, plane="XZ"):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    cmb = N.new("ShaderNodeCombineXYZ")
    a, c = (("X", "Z") if plane == "XZ" else ("X", "Y"))
    L.new(sep.outputs[a], cmb.inputs[0]); L.new(sep.outputs[c], cmb.inputs[1])
    br = N.new("ShaderNodeTexBrick"); L.new(cmb.outputs[0], br.inputs["Vector"])
    br.inputs["Scale"].default_value = scale; br.inputs["Mortar Size"].default_value = 0.02; br.inputs["Brick Width"].default_value = 1.0
    br.inputs["Row Height"].default_value = 1.0; br.offset = 0.0
    br.inputs["Color1"].default_value = (*rgb1, 1); br.inputs["Color2"].default_value = (*rgb2, 1); br.inputs["Mortar"].default_value = (0.25, 0.25, 0.26, 1)
    L.new(br.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.35
    return m

# ================= palette + materials =================
GOLD, CYAN, RED, ORANGE = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12), (1.0, 0.42, 0.10)
M_JACKET, B_JACKET = mat("Jacket", (0.78, 0.79, 0.78), 0.32, 0.0, GOLD)
M_JCUT, _ = mat("JacketEdge", (0.55, 0.56, 0.58), 0.35, 0.8)
M_FOAM, B_FOAM = mat("Foam", (0.86, 0.66, 0.26), 0.85, 0.0, GOLD, 30)
M_STEEL, B_STEEL = mat("TankSteel", (0.30, 0.32, 0.35), 0.38, 0.9, GOLD)
M_FLUE, B_FLUE = mat("Flue", (0.17, 0.18, 0.20), 0.45, 0.8, ORANGE)
M_BAFFLE, B_BAFFLE = mat("Baffle", (0.45, 0.46, 0.48), 0.32, 1.0, GOLD)
M_DIP, B_DIP = mat("DipTube", (0.88, 0.89, 0.90), 0.45, 0.0, CYAN)
M_COPPER, _ = mat("Copper", (0.86, 0.46, 0.27), 0.28, 1.0)
M_BRASS, B_BRASS = mat("Brass", (0.86, 0.66, 0.30), 0.3, 1.0, GOLD)
M_CORE, _ = mat("AnodeCore", (0.35, 0.36, 0.38), 0.5, 1.0)
M_HEX, _ = mat("HexHead", (0.55, 0.56, 0.58), 0.35, 1.0)
M_BURNER, _ = mat("Burner", (0.22, 0.22, 0.24), 0.5, 0.8)
M_DARK, _ = mat("Chamber", (0.03, 0.03, 0.035), 0.7)
M_PANEL, _ = mat("AccessPanel", (0.10, 0.10, 0.11), 0.5, 0.3)
M_KNOB, _ = mat("Knob", (0.75, 0.10, 0.08), 0.4)
M_BLUEB, _ = mat("ColdBand", (0.10, 0.35, 0.95), 0.4, 0.0, (0.1, 0.4, 1.0))
M_REDB, _ = mat("HotBand", (0.90, 0.12, 0.08), 0.4)
M_ELEM, B_ELEM = mat("Element", (0.55, 0.50, 0.45), 0.4, 1.0, ORANGE)
M_ARROW, B_ARROW = mat("ArrowHeat", ORANGE, 0.5, 0.0, ORANGE); B_ARROW.inputs["Emission Strength"].default_value = 5.0
M_DROPC, B_DROPC = mat("DropCold", (0.20, 0.55, 1.0), 0.05, 0.0, (0.2, 0.55, 1.0)); B_DROPC.inputs["Emission Strength"].default_value = 2.2
M_DROPH, B_DROPH = mat("DropHot", (1.0, 0.35, 0.10), 0.1, 0.0, (1.0, 0.35, 0.10)); B_DROPH.inputs["Emission Strength"].default_value = 2.6
M_EXH, B_EXH = mat("Exhaust", (0.9, 0.45, 0.15), 0.6, 0.0, (1.0, 0.45, 0.12), 0, 0.7); B_EXH.inputs["Emission Strength"].default_value = 2.0
M_FLAKE, _ = mat("Flake", (0.42, 0.20, 0.10), 0.7, 0.0)
M_GRAIN, _ = mat("Grain", (0.72, 0.62, 0.45), 0.8, 0.0)
M_BUB, B_BUB = mat("Bubble", (0.9, 0.95, 1.0), 0.1, 0.0, (0.9, 0.95, 1.0), 0, 0.85); B_BUB.inputs["Emission Strength"].default_value = 1.4
M_STEAM, B_STEAM = mat("Steam", (0.92, 0.95, 1.0), 0.3, 0.0, (0.9, 0.95, 1.0), 0, 0.55); B_STEAM.inputs["Emission Strength"].default_value = 1.2
def sed_material():
    m, nt, b = new_mat("Sediment"); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); vz = N.new("ShaderNodeTexVoronoi"); vz.inputs["Scale"].default_value = 28.0
    L.new(tc.outputs["Object"], vz.inputs["Vector"])
    col = mix_rgb(nt, vz.outputs["Distance"], (0.50, 0.30, 0.10), (0.16, 0.10, 0.05))
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.8; L.new(vz.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (*GOLD, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
M_FLOOR = tiles("Concrete", (0.11, 0.11, 0.12), (0.095, 0.095, 0.105), 0.12, "XY")
M_WALL = tiles("Block", (0.055, 0.06, 0.07), (0.048, 0.052, 0.062), 0.16, "XZ")
M_SLABCUT, _ = mat("SlabCut", (0.32, 0.31, 0.30), 0.9, 0.0, GOLD, 18)

def keyval(node_socket, keys):
    for t, v in keys:
        node_socket.default_value = v; node_socket.keyframe_insert("default_value", frame=F(t))

def mask_nodes(nt, scale, thr_keys, name):
    """noise > threshold (keyed) -> 0/1 mask; lower threshold = more spots."""
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    thr = N.new("ShaderNodeValue"); thr.name = name; keyval(thr.outputs[0], thr_keys)
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; L.new(nz.outputs["Fac"], gt.inputs[0]); L.new(thr.outputs[0], gt.inputs[1])
    return gt.outputs[0]
def mix_rgb(nt, fac, a, b):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = "RGBA"
    nt.links.new(fac, m.inputs[0])
    if isinstance(a, tuple): m.inputs[6].default_value = (*a, 1)
    else: nt.links.new(a, m.inputs[6])
    if isinstance(b, tuple): m.inputs[7].default_value = (*b, 1)
    else: nt.links.new(b, m.inputs[7])
    return m.outputs[2]

M_SED, B_SED = sed_material()

# ================= timing constants (beats) =================
T_LIFT0, T_LIFT1 = 0.25, C["rod"] + 0.8            # anode rises out of the closed heater in the hook
T_COR0, T_COR1 = C["rots"] - 0.1, C["purpose"] + 0.5
T_DOWN0, T_DOWN1 = C["lets"] - 0.2, C["cut"] + 0.15
T_CV0, T_CV1 = C["cut"] - 0.05, C["open"] + 0.4
T_FIRE = C["fires"] - 0.2
T_E0, T_E1 = C["electric"] - 0.1, C["hotw"] - 0.1       # electric elements window (flame off)
T_A_PITS = C["eats"]                                    # anode beat
T_A_SH0, T_A_SH1 = C["corrodes"] - 0.1, C["doesnt"] + 0.3
T_A_GONE0, T_A_GONE1 = C["used"] - 0.1, C["rust"] - 0.1
T_RUST0, T_RUST1 = C["rust"] - 0.1, C["rust"] + 0.7
T_RESET = C["sediment"] - 0.12                          # hard cut: anode + lining back to new (illustrative)
T_SED0, T_SED1 = C["minerals"], C["trap"] + 0.1
T_FL0, T_FL1 = C["flushing"], C["up"] - 0.15
T_TP0, T_TP1 = C["opens"] - 0.1, C["have"] - 0.4

# ================= materials with keyed states =================
# water: blue when cold, temperature gradient (blue bottom -> orange top) once heated
def water_material():
    m, nt, b = new_mat("TankWater"); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 1.6; mr.inputs[2].default_value = 12.0; L.new(sep.outputs["Z"], mr.inputs[0])
    rp = N.new("ShaderNodeValToRGB"); e = rp.color_ramp.elements
    e[0].position = 0.12; e[0].color = (0.06, 0.28, 0.95, 1); e[1].position = 0.92; e[1].color = (1.0, 0.30, 0.06, 1)
    mid = rp.color_ramp.elements.new(0.55); mid.color = (0.75, 0.30, 0.45, 1)
    L.new(mr.outputs[0], rp.inputs[0])
    heat = N.new("ShaderNodeValue"); heat.name = "HEAT"
    col = mix_rgb(nt, heat.outputs[0], (0.08, 0.36, 0.95), rp.outputs[0])
    L.new(col, b.inputs["Base Color"]); L.new(col, b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.45; b.inputs["Roughness"].default_value = 0.05
    wa = N.new("ShaderNodeValue"); wa.name = "WALPHA"; L.new(wa.outputs[0], b.inputs["Alpha"])
    return m, heat, wa
M_WATER, HEAT, WALPHA = water_material()
HEAT_KEYS = [(0, 0.0), (T_FIRE + 0.5, 0.0), (C["soaks"] + 0.5, 0.55), (C["electric"], 0.6), (C["hottest"], 1.0), (C["open2"] + 0.5, 1.0),
             (C["always"], 0.82), (C["now"], 0.9), (C["have"], 1.0)]
keyval(HEAT.outputs[0], HEAT_KEYS)
keyval(WALPHA.outputs[0], [(0, 0.34), (C["now"] - 0.16, 0.34), (C["now"] - 0.15, 0.13), (T_RESET - 0.01, 0.13), (T_RESET, 0.26), (C["up"] - 0.21, 0.26), (C["up"] - 0.2, 0.34)])

# glass lining: pale enamel, rust spots keyed for "starts to rust"
def lining_material():
    m, nt, b = new_mat("GlassLining")
    b.inputs["Roughness"].default_value = 0.12; b.inputs["Coat Weight"].default_value = 0.8
    mk = mask_nodes(nt, 6.0, [(0, 1.2), (T_RUST0, 1.2), (T_RUST1, 0.44), (T_RESET - 0.01, 0.44), (T_RESET, 1.2)], "RUST")
    col = mix_rgb(nt, mk, (0.62, 0.78, 0.84), (0.55, 0.15, 0.03))
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (*CYAN, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
M_LINING, B_LINING = lining_material()

# anode: magnesium grey, pits grow (red glow) while it corrodes
def anode_material():
    m, nt, b = new_mat("Anode"); N, L = nt.nodes, nt.links
    b.inputs["Metallic"].default_value = 0.15; b.inputs["Roughness"].default_value = 0.6
    thr = [(0, 1.2), (T_COR0, 1.2), (T_COR1, 0.48), (T_DOWN1 - 0.01, 0.48), (T_DOWN1, 1.2),
           (T_A_PITS - 0.1, 1.2), (C["first"] + 0.3, 0.55), (T_A_SH1, 0.40), (T_RESET - 0.01, 0.40), (T_RESET, 1.2)]
    mk = mask_nodes(nt, 7.0, thr, "PITS")
    col = mix_rgb(nt, mk, (0.20, 0.21, 0.23), (0.50, 0.20, 0.08))
    L.new(col, b.inputs["Base Color"])
    em = N.new("ShaderNodeMath"); em.operation = "MULTIPLY"; L.new(mk, em.inputs[0])
    hl = N.new("ShaderNodeValue"); hl.name = "PITGLOW"
    keyval(hl.outputs[0], [(0, 2.5)])
    L.new(hl.outputs[0], em.inputs[1])
    # gold highlight pulse on "anode" adds to the pit glow
    gold = N.new("ShaderNodeValue"); gold.name = "GOLDPULSE"
    keyval(gold.outputs[0], [(0, 0.0)] + pulse(C["anode"] - 0.05, 0.9, hold=0.8))
    ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(em.outputs[0], ad.inputs[0]); L.new(gold.outputs[0], ad.inputs[1])
    ec = mix_rgb(nt, mk, GOLD, RED)
    L.new(ec, b.inputs["Emission Color"]); L.new(ad.outputs[0], b.inputs["Emission Strength"])
    return m
M_ANODE = anode_material()

# flame: blue at the base, orange at the tips (Generated Z), strength keyed with the burner state
def flame_material():
    m, nt, b = new_mat("Flame"); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    rp = N.new("ShaderNodeValToRGB"); e = rp.color_ramp.elements
    e[0].position = 0.1; e[0].color = (0.10, 0.30, 1.0, 1); e[1].position = 0.7; e[1].color = (1.0, 0.45, 0.08, 1)
    L.new(sep.outputs["Z"], rp.inputs[0])
    L.new(rp.outputs[0], b.inputs["Base Color"]); L.new(rp.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 3.5; b.inputs["Alpha"].default_value = 0.85
    return m
M_FLAME = flame_material()

# ================= geometry: lathe (half solids of revolution, y >= 0) =================
def lathe(name, prof, m_, a0=0.0, ang=math.pi, seg=48, loc=(0, 0, 0), smooth=True, link=True):
    bm = bmesh.new()
    vs = [bm.verts.new((r * math.cos(a0), r * math.sin(a0), z)) for r, z in prof]
    f = bm.faces.new(vs)
    bmesh.ops.spin(bm, geom=vs + list(f.edges) + [f], cent=(0, 0, 0), axis=(0, 0, 1), angle=ang, steps=seg, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, m_, link=link); o.location = loc
    if smooth:
        try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(40))
        except Exception: pass
    return o
def tube_prof(r0, r1, z0, z1): return [(r0, z0), (r1, z0), (r1, z1), (r0, z1)]
def full_cyl(name, r, x, y, z0, z1, m_, seg=32):
    return cyl(name, r, z1 - z0, "Z", (x, y, (z0 + z1) / 2), m_, seg=seg)

# ---- the heater (axis = world Z at x = y = 0) ----
R_J0, R_J1 = 2.55, 2.68          # jacket
R_T0, R_T1 = 2.20, 2.32          # steel tank
R_L = 2.15                       # glass lining inner face
R_F0, R_F1 = 0.42, 0.50          # flue
Z_TOP_T, Z_TOP_J = 12.25, 13.2
BOT_OUT = [(0.50, 1.66), (1.20, 1.58), (1.80, 1.43), (2.32, 1.18)]     # tank bottom head (domed up into the tank)
BOT_IN = [(r, z + 0.12) for r, z in BOT_OUT]
BOT_LIN = [(r, z + 0.17) for r, z in BOT_OUT]
JACKET_PROF = [(R_J0, 0.0), (R_J1, 0.0), (R_J1, Z_TOP_J), (0.62, Z_TOP_J), (0.62, Z_TOP_J - 0.12), (R_J0, Z_TOP_J - 0.12)]
jacket = lathe("Jacket", JACKET_PROF, M_JACKET)
foam = lathe("Foam", [(R_T1, 1.15), (R_J0, 1.15), (R_J0, Z_TOP_J - 0.12), (0.62, Z_TOP_J - 0.12), (0.62, Z_TOP_T), (R_T1, Z_TOP_T)], M_FOAM)
tank = lathe("TankSteel", BOT_OUT + [(R_T1, Z_TOP_T), (R_F1, Z_TOP_T), (R_F1, Z_TOP_T - 0.12), (R_T0, Z_TOP_T - 0.12)]
             + [(R_T0, BOT_IN[-1][1])] + BOT_IN[::-1][1:], M_STEEL)
LIN_TOP = Z_TOP_T - 0.17
lining = lathe("Lining", BOT_IN + [(R_T0, Z_TOP_T - 0.12), (R_F1, Z_TOP_T - 0.12), (R_F1, LIN_TOP), (R_L, LIN_TOP), (R_L, BOT_LIN[-1][1])]
               + BOT_LIN[::-1][1:], M_LINING)
WAT_BOT = [(r, z + 0.02) for r, z in BOT_LIN]
water = lathe("Water", WAT_BOT + [(R_L - 0.01, LIN_TOP - 0.02), (R_F1 + 0.01, LIN_TOP - 0.02)], M_WATER, smooth=False)
water.data.polygons.foreach_set("use_smooth", [False] * len(water.data.polygons))
chamber = lathe("ChamberFloor", [(0.01, 0.0), (R_J0, 0.0), (R_J0, 0.10), (0.01, 0.10)], M_DARK)
flue = lathe("Flue", tube_prof(R_F0, R_F1, 0.95, 14.05), M_FLUE)
flue_in = lathe("FlueInner", tube_prof(R_F0 - 0.01, R_F0, 0.95, 14.05), M_DARK, smooth=False)   # dark inside so the baffle reads
hood = lathe("DraftHood", [(0.95, 14.05), (1.08, 14.05), (1.08, 14.45), (0.70, 14.95), (0.70, 18.6), (0.62, 18.6), (0.62, 14.9), (0.95, 14.40)], M_JCUT)
legs = []
for k in range(3):
    a = math.radians(30 + 60 * k)
    bm = bmesh.new(); add_bar(bm, (0.9 * math.cos(a), 0.9 * math.sin(a), Z_TOP_J), (0.98 * math.cos(a), 0.98 * math.sin(a), 14.08), 0.06)
    legs.append(mesh_obj(f"HoodLeg{k}", bm, M_JCUT))
# twisted baffle in the flue (full ribbon: pokes out of the cut a little, reads as 3D)
def baffle():
    bm = bmesh.new(); n = 140; z0, z1 = 2.6, 13.6; w, th = 0.76, 0.035; rings = []
    for i in range(n + 1):
        z = z0 + (z1 - z0) * i / n; a = 1.35 * z
        d = Vector((math.cos(a), math.sin(a), 0)); nn = Vector((-math.sin(a), math.cos(a), 0))
        rings.append([bm.verts.new(Vector((0, 0, z)) + d * sx * w / 2 + nn * sy * th) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a_, b_ in zip(rings, rings[1:]):
        for k in range(4): bm.faces.new([a_[k], a_[(k + 1) % 4], b_[(k + 1) % 4], b_[k]])
    bm.faces.new(rings[0][::-1]); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj("Baffle", bm, M_BAFFLE)
BAF = baffle()
# burner + flames
burner = lathe("Burner", [(0.01, 0.30), (1.05, 0.30), (1.05, 0.50), (0.85, 0.58), (0.01, 0.58)], M_BURNER, ang=2 * math.pi, seg=48)
pipe_g = cyl("BurnerFeed", 0.09, 2.2, "X", (-1.6, 0.6, 0.42), M_BURNER)
FLAMES = []
FCONE = bpy.data.meshes.new("FlameMesh")
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.10, radius2=0.0, depth=0.5)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.25)); bm.to_mesh(FCONE); bm.free(); FCONE.materials.append(M_FLAME)
for k in range(18):
    a = 2 * math.pi * k / 18; rr = 0.78 if k % 2 == 0 else 0.55
    o = bpy.data.objects.new(f"Flame{k}", FCONE); CL.objects.link(o); o.location = (rr * math.cos(a), rr * math.sin(a), 0.56); FLAMES.append(o)
def flame_on(t):
    on = ease((t - T_FIRE) / 0.35)
    if T_E0 <= t < T_E1: on *= 1 - ease((t - T_E0) / 0.3)
    if t >= T_E1: on = ease((t - T_E1) / 0.4)
    return on
for k, o in enumerate(FLAMES):
    ph = random.uniform(0, 6.3)
    bake_fn(o, "scale", 2, lambda t, ph=ph: max(0.0, flame_on(t) * (1.0 + 0.22 * math.sin(17 * t + ph) + 0.12 * math.sin(29 * t + 2 * ph))))
    bake_fn(o, "scale", 0, lambda t: max(0.001, flame_on(t))); bake_fn(o, "scale", 1, lambda t: max(0.001, flame_on(t)))
flame_light = bpy.data.lights.new("FlameGlow", "POINT"); flame_light.color = (1.0, 0.55, 0.25); flame_light.shadow_soft_size = 0.6
flo = bpy.data.objects.new("FlameGlow", flame_light); scene.collection.objects.link(flo); flo.location = (0, -0.6, 0.9)
fl_fc = fcurve(flame_light, "energy", -1); fl_fc.keyframe_points.clear()
for t in [i * 0.2 for i in range(int(DUR / 0.2) + 1)]:
    flame_light.energy = 55 * flame_on(t); flame_light.keyframe_insert("energy", frame=F(t))
# cold inlet + dip tube (left), hot outlet (right): cut in half at the face so the flow inside reads
X_C, X_H = -1.50, 1.60
def half_tube(name, r0, r1, x, z0, z1, m_, ycut=-0.015):
    o = lathe(name, tube_prof(r0, r1, z0, z1), m_, a0=0.0, ang=math.pi, seg=24); o.location = (x, ycut, 0); return o
dip = half_tube("DipTube", 0.10, 0.14, X_C, 2.35, Z_TOP_T, M_DIP)
nip_c = half_tube("ColdNipple", 0.16, 0.21, X_C, Z_TOP_T - 0.1, Z_TOP_J + 0.02, M_COPPER)
nip_h = half_tube("HotNipple", 0.16, 0.21, X_H, LIN_TOP - 0.25, Z_TOP_J + 0.02, M_COPPER)
Z_PIPE = 15.6
for nm, x, band in (("Cold", X_C, M_BLUEB), ("Hot", X_H, M_REDB)):
    full_cyl(f"{nm}Riser", 0.21, x, 0.0, Z_TOP_J, Z_PIPE + 0.21, M_COPPER)
    full_cyl(f"{nm}Band", 0.245, x, 0.0, 14.1, 14.45, band)
    cyl(f"{nm}Run", 0.21, 4.7, "Y", (x, 2.35, Z_PIPE), M_COPPER)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.215)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(x, 0.0, Z_PIPE)); mesh_obj(f"{nm}Elbow", bm, M_COPPER)
# anode rod (full rod behind the cut, seen through the water); origin on its axis at z = 0
X_A, Y_A, R_A = 1.22, 0.62, 0.17
A_Z0, A_Z1 = 3.1, Z_TOP_T - 0.05
anode = cyl("Anode", R_A, A_Z1 - A_Z0, "Z", (0, 0, (A_Z0 + A_Z1) / 2), M_ANODE, seg=28); anode.location = (X_A, Y_A, 0)
core = cyl("AnodeCore", 0.035, A_Z1 - A_Z0 + 0.1, "Z", (0, 0, (A_Z0 + A_Z1) / 2), M_CORE, seg=10); core.location = (X_A, Y_A, 0)
hexh = cyl("AnodeHex", 0.27, 0.30, "Z", (0, 0, A_Z1 + 0.15), M_HEX, seg=6); hexh.location = (X_A, Y_A, 0)
LIFT = 5.6
def A_LIFT(t):
    if t < T_DOWN0: return LIFT * ease((t - T_LIFT0) / (T_LIFT1 - T_LIFT0))
    return LIFT * (1 - ease((t - T_DOWN0) / (T_DOWN1 - T_DOWN0)))
def A_RAD(t):
    if t < T_DOWN1: return 1.0 - 0.28 * ease((t - T_COR0) / (T_COR1 - T_COR0))
    if t < T_RESET:
        r = 1.0 - 0.45 * ease((t - T_A_SH0) / (T_A_SH1 - T_A_SH0))
        return r * (1 - ease((t - T_A_GONE0) / (T_A_GONE1 - T_A_GONE0))) + 0.001
    return 1.0
for o in (anode, core, hexh): bake_fn(o, "location", 2, A_LIFT)
bake_fn(anode, "scale", 0, A_RAD); bake_fn(anode, "scale", 1, A_RAD)
# electric elements (only for the electric line): two hairpins from the left wall
ELEMS = []
for nm, z in (("Upper", 9.6), ("Lower", 3.7)):
    bm = bmesh.new()
    for dz in (-0.11, 0.11): add_cyl(bm, 0.075, 1.55, "X", (-1.43, 0.35, z + dz), seg=12)
    r_ = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=6, radius=0.14)
    bmesh.ops.scale(bm, verts=r_["verts"], vec=(0.6, 1.0, 1.4)); bmesh.ops.translate(bm, verts=r_["verts"], vec=(-0.655, 0.35, z))
    add_cyl(bm, 0.24, 0.35, "X", (-2.25, 0.35, z), seg=6)
    ELEMS.append(mesh_obj(f"Element{nm}", bm, M_ELEM))
for o in ELEMS: windows(o, [(T_E0, T_E1 + 0.05)])
glow(B_ELEM, [(0, 0.0), (T_E0 + 0.2, 0.0), (T_E0 + 0.7, 10.0), (T_E1, 10.0)])
# T&P relief valve (top right) + discharge pipe; drain valve (bottom left); gas control (left)
Z_TP = 11.55
tp_body = cyl("TPBody", 0.2, 0.62, "X", (R_J1 + 0.31, 0.25, Z_TP), M_BRASS)
tp_probe = cyl("TPProbe", 0.06, 1.0, "X", (R_T0 - 0.15, 0.25, Z_TP), M_BRASS)
tp_cap = cyl("TPCap", 0.15, 0.4, "Z", (R_J1 + 0.38, 0.25, Z_TP + 0.38), M_BRASS)
TP_PIV = empty("TPPivot", (R_J1 + 0.38, 0.0, Z_TP + 0.6))
bm = bmesh.new(); add_box(bm, -0.05, 0.75, -0.04, 0.04, -0.03, 0.06); tp_lever = mesh_obj("TPLever", bm, M_BRASS, TP_PIV)
bake_fn(TP_PIV, "rotation_euler", 1, PW([(0, 0.0), (T_TP0, 0.0), (T_TP0 + 0.3, math.radians(-55)), (T_TP1 - 0.3, math.radians(-55)), (T_TP1, 0.0)]))
X_D = R_J1 + 0.75
dis = []
dis.append(cyl("Discharge1", 0.14, 0.5, "X", (X_D - 0.25, 0.25, Z_TP), M_COPPER))
dis.append(cyl("Discharge2", 0.14, Z_TP - 0.9, "Z", (X_D, 0.25, (Z_TP + 0.9) / 2), M_COPPER))
X_DR = -(R_J1 + 0.3)
drain = cyl("DrainValve", 0.16, 0.65, "X", (X_DR, 0.3, 1.45), M_BRASS)
drain_sp = cyl("DrainSpout", 0.11, 0.45, "Z", (X_DR - 0.2, 0.3, 1.15), M_BRASS)
drain_k = cyl("DrainKnob", 0.18, 0.08, "Y", (X_DR + 0.05, 0.02, 1.45), M_KNOB)
gas_box = box("GasControl", -R_J1 - 0.65, -R_J1, 0.0, 0.75, 2.25, 3.05, M_PANEL)
gas_knob = cyl("GasKnob", 0.17, 0.12, "Y", (-R_J1 - 0.33, -0.06, 2.75), M_KNOB)
gas_pipe = cyl("GasPipe", 0.08, 2.2, "Z", (-R_J1 - 0.33, 0.4, 1.15), M_BURNER)
# sediment layer: shape key thin -> full on the inner bottom
def sediment():
    full = WAT_BOT[:]  # (r, z) along the bottom
    lo = [(r, z + 0.005) for r, z in full]; lo[-1] = (R_L - 0.01, lo[-1][1])
    def prof(th): return lo + [(R_L - 0.01, lo[-1][1] + th), ] + [(r, z + th) for r, z in lo[::-1][1:]]
    o = lathe("Sediment", prof(0.012), M_SED, smooth=False)
    o2 = lathe("SedFull", prof(0.48), M_SED, smooth=False, link=False)
    o.shape_key_add(name="Basis"); sk = o.shape_key_add(name="Full")
    for i, v in enumerate(o2.data.vertices): sk.data[i].co = v.co
    bpy.data.objects.remove(o2)
    return o, sk
sed, SK = sediment()
for t, v in [(0, 0.0), (T_SED0, 0.0), (T_SED1 + 0.6, 1.0), (T_FL0 + 0.2, 1.0), (T_FL1, 0.0)]:
    SK.value = v; SK.keyframe_insert("value", frame=F(t))
windows(sed, [(T_SED0 - 0.1, T_FL1 + 0.1)])
# floor + wall
floor = box("Floor", -40, 40, -40, 7, -0.6, 0.0, M_FLOOR)
wall = box("Wall", -40, 40, 4.6, 5.2, -0.6, 45, M_WALL)
# heat arrows from the flue (on "heat soaks in")
HARROWS = []
for k, (sx, z) in enumerate([(-1, 4.0), (1, 5.5), (-1, 7.0), (1, 8.5), (-1, 10.0), (1, 3.0)]):
    bm = bmesh.new(); add_arrow(bm, (0, 0), (sx, 0.0), 0.95, 0.42, y=0.0)
    o = mesh_obj(f"HeatArrow{k}", bm, M_ARROW); o.location = (sx * 0.62, -0.12, z)
    t0 = C["heat"] + 0.07 * k
    bake_fn(o, "scale", 0, lambda t, t0=t0: max(0.001, pop(t, t0) * (1 - ease((t - T_E0 + 0.25) / 0.25))))
    bake_fn(o, "scale", 2, lambda t, t0=t0: max(0.001, pop(t, t0) * (1 - ease((t - T_E0 + 0.25) / 0.25))))
    bake_fn(o, "location", 0, lambda t, sx=sx, t0=t0: sx * (0.62 + 0.25 * ((t - t0) % 0.8) / 0.8) if t > t0 else sx * 0.62)
    windows(o, [(t0 - 0.02, T_E0)])
    HARROWS.append(o)
# highlight pulses for the layer callouts
glow(B_STEEL, [(0, 0.0)] + pulse(C["steel"] - 0.05, 2.5, hold=0.6))
glow(B_LINING, [(0, 0.0)] + pulse(C["glass"] - 0.05, 2.0, hold=0.6) + pulse(C["doesnt"] - 0.3, 1.4, hold=0.6))
glow(B_FOAM, [(0, 0.0)] + pulse(C["foam"] - 0.05, 1.6, hold=0.6))
glow(B_DIP, [(0, 0.0)] + pulse(C["dip"] - 0.05, 2.5, hold=0.8))
glow(B_FLUE, [(0, 0.0), (C["climbs"], 0.0), (C["climbs"] + 0.6, 1.2), (T_E0, 1.2), (T_E0 + 0.3, 0.0), (C["have"], 0.0), (C["have"] + 0.6, 0.8)])
glow(B_BAFFLE, [(0, 0.0)] + pulse(C["baffle"] - 0.05, 2.0, hold=0.9))
glow(B_SED, [(0, 0.0)] + pulse(C["sediment"] + 0.9, 0.6, hold=0.7))
glow(B_BRASS, [(0, 0.0)] + pulse(C["safety"] - 0.05, 2.2, hold=0.9))

# ================= hook cover: the front half slides off on "cut" =================
cover = [lathe("CoverJacket", JACKET_PROF, M_JACKET, a0=math.pi, ang=math.pi)]
cover.append(lathe("CoverHood", [(0.95, 14.05), (1.08, 14.05), (1.08, 14.45), (0.70, 14.95), (0.70, 18.6), (0.62, 18.6), (0.62, 14.9), (0.95, 14.40)],
                   M_JCUT, a0=math.pi, ang=math.pi))
cover.append(lathe("CoverFlue", tube_prof(R_F0, R_F1, Z_TOP_J, 14.05), M_FLUE, a0=math.pi, ang=math.pi))
cover.append(box("AccessPanel", -0.75, 0.75, -R_J1 - 0.04, -R_J1 + 0.15, 0.25, 1.05, M_PANEL))
cover.append(box("RatingPlate", -0.65, 0.65, -R_J1 - 0.03, -R_J1 + 0.1, 6.6, 8.4, M_HEX))
for k, sx in enumerate((-1, 1)):
    bm = bmesh.new(); add_bar(bm, (sx * 0.9 * math.cos(math.radians(30)), -0.9 * math.sin(math.radians(30)), Z_TOP_J),
                              (sx * 0.98 * math.cos(math.radians(30)), -0.98 * math.sin(math.radians(30)), 14.08), 0.06)
    cover.append(mesh_obj(f"CoverLeg{k}", bm, M_JCUT))
for o in cover:
    bake_fn(o, "location", 1, PW([(0, 0.0), (T_CV0, 0.0), (T_CV1, -16.0)]))
    bake_fn(o, "location", 2, PW([(0, 0.0), (T_CV0 + 0.1, 0.0), (T_CV1, -2.0)]))
    windows(o, [(0, T_CV1 + 0.05)])

# ================= flow: baked drops along paths =================
SPH = bpy.data.meshes.new("DropMesh")
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(SPH); bm.free()
for poly in SPH.polygons: poly.use_smooth = True
SPH.materials.append(M_DROPC)
def path_fn(pts3):
    P = [Vector(p) for p in pts3]; seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]; tot = sum(seg)
    def at(u):
        d = max(0.0, min(1.0, u)) * tot
        for i, s in enumerate(seg):
            if d <= s or i == len(seg) - 1: return P[i].lerp(P[i + 1], d / s if s else 0)
            d -= s
    return at, tot
_drop_n = [0]
YP = 0.05
def stream(name, pts, t0, t1, n, speed, rad, m_=None, y=YP, jitter=0.12, wobble=0.0, jy=None):
    """n drops released evenly between t0 and t1 - travel; each one runs the whole path at `speed` units/s. pts: (x, z) or (x, y, z)."""
    P3 = [p if len(p) == 3 else (p[0], y, p[1]) for p in pts]
    at, tot = path_fn(P3); travel = tot / speed
    span = max(0.05, (t1 - t0) - travel)
    for k in range(n):
        tk = t0 + span * k / max(1, n - 1)
        o = bpy.data.objects.new(f"{name}{k}", SPH); CL.objects.link(o)
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m_ or M_DROPC
        jx, jz = random.uniform(-jitter, jitter), random.uniform(-jitter, jitter)
        jyy = random.uniform(-jitter, jitter) * 0.3 if jy is None else random.uniform(0, jy)
        ph = random.uniform(0, 6.28)
        loc = [[], [], []]; sc = []
        for t in TS:
            u = (t - tk) / travel
            p = at(u) + Vector((jx, jyy, jz)) + Vector((wobble * math.sin(9 * t + ph), 0, wobble * math.cos(7 * t + ph)))
            for ax in range(3): loc[ax].append(p[ax])
            s = rad if 0.0 <= u <= 1.0 else 0.0
            if 0 <= u < 0.06: s = rad * u / 0.06
            if 0.94 < u <= 1: s = rad * (1 - u) / 0.06
            sc.append(s)
        for ax in range(3): bake(o, "location", ax, loc[ax]); bake(o, "scale", ax, sc)
        _drop_n[0] += 1
def spiral(z0, z1, r, turns, x0=0.0, n=60):
    return [(x0 + r * math.cos(2 * math.pi * turns * i / n), -0.15 + r * math.sin(2 * math.pi * turns * i / n) * 0.6, z0 + (z1 - z0) * i / n) for i in range(n + 1)]
# hook: flakes fall off the corroding rod (outside, above the closed heater)
for k in range(2):
    stream(f"FlakeHook{k}_", [(X_A + 0.15 - 0.3 * k, Y_A - 0.2, Z_TOP_J + 4.5), (X_A + 0.2 - 0.4 * k, Y_A - 0.2, Z_TOP_J + 0.1)],
           T_COR0 + 0.1 * k, T_DOWN0 + 0.2, 9, 3.0, 0.07, M_FLAKE, jitter=0.6)
# cold water in: down the cold pipe, inside the dip tube, out at the bottom
COLD_PATH = [(X_C, 0.06, Z_PIPE + 0.1), (X_C, 0.06, 2.5), (X_C + 0.1, 0.06, 2.05), (X_C + 0.8, 0.06, 1.95), (X_C + 1.0, 0.06, 2.6)]
stream("ColdIn", COLD_PATH, C["cold"] - 0.1, C["under"] + 0.3, 26, 4.2, 0.085, M_DROPC, jitter=0.04)
# exhaust: burner -> under the dome -> up the flue around the baffle -> out of the vent
EXH = [(0.0, -0.2, 0.62), (0.0, -0.15, 1.0)] + spiral(1.2, 13.8, 0.22, 6) + [(0.0, 0.0, 14.6), (0.0, 0.0, 18.8)]
stream("Exhaust", EXH, C["exhaust"] - 0.4, T_E0 + 0.3, 46, 4.8, 0.12, M_EXH, jitter=0.06, wobble=0.04)
stream("ExhaustEnd", EXH, C["have"] - 0.5, DUR + 3.0, 22, 4.8, 0.12, M_EXH, jitter=0.06, wobble=0.04)
# convection: warm blobs rise from the bottom, spread under the top
for k, x0 in enumerate((-1.0, 1.4, -1.8, 0.9)):
    stream(f"Rise{k}_", [(x0, 0.08, 2.2), (x0 * 0.9, 0.08, 6.5), (x0 * 0.8, 0.08, 10.8), (x0 * 0.8 + (0.5 if x0 > 0 else -0.5), 0.08, 11.6)],
           C["hotw"] - 0.2 + 0.15 * k, C["pipe2"] + 0.3, 9, 3.6, 0.10, M_DROPH, jitter=0.18, wobble=0.05)
# hot water out: top of the tank -> hot nipple -> hot riser -> run to the wall
HOT_PATH = [(X_H - 0.4, 0.06, 11.1), (X_H, 0.06, LIN_TOP - 0.2), (X_H, 0.06, Z_PIPE), (X_H, 4.4, Z_PIPE)]
stream("HotOut", HOT_PATH, C["pulls"] - 0.25, C["always"] + 0.4, 30, 4.0, 0.085, M_DROPH, jitter=0.04)
stream("ColdIn2_", COLD_PATH, C["cold2"] - 0.3, C["always"] + 0.8, 22, 4.5, 0.085, M_DROPC, jitter=0.04)
# anode flakes inside the water while it corrodes
stream("FlakeIn", [(X_A, Y_A - 0.25, 10.5), (X_A - 0.1, Y_A - 0.25, 2.2)], C["corrodes"] - 0.2, T_A_GONE1, 26, 2.2, 0.06, M_FLAKE, jitter=0.4)
# sediment: grains settle; trapped water pops; flushing washes it out of the drain valve
for k in range(4):
    x0 = -1.8 + 0.95 * k
    stream(f"Grain{k}_", [(x0, 0.1, 9.0 - k), (x0 + 0.1, 0.1, 2.0 - 0.1 * abs(x0))], T_SED0 - 0.2 + 0.1 * k, T_SED1 + 0.4, 12, 6.0, 0.06, M_GRAIN, jitter=0.35)
for k in range(10):
    x0 = -1.9 + 0.36 * k + random.uniform(-0.1, 0.1); zb = 1.9 + (0.25 if abs(x0) < 1.2 else 0.0)
    stream(f"Pop{k}_", [(x0, 0.08, zb), (x0, 0.08, zb + 0.75)], C["pops"] - 0.3 + 0.07 * k, C["flushing"] - 0.1, 4, 2.2, 0.08, M_BUB, jitter=0.06)
FLUSH_PATH = [(-0.8, 0.1, 2.3), (-2.0, 0.15, 1.65), (X_DR - 0.05, 0.3, 1.45), (X_DR - 0.2, 0.3, 0.95), (X_DR - 0.2, 0.3, 0.05), (X_DR - 1.6, 0.0, 0.02)]
stream("FlushW", FLUSH_PATH, T_FL0 - 0.05, T_FL1 + 0.6, 30, 4.5, 0.085, M_DROPC, jitter=0.06)
stream("FlushG", FLUSH_PATH, T_FL0 + 0.05, T_FL1 + 0.5, 24, 4.5, 0.06, M_GRAIN, jitter=0.08)
# T&P opens: steam/water down the discharge pipe and out on the floor
TP_PATH = [(R_T0 - 0.4, 0.25, Z_TP + 0.05), (X_D, 0.25, Z_TP), (X_D, 0.25, 0.95), (X_D, 0.25, 0.05), (X_D + 1.6, 0.0, 0.05)]
stream("TPWater", TP_PATH, T_TP0 + 0.1, T_TP1, 30, 6.0, 0.085, M_STEAM, jitter=0.05)
stream("TPSteam", [(X_D, 0.0, 0.7), (X_D + 0.3, -0.4, 2.6)], T_TP0 + 1.8, T_TP1 + 0.4, 16, 1.4, 0.17, M_STEAM, jitter=0.25, wobble=0.08)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 400
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-2.5, -13.5, 17.5), (0.9, 0.0, 15.4), 32),
    (C["lets"] - 0.3, (-1.5, -11.5, 17.6), (1.0, 0.0, 15.6), 32),
    (C["lets"] - 0.25, (7.0, -24.0, 11.5), (0.2, 0.0, 9.0), 30, "cut"),
    (C["steel"] - 0.25, (3.0, -22.0, 10.0), (0.2, 0.0, 8.8), 30),
    (C["steel"] - 0.2, (3.6, -6.2, 12.6), (1.8, 0.0, 11.4), 35, "cut"),
    (C["cold"] - 0.25, (3.2, -5.6, 12.4), (1.9, 0.0, 11.3), 35),
    (C["cold"] - 0.2, (-0.8, -10.0, 15.0), (-1.2, 0.0, 12.8), 32, "cut"),
    (C["dip"] - 0.1, (-0.8, -10.5, 13.6), (-1.3, 0.0, 11.6), 32),
    (C["bottom"] + 0.2, (-0.6, -11.0, 5.0), (-1.0, 0.0, 3.2), 32),
    (C["under"] - 0.2, (-0.6, -11.0, 4.6), (-1.0, 0.0, 3.0), 32),
    (C["under"] - 0.15, (1.5, -8.5, 2.6), (0.0, 0.0, 1.2), 30, "cut"),
    (C["exhaust"] - 0.3, (1.2, -8.0, 2.5), (0.0, 0.0, 1.3), 30),
    (C["exhaust"] - 0.25, (2.0, -25.0, 10.0), (0.0, 0.0, 9.0), 30, "cut"),
    (C["baffle"] - 0.25, (1.0, -23.0, 10.0), (0.0, 0.0, 9.0), 30),
    (C["baffle"] - 0.2, (1.8, -8.0, 9.6), (0.0, 0.0, 8.6), 33, "cut"),
    (C["heat"] - 0.1, (1.2, -10.0, 9.2), (0.0, 0.0, 8.0), 33),
    (C["electric"] - 0.15, (1.0, -11.0, 9.0), (0.0, 0.0, 7.8), 33),
    (C["electric"] - 0.1, (-6.0, -22.0, 10.0), (-0.5, 0.0, 7.6), 30, "cut"),
    (C["hotw"] - 0.15, (-4.0, -21.0, 10.0), (-0.5, 0.0, 7.6), 30),
    (C["hotw"] - 0.1, (0.5, -24.0, 9.5), (0.0, 0.0, 8.0), 30, "cut"),
    (C["hottest"] - 0.2, (0.5, -22.0, 10.0), (0.0, 0.0, 8.6), 30),
    (C["hottest"] - 0.15, (2.6, -11.0, 13.5), (1.0, 0.0, 12.0), 32, "cut"),
    (C["open2"] - 0.2, (2.2, -10.0, 13.6), (1.2, 0.0, 12.4), 32),
    (C["open2"] - 0.15, (-1.0, -27.0, 10.5), (0.0, 0.0, 9.0), 30, "cut"),
    (C["now"] - 0.2, (0.5, -25.5, 10.0), (0.0, 0.0, 8.6), 30),
    (C["now"] - 0.15, (2.4, -7.0, 10.6), (X_A, Y_A, 9.6), 35, "cut"),
    (C["eats"] - 0.2, (2.2, -6.5, 9.0), (X_A, Y_A, 8.2), 35),
    (C["corrodes"] - 0.2, (2.0, -6.5, 7.6), (X_A, Y_A, 7.2), 35),
    (C["corrodes"] - 0.15, (2.6, -13.0, 9.0), (0.8, 0.3, 7.4), 32, "cut"),
    (C["rust"] - 0.25, (1.2, -14.5, 8.6), (0.6, 0.3, 7.2), 32),
    (C["sediment"] - 0.15, (-0.9, -7.0, 3.0), (-0.9, 0.0, 1.9), 32, "cut"),
    (C["flushing"] - 0.2, (-0.7, -7.4, 2.8), (-0.9, 0.0, 1.9), 32),
    (C["flushing"] - 0.15, (-4.0, -9.0, 3.0), (-2.4, 0.0, 1.3), 32, "cut"),
    (C["up"] - 0.25, (-4.2, -8.6, 2.8), (-2.5, 0.0, 1.2), 32),
    (C["up"] - 0.2, (5.4, -9.0, 12.4), (2.9, 0.0, 11.3), 32, "cut"),
    (C["hundred"] - 0.2, (5.0, -8.0, 12.0), (3.0, 0.0, 11.0), 32),
    (C["two"] - 0.2, (5.2, -12.0, 8.6), (2.4, 0.0, 7.0), 30, "cut"),
    (C["have"] - 0.25, (5.0, -12.6, 7.8), (2.4, 0.0, 6.2), 30),
    (C["have"] - 0.2, (-8.5, -16.0, 11.5), (0.0, 0.0, 8.6), 30, "cut"),
    (C["end"], (7.5, -16.5, 11.0), (0.0, 0.0, 8.6), 30),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
def shake(t):
    a = ease((t - C["pops"] + 0.1) / 0.2) * (1 - ease((t - C["flushing"] + 0.3) / 0.3))
    return Vector((0.05 * a * math.sin(t * 61), 0.0, 0.04 * a * math.sin(t * 47 + 1)))
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    sh = shake(t)
    cam_loc.append(l0 + sh + Vector((0.03 * math.sin(t * 0.7), 0.0, 0.02 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0 + sh); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()
# ================= world + lights: dark studio =================
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
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.25
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
sun = bpy.data.lights.new("Key", "SUN"); sun.energy = 2.0; sun.color = (1.0, 0.93, 0.82); sun.angle = math.radians(5)
so = bpy.data.objects.new("Key", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(10), math.radians(-28))
sun2 = bpy.data.lights.new("Fill", "SUN"); sun2.energy = 0.7; sun2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("Fill", sun2); scene.collection.objects.link(so2); so2.rotation_euler = (math.radians(75), math.radians(-10), math.radians(150))
LT_A = target("LT_Face", (0.0, 0.0, 8.0)); area("Face", (-3.0, -28.0, 14.0), 18.0, 3000, (1.0, 0.96, 0.9), LT_A)
area("Top", (1.0, -4.0, 26.0), 8.0, 900, (1.0, 0.95, 0.88), LT_A)
area("Low", (5.0, -14.0, 1.0), 8.0, 500, (0.8, 0.88, 1.0), target("LT_Low", (0.0, 0.0, 1.5)))
area("CamFill", (0, 0, 0), 3.0, 60, (1.0, 0.96, 0.9), TGT).parent = cam

# ================= render settings =================
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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4; scene.cycles.transparent_max_bounces = 16
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

# ================= export cues, events and projected anchors for the typography =================
ANCH = {
    "rod_hook": lambda t: Vector((X_A, Y_A - 0.2, Z_TOP_J + 0.4 * LIFT * min(1, A_LIFT(t) / LIFT) + 1.6)),
    "jacket": lambda t: Vector(((R_J0 + R_J1) / 2, -0.05, 10.6)),
    "foam": lambda t: Vector((1.6, -0.05, (Z_TOP_T + Z_TOP_J) / 2)),
    "steel": lambda t: Vector(((R_T0 + R_T1) / 2, -0.05, 10.8)),
    "lining": lambda t: Vector((R_L + 0.02, -0.05, 10.0)),
    "cold_in": lambda t: Vector((X_C, -0.1, 14.6)),
    "dip": lambda t: Vector((X_C, -0.05, 11.0 - 7.0 * ease((t - C["dip"]) / (C["bottom"] + 0.2 - C["dip"])))),
    "burner": lambda t: Vector((0.9, -0.5, 0.45)),
    "flue": lambda t: Vector((R_F1, -0.05, 10.5)),
    "baffle": lambda t: Vector((0.0, -0.3, 8.6)),
    "elem_up": lambda t: Vector((-1.2, 0.35, 9.6)),
    "elem_lo": lambda t: Vector((-1.2, 0.35, 3.7)),
    "hot_out": lambda t: Vector((X_H, -0.1, 14.6)),
    "anode": lambda t: Vector((X_A, Y_A - R_A, 8.0 + A_LIFT(t))),
    "sediment": lambda t: Vector((-1.4, -0.05, 1.95)),
    "drain": lambda t: Vector((X_DR - 0.3, 0.1, 1.45)),
    "tp": lambda t: Vector((R_J1 + 0.4, 0.1, Z_TP + 0.2)),
    "discharge": lambda t: Vector((X_D, 0.1, 2.5)),
}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"lift": [round(T_LIFT0, 3), round(T_LIFT1, 3)], "corrode_hook": [round(T_COR0, 3), round(T_COR1, 3)], "rod_down": [round(T_DOWN0, 3), round(T_DOWN1, 3)],
          "cover": [round(T_CV0, 3), round(T_CV1, 3)], "fire": round(T_FIRE, 3), "electric": [round(T_E0, 3), round(T_E1, 3)],
          "shrink": [round(T_A_SH0, 3), round(T_A_SH1, 3)], "gone": [round(T_A_GONE0, 3), round(T_A_GONE1, 3)], "rust": [round(T_RUST0, 3), round(T_RUST1, 3)],
          "reset": round(T_RESET, 3), "settle": [round(T_SED0, 3), round(T_SED1, 3)], "flush": [round(T_FL0, 3), round(T_FL1, 3)],
          "tp": [round(T_TP0, 3), round(T_TP1, 3)], "drops": _drop_n[0]}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS", events, "DUR", DUR, "FRAMES", FRAMES)

save = arg("--save")
if save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))
out = arg("--out", os.path.join(HERE, "checks"))
if not os.path.isabs(out): out = os.path.join(HERE, out)
if "--stills" in ARGS:
    os.makedirs(out, exist_ok=True)
    r.resolution_percentage = int(arg("--pct", "25"))
    import time
    for fr in [int(x) for x in arg("--stills").split(",")]:
        scene.frame_set(fr); r.filepath = os.path.join(out, f"still_{fr:04d}.png")
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("STILL", fr, round(time.time() - t0, 1))
if "--anim" in ARGS:
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
