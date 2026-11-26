# Septic drain field (3d-47a): "If your home is on septic, the water you flush ends up under your lawn, leaking out of pipes full of holes on purpose."
# Stake: if they clog, sewage comes back up into the yard or the house. >1 in 5 U.S. homes (EPA). Path: tank -> downhill -> small concrete
# distribution box, one outlet per trench, all dead level -> equal share -> 4-inch perforated pipes laid flat in gravel trenches, holes
# down -> drips through the gravel into the soil -> soil bacteria feed on what's left; within a few feet most germs are gone before the
# groundwater -> bacteria need air: shallow trenches, only grass on top; a parked car crushes the soil -> over the years a black slimy
# biomat grows along each trench bottom and slows the water; skip pumping and solids wash out and clog it faster -> water has nowhere to go
# but up: bright green spongy grass in dry weather, sewage surfacing -> CTA "Do you know where your drain field is?"
# Illustrative, 1 unit = 10 cm: generic house + backyard cross-section (section plane y = 0, keep y >= 0), 3 trenches (pipe exaggerated
# ~1.5x), row of 5 houses at X2. Generic car (no brand, no plate text), no people, no text.
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
random.seed(47)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("if","If"),("septic","septic,"),("water","water"),("flush","flush"),("lawn","lawn,"),("leaking","leaking"),("pipes","pipes"),
  ("holes","holes"),("purpose","purpose."),("if2","If"),("clog","clog,"),("sewage","sewage"),("back","back"),("yard","yard"),("house","house."),
  ("more","More"),("one","one"),("five","five"),("american","American"),("homes","homes"),("liquid","Liquid"),("tank","tank"),
  ("downhill","downhill"),("concrete","concrete"),("box","box."),("one2","One"),("outlet","outlet"),("trench","trench,"),("dead","dead"),
  ("level","level,"),("equal","equal"),("share","share."),("then","Then"),("pipes2","pipes"),("four","four"),("inches","inches"),
  ("laid","laid"),("flat","flat"),("trenches","trenches"),("gravel","gravel,"),("holes2","holes"),("down","down."),("drips","drips"),
  ("gravel2","gravel"),("soil","soil,"),("cleaning","cleaning"),("soil2","soil"),("packed","packed"),("bacteria","bacteria"),("left","left."),
  ("within","Within"),("feet","feet,"),("germs","germs"),("gone","gone"),("groundwater","groundwater."),("but","But"),
  ("bacteria2","bacteria"),("air","air."),("thats","That's"),("trenches2","trenches"),("shallow","shallow,"),("grass","grass"),("top","top."),
  ("park","Park"),("car","car"),("crushed","crushed"),("chokes","chokes"),("over","Over"),("black","black,"),("slimy","slimy"),
  ("layer","layer"),("bottom","bottom"),("trench2","trench."),("slows","slows"),("skip","Skip"),("pumping","pumping"),("solids","solids"),
  ("wash","wash"),("clog2","clog"),("faster","faster."),("nowhere","nowhere"),("up","up."),("grass2","grass"),("bright","bright"),
  ("green","green"),("spongy","spongy,"),("dry","dry"),("sewage2","sewage"),("surface","surface"),("yard2","yard."),("do","Do"),
  ("drain","drain"),("field","field"),("tell","Tell"),("comments","comments.")]
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
CL = coll("SepticDrainField")
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


Y = Vector((0, 1, 0))
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


def P(pts): return Path(pts)
# ================= layout (1 unit = 10 cm; section plane y = 0, keep y >= 0; camera on -y) =================
X2 = 700.0                                  # row of five houses ("one in five")
TR_X0, TR_X1 = 45.0, 165.0                  # trench length (12 m)
TR_Y = [0.0, 25.0, 50.0]                    # trench centre lines (trench 0 is cut open by the section)
TR_W, G_BOT, G_TOP = 8.0, -8.0, -3.0        # gravel bed 0.8 m wide, 0.5 m deep, 0.3 m soil cover
PZ, PR_OUT, PR_IN = -5.0, 0.75, 0.62        # 4-inch pipe drawn 1.5x so it reads on a phone
SOIL_BOT, GW_BOT = -34.0, -44.0             # groundwater table well below the trenches
TK = dict(x0=-15.0, x1=15.0, z0=-18.0, z1=-1.0, w=8.0)
DB = dict(x0=28.0, x1=34.0, z0=-7.0, z1=-2.5)
T_HOOK = (0.0, C["if2"]); T_STAKE = (C["if2"], C["more"]); T_ROW = (C["more"], C["liquid"]); T_TANK = (C["liquid"], C["one2"])
T_PLAN = (C["one2"], C["then"]); T_PIPE = (C["then"], C["drips"]); T_SOIL = (C["drips"], C["but"]); T_AIR = (C["but"], C["over"])
T_MAT = (C["over"], C["skip"]); T_SKIP = (C["skip"], C["nowhere"]); T_RISE = (C["nowhere"], C["grass2"]); T_SURF = (C["grass2"], C["do"])
T_CTA = (C["do"], DUR)

# ================= materials =================
M_SOIL = strata("Soil", [(0.06, 0.035, 0.018), (0.13, 0.075, 0.035), (0.09, 0.05, 0.025), (0.16, 0.095, 0.045)], scale=0.14, bump=0.5)
M_SUB = strata("Subsoil", [(0.22, 0.14, 0.07), (0.30, 0.20, 0.10), (0.25, 0.16, 0.08)], scale=0.05, bump=0.4)
M_CONC, _ = mat("Concrete", (0.50, 0.49, 0.46), rough=0.85, noise=0.8)
M_CONCCUT, _ = mat("ConcreteCut", (0.70, 0.68, 0.62), rough=0.9, noise=2.0)
M_PVC, B_PVC = mat("PVC", (0.90, 0.90, 0.88), rough=0.32, emit_rgb=(0.30, 0.92, 1.0))
M_PVCG, B_PVCG = mat("PVCGreen", (0.30, 0.42, 0.30), rough=0.4)
M_GRAVEL, B_GRAVEL = mat("Gravel", (0.26, 0.25, 0.23), rough=0.8, noise=9.0)
M_STONE, _ = mat("Stone", (0.38, 0.36, 0.33), rough=0.7, noise=4.0)
M_GRASS, _ = mat("Grass", (0.12, 0.24, 0.06), rough=0.9, noise=0.4)
M_GRASSF, B_GRASSF = mat("GrassField", (0.12, 0.24, 0.06), rough=0.9, noise=0.4)
M_TUFT, _ = mat("Tuft", (0.17, 0.34, 0.07), rough=0.9)
M_WALL, _ = mat("HouseWall", (0.80, 0.76, 0.68), rough=0.8)
M_WALLCUT, _ = mat("WallCut", (0.92, 0.90, 0.86), rough=0.9, noise=2.0)
M_ROOF, _ = mat("Shingles", (0.20, 0.17, 0.16), rough=0.85, noise=6.0)
M_WINDOW, _ = emit_mat("Window", (1.0, 0.78, 0.55), 2.5)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 6.0)
M_WHITEG, _ = emit_mat("AirGlow", (0.85, 0.95, 1.0), 4.0)
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 6.0)
M_REDG, _ = emit_mat("GermGlow", (1.0, 0.30, 0.24), 5.0)
M_BACT, B_BACT = emit_mat("Bacteria", (0.45, 1.0, 0.30), 3.0)
M_BROWN, _ = mat("Solids", (0.28, 0.18, 0.08), rough=0.6, noise=5.0)
M_SLUDGE, _ = mat("Sludge", (0.20, 0.13, 0.06), rough=0.5, noise=4.0)
M_SCUM, _ = mat("Scum", (0.62, 0.55, 0.32), rough=0.4, noise=6.0)
M_BIOMAT, _ = mat("Biomat", (0.012, 0.012, 0.010), rough=0.15, noise=8.0)
M_PUDDLE, _ = mat("Sewage", (0.10, 0.09, 0.04), rough=0.05)
M_CRUSH, _ = mat("Crushed", (0.05, 0.035, 0.02), rough=0.95, noise=3.0)
M_CAR, _ = mat("CarPaint", (0.55, 0.06, 0.05), rough=0.25, metallic=0.4)
M_TIRE, _ = mat("Tire", (0.03, 0.03, 0.03), rough=0.8)
M_CARGL, _ = mat("CarGlass", (0.05, 0.07, 0.09), rough=0.05)
M_WATER, B_WATER, _V = water_sec("TankWater", dens=0.05)
M_GW, B_GW, _ = water_sec("Groundwater", glow_rgb=(0.25, 0.55, 1.0), vol_rgb=(0.10, 0.28, 0.55), dens=0.05)
M_RISE, B_RISE, _ = water_sec("RisingWater", glow_rgb=(0.35, 0.80, 0.95), vol_rgb=(0.20, 0.35, 0.30), dens=0.12)
glow(B_GW, [(0, 0.3)] + pulse(C["groundwater"], 2.5, base=0.3, hold=1.2))
glow(B_RISE, [(0, 0.8)] + pulse(C["up"], 2.5, base=0.8, hold=0.8))
glow(B_PVC, [(0, 0.0)] + pulse(C["pipes2"], 1.2, hold=1.4) + pulse(C["laid"], 0.8, hold=1.2))
# field grass turns bright green on "bright"
for t_, c_ in [(0.0, (0.12, 0.24, 0.06)), (C["bright"] - 0.05, (0.12, 0.24, 0.06)), (C["green"] + 0.3, (0.16, 0.62, 0.04)), (C["do"] - 0.05, (0.16, 0.62, 0.04)), (C["do"], (0.10, 0.20, 0.05))]:
    B_GRASSF.inputs["Base Color"].default_value = (*c_, 1); B_GRASSF.inputs["Base Color"].keyframe_insert("default_value", frame=F(t_))
# gravel darkens once solids clog it
for t_, c_ in [(0.0, (0.26, 0.25, 0.23)), (C["clog2"] - 0.05, (0.26, 0.25, 0.23)), (C["faster"] + 0.4, (0.16, 0.13, 0.09))]:
    B_GRAVEL.inputs["Base Color"].default_value = (*c_, 1); B_GRAVEL.inputs["Base Color"].keyframe_insert("default_value", frame=F(t_))
glow(B_BACT, [(0, 0.0), (C["soil2"] - 0.05, 0.0), (C["bacteria"] + 0.2, 6.0), (C["left"] + 0.6, 3.0), (C["chokes"], 3.0), (C["chokes"] + 0.5, 1.6)])

# ================= ground =================
SOIL = box("Soil", -140, 260, 0, 110, SOIL_BOT, 0, M_SOIL)
GW = box("Groundwater", -140, 260, 0.02, 110, GW_BOT, SOIL_BOT, M_GW)
SUB = box("Bedrock", -400, 1000, 0, 400, -400, GW_BOT, M_SUB)
box("SideRock", -400, 1000, 110, 400, -400, -0.4, M_SUB)
GRASS = box("Grass", -140, 260, 0, 110, 0, 0.4, M_GRASS)
GRASSF = box("FieldGrass", TR_X0 - 4, TR_X1 + 4, 0, TR_Y[-1] + 6, 0, 0.46, M_GRASSF)
FAR = box("FarGrass", -1200, 1600, 110, 1600, -0.4, 0.3, M_GRASS)
TK_CUT = box("TankCut", TK["x0"], TK["x1"], -1, TK["w"], TK["z0"], TK["z1"] + 0.1, None); TK_CUT.hide_render = True; TK_CUT.display_type = "WIRE"
DB_CUT = box("DBoxCut", DB["x0"], DB["x1"], -1, 3.0, DB["z0"], DB["z1"] + 0.1, None); DB_CUT.hide_render = True; DB_CUT.display_type = "WIRE"
TR_CUT = box("Trench0Cut", TR_X0, TR_X1, -1, TR_W / 2, G_BOT, G_TOP, None); TR_CUT.hide_render = True; TR_CUT.display_type = "WIRE"
for c_ in (TK_CUT, DB_CUT, TR_CUT): boolean(SOIL, c_, c_.name)
for c_ in (TK_CUT, DB_CUT): boolean(GRASS, c_, c_.name + "G")

# ================= house (simple shell, windows lit) =================
HX0, HX1 = -110.0, -45.0
box("HouseWalls", HX0, HX1, 0, 80, 0.4, 28, M_WALL)
box("HouseCut", HX0 + 0.2, HX1 - 0.2, -0.02, 0.0, 0.4, 28, M_WALLCUT)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in [(HX0 - 3, -0.5, 28), (HX1 + 3, -0.5, 28), ((HX0 + HX1) / 2, -0.5, 44), (HX0 - 3, 82, 28), (HX1 + 3, 82, 28), ((HX0 + HX1) / 2, 82, 44)]]
for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: bm.faces.new([vs[i] for i in f])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj("Roof", bm, M_ROOF)
for wx in (-100, -80, -62):
    box(f"Win{wx}", wx, wx + 9, -0.1, 0.0, 10, 20, M_WINDOW)

# ================= pipes: house -> tank -> distribution box -> trenches =================
P_HOUSE = [Vector((HX1 + 2, 0, -3.0)), Vector((TK["x0"] + 0.5, 0, -3.4))]
pipe_wall("HouseDrain", P_HOUSE, PR_IN, PR_OUT, M_PVC)
P_TKOUT = [Vector((TK["x1"] - 0.5, 0, -4.2)), Vector((DB["x0"] + 0.4, 0, -4.5))]
pipe_wall("TankOutlet", P_TKOUT, PR_IN, PR_OUT, M_PVC)
P_T0 = [Vector((DB["x1"] - 0.4, 0, -4.8)), Vector((TR_X0, 0, PZ)), Vector((TR_X1, 0, PZ))]
pipe_wall("Trench0Pipe", P_T0, PR_IN, PR_OUT, M_PVC)
HOLES = [TR_X0 + 2.0 + 3.0 * i for i in range(int((TR_X1 - TR_X0 - 3) / 3.0))]
bm = bmesh.new()
for hx in HOLES:
    for ang in (0.55,):
        vs = add_cyl(bm, 0.16, 2.2, "Z", (0, 0, 0), seg=10)
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(ang, 3, "X"))
        bmesh.ops.translate(bm, verts=vs, vec=(hx, 0, PZ))
HOLE_CUT = mesh_obj("HoleCutter", bm, None); HOLE_CUT.hide_render = True; HOLE_CUT.display_type = "WIRE"
boolean(bpy.data.objects["Trench0Pipe"], HOLE_CUT, "Holes")
HOLE_GLOW = []
hg_me = sphere_mesh("HoleGlowM", 0.17, 1); hg_me.materials.append(M_GOLDG)
for hx in HOLES:
    d = Vector((0, math.sin(0.55), -math.cos(0.55)))
    o = obj_from(f"HoleGlow{hx:.0f}", hg_me, loc=tuple(Vector((hx, 0, PZ)) + d * PR_IN * 0.98)); HOLE_GLOW.append(o)
    windows(o, [(C["holes"] - 0.05, C["purpose"] + 0.6), (C["holes2"] - 0.05, C["down"] + 0.8)])
# trenches 1, 2: full pipes + gravel (hidden inside the soil, seen in the plan view)
HEAD = [[Vector((30, 1.5, -4.8)), Vector((30, TR_Y[1], -4.8)), Vector((TR_X0, TR_Y[1], PZ)), Vector((TR_X1, TR_Y[1], PZ))],
        [Vector((32, 1.5, -4.8)), Vector((32, TR_Y[2], -4.8)), Vector((TR_X0, TR_Y[2], PZ)), Vector((TR_X1, TR_Y[2], PZ))]]
for k, hp in enumerate(HEAD):
    mesh_obj(f"Header{k + 1}", sweep_bm(chaikin(hp, 2), [PR_OUT] * len(chaikin(hp, 2)), seg=16), M_PVC)
    box(f"Gravel{k + 1}", TR_X0, TR_X1, TR_Y[k + 1] - TR_W / 2, TR_Y[k + 1] + TR_W / 2, G_BOT, G_TOP, M_GRAVEL)
GRAV0 = box("Gravel0Back", TR_X0, TR_X1, 1.15, TR_W / 2, G_BOT, G_TOP, M_GRAVEL)   # back half of trench 0 (behind the cut pipe)
GRAV0F = box("Gravel0Floor", TR_X0, TR_X1, 0.0, 1.15, G_BOT, PZ - PR_OUT - 0.05, M_GRAVEL)
GRAV0T = box("Gravel0Top", TR_X0, TR_X1, 0.0, 1.15, PZ + PR_OUT + 0.05, G_TOP, M_GRAVEL)
# stones on the gravel faces (Geometry Nodes scatter)
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.32)
STONE = mesh_obj("StoneProto", bm, M_STONE)
fx.scatter(GRAV0F, STONE, density=3.0, scale_min=0.5, scale_max=1.3, seed=1)
fx.scatter(GRAV0T, STONE, density=3.0, scale_min=0.5, scale_max=1.3, seed=2)

# ================= septic tank (cutaway) =================
x0, x1, z0, z1, w = TK["x0"], TK["x1"], TK["z0"], TK["z1"], TK["w"]
box("TankFloor", x0, x1, 0, w, z0, z0 + 1, M_CONC); box("TankLid", x0, x1, 0, w, z1 - 1, z1, M_CONC)
box("TankBack", x0, x1, w - 1, w, z0, z1, M_CONC)
box("TankL", x0, x0 + 1, 0, w, z0, z1, M_CONC); box("TankR", x1 - 1, x1, 0, w, z0, z1, M_CONC)
box("TankBaffle", x1 - 4, x1 - 3.4, 0, w - 1, -9, -2, M_CONC)
for rx in (x0 + 4, x1 - 7):
    box(f"Riser{rx:.0f}", rx, rx + 3.5, 0, 4, z1, 0.5, M_CONC)
TWATER = box("TankLiquid", x0 + 1, x1 - 1, 0.05, w - 1, z0 + 1, -4.4, M_WATER)
SCUM = box("Scum", x0 + 1, x1 - 4, 0.05, w - 1, -5.2, -4.4, M_SCUM)
SLUDGE = box("Sludge", x0 + 1, x1 - 1, 0.06, w - 1, 0, 1, M_SLUDGE); SLUDGE.location.z = z0 + 1
bake_scale(SLUDGE, lambda t: (1, 1, 2.5 + 3.5 * ease((t - C["skip"]) / 1.6)))
# distribution box
box("DBFloor", DB["x0"], DB["x1"], 0, 3, DB["z0"], DB["z0"] + 0.6, M_CONC); box("DBBack", DB["x0"], DB["x1"], 2.4, 3, DB["z0"], DB["z1"], M_CONC)
box("DBL", DB["x0"], DB["x0"] + 0.6, 0, 3, DB["z0"], DB["z1"], M_CONC); box("DBR", DB["x1"] - 0.6, DB["x1"], 0, 3, DB["z0"], DB["z1"], M_CONC)
box("DBLid", DB["x0"] - 0.3, DB["x1"] + 0.3, 0, 3.3, DB["z1"], DB["z1"] + 0.5, M_CONC)
DBW = box("DBWater", DB["x0"] + 0.6, DB["x1"] - 0.6, 0.05, 2.4, DB["z0"] + 0.6, -4.75, M_WATER)
LEVEL = box("LevelLine", DB["x0"] - 1.5, DB["x1"] + 14, -0.06, -0.02, -4.86, -4.74, M_CYANG)
windows(LEVEL, [(C["dead"] - 0.05, C["share"] + 0.4)])

# ================= biomat, rising water, crushed soil, puddles =================
BIO = box("Biomat", TR_X0, TR_X1, 0.02, TR_W / 2, 0, 1, M_BIOMAT); BIO.location.z = G_BOT
def bio_th(t):
    return 0.02 + 0.55 * ease((t - C["black"]) / 3.0) + 0.9 * ease((t - C["clog2"]) / 1.2)
bake_scale(BIO, lambda t: (1, 1, bio_th(t)))
RISE = box("RiseTrench", TR_X0, TR_X1, -0.04, TR_W / 2, 0, 1, M_RISE); RISE.location.z = G_BOT
bake_scale(RISE, lambda t: (1, 1, max(0.01, (G_TOP - G_BOT + 0.2) * ease((t - C["nowhere"]) / 1.4))))
windows(RISE, [(C["nowhere"] - 0.05, DUR)])
RISE2 = box("RiseSoil", TR_X0 - 2, TR_X1 + 2, -0.08, 0.3, 0, 1, M_RISE); RISE2.location.z = G_TOP
bake_scale(RISE2, lambda t: (1, 1, max(0.01, (0.0 - G_TOP + 0.35) * ease((t - C["up"] + 0.3) / 1.0))))
windows(RISE2, [(C["up"] - 0.35, DUR)])
CRUSH = box("Crushed", 82, 133, -0.1, 26, 0, 1, M_CRUSH); CRUSH.location.z = -0.02
bake_scale(CRUSH, lambda t: (1, 1, -2.9 * ease((t - C["crushed"]) / 0.6)))
windows(CRUSH, [(C["crushed"] - 0.05, C["over"])])
PUD = []
for i, (px, py, pr) in enumerate([(72, 6, 4.5), (96, 14, 6.0), (118, 5, 5.0), (140, 18, 4.0), (85, 30, 3.5), (130, 34, 4.2)]):
    bm = bmesh.new(); add_cyl(bm, pr * 1.3, 0.08, "Z", (0, 0, 0), seg=24)
    o = mesh_obj(f"Puddle{i}", bm, M_PUDDLE); o.location = (px, py, 0.95); o.scale = (1.0, 0.7 + 0.3 * random.random(), 1.0)
    sc0 = o.scale.copy(); d_ = 0.25 * i
    bake_scale(o, lambda t, sc0=sc0, d_=d_: tuple(v * max(0.001, ease((t - C["clog"] - d_ * 0.5) / 0.8) * (1 - ease((t - C["more"] + 0.3) / 0.3))
                                                     + ease((t - C["sewage2"] - d_) / 0.9)) for v in sc0))
    PUD.append(o)
bpy.ops.mesh.primitive_plane_add(size=1, location=(105, 15, 0.6)); MUDEM = bpy.context.active_object; MUDEM.name = "MudEmitter"
MUDEM.scale = (60, 30, 1); MUDEM.hide_render = True
for c_ in list(MUDEM.users_collection): c_.objects.unlink(MUDEM)
CL.objects.link(MUDEM)
mm = fx.particles(MUDEM, "mud", F(C["sewage2"]), F(C["do"]), count=500)
if mm:
    s = mm.particle_system.settings; s.normal_factor = 6.0; s.particle_size = 0.25; s.lifetime = 25; MUDEM.show_instancer_for_render = False

# ================= bacteria (scatter on a thin card on the section face) =================
BACT = box("BacteriaCard", TR_X0 - 4, TR_X1 + 4, -0.14, -0.04, -20.0, G_BOT, None)
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.16)
BUG = mesh_obj("BacteriaProto", bm, M_BACT)
fx.scatter(BACT, BUG, density=1.6, scale_min=0.6, scale_max=1.4, seed=5)
try: BACT.visible_camera = True
except Exception: pass
BACT.data.materials.append(M_SOIL)
windows(BACT, [(C["soil2"] - 0.1, DUR)])

# ================= flows (glowing beads) =================
FLOW = P(P_HOUSE + [Vector((-5, 0.6, -4.6)), Vector((5, 0.6, -4.4))] + P_TKOUT + P_T0)
beads("HookFlow", FLOW, 26, 0.3, M_CYANG, [T_HOOK], 18.0)
beads("TankFlow", P([Vector((5, 0.6, -4.4))] + P_TKOUT + [Vector((31, 0.6, -4.8))]), 8, 0.3, M_CYANG, [T_TANK], 7.0)
SHARE = [P([Vector((31, 0.6, -4.8))] + P_T0[:2] + [Vector((70, 0, PZ))])] + [P(chaikin(hp, 2)[:-1] + [Vector((70, hp[-1].y, PZ))]) for hp in HEAD]
for k, sp in enumerate(SHARE):
    beads(f"Share{k}", sp, 7, 0.36, M_CYANG, [(C["one2"] + 0.2, C["then"])], 9.0)
beads("PipeFlow", P(P_T0[1:]), 18, 0.28, M_CYANG, [(C["then"], C["drips"] + 1.0)], 9.0)
SOL = P([Vector((5, 0.6, -5.0))] + P_TKOUT + P_T0)
beads("SolidsFlow", SOL, 12, 0.36, M_BROWN, [(C["solids"] - 0.1, C["nowhere"])], 12.0)
# drips: from the holes through the gravel into the soil; germs (red) fade within a few feet
DRIPS = []
for j, hx in enumerate(HOLES[::2]):
    jx = random.uniform(-0.8, 0.8)
    path = P([Vector((hx, 0.4, PZ - 0.7)), Vector((hx + jx * 0.4, -0.25, G_BOT)), Vector((hx + jx, -0.25, -16.0)), Vector((hx + jx * 1.3, -0.25, -27.0))])
    DRIPS.append(path)
    beads(f"Drip{j}", path, 3, 0.2, M_CYANG, [(C["leaking"], C["if2"]), (C["drips"], C["but"])], 4.2)
germ_me = sphere_mesh("GermM", 0.24, 1); germ_me.materials.append(M_REDG)
for j, path in enumerate(DRIPS):
    for g in range(2):
        o = obj_from(f"Germ{j}_{g}", germ_me)
        def gpos(t, path=path, g=g): return path.at(((g * 0.5) * path.L + 4.2 * t) % path.L)
        bake_loc(o, lambda t, gpos=gpos: tuple(gpos(t) + Vector((0, -0.05, 0))))
        bake_scale(o, lambda t, gpos=gpos: (max(0.001, 1.0 - lin((G_BOT - 1.0 - gpos(t).z) / 7.0)),) * 3)
        windows(o, [(C["germs"] - 0.3, C["but"])])
# air from the grass down to the trenches
for j in range(16):
    ax_ = TR_X0 + 4 + j * 7.4 + random.uniform(-1, 1)
    under_car = 82 < ax_ < 133
    wins = [(C["air"] - 0.3, C["crushed"] if under_car else C["over"])]
    beads(f"Air{j}", P([Vector((ax_, -0.25, 0.6)), Vector((ax_ + 0.5, -0.25, G_TOP)), Vector((ax_, -0.25, G_BOT + 0.5))]), 2, 0.17, M_WHITEG, wins, 3.5)

# ================= car (rigid body drop) =================
bm = bmesh.new()
add_box(bm, 86, 129, 5, 23, 2.6, 8.0, 0); add_box(bm, 97, 119, 5.6, 22.4, 8.0, 12.5, 2)
for wx in (93, 122):
    for wy in (5.4, 22.6): add_cyl(bm, 3.0, 2.2, "Y", (wx, wy, 3.0), seg=20, mi=1)
CAR = mesh_obj("Car", bm, [M_CAR, M_TIRE, M_CARGL])
for v in CAR.data.vertices: v.co -= Vector((107.5, 14, 0))
CAR.location = (107.5, 14, 5.0)
GROUND_RB = box("GroundCollider", -140, 260, 0, 110, -2, 0.42, None); GROUND_RB.hide_render = True; GROUND_RB.display_type = "WIRE"
fx.rigid([CAR], passive=[GROUND_RB], mass=1200.0, friction=0.8, bounce=0.15)
scene.gravity = (0, 0, -98.1)                       # 1 unit = 10 cm
windows_r(CAR, [(C["park"] - 0.02, C["over"])])

# ================= field outline on the lawn (CTA) =================
OUT = []
for k, ty in enumerate(TR_Y):
    o = box(f"Outline{k}", TR_X0, TR_X1, max(0.2, ty - 0.8), ty + 0.8, 1.7, 1.95, M_CYANG); OUT.append(o)
o = box("OutlineTank", x0, x1, 0.2, w, 1.7, 1.95, M_GOLDG); OUT.append(o)
o = box("OutlineHeader", 28.5, 33.5, 0.2, TR_Y[-1], 1.7, 1.95, M_CYANG); OUT.append(o)
for o in OUT: windows(o, [(C["drain"] - 0.1, DUR)])

# ================= one in five: row of houses at X2 =================
for i in range(5):
    hx = X2 - 60 + i * 30
    m_ = M_WALL
    box(f"RowHouse{i}", hx - 9, hx + 9, 2, 22, 0.4, 13, m_)
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in [(hx - 10.5, 1.5, 13), (hx + 10.5, 1.5, 13), (hx, 1.5, 20), (hx - 10.5, 22.5, 13), (hx + 10.5, 22.5, 13), (hx, 22.5, 20)]]
    for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: bm.faces.new([vs[j] for j in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj(f"RowRoof{i}", bm, M_ROOF)
    box(f"RowWin{i}", hx - 4, hx + 4, 1.9, 2.0, 5, 10, M_WINDOW)
box("RowGround", X2 - 90, X2 + 90, 0, 40, -200, 0.4, M_SOIL)
box("RowGrass", X2 - 90, X2 + 90, 0, 40, 0.4, 0.8, M_GRASS)
RG_TANK = box("RowTank", X2 + 6, X2 + 12, -0.05, 0.05, -7, -3, M_GOLDG)
RG_LINES = [box(f"RowLine{k}", X2 + 15, X2 + 32, -0.05, 0.05, -5.2 - 2.2 * k, -4.8 - 2.2 * k, M_GOLDG) for k in range(3)]
for o in [RG_TANK] + RG_LINES: windows(o, [(C["five"] + 0.1, C["liquid"])])
RG_GOLD = box("RowHalo", X2 - 9.5, X2 + 9.5, 1.8, 1.9, 0.4, 13.3, M_GOLDG); windows(RG_GOLD, [(C["five"] + 0.1, C["liquid"])])
glow(B_GOLDG, [(0, 6.0)])

# ================= plan view: soil and grass away =================
for o in (SOIL, GRASS, GRASSF, GW):
    windows(o, [(0.0, C["one2"]), (C["then"], DUR)])
for o in [bpy.data.objects[n] for n in ("Gravel1", "Gravel2", "Gravel0Back", "Gravel0Floor", "Gravel0Top")]:
    windows(o, [(0.0, C["one2"]), (C["then"], DUR)])
PLANG = box("PlanGround", -300, 500, -300, 600, -12, -8.05, M_SUB); windows(PLANG, [T_PLAN])
for k, ty in enumerate(TR_Y):
    windows(box(f"PlanGravel{k}", TR_X0, TR_X1, max(0.0, ty - TR_W / 2), ty + TR_W / 2, -8.05, -7.2, M_GRAVEL), [T_PLAN])

# ================= fx: hdri, glare, particles, scatter =================
fx.hdri("forest", strength=0.8, rotation_deg=140.0, show_background=True)
fx.glare(threshold=1.0, strength=0.55, size=7)
bm = bmesh.new(); add_cyl(bm, 0.12, 1.2, "Z", (0, 0, 0.6), seg=5, r2=0.0); add_cyl(bm, 0.1, 0.9, "Z", (0.25, 0, 0.45), seg=5, r2=0.0)
TUFT = mesh_obj("TuftProto", bm, M_TUFT)
fx.scatter(GRASS, TUFT, density=0.5, scale_min=0.5, scale_max=1.3, seed=3)
bm = bmesh.new(); add_cyl(bm, 0.12, 1.5, "Z", (0, 0, 0.75), seg=5, r2=0.0); add_cyl(bm, 0.1, 1.1, "Z", (0.25, 0, 0.55), seg=5, r2=0.0)
TUFTF = mesh_obj("TuftFieldProto", bm, M_GRASSF)
fx.scatter(GRASSF, TUFTF, density=0.9, scale_min=0.6, scale_max=1.4, seed=4)

# ================= lights =================
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 2.4; sun_d.angle = math.radians(2.0); sun_d.color = (1.0, 0.88, 0.72)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(52), 0, math.radians(-30))
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.92, 0.82)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("SectionKey", (60, -70, -10), 160.0, 3.0e4, rot=(math.radians(90), 0, 0), color=(1.0, 0.92, 0.84))
area("SectionLow", (60, -40, -32), 120.0, 1.0e4, rot=(math.radians(100), 0, 0), color=(0.75, 0.85, 1.0))
area("RowKey", (X2, -80, 40), 120.0, 3.0e4, rot=(math.radians(70), 0, 0))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 6000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (2, -160, 26), (8, 10, -7), 26),                                      # hook: house + lawn, section shows the flow
    (C["leaking"] - 0.05, (38, -125, 18), (45, 10, -6), 26),
    (C["leaking"], (88, -24, -3.0), (100, 2, -5.6), 32, "cut"),                     # pipes full of holes, drips
    (C["if2"] - 0.05, (96, -22, -3.4), (104, 2, -5.8), 32),
    (C["if2"], (112, -95, 30), (108, 20, 0), 28, "cut"),                           # stake: sewage on the lawn
    (C["more"] - 0.05, (108, -80, 24), (108, 18, 0), 28),
    (C["more"], (X2 + 10, -190, 50), (X2, 10, 2), 26, "cut"),                      # one in five homes
    (C["liquid"] - 0.05, (X2 + 4, -165, 40), (X2, 10, 0), 26),
    (C["liquid"], (6, -62, -7), (12, 0, -8), 30, "cut"),                            # tank -> downhill -> box
    (C["concrete"], (30, -26, -4.0), (31, 1, -4.8), 32),
    (C["one2"] - 0.05, (31, -22, -3.5), (31, 1, -4.8), 32),
    (C["one2"], (68, -45, 120), (75, 30, -8), 28, "cut"),                           # plan view: one outlet per trench, equal share
    (C["then"] - 0.05, (72, -38, 108), (78, 30, -8), 28),
    (C["then"], (41, -13, -3.6), (46, 1, -5.0), 34, "cut"),                        # 4-inch pipe end
    (C["laid"], (70, -45, -1), (95, 2, -5.5), 30),                                  # laid flat in gravel
    (C["holes2"] - 0.05, (78, -40, -2), (98, 2, -5.5), 30),
    (C["holes2"], (95, -10, -6.8), (95, 2, -5.4), 34, "cut"),                       # holes pointing down
    (C["drips"] - 0.05, (97, -10, -6.6), (97, 2, -5.4), 34),
    (C["drips"], (100, -38, -8), (100, 2, -10), 30, "cut"),                         # drips through the gravel into the soil
    (C["soil2"], (100, -40, -13), (100, 2, -14), 30),                               # bacteria
    (C["within"] - 0.05, (102, -42, -14), (102, 2, -15), 30),
    (C["within"], (100, -85, -18), (100, 2, -22), 28, "cut"),                       # a few feet, groundwater below
    (C["but"] - 0.05, (104, -80, -16), (102, 2, -20), 28),
    (C["but"], (105, -70, 2), (105, 5, -4), 28, "cut"),                             # air from the grass, shallow trenches
    (C["park"] - 0.05, (105, -64, 4), (105, 5, -3), 28),
    (C["park"], (105, -115, 14), (107, 12, -1), 26, "cut"),                        # car on the field crushes the soil
    (C["over"] - 0.05, (105, -104, 12), (107, 12, -1), 26),
    (C["over"], (96, -24, -6.4), (100, 2, -7.4), 32, "cut"),                        # biomat along the trench bottom
    (C["skip"] - 0.05, (104, -22, -6.2), (104, 2, -7.4), 32),
    (C["skip"], (2, -55, -8), (8, 0, -10), 30, "cut"),                              # skip pumping: sludge, solids wash out
    (C["clog2"] - 0.1, (30, -48, -7), (40, 0, -7), 30),
    (C["clog2"], (75, -32, -5.5), (82, 2, -7), 30, "cut"),
    (C["nowhere"] - 0.05, (80, -30, -5.5), (86, 2, -7), 30),
    (C["nowhere"], (100, -48, -3), (102, 2, -4), 30, "cut"),                        # nowhere to go but up
    (C["grass2"] - 0.05, (102, -52, -1), (102, 2, -3), 30),
    (C["grass2"], (100, -75, 14), (102, 25, 0), 28, "cut"),                         # bright green spongy grass
    (C["sewage2"], (108, -50, 9), (108, 14, 0), 28),                                # sewage surfaces
    (C["do"] - 0.05, (108, -46, 8), (108, 14, 0), 28),
    (C["do"], (80, -150, 175), (85, 32, 0), 28, "cut"),                           # CTA: where is your drain field?
    (DUR, (80, -185, 210), (85, 32, 0), 28),
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
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 20; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(50.0, min(4.0e4, 0.6 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (3, 4, 0)
for o_ in scene.objects:
    if o_.type == "LIGHT":
        try: o_.visible_camera = False
        except Exception: pass

# ================= render settings =================
fx.engine("cycles")
r = scene.render
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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4; scene.cycles.transparent_max_bounces = 12; scene.cycles.volume_bounces = 0
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
try: scene.cycles.volume_step_rate = 4.0
except Exception: pass
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
fx.bake_rigid(F(C["park"]) - 1, F(C["over"]) + 5)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "house": (HX1 - 10, 0, 30), "tank": (0, 0, -9), "dbox": (31, 0, -4.0), "pipe_end": (TR_X0 + 0.5, 0, PZ), "holes": (98, 0.4, PZ - 0.6),
    "gravel": (100, 0, -7.0), "soil": (120, -0.2, -14), "bacteria": (110, -0.2, -15), "groundwater": (120, 0, -38), "trench_depth": (TR_X1 - 5, 0, -5.5),
    "air": (100, -0.2, -1.5), "car": W(CAR, (0, 0, 13)), "crushed": (108, 0, -1.5), "biomat": (101, 0, G_BOT + 0.4), "sludge": (0, 0, -15),
    "puddle": (96, 14, 0.6), "field": (105, 25, 0.6), "row": (X2, 2, 22), "outlets": (31, 10, -4.8), "grass": (105, 20, 1.0),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4], "flow": RR(*T_HOOK), "drips": [RR(C["leaking"], C["if2"]), RR(C["drips"], C["but"])],
          "holes_glow": [round(C["holes"], 3), round(C["holes2"], 3)], "puddles": [round(C["clog"], 3), round(C["sewage2"], 3)],
          "row_pop": round(C["five"] + 0.1, 3), "plan": RR(*T_PLAN), "share": round(C["one2"] + 0.2, 3), "level": round(C["dead"], 3),
          "germs_fade": RR(C["germs"], C["groundwater"]), "air": RR(C["air"] - 0.3, C["over"]), "car_drop": round(C["park"], 3),
          "car_land": round(C["park"] + 0.33, 3), "crush": round(C["crushed"], 3), "biomat": RR(C["black"], C["trench2"]),
          "sludge": round(C["skip"], 3), "solids": RR(C["solids"] - 0.1, C["nowhere"]), "clog": round(C["clog2"], 3),
          "rise": RR(C["nowhere"], C["up"] + 0.8), "green": round(C["bright"], 3), "mud": RR(C["sewage2"], C["do"]), "outline": round(C["drain"], 3)}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
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
