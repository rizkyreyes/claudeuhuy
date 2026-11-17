# Wind-Turbine-3D part 1: how a wind turbine is built. Claim-first hook ("A buried slab of concrete and a pile of dirt."):
# finished turbine on a prairie, the ground cut open at y = 0 so the buried spread footing (half section) and the backfill read in the first frame
# -> tilt up to the spinning rotor -> wide: wind streaks + red push arrow at the hub, red ghost turbine tips -> back to bare ground: the pit is dug
# (mud particles) -> rebar cage builds in three steps (bottom mat, top mat + hoops, pedestal cage), cyan -> anchor-bolt ring rises, gold ->
# a mixer truck pours, the concrete level rises in the cut (optional Mantaflow pour stream, bake on the laptop) -> backfill: soil clumps fall in
# (rigid body) and the backfill layer rises -> gold down arrows (soil weight) + cyan width bar -> four steel tower sections lie on the ground
# -> crawler crane lowers section 1 over the bolts, nuts spark-tighten -> sections 2-4 stack -> camera rides up: hub height bar (340 ft) ->
# nacelle lift (cutaway window: gearbox + generator teased for part 2) -> one blade lifted and pinned to the hub -> alternative: the whole
# rotor raised from the ground, tilts upright -> rotor spins, camera falls back to the buried slab = the first frame (loop).
# Illustrative (1 unit = 1 m): hub height 103 m (US 2023 average 103.4 m), blade 64 m (DOE average ~210 ft), footing 19 m wide and 3.5 m deep
# (typical spread footing, not a specific project), rebar and bolts drawn ~2x thick and fewer than real so a phone can see them.
# Generic turbine, crane and truck: no brand, no real place, no people.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu] [--bake-fluid]
import bpy, bmesh, json, math, os, random, sys

from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 0.6, 2)   # part-1 ending: spoken part-2 tease (Rizky 17 Nov)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(12)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')

CUES = [("a", "A"), ("buried", "buried"), ("slab", "slab"), ("concrete", "concrete"), ("pile", "pile"), ("dirt", "dirt."),
        ("thats", "That's"), ("holds", "holds"), ("wind", "wind"), ("turbine", "turbine"), ("up", "up."),
        ("uptop", "Up"), ("shoves", "shoves"), ("blades", "blades,"), ("tip", "tip"), ("tower", "tower"), ("over", "over."),
        ("so", "So"), ("build", "build"), ("hole", "hole."),
        ("workers", "Workers"), ("cage", "cage"), ("rebar", "rebar,"), ("fifty", "fifty"), ("tons", "tons"),
        ("middle", "middle,"), ("ring", "ring"), ("anchor", "anchor"), ("bolts", "bolts,"), ("hundred", "hundred,"), ("sticks", "sticks"), ("straight", "straight"),
        ("then", "Then"), ("trucks", "trucks"), ("pour", "pour"), ("five", "five"), ("cubic", "cubic"), ("yards", "yards."),
        ("once", "Once"), ("hardens", "hardens,"), ("dirt2", "dirt"), ("back", "back"), ("top", "top."),
        ("soils", "soil's"), ("weight", "weight"), ("pin", "pin"), ("down", "down,"), ("wider", "wider"), ("tip2", "tip."),
        ("now", "Now"), ("tower2", "tower."), ("arrives", "arrives"), ("sections", "sections."),
        ("crane", "crane"), ("lowers", "lowers"), ("first", "first"), ("anchor2", "anchor"), ("crews", "crews"), ("tighten", "tighten"), ("nut", "nut."),
        ("each", "Each"), ("section", "section"), ("below", "below."),
        ("stacked", "Stacked"), ("average", "average"), ("hub", "hub"), ("three", "three"), ("feet", "feet"), ("air", "air."),
        ("next", "Next,"), ("big", "big"), ("nacelle", "nacelle,"), ("machine", "machine"), ("top2", "top."),
        ("smaller", "smaller"), ("fifty2", "fifty"), ("tons2", "tons."),
        ("last", "Last"), ("blades2", "blades,"), ("two", "two"), ("long", "long."),
        ("some", "Some"), ("lift", "lift"), ("time", "time."),
        ("others", "Others"), ("bolt", "bolt"), ("all", "all"), ("ground", "ground"), ("raise", "raise"), ("rotor", "rotor"), ("once2", "once."),
        ("and", "And"), ("every", "every"), ("ton", "ton"), ("rests", "rests"), ("on", "on")]
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
R_SLAB, Z_BOT, Z_EDGE, Z_TAPER = 9.5, -3.5, -2.6, -1.6      # spread footing: 19 m wide, 0.9 m edge, tapered top
R_PED, Z_PED = 3.2, 0.3                                     # pedestal, top 0.3 m above grade
R_PIT = 11.0
HUB_Z = 103.3                                               # tower top (US 2023 average hub height 103.4 m)
SEC_Z = [Z_PED, 22.3, 48.3, 75.3, HUB_Z]                    # 4 tower sections
R_T0, R_T1 = 2.25, 1.5
def r_tower(z): return R_T0 + (R_T1 - R_T0) * (z - Z_PED) / (HUB_Z - Z_PED)
BLADE = 64.0
HUB = Vector((0.0, -4.2, HUB_Z + 2.4))                      # rotor faces the camera (-y)
def slab_r(z):
    if z <= Z_EDGE: return R_SLAB
    if z <= Z_TAPER: return R_SLAB + (R_PED - R_SLAB) * (z - Z_EDGE) / (Z_TAPER - Z_EDGE)
    return R_PED

# ================= key times =================
T_HOLE0 = C["so"]                                            # cut: finished turbine -> bare ground
T_DIG0, T_DIG1 = C["build"], C["workers"] - 0.1
T_MAT1, T_MAT2, T_MAT3 = C["cage"], C["rebar"], C["fifty"]   # cage steps
T_BOLT0, T_BOLT1 = C["ring"], C["straight"] + 0.3
T_POUR0, T_POUR1 = C["pour"], C["once"] - 0.1
T_FILL0, T_FILL1 = C["dirt2"] - 0.2, C["soils"] - 0.1
T_SEC = C["arrives"]                                          # sections lie on the ground
T_S1A, T_S1B = C["crane"], C["anchor2"] + 0.35               # section 1 lowered
T_S2, T_S3, T_S4 = C["each"], C["section"], C["below"]
T_NAC0, T_NAC1 = C["next"], C["machine"] - 0.1
T_BL0, T_BL1 = C["last"], C["time"] + 0.1
T_ROT0, T_ROT1 = C["others"], C["once2"] + 0.25
T_LOOP = C["and"]
FIN = (0.0, T_HOLE0)                                          # finished turbine window (hook)

# ================= materials =================
m_grass = mat("Grass", (0.20, 0.30, 0.10), 0.9, noise=6.0)[0]
m_soil, b_soil = mat("Soil", (0.16, 0.09, 0.045), 0.95, noise=3.0)
m_soil2, b_soil2 = mat("SoilDeep", (0.22, 0.13, 0.065), 0.95, noise=2.0)
m_back, b_back = mat("Backfill", (0.42, 0.26, 0.12), 0.95, noise=5.0, emit_rgb=(0.98, 0.74, 0.27))
m_con, b_con = mat("Concrete", (0.46, 0.46, 0.45), 0.7, noise=8.0, emit_rgb=(0.98, 0.74, 0.27))
m_rebar, b_rebar = mat("Rebar", (0.25, 0.20, 0.17), 0.5, 0.8, emit_rgb=(0.30, 0.92, 1.0))
m_bolt, b_bolt = mat("AnchorBolt", (0.75, 0.62, 0.30), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
m_tower, b_tower = mat("TowerWhite", (0.86, 0.87, 0.88), 0.35, emit_rgb=(0.30, 0.92, 1.0))
m_flange, b_flange = mat("Flange", (0.55, 0.56, 0.58), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
m_blade, b_blade = mat("Blade", (0.90, 0.91, 0.92), 0.3, emit_rgb=(0.98, 0.74, 0.27))
m_gear, b_gear = mat("Gearbox", (0.45, 0.42, 0.38), 0.35, 0.9, emit_rgb=(0.98, 0.74, 0.27))
m_gen, b_gen = mat("Generator", (0.25, 0.30, 0.34), 0.35, 0.8, emit_rgb=(0.30, 0.92, 1.0))
m_dark, _ = mat("DarkSteel", (0.08, 0.08, 0.09), 0.5, 0.6)
m_crane, _ = mat("CraneYellow", (0.85, 0.62, 0.10), 0.45, 0.2)
m_truck, _ = mat("TruckWhite", (0.80, 0.80, 0.78), 0.4)
m_drum, _ = mat("Drum", (0.70, 0.40, 0.12), 0.4, 0.3)
m_red, b_red = mat("RedArrow", (1.0, 0.30, 0.24), 0.4, emit_rgb=(1.0, 0.30, 0.24))
m_gold, b_gold = mat("GoldArrow", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27))
m_cyan, b_cyan = mat("CyanBar", (0.30, 0.92, 1.0), 0.4, emit_rgb=(0.30, 0.92, 1.0))
m_wind, b_wind = mat("WindStreak", (0.85, 0.97, 1.0), 0.4, emit_rgb=(0.85, 0.97, 1.0))
m_cable, _ = mat("Cable", (0.05, 0.05, 0.05), 0.4, 0.8)
m_wet, b_wet = mat("WetConcrete", (0.42, 0.42, 0.41), 0.15, emit_rgb=(0.98, 0.74, 0.27))
m_rock, _ = mat("Rock", (0.20, 0.19, 0.17), 0.8, noise=12.0)
m_tuft, _ = mat("Tuft", (0.26, 0.36, 0.12), 0.9)
for b_ in (b_red, b_gold, b_cyan): b_.inputs["Emission Strength"].default_value = 3.0
b_wind.inputs["Emission Strength"].default_value = 2.0
red_ghost, red_fac = ghost("RedGhost", (1.0, 0.30, 0.24))

# ================= ground with the pit, cut at y = 0 =================
def ground_with_pit():
    bm = bmesh.new()
    # around the pit: four boxes + a ring (built as a lathe annulus) -> simple, no boolean
    add_box(bm, -4000, -R_PIT, 0, 4000, -14, 0); add_box(bm, R_PIT, 4000, 0, 4000, -14, 0)
    add_box(bm, -R_PIT, R_PIT, R_PIT, 4000, -14, 0)
    o = mesh_obj("GroundOuter", bm, [m_grass, m_soil])
    return o
G_OUT = ground_with_pit()
# the corner fill between the boxes and the round pit (half annulus r = R_PIT .. square) as a lathe ring + a pit floor
G_RING = lathe("GroundRing", [(R_PIT, -14), (R_PIT * 1.42, -14), (R_PIT * 1.42, 0), (R_PIT, 0)], m_soil, a0=0.0, ang=math.pi, seg=48, smooth=False)
G_RING.data.materials.append(m_grass)
# trim the ring to the square |x| <= R_PIT, y <= R_PIT with a boolean
_trim = box("RingTrim", -R_PIT, R_PIT, -0.01, R_PIT, -15, 1, m_soil)
bo = G_RING.modifiers.new("trim", "BOOLEAN"); bo.operation = "INTERSECT"; bo.object = _trim; bo.solver = "EXACT"
bpy.context.view_layer.objects.active = G_RING
try: bpy.ops.object.modifier_apply(modifier="trim")
except Exception as e: print("[build] ring trim apply failed", e)
bpy.data.objects.remove(_trim, do_unlink=True)
PIT_FLOOR = lathe("PitFloor", [(0, -14), (R_PIT, -14), (R_PIT, Z_BOT - 0.15), (0, Z_BOT - 0.15)], m_soil2, ang=math.pi, smooth=False)
# grass top colour on every face pointing up at z = 0
for o_ in (G_OUT, G_RING):
    for p in o_.data.polygons:
        if p.normal.z > 0.9 and p.center.z > -0.05: p.material_index = 1 if o_ is G_RING else 0
        else: p.material_index = 0 if o_ is G_RING else 1
# soil plug that fills the pit before the dig (scaled down from its bottom = digging)
H_PLUG = -(Z_BOT - 0.15)
def plug_scale(t): return 1.0 - ease((t - T_DIG0) / (T_DIG1 - T_DIG0))
PLUG = lathe("SoilPlug", [(0, 0), (R_PIT, 0), (R_PIT, H_PLUG), (0, H_PLUG)], [m_soil, m_grass], ang=math.pi, smooth=False)
for p in PLUG.data.polygons: p.material_index = 1 if (p.normal.z > 0.9 and p.center.z > H_PLUG - 0.05) else 0
PLUG.location = (0, 0, Z_BOT - 0.15)
bake_scale(PLUG, lambda t: (1, 1, max(0.001, plug_scale(t)) if t >= T_HOLE0 else 1.0))
windows(PLUG, [(T_HOLE0, T_DIG1 + 0.05)])
emb = bmesh.new(); bmesh.ops.create_grid(emb, x_segments=4, y_segments=4, size=6); EM_DIG = mesh_obj("DigEmitter", emb, m_soil)
EM_DIG.location = (0, 5, 0.2); EM_DIG.hide_render = False
fx.particles(EM_DIG, "mud", F(T_DIG0), F(T_DIG1), count=300)
fx.particles(EM_DIG, "dust", F(T_DIG0), F(T_DIG1 + 0.3), count=250)
bake_loc(EM_DIG, lambda t: (0, 5, (Z_BOT + 0.3) + H_PLUG * plug_scale(t)))

# ================= foundation (half section, y >= 0) =================
SLAB_PROF = [(0, Z_BOT), (R_SLAB, Z_BOT), (R_SLAB, Z_EDGE), (R_PED, Z_TAPER), (R_PED, Z_PED), (0, Z_PED)]
SLAB = lathe("Footing", SLAB_PROF, m_con, ang=math.pi, smooth=False)
# concrete appears with the pour: shader mask z < level (keyed), plus a wet level disc
nt = m_con.node_tree; geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
LEVEL = nt.nodes.new("ShaderNodeValue"); LEVEL.name = "PourLevel"
def level_t(t):
    if t < T_POUR0: return Z_BOT - 1.0 if t >= T_HOLE0 else Z_PED + 1.0
    return Z_BOT + (Z_PED + 0.02 - Z_BOT) * ease((t - T_POUR0) / (T_POUR1 - T_POUR0))
keyval(LEVEL.outputs[0], [(0, Z_PED + 1.0), (T_HOLE0 - 0.04, Z_PED + 1.0), (T_HOLE0, Z_BOT - 1.0), (T_POUR0, Z_BOT - 0.02), (T_POUR1, Z_PED + 0.02)])
lt = MATH(nt, "LESS_THAN", sep.outputs["Z"], LEVEL.outputs[0])
out_ = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"); trn = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(lt, mx.inputs[0]); nt.links.new(trn.outputs[0], mx.inputs[1]); nt.links.new(b_con.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out_.inputs["Surface"])
WET = lathe("WetLevel", [(0, 0), (1.0, 0), (1.0, 0.02), (0, 0.02)], m_wet, ang=math.pi, smooth=False)
bake_loc(WET, lambda t: (0, 0, level_t(t)))
bake_scale(WET, lambda t: (slab_r(level_t(t)) - 0.02, slab_r(level_t(t)) - 0.02, 1))
windows(WET, [(T_POUR0, T_POUR1)])
glow(b_con, [(0, 0.0)] + pulse(C["buried"], 0.5, hold=1.2) + pulse(C["thats"] + 0.2, 0.0) + pulse(C["wider"], 0.8, hold=0.8))

# rebar cage: 3 steps (bottom mat, top mat + hoops, pedestal cage)
def cage_part(name, build):
    bm = bmesh.new(); build(bm); return mesh_obj(name, bm, m_rebar)
W_BAR = 0.07
def hoop(bm, r, z, n=28, w=W_BAR):
    pts = [(r * math.cos(math.pi * i / n), max(0.06, r * math.sin(math.pi * i / n)), z) for i in range(n + 1)]
    for p0, p1 in zip(pts, pts[1:]): add_bar(bm, p0, p1, w)
def mat_bottom(bm):
    for i in range(25):
        a = math.pi * i / 24
        add_bar(bm, (0.4 * math.cos(a), max(0.06, 0.4 * math.sin(a)), Z_BOT + 0.15), (9.2 * math.cos(a), max(0.06, 9.2 * math.sin(a)), Z_BOT + 0.15), W_BAR)
    for r in (2.0, 4.0, 6.0, 8.0, 9.2): hoop(bm, r, Z_BOT + 0.22)
def mat_top(bm):
    for i in range(25):
        a = math.pi * i / 24; c, s = math.cos(a), math.sin(a)
        p0 = (9.2 * c, max(0.06, 9.2 * s), Z_EDGE - 0.12); p1 = (R_PED - 0.2) * c, max(0.06, (R_PED - 0.2) * s), Z_TAPER - 0.12
        add_bar(bm, p0, p1, W_BAR); add_bar(bm, (9.2 * c, max(0.06, 9.2 * s), Z_BOT + 0.15), p0, W_BAR)
    for r in (4.5, 6.5, 8.5): hoop(bm, r, Z_EDGE - 0.12 + (Z_TAPER - Z_EDGE) * (9.2 - r) / (9.2 - R_PED))
def ped_cage(bm):
    for i in range(17):
        a = math.pi * i / 16; c, s = math.cos(a), math.sin(a)
        for r in (R_PED - 0.2, 1.6):
            add_bar(bm, (r * c, max(0.06, r * s), Z_BOT + 0.2), (r * c, max(0.06, r * s), Z_PED - 0.1), W_BAR)
    for z in (Z_TAPER, -0.9, -0.2): hoop(bm, R_PED - 0.2, z, n=16); hoop(bm, 1.6, z, n=12)
CAGE = [cage_part("RebarBottom", mat_bottom), cage_part("RebarTop", mat_top), cage_part("RebarPedestal", ped_cage)]
for o_, t0 in zip(CAGE, (T_MAT1, T_MAT2, T_MAT3)):
    vis(o_, 1, False); vis(o_, F(T_HOLE0), True); vis(o_, F(t0), False)
    bake_loc(o_, lambda t, t0=t0: (0, 0, drop(t, t0, h=2.5, d=0.45) if t >= T_HOLE0 else 0.0))
glow(b_rebar, [(0, 0.0), (T_MAT1 - 0.01, 0.0), (T_MAT1 + 0.2, 2.5), (T_POUR0, 2.5), (T_POUR1, 0.6), (T_FILL1, 0.0)] + pulse(C["buried"], 0.0))

# anchor-bolt ring: 2 rings x 30 bolts in the half (= 120 in the full ring)
def bolts(bm):
    for r, n, off in ((2.55, 30, 0.0), (2.95, 30, 0.5)):
        for i in range(n):
            a = math.pi * (i + off + 0.5) / n
            x, y = r * math.cos(a), max(0.07, r * math.sin(a))
            add_cyl(bm, 0.045, Z_PED + 0.55 - (Z_BOT + 0.3), "Z", (x, y, (Z_PED + 0.55 + Z_BOT + 0.3) / 2), seg=6)
            add_cyl(bm, 0.09, 0.08, "Z", (x, y, Z_PED + 0.12), seg=6)          # nut
    hoop(bm, 2.75, Z_BOT + 0.35, n=24, w=0.12); hoop(bm, 2.75, Z_PED - 0.05, n=24, w=0.12)   # embed + template rings
BOLTS = cage_part("AnchorBolts", bolts); BOLTS.data.materials[0] = m_bolt
vis(BOLTS, 1, False); vis(BOLTS, F(T_HOLE0), True); vis(BOLTS, F(T_BOLT0), False)
bake_loc(BOLTS, lambda t: (0, 0, (-4.5 * (1 - ease((t - T_BOLT0) / (T_BOLT1 - T_BOLT0)))) if t >= T_HOLE0 else 0.0))
glow(b_bolt, [(0, 0.0), (T_BOLT0 - 0.01, 0.0), (T_BOLT0 + 0.3, 3.0), (T_POUR0, 1.2), (T_S1A, 1.0), (T_S1B, 3.0), (C["each"], 0.0)])

# backfill (half annulus between pedestal and pit wall, from the slab top to grade, slightly mounded)
def backfill_mesh():
    prof = [(R_PED + 0.02, Z_TAPER), (R_SLAB, Z_EDGE), (R_SLAB, Z_BOT), (R_PIT - 0.01, Z_BOT), (R_PIT - 0.01, 0.0), (R_PIT * 0.7, 0.25), (R_PED + 0.02, 0.15)]
    return lathe("Backfill", [(r, z - Z_BOT) for r, z in prof], m_back, ang=math.pi, smooth=False)
BACK = backfill_mesh(); BACK.location = (0, 0, Z_BOT)
def back_scale(t):
    if t < T_HOLE0: return 1.0
    return max(0.001, ease((t - T_FILL0) / (T_FILL1 - T_FILL0)))
bake_scale(BACK, lambda t: (1, 1, back_scale(t)))
windows(BACK, [FIN, (T_FILL0, DUR)])
# (the slab region of the backfill profile is inside the footing; outside the footing the soil fills down to the pit floor)
glow(b_back, [(0, 0.0)] + pulse(C["pile"], 1.0, hold=0.9) + pulse(C["pin"] - 0.2, 0.8, hold=1.0))
# soil clumps dropped in by the loader (rigid body), resting on a passive collider at the slab top
CLUMPS = []
for i in range(14):
    a = math.pi * (0.1 + 0.8 * random.random()); r = 5.0 + 4.5 * random.random()
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.45 + 0.35 * random.random())
    for v in bm.verts: v.co *= 0.8 + 0.4 * random.random()
    o_ = mesh_obj(f"Clump{i}", bm, m_back); o_.location = (r * math.cos(a), max(0.6, r * math.sin(a)), 5.0 + 3.0 * random.random())
    CLUMPS.append(o_)
CATCH = lathe("ClumpCatch", [(R_PED, Z_EDGE + 0.6), (R_PIT, Z_EDGE + 0.6), (R_PIT, Z_EDGE + 0.4), (R_PED, Z_EDGE + 0.4)], m_soil, ang=math.pi, smooth=False)
CATCH.hide_render = True
fx.rigid(CLUMPS, passive=[CATCH], mass=40.0, friction=0.8, bounce=0.05)
RB_FRAME0 = F(T_FILL0)
for o_ in CLUMPS: windows(o_, [(T_FILL0, T_FILL1 + 0.2)])
emf = bmesh.new(); bmesh.ops.create_grid(emf, x_segments=4, y_segments=4, size=7); EM_FILL = mesh_obj("FillEmitter", emf, m_soil)
EM_FILL.location = (0, 4, Z_EDGE + 0.8)
fx.particles(EM_FILL, "dust", F(T_FILL0 + 0.4), F(T_FILL1), count=300)

# ================= tower: 4 sections with flanges =================
def section(i):
    z0, z1 = SEC_Z[i], SEC_Z[i + 1]; ro0, ro1 = r_tower(z0), r_tower(z1)
    prof = [(ro0 - 0.05, 0), (ro0 + 0.12, 0), (ro0 + 0.12, 0.12), (ro0, 0.12), (ro1, z1 - z0 - 0.12), (ro1 + 0.12, z1 - z0 - 0.12),
            (ro1 + 0.12, z1 - z0), (ro1 - 0.05, z1 - z0)]
    o_ = lathe(f"TowerSec{i + 1}", prof, m_tower, ang=2 * math.pi, seg=48)
    return o_
SECS = [section(i) for i in range(4)]
FL_RINGS = []
for i in range(1, 4):
    z = SEC_Z[i]; r = r_tower(z)
    FL_RINGS.append(lathe(f"FlangeGlow{i}", [(r + 0.02, z - 0.14), (r + 0.16, z - 0.14), (r + 0.16, z + 0.14), (r + 0.02, z + 0.14)], m_flange, ang=2 * math.pi, seg=48))
# lying positions (on blocks next to the pit, x > 0, along y)
LIE = [Vector((22.0 + 6.5 * i, 30.0, 2.8)) for i in range(4)]
def sec_state(i, t):
    """(location of the section's bottom centre, rotation x) -- standing = (0,0,z0), lying = along +y."""
    z0 = SEC_Z[i]
    if t < T_HOLE0: return Vector((0, 0, z0)), 0.0
    t_lift = [T_S1A, T_S2 - 0.9, T_S3 - 0.75, T_S4 - 0.6][i]; t_land = [T_S1B, T_S2 + 0.25, T_S3 + 0.3, T_S4 + 0.45][i]
    if t < t_lift: return LIE[i] - Vector((0, (SEC_Z[i + 1] - z0) / 2, 0)), -math.pi / 2
    if t >= t_land: return Vector((0, 0, z0)), 0.0
    u = (t - t_lift) / (t_land - t_lift)
    up = ease(min(1.0, u / 0.55)); down = ease(max(0.0, (u - 0.55) / 0.45))
    a = LIE[i] - Vector((0, (SEC_Z[i + 1] - z0) / 2, 0)); hi = Vector((0, 0, z0 + 6.0))
    p = a.lerp(hi, up) if u < 0.55 else hi.lerp(Vector((0, 0, z0)), down)
    rot = -math.pi / 2 * (1 - ease(min(1.0, u / 0.45)))
    return p, rot
for i, o_ in enumerate(SECS):
    vals = [sec_state(i, t) for t in TS]
    for ax in range(3): bake(o_, "location", ax, [v[0][ax] for v in vals])
    bake(o_, "rotation_euler", 0, [v[1] for v in vals])
    vis(o_, 1, False); vis(o_, F(T_HOLE0), True); vis(o_, F(T_SEC - 0.1), False)
for i, o_ in enumerate(FL_RINGS):
    t_land = [T_S2 + 0.25, T_S3 + 0.3, T_S4 + 0.45][i]
    vis(o_, 1, False); vis(o_, F(T_HOLE0), True); vis(o_, F(t_land), False)
glow(b_flange, [(0, 0.0), (T_S2, 0.0), (T_S2 + 0.3, 3.0), (C["stacked"] + 0.4, 3.0), (C["average"], 0.0)])
glow(b_tower, [(0, 0.0)] + pulse(C["tower2"], 0.0))
# support blocks for the lying sections
for i in range(4):
    for dy in (-8.0, 8.0):
        box(f"Crib{i}{dy}", LIE[i].x - 1.2, LIE[i].x + 1.2, LIE[i].y + dy - 0.8, LIE[i].y + dy + 0.8, 0, 0.6, m_dark)
CRIBS = [o for o in CL.objects if o.name.startswith("Crib")]
for o_ in CRIBS: windows(o_, [(T_SEC - 0.1, C["average"])])

# ================= nacelle (cutaway window on -x: gearbox + generator, teased for part 2) =================
NAC = empty("Nacelle", (0, 0, HUB_Z))
def nac_shell(bm):
    vs = add_box(bm, -2.1, 2.1, -3.6, 9.0, 0.3, 4.6)
    bm.verts.ensure_lookup_table()
NAC_SHELL = cage_part("NacelleShell", nac_shell); NAC_SHELL.data.materials[0] = m_tower; par(NAC_SHELL, NAC)
# remove the -x side wall (cutaway window)
bm = bmesh.new(); bm.from_mesh(NAC_SHELL.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.x < -0.9], context="FACES"); bm.to_mesh(NAC_SHELL.data); bm.free()
try: NAC_SHELL.modifiers.new("thick", "SOLIDIFY").thickness = 0.12
except Exception: pass
GEAR = cyl("Gearbox", 1.3, 3.2, "Y", (0, 0.4, 2.3), m_gear, parent=NAC, seg=24)
GEN = cyl("Generator", 1.1, 2.6, "Y", (0, 4.8, 2.3), m_gen, parent=NAC, seg=24)
SHAFT = cyl("MainShaft", 0.45, 3.6, "Y", (0, -2.6, 2.4), m_flange, parent=NAC, seg=16)
YAWR = cyl("YawRing", 1.7, 0.3, "Z", (0, 0, 0.15), m_flange, parent=NAC, seg=32)
def nac_z(t):
    if t < T_HOLE0: return HUB_Z
    if t < T_NAC0: return 3.0
    u = (t - T_NAC0) / (T_NAC1 - T_NAC0)
    return 3.0 + (HUB_Z + 3.0 - 3.0) * ease(u / 0.8) - 3.0 * ease((u - 0.8) / 0.2)
def nac_xy(t):
    if t < T_HOLE0 or t >= T_NAC1: return 0.0, 0.0
    if t < T_NAC0: return 30.0, 12.0
    u = (t - T_NAC0) / (T_NAC1 - T_NAC0)
    a = Vector((30.0, 12.0)).lerp(Vector((0.0, 14.0)), ease(u / 0.5))
    return tuple(a.lerp(Vector((0.0, 0.0)), ease((u - 0.75) / 0.25)))
bake_loc(NAC, lambda t: (*nac_xy(t), nac_z(t)))
for o_ in [NAC_SHELL, GEAR, GEN, SHAFT, YAWR]:
    vis(o_, 1, False); vis(o_, F(T_HOLE0), True); vis(o_, F(C["now"]), False)
glow(b_gear, [(0, 0.0), (C["machine"], 0.0), (C["machine"] + 0.3, 2.0), (C["last"], 2.0), (C["last"] + 0.5, 0.0)])
glow(b_gen, [(0, 0.0), (C["machine"] + 0.2, 0.0), (C["machine"] + 0.5, 2.5), (C["last"], 2.5), (C["last"] + 0.5, 0.0)])

# ================= rotor: hub + 3 blades =================
def blade_mesh(name, link=True):
    bm = bmesh.new(); rings = []
    sections = [(0.0, 1.3, 1.3), (2.5, 1.35, 1.35), (6.0, 2.4, 0.9), (14.0, 2.6, 0.55), (30.0, 1.9, 0.35), (48.0, 1.2, 0.22), (BLADE, 0.25, 0.06)]
    for z, ch, th in sections:
        ring = []
        for k in range(16):
            a = 2 * math.pi * k / 16
            ring.append(bm.verts.new((0.5 * ch * math.cos(a), 0.5 * th * math.sin(a), z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(16): bm.faces.new([r0[k], r0[(k + 1) % 16], r1[(k + 1) % 16], r1[k]])
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o_ = mesh_obj(name, bm, m_blade, link=link)
    try: o_.data.shade_smooth()
    except Exception: pass
    return o_
def rotor(name):
    root = empty(name)
    spin = empty(name + "Spin"); par(spin, root)
    hub = lathe(name + "Hub", [(0, 0), (1.6, 0), (1.7, 1.2), (1.3, 3.0), (0.4, 4.2), (0, 4.4)], m_tower, ang=2 * math.pi, seg=32)
    hub.rotation_euler = (math.radians(90), 0, 0); hub.location = (0, 1.2, 0); par(hub, spin)
    bl = []
    for k in range(3):
        b_ = blade_mesh(f"{name}Blade{k}"); piv = empty(f"{name}BladePiv{k}"); par(piv, spin)
        piv.rotation_euler = (0, math.radians(120 * k), 0); par(b_, piv); b_.location = (0, 0, 1.4); bl.append(b_)
    return root, spin, hub, bl
ROT, ROT_SPIN, ROT_HUB, ROT_BL = rotor("Rotor")
def rot_state(t):
    """(hub location, tilt about x: 0 = upright facing -y, -90 deg = lying flat)."""
    if t < T_HOLE0 or t >= T_ROT1: return HUB, 0.0
    A, B = Vector((10.0, 75.0, 3.5)), Vector((0.0, 30.0, HUB.z))
    if t < T_ROT0: return A, -math.pi / 2
    u = (t - T_ROT0) / (T_ROT1 - T_ROT0)
    p = A.lerp(B, ease(u / 0.75)) if u < 0.75 else B.lerp(HUB, ease((u - 0.75) / 0.25))
    return p, -math.pi / 2 * (1 - ease((u - 0.45) / 0.45))
vals = [rot_state(t) for t in TS]
for ax in range(3): bake(ROT, "location", ax, [v[0][ax] for v in vals])
bake(ROT, "rotation_euler", 0, [v[1] for v in vals])
def spin_angle(t):
    w = 2 * math.pi * 13 / 60                    # ~13 rpm
    if t < T_HOLE0: return w * t
    if t < T_ROT1 + 0.2: return w * T_HOLE0
    return w * T_HOLE0 + w * 0.6 * (t - T_ROT1 - 0.2) ** 1.0 * ease((t - T_ROT1 - 0.2) / 1.0)
bake(ROT_SPIN, "rotation_euler", 1, [spin_angle(t) for t in TS])
for o_ in [ROT_HUB] + ROT_BL: windows(o_, [FIN, (T_ROT0, DUR)])
glow(b_blade, [(0, 0.0), (C["blades2"], 0.0), (C["blades2"] + 0.3, 1.2), (C["long"] + 0.4, 0.0)])
# single blade lift (one at a time) + the bare hub on the nacelle
HUB1 = lathe("HubOnly", [(0, 0), (1.6, 0), (1.7, 1.2), (1.3, 3.0), (0.4, 4.2), (0, 4.4)], m_tower, ang=2 * math.pi, seg=32)
HUB1.rotation_euler = (math.radians(90), 0, 0); HUB1.location = HUB + Vector((0, 1.2, 0))
windows(HUB1, [(T_NAC0, T_ROT0)])
bake_loc(HUB1, lambda t: tuple(HUB + Vector((0, 1.2, 0)) + Vector((*nac_xy(t), nac_z(t) - HUB_Z))))
BL1 = blade_mesh("BladeSingle")
def bl1_state(t):
    A, B = Vector((40.0, 20.0, 1.5)), HUB + Vector((1.4, 0, 0))
    if t < T_BL0: return A, 0.0
    return A.lerp(B, ease((t - T_BL0) / (T_BL1 - T_BL0) / 0.85)), 0.0
vals = [bl1_state(t) for t in TS]
for ax in range(3): bake(BL1, "location", ax, [v[0][ax] for v in vals])
BL1.rotation_euler = (0, math.radians(90), 0)       # blade along +x, root at the location
windows(BL1, [(T_BL0, T_ROT0)])

# ================= crawler crane (generic) =================
CR_BASE = Vector((-34.0, 22.0, 0.0)); TIP = Vector((-2.0, 6.0, 128.0))
def crane(bm):
    add_box(bm, CR_BASE.x - 6, CR_BASE.x + 6, CR_BASE.y - 5, CR_BASE.y - 3, 0, 1.6)          # tracks
    add_box(bm, CR_BASE.x - 6, CR_BASE.x + 6, CR_BASE.y + 3, CR_BASE.y + 5, 0, 1.6)
    add_box(bm, CR_BASE.x - 4, CR_BASE.x + 4, CR_BASE.y - 3, CR_BASE.y + 3, 1.6, 4.5, 0)    # body
    add_box(bm, CR_BASE.x - 9, CR_BASE.x - 4, CR_BASE.y - 2.5, CR_BASE.y + 2.5, 1.8, 5.5, 0) # counterweight
    b0 = CR_BASE + Vector((2, 0, 4.5)); d = (TIP - b0)
    side = Vector((-d.y, d.x, 0)).normalized() * 1.0
    up = d.cross(side).normalized() * 1.0
    chords = [side + up, side - up, -side + up, -side - up]
    for c_ in chords: add_bar(bm, b0 + c_, TIP + c_ * 0.4, 0.22)
    n = 40
    for k in range(n):
        s0, s1 = k / n, (k + 1) / n; sc0, sc1 = 1 - 0.6 * s0, 1 - 0.6 * s1
        p0, p1 = b0 + d * s0, b0 + d * s1
        add_bar(bm, p0 + chords[0] * sc0, p1 + chords[1] * sc1, 0.1); add_bar(bm, p0 + chords[2] * sc0, p1 + chords[3] * sc1, 0.1)
        add_bar(bm, p0 + chords[0] * sc0, p1 + chords[2] * sc1, 0.1); add_bar(bm, p0 + chords[1] * sc0, p1 + chords[3] * sc1, 0.1)
CRANE = cage_part("Crane", crane); CRANE.data.materials[0] = m_crane
windows(CRANE, [(T_SEC - 0.1, T_LOOP)])
HOOK = empty("HookTarget")
def hook_pos(t):
    if t < T_S4 + 0.5:
        i = 0 if t < T_S2 - 0.9 else (1 if t < T_S3 - 0.75 else (2 if t < T_S4 - 0.6 else 3))
        p, rot = sec_state(i, t); L = SEC_Z[i + 1] - SEC_Z[i]
        return p + Vector((0, -L * math.sin(rot) * 0.5, L * math.cos(rot)))
    if t < T_NAC1 + 0.4: return Vector((nac_xy(t)[0], nac_xy(t)[1] + 2.0, nac_z(t) + 4.8))
    if t < T_ROT0: s, _ = bl1_state(t); return s + Vector((BLADE * 0.3, 0, 2.0))
    p, _ = rot_state(t); return p + Vector((0, 0, 3.0))
bake_loc(HOOK, lambda t: tuple(hook_pos(t)))
cb = bmesh.new(); add_bar(cb, (0, 0, 0), (0, 1, 0), 0.12); CABLE = mesh_obj("CraneCable", cb, m_cable); CABLE.location = TIP
cs = CABLE.constraints.new("STRETCH_TO"); cs.target = HOOK; cs.rest_length = 1.0; cs.volume = "NO_VOLUME"; cs.keep_axis = "SWING_Y"
windows(CABLE, [(T_SEC + 0.3, C["average"]), (T_NAC0, T_ROT1 - 0.2)])

# ================= mixer truck + chute + optional Mantaflow pour =================
TRK = empty("Truck", (15.0, 4.5, 0))
box("TruckCab", 6.0, 8.5, -1.3, 1.3, 0.8, 3.6, m_truck, parent=TRK); box("TruckFrame", -4.5, 8.5, -1.2, 1.2, 0.6, 1.3, m_dark, parent=TRK)
DRUM = cyl("TruckDrum", 1.5, 6.0, "X", (0.5, 0, 3.0), m_drum, parent=TRK, seg=24)
for wx in (-3.5, -1.8, 6.8):
    for wy in (-1.2, 1.2): cyl(f"Wheel{wx}{wy}", 0.55, 0.45, "Y", (wx, wy, 0.55), m_dark, parent=TRK, seg=16)
cbm = bmesh.new(); add_bar(cbm, (-4.0, 0, 2.4), (-9.0, 0, 0.4), 0.6); CHUTE = mesh_obj("Chute", cbm, m_dark, parent=TRK)
TRK_PARTS = [TRK] + list(TRK.children_recursive)
windows(TRK, [(C["then"] - 0.3, T_FILL0)])
TRK.rotation_euler.z = math.radians(-20)
bake_loc(TRK, lambda t: (15.0 + 12.0 * (1 - ease((t - C["then"] + 0.3) / 0.9)), 4.5, 0))
sm = bmesh.new(); add_cyl(sm, 0.35, 1.0, "Z", (0, 0, -0.5), seg=12); STREAM = mesh_obj("PourStream", sm, m_wet)
STREAM.location = (6.6, 1.6, 0.6)
bake_scale(STREAM, lambda t: (1, 1, max(0.01, 0.6 - level_t(t)) if T_POUR0 + 0.2 <= t <= T_POUR1 else 0.01))
windows(STREAM, [(T_POUR0 + 0.2, T_POUR1)])
FLUID_BAKE = "--bake-fluid" in ARGS
FL_DOM = box("FluidDomain", 3.5, 8.0, -0.5, 4.0, Z_BOT - 0.2, 1.5, m_wet)
FL_IN = box("FluidInflow", 6.2, 7.0, 1.2, 2.0, 0.9, 1.2, m_wet); FL_IN.hide_render = True
fx.fluid_domain(FL_DOM, FL_IN, eff=[SLAB], res=64, start=F(T_POUR0 + 0.2), end=F(T_POUR0 + 3.8), cache_dir=os.path.join(HERE, "cache_fluid"))
windows(FL_DOM, [(T_POUR0 + 0.2, T_POUR0 + 3.8)] if FLUID_BAKE or os.path.isdir(os.path.join(HERE, "cache_fluid", "data")) else [])
glow(b_wet, [(0, 0.0), (C["five"], 0.0), (C["five"] + 0.2, 1.2), (C["yards"] + 0.4, 0.0)])

# ================= arrows, ghost, wind streaks, bars =================
def arrow_obj(name, base, direction, length, width, m_, y=0.0):
    bm = bmesh.new(); add_arrow(bm, base, direction, length, width, y=y); return mesh_obj(name, bm, m_)
PUSH = arrow_obj("WindPush", (-48.0, HUB.z + 2.0), (1, 0), 30.0, 9.0, m_red, y=-6.0)
bake_scale(PUSH, lambda t: (pop(t, C["shoves"]),) * 3)
windows(PUSH, [(C["shoves"], C["so"] - 0.2)])
glow(b_red, [(0, 3.0)] + pulse(C["tip"], 6.0, base=3.0, hold=1.0))
GPIV = empty("GhostPivot", (R_SLAB, 0, 0))
gh = bmesh.new(); add_cyl(gh, R_T0, HUB_Z, "Z", (-R_SLAB, 0, HUB_Z / 2), seg=24, r2=R_T1); add_box(gh, -R_SLAB - 2.1, -R_SLAB + 2.1, -3.6, 9.0, HUB_Z + 0.3, HUB_Z + 4.6)
for k in range(3):
    a = math.radians(120 * k + 20); d = Vector((math.sin(a), 0, math.cos(a)))
    add_bar(gh, Vector((-R_SLAB, -4.2, HUB.z)), Vector((-R_SLAB, -4.2, HUB.z)) + d * BLADE, 1.6)
add_box(gh, -2 * R_SLAB, 0, 0.1, R_SLAB, Z_BOT, Z_EDGE)
GHOST = mesh_obj("TipGhost", gh, red_ghost); par(GHOST, GPIV)
bake(GPIV, "rotation_euler", 1, [math.radians(6.0) * ease((t - C["tip"]) / (C["over"] + 0.3 - C["tip"])) for t in TS])
keyval(red_fac, [(0, 0.0), (C["tip"] - 0.1, 0.0), (C["tip"] + 0.2, 0.55), (C["so"] - 0.4, 0.55), (C["so"] - 0.1, 0.0), (C["wider"] - 0.1, 0.0), (C["wider"] + 0.2, 0.5), (C["tip2"] + 0.6, 0.5), (C["now"] - 0.1, 0.0)])
windows(GHOST, [(C["tip"] - 0.1, C["so"])])
# narrow-slab ghost for "a wider slab is harder to tip"
GPIV2 = empty("GhostPivot2", (4.0, 0, 0))
gh2 = bmesh.new(); add_box(gh2, -8.0, 0.0, 0.1, 4.0, Z_BOT, Z_EDGE); add_cyl(gh2, R_T0, 8.0, "Z", (-4.0, 0, 4.0), seg=16)
GHOST2 = mesh_obj("NarrowGhost", gh2, red_ghost); par(GHOST2, GPIV2); GHOST2.location = (0, 0, 0)
GPIV2.location = (4.0, 0.0, 0.0)
bake(GPIV2, "rotation_euler", 1, [math.radians(12.0) * ease((t - C["wider"] - 0.5) / 1.0) for t in TS])
windows(GHOST2, [(C["wider"] - 0.1, C["now"])])
GHOST.hide_render = False
# wind streaks
STREAKS = []
for k in range(10):
    sb = bmesh.new(); add_bar(sb, (0, 0, 0), (14.0 + 8 * random.random(), 0, 0), 0.35); o_ = mesh_obj(f"Wind{k}", sb, m_wind); STREAKS.append(o_)
    y0, z0, ph = -10.0 - 20 * random.random(), HUB.z - 50 + 100 * random.random(), random.random()
    bake_loc(o_, lambda t, y0=y0, z0=z0, ph=ph: (-120.0 + ((t * 70.0 + ph * 240.0) % 240.0), y0, z0))
    windows(o_, [(C["uptop"], C["so"] - 0.2)])
# gold down arrows (soil weight) + cyan width bar
DOWNS = [arrow_obj(f"Down{k}", (x, 3.2), (0, -1), 2.6, 1.6, m_gold, y=-0.3) for k, x in enumerate((-8.0, -5.2, 5.2, 8.0))]
for k, o_ in enumerate(DOWNS):
    windows(o_, [(C["pin"] - 0.3 + 0.08 * k, C["wider"] + 0.2)])
    bake_loc(o_, lambda t, k=k: (0, 0, -0.6 * (0.5 + 0.5 * math.sin(6.0 * t + k))))
WBAR = box("WidthBar", -R_SLAB, R_SLAB, -0.35, -0.2, Z_BOT - 0.55, Z_BOT - 0.35, m_cyan)
bake_scale(WBAR, lambda t: (max(0.001, ease((t - C["wider"]) / 0.5)), 1, 1)); windows(WBAR, [(C["wider"], C["now"])])
# hub height bar (cyan) beside the tower
HBAR = box("HeightBar", -6.6, -6.2, -3.0, -2.6, 0, HUB_Z, m_cyan)
bake_scale(HBAR, lambda t: (1, 1, max(0.001, ease((t - C["three"]) / 1.0)))); windows(HBAR, [(C["three"], C["next"])])
# blade length bar (gold) under the lifted blade
BLBAR = box("BladeBar", 0.0, BLADE, -0.25, 0.0, -3.0, -2.6, m_gold)
par(BLBAR, BL1); BLBAR.rotation_euler = (0, math.radians(-90), 0); BLBAR.location = (0, -1.5, 0)
windows(BLBAR, [(C["two"], C["some"])])
# sparks at the nuts when section 1 lands
emn = bmesh.new(); bmesh.ops.create_circle(emn, segments=24, radius=2.75, cap_ends=True); EM_NUT = mesh_obj("NutSparks", emn, m_bolt)
EM_NUT.location = (0, 0, Z_PED + 0.2)
fx.particles(EM_NUT, "sparks", F(C["tighten"]), F(C["nut"] + 0.4), count=220)

# ================= front ground with an open cutaway trench (so the section reads from the front) =================
def grass_top(o_, top_mi=0, side_mi=1):
    for p in o_.data.polygons: p.material_index = top_mi if (p.normal.z > 0.9 and p.center.z > -0.05) else side_mi
bmf = bmesh.new()
add_box(bmf, -4000, -60, -4000, 0, -14, 0); add_box(bmf, 60, 4000, -4000, 0, -14, 0); add_box(bmf, -60, 60, -4000, -40, -14, 0)
G_FRONT = mesh_obj("GroundFront", bmf, [m_grass, m_soil]); grass_top(G_FRONT)
TRENCH = box("TrenchFloor", -60, 60, -40, 0, -14, -6.0, m_soil2)
grass_top(G_OUT)

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
SC1 = box("ScatterNear", -70, 70, 14, 120, -0.06, -0.04, m_grass); grass_top(SC1, 0, 0)
SC2 = box("ScatterFront", -120, -62, -200, -2, -0.06, -0.04, m_grass); grass_top(SC2, 0, 0)
SC3 = box("ScatterFar", -1400, 1400, 700, 1600, -0.06, -0.04, m_grass); grass_top(SC3, 0, 0)
fx.scatter(SC1, ROCK, density=0.015, scale_min=1.0, scale_max=2.5, seed=3)
fx.scatter(SC2, TUFT, density=1.2, scale_min=0.7, scale_max=1.5, seed=5)
fx.scatter(SC3, FARM, density=0.000006, scale_min=0.9, scale_max=1.1, seed=8)
# keep the far turbines facing the camera roughly: GN random rotation is z-only; acceptable for a background

for e_ in (EM_DIG, EM_FILL, EM_NUT):
    e_.show_instancer_for_render = False; e_.show_instancer_for_viewport = False
# ================= lights + world =================
fx.hdri("sunrise", strength=0.6, rotation_deg=120.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    crw = wn.new("ShaderNodeValToRGB"); e = crw.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.95, 0.72, 0.50, 1); e[1].position = 0.35; e[1].color = (0.20, 0.42, 0.75, 1)
    wl.new(grad.outputs["Fac"], crw.inputs[0]); wl.new(crw.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.0; sun_d.color = (1.0, 0.86, 0.70); sun_d.angle = math.radians(2.0)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(62), 0, math.radians(-35))
def aimed_key(name, loc, target, energy, size=2.0):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = (1.0, 0.96, 0.9)
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tg = bpy.data.objects.new(name + "Tgt", None); scene.collection.objects.link(tg); tg.location = target
    c_ = o.constraints.new("TRACK_TO"); c_.target = tg; c_.track_axis = "TRACK_NEGATIVE_Z"; c_.up_axis = "UP_Y"
    return o, d
PIT_KEY, pit_kd = aimed_key("PitKey", (-8.0, -14.0, 9.0), (0.0, 3.0, -2.0), 9000.0, 8.0)
NAC_KEY, nac_kd = aimed_key("NacKey", (-12.0, -4.0, HUB_Z + 8.0), (0.0, 2.0, HUB_Z + 2.0), 6000.0, 4.0)
fx.glare(threshold=1.0, strength=0.5, size=7)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 6000
HOOK_SHOT = ((-11.0, -27.0, 5.5), (0.0, 0.0, 3.0), 22)
NZ = lambda d: (lambda t: nac_z(t) + d)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK_SHOT),
    (C["holds"], *HOOK_SHOT),
    (C["up"] + 0.4, (-17.0, -36.0, 3.0), (0.0, 0.0, 70.0), 22),
    (C["uptop"] - 0.05, (-17.0, -36.0, 3.2), (0.0, 0.0, 72.0), 22),
    (C["uptop"], (-60.0, -175.0, 35.0), (0.0, 0.0, 82.0), 28, "cut"),
    (C["so"] - 0.05, (-55.0, -165.0, 35.0), (0.0, 0.0, 82.0), 28),
    (C["so"], (-17.0, -32.0, 11.0), (0.0, 3.0, -1.5), 24, "cut"),
    (C["workers"] - 0.05, (-16.0, -30.0, 10.0), (0.0, 3.0, -1.8), 24),
    (C["workers"], (-9.5, -18.0, 4.5), (0.0, 3.0, -2.4), 24, "cut"),
    (C["middle"] - 0.05, (-8.5, -16.5, 4.0), (0.0, 3.0, -2.4), 24),
    (C["middle"], (-5.0, -10.0, 2.4), (0.0, 2.2, -0.9), 26, "cut"),
    (C["then"] - 0.05, (-4.4, -9.4, 2.2), (0.0, 2.2, -0.9), 26),
    (C["then"], (-12.0, -24.0, 6.5), (2.5, 3.0, -1.6), 24, "cut"),
    (C["once"] - 0.05, (-11.0, -23.0, 6.0), (2.0, 3.0, -1.6), 24),
    (C["once"], (-15.0, -27.0, 7.5), (0.0, 3.0, -1.4), 24, "cut"),
    (C["wider"] - 0.05, (-15.5, -28.5, 6.0), (0.0, 2.0, -1.6), 24),
    (C["wider"] + 0.5, (-14.0, -36.0, 3.0), (0.0, 0.0, 1.0), 22),
    (C["now"] - 0.05, (-14.0, -37.0, 3.0), (0.0, 0.0, 1.0), 22),
    (C["now"], (-12.0, -34.0, 9.0), (30.0, 26.0, 2.0), 26, "cut"),
    (C["crane"] - 0.05, (-10.0, -32.0, 9.5), (30.0, 26.0, 2.5), 26),
    (C["crane"], (-55.0, -85.0, 22.0), (2.0, 4.0, 13.0), 26, "cut"),
    (C["tighten"] - 0.05, (-52.0, -82.0, 20.0), (0.0, 2.0, 10.0), 26),
    (C["tighten"], (-8.0, -13.0, 4.5), (0.0, 0.0, 1.2), 28, "cut"),
    (C["each"] - 0.05, (-7.5, -12.5, 4.5), (0.0, 0.0, 1.4), 28),
    (C["each"], (-75.0, -130.0, 35.0), (0.0, 0.0, 48.0), 26, "cut"),
    (C["stacked"] - 0.05, (-72.0, -126.0, 38.0), (0.0, 0.0, 50.0), 26),
    (C["stacked"], (-40.0, -82.0, 18.0), (0.0, 0.0, 24.0), 26, "cut"),
    (C["air"] + 0.4, (-40.0, -82.0, 98.0), (0.0, 0.0, 98.0), 26),
    (C["next"] - 0.05, (-40.0, -82.0, 99.0), (0.0, 0.0, 99.0), 26),
    (C["next"], (-38.0, -70.0, NZ(6.0)), (8.0, 4.0, NZ(2.0)), 26, "cut"),
    (C["machine"] - 0.05, (-38.0, -70.0, NZ(6.0)), (8.0, 4.0, NZ(2.0)), 26),
    (C["machine"], (-15.0, -7.0, NZ(4.5)), (0.0, 2.2, NZ(2.3)), 28, "cut"),
    (C["last"] - 0.05, (-14.0, -7.5, NZ(4.6)), (0.0, 2.2, NZ(2.3)), 28),
    (C["last"], (-12.0, -115.0, 28.0), (38.0, 10.0, 58.0), 26, "cut"),
    (C["others"] - 0.05, (-15.0, -120.0, 85.0), (30.0, 5.0, 95.0), 26),
    (C["others"], (-80.0, -185.0, 40.0), (0.0, 40.0, 50.0), 26, "cut"),
    (C["and"] - 0.05, (-90.0, -210.0, 55.0), (0.0, 10.0, 70.0), 26),
    (C["and"], (-35.0, -95.0, 95.0), (0.0, 0.0, 92.0), 26, "cut"),
    (WORDS[218]["end"] + VO, *HOOK_SHOT),
    (DUR - 0.25, *HOOK_SHOT),
    (DUR, *HOOK_SHOT),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.03 * math.sin(t * 0.7), 0.0, 0.02 * math.sin(t * 0.9 + 1.0))))
    cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 20; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(30.0, min(4000.0, 250.0 * ((cl - ct).length / 30.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
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
fx.bake_rigid(RB_FRAME0, F(T_FILL1 + 0.3))
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
P = lambda *v: (lambda t: Vector(v))
ANCHP = {
    "slab": P(-6.0, 0.0, -3.0), "dirt": P(-8.0, 0.0, -0.6), "hub": lambda t: ROT.matrix_world.translation.copy(),
    "rebar": P(-6.5, 1.0, Z_BOT + 0.2), "bolts": lambda t: Vector((-2.8, 0.3, BOLTS.location.z + Z_PED + 0.4)),
    "concrete": lambda t: Vector((-5.0, 0.0, min(level_t(t), Z_PED) - 0.4)), "truck": lambda t: TRK.matrix_world.translation + Vector((0, 0, 4.5)),
    "backfill": P(-7.0, 0.0, -1.2), "width": P(0.0, -0.3, Z_BOT - 0.45),
    "sections": P(32.0, 30.0, 6.0), "crane": P(-34.0, 22.0, 8.0), "flange": P(-2.4, 0.0, Z_PED + 0.6),
    "flange2": P(-r_tower(SEC_Z[1]) - 0.2, 0.0, SEC_Z[1]), "hubheight": P(-6.4, -2.8, HUB_Z),
    "nacelle": lambda t: Vector((nac_xy(t)[0] - 2.2, nac_xy(t)[1] + 2.0, nac_z(t) + 4.8)), "gearbox": lambda t: Vector((nac_xy(t)[0] - 1.3, nac_xy(t)[1] + 0.4, nac_z(t) + 2.3)),
    "generator": lambda t: Vector((nac_xy(t)[0] - 1.1, nac_xy(t)[1] + 4.8, nac_z(t) + 2.3)),
    "blade": lambda t: BL1.matrix_world.translation + Vector((BLADE * 0.5, 0, 1.5)), "rotor": lambda t: ROT.matrix_world.translation + Vector((0, 0, 6.0)),
}
anchors = {k: [] for k in ANCHP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook_glow": round(C["buried"], 3), "dirt_glow": round(C["pile"], 3), "push": round(C["shoves"], 3), "tip": RR(C["tip"], C["over"] + 0.3),
          "cut_bare": round(T_HOLE0, 3), "dig": RR(T_DIG0, T_DIG1), "cage": [round(T_MAT1 + 0.45, 3), round(T_MAT2 + 0.45, 3), round(T_MAT3 + 0.45, 3)],
          "bolts": RR(T_BOLT0, T_BOLT1), "truck": round(C["then"] - 0.3, 3), "pour": RR(T_POUR0, T_POUR1), "fill": RR(T_FILL0, T_FILL1),
          "arrows": round(C["pin"] - 0.3, 3), "width": round(C["wider"], 3), "narrow_tip": RR(C["wider"] + 0.5, C["wider"] + 1.5),
          "sections": round(T_SEC - 0.1, 3), "s1": RR(T_S1A, T_S1B), "nuts": RR(C["tighten"], C["nut"] + 0.4),
          "stack": [round(T_S2 + 0.25, 3), round(T_S3 + 0.3, 3), round(T_S4 + 0.45, 3)], "heightbar": round(C["three"], 3),
          "nacelle": RR(T_NAC0, T_NAC1), "nac_glow": round(C["machine"] + 0.3, 3), "blade": RR(T_BL0, T_BL1),
          "rotor": RR(T_ROT0, T_ROT1), "spin": round(T_ROT1 + 0.2, 3), "loop": round(T_LOOP, 3)}
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
    if "--range" in ARGS: scene.frame_start, scene.frame_end = [int(x) for x in arg("--range").split(",")]  # partial re-render
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
