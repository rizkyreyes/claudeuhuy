# Pile-Driver-3D: how a diesel pile driver works (the hammer lifts itself). Build-up format ("THIS IS A HAMMER"):
# hammer + tent stake -> giant rig driving a skyscraper pile, ram flies up on its own -> a crooked blow crushes the pile head ->
# a tower stands on steel piles 100+ ft long -> the first pile drivers just dropped a heavy weight (lift, drop, lift: slow) ->
# put the weight (the ram) inside a steel cylinder -> falling, it squeezes the air below, squeezed air gets hot -> spray in diesel,
# it ignites from that heat alone (no spark, like a diesel engine) -> the ram slams the pile, the blast drives the pile down AND throws
# the ram back up -> it falls again, ~40-50 times a minute, on its own -> leads keep every blow straight, a cushioned helmet protects
# the pile head -> the crew counts blows per foot -> next piles, the tower rises on them -> CTA: the rig fires on a new pile.
# Blender Cycles, real-world site cut at y = 0 (grass, topsoil, soft clay, sand, dense gravel), camera on -y. Illustrative (1 unit = 1 m):
# hammer drawn ~1.5x real size so the ram reads on a phone, piles 32 m (~105 ft), slow-motion strokes in the explainer close-ups,
# ignition shown before the slam for the story (in a real hammer it happens at impact). Demo sets: stake at x = 200, crooked blow at x = 100.
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

CUES = [("if", "If"), ("hit", "hit"), ("hammer", "hammer,"), ("sinks", "sinks."), ("the", "The"), ("giant", "giant"), ("skyscraper", "skyscraper"),
        ("piles", "piles"), ("same", "same"), ("except", "except"), ("lifts", "lifts"), ("itself", "itself."), ("land", "Land"), ("blow", "blow"),
        ("crooked", "crooked,"), ("head", "head"), ("crushed", "crushed."), ("this", "This"), ("hammer2", "hammer."), ("tent", "tent"),
        ("takes", "takes"), ("few", "few"), ("hits", "hits."), ("a", "A"), ("tower", "tower"), ("steel", "steel"), ("piles2", "piles"),
        ("hundred", "hundred"), ("feet", "feet."), ("first", "first"), ("dropped", "dropped"), ("heavy", "heavy"), ("lift", "Lift,"),
        ("drop", "drop,"), ("lift2", "lift"), ("slow", "Slow."), ("so", "So"), ("ram", "ram,"), ("inside", "inside"), ("cylinder", "cylinder."),
        ("falling", "Falling,"), ("squeezes", "squeezes"), ("air", "air"), ("squeezed", "squeezed"), ("hot", "hot."), ("spray", "Spray"),
        ("diesel", "diesel."), ("ignites", "ignites"), ("heat", "heat"), ("no", "No"), ("spark", "spark,"), ("engine", "engine."),
        ("ram2", "ram"), ("slams", "slams"), ("blast", "blast"), ("two", "two"), ("drives", "drives"), ("down", "down,"), ("throws", "throws"),
        ("up", "up."), ("falls", "falls"), ("again", "again,"), ("forty", "forty"), ("fifty", "fifty"), ("minute", "minute,"), ("all", "all"), ("own", "own."),
        ("frame", "frame,"), ("leads", "leads,"), ("straight", "straight,"), ("cushioned", "cushioned"), ("helmet", "helmet"),
        ("protects", "protects"), ("crew", "crew"), ("counts", "counts"), ("blows", "blows"), ("foot", "foot"), ("deep", "deep"),
        ("hold", "hold."), ("then", "Then"), ("next", "next"), ("tower2", "tower"), ("stand", "stand"), ("would", "Would"),
        ("fires", "fires?"), ("tell", "Tell"), ("nextup", "Next"), ("well", "well."), ("follow", "Follow")]

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
CL = coll("PileDriver")
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




def soil_mat(name, rgb1, rgb2, scale=1.2, wet=False):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    g = N.new("ShaderNodeNewGeometry"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 8
    L.new(g.outputs["Position"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].color = (*rgb1, 1); e[1].color = (*rgb2, 1)
    L.new(n.outputs["Fac"], cr.inputs[0]); col = cr.outputs[0]
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale * 6; L.new(g.outputs["Position"], vo.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.05; mr.inputs[2].default_value = 0.18; L.new(vo.outputs["Distance"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], tuple(c * 0.55 for c in rgb1), col)          # pebbles / grains
    if wet:   # below the water table the aquifer is saturated: blue-tinted
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], sep.inputs[0])
        lt = N.new("ShaderNodeMapRange"); lt.inputs[1].default_value = WT + 0.3; lt.inputs[2].default_value = WT - 0.3
        L.new(sep.outputs["Z"], lt.inputs[0])
        wetc = mix_rgb(nt, mr.outputs[0], (0.02, 0.08, 0.15), (0.07, 0.22, 0.32))
        col = mix_rgb(nt, lt.outputs[0], col, wetc)
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m




def bake_scalar(owner, path, values):
    owner.keyframe_insert(path, frame=1)
    ad = owner.animation_data; act = ad.action
    try: fcs = act.fcurves
    except AttributeError:
        from bpy_extras import anim_utils
        fcs = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot).fcurves
    fc = fcs.find(path) or fcs.find(path, index=0)
    fc.keyframe_points.clear(); fc.keyframe_points.add(len(values)); co = []
    for i, v in enumerate(values): co += [i + 1, v]
    fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * len(values)); fc.update()
def par(o, p):
    o.parent = p; o.matrix_parent_inverse = Matrix.Identity(4); return o
def bake_loc(o, fn):
    vals = [fn(t) for t in TS]
    for ax in range(3): bake(o, "location", ax, [v[ax] for v in vals])
def bake_scale(o, fn):
    vals = [fn(t) for t in TS]
    for ax in range(3): bake(o, "scale", ax, [v[ax] for v in vals])
def bsdf_of(m): return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
def half_pile(name, r, length, m_, x=0.0):
    """Solid pile, origin at the toe, cut at y = -0.02 (its section sits just in front of the soil cut face)."""
    bm = bmesh.new(); add_cyl(bm, r, length, "Z", (0, 0, length / 2), 32); cut_front(bm, -0.02)
    o = mesh_obj(name, bm, m_); o.location = (x, 0, 0); return o
def ghost_mat(name, rgb, strength=1.4):
    """transparent <-> emissive tint, Fac and Color keyable (returns material, fac socket, color socket, strength socket)."""
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.0
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m, mx.inputs[0], em.inputs["Color"], em.inputs["Strength"]

# ================= timing =================
WT = -999.0
T_SITE, T_LAND, T_THIS, T_TOWER = C["the"], C["land"], C["this"], C["a"]
T_DW = C["first"] - 0.16
T_SO, T_RAMG, T_CYL, T_FALL, T_AIR, T_HOT = C["so"], C["ram"], C["inside"], C["falling"], C["air"], C["hot"]
T_SPRAY, T_IGN, T_SLAM, T_BLAST, T_DRV, T_THROW, T_FALLS = C["spray"], C["ignites"], C["slams"], C["blast"], C["drives"], C["throws"], C["falls"]
T_FRAME, T_HELM, T_CREW, T_NEXT, T_CTA = C["frame"] - 0.5, C["cushioned"], C["crew"], C["then"], C["would"]
T_MOVE1 = T_NEXT + 1.1
PL1, PL2, TOE0 = 32.0, 20.0, -6.0
HOOK_B = [T_SITE - 1.25, T_SITE + 0.04, T_SITE + 1.29, T_SITE + 2.54, T_SITE + 3.79]   # last one launches the slow "lifts itself" stroke
R0 = C["again"]
RAPID = []
t_ = R0
while t_ <= C["deep"] + 0.2: RAPID.append(round(t_, 3)); t_ += 1.3
CTA_B = []
t_ = T_CTA - 0.5
while t_ < DUR: CTA_B.append(round(t_, 3)); t_ += 1.3
DROP_IMP = [C["dropped"] + 0.37, C["drop"] + 0.36]
STAKE_HITS = [C["hit"] + 0.02, C["hammer"] + 0.02, C["sinks"], C["hammer2"] + 0.14, C["takes"] - 0.16, C["hits"] + 0.04]
CROOK_HITS = [C["blow"] + 0.06, C["crushed"]]

# pile 1 toe: (t, dz, duration) steps
E1 = [(b, 0.35, 0.08) for b in HOOK_B[1:]] + [(d, 0.30, 0.10) for d in DROP_IMP] + [(T_DRV + 0.2, 0.55, 0.45)]
pre = TOE0 - sum(e[1] for e in E1)
W = [1.5 - 0.1 * k for k in range(len(RAPID))]
FINAL1 = -PL1
for k, b in enumerate(RAPID): E1.append((b, (pre - FINAL1) * W[k] / sum(W), 0.10))
E2 = [(b, 0.30, 0.08) for b in CTA_B]
def toe1(t): return TOE0 - sum(dz * lin((t - tb) / d) for tb, dz, d in E1)
def toe2(t): return -4.0 - sum(dz * lin((t - tb) / d) for tb, dz, d in E2)
def top1(t): return toe1(t) + PL1
def top2(t): return toe2(t) + PL2
RX = PW([(0, 0.0), (T_NEXT, 0.0), (T_MOVE1, 16.0)])
def HZ(t):
    if t < T_NEXT: return top1(t)
    if t < T_MOVE1: return top1(T_NEXT) + (top2(T_MOVE1) - top1(T_NEXT)) * ease((t - T_NEXT) / (T_MOVE1 - T_NEXT))
    return top2(t)

def parab(t, imps, S, period=1.3):
    """ram height between impacts: thrown up after each impact, falls back for the next one."""
    prev = None; nxt = None
    for b in imps:
        if b <= t: prev = b
        elif nxt is None: nxt = b
    if prev is None: prev = (nxt - period) if nxt is not None else t
    if nxt is None: return 0.0
    u = (t - prev) / (nxt - prev); return S * 4 * u * (1 - u)
def ram_h(t):
    if t < HOOK_B[-1]: return parab(t, HOOK_B, 2.6, 1.25)
    if t < T_LAND: return PW([(HOOK_B[-1], 0.0), (C["itself"] + 0.25, 4.7), (T_LAND, 4.8)])(t)
    if t < T_SO: return 0.0
    if t < T_FALL: return 3.2
    if t < T_HOT: return 3.2 - 2.75 * lin((t - T_FALL) / (T_HOT - T_FALL)) ** 2
    if t < T_SLAM: return 0.45 - 0.08 * lin((t - T_HOT) / (T_SLAM - T_HOT))
    if t < T_SLAM + 0.1: return 0.37 * (1 - lin((t - T_SLAM) / 0.1) ** 2)
    if t < T_BLAST: return 0.0
    if t < T_DRV + 0.2: return 0.5 * ease((t - T_BLAST) / 0.25)
    if t < T_THROW: return 0.5 + 0.55 * ease((t - T_DRV - 0.2) / 0.45)          # the casing drops with the pile, the ram stays: the gap grows
    if t < T_THROW + 0.85: p = lin((t - T_THROW) / 0.85); return 1.05 + 3.15 * (1 - (1 - p) ** 2)
    if t < R0 - 0.75: return 4.2
    if t < R0: p = lin((t - (R0 - 0.75)) / 0.75); return 4.2 * (1 - p * p)
    if t < RAPID[-1]: return parab(t, RAPID, 2.8)
    if t < CTA_B[0] - 1.3: return 0.0
    return parab(t, CTA_B, 2.8)
IMPACTS = HOOK_B[1:] + [T_SLAM + 0.1] + RAPID + CTA_B

# ================= materials =================
M_STEEL, B_STEEL = mat("Steel", (0.30, 0.31, 0.33), 0.38, 0.85)
M_PILE, B_PILE = mat("Pile", (0.42, 0.44, 0.47), 0.42, 0.85, noise=6.0)
M_RAM, B_RAM = mat("Ram", (0.07, 0.07, 0.08), 0.55, 0.6, emit_rgb=(1.0, 0.74, 0.27))
M_CYL, B_CYL = mat("Cylinder", (0.80, 0.42, 0.02), 0.42, 0.15)
M_ANV, B_ANV = mat("Anvil", (0.22, 0.23, 0.25), 0.35, 0.9)
M_HELM, B_HELM = mat("Helmet", (0.36, 0.37, 0.40), 0.4, 0.85)
M_CUSH, B_CUSH = mat("Cushion", (0.42, 0.26, 0.11), 0.75, 0.0, noise=12.0)
M_RIG, B_RIG = mat("RigYellow", (0.80, 0.45, 0.02), 0.45, 0.15)
M_DARK, _ = mat("RigDark", (0.04, 0.04, 0.045), 0.6, 0.3)
M_GLASS, _ = mat("CabGlass", (0.05, 0.08, 0.10), 0.08, 0.2)
M_LEADS, B_LEADS = mat("Leads", (0.20, 0.21, 0.23), 0.45, 0.8, emit_rgb=(0.30, 0.92, 1.0))
M_GOLD, B_GOLD = mat("ArrowGold", (1.0, 0.74, 0.27), 0.4, 0.0); B_GOLD.inputs["Emission Strength"].default_value = 3.0
M_PUFF, _ = mat("Puff", (0.42, 0.42, 0.43), 0.95, 0.0, alpha=0.30)
M_WOOD, B_WOOD = mat("StakeWood", (0.55, 0.36, 0.17), 0.7, 0.0, noise=8.0)
M_HANDLE, _ = mat("Handle", (0.45, 0.28, 0.12), 0.6, 0.0)
M_HHEAD, _ = mat("HammerHead", (0.25, 0.26, 0.28), 0.3, 0.9)
M_CRUSH, B_CRUSH = mat("Crushed", (0.42, 0.44, 0.47), 0.5, 0.85, emit_rgb=(1.0, 0.30, 0.24))
M_INJ, B_INJ = mat("Injector", (0.30, 0.31, 0.33), 0.35, 0.85)
M_FUEL, B_FUEL = mat("Fuel", (0.95, 0.80, 0.30), 0.2, 0.0); B_FUEL.inputs["Emission Strength"].default_value = 2.0
M_GRASS = ground("Grass", (0.07, 0.17, 0.04), (0.16, 0.30, 0.07), 0.4)
M_TOP = soil_mat("Topsoil", (0.17, 0.10, 0.05), (0.26, 0.16, 0.08), 1.0)
M_CLAY = soil_mat("Clay", (0.40, 0.27, 0.17), (0.50, 0.35, 0.23), 0.5)
M_SAND = soil_mat("Sand", (0.60, 0.48, 0.28), (0.72, 0.60, 0.38), 0.6)
M_GRAV = soil_mat("Gravel", (0.33, 0.32, 0.31), (0.50, 0.48, 0.45), 0.8)
B_GRAV = bsdf_of(M_GRAV); B_GRAV.inputs["Emission Color"].default_value = (1.0, 0.74, 0.27, 1)
M_TOWER = tiles("TowerWin", (0.10, 0.16, 0.22), (0.16, 0.24, 0.32), 0.34)
M_AIR, AIR_FAC, AIR_COL, AIR_STR = ghost_mat("Air", (0.30, 0.92, 1.0), 1.6)
M_FIRE, FIRE_FAC, _, FIRE_STR = ghost_mat("Fire", (1.0, 0.55, 0.12), 3.0)
M_GH, GH_FAC, _, _ = ghost_mat("GhostTower", (1.0, 0.74, 0.27), 1.2)

# ================= the site: soil cut at y = 0 =================
def layer(name, z0, z1, m_, x0=-45.0, x1=45.0, y1=30.0): return box(name, x0, x1, 0.0, y1, z0, z1, m_)
layer("Grass", -0.25, 0.0, M_GRASS); layer("Topsoil", -2.0, -0.25, M_TOP); layer("Clay", -12.0, -2.0, M_CLAY)
layer("Sand", -28.0, -12.0, M_SAND); layer("Gravel", -80.0, -28.0, M_GRAV)
box("FarGround", -800, 800, 0.0, 800, -0.30, -0.02, M_GRASS)
glow(B_GRAV, [(0, 0.0)] + pulse(C["deep"], 0.35, hold=1.2, down=0.8))

# pile 1 (the one we drive) and pile 2 (CTA)
P1 = half_pile("Pile1", 0.40, PL1, M_PILE); bake_loc(P1, lambda t: (0.0, 0.0, toe1(t)))
P2 = half_pile("Pile2", 0.40, PL2, M_PILE, 16.0); bake_loc(P2, lambda t: (16.0, 0.0, toe2(t))); windows(P2, [(T_NEXT + 0.6, DUR)])
glow(B_PILE, [(0, 0.0)])

# tower piles: ghosts in the "tower" beat, real ones slide in at the end
TPX = [-16.0, -10.0, -4.0]
for k, x in enumerate(TPX):
    g = half_pile(f"GhostPile{k}", 0.40, PL1, M_GH, x); g.location.z = -PL1; g.location.y = -0.03; windows(g, [(T_TOWER, T_DW)])
    p = half_pile(f"TowerPile{k}", 0.40, PL1, M_PILE, x)
    t0 = T_NEXT + 0.15 + 0.35 * k
    bake_loc(p, lambda t, x=x, t0=t0: (x, 0.0, -PL1 + 34.0 * (1 - ease((t - t0) / 0.55))))
    windows(p, [(t0 - 0.05, DUR)])
keyval(GH_FAC, [(0, 0.0), (T_TOWER, 0.0), (T_TOWER + 0.35, 0.30), (C["hundred"], 0.30), (C["hundred"] + 0.2, 0.7), (C["feet"] + 0.5, 0.45)])
GT = box("GhostTower", -20.0, 3.0, 1.0, 21.0, 0.0, 55.0, M_GH); windows(GT, [(T_TOWER, T_DW)])
TW = box("Tower", -20.0, 3.0, 1.0, 21.0, 0.0, 55.0, M_TOWER)
TWR = empty("TowerRoot", (0, 0, 0)); par(TW, TWR)
bake_scale(TWR, lambda t: (1.0, 1.0, max(0.001, ease((t - C["tower2"] + 0.2) / 1.2))))
windows(TW, [(C["tower2"] - 0.2, DUR)])

# ================= the rig (crawler + leads), moves to x = 16 at "Then the next one" =================
RIG = empty("Rig"); bake_loc(RIG, lambda t: (RX(t), 0.0, 0.0))
def rbox(name, x0, x1, y0, y1, z0, z1, m_): return par(box(name, x0, x1, y0, y1, z0, z1, m_), RIG)
rbox("TrackA", -5.0, 7.0, 2.3, 3.6, 0.0, 1.1, M_DARK); rbox("TrackB", -5.0, 7.0, 8.9, 10.2, 0.0, 1.1, M_DARK)
rbox("Body", -4.0, 6.0, 2.5, 10.0, 1.1, 3.2, M_RIG); rbox("Counterweight", -4.5, -1.5, 3.0, 9.5, 3.2, 4.8, M_RIG)
rbox("Cab", 3.0, 6.0, 2.6, 5.2, 3.2, 5.8, M_RIG); rbox("CabWin", 3.2, 5.8, 2.55, 2.62, 4.0, 5.5, M_GLASS)
bm = bmesh.new()
for sx in (-0.62, 0.62): add_box(bm, sx - 0.13, sx + 0.13, 0.95, 1.25, 0.0, 43.0)
for z in range(2, 43, 3): add_bar(bm, (-0.62, 1.1, z), (0.62, 1.1, z + 1.5), 0.08)
add_box(bm, -0.9, 0.9, 0.6, 1.4, 43.0, 44.2)
add_bar(bm, (0.0, 1.25, 30.0), (0.5, 6.5, 3.2), 0.28); add_bar(bm, (0.0, 1.25, 2.0), (0.5, 3.0, 2.6), 0.30)
LEADS = par(mesh_obj("Leads", bm, M_LEADS), RIG)
glow(B_LEADS, [(0, 0.0)] + pulse(C["leads"], 2.5, hold=1.4, down=0.7))

# ================= the diesel hammer (front half cut at y = 0), rides on the pile top =================
HAM = empty("Hammer"); bake_loc(HAM, lambda t: (RX(t), 0.0, HZ(t)))
ANV_TOP = 1.75
def hl(name, prof, m_, z=0.0): return par(lathe(name, prof, m_, 0.0, math.pi, 48, (0, 0, z)), HAM)
hl("Helmet", [(0.41, -0.5), (0.64, -0.5), (0.64, 0.95), (0.0, 0.95), (0.0, 0.80), (0.41, 0.80)], M_HELM)
hl("Cushion", [(0.0, 0.02), (0.40, 0.02), (0.40, 0.78), (0.0, 0.78)], M_CUSH)
hl("Anvil", [(0.0, 0.95), (0.48, 0.95), (0.48, ANV_TOP), (0.0, ANV_TOP)], M_ANV)
CYLR = empty("CylRoot", (0, 0, 0), HAM)
CYL = lathe("Cylinder", [(0.50, 0.95), (0.68, 0.95), (0.68, 7.2), (0.50, 7.2)], M_CYL, 0.0, math.pi, 48); par(CYL, CYLR)
bake_loc(CYLR, lambda t: (0.0, 0.0, 9.0 * (1 - ease((t - T_CYL - 0.1) / 0.7)) if T_DW <= t < T_CYL + 0.9 else 0.0))
windows(CYL, [(0, T_DW), (T_CYL, DUR)])
bm = bmesh.new()
for z in (2.2, 6.2): add_box(bm, -0.3, 0.3, 0.68, 0.95, z, z + 0.5)
par(mesh_obj("GuideArms", bm, M_STEEL), CYLR)
INJ = hl("Injector", [(0.0, 0.0), (0.12, 0.0), (0.12, 0.30), (0.0, 0.30)], M_INJ); INJ.location = (-0.74, 0.0, ANV_TOP + 0.08)
INJ.rotation_euler = (0, math.radians(90), 0)
glow(B_INJ, [(0, 0.0)] + pulse(T_SPRAY, 3.0, hold=0.8, down=0.4))
RAM = hl("Ram", [(0.0, 0.0), (0.47, 0.0), (0.47, 3.2), (0.0, 3.2)], M_RAM)
bake_loc(RAM, lambda t: (0.0, 0.0, ANV_TOP + ram_h(t)))
glow(B_RAM, [(0, 0.0)] + pulse(C["lifts"], 1.2, hold=0.8, down=0.4) + pulse(T_RAMG, 1.6, hold=1.0, down=0.6) + pulse(T_THROW, 1.2, hold=0.6, down=0.5))
glow(B_HELM, [(0, 0.0)] + pulse(T_HELM, 0.7, hold=1.2, down=0.5)); glow(B_CUSH, [(0, 0.0)] + pulse(T_HELM, 0.8, hold=1.2, down=0.5))
B_HELM.inputs["Emission Color"].default_value = (1.0, 0.74, 0.27, 1); B_CUSH.inputs["Emission Color"].default_value = (1.0, 0.74, 0.27, 1)
AIR = hl("AirGap", [(0.0, 0.0), (0.49, 0.0), (0.49, 1.0), (0.0, 1.0)], M_AIR); AIR.location.y = -0.01
bake_scale(AIR, lambda t: (1.0, 1.0, max(0.002, ram_h(t))))
for o in (AIR,): o.location.z = ANV_TOP
keyval(AIR_FAC, [(0, 0.0), (T_AIR - 0.05, 0.0), (T_AIR + 0.25, 0.75), (T_IGN, 0.75), (T_IGN + 0.15, 0.0)])
keyval(AIR_COL, [(0, (0.30, 0.92, 1.0, 1)), (C["squeezed"], (0.30, 0.92, 1.0, 1)), (T_HOT + 0.1, (1.0, 0.42, 0.10, 1))])
keyval(AIR_STR, [(0, 1.6), (T_HOT - 0.3, 1.6), (T_HOT + 0.2, 3.0)])
FIRE = hl("Fire", [(0.0, 0.0), (0.49, 0.0), (0.49, 1.0), (0.0, 1.0)], M_FIRE); FIRE.location = (0, -0.015, ANV_TOP)
bake_scale(FIRE, lambda t: (1.0, 1.0, max(0.002, ram_h(t))))
keyval(FIRE_FAC, [(0, 0.0), (T_IGN - 0.02, 0.0), (T_IGN + 0.08, 1.0), (T_SLAM + 0.1, 0.7), (T_BLAST, 0.7), (T_BLAST + 0.1, 1.0),
                  (T_THROW + 0.5, 1.0), (T_THROW + 1.1, 0.0)])
keyval(FIRE_STR, [(0, 3.0), (T_IGN + 0.08, 8.0), (T_IGN + 0.6, 4.0), (T_BLAST + 0.1, 10.0), (T_BLAST + 0.8, 5.0)])
windows(AIR, [(T_CYL + 0.8, R0)]); windows(FIRE, [(T_IGN - 0.05, R0)])
# fuel spray from the injector
DROPS = []
for k in range(12):
    d = par(cyl(f"Fuel{k}", 0.035, 0.07, "Y", (0, 0, 0), M_FUEL, seg=8), HAM); DROPS.append(d)
    ang = math.radians(random.uniform(-14, 14)); spd = random.uniform(0.75, 1.0); dl = 0.035 * k
    def fl(t, ang=ang, spd=spd, dl=dl):
        p = lin((t - T_SPRAY - dl) / 0.55) * spd
        return (-0.45 + 0.85 * p * math.cos(ang), -0.05, ANV_TOP + 0.24 + 0.85 * p * math.sin(ang) - 0.08 * p * p)
    bake_loc(d, fl); windows(d, [(T_SPRAY - 0.02, T_IGN + 0.05)])
# blast light + exhaust puffs (pool of 4)
BL_D = bpy.data.lights.new("BlastLight", "POINT"); BL_D.color = (1.0, 0.55, 0.20); BL_D.shadow_soft_size = 0.4
BL = bpy.data.objects.new("BlastLight", BL_D); scene.collection.objects.link(BL); par(BL, HAM); BL.location = (0.0, -1.4, ANV_TOP + 0.3)
def blast_e(t):
    e = 0.0
    for b in IMPACTS:
        if b - 0.02 <= t < b + 0.45: e = max(e, 1800.0 * (1 - lin((t - b) / 0.45)))
    if T_IGN <= t < T_THROW + 1.0: e = max(e, 250.0 + (900.0 if t >= T_BLAST else 0.0) * (1 - lin((t - T_THROW - 0.4) / 0.6)))
    return e
bake_scalar(BL_D, "energy", [blast_e(t) for t in TS])
PUFFS = []
for k in range(4):
    pf = par(lathe(f"Puff{k}", [(0.0, -1.0)] + [(math.sin(a * math.pi / 8), -math.cos(a * math.pi / 8)) for a in range(1, 8)] + [(0.0, 1.0)],
                   M_PUFF, 0.0, 2 * math.pi, 16), HAM)
    PUFFS.append(pf)
    mine = [b for i, b in enumerate(IMPACTS) if i % 4 == k]
    def age(t, mine=mine):
        a = [t - b for b in mine if 0 <= t - b < 1.4]; return min(a) if a else None
    bake_loc(pf, lambda t, age=age: (0.8 * (age(t) or 0), 0.3, 7.4 + 2.6 * (age(t) or 0)))
    bake_scale(pf, lambda t, age=age: (lambda a: (0.001,) * 3 if a is None else (0.35 + 1.6 * ease(a / 1.4),) * 3)(age(t)))
# arrows: pile down, ram up
bm = bmesh.new(); add_arrow(bm, (1.25, 0.4), (0, -1), 2.2, 0.9); AD = par(mesh_obj("ArrowDown", bm, M_GOLD), HAM); AD.location.y = -0.75
windows(AD, [(T_DRV, T_THROW - 0.1)])
bm = bmesh.new(); add_arrow(bm, (1.25, 3.0), (0, 1), 2.6, 0.9); AU = par(mesh_obj("ArrowUp", bm, M_GOLD), HAM); AU.location.y = -0.75
windows(AU, [(T_THROW, T_FALLS)])
OWN = {CYL.name, "GuideArms", AIR.name, FIRE.name, AD.name, AU.name} | {d.name for d in DROPS}
def win1(o, wins):
    key(o, "hide_render", 1, True, "CONSTANT"); key(o, "hide_viewport", 1, True, "CONSTANT")
    for t0, t1 in wins:
        fr0 = 1 if t0 <= 0 else F(t0)
        key(o, "hide_render", fr0, False, "CONSTANT"); key(o, "hide_viewport", fr0, False, "CONSTANT")
        if t1 < DUR: key(o, "hide_render", F(t1), True, "CONSTANT"); key(o, "hide_viewport", F(t1), True, "CONSTANT")
HAM_WIN = [(0, T_DW), (T_SO, DUR)]
for o in HAM.children_recursive:
    if o.name not in OWN and o.type != "LIGHT" and not o.name.startswith("Puff"): win1(o, HAM_WIN)
GA = bpy.data.objects["GuideArms"]; win1(GA, [(0, T_DW), (T_CYL, DUR)])

# ================= the first pile drivers: a heavy weight on a rope =================
WTS = PW([(0, 6.0)])
def wh(t):
    d1, d2 = DROP_IMP
    if t < C["dropped"]: return 6.0
    if t < d1: return 6.0 * (1 - lin((t - C["dropped"]) / (d1 - C["dropped"])) ** 2)
    if t < C["lift"]: return 0.0
    if t < C["drop"]: return 6.0 * ease((t - C["lift"]) / (C["drop"] - C["lift"] - 0.05))
    if t < d2: return 6.0 * (1 - lin((t - C["drop"]) / (d2 - C["drop"])) ** 2)
    if t < C["lift2"]: return 0.0
    return 6.0 * ease((t - C["lift2"]) / 1.6)
M_IRON, _ = mat("Iron", (0.07, 0.07, 0.08), 0.6, 0.5)
WGT = box("DropWeight", -0.75, 0.75, -0.75, 0.75, 0.0, 2.6, M_IRON); bake_loc(WGT, lambda t: (0.0, 0.0, top1(t) + wh(t)))
CAB = cyl("Cable", 0.05, 1.0, "Z", (0, 0, 0.5), M_DARK, seg=8)
bake_loc(CAB, lambda t: (0.0, 0.3, top1(t) + wh(t) + 2.6)); bake_scale(CAB, lambda t: (1.0, 1.0, max(0.01, 43.0 - top1(t) - wh(t) - 2.6)))
windows(WGT, [(T_DW, T_SO)]); windows(CAB, [(T_DW, T_SO)])

# ================= demo 1: hammer + tent stake (x = 200) =================
SX = 200.0
box("StakeGrass", SX - 6, SX + 6, 0.0, 8.0, -0.12, 0.0, M_GRASS); box("StakeTop", SX - 6, SX + 6, 0.0, 8.0, -1.2, -0.12, M_TOP)
box("StakeClay", SX - 6, SX + 6, 0.0, 8.0, -5.0, -1.2, M_CLAY)
def stake_top(t):
    hits = STAKE_HITS[:3] if t < T_THIS - 0.1 else STAKE_HITS[3:]
    return 1.7 - sum(0.38 * lin((t - h) / 0.06) for h in hits)
bm = bmesh.new(); add_box(bm, -0.16, 0.16, -0.02, 0.30, -2.0, 0.0)
tip = [v for v in bm.verts if v.co.z < -1.99]
for v in tip: v.co.x *= 0.15
bmesh.ops.translate(bm, verts=tip, vec=(0, 0, -0.35))
STK = mesh_obj("Stake", bm, M_WOOD); bake_loc(STK, lambda t: (SX, 0.0, stake_top(t)))
HP = empty("HammerPivot"); bake_loc(HP, lambda t: (SX + 1.1, -0.35, stake_top(t) + 0.37))
def swing(t):
    a = 62.0
    for h in STAKE_HITS:
        if h - 0.26 <= t < h: a = min(a, 62.0 * lin((h - t) / 0.26) ** 0.6)
        elif h <= t < h + 0.40: a = min(a, 62.0 * ease((t - h - 0.06) / 0.34))
    return math.radians(a)
bake(HP, "rotation_euler", 1, [swing(t) for t in TS])
par(box("HHandle", -1.05, 0.30, -0.06, 0.06, -0.06, 0.06, M_HANDLE), HP)
par(box("HHead", -1.26, -0.94, -0.16, 0.16, -0.37, 0.37, M_HHEAD), HP)

# ================= demo 2: a crooked blow crushes the pile head (x = 100) =================
CX = 100.0
box("CrookGrass", CX - 6, CX + 6, 0.0, 8.0, -0.12, 0.0, M_GRASS); box("CrookTop", CX - 6, CX + 6, 0.0, 8.0, -1.5, -0.12, M_TOP)
box("CrookClay", CX - 6, CX + 6, 0.0, 8.0, -6.0, -1.5, M_CLAY)
SA = half_pile("StubIntact", 0.40, 6.0, M_PILE, CX); SA.location.z = -4.4
SB = half_pile("StubCrushed", 0.40, 5.6, M_PILE, CX); SB.location.z = -4.4
MUSH = lathe("CrushedHead", [(0.0, 1.1), (0.40, 1.1), (0.52, 1.25), (0.66, 1.36), (0.60, 1.46), (0.30, 1.42), (0.0, 1.38)], M_CRUSH, 0.0, math.pi, 32, (CX, 0, 0))
MUSH.rotation_euler = (0, math.radians(-9), 0)
windows(SA, [(0, C["crushed"])]); windows(SB, [(C["crushed"], DUR)]); windows(MUSH, [(C["crushed"], DUR)])
glow(B_CRUSH, [(0, 0.0)] + pulse(C["crushed"], 2.2, hold=0.8, down=0.5))
CH = box("CrookHammer", -0.8, 0.8, -0.7, 0.7, 0.0, 2.6, M_CYL)
CH.rotation_euler = (0, math.radians(14), 0)
def crook_z(t):
    h1, h2 = CROOK_HITS
    if t < h1: return 1.62 + 3.5 * (1 - lin((t - (h1 - 0.38)) / 0.38) ** 2)
    if t < h2 - 0.38: return 1.62 + 2.6 * ease((t - h1 - 0.15) / 0.8)
    if t < h2: return 1.52 + 2.7 * (1 - lin((t - (h2 - 0.38)) / 0.38) ** 2)
    return 1.52
bake_loc(CH, lambda t: (CX + 0.32, -0.05, crook_z(t)))
CL_D = bpy.data.lights.new("CrookFlash", "POINT"); CL_D.color = (1.0, 0.35, 0.25)
CLF = bpy.data.objects.new("CrookFlash", CL_D); scene.collection.objects.link(CLF); CLF.location = (CX + 0.6, -1.2, 1.6)
bake_scalar(CL_D, "energy", [max([0.0] + [600.0 * (1 - lin((t - h) / 0.5)) for h in CROOK_HITS if h <= t]) for t in TS])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
Z = lambda dz: (lambda t: HZ(t) + dz)
STK_CAM = ((SX + 0.6, -7.6, 1.3), (SX + 0.25, 0.0, 0.5))
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *STK_CAM, 32),
    (T_SITE - 0.05, (SX + 0.6, -7.0, 1.2), (SX + 0.25, 0.0, 0.5), 32),
    (T_SITE, (9.0, -30.0, 15.0), (0.0, 0.0, 11.0), 20, "cut"),
    (C["except"] - 0.2, (7.0, -26.0, 17.0), (0.0, 0.0, 13.0), 20),
    (C["lifts"], (2.5, -15.0, Z(5.0)), (0.0, 0.0, Z(5.0)), 24),
    (T_LAND - 0.05, (2.2, -13.5, Z(5.5)), (0.0, 0.0, Z(5.5)), 24),
    (T_LAND, (CX + 1.3, -8.5, 1.8), (CX + 0.2, 0.0, 1.0), 30, "cut"),
    (T_THIS - 0.05, (CX + 1.0, -7.6, 1.6), (CX + 0.2, 0.0, 1.0), 30),
    (T_THIS, *STK_CAM, 32, "cut"),
    (T_TOWER - 0.05, (SX + 0.5, -7.0, 1.2), (SX + 0.25, 0.0, 0.5), 32),
    (T_TOWER, (-2.0, -62.0, 8.0), (-4.0, 0.0, 4.0), 22, "cut"),
    (T_DW - 0.05, (-3.0, -58.0, 8.0), (-4.0, 0.0, 4.0), 22),
    (T_DW, (3.0, -14.0, Z(4.5)), (0.0, 0.0, Z(3.5)), 26, "cut"),
    (T_SO - 0.05, (2.5, -13.0, Z(4.5)), (0.0, 0.0, Z(3.5)), 26),
    (T_SO, (1.6, -10.5, Z(4.6)), (0.0, 0.0, Z(4.2)), 30, "cut"),
    (T_FALL, (1.4, -9.5, Z(4.0)), (0.0, 0.0, Z(3.6)), 30),
    (T_HOT, (0.9, -6.2, Z(2.5)), (0.0, 0.0, Z(2.2)), 30),
    (T_IGN + 0.4, (0.8, -5.8, Z(2.4)), (0.0, 0.0, Z(2.1)), 30),
    (T_SLAM - 0.3, (1.2, -8.5, Z(3.2)), (0.0, 0.0, Z(2.8)), 30),
    (T_DRV - 0.1, (1.8, -12.0, Z(3.0)), (0.0, 0.0, Z(2.5)), 28),
    (T_THROW, (2.2, -14.0, Z(5.0)), (0.0, 0.0, Z(4.5)), 28),
    (T_FALLS - 0.05, (2.2, -14.0, Z(5.0)), (0.0, 0.0, Z(4.5)), 28),
    (T_FALLS, (6.0, -38.0, -2.0), (0.0, 0.0, -4.0), 20, "cut"),
    (T_FRAME - 0.05, (5.5, -36.0, -3.0), (0.0, 0.0, -5.0), 20),
    (T_FRAME, (-7.0, -21.0, Z(9.0)), (0.0, 1.0, Z(12.0)), 22, "cut"),
    (T_HELM - 0.05, (-6.0, -19.0, Z(9.0)), (0.0, 1.0, Z(11.0)), 22),
    (T_HELM, (1.0, -5.2, Z(1.2)), (0.0, 0.0, Z(0.6)), 30, "cut"),
    (T_CREW - 0.05, (1.0, -5.0, Z(1.2)), (0.0, 0.0, Z(0.6)), 30),
    (T_CREW, (4.0, -40.0, -12.0), (0.0, 0.0, -16.0), 22, "cut"),
    (T_NEXT - 0.05, (4.0, -38.0, -12.0), (0.0, 0.0, -16.0), 22),
    (T_NEXT, (-2.0, -66.0, 10.0), (-2.0, 0.0, 8.0), 22, "cut"),
    (T_CTA - 0.05, (-1.0, -64.0, 10.0), (-2.0, 0.0, 8.0), 22),
    (DUR, (0.0, -76.0, 12.0), (-1.0, 0.0, 8.0), 22),
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
    cam_loc.append(l0 + Vector((0.02 * math.sin(t * 0.7), 0.0, 0.015 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)

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
    try: sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"])
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
bg.inputs["Strength"].default_value = 0.22
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.angle = math.radians(3); sun_d.energy = 2.6
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(-35))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (1.0, 0.95, 0.88); fill_d.energy = 2500
bake_scalar(fill_d, "energy", [max(40.0, min(2500.0, 2500.0 * ((cl - ct).length / 45.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)

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
    "ram": lambda t: Vector((RX(t) + 0.47, -0.1, HZ(t) + ANV_TOP + ram_h(t) + 1.6)),
    "cyl": lambda t: Vector((RX(t) + 0.68, -0.1, HZ(t) + 5.0)),
    "gap": lambda t: Vector((RX(t) + 0.45, -0.1, HZ(t) + ANV_TOP + max(0.1, ram_h(t)) * 0.5)),
    "injector": lambda t: Vector((RX(t) - 0.86, -0.1, HZ(t) + ANV_TOP + 0.23)),
    "anvil": lambda t: Vector((RX(t) + 0.48, -0.1, HZ(t) + 1.35)),
    "helmet": lambda t: Vector((RX(t) + 0.64, -0.1, HZ(t) + 0.4)),
    "leads": lambda t: Vector((RX(t) + 0.75, 1.1, min(40.0, HZ(t) + 14.0))),
    "pile": lambda t: Vector((RX(t) + 0.4, -0.1, -1.0)),
    "toe": lambda t: Vector((0.4, -0.1, toe1(t))),
    "gravel": lambda t: Vector((6.0, -0.1, -29.0)),
    "weight": lambda t: Vector((0.75, -0.1, top1(t) + wh(t) + 1.3)),
    "stake": lambda t: Vector((SX + 0.16, -0.1, stake_top(t) - 0.8)),
    "crush": lambda t: Vector((CX + 0.6, -0.1, 1.35)),
    "gpile": lambda t: Vector((-9.6, -0.1, -18.0)),
    "tower": lambda t: Vector((3.0, 1.0, 40.0)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"stake_hits": [round(x, 3) for x in STAKE_HITS], "hook_blows": [round(x, 3) for x in HOOK_B[1:]], "launch": round(HOOK_B[-1], 3),
          "crook_hits": [round(x, 3) for x in CROOK_HITS], "drops": [round(x, 3) for x in DROP_IMP], "lifts": [round(C["lift"], 3), round(C["lift2"], 3)],
          "cyl": RR(T_CYL + 0.1, T_CYL + 0.8), "fall": RR(T_FALL, T_HOT), "spray": RR(T_SPRAY, T_SPRAY + 0.6), "ignite": round(T_IGN, 3),
          "slam": round(T_SLAM + 0.1, 3), "blast": round(T_BLAST, 3), "drive": RR(T_DRV + 0.2, T_DRV + 0.65), "throw": RR(T_THROW, T_THROW + 0.85),
          "rapid": RAPID, "cta_blows": CTA_B, "move": RR(T_NEXT, T_MOVE1), "piles_in": [round(T_NEXT + 0.15 + 0.35 * k + 0.55, 3) for k in range(3)],
          "tower_rise": RR(C["tower2"] - 0.2, C["tower2"] + 1.0), "cta": round(T_CTA, 3)}
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
