# Canal-Locks-3D: how the Panama Canal lifts ships with no pumps (gravity-fed lock chambers). Blender Cycles, real-world setting
# (daylight sky, sea on the left, lake on the right). Every cue is a word in the VO.
# One set: a flight of three lock chambers (Atlantic side, like the Gatun flight) seen in long section. The near side wall is cut away
# down to a low plinth whose cut face shows the main culvert (the 18 ft tunnel) running the whole length from the lake intake to the sea
# outlet, with risers up to holes in the chamber floor. Far wall with miter-gate leaves (one leaf per gate, the near leaf is cut away),
# electric locomotives ("mules") on the far wall, a container ship (no brand, no people), a second ship for the "going down" beat and
# three water-saving side basins for the newer-locks beat.
# Illustrative scale: 1 unit ~ 10 ft for widths (chamber 11 = 110 ft, culvert 1.8 = 18 ft, ship beam 10.6 -> ~2 ft to spare per side),
# chambers shortened (40 instead of 100 units) and the steps drawn 5 units (50 ft) high instead of ~28 ft so they read in a vertical frame.
# A near-wall cover (the uncut upper near wall) is in place for the hook, sinks away on "cut", and comes back for the top-down "2 ft" shot.
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
DUR = round(WORDS[-1]["end"] + VO + 0.75, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(8)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("panama", "panama"), ("lifts", "lifts"), ("giant", "giant"), ("ships", "ships"), ("eighty", "eighty-five"), ("uphill", "uphill"),
        ("zero", "zero"), ("pumps", "pumps"), ("lets", "let's"), ("cut", "cut"), ("middle", "middle"), ("gatun", "gatun"), ("lake", "lake"),
        ("eighty2", "eighty-five"), ("sea", "sea"), ("atlantic", "atlantic"), ("climb", "climb"), ("three", "three"), ("giant2", "giant"),
        ("steps", "steps"), ("each", "each"), ("chamber", "chamber"), ("thousand", "thousand"), ("long", "long"), ("ship", "ship"),
        ("sails", "sails"), ("gates", "gates"), ("shut", "shut"), ("inside", "inside"), ("walls", "walls"), ("tunnels", "tunnels"),
        ("eighteen", "eighteen"), ("wide", "wide"), ("lake2", "lake"), ("higher", "higher"), ("valves", "valves"), ("open", "open"),
        ("gravity", "gravity"), ("down", "down"), ("tunnels2", "tunnels"), ("up", "up"), ("holes", "holes"), ("floor", "floor"),
        ("water", "water"), ("rises", "rises"), ("ship2", "ship"), ("rises2", "rises"), ("eight", "eight"), ("minutes", "minutes"),
        ("chamber2", "chamber"), ("matches", "matches"), ("next", "next"), ("gates2", "gates"), ("open2", "open"), ("ship3", "ship"),
        ("moves", "moves"), ("electric", "electric"), ("mules", "mules"), ("hold", "hold"), ("cables", "cables"), ("because", "because"),
        ("biggest", "biggest"), ("two", "two"), ("spare", "spare"), ("side", "side"), ("three2", "three"), ("later", "later"),
        ("floating", "floating"), ("lake3", "lake"), ("going", "going"), ("valves2", "valves"), ("run", "run"), ("sea2", "sea"),
        ("but", "but"), ("never", "never"), ("back", "back"), ("every", "every"), ("crosses", "crosses"), ("fifty", "fifty-two"),
        ("million", "million"), ("gallons", "gallons"), ("fresh", "fresh"), ("thats", "that's"), ("newer", "newer"), ("basins", "basins"),
        ("save", "save"), ("sixty", "sixty"), ("would", "would"), ("steer", "steer"), ("two2", "two"), ("tell", "tell"), ("next2", "next"),
        ("steel", "steel"), ("sink", "sink"), ("follow", "follow")]
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
CL = coll("Locks")

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

# ================= materials (outdoor) =================
def concrete(name, rgb=(0.50, 0.49, 0.46), scale=0.35):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    g = N.new("ShaderNodeNewGeometry"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 8
    L.new(g.outputs["Position"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].color = (rgb[0] * 0.78, rgb[1] * 0.78, rgb[2] * 0.78, 1); e[1].color = (rgb[0] * 1.08, rgb[1] * 1.08, rgb[2] * 1.06, 1)
    L.new(n.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.85
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def ground(name, rgb1, rgb2, scale=0.05):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    g = N.new("ShaderNodeNewGeometry"); n = N.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 10
    L.new(g.outputs["Position"], n.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements; e[0].color = (*rgb1, 1); e[1].color = (*rgb2, 1)
    L.new(n.outputs["Fac"], cr.inputs[0]); L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def water_sec(name, glow_rgb=(0.30, 0.92, 1.0)):
    """Section water: clear tinted transmission (IOR 1.0) + a blue volume, emission keyable for glows."""
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.55, 0.85, 0.95, 1); b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.0; b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["Emission Color"].default_value = (*glow_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.18, 0.52, 0.66, 1); va.inputs["Density"].default_value = 0.05
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.25, 0.62, 0.78, 1); vs.inputs["Density"].default_value = 0.02
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Volume"])
    lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.85, 0.95, 1.0, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.3
    n.inputs["Detail"].default_value = 6; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m, b
M_CON = concrete("Concrete"); M_CON2 = concrete("ConcreteCut", (0.62, 0.60, 0.56), 0.5)
M_CULV = mat("CulvertIn", (0.12, 0.13, 0.14), 0.9)[0]
M_GRASS = ground("Grass", (0.10, 0.20, 0.05), (0.20, 0.33, 0.09))
M_BED = ground("Bed", (0.22, 0.18, 0.13), (0.33, 0.27, 0.19), 0.12)
M_BASE = ground("SectionBase", (0.16, 0.11, 0.07), (0.24, 0.17, 0.11), 0.08)
M_STEEL, B_STEEL = mat("GateSteel", (0.16, 0.19, 0.22), 0.6, 0.25, emit_rgb=(0.98, 0.74, 0.27))
M_VALVE, B_VALVE = mat("Valve", (0.90, 0.62, 0.12), 0.35, 0.3, emit_rgb=(0.98, 0.74, 0.27))
M_HULL = mat("Hull", (0.04, 0.10, 0.22), 0.4, 0.2)[0]
M_HULLR = mat("HullRed", (0.42, 0.05, 0.04), 0.5)[0]
M_HULL2 = mat("Hull2", (0.30, 0.04, 0.05), 0.4, 0.2)[0]
M_WHITE = mat("White", (0.85, 0.85, 0.82), 0.4)[0]
M_WIN = mat("Window", (0.02, 0.03, 0.04), 0.1)[0]
CONT = [mat(f"Box{i}", c, 0.55)[0] for i, c in enumerate([(0.55, 0.12, 0.06), (0.06, 0.22, 0.45), (0.65, 0.48, 0.10), (0.12, 0.35, 0.20), (0.45, 0.45, 0.47), (0.60, 0.25, 0.08)])]
M_MULE = mat("Mule", (0.62, 0.64, 0.66), 0.35, 0.7)[0]
M_MULE2 = mat("MuleBand", (0.85, 0.55, 0.08), 0.4)[0]
M_RAIL = mat("Rail", (0.25, 0.25, 0.26), 0.3, 0.9)[0]
M_CABLE = mat("Cable", (0.05, 0.05, 0.05), 0.5, emit_rgb=(0.98, 0.74, 0.27))[0]
M_CYAN, B_CYAN = mat("Cyan", (0.05, 0.4, 0.5), 0.3, emit_rgb=(0.30, 0.92, 1.0)); B_CYAN.inputs["Emission Strength"].default_value = 6.0
M_GOLD, B_GOLD = mat("GoldLine", (0.6, 0.4, 0.05), 0.3, emit_rgb=(0.98, 0.74, 0.27)); B_GOLD.inputs["Emission Strength"].default_value = 6.0
M_DROP, B_DROP = mat("Drop", (0.3, 0.8, 1.0), 0.1, emit_rgb=(0.30, 0.92, 1.0)); B_DROP.inputs["Emission Strength"].default_value = 4.0
M_HOLE = mat("Hole", (0.01, 0.01, 0.012), 0.9)[0]
WM = [water_sec(f"Water{k}") for k in range(3)]
M_LAKE, B_LAKE = water_sec("LakeWater"); M_SEA, B_SEA = water_sec("SeaWater")
M_CW, B_CW = water_sec("CulvertWater")
M_BW, B_BW = water_sec("BasinWater")
def surf_mat(name, rgb=(0.05, 0.22, 0.30)):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = 0.08
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.15
    n.inputs["Detail"].default_value = 8; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.2; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m

# ================= layout =================
NL = 3; LX = 40.0                         # chambers: x 40k .. 40k+40
YI = 5.5; YW_ = 9.0                       # inner half width (110 ft), wall face to outside of wall
STEP = 5.0
FL = [-8.0 + STEP * k for k in range(NL)]                 # chamber floors
WT = [STEP * (k + 1) + 2.5 for k in range(NL)]            # wall tops
LAKE = STEP * NL                                           # 15
BASE = -18.0
ZC0, ZC1 = -16.4, -14.6                                    # culvert slot (1.8 = 18 ft)
YR = -6.5                                                  # back of the culvert recess
XG = [0.0, 40.0, 80.0, 120.0]                              # gates
GT = 0.8                                                   # gate leaf thickness
X_IN, X_OUT = 123.0, -1.0                                  # lake intake shaft, sea outlet
X_FV, X_DV = 117.0, 3.0                                    # fill valve, drain valve
RISERS = [8.0, 16.0, 24.0, 32.0]
# section base (dark), far ground, sea and lake beds
box("SectionBase", -260, 330, -60, 260, BASE - 2, BASE, M_BASE)
for k in range(NL):
    x0, x1 = LX * k, LX * (k + 1)
    box(f"Floor{k}", x0, x1, -YI, YI, BASE, FL[k], M_CON2)
    box(f"FarWall{k}", x0, x1, YI, YW_, BASE, WT[k], M_CON)
    box(f"Apron{k}", x0, x1, YW_, 22.0, BASE, WT[k] - 0.2, M_CON)
    box(f"Land{k}", x0, x1, 22.0, 240.0, BASE, WT[k] - 0.6, M_GRASS)
    # near plinth (cut face at y = -9): under the culvert, over it, and the back of the recess
    box(f"PlinthLo{k}", x0, x1, -YW_, -YI, BASE, ZC0, M_CON2)
    box(f"PlinthHi{k}", x0, x1, -YW_, -YI, ZC1, FL[k] + 1.0, M_CON2)
    box(f"PlinthBack{k}", x0, x1, YR, -YI, ZC0, ZC1, M_CULV)
# lake end: plinth with the intake shaft, lake bed, lake water, lake banks
box("LakePlinthLo", 120, 128, -YW_, -YI, BASE, ZC0, M_CON2)
box("LakePlinthA", 120, X_IN - 0.9, -YW_, -YI, ZC1, FL[2] + 1.0, M_CON2)
box("LakePlinthB", X_IN + 0.9, 128, -YW_, -YI, ZC0, FL[2] + 1.0, M_CON2)
box("LakeShaftBack", X_IN - 0.9, X_IN + 0.9, YR, -YI, ZC1, FL[2] + 1.0, M_CULV)
box("LakeBed", 120, 330, -YW_, 240, BASE, FL[2], M_BED)
box("LakeBank", 120, 330, 60.0, 240, BASE, LAKE + 1.5, M_GRASS)
LAKE_W = box("LakeWater", 120 + GT / 2, 330, -YW_, 60.0, FL[2], LAKE, M_LAKE)
# sea end: sea bed (deep approach channel), sea water, far shore
box("SeaBed", -260, 0, -YW_, 240, BASE, -12.0, M_BED)
box("SeaShore", -260, 0, 40.0, 240, BASE, 2.0, M_GRASS)
SEA_W = box("SeaWater", -260, -GT / 2, -YW_, 40.0, -12.0, 0.0, M_SEA)
box("OutletPlinthLo", -4, 0, -YW_, -YI, BASE, ZC0, M_CON2)
# floor holes in chamber 1 (dark discs) and riser recesses in the plinth from the culvert up to the floor
for i, x in enumerate([4 + 4 * j for j in range(9)]):
    for j, y in enumerate((-3.0, 0.0, 3.0)):
        cyl(f"Hole{i}_{j}", 0.42, 0.04, "Z", (x, y, FL[0] + 0.01), M_HOLE, seg=16)
for i, x in enumerate(RISERS):
    box(f"Riser{i}", x - 0.45, x + 0.45, YR + 0.01, -YI, ZC1 - 0.01, FL[0] + 0.02, M_CULV)

# ================= timing (video seconds) =================
T_CV0, T_CV1 = C["cut"] + 0.05, C["cut"] + 0.95                 # near-wall cover sinks away
T_SAIL0, T_SAIL1 = C["ship"] - 0.15, C["shut"] - 0.2            # ship into chamber 1
T_G0C0, T_G0C1 = C["shut"] - 0.05, C["shut"] + 0.7              # gate 0 closes
T_FV0, T_FV1 = C["valves"], C["open"] + 0.3                     # fill valve lifts
T_FLOW0 = C["open"] + 0.1                                       # water leaves the lake
T_FILL0, T_FILL1 = C["up"] + 0.2, C["matches"] + 0.35           # chamber 1 rises 0 -> 5
T_G1O0, T_G1O1 = C["gates2"] - 0.05, C["open2"] + 0.35          # gate 1 opens
T_MV0, T_MV1 = C["ship3"] - 0.1, C["electric"] + 1.2            # ship into chamber 2
T_G1C0, T_G1C1 = T_MV1 + 0.1, T_MV1 + 0.8
T_FILL2_0 = T_G1C1 + 0.2                                          # chamber 2 rises 5 -> 10 (in the background)
T_FILL2_1 = C["three2"] - 0.5
T_G2O0, T_G2O1 = C["three2"] - 0.45, C["three2"] - 0.1
T_MV2_0, T_MV2_1 = C["three2"] - 0.15, C["three2"] + 0.5         # ship into chamber 3
T_G2C0, T_G2C1 = T_MV2_1, T_MV2_1 + 0.3
T_FILL3_0, T_FILL3_1 = T_MV2_1 + 0.3, C["floating"] - 0.15       # chamber 3 rises 10 -> 15
T_G3O0, T_G3O1 = C["floating"] - 0.15, C["floating"] + 0.2
T_OUT0, T_OUT1 = C["floating"] + 0.1, C["going"] - 0.25          # ship out onto the lake
T_DOWN = C["going"] - 0.2                                       # hard cut: ship 2 in chamber 1, level 5
T_DV0, T_DV1 = C["valves2"] - 0.05, C["valves2"] + 0.5           # drain valve lifts
T_DRAIN0, T_DRAIN1 = C["run"], C["back"] + 0.4                   # chamber 1 drains 5 -> 0
T_G0O0, T_G0O1 = T_DRAIN1 + 0.1, T_DRAIN1 + 0.8                  # gate 0 opens for ship 2
T_S2_0, T_S2_1 = T_G0O1 + 0.2, C["thats"] + 0.2                  # ship 2 sails out to sea
T_BAS0 = C["basins"] - 0.15                                      # side basins pop up
T_HOOK1 = C["lets"] - 0.06                                       # end of the hook

def level0(t):
    if t < T_HOOK1: return 0.0
    if t < T_DOWN: return PW([(T_FILL0, 0.0), (T_FILL1, STEP)])(t)
    return PW([(T_DRAIN0, STEP), (T_DRAIN1, 0.0)])(t)
def level1(t):
    if t < T_HOOK1: return STEP
    if t >= T_BAS0: return PW([(C["save"] - 0.2, 2 * STEP), (C["would"] - 0.3, 2 * STEP - 1.6)])(t)   # side basins take part of it
    return PW([(T_FILL2_0, STEP), (T_FILL2_1, 2 * STEP)])(t)
def level2(t):
    if t < T_HOOK1: return PW([(0.35, 2 * STEP), (C["pumps"] + 0.2, 3 * STEP)])(t)
    return PW([(T_FILL3_0, 2 * STEP), (T_FILL3_1, 3 * STEP)])(t)
LEVELS = [level0, level1, level2]
def level_at(x, t):
    if x < 0: return 0.0
    if x >= 120: return LAKE
    return LEVELS[int(x // LX)](t)

# chamber water: unit-height box from the floor, scaled to the level
W_OBJ = []
for k in range(NL):
    bm = bmesh.new(); add_box(bm, LX * k + GT / 2, LX * (k + 1) - GT / 2, -YI, YI - 0.02, 0, 1)
    o = mesh_obj(f"ChamberWater{k}", bm, WM[k][0]); o.location = (0, 0, FL[k]); W_OBJ.append(o)
    bake_fn(o, "scale", 2, (lambda kk: (lambda t: max(0.02, LEVELS[kk](t) - FL[kk])))(k))

# gates: two miter leaves per gate, hinged in recesses inside the side walls. Closed = across the chamber to the centre line,
# open = folded into the wall recess (the far leaf disappears into the far wall, the near leaf, standing in the cut-away near wall, is hidden).
def gate_state(g):
    def f(t):
        if t < T_HOOK1: return 0.0
        if g == 0: return PW([(T_G0C0, 1.0), (T_G0C1, 0.0)])(t) if t < T_DOWN else PW([(T_G0O0, 0.0), (T_G0O1, 1.0)])(t)
        if g == 1: return 0.0 if t >= T_DOWN else PW([(T_G1O0, 0.0), (T_G1O1, 1.0), (T_G1C0, 1.0), (T_G1C1, 0.0)])(t)
        if g == 2: return 0.0 if t >= T_DOWN else PW([(T_G2O0, 0.0), (T_G2O1, 1.0), (T_G2C0, 1.0), (T_G2C1, 0.0)])(t)
        return PW([(T_G3O0, 0.0), (T_G3O1, 1.0)])(t) if t < T_DOWN else 1.0
    return f
GATES = []
YP_ = YI + 0.45
for g, xg in enumerate(XG):
    zlo = FL[g - 1] if g > 0 else -12.0
    ztop = WT[min(g, NL - 1)] + 0.3
    fn = gate_state(g)
    for side, sgn in (("F", 1), ("N", -1)):
        piv = empty(f"GatePivot{g}{side}", (xg, sgn * YP_, 0))
        bm = bmesh.new()
        y0, y1 = sorted((-sgn * YP_, -sgn * 0.08))
        add_box(bm, -GT / 2, GT / 2, y0, y1, zlo, ztop)
        for zz in (zlo + 2.0, (zlo + ztop) / 2, ztop - 2.0):      # stiffening girders on the downstream face
            add_box(bm, -GT / 2 - 0.2, -GT / 2, y0 + 0.4, y1 - 0.3, zz - 0.3, zz + 0.3)
        leaf = mesh_obj(f"GateLeaf{g}{side}", bm, M_STEEL, parent=piv)
        bake_fn(piv, "rotation_euler", 2, (lambda f_, s_: (lambda t: math.radians(-90.0 * s_) * f_(t)))(fn, sgn))
        if side == "N":
            for ax in range(3): bake_fn(leaf, "scale", ax, (lambda f_: (lambda t: 1.0 if f_(t) < 0.8 else 0.0))(fn))
        GATES.append((piv, fn))
GATE_FN = [gate_state(g) for g in range(4)]

# valves: gold blocks in the culvert, lift into the wall when open
def valve(name, x):
    o = box(name, x - 0.9, x + 0.9, -YW_ - 0.15, YR + 0.02, ZC0 + 0.02, ZC1 - 0.02, M_VALVE); return o
FVALVE = valve("FillValve", X_FV); DVALVE = valve("DrainValve", X_DV)
bake_fn(FVALVE, "location", 2, lambda t: 0.0 if t < T_HOOK1 or t >= T_DOWN else PW([(T_FV0, 0.0), (T_FV1, 2.1), (T_FILL1, 2.1), (T_FILL1 + 0.6, 0.0)])(t))
bake_fn(DVALVE, "location", 2, lambda t: 0.0 if t < T_DOWN else PW([(T_DV0, 0.0), (T_DV1, 2.1), (T_DRAIN1, 2.1), (T_DRAIN1 + 0.6, 0.0)])(t))
glow(B_VALVE, pulse(C["valves"], 3.0) + pulse(C["valves2"], 3.0))

# culvert water strip (glows on "tunnels"; flowing water inside during fill / drain)
CW = box("CulvertWater", X_OUT, X_IN + 0.9, -YW_ + 0.05, YR, ZC0 + 0.05, ZC1 - 0.05, M_CW)
glow(B_CW, [(0, 0.0), (C["tunnels"] - 0.05, 0.0), (C["tunnels"] + 0.2, 2.2), (C["lake2"] - 0.3, 2.2), (C["lake2"] + 0.2, 0.6),
            (T_FILL1 + 0.3, 0.6), (T_FILL1 + 0.9, 0.0), (C["valves2"] - 0.05, 0.0), (C["valves2"] + 0.3, 0.6), (T_DRAIN1, 0.6), (T_DRAIN1 + 0.6, 0.0)])
windows(CW, [(T_HOOK1, DUR)])
SHAFT_W = box("ShaftWater", X_IN - 0.85, X_IN + 0.85, -YW_ + 0.05, YR, ZC1 - 0.05, FL[2] + 1.0, M_CW)
windows(SHAFT_W, [(T_HOOK1, DUR)])

# ================= ships =================
DRAFT = 2.5
def zcut(bm, z, keep_above):
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
    open_edges = [e for e in bm.edges if len(e.link_faces) < 2]
    if open_edges: bmesh.ops.edgeloop_fill(bm, edges=open_edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
HB = 5.3                                                    # half beam: 10.6 in an 11-wide chamber -> 0.2 (~2 ft) each side
def hull_bm():
    pts = []
    for s in (-1, 1):
        pts += [(-15, s * HB, 0.9), (-15, s * HB, 5.0), (-13.5, s * HB, 0.0), (9, s * HB, 0.0), (9, s * HB, 5.0), (12.8, s * 3.2, 0.4), (13, s * 3.6, 5.2)]
    pts += [(15.2, 0, 1.2), (15.8, 0, 5.4)]
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]
    bmesh.ops.convex_hull(bm, input=vs); return bm
def make_ship(name, hull_m, seed):
    rig = empty(name)
    bm = hull_bm(); zcut(bm, DRAFT - 0.1, False); mesh_obj(f"{name}HullLow", bm, M_HULLR, parent=rig)
    bm = hull_bm(); zcut(bm, DRAFT - 0.1, True); mesh_obj(f"{name}HullUp", bm, hull_m, parent=rig)
    box(f"{name}Deck", -14.8, 12.5, -HB + 0.15, HB - 0.15, 4.95, 5.05, M_RAIL, parent=rig)
    rnd = random.Random(seed)
    bms = [bmesh.new() for _ in CONT]
    for bx in range(7):
        x0 = -9.0 + bx * 3.0
        for row in range(4):
            y0 = -4.4 + row * 2.2
            h = rnd.choice((2, 3, 3, 4))
            for lv in range(h):
                add_box(bms[rnd.randrange(len(CONT))], x0, x0 + 2.85, y0, y0 + 2.1, 5.05 + lv * 1.3, 5.05 + lv * 1.3 + 1.25)
    for i, b_ in enumerate(bms): mesh_obj(f"{name}Boxes{i}", b_, CONT[i], parent=rig)
    box(f"{name}House", -14.4, -10.6, -4.4, 4.4, 5.0, 11.0, M_WHITE, parent=rig)
    box(f"{name}Win", -10.65, -10.5, -4.0, 4.0, 9.8, 10.6, M_WIN, parent=rig)
    box(f"{name}Wings", -12.2, -10.8, -HB, HB, 10.4, 11.0, M_WHITE, parent=rig)
    box(f"{name}Funnel", -14.3, -13.0, -0.8, 0.8, 11.0, 12.8, hull_m, parent=rig)
    box(f"{name}Mast", 12.0, 12.4, -0.2, 0.2, 5.0, 9.0, M_WHITE, parent=rig)
    return rig
SHIP = make_ship("Ship", M_HULL, 3)
SHIP2 = make_ship("ShipB", M_HULL2, 11)
def ship1_x(t):
    if t < T_HOOK1: return 100.0
    if t >= T_DOWN: return 175.0 + 0.8 * (t - T_DOWN)
    return PW([(T_HOOK1, -78.0), (T_SAIL0, -42.0), (T_SAIL1, 20.0), (T_MV0, 20.0), (T_MV1, 60.0), (T_MV2_0, 60.0), (T_MV2_1, 100.0),
               (T_OUT0, 100.0), (T_OUT1, 175.0)])(t) if t >= T_SAIL0 else -78.0 + (-42.0 + 78.0) * lin((t - T_HOOK1) / (T_SAIL0 - T_HOOK1))
def ship2_x(t): return PW([(T_S2_0, 20.0), (T_S2_1, -60.0)])(t)
ship1_z = lambda t: level_at(ship1_x(t), t) - DRAFT
ship2_z = lambda t: level_at(ship2_x(t), t) - DRAFT
bake_fn(SHIP, "location", 0, ship1_x); bake_fn(SHIP, "location", 2, ship1_z)
bake_fn(SHIP, "rotation_euler", 0, lambda t: 0.006 * math.sin(1.3 * t))
bake_fn(SHIP2, "location", 0, ship2_x); bake_fn(SHIP2, "location", 2, ship2_z)
windows(SHIP2, [(T_DOWN, C["would"] - 0.25)])

# ================= mules (electric locomotives) on the far wall, cables to the ship =================
def wall_top(x):
    if x < 0: return WT[0]
    b = [(0, WT[0]), (37, WT[0]), (43, WT[1]), (77, WT[1]), (83, WT[2]), (125, WT[2])]
    for (x0, z0), (x1, z1) in zip(b, b[1:]):
        if x <= x1: return z0 + (z1 - z0) * ease((x - x0) / (x1 - x0))
    return WT[2]
YM = 7.25
for k in range(NL):
    for yr in (YM - 0.6, YM + 0.6):
        box(f"Rail{k}_{yr}", LX * k + 3, LX * (k + 1) - 3, yr - 0.08, yr + 0.08, WT[k], WT[k] + 0.12, M_RAIL)
def make_mule(name):
    rig = empty(name)
    box(f"{name}Body", -1.6, 1.6, -0.85, 0.85, 0.15, 1.25, M_MULE, parent=rig)
    box(f"{name}Band", -1.62, 1.62, -0.87, 0.87, 0.55, 0.75, M_MULE2, parent=rig)
    box(f"{name}Cab", -0.7, 0.7, -0.8, 0.8, 1.25, 1.95, M_MULE, parent=rig)
    box(f"{name}CabWin", -0.72, 0.72, -0.82, 0.82, 1.45, 1.8, M_WIN, parent=rig)
    return rig
def mule_x(t, front): return max(12.0, min(118.0, ship1_x(t) + 11.0)) if front else max(2.0, min(108.0, ship1_x(t) - 11.0))
MULES = []
for front in (True, False):
    m_ = make_mule("MuleF" if front else "MuleB")
    bake_fn(m_, "location", 0, (lambda fr: (lambda t: mule_x(t, fr)))(front))
    bake_fn(m_, "location", 1, lambda t: YM)
    bake_fn(m_, "location", 2, (lambda fr: (lambda t: wall_top(mule_x(t, fr)) + 0.1))(front))
    MULES.append(m_)
CAB_ME = bpy.data.meshes.new("CableMesh")
bm = bmesh.new(); add_cyl(bm, 1.0, 1.0, "Z", (0, 0, 0.5), seg=8); bm.to_mesh(CAB_ME); bm.free(); CAB_ME.materials.append(M_CABLE)
def cable_ends(t, front, along):
    mx = mule_x(t, front); sx = ship1_x(t)
    a = Vector((mx + (-0.8 if front else 0.8), YM - 0.9, wall_top(mx) + 0.9))
    b = Vector((sx + (along if front else -along), HB - 0.3, ship1_z(t) + 5.0))
    return a, b
CABLES = []
for front in (True, False):
    for along in (9.0, 12.5):
        o = bpy.data.objects.new(f"Cable{int(front)}{along}", CAB_ME); CL.objects.link(o); o.rotation_mode = "QUATERNION"
        locs = [[], [], []]; qs = [[], [], [], []]; sc = []
        for t in TS:
            a, b = cable_ends(t, front, along); d = b - a
            q = d.to_track_quat("Z", "Y")
            for ax in range(3): locs[ax].append(a[ax])
            for i in range(4): qs[i].append(q[i])
            sc.append(d.length)
        for ax in range(3): bake(o, "location", ax, locs[ax])
        for i in range(4): bake(o, "rotation_quaternion", i, qs[i])
        bake(o, "scale", 0, [0.14] * FRAMES); bake(o, "scale", 1, [0.14] * FRAMES); bake(o, "scale", 2, sc)
        windows(o, [(T_SAIL1 + 0.1, T_OUT0)])
        CABLES.append(o)
glow(bpy.data.materials["Cable"].node_tree.nodes["Principled BSDF"], pulse(C["cables"], 4.0, hold=0.8))

# ================= flows: baked drops along paths =================
SPH = bpy.data.meshes.new("DropMesh")
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); bm.to_mesh(SPH); bm.free()
for poly in SPH.polygons: poly.use_smooth = True
SPH.materials.append(M_DROP)
def path_fn(pts3):
    P = [Vector(p) for p in pts3]; seg = [(P[i + 1] - P[i]).length for i in range(len(P) - 1)]; tot = sum(seg)
    def at(u):
        d = max(0.0, min(1.0, u)) * tot
        for i, s in enumerate(seg):
            if d <= s or i == len(seg) - 1: return P[i].lerp(P[i + 1], d / s if s else 0)
            d -= s
    return at, tot
_drop_n = [0]
def stream(name, pts, t0, t1, n, speed, rad, jitter=0.15):
    at, tot = path_fn(pts); travel = tot / speed
    span = max(0.05, (t1 - t0) - travel)
    for k in range(n):
        tk = t0 + span * k / max(1, n - 1)
        o = bpy.data.objects.new(f"{name}{k}", SPH); CL.objects.link(o)
        jx, jy, jz = (random.uniform(-jitter, jitter) for _ in range(3))
        loc = [[], [], []]; sc = []
        for t in TS:
            u = (t - tk) / travel
            p = at(u) + Vector((jx, jy, jz))
            for ax in range(3): loc[ax].append(p[ax])
            s = rad if 0.0 <= u <= 1.0 else 0.0
            if 0 <= u < 0.04: s = rad * u / 0.04
            if 0.94 < u <= 1: s = rad * (1 - u) / 0.06
            sc.append(s)
        for ax in range(3): bake(o, "location", ax, loc[ax]); bake(o, "scale", ax, sc)
        _drop_n[0] += 1
YC = -7.75; ZCM = (ZC0 + ZC1) / 2
for i, xr in enumerate(RISERS):
    FILLP = [(X_IN + 7.0, -3.0, LAKE - 2.0), (X_IN, YC, FL[2] + 1.0), (X_IN, YC, ZCM), (xr, YC, ZCM), (xr, YC, FL[0] - 0.3),
             (xr, -3.5, FL[0] + 1.2), (xr + 1.0, -1.0, FL[0] + 4.0)]
    stream(f"Fill{i}_", FILLP, T_FLOW0 + 0.05 * i, T_FILL1 - 0.2, 26, 44.0, 0.34)
    DRAINP = [(xr + 1.0, -1.0, FL[0] + 4.5), (xr, -3.5, FL[0] + 1.0), (xr, YC, FL[0] - 0.3), (xr, YC, ZCM), (X_OUT - 1.0, YC, ZCM),
              (-8.0, -5.5, -11.0), (-22.0, -3.0, -5.0)]
    stream(f"Drain{i}_", DRAINP, T_DRAIN0 - 0.2 + 0.05 * i, T_DRAIN1 + 0.4, 18, 30.0, 0.34)

# ================= water-saving side basins (newer locks), beside chamber 2 =================
BAS = []
for j in range(3):
    rim = WT[1] + 2.0 - 0.8 * j; y0 = 24.0 + 9.0 * j
    rig = empty(f"BasinRig{j}")
    bm = bmesh.new()
    add_box(bm, 44, 76, y0, y0 + 0.6, rim - 5, rim); add_box(bm, 44, 76, y0 + 7.4, y0 + 8, rim - 5, rim)
    add_box(bm, 44, 44.6, y0, y0 + 8, rim - 5, rim); add_box(bm, 75.4, 76, y0, y0 + 8, rim - 5, rim); add_box(bm, 44, 76, y0, y0 + 8, rim - 5.4, rim - 4.4)
    mesh_obj(f"Basin{j}", bm, M_CON, parent=rig)
    wo = box(f"BasinWater{j}", 44.6, 75.4, y0 + 0.6, y0 + 7.4, 0, 1, M_BW, parent=rig); wo.location = (0, 0, rim - 4.4)
    bake_fn(wo, "scale", 2, (lambda jj: (lambda t: PW([(C["save"] - 0.1 + 0.25 * jj, 0.15), (C["would"] - 0.2, 2.8)])(t)))(j))
    bake_fn(rig, "location", 2, (lambda jj: (lambda t: -14.0 * (1 - pop(t, T_BAS0 + 0.15 * jj, 0.5)) if t < T_BAS0 + 0.15 * jj + 0.9 else 0.0))(j))
    windows(rig, [(T_BAS0, DUR)])
    stream(f"Save{j}_", [(60.0, 2.0, 2 * STEP - 0.5), (60.0, YW_ - 1.0, WT[1] + 2.5), (60.0, y0 + 4.0, rim + 0.5), (60.0, y0 + 4.0, rim - 3.0)],
           C["save"] - 0.3 + 0.2 * j, C["would"] + 0.6, 16, 14.0, 0.34)
glow(B_BW, pulse(C["sixty"], 2.0, hold=0.8))

# ================= guide lines (emissive, illustrative) =================
def gbar(name, x0, x1, y0, y1, z0, z1, m_, org):
    bm = bmesh.new(); add_box(bm, x0 - org[0], x1 - org[0], y0 - org[1], y1 - org[1], z0 - org[2], z1 - org[2])
    o = mesh_obj(name, bm, m_); o.location = org; return o
# 85 ft: vertical bar at the sea end from sea level to lake level + the lake-level line along the flight
B85 = gbar("Bar85", -3.2, -2.8, -9.8, -9.4, 0.0, LAKE, M_CYAN, (-3.0, -9.6, 0.0))
L85 = gbar("Line85", -3.0, 120.0, -9.75, -9.45, LAKE - 0.12, LAKE + 0.12, M_CYAN, (-3.0, -9.6, LAKE))
T85a = gbar("Tick85a", -4.2, -1.8, -9.8, -9.4, -0.12, 0.12, M_CYAN, (-3.0, -9.6, 0.0))
t85 = C["eighty2"] - 0.15
bake_fn(B85, "scale", 2, lambda t: max(0.001, ease((t - t85) / 0.6)))
bake_fn(L85, "scale", 0, lambda t: max(0.001, ease((t - t85 - 0.3) / 0.8)))
for o in (B85, L85, T85a): windows(o, [(t85, C["climb"] - 0.1)])
# 1,000 ft: along chamber 1, above where the near wall was
B1K = gbar("Bar1000", 0.4, 39.6, -5.9, -5.5, WT[0] + 1.0, WT[0] + 1.35, M_CYAN, (20.0, -5.7, WT[0] + 1.17))
TK = [gbar(f"Tick1000{i}", x - 0.2, x + 0.2, -5.9, -5.5, WT[0] + 0.3, WT[0] + 2.1, M_CYAN, (x, -5.7, WT[0] + 1.2)) for i, x in enumerate((0.4, 39.6))]
t1k = C["thousand"] - 0.1
bake_fn(B1K, "scale", 0, lambda t: max(0.001, ease((t - t1k) / 0.6)))
for o in [B1K] + TK: windows(o, [(t1k, C["ship"] - 0.2)])
# 2 ft to spare: glowing strips in the gaps between hull and walls (follow the ship and the water)
GAPS = []
for s in (-1, 1):
    o = gbar(f"Gap{s}", -14.0, 13.0, -0.09, 0.09, -0.05, 0.25, M_GOLD, (0, 0, 0))
    bake_fn(o, "location", 0, ship1_x); bake_fn(o, "location", 1, (lambda ss: (lambda t: ss * (YI - 0.1)))(s))
    bake_fn(o, "location", 2, lambda t: level_at(ship1_x(t), t))
    windows(o, [(C["two"] - 0.1, C["three2"] - 0.3)]); GAPS.append(o)

# ================= near-wall cover (hook), sinks on "cut", back for the top-down shot =================
COVER = empty("CoverRig")
cover = []
for k in range(NL):
    cover.append(box(f"Cover{k}", LX * k, LX * (k + 1), -YW_, -YI, FL[k] + 1.0, WT[k], M_CON, parent=COVER))
cover.append(box("CoverLake", 120, 128, -YW_, -YI, FL[2] + 1.0, WT[2], M_CON, parent=COVER))
T_TOP0, T_TOP1 = C["because"] - 0.25, C["three2"] - 0.3
bake_fn(COVER, "location", 2, lambda t: 0.0 if (t < T_CV0 or T_TOP0 <= t < T_TOP1) else (-40.0 * ease((t - T_CV0) / (T_CV1 - T_CV0)) if t < T_CV1 else -40.0))
windows(COVER, [(0, T_CV1 + 0.05), (T_TOP0, T_TOP1)])

# ================= highlight pulses =================
for k, cue in enumerate(("three", "giant2", "steps")): glow(WM[k][1], pulse(C[cue], 1.6, hold=0.35))
glow(WM[0][1], [(C["chamber"] - 0.01, 0.0), (C["chamber"] + 0.15, 1.2), (C["chamber"] + 0.8, 1.2), (C["chamber"] + 1.4, 0.0),
                (C["water"] - 0.01, 0.0), (C["water"] + 0.15, 0.9), (C["matches"], 0.9), (C["matches"] + 0.6, 0.0)])
glow(B_LAKE, pulse(C["gatun"], 1.0, hold=1.0) + pulse(C["lake2"], 1.2, hold=0.6) + pulse(C["fresh"], 1.6, hold=1.0))
glow(B_SEA, pulse(C["sea"], 1.0, hold=0.6) + pulse(C["sea2"], 1.0, hold=0.8))
glow(B_STEEL, pulse(C["gates"], 1.5, hold=0.5) + pulse(C["gates2"], 1.5, hold=0.5))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.5; cam_d.clip_end = 1500
ORBA = lambda t: math.radians(-35 + 30 * lin((t - C["would"]) / (DUR - C["would"])))
ORX = lambda t: 60 + 125 * math.sin(ORBA(t)); ORY = lambda t: -125 * math.cos(ORBA(t))
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (74.0, -42.0, 44.0), (100.0, 0.0, 14.0), 28),
    (T_HOOK1 - 0.3, (80.0, -36.0, 40.0), (100.0, 0.0, 15.0), 28),
    (T_HOOK1, (-72.0, -30.0, 30.0), (50.0, 0.0, 2.0), 26, "cut"),
    (C["climb"] - 0.3, (-66.0, -28.0, 28.0), (55.0, 0.0, 4.0), 26),
    (C["three"] - 0.1, (-40.0, -70.0, 58.0), (60.0, 0.0, 0.0), 26),
    (C["each"] - 0.3, (-34.0, -72.0, 55.0), (60.0, 0.0, 0.0), 26),
    (C["each"] - 0.25, (2.0, -52.0, 22.0), (20.0, 0.0, -1.0), 24, "cut"),
    (C["ship"] - 0.4, (4.0, -50.0, 21.0), (20.0, 0.0, -1.0), 24),
    (C["sails"], (-14.0, -54.0, 20.0), (4.0, 0.0, 0.0), 24),
    (C["shut"] - 0.1, (6.0, -50.0, 22.0), (16.0, 0.0, 0.0), 24),
    (C["inside"] - 0.3, (7.0, -49.0, 22.0), (16.0, 0.0, 0.0), 24),
    (C["inside"] - 0.25, (8.0, -26.0, -10.0), (45.0, -8.0, -15.5), 24, "cut"),
    (C["lake2"] - 0.3, (16.0, -25.0, -10.5), (55.0, -8.0, -15.5), 24),
    (C["lake2"] - 0.25, (100.0, -36.0, 4.0), (121.0, -6.0, -4.0), 24, "cut"),
    (C["gravity"], (102.0, -35.0, 4.0), (121.0, -6.0, -5.0), 24),
    (C["down"] - 0.2, (-22.0, -40.0, 4.0), (60.0, -8.0, -10.0), 26),
    (C["up"] - 0.25, (-18.0, -40.0, 4.0), (60.0, -8.0, -10.0), 26),
    (C["up"] - 0.2, (14.0, -36.0, 16.0), (20.0, 0.0, -6.0), 24, "cut"),
    (C["water"] - 0.25, (15.0, -35.0, 16.0), (20.0, 0.0, -5.0), 24),
    (C["water"] - 0.2, (6.0, -52.0, 22.0), (22.0, 0.0, 0.0), 24, "cut"),
    (C["gates2"] - 0.25, (9.0, -50.0, 21.0), (22.0, 0.0, 1.0), 24),
    (C["gates2"] - 0.2, (28.0, -62.0, 26.0), (44.0, 0.0, 2.0), 24, "cut"),
    (C["electric"] - 0.1, (38.0, -60.0, 26.0), (54.0, 0.0, 3.0), 24),
    (C["mules"], (46.0, -38.0, 36.0), (60.0, 6.0, 9.0), 24),
    (C["because"] - 0.3, (50.0, -36.0, 36.0), (62.0, 6.0, 9.0), 24),
    (C["because"] - 0.25, (58.0, -0.6, 120.0), (58.0, 0.0, 8.0), 80, "cut"),
    (C["three2"] - 0.35, (62.0, -0.6, 118.0), (62.0, 0.0, 8.0), 80),
    (C["three2"] - 0.3, (70.0, -80.0, 48.0), (110.0, 0.0, 8.0), 24, "cut"),
    (C["going"] - 0.3, (95.0, -80.0, 46.0), (135.0, 0.0, 10.0), 24),
    (C["going"] - 0.25, (6.0, -50.0, 18.0), (16.0, 0.0, -4.0), 24, "cut"),
    (C["run"] - 0.1, (6.0, -50.0, 17.0), (16.0, 0.0, -4.0), 24),
    (C["sea2"], (-8.0, -46.0, 8.0), (6.0, -6.0, -10.0), 24),
    (C["every"] - 0.3, (-10.0, -46.0, 8.0), (4.0, -6.0, -10.0), 24),
    (C["every"] - 0.25, (110.0, -60.0, 36.0), (170.0, 20.0, 12.0), 26, "cut"),
    (C["thats"] - 0.3, (116.0, -58.0, 36.0), (170.0, 20.0, 12.0), 26),
    (C["thats"] - 0.25, (48.0, -26.0, 48.0), (60.0, 26.0, 10.0), 24, "cut"),
    (C["would"] - 0.3, (52.0, -24.0, 46.0), (60.0, 26.0, 10.0), 24),
    (C["would"] - 0.25, (ORX, ORY, 60.0), (60.0, 0.0, 2.0), 26, "cut"),
    (C["end"], (ORX, ORY, 60.0), (60.0, 0.0, 2.0), 26),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t0_, t1 = SHOTS[k][0], SHOTS[k + 1][0]
        u = ease((t - t0_) / (t1 - t0_)) if t1 > t0_ else 1.0
        if callable(SHOTS[k][1][0]): u = 0.0
        l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.05 * math.sin(t * 0.7), 0.0, 0.04 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()

# ================= world + light: tropical daylight =================
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
    try: sky.sun_elevation = math.radians(40); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.22
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1); bg.inputs["Strength"].default_value = 0.8
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.0; sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(45), math.radians(-25), math.radians(-30))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 60; fill_d.energy = 12000; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (14, 18, 0)

# ================= render settings =================
r = scene.render; r.engine = "CYCLES"
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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4; scene.cycles.transparent_max_bounces = 16; scene.cycles.volume_bounces = 0
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
FV_Z = lambda t: 0.0 if t < T_HOOK1 or t >= T_DOWN else PW([(T_FV0, 0.0), (T_FV1, 2.1), (T_FILL1, 2.1), (T_FILL1 + 0.6, 0.0)])(t)
ANCH = {
    "lake": lambda t: Vector((165.0, 0.0, LAKE)),
    "sea": lambda t: Vector((-40.0, -4.0, 0.0)),
    "chamber": lambda t: Vector((30.0, -3.0, level0(t))),
    "gate0": lambda t: Vector((0.0, -1.0, WT[0] + 0.3)),
    "gate1": lambda t: Vector((40.0, -1.0, WT[1] + 0.3)),
    "culvert": lambda t: Vector((40.0, -9.3, ZCM)),
    "valve": lambda t: Vector((X_FV, -9.3, ZC1 + FV_Z(t))),
    "holes": lambda t: Vector((24.0, -3.0, FL[0])),
    "mule": lambda t: Vector((mule_x(t, True), YM, wall_top(mule_x(t, True)) + 2.0)),
    "ship": lambda t: Vector((ship1_x(t), 0.0, ship1_z(t) + 11.0)),
    "basins": lambda t: Vector((60.0, 33.0, WT[1] + 1.2)),
    "outlet": lambda t: Vector((X_OUT, -9.3, ZCM)),
    "gap": lambda t: Vector((ship1_x(t) + 4.0, YI - 0.1, level_at(ship1_x(t), t))),
}
anchors = {k: [] for k in ANCH}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):   # build_cover.py re-uses this scene and skips the export
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cover": R3(T_CV0, T_CV1), "sail": R3(T_SAIL0, T_SAIL1), "gate0_close": R3(T_G0C0, T_G0C1), "fill_valve": R3(T_FV0, T_FV1),
          "flow": round(T_FLOW0, 3), "fill1": R3(T_FILL0, T_FILL1), "gate1_open": R3(T_G1O0, T_G1O1), "move2": R3(T_MV0, T_MV1),
          "gate1_close": R3(T_G1C0, T_G1C1), "fill2": R3(T_FILL2_0, T_FILL2_1), "gate2_open": R3(T_G2O0, T_G2O1), "move3": R3(T_MV2_0, T_MV2_1),
          "gate2_close": R3(T_G2C0, T_G2C1), "fill3": R3(T_FILL3_0, T_FILL3_1), "gate3_open": R3(T_G3O0, T_G3O1), "out": R3(T_OUT0, T_OUT1),
          "down": round(T_DOWN, 3), "drain_valve": R3(T_DV0, T_DV1), "drain": R3(T_DRAIN0, T_DRAIN1), "gate0_open": R3(T_G0O0, T_G0O1),
          "ship2_out": R3(T_S2_0, T_S2_1), "basins": round(T_BAS0, 3), "top": R3(T_TOP0, T_TOP1), "drops": _drop_n[0]}
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
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
