# Ships-Float-3D: why a giant steel ship floats (Archimedes / displacement, load line, ballast tanks, watertight compartments).
# Blender Cycles, real-world setting: open sea in daylight, cut along the ship's centre line (section plane y = 0, camera on -y).
# One set: a container ship (no brand, no people) as a half model so the section shows thin steel plates around mostly air:
# bottom + inner bottom (the double bottom = ballast tanks), side shell, deck, 6 watertight bulkheads, stern deckhouse, propeller.
# The sea is cut too (boolean with the hull volume, so no water inside the hull). A near-half cover (hull + near sea) is in place for the
# hook and slides away on "cut". Beats: solid steel block sinks to the bed; the same steel becomes a hull that settles at its waterline
# (weight arrow vs buoyancy arrow, displaced-water ghost); containers load, the load-line mark on the far hull side (S -> F in fresh water);
# empty ship with the propeller half out, ballast tanks fill; a hole floods one compartment; four flood and it still floats; one more and it goes.
# Illustrative scale: plates drawn ~10x thick, the ship shortened, the load-line mark drawn oversize.
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
CUES = [("cargo", "cargo"), ("steel", "steel"), ("almost", "almost"), ("eight", "eight"), ("denser", "denser"), ("floats", "floats"), ("but", "but"),
        ("flood", "flood"), ("wrong", "wrong"), ("down", "down"), ("fast", "fast"), ("lets", "let's"), ("cut", "cut"),
        ("drop", "drop"), ("solid", "solid"), ("block", "block"), ("sea", "sea"), ("sinks", "sinks"), ("water", "water"),
        ("pushes", "pushes"), ("up", "up"), ("weight", "weight"), ("water2", "water"), ("shoves", "shoves"), ("aside", "aside"),
        ("small", "small"), ("little", "little"), ("weight2", "weight"), ("wins", "wins"), ("now", "now"), ("spread", "spread"),
        ("steel2", "steel"), ("giant", "giant"), ("hollow", "hollow"), ("hull", "hull"), ("inside", "inside"), ("mostly", "mostly"),
        ("air", "air"), ("ship", "ship"), ("sinks2", "sinks"), ("lower", "lower"), ("until", "until"), ("water3", "water"),
        ("weighs", "weighs"), ("exactly", "exactly"), ("ship2", "ship"), ("then", "then"), ("stops", "stops"), ("thats", "that's"),
        ("weight3", "weight"), ("displacement", "displacement"), ("load", "load"), ("containers", "containers"), ("sinks3", "sinks"),
        ("deeper", "deeper"), ("load2", "load"), ("line", "line"), ("hull2", "hull"), ("marks", "marks"), ("safely", "safely"),
        ("fresh", "fresh"), ("less", "less"), ("even", "even"), ("deeper2", "deeper"), ("empty", "empty"), ("high", "high"),
        ("propeller", "propeller"), ("half", "half"), ("water4", "water"), ("pumps", "pumps"), ("seawater", "seawater"),
        ("ballast", "ballast"), ("tanks", "tanks"), ("low", "low"), ("and", "and"), ("hull3", "hull"), ("hole", "hole"),
        ("steel3", "steel"), ("walls", "walls"), ("watertight", "watertight"), ("compartments", "compartments"),
        ("fills", "fills"), ("one", "one"), ("titanic", "titanic"), ("float", "float"), ("four", "four"), ("flooded", "flooded"),
        ("iceberg", "iceberg"), ("opened", "opened"), ("more", "more"), ("would", "would"), ("ocean", "ocean"), ("mostly2", "mostly"),
        ("tell", "tell"), ("next", "next"), ("spin", "spin"), ("cables", "cables"), ("follow", "follow")]
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
CL = coll("Ship")

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

# ================= materials =================
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
def hull_paint(name, inner=True):
    """Hull: red antifouling below the boot-top line (ship-local z 4.4), dark navy above (object coords = ship coords)."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])
    gt = N.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 4.4; L.new(sp.outputs["Z"], gt.inputs[0])
    paint = mix_rgb(nt, gt.outputs[0], (0.36, 0.05, 0.035), (0.03, 0.06, 0.13))
    if inner:
        sn = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Normal"], sn.inputs[0])
        a1 = N.new("ShaderNodeMath"); a1.operation = "LESS_THAN"; a1.inputs[1].default_value = -0.5; L.new(sn.outputs["Y"], a1.inputs[0])
        a2 = N.new("ShaderNodeMath"); a2.operation = "GREATER_THAN"; a2.inputs[1].default_value = 0.5; L.new(sn.outputs["Z"], a2.inputs[0])
        mxm = N.new("ShaderNodeMath"); mxm.operation = "MAXIMUM"; L.new(a1.outputs[0], mxm.inputs[0]); L.new(a2.outputs[0], mxm.inputs[1])
        paint = mix_rgb(nt, mxm.outputs[0], paint, (0.30, 0.32, 0.34))
    L.new(paint, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.45; b.inputs["Metallic"].default_value = 0.15
    b.inputs["Emission Color"].default_value = (1.0, 0.3, 0.24, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b

M_HULL, B_HULL = hull_paint("Hull"); M_COVER, B_COVER = hull_paint("HullCover", inner=False)
M_STEEL, B_STEEL = mat("Steel", (0.30, 0.32, 0.34), 0.5, 0.6, emit_rgb=(0.98, 0.74, 0.27))
M_BULK, B_BULK = mat("Bulkhead", (0.36, 0.38, 0.40), 0.5, 0.5, emit_rgb=(0.98, 0.74, 0.27))
M_DECK = mat("Deck", (0.20, 0.27, 0.22), 0.7)[0]
M_BLOCK, B_BLOCK = mat("SteelBlock", (0.42, 0.44, 0.46), 0.32, 1.0, emit_rgb=(1.0, 0.3, 0.24))
M_WHITE = mat("White", (0.85, 0.85, 0.82), 0.4)[0]
M_WIN = mat("Window", (0.02, 0.03, 0.04), 0.1)[0]
M_PROP, B_PROP = mat("Propeller", (0.75, 0.55, 0.22), 0.25, 1.0, emit_rgb=(1.0, 0.3, 0.24))
CONT = [mat(f"Box{i}", c, 0.55)[0] for i, c in enumerate([(0.55, 0.12, 0.06), (0.06, 0.22, 0.45), (0.65, 0.48, 0.10), (0.12, 0.35, 0.20), (0.45, 0.45, 0.47), (0.60, 0.25, 0.08)])]
M_RED, B_RED = mat("RedArrow", (0.6, 0.05, 0.03), 0.4, emit_rgb=(1.0, 0.30, 0.24)); B_RED.inputs["Emission Strength"].default_value = 5.0
M_CYAN, B_CYAN = mat("CyanArrow", (0.05, 0.4, 0.5), 0.3, emit_rgb=(0.30, 0.92, 1.0)); B_CYAN.inputs["Emission Strength"].default_value = 5.0
M_PAINT = mat("LoadLinePaint", (0.92, 0.92, 0.88), 0.5, emit_rgb=(0.98, 0.74, 0.27))
M_PAINT, B_PAINT = M_PAINT
M_GASH, B_GASH = mat("Gash", (0.05, 0.01, 0.01), 0.8, emit_rgb=(1.0, 0.30, 0.24))
M_SAND = ground("Seabed", (0.30, 0.26, 0.18), (0.45, 0.39, 0.27), 0.08)
M_MOTE = mat("Mote", (0.7, 0.85, 0.9), 0.5, emit_rgb=(0.6, 0.9, 1.0))[0]
M_SEA, B_SEA, V_SEA = water_sec("SeaWater")
M_TANK, B_TANK, _ = water_sec("BallastWater", dens=0.12)
M_FLOOD, B_FLOOD, _ = water_sec("FloodWater", glow_rgb=(1.0, 0.30, 0.24), vol_rgb=(0.45, 0.10, 0.08), dens=0.25)
M_SURF, B_SURF = surf_mat("SeaSurface")
M_AIR, AIR_FAC = ghost("AirGhost", (0.85, 0.95, 1.0))
M_DISP, DISP_FAC = ghost("DisplacedWater", (0.30, 0.92, 1.0))
M_GHB, GHB_FAC = ghost("GhostBlock", (0.30, 0.92, 1.0))

# ================= ship geometry (ship-local: keel z 0, deck z D, bow +x, section plane y 0) =================
D, T = 8.0, 0.3                     # depth, plate thickness (exaggerated so the section reads)
IB = 1.3                            # inner bottom (top of the double-bottom ballast tanks)
XS, XB_ = -30.0, 31.0               # transom, bow tip
def wid(x):
    if x < -24.0: return 4.4 + 0.6 * (x - XS) / 6.0
    if x <= 20.0: return 5.0
    u = min(1.0, (x - 20.0) / (XB_ - 20.0)); return max(0.0, 5.0 * math.sqrt(max(0.0, 1.0 - u ** 2.2)))
XSAMP = [XS + 0.0] + [XS + k * 0.5 for k in range(1, int((XB_ - XS) / 0.5))] + [XB_]
def outline(inset=0.0, x0=XS, x1=XB_, ymin=0.0, mirror=False):
    xs = [x for x in XSAMP if x0 - 1e-6 <= x <= x1 + 1e-6]
    if xs[0] > x0: xs = [x0] + xs
    if xs[-1] < x1: xs = xs + [x1]
    top = [(x, max(ymin + 0.02, wid(x) - inset)) for x in xs]
    low = [(x, -max(ymin + 0.02, wid(x) - inset)) for x in reversed(xs)] if mirror else [(x, ymin) for x in reversed(xs)]
    return top + low
def prism(name, poly, z0, z1, m_, parent=None):
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, z0)) for x, y in poly]; f = bm.faces.new(vb)
    r = bmesh.ops.extrude_face_region(bm, geom=[f]); vt = [v for v in r["geom"] if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=vt, vec=(0, 0, z1 - z0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, m_, parent)
SHIP = empty("Ship")
PARTS = {}
def part(o, key_=None):
    o.parent = SHIP; o.matrix_parent_inverse = Matrix.Identity(4)
    if key_: PARTS.setdefault(key_, []).append(o)
    return o
# hull shell, cut at the section plane y = 0 (the far half stays)
part(prism("Bottom", outline(), 0.0, T, M_HULL), "bottom")
side = outline(0.0) [:len([x for x in XSAMP])]                                  # outer edge (x, w)
side_in = [(x, max(0.02, wid(x) - T)) for x, _ in reversed(side)]
part(prism("SideShell", side + side_in, 0.0, D, M_HULL), "side")
part(box("Transom", XS, XS + T, 0.0, wid(XS), 0.0, D, M_HULL), "side")
part(prism("InnerBottom", outline(T, XS + T, XB_ - 1.0), IB, IB + T, M_STEEL), "inner")
part(prism("Deck", outline(0.0), D - T, D, M_DECK), "deck")
XBH = [-22.0, -12.0, -2.0, 8.0, 18.0, 26.0]                                     # watertight bulkheads
for i, xb in enumerate(XBH):
    part(box(f"Bulkhead{i}", xb - 0.16, xb + 0.16, 0.0, wid(xb) - T, T, D - T, M_BULK), "bulk")
# compartments from the bow: C1 26..31, C2 18..26, C3 8..18, C4 -2..8, C5 -12..-2, C6 -22..-12, engine room -30..-22
COMP = [(26.0, XB_ - 0.6), (18.0, 26.0), (8.0, 18.0), (-2.0, 8.0), (-12.0, -2.0), (-22.0, -12.0)]
# deckhouse + funnel at the stern (cut too)
part(box("Deckhouse", -29.5, -23.0, 0.0, 4.2, D, D + 7.5, M_WHITE), "house")
for k in range(4):
    part(box(f"Win{k}", -23.05, -22.95, 0.3, 3.9, D + 1.6 + k * 1.6, D + 2.4 + k * 1.6, M_WIN), "house")
part(box("Bridge", -29.5, -22.0, 0.0, 5.2, D + 7.5, D + 8.6, M_WHITE), "house")
part(box("BridgeWin", -22.05, -21.95, 0.3, 5.0, D + 7.7, D + 8.3, M_WIN), "house")
part(box("Funnel", -29.0, -26.5, 0.4, 2.4, D + 7.5, D + 11.0, M_HULL), "house")
# propeller (whole, not cut) + shaft + rudder
PROP_X, PROP_Z, PROP_R = -31.2, 1.75, 1.45
PROP = empty("Propeller", (PROP_X, 0.0, PROP_Z)); part(PROP, "prop")
bm = bmesh.new(); add_cyl(bm, 0.38, 0.9, "X", (0, 0, 0), 20)
for k in range(4):
    a = k * math.pi / 2
    vs = add_cyl(bm, 0.5, 0.12, "X", (0, 0, 0), 12)
    bmesh.ops.scale(bm, verts=vs, vec=(1.0, 0.8, PROP_R / 0.5 * 0.5)); bmesh.ops.translate(bm, verts=vs, vec=(0, 0, PROP_R * 0.5))
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(18), 3, "Z") @ Matrix.Rotation(0, 3, "X"))
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "X"))
PROPM = mesh_obj("PropBlades", bm, M_PROP, PROP)
part(cyl("Shaft", 0.18, 1.3, "X", (XS - 0.6, 0.0, PROP_Z), M_STEEL), "prop")
part(box("Rudder", XS - 3.0, XS - 2.2, -0.12, 0.12, 0.6, 5.2, M_HULL), "prop")
# containers on deck, far half: 16 bays x 2 rows x 3 tiers, one object per bay (they drop in on "containers")
BAYS = []
random.seed(3)
for k in range(16):
    x0 = -20.5 + k * 2.75
    bm = bmesh.new()
    for row in range(2):
        for tier in range(3):
            if tier == 2 and random.random() < 0.25: continue
            add_box(bm, x0, x0 + 2.55, row * 2.45 + 0.03, row * 2.45 + 2.4, D + tier * 1.32, D + tier * 1.32 + 1.28, random.randrange(len(CONT)))
    o = mesh_obj(f"Bay{k}", bm, CONT); BAYS.append(part(o, "boxes"))
# near-half cover: the uncut near side of the hull + deckhouse + containers (hook only, slides away on "cut")
COVER = empty("Cover"); part(COVER)
def cpart(o): o.parent = COVER; o.matrix_parent_inverse = Matrix.Identity(4); return o
cpart(prism("CoverHull", [(x, 0.0) for x, _ in side] + [(x, -w) for x, w in reversed(side)], 0.0, D - T, M_COVER))
cpart(prism("CoverDeck", [(x, 0.0) for x, _ in side] + [(x, -w) for x, w in reversed(side)], D - T, D, M_DECK))
cpart(box("CoverHouse", -29.5, -23.0, -4.2, 0.0, D, D + 7.5, M_WHITE)); cpart(box("CoverBridge", -29.5, -22.0, -5.2, 0.0, D + 7.5, D + 8.6, M_WHITE))
for k in range(4): cpart(box(f"CoverWin{k}", -23.05, -22.95, -3.9, -0.3, D + 1.6 + k * 1.6, D + 2.4 + k * 1.6, M_WIN))
cpart(box("CoverBridgeWin", -22.05, -21.95, -5.0, -0.3, D + 7.7, D + 8.3, M_WIN))
cpart(box("CoverFunnel", -29.0, -26.5, -2.4, 0.0, D + 7.5, D + 11.0, M_HULL))
bm = bmesh.new(); random.seed(5)
for k in range(16):
    x0 = -20.5 + k * 2.75
    for row in range(2):
        for tier in range(3):
            if tier == 2 and random.random() < 0.25: continue
            add_box(bm, x0, x0 + 2.55, -(row * 2.45 + 2.4), -(row * 2.45 + 0.03), D + tier * 1.32, D + tier * 1.32 + 1.28, random.randrange(len(CONT)))
cpart(mesh_obj("CoverBoxes", bm, CONT))
# load line ("Plimsoll") mark on the OUTSIDE of the far hull side (seen from the far side in the load-line beat), x ~ 4
S_DRAFT, F_DRAFT = 5.0, 5.38
LLX, LLY = 4.0, 5.0 + 0.03
LL = empty("LoadLine", (LLX, LLY, S_DRAFT)); part(LL, "loadline")
bm = bmesh.new()
for k in range(40):                               # ring (flat torus in the XZ plane)
    a0, a1 = 2 * math.pi * k / 40, 2 * math.pi * (k + 1) / 40
    add_bar(bm, (1.0 * math.cos(a0), 0, 1.0 * math.sin(a0)), (1.0 * math.cos(a1), 0, 1.0 * math.sin(a1)), 0.14)
add_box(bm, -1.45, 1.45, -0.04, 0.04, -0.08, 0.08)                     # the line through the ring = summer load line
add_box(bm, 2.2, 2.32, -0.04, 0.04, -0.6, 1.0)                          # vertical ladder
LADDER = [("TF", 0.60), ("F", 0.38), ("T", 0.22), ("S", 0.0), ("W", -0.22)]
for lab, z in LADDER:
    side_ = -1 if lab in ("TF", "F") else 1                             # fresh-water marks point aft (toward the ring), the rest forward
    xa, xb = (2.32, 3.1) if side_ > 0 else (1.42, 2.2)
    add_box(bm, xa, xb, -0.04, 0.04, z - 0.06, z + 0.06)
LLM = mesh_obj("LoadLineMark", bm, M_PAINT, LL); LLM.rotation_euler = (0, 0, math.pi)   # face +y (seen from the far side)
FONT_P = os.path.join(HERE, "..", "..", "pipeline3d", "fonts", "Poppins-ExtraBold.ttf")
try: FONT = bpy.data.fonts.load(os.path.abspath(FONT_P))
except Exception: FONT = None
for lab, z in LADDER:
    cu = bpy.data.curves.new(f"LL_{lab}", "FONT"); cu.body = lab; cu.size = 0.42; cu.extrude = 0.02
    if FONT: cu.font = FONT
    cu.align_x = "LEFT"; cu.align_y = "CENTER"
    o = bpy.data.objects.new(f"LL_{lab}", cu); CL.objects.link(o); o.data.materials.append(M_PAINT)
    o.parent = LL; o.matrix_parent_inverse = Matrix.Identity(4)
    side_ = -1 if lab in ("TF", "F") else 1
    o.location = (-(3.2 if side_ > 0 else 1.3), 0.06, z); o.rotation_euler = (math.radians(90), 0, math.pi)
    if side_ < 0: cu.align_x = "RIGHT"
# hull volume for the water booleans (whole beam, closed), never rendered
HULLVOL = part(prism("HullVolume", outline(0.0, mirror=True), -0.05, D + 0.05, None))
HULLVOL.hide_render = True; HULLVOL.display_type = "WIRE"
# ghost volumes in the section: air inside, displaced water (below the waterline), ballast and flood water
AIRV = part(prism("AirVolume", outline(T + 0.05, -21.8, 25.8, ymin=0.05), IB + T + 0.05, D - T - 0.05, M_AIR))
DISPV = part(prism("DisplacedVolume", outline(0.0, XS, XB_, ymin=0.04), 0.0, 1.0, M_DISP))
TANKS = part(prism("BallastWater", outline(T + 0.02, -21.8, 25.8, ymin=0.03), 0.0, 1.0, M_TANK))
TANKS.location.z = T
FLOODS = []
for i, (x0, x1) in enumerate(COMP):
    o = part(prism(f"Flood{i + 1}", outline(T + 0.02, x0 + 0.17, x1 - 0.17, ymin=0.03), 0.0, 1.0, M_FLOOD)); o.location.z = IB + T; FLOODS.append(o)
# hole in compartment 3: a red-glowing torn patch on the inside of the far side shell, low
bm = bmesh.new(); random.seed(11)
pts = [(12.6 + 1.9 * math.cos(a) * (0.6 + 0.4 * random.random()), 2.6 + 1.0 * math.sin(a) * (0.6 + 0.4 * random.random())) for a in [k * 2 * math.pi / 14 for k in range(14)]]
vs = [bm.verts.new((x, wid(x) - T - 0.02, z)) for x, z in pts]; bm.faces.new(vs)
GASH = part(mesh_obj("Hole", bm, M_GASH))

# ================= sea =================
SEA_Z0 = -24.0
WATER_FAR = box("SeaFar", -400, 400, 0.0, 400, SEA_Z0, -0.07, M_SEA)
SURF_FAR = box("SurfaceFar", -400, 400, 0.0, 400, -0.06, 0.0, M_SURF)
WATER_NEAR = box("SeaNear", -400, 400, -400, 0.0, SEA_Z0, 0.0, M_SURF)
NEAR = empty("NearSea"); WATER_NEAR.parent = NEAR; WATER_NEAR.matrix_parent_inverse = Matrix.Identity(4)
for o in (WATER_FAR, SURF_FAR, WATER_NEAR):
    md = o.modifiers.new("HullCut", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = HULLVOL
    for s_ in ("EXACT", "MANIFOLD", "FLOAT"):
        try: md.solver = s_; break
        except Exception: continue
box("Seabed", -400, 400, -400, 400, SEA_Z0 - 3.0, SEA_Z0, M_SAND)
random.seed(21)
for k in range(14):                                   # a few rocks on the bed
    x, y = random.uniform(30, 95), random.uniform(1.5, 30)
    o = cyl(f"Rock{k}", random.uniform(0.4, 1.4), random.uniform(0.4, 1.0), "Z", (x, y, SEA_Z0 + 0.2), M_SAND, seg=7)
# drifting motes in the water (depth reference in the sinking-block shot)
bm = bmesh.new()
for k in range(160):
    vs = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.03, 0.07))["verts"]
    bmesh.ops.translate(bm, verts=vs, vec=(random.uniform(48, 74), random.uniform(0.4, 9.0), random.uniform(SEA_Z0 + 0.5, -0.5)))
MOTES = mesh_obj("Motes", bm, M_MOTE)

# ================= timing (video seconds) =================
T_BLK = C["drop"] - 0.1                      # hard cut: the steel block (ship parked out of the sea)
T_BUILD = C["now"] - 0.05                    # hard cut: the same steel becomes a hull
T_CUT0, T_CUT1 = C["cut"] + 0.1, C["cut"] + 0.85
T_SINK0, T_SINK1 = C["sinks2"] - 0.05, C["ship2"]
T_LOAD0 = C["containers"] - 0.1
T_LL = C["load2"] - 0.15                     # hard cut to the far side (load line)
T_EMPTY = C["empty"] - 0.12                  # hard cut: empty ship
T_BAL0, T_BAL1 = C["pumps"], C["low"] + 0.3
T_HOLE = C["hole"]
T_FL3_0, T_FL3_1 = C["fills"] - 0.3, C["one"] + 0.6
T_TI0, T_TI1 = C["titanic"] + 0.2, C["flooded"] + 0.1
T_MORE0, T_MORE1 = C["opened"] - 0.2, C["would"] - 0.15
T_CTA = C["would"] - 0.1
DRAFT_E, DRAFT_B, DRAFT_L = 1.8, 3.6, 5.0
BAY_T = [T_LOAD0 + 0.07 * k for k in range(16)]
def ship_z(t):
    if t < T_BLK: return -DRAFT_L + PW([(C["wrong"], 0.0), (C["fast"] + 0.2, -1.6), (C["lets"] - 0.35, -1.6), (C["lets"], 0.0)])(t)
    if t < T_BUILD: return 60.0
    if t < T_LOAD0 + 0.3: return PW([(T_SINK0, 1.0), (T_SINK1, -DRAFT_E - 0.18), (T_SINK1 + 0.6, -DRAFT_E + 0.08), (C["stops"], -DRAFT_E)])(t)
    if t < T_EMPTY: return PW([(T_LOAD0 + 0.3, -DRAFT_E), (BAY_T[-1] + 0.6, -DRAFT_L), (C["fresh"], -DRAFT_L), (C["deeper2"] + 0.3, -F_DRAFT)])(t)
    if t < T_CTA: return PW([(T_BAL0, -DRAFT_E), (T_BAL1, -DRAFT_B), (T_FL3_0, -DRAFT_B), (T_FL3_1, -4.2), (T_TI0, -4.2), (T_TI1, -5.3),
                             (T_MORE0, -5.3), (T_MORE1, -9.0)])(t)
    return -DRAFT_L
def ship_pitch(t):                            # degrees, + = bow down
    if t < T_BLK: return PW([(C["wrong"], 0.0), (C["fast"] + 0.2, 4.0), (C["lets"] - 0.35, 4.0), (C["lets"], 0.0)])(t)
    if T_EMPTY <= t < T_CTA: return PW([(T_FL3_0, 0.0), (T_FL3_1, 0.8), (T_TI0, 0.8), (T_TI1, 3.5), (T_MORE0, 3.5), (T_MORE1, 11.0)])(t)
    return 0.0
bake_fn(SHIP, "location", 2, ship_z)
bake_fn(SHIP, "rotation_euler", 1, lambda t: math.radians(ship_pitch(t)))
bake_fn(PROP, "rotation_euler", 0, lambda t: t * 5.0)
# build-up: hull parts pop in (scale about the ship origin), the block flattens first
T_B = {"bottom": C["spread"] + 0.35, "side": C["steel2"] + 0.1, "bulk": C["giant"] + 0.15, "inner": C["hollow"] - 0.1,
       "deck": C["hull"] - 0.05, "house": C["hull"] + 0.25, "prop": C["hull"] + 0.35}
for k_, objs in PARTS.items():
    if k_ in T_B:
        for o in objs:
            if k_ == "boxes": continue
            for ax in range(3): bake_fn(o, "scale", ax, lambda t, t0=T_B[k_]: 1.0 if (t < T_BUILD or t >= C["inside"]) else pop(t, t0, 0.35))
# containers: in the hook, drop in on "containers", gone while empty (and while the ship is being built), back for the CTA
for k, o in enumerate(BAYS):
    windows(o, [(0, T_BLK), (BAY_T[k], T_EMPTY), (T_CTA, DUR)])
    bake_fn(o, "location", 2, lambda t, t0=BAY_T[k]: drop(t, t0, 9.0, 0.35) if T_BUILD < t < T_EMPTY else 0.0)
# cover + near sea: in place for the hook, slide toward the camera and drop away on "cut"
windows(COVER, [(0, T_CUT1 + 0.1)])
bake_fn(COVER, "location", 1, lambda t: -26.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)))
bake_fn(COVER, "location", 2, lambda t: -18.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)) ** 2)
windows(NEAR, [(0, T_CUT1 + 0.1)])
bake_fn(NEAR, "location", 1, lambda t: -40.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)))
bake_fn(NEAR, "location", 2, lambda t: -30.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)))
glow(B_COVER, [(0, 0.0)] + pulse(C["flood"], 1.6, up=0.3, hold=1.6, down=0.6))
glow(B_HULL, [(0, 0.0)] + pulse(C["flood"], 1.6, up=0.3, hold=1.6, down=0.6) + pulse(C["more"] - 0.4, 1.2, up=0.3, hold=0.6, down=0.4))
# steel block: drops in on "drop", sinks slowly to the bed, lands on "wins"; reappears at the surface on "now" and flattens into the hull
BLK_X, BLK_Y, BS = 60.0, 3.0, 2.4
BLOCK = box("SteelBlock", -BS / 2, BS / 2, -BS / 2, BS / 2, -BS / 2, BS / 2, M_BLOCK); BLOCK.location = (BLK_X, BLK_Y, 0)
T_LAND = C["wins"] + 0.05
def block_z(t):
    if t < T_BLK + 0.2: return 9.0
    if t < C["solid"] + 0.4: return 9.0 - (9.0 + 1.0) * lin((t - T_BLK - 0.2) / (C["solid"] + 0.4 - T_BLK - 0.2)) ** 2
    return -1.0 + (SEA_Z0 + BS / 2 + 1.0) * lin((t - C["solid"] - 0.4) / (T_LAND - C["solid"] - 0.4)) ** 0.85
bake_fn(BLOCK, "location", 2, block_z)
windows(BLOCK, [(T_BLK, T_BUILD)])
FLAT = box("SteelFlat", -BS / 2, BS / 2, -BS / 2, BS / 2, -BS / 2, BS / 2, M_BLOCK); FLAT.location = (2.0, 2.5, 4.0)
windows(FLAT, [(T_BUILD, T_B["bottom"] + 0.2)])
for ax, s1 in ((0, 14.0), (1, 1.6), (2, 0.08)):
    bake_fn(FLAT, "scale", ax, lambda t, s1=s1: 1.0 + (s1 - 1.0) * ease((t - C["spread"]) / 0.4))
bake_fn(FLAT, "location", 2, lambda t: 4.0 - 3.6 * ease((t - C["spread"]) / 0.4))
GHB = box("DisplacedBlock", -BS / 2, BS / 2, -BS / 2, BS / 2, -BS / 2, BS / 2, M_GHB); GHB.location = (BLK_X + 4.2, BLK_Y, 0)
bake_fn(GHB, "location", 2, block_z)
windows(GHB, [(C["shoves"] - 0.1, T_BUILD)])
keyval(GHB_FAC, [(C["shoves"] - 0.1, 0.0), (C["shoves"] + 0.2, 0.85), (C["little"], 0.85), (C["little"] + 0.3, 0.5)])
windows(MOTES, [(T_BLK, T_BUILD)])
# arrows (flat, in front of the section plane): shaft (unit box scaled to the length) + head
def arrow(name, m_, w):
    bm = bmesh.new(); add_box(bm, -w / 2, w / 2, -0.08, 0.08, 0.0, 1.0); sh = mesh_obj(name + "Shaft", bm, m_)
    bm = bmesh.new(); hw, hh = w * 1.9, w * 2.2
    vs = [bm.verts.new(p) for p in [(-hw, -0.08, 0), (hw, -0.08, 0), (0, -0.08, hh), (-hw, 0.08, 0), (hw, 0.08, 0), (0, 0.08, hh)]]
    for f in ([0, 1, 2], [5, 4, 3], [0, 3, 4, 1], [1, 4, 5, 2], [2, 5, 3, 0]): bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hd = mesh_obj(name + "Head", bm, m_)
    return sh, hd, hh
def drive_arrow(a, x, y, base_fn, len_fn, up=True, wins=None):
    sh, hd, hh = a; s = 1 if up else -1
    for o in (sh, hd):
        o.location.x, o.location.y = x, y; o.rotation_euler = (0, 0 if up else math.pi, 0)
        if wins: windows(o, wins)
    bake_fn(sh, "location", 2, base_fn)
    bake_fn(sh, "scale", 2, lambda t: max(0.01, len_fn(t) - hh))
    bake_fn(hd, "location", 2, lambda t: base_fn(t) + s * max(0.01, len_fn(t) - hh))
    bake_fn(hd, "scale", 0, lambda t: 1.0 if len_fn(t) > hh * 1.5 else 0.6)
W_BLK = arrow("BlockWeight", M_RED, 0.32); B_BLKA = arrow("BlockBuoy", M_CYAN, 0.22)
drive_arrow(W_BLK, BLK_X - 0.6, -0.3, lambda t: block_z(t) + 0.2, lambda t: 4.4, up=False, wins=[(C["weight"] - 0.05, T_BUILD)])
drive_arrow(B_BLKA, BLK_X + 0.6, -0.3, lambda t: block_z(t) - BS / 2 - 0.62, lambda t: 0.62, up=True, wins=[(C["pushes"] - 0.05, T_BUILD)])
W_SHIP = arrow("ShipWeight", M_RED, 0.55); B_SHIP = arrow("ShipBuoy", M_CYAN, 0.55)
ARROW_L = 6.0
drive_arrow(W_SHIP, -4.0, -0.4, lambda t: ship_z(t) + D + 0.3 + ARROW_L, lambda t: ARROW_L, up=False, wins=[(C["ship"] - 0.05, C["thats"] - 0.1)])
drive_arrow(B_SHIP, 4.0, -0.4, lambda t: ship_z(t) - ARROW_L * lin(-ship_z(t) / DRAFT_E) - 0.2,
            lambda t: max(0.3, ARROW_L * lin(-ship_z(t) / DRAFT_E)), up=True, wins=[(C["ship"] - 0.05, C["thats"] - 0.1)])
# ghosts: air (pulse on "air" and in the CTA on "mostly"), displaced water (scale z = draft) while the ship settles
keyval(AIR_FAC, [(0, 0.0), (C["inside"] - 0.1, 0.0), (C["air"], 0.22), (C["ship"] + 0.4, 0.22), (C["sinks2"] + 0.3, 0.0),
                 (C["mostly2"] - 0.2, 0.0), (C["mostly2"] + 0.3, 0.2), (C["tell"] + 0.6, 0.2), (C["tell"] + 1.4, 0.06)])
windows(AIRV, [(C["inside"] - 0.1, C["sinks2"] + 0.4), (C["mostly2"] - 0.2, DUR)])
windows(DISPV, [(C["water3"] - 0.1, C["load"] - 0.1)])
bake_fn(DISPV, "scale", 2, lambda t: max(0.01, -ship_z(t)))
keyval(DISP_FAC, [(C["water3"] - 0.1, 0.0), (C["water3"] + 0.25, 0.6), (C["displacement"] - 0.05, 0.6), (C["displacement"] + 0.2, 0.95), (C["load"] - 0.1, 0.95)])
# ballast tanks fill (pumps), stay full until the CTA
windows(TANKS, [(T_BAL0, T_CTA)])
bake_fn(TANKS, "scale", 2, lambda t: max(0.01, (IB - T) * ease((t - T_BAL0) / (T_BAL1 - T_BAL0))))
glow(B_TANK, [(0, 0.0)] + pulse(C["ballast"], 1.2, hold=0.9))
# flooding: C3 through the hole, then C1, C2, C4 ("four flooded"), then C5 ("opened more")
FL_LEVEL = {2: (T_FL3_0, T_FL3_1, 4.0), 0: (T_TI0, T_TI1, 5.0), 1: (T_TI0 + 0.2, T_TI1, 5.0), 3: (T_TI0 + 0.4, T_TI1 + 0.2, 5.0), 4: (T_MORE0, T_MORE1, 6.2)}
for i, o in enumerate(FLOODS):
    if i in FL_LEVEL:
        a, b, h = FL_LEVEL[i]
        windows(o, [(a, T_CTA)])
        bake_fn(o, "scale", 2, lambda t, a=a, b=b, h=h: max(0.01, (h - IB - T) * ease((t - a) / (b - a))))
    else: windows(o, [])
glow(B_FLOOD, [(0, 0.4), (C["more"] - 0.3, 0.4), (C["more"], 2.5), (C["would"], 2.5)])
windows(GASH, [(T_HOLE - 0.05, T_CTA)])
glow(B_GASH, [(T_HOLE - 0.05, 0.0), (T_HOLE + 0.1, 8.0), (T_HOLE + 0.6, 3.0)])
glow(B_BULK, [(0, 0.0)] + pulse(C["walls"], 2.5, hold=0.4) + pulse(C["watertight"], 3.0, hold=0.8))
glow(B_PROP, [(0, 0.0)] + pulse(C["propeller"], 2.0, hold=0.9))
glow(B_PAINT, [(0, 0.0)] + pulse(C["line"], 1.5, hold=0.8))
glow(B_BLOCK, [(0, 0.0)] + pulse(C["weight2"], 1.0, hold=0.5))
# fresh water: the sea turns a little greener and clearer for the fresh-water beat
for t, rgb in ((0, (0.02, 0.12, 0.20)), (C["fresh"] - 0.05, (0.02, 0.12, 0.20)), (C["fresh"] + 0.4, (0.05, 0.16, 0.13)), (T_EMPTY - 0.05, (0.05, 0.16, 0.13)), (T_EMPTY, (0.02, 0.12, 0.20))):
    B_SURF.inputs["Base Color"].default_value = (*rgb, 1); B_SURF.inputs["Base Color"].keyframe_insert("default_value", frame=F(t))
windows(LL, [(T_LL - 0.05, T_EMPTY)])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.3; cam_d.clip_end = 1500
ORBA = lambda t: math.radians(-48 + 26 * lin((t - T_CTA) / (DUR - T_CTA)))
ORX = lambda t: 2.0 + 56 * math.sin(ORBA(t)); ORY = lambda t: -56 * math.cos(ORBA(t))
BZ = lambda t: block_z(t)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (16.0, -50.0, 8.0), (2.0, 0.0, 4.0), 24),
    (C["but"] - 0.2, (13.0, -42.0, 6.5), (3.0, 0.0, 3.0), 24),
    (C["fast"] + 0.4, (12.0, -40.0, 6.0), (5.0, 0.0, 1.0), 24),
    (C["lets"] - 0.1, (12.0, -40.0, 6.0), (4.0, 0.0, 1.5), 24),
    (T_CUT1 + 0.2, (16.0, -36.0, 6.0), (4.0, 0.0, 1.5), 26),
    (T_BLK, (BLK_X + 1.0, -24.0, lambda t: BZ(t) + 2.0), (BLK_X + 1.0, 0.0, BZ), 30, "cut"),
    (C["shoves"] - 0.3, (BLK_X + 1.5, -24.0, lambda t: BZ(t) + 2.0), (BLK_X + 1.5, 0.0, BZ), 30),
    (C["shoves"], (BLK_X + 2.2, -28.0, lambda t: BZ(t) + 2.5), (BLK_X + 2.2, 0.0, BZ), 30),
    (T_BUILD - 0.01, (BLK_X + 2.2, -28.0, lambda t: BZ(t) + 2.5), (BLK_X + 2.2, 0.0, BZ), 30),
    (T_BUILD, (34.0, -60.0, 26.0), (0.0, 0.0, 3.0), 26, "cut"),
    (C["inside"] - 0.3, (30.0, -56.0, 23.0), (0.0, 0.0, 3.0), 26),
    (C["inside"] - 0.25, (14.0, -20.0, 6.0), (10.0, 2.0, 4.5), 24, "cut"),
    (C["ship"] - 0.4, (13.0, -19.0, 5.5), (10.0, 2.0, 4.0), 24),
    (C["ship"] - 0.35, (1.0, -32.0, 3.5), (0.0, 0.0, 1.0), 24, "cut"),
    (C["thats"] - 0.3, (0.5, -30.0, 2.0), (0.0, 0.0, 0.0), 24),
    (C["load"] - 0.2, (14.0, -36.0, 10.0), (2.0, 0.0, 4.0), 24),
    (T_LL - 0.2, (12.0, -34.0, 9.0), (2.0, 0.0, 3.0), 24),
    (T_LL, (LLX - 0.9, 15.5, 1.0), (LLX - 0.9, 5.0, 0.25), 34, "cut"),
    (C["fresh"] - 0.3, (LLX - 0.9, 14.0, 0.8), (LLX - 0.9, 5.0, 0.1), 34),
    (T_EMPTY - 0.01, (LLX - 0.9, 13.5, 0.7), (LLX - 0.9, 5.0, 0.0), 34),
    (T_EMPTY, (-24.0, -17.0, 2.0), (-29.5, 0.0, 1.0), 26, "cut"),
    (C["seawater"] - 0.3, (-24.5, -18.0, 2.0), (-29.5, 0.0, 0.5), 26),
    (C["seawater"] - 0.25, (1.0, -34.0, 2.0), (0.0, 0.0, -0.5), 24, "cut"),
    (C["and"] - 0.3, (2.0, -33.0, 2.0), (1.0, 0.0, -1.0), 24),
    (C["and"] - 0.25, (14.0, -24.0, 2.0), (12.0, 2.0, 0.0), 24, "cut"),
    (C["steel3"] - 0.2, (13.5, -25.0, 2.0), (12.0, 2.0, -0.5), 24),
    (C["watertight"], (9.0, -44.0, 3.0), (8.0, 0.0, -1.0), 24),
    (C["titanic"] - 0.3, (10.0, -45.0, 3.0), (9.0, 0.0, -1.5), 24),
    (T_MORE1, (13.0, -48.0, 2.0), (11.0, 0.0, -3.5), 24),
    (T_CTA, (ORX, ORY, 16.0), (2.0, 0.0, 2.0), 26, "cut"),
    (C["end"], (ORX, ORY, 16.0), (2.0, 0.0, 2.0), 26),
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

# ================= world + light: open-sea daylight =================
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
    try: sky.sun_elevation = math.radians(32); sky.sun_rotation = math.radians(210)
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
sun.rotation_euler = (math.radians(50), math.radians(-20), math.radians(-25))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 40; fill_d.energy = 9000; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (10, 14, 0)

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
def ship_pt(t, x, y, z):
    """World position of a ship-local point at time t (pitch about the keel origin)."""
    a = math.radians(ship_pitch(t)); zz = ship_z(t)
    return Vector((x * math.cos(a) + z * math.sin(a), y, zz - x * math.sin(a) + z * math.cos(a)))
ANCH = {
    "block": lambda t: Vector((BLK_X, BLK_Y - 1.2, block_z(t))),
    "ghost": lambda t: Vector((BLK_X + 4.2, BLK_Y - 1.2, block_z(t))),
    "hull": lambda t: ship_pt(t, 22.0, 0.0, 2.0),
    "weight": lambda t: ship_pt(t, -4.0, -0.4, D + 0.3 + ARROW_L * 0.6),
    "air": lambda t: ship_pt(t, 12.0, 2.0, 4.8),
    "disp": lambda t: ship_pt(t, -8.0, 2.0, 0.6),
    "loadline": lambda t: ship_pt(t, LLX, LLY, S_DRAFT + 1.0),
    "prop": lambda t: ship_pt(t, PROP_X, 0.0, PROP_Z),
    "tanks": lambda t: ship_pt(t, 0.0, 1.0, 0.8),
    "bulk": lambda t: ship_pt(t, 8.0, 0.0, 6.0),
    "hole": lambda t: ship_pt(t, 12.6, 3.5, 2.6),
    "comp": lambda t: ship_pt(t, 13.0, 1.0, 4.5),
}
anchors = {k: [] for k in ANCH}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):   # build_cover.py re-uses this scene and skips the export
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cut": R3(T_CUT0, T_CUT1), "block": round(T_BLK, 3), "splash": round(C["solid"] + 0.4, 3), "land": round(T_LAND, 3),
          "build": {k: round(v, 3) for k, v in T_B.items()}, "settle": R3(T_SINK0, T_SINK1), "bays": [round(b, 3) for b in BAY_T],
          "loadline": round(T_LL, 3), "fresh": R3(C["fresh"], C["deeper2"] + 0.3), "empty": round(T_EMPTY, 3), "ballast": R3(T_BAL0, T_BAL1),
          "hole": round(T_HOLE, 3), "flood3": R3(T_FL3_0, T_FL3_1), "flood4": R3(T_TI0, T_TI1), "more": R3(T_MORE0, T_MORE1), "cta": round(T_CTA, 3)}
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
