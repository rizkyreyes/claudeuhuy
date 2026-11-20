# Hydro dam power (3d-33): how a dam makes electricity. Claim-first hook ("This dam makes electricity without burning a thing.") on a
# cut-open dam in a desert canyon: water beads fall through the penstock, a red pressure pulse = stake (shutting the pipes too fast can
# burst them) -> the lake glows gold (stored energy, height arrow) -> intake tower, water enters the 30 ft penstock -> camera rides the
# drop (~500 ft) -> spiral casing (x-ray), beads swirl -> wicket gate ring opens, runner spins -> 90%+ -> gates slam shut, flow stops,
# red water-hammer pulse runs back up the pipe -> 1950 what-if set: an old riveted pipe on a hillside bursts (rigid body + spray) ->
# gates close gradually -> tilt up the shaft -> generator: half stator with copper bars, 300+ ton rotor with red/blue poles spins ->
# cyan electrons run through the copper -> transformer on the powerhouse roof, beads up the lines -> draft tube widens, beads slow,
# water returns to the river (Mantaflow outflow, laptop bake) -> aerial, 17 -> push into the elevator shaft in the dam (CTA question).
# Illustrative (1 unit = 1 m): generic concrete gravity dam ~120 m, one turbine unit drawn (Hoover has 17), penstock drawn in the section
# plane under the dam (Hoover's run through canyon-wall tunnels), beads oversized. No logos, no people, no real place copied.
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
random.seed(33)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("this", "This"), ("burning", "burning"), ("lets", "lets"), ("fall", "fall,"), ("pipes", "pipes"), ("burst0", "burst"), ("lake", "lake"),
        ("stored", "stored"), ("high", "high."), ("at", "At"), ("hoover", "Hoover"), ("intake", "intake"), ("penstocks", "penstocks,"),
        ("thirty", "thirty"), ("drops", "drops"), ("five", "five"), ("speed", "speed."), ("then", "Then"), ("spiral", "spiral"),
        ("turbine", "turbine."), ("ring", "ring"), ("wicket", "wicket"), ("aims", "aims"), ("blades", "blades,"), ("runner", "runner"),
        ("spins", "spins."), ("good", "Good"), ("ninety", "ninety"), ("percent", "percent"), ("energy", "energy."), ("but", "But"), ("slam", "slam"),
        ("stop", "Stop"), ("hammers", "hammers"), ("pipe", "pipe."), ("japan", "Japan,"), ("y1950", "1950,"), ("burst", "burst"),
        ("so", "So"), ("close", "close"), ("gradually", "gradually."), ("shaft", "shaft"), ("generator", "generator."), ("rotor", "rotor"),
        ("electromagnets", "electromagnets,"), ("three", "three"), ("spins2", "spins"), ("coils", "coils"), ("copper", "copper"),
        ("moving", "Moving"), ("electrons", "electrons"), ("electricity", "electricity."), ("transformer", "transformer"),
        ("lines", "lines."), ("water2", "water"), ("slows", "slows"), ("draft", "draft"), ("returns", "returns"), ("river", "river,"), ("lower", "lower."),
        ("hoover2", "Hoover"), ("seventeen", "seventeen"), ("would", "Would"), ("elevator", "elevator"), ("damq", "dam?"),
        ("tell", "Tell"), ("comments", "comments.")]
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
CL = coll("Dam")
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
T_HOOK = (0.0, C["lake"]); T_LAKE = (C["lake"], C["at"]); T_INTAKE = (C["at"], C["drops"]); T_DROP = (C["drops"], C["then"])
T_SPIRAL = (C["then"], C["ring"]); T_GATES = (C["ring"], C["good"]); T_EFF = (C["good"], C["but"]); T_HAMMER = (C["but"], C["japan"])
T_1950 = (C["japan"], C["so"]); T_SLOW = (C["so"], C["shaft"]); T_SHAFT = (C["shaft"], C["rotor"]); T_GEN = (C["rotor"], C["moving"])
T_ELEC = (C["moving"], C["transformer"]); T_XF = (C["transformer"], C["water2"]); T_DRAFT = (C["water2"], C["hoover2"])
T_WIDE = (C["hoover2"], C["would"]); T_CTA = (C["would"], DUR)

# ================= materials =================
def strata(name, cols, scale=0.045, bump=0.35):
    """rock with horizontal strata bands (world z) + noise distortion + bump."""
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
    L.new(cr.outputs[0], mx.inputs[6]); L.new(nz.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
M_ROCK = strata("CanyonRock", [(0.30, 0.13, 0.06), (0.45, 0.22, 0.10), (0.36, 0.17, 0.08), (0.52, 0.30, 0.16)], scale=0.03)
M_ROCKS = strata("RockSection", [(0.12, 0.07, 0.05), (0.22, 0.12, 0.07), (0.16, 0.10, 0.07), (0.28, 0.17, 0.10)], scale=0.05)
M_CONC, _ = mat("DamConcrete", (0.46, 0.45, 0.42), rough=0.8, noise=0.4)
M_CONC2, _ = mat("PowerhouseConcrete", (0.40, 0.39, 0.37), rough=0.7, noise=0.6)
M_STEEL, B_STEEL = mat("PenstockSteel", (0.30, 0.31, 0.33), rough=0.35, metallic=0.85, emit_rgb=(0.30, 0.92, 1.0))
M_STEELIN, B_STEELIN = mat("PenstockInner", (0.16, 0.17, 0.18), rough=0.5, metallic=0.6, emit_rgb=(1.0, 0.18, 0.10))
M_SPIRAL, B_SPIRAL = mat("SpiralCasing", (0.20, 0.42, 0.55), rough=0.3, metallic=0.6, emit_rgb=(0.30, 0.92, 1.0))
M_GATE, B_GATE = mat("WicketGate", (0.75, 0.62, 0.25), rough=0.35, metallic=0.8, emit_rgb=(0.98, 0.74, 0.27))
M_RUNNER, B_RUNNER = mat("Runner", (0.72, 0.74, 0.76), rough=0.2, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_DARK, _ = mat("DarkSteel", (0.10, 0.11, 0.12), rough=0.45, metallic=0.7)
M_IRON, _ = mat("StatorIron", (0.22, 0.24, 0.27), rough=0.4, metallic=0.75)
M_PAINTG, _ = mat("GenPaint", (0.62, 0.12, 0.08), rough=0.45, metallic=0.2)
M_RED, _ = mat("PoleRed", (0.60, 0.08, 0.06), rough=0.45)
M_BLUE, _ = mat("PoleBlue", (0.06, 0.14, 0.55), rough=0.45)
M_CU, B_CU = mat("Copper", (0.85, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_TANK, _ = mat("XfTank", (0.30, 0.33, 0.32), rough=0.5, metallic=0.3)
M_PORC, _ = mat("Porcelain", (0.36, 0.20, 0.12), rough=0.15)
M_WIRE, B_WIRE = mat("LineWire", (0.55, 0.57, 0.60), rough=0.3, metallic=0.9, emit_rgb=(0.30, 0.92, 1.0))
M_GALV, _ = mat("Galvanized", (0.58, 0.60, 0.62), rough=0.35, metallic=0.85)
M_OLD, B_OLD = mat("OldRivetedSteel", (0.22, 0.13, 0.08), rough=0.7, metallic=0.5, noise=3.0, emit_rgb=(1.0, 0.18, 0.10))
M_HILL, _ = mat("Hillside", (0.12, 0.16, 0.08), rough=0.95, noise=0.2)
M_SADDLE, _ = mat("Saddle", (0.45, 0.44, 0.42), rough=0.85)
M_SHRUB, _ = mat("Shrub", (0.16, 0.20, 0.08), rough=0.9, noise=1.5)
M_BOULDER, _ = mat("Boulder", (0.38, 0.22, 0.13), rough=0.95, noise=0.8)
M_CAR, B_CAR = mat("ElevatorCar", (0.80, 0.80, 0.78), rough=0.3, metallic=0.5, emit_rgb=(0.98, 0.74, 0.27))
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 6.0)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 7.0)
M_REDG, B_REDG = emit_mat("RedGlow", (1.0, 0.18, 0.08), 8.0)
M_ELEC, B_ELEC = emit_mat("ElectronGlow", (0.30, 0.92, 1.0), 10.0)
M_LAKE, B_LAKE, _V = water_sec("LakeWater", glow_rgb=(0.98, 0.74, 0.27), vol_rgb=(0.05, 0.30, 0.42), dens=0.03)
M_RIVER, B_RIVER, _V2 = water_sec("RiverWater", glow_rgb=(0.30, 0.92, 1.0), vol_rgb=(0.12, 0.42, 0.50), dens=0.02)

# ================= world layout (section plane y = 0, the viewer is at -y) =================
H, LAKE_Z, CREST_W, TOE_X = 120.0, 110.0, 12.0, 100.0
TX, TZ = 140.0, -50.0                 # turbine axis (x) and runner centre height
RIVER_Z, BED_Z = -22.0, -70.0         # tailrace water level and riverbed downstream
ROCK_A = box("RockUpstream", -700, 112, 0, 140, -130, 0, M_ROCKS)
ROCK_B = box("RockDownstream", 176, 1000, 0, 140, -130, BED_Z, M_ROCKS)
ROCK_C = box("RockUnderPowerhouse", 112, 176, 0, 140, -130, -74, M_ROCKS)
CLIFF = box("CanyonBackWall", -700, 1000, 90, 160, -130, 175, M_ROCK)
RIM = box("CanyonRim", -700, 1000, 160, 1400, 160, 175, M_ROCK)
# dam: gravity section extruded across the canyon (y 0..90)
bm = bmesh.new()
prof = [(0, 0), (TOE_X, 0), (CREST_W, H), (0, H)]
v0 = [bm.verts.new((x, 0, z)) for x, z in prof]; v1 = [bm.verts.new((x, 90, z)) for x, z in prof]
bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
for i in range(4):
    j = (i + 1) % 4; bm.faces.new([v0[i], v1[i], v1[j], v0[j]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
DAM = mesh_obj("Dam", bm, M_CONC)
PARAPET = box("DamParapet", -0.6, CREST_W + 0.6, 0, 90, H, H + 1.6, M_CONC)
ROADW = box("CrestRoad", 0.4, CREST_W - 0.4, 0, 90, H + 0.05, H + 0.25, M_DARK)
# elevator shaft cut into the section (CTA) + glowing car
SHAFT_CUT = box("ElevatorShaftCut", 3.0, 8.0, -2.0, 5.0, 4.0, H + 3.0, None); SHAFT_CUT.hide_render = True; SHAFT_CUT.display_type = "WIRE"
boolean(DAM, SHAFT_CUT, "ElevatorShaft"); boolean(PARAPET, SHAFT_CUT, "ElevatorShaft")
CAR = box("ElevatorCar", 3.4, 7.6, 0.3, 4.6, 0, 3.2, M_CAR)
CAR_Z = PW([(0, H - 3.4), (C["elevator"], H - 3.4), (DUR, H - 3.4 - 55.0)])
bake_loc(CAR, lambda t: (0, 0, CAR_Z(t)))
glow(B_CAR, [(0, 0.0), (C["would"], 0.0), (C["elevator"], 3.0), (DUR, 3.0)])
# lake + tailrace water
LAKE = box("Lake", -700, -0.05, 0.02, 89.9, 0.02, LAKE_Z, M_LAKE)
LAKE_TOP = box("LakeSurface", -700, -0.05, 0.02, 89.9, LAKE_Z - 0.05, LAKE_Z, M_RIVER)
RIVER = box("Tailrace", 176.05, 1000, 0.02, 89.9, BED_Z + 0.02, RIVER_Z, M_RIVER)
# intake tower in the lake (half, hollow, cut at y = 0)
TWX = -35.0
TOWER = lathe("IntakeTower", tube_prof(4.6, 7.0, -2.0, H + 8.0), M_CONC2, a0=0.0, ang=math.pi, seg=48, loc=(TWX, 0, 0))
TOWER_CAP = lathe("IntakeTowerCap", tube_prof(0.0, 8.0, H + 8.0, H + 11.0), M_CONC2, a0=0.0, ang=math.pi, seg=48, loc=(TWX, 0, 0))
bm = bmesh.new()
for k in range(6):                                   # dark intake ports around the tower
    a = math.pi * (k + 0.5) / 6
    add_box(bm, -1.4, 1.4, -0.3, 0.3, 66.0, 76.0)
PORTS = []
for k in range(6):
    a = math.pi * (k + 0.5) / 6
    p_ = box(f"IntakePort{k}", -1.3, 1.3, -0.4, 0.4, 66.0, 76.0, M_DARK); p_.location = (TWX + 7.05 * math.cos(a), 7.05 * math.sin(a), 0)
    p_.rotation_euler = (0, 0, a + math.pi / 2); PORTS.append(p_)
bm.free()

# ================= penstock: tower -> under the dam -> turbine (in the section plane) =================
P_RAW = [(TWX, 0, 72.0), (TWX, 0, -14.0), (TWX + 14, 0, -24.0), (96.0, 0, -50.0), (118.0, 0, TZ), (TX - 10.0, 0, TZ)]
P_PTS = chaikin(P_RAW, 4); P_PTS[0] = Vector(P_RAW[0]); P_PTS[-1] = Vector(P_RAW[-1])
P_R = interp_r(P_PTS, [(0, 4.6), (0.82, 4.6), (1.0, 3.3)])
PEN = half_pipe("Penstock", P_PTS, P_R, M_STEEL)
PEN_IN = half_pipe("PenstockInner", P_PTS, [r * 0.97 for r in P_R], M_STEELIN)
PEN_CUT = cutter("PenstockCutter", P_PTS[3:], [r + 0.6 for r in P_R[3:]])
boolean(ROCK_A, PEN_CUT, "PenstockTunnel")
glow(B_STEEL, [(0, 0.0), (C["penstocks"] - 0.01, 0.0), (C["penstocks"] + 0.2, 1.6), (C["drops"] + 0.4, 1.6), (C["then"], 0.0), (DUR, 0.0)])
# red pressure glow on the pipe's inner wall: hook stake + water hammer
glow(B_STEELIN, [(0, 0.0), (C["burst0"] - 0.3, 0.0), (C["burst0"], 3.0), (C["lake"] - 0.05, 3.0), (C["lake"], 0.0),
                 (C["hammers"] - 0.01, 0.0), (C["hammers"] + 0.25, 3.5), (C["japan"] - 0.05, 2.0), (C["japan"], 0.0), (DUR, 0.0)])

# ================= spiral casing (x-ray), wicket gates, runner =================
def spiral_pts(n=80):
    out = []
    for i in range(n + 1):
        u = i / n; th = math.pi - 2 * math.pi * 0.92 * u
        R = 10.0 - 3.4 * u
        out.append(Vector((TX + R * math.cos(th), R * math.sin(th), TZ)))
    return out
SP_PTS = spiral_pts()
SP_R = [3.3 - 1.9 * (i / (len(SP_PTS) - 1)) for i in range(len(SP_PTS))]
bm = sweep_bm(SP_PTS, SP_R, 28, cap=False); cut_front(bm, 0.0, fill=False)
SPIRAL = mesh_obj("SpiralCasing", bm, M_SPIRAL)
try: SPIRAL.data.shade_smooth()
except Exception: pass
B_SPIRAL.inputs["Alpha"].default_value = 1.0
keyval(B_SPIRAL.inputs["Alpha"], [(0, 1.0), (C["then"] - 0.01, 1.0), (C["spiral"], 0.35), (C["ring"] + 0.5, 0.35), (C["ring"] + 1.2, 1.0), (DUR, 1.0)])
glow(B_SPIRAL, [(0, 0.0), *pulse(C["spiral"], 1.2, hold=1.6), (DUR, 0.0)])
# wicket gates: 20 blades on a ring, rotate open/shut about their own vertical axis
NG, GR = 20, 5.4
GATE_OPEN = math.radians(32)
def gate_angle(t):
    keys = [(0, 1.0), (C["slam"] - 0.01, 1.0), (C["slam"] + 0.15, 0.0), (C["so"] - 0.01, 0.0), (C["so"] + 0.3, 1.0),
            (C["close"], 1.0), (C["gradually"] + 0.9, 0.0), (C["shaft"] + 0.1, 0.0), (C["shaft"] + 1.0, 1.0), (DUR, 1.0)]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t <= t1: return v0 + (v1 - v0) * (lin((t - t0) / (t1 - t0)) if t1 > t0 else 1)
    return keys[-1][1]
GATES = []
gate_me = None
for k in range(NG):
    a = 2 * math.pi * k / NG
    g = box(f"WicketGate{k}", -1.05, 1.05, -0.16, 0.16, TZ - 1.4, TZ + 1.4, M_GATE)
    g.location = (TX + GR * math.cos(a), GR * math.sin(a), 0)
    base = a + math.pi / 2
    bake(g, "rotation_euler", 2, [base + GATE_OPEN * gate_angle(t) for t in TS]); GATES.append(g)
RING_TOP = lathe("GateRingTop", tube_prof(4.4, 7.0, TZ + 1.4, TZ + 1.9), M_DARK, a0=0.0, ang=math.pi, seg=48, loc=(TX, 0, 0))
RING_BOT = lathe("GateRingBottom", tube_prof(4.4, 7.0, TZ - 1.9, TZ - 1.4), M_DARK, a0=0.0, ang=math.pi, seg=48, loc=(TX, 0, 0))
glow(B_GATE, [(0, 0.0), *pulse(C["wicket"], 2.0, hold=1.0), *pulse(C["slam"], 3.0, hold=0.8), *pulse(C["close"], 2.0, hold=1.2), (DUR, 0.0)])
# flow (0..1): water speed + spin speed share it
def flow(t):
    g = gate_angle(t)
    return g
FLOW_INT = []; acc = 0.0
for t in TS: FLOW_INT.append(acc); acc += flow(t) / FPS
def flow_int(t): return FLOW_INT[max(0, min(len(TS) - 1, int(round(t * FPS))))]
# runner: hub + 13 curved blades, spins with the flow (rotor uses the same angle; illustrative speed, not a real rpm)
RUN = empty("Runner", (TX, 0, TZ))
bm = bmesh.new(); add_cyl(bm, 1.2, 3.6, "Z", (0, 0, 0.2), 32); add_cyl(bm, 3.9, 0.35, "Z", (0, 0, 1.9), 48, r2=3.6)
r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=3.2, radius2=1.6, depth=1.0); bmesh.ops.translate(bm, verts=r_["verts"], vec=(0, 0, -1.9))
for k in range(13):
    a = 2 * math.pi * k / 13
    vs = add_box(bm, 1.1, 3.8, -0.07, 0.07, -1.7, 1.7)
    M = Matrix.Rotation(a, 4, "Z") @ Matrix.Rotation(math.radians(28), 4, "X")
    bmesh.ops.transform(bm, matrix=M, verts=vs)
RUNNER = mesh_obj("RunnerMesh", bm, M_RUNNER, parent=RUN)
SPIN = 2 * math.pi * 0.75
bake(RUN, "rotation_euler", 2, [-SPIN * flow_int(t) for t in TS])
glow(B_RUNNER, [(0, 0.0), *pulse(C["runner"], 1.0, hold=1.2), *pulse(C["ninety"], 1.4, hold=1.6), (DUR, 0.0)])
SHAFT = cyl("Shaft", 1.0, 34.0, "Z", (0, 0, 0), M_GALV, seg=32); par(SHAFT, RUN); SHAFT.location = (0, 0, 2.0 + 17.0)
# draft tube: widening elbow from under the runner out into the river
D_RAW = [(TX, 0, TZ - 2.2), (TX, 0, -60.0), (TX + 10, 0, -65.0), (178.0, 0, -63.0), (196.0, 0, -56.0)]
D_PTS = chaikin(D_RAW, 4); D_PTS[0] = Vector(D_RAW[0]); D_PTS[-1] = Vector(D_RAW[-1])
D_R = interp_r(D_PTS, [(0, 2.9), (0.25, 3.4), (0.6, 5.2), (1.0, 7.4)])
DRAFT = half_pipe("DraftTube", D_PTS, D_R, M_CONC2)
DRAFT_CUT = cutter("DraftCutter", D_PTS[len(D_PTS) // 2:], [r + 0.8 for r in D_R[len(D_PTS) // 2:]])

# ================= powerhouse (open section) + generator =================
PH_BASE = box("PowerhouseBase", 112, 176, 0, 45, -74, -68, M_CONC2)
PH_BACK = box("PowerhouseBack", 112, 176, 41, 45, -68, 14, M_CONC2)
PH_UP = box("PowerhouseUpstreamWall", 112, 116, 0, 45, -68, 14, M_CONC2)
PH_DN = box("PowerhouseDownstreamWall", 172, 176, 0, 45, -68, 14, M_CONC2)
PH_ROOF = box("PowerhouseRoof", 111, 177, 0, 46, 10, 14, M_CONC2)
boolean(PH_UP, PEN_CUT, "PenstockHole"); boolean(PH_DN, DRAFT_CUT, "DraftHole"); boolean(PH_BASE, DRAFT_CUT, "DraftHole"); boolean(ROCK_B, DRAFT_CUT, "DraftHole")
GEN_FLOOR = box("GeneratorFloor", 116, 172, 0, 41, -26.2, -24.0, M_CONC2)
HOLE = cyl("FloorHole", 7.6, 4.0, "Z", (TX, 0, -25.0), None, seg=48); HOLE.hide_render = True; HOLE.display_type = "WIRE"
boolean(GEN_FLOOR, HOLE, "ShaftHole")
GZ0, GZ1 = -23.5, -15.0
STATOR = lathe("Stator", tube_prof(7.25, 9.4, GZ0, GZ1), M_IRON, a0=0.0, ang=math.pi, seg=64, loc=(TX, 0, 0))
HOUSING = lathe("GenHousing", tube_prof(9.4, 10.2, GZ0 - 0.5, GZ1 + 1.6), M_PAINTG, a0=0.0, ang=math.pi, seg=64, loc=(TX, 0, 0))
bm = bmesh.new(); BARS = []
for k in range(15):
    a = math.pi * (k + 0.5) / 15
    x_, y_ = 7.45 * math.cos(a), 7.45 * math.sin(a)
    add_box(bm, x_ - 0.22, x_ + 0.22, y_ - 0.22, y_ + 0.22, GZ0 - 0.9, GZ1 + 0.9)
    BARS.append((TX + x_, y_))
for k in range(14):                                  # end-turn loops linking neighbouring bars (top + bottom)
    a0, a1 = math.pi * (k + 0.5) / 15, math.pi * (k + 1.5) / 15
    for zz in (GZ0 - 1.1, GZ1 + 1.1):
        add_bar(bm, (7.45 * math.cos(a0), 7.45 * math.sin(a0), zz), (7.45 * math.cos(a1), 7.45 * math.sin(a1), zz), 0.3)
COILS = mesh_obj("StatorCopper", bm, M_CU); COILS.location = (TX, 0, 0)
glow(B_CU, [(0, 0.0), (C["coils"] - 0.01, 0.0), (C["copper"], 1.2), (C["moving"], 0.6), (C["electricity"], 2.2), (C["transformer"] + 0.5, 0.4), (DUR, 0.4)])
ROTOR_E = empty("RotorSpin", (TX, 0, 0))
bm = bmesh.new(); add_cyl(bm, 5.4, GZ1 - GZ0 - 0.4, "Z", (0, 0, (GZ0 + GZ1) / 2), 48)
M_ROTB, B_ROTB = mat("RotorBody", (0.10, 0.11, 0.12), rough=0.45, metallic=0.7)
ROTOR = mesh_obj("Rotor", bm, M_ROTB, parent=ROTOR_E)
XRAY = [(0, 1.0), (C["moving"] - 0.01, 1.0), (C["moving"] + 0.25, 0.18), (C["transformer"] - 0.12, 0.18), (C["transformer"], 1.0), (DUR, 1.0)]
for b_ in (B_ROTB, bsdf_of(M_RED), bsdf_of(M_BLUE)): keyval(b_.inputs["Alpha"], XRAY)
bm = bmesh.new()
for k in range(16):
    a = 2 * math.pi * k / 16
    vs = add_box(bm, 5.35, 6.95, -0.95, 0.95, GZ0 + 0.3, GZ1 - 0.3, mi=k % 2)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "Z"))
POLES = mesh_obj("RotorPoles", bm, [M_RED, M_BLUE], parent=ROTOR_E)
SPIDER = cyl("RotorSpider", 5.6, 0.8, "Z", (0, 0, GZ1 + 0.2), M_PAINTG, seg=48); par(SPIDER, ROTOR_E)
bake(ROTOR_E, "rotation_euler", 2, [-SPIN * flow_int(t) for t in TS])
TOPCAP = lathe("GenTopBracket", tube_prof(0.0, 10.2, GZ1 + 1.6, GZ1 + 2.6), M_PAINTG, a0=0.0, ang=math.pi, seg=64, loc=(TX, 0, 0))
windows(TOPCAP, [(0, C["shaft"]), (C["transformer"], DUR)])
# electrons: cyan beads running along the copper bars (alternating up/down), only while the magnets sweep past
EL_ME = sphere_mesh("Electron", 0.5, 1); EL_ME.materials.append(M_ELEC)
ELECTRONS = []
for k, (bx, by) in enumerate(BARS):
    for j in range(4):
        o = obj_from(f"Electron{k}_{j}", EL_ME)
        sgn = 1 if k % 2 == 0 else -1
        def fn(t, j=j, sgn=sgn, bx=bx, by=by):
            u = ((t * 0.55 + j / 4.0) % 1.0); z = GZ0 - 0.6 + (GZ1 - GZ0 + 1.2) * (u if sgn > 0 else 1 - u)
            return (bx + (-0.35 if by > 0 else 0) * 0, by - 0.32, z)
        bake_loc(o, fn); windows(o, [(C["moving"] + 0.3, C["transformer"] + 0.6)]); ELECTRONS.append(o)

# ================= transformer on the roof + line up to the canyon rim =================
XF = box("Transformer", 150, 162, 8, 18, 14, 22, M_TANK)
bm = bmesh.new()
for k in range(9): add_box(bm, 150.5 + 1.25 * k, 150.9 + 1.25 * k, 6.6, 8.0, 14.5, 21.0)
FINS = mesh_obj("XfFins", bm, M_TANK)
BUSH = []
for k in range(3):
    BUSH.append(cyl(f"Bushing{k}", 0.55, 4.0, "Z", (152.5 + 3.5 * k, 13.0, 24.0), M_PORC, seg=16))
TOWER_TOP = Vector((290.0, 70.0, 205.0))
bm = bmesh.new()
for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    add_bar(bm, (290 + 6 * sx, 70 + 6 * sy, 170), (290 + 1.2 * sx, 70 + 1.2 * sy, 208), 0.6)
add_bar(bm, (279, 70, 205), (301, 70, 205), 0.7)
LTOWER = mesh_obj("RimTower", bm, M_GALV)
LINE_PTS = []
for k in range(3):
    a_ = Vector((152.5 + 3.5 * k, 13.0, 26.0)); b_ = Vector((281.0 + 9.0 * k, 70.0, 204.5))
    pts = sag_pts(a_, b_, 9.0, n=20); LINE_PTS.append(pts)
    poly_obj(f"Line{k}", pts, 0.22, M_WIRE)
glow(B_WIRE, [(0, 0.0), *pulse(C["transformer"] + 0.5, 1.5, hold=1.5), (DUR, 0.0)])
LBEADS = []
for k in range(3):
    LBEADS += beads(f"LineBead{k}_", Path(LINE_PTS[k]), 8, 0.9, M_CYANG, [T_XF, T_WIDE], speed=60.0)

# ================= water beads along the whole route (tower -> penstock -> spiral -> runner -> draft tube) =================
ROUTE = [Vector(p) + Vector((0, 1.6, 0)) for p in P_PTS[:-1]]
ROUTE += [Vector(p) for p in SP_PTS[:44]]                       # back half of the spiral (y >= 0)
ROUTE += [Vector((TX + 3.0, 2.0, TZ)), Vector((TX, 1.5, TZ - 2.4))]
ROUTE += [Vector(p) + Vector((0, 1.6, 0)) for p in D_PTS[1:]]
RP = Path(ROUTE)
L_PEN = Path([Vector(p) for p in P_PTS[:-1]]).L
L_SP = L_PEN + Path(SP_PTS[:44]).L + 6.0
# map a uniform flow parameter q (0..1) to arc length; slow in the tower, fast down the pipe, slows in the draft tube
QK = [(0.0, 0.0), (0.20, 80.0), (0.55, L_PEN), (0.74, L_SP), (1.0, RP.L)]
def q2s(q):
    for (q0, s0), (q1, s1) in zip(QK, QK[1:]):
        if q <= q1:
            u = (q - q0) / (q1 - q0)
            if q0 >= 0.74: u = math.sqrt(u)                     # draft tube: slowing down
            return s0 + (s1 - s0) * u
    return RP.L
NB = 110
WB_ME = sphere_mesh("WaterBead", 1.25, 2); WB_ME.materials.append(M_CYANG)
WBEADS = []
for i in range(NB):
    o = obj_from(f"WaterBead{i}", WB_ME)
    bake_loc(o, lambda t, i=i: tuple(RP.at(q2s((i / NB + flow_int(t) / 11.0) % 1.0))))
    windows(o, [(0, C["japan"]), (C["so"], DUR)]); WBEADS.append(o)
# water-hammer pulse: a red glow running from the gates back up the pipe
HAM = obj_from("HammerPulse", sphere_mesh("HammerPulse", 4.2, 3), M_REDG)
HAM_PATH = Path(list(reversed([Vector(p) for p in P_PTS])))
bake_loc(HAM, lambda t: tuple(HAM_PATH.at(HAM_PATH.L * ease((t - C["hammers"]) / 1.5))))
windows(HAM, [(C["hammers"], C["japan"])])
HOOKP = obj_from("HookPulse", sphere_mesh("HookPulse", 4.0, 3), M_REDG)
bake_loc(HOOKP, lambda t: tuple(Path([Vector(p) for p in P_PTS]).at(Path([Vector(p) for p in P_PTS]).L * (0.35 + 0.6 * ease((t - C["burst0"] + 0.3) / 1.0)))))
windows(HOOKP, [(C["burst0"] - 0.3, C["lake"])])
# lake height arrow (stored energy)
bm = bmesh.new(); add_arrow(bm, (-80.0, 2.0), (0, 1), LAKE_Z - 4.0, 9.0, y=-1.0)
ARROW = mesh_obj("HeightArrow", bm, M_GOLDG); windows(ARROW, [T_LAKE])
# ================= 1950 what-if set (x 3000): old riveted pipe on a hillside bursts =================
X5 = 3000.0; SLOPE = math.radians(24)
HILL = box("Hillside", -160, 160, -80, 80, -3, 0, M_HILL); HILL.location = (X5, 0, 0); HILL.rotation_euler = (0, SLOPE, 0)
def on_slope(u, h=0.0):
    """point at distance u along the slope (x) and h above it."""
    return Vector((X5 + u * math.cos(SLOPE) - h * math.sin(SLOPE), 0, -u * math.sin(SLOPE) + h * math.cos(SLOPE)))
PR5 = 2.2
SADDLES = []
for k in range(-6, 7):
    s_ = box(f"Saddle{k}", -1.0, 1.0, -2.4, 2.4, 0.0, 1.4, M_SADDLE); s_.location = on_slope(k * 10.0); s_.rotation_euler = (0, SLOPE, 0); SADDLES.append(s_)
PIPE_A = cyl("OldPipeUpper", PR5, 52.0, "X", (0, 0, 0), M_OLD, seg=32); PIPE_A.location = on_slope(-32.0, 1.4 + PR5); PIPE_A.rotation_euler = (0, SLOPE, 0)
PIPE_B = cyl("OldPipeLower", PR5, 52.0, "X", (0, 0, 0), M_OLD, seg=32); PIPE_B.location = on_slope(32.0, 1.4 + PR5); PIPE_B.rotation_euler = (0, SLOPE, 0)
bm = bmesh.new()
for k in range(-6, 7):
    for j in range(16):
        a = 2 * math.pi * j / 16
        add_box(bm, k * 4.0 - 0.15, k * 4.0 + 0.15, PR5 * math.cos(a) - 0.12, PR5 * math.cos(a) + 0.12, PR5 * math.sin(a) - 0.12, PR5 * math.sin(a) + 0.12)
RIVETS_ME = bpy.data.meshes.new("RivetRings"); bm.to_mesh(RIVETS_ME); bm.free()
for nm, pp in (("RivetsUpper", PIPE_A), ("RivetsLower", PIPE_B)):
    o = obj_from(nm, RIVETS_ME, M_DARK); o.location = pp.location; o.rotation_euler = pp.rotation_euler
CHUNKS = []
BURST_T = C["burst"]
for kk in range(3):
    for j in range(8):
        a0 = 2 * math.pi * j / 8
        bm = bmesh.new()
        prof2 = []
        for s in range(5):
            a = a0 + (2 * math.pi / 8) * s / 4
            prof2.append((math.cos(a), math.sin(a)))
        vs = []
        for xx in (-2.0, 2.0):
            for (c_, s_) in prof2:
                vs.append(bm.verts.new((xx, (PR5 - 0.12) * c_, (PR5 - 0.12) * s_))); vs.append(bm.verts.new((xx, (PR5 + 0.12) * c_, (PR5 + 0.12) * s_)))
        bmesh.ops.convex_hull(bm, input=vs)
        ch = mesh_obj(f"BurstChunk{kk}_{j}", bm, M_OLD)
        cx_ = (kk - 1) * 4.0
        base = on_slope(cx_, 1.4 + PR5)
        ch.location = base; ch.rotation_euler = (0, SLOPE, 0)
        out_dir = Matrix.Rotation(SLOPE, 3, "Y") @ Vector((0, math.cos(a0 + math.pi / 8), math.sin(a0 + math.pi / 8)))
        CHUNKS.append((ch, base, out_dir))
fx.rigid([c[0] for c in CHUNKS], passive=[HILL], mass=2.0, friction=0.6, bounce=0.15)
for ch, base, d in CHUNKS:
    try:
        rb = ch.rigid_body; rb.collision_shape = "CONVEX_HULL"
        f_rel = F(BURST_T)
        rb.kinematic = True; ch.keyframe_insert("rigid_body.kinematic", frame=1)
        ch.location = base; ch.keyframe_insert("location", frame=f_rel - 1)
        ch.location = base + d * 0.55 + Vector((0, 0, 0.25)); ch.keyframe_insert("location", frame=f_rel + 1)
        rb.kinematic = True; ch.keyframe_insert("rigid_body.kinematic", frame=f_rel + 1)
        rb.kinematic = False; ch.keyframe_insert("rigid_body.kinematic", frame=f_rel + 2)
    except Exception as e: print("[build] chunk kinematic skipped", e)
SPRAY = obj_from("SprayEmitter", sphere_mesh("SprayEmitter", 1.6, 2), M_DARK, loc=tuple(on_slope(0.0, 1.4 + PR5)))
SPRAY_MOD = fx.particles(SPRAY, "rain", F(BURST_T), F(C["so"] - 0.5), count=2200)
try:
    ps = SPRAY_MOD.particle_system.settings; ps.normal_factor = 14.0; ps.particle_size = 0.16; ps.lifetime = 34; ps.factor_random = 0.8
    dm = ps.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    dm.inputs["Base Color"].default_value = (0.80, 0.90, 1.0, 1); dm.inputs["Emission Color"].default_value = (0.6, 0.85, 1.0, 1); dm.inputs["Emission Strength"].default_value = 1.5
except Exception as e: print("[build] spray tune skipped", e)
SPRAY.hide_render = False
glow(B_OLD, [(0, 0.0), (C["japan"], 0.0), (BURST_T - 0.6, 1.2), (BURST_T, 2.5), (BURST_T + 0.6, 0.15), (DUR, 0.15)])
RED5 = bpy.data.lights.new("BurstRed", "POINT"); RED5.color = (1.0, 0.3, 0.18); RED5.shadow_soft_size = 2.0
RED5_O = bpy.data.objects.new("BurstRed", RED5); scene.collection.objects.link(RED5_O); RED5_O.location = tuple(on_slope(0, 10.0) + Vector((0, -12, 0)))
for t_, v_ in [(0, 0.0), (BURST_T - 0.05, 0.0), (BURST_T, 60000.0), (BURST_T + 0.6, 15000.0), (C["so"], 15000.0)]:
    RED5.energy = v_; RED5.keyframe_insert("energy", frame=F(t_))
L5 = bpy.data.lights.new("HillMoon", "SUN"); L5.energy = 0.0
# hammer red light in the main set
RED_H = bpy.data.lights.new("HammerRed", "POINT"); RED_H.color = (1.0, 0.25, 0.15); RED_H.shadow_soft_size = 4.0
RED_HO = bpy.data.objects.new("HammerRed", RED_H); scene.collection.objects.link(RED_HO); RED_HO.location = (60.0, -40.0, -25.0)
for t_, v_ in [(0, 0.0), (C["burst0"] - 0.05, 0.0), (C["burst0"], 5.0e5), (C["lake"] - 0.05, 2.5e5), (C["lake"], 0.0),
               (C["hammers"] - 0.05, 0.0), (C["hammers"], 6.0e5), (C["japan"] - 0.05, 3.0e5), (C["japan"], 0.0), (DUR, 0.0)]:
    RED_H.energy = v_; RED_H.keyframe_insert("energy", frame=F(t_))

# ================= Mantaflow: short outflow at the draft-tube exit (laptop --bake-fluid) =================
FL_DOM = box("OutflowDomain", 182, 214, 0.5, 26, BED_Z + 0.5, RIVER_Z + 6, M_RIVER)
FL_IN = cyl("OutflowInflow", 3.0, 2.0, "X", (188.0, 8.0, -57.0), M_RIVER, seg=16)
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=64, start=F(C["water2"]), end=F(C["water2"] + 3.8), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_IN.hide_render = True
if FLUID_BAKE: windows(FL_DOM, [(C["water2"], C["hoover2"])])
else: windows(FL_DOM, [])

# ================= GN scatter: boulders + shrubs on the rim and the river banks =================
def boulder_inst():
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=3.0)
    for v in bm.verts: v.co.x *= random.uniform(0.8, 1.4); v.co.z *= 0.6
    return mesh_obj("BoulderInst", bm, M_BOULDER)
def shrub_inst():
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=2.2)
    for v in bm.verts: v.co.z = abs(v.co.z) * 0.7
    return mesh_obj("ShrubInst", bm, M_SHRUB)
BOUL = boulder_inst(); SHRUB = shrub_inst()
def plane(name, x0, x1, y0, y1, z, m_):
    bm = bmesh.new(); v = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]; bm.faces.new(v)
    return mesh_obj(name, bm, m_)
S1 = plane("RimScatterA", -700, 1000, 162, 800, 175.02, M_ROCK)
fx.scatter(S1, BOUL, density=0.0012, scale_min=0.5, scale_max=2.2, seed=3)
S2 = plane("RimScatterB", -700, 1000, 162, 800, 175.03, M_ROCK)
fx.scatter(S2, SHRUB, density=0.0016, scale_min=0.5, scale_max=1.4, seed=8)
S3 = plane("HillScatter", -150, 150, -70, 70, 0.05, M_HILL); S3.location = (X5, 0, 0); S3.rotation_euler = (0, SLOPE, 0)
fx.scatter(S3, SHRUB, density=0.01, scale_min=0.3, scale_max=0.9, seed=11)
BOUL.location = (0, 0, -900); SHRUB.location = (0, 0, -900)

# ================= world: HDRI light + own sky gradient =================
fx.hdri("sunset", strength=0.6, rotation_deg=200.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.04, 0.035, 0.035, 1); e[1].position = 0.42; e[1].color = (0.20, 0.36, 0.70, 1)
    eh = e.new(0.015); eh.color = (0.98, 0.62, 0.36, 1)
    wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.2; sun_d.color = (1.0, 0.84, 0.66); sun_d.angle = math.radians(1.5)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(58), 0, math.radians(-25))
fx.glare(threshold=1.0, strength=0.55, size=7)
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.95, 0.88)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("PitLight", (TX, -14.0, -32.0), 22.0, 6000.0, rot=(math.radians(60), 0, 0))
area("GenLight", (TX, -16.0, -6.0), 24.0, 6000.0, rot=(math.radians(50), 0, 0))
area("DraftLight", (165.0, -20.0, -50.0), 26.0, 6000.0, rot=(math.radians(70), 0, 0))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 12000
def bead_at(t, off=(0, 0, 0)):
    q = (37 / NB + flow_int(t) / 11.0) % 1.0
    return tuple(RP.at(q2s(q)) + Vector(off))
DROP_T0 = C["drops"]
def drop_cam(t):
    u = ease((t - DROP_T0) / (C["then"] - DROP_T0)); p = Path([Vector(x) for x in P_PTS]).at(Path([Vector(x) for x in P_PTS]).L * (0.40 + 0.52 * u))
    return tuple(p + Vector((-22.0, -62.0, 16.0)))
def drop_tgt(t):
    u = ease((t - DROP_T0) / (C["then"] - DROP_T0)); p = Path([Vector(x) for x in P_PTS]).at(Path([Vector(x) for x in P_PTS]).L * (0.44 + 0.52 * u))
    return tuple(p)
HOOK_A = ((250.0, -270.0, 55.0), (60.0, 20.0, 0.0), 24)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK_A),
    (C["fall"], (250.0, -280.0, 40.0), (50.0, 10.0, -10.0), 24),
    (C["burst0"] - 0.3, (150.0, -210.0, 10.0), (40.0, 0.0, -25.0), 24),
    (C["lake"], (-250.0, -300.0, 70.0), (-60.0, 20.0, 50.0), 24, "cut"),
    (C["at"] - 0.05, (-230.0, -270.0, 66.0), (-55.0, 20.0, 50.0), 24),
    (C["at"], (TWX - 30.0, -62.0, 100.0), (TWX, 0.0, 72.0), 26, "cut"),
    (C["penstocks"] - 0.05, (TWX - 26.0, -58.0, 92.0), (TWX, 0.0, 66.0), 26),
    (C["thirty"], (TWX - 10.0, -60.0, 30.0), (TWX + 8.0, 0.0, 0.0), 26),
    (C["drops"] - 0.05, (TWX - 2.0, -58.0, 18.0), (TWX + 14.0, 0.0, -12.0), 26),
    (C["drops"], drop_cam, drop_tgt, 26, "cut"),
    (C["then"] - 0.05, drop_cam, drop_tgt, 26),
    (C["then"], (TX - 4.0, -40.0, -30.0), (TX, 4.0, TZ), 24, "cut"),
    (C["ring"] - 0.05, (TX - 2.0, -34.0, -34.0), (TX, 4.0, TZ), 24),
    (C["ring"], (TX + 3.0, -15.0, -38.5), (TX, 2.0, TZ), 26, "cut"),
    (C["good"] - 0.05, (TX + 4.5, -13.0, -40.0), (TX, 1.0, TZ), 26),
    (C["good"], (TX + 9.0, -10.0, -46.5), (TX, 0.5, TZ), 24, "cut"),
    (C["but"] - 0.05, (TX + 6.5, -9.0, -46.0), (TX, 0.5, TZ), 24),
    (C["but"], (TX + 3.0, -15.0, -38.5), (TX, 2.0, TZ), 26, "cut"),
    (C["hammers"] - 0.05, (TX + 2.0, -14.0, -39.0), (TX, 2.0, TZ), 26),
    (C["hammers"], (40.0, -190.0, -5.0), (35.0, 0.0, -25.0), 24, "cut"),
    (C["japan"] - 0.05, (25.0, -180.0, 2.0), (25.0, 0.0, -20.0), 24),
    (C["japan"], tuple(on_slope(-22.0, 6.0) + Vector((0, -36.0, 0))), tuple(on_slope(0.0, 3.0)), 26, "cut"),
    (C["so"] - 0.05, tuple(on_slope(-16.0, 7.0) + Vector((0, -33.0, 0))), tuple(on_slope(0.0, 2.0)), 26),
    (C["so"], (TX + 3.0, -15.0, -38.5), (TX, 2.0, TZ), 26, "cut"),
    (C["shaft"] - 0.05, (TX + 2.0, -14.0, -39.0), (TX, 2.0, TZ), 26),
    (C["shaft"], (TX + 6.0, -22.0, -44.0), (TX, 0.0, -46.0), 22, "cut"),
    (C["rotor"] - 0.05, (TX + 7.0, -28.0, -20.0), (TX, 0.0, -21.0), 22),
    (C["rotor"], (TX + 10.0, -27.0, -10.0), (TX, 2.0, -19.5), 24, "cut"),
    (C["moving"] - 0.05, (TX + 6.0, -25.0, -12.0), (TX, 2.0, -19.5), 24),
    (C["moving"], (TX - 3.0, -26.0, -13.0), (TX, 4.0, -19.5), 28, "cut"),
    (C["transformer"] - 0.05, (TX - 1.0, -22.0, -14.0), (TX, 4.0, -19.5), 28),
    (C["transformer"], (205.0, -70.0, 45.0), (175.0, 20.0, 32.0), 24, "cut"),
    (C["water2"] - 0.05, (215.0, -80.0, 60.0), (195.0, 30.0, 50.0), 24),
    (C["water2"], (150.0, -42.0, -52.0), (155.0, 0.0, -60.0), 24, "cut"),
    (C["river"], (182.0, -55.0, -44.0), (192.0, 4.0, -54.0), 24),
    (C["hoover2"] - 0.05, (190.0, -60.0, -36.0), (195.0, 6.0, -48.0), 24),
    (C["hoover2"], (520.0, -470.0, 300.0), (70.0, 30.0, 10.0), 24, "cut"),
    (C["would"] - 0.05, (480.0, -430.0, 270.0), (70.0, 30.0, 15.0), 24),
    (C["would"], (60.0, -95.0, 150.0), (6.0, 2.0, 108.0), 26, "cut"),
    (DUR, (24.0, -40.0, 108.0), (5.5, 2.0, 78.0), 26),
]
def ev(p, t):
    if callable(p): return Vector(p(t))
    return Vector(p)
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
bake_scalar(fill_d, "energy", [max(200.0, min(2.0e6, 220.0 * ((cl - ct).length / 30.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
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
scene.view_settings.exposure = float(arg("--exposure", "-0.6"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["japan"]), F(C["so"]) + 2)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
PEN_PATH = Path([Vector(p) for p in P_PTS])
AP = {
    "dam": (50.0, 0.0, 60.0), "lake": (-90.0, 0.0, 80.0), "tower": (TWX + 7.0, 0.0, 95.0), "intake": (TWX + 7.2, 0.0, 71.0),
    "penstock": tuple(PEN_PATH.at(PEN_PATH.L * 0.55) + Vector((0, 0, 4.8))), "penstock_up": tuple(PEN_PATH.at(PEN_PATH.L * 0.22)),
    "spiral": (TX - 9.5, 0.0, TZ + 3.4), "gates": (TX + GR, 0.0, TZ + 1.5), "runner": (TX + 2.2, -2.0, TZ - 1.0),
    "shaft": (TX + 1.0, 0.0, -33.0), "stator": (TX - 9.6, 0.0, GZ1 - 1.0), "rotor": (TX + 4.0, -4.5, GZ1 - 2.0), "coils": (TX - 7.3, 0.4, GZ0 + 2.0),
    "generator": (TX + 10.2, 0.0, GZ1 + 1.0), "transformer": (150.0, 8.0, 22.0), "lines": tuple(Vector(LINE_PTS[1][10])),
    "draft": tuple(Vector(D_PTS[int(len(D_PTS) * 0.8)]) + Vector((0, 0, 6.0))), "river": (215.0, 0.0, RIVER_Z), "elevator": (8.0, 0.0, 95.0),
    "oldpipe": tuple(on_slope(0.0, 1.4 + 2 * PR5)), "powerhouse": (176.0, 0.0, 14.0),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "hook_pulse": round(C["burst0"] - 0.3, 3), "lake": RR(*T_LAKE), "lake_glow": round(C["stored"], 3),
          "intake": RR(*T_INTAKE), "pen_glow": round(C["penstocks"], 3), "drop": RR(*T_DROP), "spiral": RR(*T_SPIRAL), "gates": RR(*T_GATES),
          "gates_open": round(C["aims"], 3), "runner_spin": round(C["runner"], 3), "eff": RR(*T_EFF), "hammer": RR(*T_HAMMER),
          "slam": round(C["slam"], 3), "hammer_pulse": RR(C["hammers"], C["hammers"] + 1.5), "y1950": RR(*T_1950), "burst": round(C["burst"], 3),
          "slow": RR(*T_SLOW), "gates_reopen": round(C["so"], 3), "gates_close_slow": RR(C["close"], C["gradually"] + 0.9),
          "shaft": RR(*T_SHAFT), "gen": RR(*T_GEN), "elec": RR(*T_ELEC), "electrons_on": round(C["moving"] + 0.3, 3), "xf": RR(*T_XF),
          "draft": RR(*T_DRAFT), "wide": RR(*T_WIDE), "cta": RR(*T_CTA), "elevator_down": round(C["elevator"], 3),
          "gate_clicks": [round(C["aims"] + 0.02 * j, 3) for j in range(6)]}
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
