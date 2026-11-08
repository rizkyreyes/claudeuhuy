# Suspension-Bridge-P1-3D: how a suspension bridge is built, part 1 (anchorages, towers + saddles, pilot line by kite, catwalk,
# aerial cable spinning, 61 strands compacted into one round cable). Blender Cycles, real-world setting: a sea strait between two
# rocky headlands in daylight, bridge along x, the two main cables at y = +-CY, camera mostly on -y.
# Cutaways: the left anchorage is cut at its near cable plane (near piece slides away) so the eyebars cast inside show;
# a separate cable-end set (61 hex strands of ~452 wires, drawn with a Voronoi wire texture) shows the cut face of the cable.
# Illustrative scale: spans shortened (main span 110, towers 72 high), cable drawn ~2x thick, 61 strands as one hex pack.
# The bridge is generic (orange towers, no logos, no people); the Golden Gate is named in the VO only.
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
random.seed(11)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("each", "each"), ("golden", "golden"), ("n27572", "27572"), ("wires", "wires"), ("spun", "spun"), ("every", "every"),
        ("hangs", "hangs"), ("slip", "slip"), ("lets", "let's"), ("cut", "cut"), ("first", "first"), ("anchorages", "anchorages"),
        ("cables", "cables"), ("pull", "pull"), ("force", "force"), ("giant", "giant"), ("concrete", "concrete"), ("eyebars", "eyebars"),
        ("next", "next"), ("towers", "towers"), ("rise", "rise"), ("saddle", "saddle"), ("cradle", "cradle"), ("so", "so"),
        ("first2", "first"), ("line", "line"), ("across", "across"), ("niagara", "niagara"), ("n1848", "1848"), ("kite", "kite"),
        ("thin", "thin"), ("heavier", "heavier"), ("ropes", "ropes"), ("catwalk", "catwalk"), ("sky", "sky"), ("spinning", "spinning"),
        ("wheel", "wheel"), ("anchorage", "anchorage"), ("towers2", "towers"), ("side", "side"), ("loop", "loop"), ("wire", "wire"),
        ("loop2", "loop"), ("hooked", "hooked"), ("back", "back"), ("more", "more"), ("golden2", "golden"), ("six", "six"),
        ("months", "months"), ("eighty", "eighty"), ("miles", "miles"), ("wires2", "wires"), ("n61", "61"), ("strands", "strands"),
        ("squeezed", "squeezed"), ("round", "round"), ("about", "about"), ("three", "three"), ("thick", "thick"), ("but", "but"),
        ("road", "road"), ("would", "would"), ("catwalk2", "catwalk"), ("sea", "sea"), ("tell", "tell"), ("part", "part"),
        ("tomorrow", "tomorrow"), ("hang", "hang"), ("road2", "road"), ("follow", "follow")]
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
CL = coll("Bridge")
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

# ================= materials =================
M_CONC, B_CONC = mat("Concrete", (0.50, 0.49, 0.46), 0.85, emit_rgb=(0.98, 0.74, 0.27), noise=6.0)
M_CONC_IN = mat("ConcreteCut", (0.40, 0.39, 0.37), 0.9)[0]
M_TOWER, B_TOWER = mat("TowerPaint", (0.62, 0.13, 0.04), 0.5, 0.2, emit_rgb=(0.98, 0.74, 0.27))
M_SADDLE, B_SADDLE = mat("Saddle", (0.28, 0.29, 0.31), 0.35, 0.9, emit_rgb=(0.98, 0.74, 0.27))
M_CABLE, B_CABLE = mat("Cable", (0.50, 0.52, 0.54), 0.4, 0.8, emit_rgb=(0.98, 0.74, 0.27))
M_WIRE, B_WIRE = mat("LiveWire", (0.75, 0.80, 0.82), 0.25, 0.9, emit_rgb=(0.30, 0.92, 1.0)); B_WIRE.inputs["Emission Strength"].default_value = 3.0
M_ROPE = mat("Rope", (0.16, 0.16, 0.17), 0.6, 0.4)[0]
M_EYE, B_EYE = mat("Eyebar", (0.36, 0.37, 0.39), 0.4, 0.9, emit_rgb=(0.98, 0.74, 0.27))
M_WALK = mat("Catwalk", (0.20, 0.19, 0.17), 0.8)[0]
M_KITE = mat("Kite", (0.85, 0.20, 0.12), 0.5, emit_rgb=(1.0, 0.4, 0.2))[0]
bpy.data.materials["Kite"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5
M_WHEEL, B_WHEEL = mat("Wheel", (0.85, 0.62, 0.15), 0.35, 0.6, emit_rgb=(0.98, 0.74, 0.27))
M_ARROW = mat("PullArrow", (0.9, 0.2, 0.15), 0.5, emit_rgb=(1.0, 0.3, 0.24))[0]
bpy.data.materials["PullArrow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0
M_GOLD = mat("GoldBar", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27))[0]
bpy.data.materials["GoldBar"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.5
M_FACE, B_FACE = wire_face("WireFace")
M_SHEATH = mat("Sheath", (0.40, 0.42, 0.44), 0.45, 0.7)[0]
M_ROCK = ground("Rock", (0.20, 0.18, 0.15), (0.38, 0.34, 0.28), 0.06)
M_GRASS = ground("Grass", (0.14, 0.20, 0.08), (0.28, 0.33, 0.14), 0.08)
M_SEA, B_SEA = surf_mat("Sea", (0.02, 0.11, 0.17))
M_GHOST, GH_FAC = ghost("GhostDeck", (0.30, 0.92, 1.0))
M_GHOST_R, GHR_FAC = ghost("GhostDeckRed", (1.0, 0.30, 0.24))

# ================= layout =================
CY, TX, TH, AX = 7.0, 55.0, 72.0, 102.0     # cable y, tower x, tower top z, anchorage front x
LOW, AZ = 26.0, 14.0                        # main-span cable low point, cable entry z at the anchorage front
LAND_X = 84.0
def cable_z(x):
    ax_ = abs(x)
    if ax_ <= TX: return LOW + (TH - LOW) * (x / TX) ** 2
    u = (ax_ - TX) / (AX - TX)
    return TH + (AZ - TH) * u - 4.0 * math.sin(math.pi * u)
XS = [-AX + i * 1.0 for i in range(int(2 * AX) + 1)]
def path(y, dz=0.0, x0=-AX, x1=AX): return [(x, y, cable_z(x) + dz) for x in XS if x0 - 1e-6 <= x <= x1 + 1e-6]
def arclen(pts):
    L = [0.0]
    for a, b in zip(pts, pts[1:]): L.append(L[-1] + (Vector(b) - Vector(a)).length)
    return L
P_NEAR = path(-CY); LEN = arclen(P_NEAR); TOT = LEN[-1]
def at_s(s, y=-CY, dz=0.0):
    """Point and slope angle on the cable path at arc fraction s."""
    s = max(0.0, min(1.0, s)); d = s * TOT
    i = max(0, min(len(LEN) - 2, next((k for k in range(len(LEN) - 1) if LEN[k + 1] >= d), len(LEN) - 2)))
    a, b = Vector(P_NEAR[i]), Vector(P_NEAR[i + 1]); u = (d - LEN[i]) / max(1e-6, LEN[i + 1] - LEN[i])
    p = a.lerp(b, u); ang = math.atan2(b.z - a.z, b.x - a.x)
    return Vector((p.x, y, p.z + dz)), ang

def curve(name, pts, depth, m_, res=6):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1.0)
    cu.bevel_depth = depth; cu.bevel_resolution = res; cu.use_fill_caps = True
    try: cu.bevel_factor_mapping_end = "SPLINE"
    except Exception: pass
    o = bpy.data.objects.new(name, cu); CL.objects.link(o)
    if m_: cu.materials.append(m_)
    return o

# ================= terrain + sea =================
SEA = box("Sea", -600, 600, -600, 600, -3.0, 0.0, M_SEA)
for s in (-1, 1):
    x0, x1 = (-400, -LAND_X) if s < 0 else (LAND_X, 400)
    box(f"Headland{s}", x0, x1, -150, 150, -20, 6.0, M_ROCK)
    box(f"HeadlandTop{s}", x0 + s * 0.0, x1, -150, 150, 6.0, 6.4, M_GRASS)
    # a sloped cliff face toward the water
    bm = bmesh.new(); xf = s * LAND_X
    vs = [bm.verts.new(v) for v in [(xf, -150, 6.4), (xf, 150, 6.4), (xf - s * 0.0 + s * -10.0, 150, -3.0), (xf + s * -10.0, -150, -3.0),
                                    (xf, -150, -3.0), (xf, 150, -3.0)]]
    for f in ([0, 1, 2, 3], [0, 3, 4], [1, 5, 2], [3, 2, 5, 4]):
        try: bm.faces.new([vs[i] for i in f])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj(f"Cliff{s}", bm, M_ROCK)
# distant hills for the horizon
for i in range(7):
    x = -330 + i * 110 + random.uniform(-20, 20)
    o = cyl(f"Hill{i}", random.uniform(45, 80), 1.0, "Z", (0, 0, 0), M_GRASS, seg=24); o.location = (x, 520, -2); o.scale = (1.6, 1.0, random.uniform(28, 55))

# ================= anchorages (left one is cut at its near cable plane) =================
AW0, AW1, AH = AX, AX + 26.0, 22.0          # |x| from front to back, height
SLOT = -CY + 2.6                            # far piece starts here (the slot that holds the eyebars)
ANCH, ANCH_NEAR, EYES = {}, None, []
for s in (-1, 1):
    root = empty(f"Anchorage{s}"); ANCH[s] = root
    xa, xb = sorted((s * AW0, s * AW1))
    if s < 0:
        far = box("AnchorFar", xa, xb, SLOT, 14.0, 0.0, AH, M_CONC, root)
        nr = empty("AnchorNearRoot", parent=root)
        box("AnchorNear", xa, xb, -14.0, SLOT, 0.0, AH, M_CONC, nr); ANCH_NEAR = nr
        box("AnchorSlotBack", xa + 0.2, xb - 0.2, SLOT - 0.05, SLOT, 0.0, AH - 0.2, M_CONC_IN, root)
        # eyebar fan: splay point at the front, bars down and back to an anchor plate deep in the concrete (in the slot)
        SPL = Vector((s * (AW0 + 1.5), -CY + 1.2, AZ))
        box("AnchorPlate", -AW1 + 2.0, -AW1 + 3.2, -CY + 0.1, -CY + 2.4, 1.5, 11.0, M_EYE, root)
        for k in range(9):
            zt = 2.0 + k * 1.1
            bm = bmesh.new(); add_bar(bm, SPL, (-AW1 + 3.2, -CY + 1.2 + 0.3 * math.sin(k), zt), 0.45)
            o = mesh_obj(f"Eyebar{k}", bm, M_EYE, root); EYES.append(o)
        bm = bmesh.new(); add_cyl(bm, 1.1, 2.6, "X", (0, 0, 0)); o = mesh_obj("SplaySaddle", bm, M_SADDLE, root); o.location = SPL
    else:
        box("AnchorR", xa, xb, -14.0, 14.0, 0.0, AH, M_CONC, root)
    for o in [root] + list(root.children_recursive): o.location.z += 6.0 if o is root else 0.0
# ================= towers + saddles =================
TOWERS, SADDLES = [], []
for s in (-1, 1):
    box(f"Pier{s}", s * TX - 6, s * TX + 6, -12, 12, -3.0, 4.0, M_CONC)
    root = empty(f"Tower{s}", (s * TX, 0, 4.0)); TOWERS.append(root)
    bm = bmesh.new()
    for yy in (-CY, CY):
        add_box(bm, -2.2, 2.2, yy - 2.2, yy + 2.2, 0.0, TH - 4.0 - 1.2)
    for zz in (16.0, 34.0, 50.0, TH - 4.0 - 4.0):
        add_box(bm, -1.6, 1.6, -CY, CY, zz, zz + 3.0)
    mesh_obj(f"TowerLegs{s}", bm, M_TOWER, root)
    for yy in (-CY, CY):
        sd = empty(f"Saddle{s}{yy}", (s * TX, yy, TH - 1.6)); SADDLES.append(sd)
        bm = bmesh.new(); add_box(bm, -2.6, 2.6, -1.8, 1.8, -0.6, 0.6); add_cyl(bm, 2.2, 3.4, "Y", (0, 0, 0.4), seg=24)
        mesh_obj(f"SaddleM{s}{yy}", bm, M_SADDLE, sd)
# ================= cables, pilot line, ropes, catwalk, wheels, live wires =================
CABLES = [curve(f"MainCable{yy}", path(yy), 1.0, M_CABLE) for yy in (-CY, CY)]
PILOT = curve("PilotLine", [(x, -CY, TH + 1.0 - 9.0 * math.cos(math.pi * x / (2 * TX))) for x in XS if abs(x) <= TX], 0.16, M_WIRE, 3)
ROPES = [curve(f"Rope{yy}", path(yy, -0.4), 0.18, M_ROPE, 3) for yy in (-CY, CY)]
WALK = []
for yy in (-CY, CY):
    pts = path(yy, -1.7)
    chunks = [pts[i:i + 9] for i in range(0, len(pts) - 1, 8)]
    for ci, ch in enumerate(chunks):
        bm = bmesh.new()
        for a, b in zip(ch, ch[1:]):
            a, b = Vector(a), Vector(b); d = b - a; ang = math.atan2(d.z, d.x)
            vs = add_box(bm, -0.55, 0.55, yy - 1.7, yy + 1.7, -0.08, 0.08)
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(-ang, 3, "Y"))
            bmesh.ops.translate(bm, verts=vs, vec=(a + b) / 2)
        o = mesh_obj(f"Walk{yy}_{ci}", bm, M_WALK)
        cx = sum(p[0] for p in ch) / len(ch); WALK.append((o, cx))
RAILS = [curve(f"Rail{yy}{dy}", path(yy + dy, -0.6), 0.07, M_ROPE, 2) for yy in (-CY, CY) for dy in (-1.6, 1.6)]
WIRES = [curve(f"LiveWire{yy}", path(yy, 0.25), 0.10, M_WIRE, 3) for yy in (-CY, CY)]
WIRES2 = [curve(f"ReturnWire{yy}", path(yy, 0.45), 0.10, M_WIRE, 3) for yy in (-CY, CY)]
WHEELS = []
for yy in (-CY, CY):
    w = empty(f"WheelRoot{yy}")
    bm = bmesh.new(); add_cyl(bm, 1.3, 0.35, "Y", (0, 0, 0), seg=32)
    for k in range(3):
        a = k * math.pi / 3; add_bar(bm, (-1.2 * math.cos(a), 0, -1.2 * math.sin(a)), (1.2 * math.cos(a), 0, 1.2 * math.sin(a)), 0.18)
    wm = mesh_obj(f"Wheel{yy}", bm, M_WHEEL, w)
    bm = bmesh.new(); add_bar(bm, (0, 0, 0), (0, 0, 3.0), 0.15); mesh_obj(f"WheelHanger{yy}", bm, M_ROPE, w)
    WHEELS.append((w, wm, yy))
# ghost deck for the hook ("every car hangs from them") and the "still no road" beat
GHOST = empty("GhostDeck"); GHOST_R = empty("GhostDeckRed")
for root_, m_ in ((GHOST, M_GHOST), (GHOST_R, M_GHOST_R)):
    bm = bmesh.new(); add_box(bm, -AX, AX, -CY - 2.5, CY + 2.5, 19.0, 20.6)
    if root_ is GHOST:
        for x in range(-52, 53, 4):
            for yy in (-CY, CY): add_box(bm, x - 0.12, x + 0.12, yy - 0.12, yy + 0.12, 20.6, cable_z(x))
        for i in range(14):
            x = -90 + i * 13 + random.uniform(-3, 3); yy = random.choice((-2.6, 2.6))
            add_box(bm, x - 2.0, x + 2.0, yy - 1.0, yy + 1.0, 20.6, 22.0)
    mesh_obj("GhostDeckM" if root_ is GHOST else "GhostDeckRedM", bm, m_, root_)
# pull arrow at the left anchorage (the cable pulls toward the span)
bm = bmesh.new(); add_arrow(bm, (-AW0 + 1.0, AZ + 6.0 + 2.0), (1.0, 0.35), 18.0, 2.6, y=-CY - 3.0); ARROW = mesh_obj("PullArrow", bm, M_ARROW)
# kite
KITE = empty("Kite")
bm = bmesh.new(); vs = [bm.verts.new(v) for v in [(0, 0, 1.6), (1.1, 0, 0.3), (0, 0, -2.2), (-1.1, 0, 0.3)]]; bm.faces.new(vs)
bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.06); mesh_obj("KiteSail", bm, M_KITE, KITE)
bm = bmesh.new(); add_bar(bm, (0, 0, -2.2), (-0.6, 0, -5.0), 0.06); mesh_obj("KiteTail", bm, M_KITE, KITE)
KITE.scale = (3.5, 3.5, 3.5)

# ================= cable-end set (separate, far out over the sea behind the camera) =================
SET = Vector((0.0, -400.0, 30.0))
RS = 0.5
HEX = [(0, 0)]
for ring in range(1, 5):
    q, r_ = ring, 0
    dirs = [(-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0), (0, 1)]
    for dq, dr in dirs:
        for _ in range(ring): HEX.append((q, r_)); q += dq; r_ += dr
HEXP = [((q + r_ / 2.0) * 2 * RS, r_ * math.sqrt(3) / 2 * 2 * RS) for q, r_ in HEX]
RING = [max(abs(q), abs(r_), abs(-q - r_)) for q, r_ in HEX]
assert len(HEXP) == 61
def compact(px, pz):
    r = math.hypot(px, pz)
    if r < 1e-6: return 0.0, 0.0
    th = math.atan2(pz, px)
    rv = 4 * 2 * RS                                                     # corner strand distance
    bound = rv * math.cos(math.pi / 6) / math.cos((th % (math.pi / 3)) - math.pi / 6)
    k = (3.62 / bound) if r > 0 else 1.0
    return px * k, pz * k
STR = []
for i, (px, pz) in enumerate(HEXP):
    o = empty(f"Strand{i}", (SET.x + px, SET.y, SET.z + pz))
    bm = bmesh.new(); add_cyl(bm, RS * 0.98, 60.0, "Y", (0, -30.0, 0), seg=20); sm = mesh_obj(f"StrandM{i}", bm, [M_SHEATH], o)
    bm = bmesh.new(); add_cyl(bm, RS * 0.985, 0.02, "Y", (0, 0.005, 0), seg=20); mesh_obj(f"StrandFace{i}", bm, M_FACE, o)
    STR.append((o, px, pz, RING[i]))
WRAP = lathe("CableWrap", tube_prof(4.12, 4.45, 0.0, 60.0), M_SHEATH, ang=2 * math.pi, seg=64)
WRAP.rotation_euler = (math.radians(90), 0, 0); WRAP.location = (SET.x, SET.y, SET.z)   # +z of the lathe -> -y
BAR = box("DiameterBar", -4.45, 4.45, 0.15, 0.35, -0.12, 0.12, M_GOLD); BAR.location = (SET.x, SET.y, SET.z - 5.3)
BARTICKS = []
for s in (-1, 1): BARTICKS.append(box(f"BarTick{s}", s * 4.45 - 0.12, s * 4.45 + 0.12, 0.15, 0.35, -0.7, 0.7, M_GOLD)); BARTICKS[-1].location = (SET.x, SET.y, SET.z - 5.3)

# ================= timing =================
T_HOOK2 = C["spun"] - 0.05          # hard cut: cable end -> whole bridge
T_CUT0, T_CUT1 = C["cut"], C["cut"] + 0.75
T_SITE = C["first"] - 0.05          # hard cut: the empty site
T_AR0, T_AR1 = C["anchorages"], C["anchorages"] + 1.0
T_EY0, T_EY1 = C["eyebars"] - 0.35, C["eyebars"] + 0.35
T_TW0, T_TW1 = C["towers"], C["rise"] + 1.0
T_SAD = C["saddle"] - 0.1
T_K0, T_K1 = C["n1848"] - 0.1, C["kite"] + 0.35
T_R0, T_R1 = C["heavier"], C["ropes"] + 0.6
T_W0, T_W1 = C["catwalk"] - 0.35, C["sky"] + 0.5
T_S0, T_S1 = C["wheel"] - 0.1, C["wire"] + 0.4    # first trip, anchorage to anchorage
T_HOOK = C["hooked"]
T_B0, T_B1 = C["back"] - 0.3, C["more"] + 0.3      # fast return trip
T_M0, T_M1 = T_B1, C["wires2"] - 0.25              # montage: shuttling, the cable grows
T_SET = C["wires2"] - 0.15                         # hard cut: cable-end set
T_SQ0, T_SQ1 = C["squeezed"], C["round"] + 0.2
T_WRAP = C["round"]
T_BAR = C["about"] - 0.05
T_NOROAD = C["but"] - 0.05
T_CTA = C["would"] - 0.1

def s_wheel(t):
    if t < T_S0: return 0.0
    if t < T_S1: return ease((t - T_S0) / (T_S1 - T_S0)) * 0.6 + lin((t - T_S0) / (T_S1 - T_S0)) * 0.4
    if t < T_B0: return 1.0
    if t < T_B1: return 1.0 - ease((t - T_B0) / (T_B1 - T_B0))
    if t < T_M1:
        ph = ((t - T_M0) / 0.9) % 2.0
        return ph if ph <= 1.0 else 2.0 - ph
    return 0.0
# anchorages: whole in the hook, drop out of sight for the empty site, rise on "anchorages"
for s, root in ANCH.items():
    bake_fn(root, "location", 2, lambda t: 6.0 if t < T_SITE else 6.0 - 28.0 * (1 - ease((t - T_AR0) / (T_AR1 - T_AR0))))
windows(ANCH_NEAR, [(0, T_CUT1 + 0.05), (T_SITE, T_EY1 + 0.05)])
def near_slide(t):
    if t < T_SITE: p = ease((t - T_CUT0) / (T_CUT1 - T_CUT0))
    else: p = ease((t - T_EY0) / (T_EY1 - T_EY0))
    return p
bake_fn(ANCH_NEAR, "location", 1, lambda t: -26.0 * near_slide(t))
bake_fn(ANCH_NEAR, "location", 2, lambda t: -60.0 * near_slide(t) ** 2)
glow(B_CONC, [(0, 0.0)] + [(C["slip"] - 0.05, 0.0), (C["slip"] + 0.1, 0.0)] + pulse(C["giant"], 0.9, hold=0.9))
glow(B_EYE, [(0, 0.0)] + pulse(T_CUT1 - 0.1, 1.2, hold=0.4) + pulse(C["eyebars"] + 0.1, 2.0, hold=1.2))
windows(ARROW, [(C["pull"] - 0.05, C["eyebars"] - 0.4)])
bake_fn(ARROW, "scale", 0, lambda t: 0.2 + 0.8 * ease((t - C["pull"]) / 0.5)); 
# towers: whole in the hook, gone for the site, rise on "towers"
for root in TOWERS:
    windows(root, [(0, T_SITE), (T_TW0, DUR)])
    bake_fn(root, "scale", 2, lambda t: 1.0 if t < T_SITE else max(0.02, ease((t - T_TW0) / (T_TW1 - T_TW0))))
for sd in SADDLES:
    windows(sd, [(0, T_SITE), (T_SAD, DUR)])
    for ax in range(3): bake_fn(sd, "scale", ax, lambda t: 1.0 if t < T_SITE else pop(t, T_SAD, 0.3))
glow(B_SADDLE, [(0, 0.0)] + pulse(C["cradle"], 1.6, hold=0.8))
# main cables: done in the hook, then built from the montage on (thin -> full)
for cb in CABLES:
    windows(cb, [(0, T_SITE), (T_M0, DUR)])
    bake_fn(cb.data, "bevel_depth", -1, lambda t: 1.0 if (t < T_SITE or t >= T_M1) else 0.12 + 0.88 * ease((t - T_M0) / (T_M1 - T_M0)))
glow(B_CABLE, [(0, 0.0)] + pulse(C["hangs"], 1.2, hold=1.2) + pulse(C["but"] + 0.2, 0.8, hold=0.6))
# pilot line + kite
windows(PILOT, [(T_K0, T_M0)])
bake_fn(PILOT.data, "bevel_factor_end", -1, lambda t: lin((t - T_K0) / (T_K1 - T_K0)))
windows(KITE, [(T_K0 - 0.3, C["thin"] - 0.1)])
PIL_PTS = [p for p in path(-CY) if abs(p[0]) <= TX]
def kite_pos(t):
    u = lin((t - T_K0) / (T_K1 - T_K0)); x = -TX + 2 * TX * u
    return Vector((x, -CY, TH + 1.0 - 9.0 * math.cos(math.pi * x / (2 * TX)) + 4.0 + 0.8 * math.sin(t * 5)))
for ax in range(3): bake_fn(KITE, "location", ax, lambda t, ax=ax: kite_pos(t)[ax])
bake_fn(KITE, "rotation_euler", 1, lambda t: 0.25 * math.sin(t * 3.1))
# heavier ropes (both sides), catwalk chunks, rails
for rp in ROPES:
    windows(rp, [(T_R0 - 0.05, T_M1)])
    bake_fn(rp.data, "bevel_factor_end", -1, lambda t: lin((t - T_R0) / (T_R1 - T_R0)))
for o, cx in WALK:
    t0 = T_W0 + (T_W1 - T_W0 - 0.3) * (cx + AX) / (2 * AX)
    windows(o, [(t0, DUR)])
for rl in RAILS:
    windows(rl, [(T_W0, DUR)])
    bake_fn(rl.data, "bevel_factor_end", -1, lambda t: lin((t - T_W0) / (T_W1 - T_W0)))
# spinning wheels + live wires
for w, wm, yy in WHEELS:
    windows(w, [(C["spinning"] - 0.1, T_SET)])
    def wpos(t, yy=yy):
        p, a = at_s(s_wheel(t), yy, 1.6); return p, a
    for ax in range(3): bake_fn(w, "location", ax, lambda t, ax=ax, wpos=wpos: wpos(t)[0][ax])
    bake_fn(w, "rotation_euler", 1, lambda t, wpos=wpos: -wpos(t)[1])
    bake_fn(wm, "rotation_euler", 1, lambda t: -s_wheel(t) * TOT / 1.3)
for wr in WIRES:
    windows(wr, [(T_S0, T_M0 + 0.4)])
    bake_fn(wr.data, "bevel_factor_end", -1, lambda t: s_wheel(t) if t < T_S1 else 1.0)
for wr in WIRES2:
    windows(wr, [(T_B0, T_M0 + 0.4)])
    bake_fn(wr.data, "bevel_factor_start", -1, lambda t: s_wheel(t) if t < T_B1 else 0.0)
glow(B_WIRE, [(0, 3.0), (T_HOOK - 0.05, 3.0), (T_HOOK + 0.12, 8.0), (T_HOOK + 0.5, 3.0)])
glow(B_WHEEL, [(0, 0.0)] + pulse(C["wheel"], 1.4, hold=0.5))
# ghost decks
windows(GHOST, [(C["every"] - 0.1, C["lets"] - 0.05)])
keyval(GH_FAC, [(C["every"] - 0.1, 0.0), (C["every"] + 0.3, 0.75), (C["slip"], 0.75), (C["lets"] - 0.1, 0.4)])
windows(GHOST_R, [(C["road"] - 0.4, T_CTA)])
keyval(GHR_FAC, [(C["road"] - 0.4, 0.0), (C["road"] - 0.1, 0.9), (C["road"] + 0.35, 0.9), (T_CTA - 0.05, 0.0)])
# cable-end set: compacted + wrapped in the hook; strands pop in ring by ring, squeeze into a round cable, wrap, diameter bar
def strand_xy(px, pz, t):
    cx, cz = compact(px, pz)
    if t < T_SET: return cx, cz
    p = ease((t - T_SQ0) / (T_SQ1 - T_SQ0)); return px + (cx - px) * p, pz + (cz - pz) * p
for o, px, pz, ring in STR:
    windows(o, [(0, T_HOOK2), (T_SET, T_NOROAD)])
    bake_fn(o, "location", 0, lambda t, px=px, pz=pz: SET.x + strand_xy(px, pz, t)[0])
    bake_fn(o, "location", 2, lambda t, px=px, pz=pz: SET.z + strand_xy(px, pz, t)[1])
    tp = C["wires2"] + 0.05 + ring * 0.2
    for ax in (0, 2): bake_fn(o, "scale", ax, lambda t, tp=tp: 1.0 if t < T_SET else pop(t, tp, 0.25))
windows(WRAP, [(0, T_HOOK2), (T_WRAP, T_NOROAD)])
bake_fn(WRAP, "location", 1, lambda t: SET.y if t < T_SET else SET.y - 40.0 * (1 - ease((t - T_WRAP) / 0.45)))
glow(B_FACE, [(0, 0.0), (C["wires"] - 0.1, 0.0), (C["wires"] + 0.15, 0.35), (C["spun"] - 0.1, 0.0)] + pulse(C["strands"], 0.35, hold=0.4))
for o in [BAR] + BARTICKS:
    windows(o, [(T_BAR, T_NOROAD)])
    bake_fn(o, "scale", 0, lambda t: pop(t, T_BAR, 0.3))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.3; cam_d.clip_end = 2500
WP = lambda t: at_s(s_wheel(t), -CY, 1.6)[0]
WX = lambda dx: (lambda t: WP(t).x + dx); WZ = lambda dz: (lambda t: WP(t).z + dz)
KP = lambda t: kite_pos(t)
SX, SY, SZ = SET
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (SX + 1.0, SY + 9.0, SZ + 1.2), (SX, SY, SZ), 30),
    (T_HOOK2 - 0.3, (SX + 7.0, SY + 26.0, SZ + 5.0), (SX, SY - 12.0, SZ), 26),
    (T_HOOK2, (-125.0, -95.0, 22.0), (-20.0, 0.0, 44.0), 22, "cut"),
    (C["lets"] - 0.3, (-112.0, -80.0, 26.0), (-25.0, 0.0, 40.0), 22),
    (C["lets"] - 0.15, (-70.0, -62.0, 30.0), (-114.0, -6.0, 14.0), 22, "cut"),
    (T_SITE - 0.02, (-72.0, -60.0, 28.0), (-114.0, -6.0, 13.0), 22),
    (T_SITE, (-66.0, -66.0, 34.0), (-112.0, 0.0, 14.0), 22, "cut"),
    (C["giant"], (-74.0, -58.0, 30.0), (-114.0, -4.0, 14.0), 22),
    (T_EY0 - 0.1, (-112.0, -48.0, 15.0), (-114.0, -5.0, 13.0), 26),
    (C["next"] - 0.1, (-112.0, -42.0, 14.0), (-114.0, -5.0, 13.0), 26),
    (C["next"], (-20.0, -70.0, 8.0), (-55.0, 0.0, 34.0), 20, "cut"),
    (C["saddle"] - 0.6, (-26.0, -60.0, 20.0), (-55.0, 0.0, 52.0), 20),
    (C["cradle"] + 0.2, (-40.0, -26.0, 76.0), (-55.0, -CY, 71.5), 24),
    (C["so"] - 0.05, (-40.0, -25.0, 76.5), (-55.0, -CY, 71.5), 24),
    (C["so"], (0.0, -125.0, 60.0), (0.0, 0.0, 58.0), 22, "cut"),
    (T_K1, (20.0, -80.0, 70.0), (20.0, 0.0, 70.0), 24),
    (C["thin"] - 0.05, (-22.0, -42.0, 64.0), (-45.0, -CY, 66.0), 22, "cut"),
    (C["catwalk"] - 0.4, (-24.0, -40.0, 60.0), (-45.0, -CY, 62.0), 22),
    (C["sky"] + 0.3, (25.0, -70.0, 60.0), (-30.0, 0.0, 50.0), 20),
    (C["spinning"] - 0.05, (-80.0, -38.0, 26.0), (-100.0, -CY, 16.0), 24, "cut"),
    (T_S0, (WX(-16.0), -32.0, WZ(7.0)), (WX(6.0), -CY, WZ(0.0)), 24),
    (T_S1 - 0.6, (WX(-16.0), -32.0, WZ(7.0)), (WX(6.0), -CY, WZ(0.0)), 24),
    (C["loop2"] - 0.1, (88.0, -34.0, 24.0), (104.0, -CY, 15.0), 24, "cut"),
    (T_B0 - 0.05, (89.0, -33.0, 23.0), (104.0, -CY, 15.0), 24),
    (T_B0, (0.0, -165.0, 56.0), (0.0, 0.0, 44.0), 20, "cut"),
    (T_M1, (0.0, -140.0, 52.0), (0.0, 0.0, 46.0), 20),
    (T_SET, (SX + 0.6, SY + 19.0, SZ + 0.6), (SX, SY, SZ), 30, "cut"),
    (T_NOROAD - 0.05, (SX + 1.2, SY + 21.0, SZ + 0.9), (SX, SY, SZ - 0.3), 30),
    (T_NOROAD, (70.0, -150.0, 12.0), (0.0, 0.0, 34.0), 20, "cut"),
    (T_CTA - 0.05, (64.0, -140.0, 14.0), (0.0, 0.0, 34.0), 20),
    (T_CTA, (16.0, -CY - 1.5, cable_z(16.0) + 0.2), (-55.0, -CY - 1.0, 64.0), 18, "cut"),
    (C["end"], (8.0, -CY - 1.5, cable_z(8.0) + 0.2), (-55.0, -CY - 1.0, 64.0), 18),
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
    cam_loc.append(l0 + Vector((0.05 * math.sin(t * 0.7), 0.0, 0.04 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()

# ================= world + light: strait in daylight =================
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
    try: sky.sun_elevation = math.radians(28); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.22
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1); bg.inputs["Strength"].default_value = 0.8
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.2; sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), math.radians(-18), math.radians(-30))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 40; fill_d.energy = 6000; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (10, 14, 0)

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
def anch_z(t): return 6.0 if t < T_SITE else 6.0 - 28.0 * (1 - ease((t - T_AR0) / (T_AR1 - T_AR0)))
ANCHP = {
    "anchorage": lambda t: Vector((-AX - 13.0, -14.0, anch_z(t) + AH)),
    "eyebars": lambda t: Vector((-AX - 12.0, -CY + 1.2, anch_z(t) + 8.0)),
    "tower": lambda t: Vector((-TX, -CY - 2.2, 4.0 + 40.0 * max(0.02, ease((t - T_TW0) / (T_TW1 - T_TW0))) if t >= T_SITE else 44.0)),
    "saddle": lambda t: Vector((-TX, -CY - 1.8, TH)),
    "kite": lambda t: kite_pos(t),
    "rope": lambda t: Vector((-35.0, -CY, cable_z(-35.0) - 0.4)),
    "catwalk": lambda t: Vector((-28.0, -CY - 1.7, cable_z(-28.0) - 1.7)),
    "wheel": lambda t: WP(t) + Vector((0, 0, 1.4)),
    "cable": lambda t: Vector((-20.0, -CY, cable_z(-20.0))),
    "strand": lambda t: Vector((SX + strand_xy(HEXP[30][0], HEXP[30][1], t)[0], SY, SZ + strand_xy(HEXP[30][0], HEXP[30][1], t)[1])),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook2": round(T_HOOK2, 3), "cut": R3(T_CUT0, T_CUT1), "site": round(T_SITE, 3), "anch_rise": R3(T_AR0, T_AR1),
          "eyecut": R3(T_EY0, T_EY1), "tower_rise": R3(T_TW0, T_TW1), "saddle": round(T_SAD, 3), "kite": R3(T_K0, T_K1),
          "ropes": R3(T_R0, T_R1), "walk": R3(T_W0, T_W1), "trip1": R3(T_S0, T_S1), "hook": round(T_HOOK, 3), "trip2": R3(T_B0, T_B1),
          "montage": R3(T_M0, T_M1), "passes": [round(T_M0 + 0.9 * k, 3) for k in range(int((T_M1 - T_M0) / 0.9) + 1)],
          "set": round(T_SET, 3), "rings": [round(C["wires2"] + 0.05 + k * 0.2, 3) for k in range(5)], "squeeze": R3(T_SQ0, T_SQ1),
          "wrap": round(T_WRAP, 3), "bar": round(T_BAR, 3), "noroad": round(T_NOROAD, 3), "cta": round(T_CTA, 3)}
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
