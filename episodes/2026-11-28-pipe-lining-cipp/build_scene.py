# Pipe lining / CIPP (3d-35): how plumbers fix a drain under a house without digging. Claim-first hook ("They fixed this broken pipe
# without breaking the floor.") on a cross-section of a house on a slab with the cracked cast-iron drain below -> the finished liner
# inside the old pipe (story trick) -> stake what-if: jackhammered floor (rigid body slab chunks + dust) -> the cleanout in the yard
# opens -> inspection camera crawls in (cracks, roots), chain cutter clears it (debris particles) -> felt tube soaked in resin ->
# INVERSION: the liner turns inside out down the pipe (rolling lip, inner tail, air arrows), pressed against the walls, follows the
# bends -> cure: hot water (Mantaflow fill set up, laptop bake), steam, UV light train -> hardens, seamless, no joints -> the old pipe
# crumbles (rigid body shards), the liner stands on its own -> the side branch is sealed over, a robot cutter reopens it (animated
# boolean) -> pull out, 50 years -> London 1971 egg-shaped brick sewer with a liner -> CTA push-in.
# Illustrative, 1 unit = 10 cm: generic slab-on-grade house, 4-inch cast-iron drain (wall and liner thickness exaggerated),
# generic equipment. No logos, no people.
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
random.seed(35)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("they", "They"), ("fixed", "fixed"), ("broken", "broken"), ("without", "without"), ("floor", "floor."), ("new", "new"),
        ("built", "built"), ("inside", "inside"), ("normally", "Normally,"), ("cracked", "cracked"), ("jackhammers", "jackhammers,"),
        ("trench", "trench"), ("giant", "giant"), ("mess", "mess."), ("instead", "Instead,"), ("opens", "opens"), ("one", "one"), ("cleanout", "cleanout."),
        ("first", "First,"), ("camera", "camera"), ("crawls", "crawls"), ("cracks", "cracks"), ("roots", "roots,"), ("old", "old"),
        ("scrubbed", "scrubbed"), ("next", "Next"), ("liner", "liner:"), ("soft", "soft"), ("felt", "felt"), ("soaked", "soaked"),
        ("resin", "resin"), ("sponge", "sponge."), ("heres", "Here's"), ("trick", "trick."), ("push", "push"), ("inside2", "inside"),
        ("air", "Air"), ("pressure", "pressure"), ("unrolls", "unrolls"), ("sock", "sock"), ("pressing", "pressing"), ("wet", "wet"),
        ("walls", "walls."), ("because", "Because"), ("soft2", "soft,"), ("follows", "follows"), ("bend", "bend."), ("then", "Then"),
        ("cure", "cure"), ("hot", "hot"), ("steam", "steam,"), ("ultraviolet", "ultraviolet"), ("light", "light."), ("hardens", "hardens"),
        ("seamless", "seamless"), ("joints", "joints"), ("roots2", "roots"), ("its", "It's"), ("stand", "stand"), ("own", "own,"),
        ("crumbles", "crumbles"), ("but", "But"), ("liner2", "liner"), ("sealed", "sealed"), ("side", "side"), ("branch", "branch."),
        ("so", "So"), ("robot", "robot"), ("camera2", "camera"), ("rolls", "rolls"), ("cuts", "cuts"), ("opening", "opening"),
        ("out", "out."), ("these", "These"), ("designed", "designed"), ("fifty", "fifty"), ("years", "years."), ("very", "very"),
        ("first2", "first"), ("london", "London"), ("sewer", "sewer"), ("nineteen", "nineteen"), ("still", "still"),
        ("service", "service"), ("would", "Would"), ("robot2", "robot"), ("pipes", "pipes"), ("house", "house?"), ("tell", "Tell"),
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
CL = coll("PipeLining")
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


# ================= timing =================
T_HOOK = (0.0, C["new"] - 0.2); T_STORY = (C["new"] - 0.2, C["normally"]); T_STAKE = (C["normally"], C["instead"])
T_CLEAN = (C["instead"], C["first"]); T_CRAWL = (C["first"], C["next"]); T_FELT = (C["next"], C["heres"])
T_INV = (C["heres"], C["because"]); T_BEND = (C["because"], C["then"]); T_CURE = (C["then"], C["hardens"] - 0.5)
T_HARD = (C["hardens"] - 0.5, C["its"]); T_OWN = (C["its"], C["but"]); T_BRANCH = (C["but"], C["these"])
T_FIFTY = (C["these"], C["very"] - 0.15); T_LONDON = (C["very"] - 0.15, C["would"]); T_CTA = (C["would"], DUR)
LX = 3000.0          # London 1971 set, far away (camera clip 3 km)
Y = Vector((0, 1, 0))
ZP = -7.0            # pipe axis
R_IN, R_OUT = 0.50, 0.60          # cast iron (exaggerated wall)
R_LO, R_LI = 0.495, 0.43          # liner outer / inner
R_TAIL = 0.26
XB = -15.0           # side branch (toilet)

# ================= path + tube builders (path in the XZ plane, cut at y = 0, keep y >= 0) =================
def fillet_path(corners, R, n=12, step=1.5):
    c = [Vector(p) for p in corners]; pts = [c[0]]
    for i in range(1, len(c) - 1):
        a, b, d = c[i - 1], c[i], c[i + 1]
        d1, d2 = (b - a).normalized(), (d - b).normalized()
        p0, p1 = b - d1 * R, b + d2 * R
        last = pts[-1]; L_ = (p0 - last).length; k = max(1, int(L_ / step))
        pts += [last.lerp(p0, j / k) for j in range(1, k + 1)]
        for j in range(1, n + 1):
            u = j / n; pts.append((1 - u) ** 2 * p0 + 2 * (1 - u) * u * b + u * u * p1)
    last = pts[-1]; L_ = (c[-1] - last).length; k = max(1, int(L_ / step))
    pts += [last.lerp(c[-1], j / k) for j in range(1, k + 1)]
    return pts
def arclen(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + (b - a).length)
    return s
def subpath(pts, s0, s1):
    P = Path(pts); s = arclen(pts)
    return [P.at(s0)] + [p for p, si in zip(pts, s) if s0 < si < s1] + [P.at(s1)]
def frame_at(pts, i):
    n = len(pts); t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
    return t, Y.cross(t).normalized()
def pipe_wall(name, pts, r_in, r_out, m_, a0=0.0, a1=math.pi, seg=20, caps=True, link=True, s_off=0.0, s_tot=None):
    """Half tube (angles a0..a1 around the axis, y >= 0) with wall thickness; r_in = 0 -> solid half cylinder.
    UV.x = arc length / s_tot (for the liner reveal masks)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    s = arclen(pts); tot = s_tot or s[-1]
    A = [a0 + (a1 - a0) * k / seg for k in range(seg + 1)]
    ring_o, ring_i, us = [], [], []
    for i, p in enumerate(pts):
        t, v = frame_at(pts, i)
        ring_o.append([bm.verts.new(p + r_out * (math.cos(a) * v + math.sin(a) * Y)) for a in A])
        ring_i.append([bm.verts.new(p + r_in * (math.cos(a) * v + math.sin(a) * Y)) for a in A] if r_in > 0 else
                      [bm.verts.new(p + r_out * math.cos(a0) * v), bm.verts.new(p + r_out * math.cos(a1) * v)])
        us.append((s_off + s[i]) / tot)
    faces = []
    def F4(vs, u):
        try:
            f = bm.faces.new(vs)
            for lp, uu in zip(f.loops, u): lp[uvl].uv = (uu, 0.5)
            faces.append(f)
        except ValueError: pass
    for i in range(len(pts) - 1):
        u0, u1 = us[i], us[i + 1]
        for k in range(seg):
            F4([ring_o[i][k], ring_o[i][k + 1], ring_o[i + 1][k + 1], ring_o[i + 1][k]], [u0, u0, u1, u1])
            if r_in > 0: F4([ring_i[i][k + 1], ring_i[i][k], ring_i[i + 1][k], ring_i[i + 1][k + 1]], [u0, u0, u1, u1])
        if r_in > 0:
            F4([ring_i[i][0], ring_o[i][0], ring_o[i + 1][0], ring_i[i + 1][0]], [u0, u0, u1, u1])
            F4([ring_o[i][seg], ring_i[i][seg], ring_i[i + 1][seg], ring_o[i + 1][seg]], [u0, u0, u1, u1])
        else:
            F4([ring_i[i][0], ring_i[i][1], ring_i[i + 1][1], ring_i[i + 1][0]], [u0, u0, u1, u1])
    if caps:
        for i in (0, len(pts) - 1):
            u = us[i]
            if r_in > 0:
                for k in range(seg): F4([ring_o[i][k], ring_o[i][k + 1], ring_i[i][k + 1], ring_i[i][k]], [u] * 4)
            else:
                F4(ring_o[i] + [], [u] * len(ring_o[i]))
    o = mesh_obj(name, bm, m_, link=link)
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(50))
    except Exception: pass
    return o
def half_torus(name, R, r, m_, segU=28, segV=14):
    """torus around local Z, only local y >= 0 kept (major angle 0..pi)."""
    bm = bmesh.new(); rings = []
    for i in range(segU + 1):
        a = math.pi * i / segU; c = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c * (R + r * math.cos(2 * math.pi * j / segV)) + Vector((0, 0, r * math.sin(2 * math.pi * j / segV)))) for j in range(segV)])
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(segV): bm.faces.new([r0[j], r0[(j + 1) % segV], r1[(j + 1) % segV], r1[j]])
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def orient(t):
    """rotation with local Z -> tangent t (in XZ), local Y -> world Y."""
    t = Vector(t).normalized(); v = Y.cross(t).normalized()
    return Matrix((v, Y, t)).transposed().to_euler()
def bake_rot(o, fn):
    vals = [fn(t) for t in TS]
    for ax in range(3): bake(o, "rotation_euler", ax, [v[ax] for v in vals])

# ================= materials =================
M_SOIL = strata("Soil", [(0.09, 0.055, 0.03), (0.17, 0.10, 0.05), (0.12, 0.075, 0.04), (0.21, 0.13, 0.07)], scale=0.06, bump=0.5)
M_CLAY = strata("ClaySection", [(0.38, 0.22, 0.12), (0.46, 0.29, 0.16), (0.40, 0.25, 0.14), (0.52, 0.34, 0.19)], scale=0.05)
def concrete(name, rgb, scale=0.6):
    m, b = mat(name, rgb, rough=0.85, noise=scale); return m, b
M_CONC, B_CONC = concrete("Slab", (0.52, 0.51, 0.48), 0.8)
M_FLOOR = tiles("FloorTile", (0.82, 0.80, 0.76), (0.76, 0.74, 0.70), 0.18, plane="XY")
M_WALL, _ = mat("Wall", (0.86, 0.84, 0.80), rough=0.8)
M_WALLCUT, _ = mat("WallCut", (0.62, 0.58, 0.52), rough=0.9, noise=2.0)
M_CAB, _ = mat("Cabinet", (0.20, 0.30, 0.38), rough=0.5)
M_COUNTER, _ = mat("Counter", (0.88, 0.88, 0.86), rough=0.25)
M_WOOD, _ = mat("Wood", (0.45, 0.30, 0.18), rough=0.6, noise=3.0)
M_CERAMIC, _ = mat("Ceramic", (0.93, 0.94, 0.95), rough=0.15)
M_STEEL, _ = mat("Steel", (0.70, 0.71, 0.73), rough=0.3, metallic=0.9)
M_DARKM, _ = mat("DarkMetal", (0.08, 0.08, 0.09), rough=0.4, metallic=0.6)
M_YELLOW, _ = mat("EquipYellow", (0.85, 0.62, 0.08), rough=0.45)
M_HOSE, _ = mat("Hose", (0.05, 0.05, 0.05), rough=0.6)
M_GRASS, _ = mat("Grass", (0.14, 0.26, 0.07), rough=0.9, noise=0.4)
M_TUFT, _ = mat("Tuft", (0.18, 0.34, 0.08), rough=0.9)
M_PEBBLE, _ = mat("Pebble", (0.45, 0.43, 0.40), rough=0.8, noise=2.0)
M_ROOT, B_ROOT = mat("Root", (0.30, 0.20, 0.11), rough=0.8, noise=4.0, emit_rgb=(1.0, 0.18, 0.08))
M_BRICK = tiles("Brick", (0.48, 0.20, 0.12), (0.40, 0.16, 0.10), 0.5, plane="XZ")
M_BRICKY = tiles("BrickY", (0.48, 0.20, 0.12), (0.40, 0.16, 0.10), 0.5, plane="XY")
M_DIRT, _ = mat("Dirt", (0.30, 0.20, 0.11), rough=0.95, noise=1.0)
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 6.0)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 6.0)
M_REDG, B_REDG = emit_mat("RedGlow", (1.0, 0.18, 0.08), 0.0)
M_WHITEG, B_WHITEG = emit_mat("WhiteGlow", (1.0, 1.0, 1.0), 8.0)
M_VIOLETG, B_VIOLETG = emit_mat("UVGlow", (0.55, 0.25, 1.0), 12.0)
M_WINDOW, _ = emit_mat("Window", (0.85, 0.92, 1.0), 3.0)
M_WATER, B_WATER, _V = water_sec("SewerWater", vol_rgb=(0.20, 0.30, 0.25), dens=0.2)
M_INV, INV_FAC = ghost("Invisible", (1, 1, 1))
INV_FAC.default_value = 0.0

def cast_iron(name, hole=True):
    m, b = mat(name, (0.20, 0.12, 0.08), rough=0.75, metallic=0.35, noise=3.0, emit_rgb=(1.0, 0.18, 0.08))
    nt = m.node_tree; N, L = nt.nodes, nt.links
    # rust mottling
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    L.new(mix_rgb(nt, nz.outputs["Fac"], (0.12, 0.09, 0.08), (0.36, 0.17, 0.07)), b.inputs["Base Color"])
    if hole:   # permanent opening under the side branch (world position, top half only)
        out = next(x for x in N if x.type == "OUTPUT_MATERIAL"); src = out.inputs["Surface"].links[0].from_socket
        geo = N.new("ShaderNodeNewGeometry"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sp.inputs[0])
        dx = MATH(nt, "SUBTRACT", sp.outputs[0], XB); d2 = MATH(nt, "ADD", MATH(nt, "MULTIPLY", dx, dx), MATH(nt, "MULTIPLY", sp.outputs[1], sp.outputs[1]))
        inside = MATH(nt, "MULTIPLY", MATH(nt, "LESS_THAN", d2, R_IN * R_IN), MATH(nt, "GREATER_THAN", sp.outputs[2], ZP + 0.2))
        tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
        L.new(inside, mx.inputs[0]); L.new(src, mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m, b
M_IRON, B_IRON = cast_iron("CastIron")
M_HUB, B_HUB = cast_iron("CastIronHub", hole=False)

LINER_VALUES = []
def liner_mat(name, tail=False):
    """Liner: visible where TS < UV.x < FRONT; hole + red seal over the side branch (world position); colour/emission keyed."""
    m, b = mat(name, (0.75, 0.45, 0.12), rough=0.35, emit_rgb=(0.98, 0.74, 0.27))
    nt = m.node_tree; N, L = nt.nodes, nt.links
    out = next(x for x in N if x.type == "OUTPUT_MATERIAL")
    uv = N.new("ShaderNodeUVMap"); uv.uv_map = "UVMap"; sp = N.new("ShaderNodeSeparateXYZ"); L.new(uv.outputs["UV"], sp.inputs[0])
    fr = N.new("ShaderNodeValue"); fr.name = "FRONT"; ts = N.new("ShaderNodeValue"); ts.name = "TS"
    hole = N.new("ShaderNodeValue"); hole.name = "HOLE"; seal = N.new("ShaderNodeValue"); seal.name = "SEAL"
    vis = MATH(nt, "MULTIPLY", MATH(nt, "LESS_THAN", sp.outputs[0], fr.outputs[0]), MATH(nt, "GREATER_THAN", sp.outputs[0], ts.outputs[0]))
    geo = N.new("ShaderNodeNewGeometry"); gp = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], gp.inputs[0])
    dx = MATH(nt, "SUBTRACT", gp.outputs[0], XB); d2 = MATH(nt, "ADD", MATH(nt, "MULTIPLY", dx, dx), MATH(nt, "MULTIPLY", gp.outputs[1], gp.outputs[1]))
    top = MATH(nt, "GREATER_THAN", gp.outputs[2], ZP + 0.2)
    hr2 = MATH(nt, "MULTIPLY", hole.outputs[0], hole.outputs[0])
    inhole = MATH(nt, "MULTIPLY", MATH(nt, "LESS_THAN", d2, hr2), top)
    vis = MATH(nt, "MULTIPLY", vis, MATH(nt, "SUBTRACT", 1.0, inhole))
    inseal = MATH(nt, "MULTIPLY", MATH(nt, "LESS_THAN", d2, (R_IN + 0.04) ** 2), top)
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.16, 0.06, 1)
    L.new(MATH(nt, "MULTIPLY", inseal, seal.outputs[0]), em.inputs["Strength"])
    ad = N.new("ShaderNodeAddShader"); L.new(b.outputs[0], ad.inputs[0]); L.new(em.outputs[0], ad.inputs[1])
    tr = N.new("ShaderNodeBsdfTransparent"); mx = N.new("ShaderNodeMixShader")
    L.new(vis, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(ad.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    LINER_VALUES.append((nt, tail))
    return m, b
M_LINER, B_LINER = liner_mat("Liner")
M_TAIL, B_TAIL = liner_mat("LinerTail", tail=True)
M_HOTW, B_HOTW = liner_mat("HotWater")       # same reveal along the pipe, used for the hot-water fill

# ================= ground: soil section, slab, house =================
MAIN_C = [(55.0, 0, 2.2), (55.0, 0, ZP), (-30.0, 0, ZP), (-30.0, 0, 1.2)]
OLD = fillet_path(MAIN_C, 2.0)
LIN_C = [(55.0, 0, 2.2), (55.0, 0, ZP), (-30.0, 0, ZP), (-30.0, 0, -2.5)]
LIN = fillet_path(LIN_C, 2.0)
LP = Path(LIN); LL = LP.L
def s_at_x(x, pts=LIN):
    s = arclen(pts); best = None
    for p, si in zip(pts, s):
        if abs(p.z - ZP) < 0.01 and (best is None or abs(p.x - x) < abs(best[0] - x)): best = (p.x, si)
    return best[1] + (best[0] - x)
SOIL = box("Soil", -70, 80, 0, 60, -70, 0, M_SOIL)
GRASS = box("Yard", 42, 80, 0, 60, 0, 0.25, M_GRASS)
SLAB = box("Slab", -42, 42, 0, 52, 0, 1.0, M_CONC)
FLOOR = box("FloorTiles", -40, 40, 0, 50, 1.0, 1.15, M_FLOOR)
CUT_MAIN = cutter("CutMain", OLD, [R_OUT + 0.03] * len(OLD))
STREET = [Vector((53.0 + i * 1.5, 0, ZP)) for i in range(19)]
CUT_STREET = cutter("CutStreet", STREET, [R_OUT + 0.03] * len(STREET))
BRP = [Vector((XB, 0, ZP + 0.3)), Vector((XB, 0, 1.3))]
CUT_BR = cutter("CutBranch", BRP, [R_OUT + 0.03] * 2)
HUBX = (40.0, 25.0, 10.0, -5.5, -22.0)
bm = bmesh.new()
for hx in HUBX: add_cyl(bm, 0.87, 1.44, "X", (hx, 0, ZP), 28)
CUT_HUB = mesh_obj("CutHubs", bm, None); CUT_HUB.hide_render = True; CUT_HUB.display_type = "WIRE"
for tgt in (SOIL, GRASS, SLAB, FLOOR):
    for cu in (CUT_MAIN, CUT_STREET, CUT_BR, CUT_HUB): boolean(tgt, cu, "Cut" + cu.name)
# house walls (cut at y = 0), rooms: bathroom (x < -5) + kitchen
box("WallBack", -42, 42, 50, 52, 1.0, 27.0, M_WALL)
for x0, x1 in ((-42, -40), (40, 42)): box("WallSide", x0, x1, 0, 52, 1.0, 27.0, M_WALLCUT)
box("WallInner", -5.6, -5.0, 0, 50, 1.15, 27.0, M_WALLCUT)
box("Window", 8, 24, 49.8, 50.0, 12, 21, M_WINDOW)
box("Mirror", -33, -27, 49.8, 50.0, 12, 19, M_STEEL)
box("Vanity", -35, -25, 44, 50, 1.15, 8.6, M_CAB); box("VanityTop", -35.5, -24.5, 43.6, 50, 8.6, 9.1, M_COUNTER)
box("Cabinets", 0, 30, 44, 50, 1.15, 8.6, M_CAB); box("CounterTop", -0.5, 30.5, 43.4, 50, 8.6, 9.1, M_COUNTER)
box("Uppers", 0, 18, 47, 50, 15, 21.5, M_CAB)
box("Fridge", 31.5, 39, 43, 50, 1.15, 18.5, M_STEEL)
box("TableTop", 8, 22, 18, 30, 7.2, 7.6, M_WOOD)
for lx, ly in ((8.6, 18.6), (21.4, 18.6), (8.6, 29.4), (21.4, 29.4)): box("TableLeg", lx - 0.3, lx + 0.3, ly - 0.3, ly + 0.3, 1.15, 7.2, M_WOOD)
box("ToiletBase", XB - 1.4, XB + 1.4, 0.6, 6.0, 1.15, 4.2, M_CERAMIC)
cyl("ToiletBowl", 2.0, 0.8, "Z", (XB, 3.2, 4.4), M_CERAMIC, seg=32)
box("ToiletTank", XB - 2.4, XB + 2.4, 6.0, 8.4, 4.2, 9.6, M_CERAMIC)
# gold outline: the floor stays untouched (hook)
FLOOR_LINE = poly_obj("FloorLine", [Vector((-40, -0.1, 1.2)), Vector((40, -0.1, 1.2))], 0.18, M_GOLDG, seg=6)
windows(FLOOR_LINE, [(C["floor"] - 0.1, C["new"] - 0.2)])
# yard: grass tufts + pebbles (Geometry Nodes scatter)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.04, radius2=0.0, depth=0.32)
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, 0.16)); TUFT = mesh_obj("Tuft", bm, M_TUFT)
fx.scatter(GRASS, TUFT, density=5.0, scale_min=0.5, scale_max=1.4, seed=5)
PEB = obj_from("Pebble", sphere_mesh("PebbleM", 0.35, 1), M_PEBBLE)
GRAV = box("GravelStrip", 42, 46, 0, 60, 0.25, 0.3, M_PEBBLE)
fx.scatter(GRAV, PEB, density=0.8, scale_min=0.4, scale_max=1.1, seed=7)

# ================= the old drain: cast iron, hubs, cracks, roots, branch, street run =================
S8, SM4 = s_at_x(8.0, OLD), s_at_x(-4.0, OLD)
OLD_A = pipe_wall("OldPipeA", subpath(OLD, 0, S8), R_IN, R_OUT, M_IRON, seg=22)
OLD_C = pipe_wall("OldPipeC", subpath(OLD, SM4, Path(OLD).L), R_IN, R_OUT, M_IRON, seg=22)
pipe_wall("OldStreet", STREET, R_IN, R_OUT, M_IRON, seg=22)
pipe_wall("OldBranch", BRP, R_IN, R_OUT, M_IRON, seg=22)
for hx in HUBX:
    pipe_wall(f"Hub{hx:.0f}", [Vector((hx + 0.7, 0, ZP)), Vector((hx - 0.7, 0, ZP))], R_OUT - 0.02, 0.84, M_HUB, seg=22)
glow(B_HUB, [(0, 0.0)] + pulse(C["joints"], 4.0, hold=0.7))
# shards: the stretch that crumbles (x 8 .. -4), 3 along x x 3 around
SHARDS = []
for i, (x0, x1) in enumerate(((8.0, 4.0), (4.0, 0.0), (0.0, -4.0))):
    for j in range(3):
        a0, a1 = math.pi * j / 3, math.pi * (j + 1) / 3
        o = pipe_wall(f"Shard{i}{j}", [Vector((x0, 0, ZP)), Vector((x1, 0, ZP))], R_IN, R_OUT, M_IRON, a0=a0, a1=a1, seg=8)
        SHARDS.append(o)
# cracks (red glow on the inner back wall)
def crack_pts(xc, a_from, a_to, r, n=7, seed=0):
    rnd = random.Random(seed); pts = []
    for k in range(n + 1):
        a = a_from + (a_to - a_from) * k / n; x = xc + rnd.uniform(-0.35, 0.35)
        pts.append(Vector((x, r * math.sin(a), ZP + r * math.cos(a))))
    return pts
CRACKS = []
for k, xc in enumerate((32.0, 18.0, 2.0)):
    bm = bmesh.new()
    add_poly(bm, crack_pts(xc, -2.6, 2.6, R_IN - 0.015, 9, k), 0.035, 6)
    add_poly(bm, crack_pts(xc + 0.5, 0.3, 1.6, R_IN - 0.015, 5, k + 9), 0.03, 6)
    CRACKS.append(mesh_obj(f"Crack{k}", bm, M_REDG))
glow(B_REDG, [(0, 3.0), (C["new"] - 0.25, 3.0), (C["new"] - 0.2, 0.0), (C["normally"], 0.0), (C["normally"] + 0.02, 3.0),
              (C["instead"], 3.0), (C["instead"] + 0.02, 1.2), (C["cracks"] - 0.02, 1.2), (C["cracks"] + 0.2, 6.0), (C["roots"] + 0.6, 6.0),
              (C["next"], 2.0), (C["push"], 2.0), (C["air"], 0.0)])
for c_ in CRACKS[:2]: windows(c_, [(0, C["new"] - 0.2), (C["normally"], C["pressing"])])
windows(CRACKS[2], [(0, C["new"] - 0.2), (C["normally"], C["pressing"])])
# roots through the hub at x = 10: drawn on the soil face + a tangle hanging inside the pipe
rnd = random.Random(3)
bm = bmesh.new()
for k in range(5):
    p = Vector((10.0 + rnd.uniform(-5, 5), -0.05, -0.6)); pts = [p]
    for j in range(8):
        p = p.lerp(Vector((10.0 + rnd.uniform(-0.5, 0.5), -0.05, ZP + 0.85)), 0.32) + Vector((rnd.uniform(-0.5, 0.5), 0, 0)); pts.append(p.copy())
    add_poly(bm, pts, 0.09 - 0.012 * k, 6)
ROOTS_OUT = mesh_obj("RootsOut", bm, M_ROOT)
bm = bmesh.new()
for k in range(16):
    p = Vector((10.0 + rnd.uniform(-0.5, 0.5), rnd.uniform(0.05, 0.42), ZP + R_IN - 0.05)); pts = [p]
    for j in range(6):
        p = p + Vector((rnd.uniform(-0.18, 0.18), rnd.uniform(-0.05, 0.05), -rnd.uniform(0.05, 0.16)))
        p.z = max(p.z, ZP - R_IN + 0.06); pts.append(p.copy())
    add_poly(bm, pts, 0.025, 5)
ROOTS_IN = mesh_obj("RootsIn", bm, M_ROOT)
windows(ROOTS_IN, [(0, C["scrubbed"] + 0.15)])
glow(B_ROOT, [(0, 0.0)] + pulse(C["roots"], 0.35, hold=0.6) + pulse(C["roots2"], 0.35, hold=0.6))

# ================= cleanout in the yard =================
CAP = cyl("CleanoutCap", 0.78, 0.5, "Z", (0, 0, 0), M_DARKM, seg=24)
bake_loc(CAP, lambda t: (55.0 + 1.6 * ease((t - C["opens"]) / 0.5), 0.0, 2.45 + 1.2 * math.sin(math.pi * lin((t - C["opens"]) / 0.5))))
bake_rot(CAP, lambda t: (0.0, -1.2 * ease((t - C["opens"]) / 0.5), 0.0))
windows(CAP, [(0, C["opens"] + 1.4)])
CO_RING = pipe_wall("CleanoutCollar", [Vector((55, 0, 2.4)), Vector((55, 0, 1.6))], R_OUT, 0.8, M_DARKM, seg=22)

# ================= inspection camera + chain cutter (B5) =================
def crawler_x(t): return PW([(C["first"], 40.0), (C["cracks"], 31.0), (C["roots"] - 0.1, 12.0), (C["old"], 11.2)])(t)
def cutter_x(t): return PW([(C["old"] - 0.1, 16.0), (C["scrubbed"], 10.0), (C["next"], 2.0)])(t)
CRAWL = empty("Crawler")
bm = bmesh.new(); add_cyl(bm, 0.22, 1.0, "X", (0.5, 0, 0), 20); CRB = mesh_obj("CrawlerBody", bm, M_STEEL, parent=CRAWL)
bm = bmesh.new(); add_cyl(bm, 0.16, 0.05, "X", (-0.02, 0, 0), 20); mesh_obj("CrawlerLens", bm, M_WHITEG, parent=CRAWL)
bm = bmesh.new(); add_box(bm, 1.0, 26.0, -0.03, 0.03, -0.03, 0.03); CABLE = mesh_obj("CrawlerCable", bm, M_HOSE, parent=CRAWL)
spot_d = bpy.data.lights.new("CrawlerLamp", "SPOT"); spot_d.energy = 25.0; spot_d.spot_size = math.radians(70); spot_d.color = (1.0, 0.95, 0.85)
spot = bpy.data.objects.new("CrawlerLamp", spot_d); CL.objects.link(spot); par(spot, CRAWL); spot.location = (-0.1, 0, 0); spot.rotation_euler = (0, math.radians(-90), 0)
bake_loc(CRAWL, lambda t: (crawler_x(t), 0.1, ZP - R_IN + 0.24))
windows(CRAWL, [(C["first"], C["next"])])
CUTR = empty("ChainCutter")
bm = bmesh.new(); add_cyl(bm, 0.07, 0.6, "X", (0.3, 0, 0), 10); add_cyl(bm, 0.12, 0.25, "X", (0.0, 0, 0), 12)
for k in range(8):
    a = 2 * math.pi * k / 8; vs_ = add_box(bm, -0.06, 0.06, -0.03, 0.03, 0.12, R_IN - 0.06)
    bmesh.ops.rotate(bm, verts=vs_, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "X"))
CUTHEAD = mesh_obj("CutterHead", bm, M_STEEL, parent=CUTR)
bake_fn(CUTHEAD, "rotation_euler", 0, lambda t: 40.0 * t)
bm = bmesh.new(); add_box(bm, 0.6, 26.0, -0.035, 0.035, -0.035, 0.035); mesh_obj("CutterCable", bm, M_HOSE, parent=CUTR)
bake_loc(CUTR, lambda t: (cutter_x(t), 0.12, ZP))
windows(CUTR, [(C["old"] - 0.1, C["next"])])
DEB = box("RootDebrisEmitter", 9.4, 10.6, 0.05, 0.4, ZP - 0.1, ZP + 0.3, M_INV)
fx.particles(DEB, "mud", F(C["scrubbed"] - 0.1), F(C["scrubbed"] + 0.9), count=260)

# ================= felt tube soaked in resin (B6, yard) =================
def felt_mat():
    m, b = mat("Felt", (0.86, 0.85, 0.80), rough=0.95, noise=12.0, emit_rgb=(0.98, 0.74, 0.27))
    nt = m.node_tree; N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    rv = N.new("ShaderNodeValue"); rv.name = "RESIN"
    keyval(rv.outputs[0], [(0, -0.05), (C["soaked"] - 0.01, -0.05), (C["sponge"] + 0.8, 1.05)])
    wet = MATH(nt, "LESS_THAN", sp.outputs[0], rv.outputs[0])
    L.new(mix_rgb(nt, wet, (0.86, 0.85, 0.80), (0.72, 0.42, 0.10)), b.inputs["Base Color"])
    L.new(MATH(nt, "ADD", MATH(nt, "MULTIPLY", wet, -0.6), 0.95), b.inputs["Roughness"])
    L.new(MATH(nt, "MULTIPLY", wet, 0.6), b.inputs["Emission Strength"])
    return m
M_FELT = felt_mat()
FELT = cyl("FeltTube", 1.0, 20.0, "X", (68.0, 22.0, 1.0), M_FELT, seg=32); FELT.scale = (1, 1, 0.42); FELT.location.z = -0.15
ROLLER = cyl("ResinRoller", 0.55, 3.0, "Y", (0, 0, 0), M_YELLOW, seg=24)
bake_loc(ROLLER, lambda t: (58.0 + 20.0 * lin((t - C["soaked"]) / (C["sponge"] + 0.8 - C["soaked"])), 22.0, 1.05))
bake_fn(ROLLER, "rotation_euler", 1, lambda t: 36.0 * lin((t - C["soaked"]) / (C["sponge"] + 0.8 - C["soaked"])))
windows(FELT, [T_FELT]); windows(ROLLER, [T_FELT])

# ================= liner: wall (inverted), tail (inside out, travelling), rolling lip, air arrows =================
S_B1 = s_at_x(53.0); S_X22 = s_at_x(-22.0); S_B2 = s_at_x(-28.5)
FRONT_KEYS = [(C["push"], 0.0), (C["air"], S_B1), (C["pressing"], s_at_x(14.0)), (C["because"], S_X22), (C["bend"], S_B2 + 2.5), (C["bend"] + 0.7, LL)]
FRONT_S = PW(FRONT_KEYS)
def front_u(t):
    if t < T_STORY[0]: return 0.0
    if t < T_STORY[1]: return 1.01
    if t < C["push"]: return 0.0
    if t > C["bend"] + 0.7: return 1.01
    return FRONT_S(t) / LL
def ts_u(t):
    if C["push"] <= t <= C["bend"] + 0.7: return max(-0.01, 2 * front_u(t) - 1.0)
    return 1.02
LINER = pipe_wall("LinerWall", LIN, R_LI, R_LO, M_LINER, seg=24)
TAIL = pipe_wall("LinerTail", LIN, 0.0, R_TAIL, M_TAIL, seg=16)
for nt, tail in LINER_VALUES:
    bake_scalar(nt, 'nodes["FRONT"].outputs[0].default_value', [front_u(t) for t in TS])
    bake_scalar(nt, 'nodes["TS"].outputs[0].default_value', [ts_u(t) if tail else -0.01 for t in TS])
    bake_scalar(nt, 'nodes["HOLE"].outputs[0].default_value',
                [0.0 if t < C["cuts"] else 0.04 + (R_IN - 0.04) * ease((t - C["cuts"]) / (C["out"] + 0.3 - C["cuts"])) for t in TS])
    bake_scalar(nt, 'nodes["SEAL"].outputs[0].default_value',
                [6.0 if C["sealed"] <= t < C["cuts"] + 0.4 else 0.0 for t in TS])
# hot water fill uses the same reveal, but its own FRONT (fills fast on "hot", drains on "steam")
hw_nt = M_HOTW.node_tree
bake_scalar(hw_nt, 'nodes["FRONT"].outputs[0].default_value', [lin((t - C["hot"] + 0.1) / 0.8) * 1.01 if t < C["steam"] else -0.1 for t in TS])
bake_scalar(hw_nt, 'nodes["HOLE"].outputs[0].default_value', [0.0] * len(TS))
bake_scalar(hw_nt, 'nodes["SEAL"].outputs[0].default_value', [0.0] * len(TS))
HOTW = pipe_wall("HotWater", LIN, 0.0, R_LI - 0.02, M_HOTW, seg=16)
B_HOTW.inputs["Base Color"].default_value = (0.9, 0.35, 0.1, 1); B_HOTW.inputs["Emission Color"].default_value = (1.0, 0.36, 0.08, 1)
B_HOTW.inputs["Emission Strength"].default_value = 2.5; B_HOTW.inputs["Alpha"].default_value = 0.85
windows(HOTW, [(C["hot"] - 0.1, C["steam"])])
# liner colour states: wet resin -> pressed (gold) -> hot water (orange) -> steam (white) -> UV (violet) -> cured (pale)
CURED, WET = (0.42, 0.56, 0.62), (0.62, 0.34, 0.07)
def col_keys(bsdf, keys):
    for t_, base, ecol, es in keys:
        for sock, v in (("Base Color", (*base, 1)), ("Emission Color", (*ecol, 1))):
            bsdf.inputs[sock].default_value = v; bsdf.inputs[sock].keyframe_insert("default_value", frame=F(t_))
        bsdf.inputs["Emission Strength"].default_value = es; bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=F(t_))
GOLD, CYAN, ORANGE, STEAMC, VIOLET = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.36, 0.08), (1.0, 0.92, 0.85), (0.55, 0.25, 1.0)
for bs in (B_LINER, B_TAIL):
    col_keys(bs, [(0, CURED, CYAN, 0.3), (C["normally"] - 0.02, CURED, CYAN, 0.3), (C["normally"], WET, GOLD, 0.5),
                  (C["pressing"] - 0.02, WET, GOLD, 0.5), (C["pressing"] + 0.3, WET, GOLD, 1.2), (C["walls"] + 0.5, WET, GOLD, 1.2),
                  (C["because"] + 0.3, WET, GOLD, 0.6), (C["hot"] - 0.02, WET, GOLD, 0.6), (C["hot"] + 0.2, (0.8, 0.32, 0.1), ORANGE, 2.0),
                  (C["steam"] - 0.02, (0.8, 0.32, 0.1), ORANGE, 2.0), (C["steam"] + 0.2, (0.85, 0.75, 0.6), STEAMC, 1.2),
                  (C["ultraviolet"] - 0.02, (0.85, 0.75, 0.6), STEAMC, 1.2), (C["ultraviolet"] + 0.2, (0.6, 0.5, 0.8), VIOLET, 3.0),
                  (C["hardens"] - 0.02, (0.6, 0.5, 0.8), VIOLET, 3.0), (C["hardens"] + 0.4, CURED, CYAN, 0.3),
                  (C["seamless"] - 0.02, CURED, CYAN, 0.3), (C["seamless"] + 0.2, CURED, CYAN, 1.4), (C["joints"] + 0.3, CURED, CYAN, 0.3),
                  (C["stand"] - 0.02, CURED, CYAN, 0.3), (C["stand"] + 0.2, CURED, CYAN, 1.2), (C["crumbles"] + 1.2, CURED, CYAN, 0.4)])
LIP = half_torus("LinerLip", (R_LO + R_TAIL) / 2, (R_LO - R_TAIL) / 2, M_GOLDG)
B_GOLDG.inputs["Emission Strength"].default_value = 5.0
bake_loc(LIP, lambda t: tuple(LP.at(FRONT_S(t))))
def tangent_at(s):
    return (LP.at(min(LL, s + 0.3)) - LP.at(max(0.0, s - 0.3))).normalized()
bake_rot(LIP, lambda t: tuple(orient(tangent_at(FRONT_S(t)))))
windows(LIP, [(C["push"], C["bend"] + 0.7)])
# chute from the inverter drum down into the cleanout + drum + compressor
DRUM = cyl("InverterDrum", 3.2, 3.0, "Y", (63.0, 10.0, 3.6), M_YELLOW, seg=32)
cyl("DrumCore", 1.6, 3.2, "Y", (63.0, 10.0, 3.6), M_DARKM, seg=24)
CHUTE = poly_obj("Chute", [Vector((60.5, 9.0, 2.2)), Vector((57.5, 4.0, 3.0)), Vector((55.4, 1.0, 3.0)), Vector((55.0, 0.3, 2.3))], 0.45, M_TAIL, seg=12)
COMP = box("Compressor", 66, 72, 16, 20, 0.25, 4.0, M_YELLOW)
HOSE = poly_obj("AirHose", sag_pts((66, 17, 1.5), (56.2, 1.0, 2.6), 1.2, 16), 0.18, M_HOSE, seg=8)
bake_fn(DRUM, "rotation_euler", 1, lambda t: -2.2 * lin((t - C["push"]) / (C["bend"] + 0.7 - C["push"])) * 2 * math.pi)
for o_ in (DRUM, CHUTE, COMP, HOSE, bpy.data.objects["DrumCore"]): windows(o_, [(C["heres"], C["then"])])
# air arrows chasing the front (between the tail and the liner wall)
ARROWS = []
for k in range(3):
    bm = bmesh.new(); add_arrow(bm, (0, 0), (0, 1), 0.7, 0.16, 0.0); A_ = mesh_obj(f"AirArrow{k}", bm, M_CYANG)
    off = 1.1 + 1.0 * k
    def pos(t, off=off):
        s = max(0.0, FRONT_S(t) - off); p = LP.at(s); tt = tangent_at(s); v = Y.cross(tt).normalized()
        return tuple(p + v * 0.36 + Vector((0, 0.04, 0)) - tt * 0.35)
    bake_loc(A_, pos)
    bake_rot(A_, lambda t, off=off: tuple(orient(tangent_at(max(0.0, FRONT_S(t) - off)))))
    windows(A_, [(C["air"], C["bend"] + 0.7)]); ARROWS.append(A_)

# ================= cure: Mantaflow hot-water inflow (short shot, laptop --bake-fluid), steam, UV light train =================
FL_DOM = box("HotWaterFluidDomain", 2.0, 12.0, 0.0, 0.42, ZP - 0.42, ZP + 0.42, M_HOTW)
FL_IN = cyl("HotWaterInflow", 0.2, 0.4, "X", (11.5, 0.2, ZP), M_HOTW, seg=12)
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=64, start=F(C["hot"] - 0.1), end=F(C["hot"] + 3.3), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_IN.hide_render = True
if FLUID_BAKE: windows(FL_DOM, [(C["hot"] - 0.1, C["steam"])])
else: windows(FL_DOM, [])
STEAM = pipe_wall("SteamEmitter", [Vector((14, 0, ZP)), Vector((-2, 0, ZP))], 0.0, 0.15, M_INV, seg=8)
fx.particles(STEAM, "dust", F(C["steam"] - 0.05), F(C["ultraviolet"] + 0.4), count=900)
try:
    ps = STEAM.particle_systems[0].settings; ps.normal_factor = 0.12; ps.effector_weights.gravity = -0.05; ps.lifetime = 18; ps.particle_size = 0.05
    dm = ps.instance_object.data.materials[0]; bb = bsdf_of(dm); bb.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bb.inputs["Emission Color"].default_value = (1, 1, 1, 1); bb.inputs["Emission Strength"].default_value = 2.0
except Exception as e: print("[build] steam tune skipped", e)
UVT = empty("UVTrain")
for k in range(3):
    bm = bmesh.new(); add_cyl(bm, 0.2, 0.5, "X", (k * 0.8, 0, 0), 16); mesh_obj(f"UVLamp{k}", bm, M_VIOLETG, parent=UVT)
uvl_d = bpy.data.lights.new("UVLight", "POINT"); uvl_d.energy = 40.0; uvl_d.color = (0.55, 0.25, 1.0); uvl_d.shadow_soft_size = 0.2
uvl = bpy.data.objects.new("UVLight", uvl_d); CL.objects.link(uvl); par(uvl, UVT); uvl.location = (0.8, 0, 0)
bake_loc(UVT, lambda t: (PW([(C["ultraviolet"] - 0.1, 15.0), (C["hardens"] - 0.3, -1.0)])(t), 0.08, ZP))
windows(UVT, [(C["ultraviolet"] - 0.1, C["hardens"] - 0.3)])

# ================= stake what-if: jackhammered floor (rigid body slab chunks + dust + trench + dirt pile) =================
CHUNKS = []
for i in range(6):
    for j in range(6):
        x0, y0 = -20.0 + i * 5.0, j * 8.4
        bm = bmesh.new(); add_box(bm, x0 + 0.3, x0 + 4.7, y0 + 0.3, y0 + 8.1, 0.0, 1.0, 0); add_box(bm, x0 + 0.3, x0 + 4.7, y0 + 0.3, y0 + 8.1, 1.0, 1.15, 1)
        o = mesh_obj(f"SlabChunk{i}{j}", bm, [M_CONC, M_FLOOR]); CHUNKS.append(o)
SLAB_L = box("SlabStakeL", -42, -20, 0, 52, 0, 1.15, M_CONC); SLAB_R = box("SlabStakeR", 10, 42, 0, 52, 0, 1.15, M_CONC)
GROUND_P = [box("GroundPassiveL", -60, -9, -2, 60, -2, 0, M_INV), box("GroundPassiveR", 1, 60, -2, 60, -2, 0, M_INV), box("TrenchBottom", -9, 1, -2, 60, -5.9, -5.5, M_INV)]
TRENCH = box("TrenchVoid", -8.5, 0.5, -0.05, 0.0, -5.5, 0.02, M_DARKM)
PILE = lathe("DirtPile", [(0.0, 0.0), (6.0, 0.0), (3.5, 2.5), (0.0, 3.6)], M_DIRT, ang=2 * math.pi, seg=24, loc=(22.0, 12.0, 1.15))
bake_scale(PILE, lambda t: (max(0.01, ease((t - C["trench"]) / 1.2)),) * 3)
for o_ in [SLAB_L, SLAB_R, TRENCH, PILE]: windows(o_, [T_STAKE])
for o_ in (SLAB, FLOOR): windows(o_, [(0, C["normally"]), (C["instead"], DUR)])
fx.rigid(CHUNKS + SHARDS, passive=GROUND_P, mass=4.0, friction=0.7, bounce=0.15)
rnd = random.Random(11)
for o in CHUNKS:
    try:
        rb = o.rigid_body; rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=1)
        f0 = F(C["jackhammers"]) + rnd.randint(0, 9)
        o.location = (0, 0, 0); o.keyframe_insert("location", frame=1); o.keyframe_insert("location", frame=f0)
        o.location = (rnd.uniform(-0.04, 0.04), -rnd.uniform(0.0, 0.05), rnd.uniform(0.10, 0.18)); o.keyframe_insert("location", frame=f0 + 2)
        rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 2)
        rb.kinematic = False; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 3)
    except Exception as e: print("[build] chunk kinematic skipped", e)
    windows_r(o, [T_STAKE])
for k, o in enumerate(SHARDS):
    try:
        rb = o.rigid_body; rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=1)
        f0 = F(C["crumbles"]) + rnd.randint(0, 6)
        o.location = (0, 0, 0); o.keyframe_insert("location", frame=1); o.keyframe_insert("location", frame=f0)
        o.location = (rnd.uniform(-0.05, 0.05), -0.12, -0.02); o.keyframe_insert("location", frame=f0 + 2)
        rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 2)
        rb.kinematic = False; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 3)
    except Exception as e: print("[build] shard kinematic skipped", e)
    windows_r(o, [(0, C["but"])])
DUST = box("StakeDustEmitter", -20, 10, 0.2, 50, 1.2, 1.3, M_INV)
fx.particles(DUST, "dust", F(C["jackhammers"]), F(C["instead"] - 0.3), count=900)
DUST2 = box("CrumbleDustEmitter", -4, 8, 0.05, 0.5, ZP - 0.3, ZP + 0.5, M_INV)
fx.particles(DUST2, "dust", F(C["crumbles"]), F(C["but"]), count=400)
DUST3 = box("CutDustEmitter", XB - 0.4, XB + 0.4, 0.02, 0.3, ZP + 0.3, ZP + 0.5, M_INV)
fx.particles(DUST3, "dust", F(C["cuts"]), F(C["out"] + 0.3), count=250)
for d_ in (DUST, DUST2, DUST3):
    try: ps = d_.particle_systems[0].settings; ps.particle_size = 0.06 if d_ is DUST else 0.025; ps.normal_factor = 1.5 if d_ is DUST else 0.4
    except Exception as e: print("[build] dust tune skipped", e)

# ================= robot cutter (B12) =================
ROB = empty("Robot")
bm = bmesh.new(); add_box(bm, 0.0, 1.5, -0.2, 0.2, -0.13, 0.13); RB_ = mesh_obj("RobotBody", bm, M_YELLOW, parent=ROB)
for wx in (0.25, 1.25):
    for wy in (-0.2, 0.2):
        bm = bmesh.new(); add_cyl(bm, 0.1, 0.06, "Y", (wx, wy, -0.15), 12); mesh_obj("RobotWheel", bm, M_DARKM, parent=ROB)
bm = bmesh.new(); add_cyl(bm, 0.07, 0.03, "X", (-0.01, 0, 0.02), 14); mesh_obj("RobotLens", bm, M_WHITEG, parent=ROB)
ARM = empty("RobotArm", (0.1, 0, 0.1), parent=ROB)
bm = bmesh.new(); add_cyl(bm, 0.04, 0.3, "Z", (0, 0, 0.15), 10); mesh_obj("ArmShaft", bm, M_STEEL, parent=ARM)
BURR = empty("Burr", (0, 0, 0.32), parent=ARM)
bm = bmesh.new(); add_cyl(bm, 0.11, 0.12, "Z", (0, 0, 0), 12)
for k in range(6):
    vs_ = add_box(bm, 0.08, 0.14, -0.015, 0.015, -0.06, 0.06); bmesh.ops.rotate(bm, verts=vs_, cent=(0, 0, 0), matrix=Matrix.Rotation(2 * math.pi * k / 6, 3, "Z"))
mesh_obj("BurrHead", bm, M_STEEL, parent=BURR)
bake_fn(BURR, "rotation_euler", 2, lambda t: 0.0 if t < C["cuts"] else 60.0 * (t - C["cuts"]))
bake_fn(ARM, "location", 2, lambda t: 0.1 + 0.16 * ease((t - C["cuts"] + 0.3) / 0.5) - 0.16 * ease((t - C["out"] - 0.3) / 0.5))
ROB_X = PW([(C["so"], 6.0), (C["rolls"] + 0.3, XB - 0.1)])
bake_loc(ROB, lambda t: (ROB_X(t), 0.12, ZP - R_LI + 0.25))
windows(ROB, [(C["so"], DUR)])
rl_d = bpy.data.lights.new("RobotLamp", "POINT"); rl_d.energy = 6.0; rl_d.color = (1.0, 0.95, 0.85); rl_d.shadow_soft_size = 0.1
rl = bpy.data.objects.new("RobotLamp", rl_d); CL.objects.link(rl); par(rl, ROB); rl.location = (-0.3, 0, 0.1)

# ================= London 1971: egg-shaped brick sewer with a liner (LX) =================
def egg(sc, n=48):
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n; s, c = math.sin(a), math.cos(a)
        if s >= 0: pts.append((6.0 * sc * c, 6.0 * sc * s))
        else: pts.append((6.0 * sc * c * (1 + 0.45 * s), 9.0 * sc * s))
    return pts
def egg_ring(name, s_out, s_in, y0, y1, m_):
    bm = bmesh.new(); po, pi_ = egg(s_out), egg(s_in); n = len(po)
    vo = [[bm.verts.new((LX + x, y, z)) for x, z in po] for y in (y0, y1)]
    vi = [[bm.verts.new((LX + x, y, z)) for x, z in pi_] for y in (y0, y1)]
    for k in range(n):
        k2 = (k + 1) % n
        bm.faces.new([vo[0][k], vo[0][k2], vo[1][k2], vo[1][k]]); bm.faces.new([vi[0][k2], vi[0][k], vi[1][k], vi[1][k2]])
        bm.faces.new([vo[0][k2], vo[0][k], vi[0][k], vi[0][k2]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_)
LSOIL = box("LondonClay", LX - 30, LX + 30, 0, 60, -30, 30, M_CLAY)
bm = bmesh.new(); po = egg(1.18)
v0 = [bm.verts.new((LX + x, -1, z)) for x, z in po]; v1 = [bm.verts.new((LX + x, 61, z)) for x, z in po]
for k in range(len(po)): bm.faces.new([v0[k], v0[(k + 1) % len(po)], v1[(k + 1) % len(po)], v1[k]])
bm.faces.new(list(reversed(v0))); bm.faces.new(v1); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
LCUT = mesh_obj("LondonCut", bm, None); LCUT.hide_render = True; LCUT.display_type = "WIRE"
boolean(LSOIL, LCUT, "EggCut")
egg_ring("BrickSewer", 1.18, 1.0, 0, 60, M_BRICK)
M_LLINER, B_LLINER = mat("LondonLiner", CURED, rough=0.3, emit_rgb=(0.30, 0.92, 1.0))
egg_ring("LondonLiner", 1.0, 0.95, 0, 60, M_LLINER)
B_LLINER.inputs["Base Color"].default_value = (0.35, 0.50, 0.56, 1)
glow(B_LLINER, [(0, 0.15), (C["london"] - 0.02, 0.15), (C["london"] + 0.3, 1.0), (C["still"] + 0.2, 1.0), (C["service"] + 0.6, 0.4)])
box("LondonWater", LX - 2.2, LX + 2.2, 0, 60, -8.4, -7.0, M_WATER)
ll_d = bpy.data.lights.new("SewerLamp", "POINT"); ll_d.energy = 700.0; ll_d.color = (1.0, 0.85, 0.6); ll_d.shadow_soft_size = 1.0
ll = bpy.data.objects.new("SewerLamp", ll_d); scene.collection.objects.link(ll); ll.location = (LX, 22.0, 1.0)

# ================= world: HDRI light + own sky gradient, sun, room lights =================
fx.hdri("courtyard", strength=0.5, rotation_deg=40.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.03, 0.03, 0.04, 1); e[1].position = 0.5; e[1].color = (0.20, 0.36, 0.62, 1)
    eh = e.new(0.03); eh.color = (0.85, 0.66, 0.50, 1)
    wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.4; sun_d.angle = math.radians(2.0); sun_d.color = (1.0, 0.88, 0.72)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.95, 0.88)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("RoomBath", (-22.0, 25.0, 26.0), 14.0, 900.0)
area("RoomKitchen", (18.0, 25.0, 26.0), 18.0, 1200.0)
PIPE_FILL = area("PipeFill", (10.0, -10.0, -5.0), 30.0, 400.0, rot=(math.radians(90), 0, 0))
RED_D = bpy.data.lights.new("StakeRed", "POINT"); RED_D.color = (1.0, 0.25, 0.15); RED_D.shadow_soft_size = 5.0
RED_O = bpy.data.objects.new("StakeRed", RED_D); scene.collection.objects.link(RED_O); RED_O.location = (-5.0, -15.0, 12.0)
for t_, v_ in [(0, 0.0), (C["jackhammers"] - 0.02, 0.0), (C["jackhammers"] + 0.3, 60000.0), (C["instead"] - 0.02, 60000.0), (C["instead"], 0.0)]:
    RED_D.energy = v_; RED_D.keyframe_insert("energy", frame=F(t_))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.02; cam_d.clip_end = 6000
def follow(xfn, off, toff=(0, 0, 0)):
    return (lambda t: (xfn(t) + off[0], off[1], ZP + off[2])), (lambda t: (xfn(t) + toff[0], toff[1], ZP + toff[2]))
CR_L, CR_T = follow(lambda t: crawler_x(t) if t < C["old"] else PW([(C["old"], crawler_x(C["old"])), (C["next"], 6.0)])(t), (-1.0, -2.6, 0.45), (-0.9, 0.3, -0.1))
def front_cam(off, toff):
    return (lambda t: tuple(LP.at(FRONT_S(t)) + Vector(off))), (lambda t: tuple(LP.at(FRONT_S(t)) + Vector(toff)))
FR_L, FR_T = front_cam((1.4, -2.8, 0.6), (-0.7, 0.3, 0.0))
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (16.0, -27.0, -0.5), (16.0, 0.0, -2.8), 26),
    (C["new"] - 0.25, (17.0, -20.0, -1.5), (17.5, 0.0, -3.3), 26),
    (C["new"] - 0.2, (22.5, -4.0, -6.2), (19.8, 0.3, -7.0), 28, "cut"),
    (C["normally"] - 0.05, (21.6, -3.6, -6.3), (19.2, 0.3, -7.0), 28),
    (C["normally"], (-4.0, -60.0, 20.0), (-4.0, 0.0, -1.0), 26, "cut"),
    (C["instead"] - 0.05, (-4.0, -50.0, 17.0), (-4.0, 0.0, -1.0), 26),
    (C["instead"], (60.5, -14.0, 7.0), (55.0, 2.0, 0.0), 26, "cut"),
    (C["first"] - 0.05, (59.0, -11.0, 5.0), (55.0, 2.0, -0.5), 26),
    (C["first"], CR_L, CR_T, 26, "cut"),
    (C["next"] - 0.05, CR_L, CR_T, 26),
    (C["next"], (71.0, 13.0, 5.0), (67.0, 22.0, 0.8), 26, "cut"),
    (C["heres"] - 0.05, (67.0, 14.0, 4.2), (66.0, 22.0, 0.8), 26),
    (C["heres"], (63.0, -22.0, 9.0), (57.0, 2.0, -0.5), 24, "cut"),
    (C["air"] - 0.05, (60.0, -16.0, 2.0), (55.0, 0.0, -3.5), 24),
    (C["air"], FR_L, FR_T, 26, "cut"),
    (C["because"] - 0.05, FR_L, FR_T, 26),
    (C["because"], (-24.0, -7.5, -4.0), (-29.0, 0.3, -5.2), 24, "cut"),
    (C["then"] - 0.05, (-25.0, -7.0, -3.2), (-29.0, 0.3, -4.6), 24),
    (C["then"], (11.5, -4.4, -5.9), (7.5, 0.3, -7.0), 26, "cut"),
    (C["hardens"] - 0.55, (9.5, -4.4, -5.9), (5.5, 0.3, -7.0), 26),
    (C["hardens"] - 0.5, (-1.0, -6.5, -5.4), (-5.0, 0.3, -7.0), 26, "cut"),
    (C["its"] - 0.05, (-3.0, -6.5, -5.4), (-6.0, 0.3, -7.0), 26),
    (C["its"], (3.0, -6.5, -5.6), (2.0, 0.3, -7.3), 26, "cut"),
    (C["but"] - 0.05, (2.5, -5.8, -5.8), (2.0, 0.3, -7.3), 26),
    (C["but"], (-11.5, -5.2, -4.8), (-15.0, 0.3, -6.4), 26, "cut"),
    (C["so"] - 0.05, (-12.5, -4.6, -5.0), (-15.0, 0.3, -6.5), 26),
    (C["so"], (-9.0, -5.0, -5.6), (-13.0, 0.3, -6.8), 26),
    (C["cuts"] - 0.3, (-13.0, -3.0, -5.9), (-15.0, 0.3, -6.6), 28),
    (C["these"] - 0.05, (-13.5, -2.8, -5.8), (-15.0, 0.3, -6.5), 28),
    (C["these"], (5.0, -60.0, 6.0), (5.0, 0.0, -3.0), 26, "cut"),
    (C["very"] - 0.2, (5.0, -96.0, 10.0), (5.0, 0.0, -2.0), 26),
    (C["very"] - 0.15, (LX, -30.0, 1.5), (LX, 10.0, -0.5), 26, "cut"),
    (C["would"] - 0.05, (LX, -18.0, 0.5), (LX, 10.0, -0.5), 26),
    (C["would"], (2.0, -70.0, 10.0), (2.0, 0.0, -3.0), 26, "cut"),
    (DUR, (-8.0, -30.0, 0.0), (-12.0, 0.0, -4.5), 26),
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
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 6; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(4.0, min(2.0e5, 18.0 * ((cl - ct).length / 5.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (1.5, 2.0, 0)
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
fx.bake_rigid(F(C["normally"]) - 5, F(C["but"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "floor": (8.0, 0.0, 1.15), "pipe": (20.0, 0.0, ZP + R_OUT), "crack": (18.0, 0.0, ZP + R_OUT), "cleanout": (55.0, 0.0, 2.7),
    "camhead": lambda t: (crawler_x(t), 0.0, ZP - R_IN + 0.4), "roots": (10.0, 0.0, ZP + R_IN), "felt": (64.0, 22.0, 1.4),
    "front": lambda t: tuple(LP.at(FRONT_S(t)) + Vector((0, 0, R_LO))), "joint": (-5.5, 0.0, ZP + 0.84), "branch": (XB, 0.0, ZP + 1.6),
    "robot": lambda t: (ROB_X(t) + 0.7, 0.0, ZP - 0.1), "liner": (2.0, 0.0, ZP - R_LO), "sewer": (LX, 0.0, -10.0),
    "bend": (-29.0, 0.0, -5.5), "drum": (63.0, 10.0, 6.8),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); t = TS[fr - 1]
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_(t) if callable(p_) else p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "story": RR(*T_STORY), "stake": RR(*T_STAKE), "kick": round(C["jackhammers"], 3), "clean": RR(*T_CLEAN),
          "cap_off": round(C["opens"], 3), "crawl": RR(*T_CRAWL), "scrub": round(C["scrubbed"], 3), "felt": RR(*T_FELT),
          "resin_roll": RR(C["soaked"], C["sponge"] + 0.8), "inv": RR(*T_INV), "front_start": round(C["push"], 3),
          "front_end": round(C["bend"] + 0.7, 3), "bend": RR(*T_BEND), "cure": RR(*T_CURE), "hot": round(C["hot"], 3),
          "steam": round(C["steam"], 3), "uv": RR(C["ultraviolet"] - 0.1, C["hardens"] - 0.3), "hard": RR(*T_HARD), "own": RR(*T_OWN),
          "crumble": round(C["crumbles"], 3), "branch": RR(*T_BRANCH), "robot_in": RR(C["so"], C["rolls"] + 0.3),
          "cut": RR(C["cuts"], C["out"] + 0.3), "fifty": RR(*T_FIFTY), "london": RR(*T_LONDON), "cta": RR(*T_CTA)}
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
