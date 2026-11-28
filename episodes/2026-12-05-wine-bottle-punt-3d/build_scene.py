# Wine bottle punt (3d-41): "The dent in the bottom of a wine bottle has nothing to do with how good the wine is."
# Stake: in a bottle of bubbly it helps keep the glass from bursting. Hand-blown bottles had a rough seam / sharp point in the middle of
# the base -> wobbles; glassblowers pushed it up -> stands on a smooth ring, rough part out of the way, dome may add strength. Machines
# today -> mostly tradition for still wine, some bottles have none. Sparkling: ~5-6 atm, ~3x a car tire; a flat bottom is a weak spot,
# the dome helps spread the pressure; champagne bottles use thicker, heavier glass. Deeper dent != better wine (Wine Spectator), sediment
# idea unproven. Illustrative, 1 unit = 1 cm. Generic bottles, no labels, no brand, no text, no people (no hands).
# Sets along X: S1 studio table x=0 | S2 glass shop x=200 | S3 machine line x=400 | S4 champagne x=600 | S5 flat-bottom failure x=800 |
#               S6 wall compare x=1000 | S7 myth/sediment x=1200. Section plane y = 0 (the y >= 0 half is kept, the camera sits at -Y).
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
random.seed(41)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("dent","dent"),("bottom","bottom"),("nothing","nothing"),("good","good"),("but","But"),("bubbly","bubbly,"),("keep","keep"),
  ("bursting","bursting."),("called","called"),("punt","punt."),("back","Back"),("blown","blown"),("hand","hand,"),("base","base"),
  ("rough","rough"),("seam","seam,"),("sharp","sharp"),("point","point"),("middle","middle."),("wobbles","wobbles."),("so","So"),
  ("pushed","pushed"),("up","up,"),("now","Now"),("stands","stands"),("ring","ring"),("rough2","rough"),("way","way."),("dome","dome"),
  ("stronger","stronger,"),("today","Today,"),("machines","machines"),("tougher","tougher,"),("still","still"),("tradition","tradition."),
  ("some","Some"),("dont","don't"),("one","one."),("sparkling","Sparkling"),("different","different."),("inside","Inside"),
  ("champagne","champagne,"),("gas","gas"),("five","five"),("atmospheres","atmospheres."),("thats","That's"),("three","three"),
  ("car","car"),("tire","tire."),("under","Under"),("flat","flat"),("weak","weak"),("spot","spot."),("dome2","dome"),("spread","spread"),
  ("out","out."),("thats2","That's"),("champagne2","champagne"),("thicker","thicker,"),("glass","glass."),("so2","So"),("deeper","deeper"),
  ("better","better"),("wine2","wine?"),("spectator","Spectator"),("no","no."),("gimmick","gimmick."),("idea","idea"),("sediment","sediment?"),
  ("nobody","Nobody"),("proven","proven"),("have","Have"),("noticed","noticed"),("bottle9","bottle?"),("tell","Tell"),("comments","comments.")]
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
CL = coll("Bottle")
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
GOLD, CYAN, RED, ORANGE = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.15)
X1, X2, X3, X4, X5, X6, X7 = 0.0, 200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0

# ---------- bottle profiles (r, z), base ring at z = 0 ----------
def dome_f(u, hp):
    """underside height at fraction u (0 = axis, 1 = inner edge of the standing ring); hp < 0 = a hand-blown point."""
    u = max(0.0, min(1.0, u))
    if hp >= 0: return hp * (1 - u * u) ** 0.9
    return hp * (1 - u) ** 2.2
def bottle_prof(R=3.7, H=30.0, t=0.32, hp=2.2, neck=1.45, lip=1.68, ring=0.75, heel=1.1, nd=14):
    Hs, Hn = 0.60 * H, 0.77 * H
    ri = R - ring
    out = [(0.04 + (ri - 0.04) * (i / nd), dome_f(i / nd, hp)) for i in range(nd + 1)]
    out += [(R - 0.42, 0.0)]
    for k in range(1, 7):                       # heel arc
        a = (math.pi / 2) * k / 6; out.append((R - 0.42 + 0.42 * math.sin(a), heel * (1 - math.cos(a))))
    out += [(R, Hs)]
    for k in range(1, 9):                       # shoulder
        u = k / 8; s = ease(u); out.append((R + (neck - R) * s, Hs + (Hn - Hs) * u))
    out += [(neck, H - 1.3), (lip, H - 1.2), (lip, H), (neck - 0.5, H)]
    inn = [(neck - 0.5, Hn + 0.2)]
    for k in range(7, 0, -1):
        u = k / 8; s = ease(u); inn.append((R - t + (neck - 0.5 - (R - t)) * s, Hs + (Hn - Hs) * u))
    inn += [(R - t, Hs), (R - t, heel + t)]
    for k in range(5, 0, -1):
        a = (math.pi / 2) * k / 6; inn.append((R - t - 0.5 + 0.5 * math.sin(a), t + heel * 0.6 * (1 - math.cos(a))))
    inn += [(ri - 0.05, t * 0.9 + dome_f(1.0, hp))]
    inn += [(0.04 + (ri - 0.09) * (i / nd), t + dome_f(i / nd, hp)) for i in range(nd - 1, -1, -1)]
    return out + inn
def liquid_prof(R, t, hp, fill, ring=0.75, nd=14, gap=0.05):
    ri = R - ring
    pts = [(0.04 + (ri - 0.09) * (i / nd), t + gap + dome_f(i / nd, hp)) for i in range(nd + 1)]
    pts += [(R - t - 0.5, t + gap + 0.15), (R - t - gap, t + 0.7), (R - t - gap, fill), (0.04, fill)]
    return pts
def lathe_bm(prof, a0=0.0, ang=math.pi, seg=48):
    bm = bmesh.new()
    vs = [bm.verts.new((r * math.cos(a0), r * math.sin(a0), z)) for r, z in prof]
    f = bm.faces.new(vs)
    bmesh.ops.spin(bm, geom=vs + list(f.edges) + [f], cent=(0, 0, 0), axis=(0, 0, 1), angle=ang, steps=seg, use_duplicate=False)
    if ang >= 2 * math.pi - 1e-6:
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        for f_ in [f_ for f_ in bm.faces if abs(f_.normal.y) > 0.999 and abs(f_.calc_center_median().y) < 1e-4]: bm.faces.remove(f_)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f_ in bm.faces:                         # the section caps (plane y = 0) get material slot 1
        if abs(f_.normal.y) > 0.99 and abs(f_.calc_center_median().y) < 1e-3: f_.material_index = 1
    return bm
def lathe_obj(name, prof, mats, loc=(0, 0, 0), ang=math.pi, seg=48, keys=()):
    """keys: [(name, prof)] shape keys with the same topology"""
    o = mesh_obj(name, lathe_bm(prof, ang=ang, seg=seg), mats); o.location = loc
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(50))
    except Exception: pass
    if keys:
        o.shape_key_add(name="Basis")
        for kn, kp in keys:
            bm2 = lathe_bm(kp, ang=ang, seg=seg); bm2.verts.ensure_lookup_table()
            sk = o.shape_key_add(name=kn)
            assert len(bm2.verts) == len(sk.data), (name, kn)
            for i, v in enumerate(bm2.verts): sk.data[i].co = v.co
            bm2.free()
    return o
def sk_bake(o, kname, fn):
    bake_scalar(o.data.shape_keys, f'key_blocks["{kname}"].value', [fn(t) for t in TS])

# ---------- materials ----------
def glass_mat(name, rgb, emit=(1.0, 0.45, 0.12)):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.06
    b.inputs["Transmission Weight"].default_value = 0.92; b.inputs["IOR"].default_value = 1.5
    b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = 0.0
    try: b.inputs["Coat Weight"].default_value = 0.3
    except Exception: pass
    return m, b
M_GREEN, B_GREEN = glass_mat("GreenGlass", (0.10, 0.42, 0.14))
M_CLEAR, B_CLEAR = glass_mat("ChampGlass", (0.12, 0.36, 0.16))
M_HOT, B_HOT = glass_mat("HotGlass", (0.10, 0.40, 0.14), emit=(1.0, 0.42, 0.10))
glow(B_HOT, [(0, 1.1), (C["now"], 1.1), (C["dome"], 0.0)])
def sec_mat(name, rgb=ORANGE, e=0.35):
    m, b = mat(name, rgb, rough=0.35, emit_rgb=rgb); b.inputs["Emission Strength"].default_value = e; return m, b
M_SEC, B_SEC = sec_mat("GlassSection", (1.0, 0.52, 0.18), 0.25)
M_SEC_HOT, B_SEC_HOT = sec_mat("HotSection", (1.0, 0.62, 0.22), 1.2)
glow(B_SEC_HOT, [(0, 1.6), (C["now"], 1.6), (C["dome"], 0.3)])
M_SEC_F, B_SEC_F = sec_mat("FlatSection", (1.0, 0.52, 0.18), 0.25)
M_CHAMP, B_CHAMP, _ = water_sec("Champagne", glow_rgb=(1.0, 0.82, 0.35), vol_rgb=(0.85, 0.62, 0.20), dens=0.06)
bsdf_of(M_CHAMP).inputs["Base Color"].default_value = (1.0, 0.86, 0.45, 1)
M_RED, B_REDW, _ = water_sec("RedWine", glow_rgb=(0.8, 0.1, 0.15), vol_rgb=(0.55, 0.04, 0.08), dens=0.35)
bsdf_of(M_RED).inputs["Base Color"].default_value = (0.6, 0.05, 0.1, 1)
M_WOOD, _ = mat("Wood", (0.30, 0.17, 0.08), rough=0.55, noise=6.0)
M_STUDIO, _ = mat("StudioFloor", (0.035, 0.038, 0.045), rough=0.45)
M_BACK, _ = mat("Backdrop", (0.02, 0.025, 0.035), rough=0.8)
M_STEEL, _ = mat("Steel", (0.62, 0.63, 0.66), rough=0.28, metallic=1.0)
M_DSTEEL, _ = mat("DarkSteel", (0.18, 0.19, 0.21), rough=0.4, metallic=1.0)
M_RUBBER, _ = mat("Rubber", (0.025, 0.025, 0.028), rough=0.7)
M_CORK, _ = mat("Cork", (0.55, 0.38, 0.22), rough=0.8, noise=18.0)
M_FOIL, _ = mat("Foil", (0.75, 0.6, 0.25), rough=0.3, metallic=1.0)
M_GOLDE, B_GOLDE = emit_mat("GoldGlow", GOLD, 0.0)
M_CYANE, B_CYANE = emit_mat("CyanGlow", CYAN, 0.0)
M_REDE, B_REDE = emit_mat("RedGlow", RED, 0.0)
M_REDP, B_REDP = emit_mat("RedPressure", RED, 0.0)
M_DOT, B_DOT = emit_mat("RoughDot", RED, 0.0)
M_BUB, _ = emit_mat("Bubble", (1.0, 0.97, 0.85), 1.6)
M_SED, _ = mat("Sediment", (0.12, 0.04, 0.03), rough=0.9)
M_FURN, B_FURN = emit_mat("Furnace", (1.0, 0.42, 0.1), 6.0)

# ---------- studio sets: floor + backdrop per set ----------
for nm, x in (("S1", X1 + 30), ("S2", X2 + 15), ("S3", X3), ("S4", X4 + 15), ("S5", X5), ("S6", X6), ("S7", X7)):
    box(f"Floor{nm}", x - 95, x + 95, -120, 90, -62.0, -60.0, M_STUDIO)
    box(f"Back{nm}", x - 95, x + 95, 60, 62, -60, 120, M_BACK)

# ================= S1 studio table: the hook bottle + the "punt" section =================
box("Table", X1 - 70, X1 + 100, -40, 40, -4.0, 0.0, M_WOOD)
WINE = dict(R=3.7, H=30.0, t=0.32, hp=2.4)
HOOK_P = empty("HookPivot", (X1, 0, 15.0))
HOOK = lathe_obj("HookBottle", bottle_prof(**WINE), [M_GREEN, M_SEC], ang=2 * math.pi, seg=56)
par(HOOK, HOOK_P); HOOK.location = (0, 0, -15.0)
M_HRING, _ = emit_mat("HookRingGlow", GOLD, 2.5)
HRING = torus("HookRing", 3.7 - 0.5, 0.1, M_HRING, (0, 0, 0.02), segU=56, segV=8); par(HRING, HOOK_P); HRING.location = (0, 0, -15.0 + 0.02)
T_FLIP = 1.5
def hook_rot(t):
    p = ease(t / T_FLIP); return (math.radians(-68) * p, 0.0, math.radians(6) * p + 0.012 * min(t, 5.0))
def hook_loc(t): return (X1, 0.0, 15.0 + 7.0 * ease(t / T_FLIP))
bake_rot(HOOK_P, hook_rot); bake_loc(HOOK_P, hook_loc)
PUNT_X = X1 + 60
PUNT_SEC = lathe_obj("PuntSection", bottle_prof(**WINE), [M_GREEN, M_SEC], (PUNT_X, 0, 0))
lathe_obj("PuntSectionWine", liquid_prof(3.7, 0.32, 2.4, 22.0), [M_RED, M_RED], (PUNT_X, 0, 0))

# ================= S2 glass shop: hand-blown bottle, sharp point, wobble, pushed up =================
box("Marver", X2 - 25, X2 + 18, -14, 14, -3.0, 0.0, M_STEEL)
box("MarverStand", X2 - 20, X2 + 13, -10, 10, -60, -3.0, M_DSTEEL)
FURN = box("FurnaceMouth", X2 - 60, X2 - 20, 55, 58, 5, 40, M_FURN)
NUB = -0.9
HOT_PIV = empty("HotPivot", (X2, 0, 0))
HOT = lathe_obj("HotBottle", bottle_prof(R=3.7, H=30.0, t=0.4, hp=NUB), [M_HOT, M_SEC_HOT], keys=[("Punt", bottle_prof(R=3.7, H=30.0, t=0.4, hp=2.2))])
par(HOT, HOT_PIV)
PIPE = cyl("Blowpipe", 0.55, 70.0, "Z", (0, 0, 30.0 + 35.0), M_STEEL); par(PIPE, HOT_PIV)
cyl("BlowpipeCollar", 1.1, 1.6, "Z", (0, 0, 30.6), M_DSTEEL).parent = HOT_PIV
X_PUSH = X2 + 32
T_DOWN0, T_DOWN1 = C["wobbles"] - 1.0, C["wobbles"] - 0.45
T_LIFT0, T_LIFT1 = C["so"] - 0.1, C["pushed"] - 0.2
T_PUSH0, T_PUSH1 = C["pushed"] + 0.1, C["up"] + 0.35
T_BACK0, T_BACK1 = C["now"] - 0.15, C["stands"] + 0.25
def punt_k(t): return ease((t - T_PUSH0) / (T_PUSH1 - T_PUSH0))
def hot_xz(t):
    if t < T_DOWN0: return X2, 12.0 + 0.3 * math.sin(1.3 * t)
    if t < T_LIFT0: return X2, 12.0 + (-NUB - 12.0) * ease((t - T_DOWN0) / (T_DOWN1 - T_DOWN0))
    if t < T_BACK0:
        u = ease((t - T_LIFT0) / (T_LIFT1 - T_LIFT0)); return X2 + (X_PUSH - X2) * u, -NUB + (12.0 + NUB) * u
    u = ease((t - T_BACK0) / (T_BACK1 - T_BACK0)); return X_PUSH + (X2 - X_PUSH) * u, 12.0 * (1 - u)
def hot_tilt(t):
    if T_DOWN1 <= t < T_LIFT0: return math.radians(7.0) * math.sin(2 * math.pi * 1.5 * (t - T_DOWN1)) * min(1.0, (t - T_DOWN1) / 0.2)
    return 0.0
bake_loc(HOT_PIV, lambda t: (hot_xz(t)[0], 0.0, hot_xz(t)[1] + (NUB if T_DOWN0 <= t < T_LIFT0 else 0.0) * ease((t - T_DOWN0) / 0.55)))
# pivot = nub tip while it rocks on the marver: the bottle sits -NUB above the pivot
bake_loc(HOT, lambda t: (0.0, 0.0, (-NUB) * ease((t - T_DOWN0) / 0.55) if T_DOWN0 <= t < T_LIFT0 else 0.0))
bake_rot(HOT_PIV, lambda t: (0.0, hot_tilt(t), 0.0))
sk_bake(HOT, "Punt", punt_k)
# the pushing rod (steel, from below), tip follows the base apex
ROD = cyl("PuntRod", 0.7, 40.0, "Z", (0, 0, -20.0), M_STEEL)
cyl("PuntRodTip", 1.0, 0.6, "Z", (0, 0, -0.3), M_DSTEEL).parent = ROD; ROD.children[0].matrix_parent_inverse = Matrix.Identity(4)
def rod_z(t):
    apex = 12.0 + NUB + (2.2 - NUB) * punt_k(t) + 0.4 - 0.4
    if t < T_PUSH0 - 0.5: return -70.0
    if t < T_PUSH0: return -70.0 + (apex + 70.0) * ease((t - (T_PUSH0 - 0.5)) / 0.5)
    if t < T_PUSH1 + 0.1: return apex
    return apex - 80.0 * ease((t - T_PUSH1 - 0.1) / 0.7)
bake_loc(ROD, lambda t: (X_PUSH, 0.0, rod_z(t)))
windows(ROD, [(T_PUSH0 - 0.55, T_PUSH1 + 0.9)])
# standing ring glow (gold), rough spot (red dot at the apex), dome strength arc (cyan)
RING = torus("RingGlow", 3.7 - 0.55, 0.16, M_GOLDE, (0, 0, 0.05), segU=48, segV=8); par(RING, HOT_PIV)
glow(B_GOLDE, [(0, 0.0), (C["ring"] - 0.1, 0.0), (C["ring"] + 0.2, 6.0), (C["rough2"] - 0.1, 6.0), (C["way"] + 0.3, 1.2), (C["today"], 1.2)])
windows(RING, [(C["ring"] - 0.2, C["today"])])
DOT = obj_from("RoughDot", sphere_mesh("RoughDotMe", 0.35, 2), M_DOT, (0, -0.2, 2.2 + 0.2)); par(DOT, HOT_PIV); DOT.location = (0, -0.25, 2.2 + 0.25)
glow(B_DOT, [(0, 0.0), (C["rough2"] - 0.1, 0.0), (C["rough2"] + 0.15, 8.0), (C["dome"], 8.0), (C["dome"] + 0.4, 2.0)])
windows(DOT, [(C["rough2"] - 0.2, C["today"])])
arc = [Vector((x_, -0.12, 0.32 + 0.2 + dome_f(abs(x_) / (3.7 - 0.75), 2.2))) for x_ in [(-2.95 + 5.9 * i / 24) for i in range(25)]]
ARC, _ = tube("DomeArc", arc, 0.12, M_CYANE, seg=8); par(ARC, HOT_PIV)
glow(B_CYANE, [(0, 0.0), (C["dome"] - 0.05, 0.0), (C["dome"] + 0.3, 7.0), (C["today"] - 0.3, 7.0), (C["today"], 0.0),
               (C["dome2"] - 0.05, 0.0), (C["dome2"] + 0.3, 7.0), (C["thats2"], 7.0), (C["thats2"] + 0.1, 0.0)])
windows(ARC, [(C["dome"] - 0.1, C["today"])])
# glass-shop floor: scattered cullet (Geometry Nodes)
SHOP_FLOOR = box("ShopFloorScatter", X2 - 60, X2 + 70, -50, 40, -60.0, -59.99, M_STUDIO)
_cul = obj_from("Cullet", sphere_mesh("CulletMe", 0.9, 1), M_GREEN, (0, 0, -500))
fx.scatter(SHOP_FLOOR, _cul, density=0.02, scale_min=0.4, scale_max=1.4, seed=3)
# sparks off the hot glass at the collar while it is worked (particles)
SPK_EM = obj_from("SparkEmitter", sphere_mesh("SparkEmMe", 0.6, 1), None, (0, 0, 30.4)); par(SPK_EM, HOT_PIV); SPK_EM.hide_render = True
fx.particles(SPK_EM, "sparks", F(C["blown"] - 0.2), F(C["base"]), count=60)

# ================= S3 machine line: bottles today, and one with no punt =================
box("Belt", X3 - 75, X3 + 75, -6, 6, -2.0, 0.0, M_RUBBER)
box("BeltFrame", X3 - 75, X3 + 75, -7, 7, -6.0, -2.0, M_DSTEEL)
for i in range(16): cyl(f"Roller{i}", 0.9, 13.0, "Y", (X3 - 70 + i * 9.3, 0, -3.0), M_STEEL, seg=12)
box("MoldMachineL", X3 - 95, X3 - 62, -16, 16, -6, 48, M_DSTEEL); box("MoldHead", X3 - 64, X3 - 58, -10, 10, 30, 44, M_STEEL)
_mbm = lathe_bm(bottle_prof(**WINE), ang=2 * math.pi, seg=40); _mme = bpy.data.meshes.new("LineBottleMe"); _mbm.to_mesh(_mme); _mbm.free()
for i_m in (M_GREEN, M_SEC): _mme.materials.append(i_m)
try: _mme.shade_smooth()
except Exception: pass
SPD, LOOP = 9.0, 150.0
for i in range(8):
    o = obj_from(f"LineBottle{i}", _mme)
    bake_loc(o, lambda t, i=i: (X3 - 68 + ((i * LOOP / 8 + SPD * (t - C["today"])) % LOOP), 0.0, 0.0))
FLATB = dict(R=3.3, H=34.0, t=0.32, hp=0.12, neck=1.3, lip=1.5)
box("FlatPedestal", X3 + 12, X3 + 28, -24, -8, -60, -0.01, M_DSTEEL)
FLAT_P = empty("FlatPop", (X3 + 20, -16, 0))
FLAT_SEC = lathe_obj("FlatBottomSection", bottle_prof(**FLATB), [M_GREEN, M_SEC]); par(FLAT_SEC, FLAT_P)
par(lathe_obj("FlatBottomWine", liquid_prof(3.3, 0.32, 0.12, 24.0), [M_RED, M_RED]), FLAT_P)
bake_scale(FLAT_P, lambda t: (max(0.001, pop(t, C["some"] - 0.1, 0.3)),) * 3)

# ================= S4 champagne: pressure, bubbles, ~3x a car tire, dome spreads it =================
CH = dict(R=4.5, H=30.0, t=0.62, hp=3.2, neck=1.6, lip=1.85, ring=0.9, heel=1.3)
CHB = lathe_obj("ChampSection", bottle_prof(**CH), [M_CLEAR, M_SEC], (X4, 0, 0))
CHL = lathe_obj("ChampLiquid", liquid_prof(4.5, 0.62, 3.2, 21.5, ring=0.9), [M_CHAMP, M_CHAMP], (X4, 0, 0))
cork_prof = [(0.04, 27.0), (1.05, 27.0), (1.05, 30.0), (1.7, 30.2), (1.75, 31.6), (1.2, 32.2), (0.04, 32.3)]
lathe_obj("Cork", cork_prof, [M_CORK, M_CORK], (X4, 0, 0))
CAGE = torus("CageRing", 1.95, 0.08, M_STEEL, (X4, 0, 29.0), segU=40, segV=6)
for k in range(4):
    a = math.pi * (0.15 + 0.7 * k / 3)
    tube(f"CageWire{k}", [(X4 + 1.95 * math.cos(a), 1.95 * math.sin(a), 29.0), (X4 + 1.85 * math.cos(a), 1.85 * math.sin(a), 31.4), (X4, 0.5, 32.4)], 0.07, M_STEEL, seg=6)
cyl("CageCap", 0.9, 0.12, "Z", (X4, 0.3, 32.45), M_FOIL)
# pressure arrows (one mesh, flat, in front of the section)
def arrows_bm(specs, y=-0.35, mi=0):
    bm = bmesh.new()
    for (bx, bz, dx, dz, L_, w_) in specs: add_arrow(bm, (bx, bz), (dx, dz), L_, w_, y=y, mi=mi)
    return bm
_sp = []
for z_ in (6.0, 11.0, 16.0):
    _sp += [(X4 + 1.6, z_, 1, 0, 2.0, 0.9), (X4 - 1.6, z_, -1, 0, 2.0, 0.9)]
_sp += [(X4 + 1.5, 6.6, 0.5, -1, 2.0, 0.9), (X4 - 1.5, 6.6, -0.5, -1, 2.0, 0.9), (X4, 7.0, 0, -1, 2.4, 0.9),
        (X4 + 1.4, 20.0, 0.7, 0.7, 2.0, 0.9), (X4 - 1.4, 20.0, -0.7, 0.7, 2.0, 0.9)]
PARR = mesh_obj("PressureArrows", arrows_bm(_sp), M_REDP)
T_P0 = C["gas"] - 0.1
glow(B_REDP, [(0, 0.0), (C["bubbly"], 0.0), (C["bubbly"] + 0.3, 4.0), (C["called"] - 0.1, 4.0), (C["called"], 0.0),
              (T_P0, 0.0), (T_P0 + 0.3, 4.0), (C["under"] - 0.1, 4.0), (C["under"], 0.0), (C["dome2"] - 0.1, 3.0), (C["spread"], 3.0), (C["out"] + 0.2, 0.0)])
bake_scale(PARR, lambda t: (1.0,) * 3)
PARR.location = (0, 0, 0)
def parr_pulse(t):
    return 1.0 + 0.05 * math.sin(2 * math.pi * 2.2 * t)
bake_loc(PARR, lambda t: (0.0, 0.0, 0.0))
# bubbles: particle stream off the dome (rise), plus bead columns
BUB_EM = box("BubbleEmitter", X4 - 2.6, X4 + 2.6, -0.6, -0.1, 4.0, 4.05, None); BUB_EM.hide_render = True
_pb = fx.particles(BUB_EM, "dust", 1, FRAMES, count=900)
try:
    ps = _pb.particle_system.settings; ps.normal_factor = 0.0; ps.object_align_factor = (0, 0, 7.0); ps.effector_weights.gravity = 0.0
    ps.lifetime = 75; ps.particle_size = 0.2; ps.size_random = 0.6; ps.factor_random = 0.3
    ps.instance_object.data.materials[0] = M_BUB
except Exception as e: print("[fx] bubble tune skipped:", e)
bpy.data.objects["fx_dust_dot"].location = (0, 0, -1000) if "fx_dust_dot" in bpy.data.objects else (0, 0, 0)
# ~3x a car tire: tire + two pressure bars
TIRE_P = empty("TireP", (X4 + 34, 0, 10.0))
tz = torus("Tire", 6.2, 2.4, M_RUBBER, (0, 0, 0), segU=48, segV=16); par(tz, TIRE_P); tz.rotation_euler = (math.radians(90), 0, 0)
rim = cyl("TireRim", 4.1, 3.0, "Y", (0, 0, 0), M_STEEL, seg=40); par(rim, TIRE_P)
cyl("TireHub", 1.2, 3.4, "Y", (0, 0, 0), M_DSTEEL).parent = TIRE_P
bake_scale(TIRE_P, lambda t: (max(0.001, pop(t, C["car"] - 0.1)),) * 3)
BAR_T = box("BarTire", -1.4, 1.4, -1.4, 1.4, 0.0, 1.0, M_CYANE); BAR_T.location = (X4 + 20, -6, -0.0)
BAR_C = box("BarChamp", -1.4, 1.4, -1.4, 1.4, 0.0, 1.0, M_REDE); BAR_C.location = (X4 + 13, -6, -0.0)
glow(B_CYANE, [])
glow(B_REDE, [(0, 0.0), (C["three"] - 0.1, 0.0), (C["three"] + 0.2, 3.5), (C["under"], 3.5), (C["under"] + 0.1, 0.0),
              (C["flat"] - 0.1, 0.0), (C["flat"] + 0.3, 3.0), (C["spot"] + 0.2, 3.0), (C["spot"] + 0.6, 0.0),
              (C["no"] - 0.05, 0.0), (C["no"] + 0.15, 6.0), (C["gimmick"] + 0.5, 6.0), (C["idea"] - 0.1, 0.0)])
bake_scale(BAR_T, lambda t: (1.0, 1.0, max(0.001, 4.0 * ease((t - C["car"]) / 0.5))))
bake_scale(BAR_C, lambda t: (1.0, 1.0, max(0.001, 12.0 * ease((t - C["three"] - 0.1) / 0.8))))
windows(BAR_T, [(C["car"] - 0.05, C["under"])]); windows(BAR_C, [(C["three"], C["under"])])
M_BART, B_BART = emit_mat("BarTireGlow", CYAN, 3.0); BAR_T.data.materials[0] = M_BART
# dome spreads it: cyan beads flowing from the apex along the dome into the heel and up the walls (both sides)
def flow_path(sign):
    R_, t_, hp_, ri = 4.5, 0.62, 3.2, 4.5 - 0.9
    pts = [(X4 + sign * (0.1 + (ri - 0.1) * i / 12), -0.2, t_ * 0.5 + dome_f(i / 12, hp_)) for i in range(13)]
    pts += [(X4 + sign * (R_ - 0.45), -0.2, 0.55), (X4 + sign * (R_ - 0.3), -0.2, 1.6), (X4 + sign * (R_ - 0.3), -0.2, 9.0)]
    return Path(chaikin(pts, 2))
M_FLOW, B_FLOW = emit_mat("FlowBead", CYAN, 6.0)
for sgn in (1, -1):
    beads(f"Flow{'R' if sgn > 0 else 'L'}", flow_path(sgn), 9, 0.26, M_FLOW, [(C["spread"] - 0.1, C["thats2"])], speed=7.0)

# ================= S5 flat-bottom failure: bulge, crack, burst (rigid shards, glints, Mantaflow on the laptop) =================
FL = dict(R=4.5, H=30.0, t=0.62, hp=0.12, neck=1.6, lip=1.85, ring=0.9, heel=1.3)
ZF = 12.0
T_BREAK = C["spot"] - 0.05
FLATCH = lathe_obj("FlatChamp", bottle_prof(**FL), [M_CLEAR, M_SEC_F], (X5, 0, ZF), keys=[("Bulge", bottle_prof(**dict(FL, hp=-1.1)))])
sk_bake(FLATCH, "Bulge", lambda t: 0.6 * ease((t - C["flat"]) / 1.0) + 0.06 * math.sin(2 * math.pi * 6 * t) * lin((t - C["flat"]) / 0.8))
glow(B_SEC_F, [(0, 0.25), (C["flat"], 0.25), (C["weak"], 3.5), (T_BREAK, 4.0)])
b_sec = bsdf_of(M_SEC_F); b_sec.inputs["Emission Color"].default_value = (*RED, 1)
FLATL = lathe_obj("FlatChampLiquid", liquid_prof(4.5, 0.62, 0.12, 21.5, ring=0.9), [M_CHAMP, M_CHAMP], (X5, 0, ZF))
windows(FLATCH, [(0, T_BREAK)]); windows(FLATL, [(0, T_BREAK + 0.15)])
_bk = lathe_bm(bottle_prof(**FL))
bmesh.ops.bisect_plane(_bk, geom=list(_bk.verts) + list(_bk.edges) + list(_bk.faces), plane_co=(0, 0, 1.6), plane_no=(0, 0, 1), clear_inner=True)
FLATBROKE = mesh_obj("FlatChampBroken", _bk, [M_CLEAR, M_SEC]); FLATBROKE.location = (X5, 0, ZF)
windows(FLATBROKE, [(T_BREAK, DUR)])
# down-pressure arrows on the flat base
FARR = mesh_obj("FlatArrows", arrows_bm([(X5 + dx, ZF + 4.5, 0, -1, 2.6, 1.0) for dx in (-2.4, 0.0, 2.4)]), M_REDE)
windows(FARR, [(C["flat"] - 0.1, T_BREAK + 0.1)])
# lab clamp holding the neck
cyl("ClampRod", 0.7, 75.0, "Z", (X5 + 14, 8, -22.5), M_STEEL)
box("ClampArm", X5 + 1.5, X5 + 14, 6.5, 9.5, ZF + 24, ZF + 25.5, M_STEEL)
torus("ClampRing", 1.9, 0.35, M_STEEL, (X5, 0, ZF + 24.7), segU=32, segV=8)
box("ClampBase", X5 + 6, X5 + 22, 0, 16, -60, -58.5, M_DSTEEL)
# shards: chunks of the base, kinematic until the break, then rigid-body fall onto the floor
SHARDS = []
rs = random.Random(5)
for k in range(16):
    a = math.pi * (k + 0.5) / 16; rr = 0.8 + 2.6 * rs.random()
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * (0.9 + 0.7 * rs.random()), v.co.y * (0.7 + 0.6 * rs.random()), v.co.z * 0.32))
    o = mesh_obj(f"Shard{k}", bm, [M_CLEAR, M_SEC]); o.location = (X5 + rr * math.cos(a), max(0.3, rr * math.sin(a)) * 0.8, ZF + 0.35)
    o.rotation_euler = (rs.random() * 0.3, rs.random() * 0.3, rs.random() * 6.28)
    SHARDS.append(o)
box("CatchTray", X5 - 16, X5 + 16, -12, 12, -2.0, -0.6, M_STEEL); box("CatchTrayStand", X5 - 10, X5 + 10, -8, 8, -60, -2.0, M_DSTEEL)
SH_FLOOR = box("ShardFloor", X5 - 16, X5 + 16, -12, 12, -2.0, -0.6, None); SH_FLOOR.hide_render = True; SH_FLOOR.display_type = "WIRE"
fx.rigid(SHARDS, passive=[SH_FLOOR], mass=0.02, friction=0.6, bounce=0.25)
for o in SHARDS:
    rb = o.rigid_body
    if rb is None: continue
    rb.kinematic = True; o.keyframe_insert("rigid_body.kinematic", frame=1); o.keyframe_insert("rigid_body.kinematic", frame=F(T_BREAK) + 2)
    rb.kinematic = False; o.keyframe_insert("rigid_body.kinematic", frame=F(T_BREAK) + 3)
    p0 = o.location.copy(); d = Vector((p0.x - X5, -1.0 - rs.random() * 2, -3.0)).normalized()
    key(o, "location", F(T_BREAK), tuple(p0)); key(o, "location", F(T_BREAK) + 2, tuple(p0 + d * 1.6), "LINEAR")
windows_r_list = [windows_r(o, [(T_BREAK, C["thats2"] + 0.5)]) for o in SHARDS]
# glints + falling drops at the break (particles), Mantaflow gush (laptop --bake-fluid only)
GL_EM = box("GlintEmitter", X5 - 3.5, X5 + 3.5, -1.0, 2.0, ZF, ZF + 0.6, None); GL_EM.hide_render = True
_pg = fx.particles(GL_EM, "sparks", F(T_BREAK), F(T_BREAK) + 4, count=120)
try:
    _pg.particle_system.settings.particle_size = 0.12; _pg.particle_system.settings.normal_factor = 120.0; _pg.particle_system.settings.effector_weights.gravity = 1.0
    _m = _pg.particle_system.settings.instance_object.data.materials[0]; bsdf_of(_m).inputs["Emission Color"].default_value = (0.85, 1.0, 0.9, 1)
except Exception as e: print("[fx] glint tune skipped:", e)
DR_EM = box("DropEmitter", X5 - 3.0, X5 + 3.0, -1.0, 1.0, ZF + 0.2, ZF + 0.4, None); DR_EM.hide_render = True
_pd = fx.particles(DR_EM, "mud", F(T_BREAK), F(C["dome2"]), count=260)
try:
    s_ = _pd.particle_system.settings; s_.particle_size = 0.22; s_.normal_factor = -10.0; s_.lifetime = 30
    s_.instance_object.data.materials[0] = M_CHAMP
except Exception as e: print("[fx] drop tune skipped:", e)
FL_DOM = box("FluidDomain", X5 - 15, X5 + 15, -11, 11, -0.6, ZF + 2.0, None); FL_DOM.display_type = "WIRE"
FL_IN = obj_from("FluidInflow", sphere_mesh("FluidInMe", 1.6, 2), None, (X5, 0.5, ZF + 0.5)); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
fx.fluid_domain(FL_DOM, FL_IN, eff=[SH_FLOOR], res=48, start=F(T_BREAK), end=F(T_BREAK + 2.5), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_DOM.data.materials.append(M_CHAMP)
windows(FL_DOM, [(T_BREAK, C["dome2"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True
try:   # inflow only for the first 1.2 s
    fs_ = FL_IN.modifiers["fx_flow"].flow_settings; fs_.use_plane_init = False
    FL_IN.modifiers["fx_flow"].flow_settings.keyframe_insert("use_initial_velocity", frame=1)
except Exception: pass

M_THK, _ = emit_mat("ThickGlow", GOLD, 5.0)
# ================= S6 wall compare: still wine vs champagne glass =================
S6A = lathe_obj("WallStill", bottle_prof(**WINE), [M_GREEN, M_SEC], (X6 - 7, 0, 0))
S6B = lathe_obj("WallChamp", bottle_prof(**CH), [M_CLEAR, M_SEC], (X6 + 7, 0, 0))
box("S6Stand", X6 - 16, X6 + 16, -10, 10, -60, -0.01, M_DSTEEL)
# thickness callouts: gold bars across each wall at z = 6
for nm, x0_, th in (("Still", X6 - 7 + 3.7 - 0.32, 0.32), ("Champ", X6 + 7 - 4.5, 0.62)):
    b_ = box(f"Thick{nm}", x0_ - 0.15, x0_ + th + 0.15, -0.6, -0.3, 3.0, 10.0, M_THK)
    windows(b_, [(C["thicker"] - 0.1, C["so2"])])

# ================= S7 myth: shallow vs deep punt, red X, sediment =================
SH = dict(R=3.7, H=30.0, t=0.32, hp=0.8)
DP = dict(R=3.7, H=30.0, t=0.32, hp=5.2)
lathe_obj("MythShallow", bottle_prof(**SH), [M_GREEN, M_SEC], (X7 - 9, 0, 0))
lathe_obj("MythShallowWine", liquid_prof(3.7, 0.32, 0.8, 22.0), [M_RED, M_RED], (X7 - 9, 0, 0))
DEEP = lathe_obj("MythDeep", bottle_prof(**DP), [M_GREEN, M_SEC], (X7 + 9, 0, 0))
lathe_obj("MythDeepWine", liquid_prof(3.7, 0.32, 5.2, 22.0), [M_RED, M_RED], (X7 + 9, 0, 0))
box("S7Stand", X7 - 18, X7 + 18, -10, 10, -60, -0.01, M_DSTEEL)
XP = empty("RedX", (X7, -8, 15))
for a in (45, -45):
    bm = bmesh.new(); add_box(bm, -9, 9, -0.6, 0.6, -1.0, 1.0); o = mesh_obj(f"RedXBar{a}", bm, M_REDE); par(o, XP); o.rotation_euler = (0, math.radians(a), 0)
bake_scale(XP, lambda t: (pop(t, C["no"] - 0.05),) * 3)
windows(XP, [(C["no"] - 0.06, C["idea"])])
# sediment specks drifting down into the ring trough around the deep punt
SED = []
for k in range(26):
    sgn = 1 if k % 2 else -1
    rx = sgn * (3.7 - 0.62 + 0.12 * rs.random()); z_end = 0.32 + 0.25 + 0.25 * rs.random()
    x_s, z_s = sgn * (0.6 + 2.6 * rs.random()), 9.0 + 9.0 * rs.random()
    o = obj_from(f"Sediment{k}", sphere_mesh(f"SedMe{k}", 0.16 + 0.1 * rs.random(), 1), M_SED)
    t0_ = C["idea"] - 0.2 + 0.9 * rs.random()
    bake_loc(o, lambda t, x_s=x_s, z_s=z_s, rx=rx, z_end=z_end, t0_=t0_: (X7 + 9 + x_s + (rx - x_s) * ease((t - t0_) / 2.4), -0.15, z_s + (z_end - z_s) * ease((t - t0_) / 2.4)))
    windows(o, [(C["idea"] - 0.25, C["have"])]); SED.append(o)

# ================= lights + world =================
fx.hdri("studio", strength=0.30, rotation_deg=30.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, size, energy, rgb, target):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); return o
for x_, zc in ((X1, 18), (X1 + 60, 6), (X2 + 15, 12), (X3, 14), (X4 + 15, 14), (X5, 18), (X6, 8), (X7, 12)):
    area(f"Key{x_}", (x_ - 35, -55, zc + 35), 40, 1.6e4, (1.0, 0.93, 0.85), (x_, 0, zc))
    area(f"Rim{x_}", (x_ + 40, 45, zc + 20), 30, 9.0e3, (0.6, 0.78, 1.0), (x_, 0, zc))
    area(f"Under{x_}", (x_ + 5, -30, zc - 25), 25, 2.5e3, (1.0, 0.9, 0.8), (x_, 0, zc - 5))
area("HookGraze", (X1 - 24, -30, 26), 14, 3.0e3, (1.0, 0.95, 0.88), (X1, -14, 17))
FURN_L = bpy.data.lights.new("FurnaceGlow", "POINT"); FURN_L.energy = 6.0e4; FURN_L.color = (1.0, 0.45, 0.15)
_fl = bpy.data.objects.new("FurnaceGlow", FURN_L); scene.collection.objects.link(_fl); _fl.location = (X2 - 40, 40, 22)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.5; cam_d.clip_end = 3000
def hotp(dx, dy, dz):
    return lambda t: (hot_xz(t)[0] + dx, dy, hot_xz(t)[1] + dz)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (X1 + 10, -80, 17), (X1, 0, 16), 42),                                  # hook: bottle lifts and flips its base to the camera
    (T_FLIP, (X1 + 3, -56, 8.0), (X1, -14, 17.0), 48),
    (C["but"] - 0.05, (X1 + 2, -48, 9.0), (X1, -14, 17.0), 50),
    (C["but"], (X4, -100, 16), (X4, 0, 15.5), 45, "cut"),                        # stake: bubbly under pressure
    (C["bursting"] - 0.1, (X4 + 2, -60, 9), (X4, 0, 7), 45),
    (C["called"], (PUNT_X + 4, -26, 7), (PUNT_X, 0, 2.6), 50, "cut"),             # "It's called a punt": the section
    (C["back"] - 0.05, (PUNT_X + 3, -22, 6), (PUNT_X, 0, 2.4), 50),
    (C["back"], (X2 + 6, -95, 26), (X2 + 2, 0, 24), 40, "cut"),                  # hand-blown: hot bottle on the blowpipe
    (C["base"] - 0.05, (X2 + 4, -80, 20), (X2 + 2, 0, 20), 40),
    (C["base"], hotp(4, -30, 0.5), hotp(0, 0, 1.0), 50, "cut"),                          # close: the sharp point under the base
    (T_DOWN0 - 0.05, hotp(3, -25, 0.5), hotp(0, 0, 0.6), 50),
    (T_DOWN0, (X2 + 4, -62, 12), (X2, 0, 8), 45, "cut"),                         # it wobbles on the marver
    (T_LIFT0, (X2 + 4, -60, 12), (X2, 0, 8), 45),
    (T_LIFT0 + 0.01, (X_PUSH + 6, -48, 4), (X_PUSH, 0, 12), 45, "cut"),             # pushed up from below
    (T_BACK0 - 0.05, (X_PUSH + 4, -40, 6), (X_PUSH, 0, 12.5), 45),
    (T_BACK0, (X2 + 5, -38, 9), (X2, 0, 3.0), 45, "cut"),                        # stands on a smooth ring
    (C["dome"] - 0.05, (X2 + 4, -32, 8), (X2, 0, 2.5), 47),
    (C["dome"], (X2 + 2, -24, 4.5), (X2, 0, 2.0), 50, "cut"),                    # the dome, maybe stronger
    (C["today"] - 0.05, (X2 + 1, -21, 4), (X2, 0, 2.0), 50),
    (C["today"], (X3 - 10, -110, 28), (X3, 0, 12), 35, "cut"),                   # machines today
    (C["some"] - 0.05, (X3 + 6, -100, 24), (X3 + 5, 0, 12), 35),
    (C["some"], (X3 + 24, -64, 13), (X3 + 20, -16, 11), 45, "cut"),              # some have none: flat bottom
    (C["sparkling"] - 0.05, (X3 + 23, -56, 9), (X3 + 20, -16, 7.5), 45),
    (C["sparkling"], (X4, -95, 18), (X4, 0, 16), 45, "cut"),                     # champagne under pressure
    (C["three"] - 0.05, (X4, -80, 15), (X4, 0, 14), 45),
    (C["three"], (X4 + 17, -100, 14), (X4 + 17, 0, 12), 45, "cut"),              # ~3x a car tire
    (C["under"] - 0.05, (X4 + 17, -94, 14), (X4 + 17, 0, 12), 45),
    (C["under"], (X5 + 3, -82, ZF + 12), (X5, 0, ZF + 11), 45, "cut"),            # a flat bottom is a weak spot
    (C["weak"] - 0.05, (X5 + 3, -50, ZF + 3), (X5, 0, ZF + 1.0), 45),
    (C["weak"], (X5 + 5, -50, ZF - 2), (X5, 0, ZF - 6), 45, "cut"),             # burst: shards fall into the tray
    (C["dome2"] - 0.05, (X5 + 4, -44, ZF - 4), (X5, 0, ZF - 7.5), 45),
    (C["dome2"], (X4 + 2, -36, 6), (X4, 0, 3.5), 45, "cut"),                     # the dome spreads the pressure
    (C["thats2"] - 0.05, (X4 + 2, -30, 5), (X4, 0, 3.5), 45),
    (C["thats2"], (X6, -78, 16), (X6, 0, 14), 45, "cut"),                        # thicker, heavier glass
    (C["thicker"] - 0.2, (X6, -38, 9), (X6, 0, 7), 45),
    (C["so2"] - 0.05, (X6, -34, 8), (X6, 0, 7), 45),
    (C["so2"], (X7, -90, 16), (X7, 0, 14), 45, "cut"),                           # deeper = better? no
    (C["idea"] - 0.05, (X7, -82, 15), (X7, 0, 13), 45),
    (C["idea"], (X7 + 11, -30, 6), (X7 + 9, 0, 3.0), 45, "cut"),                 # sediment idea: unproven
    (C["have"] - 0.05, (X7 + 10, -26, 5), (X7 + 9, 0, 2.5), 45),
    (C["have"], (X1 + 2, -46, 9.5), (X1, -14, 17.0), 50, "cut"),               # CTA: the dent, slow pull-out
    (DUR, (X1 + 6, -80, 21), (X1, -8, 20), 45),
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
bake_scalar(cam_d, "dof.aperture_fstop", [max(5.6, min(22.0, 0.25 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
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
fx.bake_rigid(F(T_BREAK) - 1, F(C["dome2"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "hook_base": W(HOOK, (0, 0, 1.6)), "punt": (PUNT_X, -0.1, 0.32 + 2.4), "nub": W(HOT, (0, 0, NUB)), "ring": W(HOT, (3.15, 0, 0.0)),
    "rough": W(DOT, (0, 0, 0)), "dome": W(HOT, (0, -0.1, 2.6)), "flatb": (X3 + 20 + 3.0, -16.2, 6.0), "line": (X3, 0, 20.0),
    "cork": (X4, -0.2, 31.0), "liquid": (X4 + 2.0, -0.2, 14.0), "tire": W(TIRE_P, (0, 0, 8.6)), "bar_c": (X4 + 13, -6, 12.0), "bar_t": (X4 + 20, -6, 4.0),
    "flat_base": (X5, -0.2, ZF + 0.2), "dome2": (X4, -0.2, 0.62 + 3.2), "still": (X6 - 7 + 3.55, -0.6, 10.0), "champ": (X6 + 7 - 4.2, -0.6, 10.0),
    "shallow": (X7 - 9, -0.2, 1.2), "deep": (X7 + 9, -0.2, 5.6), "trough": (X7 + 9 + 3.0, -0.2, 0.6),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4], "flip": RR(0.0, T_FLIP), "down": round(T_DOWN1, 3), "wobble": RR(T_DOWN1, T_LIFT0),
          "lift": round(T_LIFT0, 3), "push": RR(T_PUSH0, T_PUSH1), "stand": round(T_BACK1, 3), "ring": round(C["ring"], 3),
          "line": RR(C["today"], C["sparkling"]), "flat_pop": round(C["some"], 3), "fizz": RR(C["sparkling"], C["under"]),
          "pressure": RR(T_P0, C["under"]), "bars": [round(C["three"] + 0.1, 3), round(C["car"], 3)], "bulge": RR(C["flat"], T_BREAK),
          "break": round(T_BREAK, 3), "shards_land": round(T_BREAK + 0.42, 3), "flow": RR(C["spread"], C["thats2"]), "xstamp": round(C["no"], 3),
          "sediment": RR(C["idea"], C["have"])}
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
