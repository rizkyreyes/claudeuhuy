# Washer debris filter door (3d-38): what hides behind the tiny door at the bottom of a front-load washer. Claim hook "That tiny door at
# the bottom of your front-load washer hides a trap for everything your pockets forget." -> stake: ignore it and the washer stops draining,
# clothes in dirty water -> side cutaway: the drain pump switches on, impeller pushes the water out of the drum, up the drain hose, into the
# standpipe -> passengers (coins, buttons, plastic, lint) ride down; what-if: a coin reaches the impeller (sparks) -> the plastic strainer in
# front of the pump: water slips through the slots, junk doesn't; it's also the lint filter -> months: lint packs tight, flow slows to a
# trickle, error light (Whirlpool: drain over 8 min) -> cleaning: towels + shallow pan, hot water waits behind the door, emergency hose
# drains it, twist the filter counterclockwise, pull it out (the gross reveal), rinse (junk falls into the pan, rigid body), impeller spins
# freely, screw back tight or it leaks -> calendar: every month (LG) vs 5-6 times a year (Samsung) -> CTA push-in on the little door.
# Illustrative, 1 unit = 1 cm: generic washer (no brand, no text, no logo), generic laundry room. No people, no hands.
# Section plane x = PX (pump, hoses, cabinet) and x = 0 (tub + drum); the camera looks from +x.
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
random.seed(38)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("that","That"),("tiny","tiny"),("door","door"),("bottom","bottom"),("washer","washer"),("hides","hides"),("trap","trap"),
  ("everything","everything"),("pockets","pockets"),("forget","forget."),("ignore","Ignore"),("stop","stop"),("draining","draining,"),
  ("leaving","leaving"),("clothes","clothes"),("dirty","dirty"),("water","water."),("at","At"),("end","end"),("wash","wash"),("rinse","rinse,"),
  ("electric","electric"),("pump","pump"),("switches","switches"),("on","on."),("its","Its"),("spinning","spinning"),("impeller","impeller"),
  ("pushes","pushes"),("drum","drum,"),("up","up"),("hose","hose,"),("into","into"),("drain2","drain"),("pipe","pipe."),("but","But"),
  ("carries","carries"),("passengers","passengers:"),("coins","coins,"),("buttons","buttons,"),("bits","bits"),("plastic","plastic,"),
  ("loads","loads"),("lint","lint."),("junk","junk"),("chew","chew"),("impeller2","impeller."),("so","So"),("front","front"),("pump2","pump"),
  ("plastic2","plastic"),("strainer","strainer."),("water2","Water"),("slips","slips"),("slots","slots."),("junk2","Junk"),("doesnt","doesn't."),
  ("also","also"),("lint2","lint"),("filter","filter."),("over","Over"),("months","months,"),("packs","packs"),("tight","tight."),
  ("water3","water"),("slows","slows"),("trickle","trickle,"),("drain3","drain"),("long","long."),("some","some"),("whirlpool","Whirlpool"),
  ("drain4","drain"),("eight","eight"),("minutes","minutes"),("throws","throws"),("error","error"),("code","code."),("before","Before"),
  ("opening","opening"),("door2","door,"),("lay","lay"),("towels","towels"),("pan","pan."),("water4","Water"),("waits","waits"),("hot","hot"),
  ("burn","burn."),("many","Many"),("hose2","hose"),("drain5","drain"),("twist","Twist"),("filter2","filter"),("ccw","counterclockwise,"),
  ("pull","pull"),("out","out,"),("rinse2","rinse"),("warm","warm"),("check","Check"),("impeller3","impeller"),("spins","spins"),
  ("freely","freely."),("screw","Screw"),("back","back"),("tight2","tight,"),("leak","leak."),("lg","LG"),("every","every"),("month","month."),
  ("samsung","Samsung"),("five","five"),("six","six"),("year","year."),("when","When"),("last","last"),("open","open"),("yours","yours?"),
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
CL = coll("Washer")
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
scene.gravity = (0.0, 0.0, -981.0)          # cm world: real gravity for rigid bodies and particles
PX, PZ = 19.0, 9.0                          # pump/filter axis (along y) and the section plane of pump, hoses and cabinet
X_CAL = 400.0                               # calendar set, far to the side
def cut_x(bm, x0, fill=True):
    """Keep x <= x0 (the camera looks from +x), cap the cut."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
    if fill:
        oe = [e for e in bm.edges if len(e.link_faces) < 2]
        if oe:
            try: bmesh.ops.edgeloop_fill(bm, edges=oe)
            except Exception: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def ylathe(name, prof, m_, loc, half=True, seg=48):
    """Lathe around +y (profile (r, y_local)); half=True keeps x <= 0 of the object (section)."""
    o = lathe(name, prof, m_, a0=math.pi / 2 if half else 0.0, ang=math.pi if half else 2 * math.pi, seg=seg)
    if not half:
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    o.rotation_euler = (-math.pi / 2, 0, 0); o.location = loc; return o
def sec_pipe(name, pts, r, m_, x0=PX, seg=20, smooth_it=2):
    pts = chaikin([Vector(p) for p in pts], smooth_it)
    bm = sweep_bm(pts, [r] * len(pts), seg, cap=False); cut_x(bm, x0, fill=False)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    solidify(o, 0.25); return o, pts
def rgb_mat(name, rgb, rough=0.4, metallic=0.0, emit=(1, 1, 1)):
    return mat(name, rgb, rough=rough, metallic=metallic, emit_rgb=emit)

# ---------- beat windows ----------
T_HOOK = (0.0, C["ignore"]); T_STAKE = (C["ignore"], C["at"]); T_PUMP = (C["at"], C["but"]); T_JUNK = (C["but"], C["so"])
T_STRAIN = (C["so"], C["some"] - 0.13); T_ERR = (C["some"] - 0.13, C["before"]); T_CLEAN = (C["before"], C["lg"]); T_CAL = (C["lg"], C["when"])
T_CTA = (C["when"], DUR)
# cutaway (right side of the cabinet removed) in these windows; exterior otherwise
CUT = [(C["hides"], C["some"] - 0.13), (C["water4"], C["many"]), (C["check"], C["screw"])]
def is_cut(t): return any(a <= t < b for a, b in CUT)

# ---------- materials ----------
M_WHITE, B_WHITE = mat("CabinetWhite", (0.86, 0.87, 0.88), rough=0.28)
M_SEC, B_SEC = mat("CutFace", (0.98, 0.55, 0.12), rough=0.5, emit_rgb=(1.0, 0.45, 0.1)); B_SEC.inputs["Emission Strength"].default_value = 0.6
M_TUB, _ = mat("TubGrey", (0.30, 0.32, 0.34), rough=0.5)
M_STEEL, _ = mat("DrumSteel", (0.75, 0.76, 0.78), rough=0.22, metallic=1.0)
M_DARK, _ = mat("DarkPlastic", (0.05, 0.05, 0.06), rough=0.45)
M_HOUSE, B_HOUSE = mat("HousingGrey", (0.18, 0.19, 0.21), rough=0.4, emit_rgb=(1.0, 0.3, 0.24))
M_CART, B_CART = mat("Strainer", (0.92, 0.92, 0.90), rough=0.35, emit_rgb=(0.30, 0.92, 1.0))
M_IMP, B_IMP = mat("Impeller", (0.85, 0.86, 0.88), rough=0.3, emit_rgb=(0.30, 0.92, 1.0))
M_MOTOR, B_MOTOR = mat("MotorCopper", (0.72, 0.38, 0.18), rough=0.3, metallic=1.0, emit_rgb=(1.0, 0.74, 0.27))
M_HOSE, _ = mat("HoseGrey", (0.55, 0.57, 0.6), rough=0.5)
M_BLACKHOSE, _ = mat("BlackHose", (0.03, 0.03, 0.03), rough=0.5)
M_GLASS, _ = mat("DoorGlass", (0.05, 0.07, 0.09), rough=0.05, metallic=0.4)
M_CHROME, _ = mat("Chrome", (0.9, 0.9, 0.92), rough=0.1, metallic=1.0)
M_TOWEL, _ = mat("Towel", (0.12, 0.32, 0.62), rough=0.95, noise=40)
M_PAN, _ = mat("Pan", (0.70, 0.71, 0.73), rough=0.3, metallic=1.0)
M_LED, B_LED = mat("Led", (0.02, 0.02, 0.02), rough=0.4, emit_rgb=(1.0, 0.3, 0.24))
M_COIN_G, _ = mat("CoinCopper", (0.78, 0.45, 0.25), rough=0.25, metallic=1.0)
M_COIN_S, _ = mat("CoinSilver", (0.8, 0.8, 0.82), rough=0.25, metallic=1.0)
M_LINT, B_LINT = mat("Lint", (0.36, 0.33, 0.30), rough=1.0, noise=25, emit_rgb=(1.0, 0.74, 0.27))
JUNK_COLS = [(0.85, 0.15, 0.12), (0.10, 0.35, 0.85), (0.95, 0.75, 0.10), (0.10, 0.65, 0.30), (0.9, 0.9, 0.9)]
M_JUNK = [mat(f"Junk{i}", c, rough=0.4, emit_rgb=(1.0, 0.3, 0.24)) for i, c in enumerate(JUNK_COLS)]
M_CLOTH = [mat(f"Cloth{i}", c, rough=0.95, noise=30)[0] for i, c in enumerate([(0.15, 0.2, 0.45), (0.6, 0.1, 0.12), (0.75, 0.72, 0.6), (0.2, 0.4, 0.25)])]
M_WCLEAN, B_WCLEAN, _ = water_sec("WaterClean")
M_WDIRTY, B_WDIRTY, _ = water_sec("WaterDirty", glow_rgb=(1.0, 0.3, 0.24), vol_rgb=(0.35, 0.25, 0.12), dens=0.25)
M_WHOT, B_WHOT, _ = water_sec("WaterHousing", glow_rgb=(1.0, 0.35, 0.12))
M_BEAD, B_BEAD = emit_mat("BeadCyan", (0.30, 0.92, 1.0), 6.0)
M_RED, B_REDD = emit_mat("DropRed", (1.0, 0.3, 0.24), 5.0)
M_TILE_DIM, B_TILE_DIM = mat("TileDim", (0.10, 0.11, 0.13), rough=0.4, emit_rgb=(0.98, 0.74, 0.27))
FLOOR_M = tiles("FloorTiles", (0.16, 0.165, 0.17), (0.13, 0.135, 0.14), 0.025, plane="XY")
WALL_M, WALL_B = mat("Wall", (0.07, 0.085, 0.11), rough=0.8)

# ================= room =================
floor = box("Floor", -200, 520, -220, 48, -1, 0, FLOOR_M)
wall = box("WallBack", -200, 520, 48, 50, 0, 200, WALL_M)
wall_l = box("WallLeft", -42, -40, -120, 48, 0, 200, WALL_M)

# ================= cabinet (x -30..30, y -32..30, z 1..86) =================
CX0, CX1, CY0, CY1, CZ0, CZ1 = -30.0, 30.0, -32.0, 30.0, 1.0, 86.0
DOOR_Z, DOOR_R = 50.0, 17.0
KD = (12.0, 26.0, 3.0, 15.0)                # kick door opening x0, x1, z0, z1
def cab_part(name, x0, x1, y0, y1, z0, z1): return rbox(name, x0, x1, y0, y1, z0, z1, 0.6, M_WHITE)
LEFT = cab_part("CabLeft", CX0, CX0 + 1, CY0, CY1, CZ0, CZ1)
BACK = cab_part("CabBack_L", CX0, PX, CY1 - 1, CY1, CZ0, CZ1)
TOP_L = cab_part("CabTop_L", CX0, PX, CY0, CY1, CZ1 - 1, CZ1)
BASE_L = cab_part("CabBase_L", CX0, PX, CY0, CY1, CZ0, CZ0 + 1)
FEET = [cyl(f"Foot{i}", 2.0, 1.2, "Z", (x, y, 0.6), M_DARK) for i, (x, y) in enumerate([(-26, -28), (26, -28), (-26, 26), (26, 26)])]
# front panel with the porthole and the kick-door opening, split at PX
def front_panel(name, x0, x1):
    bm = bmesh.new()
    add_box(bm, x0, x1, CY0, CY0 + 1, KD[3], CZ1)                        # above the kick door
    add_box(bm, x0, x1, CY0, CY0 + 1, CZ0, KD[2])                        # below
    if x0 < KD[0]: add_box(bm, x0, min(x1, KD[0]), CY0, CY0 + 1, KD[2], KD[3])
    if x1 > KD[1]: add_box(bm, max(x0, KD[1]), x1, CY0, CY0 + 1, KD[2], KD[3])
    o = mesh_obj(name, bm, M_WHITE)
    c = cyl(name + "_hole", DOOR_R + 1.5, 6, "Y", (0, CY0 + 0.5, DOOR_Z), None, seg=64); c.hide_render = True; c.display_type = "WIRE"
    boolean(o, c); return o
FRONT_L = front_panel("Front_L", CX0, PX); FRONT_R = front_panel("Front_R", PX, CX1)
RIGHT = cab_part("CabRight", CX1 - 1, CX1, CY0, CY1, CZ0, CZ1)
BACK_R = cab_part("CabBack_R", PX, CX1, CY1 - 1, CY1, CZ0, CZ1)
TOP_R = cab_part("CabTop_R", PX, CX1, CY0, CY1, CZ1 - 1, CZ1)
BASE_R = cab_part("CabBase_R", PX, CX1, CY0, CY1, CZ0, CZ0 + 1)
EXTERIOR_ONLY = [FRONT_R, RIGHT, BACK_R, TOP_R, BASE_R]
# cut faces glow orange like a section (thin plates on the cut plane)
SEC_FACES = [box("SecFront", PX - 0.05, PX + 0.05, CY0, CY0 + 1, KD[3], CZ1, M_SEC), box("SecTop", PX - 0.05, PX + 0.05, CY0, CY1, CZ1 - 1, CZ1, M_SEC),
             box("SecBack", PX - 0.05, PX + 0.05, CY1 - 1, CY1, CZ0, CZ1, M_SEC), box("SecBase", PX - 0.05, PX + 0.05, CY0, CY1, CZ0, CZ0 + 1, M_SEC)]
# porthole: chrome ring + dark glass
ring = torus("DoorRing", DOOR_R + 1.2, 1.6, M_CHROME, (0, CY0 - 0.8, DOOR_Z)); ring.rotation_euler = (math.pi / 2, 0, 0)
glass = cyl("DoorGlass", DOOR_R, 1.0, "Y", (0, CY0 - 0.6, DOOR_Z), M_GLASS, seg=64)
# control strip: knob, drawer, display + error LED (generic, no text)
knob = cyl("Knob", 3.2, 2.0, "Y", (14, CY0 - 1.0, 79.5), M_CHROME, seg=40)
drawer = rbox("Drawer", -27, -10, CY0 - 0.8, CY0 + 0.2, 75, 83, 0.5, M_WHITE)
disp = rbox("Display", -5, 6, CY0 - 0.6, CY0 + 0.2, 76.5, 82.5, 0.4, M_DARK)
led = cyl("ErrLed", 0.9, 0.5, "Y", (3.5, CY0 - 0.8, 79.5), M_LED, seg=20)
glow(B_LED, [(0, 0.0), (C["error"] - 0.01, 0.0)] + [kv for k in range(6) for kv in ((C["error"] + 0.5 * k, 30.0), (C["error"] + 0.5 * k + 0.25, 0.0))])

# kick door on a bottom hinge (opens down towards the camera), full + section versions
HINGE = empty("KickHinge", (19.0, CY0 - 0.2, KD[2]))
kd_full = rbox("KickDoor", -7, 7, -0.5, 0.0, 0.0, 12.0, 0.4, M_WHITE); par(kd_full, HINGE)
kd_cut = rbox("KickDoorCut", -7, 0, -0.5, 0.0, 0.0, 12.0, 0.4, M_WHITE); par(kd_cut, HINGE)
notch = box("KickNotch", -2, 2, -0.6, -0.4, 10.6, 11.4, M_DARK); par(notch, HINGE)
RIM_M, RIM_B = emit_mat("DoorRim", (0.98, 0.74, 0.27), 0.0)
rim = poly_obj("KickRim", [(-7.2, -0.6, 0), (7.2, -0.6, 0), (7.2, -0.6, 12), (-7.2, -0.6, 12), (-7.2, -0.6, 0)], 0.25, RIM_M); par(rim, HINGE)
glow(RIM_B, pulse(C["door"], 8.0, up=0.15, hold=1.8, down=0.5) + pulse(C["door2"], 8.0, up=0.1, hold=0.6, down=0.3) + [(C["when"], 0.0), (C["open"], 9.0), (DUR, 9.0)])
OPEN_T = [(C["pan"] + 0.4, C["screw"] + 1.9)]
def door_ang(t):
    a = 0.0
    for t0, t1 in OPEN_T:
        if t >= t0: a = -math.radians(95) * ease((t - t0) / 0.45)
        if t >= t1: a = -math.radians(95) * (1 - ease((t - t1) / 0.45))
    return a
bake_rot(HINGE, lambda t: (door_ang(t), 0, 0))

# ================= tub + drum (section x <= 0) =================
TUB_C = (0.0, -2.0, 46.0); TY0, TY1 = -24.0, 20.0
tub = ylathe("Tub", [(17, TY0 - 1), (27, TY0 - 1), (27, TY1), (0, TY1), (0, TY1 - 1), (26, TY1 - 1), (26, TY0), (17, TY0)], M_TUB, (TUB_C[0], 0, TUB_C[2]))
drum = ylathe("Drum", [(15, TY0 + 2), (25, TY0 + 2), (25, TY1 - 2), (0, TY1 - 2), (0, TY1 - 2.6), (24.4, TY1 - 2.6), (24.4, TY0 + 2.6), (15, TY0 + 2.6)], M_STEEL, (0, 0, TUB_C[2]))
for k in range(3):                                   # lifters
    a = math.radians(200 + 60 * k); lx, lz = 23.0 * math.cos(a), TUB_C[2] + 23.0 * math.sin(a)
    if lx <= 0: rbox(f"Lifter{k}", lx - 1.2, lx + 1.2, TY0 + 4, TY1 - 4, lz - 1.2, lz + 1.2, 0.5, M_STEEL)
# water in the drum: section slab, origin at the drum bottom, scaled in z as it drains
W_BOT = TUB_C[2] - 24.2
def drum_water(name, m_):
    bm = bmesh.new(); add_cyl(bm, 24.2, (TY1 - 2.6) - (TY0 + 2.6), "Y", (0, ((TY0 + 2.6) + (TY1 - 2.6)) / 2, 24.2), seg=48)
    cut_x(bm, -0.05)
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 13.0), plane_no=(0, 0, 1), clear_outer=True)
    oe = [e for e in bm.edges if len(e.link_faces) < 2]
    if oe:
        try: bmesh.ops.edgeloop_fill(bm, edges=oe)
        except Exception: pass
    o = mesh_obj(name, bm, m_); o.location = (0, 0, W_BOT); return o
WD = drum_water("DrumWaterDirty", M_WDIRTY); WC = drum_water("DrumWaterClean", M_WCLEAN)
windows(WD, [(0.0, C["at"])]); windows(WC, [(C["at"], C["some"] - 0.13)])
LEVEL = PW([(0, 1.0), (C["pushes"], 1.0), (C["but"] + 1.0, 0.55), (C["packs"], 0.55), (C["slows"], 0.75), (C["long"], 0.9)])
bake_scale(WD, lambda t: (1, 1, 1.0)); bake_scale(WC, lambda t: (1, 1, max(0.03, LEVEL(t))))
glow(B_WDIRTY, pulse(C["dirty"], 0.8, hold=0.8))
# clothes resting in the drum (generic fabric lumps)
CLOTHES = []
for i, (x, y, z, s) in enumerate([(-9, -12, 28, 6.5), (-14, 2, 27, 7.5), (-7, 10, 26, 6.0), (-17, -6, 32, 5.5), (-5, -2, 25, 5.0)]):
    me = sphere_mesh(f"Cloth{i}", 1.0, 3); o = obj_from(f"Cloth{i}", me, M_CLOTH[i % 4], (x, y, z))
    o.scale = (s * 1.3, s * 1.1, s * 0.55); o.rotation_euler = (random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(0, 3)); CLOTHES.append(o)
    d = o.modifiers.new("Wrinkle", "DISPLACE"); tx = bpy.data.textures.new(f"ClothTex{i}", "CLOUDS"); tx.noise_scale = 0.6; d.texture = tx; d.strength = 0.25

# ================= pump assembly (axis along y at x = PX, z = PZ; section x <= PX) =================
H_Y0, H_Y1 = -31.0, -12.0                    # filter housing
housing = ylathe("FilterHousing", [(4.0, 0), (4.7, 0), (4.7, H_Y1 - H_Y0), (4.0, H_Y1 - H_Y0)], M_HOUSE, (PX, H_Y0, PZ))
chamber = ylathe("ImpellerChamber", [(4.0, 0), (5.8, 0), (5.8, 8), (0, 8), (0, 7.4), (5.2, 7.4), (5.2, 0.6), (4.0, 0.6)], M_HOUSE, (PX, H_Y1, PZ))
motor = ylathe("Motor", [(0, 0), (4.8, 0), (4.8, 10), (0, 10)], M_DARK, (PX - 0.6, H_Y1 + 8, PZ), half=True)
coil = torus("MotorCoil", 3.6, 0.9, M_MOTOR, (PX, H_Y1 + 13, PZ)); coil.rotation_euler = (math.pi / 2, 0, 0)
glow(B_MOTOR, [(0, 0.0), (C["electric"], 0.0), (C["pump"], 6.0), (C["pushes"], 2.5), (C["before"], 2.5), (C["before"] + 0.3, 0.0)])
# water inside the housing (hot water that waits behind the door)
HW = mesh_obj("HousingWater", (lambda bm: (add_cyl(bm, 3.95, H_Y1 - H_Y0 - 0.5, "Y", (PX, (H_Y0 + H_Y1) / 2, PZ), seg=32), cut_x(bm, PX - 0.05), bm)[2])(bmesh.new()), M_WHOT)
windows(HW, [(C["hides"], C["some"] - 0.13), (C["water4"], C["many"])])
glow(B_WHOT, [(0, 0.0), (C["hot"] - 0.01, 0.0), (C["hot"] + 0.3, 2.5), (C["burn"] + 0.2, 4.5), (C["many"], 4.5)])
# impeller: hub + 6 curved blades, spins about y
IMP = empty("Impeller", (PX, H_Y1 + 4.0, PZ))
bm = bmesh.new(); add_cyl(bm, 1.2, 3.0, "Y", (0, 0, 0), seg=24)
for k in range(6):
    a = 2 * math.pi * k / 6
    add_bar(bm, (1.0 * math.cos(a), 0, 1.0 * math.sin(a)), (4.4 * math.cos(a + 0.35), 0, 4.4 * math.sin(a + 0.35)), 0.7)
imp = mesh_obj("ImpellerBlades", bm, M_IMP); par(imp, IMP)
def omega(t):
    if t < C["switches"]: return 0.0
    if t < C["before"]: return 40.0 * ease((t - C["switches"]) / 0.8) * (0.55 if C["packs"] < t else 1.0)
    if C["check"] - 0.2 < t < C["screw"]: return 9.0
    return 0.0
_ang = [0.0]
for i in range(1, len(TS)): _ang.append(_ang[-1] + omega(TS[i]) / FPS)
bake(IMP, "rotation_euler", 1, _ang)
glow(B_IMP, pulse(C["spinning"], 1.2, hold=0.6) + pulse(C["impeller3"], 1.5, hold=1.2))
glow(B_HOUSE, pulse(C["chew"], 1.6, hold=0.8) + pulse(C["trickle"], 1.4, hold=1.2))
# hoses: sump (tub -> housing top), drain (chamber top -> back -> over -> standpipe), all half-cut at PX
SUMP_PTS = [(1.5, -4.0, 19.6), (4.0, -6.0, 17.5), (10.0, -12.0, 16.0), (PX, -18.0, 15.5), (PX, -20.0, 13.4)]
sump, SUMP_S = sec_pipe("SumpHose", SUMP_PTS, 1.9, M_HOSE)
DRAIN_PTS = [(PX, H_Y1 + 3.0, PZ + 5.6), (PX, H_Y1 + 3.0, 18.0), (PX, 0.0, 19.0), (PX, 24.0, 20.0), (PX, 26.5, 30.0), (PX, 26.5, 80.0),
             (PX, 31.0, 92.0), (PX, 40.0, 95.0), (PX, 44.0, 91.0), (PX, 44.0, 84.0)]
drainh, DRAIN_S = sec_pipe("DrainHose", DRAIN_PTS, 1.6, M_HOSE)
stand, _ = sec_pipe("Standpipe", [(PX, 44.0, 30.0), (PX, 44.0, 88.0)], 2.8, M_CHROME, smooth_it=0)
stand_bot, _ = sec_pipe("StandpipeLow", [(PX, 44.0, 30.0), (PX, 44.0, 24.0), (PX, 49.0, 20.0)], 2.8, M_CHROME)
# ---------- strainer cartridge (full, not cut) on CART: origin at its front face (in place: y = -30.5) ----------
CART = empty("Cartridge", (PX, -30.5, PZ))
cap = ylathe("CartCap", [(0, -2.0), (5.2, -2.0), (5.2, 0.0), (0, 0.0)], M_CART, (0, 0, 0), half=False); par(cap, CART)
grip = box("CartGrip", -0.6, 0.6, -2.9, -1.9, -4.2, 4.2, M_CART); par(grip, CART)
bm = bmesh.new()
for k in range(12):                          # slotted cage: 12 ribs + 4 rings
    a = 2 * math.pi * k / 12; add_bar(bm, (3.6 * math.cos(a), 0.2, 3.6 * math.sin(a)), (3.6 * math.cos(a), 16.0, 3.6 * math.sin(a)), 0.45)
cage = mesh_obj("CartCage", bm, M_CART); par(cage, CART)
for k, yy in enumerate([0.5, 5.5, 10.5, 15.7]):
    rg = torus(f"CartRing{k}", 3.6, 0.35, M_CART, (0, yy, 0)); rg.rotation_euler = (math.pi / 2, 0, 0); par(rg, CART)
endc = cyl("CartEnd", 3.8, 0.6, "Y", (0, 16.2, 0), M_CART); par(endc, CART)
glow(B_CART, pulse(C["trap"], 0.9, hold=1.0) + pulse(C["strainer"], 0.9, hold=1.2) + pulse(C["slots"], 0.7, hold=0.5))
T_CCW0, T_CCW1 = C["twist"] + 0.2, C["pull"] - 0.2
T_PULL0, T_PULL1 = C["pull"], C["pull"] + 0.7
T_LIFT0, T_LIFT1 = C["rinse2"] - 0.1, C["rinse2"] + 0.25
T_R = C["rinse2"] + 0.35                      # rinse hits, junk falls (rigid body starts)
T_BACK0, T_BACK1 = C["screw"], C["screw"] + 0.7
T_CW0, T_CW1 = C["tight2"] - 0.25, C["tight2"] + 0.4
CART_IN = Vector((PX, -30.5, PZ)); CART_OUT = Vector((PX, -52.5, PZ)); CART_UP = Vector((PX, -52.0, 24.0))
def cart_loc(t):
    if t < T_PULL0: return CART_IN
    if t < T_LIFT0: return CART_IN.lerp(CART_OUT, ease((t - T_PULL0) / (T_PULL1 - T_PULL0)))
    if t < T_BACK0: return CART_OUT.lerp(CART_UP, ease((t - T_LIFT0) / (T_LIFT1 - T_LIFT0)))
    return CART_UP.lerp(CART_IN, ease((t - T_BACK0) / (T_BACK1 - T_BACK0)))
ANG_OPEN = -math.radians(150)                 # counterclockwise seen from the front (viewer looks along +y)
def cart_rot(t):
    if t < T_CCW0: return 0.0
    if t < T_CW0: return ANG_OPEN * ease((t - T_CCW0) / (T_CCW1 - T_CCW0))
    return ANG_OPEN * (1 - ease((t - T_CW0) / (T_CW1 - T_CW0)))
bake_loc(CART, lambda t: tuple(cart_loc(t))); bake_rot(CART, lambda t: (0, cart_rot(t), 0))
def cart_world(t, local):
    return cart_loc(t) + Matrix.Rotation(cart_rot(t), 3, "Y") @ Vector(local)

# ================= junk: travellers (ride the water path) + resters (sit in the cartridge) =================
JPATH = Path(chaikin([Vector(p) for p in [(-8.0, -6.0, 24.0), (-2.0, -4.5, 21.0)] + SUMP_PTS + [(PX, -22.0, PZ + 1.0)]], 2))
def coin_me(name, r): bm = bmesh.new(); add_cyl(bm, r, 0.22, "Z", (0, 0, 0), seg=28); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me
def button_me(name):
    bm = bmesh.new(); add_cyl(bm, 0.75, 0.25, "Z", (0, 0, 0), seg=24)
    for dx, dy in ((0.2, 0.2), (-0.2, 0.2), (0.2, -0.2), (-0.2, -0.2)): add_cyl(bm, 0.08, 0.3, "Z", (dx, dy, 0.02), seg=8)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me
def plastic_me(name):
    bm = bmesh.new(); add_box(bm, -0.9, 0.9, -0.35, 0.35, -0.12, 0.12)
    for v in bm.verts: v.co.x += random.uniform(-0.2, 0.2); v.co.y += random.uniform(-0.15, 0.15)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); return me
def lint_me(name, r):
    me = sphere_mesh(name, r, 3); return me
# (kind, cue, local rest pos in the cartridge (x, y, z), mesh, material)
JUNK = [("coin", "coins", (-1.0, 4.0, -2.4), coin_me("CoinA", 1.2), M_COIN_G), ("coin", "coins", (1.2, 8.0, -2.3), coin_me("CoinB", 1.05), M_COIN_S),
        ("coin", "coins", (0.0, 12.0, -2.5), coin_me("CoinC", 0.95), M_COIN_S),
        ("button", "buttons", (-1.8, 6.0, -1.8), button_me("BtnA"), M_JUNK[0][0]), ("button", "buttons", (1.9, 11.0, -1.6), button_me("BtnB"), M_JUNK[1][0]),
        ("plastic", "plastic", (0.6, 2.5, -2.0), plastic_me("PlasA"), M_JUNK[2][0]), ("plastic", "plastic", (-1.2, 13.5, -1.9), plastic_me("PlasB"), M_JUNK[3][0]),
        ("lint", "lint", (0.0, 7.0, 0.8), lint_me("LintA", 1.4), M_LINT), ("lint", "lint", (-0.8, 10.5, 0.9), lint_me("LintB", 1.2), M_LINT),
        ("lint", "lint", (0.9, 3.5, 1.0), lint_me("LintC", 1.1), M_LINT)]
TRAVEL = 2.6
RESTERS, RIGIDS, EV_ARRIVE = [], [], []
for i, (kind, cue, rest, me, m_) in enumerate(JUNK):
    t0 = C[cue] + 0.12 * (i % 3); t1 = t0 + TRAVEL; EV_ARRIVE.append(t1)
    tr = obj_from(f"Trav_{i}", me, m_)
    if not me.materials: me.materials.append(m_)
    end_w = cart_world(t1, rest)
    def tfn(t, t0=t0, t1=t1, end_w=end_w):
        u = lin((t - t0) / (t1 - t0)); s = ease(u) * JPATH.L
        p = JPATH.at(s) if u < 0.97 else JPATH.at(JPATH.L).lerp(end_w, (u - 0.97) / 0.03)
        return tuple(p + Vector((0.0, 0.0, 0.35 * math.sin(7 * t + i))))
    bake_loc(tr, tfn); bake_rot(tr, lambda t, i=i: (1.3 * t + i, 0.9 * t, 0.4 * i))
    windows(tr, [(t0, t1)]); bake_scale(tr, lambda t, t0=t0, t1=t1: (pop(t, t0, 0.3) * (1.0 + 0.5 * (1 - ease((t - t1 + 0.4) / 0.4))),) * 3)
    rs = obj_from(f"Rest_{i}", me, m_); par(rs, CART); rs.location = rest; rs.rotation_euler = (random.uniform(-0.6, 0.6), random.uniform(0, 3), random.uniform(-0.6, 0.6))
    if kind in ("coin", "button", "plastic"): rs.rotation_euler = (math.pi / 2 + random.uniform(-0.3, 0.3), random.uniform(0, 3), 0)
    windows(rs, [(0.0, C["ignore"]), (t1, T_R)]); RESTERS.append(rs)
    rb = obj_from(f"Rigid_{i}", me.copy(), m_); rb.location = tuple(cart_world(T_R, rest)); rb.rotation_euler = rs.rotation_euler
    windows_r(rb, [(T_R, C["screw"] + 0.1)]); RIGIDS.append(rb)
# junk flashes red on "doesn't"
for m_ in [M_JUNK[k][1] for k in range(4)]: glow(m_, pulse(C["doesnt"], 2.0, hold=0.6))
glow(B_LINT, pulse(C["lint2"], 3.0, hold=0.8) + pulse(C["out"], 1.5, hold=0.6))
# what-if ghost coin into the impeller (red)
GC = obj_from("GhostCoin", coin_me("GhostCoinMe", 1.1), M_RED)
gc_path = Path([Vector((PX, -22.0, PZ + 1.0)), Vector((PX, -15.0, PZ)), Vector((PX, H_Y1 + 3.0, PZ + 1.5))])
bake_loc(GC, lambda t: tuple(gc_path.at(ease((t - C["chew"] + 0.4) / 0.6) * gc_path.L)))
bake_rot(GC, lambda t: (math.pi / 2, 6 * t, 0)); windows(GC, [(C["chew"] - 0.4, C["so"])])
SPK = cyl("SparkEmitter", 1.0, 0.5, "Y", (PX - 0.5, H_Y1 + 3.0, PZ + 2.0), M_RED, seg=12); SPK.hide_render = True
pm = fx.particles(SPK, "sparks", F(C["impeller2"] - 0.05), F(C["impeller2"] + 0.4), count=140)
try: ps_ = pm.particle_system.settings; ps_.particle_size = 0.12; ps_.normal_factor = 120; ps_.lifetime = 12
except Exception as e: print("[fx] sparks tune skipped:", e)
# lint mat packing the cartridge ("over months it packs tight")
LM = obj_from("LintMat", sphere_mesh("LintMatMe", 1.0, 4), M_LINT); par(LM, CART); LM.location = (0, 8.0, 0)
d = LM.modifiers.new("Fluff", "DISPLACE"); tx = bpy.data.textures.new("LintTex", "CLOUDS"); tx.noise_scale = 0.5; d.texture = tx; d.strength = 0.5
GROW = PW([(0, 0.0), (C["over"], 0.0), (C["tight"] + 0.2, 1.0), (T_R, 1.0), (T_R + 0.8, 0.0)])
bake_scale(LM, lambda t: ((3.1 * max(0.001, GROW(t)), 7.6 * max(0.001, GROW(t)), 3.1 * max(0.001, GROW(t))) if t >= C["ignore"] else (3.1, 7.6, 3.1)))
windows(LM, [(0.0, C["ignore"]), (C["over"], T_R + 0.8)])
FIB_M, _ = mat("LintFiber", (0.45, 0.42, 0.4), rough=1.0)
fiber = cyl("LintFiber", 0.04, 0.9, "X", (0, 0, -500), FIB_M, seg=6)
fx.scatter(LM, fiber, density=2.5, scale_min=0.5, scale_max=1.5, seed=3)

# ================= water beads along the drain route (slow to a trickle as the lint packs) =================
WPATH = Path(chaikin([Vector(p) for p in [(-8.0, -6.0, 23.5), (-2.0, -4.5, 21.0)] + SUMP_PTS +
                      [(PX, -22.0, PZ + 2.0), (PX, -18.0, PZ), (PX, H_Y1 + 3.0, PZ)] + DRAIN_PTS + [(PX, 44.0, 70.0)]], 2))
def vel(t):
    if t < C["on"] or t > C["drain3"] + 1.6: return 0.0
    v = 46.0 * ease((t - C["on"]) / 0.8)
    return v * (1.0 - 0.85 * ease((t - C["slows"]) / 1.2))
S_ACC = [0.0]
for i in range(1, len(TS)): S_ACC.append(S_ACC[-1] + vel(TS[i]) / FPS)
NB = 46
bme = sphere_mesh("BeadMe", 0.55, 2); bme.materials.append(M_BEAD)
B_WIN = [(C["on"], C["drain3"] + 1.6)]
for i in range(NB):
    o = obj_from(f"Bead{i}", bme)
    vals = [tuple(WPATH.at((s + i * WPATH.L / NB) % WPATH.L)) for s in S_ACC]
    for ax in range(3): bake(o, "location", ax, [v[ax] for v in vals])
    # trickle: only every 4th bead keeps running once the flow slows
    w = B_WIN if i % 4 == 0 else [(C["on"], C["trickle"] + 0.3)]
    windows(o, w)

# ================= cleaning props: towel, pan, emergency hose, rinse stream, leak drops =================
TOWEL = rbox("Towel", 0, 42, -64, -34, 0.0, 0.9, 0.3, M_TOWEL)
bake_loc(TOWEL, lambda t: (0, -60 * (1 - ease((t - C["lay"]) / 0.6)), 0) if t < C["lay"] + 0.6 else (0, 0, 0))
bm = bmesh.new(); add_box(bm, 6, 32, -56, -36, 0.9, 1.3)
for (x0, x1, y0, y1) in [(6, 6.5, -56, -36), (31.5, 32, -56, -36), (6, 32, -56, -55.5), (6, 32, -36.5, -36)]: add_box(bm, x0, x1, y0, y1, 0.9, 3.6)
PAN = mesh_obj("Pan", bm, M_PAN)
PAN_DROP = lambda t: (0, 0, drop(t, C["pan"] - 0.25, h=30.0, d=0.4))
bake_loc(PAN, PAN_DROP); windows(PAN, [(C["lay"], C["lg"])]); windows(TOWEL, [(C["lay"], C["lg"])])
PANW_M, PANW_B, _ = water_sec("PanWater", dens=0.05)
PANW = box("PanWater", 6.6, 31.4, -55.4, -36.6, 1.3, 2.9, PANW_M)
bake_scale(PANW, lambda t: (1, 1, max(0.02, ease((t - C["drain5"]) / 1.4))))
PANW.location = (0, 0, 0); windows(PANW, [(C["drain5"], C["lg"])])
# emergency drain hose: pops out of the door opening and bends into the pan
EH_PTS = chaikin([Vector(p) for p in [(13.5, -31.0, 5.0), (13.5, -35.0, 5.0), (13.5, -39.0, 4.0), (14.0, -42.0, 3.6)]], 2)
EH = mesh_obj("EmergencyHose", sweep_bm(EH_PTS, [0.7] * len(EH_PTS), 14), M_BLACKHOSE)
bake_scale(EH, lambda t: (1, pop(t, C["hose2"] - 0.1, 0.3), 1)); EH.location = (0, 0, 0)
windows(EH, [(C["hose2"] - 0.1, C["twist"])])
# the scale is about the world origin in y: move the origin to the hose root
EH.data.transform(Matrix.Translation((0, 31.0, 0))); EH.location = (0, -31.0, 0)
EHT = cyl("HoseTip", 0.5, 0.2, "Z", (14.0, -42.0, 3.0), M_BLACKHOSE, seg=10); EHT.hide_render = True
pm2 = fx.particles(EHT, "rain", F(C["drain5"]), F(C["twist"] - 0.1), count=420)
try: ps_ = pm2.particle_system.settings; ps_.particle_size = 0.16; ps_.normal_factor = -30; ps_.lifetime = 10
except Exception as e: print("[fx] drain stream tune skipped:", e)
# Mantaflow: the short stream into the pan (<= 3 s, res 64; baked on the laptop with --bake-fluid)
FL_DOM = box("FluidDomain", 5.0, 33.0, -57.0, -35.0, 1.0, 9.0, None); FL_DOM.display_type = "WIRE"
FL_IN = cyl("FluidInflow", 0.6, 0.6, "Z", (14.0, -42.0, 4.5), None, seg=10); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
fx.fluid_domain(FL_DOM, FL_IN, eff=[PAN], res=64, start=F(C["drain5"]), end=F(C["drain5"] + 2.8), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_M, _, _ = water_sec("FluidWater")
FL_DOM.data.materials.append(FL_M)
windows(FL_DOM, [(C["drain5"], C["twist"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True
# solid streams (read better than particles at phone size): emergency hose -> pan, tap -> cartridge
M_STREAM, B_STREAM = emit_mat("Stream", (0.45, 0.85, 1.0), 1.2)
st_pts = [Vector((14.0, -42.0, 3.4)), Vector((14.2, -43.0, 2.4)), Vector((14.4, -44.0, 1.4))]
STREAM1 = mesh_obj("HoseStream", sweep_bm(st_pts, [0.45, 0.4, 0.5], 12), M_STREAM); windows(STREAM1, [(C["drain5"], C["twist"] - 0.1)])
STREAM2 = mesh_obj("RinseStream", sweep_bm([Vector((PX, -44.0, 46.0)), Vector((PX, -44.0, 28.6))], [0.9, 1.1], 16), M_STREAM)
windows(STREAM2, [(C["rinse2"], C["check"] - 0.1)])
TAP = cyl("Tap", 1.6, 4.0, "Z", (PX, -44.0, 48.0), M_CHROME, seg=24); windows(TAP, [(C["rinse2"] - 0.3, C["check"])])
# rinse stream from above (warm water) onto the pulled cartridge
RIN = box("RinseEmitter", PX - 2.5, PX + 2.5, -48.0, -40.0, 46.0, 46.2, None); RIN.hide_render = True
pm3 = fx.particles(RIN, "rain", F(C["rinse2"]), F(C["check"] - 0.1), count=900)
try: ps_ = pm3.particle_system.settings; ps_.particle_size = 0.14; ps_.normal_factor = -60; ps_.lifetime = 10
except Exception as e: print("[fx] rinse tune skipped:", e)
# steam from the hot housing water ("after a hot cycle it can burn")
STM = box("SteamEmitter", PX - 3, PX - 0.5, -30, -14, PZ + 3.5, PZ + 3.8, None); STM.hide_render = True
pm4 = fx.particles(STM, "dust", F(C["hot"]), F(C["many"]), count=220)
try:
    ps_ = pm4.particle_system.settings; ps_.particle_size = 0.25; ps_.normal_factor = 8; ps_.lifetime = 25; ps_.effector_weights.gravity = -0.004
    ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (1.0, 0.6, 0.4, 1)
except Exception as e: print("[fx] steam tune skipped:", e)
# leak drops if it is not screwed tight (red what-if)
DROPS = []
for k in range(4):
    o = obj_from(f"LeakDrop{k}", sphere_mesh(f"LeakDropMe{k}", 0.45, 2), M_RED)
    t0 = C["leak"] + 0.18 * k
    bake_loc(o, lambda t, t0=t0, k=k: (PX - 3 + k, -33.2, max(1.0, 5.0 - 0.5 * 981 * max(0.0, t - t0) ** 2)))
    windows(o, [(t0, t0 + 0.32)]); DROPS.append(o)
# rigid body: junk knocked off the cartridge by the rinse falls into the pan
PAN_COLL = box("PanCollider", 6, 32, -56, -36, 0.0, 1.3, None); PAN_COLL.hide_render = True; PAN_COLL.display_type = "WIRE"
fx.rigid(RIGIDS, passive=[PAN_COLL], mass=0.01, friction=0.5, bounce=0.25)

# ================= calendar set (frequency) =================
CAL = []
for k in range(12):
    r_, c_ = divmod(k, 4); x = X_CAL - 33 + c_ * 22; z = 92 - r_ * 26
    m_, b_ = mat(f"Tile{k}", (0.12, 0.13, 0.15), rough=0.4, emit_rgb=(0.98, 0.74, 0.27))
    o = rbox(f"CalTile{k}", x - 9.5, x + 9.5, -1.0, 1.0, z - 11, z + 11, 1.2, m_); CAL.append((o, b_))
    ring_ = rbox(f"CalHead{k}", x - 9.5, x + 9.5, -1.4, -0.9, z + 7, z + 11, 0.4, M_DARK)
cal_back = box("CalBack", X_CAL - 60, X_CAL + 60, 3, 4, 0, 160, WALL_M)
T_MONTH = C["every"]; T_SIX = C["five"]
for k, (o, b_) in enumerate(CAL):
    keys = [(0, 0.0), (T_MONTH + 0.06 * k - 0.01, 0.0), (T_MONTH + 0.06 * k + 0.12, 4.0), (C["samsung"] - 0.05, 4.0), (C["samsung"] + 0.15, 0.0)]
    if k % 2 == 0: keys += [(T_SIX + 0.12 * k - 0.01, 0.0), (T_SIX + 0.12 * k + 0.12, 4.0), (DUR, 4.0)]
    glow(b_, keys)
    b_.inputs["Emission Color"].default_value = (0.98, 0.74, 0.27, 1)
    nt_ = o.data.materials[0].node_tree
    col = b_.inputs["Emission Color"]
    col.default_value = (0.98, 0.74, 0.27, 1); col.keyframe_insert("default_value", frame=1)
    col.default_value = (0.98, 0.74, 0.27, 1); col.keyframe_insert("default_value", frame=F(C["samsung"]))
    col.default_value = (0.30, 0.92, 1.0, 1); col.keyframe_insert("default_value", frame=F(C["samsung"]) + 1)

# ================= visibility of the exterior-only pieces / section faces =================
EXT_WINS, t_prev = [], 0.0
for a, b in CUT: EXT_WINS.append((t_prev, a)); t_prev = b
EXT_WINS.append((t_prev, DUR))
for o in EXTERIOR_ONLY + [kd_full, FEET[1], FEET[3]]: windows(o, EXT_WINS)
for o in SEC_FACES: windows(o, CUT)
windows(kd_cut, []); windows(rim, EXT_WINS)
windows(notch, EXT_WINS)
# the cartridge, hoses and pump only matter in the cutaway + cleaning shots; keep them (hidden inside the cabinet otherwise)

# ================= lights + world =================
fx.hdri("interior", strength=0.35, rotation_deg=30.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, rot, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("Key", (140, -120, 160), (math.radians(50), 0, math.radians(50)), 120, 1.4e5, (1.0, 0.95, 0.88))
area("Rim", (-60, 120, 150), (math.radians(-50), 0, math.radians(200)), 80, 7.0e4, (0.6, 0.8, 1.0))
area("Low", (90, -90, 20), (math.radians(80), 0, math.radians(45)), 60, 2.5e4, (1.0, 0.9, 0.8))
area("CalKey", (X_CAL + 40, -160, 140), (math.radians(55), 0, math.radians(15)), 100, 1.2e5)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.5; cam_d.clip_end = 6000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (95, -175, 70), (5, -10, 42), 35),
    (C["bottom"] + 0.4, (60, -120, 30), (15, -32, 14), 40),
    (C["hides"] - 0.05, (56, -112, 27), (16, -32, 12), 40),
    (C["hides"], (62, -70, 22), (PX, -22, PZ), 45, "cut"),
    (C["ignore"] - 0.05, (55, -62, 18), (PX, -22, PZ), 45),
    (C["ignore"], (140, -48, 58), (6, 0, 44), 32, "cut"),
    (C["electric"] - 0.05, (125, -40, 54), (6, 0, 42), 32),
    (C["electric"], (52, -30, 20), (PX, -6, PZ), 50, "cut"),
    (C["pushes"] - 0.05, (48, -26, 18), (PX, -6, PZ), 50),
    (C["pushes"], (125, -40, 36), (8, -6, 28), 32, "cut"),
    (C["drum"], (125, -36, 40), (8, -6, 30), 32),
    (C["hose"], (128, -10, 58), (PX, 18, 55), 32),
    (C["pipe"], (120, 10, 78), (PX, 34, 80), 34),
    (C["but"] - 0.05, (118, 8, 78), (PX, 34, 80), 34),
    (C["but"], (110, -60, 40), (4, -8, 22), 40, "cut"),
    (C["junk"], (70, -55, 20), (PX, -18, 12), 45),
    (C["chew"] - 0.05, (68, -54, 19), (PX, -18, 12), 45),
    (C["chew"], (42, -26, 14), (PX, -10, PZ), 55, "cut"),
    (C["so"] - 0.05, (41, -25, 14), (PX, -10, PZ), 55),
    (C["so"], (55, -52, 16), (PX, -21, PZ), 50, "cut"),
    (C["doesnt"], (48, -46, 14), (PX, -21, PZ), 50),
    (C["drain3"] - 0.05, (45, -43, 13), (PX, -21, PZ), 50),
    (C["drain3"], (135, -45, 56), (6, 0, 44), 32, "cut"),
    (C["some"] - 0.18, (128, -42, 55), (6, 0, 44), 32),
    (C["some"] - 0.13, (40, -150, 70), (0, -30, 62), 38, "cut"),
    (C["error"], (25, -120, 76), (0, -32, 74), 45),
    (C["before"] - 0.05, (22, -112, 76), (0, -32, 75), 45),
    (C["before"], (75, -130, 32), (18, -45, 5), 38, "cut"),
    (C["water4"] - 0.05, (70, -122, 30), (18, -45, 5), 38),
    (C["water4"], (58, -62, 16), (PX, -22, PZ), 45, "cut"),
    (C["many"] - 0.05, (54, -58, 15), (PX, -22, PZ), 45),
    (C["many"], (55, -105, 22), (16, -42, 4), 42, "cut"),
    (C["twist"] - 0.05, (52, -100, 21), (16, -42, 4), 42),
    (C["twist"], (34, -78, 14), (PX, -34, PZ), 50, "cut"),
    (C["pull"], (38, -84, 16), (PX, -38, PZ), 48),
    (C["rinse2"], (60, -110, 32), (PX, -46, 14), 40),
    (C["check"] - 0.05, (62, -112, 33), (PX, -46, 14), 40),
    (C["check"], (40, -40, 12), (PX, -10, PZ), 55, "cut"),
    (C["screw"] - 0.05, (38, -38, 12), (PX, -10, PZ), 55),
    (C["screw"], (52, -100, 22), (PX, -38, 8), 45, "cut"),
    (C["lg"] - 0.05, (48, -94, 20), (PX, -38, 8), 45),
    (C["lg"], (X_CAL + 15, -190, 66), (X_CAL, 0, 66), 35, "cut"),
    (C["when"] - 0.05, (X_CAL + 5, -175, 66), (X_CAL, 0, 66), 35),
    (C["when"], (80, -160, 55), (8, -20, 30), 35, "cut"),
    (DUR, (55, -115, 30), (16, -32, 12), 40),
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
bake_scalar(cam_d, "dof.aperture_fstop", [max(2.8, min(16.0, 0.05 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0e2, min(3.0e4, 0.4 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
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
fx.bake_rigid(F(T_R), F(T_R) + 75)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "kickdoor": (19.0, -33.0, 9.0), "cart": (PX, -22.0, PZ + 3.8), "imp": (PX, H_Y1 + 4.0, PZ + 4.5), "motor": (PX, H_Y1 + 13.0, PZ + 4.8),
    "sump": (10.0, -12.0, 17.5), "hose": (PX, 26.5, 55.0), "stand": (PX, 44.0, 86.0), "drum": (-8.0, -2.0, 40.0), "led": (3.5, -33.0, 79.5),
    "pan": (28.0, -46.0, 3.6), "ehose": (13.5, -38.0, 4.5), "towel": (36.0, -58.0, 1.0), "lintmat": (PX, -22.5, PZ + 3.2),
    "cart_out": (PX, -44.0, 24.0 + 3.8), "cart_pulled": (PX, -45.0, PZ + 4.0), "cap": (PX, -32.5, PZ + 5.2), "hw": (PX, -22.0, PZ),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "stake": RR(*T_STAKE), "pump": RR(*T_PUMP), "junk": RR(*T_JUNK), "strain": RR(*T_STRAIN), "err": RR(*T_ERR),
          "clean": RR(*T_CLEAN), "cal": RR(*T_CAL), "cta": RR(*T_CTA), "cut": [RR(a, b) for a, b in CUT],
          "door_open": round(OPEN_T[0][0], 3), "door_close": round(OPEN_T[0][1], 3), "pump_on": round(C["switches"], 3), "pump_off": round(C["before"], 3),
          "arrive": [round(x, 3) for x in EV_ARRIVE], "sparks": round(C["impeller2"], 3), "towel": round(C["lay"], 3), "pan_land": round(C["pan"] + 0.15, 3),
          "hose_pop": round(C["hose2"], 3), "stream": RR(C["drain5"], C["twist"] - 0.1), "ccw": RR(T_CCW0, T_CCW1), "pull": RR(T_PULL0, T_PULL1),
          "rinse": RR(C["rinse2"], C["check"] - 0.1), "junk_fall": round(T_R, 3), "back": RR(T_BACK0, T_BACK1), "cw": RR(T_CW0, T_CW1),
          "leak": round(C["leak"], 3), "led": round(C["error"], 3)}
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
