# Toilet-Flush-3D: how a toilet flush really works (siphon). Studio cutaway in Blender Cycles. Every cue is a word in the VO.
# One set: a gravity-flush toilet sectioned through its centre line (porcelain extruded from a side profile: bowl, rim channels, siphon jet,
#   trapway, tank) standing on a cut floor slab next to a cut wall, with the drain pipe below the floor.
#   Tank parts are real 3D pieces behind the cut: handle + lever, chain, flapper on the flush valve, overflow tube, fill valve, float cup, refill tube.
#   Water levels are driven by empties (material threshold on z), water flow = baked drops along paths, a full trapway = its own water body.
# A front cover (the uncut front half) is in place for the hook and slides away on "cut".
# No people anywhere. Sizes are illustrative (1 unit = 10 cm, not to scale); only "one point six gallons" is spoken.
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

CUES = [("your", "your"), ("toilet", "toilet"), ("push", "push"), ("sucks", "sucks"), ("cut", "cut"), ("open", "open"), ("hidden", "hidden"),
        ("base", "base"), ("bent", "bent"), ("pipe", "pipe"), ("trapway", "trapway"), ("climbs", "climbs"), ("drops", "drops"), ("drain", "drain"),
        ("water", "water"), ("bowl", "bowl"), ("high", "high"), ("top", "top"), ("bend", "bend"), ("add", "add"), ("spills", "spills"),
        ("thats", "that's"), ("level", "level"), ("never", "never"), ("changes", "changes"), ("that", "that"), ("blocks", "blocks"),
        ("sewer", "sewer"), ("gas", "gas"), ("now", "now"), ("press", "press"), ("handle", "handle"), ("chain", "chain"), ("lifts", "lifts"),
        ("flap", "flap"), ("flapper", "flapper"), ("tank", "tank"), ("dumps", "dumps"), ("once", "once"), ("rushes", "rushes"), ("holes", "holes"),
        ("rim", "rim"), ("jet", "jet"), ("bottom", "bottom"), ("bend2", "bend"), ("fills", "fills"), ("completely", "completely"),
        ("trick", "trick"), ("falling", "falling"), ("drain2", "drain"), ("pulls", "pulls"), ("bowl2", "bowl"), ("siphon", "siphon"),
        ("keeps", "keeps"), ("air", "air"), ("pipe2", "pipe"), ("gurgle", "gurgle"), ("end_", "end"), ("then", "then"), ("flapper2", "flapper"),
        ("drops2", "drops"), ("seals", "seals"), ("float", "float"), ("falls", "falls"), ("opens", "opens"), ("fill", "fill"), ("valve", "valve"),
        ("small", "small"), ("tube", "tube"), ("refills", "refills"), ("bowl3", "bowl"), ("seal", "seal"), ("back", "back"), ("as", "as"),
        ("float2", "float"), ("rises", "rises"), ("shuts", "shuts"), ("off", "off"), ("if", "if"), ("fails", "fails"), ("overflow", "overflow"),
        ("tube2", "tube"), ("extra", "extra"), ("bowl4", "bowl"), ("not", "not"), ("floor", "floor"), ("in", "in"), ("us", "us"),
        ("new", "new"), ("one", "one"), ("six", "six"), ("gallons", "gallons"), ("flush", "flush"), ("have", "have"), ("bucket", "bucket"),
        ("tell", "tell"), ("comments", "comments"), ("next", "next"), ("dam", "dam"), ("follow", "follow")]
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
CL = coll("Toilet")

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


# ================= palette + materials =================
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
M_PORC, B_PORC = mat("Porcelain", (0.86, 0.87, 0.89), 0.14, 0.0, GOLD)
M_PORC_CUT, _ = mat("PorcelainCut", (0.80, 0.80, 0.80), 0.55, 0.0, GOLD, 40)
M_SEAT, _ = mat("Seat", (0.93, 0.93, 0.94), 0.3)
M_CHROME, _ = mat("Chrome", (0.85, 0.87, 0.9), 0.12, 1.0)
M_PLASTIC_D, _ = mat("PlasticDark", (0.06, 0.065, 0.075), 0.45)
M_PLASTIC_W, _ = mat("PlasticWhite", (0.78, 0.80, 0.82), 0.4)
M_RUBBER, B_RUBBER = mat("Flapper", (0.55, 0.12, 0.08), 0.6, 0.0, GOLD)
M_FLOAT, B_FLOAT = mat("FloatCup", (0.20, 0.22, 0.26), 0.45, 0.0, GOLD)
M_FILLV, B_FILLV = mat("FillValve", (0.30, 0.32, 0.36), 0.4, 0.0, GOLD)
M_OVER, B_OVER = mat("OverflowTube", (0.70, 0.72, 0.76), 0.35, 0.0, GOLD)
M_HOSE, B_HOSE = mat("RefillHose", (0.10, 0.10, 0.11), 0.5, 0.0, GOLD)
M_PVC, _ = mat("PVC", (0.82, 0.82, 0.80), 0.4)
M_PVC_IN, _ = mat("PVCInner", (0.25, 0.25, 0.26), 0.7)
M_PED, _ = mat("Pedestal", (0.05, 0.055, 0.065), 0.6, 0.2)
M_TRACE, B_TRACE = mat("TracerCyan", CYAN, 0.5, 0.0, CYAN); B_TRACE.inputs["Emission Strength"].default_value = 6.0
M_LINE, B_LINE = mat("LevelLine", CYAN, 0.5, 0.0, CYAN); B_LINE.inputs["Emission Strength"].default_value = 6.0
M_REDBAR, B_REDBAR = mat("RedBar", RED, 0.5, 0.0, RED); B_REDBAR.inputs["Emission Strength"].default_value = 6.0
M_GAS, B_GAS = mat("SewerGas", (0.45, 0.55, 0.15), 0.6, 0.0, (0.55, 0.75, 0.15), 0, 0.75); B_GAS.inputs["Emission Strength"].default_value = 1.6
M_DROP, B_DROP = mat("WaterDrop", (0.30, 0.65, 1.0), 0.05, 0.0, (0.30, 0.65, 1.0)); B_DROP.inputs["Emission Strength"].default_value = 1.6
M_AIR, B_AIR = mat("AirBubble", (0.9, 0.95, 1.0), 0.1, 0.0, (0.9, 0.95, 1.0), 0, 0.85); B_AIR.inputs["Emission Strength"].default_value = 1.2
M_ARROW, B_ARROW = mat("ArrowCyan", CYAN, 0.5, 0.0, CYAN); B_ARROW.inputs["Emission Strength"].default_value = 5.0
M_ARROWR, B_ARROWR = mat("ArrowRed", RED, 0.5, 0.0, RED); B_ARROWR.inputs["Emission Strength"].default_value = 5.0

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
M_FLOOR = tiles("FloorTile", (0.42, 0.40, 0.37), (0.38, 0.36, 0.34), 0.35, "XY")
M_WALL = tiles("WallTile", (0.30, 0.42, 0.46), (0.28, 0.40, 0.44), 0.45, "XZ")
M_SLABCUT, _ = mat("SlabCut", (0.36, 0.34, 0.32), 0.9, 0.0, GOLD, 18)

def level_water(name, level_obj, rgb=(0.16, 0.48, 0.88), alpha=0.62, flow_obj=None):
    """Water that exists only below the z of level_obj (an empty). Emission keyable for highlight pulses."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.04
    b.inputs["Alpha"].default_value = alpha
    b.inputs["Emission Color"].default_value = (rgb[0] * 1.2, rgb[1] * 1.2, min(1, rgb[2] * 1.2), 1); b.inputs["Emission Strength"].default_value = 0.35
    if flow_obj is not None:   # moving streaks so a full pipe reads as flowing
        tcf = N.new("ShaderNodeTexCoord"); tcf.object = flow_obj
        wv = N.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 1.6; wv.inputs["Distortion"].default_value = 4.0
        L.new(tcf.outputs["Object"], wv.inputs["Vector"])
        mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 0.2; mr.inputs[4].default_value = 1.1; L.new(wv.outputs["Fac"], mr.inputs[0])
        L.new(mr.outputs[0], b.inputs["Emission Strength"])
    tc = N.new("ShaderNodeTexCoord"); tc.object = level_obj
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.0; L.new(sep.outputs["Z"], gt.inputs[0])
    tr = N.new("ShaderNodeBsdfTransparent"); mix = N.new("ShaderNodeMixShader")
    L.new(gt.outputs[0], mix.inputs[0]); L.new(b.outputs[0], mix.inputs[1]); L.new(tr.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs["Surface"])
    return m, b

# ================= 2D profile helpers (x = front->back, z = up; cut face at y = 0, the toilet extends to +y) =================
def catmull(pts, closed=False, n=6):
    P = [Vector((p[0], p[1])) for p in pts]
    out = []; m = len(P)
    rng_ = range(m) if closed else range(m - 1)
    for i in rng_:
        p0 = P[(i - 1) % m] if closed else P[max(i - 1, 0)]; p1 = P[i]; p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        if (p2 - p1).length < 1e-6: continue                      # duplicated point = sharp corner
        if (p1 - p0).length < 1e-6: p0 = p1 - (p2 - p1)            # no overshoot next to a corner
        if (p3 - p2).length < 1e-6: p3 = p2 + (p2 - p1)
        for k in range(n):
            u = k / n
            q = 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
            out.append(q)
    if not closed: out.append(P[-1])
    clean = [out[0]]
    for q in out[1:]:
        if (q - clean[-1]).length > 1e-4: clean.append(q)
    if closed and (clean[0] - clean[-1]).length < 1e-4: clean.pop()
    return [(q.x, q.y) for q in clean]
def tube_poly(center, r):
    """Closed outline of a thick 2D path (offset both sides)."""
    P = [Vector(p) for p in center]; left, right = [], []
    for i, p in enumerate(P):
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]).normalized(); nrm = Vector((-t.y, t.x))
        left.append(p + nrm * r); right.append(p - nrm * r)
    return [(v.x, v.y) for v in left + right[::-1]], [(v.x, v.y) for v in right]
def prism_bm(bm, pts, y0, y1, mi=0):
    """Extrude a 2D outline (x, z) along y from y0 to y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in pts]; b_ = [bm.verts.new((x, y1, z)) for x, z in pts]
    f = bm.faces.new(a); f.material_index = mi
    f = bm.faces.new(b_[::-1]); f.material_index = mi
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new([a[i], b_[i], b_[j], a[j]]); f.material_index = mi
def earclip(pts):
    """Ear-clipping triangulation of a simple polygon (concave is fine)."""
    P = [Vector(p) for p in pts]; n = len(P)
    area = sum(P[i].x * P[(i + 1) % n].y - P[(i + 1) % n].x * P[i].y for i in range(n))
    idx = list(range(n)) if area > 0 else list(range(n))[::-1]
    cr = lambda a, b, c: (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
    def inside(p, a, b, c): return cr(a, b, p) >= -1e-12 and cr(b, c, p) >= -1e-12 and cr(c, a, p) >= -1e-12
    tris = []; guard = 0
    while len(idx) > 3 and guard < 100000:
        guard += 1; m = len(idx); found = False
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = P[i0], P[i1], P[i2]
            if cr(a, b, c) <= 1e-12: continue
            if any(inside(P[j], a, b, c) for j in idx if j not in (i0, i1, i2)): continue
            tris.append((i0, i1, i2)); idx.pop(k); found = True; break
        if not found:                                              # degenerate leftovers: clip the flattest corner
            k = min(range(m), key=lambda k: abs(cr(P[idx[k - 1]], P[idx[k]], P[idx[(k + 1) % m]])))
            tris.append((idx[k - 1], idx[k], idx[(k + 1) % m])); idx.pop(k)
    tris.append(tuple(idx))
    return tris
def prism(name, pts, y0, y1, m_, parent=None, link=True):
    """Extrude a 2D outline (x, z) along y: caps triangulated with tessellate_polygon (handles concave shapes), walls share the cap verts
    so the result is watertight (the boolean solvers need that)."""
    bm = bmesh.new()
    a = [bm.verts.new((x, y0, z)) for x, z in pts]; b_ = [bm.verts.new((x, y1, z)) for x, z in pts]
    tris = earclip(pts)
    for i, j, k in tris:
        bm.faces.new([a[i], a[j], a[k]])
        bm.faces.new([b_[k], b_[j], b_[i]])
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([a[i], b_[i], b_[j], a[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_, parent, link)
def boxpts(x0, x1, z0, z1): return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
SOLVER = "MANIFOLD"
def carve(name, solid, cutters, m_, smooth_angle=None):
    """Bake solid minus cutters into a new mesh object (EXACT boolean), then drop the helpers."""
    for k, c in enumerate(cutters):
        md = solid.modifiers.new(f"cut{k}", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = c; md.solver = SOLVER
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(solid.evaluated_get(dg))
    for c in cutters: bpy.data.objects.remove(c, do_unlink=True)
    bpy.data.objects.remove(solid, do_unlink=True)
    me.name = name
    o = bpy.data.objects.new(name, me); CL.objects.link(o)
    me.materials.clear(); me.materials.append(m_)
    if smooth_angle:
        try: me.shade_smooth(); me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        except Exception: pass
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.025; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(35)
    return o

# ================= the profile =================
DEPTH, CAV = 2.4, 2.0            # porcelain extends y 0..DEPTH, cavities y -0.2..CAV (back wall stays)
EXT = catmull([(-1.25, 0.0), (-1.25, 0.0), (3.0, 0.0), (3.0, 0.0), (3.3, 2.0), (3.8, 3.5), (4.3, 4.3), (4.3, 4.3), (4.3, 4.6), (4.3, 4.6),
               (2.2, 4.6), (2.2, 4.6), (2.05, 4.3), (2.05, 4.3), (-3.55, 4.3), (-3.55, 4.3), (-3.86, 4.05), (-3.8, 3.45), (-3.3, 2.45),
               (-2.35, 1.4), (-1.5, 0.65), (-1.3, 0.2)], closed=True, n=5)
BOWL = catmull([(-3.3, 4.9), (-3.3, 4.9), (-3.3, 3.75), (-3.15, 3.25), (-2.85, 2.75), (-2.35, 2.25), (-1.75, 1.85), (-1.1, 1.5), (-0.7, 1.2),
                (-0.55, 0.85), (-0.3, 0.72), (0.1, 0.75), (0.25, 1.15), (0.45, 1.7), (0.85, 2.4), (1.3, 3.1), (1.75, 3.75), (1.75, 4.9), (1.75, 4.9)],
               closed=True, n=5)
TRAP_C = catmull([(0.0, 0.92), (0.65, 1.25), (1.2, 2.05), (1.6, 2.7), (2.05, 2.95), (2.5, 2.65), (2.58, 1.6), (2.25, 0.5), (2.15, -0.25)], n=8)
TR = 0.27
TRAP, TRAP_LOW = tube_poly(TRAP_C, TR)
iapex = max(range(len(TRAP_C)), key=lambda i: TRAP_C[i][1])
WL = max(z for x, z in TRAP_LOW[:iapex + 4])            # weir: highest point of the trap's lower wall = the bowl's standing water level
WL = round(WL, 3)
UP_C = TRAP_C[:iapex + 1]                                  # up-leg (bowl side) of the trap
UP, _ = tube_poly(UP_C, TR)
JET_C = catmull([(-3.57, 3.95), (-3.5, 3.3), (-3.1, 2.6), (-2.2, 1.75), (-1.3, 1.05), (-0.55, 0.92)], n=6)
JET, _ = tube_poly(JET_C, 0.12)
RIMF = boxpts(-3.72, -3.42, 3.85, 4.14); HOLEF = boxpts(-3.47, -3.26, 3.74, 3.9)
RIMB = boxpts(1.9, 3.82, 3.9, 4.2); HOLEB = boxpts(1.68, 1.95, 3.78, 3.95); VALVE_IN = boxpts(3.15, 3.85, 3.9, 4.75)

body0 = prism("BodySolid", EXT, 0.0, DEPTH, M_PORC)
cut_objs = [prism(f"cut_{k}", p, -0.2, CAV, M_PORC) for k, p in enumerate([BOWL, TRAP, JET, RIMF, HOLEF, RIMB, HOLEB, VALVE_IN])]
BODY = carve("Bowl", body0, cut_objs, M_PORC, 32)
# tank
TK_X0, TK_X1, TK_Z0, TK_Z1 = 2.6, 5.9, 4.6, 9.4
TI_X0, TI_X1, TI_Z0, TI_Z1 = 2.85, 5.65, 4.85, 9.15
tank0 = prism("TankSolid", boxpts(TK_X0, TK_X1, TK_Z0, TK_Z1), 0.0, DEPTH, M_PORC)
TANK = carve("Tank", tank0, [prism("cut_tank", boxpts(TI_X0, TI_X1, TI_Z0, TI_Z1), -0.2, CAV, M_PORC),
                             prism("cut_valve", boxpts(3.15, 3.85, 4.4, 4.95), -0.2, CAV, M_PORC)], M_PORC)
LID = prism("Lid", boxpts(2.5, 6.0, 9.4, 9.72), 0.0, DEPTH + 0.1, M_PORC)
SEAT = prism("Seat", boxpts(-3.75, 2.0, 4.3, 4.45), 0.0, DEPTH, M_SEAT)
LIDUP = prism("SeatLid", boxpts(2.05, 2.22, 4.45, 9.0), 0.0, DEPTH, M_SEAT)      # seat lid raised against the tank

# front cover (the uncut front half) for the hook
cov0 = prism("CoverSolid", EXT, -DEPTH, 0.0, M_PORC)
COVER = carve("Cover", cov0, [prism("cutc", BOWL, -DEPTH + 0.35, 0.05, M_PORC)], M_PORC, 32)
tcov0 = prism("TankCoverSolid", boxpts(TK_X0, TK_X1, TK_Z0, TK_Z1), -DEPTH, 0.0, M_PORC)
TCOVER = prism("TankCover", boxpts(TK_X0, TK_X1, TK_Z0, TK_Z1), -DEPTH, 0.0, M_PORC); bpy.data.objects.remove(tcov0, do_unlink=True)
LIDC = prism("LidCover", boxpts(2.5, 6.0, 9.4, 9.72), -DEPTH - 0.1, 0.0, M_PORC)
SEATC = prism("SeatCover", boxpts(-3.75, 2.0, 4.3, 4.45), -DEPTH, 0.0, M_SEAT)
LIDUPC = prism("SeatLidCover", boxpts(2.05, 2.22, 4.45, 9.0), -DEPTH, 0.0, M_SEAT)

# room: floor slab (cut at y = 0) and the wall behind the tank
FL_Z = -0.6
floor0 = prism("FloorSolid", boxpts(-12.0, 9.0, FL_Z, 0.0), 0.0, 10.0, M_FLOOR)
FLOOR = carve("Floor", floor0, [prism("cut_flange", boxpts(1.82, 2.48, FL_Z - 0.2, 0.2), -0.2, 1.4, M_FLOOR)], M_FLOOR)
FLOOR.data.materials.append(M_SLABCUT)
WALL = prism("Wall", boxpts(6.15, 6.75, FL_Z, 14.0), 0.0, 10.0, M_WALL)
floorC = prism("FloorCover", boxpts(-12.0, 9.0, FL_Z, 0.0), -8.0, 0.0, M_FLOOR)
wallC = prism("WallCover", boxpts(6.15, 6.75, FL_Z, 14.0), -8.0, 0.0, M_WALL)
PED = box("Pedestal", -14.0, 11.0, -12.0, 12.0, -9.5, -9.0, M_PED)

# drain pipe below the floor (half-section)
PIPE_C = catmull([(2.15, -0.1), (2.15, -1.5), (2.55, -2.35), (3.6, -2.75), (6.0, -2.85), (9.5, -2.9)], n=8)
PIPE_O, _ = tube_poly(PIPE_C, 0.4); PIPE_I, _ = tube_poly([(2.15, 0.3)] + PIPE_C[1:] + [(10.5, -2.9)], 0.31)
pipe0 = prism("PipeSolid", PIPE_O, 0.0, 1.6, M_PVC)
PIPE = carve("DrainPipe", pipe0, [prism("cut_pipe", PIPE_I, -0.2, 1.25, M_PVC)], M_PVC, 30)
PIPE.data.materials.append(M_PVC_IN)
FLANGE = prism("Flange", boxpts(1.65, 2.65, -0.12, 0.0), 0.0, 1.8, M_PLASTIC_D)
FLANGE = carve("FlangeRing", FLANGE, [prism("cut_fl", boxpts(1.88, 2.42, -0.5, 0.5), -0.2, 1.4, M_PLASTIC_D)], M_PLASTIC_D)

cover_parts = [COVER, TCOVER, LIDC, SEATC, LIDUPC, floorC, wallC]

# ================= water bodies =================
E_B = empty("LevelBowl"); E_T = empty("LevelTank"); E_F = empty("FlowTrap")
M_WB, B_WB = level_water("WaterBowl", E_B)
M_WT, B_WT = level_water("WaterTank", E_T)
M_WF, B_WF = level_water("WaterTrapFull", empty("LevelAlways", (0, 0, 50)), flow_obj=E_F)
YW0, YW1 = 0.02, CAV - 0.02
_wb = [(x, z) for x, z in BOWL if z <= 4.2]
_i = max(range(len(BOWL)), key=lambda i: BOWL[i][1])
W_BOWL = prism("WaterBowlBody", [(-3.3, 4.2)] + [p for p in _wb if p[0] > -3.29 or p[1] < 4.19] + [(1.75, 4.2)], YW0, YW1, M_WB)
W_UP = prism("WaterUpLeg", UP, YW0 + 0.005, YW1 - 0.005, M_WB)
W_TRAP = prism("WaterTrapFull", TRAP, YW0 - 0.008, YW1 + 0.008, M_WF)
W_TANK = prism("WaterTankBody", boxpts(TI_X0 + 0.02, TI_X1 - 0.02, TI_Z0 + 0.02, TI_Z1 - 0.3), YW0, YW1, M_WT)

# ================= tank parts (real 3D, behind the cut) =================
YP = 1.0
VX = 3.5                       # flush valve axis
OVX, OV_TOP = 4.28, 8.05       # overflow tube
FVX = 5.25                     # fill valve axis
ring = cyl("ValveSeat", 0.46, 0.22, "Z", (VX, YP, TI_Z0 + 0.11), M_PLASTIC_W, None, 32)
ovt = cyl("OverflowTube", 0.19, OV_TOP - TI_Z0, "Z", (OVX, YP, (OV_TOP + TI_Z0) / 2), M_OVER, None, 24)
cyl("OverflowMouth", 0.13, 0.04, "Z", (OVX, YP, OV_TOP + 0.005), M_PLASTIC_D, None, 20)
box("ValveArm", VX, OVX, YP - 0.08, YP + 0.08, TI_Z0 + 0.05, TI_Z0 + 0.25, M_PLASTIC_W)
# flapper on a hinge next to the overflow tube
HINGE = empty("FlapperHinge", (VX + 0.52, YP, TI_Z0 + 0.3))
bm = bmesh.new(); add_cyl(bm, 0.5, 0.14, "Z", (-0.52, 0, 0), 32); add_box(bm, -0.06, 0.1, -0.12, 0.12, -0.05, 0.06)
FLAP = mesh_obj("Flapper", bm, M_RUBBER, HINGE)
# handle + lever (pivot inside the front wall of the tank)
LEV = empty("LeverPivot", (TI_X0 + 0.12, YP, 8.55))
bm = bmesh.new(); add_box(bm, 0.0, 1.0, -0.05, 0.05, -0.05, 0.05)
LEVER = mesh_obj("Lever", bm, M_CHROME, LEV)
bm = bmesh.new(); add_box(bm, -0.85, -0.25, -0.09, 0.09, -0.07, 0.07); add_cyl(bm, 0.12, 0.2, "X", (-0.3, 0, 0), 16)
HANDLE = mesh_obj("Handle", bm, M_CHROME, LEV)       # the outer handle (sticks out of the front of the tank)
# fill valve + float cup + refill hose
cyl("FillValveShaft", 0.13, 8.55 - TI_Z0, "Z", (FVX, YP, (8.55 + TI_Z0) / 2), M_FILLV, None, 20)
cyl("FillValveHead", 0.3, 0.42, "Z", (FVX, YP, 8.75), M_FILLV, None, 24)
cyl("FillValveFoot", 0.24, 0.3, "Z", (FVX, YP, TI_Z0 + 0.15), M_FILLV, None, 24)
FLOAT = cyl("FloatCup", 0.4, 0.85, "Z", (0, 0, 0), M_FLOAT, None, 28); FLOAT.location = (FVX, YP, 6.0)
hose_c = bpy.data.curves.new("RefillHose", "CURVE"); hose_c.dimensions = "3D"; hose_c.bevel_depth = 0.055; hose_c.bevel_resolution = 3
sp = hose_c.splines.new("BEZIER"); sp.bezier_points.add(1)
for bp_, co, hl, hr in [(sp.bezier_points[0], (FVX - 0.28, YP, 8.8), (FVX - 0.1, YP, 8.8), (FVX - 0.6, YP, 9.0)),
                         (sp.bezier_points[1], (OVX + 0.02, YP, OV_TOP + 0.32), (OVX + 0.3, YP, 9.0), (OVX, YP, OV_TOP + 0.1))]:
    bp_.co = co; bp_.handle_left = hl; bp_.handle_right = hr
HOSE = bpy.data.objects.new("RefillHose", hose_c); CL.objects.link(HOSE); hose_c.materials.append(M_HOSE)
# supply line from the wall into the bottom of the fill valve
sup_c = bpy.data.curves.new("Supply", "CURVE"); sup_c.dimensions = "3D"; sup_c.bevel_depth = 0.08; sup_c.bevel_resolution = 3
sp = sup_c.splines.new("POLY"); pts_ = [(FVX, YP, TK_Z0 + 0.02), (FVX, YP, 3.0), (6.15, YP, 2.4)]
sp.points.add(len(pts_) - 1)
for p_, co in zip(sp.points, pts_): p_.co = (*co, 1)
SUP = bpy.data.objects.new("Supply", sup_c); CL.objects.link(SUP); sup_c.materials.append(M_CHROME)
cyl("ShutOff", 0.17, 0.4, "X", (5.95, YP, 2.4), M_CHROME, None, 16)

# chain: 14 links between the lever tip and the flapper tip, baked per frame
N_CH = 14
links = []
for k in range(N_CH):
    bm = bmesh.new(); add_cyl(bm, 0.035, 0.16, "Z", (0, 0, 0), 8); links.append(mesh_obj(f"Chain{k}", bm, M_CHROME))

# ================= motion: levels and parts =================
T_FL0 = C["lifts"] - 0.05; T_FL1 = T_FL0 + 0.5                    # flapper opens (chain lifts it)
T_FLC0 = C["drops2"] - 0.05; T_FLC1 = T_FLC0 + 0.45                # flapper drops onto the seat
T_TK0, T_TK1 = T_FL1 - 0.1, C["trick"] + 0.3                       # tank empties
T_REF0, T_REF1 = C["opens"] - 0.05, C["off"] + 0.3                 # tank refills
T_FAIL0, T_FAIL1 = C["fails"] - 0.1, C["fails"] + 0.6              # valve fails -> level climbs to the overflow
T_FAILE = C["in"] - 0.15                                            # (reset during the cut to the US beat)
LT_REST, LT_LOW, LT_FAIL = 7.6, TI_Z0 + 0.25, OV_TOP + 0.08
LT = PW([(0, LT_REST), (T_TK0, LT_REST), (T_TK1, LT_LOW), (T_REF0, LT_LOW), (T_REF1, LT_REST), (T_FAIL0, LT_REST), (T_FAIL1, LT_FAIL),
         (T_FAILE, LT_FAIL), (T_FAILE + 0.05, LT_REST)])
T_ADD0, T_ADD1, T_ADD2 = C["add"] - 0.05, C["spills"] + 0.1, C["changes"] + 0.2
T_BR0, T_BR1 = T_FL1 + 0.2, C["completely"] + 0.1                  # bowl rises while the tank dumps in
T_SI0, T_SI1 = C["falling"] - 0.2, C["siphon"] + 0.6               # siphon empties the bowl
T_AIR = C["air"] - 0.05; T_GUR = C["gurgle"] - 0.1
T_RB0, T_RB1 = C["refills"] - 0.05, C["seal"] + 0.5                 # bowl refills, the seal comes back
LB_LOW = 0.95
LB = PW([(0, WL), (T_ADD0 + 0.3, WL), (T_ADD1, WL + 0.12), (T_ADD2, WL), (T_BR0, WL), (T_BR1, WL + 0.55), (T_SI0, WL + 0.55), (T_SI1, LB_LOW),
         (T_RB0, LB_LOW), (T_RB1, WL)])
bake_fn(E_B, "location", 2, LB); bake_fn(E_T, "location", 2, LT)
bake_fn(E_F, "location", 0, lambda t: -1.4 * t)
bake_fn(E_F, "location", 2, lambda t: -1.4 * t)
windows(W_TRAP, [(C["completely"] - 0.15, T_GUR + 0.4)])
# flapper: opens on "lifts", floats open while the tank empties, drops on "drops"
FA = PW([(0, 0.0), (T_FL0, 0.0), (T_FL1, 68.0), (T_FLC0, 68.0), (T_FLC1, 0.0)])
bake_fn(HINGE, "rotation_euler", 1, lambda t: math.radians(FA(t)) * -1.0)
# lever: a small dip on "press the handle", full pull on "lifts", released after the dump starts
LA = PW([(0, 0.0), (C["press"], 0.0), (C["handle"] + 0.2, 10.0), (T_FL0, 10.0), (T_FL0 + 0.3, 24.0), (C["dumps"] + 0.6, 24.0), (C["once"] + 0.5, 0.0)])
bake_fn(LEV, "rotation_euler", 1, lambda t: math.radians(LA(t)))
# float cup rides the tank water; it rests on its stop when the tank is low
FZ = lambda t: max(TI_Z0 + 0.6, min(LT(t) - 0.28, 8.0))
bake_fn(FLOAT, "location", 2, FZ)
def lever_tip(t):
    a = math.radians(LA(t)); return Vector((LEV.location.x + 0.95 * math.cos(a), YP, LEV.location.z - 0.95 * math.sin(a)))
def flap_tip(t):
    a = math.radians(FA(t)); hx, hz = HINGE.location.x, HINGE.location.z
    return Vector((hx - 0.95 * math.cos(a), YP, hz + 0.07 + 0.95 * math.sin(a)))
ch_loc = [[] for _ in range(N_CH)]; ch_rot = [[] for _ in range(N_CH)]
for t in TS:
    p0, p1 = lever_tip(t), flap_tip(t); L_ = (p1 - p0).length; slack = max(0.0, 3.25 - L_)
    for k in range(N_CH):
        u = (k + 0.5) / N_CH
        p = p0.lerp(p1, u) + Vector((0.55 * slack * math.sin(math.pi * u), 0, 0))
        ch_loc[k].append(p); ch_rot[k].append(0.5 * (k % 2) * math.pi)
for k in range(N_CH):
    for ax in range(3): bake(links[k], "location", ax, [v[ax] for v in ch_loc[k]])
    links[k].rotation_euler = (0, 0, (k % 2) * math.pi / 2)

# ================= flow: baked drops along paths =================
SPH = bpy.data.meshes.new("DropMesh")
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(SPH); bm.free()
for poly in SPH.polygons: poly.use_smooth = True
SPH.materials.append(M_DROP)
def path_fn(pts3):
    P = [Vector(p) for p in pts3]; seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]; tot = sum(seg)
    def at(u):
        d = max(0.0, min(1.0, u)) * tot
        for i, s in enumerate(seg):
            if d <= s or i == len(seg) - 1: return P[i].lerp(P[i + 1], d / s if s else 0)
            d -= s
    return at, tot
_drop_n = [0]
def stream(name, pts2, t0, t1, n, speed, rad, m_=None, y=YP, jitter=0.12, wobble=0.0):
    """n drops released evenly between t0 and t1 - travel; each one runs the whole path at `speed` units/s."""
    at, tot = path_fn([(x, y, z) for x, z in pts2]); travel = tot / speed
    span = max(0.05, (t1 - t0) - travel)
    for k in range(n):
        tk = t0 + span * k / max(1, n - 1)
        o = bpy.data.objects.new(f"{name}{k}", SPH); CL.objects.link(o)
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m_ or M_DROP
        jx, jy, jz = (random.uniform(-jitter, jitter) for _ in range(3)); ph = random.uniform(0, 6.28)
        loc = [[], [], []]; sc = []
        for t in TS:
            u = (t - tk) / travel
            p = at(u) + Vector((jx, jy * 2.0, jz)) + Vector((wobble * math.sin(9 * t + ph), 0, wobble * math.cos(7 * t + ph)))
            for ax in range(3): loc[ax].append(p[ax])
            s = rad if 0.0 <= u <= 1.0 else 0.0
            if 0 <= u < 0.06: s = rad * u / 0.06
            if 0.94 < u <= 1: s = rad * (1 - u) / 0.06
            sc.append(s)
        for ax in range(3): bake(o, "location", ax, loc[ax]); bake(o, "scale", ax, sc)
        _drop_n[0] += 1
SPILL = [p for p in TRAP_C[iapex - 1:]] + [(2.15, -1.5), (2.55, -2.35), (3.6, -2.75), (6.0, -2.85), (9.0, -2.9)]
SPILL = [(x, z - 0.12) for x, z in SPILL]
TANK_TO_BACK = [(3.5, 5.6), (3.5, 4.6), (3.45, 4.05), (1.95, 4.05), (1.8, 3.86), (1.3, 3.15), (0.85, 2.5)]
FRONT_RIM = [(-3.56, 4.0), (-3.38, 3.82), (-3.2, 3.3), (-2.85, 2.8), (-2.4, 2.4)]
JET_PATH = list(JET_C) + [(0.0, 0.92), (0.65, 1.25), (1.2, 2.05)]
OVER_PATH = [(OVX, OV_TOP + 0.2), (OVX, 4.95), (VX + 0.3, 4.3), (3.45, 4.05), (1.95, 4.05), (1.8, 3.86), (1.3, 3.15), (0.85, 2.6)]
# B3 add a little more water: pour from above, it spills over the bend
stream("Pour", [(-1.4, 7.6), (-1.4, WL)], T_ADD0, T_ADD1 + 0.2, 22, 9.0, 0.09, jitter=0.05)
stream("Spill", SPILL, C["spills"] - 0.25, C["changes"] + 0.6, 26, 4.0, 0.075, jitter=0.03)
# B5-B6 the flush: tank -> flush valve -> rim channel -> rim holes; jet; spill + full trap flow
stream("Dump", TANK_TO_BACK, T_FL1 - 0.1, C["trick"], 46, 4.5, 0.085, jitter=0.1)
stream("Rim", FRONT_RIM, C["rushes"] - 0.4, C["trick"], 30, 3.5, 0.075, jitter=0.04)
stream("Jet", JET_PATH, C["jet"] - 0.5, C["trick"], 34, 5.0, 0.07, jitter=0.03)
stream("FlowDown", SPILL, T_BR0 + 1.2, T_GUR + 0.4, 60, 5.0, 0.085, jitter=0.05)
# B7 air gets in -> gurgle
stream("Air", [(0.1, 1.0), (0.65, 1.25), (1.2, 2.05), (1.6, 2.7), (2.05, 2.95), (2.5, 2.65), (2.58, 1.6)], T_AIR, T_GUR + 0.8, 14, 2.6, 0.12,
       M_AIR, jitter=0.08, wobble=0.04)
# B4 sewer gas comes up the drain and stops under the water seal
GAS_PATH = [(9.0, -2.8), (6.0, -2.75), (3.6, -2.65), (2.55, -2.25), (2.2, -1.4), (2.2, 0.4), (2.5, 1.5), (2.48, 2.35)]
stream("Gas", GAS_PATH, C["that"] - 1.2, C["now"] + 0.6, 22, 3.6, 0.24, M_GAS, jitter=0.1, wobble=0.06)
# B8 refill: fill valve sprays, the refill tube feeds the overflow tube -> bowl
stream("Fill", [(FVX - 0.2, TI_Z0 + 0.3), (FVX - 0.55, TI_Z0 + 0.35), (FVX - 0.9, TI_Z0 + 0.2)], T_REF0, T_REF1, 40, 1.6, 0.06, jitter=0.12)
stream("Refill", OVER_PATH, C["small"] - 0.1, T_RB1 + 0.4, 34, 4.5, 0.06, jitter=0.03)
# B9 the valve fails: water rises into the overflow tube and runs into the bowl, then over the bend
stream("Over", OVER_PATH, T_FAIL1 - 0.1, T_FAILE, 40, 4.5, 0.075, jitter=0.04)
stream("OverSpill", SPILL, T_FAIL1 + 1.0, T_FAILE + 0.3, 26, 4.0, 0.075, jitter=0.03)

# ================= graphics in the scene =================
# trapway tracer (cyan line that draws along the trap on "climbs, then drops")
tr_c = bpy.data.curves.new("TrapTracer", "CURVE"); tr_c.dimensions = "3D"; tr_c.bevel_depth = 0.055; tr_c.bevel_resolution = 3
sp = tr_c.splines.new("POLY"); sp.points.add(len(TRAP_C) - 1)
for p_, (x, z) in zip(sp.points, TRAP_C): p_.co = (x, -0.08, z, 1)
TRACER = bpy.data.objects.new("TrapTracer", tr_c); CL.objects.link(TRACER); tr_c.materials.append(M_TRACE)
T_TR0, T_TR1 = C["climbs"] - 0.2, C["drain"] + 0.3
tr_c.bevel_factor_end = 0.0; tr_c.keyframe_insert("bevel_factor_end", frame=F(T_TR0))
tr_c.bevel_factor_end = 1.0; tr_c.keyframe_insert("bevel_factor_end", frame=F(T_TR1))
windows(TRACER, [(C["bent"] - 0.1, C["water"] - 0.1), (C["bend2"] - 0.1, C["completely"] + 0.2), (C["siphon"] - 0.1, C["keeps"])])
# water level line through the bowl and the top of the bend
lvl = box("LevelLine", -2.9, 2.3, -0.12, -0.06, WL - 0.03, WL + 0.03, M_LINE)
windows(lvl, [(C["high"] - 0.1, C["that"] - 0.1), (C["seal"] - 0.1, C["as"] - 0.1)])
# red bar: the water seal stops the gas
bar = box("SealBar", 1.4, 2.3, -0.12, -0.06, WL - 0.06, WL + 0.06, M_REDBAR)
windows(bar, [(C["blocks"] - 0.1, C["now"] - 0.1)])
# arrows: suction pull on "pulls", overflow "not onto your floor"
bm = bmesh.new()
for (x, z), d in [((2.58, 1.9), (0, -1)), ((2.4, 0.4), (-0.1, -1)), ((0.0, 2.2), (0.2, -1)), ((-1.2, 2.0), (0.7, -0.6))]:
    add_arrow(bm, (x, z), d, 0.9, 0.42, -0.1)
PULL = mesh_obj("PullArrows", bm, M_ARROW)
bake_fn(PULL, "location", 2, lambda t: -0.12 * ((t * 2.5) % 1.0))
windows(PULL, [(C["pulls"] - 0.1, C["keeps"] - 0.1)])
bm = bmesh.new(); add_arrow(bm, (OVX - 0.6, 7.2), (0, -1), 1.4, 0.5, -0.1)
OVA = mesh_obj("OverflowArrow", bm, M_ARROW)
windows(OVA, [(C["overflow"] - 0.1, C["in"] - 0.1)])
# highlight pulses
glow(B_RUBBER, pulse(C["flapper"] - 0.05, 1.6, 0.0, 0.15, 0.8, 0.5) + pulse(C["flapper2"] - 0.05, 1.6, 0.0, 0.15, 1.0, 0.5)[1:])
glow(B_FLOAT, pulse(C["float"] - 0.05, 2.0, 0.0, 0.15, 1.0, 0.5) + pulse(C["float2"] - 0.05, 2.0, 0.0, 0.15, 1.0, 0.5)[1:])
B_FILLV.inputs["Emission Color"].default_value = (*GOLD, 1)
glow(B_FILLV, pulse(C["fill"] - 0.05, 2.0, 0.0, 0.15, 0.9, 0.4))
glow(B_HOSE, pulse(C["tube"] - 0.05, 2.5, 0.0, 0.15, 1.0, 0.5))
glow(B_OVER, pulse(C["overflow"] - 0.05, 1.8, 0.0, 0.15, 1.6, 0.6))
glow(B_WT, [(0, 0.35), (C["one"] - 0.1, 0.35), (C["one"] + 0.15, 0.35), (C["gallons"] + 0.1, 3.0), (C["have"] - 0.2, 3.0), (C["have"] + 0.4, 0.35)])
B_WT.inputs["Emission Color"].default_value = (0.25, 0.65, 1.0, 1)
glow(B_WB, [(0, 0.35)] + pulse(C["seal"] - 0.05, 2.2, 0.35, 0.2, 1.0, 0.6)[1:])
# fill valve turns red when it "fails" (separate red cap so the gold pulse stays clean)
fail_cap = cyl("FailCap", 0.33, 0.46, "Z", (FVX, YP, 8.75), M_REDBAR, None, 24)
windows(fail_cap, [(C["fails"] - 0.05, T_FAILE)])

# ================= hook: the cover slides off on "cut" =================
T_CV0, T_CV1 = C["cut"] - 0.05, C["open"] + 0.35
for o in cover_parts:
    bake_fn(o, "location", 1, PW([(0, 0.0), (T_CV0, 0.0), (T_CV1, -14.0)]))
    bake_fn(o, "location", 2, PW([(0, 0.0), (T_CV0 + 0.1, 0.0), (T_CV1, -3.0)]))
    windows(o, [(0, T_CV1 + 0.05)])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 400
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-11.0, -19.0, 10.0), (1.0, 0.0, 4.6), 30),
    (C["cut"] - 0.15, (-7.5, -16.0, 8.0), (1.0, 0.0, 4.4), 30),
    (C["cut"] - 0.05, (1.0, -21.0, 6.0), (1.1, 0.0, 4.2), 30, "cut"),
    (C["hidden"] - 0.1, (1.0, -19.5, 5.4), (1.1, 0.0, 4.0), 30),
    (C["bent"] - 0.2, (1.4, -12.0, 2.6), (1.2, 0.0, 1.5), 32, "cut"),
    (C["water"] - 0.1, (1.2, -10.5, 2.4), (1.2, 0.0, 1.4), 32),
    (C["water"], (-0.4, -12.0, 3.6), (-0.2, 0.0, 2.6), 32, "cut"),
    (C["add"] - 0.15, (-0.2, -11.0, 3.4), (-0.1, 0.0, 2.6), 32),
    (C["add"] - 0.1, (1.5, -16.5, 3.0), (1.6, 0.0, 1.8), 30, "cut"),
    (C["that"] - 0.15, (1.8, -15.5, 2.6), (1.8, 0.0, 1.4), 30),
    (C["that"] - 0.1, (3.6, -12.5, 1.2), (3.2, 0.0, 0.0), 30, "cut"),
    (C["now"] - 0.2, (3.4, -11.5, 1.2), (3.0, 0.0, 0.2), 30),
    (C["now"] - 0.1, (3.2, -13.0, 8.4), (4.1, 0.0, 7.0), 32, "cut"),
    (C["chain"] - 0.25, (3.4, -11.5, 8.0), (4.0, 0.0, 6.8), 32),
    (C["chain"] - 0.2, (3.0, -8.5, 6.5), (3.8, 0.0, 5.75), 32, "cut"),
    (C["tank"] - 0.2, (3.1, -8.0, 6.3), (3.8, 0.0, 5.65), 32),
    (C["tank"] - 0.1, (2.0, -14.0, 7.0), (2.4, 0.0, 5.2), 30, "cut"),
    (C["rushes"] - 0.2, (1.6, -13.5, 6.0), (1.6, 0.0, 4.2), 30),
    (C["rushes"] - 0.1, (-0.6, -12.0, 4.6), (-0.6, 0.0, 2.9), 32, "cut"),
    (C["bend2"] - 0.2, (-0.3, -11.0, 4.0), (-0.3, 0.0, 2.6), 32),
    (C["bend2"] - 0.1, (1.4, -12.0, 2.4), (1.3, 0.0, 1.3), 32, "cut"),
    (C["falling"] - 0.2, (1.4, -11.0, 2.2), (1.3, 0.0, 1.2), 32),
    (C["falling"] - 0.1, (1.4, -16.0, 3.0), (1.6, 0.0, 1.4), 30, "cut"),
    (C["air"] - 0.3, (1.3, -15.0, 2.8), (1.5, 0.0, 1.4), 30),
    (C["air"] - 0.2, (1.4, -9.5, 2.2), (1.3, 0.0, 1.6), 32, "cut"),
    (C["then"] - 0.2, (1.5, -9.0, 2.2), (1.3, 0.0, 1.6), 32),
    (C["then"] - 0.1, (3.0, -10.0, 7.2), (3.9, 0.0, 6.0), 32, "cut"),
    (C["small"] - 0.2, (3.2, -9.5, 7.0), (4.0, 0.0, 6.0), 32),
    (C["small"] - 0.1, (2.0, -17.0, 6.6), (2.2, 0.0, 4.6), 30, "cut"),
    (C["as"] - 0.2, (2.0, -16.0, 6.4), (2.2, 0.0, 4.6), 30),
    (C["as"] - 0.1, (3.8, -10.0, 8.4), (4.4, 0.0, 7.2), 32, "cut"),
    (C["if"] - 0.2, (3.8, -9.5, 8.2), (4.4, 0.0, 7.2), 32),
    (C["if"] - 0.1, (2.2, -17.0, 6.8), (2.2, 0.0, 4.8), 30, "cut"),
    (C["in"] - 0.2, (2.0, -16.0, 6.5), (2.2, 0.0, 4.6), 30),
    (C["in"] - 0.1, (11.0, -16.0, 9.0), (2.4, 0.0, 5.6), 30, "cut"),
    (C["have"] - 0.2, (9.0, -14.5, 8.6), (3.2, 0.0, 6.2), 30),
    (C["have"] - 0.1, (-10.0, -18.0, 8.0), (1.2, 0.0, 4.0), 30, "cut"),
    (C["end"], (9.0, -19.0, 8.0), (1.2, 0.0, 4.0), 30),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.03 * math.sin(t * 0.7), 0.0, 0.02 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
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
sun = bpy.data.lights.new("Key", "SUN"); sun.energy = 2.2; sun.color = (1.0, 0.93, 0.82); sun.angle = math.radians(5)
so = bpy.data.objects.new("Key", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(10), math.radians(-28))
sun2 = bpy.data.lights.new("Fill", "SUN"); sun2.energy = 0.8; sun2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("Fill", sun2); scene.collection.objects.link(so2); so2.rotation_euler = (math.radians(75), math.radians(-10), math.radians(150))
# the cut face looks along -Y: a big soft front light keeps the section readable, warm key from the upper left, cool rim from behind
LT_A = target("LT_Face", (1.5, 0.0, 4.0)); area("Face", (-2.0, -26.0, 10.0), 16.0, 2600, (1.0, 0.96, 0.9), LT_A)
area("Top", (1.0, -4.0, 18.0), 8.0, 900, (1.0, 0.95, 0.88), LT_A)
area("Under", (4.0, -14.0, -6.0), 8.0, 500, (0.8, 0.88, 1.0), target("LT_Pipe", (4.0, 0.0, -2.5)))
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


# ================= export cues, events and projected anchors for the typography =================
ANCH = {
    "trapway": lambda t: Vector((2.05, -0.1, 2.95 + TR)),
    "trap_mid": lambda t: Vector((1.2, -0.1, 2.05)),
    "bowl_water": lambda t: Vector((-1.6, -0.1, WL - 0.3)),
    "level": lambda t: Vector((-2.6, -0.1, WL)),
    "weir": lambda t: Vector((2.05, -0.1, WL)),
    "drain": lambda t: Vector((4.5, -0.1, -2.8)),
    "gas": lambda t: Vector((2.3, -0.1, 0.6)),
    "handle": lambda t: Vector((TI_X0 - 0.55, -0.1, 8.55 - 0.2 * math.sin(math.radians(LA(t))))),
    "chain": lambda t: (lever_tip(t) + flap_tip(t)) * 0.5 + Vector((0.0, -1.0, 0.0)),
    "flapper": lambda t: flap_tip(t) * 0.5 + HINGE.location * 0.5 + Vector((0.0, -0.5, 0.0)),
    "tank": lambda t: Vector((3.0, -0.1, 6.4)),
    "rim_front": lambda t: Vector((-3.4, -0.1, 3.82)),
    "rim_back": lambda t: Vector((1.82, -0.1, 3.86)),
    "jet": lambda t: Vector((-0.6, -0.1, 0.92)),
    "float": lambda t: Vector((FVX - 0.4, YP - 0.4, FZ(t))),
    "fill_valve": lambda t: Vector((FVX + 0.3, YP - 0.3, 8.75)),
    "refill_tube": lambda t: Vector((4.75, YP - 0.2, 9.08)),
    "overflow": lambda t: Vector((OVX, YP - 0.3, 6.8)),
    "tank_water": lambda t: Vector((4.0, -0.1, (TI_Z0 + LT(t)) / 2)),
}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"cover": [round(T_CV0, 3), round(T_CV1, 3)], "tracer": [round(T_TR0, 3), round(T_TR1, 3)], "pour": [round(T_ADD0, 3), round(T_ADD1, 3)],
          "spill": round(C["spills"], 3), "gas": [round(C["that"] - 0.6, 3), round(C["now"], 3)], "lever": round(C["handle"], 3),
          "flap_open": round(T_FL0, 3), "dump": [round(T_FL1, 3), round(T_TK1, 3)], "trap_full": round(C["completely"] - 0.15, 3),
          "siphon": [round(T_SI0, 3), round(T_SI1, 3)], "air": round(T_AIR, 3), "gurgle": round(T_GUR, 3), "flap_close": round(T_FLC1 - 0.1, 3),
          "refill": [round(T_REF0, 3), round(T_REF1, 3)], "bowl_refill": [round(T_RB0, 3), round(T_RB1, 3)], "fail": [round(T_FAIL0, 3), round(T_FAILE, 3)],
          "weir": WL, "drops": _drop_n[0]}
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
