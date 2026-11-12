# Lightning-Rod-3D: how a lightning rod protects a house. Build-up format ("THIS IS A METAL ROD", drafts/build-up-scripts-2026-11-09.md #3):
# hook: a bolt hits the rod on the ridge, the current rides the cables into the ground (a rod doesn't pull lightning in, it picks the road) ->
# without one: front wall cut away, the bolt runs through wiring, pipes, the wood in between, fire glow -> a bare metal rod on the ridge does
# nothing on its own (the strike spills into the roof) -> a thick copper cable down the outside -> no sharp corners (demo wall at x = 100:
# the current leaps off a tight corner into the wall) -> ground rod driven into the dirt, current spreads out (rings in the soil) ->
# a second cable + ground rod on the far corner -> more short rods along the ridge, tied together, ghost strikes hit metal first ->
# bonded to the house's electrical ground (bond wire in the soil) -> the storm: bolt on the ridge, both cables glow, gone into the ground -> CTA pull-out.
# Blender Cycles, stormy dusk, generic gable house on a lawn block cut at y = -5 (soil face shows the ground rods), camera on -y.
# Illustrative (1 unit = 1 m): conductors and rods drawn ~3x thick so they read on a phone, ground rods ~2.7 m, no real address or brand.
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

CUES = [("if", "If"), ("hits", "hits"), ("ground", "ground"), ("a", "A"), ("rod", "rod"), ("pull", "pull"), ("picks", "picks"), ("road", "road."),
        ("without", "Without"), ("bolt", "bolt"), ("wiring", "wiring,"), ("pipes", "pipes,"), ("wood", "wood"), ("between", "between."),
        ("lightning", "Lightning"), ("billion", "billion"), ("year", "year."), ("this", "This"), ("metal", "metal"), ("rod2", "rod."),
        ("own", "own,"), ("nothing", "nothing."), ("typical", "typical"), ("bolt2", "bolt"), ("thirty", "thirty"), ("amps", "amps,"),
        ("needs", "needs"), ("down", "down."), ("so", "So"), ("thick", "thick"), ("cable", "cable,"), ("copper", "copper"), ("running", "running"),
        ("house", "house."), ("no", "No"), ("sharp", "sharp"), ("bends", "bends"), ("gentle", "gentle,"), ("because", "because"), ("tight", "tight"),
        ("leap", "leap"), ("wall", "wall."), ("at", "At"), ("bottom", "bottom,"), ("clamps", "clamps"), ("groundrod", "ground"), ("driven", "driven"),
        ("deep", "deep"), ("spreads", "spreads"), ("earth", "earth."), ("one", "One"), ("path", "path"), ("two", "two"), ("cables", "cables"),
        ("apart", "apart"), ("more", "More"), ("rods", "rods"), ("ridge", "ridge,"), ("tied", "tied"), ("wherever", "wherever"), ("lands", "lands,"),
        ("metal2", "metal"), ("first", "first."), ("and", "And"), ("system", "system"), ("bonded", "bonded"), ("electrical", "electrical"),
        ("gap", "gap"), ("jump", "jump."), ("now", "Now"), ("storm", "storm"), ("bolt3", "bolt"), ("lands2", "lands"), ("ridge2", "ridge,"),
        ("rides", "rides"), ("cables2", "cables"), ("vanishes", "vanishes"), ("ground3", "ground."), ("does", "Does"), ("hoping", "hoping?"),
        ("tell", "Tell"), ("nextup", "Next"), ("flush", "flush"), ("follow", "Follow")]
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
CL = coll("LightningRod")
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
def half_pile(name, r, length, m_, x=0.0):
    """Solid pile, origin at the toe, cut at y = -0.02 (its section sits just in front of the soil cut face)."""
    bm = bmesh.new(); add_cyl(bm, r, length, "Z", (0, 0, length / 2), 32); cut_front(bm, -0.02)
    o = mesh_obj(name, bm, m_); o.location = (x, 0, 0); return o
def ghost_mat(name, rgb, strength=1.4):
    """transparent <-> emissive tint, Fac and Color keyable (returns material, fac socket, color socket, strength socket)."""
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    tr = N.new("ShaderNodeBsdfTransparent"); em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1)
    em.inputs["Strength"].default_value = strength
    mx = N.new("ShaderNodeMixShader"); mx.inputs[0].default_value = 0.0
    L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    return m, mx.inputs[0], em.inputs["Color"], em.inputs["Strength"]


# ================= materials =================
def emis(name, rgb, strength=4.0):
    """Pure emission (glow curves, bolts, rings); Strength socket keyable."""
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; N = nt.nodes
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    em = N.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*rgb, 1); em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m, em.inputs["Strength"]
M_SIDING, B_SIDING = mat("Siding", (0.50, 0.53, 0.56), 0.6, noise=3.0)
M_TRIM, _ = mat("Trim", (0.82, 0.82, 0.80), 0.5)
M_ROOF, _ = mat("Roof", (0.075, 0.075, 0.085), 0.85, noise=6.0)
M_SLAB, _ = mat("Slab", (0.42, 0.42, 0.40), 0.9, noise=2.0)
M_WIN, B_WIN = mat("Window", (0.10, 0.08, 0.05), 0.2, emit_rgb=(1.0, 0.72, 0.38)); B_WIN.inputs["Emission Strength"].default_value = 2.2
M_DOOR, _ = mat("Door", (0.22, 0.12, 0.08), 0.6)
M_WOOD, B_WOOD = mat("Wood", (0.62, 0.45, 0.28), 0.7, emit_rgb=(1.0, 0.35, 0.06), noise=4.0)
M_FLOOR, _ = mat("Floor", (0.35, 0.27, 0.20), 0.6)
M_WALLIN, _ = mat("WallIn", (0.78, 0.76, 0.72), 0.8)
M_WIRE, _ = mat("Wire", (0.12, 0.12, 0.13), 0.5)
M_PIPE, _ = mat("Pipe", (0.70, 0.71, 0.72), 0.3, metallic=0.8)
M_PANEL, _ = mat("Panel", (0.55, 0.57, 0.58), 0.4, metallic=0.6)
M_COPPER, B_COPPER = mat("Copper", (0.86, 0.43, 0.22), 0.28, metallic=1.0, emit_rgb=(1.0, 0.70, 0.30))
M_GROD, B_GROD = mat("GroundRod", (0.80, 0.42, 0.24), 0.32, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_EGROD, B_EGROD = mat("ElecGroundRod", (0.62, 0.50, 0.40), 0.4, metallic=0.9, emit_rgb=(0.30, 0.92, 1.0))
M_GRASS = ground("Grass", (0.035, 0.085, 0.03), (0.07, 0.15, 0.05), 0.8)
M_TOP = soil_mat("Topsoil", (0.16, 0.10, 0.06), (0.24, 0.16, 0.10), 1.0)
M_CLAY = soil_mat("Clay", (0.24, 0.13, 0.07), (0.34, 0.20, 0.11), 0.7)
M_DEEP = soil_mat("Deep", (0.10, 0.07, 0.05), (0.15, 0.10, 0.07), 0.5)
M_TRUNK, _ = mat("Trunk", (0.10, 0.07, 0.05), 0.9)
M_LEAF, _ = mat("Leaf", (0.03, 0.07, 0.035), 0.9)
M_CLOUD, B_CLOUD = mat("Cloud", (0.24, 0.25, 0.30), 1.0, emit_rgb=(0.55, 0.65, 1.0))
M_BOLT, S_BOLT = emis("Bolt", (0.80, 0.88, 1.0), 40.0)
M_BOLTR, _ = emis("BoltRed", (1.0, 0.35, 0.22), 30.0)
M_GOLD, _ = emis("CurrentGold", (1.0, 0.62, 0.12), 4.0)
M_CYANG, _ = emis("CurrentCyan", (0.30, 0.92, 1.0), 7.0)
M_RED, _ = emis("CurrentRed", (1.0, 0.25, 0.15), 8.0)
M_RING, _ = emis("Ring", (0.30, 0.92, 1.0), 5.0)
M_SPILL, F_SPILL, _, _ = ghost_mat("Spill", (1.0, 0.25, 0.12), 3.0)
M_SCORCH, F_SCORCH, _, _ = ghost_mat("Scorch", (0.9, 0.12, 0.04), 1.6)

# ================= geometry constants =================
HX, HY, WH, RIDGE, EY, OX = 6.0, 4.0, 5.0, 8.0, 4.4, 6.35     # half width, half depth, wall height, ridge z, eave y, roof overhang x
RT = 0.2                                                     # roof thickness
def zr(y): return RIDGE + RT - (RIDGE - WH) * abs(y) / EY      # roof top surface
ZR = zr(0.0)
YF = -5.0                                                    # soil cut face (front of the lawn block)
R_X = [-5.6, -1.9, 1.9, 5.6]                                 # air terminals along the ridge
ROD_H = 0.95
GL_X, GR_X, EG_X = -6.7, 6.7, -3.6                           # ground rods (lightning L/R, electrical service)
G_TOP, G_LEN = -0.35, 2.7
T_W = C["without"] - 0.02                                    # the finished system is shown in the hook, then rebuilt

def curve(name, pts, r, m_, res=3):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (p[0], p[1], p[2], 1.0)
    cu.bevel_depth = r; cu.bevel_resolution = res; cu.use_fill_caps = True
    cu.bevel_factor_mapping_start = "SPLINE"; cu.bevel_factor_mapping_end = "SPLINE"
    o = bpy.data.objects.new(name, cu); CL.objects.link(o); cu.materials.append(m_)
    return o, cu
def reveal(cu, f0, f1):
    bake_scalar(cu, "bevel_factor_start", [max(0.0, min(0.999, f0(t))) for t in TS])
    bake_scalar(cu, "bevel_factor_end", [max(0.001, min(1.0, f1(t))) for t in TS])
def rounded(pts, r=0.55, n=7):
    """Polyline with every inner corner replaced by a gentle arc (lightning conductors: no sharp bends)."""
    P = [Vector(p) for p in pts]; out = [P[0]]
    for i in range(1, len(P) - 1):
        a_, b_, c_ = P[i - 1], P[i], P[i + 1]
        ra = min(r, (a_ - b_).length * 0.45); rb = min(r, (c_ - b_).length * 0.45)
        s0 = b_ + (a_ - b_).normalized() * ra; s1 = b_ + (c_ - b_).normalized() * rb
        for k in range(n + 1):
            u = k / n; out.append((1 - u) ** 2 * s0 + 2 * (1 - u) * u * b_ + u * u * s1)
    out.append(P[-1]); return out
def plen(pts): return sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))
def frac_at(pts, idx):
    """Length fraction of the polyline up to point idx."""
    return plen(pts[:idx + 1]) / plen(pts)

# ================= the yard: lawn block cut at y = YF =================
box("Lawn", -40, 40, YF, 60, -0.25, 0.0, M_GRASS)
box("Topsoil", -40, 40, YF, 60, -1.6, -0.25, M_TOP)
box("Clay", -40, 40, YF, 60, -4.5, -1.6, M_CLAY)
box("Deep", -40, 40, YF, 60, -22.0, -4.5, M_DEEP)
box("FarLawn", -300, 300, 60, 400, -0.25, 0.0, M_GRASS)
for k, (x, y, h) in enumerate([(-17, 16, 7), (-12, 24, 9), (-22, 30, 8), (14, 18, 8), (20, 26, 10), (9, 32, 7), (-4, 36, 9), (27, 14, 6), (-28, 14, 7)]):
    full_cyl(f"Trunk{k}", 0.25, x, y, 0.0, h * 0.4, M_TRUNK, seg=10)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=h * 0.3)
    for vv in bm.verts: vv.co.z *= 1.5; vv.co *= random.uniform(0.9, 1.1)
    cr_ = mesh_obj(f"Crown{k}", bm, M_LEAF); cr_.location = (x, y, h * 0.7); cr_.data.shade_smooth()

# ================= the house =================
box("Slab", -HX - 0.2, HX + 0.2, -HY - 0.2, HY + 0.2, -0.45, 0.3, M_SLAB)
FRONT = box("FrontWall", -HX, HX, -HY, -HY + 0.25, 0.3, WH, M_SIDING)
for k, (x0, x1, z0, z1) in enumerate([(-4.6, -2.8, 2.0, 3.6), (2.2, 4.0, 2.0, 3.6), (-0.6, 0.6, 0.3, 2.6)]):
    par(box(f"FrontOpening{k}", x0, x1, -HY - 0.04, -HY + 0.05, z0, z1, M_WIN if k < 2 else M_DOOR), FRONT)
    par(box(f"FrontTrim{k}", x0 - 0.12, x1 + 0.12, -HY - 0.06, -HY + 0.02, z0 - 0.12, z0, M_TRIM), FRONT)
box("BackWall", -HX, HX, HY - 0.25, HY, 0.3, WH, M_WALLIN)
box("SideWallL", -HX, -HX + 0.25, -HY, HY, 0.3, WH, M_SIDING)
box("SideWallR", HX - 0.25, HX, -HY, HY, 0.3, WH, M_SIDING)
for k, x in enumerate([-HX + 0.25, HX - 0.25]):       # interior faces of the side walls (light), visible in the cutaway
    box(f"SideIn{k}", x - 0.02, x + 0.02, -HY + 0.25, HY - 0.25, 0.3, WH, M_WALLIN)
box("Floor", -HX + 0.25, HX - 0.25, -HY + 0.25, HY - 0.25, 0.3, 0.36, M_FLOOR)
box("Ceiling", -HX + 0.25, HX - 0.25, -HY + 0.25, HY - 0.25, WH - 0.1, WH, M_WALLIN)
def gable(name, x0, x1):
    bm = bmesh.new()
    pts = [(-HY, WH), (HY, WH), (0.0, RIDGE)]
    a = [bm.verts.new((x0, y, z)) for y, z in pts]; b = [bm.verts.new((x1, y, z)) for y, z in pts]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(3):
        j = (i + 1) % 3; bm.faces.new([a[i], b[i], b[j], a[j]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return mesh_obj(name, bm, M_SIDING)
gable("GableL", -HX, -HX + 0.25); gable("GableR", HX - 0.25, HX)
def roof_slab(name, s):
    bm = bmesh.new(); vs = []
    for x in (-OX, OX):
        for y, dz in ((0.0, 0.0), (s * EY, 0.0)):
            vs.append((x, y, zr(y) - RT)); vs.append((x, y, zr(y)))
    v = [bm.verts.new(p) for p in vs]
    # v: x-,y0,bot / x-,y0,top / x-,ye,bot / x-,ye,top / x+,y0,bot / x+,y0,top / x+,ye,bot / x+,ye,top
    for f in ([0, 2, 3, 1], [4, 5, 7, 6], [1, 3, 7, 5], [0, 4, 6, 2], [0, 1, 5, 4], [2, 6, 7, 3]): bm.faces.new([v[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); return mesh_obj(name, bm, M_ROOF)
roof_slab("RoofFront", -1); roof_slab("RoofBack", 1)
box("RidgeCap", -OX, OX, -0.12, 0.12, ZR - 0.08, ZR + 0.04, M_ROOF)
# interior: studs on the back wall, wiring, pipes, the electrical panel
for k in range(15):
    x = -5.4 + k * 0.77
    box(f"Stud{k}", x - 0.06, x + 0.06, HY - 0.42, HY - 0.25, 0.36, WH - 0.1, M_WOOD)
box("TopPlate", -5.6, 5.6, HY - 0.42, HY - 0.25, WH - 0.25, WH - 0.1, M_WOOD)
for k in range(9):                                  # attic rafters seen through the cut
    x = -5.2 + k * 1.3
    box(f"Joist{k}", x - 0.06, x + 0.06, -HY + 0.3, HY - 0.3, WH - 0.32, WH - 0.1, M_WOOD)
PANEL = box("Panel", -HX + 0.25, -HX + 0.42, -2.9, -2.1, 1.1, 2.3, M_PANEL)
WIRE_A = [(1.0, -1.0, WH - 0.4), (-5.55, -1.0, WH - 0.4), (-5.55, -2.5, WH - 0.4), (-5.55, -2.5, 2.3)]
WIRE_B = [(1.0, -1.0, WH - 0.4), (1.0, HY - 0.5, WH - 0.4), (2.6, HY - 0.5, WH - 0.4), (2.6, HY - 0.5, 0.8)]
box("Outlet", 2.45, 2.75, HY - 0.48, HY - 0.42, 0.65, 0.95, M_TRIM)
box("JBox", 0.85, 1.15, -1.15, -0.85, WH - 0.5, WH - 0.32, M_PANEL)
PIPE = [(3.6, 1.6, zr(1.6) + 0.5), (3.6, 1.6, 0.36), (3.6, 1.6, -0.3), (3.6, -HY - 0.6, -0.3), (3.6, YF, -0.3), (3.6, YF, -1.2)]
curve("WireA", WIRE_A, 0.035, M_WIRE); curve("WireB", WIRE_B, 0.035, M_WIRE)
curve("PipeVent", PIPE[:2], 0.09, M_PIPE); curve("PipeUnder", PIPE[1:], 0.07, M_PIPE)
ELEC_GND = [(-5.6, -2.5, 1.1), (-5.6, -2.5, 0.4), (-5.6, -3.3, 0.4), (EG_X, -3.3, 0.4), (EG_X, -3.3, -0.3), (EG_X, YF, -0.3), (EG_X, YF, -0.5)]
curve("ElecGroundWire", ELEC_GND, 0.03, M_COPPER)
EG = full_cyl("ElecGroundRod", 0.07, EG_X, YF, -0.5 - G_LEN + 0.3, -0.5, M_EGROD, seg=16)

# ================= the lightning protection system =================
def air_terminal(name, x):
    m_ = M_COPPER.copy(); m_.name = name + "Mat"
    o = lathe(name, [(0.0, 0.0), (0.11, 0.0), (0.11, 0.1), (0.05, 0.1), (0.05, ROD_H - 0.12), (0.0, ROD_H)], m_, 0.0, 2 * math.pi, 20, (x, 0.0, ZR - 0.02))
    return o, bsdf_of(m_)
RODS = [air_terminal(f"AirTerminal{k}", x) for k, x in enumerate(R_X)]
R1 = RODS[0][0]
def cable_path(s):
    """Left (s = -1) / right (s = +1) down conductor: rod base -> ridge end -> down the rake -> over the eave -> down the corner -> into the soil -> ground rod."""
    x = s * 6.12; rx = R_X[0] if s < 0 else R_X[3]; gx = GL_X if s < 0 else GR_X
    return rounded([(rx, 0.0, ZR + 0.05), (x, 0.0, ZR + 0.05), (x, -EY + 0.05, zr(-EY) + 0.05), (x, -EY - 0.05, WH - 0.2),
                    (x, -HY - 0.12, WH - 0.6), (x, -HY - 0.12, 0.5), (gx, YF, 0.0), (gx, YF, G_TOP)], r=0.45)
PATH_L, PATH_R = cable_path(-1), cable_path(1)
CABLE_L, CL_CU = curve("CableL", PATH_L, 0.06, M_COPPER)
CABLE_R, CR_CU = curve("CableR", PATH_R, 0.06, M_COPPER)
RIDGE_PTS = [(R_X[0], 0.0, ZR + 0.05), (R_X[3], 0.0, ZR + 0.05)]
RIDGE_C, RC_CU = curve("RidgeConductor", RIDGE_PTS, 0.05, M_COPPER)
SHARP = [(-6.12, -EY * 0.55, zr(-EY * 0.55) + 0.05), (-6.12, -EY - 0.05, zr(-EY) + 0.05), (-6.12, -EY - 0.05, WH - 1.6)]
SHARP_O, _ = curve("SharpCorner", SHARP, 0.065, M_BOLTR)
def ground_rod(name, x, m_):
    o = full_cyl(name, 0.08, 0.0, 0.0, -G_LEN, 0.0, m_, seg=16); o.location = (x, YF, G_TOP); return o
GL = ground_rod("GroundRodL", GL_X, M_GROD); GR = ground_rod("GroundRodR", GR_X, M_GROD)
def clamp(name, x):
    o = box(name, -0.16, 0.16, -0.14, 0.14, -0.2, 0.08, M_PANEL); o.location = (x, YF, G_TOP); return o
CLAMP_L, CLAMP_R = clamp("ClampL", GL_X), clamp("ClampR", GR_X)
BOND_PTS = [(GL_X, YF, -0.75), (EG_X, YF, -0.75)]
BOND, BOND_CU = curve("Bond", BOND_PTS, 0.05, M_COPPER)

# visibility + build-up timing
windows(R1, [(0, T_W), (C["metal"] - 0.05, DUR)])
bake_loc(R1, lambda t: (R_X[0], 0.0, ZR - 0.02 + (drop(t, C["metal"] - 0.05, h=4.0, d=0.45) if t > T_W else 0.0)))
windows(CABLE_L, [(0, T_W), (C["thick"], C["no"]), (C["bends"], DUR)])
reveal(CL_CU, lambda t: 0.0, lambda t: 1.0 if t < T_W else lin((t - C["thick"]) / (C["house"] - C["thick"])))
windows(SHARP_O, [(C["no"], C["bends"])])
windows(CLAMP_L, [(0, T_W), (C["clamps"], DUR)])
bake_scale(CLAMP_L, lambda t: (1, 1, 1) if t < T_W else (pop(t, C["clamps"]),) * 3)
windows(GL, [(0, T_W), (C["groundrod"], DUR)])
DRIVE_HITS = [C["driven"] + 0.05, C["deep"] + 0.0, C["deep"] + 0.42]
def gl_off(t):
    if t < T_W: return 0.0
    off = G_LEN + 0.2
    for k, h in enumerate(DRIVE_HITS):
        off -= (G_LEN + 0.2) / 3 * ease((t - h) / 0.12)
    return off
bake_loc(GL, lambda t: (GL_X, YF, G_TOP + gl_off(t)))
T_TWO = C["two"]; T_GR = C["cables"] + 0.9
windows(CABLE_R, [(0, T_W), (T_TWO, DUR)]); windows(RODS[3][0], [(0, T_W), (T_TWO, DUR)])
reveal(CR_CU, lambda t: 0.0, lambda t: 1.0 if t < T_W else lin((t - T_TWO) / 1.3))
windows(GR, [(0, T_W), (T_GR, DUR)]); windows(CLAMP_R, [(0, T_W), (T_GR, DUR)])
bake_loc(GR, lambda t: (GR_X, YF, G_TOP + (0.0 if t < T_W else (G_LEN + 0.2) * (1 - ease((t - T_GR) / 0.55)))))
ROD_POPS = [C["rods"] + 0.05, C["rods"] + 0.3]
for k, tp in zip((1, 2), ROD_POPS):
    windows(RODS[k][0], [(0, T_W), (tp, DUR)])
    bake_scale(RODS[k][0], lambda t, tp=tp: (1, 1, 1) if t < T_W else (1.0, 1.0, pop(t, tp, 0.3)))
windows(RIDGE_C, [(0, T_W), (C["tied"], DUR)])
reveal(RC_CU, lambda t: 0.0, lambda t: 1.0 if t < T_W else lin((t - C["tied"]) / 0.9))
windows(BOND, [(0, T_W), (C["bonded"], DUR)])
reveal(BOND_CU, lambda t: 0.0, lambda t: 1.0 if t < T_W else lin((t - C["bonded"]) / 1.0))
windows(FRONT, [(0, C["without"]), (C["this"], C["and"]), (C["now"], DUR)])
# copper glints: the whole system on "system", each rod as a ghost strike lands on it
glow(B_COPPER, [(0, 0.0)] + pulse(C["system"], 1.6, hold=0.6, down=0.5))
GHOST = [(C["wherever"] + 0.15, 2), (C["lands"] + 0.05, 1), (C["metal2"], 3)]
for tg, k in GHOST: glow(RODS[k][1], [(0, 0.0)] + pulse(tg, 6.0, up=0.05, hold=0.25, down=0.4))
glow(B_GROD, [(0, 0.0)] + pulse(C["ground"], 3.0, hold=1.2) + pulse(C["spreads"] - 0.2, 3.0, hold=1.2) + pulse(C["vanishes"], 3.0, hold=1.0))
glow(B_EGROD, [(0, 0.0)] + pulse(C["gap"] - 0.3, 2.5, hold=0.6) + pulse(C["vanishes"], 2.5, hold=1.0))

# ================= current: glowing paths =================
def glow_curve(name, pts, m_, r, wins, f0, f1):
    o, cu = curve(name, pts, r, m_); windows(o, wins); reveal(cu, f0, f1); return o
S0 = C["hits"] + 0.1                      # hook strike on the ridge rod
STORM = C["lands2"]                       # the storm strike on rod 2
glow_curve("GlowHookL", PATH_L, M_GOLD, 0.085, [(S0 + 0.05, C["a"] - 0.1)],
           lambda t: 0.0, lambda t: lin((t - S0) / (C["ground"] - S0)))
glow_curve("PulseRoadL", PATH_L, M_GOLD, 0.095, [(C["picks"], T_W)],
           lambda t: lin((t - C["picks"]) / 0.9) - 0.25, lambda t: lin((t - C["picks"]) / 0.9))
glow_curve("PulseBends", PATH_L, M_CYANG, 0.09, [(C["bends"], C["because"])],
           lambda t: lin((t - C["bends"]) / 1.3) - 0.3, lambda t: lin((t - C["bends"]) / 1.3))
glow_curve("BondGlow", BOND_PTS, M_CYANG, 0.07, [(C["gap"], C["now"])], lambda t: 0.0, lambda t: lin((t - C["gap"]) / 0.4))
SL = [(R_X[1], 0.0, ZR + 0.05)] + PATH_L
SR = [(R_X[1], 0.0, ZR + 0.05), (R_X[3], 0.0, ZR + 0.05)] + PATH_R[1:]
def storm_f1(t, pts, ridge_idx):
    a = frac_at(pts, ridge_idx)
    if t < C["rides"]: return a * lin((t - STORM) / 0.5)
    return a + (1 - a) * lin((t - C["rides"]) / (C["vanishes"] - C["rides"]))
glow_curve("StormL", SL, M_GOLD, 0.09, [(STORM + 0.05, C["does"])], lambda t: lin((t - C["vanishes"]) / 0.9), lambda t: storm_f1(t, SL, 1))
glow_curve("StormR", SR, M_GOLD, 0.09, [(STORM + 0.05, C["does"])], lambda t: lin((t - C["vanishes"]) / 0.9), lambda t: storm_f1(t, SR, 2))
glow_curve("StormBond", BOND_PTS, M_GOLD, 0.07, [(C["vanishes"], C["does"])], lambda t: lin((t - C["ground3"] - 0.4) / 0.6), lambda t: lin((t - C["vanishes"]) / 0.4))
# without a rod: the strike runs through the wiring, the pipes, the wood
T_HIT1 = C["bolt"]
glow_curve("RedWireA", WIRE_A, M_RED, 0.06, [(C["wiring"] - 0.25, C["this"])], lambda t: 0.0, lambda t: lin((t - C["wiring"] + 0.25) / 0.7))
glow_curve("RedWireB", WIRE_B, M_RED, 0.06, [(C["wiring"] - 0.1, C["this"])], lambda t: 0.0, lambda t: lin((t - C["wiring"] + 0.1) / 0.7))
glow_curve("RedPipe", PIPE, M_RED, 0.11, [(C["pipes"] - 0.15, C["this"])], lambda t: 0.0, lambda t: lin((t - C["pipes"] + 0.15) / 0.7))
glow_curve("RedJump", [(1.0, -1.5, zr(-1.5)), (1.2, -1.2, 6.2), (0.9, -1.1, 5.4), (1.0, -1.0, WH - 0.3)], M_BOLTR, 0.05,
           [(T_HIT1 + 0.05, T_HIT1 + 0.3), (C["wiring"] - 0.35, C["wiring"] - 0.1)], lambda t: 0.0, lambda t: 1.0)
glow_curve("RedJumpPipe", [(1.1, -1.0, WH - 0.35), (2.3, 0.3, 5.6), (3.6, 1.6, 5.2)], M_BOLTR, 0.05,
           [(C["pipes"] - 0.3, C["pipes"] + 0.1)], lambda t: 0.0, lambda t: 1.0)
glow(B_WOOD, [(0, 0.0), (C["wood"] - 0.05, 0.0), (C["wood"] + 0.25, 2.5), (C["between"], 1.2), (C["lightning"], 2.2), (C["year"], 2.8), (C["this"] - 0.05, 2.8), (C["this"], 0.0)])

# ================= bolts =================
def bolt_pts(top, bot, seed, n=18, amp=1.4):
    rnd = random.Random(seed); top, bot = Vector(top), Vector(bot); pts = []
    for i in range(n + 1):
        u = i / n; p = top.lerp(bot, u)
        if 0 < i < n: p += Vector((rnd.uniform(-1, 1) * amp * (1 - u) ** 0.6, rnd.uniform(-0.4, 0.4) * amp * (1 - u), rnd.uniform(-0.3, 0.3)))
        pts.append(p)
    return pts
FLICK = [(0.0, 0.07, 1.0), (0.11, 0.24, 0.75), (0.30, 0.36, 0.5)]
def flick(t, t0):
    for a_, b_, g in FLICK:
        if t0 + a_ <= t < t0 + b_: return g
    return 0.0
def make_bolt(name, target, t0, seed, m_=M_BOLT, top_z=46.0, r=0.07, branches=2, amp=1.4, extra=()):
    tgt = Vector(target); top = (tgt.x + random.Random(seed).uniform(-6, 6), tgt.y + 10.0, top_z)
    main = bolt_pts(top, tgt, seed, 22, amp * 2.2)
    objs = [curve(name, main, r, m_)[0]]
    rnd = random.Random(seed + 7)
    for b in range(branches):
        k = rnd.randint(4, 12); s = main[k]
        end = s + Vector((rnd.uniform(-7, 7), rnd.uniform(-1, 1), -rnd.uniform(5, 10)))
        objs.append(curve(f"{name}Br{b}", bolt_pts(s, end, seed + 11 * b + 3, 8, amp), r * 0.55, m_)[0])
    wins = [(t0 + a_, t0 + b_) for a_, b_, g in FLICK] + list(extra)
    for o in objs: windows(o, wins)
    return objs
# ================= the rod alone does nothing: the strike spills into the roof =================
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
SPILL = mesh_obj("Spill", bm, M_SPILL); SPILL.location = (R_X[0], 0.0, ZR - 0.05)
S2, S3 = C["own"] + 0.1, C["bolt2"]
def spill_s(t):
    for t0, t1 in ((S2, C["typical"]), (S3, C["so"])):
        if t0 <= t < t1: g = 0.2 + 1.0 * ease((t - t0) / 0.6); return (g * 0.7, g, 0.10 * g)
    return (0.01, 0.01, 0.01)
bake_scale(SPILL, spill_s)
for k in range(5):     # red arcs: the current crawls off the rod base into the roof
    rnd = random.Random(70 + k); yy = rnd.choice((-1, 1)) * rnd.uniform(0.8, 2.2); xx = R_X[0] + rnd.uniform(-1.0, 1.4)
    arc = bolt_pts((R_X[0], 0.0, ZR + 0.08), (xx, yy, zr(yy) + 0.04), 80 + k, 6, 0.25)
    o, _ = curve(f"RoofArc{k}", arc, 0.035, M_BOLTR)
    windows(o, [(S2 + 0.05 + 0.04 * k, S2 + 0.5 + 0.04 * k), (S3 + 0.05 + 0.03 * k, S3 + 0.7), (S3 + 1.0, S3 + 1.25), (S3 + 1.6 + 0.05 * k, S3 + 1.85)])
windows(SPILL, [(S2, C["typical"]), (S3, C["so"])])
keyval(F_SPILL, [(0, 0.0), (S2, 0.0), (S2 + 0.1, 1.0), (C["typical"] - 0.3, 0.6), (C["typical"], 0.0), (S3, 0.0), (S3 + 0.1, 1.0), (C["so"] - 0.3, 0.6), (C["so"], 0.0)])

# ================= demo wall (x = 100): a tight corner, the current leaps off into the wall =================
DX = 100.0
box("DemoWall", DX - 3.0, DX + 3.0, 0.25, 0.6, 0.0, 4.6, M_SIDING)
box("DemoGround", DX - 6.0, DX + 6.0, -4.0, 4.0, -0.3, 0.0, M_GRASS)
box("DemoEave", DX - 3.2, DX + 3.2, -0.6, 0.6, 4.6, 4.85, M_ROOF)
DEMO = [(DX - 2.8, 0.12, 3.6), (DX + 0.3, 0.12, 3.6), (DX + 0.3, 0.12, 0.0)]
curve("DemoCable", DEMO, 0.06, M_COPPER)
DC = frac_at(DEMO, 1)
glow_curve("DemoPulse", DEMO, M_GOLD, 0.085, [(C["tight"] - 0.2, C["at"])],
           lambda t: max(0.0, lin((t - C["tight"] + 0.2) / 1.2) * DC - 0.15), lambda t: lin((t - C["tight"] + 0.2) / 1.2) * DC)
SCORCH = mesh_obj("Scorch", (lambda b: (bmesh.ops.create_circle(b, cap_ends=True, segments=32, radius=1.0), b)[1])(bmesh.new()), M_SCORCH)
SCORCH.location = (DX + 0.9, 0.235, 2.9); SCORCH.rotation_euler = (math.radians(90), 0, 0)
bake_scale(SCORCH, lambda t: (0.01,) * 3 if t < C["leap"] else ((0.25 + 0.75 * ease((t - C["leap"]) / 0.8)),) * 3)
for k, end in enumerate([(DX + 0.95, 0.22, 2.95), (DX + 0.6, 0.22, 2.4), (DX + 1.3, 0.22, 3.3)]):
    o, _ = curve(f"DemoSpark{k}", bolt_pts((DX + 0.3, 0.12, 3.6), end, 90 + k, 7, 0.35), 0.045 if k == 0 else 0.03, M_BOLTR)
    windows(o, [(C["leap"] + 0.03 * k, C["leap"] + 0.1 + 0.03 * k), (C["leap"] + 0.16, C["leap"] + 0.32), (C["leap"] + 0.5, C["leap"] + 0.58)])
keyval(F_SCORCH, [(0, 0.0), (C["leap"], 0.0), (C["leap"] + 0.15, 1.0), (C["at"], 0.9)])

STRIKES = []    # (time, target, strength) for the flash lights
def strike(name, target, t0, seed, **kw):
    make_bolt(name, target, t0, seed, **kw); STRIKES.append((t0, Vector(target), kw.get("r", 0.07) / 0.07))
RT1 = (R_X[0], 0.0, ZR + ROD_H)
strike("BoltHook", RT1, S0, 11)
strike("BoltNoRod", (1.0, -1.5, zr(-1.5)), T_HIT1, 23)
strike("BoltAlone", RT1, S2, 31)
strike("BoltTypical", RT1, S3, 37, extra=[(S3 + 0.45, S3 + 0.55), (S3 + 0.7, S3 + 0.78)])
for k, (tg, ri) in enumerate(GHOST): strike(f"BoltGhost{k}", (R_X[ri], 0.0, ZR + ROD_H), tg, 41 + k, r=0.04, branches=1)
strike("BoltStorm", (R_X[1], 0.0, ZR + ROD_H), STORM, 53, r=0.09, branches=3)
SKY_FLASH = [C["storm"] + 0.1, C["storm"] + 0.5, DUR - 0.6]   # cloud flashes with no bolt (the storm builds; the loop)

# ================= soil rings: the current spreads into the earth =================
def ring_obj(name, x):
    pts = [(2.6 * math.cos(a), -0.02, 2.4 * math.sin(a)) for a in [math.pi + math.pi * k / 40 for k in range(41)]]
    o, cu = curve(name, pts, 0.045, M_RING); o.location = (x, YF - 0.06, G_TOP - 0.1); return o
RING_T = [C["ground"] - 0.1, C["spreads"], C["vanishes"] + 0.1]
for x, tag, ts in ((GL_X, "L", RING_T), (GR_X, "R", [RING_T[0], RING_T[2]]), (EG_X, "E", [RING_T[2]])):
    for j in range(3):
        o = ring_obj(f"Ring{tag}{j}", x); starts = [t0 + 0.35 * j for t0 in ts]
        windows(o, [(s, s + 1.3) for s in starts])
        def rs(t, starts=starts):
            for s in starts:
                if s <= t < s + 1.3: u = 0.1 + 0.9 * ease((t - s) / 1.3); return (u, 1.0, u)
            return (0.05, 1.0, 0.05)
        bake_scale(o, rs)

# ================= clouds =================
for k in range(14):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    ph = random.uniform(0, 6)
    for vv in bm.verts: vv.co *= 1.0 + 0.12 * math.sin(3 * vv.co.x + ph) * math.cos(2 * vv.co.y + ph)
    o = mesh_obj(f"Cloud{k}", bm, M_CLOUD); o.data.shade_smooth()
    o.location = (random.uniform(-70, 70), random.uniform(25, 90), random.uniform(32, 44)); o.scale = (random.uniform(12, 22), random.uniform(8, 14), random.uniform(2.5, 4.0))

# ================= lights: moon, lightning flashes, strike point light, fire =================
def flash_level(t):
    v = max([0.0] + [g * flick(t, t0) for t0, _, g in STRIKES])
    return max(v, max([0.0] + [0.6 * flick(t, t0) for t0 in SKY_FLASH]))
FL = [flash_level(t) for t in TS]
moon_d = bpy.data.lights.new("Moon", "SUN"); moon_d.energy = 0.9; moon_d.color = (0.62, 0.72, 1.0); moon_d.angle = math.radians(4)
moon = bpy.data.objects.new("Moon", moon_d); scene.collection.objects.link(moon); moon.rotation_euler = (math.radians(55), math.radians(-10), math.radians(-30))
fsun_d = bpy.data.lights.new("FlashSun", "SUN"); fsun_d.color = (0.82, 0.88, 1.0); fsun_d.angle = math.radians(8)
fsun = bpy.data.objects.new("FlashSun", fsun_d); scene.collection.objects.link(fsun); fsun.rotation_euler = (math.radians(20), math.radians(15), math.radians(-10))
bake_scalar(fsun_d, "energy", [0.0 + 7.0 * v for v in FL])
sp_d = bpy.data.lights.new("StrikeLight", "POINT"); sp_d.color = (0.80, 0.88, 1.0); sp_d.shadow_soft_size = 0.5
spl = bpy.data.objects.new("StrikeLight", sp_d); scene.collection.objects.link(spl)
def last_strike(t):
    past = [s for s in STRIKES if s[0] <= t + 0.01]
    return past[-1] if past else STRIKES[0]
bake_loc(spl, lambda t: tuple(last_strike(t)[1] + Vector((0.0, -1.2, 0.6))))
bake_scalar(sp_d, "energy", [4000.0 * last_strike(t)[2] * flick(t, last_strike(t)[0]) for t in TS])
spark_d = bpy.data.lights.new("SparkLight", "POINT"); spark_d.color = (1.0, 0.4, 0.2)
spk = bpy.data.objects.new("SparkLight", spark_d); scene.collection.objects.link(spk); spk.location = (DX + 0.6, -0.8, 3.2)
bake_scalar(spark_d, "energy", [250.0 * flick(t, C["leap"]) + (25.0 if t > C["leap"] + 0.4 and t < C["at"] else 0.0) for t in TS])
fire_d = bpy.data.lights.new("FireLight", "POINT"); fire_d.color = (1.0, 0.42, 0.10); fire_d.shadow_soft_size = 1.5
fire = bpy.data.objects.new("FireLight", fire_d); scene.collection.objects.link(fire); fire.location = (-0.5, 1.5, 3.6)
bake_scalar(fire_d, "energy", [(900.0 * ease((t - C["wood"]) / 1.5) * (0.75 + 0.25 * math.sin(t * 23.0) * math.sin(t * 7.3))) if C["wood"] <= t < C["this"] else 0.0 for t in TS])
room_d = bpy.data.lights.new("RoomLight", "POINT"); room_d.color = (1.0, 0.78, 0.5); room_d.energy = 350.0; room_d.shadow_soft_size = 1.0
room = bpy.data.objects.new("RoomLight", room_d); scene.collection.objects.link(room); room.location = (0.0, 0.5, 3.8)
glow(B_CLOUD, [(0, 0.0)] + [kv for t0 in [s[0] for s in STRIKES] + SKY_FLASH for kv in [(t0 - 0.02, 0.0), (t0 + 0.02, 0.9), (t0 + 0.24, 0.5), (t0 + 0.4, 0.0)]])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-12.0, -29.0, 4.5), (-1.5, 0.0, 5.0), 28),
    (C["ground"] - 0.2, (-11.0, -26.0, 3.0), (-2.5, -1.0, 3.2), 28),
    (C["a"] - 0.05, (-10.5, -24.5, 2.6), (-3.0, -1.5, 2.8), 28),
    (C["a"], (-12.5, -7.5, 10.2), (-5.6, -0.4, 8.4), 28, "cut"),
    (C["picks"] - 0.05, (-12.8, -8.0, 10.2), (-5.6, -0.4, 8.4), 28),
    (C["road"] + 0.3, (-14.0, -21.0, 4.0), (-5.0, -2.0, 3.6), 26),
    (C["without"], (1.0, -21.0, 4.3), (0.0, 0.0, 3.8), 28, "cut"),
    (C["lightning"] - 0.05, (1.0, -18.5, 4.0), (0.0, 0.0, 3.6), 28),
    (C["this"] - 0.05, (2.0, -29.0, 5.5), (0.0, 0.0, 4.4), 26),
    (C["this"], (-12.5, -7.5, 10.2), (-5.6, -0.4, 8.4), 28, "cut"),
    (C["typical"] - 0.05, (-12.8, -8.0, 10.2), (-5.6, -0.4, 8.4), 28),
    (C["so"] - 0.05, (-15.0, -11.0, 10.0), (-5.6, -0.6, 7.6), 26),
    (C["so"], (-9.0, -11.0, 9.5), (-5.9, -1.2, 7.4), 28, "cut"),
    (C["running"], (-13.0, -15.0, 5.5), (-6.1, -3.6, 4.0), 28),
    (C["no"] - 0.05, (-15.0, -17.0, 2.5), (-6.2, -4.3, 1.6), 28),
    (C["no"], (-9.6, -9.8, 6.1), (-6.12, -4.4, 4.9), 32, "cut"),
    (C["because"] - 0.05, (-9.3, -9.4, 6.0), (-6.12, -4.4, 4.9), 32),
    (C["because"], (DX - 1.2, -8.6, 3.4), (DX - 0.2, 0.2, 2.6), 28, "cut"),
    (C["at"] - 0.05, (DX - 0.6, -7.6, 3.2), (DX + 0.1, 0.2, 2.7), 28),
    (C["at"], (-10.8, -13.6, 0.6), (-6.4, -5.0, -1.2), 30, "cut"),
    (C["one"] - 0.05, (-10.4, -13.0, 0.4), (-6.4, -5.0, -1.3), 30),
    (C["one"], (0.0, -33.0, 3.6), (0.0, 0.0, 2.6), 26, "cut"),
    (C["more"] - 0.05, (0.0, -31.0, 3.6), (0.0, 0.0, 2.6), 26),
    (C["more"], (0.0, -15.5, 12.8), (0.0, 0.0, 8.3), 26, "cut"),
    (C["and"] - 0.05, (0.0, -16.5, 13.2), (0.0, 0.0, 8.3), 26),
    (C["and"], (-1.8, -15.0, 1.4), (-4.8, -3.6, 0.2), 28, "cut"),
    (C["now"] - 0.05, (-2.0, -14.0, 1.2), (-4.9, -3.8, 0.1), 28),
    (C["now"], (-13.0, -32.0, 5.0), (-0.5, 0.0, 4.6), 26, "cut"),
    (C["vanishes"], (-11.5, -28.0, 3.4), (-1.0, -1.0, 3.0), 26),
    (C["does"], (-11.0, -27.0, 3.2), (-1.0, -1.0, 3.0), 26),
    (DUR, (-18.0, -44.0, 8.0), (0.0, 0.0, 4.2), 26),
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
    shake = 0.06 * max([0.0] + [g * max(0.0, 1 - (t - t0) / 0.4) for t0, _, g in STRIKES if t0 <= t])
    cam_loc.append(l0 + Vector((0.02 * math.sin(t * 0.7) + shake * math.sin(t * 61), 0.0, 0.015 * math.sin(t * 0.9 + 1.0) + shake * math.cos(t * 53))))
    cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake_scalar(cam_d, "lens", cam_lens)

world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(-90), 0)
wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
e[0].position = 0.45; e[0].color = (0.10, 0.12, 0.17, 1); e[1].position = 0.75; e[1].color = (0.025, 0.03, 0.05, 1)
wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], bg.inputs["Color"])
keyval(bg.inputs["Strength"], [(0, 1.0)] + [kv for t0 in [s[0] for s in STRIKES] + SKY_FLASH for kv in [(t0 - 0.02, 1.0), (t0 + 0.02, 3.0), (t0 + 0.3, 1.0)]])
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0); fill_d.energy = 1800
bake_scalar(fill_d, "energy", [max(40.0, min(1800.0, 1800.0 * ((cl - ct).length / 45.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
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

# ================= export cues, events and projected anchors for the typography =================
ANCHP = {
    "rod": lambda t: Vector((R_X[0], 0.0, ZR + ROD_H * 0.6)),
    "cable": lambda t: Vector((-6.12, -HY - 0.12, 2.6)),
    "corner": lambda t: Vector((-6.12, -EY, WH - 0.2)),
    "groundrod": lambda t: Vector((GL_X, YF - 0.05, G_TOP - 1.5)),
    "groundrod2": lambda t: Vector((GR_X, YF - 0.05, G_TOP - 1.5)),
    "cable2": lambda t: Vector((6.12, -HY - 0.12, 2.6)),
    "wiring": lambda t: Vector((-2.5, -1.0, WH - 0.4)),
    "pipes": lambda t: Vector((3.6, 1.6, 2.4)),
    "wood": lambda t: Vector((-1.6, HY - 0.42, 2.4)),
    "democorner": lambda t: Vector((DX + 0.3, 0.12, 3.6)),
    "ridgecond": lambda t: Vector((0.0, 0.0, ZR + 0.05)),
    "bond": lambda t: Vector(((GL_X + EG_X) / 2, YF - 0.05, -0.75)),
    "panel": lambda t: Vector((-5.6, -2.5, 1.9)),
    "elecground": lambda t: Vector((EG_X, YF - 0.05, -1.6)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"strikes": [round(s[0], 3) for s in STRIKES], "strike_big": [round(S0, 3), round(STORM, 3)], "ghosts": [round(g[0], 3) for g in GHOST],
          "sky_flash": [round(x, 3) for x in SKY_FLASH], "red_wiring": round(C["wiring"] - 0.25, 3), "red_pipes": round(C["pipes"] - 0.15, 3),
          "fire": RR(C["wood"], C["this"]), "rod_drop": round(C["metal"] + 0.35, 3), "spill": [round(S2, 3), round(S3, 3)],
          "cable_grow": RR(C["thick"], C["house"]), "sharp": RR(C["no"], C["bends"]), "demo_pulse": RR(C["tight"] - 0.2, C["tight"] + 1.0),
          "spark": round(C["leap"], 3), "clamp": round(C["clamps"], 3), "drive_hits": [round(h + 0.12, 3) for h in DRIVE_HITS],
          "rings": [round(x, 3) for x in RING_T], "cable2_grow": RR(T_TWO, T_TWO + 1.3), "gr_drop": round(T_GR + 0.55, 3),
          "rod_pops": [round(x, 3) for x in ROD_POPS], "ridge_grow": RR(C["tied"], C["tied"] + 0.9), "bond_grow": RR(C["bonded"], C["bonded"] + 1.0),
          "system_glow": round(C["system"], 3), "storm_ride": RR(C["rides"], C["vanishes"]), "cta": round(C["does"], 3)}
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
