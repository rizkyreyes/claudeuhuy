# Subway station (3d-32): how a station is built under a busy street (cut and cover, bottom-up with street decking).
# Claim-first hook ("Cars are driving right over this subway station while it's being built."): section through the street, cars on the
# deck above a 68 ft deep braced hole -> what-if: an unsupported hole caves in, the road slab and a car drop in (rigid body) -> walls first:
# ghost outlines of the two slurry walls -> clamshell bucket digs the trench, bentonite slurry fills it -> slurry pressure arrows ->
# steel cage drops in, concrete via tremie pipe from the bottom, slurry pushed up and out (Mantaflow overflow shot, laptop bake) ->
# x-ray long view: panels pop in one by one along both sides, 3.5 ft -> dig the top, steel beams + deck panels, traffic back on ->
# water main + duct bank hung from the beams -> excavator digs under the deck (dust), struts pop in level by level -> floor, platform,
# columns, mezzanine, roof -> struts out, backfill, deck lifted, asphalt back -> inside the finished station, a train pulls in (1904)
# -> street level, last road plates lift off, glide back to the hook framing over the finished station (loop: "...hiding under the cars." -> hook).
# Illustrative (1 unit = 1 m): generic two-track island-platform station; depth 20.7 m (68 ft) and 1.07 m (3.5 ft) walls follow the
# Second Avenue Subway 96th St station (ASCE); the station length is shortened; no logos, no people.
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
DUR = round(WORDS[-1]["end"] + VO + 0.25, 2)   # loop ending (15 Nov): hard cut right after the last word
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(30)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
CUES = [("cars", "Cars"), ("built", "built."), ("under", "Under"), ("sixty", "sixty-eight"), ("down", "down,"), ("and", "and"),
        ("caved", "caved"), ("road", "road"), ("drop", "drop"), ("so", "So"), ("walls", "walls"), ("first", "first,"), ("digs", "digs."),
        ("clamshell", "clamshell"), ("trench", "trench"), ("full", "full"), ("clay", "clay"), ("bentonite", "bentonite"), ("it", "It"),
        ("pushes", "pushes"), ("dirt", "dirt,"), ("open", "open"), ("no", "no"), ("then", "Then"), ("cage", "cage"), ("concrete", "concrete"),
        ("bottom", "bottom."), ("heavier", "heavier,"), ("shoves", "shoves"), ("out", "out."), ("panel", "Panel"), ("solid", "solid"),
        ("three", "three"), ("thick", "thick."), ("now", "Now"), ("dig", "dig"), ("top", "top,"), ("beams", "beams"), ("deck", "deck"),
        ("traffic", "Traffic"), ("water", "Water"), ("cables", "cables"), ("hung", "hung"), ("then2", "Then"), ("real", "real"),
        ("digging", "digging"), ("under2", "under"), ("as", "As"), ("struts", "struts"), ("brace", "brace"), ("apart", "apart,"),
        ("fold", "fold"), ("at", "At"), ("bottom2", "bottom,"), ("floor", "floor,"), ("station", "station"), ("roof", "roof."),
        ("the", "The"), ("dirt2", "dirt"), ("street", "street"), ("thats", "That's"), ("cut", "cut"), ("new", "New"), ("first2", "first"),
        ("y1904", "1904."), ("and2", "And"), ("deck2", "deck"), ("normal", "normal"), ("whole", "whole"), ("station2", "station"),
        ("cars2", "cars.")]
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
CL = coll("Subway")
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


# ================= story time: the hook shows the braced hole under the deck (state just after "fold"), the build runs from "So" =================
S_HOOK = C["fold"] + 0.4
def ST(t): return S_HOOK if t < C["so"] else t
SS = [ST(t) for t in TS]
def vis_fn(obj, pred):
    """Visibility from a per-frame predicate pred(t) (keys only where it changes)."""
    prev = None
    for i, t in enumerate(TS):
        v = bool(pred(t))
        if v != prev:
            vis(obj, i + 1, not v); prev = v
def vis_s(obj, a, b=1e9):
    """Visible while a <= story time < b."""
    vis_fn(obj, lambda t: a <= ST(t) < b)
def bake_loc_s(o, fn): bake_loc(o, lambda t: fn(ST(t)))
def bake_scale_s(o, fn): bake_scale(o, lambda t: fn(ST(t)))
def boxb(name, x0, x1, y0, y1, z0, z1, m_):
    """Box with its origin on the bottom face centre line (z0), so scale z grows it upwards."""
    o = box(name, x0, x1, y0, y1, 0, z1 - z0, m_); o.location = (0, 0, z0); return o
def boxt(name, x0, x1, y0, y1, ztop, m_):
    """Unit-deep box hanging from ztop (origin on top): scale z = depth below ztop."""
    o = box(name, x0, x1, y0, y1, -1.0, 0.0, m_); o.location = (0, 0, ztop); return o
def grow(t, t0, t1): return max(0.0001, min(1.0, ease((t - t0) / (t1 - t0)))) if t1 > t0 else (1.0 if t >= t0 else 0.0001)
def first_s(pred):
    for t in TS:
        if t >= C["so"] and pred(t): return t
    return DUR

# ================= dimensions (m) =================
WX0, WX1 = 9.53, 10.60          # inner / outer face of the slurry walls (1.07 m = 3.5 ft)
WXC = (WX0 + WX1) / 2
DEPTH = 20.7                    # 68 ft
WALL_BOT, WALL_TOP = -24.0, -1.0
ROAD_T = -0.25
L = 72.0                        # station box length shown (shortened)
PANEL = 6.0; NP = int(L / PANEL)
ENDW = L - 1.07
Z_S = [-3.8, -10.0, -16.0]      # strut levels
ROOF0, ROOF1 = -6.0, -4.9
BASE1 = -19.5
TX = 6.0                        # track centre lines at +-TX

# ================= timing =================
T_HOOK = (0.0, C["and"]); T_FAIL = (C["and"], C["so"]); T_GHOST = (C["so"], C["clamshell"]); T_TRENCH = (C["clamshell"], C["it"])
T_PUSH = (C["it"], C["then"]); T_CAGE = (C["then"], C["panel"]); T_PANELS = (C["panel"], C["now"]); T_DECK = (C["now"], C["water"])
T_UTIL = (C["water"], C["then2"]); T_DIG = (C["then2"], C["at"]); T_BUILD = (C["at"], C["the"]); T_FILL = (C["the"], C["thats"])
T_INSIDE = (C["thats"], C["and2"]); T_END = (C["and2"], DUR)
DIG0, DIG1 = C["clamshell"] + 0.2, C["it"] + 0.5
def trench_d(s): return 23.7 * PW([(DIG0, 0.0), (DIG1, 1.0)])(s)
CONC0, CONC1 = C["concrete"] + 0.3, C["out"] + 0.2
def conc_top(s): return WALL_BOT + (WALL_TOP - WALL_BOT) * PW([(CONC0, 0.0), (CONC1, 1.0)])(s)
CORE_TOP = PW([(C["dig"], ROAD_T), (C["top"] + 0.4, -3.2), (C["digging"], -3.2), (C["fold"] + 0.3, -DEPTH + 0.02)])

# ================= materials =================
XRAY_KEYS = [(0, 0.0), (C["so"] - 0.01, 0.0), (C["so"] + 0.3, 0.75), (C["clamshell"] - 0.3, 0.75), (C["clamshell"] + 0.1, 0.0), (C["panel"] - 0.05, 0.0), (C["panel"] + 0.3, 0.86), (C["now"] - 0.35, 0.86), (C["now"], 0.0), (DUR, 0.0)]
def soil_mat(name, shade=1.0, xray=True):
    m, nt, b = new_mat(name); N, Lk = nt.nodes, nt.links
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(geo.outputs["Position"], sep.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -30.0; mr.inputs[2].default_value = 0.0
    Lk.new(sep.outputs["Z"], mr.inputs[0])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 8.0
    Lk.new(geo.outputs["Position"], nz.inputs["Vector"])
    fac = MATH(nt, "ADD", mr.outputs[0], MATH(nt, "MULTIPLY", MATH(nt, "SUBTRACT", nz.outputs["Fac"], 0.5), 0.05))
    cr = N.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"; e = cr.color_ramp.elements
    bands = [(0.0, (0.19, 0.19, 0.20)), (0.40, (0.30, 0.26, 0.21)), (0.60, (0.52, 0.42, 0.27)), (0.80, (0.40, 0.25, 0.14)), (0.95, (0.14, 0.10, 0.06))]
    e[0].position, e[0].color = bands[0][0], (*[c * shade for c in bands[0][1]], 1)
    e[1].position, e[1].color = bands[1][0], (*[c * shade for c in bands[1][1]], 1)
    for p, c in bands[2:]:
        el = e.new(p); el.color = (*[x * shade for x in c], 1)
    Lk.new(fac, cr.inputs[0])
    spk = N.new("ShaderNodeTexNoise"); spk.inputs["Scale"].default_value = 6.0; Lk.new(geo.outputs["Position"], spk.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 0.35
    Lk.new(cr.outputs[0], mx.inputs[6]); Lk.new(spk.outputs["Fac"], mx.inputs[7]); Lk.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    if xray:
        out = next(x for x in N if x.type == "OUTPUT_MATERIAL")
        tr = N.new("ShaderNodeBsdfTransparent"); ms = N.new("ShaderNodeMixShader")
        Lk.new(VALUE(nt, "XRay", XRAY_KEYS), ms.inputs[0]); Lk.new(b.outputs[0], ms.inputs[1]); Lk.new(tr.outputs[0], ms.inputs[2])
        Lk.new(ms.outputs[0], out.inputs["Surface"])
    return m
M_SOIL = soil_mat("Soil")
M_SOIL_W = soil_mat("SoilWhatIf", xray=False)
M_FILL, _ = mat("Backfill", (0.24, 0.17, 0.11), rough=0.95, noise=2.0)
M_ROAD, _ = mat("Asphalt", (0.035, 0.035, 0.038), rough=0.85, noise=0.6)
M_NEWROAD, _ = mat("NewAsphalt", (0.018, 0.018, 0.02), rough=0.7, noise=0.6)
M_LINE, _ = mat("RoadLine", (0.85, 0.72, 0.25), rough=0.5)
M_LINEW, _ = mat("RoadLineW", (0.85, 0.85, 0.82), rough=0.5)
M_WALK, _ = mat("Sidewalk", (0.52, 0.51, 0.49), rough=0.8, noise=1.5)
M_PLAZA, _ = mat("Plaza", (0.33, 0.33, 0.33), rough=0.85, noise=0.4)
M_WALL, B_WALL = mat("SlurryWall", (0.50, 0.50, 0.48), rough=0.8, noise=0.9)
M_CONC, B_CONC = mat("StationConcrete", (0.62, 0.61, 0.58), rough=0.75, noise=0.9)
M_WET, B_WET = mat("WetConcrete", (0.45, 0.45, 0.44), rough=0.25, noise=1.2)
M_SLURRY, B_SLURRY = mat("Bentonite", (0.42, 0.36, 0.27), rough=0.12, emit_rgb=(0.98, 0.74, 0.27), alpha=0.55)
M_SLURRY_T, _ = mat("BentoniteTank", (0.42, 0.36, 0.27), rough=0.12)
M_TREMIE, B_TREMIE = mat("Tremie", (0.22, 0.23, 0.25), rough=0.4, metallic=0.85, emit_rgb=(0.98, 0.74, 0.27))
M_STEEL, B_STEEL = mat("Steel", (0.22, 0.23, 0.25), rough=0.4, metallic=0.85, emit_rgb=(0.30, 0.92, 1.0))
M_STRUT, B_STRUT = mat("Strut", (0.55, 0.42, 0.10), rough=0.45, metallic=0.6, emit_rgb=(0.30, 0.92, 1.0))
M_REBAR, _ = mat("Rebar", (0.25, 0.14, 0.08), rough=0.6, metallic=0.7)
M_DECK, _ = mat("DeckPanel", (0.20, 0.19, 0.17), rough=0.75, noise=3.0)
M_PLATE, _ = mat("RoadPlate", (0.30, 0.30, 0.31), rough=0.45, metallic=0.8, noise=4.0)
M_PIPE, B_PIPE = mat("WaterMain", (0.10, 0.20, 0.35), rough=0.5, metallic=0.4, emit_rgb=(0.30, 0.92, 1.0))
M_DUCT, B_DUCT = mat("Duct", (0.85, 0.40, 0.10), rough=0.5, emit_rgb=(0.98, 0.74, 0.27))
M_YEL, _ = mat("MachineYellow", (0.85, 0.55, 0.05), rough=0.45)
M_DARK, _ = mat("DarkSteel", (0.08, 0.08, 0.09), rough=0.5, metallic=0.6)
M_TILE = tiles("StationTile", (0.80, 0.80, 0.76), (0.74, 0.75, 0.72), 1.2)
M_EDGE, _ = mat("PlatformEdge", (0.90, 0.70, 0.10), rough=0.5)
M_RAIL, _ = mat("Rail", (0.55, 0.55, 0.57), rough=0.3, metallic=1.0)
M_TIE, _ = mat("Tie", (0.30, 0.29, 0.27), rough=0.8)
M_TRAIN, _ = mat("TrainBody", (0.70, 0.72, 0.75), rough=0.25, metallic=0.85)
M_TWIN, B_TWIN = mat("TrainWindow", (0.05, 0.06, 0.07), rough=0.1, emit_rgb=(1.0, 0.93, 0.80))
B_TWIN.inputs["Emission Strength"].default_value = 2.0
M_TUNNEL, _ = mat("TunnelLining", (0.10, 0.10, 0.11), rough=0.8)
M_FACADE = tiles("Facade", (0.12, 0.15, 0.19), (0.62, 0.60, 0.56), 0.35)
M_ROOFB, _ = mat("BldgRoof", (0.20, 0.20, 0.21), rough=0.8)
M_TYRE, _ = mat("Tyre", (0.02, 0.02, 0.02), rough=0.7)
M_GLASS, _ = mat("CarGlass", (0.03, 0.04, 0.05), rough=0.05, metallic=0.3)
CAR_COLS = [(0.60, 0.04, 0.03), (0.85, 0.85, 0.86), (0.05, 0.08, 0.20), (0.75, 0.60, 0.08), (0.12, 0.12, 0.13), (0.30, 0.45, 0.55)]
M_CARS = [mat(f"CarPaint{i}", c, rough=0.25, metallic=0.5)[0] for i, c in enumerate(CAR_COLS)]
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 2.2)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 2.5)
M_REDG, B_REDG = emit_mat("RedGlow", (1.0, 0.25, 0.18), 2.5)
M_LAMP, B_LAMP = emit_mat("StationLamp", (1.0, 0.95, 0.85), 0.0)
M_GHOST, GHOST_FAC = ghost("WallGhost", (0.30, 0.92, 1.0))
keyval(GHOST_FAC, [(0, 0.0), (C["so"] + 0.05, 0.0), (C["walls"] + 0.1, 0.55), (C["first"] + 0.3, 0.8), (C["clamshell"] - 0.2, 0.55), (C["clamshell"] + 0.3, 0.0), (DUR, 0.0)])

# ================= ground, street, soil (section plane y = 0) =================
def plane(name, x0, x1, y0, y1, z, m_):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]; bm.faces.new(vs)
    return mesh_obj(name, bm, m_)
PLAZA_L = plane("PlazaL", -200, -20, 0, 600, 0.15, M_PLAZA); PLAZA_R = plane("PlazaR", 20, 200, 0, 600, 0.15, M_PLAZA)
WALK_L = box("SidewalkL", -20, -16, 0, 600, ROAD_T, 0.15, M_WALK); WALK_R = box("SidewalkR", 16, 20, 0, 600, ROAD_T, 0.15, M_WALK)
SROAD_L = box("RoadSideL", -16, -WX1, 0, 600, ROAD_T, 0.0, M_ROAD); SROAD_R = box("RoadSideR", WX1, 16, 0, 600, ROAD_T, 0.0, M_ROAD)
FROAD = box("RoadFar", -WX1, WX1, L, 600, ROAD_T, 0.0, M_ROAD)
SOIL = [box("SoilL", -70, -WX1, 0, L + 40, -35, ROAD_T, M_SOIL), box("SoilR", WX1, 70, 0, L + 40, -35, ROAD_T, M_SOIL),
        box("SoilDeep", -WX1, WX1, 0, L + 40, -35, WALL_BOT, M_SOIL), box("SoilBase", -WX0, WX0, 0, L, WALL_BOT, -DEPTH, M_SOIL),
        box("SoilEndLow", -WX1, WX1, L, L + 40, WALL_BOT, BASE1 - 0.1, M_SOIL),
        box("SoilEndHigh", -WX1, WX1, L, L + 40, -15.0, ROAD_T, M_SOIL)]
for x0, x1 in ((-WX1, -TX - 2.2), (-TX + 2.2, TX - 2.2), (TX + 2.2, WX1)):
    SOIL.append(box(f"SoilEndMid{x0:.0f}", x0, x1, L, L + 40, BASE1 - 0.1, -15.0, M_SOIL))
# tunnels beyond the station end (dark lining, the train comes out of the right one)
for sx in (-1, 1):
    bm = bmesh.new(); xc = sx * TX
    add_box(bm, xc - 2.2, xc + 2.2, L, L + 40, BASE1 - 0.1, BASE1, 0); add_box(bm, xc - 2.2, xc + 2.2, L, L + 40, -15.2, -15.0, 0)
    add_box(bm, xc - 2.2, xc - 2.0, L, L + 40, BASE1, -15.0, 0); add_box(bm, xc + 2.0, xc + 2.2, L, L + 40, BASE1, -15.0, 0)
    mesh_obj(f"Tunnel{sx}", bm, M_TUNNEL)
# end wall of the station box (with the two track portals)
bm = bmesh.new()
add_box(bm, -WX0, WX0, ENDW, L, WALL_BOT, -DEPTH); add_box(bm, -WX0, WX0, ENDW, L, -15.0, WALL_TOP)
for x0, x1 in ((-WX0, -TX - 2.2), (-TX + 2.2, TX - 2.2), (TX + 2.2, WX0)): add_box(bm, x0, x1, ENDW, L, -DEPTH, -15.0)
ENDWALL = mesh_obj("EndWall", bm, M_WALL)
vis_s(ENDWALL, C["panel"] + 4.2)
SOIL_ENDCORE = box("SoilEndCore", -WX0, WX0, ENDW, L, -DEPTH, ROAD_T, M_SOIL)
vis_s(SOIL_ENDCORE, 0, C["panel"] + 4.2)

# core soil between the walls (dug from the top)
CORE = boxb("CoreSoil", -WX0, WX0, 0, ENDW, -DEPTH, ROAD_T, M_SOIL)
bake_scale_s(CORE, lambda s: (1, 1, max(0.0005, (CORE_TOP(s) + DEPTH) / (ROAD_T + DEPTH))))
vis_s(CORE, 0, C["fold"] + 0.32)

# ================= slurry walls: 12 panels per side; the left front panel is built on camera =================
ORDER = [(1, 0)] + [p for k in range(1, NP) for p in ((0, k), (1, k))]
PANEL_T = {}
for i, (side, k) in enumerate(ORDER): PANEL_T[(side, k)] = C["panel"] + 0.17 * i
PANELS, SLOTS = {}, {}
for side, sx in ((0, -1), (1, 1)):
    xa, xb = sorted((sx * WX0, sx * WX1))
    for k in range(NP):
        y0, y1 = k * PANEL + 0.015, (k + 1) * PANEL - 0.015
        slot = boxb(f"SlotSoil{side}_{k}", xa, xb, y0, y1, WALL_BOT, ROAD_T, M_SOIL); SLOTS[(side, k)] = slot
        pn = boxb(f"Panel{side}_{k}", xa, xb, y0, y1, WALL_BOT, WALL_TOP, M_WALL); PANELS[(side, k)] = pn
        if (side, k) == (0, 0):
            H = ROAD_T - WALL_BOT
            bake_scale_s(slot, lambda s: (1, 1, max(0.0005, (H - trench_d(s)) / H)))
            vis_s(slot, 0, DIG1 + 0.2)
            HW = WALL_TOP - WALL_BOT
            bake_scale_s(pn, lambda s: (1, 1, max(0.0005, (conc_top(s) - WALL_BOT) / HW)))
            vis_s(pn, CONC0)
        else:
            t0 = PANEL_T[(side, k)]
            bake_scale_s(pn, lambda s, t0=t0: (1, 1, grow(s, t0, t0 + 0.35)))
            vis_s(pn, t0); vis_s(slot, 0, t0 + 0.05)
glow(B_WALL, [(0, 0.0), (C["panel"] - 0.01, 0.0), (C["panel"] + 0.2, 0.9), (C["thick"] - 0.2, 0.9), (C["thick"] + 0.5, 0.0), (DUR, 0.0)])
B_WALL.inputs["Emission Color"].default_value = (0.98, 0.74, 0.27, 1)
# ghost outlines of both walls ("walls go in first")
bm = bmesh.new()
for sx in (-1, 1):
    xa, xb = sorted((sx * WX0, sx * WX1)); add_box(bm, xa, xb, 0.02, L - 0.02, WALL_BOT, WALL_TOP)
GHOSTW = mesh_obj("WallGhost", bm, M_GHOST)
vis_fn(GHOSTW, lambda t: T_GHOST[0] <= t < T_GHOST[1] + 0.4)
# road over the slots (open during construction) + guide walls
SLOTROAD = []
for sx in (-1, 1):
    xa, xb = sorted((sx * WX0, sx * WX1)); o = box(f"SlotRoad{sx}", xa, xb, 0, L, ROAD_T, 0.0, M_ROAD); SLOTROAD.append(o)
    vis_fn(o, lambda t: ST(t) < C["clamshell"] or ST(t) >= C["street"] + 0.2)
    bm = bmesh.new(); add_box(bm, xa - 0.3, xa, 0, L, -1.0, 0.02); add_box(bm, xb, xb + 0.3, 0, L, -1.0, 0.02)
    g = mesh_obj(f"GuideWall{sx}", bm, M_CONC); vis_s(g, C["clamshell"], C["street"] + 0.2)
# center road (dug out, then rebuilt) + lane lines
CROAD = box("RoadCenter", -WX0, WX0, 0, L, ROAD_T, 0.0, M_ROAD)
vis_fn(CROAD, lambda t: ST(t) < C["dig"])
NEWROAD = box("RoadNew", -WX1, WX1, 0, L, ROAD_T, 0.0, M_NEWROAD)
bake_loc_s(NEWROAD, lambda s: (0, 0, drop(s, C["street"], 3.0, 0.45)))
vis_s(NEWROAD, C["street"])
def lane_lines(name, y0, y1):
    bm = bmesh.new()
    for y in range(int(y0), int(y1), 9):
        for x in (-5.2, 5.2): add_box(bm, x - 0.07, x + 0.07, y + 0.5, y + 4.5, 0.0, 0.012)
    o1 = mesh_obj(name + "W", bm, M_LINEW)
    bm = bmesh.new(); add_box(bm, -0.22, -0.08, y0, y1, 0.0, 0.012); add_box(bm, 0.08, 0.22, y0, y1, 0.0, 0.012)
    return o1, mesh_obj(name + "Y", bm, M_LINE)
lane_lines("LanesFar", L, 600)
for o in lane_lines("LanesNear", 0, L): vis_fn(o, lambda t: ST(t) < C["dig"] or ST(t) >= C["street"] + 0.5)

# ================= trench: clamshell crane, bentonite slurry, steel cage, tremie pipe =================
TRX, TRY = -WXC, 3.0
SLURRY = boxt("Slurry", -WX1 + 0.01, -WX0 - 0.01, 0.02, PANEL - 0.03, -0.45, M_SLURRY)
def slurry_depth(s):
    top = -0.45
    bot = -0.45 - trench_d(s) if s < CONC0 else conc_top(s)
    return max(0.0005, top - bot)
bake_scale_s(SLURRY, lambda s: (1, 1, slurry_depth(s)))
vis_s(SLURRY, DIG0, CONC1 + 0.1)
glow(B_SLURRY, [(0, 0.0), *pulse(C["clay"], 0.5, hold=0.3), *pulse(C["bentonite"], 1.4, hold=0.9), (DUR, 0.0)])
# crawler crane on the closed lane
CRANE = empty("Crane", (-21.0, 4.5, 0.0))
bm = bmesh.new()
add_box(bm, -2.6, 2.6, -2.6, -1.6, 0.0, 1.1, 1); add_box(bm, -2.6, 2.6, 1.6, 2.6, 0.0, 1.1, 1)
add_box(bm, -2.2, 2.2, -2.0, 2.0, 1.1, 2.0, 0); add_box(bm, -3.4, 1.6, -1.8, 1.8, 2.0, 4.2, 0); add_box(bm, -3.6, -1.6, -1.6, 1.6, 2.0, 5.0, 1)
add_box(bm, 0.4, 1.8, -1.6, -0.4, 4.2, 5.8, 0)
CR_BODY = mesh_obj("CraneBody", bm, [M_YEL, M_DARK], parent=CRANE)
TIP = Vector((TRX, TRY, 24.0)); BOOT = Vector((-20.0, 4.5, 4.4))
bm = bmesh.new()
for dy in (-0.55, 0.55):
    add_bar(bm, BOOT + Vector((0, dy, 0)), TIP + Vector((0, dy * 0.4, 0)), 0.28)
n_ = 14
for j in range(n_):
    a = BOOT.lerp(TIP, j / n_); b = BOOT.lerp(TIP, (j + 1) / n_)
    add_bar(bm, a + Vector((0, -0.55 * (1 - 0.6 * j / n_), 0)), b + Vector((0, 0.55 * (1 - 0.6 * (j + 1) / n_), 0)), 0.1)
add_cyl(bm, 0.5, 1.2, "Y", tuple(TIP), seg=16)
BOOM = mesh_obj("CraneBoom", bm, M_YEL)
for o in (CRANE, BOOM): vis_s(o, C["clamshell"], C["panel"])
def bucket_z(s):
    if s < DIG0: return 2.5
    if s < C["then"]:
        u = 0.5 - 0.5 * math.cos(2 * math.pi * (s - DIG0) / 2.3)
        return 2.5 + (-trench_d(s) - 0.6 - 2.5) * u
    return 2.5
BUCKET = empty("Bucket")
bm = bmesh.new()
add_box(bm, -0.42, 0.42, -1.4, 1.4, 0.0, 2.6, 0); add_box(bm, -0.5, 0.5, -1.5, 1.5, 2.6, 3.0, 0)
for sy in (-1, 1):
    v0 = Vector((0, sy * 1.35, -0.9)); add_bar(bm, v0 + Vector((-0.38, 0, 0)), v0 + Vector((0.38, 0, 0)), 0.12, 1)
add_box(bm, -0.38, 0.38, -1.38, 1.38, -0.9, 0.0, 1)
BK = mesh_obj("BucketBody", bm, [M_DARK, M_STEEL], parent=BUCKET)
bake_loc_s(BUCKET, lambda s: (TRX, TRY, bucket_z(s)))
vis_s(BUCKET, C["clamshell"], C["then"])
# steel cage (dropped in), tremie pipe
bm = bmesh.new()
cx0, cx1, cy0, cy1, ch = -WX1 + 0.14, -WX0 - 0.14, 0.35, PANEL - 0.35, 23.0
for x in (cx0, cx1):
    y = cy0
    while y <= cy1 + 1e-3: add_box(bm, x - 0.025, x + 0.025, y - 0.025, y + 0.025, 0.0, ch); y += 0.45
z = 0.3
while z < ch:
    for x in (cx0, cx1): add_box(bm, x - 0.02, x + 0.02, cy0, cy1, z - 0.02, z + 0.02)
    add_box(bm, cx0, cx1, cy0 - 0.02, cy0 + 0.02, z - 0.02, z + 0.02); add_box(bm, cx0, cx1, cy1 - 0.02, cy1 + 0.02, z - 0.02, z + 0.02)
    z += 1.2
CAGE = mesh_obj("SteelCage", bm, M_REBAR)
CAGE_Z = lambda s: WALL_BOT + 0.3 + PW([(C["cage"] - 0.2, 27.0), (C["cage"] + 1.3, 0.0)])(s)
bake_loc_s(CAGE, lambda s: (0, 0, CAGE_Z(s)))
vis_s(CAGE, C["cage"] - 0.2, C["panel"])
# crane cable (to the bucket while digging, to the cage while lowering it)
CABLE = box("CraneCable", -0.03, 0.03, -0.03, 0.03, -1.0, 0.0, M_DARK); CABLE.location = TIP
def cable_len(s):
    if s < C["then"]: return TIP.z - (bucket_z(s) + 3.0)
    if s < C["concrete"]: return TIP.z - (CAGE_Z(s) + ch)
    return 2.0
bake_scale_s(CABLE, lambda s: (1, 1, max(0.05, cable_len(s))))
vis_s(CABLE, C["clamshell"], C["panel"])
bm = bmesh.new(); add_cyl(bm, 0.14, 26.5, "Z", (0, 0, 0), seg=16)
r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.15, radius2=0.7, depth=1.2); bmesh.ops.translate(bm, verts=r_["verts"], vec=(0, 0, 13.8))
TREMIE = mesh_obj("Tremie", bm, M_TREMIE)
bake_loc_s(TREMIE, lambda s: (TRX, TRY + 1.0, -9.9 + PW([(C["concrete"] - 0.6, 18.0), (C["concrete"], 0.0)])(s) + 0.85 * max(0.0, conc_top(s) - WALL_BOT) * 0.0))
vis_s(TREMIE, C["concrete"] - 0.6, CONC1 + 0.4)
glow(B_TREMIE, [(0, 0.0), *pulse(C["concrete"] + 0.1, 1.5, hold=1.2), (DUR, 0.0)])
glow(B_WET, [(0, 0.0), *pulse(C["bottom"], 0.4, hold=1.0), (DUR, 0.0)])

# arrows on the section face (flat, facing the camera at y = -0.06)
def arrow_obj(name, base, d, length, width, m_):
    bm = bmesh.new(); add_arrow(bm, (0, 0), d, length, width, y=0.0)
    o = mesh_obj(name, bm, m_); o.location = (base[0], -0.08, base[1]); return o
PUSH = []
for j, zz in enumerate((-4.0, -9.0, -14.0, -19.0)):
    for sx in (-1, 1):
        a = arrow_obj(f"Push{j}{sx}", (TRX + sx * 0.25, zz), (sx, 0), 2.4, 0.9, M_GOLDG); PUSH.append(a)
        t0 = C["pushes"] + 0.08 * j
        bake_scale(a, lambda t, t0=t0: (pop(t, t0, 0.25),) * 3); vis_fn(a, lambda t: T_PUSH[0] <= t < T_PUSH[1])
UPA = []
for j in range(3):
    a = arrow_obj(f"Up{j}", (TRX, -6.0 - 2.2 * j), (0, 1), 1.8, 0.8, M_CYANG); UPA.append(a)
    t0 = C["shoves"] + 0.1 * j
    bake_scale(a, lambda t, t0=t0: (pop(t, t0, 0.25),) * 3); vis_fn(a, lambda t: t0 <= t < C["panel"])
INA = arrow_obj("PumpIn", (TRX + 0.0, WALL_BOT + 0.5), (0, 1), 2.4, 0.8, M_GOLDG)
bake_scale(INA, lambda t: (pop(t, C["bottom"] - 0.1, 0.25),) * 3); vis_fn(INA, lambda t: C["bottom"] - 0.1 <= t < C["shoves"])
# slurry return: hose to a tank on the lane (Mantaflow overflow, laptop bake with --bake-fluid; rising box stand-in otherwise)
TANK = empty("SlurryTank", (-15.8, 4.0, 0.0))
bm = bmesh.new()
add_box(bm, -1.6, 1.6, -1.6, -1.45, 0.0, 2.6); add_box(bm, -1.6, 1.6, 1.45, 1.6, 0.0, 2.6); add_box(bm, -1.6, -1.45, -1.6, 1.6, 0.0, 2.6)
add_box(bm, 1.45, 1.6, -1.6, 1.6, 0.0, 2.6); add_box(bm, -1.6, 1.6, -1.6, 1.6, 0.0, 0.12)
TANK_B = mesh_obj("TankBody", bm, M_DARK, parent=TANK)
HOSE = poly_obj("SlurryHose", [(TRX - 0.2, 1.0, -0.2), (TRX - 0.6, 1.0, 1.2), (-14.2, 2.0, 3.0), (-14.6, 3.2, 2.8)], 0.12, M_DARK)
TANK_LVL = boxb("TankSlurry", -17.25, -14.35, 2.55, 5.45, 0.12, 2.3, M_SLURRY_T)
bake_scale_s(TANK_LVL, lambda s: (1, 1, grow(s, C["shoves"], CONC1 + 0.4) * 0.9 + 0.05))
FL_DOM = box("SlurryDomain", -17.3, -14.3, 2.5, 5.5, 0.12, 3.2, M_SLURRY)
FL_IN = cyl("SlurryInflow", 0.18, 0.3, "Z", (-14.8, 3.4, 2.75), M_SLURRY, seg=12)
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=64, start=F(C["shoves"] - 0.2), end=F(C["shoves"] + 3.6), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_IN.hide_render = True
for o in (TANK, HOSE): vis_s(o, C["concrete"] - 0.6, C["panel"])
if FLUID_BAKE: vis_s(FL_DOM, C["shoves"] - 0.2, C["panel"]); vis_s(TANK_LVL, 1e8)
else: vis_s(FL_DOM, 1e8); vis_s(TANK_LVL, C["shoves"], C["panel"])

# ================= decking: steel beams across the walls, deck panels on top =================
LIFT0 = C["dirt2"] - 0.35
def lift(s, t0, h=9.0, d=0.6): return 0.0 if s < t0 else h * ease((s - t0) / d)
BEAMS = []
NB = int((ENDW - 1.0) / 3.0)
for k in range(NB + 1):
    y = 1.5 + 3.0 * k
    if y > ENDW - 0.4: break
    bm = bmesh.new()
    add_box(bm, -WX1 + 0.05, WX1 - 0.05, y - 0.22, y + 0.22, -0.46, -0.40); add_box(bm, -WX1 + 0.05, WX1 - 0.05, y - 0.22, y + 0.22, -1.0, -0.94)
    add_box(bm, -WX1 + 0.05, WX1 - 0.05, y - 0.03, y + 0.03, -0.94, -0.46)
    o = mesh_obj(f"Beam{k}", bm, M_STEEL); BEAMS.append(o)
    t0 = C["beams"] - 0.5 + 0.035 * k
    bake_loc_s(o, lambda s, t0=t0: (0, 0, drop(s, t0, 7.0, 0.45) + lift(s, LIFT0 + 0.15, 9.0)))
    vis_s(o, t0, LIFT0 + 0.8)
DECK = []
NR = int(ENDW / 3.0)
for r in range(NR):
    bm = bmesh.new(); w = 2 * WX1 / 6
    for c in range(6): add_box(bm, -WX1 + c * w + 0.02, -WX1 + (c + 1) * w - 0.02, r * 3.0 + 0.02, (r + 1) * 3.0 - 0.02, -0.40, 0.0)
    o = mesh_obj(f"DeckRow{r}", bm, M_DECK); DECK.append(o)
    t0 = C["deck"] - 0.3 + 0.03 * r
    bake_loc_s(o, lambda s, t0=t0, r=r: (0, 0, drop(s, t0, 5.0, 0.4) + lift(s, LIFT0 + 0.02 * r, 9.0)))
    vis_s(o, t0, LIFT0 + 0.75)
# steel road plates left on the new asphalt (lifted on the last "deck")
PLATES = []
for j, (x0, y0) in enumerate(((-7.6, 10.0), (-4.4, 10.0), (-7.6, 16.4), (-4.4, 16.4))):
    o = box(f"RoadPlate{j}", x0, x0 + 3.0, y0, y0 + 6.2, 0.0, 0.05, M_PLATE); PLATES.append(o)
    bake_loc_s(o, lambda s, j=j: (0, 0, drop(s, C["street"] + 0.25, 2.0, 0.35) + lift(s, C["deck2"] + 0.08 * j, 6.0, 0.7)))
    vis_s(o, C["street"] + 0.25, C["deck2"] + 0.9)

# ================= utilities: water main + duct bank, hung from the beams =================
MAIN = cyl("WaterMain", 0.42, ENDW - 0.1, "Y", (-4.0, ENDW / 2 + 0.05, -2.0), M_PIPE, seg=32)
bm = bmesh.new()
for i in range(3):
    for j in range(2): add_cyl(bm, 0.11, ENDW - 0.1, "Y", (2.8 + 0.3 * i, ENDW / 2 + 0.05, -1.75 + 0.28 * j), seg=12)
DUCTS = mesh_obj("DuctBank", bm, M_DUCT)
glow(B_PIPE, [(0, 0.0), *pulse(C["water"], 1.5, hold=0.5), (DUR, 0.0)])
glow(B_DUCT, [(0, 0.0), *pulse(C["cables"], 1.5, hold=0.5), (DUR, 0.0)])
HANG = []
for k, b_ in enumerate(BEAMS):
    y = 1.5 + 3.0 * k
    bm = bmesh.new(); add_box(bm, -4.03, -3.97, y - 0.03, y + 0.03, -1.6, -1.0); add_box(bm, -4.5, -3.5, y - 0.06, y + 0.06, -2.48, -2.42)
    add_box(bm, -4.5, -4.44, y - 0.03, y + 0.03, -2.45, -1.6); add_box(bm, -3.56, -3.5, y - 0.03, y + 0.03, -2.45, -1.6)
    add_box(bm, 3.08, 3.14, y - 0.03, y + 0.03, -1.4, -1.0); add_box(bm, 2.6, 3.6, y - 0.05, y + 0.05, -1.95, -1.89)
    add_box(bm, 2.6, 2.66, y - 0.03, y + 0.03, -1.9, -1.4); add_box(bm, 3.54, 3.6, y - 0.03, y + 0.03, -1.9, -1.4)
    o = mesh_obj(f"Hanger{k}", bm, M_CYANG); HANG.append(o)
    t0 = C["hung"] + 0.03 * k
    bake_scale_s(o, lambda s, t0=t0: (1, 1, 1)); vis_s(o, t0, LIFT0 + 0.1)

# ================= excavator under the deck (rides the dig level) =================
EXC = empty("Excavator")
bm = bmesh.new()
add_box(bm, -1.7, -0.9, -2.2, 2.2, 0.0, 0.9, 1); add_box(bm, 0.9, 1.7, -2.2, 2.2, 0.0, 0.9, 1); add_box(bm, -1.3, 1.3, -1.6, 1.6, 0.9, 2.1, 0)
add_box(bm, -0.3, 1.2, -1.5, -0.2, 2.1, 3.1, 0)
EXC_B = mesh_obj("ExcBody", bm, [M_YEL, M_DARK], parent=EXC)
ARM = empty("ExcArm", (0.0, 1.2, 1.9), parent=EXC)
bm = bmesh.new(); add_bar(bm, (0, 0, 0), (0, 3.2, 1.6), 0.4); add_bar(bm, (0, 3.2, 1.6), (0, 5.0, -0.4), 0.32)
add_box(bm, -0.6, 0.6, 4.6, 5.5, -1.2, -0.3, 1)
ARM_B = mesh_obj("ExcArmBody", bm, [M_YEL, M_DARK], parent=ARM)
EXC_Y = 14.0
bake_loc_s(EXC, lambda s: (-2.5, EXC_Y, max(CORE_TOP(s), -DEPTH)))
bake_fn(ARM, "rotation_euler", 0, lambda t: 0.25 * math.sin(2 * math.pi * ST(t) / 2.6) - 0.1)
bake_fn(EXC, "rotation_euler", 2, lambda t: 0.35 * math.sin(2 * math.pi * ST(t) / 5.2))
vis_s(EXC, C["now"], C["at"])
DUST_E = sphere_mesh("DustEmitter", 0.5, 1)
DUST = obj_from("DustEmitter", DUST_E, M_SOIL)
bake_loc_s(DUST, lambda s: (-2.5, EXC_Y + 5.5, max(CORE_TOP(s), -DEPTH) + 0.3))
fx.particles(DUST, "dust", F(C["digging"] - 0.2), F(C["at"]), count=500)
vis_fn(DUST, lambda t: C["digging"] - 0.2 <= t < C["at"])

# ================= struts + walers (pop in as the dig passes each level, out bottom-first) =================
STRUT_IN = [first_s(lambda t, z=z: CORE_TOP(t) <= z - 1.0) for z in Z_S]
STRUT_OUT = [C["the"] + 0.35 * (2 - i) for i in range(3)]
STRUTS = []
for i, z in enumerate(Z_S):
    bm = bmesh.new(); y = 3.0
    while y < ENDW - 2.0:
        add_cyl(bm, 0.42, 2 * WX0 - 0.9, "X", (0, y, z), seg=20)
        for sx in (-1, 1): add_box(bm, sx * (WX0 - 0.45) - 0.25, sx * (WX0 - 0.45) + 0.25, y - 0.5, y + 0.5, z - 0.5, z + 0.5)
        y += 6.0
    for sx in (-1, 1): add_box(bm, sx * WX0 - (0.45 if sx > 0 else 0), sx * WX0 + (0.45 if sx < 0 else 0), 0.05, ENDW - 0.3, z - 0.45, z + 0.45)
    o = mesh_obj(f"StrutLevel{i}", bm, M_STRUT); STRUTS.append(o)
    ti, to = STRUT_IN[i], STRUT_OUT[i]
    bake_scale_s(o, lambda s, ti=ti, to=to: (grow(s, ti, ti + 0.35) if s < to else max(0.0005, 1 - ease((s - to) / 0.3)), 1, 1))
    vis_s(o, ti, to + 0.32)
glow(B_STRUT, [(0, 0.0), *pulse(C["brace"], 2.2, hold=1.4), (DUR, 0.0)])
INWARD = []
for j, zz in enumerate((-5.0, -12.0, -18.0)):
    for sx in (-1, 1):
        a = arrow_obj(f"Soil{j}{sx}", (sx * (WX1 + 4.2), zz), (-sx, 0), 3.2, 1.2, M_REDG); INWARD.append(a)
        t0 = C["fold"] - 0.5 + 0.06 * j
        bake_scale(a, lambda t, t0=t0: (pop(t, t0, 0.25),) * 3); vis_fn(a, lambda t, t0=t0: t0 <= t < C["at"])

# ================= the station: floor, tracks, platform, columns, roof =================
BASE = boxb("BaseSlab", -WX0, WX0, 0, ENDW, -DEPTH, BASE1, M_WET)
bake_scale_s(BASE, lambda s: (1, 1, grow(s, C["bottom2"] + 0.1, C["floor"] + 0.3))); vis_s(BASE, C["bottom2"] + 0.1)
bm = bmesh.new()
for sx in (-1, 1):
    y = 0.4
    while y < ENDW - 0.3: add_box(bm, sx * TX - 1.3, sx * TX + 1.3, y - 0.13, y + 0.13, BASE1, BASE1 + 0.18, 1); y += 0.7
    for dx in (-0.72, 0.72): add_box(bm, sx * TX + dx - 0.04, sx * TX + dx + 0.04, 0.05, L + 40, BASE1 + 0.18, BASE1 + 0.33, 0)
TRACKS = mesh_obj("Tracks", bm, [M_RAIL, M_TIE])
bake_scale_s(TRACKS, lambda s: (1, 1, grow(s, C["floor"] + 0.2, C["floor"] + 0.5))); TRACKS.location = (0, 0, 0)
vis_s(TRACKS, C["floor"] + 0.2)
PLAT = boxb("Platform", -3.2, 3.2, 1.0, ENDW - 3.0, BASE1, -18.4, M_TILE)
bm = bmesh.new()
for sx in (-1, 1): add_box(bm, sx * 3.2 - 0.3 * (sx > 0) - 0.0, sx * 3.2 + 0.3 * (sx < 0), 1.0, ENDW - 3.0, 0.0, 1.11)
EDGE = mesh_obj("PlatformEdge", bm, M_EDGE); EDGE.location = (0, 0, BASE1); par(EDGE, PLAT); EDGE.location = (0, 0, 0)
bake_scale_s(PLAT, lambda s: (1, 1, grow(s, C["station"] - 0.45, C["station"] - 0.1))); vis_s(PLAT, C["station"] - 0.45)
COLS = []
for k in range(int((ENDW - 6) / 6.0)):
    y = 6.0 + 6.0 * k
    for sx in (-1, 1):
        o = boxb(f"Column{k}{sx}", sx * 1.9 - 0.3, sx * 1.9 + 0.3, y - 0.3, y + 0.3, -18.4, ROOF0, M_CONC); COLS.append(o)
        t0 = C["station"] + 0.04 * k
        bake_scale_s(o, lambda s, t0=t0: (1, 1, grow(s, t0, t0 + 0.35))); vis_s(o, t0)
ROOF = box("RoofSlab", -WX0, WX0, 0, ENDW, ROOF0, ROOF1, M_CONC)
bake_loc_s(ROOF, lambda s: (0, 0, drop(s, C["roof"] - 0.35, 5.0, 0.4))); vis_s(ROOF, C["roof"] - 0.35)
MEZZ0, MEZZ1 = -12.3, -11.7
bm = bmesh.new(); add_box(bm, -WX0, WX0, 0, ENDW * 0.62, MEZZ0, MEZZ1)
for sx in (-1, 1): add_box(bm, sx * 3.25 - 0.05, sx * 3.25 + 0.05, 0, ENDW * 0.62, MEZZ1, MEZZ1 + 1.1)
MEZZ = mesh_obj("Mezzanine", bm, M_CONC)
bake_loc_s(MEZZ, lambda s: (0, 0, drop(s, C["station"] + 0.35, 4.0, 0.4))); vis_s(MEZZ, C["station"] + 0.35)
bm = bmesh.new()
for x in (-5.5, 0.0, 5.5):
    add_box(bm, x - 0.12, x + 0.12, 0.5, ENDW - 0.5, ROOF0 - 0.06, ROOF0)
    add_box(bm, x - 0.12, x + 0.12, 0.5, ENDW * 0.62 - 0.5, MEZZ0 - 0.06, MEZZ0)
LAMPS = mesh_obj("StationLamps", bm, M_LAMP); vis_s(LAMPS, C["roof"] - 0.35)
glow(B_LAMP, [(0, 0.0), (C["roof"] + 0.1, 0.0), (C["roof"] + 0.5, 3.0), (DUR, 3.0)])
st_d = bpy.data.lights.new("StationLight", "AREA"); st_d.size = 16; st_d.shape = "RECTANGLE"; st_d.size_y = 60
ST_L = bpy.data.objects.new("StationLight", st_d); scene.collection.objects.link(ST_L); ST_L.location = (0, ENDW / 2, MEZZ0 - 0.4)
for t_, v_ in [(0, 0.0), (C["roof"], 0.0), (C["roof"] + 0.5, 2200.0), (DUR, 2200.0)]:
    st_d.energy = v_; st_d.keyframe_insert("energy", frame=F(t_))

# ================= backfill + work lights =================
FILL = boxb("Backfill", -WX0, WX0, 0, ENDW, ROOF1, ROAD_T, M_FILL)
bake_scale_s(FILL, lambda s: (1, 1, grow(s, C["dirt2"], C["dirt2"] + 0.9))); vis_s(FILL, C["dirt2"])
WORK = []
for k, y in enumerate((5.0, 22.0, 40.0, 58.0)):
    ld = bpy.data.lights.new(f"WorkLight{k}", "POINT"); ld.color = (1.0, 0.85, 0.62); ld.shadow_soft_size = 0.6
    lo = bpy.data.objects.new(f"WorkLight{k}", ld); scene.collection.objects.link(lo); lo.location = (0.0, y, -2.6); WORK.append(ld)
    vals = [(2600.0 if C["now"] <= s < C["dirt2"] else 0.0) for s in SS]
    bake_scalar(ld, "energy", vals)

# ================= 68 ft depth bar (hook) =================
DBAR = box("DepthBar", WX0 - 1.6, WX0 - 0.9, -0.3, -0.1, -1.0, 0.0, M_GOLDG); DBAR.location = (0, 0, ROAD_T)
bake_scale(DBAR, lambda t: (1, 1, max(0.0005, (DEPTH + ROAD_T) * ease((t - C["under"] - 0.2) / (C["down"] - C["under"] - 0.2)))))
vis_fn(DBAR, lambda t: C["under"] + 0.2 <= t < C["and"])
bm = bmesh.new()
for zz in (ROAD_T, -DEPTH): add_box(bm, WX0 - 1.4, WX0 + 0.2, -0.3, -0.1, zz - 0.1, zz + 0.1)
DTICK = mesh_obj("DepthTicks", bm, M_GOLDG); vis_fn(DTICK, lambda t: C["sixty"] <= t < C["and"])

# ================= traffic (loops so frame 1 == last frame) =================
def car_mesh(name, k):
    bm = bmesh.new()
    add_box(bm, -0.9, 0.9, -2.2, 2.2, 0.28, 1.0, 0); add_box(bm, -0.8, 0.8, -1.2, 1.0, 1.0, 1.5, 1)
    for sx in (-1, 1):
        for sy in (-1.4, 1.4): add_cyl(bm, 0.33, 0.26, "X", (sx * 0.8, sy, 0.33), seg=14, mi=2)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (M_CARS[k % len(M_CARS)], M_GLASS, M_TYRE): me.materials.append(m_)
    return me
PER = DUR / max(1, round(DUR / 10.0))
Y0, Y1 = 1.0, 150.0
CAR_WINS = [(0.0, C["and"]), (C["traffic"] - 0.1, C["then2"]), (C["street"] + 0.5, C["thats"]), (C["and2"], DUR + 1)]
CARS = []
lanes = [(-7.2, 0.00), (-7.2, 0.50), (-3.4, 0.22), (-3.4, 0.72), (3.4, 0.10), (3.4, 0.61), (7.2, 0.36), (7.2, 0.86)]
for i, (x, ph) in enumerate(lanes):
    o = obj_from(f"Car{i}", car_mesh(f"CarMesh{i}", i))
    sgn = 1 if x < 0 else -1
    def ypos(t, ph=ph, sgn=sgn):
        u = ((t / PER) + ph) % 1.0
        return Y0 + (Y1 - Y0) * (u if sgn > 0 else 1 - u)
    bake_loc(o, lambda t, x=x, ypos=ypos: (x, ypos(t), 0.0))
    if sgn < 0: o.rotation_euler = (0, 0, math.pi)
    bake_scale(o, lambda t, ypos=ypos: (max(0.0005, min(1.0, (ypos(t) - Y0) / 3.0, (Y1 - ypos(t)) / 3.0)),) * 3)
    def on(t, x=x):
        if not any(a <= t < b for a, b in CAR_WINS): return False
        if C["street"] + 0.5 <= t < C["and2"] + 1.2 and -7.8 < x < -3.0: return False   # plates lane closed until they lift
        return True
    vis_fn(o, on); CARS.append(o)

# ================= train (pulls in for the 1904 beat) =================
TRAIN = empty("Train")
bm = bmesh.new()
for c in range(2):
    y0 = c * 18.6
    add_box(bm, -1.45, 1.45, y0, y0 + 18.0, 0.55, 3.9, 0)
    for k in range(5): add_box(bm, -1.47, 1.47, y0 + 1.2 + 3.3 * k, y0 + 3.4 + 3.3 * k, 2.1, 3.1, 1)
    add_box(bm, -1.3, 1.3, y0 + 0.5, y0 + 17.5, 0.3, 0.55, 2)
TR_B = mesh_obj("TrainBody", bm, [M_TRAIN, M_TWIN, M_DARK], parent=TRAIN)
bake_loc(TRAIN, lambda t: (TX, PW([(C["thats"], L + 6.0), (C["y1904"] + 0.4, 3.0)])(t), BASE1 + 0.33))
vis_fn(TRAIN, lambda t: T_INSIDE[0] <= t < T_INSIDE[1])

# ================= what-if set (x + 300): a hole with no walls caves in, the road and a car go with it =================
W = Vector((300.0, 0.0, 0.0))
WI = []
def wbox(name, x0, x1, y0, y1, z0, z1, m_):
    o = box(name, x0 + W.x, x1 + W.x, y0, y1, z0, z1, m_); WI.append(o); return o
W_FLOOR = wbox("W_Floor", -40, 40, 0, 30, -35, -DEPTH, M_SOIL_W)
W_RIGHT = wbox("W_Right", WX0, 40, 0, 30, -DEPTH, ROAD_T, M_SOIL_W)
W_LEFT = wbox("W_Left", -40, -15.5, 0, 30, -DEPTH, ROAD_T, M_SOIL_W)
wbox("W_RoadR", WX0, 20, 0, 30, ROAD_T, 0.0, M_ROAD); wbox("W_RoadL", -40, -15.5, 0, 30, ROAD_T, 0.0, M_ROAD)
wbox("W_Back", -15.5, WX0, 28.0, 30, -DEPTH, ROAD_T, M_SOIL_W)
CHUNKS = []
nzc = 8; hz = DEPTH / nzc
for iz in range(nzc):
    for ix in range(3):
        for iy in range(4):
            x0 = -15.5 + 2.0 * ix + 0.55 * iz
            ch_ = box(f"W_Chunk{iz}{ix}{iy}", -0.98, 0.98, -3.4, 3.4, -hz / 2 + 0.02, hz / 2 - 0.02, M_SOIL_W)
            ch_.location = (W.x + x0 + 1.0, 3.5 + 7.0 * iy, -DEPTH + hz * (iz + 0.5))
            ch_.rotation_euler = (random.uniform(-0.03, 0.03), random.uniform(0.06, 0.14), random.uniform(-0.03, 0.03))
            CHUNKS.append(ch_)
ROADP = []
for iy in range(4):
    rp = box(f"W_RoadSlab{iy}", -3.0, 3.0, -3.4, 3.4, -0.2, 0.2, M_ROAD); rp.location = (W.x - 12.5 + 3.9, 3.5 + 7.0 * iy, 0.3); ROADP.append(rp)
WCAR = obj_from("W_Car", car_mesh("W_CarMesh", 0)); WCAR.location = (W.x - 8.4, 10.5, 0.55)
fx.rigid(CHUNKS + ROADP + [WCAR], passive=[W_FLOOR, W_LEFT, W_RIGHT], mass=2.0, friction=0.6, bounce=0.05)
try:
    for o in CHUNKS + ROADP + [WCAR]: o.rigid_body.collision_margin = 0.02
    for o in ROADP + [WCAR]: o.rigid_body.mass = 1.0
except Exception: pass
for o in WI + CHUNKS + ROADP + [WCAR]: vis_fn(o, lambda t: T_FAIL[0] <= t < T_FAIL[1])
WDUST = obj_from("W_DustEmitter", DUST_E, M_SOIL_W, loc=(W.x - 6.0, 12.0, -DEPTH + 1.0))
fx.particles(WDUST, "dust", F(C["caved"]), F(C["so"]), count=700)
vis_fn(WDUST, lambda t: T_FAIL[0] <= t < T_FAIL[1])
RED_D = bpy.data.lights.new("RedFlash", "AREA"); RED_D.color = (1.0, 0.22, 0.14); RED_D.size = 12
RED_O = bpy.data.objects.new("RedFlash", RED_D); scene.collection.objects.link(RED_O); RED_O.location = (W.x - 6.0, -10.0, -4.0)
RED_O.rotation_euler = (math.radians(70), 0, 0)
for t_, v_ in [(0, 0.0), (C["caved"] - 0.05, 0.0), (C["caved"] + 0.1, 25000.0), (C["drop"], 12000.0), (C["so"] - 0.05, 12000.0), (C["so"], 0.0), (DUR, 0.0)]:
    RED_D.energy = v_; RED_D.keyframe_insert("energy", frame=F(t_))

# ================= fx: GN scatter of city blocks along the street =================
def bldg_inst():
    bm = bmesh.new(); add_box(bm, -6, 6, -6, 6, 0, 26, 0); add_box(bm, -6.05, 6.05, -6.05, 6.05, 26, 26.6, 1)
    return mesh_obj("BldgInst", bm, [M_FACADE, M_ROOFB])
BLDG = bldg_inst()
for k, (x0, x1, y0, y1, d) in enumerate(((22, 70, 8, 260, 0.0035), (-70, -22, 8, 260, 0.0035), (70, 200, 8, 420, 0.0012), (-200, -70, 8, 420, 0.0012))):
    s_ = plane(f"BldgScatter{k}", x0, x1, y0, y1, 0.14, M_PLAZA)
    fx.scatter(s_, BLDG, density=d, scale_min=0.7, scale_max=1.6, seed=3 + k)
BLDG.location = (0, 0, -900)

# ================= world: HDRI light + own sky gradient =================
fx.hdri("sunrise", strength=0.8, rotation_deg=200.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.05, 0.05, 0.06, 1); e[1].position = 0.42; e[1].color = (0.30, 0.50, 0.78, 1)
    eh = e.new(0.015); eh.color = (0.95, 0.70, 0.48, 1)
    wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.2; sun_d.color = (1.0, 0.90, 0.76); sun_d.angle = math.radians(1.5)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(58), 0, math.radians(28))
fx.glare(threshold=1.0, strength=0.5, size=7)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
HOOK_SHOT = ((19.0, -30.0, 6.0), (0.0, 14.0, -6.5), 22)
V = lambda a, b=(0, 0, 0): tuple(Vector(a) + Vector(b))
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK_SHOT),
    (C["under"] - 0.05, (16.5, -27.0, 4.5), (0.0, 14.0, -7.0), 22),
    (C["under"], (3.0, -34.0, -3.0), (0.0, 10.0, -9.0), 22, "cut"),
    (C["and"] - 0.05, (2.0, -31.0, -9.0), (0.0, 10.0, -13.0), 22),
    (C["and"], V(W, (-30.0, -30.0, 3.0)), V(W, (-8.0, 10.0, -8.0)), 22, "cut"),
    (C["so"] - 0.05, V(W, (-27.0, -27.0, 2.0)), V(W, (-7.0, 10.0, -10.0)), 22),
    (C["so"], (24.0, -36.0, 14.0), (0.0, 16.0, -8.0), 22, "cut"),
    (C["clamshell"] - 0.05, (20.0, -32.0, 11.0), (0.0, 16.0, -9.0), 22),
    (C["clamshell"], (-4.5, -17.0, 2.0), (-12.5, 4.0, -4.0), 22, "cut"),
    (C["it"] - 0.05, (-6.0, -15.0, -3.0), (-11.0, 3.0, -10.0), 22),
    (C["it"], (-7.6, -9.5, -9.0), (-WXC, 0.0, -10.5), 26, "cut"),
    (C["then"] - 0.05, (-7.8, -9.0, -14.0), (-WXC, 0.0, -15.0), 26),
    (C["then"], (-2.0, -27.0, 3.0), (-11.0, 3.0, -9.0), 22, "cut"),
    (C["panel"] - 0.05, (-3.5, -25.0, -2.0), (-11.0, 3.0, -11.0), 22),
    (C["panel"], (0.0, -22.0, -8.0), (0.0, 30.0, -12.0), 22, "cut"),
    (C["now"] - 0.05, (0.0, -15.0, -9.0), (0.0, 34.0, -12.0), 22),
    (C["now"], (17.0, -27.0, 8.0), (0.0, 10.0, -3.0), 24, "cut"),
    (C["water"] - 0.05, (13.0, -22.0, 6.0), (0.0, 12.0, -2.0), 24),
    (C["water"], (-1.0, -8.0, -2.2), (-1.8, 14.0, -1.6), 20, "cut"),
    (C["then2"] - 0.05, (-1.0, -4.5, -2.1), (-1.8, 16.0, -1.6), 20),
    (C["then2"], (5.0, -34.0, -7.0), (0.0, 10.0, -11.0), 22, "cut"),
    (C["at"] - 0.05, (3.0, -31.0, -10.0), (0.0, 10.0, -12.0), 22),
    (C["at"], (13.0, -30.0, -9.0), (0.0, 10.0, -12.0), 22, "cut"),
    (C["the"] - 0.05, (10.0, -27.0, -10.0), (0.0, 10.0, -12.5), 22),
    (C["the"], (21.0, -34.0, 4.0), (0.0, 10.0, -7.0), 22, "cut"),
    (C["thats"] - 0.05, (19.0, -31.0, 3.0), (0.0, 10.0, -7.0), 22),
    (C["thats"], (-1.6, -7.0, -16.4), (4.5, 40.0, -16.8), 20, "cut"),
    (C["and2"] - 0.05, (-1.6, -2.0, -16.4), (4.5, 40.0, -16.8), 20),
    (C["and2"], (-1.0, 2.5, 1.7), (-6.0, 16.0, 0.6), 24, "cut"),
    (C["normal"], (6.0, -14.0, 3.2), (0.0, 16.0, -2.0), 22),
    (C["whole"], HOOK_SHOT[0], HOOK_SHOT[1], HOOK_SHOT[2]),
    (DUR, *HOOK_SHOT),
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
    if T_FAIL[0] + 0.3 <= t < T_FAIL[1]:        # rumble while it caves in
        a = 0.12 * max(0.0, 1 - (t - T_FAIL[0]) / 3.5)
        l0 = l0 + Vector((a * math.sin(t * 47), 0, a * math.sin(t * 61)))
    cam_loc.append(l0); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 14; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(20.0, min(9000.0, 160.0 * ((cl - ct).length / 30.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (4, 5, 0)
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
fx.bake_rigid(F(C["and"]), F(C["so"]))
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "deck": (-3.0, 4.0, 0.2), "hole": (0.0, 2.0, -12.0), "depth_mid": (WX0 - 0.6, 0.0, -10.0),
    "w_road": (W.x - 12.0, 10.0, 0.6), "ghost_l": (-WXC, 0.0, -12.0), "ghost_r": (WXC, 0.0, -12.0),
    "bucket": (TRX, TRY, 3.0), "trench": (-WXC, 0.0, -8.0), "slurry": (-WXC, 0.0, -10.5), "cage": (-WXC, 0.0, -6.0),
    "tremie": (TRX, TRY + 1.0, 2.5), "tank": (-15.8, 4.0, 2.6), "panel_r": (WXC, 0.0, -12.0), "panels_far": (-WXC, 36.0, -12.0),
    "beam": (6.0, 1.5, -0.7), "deckp": (4.0, 6.0, 0.2), "main": (-4.0, 9.0, -2.0), "ducts": (3.1, 9.0, -1.6),
    "excavator": (-2.5, EXC_Y, -10.0), "strut": (0.0, 3.0, Z_S[1]), "wall_l": (-WXC, 0.0, -14.0), "floor": (0.0, 0.0, -20.1),
    "platform": (0.0, 1.0, -18.4), "roof": (0.0, 0.0, -5.4), "backfill": (0.0, 0.0, -2.6), "station": (0.0, 2.0, -12.0),
    "train": (TX, 20.0, -17.0), "plates": (-4.4, 13.0, 0.1),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "fail": RR(*T_FAIL), "cave": round(C["caved"], 3), "ghost": RR(*T_GHOST), "trench": RR(*T_TRENCH),
          "bucket_hits": [round(DIG0 + 2.3 * (j + 0.5), 3) for j in range(int((C["then"] - DIG0) / 2.3))],
          "push": RR(*T_PUSH), "cage_drop": round(C["cage"] - 0.2, 3), "cage_land": round(C["cage"] + 1.3, 3),
          "concrete": RR(CONC0, CONC1), "panels": [round(PANEL_T[p], 3) for p in ORDER[1:]], "deck": RR(*T_DECK),
          "beams": [round(C["beams"] - 0.05 + 0.035 * k, 3) for k in range(0, len(BEAMS), 4)],
          "deck_rows": [round(C["deck"] + 0.1 + 0.03 * r, 3) for r in range(0, NR, 4)], "util": RR(*T_UTIL),
          "hang": round(C["hung"], 3), "dig": RR(*T_DIG), "strut_in": [round(x, 3) for x in STRUT_IN],
          "build": RR(*T_BUILD), "floor": round(C["bottom2"] + 0.1, 3), "platform": round(C["station"] - 0.45, 3),
          "roof": round(C["roof"] + 0.05, 3), "strut_out": [round(x, 3) for x in STRUT_OUT], "backfill": round(C["dirt2"], 3),
          "deck_lift": round(LIFT0, 3), "asphalt": round(C["street"] + 0.45, 3), "inside": RR(*T_INSIDE),
          "train_stop": round(C["y1904"] + 0.4, 3), "end": RR(*T_END), "plates_lift": round(C["deck2"], 3)}
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
