# Airport-Runway-3D: why runways are so thick. Claim-first hook ("This runway has nineteen inches of solid concrete"):
# a generic airliner lands toward the camera above the runway cut open at y = 0 (layers in the foreground) -> push in on the 19 in slab ->
# compare set (x = -300): runway slab vs a ~10 in highway slab -> back: the layers below glow -> demo set (x = -200): wheels slam a slab,
# soft ground gives, the slab cracks and falls in (rigid body) -> one main gear (6 wheels) at the cut, load arrow, a car tire for scale ->
# cyan load spread down through the layers -> layer cake: explode, fly away, rebuild: subgrade loosened + rolled, subbase of crushed stone
# (GN scatter), cement-treated base, concrete slabs -> joint at x = 0: slabs expand/shrink, concrete turns see-through, steel dowels glow,
# load arrow across -> weaker soil (wet clay) -> every layer grows -> surface: crown arrows + rain -> grooving machine (slurry) -> macro
# groove profile (x = -320, 1/4 in x 1/4 in, 1.5 in apart) -> hydroplane set (x = -340): water wedge lifts the tire, grooved surface lets
# it out (spray particles + optional Mantaflow) -> rubber streaks in the touchdown zone, a water-blast truck cleans one track -> CTA wide
# with the plane taking off.
# Illustrative (1 unit = 1 m): layer thicknesses real (19 in concrete, 12 in base, 12 in subbase per a LAWA standard section), grooves on the
# full runway drawn ~2.5x wider apart so a phone can see them (exact on the macro specimen), generic plane, gear and machines, no real place or brand.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu] [--bake-fluid]
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

CUES = [("this", "This"), ("runway", "runway"), ("has", "has"), ("nineteen", "nineteen"), ("inches", "inches"), ("concrete", "concrete,"),
        ("nearly", "nearly"), ("double", "double"), ("highway", "highway,"), ("only", "only"), ("top", "top"), ("layer", "layer."),
        ("jets", "Jets"), ("slam", "slam"), ("down", "down"), ("gives", "gives,"), ("slabs", "slabs"), ("crack", "crack."),
        ("heres", "Here's"), ("gear", "gear."), ("boeing", "Boeing"), ("each", "each"), ("carry", "carry"), ("three", "three"),
        ("pounds", "pounds."), ("tires", "tires"), ("pumped", "pumped"), ("two", "two"), ("psi", "PSI,"), ("six", "six"), ("car", "car's."),
        ("all", "All"), ("weight", "weight"), ("spread", "spread"), ("dirt", "dirt."), ("so", "So"), ("cake", "cake."),
        ("first", "First,"), ("soil", "soil"), ("packed", "packed"), ("subgrade", "subgrade."), ("next", "Next,"), ("subbase", "subbase"),
        ("crushed", "crushed"), ("then", "Then"), ("base", "base"), ("cement", "cement."), ("then2", "Then"), ("concrete2", "concrete,"),
        ("poured", "poured"), ("giant", "giant"), ("slabs2", "slabs."), ("joints", "Joints"), ("expand", "expand"), ("shrink", "shrink,"),
        ("steel", "steel"), ("dowels", "dowels"), ("load", "load"), ("across", "across."), ("how", "How"), ("thick", "thick?"),
        ("depends", "depends"), ("soil2", "soil"), ("planes", "planes"), ("weaker", "Weaker"), ("thicker", "thicker"), ("layers", "layers."),
        ("now", "Now"), ("surface", "surface."), ("crown", "crown,"), ("rain", "rain"), ("sides", "sides."), ("then3", "Then"),
        ("saws", "saws"), ("grooves", "grooves"), ("quarter", "quarter"), ("deep", "deep,"), ("every", "every"), ("half", "half."),
        ("at", "At"), ("landing", "landing"), ("water", "water"), ("tire", "tire"), ("lift", "lift"), ("ski", "ski."),
        ("grooves2", "grooves"), ("way", "way"), ("out", "out."), ("every2", "Every"), ("touchdown", "touchdown"), ("rubber", "rubber"),
        ("crews", "crews"), ("blast", "blast"), ("off", "off."), ("which", "Which"), ("surprised", "surprised"), ("nextup", "Next"),
        ("wind", "wind"), ("turbines", "turbines.")]
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
CL = coll("Runway")
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

# ================= dimensions (1 unit = 1 m, real thicknesses; crown 1.5 %) =================
HW = 22.5                     # half width of a 150 ft runway
CON, BASE, SUBB, SUBG = 0.48, 0.30, 0.30, 0.60      # 19 in concrete (LAWA standard section), 12 in base, 12 in subbase, compacted subgrade
Z_CON, Z_BASE, Z_SUBB, Z_SUBG = 0.0, -CON, -CON - BASE, -CON - BASE - SUBB
Z_SOIL = Z_SUBG - SUBG        # -1.68
LEN = 600.0
def crown(x): return -0.015 * min(abs(x), HW)
GX = [-HW, -15.0, -7.5, 0.0, 7.5, 15.0, HW]        # longitudinal joints every 7.5 m
YJ = 7.5                                            # transverse joints

def prism(name, x0, x1, top_fn, thick, y0, y1, m_, parent=None, xs_extra=(), bottom_fn=None):
    """Extrude a cross-section (top follows top_fn, bottom = top - thick or bottom_fn) along y."""
    xs = sorted(set([x0, x1] + [x for x in (0.0, -HW, HW) + tuple(xs_extra) if x0 < x < x1]))
    top = [(x, top_fn(x)) for x in xs]
    bot = [(x, (bottom_fn(x) if bottom_fn else top_fn(x) - thick)) for x in reversed(xs)]
    poly = top + bot
    bm = bmesh.new()
    fr = [bm.verts.new((x, y0, z)) for x, z in poly]; bk = [bm.verts.new((x, y1, z)) for x, z in poly]
    bm.faces.new(list(reversed(fr))); bm.faces.new(bk)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new([fr[i], fr[j], bk[j], bk[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_, parent)

# ================= materials =================
def aggregate_mat(name, rgb1, rgb2, scale=9.0, cell=0.12, gap_rgb=None, rough=0.85):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale * 0.3; n.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].color = (*rgb1, 1); e[1].color = (*rgb2, 1)
    L.new(n.outputs["Fac"], cr.inputs[0])
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    try: vo.feature = "DISTANCE_TO_EDGE"
    except Exception: pass
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = cell; L.new(vo.outputs["Distance"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], gap_rgb or tuple(c * 0.45 for c in rgb1), cr.outputs[0])
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(mr.outputs[0], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (0.98, 0.74, 0.27, 1)
    return m, b, nt, col

# concrete: aggregate + transverse joint lines + grooves (keyed front) + rubber (keyed) on the top face only
m_con, b_con, nt, col = aggregate_mat("Concrete", (0.42, 0.42, 0.41), (0.52, 0.52, 0.50), scale=26.0, cell=0.03, gap_rgb=(0.33, 0.33, 0.32), rough=0.7)
N, L = nt.nodes, nt.links
tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
geo = N.new("ShaderNodeNewGeometry"); nsep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Normal"], nsep.inputs[0])
X, Y = sep.outputs["X"], sep.outputs["Y"]
is_top = MATH(nt, "GREATER_THAN", nsep.outputs["Z"], 0.5)
# transverse joints (dark sealant lines every 7.5 m)
jl = MATH(nt, "LESS_THAN", MATH(nt, "PINGPONG", Y, YJ / 2), 0.025)
# grooves: every ~0.1 m drawn (real 1.5 in; shown wider so a phone can see them), y > 3
gstripe = MATH(nt, "LESS_THAN", MATH(nt, "FRACT", MATH(nt, "DIVIDE", Y, 0.10)), 0.3)
G_XALL = VALUE(nt, "GrooveXAll", [(0, 100.0)])     # keyed below once the cues exist
G_FRONT = VALUE(nt, "GrooveFront", [(0, 3.0)])
gA = MATH(nt, "GREATER_THAN", X, G_XALL)
gB = MATH(nt, "MULTIPLY", MATH(nt, "GREATER_THAN", X, -3.2), MATH(nt, "LESS_THAN", Y, G_FRONT))
greg = MATH(nt, "MULTIPLY", MATH(nt, "MAXIMUM", gA, gB), MATH(nt, "GREATER_THAN", Y, 3.0))
gmask = MATH(nt, "MULTIPLY", MATH(nt, "MULTIPLY", greg, gstripe), MATH(nt, "LESS_THAN", MATH(nt, "ABSOLUTE", X), HW - 0.6))
# rubber: streaks along the two wheel tracks in the touchdown zone, keyed amount, left track cleaned behind the truck
rn = N.new("ShaderNodeTexNoise"); rn.inputs["Scale"].default_value = 1.0; rn.inputs["Detail"].default_value = 6
cmb = N.new("ShaderNodeCombineXYZ"); L.new(MATH(nt, "MULTIPLY", X, 4.0), cmb.inputs[0]); L.new(MATH(nt, "MULTIPLY", Y, 0.12), cmb.inputs[1])
L.new(cmb.outputs[0], rn.inputs["Vector"])
streak = MATH(nt, "GREATER_THAN", rn.outputs["Fac"], 0.47)
trackL = MATH(nt, "LESS_THAN", MATH(nt, "ABSOLUTE", MATH(nt, "ADD", X, 5.5)), 1.9)
trackR = MATH(nt, "LESS_THAN", MATH(nt, "ABSOLUTE", MATH(nt, "SUBTRACT", X, 5.5)), 1.9)
zone = MATH(nt, "MULTIPLY", MATH(nt, "GREATER_THAN", Y, 14.0), MATH(nt, "LESS_THAN", Y, 140.0))
R_AMT = VALUE(nt, "RubberAmt", [(0, 0.0)])
C_FRONT = VALUE(nt, "CleanFront", [(0, 0.0)])
cleaned = MATH(nt, "MULTIPLY", MATH(nt, "LESS_THAN", Y, C_FRONT), trackL)
rub = MATH(nt, "MULTIPLY", MATH(nt, "MULTIPLY", MATH(nt, "MAXIMUM", trackL, trackR), zone), streak)
rub = MATH(nt, "MULTIPLY", MATH(nt, "MULTIPLY", rub, R_AMT), MATH(nt, "SUBTRACT", 1.0, cleaned))
c1 = mix_rgb(nt, MATH(nt, "MULTIPLY", jl, is_top), col, (0.08, 0.08, 0.08))
c2 = mix_rgb(nt, MATH(nt, "MULTIPLY", gmask, is_top), c1, (0.22, 0.22, 0.21))
c3 = mix_rgb(nt, MATH(nt, "MULTIPLY", rub, is_top), c2, (0.025, 0.025, 0.025))
L.new(c3, b_con.inputs["Base Color"])
CON_ALPHA = b_con.inputs["Alpha"]
m_base, b_base, *_ = aggregate_mat("CementBase", (0.46, 0.44, 0.40), (0.55, 0.53, 0.49), scale=30.0, cell=0.03)
m_subb, b_subb, *_ = aggregate_mat("CrushedStone", (0.40, 0.38, 0.36), (0.52, 0.50, 0.46), scale=14.0, cell=0.18, gap_rgb=(0.12, 0.11, 0.10))
# subgrade: loose (light) -> compacted (darker), keyed
m_subg, b_subg, nt, colg = aggregate_mat("Subgrade", (0.30, 0.20, 0.12), (0.38, 0.27, 0.17), scale=40.0, cell=0.02, gap_rgb=(0.25, 0.17, 0.10))
SUBG_LOOSE = VALUE(nt, "Loose", [(0, 0.0)])
L2 = nt.links; c = mix_rgb(nt, SUBG_LOOSE, colg, (0.50, 0.38, 0.25)); L2.new(c, b_subg.inputs["Base Color"])
# natural soil: normal -> weak wet clay (keyed for "weaker soil")
m_soil, b_soil, nt, cols = aggregate_mat("Soil", (0.20, 0.14, 0.09), (0.28, 0.20, 0.12), scale=6.0, cell=0.015, gap_rgb=(0.17, 0.12, 0.08))
SOIL_WEAK = VALUE(nt, "Weak", [(0, 0.0)])
c = mix_rgb(nt, SOIL_WEAK, cols, (0.17, 0.18, 0.20)); nt.links.new(c, b_soil.inputs["Base Color"])
m_fill, b_fill, *_ = aggregate_mat("Fill", (0.22, 0.15, 0.10), (0.29, 0.21, 0.13), scale=8.0, cell=0.015, gap_rgb=(0.18, 0.13, 0.08))
m_asph, b_asph = mat("Asphalt", (0.07, 0.07, 0.075), 0.8, noise=40.0)
m_grass, b_grass, nt, colgr = aggregate_mat("Grass", (0.16, 0.24, 0.07), (0.25, 0.34, 0.10), scale=0.6, cell=0.02, gap_rgb=(0.12, 0.17, 0.05), rough=0.95)
m_paint, _ = mat("Paint", (0.78, 0.78, 0.76), 0.5)
m_white, _ = mat("PlaneWhite", (0.72, 0.73, 0.75), 0.3)
m_grey, _ = mat("PlaneGrey", (0.42, 0.44, 0.47), 0.35, metallic=0.6)
m_tire, _ = mat("Tire", (0.07, 0.07, 0.075), 0.55)
m_hub, _ = mat("Hub", (0.62, 0.63, 0.65), 0.25, metallic=0.9)
m_chrome, _ = mat("Chrome", (0.85, 0.86, 0.88), 0.12, metallic=1.0)
m_steel, b_steel = mat("Dowel", (0.55, 0.56, 0.58), 0.3, metallic=0.9, emit_rgb=(0.30, 0.92, 1.0))
m_yel, _ = mat("MachineYellow", (0.95, 0.66, 0.05), 0.4)
m_truck, _ = mat("TruckWhite", (0.75, 0.75, 0.73), 0.35)
m_orng, _ = mat("TruckOrange", (0.95, 0.35, 0.05), 0.4)
m_dark, _ = mat("DarkMetal", (0.06, 0.06, 0.07), 0.5, metallic=0.5)
m_glass, _ = mat("Glass", (0.05, 0.08, 0.10), 0.05)
m_plinth, _ = mat("Plinth", (0.05, 0.05, 0.06), 0.6)
m_light, b_light = mat("EdgeLight", (1.0, 0.9, 0.7), 0.3, emit_rgb=(1.0, 0.86, 0.6)); b_light.inputs["Emission Strength"].default_value = 18.0
m_water, b_water = mat("Water", (0.10, 0.45, 0.75), 0.05, emit_rgb=(0.30, 0.92, 1.0))
b_water.inputs["Transmission Weight"].default_value = 0.5; b_water.inputs["Emission Strength"].default_value = 0.6
m_loadcone, LOADFAC = ghost("LoadSpread", (0.30, 0.92, 1.0))
next(n for n in m_loadcone.node_tree.nodes if n.type == "EMISSION").inputs["Strength"].default_value = 1.6
m_arrowG, b_arrowG = mat("ArrowGold", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27)); b_arrowG.inputs["Emission Strength"].default_value = 3.0
m_arrowC, b_arrowC = mat("ArrowCyan", (0.30, 0.92, 1.0), 0.4, emit_rgb=(0.30, 0.92, 1.0)); b_arrowC.inputs["Emission Strength"].default_value = 3.0
m_red, RED_FAC = ghost("RedGlow", (1.0, 0.30, 0.24))
m_inv, _ = ghost("Invisible", (0, 0, 0))                     # emitters: never visible (fac stays 0)

# ================= the runway section (cut at y = 0, camera on -y) =================
GROUND = empty("Ground")
STRIPS = []
for i in range(6):
    x0, x1 = GX[i] + 0.01, GX[i + 1] - 0.01
    s = prism(f"Slab{i}", x0, x1, crown, CON, 0.0, LEN, m_con, GROUND); STRIPS.append(s)
    # centreline dashes + side stripes ride on their slab
    if i in (2, 3):
        xa, xb = (-0.45, -0.02) if i == 2 else (0.02, 0.45)
        for k in range(10):
            box(f"CL{i}_{k}", xa, xb, 20 + k * 60, 56 + k * 60, crown(0.3) - 0.01, crown(0.3) + 0.006, m_paint, s)
    if i in (0, 5):
        sx = -21.4 if i == 0 else 21.4
        box(f"Side{i}", sx - 0.45, sx + 0.45, 0.5, LEN, crown(sx) - 0.01, crown(sx) + 0.006, m_paint, s)
SLAB_BASE = prism("Base", -HW, HW, lambda x: crown(x) - CON, BASE, 0.0, LEN, m_base, GROUND)
SLAB_SUBB = prism("Subbase", -HW, HW, lambda x: crown(x) - CON - BASE, SUBB, 0.0, LEN, m_subb, GROUND)
SLAB_SUBG = prism("Subgrade", -HW - 3, HW + 3, lambda x: crown(x) - CON - BASE - SUBB, SUBG, 0.0, LEN, m_subg, GROUND,
                  bottom_fn=lambda x: Z_SOIL)
for sgn in (-1, 1):   # shoulders (asphalt) and fill + grass beyond
    xa, xb = (HW, HW + 7.5) if sgn > 0 else (-HW - 7.5, -HW)
    prism(f"Shoulder{sgn}", xa, xb, lambda x: crown(HW) - 0.015 * (abs(x) - HW), 0.15, 0.0, LEN, m_asph, GROUND)
    prism(f"ShoulderFill{sgn}", xa, xb, lambda x: crown(HW) - 0.015 * (abs(x) - HW) - 0.15, 0.0, 0.0, LEN, m_fill, GROUND,
          bottom_fn=lambda x: Z_SUBG if abs(x) < HW + 3 else Z_SOIL)
    xa, xb = (HW + 7.5, 420.0) if sgn > 0 else (-420.0, -HW - 7.5)
    prism(f"Grass{sgn}", xa, xb, lambda x: -0.56, 0.06, 0.0, LEN + 400, m_grass, GROUND)
    prism(f"GrassFill{sgn}", xa, xb, lambda x: -0.62, 0.0, 0.0, LEN + 400, m_fill, GROUND, bottom_fn=lambda x: Z_SOIL)
box("SoilA", -HW - 3, HW + 3, 0.0, LEN, Z_SOIL - 30, Z_SOIL, m_soil, GROUND)
box("SoilB", -420, -HW - 3, 0.0, LEN + 400, Z_SOIL - 30, Z_SOIL, m_fill, GROUND)
box("SoilC", HW + 3, 420, 0.0, LEN + 400, Z_SOIL - 30, Z_SOIL, m_fill, GROUND)
box("FarRunwayCap", -HW, HW, LEN, LEN + 400, -0.60, -0.56, m_grass, GROUND)
bm = bmesh.new()   # far ground: around the runway block, never over the side sets (x <= -580) or the runway section itself
add_box(bm, -560, -420, 0.0, 3000, -0.70, -0.62); add_box(bm, 420, 3000, 0.0, 3000, -0.70, -0.62); add_box(bm, -420, 420, LEN + 400, 3000, -0.70, -0.62)
mesh_obj("Horizon", bm, m_grass)
for sgn in (-1, 1):   # edge lights every 60 m
    for k in range(10):
        cyl(f"EdgeLight{sgn}_{k}", 0.09, 0.35, "Z", (sgn * (HW + 1.0), 6 + k * 60, crown(HW) + 0.1), m_light, GROUND, seg=10)

# dowels across the joint at x = 0 (inside the slabs; seen when the concrete turns see-through)
DOWELS = []
for k in range(16):
    d = cyl(f"Dowel{k}", 0.019, 0.46, "X", (0.0, 0.22 + 0.38 * k, -0.24), m_steel, STRIPS[3], seg=12); DOWELS.append(d)

# subbase stones (Geometry Nodes scatter on a strip of the subbase top near the camera)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.06, location=(0, 0, -50))
STONE = bpy.context.active_object; STONE.name = "Stone"; STONE.data.materials.append(m_subb)
for c_ in list(STONE.users_collection): c_.objects.unlink(STONE)
CL.objects.link(STONE)
bm = bmesh.new()
for x0 in (-9.0,):
    add_box(bm, x0, 6.0, 0.05, 6.0, crown(0) - CON - BASE - 0.002, crown(0) - CON - BASE + 0.0)
STONE_BED = mesh_obj("StoneBed", bm, m_subb, SLAB_SUBB)
fx.scatter(STONE_BED, STONE, density=110.0, scale_min=0.5, scale_max=1.3, seed=3)

# ================= compare set (x = -600): runway concrete vs highway concrete =================
XC = -600.0
box("Plinth", XC - 1.8, XC + 1.8, 0.0, 1.6, -0.62, 0.0, m_plinth)
CMP_R = box("CmpRunway", XC - 1.4, XC - 0.2, 0.0, 1.2, 0.0, 0.48, m_con)
CMP_H = box("CmpHighway", XC + 0.2, XC + 1.4, 0.0, 1.2, 0.0, 0.25, m_con)       # ~10 in (FHWA LTPP 8-11 in)

# ================= demo set (x = -700): soft ground gives, slab cracks (rigid body) =================
XD = -700.0
DEMO = []
box("DemoSoilL", XD - 4.0, XD - 1.8, 0.0, 4.0, -2.4, -0.48, m_soil)
box("DemoSoilR", XD + 1.8, XD + 4.0, 0.0, 4.0, -2.4, -0.48, m_soil)
box("DemoSoilB", XD - 1.8, XD + 1.8, 0.0, 4.0, -2.4, -1.5, m_soil)
box("DemoSoilBack", XD - 1.8, XD + 1.8, 3.8, 4.0, -1.5, -0.48, m_soil)
PIT = box("DemoPit", XD - 1.8, XD + 1.8, 0.0, 3.8, -1.52, -1.5, m_soil)
PLUG = box("DemoPlug", XD - 1.79, XD + 1.79, 0.0, 3.79, -1.5, -0.49, m_soil)
PLUG_RED = box("DemoPlugRed", XD - 1.8, XD + 1.8, -0.01, 3.8, -0.62, -0.48, m_red)
box("DemoSlabL", XD - 4.0, XD - 1.8, 0.0, 4.0, -0.48, 0.0, m_con)
box("DemoSlabR", XD + 1.8, XD + 4.0, 0.0, 4.0, -0.48, 0.0, m_con)
random.seed(5)
PIECES = []
xs = [XD - 1.8, XD - 0.55, XD + 0.6, XD + 1.8]; ys = [0.0, 1.35, 2.5, 4.0]
for i in range(3):
    for j in range(3):
        p = box(f"Piece{i}{j}", xs[i] + 0.006, xs[i + 1] - 0.006, ys[j] + 0.006, ys[j + 1] - 0.006, -0.48, 0.0, m_con)
        PIECES.append(p)
fx.rigid(PIECES, passive=[PIT], mass=50.0, friction=0.7, bounce=0.05)
for p in PIECES:
    try:
        p.rigid_body.kinematic = True; p.rigid_body.keyframe_insert("kinematic", frame=1)
    except Exception as e: print("[fx] kinematic key skipped:", e)
DEMO_WHEELS = empty("DemoWheels")
for dx in (-0.45, 0.45):
    cyl(f"DemoTire{dx}", 0.66, 0.42, "X", (dx, 0, 0), m_tire, DEMO_WHEELS, seg=40)
    cyl(f"DemoHub{dx}", 0.36, 0.44, "X", (dx, 0, 0), m_hub, DEMO_WHEELS, seg=24)
cyl("DemoAxle", 0.12, 1.6, "X", (0, 0, 0), m_chrome, DEMO_WHEELS)
cyl("DemoStrut", 0.2, 3.0, "Z", (0, 0, 1.5), m_chrome, DEMO_WHEELS)

# ================= main landing gear (6 wheels, generic) + a cut wing chunk above =================
def gear(name):
    g = empty(name)
    for ay in (-1.45, 0.0, 1.45):
        for dx in (-0.72, 0.72):
            cyl(f"{name}Tire{ay}{dx}", 0.66, 0.5, "X", (dx, ay, 0.66), m_tire, g, seg=40)
            cyl(f"{name}Hub{ay}{dx}", 0.36, 0.52, "X", (dx, ay, 0.66), m_hub, g, seg=24)
        cyl(f"{name}Axle{ay}", 0.1, 1.9, "X", (0, ay, 0.66), m_chrome, g)
    box(f"{name}Beam", -0.14, 0.14, -1.6, 1.6, 0.58, 0.86, m_grey, g)
    cyl(f"{name}Strut", 0.22, 4.0, "Z", (0, 0, 2.7), m_chrome, g)
    cyl(f"{name}Oleo", 0.30, 2.0, "Z", (0, 0, 3.6), m_grey, g)
    bm = bmesh.new(); add_bar(bm, (0, -0.2, 1.4), (0, -2.2, 4.4), 0.16); mesh_obj(f"{name}Brace", bm, m_grey, g)
    return g
GEAR = gear("Gear")
WING = box("WingChunk", -7.0, 5.0, -3.0, 6.0, 4.55, 5.25, m_white, GEAR)
cyl("Nacelle", 1.5, 5.0, "Y", (-4.6, 0.6, 3.15), m_white, GEAR, seg=40)
cyl("NacelleIntake", 1.25, 0.1, "Y", (-4.6, -1.92, 3.15), m_dark, GEAR, seg=40)
CAR_TIRE = empty("CarTire")
cyl("CarTireRubber", 0.33, 0.22, "X", (0, 0, 0.33), m_tire, CAR_TIRE, seg=36)
cyl("CarTireRim", 0.2, 0.24, "X", (0, 0, 0.33), m_hub, CAR_TIRE, seg=24)
bm = bmesh.new(); add_arrow(bm, (0.0, 3.9), (0, -1), 2.4, 0.9, y=0.0); LOAD_ARROW = mesh_obj("LoadArrow", bm, m_arrowG)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in ((-1.6, 0, 0.0), (1.6, 0, 0.0), (3.6, 0, Z_SOIL - 0.6), (-3.6, 0, Z_SOIL - 0.6))]
bm.faces.new(vs); LOADCONE = mesh_obj("LoadSpread", bm, m_loadcone)
bm = bmesh.new(); add_arrow(bm, (-1.3, -0.24), (1, 0), 2.6, 0.22, y=0.0); JOINT_ARROW = mesh_obj("JointArrow", bm, m_arrowC)

# ================= the airliner (generic, no livery): nose to local -y, origin at the wheel contact patch =================
PLANE = empty("Plane")
fus = lathe("Fuselage", [(0.0, -32.0), (0.9, -31.3), (1.9, -29.6), (2.7, -27.0), (3.1, -23.0), (3.1, 18.0), (2.6, 24.0), (1.6, 29.0), (0.5, 32.0), (0.0, 32.2)],
            m_white, a0=0.0, ang=2 * math.pi, seg=40)
par(fus, PLANE); fus.location = (0, 0, 5.0); fus.rotation_euler = (math.radians(-90), 0, 0)
def plate(name, pts, th, m_, parent):
    bm = bmesh.new(); top = [bm.verts.new((x, y, z + th / 2)) for x, y, z in pts]; bot = [bm.verts.new((x, y, z - th / 2)) for x, y, z in pts]
    bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts); bm.faces.new([top[i], bot[i], bot[j], top[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return mesh_obj(name, bm, m_, parent)
for sg in (-1, 1):
    plate(f"Wing{sg}", [(sg * 2.5, -7.0, 3.7), (sg * 31.0, 11.0, 5.2), (sg * 31.0, 14.0, 5.2), (sg * 2.5, 6.0, 3.7)], 0.5, m_white, PLANE)
    plate(f"Stab{sg}", [(sg * 0.5, 24.0, 6.4), (sg * 11.0, 30.5, 7.0), (sg * 11.0, 32.5, 7.0), (sg * 0.5, 31.0, 6.4)], 0.3, m_white, PLANE)
    cyl(f"Engine{sg}", 1.6, 6.5, "Y", (sg * 10.0, -6.0, 2.9), m_grey, PLANE, seg=40)
    cyl(f"EngineIntake{sg}", 1.35, 0.1, "Y", (sg * 10.0, -9.3, 2.9), m_dark, PLANE, seg=40)
    g = gear(f"PG{sg}"); par(g, PLANE); g.location = (sg * 5.5, 3.0, 0.0)
bm = bmesh.new(); pts = [(23.0, 7.0), (32.0, 7.6), (35.5, 17.5), (31.5, 17.5)]
l_ = [bm.verts.new((-0.2, y, z)) for y, z in pts]; r_ = [bm.verts.new((0.2, y, z)) for y, z in pts]
bm.faces.new(l_); bm.faces.new(list(reversed(r_)))
for i in range(4):
    j = (i + 1) % 4; bm.faces.new([l_[i], r_[i], r_[j], l_[j]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj("Fin", bm, m_white, PLANE)
for dx in (-0.4, 0.4): cyl(f"NoseTire{dx}", 0.6, 0.4, "X", (dx, -25.0, 0.6), m_tire, PLANE, seg=32)
cyl("NoseStrut", 0.16, 2.6, "Z", (0, -25.0, 1.8), m_chrome, PLANE)

# ================= construction machines =================
ROLLER = empty("Roller")
DRUM = cyl("Drum", 0.75, 2.1, "Y", (0, 0, 0), m_yel, None, seg=40); par(DRUM, ROLLER)
box("RollerFrame", -1.1, 1.1, -1.2, 1.2, 0.6, 1.1, m_yel, ROLLER)
box("RollerCab", 0.4, 2.6, -0.9, 0.9, 0.6, 2.6, m_yel, ROLLER)
box("RollerGlass", 0.45, 2.55, -0.92, 0.92, 1.7, 2.5, m_glass, ROLLER)
SAW = empty("GroovingMachine")
box("SawBody", -1.3, 1.3, -2.0, 2.0, 0.35, 1.9, m_yel, SAW); box("SawHood", -1.25, 1.25, -2.4, -1.6, 0.05, 0.6, m_dark, SAW)
for dx in (-1.0, 1.0):
    for dy in (-1.4, 1.2): cyl(f"SawWheel{dx}{dy}", 0.35, 0.3, "X", (dx * 1.05, dy, 0.35), m_tire, SAW, seg=24)
TRUCK = empty("RubberTruck")
box("TruckBody", -1.25, 1.25, -3.5, 3.5, 0.6, 3.0, m_truck, TRUCK); box("TruckStripe", -1.27, 1.27, -3.52, 3.52, 1.5, 1.8, m_orng, TRUCK)
box("TruckCab", -1.2, 1.2, -5.2, -3.5, 0.6, 2.6, m_truck, TRUCK); box("TruckGlass", -1.22, 1.22, -5.25, -4.4, 1.6, 2.4, m_glass, TRUCK)
box("SprayBar", -1.6, 1.6, 3.6, 3.9, 0.15, 0.35, m_dark, TRUCK)
for dx in (-1.0, 1.0):
    for dy in (-4.2, 2.4): cyl(f"TruckWheel{dx}{dy}", 0.5, 0.4, "X", (dx * 1.1, dy, 0.5), m_tire, TRUCK, seg=24)

# ================= macro set (x = -720): groove profile; hydroplane set (x = -740) =================
def groove_block(name, x0, x1, y0, y1, depth=0.12, grooves=True, m_=m_con):
    """Block with saw-cut grooves running along x (1/4 in wide x 1/4 in deep, 1.5 in apart), profile in the yz plane."""
    gw, pitch = 0.00635, 0.0381
    prof = [(y0, 0.0)]
    if grooves:
        y = y0 + pitch / 2
        while y + gw < y1:
            prof += [(y, 0.0), (y, -gw), (y + gw, -gw), (y + gw, 0.0)]; y += pitch
    prof += [(y1, 0.0), (y1, -depth), (y0, -depth)]
    bm = bmesh.new(); a = [bm.verts.new((x0, y, z)) for y, z in prof]; b_ = [bm.verts.new((x1, y, z)) for y, z in prof]
    bm.faces.new(a); bm.faces.new(list(reversed(b_)))
    for i in range(len(prof)):
        j = (i + 1) % len(prof); bm.faces.new([a[i], a[j], b_[j], b_[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return mesh_obj(name, bm, m_)
XM, XH = -720.0, -740.0
box("MacroPlinth", XM - 0.3, XM + 0.6, -0.2, 0.55, -0.6, -0.121, m_plinth)
MACRO = groove_block("GrooveSpecimen", XM, XM + 0.5, 0.0, 0.35)
SMOOTH = groove_block("HydroSmooth", XH - 0.6, XH + 0.6, -3.0, 3.0, 0.4, grooves=False)
GROOVED = groove_block("HydroGrooved", XH - 0.6, XH + 0.6, -3.0, 3.0, 0.4, grooves=True)
box("HydroPlinth", XH - 0.7, XH + 0.7, -3.1, 3.1, -1.2, -0.401, m_plinth)
HTIRE = empty("HydroTire")
HT = cyl("HydroTireRubber", 0.66, 0.5, "X", (0, 0, 0), m_tire, HTIRE, seg=48)
cyl("HydroHub", 0.36, 0.52, "X", (0, 0, 0), m_hub, HTIRE, seg=24)
box("HydroSpoke", -0.27, 0.27, -0.05, 0.05, -0.30, 0.30, m_dark, HTIRE)
FILM = box("WaterFilm", XH - 0.6, XH + 0.6, -3.0, 3.0, 0.0, 0.012, m_water)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in ((XH - 0.25, -0.75, 0.0), (XH - 0.25, 0.15, 0.0), (XH - 0.25, 0.0, 0.07), (XH - 0.25, -0.75, 0.016),
                                 (XH + 0.25, -0.75, 0.0), (XH + 0.25, 0.15, 0.0), (XH + 0.25, 0.0, 0.07), (XH + 0.25, -0.75, 0.016))]
bm.faces.new(vs[:4]); bm.faces.new(list(reversed(vs[4:])))
for i in range(4):
    j = (i + 1) % 4; bm.faces.new([vs[i], vs[4 + i], vs[4 + j], vs[j]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); WEDGE = mesh_obj("WaterWedge", bm, m_water)
# Mantaflow (1 short shot, <= 4 s, res 64): water squeezed out from under the tire into the grooves
FL_DOM = box("FluidDomain", XH - 0.6, XH + 0.6, -1.2, 1.2, -0.02, 0.7, m_water)
FL_IN = box("FluidInflow", XH - 0.24, XH + 0.24, -0.9, -0.6, 0.004, 0.03, m_inv)

m_studio, _ = mat("Studio", (0.035, 0.038, 0.045), 0.6)
for xc_, fz in ((XC, -0.62), (XD, -2.42)):
    box(f"StudioFloor{xc_}", xc_ - 14, xc_ + 14, -16.0, 9.0, fz - 0.01, fz, m_studio)
    box(f"StudioWall{xc_}", xc_ - 14, xc_ + 14, 9.0, 9.2, fz, 14.0, m_studio)
box("StudioFloorMH", XH - 6, XM + 3, -6.0, 6.0, -1.25, -1.24, m_studio)
box("StudioWallM", XM + 1.2, XM + 1.4, -3.0, 3.0, -1.25, 3.0, m_studio)
box("StudioWallH", XH + 3.0, XH + 3.2, -6.0, 6.0, -1.25, 6.0, m_studio)
print("[build] geometry done")

# ================= animation =================
def keyv(sock, keys, interp="LINEAR"):
    prefs.keyframe_new_interpolation_type = interp
    keyval(sock, keys)
    prefs.keyframe_new_interpolation_type = "BEZIER"
def hold_keys(sock, keys):      # step changes
    keyv(sock, keys, "CONSTANT")
def win(t, a, b): return a <= t < b

# ---- the plane: lands toward the camera in the hook, takes off away over the CTA ----
TD = C["has"]
def plane_state(t):
    if t < C["which"]:
        if t < TD: y = 200.0 + 70.0 * (TD - t); z = 3.2 * (TD - t) / TD; pitch = -4.0
        else:
            tau = min(t - TD, 2.9); y = 200.0 - (70.0 * tau - 3.0 * tau * tau); z = 0.0; pitch = -4.0 * (1 - ease((t - TD) / 1.2))
        return (0.0, y, z), (math.radians(pitch), 0, 0)
    tau = t - C["which"]; y = 150.0 + 40.0 * tau + 6.0 * tau * tau
    z = 0.0 if tau < 2.2 else 4.0 * (tau - 2.2) ** 1.6
    pitch = -9.0 * ease((tau - 1.8) / 0.8)
    return (0.0, y, z), (math.radians(pitch), 0, math.pi)
PS = [plane_state(t) for t in TS]
for ax in range(3):
    bake(PLANE, "location", ax, [p[0][ax] for p in PS]); bake(PLANE, "rotation_euler", ax, [p[1][ax] for p in PS])
windows(PLANE, [(0, C["nearly"]), (C["which"], DUR)])
# touchdown smoke (hook) + touchdown puffs (rubber beat)
def emitter(name, x0, x1, y0, y1, z, parent=None):
    o = box(name, x0, x1, y0, y1, z, z + 0.02, m_inv, parent); return o
for sg in (-1, 1):
    e = emitter(f"TDSmoke{sg}", sg * 5.5 - 1.0, sg * 5.5 + 1.0, 197.0, 203.0, 0.0)
    m_ = fx.particles(e, "dust", F(TD), F(TD + 0.5), count=160)
    if m_: m_.particle_system.settings.particle_size = 0.7; m_.particle_system.settings.normal_factor = 2.0
    e = emitter(f"TDPuff{sg}", sg * 5.5 - 1.0, sg * 5.5 + 1.0, 36.0, 42.0, 0.0)
    m_ = fx.particles(e, "dust", F(C["touchdown"] - 0.05), F(C["touchdown"] + 0.35), count=120)
    if m_: m_.particle_system.settings.particle_size = 0.22; m_.particle_system.settings.normal_factor = 1.2
    try: m_.particle_system.settings.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.75, 0.75, 0.75, 1)
    except Exception: pass

# ---- compare columns pop ----
for o, t0 in ((CMP_R, C["nearly"] + 0.1), (CMP_H, C["double"])):
    bake_scale(o, lambda t, t0=t0: (1, 1, max(0.001, pop(t, t0, 0.3))))
    o.data.transform(Matrix.Translation((0, 0, 0)))

# ---- 'only the top layer': the layers below glow one after another ----
for b_, t0 in ((b_base, C["only"]), (b_subb, C["top"]), (b_subg, C["layer"])):
    glow(b_, pulse(t0, 1.2, 0.0, 0.12, 0.45, 0.4))
glow(b_con, pulse(C["nineteen"], 0.3, 0.0, 0.15, 1.4, 0.5))

# ---- demo: wheels slam, soft ground gives, the slab cracks and falls in (rigid body) ----
def wheel_z(t):
    if t < C["slam"]: return 6.5
    if t < C["down"]: p = lin((t - C["slam"]) / (C["down"] - C["slam"])); return 6.5 - 5.84 * p * p
    if t < C["gives"]: return 0.66 + 0.12 * math.sin(math.pi * lin((t - C["down"]) / 0.3)) if t < C["down"] + 0.3 else 0.66
    return 0.66 + 7.0 * ease((t - C["gives"] - 0.25) / 0.6)
bake_loc(DEMO_WHEELS, lambda t: (XD, 2.0, wheel_z(t)))
windows(DEMO_WHEELS, [(C["jets"] - 0.1, C["heres"])])
T_GIVE = C["gives"] + 0.45
bake_loc(PLUG, lambda t: (0, 0, -0.95 * ease((t - C["gives"]) / 0.6)))
par(PLUG_RED, PLUG)
keyv(RED_FAC, [(0, 0.0), (C["gives"] - 0.01, 0.0), (C["gives"] + 0.2, 0.8), (C["heres"], 0.8)])
for p in PIECES:
    try:
        p.rigid_body.kinematic = False; p.rigid_body.keyframe_insert("kinematic", frame=F(T_GIVE))
    except Exception as e: print("[fx] kinematic key skipped:", e)
for p in PIECES: windows(p, [(0, C["heres"])])

# ---- the main gear (two positions) + car tire + load arrow + load spread ----
def gear_loc(t):
    if win(t, C["joints"], C["how"]): return (-3.0, 3.0, 0.0)
    return (-5.5, 3.0, crown(-5.5) - 0.03 * ease((t - C["carry"]) / 0.4))
bake_loc(GEAR, gear_loc)
windows(GEAR, [(C["heres"], C["so"]), (C["joints"], C["how"])])
bake_loc(CAR_TIRE, lambda t: (-3.3, 0.8, crown(-3.3)))
bake_scale(CAR_TIRE, lambda t: (max(0.001, pop(t, C["six"] - 0.1)),) * 3)
windows(CAR_TIRE, [(C["six"] - 0.12, C["all"])])
bake_loc(LOAD_ARROW, lambda t: (-5.5, 0.25, 1.2 * (1 - ease((t - C["carry"] + 0.1) / 0.35))))
windows(LOAD_ARROW, [(C["carry"] - 0.1, C["tires"])])
glow(b_arrowG, [(0, 1.2), (C["three"], 1.2), (C["three"] + 0.2, 2.5), (C["pounds"] + 0.5, 1.2)])
bake_loc(LOADCONE, lambda t: (-5.5, -0.03, crown(-5.5)))
bake_scale(LOADCONE, lambda t: (0.4 + 0.6 * ease((t - C["all"]) / 1.2), 1, max(0.001, ease((t - C["all"]) / (C["dirt"] - C["all"])))))
windows(LOADCONE, [(C["all"], C["so"] + 0.3)])
keyv(LOADFAC, [(0, 0.0), (C["all"], 0.0), (C["all"] + 0.4, 0.42), (C["so"] + 0.3, 0.42)])
bake_loc(JOINT_ARROW, lambda t: (-0.4 + 0.4 * ease((t - C["load"]) / 0.5), -0.06, 0.0))
windows(JOINT_ARROW, [(C["load"] - 0.1, C["how"])])

# ---- layer cake: explode, fly away, rebuild layer by layer ----
EX0, EX1 = C["so"] + 0.15, C["cake"] - 0.2
FLY0, FLY1 = C["cake"], C["first"] - 0.15
R0, R1 = C["first"] + 0.25, C["subgrade"] - 0.05
def layer_off(t, lift, td):
    if t < EX0: return 0.0
    if t < FLY0: return lift * ease((t - EX0) / (EX1 - EX0))
    if t < td - 0.6: return lift + 40.0 * ease((t - FLY0) / (FLY1 - FLY0))
    return drop(t, td, h=2.5, d=0.45)
TD_SUBB, TD_BASE = C["subbase"] - 0.1, C["base"] - 0.1
TD_STRIP = {2: C["concrete2"] - 0.05, 3: C["poured"] - 0.05, 1: C["giant"], 4: C["giant"] + 0.15, 0: C["giant"] + 0.3, 5: C["giant"] + 0.45}
def strip_dx(t, i):
    if i not in (2, 3): return 0.0
    sg = 1 if i == 2 else -1                  # +: toward the joint at x = 0
    if win(t, C["expand"] - 0.05, C["shrink"] - 0.05): return sg * 0.008 * ease((t - C["expand"] + 0.05) / 0.3)
    if win(t, C["shrink"] - 0.05, C["steel"]): return sg * (0.008 - 0.038 * ease((t - C["shrink"] + 0.05) / 0.35))
    if win(t, C["steel"], C["steel"] + 0.4): return sg * -0.03 * (1 - ease((t - C["steel"]) / 0.4))
    return 0.0
for i, s in enumerate(STRIPS):
    bake_loc(s, lambda t, i=i: (strip_dx(t, i), 0.0, layer_off(t, 2.4, TD_STRIP[i])))
    windows(s, [(0, FLY1 + 0.05), (TD_STRIP[i] - 0.02, DUR)])
for o, lift, td in ((SLAB_BASE, 1.6, TD_BASE), (SLAB_SUBB, 0.8, TD_SUBB)):
    bake_loc(o, lambda t, lift=lift, td=td: (0.0, 0.0, layer_off(t, lift, td)))
    windows(o, [(0, FLY1 + 0.05), (td - 0.02, DUR)])
def loose(t):
    if t < FLY0: return 0.0
    if t < R0: return ease((t - FLY0) / (R0 - FLY0))
    return 1.0 - lin((t - R0) / (R1 - R0))
bake_loc(SLAB_SUBG, lambda t: (0.0, 0.0, 0.10 * loose(t)))
keyv(SUBG_LOOSE, [(t, loose(t)) for t in (0, FLY0, R0, R1)])
def roller_x(t): return -6.0 + 9.0 * ease((t - R0) / (R1 - R0))
bake_loc(ROLLER, lambda t: (roller_x(t), 1.35, Z_SUBG + 0.10 * loose(t) + crown(roller_x(t)) + 0.75))
bake_fn(DRUM, "rotation_euler", 1, lambda t: (roller_x(t) + 6.0) / 0.75)
windows(ROLLER, [(FLY1 - 0.1, C["next"])])
rd = emitter("RollerDust", -1.0, 1.0, -1.0, 1.0, -0.74, ROLLER)
m_ = fx.particles(rd, "dust", F(R0), F(R1), count=350)
if m_: m_.particle_system.settings.particle_size = 0.035
# drop dust when the layers land
for name, td in (("Subbase", TD_SUBB), ("Base", TD_BASE), ("Slab", TD_STRIP[2])):
    e = emitter(f"DropDust{name}", -6.0, 3.0, 0.0, 3.0, 0.02)
    m_ = fx.particles(e, "dust", F(td + 0.42), F(td + 0.65), count=90)
    if m_: m_.particle_system.settings.particle_size = 0.05
# ---- joints and dowels: the concrete turns see-through ----
keyv(CON_ALPHA, [(0, 1.0), (C["steel"] - 0.1, 1.0), (C["dowels"] + 0.2, 0.18), (C["how"] - 0.1, 0.18), (C["how"] - 0.05, 1.0)])
glow(b_steel, [(0, 0.0), (C["dowels"] - 0.01, 0.0), (C["dowels"] + 0.15, 3.5), (C["across"] + 0.4, 1.5), (C["how"], 0.0)])
# ---- weaker soil -> thicker layers ----
TH0, TH1 = C["thicker"] - 0.35, C["thicker"] + 0.45
def gscale(t):
    if win(t, TH0, C["now"] - 0.05): return 1.0 + 0.45 * ease((t - TH0) / (TH1 - TH0))
    return 1.0
bake_scale(GROUND, lambda t: (1.0, 1.0, gscale(t)))
keyv(SOIL_WEAK, [(0, 0.0), (C["weaker"], 0.0), (C["weaker"] + 0.5, 1.0), (C["now"] - 0.06, 1.0), (C["now"] - 0.05, 0.0)])
# ---- surface: crown arrows + rain ----
CROWN_ARROWS = []
for sg in (-1, 1):
    bm = bmesh.new(); add_arrow(bm, (sg * 0.6, 0.30), (sg * 1.0, -0.12), 7.0, 0.5, y=-0.05); a = mesh_obj(f"CrownArrow{sg}", bm, m_arrowC)
    windows(a, [(C["crown"] - 0.1, C["then3"])]); CROWN_ARROWS.append(a)
    bake_loc(a, lambda t, sg=sg: (sg * 1.5 * lin((t - C["rain"]) / 1.2), 0.0, -0.18 * lin((t - C["rain"]) / 1.2)))
rain = emitter("RainCloud", -16.0, 16.0, 0.0, 55.0, 13.0)
m_ = fx.particles(rain, "rain", F(C["rain"] - 0.6), F(C["then3"]), count=7000)
if m_: m_.particle_system.settings.particle_size = 0.03
# ---- grooving machine ----
GF0, GF1 = C["saws"], C["half"]
def gfront(t): return 3.0 + 37.0 * lin((t - GF0) / (GF1 - GF0))
hold_keys(G_XALL, [(0, 100.0), (C["saws"] - 0.02, -0.8), (C["at"], -100.0)])
keyv(G_FRONT, [(0, 3.0), (GF0, 3.0), (GF1, 40.0), (C["at"] - 0.05, 40.0), (C["at"], 600.0)])
bake_loc(SAW, lambda t: (-2.0, gfront(t) + 2.4, crown(-2.0)))
windows(SAW, [(C["then3"] - 0.3, C["quarter"])])
se = emitter("SawSlurry", -1.2, 1.2, -2.6, -2.3, 0.05, SAW)
m_ = fx.particles(se, "mud", F(GF0), F(GF1), count=300)
if m_:
    m_.particle_system.settings.particle_size = 0.03
    try: m_.particle_system.settings.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.55, 0.55, 0.53, 1)
    except Exception: pass
# ---- hydroplaning ----
def hlift(t):
    if t < C["lift"] - 0.2: return 0.0
    if t < C["grooves2"]: return 0.075 * ease((t - C["lift"] + 0.2) / 0.5)
    return 0.075 * (1 - ease((t - C["grooves2"]) / 0.4))
bake_loc(HTIRE, lambda t: (XH, 0.0, 0.66 + hlift(t)))
bake_fn(HTIRE, "rotation_euler", 0, lambda t: -18.0 * t)
windows(HTIRE, [(C["at"] - 0.05, C["every2"])])
windows(SMOOTH, [(0, C["grooves2"])]); windows(GROOVED, [(C["grooves2"], DUR)])
windows(FILM, [(C["at"] - 0.05, C["grooves2"])])
windows(WEDGE, [(C["water"] - 0.1, C["grooves2"])])
bake_scale(WEDGE, lambda t: (1.0, 0.4 + 0.6 * ease((t - C["water"]) / 0.5), 1.0 + 1.2 * ease((t - C["lift"] + 0.2) / 0.5)))
WEDGE.data.transform(Matrix.Translation((-XH, 0, 0))); WEDGE.location = (XH, 0, 0)
hs = box("HydroSprayEmitter", XH - 0.27, XH + 0.27, -0.25, 0.25, 0.0, 0.03, m_inv)
m_ = fx.particles(hs, "rain", F(C["grooves2"]), F(C["out"] + 0.3), count=900)
if m_: m_.particle_system.settings.particle_size = 0.01; m_.particle_system.settings.normal_factor = 2.5
FLUID_BAKE = "--bake-fluid" in ARGS
fx.fluid_domain(FL_DOM, FL_IN, eff=[HT, GROOVED], res=64, start=F(C["grooves2"] - 0.3), end=F(C["every2"]),
                cache_dir=os.path.join(HERE, "cache_fluid"))
windows(FL_DOM, [(C["grooves2"], C["every2"])] if FLUID_BAKE or os.path.isdir(os.path.join(HERE, "cache_fluid", "data")) else [])
FL_IN.hide_render = True
# ---- rubber + water-blast truck ----
keyv(R_AMT, [(0, 0.0), (C["touchdown"] - 0.05, 0.0), (C["rubber"] + 0.3, 1.0)])
TR0, TR1 = C["crews"] - 0.4, C["which"] + 0.2
def truck_y(t): return 58.0 - 28.0 * lin((t - TR0) / (TR1 - TR0))
bake_loc(TRUCK, lambda t: (-5.5, truck_y(t), crown(-5.5)))
windows(TRUCK, [(TR0, C["which"])])
keyv(C_FRONT, [(0, 999.0), (TR0 - 0.02, 999.0), (TR0, truck_y(TR0) + 3.75), (TR1, truck_y(TR1) + 3.75), (C["which"], 999.0)])
hold_keys(C_FRONT, [(C["which"], 999.0)])
ts = emitter("TruckSpray", -1.6, 1.6, 3.6, 3.9, 0.12, TRUCK)
m_ = fx.particles(ts, "rain", F(C["crews"]), F(C["which"]), count=1600)
if m_: m_.particle_system.settings.particle_size = 0.02
# compare set, macro + hydro sets are separate places; nothing to hide there

# ================= lights + world =================
fx.hdri("sunset", strength=0.55, rotation_deg=40.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    crw = wn.new("ShaderNodeValToRGB"); e = crw.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.92, 0.70, 0.52, 1); e[1].position = 0.30; e[1].color = (0.22, 0.36, 0.62, 1)
    wl.new(grad.outputs["Fac"], crw.inputs[0]); wl.new(crw.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 2.4; sun_d.color = (1.0, 0.88, 0.74); sun_d.angle = math.radians(2.0)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(58), 0, math.radians(-28))
mac_d = bpy.data.lights.new("MacroKey", "AREA"); mac_d.size = 0.6; mac_d.energy = 6.0; mac_d.color = (1.0, 0.96, 0.9)
mac = bpy.data.objects.new("MacroKey", mac_d); scene.collection.objects.link(mac); mac.location = (XM - 0.5, -0.4, 0.5)
mac.rotation_euler = (math.radians(55), 0, math.radians(-50))
hyd_d = bpy.data.lights.new("HydroKey", "AREA"); hyd_d.size = 3.0; hyd_d.energy = 250.0; hyd_d.color = (1.0, 0.96, 0.9)
hyd = bpy.data.objects.new("HydroKey", hyd_d); scene.collection.objects.link(hyd); hyd.location = (XH - 3.0, -2.0, 3.0)
hyd.rotation_euler = (math.radians(50), 0, math.radians(-60))
def aimed_key(name, loc, target, energy, size=2.0):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = (1.0, 0.96, 0.9)
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tg = bpy.data.objects.new(name + "Tgt", None); scene.collection.objects.link(tg); tg.location = target
    c_ = o.constraints.new("TRACK_TO"); c_.target = tg; c_.track_axis = "TRACK_NEGATIVE_Z"; c_.up_axis = "UP_Y"
    return o
aimed_key("CompareKey", (XC - 3.0, -4.0, 3.0), (XC, 0.5, 0.2), 400.0, 3.0)
aimed_key("DemoKey", (XD - 3.0, -5.0, 4.0), (XD, 1.0, -0.6), 900.0, 4.0)
aimed_key("DemoFill", (XD + 4.0, -5.0, 1.0), (XD, 1.0, -0.8), 250.0, 3.0)
for o_ in (mac, hyd): bpy.data.objects.remove(o_, do_unlink=True)
aimed_key("MacroKey", (XM - 0.25, -0.15, 0.12), (XM, 0.04, -0.01), 0.7, 0.2)
aimed_key("HydroKey", (XH - 2.6, -1.4, 1.6), (XH, 0.0, 0.4), 300.0, 2.0)
fx.glare(threshold=1.0, strength=0.5, size=7)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.02; cam_d.clip_end = 4000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-3.0, -14.0, 1.6), (-1.0, 200.0, -8.0), 60),
    (C["nineteen"], (-3.0, -12.8, 1.4), (-1.0, 200.0, -8.0), 60),
    (C["concrete"] + 0.4, (-1.2, -3.4, 0.25), (-1.2, 0.0, -0.25), 35),
    (C["nearly"] - 0.05, (-1.2, -3.1, 0.2), (-1.2, 0.0, -0.25), 35),
    (C["nearly"], (XC - 0.1, -3.7, 0.42), (XC, 0.6, 0.22), 26, "cut"),
    (C["only"] - 0.05, (XC, -3.4, 0.38), (XC, 0.6, 0.22), 26),
    (C["only"], (-1.2, -3.0, 0.2), (-1.2, 0.0, -0.3), 35, "cut"),
    (C["layer"] + 0.3, (-1.2, -5.4, -0.3), (-1.2, 0.0, -0.9), 35),
    (C["jets"] - 0.05, (-1.2, -5.6, -0.35), (-1.2, 0.0, -0.9), 35),
    (C["jets"], (XD - 1.0, -8.5, 2.4), (XD, 1.0, 0.6), 30, "cut"),
    (C["down"], (XD - 0.6, -7.8, 1.4), (XD, 1.0, -0.2), 30),
    (C["gives"], (XD - 0.3, -7.2, 0.6), (XD, 1.0, -0.6), 30),
    (C["heres"] - 0.05, (XD, -7.0, 0.5), (XD, 1.0, -0.7), 30),
    (C["heres"], (-2.0, -7.5, 2.4), (-5.3, 2.6, 1.6), 26, "cut"),
    (C["carry"], (-2.6, -8.5, 3.2), (-5.3, 2.2, 2.0), 26),
    (C["tires"] - 0.05, (-3.0, -8.2, 2.6), (-5.3, 2.2, 1.6), 26),
    (C["tires"], (-3.0, -3.8, 0.9), (-5.0, 1.2, 0.55), 30, "cut"),
    (C["all"] - 0.05, (-2.4, -3.9, 0.75), (-4.4, 1.0, 0.45), 30),
    (C["all"], (-4.2, -6.2, 0.9), (-5.3, 0.0, -0.4), 28, "cut"),
    (C["dirt"] + 0.4, (-4.6, -7.2, -0.3), (-5.3, 0.0, -1.1), 28),
    (C["so"] - 0.05, (-4.6, -7.3, -0.3), (-5.3, 0.0, -1.1), 28),
    (C["so"], (-1.5, -15.0, 1.2), (-1.5, 0.0, 0.6), 40, "cut"),
    (C["cake"] + 0.4, (-1.5, -15.5, 1.0), (-1.5, 0.0, 0.4), 40),
    (C["first"], (-1.5, -13.0, 0.0), (-1.5, 0.0, -0.9), 40),
    (C["subgrade"] + 0.6, (-1.5, -12.5, -0.3), (-1.5, 0.0, -1.0), 40),
    (C["next"] - 0.05, (-1.5, -12.4, -0.3), (-1.5, 0.0, -1.0), 40),
    (C["next"], (-2.5, -7.0, 0.9), (-2.0, 2.0, -0.9), 32, "cut"),
    (C["crushed"] + 0.5, (-2.3, -5.5, 0.4), (-2.0, 1.5, -0.85), 32),
    (C["then"] - 0.05, (-2.3, -5.4, 0.4), (-2.0, 1.5, -0.85), 32),
    (C["then"], (-1.5, -13.0, 0.6), (-1.5, 0.0, -0.5), 40, "cut"),
    (C["slabs2"] + 0.6, (-1.5, -12.0, 0.9), (-1.5, 0.0, -0.4), 40),
    (C["joints"] - 0.05, (-1.5, -11.9, 0.9), (-1.5, 0.0, -0.4), 40),
    (C["joints"], (0.0, -3.4, 0.9), (0.0, 0.6, -0.2), 30, "cut"),
    (C["steel"] - 0.1, (0.3, -2.8, 0.6), (0.0, 0.8, -0.25), 30),
    (C["across"] + 0.6, (0.6, -2.6, 0.5), (0.0, 1.0, -0.25), 30),
    (C["how"] - 0.05, (0.6, -2.6, 0.5), (0.0, 1.0, -0.25), 30),
    (C["how"], (-1.5, -14.0, 0.2), (-1.5, 0.0, -1.2), 36, "cut"),
    (C["weaker"], (-1.5, -15.0, -0.2), (-1.5, 0.0, -1.6), 36),
    (C["layers"] + 0.8, (-1.5, -16.5, -0.6), (-1.5, 0.0, -2.0), 36),
    (C["now"] - 0.05, (-1.5, -16.6, -0.6), (-1.5, 0.0, -2.0), 36),
    (C["now"], (-4.0, -10.0, 2.6), (0.0, 25.0, -0.6), 24, "cut"),
    (C["then3"] - 0.05, (-3.0, -9.0, 2.2), (0.0, 25.0, -0.6), 24),
    (C["then3"], (-6.5, -1.0, 5.5), (-2.0, 22.0, 0.0), 26, "cut"),
    (C["quarter"] - 0.05, (-6.0, 4.0, 5.0), (-2.0, 28.0, 0.0), 26),
    (C["quarter"], (XM - 0.13, 0.041, -0.008), (XM, 0.041, -0.010), 50, "cut"),
    (C["at"] - 0.05, (XM - 0.12, 0.043, -0.008), (XM, 0.043, -0.010), 50),
    (C["at"], (XH - 3.2, 0.3, 0.7), (XH, 0.1, 0.35), 35, "cut"),
    (C["every2"] - 0.05, (XH - 3.0, 0.3, 0.6), (XH, 0.1, 0.3), 35),
    (C["every2"], (-10.0, 8.0, 3.5), (-5.5, 40.0, 0.0), 26, "cut"),
    (C["which"] - 0.05, (-10.0, 10.0, 3.2), (-5.5, 40.0, 0.0), 26),
    (C["which"], (-10.0, -16.0, 2.2), (0.0, 80.0, -1.0), 30, "cut"),
    (DUR, (-9.0, -14.0, 2.0), (0.0, 80.0, -1.0), 30),
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
    shake = 0.0 if abs(l0.x) > 650 else 1.0          # no drift on the macro sets
    cam_loc.append(l0 + shake * Vector((0.02 * math.sin(t * 0.7), 0.0, 0.015 * math.sin(t * 0.9 + 1.0))))
    cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0); fill_d.energy = 1500
bake_scalar(fill_d, "energy", [max(20.0, min(1200.0, 700.0 * ((cl - ct).length / 45.0) ** 2)) if abs(cl.x) < 150 or abs(cl.x - XC) < 20 or abs(cl.x - XD) < 20 else 0.0
                               for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (6, 8, 0)

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
scene.view_settings.exposure = -0.3
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(1, F(C["heres"]))
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def layer_anchor(x, z):
    return lambda t: Vector((x, 0.0, z * gscale(t)))
ANCHP = {
    "concrete": layer_anchor(-1.2, -0.24), "base": layer_anchor(-1.2, -0.63), "subbase": layer_anchor(-1.2, -0.93),
    "subgrade": layer_anchor(-1.2, -1.38), "soil": layer_anchor(-1.2, -2.6),
    "concrete_w": layer_anchor(-8.0, -0.25), "base_w": layer_anchor(-8.0, -0.64), "subbase_w": layer_anchor(-8.0, -0.94), "subgrade_w": layer_anchor(-8.0, -1.4),
    "cmp_runway": lambda t: Vector((XC - 0.8, 0.0, 0.48)), "cmp_highway": lambda t: Vector((XC + 0.8, 0.0, 0.25)),
    "demo": lambda t: Vector((XD, 0.0, -0.7)),
    "gear": lambda t: Vector((-5.5, 1.2, 2.6)), "tire": lambda t: Vector((-6.2, 0.9, 0.66)), "cartire": lambda t: Vector((-3.3, 0.6, 0.45)),
    "dirt": lambda t: Vector((-5.5, 0.0, -1.95)),
    "joint": lambda t: Vector((0.0, 0.0, -0.05)), "dowel": lambda t: Vector((0.12, 0.22, -0.24)),
    "crown": lambda t: Vector((0.0, 0.0, 0.0)),
    "groove": lambda t: Vector((XM, 0.0222, -0.004)), "groove2": lambda t: Vector((XM, 0.0603, -0.004)),
    "htire": lambda t: Vector((XH, 0.0, 0.66 + hlift(t))), "water": lambda t: Vector((XH, -0.35, 0.02)),
    "rubber": lambda t: Vector((-5.5, 34.0, 0.0)), "truck": lambda t: Vector((-5.5, truck_y(t), 3.0)),
    "roller": lambda t: Vector((roller_x(t), 1.35, Z_SUBG + 2.2)),
    "saw": lambda t: Vector((-2.0, gfront(t) + 2.4, 1.9)),
    "plane": lambda t: Vector(plane_state(t)[0]) + Vector((0, 0, 5.0)),
}
anchors = {k: [] for k in ANCHP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"touchdown": round(TD, 3), "cmp_pops": [round(C["nearly"] + 0.1, 3), round(C["double"], 3)],
          "layer_glows": [round(C["only"], 3), round(C["top"], 3), round(C["layer"], 3)],
          "slam": round(C["down"], 3), "give": round(C["gives"], 3), "crack": round(T_GIVE, 3),
          "gear": round(C["heres"], 3), "load": round(C["carry"], 3), "cartire": round(C["six"] - 0.1, 3), "spread": RR(C["all"], C["dirt"]),
          "explode": RR(EX0, EX1), "fly": RR(FLY0, FLY1), "roller": RR(R0, R1),
          "drops": {"subbase": round(TD_SUBB + 0.45, 3), "base": round(TD_BASE + 0.45, 3), "slabs": sorted(round(v + 0.45, 3) for v in TD_STRIP.values())},
          "expand": round(C["expand"], 3), "shrink": round(C["shrink"], 3), "dowels": round(C["dowels"], 3), "load_across": round(C["load"], 3),
          "thicken": RR(TH0, TH1), "rain": RR(C["rain"] - 0.6, C["then3"]), "saw": RR(GF0, GF1),
          "hydro": RR(C["at"], C["every2"]), "lift": round(C["lift"] - 0.2, 3), "grooves_out": round(C["grooves2"], 3),
          "rubber": round(C["touchdown"], 3), "spray": RR(C["crews"], C["which"]), "takeoff": round(C["which"], 3)}
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
    if "--range" in ARGS: scene.frame_start, scene.frame_end = [int(x) for x in arg("--range").split(",")]  # partial re-render
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
