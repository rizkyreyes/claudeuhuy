# P-Trap-3D: why your sink drain doesn't smell (the P-trap water seal). Studio cutaway in Blender Cycles. Every cue is a word in the VO.
# One set: a bathroom sink drain cut in half through its centre line (the cut face looks at -Y): ceramic basin + drain flange, tailpiece,
#   1-1/2" PVC J-bend with slip nuts and its standing water (the seal), trap arm into the wall, 2" sanitary tee, drain stack down to the
#   building drain (sewer side) and the vent up through the roof. A second small set to the left: an old S-trap (no vent).
# A front cover (the uncut front halves) is in place for the hook and slides away on "cut".
# No people, no brand. 1 unit = 1 inch; the seal is drawn 2.25" deep (code: 2-4"). Wall/roof distances are compressed (illustrative).
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
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
random.seed(8)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("pipe", "pipe"), ("sink", "sink"), ("always", "always"), ("full", "full"), ("water", "water"), ("purpose", "purpose"),
        ("lets", "let's"), ("cut", "cut"), ("open", "open"), ("drain", "drain"), ("drops", "drops"), ("bends", "bends"), ("u", "u"),
        ("turns", "turns"), ("wall", "wall"), ("shape", "shape"), ("ptrap", "p-trap"), ("most", "most"), ("flows", "flows"),
        ("last", "last"), ("stays", "stays"), ("bottom", "bottom"), ("bend", "bend"), ("leftover", "leftover"), ("seal", "seal"),
        ("past", "past"), ("pipes", "pipes"), ("sewer", "sewer"), ("gas", "gas"), ("smells", "smells"), ("rotten", "rotten"),
        ("eggs", "eggs"), ("mostly", "mostly"), ("hydrogen", "hydrogen"), ("without", "without"), ("trap", "trap"),
        ("straight", "straight"), ("drain2", "drain"), ("but", "but"), ("gas2", "gas"), ("push", "push"), ("stays2", "stays"),
        ("plumbing", "plumbing"), ("code", "code"), ("seal2", "seal"), ("two", "two"), ("four", "four"), ("inches", "inches"),
        ("deep", "deep"), ("but2", "but"), ("big", "big"), ("rush", "rush"), ("pull", "pull"), ("seal3", "seal"), ("siphon", "siphon"),
        ("thats", "that's"), ("second", "second"), ("vent", "vent"), ("runs", "runs"), ("roof", "roof"), ("air", "air"),
        ("trap2", "trap"), ("put", "put"), ("old", "old"), ("straps", "s-traps"), ("siphon2", "siphon"), ("dry", "dry"),
        ("banned", "banned"), ("new", "new"), ("trap3", "trap"), ("job", "job"), ("dropr", "drop"), ("ring", "ring"), ("heavy", "heavy"),
        ("sinks", "sinks"), ("bend2", "bend"), ("sewer2", "sewer"), ("loosen", "loosen"), ("nuts", "nuts"), ("there", "there"),
        ("if", "if"), ("guest", "guest"), ("smells2", "smells"), ("trap4", "trap"), ("dried", "dried"), ("run", "run"),
        ("seconds", "seconds"), ("seal4", "seal"), ("back", "back"), ("have", "have"), ("dropped", "dropped"), ("tell", "tell"),
        ("next", "next"), ("canal", "canal"), ("pumps", "pumps"), ("follow", "follow")]
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
CL = coll("PTrap")

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
# ================= palette + materials =================
GOLD, CYAN, RED, ORANGE = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12), (1.0, 0.42, 0.10)
GAS = (0.62, 0.86, 0.18)
def pvc(name):
    m, b = mat(name, (0.86, 0.87, 0.85), 0.32, 0.0, GOLD); b.inputs["Coat Weight"].default_value = 0.3; return m, b
M_PVC, _ = pvc("PVC")
M_TAIL, B_TAIL = pvc("Tailpiece"); M_JB, B_JB = pvc("JBend"); M_ARM, B_ARM = pvc("TrapArm")
M_STACK, B_STACK = pvc("StackLow"); M_VENT, B_VENT = pvc("Vent")
M_STRAP, B_STRAP = pvc("STrap")
M_NUT, B_NUT = mat("SlipNut", (0.80, 0.81, 0.79), 0.45, 0.0, GOLD)
M_CHROME, _ = mat("Chrome", (0.80, 0.82, 0.85), 0.12, 1.0)
M_CERAMIC, _ = mat("Ceramic", (0.93, 0.93, 0.91), 0.12, 0.0); 
M_COUNTER, _ = mat("Counter", (0.20, 0.21, 0.23), 0.35, 0.0, GOLD, 9)
M_DRYWALL, _ = mat("Drywall", (0.62, 0.60, 0.56), 0.85, 0.0, GOLD, 14)
M_ROOF, _ = mat("Roof", (0.24, 0.20, 0.18), 0.8, 0.0, GOLD, 10)
M_SLABCUT, _ = mat("SlabCut", (0.32, 0.31, 0.30), 0.9, 0.0, GOLD, 18)
M_GOLDRING, B_RING = mat("Ring", (1.0, 0.62, 0.12), 0.22, 1.0, GOLD); B_RING.inputs["Emission Strength"].default_value = 1.6
M_LINE, B_LINE = mat("Bracket", CYAN, 0.4, 0.0, CYAN); B_LINE.inputs["Emission Strength"].default_value = 6.0
M_DROPW, B_DROPW = mat("DropWater", (0.45, 0.85, 1.0), 0.05, 0.0, (0.45, 0.85, 1.0)); B_DROPW.inputs["Emission Strength"].default_value = 2.4
M_GASD, B_GASD = mat("Gas", GAS, 0.6, 0.0, GAS, 0, 0.7); B_GASD.inputs["Emission Strength"].default_value = 3.2
M_AIR, B_AIR = mat("Air", (0.92, 0.96, 1.0), 0.3, 0.0, (0.92, 0.96, 1.0), 0, 0.75); B_AIR.inputs["Emission Strength"].default_value = 1.8
M_ARROWR, B_ARROWR = mat("ArrowRed", RED, 0.5, 0.0, RED); B_ARROWR.inputs["Emission Strength"].default_value = 5.0
M_FLOOR = tiles("Floor", (0.11, 0.11, 0.12), (0.095, 0.095, 0.105), 0.10, "XY")
M_WALL = tiles("Tile", (0.055, 0.06, 0.07), (0.048, 0.052, 0.062), 0.12, "XZ")

# water: pale blue, slightly see-through; emission colour mixes to red when the seal is broken (REDV), pulse on "seal" (WGLOW)
def water_material():
    m, nt, b = new_mat("TrapWater"); N, L = nt.nodes, nt.links
    rv = N.new("ShaderNodeValue"); rv.name = "REDV"
    col = mix_rgb(nt, rv.outputs[0], (0.10, 0.55, 1.0), (1.0, 0.16, 0.10))
    L.new(col, b.inputs["Base Color"]); L.new(col, b.inputs["Emission Color"])
    gl = N.new("ShaderNodeValue"); gl.name = "WGLOW"; L.new(gl.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Roughness"].default_value = 0.05; b.inputs["Alpha"].default_value = 0.72
    return m, rv, gl
M_WATER, REDV, WGLOW = water_material()

# ================= geometry: swept half pipes along paths in the XZ plane (cut face at y = 0) =================
def P_line(p0, p1, n=8): return [(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n) for i in range(n + 1)]
def P_arc(c, R_, a0, a1, n=24):
    return [(c[0] + R_ * math.cos(math.radians(a0 + (a1 - a0) * i / n)), c[1] + R_ * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
def P_join(*parts):
    out = []
    for p in parts:
        for q in p:
            if not out or (abs(out[-1][0] - q[0]) + abs(out[-1][1] - q[1])) > 1e-6: out.append(q)
    return out
def frames(pts):
    """(point, in-plane normal) per sample of a 2D path (x, z)."""
    F_ = []
    for i, (x, z) in enumerate(pts):
        a, b_ = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        t = Vector((b_[0] - a[0], 0, b_[1] - a[1])).normalized()
        F_.append((Vector((x, 0, z)), Vector((t.z, 0, -t.x))))
    return F_
def ring_pts(P, N, r, a0, span, seg):
    return [P + r * (math.cos(a0 + span * k / seg) * N + math.sin(a0 + span * k / seg) * Vector((0, 1, 0))) for k in range(seg + 1)]
def half_pipe(name, pts, r0, r1, m_, a0=0.0, span=math.pi, seg=18, parent=None):
    bm = bmesh.new(); secs = []
    for P, N in frames(pts):
        o = [bm.verts.new(p) for p in ring_pts(P, N, r1, a0, span, seg)]
        i = [bm.verts.new(p) for p in ring_pts(P, N, r0, a0, span, seg)][::-1]
        secs.append(o + i)
    n = len(secs[0])
    for A_, B_ in zip(secs, secs[1:]):
        for k in range(n): bm.faces.new([A_[k], A_[(k + 1) % n], B_[(k + 1) % n], B_[k]])
    for S in (secs[0], secs[-1]):
        h = seg + 1
        for k in range(seg): bm.faces.new([S[k], S[k + 1], S[n - 2 - k], S[n - 1 - k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, m_, parent)
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(50))
    except Exception: pass
    return o
def half_solid(name, pts, r, m_, zcut=None, seg=18, parent=None, a0=0.0):
    bm = bmesh.new(); secs = []
    for P, N in frames(pts): secs.append([bm.verts.new(p) for p in ring_pts(P, N, r, a0, math.pi, seg)])
    n = len(secs[0])
    for A_, B_ in zip(secs, secs[1:]):
        for k in range(n): bm.faces.new([A_[k], A_[(k + 1) % n], B_[(k + 1) % n], B_[k]])
    bm.faces.new(secs[0]); bm.faces.new(secs[-1][::-1])
    if zcut is not None:
        geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, zcut), plane_no=(0, 0, 1), clear_outer=True)
        open_edges = [e for e in bm.edges if len(e.link_faces) < 2]
        if open_edges: bmesh.ops.edgeloop_fill(bm, edges=open_edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_, parent)

# ---- dimensions: 1 unit = 1 inch. 1-1/2" trap (bore radius 0.75, outside 0.95), 2" stack ----
R0, R1 = 0.75, 0.95
RS0, RS1 = 1.0, 1.19
XS = 13.5                     # stack axis
Z_ARM = 11.75                 # trap arm centre line
Z_WEIR = Z_ARM - R0           # 11.0: water stands at the weir
Z_DIP = 8.0 + R0              # 8.75: top of the bore at the bottom of the bend -> seal 2.25"
X_IN, X_OUT = -2.0, 2.0
JB_PATH = P_join(P_line((X_IN, 13.2), (X_IN, 10.0), 6), P_arc((0, 10.0), 2.0, 180, 360, 30), P_line((X_OUT, 10.0), (X_OUT, 10.55), 2),
                 P_arc((X_OUT + 1.2, 10.55), 1.2, 180, 90, 12), P_line((X_OUT + 1.2, Z_ARM), (4.6, Z_ARM), 3))
TAIL_PATH = P_line((X_IN, 24.3), (X_IN, 12.6), 6)
ARM_PATH = P_line((4.4, Z_ARM), (XS - RS1 + 0.05, Z_ARM), 8)
WATER_PATH = P_join(P_line((X_IN, 12.4), (X_IN, 10.0), 4), P_arc((0, 10.0), 2.0, 180, 360, 30), P_line((X_OUT, 10.0), (X_OUT, 10.55), 2),
                    P_arc((X_OUT + 1.2, 10.55), 1.2, 180, 90, 12), P_line((X_OUT + 1.2, Z_ARM), (4.4, Z_ARM), 2))
JB = empty("JBendRig")                       # the J-bend, its water and the ring drop together on "loosen two nuts"
jbend = half_pipe("JBend", JB_PATH, R0, R1, M_JB, parent=JB)
tail = half_pipe("Tailpiece", TAIL_PATH, R0 - 0.12, R1 - 0.13, M_TAIL)     # tailpiece slips inside the J-bend
arm = half_pipe("TrapArm", ARM_PATH, R0, R1, M_ARM)
# slip nuts at both joints of the J-bend
def nut(name, x, z, axis, parent):
    pts = P_line((x, z - 0.45), (x, z + 0.45), 2) if axis == "Z" else P_line((x - 0.45, z), (x + 0.45, z), 2)
    return half_pipe(name, pts, R1 - 0.01, R1 + 0.28, M_NUT, seg=24, parent=parent)
nut1 = nut("SlipNutIn", X_IN, 13.0, "Z", JB); nut2 = nut("SlipNutOut", 4.4, Z_ARM, "X", JB)
# water levels (separate objects = hold states): 0 full .. 5 a puddle, 6 = none
LEVELS = [Z_WEIR, 10.35, 9.7, 9.1, 8.5, 7.75]
WAT = [half_solid(f"Water{k}", WATER_PATH, R0 - 0.03, M_WATER, zcut=z, parent=JB) for k, z in enumerate(LEVELS)]
# stack: drain below the tee, vent above it; the tee leaves the left-front quarter open where the arm comes in
STACK_LO = P_join(P_line((XS, 10.55), (XS, -12.0), 10), P_arc((XS + 1.6, -12.0), 1.6, 180, 270, 10), P_line((XS + 1.6, -13.6), (40.0, -13.6), 10))
stack_lo = half_pipe("StackDrain", STACK_LO, RS0, RS1, M_STACK)
tee = half_pipe("Tee", P_line((XS, 10.5), (XS, 13.0), 2), RS0, RS1, M_STACK, a0=0.0, span=0.60 * math.pi)
vent = half_pipe("Vent", P_line((XS, 12.95), (XS, 57.0), 12), RS0, RS1, M_VENT)
# sink: half basin (lathe), drain flange, counter, faucet
X_SINK = X_IN
basin = lathe("Basin", [(0.95, 24.6), (3.2, 25.3), (5.4, 27.0), (6.6, 29.4), (7.0, 31.5), (7.7, 31.6), (7.7, 31.15), (7.3, 29.2), (6.0, 26.6), (3.6, 24.6), (1.0, 23.9)],
              M_CERAMIC, loc=(X_SINK, 0, 0))
flange = lathe("Flange", [(0.62, 24.3), (1.25, 24.62), (1.25, 24.75), (0.62, 24.75)], M_CHROME, loc=(X_SINK, 0, 0))
counter = [box("CounterL", -16.0, X_SINK - 7.4, 0, 12, 30.6, 32.0, M_COUNTER), box("CounterR", X_SINK + 7.4, 12.0, 0, 12, 30.6, 32.0, M_COUNTER),
           box("CounterB", X_SINK - 7.5, X_SINK + 7.5, 7.4, 12, 30.6, 32.0, M_COUNTER)]
fz = 32.0
faucet = [cyl("FaucetBase", 0.9, 0.6, "Z", (X_SINK, 9.0, fz + 0.3), M_CHROME), cyl("FaucetNeck", 0.45, 4.5, "Z", (X_SINK, 9.0, fz + 2.6), M_CHROME)]
bm = bmesh.new(); add_bar(bm, (X_SINK, 9.0, fz + 4.7), (X_SINK, 3.2, fz + 4.3), 0.7); add_bar(bm, (X_SINK, 3.4, fz + 4.4), (X_SINK, 3.0, fz + 3.6), 0.62)
faucet.append(mesh_obj("FaucetSpout", bm, M_CHROME))
# walls, floor, roof
dry = [box("DrywallLo", 11.0, 11.5, 0, 12, 0.0, 10.6, M_DRYWALL), box("DrywallHi", 11.0, 11.5, 0, 12, 12.9, 50.0, M_DRYWALL)]
floor = box("Floor", -70, 45, 0, 40, -2.0, 0.0, M_FLOOR)
back = box("BackWall", -70, 45, 12, 13, -30, 70, M_WALL)
roof = box("Roof", 2.0, 30.0, 0, 12, 50.0, 53.0, M_ROOF)
# the old S-trap (no vent), its own little set to the left
X0 = -42.0
ST_PATH = P_join(P_line((X0 + X_IN, 20.0), (X0 + X_IN, 10.0), 8), P_arc((X0, 10.0), 2.0, 180, 360, 30), P_line((X0 + 2.0, 10.0), (X0 + 2.0, 11.0), 2),
                 P_arc((X0 + 4.0, 11.0), 2.0, 180, 0, 30), P_line((X0 + 6.0, 11.0), (X0 + 6.0, -6.0), 10))
strap = half_pipe("STrap", ST_PATH, R0, R1, M_STRAP)
ST_W = P_join(P_line((X0 + X_IN, 13.0), (X0 + X_IN, 10.0), 4), P_arc((X0, 10.0), 2.0, 180, 360, 30), P_line((X0 + 2.0, 10.0), (X0 + 2.0, 11.0), 2),
              P_arc((X0 + 4.0, 11.0), 2.0, 180, 100, 10))
ST_LEVELS = [13.0 - R0, 11.0, 9.9, 9.0, 8.4, 7.75]
SWAT = [half_solid(f"SWater{k}", ST_W, R0 - 0.03, M_WATER, zcut=z) for k, z in enumerate(ST_LEVELS)]
s_basin = lathe("SBasin", [(0.95, 24.6), (3.2, 25.3), (5.4, 27.0), (6.6, 29.4), (7.0, 31.5), (7.7, 31.6), (7.7, 31.15), (7.3, 29.2), (6.0, 26.6), (3.6, 24.6), (1.0, 23.9)],
                M_CERAMIC, loc=(X0 + X_IN, 0, 0))
s_tail = half_pipe("STail", P_line((X0 + X_IN, 24.3), (X0 + X_IN, 19.5), 3), R0 - 0.12, R1 - 0.13, M_STRAP)

# ================= timing (beats) =================
T_CV0, T_CV1 = C["cut"] - 0.05, C["open"] + 0.4
T_NOTRAP0, T_NOTRAP1 = C["without"] + 0.1, C["but"] - 0.05          # water hidden: gas straight up the drain
T_SIPH0, T_SIPH1 = C["pull"] - 0.1, C["pull"] + 0.8                      # big rush pulls the seal down
T_RESET1 = C["thats"] - 0.12                                         # hard cut back to a full trap
T_SDRY0, T_SDRY1 = C["siphon2"] - 0.1, C["dry"] + 0.3
T_RING0, T_RING1 = C["dropr"] - 0.1, C["sinks"] + 0.8
T_JB0, T_JB1 = C["nuts"] + 0.1, C["nuts"] + 0.7
T_RESET2 = C["if"] - 0.12
T_DRY0, T_DRY1 = C["guest"], C["dried"] + 0.2
T_FILL0, T_FILL1 = C["water"] if False else C["run"] + 0.35, C["seal4"] + 0.1

def steps(t, t0, t1, a, b):
    """integer level stepping from a to b between t0 and t1"""
    u = lin((t - t0) / (t1 - t0)) if t1 > t0 else 1.0
    return int(round(a + (b - a) * u))
def level(t):
    if T_NOTRAP0 <= t < T_NOTRAP1: return 6
    if T_SIPH0 <= t < T_RESET1: return steps(t, T_SIPH0, T_SIPH1, 0, 4)
    if T_DRY0 <= t < T_FILL0: return steps(t, T_DRY0, T_DRY1, 0, 6)
    if T_FILL0 <= t: return steps(t, T_FILL0, T_FILL1, 6, 0)
    return 0
def slevel(t): return steps(t, T_SDRY0, T_SDRY1, 0, 5)
def bake_levels(objs, fn):
    for k, o in enumerate(objs):
        vals = [0.0 if fn(t) == k else 1.0 for t in TS]
        for path in ("hide_render", "hide_viewport"):
            o.keyframe_insert(path, frame=1)
            fc = fcurve(o, path, -1); fc.keyframe_points.clear()
            ch = [0] + [i for i in range(1, len(vals)) if vals[i] != vals[i - 1]]
            for i in ch:
                kp = fc.keyframe_points.insert(i + 1, vals[i]); kp.interpolation = "CONSTANT"
bake_levels(WAT, level); bake_levels(SWAT, slevel)
keyval(REDV.outputs[0], [(0, 0.0), (T_SIPH0 + 0.3, 0.0), (T_SIPH1, 1.0), (T_RESET1 - 0.01, 1.0), (T_RESET1, 0.0),
                         (T_SDRY0, 0.0), (T_SDRY1, 1.0), (C["trap3"] - 0.2, 1.0), (C["trap3"] - 0.19, 0.0),
                         (T_DRY0, 0.0), (T_DRY1, 0.8), (T_FILL0, 0.8), (T_FILL0 + 0.6, 0.0)])
keyval(WGLOW.outputs[0], [(0, 0.35)] + [(t, v) for t0, pk in ((C["full"] - 0.1, 2.2), (C["seal"] - 0.1, 3.0), (C["stays2"] - 0.2, 2.4),
                                                              (C["seal2"] - 0.1, 2.0), (C["put"] - 0.2, 2.4), (C["seal4"] - 0.1, 3.0))
                                         for t, v in pulse(t0, pk, base=0.35, hold=0.6)])
# J-bend drops on "nuts", back at the hard cut on "If"
bake_fn(JB, "location", 2, PW([(0, 0.0), (T_JB0, 0.0), (T_JB1, -4.5), (T_RESET2 - 0.01, -4.5), (T_RESET2, 0.0)]))
bake_fn(JB, "location", 1, PW([(0, 0.0), (T_JB0, 0.0), (T_JB1, -1.5), (T_RESET2 - 0.01, -1.5), (T_RESET2, 0.0)]))
# highlight pulses
glow(B_TAIL, [(0, 0.0)] + pulse(C["drops"] - 0.1, 1.6, hold=0.5))
glow(B_JB, [(0, 0.0)] + pulse(C["bends"] - 0.1, 1.6, hold=0.9) + pulse(C["ptrap"] - 0.1, 1.2, hold=0.7))
glow(B_ARM, [(0, 0.0)] + pulse(C["turns"] - 0.1, 1.6, hold=0.6))
glow(B_STACK, [(0, 0.0)] + pulse(C["sewer"] - 0.1, 1.3, hold=0.8))
glow(B_VENT, [(0, 0.0)] + pulse(C["vent"] - 0.1, 1.8, hold=1.4))
glow(B_NUT, [(0, 0.0)] + pulse(C["loosen"] - 0.05, 3.0, hold=0.5))
glow(B_RING, [(0, 1.6)] + pulse(C["there"] - 0.05, 5.0, base=1.6, hold=0.6))
glow(B_STRAP, [(0, 0.0)] + pulse(C["straps"] - 0.1, 1.2, hold=0.6))
# seal bracket for "two to four inches": weir line + dip line + a bar between them
BR = []
for nm, z in (("Weir", Z_WEIR), ("Dip", Z_DIP)):
    BR.append(box(f"Br{nm}", -3.6, 3.6, -1.3, -1.2, z - 0.04, z + 0.04, M_LINE))
BR.append(box("BrBar", -4.05, -3.97, -1.3, -1.2, Z_DIP, Z_WEIR, M_LINE))
for o in BR:
    bake_fn(o, "scale", 0, lambda t: max(0.001, ease((t - C["seal2"] + 0.1) / 0.35)))
    windows(o, [(C["seal2"] - 0.12, C["but2"] - 0.15)])
# "banned" cross over the S-trap
XB = []
for k, sgn in enumerate((1, -1)):
    bm = bmesh.new(); add_bar(bm, (X0 - 4.5, -2.0, 10.5 - sgn * 6.0), (X0 + 8.5, -2.0, 10.5 + sgn * 6.0), 0.55); XB.append(mesh_obj(f"BanX{k}", bm, M_ARROWR))
    bake_fn(XB[-1], "scale", 2, lambda t: max(0.001, ease((t - C["banned"] + 0.05) / 0.25)))
    windows(XB[-1], [(C["banned"] - 0.06, C["trap3"] - 0.2)])
# ring: drops in from the drain, tumbles down the tailpiece, settles at the bottom of the bend (parented to the J-bend rig)
def torus(name, R_, r_, m_, parent=None, seg=32, sseg=12):
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; c_ = Vector((R_ * math.cos(a), R_ * math.sin(a), 0)); d = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c_ + r_ * (math.cos(2 * math.pi * j / sseg) * d + math.sin(2 * math.pi * j / sseg) * Vector((0, 0, 1)))) for j in range(sseg)])
    for i in range(seg):
        A_, B_ = rings[i], rings[(i + 1) % seg]
        for j in range(sseg): bm.faces.new([A_[j], A_[(j + 1) % sseg], B_[(j + 1) % sseg], B_[j]])
    o = mesh_obj(name, bm, m_, parent)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
ring = torus("Ring", 0.38, 0.11, M_GOLDRING, parent=JB)
RING_PATH = [(X_IN, -0.12, 27.0), (X_IN, -0.12, 24.6), (X_IN, -0.12, 13.0), (X_IN, -0.12, 10.0)] + \
            [(2.45 * math.cos(math.radians(a)), -0.12, 10.0 + 2.45 * math.sin(math.radians(a))) for a in (200, 220, 240, 255, 270)]
def ring_pos(t):
    u = (t - T_RING0) / (T_RING1 - T_RING0)
    P = [Vector(p) for p in RING_PATH]; seg_ = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]; tot = sum(seg_)
    uu = lin(u); uu = 1 - (1 - uu) ** 1.6                 # fast at first, slows in the water
    d = uu * tot
    for i, s in enumerate(seg_):
        if d <= s or i == len(seg_) - 1: return P[i].lerp(P[i + 1], d / s if s else 0)
        d -= s
for ax in range(3): bake_fn(ring, "location", ax, lambda t, ax=ax: ring_pos(t)[ax] + (0.0 if ax != 2 else 0.2))
bake_fn(ring, "rotation_euler", 0, lambda t: math.radians(90) * (1 - ease((t - T_RING1 + 0.6) / 0.6)) + 4.0 * lin((t - T_RING0) / (T_RING1 - T_RING0 - 0.6)))
windows(ring, [(T_RING0, T_RESET2)])

# ================= hook cover: the front halves slide off on "cut" =================
cover = [half_pipe("CoverJB", JB_PATH, R0, R1, M_PVC, a0=math.pi), half_pipe("CoverTail", TAIL_PATH, R0 - 0.12, R1 - 0.13, M_PVC, a0=math.pi),
         half_pipe("CoverArm", ARM_PATH, R0, R1, M_PVC, a0=math.pi),
         half_pipe("CoverNut1", P_line((X_IN, 12.55), (X_IN, 13.45), 2), R1 - 0.01, R1 + 0.28, M_NUT, a0=math.pi, seg=24),
         half_pipe("CoverNut2", P_line((3.95, Z_ARM), (4.85, Z_ARM), 2), R1 - 0.01, R1 + 0.28, M_NUT, a0=math.pi, seg=24),
         lathe("CoverBasin", [(0.95, 24.6), (3.2, 25.3), (5.4, 27.0), (6.6, 29.4), (7.0, 31.5), (7.7, 31.6), (7.7, 31.15), (7.3, 29.2), (6.0, 26.6), (3.6, 24.6), (1.0, 23.9)],
               M_CERAMIC, a0=math.pi, loc=(X_SINK, 0, 0)),
         lathe("CoverFlange", [(0.62, 24.3), (1.25, 24.62), (1.25, 24.75), (0.62, 24.75)], M_CHROME, a0=math.pi, loc=(X_SINK, 0, 0)),
         box("CoverCounterL", -16.0, X_SINK - 7.4, -9, 0, 30.6, 32.0, M_COUNTER), box("CoverCounterR", X_SINK + 7.4, 12.0, -9, 0, 30.6, 32.0, M_COUNTER),
         box("CoverCounterF", X_SINK - 7.5, X_SINK + 7.5, -9, -7.4, 30.6, 32.0, M_COUNTER),
         box("CoverDrywall", 11.0, 11.5, -9, 0, 0.0, 50.0, M_DRYWALL)]
for o in cover:
    bake_fn(o, "location", 1, PW([(0, 0.0), (T_CV0, 0.0), (T_CV1, -40.0)]))
    bake_fn(o, "location", 2, PW([(0, 0.0), (T_CV0 + 0.1, 0.0), (T_CV1, -3.0)]))
    windows(o, [(0, T_CV1 + 0.05)])
# ================= flow: baked drops along paths =================
SPH = bpy.data.meshes.new("DropMesh")
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(SPH); bm.free()
for poly in SPH.polygons: poly.use_smooth = True
SPH.materials.append(M_DROPW)
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
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = m_ or M_DROPW
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
YW = 0.35
def xz(path, y=YW): return [(x, y, z) for x, z in path]
FAUCET = [(X_SINK, 3.1, fz + 3.4), (X_SINK, 2.0, 27.5), (X_SINK, 0.6, 25.0)]
DRAIN_TO_SEWER = xz(P_join(P_line((X_IN, 24.4), (X_IN, 10.0), 4), P_arc((0, 10.0), 2.0, 180, 360, 12), P_line((X_OUT, 10.0), (X_OUT, 10.55), 1),
                           P_arc((X_OUT + 1.2, 10.55), 1.2, 180, 90, 6), P_line((X_OUT + 1.2, Z_ARM), (XS, Z_ARM - 0.3), 4), P_line((XS, 10.8), (XS, -12.0), 4),
                           P_arc((XS + 1.6, -12.0), 1.6, 180, 270, 6), P_line((XS + 1.6, -13.6), (40.0, -13.6), 4)))
WATER_FULL = FAUCET + DRAIN_TO_SEWER
# hook + "most of the water flows on": a gentle stream through the trap
stream("Flow", WATER_FULL, 0.0, C["lets"] + 0.2, 22, 9.0, 0.16, M_DROPW, jitter=0.12)
stream("Flow2", WATER_FULL, C["most"] - 2.2, C["leftover"] + 0.4, 26, 9.0, 0.16, M_DROPW, jitter=0.12)
# sewer gas: from the sewer side, up the drain stack; part goes into the arm and stops on the water, part leaves through the vent
GAS_TO_TRAP = xz(P_join(P_line((40.0, -13.6), (XS + 1.6, -13.6), 4), P_arc((XS + 1.6, -12.0), 1.6, 270, 180, 6), P_line((XS, -12.0), (XS, Z_ARM), 6),
                        P_line((XS - 1.0, Z_ARM + 0.2), (X_OUT + 1.2, Z_ARM + 0.2), 5), P_arc((X_OUT + 1.2, 10.55), 1.0, 90, 160, 4), P_line((X_OUT + 0.15, 11.0), (X_OUT, Z_WEIR + 0.25), 1)), 0.4)
GAS_VENT = xz(P_join(P_line((40.0, -13.6), (XS + 1.6, -13.6), 4), P_arc((XS + 1.6, -12.0), 1.6, 270, 180, 6), P_line((XS, -12.0), (XS, 60.0), 12)), 0.4)
stream("Gas", GAS_TO_TRAP, C["past"] - 0.2, C["without"] + 0.2, 30, 6.5, 0.44, M_GASD, jitter=0.25, wobble=0.12)
stream("GasV", GAS_VENT, C["past"] - 0.2, C["without"] + 0.6, 22, 7.5, 0.44, M_GASD, jitter=0.25, wobble=0.12)
# no water: gas goes straight up the drain into the room
GAS_UP = xz(P_join(P_line((XS - 1.0, Z_ARM + 0.2), (X_OUT + 1.2, Z_ARM + 0.2), 5), P_arc((X_OUT + 1.2, 10.55), 1.2, 90, 180, 4), P_line((X_OUT, 10.55), (X_OUT, 10.0), 1),
                       P_arc((0, 10.0), 2.0, 360, 180, 12), P_line((X_IN, 10.0), (X_IN, 24.5), 6)), 0.4) + [(X_IN, 0.4, 28.0), (X_IN + 1.5, -2.0, 34.0)]
stream("GasUp", GAS_UP, T_NOTRAP0 - 0.4, T_NOTRAP1 + 1.6, 26, 9.0, 0.44, M_GASD, jitter=0.2, wobble=0.12)
# "gas can't push through water": gas reaches the water and stops there
stream("GasStop", GAS_TO_TRAP[-14:], C["but"] - 0.2, C["plumbing"] + 0.2, 16, 4.0, 0.44, M_GASD, jitter=0.2, wobble=0.08)
# big rush (siphon): heavy, fat drops fill the bore; the trap water is pulled along
RUSH = FAUCET + DRAIN_TO_SEWER
stream("Rush", RUSH, C["big"] - 0.8, C["thats"] - 0.1, 70, 13.0, 0.42, M_DROPW, jitter=0.18)
# vent beat: air comes down the vent to the tee while water drains, the trap stays full
AIR = xz(P_line((XS, 57.0), (XS, Z_ARM + 0.6), 10), 0.4)
stream("Air", AIR, C["lets"] if False else C["air"] - 1.8, C["put"] + 0.6, 34, 14.0, 0.22, M_AIR, jitter=0.35, wobble=0.1)
stream("Rush2", RUSH, C["air"] - 0.8, C["put"] + 0.5, 34, 13.0, 0.36, M_DROPW, jitter=0.18)
# S-trap: a rush of water pulls the seal out and down the floor leg
ST_FLOW = [(X0 + X_IN, YW, 24.4)] + xz([(x, z) for x, z in ST_PATH[::2]])
stream("SRush", ST_FLOW, C["old"] - 0.3, C["banned"] + 0.4, 40, 13.0, 0.36, M_DROPW, jitter=0.15)
# dried trap: gas comes up through the empty trap; running water refills it
stream("GasUp2", GAS_UP, C["dried"] - 0.6, T_FILL0 + 0.2, 24, 9.0, 0.44, M_GASD, jitter=0.2, wobble=0.12)
stream("Refill", WATER_FULL[:15], C["run"] - 0.15, C["have"] + 0.4, 30, 9.0, 0.16, M_DROPW, jitter=0.12)
stream("Refill2", WATER_FULL, C["seal4"] - 1.8, DUR + 4.0, 28, 9.0, 0.16, M_DROPW, jitter=0.12)
# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 600
ORB = lambda t, a0, a1, R_, cx, cy, z: (cx + R_ * math.sin(math.radians(a0 + (a1 - a0) * lin((t - C["have"]) / (DUR - C["have"])))),
                                         cy - R_ * math.cos(math.radians(a0 + (a1 - a0) * lin((t - C["have"]) / (DUR - C["have"])))), z)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-9.0, -26.0, 20.0), (0.0, 0.0, 15.5), 30),
    (C["lets"] - 0.3, (-6.0, -22.0, 18.5), (0.5, 0.0, 14.5), 30),
    (C["lets"] - 0.25, (2.0, -44.0, 19.0), (3.0, 0.0, 17.5), 30, "cut"),
    (C["most"] - 0.25, (1.0, -42.0, 18.0), (3.0, 0.0, 16.5), 30),
    (C["most"] - 0.2, (1.5, -17.0, 12.0), (1.0, 0.0, 10.4), 32, "cut"),
    (C["past"] - 0.25, (0.5, -15.5, 11.0), (1.0, 0.0, 10.2), 32),
    (C["past"] - 0.2, (7.0, -40.0, 6.0), (8.0, 0.0, 4.0), 28, "cut"),
    (C["without"] - 0.25, (6.0, -38.0, 7.0), (7.5, 0.0, 5.0), 28),
    (C["without"] - 0.2, (-2.0, -33.0, 19.0), (1.0, 0.0, 17.0), 30, "cut"),
    (C["but"] - 0.25, (-1.0, -31.0, 18.0), (1.0, 0.0, 16.5), 30),
    (C["but"] - 0.2, (5.5, -14.0, 13.0), (4.0, 0.0, 11.2), 32, "cut"),
    (C["plumbing"] - 0.25, (5.0, -13.0, 12.5), (3.8, 0.0, 11.0), 32),
    (C["plumbing"] - 0.2, (0.5, -16.0, 10.0), (0.3, 0.0, 9.9), 35, "cut"),
    (C["but2"] - 0.25, (0.2, -15.0, 10.0), (0.3, 0.0, 9.9), 35),
    (C["but2"] - 0.2, (3.0, -40.0, 18.0), (4.5, 0.0, 16.0), 30, "cut"),
    (C["thats"] - 0.25, (3.5, -38.0, 17.5), (4.5, 0.0, 15.5), 30),
    (C["thats"] - 0.2, (10.0, -38.0, 16.0), (11.0, 0.0, 16.0), 30, "cut"),
    (C["runs"], (10.0, -38.0, 18.0), (12.0, 0.0, 18.0), 30),
    (C["roof"] + 0.1, (14.0, -34.0, 44.0), (13.5, 0.0, 47.0), 30),
    (C["air"] + 0.2, (14.0, -34.0, 40.0), (13.5, 0.0, 42.0), 30),
    (C["trap2"], (5.0, -30.0, 16.0), (6.0, 0.0, 12.5), 30),
    (C["old"] - 0.25, (4.5, -28.0, 15.5), (6.0, 0.0, 12.5), 30),
    (C["old"] - 0.2, (X0 + 2.0, -30.0, 13.0), (X0 + 2.0, 0.0, 11.0), 30, "cut"),
    (C["trap3"] - 0.25, (X0 + 3.0, -28.0, 12.5), (X0 + 2.0, 0.0, 10.5), 30),
    (C["trap3"] - 0.2, (-3.0, -30.0, 19.0), (0.0, 0.0, 17.0), 30, "cut"),
    (C["sinks"] - 0.3, (-2.0, -28.0, 16.0), (0.0, 0.0, 14.0), 30),
    (C["bend2"], (0.5, -17.0, 10.0), (0.3, 0.0, 9.0), 32),
    (C["loosen"] - 0.1, (0.5, -17.0, 9.0), (0.3, 0.0, 8.5), 32),
    (C["nuts"] + 0.1, (1.5, -21.0, 8.0), (0.8, 0.0, 7.0), 30),
    (C["if"] - 0.25, (1.5, -21.0, 7.5), (0.8, 0.0, 6.5), 30),
    (C["if"] - 0.2, (-1.0, -36.0, 20.0), (1.0, 0.0, 18.0), 30, "cut"),
    (C["run"] - 0.1, (-1.5, -34.0, 19.5), (0.5, 0.0, 18.0), 30),
    (C["have"] - 0.25, (-1.5, -32.0, 19.0), (0.5, 0.0, 17.5), 30),
    (C["have"] - 0.2, (lambda t: ORB(t, -22, 18, 44.0, 3.0, 0.0, 22.0)[0], lambda t: ORB(t, -22, 18, 44.0, 3.0, 0.0, 22.0)[1], 22.0), (3.0, 0.0, 16.0), 30, "cut"),
    (C["end"], (lambda t: ORB(t, -22, 18, 44.0, 3.0, 0.0, 22.0)[0], lambda t: ORB(t, -22, 18, 44.0, 3.0, 0.0, 22.0)[1], 22.0), (3.0, 0.0, 16.0), 30),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        if callable(SHOTS[k][1][0]): u = 0.0      # orbit: follow the lambda
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
sun = bpy.data.lights.new("Key", "SUN"); sun.energy = 2.0; sun.color = (1.0, 0.93, 0.82); sun.angle = math.radians(5)
so = bpy.data.objects.new("Key", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(10), math.radians(-28))
sun2 = bpy.data.lights.new("Fill", "SUN"); sun2.energy = 0.7; sun2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("Fill", sun2); scene.collection.objects.link(so2); so2.rotation_euler = (math.radians(75), math.radians(-10), math.radians(150))
LT_A = target("LT_Face", (2.0, 0.0, 14.0)); area("Face", (-6.0, -48.0, 30.0), 28.0, 9000, (1.0, 0.96, 0.9), LT_A)
area("Top", (2.0, -10.0, 48.0), 12.0, 2500, (1.0, 0.95, 0.88), LT_A)
area("Low", (14.0, -30.0, -8.0), 14.0, 2500, (0.8, 0.88, 1.0), target("LT_Low", (8.0, 0.0, 0.0)))
area("Roof", (6.0, -30.0, 60.0), 14.0, 3000, (1.0, 0.95, 0.88), target("LT_Roof", (13.5, 0.0, 48.0)))
area("SSet", (X0 - 6.0, -30.0, 24.0), 16.0, 4000, (1.0, 0.96, 0.9), target("LT_S", (X0 + 2.0, 0.0, 10.0)))
area("CamFill", (0, 0, 0), 3.0, 80, (1.0, 0.96, 0.9), TGT).parent = cam

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
JBZ = PW([(0, 0.0), (T_JB0, 0.0), (T_JB1, -4.5), (T_RESET2 - 0.01, -4.5), (T_RESET2, 0.0)])
ANCH = {
    "tail": lambda t: Vector((X_IN - R1, -0.1, 18.0)),
    "jbend": lambda t: Vector((0.0, -0.1, 8.0 - R1)),
    "arm": lambda t: Vector((8.0, -0.1, Z_ARM + R1)),
    "water": lambda t: Vector((X_IN, -0.1, 10.0)),
    "seal": lambda t: Vector((X_OUT, -0.1, Z_WEIR)),
    "sewer": lambda t: Vector((30.0, -0.1, -13.6 - RS1)),
    "stack": lambda t: Vector((XS + RS1, -0.1, -4.0)),
    "vent": lambda t: Vector((XS + RS1, -0.1, 30.0)),
    "vent_top": lambda t: Vector((XS + RS1, -0.1, 52.5)),
    "strap": lambda t: Vector((X0 + 4.0, -0.1, 13.0 + R1)),
    "ring": lambda t: Vector((ring_pos(t)[0], 0.0, ring_pos(t)[2] + JBZ(t))),
    "nut1": lambda t: Vector((X_IN - R1 - 0.3, -0.1, 13.0 + JBZ(t))),
    "nut2": lambda t: Vector((4.4, -0.1, Z_ARM + R1 + 0.3 + JBZ(t))),
    "drain": lambda t: Vector((X_IN, -0.1, 25.0)),
}
anchors = {k: [] for k in ANCH}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):   # build_cover.py re-uses this scene and skips the export
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"cover": [round(T_CV0, 3), round(T_CV1, 3)], "notrap": [round(T_NOTRAP0, 3), round(T_NOTRAP1, 3)], "siphon": [round(T_SIPH0, 3), round(T_SIPH1, 3)],
          "reset1": round(T_RESET1, 3), "sdry": [round(T_SDRY0, 3), round(T_SDRY1, 3)], "ring": [round(T_RING0, 3), round(T_RING1, 3)],
          "jbend": [round(T_JB0, 3), round(T_JB1, 3)], "reset2": round(T_RESET2, 3), "dry": [round(T_DRY0, 3), round(T_DRY1, 3)],
          "fill": [round(T_FILL0, 3), round(T_FILL1, 3)], "drops": _drop_n[0]}
if not os.environ.get("COVER"): json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
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
