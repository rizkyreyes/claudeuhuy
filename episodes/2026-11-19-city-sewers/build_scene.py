# City-Sewers-3D: where your flush goes. Build-up format ("THIS IS A TOILET", drafts/build-up-scripts-2026-11-09.md style):
# hook: a flush drops down the stack, rolls along the tilted lateral into the main, then the whole street network carries it downhill ->
# too flat (demo pipe at x = -200): the flow stops, the backup comes up through the basement floor drain -> toilet -> pipe under the floor ->
# lateral leaves the house tilted (exaggerated ~2x) -> under the yard to the sewer main under the street -> every house on the block ties in
# (street set at x = 95..265, longitudinal cut along the main) -> the main tilts, flow carries solids -> manholes at a turn, a slope change,
# a size change; crews reach it (cover lifts) -> small mains join bigger ones -> flat ground: the pipe keeps getting deeper (red ghost),
# digging gets expensive (deep shored trench) -> lift station: wet well fills, float switch, pump, force main up to a higher manhole,
# gravity again -> pull-out to the treatment plant -> CTA over an open manhole.
# Blender Cycles, overcast daylight. Both sets are cut at y = 0 (camera on -y). Soil faces are carved with boolean cutters; "plugs" (thin
# soil boxes with the same position-based materials) hide holes for parts that are built later (lift station, trench).
# Illustrative (1 unit = 1 m): slopes exaggerated 2-10x so a phone can see the tilt, pipes drawn ~2x thick, generic houses, no real place or brand.
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

CUES = [("if", "If"), ("flush", "flush"), ("toilet", "toilet,"), ("gravity", "gravity"), ("work", "work."), ("rolls", "rolls"), ("town", "town"), ("always", "always"),
        ("tilt", "tilt"), ("downhill", "downhill."), ("lay", "Lay"), ("flat", "flat,"), ("waste", "waste"), ("stops", "stops,"), ("backup", "backup"),
        ("lowest", "lowest"), ("drain", "drain"), ("house", "house."), ("this", "This"), ("toilet2", "toilet."), ("flushes", "flushes,"),
        ("drops", "drops"), ("pipe", "pipe"), ("floor", "floor."), ("that", "That"), ("leaves", "leaves"), ("tilted", "tilted,"), ("quarter", "quarter"),
        ("foot", "foot."), ("lateral", "lateral."), ("runs", "runs"), ("yard", "yard"), ("bigger", "bigger"), ("street", "street,"), ("sewer", "sewer"),
        ("main", "main."), ("every", "Every"), ("block", "block"), ("ties", "ties"), ("the", "The"), ("main2", "main"), ("tilts", "tilts"),
        ("flow", "flow"), ("fast", "fast"), ("solids", "solids."), ("every2", "Every"), ("turns", "turns,"), ("slope", "slope,"), ("bigger2", "bigger,"),
        ("manhole", "manhole,"), ("crews", "crews"), ("reach", "reach"), ("downhill2", "Downhill,"), ("small", "small"), ("join", "join"),
        ("bigger3", "bigger"), ("but", "But"), ("catch", "catch."), ("flat2", "flat"), ("tilting", "tilting"), ("deeper", "deeper."), ("too", "Too"),
        ("deep", "deep,"), ("digging", "digging"), ("expensive", "expensive."), ("so", "So"), ("lift", "lift"), ("station", "station."),
        ("sewage", "Sewage"), ("pours", "pours"), ("pit", "pit,"), ("wet", "wet"), ("well", "well."), ("level", "level"), ("rises", "rises,"),
        ("float", "float"), ("starts", "starts"), ("pump", "pump."), ("pushes", "pushes"), ("up", "up"), ("pressure", "pressure"), ("force", "force"),
        ("main3", "main,"), ("higher", "higher"), ("manhole2", "manhole,"), ("gravity2", "gravity"), ("again", "again."), ("america", "America"),
        ("eight", "eight"), ("miles", "miles"), ("sewers", "sewers,"), ("treatment", "treatment"), ("plants", "plants."), ("would", "Would"),
        ("one", "one?"), ("nextup", "Next"), ("runways", "runways.")]
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
CL = coll("CitySewers")
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

# ================= more helpers =================
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
def plen(pts): return sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))
def along(pts, s):
    """Point at arc length s (clamped) on a polyline."""
    P = [Vector(p) for p in pts]; s = max(0.0, s)
    for a_, b_ in zip(P, P[1:]):
        L_ = (b_ - a_).length
        if s <= L_: return a_.lerp(b_, s / L_ if L_ else 0)
        s -= L_
    return P[-1].copy()
def emis(name, rgb, strength=4.0):
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
def prism(name, poly, y0, y1, m_):
    """Polygon in XZ extruded along +y."""
    bm = bmesh.new()
    f0 = [bm.verts.new((x, y0, z)) for x, z in poly]; f1 = [bm.verts.new((x, y1, z)) for x, z in poly]
    bm.faces.new(f0); bm.faces.new(f1[::-1])
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n; bm.faces.new([f0[i], f0[j], f1[j], f1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_)
def seg_rot(p0, p1):
    d = Vector(p1) - Vector(p0); return math.atan2(d.x, d.z), d.length
def half_pipe(name, p0, p1, r_in, r_out, m_, seg=40):
    """Hollow pipe from p0 to p1 (both in the y = 0 plane), cut at y = 0, keeps the y >= 0 half."""
    th, L_ = seg_rot(p0, p1)
    o = lathe(name, tube_prof(r_in, r_out, 0.0, L_), m_, a0=0.0, ang=math.pi, seg=seg, loc=p0, smooth=True)
    o.rotation_euler = (0.0, th, 0.0); return o
def cutter(name, p0, p1, r, ext=0.05):
    th, L_ = seg_rot(p0, p1)
    bm = bmesh.new(); add_cyl(bm, r, L_ + 2 * ext, "Z", (0, 0, L_ / 2), 32)
    o = mesh_obj(name, bm, None, link=False); CUTS.objects.link(o)
    o.location = p0; o.rotation_euler = (0.0, th, 0.0); o.hide_render = True; o.display_type = "WIRE"; return o
def cut_box(name, x0, x1, z0, z1, y0=-1.0, y1=12.0):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1)
    o = mesh_obj(name, bm, None, link=False); CUTS.objects.link(o); o.hide_render = True; o.display_type = "WIRE"; return o
def cut_vcyl(name, x, r, z0, z1, y=0.0):
    bm = bmesh.new(); add_cyl(bm, r, z1 - z0, "Z", (x, y, (z0 + z1) / 2), 40)
    o = mesh_obj(name, bm, None, link=False); CUTS.objects.link(o); o.hide_render = True; o.display_type = "WIRE"; return o
def carve(objs):
    for o in objs:
        md = o.modifiers.new("carve", "BOOLEAN"); md.operation = "DIFFERENCE"; md.operand_type = "COLLECTION"; md.collection = CUTS
        try: md.solver = "EXACT"
        except Exception: pass
def water_band(name, p0, p1, r_in, fill, m_, ywid=None):
    """Flow inside a sloped pipe: a box from the invert up to `fill`, its local +x along the pipe (for the moving texture)."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L_ = d.length
    bm = bmesh.new(); add_box(bm, 0.0, L_, 0.004, ywid or r_in * 0.92, -r_in + 0.01, -r_in + fill)
    o = mesh_obj(name, bm, m_); o.location = p0; o.rotation_euler = (0.0, math.atan2(-d.z, d.x), 0.0); return o
def flow_mat(name, speed_keys, rgb=(0.24, 0.19, 0.10), hi=(0.58, 0.50, 0.33), emit=0.25):
    """Murky water with streaks that move along local +x; speed_keys = [(t, offset)] (linear)."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    off = N.new("ShaderNodeValue")
    prefs.keyframe_new_interpolation_type = "LINEAR"
    for t, v in speed_keys: off.outputs[0].default_value = v; off.outputs[0].keyframe_insert("default_value", frame=F(t))
    prefs.keyframe_new_interpolation_type = "BEZIER"
    sub = N.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; L.new(sep.outputs["X"], sub.inputs[0]); L.new(off.outputs[0], sub.inputs[1])
    cmb = N.new("ShaderNodeCombineXYZ"); mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 0.25
    L.new(sub.outputs[0], mul.inputs[0]); L.new(mul.outputs[0], cmb.inputs[0]); L.new(sep.outputs["Y"], cmb.inputs[1]); L.new(sep.outputs["Z"], cmb.inputs[2])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 4
    L.new(cmb.outputs[0], nz.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.5; mr.inputs[2].default_value = 0.7; L.new(nz.outputs["Fac"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], rgb, hi)
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.12
    L.new(col, b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    return m, b
SPEED = 2.2                                                      # texture offset per second (reads as flowing)
FLOWK = [(0.0, 0.0), (DUR, SPEED * DUR)]

# ================= materials =================
M_GRASS = ground("Grass", (0.05, 0.11, 0.035), (0.09, 0.18, 0.06), 0.8)
M_ASPH, _ = mat("Asphalt", (0.05, 0.05, 0.055), 0.85, noise=8.0)
M_BASE = soil_mat("Gravel", (0.30, 0.28, 0.25), (0.42, 0.40, 0.36), 2.5)
M_TOP = soil_mat("Topsoil", (0.16, 0.10, 0.06), (0.24, 0.16, 0.10), 1.0)
M_CLAY = soil_mat("Clay", (0.30, 0.17, 0.08), (0.40, 0.25, 0.13), 0.7)
M_DEEP = soil_mat("Deep", (0.17, 0.12, 0.08), (0.24, 0.17, 0.11), 0.5)
M_CONC, B_CONC = mat("Concrete", (0.55, 0.55, 0.53), 0.85, noise=3.0, emit_rgb=(0.30, 0.92, 1.0))
M_MAIN, B_MAIN = mat("MainPipe", (0.60, 0.60, 0.58), 0.7, noise=4.0, emit_rgb=(0.30, 0.92, 1.0))
M_PVC, B_PVC = mat("PVC", (0.88, 0.88, 0.86), 0.35, emit_rgb=(1.0, 0.62, 0.12))
M_LAT, B_LAT = mat("LateralPVC", (0.30, 0.52, 0.30), 0.4, emit_rgb=(1.0, 0.62, 0.12))
M_FM, B_FM = mat("ForceMain", (0.16, 0.24, 0.40), 0.4, metallic=0.5, emit_rgb=(0.30, 0.92, 1.0))
M_SIDING, _ = mat("Siding", (0.62, 0.60, 0.55), 0.6, noise=3.0)
M_SIDING2, _ = mat("Siding2", (0.45, 0.52, 0.58), 0.6, noise=3.0)
M_SIDING3, _ = mat("Siding3", (0.70, 0.58, 0.45), 0.6, noise=3.0)
M_ROOF, _ = mat("Roof", (0.10, 0.10, 0.11), 0.85, noise=6.0)
M_WALLIN, _ = mat("WallIn", (0.85, 0.83, 0.78), 0.8)
M_FLOOR, _ = mat("Floor", (0.45, 0.33, 0.22), 0.6, noise=2.0)
M_TILE = tiles("Tile", (0.80, 0.84, 0.86), (0.76, 0.80, 0.83), 4.0)
M_PORC, B_PORC = mat("Porcelain", (0.93, 0.93, 0.92), 0.12, emit_rgb=(1.0, 0.62, 0.12))
M_BOWLW, B_BOWLW = mat("BowlWater", (0.35, 0.65, 0.75), 0.05, emit_rgb=(0.30, 0.92, 1.0))
M_DARK, _ = mat("Mouth", (0.015, 0.015, 0.015), 0.9)
M_IRON, B_IRON = mat("Iron", (0.10, 0.10, 0.11), 0.5, metallic=0.9, emit_rgb=(0.30, 0.92, 1.0))
M_WOOD, _ = mat("Shoring", (0.55, 0.40, 0.24), 0.7, noise=4.0)
M_TRUNK, _ = mat("Trunk", (0.12, 0.08, 0.05), 0.9)
M_LEAF, _ = mat("Leaf", (0.06, 0.15, 0.05), 0.9)
M_WIN, B_WIN = mat("Window", (0.08, 0.10, 0.12), 0.1, emit_rgb=(1.0, 0.80, 0.55)); B_WIN.inputs["Emission Strength"].default_value = 0.8
M_TANKW, _ = mat("TankWater", (0.12, 0.22, 0.20), 0.1)
M_STUDIO, _ = mat("Studio", (0.05, 0.055, 0.065), 0.9)
M_PUMP, B_PUMP = mat("Pump", (0.20, 0.36, 0.60), 0.35, metallic=0.6, emit_rgb=(0.30, 0.92, 1.0))
M_FLOATM, B_FLOAT = mat("Float", (0.95, 0.70, 0.10), 0.3, emit_rgb=(1.0, 0.62, 0.12))
M_FLOW, B_FLOW = flow_mat("Flow", FLOWK)
M_BACK, B_BACK = flow_mat("Backup", [(0.0, 0.0), (DUR, 0.6 * DUR)], rgb=(0.20, 0.14, 0.06), hi=(0.40, 0.28, 0.12), emit=0.15)
T_STOP = C["stops"]
M_DFLOW, B_DFLOW = flow_mat("DemoFlow", [(0.0, 0.0), (C["flat"], SPEED * C["flat"]), (T_STOP, SPEED * C["flat"] + 0.9), (DUR, SPEED * C["flat"] + 0.9)])
M_GOLD, S_GOLD = emis("RouteGold", (1.0, 0.62, 0.12), 5.0)
M_CYAN, S_CYAN = emis("Cyan", (0.30, 0.92, 1.0), 6.0)
M_REDG, S_REDG = emis("RedGlow", (1.0, 0.25, 0.15), 5.0)
M_JET, S_JET = emis("Jet", (0.70, 0.55, 0.30), 1.6)
M_SOLID, _ = mat("Solids", (0.22, 0.13, 0.06), 0.6)
M_SLUG, S_SLUG = emis("Slug", (1.0, 0.70, 0.25), 8.0)
M_GHOST, F_GHOST, _, _ = ghost_mat("GhostRed", (1.0, 0.25, 0.15), 2.5)

CUTS = bpy.data.collections.new("Cutters"); scene.collection.children.link(CUTS)

def soil_layers(tag, x0, x1, y0, y1, zb, top_mat=None, top_split=None):
    """Grass/asphalt top, gravel/topsoil, clay, deep. top_split = [(xa, xb, mat)] for the top layer."""
    objs = []
    for xa, xb, m_ in (top_split or [(x0, x1, top_mat or M_GRASS)]):
        objs.append(box(f"{tag}Top{xa:.0f}", xa, xb, y0, y1, -0.3, 0.0, m_))
    objs.append(box(f"{tag}Soil", x0, x1, y0, y1, -1.6, -0.3, M_TOP))
    objs.append(box(f"{tag}Clay", x0, x1, y0, y1, -6.0, -1.6, M_CLAY))
    objs.append(box(f"{tag}Deep", x0, x1, y0, y1, zb, -6.0, M_DEEP))
    return objs
def plug(tag, x0, x1, z0, wins, top_split):
    """Thin soil patch on the cut face that hides a carved hole until the part is built."""
    ps = []
    for xa, xb, m_ in top_split:
        a_, b_ = max(xa, x0), min(xb, x1)
        if a_ < b_: ps.append(box(f"{tag}PTop{a_:.0f}", a_, b_, -0.004, 0.25, -0.3, 0.0, m_))
    for (za, zb), m_ in (((-1.6, -0.3), M_TOP), ((-6.0, -1.6), M_CLAY), ((-40, -6.0), M_DEEP)):
        a_, b_ = max(za, z0), zb
        if a_ < b_: ps.append(box(f"{tag}P{zb:.0f}", x0, x1, -0.004, 0.25, a_, b_, m_))
    for p in ps: windows(p, wins)
    return ps

# =====================================================================================
# SET A: one house, cut along its sewer line (x = -30..30): toilet -> stack -> building drain -> lateral -> main (end-on) under the street
# =====================================================================================
HX0, HX1 = -12.3, -1.7                          # house outer walls
FL = 0.6                                        # ground floor top
BS = -2.6                                       # basement slab top
TX, TY = -5.0, 1.25                             # toilet
SX = -5.6                                       # stack x
DRX = -9.5                                      # basement floor drain x
BD0, BD1 = (-9.5, 0.0, -3.05), (-1.7, 0.0, -3.30)   # building drain (under the slab)
LAT0, LAT1 = (-1.7, 0.0, -3.30), (15.45, 0.0, -3.98)  # lateral (slope exaggerated ~2x)
MX, MZ, MR_IN, MR_OUT = 16.0, -4.35, 0.45, 0.56   # street main, seen end-on (axis along +y)
STREET = (11.0, 22.0)
TOPA = [(-60.0, STREET[0], M_GRASS), (STREET[0], STREET[1], M_ASPH), (STREET[1], 38.0, M_GRASS)]
SOIL_A = soil_layers("A", -60.0, 38.0, 0.0, 30.0, -500.0, top_split=TOPA)
cut_box("CutBasement", HX0, HX1, BS - 0.3, 0.2)
cutter("CutStack", (SX, 0, BS - 0.3), (SX, 0, -3.05), 0.17)
cutter("CutBD", BD0, BD1, 0.17)
cutter("CutLat", LAT0, (LAT1[0] + 0.3, 0, LAT1[2] - 0.01), 0.20)
bm = bmesh.new(); add_cyl(bm, MR_OUT + 0.04, 40.0, "Y", (MX, 10.0, MZ), 40)
o = mesh_obj("CutMainA", bm, None, link=False); CUTS.objects.link(o); o.hide_render = True
cut_vcyl("CutDrainTrap", DRX, 0.14, -3.05, BS)
# house shell
box("FoundL", HX0, HX0 + 0.3, 0.0, 9.0, BS - 0.3, FL, M_CONC)
box("FoundR", HX1 - 0.3, HX1, 0.0, 9.0, BS - 0.3, FL, M_CONC)
box("BSlab", HX0, HX1, 0.0, 9.0, BS - 0.3, BS, M_CONC)
box("BBack", HX0, HX1, 8.7, 9.0, BS, FL, M_CONC)
box("GFloor", HX0 + 0.3, HX1 - 0.3, 0.0, 9.0, FL - 0.3, FL, M_FLOOR)
box("WallL", HX0, HX0 + 0.25, 0.0, 9.0, FL, 3.6, M_SIDING)
box("WallR", HX1 - 0.25, HX1, 0.0, 9.0, FL, 3.6, M_SIDING)
box("WallBack", HX0, HX1, 8.75, 9.0, FL, 3.6, M_WALLIN)
box("Ceiling", HX0, HX1, 0.0, 9.0, 3.6, 3.85, M_WALLIN)
prism("Roof", [(HX0 - 0.6, 3.6), (HX1 + 0.6, 3.6), ((HX0 + HX1) / 2, 6.6)], -0.3, 9.3, M_ROOF)
box("BathWall", -6.6, -3.4, 2.05, 2.25, FL, 3.6, M_TILE)
box("BathSide", -3.6, -3.4, 0.0, 2.25, FL, 3.6, M_TILE)
box("Win1", -10.4, -8.6, 8.7, 8.76, 1.5, 2.9, M_WIN)
# toilet (faces the camera)
lathe("Bowl", [(0.0, FL), (0.16, FL), (0.15, FL + 0.18), (0.22, FL + 0.36), (0.20, FL + 0.40), (0.0, FL + 0.40)], M_PORC, ang=2 * math.pi, seg=40, loc=(TX, TY - 0.05, 0))
box("Seat", TX - 0.22, TX + 0.22, TY - 0.30, TY + 0.22, FL + 0.40, FL + 0.44, M_PORC)
box("Tank", TX - 0.24, TX + 0.24, TY + 0.40, TY + 0.62, FL + 0.42, FL + 0.95, M_PORC)
box("TankLid", TX - 0.26, TX + 0.26, TY + 0.38, TY + 0.64, FL + 0.95, FL + 1.0, M_PORC)
bowlw = cyl("BowlWater", 0.17, 0.02, "Z", (TX, TY - 0.05, FL + 0.37), M_BOWLW)
box("Lever", TX - 0.22, TX - 0.10, TY + 0.36, TY + 0.40, FL + 0.86, FL + 0.89, M_IRON)
# drain-waste pipes (white PVC in the house, green PVC lateral outside)
curve("ClosetBend", [(TX, TY - 0.05, FL - 0.05), (TX, TY - 0.05, 0.15), (SX + 0.1, 0.5, 0.0), (SX, 0.12, -0.1)], 0.09, M_PVC)
half_pipe("Stack", (SX, 0, 0.1), (SX, 0, -3.05), 0.10, 0.14, M_PVC)
half_pipe("BuildingDrain", BD0, BD1, 0.12, 0.16, M_PVC)
half_pipe("Lateral", LAT0, LAT1, 0.13, 0.18, M_LAT)
half_pipe("DrainTrap", (DRX, 0, BS + 0.02), (DRX, 0, -3.0), 0.08, 0.11, M_PVC)
box("Grate", DRX - 0.16, DRX + 0.16, 0.0, 0.32, BS, BS + 0.02, M_IRON)
# main under the street, end-on: a full ring running back along +y
mainA = lathe("MainA", tube_prof(MR_IN, MR_OUT, 0.0, 30.0), M_MAIN, ang=2 * math.pi, seg=48)
mainA.rotation_euler = (-math.pi / 2, 0, 0); mainA.location = (MX, 0.0, MZ)
bm = bmesh.new(); add_cyl(bm, MR_IN - 0.01, 30.0, "Y", (MX, 15.0, MZ), 40)
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, MZ - MR_IN + 0.32), plane_no=(0, 0, 1), clear_outer=True)
bmesh.ops.edgeloop_fill(bm, edges=[e for e in bm.edges if len(e.link_faces) < 2]) if any(len(e.link_faces) < 2 for e in bm.edges) else None
mesh_obj("MainAWater", bm, M_FLOW)
box("Curb", STREET[0] - 0.25, STREET[0], 0.0, 30.0, -0.3, 0.15, M_CONC)
box("Curb2", STREET[1], STREET[1] + 0.25, 0.0, 30.0, -0.3, 0.15, M_CONC)
for k, (x, y) in enumerate([(4.0, 14.0), (26.0, 12.0), (-20.0, 16.0), (8.0, 24.0)]):
    full_cyl(f"TrunkA{k}", 0.22, x, y, 0.0, 3.0, M_TRUNK, seg=10)
    o = bpy.data.objects.new(f"LeafA{k}", None)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=2.0); bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, 4.2))
    mesh_obj(f"CrownA{k}", bm, M_LEAF)
box("FarA", -200, 38, 30.0, 400.0, -0.3, 0.0, M_GRASS)
carve(SOIL_A)

# the flush route in set A (a glowing slug rides it; the gold route line grows along it)
ROUTE_A = [(TX, TY - 0.05, FL + 0.2), (TX, TY - 0.05, 0.15), (SX, 0.12, -0.1), (SX, 0.05, -2.95), (SX + 0.2, 0.05, BD0[2] - (SX - BD0[0]) / (BD1[0] - BD0[0]) * (BD0[2] - BD1[2]) - 0.05),
           (BD1[0], 0.05, BD1[2] - 0.05), (LAT1[0], 0.05, LAT1[2] - 0.05), (MX, 0.3, MZ - 0.15)]
LRA = plen(ROUTE_A)
def slug_path(t0, t1):
    """arc length along ROUTE_A between t0 and t1 (fast drop in the stack, then rolling)."""
    def s(t):
        if t <= t0: return -1.0
        if t >= t1: return LRA + 1.0
        p = (t - t0) / (t1 - t0); return LRA * (p ** 1.4)
    return s
SLUGS = [(C["flush"] + 0.25, C["rolls"] - 0.25), (C["drops"] - 0.2, C["sewer"] + 0.2)]
slug = bpy.data.objects.new("SlugA", None); CL.objects.link(slug)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=0.13); slugm = mesh_obj("SlugAMesh", bm, M_SLUG)
def slug_pos(t):
    for t0, t1 in SLUGS:
        if t0 - 0.05 <= t <= t1 + 0.3:
            s = slug_path(t0, t1)(t)
            if 0 <= s <= LRA: return tuple(along(ROUTE_A, s))
    return (0.0, -50.0, -50.0)
bake_loc(slugm, slug_pos)
routeA, routeA_cu = curve("RouteA", [p for p in ROUTE_A[2:]], 0.08, M_GOLD)
def routeA_end(t):
    if C["drops"] <= t < C["every"]:
        return lin((t - C["drops"]) / (C["sewer"] - C["drops"]))
    return 0.0
reveal(routeA_cu, lambda t: 0.0, routeA_end)
# tilt helper: a dashed cyan level line from the house to the street + the drop shown at the far end
lvl, lvl_cu = curve("LevelLine", [(LAT0[0], -0.08, LAT0[2] - 0.0), (LAT1[0], -0.08, LAT0[2])], 0.025, M_CYAN)
reveal(lvl_cu, lambda t: 0.0, lambda t: lin((t - C["tilted"]) / 0.7) if C["tilted"] <= t < C["runs"] else 0.0)
drop_o, drop_cu = curve("DropBar", [(LAT1[0] - 0.4, -0.08, LAT0[2]), (LAT1[0] - 0.4, -0.08, LAT1[2] + 0.02)], 0.03, M_GOLD)
reveal(drop_cu, lambda t: 0.0, lambda t: lin((t - C["quarter"]) / 0.5) if C["quarter"] <= t < C["runs"] else 0.0)
glow(B_LAT, [(0, 0.0), *pulse(C["lateral"] - 0.1, 2.5, hold=0.8, down=0.6)])
glow(B_MAIN, [(0, 0.0), *pulse(C["main"] - 0.1, 1.2, hold=0.6, down=0.5)])
glow(B_PORC, [(0, 0.0), *pulse(C["toilet2"] - 0.1, 0.6, hold=0.5, down=0.5)])
glow(B_BOWLW, [(0, 0.0), *pulse(C["flush"], 4.0, hold=0.3, down=0.5), *pulse(C["flushes"], 4.0, hold=0.4, down=0.6)])
glow(B_PVC, [(0, 0.0), *pulse(C["pipe"] - 0.1, 1.5, hold=0.6, down=0.5)])
# backup in the basement: the building drain + stack fill up, sewage comes up the floor drain and spreads on the slab
T_BU = C["backup"]
bdfull = half_pipe("BDBackup", BD0, BD1, 0.0, 0.118, M_BACK, seg=24)
latfull = half_pipe("LatBackup", LAT0, LAT1, 0.0, 0.128, M_BACK, seg=24)
trapfull = half_pipe("TrapBackup", (DRX, 0, BS + 0.02), (DRX, 0, -3.0), 0.0, 0.078, M_BACK, seg=16)
for o in (bdfull, latfull, trapfull): windows(o, [(T_BU - 0.1, C["this"])])
bm = bmesh.new(); add_box(bm, -0.5, 0.5, 0.0, 1.0, 0.0, 1.0); pool = mesh_obj("BasementPool", bm, M_BACK)
pool.location = (DRX, 0.0, BS + 0.002)
bake_scale(pool, lambda t: (0.3 + 9.0 * ease((t - C["drain"]) / 1.4), 8.6 * ease((t - C["drain"]) / 0.5), 0.16 * ease((t - C["drain"]) / 0.5)) if C["drain"] <= t < C["this"] else (0.0, 0.0, 0.0))
bake_loc(pool, lambda t: (min(DRX + 3.8 * ease((t - C["drain"]) / 1.4), DRX + 3.8), 0.0, BS + 0.002))
bm = bmesh.new(); add_cyl(bm, 0.07, 1.0, "Z", (0, 0, 0.5), 16); spurt = mesh_obj("Spurt", bm, M_BACK); spurt.location = (DRX, 0.15, BS)
bake_scale(spurt, lambda t: (1.0, 1.0, 0.45 * ease((t - C["lowest"]) / 0.3) * (0.7 + 0.3 * math.sin(t * 17))) if C["lowest"] <= t < C["this"] else (0, 0, 0))

# =====================================================================================
# DEMO: one pipe on a dark studio backdrop (x = -200): tilted, then laid flat -> the flow stops
# =====================================================================================
DXD = -200.0
for o in (box("StudioFloor", DXD - 30, DXD + 30, -10, 30, -2.6, -2.5, M_STUDIO), box("StudioBack", DXD - 30, DXD + 30, 6.0, 6.2, -2.6, 20.0, M_STUDIO)):
    windows(o, [(C["lay"] - 0.2, C["backup"] + 0.2)])
dpiv = empty("DemoPivot", (DXD, 0.0, 0.0))
dp = lathe("DemoPipe", tube_prof(0.50, 0.62, -5.0, 5.0), M_LAT, a0=0.0, ang=math.pi, seg=48)
dp.rotation_euler = (0, math.pi / 2, 0); dp.location = (0, 0, 0); par(dp, dpiv)
bm = bmesh.new(); add_box(bm, -5.0, 5.0, 0.004, 0.46, -0.49, -0.49 + 0.30); dwat = mesh_obj("DemoWater", bm, M_DFLOW); par(dwat, dpiv)
T_FLAT = C["flat"]
bake_fn(dpiv, "rotation_euler", 1, lambda t: math.radians(6.0) * (1 - ease((t - T_FLAT) / 0.55)))
dred, dred_cu = curve("DemoRed", [(-5.0, -0.05, -0.62), (5.0, -0.05, -0.62)], 0.05, M_REDG); par(dred, dpiv)
reveal(dred_cu, lambda t: 0.0, lambda t: lin((t - T_STOP) / 0.6))
for k in range(9):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.09 + 0.04 * (k % 3))
    bmesh.ops.scale(bm, verts=bm.verts, vec=(1.5, 1.0, 0.8))
    so = mesh_obj(f"DemoSolid{k}", bm, M_SOLID); par(so, dpiv)
    x0 = -5.0 + k * 1.15; yk = 0.12 + 0.07 * (k % 4)
    def dsx(t, x0=x0):
        tt = min(t, T_FLAT) + 0.25 * max(0.0, min(t, T_STOP) - T_FLAT)              # slows after "flat", stops at "stops"
        return ((x0 + 2.4 * tt) + 5.0) % 10.0 - 5.0
    bake_loc(so, lambda t, dsx=dsx, yk=yk: (dsx(t), yk, -0.49 + 0.09 + (0.0 if t < T_STOP else -0.03 * ease((t - T_STOP) / 0.5))))

# =====================================================================================
# SET B: a street, cut along its sewer main (x = 95..265)
# =====================================================================================
S1 = ((100.0, 0, -2.6), (130.0, 0, -3.5)); S2 = ((130.0, 0, -3.5), (150.0, 0, -4.7)); S3 = ((150.0, 0, -4.85), (186.6, 0, -7.6))
S4 = ((200.0, 0, -2.4), (238.0, 0, -3.6))
R1 = (0.45, 0.56); R3 = (0.66, 0.80)
WX, WR_IN, WR_OUT, WZ0 = 189.0, 2.2, 2.5, -10.5        # wet well
FMZ = -1.6                                             # force main height
MH = {"M0": (100.0, -2.6), "M1": (130.0, -3.5), "M2": (150.0, -4.75), "M3": (200.0, -2.4)}
TOPB = [(40.0, 3000.0, M_ASPH)]
SOIL_B = soil_layers("B", 40.0, 3000.0, 0.0, 7.0, -2000.0, top_split=TOPB) + soil_layers("Bb", 40.0, 3000.0, 7.0, 60.0, -2000.0)
for nm, (p0, p1), r in (("S1", S1, R1), ("S2", S2, R1), ("S3", S3, R3), ("S4", S4, R1)):
    cutter("Cut" + nm, p0, p1, r[1] + 0.03)
for nm, (x, z) in MH.items(): cut_vcyl("Cut" + nm, x, 0.78, z, 0.3)
cut_vcyl("CutWell", WX, WR_OUT + 0.03, WZ0 - 0.3, 0.3)
cutter("CutFM", (WX, 0, FMZ), (200.0, 0, FMZ), 0.36)
cut_box("CutTrench", 172.0, 182.0, -5.6, 0.3, y1=6.5)
cutter("CutPlant", (238.0, 0, -3.6), (246.0, 0, -3.6), 0.6)
carve(SOIL_B)
PLUG_TOP = TOPB
plug("Well", 186.45, 199.2, WZ0 - 0.4, [(0, C["lift"])], PLUG_TOP)
plug("S4", 199.2, 247.0, -5.0, [(0, C["lift"])], PLUG_TOP)
plug("Trench", 172.0, 182.0, -5.6, [(0, C["digging"]), (C["so"], DUR)], PLUG_TOP)
box("FarB", 0, 500, 60.0, 600.0, -0.3, 0.0, M_GRASS)
# mains (half pipes) and their flow
PIPES_B = {}
for nm, (p0, p1), r in (("S1", S1, R1), ("S2", S2, R1), ("S3", S3, R3), ("S4", S4, R1)):
    PIPES_B[nm] = half_pipe("Main" + nm, p0, p1, r[0], r[1], M_MAIN, seg=40)
    w = water_band("Flow" + nm, p0, p1, r[0], r[0] * 0.75, M_FLOW)
    if nm == "S4": windows(w, [(C["gravity2"] - 0.6, DUR)]); windows(PIPES_B[nm], [(C["lift"], DUR)])
# manholes: half shafts, ring + cover at the street, ladder rungs on the back wall
COVERS = {}
for nm, (x, z) in MH.items():
    crown = z + (R3[1] if nm == "M2" else R1[1]) - 0.15
    sh = lathe("Shaft" + nm, tube_prof(0.6, 0.75, crown, 0.0), M_CONC, a0=0.0, ang=math.pi, seg=40, loc=(x, 0, 0))
    for k in range(int((0.0 - crown) / 0.4) - 1):
        box(f"Rung{nm}{k}", x - 0.2, x + 0.2, 0.5, 0.6, -0.5 - k * 0.4, -0.46 - k * 0.4, M_IRON)
    cv = cyl("Cover" + nm, 0.62, 0.07, "Z", (0, 0, 0.0), M_IRON, seg=40)
    cv.location = (x, 0.0, 0.035); COVERS[nm] = cv
    if nm == "M3": windows(sh, [(C["lift"], DUR)]); windows(cv, [(C["lift"], DUR)])
# M0: the upstream main turns here (it comes in from behind, along +y)
box("M0Mouth", 99.55, 100.45, 0.47, 0.5, -3.0, -2.25, M_DARK)
lathe("M0Elbow", tube_prof(R1[0], R1[1], 0.5, 14.0), M_MAIN, ang=2 * math.pi, seg=32).rotation_euler = (-math.pi / 2, 0, 0)
bpy.data.objects["M0Elbow"].location = (100.0, 0.0, -2.6)
# house laterals: dark mouths on the back wall of S1 (the pipes run back to the houses), jets when they flush
JET_T = [C["ties"] - 0.35, C["ties"], C["ties"] + 0.35]
HOUSES_X = [104.0, 114.0, 124.0]
def zS(seg, x):
    (x0, _, z0), (x1, _, z1) = seg; return z0 + (z1 - z0) * (x - x0) / (x1 - x0)
JETS = []
for k, hx in enumerate(HOUSES_X):
    zc = zS(S1, hx) + 0.18
    cyl(f"LatMouth{k}", 0.15, 0.04, "Y", (hx, 0.44, zc), M_DARK, seg=24)
    bm = bmesh.new(); add_cyl(bm, 0.10, 1.0, "Y", (0, -0.5, 0), 16); j = mesh_obj(f"Jet{k}", bm, M_JET); j.location = (hx, 0.44, zc)
    t0 = JET_T[k]
    bake_scale(j, lambda t, t0=t0: (1.0, 0.38 * ease((t - t0) / 0.25) * (1 - ease((t - t0 - 1.1) / 0.4)), 1.0) if t0 <= t < t0 + 1.6 else (0, 0, 0))
    JETS.append(j)
    # house on the far side of the street
    hm = [M_SIDING, M_SIDING2, M_SIDING3][k]
    box(f"House{k}", hx - 3.5, hx + 3.5, 10.0, 18.0, 0.0, 3.2, hm)
    prism(f"HouseRoof{k}", [(hx - 4.0, 3.2), (hx + 4.0, 3.2), (hx, 5.4)], 9.6, 18.4, M_ROOF)
    box(f"HouseWin{k}", hx - 1.8, hx - 0.4, 9.95, 10.0, 1.2, 2.3, M_WIN); box(f"HouseDoor{k}", hx + 0.6, hx + 1.6, 9.95, 10.0, 0.0, 2.1, M_ROOF)
    lat_o, lat_c = curve(f"LatGhost{k}", [(hx, 10.0, -0.9), (hx, 0.6, zc)], 0.06, M_GOLD)
    reveal(lat_c, lambda t: 0.0, lambda t, t0=t0: lin((t - (C["every"] + 0.2 * k)) / 0.7) if C["every"] <= t < C["the"] else 0.0)
for k, hx in enumerate([136.0, 146.0, 160.0, 172.0]):
    hm = [M_SIDING2, M_SIDING3, M_SIDING, M_SIDING2][k]
    box(f"HouseB{k}", hx - 3.5, hx + 3.5, 10.0, 18.0, 0.0, 3.2, hm)
    prism(f"HouseBRoof{k}", [(hx - 4.0, 3.2), (hx + 4.0, 3.2), (hx, 5.4)], 9.6, 18.4, M_ROOF)
    box(f"HouseBWin{k}", hx - 1.8, hx - 0.4, 9.95, 10.0, 1.2, 2.3, M_WIN)
for k, (x, y) in enumerate([(109, 22), (119, 24), (141, 21), (155, 25), (166, 22), (130, 30), (180, 26), (210, 20), (226, 24)]):
    full_cyl(f"TrunkB{k}", 0.25, x, y, 0.0, 3.2, M_TRUNK, seg=10)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=2.3); bmesh.ops.translate(bm, verts=bm.verts, vec=(x, y, 4.6))
    mesh_obj(f"CrownB{k}", bm, M_LEAF)
# M2: a side main joins from behind and the pipe gets bigger after it
cyl("SideMouth", 0.36, 0.04, "Y", (150.0, R3[0] - 0.02, -4.55), M_DARK, seg=28)
bm = bmesh.new(); add_cyl(bm, 0.22, 1.0, "Y", (0, -0.5, 0), 16); sidejet = mesh_obj("SideJet", bm, M_JET); sidejet.location = (150.0, R3[0] - 0.02, -4.55)
bake_scale(sidejet, lambda t: (1.0, 0.5 * ease((t - C["join"]) / 0.3), 1.0) if C["join"] <= t < C["but"] else (0, 0, 0))
# solids riding the flow S1 -> S2 -> S3 (and S4 after the lift station)
PATH_B = [(S1[0][0], 0.2, S1[0][2] - R1[0] + 0.22), (S1[1][0], 0.2, S1[1][2] - R1[0] + 0.22), (S2[1][0], 0.2, S2[1][2] - R1[0] + 0.22),
          (S3[0][0], 0.2, S3[0][2] - R3[0] + 0.26), (S3[1][0] - 0.3, 0.2, S3[1][2] - R3[0] + 0.26)]
PATH_4 = [(S4[0][0] + 0.8, 0.2, S4[0][2] - R1[0] + 0.22), (S4[1][0], 0.2, S4[1][2] - R1[0] + 0.22)]
LB, L4 = plen(PATH_B), plen(PATH_4)
for k in range(26):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.09 + 0.035 * (k % 3)); bmesh.ops.scale(bm, verts=bm.verts, vec=(1.6, 1.0, 0.8))
    so = mesh_obj(f"Solid{k}", bm, M_SOLID); s0 = k * LB / 26.0; yk = 0.08 + 0.05 * (k % 5)
    def sp(t, s0=s0, yk=yk):
        p = along(PATH_B, (s0 + 3.2 * t) % LB); return (p.x, yk, p.z)
    bake_loc(so, sp)
for k in range(8):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.1); bmesh.ops.scale(bm, verts=bm.verts, vec=(1.6, 1.0, 0.8))
    so = mesh_obj(f"Solid4_{k}", bm, M_SOLID); s0 = k * L4 / 8.0; yk = 0.1 + 0.06 * (k % 3)
    def sp4(t, s0=s0, yk=yk):
        if t < C["gravity2"] - 0.5: return (0.0, -60.0, -60.0)
        p = along(PATH_4, (s0 + 3.2 * t) % L4); return (p.x, yk, p.z)
    bake_loc(so, sp4)
# slope arrows (cyan) above the mains: "always tilt downhill" (hook) and "the main tilts too"
def slope_arrow(name, seg, wins, off=0.9):
    (x0, _, z0), (x1, _, z1) = seg
    a = Vector((x0 + (x1 - x0) * 0.2, -0.1, z0 + (z1 - z0) * 0.2 + off)); b = Vector((x0 + (x1 - x0) * 0.8, -0.1, z0 + (z1 - z0) * 0.8 + off))
    bm = bmesh.new(); add_arrow(bm, (0, 0), ((b - a).x, (b - a).z), (b - a).length, 0.9)
    o = mesh_obj(name, bm, M_CYAN); o.location = (a.x, -0.12, a.z); windows(o, wins); return o
ARROWS = [slope_arrow("ArrS1", S1, [(C["tilt"] - 0.1, C["lay"]), (C["tilts"], C["every2"])]),
          slope_arrow("ArrS2", S2, [(C["tilt"], C["lay"]), (C["tilts"] + 0.2, C["every2"])]),
          slope_arrow("ArrS3", S3, [(C["tilt"] + 0.1, C["lay"])], off=1.2)]
# manhole highlights (cyan rings around each shaft on "manhole")
for nm, (x, z) in MH.items():
    if nm == "M3": continue
    crown = z + (R3[1] if nm == "M2" else R1[1]) - 0.15
    ho, hc = curve("MHGlow" + nm, [(x - 0.8, -0.06, crown), (x - 0.8, -0.06, 0.05), (x + 0.8, -0.06, 0.05), (x + 0.8, -0.06, crown)], 0.05, M_CYAN)
    tm = {"M0": C["turns"], "M1": C["slope"], "M2": C["bigger2"]}[nm]
    reveal(hc, lambda t: 0.0, lambda t, tm=tm: lin((t - tm) / 0.5) if tm <= t < C["downhill2"] else (lin((t - C["manhole"]) / 0.4) if C["manhole"] <= t < C["downhill2"] else 0.0))
# M1 cover lifts and slides on "crews"
bake_loc(COVERS["M1"], lambda t: (130.0 + 1.2 * ease((t - C["crews"] - 0.25) / 0.6), 0.0 - 0.0, 0.035 + 0.25 * ease((t - C["crews"]) / 0.3) * (1 - ease((t - C["crews"] - 0.55) / 0.3))) if t < C["but"] else
         ((130.0 + 1.2, 0.0, 0.035) if C["would"] <= t else (130.0, 0.0, 0.035)))
# bigger-pipe glow at M2 (size change, small mains join bigger ones)
s3glow, s3c = curve("S3Glow", [(S3[0][0], -0.06, S3[0][2] - R3[1] - 0.05), (S3[0][0] + 14.0, -0.06, zS(S3, S3[0][0] + 14.0) - R3[1] - 0.05)], 0.05, M_CYAN)
reveal(s3c, lambda t: 0.0, lambda t: lin((t - C["bigger3"] + 0.2) / 0.6) if C["bigger3"] - 0.2 <= t < C["but"] else (lin((t - C["bigger2"]) / 0.4) if C["bigger2"] <= t < C["manhole"] else 0.0))
# "keeps getting deeper": the main keeps going down (red ghost) past where the lift station will be, depth bar grows
GH = [(186.6, -0.15, -7.6), (226.0, -0.15, -10.6)]
gho, ghc = curve("DeepGhost", GH, 0.62, M_GHOST)
reveal(ghc, lambda t: 0.0, lambda t: lin((t - C["tilting"]) / 1.3) if C["tilting"] <= t < C["so"] else 0.0)
keyval(F_GHOST, [(0, 0.0), (C["tilting"] - 0.1, 0.0), (C["tilting"], 0.75), (C["so"] - 0.05, 0.75), (C["so"], 0.0)])
dep_o, dep_c = curve("DepthBar", [(226.0, -0.2, 0.0), (226.0, -0.2, -10.6)], 0.08, M_CYAN)
reveal(dep_c, lambda t: 0.0, lambda t: lin((t - C["deeper"] + 0.5) / 0.9) if C["deeper"] - 0.5 <= t < C["so"] else 0.0)
srf_o, srf_c = curve("FlatLine", [(96.0, -0.2, 0.05), (230.0, -0.2, 0.05)], 0.07, M_CYAN)
reveal(srf_c, lambda t: 0.0, lambda t: lin((t - C["flat2"]) / 0.8) if C["flat2"] <= t < C["so"] else 0.0)
# the deep trench: shoring + spoil pile, only while "digging gets very expensive"
TR_W = [(C["digging"], C["so"])]
for k in range(8):
    windows(box(f"ShoreL{k}", 172.0, 172.15, 0.0, 6.0, -5.6 + k * 0.7, -5.0 + k * 0.7, M_WOOD), TR_W)
    windows(box(f"ShoreR{k}", 181.85, 182.0, 0.0, 6.0, -5.6 + k * 0.7, -5.0 + k * 0.7, M_WOOD), TR_W)
for k in range(3):
    windows(box(f"Strut{k}", 172.15, 181.85, 1.0, 1.25, -4.8 + k * 1.8, -4.6 + k * 1.8, M_IRON), TR_W)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0); spoil = mesh_obj("Spoil", bm, M_CLAY)
spoil.location = (165.5, 4.0, 0.0)
bake_scale(spoil, lambda t: (4.0, 3.0, 3.2 * ease((t - C["digging"]) / 0.8)) if C["digging"] <= t < C["so"] else (0, 0, 0))
trench_red, trc = curve("TrenchRed", [(172.0, -0.1, 0.1), (172.0, -0.1, -5.6), (182.0, -0.1, -5.6), (182.0, -0.1, 0.1)], 0.07, M_REDG)
reveal(trc, lambda t: 0.0, lambda t: lin((t - C["expensive"] + 0.4) / 0.6) if C["expensive"] - 0.4 <= t < C["so"] else 0.0)

# ---------- lift station ----------
T_LIFT = C["lift"]
LS = [(T_LIFT, DUR)]
well = lathe("WetWell", tube_prof(WR_IN, WR_OUT, WZ0, 0.25), M_CONC, a0=0.0, ang=math.pi, seg=48, loc=(WX, 0, 0))
wfloor = half_pipe("WellFloor", (WX, 0, WZ0 - 0.35), (WX, 0, WZ0), 0.0, WR_OUT, M_CONC)
hut = box("Hut", WX - 2.8, WX + 2.8, 0.0, 6.0, 0.25, 3.2, M_SIDING2)
hutr = prism("HutRoof", [(WX - 3.1, 3.2), (WX + 3.1, 3.2), (WX, 4.4)], -0.2, 6.2, M_ROOF)
for o in (well, wfloor, hut, hutr): windows(o, LS)
bake_fn(hut, "location", 2, lambda t: drop(t, T_LIFT, h=10.0, d=0.5)); bake_fn(hutr, "location", 2, lambda t: drop(t, T_LIFT, h=10.0, d=0.5))
# sewage in the well: level rises from "pours" to "float", drops while pumping
def level(t):
    lo, hi = WZ0 + 0.4, -6.2
    if t < C["pours"]: return lo
    if t < C["starts"] + 0.3: return lo + (hi - lo) * ease((t - C["pours"]) / (C["starts"] + 0.3 - C["pours"]))
    return hi - (hi - (lo + 1.2)) * ease((t - C["starts"] - 0.3) / 4.5)
wwat = lathe("WellWater", [(0.0, 0.0), (WR_IN - 0.02, 0.0), (WR_IN - 0.02, 1.0), (0.0, 1.0)], M_FLOW, a0=0.0, ang=math.pi, seg=40, loc=(WX, 0, WZ0))
windows(wwat, LS); bake_fn(wwat, "scale", 2, lambda t: max(0.01, level(t) - WZ0))
injet = cyl("InJet", 0.25, 1.0, "Z", (0, 0, -0.5), M_JET, seg=16); injet.location = (WX - WR_IN + 0.3, 0.3, S3[1][2] - 0.3)
bake_scale(injet, lambda t: (1.0, 1.0, max(0.0, (S3[1][2] - 0.3 - level(t)))) if C["pours"] <= t < C["america"] else (0, 0, 0))
# pump on the floor, discharge riser, check valve, force main to M3
pump = box("Pump", WX + 0.2, WX + 1.4, 0.6, 1.6, WZ0, WZ0 + 1.1, M_PUMP)
riser = half_pipe("Riser", (WX + 1.0, 0, WZ0 + 1.1), (WX + 1.0, 0, FMZ), 0.22, 0.30, M_FM, seg=24)
fm = half_pipe("ForceMain", (WX + 1.0, 0, FMZ), (200.0 - 0.6, 0, FMZ), 0.22, 0.30, M_FM, seg=24)
for o in (pump, riser, fm): windows(o, LS)
imp = cyl("Impeller", 0.35, 0.08, "Y", (0, 0, 0), M_IRON, seg=6); imp.location = (WX + 0.8, 0.55, WZ0 + 0.55); windows(imp, LS)
bake_fn(imp, "rotation_euler", 1, lambda t: 0.0 if t < C["starts"] else 18.0 * (t - C["starts"]))
glow(B_PUMP, [(0, 0.0), (C["starts"] - 0.01, 0.0), (C["starts"] + 0.2, 2.5), (C["pushes"] + 0.5, 2.5), (C["higher"], 0.6), (C["america"], 0.0)])
# float switch: cable from the top, the float tilts up with the level
fpiv = empty("FloatPivot", (WX - 0.9, 0.5, -4.0)); windows(fpiv, LS)
fc_o, fc_c = curve("FloatCable", [(0, 0, 0), (0, 0, -1.4)], 0.025, M_IRON); par(fc_o, fpiv); windows(fc_o, LS)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.28); bmesh.ops.scale(bm, verts=bm.verts, vec=(1.0, 1.0, 1.5))
bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, -1.6)); flt = mesh_obj("Float", bm, M_FLOATM); par(flt, fpiv); windows(flt, LS)
cable_hang = curve("FloatHanger", [(WX - 0.9, 0.5, -4.0), (WX - 0.9, 0.5, -0.2)], 0.025, M_IRON)[0]; windows(cable_hang, LS)
bake_fn(fpiv, "rotation_euler", 1, lambda t: -math.radians(80) * ease((level(t) + 6.2 - 1.2) / 1.2) if level(t) > -7.4 else 0.0)
glow(B_FLOAT, [(0, 0.0), *pulse(C["float"], 3.0, hold=0.5, down=0.5)])
# force main: cyan pulses ride up the riser and along to M3
FM_PTS = [(WX + 1.0, -0.06, WZ0 + 1.1), (WX + 1.0, -0.06, FMZ), (199.4, -0.06, FMZ)]
for k in range(3):
    po, pc = curve(f"FMPulse{k}", FM_PTS, 0.16, M_CYAN)
    t0 = C["pushes"] + 0.9 * k
    reveal(pc, lambda t, t0=t0: lin((t - t0 - 0.35) / 1.6), lambda t, t0=t0: lin((t - t0) / 1.6) if t0 <= t < t0 + 2.2 else 0.0)
glow(B_FM, [(0, 0.0), *pulse(C["force"] - 0.1, 1.2, hold=0.9, down=0.5)])
# gravity again: a gold arrow along S4
arr4 = slope_arrow("ArrS4", S4, [(C["gravity2"], C["america"] + 1.5)])
arr4.data.materials[0] = M_GOLD
# treatment plant (generic): headworks building at the end of S4, round clarifiers + basins behind
box("Headworks", 238.0, 246.0, 0.0, 8.0, -4.6, 3.4, M_CONC)
box("HeadworksIn", 238.4, 245.6, 0.0, 7.6, -4.2, 3.0, M_DARK)
for k, (x, y, r) in enumerate([(254.0, 12.0, 6.0), (268.0, 14.0, 6.0), (282.0, 12.0, 6.0)]):
    lathe(f"Clarifier{k}", tube_prof(r - 0.3, r, -0.3, 1.4), M_CONC, ang=2 * math.pi, seg=48, loc=(x, y, 0))
    full_cyl(f"ClarW{k}", r - 0.3, x, y, 0.0, 1.2, M_TANKW, seg=48)
for k in range(3):
    box(f"Basin{k}", 250.0 + k * 13, 261.0 + k * 13, 24.0, 40.0, -0.3, 1.2, M_CONC)
    box(f"BasinW{k}", 250.4 + k * 13, 260.6 + k * 13, 24.4, 39.6, -0.3, 1.1, M_TANKW)
glow(B_CONC, [(0, 0.0), *pulse(C["treatment"], 0.6, hold=0.8, down=0.6)])

# ================= lights + world =================
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.2; sun_d.color = (1.0, 0.96, 0.9); sun_d.angle = math.radians(8)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
room_d = bpy.data.lights.new("RoomLight", "POINT"); room_d.color = (1.0, 0.85, 0.65); room_d.energy = 250.0; room_d.shadow_soft_size = 1.0
room = bpy.data.objects.new("RoomLight", room_d); scene.collection.objects.link(room); room.location = (-7.0, 1.5, 3.0)
bas_d = bpy.data.lights.new("BasementLight", "POINT"); bas_d.color = (1.0, 0.9, 0.75); bas_d.energy = 160.0; bas_d.shadow_soft_size = 0.8
bas = bpy.data.objects.new("BasementLight", bas_d); scene.collection.objects.link(bas); bas.location = (-7.0, 2.0, -0.4)
st_d = bpy.data.lights.new("StudioKey", "AREA"); st_d.size = 6; st_d.energy = 1500; st_d.color = (1.0, 0.95, 0.9)
st = bpy.data.objects.new("StudioKey", st_d); scene.collection.objects.link(st); st.location = (DXD - 3, -6, 6); st.rotation_euler = (math.radians(45), 0, math.radians(-20))
ww_d = bpy.data.lights.new("WellLight", "POINT"); ww_d.energy = 300.0; ww_d.color = (0.9, 0.95, 1.0); ww_d.shadow_soft_size = 1.0
wwl = bpy.data.objects.new("WellLight", ww_d); scene.collection.objects.link(wwl); wwl.location = (WX - 0.5, 0.9, -5.0)
bake_scalar(ww_d, "energy", [300.0 if T_LIFT <= t else 0.0 for t in TS])
mh_d = bpy.data.lights.new("ShaftLight", "POINT"); mh_d.energy = 0.0; mh_d.color = (1.0, 0.95, 0.85); mh_d.shadow_soft_size = 0.4
mhl = bpy.data.objects.new("ShaftLight", mh_d); scene.collection.objects.link(mhl); mhl.location = (130.0, 0.45, -1.6)
bake_scalar(mh_d, "energy", [60.0 if (C["crews"] <= t < C["downhill2"] or t >= C["would"]) else 0.0 for t in TS])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-5.0, -10.5, -0.6), (-5.4, 0.0, -1.5), 26),
    (C["gravity"], (-3.5, -10.5, -0.9), (-4.0, 0.0, -1.9), 26),
    (C["work"], (6.0, -11.5, -1.0), (6.5, 0.0, -2.6), 26),
    (C["rolls"] - 0.05, (13.0, -9.5, -1.6), (14.5, 0.0, -3.4), 26),
    (C["rolls"], (98.0, -24.0, 4.0), (132.0, 0.0, -4.5), 24, "cut"),
    (C["lay"] - 0.05, (104.0, -22.0, 3.0), (138.0, 0.0, -5.0), 24),
    (C["lay"], (DXD - 1.0, -14.0, 1.6), (DXD, 0.0, -0.3), 30, "cut"),
    (C["backup"] - 0.05, (DXD + 0.5, -12.5, 1.2), (DXD, 0.0, -0.3), 30),
    (C["backup"], (-6.0, -8.0, -1.4), (-6.5, 0.0, -2.5), 26, "cut"),
    (C["this"] - 0.05, (-7.0, -6.5, -1.7), (-7.8, 0.0, -2.6), 26),
    (C["this"], (TX + 0.2, -3.6, 1.7), (TX, TY - 0.3, 0.9), 30, "cut"),
    (C["drops"], (TX + 0.0, -4.4, 1.0), (TX - 0.3, 0.6, 0.2), 28),
    (C["that"] - 0.05, (SX, -7.5, -1.6), (SX, 0.0, -2.0), 26),
    (C["that"], (-1.0, -7.5, -2.4), (-0.5, 0.0, -3.3), 26, "cut"),
    (C["quarter"], (2.5, -9.0, -2.2), (3.5, 0.0, -3.4), 26),
    (C["runs"], (5.0, -10.0, -1.8), (6.0, 0.0, -3.3), 26),
    (C["street"], (14.5, -8.5, -1.2), (15.5, 0.0, -3.0), 26),
    (C["every"] - 0.05, (16.5, -6.5, -2.4), (16.0, 0.0, -4.0), 26),
    (C["every"], (106.0, -14.0, 0.8), (114.0, 0.0, -2.6), 26, "cut"),
    (C["the"] - 0.05, (108.0, -13.0, 0.4), (115.0, 0.0, -2.8), 26),
    (C["the"], (118.0, -19.0, 1.5), (126.0, 0.0, -3.2), 26, "cut"),
    (C["every2"] - 0.05, (122.0, -16.0, 0.5), (128.0, 0.0, -3.4), 26),
    (C["every2"], (96.5, -9.5, -0.6), (100.8, 0.0, -2.2), 26, "cut"),
    (C["slope"] - 0.05, (97.0, -9.0, -0.8), (101.0, 0.0, -2.3), 26),
    (C["slope"], (126.0, -10.0, -1.0), (130.5, 0.0, -2.9), 26, "cut"),
    (C["bigger2"] - 0.05, (126.5, -9.5, -1.2), (130.5, 0.0, -3.0), 26),
    (C["bigger2"], (145.5, -10.5, -1.5), (150.5, 0.0, -3.8), 26, "cut"),
    (C["manhole"] - 0.05, (146.0, -10.0, -1.6), (150.5, 0.0, -3.8), 26),
    (C["manhole"] + 0.05, (112.0, -36.0, 6.0), (126.0, 0.0, -2.6), 26),
    (C["crews"], (126.5, -8.5, 1.2), (130.0, 0.0, -0.8), 26),
    (C["downhill2"] - 0.05, (127.0, -8.0, 0.8), (130.0, 0.0, -1.0), 26),
    (C["downhill2"], (143.0, -12.0, -1.0), (151.0, 0.0, -4.6), 26, "cut"),
    (C["but"] - 0.05, (141.0, -17.0, 0.0), (152.0, 0.0, -4.8), 26),
    (C["but"], (122.0, -42.0, 6.0), (170.0, 0.0, -6.0), 24, "cut"),
    (C["too"] - 0.05, (128.0, -46.0, 5.0), (180.0, 0.0, -6.5), 24),
    (C["digging"] - 0.05, (162.0, -26.0, 4.0), (177.0, 0.0, -3.5), 24),
    (C["so"] - 0.05, (163.0, -24.0, 3.0), (177.0, 0.0, -3.5), 24),
    (C["so"], (180.0, -26.0, 3.0), (189.5, 0.0, -4.0), 24, "cut"),
    (C["sewage"], (183.0, -17.0, -2.0), (189.0, 0.0, -6.0), 24),
    (C["float"] - 0.3, (184.5, -12.5, -4.5), (189.0, 0.0, -7.0), 24),
    (C["pushes"], (185.0, -14.0, -3.5), (190.0, 0.0, -6.0), 24),
    (C["pressure"], (188.0, -20.0, 0.0), (194.0, 0.0, -3.8), 24),
    (C["higher"], (194.0, -18.0, 1.0), (199.0, 0.0, -2.6), 24),
    (C["gravity2"], (200.0, -20.0, 1.5), (210.0, 0.0, -2.8), 24),
    (C["america"] - 0.05, (203.0, -20.0, 1.5), (213.0, 0.0, -2.9), 24),
    (C["america"], (178.0, -52.0, 9.0), (212.0, 0.0, -4.0), 24, "cut"),
    (C["would"] - 0.05, (172.0, -66.0, 12.0), (212.0, 0.0, -3.5), 24),
    (C["would"], (130.0, -3.0, 3.0), (130.0, 0.4, -2.9), 24, "cut"),
    (DUR, (130.0, -2.6, 1.6), (130.0, 0.3, -2.9), 24),
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
    cam_loc.append(l0 + Vector((0.02 * math.sin(t * 0.7), 0.0, 0.015 * math.sin(t * 0.9 + 1.0))))
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
e[0].position = 0.45; e[0].color = (0.55, 0.62, 0.70, 1); e[1].position = 0.80; e[1].color = (0.20, 0.30, 0.45, 1)
wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.9
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0); fill_d.energy = 1500
bake_scalar(fill_d, "energy", [max(60.0, min(2500.0, 1500.0 * ((cl - ct).length / 45.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (6, 8, 0)
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
def fpos(t):
    return Vector((WX - 0.9, 0.5, -4.0)) + Matrix.Rotation(fpiv.rotation_euler.y, 3, "Y") @ Vector((0, 0, -1.6))
ANCHP = {
    "toilet": lambda t: Vector((TX, TY, FL + 0.9)),
    "stack": lambda t: Vector((SX, 0.0, -1.3)),
    "floordrain": lambda t: Vector((DRX, 0.0, BS + 0.05)),
    "lateral": lambda t: Vector((6.0, 0.0, -3.55)),
    "maina": lambda t: Vector((MX, 0.0, MZ)),
    "street": lambda t: Vector((16.5, 0.0, 0.0)),
    "m0": lambda t: Vector((100.0, 0.0, -1.0)),
    "m1": lambda t: Vector((130.0, 0.0, -1.2)),
    "m2": lambda t: Vector((150.0, 0.0, -1.6)),
    "s1": lambda t: Vector((116.0, 0.0, zS(S1, 116.0))),
    "s3": lambda t: Vector((160.0, 0.0, zS(S3, 160.0))),
    "trench": lambda t: Vector((177.0, 0.0, -2.5)),
    "deepend": lambda t: Vector((226.0, 0.0, -10.6)),
    "wetwell": lambda t: Vector((WX - 1.2, 0.0, -8.6)),
    "float": fpos,
    "pump": lambda t: Vector((WX + 0.8, 0.6, WZ0 + 0.6)),
    "forcemain": lambda t: Vector((195.0, 0.0, FMZ)),
    "m3": lambda t: Vector((200.0, 0.0, -1.0)),
    "plant": lambda t: Vector((242.0, 0.0, 3.4)),
    "demo": lambda t: Vector((DXD, 0.0, -0.6)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"slugs": [RR(a, b) for a, b in SLUGS], "flushes": [round(C["flush"], 3), round(C["flushes"], 3)], "demo_flat": RR(T_FLAT, T_FLAT + 0.55),
          "demo_stop": round(T_STOP, 3), "backup_spurt": round(C["lowest"], 3), "pool": RR(C["drain"], C["drain"] + 1.4),
          "level_line": round(C["tilted"], 3), "drop_bar": round(C["quarter"], 3), "jets": [round(x, 3) for x in JET_T],
          "mh_glows": [round(C["turns"], 3), round(C["slope"], 3), round(C["bigger2"], 3), round(C["manhole"], 3)],
          "cover_lift": RR(C["crews"], C["crews"] + 0.85), "side_jet": round(C["join"], 3), "ghost": RR(C["tilting"], C["tilting"] + 1.3),
          "dig": RR(C["digging"], C["digging"] + 0.8), "lift_drop": RR(T_LIFT, T_LIFT + 0.5), "pour": round(C["pours"], 3),
          "float": round(C["float"], 3), "pump_start": round(C["starts"], 3), "fm_pulses": [round(C["pushes"] + 0.9 * k, 3) for k in range(3)],
          "gravity_again": round(C["gravity2"], 3), "plant": round(C["treatment"], 3), "cta": round(C["would"], 3)}
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
