# Suspension-Bridge-P2-3D: how a suspension bridge is built, part 2 (cable bands, suspender ropes, deck sections lifted from a
# barge by a gantry crane riding on the main cables, balanced erection out from the towers, closure, safety net, load path).
# Blender Cycles, same real-world set as part 1: a sea strait between two rocky headlands in daylight, bridge along x,
# the two main cables at y = +-CY, camera mostly on -y.
# Cutaway: a separate cable-band set (a piece of main cable with one band, two suspender ropes) is cut at its middle plane; the near
# half slides away so the wires inside the cable and the band clamping round it show.
# Illustrative scale: spans shortened (main span 110, towers 72 high), cable drawn ~2x thick, bands every 2.75 units, deck 5.5-unit
# sections. The bridge is generic (orange towers, no logos, no people); the Golden Gate is named in the VO only.
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
DUR = round(WORDS[-1]["end"] + VO + 0.85, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(12)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("road", "road"), ("suspension", "suspension"), ("isnt", "isn't"), ("held", "held"), ("below", "below"), ("hangs", "hangs"),
        ("steel", "steel"), ("ropes", "ropes"), ("hundreds", "hundreds"), ("sea", "sea"), ("yesterday", "yesterday"), ("spun", "spun"),
        ("cables", "cables"), ("today", "today"), ("hang", "hang"), ("road2", "road"), ("lets", "let's"), ("cut", "cut"), ("first", "first"),
        ("cable", "cable"), ("bands", "bands"), ("steel2", "steel"), ("bands2", "bands"), ("clamped", "clamped"), ("around", "around"),
        ("each", "each"), ("cable2", "cable"), ("every", "every"), ("fifty", "fifty"), ("golden", "golden"), ("from", "from"),
        ("band", "band"), ("pair", "pair"), ("suspender", "suspender"), ("ropes2", "ropes"), ("drops", "drops"), ("thats", "that's"),
        ("two", "two"), ("fifty2", "fifty"), ("pairs", "pairs"), ("next", "next"), ("deck", "deck"), ("once", "once"), ("towers", "towers"),
        ("anchorages", "anchorages"), ("cables2", "cables"), ("road3", "road"), ("needs", "needs"), ("no", "no"), ("support", "support"),
        ("underneath", "underneath"), ("on", "on"), ("modern", "modern"), ("deck2", "deck"), ("sections", "sections"), ("arrive", "arrive"),
        ("barge", "barge"), ("gantry", "gantry"), ("crane", "crane"), ("rides", "rides"), ("train", "train"), ("rails", "rails"),
        ("grabs", "grabs"), ("section", "section"), ("lifts", "lifts"), ("straight", "straight"), ("up", "up"), ("hangers", "hangers"),
        ("hooked", "hooked"), ("crane2", "crane"), ("rolls", "rolls"), ("next2", "next"), ("spot", "spot"), ("sections2", "sections"),
        ("grow", "grow"), ("towers2", "towers"), ("balanced", "balanced"), ("meet", "meet"), ("middle", "middle"), ("then", "then"),
        ("joined", "joined"), ("one", "one"), ("continuous", "continuous"), ("road4", "road"), ("golden2", "golden"), ("net", "net"),
        ("caught", "caught"), ("nineteen", "nineteen"), ("workers", "workers"), ("fell", "fell"), ("now", "now"), ("every2", "every"),
        ("cars", "car's"), ("weight", "weight"), ("hangers2", "hangers"), ("cables3", "cables"), ("towers3", "towers"),
        ("anchorages2", "anchorages"), ("would", "would"), ("trust", "trust"), ("road5", "road"), ("hangs2", "hangs"), ("tell", "tell"),
        ("next3", "next"), ("water", "water"), ("towers4", "towers"), ("high", "high"), ("follow", "follow")]
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
CL = coll("Bridge")
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

def ground(name, rgb1, rgb2, scale=0.05):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    g = N.new("ShaderNodeNewGeometry"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 10
    L.new(g.outputs["Position"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].color = (*rgb1, 1); e[1].color = (*rgb2, 1)
    L.new(n.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def water_sec(name, glow_rgb=(0.30, 0.92, 1.0), vol_rgb=(0.16, 0.46, 0.62), dens=0.035):
    """Section water: clear tinted transmission (IOR 1.0) + a blue volume, emission keyable for glows."""
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.55, 0.85, 0.95, 1); b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.0; b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Emission Color"].default_value = (*glow_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (*vol_rgb, 1); va.inputs["Density"].default_value = dens
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.25, 0.62, 0.78, 1); vs.inputs["Density"].default_value = dens * 0.35
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Volume"])
    lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.85, 0.95, 1.0, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m, b, va
def surf_mat(name, rgb=(0.02, 0.12, 0.20)):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.14
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.35
    n.inputs["Detail"].default_value = 8; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m, b
def ghost(name, rgb):
    """Invisible until its 'Fac' value is keyed up: transparent -> glowing tint (for 'air' and 'displaced water')."""
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = 1.4
    ad = N.new("ShaderNodeAddShader"); L.new(tr.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    tr2 = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.0
    L.new(tr2.outputs[0], mx.inputs[1]); L.new(ad.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    tr.inputs["Color"].default_value = (0.75, 0.75, 0.75, 1)
    return m, mx.inputs[0]

def wire_face(name, rgb=(0.62, 0.64, 0.66), scale=14.0):
    """Cut face of a strand: Voronoi cells = the ends of the parallel wires (bright round wire ends, dark gaps)."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
    try: vo.inputs["Randomness"].default_value = 0.15
    except Exception: pass
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    try: vo.feature = "DISTANCE_TO_EDGE"
    except Exception: pass
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.02; mr.inputs[2].default_value = 0.10
    L.new(vo.outputs["Distance"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], (0.03, 0.03, 0.035), rgb)
    L.new(col, b.inputs["Base Color"]); b.inputs["Metallic"].default_value = 0.85; b.inputs["Roughness"].default_value = 0.32
    b.inputs["Emission Color"].default_value = (0.30, 0.92, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b

def stripes(name, rgb=(0.62, 0.64, 0.66), scale=1.6):
    """Long cut face of the main cable: thin bright bands along x = the parallel wires, dark gaps between them."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 0.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.25; mr.inputs[2].default_value = 0.55
    L.new(wv.outputs["Fac"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], (0.03, 0.03, 0.035), rgb)
    L.new(col, b.inputs["Base Color"]); b.inputs["Metallic"].default_value = 0.85; b.inputs["Roughness"].default_value = 0.32
    b.inputs["Emission Color"].default_value = (0.30, 0.92, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b

# ================= materials =================
M_CONC, B_CONC = mat("Concrete", (0.50, 0.49, 0.46), 0.85, emit_rgb=(0.30, 0.92, 1.0), noise=6.0)
M_TOWER, B_TOWER = mat("TowerPaint", (0.62, 0.13, 0.04), 0.5, 0.2, emit_rgb=(0.30, 0.92, 1.0))
M_DECKP, B_DECKP = mat("DeckPaint", (0.62, 0.13, 0.04), 0.5, 0.2, emit_rgb=(0.98, 0.74, 0.27))
M_ROAD = mat("Asphalt", (0.07, 0.07, 0.075), 0.8, noise=30.0)[0]
M_LANE = mat("LaneMark", (0.85, 0.85, 0.80), 0.6)[0]
M_SADDLE = mat("Saddle", (0.28, 0.29, 0.31), 0.35, 0.9)[0]
M_CABLE, B_CABLE = mat("Cable", (0.50, 0.52, 0.54), 0.4, 0.8, emit_rgb=(0.98, 0.74, 0.27))
M_BAND, B_BAND = mat("CableBand", (0.62, 0.13, 0.04), 0.4, 0.5, emit_rgb=(0.98, 0.74, 0.27))
M_HANG, B_HANG = mat("Hanger", (0.55, 0.12, 0.04), 0.45, 0.5, emit_rgb=(0.30, 0.92, 1.0))
M_BOLT, B_BOLT = mat("Bolt", (0.70, 0.71, 0.72), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
M_WIRE, B_WIRE = mat("HoistLine", (0.75, 0.80, 0.82), 0.25, 0.9, emit_rgb=(0.30, 0.92, 1.0)); B_WIRE.inputs["Emission Strength"].default_value = 2.5
M_GANTRY, B_GANTRY = mat("Gantry", (0.85, 0.62, 0.15), 0.35, 0.6, emit_rgb=(0.98, 0.74, 0.27))
M_BARGE = mat("Barge", (0.16, 0.17, 0.19), 0.6, 0.3)[0]
M_BARGE2 = mat("BargeDeck", (0.30, 0.25, 0.20), 0.8)[0]
M_NET, B_NET = mat("SafetyNet", (0.95, 0.85, 0.55), 0.6, emit_rgb=(0.98, 0.74, 0.27))
M_GOLD = mat("GoldBar", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27))[0]
bpy.data.materials["GoldBar"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.5
M_FACE, B_FACE = stripes("WireStripes")
M_ROCK = ground("Rock", (0.20, 0.18, 0.15), (0.38, 0.34, 0.28), 0.06)
M_GRASS = ground("Grass", (0.14, 0.20, 0.08), (0.28, 0.33, 0.14), 0.08)
M_SEA, B_SEA = surf_mat("Sea", (0.02, 0.11, 0.17))
M_GHOST, GH_FAC = ghost("GhostDeck", (0.30, 0.92, 1.0))
M_GHOST_R, GHR_FAC = ghost("GhostPiers", (1.0, 0.30, 0.24))
M_GHOST_S, GHS_FAC = ghost("GhostScaffold", (1.0, 0.30, 0.24))
CAR_RGB = [(0.75, 0.75, 0.78), (0.10, 0.10, 0.12), (0.55, 0.08, 0.06), (0.10, 0.22, 0.45), (0.85, 0.85, 0.82), (0.30, 0.32, 0.30)]
M_CARS = [mat(f"Car{i}", c, 0.25, 0.6)[0] for i, c in enumerate(CAR_RGB)]
M_HERO, B_HERO = mat("HeroCar", (0.85, 0.85, 0.82), 0.25, 0.6, emit_rgb=(0.98, 0.74, 0.27))
M_GLASS = mat("CarGlass", (0.02, 0.03, 0.04), 0.1, 0.2)[0]

# ================= layout (same bridge as part 1) =================
CY, TX, TH, AX = 7.0, 55.0, 72.0, 102.0     # cable y, tower x, tower top z, anchorage front x
LOW, AZ = 26.0, 14.0
LAND_X = 84.0
DZ0, DZ1 = 19.0, 20.6                       # deck girder bottom / road surface
DW = CY + 2.5                               # deck half width
SL = 5.5                                    # deck section length
DEND = TX + 6 * SL                          # deck end over land (88)
def cable_z(x):
    ax_ = abs(x)
    if ax_ <= TX: return LOW + (TH - LOW) * (x / TX) ** 2
    u = (ax_ - TX) / (AX - TX)
    return TH + (AZ - TH) * u - 4.0 * math.sin(math.pi * u)
XS = [-AX + i * 1.0 for i in range(int(2 * AX) + 1)]
def path(y, dz=0.0, x0=-AX, x1=AX): return [(x, y, cable_z(x) + dz) for x in XS if x0 - 1e-6 <= x <= x1 + 1e-6]
def slope(x): return math.atan2(cable_z(x + 0.5) - cable_z(x - 0.5), 1.0)
def curve(name, pts, depth, m_, res=6):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1.0)
    cu.bevel_depth = depth; cu.bevel_resolution = res; cu.use_fill_caps = True
    o = bpy.data.objects.new(name, cu); CL.objects.link(o)
    if m_: cu.materials.append(m_)
    return o

# ================= terrain + sea =================
SEA = box("Sea", -600, 600, -600, 600, -3.0, 0.0, M_SEA)
for s in (-1, 1):
    x0, x1 = (-400, -LAND_X) if s < 0 else (LAND_X, 400)
    box(f"Headland{s}", x0, x1, -150, 150, -20, 6.0, M_ROCK)
    box(f"HeadlandTop{s}", x0, x1, -150, 150, 6.0, 6.4, M_GRASS)
    bm = bmesh.new(); xf = s * LAND_X
    vs = [bm.verts.new(v) for v in [(xf, -150, 6.4), (xf, 150, 6.4), (xf - s * 10.0, 150, -3.0), (xf - s * 10.0, -150, -3.0),
                                    (xf, -150, -3.0), (xf, 150, -3.0)]]
    for f in ([0, 1, 2, 3], [0, 3, 4], [1, 5, 2], [3, 2, 5, 4]):
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj(f"Cliff{s}", bm, M_ROCK)
for i in range(7):
    x = -330 + i * 110 + random.uniform(-20, 20)
    o = cyl(f"Hill{i}", random.uniform(45, 80), 1.0, "Z", (0, 0, 0), M_GRASS, seg=24); o.location = (x, 520, -2); o.scale = (1.6, 1.0, random.uniform(28, 55))

# ================= anchorages, towers, saddles, main cables (finished in part 1) =================
AW0, AW1, AH = AX, AX + 26.0, 22.0
for s in (-1, 1):
    xa, xb = sorted((s * AW0, s * AW1)); box(f"Anchorage{s}", xa, xb, -14.0, 14.0, 6.0, 6.0 + AH, M_CONC)
    for yy in (-CY, CY):
        o = cyl(f"Splay{s}{yy}", 1.1, 2.6, "X", (s * (AW0 + 0.6), yy, AZ), M_SADDLE)
    # approach: deck end support on land (abutment pier) + approach slab up to the anchorage face
    box(f"Abutment{s}", *sorted((s * (DEND - 1.0), s * (DEND + 3.0))), -DW + 0.5, DW - 0.5, 6.0, DZ0, M_CONC)
    box(f"Approach{s}", *sorted((s * DEND, s * AW0)), -DW, DW, DZ0, DZ1 - 0.15, M_DECKP)
    box(f"ApproachRoad{s}", *sorted((s * DEND, s * AW0)), -DW + 0.6, DW - 0.6, DZ1 - 0.15, DZ1, M_ROAD)
TOWERS = []
for s in (-1, 1):
    box(f"Pier{s}", s * TX - 6, s * TX + 6, -12, 12, -3.0, 4.0, M_CONC)
    bm = bmesh.new()
    for yy in (-CY, CY): add_box(bm, s * TX - 2.2, s * TX + 2.2, yy - 2.2, yy + 2.2, 4.0, TH - 1.2)
    for zz in (16.0, 34.0, 50.0, TH - 8.0): add_box(bm, s * TX - 1.6, s * TX + 1.6, -CY, CY, 4.0 + zz, 4.0 + zz + 3.0)
    TOWERS.append(mesh_obj(f"Tower{s}", bm, M_TOWER))
    for yy in (-CY, CY):
        bm = bmesh.new(); add_box(bm, -2.6, 2.6, -1.8, 1.8, -0.6, 0.6); add_cyl(bm, 2.2, 3.4, "Y", (0, 0, 0.4), seg=24)
        o = mesh_obj(f"Saddle{s}{yy}", bm, M_SADDLE); o.location = (s * TX, yy, TH - 1.6)
CABLES = [curve(f"MainCable{yy}", path(yy), 1.0, M_CABLE) for yy in (-CY, CY)]

# ================= cable bands + suspender ropes (a pair per band) =================
BXS = [round(-DEND + 2.75 * i, 3) for i in range(int(2 * DEND / 2.75) + 1)]
BXS = [x for x in BXS if abs(abs(x) - TX) > 1.5 and abs(x) < DEND - 1.0]
BANDS, HANGS = [], []
for yy in (-CY, CY):
    for x in BXS:
        zc = cable_z(x)
        o = cyl(f"Band{yy}_{x}", 1.09, 0.6, "X", (0, 0, 0), M_BAND, seg=20); o.location = (x, yy, zc); o.rotation_euler = (0, -slope(x), 0)
        BANDS.append((o, x, yy))
        h = empty(f"Hanger{yy}_{x}", (x, yy, zc - 1.0))
        bm = bmesh.new()
        for dx in (-0.28, 0.28): add_box(bm, dx - 0.09, dx + 0.09, -0.09, 0.09, -1.0, 0.0)
        mesh_obj(f"HangerM{yy}_{x}", bm, M_HANG, h)
        HANGS.append((h, x, yy, zc - 1.0 - DZ1))          # length from the band down to the road surface

# ================= deck sections (box girder + road), balanced out from the towers =================
SECS = []      # (root, x_center, k, span) ; span "main" k 0..9 out from the tower, "side" k 0..5
def section(name, xc, ln):
    root = empty(name, (xc, 0, 0))
    bm = bmesh.new()
    add_box(bm, -ln / 2, ln / 2, -DW, DW, DZ0, DZ0 + 0.25)                      # bottom plate
    for yy in (-DW, DW): add_box(bm, -ln / 2, ln / 2, yy - 0.18 * (1 if yy > 0 else -1), yy, DZ0, DZ1 - 0.15)   # side walls
    for xx in (-ln / 2, ln / 2 - 0.2): add_box(bm, xx, xx + 0.2, -DW, DW, DZ0, DZ1 - 0.15)                    # diaphragms
    add_box(bm, -ln / 2, ln / 2, -DW, DW, DZ1 - 0.35, DZ1 - 0.15)                # deck plate
    g = mesh_obj(name + "G", bm, M_DECKP, root)
    bm = bmesh.new(); add_box(bm, -ln / 2, ln / 2, -DW + 0.6, DW - 0.6, DZ1 - 0.15, DZ1); mesh_obj(name + "R", bm, M_ROAD, root)
    bm = bmesh.new()
    for yy in (-0.1, 0.1): add_box(bm, -ln / 2 + 0.3, -0.4, yy - 0.06, yy + 0.06, DZ1, DZ1 + 0.02)
    for yy in (-3.3, 3.3): add_box(bm, -ln / 2 + 0.3, -ln / 2 + 1.8, yy - 0.06, yy + 0.06, DZ1, DZ1 + 0.02)
    mesh_obj(name + "L", bm, M_LANE, root)
    for yy in (-DW + 0.3, DW - 0.3): add_box(bm := bmesh.new(), -ln / 2, ln / 2, yy - 0.12, yy + 0.12, DZ1, DZ1 + 0.9); mesh_obj(name + f"Rail{yy}", bm, M_DECKP, root)
    return root
for s in (-1, 1):
    for k in range(10):
        xc = s * (TX - SL * (k + 0.5)); SECS.append((section(f"SecM{s}_{k}", xc, SL * 0.97), xc, k, "main"))
    for k in range(6):
        xc = s * (TX + SL * (k + 0.5)); SECS.append((section(f"SecS{s}_{k}", xc, SL * 0.97), xc, k, "side"))
# short tower stubs under the deck where it passes the tower (deck rests on the tower strut there)
for s in (-1, 1): box(f"TowerDeckStrut{s}", s * TX - 1.6, s * TX + 1.6, -DW, DW, DZ0 - 1.2, DZ0, M_TOWER)

# ================= cars =================
CARS, HERO = [], None
def car(name, x, y, m_):
    root = empty(name, (x, y, DZ1))
    bm = bmesh.new(); add_box(bm, -1.1, 1.1, -0.5, 0.5, 0.15, 0.75); mesh_obj(name + "B", bm, m_, root)
    bm = bmesh.new(); add_box(bm, -0.6, 0.55, -0.45, 0.45, 0.75, 1.15); mesh_obj(name + "C", bm, M_GLASS, root)
    return root
for i in range(18):
    x = -84 + i * 9.7 + random.uniform(-2.5, 2.5)
    if abs(x - (-4.0)) < 4: x += 6
    CARS.append(car(f"Car{i}", x, random.choice((-6.0, -2.3, 2.3, 6.0)), random.choice(M_CARS)))
HERO = car("HeroCar", -4.0, -2.3, M_HERO)

# ================= ghosts: piers that are NOT there (hook), scaffolding that is NOT needed, the road to come =================
GPIER = empty("GhostPiers"); bm = bmesh.new()
for x in (-36.0, -18.0, 0.0, 18.0, 36.0): add_box(bm, x - 2.0, x + 2.0, -5.0, 5.0, -3.0, DZ0)
mesh_obj("GhostPiersM", bm, M_GHOST_R, GPIER)
GSCAF = empty("GhostScaffold"); bm = bmesh.new()
for x in range(-50, 51, 6):
    for yy in (-6.0, 0.0, 6.0): add_box(bm, x - 0.35, x + 0.35, yy - 0.35, yy + 0.35, -3.0, DZ0)
for z in (4.0, 10.0, 16.0): add_box(bm, -50.5, 50.5, -6.3, -5.7, z, z + 0.5); add_box(bm, -50.5, 50.5, 5.7, 6.3, z, z + 0.5)
mesh_obj("GhostScaffoldM", bm, M_GHOST_S, GSCAF)
GDECK = empty("GhostDeck"); bm = bmesh.new(); add_box(bm, -DEND, DEND, -DW, DW, DZ0, DZ1); mesh_obj("GhostDeckM", bm, M_GHOST, GDECK)

# ================= barge, gantry crane, hoist lines (lift of section main k=2 at the left tower) =================
LIFT = next(r for r in SECS if r[3] == "main" and r[2] == 2 and r[1] < 0)
LX = LIFT[1]
BARGE = empty("Barge", (LX, 0, 0))
box("BargeHull", -4.2, 4.2, -12, 12, -1.0, 1.2, M_BARGE, BARGE); box("BargeDeck", -3.9, 3.9, -11.6, 11.6, 1.2, 1.3, M_BARGE2, BARGE)
for yy in (-10.5, 10.5): box(f"BargeBlock{yy}", -2.0, 2.0, yy - 0.6, yy + 0.6, 1.3, 2.0, M_BARGE, BARGE)
BZ = 2.0                                      # section bottom z while it rests on the barge (blocks)
GANT = empty("Gantry")
bm = bmesh.new()
for yy in (-CY, CY):
    add_box(bm, -2.4, 2.4, yy - 0.5, yy + 0.5, 1.2, 1.7)                      # truck on the cable
    add_box(bm, -2.0, -1.4, yy - 0.3, yy + 0.3, 1.7, 4.6); add_box(bm, 1.4, 2.0, yy - 0.3, yy + 0.3, 1.7, 4.6)
add_box(bm, -2.0, 2.0, -CY - 0.5, CY + 0.5, 4.6, 5.6)                          # cross beam
add_box(bm, -1.0, 1.0, -2.5, 2.5, 3.6, 4.6)                                    # winch house
GM = mesh_obj("GantryM", bm, M_GANTRY, GANT)
for yy in (-CY, CY):
    for dx in (-1.6, 1.6):
        o = cyl(f"GWheel{yy}{dx}", 0.55, 0.4, "Y", (dx, yy, 1.0), M_SADDLE, GANT, 16)
HOIST = []
for dx in (-1.8, 1.8):
    for yy in (-4.5, 4.5):
        h = empty(f"Hoist{dx}{yy}"); bm = bmesh.new(); add_box(bm, -0.07, 0.07, -0.07, 0.07, -1.0, 0.0); mesh_obj(f"HoistM{dx}{yy}", bm, M_WIRE, h)
        HOIST.append((h, dx, yy))
SPREAD = empty("Spreader"); box("SpreaderM", -2.4, 2.4, -5.0, 5.0, 0.0, 0.35, M_GANTRY, SPREAD)

# ================= safety net under the deck (Golden Gate: a net under the work) =================
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=90, y_segments=14, size=1.0)
bmesh.ops.scale(bm, vec=(22.0, 3.6, 1.0), verts=bm.verts)
for v in bm.verts: v.co.z = -0.9 * (1 - (v.co.y / 3.6) ** 2)          # sags in the middle
NET = mesh_obj("SafetyNet", bm, M_NET); NET.location = (-35.0, -DW - 3.0, DZ0 - 1.4)
wf = NET.modifiers.new("Wire", "WIREFRAME"); wf.thickness = 0.10; wf.use_replace = True
NETP = []
for x in range(-57, -12, 6):
    for yy in (-DW, -DW - 6.6): NETP.append(box(f"NetPost{x}{yy}", x - 0.08, x + 0.08, yy - 0.08, yy + 0.08, DZ0 - 2.3, DZ0 - 0.2, M_BOLT))

# ================= cable-band set (separate, far out over the sea behind the camera): cut at y = 0 =================
SET = Vector((0.0, -400.0, 30.0)); SX, SY, SZ = SET
RC, RB, BL = 3.6, 4.3, 3.2                      # cable radius, band outer radius, band length
def keep_side(bm, far=True):
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 1 if far else -1, 0), clear_inner=True)
    open_edges = [e for e in bm.edges if len(e.link_faces) < 2]
    if open_edges: bmesh.ops.edgeloop_fill(bm, edges=open_edges)
    for f in bm.faces:
        if all(abs(v.co.y) < 1e-4 for v in f.verts): f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
SFAR = empty("SetFar", SET); SNEAR = empty("SetNear", SET)
for far, root in ((True, SFAR), (False, SNEAR)):
    bm = bmesh.new(); add_cyl(bm, RC, 16.0, "X", (0, 0, 0), seg=48); keep_side(bm, far)
    mesh_obj(f"SetCable{far}", bm, [M_CABLE, M_FACE], root)
BANDQ = {}                                      # (top, far) -> object, quarter shells of the band
for top in (True, False):
    for far in (True, False):
        r = empty(f"BandQ{top}{far}", parent=SFAR if far else SNEAR)
        a0 = {(True, True): math.pi / 2, (True, False): math.pi, (False, True): 0.0, (False, False): -math.pi / 2}[(top, far)]
        q = lathe(f"BandQM{top}{far}", tube_prof(RC + 0.02, RB, -BL / 2, BL / 2), M_BAND, a0=a0, ang=math.pi / 2, seg=16)
        q.parent = r; q.matrix_parent_inverse = Matrix.Identity(4); q.rotation_euler = (0, math.pi / 2, 0)
        sgn = 1 if far else -1
        bm = bmesh.new(); add_box(bm, -BL / 2, BL / 2, sgn * (RB - 0.2), sgn * (RB + 1.0), 0.0 if top else -0.55, 0.55 if top else 0.0)
        mesh_obj(f"BandEar{top}{far}", bm, M_BAND, r)
        BANDQ[(top, far)] = r
BOLTS = []
for far in (True, False):
    sgn = 1 if far else -1
    for dx in (-0.9, 0.9):
        o = cyl(f"Bolt{far}{dx}", 0.22, 2.2, "Z", (0, 0, 0), M_BOLT, SFAR if far else SNEAR, 12); o.location = (dx, sgn * (RB + 0.45), 0.0)
        BOLTS.append((o, far))
LUG = empty("Lug", parent=BANDQ[(False, True)]); box("LugM", -0.7, 0.7, -0.45, 0.45, -RB - 1.6, -RB + 0.2, M_BAND, LUG)
SROPES = []
for dx in (-0.35, 0.35):
    o = box(f"SetRope{dx}", dx - 0.16, dx + 0.16, -0.16, 0.16, -60.0, -RB - 1.2, M_HANG, BANDQ[(False, True)]); SROPES.append(o)

# ================= timing =================
T_REC = C["yesterday"] - 0.05                       # hard cut: recap, cables only
T_SET0, T_CUT0, T_CUT1 = C["lets"] - 0.05, C["cut"], C["cut"] + 0.75
T_OP0, T_OP1 = C["steel2"] - 0.05, C["steel2"] + 0.35  # band opens ...
T_CL0, T_CL1 = C["clamped"], C["clamped"] + 0.22      # ... and clamps shut
T_BOLT = C["around"]
T_BR = C["every"] - 0.05                            # hard cut: bands along the bridge
T_BA0, T_BA1 = C["band"] - 0.0, C["band"] + 0.1
T_HD = C["drops"] - 0.1                             # hangers drop
T_PRE = C["on"] - 0.05                              # first sections already hung at the towers
T_BG0, T_BG1 = T_PRE, C["barge"] + 0.3              # barge comes in
T_GR0, T_GR1 = C["rides"], C["rails"] + 0.3         # gantry rides in on the cables
T_GB = C["grabs"]
T_L0, T_L1 = C["lifts"], C["up"] + 0.4
T_HK = C["hooked"]
T_RO0, T_RO1 = C["rolls"], C["spot"] + 0.3
T_MO = C["sections2"] - 0.1                         # balanced montage
T_JN = C["joined"]
T_NET = C["golden2"] - 0.25
T_NOW = C["now"] - 0.05
T_CTA = C["would"] - 0.1
def bands_t(x): return T_BR + 0.05 + 1.5 * (x + DEND) / (2 * DEND)
def hang_t(x): return T_HD + 0.8 * abs(x) / DEND
def sec_t(k, span):
    if span == "main": return T_PRE if k <= 1 else (T_L1 if k == 2 else T_MO + (k - 3) * 0.45)
    return T_PRE if k <= 1 else T_MO + (k - 2) * 0.7

# hook: the finished bridge; hidden from the recap on, rebuilt in order
for o, x, yy in BANDS:
    windows(o, [(0, T_REC), (bands_t(x), DUR)])
    for ax in range(3): bake_fn(o, "scale", ax, lambda t, x=x: 1.0 if t < T_REC else pop(t, bands_t(x), 0.25))
for h, x, yy, ln in HANGS:
    windows(h, [(0, T_REC), (hang_t(x), DUR)])
    bake_fn(h, "scale", 2, lambda t, x=x, ln=ln: ln if t < T_REC else max(0.02, ln * ease((t - hang_t(x)) / 0.35)))
def lift_z(t):
    if t < T_L0: return BZ - DZ0
    return (BZ - DZ0) * (1 - ease((t - T_L0) / (T_L1 - T_L0)))
def barge_y(t): return -60.0 * (1 - ease((t - T_BG0) / (T_BG1 - T_BG0)))
for root, xc, k, span in SECS:
    t0 = sec_t(k, span)
    if root is LIFT[0]:
        windows(root, [(0, T_REC), (T_PRE, DUR)])
        bake_fn(root, "location", 2, lambda t: 0.0 if t < T_REC else lift_z(t))
        bake_fn(root, "location", 1, lambda t: 0.0 if (t < T_REC or t >= T_L0) else barge_y(t))
    else:
        windows(root, [(0, T_REC), (t0, DUR)])
        if t0 > T_PRE: bake_fn(root, "location", 2, lambda t, t0=t0: 0.0 if t < T_REC else -14.0 * (1 - ease((t - t0) / 0.35)))
    bake_fn(root, "scale", 0, lambda t: 1.0 / 0.97 if (t < T_REC or t >= T_JN + 0.3) else (1.0 + (1.0 / 0.97 - 1.0) * ease((t - T_JN) / 0.3) if t >= T_JN else 1.0))
glow(B_DECKP, [(0, 0.0)] + pulse(C["continuous"], 1.3, hold=0.9))
# glows: hook hangers, recap cables, deck intro (towers / anchorages / cables), load path at the end
glow(B_HANG, [(0, 0.0)] + pulse(C["hangs"], 2.2, hold=1.2) + pulse(C["pairs"], 1.4, hold=0.6) + pulse(T_HK + 0.1, 2.5, hold=0.4)
     + pulse(C["hangers2"], 2.5, hold=3.2, down=0.8))
glow(B_CABLE, [(0, 0.0)] + pulse(C["spun"], 1.2, hold=1.2) + pulse(C["cables2"], 1.0, hold=0.6) + pulse(C["cables3"], 1.3, hold=2.4, down=0.8))
glow(B_TOWER, [(0, 0.0)] + pulse(C["towers"], 1.0, hold=0.5) + pulse(C["towers3"], 1.4, hold=1.6, down=0.8))
glow(B_CONC, [(0, 0.0)] + pulse(C["anchorages"], 0.9, hold=0.5) + pulse(C["anchorages2"], 1.2, hold=1.0, down=0.6))
glow(B_BAND, [(0, 0.0)] + pulse(C["bands"], 1.4, hold=0.6) + pulse(C["fifty"], 0.9, hold=0.8))
# ghosts
windows(GPIER, [(C["below"] - 0.35, C["hangs"] + 0.3)])
keyval(GHR_FAC, [(C["below"] - 0.35, 0.0), (C["below"], 0.85), (C["below"] + 0.5, 0.85), (C["hangs"] + 0.25, 0.0)])
windows(GSCAF, [(C["no"] - 0.3, T_PRE)])
keyval(GHS_FAC, [(C["no"] - 0.3, 0.0), (C["support"], 0.85), (C["underneath"] + 0.2, 0.85), (C["underneath"] + 0.7, 0.0)])
windows(GDECK, [(C["hang"] - 0.1, T_SET0)])
keyval(GH_FAC, [(C["hang"] - 0.1, 0.0), (C["road2"] + 0.1, 0.7), (T_SET0 - 0.05, 0.7)])
# barge, gantry, hoist lines, spreader
windows(BARGE, [(T_PRE, C["then"] - 0.05)])
bake_fn(BARGE, "location", 1, barge_y)
def gant_x(t):
    if t < T_GR0: return LX - 10.0
    if t < T_RO0: return LX - 10.0 + 10.0 * ease((t - T_GR0) / (T_GR1 - T_GR0))
    return LX + SL * ease((t - T_RO0) / (T_RO1 - T_RO0))
gant_z = lambda t: cable_z(gant_x(t))
windows(GANT, [(C["gantry"] - 0.1, T_MO)])
bake_fn(GANT, "location", 0, gant_x); bake_fn(GANT, "location", 2, gant_z)
bake_fn(GANT, "rotation_euler", 1, lambda t: -slope(gant_x(t)) * 0.5)
glow(B_GANTRY, [(0, 0.0)] + pulse(C["gantry"], 1.2, hold=0.5))
def sec_top(t): return DZ1 + lift_z(t)
def spread_z(t):
    up = gant_z(t) + 3.0
    if t < T_GB: return up
    if t < T_GB + 0.5: return up + (sec_top(t) - up) * ease((t - T_GB) / 0.5)
    if t < T_HK + 0.25: return sec_top(t)
    if t < T_HK + 0.85: return sec_top(t) + (up - sec_top(t)) * ease((t - T_HK - 0.25) / 0.6)
    return up
windows(SPREAD, [(C["gantry"] - 0.1, T_MO)])
bake_fn(SPREAD, "location", 0, gant_x); bake_fn(SPREAD, "location", 2, spread_z)
for h, dx, yy in HOIST:
    windows(h, [(C["gantry"] - 0.1, T_MO)])
    bake_fn(h, "location", 0, lambda t, dx=dx: gant_x(t) + dx); h.location.y = yy
    bake_fn(h, "location", 2, lambda t: gant_z(t) + 4.6)
    bake_fn(h, "scale", 2, lambda t: max(0.05, gant_z(t) + 4.6 - spread_z(t) - 0.35))
glow(B_WIRE, [(0, 2.5), (T_GB - 0.05, 2.5), (T_GB + 0.12, 6.0), (T_GB + 0.6, 2.5)])
# safety net
windows(NET, [(T_NET, T_NOW)])
for o in NETP: windows(o, [(T_NET, T_NOW)])
bake_fn(NET, "scale", 1, lambda t: max(0.02, ease((t - C["net"] + 0.1) / 0.4)))
glow(B_NET, [(0, 0.4)] + pulse(C["caught"], 2.0, hold=1.4, base=0.4))
# cars: in the hook and from the load path on; the hero car glows on "car's weight"
def car_x(x0, v, t): return ((x0 + v * t + 84.0) % 168.0) - 84.0
for o in CARS:
    x0, yy = o.location.x, o.location.y; v = 1.6 if yy < 0 else -1.6
    windows(o, [(0, T_REC), (T_NOW, DUR)])
    bake_fn(o, "location", 0, lambda t, x0=x0, v=v: car_x(x0, v, t))
    o.rotation_euler.z = 0.0 if v > 0 else math.pi
windows(HERO, [(0, T_REC), (T_NOW, DUR)])
bake_fn(HERO, "location", 0, lambda t: -4.0 + 0.5 * max(0.0, t - T_NOW) if t >= T_NOW else -4.0 + 0.5 * t)
glow(B_HERO, [(0, 0.0)] + pulse(C["cars"], 1.6, hold=1.0))
# cable-band set: closed, cut on "cut", band opens and clamps shut, bolts back in
for root in (SFAR, SNEAR): windows(root, [(T_SET0, T_BR)])
windows(SNEAR, [(T_SET0, T_CUT1 + 0.05)])
bake_fn(SNEAR, "location", 0, lambda t: SX + 30.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)))
bake_fn(SNEAR, "location", 2, lambda t: SZ - 50.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)) ** 2)
def band_open(t):
    if t < T_OP0: return 0.0
    if t < T_CL0: return 2.2 * ease((t - T_OP0) / (T_OP1 - T_OP0))
    return 2.2 * (1 - lin((t - T_CL0) / (T_CL1 - T_CL0)) ** 2)
for (top, far), r in BANDQ.items():
    if far: bake_fn(r, "location", 2, lambda t, top=top: band_open(t) * (1 if top else -1))
for o, far in BOLTS:
    if far:
        windows(o, [(T_SET0, T_OP0), (T_BOLT, T_BR)])
        for ax in range(3): bake_fn(o, "scale", ax, lambda t: 1.0 if t < T_OP0 else pop(t, T_BOLT, 0.25))
glow(B_FACE, [(0, 0.0)] + pulse(T_CUT1 - 0.1, 0.5, hold=0.6) + pulse(C["clamped"] + 0.1, 0.35, hold=0.3))
glow(B_BOLT, [(0, 0.0)] + pulse(T_BOLT, 1.6, hold=0.5))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.3; cam_d.clip_end = 2500
LZ = lambda dz: (lambda t: sec_top(t) + dz)
GX = lambda dx: (lambda t: gant_x(t) + dx)
HX = lambda dx: (lambda t: HERO_X(t) + dx)
HERO_X = lambda t: -4.0 + 0.5 * max(0.0, t - T_NOW)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-6.0, -26.0, 9.0), (6.0, 0.0, 24.0), 20),
    (C["hangs"] - 0.2, (-10.0, -36.0, 12.0), (4.0, 0.0, 30.0), 20),
    (C["hundreds"], (-12.0, -46.0, 10.0), (2.0, 0.0, 28.0), 20),
    (T_REC - 0.05, (30.0, -150.0, 4.0), (0.0, 0.0, 30.0), 20),
    (T_REC, (-125.0, -95.0, 22.0), (-20.0, 0.0, 44.0), 22, "cut"),
    (T_SET0 - 0.05, (-110.0, -80.0, 26.0), (-25.0, 0.0, 40.0), 22),
    (T_SET0, (SX + 14.0, SY - 24.0, SZ + 7.0), (SX, SY, SZ - 2.0), 35, "cut"),
    (C["first"], (SX + 12.0, SY - 23.0, SZ + 6.5), (SX, SY, SZ - 2.0), 35),
    (T_OP0 - 0.1, (SX + 10.5, SY - 22.5, SZ + 6.0), (SX, SY, SZ - 2.0), 35),
    (T_BR - 0.05, (SX + 9.0, SY - 22.0, SZ + 5.5), (SX, SY, SZ - 2.0), 35),
    (T_BR, (-45.0, -125.0, 44.0), (-45.0, 0.0, 42.0), 22, "cut"),
    (C["from"] - 0.05, (0.0, -125.0, 44.0), (0.0, 0.0, 40.0), 22),
    (C["from"], (-22.0, -36.0, 30.0), (2.0, -CY, 34.0), 22, "cut"),
    (C["thats"] - 0.2, (-18.0, -46.0, 26.0), (4.0, -CY, 30.0), 22),
    (C["next"] - 0.05, (0.0, -140.0, 10.0), (0.0, 0.0, 36.0), 20),
    (C["next"], (80.0, -160.0, 45.0), (0.0, 0.0, 30.0), 20, "cut"),
    (T_PRE - 0.05, (60.0, -140.0, 40.0), (0.0, 0.0, 28.0), 20),
    (T_PRE, (-26.0, -50.0, 6.0), (LX, -6.0, 8.0), 22, "cut"),
    (C["gantry"] - 0.1, (-25.0, -54.0, 8.0), (LX, 0.0, 12.0), 22),
    (C["rides"], (-28.0, -62.0, 30.0), (LX - 3.0, 0.0, 42.0), 22),
    (T_GB - 0.1, (-29.0, -64.0, 27.0), (LX, 0.0, 28.0), 22),
    (T_L0, (-29.0, -64.0, 24.0), (LX, 0.0, 26.0), 22),
    (T_L1, (-30.0, -60.0, 28.0), (LX, 0.0, 28.0), 22),
    (C["hangers"] - 0.05, (LX + 14.0, -34.0, 26.0), (LX, -CY, 22.0), 24, "cut"),
    (T_RO0 - 0.1, (LX + 14.0, -36.0, 28.0), (LX, -CY, 24.0), 24),
    (T_RO1 + 0.5, (LX + 22.0, -58.0, 46.0), (LX + 4.0, 0.0, 40.0), 22),
    (T_MO - 0.05, (70.0, -190.0, 95.0), (0.0, 0.0, 22.0), 20, "cut"),
    (C["then"] - 0.1, (50.0, -180.0, 80.0), (0.0, 0.0, 22.0), 20),
    (C["then"], (7.0, -24.0, 27.0), (0.0, 0.0, DZ1), 22, "cut"),
    (C["one"], (5.0, -40.0, 30.0), (0.0, 0.0, 22.0), 22),
    (T_NET - 0.05, (0.0, -140.0, 34.0), (0.0, 0.0, 26.0), 20),
    (T_NET, (-27.0, -28.0, 6.0), (-38.0, -DW - 3.0, 17.4), 20, "cut"),
    (T_NOW - 0.05, (-30.0, -27.0, 7.0), (-39.0, -DW - 3.0, 17.4), 20),
    (T_NOW, (HX(-8.0), -20.0, 25.0), (HX(0.0), -2.3, DZ1 + 0.6), 24, "cut"),
    (C["hangers2"], (HX(-10.0), -36.0, 30.0), (HX(0.0), -CY, 28.0), 22),
    (C["cables3"], (-8.0, -70.0, 45.0), (-15.0, 0.0, 45.0), 22),
    (C["towers3"], (0.0, -180.0, 40.0), (0.0, 0.0, 34.0), 20),
    (C["anchorages2"], (0.0, -240.0, 45.0), (0.0, 0.0, 30.0), 20),
    (T_CTA - 0.05, (0.0, -242.0, 45.0), (0.0, 0.0, 30.0), 20),
    (T_CTA, (30.0, -4.15, DZ1 + 2.2), (-55.0, -4.0, 58.0), 18, "cut"),
    (DUR, (18.0, -4.15, DZ1 + 2.2), (-55.0, -4.0, 58.0), 18),
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
    cam_loc.append(l0 + Vector((0.05 * math.sin(t * 0.7), 0.0, 0.04 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()
# ================= world + light: strait in daylight =================
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
try:
    sky = wn.new("ShaderNodeTexSky")
    for st_ in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try: sky.sky_type = st_; break
        except Exception: continue
    try: sky.sun_elevation = math.radians(28); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.22
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1); bg.inputs["Strength"].default_value = 0.8
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.2; sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(-18), math.radians(-30))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 40; fill_d.energy = 6000; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (10, 14, 0)

# ================= render settings =================
r = scene.render; r.engine = "CYCLES"
use_gpu = False
if "--cpu" not in ARGS and str(arg("--cycles-device", "")).upper() != "CPU":
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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4; scene.cycles.transparent_max_bounces = 16; scene.cycles.volume_bounces = 0
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
ANCHP = {
    "band": lambda t: Vector((-22.0, -CY - 1.2, cable_z(-22.0))),
    "hanger": lambda t: Vector((-8.25, -CY, (cable_z(-8.25) + DZ1) / 2)),
    "setband": lambda t: Vector((SX, SY - RB, SZ + 1.5)),
    "setwires": lambda t: Vector((SX - 9.0, SY, SZ + 1.0)),
    "setrope": lambda t: Vector((SX, SY, SZ - 9.0)),
    "barge": lambda t: Vector((LX, barge_y(t) - 12.0, 1.2)),
    "gantry": lambda t: Vector((gant_x(t), -CY, gant_z(t) + 5.0)),
    "section": lambda t: Vector((LX, -DW, DZ0 + lift_z(t) + 0.8)),
    "net": lambda t: Vector((-35.0, -DW - 6.0, DZ0 - 1.8)),
    "car": lambda t: Vector((HERO_X(t), -2.3, DZ1 + 1.2)),
    "cable": lambda t: Vector((-20.0, -CY, cable_z(-20.0))),
    "tower": lambda t: Vector((-TX, -CY - 2.2, 50.0)),
    "anchorage": lambda t: Vector((-AX - 13.0, -14.0, 28.0)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"recap": round(T_REC, 3), "set": round(T_SET0, 3), "cut": R3(T_CUT0, T_CUT1), "open": R3(T_OP0, T_OP1), "clamp": R3(T_CL0, T_CL1),
          "bolts": round(T_BOLT, 3), "bridge": round(T_BR, 3), "bands": R3(T_BR + 0.05, T_BR + 1.55),
          "band_pops": [round(T_BR + 0.05 + 1.5 * i / 11, 3) for i in range(12)], "hangers": R3(T_HD, T_HD + 0.8 + 0.35),
          "pre": round(T_PRE, 3), "barge": R3(T_BG0, T_BG1), "gantry_in": R3(T_GR0, T_GR1), "grab": round(T_GB, 3), "lift": R3(T_L0, T_L1),
          "hook": round(T_HK, 3), "roll": R3(T_RO0, T_RO1), "montage": round(T_MO, 3),
          "placements": sorted({round(sec_t(k, sp), 3) for _, _, k, sp in SECS if sec_t(k, sp) >= T_MO}),
          "join": round(T_JN, 3), "net": round(T_NET, 3), "now": round(T_NOW, 3), "cta": round(T_CTA, 3)}
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
    if "--range" in ARGS: scene.frame_start, scene.frame_end = [int(x) for x in arg("--range").split(",")]  # partial re-render
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
