# Water-Tower-3D: how a water tower works (gravity pressure from height, riser, night fill by pumps, morning drain, power outage,
# fire reserve, overflow). Blender Cycles, real-world set: a small town on flat ground in daylight (one night beat), generic elevated
# steel tank on four legs (no logos, no people), camera mostly on -y.
# Cutaway: the tower, its riser, the water main under the street, the pump house and the ground are cut at y = 0; the near half slides
# away so the water inside the tank and the pipes shows. A separate "pressure column" set (a clear tube of stacked water discs on a
# shower pipe with a gauge, then a wide tank of the same height with the same reading) shows that height, not width, sets the pressure.
# Illustrative scale: 1 unit = 1 m, tank bottom ~27 m (~90 ft) and top ~43 m (~140 ft); each disc in the column = 5 ft; levels and
# the fire-reserve band are illustrative.
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
CUES = [("water", "water"), ("towers", "towers"), ("dont", "don't"), ("pump", "pump"), ("house", "house."), ("gravity", "gravity"),
        ("does", "does,"), ("tank", "tank"), ("hundred", "hundred"), ("feet", "feet"), ("up", "up."), ("pressure", "pressure"),
        ("drops", "drops"), ("low", "low,"), ("states", "states"), ("boil", "boil"), ("lets", "let's"), ("cut", "cut"), ("open", "open."),
        ("first", "first,"), ("height", "height."), ("every", "every"), ("foot", "foot"), ("stacked", "stacked"), ("tap", "tap"),
        ("adds", "adds"), ("point", "point"), ("pounds", "pounds"), ("hundred2", "hundred"), ("feet2", "feet"), ("fortythree", "forty-three"),
        ("psi", "psi."), ("thats", "that's"), ("push", "push"), ("shower", "shower."), ("tanks", "tank's"), ("width", "width"),
        ("matter", "matter"), ("only", "only"), ("high", "high"), ("sits", "sits."), ("thats2", "that's"), ("tank2", "tank"),
        ("goes", "goes"), ("legs", "legs."), ("heightis", "height"), ("pressure2", "pressure."), ("inside", "inside,"), ("many", "many"),
        ("one", "one"), ("pipe", "pipe"), ("riser", "riser"), ("runs", "runs"), ("main", "main"), ("tank3", "tank."), ("at", "at"),
        ("night", "night,"), ("nobody", "nobody"), ("pumps", "pumps"), ("riser2", "riser"), ("fill", "fill"), ("tank4", "tank."),
        ("in", "in"), ("morning", "morning,"), ("everyone", "everyone"), ("showers", "showers"), ("once", "once."), ("pumps2", "pumps"),
        ("cant", "can't"), ("drains", "drains"), ("same", "same"), ("covers", "covers"), ("rush", "rush."), ("means", "means"),
        ("average", "average"), ("peak", "peak."), ("if", "if"), ("power", "power"), ("out", "out,"), ("gravity2", "gravity"),
        ("flowing", "flowing"), ("part", "part"), ("held", "held"), ("firefighters", "firefighters."), ("too", "too"), ("full", "full?"),
        ("overflow", "overflow"), ("dumps", "dumps"), ("extra", "extra."), ("would", "would"), ("climb", "climb"), ("ladder", "ladder"),
        ("top", "top"), ("tell", "tell"), ("next", "next"), ("nuclear", "nuclear"), ("boiling", "boiling"), ("follow", "follow")]
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
CL = coll("WaterTower")
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


# ================= timing =================
T_CUT0 = C["cut"] + 0.05; T_CUT1 = T_CUT0 + 0.8                 # near half slides away (1st time)
T_SET0 = C["first"] - 0.05; T_SET1 = C["thats2"] - 0.05          # pressure-column set
T_RISE0 = C["goes"] - 0.05; T_RISE1 = C["legs"] + 0.45           # tower rises on its legs
T_IN0 = C["inside"] + 0.05; T_IN1 = T_IN0 + 0.75                  # near half slides away (2nd time)
T_NI0 = C["at"] - 0.05; T_NI1 = T_NI0 + 0.5                       # day -> night
T_FILL0 = C["pumps"] + 0.3; T_FILL1 = C["in"] - 0.15               # pumps fill the tank
T_MO0 = C["in"] - 0.05; T_MO1 = T_MO0 + 0.5                       # night -> morning
T_DR0 = C["drains"]; T_DR1 = C["rush"] + 0.3                      # tank drains down the riser
T_PWR = C["out"]; T_GR0 = C["gravity2"]; T_GR1 = C["part"] - 0.1   # power out, gravity keeps it flowing
T_FULL0 = C["too"]; T_FULL1 = C["full"] + 0.55                    # too full
T_DUMP = C["dumps"]; T_CTA = C["would"]
ZRES = 30.4                                                      # top of the fire reserve (illustrative)
def level(t):
    """Water surface height (world z at full tower height) inside the tank."""
    if t < T_FILL0: return 35.2 if t < T_NI0 else 33.6
    if t < T_FILL1: return 33.6 + (38.0 - 33.6) * ease((t - T_FILL0) / (T_FILL1 - T_FILL0))
    if t < T_DR0: return 38.0
    if t < T_DR1: return 38.0 - (38.0 - 33.4) * ease((t - T_DR0) / (T_DR1 - T_DR0))
    if t < T_GR0: return 33.4
    if t < T_GR1: return 33.4 - 1.4 * ease((t - T_GR0) / (T_GR1 - T_GR0))
    if t < T_FULL0: return 32.0
    return 32.0 + (38.75 - 32.0) * ease((t - T_FULL0) / (T_FULL1 - T_FULL0))
def near_off(t):
    """0 = near half in place, 1 = slid away."""
    if t < T_CUT0: return 0.0
    if t < T_SET0: return ease((t - T_CUT0) / (T_CUT1 - T_CUT0))
    if t < T_IN0: return 0.0
    if t < T_CTA: return ease((t - T_IN0) / (T_IN1 - T_IN0))
    return 0.0
def rise(t):
    """Tower height factor: 0.28 (short legs) -> 1 on 'goes up on legs'."""
    if T_SET1 <= t < T_RISE1: return 0.28 + 0.72 * ease((t - T_RISE0) / (T_RISE1 - T_RISE0))
    return 1.0
def night(t):
    if t < T_NI0 or t >= T_MO1: return 0.0
    if t < T_NI1: return ease((t - T_NI0) / (T_NI1 - T_NI0))
    if t < T_MO0: return 1.0
    return 1.0 - ease((t - T_MO0) / (T_MO1 - T_MO0))

# ================= materials =================
M_PAINT, B_PAINT = mat("TowerPaint", (0.78, 0.84, 0.88), 0.35, 0.3, emit_rgb=(1.0, 0.30, 0.24))
M_STEELIN = mat("TankInside", (0.30, 0.32, 0.34), 0.5, 0.6)[0]
M_PIPE, B_PIPE = mat("PipeSteel", (0.22, 0.30, 0.38), 0.35, 0.7, emit_rgb=(0.30, 0.92, 1.0))
M_MAIN, B_MAIN = mat("MainPipe", (0.18, 0.20, 0.24), 0.45, 0.4, emit_rgb=(0.30, 0.92, 1.0))
M_OVF, B_OVF = mat("OverflowPipe", (0.26, 0.30, 0.34), 0.35, 0.7, emit_rgb=(0.30, 0.92, 1.0))
M_SOIL = ground("Soil", (0.16, 0.10, 0.06), (0.30, 0.20, 0.12), 0.35)
M_GRASS = ground("Grass", (0.10, 0.20, 0.06), (0.24, 0.34, 0.12), 0.08)
M_ROAD = mat("Asphalt", (0.06, 0.06, 0.065), 0.8, noise=30.0)[0]
M_WALL, B_WALL = mat("HouseWall", (0.80, 0.74, 0.64), 0.7, emit_rgb=(1.0, 0.30, 0.24))
M_WALL2 = mat("HouseWall2", (0.62, 0.70, 0.74), 0.7)[0]
M_ROOF = mat("Roof", (0.24, 0.12, 0.10), 0.6)[0]
M_WIN, B_WIN = mat("Window", (0.05, 0.07, 0.09), 0.1, 0.3, emit_rgb=(1.0, 0.82, 0.55))
M_PH = mat("PumpHouse", (0.55, 0.52, 0.48), 0.8, noise=8.0)[0]
M_PUMP, B_PUMP = mat("Pump", (0.10, 0.32, 0.55), 0.35, 0.5, emit_rgb=(0.98, 0.74, 0.27))
M_IMP = mat("Impeller", (0.75, 0.62, 0.30), 0.3, 0.9)[0]
M_HYD, B_HYD = mat("Hydrant", (0.75, 0.10, 0.06), 0.4, 0.2, emit_rgb=(1.0, 0.30, 0.24))
M_GOLD, B_GOLD = mat("GoldBar", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27))
M_ARROW, B_ARROW = mat("FlowArrow", (0.30, 0.92, 1.0), 0.3, emit_rgb=(0.30, 0.92, 1.0)); B_ARROW.inputs["Emission Strength"].default_value = 3.0
M_GARROW, B_GARROW = mat("GravityArrow", (0.98, 0.74, 0.27), 0.3, emit_rgb=(0.98, 0.74, 0.27)); B_GARROW.inputs["Emission Strength"].default_value = 2.5
M_LAMP, B_LAMP = mat("Lamp", (0.9, 0.85, 0.7), 0.3, emit_rgb=(1.0, 0.80, 0.50))
M_POLE = mat("Pole", (0.15, 0.15, 0.16), 0.5, 0.6)[0]
M_TILE = tiles("Tiles", (0.78, 0.80, 0.80), (0.70, 0.73, 0.74), 0.9)
M_TILEF = tiles("FloorTiles", (0.30, 0.32, 0.34), (0.26, 0.28, 0.30), 0.6, plane="XY")
M_CHROME = mat("Chrome", (0.85, 0.86, 0.88), 0.12, 1.0)[0]
M_DIAL = mat("Dial", (0.95, 0.95, 0.92), 0.4)[0]
M_NEEDLE = mat("Needle", (0.9, 0.12, 0.08), 0.4, emit_rgb=(1.0, 0.30, 0.24))[0]
M_CONC = mat("Concrete", (0.50, 0.49, 0.46), 0.85, noise=6.0)[0]
M_TREE = mat("Tree", (0.08, 0.20, 0.07), 0.8)[0]
M_TRUNK = mat("Trunk", (0.20, 0.13, 0.08), 0.8)[0]
def glass(name):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.9, 0.97, 1.0, 1); b.inputs["Roughness"].default_value = 0.03
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.2
    return m
M_GLASS = glass("Glass")
def water_mat(name, fire=False):
    """Opaque-ish water for cut sections; emission cyan, keyable; with fire=True the part below ZRES can glow red."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    b.inputs["Base Color"].default_value = (0.01, 0.13, 0.36, 1); b.inputs["Roughness"].default_value = 0.35
    b.inputs["Specular IOR Level"].default_value = 0.6
    if fire:
        tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
        lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = ZRES; L.new(sp.outputs["Z"], lt.inputs[0])
        fv = N.new("ShaderNodeValue"); fv.name = "FireFac"
        mu = N.new("ShaderNodeMath"); mu.operation = "MULTIPLY"; L.new(lt.outputs[0], mu.inputs[0]); L.new(fv.outputs[0], mu.inputs[1])
        col = mix_rgb(nt, mu.outputs[0], (0.30, 0.92, 1.0), (1.0, 0.25, 0.18)); L.new(col, b.inputs["Emission Color"])
        fv.outputs[0].default_value = 0.0
        return m, b, fv.outputs[0]
    b.inputs["Emission Color"].default_value = (0.30, 0.92, 1.0, 1)
    return m, b, None
M_WAT, B_WAT, FIREFAC = water_mat("TankWater", fire=True)
M_PWAT, B_PWAT, _ = water_mat("PipeWater")
M_SWAT, B_SWAT, _ = water_mat("SetWater"); B_SWAT.inputs["Emission Strength"].default_value = 0.35

# ================= hierarchy: far half stays, near half slides away; TOP = tank (moves up), LEGS = scales in z =================
FAR = empty("Far"); NEAR = empty("Near")
FAR_TOP = empty("FarTop", parent=FAR); FAR_LEGS = empty("FarLegs", parent=FAR)
NEAR_TOP = empty("NearTop", parent=NEAR); NEAR_LEGS = empty("NearLegs", parent=NEAR)

# ---- tank shell (lathe of the wall section), far half a0=0..pi (y>=0), near half pi..2pi ----
OUT = [(0.0, 27.3), (2.5, 27.45), (4.8, 28.0), (6.6, 29.0), (7.7, 30.4), (8.0, 31.6), (8.0, 39.2), (4.0, 41.4), (0.0, 42.6)]
INN = [(0.0, 27.6), (2.5, 27.75), (4.7, 28.3), (6.4, 29.3), (7.4, 30.6), (7.7, 31.7), (7.7, 39.0), (3.9, 41.1), (0.0, 42.3)]
SHELL = OUT + INN[::-1]
SH_F = lathe("TankShellFar", SHELL, [M_PAINT], a0=0.0, ang=math.pi, seg=48); SH_F.parent = FAR_TOP
SH_N = lathe("TankShellNear", SHELL, [M_PAINT], a0=math.pi, ang=math.pi, seg=48); SH_N.parent = NEAR_TOP
# inside of the shell reads as bare steel: second material on faces whose normal points to the axis
def inner_faces(o):
    o.data.materials.append(M_STEELIN)
    for p in o.data.polygons:
        c = p.center; r = math.hypot(c.x, c.y)
        if r > 0.3 and abs(p.normal.z) < 0.95 and (p.normal.x * c.x + p.normal.y * c.y) < 0 and r < 7.85: p.material_index = 1
inner_faces(SH_F)
# finial on the roof
FIN = full_cyl("Finial", 0.25, 0, 0, 42.4, 43.6, M_PAINT); FIN.parent = FAR_TOP
# ---- water inside the tank (far half only, level = boolean intersect with a keyed box) ----
WPROF = [(0.0, 27.6)] + INN[1:7] + [(0.0, 39.0)]
WAT = lathe("TankWater", WPROF, [M_WAT], a0=0.0, ang=math.pi, seg=48, smooth=False); WAT.parent = FAR_TOP
LVL = box("LevelBox", -20, 20, -1, 20, -40, 0, M_WAT, FAR_TOP); LVL.hide_render = True; LVL.display_type = "WIRE"
bm_ = WAT.modifiers.new("Level", "BOOLEAN"); bm_.operation = "INTERSECT"; bm_.object = LVL
try: bm_.solver = "EXACT"
except Exception: pass
bake_fn(LVL, "location", 2, level)
# ---- balcony (catwalk ring) at the bottom of the wall ----
BAL = [(8.0, 31.35), (9.5, 31.35), (9.5, 31.6), (8.0, 31.6)]
RAIL = [(9.35, 32.6), (9.5, 32.6), (9.5, 32.75), (9.35, 32.75)]
for nm, prof in (("Balcony", BAL), ("Rail", RAIL)):
    lathe(nm + "Far", prof, [M_PAINT], 0.0, math.pi, 64).parent = FAR_TOP
    lathe(nm + "Near", prof, [M_PAINT], math.pi, math.pi, 64).parent = NEAR_TOP
# ---- legs + braces ----
def add_tube(bm, p0, p1, r, seg=12, mi=0):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length); vs = res["verts"]
    M = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
LEGB, LEGT = 7.4, 5.7
LEGXY = [(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]
def leg_pt(sx, sy, z): k = z / 31.0; return (sx * (LEGB + (LEGT - LEGB) * k), sy * (LEGB + (LEGT - LEGB) * k), z)
bmf, bmn = bmesh.new(), bmesh.new()
for sx, sy in LEGXY:
    add_tube(bmf if sy > 0 else bmn, leg_pt(sx, sy, 0), leg_pt(sx, sy, 31.4), 0.45, 16)
for z0, z1 in ((0.5, 10.5), (10.5, 20.5), (20.5, 30.5)):
    # back face (y>0) braces stay; front + side faces go with the near half
    for (a, b_), tgt in ((((-1, 1), (1, 1))), bmf), ((((-1, -1), (1, -1))), bmn), ((((-1, -1), (-1, 1))), bmn), ((((1, -1), (1, 1))), bmn):
        add_tube(tgt, leg_pt(*a, z1), leg_pt(*b_, z1), 0.16, 8)
        add_tube(tgt, leg_pt(*a, z0), leg_pt(*b_, z1), 0.09, 6); add_tube(tgt, leg_pt(*b_, z0), leg_pt(*a, z1), 0.09, 6)
mesh_obj("LegsFar", bmf, M_PAINT, FAR_LEGS); mesh_obj("LegsNear", bmn, M_PAINT, NEAR_LEGS)
# footings
for sx, sy in LEGXY:
    box(f"Footing{sx}{sy}", sx * LEGB - 1.0, sx * LEGB + 1.0, sy * LEGB - 1.0, sy * LEGB + 1.0, -0.6, 0.35, M_CONC, FAR if sy > 0 else NEAR)
# ladder up the near-right leg, then up the tank wall to the roof (for the CTA climb)
bm = bmesh.new()
lad = lambda z: Vector(leg_pt(1, -1, z)) + Vector((-0.9, 0.0, 0.0))
for side in (-0.35, 0.35):
    add_tube(bm, lad(0.3) + Vector((side, -0.55, 0)), lad(31.3) + Vector((side, -0.55, 0)), 0.06, 6)
for k in range(1, 104):
    z = 0.3 * k
    add_tube(bm, lad(z) + Vector((-0.35, -0.55, 0)), lad(z) + Vector((0.35, -0.55, 0)), 0.04, 5)
mesh_obj("Ladder", bm, M_PAINT, NEAR_LEGS)
# ---- riser: half pipes (far keeps y>=0), water inside; near half for the intact look ----
RR0, RR1, RZ0, RZ1 = 0.85, 1.05, -3.5, 27.7
lathe("RiserFar", tube_prof(RR0, RR1, RZ0, RZ1), [M_PIPE], 0.0, math.pi, 32).parent = FAR_LEGS
lathe("RiserNear", tube_prof(RR0, RR1, 0.0, RZ1), [M_PIPE], math.pi, math.pi, 32).parent = NEAR_LEGS
lathe("RiserWater", [(0, RZ0), (RR0, RZ0), (RR0, RZ1 + 0.1), (0, RZ1 + 0.1)], [M_PWAT], 0.0, math.pi, 32, smooth=False).parent = FAR_LEGS
# ---- water main along x (under the street), far half, + elbow region at the riser ----
MR0, MR1, MZ, MX0, MX1 = 0.5, 0.65, -3.5, -22.0, 80.0
def xpipe(name, prof, m_, parent):
    o = lathe(name, prof, [m_], 0.0, math.pi, 32, smooth=False); o.rotation_euler = (0, math.radians(90), 0)
    o.location = (0, 0, MZ); o.parent = parent; return o
# rotating +90 about y maps the lathe axis (local z) to world +x and keeps y, so the half a0=0..pi stays at y >= 0
MAINP = xpipe("MainPipe", tube_prof(MR0, MR1, MX0, MX1), M_MAIN, FAR)
MAINW = xpipe("MainWater", [(0, MX0), (MR0, MX0), (MR0, MX1), (0, MX1)], M_PWAT, FAR)
# ---- pump house + pump (x = -18) ----
PX = -18.0
box("PHFloor", PX - 5, PX + 5, 0, 6, 0, 0.3, M_CONC, FAR); box("PHFloorN", PX - 5, PX + 5, -4, 0, 0, 0.3, M_CONC, NEAR)
box("PHBack", PX - 5, PX + 5, 5.6, 6, 0.3, 5.0, M_PH, FAR)
for xx in (PX - 5, PX + 4.6):
    box(f"PHSide{xx}", xx, xx + 0.4, 0, 6, 0.3, 5.0, M_PH, FAR); box(f"PHSideN{xx}", xx, xx + 0.4, -4, 0, 0.3, 5.0, M_PH, NEAR)
box("PHRoof", PX - 5.3, PX + 5.3, 0, 6.3, 5.0, 5.5, M_ROOF, FAR); box("PHRoofN", PX - 5.3, PX + 5.3, -4.3, 0, 5.0, 5.5, M_ROOF, NEAR)
box("PHFront", PX - 5, PX + 5, -4, -3.6, 0.3, 5.0, M_PH, NEAR)
box("PHDoor", PX - 1.2, PX + 1.2, -4.08, -3.98, 0.3, 3.2, M_ROOF, NEAR)
PUMPR = empty("PumpRoot", (PX, 0, 0), FAR)
lathe("PumpCasing", tube_prof(1.2, 1.45, 0.35, 1.6), [M_PUMP], 0.0, math.pi, 32).parent = PUMPR
lathe("PumpLid", [(0, 1.6), (1.45, 1.6), (1.45, 1.8), (0, 1.8)], [M_PUMP], 0.0, math.pi, 32).parent = PUMPR
lathe("PumpMotor", [(0, 1.8), (0.95, 1.8), (0.95, 4.0), (0, 4.0)], [M_PUMP], 0.0, math.pi, 32).parent = PUMPR
IMP = empty("Impeller", (0, 0, 0.95), PUMPR); bm = bmesh.new()
add_cyl(bm, 0.35, 0.9, "Z", (0, 0, 0))
for k in range(6):
    a = k * math.pi / 3; add_bar(bm, (0.3 * math.cos(a), 0.3 * math.sin(a), 0), (1.1 * math.cos(a + 0.4), 1.1 * math.sin(a + 0.4), 0), 0.14)
mesh_obj("ImpellerM", bm, M_IMP, IMP)
lathe("PumpDown", tube_prof(0.35, 0.5, MZ, 0.35), [M_PIPE], 0.0, math.pi, 24).location = (PX, 0, 0)
bpy.data.objects["PumpDown"].parent = FAR
# ---- overflow pipe outside the tank: from near the top of the wall down the outside, outlet above a drain ----
OVX, OVZ0, OVZ1 = 9.0, 3.2, 38.8
OVF = empty("Overflow", (0, 0, 0), FAR)
bm = bmesh.new(); add_tube(bm, (OVX, 0.3, OVZ0), (OVX, 0.3, OVZ1), 0.42, 20); add_tube(bm, (7.6, 0.3, OVZ1), (OVX + 0.42, 0.3, OVZ1), 0.42, 20)
add_tube(bm, (OVX, 0.3, OVZ0), (OVX + 0.9, 0.3, OVZ0 - 0.5), 0.42, 20)
OVP = mesh_obj("OverflowPipe", bm, M_OVF, OVF)
box("Drain", OVX - 0.5, OVX + 3.0, -0.8, 1.6, -0.25, 0.08, M_CONC, FAR)
SPILL = empty("Spill", (OVX + 1.2, 0.3, 0), FAR); bm = bmesh.new()
for k in range(5):
    add_tube(bm, (0.15 * k - 0.3, 0.12 * ((k * 7) % 3 - 1), OVZ0 - 0.7), (0.35 * k - 0.4, 0.2 * ((k * 5) % 3 - 1), 0.1), 0.12 + 0.03 * (k % 2), 8)
add_cyl(bm, 1.1, 0.08, "Z", (0, 0, 0.1))
mesh_obj("SpillM", bm, M_ARROW, SPILL)

# ================= ground (cut at y = 0), street, houses, hydrant, lamps, trees =================
def ground_block(name, y0, y1, parent):
    bm = bmesh.new(); add_box(bm, -1500, 1500, y0, y1, -90.0, 0.0)
    o = mesh_obj(name, bm, [M_SOIL, M_GRASS], parent)
    for p in o.data.polygons:
        if p.normal.z > 0.9: p.material_index = 1
    return o
GF = ground_block("GroundFar", 0.0, 1500.0, FAR); GN = ground_block("GroundNear", -450.0, 0.0, NEAR)
CUTTERS = []
for nm, loc, r_, d_, ax in (("CutMain", ((MX0 + MX1) / 2, 0, MZ), MR1 + 0.03, MX1 - MX0 + 0.4, "X"), ("CutRiser", (0, 0, -1.7), RR1 + 0.03, 4.4, "Z"),
                            ("CutPump", (PX, 0, -1.7), 0.53, 4.4, "Z")):
    c = cyl(nm, r_, d_, ax, loc, M_SOIL, seg=32); c.hide_render = True; c.display_type = "WIRE"; CUTTERS.append(c)
for c in CUTTERS:
    md = GF.modifiers.new(c.name, "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = c
    try: md.solver = "EXACT"
    except Exception: pass
box("StreetFar", -260, 260, 0, 4.0, 0.0, 0.06, M_ROAD, FAR); box("StreetNear", -260, 260, -3.0, 0, 0.0, 0.06, M_ROAD, NEAR)
HOUSES = []
def house(name, x, y, w, d, h, parent, wall=M_WALL):
    root = empty(name, (x, y, 0), parent)
    box(name + "Body", -w / 2, w / 2, -d / 2, d / 2, 0, h, wall, root)
    bm = bmesh.new(); rh = 2.2
    v = [bm.verts.new(p) for p in ((-w / 2 - 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, -d / 2 - 0.3, h), (w / 2 + 0.3, 0, h + rh), (-w / 2 - 0.3, 0, h + rh),
                                    (-w / 2 - 0.3, d / 2 + 0.3, h), (w / 2 + 0.3, d / 2 + 0.3, h))]
    for f in ((v[0], v[1], v[2], v[3]), (v[3], v[2], v[5], v[4]), (v[0], v[3], v[4]), (v[1], v[5], v[2]), (v[0], v[4], v[5], v[1])): bm.faces.new(f)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj(name + "Roof", bm, M_ROOF, root)
    bm = bmesh.new()
    for wx in (-w / 4, w / 4):
        add_box(bm, wx - 0.7, wx + 0.7, -d / 2 - 0.08, -d / 2 + 0.02, h * 0.42, h * 0.42 + 1.3)
    mesh_obj(name + "Win", bm, M_WIN, root)
    HOUSES.append(root); return root
random.seed(7)
for i, x in enumerate([16, 28, 40, 52, 64, 76, -36, -48, -60]):
    house(f"HouseA{i}", x, 12.0, 8.0, 7.0, 4.2 + 0.6 * (i % 2), FAR, M_WALL if i % 3 else M_WALL2)
for i, x in enumerate([22, 36, 50, 66, -30, -44, -58, 4, -12]):
    house(f"HouseB{i}", x, 28.0 + 3 * (i % 2), 8.5, 7.0, 4.4 + 0.5 * (i % 3), FAR, M_WALL2 if i % 2 else M_WALL)
for i, x in enumerate([22, 38, 56, -40, -60]):
    house(f"HouseN{i}", x, -14.0, 8.0, 7.0, 4.4, NEAR, M_WALL)
HYD = empty("Hydrant", (15.0, 3.0, 0), FAR); bm = bmesh.new()
add_cyl(bm, 0.28, 1.0, "Z", (0, 0, 0.55)); add_cyl(bm, 0.34, 0.2, "Z", (0, 0, 1.1)); add_cyl(bm, 0.12, 0.6, "X", (0, 0, 0.75))
mesh_obj("HydrantM", bm, M_HYD, HYD)
LAMPS = []
for x in (-30, -6, 24, 48, 72):
    box(f"Pole{x}", x - 0.12, x + 0.12, 5.0, 5.24, 0, 6.0, M_POLE, FAR)
    l = full_cyl(f"Lamp{x}", 0.35, x, 4.8, 5.8, 6.2, M_LAMP); l.parent = FAR; LAMPS.append(l)
for i in range(26):
    x = random.uniform(-150, 150); y = random.choice([random.uniform(40, 150), random.uniform(-150, -24)])
    if abs(x) < 14 and y < 0: continue
    par = FAR if y > 0 else NEAR; s = random.uniform(1.6, 2.6)
    full_cyl(f"Trunk{i}", 0.25 * s, x, y, 0, 2.0 * s, M_TRUNK).parent = par
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.6 * s); bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, 2.6 * s))
    mesh_obj(f"Crown{i}", bm, M_TREE, par)
# hill line far behind the town
for i in range(7):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=60); bmesh.ops.scale(bm, verts=bm.verts, vec=(1.6, 1.0, 0.35))
    bmesh.ops.translate(bm, verts=bm.verts, vec=(-260 + i * 90, 300 + 20 * (i % 2), -8)); mesh_obj(f"Hill{i}", bm, M_GRASS, FAR)

# ================= hook props: gold gravity arrow, gold height bar =================
GARR = empty("GravityArrow", (-12.5, -3.0, 0)); bm = bmesh.new(); add_arrow(bm, (0, 40.0), (0, -1), 14.0, 2.4); mesh_obj("GravityArrowM", bm, M_GARROW, GARR)
HBAR = empty("HeightBar", (12.5, -3.0, 0)); bm = bmesh.new(); add_box(bm, -0.25, 0.25, -0.25, 0.25, 0, 27.3)
add_box(bm, -1.2, 1.2, -0.25, 0.25, 27.05, 27.55); add_box(bm, -1.2, 1.2, -0.25, 0.25, 0, 0.5); mesh_obj("HeightBarM", bm, M_GOLD, HBAR)

# ================= flow arrows (cyan cones in front of the cut faces) =================
def arrow_set(name, p0, p1, n, speed, wins, r=0.45):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; Lr = d.length; dn = d.normalized()
    objs = []
    for k in range(n):
        bm = bmesh.new(); res = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r, radius2=0.0, depth=r * 2.0)
        bmesh.ops.transform(bm, matrix=dn.to_track_quat("Z", "Y").to_matrix().to_4x4(), verts=res["verts"])
        o = mesh_obj(f"{name}{k}", bm, M_ARROW); windows(o, wins)
        for ax in range(3):
            bake_fn(o, "location", ax, lambda t, k=k, ax=ax: (p0 + dn * (((k / n) * Lr + speed * t) % Lr))[ax])
        objs.append(o)
    return objs
AY = -0.75
FLOW_FILL = [(T_FILL0 - 0.1, T_FILL1)]
arrow_set("ArrPumpMain", (PX + 0.6, AY, MZ), (-1.2, AY, MZ), 4, 5.0, FLOW_FILL, 0.35)
arrow_set("ArrPumpDown", (PX, AY, 0.0), (PX, AY, MZ + 0.3), 2, 3.0, FLOW_FILL, 0.3)
arrow_set("ArrUp", (0, AY - 0.2, MZ + 0.5), (0, AY - 0.2, 27.0), 7, 7.0, FLOW_FILL, 0.55)
FLOW_OUT = [(T_DR0 - 0.05, T_DR1 + 0.3), (T_GR0, T_GR1)]
arrow_set("ArrDown", (0, AY - 0.2, 27.0), (0, AY - 0.2, MZ + 0.5), 7, 7.0, FLOW_OUT, 0.55)
arrow_set("ArrMainOut", (1.2, AY, MZ), (78.0, AY, MZ), 12, 6.0, FLOW_OUT, 0.35)
arrow_set("ArrOvf", (OVX, -0.5, OVZ1 - 0.6), (OVX, -0.5, OVZ0 + 0.3), 6, 7.0, [(T_DUMP - 0.1, T_CTA)], 0.38)

# ================= pressure-column set (far behind the camera): a clear tube of stacked water on a shower, + a wide tank =================
SET = Vector((0.0, -600.0, 0.0)); SX, SY, SZ = SET
SETR = empty("PressureSet", SET)
box("SetFloor", -40, 40, -40, 12, -0.5, 0.0, M_TILEF, SETR); box("SetWall", -60, 60, 6.0, 6.6, 0.0, 80.0, M_TILE, SETR)
TZ0, TN = 4.0, 20                                    # tube bottom, discs (each = 5 ft)
lathe("SetTube", tube_prof(0.62, 0.72, TZ0, TZ0 + TN + 0.6), [M_GLASS], 0.0, 2 * math.pi, 32).parent = SETR
lathe("SetTubeBase", [(0, 2.2), (0.95, 2.2), (0.95, TZ0), (0, TZ0)], [M_CHROME], 0.0, 2 * math.pi, 32).parent = SETR
lathe("SetStand", [(0, 0), (0.3, 0), (0.3, 2.2), (0, 2.2)], [M_CHROME], 0.0, 2 * math.pi, 16).parent = SETR
bm = bmesh.new(); add_tube(bm, (0.6, 0, 3.0), (4.6, 0, 3.0), 0.22, 16); add_tube(bm, (2.2, 0, 3.0), (2.2, 0, 4.3), 0.12, 10)
mesh_obj("SetPipe", bm, M_CHROME, SETR)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.2, radius2=0.6, depth=0.5)
bmesh.ops.translate(bm, verts=bm.verts, vec=(4.75, 0, 2.7)); mesh_obj("SetHead", bm, M_CHROME, SETR)
def gauge(name, cx, cz):
    g = empty(name, (cx, -0.25, cz), SETR)
    o = cyl(name + "Dial", 0.95, 0.25, "Y", (0, 0, 0), M_DIAL, g, seg=40); cyl(name + "Rim", 1.08, 0.2, "Y", (0, 0.06, 0), M_CHROME, g, seg=40)
    bm = bmesh.new()
    for k in range(7):
        a = math.radians(-135 + 45 * k); add_bar(bm, (0.72 * math.sin(a), -0.14, 0.72 * math.cos(a)), (0.88 * math.sin(a), -0.14, 0.88 * math.cos(a)), 0.07)
    mesh_obj(name + "Ticks", bm, M_ROOF, g)
    nd = empty(name + "Needle", (0, -0.2, 0), g); bm = bmesh.new(); add_box(bm, -0.04, 0.04, -0.03, 0.03, -0.1, 0.78); mesh_obj(name + "NeedleM", bm, M_NEEDLE, nd)
    cyl(name + "Hub", 0.1, 0.1, "Y", (0, -0.22, 0), M_CHROME, g)
    return g, nd
G1, ND1 = gauge("Gauge1", 2.2, 5.3)
# discs of water (each = 5 ft of height); 4 slowly, then 16 fast
DISC_T = [C["stacked"], C["tap"], C["adds"], C["point"]] + [C["hundred2"] + (k + 1) * (C["fortythree"] - C["hundred2"]) / 16 for k in range(16)]
DISCS = []
for k in range(TN):
    d = empty(f"Disc{k}", (0, 0, 0), SETR)
    lathe(f"DiscM{k}", [(0, 0.02), (0.6, 0.02), (0.6, 0.98), (0, 0.98)], [M_SWAT], 0.0, 2 * math.pi, 24, smooth=False).parent = d
    windows(d, [(DISC_T[k], T_SET1)])
    bake_fn(d, "location", 2, lambda t, k=k: TZ0 + k + (drop(t, DISC_T[k], 2.5, 0.22) if t < DISC_T[k] + 0.6 else 0.0))
    DISCS.append(d)
def ncount(t): return sum(1 for k in range(TN) if t >= DISC_T[k] + 0.22)
psi_now = lambda t: 43.0 * ncount(t) / TN
bake_fn(ND1, "rotation_euler", 1, lambda t: math.radians(-135 + 270 * min(60.0, psi_now(t)) / 60.0))
# shower spray from the head (on "push")
SPRAY = empty("Spray", (4.75, 0, 2.45), SETR); bm = bmesh.new()
for k in range(14):
    a = k * 2 * math.pi / 14; rr = 0.25 + 0.2 * (k % 3)
    add_tube(bm, (0.3 * math.cos(a), 0.3 * math.sin(a), 0), (1.6 * rr * math.cos(a) * 2.2, 1.6 * rr * math.sin(a) * 2.2, -2.4), 0.035, 5)
mesh_obj("SprayM", bm, M_ARROW, SPRAY); windows(SPRAY, [(C["push"], T_SET1)])
# wide tank, same height, same gauge reading
WT = empty("WideTank", (-11.0, 0.5, 0), SETR)
lathe("WideGlass", tube_prof(4.0, 4.12, TZ0, TZ0 + TN + 0.6), [M_GLASS], 0.0, 2 * math.pi, 64).parent = WT
lathe("WideWater", [(0, TZ0 + 0.02), (3.98, TZ0 + 0.02), (3.98, TZ0 + TN), (0, TZ0 + TN)], [M_SWAT], 0.0, 2 * math.pi, 64, smooth=False).parent = WT
lathe("WideBase", [(0, 0), (4.4, 0), (4.4, TZ0), (0, TZ0)], [M_CONC], 0.0, 2 * math.pi, 64).parent = WT
bm = bmesh.new(); add_tube(bm, (4.0, -0.5, 3.0), (6.4, -0.5, 3.0), 0.22, 16); add_tube(bm, (6.4, -0.5, 3.0), (6.4, -0.5, 4.3), 0.12, 10)
mesh_obj("WidePipe", bm, M_CHROME, WT)
G2 = empty("Gauge2Root", (0, 0, 0), WT)
g2, ND2 = gauge("Gauge2", 0, 0); g2.parent = WT; g2.location = (6.4, -0.75, 5.3)
ND2.rotation_euler.y = math.radians(-135 + 270 * 43.0 / 60.0)
T_WT = C["tanks"] - 0.05
windows(WT, [(T_WT, T_SET1)])
for ax in range(3): bake_fn(WT, "scale", ax, lambda t: max(0.001, pop(t, T_WT, 0.3)))
LEVEL = empty("LevelLine", (0, -4.6, TZ0 + TN), SETR); bm = bmesh.new(); add_box(bm, -16.5, 2.0, -0.12, 0.12, -0.12, 0.12); mesh_obj("LevelLineM", bm, M_GOLD, LEVEL)
windows(LEVEL, [(C["high"] - 0.05, T_SET1)])
bake_fn(LEVEL, "scale", 0, lambda t: max(0.001, ease((t - C["high"] + 0.05) / 0.35)))
glow(B_GOLD, [(0, 1.2)])

# ================= animation: halves, rise, glows, sky =================
for r_ in (NEAR,):
    bake_fn(r_, "location", 1, lambda t: -140.0 * near_off(t))
    bake_fn(r_, "location", 2, lambda t: -60.0 * near_off(t) ** 2)
NEAR_HIDE = [(0, T_CUT1 + 0.05), (T_SET0, T_IN1 + 0.05), (T_CTA, DUR)]
for o in list(NEAR.children_recursive): pass
vis_objs = [o for o in NEAR.children_recursive if o.type == "MESH"]
for o in vis_objs: windows(o, NEAR_HIDE)
for top in (FAR_TOP, NEAR_TOP): bake_fn(top, "location", 2, lambda t: -31.0 * (1.0 - rise(t)))
for lg in (FAR_LEGS, NEAR_LEGS): bake_fn(lg, "scale", 2, lambda t: rise(t))
windows(OVF, [(0, T_SET1), (T_RISE1, DUR)])
windows(SPILL, [(T_DUMP - 0.05, T_CTA)])
windows(GARR, [(C["gravity"] - 0.05, C["pressure"] - 0.1)])
bake_fn(GARR, "location", 2, lambda t: -6.0 * (1 - ease((t - C["gravity"] + 0.05) / 0.4)))
windows(HBAR, [(C["hundred"] - 0.1, C["lets"] - 0.1), (C["heightis"] - 0.05, C["inside"] + 0.4)])
bake_fn(HBAR, "scale", 2, lambda t: max(0.001, ease((t - C["hundred"] + 0.1) / 0.5)) if t < C["lets"] else max(0.001, ease((t - C["heightis"] + 0.05) / 0.4)))
# pump: spins while running (fill + morning + average), stops at "out"
def pump_ang(t):
    a = 0.0
    on = [(T_FILL0 - 0.3, T_FILL1 + 0.3), (T_MO1, T_PWR)]
    for t0, t1 in on:
        if t > t0: a += 14.0 * (min(t, t1) - t0)
    return a
bake_fn(IMP, "rotation_euler", 2, pump_ang)
glow(B_PUMP, [(0, 0.0), (T_FILL0 - 0.4, 0.0), (T_FILL0 - 0.2, 1.6), (T_FILL1, 1.6), (T_FILL1 + 0.3, 0.0), (C["average"] - 0.1, 0.0), (C["average"] + 0.1, 1.6),
              (C["peak"] - 0.2, 1.6), (C["peak"], 0.0)])
# pump red when it can't keep up / at the peak / when the power goes out: red overlay via the casing emission colour key
ec = B_PUMP.inputs["Emission Color"]
def ecol(t, rgb): ec.default_value = (*rgb, 1); ec.keyframe_insert("default_value", frame=F(t))
ecol(0, (0.98, 0.74, 0.27)); ecol(C["cant"] - 0.05, (0.98, 0.74, 0.27)); ecol(C["cant"], (1.0, 0.3, 0.24)); ecol(C["average"] - 0.15, (1.0, 0.3, 0.24))
ecol(C["average"] - 0.1, (0.98, 0.74, 0.27)); ecol(C["peak"] - 0.05, (0.98, 0.74, 0.27)); ecol(C["peak"], (1.0, 0.3, 0.24))
glow(B_PUMP, [(C["cant"] - 0.05, 0.0), (C["cant"] + 0.1, 2.0), (C["cant"] + 1.2, 2.0), (C["cant"] + 1.6, 0.0)] + pulse(C["peak"], 2.0, hold=0.4)
     + pulse(T_PWR, 2.2, hold=0.8))
glow(B_PIPE, [(0, 0.0)] + pulse(C["riser"], 1.2, hold=0.8) + pulse(C["riser2"], 0.8, hold=0.4))
glow(B_MAIN, [(0, 0.0)] + pulse(C["main"], 1.4, hold=0.6))
glow(B_OVF, [(0, 0.0)] + pulse(C["overflow"], 1.5, hold=0.6))
glow(B_PWAT, [(0, 0.0)] + pulse(C["riser"], 0.6, hold=0.8) + [(T_FILL0, 0.0), (T_FILL0 + 0.3, 0.5), (T_FILL1, 0.5), (T_FILL1 + 0.3, 0.0),
     (T_DR0, 0.0), (T_DR0 + 0.3, 0.5), (T_DR1, 0.5), (T_DR1 + 0.3, 0.0), (T_GR0, 0.0), (T_GR0 + 0.3, 0.5), (T_GR1 - 0.3, 0.5), (T_GR1, 0.0)])
glow(B_WAT, [(0, 0.0)] + pulse(C["tank3"], 0.8, hold=0.5) + [(C["part"] - 0.1, 0.0), (C["part"] + 0.2, 1.6), (C["too"] - 0.3, 1.6), (C["too"], 0.0)])
keyval(FIREFAC, [(0, 0.0), (C["part"] - 0.12, 0.0), (C["part"] - 0.1, 1.0), (C["too"] - 0.05, 1.0), (C["too"], 0.0)])
glow(B_HYD, [(0, 0.0)] + pulse(C["firefighters"], 2.0, hold=0.7))
glow(B_PAINT, [(0, 0.0)])
# houses: red on "drops too low" / "boil"; windows cyan when everyone showers
glow(B_WALL, [(0, 0.0)] + pulse(C["low"], 0.6, hold=0.4) + pulse(C["boil"], 0.9, hold=0.5))
wc = B_WIN.inputs["Emission Color"]
for t, rgb in ((0, (1.0, 0.82, 0.55)), (C["everyone"] - 0.05, (1.0, 0.82, 0.55)), (C["everyone"], (0.30, 0.92, 1.0))):
    wc.default_value = (*rgb, 1); wc.keyframe_insert("default_value", frame=F(t))
glow(B_WIN, [(0, 0.0), (T_NI0, 0.0), (T_NI1, 0.25), (C["nobody"], 0.25), (C["nobody"] + 0.4, 0.04), (T_MO0, 0.04), (T_MO1, 0.0)]
     + pulse(C["everyone"], 3.0, hold=1.5))
glow(B_LAMP, [(0, 0.0), (T_NI0, 0.0), (T_NI1, 6.0), (T_MO0, 6.0), (T_MO1, 0.0)])
glow(B_ARROW, [(0, 3.0)])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.2; cam_d.clip_end = 3000
S = lambda x, y, z: (SX + x, SY + y, SZ + z)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (9.0, -30.0, 2.0), (0.0, 0.0, 33.0), 17),
    (C["gravity"] - 0.1, (6.0, -26.0, 3.0), (0.0, 0.0, 35.0), 17),
    (C["gravity"], (-2.0, -66.0, 15.0), (0.0, 0.0, 22.0), 19, "cut"),
    (C["pressure"] - 0.1, (-1.0, -60.0, 15.0), (0.0, 0.0, 22.0), 19),
    (C["pressure"], (52.0, -62.0, 26.0), (34.0, 12.0, 4.0), 20, "cut"),
    (C["lets"] - 0.1, (46.0, -54.0, 23.0), (34.0, 12.0, 4.0), 20),
    (C["lets"], (2.0, -80.0, 18.0), (2.0, 0.0, 17.0), 20, "cut"),
    (T_SET0 - 0.05, (2.0, -72.0, 17.0), (2.0, 0.0, 16.0), 20),
    (T_SET0, S(5.5, -11.0, 4.5), S(2.0, 0.0, 4.0), 30, "cut"),
    (C["point"], S(4.5, -12.5, 6.0), S(1.5, 0.0, 5.5), 30),
    (C["hundred2"] - 0.1, S(4.0, -14.0, 7.5), S(1.0, 0.0, 7.0), 30),
    (C["fortythree"] + 0.3, S(4.0, -27.0, 13.0), S(1.5, 0.0, 13.0), 26),
    (C["thats"] - 0.05, S(4.0, -28.0, 13.0), S(1.5, 0.0, 13.0), 26),
    (C["thats"], S(9.0, -11.0, 4.5), S(4.2, 0.0, 2.6), 26, "cut"),
    (T_WT - 0.05, S(8.5, -10.5, 4.2), S(4.2, 0.0, 2.4), 26),
    (T_WT, S(-3.0, -50.0, 13.0), S(-5.0, 0.0, 13.0), 24, "cut"),
    (T_SET1 - 0.05, S(-3.0, -46.0, 14.0), S(-5.0, 0.0, 13.5), 24),
    (T_SET1, (4.0, -66.0, 12.0), (0.0, 0.0, 20.0), 20, "cut"),
    (T_IN0 - 0.05, (2.0, -60.0, 12.0), (0.0, 0.0, 21.0), 20),
    (T_IN0, (6.0, -50.0, 18.0), (0.0, 0.0, 17.0), 20, "cut"),
    (C["riser"] - 0.2, (3.0, -36.0, 12.0), (0.0, 0.0, 11.0), 20),
    (C["main"] - 0.2, (12.0, -34.0, 4.0), (8.0, 0.0, 0.0), 20),
    (C["tank3"] - 0.25, (14.0, -32.0, 3.5), (9.0, 0.0, -0.5), 20),
    (C["tank3"] - 0.2, (2.0, -40.0, 28.0), (0.0, 0.0, 32.0), 20, "cut"),
    (T_NI0 - 0.05, (1.0, -44.0, 30.0), (0.0, 0.0, 32.0), 20),
    (T_NI0, (-8.0, -66.0, 14.0), (-8.0, 0.0, 14.0), 20, "cut"),
    (T_MO0 - 0.05, (-7.0, -58.0, 15.0), (-7.0, 0.0, 14.0), 20),
    (T_MO0, (30.0, -84.0, 24.0), (22.0, 0.0, 12.0), 20, "cut"),
    (T_DR0 - 0.05, (27.0, -76.0, 22.0), (22.0, 0.0, 12.0), 20),
    (T_DR0, (8.0, -58.0, 16.0), (5.0, 0.0, 15.0), 20, "cut"),
    (C["means"] - 0.05, (6.0, -54.0, 16.0), (4.0, 0.0, 15.0), 20),
    (C["means"], (PX + 6.0, -20.0, 5.0), (PX, 1.0, 2.0), 22, "cut"),
    (C["if"] - 0.05, (PX + 4.0, -17.0, 4.5), (PX, 1.0, 2.0), 22),
    (C["if"], (-4.0, -72.0, 18.0), (2.0, 0.0, 16.0), 20, "cut"),
    (C["part"] - 0.05, (-2.0, -66.0, 17.0), (2.0, 0.0, 16.0), 20),
    (C["part"], (12.0, -48.0, 15.0), (7.0, 0.0, 16.0), 20, "cut"),
    (C["too"] - 0.05, (13.0, -46.0, 14.0), (8.0, 0.0, 15.0), 20),
    (C["too"], (17.0, -38.0, 22.0), (7.0, 0.0, 21.0), 20, "cut"),
    (T_CTA - 0.05, (17.0, -35.0, 19.0), (7.5, 0.0, 18.0), 20),
    (T_CTA, (7.0, -9.8, 5.0), (3.0, -3.0, 40.0), 16, "cut"),
    (DUR, (6.4, -8.8, 22.0), (2.0, -2.0, 44.0), 16),
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
    cam_loc.append(l0 + Vector((0.04 * math.sin(t * 0.7), 0.0, 0.03 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()
# ================= world + light: small town in daylight; night for the fill beat =================
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
    try: sky.sun_elevation = math.radians(30); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"])
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1)
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
# night: a deep-blue sky, dim ambient (keyed every 3 frames through the transitions)
nkeys = sorted(set([0.0, T_NI0 - 0.05, T_NI1 + 0.05, T_MO0 - 0.05, T_MO1 + 0.05] + [T_NI0 + i * 0.1 for i in range(6)] + [T_MO0 + i * 0.1 for i in range(6)]))
sky_on = wn.new("ShaderNodeMix"); sky_on.data_type = "RGBA"
try: wl.new(sky.outputs["Color"], sky_on.inputs[6])
except Exception: sky_on.inputs[6].default_value = (0.45, 0.62, 0.85, 1)
sky_on.inputs[7].default_value = (0.004, 0.008, 0.03, 1); wl.new(sky_on.outputs[2], bg.inputs["Color"])
for t in nkeys:
    n = night(t)
    sky_on.inputs[0].default_value = n; sky_on.inputs[0].keyframe_insert("default_value", frame=F(t))
    bg.inputs["Strength"].default_value = 0.22 * (1 - n) + 1.0 * n; bg.inputs["Strength"].keyframe_insert("default_value", frame=F(t))
    amb.inputs["Strength"].default_value = 0.45 * (1 - n) + 0.06 * n; amb.inputs["Strength"].keyframe_insert("default_value", frame=F(t))
    amb.inputs["Color"].default_value = (0.55 * (1 - n) + 0.10 * n, 0.68 * (1 - n) + 0.16 * n, 0.85 * (1 - n) + 0.40 * n, 1)
    amb.inputs["Color"].keyframe_insert("default_value", frame=F(t))
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), math.radians(-15), math.radians(-35))
for t in nkeys: sun_d.energy = 3.2 * (1 - night(t)) + 0.15 * night(t); sun_d.keyframe_insert("energy", frame=F(t))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)
for t in nkeys: fill_d.energy = 4500 * (1 - night(t)) + 1600 * night(t); fill_d.keyframe_insert("energy", frame=F(t))
LAMPL = []
for x in (-30, -6, 24, 48):
    ld = bpy.data.lights.new(f"StreetLamp{x}", "POINT"); ld.color = (1.0, 0.78, 0.5); ld.shadow_soft_size = 0.5
    lo = bpy.data.objects.new(f"StreetLamp{x}", ld); scene.collection.objects.link(lo); lo.location = (x, 4.3, 5.4)
    for t in nkeys: ld.energy = 1500 * night(t); ld.keyframe_insert("energy", frame=F(t))

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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 6; scene.cycles.transparent_max_bounces = 12; scene.cycles.volume_bounces = 0
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
    "tank": lambda t: Vector((-8.0, -0.5, 36.0 - 31.0 * (1 - rise(t)))),
    "riser": lambda t: Vector((-RR1, -0.6, 12.0)),
    "main": lambda t: Vector((10.0, -0.6, MZ)),
    "pump": lambda t: Vector((PX - 1.0, -0.5, 1.4)),
    "overflow": lambda t: Vector((OVX + 0.4, 0.0, 24.0)),
    "hydrant": lambda t: Vector((15.0, 3.0, 1.4)),
    "reserve": lambda t: Vector((-4.0, -0.2, 29.0)),
    "water": lambda t: Vector((3.0, -0.2, level(t) - 1.5)),
    "gauge": lambda t: Vector((SX + 2.2 - 0.9, SY - 0.4, 5.3)),
    "column": lambda t: Vector((SX - 0.7, SY, SZ + 14.0)),
    "shower": lambda t: Vector((SX + 4.75, SY, 2.5)),
    "gauge2": lambda t: Vector((SX - 11.0 + 6.4, SY - 0.8, 5.3)),
    "widetank": lambda t: Vector((SX - 15.0, SY - 0.5, 14.0)),
    "ladder": lambda t: Vector((LEGB - 0.9, -LEGB - 0.6, 4.0)),
    "house": lambda t: Vector((28.0, 8.4, 3.0)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cut": R3(T_CUT0, T_CUT1), "set": R3(T_SET0, T_SET1), "discs": [round(x, 3) for x in DISC_T], "spray": round(C["push"], 3),
          "widetank": round(T_WT, 3), "rise": R3(T_RISE0, T_RISE1), "cut2": R3(T_IN0, T_IN1), "night": R3(T_NI0, T_NI1),
          "fill": R3(T_FILL0, T_FILL1), "morning": R3(T_MO0, T_MO1), "drain": R3(T_DR0, T_DR1), "power": round(T_PWR, 3),
          "gravity": R3(T_GR0, T_GR1), "full": R3(T_FULL0, T_FULL1), "dump": round(T_DUMP, 3), "cta": round(T_CTA, 3)}
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
