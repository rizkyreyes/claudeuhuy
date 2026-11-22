# Jeans rivets (3d-36): why jeans have copper rivets + the tiny watch pocket. Claim-first hook ("Those little copper dots on your jeans
# were patented in 1873.") on a close-up of the copper rivet at a jeans pocket corner -> both rivets hold the pocket (answer) -> stake
# what-if: no rivets, the corner rips and everything falls out (rigid body coins/nails, lint dust) -> why: the pull runs along the
# opening, the seam stops at the corner, the force piles on the last stitches, they snap, the tear runs -> 1870s tailor's bench (no
# people): work pants, rivet tray (GN scatter), horse blanket strap with copper rivets -> rivets drop onto the pocket corners ->
# RIVET CROSS-SECTION: post up through 3 denim layers, cap on top, the setting punch hits, the post mushrooms into the cap (sparks),
# layers clamp, the pull spreads into the metal ring -> patent fee coins, the bolt of denim from the cloth seller, the patent sheet ->
# the watch pocket: a pocket watch slides in -> CTA push-in.
# Illustrative, 1 unit = 1 cm (cross-section set exaggerated ~10x): generic jeans front panel, generic rivets, generic bench props.
# No logos, no brand names, no text in 3D, no people.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
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
random.seed(36)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("those", "Those"), ("copper", "copper"), ("dots", "dots"), ("jeans", "jeans"), ("patented", "patented"), ("eighteen", "eighteen"),
        ("theyre", "They're"), ("holding", "holding"), ("pockets", "pockets"), ("without", "Without"), ("corner", "corner"), ("rip", "rip,"),
        ("everything", "everything"), ("fell", "fell"), ("heres", "Here's"), ("when", "When"), ("shove", "shove"), ("tool", "tool"),
        ("pull", "pull"), ("opening", "opening,"), ("seam", "seam"), ("stops", "stops"), ("corner2", "corner."), ("force", "force"),
        ("last", "last"), ("stitches", "stitches,"), ("thread", "thread"), ("snaps", "snaps,"), ("tear", "tear"), ("runs", "runs."),
        ("reno", "Reno"), ("tailor", "tailor"), ("davis", "Davis"), ("customer", "customer"), ("tearing", "tearing"), ("davis2", "Davis"),
        ("rivets", "rivets"), ("straps", "straps"), ("horse", "horse"), ("blankets", "blankets."), ("so", "So"), ("one", "one"),
        ("corner3", "corner."), ("rivet", "rivet"), ("two", "two"), ("post", "post"), ("pushed", "pushed"), ("every", "every"),
        ("layer", "layer"), ("inside", "inside,"), ("cap", "cap"), ("outside", "outside."), ("hit", "hit"), ("hammer", "hammer"),
        ("crushes", "crushes"), ("clamping", "clamping"), ("sandwich", "sandwich."), ("now", "Now"), ("spreads", "spreads"),
        ("metal", "metal"), ("threads", "threads."), ("davis3", "Davis"), ("afford", "afford"), ("fee", "fee,"), ("teamed", "teamed"),
        ("cloth", "cloth,"), ("levi", "Levi"), ("they", "They"), ("patent2", "patent"), ("may", "May"), ("eighteen2", "eighteen"),
        ("and", "And"), ("tiny", "tiny"), ("pocket", "pocket"), ("right", "right"), ("made", "made"), ("watch", "watch,"),
        ("safe", "safe"), ("smashed", "smashed."), ("do", "Do"), ("tiny2", "tiny"), ("jeans2", "jeans?"), ("tell", "Tell"),
        ("comments", "comments.")]
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
CL = coll("JeansRivets")
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



def windows_r(obj, wins):
    """render-only visibility (rigid bodies must stay in the sim)"""
    def kr(o, fr, h): key(o, "hide_render", fr, h, "CONSTANT")
    kr(obj, 1, True)
    for t0, t1 in wins:
        kr(obj, 1 if t0 <= 0 else F(t0), False)
        if t1 < DUR: kr(obj, F(t1), True)

# ================= timing =================
T_HOOK = (0.0, C["theyre"]); T_ANS = (C["theyre"], C["without"]); T_STAKE = (C["without"], C["heres"])
T_WHY = (C["heres"], C["reno"]); T_BENCH = (C["reno"], C["so"]); T_SET = (C["so"], C["rivet"]); T_XS = (C["rivet"], C["davis3"])
T_PAT = (C["davis3"], C["and"]); T_WATCH = (C["and"], C["do"]); T_CTA = (C["do"], DUR)
BX = 1000.0          # 1870s tailor's bench set
RX = 2000.0          # rivet cross-section set (exaggerated scale)

# ================= materials =================
def denim(name, base=(0.016, 0.03, 0.09), light=(0.06, 0.10, 0.22), scale=5.0, fade=True):
    """Indigo twill: diagonal wave bands (warp) + white-ish weft specks + soft fading noise."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "DIAGONAL"
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 0.6; wv.inputs["Detail"].default_value = 2.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.08; nz.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    c1 = mix_rgb(nt, wv.outputs["Fac"], base, light)
    if fade:
        mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.45; mr.inputs[2].default_value = 0.75; mr.inputs[3].default_value = 0.0; mr.inputs[4].default_value = 0.28
        L.new(nz.outputs["Fac"], mr.inputs[0]); c1 = mix_rgb(nt, mr.outputs[0], c1, (0.20, 0.30, 0.50))
    L.new(c1, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.85
    try: b.inputs["Sheen Weight"].default_value = 0.4; b.inputs["Sheen Tint"].default_value = (0.6, 0.7, 1.0, 1)
    except Exception: pass
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; bp.inputs["Distance"].default_value = 0.02
    L.new(wv.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (1.0, 0.3, 0.24, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
def wood(name, c1=(0.30, 0.17, 0.08), c2=(0.16, 0.08, 0.035), scale=0.06):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1.0, 8.0, 1.0)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS"; wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 8.0
    wv.inputs["Detail"].default_value = 3.0; L.new(mp.outputs[0], wv.inputs["Vector"])
    L.new(mix_rgb(nt, wv.outputs["Fac"], c1, c2), b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.55
    return m, b
def plaid(name, c1=(0.30, 0.07, 0.045), c2=(0.10, 0.045, 0.03), scale=0.35):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); ch = N.new("ShaderNodeTexChecker"); ch.inputs["Scale"].default_value = scale
    ch.inputs["Color1"].default_value = (*c1, 1); ch.inputs["Color2"].default_value = (*c2, 1)
    L.new(tc.outputs["Object"], ch.inputs["Vector"]); L.new(ch.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    return m, b
M_DEN, B_DEN = denim("Denim")
M_DEN2, _ = denim("DenimFacing", base=(0.012, 0.022, 0.07), light=(0.045, 0.08, 0.17))
M_DENCUT, B_DENCUT = denim("DenimCut", base=(0.03, 0.06, 0.18), light=(0.55, 0.58, 0.66), scale=1.2, fade=False)
M_COP, B_COP = mat("Copper", (0.80, 0.36, 0.18), rough=0.42, metallic=1.0, emit_rgb=(1.0, 0.45, 0.15))
M_COP2, B_COP2 = mat("CopperBench", (0.80, 0.36, 0.18), rough=0.42, metallic=1.0, emit_rgb=(1.0, 0.45, 0.15))
M_POST, B_POST = mat("CopperPost", (0.80, 0.36, 0.18), rough=0.40, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_CAPX, B_CAPX = mat("CopperCapX", (0.82, 0.38, 0.19), rough=0.38, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_BRASS, _ = mat("Brass", (0.85, 0.66, 0.30), rough=0.3, metallic=1.0)
M_GOLDW, B_GOLDW = mat("WatchGold", (1.0, 0.76, 0.36), rough=0.18, metallic=1.0, emit_rgb=(1.0, 0.75, 0.3))
M_FACE, _ = mat("WatchFace", (0.92, 0.90, 0.84), rough=0.3)
M_HAND, _ = mat("WatchHands", (0.05, 0.05, 0.06), rough=0.4)
M_THREAD, B_THREAD = mat("Thread", (0.85, 0.58, 0.18), rough=0.6, emit_rgb=(1.0, 0.74, 0.27))
M_LAST, B_LAST = mat("LastStitches", (0.85, 0.58, 0.18), rough=0.6, emit_rgb=(1.0, 0.25, 0.18))
M_BROKEN, B_BROKEN = mat("BrokenThread", (0.85, 0.58, 0.18), rough=0.6, emit_rgb=(1.0, 0.25, 0.18))
M_GAP, _ = mat("TearGap", (0.006, 0.008, 0.015), rough=0.9)
M_FRAY, _ = mat("Fray", (0.85, 0.86, 0.88), rough=0.9)
M_STEEL, B_STEEL = mat("Steel", (0.30, 0.31, 0.33), rough=0.5, metallic=1.0)
M_SILVER, _ = mat("Silver", (0.80, 0.80, 0.82), rough=0.25, metallic=1.0)
M_COINR, B_COINR = mat("CoinRed", (0.80, 0.80, 0.82), rough=0.25, metallic=1.0, emit_rgb=(1.0, 0.25, 0.18))
M_WOOD, _ = wood("Bench")
M_WALL, _ = wood("Wall", c1=(0.10, 0.06, 0.035), c2=(0.06, 0.035, 0.02), scale=0.03)
M_LEATHER, _ = mat("Leather", (0.28, 0.13, 0.05), rough=0.6, noise=0.5)
M_BLANKET, _ = plaid("Blanket")
M_PAPER, B_PAPER = mat("Paper", (0.86, 0.79, 0.62), rough=0.8, emit_rgb=(1.0, 0.8, 0.4))
M_INK, _ = mat("Ink", (0.18, 0.10, 0.05), rough=0.7)
M_WAX, _ = mat("Wax", (0.55, 0.05, 0.04), rough=0.35)
M_WHITE, _ = mat("Cotton", (0.82, 0.80, 0.76), rough=0.9)
M_BACK, _ = mat("Backdrop", (0.035, 0.04, 0.055), rough=0.9)
M_FLOOR, _ = mat("StudioFloor", (0.05, 0.05, 0.06), rough=0.5)
M_CYAN, B_CYAN = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 3.0)
M_RED, B_RED = emit_mat("RedGlow", (1.0, 0.30, 0.24), 6.0)
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (1.0, 0.74, 0.27), 5.0)
M_INV = bpy.data.materials.new("Invisible")
try: M_INV.use_nodes = True
except Exception: pass
_nt = M_INV.node_tree
for _n in list(_nt.nodes):
    if _n.type != "OUTPUT_MATERIAL": _nt.nodes.remove(_n)
_tr = _nt.nodes.new("ShaderNodeBsdfTransparent"); _nt.links.new(_tr.outputs[0], next(n for n in _nt.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])

# ================= geometry helpers =================
def prism(name, outline, y0, y1, m_, link=True):
    """Extrude an XZ outline (list of (x, z)) between y0 (front) and y1 (back)."""
    bm = bmesh.new()
    fr = [bm.verts.new((x, y0, z)) for x, z in outline]; bk = [bm.verts.new((x, y1, z)) for x, z in outline]
    bm.faces.new(fr); bm.faces.new(list(reversed(bk)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        try: bm.faces.new([fr[i], fr[j], bk[j], bk[i]])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_, link=link)
def qbez(a, c, b, n=40):
    return [((1 - u) ** 2 * a[0] + 2 * u * (1 - u) * c[0] + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * u * (1 - u) * c[1] + u * u * b[1]) for u in [i / n for i in range(n + 1)]]
def offset2d(pts, d):
    out = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]; b = pts[min(len(pts) - 1, i + 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, tz) or 1
        out.append((p[0] + d * tz / L, p[1] - d * tx / L))
    return out
def resample(pts, step):
    P = Path([(x, 0, z) for x, z in pts]); n = max(1, int(P.L / step))
    return [(P.at(P.L * i / n).x, P.at(P.L * i / n).z) for i in range(n + 1)], P.L
def stitches(bm, pts2d, y, dash=0.45, gap=0.22, w=0.12, mi=0, keep=None):
    """Raised stitch dashes along a 2D path in the XZ plane at depth y. keep(s, L) filters by arc length."""
    P = Path([(x, y, z) for x, z in pts2d]); s = 0.0
    while s + dash <= P.L:
        if keep is None or keep(s, P.L):
            add_seg(bm, P.at(s), P.at(s + dash), w * 0.5, seg=6, mi=mi)
        s += dash + gap
def dome(name, r, h, m_, loc, seg=32, base=0.08):
    prof = [(0.0, 0.0), (r, 0.0), (r, base)] + [(r * math.cos(a), base + h * math.sin(a)) for a in [math.radians(x) for x in range(10, 91, 10)]]
    prof[-1] = (0.0, base + h)
    o = lathe(name, prof, m_, ang=2 * math.pi, seg=seg); o.location = loc
    return o

# ================= MAIN SET: jeans front panel (x -20..20, z -30..40, front face at y = 0) =================
PA, PCTRL, PB = (2.0, 36.0), (5.0, 24.0), (20.0, 21.0)     # pocket opening: top (waistband) -> side seam
CURVE = qbez(PA, PCTRL, PB, 48)
PANEL = prism("FrontPanel", [(-20.0, -30.0), (20.0, -30.0), (20.0, PB[1])] + list(reversed(CURVE))[1:-1] + [PA, (-20.0, 36.0)], 0.0, 0.25, M_DEN)
FACING = prism("PocketFacing", [PA, (20.0, 36.0), PB] + list(reversed(CURVE))[1:-1], 1.30, 1.55, M_DEN2)
BAGBACK = box("PocketBagBack", 0, 20.5, 1.55, 1.7, 18, 36, M_WHITE)
WAIST = box("Waistband", -20.5, 20.5, -0.25, 1.6, 36.0, 40.0, M_DEN)
LOOPS = [box(f"BeltLoop{i}", x - 0.7, x + 0.7, -0.55, -0.25, 34.8, 40.6, M_DEN) for i, x in enumerate((-9.0, 7.0))]
BUTTON = dome("WaistButton", 1.1, 0.45, M_BRASS, (-17.0, -0.25, 38.0)); BUTTON.rotation_euler = (math.radians(90), 0, 0)
WP_X0, WP_X1, WP_Z0, WP_Z1 = 9.0, 15.4, 27.4, 34.6
WPOCK = box("WatchPocket", WP_X0, WP_X1, 0.36, 0.46, WP_Z0, WP_Z1, M_DEN)
SIDE = box("SidePanel", 20.0, 34.0, 0.3, 0.6, -30.0, 36.0, M_DEN2)
BACKDROP = box("Backdrop", -400, 400, 60, 61, -200, 300, M_BACK)
SFLOOR = box("StudioFloor", -400, 400, -60, 60, -32.2, -32.0, M_FLOOR)
# stitching (gold thread): double row along the opening, side seam, waistband, fly J, watch pocket
SEAM_IN = offset2d(CURVE, -0.55); SEAM_IN2 = offset2d(CURVE, -1.0)
L_CURVE = Path([(x, 0, z) for x, z in SEAM_IN]).L
LAST_S = 2.6                                     # the "last few stitches" before the side-seam corner (arc length from the end)
bm = bmesh.new()
for pts in (SEAM_IN, SEAM_IN2):
    stitches(bm, pts, -0.03, keep=lambda s, L: s < L - LAST_S)
for xs in (19.3, 18.9): stitches(bm, [(xs, -30.0), (xs, 20.6)], -0.03)
for zs in (36.4, 39.6): stitches(bm, [(-20.0, zs), (20.0, zs)], -0.28)
stitches(bm, [(-14.0, 35.8)] + [(-14.0 + 3.0 * (1 - math.cos(a)), 14.0 - 3.0 * math.sin(a) - 4.0) for a in [math.radians(x) for x in range(0, 91, 10)]][::-1][::-1], -0.03)
stitches(bm, [(-14.0, 35.8), (-14.0, 10.0)] + [(-14.0 + 4.0 * (1 - math.cos(a)), 10.0 - 4.0 * math.sin(a)) for a in [math.radians(x) for x in range(10, 91, 10)]], -0.03)
stitches(bm, [(WP_X0 + 0.4, WP_Z1 - 0.5), (WP_X0 + 0.4, WP_Z0 + 0.4), (WP_X1 - 0.4, WP_Z0 + 0.4), (WP_X1 - 0.4, WP_Z1 - 0.5)], 0.33, dash=0.35, gap=0.18, w=0.1)
stitches(bm, [(WP_X0 + 0.3, WP_Z1 - 0.35), (WP_X1 - 0.3, WP_Z1 - 0.35)], 0.33, dash=0.35, gap=0.18, w=0.1)
THREAD = mesh_obj("Stitching", bm, M_THREAD)
bm = bmesh.new()
for pts in (SEAM_IN, SEAM_IN2): stitches(bm, pts, -0.03, keep=lambda s, L: s >= L - LAST_S)
LASTST = mesh_obj("LastStitches", bm, M_LAST)
# broken stitches: short tilted ends + loose fibres near the corner
bm = bmesh.new(); rnd = random.Random(5)
PIN = Path([(x, -0.05, z) for x, z in SEAM_IN])
for k in range(10):
    p = PIN.at(PIN.L - LAST_S + LAST_S * k / 10.0) + Vector((rnd.uniform(-0.3, 0.3), 0, rnd.uniform(-0.3, 0.3)))
    d = Vector((rnd.uniform(-1, 1), -rnd.uniform(0.2, 0.8), rnd.uniform(-1, 1))).normalized() * rnd.uniform(0.3, 0.6)
    add_seg(bm, p, p + d, 0.05, seg=5)
BROKEN = mesh_obj("BrokenStitches", bm, M_BROKEN)
# rivets: copper domes at both ends of the opening
P_IN = Path([(x, 0, z) for x, z in SEAM_IN])
RA, RB = P_IN.at(0.7), P_IN.at(P_IN.L - 0.7)
RIV_A = dome("RivetTop", 0.55, 0.32, M_COP, (RA.x, -0.02, RA.z)); RIV_A.rotation_euler = (math.radians(90), 0, 0)
RIV_B = dome("RivetSide", 0.55, 0.32, M_COP, (RB.x, -0.02, RB.z)); RIV_B.rotation_euler = (math.radians(90), 0, 0)
WR_A = dome("WatchRivetL", 0.32, 0.18, M_COP, (WP_X0 + 0.45, 0.32, WP_Z1 - 0.45)); WR_A.rotation_euler = (math.radians(90), 0, 0)
WR_B = dome("WatchRivetR", 0.32, 0.18, M_COP, (WP_X1 - 0.45, 0.32, WP_Z1 - 0.45)); WR_B.rotation_euler = (math.radians(90), 0, 0)
# rivets: absent from "Without" until they drop back in on "one" / "corner."
for o_, t_ in ((RIV_A, C["one"]), (RIV_B, C["corner3"])):
    windows(o_, [(0, C["without"]), (t_ - 0.45, DUR)])
    base = Vector(o_.location)
    bake_loc(o_, lambda t, b=base, t_=t_: (b.x, b.y - (drop(t, t_ - 0.45, h=9.0, d=0.45) if T_SET[0] <= t < T_SET[1] else 0.0), b.z))
glow(B_COP, [(0, 0.0), (C["copper"] - 0.05, 0.0), (C["copper"] + 0.2, 0.45), (C["dots"] + 0.6, 0.45), (C["jeans"] + 0.4, 0.0),
             (C["holding"], 0.0), (C["holding"] + 0.2, 0.8), (C["without"] - 0.2, 0.8), (C["without"], 0.0),
             (C["corner3"] + 0.1, 0.0), (C["corner3"] + 0.3, 0.8), (C["rivet"], 0.0)])
# pocket corner tear (origin at the corner, grows down the side seam)
TEAR_PTS = [(0.0, 0.0), (0.55, -1.2), (0.25, -2.6), (0.75, -4.0), (0.35, -5.6), (0.7, -7.0), (0.2, -8.6), (0.0, -9.2),
            (-0.3, -8.0), (-0.1, -6.4), (-0.55, -4.8), (-0.2, -3.2), (-0.6, -1.6), (-0.25, -0.6)]
TEAR = prism("Tear", TEAR_PTS, -0.04, -0.02, M_GAP)
bm = bmesh.new(); rnd = random.Random(9)
for x, z in TEAR_PTS[1:-1]:
    for _ in range(3):
        p = Vector((x + rnd.uniform(-0.15, 0.15), -0.05, z + rnd.uniform(-0.3, 0.3)))
        add_seg(bm, p, p + Vector((math.copysign(rnd.uniform(0.2, 0.5), x or 1), -0.05, rnd.uniform(-0.2, 0.2))), 0.03, seg=4)
FRAY = mesh_obj("TearFray", bm, M_FRAY); par(FRAY, TEAR)
TEAR.location = (PB[0] - 0.9, -0.0, PB[1] - 0.3)
def tear_s(t):
    if C["rip"] - 0.05 <= t < C["heres"]: return max(0.001, ease((t - C["rip"] + 0.05) / 0.7))
    if C["tear"] - 0.05 <= t < C["reno"]: return max(0.001, ease((t - C["tear"] + 0.05) / 0.8))
    return 0.001
bake_scale(TEAR, lambda t: (1.0, 1.0, tear_s(t)))
windows(TEAR, [(C["rip"] - 0.05, C["heres"]), (C["tear"] - 0.05, C["reno"])])
windows(BROKEN, [(C["rip"] - 0.05, C["heres"]), (C["snaps"] - 0.02, C["reno"])])
windows(LASTST, [(0, C["rip"] - 0.05), (C["heres"], C["snaps"] - 0.02), (C["reno"], DUR)])
glow(B_LAST, [(0, 0.0), (C["force"] - 0.05, 0.0), (C["force"] + 0.3, 4.0), (C["last"], 6.0), (C["stitches"] + 0.3, 12.0), (C["snaps"], 12.0)])
glow(B_BROKEN, [(0, 3.0)])
glow(B_THREAD, [(0, 0.0), (C["seam"] - 0.05, 0.0), (C["seam"] + 0.15, 4.0), (C["stops"] + 0.5, 4.0), (C["force"], 0.0)])
glow(B_DEN, [(0, 0.0), (C["force"], 0.0), (C["stitches"], 0.0), (C["snaps"], 0.0)])
# red stress light at the corner
RED_D = bpy.data.lights.new("StressRed", "POINT"); RED_D.color = (1.0, 0.25, 0.15); RED_D.shadow_soft_size = 1.0
RED_O = bpy.data.objects.new("StressRed", RED_D); scene.collection.objects.link(RED_O); RED_O.location = (PB[0] - 1.5, -2.0, PB[1] + 0.5)
for t_, v_ in [(0, 0.0), (C["rip"] - 0.05, 0.0), (C["rip"] + 0.2, 25.0), (C["heres"] - 0.05, 25.0), (C["heres"], 0.0),
               (C["force"], 0.0), (C["stitches"] + 0.2, 40.0), (C["runs"] + 0.6, 40.0), (C["reno"] - 0.02, 0.0)]:
    RED_D.energy = v_; RED_D.keyframe_insert("energy", frame=F(t_))
# the pull along the opening: cyan beads running from mid-opening to the corner (B4)
PULL = Path([(x, -0.25, z) for x, z in offset2d(CURVE, -0.3)[20:]])
beads("PullBead", PULL, 9, 0.22, M_CYAN, [(C["pull"] - 0.05, C["seam"] + 0.3)], speed=7.0)
beads("PullBead2", PULL, 7, 0.24, M_RED, [(C["force"] - 0.05, C["thread"])], speed=5.0)
# wrench sliding into the pocket (between the front panel and the facing)
bm = bmesh.new()
add_box(bm, -0.55, 0.55, -0.15, 0.15, -9.0, 0.0)
for a in range(0, 360, 30):
    a0, a1 = math.radians(a), math.radians(a + 30)
    if 60 < a < 120: continue
    add_seg(bm, (1.0 * math.cos(a0), 0, 1.0 + 1.0 * math.sin(a0)), (1.0 * math.cos(a1), 0, 1.0 + 1.0 * math.sin(a1)), 0.35, seg=6)
WRENCH = mesh_obj("Wrench", bm, M_STEEL); WRENCH.rotation_euler = (0, math.radians(-12), 0)
bake_loc(WRENCH, lambda t: (5.0, 0.75, PW([(C["shove"] - 0.3, 47.0), (C["tool"] + 0.4, 31.0), (C["pull"] + 0.5, 30.0)])(t)))
windows(WRENCH, [(C["shove"] - 0.3, C["seam"])])
# stake: what falls out (rigid body coins + nails), released on "fell"
FALL = []
for k in range(6):
    o = cyl(f"Coin{k}", 0.95 if k % 2 else 1.2, 0.18, "Y", (0, 0, 0), M_COP2 if k % 3 == 0 else M_SILVER, seg=24); FALL.append(o)
for k in range(5):
    bm = bmesh.new(); add_seg(bm, (0, 0, -2.2), (0, 0, 2.2), 0.09, seg=6); add_cyl(bm, 0.28, 0.1, "Z", (0, 0, 2.2), seg=10)
    FALL.append(mesh_obj(f"Nail{k}", bm, M_STEEL))
rnd = random.Random(3)
FLOOR_P = box("FallFloorPassive", -40, 60, -40, 40, -33.0, -32.0, M_INV)
fx.rigid(FALL, passive=[FLOOR_P], mass=0.05, friction=0.5, bounce=0.3)
for k, o in enumerate(FALL):
    p0 = Vector((PB[0] - 2.0 + rnd.uniform(-1.2, 1.2), -0.6 - rnd.uniform(0, 0.6), PB[1] - 2.5 + rnd.uniform(-2.0, 1.5)))
    o.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), rnd.uniform(0, 3))
    try:
        rb = o.rigid_body; rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=1)
        f0 = F(C["fell"]) + rnd.randint(0, 6)
        o.location = p0; o.keyframe_insert("location", frame=1); o.keyframe_insert("location", frame=f0)
        o.location = p0 + Vector((rnd.uniform(-0.1, 0.25), -0.25, -0.15)); o.keyframe_insert("location", frame=f0 + 2)
        rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 2)
        rb.kinematic = False; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 3)
    except Exception as e: print("[build] fall kinematic skipped", e)
    windows_r(o, [(C["fell"] - 0.1, C["heres"])])
LINT = box("LintEmitter", PB[0] - 1.6, PB[0] - 0.2, -0.3, -0.1, PB[1] - 8.0, PB[1] - 0.5, M_INV)
fx.particles(LINT, "dust", F(C["rip"]), F(C["fell"] + 0.6), count=260)
LINT2 = box("LintEmitter2", PB[0] - 1.8, PB[0] - 0.4, -0.3, -0.1, PB[1] - 2.0, PB[1] + 0.2, M_INV)
fx.particles(LINT2, "dust", F(C["snaps"]), F(C["runs"] + 0.6), count=160)
for d_ in (LINT, LINT2):
    try:
        ps = d_.particle_systems[0].settings; ps.particle_size = 0.05; ps.normal_factor = -0.8; ps.effector_weights.gravity = 0.05
        ps.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.75, 0.8, 0.9, 1)
    except Exception as e: print("[build] lint tune skipped", e)
# pocket watch (B8): slides down into the watch pocket, chain stays out to the belt loop
WATCH = empty("PocketWatch")
wc = cyl("WatchCase", 2.1, 0.75, "Y", (0, 0, 0), M_GOLDW, seg=48); par(wc, WATCH)
wf = cyl("WatchFace", 1.8, 0.05, "Y", (0, -0.4, 0), M_FACE, seg=48); par(wf, WATCH)
bm = bmesh.new(); add_box(bm, -0.06, 0.06, -0.46, -0.42, 0, 1.3); add_box(bm, -0.05, 0.05, -0.46, -0.42, 0, 0.9)
for a in range(0, 360, 30): add_box(bm, -0.04, 0.04, -0.45, -0.43, 1.5, 1.7)
hands = mesh_obj("WatchHands", bm, M_HAND); par(hands, WATCH); hands.rotation_euler = (0, math.radians(40), 0)
crown = cyl("WatchCrown", 0.35, 0.5, "Z", (0, 0, 2.35), M_GOLDW, seg=16); par(crown, WATCH)
bm = bmesh.new()
for a in range(0, 360, 20):
    a0, a1 = math.radians(a), math.radians(a + 20); add_seg(bm, (0.55 * math.cos(a0), 0, 2.95 + 0.55 * math.sin(a0)), (0.55 * math.cos(a1), 0, 2.95 + 0.55 * math.sin(a1)), 0.1, seg=6)
bow = mesh_obj("WatchBow", bm, M_GOLDW); par(bow, WATCH)
W_IN = C["made"] + 0.2
bake_loc(WATCH, lambda t: (12.2, 0.88, PW([(C["watch"] - 1.0, 44.0), (W_IN + 0.9, 33.2)])(t)))
windows(WATCH, [(C["watch"] - 1.0, C["do"]), (C["do"], DUR)])
CHAIN = poly_obj("WatchChain", sag_pts((12.2, 0.4, 36.5), (7.0, -0.5, 37.5), 2.0, 16), 0.09, M_GOLDW, seg=6)
windows(CHAIN, [(W_IN + 0.9, DUR)])
glow(B_GOLDW, [(0, 0.0), (C["watch"] - 0.05, 0.0), (C["watch"] + 0.2, 0.5), (C["safe"] + 0.8, 0.5), (C["do"], 0.0)])
# outline frame (a solid panel hid the pocket on the laptop GPU check, 22 Nov)
_wx0, _wx1, _wz0, _wz1, _t = WP_X0 - 0.15, WP_X1 + 0.15, WP_Z0 - 0.15, WP_Z1 + 0.15, 0.14
for _n, _b in (("L", (_wx0, _wx0 + _t, _wz0, _wz1)), ("R", (_wx1 - _t, _wx1, _wz0, _wz1)),
               ("B", (_wx0, _wx1, _wz0, _wz0 + _t)), ("T", (_wx0, _wx1, _wz1 - _t, _wz1))):
    WP_GLOW = box("WatchPocketGlow" + _n, _b[0], _b[1], 0.30, 0.34, _b[2], _b[3], M_GOLDG)
    windows(WP_GLOW, [(C["tiny"] - 0.05, C["made"] - 0.2)])

# ================= BENCH SET (1870s tailor's bench, no people) =================
BENCH = box("BenchTop", BX - 45, BX + 45, -18, 30, -5, 0, M_WOOD)
WALLB = box("BenchWall", BX - 120, BX + 120, 31, 32, -60, 90, M_WALL)
PANTS = [box(f"FoldedPants{i}", BX - 36 + i * 1.0, BX - 12 + i * 1.0, -12 + i * 0.8, 6 + i * 0.8, i * 2.2, i * 2.2 + 2.1, M_DEN) for i in range(3)]
bm = bmesh.new(); stitches(bm, [(BX - 33.0, 6.6), (BX - 11.0, 6.6)], -10.5, dash=0.8, gap=0.4, w=0.2)
PST = mesh_obj("PantsStitch", bm, M_THREAD); PST.rotation_euler = (0, 0, 0)
SPOOL = empty("Spool", (BX + 4, -8, 0))
for o_ in (cyl("SpoolCore", 1.4, 4.0, "Z", (0, 0, 2.6), M_THREAD), cyl("SpoolTop", 2.1, 0.4, "Z", (0, 0, 4.8), M_WOOD), cyl("SpoolBot", 2.1, 0.4, "Z", (0, 0, 0.2), M_WOOD)):
    par(o_, SPOOL)
SHEARS = empty("Shears", (BX - 4, -12, 0.3)); SHEARS.rotation_euler = (0, 0, math.radians(20))
for o_ in (box("BladeA", 0, 13, -0.5, 0.5, 0, 0.25, M_STEEL), box("BladeB", 0, 13, -0.5, 0.5, 0.25, 0.5, M_STEEL)):
    par(o_, SHEARS)
SHEARS.children[1].rotation_euler = (0, 0, math.radians(8))
TRAY = box("RivetTray", BX - 8, BX + 4, 4, 13, 0, 0.4, M_WOOD)
TRAYW = [box("TrayWallF", BX - 8, BX + 4, 3.6, 4, 0, 1.6, M_WOOD), box("TrayWallB", BX - 8, BX + 4, 13, 13.4, 0, 1.6, M_WOOD),
         box("TrayWallL", BX - 8.4, BX - 8, 3.6, 13.4, 0, 1.6, M_WOOD), box("TrayWallR", BX + 4, BX + 4.4, 3.6, 13.4, 0, 1.6, M_WOOD)]
TRAYF = box("TrayScatterSurface", BX - 7.6, BX + 3.6, 4.4, 12.6, 0.4, 0.42, M_WOOD)
RIV_INST = dome("LooseRivet", 0.5, 0.3, M_COP2, (0, 0, 0))
fx.scatter(TRAYF, RIV_INST, density=1.6, scale_min=0.8, scale_max=1.1, seed=4)
BLANKET = box("HorseBlanket", BX + 10, BX + 38, 2, 22, 0, 5, M_BLANKET)
STRAP = box("BlanketStrap", BX + 12, BX + 36, 1.6, 2.0, 1.6, 3.6, M_LEATHER)
STRAP_R = []
for k, x in enumerate((BX + 19.0, BX + 29.0)):
    o_ = dome(f"StrapRivet{k}", 0.55, 0.3, M_COP2, (x, 1.6, 2.6)); o_.rotation_euler = (math.radians(90), 0, 0); STRAP_R.append(o_)
glow(B_COP2, [(0, 0.0), (C["rivets"] - 0.05, 0.0), (C["rivets"] + 0.2, 0.5), (C["blankets"] + 0.6, 0.5), (C["so"], 0.0)])
BOLT = cyl("DenimBolt", 6.0, 32, "X", (BX - 18, 22, 6.0), M_DEN, seg=40)
BOLT_CORE = cyl("DenimBoltCore", 1.4, 32.4, "X", (BX - 18, 22, 6.0), M_WOOD, seg=16)
BOLT_G = cyl("DenimBoltGlow", 6.15, 0.5, "X", (BX - 10.0, 22, 6.0), M_GOLDG, seg=40)
windows(BOLT_G, [(C["cloth"] - 0.05, C["they"])])
COINS = [cyl(f"FeeCoin{k}", 1.2, 0.2, "Z", (BX + 16 + (k % 2) * 0.15, -9, 0.1 + 0.21 * k), M_COINR, seg=24) for k in range(5)]
glow(B_COINR, [(0, 0.0), (C["afford"] - 0.05, 0.0), (C["afford"] + 0.2, 3.0), (C["fee"] + 0.6, 3.0), (C["teamed"], 0.0)])
# patent sheet: parchment with a line drawing of riveted work pants (no text) and a wax seal; slides in on "patent"
SHEET = empty("PatentSheet")
sh = box("SheetPaper", -10.5, 10.5, -14, 14, 0, 0.05, M_PAPER); par(sh, SHEET)
legs = [(-5, 10), (5, 10), (5.6, -11), (1.2, -11), (0, 2), (-1.2, -11), (-5.6, -11), (-5, 10)]
bm = bmesh.new(); add_poly(bm, [(x, y, 0.1) for x, y in legs], 0.09, seg=5)
add_poly(bm, [(x, y, 0.1) for x, y in [(-5, 7.5), (-2.5, 7.0), (-1.2, 4.5)]], 0.07, seg=5); add_poly(bm, [(x, y, 0.1) for x, y in [(5, 7.5), (2.5, 7.0), (1.2, 4.5)]], 0.07, seg=5)
for x, y in [(-1.3, 4.6), (1.3, 4.6), (-4.8, 7.5), (4.8, 7.5)]: add_cyl(bm, 0.35, 0.1, "Z", (x, y, 0.12), seg=12)
draw = mesh_obj("SheetDrawing", bm, M_INK); par(draw, SHEET)
seal = cyl("WaxSeal", 1.5, 0.3, "Z", (6.5, -10.5, 0.2), M_WAX, seg=24); par(seal, SHEET)
bake_loc(SHEET, lambda t: (PW([(C["patent2"] - 0.45, BX + 40.0), (C["patent2"] + 0.35, BX + 2.0)])(t), -5.0, 0.05))
for o_ in [SPOOL, SHEARS] + COINS: windows(o_, [(0, C["they"])])
SHEET.rotation_euler = (0, 0, math.radians(-6))
windows(SHEET, [T_PAT])
glow(B_PAPER, [(0, 0.0), (C["may"] - 0.05, 0.0), (C["may"] + 0.2, 0.6), (C["and"] - 0.2, 0.6), (C["and"], 0.0)])
area_b = None

# ================= CROSS-SECTION SET: rivet through 3 denim layers (cut at y = 0, keep y >= 0) =================
LAYZ = [(0.0, 1.0), (1.08, 2.08), (2.16, 3.16)]
LAYERS = []
HOLE = cyl("RivetHoleCutter", 0.62, 12, "Z", (RX, 0, 1.5), M_INV, seg=40); HOLE.hide_render = True; HOLE.hide_viewport = True
for i, (z0, z1) in enumerate(LAYZ):
    o = box(f"DenimLayer{i}", RX - 9, RX + 9, 0.0, 9.0, z0, z1, [M_DENCUT])
    md = o.modifiers.new("Hole", "BOOLEAN"); md.object = HOLE; md.operation = "DIFFERENCE"; md.solver = "EXACT"
    LAYERS.append(o)
LGRP = empty("LayerStack", (RX, 0, 0))
for o in LAYERS:
    o.location = (-RX, 0, 0); par(o, LGRP)
POST_P = [(0.0, -0.4), (1.7, -0.4), (1.75, -0.2), (1.6, 0.0), (0.5, 0.0), (0.5, 3.75), (0.0, 3.75)]
POST_F = [(0.0, -0.4), (1.7, -0.4), (1.75, -0.2), (1.6, 0.0), (0.5, 0.0), (0.5, 3.35), (0.95, 3.55), (0.9, 3.7), (0.0, 3.62)]
POST = lathe("RivetPost", POST_P, M_POST, ang=math.pi, seg=40)
POSTF = lathe("RivetPostCrushed", POST_F, M_POST, ang=math.pi, seg=40)
CAP_P = [(0.6, 3.16), (1.5, 3.16), (1.52, 3.3)] + [(1.5 * math.cos(math.radians(a)), 3.3 + 0.9 * math.sin(math.radians(a))) for a in range(15, 91, 15)]
CAP_P[-1] = (0.0, 4.2)
CAP_P += [(0.0, 3.95), (0.62, 3.85)]
CAP = lathe("RivetCap", CAP_P, M_CAPX, ang=math.pi, seg=40)
T_HIT = C["hammer"] + 0.12
for o in (POST, POSTF, CAP): o.location = (RX, 0, 0)
bake_loc(POST, lambda t: (RX, 0, PW([(C["post"] - 0.1, -7.0), (C["inside"] + 0.3, 0.0)])(t)))
bake_loc(CAP, lambda t: (RX, 0, PW([(C["cap"] - 0.15, 7.0), (C["cap"] + 0.35, 0.25), (T_HIT - 0.02, 0.25), (T_HIT + 0.05, -0.05)])(t)))
bake_loc(POSTF, lambda t: (RX, 0, 0.0))
windows(POST, [(T_XS[0], T_HIT)]); windows(POSTF, [(T_HIT, T_XS[1])]); windows(CAP, [T_XS])
bake_scale(LGRP, lambda t: (1.0, 1.0, PW([(T_HIT - 0.01, 1.0), (T_HIT + 0.08, 0.93), (C["clamping"] + 0.4, 0.93)])(t)))
PUNCH = empty("SettingPunch")
M_PUNCH, _ = mat("PunchSteel", (0.20, 0.21, 0.23), rough=0.6, metallic=0.5)
for o_ in (cyl("PunchShaft", 1.3, 9.0, "Z", (0, 0, 4.6), M_PUNCH, seg=40), cyl("PunchTip", 1.55, 0.3, "Z", (0, 0, 0.15), M_PUNCH, seg=40)):
    par(o_, PUNCH)
bake_loc(PUNCH, lambda t: (RX, 3.0, PW([(C["one"], 16.0), (C["hit"] + 0.1, 9.0), (T_HIT - 0.07, 9.0), (T_HIT, 4.22), (T_HIT + 0.35, 4.3), (C["clamping"] + 0.4, 12.0), (C["layer"], 12)])(t)
                               if t < C["now"] else 30.0))
windows(PUNCH, [(C["hit"] - 0.2, C["now"])])
SPARK = box("SparkEmitter", RX - 1.5, RX + 1.5, -0.2, 0.2, 4.1, 4.3, M_INV)
fx.particles(SPARK, "sparks", F(T_HIT), F(T_HIT + 0.25), count=180)
try: SPARK.particle_systems[0].settings.particle_size = 0.05
except Exception as e: print("[build] spark tune skipped", e)
XFLOOR = box("XSetFloor", RX - 60, RX + 60, -40, 40, -8.2, -8.0, M_FLOOR)
XBACK = box("XSetBack", RX - 200, RX + 200, 40, 41, -100, 100, M_BACK)
# spread arrows (cyan) on the cut face of every layer, pointing at the rivet; a few red threads before it
bm = bmesh.new()
for z0, z1 in LAYZ:
    zc = (z0 + z1) / 2
    for side in (-1, 1):
        add_arrow(bm, (RX + side * 7.5, zc), (-side, 0), 5.2, 0.7, y=-0.08)
ARROWS = mesh_obj("SpreadArrows", bm, M_CYAN)
windows(ARROWS, [(C["spreads"] - 0.05, T_XS[1])])
glow(B_POST, [(0, 0.0), (C["spreads"] - 0.05, 0.0), (C["spreads"] + 0.25, 0.25), (T_XS[1], 0.25)])
glow(B_CAPX, [(0, 0.0), (C["spreads"] - 0.05, 0.0), (C["spreads"] + 0.25, 0.25), (T_XS[1], 0.25)])
bm = bmesh.new()
for k, (z0, z1) in enumerate(LAYZ):
    add_seg(bm, (RX - 8.5, -0.06, (z0 + z1) / 2 + 0.2), (RX - 0.7, -0.06, (z0 + z1) / 2 + 0.2), 0.06, seg=5)
THREADS_R = mesh_obj("FewThreads", bm, M_RED)
windows(THREADS_R, [(C["threads"] - 0.1, T_XS[1])])

# ================= world: HDRI light + own backdrop, key/rim lights per set =================
fx.hdri("interior", strength=0.35, rotation_deg=120.0, show_background=False)
try:
    wn = scene.world.node_tree.nodes
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    plain.inputs["Color"].default_value = (0.012, 0.014, 0.02, 1)
except Exception as e: print("[build] world colour skipped", e)
fx.glare(threshold=1.0, strength=0.45, size=7)
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.95, 0.88), target=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    if target is not None:
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    else: o.rotation_euler = rot
    return d
area("JeansKey", (-25.0, -45.0, 60.0), 30.0, 26000.0, target=(5, 0, 15))
area("JeansRim", (45.0, 20.0, 40.0), 20.0, 9000.0, target=(10, 0, 15), color=(0.75, 0.85, 1.0))
area("JeansFill", (30.0, -50.0, 0.0), 30.0, 5000.0, target=(10, 0, 15), color=(0.8, 0.88, 1.0))
area("BenchKey", (BX - 20.0, -35.0, 70.0), 30.0, 30000.0, target=(BX, 5, 0), color=(1.0, 0.85, 0.62))
area("BenchFill", (BX + 50.0, -40.0, 25.0), 25.0, 7000.0, target=(BX, 5, 0), color=(0.85, 0.9, 1.0))
area("XKey", (RX - 15.0, -25.0, 25.0), 15.0, 6000.0, target=(RX, 0, 2))
area("XRim", (RX + 20.0, 15.0, 15.0), 12.0, 4000.0, target=(RX, 0, 2), color=(0.7, 0.85, 1.0))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (RB.x - 7.0, -26.0, RB.z + 6.0), (RB.x - 2.0, 0.0, RB.z + 1.0), 50),
    (C["theyre"] - 0.05, (RB.x - 3.5, -13.0, RB.z + 2.5), (RB.x - 1.0, 0.0, RB.z + 0.5), 50),
    (C["theyre"], (7.0, -78.0, 20.0), (9.0, 0.0, 22.0), 40, "cut"),
    (C["without"] - 0.05, (8.0, -68.0, 21.0), (9.5, 0.0, 22.0), 40),
    (C["without"], (24.0, -46.0, 16.0), (16.0, 0.0, 13.0), 40, "cut"),
    (C["heres"] - 0.05, (23.0, -50.0, 12.0), (16.0, 0.0, 9.0), 40),
    (C["heres"], (11.0, -50.0, 30.0), (11.5, 0.0, 28.0), 45, "cut"),
    (C["seam"], (14.0, -40.0, 27.0), (14.0, 0.0, 25.0), 45),
    (C["force"], (PB[0] - 3.0, -20.0, PB[1] + 1.0), (PB[0] - 2.5, 0.0, PB[1] - 0.5), 45),
    (C["reno"] - 0.05, (PB[0] - 3.0, -22.0, PB[1] - 1.5), (PB[0] - 2.5, 0.0, PB[1] - 3.0), 45),
    (C["reno"], (BX - 8.0, -75.0, 40.0), (BX - 2.0, 6.0, 0.0), 35, "cut"),
    (C["davis2"] - 0.05, (BX - 2.0, -66.0, 36.0), (BX + 2.0, 6.0, 0.0), 35),
    (C["davis2"], (BX - 6.0, -22.0, 20.0), (BX - 2.0, 8.0, 0.0), 40, "cut"),
    (C["horse"] - 0.05, (BX - 3.0, -20.0, 18.0), (BX - 1.0, 8.0, 0.0), 40),
    (C["horse"], (BX + 22.0, -26.0, 9.0), (BX + 24.0, 2.0, 3.0), 40, "cut"),
    (C["so"] - 0.05, (BX + 24.0, -22.0, 8.0), (BX + 24.0, 2.0, 3.0), 40),
    (C["so"], (9.0, -62.0, 26.0), (11.0, 0.0, 27.0), 40, "cut"),
    (C["rivet"] - 0.05, (10.0, -56.0, 26.0), (11.0, 0.0, 27.0), 40),
    (C["rivet"], (RX + 8.0, -30.0, 9.0), (RX, 0.0, 1.8), 40, "cut"),
    (C["hit"], (RX + 5.0, -21.0, 7.0), (RX, 0.0, 2.6), 40),
    (C["now"] - 0.05, (RX + 3.0, -20.0, 6.0), (RX, 0.0, 2.2), 40),
    (C["now"], (RX + 2.0, -31.0, 6.0), (RX, 0.0, 1.8), 40),
    (C["davis3"] - 0.05, (RX + 1.0, -29.0, 5.5), (RX, 0.0, 1.8), 40),
    (C["davis3"], (BX + 14.0, -24.0, 13.0), (BX + 16.0, -8.0, 0.5), 45, "cut"),
    (C["teamed"] - 0.05, (BX + 12.0, -22.0, 12.0), (BX + 15.0, -8.0, 0.5), 45),
    (C["teamed"], (BX - 2.0, -30.0, 22.0), (BX - 14.0, 18.0, 4.0), 40, "cut"),
    (C["they"] - 0.05, (BX - 6.0, -28.0, 20.0), (BX - 15.0, 18.0, 4.0), 40),
    (C["they"], (BX + 8.0, -22.0, 42.0), (BX + 6.0, -2.0, 0.0), 40, "cut"),
    (C["and"] - 0.05, (BX + 7.0, -18.0, 38.0), (BX + 6.0, -2.0, 0.0), 40),
    (C["and"], (13.0, -48.0, 31.0), (12.2, 0.0, 30.0), 45, "cut"),
    (C["do"] - 0.05, (12.5, -36.0, 31.0), (12.2, 0.0, 30.5), 45),
    (C["do"], (5.0, -85.0, 16.0), (7.0, 0.0, 18.0), 40, "cut"),
    (DUR, (10.0, -58.0, 26.0), (11.0, 0.0, 28.0), 40),
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
scene.view_settings.exposure = float(arg("--exposure", "-0.3"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["fell"]) - 5, F(C["heres"]) + 5)
# Mantaflow: not used in this episode (no liquid in the story; see run log)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "rivet_b": (RB.x, -0.3, RB.z), "rivet_a": (RA.x, -0.3, RA.z), "corner": (PB[0] - 0.8, 0.0, PB[1] - 0.4),
    "laststitch": tuple(PIN.at(PIN.L - LAST_S * 0.5)), "seam": tuple(PIN.at(PIN.L * 0.55)), "opening": (8.0, 0.0, 26.3),
    "post": (RX - 1.6, 0.0, -0.3), "cap": (RX - 1.0, 0.0, 4.0), "layers": (RX - 6.0, 0.0, 2.6),
    "tray": (BX - 2.0, 8.0, 1.0), "strap": (STRAP_R[0].location.x, 1.6, 2.6), "bolt": (BX - 18.0, 22.0, 12.0),
    "watchpocket": ((WP_X0 + WP_X1) / 2, 0.36, WP_Z1), "watch": lambda t: (12.2, 0.4, PW([(C["watch"] - 1.0, 44.0), (W_IN + 0.9, 33.2)])(t) + 2.4),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); t = TS[fr - 1]
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_(t) if callable(p_) else p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "answer": RR(*T_ANS), "stake": RR(*T_STAKE), "rip": round(C["rip"], 3), "fall": round(C["fell"], 3),
          "why": RR(*T_WHY), "wrench_in": round(C["tool"] + 0.4, 3), "snap": round(C["snaps"], 3), "tear": round(C["tear"], 3),
          "bench": RR(*T_BENCH), "set": RR(*T_SET), "drop_a": round(C["one"], 3), "drop_b": round(C["corner3"], 3),
          "xs": RR(*T_XS), "post_up": RR(C["post"] - 0.1, C["inside"] + 0.3), "cap_land": round(C["cap"] + 0.35, 3),
          "hit": round(T_HIT, 3), "pat": RR(*T_PAT), "sheet_in": round(C["patent2"] + 0.35, 3), "watch": RR(*T_WATCH),
          "watch_in": round(W_IN + 0.9, 3), "cta": RR(*T_CTA)}
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
