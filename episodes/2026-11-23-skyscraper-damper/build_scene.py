# Skyscraper damper (3d-30): why tall towers don't sway you off your feet. Claim-first hook ("A six-hundred-sixty-ton steel ball hangs near the
# top of this tower."): close on the gold ball swinging inside the cut-open top floors -> storm what-if, tower sways (exaggerated), glass tints
# red -> wide of the whole tower in the city, height bar -> side view: wind bends the tower like a tree -> rhythm: gusts in time, swing grows
# -> top-floor office set (no people): lamps swing, cartons slide (rigid body), fish tank sloshes (Mantaflow) -> exterior top, front wall cut
# away -> 41 plates drop and stack into the ball, width bar, cables, floors 87-92 -> side view: cable length bar, ball swings in time with
# the tower -> ball lags and swings the other way (gold push arrow, cyan pull arrow) -> under the ball: 8 hydraulic dampers telescope, glow
# hot, sparks -> wide side view with a red ghost tower (more sway) -> typhoon: rain, ball swings ~1 m, gold move bar -> bumper ring, red
# ghost ball at the 1.5 m limit -> storm outside -> back to the first frame (loop: "...what keeps the top floors calm is" -> hook).
# Illustrative (1 unit = 1 m): a generic stepped supertall with the real tower's proportions (508 m to the tip, damper ~ floors 87-92,
# ball 5.5 m of 41 plates, 8 cables, 8 dampers, 1.5 m limit). Tower sway is EXAGGERATED (real roof movement is far smaller); cable length and
# swing period are visual. No logos, no people.
# Run from the episode folder:
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu] [--bake-fluid]
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
    raise ValueError(f'cue "{word}" after {_last[0]} not found')

CUES = [("a", "A"), ("steel", "steel"), ("ball0", "ball"), ("hangs", "hangs"), ("top", "top"), ("tower", "tower."),
        ("without", "Without"), ("seasick", "seasick"), ("typhoon", "typhoon."), ("this", "This"), ("taipei", "Taipei"), ("over", "over"),
        ("sixteen", "sixteen"), ("tall", "tall."), ("tall2", "Tall"), ("rigid", "rigid."), ("strong", "strong"), ("sway", "sway"), ("tree", "tree."),
        ("every", "Every"), ("rhythm", "rhythm."), ("gust", "Gust"), ("at2", "at"), ("growing", "growing."),
        ("it", "It"), ("snap", "snap,"), ("top2", "top,"), ("feel", "feel"), ("so", "So"), ("engineers", "engineers"), ("pendulum", "pendulum"),
        ("inside", "inside."), ("fortyone", "Forty-one"), ("plates", "plates,"), ("ball", "ball"), ("eighteen", "eighteen"), ("wide", "wide,"),
        ("cables", "cables"), ("eightyseven", "eighty-seven"), ("ninetytwo", "ninety-two."),
        ("trick", "trick:"), ("cable", "cable"), ("length", "length"), ("swings", "swings,"), ("matched", "matched"), ("rhythm2", "rhythm."),
        ("tuned", "tuned"), ("damper", "damper."),
        ("when", "When"), ("pushes", "pushes"), ("one", "one"), ("ball2", "ball"), ("lags", "lags"), ("other", "other"), ("pulling", "pulling"),
        ("sway2", "sway."),
        ("underneath", "Underneath,"), ("eight", "eight"), ("hydraulic", "hydraulic"), ("shock", "shock"), ("turn", "turn"), ("heat", "heat."),
        ("its", "Its"), ("maker", "maker"), ("sway4", "sway"), ("forty", "forty"), ("percent", "percent."),
        ("in", "In"), ("y2015", "2015,"), ("typhoon2", "Typhoon"), ("soudelor", "Soudelor"), ("swung", "swung"), ("three", "three"), ("record", "record."),
        ("can", "can"), ("almost", "almost"), ("five", "five,"), ("never", "never"),
        ("so2", "So"), ("next", "next"), ("hits", "hits,"), ("calm", "calm"), ("is", "is")]
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


# ================= dimensions (1 unit = 1 m) =================
# Generic stepped supertall modelled on the real tower's proportions (508 m to the spire tip, damper bay ~ floors 87-92).
FLOOR_H = 4.2
Z87, Z92 = 87 * FLOOR_H, 92 * FLOOR_H            # 365.4, 386.4
R_BALL = 2.75                                    # ~5.5 m (18 ft) sphere
PIVOT_Z = Z92 - 0.6                              # cable frame under floor 92
BALL_Z = 372.4                                   # sphere centre at rest
L_PEND = PIVOT_Z - BALL_Z                        # visual pendulum length
PIN_Z = BALL_Z - R_BALL - 1.6                    # bottom of the pin under the ball
RING_Z = Z87 + 1.2                               # bumper ring height
H_TOP = 448.0                                    # roof; spire to 508
MOD_Z0, MOD_H, NMOD = 108.0, 33.6, 8             # 8 flared modules
CROWN_Z0 = MOD_Z0 + MOD_H * NMOD                 # 376.8
SPLIT_Z = MOD_Z0 + MOD_H * 6                     # modules 7, 8 + crown are split into front/back halves (cutaway)
STUDIO = Vector((-900.0, 0.0, 380.0))            # "top floor office" set (people-feel-it beat), no people

# ================= key times =================
T_HOOK1 = C["tower"]
T_STORM1 = (C["tower"], C["this"])
T_CITY = (C["this"], C["tall2"])
T_BEND = (C["tall2"], C["every"])
T_RHY = (C["every"], C["it"])
T_OFFICE = (C["it"], C["so"])
T_BUILD = (C["pendulum"] - 0.1, C["ball"] + 0.2)
T_TUNE = (C["trick"], C["when"])
T_LAG = (C["when"], C["underneath"])
T_DAMP = (C["underneath"], C["its"])
T_GHOST = (C["its"], C["in"])
T_TYPH = (C["in"], C["can"])
T_LIMIT = (C["can"], C["so2"])
T_END = (C["so2"], C["calm"])
T_LOOP = C["calm"]
P0 = DUR / max(1, round(DUR / 7.0))              # hook swing period, DUR is a whole number of periods (loop)
def env(t, t0, t1, a=0.4):
    return lin((t - t0) / a) * lin((t1 - t) / a)
def inw(t, w): return w[0] <= t < w[1]
def hook_swing(t): return 0.16 * math.sin(2 * math.pi * t / P0)

def tower_sway(t):
    """Lateral displacement of the roof (m, exaggerated for the beats that say so)."""
    if inw(t, T_STORM1): return 7.0 * math.sin(2 * math.pi * (t - T_STORM1[0]) / 2.4) * env(t, *T_STORM1, 0.5)
    if inw(t, T_BEND):
        b = 11.0 * ease((t - C["strong"]) / 1.0) * env(t, *T_BEND, 0.3)
        return b + 1.5 * math.sin(2 * math.pi * (t - C["strong"]) / 1.6) * lin((t - C["strong"]) / 0.6) * env(t, *T_BEND, 0.3)
    if inw(t, T_RHY):
        amp = 3.0 + 13.0 * ease((t - C["gust"]) / (C["growing"] + 0.6 - C["gust"]))
        return amp * math.sin(2 * math.pi * (t - T_RHY[0]) / 2.0) * env(t, *T_RHY, 0.3)
    if inw(t, T_TUNE): return 1.6 * math.sin(2 * math.pi * (t - C["matched"]) / 3.0) * lin((t - C["matched"]) / 0.8) * env(t, *T_TUNE, 0.3)
    if inw(t, T_LAG): return 3.2 * math.sin(2 * math.pi * (t - C["pushes"]) / 3.2) * env(t, *T_LAG, 0.4)
    if inw(t, T_DAMP): return 0.6 * math.sin(2 * math.pi * (t - T_DAMP[0]) / 3.2) * env(t, *T_DAMP, 0.3)
    if inw(t, T_GHOST): return 0.6 * 30.0 * math.sin(2 * math.pi * (t - C["sway4"]) / 2.4) * lin((t - C["sway4"] + 0.6) / 0.6) * env(t, *T_GHOST, 0.3)
    if inw(t, T_TYPH): return 1.5 * math.sin(2 * math.pi * (t - T_TYPH[0]) / 3.2) * env(t, *T_TYPH, 0.4)
    if inw(t, T_END): return 2.0 * math.sin(2 * math.pi * (t - T_END[0]) / 2.8) * env(t, *T_END, 0.3)
    return 0.0
def ghost_sway(t):
    if inw(t, T_GHOST): return 30.0 * math.sin(2 * math.pi * (t - C["sway4"]) / 2.4) * lin((t - C["sway4"] + 0.6) / 0.6) * env(t, *T_GHOST, 0.3)
    return 0.0
def ball_rel(t):
    """Sphere offset (m) relative to the tower, along x. Opposite to the sway."""
    if inw(t, T_TUNE): return -0.55 * math.sin(2 * math.pi * (t - C["matched"]) / 3.0) * lin((t - C["matched"]) / 0.8) * env(t, *T_TUNE, 0.3) \
        + 0.35 * math.sin(2 * math.pi * (t - C["cable"]) / 3.0) * env(t, C["cable"], C["matched"], 0.4)
    if inw(t, T_LAG): return -1.0 * math.sin(2 * math.pi * (t - C["pushes"] - 0.25) / 3.2) * env(t, *T_LAG, 0.4)
    if inw(t, T_DAMP): return -0.8 * math.sin(2 * math.pi * (t - T_DAMP[0]) / 3.2) * env(t, *T_DAMP, 0.3)
    if inw(t, T_TYPH):
        a = 0.25 + 0.75 * ease((t - C["typhoon2"]) / (C["three"] - C["typhoon2"]))
        return a * math.sin(2 * math.pi * (t - C["three"]) / 3.2 + math.pi / 2) * env(t, *T_TYPH, 0.4)
    if inw(t, T_LIMIT): return 0.45 * math.sin(2 * math.pi * (t - T_LIMIT[0]) / 3.2) * env(t, *T_LIMIT, 0.3)
    if inw(t, T_END): return -0.5 * math.sin(2 * math.pi * (t - T_END[0]) / 2.8) * env(t, *T_END, 0.3)
    if inw(t, T_STORM1) or inw(t, T_GHOST): return -0.4 * tower_sway(t) / 7.0
    return hook_swing(t)
def bend_at(z, t, s=None):
    """(x offset, tilt) of the tower axis at height z (quadratic bend, like a cantilever)."""
    s = tower_sway(t) if s is None else s
    u = (max(0.0, z) / H_TOP)
    return s * u * u, math.atan(2 * s * max(0.0, z) / (H_TOP * H_TOP))

# ================= materials =================
m_glass = None
def glass_mat(name, tint=(0.10, 0.22, 0.24)):
    m, nt, b = new_mat(name); N, Lk = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); Lk.new(tc.outputs["Object"], sep.inputs[0])
    add = N.new("ShaderNodeMath"); add.operation = "ADD"; Lk.new(sep.outputs["X"], add.inputs[0]); Lk.new(sep.outputs["Y"], add.inputs[1])
    cmb = N.new("ShaderNodeCombineXYZ"); Lk.new(add.outputs[0], cmb.inputs[0]); Lk.new(sep.outputs["Z"], cmb.inputs[1])
    br = N.new("ShaderNodeTexBrick"); Lk.new(cmb.outputs[0], br.inputs["Vector"]); br.offset = 0.0
    br.inputs["Scale"].default_value = 0.24; br.inputs["Mortar Size"].default_value = 0.035
    br.inputs["Brick Width"].default_value = 1.6; br.inputs["Row Height"].default_value = FLOOR_H
    br.inputs["Color1"].default_value = (*tint, 1); br.inputs["Color2"].default_value = (tint[0] * 1.25, tint[1] * 1.2, tint[2] * 1.2, 1)
    br.inputs["Mortar"].default_value = (0.55, 0.60, 0.60, 1)
    Lk.new(br.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange"); Lk.new(br.outputs["Fac"], rr.inputs[0]); rr.inputs[3].default_value = 0.08; rr.inputs[4].default_value = 0.45
    Lk.new(rr.outputs[0], b.inputs["Roughness"]); b.inputs["Metallic"].default_value = 0.55
    b.inputs["Emission Color"].default_value = (1.0, 0.3, 0.24, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
m_glass, b_glass = glass_mat("TowerGlass")
m_concrete, _ = mat("Concrete", (0.46, 0.46, 0.45), 0.8, noise=3.0)
m_slab, b_slab = mat("Slab", (0.36, 0.36, 0.37), 0.7)
m_steel, b_steel = mat("Steel", (0.50, 0.52, 0.55), 0.3, 0.9)
m_dark, _ = mat("DarkSteel", (0.08, 0.085, 0.09), 0.4, 0.8)
m_gold1, b_gold1 = mat("BallGold", (0.95, 0.66, 0.22), 0.22, 1.0, emit_rgb=(1.0, 0.74, 0.27))
m_gold2, b_gold2 = mat("BallGold2", (0.80, 0.52, 0.15), 0.28, 1.0, emit_rgb=(1.0, 0.74, 0.27))
m_cable, b_cable = mat("Cable", (0.30, 0.31, 0.33), 0.35, 0.9, emit_rgb=(0.30, 0.92, 1.0))
m_barrel, b_barrel = mat("DamperBarrel", (0.75, 0.76, 0.78), 0.25, 0.9, emit_rgb=(1.0, 0.35, 0.08))
m_rod, _ = mat("DamperRod", (0.9, 0.9, 0.92), 0.08, 1.0)
m_ring, b_ring = mat("BumperRing", (0.35, 0.36, 0.38), 0.3, 0.9, emit_rgb=(1.0, 0.30, 0.24))
m_ground, _ = mat("Ground", (0.07, 0.07, 0.075), 0.9, noise=0.02)
m_bldg, _ = glass_mat("CityGlass", (0.16, 0.17, 0.19))
m_cyan, b_cyan = mat("CyanGlow", (0.30, 0.92, 1.0), 0.3, emit_rgb=(0.30, 0.92, 1.0))
m_goldglow, b_goldglow = mat("GoldGlow", (1.0, 0.74, 0.27), 0.3, emit_rgb=(1.0, 0.74, 0.27))
m_red, b_red = mat("RedGlow", (1.0, 0.30, 0.24), 0.3, emit_rgb=(1.0, 0.30, 0.24))
glow(b_cyan, [(0, 6.0)]); glow(b_goldglow, [(0, 6.0)]); glow(b_red, [(0, 6.0)])
m_ghost, ghost_fac = ghost("SwayGhost", (1.0, 0.30, 0.24))
m_wall, _ = mat("OfficeWall", (0.70, 0.70, 0.68), 0.8)
m_floor, _ = mat("OfficeFloor", (0.30, 0.25, 0.20), 0.5, noise=4.0)
m_box, _ = mat("Box", (0.62, 0.45, 0.28), 0.8)
m_win, b_win = mat("Window", (0.5, 0.7, 0.9), 0.1, emit_rgb=(0.55, 0.75, 1.0)); glow(b_win, [(0, 2.5)])
m_lamp, b_lamp = mat("Bulb", (1.0, 0.9, 0.7), 0.3, emit_rgb=(1.0, 0.85, 0.6)); glow(b_lamp, [(0, 12.0)])
m_water, b_water, _wv = water_sec("TankWater")

# ================= hollow tapered wall helper =================
def add_hex(bm, pts, mi=0):
    vs = [bm.verts.new(p) for p in pts]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        try: bm.faces.new([vs[i] for i in f]).material_index = mi
        except ValueError: pass
def wall_half(bm, z0, z1, w0, w1, side, th=0.6):
    """Walls of a square frustum (half-width w0 at z0, w1 at z1), only the y<0 (side=-1) or y>=0 (side=+1) half, origin at z0."""
    h = z1 - z0
    def ring(w, z, inset): return w - inset, z
    # back/front wall (y = side*w)
    for (wa, za), (wb, zb) in [((w0, 0.0), (w1, h))]:
        pass
    for k in range(2):   # 0: the y wall, 1: the two x walls
        pass
    def P(x, y, z): return Vector((x, y, z))
    for (ia, ib) in [(0, 1)]:
        wo0, wo1, wi0, wi1 = w0, w1, w0 - th, w1 - th
        s = side
        # y wall: spans x from -w..w at y = s*w
        add_hex(bm, [P(-wo0, s * wo0, 0), P(wo0, s * wo0, 0), P(wi0, s * wi0, 0), P(-wi0, s * wi0, 0),
                     P(-wo1, s * wo1, h), P(wo1, s * wo1, h), P(wi1, s * wi1, h), P(-wi1, s * wi1, h)])
        for sx in (-1, 1):  # x walls from y=0 to y=s*w
            add_hex(bm, [P(sx * wo0, 0, 0), P(sx * wo0, s * wo0, 0), P(sx * wi0, s * wi0, 0), P(sx * wi0, 0, 0),
                         P(sx * wo1, 0, h), P(sx * wo1, s * wo1, h), P(sx * wi1, s * wi1, h), P(sx * wi1, 0, h)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def frustum(bm, z0, z1, w0, w1, mi=0):
    h = z1 - z0
    add_hex(bm, [Vector((-w0, -w0, 0)), Vector((w0, -w0, 0)), Vector((w0, w0, 0)), Vector((-w0, w0, 0)),
                 Vector((-w1, -w1, h)), Vector((w1, -w1, h)), Vector((w1, w1, h)), Vector((-w1, w1, h))], mi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

# ================= tower pieces (each follows the bend at its base) =================
PIECES = []   # (obj, z0)
def piece(name, bm, m_, z0):
    o = mesh_obj(name, bm, m_); o.location = (0, 0, z0); PIECES.append((o, z0)); return o
# podium + trunk
bm = bmesh.new(); frustum(bm, 0, 26, 70, 66); piece("Podium", bm, m_concrete, 0.0).location.y = 30.0
bm = bmesh.new(); frustum(bm, 0, MOD_Z0, 31.0, 25.5); piece("Trunk", bm, m_glass, 0.0)
FRONT_HALVES = []
for k in range(NMOD):
    z0 = MOD_Z0 + k * MOD_H
    if z0 < SPLIT_Z - 1:
        bm = bmesh.new(); frustum(bm, 0, MOD_H, 21.5, 26.5); piece(f"Module{k+1}", bm, m_glass, z0)
        bm = bmesh.new(); frustum(bm, 0, 1.2, 26.8, 26.8); piece(f"Ledge{k+1}", bm, m_concrete, z0 + MOD_H - 0.6)
    else:
        for side in (1, -1):
            bm = bmesh.new(); wall_half(bm, 0, MOD_H, 21.5, 26.5, side)
            o = piece(f"Module{k+1}_{'B' if side > 0 else 'F'}", bm, m_glass, z0)
            if side < 0: FRONT_HALVES.append(o)
        bm = bmesh.new(); frustum(bm, 0, 1.2, 26.8, 26.8); bm2 = bm
        bmesh.ops.bisect_plane(bm2, geom=list(bm2.verts) + list(bm2.edges) + list(bm2.faces), plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
        piece(f"Ledge{k+1}_B", bm2, m_concrete, z0 + MOD_H - 0.6)
        bm = bmesh.new(); frustum(bm, 0, 1.2, 26.8, 26.8)
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_outer=True)
        FRONT_HALVES.append(piece(f"Ledge{k+1}_F", bm, m_concrete, z0 + MOD_H - 0.6))
# crown: two steps, split
for j, (z0, z1, w0, w1) in enumerate([(CROWN_Z0, CROWN_Z0 + 36.0, 20.0, 18.0), (CROWN_Z0 + 36.0, H_TOP, 14.0, 11.0)]):
    for side in (1, -1):
        bm = bmesh.new(); wall_half(bm, 0, z1 - z0, w0, w1, side, 0.5)
        o = piece(f"Crown{j}_{'B' if side > 0 else 'F'}", bm, m_glass, z0)
        if side < 0: FRONT_HALVES.append(o)
bm = bmesh.new(); frustum(bm, 0, 1.0, 11.5, 11.5); piece("Roof", bm, m_concrete, H_TOP)
bm = bmesh.new(); add_cyl(bm, 1.6, 60.0, "Z", (0, 0, 30.0), 12, r2=0.35); piece("Spire", bm, m_steel, H_TOP + 1.0)
# interior floor slabs of the cut part (back half only, with an atrium hole around the damper)
for fl in range(int(SPLIT_Z // FLOOR_H) + 1, int(CROWN_Z0 // FLOOR_H) + 9):
    z = fl * FLOOR_H
    if z > CROWN_Z0 + 34: break
    w = 25.4 if z < CROWN_Z0 else 19.0
    bm = bmesh.new()
    if abs(z - Z87) < 0.1:
        add_box(bm, -w, w, -w, w, -0.4, 0)
    elif Z87 < z <= Z92 + 0.1:
        add_box(bm, -w, -9, 0, w, -0.4, 0); add_box(bm, 9, w, 0, w, -0.4, 0); add_box(bm, -9, 9, 9, w, -0.4, 0)
    else:
        add_box(bm, -w, w, 0, w, -0.4, 0)
    piece(f"Slab{fl}", bm, m_slab, z)

# ================= damper bay: frame that follows the tower at the bay height =================
BAY = empty("BayFrame")
def bay_xf(t):
    x, a = bend_at(Z87, t); return x, a
bake_fn(BAY, "location", 0, lambda t: bay_xf(t)[0]); bake_fn(BAY, "location", 2, lambda t: Z87)
bake_fn(BAY, "rotation_euler", 1, lambda t: bay_xf(t)[1])
LZ = lambda z: z - Z87                     # bay-local z
# cable frame (beams under floor 92)
bm = bmesh.new()
for a in (0, 90):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    add_bar(bm, (-9 * ca, -9 * sa, LZ(PIVOT_Z) + 0.3), (9 * ca, 9 * sa, LZ(PIVOT_Z) + 0.3), 0.9)
add_cyl(bm, 4.6, 0.5, "Z", (0, 0, LZ(PIVOT_Z) + 0.3), 32)
par(mesh_obj("CableFrame", bm, m_dark), BAY)
# pendulum: pivot empty rotates about y; sphere + cables are children
PEND = par(empty("Pendulum", (0, 0, LZ(PIVOT_Z))), BAY)
def phi(t): return math.asin(max(-0.95, min(0.95, ball_rel(t) / L_PEND)))
bake_fn(PEND, "rotation_euler", 1, lambda t: phi(t))
CAB = []
for k in range(8):
    a = 2 * math.pi * (k + 0.5) / 8
    bm = bmesh.new(); add_bar(bm, (4.2 * math.cos(a), 4.2 * math.sin(a), 0), (2.35 * math.cos(a), 2.35 * math.sin(a), -L_PEND + 0.9), 0.16)
    CAB.append(par(mesh_obj(f"Cable{k}", bm, m_cable), PEND))
# cradle ring the cables hold
bm = bmesh.new(); res = bmesh.ops.create_circle(bm, cap_ends=False, segments=48, radius=2.45)
CRADLE_PROF = None
cr = lathe("Cradle", tube_prof(2.3, 2.7, -0.25, 0.25), m_dark, ang=2 * math.pi, seg=48, loc=(0, 0, -L_PEND + 0.8)); par(cr, PEND)
cr.location = (0, 0, -L_PEND + 0.8)
# 41 plates (alternate tones), stacked into the ball; each can drop in from above
BALL = par(empty("Ball", (0, 0, -L_PEND)), PEND)
PLATES = []
NPL = 41; TH = 2 * R_BALL / NPL
for i in range(NPL):
    zc = -R_BALL + TH * (i + 0.5)
    rr = math.sqrt(max(0.05, R_BALL * R_BALL - zc * zc))
    bm = bmesh.new(); add_cyl(bm, rr, TH * 0.96, "Z", (0, 0, 0), 40)
    o = par(mesh_obj(f"Plate{i:02d}", bm, m_gold1 if i % 2 == 0 else m_gold2), BALL)
    o.location = (0, 0, zc)
    try: o.data.shade_smooth()
    except Exception: pass
    PLATES.append((o, zc))
def plate_drop(i, t):
    """z offset of plate i: hidden-high between 'So' and its drop, then lands (stacked bottom-up)."""
    t0 = T_BUILD[0] + (T_BUILD[1] - T_BUILD[0] - 0.7) * i / (NPL - 1)
    if t < C["so"] or t >= t0 + 0.7: return 0.0
    return drop(t, t0, h=14.0, d=0.5) if t >= t0 else 60.0
def plate_scale(i, t):
    t0 = T_BUILD[0] + (T_BUILD[1] - T_BUILD[0] - 0.7) * i / (NPL - 1)
    return 0.0 if C["so"] <= t < t0 else 1.0
for i, (o, zc) in enumerate(PLATES):
    bake_fn(o, "location", 2, lambda t, i=i, zc=zc: zc + plate_drop(i, t))
    sc_vals = [plate_scale(i, t) for t in TS]
    for ax in range(3): bake(o, "scale", ax, sc_vals)
# cables only exist once the ball is hung (hidden during the build until the last plates land)
for c_ in CAB: windows(c_, [(0, C["so"]), (C["ball"] - 0.3, DUR)])
windows(cr, [(0, C["so"]), (C["ball"] - 0.3, DUR)])
# pin under the ball + bumper ring (limit ~1.5 m)
PIN = par(cyl("Pin", 0.35, 1.9, "Z", (0, 0, -L_PEND - R_BALL - 0.75), m_dark), PEND)
windows(PIN, [(0, C["so"]), (C["ball"] - 0.3, DUR)])
RING = lathe("BumperRing", tube_prof(1.5 + 0.35, 2.3, -0.35, 0.35), m_ring, ang=2 * math.pi, seg=48, loc=(0, 0, LZ(RING_Z))); par(RING, BAY)
RING.location = (0, 0, LZ(RING_Z))
bm = bmesh.new()
for k in range(6):
    a = 2 * math.pi * k / 6; add_bar(bm, (2.0 * math.cos(a), 2.0 * math.sin(a), LZ(RING_Z)), (2.4 * math.cos(a), 2.4 * math.sin(a), 0.05), 0.35)
par(mesh_obj("RingLegs", bm, m_dark), BAY)
glow(b_ring, [(0, 0.0)] + pulse(C["almost"], 6.0, hold=C["so2"] - C["almost"] - 0.8, down=0.4))
# ghost sphere at the 1.5 m limit
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=R_BALL)
m_ghost2, ghost2_fac = ghost("LimitGhost", (1.0, 0.30, 0.24))
GH2 = par(mesh_obj("LimitGhostBall", bm, m_ghost2), BAY); GH2.location = (-1.5, 0, LZ(BALL_Z))
keyval(ghost2_fac, [(0, 0.0), (C["almost"] - 0.05, 0.0), (C["almost"] + 0.25, 0.22), (C["so2"] - 0.3, 0.22), (C["so2"], 0.0)])
windows(GH2, [(C["almost"] - 0.1, C["so2"])])
# 8 hydraulic dampers: barrel at the floor anchor tracking the pin collar, rod at the collar tracking the anchor
COLLAR = []
DAMPERS = []
for k in range(8):
    a = 2 * math.pi * (k + 0.5) / 8
    pin_p = par(empty(f"Collar{k}", (1.9 * math.cos(a), 1.9 * math.sin(a), -L_PEND - R_BALL + 0.9)), PEND)
    anc = par(empty(f"Anchor{k}", (7.2 * math.cos(a), 7.2 * math.sin(a), 0.6)), BAY)
    bar = cyl(f"Barrel{k}", 0.42, 3.4, "Z", (0, 0, 1.7), m_barrel); par(bar, anc); bar.location = (0, 0, 0)
    c1 = bar.constraints.new("DAMPED_TRACK"); c1.target = pin_p; c1.track_axis = "TRACK_Z"
    rod = cyl(f"Rod{k}", 0.2, 3.6, "Z", (0, 0, 1.8), m_rod); par(rod, pin_p); rod.location = (0, 0, 0)
    c2 = rod.constraints.new("DAMPED_TRACK"); c2.target = anc; c2.track_axis = "TRACK_Z"
    bm = bmesh.new(); add_box(bm, -0.9, 0.9, -0.9, 0.9, 0, 0.6); base = par(mesh_obj(f"DamperBase{k}", bm, m_dark), anc); base.location = (0, 0, -0.6)
    windows(rod, [(0, C["so"]), (C["ball"] - 0.3, DUR)])
    DAMPERS.append((bar, rod, anc, pin_p))
glow(b_barrel, [(0, 0.0)] + pulse(C["turn"], 4.0, hold=C["its"] - C["turn"] - 0.9, down=0.5))
glow(b_cable, [(0, 0.0)] + pulse(C["cables"], 3.5, hold=0.9) + pulse(C["cable"], 5.0, hold=C["tuned"] - C["cable"] - 0.2, down=0.5))
glow(b_gold1, [(0, 0.0)] + pulse(C["steel"], 0.6, hold=0.6) + pulse(C["fortyone"], 0.5, hold=1.0))
glow(b_gold2, [(0, 0.0)] + pulse(C["steel"], 0.6, hold=0.6) + pulse(C["fortyone"], 0.5, hold=1.0))
# bay lights (inside the cut floors)
def bay_light(name, loc, energy, size=6.0, color=(1.0, 0.93, 0.82)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); par(o, BAY); o.location = loc
    return o, d
_, top_d = bay_light("BayTop", (0, 2.0, LZ(PIVOT_Z) - 1.0), 3200.0, 10.0)
for t_, v in [(0, 3200.0), (T_TYPH[0] - 0.01, 3200.0), (T_TYPH[0], 900.0), (T_TYPH[1] - 0.01, 900.0), (T_TYPH[1], 3200.0)]:
    top_d.energy = v; top_d.keyframe_insert("energy", frame=F(t_))
bay_light("BayFront", (-6.0, -14.0, LZ(BALL_Z) + 3.0), 2200.0, 8.0)
_, cool_d = bay_light("BayStorm", (-8.0, -10.0, LZ(BALL_Z) + 6.0), 0.0, 10.0, (0.45, 0.6, 1.0))
for t_, v in [(0, 0.0), (T_TYPH[0] - 0.01, 0.0), (T_TYPH[0], 2500.0), (C["swung"], 2500.0), (C["swung"] + 0.08, 9000.0), (C["swung"] + 0.2, 2500.0), (T_TYPH[1] - 0.01, 2500.0), (T_TYPH[1], 0.0)]:
    cool_d.energy = v; cool_d.keyframe_insert("energy", frame=F(t_))
_, heat_d = bay_light("BayHeat", (0, 0, 2.0), 0.0, 8.0, (1.0, 0.45, 0.15))
for t_, v in [(0, 0.0), (C["turn"] - 0.01, 0.0), (C["heat"], 5000.0), (C["its"] - 0.4, 5000.0), (C["its"], 0.0)]:
    heat_d.energy = v; heat_d.keyframe_insert("energy", frame=F(t_))

# ================= measure bars (scaled bars that grow) =================
def grow_bar(name, p0, p1, w, m_, t0, t1, parent=None, dur=0.45):
    """Bar from p0 to p1 growing from p0 at t0, gone at t1 (origin at p0, along local +Z)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bm = bmesh.new(); add_box(bm, -w / 2, w / 2, -w / 2, w / 2, 0, d.length)
    o = mesh_obj(name, bm, m_); o.location = p0; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
    if parent: par(o, parent); o.location = p0
    bake_fn(o, "scale", 2, lambda t: ease((t - t0) / dur) if t < t1 else 0.0)
    windows(o, [(t0, t1)]); return o
HB = grow_bar("HeightBar", (60, -40, 0), (60, -40, 508), 2.5, m_goldglow, C["sixteen"] - 0.1, C["tall2"])
WB = grow_bar("WidthBar", (-R_BALL, -R_BALL - 0.4, LZ(BALL_Z) + R_BALL + 0.6), (R_BALL, -R_BALL - 0.4, LZ(BALL_Z) + R_BALL + 0.6), 0.14, m_goldglow,
              C["eighteen"] - 0.1, C["cables"], BAY)
LB = grow_bar("LengthBar", (-5.3, -4.0, LZ(PIVOT_Z)), (-5.3, -4.0, LZ(BALL_Z)), 0.16, m_cyan, C["cable"] - 0.1, C["tuned"], BAY)
MB = grow_bar("MoveBar", (0, -R_BALL - 0.5, LZ(BALL_Z) - R_BALL - 0.3), (-1.0, -R_BALL - 0.5, LZ(BALL_Z) - R_BALL - 0.3), 0.12, m_goldglow,
              C["three"] - 0.1, C["can"], BAY)
LMB = grow_bar("LimitBar", (0, -R_BALL - 0.5, LZ(BALL_Z) - R_BALL - 0.3), (-1.5, -R_BALL - 0.5, LZ(BALL_Z) - R_BALL - 0.3), 0.12, m_red,
               C["almost"] - 0.1, C["so2"], BAY)

# ================= arrows: wind, push (gold) and lag (cyan) =================
def arrow_obj(name, base, direction, length, width, m_, y=0.0, parent=None):
    bm = bmesh.new(); add_arrow(bm, base, direction, length, width, y); o = mesh_obj(name, bm, m_)
    if parent: par(o, parent)
    return o
WIND = []
for k, z in enumerate((150, 250, 340, 420)):
    o = arrow_obj(f"Wind{k}", (-150, z), (1, 0), 70, 14, m_cyan, y=-40)
    bake_fn(o, "location", 0, lambda t, k=k: -60 + 120 * ((t * 0.9 + k * 0.27) % 1.0))
    windows(o, [(C["strong"] - 0.1, T_BEND[1])]); WIND.append(o)
GUSTS = []
for k in range(4):
    o = arrow_obj(f"Gust{k}", (-160, 300 + 30 * (k % 2)), (1, 0), 80, 18, m_red if k >= 2 else m_cyan, y=-40)
    tk = C["gust"] + 2.0 * k * 0.5 if k < 2 else C["at2"] + 1.0 * (k - 2)
    bake_fn(o, "location", 0, lambda t, tk=tk: -40 + 140 * lin((t - tk) / 0.5))
    windows(o, [(tk, tk + 0.55)]); GUSTS.append(o)
PUSH = arrow_obj("PushArrow", (-30, LZ(BALL_Z) + 10), (1, 0), 18, 5, m_goldglow, y=-27, parent=BAY)
windows(PUSH, [(C["pushes"] - 0.05, C["ball2"] + 0.3)])
LAG = arrow_obj("LagArrow", (6, LZ(BALL_Z)), (-1, 0), 12, 3.4, m_cyan, y=-6, parent=BAY)
windows(LAG, [(C["other"] - 0.05, C["underneath"])])
PULL = arrow_obj("PullArrow", (14, LZ(BALL_Z) + 10), (-1, 0), 18, 5, m_cyan, y=-27, parent=BAY)
windows(PULL, [(C["pulling"] - 0.05, C["underneath"])])

# ================= ghost tower (sway without the damper, exaggerated) =================
bm = bmesh.new(); frustum(bm, 0, H_TOP, 27.5, 15.0)
GHOST_T = mesh_obj("GhostTower", bm, m_ghost)
bake_fn(GHOST_T, "rotation_euler", 1, lambda t: math.atan(ghost_sway(t) / H_TOP) * 1.6)
keyval(ghost_fac, [(0, 0.0), (C["its"], 0.0), (C["its"] + 0.3, 0.55), (C["in"] - 0.25, 0.55), (C["in"], 0.0)])
windows(GHOST_T, [(C["its"], C["in"])])
# tower glass goes red in the storm what-if and the growing-swing beat
keyval(b_glass.inputs["Emission Strength"], [(0, 0.0), (C["seasick"] - 0.3, 0.0), (C["seasick"], 0.35), (C["this"] - 0.1, 0.35), (C["this"], 0.0),
                                             (C["growing"] - 0.5, 0.0), (C["growing"], 0.3), (C["it"] - 0.05, 0.3), (C["it"], 0.0)])
# bake the bend on every piece
for o, z0 in PIECES:
    bake_fn(o, "location", 0, lambda t, z0=z0: bend_at(z0, t)[0])
    bake_fn(o, "rotation_euler", 1, lambda t, z0=z0: bend_at(z0, t)[1])
for o in FRONT_HALVES:
    windows(o, [(T_HOOK1, C["pendulum"]), (C["its"], C["in"]), (T_END[0], T_END[1])])

# ================= top-floor office set (people-feel-it beat; no people) =================
OF = empty("Office", tuple(STUDIO))
def obox(name, x0, x1, y0, y1, z0, z1, m_):
    o = box(name, x0, x1, y0, y1, z0, z1, m_); par(o, OF); return o
FLOOR = obox("OfficeFloor", -14, 14, -16, 6, -0.3, 0.0, m_floor)
obox("OfficeCeil", -9, 9, -6, 6, 3.6, 3.9, m_wall)
obox("OfficeBack", -9, 9, 5.8, 6.0, 0.0, 3.6, m_wall)
for k in range(5):
    obox(f"OfficeWin{k}", -8.0 + k * 3.4, -5.6 + k * 3.4, 5.75, 5.8, 0.5, 3.2, m_win)
obox("OfficeLeft", -9.2, -9.0, -6, 6, 0, 3.6, m_wall); obox("OfficeRight", 9.0, 9.2, -6, 6, 0, 3.6, m_wall)
DESK = obox("Desk", -1.5, 2.5, 1.0, 2.6, 0.72, 0.78, m_box); obox("DeskLeg", -1.4, 2.4, 2.4, 2.5, 0.0, 0.72, m_dark)
LAMPS = []
for k, x in enumerate((-5.0, 0.4, 5.5)):
    piv = par(empty(f"LampPivot{k}", (x, 0.5, 3.6)), OF)
    bm = bmesh.new(); add_bar(bm, (0, 0, 0), (0, 0, -1.4), 0.02); cord = par(mesh_obj(f"Cord{k}", bm, m_dark), piv)
    sh = lathe(f"Shade{k}", [(0.05, -1.35), (0.45, -1.75), (0.43, -1.75), (0.03, -1.37)], m_dark, ang=2 * math.pi, seg=24); par(sh, piv); sh.location = (0, 0, 0)
    bl = cyl(f"Bulb{k}", 0.12, 0.2, "Z", (0, 0, -1.6), m_lamp); par(bl, piv)
    bake_fn(piv, "rotation_euler", 1, lambda t, k=k: math.radians(16) * math.sin(2 * math.pi * (t - T_OFFICE[0]) / 2.0 + k * 0.4)
            * lin((t - T_OFFICE[0] + 0.3) / 0.6) if inw(t, T_OFFICE) else 0.0)
    LAMPS.append(piv)
# kinematic tilting floor plate + loose boxes (rigid body)
TILT = box("TiltPlate", -2.4, 2.4, -1.6, 1.6, -0.02, 0.0, m_floor); TILT.location = (STUDIO.x - 2.2, STUDIO.y - 1.2, STUDIO.z)
BOXES = []
for k in range(7):
    x = STUDIO.x - 3.6 + (k % 3) * 1.05 + random.uniform(-0.1, 0.1); y = STUDIO.y - 1.2 + random.uniform(-0.3, 0.3)
    z = STUDIO.z + 0.36 + (k // 3) * 0.72
    bx = box(f"Carton{k}", -0.4, 0.4, -0.35, 0.35, -0.35, 0.35, m_box)
    bx.location = (x, y, z); BOXES.append(bx)
fx.rigid(BOXES, passive=[TILT], mass=4.0, friction=0.35, bounce=0.05)
try:
    TILT.rigid_body.kinematic = True
    TILT.rotation_mode = "XYZ"
except Exception as e: print("[build] kinematic", e)
bake_fn(TILT, "rotation_euler", 1, lambda t: math.radians(7) * math.sin(2 * math.pi * (t - T_OFFICE[0]) / 2.0) * lin((t - T_OFFICE[0]) / 0.5) if inw(t, T_OFFICE) else 0.0)
# cartons + plate stay unhidden (hidden rigid bodies drop out of the sim); the office set is far off-frame in every other shot

# ================= Mantaflow: fish tank sloshing on the desk (one short shot, bake on the laptop) =================
FLUID_BAKE = "--bake-fluid" in ARGS
TX, TY, TZ = STUDIO.x + 0.5, STUDIO.y + 1.8, STUDIO.z + 0.78
m_tank, b_tank = mat("TankGlass", (0.9, 0.95, 1.0), 0.02); b_tank.inputs["Transmission Weight"].default_value = 1.0
bm = bmesh.new(); wall_half(bm, 0, 0.6, 0.5, 0.5, 1, 0.03); wall_half(bm, 0, 0.6, 0.5, 0.5, -1, 0.03)
TANK = mesh_obj("Tank", bm, m_tank); TANK.location = (TX, TY, TZ); TANK.scale = (1.0, 0.5, 1.0)
FL_DOM = box("FluidDomain", TX - 0.47, TX + 0.47, TY - 0.22, TY + 0.22, TZ + 0.02, TZ + 0.75, m_water)
FL_IN = box("FluidInit", TX - 0.45, TX + 0.45, TY - 0.2, TY + 0.2, TZ + 0.04, TZ + 0.34, m_water); FL_IN.hide_render = True
PADDLE = box("SloshPaddle", TX - 0.02, TX + 0.02, TY - 0.2, TY + 0.2, TZ + 0.05, TZ + 0.3, m_dark); PADDLE.hide_render = True
bake_fn(PADDLE, "location", 0, lambda t: 0.3 * math.sin(2 * math.pi * (t - T_OFFICE[0]) / 2.0) if inw(t, T_OFFICE) else 0.0)
fx.fluid_domain(FL_DOM, FL_IN, eff=[PADDLE], res=64, start=F(T_OFFICE[0] - 0.4), end=F(T_OFFICE[1]), cache_dir=os.path.join(HERE, "cache_fluid"))
try: FL_IN.modifiers["fx_flow"].flow_settings.flow_behavior = "GEOMETRY"
except Exception as e: print("[build] flow behavior", e)
_has_cache = os.path.isdir(os.path.join(HERE, "cache_fluid")) and any(os.scandir(os.path.join(HERE, "cache_fluid")))
WATER_STATIC = box("TankWaterStatic", TX - 0.45, TX + 0.45, TY - 0.2, TY + 0.2, TZ + 0.04, TZ + 0.34, m_water)
if FLUID_BAKE or _has_cache:
    windows(FL_DOM, [(T_OFFICE[0], T_OFFICE[1])]); WATER_STATIC.hide_render = True
else:
    FL_DOM.hide_render = True; FL_DOM.hide_viewport = True; print("[build] fluid domain hidden (no cache): bake on the laptop with --bake-fluid")
    bake_fn(WATER_STATIC, "rotation_euler", 1, lambda t: math.radians(6) * math.sin(2 * math.pi * (t - T_OFFICE[0]) / 2.0 - 0.6) if inw(t, T_OFFICE) else 0.0)
for o_ in (TANK, WATER_STATIC): windows(o_, [(T_OFFICE[0] - 0.05, T_OFFICE[1])])
OK_ = [o for o in OF.children_recursive]
windows(OF, [(T_OFFICE[0] - 0.05, T_OFFICE[1])])

# ================= ground + Geometry Nodes city scatter =================
GROUND = box("Ground", -6000, 6000, -6000, 6000, -0.5, 0.0, m_ground)
bm = bmesh.new(); add_box(bm, -12, 12, -12, 12, 0, 70)
CITY = mesh_obj("CityBlockInst", bm, m_bldg)
SCS = []
for k, (x0, x1, y0, y1) in enumerate([(-1500, -140, -150, 1500), (140, 1500, -150, 1500), (-140, 140, 140, 1500), (-2500, 2500, -2600, -1450), (220, 1500, -1450, -150)]):
    s_ = box(f"CityScatter{k}", x0, x1, y0, y1, -0.6, -0.55, m_ground); SCS.append(s_)
    fx.scatter(s_, CITY, density=0.00005, scale_min=0.35, scale_max=0.9, seed=3 + k)
FAR = box("CityScatterFar", -4000, 4000, 1400, 4000, -0.6, -0.55, m_ground)
fx.scatter(FAR, CITY, density=0.00002, scale_min=0.6, scale_max=1.4, seed=11)

# ================= particles: rain in the two storms, heat motes at the dampers =================
def plane(name, x0, x1, y0, y1, z):
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]; bm.faces.new(vs)
    return mesh_obj(name, bm, m_dark)
RAIN1 = plane("RainEmitter1", -160, 160, -260, 60, 470)
fx.particles(RAIN1, "rain", F(T_STORM1[0] - 1.0), F(T_STORM1[1]), count=9000)
RAIN3 = plane("RainEmitter3", -160, 160, -260, 60, 470)
fx.particles(RAIN3, "rain", F(T_END[0] - 1.0), F(T_END[1]), count=9000)
for em_ in (RAIN1, RAIN3):
    em_.hide_render = False
    for ms in em_.modifiers:
        if ms.type == "PARTICLE_SYSTEM":
            ps = ms.particle_system.settings; ps.particle_size = 0.45; ps.lifetime = 70; ps.normal_factor = -14.0
            em_.show_instancer_for_render = False
windows(RAIN1, [(T_STORM1[0], T_STORM1[1])]); windows(RAIN3, [(T_END[0], T_END[1])])
HEATE = cyl("HeatEmitter", 6.5, 0.2, "Z", (0, 0, 1.2), m_dark); par(HEATE, BAY); HEATE.location = (0, 0, 0)
fx.particles(HEATE, "sparks", F(C["turn"]), F(C["its"] - 0.4), count=180)
for ms in HEATE.modifiers:
    if ms.type == "PARTICLE_SYSTEM": ms.particle_system.settings.normal_factor = 0.8; ms.particle_system.settings.effector_weights.gravity = -0.05
HEATE.show_instancer_for_render = False
windows(HEATE, [(C["turn"], C["its"])])

# ================= world: city HDRI light + own sky gradient, mixed to a storm sky =================
fx.hdri("city", strength=0.8, rotation_deg=120.0, show_background=False)
STORM_KEYS = [(0, 0.0), (T_STORM1[0] - 0.05, 0.0), (T_STORM1[0], 1.0), (T_STORM1[1] - 0.05, 1.0), (T_STORM1[1], 0.0),
              (T_TYPH[0] - 0.05, 0.0), (T_TYPH[0], 1.0), (T_TYPH[1] - 0.05, 1.0), (T_TYPH[1], 0.0),
              (T_END[0] - 0.05, 0.0), (T_END[0], 1.0), (T_END[1] - 0.05, 1.0), (T_END[1], 0.0), (DUR, 0.0)]
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    hdr_bg = next(n for n in wn if n.type == "BACKGROUND" and n is not plain)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    def ramp(cols):
        cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
        e[0].position = 0.0; e[0].color = cols[0]; e[1].position = 0.45; e[1].color = cols[1]
        wl.new(grad.outputs["Fac"], cr.inputs[0]); return cr
    clear = ramp([(0.95, 0.80, 0.62, 1), (0.20, 0.42, 0.78, 1)])
    storm = ramp([(0.15, 0.17, 0.20, 1), (0.05, 0.06, 0.08, 1)])
    mx = wn.new("ShaderNodeMix"); mx.data_type = "RGBA"
    wl.new(clear.outputs[0], mx.inputs[6]); wl.new(storm.outputs[0], mx.inputs[7]); wl.new(mx.outputs[2], plain.inputs["Color"])
    plain.inputs["Strength"].default_value = 1.0
    keyval(mx.inputs[0], STORM_KEYS)
    keyval(hdr_bg.inputs["Strength"], [(t_, 0.8 - 0.55 * v) for t_, v in STORM_KEYS])
    print("[build] sky gradient + storm mix on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.4; sun_d.color = (1.0, 0.86, 0.68); sun_d.angle = math.radians(2.0)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
for t_, v in STORM_KEYS:
    sun_d.energy = 3.4 - 3.0 * v; sun_d.keyframe_insert("energy", frame=F(t_))
fx.glare(threshold=1.0, strength=0.55, size=7)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 12000
BZ = BALL_Z
HOOK_SHOT = ((-8.5, -17.0, BZ + 2.4), (0.0, 0.0, BZ - 0.4), 26)
SO = lambda x, y, z: STUDIO + Vector((x, y, z))
SIDE = ((0.0, -980.0, 230.0), (0.0, 0.0, 255.0), 30)
STORM_EXT = ((-95.0, -240.0, 300.0), (0.0, 0.0, 385.0), 26)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK_SHOT),
    (T_HOOK1 - 0.05, (-10.0, -20.0, BZ + 3.0), (0.0, 0.0, BZ - 0.2), 26),
    (T_HOOK1, *STORM_EXT, "cut"),
    (C["this"] - 0.05, (-82.0, -212.0, 312.0), (0.0, 0.0, 385.0), 26),
    (C["this"], (-320.0, -800.0, 40.0), (0.0, 0.0, 235.0), 24, "cut"),
    (C["tall2"] - 0.05, (-270.0, -700.0, 60.0), (0.0, 0.0, 245.0), 24),
    (C["tall2"], *SIDE, "cut"),
    (C["it"] - 0.05, (0.0, -930.0, 235.0), (0.0, 0.0, 258.0), 30),
    (C["it"], SO(-1.0, -6.0, 1.7), SO(-1.0, 0.5, 1.2), 22, "cut"),
    (C["so"] - 0.05, SO(-0.6, -5.2, 1.6), SO(-1.0, 0.5, 1.2), 22),
    (C["so"], (-48.0, -125.0, 398.0), (0.0, 0.0, 380.0), 28, "cut"),
    (C["pendulum"] - 0.05, (-42.0, -108.0, 394.0), (0.0, 0.0, 378.0), 28),
    (C["pendulum"], (-11.0, -24.0, BZ + 5.0), (0.0, 0.0, BZ + 1.2), 24, "cut"),
    (C["eighteen"] - 0.05, (-9.0, -20.0, BZ + 3.5), (0.0, 0.0, BZ + 0.2), 24),
    (C["eighteen"], (0.0, -14.5, BZ + 0.8), (0.0, 0.0, BZ + 0.9), 28, "cut"),
    (C["cables"] - 0.05, (0.0, -15.5, BZ + 1.2), (0.0, 0.0, BZ + 1.0), 28),
    (C["cables"], (-15.0, -31.0, BZ + 2.0), (0.0, 0.0, BZ + 3.5), 22, "cut"),
    (C["trick"] - 0.05, (-17.0, -35.0, BZ + 2.0), (0.0, 0.0, BZ + 3.5), 22),
    (C["trick"], (0.0, -40.0, BZ + 3.0), (0.0, 0.0, BZ + 3.0), 26, "cut"),
    (C["when"] - 0.05, (0.0, -35.0, BZ + 3.0), (0.0, 0.0, BZ + 2.5), 26),
    (C["when"], (0.0, -200.0, 330.0), (0.0, 0.0, 348.0), 30, "cut"),
    (C["underneath"] - 0.05, (0.0, -185.0, 335.0), (0.0, 0.0, 350.0), 30),
    (C["underneath"], (-6.5, -11.5, Z87 + 2.2), (0.0, 0.0, Z87 + 3.4), 20, "cut"),
    (C["its"] - 0.05, (-7.6, -12.8, Z87 + 2.7), (0.0, 0.0, Z87 + 3.4), 20),
    (C["its"], *SIDE, "cut"),
    (C["in"] - 0.05, (0.0, -940.0, 232.0), (0.0, 0.0, 255.0), 30),
    (C["in"], (-9.5, -19.5, BZ + 1.2), (0.0, 0.0, BZ - 0.6), 26, "cut"),
    (C["can"] - 0.05, (-8.0, -17.0, BZ + 0.6), (0.0, 0.0, BZ - 0.6), 26),
    (C["can"], (-3.0, -16.0, RING_Z + 3.0), (-0.8, 0.0, RING_Z + 2.4), 24, "cut"),
    (C["so2"] - 0.05, (-3.6, -17.5, RING_Z + 3.2), (-0.8, 0.0, RING_Z + 2.4), 24),
    (C["so2"], *STORM_EXT, "cut"),
    (C["calm"] - 0.05, (-82.0, -210.0, 322.0), (0.0, 0.0, 385.0), 26),
    (C["calm"], (-11.0, -22.0, BZ + 3.6), (0.0, 0.0, BZ - 0.3), 26, "cut"),
    (DUR - 0.25, *HOOK_SHOT),
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
    cam_loc.append(l0); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 20; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(20.0, min(6000.0, 180.0 * ((cl - ct).length / 30.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
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
fx.bake_rigid(1, F(T_OFFICE[1]))
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def anchor(name, parent, loc):
    return par(empty("A_" + name, loc), parent)
ROOF = next(o for o, z in PIECES if o.name == "Roof")
AOBJ = {
    "ball": anchor("ball", BALL, (-R_BALL - 0.3, 0, 0.8)), "cables": anchor("cables", PEND, (-3.4, -1.4, -L_PEND * 0.45)),
    "pivot": anchor("pivot", PEND, (0, 0, 0.6)),
    "damper": DAMPERS[6][2], "pin": anchor("pin", PEND, (0, 0, -L_PEND - R_BALL - 1.5)), "ring": anchor("ring", BAY, (-2.4, -1.0, LZ(RING_Z))),
    "floor87": anchor("floor87", BAY, (-8.0, -3.0, 0.0)), "floor92": anchor("floor92", BAY, (-8.0, -3.0, LZ(Z92))),
    "top": anchor("top", ROOF, (0, 0, 70.0)), "lamp": anchor("lamp", LAMPS[1], (0, 0, -1.8)), "boxes": BOXES[3],
}
anchors = {k: [] for k in AOBJ}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, o in AOBJ.items():
        p = world_to_camera_view(scene, cam, o.matrix_world.translation)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"storm1": RR(*T_STORM1), "city": RR(*T_CITY), "bend": RR(*T_BEND), "rhythm": RR(*T_RHY), "office": RR(*T_OFFICE),
          "cut_open": round(C["pendulum"], 3), "build": RR(*T_BUILD), "tune": RR(*T_TUNE), "lag": RR(*T_LAG), "damp": RR(*T_DAMP),
          "ghost": RR(*T_GHOST), "typhoon": RR(*T_TYPH), "limit": RR(*T_LIMIT), "end_storm": RR(*T_END), "loop": round(T_LOOP, 3),
          "plate_lands": [round(T_BUILD[0] + (T_BUILD[1] - T_BUILD[0] - 0.7) * i / (NPL - 1) + 0.5, 3) for i in range(0, NPL, 4)],
          "gusts": [round(C["gust"] + 1.0 * k, 3) for k in range(2)] + [round(C["at2"] + 1.0 * k, 3) for k in range(2)],
          "swing_peaks_hook": round(P0, 3)}
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
