# Sump pump (3d-48a): "Many basements have a hole in the floor on purpose. It's there to catch the water the ground is pushing in."
# Stake: if the pump stops during a storm the basement floods, and a standard home policy usually won't cover it.
# Story: rain/snowmelt -> saturated soil presses on walls + floor, finds cracks -> perforated drain tile along the footing -> water seeps in,
# runs to the lowest spot = the sump pit -> float rides up, flips the switch, pump on -> impeller throws the water up the discharge pipe, out
# of the house, away from the walls -> level drops, float falls, pump off -> pipe still full: without the check valve (one-way flap) it falls
# back and the pump re-pumps the same water, wearing itself out -> the storm can cut the power (branch on the line, lights out) -> battery
# backup pump -> stuck float, frozen outdoor pipe -> most pumps last ~7-10 years -> CTA "Is there a pump pit in your basement?"
# Illustrative, 1 unit = 10 cm: generic house + basement cross-section (section plane y = 0, keep y >= 0, camera on -y). Pit, pump and
# pipes drawn ~1.3-2x so they read on a phone. No people, no brands, no text in the scene.
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
random.seed(48)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("many","Many"),("hole","hole"),("floor","floor"),("purpose","purpose."),("catch","catch"),("water","water"),("ground","ground"),
  ("pushing","pushing"),("if","If"),("pump","pump"),("stops","stops"),("storm","storm,"),("basement","basement"),("floods","floods,"),
  ("standard","standard"),("policy","policy"),("cover","cover"),("after","After"),("rain","rain"),("snowmelt","snowmelt,"),("soil","soil"),
  ("fills","fills"),("water2","water."),("that","That"),("presses","presses"),("walls","walls"),("floor2","floor,"),("finds","finds"),
  ("crack","crack."),("so","So"),("builders","builders"),("pipe","pipe"),("holes","holes"),("bottom","bottom"),("footing","footing."),
  ("water3","Water"),("seeps","seeps"),("carries","carries"),("lowest","lowest"),("sump","sump"),("pit","pit."),("as","As"),
  ("fills2","fills,"),("float","float"),("rides","rides"),("near","Near"),("flips","flips"),("switch","switch,"),("pump2","pump"),
  ("kicks","kicks"),("impeller","impeller"),("spins","spins"),("throws","throws"),("up","up"),("out","out"),("house","house,"),
  ("away","away"),("when","When"),("level","level"),("drops","drops,"),("float2","float"),("falls","falls"),("shuts","shuts"),
  ("but","But"),("pipe2","pipe"),("full","full"),("without","Without"),("flap","flap"),("check","check"),("valve","valve,"),
  ("all","all"),("fall","fall"),("back","back"),("move","move"),("same","same"),("again","again"),("wearing","wearing"),
  ("and","And"),("worst","worst"),("storm2","storm"),("fills3","fills"),("knock","knock"),("power","power."),("thats","That's"),
  ("battery","battery"),("backup","backup"),("floats","Floats"),("stuck","stuck"),("wall","wall,"),("winter","winter"),
  ("outside","outside"),("freeze","freeze"),("solid","solid."),("most","Most"),("seven","seven"),("ten","ten"),("years","years."),
  ("is","Is"),("pit2","pit"),("tell","Tell"),("comments","comments.")]
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
CL = coll("SumpPump")
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
GZ = 0.0                                   # grade
FLZ, SLAB0 = -22.0, -23.0                  # basement floor top / slab bottom
WX0, WX1 = 40.0, 42.0                      # basement wall inner / outer face (both sides, mirrored)
WTOP = 3.0                                 # wall top (sill) above grade
FT = dict(x0=37.0, x1=47.0, z0=-27.0, z1=-24.0)   # footing (right side, mirrored on the left)
DEPTH = 60.0                               # basement depth in y
PX, PR, PZ0 = 20.0, 3.6, -31.0             # sump pit centre x, liner radius (drawn ~1.3x), pit bottom
PMX, PMR = 20.9, 1.25                      # main pump
FRX = 22.85                                # float rod x
BKX = 18.0                                 # battery backup pump x
TILE_X, TILE_Z, TILE_R = 49.5, -25.6, 0.85 # drain tile (4-inch drawn 2x) along the footing, axis Y
SOIL_BOT = -140.0
T_HOOK = (0.0, C["if"]); T_STAKE = (C["if"], C["after"]); T_RAIN = (C["after"], C["so"]); T_TILE = (C["so"], C["as"])
T_FLOAT = (C["as"], C["impeller"]); T_IMP = (C["impeller"], C["when"]); T_DROP = (C["when"], C["but"]); T_FULL = (C["but"], C["without"])
T_VALVE = (C["without"], C["and"]); T_POWER = (C["and"], C["thats"]); T_BACKUP = (C["thats"], C["floats"]); T_STUCK = (C["floats"], C["winter"])
T_FREEZE = (C["winter"], C["most"]); T_AGE = (C["most"], C["is"]); T_CTA = (C["is"], DUR)
inw = lambda t, w: w[0] <= t < w[1]

# ================= materials =================
M_SOIL = strata("Soil", [(0.06, 0.035, 0.018), (0.13, 0.075, 0.035), (0.09, 0.05, 0.025), (0.16, 0.095, 0.045)], scale=0.10, bump=0.5)
M_CONC, B_CONC = mat("Concrete", (0.50, 0.49, 0.46), rough=0.85, noise=0.8)
M_CONCCUT, _ = mat("ConcreteCut", (0.66, 0.64, 0.60), rough=0.9, noise=2.0)
M_FOOT, _ = mat("Footing", (0.42, 0.41, 0.39), rough=0.9, noise=1.2)
M_GRAVEL, B_GRAVEL = mat("Gravel", (0.24, 0.23, 0.21), rough=0.8, noise=9.0)
M_STONE, _ = mat("Stone", (0.40, 0.38, 0.35), rough=0.7, noise=4.0)
M_GRASS, _ = mat("Grass", (0.10, 0.20, 0.05), rough=0.9, noise=0.4)
M_TUFT, _ = mat("Tuft", (0.14, 0.28, 0.06), rough=0.9)
M_WALL, _ = mat("HouseWall", (0.74, 0.70, 0.63), rough=0.8)
M_WALLCUT, _ = mat("WallCut", (0.92, 0.90, 0.86), rough=0.9, noise=2.0)
M_WOOD, _ = mat("Joist", (0.55, 0.38, 0.22), rough=0.7, noise=3.0)
M_ROOF, _ = mat("Shingles", (0.18, 0.15, 0.14), rough=0.85, noise=6.0)
M_WINDOW, B_WINDOW = emit_mat("Window", (1.0, 0.78, 0.55), 3.0)
M_BULB, B_BULB = emit_mat("Bulb", (1.0, 0.85, 0.6), 12.0)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 5.0)
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 0.0)
M_REDG, B_REDG = emit_mat("RedGlow", (1.0, 0.30, 0.24), 0.0)
M_GREENG, B_GREENG = emit_mat("GreenGlow", (0.35, 1.0, 0.45), 0.0)
M_LINER, B_LINER = mat("PitLiner", (0.05, 0.05, 0.055), rough=0.45, emit_rgb=(0.98, 0.74, 0.27))
M_LINERCUT, _ = mat("PitLinerCut", (0.85, 0.35, 0.12), rough=0.5)
M_PVC, B_PVC = mat("PVC", (0.90, 0.90, 0.88), rough=0.32, emit_rgb=(0.98, 0.74, 0.27))
M_PVCCUT, _ = mat("PVCCut", (0.85, 0.35, 0.12), rough=0.5)
M_TILE, B_TILE = mat("DrainTile", (0.10, 0.10, 0.10), rough=0.55, emit_rgb=(0.98, 0.74, 0.27))
M_PUMP, B_PUMP = mat("PumpBody", (0.12, 0.26, 0.42), rough=0.35, metallic=0.6, emit_rgb=(1.0, 0.30, 0.24))
M_PUMPCUT, _ = mat("PumpCut", (0.85, 0.35, 0.12), rough=0.5)
M_COPPER, B_COPPER = mat("Copper", (0.80, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(1.0, 0.30, 0.10))
M_STEEL, _ = mat("Steel", (0.62, 0.63, 0.65), rough=0.25, metallic=1.0)
M_FLOAT, B_FLOAT = mat("Float", (0.95, 0.55, 0.10), rough=0.35, emit_rgb=(0.98, 0.74, 0.27))
M_VALVE, B_VALVE = mat("ValveBody", (0.75, 0.88, 0.95), rough=0.08, emit_rgb=(0.98, 0.74, 0.27), alpha=0.35)
M_FLAP, B_FLAP = mat("Flap", (0.15, 0.15, 0.16), rough=0.5, emit_rgb=(0.98, 0.74, 0.27))
M_BATT, B_BATT = mat("Battery", (0.10, 0.10, 0.11), rough=0.5, emit_rgb=(0.35, 1.0, 0.45))
M_ICE, B_ICE = mat("Ice", (0.85, 0.93, 1.0), rough=0.15, emit_rgb=(0.45, 0.85, 1.0))
M_HOLE, _ = mat("HoleDark", (0.01, 0.01, 0.012), rough=0.6)
M_POLE, _ = mat("Pole", (0.30, 0.22, 0.15), rough=0.85, noise=4.0)
M_BARK, _ = mat("Bark", (0.22, 0.15, 0.09), rough=0.9, noise=5.0)
M_LEAF, _ = mat("Leaf", (0.10, 0.22, 0.06), rough=0.8)
M_CABLE, _ = mat("Cable", (0.03, 0.03, 0.03), rough=0.5)
M_WATER, B_WATER, VA_WATER = water_sec("PitWater")
M_PIPEW, B_PIPEW, _ = water_sec("PipeWater", dens=0.08)
M_FLOODW, B_FLOODW, _ = water_sec("FloodWater")
M_GW, FAC_GW = ghost("GroundWater", (0.10, 0.40, 1.0))
for n_ in M_GW.node_tree.nodes:
    if n_.type == "EMISSION": n_.inputs["Strength"].default_value = 0.35
M_ARROW, B_ARROW = emit_mat("PressArrow", (0.30, 0.92, 1.0), 0.0)
M_BEAD, _ = emit_mat("Bead", (0.30, 0.92, 1.0), 7.0)
M_BEADR, _ = emit_mat("BeadRed", (1.0, 0.30, 0.24), 7.0)
M_BEADG, _ = emit_mat("BeadGreen", (0.35, 1.0, 0.45), 7.0)

# pump ageing: body colour drifts to rust over "seven to ten years"
nt = M_PUMP.node_tree
rust_fac = VALUE(nt, "Rust", [(0, 0.0), (C["seven"] - 0.2, 0.0), (C["years"] + 0.3, 0.85), (C["is"] - 0.05, 0.85), (C["is"], 0.0)])
nz_ = nt.nodes.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 3.0; nz_.inputs["Detail"].default_value = 8.0
msk = MATH(nt, "MULTIPLY", nz_.outputs["Fac"], rust_fac); msk = MATH(nt, "MULTIPLY", msk, 1.6, clamp=True)
nt.links.new(mix_rgb(nt, msk, (0.12, 0.26, 0.42), (0.36, 0.16, 0.06)), B_PUMP.inputs["Base Color"])
# ice on the outdoor pipe end: keyed alpha-free mix (white crust)
glow(B_ICE, [(0, 0.0), (C["freeze"] - 0.1, 0.0), (C["freeze"] + 0.4, 3.0), (C["most"], 2.0)])

# ================= ground, soil, gravel, slab, walls, footings =================
SOIL_L = box("SoilLeft", -170, -WX1, 0, 90, SOIL_BOT, GZ, M_SOIL)
SOIL_R = box("SoilRight", WX1, 170, 25, 90, SOIL_BOT, GZ, M_SOIL)
SOIL_RF = box("SoilRightFront", WX1, 170, 0, 25, SOIL_BOT, GZ, M_SOIL)
GRASS_RF = box("GrassRightFront", WX1, 170, 0, 25, GZ, GZ + 0.4, M_GRASS)
SOIL_B = box("SoilUnder", -WX1, WX1, 0, 90, SOIL_BOT, FT["z0"], M_SOIL)
GRASS_L = box("GrassLeft", -170, -WX1, 0, 90, GZ, GZ + 0.4, M_GRASS)
GRASS_R = box("GrassRight", WX1, 170, 25, 90, GZ, GZ + 0.4, M_GRASS)
GRAV = box("GravelBed", -WX0, WX0, 0, DEPTH, FT["z0"], SLAB0, M_GRAVEL)
SLAB = box("Slab", -WX0, WX0, 0, DEPTH, SLAB0, FLZ, M_CONC)
for sx in (1, -1):
    box(f"Wall{sx}", sx * WX0, sx * WX1, 0, DEPTH + 2, FT["z1"], WTOP, M_CONC)
    box(f"Footing{sx}", sx * FT["x0"], sx * FT["x1"], 0, DEPTH + 2, FT["z0"], FT["z1"], M_FOOT)
    # gravel envelope around the drain tile
    if sx == 1:
        box("TileGravel1", FT["x1"] - 0.5, FT["x1"] + 5.5, 25, DEPTH + 2, FT["z0"], -22.5, M_GRAVEL)
        box("TileGravel1Front", FT["x1"] - 0.5, FT["x1"] + 5.5, 0, 25, FT["z0"], -22.5, M_GRAVEL)
    else: box(f"TileGravel{sx}", sx * (FT["x1"] - 0.5), sx * (FT["x1"] + 5.5), 0, DEPTH + 2, FT["z0"], -22.5, M_GRAVEL)
box("BackWall", -WX1, WX1, DEPTH, DEPTH + 2, FT["z1"], WTOP, M_CONC)
# pit hole through the slab + gravel (and the under-slab soil)
PITCUT = full_cyl("PitCut", PR + 0.15, PX, 0, PZ0 - 0.3, FLZ + 1.0, None); PITCUT.hide_render = True; PITCUT.display_type = "WIRE"
for o in (SLAB, GRAV, SOIL_B): boolean(o, PITCUT)
# cross pipe (right tile -> through the footing -> pit) cut channel
XP = [Vector((TILE_X, 0, TILE_Z)), Vector((FT["x0"] - 1, 0, -26.0)), Vector((PX + PR + 0.4, 0, -26.6))]
XPC = cutter("CrossCut", fillet_path(XP, 2.0, 6, 0.8), [0.95] * len(fillet_path(XP, 2.0, 6, 0.8)))
for o in (GRAV, bpy.data.objects["Footing1"], bpy.data.objects["TileGravel1Front"]): boolean(o, XPC)
# crack in the left wall (red flash on "crack")
CRACK = poly_obj("Crack", [Vector((-41.0, -0.05, z)) + Vector((0.4 * math.sin(z * 1.7), 0, 0)) for z in [-20 + 0.9 * i for i in range(12)]], 0.18, M_REDG)
glow(B_REDG, [(0, 0.0)] + pulse(C["crack"], 6.0, hold=0.9) + pulse(C["wearing"], 3.0, hold=1.0) + pulse(C["stuck"], 4.0, hold=1.2))
windows(CRACK, [(C["finds"], C["so"])])

# ================= house above (simple shell, lit windows) =================
box("FirstFloor", -WX1, WX1, 0, DEPTH + 2, WTOP, WTOP + 1.2, M_WOOD)
for sx in (1, -1): box(f"HouseWall{sx}", sx * WX0, sx * WX1, 0, DEPTH + 2, WTOP + 1.2, 30, M_WALL)
box("HouseBack", -WX1, WX1, DEPTH, DEPTH + 2, WTOP + 1.2, 30, M_WALL)
box("Ceiling", -WX1, WX1, 0, DEPTH + 2, 30, 31, M_WALLCUT)
bm = bmesh.new()
vs = [bm.verts.new(v) for v in [(-45, 0, 31), (45, 0, 31), (0, 0, 52), (-45, DEPTH + 2, 31), (45, DEPTH + 2, 31), (0, DEPTH + 2, 52)]]
for f in [(0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]: bm.faces.new([vs[j] for j in f])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj("Roof", bm, M_ROOF)
for wx in (-24, 0, 24): box(f"Win{wx}", wx - 6, wx + 6, DEPTH - 0.1, DEPTH, 10, 22, M_WINDOW)
OFF = C["power"] - 0.1
glow(B_WINDOW, [(0, 3.0), (C["stops"] - 0.1, 3.0), (C["stops"], 0.0), (C["after"] - 0.01, 0.0), (C["after"], 3.0), (OFF, 3.0), (OFF + 0.06, 0.0),
                 (OFF + 0.16, 2.0), (OFF + 0.22, 0.0), (C["winter"], 0.0), (C["winter"] + 0.01, 3.0)])
# basement lamp
BULB = full_cyl("Bulb", 0.9, 0, 30, WTOP - 1.8, WTOP - 0.2, M_BULB)
glow(B_BULB, [(0, 12.0), (C["stops"] - 0.1, 12.0), (C["stops"], 0.0), (C["after"] - 0.01, 0.0), (C["after"], 12.0), (OFF, 12.0), (OFF + 0.06, 0.0),
               (OFF + 0.16, 8.0), (OFF + 0.22, 0.0), (C["winter"], 0.0), (C["winter"] + 0.01, 12.0)])
lamp_d = bpy.data.lights.new("BasementLamp", "POINT"); lamp_d.shadow_soft_size = 1.0; lamp_d.color = (1.0, 0.86, 0.66)
lamp = bpy.data.objects.new("BasementLamp", lamp_d); scene.collection.objects.link(lamp); lamp.location = (0, 25, WTOP - 3)
def lamp_e(t):
    on = 2.5e4
    if C["stops"] <= t < C["after"]: return 0.0
    if C["power"] - 0.1 <= t < C["winter"]: return 0.0 if not (OFF + 0.06 + 0.1 <= t < OFF + 0.22) else on * 0.6
    return on
bake_scalar(lamp_d, "energy", [lamp_e(t) for t in TS])

# ================= sump pit, water, pump, float, discharge, check valve =================
# liner: half tube (y >= 0) with an orange cut rim, small inlet holes on the back
LINER = lathe("PitLiner", tube_prof(PR - 0.22, PR, PZ0, FLZ + 0.5), M_LINER, seg=40, loc=(PX, 0, 0))
box("PitLinerFloor", PX - PR, PX + PR, 0, PR, PZ0 - 0.4, PZ0, M_LINER)
for sgn in (1, -1): box(f"LinerCut{sgn}", PX + sgn * (PR - 0.22), PX + sgn * PR, -0.02, 0.02, PZ0, FLZ + 0.5, M_LINERCUT)
glow(B_LINER, [(0, 0.0)] + pulse(C["sump"], 1.6, hold=1.0) + pulse(C["pit2"], 1.2, hold=3.0))
# pit water level (z of the surface), keyed per beat
WL_LO, WL_ON, WL_RIM = -29.2, -24.6, FLZ + 0.4
def wl(t):
    if t < C["if"]: return PW([(0, -27.0), (C["if"], -26.0)])(t)
    if t < C["after"]: return PW([(C["if"], -26.0), (C["stops"], -25.5), (C["floods"], WL_RIM), (C["after"], WL_RIM)])(t)
    if t < C["as"]: return PW([(C["after"], -29.6), (C["seeps"], -29.6), (C["as"], WL_LO)])(t)
    if t < C["when"]: return PW([(C["as"], WL_LO), (C["flips"], WL_ON), (C["kicks"] + 0.4, WL_ON), (C["when"], -26.0)])(t)
    if t < C["without"]: return PW([(C["when"], -26.0), (C["shuts"], WL_LO), (C["without"], WL_LO)])(t)
    if t < C["and"]:
        # no check valve: the column falls back, pump restarts, again and again
        return PW([(C["without"], WL_LO), (C["fall"], WL_LO), (C["back"] + 0.4, WL_ON), (C["move"] + 0.5, WL_LO), (C["again"] + 0.1, WL_ON),
                   (C["wearing"], WL_LO), (C["and"], -27.5)])(t)
    if t < C["thats"]: return PW([(C["and"], -27.5), (C["power"], -25.0), (C["thats"], -24.0)])(t)
    if t < C["floats"]: return PW([(C["thats"], -24.0), (C["battery"], -24.0), (C["floats"], -27.5)])(t)
    if t < C["winter"]: return PW([(C["floats"], -27.5), (C["stuck"] + 0.2, -25.5), (C["winter"], -23.6)])(t)
    return PW([(C["winter"], -27.0), (DUR, -27.0)])(t)
WATER = lathe("PitWaterMesh", [(0.0, 0.0), (PR - 0.24, 0.0), (PR - 0.24, 1.0), (0.0, 1.0)], M_WATER, seg=40, loc=(PX, 0, PZ0))
bake(WATER, "scale", 2, [max(0.02, wl(t) - PZ0) for t in TS])
glow(B_WATER, [(0, 0.0)] + pulse(C["catch"], 0.8, hold=1.0) + pulse(C["rides"], 0.6, hold=1.0))

# pump state (1 = running) per frame
def pump_on(t):
    if inw(t, T_HOOK): return 1.0
    if inw(t, (C["kicks"], C["shuts"])): return 1.0
    if inw(t, T_VALVE): return 1.0 if (C["back"] + 0.4 <= t < C["move"] + 0.5) or (C["again"] + 0.1 <= t < C["wearing"]) else 0.0
    if inw(t, T_AGE) or inw(t, T_CTA): return 0.0
    return 0.0
def backup_on(t): return 1.0 if C["battery"] <= t < C["floats"] else 0.0

# main pump: half housing (lathe y >= 0) + motor + impeller + volute
PUMP = empty("Pump", (PMX, 0, 0))
pp = [(0.0, PZ0 + 0.2), (PMR + 0.25, PZ0 + 0.2), (PMR + 0.25, PZ0 + 1.6), (PMR, PZ0 + 1.8), (PMR, PZ0 + 5.6), (0.55, PZ0 + 6.1), (0.0, PZ0 + 6.1)]
par(lathe("PumpShell", pp, M_PUMP, seg=36), PUMP)
box("PumpCutFace", PMX - PMR - 0.25, PMX + PMR + 0.25, -0.03, 0.0, PZ0 + 0.2, PZ0 + 0.5, M_PUMPCUT)
MOTOR = par(lathe("Motor", tube_prof(0.25, PMR - 0.18, PZ0 + 2.2, PZ0 + 5.2), M_COPPER, a0=0.0, seg=28), PUMP); MOTOR.location = (0, -0.05, 0)
glow(B_COPPER, [(0, 0.0), (C["wearing"] - 0.2, 0.0), (C["wearing"] + 0.3, 4.0), (C["and"], 4.0), (C["and"] + 0.3, 0.0)])
IMP = empty("Impeller", (0, -0.4, PZ0 + 0.9)); par(IMP, PUMP)
bm = bmesh.new()
for k in range(6):
    a = k * math.pi / 3
    add_bar(bm, (0.15 * math.cos(a), 0.15 * math.sin(a), 0), (0.95 * math.cos(a + 0.5), 0.95 * math.sin(a + 0.5), 0), 0.22)
add_cyl(bm, 0.22, 0.7, "Z", (0, 0, 0.0), seg=12)
par(mesh_obj("ImpellerBlades", bm, M_STEEL), IMP)
spin = [0.0]
ang = []
for t in TS:
    spin[0] += (pump_on(t) * 0.9) if not inw(t, T_IMP) else pump_on(t) * 0.35   # slower in the close-up so the blades read
    ang.append(spin[0])
bake(IMP, "rotation_euler", 2, ang)
SHAFT = par(full_cyl("Shaft", 0.14, 0, -0.4, PZ0 + 0.9, PZ0 + 2.4, M_STEEL), PUMP)
# inlet screen ring at the base
par(lathe("Screen", tube_prof(PMR + 0.05, PMR + 0.3, PZ0 + 0.25, PZ0 + 1.4), M_STEEL, seg=36), PUMP)
# pump running indicator (on the switch box)
SWBOX = box("SwitchBox", FRX - 0.55, FRX + 0.55, 0.0, 1.2, -23.6, -22.6, M_PUMP)
LED = box("SwitchLED", FRX - 0.25, FRX + 0.25, -0.05, 0.0, -23.35, -22.85, M_GREENG)
def socket_steps(sock, fn, on_v, off_v=0.0):
    """key a socket at every on/off edge of fn (0.06 s ramps)"""
    sock.default_value = off_v; sock.keyframe_insert("default_value", frame=1); prev = False
    for t in TS:
        o = fn(t) > 0.5
        if o != prev:
            sock.default_value = off_v if o else on_v; sock.keyframe_insert("default_value", frame=F(max(0, t - 0.06)))
            sock.default_value = on_v if o else off_v; sock.keyframe_insert("default_value", frame=F(t))
        prev = o
socket_steps(B_GREENG.inputs["Emission Strength"], lambda t: max(pump_on(t), backup_on(t)), 6.0)
# float rod + float (rides the water between the stops; jams tilted on "stuck")
ROD = full_cyl("FloatRod", 0.12, FRX, 0.6, PZ0 + 1.0, -23.6, M_STEEL)
box("StopLow", FRX - 0.3, FRX + 0.3, 0.3, 0.9, WL_LO - 0.6, WL_LO - 0.45, M_STEEL)
box("StopHigh", FRX - 0.3, FRX + 0.3, 0.3, 0.9, WL_ON + 0.35, WL_ON + 0.5, M_STEEL)
FLOAT = obj_from("Float", bpy.data.meshes.new("FloatMe"))
bm = bmesh.new(); add_cyl(bm, 0.55, 1.0, "Z", (0, 0, 0), seg=20); bm.to_mesh(FLOAT.data); bm.free(); FLOAT.data.materials.append(M_FLOAT)
def float_z(t):
    if inw(t, T_STUCK) and t >= C["stuck"]: return -26.4                     # jammed on the liner wall
    return max(WL_LO - 0.45 + 0.5, min(WL_ON + 0.35 - 0.5, wl(t) - 0.15))
def float_x(t): return FRX + (0.45 * ease((t - C["stuck"]) / 0.4) if inw(t, T_STUCK) else 0.0)
bake_loc(FLOAT, lambda t: (float_x(t), 0.6, float_z(t)))
bake(FLOAT, "rotation_euler", 1, [math.radians(24) * ease((t - C["stuck"]) / 0.4) if inw(t, T_STUCK) else 0.0 for t in TS])
glow(B_FLOAT, [(0, 0.0)] + pulse(C["float"], 2.5, hold=1.0) + pulse(C["flips"], 4.0, hold=0.4) + pulse(C["float2"], 2.0, hold=0.6))
STUCKRING = lathe("StuckRing", tube_prof(0.7, 0.9, -0.08, 0.08), M_REDG, a0=0.0, ang=2 * math.pi, seg=24)
bake_loc(STUCKRING, lambda t: (float_x(t), 0.6, float_z(t)))
bake(STUCKRING, "rotation_euler", 1, [math.radians(24) for t in TS])
windows(STUCKRING, [(C["stuck"], C["winter"])])

# discharge pipe: pump top -> up -> check valve -> through the rim above grade -> outside -> along the lawn, away from the walls
DPTS = fillet_path([(PMX, 0, PZ0 + 6.0), (PMX, 0, 1.6), (WX1 + 6, 0, 1.6), (WX1 + 8, 0, 1.5), (95, 0, 1.5)], 1.6, 10, 0.6)
DR_O, DR_I = 0.62, 0.48
DPIPE = pipe_wall("DischargePipe", DPTS, DR_I, DR_O, M_PVC, a0=0.0, a1=math.pi, seg=18)
glow(B_PVC, [(0, 0.0)] + pulse(C["throws"], 2.0, hold=2.4) + pulse(C["pipe2"], 1.5, hold=1.2))
VZ = -16.0                                                   # check valve height
VALVE = lathe("CheckValve", tube_prof(DR_O + 0.02, 0.95, VZ - 1.3, VZ + 1.3), M_VALVE, seg=28, loc=(PMX, 0, 0))
for zz in (VZ - 1.4, VZ + 1.4): lathe(f"ValveCollar{zz:.0f}", tube_prof(DR_O, 1.05, zz - 0.25, zz + 0.25), M_PVC, seg=28, loc=(PMX, 0, 0))
glow(B_VALVE, [(0, 0.0)] + pulse(C["check"], 3.0, hold=1.2))
FLAPH = empty("FlapHinge", (PMX - DR_I + 0.05, 0, VZ))
FLAP = lathe("Flap", tube_prof(0.0, DR_I - 0.05, -0.14, 0.14), M_FLAP, seg=20); par(FLAP, FLAPH); FLAP.location = (DR_I - 0.05, 0, 0)
glow(B_FLAP, [(0, 0.0)] + pulse(C["flap"], 3.0, hold=1.4))
def flap_ang(t):
    on = pump_on(t) > 0.5 or backup_on(t) > 0.5
    if inw(t, T_VALVE) and t >= C["all"]: return 0.0
    return math.radians(-75) if on else 0.0
fa = []; cur = 0.0
for t in TS:
    tgt = flap_ang(t); cur += (tgt - cur) * (0.45 if tgt != 0 else 0.7); fa.append(cur)
bake(FLAPH, "rotation_euler", 1, fa)
windows(FLAPH, [(0, C["all"]), (C["and"], DUR)])
VALVE_X = [box(f"NoValveX{k}", PMX - 1.6, PMX + 1.6, -0.3, -0.2, VZ - 0.16, VZ + 0.16, M_REDG) for k in range(2)]
VALVE_X[0].rotation_euler = (0, math.radians(45), 0); VALVE_X[1].rotation_euler = (0, math.radians(-45), 0)
for o in VALVE_X:
    for v in o.data.vertices: v.co -= Vector((PMX, 0, VZ))
    o.location = (PMX, 0, VZ); windows(o, [(C["all"], C["and"])])
for o in (VALVE,): windows(o, [(0, C["all"]), (C["and"], DUR)])
# water column standing in the vertical pipe ("still full of water"), falls back without the valve
COL = lathe("PipeColumn", [(0.0, 0.0), (DR_I - 0.02, 0.0), (DR_I - 0.02, 1.0), (0.0, 1.0)], M_PIPEW, seg=20, loc=(PMX, 0, PZ0 + 6.0))
COL_H = 1.6 - (PZ0 + 6.0)
def col_h(t):
    if inw(t, T_HOOK): return COL_H
    if t < C["kicks"]: return 0.0
    if t < C["without"]: return COL_H
    if t < C["and"]:
        if t < C["all"]: return COL_H
        if pump_on(t) > 0.5: return COL_H
        # falls back: drains down in ~0.6 s after each stop
        stops = [C["all"], C["move"] + 0.5, C["wearing"]]
        s0 = max(s for s in stops if s <= t + 1e-6)
        return COL_H * (1 - lin((t - s0) / 0.6))
    return COL_H
bake(COL, "scale", 2, [max(0.01, col_h(t)) for t in TS])
glow(B_PIPEW, [(0, 0.0)] + pulse(C["full"], 0.5, hold=1.2) + pulse(C["fall"], 0.4, hold=0.8))

# battery backup: small pump on a bracket + battery box on the floor + its own line into the main pipe above the valve
BKP = empty("BackupPump", (BKX, 0.4, 0))
par(lathe("BackupShell", [(0.0, -27.8), (0.85, -27.8), (0.85, -25.0), (0.4, -24.6), (0.0, -24.6)], M_PUMP, a0=0.0, ang=2 * math.pi, seg=24), BKP)
box("BackupBracket", BKX - 1.1, BKX + 1.1, 0.0, 1.0, -28.2, -27.8, M_STEEL)
BKL = pipe_wall("BackupLine", fillet_path([(BKX, 0.4, -24.6), (BKX, 0.4, -18.0), (PMX - 0.5, 0.4, -18.0)], 0.8, 6, 0.4), 0.0, 0.3, M_PVC, a0=-math.pi, a1=math.pi, seg=12)
BATT = box("BatteryBox", 4.0, 11.0, 2.0, 7.0, FLZ, FLZ + 5.0, M_BATT)
BATTLED = box("BatteryLED", 6.5, 8.5, 1.95, 2.0, FLZ + 3.6, FLZ + 4.2, M_GREENG)
glow(B_BATT, [(0, 0.0)] + pulse(C["battery"], 2.0, hold=1.6))
CORD = poly_obj("BatteryCord", sag_pts((11.0, 3.5, FLZ + 2.0), (BKX - 0.6, 1.2, -24.8), 1.0, 14), 0.15, M_CABLE)
for o in (BKP, BKL, BATT, BATTLED, CORD, bpy.data.objects["BackupBracket"]): windows(o, [(C["thats"], C["is"])])

# ================= flows (glowing beads) =================
# soil water heading for the tile (right side) + seeping in; tile -> cross pipe -> pit; pump -> up -> out -> lawn; falling back
SOILP = []
for j in range(6):
    sx, sz = 62 + 9 * j % 30, -6 - 4.5 * j
    SOILP.append(P([Vector((sx, -0.35, sz)), Vector((TILE_X + 2.5, -0.35, TILE_Z + 1.2)), Vector((TILE_X, -0.35, TILE_Z))]))
for j, pth in enumerate(SOILP): beads(f"Seep{j}", pth, 3, 0.32, M_BEAD, [(C["water3"], C["as"])], 7.0)
XPATH = P(fillet_path(XP, 2.0, 6, 0.8))
beads("Cross", XPATH, 6, 0.42, M_BEAD, [(C["carries"] - 0.2, C["as"])], 8.0)
TILEP = P([Vector((TILE_X, 30, TILE_Z)), Vector((TILE_X, 0.2, TILE_Z))])
beads("Tile", TILEP, 6, 0.4, M_BEAD, [(C["seeps"], C["as"])], 9.0)
UPP = P(DPTS)
def up_wins():
    ws, on, t0 = [], False, 0.0
    for t in TS:
        o = pump_on(t) > 0.5
        if o and not on: t0 = t
        if not o and on: ws.append((t0, t))
        on = o
    if on: ws.append((t0, DUR))
    return ws
beads("Up", UPP, 18, 0.36, M_BEAD, up_wins(), 26.0)
BACKP = P([Vector((PMX, -0.3, 1.0)), Vector((PMX, -0.3, -24.0))])
beads("FallBack", BACKP, 8, 0.38, M_BEADR, [(C["all"], C["back"] + 0.4), (C["move"] + 0.5, C["again"] + 0.1)], 30.0)
BKUP = P(fillet_path([(BKX, -0.1, -24.6), (BKX, -0.1, -18.0), (PMX - 0.5, -0.1, -18.0), (PMX, -0.3, -18.0), (PMX, -0.3, 1.6), (WX1 + 6, -0.3, 1.6), (WX1 + 8, -0.3, 1.5), (95, -0.3, 1.5)], 0.8, 6, 0.6))
beads("BackupFlow", BKUP, 14, 0.3, M_BEADG, [(C["battery"], C["floats"])], 22.0)
# soil + groundwater cards on the section face (rise with the rain, press on the walls)
def gw_top(t):
    if t < C["after"]: return PW([(0, -40.0), (C["storm"], -30.0), (C["floods"], -16.0), (C["after"], -16.0)])(t)
    if t < C["so"]: return PW([(C["after"], -60.0), (C["fills"], -50.0), (C["water2"] + 0.4, -14.0), (C["so"], -14.0)])(t)
    if t < C["as"]: return PW([(C["so"], -14.0), (C["seeps"], -14.0), (C["sump"], -24.5), (C["as"], -24.5)])(t)
    if t < C["and"]: return -25.0
    if t < C["floats"]: return PW([(C["and"], -25.0), (C["fills3"], -14.0), (C["floats"], -14.0)])(t)
    return -26.0
GWS = []
for nm, x0, x1 in (("GWLeft", -170, -WX1 - 0.05), ("GWRight", WX1 + 0.05, 170)):
    o = box(nm, x0, x1, -0.32, -0.22, 0.0, 1.0, M_GW); o.location.z = SOIL_BOT
    bake(o, "scale", 2, [max(0.01, gw_top(t) - SOIL_BOT) for t in TS]); GWS.append(o)
o = box("GWUnder", -WX1 + 0.05, WX1 - 0.05, -0.32, -0.22, 0.0, 1.0, M_GW); o.location.z = SOIL_BOT
bake(o, "scale", 2, [max(0.01, min(PZ0 - 0.8, gw_top(t)) - SOIL_BOT) for t in TS]); GWS.append(o)
keyval(FAC_GW, [(0, 0.30), (C["after"], 0.30), (C["water2"], 0.55), (C["so"], 0.40)])
# pressure arrows at the walls and under the floor ("presses on the walls and the floor")
ARR = []
for k, (bx, bz, dx, dz) in enumerate([(60, -8, -1, 0), (60, -15, -1, 0), (-60, -8, 1, 0), (-60, -15, 1, 0), (-18, -40, 0, 1), (8, -40, 0, 1)]):
    bm = bmesh.new(); add_arrow(bm, (bx, bz), (dx, dz), 12.0 if dz == 0 else 9.0, 2.6, y=-0.6); o = mesh_obj(f"PressArrow{k}", bm, M_ARROW)
    piv = Vector((bx, -0.6, bz)); 
    for v in o.data.vertices: v.co -= piv
    o.location = piv
    d = Vector((dx, 0, dz))
    bake_loc(o, lambda t, piv=piv, d=d: tuple(piv + d * (1.2 * math.sin(2 * math.pi * 1.6 * t))))
    windows(o, [(C["presses"], C["so"])]); ARR.append(o)
glow(B_ARROW, [(0, 0.0), (C["presses"], 0.0), (C["presses"] + 0.25, 6.0), (C["so"], 6.0)])
# tile: perforated pipe along each footing (holes by boolean), gold glow on "pipe full of holes"
TILES = []
for sx in (1, -1):
    t_ = cyl(f"DrainTile{sx}", TILE_R, DEPTH + 2, "Y", (sx * TILE_X, (DEPTH + 2) / 2, TILE_Z), M_TILE, seg=28); TILES.append(t_)
    bm = bmesh.new()
    for yy in range(2, int(DEPTH), 4):
        for a in (-55, 0, 55):
            add_cyl(bm, 0.3, 1.2, "Z", (0, 0, 0), seg=8)
            vs = bm.verts[-16:]
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(a), 3, "Y"))
            bmesh.ops.translate(bm, verts=vs, vec=(sx * TILE_X + TILE_R * math.sin(math.radians(a)), yy, TILE_Z + TILE_R * math.cos(math.radians(a))))
    hc = mesh_obj(f"TileHoles{sx}", bm, M_HOLE); hc.hide_render = True; hc.display_type = "WIRE"; md_ = boolean(t_, hc)
    try: md_.material_mode = "TRANSFER"
    except Exception: pass
    bm = bmesh.new(); add_cyl(bm, TILE_R - 0.15, DEPTH + 2.4, "Y", (sx * TILE_X, (DEPTH + 2) / 2, TILE_Z), seg=28)
    inner = mesh_obj(f"TileBore{sx}", bm, M_HOLE); inner.hide_render = True; inner.display_type = "WIRE"; md_ = boolean(t_, inner, "Bore")
    try: md_.material_mode = "TRANSFER"
    except Exception: pass
    for o in ([bpy.data.objects["TileGravel1"], bpy.data.objects["TileGravel1Front"]] if sx == 1 else [bpy.data.objects[f"TileGravel{sx}"]]):
        bm = bmesh.new(); add_cyl(bm, TILE_R + 0.05, DEPTH + 3, "Y", (sx * TILE_X, (DEPTH + 2) / 2, TILE_Z), seg=28)
        tcut = mesh_obj(f"TileCut{sx}", bm, None); tcut.hide_render = True; tcut.display_type = "WIRE"; boolean(o, tcut, "TileCut")
glow(B_TILE, [(0, 0.0)] + pulse(C["pipe"], 0.45, hold=2.2) + pulse(C["carries"], 0.35, hold=1.5))
XPIPE = pipe_wall("CrossPipe", fillet_path(XP, 2.0, 6, 0.8), 0.72, 0.9, M_TILE, a0=0.0, a1=math.pi, seg=16)

# ================= storm outside: power pole, line, tree, falling branch (rigid body) =================
POLE_X = 128.0
full_cyl("Pole", 0.9, POLE_X, 30, GZ, 46, M_POLE)
box("CrossArm", POLE_X - 5, POLE_X + 5, 29.4, 30.6, 43.5, 44.5, M_POLE)
LINE = poly_obj("ServiceLine", sag_pts((POLE_X - 1, 30, 43.0), (WX1 + 0.5, 30, 26.0), 3.0, 18), 0.16, M_CABLE)
TREE_X = 104.0
full_cyl("TreeTrunk", 1.6, TREE_X, 45, GZ, 38, M_BARK)
for k, (dx, dz, r) in enumerate([(0, 40, 9), (-6, 35, 7), (6, 35, 7), (0, 47, 6)]):
    o = obj_from(f"Crown{k}", sphere_mesh(f"CrownMe{k}", r, 2), M_LEAF, (TREE_X + dx, 45, dz))
bm = bmesh.new(); add_seg(bm, (0, 0, 0), (-22, 0, -3), 0.9, 10); add_seg(bm, (-10, 0, -1.5), (-14, 3, 2), 0.5, 8); add_seg(bm, (-16, 0, -2.4), (-20, -2, 1), 0.4, 8)
BRANCH = mesh_obj("Branch", bm, M_BARK)
BRANCH.location = (TREE_X - 2, 30, 33.0)
fx.rigid([BRANCH], passive=[], mass=60.0, friction=0.8, bounce=0.1)
GROUND_RB = box("GroundCollider", -170, 170, 0, 90, -2, GZ + 0.4, None); GROUND_RB.hide_render = True; GROUND_RB.display_type = "WIRE"
LINE_RB = poly_obj("LineCollider", sag_pts((POLE_X - 1, 30, 43.0), (WX1 + 0.5, 30, 26.0), 3.0, 18), 0.5, None); LINE_RB.hide_render = True; LINE_RB.display_type = "WIRE"
fx.rigid([], passive=[GROUND_RB, LINE_RB], mass=1.0, friction=0.8, bounce=0.1)
try:
    BRANCH.rigid_body.kinematic = True
    BRANCH.rigid_body.keyframe_insert("kinematic", frame=F(C["knock"]) - 1)
    BRANCH.rigid_body.kinematic = False
    BRANCH.rigid_body.keyframe_insert("kinematic", frame=F(C["knock"]))
except Exception as e: print("branch kinematic key skipped", e)
scene.gravity = (0, 0, -98.1)                       # 1 unit = 10 cm
# spark burst where the branch hits the line
SPK_LINE = obj_from("LineSparkEmitter", sphere_mesh("LineSparkMe", 0.6, 1), None, (TREE_X - 14, 30, 31.0)); SPK_LINE.hide_render = False
ps_line = fx.particles(SPK_LINE, "sparks", F(C["power"]) - 4, F(C["power"]) + 6, count=220)
# rain (two short systems: stake + storm)
RAIN1 = box("RainEmitter1", -80, 170, 0, 70, 70, 70.2, None); RAIN2 = box("RainEmitter2", -80, 170, 0, 70, 70, 70.2, None)
pr1 = fx.particles(RAIN1, "rain", 1, F(C["soil"]), count=2500)
pr2 = fx.particles(RAIN2, "rain", max(1, F(C["and"]) - 25), F(C["floats"]), count=2500)
# sparks at the worn motor
SPK_M = obj_from("MotorSparkEmitter", sphere_mesh("MotorSparkMe", 0.5, 1), None, (PMX + 0.6, -0.2, PZ0 + 4.0))
ps_m = fx.particles(SPK_M, "sparks", F(C["wearing"]), F(C["and"]), count=160)
def tune(mod, size, vel, life, grav=None):
    try:
        s = mod.particle_system.settings; s.particle_size = size; s.normal_factor = vel; s.lifetime = life
        if grav is not None: s.effector_weights.gravity = grav
    except Exception as e: print("[fx] particle tune skipped:", e)
for m_ in (pr1, pr2): tune(m_, 0.09, -60.0, 14, 1.0)
tune(ps_line, 0.18, 14.0, 12, 0.6); tune(ps_m, 0.08, 6.0, 10, 0.4)
for e_ in (RAIN1, RAIN2, SPK_LINE, SPK_M):
    e_.show_instancer_for_render = False
    try: e_.display_type = "WIRE"
    except Exception: pass
try:
    for m_ in (pr1, pr2):
        s = m_.particle_system.settings; s.instance_object.scale = (1, 1, 8)     # streaks
except Exception as e: print("rain streak skipped", e)

# ================= floor flood (stake): rising water slab + Mantaflow overflow (laptop --bake-fluid) =================
FLOOD = box("FloodSlab", -WX0 + 0.05, WX0 - 0.05, 0.0, DEPTH - 0.05, FLZ, FLZ + 1.0, M_FLOODW)
bake(FLOOD, "scale", 2, [max(0.01, 2.2 * ease((t - C["floods"] + 0.3) / 2.0)) if inw(t, T_STAKE) else 0.01 for t in TS])
for v in FLOOD.data.vertices: v.co.z -= FLZ
FLOOD.location.z = FLZ
windows(FLOOD, [(C["floods"] - 0.3, C["after"])])
FL_DOM = box("FluidDomain", PX - 12, PX + 12, 0.0, 16.0, FLZ, FLZ + 5.0, None); FL_DOM.display_type = "WIRE"
FL_IN = obj_from("FluidInflow", sphere_mesh("FluidInMe", 1.2, 2), None, (PX, 3.0, FLZ + 0.6)); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
FL_RB = box("FloorRB", PX - 20, PX + 20, -5, 25, FLZ - 2.0, FLZ, None); FL_RB.hide_render = True; FL_RB.display_type = "WIRE"
fx.fluid_domain(FL_DOM, FL_IN, eff=[FL_RB], res=64, start=F(C["floods"] - 0.3), end=F(C["floods"] + 3.0), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_DOM.data.materials.append(water_sec("FluidWater")[0])
windows(FL_DOM, [(C["floods"] - 0.3, C["after"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True

# ================= outdoor pipe end: ice plug ("freeze solid") =================
ICE = lathe("IcePlug", tube_prof(0.0, DR_O + 0.35, 0.0, 9.0), M_ICE, a0=-math.pi / 2, ang=math.pi, seg=16)
ICE.rotation_euler = (0, math.radians(90), 0); ICE.location = (86.0, 0, 1.5)
bake(ICE, "scale", 2, [1.0 * ease((t - C["freeze"] + 0.2) / 0.8) + 0.001 for t in TS])
windows(ICE, [(C["freeze"] - 0.2, C["most"])])
ICEBEADS = beads("Blocked", P([Vector((WX1 + 9, -0.3, 1.5)), Vector((84.5, -0.3, 1.5))]), 6, 0.3, M_BEADR, [(C["freeze"] + 0.3, C["most"])], 0.0)
for k, o in enumerate(ICEBEADS): bake_loc(o, lambda t, k=k: (84.0 - 1.2 * k, -0.3, 1.5))

# ================= CTA: gold ring around the pit on the floor =================
CTA_RING = lathe("CTARing", tube_prof(PR + 0.5, PR + 1.1, FLZ + 0.02, FLZ + 0.22), M_GOLDG, a0=0.0, ang=2 * math.pi, seg=48, loc=(PX, 0, 0))
windows(CTA_RING, [(C["pit2"] - 0.1, DUR)])
glow(B_GOLDG, [(0, 6.0)])
# hook: gold ring too (the hole, on purpose)
HOOK_RING = lathe("HookRing", tube_prof(PR + 0.5, PR + 1.1, FLZ + 0.02, FLZ + 0.22), M_GOLDG, a0=0.0, ang=2 * math.pi, seg=48, loc=(PX, 0, 0))
windows(HOOK_RING, [(C["hole"] - 0.05, C["water"])])

# ================= fx: hdri, glare, scatter =================
fx.hdri("night", strength=0.9, rotation_deg=200.0, show_background=True)
fx.glare(threshold=1.0, strength=0.55, size=7)
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.45)
STONE = mesh_obj("StoneProto", bm, M_STONE)
GFACE = box("GravelFaceCard", -WX0 + 0.5, WX0 - 0.5, -0.08, -0.02, FT["z0"] + 0.3, SLAB0 - 0.2, M_GRAVEL)
boolean(GFACE, PITCUT, "PitCut"); boolean(GFACE, XPC, "Cross")
fx.scatter(GFACE, STONE, density=1.4, scale_min=0.5, scale_max=1.3, seed=1)
for sx in (1, -1):
    gf = box(f"TileGravelCard{sx}", sx * (FT["x1"] - 0.3), sx * (FT["x1"] + 5.3), -0.08, -0.02, FT["z0"] + 0.3, -22.8, M_GRAVEL)
    bm = bmesh.new(); add_cyl(bm, TILE_R + 0.1, 2.0, "Y", (sx * TILE_X, 0, TILE_Z), seg=28)
    tc_ = mesh_obj(f"TileCardCut{sx}", bm, None); tc_.hide_render = True; tc_.display_type = "WIRE"; boolean(gf, tc_)
    if sx == 1: boolean(gf, XPC, "Cross")
    fx.scatter(gf, STONE, density=1.4, scale_min=0.5, scale_max=1.3, seed=2 + sx)
bm = bmesh.new(); add_cyl(bm, 0.12, 1.2, "Z", (0, 0, 0.6), seg=5, r2=0.0); add_cyl(bm, 0.1, 0.9, "Z", (0.25, 0, 0.45), seg=5, r2=0.0)
TUFT = mesh_obj("TuftProto", bm, M_TUFT)
for g_ in (GRASS_L, GRASS_R, GRASS_RF): fx.scatter(g_, TUFT, density=0.35, scale_min=0.5, scale_max=1.3, seed=7)
for o_ in (STONE, TUFT): o_.location = (0, 0, -2000)

XRAY = (C["so"], C["water3"])
for o in [SOIL_RF, GRASS_RF, bpy.data.objects["TileGravel1Front"], bpy.data.objects["TileGravelCard1"], GWS[1]]: windows(o, [(0.0, XRAY[0]), (XRAY[1], DUR)])
# ================= lights =================
sun_d = bpy.data.lights.new("Moon", "SUN"); sun_d.energy = 0.6; sun_d.angle = math.radians(3.0); sun_d.color = (0.70, 0.80, 1.0)
sun = bpy.data.objects.new("Moon", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(55), 0, math.radians(-25))
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.92, 0.82)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("SectionKey", (10, -80, -5), 170.0, 2.4e4, rot=(math.radians(90), 0, 0), color=(1.0, 0.93, 0.86))
area("SectionLow", (20, -45, -40), 120.0, 0.8e4, rot=(math.radians(105), 0, 0), color=(0.75, 0.85, 1.0))
area("YardKey", (90, -90, 50), 140.0, 1.5e4, rot=(math.radians(65), 0, 0), color=(0.80, 0.86, 1.0))
# lightning flashes in the storm beats
flash_d = bpy.data.lights.new("Lightning", "SUN"); flash_d.angle = math.radians(8); flash_d.color = (0.85, 0.9, 1.0)
flash = bpy.data.objects.new("Lightning", flash_d); scene.collection.objects.link(flash); flash.rotation_euler = (math.radians(30), 0, math.radians(30))
FLASHES = [C["storm"] - 0.1, C["after"] + 0.4, C["worst"], C["knock"] + 0.3]
def flash_e(t):
    v = 0.0
    for f0 in FLASHES:
        if f0 <= t < f0 + 0.25: v = max(v, 9.0 * (1 - (t - f0) / 0.25))
    return v
bake_scalar(flash_d, "energy", [flash_e(t) for t in TS])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 6000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (14, -26, -11), (20, 4, -26), 28),                                    # hook: the hole in the floor, pump running
    (C["water"] - 0.05, (16, -34, -9), (20, 4, -25), 28),
    (C["water"], (25, -150, -12), (25, 20, -22), 26, "cut"),                     # the ground pushing water in
    (C["if"] - 0.05, (25, -138, -12), (25, 20, -22), 26),
    (C["if"], (45, -210, 30), (45, 20, 4), 26, "cut"),                           # stake: storm, lights out
    (C["floods"] - 0.35, (45, -195, 26), (45, 20, 2), 26),
    (C["floods"] - 0.3, (2, -62, -12), (16, 12, -21), 28, "cut"),               # basement floods
    (C["after"] - 0.05, (4, -52, -14), (16, 12, -21), 28),
    (C["after"], (70, -175, 4), (70, 20, -26), 26, "cut"),                       # rain, soil fills with water
    (C["that"] - 0.05, (68, -160, 0), (66, 20, -26), 26),
    (C["that"], (8, -130, -14), (5, 20, -22), 26, "cut"),                        # presses on walls + floor
    (C["finds"], (-34, -45, -12), (-41, 5, -15), 30),                             # finds every crack
    (C["so"] - 0.05, (-35, -42, -13), (-41, 5, -15), 30),
    (C["so"], (57, -7, -20.5), (TILE_X, 14, -25.6), 30, "cut"),                    # perforated drain tile along the footing
    (C["water3"] - 0.05, (56, -9, -19.5), (TILE_X, 12, -25.6), 30),
    (C["water3"], (55, -55, -18), (45, 4, -25), 28, "cut"),                       # seeps in, carried to the pit
    (C["sump"] - 0.05, (36, -55, -16), (28, 4, -26), 28),
    (C["as"], (20, -21, -24.5), (21, 3, -27), 32, "cut"),                         # float rides up
    (C["flips"], (21.5, -14, -23.5), (22.5, 2, -24.6), 34),                        # flips the switch
    (C["kicks"] - 0.05, (21.5, -13, -23.6), (22.5, 2, -24.6), 34),
    (C["impeller"], (19.5, -9, -28.8), (20.9, 2, -30.0), 34, "cut"),               # impeller close
    (C["throws"] - 0.05, (19.5, -10, -28.5), (20.9, 2, -29.8), 34),
    (C["throws"], (24, -40, -24), (21, 3, -22), 30, "cut"),                        # up the pipe
    (C["out"] - 0.05, (28, -62, -4), (25, 3, -6), 30),
    (C["out"], (68, -120, 18), (66, 15, 0), 28, "cut"),                            # out of the house, away from the walls
    (C["when"] - 0.05, (74, -112, 15), (70, 15, 0), 28),
    (C["when"], (20, -22, -24.5), (21, 3, -27), 32, "cut"),                        # level drops, float falls, pump off
    (C["but"] - 0.05, (20, -24, -24), (21, 3, -26.5), 32),
    (C["but"], (19, -46, -11), (20.9, 2, -12), 28, "cut"),                         # pipe still full of water
    (C["without"] - 0.05, (19, -40, -12), (20.9, 2, -13), 28),
    (C["without"], (19.6, -11, -15.4), (20.9, 2, -16), 34, "cut"),                 # check valve close
    (C["all"] - 0.05, (19.6, -10, -15.6), (20.9, 2, -16), 34),
    (C["all"], (17, -48, -14), (20.9, 3, -20), 28, "cut"),                         # falls back, pumps again and again
    (C["wearing"] - 0.05, (17, -44, -16), (20.9, 3, -21), 28),
    (C["wearing"], (20.0, -10, -26.0), (20.9, 2, -27.6), 34, "cut"),               # motor wearing out (sparks)
    (C["and"] - 0.05, (20.2, -9, -26.2), (20.9, 2, -27.6), 34),
    (C["and"], (70, -230, 36), (70, 20, 8), 26, "cut"),                            # storm: branch on the line, power out
    (C["power"], (80, -200, 34), (80, 20, 12), 26),
    (C["thats"] - 0.05, (80, -196, 33), (80, 20, 12), 26),
    (C["thats"], (8, -38, -17), (15, 4, -24), 30, "cut"),                          # battery backup
    (C["floats"] - 0.05, (10, -34, -18), (16, 4, -24), 30),
    (C["floats"], (21, -17, -24.5), (22.5, 2, -26.2), 34, "cut"),                  # stuck float
    (C["winter"] - 0.05, (21.2, -16, -24.6), (22.5, 2, -26.2), 34),
    (C["winter"], (82, -16, 4.5), (86, 2, 1.5), 34, "cut"),                          # outdoor pipe freezes solid
    (C["most"] - 0.05, (83, -14, 4.0), (86.5, 2, 1.5), 34),
    (C["most"], (16, -20, -25.5), (20.9, 2, -27.5), 32, "cut"),                    # pump ageing, 7-10 years
    (C["is"] - 0.05, (17, -18, -25.5), (20.9, 2, -27.5), 32),
    (C["is"], (22, -80, -10), (20, 20, -20), 26, "cut"),                           # CTA: pull-out over the pit
    (DUR, (24, -112, -2), (20, 20, -17), 26),
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
bake_scalar(fill_d, "energy", [max(50.0, min(3.0e4, 0.5 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
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
scene.view_settings.exposure = float(arg("--exposure", "-0.2"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["knock"]) - 2, F(C["thats"]) + 5)
windows_r(BRANCH, [(0.0, C["after"]), (C["and"], C["thats"])])
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "pit": (PX - PR, 0, FLZ + 0.5), "pump": (PMX + PMR, 0, PZ0 + 4.0), "soil": (110, 0, -30), "wall": (WX1, 0, -10), "wallL": (-WX1, 0, -12),
    "tile": (TILE_X + TILE_R, 0, TILE_Z), "tile_far": (TILE_X + TILE_R, 20, TILE_Z), "footing": (FT["x1"], 0, -25.5), "float": W(FLOAT, (0.55, 0, 0)),
    "switch": (FRX + 0.55, 0, -23.1), "impeller": (PMX + 0.95, -0.4, PZ0 + 0.9), "pipe": (PMX + DR_O, 0, -8), "valve": (PMX + 0.95, 0, VZ),
    "flap": (PMX, 0, VZ), "outlet": (90, 0, 1.5), "motor": (PMX + PMR, 0, PZ0 + 3.8), "line": (TREE_X - 14, 30, 31), "battery": (11, 2, FLZ + 4),
    "backup": (BKX - 0.85, 0.4, -26.0), "ice": (86, 0, 1.6), "crack": (-41, 0, -14), "groundwater": (100, 0, -20),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
def edges(fn):
    on, out, t0 = False, [], 0.0
    for t in TS:
        o = fn(t) > 0.5
        if o and not on: t0 = t
        if not o and on: out.append(RR(t0, t))
        on = o
    if on: out.append(RR(t0, DUR))
    return out
events = {"cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4], "pump_runs": edges(pump_on), "backup_runs": edges(backup_on),
          "lights_out": [round(C["stops"], 3), round(OFF + 0.06, 3)], "flood": RR(C["floods"] - 0.3, C["after"]), "rain": [RR(0.0, C["soil"]), RR(C["and"] - 0.8, C["floats"])],
          "lightning": [round(x, 3) for x in FLASHES], "press": RR(C["presses"], C["so"]), "crack": round(C["crack"], 3), "seep": RR(C["seeps"], C["as"]),
          "float_up": RR(C["as"], C["flips"]), "switch": round(C["flips"], 3), "valve_shut": [round(C["shuts"], 3)], "fall_back": [round(C["all"], 3), round(C["move"] + 0.5, 3), round(C["wearing"], 3)],
          "sparks": RR(C["wearing"], C["and"]), "branch": round(C["knock"], 3), "line_spark": round(C["power"], 3), "stuck": round(C["stuck"], 3),
          "freeze": round(C["freeze"], 3), "rust": RR(C["seven"], C["years"]), "ring": round(C["pit2"], 3)}
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
