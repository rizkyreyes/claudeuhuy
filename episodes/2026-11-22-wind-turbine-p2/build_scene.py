# Wind-Turbine-3D part 2: how a wind turbine makes power. Claim-first hook ("A wind turbine's blades are wings."):
# low front view of the spinning rotor, blades glow cyan -> airfoil studio: cut blade section, streamlines, lift arrow -> storm what-if: red
# overspeed, a blade tip breaks off (rigid body), rain -> wide sunrise shot of the finished turbine (part 1 recap) -> push into the nacelle
# cutaway -> airfoil studio again: low-pressure zone + lift arrow -> front view, rotor turns, gold tip ring (100+ mph) -> hub close (under
# 20 rpm) -> nacelle cutaway: main shaft (gold) -> two-stage gearbox (big gears turn small gears, optional Mantaflow oil splash) -> fast
# shaft (cyan) -> generator cutaway: magnets on the rotor sweep past copper coils, coils glow, cyan motes -> tower cut open: a cyan pulse runs
# down the cables to the pad transformer -> top view: wind arrows swing, vane turns, yaw motors glow, nacelle yaws 35 deg -> blade root close:
# gold pitch bearings, blades twist -> storm: rain, 55 mph, blades feather edge-on, rotor stops -> storm clears, blades twist back, camera
# returns to the first frame (loop: "...they twist back, because" -> "A wind turbine's blades are wings.").
# Illustrative (1 unit = 1 m): same turbine as part 1 (hub 103 m, blade 64 m). Drivetrain drawn as a generic geared turbine (some turbines are
# direct-drive, no gearbox); gear sizes and rotation speeds are visual (real output shaft > 1,000 rpm would be a blur).
# Generic turbine, no brand, no real place, no people.
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
random.seed(22)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')

CUES = [("a", "A"), ("blades", "blades"), ("wings", "wings."),
        ("they", "They"), ("spin", "spin"), ("lift", "lift,"), ("plane", "plane,"), ("and", "and"), ("storm", "storm,"), ("lift2", "lift"),
        ("wreck", "wreck"), ("machine", "machine."),
        ("yesterday", "Yesterday"), ("built", "built"), ("today", "Today,"), ("power", "power."),
        ("wind", "Wind"), ("flows", "flows"), ("curved", "curved"), ("air", "air"), ("pressure", "pressure"), ("side", "side"), ("drops", "drops."),
        ("that", "That"), ("difference", "difference"), ("pulls", "pulls"), ("forward", "forward,"), ("and2", "and"), ("rotor", "rotor"), ("turns", "turns."),
        ("out", "Out"), ("tips", "tips,"), ("move", "move"), ("hundred", "hundred"), ("hour", "hour."),
        ("but", "But"), ("hub", "hub"), ("slowly", "slowly,"), ("under", "under"), ("twenty", "twenty"), ("minute", "minute."),
        ("generator", "generator"), ("needs", "needs"), ("speed", "speed."),
        ("so", "So"), ("slow", "slow,"), ("main", "main"), ("shaft", "shaft"), ("gearbox", "gearbox."),
        ("big", "Big"), ("gears", "gears"), ("smaller", "smaller"), ("until", "until"), ("shaft2", "shaft"), ("spins", "spins"),
        ("thousand", "thousand"), ("minute2", "minute."),
        ("fast", "fast"), ("generator2", "generator:"), ("magnets", "magnets"), ("coils", "coils"), ("copper", "copper"),
        ("pushing", "pushing"), ("current", "current"),
        ("cables", "Cables"), ("down", "down"), ("tower", "tower"), ("transformer", "transformer"), ("base", "base."),
        ("now", "Now,"), ("changing", "changing"), ("direction", "direction."), ("vane", "vane"), ("roof", "roof"), ("tracks", "tracks"),
        ("yaw", "yaw"), ("motors", "motors"), ("nacelle", "nacelle"), ("face", "face"), ("wind2", "wind."),
        ("each", "Each"), ("blade", "blade"), ("twist", "twist"), ("bearing", "bearing."), ("pitch", "pitch,"), ("keeps", "keeps"),
        ("right", "right"), ("speed2", "speed."),
        ("above", "Above"), ("fiftyfive", "fifty-five"), ("hour2", "hour,"), ("blades2", "blades"), ("twist2", "twist"), ("edge", "edge-on,"),
        ("rotor2", "rotor"), ("slows", "slows"), ("turbine", "turbine"), ("waits", "waits"), ("storm2", "storm."),
        ("when", "When"), ("passes", "passes,"), ("twist3", "twist"), ("back", "back,"), ("because", "because")]
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
CL = coll("Turbine")
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

# ================= dimensions (1 unit = 1 m), same turbine as part 1 =================
Z_PED = 0.3
HUB_Z = 103.3
SEC_Z = [Z_PED, 22.3, 48.3, 75.3, HUB_Z]
R_T0, R_T1 = 2.25, 1.5
def r_tower(z): return R_T0 + (R_T1 - R_T0) * (z - Z_PED) / (HUB_Z - Z_PED)
BLADE = 64.0
HUB_L = Vector((0.0, -4.2, 2.4))                 # hub centre in nacelle (yaw) space; rotor faces -y
HUB = HUB_L + Vector((0, 0, HUB_Z))
ZA, ZB = 2.4, 0.95                               # main shaft axis, intermediate axis
ZC = ZB + 1.2                                    # high-speed axis
STUDIO = Vector((-600.0, 0.0, 400.0))              # airfoil studio set
W13 = 2 * math.pi * 13 / 60                      # rotor ~13 rpm

# ================= key times =================
T_STORM1 = (C["and"] - 0.05, C["yesterday"])                 # what-if storm (hook)
T_CLEAR1 = C["yesterday"]
T_FEATH0, T_FEATH1 = C["twist2"], C["edge"] + 0.5            # blades feather
T_STOP0, T_STOP1 = C["rotor2"], C["turbine"]                 # rotor slows to a stop
T_BACK0, T_BACK1 = C["twist3"], C["back"] + 0.55             # blades twist back
T_STORM2 = (C["above"] - 0.05, C["passes"] + 0.4)
T_YAW0, T_YAW1 = C["motors"], C["wind2"]
T_WINDDIR0, T_WINDDIR1 = C["changing"], C["direction"] + 0.6
T_PITCH0, T_PITCH1 = C["twist"], C["bearing"] + 0.2

# ================= materials =================
m_grass = mat("Grass", (0.20, 0.30, 0.10), 0.9, noise=6.0)[0]
m_soil, _ = mat("Soil", (0.16, 0.09, 0.045), 0.95, noise=3.0)
m_con, _ = mat("Concrete", (0.46, 0.46, 0.45), 0.7, noise=8.0)
m_tower, b_tower = mat("TowerWhite", (0.86, 0.87, 0.88), 0.35, emit_rgb=(0.30, 0.92, 1.0))
m_twin, _ = mat("TowerInside", (0.55, 0.56, 0.58), 0.5)
m_flange, b_flange = mat("Flange", (0.55, 0.56, 0.58), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
m_blade, b_blade = mat("Blade", (0.90, 0.91, 0.92), 0.3, emit_rgb=(0.30, 0.92, 1.0))
m_shaft, b_shaft = mat("MainShaft", (0.55, 0.50, 0.42), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
m_gear, b_gear = mat("Gears", (0.42, 0.34, 0.20), 0.35, 1.0, emit_rgb=(0.98, 0.74, 0.27))
m_hs, b_hs = mat("FastShaft", (0.50, 0.55, 0.60), 0.3, 1.0, emit_rgb=(0.30, 0.92, 1.0))
m_case, _ = mat("GearCase", (0.12, 0.13, 0.15), 0.5, 0.6)
m_copper, b_copper = mat("Copper", (0.78, 0.40, 0.18), 0.3, 1.0, emit_rgb=(0.30, 0.92, 1.0))
m_magN, b_magN = mat("MagnetN", (0.75, 0.10, 0.08), 0.35, 0.3, emit_rgb=(1.0, 0.30, 0.24))
m_magS, b_magS = mat("MagnetS", (0.10, 0.22, 0.70), 0.35, 0.3, emit_rgb=(0.30, 0.55, 1.0))
m_genrot, _ = mat("GenRotor", (0.20, 0.21, 0.23), 0.4, 0.8)
m_dark, _ = mat("DarkSteel", (0.08, 0.08, 0.09), 0.5, 0.6)
m_cab, _ = mat("Cabinet", (0.70, 0.72, 0.74), 0.5)
m_xf, b_xf = mat("Transformer", (0.22, 0.32, 0.26), 0.5, 0.2, emit_rgb=(0.30, 0.92, 1.0))
m_yawm, b_yawm = mat("YawMotor", (0.30, 0.32, 0.36), 0.4, 0.6, emit_rgb=(0.98, 0.74, 0.27))
m_vane, b_vane = mat("Vane", (0.20, 0.20, 0.22), 0.4, 0.5, emit_rgb=(0.98, 0.74, 0.27))
m_pitch, b_pitch = mat("PitchBearing", (0.50, 0.50, 0.52), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
m_red, b_red = mat("RedArrow", (1.0, 0.30, 0.24), 0.4, emit_rgb=(1.0, 0.30, 0.24))
m_gold, b_gold = mat("GoldArrow", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27))
m_cyan, b_cyan = mat("Cyan", (0.30, 0.92, 1.0), 0.4, emit_rgb=(0.30, 0.92, 1.0))
m_wind, b_wind = mat("WindArrow", (0.85, 0.97, 1.0), 0.4, emit_rgb=(0.85, 0.97, 1.0))
m_rock, _ = mat("Rock", (0.20, 0.19, 0.17), 0.8, noise=12.0)
m_tuft, _ = mat("Tuft", (0.26, 0.36, 0.12), 0.9)
m_back, _ = mat("StudioBackdrop", (0.025, 0.035, 0.055), 0.8)
m_foil, b_foil = mat("FoilSkin", (0.88, 0.89, 0.90), 0.35, emit_rgb=(0.30, 0.92, 1.0))
m_foilcut, _ = mat("FoilCore", (0.30, 0.32, 0.36), 0.6)
for b_ in (b_red, b_gold, b_cyan): b_.inputs["Emission Strength"].default_value = 3.0
b_wind.inputs["Emission Strength"].default_value = 2.5
low_m, low_fac = ghost("LowPressure", (0.30, 0.80, 1.0))
tip_m, tip_fac = ghost("TipRing", (0.98, 0.74, 0.27))

# ================= ground, pedestal, transformer =================
def grass_top(o_, top_mi=0, side_mi=1):
    for p in o_.data.polygons: p.material_index = top_mi if (p.normal.z > 0.9 and p.center.z > -0.05) else side_mi
GROUND = box("Ground", -4000, 4000, -4000, 4000, -3, 0, [m_grass, m_soil]); grass_top(GROUND)
PED = full_cyl("Pedestal", 3.2, 0, 0, -0.2, Z_PED, m_con, seg=48)
XF = box("PadTransformer", 6.0, 8.6, -4.6, -2.0, 0.0, 2.3, m_xf)
XF_FINS = box("TransformerFins", 8.6, 8.9, -4.3, -2.3, 0.3, 2.0, m_dark)
XF_PAD = box("TransformerPad", 5.6, 9.2, -5.0, -1.6, -0.05, 0.12, m_con)

# ================= tower: full shell + a cut-open half for the cable beat =================
T_WALL = 0.05 * 3
def tower_prof(z0, z1): return [(r_tower(z0) - T_WALL, z0), (r_tower(z0), z0), (r_tower(z1), z1), (r_tower(z1) - T_WALL, z1)]
T_CABLE = (C["cables"] - 0.05, C["now"] - 0.05)
TOWER = [lathe(f"Tower{i}", tower_prof(SEC_Z[i], SEC_Z[i + 1]), m_tower, ang=2 * math.pi, seg=48, smooth=True) for i in range(4)]
TOWER_CUT = [lathe(f"TowerCut{i}", tower_prof(SEC_Z[i], SEC_Z[i + 1]), m_twin, a0=-math.pi / 2, ang=math.pi, seg=24, smooth=True) for i in range(4)]
FLANGES = [lathe(f"Flange{i}", [(r_tower(z) - 0.35, z - 0.12), (r_tower(z) + 0.06, z - 0.12), (r_tower(z) + 0.06, z + 0.12), (r_tower(z) - 0.35, z + 0.12)],
                 m_flange, ang=2 * math.pi, seg=48, smooth=False) for i, z in enumerate(SEC_Z[1:4])]
PLATF = [lathe(f"Platform{i}", [(0, z - 0.6), (r_tower(z) - T_WALL, z - 0.6), (r_tower(z) - T_WALL, z - 0.45), (0, z - 0.45)], m_dark,
               a0=-math.pi / 2, ang=math.pi, seg=24, smooth=False) for i, z in enumerate(SEC_Z[1:4])]
for o_ in TOWER + FLANGES: windows(o_, [(0.0, T_CABLE[0]), (T_CABLE[1], DUR)])
for o_ in TOWER_CUT + PLATF: windows(o_, [T_CABLE])

# cables inside the tower: a cyan pulse runs down (shader: |z - PulseZ|)
m_cab3, b_cab3 = mat("PowerCable", (0.05, 0.05, 0.05), 0.4, 0.6, emit_rgb=(0.30, 0.92, 1.0))
def pulse_shader(m_, b_, name, keys, axis="Z", width=7.0, peak=9.0, base=0.0):
    nt = m_.node_tree
    tc = NODE(nt, "ShaderNodeTexCoord"); sep = NODE(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    pz = VALUE(nt, name, keys)
    d = MATH(nt, "ABSOLUTE", MATH(nt, "SUBTRACT", sep.outputs[axis], pz))
    s = MATH(nt, "MULTIPLY", MATH(nt, "SUBTRACT", 1.0, MATH(nt, "DIVIDE", d, width), clamp=True), peak)
    nt.links.new(MATH(nt, "ADD", s, base), b_.inputs["Emission Strength"])
P_TOP, P_BASE = C["cables"], C["transformer"] + 0.1
pulse_shader(m_cab3, b_cab3, "PulseZ", [(0, 400.0), (P_TOP - 0.05, 400.0), (P_TOP, HUB_Z + 4), (P_BASE, -2.0), (P_BASE + 0.3, -60.0), (DUR, -60.0)], width=9.0)
CABLES = []
for k, (cx, cy) in enumerate([(0.35, 0.55), (0.55, 0.35), (0.15, 0.70)]):
    o_ = cyl(f"TowerCable{k}", 0.07, HUB_Z - 0.6, "Z", (cx, cy, (HUB_Z + 0.6) / 2 + 0.3), m_cab3, seg=8); CABLES.append(o_)
m_gnd, b_gnd = mat("GroundCable", (0.05, 0.05, 0.05), 0.4, 0.6, emit_rgb=(0.30, 0.92, 1.0))
GCABLE = mesh_obj("BaseCable", (lambda bm: (add_bar(bm, (0.4, 0.5, 0.25), (0.4, -3.2, 0.25), 0.16), add_bar(bm, (0.4, -3.2, 0.25), (6.0, -3.2, 0.25), 0.16), bm)[-1])(bmesh.new()), m_gnd)
glow(b_gnd, [(0, 0.0), (C["transformer"] - 0.15, 0.0), (C["transformer"] + 0.1, 8.0), (C["now"] - 0.1, 3.0), (C["now"] + 0.3, 0.0)])
glow(b_xf, [(0, 0.0), (C["transformer"], 0.0), (C["transformer"] + 0.25, 2.5), (C["now"], 1.2), (C["now"] + 0.4, 0.0)])
for o_ in CABLES + [GCABLE]: windows(o_, [T_CABLE])

# ================= yaw system: static gear ring on the tower top, nacelle frame rotates about z =================
def gear_mesh(name, r, teeth, thick, m_, h=None, link=True):
    """Spur gear in the XZ plane, axis = local Y."""
    h = h or max(0.06, r * 0.12); bm = bmesh.new(); vs = []
    for k in range(teeth * 4):
        a = 2 * math.pi * k / (teeth * 4); rr = r + (h if k % 4 in (1, 2) else 0.0)
        vs.append(bm.verts.new((rr * math.cos(a), -thick / 2, rr * math.sin(a))))
    f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in ex["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0, thick, 0)); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_, link=link)
YAW_RING = gear_mesh("YawRing", 1.7, 60, 0.3, m_flange); YAW_RING.rotation_euler = (math.radians(90), 0, 0); YAW_RING.location = (0, 0, HUB_Z + 0.15)
YAW = empty("YawFrame", (0, 0, HUB_Z))
def yaw_angle(t):
    return math.radians(35) * (ease((t - T_YAW0) / (T_YAW1 - T_YAW0)) - ease((t - C["above"] - 0.3) / 2.2))
bake_fn(YAW, "rotation_euler", 2, yaw_angle)
def yaw_w(v, t):
    """nacelle-space point -> world at time t"""
    return Vector((0, 0, HUB_Z)) + Matrix.Rotation(yaw_angle(t), 3, "Z") @ Vector(v)

# ================= nacelle shell (cutaway: -x wall and the front roof removed) =================
def shell(bm):
    add_box(bm, -2.1, 2.1, -3.6, 9.0, 0.30, 0.45)          # floor
    add_box(bm, 1.98, 2.1, -3.6, 9.0, 0.45, 4.6)           # +x wall
    add_box(bm, -2.1, 2.1, -3.6, -3.48, 0.45, 4.6)         # front wall (shaft passes through)
    add_box(bm, -2.1, 2.1, 8.88, 9.0, 0.45, 4.6)           # back wall
    add_box(bm, -2.1, 2.1, 4.9, 9.0, 4.48, 4.6)            # rear roof (vane + anemometer)
    add_box(bm, -2.1, -1.98, 4.9, 9.0, 3.2, 4.48)          # short -x lip at the rear
NAC = mesh_obj("NacelleShell", (lambda bm: (shell(bm), bm)[-1])(bmesh.new()), m_tower); par(NAC, YAW)
MAINB = cyl("MainBearing", 0.85, 0.9, "Y", (0, -2.7, ZA), m_dark, parent=YAW, seg=32)
MAINB2 = box("BearingFoot", -0.7, 0.7, -3.1, -2.3, 0.45, ZA - 0.6, m_dark, parent=YAW)
SPINNERS = []                                                # objects that spin about their own local Y
def spinner(name, obj_fn, center, parent=YAW):
    e = empty(name, center, parent); o_ = obj_fn(); par(o_, e); SPINNERS.append(e); return e, o_
# main (slow) shaft + stage 1 big gear on axis A
SH_A, _ = spinner("ShaftA", lambda: cyl("MainShaftMesh", 0.42, 3.9, "Y", (0, -1.95, 0), m_shaft, seg=24), (0, -0.1, ZA))
G1E = empty("G1", (0, 0.0, ZA), YAW); G1 = gear_mesh("Gear1", 1.1, 33, 0.42, m_gear); par(G1, G1E)
# axis B: pinion 1 + big gear 2
P1E = empty("P1", (0, 0.0, ZB), YAW); P1 = gear_mesh("Pinion1", 0.35, 11, 0.42, m_gear); par(P1, P1E)
G2E = empty("G2", (0, 1.0, ZB), YAW); G2 = gear_mesh("Gear2", 0.9, 27, 0.36, m_gear); par(G2, G2E)
SHB = cyl("ShaftB", 0.13, 1.7, "Y", (0, 0.5, 0), m_gear, seg=12); par(SHB, P1E)
# axis C: pinion 2 + fast shaft
P2E = empty("P2", (0, 1.0, ZC), YAW); P2 = gear_mesh("Pinion2", 0.3, 9, 0.36, m_hs); par(P2, P2E)
SHC = cyl("FastShaftMesh", 0.16, 3.0, "Y", (0, 1.5, 0), m_hs, seg=16); par(SHC, P2E)
CASE = mesh_obj("GearCaseBack", (lambda bm: (add_box(bm, 1.35, 1.5, -0.7, 1.6, 0.45, 3.8), add_box(bm, -1.5, 1.5, -0.7, 1.6, 0.45, 0.6), bm)[-1])(bmesh.new()), m_case, parent=YAW)
# generator on axis C: rotor with magnets (spins with P2), stator copper coils (cut open on -x)
GEN_Y0, GEN_Y1 = 3.4, 6.0
def gen_rotor():
    bm = bmesh.new(); add_cyl(bm, 0.55, GEN_Y1 - GEN_Y0, "Y", (0, (GEN_Y0 + GEN_Y1) / 2 - 1.0, 0), seg=24, mi=0)
    for k in range(8):
        a = 2 * math.pi * k / 8; c, s = math.cos(a), math.sin(a)
        vs = add_box(bm, -0.07, 0.07, GEN_Y0 - 1.0 + 0.15, GEN_Y1 - 1.0 - 0.15, -0.17, 0.17, mi=1 + k % 2)
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(-a, 3, "Y"))
        bmesh.ops.translate(bm, verts=vs, vec=(0.62 * c, 0, 0.62 * s))
    return mesh_obj("GenRotor", bm, [m_genrot, m_magN, m_magS])
GENR = gen_rotor(); par(GENR, P2E)
def stator(bm):
    for k in range(14):
        a = 2 * math.pi * k / 14; c, s = math.cos(a), math.sin(a)
        if c < -0.15: continue                                  # cut open towards the camera (-x)
        vs = add_box(bm, -0.13, 0.13, GEN_Y0 + 0.1, GEN_Y1 - 0.1, -0.16, 0.16)
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(-a, 3, "Y"))
        bmesh.ops.translate(bm, verts=vs, vec=(0.92 * c, 0, ZC + 0.92 * s))
COILS = mesh_obj("StatorCoils", (lambda bm: (stator(bm), bm)[-1])(bmesh.new()), m_copper, parent=YAW)
GHOUSE = lathe("GenHousing", [(1.12, -1.3), (1.25, -1.3), (1.25, 1.3), (1.12, 1.3)], m_case, a0=-math.pi / 2, ang=math.pi, seg=24, smooth=False)
GHOUSE.rotation_euler = (math.radians(90), 0, 0); GHOUSE.location = (0, (GEN_Y0 + GEN_Y1) / 2, ZC); par(GHOUSE, YAW)
GEN_CAB = box("Converter", -1.2, 1.4, 6.8, 8.6, 0.45, 3.0, m_cab, parent=YAW)
m_ncab, b_ncab = mat("NacelleCable", (0.05, 0.05, 0.05), 0.4, 0.6, emit_rgb=(0.30, 0.92, 1.0))
glow(b_ncab, [(0, 0.0), (C["current"] - 0.2, 0.0), (C["current"] + 0.2, 6.0), (C["cables"] + 0.4, 6.0), (C["cables"] + 0.9, 0.0)])
NCABLE = mesh_obj("NacelleCable", (lambda bm: (add_bar(bm, (0.3, 5.5, ZC - 1.1), (0.3, 5.5, 0.5), 0.12), add_bar(bm, (0.3, 5.5, 0.5), (0.35, 0.55, 0.5), 0.12),
                  add_bar(bm, (0.35, 0.55, 0.5), (0.35, 0.55, -2.0), 0.12), bm)[-1])(bmesh.new()), m_ncab, parent=YAW)
# yaw motors (4) with pinions on the ring
YAWM = []
for k in range(4):
    a = math.radians(45 + 90 * k); x, y = 1.95 * math.cos(a), 1.95 * math.sin(a)
    o_ = mesh_obj(f"YawMotor{k}", (lambda bm: (add_cyl(bm, 0.24, 1.0, "Z", (x, y, 0.95), seg=16), add_cyl(bm, 0.28, 0.25, "Z", (x, y, 0.15), seg=12), bm)[-1])(bmesh.new()), m_yawm, parent=YAW)
    YAWM.append(o_)
# wind vane + anemometer on the rear roof
VANE_E = empty("VaneSpin", (0.9, 8.0, 4.6), YAW)
VANE = mesh_obj("Vane", (lambda bm: (add_cyl(bm, 0.05, 1.2, "Z", (0, 0, 0.6), seg=8), add_box(bm, -0.03, 0.03, 0.0, 0.9, 1.0, 1.5), add_bar(bm, (0, 0, 1.25), (0, -0.5, 1.25), 0.05), bm)[-1])(bmesh.new()), m_vane)
par(VANE, VANE_E)
ANEMO_E = empty("Anemometer", (-0.9, 8.0, 4.6), YAW)
ANEMO = mesh_obj("AnemoPole", (lambda bm: (add_cyl(bm, 0.05, 1.2, "Z", (0, 0, 0.6), seg=8), bm)[-1])(bmesh.new()), m_vane); par(ANEMO, ANEMO_E)
CUPS_E = empty("Cups", (0, 0, 1.25), ANEMO_E)
def cups(bm):
    for k in range(3):
        a = 2 * math.pi * k / 3; add_bar(bm, (0, 0, 0), (0.35 * math.cos(a), 0.35 * math.sin(a), 0), 0.03)
        add_cyl(bm, 0.09, 0.12, "X", (0.38 * math.cos(a), 0.38 * math.sin(a), 0), seg=10)
CUPS = mesh_obj("Cups", (lambda bm: (cups(bm), bm)[-1])(bmesh.new()), m_vane); par(CUPS, CUPS_E)
bake_fn(CUPS_E, "rotation_euler", 2, lambda t: 9.0 * t)
# the vane points into the wind: world wind direction (deg) minus the nacelle yaw
def wind_dir(t): return math.radians(35) * (ease((t - T_WINDDIR0) / (T_WINDDIR1 - T_WINDDIR0)) - ease((t - C["above"]) / 1.6))
bake_fn(VANE_E, "rotation_euler", 2, lambda t: wind_dir(t) - yaw_angle(t) + 0.04 * math.sin(t * 3.1))

# ================= rotor: hub, 3 airfoil blades with pitch bearings =================
def naca(t_c, m=0.04, p=0.4, n=28):
    """closed NACA-like loop (x 0..1 chord, y thickness), TE -> upper -> LE -> lower -> TE, n points"""
    pts = []
    for k in range(n):
        ph = 2 * math.pi * k / n; x = (1 + math.cos(ph)) / 2
        yt = 5 * t_c * (0.2969 * math.sqrt(x) - 0.1260 * x - 0.3516 * x * x + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        yc = m / p ** 2 * (2 * p * x - x * x) if x < p else m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x * x)
        pts.append((x, yc + (yt if k <= n // 2 else -yt)))
    return pts
NSEC = 28
def blade_mesh(name, link=True):
    bm = bmesh.new(); rings = []
    # (span z, chord, t/c or None = round root of that diameter, twist deg)
    secs = [(0.0, 2.5, None, 0), (2.4, 2.5, None, 0), (6.5, 4.2, 0.36, 16), (14.0, 4.0, 0.25, 11), (30.0, 3.0, 0.20, 6), (48.0, 1.9, 0.18, 2.5), (60.0, 1.0, 0.16, 0.5), (BLADE, 0.35, 0.14, 0)]
    for z, ch, tc, tw in secs:
        ring = []
        if tc is None:
            for k in range(NSEC):
                ph = 2 * math.pi * k / NSEC; ring.append(bm.verts.new((0.5 * ch * math.cos(ph), 0.5 * ch * math.sin(ph), z)))
        else:
            R_ = Matrix.Rotation(math.radians(tw), 3, "Z")
            for x, y in naca(tc, n=NSEC):
                ring.append(bm.verts.new(R_ @ Vector(((x - 0.35) * ch, y * ch, z))))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(NSEC): bm.faces.new([r0[k], r0[(k + 1) % NSEC], r1[(k + 1) % NSEC], r1[k]])
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o_ = mesh_obj(name, bm, m_blade, link=link)
    try: o_.data.shade_smooth(); o_.data.set_sharp_from_angle(angle=math.radians(50))
    except Exception: pass
    return o_
ROT = empty("Rotor", tuple(HUB_L), YAW)
ROT_SPIN = empty("RotorSpin"); par(ROT_SPIN, ROT)
ROT_HUB = lathe("RotorHub", [(0, 0), (1.7, 0), (1.8, 1.2), (1.4, 3.0), (0.5, 4.2), (0, 4.5)], m_tower, ang=2 * math.pi, seg=32)
ROT_HUB.rotation_euler = (math.radians(90), 0, 0); ROT_HUB.location = (0, 1.3, 0); par(ROT_HUB, ROT_SPIN)
BLADES, PITCH_RINGS = [], []
for k in range(3):
    piv = empty(f"BladePiv{k}"); par(piv, ROT_SPIN); piv.rotation_euler = (0, math.radians(120 * k), 0)
    b_ = blade_mesh(f"Blade{k}"); par(b_, piv); b_.location = (0, 0, 1.45); BLADES.append(b_)
    pr = lathe(f"PitchBearing{k}", [(1.18, 1.25), (1.42, 1.25), (1.42, 1.65), (1.18, 1.65)], m_pitch, ang=2 * math.pi, seg=32, smooth=False); par(pr, piv)
    PITCH_RINGS.append(pr)
def pitch_deg(t):
    p = 22.0 * ease((t - T_PITCH0) / 0.8) - 14.0 * ease((t - C["keeps"]) / 0.9) - 8.0 * ease((t - C["speed2"]) / 0.7)
    p += 86.0 * ease((t - T_FEATH0) / (T_FEATH1 - T_FEATH0)) - 86.0 * ease((t - T_BACK0) / (T_BACK1 - T_BACK0))
    return p
for b_ in BLADES: bake_fn(b_, "rotation_euler", 2, lambda t: math.radians(pitch_deg(t)))
# spin: ~13 rpm; what-if overspeed in the storm hook; slows to a stop when feathered; restarts; ends on a 120-deg multiple (loop)
def omega(t):
    w = W13
    if T_STORM1[0] + 0.2 <= t < T_STORM1[1]: w = W13 * (1 + 2.2 * ease((t - T_STORM1[0] - 0.2) / 0.6))
    if t >= T_STOP0: w = W13 * (1 - ease((t - T_STOP0) / (T_STOP1 - T_STOP0)))
    if t >= T_BACK0: w = W13 * ease((t - T_BACK0) / (DUR - T_BACK0))
    return w
ANG = [0.0]
for t0_, t1_ in zip(TS, TS[1:]): ANG.append(ANG[-1] + omega(t0_) / FPS)
step = 2 * math.pi / 3; corr = (-ANG[-1]) % step                # forward nudge to a 120-deg multiple
T_CORR = T_BACK0
ANG = [a + corr * ease((t - T_CORR) / (DUR - T_CORR)) for a, t in zip(ANG, TS)]
bake(ROT_SPIN, "rotation_euler", 1, ANG)
spin_at = lambda t: ANG[min(len(ANG) - 1, max(0, int(round(t * FPS))))]
# drivetrain speeds follow the rotor (visual ratios ~3.1x per stage)
R1, R2 = 1.1 / 0.35, 0.9 / 0.3
bake(SH_A, "rotation_euler", 1, ANG)
bake(G1E, "rotation_euler", 1, ANG)
bake(P1E, "rotation_euler", 1, [-a * R1 + math.pi / 11 for a in ANG])
bake(G2E, "rotation_euler", 1, [-a * R1 for a in ANG])
bake(P2E, "rotation_euler", 1, [a * R1 * R2 for a in ANG])
# blade glow: cyan "wings" in the hook, red in the storm what-if, gold tips later
glow(b_blade, [(0, 0.0), (C["wings"] - 0.2, 0.0), (C["wings"] + 0.1, 1.6), (C["they"], 1.6), (C["they"] + 0.4, 0.0),
               (C["wreck"] - 0.3, 0.0), (C["wreck"], 1.4), (C["yesterday"] - 0.1, 1.4), (C["yesterday"], 0.0)])
ec = b_blade.inputs["Emission Color"]
for t_, col in [(0, (0.30, 0.92, 1.0, 1)), (C["and"], (0.30, 0.92, 1.0, 1)), (C["and"] + 0.05, (1.0, 0.30, 0.24, 1)), (C["yesterday"], (1.0, 0.30, 0.24, 1)), (C["yesterday"] + 0.05, (0.30, 0.92, 1.0, 1))]:
    ec.default_value = col; ec.keyframe_insert("default_value", frame=F(t_))
glow(b_pitch, [(0, 0.0), (C["bearing"] - 0.9, 0.0), (C["bearing"] - 0.5, 3.0), (C["speed2"], 3.0), (C["above"], 0.0),
               (C["twist2"] - 0.1, 0.0), (C["twist2"] + 0.2, 3.0), (C["slows"], 3.0), (C["slows"] + 0.5, 0.0)])
# gold ring along the blade-tip path (tips > 100 mph)
TIPR = lathe("TipRing", [(BLADE + 0.6, -0.25), (BLADE + 2.2, -0.25), (BLADE + 2.2, 0.25), (BLADE + 0.6, 0.25)], tip_m, ang=2 * math.pi, seg=96, smooth=False)
TIPR.rotation_euler = (math.radians(90), 0, 0); TIPR.location = (0, -0.5, 0); par(TIPR, ROT)
keyval(tip_fac, [(0, 0.0), (C["tips"] - 0.2, 0.0), (C["tips"] + 0.3, 0.9), (C["but"], 0.9), (C["but"] + 0.3, 0.0)])
windows(TIPR, [(C["tips"] - 0.3, C["but"] + 0.35)])

# ================= drivetrain glows =================
glow(b_shaft, [(0, 0.0), (C["main"] - 0.2, 0.0), (C["main"] + 0.1, 1.6), (C["big"], 0.6), (C["fast"], 0.0)])
glow(b_gear, [(0, 0.0), (C["gearbox"] - 0.1, 0.0), (C["gearbox"] + 0.2, 0.7), (C["until"], 0.35), (C["fast"], 0.0)])
glow(b_hs, [(0, 0.0), (C["shaft2"] - 0.2, 0.0), (C["shaft2"] + 0.1, 2.0), (C["magnets"], 1.0), (C["cables"], 0.0)])
glow(b_copper, [(0, 0.0), (C["coils"] - 0.2, 0.0), (C["coils"] + 0.2, 2.2), (C["current"], 4.0), (C["cables"] + 0.4, 0.0)])
glow(b_magN, [(0, 0.0), (C["magnets"] - 0.1, 0.0), (C["magnets"] + 0.2, 2.0), (C["coils"] + 0.3, 0.6), (C["cables"], 0.0)])
glow(b_magS, [(0, 0.0), (C["magnets"] - 0.1, 0.0), (C["magnets"] + 0.2, 2.0), (C["coils"] + 0.3, 0.6), (C["cables"], 0.0)])
glow(b_yawm, [(0, 0.0), (C["yaw"] - 0.1, 0.0), (C["yaw"] + 0.2, 3.0), (C["face"] + 0.3, 3.0), (C["each"], 0.0)])
glow(b_vane, [(0, 0.0), (C["vane"] - 0.1, 0.0), (C["vane"] + 0.2, 2.5), (C["yaw"], 2.5), (C["yaw"] + 0.4, 0.0)])

# ================= wind arrows (yaw beat) and storm gust arrows =================
WIND = empty("WindDir", (0, 0, HUB_Z + 9.0))
bake_fn(WIND, "rotation_euler", 2, wind_dir)
def flat_arrow(name, base_xy, length, width, m_, parent):
    bm = bmesh.new(); add_arrow(bm, (base_xy[0], base_xy[1]), (0, 1), length, width, y=0.0)
    o_ = mesh_obj(name, bm, m_); par(o_, parent); o_.rotation_euler = (math.radians(-90), 0, 0); return o_
# arrow drawn in XZ then rotated so that +z (arrow direction) maps to +y: wind blows from -y towards the rotor
WARROWS = []
for k, (x, z0) in enumerate([(-15.0, -44.0), (0.0, -52.0), (15.0, -46.0)]):
    o_ = flat_arrow(f"WindArrow{k}", (x, 0.0), 20.0, 7.0, m_wind, WIND); o_.location = (0, z0, 0); WARROWS.append(o_)
    bake_fn(o_, "location", 1, (lambda z0_: (lambda t: z0_ + ((t * 9.0) % 12.0)))(z0))
    windows(o_, [(C["now"] - 0.05, C["each"] - 0.05)])

# ================= storm what-if: blade tip fragments (rigid body) =================
RB0 = F(C["wreck"])
FRAGS = []
tip0 = HUB + Vector((math.sin(spin_at(C["wreck"])) * (BLADE + 1.0), 0, math.cos(spin_at(C["wreck"])) * (BLADE + 1.0)))
for k in range(6):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * random.uniform(0.6, 1.4), v.co.y * 0.3, v.co.z * random.uniform(1.0, 2.6)))
    o_ = mesh_obj(f"TipFrag{k}", bm, m_blade); o_.location = tip0 + Vector((random.uniform(-1.5, 1.5), random.uniform(-0.6, 0.6), -k * 2.4))
    o_.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3)); FRAGS.append(o_)
fx.rigid(FRAGS, passive=[GROUND], mass=40.0, friction=0.6, bounce=0.2)
for o_ in FRAGS: windows(o_, [(C["wreck"], C["yesterday"])])

# ================= airfoil studio (x = -600): cut blade section, streamlines, low pressure, lift arrow =================
T_STU = [(C["they"] - 0.05, C["and"] - 0.05), (C["wind"] - 0.05, C["and2"] - 0.05)]
CH, AOA, SPAN = 10.0, math.radians(7.0), 5.0
FOIL = [Vector(((x - 0.35) * CH, 0, y * CH)) for x, y in naca(0.16, m=0.05, p=0.4, n=64)]
FOIL = [Matrix.Rotation(AOA, 3, "Y") @ p for p in FOIL]       # nose up (camera looks along +y)
def foil_obj():
    bm = bmesh.new()
    front = [bm.verts.new(p + Vector((0, -SPAN / 2, 0))) for p in FOIL]
    back = [bm.verts.new(p + Vector((0, SPAN / 2, 0))) for p in FOIL]
    n = len(FOIL)
    for k in range(n): bm.faces.new([front[k], front[(k + 1) % n], back[(k + 1) % n], back[k]]).material_index = 0
    bm.faces.new(list(reversed(front))).material_index = 1; bm.faces.new(back).material_index = 0
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o_ = mesh_obj("StudioFoil", bm, [m_foil, m_foilcut]); o_.location = STUDIO; return o_
SFOIL = foil_obj()
OUTL = mesh_obj("FoilOutline", (lambda bm: ([add_bar(bm, FOIL[k] + Vector((0, -SPAN / 2 - 0.04, 0)), FOIL[(k + 1) % len(FOIL)] + Vector((0, -SPAN / 2 - 0.04, 0)), 0.09) for k in range(len(FOIL))], bm)[-1])(bmesh.new()), m_cyan)
OUTL.location = STUDIO
def surf(x, upper=True):
    """foil surface height at x (studio local), 0 outside the chord"""
    pts = FOIL[:len(FOIL) // 2 + 1] if upper else FOIL[len(FOIL) // 2:] + [FOIL[0]]
    best = None
    for p0, p1 in zip(pts, pts[1:]):
        lo_, hi_ = sorted((p0.x, p1.x))
        if lo_ <= x <= hi_ and hi_ > lo_:
            z = p0.z + (p1.z - p0.z) * (x - p0.x) / (p1.x - p0.x)
            best = z if best is None else (max(best, z) if upper else min(best, z))
    return best
def stream(d, upper=True, x0=-16.0, x1=16.0, n=90):
    pts = []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        acc, wsum = 0.0, 0.0                                   # smoothed surface (gaussian over x)
        for j in range(-6, 7):
            s = surf(x + j * 0.5, upper); g = math.exp(-(j * 0.5) ** 2 / 2.2)
            if s is None: s = 0.0
            acc += s * g; wsum += g
        base = acc / wsum; decay = math.exp(-abs(d) / 3.5)
        pts.append(Vector((x, -SPAN / 2 - 0.3, d + base * decay * (1.25 if upper else 1.0))))
    return pts
m_su, b_su = mat("StreamUpper", (0.30, 0.92, 1.0), 0.4, emit_rgb=(0.30, 0.92, 1.0))
m_sl, b_sl = mat("StreamLower", (0.85, 0.97, 1.0), 0.4, emit_rgb=(0.85, 0.97, 1.0))
def stripe_shader(m_, b_, name, speed, base=0.4, peak=6.0):
    nt = m_.node_tree
    tc = NODE(nt, "ShaderNodeTexCoord"); sep = NODE(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    prefs.keyframe_new_interpolation_type = "LINEAR"
    off = VALUE(nt, name, [(0, 0.0), (DUR, speed * DUR)])
    prefs.keyframe_new_interpolation_type = "BEZIER"
    fr = MATH(nt, "FRACT", MATH(nt, "DIVIDE", MATH(nt, "SUBTRACT", sep.outputs["X"], off), 2.4))
    st = MATH(nt, "MULTIPLY", MATH(nt, "LESS_THAN", fr, 0.45), peak)
    nt.links.new(MATH(nt, "ADD", st, base), b_.inputs["Emission Strength"])
stripe_shader(m_su, b_su, "FlowUpper", 9.0); stripe_shader(m_sl, b_sl, "FlowLower", 5.5)
STREAMS = []
for k, d in enumerate([0.9, 2.2, 3.8, 5.6]):
    bm = bmesh.new(); pts = stream(d, True)
    for p0, p1 in zip(pts, pts[1:]): add_bar(bm, p0, p1, 0.11)
    o_ = mesh_obj(f"StreamUp{k}", bm, m_su); o_.location = STUDIO; STREAMS.append(o_)
for k, d in enumerate([-1.1, -2.6, -4.4]):
    bm = bmesh.new(); pts = stream(d, False)
    for p0, p1 in zip(pts, pts[1:]): add_bar(bm, p0, p1, 0.11)
    o_ = mesh_obj(f"StreamLow{k}", bm, m_sl); o_.location = STUDIO; STREAMS.append(o_)
LOWZ = mesh_obj("LowPressureZone", (lambda bm: (bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0), bm)[-1])(bmesh.new()), low_m)
LOWZ.scale = (5.2, 0.4, 1.5); LOWZ.location = STUDIO + Vector((-0.6, -SPAN / 2 - 0.6, 2.0))
keyval(low_fac, [(0, 0.0), (C["pressure"] - 0.1, 0.0), (C["drops"], 0.75), (C["and2"], 0.75)])
bm = bmesh.new(); add_arrow(bm, (-0.3, 2.0), (-0.12, 1.0), 4.2, 1.5, y=-SPAN / 2 - 0.9)
m_lift, b_lift = mat("LiftArrow", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27)); b_lift.inputs["Emission Strength"].default_value = 1.2
LIFT = mesh_obj("LiftArrow", bm, m_lift); LIFT.location = STUDIO
bake_scale(LIFT, lambda t: (pop(t, C["lift"] - 0.1),) * 3 if t < C["wind"] - 0.1 else (pop(t, C["pulls"] - 0.1),) * 3)
BACKDROP = box("StudioBackdrop", -80, 80, 14, 15, -60, 60, m_back); BACKDROP.location = STUDIO
STUDIO_FLOOR = box("StudioFloor", -80, 80, -60, 15, -14, -13, m_back); STUDIO_FLOOR.location = STUDIO
for o_ in [SFOIL, OUTL, LIFT, BACKDROP, STUDIO_FLOOR] + STREAMS: windows(o_, T_STU)
for o_ in [LOWZ]: windows(o_, [(C["pressure"] - 0.2, C["and2"] - 0.05)])
SKEY_D = bpy.data.lights.new("StudioKey", "AREA"); SKEY_D.size = 30; SKEY_D.energy = 60000; SKEY = bpy.data.objects.new("StudioKey", SKEY_D)
scene.collection.objects.link(SKEY); SKEY.location = STUDIO + Vector((-10, -30, 25)); SKEY.rotation_euler = (math.radians(50), 0, math.radians(-18))

# ================= particles: rain (2 storms), cyan motes at the coils =================
def rain_box(name, t0, t1, n):
    o_ = box(name, -75, 5, -140, -40, 0, 120, m_dark)
    mod = fx.particles(o_, "rain", F(t0), F(t1), count=n)
    try:
        ps = mod.particle_system.settings; ps.emit_from = "VOLUME"; ps.particle_size = 0.08; ps.lifetime = 30
        ps.normal_factor = 0.0; ps.object_align_factor = (0.0, 0.0, -14.0)
        dot = ps.instance_object; dot.scale = (0.5, 0.5, 12.0); ps.use_scale_instance = True; ps.use_rotation_instance = False
        bd = bsdf_of(dot.data.materials[0]); bd.inputs["Emission Color"].default_value = (0.75, 0.85, 1.0, 1); bd.inputs["Emission Strength"].default_value = 0.45
        o_.show_instancer_for_render = False; o_.show_instancer_for_viewport = False
    except Exception as e: print("[build] rain tweak", e)
    return o_
RAIN1 = rain_box("RainVolume1", T_STORM1[0] - 1.0, T_STORM1[1], 90000)
RAIN2 = rain_box("RainVolume2", T_STORM2[0] - 1.0, T_STORM2[1], 120000)
MOTE_EM = cyl("MoteEmitter", 1.0, 2.2, "Y", (0, (GEN_Y0 + GEN_Y1) / 2, ZC), m_dark, parent=YAW, seg=16)
mod = fx.particles(MOTE_EM, "dust", F(C["coils"]), F(C["cables"]), count=500)
try:
    ps = mod.particle_system.settings; ps.particle_size = 0.025; ps.lifetime = 30; ps.normal_factor = 0.8; ps.effector_weights.gravity = 0.0
    mm = ps.instance_object.data.materials[0]; bb = bsdf_of(mm)
    bb.inputs["Base Color"].default_value = (0.3, 0.92, 1.0, 1); bb.inputs["Emission Color"].default_value = (0.3, 0.92, 1.0, 1); bb.inputs["Emission Strength"].default_value = 12.0
except Exception as e: print("[build] mote tweak", e)
MOTE_EM.show_instancer_for_render = False; MOTE_EM.show_instancer_for_viewport = False

# ================= Mantaflow: gear-oil splash in the gearbox sump (one short shot, bake on the laptop) =================
FLUID_BAKE = "--bake-fluid" in ARGS
FL_DOM = box("FluidDomain", -1.4, 1.4, -0.6, 1.6, HUB_Z + 0.45, HUB_Z + 2.2, m_hs)
FL_IN = box("FluidInflow", -0.3, 0.3, 0.6, 1.2, HUB_Z + 1.6, HUB_Z + 1.9, m_hs); FL_IN.hide_render = True
m_oil, _ = mat("GearOil", (0.55, 0.38, 0.08), 0.1, 0.0)
FL_DOM.data.materials.clear(); FL_DOM.data.materials.append(m_oil)
fx.fluid_domain(FL_DOM, FL_IN, eff=[P1, G2], res=64, start=F(C["big"]), end=F(C["minute2"]), cache_dir=os.path.join(HERE, "cache_fluid"))
_has_cache = os.path.isdir(os.path.join(HERE, "cache_fluid")) and any(os.scandir(os.path.join(HERE, "cache_fluid")))
if FLUID_BAKE or _has_cache: windows(FL_DOM, [(C["big"], C["fast"] - 0.05)])
else: FL_DOM.hide_render = True; FL_DOM.hide_viewport = True; print("[build] fluid domain hidden (no cache): bake on the laptop with --bake-fluid")

# ================= Geometry Nodes scatter: rocks, grass tufts, a distant wind farm =================
rk = bmesh.new(); bmesh.ops.create_icosphere(rk, subdivisions=1, radius=0.18)
for v in rk.verts: v.co.z *= 0.6
ROCK = mesh_obj("RockInst", rk, m_rock)
tf = bmesh.new()
for k in range(5):
    a = 2 * math.pi * k / 5; add_bar(tf, (0, 0, 0), (0.12 * math.cos(a), 0.12 * math.sin(a), 0.35), 0.03)
TUFT = mesh_obj("TuftInst", tf, m_tuft)
ft = bmesh.new(); add_cyl(ft, 2.2, 100.0, "Z", (0, 0, 50.0), seg=10, r2=1.4); add_box(ft, -1.6, 1.6, -2.0, 7.0, 100.0, 104.0)
for k in range(3):
    a = math.radians(120 * k + 35); add_bar(ft, (0, -2.6, 102.0), (60 * math.sin(a), -2.6, 102.0 + 60 * math.cos(a)), 1.4)
FARM = mesh_obj("FarTurbineInst", ft, m_tower)
SC1 = box("ScatterNear", -60, 60, -60, 40, -0.04, -0.03, m_grass)
SC2 = box("ScatterTufts", -80, 40, -120, -8, -0.04, -0.03, m_grass)
SC3 = box("ScatterFar", -1600, 1600, 700, 1700, -0.04, -0.03, m_grass)
fx.scatter(SC1, ROCK, density=0.02, scale_min=1.0, scale_max=2.5, seed=4)
fx.scatter(SC2, TUFT, density=1.0, scale_min=0.7, scale_max=1.5, seed=6)
fx.scatter(SC3, FARM, density=0.000005, scale_min=0.9, scale_max=1.1, seed=9)

# ================= world: sunset HDRI light + own sky gradient, mixed to a storm sky =================
fx.hdri("sunset", strength=0.7, rotation_deg=200.0, show_background=False)
STORM_KEYS = [(0, 0.0), (T_STORM1[0], 0.0), (T_STORM1[0] + 0.25, 1.0), (T_STORM1[1] - 0.05, 1.0), (T_STORM1[1], 0.0),
              (T_STORM2[0] - 0.05, 0.0), (T_STORM2[0], 1.0), (C["passes"] - 0.2, 1.0), (T_BACK1 + 0.3, 0.0), (DUR, 0.0)]
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    hdr_bg = next(n for n in wn if n.type == "BACKGROUND" and n is not plain)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    def ramp(cols):
        cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
        e[0].position = 0.0; e[0].color = cols[0]; e[1].position = 0.40; e[1].color = cols[1]
        wl.new(grad.outputs["Fac"], cr.inputs[0]); return cr
    clear = ramp([(1.0, 0.62, 0.38, 1), (0.22, 0.36, 0.70, 1)])
    storm = ramp([(0.16, 0.17, 0.20, 1), (0.05, 0.06, 0.08, 1)])
    mx = wn.new("ShaderNodeMix"); mx.data_type = "RGBA"
    wl.new(clear.outputs[0], mx.inputs[6]); wl.new(storm.outputs[0], mx.inputs[7]); wl.new(mx.outputs[2], plain.inputs["Color"])
    plain.inputs["Strength"].default_value = 1.0
    keyval(mx.inputs[0], STORM_KEYS)
    keyval(hdr_bg.inputs["Strength"], [(t_, 0.7 - 0.5 * v) for t_, v in STORM_KEYS])
    print("[build] sky gradient + storm mix on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.2; sun_d.color = (1.0, 0.80, 0.60); sun_d.angle = math.radians(2.0)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(70), 0, math.radians(-50))
for t_, v in STORM_KEYS:
    sun_d.energy = 3.2 - 2.8 * v; sun_d.keyframe_insert("energy", frame=F(t_))
def aimed_key(name, loc, target, energy, size=2.0):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = (1.0, 0.96, 0.9)
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tg = bpy.data.objects.new(name + "Tgt", None); scene.collection.objects.link(tg); tg.location = target
    c_ = o.constraints.new("TRACK_TO"); c_.target = tg; c_.track_axis = "TRACK_NEGATIVE_Z"; c_.up_axis = "UP_Y"
    return o, d
NAC_KEY, nac_kd = aimed_key("NacKey", (-9.0, 1.0, HUB_Z + 9.0), (0.0, 2.0, HUB_Z + 1.5), 3500.0, 5.0)
BASE_KEY, base_kd = aimed_key("BaseKey", (-14.0, -14.0, 9.0), (2.0, -1.0, 1.5), 4000.0, 6.0)
fx.glare(threshold=1.0, strength=0.55, size=7)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 8000
HOOK_SHOT = ((-24.0, -64.0, 80.0), (0.0, -4.0, 100.0), 22)
NZ = lambda d: HUB_Z + d
YW = lambda v: (lambda t: yaw_w(v, t))                       # nacelle-space camera point
def ev(p, t):
    if callable(p): return Vector(p(t))
    return Vector([c(t) if callable(c) else c for c in p])
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK_SHOT),
    (C["they"] - 0.05, (-25.0, -66.0, 79.0), (0.0, -4.0, 100.5), 22),
    (C["they"], STUDIO + Vector((-1.5, -30.0, 2.5)), STUDIO + Vector((0.5, 0.0, 0.8)), 38, "cut"),
    (C["and"] - 0.05, STUDIO + Vector((0.5, -28.0, 2.0)), STUDIO + Vector((0.5, 0.0, 0.8)), 38),
    (C["and"], (-70.0, -175.0, 22.0), (0.0, 0.0, 78.0), 24, "cut"),
    (C["yesterday"] - 0.05, (-60.0, -160.0, 26.0), (0.0, 0.0, 80.0), 24),
    (C["yesterday"], (-120.0, -250.0, 12.0), (0.0, 0.0, 55.0), 22, "cut"),
    (C["today"] - 0.05, (-105.0, -225.0, 22.0), (0.0, 0.0, 62.0), 22),
    (C["today"] + 0.2, (-105.0, -225.0, 22.0), (0.0, 0.0, 62.0), 22),
    (C["wind"] - 0.05, (-16.0, -8.0, NZ(7.0)), (0.0, 1.5, NZ(2.0)), 24),
    (C["wind"], STUDIO + Vector((-0.5, -31.0, 1.5)), STUDIO + Vector((0.5, 0.0, 0.8)), 36, "cut"),
    (C["and2"] - 0.05, STUDIO + Vector((0.8, -27.0, 2.2)), STUDIO + Vector((0.5, 0.0, 1.0)), 38),
    (C["and2"], (-25.0, -230.0, 96.0), (0.0, -4.0, 100.0), 26, "cut"),
    (C["but"] - 0.05, (-22.0, -215.0, 97.0), (0.0, -4.0, 100.5), 26),
    (C["but"], (-20.0, -40.0, NZ(5.0)), (0.0, -4.5, NZ(2.4)), 30, "cut"),
    (C["generator"] - 0.05, (-18.0, -36.0, NZ(5.5)), (0.0, -4.0, NZ(2.4)), 30),
    (C["generator"], (-13.0, 3.0, NZ(6.0)), (0.0, 3.0, NZ(1.8)), 24, "cut"),
    (C["so"] - 0.05, (-12.0, 2.0, NZ(5.6)), (0.0, 3.0, NZ(1.8)), 24),
    (C["so"], (-6.2, 0.2, NZ(4.6)), (0.0, -2.2, NZ(2.2)), 24, "cut"),
    (C["big"] - 0.05, (-5.8, 0.4, NZ(4.3)), (0.0, -1.2, NZ(2.0)), 24),
    (C["big"], (-4.6, -0.6, NZ(3.6)), (0.0, 0.5, NZ(1.7)), 24, "cut"),
    (C["until"] - 0.05, (-4.4, -0.4, NZ(3.4)), (0.0, 0.6, NZ(1.7)), 24),
    (C["until"] + 0.3, (-5.0, -0.5, NZ(3.4)), (0.0, 2.0, NZ(2.0)), 24),
    (C["fast"] - 0.05, (-5.2, 0.0, NZ(3.4)), (0.0, 2.4, NZ(2.0)), 24),
    (C["fast"], (-4.6, 2.2, NZ(3.4)), (0.0, 4.7, NZ(2.1)), 24, "cut"),
    (C["cables"] - 0.05, (-4.2, 2.8, NZ(3.2)), (0.0, 4.8, NZ(2.1)), 24),
    (C["cables"], (-9.0, 3.0, NZ(-2.0)), (0.3, 0.5, NZ(-8.0)), 22, "cut"),
    (C["transformer"] - 0.2, (-12.0, -16.0, 6.0), (2.0, -1.0, 2.0), 22),
    (C["now"] - 0.05, (-12.5, -17.0, 5.5), (3.0, -1.5, 1.4), 22),
    (C["now"], (-12.0, 26.0, NZ(34.0)), (0.0, -12.0, NZ(2.0)), 22, "cut"),
    (C["each"] - 0.05, (-11.0, 23.0, NZ(31.0)), (0.0, -10.0, NZ(2.0)), 22),
    (C["each"], YW((-10.0, -17.0, 5.0)), YW((0.0, -4.4, 2.6)), 22, "cut"),
    (C["above"] - 0.05, YW((-9.0, -15.5, 4.6)), YW((0.0, -4.4, 2.5)), 22),
    (C["above"], (-42.0, -100.0, 42.0), (0.0, -2.0, 92.0), 24, "cut"),
    (C["when"] - 0.05, (-36.0, -88.0, 50.0), (0.0, -3.0, 96.0), 24),
    (C["when"] + 0.2, (-50.0, -130.0, 40.0), (0.0, -2.0, 90.0), 23),
    (DUR - 0.2, *HOOK_SHOT),
    (DUR, *HOOK_SHOT),
]
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.03 * math.sin(t * 0.7), 0.0, 0.02 * math.sin(t * 0.9 + 1.0))) * (0 if t > DUR - 0.25 or t < 0.01 else 1))
    cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 20; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(20.0, min(4000.0, 220.0 * ((cl - ct).length / 30.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (5, 6, 0)

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
scene.view_settings.exposure = float(arg("--exposure", "-0.2"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(RB0, F(C["yesterday"] + 0.2))
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
P = lambda *v: (lambda t: Vector(v))
NW = lambda v: (lambda t: yaw_w(v, t))
def blade_root(t, k=0, s=6.0):
    a = spin_at(t) + math.radians(120 * k)
    return yaw_w(HUB_L + Vector((math.sin(a) * s, 0, math.cos(a) * s)), t)
ANCHP = {
    "lowp": P(*(STUDIO + Vector((-0.6, -SPAN / 2 - 0.6, 2.4)))), "lift": P(*(STUDIO + Vector((-0.4, -SPAN / 2 - 0.9, 6.5)))),
    "foil": P(*(STUDIO + Vector((-3.5, -SPAN / 2, -0.4)))), "hub": NW(HUB_L + Vector((0, -2.5, 0))),
    "tip": lambda t: yaw_w(HUB_L + Vector((math.sin(spin_at(t)) * (BLADE + 1.4), -0.5, math.cos(spin_at(t)) * (BLADE + 1.4))), t),
    "mainshaft": NW((0, -1.8, ZA + 0.42)), "gearbox": NW((0, 0.0, ZA + 1.1)), "fastshaft": NW((0, 2.4, ZC + 0.16)),
    "generator": NW((0, 4.7, ZC + 1.25)), "magnets": NW((-0.6, 4.2, ZC)), "coils": NW((0.0, 5.2, ZC + 0.95)),
    "cable": lambda t: Vector((0.35, 0.55, max(3.0, min(HUB_Z - 4, HUB_Z + 4 - (HUB_Z + 6) * lin((t - P_TOP) / (P_BASE - P_TOP)))))),
    "transformer": P(7.3, -4.6, 2.3), "vane": NW((0.9, 8.0, 6.1)), "yawmotor": NW((-1.38, 1.38, 1.5)),
    "pitch": lambda t: blade_root(t, 0, 1.5), "blade": lambda t: blade_root(t, 0, 20.0),
}
anchors = {k: [] for k in ANCHP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"wings_glow": round(C["wings"], 3), "studio": round(C["they"], 3), "lift_pop": round(C["lift"] - 0.1, 3),
          "storm1": RR(*T_STORM1), "wreck": round(C["wreck"], 3), "recap": round(C["yesterday"], 3), "push": round(C["today"] + 0.2, 3),
          "studio2": round(C["wind"], 3), "lowp": round(C["pressure"], 3), "lift2": round(C["pulls"] - 0.1, 3), "front": round(C["and2"], 3),
          "tipring": round(C["tips"], 3), "hub": round(C["but"], 3), "gen_side": round(C["generator"], 3), "nacelle_in": round(C["so"], 3),
          "gears": round(C["big"], 3), "gen": round(C["fast"], 3), "coils": round(C["coils"], 3), "pulse": RR(P_TOP, P_BASE),
          "xf": round(C["transformer"], 3), "yaw_shot": round(C["now"], 3), "winddir": RR(T_WINDDIR0, T_WINDDIR1), "yaw": RR(T_YAW0, T_YAW1),
          "pitch_shot": round(C["each"], 3), "pitch": RR(T_PITCH0, T_PITCH0 + 0.8), "storm2": RR(*T_STORM2), "feather": RR(T_FEATH0, T_FEATH1),
          "stop": RR(T_STOP0, T_STOP1), "back": RR(T_BACK0, T_BACK1)}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS", events, "DUR", DUR, "FRAMES", FRAMES, "rotor end angle (deg mod 120)", round(math.degrees(ANG[-1]) % 120, 2))
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
