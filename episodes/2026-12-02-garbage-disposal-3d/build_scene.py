# Garbage disposal (3d-45a): "Your garbage disposal has no blades. Not one." Stake: treat it like a blender and it jams or clogs the
# pipe under the sink -> cutaway under the sink: steel grind chamber, flat spinning plate (turntable), motor (~1,725 rpm on many models),
# two blunt swivel lugs (impellers) fling food outward into the stationary grind ring (sharp teeth + narrow slots), food torn like on a
# cheese grater, only bits small enough pass the slots, running water flushes them into the P-trap -> ice cube myth (nothing to sharpen,
# ice scrubs gunk off the ring) -> cold water keeps grease solid, hot water melts it and it hardens further down the pipe -> jam: hums but
# won't spin (pit wedged), cut the power, hex wrench in the bottom socket, red reset button -> CTA hero push-in.
# Illustrative, 1 unit = 1 cm: generic disposer (no brand, no text, no logo), generic kitchen sink cabinet. No people, no hands.
# Section plane y = 0 (keep y >= 0, orange cut faces); the camera looks from -y. Plate, impellers, food and rotor are drawn whole.
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
random.seed(45)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("your","Your"),("garbage","garbage"),("disposal","disposal"),("no","no"),("blades","blades."),("not","Not"),("one","one."),
  ("treat","Treat"),("blender","blender,"),("jams","jams,"),("or","or"),("clogs","clogs"),("pipe","pipe"),("sink","sink."),("heres","Here's"),
  ("down","down"),("below","Below"),("drain","drain"),("steel","steel"),("chamber","chamber,"),("bottom","bottom,"),("flat","flat"),
  ("spinning","spinning"),("plate","plate."),("flip","Flip"),("switch","switch,"),("many","many"),("motor","motor"),("spins","spins"),
  ("about","about"),("seventeen","seventeen"),("hundred","hundred"),("minute","minute."),("on","On"),("top","top"),("plate2","plate"),
  ("ride","ride"),("two","two"),("lugs","lugs"),("impellers","impellers."),("theyre","They're"),("blunt","blunt,"),("swivel","swivel."),
  ("as","As"),("spins2","spins,"),("fling","fling"),("food","food"),("outward","outward,"),("hard","hard,"),("wall","wall."),
  ("that","That"),("grind","grind"),("ring","ring."),("never","never"),("moves","moves."),("lined","lined"),("sharp","sharp"),
  ("teeth","teeth"),("narrow","narrow"),("slots","slots."),("food2","food"),("torn","torn"),("teeth2","teeth,"),("cheese","cheese"),
  ("grater","grater."),("only","Only"),("bits","bits"),("slots2","slots"),("escape","escape,"),("running","running"),("water","water"),
  ("flushes","flushes"),("drain2","drain."),("thats","That's"),("ice","ice"),("trick","trick"),("cant","can't"),("sharpen","sharpen"),
  ("theres","There's"),("nothing","nothing"),("sharpen2","sharpen."),("ice2","Ice"),("scrubs","scrubs"),("gunk","gunk"),("ring2","ring."),
  ("run","Run"),("cold","cold"),("grease","grease"),("solid","solid"),("chopped","chopped"),("hot","Hot"),("melts","melts"),
  ("harden","harden"),("further","further"),("pipe2","pipe."),("if","If"),("hums","hums"),("wont","won't"),("jammed","jammed."),
  ("cut","Cut"),("power","power"),("then","Then"),("turn","turn"),("hex","hex"),("socket","socket"),("bottom2","bottom"),
  ("wrench","wrench,"),("press","press"),("red","red"),("reset","reset"),("button","button."),("did","Did"),("blades2","blades?"),
  ("tell","Tell"),("comments","comments.")]
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
CL = coll("Disposal")
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

# ================= helpers for this episode =================
def rbox_bm(x0, x1, y0, y1, z0, z1, r, seg=4):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=seg, profile=0.5, affect="EDGES")
    return bm
def rbox(name, x0, x1, y0, y1, z0, z1, r, m_, seg=4):
    o = mesh_obj(name, rbox_bm(x0, x1, y0, y1, z0, z1, r, seg), m_)
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(35))
    except Exception: pass
    return o
def cut_back(bm, y_cut, fill=True):
    """Keep only y <= y_cut (the removable front half)."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, y_cut, 0), plane_no=(0, 1, 0), clear_outer=True)
    if fill:
        oe = [e for e in bm.edges if len(e.link_faces) < 2]
        if oe: bmesh.ops.edgeloop_fill(bm, edges=oe)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def solidify(o, th):
    md = o.modifiers.new("Solid", "SOLIDIFY"); md.thickness = th; md.offset = -1.0; md.use_even_offset = True; return md
def torus(name, R, r, m_, loc, segU=40, segV=16):
    prof = [(R + r * math.cos(2 * math.pi * k / segV), r * math.sin(2 * math.pi * k / segV)) for k in range(segV)]
    bm = bmesh.new()
    rings = [[bm.verts.new(((rr) * math.cos(2 * math.pi * i / segU), (rr) * math.sin(2 * math.pi * i / segU), zz)) for rr, zz in prof] for i in range(segU)]
    for i in range(segU):
        a, b = rings[i], rings[(i + 1) % segU]
        for k in range(segV): bm.faces.new([a[k], a[(k + 1) % segV], b[(k + 1) % segV], b[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, m_); o.location = loc
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def tube(name, pts, r, m_, seg=14, half=False):
    pts = chaikin([Vector(p) for p in pts], 3)
    bm = sweep_bm(pts, [r] * len(pts), seg, cap=not half)
    if half: cut_front(bm, 0.0, fill=False)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o, pts
def bake_rot(o, fn):
    vals = [fn(t) for t in TS]
    for ax in range(3): bake(o, "rotation_euler", ax, [v[ax] for v in vals])
def winding_mat(name, rgb, scale, emit_rgb):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS" if False else "BANDS"
    wv.bands_direction = "X"; wv.inputs["Scale"].default_value = scale; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 0.55; mr.inputs[4].default_value = 1.0
    L.new(wv.outputs["Fac"], mr.inputs[0])
    mx = mix_rgb(nt, mr.outputs[0], tuple(c * 0.45 for c in rgb), rgb); L.new(mx, b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.3
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b


# ================= this episode =================
scene.gravity = (0.0, 0.0, -981.0)          # cm world
X_GR = -150.0                                # cheese grater set (on the counter, far left)
# ---------- beat windows ----------
T_HOOK = (0.0, C["treat"]); T_STAKE = (C["treat"], C["heres"]); T_TOUR = (C["heres"], C["on"]); T_IMP = (C["on"], C["that"])
T_RING = (C["that"], C["thats"]); T_ICE = (C["thats"], C["run"]); T_GREASE = (C["run"], C["if"]); T_JAM = (C["if"], C["did"])
T_CTA = (C["did"], DUR)
EXT = [(C["then"], C["did"])]                # bottom view: whole motor housing
def is_ext(t): return any(a <= t < b for a, b in EXT)

# ---------- materials ----------
M_SEC, B_SEC = mat("CutFace", (0.90, 0.38, 0.06), rough=0.5, emit_rgb=(1.0, 0.40, 0.08)); B_SEC.inputs["Emission Strength"].default_value = 0.12
M_STEEL, B_STEEL = mat("ChamberSteel", (0.62, 0.63, 0.66), rough=0.28, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_SINK, _ = mat("SinkSteel", (0.78, 0.79, 0.81), rough=0.18, metallic=1.0)
M_RING, B_RING = mat("GrindRing", (0.55, 0.56, 0.6), rough=0.3, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_TEETH, B_TEETH = mat("Teeth", (0.75, 0.76, 0.8), rough=0.2, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_SLOT, B_SLOT = emit_mat("SlotGlow", (0.30, 0.92, 1.0), 0.0)
M_PLATE, B_PLATE = mat("Plate", (0.70, 0.71, 0.74), rough=0.25, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_LUG, B_LUG = mat("Lugs", (0.80, 0.81, 0.84), rough=0.22, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_BODY, B_BODY = mat("MotorBody", (0.04, 0.045, 0.05), rough=0.35, emit_rgb=(1.0, 0.3, 0.24))
M_MOUNT, _ = mat("MountRing", (0.5, 0.5, 0.52), rough=0.3, metallic=1.0)
M_RUBBER, _ = mat("Baffle", (0.02, 0.02, 0.02), rough=0.7)
M_WIND, B_WIND = winding_mat("Windings", (0.72, 0.38, 0.18), 6.0, (0.98, 0.74, 0.27))
M_ROTOR, B_ROTOR = mat("Rotor", (0.45, 0.46, 0.5), rough=0.3, metallic=1.0)
M_PVC, _ = mat("PVC", (0.88, 0.88, 0.86), rough=0.35)
M_RESET, B_RESET = mat("ResetRed", (0.75, 0.05, 0.04), rough=0.35, emit_rgb=(0.98, 0.74, 0.27))
M_WRENCH, B_WRENCH = mat("Wrench", (0.12, 0.12, 0.13), rough=0.3, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_COUNTER, _ = mat("Counter", (0.20, 0.19, 0.18), rough=0.3, noise=8)
M_CAB, _ = mat("Cabinet", (0.36, 0.25, 0.16), rough=0.6, noise=3)
WALL_M, _ = mat("Wall", (0.07, 0.085, 0.11), rough=0.8)
M_FLOOR, _ = mat("CabFloor", (0.12, 0.11, 0.10), rough=0.7)
M_PLATEW, _ = mat("SwitchPlate", (0.9, 0.9, 0.88), rough=0.3)
M_LEVER, B_LEVER = mat("Lever", (0.92, 0.92, 0.9), rough=0.3, emit_rgb=(0.98, 0.74, 0.27))
M_GUNK, _ = mat("Gunk", (0.18, 0.12, 0.05), rough=0.9, noise=40)
M_GREASE, B_GREASE = mat("Grease", (0.92, 0.88, 0.70), rough=0.6, emit_rgb=(1.0, 0.3, 0.24))
M_GHOST, B_GHOST = emit_mat("GhostBlade", (1.0, 0.12, 0.08), 0.0)
M_PIT, B_PIT = mat("Pit", (0.42, 0.22, 0.10), rough=0.8, noise=20, emit_rgb=(1.0, 0.3, 0.24))
M_ICE, _ = mat("Ice", (0.85, 0.95, 1.0), rough=0.05); bsdf_of(M_ICE).inputs["Transmission Weight"].default_value = 0.85
M_BEAD, B_BEAD = emit_mat("BeadCyan", (0.30, 0.92, 1.0), 4.0)
M_HOTB, B_HOTB = emit_mat("BeadHot", (1.0, 0.45, 0.15), 4.0)
M_GRB, B_GRB = emit_mat("BeadGrease", (1.0, 0.85, 0.35), 3.0)
M_STREAM, B_STREAM = emit_mat("Stream", (0.30, 0.92, 1.0), 1.2)
FOOD_COLS = [(0.95, 0.42, 0.06), (0.25, 0.62, 0.15), (0.92, 0.80, 0.30), (0.85, 0.72, 0.52), (0.70, 0.10, 0.12)]
M_FOOD = [mat(f"Food{i}", c, rough=0.6, emit_rgb=(0.98, 0.74, 0.27)) for i, c in enumerate(FOOD_COLS)]

def mark_caps(o, y_cut=0.0, eps=1e-3):
    """faces lying on the section plane -> material 1 (orange cut face)"""
    me = o.data
    if len(me.materials) < 2: me.materials.append(M_SEC)
    for p in me.polygons:
        if all(abs(me.vertices[v].co.y + o.location.y - y_cut) < eps for v in p.vertices): p.material_index = 1
def lathe_sec(name, prof, m_, a0=0.0, ang=math.pi, seg=48, loc=(0, 0, 0)):
    o = lathe(name, prof, [m_, M_SEC], a0=a0, ang=ang, seg=seg, loc=loc)
    if abs(ang - math.pi) < 1e-6 and a0 == 0.0: mark_caps(o)
    return o
def lathe_full(name, prof, m_, seg=64, loc=(0, 0, 0)):
    o = lathe(name, prof, m_, a0=0.0, ang=2 * math.pi, seg=seg, loc=loc)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    return o
def sec_box(name, x0, x1, y0, y1, z0, z1, m_):
    """box cut at y = 0 (keeps y >= 0) with an orange cap"""
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1)
    if y0 < 0 < y1: cut_front(bm, 0.0)
    o = mesh_obj(name, bm, [m_, M_SEC]); mark_caps(o); return o
def rot_box(bm, ang, r0, r1, hw, z0, z1, mi=0):
    vs = add_box(bm, r0, r1, -hw, hw, z0, z1, mi)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(ang, 3, "Z"))
def sec_tube(name, pts, r, m_, seg=24, th=0.35):
    pts = chaikin([Vector(p) for p in pts], 3)
    bm = sweep_bm(pts, [r] * len(pts), seg, cap=False); cut_front(bm, 0.0, fill=False)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    solidify(o, th); return o, pts

# ================= room: cabinet under the sink =================
FLOOR = box("CabFloor", -60, 60, -40, 40, -2, 0, M_FLOOR)
BACK = box("BackWall", -200, 80, 40, 42, -2, 170, WALL_M)
SIDE_R = box("SideR", 50, 52, -40, 40, 0, 88, M_CAB); SIDE_L = box("SideL", -52, -50, -40, 40, 0, 88, M_CAB)
# counter (with the sink hole), cut at y = 0
for nm, xs, ys in (("CtrL", (-200, -24), (-30, 40)), ("CtrR", (24, 80), (-30, 40)), ("CtrB", (-24, 24), (18, 40))):
    sec_box(nm, xs[0], xs[1], ys[0], ys[1], 88, 92, M_COUNTER)
# sink bowl (section): bottom z 70, walls to the counter
SINK = []
SINK.append(sec_box("SinkBottom", -22, 22, -18, 16, 69.2, 70.0, M_SINK))
SINK.append(sec_box("SinkWallL", -22.8, -22, -18, 16, 69.2, 91, M_SINK))
SINK.append(sec_box("SinkWallR", 22, 22.8, -18, 16, 69.2, 91, M_SINK))
SINK.append(box("SinkWallB", -22.8, 22.8, 16, 16.8, 69.2, 91, M_SINK))
# sink flange + throat + mount ring + baffle
lathe_sec("Flange", [(4.2, 70.0), (8.5, 70.0), (8.5, 70.6), (4.2, 71.2)], M_SINK)
lathe_sec("Throat", [(4.2, 62.0), (5.0, 62.0), (5.0, 70.0), (4.2, 70.0)], M_MOUNT)
lathe_sec("Mount", [(5.0, 63.0), (10.5, 63.0), (10.5, 67.5), (5.0, 67.5)], M_MOUNT)
lathe_sec("Baffle", [(1.0, 61.6), (5.0, 61.6), (5.0, 62.4), (1.0, 62.6)], M_RUBBER)
# hopper / grind chamber shell (z 44..62)
CH = lathe_sec("Chamber", [(5.0, 62.0), (5.8, 62.0), (8.9, 58.5), (8.9, 40.0), (8.2, 40.0), (8.2, 58.0), (5.0, 61.2)], M_STEEL)
# dishwasher inlet stub (-x side)
cyl("DWInlet", 1.4, 6.0, "X", (-11.5, 2.0, 55.0), M_STEEL, seg=16)
# grind ring z 41.5..47.5: 15 segments with slots between them, a sharp tooth at each segment's leading edge
NSEG = 15; SEG_A = math.pi / NSEG; GAP = 0.25 * SEG_A
RING = []
for k in range(NSEG):
    a0 = k * SEG_A + GAP / 2
    o = lathe(f"RingSeg{k}", [(7.0, 41.5), (8.2, 41.5), (8.2, 47.5), (7.0, 47.5)], M_RING, a0=a0, ang=SEG_A - GAP, seg=4, smooth=False); RING.append(o)
bm = bmesh.new()
for k in range(NSEG):
    a = k * SEG_A + GAP / 2 + 0.12 * SEG_A
    rot_box(bm, a, 6.25, 7.05, 0.18, 41.8, 47.2)
TEETH = mesh_obj("Teeth", bm, M_TEETH)
bm = bmesh.new()
for k in range(NSEG + 1):
    rot_box(bm, k * SEG_A, 7.2, 8.1, GAP * 3.0, 41.6, 47.4)
SLOTS = mesh_obj("SlotGlow", bm, M_SLOT)
# gunk patches on the ring (scrubbed off by the ice)
bm = bmesh.new()
for k in range(0, NSEG, 2):
    a = k * SEG_A + 0.5 * SEG_A; z = random.uniform(42.5, 45.5)
    rot_box(bm, a, 6.8, 7.05, 0.55, z, z + random.uniform(1.0, 1.8))
GUNK = mesh_obj("Gunk", bm, M_GUNK)
# lower chamber + discharge outlet + motor top
lathe_sec("LowerCh", [(8.2, 34.5), (8.9, 34.5), (8.9, 40.0), (8.2, 40.0)], M_STEEL)
lathe_sec("MotorTop", [(0.9, 34.0), (9.6, 34.0), (9.6, 35.0), (0.9, 35.0)], M_STEEL)
# motor housing (section) + full exterior version for the bottom view
MOT_PROF = [(9.2, 13.0), (9.9, 13.0), (9.9, 34.0), (9.2, 34.0)]
MOTOR_SEC = lathe_sec("MotorShell", MOT_PROF, M_BODY)
BOT_PROF = [(1.2, 11.8), (9.9, 11.8), (9.9, 13.2), (1.2, 13.2)]
BOT_SEC = lathe_sec("MotorBottom", BOT_PROF, M_BODY)
MOTOR_FULL = lathe_full("MotorShellFull", MOT_PROF, M_BODY); BOT_FULL = lathe_full("MotorBottomFull", BOT_PROF, M_BODY)
CH_FULL = lathe_full("ChamberFull", [(5.0, 62.0), (5.8, 62.0), (8.9, 58.5), (8.9, 34.5), (8.2, 34.5), (8.2, 58.0), (5.0, 61.2)], M_STEEL)
STATOR = lathe("Stator", [(5.2, 18.0), (8.9, 18.0), (8.9, 31.0), (5.2, 31.0)], M_WIND, a0=0.0, ang=math.pi)
# hex socket (bottom centre) + red reset button
bm = bmesh.new(); add_cyl(bm, 0.75, 0.5, "Z", (0, 0, 11.75), seg=6)
HEX = mesh_obj("HexSocket", bm, M_RUBBER)
RESET = cyl("ResetButton", 0.9, 1.0, "Z", (5.0, -4.0, 11.4), M_RESET, seg=20)
CORD = poly_obj("Cord", [(-7.0, -2.0, 12.0), (-8.0, -3.0, 8.0), (-14.0, -4.0, 2.0), (-40.0, 10.0, 0.6)], 0.5, M_RUBBER)
# rotating group: rotor + shaft + plate + lugs (driven by one empty)
SPIN = empty("Spin", (0, 0, 0))
ROTOR = cyl("RotorCore", 4.6, 12.0, "Z", (0, 0, 24.5), M_ROTOR, seg=32); par(ROTOR, SPIN)
bm = bmesh.new()
for k in range(12): rot_box(bm, k * math.pi / 6, 3.8, 4.75, 0.35, 18.7, 30.3)
RBARS = mesh_obj("RotorBars", bm, M_WIND); par(RBARS, SPIN)
SHAFT = cyl("Shaft", 0.8, 13.0, "Z", (0, 0, 37.5), M_ROTOR, seg=16); par(SHAFT, SPIN)
PLATE = cyl("Plate", 6.8, 0.8, "Z", (0, 0, 44.4), M_PLATE, seg=64); par(PLATE, SPIN)
bm = bmesh.new()
for k in range(10): add_cyl(bm, 0.55, 0.9, "Z", (4.0 * math.cos(k * 0.63 + 0.3), 4.0 * math.sin(k * 0.63 + 0.3), 44.4), seg=12)
HOLES = mesh_obj("PlateHoles", bm, M_RUBBER); par(HOLES, SPIN)
LUGS = []
for k in (0, 1):
    a = k * math.pi
    piv = empty(f"LugPivot{k}", (4.6 * math.cos(a), 4.6 * math.sin(a), 45.0)); par(piv, SPIN)
    piv.rotation_euler = (0, 0, a)
    bm = bmesh.new(); add_box(bm, -0.6, 1.9, -0.75, 0.75, 0.0, 1.5)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.22, segments=3, profile=0.5, affect="EDGES")
    lug = mesh_obj(f"Lug{k}", bm, M_LUG); par(lug, piv)
    pin = cyl(f"LugPin{k}", 0.35, 2.0, "Z", (0, 0, 0.8), M_STEEL, seg=12); par(pin, piv)
    LUGS.append(piv)

# ---------- spin: angular speed keys (rev/s, visual), integrated ----------
OM = PW([(0, 0.35), (C["jams"] - 0.2, 0.35), (C["jams"], 0.0), (C["heres"], 0.0), (C["spins"], 0.0), (C["spins"] + 0.6, 1.15),
         (C["hums"] - 0.15, 1.15), (C["hums"], 0.0), (C["did"], 0.0), (C["did"] + 0.6, 0.3)])
ANG = [0.0]
for t0, t1 in zip(TS, TS[1:]): ANG.append(ANG[-1] + 2 * math.pi * OM(t0) * (t1 - t0))
JIT = lambda t: (0.05 * math.sin(2 * math.pi * 30 * t) if (C["jams"] <= t < C["or"]) or (C["hums"] <= t < C["cut"]) else 0.0)
WR = lambda t: (0.7 * math.sin(2 * math.pi * 1.4 * (t - C["wrench"])) * ease((t - C["wrench"]) / 0.2) if C["wrench"] <= t < C["press"] + 0.2 else 0.0)
bake(SPIN, "rotation_euler", 2, [ANG[i] + JIT(t) + WR(t) for i, t in enumerate(TS)])
def plate_ang(t): return ANG[min(len(ANG) - 1, max(0, int(round(t * FPS))))]
# lug swivel: lean out while flinging, wiggle on "swivel"
def swing(t):
    s = 0.0
    if C["swivel"] - 0.1 <= t < C["as"]: s += 0.55 * math.sin(2 * math.pi * 1.8 * (t - C["swivel"] + 0.1))
    if C["fling"] <= t < C["thats"]: s += 0.35 * ease((t - C["fling"]) / 0.4)
    return s
for k, piv in enumerate(LUGS): bake(piv, "rotation_euler", 2, [k * math.pi + swing(t) for t in TS])

# ================= drain: outlet -> P-trap -> trap arm into the side wall =================
TRAP_PTS = [(8.6, 0, 38.0), (16, 0, 38.0), (20, 0, 37.0), (22, 0, 33.0), (22, 0, 25.0), (24.5, 0, 20.5), (29.5, 0, 20.5), (32, 0, 25.0),
            (32, 0, 32.0), (34, 0, 35.0), (40, 0, 35.0), (52, 0, 35.0)]
TRAP, TRAP_S = sec_tube("Trap", TRAP_PTS, 2.4, M_PVC)
mark_caps(TRAP)
NUT = lathe_sec("SlipNut", [(2.5, -1.0), (3.2, -1.0), (3.2, 1.0), (2.5, 1.0)], M_PVC, loc=(22, 0, 31.0))
# water path for beads: sink drain -> chamber -> plate edge -> slot -> outlet -> trap -> wall
FLOW = Path(chaikin([Vector(p) for p in [(0.8, 1.0, 69.0), (1.5, 1.5, 58.0), (4.0, 2.0, 47.0), (7.4, 2.3, 45.0), (7.6, 2.5, 39.5), (9.0, 1.2, 38.0)]]
            + [Vector(p) + Vector((0, 0.8, 0)) for p in TRAP_S[6:]], 1))
SLOT_PATH = Path([Vector((7.0, 1.6, 45.0)), Vector((7.65, 1.0, 44.0)), Vector((7.65, 1.0, 39.0)), Vector((9.0, 1.0, 38.0))] + [Vector(p) + Vector((0, 0.8, 0)) for p in TRAP_S[6:]])
WATER_WINS = [(C["running"], C["thats"]), (C["run"], C["if"])]
CYAN = beads("WBead", FLOW, 26, 0.55, M_BEAD, WATER_WINS, speed=55.0)
# water colour: cyan for cold, orange for hot
for b_ in (B_BEAD, B_STREAM):
    col = b_.inputs["Emission Color"]
    for t, c in ((0, (0.30, 0.92, 1.0)), (C["hot"] - 0.05, (0.30, 0.92, 1.0)), (C["hot"] + 0.15, (1.0, 0.42, 0.12)), (C["if"], (1.0, 0.42, 0.12)), (C["if"] + 0.05, (0.30, 0.92, 1.0))):
        col.default_value = (*c, 1); col.keyframe_insert("default_value", frame=F(t))
# faucet + stream
FAU = tube("Faucet", [(0, 30, 92), (0, 30, 118), (0, 26, 126), (0, 18, 126), (0, 12, 120), (0, 11, 116)], 1.3, M_SINK, seg=18)[0]
cyl("FaucetBase", 2.6, 2.0, "Z", (0, 30, 93), M_SINK, seg=24)
STREAM = cyl("Stream", 0.55, 45.0, "Z", (0, 11, 93.5), M_STREAM, seg=12)
windows(STREAM, WATER_WINS)
STR_EM = cyl("StreamEmitter", 0.6, 0.3, "Z", (0, 11, 115.5), None, seg=10); STR_EM.hide_render = True
pm_rain = fx.particles(STR_EM, "rain", F(C["running"]), F(C["drain2"]), count=300)
try: ps_ = pm_rain.particle_system.settings; ps_.particle_size = 0.18; ps_.normal_factor = -40; ps_.lifetime = 14
except Exception as e: print("[fx] stream tune skipped:", e)
# Mantaflow: faucet stream splashing into the bowl around the drain (laptop --bake-fluid; hidden without the cache)
FL_DOM = box("FluidDomain", -21.5, 21.5, 0.2, 15.5, 70.0, 84.0, None); FL_DOM.display_type = "WIRE"
FL_IN = cyl("FluidInflow", 0.6, 0.6, "Z", (0, 11, 82.5), None, seg=10); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
SINK_COLL = box("SinkCollider", -22, 22, -18, 16, 68.0, 70.0, None); SINK_COLL.hide_render = True; SINK_COLL.display_type = "WIRE"
fx.fluid_domain(FL_DOM, FL_IN, eff=[SINK_COLL], res=64, start=F(C["running"]), end=F(C["running"] + 3.0), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_M, _ = water_sec("FluidWater")[:2]
FL_DOM.data.materials.append(FL_M)
windows(FL_DOM, [(C["running"], C["thats"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True

# ================= food: drops in, rides the plate, flung into the ring, torn up =================
def food_me(name, kind):
    bm = bmesh.new()
    if kind == 0: add_box(bm, -0.7, 0.7, -0.5, 0.5, -0.5, 0.5)
    elif kind == 1: add_box(bm, -1.0, 1.0, -0.8, 0.8, -0.12, 0.12)
    else: bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.7)
    for v in bm.verts: v.co += Vector((random.uniform(-0.15, 0.15), random.uniform(-0.15, 0.15), random.uniform(-0.1, 0.1)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me
FOOD = []
T_DROP = C["food"] - 1.6
for i in range(8):
    o = obj_from(f"Food{i}", food_me(f"FoodMe{i}", i % 3), M_FOOD[i % 5][0])
    off = i * 2 * math.pi / 8; t_in = T_DROP + 0.12 * i
    def ffn(t, off=off, t_in=t_in, i=i):
        if t < t_in + 0.45:                                     # falling down the throat
            u = lin((t - t_in) / 0.45); return (0.6 * math.cos(off), 0.6 * math.sin(off), 66.0 - 20.0 * u * u)
        r = 2.2 + 4.0 * ease((t - C["fling"]) / (C["wall"] - C["fling"] + 0.2))
        a = plate_ang(t) + off
        return (r * math.cos(a), r * math.sin(a), 46.0 + 0.4 * math.sin(9 * t + i))
    bake_loc(o, ffn); bake_rot(o, lambda t, i=i: (2.0 * t + i, 1.3 * t, 0.5 * i))
    bake_scale(o, lambda t, i=i: (max(0.001, 1.0 - ease((t - C["torn"] - 0.15 * i % 0.6) / 1.6)),) * 3)
    windows(o, [(t_in, C["only"])]); FOOD.append(o)
for m_, b_ in M_FOOD: glow(b_, pulse(C["food"], 0.35, hold=0.4))
# crumbs torn off at the ring (particles)
CRUMB = cyl("CrumbEmitter", 6.9, 5.0, "Z", (0, 0, 45.5), None, seg=24); CRUMB.hide_render = True
pm_c = fx.particles(CRUMB, "dust", F(C["torn"]), F(C["only"] + 0.5), count=260)
try:
    ps_ = pm_c.particle_system.settings; ps_.particle_size = 0.13; ps_.normal_factor = 3; ps_.lifetime = 30; ps_.effector_weights.gravity = 0.03
    ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.95, 0.45, 0.08, 1)
except Exception as e: print("[fx] crumbs tune skipped:", e)
# bits small enough slip through a slot and ride the water out
BITS = []
for i in range(14):
    o = obj_from(f"Bit{i}", sphere_mesh(f"BitMe{i}", 0.32, 1), M_FOOD[i % 5][0])
    t0 = C["bits"] + 0.25 * i
    bake_loc(o, lambda t, t0=t0: tuple(SLOT_PATH.at(max(0.0, t - t0) * 26.0)))
    windows(o, [(t0, min(C["thats"], t0 + SLOT_PATH.L / 26.0))]); BITS.append(o)

# ================= ghost blender blade (the myth) =================
bm = bmesh.new()
for k in range(4):
    vs = add_box(bm, 0.0, 5.5, -0.9, 0.9, -0.08, 0.08)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(0.35 * (1 if k % 2 else -1), 3, "X"))
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(k * math.pi / 2, 3, "Z"))
add_cyl(bm, 1.0, 1.2, "Z", (0, 0, 0), seg=16)
GB = mesh_obj("GhostBlade", bm, M_GHOST); GB.location = (0, 0, 50.0)
bake(GB, "rotation_euler", 2, [6.0 * t for t in TS])
bake_scale(GB, lambda t: ((1.0 - 0.9 * ease((t - C["not"]) / 0.5)) if t < C["treat"] else (1.0 - 0.9 * ease((t - C["sharpen2"] - 0.1) / 0.5)),) * 3)
windows(GB, [(0.0, C["one"] + 0.5), (C["theres"] - 0.1, C["sharpen2"] + 0.6)])
glow(B_GHOST, [(0, 7.0), (C["not"] - 0.05, 7.0), (C["not"] + 0.1, 12.0), (C["one"] + 0.5, 0.0), (C["theres"] - 0.1, 7.0), (C["sharpen2"] + 0.6, 0.0)])

# ================= pit (jam), grease, ice in the chamber =================
PIT = obj_from("Pit", sphere_mesh("PitMe", 1.0, 3), M_PIT); PIT.scale = (1.3, 0.95, 0.85)
def pit_pos(t):
    a = plate_ang(t) + 0.55
    return (6.1 * math.cos(a), 6.1 * math.sin(a), 46.2)
bake_loc(PIT, pit_pos)
windows(PIT, [(C["blender"], C["or"]), (C["if"] - 0.4, C["press"])])
glow(B_PIT, pulse(C["jams"], 2.5, hold=0.5) + pulse(C["jammed"], 2.5, hold=0.6))
# hum: motor body glows red, windings pulse
glow(B_WIND, [(0, 0.0)] + pulse(C["motor"], 1.2, hold=1.0) + [(C["hums"] - 0.01, 0.0)] + [(C["hums"] + 0.08 * k, 0.9 if k % 2 == 0 else 0.2) for k in range(1, 30)]
     + [(C["power"], 0.0)])
glow(B_STEEL, pulse(C["chamber"], 0.6, hold=0.7))
glow(B_PLATE, pulse(C["plate"], 1.0, hold=0.7) + pulse(C["spins2"], 0.6, hold=0.5))
glow(B_LUG, pulse(C["lugs"], 1.5, hold=1.2) + pulse(C["fling"], 1.0, hold=0.8))
glow(B_RING, pulse(C["wall"], 0.6, hold=0.4) + pulse(C["grind"], 1.0, hold=1.0) + pulse(C["did"], 0.5, hold=2.5))
glow(B_TEETH, pulse(C["teeth"], 2.5, hold=0.6) + pulse(C["teeth2"], 2.0, hold=0.6))
glow(B_SLOT, pulse(C["slots"], 2.5, hold=0.6) + pulse(C["slots2"], 2.0, hold=1.5))
# blunt: lugs flash cyan on "blunt"
col = B_LUG.inputs["Emission Color"]
for t, c in ((0, (0.98, 0.74, 0.27)), (C["blunt"] - 0.05, (0.98, 0.74, 0.27)), (C["blunt"], (0.30, 0.92, 1.0)), (C["as"], (0.30, 0.92, 1.0)), (C["as"] + 0.05, (0.98, 0.74, 0.27))):
    col.default_value = (*c, 1); col.keyframe_insert("default_value", frame=F(t))
glow(B_LUG, pulse(C["blunt"], 1.8, hold=0.5))
# gunk scrubbed off by the ice
bake_scale(GUNK, lambda t: (1.0, 1.0, max(0.001, 1.0 - ease((t - C["scrubs"]) / 1.0))) if t < C["run"] else (0.001,) * 3)
GUNK.location = (0, 0, 0)
# ice in the chamber (rides the plate next to the ring)
ICE_IN = []
for i in range(4):
    bm = bmesh.new(); add_box(bm, -1.1, 1.1, -1.1, 1.1, -1.1, 1.1)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.25, segments=2, profile=0.5, affect="EDGES")
    o = mesh_obj(f"IceIn{i}", bm, M_ICE)
    off = i * math.pi / 2
    bake_loc(o, lambda t, off=off: (5.4 * math.cos(plate_ang(t) + off), 5.4 * math.sin(plate_ang(t) + off), 46.4))
    bake_rot(o, lambda t, i=i: (1.5 * t, 2.1 * t + i, 0))
    bake_scale(o, lambda t: (max(0.001, 1.0 - 0.6 * ease((t - C["scrubs"]) / 1.4)),) * 3)
    windows(o, [(C["sharpen2"] + 0.5, C["run"])]); ICE_IN.append(o)
# grease chunks (cold: solid, chopped)
GREASE = []
for i in range(5):
    o = obj_from(f"GreaseChunk{i}", sphere_mesh(f"GreaseMe{i}", 0.9, 2), M_GREASE); o.scale = (1.3, 1.0, 0.7)
    off = i * 2 * math.pi / 5; t_in = C["grease"] - 0.3 + 0.08 * i
    def gfn(t, off=off, t_in=t_in):
        if t < t_in + 0.4: u = lin((t - t_in) / 0.4); return (0.5 * math.cos(off), 0.5 * math.sin(off), 66.0 - 20.0 * u * u)
        r = 2.2 + 3.8 * ease((t - t_in - 0.4) / 0.5); a = plate_ang(t) + off
        return (r * math.cos(a), r * math.sin(a), 46.0)
    bake_loc(o, gfn)
    bake_scale(o, lambda t: (max(0.001, 1.0 - ease((t - C["chopped"]) / 0.6)) * 1.3, max(0.001, 1.0 - ease((t - C["chopped"]) / 0.6)), max(0.001, 1.0 - ease((t - C["chopped"]) / 0.6)) * 0.7))
    windows(o, [(t_in, C["hot"])]); GREASE.append(o)
glow(B_GREASE, pulse(C["solid"], 0.8, hold=0.5))
# hot: melted grease rides the water and hardens in the trap arm
GRB = beads("GreaseBead", Path([Vector((3.0, 1.0, 46.0))] + list(SLOT_PATH.p[1:])), 10, 0.5, M_GRB, [(C["melts"], C["harden"] + 0.3)], speed=40.0)
PLUG = obj_from("GreasePlug", sphere_mesh("PlugMe", 1.0, 3), M_GREASE); PLUG.location = (45.0, 0.6, 34.2)
dplug = PLUG.modifiers.new("Lumpy", "DISPLACE"); tx = bpy.data.textures.new("PlugTex", "CLOUDS"); tx.noise_scale = 0.8; dplug.texture = tx; dplug.strength = 0.35
PG = PW([(0, 0.0), (C["clogs"] - 0.1, 0.0), (C["clogs"] + 0.5, 1.0), (C["heres"] - 0.1, 1.0), (C["heres"], 0.0), (C["harden"] - 0.1, 0.0), (C["harden"] + 0.9, 1.0)])
bake_scale(PLUG, lambda t: (4.5 * max(0.001, PG(t)), 2.0 * max(0.001, PG(t)), 2.0 * max(0.001, PG(t))))
windows(PLUG, [(C["clogs"] - 0.1, C["heres"]), (C["harden"] - 0.1, C["if"])])
glow(B_GREASE, pulse(C["clogs"], 1.5, hold=0.9) + pulse(C["harden"], 1.5, hold=0.9))

# ================= ice cubes into the sink (rigid body) =================
ICE = []
for i in range(6):
    bm = bmesh.new(); add_box(bm, -1.3, 1.3, -1.3, 1.3, -1.3, 1.3)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=0.3, segments=2, profile=0.5, affect="EDGES")
    o = mesh_obj(f"IceCube{i}", bm, M_ICE)
    o.location = (random.uniform(-6, 6), random.uniform(3.0, 11.0), 100.0 + 4.0 * i); o.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
    windows_r(o, [(C["ice"], C["ice2"])]); ICE.append(o)
SINK_RB = box("SinkRB", -22, 22, 0.0, 16, 68.5, 70.0, None); SINK_RB.hide_render = True; SINK_RB.display_type = "WIRE"
SINK_RBB = box("SinkRBBack", -22, 22, 16, 18, 68.5, 92, None); SINK_RBB.hide_render = True; SINK_RBB.display_type = "WIRE"
SINK_RBF = box("SinkRBFront", -22, 22, -2, 0.0, 68.5, 92, None); SINK_RBF.hide_render = True; SINK_RBF.display_type = "WIRE"
fx.rigid(ICE, passive=[SINK_RB, SINK_RBB, SINK_RBF], mass=0.02, friction=0.3, bounce=0.35)

# ================= wall switch, wrench, grater =================
SWP = rbox("SwitchPlate", -44, -36, 38.6, 39.6, 104, 116, 0.4, M_PLATEW)
LEVER = box("Lever", -0.7, 0.7, -2.2, 0.0, -0.4, 1.8, M_LEVER); LEVER.location = (-40, 38.6, 110)
LV = PW([(0, -0.5), (C["flip"], -0.5), (C["switch"], 0.5), (C["cut"], 0.5), (C["power"], -0.5)])
bake(LEVER, "rotation_euler", 0, [LV(t) for t in TS])
glow(B_LEVER, pulse(C["switch"], 1.5, hold=0.6) + pulse(C["power"], 1.5, hold=0.6))
bm = bmesh.new(); add_cyl(bm, 0.72, 9.0, "Z", (0, 0, -4.5), seg=6); add_cyl(bm, 0.72, 6.0, "X", (3.0 - 0.72, 0, -9.0), seg=6)
WRENCH = mesh_obj("HexWrench", bm, M_WRENCH)
WZ = PW([(0, -12.0), (C["hex"] - 0.2, -12.0), (C["socket"] + 0.2, 12.3), (C["press"] - 0.1, 12.3), (C["press"] + 0.4, -12.0)])
bake_loc(WRENCH, lambda t: (0, 0, WZ(t)))
bake(WRENCH, "rotation_euler", 2, [WR(t) * 1.0 + 0.6 for t in TS])
windows(WRENCH, [(C["hex"] - 0.2, C["press"] + 0.4)])
glow(B_WRENCH, pulse(C["wrench"], 0.4, hold=0.5))
RZ = PW([(0, 0.0), (C["reset"] - 0.15, 0.0), (C["reset"], 0.45), (C["reset"] + 0.25, 0.0)])
bake_loc(RESET, lambda t: (0, 0, RZ(t)))
glow(B_RESET, pulse(C["reset"], 2.0, hold=0.6) + pulse(C["red"], 0.8, hold=0.3))
# cheese grater on a cutting board, far left on the counter
bm = bmesh.new()
for k in range(4):
    vs = add_box(bm, -4.5, 4.5, -0.15, 0.15, 0, 22)
    for v in vs:
        if v.co.z > 1: v.co.x *= 0.7
        v.co.y -= 4.5 * (1 - 0.3 * v.co.z / 22)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(k * math.pi / 2, 3, "Z"))
add_box(bm, -1.0, 1.0, -3.5, 3.5, 22, 24)
M_GRATER, B_GRATER = mat("GraterSteel", (0.55, 0.56, 0.58), rough=0.3, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
_nt = M_GRATER.node_tree; _tc = _nt.nodes.new("ShaderNodeTexCoord"); _vo = _nt.nodes.new("ShaderNodeTexVoronoi"); _vo.inputs["Scale"].default_value = 0.9
_vo.inputs["Randomness"].default_value = 0.0; _nt.links.new(_tc.outputs["Object"], _vo.inputs["Vector"])
_lt = MATH(_nt, "LESS_THAN", _vo.outputs["Distance"], 0.28)
_nt.links.new(mix_rgb(_nt, _lt, (0.55, 0.56, 0.58), (0.01, 0.01, 0.01)), B_GRATER.inputs["Base Color"])
GRATER = mesh_obj("Grater", bm, M_GRATER); GRATER.location = (X_GR, 8, 93.5)
gr_m, gr_b = mat("GraterHoles", (0.0, 0.0, 0.0), rough=0.5, emit_rgb=(0.98, 0.74, 0.27))
BOARD = rbox("Board", X_GR - 22, X_GR + 22, -10, 26, 92, 93.5, 0.5, mat("Wood", (0.55, 0.36, 0.18), rough=0.6, noise=6)[0])
CHEESE = rbox("Cheese", X_GR + 7, X_GR + 15, 0, 10, 93.5, 99, 0.4, mat("Cheese", (0.95, 0.72, 0.18), rough=0.5)[0])
CRB = obj_from("CrumbSeed", sphere_mesh("CrumbSeedMe", 0.35, 1), mat("Crumb", (0.95, 0.75, 0.2), rough=0.6)[0])
fx.scatter(BOARD, CRB, density=0.06, scale_min=0.5, scale_max=1.3, seed=7)
glow(B_GRATER, pulse(C["cheese"], 0.2, hold=0.6))
for o in [GRATER]: pass

# ================= visibility: section vs whole motor housing =================
CUTW = [(0.0, EXT[0][0]), (EXT[0][1], DUR)]
for o in (MOTOR_SEC, BOT_SEC, CH): windows(o, CUTW)
for o in (MOTOR_FULL, BOT_FULL, CH_FULL): windows(o, EXT)

# ================= lights + world =================
fx.hdri("interior", strength=0.3, rotation_deg=40.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, rot, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("Key", (90, -110, 120), (math.radians(50), 0, math.radians(40)), 100, 9.0e4, (1.0, 0.95, 0.88))
area("Rim", (-60, 30, 60), (math.radians(-70), 0, math.radians(-120)), 60, 2.5e4, (0.6, 0.8, 1.0))
area("Low", (40, -60, 0), (math.radians(110), 0, math.radians(30)), 50, 1.2e4, (1.0, 0.9, 0.8))
area("Top", (0, -20, 160), (0, 0, 0), 80, 1.2e4, (1.0, 0.97, 0.92))
area("GrKey", (X_GR + 40, -80, 150), (math.radians(45), 0, math.radians(25)), 80, 1.5e4)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.5; cam_d.clip_end = 6000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (16, -62, 60), (0, 2, 48), 40),
    (C["treat"] - 0.05, (12, -50, 56), (0, 2, 47), 40),
    (C["treat"], (16, -34, 56), (3, 2, 45.5), 42, "cut"),
    (C["or"] - 0.05, (14, -31, 55), (3, 2, 45.5), 42),
    (C["or"], (52, -62, 42), (36, 0, 32), 40, "cut"),
    (C["heres"] - 0.05, (48, -56, 40), (38, 0, 33), 40),
    (C["heres"], (6, -95, 128), (0, 4, 80), 38, "cut"),
    (C["below"], (10, -95, 85), (0, 2, 62), 38),
    (C["bottom"], (14, -80, 60), (0, 2, 48), 40),
    (C["flip"] - 0.05, (12, -72, 56), (0, 2, 46), 40),
    (C["flip"], (-30, -12, 113), (-40, 39, 110), 45, "cut"),
    (C["many"] - 0.25, (-31, -10, 112), (-40, 39, 110), 45),
    (C["many"] - 0.2, (22, -78, 30), (0, 2, 26), 40, "cut"),
    (C["about"], (20, -78, 36), (0, 2, 32), 40),
    (C["on"] - 0.05, (18, -74, 44), (0, 2, 40), 40),
    (C["on"], (9, -30, 62), (0, 1, 45), 42, "cut"),
    (C["as"] - 0.05, (8, -28, 60), (0, 1, 45), 42),
    (C["as"], (12, -40, 66), (0, 2, 46), 40, "cut"),
    (C["that"] - 0.05, (11, -36, 63), (0, 2, 46), 40),
    (C["that"], (5, -24, 50), (1, 4, 44.5), 42, "cut"),
    (C["food2"] - 0.05, (4, -21, 49), (1, 4, 44.5), 42),
    (C["food2"], (14, -36, 56), (2, 3, 45), 40, "cut"),
    (C["cheese"] - 0.05, (12, -33, 55), (2, 3, 45), 40),
    (C["cheese"], (X_GR + 10, -45, 112), (X_GR, 6, 103), 42, "cut"),
    (C["only"] - 0.05, (X_GR + 8, -40, 110), (X_GR, 6, 103), 42),
    (C["only"], (22, -36, 44), (9, 1, 40), 40, "cut"),
    (C["running"] - 0.25, (24, -40, 44), (10, 1, 40), 40),
    (C["running"] - 0.2, (28, -165, 72), (14, 2, 58), 32, "cut"),
    (C["thats"] - 0.05, (26, -150, 70), (14, 2, 58), 32),
    (C["thats"], (14, -72, 104), (0, 6, 70), 38, "cut"),
    (C["theres"] - 0.15, (12, -66, 100), (0, 6, 68), 38),
    (C["theres"] - 0.1, (8, -30, 56), (0, 2, 47), 42, "cut"),
    (C["run"] - 0.05, (7, -27, 54), (0, 2, 46), 42),
    (C["run"], (26, -150, 72), (12, 2, 60), 32, "cut"),
    (C["hot"] - 0.05, (24, -138, 70), (12, 2, 58), 32),
    (C["hot"], (14, -42, 56), (3, 2, 46), 40, "cut"),
    (C["harden"] - 0.2, (14, -40, 55), (4, 2, 45), 40),
    (C["harden"] - 0.15, (50, -55, 40), (40, 0, 33), 40, "cut"),
    (C["if"] - 0.05, (47, -52, 39), (41, 0, 33), 40),
    (C["if"], (22, -82, 46), (0, 2, 36), 38, "cut"),
    (C["cut"] - 0.05, (20, -76, 44), (0, 2, 36), 38),
    (C["cut"], (-30, -12, 113), (-40, 39, 110), 45, "cut"),
    (C["then"] - 0.05, (-31, -10, 112), (-40, 39, 110), 45),
    (C["then"], (22, -44, 2.0), (0, 0, 13), 40, "cut"),
    (C["press"], (16, -36, 1.5), (2, -2, 12), 42),
    (C["did"] - 0.05, (14, -33, 1.5), (2, -2, 12), 42),
    (C["did"], (40, -125, 78), (6, 2, 48), 36, "cut"),
    (DUR, (26, -88, 62), (4, 2, 46), 36),
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
cam_d.dof.use_dof = True; cam_d.dof.focus_object = TGT
bake_scalar(cam_d, "dof.aperture_fstop", [max(2.8, min(16.0, 0.08 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0e2, min(2.0e4, 0.3 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)
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
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = False
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
scene.view_settings.exposure = float(arg("--exposure", "-0.2"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["ice"]), F(C["ice"]) + 60)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "sink": (0.0, 0.0, 71.0), "chamber": (8.9, 0.0, 54.0), "plate": (-6.8, -1.0, 44.4), "motor": (9.9, 0.0, 24.0), "lug": LUGS[0],
    "lug2": LUGS[1], "ring": (7.6, 0.2, 47.5), "slot": (7.65, 0.5, 42.0), "trap": (27.0, 0.0, 18.2), "plug": (45.0, 0.0, 36.5),
    "switch": (-40.0, 38.6, 116.0), "hex": (0.0, 0.0, 11.5), "reset": (5.0, -4.0, 10.9), "wrench": (2.3, 0.0, -2.0),
    "grater": (X_GR, 8.0, 117.0), "faucet": (0.0, 11.0, 118.0), "outlet": (14.0, 0.0, 40.5), "pit": PIT, "teeth": (6.6, 1.5, 47.2), "ring_back": (0.0, 7.2, 47.6),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        pw = p_.matrix_world.translation if hasattr(p_, "matrix_world") else Vector(p_)
        p = world_to_camera_view(scene, cam, pw)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "stake": RR(*T_STAKE), "tour": RR(*T_TOUR), "imp": RR(*T_IMP), "ring": RR(*T_RING), "ice": RR(*T_ICE),
          "grease": RR(*T_GREASE), "jam": RR(*T_JAM), "cta": RR(*T_CTA), "ext": [RR(a, b) for a, b in EXT],
          "cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4],
          "spin_up": round(C["spins"], 3), "spin_stop": [round(C["jams"], 3), round(C["hums"], 3)], "switch_on": round(C["switch"], 3),
          "switch_off": round(C["power"], 3), "food_drop": round(T_DROP, 3), "food_land": round(T_DROP + 0.45, 3),
          "fling": round(C["fling"], 3), "hit_wall": round(C["wall"], 3), "swivel": round(C["swivel"], 3), "torn": RR(C["torn"], C["only"]),
          "water": [RR(a, b) for a, b in WATER_WINS], "ice_drop": round(C["ice"] + 0.35, 3), "scrub": RR(C["scrubs"], C["run"]),
          "grease_in": round(C["grease"], 3), "chop": round(C["chopped"], 3), "plug": [round(C["clogs"], 3), round(C["harden"], 3)],
          "wrench_in": round(C["socket"], 3), "wrench_turn": RR(C["wrench"], C["press"]), "reset_click": round(C["reset"], 3),
          "hum": RR(C["hums"], C["power"])}
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
    r.filepath = os.path.join(out, f"f_"); bpy.ops.render.render(animation=True)
