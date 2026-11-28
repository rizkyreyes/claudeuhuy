# Wine bottle punt (3d-41): "The dent in the bottom of a wine bottle has nothing to do with how good the wine is."
# Stake: in champagne the dent sits under up to ~90 psi (~3x a car tire). It's called a punt; hand-blown bottles came out with a rough
# seam in the middle of the base -> wobble + sharp point; glassblowers pushed the seam up -> stands level on a smooth ring, sharp bit
# tucked inside; may have added strength. Today machines: a glob (~2,000 F) drops into a mold, air blows it into shape, dent and all.
# Still wine: mostly tradition. Sparkling: second fermentation, gas pushes on every inch; the curved punt helps spread that push.
# Sediment story unproven; deeper dent != better wine, mostly more glass.
# Illustrative, 1 unit = 1 cm. Sets along X: hook/CTA bottle (x 0), champagne cutaway + tire (x 100), hand glassblowing (x 200),
# table (x 300), machine mold + cooling floor (x 400-525), shallow vs deep punt (x 620). Generic bottles, no brand, no text, no people.
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
CUES = [("the","The"),("dent","dent"),("bottom","bottom"),("wine","wine"),("bottle","bottle"),("nothing","nothing"),("good","good"),("is","is."),
  ("but","But"),("champagne","champagne,"),("that","that"),("dent2","dent"),("sits","sits"),("under","under"),("ninety","ninety"),("pounds","pounds"),
  ("inch","inch."),("thats","That's"),("three","three"),("times","times"),("car","car"),("tire","tire."),
  ("its","It's"),("called","called"),("punt","punt,"),("started","started"),("glassblowers","glassblower's"),("fix","fix."),
  ("back","Back"),("every","every"),("blown","blown"),("hand","hand,"),("bottom2","bottom"),("rough","rough"),("seam","seam"),("middle","middle."),
  ("stand","Stand"),("table","table"),("wobbles","wobbles,"),("sharp","sharp"),("point","point"),("underneath","underneath."),
  ("so","So"),("glassblower","glassblower"),("pushed","pushed"),("seam2","seam"),("up","up,"),("into","into"),("bottle2","bottle."),
  ("now","Now"),("stands","stands"),("level","level"),("smooth","smooth"),("ring","ring,"),("sharp2","sharp"),("tucked","tucked"),("inside","inside."),
  ("it","It"),("stronger","stronger,"),("today","Today,"),("machines","machines"),("glob","glob"),("two","two"),("thousand","thousand"),
  ("degrees","degrees"),("drops","drops"),("mold","mold,"),("air","air"),("blows","blows"),("shape","shape,"),("dent3","dent"),("all","all."),
  ("those","Those"),("tough","tough,"),("still","still"),("tradition","tradition."),
  ("sparkling","Sparkling"),("different","different."),("champagne2","champagne,"),("second","second"),("fermentation","fermentation"),
  ("fills","fills"),("sealed","sealed"),("gas","gas"),("pushes","pushes"),("every2","every"),("glass","glass."),
  ("curved","curved"),("punt2","punt"),("spread","spread"),("evenly","evenly"),("base","base."),
  ("sediment","sediment"),("story","story?"),("nobody","Nobody"),("proven","proven"),
  ("deeper","deeper"),("dent4","dent"),("better","better"),("either","either."),("mostly","Mostly,"),("more","more"),("glass2","glass."),
  ("have","Have"),("checked","checked"),("bottom3","bottom"),("buying","buying"),("tell","Tell"),("comments","comments.")]
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
CL = coll("Wine")
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
TAU = 2 * math.pi
X_H, X_P, X_G, X_T, X_M, X_S = 0.0, 100.0, 200.0, 300.0, 400.0, 620.0
# ---------- materials ----------
def glass_mat(name, rgb, rough=0.04, emit=(0.3, 0.9, 0.45)):
    m, b = mat(name, rgb, rough=rough, emit_rgb=emit)
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.5
    return m, b
M_GLASS, B_GLASS = glass_mat("Glass", (0.16, 0.52, 0.22))
M_GLASS_CH, _ = glass_mat("GlassChamp", (0.10, 0.36, 0.14))
M_CUT, B_CUT = mat("GlassCut", (0.42, 0.92, 0.52), rough=0.25, emit_rgb=(0.35, 1.0, 0.55))
B_CUT.inputs["Transmission Weight"].default_value = 0.35; B_CUT.inputs["Emission Strength"].default_value = 0.55
M_HOT, B_HOT = mat("HotGlass", (0.55, 0.16, 0.03), rough=0.12, emit_rgb=(1.0, 0.36, 0.06)); B_HOT.inputs["Emission Strength"].default_value = 1.1
M_HOTCUT, B_HOTCUT = mat("HotGlassCut", (1.0, 0.55, 0.15), rough=0.3, emit_rgb=(1.0, 0.62, 0.18)); B_HOTCUT.inputs["Emission Strength"].default_value = 2.2
M_WINE, B_WINE = mat("Wine", (0.30, 0.02, 0.06), rough=0.08, emit_rgb=(0.6, 0.05, 0.12))
B_WINE.inputs["Transmission Weight"].default_value = 0.55; B_WINE.inputs["IOR"].default_value = 1.05; B_WINE.inputs["Emission Strength"].default_value = 0.15
M_FIZZ, B_FIZZ = mat("Champagne", (0.95, 0.80, 0.42), rough=0.05, emit_rgb=(1.0, 0.82, 0.4))
B_FIZZ.inputs["Transmission Weight"].default_value = 0.75; B_FIZZ.inputs["IOR"].default_value = 1.05; B_FIZZ.inputs["Emission Strength"].default_value = 0.25
M_LABEL, _ = mat("Label", (0.86, 0.80, 0.66), rough=0.6)
M_CAPS, _ = mat("Capsule", (0.40, 0.04, 0.07), rough=0.3, metallic=0.7)
M_FOIL, _ = mat("Foil", (0.80, 0.62, 0.26), rough=0.28, metallic=1.0)
M_CORK, _ = mat("Cork", (0.62, 0.46, 0.28), rough=0.8, noise=40.0)
M_FLOOR, _ = mat("StudioFloor", (0.030, 0.031, 0.036), rough=0.55)
M_BACK, _ = mat("Backdrop", (0.045, 0.05, 0.065), rough=0.9)
M_WOOD, _ = mat("Wood", (0.34, 0.19, 0.09), rough=0.45, noise=6.0)
M_STEEL, _ = mat("Steel", (0.42, 0.43, 0.46), rough=0.32, metallic=1.0, noise=12.0)
M_MOLDCUT, B_MOLDCUT = mat("MoldCut", (0.07, 0.07, 0.08), rough=0.5, metallic=0.6, emit_rgb=(1.0, 0.45, 0.12))
M_RUBBER, _ = mat("Rubber", (0.025, 0.025, 0.028), rough=0.7)
M_BELT, _ = mat("Belt", (0.06, 0.06, 0.07), rough=0.6, noise=30.0)
M_SED, _ = mat("Sediment", (0.12, 0.05, 0.03), rough=0.9)
M_GOLD, B_GOLD = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 0.0)
M_GOLDX, B_GOLDX = emit_mat("GoldGlass", (0.98, 0.74, 0.27), 0.0)
M_GOLD2, B_GOLD2 = emit_mat("GoldRing", (0.98, 0.74, 0.27), 5.0)
M_CYAN2, B_CYAN2 = emit_mat("CyanArch", (0.30, 0.92, 1.0), 0.0)
M_CYAN, B_CYAN = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 0.0)
M_CYANA, B_CYANA = emit_mat("CyanArrows", (0.30, 0.92, 1.0), 0.0)
M_TIREA, B_TIREA = emit_mat("TireArrows", (0.30, 0.92, 1.0), 0.0)
M_RED, B_RED = emit_mat("RedGlow", (1.0, 0.30, 0.24), 0.0)
M_FURN, B_FURN = emit_mat("Furnace", (1.0, 0.45, 0.1), 14.0)
M_BUB, B_BUB = mat("Bubble", (0.95, 0.95, 0.9), rough=0.05, emit_rgb=(1.0, 0.95, 0.8)); B_BUB.inputs["Emission Strength"].default_value = 1.2

# ---------- bottle profiles (r, z), same vertex count for every parameter set -> shape keys ----------
STILL = dict(R=3.7, H=30.0, th=0.32, thb=0.55, hp=2.0, rr=0.84, bt=19.0, nr=1.45, nz=23.5)
CHAMP = dict(R=4.4, H=30.5, th=0.50, thb=0.80, hp=3.6, rr=0.80, bt=17.5, nr=1.60, nz=24.5)
NB = 12
def bprof(R, H, th, thb, hp, rr, bt, nr, nz, pointy=False, zoff=0.0):
    O = []
    for i in range(NB + 1):
        u = i / NB; r = max(0.003, rr * R * u)
        z = hp * (1 - u) ** 1.7 if pointy else hp * (1 - u * u)
        O.append((r, z))
    O += [(rr * R + (R - rr * R) * 0.45, 0.10), (R * 0.985, 0.50), (R, 1.3), (R, bt * 0.5), (R, bt)]
    for k in range(1, 8):
        s = k / 7; O.append((R + (nr - R) * ease(s), bt + (nz - bt) * s))
    O.append((nr, H - 1.3))
    I = []
    for j, (r, z) in enumerate(O):
        a = O[max(0, j - 1)]; b = O[min(len(O) - 1, j + 1)]
        dr, dz = b[0] - a[0], b[1] - a[1]; L = math.hypot(dr, dz) or 1.0
        nx, nz_ = -dz / L, dr / L
        d = thb if j <= NB else (thb + th) / 2 if j <= NB + 2 else th
        I.append((max(0.003, r + nx * d), z + nz_ * d))
    I[0] = (0.003, O[0][1] + thb)
    lip = [(nr + 0.18, H - 1.1), (nr + 0.18, H), (nr - th * 0.9, H)]
    poly = O + lip + list(reversed(I))
    if zoff: poly = [(r, z + zoff) for r, z in poly]; O = [(r, z + zoff) for r, z in O]; I = [(r, z + zoff) for r, z in I]
    return poly, O, I
def P(base, **kw): d = dict(base); d.update(kw); return d
def lathe_bm(prof, ang=TAU, seg=48, a0=0.0, cap_mi=1, bm=None, offset=(0, 0, 0)):
    closed = abs(ang - TAU) < 1e-6
    bm = bm or bmesh.new(); n = len(prof); steps = seg if closed else seg + 1
    ox, oy, oz = offset
    rings = [[bm.verts.new((ox + r * math.cos(a0 + ang * i / seg), oy + r * math.sin(a0 + ang * i / seg), oz + z)) for r, z in prof] for i in range(steps)]
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % steps]
        for k in range(n):
            try: bm.faces.new([a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]])
            except ValueError: pass
    if not closed:
        for ring in (rings[0], rings[-1]):
            try: f = bm.faces.new(ring); f.material_index = cap_mi
            except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
def lathe_coords(prof, ang=TAU, seg=48, a0=0.0):
    closed = abs(ang - TAU) < 1e-6; steps = seg if closed else seg + 1
    return [(r * math.cos(a0 + ang * i / seg), r * math.sin(a0 + ang * i / seg), z) for i in range(steps) for r, z in prof]
def smooth(o, ang=50):
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(ang))
    except Exception: pass
    return o
def lathe_obj(name, prof, mats, ang=TAU, seg=48, a0=0.0, loc=(0, 0, 0), parent=None):
    o = mesh_obj(name, lathe_bm(prof, ang, seg, a0), mats, parent); o.location = loc; return smooth(o)
def half(name, prof, mats, loc=(0, 0, 0), seg=40, parent=None):
    """back half (y >= 0): the camera at -Y looks into the cut."""
    return lathe_obj(name, prof, mats, ang=math.pi, seg=seg, a0=0.0, loc=loc, parent=parent)
def region_below(I, zf):
    """liquid region inside the bottle up to zf (from the inner profile)."""
    pts = []
    for (r0, z0), (r1, z1) in zip(I, I[1:]):
        if z0 <= zf: pts.append((r0, z0))
        if (z0 - zf) * (z1 - zf) < 0:
            u = (zf - z0) / (z1 - z0); pts.append((r0 + (r1 - r0) * u, zf)); break
    pts.append((0.003, zf)); return pts
def base_glass(O, I):
    return O[:NB + 1] + list(reversed(I[:NB + 1]))
def nub_bm(bm, center, r=0.34, seed=3):
    rnd = random.Random(seed)
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in res["verts"]:
        v.co *= 0.75 + 0.5 * rnd.random(); v.co += Vector(center)
    return res["verts"]
def arrows_obj(name, specs, m_, y=-0.35):
    bm = bmesh.new()
    for (bx, bz), (dx, dz), L, w in specs: add_arrow(bm, (bx, bz), (dx, dz), L, w, y=y)
    return mesh_obj(name, bm, m_)
def pulse_keys(t0, t1, peak, up=0.25):
    return [(t0 - 0.01, 0.0), (t0 + up, peak), (t1 - up, peak), (t1, 0.0)]
def lens_ring(name, R, r, m_, loc, parent=None):
    o = torus(name, R, r, m_, loc)
    if parent: par(o, parent)
    return o

# ---------- studio: floor + backdrop across all sets ----------
box("StudioFloor", -120, 760, -220, 70, -2.0, -0.05, M_FLOOR)
box("Backdrop", -120, 760, 70, 72, -2.0, 220, M_BACK)

# ================= SET H: hook + CTA bottle (x 0) =================
pH, OH, IH = bprof(**STILL)
HOOK_PIV = empty("HookPivot", (X_H, 0, 22.0))
HOOK_SPIN = empty("HookSpin", (0, 0, 0), HOOK_PIV)
HOOK_B = lathe_obj("HookBottle", pH, [M_GLASS], loc=(0, 0, -15.0), parent=HOOK_SPIN)
lathe_obj("HookWine", region_below(IH, 22.0), [M_WINE], loc=(0, 0, -15.0), parent=HOOK_SPIN)
lathe_obj("HookLabel", [(3.71, 8.0), (3.76, 8.0), (3.76, 16.0), (3.71, 16.0)], [M_LABEL], loc=(0, 0, -15.0), parent=HOOK_SPIN)
lathe_obj("HookCapsule", [(0.003, 30.05), (1.66, 30.05), (1.66, 26.0), (1.50, 26.0), (1.50, 29.9), (0.003, 29.9)], [M_CAPS], loc=(0, 0, -15.0), parent=HOOK_SPIN)
HOOK_RING = lens_ring("HookPuntRing", STILL["rr"] * STILL["R"], 0.09, M_GOLD, (0, 0, -15.0 + 0.04), HOOK_SPIN)
def hook_rot(t):
    if t < C["have"]: return PW([(0.0, -34.0), (C["is"], -44.0), (C["but"], -46.0)])(t)
    return PW([(C["have"], -48.0), (DUR, -34.0)])(t)
bake_rot(HOOK_PIV, lambda t: (math.radians(hook_rot(t)), 0.0, math.radians(12.0)))
bake_rot(HOOK_SPIN, lambda t: (0.0, 0.0, 0.35 * t))
glow(B_GOLD, [(0.0, 0.0), (C["dent"], 0.0), (C["dent"] + 0.3, 6.0), (C["is"], 3.0), (C["but"] - 0.05, 3.0), (C["but"], 0.0),
              (C["checked"], 0.0), (C["bottom3"] + 0.2, 6.0), (DUR, 4.0)])

# ================= SET P: champagne cutaway + tire (x 100) =================
pC, OC, IC = bprof(**CHAMP)
half("Champ", pC, [M_GLASS_CH, M_CUT], loc=(X_P, 0, 0))
half("ChampWine", region_below(IC, 23.0), [M_FIZZ, M_FIZZ], loc=(X_P, 0, 0))
H_C = CHAMP["H"]; NRI = CHAMP["nr"] - CHAMP["th"]
half("ChampCork", [(0.003, H_C - 4.0), (NRI, H_C - 4.0), (NRI, H_C + 0.8), (1.55, H_C + 0.9), (1.55, H_C + 2.2), (0.003, H_C + 2.3)], [M_CORK, M_CORK], loc=(X_P, 0, 0))
half("ChampFoil", [(CHAMP["nr"] + 0.2, H_C - 5.5), (CHAMP["nr"] + 0.26, H_C - 5.5), (CHAMP["nr"] + 0.26, H_C + 0.2), (CHAMP["nr"] + 0.2, H_C + 0.2)], [M_FOIL, M_FOIL], loc=(X_P, 0, 0))
for k, zz in enumerate((H_C + 0.5, H_C + 1.6)):
    o = torus(f"Cage{k}", 1.62, 0.05, M_FOIL, (X_P, 0, zz))
R_C, TH_C, HP_C, RR_C, THB_C = CHAMP["R"], CHAMP["th"], CHAMP["hp"], CHAMP["rr"], CHAMP["thb"]
# pressure arrows: walls (outward), dome (down onto the punt), cork (up)
spec = []
for zz in (5.0, 9.0, 13.0, 17.0):
    for sgn in (-1, 1): spec.append(((X_P + sgn * (R_C - TH_C - 1.9), zz), (sgn, 0), 1.6, 0.9))
for u in (0.0, 0.45, 0.8):
    for sgn in ((1,) if u == 0 else (-1, 1)):
        xs = sgn * RR_C * R_C * u; zs = HP_C * (1 - u * u) + THB_C
        d = Vector((sgn * 0.9 * u, -1.0)).normalized()
        spec.append(((X_P + xs - d.x * 1.9, zs - d.y * 1.9), (d.x, d.y), 1.6, 0.9))
spec.append(((X_P, H_C - 6.5), (0, 1), 1.6, 0.9))
P_ARROWS = arrows_obj("PressureArrows", spec, M_CYANA)
PRESS_W = [(C["sits"], C["its"]), (C["fills"], C["sediment"])]
windows(P_ARROWS, PRESS_W)
glow(B_CYANA, [(0.0, 0.0), (C["sits"], 0.0), (C["sits"] + 0.3, 4.0), (C["ninety"], 4.0), (C["inch"], 7.0), (C["its"], 3.0),
               (C["fills"], 0.0), (C["gas"], 4.0), (C["pushes"] + 0.2, 7.0), (C["glass"], 4.0), (C["curved"], 2.0), (C["spread"], 5.0), (C["sediment"], 3.0)])
bake_scale(P_ARROWS, lambda t: (1.0, 1.0, 1.0))
# tire at the same scale cue (about 1/3 the pressure: 3 short arrows)
TIRE_PIV = empty("TirePivot", (X_P + 23.0, 0, 8.4))
TIRE_PIV.rotation_euler = (math.radians(90), 0, 0)
t_ = torus("Tire", 6.0, 2.4, M_RUBBER, (0, 0, 0), segU=48, segV=18); par(t_, TIRE_PIV)
o = cyl("TireRim", 3.9, 3.2, "Z", (0, 0, 0), M_STEEL, seg=40); par(o, TIRE_PIV)
o = cyl("TireHub", 1.1, 3.6, "Z", (0, 0, 0), M_STEEL, seg=20); par(o, TIRE_PIV)
tspec = []
for k in range(6):
    a = TAU * k / 6 + 0.3; c_, s_ = math.cos(a), math.sin(a)
    tspec.append(((X_P + 23.0 + c_ * 4.4, 8.4 + s_ * 4.4), (c_, s_), 0.55, 0.6))
T_ARROWS = arrows_obj("TireArrows", tspec, M_TIREA, y=-2.6)
TIRE_W = [(C["thats"] - 0.2, C["its"])]
for o in (TIRE_PIV, T_ARROWS): windows(o, TIRE_W)
glow(B_TIREA, [(C["three"], 0.0), (C["three"] + 0.3, 4.0), (C["its"], 4.0)])
# bubbles rising in the champagne
B_ME = sphere_mesh("BubbleMe", 0.13, 1); B_ME.materials.append(M_BUB)
BUB_W = [(C["but"], C["its"]), (C["sparkling"], C["sediment"])]
rnd = random.Random(7)
BUBBLES = []
for i in range(36):
    bx = rnd.uniform(-(R_C - TH_C - 0.6), R_C - TH_C - 0.6); by = rnd.uniform(-0.15, 0.6); ph = rnd.random(); sp = rnd.uniform(3.0, 5.5)
    o = obj_from(f"Bubble{i}", B_ME)
    def fb(t, bx=bx, by=by, ph=ph, sp=sp):
        z0, z1 = HP_C + THB_C + 0.6, 22.4
        z = z0 + ((ph * (z1 - z0) + sp * t) % (z1 - z0))
        rmax = (R_C - TH_C - 0.4) if z < 17.5 else max(0.3, (R_C - TH_C - 0.4) * (1 - (z - 17.5) / 6.0))
        return (X_P + max(-rmax, min(rmax, bx + 0.25 * math.sin(3 * t + ph * 9))), by, z)
    bake_loc(o, fb); windows(o, BUB_W); BUBBLES.append(o)
# spread lines on the dome + gold ring at the rest ring
SP_LINES = []
for sgn in (-1, 1):
    pts = [(X_P + sgn * RR_C * R_C * (i / 10), -0.32, HP_C * (1 - (i / 10) ** 2) + 0.06) for i in range(11)]
    pts += [(X_P + sgn * R_C * 0.93, -0.32, 0.45), (X_P + sgn * R_C * 1.005, -0.32, 1.6), (X_P + sgn * R_C * 1.005, -0.32, 5.0)]
    o, _ = tube(f"SpreadLine{sgn}", pts, 0.085, M_CYAN, seg=8); SP_LINES.append(o)
    windows(o, [(C["curved"], C["sediment"])])
glow(B_CYAN, [(C["curved"], 0.0), (C["spread"], 0.0), (C["spread"] + 0.4, 6.0), (C["sediment"], 6.0)])
CH_RING = torus("ChampRing", RR_C * R_C, 0.1, M_GOLD2, (X_P, 0, 0.05)); windows(CH_RING, [(C["evenly"], C["sediment"]), (C["punt"], C["back"])])

# ================= SET G: hand glassblowing (x 200) =================
G_Z = 20.0
GB_PIV = empty("BlowPivot", (X_G, 0, G_Z)); GB_PIV.rotation_euler = (0, math.radians(-90), 0)
pHotA, OA, IA = bprof(**P(STILL, hp=-1.3), pointy=True)
pHotB, _, _ = bprof(**STILL)
HOT = mesh_obj("HotBottle", lathe_bm(pHotA, seg=48), [M_HOT], GB_PIV); smooth(HOT)
HOT.shape_key_add(name="Basis"); SK = HOT.shape_key_add(name="Punt")
for v, co in zip(SK.data, lathe_coords(pHotB, seg=48)): v.co = co
HP_G = PW([(C["pushed"], -1.3), (C["up"] + 0.5, 2.0)])
for fr in range(F(C["pushed"]) - 1, F(C["up"] + 0.5) + 2):
    t = (fr - 1) / FPS; SK.value = (HP_G(t) + 1.3) / 3.3; SK.keyframe_insert("value", frame=fr)
bm = bmesh.new(); nub_bm(bm, (0, 0, 0), 0.32, seed=4); HOT_NUB = mesh_obj("HotNub", bm, [M_HOTCUT], HOT); smooth(HOT_NUB)
bake_loc(HOT_NUB, lambda t: (0.0, 0.0, HP_G(t) - 0.12))
bake_rot(HOT, lambda t: (0.0, 0.0, 0.6 * t))
bake_scale(HOT, lambda t: (0.55 + 0.45 * ease((t - C["back"]) / (C["hand"] + 0.3 - C["back"])),) * 3)
o = cyl("Blowpipe", 0.45, 34.0, "X", (X_G - 30.0 - 17.0, 0, G_Z), M_STEEL, seg=16)
o = cyl("BlowpipeCollar", 1.0, 2.0, "X", (X_G - 31.0, 0, G_Z), M_STEEL, seg=20)
ROD = mesh_obj("PushTool", bmesh.new(), [M_STEEL])
bm = bmesh.new(); add_cyl(bm, 0.38, 40.0, "X", (20.0 + 0.4, 0, 0), seg=16); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
bm.to_mesh(ROD.data); bm.free(); smooth(ROD)
def rod_x(t):
    if t < C["so"]: return X_G + 60.0
    x_c = X_G - (-1.3 - 0.44) + 0.5
    if t < C["pushed"]: return X_G + 60.0 + (x_c - X_G - 60.0) * ease((t - C["so"]) / (C["pushed"] - C["so"]))
    if t < C["into"] + 0.2: return X_G - (HP_G(t) - 0.44) + 0.5
    x_e = X_G - (2.0 - 0.44) + 0.5
    return x_e + 60.0 * ease((t - C["into"] - 0.2) / 1.2)
bake_loc(ROD, lambda t: (rod_x(t), 0.0, G_Z))
windows(ROD, [(C["so"], C["now"])])
FURN = cyl("Furnace", 16.0, 22.0, "Y", (X_G - 48.0, 46.0, 18.0), M_RUBBER, seg=40)
FMOUTH = cyl("FurnaceMouth", 7.0, 0.4, "Y", (X_G - 48.0, 34.8, 18.0), M_FURN, seg=40)
for att in ("visible_glossy", "visible_transmission"):
    try: setattr(FMOUTH, att, False)
    except Exception: pass
SP_EM = cyl("SparkEmitter", 1.0, 0.2, "X", (X_G + 2.2, 0, G_Z), None, seg=12); SP_EM.hide_render = True
fx.particles(SP_EM, "sparks", F(C["pushed"]), F(C["up"] + 0.4), count=90)
SP_EM2 = cyl("GlowEmitter", 2.5, 0.2, "Z", (X_G - 14.0, 0, G_Z - 3.5), None, seg=12); SP_EM2.hide_render = True
fx.particles(SP_EM2, "sparks", F(C["back"]), F(C["middle"]), count=40)

# ================= SET T: table (x 300) =================
TABLE = box("TableTop", X_T - 34, X_T + 34, -22, 26, -3.0, 0.0, M_WOOD)   # a wooden board flush with the studio floor
pPT, OPT, IPT = bprof(**P(STILL, hp=-1.3), pointy=True)
bm = lathe_bm(pPT, seg=40); nub_bm(bm, (0, 0, -1.30), 0.30, seed=9)
PT = mesh_obj("PointyBottle", bm, [M_GLASS]); smooth(PT)
T_DROP0, T_DROP1 = C["stand"], C["table"]
T_REL = C["wobbles"] - 0.15
PT_X = X_T - 12.0
def pt_z(t): return 1.62 + 12.0 * (1 - ease((t - T_DROP0) / (T_DROP1 - T_DROP0)))
bake_loc(PT, lambda t: (PT_X, 0.0, pt_z(t)))
bake_rot(PT, lambda t: (0.0, math.radians(9.0 * ease((t - T_DROP1) / (T_REL - T_DROP1))), 0.0))
TABLE_RB = box("TableRB", X_T - 34, X_T + 34, -22, 26, -3.0, 0.0, None); TABLE_RB.hide_render = True; TABLE_RB.display_type = "WIRE"
fx.rigid([PT], passive=[TABLE_RB], mass=0.5, friction=0.6, bounce=0.15)
try:
    rb = PT.rigid_body; rb.collision_margin = 0.01
    rb.kinematic = True; PT.keyframe_insert("rigid_body.kinematic", frame=1); PT.keyframe_insert("rigid_body.kinematic", frame=F(T_REL))
    rb.kinematic = False; PT.keyframe_insert("rigid_body.kinematic", frame=F(T_REL) + 1)
except Exception as e: print("[build] pointy kinematic skipped", e)
windows_r(PT, [(C["stand"], C["so"])])
try:
    rw = scene.rigidbody_world; rw.substeps_per_frame = 20; rw.solver_iterations = 20
except Exception as e: print("[build] rigid world tune skipped", e)
DUST_EM = box("DustEmitter", X_T - 10, X_T + 20, -3, 3, 0.0, 0.05, None); DUST_EM.hide_render = True
fx.particles(DUST_EM, "dust", F(T_REL + 0.45), F(T_REL + 0.9), count=120)
# the fixed bottle: half cut, punt up, rests on the gold ring, the rough nub tucked at the top of the dent
pPU, OPU, IPU = bprof(**STILL)
PU_X = X_T + 10.0
PU = half("PuntBottle", pPU, [M_GLASS, M_CUT], loc=(PU_X, 0, 0))
bm = bmesh.new(); nub_bm(bm, (0, 0, STILL["hp"] - 0.12), 0.30, seed=4); PU_NUB = mesh_obj("PuntNub", bm, [M_CUT], PU); smooth(PU_NUB)
bake_loc(PU, lambda t: (PU_X, 0.0, 9.0 * (1 - ease((t - C["now"]) / 0.55))))
windows(PU, [(C["now"], C["today"])])
PU_RING = torus("PuntRing", STILL["rr"] * STILL["R"], 0.09, M_GOLD2, (0, 0, 0.04)); par(PU_RING, PU)
windows(PU_RING, [(C["level"], C["today"])])
pts = [(STILL["rr"] * STILL["R"] * (i / 10 * 2 - 1), -0.25, STILL["hp"] * (1 - (i / 10 * 2 - 1) ** 2) + 0.03) for i in range(11)]
ARCH, _ = tube("ArchLine", pts, 0.07, M_CYAN2, seg=8); par(ARCH, PU); ARCH.location = (0, 0, 0)
windows(ARCH, [(C["it"], C["today"])])
glow(B_CYAN2, [(C["it"], 0.0), (C["stronger"], 6.0), (C["today"], 6.0)])
RED_RING = torus("SharpRing", 0.9, 0.07, M_RED, (0, 0, 0)); par(RED_RING, PT); RED_RING.location = (0, 0, -1.45)
glow(B_RED, [(C["sharp"], 0.0), (C["sharp"] + 0.2, 6.0), (C["so"], 6.0), (C["so"] + 0.01, 0.0), (C["rough"], 0.0), (C["seam"], 6.0), (C["stand"] - 0.05, 6.0), (C["stand"], 0.0)])
RED_RING2 = torus("SeamRing", 0.9, 0.07, M_RED, (0, 0, 0)); par(RED_RING2, GB_PIV); RED_RING2.location = (0, 0, -1.45)
windows(RED_RING2, [(C["rough"], C["stand"])])
windows(RED_RING, [(C["sharp"], C["so"])])

# ================= SET M: machine mold + cooling floor (x 400) =================
pMB, OMB, IMB = bprof(**STILL)
M_Z = 0.8
RM = 7.5
mold_prof = OMB[:] + [(STILL["nr"] + 0.18, STILL["H"] - 1.1), (STILL["nr"] + 0.18, STILL["H"]), (RM, STILL["H"]), (RM, -M_Z), (0.003, -M_Z)]
MOLD = half("Mold", mold_prof, [M_STEEL, M_MOLDCUT], loc=(X_M, 0, M_Z), seg=48)
torus("MoldFunnel", 2.6, 0.5, M_STEEL, (X_M, 0, M_Z + STILL["H"] + 0.6))
glow(B_MOLDCUT, [(C["drops"], 0.05), (C["mold"], 0.3), (C["all"] + 0.4, 0.3), (C["those"], 0.05)])
B_MOLDCUT.inputs["Emission Strength"].default_value = 0.3
GOB = obj_from("Gob", sphere_mesh("GobMe", 1.0, 3), M_HOT); GOB.scale = (1.45, 1.45, 2.4)
T_G0, T_G1 = C["drops"], C["mold"] + 0.05
def gob_z(t):
    if t < T_G0: return 41.0 + 0.3 * math.sin(4 * t)
    p = lin((t - T_G0) / (T_G1 - T_G0)); return 41.0 + (M_Z + STILL["hp"] + 2.4 + 0.1 - 41.0) * p * p
bake_loc(GOB, lambda t: (X_M, 0.0, gob_z(t)))
bake_scale(GOB, lambda t: (1.45 + 0.35 * ease((t - T_G1) / 0.25), 1.45 + 0.35 * ease((t - T_G1) / 0.25), 2.4 - 0.5 * ease((t - T_G1) / 0.25)))
windows(GOB, [(C["glob"] - 0.2, C["air"])])
pPar, _, _ = bprof(R=2.3, H=11.5, th=0.9, thb=1.0, hp=0.3, rr=0.8, bt=5.0, nr=1.45, nz=8.5)
PAR = mesh_obj("Parison", lathe_bm(pPar, ang=math.pi, seg=40), [M_HOT, M_HOTCUT]); smooth(PAR); PAR.location = (X_M, 0, M_Z)
PAR.shape_key_add(name="Basis"); SKP = PAR.shape_key_add(name="Blown")
for v, co in zip(SKP.data, lathe_coords(pMB, ang=math.pi, seg=40)): v.co = co
for fr in range(F(C["air"]) - 1, F(C["shape"] + 0.3) + 2):
    t = (fr - 1) / FPS; SKP.value = ease((t - C["air"]) / (C["shape"] + 0.3 - C["air"])); SKP.keyframe_insert("value", frame=fr)
windows(PAR, [(C["air"], C["those"])])
air_spec = [((X_M, M_Z + STILL["H"] + 6.5 - k * 3.0), (0, -1), 2.0, 1.1) for k in range(3)]
AIR = arrows_obj("AirArrows", air_spec, M_CYANA, y=-2.2)
windows(AIR, [(C["air"], C["shape"] + 0.6)])
glow(B_CYANA, [(C["air"] - 0.01, 0.0), (C["air"] + 0.2, 6.0), (C["shape"] + 0.6, 6.0), (C["shape"] + 0.61, 0.0)])
# Mantaflow: the glowing gob dropping into the mold (laptop --bake-fluid; hidden without the cache)
FL_DOM = box("FluidDomain", X_M - 2.9, X_M + 2.9, -2.9, 2.9, M_Z + STILL["hp"] + 0.4, M_Z + 30.0, None); FL_DOM.display_type = "WIRE"
FL_IN = obj_from("FluidInflow", sphere_mesh("FluidInMe", 1.1, 2), None, (X_M, 0, M_Z + 27.5)); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=64, start=F(C["drops"]), end=F(C["air"] + 0.2), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_DOM.data.materials.append(M_HOT)
windows(FL_DOM, [(C["drops"], C["air"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True
# cooling floor with many finished bottles (GN scatter)
BELT = box("CoolingBelt", X_M + 50, X_M + 130, -30, 30, 0.0, 0.25, M_BELT)
pInst, _, _ = bprof(**STILL)
INST = mesh_obj("BottleInst", lathe_bm(pInst, seg=20), [M_GLASS]); smooth(INST)
bm = bmesh.new(); vs_ = [bm.verts.new(v) for v in ((X_M + 52, -28, 0.26), (X_M + 128, -28, 0.26), (X_M + 128, 28, 0.26), (X_M + 52, 28, 0.26))]; bm.faces.new(vs_)
BELT_TOP = mesh_obj("CoolingBeltTop", bm, [M_BELT])
fx.scatter(BELT_TOP, INST, density=0.003, scale_min=0.96, scale_max=1.04, seed=11)
_ = box("BeltRailA", X_M + 50, X_M + 130, -31.5, -30, 0.0, 2.0, M_STEEL); _ = box("BeltRailB", X_M + 50, X_M + 130, 30, 31.5, 0.0, 2.0, M_STEEL)

# ================= SET S: shallow vs deep punt (x 620) =================
SH = P(STILL, hp=0.9); DP = P(STILL, hp=4.2, thb=1.1)
pSH, OSH, ISH = bprof(**SH); pDP, ODP, IDP = bprof(**DP)
half("Shallow", pSH, [M_GLASS, M_CUT], loc=(X_S - 7.5, 0, 0)); half("ShallowWine", region_below(ISH, 21.0), [M_WINE, M_WINE], loc=(X_S - 7.5, 0, 0))
half("Deep", pDP, [M_GLASS, M_CUT], loc=(X_S + 7.5, 0, 0)); half("DeepWine", region_below(IDP, 21.0), [M_WINE, M_WINE], loc=(X_S + 7.5, 0, 0))
for nm, xx in (("ShallowCaps", X_S - 7.5), ("DeepCaps", X_S + 7.5)):
    half(nm, [(0.003, 30.05), (1.66, 30.05), (1.66, 26.0), (1.50, 26.0), (1.50, 29.9), (0.003, 29.9)], [M_CAPS, M_CAPS], loc=(xx, 0, 0))
XG = half("DeepExtraGlass", base_glass(ODP, IDP), [M_GOLDX, M_GOLDX], loc=(X_S + 7.5, -0.03, 0)); XG.scale = (1.004, 1.0, 1.004)
windows(XG, [(C["mostly"], C["have"])])
glow(B_GOLDX, [(C["mostly"], 0.0), (C["more"], 5.0), (C["have"], 5.0)])
r_in = DP["rr"] * DP["R"] * 0.92; r_out = DP["R"] - DP["th"] - 0.15
r_in = 2.95; SEDS = half("SedimentBed", [(r_in, 1.35), (r_out, 1.35), (r_out, 1.42), (r_in, 1.42)], [M_WINE, M_WINE], loc=(X_S + 7.5, 0, 0), seg=24)
SED_I = obj_from("SedimentSpeck", sphere_mesh("SedMe", 0.11, 1), M_SED)
fx.scatter(SEDS, SED_I, density=30.0, scale_min=0.6, scale_max=1.5, seed=5)
windows(SEDS, [(C["sediment"], C["deeper"])])
Q_RING = torus("UnprovenRing", 1.4, 0.08, M_RED, (X_S + 7.5 - 2.9, -0.4, 1.2)); Q_RING.rotation_euler = (math.radians(90), 0, 0)
windows(Q_RING, [(C["nobody"], C["deeper"])])
glow(B_RED, [(C["nobody"], 0.0), (C["nobody"] + 0.2, 6.0), (C["deeper"], 6.0), (C["deeper"] + 0.01, 0.0)])

# ================= lights + world =================
fx.hdri("studio", strength=0.30, rotation_deg=30.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; return o, d_
def aim(o, target):
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
for X, zc in ((X_H, 12), (X_P, 14), (X_G, 20), (X_T, 10), (X_M, 15), (X_M + 90, 5), (X_S, 12)):
    for nm, dl, size, en, rgb in [("Key", (-35, -55, 50), 40, 1.4e4, (1.0, 0.93, 0.85)), ("Fill", (45, -40, 12), 40, 3.0e3, (0.75, 0.82, 1.0)),
                                  ("Rim", (40, 45, 35), 30, 7.0e3, (0.6, 0.75, 1.0)), ("RimL", (-40, 45, 25), 30, 5.0e3, (1.0, 0.85, 0.7))]:
        o, _ = area(f"{nm}{int(X)}", (X + dl[0], dl[1], zc + dl[2]), size, en, rgb); aim(o, (X, 0, zc))
    o, _ = area(f"BackGlow{int(X)}", (X, 30, zc + 5), 50, 4.0e3, (0.55, 0.65, 0.85)); aim(o, (X, 72, zc + 8))
    for att in ("visible_glossy", "visible_transmission", "visible_diffuse"):
        try: setattr(o, att, False)
        except Exception: pass

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (7.0, -40.0, 6.0), (1.0, -3.0, 15.5), 36),                                   # hook: bottle tipped, the dent faces us, gold ring
    (C["but"] - 0.05, (6.0, -38.0, 5.5), (1.0, -4.0, 15.0), 36),
    (C["but"], (X_P + 7.0, -46.0, 17.0), (X_P + 1.5, 0.0, 15.0), 38, "cut"),            # stake: champagne cutaway, arrows under pressure
    (C["inch"], (X_P + 5.0, -34.0, 10.0), (X_P + 1.0, 0.0, 9.0), 40),
    (C["thats"], (X_P + 12.0, -74.0, 14.0), (X_P + 12.0, 0.0, 12.0), 40, "cut"),       # vs a car tire
    (C["its"] - 0.05, (X_P + 12.0, -68.0, 13.0), (X_P + 12.0, 0.0, 11.0), 40),
    (C["its"], (X_P + 6.0, -21.0, 5.5), (X_P, 0.0, 2.6), 40, "cut"),                   # "It's called a punt"
    (C["back"] - 0.05, (X_P + 4.0, -18.0, 4.5), (X_P, 0.0, 2.6), 42),
    (C["back"], (X_G + 22.0, -36.0, 30.0), (X_G - 12.0, 0.0, 20.0), 32, "cut"),         # hand glassblowing
    (C["bottom2"] - 0.05, (X_G + 18.0, -32.0, 27.0), (X_G - 9.0, 0.0, 20.0), 34),
    (C["bottom2"], (X_G + 13.0, -15.0, 24.0), (X_G + 0.5, 0.0, 20.0), 42, "cut"),        # rough seam
    (C["stand"] - 0.05, (X_G + 12.0, -13.0, 23.0), (X_G + 0.5, 0.0, 20.0), 44),
    (C["stand"], (X_T - 8.0, -68.0, 20.0), (X_T - 8.0, 0.0, 13.0), 36, "cut"),           # table: it wobbles and falls, sharp point
    (C["sharp"], (X_T - 4.0, -30.0, 5.0), (X_T - 11.0, 0.0, 2.0), 38, "cut"),
    (C["so"] - 0.05, (X_T - 5.0, -27.0, 4.5), (X_T - 11.0, 0.0, 2.0), 40),
    (C["so"], (X_G + 16.0, -22.0, 25.0), (X_G - 3.0, 0.0, 20.0), 38, "cut"),             # push the seam up
    (C["into"], (X_G + 13.0, -18.0, 23.0), (X_G - 2.0, 0.0, 20.0), 40),
    (C["now"], (PU_X + 3.0, -40.0, 12.0), (PU_X, 0.0, 10.0), 38, "cut"),                # stands level on a smooth ring
    (C["ring"], (PU_X + 6.0, -24.0, 3.5), (PU_X, 0.0, 1.8), 42),
    (C["it"], (PU_X - 4.0, -22.0, 4.5), (PU_X, 0.0, 2.0), 42),
    (C["today"] - 0.05, (PU_X - 5.0, -21.0, 5.0), (PU_X, 0.0, 2.0), 42),
    (C["today"], (X_M + 10.0, -62.0, 30.0), (X_M, 0.0, 22.0), 36, "cut"),               # machine: gob drops into the mold
    (C["air"], (X_M + 6.0, -48.0, 20.0), (X_M, 0.0, 16.0), 38),
    (C["dent3"], (X_M + 5.0, -20.0, 4.5), (X_M, 0.0, 2.6), 42, "cut"),                 # dent and all
    (C["those"] - 0.05, (X_M + 4.0, -18.0, 4.0), (X_M, 0.0, 2.6), 42),
    (C["those"], (X_M + 62.0, -70.0, 60.0), (X_M + 92.0, 0.0, 2.0), 34, "cut"),         # cooling floor, many bottles
    (C["sparkling"] - 0.05, (X_M + 78.0, -62.0, 50.0), (X_M + 94.0, 0.0, 2.0), 34),
    (C["sparkling"], (X_P + 8.0, -50.0, 20.0), (X_P + 1.0, 0.0, 15.0), 38, "cut"),     # champagne: gas pushes on every inch
    (C["curved"] - 0.05, (X_P + 5.0, -40.0, 16.0), (X_P + 1.0, 0.0, 13.0), 38),
    (C["curved"], (X_P + 5.0, -19.0, 5.0), (X_P, 0.0, 2.5), 40, "cut"),                 # the dome spreads the push
    (C["sediment"] - 0.05, (X_P - 2.0, -18.0, 4.0), (X_P, 0.0, 2.5), 40),
    (C["sediment"], (X_S + 12.0, -22.0, 7.0), (X_S + 7.5, 0.0, 3.0), 42, "cut"),        # the sediment story
    (C["deeper"] - 0.05, (X_S + 11.0, -20.0, 6.0), (X_S + 7.5, 0.0, 3.0), 42),
    (C["deeper"], (X_S + 2.0, -66.0, 17.0), (X_S, 0.0, 13.0), 38, "cut"),               # shallow vs deep
    (C["mostly"], (X_S + 5.0, -36.0, 6.0), (X_S + 3.0, 0.0, 3.5), 40),
    (C["have"] - 0.05, (X_S + 6.0, -33.0, 5.5), (X_S + 3.0, 0.0, 3.5), 40),
    (C["have"], (6.0, -38.0, 5.5), (1.0, -4.0, 15.0), 36, "cut"),                       # CTA: the bottom of the bottle, slow pull-out
    (DUR, (10.0, -54.0, 8.0), (1.0, -2.0, 16.0), 34),
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
scene.cycles.max_bounces = 8; scene.cycles.transmission_bounces = 8; scene.cycles.transparent_max_bounces = 12; scene.cycles.volume_bounces = 0
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
fx.bake_rigid(F(C["stand"]) - 1, F(C["so"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "hook_punt": W(HOOK_B, (0, 0, STILL["hp"])), "champ_punt": (X_P, 0.0, HP_C), "champ_wall": (X_P + R_C, 0.0, 12.0),
    "cork": (X_P, 0.0, H_C + 2.3), "tire": (X_P + 23.0, 0.0, 8.4 + 8.4), "seam": W(HOT_NUB), "point": W(PT, (0, 0, -1.45)),
    "ring": W(PU, (-STILL["rr"] * STILL["R"], 0, 0.0)), "tucked": W(PU, (0, 0, STILL["hp"])), "gob": W(GOB), "mold": (X_M + RM, 0.0, 18.0),
    "mold_dent": (X_M, 0.0, M_Z + STILL["hp"]), "deep": (X_S + 7.5, 0.0, DP["hp"]), "shallow": (X_S - 7.5, 0.0, SH["hp"]),
    "sediment": (X_S + 7.5 - 3.1, 0.0, 1.4), "dome": (X_P + RR_C * R_C * 0.5, 0.0, HP_C * 0.75),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4], "press": [RR(a, b) for a, b in PRESS_W], "tire": RR(*TIRE_W[0]),
          "bubbles": [RR(a, b) for a, b in BUB_W], "inflate": RR(C["back"], C["hand"] + 0.3), "drop_bottle": RR(T_DROP0, T_DROP1),
          "release": round(T_REL, 3), "topple": round(T_REL + 0.55, 3), "push": RR(C["pushed"], C["up"] + 0.5), "rod_in": RR(C["so"], C["pushed"]),
          "rod_out": RR(C["into"] + 0.2, C["into"] + 1.4), "punt_drop": RR(C["now"], C["now"] + 0.55), "ring_glow": round(C["level"], 3),
          "arch": round(C["stronger"], 3), "gob_show": round(C["glob"] - 0.2, 3), "gob_drop": RR(T_G0, T_G1), "blow": RR(C["air"], C["shape"] + 0.3),
          "spread": round(C["spread"], 3), "sediment": round(C["sediment"], 3), "extra_glass": round(C["more"], 3), "hook_ring": round(C["dent"], 3),
          "cta_ring": round(C["bottom3"], 3)}
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
