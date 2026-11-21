# Roman aqueduct (3d-34): how Roman aqueducts moved water with only gravity. Claim-first hook ("The water on top of this bridge drops
# less than an inch from one end to the other.") on the channel on top of a three-tier Roman aqueduct bridge (Pont du Gard type):
# cyan water flows in the cut-open channel, a gold level line + ruler -> pull back over the valley (30 miles, no pumps, gravity) ->
# stake: a red wrongly-tilted ghost, the water stops -> establishing shot -> map set: spring barely higher than the city, the channel
# winds and grows across the hills -> underground set: buried stone channel in a soil section, waterproof lining glows, lime + crushed
# tile heaps -> valley: the route reaches the bridge, the three tiers rise, 160 ft arrow -> block set: dry-laid stones drop in (rigid
# body + dust), joints glow (no mortar) -> sunset wide (still standing) -> siphon set: header tank, lead pipes down one side and up the
# other, red pressure at the bottom (Mantaflow header-tank fill, laptop bake) -> castellum set: round tank splits the flow into 10
# pipes -> sinter set: limestone layers grow inside the channel, chunks are chipped out (rigid body + dust) -> CTA wide push-in.
# Illustrative (1 unit = 1 m): generic three-tier arched aqueduct bridge in the proportions of the Pont du Gard (~49 m, 6/11/35
# arches), map not to scale, siphon/castellum generic. No logos, no people.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu] [--bake-fluid]
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view


ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 1.0, 2)   # CTA ending (19-20 Nov): complete question + "Tell me in the comments.", then ~1 s fade
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(34)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("the", "The"), ("bridge", "bridge"), ("drops", "drops"), ("inch", "inch"), ("thats", "That's"), ("purpose", "purpose."),
        ("romans", "Romans"), ("thirty", "thirty"), ("no", "no"), ("pumps", "pumps,"), ("only", "only"), ("gravity", "gravity,"),
        ("slope", "slope"), ("gentle", "gentle"), ("bad", "bad"), ("stop", "stop"), ("this", "This"), ("pont", "Pont"), ("france", "France,"),
        ("built", "built"), ("fifty", "fifty"), ("city", "city"), ("nimes", "Nîmes."), ("springs", "springs"), ("barely", "barely"),
        ("city2", "city,"), ("channel", "channel"), ("winds", "winds"), ("thirty2", "thirty"), ("falling", "falling"), ("most", "Most"),
        ("underground", "underground:"), ("stone", "stone"), ("lined", "lined"), ("waterproof", "waterproof"), ("mortar", "mortar"),
        ("lime", "lime"), ("crushed", "crushed"), ("tile", "tile."), ("arches", "Arches"), ("valley", "valley"), ("here", "Here,"),
        ("three", "three"), ("tiers", "tiers"), ("lift", "lift"), ("one", "one"), ("feet", "feet"), ("river", "river."), ("some", "Some"),
        ("stones", "stones"), ("six", "six"), ("tons", "tons,"), ("stacked", "stacked"), ("nomortar", "mortar"), ("still", "still"),
        ("two", "two"), ("years", "years"), ("deeper", "deeper"), ("romans2", "Romans"), ("sealed", "sealed"), ("lead", "lead"),
        ("pipes", "pipes."), ("water3", "Water"), ("rushes", "rushes"), ("down", "down"), ("pressure", "pressure"), ("pushes", "pushes"),
        ("up", "up"), ("other", "other."), ("at", "At"), ("round", "round"), ("tank", "tank"), ("split", "split"), ("ten", "ten"),
        ("pipes2", "pipes."), ("but", "But"), ("dissolved", "dissolved"), ("limestone", "limestone."), ("coated", "coated"),
        ("layer", "layer"), ("crews", "crews"), ("chipped", "chipped"), ("every", "every"), ("would", "Would"), ("drink", "drink"),
        ("thirty3", "thirty"), ("stone2", "stone?"), ("tell", "Tell"), ("comments", "comments.")]
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
CL = coll("Aqueduct")
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

# ================= fx power-ups (pipeline3d/fx.py, Rizky 15 Nov 2026) =================
sys.path.insert(0, os.path.join(HERE, "..", "..", "pipeline3d"))
import fx
NODE = lambda nt, kind: nt.nodes.new(kind)
def MATH(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: nt.links.new(v, n.inputs[i])
    return n.outputs[0]
def VALUE(nt, name, keys):
    v = nt.nodes.new("ShaderNodeValue"); v.name = name; keyval(v.outputs[0], keys); return v.outputs[0]



# ================= extra helpers =================
FLUID_BAKE = "--bake-fluid" in ARGS
def add_seg(bm, p0, p1, r, seg=8, mi=0):
    """Round tube segment between two points."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    if L < 1e-6: return
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L); vs = res["verts"]
    M = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
def add_poly(bm, pts, r, seg=8, mi=0):
    for a, b in zip(pts, pts[1:]): add_seg(bm, a, b, r, seg, mi)
def sag_pts(a, b, sag, n=14):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, 4 * sag * (i / n) * (1 - i / n))) for i in range(n + 1)]
def poly_obj(name, pts, r, m_, seg=8):
    bm = bmesh.new(); add_poly(bm, pts, r, seg); return mesh_obj(name, bm, m_)
class Path:
    def __init__(self, pts):
        self.p = [Vector(x) for x in pts]; self.s = [0.0]
        for a, b in zip(self.p, self.p[1:]): self.s.append(self.s[-1] + (b - a).length)
        self.L = self.s[-1]
    def at(self, s):
        import bisect
        s = max(0.0, min(self.L, s)); i = min(len(self.p) - 2, max(0, bisect.bisect_right(self.s, s) - 1))
        seg = self.s[i + 1] - self.s[i]
        return self.p[i].lerp(self.p[i + 1], (s - self.s[i]) / seg if seg > 0 else 0)
def sphere_mesh(name, r, sub=2):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    try: me.shade_smooth()
    except Exception: pass
    return me
def obj_from(name, me, m_=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); CL.objects.link(o); o.location = loc
    if m_ and not me.materials: me.materials.append(m_)
    return o
def beads(name, path, n, r, m_, wins, speed, scale_fn=None, loop_period=None):
    """n glowing beads running along a Path, visible only inside wins. loop_period makes t=0 and t=DUR identical."""
    me = sphere_mesh(name, r); me.materials.append(m_); out = []
    gap = path.L / n
    for i in range(n):
        o = obj_from(f"{name}{i}", me)
        def fn(t, i=i):
            if loop_period: u = (t % loop_period) / loop_period; s = (u + i / n) % 1.0 * path.L
            else: s = (i * gap + speed * t) % path.L
            return tuple(path.at(s))
        bake_loc(o, fn)
        if scale_fn: bake_scale(o, lambda t, i=i: (scale_fn(t, i),) * 3)
        windows(o, wins); out.append(o)
    return out
def emit_mat(name, rgb, strength):
    m, b = mat(name, (0.02, 0.02, 0.02), rough=0.5, emit_rgb=rgb); b.inputs["Emission Strength"].default_value = strength; return m, b


# ================= sweep tubes (one watertight mesh per pipe, for booleans) =================
def chaikin(pts, it=3):
    p = [Vector(x) for x in pts]
    for _ in range(it):
        q = [p[0]]
        for a, b in zip(p, p[1:]): q += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
        q.append(p[-1]); p = q
    return p
def sweep_bm(pts, radii, seg=28, cap=True):
    bm = bmesh.new(); rings = []
    n = len(pts); t_prev = None; nrm = None
    for i, p in enumerate(pts):
        t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        if nrm is None:
            a = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0)); nrm = (a - t * a.dot(t)).normalized()
        else:
            nrm = (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm); r = radii[i]
        rings.append([bm.verts.new(p + r * (math.cos(2 * math.pi * k / seg) * nrm + math.sin(2 * math.pi * k / seg) * b)) for k in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new([r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]])
    if cap:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
def interp_r(pts, keys):
    """radius per point from (fraction of length, r) keys."""
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + (b - a).length)
    out = []
    for si in s:
        u = si / s[-1]
        for (u0, r0), (u1, r1) in zip(keys, keys[1:]):
            if u <= u1: out.append(r0 + (r1 - r0) * ((u - u0) / (u1 - u0) if u1 > u0 else 1)); break
        else: out.append(keys[-1][1])
    return out
def half_pipe(name, pts, radii, m_, seg=32):
    bm = sweep_bm(pts, radii, seg, cap=False); cut_front(bm, 0.0, fill=False)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def cutter(name, pts, radii, seg=28):
    o = mesh_obj(name, sweep_bm(pts, radii, seg, cap=True), None); o.hide_render = True; o.display_type = "WIRE"; return o
def boolean(target, cut, name="Cut"):
    md = target.modifiers.new(name, "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cut
    try: md.solver = "EXACT"
    except Exception: pass
    return md



# ================= timing =================
C["layer2"] = next(round(VO + w["start"], 3) for w in WORDS if norm(w["text"]) == "layer" and VO + w["start"] > C["layer"] + 0.05)
T_HOOK = (0.0, C["romans"]); T_PULL = (C["romans"], C["slope"]); T_STAKE = (C["slope"], C["this"]); T_EST = (C["this"], C["springs"])
T_MAP = (C["springs"], C["most"]); T_UG = (C["most"], C["arches"]); T_VALLEY = (C["arches"], C["some"]); T_BLOCK = (C["some"], C["still"])
T_SUNSET = (C["still"], C["deeper"]); T_SIPH = (C["deeper"], C["at"]); T_CAST = (C["at"], C["but"]); T_SINTER = (C["but"], C["would"])
T_CTA = (C["would"], DUR)
MX, UX, BX, SX, CX = 10000.0, 20000.0, 30000.0, 40000.0, 50000.0     # far-apart sets (camera clip 3 km)

def windows_r(obj, wins):
    """render-only visibility (rigid bodies must stay in the sim)"""
    def kr(o, fr, h): key(o, "hide_render", fr, h, "CONSTANT")
    kr(obj, 1, True)
    for t0, t1 in wins:
        kr(obj, 1 if t0 <= 0 else F(t0), False)
        if t1 < DUR: kr(obj, F(t1), True)

# ================= materials =================
def strata(name, cols, scale=0.045, bump=0.35):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 8.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].color = (*cols[0], 1); e[1].color = (*cols[-1], 1)
    for i, c_ in enumerate(cols[1:-1]):
        el = e.new((i + 1) / (len(cols) - 1)); el.color = (*c_, 1)
    L.new(wv.outputs["Fac"], cr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[0].default_value = 0.25
    L.new(cr.outputs[0], mx.inputs[6]); L.new(nz.outputs["Fac"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
def stone(name, rgb1, rgb2, scale, row=0.55, plane="XZ"):
    """dry-laid ashlar: brick texture (object coords) + noise + bump on the joints."""
    m = tiles(name, rgb1, rgb2, scale, plane); nt = m.node_tree; N, L = nt.nodes, nt.links
    br = next(n for n in N if n.type == "TEX_BRICK"); br.inputs["Row Height"].default_value = row; br.inputs["Mortar Size"].default_value = 0.012
    br.offset = 0.5; br.inputs["Mortar"].default_value = (0.20, 0.17, 0.13, 1)
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED"); b.inputs["Roughness"].default_value = 0.85
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[0].default_value = 0.18
    L.new(br.outputs["Color"], mx.inputs[6]); L.new(nz.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (0.98, 0.74, 0.27, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
M_STONE, B_STONE = stone("Limestone", (0.66, 0.54, 0.38), (0.56, 0.45, 0.31), 0.62)
M_STONEY, _ = stone("LimestoneSide", (0.66, 0.54, 0.38), (0.56, 0.45, 0.31), 0.62, plane="XY")
M_CHAN, B_CHAN = stone("ChannelStone", (0.58, 0.50, 0.38), (0.50, 0.42, 0.31), 1.6, row=0.6)
M_CHANY, _ = stone("ChannelStoneY", (0.58, 0.50, 0.38), (0.50, 0.42, 0.31), 1.6, row=0.6, plane="XY")
M_SOIL = strata("Soil", [(0.16, 0.10, 0.05), (0.27, 0.17, 0.09), (0.20, 0.13, 0.07), (0.33, 0.23, 0.13)], scale=0.25, bump=0.5)
M_ROCKS = strata("RockSection", [(0.30, 0.26, 0.20), (0.40, 0.34, 0.25), (0.34, 0.29, 0.22), (0.46, 0.40, 0.30)], scale=0.04)
M_GRASS, _ = mat("Garrigue", (0.20, 0.22, 0.09), rough=0.95, noise=0.05)
M_DIRT, _ = mat("Dirt", (0.40, 0.33, 0.22), rough=0.95, noise=0.2)
M_LINING, B_LINING = mat("OpusSigninum", (0.60, 0.30, 0.22), rough=0.6, noise=6.0, emit_rgb=(0.98, 0.74, 0.27))
M_LIME, B_LIME = mat("Lime", (0.88, 0.87, 0.82), rough=0.9, noise=4.0)
M_TILE, B_TILE = mat("CrushedTile", (0.55, 0.20, 0.10), rough=0.9, noise=8.0)
M_SINTER, B_SINTER = mat("Sinter", (0.86, 0.80, 0.64), rough=0.7, noise=5.0, emit_rgb=(0.98, 0.74, 0.27))
M_LEAD, B_LEAD = mat("Lead", (0.36, 0.37, 0.40), rough=0.45, metallic=0.7, emit_rgb=(1.0, 0.18, 0.08))
M_LEADB, B_LEADB = mat("LeadBottom", (0.36, 0.37, 0.40), rough=0.45, metallic=0.7, emit_rgb=(1.0, 0.18, 0.08))
M_DARK, _ = mat("Dark", (0.06, 0.05, 0.05), rough=0.8)
M_TREE, _ = mat("Pine", (0.07, 0.13, 0.05), rough=0.9, noise=2.0)
M_TRUNK, _ = mat("Trunk", (0.18, 0.11, 0.06), rough=0.9)
M_HOUSE, _ = mat("HouseWall", (0.78, 0.70, 0.56), rough=0.8, noise=1.0)
M_ROOF, _ = mat("RoofTile", (0.55, 0.22, 0.12), rough=0.7)
M_PAVE, _ = stone("Paving", (0.55, 0.50, 0.42), (0.48, 0.43, 0.36), 0.8, row=1.0, plane="XY")
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 6.0)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 7.0)
M_REDG, B_REDG = emit_mat("RedGlow", (1.0, 0.18, 0.08), 6.0)
M_WHITEG, B_WHITEG = emit_mat("WhiteGlow", (1.0, 1.0, 1.0), 4.0)
M_JOINT, B_JOINT = emit_mat("JointGlow", (0.30, 0.92, 1.0), 0.0)
M_ROUTE, B_ROUTE = emit_mat("RouteGlow", (0.30, 0.92, 1.0), 5.0)
M_WATER, B_WATER, _V = water_sec("ChannelWater", dens=0.25)
M_RIVER, B_RIVER, _V2 = water_sec("RiverWater", vol_rgb=(0.10, 0.36, 0.34), dens=0.05)
M_INV, INV_FAC = ghost("Invisible", (1, 1, 1))

# ================= main set: valley + three-tier bridge (bridge along x, faces -y) =================
HK = [(0, -3.0), (15, -3.0), (19, 0.3), (77, 22.0), (121, 40.5), (138, 47.2), (260, 60.0), (500, 75.0), (1300, 95.0)]
def h_x(ax):
    for (x0, z0), (x1, z1) in zip(HK, HK[1:]):
        if ax <= x1: return z0 + (z1 - z0) * (ax - x0) / (x1 - x0)
    return HK[-1][1]
def terrain_h(x, y):
    base = h_x(abs(x))
    n = 2.2 * math.sin(x * 0.031 + 1.3) * math.cos(y * 0.027) + 1.4 * math.sin(y * 0.05 + x * 0.013)
    return base + (n if abs(x) > 22 else 0.0) + 0.0008 * max(0.0, abs(y) - 60) ** 1.5 * (1 if abs(x) > 30 else 0.3)
def grid(name, x0, x1, y0, y1, nx, ny, hf, m_, off=(0, 0, 0)):
    bm = bmesh.new(); vs = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx; y = y0 + (y1 - y0) * j / ny
            row.append(bm.verts.new((x + off[0], y + off[1], hf(x, y) + off[2])))
        vs.append(row)
    for j in range(ny):
        for i in range(nx): bm.faces.new([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]])
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
TERR = grid("Valley", -1300, 1300, -1300, 1300, 130, 130, terrain_h, M_GRASS)
M_RIVERS, _ = mat("RiverSurface", (0.07, 0.24, 0.26), rough=0.06)
RIVERW = box("RiverGardon", -19.5, 19.5, -1300, 1300, -3.0, -0.5, M_RIVERS)

def add_bay(bm, xa, xb, z0, z1, span, y0, y1, crown=1.4, seg=14):
    """one arch bay between xa..xb: two piers + a semicircular arch ring + spandrel up to z1 (front y0, back y1)."""
    xc, w = (xa + xb) / 2, xb - xa; r = span / 2; zs = z1 - crown - r
    add_box(bm, xa, xc - r, y0, y1, z0, zs); add_box(bm, xc + r, xb, y0, y1, z0, zs)
    a1 = math.atan2(z1 - zs, w / 2)
    angs = sorted(set([math.pi * k / seg for k in range(seg + 1)] + [a1, math.pi - a1]))
    inner, outer = [], []
    for a in angs:
        ca, sa = math.cos(a), math.sin(a)
        inner.append((xc + r * ca, zs + r * sa))
        tt = []
        if abs(ca) > 1e-6: tt.append((w / 2) / abs(ca))
        if sa > 1e-6: tt.append((z1 - zs) / sa)
        tq = min(tt); outer.append((xc + tq * ca, zs + tq * sa))
    F_ = [[bm.verts.new((x, y0, z)) for x, z in inner], [bm.verts.new((x, y0, z)) for x, z in outer]]
    B_ = [[bm.verts.new((x, y1, z)) for x, z in inner], [bm.verts.new((x, y1, z)) for x, z in outer]]
    for k in range(len(angs) - 1):
        for quad in ([F_[0][k], F_[0][k + 1], F_[1][k + 1], F_[1][k]], [B_[1][k], B_[1][k + 1], B_[0][k + 1], B_[0][k]],
                     [F_[0][k], B_[0][k], B_[0][k + 1], F_[0][k + 1]], [F_[1][k + 1], B_[1][k + 1], B_[1][k], F_[1][k]]):
            try: bm.faces.new(quad)
            except ValueError: pass
    return zs
def tier(name, edges, z0, z1, yh, span_fn, m_):
    bm = bmesh.new()
    for xa, xb in zip(edges, edges[1:]): add_bay(bm, xa, xb, z0, z1, span_fn(xb - xa), -yh, yh)
    add_box(bm, edges[0] - 0.4, edges[-1] + 0.4, -yh - 0.35, yh + 0.35, z1, z1 + 0.6)      # cornice course
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_)
E1 = [-77, -55, -37, -15, 15, 37, 55, 77]
E2 = [-121, -99, -77, -55, -37, -15, 15, 37, 55, 77, 99, 121]
E3 = [-137.5 + 275.0 * k / 35 for k in range(36)]
Z1, Z2, Z3 = 21.0, 40.5, 46.6
TIER1 = tier("Tier1", E1, -4.0, Z1, 3.0, lambda w: w - 4.6, M_STONE)
TIER2 = tier("Tier2", E2, Z1 + 0.6, Z2, 2.25, lambda w: w - 4.2, M_STONE)
TIER3 = tier("Tier3", E3, Z2 + 0.6, Z3, 1.5, lambda w: w - 2.2, M_STONE)
# channel (specus) on top: floor, two walls, cover slabs; front wall + covers cut away for x in [-70, 40] (hook cutaway)
TOP = empty("ChannelTop")
CW, CWT, CF0, CF1, CH = 0.6, 0.6, Z3 + 0.6, Z3 + 1.2, Z3 + 3.0
WZ0, WZ1 = CF1, CF1 + 0.95
CUT0, CUT1 = -70.0, 40.0
bm = bmesh.new()
add_box(bm, -160, 160, -CW - CWT, CW + CWT, CF0, CF1)
add_box(bm, -160, 160, CW, CW + CWT, CF1, CH)
add_box(bm, -160, CUT0, -CW - CWT, -CW, CF1, CH); add_box(bm, CUT1, 160, -CW - CWT, -CW, CF1, CH)
CHAN = mesh_obj("Channel", bm, M_CHAN, parent=TOP)
bm = bmesh.new()
for k in range(160):
    x0 = -160 + 2.0 * k
    if x0 + 2.0 > CUT0 and x0 < CUT1: continue
    add_box(bm, x0 + 0.02, x0 + 1.98, -CW - CWT - 0.15, CW + CWT + 0.15, CH, CH + 0.4)
COVERS = mesh_obj("CoverSlabs", bm, M_CHANY, parent=TOP)
WATER = box("ChannelWaterBox", -160, 160, -CW + 0.01, CW - 0.01, WZ0, WZ1, M_WATER, parent=TOP)
LEVEL = box("LevelLine", CUT0, CUT1, -CW - 0.02, -CW + 0.06, WZ1 - 0.03, WZ1 + 0.05, M_GOLDG, parent=TOP)
windows(LEVEL, [(C["drops"] - 0.1, C["romans"])])
glow(B_GOLDG, [(0, 6.0)])
RULER = box("RulerTick", CUT1 - 0.06, CUT1 + 0.06, -CW - 0.03, -CW + 0.05, WZ1 - 0.45, WZ1 + 0.45, M_GOLDG, parent=TOP)
windows(RULER, [(C["inch"] - 0.1, C["romans"])])
# stake: red ghost of a wrongly tilted water line (the slope tips the wrong way, the flow stops)
GHOST = box("WrongSlopeGhost", -55.0, 25.0, -CW - 0.04, -CW + 0.04, -0.05, 0.05, M_REDG)
GHOST.location = (-15.0, 0, WZ1); 
bake_fn(GHOST, "rotation_euler", 1, PW([(0, 0.0), (C["bad"], 0.0), (C["bad"] + 0.6, math.radians(-1.6)), (DUR, math.radians(-1.6))]))
windows(GHOST, [(C["bad"] - 0.05, C["this"])])
# flow speed: stops on "stop", restarts with the next shot
FLOW = PW([(0, 1.0), (C["bad"] + 0.3, 1.0), (C["stop"] + 0.2, 0.0), (C["this"] - 0.05, 0.0), (C["this"], 1.0), (DUR, 1.0)])
FLOW_INT = [0.0]
for fr in range(1, len(TS)): FLOW_INT.append(FLOW_INT[-1] + FLOW(TS[fr]) / FPS)
def fint(t): return FLOW_INT[max(0, min(len(TS) - 1, int(round(t * FPS))))]
BEADME = sphere_mesh("ChanBead", 0.11, 1); BEADME.materials.append(M_CYANG)
CHAN_BEADS = []
for i in range(90):
    o = obj_from(f"ChanBead{i}", BEADME); par(o, TOP)
    x0_, y_, z_ = random.uniform(-160, 160), random.uniform(-0.42, 0.42), random.uniform(WZ0 + 0.25, WZ1 - 0.08)
    bake_loc(o, lambda t, x0_=x0_, y_=y_, z_=z_: ((x0_ + 160 + 5.0 * fint(t)) % 320 - 160, y_, z_))
    windows(o, [(0, C["springs"]), (C["lift"], C["some"]), (C["still"], C["deeper"]), (C["would"], DUR)])
    CHAN_BEADS.append(o)
# B8: the valley is empty first, then the three tiers rise on "three" / "tiers" / "lift"
def rise(t_up):
    return PW([(0, 0.0), (C["arches"] - 0.04, 0.0), (C["arches"] - 0.01, -75.0), (t_up - 0.05, -75.0), (t_up + 0.65, 0.0), (DUR, 0.0)])
for ob, t_up in ((TIER1, C["three"]), (TIER2, C["tiers"]), (TIER3, C["lift"]), (TOP, C["lift"])):
    f_ = rise(t_up); bake_loc(ob, lambda t, f_=f_: (0.0, 0.0, f_(t)))
# buried route glowing on both hillsides (arches only where a valley gets in the way)
def route_hill(sign):
    pts = []
    for k in range(60):
        ax = 137.5 + (900 - 137.5) * k / 59
        pts.append(Vector((sign * ax, 0.0, terrain_h(sign * ax, 0.0) + 1.2)))
    return pts
ROUTES = [poly_obj(f"HillRoute{s}", route_hill(s), 1.6, M_ROUTE, seg=10) for s in (-1, 1)]
for o in ROUTES: windows(o, [(C["arches"], C["some"])])
# 160 ft height arrow (river -> channel)
bm = bmesh.new(); add_box(bm, -0.6, 0.6, -0.6, 0.6, 0, 1.0)
HARROW = mesh_obj("HeightBar", bm, M_GOLDG); HARROW.location = (19.0, -5.5, -0.5)
bake_scale(HARROW, lambda t: (1.0, 1.0, max(0.001, (CH + 0.5) * ease((t - C["one"]) / 1.0))))
windows(HARROW, [(C["one"] - 0.05, C["some"])])
HCAP = box("HeightCap", 15.5, 22.5, -6.3, -4.7, CH, CH + 0.8, M_GOLDG); windows(HCAP, [(C["one"] + 1.0, C["some"])])
# trees on the hills (GN scatter), kept off the bridge line and the river
def tree_inst():
    bm = bmesh.new(); add_cyl(bm, 0.35, 3.0, "Z", (0, 0, 1.5), seg=6, mi=1)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=2.6, radius2=0.2, depth=7.0)
    bmesh.ops.translate(bm, verts=res["verts"], vec=(0, 0, 5.8))
    return mesh_obj("TreeInst", bm, [M_TREE, M_TRUNK])
TREE = tree_inst()
for nm, (xa, xb, ya, yb, dens, sd) in {"TreesBack": (-1100, 1100, 30, 900, 0.0016, 2), "TreesFrontL": (-1100, -40, -900, -60, 0.0011, 5),
                                      "TreesFrontR": (40, 1100, -900, -60, 0.0011, 7)}.items():
    hf = lambda x, y: terrain_h(x, y) + 0.05
    pt = grid(nm, xa, xb, ya, yb, 60, 40, hf, M_GRASS)
    fx.scatter(pt, TREE, density=dens, scale_min=0.6, scale_max=1.5, seed=sd)
TREE.location = (0, 0, -900)

# ================= map set: spring -> city, the channel winds (MX) =================
def map_h(x, y):
    return 30.0 + 26.0 * math.sin(x / 170.0 + 0.6) * math.cos(y / 150.0) + 14.0 * math.sin(x / 75.0 + y / 110.0) + 0.012 * (-x) * 0.6
box("MapUnder", MX - 4000, MX + 4000, -4000, 4000, -40, -15, M_GRASS)
MAPT = grid("MapTerrain", -900, 900, -700, 700, 120, 90, map_h, M_GRASS, off=(MX, 0, 0))
SPR = Vector((-640.0, 330.0)); CITY = Vector((600.0, -300.0))
RAW = [SPR, (-520, 120), (-600, -60), (-380, -180), (-260, 40), (-120, 220), (20, 120), (-40, -120), (120, -260), (260, -140),
       (330, 80), (470, 40), (430, -180), CITY]
RAW = [Vector((p[0], p[1])) for p in RAW]
RP = chaikin([Vector((p.x, p.y, 0)) for p in RAW], 4)
RPTS = [Vector((MX + p.x, p.y, map_h(p.x, p.y) + 5.0)) for p in RP]
NSEG = 48
ROUTE_SEGS = []
per = max(1, len(RPTS) // NSEG)
for k in range(NSEG):
    seg_pts = RPTS[k * per: min(len(RPTS), (k + 1) * per + 1)]
    if len(seg_pts) < 2: continue
    o = poly_obj(f"MapRoute{k}", seg_pts, 5.5, M_ROUTE, seg=10)
    t_on = C["winds"] + (C["falling"] + 0.8 - C["winds"]) * k / NSEG
    windows(o, [(t_on, C["most"])]); ROUTE_SEGS.append(o)
sz = map_h(SPR.x, SPR.y); cz = map_h(CITY.x, CITY.y)
SPRING = obj_from("Spring", sphere_mesh("SpringBall", 16.0, 2), M_CYANG, loc=(MX + SPR.x, SPR.y, sz + 10))
LVL = max(sz, cz) + 40.0
SPR_PIL = box("SpringPillar", MX + SPR.x - 3, MX + SPR.x + 3, SPR.y - 3, SPR.y + 3, sz, LVL, M_GOLDG)
CITY_PIL = box("CityPillar", MX + CITY.x - 3, MX + CITY.x + 3, CITY.y - 3, CITY.y + 3, cz, LVL - 14.0, M_WHITEG)
LVL_LINE = poly_obj("LevelRef", [Vector((MX + SPR.x, SPR.y, LVL)), Vector((MX + CITY.x, CITY.y, LVL))], 1.6, M_GOLDG, seg=8)
for o in (SPR_PIL, CITY_PIL, LVL_LINE): windows(o, [(C["barely"] - 0.1, C["channel"] + 0.6)])
def house_inst():
    bm = bmesh.new(); add_box(bm, -4, 4, -3, 3, 0, 5, mi=0); add_box(bm, -4.4, 4.4, -3.4, 3.4, 5, 6.2, mi=1)
    return mesh_obj("HouseInst", bm, [M_HOUSE, M_ROOF])
HOUSE = house_inst()
CPATCH = grid("CityPatch", CITY.x - 70, CITY.x + 70, CITY.y - 60, CITY.y + 60, 10, 10, lambda x, y: map_h(x, y) + 0.3, M_DIRT, off=(MX, 0, 0))
fx.scatter(CPATCH, HOUSE, density=0.012, scale_min=0.8, scale_max=1.6, seed=21)
MTREE = grid("MapTrees", -900, 900, -700, 700, 40, 30, lambda x, y: map_h(x, y) + 0.2, M_GRASS, off=(MX, 0, 0))
fx.scatter(MTREE, TREE, density=0.0009, scale_min=1.5, scale_max=3.0, seed=23)
MB = []
for i in range(36):
    o = obj_from(f"MapBead{i}", sphere_mesh(f"MapBeadM{i}", 4.0, 1), M_CYANG)
    MPATH = Path(RPTS)
    bake_loc(o, lambda t, i=i, P=MPATH: tuple(P.at((i / 36 * P.L + 60.0 * max(0.0, t - C["falling"])) % P.L) + Vector((0, 0, 2.0))))
    windows(o, [(C["falling"] + 0.6, C["most"])]); MB.append(o)
HOUSE.location = (0, 0, -900)

# ================= underground set: buried channel section (cut at y = 0) + sinter (UX) =================
UGW, WT, LT = 0.6, 0.62, 0.08          # inner half width, wall, lining
FL0, FL1 = -5.0, -4.4                   # floor slab
WTOP, COV = -2.6, -2.2
UL = 40.0
box("UGSoilL", UX - 18, UX - (UGW + LT + WT), 0, UL, -12, 0, M_SOIL); box("UGSoilR", UX + (UGW + LT + WT), UX + 18, 0, UL, -12, 0, M_SOIL)
box("UGSoilBelow", UX - (UGW + LT + WT), UX + (UGW + LT + WT), 0, UL, -12, FL0, M_SOIL)
box("UGBackfill", UX - (UGW + LT + WT), UX + (UGW + LT + WT), 0, UL, COV, 0, M_SOIL)
box("UGGrass", UX - 18, UX + 18, 0, UL, 0, 0.35, M_GRASS)
box("UGGroundL", UX - 300, UX - 18, 0, 400, -12, 0.3, M_GRASS); box("UGGroundR", UX + 18, UX + 300, 0, 400, -12, 0.3, M_GRASS)
box("UGGroundBack", UX - 18, UX + 18, UL, 400, -12, 0.3, M_GRASS)
STONE_UG = []
STONE_UG.append(box("UGFloor", UX - (UGW + LT + WT), UX + (UGW + LT + WT), 0, UL, FL0, FL1, M_CHAN))
STONE_UG.append(box("UGWallL", UX - (UGW + LT + WT), UX - (UGW + LT), 0, UL, FL1, WTOP, M_CHAN))
STONE_UG.append(box("UGWallR", UX + (UGW + LT), UX + (UGW + LT + WT), 0, UL, FL1, WTOP, M_CHAN))
STONE_UG.append(box("UGCover", UX - (UGW + LT + WT), UX + (UGW + LT + WT), 0, UL, WTOP, COV, M_CHAN))
glow(B_CHAN, [(0, 0.0), (C["stone"] - 0.01, 0.0), (C["stone"] + 0.2, 0.6), (C["lined"], 0.0), (DUR, 0.0)])
bm = bmesh.new()
add_box(bm, UX - (UGW + LT), UX - UGW, 0, UL, FL1, WTOP); add_box(bm, UX + UGW, UX + UGW + LT, 0, UL, FL1, WTOP)
add_box(bm, UX - UGW, UX + UGW, 0, UL, FL1, FL1 + LT)
LINING = mesh_obj("Lining", bm, M_LINING)
glow(B_LINING, [(0, 0.0), (C["lined"] - 0.01, 0.0), (C["lined"] + 0.25, 2.5), (C["tile"] + 0.4, 2.5), (C["arches"], 0.0), (DUR, 0.0)])
UWZ0, UWZ1 = FL1 + LT, FL1 + LT + 0.95
SINT_T = PW([(0, 0.0), (C["coated"], 0.0), (C["coated"] + 0.4, 0.06), (C["layer"], 0.06), (C["layer"] + 0.4, 0.12), (C["layer2"], 0.12),
             (C["layer2"] + 0.4, 0.18), (DUR, 0.18)])
UWATER = box("UGWater", -UGW + 0.01, UGW - 0.01, 0.01, UL, UWZ0, UWZ1, M_WATER); UWATER.location = (UX, 0, 0)
bake_scale(UWATER, lambda t: (max(0.3, 1.0 - SINT_T(t) / UGW * (1.0 if t < C["chipped"] + 0.4 else max(0.0, 1 - (t - C["chipped"] - 0.4) / 0.6))), 1.0, 1.0))
# sinter chunks: 2 walls x 6 along y x 3 rows, each grows inward with the layers, then is chipped out (kinematic -> dynamic)
CHUNKS = []
NY, NZ, CY = 6, 3, 1.25
for side in (-1, 1):
    for j in range(NY):
        for kz in range(NZ):
            z0_ = UWZ0 + (UWZ1 + 0.35 - UWZ0) * kz / NZ; z1_ = UWZ0 + (UWZ1 + 0.35 - UWZ0) * (kz + 1) / NZ
            bm = bmesh.new(); add_box(bm, 0.0, 1.0, 0.03, CY - 0.03, z0_ - (z0_ + z1_) / 2 + 0.01, z1_ - (z0_ + z1_) / 2 - 0.01)
            ch = mesh_obj(f"Sinter{side}_{j}_{kz}", bm, M_SINTER)
            base = Vector((UX + side * UGW, (j + (1 if side > 0 else 0)) * CY, (z0_ + z1_) / 2))
            ch.location = base; ch.rotation_euler = (0, 0, 0 if side < 0 else math.pi)
            ch.scale = (0.001, 1, 1); CHUNKS.append((ch, base, side, j, kz))
FLOORS = box("SinterFloor", -UGW, UGW, 0.01, UL, 0, 1.0, M_SINTER); FLOORS.location = (UX, 0, UWZ0)
bake_scale(FLOORS, lambda t: (1.0, 1.0, max(0.001, SINT_T(t) * 0.5)))
windows(FLOORS, [(C["coated"], C["chipped"] + 0.6)])
glow(B_SINTER, [(0, 0.0), (C["coated"] - 0.01, 0.0), (C["coated"] + 0.2, 0.5), (C["crews"], 0.0), (DUR, 0.0)])
UFLOOR_PASSIVE = box("UGFloorCollide", UX - UGW, UX + UGW, 0, UL, FL1, UWZ0, M_LINING); UFLOOR_PASSIVE.hide_render = True
# lime + crushed tile heaps on the surface
def heap(name, x, m_, r=1.5, hgt=1.1):
    bm = bmesh.new(); res = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=0.1, depth=hgt)
    bmesh.ops.translate(bm, verts=res["verts"], vec=(0, 0, hgt / 2))
    for v in bm.verts: v.co.x += 0.1 * math.sin(v.co.y * 5); v.co.y += 0.1 * math.cos(v.co.x * 4)
    o = mesh_obj(name, bm, m_); o.location = (x, 1.6, 0.35); return o
LIMEH = heap("LimeHeap", UX - 2.2, M_LIME, r=0.75, hgt=0.7); TILEH = heap("TileHeap", UX + 2.2, M_TILE, r=0.75, hgt=0.7)
bake_scale(LIMEH, lambda t: (pop(t, C["lime"]),) * 3); bake_scale(TILEH, lambda t: (pop(t, C["crushed"]),) * 3)
UB = []
for i in range(30):
    o = obj_from(f"UGBead{i}", BEADME)
    xx, zz, y0_ = UX + random.uniform(-0.35, 0.35), random.uniform(UWZ0 + 0.2, UWZ1 - 0.1), random.uniform(0, UL)
    bake_loc(o, lambda t, xx=xx, zz=zz, y0_=y0_: (xx, (y0_ + 2.5 * t) % UL, zz)); windows(o, [(C["most"], C["arches"]), (C["but"], C["crews"])]); UB.append(o)

# ================= block set: dry-laid courses, 3 six-ton blocks drop in (BX) =================
BW, BD, BH, GAP = 2.0, 1.4, 0.95, 0.03
box("BlockGround", BX - 60, BX + 60, -60, 60, -0.3, 0.0, M_GRASS)
COURSE_PASSIVE = []
for row in range(4):
    off_ = 0.0 if row % 2 == 0 else BW / 2
    for k in range(-3, 4):
        x0_ = BX + k * (BW + GAP) + off_ - BW / 2
        if x0_ < BX - 7.2 or x0_ + BW > BX + 7.6: continue
        b_ = box(f"Course{row}_{k}", x0_, x0_ + BW, -BD / 2, BD / 2, row * (BH + GAP), row * (BH + GAP) + BH, M_STONE)
        pass
# glowing joints on the front face
bm = bmesh.new()
for row in range(4):
    z0_ = row * (BH + GAP); add_box(bm, BX - 7.2, BX + 7.6, -BD / 2 - 0.03, -BD / 2 - 0.01, z0_ + BH, z0_ + BH + GAP)
    off_ = 0.0 if row % 2 == 0 else BW / 2
    for k in range(-3, 4):
        xg = BX + k * (BW + GAP) + off_ + BW / 2
        if BX - 7.2 < xg < BX + 7.6: add_box(bm, xg, xg + GAP, -BD / 2 - 0.03, -BD / 2 - 0.01, z0_, z0_ + BH)
JOINTS = mesh_obj("Joints", bm, M_JOINT)
glow(B_JOINT, [(0, 0.0), (C["nomortar"] - 0.4, 0.0), (C["nomortar"] - 0.1, 8.0), (C["still"] - 0.1, 8.0), (C["still"], 0.0)])
DROPS = []
ZT = 4 * (BH + GAP)

for i, (t_rel, xk) in enumerate(((C["six"], -1), (C["tons"], 0), (C["stacked"], 1))):
    x0_ = BX + xk * (BW + 0.45) - BW / 2
    b_ = box(f"BigBlock{i}", 0, BW, -BD / 2, BD / 2, 0, BH, M_STONE); base = Vector((x0_, 0.0, ZT + 0.002))
    b_.location = base + Vector((0, 0, 7.0)); DROPS.append((b_, base, t_rel))
# ================= siphon set: header tank, lead pipes down one side and up the other (SX) =================
SP = [(-400, 62), (-50, 60), (-16, 2), (16, 2), (50, 56), (400, 58)]
def sprof(x):
    for (x0, z0), (x1, z1) in zip(SP, SP[1:]):
        if x <= x1: return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
    return SP[-1][1]
bm = bmesh.new(); xs = [SX - 400 + 4 * i for i in range(201)]
fr = [bm.verts.new((x, 0, sprof(x - SX))) for x in xs] + [bm.verts.new((SX + 400, 0, -90)), bm.verts.new((SX - 400, 0, -90))]
bk = [bm.verts.new((v.co.x, 80, v.co.z)) for v in fr]
bm.faces.new(fr); bm.faces.new(list(reversed(bk)))
for i in range(len(fr)):
    j = (i + 1) % len(fr); bm.faces.new([fr[i], fr[j], bk[j], bk[i]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
SVALLEY = mesh_obj("SiphonValley", bm, M_ROCKS)
box("SiphonFar", SX - 900, SX + 900, 80, 900, -30, 58, M_GRASS)
SRIVER = box("SiphonRiver", SX - 13, SX + 13, 0.5, 79, 0, 2.6, M_RIVER)
HT = box("HeaderTank", SX - 62, SX - 50, 0.6, 9, 60, 67, M_CHAN); RT = box("ReceiverTank", SX + 50, SX + 62, 0.6, 9, 56, 63, M_CHAN)
HTW = box("HeaderWater", SX - 61, SX - 51, 1.4, 8.2, 61, 65.6, M_WATER); RTW = box("ReceiverWater", SX + 51, SX + 61, 1.4, 8.2, 57, 62.4, M_WATER)
for o in (HT, RT):
    cut = box(o.name + "Hollow", o.bound_box[0][0] + 1.0, o.bound_box[6][0] - 1.0, 1.4, 8.2, 61, 68, None); cut.hide_render = True; cut.display_type = "WIRE"
    boolean(o, cut, "Hollow")
for k in range(4):
    box(f"Venter{k}", SX - 14.5 + 9.5 * k, SX - 14.5 + 9.5 * k + 2.2, 0.8, 9, 0, 7.0, M_CHAN)
box("VenterDeck", SX - 16, SX + 16, 0.8, 9, 7.0, 7.8, M_CHAN)
PRAW = [(-51, 62.2), (-48, 60.5), (-17, 3.8), (-15, 8.6), (15, 8.6), (17, 3.8), (48, 56.5), (51, 58.2)]
PIPES = []
for j, yc in enumerate((2.4, 4.6, 6.8)):
    pts = chaikin([Vector((SX + x, yc, z)) for x, z in PRAW], 3)
    bm = sweep_bm(pts, [0.75] * len(pts), 24, cap=False)
    if j == 0: cut_front(bm, yc, fill=False)
    p_ = mesh_obj(f"LeadPipe{j}", bm, M_LEAD)
    try: p_.data.shade_smooth()
    except Exception: pass
    PIPES.append((p_, pts))
bm = bmesh.new()
for yc in (2.4, 4.6, 6.8): add_seg(bm, (SX - 15, yc, 8.6), (SX + 15, yc, 8.6), 0.8, 20)
BOTTOM = mesh_obj("PipeBottomGlow", bm, M_LEADB)
glow(B_LEADB, [(0, 0.0), (C["pressure"] - 0.01, 0.0), (C["pressure"] + 0.25, 3.0), (C["other"] + 0.3, 3.0), (C["at"], 0.0)])
SPATH = Path(PIPES[0][1])
SB = []
for i in range(34):
    o = obj_from(f"SiphonBead{i}", sphere_mesh(f"SiphonBeadM{i}", 0.42, 1), M_CYANG)
    bake_loc(o, lambda t, i=i: tuple(SPATH.at((i / 34 * SPATH.L + 16.0 * max(0.0, t - C["water3"] + 0.6)) % SPATH.L)))
    windows(o, [(C["water3"] - 0.6, C["at"])]); SB.append(o)
SLEVEL = poly_obj("SiphonLevel", [Vector((SX - 51, 0.3, 65.6)), Vector((SX + 61, 0.3, 65.6))], 0.35, M_GOLDG, seg=6)
windows(SLEVEL, [(C["up"], C["at"])])
# Mantaflow: header tank filling from its inlet (short shot, laptop --bake-fluid)
FL_DOM = box("TankFluidDomain", SX - 61, SX - 51, 1.4, 8.2, 61, 67, M_WATER)
FL_IN = cyl("TankInflow", 1.2, 2.0, "X", (SX - 59.0, 4.8, 65.0), M_WATER, seg=16)
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=64, start=F(C["deeper"]), end=F(C["deeper"] + 3.6), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_IN.hide_render = True
if FLUID_BAKE: windows(FL_DOM, [(C["deeper"], C["water3"])]); windows(HTW, [(0, C["deeper"]), (C["water3"], DUR)])
else: windows(FL_DOM, [])

# ================= castellum set: round tank splits the flow into ten pipes (CX) =================
box("CastGround", CX - 120, CX + 120, -120, 120, -1.0, 0.0, M_PAVE)
CR0, CR1, CHW = 2.8, 3.5, 1.9
BASIN = lathe("Basin", [(CR0, 0.0), (CR1, 0.0), (CR1, CHW), (CR0, CHW)], M_CHAN, a0=0.0, ang=2 * math.pi, seg=64, loc=(CX, 0, 0))
BFLOOR = cyl("BasinFloor", CR0 + 0.05, 0.25, "Z", (CX, 0, 0.125), M_CHAN, seg=48)
CWAT = cyl("BasinWater", CR0 - 0.02, 1.1, "Z", (CX, 0, 0.25 + 0.55), M_WATER, seg=48)
INFL = box("InflowChannel", CX - 0.9, CX + 0.9, CR0 - 0.2, 30, 0.0, 1.7, M_CHAN)
INFC = box("InflowCut", CX - 0.55, CX + 0.55, CR0 - 0.5, 31, 0.6, 1.9, None); INFC.hide_render = True; INFC.display_type = "WIRE"; boolean(INFL, INFC, "Groove")
INW = box("InflowWater", CX - 0.54, CX + 0.54, CR0 - 0.3, 30, 0.6, 1.25, M_WATER)
CPIPES = []
for k in range(10):
    a = math.radians(200 + 140 * k / 9)
    p0 = Vector((CX + (CR1 - 0.1) * math.cos(a), (CR1 - 0.1) * math.sin(a), 0.45)); p1 = Vector((CX + 16 * math.cos(a), 16 * math.sin(a), 0.25))
    bm = bmesh.new(); add_seg(bm, p0, p1, 0.24, 14)
    m_k, b_k = mat(f"CastPipe{k}", (0.36, 0.37, 0.40), rough=0.45, metallic=0.7, emit_rgb=(0.30, 0.92, 1.0))
    o = mesh_obj(f"CastPipe{k}", bm, m_k); CPIPES.append((o, p0, p1))
    glow(b_k, [(0, 0.0), (C["ten"] - 0.3 + 0.06 * k, 0.0), (C["ten"] - 0.1 + 0.06 * k, 1.6), (DUR, 1.6)])
CB = []
for k, (o, p0, p1) in enumerate(CPIPES):
    for i in range(5):
        b_ = obj_from(f"CastBead{k}_{i}", sphere_mesh(f"CastBeadM{k}_{i}", 0.17, 1), M_CYANG)
        bake_loc(b_, lambda t, i=i, p0=p0, p1=p1: tuple(p0.lerp(p1, ((i / 5) + 0.5 * max(0.0, t - C["split"])) % 1.0) + Vector((0, 0, 0.32))))
        windows(b_, [(C["split"], C["but"])]); CB.append(b_)
for i in range(14):
    b_ = obj_from(f"InBead{i}", sphere_mesh(f"InBeadM{i}", 0.16, 1), M_CYANG)
    bake_loc(b_, lambda t, i=i: (CX + 0.25 * math.sin(i * 2.1), 30 - ((i / 14 * 27.5) + 9.0 * max(0.0, t - C["at"])) % 27.5, 1.3))
    windows(b_, [(C["at"], C["but"])]); CB.append(b_)
CHP = grid("CastHouses", -110, 110, -110, 110, 10, 10, lambda x, y: 0.02 if math.hypot(x, y) > 24 else -50.0, M_PAVE, off=(CX, 0, 0))
fx.scatter(CHP, HOUSE, density=0.006, scale_min=0.7, scale_max=1.3, seed=31)

# ================= rigid bodies: six-ton blocks + sinter chunks (one world) =================
fx.rigid([c[0] for c in CHUNKS], passive=[UFLOOR_PASSIVE] + STONE_UG[:3], mass=3.0, friction=0.7, bounce=0.15)
for b_, base, t_rel in DROPS:      # keyed drop with a small settle (the rigid-body sim is used for the sinter chip-out)
    bake_loc(b_, lambda t, base=base, t_rel=t_rel: tuple(base + Vector((0, 0, drop(t, t_rel + 0.3, h=6.0, d=0.6) if t > t_rel - 0.3 else 6.0))))
    windows(b_, [(t_rel - 0.25, C["still"])])
for ch, base, side, j, kz in CHUNKS:
    try:
        fr_ = F(C["chipped"] + 0.05 * (j + 2 * kz) + (0.12 if side > 0 else 0.0))
        thick = lambda t: max(0.001, SINT_T(t))
        for fr2 in range(1, fr_ + 1, 3):
            ch.scale = (thick(TS[fr2 - 1]), 1, 1); ch.keyframe_insert("scale", frame=fr2)
        ch.scale = (0.18, 1, 1); ch.keyframe_insert("scale", frame=fr_)
        rb = ch.rigid_body; rb.collision_shape = "CONVEX_HULL"; rb.kinematic = True
        ch.keyframe_insert("rigid_body.kinematic", frame=1); ch.keyframe_insert("rigid_body.kinematic", frame=fr_)
        ch.location = base; ch.keyframe_insert("location", frame=1); ch.keyframe_insert("location", frame=fr_ - 1)
        ch.location = base + Vector((-side * 0.12, 0, 0.05)); ch.keyframe_insert("location", frame=fr_ + 1)
        rb.kinematic = True; ch.keyframe_insert("rigid_body.kinematic", frame=fr_ + 1)
        rb.kinematic = False; ch.keyframe_insert("rigid_body.kinematic", frame=fr_ + 2)
    except Exception as e: print("[build] chunk kinematic skipped", e)
    windows_r(ch, [(C["coated"], DUR)])
# dust: block landing + chip-out
INV_FAC.default_value = 0.0
DUST1 = box("BlockDustEmitter", BX - 5, BX + 5, -0.9, 0.9, ZT, ZT + 0.05, M_INV)
fx.particles(DUST1, "dust", F(C["six"] + 0.85), F(C["stacked"] + 1.2), count=600)
DUST2 = box("SinterDustEmitter", UX - UGW, UX + UGW, 0.2, 6.5, UWZ0 + 0.3, UWZ0 + 0.35, M_INV)
fx.particles(DUST2, "dust", F(C["chipped"]), F(C["would"]), count=500)
for d_ in (DUST1, DUST2):
    try: ps = d_.particle_systems[0].settings; ps.particle_size = 0.035; ps.normal_factor = 1.2
    except Exception as e: print("[build] dust tune skipped", e)

# ================= world: HDRI light + own sky gradient, warm sun =================
fx.hdri("forest", strength=0.55, rotation_deg=120.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.10, 0.09, 0.07, 1); e[1].position = 0.45; e[1].color = (0.16, 0.34, 0.68, 1)
    eh = e.new(0.02); eh.color = (0.98, 0.72, 0.46, 1)
    wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.6; sun_d.angle = math.radians(1.5)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(62), 0, math.radians(-38))
for t_, col, en in [(0, (1.0, 0.86, 0.68), 3.6), (C["still"] - 0.02, (1.0, 0.86, 0.68), 3.6), (C["still"], (1.0, 0.58, 0.32), 3.2),
                    (C["deeper"] - 0.02, (1.0, 0.58, 0.32), 3.2), (C["deeper"], (1.0, 0.86, 0.68), 3.6), (C["would"] - 0.02, (1.0, 0.86, 0.68), 3.6),
                    (C["would"], (1.0, 0.66, 0.40), 3.4)]:
    sun_d.color = col; sun_d.keyframe_insert("color", frame=F(t_)); sun_d.energy = en; sun_d.keyframe_insert("energy", frame=F(t_))
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.95, 0.88)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("UGFill", (UX, -8.0, -2.0), 8.0, 900.0, rot=(math.radians(80), 0, 0))
area("BlockFill", (BX, -12.0, 6.0), 10.0, 1500.0, rot=(math.radians(70), 0, 0))
RED_D = bpy.data.lights.new("StakeRed", "POINT"); RED_D.color = (1.0, 0.25, 0.15); RED_D.shadow_soft_size = 2.0
RED_O = bpy.data.objects.new("StakeRed", RED_D); scene.collection.objects.link(RED_O); RED_O.location = (-15.0, -6.0, 50.5)
for t_, v_ in [(0, 0.0), (C["bad"] - 0.02, 0.0), (C["bad"] + 0.3, 2500.0), (C["this"] - 0.02, 2500.0), (C["this"], 0.0)]:
    RED_D.energy = v_; RED_D.keyframe_insert("energy", frame=F(t_))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-66.0, -3.0, 50.4), (-12.0, 0.25, 48.0), 22),
    (C["romans"] - 0.05, (-56.0, -3.4, 51.2), (-6.0, 0.25, 47.8), 22),
    (C["romans"], (-44.0, -34.0, 58.0), (0.0, 0.0, 44.0), 24, "cut"),
    (C["slope"] - 0.05, (-170.0, -270.0, 98.0), (0.0, 0.0, 30.0), 24),
    (C["slope"], (-15.0, -16.0, 51.6), (-15.0, 0.0, 48.6), 26, "cut"),
    (C["this"] - 0.05, (-11.0, -14.0, 51.8), (-13.0, 0.0, 48.6), 26),
    (C["this"], (40.0, -175.0, 8.0), (0.0, 0.0, 28.0), 22, "cut"),
    (C["springs"] - 0.05, (12.0, -150.0, 14.0), (0.0, 0.0, 30.0), 22),
    (C["springs"], (MX - 560.0, -40.0, 1250.0), (MX - 130.0, 0.0, 0.0), 20, "cut"),
    (C["most"] - 0.05, (MX - 500.0, -90.0, 1170.0), (MX - 130.0, 0.0, 0.0), 20),
    (C["most"], (UX + 3.6, -6.8, -0.6), (UX, 3.0, -3.5), 26, "cut"),
    (C["lime"] - 0.3, (UX + 2.8, -6.2, -0.9), (UX, 3.0, -3.4), 26),
    (C["arches"] - 0.05, (UX + 2.2, -7.4, 1.4), (UX, 3.0, -2.2), 26),
    (C["arches"], (-40.0, -470.0, 150.0), (0.0, 0.0, 22.0), 22, "cut"),
    (C["some"] - 0.05, (60.0, -380.0, 95.0), (0.0, 0.0, 26.0), 22),
    (C["some"], (BX + 7.0, -10.5, 7.5), (BX, 0.0, 3.4), 26, "cut"),
    (C["still"] - 0.05, (BX + 5.0, -9.0, 6.4), (BX, 0.0, 3.6), 26),
    (C["still"], (-230.0, -320.0, 98.0), (0.0, 0.0, 26.0), 24, "cut"),
    (C["deeper"] - 0.05, (-200.0, -300.0, 90.0), (0.0, 0.0, 26.0), 24),
    (C["deeper"], (SX - 4.0, -150.0, 74.0), (SX, 0.0, 40.0), 20, "cut"),
    (C["at"] - 0.05, (SX + 6.0, -140.0, 70.0), (SX, 0.0, 40.0), 20),
    (C["at"], (CX - 3.0, -17.0, 12.0), (CX, -3.0, 0.5), 24, "cut"),
    (C["but"] - 0.05, (CX + 2.0, -14.0, 10.0), (CX, -3.0, 0.5), 24),
    (C["but"], (UX + 1.4, -5.6, -3.0), (UX, 2.0, -3.7), 26, "cut"),
    (C["would"] - 0.05, (UX + 0.9, -4.6, -3.2), (UX, 2.0, -3.7), 26),
    (C["would"], (190.0, -150.0, 72.0), (0.0, 0.0, 38.0), 24, "cut"),
    (DUR, (70.0, -48.0, 54.0), (-25.0, 0.0, 46.0), 24),
]
def ev(p, t): return Vector(p(t)) if callable(p) else Vector(p)
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(60.0, min(1.5e6, 120.0 * ((cl - ct).length / 30.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)
# ================= render settings =================
fx.engine("cycles")
r = scene.render
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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4; scene.cycles.transparent_max_bounces = 12; scene.cycles.volume_bounces = 0
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = False
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
scene.view_settings.exposure = float(arg("--exposure", "-0.4"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["some"]) - 5, F(C["would"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "channel": (-22.0, -CW, WZ1), "level": (CUT1, -CW, WZ1 + 0.4), "stake": (-40.0, -CW, WZ1 + 0.3), "bridge": (-30.0, -3.0, 30.0),
    "spring": (MX + SPR.x, SPR.y, sz + 34.0), "city": (MX + CITY.x, CITY.y, cz + 16.0),
    "stonech": (UX - 1.0, 0.0, -3.4), "lining": (UX + UGW + 0.04, 0.0, -3.0), "lime": (UX - 2.2, 1.6, 0.9), "tile": (UX + 2.2, 1.6, 0.9),
    "tier1": (-46.0, -3.0, 13.0), "tier2": (-88.0, -2.25, 33.0), "tier3": (-112.0, -1.5, 44.5), "hillroute": (420.0, 0.0, terrain_h(420.0, 0.0) + 2.0),
    "block": (BX, 0.0, ZT + 1.6), "joint": (BX - 2.05, -0.7, 1.4),
    "header": (SX - 56.0, 0.0, 68.0), "receiver": (SX + 56.0, 0.0, 64.0), "pipes": (SX - 33.0, 2.4, 33.9), "bottom": (SX + 6.0, 2.4, 9.6),
    "tank": (CX - 1.5, -CR1, CHW), "pipes10": (CX + 2.0, -10.0, 0.5), "sinter": (UX - UGW + 0.1, 0.0, -3.4), "chan_cta": (0.0, -CW - CWT, CH),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "pull": RR(*T_PULL), "stake": RR(*T_STAKE), "flow_stop": round(C["stop"] + 0.2, 3), "est": RR(*T_EST),
          "map": RR(*T_MAP), "route_grow": RR(C["winds"], C["falling"] + 0.8), "ug": RR(*T_UG), "valley": RR(*T_VALLEY),
          "tier_up": [round(C["three"], 3), round(C["tiers"], 3), round(C["lift"], 3)], "height_bar": RR(C["one"], C["one"] + 1.0),
          "block": RR(*T_BLOCK), "block_drops": [round(t_ + 0.9, 3) for t_ in (C["six"], C["tons"], C["stacked"])],
          "sunset": RR(*T_SUNSET), "siphon": RR(*T_SIPH), "castellum": RR(*T_CAST), "sinter": RR(*T_SINTER),
          "layers": [round(C["coated"], 3), round(C["layer"], 3), round(C["layer2"], 3)], "chip": RR(C["chipped"], C["chipped"] + 1.0),
          "cta": RR(*T_CTA)}
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
    if "--range" in ARGS: scene.frame_start, scene.frame_end = [int(x) for x in arg("--range").split(",")]
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
