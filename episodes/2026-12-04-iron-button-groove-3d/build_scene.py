# Iron button groove (3d-40): "That little notch at the tip of your iron is a parking spot for buttons."
# Stake: run a hot plate straight over a plastic button and it can melt, crack or scorch. The notch = a shallow groove along the
# front edge, between the hot plate and the body; slide the tip in beside a button, the button slips into the gap, stays out of the
# heat while the plate presses the fabric right up to its edge. Inside (most irons): heating element cast into the aluminum plate,
# bimetal strip thermostat bends -> clicks power off, cools -> back on. Water tank above, a valve drips water into a chamber inside the
# hot plate, each drop flashes into steam and blasts out through the holes. Too cold -> water can't boil and leaks out (many irons keep
# the valve shut until the plate is hot enough). Hard water -> limescale clogs the holes. Many irons switch off face down (~30 s).
# Illustrative, 1 unit = 1 cm. Sets: ironing board (x ~0, board top z 0), studio cutaway iron at x = 600 (section y = 0; front housing
# slides off; the soleplate in front of the section is cut level with the heating element). Generic iron, no brand, no text, no people.
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
random.seed(40)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("that","That"),("notch","notch"),("tip","tip"),("parking","parking"),("buttons","buttons."),("run","Run"),("hot","hot"),
  ("plate","plate"),("over","over"),("plastic","plastic"),("button","button,"),("melt","melt,"),("crack","crack,"),("scorch","scorch."),
  ("heres","Here's"),("notch2","notch"),("works","works."),("its","It's"),("shallow","shallow"),("groove","groove"),("front","front"),
  ("edge","edge,"),("between","between"),("hot2","hot"),("plate2","plate"),("body","body"),("slide","Slide"),("tip2","tip"),
  ("beside","beside"),("button2","button,"),("button3","button"),("slips","slips"),("gap","gap."),("it","It"),("sits","sits"),
  ("heat","heat,"),("while","while"),("presses","presses"),("fabric","fabric"),("edge2","edge."),("now","Now"),("cut","cut"),
  ("open","open."),("in","In"),("heating","heating"),("element","element"),("cast","cast"),("aluminum","aluminum"),("on","On"),
  ("top","top"),("strip","strip"),("two","two"),("metals","metals."),("as","As"),("heats","heats"),("bends","bends,"),("clicks","clicks"),
  ("off","off,"),("then","then"),("cools","cools"),("clicks2","clicks"),("back","back"),("on2","on."),("above","Above"),("water","water"),
  ("tank","tank."),("valve","valve"),("drip","drip"),("chamber","chamber"),("plate3","plate."),("each","Each"),("drop","drop"),
  ("flashes","flashes"),("steam","steam"),("blasts","blasts"),("holes","holes"),("bottom","bottom."),("if","If"),("plate4","plate"),
  ("cold","cold,"),("boil","boil,"),("leaks","leaks"),("instead","instead."),("thats","That's"),("many","many"),("valve2","valve"),
  ("shut","shut"),("hot3","hot"),("enough","enough."),("hard","Hard"),("limescale","limescale"),("clogs","clogs"),("holes2","holes."),
  ("and","And"),("switch","switch"),("off2","off"),("face","face"),("thirty","thirty"),("seconds","seconds."),("have","Have"),
  ("used","used"),("notch3","notch"),("iron","iron?"),("tell","Tell"),("comments","comments.")]
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
CL = coll("Iron")
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
X0 = 600.0                                    # studio cutaway set
IZ = 3.2                                      # cutaway iron floats this high over the fabric swatch
GOLD, CYAN, RED, ORANGE, GREEN = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.15), (0.25, 1.0, 0.35)
SET_A = [(0.0, C["cut"]), (C["and"], DUR)]
SET_C = [(C["cut"], C["and"])]
# valve / water windows in the cutaway
OPEN_W = [(C["valve"], C["thats"]), (C["enough"], DUR)]                  # needle lifted
DRIP_W = [(C["drip"] - 0.1, C["if"]), (C["enough"] + 0.15, C["and"])]    # drops fall into the hot chamber and flash
LEAK_W = [(C["cold"], C["thats"] + 0.3)]                                  # cold plate: drops fall straight through the holes
STEAM1 = (C["flashes"], C["if"])
STEAM2 = (C["enough"] + 0.3, C["hard"])

# ---------- materials ----------
M_SEC, B_SEC = mat("CutFace", (0.90, 0.38, 0.06), rough=0.5, emit_rgb=(1.0, 0.40, 0.08)); B_SEC.inputs["Emission Strength"].default_value = 0.10
def glowc(bsdf, keys):
    s_in, c_in = bsdf.inputs["Emission Strength"], bsdf.inputs["Emission Color"]
    for t, s, rgb in keys:
        s_in.default_value = s; s_in.keyframe_insert("default_value", frame=F(t))
        c_in.default_value = (*rgb, 1); c_in.keyframe_insert("default_value", frame=F(t))
M_SOLE, B_SOLE = mat("Soleplate", (0.62, 0.63, 0.66), rough=0.32, metallic=1.0, emit_rgb=CYAN)
M_SOLEA, B_SOLEA = mat("SoleplateA", (0.80, 0.81, 0.83), rough=0.18, metallic=1.0, emit_rgb=ORANGE)
M_SKIRT, _ = mat("Skirt", (0.10, 0.11, 0.13), rough=0.35)
M_BODY, _ = mat("Body", (0.93, 0.94, 0.95), rough=0.3)
M_ACCENT, _ = mat("Accent", (0.05, 0.42, 0.55), rough=0.3)
M_HANDLE, _ = mat("Handle", (0.08, 0.09, 0.10), rough=0.45)
M_GROOVE, B_GROOVE = emit_mat("GrooveGlow", GOLD, 0.0)
M_LED, B_LED = emit_mat("PowerLED", (1.0, 0.55, 0.15), 0.0)
HEAT = (1.0, 0.32, 0.08)
M_ELEM, B_ELEM = mat("Element", (0.25, 0.22, 0.20), rough=0.4, metallic=0.8, emit_rgb=HEAT)
M_HOLE, _ = mat("Hole", (0.01, 0.01, 0.012), rough=0.6)
M_CERAM, _ = mat("Ceramic", (0.92, 0.90, 0.85), rough=0.5)
M_STEEL, _ = mat("Steel", (0.70, 0.71, 0.73), rough=0.25, metallic=1.0)
M_BIM1, B_BIM1 = mat("BimetalTop", (0.85, 0.50, 0.25), rough=0.25, metallic=1.0, emit_rgb=GOLD)
M_BIM2, B_BIM2 = mat("BimetalBottom", (0.78, 0.79, 0.80), rough=0.25, metallic=1.0, emit_rgb=GOLD)
M_CONT, B_CONT = mat("Contact", (0.85, 0.85, 0.88), rough=0.2, metallic=1.0, emit_rgb=GOLD)
M_BRASS, B_BRASS = mat("ValveSeat", (0.80, 0.60, 0.28), rough=0.25, metallic=1.0, emit_rgb=RED)
M_COPPER, _ = mat("Wire", (0.72, 0.38, 0.18), rough=0.3, metallic=1.0)
M_TANK, _ = mat("TankShell", (0.75, 0.90, 0.98), rough=0.05)
_bt = bsdf_of(M_TANK); _bt.inputs["Transmission Weight"].default_value = 1.0; _bt.inputs["IOR"].default_value = 1.2; _bt.inputs["Alpha"].default_value = 0.35
M_WATER, B_WATER, _ = water_sec("TankWater")
M_DROP, B_DROP = emit_mat("Drop", CYAN, 3.0)
M_PUFF, B_PUFF = mat("Puff", (0.95, 0.96, 0.98), rough=1.0, emit_rgb=(1, 1, 1), alpha=0.6); B_PUFF.inputs["Emission Strength"].default_value = 0.8
M_SCALE, _ = mat("Limescale", (0.93, 0.92, 0.86), rough=0.95, noise=30)
M_SHIRT, _ = mat("Shirt", (0.55, 0.70, 0.88), rough=0.9, noise=60)
M_PLACKET, _ = mat("Placket", (0.60, 0.75, 0.92), rough=0.9, noise=60)
M_BOARD, _ = mat("BoardCover", (0.55, 0.56, 0.58), rough=0.8, noise=25)
M_BTN, B_BTN = mat("Button", (0.96, 0.95, 0.92), rough=0.25, emit_rgb=CYAN)
M_BTNM, B_BTNM = mat("ButtonMelt", (0.96, 0.95, 0.92), rough=0.25, emit_rgb=RED)
M_BURNT, _ = mat("BurntButton", (0.45, 0.30, 0.16), rough=0.35)
M_SCORCH, _ = mat("Scorch", (0.28, 0.16, 0.07), rough=1.0, noise=8)
M_WET, _ = mat("WetSpot", (0.22, 0.34, 0.52), rough=0.15)
M_STUDIO, _ = mat("StudioFloor", (0.035, 0.04, 0.05), rough=0.6)
M_BACK, _ = mat("Backdrop", (0.05, 0.06, 0.08), rough=0.8)
B_PARK_X, B_MELT_X = 12.0, 40.0
B_Z = 0.20                                    # shirt top (button bottom)

# ---------- iron geometry (local: soleplate bottom z = 0, tip toward +X) ----------
SOLE_L0, SOLE_TIP, SOLE_W = -12.0, 13.0, 5.5
LIP, CORE, SKIRT = 0.30, 1.10, 1.70          # z tops: thin lip, core (groove = slot between lip and skirt), dark skirt
GROOVE = 0.8
def w_out(x):
    if x >= 0: return SOLE_W * max(0.0, 1 - (x / SOLE_TIP) ** 2) ** 0.6
    if x < -10.5: u = (-10.5 - x) / 1.5; return SOLE_W - 1.5 * (1 - math.sqrt(max(0.0, 1 - u * u)))
    return SOLE_W
def g_in(x): return GROOVE * ease((x + 6.0) / 3.0)
def us(n): return [(1 - math.cos(math.pi * i / n)) / 2 for i in range(n + 1)]
def side_pts(inset=lambda x: 0.0, n=36, xmin=SOLE_L0):
    xs = [xmin + (SOLE_TIP - xmin) * u for u in us(n)]
    return [(x, w_out(x) - inset(x)) for x in xs if w_out(x) - inset(x) > 0.05]
def outline2d(inset=lambda x: 0.0, n=36):
    side = side_pts(inset, n)
    xt = side[-1][0] + 0.35 * side[-1][1]
    return [(xt, 0.0)] + [(x, y) for x, y in reversed(side)] + [(x, -y) for x, y in side]
def inset2d(pts, dfn):
    n = len(pts); out = []
    for i in range(n):
        a, b = Vector(pts[i - 1]), Vector(pts[(i + 1) % n]); d = (b - a).normalized(); nrm = Vector((-d.y, d.x))
        p = Vector(pts[i]) + nrm * dfn(pts[i][0]); out.append((p.x, p.y))
    return out
def sole_bm(ztop=None, n=40):
    """one manifold: lip (full outline) + core (inset by the groove) -> the groove is the step between them"""
    o = outline2d(n=n); i = inset2d(o, g_in); zt = CORE if ztop is None else ztop
    bm = bmesh.new(); loft_bm(bm, [[(x, y, 0.0) for x, y in o], [(x, y, LIP) for x, y in o], [(x, y, LIP) for x, y in i], [(x, y, zt) for x, y in i]])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
def prism_bm(bm, pts, z0, z1, mi=0):
    b = [bm.verts.new((x, y, z0)) for x, y in pts]; t = [bm.verts.new((x, y, z1)) for x, y in pts]
    fs = [bm.faces.new(list(reversed(b))), bm.faces.new(t)]
    for i in range(len(pts)):
        j = (i + 1) % len(pts); fs.append(bm.faces.new([b[i], b[j], t[j], t[i]]))
    for f in fs: f.material_index = mi
def loft_bm(bm, rings, mi=0):
    R = [[bm.verts.new(p) for p in r] for r in rings]; n = len(rings[0])
    fs = [bm.faces.new(list(reversed(R[0]))), bm.faces.new(R[-1])]
    for a, b in zip(R, R[1:]):
        for i in range(n):
            j = (i + 1) % n; fs.append(bm.faces.new([a[i], a[j], b[j], b[i]]))
    for f in fs: f.material_index = mi
BODY_RINGS = [(SKIRT, 1.0, 1.0), (2.9, 0.98, 0.95), (4.1, 0.90, 0.84), (5.0, 0.79, 0.67), (5.55, 0.66, 0.50)]
def body_rings(cx=-1.0):
    base = outline2d(n=36)
    return [[(cx + (x - cx) * sx, y * sy, z) for x, y in base] for z, sx, sy in BODY_RINGS]
def clip_bm(bm, co, no, fill=True):
    """remove the side the normal points to; cap the cut"""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=True)
    if fill:
        oe = [e for e in bm.edges if len(e.link_faces) < 2]
        if oe: bmesh.ops.edgeloop_fill(bm, edges=oe)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def mark_plane(o, co, no, mi=1, eps=1e-3):
    me = o.data; co, no = Vector(co), Vector(no)
    while len(me.materials) <= mi: me.materials.append(M_SEC)
    for p in me.polygons:
        if all(abs((me.vertices[v].co - co).dot(no)) < eps for v in p.vertices): p.material_index = mi
def smooth(o, ang=40):
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(ang))
    except Exception: pass
    return o
HANDLE_PTS = [(-9.6, 0, 4.8), (-9.4, 0, 8.0), (-8.2, 0, 10.2), (-5.0, 0, 10.9), (0.0, 0, 10.9), (3.6, 0, 10.4), (5.6, 0, 8.6), (6.8, 0, 5.2)]
def element_pts():
    side = side_pts(lambda x: 1.6, n=40, xmin=-9.5)
    xt = side[-1][0] + 0.35 * side[-1][1]
    p = [(-10.2, -side[0][1], 1.6), (-10.2, -side[0][1], 0.7)] + [(x, -y, 0.7) for x, y in side] + [(xt, 0.0, 0.7)] \
        + [(x, y, 0.7) for x, y in reversed(side)] + [(-10.2, side[0][1], 0.7), (-10.2, side[0][1], 1.6)]
    return p
def groove_band(name, m_):
    """thin glowing band on the groove wall (front part only)"""
    side = [(x, y + 0.03) for x, y in side_pts(g_in, n=40, xmin=-4.0)]
    xt = side[-1][0] + 0.35 * side[-1][1] + 0.03
    path = [(x, -y) for x, y in side] + [(xt, 0.0)] + [(x, y) for x, y in reversed(side)]
    bm = bmesh.new(); lo = [bm.verts.new((x, y, LIP + 0.02)) for x, y in path]; hi = [bm.verts.new((x, y, CORE - 0.02)) for x, y in path]
    for i in range(len(path) - 1): bm.faces.new([lo[i], lo[i + 1], hi[i + 1], hi[i]])
    return mesh_obj(name, bm, m_)

# ---------- whole iron (board set) ----------
IRON = empty("IronA")
def part(o, parent): par(o, parent); return o
LIPA = part(smooth(mesh_obj("IronA_Sole", sole_bm(), M_SOLEA), 50), IRON)
_bm = bmesh.new(); prism_bm(_bm, outline2d(n=40), CORE, SKIRT); part(smooth(mesh_obj("IronA_Skirt", _bm, M_SKIRT), 50), IRON)
_bm = bmesh.new(); loft_bm(_bm, body_rings()); BODYA = part(smooth(mesh_obj("IronA_Body", _bm, M_BODY), 50), IRON)
_ho, _ = tube("IronA_Handle", HANDLE_PTS, 1.25, M_HANDLE, seg=20); part(_ho, IRON)
part(cyl("IronA_Dial", 1.7, 0.7, "Z", (-7.6, 0, 5.55), M_ACCENT, seg=40), IRON)
part(box("IronA_Stripe", -1.0, 9.0, -0.6, 0.6, 4.6, 5.25, M_ACCENT), IRON)
LEDA = part(obj_from("IronA_LED", sphere_mesh("LEDMe", 0.35, 2), M_LED, (-4.6, 0.0, 5.62)), IRON)
GBAND = part(groove_band("IronA_GrooveBand", M_GROOVE), IRON)
# board, shirt, buttons
box("Board", -70, 95, -24, 24, -4.0, 0.0, M_BOARD)
box("Shirt", -66, 92, -18, 18, 0.0, 0.12, M_SHIRT)
box("Placket", -66, 92, -2.4, 2.4, 0.12, B_Z, M_PLACKET)
box("StudioFloorA", -400, 400, -400, 400, -90, -88, M_STUDIO)
box("BackdropA", -400, 400, 160, 162, -90, 200, M_BACK)
def button_obj(name, m_, x):
    root = empty(name, (x, 0.0, B_Z))
    b = part(cyl(name + "Disc", 0.62, 0.26, "Z", (0, 0, 0.13), m_, seg=40), root)
    part(torus(name + "Rim", 0.55, 0.07, m_, (0, 0, 0.26), 40, 10), root)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        part(cyl(f"{name}Hole{k}", 0.08, 0.30, "Z", (0.17 * math.cos(a), 0.17 * math.sin(a), 0.14), M_HOLE, seg=10), root)
    return root, b
BUTTONS = {}
for nm, x in [("BtnA", -34.0), ("BtnB", -12.0), ("BtnPark", B_PARK_X), ("BtnMelt", B_MELT_X), ("BtnE", 66.0)]:
    BUTTONS[nm] = button_obj(nm, M_BTNM if nm == "BtnMelt" else M_BTN, x)
PARK = BUTTONS["BtnPark"][0]; MELT = BUTTONS["BtnMelt"][0]
# iron path on the board (keys: t, x, y, z, rot z)
Y_PARK = -3.95
XK = [(0.0, -5.0), (C["buttons"], 4.0), (C["run"] - 0.02, 4.0), (C["run"], 20.0), (C["button"] + 0.25, 33.0), (C["heres"] - 0.02, 33.0),
      (C["heres"], -8.0), (C["slide"] - 0.02, -8.0), (C["slide"], -14.0), (C["gap"], 4.0), (C["edge2"], 4.0), (C["and"] - 0.02, 4.0),
      (C["and"], -26.0), (C["have"] - 0.02, -26.0), (C["have"], 4.0), (DUR, 4.0)]
YK = [(0.0, Y_PARK), (C["run"] - 0.02, Y_PARK), (C["run"], 0.0), (C["heres"] - 0.02, 0.0), (C["heres"], Y_PARK), (C["and"] - 0.02, Y_PARK),
      (C["and"], 7.0), (C["have"] - 0.02, 7.0), (C["have"], Y_PARK), (DUR, Y_PARK)]
RZK = [(0.0, 0.0), (C["and"] - 0.02, 0.0), (C["and"], 0.35), (C["have"] - 0.02, 0.35), (C["have"], 0.0), (DUR, 0.0)]
fx_, fy_, frz_ = PW(XK), PW(YK), PW(RZK)
def iron_z(t):
    z = 0.0
    if C["run"] <= t < C["heres"]:
        x = fx_(t); z = 0.28 * ease((x + 13.0 - (B_MELT_X - 0.6)) / 1.2)            # rides up onto the button
        z -= 0.20 * ease((t - C["plastic"]) / (C["melt"] + 0.3 - C["plastic"]))      # ... and sinks in as it melts
        z += 5.0 * ease((t - C["crack"]) / 0.35)                                     # lifted off on "crack"
    return z
def wiggle(t): return 0.45 * math.sin(2 * math.pi * 0.9 * (t - C["it"])) * ease((t - C["it"]) / 0.4) if C["it"] <= t < C["now"] else 0.0
bake_loc(IRON, lambda t: (fx_(t) + wiggle(t), fy_(t), B_Z + iron_z(t)))
bake_rot(IRON, lambda t: (0.0, 0.0, frz_(t)))
# hot plate glow (board set), groove glow, power LED (goes out on auto-off)
glowc(B_SOLEA, [(0.0, 0.0, ORANGE), (C["hot"] - 0.05, 0.0, ORANGE), (C["hot"] + 0.3, 0.5, ORANGE), (C["heres"] - 0.05, 0.5, ORANGE), (C["heres"], 0.0, ORANGE),
                (C["hot2"] - 0.05, 0.0, ORANGE), (C["hot2"] + 0.3, 0.5, ORANGE), (C["now"], 0.5, ORANGE), (C["and"], 0.4, ORANGE),
                (C["seconds"], 0.4, ORANGE), (C["seconds"] + 0.6, 0.0, ORANGE), (C["have"], 0.0, ORANGE)])
glowc(B_GROOVE, [(0.0, 0.0, GOLD), (C["notch"] - 0.05, 0.0, GOLD), (C["notch"] + 0.25, 2.5, GOLD), (C["run"] - 0.05, 2.5, GOLD), (C["run"], 0.0, GOLD),
                 (C["groove"] - 0.05, 0.0, GOLD), (C["groove"] + 0.25, 3.5, GOLD), (C["slide"], 2.0, GOLD), (C["now"], 2.0, GOLD), (C["and"], 0.0, GOLD),
                 (C["notch3"] - 0.05, 0.0, GOLD), (C["notch3"] + 0.25, 2.5, GOLD)])
glowc(B_LED, [(0.0, 3.0, (1.0, 0.55, 0.15)), (C["seconds"], 3.0, (1.0, 0.55, 0.15)), (C["seconds"] + 0.25, 0.0, (1.0, 0.55, 0.15)),
              (C["have"] - 0.05, 0.0, (1.0, 0.55, 0.15)), (C["have"], 3.0, (1.0, 0.55, 0.15))])
# the parked button: rides up into the groove as the tip slides past, stays cool (cyan rim)
def park_z(t):
    if t < C["run"]: return 0.20 * ease((t - (C["buttons"] - 0.9)) / 0.7)
    if C["slide"] <= t < C["and"]: return 0.20 * ease((t - (C["gap"] - 0.8)) / 0.7)
    if t >= C["have"]: return 0.20
    return 0.0
bake_loc(PARK, lambda t: (B_PARK_X, 0.0, B_Z + park_z(t)))
bake_rot(PARK, lambda t: (0.0, -0.25 * park_z(t), 0.0))
glowc(B_BTN, [(0.0, 0.0, CYAN), (C["it"] - 0.05, 0.0, CYAN), (C["sits"] + 0.2, 0.6, CYAN), (C["now"], 0.6, CYAN), (C["now"] + 0.05, 0.0, CYAN)])
# the melting button: squashes + reddens under the plate, then cracks; halves stick to the plate and fall off (rigid body)
T_MELT0, T_CRACK = C["plastic"], C["crack"]
bake_scale(MELT, lambda t: (1.0 + 0.3 * ease((t - T_MELT0) / (C["melt"] + 0.3 - T_MELT0)),) * 2 + (1.0 - 0.55 * ease((t - T_MELT0) / (C["melt"] + 0.3 - T_MELT0)),))
glowc(B_BTNM, [(0.0, 0.0, RED), (T_MELT0, 0.0, RED), (C["melt"] + 0.2, 1.5, RED), (T_CRACK, 1.5, RED)])
windows(MELT, [(0.0, T_CRACK)])
HALVES = []
for k, sgn in enumerate((-1, 1)):
    bm = bmesh.new(); add_cyl(bm, 0.72, 0.14, "Z", (0, 0, 0.07), 32)
    clip_bm(bm, (0, 0, 0), (-sgn, 0, 0))
    h = mesh_obj(f"ButtonHalf{k}", bm, M_BURNT); HALVES.append(h)
    hx = B_MELT_X + sgn * 0.08
    bake_loc(h, lambda t, hx=hx: (hx, 0.0, B_Z + 0.01 + 5.0 * ease((t - T_CRACK) / 0.35)))
    bake_rot(h, lambda t, sgn=sgn: (0.0, sgn * 0.25 * ease((t - T_CRACK) / 0.35), 0.0))
SHIRT_RB = box("ShirtRB", -66, 92, -18, 18, -2.0, B_Z, None); SHIRT_RB.hide_render = True; SHIRT_RB.display_type = "WIRE"
fx.rigid(HALVES, passive=[SHIRT_RB], mass=0.002, friction=0.7, bounce=0.2)
T_FALL = T_CRACK + 0.38
for h in HALVES:
    try:
        rb = h.rigid_body; rb.collision_margin = 0.004
        rb.kinematic = True; h.keyframe_insert("rigid_body.kinematic", frame=1); h.keyframe_insert("rigid_body.kinematic", frame=F(T_FALL))
        rb.kinematic = False; h.keyframe_insert("rigid_body.kinematic", frame=F(T_FALL) + 1)
    except Exception as e: print("[build] half kinematic skipped", e)
    windows_r(h, [(T_CRACK, C["heres"])])
try:
    rw = scene.rigidbody_world; rw.substeps_per_frame = 30; rw.solver_iterations = 20
except Exception as e: print("[build] rigid world tune skipped", e)
SCORCH = cyl("ScorchMark", 1.6, 0.02, "Z", (B_MELT_X, 0.0, B_Z + 0.005), M_SCORCH, seg=40)
bake_scale(SCORCH, lambda t: (0.3 + 0.7 * ease((t - T_CRACK - 0.1) / 0.5), 0.75 + 0.25 * ease((t - T_CRACK - 0.1) / 0.5), 1.0))
windows(SCORCH, [(T_CRACK + 0.1, C["heres"])])
SM_EM = cyl("ScorchSmokeEm", 1.2, 0.05, "Z", (B_MELT_X, 0.0, B_Z + 0.1), None, seg=16); SM_EM.hide_render = True
pm_smoke = fx.particles(SM_EM, "dust", F(T_CRACK), F(C["heres"]), count=160)
try:
    ps_ = pm_smoke.particle_system.settings; ps_.particle_size = 0.35; ps_.size_random = 0.7; ps_.lifetime = 45; ps_.normal_factor = 6.0
    ps_.factor_random = 1.2; ps_.effector_weights.gravity = -0.004; ps_.brownian_factor = 1.0
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.35, 0.34, 0.33, 1); b_.inputs["Alpha"].default_value = 0.5
    SM_EM.show_instancer_for_render = False
except Exception as e: print("[fx] smoke tune skipped:", e)

# ================= cutaway iron (x = X0): section y = 0 behind, soleplate cut level with the element in front =================
CUT = empty("IronC", (X0, 0.0, IZ))
SECW = [(C["cut"], C["and"])]
CH = (-2.5, 5.0, -2.2, 2.2, 0.42, 1.0)                                       # steam chamber (local)
CHCUT = box("ChamberCutter", CH[0], CH[1], CH[2], CH[3], CH[4], CH[5], None); CHCUT.hide_render = True; CHCUT.display_type = "WIRE"; par(CHCUT, CUT)
def sole_piece(name, y_side, ztop):
    bm = sole_bm(ztop); clip_bm(bm, (0, 0, 0), (0, -y_side, 0))
    o = mesh_obj(name, bm, [M_SOLE, M_SEC]); mark_plane(o, (0, 0, 0), (0, 1, 0))
    if ztop < CORE: mark_plane(o, (0, 0, ztop), (0, 0, 1), mi=0)
    boolean(o, CHCUT, "Chamber"); par(o, CUT); return o
SOLE_B = sole_piece("SoleBack", 1, CORE)                                      # y >= 0, full height
SOLE_F = sole_piece("SoleFront", -1, 0.70)                                    # y <= 0, cut level with the element
_bm = bmesh.new(); prism_bm(_bm, inset2d(outline2d(n=40), g_in), 0.70, CORE); clip_bm(_bm, (0, 0, 0), (0, 1, 0))
SOLE_FT = mesh_obj("SoleFrontTop", _bm, M_SOLE)                              # the slab that lifts off with the front housing
ELEM, _ = tube("HeatingElement", element_pts(), 0.32, M_ELEM, seg=16); par(ELEM, CUT)
glowc(B_ELEM, [(0.0, 0.0, HEAT), (C["heating"] - 0.05, 0.0, HEAT), (C["heating"] + 0.5, 2.4, HEAT), (C["off"] - 0.02, 2.4, HEAT),
               (C["off"] + 0.5, 0.4, RED), (C["on2"] - 0.05, 0.4, RED), (C["on2"] + 0.4, 2.4, HEAT), (C["if"], 2.4, HEAT), (C["cold"] + 0.3, 0.0, HEAT),
               (C["shut"] - 0.05, 0.0, HEAT), (C["enough"], 2.4, HEAT), (DUR, 2.4, HEAT)])
glowc(B_SOLE, [(0.0, 0.0, CYAN), (C["if"], 0.0, CYAN), (C["cold"] + 0.3, 0.35, CYAN), (C["shut"], 0.35, CYAN), (C["enough"], 0.0, CYAN)])
# steam holes: dark discs on the chamber floor and the bottom
HOLES = [(x, y) for x in (-1.8, -0.2, 1.4, 3.0, 4.4) for y in (-1.4, 1.4)]
_bm = bmesh.new()
for x, y in HOLES: add_cyl(_bm, 0.2, 0.435, "Z", (x, y, 0.2075), 16)
par(mesh_obj("SteamHoles", _bm, M_HOLE), CUT)
# limescale: white crust plugs growing over the holes on "clogs", GN-scattered scale specks on the chamber floor
PLUGS = []
for k, (x, y) in enumerate(HOLES):
    o = cyl(f"ScalePlug{k}", 0.26, 0.06, "Z", (x, y, 0.45), M_SCALE, seg=16); par(o, CUT); PLUGS.append(o)
    tk = C["clogs"] - 0.1 + 0.06 * k
    bake_scale(o, lambda t, tk=tk: (max(1e-3, ease((t - tk) / 0.4)),) * 2 + (1.0,))
    windows(o, [(C["clogs"] - 0.1, C["and"])])
_bm = bmesh.new(); bmesh.ops.create_grid(_bm, x_segments=6, y_segments=4, size=1.0)
bmesh.ops.scale(_bm, verts=_bm.verts, vec=(3.6, 2.1, 1)); bmesh.ops.translate(_bm, verts=_bm.verts, vec=(1.25, 0, 0.432))
M_SCALEF, _ = mat("ScaleFilm", (0.93, 0.92, 0.86), rough=0.95, noise=30, alpha=0.55)
SCALE_FLOOR = mesh_obj("ScaleFloor", _bm, M_SCALEF); par(SCALE_FLOOR, CUT)
_sp = obj_from("ScaleSpeck", sphere_mesh("ScaleSpeckMe", 0.07, 1), M_SCALE)
fx.scatter(SCALE_FLOOR, _sp, density=9.0, scale_min=0.5, scale_max=1.6, seed=5)
_sp.location = (0, 0, -500)
windows(SCALE_FLOOR, [(C["limescale"] - 0.1, C["and"])])
# housing, back half (y >= 0): skirt + hollow shell, orange rims on the cut
def housing_half(name, keep_y):
    bm = bmesh.new(); prism_bm(bm, outline2d(n=40), CORE, SKIRT)
    for f in [f for f in bm.faces if abs(f.normal.z) > 0.9]: bm.faces.remove(f)
    clip_bm(bm, (0, 0, 0), (0, -keep_y, 0), fill=False)
    sk = mesh_obj(name + "Skirt", bm, [M_SKIRT, M_SEC])
    md = sk.modifiers.new("Ring", "SOLIDIFY"); md.thickness = 0.5; md.offset = -1.0; md.material_offset_rim = 1; md.use_rim = True
    bm = bmesh.new(); loft_bm(bm, body_rings()); clip_bm(bm, (0, 0, 0), (0, -keep_y, 0), fill=False)
    bm.faces.ensure_lookup_table()
    for f in list(bm.faces):
        if abs(f.calc_center_median().z - SKIRT) < 1e-3: bm.faces.remove(f)       # open bottom so the tank shows from inside
    sh = mesh_obj(name + "Shell", bm, [M_BODY, M_SEC]); smooth(sh, 50)
    md = sh.modifiers.new("Shell", "SOLIDIFY"); md.thickness = 0.28; md.offset = -1.0; md.material_offset_rim = 1; md.use_rim = True
    bm = sweep_bm(chaikin([Vector(p) for p in HANDLE_PTS], 3), [1.25] * len(chaikin([Vector(p) for p in HANDLE_PTS], 3)), 20)
    clip_bm(bm, (0, 0, 0), (0, -keep_y, 0))
    hd = mesh_obj(name + "Handle", bm, [M_HANDLE, M_SEC]); mark_plane(hd, (0, 0, 0), (0, 1, 0)); smooth(hd, 50)
    return [sk, sh, hd]
HB = housing_half("HousingBack", 1)
for o in HB: par(o, CUT)
HF = housing_half("HousingFront", -1)
FRONT = empty("FrontHalf", (X0, 0.0, IZ))
for o in HF + [SOLE_FT]: par(o, FRONT)
T_OPEN = C["open"] - 0.2
bake_loc(FRONT, lambda t: (X0, -28.0 * ease((t - T_OPEN) / 0.9), IZ + 2.0 * math.sin(math.pi * lin((t - T_OPEN) / 0.9))))
windows(FRONT, [(C["cut"], T_OPEN + 0.95)])
# water tank (front, under the handle) + water section
_bm = bmesh.new(); add_box(_bm, -3.7, 6.7, 0.0, 3.3, 1.8, 4.6)
for f in [f for f in _bm.faces if abs(f.calc_center_median().y) < 1e-3]: _bm.faces.remove(f)
TANK = mesh_obj("TankShell", _bm, M_TANK)
solidify(TANK, 0.12); par(TANK, CUT)
WATER = box("TankWater", -3.55, 6.55, 0.0, 3.15, 1.95, 3.7, M_WATER); par(WATER, CUT)
glowc(B_WATER, [(0.0, 0.0, CYAN), (C["water"] - 0.05, 0.0, CYAN), (C["tank"] + 0.2, 1.2, CYAN), (C["valve"] + 0.5, 0.3, CYAN), (C["hard"] - 0.05, 0.3, CYAN),
                (C["hard"] + 0.2, 0.9, (0.95, 0.92, 0.80)), (C["and"], 0.3, CYAN)])
# valve: brass seat tube (tank floor -> chamber roof) + steel needle that lifts to let drops through
VX, VY = 1.0, 0.65
SEAT = cyl("ValveSeat", 0.36, 1.0, "Z", (VX, VY, 1.45), M_BRASS, seg=24); par(SEAT, CUT)
NEEDLE = empty("Needle", (0, 0, 0), CUT)
part(cyl("NeedleRod", 0.14, 4.0, "Z", (VX, VY, 3.6), M_STEEL, seg=16), NEEDLE)
_bm = bmesh.new(); add_cyl(_bm, 0.001, 0.4, "Z", (VX, VY, 1.4), 16, r2=0.14); part(mesh_obj("NeedleTip", _bm, M_STEEL), NEEDLE)
part(cyl("NeedleKnob", 0.5, 0.5, "Z", (VX, VY, 5.75), M_ACCENT, seg=24), NEEDLE)
def needle_z(t):
    up = 0.0
    for a, b in OPEN_W: up = max(up, ease((t - a) / 0.3) * (1 - ease((t - b) / 0.25)))
    return 0.45 * up
bake_loc(NEEDLE, lambda t: (0.0, 0.0, needle_z(t)))
glowc(B_BRASS, [(0.0, 0.0, RED), (C["thats"] - 0.05, 0.0, RED), (C["shut"], 3.0, RED), (C["enough"] - 0.1, 3.0, RED), (C["enough"] + 0.2, 0.0, RED)])
# drops: fall from the seat into the chamber (flash when hot), or straight through a hole onto the fabric (cold)
DROP_ME = sphere_mesh("DropMe", 0.2, 2)
def drop_beads(name, wins, z_end, n=4, period=0.55, flash=True):
    out = []
    for i in range(n):
        o = obj_from(f"{name}{i}", DROP_ME, M_DROP); par(o, CUT)
        def loc(t, i=i):
            u = ((t / period) + i / n) % 1.0
            return (VX, VY, 1.0 - (1.0 - z_end) * (u * u))
        def scl(t, i=i):
            u = ((t / period) + i / n) % 1.0
            s = 0.6 + 0.4 * ease(u / 0.2)
            if flash and u > 0.85: s *= max(0.0, 1 - (u - 0.85) / 0.15)
            return (s, s, s * (1.0 + 0.6 * u))
        bake_loc(o, loc); bake_scale(o, scl); windows(o, wins); out.append(o)
    return out
DROPS = drop_beads("Drop", DRIP_W, 0.47, n=3, period=0.6, flash=True)
# chamber flash puffs: tiny steam balls popping where each drop lands
PUFFS = []
for i in range(3):
    o = obj_from(f"Puff{i}", sphere_mesh(f"PuffMe{i}", 0.5, 2), M_PUFF); par(o, CUT); PUFFS.append(o)
    def sc(t, i=i):
        u = ((t / 0.6) + i / 3) % 1.0
        return (max(1e-3, 1.6 * ease((u - 0.85) / 0.15)) if u > 0.85 else (max(1e-3, 1.6 * (1 - ease(u / 0.35))) if u < 0.35 else 1e-3),) * 3
    o.location = (VX + 0.3 * (i - 1), VY - 0.4, 0.62); bake_scale(o, sc); windows(o, [(STEAM1[0], STEAM1[1]), (STEAM2[0], C["and"])])
# cold plate: drops run through the hole under the valve and drip onto the fabric
LEAK = []
for i in range(3):
    o = obj_from(f"Leak{i}", DROP_ME, M_DROP); par(o, CUT); LEAK.append(o)
    def lk(t, i=i):
        u = ((t / 0.7) + i / 3) % 1.0
        e = ease(u / 0.3)
        return (VX + (1.4 - VX) * e, VY + (1.4 - VY) * e, 1.0 - (1.0 + IZ - 0.13) * (u * u))
    bake_loc(o, lk); windows(o, LEAK_W)
# wet spot on the fabric under the plate (cold leak)
WET = cyl("WetSpot", 2.2, 0.02, "Z", (X0 + 1.2, 1.0, 0.13), M_WET, seg=40)
bake_scale(WET, lambda t: (max(1e-3, ease((t - C["leaks"]) / 1.4)),) * 2 + (1.0,))
windows(WET, [(C["leaks"], C["thats"] + 0.3)])
# steam jets under the plate: particles from small discs at the holes, normals down
def hole_emitter(name):
    bm = bmesh.new()
    for x, y in HOLES:
        vs = bmesh.ops.create_circle(bm, cap_ends=True, segments=10, radius=0.18)["verts"]
        bmesh.ops.translate(bm, verts=vs, vec=(x, y, -0.03))
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    o = mesh_obj(name, bm, None); par(o, CUT); return o
def steam_sys(em, t0, t1, count, vel, size, life=24):
    pm = fx.particles(em, "dust", F(t0), F(t1), count=count)
    try:
        ps_ = pm.particle_system.settings; ps_.particle_size = size; ps_.size_random = 0.6; ps_.normal_factor = vel; ps_.factor_random = vel * 0.35
        ps_.lifetime = life; ps_.effector_weights.gravity = 0.0; ps_.brownian_factor = 2.0
        b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
        b_.inputs["Base Color"].default_value = (0.92, 0.94, 0.97, 1); b_.inputs["Emission Color"].default_value = (0.92, 0.94, 0.97, 1)
        b_.inputs["Emission Strength"].default_value = 0.35; b_.inputs["Alpha"].default_value = 0.28; b_.inputs["Roughness"].default_value = 1.0
        inst = ps_.instance_object; bm_ = bmesh.new(); bmesh.ops.create_icosphere(bm_, subdivisions=3, radius=1.0); bm_.to_mesh(inst.data); bm_.free()
        inst.data.shade_smooth()
        em.show_instancer_for_render = False
    except Exception as e: print("[fx] steam tune skipped:", e)
    return pm
ST_EM1 = hole_emitter("SteamEm1"); steam_sys(ST_EM1, C["blasts"] - 0.25, C["if"], 1400, 16.0, 0.55)
ST_EM2 = hole_emitter("SteamEm2"); steam_sys(ST_EM2, STEAM2[0], STEAM2[1], 500, 9.0, 0.45)
# contact sparks when the thermostat opens
# thermostat: ceramic post, bimetal strip (copper over steel) pivoting at the post, contacts at its free end
PIV = (-9.6, 0.9, 2.25)
par(box("ThermoPost", -10.5, -9.5, 0.3, 1.5, CORE, 2.6, M_CERAM), CUT)
STRIP = empty("BimetalPivot", PIV, CUT)
part(box("BimetalBottom", 0.0, 4.9, -0.5, 0.5, -0.11, 0.0, M_BIM2), STRIP)
part(box("BimetalTop", 0.0, 4.9, -0.5, 0.5, 0.0, 0.11, M_BIM1), STRIP)
part(cyl("ContactMoving", 0.22, 0.12, "Z", (4.55, 0.0, -0.17), M_CONT, seg=16), STRIP)
par(box("ContactBlock", -5.6, -4.5, 0.4, 1.4, CORE, 1.95, M_CERAM), CUT)
CFIX = par(cyl("ContactFixed", 0.22, 0.1, "Z", (PIV[0] + 4.55, PIV[1], 2.0), M_CONT, seg=16), CUT)
def bend(t):
    a = ease((t - C["heats"]) / (C["off"] - C["heats"])) * (1 - ease((t - C["cools"]) / (C["clicks2"] + 0.15 - C["cools"])))
    return -0.14 * a
bake_rot(STRIP, lambda t: (0.0, bend(t), 0.0))
glowc(B_BIM1, [(0.0, 0.0, GOLD), (C["strip"] - 0.05, 0.0, GOLD), (C["strip"] + 0.2, 1.2, GOLD), (C["metals"] + 0.4, 0.4, GOLD), (C["on2"] + 0.5, 0.0, GOLD)])
glowc(B_BIM2, [(0.0, 0.0, GOLD), (C["two"] - 0.05, 0.0, GOLD), (C["two"] + 0.2, 1.0, GOLD), (C["metals"] + 0.4, 0.3, GOLD), (C["on2"] + 0.5, 0.0, GOLD)])
glowc(B_CONT, [(0.0, 0.0, GOLD), (C["clicks"] - 0.05, 0.0, GOLD), (C["clicks"] + 0.05, 5.0, GOLD), (C["clicks"] + 0.4, 0.0, GOLD),
               (C["clicks2"] - 0.05, 0.0, CYAN), (C["clicks2"] + 0.05, 5.0, CYAN), (C["clicks2"] + 0.4, 0.0, CYAN)])
SP_EM = obj_from("SparkEm", sphere_mesh("SparkEmMe", 0.15, 1), None); SP_EM.hide_render = True; par(SP_EM, CUT); SP_EM.location = (PIV[0] + 4.55, PIV[1] - 0.3, 2.07)
pm_sp = fx.particles(SP_EM, "sparks", F(C["clicks"] + 0.05), F(C["clicks"] + 0.2), count=40)
try:
    ps_ = pm_sp.particle_system.settings; ps_.particle_size = 0.04; ps_.normal_factor = 25.0; ps_.lifetime = 10; ps_.effector_weights.gravity = 0.3
except Exception as e: print("[fx] spark tune skipped:", e)
# wires: element terminals -> thermostat
for k, yy in enumerate((-3.9, 3.9)):
    if yy < 0: continue
    o, _ = tube(f"Wire{k}", [(-10.2, yy, 1.6), (-10.6, yy * 0.7, 2.2), (-10.2, 1.0, 2.6)], 0.09, M_COPPER, seg=8); par(o, CUT)
# Mantaflow: the cold-plate leak dripping onto the fabric (laptop --bake-fluid; hidden without the cache)
FL_DOM = box("FluidDomain", X0 - 1.0, X0 + 4.0, -1.0, 3.5, 0.12, IZ - 0.05, None); FL_DOM.display_type = "WIRE"
FL_IN = obj_from("FluidInflow", sphere_mesh("FluidInMe", 0.16, 2), None, (X0 + 1.0, 1.4, IZ - 0.25)); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
FL_RB = box("FabricRB", X0 - 30, X0 + 30, -20, 20, -2.0, 0.12, None); FL_RB.hide_render = True; FL_RB.display_type = "WIRE"
fx.fluid_domain(FL_DOM, FL_IN, eff=[FL_RB], res=48, start=F(C["cold"]), end=F(C["cold"] + 3.0), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_DOM.data.materials.append(water_sec("FluidWater")[0])
windows(FL_DOM, [(C["cold"], C["thats"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True
# studio set: dark floor, folded fabric swatch under the iron, backdrop
box("StudioFloorC", X0 - 300, X0 + 300, -300, 300, -2.0, 0.0, M_STUDIO)
box("SwatchC", X0 - 22, X0 + 24, -14, 12, 0.0, 0.12, M_SHIRT)
box("BackdropC", X0 - 300, X0 + 300, 60, 62, -2, 200, M_BACK)

# ================= lights + world =================
fx.hdri("studio", strength=0.35, rotation_deg=40.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, rot, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o, d_
def aim(o, target):
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
for nm, loc, tgt, size, en, rgb in [
        ("KeyA", (30, -60, 55), (15, 0, 0), 60, 2.2e4, (1.0, 0.93, 0.85)), ("FillA", (-40, 40, 40), (15, 0, 0), 60, 6.0e3, (0.75, 0.82, 1.0)),
        ("RimA", (40, 70, 20), (15, 0, 0), 40, 6.0e3, (0.6, 0.75, 1.0)),
        ("KeyC", (X0 - 30, -45, 35), (X0, 0, IZ + 3), 30, 4.0e3, (1.0, 0.95, 0.9)), ("RimC", (X0 + 35, 30, 25), (X0, 0, IZ + 3), 30, 2.5e3, (0.6, 0.75, 1.0)),
        ("LowC", (X0, -30, -5), (X0, 0, IZ), 25, 1.2e3, (1.0, 0.9, 0.8))]:
    o, _ = area(nm, loc, (0, 0, 0), size, en, rgb); aim(o, tgt)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
GX = B_PARK_X                                  # the parked button (board set)
def cX(dx, dy, dz): return (X0 + dx, dy, IZ + dz)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (15, 12, 5.0), (10.0, -1.4, 0.7), 40),                                  # hook: the tip slides up to a button, the groove glows
    (C["buttons"], (14.5, 10.5, 4.0), (11.0, -0.8, 0.6), 42),
    (C["run"], (B_MELT_X + 16, -26, 15), (B_MELT_X - 2, 0, 1.5), 38, "cut"),     # stake: straight over a plastic button
    (C["melt"], (B_MELT_X + 12, -20, 11), (B_MELT_X - 1, 0, 1.2), 40),
    (C["crack"] - 0.05, (B_MELT_X + 12, -20, 11), (B_MELT_X - 1, 0, 1.2), 40),
    (C["crack"], (B_MELT_X + 6, -12, 8), (B_MELT_X, 0, 1.6), 40, "cut"),        # crack: the stuck halves fall off, scorch mark + smoke
    (C["heres"] - 0.05, (B_MELT_X + 5, -10, 6.5), (B_MELT_X, 0, 0.6), 42),
    (C["heres"], (27, 5, 10), (4.0, -3.9, 1.0), 36, "cut"),                     # the groove: the whole tip, glowing slot
    (C["between"], (17, 8, 5.0), (3.0, -2.4, 0.9), 42),
    (C["slide"] - 0.05, (16, 7.5, 4.6), (3.0, -2.4, 0.9), 42),
    (C["slide"], (GX + 8, 14, 6.0), (GX - 3, -1.0, 0.6), 40, "cut"),            # slide the tip in beside a button
    (C["gap"], (GX + 5, 9.5, 3.4), (GX - 0.5, -0.4, 0.7), 46),
    (C["it"], (GX + 4.5, 8.5, 2.8), (GX, -0.3, 0.6), 48),
    (C["presses"], (GX + 4, -20, 10), (GX - 6, -4, 0.8), 40, "cut"),            # the plate presses the fabric right up to its edge
    (C["now"] - 0.05, (GX + 3, -18, 9), (GX - 6, -4, 0.8), 40),
    (C["now"], cX(21, -28, 15), cX(0.0, 0, 3.5), 35, "cut"),                    # cut the iron open: front half lifts away
    (C["heating"] - 0.05, cX(22, -31, 16), cX(0.0, 0, 3.0), 35),
    (C["heating"], cX(9, -21, 14), cX(3.0, -2.5, 0.8), 40, "cut"),              # heating element in the aluminum
    (C["on"] - 0.05, cX(8, -19, 12.5), cX(3.0, -2.5, 0.8), 40),
    (C["on"], cX(-3, -14, 6.5), cX(-7.0, 0.9, 2.0), 45, "cut"),                 # the bimetal strip
    (C["above"] - 0.05, cX(-3.5, -13, 6.0), cX(-7.0, 0.9, 2.0), 45),
    (C["above"], cX(7, -27, 11), cX(1.5, 1.5, 3.0), 40, "cut"),                 # the water tank
    (C["valve"], cX(4.5, -13, 5.5), cX(1.2, 0.4, 0.9), 45, "cut"),              # valve + drips into the chamber
    (C["each"] - 0.05, cX(4.0, -12, 5.0), cX(1.2, 0.4, 0.8), 45),
    (C["each"], cX(3.5, -10.5, 4.4), cX(1.1, 0.4, 0.7), 45),
    (C["blasts"] - 0.1, cX(10, -28, 1.0), cX(1.5, 0, -0.9), 35, "cut"),          # steam blasts out of the holes onto the fabric
    (C["if"] - 0.05, cX(9, -26, 0.8), cX(1.5, 0, -0.9), 35),
    (C["if"], cX(8, -22, 2.5), cX(1.5, 0.8, -1.0), 40, "cut"),                  # too cold: drops leak through onto the fabric
    (C["thats"] - 0.05, cX(7.5, -21, 2.2), cX(1.5, 0.8, -1.2), 40),
    (C["thats"], cX(4.5, -13, 5.5), cX(1.2, 0.5, 1.2), 45, "cut"),              # valve shut until hot
    (C["hard"] - 0.05, cX(4.0, -12, 5.0), cX(1.2, 0.5, 1.1), 45),
    (C["hard"], cX(3.5, -10, 6.5), cX(1.5, 0.0, 0.45), 45, "cut"),              # limescale on the chamber floor, holes clog
    (C["and"] - 0.05, cX(3.0, -9, 5.8), cX(1.5, 0.0, 0.45), 45),
    (C["and"], (-14, -30, 20), (-24, 7, 2.0), 36, "cut"),                       # auto-off: face down, unmoved, LED goes out
    (C["have"] - 0.05, (-15, -25, 16), (-24, 7, 3.0), 38),
    (C["have"], (GX + 4.5, 8.5, 2.8), (GX, -0.3, 0.6), 48, "cut"),              # CTA: button parked in the notch, slow pull-out
    (DUR, (GX + 12, 18, 9), (GX - 4, -2, 1.0), 40),
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
bake_scalar(cam_d, "dof.aperture_fstop", [max(5.6, min(22.0, 0.8 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 6; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0, min(4.0e3, 0.12 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (2, 3, 0)
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
fx.bake_rigid(F(T_CRACK) - 1, F(C["heres"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "groove": W(IRON, (8.0, w_out(8.0) - 0.4, 0.7)), "lip": W(IRON, (10.0, w_out(10.0), 0.15)), "body": W(IRON, (6.0, 2.5, 3.0)),
    "button": W(PARK, (0, 0, 0.26)), "melt": (B_MELT_X, 0.0, B_Z + 0.3), "led": W(IRON, (-4.6, 0.0, 5.95)),
    "element": W(CUT, (6.5, -(w_out(6.5) - 1.6), 1.0)), "plate": W(CUT, (4.5, -2.8, 0.7)), "strip": W(STRIP, (2.4, 0.0, 0.11)),
    "tank": W(CUT, (3.0, 1.5, 3.7)), "valve": W(CUT, (VX, VY, 1.95)), "chamber": W(CUT, (3.8, -1.2, 0.45)), "holes": W(CUT, (3.0, -1.4, -0.05)),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4], "melt": RR(T_MELT0, C["melt"] + 0.3), "crack": round(T_CRACK, 3), "fall": round(T_FALL + 0.1, 3),
          "slide_a": RR(0.0, C["buttons"]), "slide_b": RR(C["slide"], C["gap"]), "run": RR(C["run"], C["button"] + 0.25), "open": round(T_OPEN, 3),
          "elem_on": round(C["heating"], 3), "click_off": round(C["clicks"], 3), "click_on": round(C["clicks2"], 3), "bend": RR(C["heats"], C["off"]),
          "valve_open": [RR(a, b) for a, b in OPEN_W], "drips": [RR(a, b) for a, b in DRIP_W], "leak": [RR(a, b) for a, b in LEAK_W],
          "steam1": RR(*STEAM1), "steam2": RR(*STEAM2), "valve_shut": round(C["shut"], 3), "clog": round(C["clogs"] - 0.1, 3),
          "led_off": round(C["seconds"], 3), "park_in": [round(C["buttons"] - 0.9, 3), round(C["gap"] - 0.8, 3), round(C["have"], 3)],
          "set_a": [RR(a, b) for a, b in SET_A], "set_c": [RR(a, b) for a, b in SET_C]}
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
