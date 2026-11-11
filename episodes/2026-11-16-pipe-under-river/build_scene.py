# Pipe-Under-River-3D: how a pipe gets under a river with no digging (horizontal directional drilling). Build-up format ("THIS IS A GARDEN HOSE"):
# trench (tears up the riverbed, mud downstream) -> rig on the bank pushes a steel rod in at an angle -> straight it would keep going down ->
# slanted bit: spin = straight, push without spinning = it turns -> transmitter tells the crew where it is -> pilot bore under the river, out on
# the far bank -> reamer pulled back to widen it (two passes) -> walls cave -> drilling mud (water + clay) holds the walls, carries cuttings out ->
# push too hard = mud bubbles up into the river (inadvertent return) -> pipe welded into one string on the far bank -> pulled back in one piece ->
# boats never notice -> CTA: other pipes under the river light up.
# Blender Cycles, real-world set cut at y = 0 along the bore (soil layers, river channel, water), camera on -y. Illustrative scale (1 unit = 1 m):
# crossing 110 m, 12 m deep, entry/exit angle ~24 deg (real crossings are usually shallower, ~8-20 deg), rod, bit, reamer and pipe drawn
# thicker than real so they read on a phone; holes are painted on the cut face (flattened tubes). Demo set for the bit at x = 400.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
import bpy, bmesh, json, math, os, random, sys

from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 0.85, 2)
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

CUES = [("if", "If"), ("pipe", "pipe"), ("river", "river,"), ("dig", "dig"), ("drill", "drill"), ("under", "under"), ("steer", "steer"), ("way", "way."), ("dig2", "Dig"), ("trench", "trench"), ("tear", "tear"), ("riverbed", "riverbed"), ("mud1", "mud"), ("downstream", "downstream."), ("lets", "Let's"), ("this", "This"), ("garden", "garden"), ("hose", "hose."), ("now", "Now"), ("gas", "gas"), ("main", "main"), ("river2", "river."), ("so", "So"), ("rig", "rig"), ("bank0", "bank"), ("pushes", "pushes"), ("rod", "rod"), ("ground", "ground"), ("angle", "angle."), ("straight", "Straight,"), ("down", "down."), ("so2", "So"), ("tip", "tip"), ("slanted", "slanted"), ("face", "face."), ("spin", "Spin"), ("drills", "drills"), ("straight2", "straight."), ("stop", "Stop"), ("push", "push,"), ("slant", "slant"), ("bends", "bends"), ("a", "A"), ("transmitter", "transmitter"), ("tells", "tells"), ("crew", "crew"), ("where", "where"), ("the", "The"), ("rod2", "rod"), ("dives", "dives"), ("under2", "under"), ("riverbed2", "riverbed,"), ("climbs", "climbs"), ("far", "far"), ("bank", "bank."), ("but", "But"), ("hole", "hole"), ("barely", "barely"), ("rod3", "rod."), ("so3", "So"), ("spinning", "spinning"), ("reamer", "reamer"), ("pulled", "pulled"), ("widen", "widen"), ("sometimes", "sometimes"), ("once", "once."), ("now2", "Now"), ("walls", "walls"), ("cave", "cave"), ("so4", "So"), ("pump", "pump"), ("drilling", "drilling"), ("mud", "mud,"), ("water", "water"), ("clay", "clay."), ("it", "It"), ("holds", "holds"), ("walls2", "walls"), ("carries", "carries"), ("cuttings", "cuttings"), ("push2", "Push"), ("hard", "hard,"), ("bubbles", "bubbles"), ("river3", "river."), ("on", "On"), ("far2", "far"), ("pipe2", "pipe"), ("welded", "welded"), ("string", "string,"), ("then", "then"), ("pulled2", "pulled"), ("single", "single"), ("piece", "piece."), ("the2", "The"), ("boats", "boats"), ("never", "never"), ("how", "How"), ("many", "many"), ("pipes", "pipes"), ("closest", "closest"), ("tell", "Tell"), ("next", "Next"), ("lightning", "lightning"), ("follow", "Follow")]

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
CL = coll("PipeUnderRiver")
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

def ground(name, rgb1, rgb2, scale=0.05):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    g = N.new("ShaderNodeNewGeometry"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 10
    L.new(g.outputs["Position"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].color = (*rgb1, 1); e[1].color = (*rgb2, 1)
    L.new(n.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
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
def surf_mat(name, rgb=(0.02, 0.12, 0.20)):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.14
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.35
    n.inputs["Detail"].default_value = 8; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m, b
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

def wire_face(name, rgb=(0.62, 0.64, 0.66), scale=14.0):
    """Cut face of a strand: Voronoi cells = the ends of the parallel wires (bright round wire ends, dark gaps)."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale
    try: vo.inputs["Randomness"].default_value = 0.15
    except Exception: pass
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    try: vo.feature = "DISTANCE_TO_EDGE"
    except Exception: pass
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.02; mr.inputs[2].default_value = 0.10
    L.new(vo.outputs["Distance"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], (0.03, 0.03, 0.035), rgb)
    L.new(col, b.inputs["Base Color"]); b.inputs["Metallic"].default_value = 0.85; b.inputs["Roughness"].default_value = 0.32
    b.inputs["Emission Color"].default_value = (0.30, 0.92, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b

def stripes(name, rgb=(0.62, 0.64, 0.66), scale=1.6):
    """Long cut face of the main cable: thin bright bands along x = the parallel wires, dark gaps between them."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 0.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.25; mr.inputs[2].default_value = 0.55
    L.new(wv.outputs["Fac"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], (0.03, 0.03, 0.035), rgb)
    L.new(col, b.inputs["Base Color"]); b.inputs["Metallic"].default_value = 0.85; b.inputs["Roughness"].default_value = 0.32
    b.inputs["Emission Color"].default_value = (0.30, 0.92, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b




def soil_mat(name, rgb1, rgb2, scale=1.2, wet=False):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    g = N.new("ShaderNodeNewGeometry"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 8
    L.new(g.outputs["Position"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].color = (*rgb1, 1); e[1].color = (*rgb2, 1)
    L.new(n.outputs["Fac"], cr.inputs[0]); col = cr.outputs[0]
    vo = N.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = scale * 6; L.new(g.outputs["Position"], vo.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.05; mr.inputs[2].default_value = 0.18; L.new(vo.outputs["Distance"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], tuple(c * 0.55 for c in rgb1), col)          # pebbles / grains
    if wet:   # below the water table the aquifer is saturated: blue-tinted
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], sep.inputs[0])
        lt = N.new("ShaderNodeMapRange"); lt.inputs[1].default_value = WT + 0.3; lt.inputs[2].default_value = WT - 0.3
        L.new(sep.outputs["Z"], lt.inputs[0])
        wetc = mix_rgb(nt, mr.outputs[0], (0.02, 0.08, 0.15), (0.07, 0.22, 0.32))
        col = mix_rgb(nt, lt.outputs[0], col, wetc)
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


# ================= the crossing: path, lengths, timing =================
WT = -999.0                                                                     # no water table tint in this set
H, DEP = 55.0, 12.0                                                             # entry x = -55, exit x = +55, 12 m deep at the centre
def zp(x): return -DEP * (1 - (x / H) ** 2)
PX = [-H + i * 0.5 for i in range(int(2 * H / 0.5) + 1)]
PP = [Vector((x, 0.0, zp(x))) for x in PX]
def cum(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + (b - a).length)
    return s
SP = cum(PP); L = SP[-1]
def at(pts, sl, s):
    """point + tangent angle (radians, in XZ) at arc length s."""
    s = max(0.0, min(sl[-1], s))
    lo, hi = 0, len(sl) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if sl[mid] <= s: lo = mid
        else: hi = mid
    u = (s - sl[lo]) / max(1e-9, sl[hi] - sl[lo]); p = pts[lo].lerp(pts[hi], u); d = pts[hi] - pts[lo]
    return p, math.atan2(d.z, d.x)
def x2s(x):
    for i in range(len(PX) - 1):
        if PX[i + 1] >= x: return SP[i] + (SP[i + 1] - SP[i]) * (x - PX[i]) / (PX[i + 1] - PX[i])
    return L
ANG = math.atan(2 * DEP / H)                                                    # entry/exit angle (~23.6 deg, steeper than real for the frame)
U = Vector((-math.cos(ANG), 0, math.sin(ANG)))                                  # up the rig's rack from the entry point
PRE = [Vector((-H, 0, 0)) + U * (10.0 - 0.5 * k) for k in range(20)]            # rod above ground, in the rig
ROD_P = PRE + PP; SROD = cum(ROD_P); LPRE = SROD[len(PRE)]
EXIT_D = Vector((math.cos(ANG), 0, math.sin(ANG)))
TAIL0 = Vector((H, 0, 0)) + EXIT_D * (0.8 / math.sin(ANG))                      # the pipe string rests on rollers 0.8 m up
LP = L + 2.0
TAIL = [TAIL0 + Vector((1.0 * k, 0, 0)) for k in range(int(LP + 6))]
PIPE_P = PP + TAIL; SPIPE = cum(PIPE_P); LT = SPIPE[-1]

T_TR, T_LB, T_HOSE, T_GAS, T_RIG = C["dig2"], C["lets"], C["this"], C["now"], C["so"]
T_STR, T_SLANT, T_SPIN, T_STOP, T_PUSH, T_TX = C["straight"], C["so2"], C["spin"], C["stop"], C["push"], C["a"]
T_DIVE, T_BUT, T_REAM, T_CAVE0, T_MUD, T_HOLD, T_FRAC, T_WELD, T_PULL, T_BOAT, T_CTA = (
    C["the"], C["but"], C["so3"], C["now2"], C["so4"], C["it"], C["push2"], C["on"], C["then"], C["the2"], C["how"])
R0, R1 = C["pulled"], C["sometimes"] - 0.1                                      # first reaming pass
R2, R3 = C["sometimes"] + 0.05, C["now2"] - 0.1                                 # second pass (bigger)
P0, P1 = C["pulled2"], C["piece"] + 0.3                                         # pullback

def sh(t):
    """arc length of the drill head along the bore."""
    if t < T_TR: return x2s(-16.0 + 24.0 * lin(t / T_TR))
    if t < C["pushes"]: return 0.0
    if t < T_STR: return x2s(-55.0 + 5.0 * ease((t - C["pushes"]) / (T_STR - 0.3 - C["pushes"])))
    if t < C["transmitter"]: return x2s(-50.0)
    if t < T_DIVE: return x2s(-50.0 + 20.0 * ease((t - C["transmitter"]) / (T_DIVE - C["transmitter"])))
    return x2s(-30.0) + (L - x2s(-30.0)) * ease((t - T_DIVE) / (C["bank"] + 0.3 - T_DIVE))
def sr(t):
    """reamer position (arc length) during the two passes."""
    if t < R0: return L
    if t < R1: return L * (1 - ease((t - R0) / (R1 - R0)))
    if t < R2: return 0.0
    if t < R3: return L * (1 - ease((t - R2) / (R3 - R2)))
    return 0.0
def spull(t):
    if t < P0: return L
    return L * (1 - ease((t - P0) / (P1 - P0)))
def rod_end(t):
    if t < T_REAM: return sh(t)
    if t < T_CAVE0: return L if t < R0 else (sr(t) if t < R1 or t >= R2 else L)
    if t < P0: return L
    return spull(t)
def reamer_s(t):
    if t < R0: return L
    if t < R1: return sr(t)
    if t < R2: return L
    if t < R3: return sr(t)
    return spull(t) if t >= T_WELD else L

# ================= materials =================
M_TOP = soil_mat("Topsoil", (0.10, 0.06, 0.035), (0.16, 0.10, 0.06), 2.0)
M_CLAY = soil_mat("Clay", (0.34, 0.17, 0.08), (0.46, 0.25, 0.12), 0.8)
M_SAND = soil_mat("Sand", (0.33, 0.25, 0.13), (0.45, 0.35, 0.19), 1.6)
M_ROCK = soil_mat("Bedrock", (0.20, 0.20, 0.21), (0.34, 0.33, 0.33), 0.5)
M_GRASS = ground("Grass", (0.10, 0.22, 0.05), (0.20, 0.36, 0.08), 0.6)
M_HOLE, B_HOLE = mat("Hole", (0.025, 0.018, 0.012), 0.9, emit_rgb=(1.0, 0.30, 0.24))
M_HOLE2, B_HOLE2 = mat("HoleReamed", (0.035, 0.026, 0.018), 0.9, emit_rgb=(1.0, 0.30, 0.24))
M_MUD, B_MUD = mat("DrillingMud", (0.30, 0.31, 0.33), 0.25, emit_rgb=(0.98, 0.74, 0.27))
M_ROD, B_ROD = mat("Rod", (0.55, 0.57, 0.60), 0.3, 0.9, emit_rgb=(0.30, 0.92, 1.0))
M_BIT, B_BIT = mat("Bit", (0.70, 0.60, 0.40), 0.25, 1.0, emit_rgb=(0.98, 0.74, 0.27))
M_SONDE, B_SONDE = mat("Sonde", (0.20, 0.22, 0.25), 0.3, 0.8, emit_rgb=(0.30, 0.92, 1.0))
M_REAM, B_REAM = mat("Reamer", (0.60, 0.50, 0.30), 0.3, 1.0, emit_rgb=(0.98, 0.74, 0.27))
M_PIPEY, B_PIPEY = mat("GasPipe", (0.85, 0.62, 0.06), 0.35, emit_rgb=(0.98, 0.74, 0.27))
M_RIG, _ = mat("RigYellow", (0.75, 0.55, 0.05), 0.4, 0.3)
M_STEEL, _ = mat("Steel", (0.30, 0.31, 0.33), 0.35, 0.9)
M_DARK, _ = mat("DarkSteel", (0.05, 0.05, 0.055), 0.5, 0.5)
M_WIN, B_WIN = mat("Screen", (0.03, 0.05, 0.07), 0.1, emit_rgb=(0.30, 0.92, 1.0))
M_HOSE, _ = mat("Hose", (0.06, 0.35, 0.08), 0.35)
M_BRASS, _ = mat("Brass", (0.75, 0.55, 0.25), 0.3, 1.0)
M_HULL, _ = mat("Hull", (0.85, 0.86, 0.88), 0.4)
M_HULLR, _ = mat("HullRed", (0.55, 0.08, 0.06), 0.5)
M_BARK, _ = mat("Bark", (0.18, 0.11, 0.06), 0.9)
M_LEAF, _ = mat("Leaf", (0.07, 0.20, 0.05), 0.8, noise=4.0)
M_SPOIL, B_SPOIL = mat("Spoil", (0.22, 0.12, 0.06), 0.9, emit_rgb=(1.0, 0.30, 0.24))
M_CLOUD, B_CLOUD = mat("MudCloud", (0.30, 0.18, 0.08), 0.9, emit_rgb=(0.45, 0.25, 0.10)); B_CLOUD.inputs["Emission Strength"].default_value = 0.6
M_REDL, B_REDL = mat("RedLine", (1.0, 0.30, 0.24), 0.4, emit_rgb=(1.0, 0.30, 0.24)); B_REDL.inputs["Emission Strength"].default_value = 3.0
M_CYAN, B_CYAN = mat("CyanGlow", (0.30, 0.92, 1.0), 0.3, emit_rgb=(0.30, 0.92, 1.0)); B_CYAN.inputs["Emission Strength"].default_value = 4.0
M_GOLD, B_GOLD = mat("GoldGlow", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27)); B_GOLD.inputs["Emission Strength"].default_value = 3.0
M_WHITEG, B_WHITEG = mat("WhiteGlow", (0.9, 0.95, 1.0), 0.4, emit_rgb=(0.9, 0.95, 1.0)); B_WHITEG.inputs["Emission Strength"].default_value = 2.5
M_MUDD, B_MUDD = mat("MudDot", (0.80, 0.68, 0.48), 0.4, emit_rgb=(0.95, 0.80, 0.55)); B_MUDD.inputs["Emission Strength"].default_value = 1.2
M_CUT, _ = mat("Cuttings", (0.16, 0.09, 0.04), 0.8)
M_WATER, B_WATER, VA_WATER = water_sec("RiverWater", dens=0.06)
M_SURF, _ = surf_mat("RiverSurface", (0.05, 0.20, 0.28))
M_GHOST, A_GHOST = ghost("GhostPipe", (0.98, 0.74, 0.27))

# ================= ground: layers cut at y = 0, river channel boolean =================
def prism(name, poly, y0, y1, m_):
    bm = bmesh.new(); vs = [bm.verts.new((x, y0, z)) for x, z in poly]; f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f]); nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0, y1 - y0, 0)); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_)
CHAN = prism("ChannelCutter", [(-25.6, 1.5), (-12.0, -6.0), (12.0, -6.0), (25.6, 1.5)], -1.0, 700.0, None)
CHAN.hide_render = True; CHAN.display_type = "WIRE"
def layer(name, z0, z1, m_):
    o = box(name, -300.0, 380.0, 0.0, 600.0, z0, z1, m_)
    md = o.modifiers.new("river", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = CHAN
    try: md.solver = "EXACT"
    except Exception: pass
    return o
layer("GrassL", -0.02, 0.10, M_GRASS); layer("TopsoilL", -1.5, -0.02, M_TOP); layer("ClayL", -9.0, -1.5, M_CLAY)
box("SandL", -300.0, 380.0, 0.0, 600.0, -20.0, -9.0, M_SAND); box("RockL", -300.0, 380.0, 0.0, 600.0, -160.0, -20.0, M_ROCK)
box("FarGrass", -900, 900, 600.0, 1500, -2.0, 0.10, M_GRASS)
box("SideGrassL", -900, -300.0, 0.0, 600.0, -2.0, 0.10, M_GRASS); box("SideGrassR", 380.0, 900, 0.0, 600.0, -2.0, 0.10, M_GRASS)
WX = 12.0 + 12.0 * (5.4 / 7.5)
WATER = prism("River", [(-WX + 0.02, -0.6), (-11.98, -5.98), (11.98, -5.98), (WX - 0.02, -0.6)], 0.0, 10.0, M_WATER)
M_WBACK, B_WBACK = mat("WaterBack", (0.04, 0.20, 0.30), 0.3, emit_rgb=(0.05, 0.28, 0.42)); B_WBACK.inputs["Emission Strength"].default_value = 0.6
prism("RiverBack", [(-WX, -0.55), (-11.9, -6.05), (11.9, -6.05), (WX, -0.55)], 10.0, 10.2, M_WBACK)
box("RiverSurface", -WX, WX, 0.08, 600.0, -0.62, -0.60, M_SURF)
box("RiverFar", -WX, WX, 600.0, 1500.0, -0.62, -0.60, M_SURF)
# water turns muddy in the trench beat, a little again at the frac-out
CLEAR, MUDDY = (0.16, 0.46, 0.62, 1), (0.55, 0.32, 0.12, 1)
keyval(VA_WATER.inputs["Color"], [(0, CLEAR), (C["tear"] - 0.05, CLEAR), (C["downstream"], MUDDY), (T_LB - 0.05, MUDDY), (T_LB, CLEAR)])
# trees along both banks
random.seed(5)
for k in range(26):
    side = -1 if k % 2 else 1
    x = side * random.uniform(28.0, 95.0); y = random.uniform(14.0, 160.0); h = random.uniform(5.0, 9.0)
    cyl(f"Trunk{k}", 0.25, h * 0.45, "Z", (x, y, h * 0.22), M_BARK, seg=8)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=h * 0.32)
    for vv in bm.verts: vv.co.z *= 1.3; vv.co *= random.uniform(0.9, 1.1)
    mesh_obj(f"Crown{k}", bm, M_LEAF).location = (x, y, h * 0.62)

# ================= curves (rod, pipe, holes painted on the cut face) =================
def curve(name, pts, r, m_, flat=False, res=4):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (p.x, p.y, p.z, 1.0)
    cu.bevel_depth = r; cu.bevel_resolution = res; cu.use_fill_caps = True
    cu.bevel_factor_mapping_start = "SPLINE"; cu.bevel_factor_mapping_end = "SPLINE"
    o = bpy.data.objects.new(name, cu); CL.objects.link(o); cu.materials.append(m_)
    if flat: o.scale = (1.0, 0.02, 1.0); o.location = (0.0, -0.035, 0.0)       # flattened tube = a band painted on the cut face
    return o, cu
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
def reveal(cu, f0, f1):
    bake_scalar(cu, "bevel_factor_start", [max(0.0, min(0.999, f0(t))) for t in TS])
    bake_scalar(cu, "bevel_factor_end", [max(0.001, min(1.0, f1(t))) for t in TS])
HP, HPC = curve("HolePilot", PP, 0.40, M_HOLE, flat=True)
reveal(HPC, lambda t: 0.0, lambda t: sh(t) / L)
windows(HP, [(0, T_TR), (C["pushes"], DUR)])
HR1, HR1C = curve("HoleReam1", PP, 0.62, M_HOLE2, flat=True); HR1.location.y = -0.04
reveal(HR1C, lambda t: sr(t) / L if t < R1 else 0.0, lambda t: 1.0); windows(HR1, [(R0, DUR)])
HR2, HR2C = curve("HoleReam2", PP, 0.92, M_HOLE2, flat=True); HR2.location.y = -0.045
reveal(HR2C, lambda t: sr(t) / L if R2 <= t < R3 else (1.0 if t < R2 else 0.0), lambda t: 1.0); windows(HR2, [(R2, DUR)])
MUDB, MUDC = curve("MudFill", PP, 0.92, M_MUD, flat=True); MUDB.location.y = -0.05
reveal(MUDC, lambda t: 0.0, lambda t: ease((t - C["drilling"]) / 1.4)); windows(MUDB, [(C["drilling"], P0 + 0.5)])
glow(B_MUD, [(0, 0)] + pulse(C["mud"], 0.35, up=0.3, hold=0.8) + pulse(C["holds"], 0.3, up=0.2, hold=0.8))
glow(B_HOLE2, [(0, 0)] + pulse(T_CAVE0 + 0.9, 1.2, up=0.15, hold=0.5))
ROD, RODC = curve("Rod", ROD_P, 0.13, M_ROD, res=3)
reveal(RODC, lambda t: 0.0, lambda t: (LPRE + rod_end(t)) / SROD[-1])
windows(ROD, [(0, T_TR), (T_LB, P1 + 0.1)])
glow(B_ROD, [(0, 0)] + pulse(C["rod"], 1.0, up=0.2, hold=0.5) + pulse(C["barely"], 1.0, up=0.2, hold=0.6))
PIPE, PIPEC = curve("GasMain", PIPE_P, 0.60, M_PIPEY, res=4)
reveal(PIPEC, lambda t: (spull(t) + 1.0) / LT, lambda t: (spull(t) + 1.0 + LP) / LT)
windows(PIPE, [(T_WELD - 0.1, DUR)])
glow(B_PIPEY, [(0, 0)] + pulse(C["single"], 0.8, up=0.3, hold=0.8) + [(T_BOAT, 0.0), (T_BOAT + 0.5, 0.6), (T_CTA, 0.6), (T_CTA + 0.6, 0.3)])
GH, GHC = curve("GhostPipe", PP, 0.60, M_GHOST)
windows(GH, [(C["gas"] - 0.05, T_RIG), (C["barely"] - 0.1, T_REAM)])
keyval(A_GHOST, [(0, 0.0), (C["gas"] - 0.05, 0.0), (C["gas"] + 0.3, 0.8), (T_RIG - 0.1, 0.8), (C["barely"] - 0.1, 0.0), (C["barely"] + 0.2, 0.8)])
ROUTE, ROUTEC = curve("Route", PP, 0.07, M_CYAN, res=2); ROUTE.location.y = -0.7
reveal(ROUTEC, lambda t: 0.0, lambda t: ease((t - C["steer"]) / 1.0)); windows(ROUTE, [(C["steer"], T_TR)])
STR, STRC = curve("StraightLine", [Vector((-H, 0, 0)) - U * 0.5 * k for k in range(70)], 0.10, M_REDL, res=2); STR.location.y = -0.6
reveal(STRC, lambda t: 0.0, lambda t: ease((t - T_STR) / 1.3)); windows(STR, [(T_STR, T_SLANT)])

# ================= drill head: slanted bit + transmitter housing, spinning =================
def bit_mesh(name, m_bit, m_sonde, parent):
    bm = bmesh.new(); add_cyl(bm, 0.24, 0.9, "X", (0.15, 0, 0), 24)
    n = Vector((0.55, 0, 0.83)).normalized()
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0.35, 0, 0), plane_no=n, clear_outer=True)
    oe = [e for e in bm.edges if len(e.link_faces) < 2]
    if oe: bmesh.ops.edgeloop_fill(bm, edges=oe)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    b = mesh_obj(name + "Bit", bm, m_bit, parent)
    s = cyl(name + "Sonde", 0.21, 1.3, "X", (-0.95, 0, 0), m_sonde, parent, seg=24)
    return b, s
HEADP = empty("HeadPivot")
HSPIN = empty("HeadSpin", parent=HEADP)
HBIT, HSON = bit_mesh("Head", M_BIT, M_SONDE, HSPIN)
def head_pose(t):
    p, a = at(PP, SP, sh(t)); return p, a
hp = [head_pose(t) for t in TS]
bake(HEADP, "location", 0, [p.x for p, a in hp]); bake(HEADP, "location", 1, [-0.0 for p, a in hp]); bake(HEADP, "location", 2, [p.z for p, a in hp])
bake(HEADP, "rotation_euler", 1, [-a for p, a in hp])
bake_fn(HSPIN, "rotation_euler", 0, lambda t: t * 9.0)
windows(HEADP, [(0, T_TR), (T_RIG, T_SLANT), (T_TX, T_BUT)])
glow(B_SONDE, [(0, 0)] + pulse(C["transmitter"], 2.5, up=0.2, hold=2.4, down=0.4))

# ================= the rig on the near bank =================
RIG = empty("Rig")
k0, k1 = 1.6, 12.0
bm = bmesh.new(); add_bar(bm, Vector((-H, 0, 0)) + U * k0 + Vector((0, 0, -0.45)), Vector((-H, 0, 0)) + U * k1 + Vector((0, 0, -0.45)), 0.55)
mesh_obj("Rack", bm, M_RIG, RIG)
for k in (k0 + 0.5, k1 - 0.5):
    p = Vector((-H, 0, 0)) + U * k
    box(f"RackLeg{k:.0f}", p.x - 0.25, p.x + 0.25, -0.9, 0.9, 0.1, p.z - 0.5, M_STEEL, RIG)
box("Tracks", -H - 13.5, -H - 2.0, -1.7, 1.7, 0.1, 0.9, M_DARK, RIG)
box("Deck", -H - 13.0, -H - 2.5, -1.5, 1.5, 0.9, 1.3, M_RIG, RIG)
box("Cab", -H - 15.8, -H - 13.2, -1.3, 1.3, 1.3, 3.6, M_RIG, RIG)
SCREEN = box("CabScreen", -H - 13.25, -H - 13.15, -0.8, 0.8, 2.3, 3.2, M_WIN, RIG)
glow(B_WIN, [(0, 0.3)] + pulse(C["tells"], 3.5, base=0.3, up=0.2, hold=1.2))
for j in range(6):
    cyl(f"RodStack{j}", 0.13, 9.0, "X", (-H - 7.5, 1.0 + 0.28 * (j % 3), 1.45 + 0.27 * (j // 3)), M_ROD, RIG, seg=12)
cyl("MudTank", 1.0, 5.0, "X", (-H - 9.0, 4.5, 1.1), M_STEEL, RIG)
box("EntryPit", -H - 1.5, -H + 2.5, 0.0, 3.0, -0.35, 0.11, M_CUT, RIG)
box("ExitPit", H - 2.5, H + 1.5, 0.0, 3.0, -0.35, 0.11, M_CUT)
CARR = empty("Carriage")
box("CarriageBox", -0.9, 0.9, -0.7, 0.7, -0.6, 0.6, M_DARK, CARR)
def carr_k(t):
    d = LPRE + rod_end(t) if (T_LB <= t) else LPRE
    return 2.2 + (d % 9.0)
cp = [Vector((-H, 0, 0)) + U * (11.5 - (carr_k(t) - 2.2)) + Vector((0, 0, 0.15)) for t in TS]
for ax in range(3): bake(CARR, "location", ax, [v[ax] for v in cp])
CARR.rotation_euler = (0, ANG, 0)

# ================= demo set: the slanted bit up close (x = 400) =================
DO = Vector((400.0, 0.0, -60.0))
box("DemoBlock", 385.0, 415.0, 0.0, 12.0, DO.z - 14.0, DO.z + 14.0, M_CLAY)
RA = 7.0
DPTS = [DO + Vector((-15.0 + 0.5 * k, 0, 0)) for k in range(30)] + \
       [DO + Vector((RA * math.sin(math.radians(a)), 0, -RA * (1 - math.cos(math.radians(a))))) for a in range(0, 61, 2)]
SD = cum(DPTS); S_STRAIGHT = SD[29] + 0.5
def sd(t):
    s_spin0, s_spin1 = S_STRAIGHT - 4.0, S_STRAIGHT
    if t < T_SPIN: return s_spin0
    if t < T_STOP: return s_spin0 + 4.0 * lin((t - T_SPIN) / (T_STOP - 0.1 - T_SPIN))
    if t < T_PUSH: return s_spin1
    return s_spin1 + RA * 0.95 * ease((t - T_PUSH) / (T_TX - 0.2 - T_PUSH))
DH, DHC = curve("DemoHole", DPTS, 0.40, M_HOLE, flat=True)
reveal(DHC, lambda t: 0.0, lambda t: sd(t) / SD[-1])
DR, DRC = curve("DemoRod", DPTS, 0.13, M_ROD, res=3)
reveal(DRC, lambda t: 0.0, lambda t: (sd(t) - 1.1) / SD[-1])
DP = empty("DemoPivot"); DSP = empty("DemoSpin", parent=DP)
DBIT, DSON = bit_mesh("Demo", M_BIT, M_SONDE, DSP)
dp = [at(DPTS, SD, sd(t)) for t in TS]
bake(DP, "location", 0, [p.x for p, a in dp]); bake(DP, "location", 2, [p.z for p, a in dp]); bake(DP, "rotation_euler", 1, [-a for p, a in dp])
SPIN_N = 6
bake_fn(DSP, "rotation_euler", 0, lambda t: 2 * math.pi * SPIN_N * lin((t - T_SPIN) / (T_STOP - T_SPIN)))
glow(B_BIT, [(0, 0)] + pulse(C["slanted"], 2.0, up=0.2, hold=1.2) + pulse(T_PUSH, 1.5, up=0.2, hold=1.5))
# gold arrows: soil pressing on the slanted face while the rod is pushed without spinning
bm = bmesh.new()
for k in range(3): add_arrow(bm, (DO.x + 0.2 + 0.55 * k, DO.z + 2.2), (-0.35, -1.0), 1.5, 0.45, y=-0.5)
ARR = mesh_obj("PushArrows", bm, M_GOLD); windows(ARR, [(T_PUSH + 0.1, T_TX)])
bake_fn(ARR, "location", 0, lambda t: 0.0 if t < T_PUSH else 2.2 * ease((t - T_PUSH) / (T_TX - T_PUSH)))
bake_fn(ARR, "location", 2, lambda t: 0.0 if t < T_PUSH else -1.0 * ease((t - T_PUSH) / (T_TX - T_PUSH)))
bm = bmesh.new(); add_arrow(bm, (DO.x - 3.2, DO.z), (1.0, 0.0), 2.6, 0.45, y=-0.5)
SARR = mesh_obj("StraightArrow", bm, M_CYAN); windows(SARR, [(C["drills"], T_STOP)])

# ================= transmitter: rings rise to the surface, a locator mark on the ground =================
RINGS = []
for k in range(5):
    o = lathe(f"Ring{k}", [(1.0 + 0.08 * math.cos(2 * math.pi * j / 8), 0.08 * math.sin(2 * math.pi * j / 8)) for j in range(8)], M_CYAN, 0.0, 2 * math.pi, 40)
    ph = k / 5.0
    def ring_u(t, ph=ph): return ((t - C["transmitter"]) / 1.6 + ph) % 1.0
    bake_fn(o, "location", 0, lambda t: head_pose(t)[0].x)
    bake_fn(o, "location", 1, lambda t: -0.3)
    bake_fn(o, "location", 2, lambda t, f=ring_u: head_pose(t)[0].z + (0.2 - head_pose(t)[0].z) * f(t))
    for ax in (0, 1): bake_fn(o, "scale", ax, lambda t, f=ring_u: 0.3 + 1.6 * f(t))
    o.rotation_euler = (math.radians(90), 0, 0)
    windows(o, [(C["transmitter"], T_DIVE)]); RINGS.append(o)
MARK = cyl("LocatorMark", 0.8, 0.06, "Z", (0, 0, 0.0), M_CYAN, seg=32)
bake_fn(MARK, "location", 0, lambda t: head_pose(t)[0].x); bake_fn(MARK, "location", 1, lambda t: 1.2); bake_fn(MARK, "location", 2, lambda t: 0.16)
windows(MARK, [(C["crew"], T_DIVE)])

# ================= reamer (spinning barrel with teeth) =================
RMP = empty("ReamerPivot"); RMS = empty("ReamerSpin", parent=RMP)
cyl("ReamBarrel", 0.55, 1.6, "X", (0, 0, 0), M_REAM, RMS, seg=24)
bm = bmesh.new(); add_cyl(bm, 0.55, 0.6, "X", (-1.1, 0, 0), 24, r2=0.14); mesh_obj("ReamCone", bm, M_REAM, RMS)
for k in range(10):
    a = 2 * math.pi * k / 10
    for xx in (-0.5, 0.0, 0.5):
        o = box(f"Tooth{k}_{xx}", xx - 0.12, xx + 0.12, -0.07, 0.07, 0.5, 0.78, M_STEEL, RMS); o.rotation_euler = (a, 0, 0)
rp = [at(PP, SP, reamer_s(t)) for t in TS]
bake(RMP, "location", 0, [p.x - 0.0 for p, a in rp]); bake(RMP, "location", 2, [p.z for p, a in rp]); bake(RMP, "rotation_euler", 1, [-a for p, a in rp])
bake_fn(RMS, "rotation_euler", 0, lambda t: t * 7.0)
bake_fn(RMS, "scale", 1, lambda t: 1.15 if R2 <= t < R3 or t >= T_WELD else 0.8)
bake_fn(RMS, "scale", 2, lambda t: 1.15 if R2 <= t < R3 or t >= T_WELD else 0.8)
windows(RMP, [(T_REAM, T_CAVE0), (P0 - 0.5, P1 + 0.1)])
glow(B_REAM, [(0, 0)] + pulse(C["reamer"], 1.2, up=0.2, hold=0.6))

# ================= cave-in chunks, mud flow, cuttings, wall arrows, frac-out =================
random.seed(21)
for k in range(14):
    x0 = random.uniform(-7.0, 7.0); z0 = zp(x0) + random.uniform(0.75, 0.95); r_ = random.uniform(0.15, 0.28)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r_)
    for vv in bm.verts: vv.co *= random.uniform(0.75, 1.2)
    o = mesh_obj(f"Chunk{k}", bm, M_SPOIL); o.location = (x0, -0.2, z0)
    t0 = C["cave"] + 0.05 * k; zf = zp(x0) - 0.7
    bake_fn(o, "location", 2, lambda t, z0=z0, t0=t0, zf=zf: z0 if t < t0 else max(zf, z0 - 0.5 * 20.0 * (t - t0) ** 2))
    windows(o, [(T_CAVE0, T_MUD + 0.3)])
glow(B_SPOIL, [(0, 0)] + pulse(C["cave"], 1.0, up=0.15, hold=0.6))
def dots_along(name, n, m_, r, speed, s_fn_window, wins, dirn=1):
    objs = []
    for k in range(n):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        o = mesh_obj(f"{name}{k}", bm, m_)
        off = L * k / n
        def pos(t, off=off): return at(PP, SP, (off + dirn * speed * t) % L)[0]
        ps = [pos(t) for t in TS]
        bake(o, "location", 0, [p.x for p in ps]); bake(o, "location", 1, [-0.3] * FRAMES); bake(o, "location", 2, [p.z + random.uniform(-0.3, 0.3) for p in ps])
        windows(o, wins); objs.append(o)
    return objs
dots_along("MudDot", 34, M_MUDD, 0.16, 9.0, None, [(C["drilling"] + 0.3, T_FRAC)])
dots_along("Cutting", 30, M_CUT, 0.2, 9.0, None, [(C["carries"], T_FRAC)], dirn=-1)
bm = bmesh.new()
for x in (-1.5, 1.5):
    add_arrow(bm, (x, zp(x) + 0.2), (0, 1), 1.6, 0.6, y=-0.5); add_arrow(bm, (x, zp(x) - 0.2), (0, -1), 1.6, 0.6, y=-0.5)
WARR = mesh_obj("WallArrows", bm, M_GOLD); windows(WARR, [(C["holds"], C["carries"])])
CRACK = []
bm = bmesh.new(); add_bar(bm, (2.0, -0.4, zp(2.0) + 0.9), (2.6, -0.4, -4.5), 0.18); add_bar(bm, (2.6, -0.4, -4.5), (3.4, -0.4, -6.0), 0.18)
CRK = mesh_obj("FracCrack", bm, M_REDL); windows(CRK, [(C["hard"], T_WELD)])
bake_fn(CRK, "scale", 2, lambda t: 0.02 + 0.98 * ease((t - C["hard"]) / 0.5)); CRK.location = (0, 0, 0)
for k in range(9):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.6)
    o = mesh_obj(f"Plume{k}", bm, M_CLOUD)
    t0 = C["bubbles"] + 0.18 * k
    bake_fn(o, "location", 0, lambda t, k=k: 3.4 + 0.4 * math.sin(k * 1.7))
    bake_fn(o, "location", 1, lambda t, k=k: 0.8 + 0.5 * k)
    bake_fn(o, "location", 2, lambda t, t0=t0: -5.6 + 4.6 * ease((t - t0) / 1.6))
    for ax in range(3): bake_fn(o, "scale", ax, lambda t, t0=t0: max(0.01, 0.6 + 2.4 * ease((t - t0) / 1.8)) if t >= t0 else 0.01)
    windows(o, [(t0, T_WELD)])
# trench in the hook: a dark slot in the riverbed, spoil heaps, a mud cloud drifting downstream
TRENCH = box("Trench", -3.0, 3.0, -0.06, 60.0, -9.5, -5.95, M_CUT); windows(TRENCH, [(C["trench"], T_LB)])
for k, x in enumerate((-6.5, 6.5)):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=2.6)
    for vv in bm.verts: vv.co.z *= 0.5
    o = mesh_obj(f"SpoilHeap{k}", bm, M_SPOIL); o.location = (x, 6.0, -6.0); windows(o, [(C["trench"], T_LB)])
for k in range(10):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    o = mesh_obj(f"Cloud{k}", bm, M_CLOUD)
    t0 = C["mud1"] - 0.6 + 0.12 * k
    bake_fn(o, "location", 0, lambda t, k=k: -6.0 + 1.4 * k)
    bake_fn(o, "location", 1, lambda t, t0=t0, k=k: 2.0 + 3.0 * (k % 3) + 6.0 * max(0.0, t - t0))
    bake_fn(o, "location", 2, lambda t, k=k: -4.8 + 0.6 * (k % 4))
    for ax in range(3): bake_fn(o, "scale", ax, lambda t, t0=t0: max(0.01, 0.6 + 1.5 * ease((t - t0) / 1.5)) if t >= t0 else 0.01)
    windows(o, [(t0, T_LB)])
glow(B_SPOIL, [(0, 0)])

# ================= garden hose, pipe rollers + weld flashes, boats, other pipes for the CTA =================
HOSEP = Vector((-40.0, 2.5, 0.12))
for k in range(4):
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=False, radius=0.42 - 0.03 * k, segments=36)
    o = mesh_obj(f"HoseCoil{k}", bm, M_HOSE); o.location = HOSEP + Vector((0, 0, 0.05 * k))
    md = o.modifiers.new("skin", "SKIN")
    try:
        for sv in o.data.skin_vertices[0].data: sv.radius = (0.035, 0.035)
    except Exception: pass
    md2 = o.modifiers.new("sub", "SUBSURF"); md2.levels = 1; md2.render_levels = 1
cyl("HoseNozzle", 0.05, 0.25, "X", (HOSEP.x + 0.55, HOSEP.y - 0.1, 0.17), M_BRASS, seg=16)
for k in range(0, int(LP) + 4, 6):
    p = TAIL0 + Vector((k, 0, 0)); box(f"Roller{k}", p.x - 0.35, p.x + 0.35, -0.6, 0.6, 0.1, 0.2, M_DARK)
WELDS = []
for j, k in enumerate(range(12, int(LP), 12)):
    p = TAIL0 + Vector((k, 0, 0))
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.7); o = mesh_obj(f"Weld{j}", bm, M_GOLD); o.location = (p.x, -0.1, p.z)
    t0 = C["welded"] + 0.11 * j
    for ax in range(3): bake_fn(o, "scale", ax, lambda t, t0=t0: 1.0 if t0 <= t < t0 + 0.35 else 0.01)
    windows(o, [(t0, t0 + 0.4)]); WELDS.append(round(t0, 3))
def boat(name, x, yfn):
    g = empty(name)
    bm = bmesh.new(); add_box(bm, -1.1, 1.1, -3.0, 3.0, -0.4, 0.5)
    for v in bm.verts:
        if v.co.y > 2.0: v.co.x *= 0.35
    mesh_obj(name + "Hull", bm, M_HULL, g)
    box(name + "Stripe", -1.12, 1.12, -3.0, 2.2, -0.42, -0.15, M_HULLR, g)
    box(name + "Cabin", -0.8, 0.8, -1.8, 0.4, 0.5, 1.6, M_HULL, g)
    box(name + "Glass", -0.82, 0.82, 0.2, 0.42, 0.8, 1.4, M_DARK, g)
    bake_fn(g, "location", 0, lambda t: x); bake_fn(g, "location", 1, yfn); bake_fn(g, "location", 2, lambda t: -0.45 + 0.05 * math.sin(t * 2.0))
    return g
boat("BoatA", -5.0, lambda t: 9.0 + 0.6 * t)
boat("BoatB", 6.0, lambda t: 70.0 - 0.9 * t)
OTHER = []
for k, (dep, h, m_, r_) in enumerate([(8.5, 34.0, M_CYAN, 0.18), (16.0, 70.0, M_WHITEG, 0.35), (10.0, 48.0, M_CYAN, 0.15)]):
    pts = [Vector((x, 0.0, -dep * (1 - (x / h) ** 2))) for x in [-h + 0.5 * i for i in range(int(4 * h) + 1)]]
    o, cu = curve(f"OtherPipe{k}", pts, r_, m_, res=3); o.location.y = 1.0 + 0.6 * k
    t0 = C["many"] + 0.35 * k
    reveal(cu, lambda t: 0.0, lambda t, t0=t0: ease((t - t0) / 0.8)); windows(o, [(t0, DUR)]); OTHER.append(round(t0, 3))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
HX = lambda t: head_pose(t)[0].x
HZ = lambda t: head_pose(t)[0].z
HOOK = ((lambda t: HX(t) + 1.5), -16.0, (lambda t: HZ(t) + 7.0)), (HX, 0.0, (lambda t: HZ(t) + 5.5))
TRK = ((lambda t: HX(t) + 2.0), -13.0, (lambda t: HZ(t) + 4.5)), (HX, 0.0, (lambda t: HZ(t) + 2.5))
WIDE = ((lambda t: 0.55 * HX(t)), -70.0, -3.0), ((lambda t: 0.55 * HX(t)), 0.0, -5.0)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK, 22),
    (T_TR - 0.05, *HOOK, 22),
    (T_TR, (0.0, -40.0, -1.0), (0.0, 0.0, -4.5), 18, "cut"),
    (T_LB - 0.05, (0.0, -35.0, -1.5), (0.0, 0.0, -4.5), 18),
    (T_LB, (-75.0, -85.0, 45.0), (0.0, 20.0, -6.0), 22, "cut"),
    (T_HOSE - 0.05, (-70.0, -80.0, 42.0), (0.0, 20.0, -6.0), 22),
    (T_HOSE, (-39.5, -0.2, 1.0), (-40.0, 2.5, 0.15), 30, "cut"),
    (T_GAS - 0.05, (-39.4, 0.1, 0.85), (-40.0, 2.5, 0.15), 30),
    (T_GAS, (0.0, -95.0, -2.0), (0.0, 0.0, -5.0), 20, "cut"),
    (T_RIG - 0.05, (0.0, -88.0, -2.0), (0.0, 0.0, -5.0), 20),
    (T_RIG, (-51.0, -15.0, 3.5), (-59.0, 0.0, 0.8), 24, "cut"),
    (T_STR - 0.05, (-52.0, -13.0, 3.0), (-59.0, 0.0, 0.8), 24),
    (T_STR, (-42.0, -34.0, -6.0), (-44.0, 0.0, -8.0), 20, "cut"),
    (T_SLANT - 0.05, (-42.0, -32.0, -6.0), (-44.0, 0.0, -8.0), 20),
    (T_SLANT, (396.6, -3.2, -59.5), (396.3, 0.0, -60.0), 30, "cut"),
    (T_SPIN - 0.05, (396.5, -2.9, -59.6), (396.3, 0.0, -60.0), 30),
    (T_SPIN + 0.6, (399.0, -11.0, -60.5), (399.5, 0.0, -61.0), 24),
    (T_PUSH, (400.5, -11.5, -61.0), (401.0, 0.0, -61.5), 24),
    (T_TX - 0.05, (401.5, -12.0, -61.5), (402.0, 0.0, -62.0), 24),
    (T_TX, *TRK, 22, "cut"),
    (T_DIVE - 0.05, *TRK, 22),
    (T_DIVE, *WIDE, 20, "cut"),
    (C["climbs"], *WIDE, 20),
    (C["bank"] + 0.3, (40.0, -30.0, 0.0), (50.0, 0.0, -2.0), 22),
    (T_BUT - 0.05, (40.5, -29.0, 0.0), (50.0, 0.0, -2.0), 22),
    (T_BUT, (0.8, -6.0, -10.5), (0.0, 0.0, -12.0), 24, "cut"),
    (T_REAM - 0.05, (0.6, -5.0, -11.0), (0.0, 0.0, -12.0), 24),
    (T_REAM, (47.0, -16.0, 1.0), (54.0, 0.0, -1.0), 22, "cut"),
    (R0 + 0.3, (47.0, -16.0, 1.0), (54.0, 0.0, -1.0), 22),
    (R0 + 1.2, (0.0, -90.0, -2.0), (0.0, 0.0, -5.0), 20),
    (T_CAVE0 - 0.05, (0.0, -88.0, -2.0), (0.0, 0.0, -5.0), 20),
    (T_CAVE0, (1.0, -7.0, -10.5), (0.0, 0.0, -12.0), 22, "cut"),
    (C["carries"], (0.5, -8.0, -10.5), (0.0, 0.0, -12.0), 22),
    (C["carries"] + 0.6, (-44.0, -22.0, -2.0), (-50.0, 0.0, -3.0), 22),
    (T_FRAC - 0.05, (-44.5, -21.0, -2.0), (-50.0, 0.0, -3.0), 22),
    (T_FRAC, (2.0, -28.0, -4.0), (2.0, 0.0, -6.0), 20, "cut"),
    (T_WELD - 0.05, (2.5, -25.0, -3.5), (2.0, 0.0, -6.0), 20),
    (T_WELD, (78.0, -26.0, 5.0), (100.0, 0.0, 0.5), 22, "cut"),
    (T_PULL - 0.05, (90.0, -26.0, 5.0), (110.0, 0.0, 0.5), 22),
    (T_PULL, (20.0, -110.0, 8.0), (25.0, 0.0, -4.0), 20, "cut"),
    (T_BOAT - 0.05, (5.0, -100.0, 6.0), (0.0, 0.0, -4.0), 20),
    (T_BOAT, (-65.0, -75.0, 38.0), (0.0, 18.0, -6.0), 22, "cut"),
    (T_CTA - 0.05, (-55.0, -80.0, 32.0), (0.0, 18.0, -6.0), 22),
    (T_CTA, (-35.0, -55.0, 14.0), (0.0, 8.0, -7.0), 22, "cut"),
    (DUR, (-28.0, -46.0, 11.0), (0.0, 8.0, -7.0), 22),
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
    cam_loc.append(l0 + Vector((0.03 * math.sin(t * 0.7), 0.0, 0.02 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)

world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
try:
    sky = wn.new("ShaderNodeTexSky")
    for st_ in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try: sky.sky_type = st_; break
        except Exception: continue
    try: sky.sun_elevation = math.radians(35); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"])
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1)
bg.inputs["Strength"].default_value = 0.22
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.angle = math.radians(3); sun_d.energy = 3.2
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(-35))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (1.0, 0.95, 0.88); fill_d.energy = 3000
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)

# ================= render settings =================
r = scene.render; r.engine = "CYCLES"
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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 6; scene.cycles.transparent_max_bounces = 12; scene.cycles.volume_bounces = 0
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = False
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
prefs.keyframe_new_interpolation_type = "BEZIER"


sun_d.energy = 3.4
# ================= export cues, events and projected anchors for the typography =================
def demo_face(t):
    p, a = at(DPTS, SD, sd(t)); return p + Vector((math.cos(a), 0, math.sin(a))) * 0.4 + Vector((0, -0.3, 0.15))
ANCHP = {
    "head": lambda t: head_pose(t)[0] + Vector((0, -0.3, 0)),
    "sonde": lambda t: (lambda pa: pa[0] - Vector((math.cos(pa[1]), 0, math.sin(pa[1]))) * 0.95 + Vector((0, -0.3, 0)))(head_pose(t)),
    "rig": lambda t: Vector((-H - 8.0, 0.0, 2.6)),
    "rod": lambda t: Vector((-H + 3.0, -0.2, zp(-H + 3.0))),
    "slant": demo_face,
    "reamer": lambda t: at(PP, SP, reamer_s(t))[0] + Vector((0, -0.6, 0.9)),
    "mud": lambda t: Vector((-3.0, -0.3, zp(-3.0))),
    "pipe": lambda t: TAIL0 + Vector((46.0, -0.6, 0.0)),
    "hose": lambda t: HOSEP + Vector((0, 0, 0.1)),
    "trench": lambda t: Vector((0.0, -0.1, -7.5)),
    "crack": lambda t: Vector((2.8, -0.4, -5.2)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(0.0, T_TR), "trench": round(C["trench"], 3), "push": RR(C["pushes"], T_STR - 0.3), "spin": RR(T_SPIN, T_STOP),
          "bend": RR(T_PUSH, T_TX - 0.2), "dive": RR(T_DIVE, C["bank"] + 0.3), "exit": round(C["bank"] + 0.3, 3), "ream1": RR(R0, R1), "ream2": RR(R2, R3),
          "cave": round(C["cave"], 3), "mud": round(C["drilling"], 3), "frac": round(C["bubbles"], 3), "welds": WELDS, "pull": RR(P0, P1),
          "others": OTHER, "cta": round(T_CTA, 3)}
if not os.environ.get("COVER"): json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
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
