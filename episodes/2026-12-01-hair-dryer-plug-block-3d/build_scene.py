# Hair dryer plug block (3d-37): what the chunky block on a hair dryer plug does. Claim hook "That chunky block on your hair dryer plug is a
# tiny safety switch." on the block, front shell lifts off -> stake: dryers used to electrocute ~18 Americans a year, a dryer falls into a
# bathtub and electrifies the water, even switched off -> cutaway: hot wire out (gold beads), neutral back (cyan), both through a ring-shaped
# sensing coil, equal currents = fields cancel -> dryer dropped into a sink: current leaks through the water and down the drain pipe ->
# out and back don't match, ~6 mA -> coil signal -> chip -> electromagnet (solenoid plunger) -> contacts snap open (sparks), reset pops
# -> test button fakes a leak, press reset / test -> history chart (18 a year, half children, 1991 on-or-off rule, 2 in 1992) with the
# dryer switch on/off -> unplug first (plug pulled from the outlet) -> CTA push-in on the block.
# Illustrative, 1 unit = 1 cm: generic block plug (no brand, no text), generic dryer, generic bathroom. No logos, no people.
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
CUES = [("that", "That"), ("chunky", "chunky"), ("block", "block"), ("plug", "plug"), ("tiny", "tiny"), ("safety", "safety"), ("switch", "switch."),
        ("its", "It's"), ("because", "because"), ("electrocute", "electrocute"), ("eighteen", "eighteen"), ("americans", "Americans"),
        ("a_", "A"), ("fell", "fell"), ("bathtub", "bathtub"), ("electrify", "electrify"), ("water", "water,"), ("even", "even"),
        ("off", "off."), ("power", "Power"), ("out", "out"), ("one", "one"), ("wire", "wire"), ("back", "back"), ("other", "other."),
        ("both", "Both"), ("pass", "pass"), ("ring", "ring-shaped"), ("coil", "coil."), ("normally", "Normally"), ("equal", "equal,"),
        ("magnetic", "magnetic"), ("cancel", "cancel,"), ("coil2", "coil"), ("nothing", "nothing."), ("now", "Now"), ("drop", "drop"),
        ("sink", "sink."), ("some", "Some"), ("leaks", "leaks"), ("water2", "water"), ("another", "another"), ("home", "home."),
        ("out2", "Out"), ("match", "match"), ("leak", "leak"), ("six", "six"), ("milliamps", "milliamps"), ("enough", "enough."),
        ("coil3", "coil"), ("signal", "signal"), ("circuit", "circuit,"), ("fires", "fires"), ("electromagnet", "electromagnet,"),
        ("snaps", "snaps"), ("contacts", "contacts"), ("few", "few"), ("second", "second."), ("power2", "power"), ("cut", "cut,"),
        ("reset", "reset"), ("pops", "pops"), ("test", "test"), ("fakes", "fakes"), ("purpose", "purpose."), ("press", "Press"),
        ("reset2", "reset,"), ("test2", "test."), ("if_", "If"), ("pop", "pop,"), ("stop", "stop"), ("dryer_s", "dryer."),
        ("about", "About"), ("half", "half"), ("children", "children."), ("since", "Since"), ("y1991", "1991,"), ("protection", "protection"),
        ("on", "on"), ("off2", "off,"), ("by", "by"), ("y1992", "1992,"), ("deaths", "deaths"), ("two", "two"), ("year2", "year."),
        ("still", "Still,"), ("falls", "falls"), ("unplug", "unplug"), ("first", "first,"), ("reach", "reach"), ("does", "Does"),
        ("blocks", "blocks?"), ("tell", "Tell"), ("comments", "comments.")]
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
CL = coll("PlugBlock")
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

# ================= beat windows =================
T_HOOK = (0.0, C["its"]); T_TUB = (C["its"], C["power"]); T_FLOW = (C["power"], C["now"])
T_SINK = (C["now"], C["out2"]); T_TRIP = (C["out2"], C["about"]); T_CHART = (C["about"], C["on"] - 0.15)
T_ONOFF = (C["on"] - 0.15, C["by"]); T_CHART2 = (C["by"], C["still"]); T_UNPLUG = (C["still"], C["does"]); T_CTA = (C["does"], DUR)
# contacts open (tripped) windows: real trip, then the test trip
OPEN = [(C["snaps"], C["reset2"]), (C["test2"] + 0.25, C["does"])]
def is_open(t): return any(a <= t < b for a, b in OPEN)
def open_amt(t):
    v = 0.0
    for a, b in OPEN:
        v = max(v, min(ease((t - a) / 0.08), 1.0 - ease((t - b) / 0.15)))
    return v

# ================= materials =================
M_SHELL, B_SHELL = mat("ShellPlastic", (0.86, 0.86, 0.84), rough=0.32)
M_SHELLIN, _ = mat("ShellInside", (0.30, 0.30, 0.31), rough=0.6)
M_PRONG, _ = mat("Prong", (0.85, 0.80, 0.62), rough=0.22, metallic=1.0)
M_COPPER, B_COPPER = mat("Copper", (0.90, 0.48, 0.25), rough=0.28, metallic=1.0, emit_rgb=(1.0, 0.30, 0.20))
M_HOTINS, _ = mat("HotInsulation", (0.05, 0.05, 0.05), rough=0.45)
M_NEUINS, _ = mat("NeutralInsulation", (0.82, 0.82, 0.80), rough=0.45)
M_PCB, _ = mat("PCB", (0.03, 0.22, 0.10), rough=0.45, noise=40)
M_CHIP, B_CHIP = mat("Chip", (0.03, 0.03, 0.035), rough=0.35, emit_rgb=(1.0, 0.30, 0.22))
M_PIN, _ = mat("Pins", (0.75, 0.75, 0.72), rough=0.25, metallic=1.0)
M_STEEL, _ = mat("Steel", (0.62, 0.63, 0.66), rough=0.30, metallic=1.0)
M_SOL, B_SOL = mat("SolenoidWinding", (0.80, 0.40, 0.18), rough=0.35, metallic=1.0, emit_rgb=(1.0, 0.30, 0.20))
M_TEST, _ = mat("TestButton", (0.25, 0.26, 0.28), rough=0.4)
M_RESET, _ = mat("ResetButton", (0.95, 0.95, 0.93), rough=0.35)
M_RES, B_RES = mat("TestResistor", (0.80, 0.68, 0.45), rough=0.5, emit_rgb=(1.0, 0.30, 0.22))
M_TRACE, B_TRACE = mat("SenseTrace", (0.70, 0.55, 0.20), rough=0.3, metallic=1.0, emit_rgb=(1.0, 0.30, 0.22))
M_GOLDG, _ = emit_mat("GoldBead", (0.98, 0.74, 0.27), 6.0)
M_CYANG, _ = emit_mat("CyanBead", (0.30, 0.92, 1.0), 6.0)
M_REDG, _ = emit_mat("RedBead", (1.0, 0.30, 0.24), 7.0)
M_GOLDF, B_GOLDF = emit_mat("GoldField", (0.98, 0.74, 0.27), 3.0)
M_CYANF, B_CYANF = emit_mat("CyanField", (0.30, 0.92, 1.0), 3.0)
M_FLOOR, _ = mat("StudioFloor", (0.035, 0.038, 0.045), rough=0.35)
M_DRYER, _ = mat("DryerBody", (0.10, 0.11, 0.13), rough=0.30)
M_DRYER2, _ = mat("DryerTrim", (0.55, 0.56, 0.58), rough=0.25, metallic=1.0)
M_HEAT, B_HEAT = mat("HeaterGlow", (0.15, 0.05, 0.02), rough=0.5, emit_rgb=(1.0, 0.42, 0.12))
M_GRILLE, _ = mat("Grille", (0.04, 0.04, 0.04), rough=0.6)
M_SLIDER, _ = mat("Slider", (0.85, 0.85, 0.85), rough=0.35)
M_CORD, _ = mat("Cord", (0.06, 0.06, 0.065), rough=0.45)
M_TILE = tiles("WallTiles", (0.62, 0.66, 0.68), (0.58, 0.62, 0.65), 0.08)
M_TILEF = tiles("FloorTiles", (0.20, 0.21, 0.23), (0.18, 0.19, 0.21), 0.05, plane="XY")
M_ENAMEL, _ = mat("Enamel", (0.93, 0.93, 0.92), rough=0.15)
M_COUNTER, _ = mat("Counter", (0.25, 0.24, 0.23), rough=0.25, noise=12)
M_CAB, _ = mat("Cabinet", (0.42, 0.30, 0.20), rough=0.5, noise=6)
M_CABIN, _ = mat("CabinetInside", (0.10, 0.08, 0.07), rough=0.7)
M_CHROME, _ = mat("Chrome", (0.85, 0.86, 0.88), rough=0.08, metallic=1.0)
M_PLATE, _ = mat("OutletPlate", (0.92, 0.91, 0.88), rough=0.35)
M_BAR, B_BAR = mat("BarGold", (0.98, 0.74, 0.27), rough=0.35, emit_rgb=(0.98, 0.74, 0.27))
M_BARR, B_BARR = mat("BarRed", (1.0, 0.30, 0.24), rough=0.35, emit_rgb=(1.0, 0.30, 0.24))
M_BARC, B_BARC = mat("BarCyan", (0.30, 0.92, 1.0), rough=0.35, emit_rgb=(0.30, 0.92, 1.0))
M_INV, _ = mat("Invisible", (0, 0, 0)); M_INV.blend_method = "BLEND" if hasattr(M_INV, "blend_method") else None
M_WATT, B_WATT, _ = water_sec("TubWater", glow_rgb=(1.0, 0.25, 0.18))
M_WATS, B_WATS, _ = water_sec("SinkWater", glow_rgb=(1.0, 0.25, 0.18))
glow(B_WATT, [(0, 0.0), (C["electrify"] - 0.01, 0.0), (C["electrify"] + 0.25, 0.12), (C["off"] + 0.4, 0.12), (C["power"], 0.0)])
glow(B_WATS, [(0, 0.0), (C["leaks"] - 0.01, 0.0), (C["leaks"] + 0.3, 0.12), (C["out2"], 0.12), (C["out2"] + 0.05, 0.0),
              (C["still"], 0.0), (C["still"] + 0.3, 0.1), (C["unplug"] + 0.25, 0.1), (C["first"], 0.0)])

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

# ================= STUDIO: the block plug (origin, standing on the floor, front = -y) =================
BX0, BX1, BY0, BY1, BZ0, BZ1 = -3.2, 3.2, -1.9, 1.9, 0.0, 7.4
FLOOR = box("StudioFloor", -60, 80, -40, 60, -0.6, 0.0, M_FLOOR)
BACKDROP = box("StudioBack", -60, 80, 60, 61, -0.6, 70, M_FLOOR)
# back half of the shell (open towards the camera), hollow
bm = rbox_bm(BX0, BX1, BY0, BY1, BZ0, BZ1, 0.9, seg=5); cut_front(bm, 0.0, fill=False)
SHELL_B = mesh_obj("ShellBack", bm, [M_SHELL]); solidify(SHELL_B, 0.28)
try: SHELL_B.data.shade_smooth()
except Exception: pass
SHELL_IN = box("ShellBackInner", BX0 + 0.35, BX1 - 0.35, 1.45, 1.55, BZ0 + 0.35, BZ1 - 0.35, M_SHELLIN)
# front half: a separate lid that lifts off on "safety" and comes back for the CTA
bm = rbox_bm(BX0, BX1, BY0, BY1, BZ0, BZ1, 0.9, seg=5); cut_back(bm, 0.0, fill=False)
SHELL_F = mesh_obj("ShellFront", bm, [M_SHELL]); solidify(SHELL_F, 0.28)
try: SHELL_F.data.shade_smooth()
except Exception: pass
LID_OFF = [(C["safety"], C["does"] + 0.8)]
def lid_fn(t):
    a = ease((t - C["safety"]) / 0.55); b = ease((t - (C["does"] + 0.1)) / 0.7)
    u = a * (1 - b)
    return (0.0, -9.0 * u, 3.5 * u * (1 - u) * 2 + 0.0)
bake_loc(SHELL_F, lid_fn)
windows(SHELL_F, [(0, C["safety"] + 0.5), (C["does"], DUR)])
# prongs out of the top, buttons on the front face (on stems, they stay when the lid lifts)
PR_X = (-0.8, 0.8)
for i, x in enumerate(PR_X):
    box(f"Prong{i}", x - 0.08, x + 0.08, -0.32, 0.32, BZ1 - 0.6, BZ1 + 2.0, M_PRONG)
    box(f"ProngBase{i}", x - 0.35, x + 0.35, -0.5, 0.6, BZ1 - 1.3, BZ1 - 0.4, M_STEEL)
BTN = {}
for nm, x, m_ in (("Test", -1.35, M_TEST), ("Reset", 1.35, M_RESET)):
    par_ = empty(f"{nm}Btn")
    bm = bmesh.new(); add_cyl(bm, 0.55, 0.7, "Y", (0, -0.35, 0), seg=28); bmesh.ops.bevel(bm, geom=[e for e in bm.edges if e.verts[0].co.y < -0.6 and e.verts[1].co.y < -0.6], offset=0.15, segments=3, affect="EDGES")
    cap = mesh_obj(f"{nm}Cap", bm, m_, parent=par_)
    try: cap.data.shade_smooth(); cap.data.set_sharp_from_angle(angle=math.radians(40))
    except Exception: pass
    bm = bmesh.new(); add_cyl(bm, 0.18, 1.6, "Y", (0, 0.8, 0), seg=12); mesh_obj(f"{nm}Stem", bm, M_STEEL, parent=par_)
    BTN[nm] = par_
BTN_Z = 3.0; BTN_Y = BY0 - 0.05
def test_fn(t):
    d = 0.0
    for tt in (C["fakes"], C["test2"]):
        d = max(d, min(ease((t - tt) / 0.12), 1 - ease((t - tt - 0.35) / 0.2)))
    return (-1.35, BTN_Y + 0.45 * d, BTN_Z)
def reset_fn(t):
    out_ = 0.0
    for a, b in OPEN:
        out_ = max(out_, min(ease((t - a - 0.06) / 0.10) * (1.0 + 0.12 * math.exp(-max(0, t - a - 0.16) * 18) * math.sin(max(0, t - a - 0.16) * 40)), 1 - ease((t - b) / 0.15)))
    press = min(ease((t - C["reset2"] + 0.1) / 0.1), 1 - ease((t - C["reset2"] - 0.25) / 0.2)) if C["reset2"] - 0.1 <= t <= C["reset2"] + 0.5 else 0.0
    return (1.35, BTN_Y - 0.8 * out_ + 0.35 * press, BTN_Z)
bake_loc(BTN["Test"], test_fn); bake_loc(BTN["Reset"], reset_fn)
# circuit board on the back wall
PCB = box("PCB", -2.6, 2.6, 1.05, 1.25, 0.6, 6.4, M_PCB)
CHIP = box("Chip", 1.0, 2.3, 0.55, 1.05, 1.0, 2.3, M_CHIP)
for k in range(5):
    for sx in (0.92, 2.38):
        box(f"ChipPin{k}{int(sx*10)}", sx - 0.08, sx + 0.08, 0.7, 1.05, 1.15 + k * 0.25, 1.27 + k * 0.25, M_PIN)
# sensing coil: copper-wound ring (axis Z), both wires pass through its hole
COIL_C = Vector((0.0, 0.0, 3.6))
M_WIND, B_WIND = winding_mat("CoilWinding", (0.92, 0.50, 0.25), 18.0, (1.0, 0.28, 0.20))
COIL = torus("SenseCoil", 1.05, 0.42, M_WIND, tuple(COIL_C), segU=56, segV=18)
COIL.rotation_euler = (math.radians(-18), 0, 0)
glow(B_WIND, [(0, 0.0), (C["coil"] - 0.3, 0.0), (C["coil"], 0.0), (C["out2"] - 0.01, 0.0), (C["six"], 0.25), (C["signal"], 0.3),
              (C["circuit"] + 0.3, 0.3), (C["snaps"] + 0.3, 0.0), (C["fakes"], 0.0), (C["fakes"] + 0.25, 0.3), (C["purpose"] + 0.4, 0.0),
              (C["test2"], 0.0), (C["test2"] + 0.15, 0.3), (C["test2"] + 0.7, 0.0)])
# solenoid (electromagnet) + plunger + latch bar to the contacts
SOL = cyl("Solenoid", 0.55, 1.6, "X", (1.6, 0.2, 5.15), M_SOL, seg=28)
M_SOLW, B_SOLW = winding_mat("SolWinding", (0.85, 0.42, 0.2), 30.0, (1.0, 0.30, 0.2))
SOL.data.materials.clear(); SOL.data.materials.append(M_SOLW)
for x_ in (0.75, 2.45): cyl(f"SolCap{int(x_*100)}", 0.62, 0.12, "X", (x_, 0.2, 5.15), M_STEEL, seg=28)
PLUNGER = cyl("Plunger", 0.2, 2.2, "X", (0.0, 0.0, 0.0), M_STEEL, seg=16)
def fires(t):
    v = 0.0
    for a in (C["electromagnet"], C["test2"] + 0.18):
        v = max(v, min(ease((t - a) / 0.07), 1 - ease((t - a - 0.4) / 0.3)))
    return v
bake_loc(PLUNGER, lambda t: (1.25 - 0.7 * fires(t), 0.2, 5.15))
glow(B_SOLW, [(0, 0.0), (C["fires"] - 0.01, 0.0), (C["electromagnet"], 2.5), (C["snaps"] + 0.4, 0.0),
              (C["test2"] + 0.1, 0.0), (C["test2"] + 0.2, 2.5), (C["test2"] + 0.8, 0.0)])
LATCH = box("LatchBar", -1.15, 0.6, 0.05, 0.35, 5.6, 5.8, M_STEEL)
# wires: hot (black) on the left, neutral (white) on the right; half insulation (cut at y = 0) with a copper core and the beads
HX, NX = -0.32, 0.32
CON_Z = 5.9          # contact gap height
HOT_UP = [(PR_X[0], 0, BZ1 - 1.0), (PR_X[0], 0, CON_Z + 0.55), (-0.7, 0, CON_Z + 0.2)]
HOT_DN = [(-0.7, 0, CON_Z - 0.15), (-0.62, 0, CON_Z - 0.8), (HX, 0, 4.8), (HX, 0, 2.4), (-0.6, 0, 1.4), (1.6, 0, 0.9), (BX1 + 0.2, 0, 0.9)]
NEU_UP = [(PR_X[1], 0, BZ1 - 1.0), (PR_X[1], 0, CON_Z + 0.55), (0.7, 0, CON_Z + 0.2)]
NEU_DN = [(0.7, 0, CON_Z - 0.15), (0.62, 0, CON_Z - 0.8), (NX, 0, 4.8), (NX, 0, 2.4), (0.5, 0, 1.6), (1.8, 0, 1.2), (BX1 + 0.2, 0, 1.2)]
WIRES = {}
for nm, up, dn, mi in (("Hot", HOT_UP, HOT_DN, M_HOTINS), ("Neu", NEU_UP, NEU_DN, M_NEUINS)):
    o1, p1 = tube(f"{nm}WireUp", up, 0.16, mi, half=True); o2, p2 = tube(f"{nm}WireDn", dn, 0.16, mi, half=True)
    tube(f"{nm}CoreUp", up, 0.07, M_COPPER); tube(f"{nm}CoreDn", dn, 0.07, M_COPPER)
    WIRES[nm] = (p1, p2)
# contacts: fixed pad on the upper wire, moving pad on the lower wire drops on a trip
PADS = []
for nm, x in (("Hot", -0.7), ("Neu", 0.7)):
    box(f"{nm}PadFixed", x - 0.3, x + 0.3, -0.25, 0.35, CON_Z + 0.08, CON_Z + 0.25, M_COPPER)
    pad = box(f"{nm}PadMove", x - 0.3, x + 0.3, -0.25, 0.35, -0.17, 0.0, M_COPPER); PADS.append(pad)
    bake_loc(pad, lambda t: (0, 0, CON_Z + 0.08 - 0.55 * open_amt(t)))
bake_loc(LATCH, lambda t: (0, 0, -0.55 * open_amt(t)))
# the cord leaves the block at the lower right and runs to the dryer
CORD_PTS = [(BX1 - 0.2, 0.0, 1.05), (BX1 + 2.0, 0.0, 1.0), (6.5, -1.0, 0.45), (10.0, 0.5, 0.45), (12.5, 4.5, 0.45), (14.2, 7.6, 0.8)]
CORD, _ = tube("StudioCord", CORD_PTS, 0.42, M_CORD, seg=16)
CORD_SLEEVE = cyl("CordSleeve", 0.62, 1.2, "X", (BX1 + 0.4, 0.0, 1.05), M_SHELL, seg=20)
# test resistor: a bypass from the hot side (below the coil) to the neutral side (above the coil)
RES_PTS = [(HX, 0, 2.2), (-1.4, -0.1, 2.0), (-1.9, -0.1, 3.4), (-1.6, -0.1, 4.9), (NX + 0.15, 0, 5.1)]
RES_W, _ = tube("TestPath", RES_PTS, 0.05, M_TRACE)
RESISTOR = cyl("TestResistor", 0.22, 0.9, "Z", (-1.9, -0.1, 3.4), M_RES, seg=16)
glow(B_TRACE, [(0, 0.0), (C["fakes"] - 0.01, 0.0), (C["fakes"] + 0.15, 2.0), (C["purpose"] + 0.5, 2.0), (C["press"], 0.0),
               (C["test2"] - 0.01, 0.0), (C["test2"] + 0.1, 2.0), (C["test2"] + 0.8, 0.0)])
glow(B_RES, [(0, 0.0), (C["fakes"] - 0.01, 0.0), (C["fakes"] + 0.15, 1.5), (C["purpose"] + 0.5, 1.5), (C["press"], 0.0),
             (C["test2"] - 0.01, 0.0), (C["test2"] + 0.1, 1.5), (C["test2"] + 0.8, 0.0)])
# sense trace from the coil to the chip (signal pulse)
SIG_PTS = [(1.05, 0.1, 3.4), (1.35, 0.5, 3.0), (1.6, 0.55, 2.4)]
SIG_W, _ = tube("SenseLead", SIG_PTS, 0.05, M_TRACE)
glow(B_CHIP, [(0, 0.0), (C["signal"], 0.0), (C["circuit"], 1.8), (C["electromagnet"] + 0.6, 1.8), (C["snaps"] + 0.6, 0.0),
              (C["test2"] + 0.08, 0.0), (C["test2"] + 0.15, 1.8), (C["test2"] + 0.7, 0.0)])

# ---- beads: current out on the hot wire (gold), back on the neutral (cyan) ----
def chain(*segs):
    pts = []
    for s in segs: pts += [Vector(p) for p in s]
    return Path(pts)
P_HOT = chain(WIRES["Hot"][0], WIRES["Hot"][1])                 # prong -> exit (out to the dryer)
P_NEU = chain(list(reversed(WIRES["Neu"][1])), list(reversed(WIRES["Neu"][0])))   # exit -> prong (back)
FLOW_WINS = [(C["power"] + 0.25, C["snaps"]), (C["reset2"] + 0.2, C["test2"] + 0.25)]
FLOW_WINS = [(a, b) for a, b in FLOW_WINS if not (a >= C["now"] and b <= C["out2"])]
BEAD_HOT = beads("HotBead", P_HOT, 14, 0.12, M_GOLDG, [(C["out"], C["snaps"]), (C["reset2"] + 0.15, C["test2"] + 0.25)], speed=4.0)
BEAD_NEU = beads("NeuBead", P_NEU, 14, 0.12, M_CYANG, [(C["back"], C["out2"]), (C["reset2"] + 0.15, C["test2"] + 0.25)], speed=4.0)
# "don't match": only part of the neutral beads come back
BEAD_NEU2 = beads("NeuBeadLeak", P_NEU, 8, 0.12, M_CYANG, [(C["out2"], C["snaps"])], speed=4.0)
# magnetic fields: one ring of arrows around each wire inside the coil, opposite directions, cancel on "cancel"
def field_ring(name, x, m_, sign):
    root = empty(name, (x, 0.0, 4.75))
    for k in range(6):
        a0 = 2 * math.pi * k / 6
        pts = [(0.5 * math.cos(a0 + sign * u * 0.75), 0.5 * math.sin(a0 + sign * u * 0.75), 0.0) for u in [i / 6 for i in range(7)]]
        bm = bmesh.new(); add_poly(bm, pts, 0.035, seg=6)
        tip = Vector(pts[-1]); d = (Vector(pts[-1]) - Vector(pts[-2])).normalized()
        add_cyl(bm, 0.09, 0.2, "Z", (0, 0, 0), seg=8, r2=0.0)
        bm2 = bmesh.new(); add_cyl(bm2, 0.09, 0.2, "Z", (0, 0, 0.1), seg=8, r2=0.0)
        mesh_obj(f"{name}Arc{k}", bm, m_, parent=root)
        cone = mesh_obj(f"{name}Tip{k}", bm2, m_, parent=root); cone.location = tip
        cone.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    bake_rot(root, lambda t: (0, 0, sign * 3.0 * t))
    return root
FR_H = field_ring("FieldHot", HX, M_GOLDF, -1); FR_N = field_ring("FieldNeu", NX, M_CYANF, 1)
for fr_ in (FR_H, FR_N): windows(fr_, [(C["magnetic"], C["nothing"] + 0.3), (C["match"], C["leak"] + 0.6)])
glow(B_GOLDF, [(0, 3.0), (C["cancel"], 3.0), (C["cancel"] + 0.5, 0.3), (C["match"] - 0.01, 0.3), (C["match"], 3.0)])
glow(B_CYANF, [(0, 3.0), (C["cancel"], 3.0), (C["cancel"] + 0.5, 0.3), (C["match"] - 0.01, 0.3), (C["match"], 1.2)])
# signal pulse coil -> chip
SIGB = beads("SignalBead", Path([Vector(p) for p in SIG_PTS]), 3, 0.09, M_REDG, [(C["signal"] - 0.1, C["circuit"] + 0.2), (C["test2"] + 0.05, C["test2"] + 0.4)], speed=4.5)
# test-leak beads along the bypass
TSTB = beads("TestLeakBead", Path([Vector(p) for p in chaikin([Vector(p) for p in RES_PTS], 3)]), 6, 0.08, M_REDG, [(C["fakes"] + 0.1, C["purpose"] + 0.5), (C["test2"], C["test2"] + 0.3)], speed=3.0)

# ================= generic hair dryer (upright on its handle; nozzle +x; switch slider on the handle front) =================
def make_dryer(name, heat=False):
    root = empty(name)
    prof = [(0.0, -7.6), (2.6, -7.5), (3.8, -7.0), (4.2, -6.0), (4.25, 5.5), (3.6, 7.0), (3.2, 7.2), (2.6, 11.0), (2.3, 11.2), (0.0, 11.2)]
    body = lathe(f"{name}Body", prof, M_DRYER, ang=2 * math.pi, seg=40)
    body.rotation_euler = (0, math.radians(90), 0); body.location = (0, 0, 13.6); par(body, root); body.location = (0, 0, 13.6)
    trim = torus(f"{name}Trim", 4.22, 0.25, M_DRYER2, (0, 0, 0)); par(trim, root); trim.location = (5.4, 0, 13.6); trim.rotation_euler = (0, math.radians(90), 0)
    gr = cyl(f"{name}Grille", 2.7, 0.2, "X", (-7.65, 0, 13.6), M_GRILLE, seg=32); par(gr, root)
    heat_o = cyl(f"{name}Heater", 2.05, 0.15, "X", (11.15, 0, 13.6), M_HEAT if heat else M_GRILLE, seg=28); par(heat_o, root)
    h = rbox(f"{name}Handle", -2.2, 2.2, -1.7, 1.7, 0.0, 11.0, 0.8, M_DRYER); par(h, root); h.rotation_euler = (0, math.radians(-8), 0)
    sl = rbox(f"{name}Switch", -0.5, 0.5, -1.95, -1.6, 6.6, 8.0, 0.15, M_SLIDER); par(sl, root)
    return root, sl
DRY_S, SW_S = make_dryer("StudioDryer", heat=True)
DRY_S.location = (14.5, 8.5, 0.0); DRY_S.rotation_euler = (0, 0, math.radians(-25))
# switch: OFF (down) except ON in the "on or off" beat, heater glows when on
def sw_fn(t):
    on = ease((t - C["on"]) / 0.12) * (1 - ease((t - C["off2"]) / 0.12))
    return (0, 0, 1.0 * on)
bake_loc(SW_S, sw_fn)
glow(B_HEAT, [(0, 0.0), (C["on"] - 0.01, 0.0), (C["on"] + 0.2, 3.5), (C["off2"], 3.5), (C["off2"] + 0.3, 0.0)])
# protective glow on the block in the on/off beat (the block works both ways)
GUARD = box("GuardGlow", BX0 - 0.1, BX1 + 0.1, 1.6, 1.7, BZ0 + 0.3, BZ1 - 0.3, emit_mat("GuardGlowM", (0.30, 0.92, 1.0), 2.0)[0])
windows(GUARD, [(C["on"] - 0.15, C["by"])])

# ================= BATHTUB set (stake: a dryer falls into the tub, the water is electrified, even switched off) =================
X_T = 300.0
TUB_ROOT = empty("TubSet", (X_T, 0, 0))
def tb(name, *a): o = box(name, *a); par(o, TUB_ROOT); return o
tb("TubFloor", -130, 130, -80, 60, -2, 0, M_TILEF)
tb("TubWall", -130, 130, 40, 42, 0, 180, M_TILE)
tb("TubEndL", -80, -72, 0, 40, 0, 55, M_ENAMEL); tb("TubEndR", 72, 80, 0, 40, 0, 55, M_ENAMEL)
tb("TubBack", -80, 80, 32, 40, 0, 58, M_ENAMEL); tb("TubBottom", -80, 80, 0, 40, 0, 6, M_ENAMEL)
tb("TubLedge", -80, 80, 32, 44, 58, 61, M_COUNTER)
TW = tb("TubWaterBody", -72, 72, 0.02, 32, 6, 40, M_WATT)
DRY_T, SW_T = make_dryer("TubDryer")
DRY_T.scale = (1, 1, 1)
p0, r0 = Vector((X_T + 30, 38.0, 61.0)), Vector((0, 0, math.radians(20)))
p1, r1 = Vector((X_T + 22, 24.0, 50.0)), Vector((math.radians(-50), math.radians(10), math.radians(10)))
p2, r2 = Vector((X_T + 12, 3.0, 18.0)), Vector((math.radians(-95), math.radians(15), 0.0))
def dry_t_loc(t):
    u1 = ease((t - C["fell"]) / 0.35); u2 = lin((t - C["fell"] - 0.35) / 0.4); u2 = u2 * u2 * (3 - 2 * u2)
    return tuple(p0.lerp(p1, u1).lerp(p2, u2))
def dry_t_rot(t):
    u1 = ease((t - C["fell"]) / 0.35); u2 = ease((t - C["fell"] - 0.35) / 0.45)
    return tuple(r0.lerp(r1, u1).lerp(r2, u2))
bake_loc(DRY_T, dry_t_loc); bake_rot(DRY_T, dry_t_rot)
CORD_T, _ = tube("TubCord", [(X_T + 30, 38, 61.5), (X_T + 45, 42, 62), (X_T + 70, 41, 75), (X_T + 95, 40.5, 92)], 0.45, M_CORD)
CORD_T2, _ = tube("TubCord2", [(X_T + 12, 3.0, 18.5), (X_T + 14, 10, 30), (X_T + 22, 30, 50), (X_T + 34, 40, 61.5), (X_T + 45, 42, 62), (X_T + 70, 41, 75), (X_T + 95, 40.5, 92)], 0.45, M_CORD)
windows(CORD_T, [(0, C["fell"] + 0.5)]); windows(CORD_T2, [(C["fell"] + 0.5, DUR)])
OUT_T = box("TubOutletPlate", X_T + 90, X_T + 100, 39.6, 40.0, 88, 103, M_PLATE)
TUB_RED = bpy.data.lights.new("TubRed", "POINT"); TUB_RED.color = (1.0, 0.25, 0.15); TUB_RED.shadow_soft_size = 20
TUB_RED_O = bpy.data.objects.new("TubRed", TUB_RED); scene.collection.objects.link(TUB_RED_O); TUB_RED_O.location = (X_T + 5, -25, 35)
for t_, v_ in [(0, 0.0), (C["electrify"] - 0.02, 0.0), (C["electrify"] + 0.25, 7000.0), (C["off"] + 0.4, 7000.0), (C["power"], 0.0)]:
    TUB_RED.energy = v_; TUB_RED.keyframe_insert("energy", frame=F(t_))
SPL_T = box("TubSplashEmitter", X_T - 2, X_T + 26, 6, 26, 39.8, 40.0, M_INV); SPL_T.hide_render = True
spm = fx.particles(SPL_T, "rain", F(C["fell"] + 0.6), F(C["fell"] + 1.0), count=500)
if spm:
    s_ = spm.particle_system.settings; s_.normal_factor = 260.0; s_.lifetime = 22; s_.particle_size = 0.45; s_.effector_weights.gravity = 1.0
    SPL_T.show_instancer_for_render = False

# ================= SINK set (the leak demo + "unplug it first") =================
X_S = 600.0
SINK_ROOT = empty("SinkSet", (X_S, 0, 0))
def sb(name, *a): o = box(name, *a); par(o, SINK_ROOT); return o
sb("SinkFloor", -150, 150, -80, 60, -2, 0, M_TILEF)
sb("SinkWall", -150, 150, 25, 27, 0, 200, M_TILE)
sb("CabinetSide", -45, -42, 0, 25, 0, 84, M_CAB); sb("CabinetSide2", 42, 45, 0, 25, 0, 84, M_CAB)
sb("CabinetBack", -42, 42, 23, 25, 8, 84, M_CABIN); sb("CabinetBase", -45, 45, 0, 25, 0, 8, M_CAB)
sb("CabinetCutFace", -45, 45, -0.3, 0.0, 0, 8, M_CAB)
# countertop with a basin hole (front half removed at y = 0)
CT = box("Countertop", -50, 50, 0.0, 25, 84, 88, M_COUNTER); par(CT, SINK_ROOT)
HOLE = cyl("BasinHoleCut", 17.5, 10, "Z", (0, 8, 86), None, seg=48); HOLE.hide_render = True; HOLE.display_type = "WIRE"; par(HOLE, SINK_ROOT)
boolean(CT, HOLE)
BOWL_PROF = [(17.5, 88.0), (18.2, 88.0), (18.0, 84.0), (16.5, 79.0), (12.5, 75.0), (5.0, 73.2), (2.0, 73.0), (2.0, 72.2), (4.8, 72.2), (12.0, 74.2), (15.6, 78.2), (17.0, 83.5)]
BOWL = lathe("Basin", BOWL_PROF, M_ENAMEL, a0=0.0, ang=math.pi, seg=48, loc=(X_S, 8, 0))
WAT_PROF = [(0.0, 73.3), (4.8, 73.3), (12.0, 75.1), (15.4, 78.9), (16.4, 83.0), (0.0, 83.0)]
SWAT = lathe("SinkWaterBody", WAT_PROF, M_WATS, a0=0.0, ang=math.pi, seg=48, loc=(X_S, 8, 0))
for o_ in (BOWL, SWAT): o_.rotation_euler = (0, 0, 0)
# drain tail piece, P-trap and arm into the wall (metal, cut open): this is the leak's "way home"
DRAIN_PTS = [(X_S, 8.0, 72.5), (X_S, 8.0, 55.0), (X_S, 8.0, 44.0), (X_S + 7, 8.0, 40.0), (X_S + 12, 8.0, 46.0), (X_S + 14, 14.0, 50.0), (X_S + 16, 25.0, 50.0)]
DRAIN, DRAIN_P = tube("DrainPipe", DRAIN_PTS, 2.0, M_CHROME, seg=20, half=True)
FAUCET, _ = tube("Faucet", [(X_S, 22.0, 88.0), (X_S, 22.0, 100.0), (X_S, 18.0, 104.0), (X_S, 12.0, 102.0)], 1.2, M_CHROME, seg=16)
OUT_S = box("SinkOutletPlate", X_S - 31, X_S - 21, 24.6, 25.0, 104, 119, M_PLATE)
for k, x_ in enumerate((X_S - 27.6, X_S - 24.4)): box(f"OutletSlot{k}", x_ - 0.2, x_ + 0.2, 24.5, 24.6, 112.5, 114.5, M_GRILLE)
# the block plug, plugged into the outlet (prongs into the wall), pulled out on "unplug"
PLUG_S = empty("SinkPlug")
pb = rbox("SinkPlugBody", BX0, BX1, BY0, BY1, BZ0, BZ1, 0.9, M_SHELL); par(pb, PLUG_S)
for nm, x, m_ in (("T", -1.35, M_TEST), ("R", 1.35, M_RESET)):
    c_ = cyl(f"SinkPlugBtn{nm}", 0.55, 0.5, "Y", (x, BY0 - 0.2, 3.0), m_, seg=24); par(c_, PLUG_S)
PLUG_S.rotation_euler = (math.radians(-90), 0, 0)
PLUG_IN = Vector((X_S - 26, 24.5 - BZ1, 113.0)); PLUG_OUT = Vector((X_S - 26, 24.5 - BZ1 - 14.0, 108.0))
bake_loc(PLUG_S, lambda t: tuple(PLUG_IN.lerp(PLUG_OUT, ease((t - C["unplug"]) / 0.45))))
# dryer on the counter -> drops into the basin on "drop"
DRY_K, SW_K = make_dryer("SinkDryer")
q0, e0 = Vector((X_S + 30, 12.0, 88.0)), Vector((0, 0, math.radians(20)))
q1, e1 = Vector((X_S + 16, 6.0, 92.0)), Vector((math.radians(-40), 0, math.radians(10)))
q2, e2 = Vector((X_S - 2, 1.5, 79.0)), Vector((math.radians(-85), math.radians(8), 0.0))
T_LAND = C["drop"] + 0.75
def dry_k(t):
    u1 = ease((t - C["drop"]) / 0.35); u2 = lin((t - C["drop"] - 0.35) / 0.4); u2 = u2 * u2
    return tuple(q0.lerp(q1, u1).lerp(q2, u2)), tuple(e0.lerp(e1, u1).lerp(e2, ease((t - C["drop"] - 0.35) / 0.4)))
bake_loc(DRY_K, lambda t: dry_k(t)[0]); bake_rot(DRY_K, lambda t: dry_k(t)[1])
DRY_K.scale = (0.85, 0.85, 0.85)
PI_ = PLUG_IN + Vector((0, -BZ1 + 0.4, -2.0)) * 0 + Vector((2.2, -7.0, -2.5))
CORD_A, _ = tube("SinkCordA", [(X_S - 23.8, 17.5, 111.0), (X_S - 22, 16.0, 100.0), (X_S - 15, 18.0, 89.0), (X_S + 5, 19.0, 88.4), (X_S + 30, 14.0, 88.5)], 0.4, M_CORD)
CORD_B, _ = tube("SinkCordB", [(X_S - 23.8, 17.5, 111.0), (X_S - 22, 16.0, 100.0), (X_S - 15, 18.0, 89.0), (X_S - 4, 16.0, 88.6), (X_S - 3, 6.0, 86.0), (X_S - 2, 1.5, 79.5)], 0.4, M_CORD)
CORD_C, _ = tube("SinkCordC", [(X_S - 23.8, 3.5, 106.0), (X_S - 22, 6.0, 96.0), (X_S - 15, 15.0, 89.0), (X_S - 4, 16.0, 88.6), (X_S - 3, 6.0, 86.0), (X_S - 2, 1.5, 79.5)], 0.4, M_CORD)
windows(CORD_A, [(0, T_LAND - 0.3)]); windows(CORD_B, [(T_LAND - 0.3, C["unplug"] + 0.22)]); windows(CORD_C, [(C["unplug"] + 0.22, DUR)])
# leak beads: from the dryer through the water, down the drain pipe
LEAK_P = Path([Vector((X_S + 2, 10, 76)), Vector((X_S + 1, 8.0, 74.5)), Vector((X_S, 8.0, 72.5))] + [Vector(p) for p in DRAIN_P[1:]])
LEAKB = beads("LeakBead", LEAK_P, 16, 0.55, M_REDG, [(C["leaks"], C["out2"]), (C["still"] + 0.1, C["unplug"] + 0.3)], speed=26.0)
SINK_RED = bpy.data.lights.new("SinkRed", "POINT"); SINK_RED.color = (1.0, 0.25, 0.15); SINK_RED.shadow_soft_size = 8
SINK_RED_O = bpy.data.objects.new("SinkRed", SINK_RED); scene.collection.objects.link(SINK_RED_O); SINK_RED_O.location = (X_S, -12, 84)
for t_, v_ in [(0, 0.0), (C["leaks"] - 0.02, 0.0), (C["leaks"] + 0.3, 2500.0), (C["out2"], 2500.0), (C["out2"] + 0.05, 0.0),
               (C["still"], 0.0), (C["still"] + 0.3, 1800.0), (C["unplug"] + 0.25, 1800.0), (C["first"], 0.0)]:
    SINK_RED.energy = v_; SINK_RED.keyframe_insert("energy", frame=F(t_))
SPL_S = cyl("SinkSplashEmitter", 9.0, 0.1, "Z", (X_S + 2, 9, 83.2), M_INV, seg=16); SPL_S.hide_render = True
spm2 = fx.particles(SPL_S, "rain", F(T_LAND - 0.05), F(T_LAND + 0.25), count=350)
if spm2:
    s_ = spm2.particle_system.settings; s_.normal_factor = 160.0; s_.lifetime = 20; s_.particle_size = 0.3; s_.effector_weights.gravity = 1.0
    SPL_S.show_instancer_for_render = False
# toiletries on the counter: kicked over when the dryer goes in (rigid body)
BOTTLES = []
for k, (bx, by, h_, r_) in enumerate([(20.0, 19.0, 14.0, 2.6), (25.5, 20.5, 10.0, 2.2), (-30.0, 18.0, 12.0, 3.0), (-36.0, 12.0, 8.0, 2.4)]):
    col = [(0.20, 0.55, 0.75), (0.85, 0.85, 0.80), (0.75, 0.35, 0.25), (0.35, 0.65, 0.45)][k]
    mb, _ = mat(f"Bottle{k}", col, rough=0.3)
    o = cyl(f"Bottle{k}", r_, h_, "Z", (X_S + bx, by, 88.0 + h_ / 2 + 0.02), mb, seg=20); BOTTLES.append(o)
CT_P = box("CounterPassive", X_S - 50, X_S + 50, 0, 25, 87.0, 88.0, M_INV); CT_P.hide_render = True
fx.rigid(BOTTLES[:2], passive=[CT_P], mass=0.3, friction=0.5, bounce=0.2)
for k, o in enumerate(BOTTLES[:2]):
    try:
        rb = o.rigid_body; rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=1)
        f0 = F(C["drop"] + 0.15) + k * 2
        loc0 = o.location.copy(); o.keyframe_insert("location", frame=1); o.keyframe_insert("location", frame=f0)
        o.location = loc0 + Vector((-0.6, -0.5, 0.25)); o.keyframe_insert("location", frame=f0 + 2)
        rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 2)
        rb.kinematic = False; o.keyframe_insert("rigid_body.kinematic", frame=f0 + 3)
    except Exception as e: print("[build] bottle kinematic skipped", e)
# Mantaflow: the faucet stream filling the basin around the drop (short shot, laptop --bake-fluid)
M_FLW, _, _ = water_sec("FluidWater")
FL_DOM = box("SinkFluidDomain", X_S - 17, X_S + 17, 8.0, 22.0, 73.0, 102.0, M_FLW)
FL_IN = cyl("SinkFluidInflow", 0.9, 1.5, "Z", (X_S, 12.0, 100.5), M_FLW, seg=12)
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=64, start=F(C["now"] - 0.1), end=F(C["sink"] + 2.0), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_IN.hide_render = True
windows(FL_DOM, [(C["now"] - 0.1, C["some"])] if FLUID_BAKE else [])
STREAM = cyl("FaucetStream", 0.55, 19.0, "Z", (X_S, 12.0, 92.5), M_WATS, seg=12)
windows(STREAM, [(0, C["drop"] + 0.2)] if not FLUID_BAKE else [])

# ================= CHART set (the history numbers) =================
X_C = 900.0
box("ChartFloor", X_C - 150, X_C + 150, -80, 80, -2, 0, M_FLOOR); box("ChartBack", X_C - 150, X_C + 150, 60, 61, 0, 150, M_FLOOR)
U_ = 4.0   # cm per death
BAR_B = box("BarBefore", X_C - 32, X_C - 12, -10, 10, 0, 18 * U_, M_BAR)
BAR_H = box("BarHalf", X_C - 32.3, X_C - 11.7, -10.3, 10.3, 0, 9 * U_, M_BARR)
BAR_A = box("Bar1992", X_C + 12, X_C + 32, -10, 10, 0, 2 * U_, M_BARC)
BASE = box("ChartBase", X_C - 60, X_C + 60, -16, 16, 0, 0.6, M_STEEL)
MARK = box("Marker1991", X_C - 1.0, X_C + 1.0, -1.0, 1.0, 0.6, 70, emit_mat("MarkerM", (0.98, 0.74, 0.27), 4.0)[0])
bake_scale(BAR_B, lambda t: (1, 1, max(0.01, ease((t - C["about"]) / 0.5))))
windows(BAR_H, [(C["half"], DUR)])
bake_scale(BAR_H, lambda t: (1, 1, max(0.01, ease((t - C["half"]) / 0.4))))
bake_scale(MARK, lambda t: (1, 1, max(0.01, ease((t - C["y1991"]) / 0.4))))
bake_scale(BAR_A, lambda t: (1, 1, max(0.01, ease((t - C["y1992"]) / 0.45))))
glow(B_BAR, [(0, 0.2)]); glow(B_BARR, [(0, 0.6)]); glow(B_BARC, [(0, 1.2), (C["two"], 1.2), (C["two"] + 0.2, 3.0), (C["year2"] + 0.4, 1.2)])

# ================= fx: hdri light, glare, sparks, scatter =================
fx.hdri("interior", strength=0.35, rotation_deg=40.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
SPK = box("ContactSparkEmitter", -1.0, 1.0, -0.3, 0.0, CON_Z - 0.2, CON_Z + 0.1, M_INV); SPK.hide_render = True
for t0_ in (C["snaps"], C["test2"] + 0.25):
    pm_ = fx.particles(SPK, "sparks", F(t0_), F(t0_ + 0.2), count=120)
    if pm_:
        s_ = pm_.particle_system.settings; s_.particle_size = 0.03; s_.normal_factor = 6.0; s_.lifetime = 10
        SPK.show_instancer_for_render = False
# water droplets scattered on the countertop (Geometry Nodes)
M_CLEAR = bpy.data.materials.new("Clear")
try: M_CLEAR.use_nodes = True
except Exception: pass
_out = next(n for n in M_CLEAR.node_tree.nodes if n.type == "OUTPUT_MATERIAL")
_tr = M_CLEAR.node_tree.nodes.new("ShaderNodeBsdfTransparent"); M_CLEAR.node_tree.links.new(_tr.outputs[0], _out.inputs["Surface"])
DZ = box("DropletZone", X_S - 48, X_S + 48, 1.0, 22.0, 88.0, 88.01, M_CLEAR)
dme = sphere_mesh("DropletProto", 0.45, sub=2); M_DROP, _, _ = water_sec("DropletWater")
DROP = obj_from("DropletProto", dme, M_DROP); DROP.scale = (1, 1, 0.35)
bpy.context.view_layer.update()
fx.scatter(DZ, DROP, density=0.06, scale_min=0.4, scale_max=1.3, seed=7)

# ================= lights =================
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.95, 0.9)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("StudioKey", (-14, -18, 22), 14.0, 1400.0, rot=(math.radians(50), 0, math.radians(-35)))
area("StudioRim", (12, 10, 18), 8.0, 900.0, rot=(math.radians(-50), 0, math.radians(140)), color=(0.45, 0.85, 1.0))
area("StudioTop", (2, 0, 30), 18.0, 900.0)
area("BlockInside", (0, -8, 5), 5.0, 30.0, rot=(math.radians(90), 0, 0))
area("TubTop", (X_T, -20, 175), 120.0, 30000.0, color=(0.85, 0.9, 1.0))
area("TubFront", (X_T, -140, 90), 80.0, 9000.0, rot=(math.radians(80), 0, 0), color=(0.7, 0.8, 1.0))
area("SinkTop", (X_S, -10, 170), 100.0, 26000.0)
area("SinkFront", (X_S, -120, 100), 80.0, 7000.0, rot=(math.radians(80), 0, 0))
area("UnderSink", (X_S, -30, 40), 40.0, 3000.0, rot=(math.radians(80), 0, 0))
area("ChartTop", (X_C, -60, 140), 120.0, 26000.0)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 6000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (5.0, -19.0, 11.0), (0.2, 0.0, 4.6), 50),
    (C["safety"], (3.5, -16.0, 9.0), (0.0, 0.0, 4.4), 50),
    (C["its"] - 0.05, (3.0, -15.0, 8.6), (0.0, 0.0, 4.4), 50),
    (C["its"], (X_T + 22, -140, 78), (X_T + 22, 0, 46), 40, "cut"),
    (C["fell"] - 0.05, (X_T + 24, -122, 74), (X_T + 24, 0, 46), 40),
    (C["fell"], (X_T + 25, -95, 72), (X_T + 16, 10, 38), 35, "cut"),
    (C["even"] - 0.05, (X_T + 22, -85, 66), (X_T + 14, 10, 34), 35),
    (C["even"], (X_T + 16, -48, 48), (X_T + 12, 12, 22), 35, "cut"),
    (C["power"] - 0.05, (X_T + 15, -44, 46), (X_T + 12, 12, 22), 35),
    (C["power"], (0.8, -13.5, 7.4), (0.0, 0.3, 5.4), 50, "cut"),
    (C["both"], (0.6, -12.0, 6.0), (0.0, 0.3, 4.2), 50),
    (C["coil"], (0.4, -8.5, 6.4), (0.0, 0.2, 3.7), 55),
    (C["now"] - 0.05, (0.3, -7.6, 6.6), (0.0, 0.2, 3.6), 55),
    (C["now"], (X_S + 10, -130, 128), (X_S + 5, 10, 90), 40, "cut"),
    (C["leaks"], (X_S + 4, -82, 108), (X_S + 2, 10, 82), 40),
    (C["another"], (X_S + 6, -90, 80), (X_S + 5, 10, 62), 40),
    (C["out2"] - 0.05, (X_S + 6, -92, 76), (X_S + 5, 10, 60), 40),
    (C["out2"], (0.2, -11.0, 6.0), (0.0, 0.2, 3.9), 50, "cut"),
    (C["signal"], (1.3, -10.0, 4.4), (0.9, 0.3, 2.9), 50),
    (C["fires"], (1.3, -10.0, 4.6), (0.9, 0.3, 3.1), 50),
    (C["electromagnet"] + 0.2, (1.8, -10.0, 6.6), (0.9, 0.2, 5.3), 52),
    (C["contacts"], (0.6, -9.5, 7.0), (0.2, 0.2, 5.7), 52),
    (C["power2"] - 0.05, (0.5, -10.0, 7.0), (0.2, 0.2, 5.6), 52),
    (C["power2"], (-1.5, -17.0, 6.5), (0.0, 0.0, 3.9), 45, "cut"),
    (C["dryer_s"] + 0.6, (1.5, -16.0, 6.0), (0.0, 0.0, 3.9), 45),
    (C["about"], (X_C, -205, 52), (X_C, 0, 38), 35, "cut"),
    (C["on"] - 0.2, (X_C + 2, -190, 50), (X_C + 2, 0, 38), 35),
    (C["on"] - 0.15, (6.0, -38.0, 16.0), (6.5, 3.0, 6.5), 35, "cut"),
    (C["by"] - 0.05, (7.5, -35.0, 15.0), (6.5, 3.0, 6.5), 35),
    (C["by"], (X_C + 2, -185, 46), (X_C + 2, 0, 30), 35, "cut"),
    (C["still"] - 0.05, (X_C + 8, -170, 42), (X_C + 6, 0, 28), 35),
    (C["still"], (X_S - 6, -120, 122), (X_S - 10, 15, 96), 38, "cut"),
    (C["does"] - 0.05, (X_S - 12, -105, 118), (X_S - 14, 15, 100), 38),
    (C["does"], (7.0, -24.0, 10.0), (3.0, 0.0, 4.8), 40, "cut"),
    (DUR, (4.5, -17.5, 8.4), (2.0, 0.0, 4.6), 40),
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
FST = [max(1.4, min(16.0, 0.12 * (cl - ct).length ** 1.2)) for cl, ct in zip(cam_loc, cam_tgt)]
bake_scalar(cam_d, "dof.aperture_fstop", FST)
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 4; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0, min(2.0e5, 10.0 * ((cl - ct).length / 5.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (0.8, 1.0, 0)

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
scene.view_settings.exposure = float(arg("--exposure", "-0.3"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["drop"]) - 5, F(C["out2"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "prongs": (0.0, 0.0, BZ1 + 1.8), "coil": (-1.05, 0.0, 3.6), "hot": (HX, 0.0, 4.5), "neu": (NX, 0.0, 4.5), "lead": (1.35, 0.5, 3.0),
    "chip": (1.65, 0.55, 2.3), "sol": (2.45, 0.2, 5.6), "contacts": (-0.7, -0.2, CON_Z), "test": (-1.35, BTN_Y - 0.7, BTN_Z),
    "reset": (1.35, BTN_Y - 0.7, BTN_Z), "resistor": (-1.9, -0.1, 3.4), "block": (0.0, -1.9, 5.0), "switch": (14.5, 6.7, 7.3),
    "tub": (X_T - 30, 0.0, 30.0), "dryer_t": (X_T + 12, 16.0, 26.0), "sinkw": (X_S - 8, 4.0, 80.0), "drain": (X_S + 1, 8.0, 50.0),
    "outlet": (X_S - 26, 18.0, 113.0), "bar_b": (X_C - 22, -10.0, 18 * U_ + 4), "bar_h": (X_C - 22, -10.3, 4.5 * U_),
    "bar_a": (X_C + 22, -10.0, 2 * U_ + 4), "mark": (X_C, 0.0, 72.0),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "tub": RR(*T_TUB), "flow": RR(*T_FLOW), "sink": RR(*T_SINK), "trip": RR(*T_TRIP), "chart": RR(*T_CHART),
          "onoff": RR(*T_ONOFF), "chart2": RR(*T_CHART2), "unplug": RR(*T_UNPLUG), "cta": RR(*T_CTA),
          "lid_off": round(C["safety"], 3), "tub_splash": round(C["fell"] + 0.6, 3), "sink_land": round(T_LAND, 3),
          "snap": round(C["snaps"], 3), "pop1": round(C["snaps"] + 0.06, 3), "test1": round(C["fakes"], 3), "reset_press": round(C["reset2"], 3),
          "test2": round(C["test2"], 3), "snap2": round(C["test2"] + 0.25, 3), "plunger1": round(C["electromagnet"], 3),
          "plunger2": round(C["test2"] + 0.18, 3), "unplug_pull": round(C["unplug"], 3), "switch_on": round(C["on"], 3), "switch_off": round(C["off2"], 3),
          "lid_back": round(C["does"] + 0.1, 3)}
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
