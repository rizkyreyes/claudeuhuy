# Nuclear-Power-Plant-3D: how a nuclear power plant makes electricity (it boils water). Blender Cycles.
# Real-world set: a generic pressurized-water-reactor plant on flat ground in daylight (no logos, no people): containment dome,
# reactor vessel with fuel assemblies + control rods, pressurizer, steam generator (U-tubes), turbine hall (turbine, generator,
# condenser), power line, hyperbolic cooling tower with a vapor plume, a few houses for the CTA.
# Cutaway: the containment, the vessel, steam generator, pressurizer, turbine casing and condenser are cut at y = 0 (only the far
# halves exist inside); the near half of the containment slides away on "cut".
# Two studio sets far from the plant: SET (x = 400) a fuel pellet next to a heap of coal, a glass tube that fills with pellets and is
# sealed into a fuel rod, then a 17 x 17 fuel assembly that grows around it; MICRO (x = -400) a uranium nucleus split by a neutron.
# Illustrative scale: plant 1 unit = 1 m (dimensions generic); SET is 10x real size (pellet ~1 cm -> 1 unit; the coal heap ~1.15 m3
# -> ~1150 units3; rod pitch 12.6 mm -> 1.26); rod and assembly lengths are cut short; the fission nucleus is a cartoon.
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
CUES = [("nuclear", "nuclear"), ("plant", "plant"), ("giant", "giant"), ("kettle", "kettle."), ("all", "all"), ("uranium", "uranium"),
        ("boils", "boils"), ("if", "if"), ("water", "water"), ("stops", "stops"), ("flowing", "flowing,"), ("core", "core"),
        ("melt", "melt,"), ("partly", "partly"), ("three", "three"), ("y1979", "1979."), ("lets", "let's"), ("cut", "cut"),
        ("open", "open."), ("starts", "starts"), ("pellet", "pellet"), ("gummy", "gummy"), ("one", "one"), ("pellet2", "pellet"),
        ("energy", "energy"), ("ton", "ton"), ("coal", "coal."), ("theyre", "they're"), ("stacked", "stacked"), ("sealed", "sealed"),
        ("tubes", "tubes"), ("fuel", "fuel"), ("rods", "rods,"), ("over", "over"), ("two", "two"), ("hundred", "hundred"),
        ("assembly", "assembly."), ("in", "in"), ("core2", "core,"), ("uranium2", "uranium"), ("atoms", "atoms"), ("split", "split,"),
        ("releasing", "releasing"), ("heat", "heat."), ("control", "control"), ("slide", "slide"), ("in2", "in"), ("out", "out."),
        ("soak", "soak"), ("neutrons", "neutrons,"), ("pushing", "pushing"), ("slows", "slows"), ("stops2", "stops"), ("now", "now"),
        ("water2", "water."), ("twothirds", "two-thirds"), ("reactors", "reactors,"), ("around", "around"), ("six", "six"),
        ("fahrenheit", "fahrenheit,"), ("never", "never"), ("boils2", "boils."), ("squeezed", "squeezed"), ("twentytwo", "twenty-two"),
        ("psi", "psi."), ("that", "that"), ("hot", "hot"), ("tubes2", "tubes"), ("steam", "steam"), ("generator", "generator"),
        ("boils3", "boils"), ("second", "second,"), ("separate", "separate"), ("clean", "clean"), ("steam2", "steam"), ("blasts", "blasts"),
        ("turbine", "turbine,"), ("spins", "spins"), ("generator2", "generator,"), ("electricity", "electricity."), ("then", "then"),
        ("cooled", "cooled"), ("pumped", "pumped"), ("again", "again."), ("towers", "towers?"), ("just", "just"), ("vapor", "vapor,"),
        ("third", "third"), ("never2", "never"), ("touches", "touches"), ("would", "would"), ("live", "live"), ("tell", "tell"),
        ("next", "next"), ("hole", "hole"), ("well", "well."), ("follow", "follow")]
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
CL = coll("NuclearPlant")
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


# ================= timing =================
T_IN0 = C["all"] - 0.05                 # hook: inside (near half hidden)
T_EXT = C["lets"] - 0.05                # exterior again, then the cut
T_CUT0, T_CUT1 = C["cut"], C["open"] + 0.45
T_SET0 = C["starts"] - 0.25             # pellet set
T_HEAP = C["ton"] - 0.05
T_ROD0 = C["theyre"] - 0.05             # rod set
DROP_T = [C["stacked"] - 0.15 + k * 0.075 for k in range(12)]
T_CAP = C["sealed"] + 0.15
T_METAL = C["tubes"]
ROW_T = [C["two"] - 0.1 + i * 0.07 for i in range(17)]
T_NOZ = C["assembly"] - 0.1
T_CORE0 = C["in"] - 0.05
T_MIC0, T_MIC1 = C["uranium2"] - 0.05, C["heat"] - 0.1
T_HIT, T_SPLIT = C["atoms"] + 0.15, C["split"]
T_WATER = C["now"] - 0.05
T_HOT = C["that"] - 0.05
T_TURB = C["steam2"] - 0.1
T_COND = C["then"] - 0.05
T_TOW = C["towers"] - 0.62
T_LOOPS = C["third"] - 0.05
T_CTA = C["would"] - 0.05
def near_x(t):
    """The near half slides off to the left (x), never toward the camera."""
    if t < T_CUT0 or t >= T_CTA: return 0.0
    return -48.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0))
NEAR_WINS = [(0, T_IN0), (T_EXT, T_CUT1 + 0.6), (T_CTA, DUR)]
ROD_KEYS = [(0, 0.0), (C["slide"], 0.0), (C["in2"] + 0.2, -2.6), (C["out"], -2.6), (C["out"] + 0.45, 0.0), (C["pushing"], 0.0),
            (C["slows"] + 0.2, -2.2), (C["stops2"] - 0.1, -2.2), (C["stops2"] + 0.5, -4.2)]
_rods = PW(ROD_KEYS)
def rods_z(t): return 0.0 if t >= T_WATER else _rods(t)
def vlevel(t):                          # vessel water height scale (drops for "stops flowing ... melt")
    if t >= T_EXT: return 1.0
    return PW([(C["stops"], 1.0), (C["melt"] + 0.3, 0.42)])(t)

# ================= materials =================
def emis(name, rgb, strength=6.0):
    m, b = mat(name, rgb, 0.4, 0.0, emit_rgb=rgb); b.inputs["Emission Strength"].default_value = strength; return m
def ecol(bsdf, keys):
    inp = bsdf.inputs["Emission Color"]
    for t, rgb in keys:
        inp.default_value = (*rgb, 1); inp.keyframe_insert("default_value", frame=F(t))
GOLD, RED, CYAN, WHITE_E, ORANGE = (1.0, 0.74, 0.27), (1.0, 0.30, 0.24), (0.30, 0.92, 1.0), (1.0, 0.97, 0.90), (1.0, 0.48, 0.14)
M_CONC, _ = mat("Concrete", (0.55, 0.55, 0.53), 0.85, noise=0.8)
M_FLOOR, _ = mat("PlantFloor", (0.22, 0.22, 0.23), 0.8)
M_STEEL, _ = mat("Steel", (0.45, 0.47, 0.50), 0.35, 0.85)
M_VES, B_VES = mat("VesselSteel", (0.32, 0.33, 0.36), 0.40, 0.85, emit_rgb=GOLD)
M_SG, _ = mat("SGSteel", (0.56, 0.58, 0.61), 0.35, 0.80)
M_PZR, B_PZR = mat("Pressurizer", (0.56, 0.58, 0.61), 0.35, 0.80, emit_rgb=GOLD)
M_PRI, B_PRI = mat("PrimaryPipe", (0.50, 0.50, 0.52), 0.30, 0.85, emit_rgb=RED)
M_SEC, B_SEC = mat("SecondaryPipe", (0.80, 0.80, 0.78), 0.40, 0.30, emit_rgb=WHITE_E)
M_COOL, B_COOL = mat("CoolingPipe", (0.22, 0.42, 0.58), 0.40, 0.30, emit_rgb=CYAN)
M_UT, B_UT = mat("UTubes", (0.80, 0.50, 0.30), 0.30, 0.90, emit_rgb=ORANGE)
M_CR, B_CR = mat("ControlRod", (0.10, 0.10, 0.11), 0.30, 0.80, emit_rgb=CYAN)
M_TURB, B_TURB = mat("Rotor", (0.78, 0.80, 0.82), 0.25, 0.95, emit_rgb=WHITE_E)
M_CASE, _ = mat("Casing", (0.26, 0.40, 0.52), 0.50, 0.40)
M_GEN, B_GEN = mat("Generator", (0.18, 0.30, 0.27), 0.45, 0.50, emit_rgb=GOLD)
M_WIRE, B_WIRE = mat("Wire", (0.10, 0.10, 0.10), 0.40, 0.60, emit_rgb=GOLD)
M_HALL, _ = mat("HallWall", (0.55, 0.62, 0.68), 0.70)
M_TOWER, _ = mat("TowerConcrete", (0.74, 0.73, 0.70), 0.90, noise=0.3)
M_HOUSE, _ = mat("HouseWall", (0.86, 0.82, 0.74), 0.80)
M_ROOF, _ = mat("Roof", (0.30, 0.17, 0.14), 0.70)
M_WIN, _ = mat("Window", (0.06, 0.08, 0.10), 0.10, 0.20)
M_TRUNK, _ = mat("Trunk", (0.18, 0.11, 0.06), 0.90)
M_LEAF, _ = mat("Leaves", (0.10, 0.22, 0.07), 0.80, noise=2.0)
M_PELLET, B_PEL = mat("Pellet", (0.07, 0.07, 0.075), 0.55, 0.30, emit_rgb=GOLD)
M_COAL, _ = mat("Coal", (0.018, 0.018, 0.02), 0.28, 0.10, noise=3.0)
M_ZR, B_ZR = mat("Zircaloy", (0.62, 0.64, 0.66), 0.30, 0.90, emit_rgb=GOLD)
M_GRID, _ = mat("GridSteel", (0.70, 0.72, 0.74), 0.30, 0.90)
M_PROT, B_PROT = mat("Proton", (0.75, 0.12, 0.08), 0.35, 0.0, emit_rgb=ORANGE)
M_NEUT, B_NEUT = mat("Neutron", (0.55, 0.56, 0.60), 0.35, 0.0, emit_rgb=ORANGE)
M_DOT_R, M_DOT_W, M_DOT_C, M_DOT_N = emis("DotRed", RED, 8), emis("DotWhite", WHITE_E, 6), emis("DotCyan", CYAN, 7), emis("DotNeutron", (0.6, 0.9, 1.0), 10)
M_BUB, B_BUB = mat("Bubble", (0.92, 0.97, 1.0), 0.05, 0.0, emit_rgb=WHITE_E); B_BUB.inputs["Emission Strength"].default_value = 1.5
def glass(name):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.9, 0.97, 1.0, 1); b.inputs["Roughness"].default_value = 0.04
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.45
    return m
M_GLASS = glass("Glass")
def fuel_mat(name):
    """Cut face of the core: vertical bright rod lines (bands along x) on dark steel, emission keyable (gold = heat, red = melt)."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 9.0; wv.inputs["Distortion"].default_value = 0.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.3; mr.inputs[2].default_value = 0.6; L.new(wv.outputs["Fac"], mr.inputs[0])
    col = mix_rgb(nt, mr.outputs[0], (0.05, 0.05, 0.055), (0.55, 0.56, 0.58))
    L.new(col, b.inputs["Base Color"]); b.inputs["Metallic"].default_value = 0.8; b.inputs["Roughness"].default_value = 0.35
    b.inputs["Emission Color"].default_value = (*GOLD, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
M_FUEL, B_FUEL = fuel_mat("FuelCore")
M_STUDIO_F = tiles("StudioFloor", (0.045, 0.045, 0.05), (0.06, 0.06, 0.066), 0.25, "XY")
M_STUDIO_W = tiles("StudioWall", (0.035, 0.035, 0.04), (0.05, 0.05, 0.055), 0.08, "XZ")
for m_ in (M_STUDIO_F, M_STUDIO_W): next(n for n in m_.node_tree.nodes if n.type == "TEX_BRICK").inputs["Mortar"].default_value = (0.015, 0.015, 0.02, 1)
M_WATER, B_WATER, _va = water_sec("VesselWater", glow_rgb=CYAN)
M_WATER2, B_WATER2, _va2 = water_sec("SecondaryWater", glow_rgb=WHITE_E)
M_POND, _ = mat("Pond", (0.03, 0.10, 0.14), 0.08)
def plume_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree; N, L = nt.nodes, nt.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL": N.remove(n)
    out = next(n for n in N if n.type == "OUTPUT_MATERIAL")
    vs = N.new("ShaderNodeVolumePrincipled"); vs.inputs["Color"].default_value = (0.97, 0.98, 1.0, 1); vs.inputs["Density"].default_value = 0.10
    vs.inputs["Emission Color"].default_value = (0.9, 0.93, 0.97, 1)
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.6; nz.inputs["Detail"].default_value = 4
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    # soft edge: density falls off with distance from the sphere centre, broken up by noise
    vl = N.new("ShaderNodeVectorMath"); vl.operation = "LENGTH"; L.new(tc.outputs["Object"], vl.inputs[0])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.55; mr.inputs[2].default_value = 1.0; mr.inputs[3].default_value = 1.0; mr.inputs[4].default_value = 0.0
    L.new(vl.outputs["Value"], mr.inputs[0])
    mul = N.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; L.new(mr.outputs[0], mul.inputs[0]); L.new(nz.outputs["Fac"], mul.inputs[1])
    mul2 = N.new("ShaderNodeMath"); mul2.operation = "MULTIPLY"; mul2.inputs[1].default_value = 0.22; L.new(mul.outputs[0], mul2.inputs[0])
    L.new(mul2.outputs[0], vs.inputs["Density"]); L.new(mul.outputs[0], vs.inputs["Emission Strength"]); L.new(vs.outputs[0], out.inputs["Volume"])
    return m
M_PLUME = plume_mat("Plume")

# ================= geometry helpers (pipes, spheres) =================
def add_seg(bm, p0, p1, r, seg=16, mi=0):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L_ = d.length
    if L_ < 1e-4: return
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L_)
    M = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=res["verts"])
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def add_ball(bm, c, r, mi=0, seg=12):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg * 2 // 3), radius=r)
    bmesh.ops.translate(bm, verts=res["verts"], vec=Vector(c))
    for f in {f for v in res["verts"] for f in v.link_faces}: f.material_index = mi
def pipe(name, pts, r, m_, parent=None):
    bm = bmesh.new()
    for a, b in zip(pts, pts[1:]): add_seg(bm, a, b, r)
    for p in pts[1:-1]: add_ball(bm, p, r * 1.02)
    o = mesh_obj(name, bm, m_, parent)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def ball(name, c, r, m_, seg=16):
    bm = bmesh.new(); add_ball(bm, (0, 0, 0), r, seg=seg); o = mesh_obj(name, bm, m_); o.location = c
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def path_pt(pts, s):
    """Point at arc length s along a polyline (clamped)."""
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b); L_ = (b - a).length
        if s <= L_: return a.lerp(b, s / L_ if L_ else 0)
        s -= L_
    return Vector(pts[-1])
def path_len(pts): return sum((Vector(b) - Vector(a)).length for a, b in zip(pts, pts[1:]))
DOTS = []
def dots(name, pts, n, speed, wins, m_, r=0.24):
    L_ = path_len(pts); me = None
    for k in range(n):
        if me is None:
            bm = bmesh.new(); add_ball(bm, (0, 0, 0), r, seg=10); o = mesh_obj(f"{name}{k}", bm, m_); me = o.data
        else:
            o = bpy.data.objects.new(f"{name}{k}", me); CL.objects.link(o)
        vals = [path_pt(pts, (speed * t + k * L_ / n) % L_) for t in TS]
        for ax in range(3): bake(o, "location", ax, [v[ax] for v in vals])
        windows(o, wins); DOTS.append(o)
def lift(pts, dy=0.0, dz=0.0): return [(p[0], p[1] + dy, p[2] + dz) for p in pts]

# ================= ground, pad, sky props =================
gbm = bmesh.new(); add_box(gbm, -1200, 1200, -1200, 1200, -2, 0); G_ = mesh_obj("Ground", gbm, ground("Grass", (0.10, 0.16, 0.06), (0.20, 0.24, 0.10), 0.04))
box("Pad", -24, 62, -36, 32, 0, 0.06, M_FLOOR)
box("Road", -24, 140, -48, -42, 0, 0.04, mat("Asphalt", (0.05, 0.05, 0.055), 0.8)[0])

# ================= containment (cut at y = 0; near half slides away) =================
VX, PZX, SGX = -5.0, -11.0, 6.0
NEAR = empty("NearHalf")
arc = [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 91, 6)]
cprof = [(15.0, 0.0), (16.2, 0.0)] + [(max(0.02, 16.2 * c), 22.0 + 16.2 * s) for c, s in arc] + [(max(0.02, 15.0 * c), 22.0 + 15.0 * s) for c, s in reversed(arc)]
CONT_FAR = lathe("ContainmentFar", cprof, M_CONC, a0=0.0, ang=math.pi, seg=48)
CONT_NEAR = lathe("ContainmentNear", cprof, M_CONC, a0=math.pi, ang=math.pi, seg=48)
CONT_NEAR.parent = NEAR; CONT_NEAR.matrix_parent_inverse = Matrix.Identity(4)
half_cyl("InnerFloor", 15.0, 0.0, 0.0, 0.0, 0.0, 1.0, M_FLOOR)
nfl = bmesh.new(); add_cyl(nfl, 15.0, 1.0, "Z", (0, 0, 0.5), 48); geom = list(nfl.verts) + list(nfl.edges) + list(nfl.faces)
bmesh.ops.bisect_plane(nfl, geom=geom, plane_co=(0, 0, 0), plane_no=(0, -1, 0), clear_inner=True)
mesh_obj("InnerFloorNear", nfl, M_FLOOR, NEAR)
bake_fn(NEAR, "location", 0, near_x)
windows(NEAR, NEAR_WINS)
# biological shield (concrete cavity around the vessel), far half
box("ShieldBack", VX - 3.6, VX + 3.6, 3.0, 3.6, 1.0, 11.0, M_CONC)
box("ShieldL", VX - 3.6, VX - 3.0, 0.0, 3.0, 1.0, 11.0, M_CONC)
box("ShieldR", VX + 3.0, VX + 3.6, 0.0, 3.0, 1.0, 11.0, M_CONC)
box("OperatingDeckBack", -14.5, 14.5, 9.0, 14.0, 11.0, 11.6, M_CONC)

# ================= reactor vessel, core, control rods, water =================
vout = [(0.02, 1.6), (1.6, 1.8), (2.4, 2.4), (2.6, 3.2), (2.6, 12.8), (2.4, 13.6), (1.6, 14.2), (0.02, 14.4)]
vin = [(0.02, 14.1), (1.5, 13.9), (2.15, 13.4), (2.3, 12.8), (2.3, 3.2), (2.15, 2.6), (1.5, 2.1), (0.02, 1.9)]
VES = lathe("Vessel", vout + vin, M_VES, a0=0.0, ang=math.pi, seg=40, loc=(VX, 0, 0))
cbm = bmesh.new()
for i in range(7):
    for j in range(3):
        x0 = VX - 1.68 + i * 0.48; y0 = 0.0 + j * 0.48
        if math.hypot(abs(x0 - VX) + 0.44, y0 + 0.44) > 2.25: continue
        add_box(cbm, x0, x0 + 0.44, y0, y0 + 0.44, 4.0, 8.0)
CORE = mesh_obj("Core", cbm, M_FUEL)
# core barrel + support plates (thin)
box("CorePlateLow", VX - 1.9, VX + 1.9, 0.0, 1.8, 3.6, 3.85, M_STEEL); box("CorePlateTop", VX - 1.9, VX + 1.9, 0.0, 1.8, 8.15, 8.3, M_STEEL)
CRG = empty("ControlRods", (VX, 0, 0))
rbm = bmesh.new()
for x in (-1.2, -0.72, -0.24, 0.24, 0.72, 1.2):
    add_box(rbm, x - 0.07, x + 0.07, 0.30, 0.66, 8.35, 12.55)           # absorber blade (out: above the core)
    add_box(rbm, x - 0.03, x + 0.03, 0.44, 0.52, 12.55, 18.6)           # drive shaft up through the head
add_box(rbm, -1.3, 1.3, 0.38, 0.58, 12.5, 12.75)                        # spider
mesh_obj("ControlRodBlades", rbm, M_CR, CRG)
bake_fn(CRG, "location", 2, rods_z)
for x in (-1.2, -0.72, -0.24, 0.24, 0.72, 1.2): box(f"CRDM{x}", VX + x - 0.09, VX + x + 0.09, 0.38, 0.58, 14.4, 17.2, M_STEEL)
wbm = bmesh.new(); add_cyl(wbm, 2.26, 10.6, "Z", (0, 0, 5.3), 40); cut_front(wbm, 0.0)
VWATER = mesh_obj("VesselWater", wbm, M_WATER); VWATER.location = (VX, 0, 2.2)
bake_fn(VWATER, "scale", 2, vlevel)
# pressurizer (far half) + heaters + water, surge line
pzp = [(1.1, 3.6)] + [(1.1 * math.cos(math.radians(a)), 15.0 + 1.1 * math.sin(math.radians(a))) for a in range(0, 91, 15)][:-1] + [(0.02, 16.1), (0.02, 15.95)] + \
      [(0.95 * math.cos(math.radians(a)), 15.0 + 0.95 * math.sin(math.radians(a))) for a in range(90, -1, -15)][1:] + [(0.95, 3.75), (0.02, 3.75), (0.02, 3.6)]
PZR = lathe("Pressurizer", pzp, M_PZR, a0=0.0, ang=math.pi, seg=32, loc=(PZX, 0, 0))
pw = bmesh.new(); add_cyl(pw, 0.93, 6.2, "Z", (0, 0, 3.1), 32); cut_front(pw, 0.0); o = mesh_obj("PzrWater", pw, M_WATER); o.location = (PZX, 0, 3.8)
hbm = bmesh.new()
for x in (-0.5, -0.25, 0.0, 0.25, 0.5): add_seg(hbm, (x, 0.4, 3.8), (x, 0.4, 6.0), 0.05)
o = mesh_obj("PzrHeaters", hbm, M_UT); o.location = (PZX, 0, 0)
box("PzrSkirt", PZX - 1.0, PZX + 1.0, 0.0, 1.2, 1.0, 3.6, M_STEEL)
pipe("SurgeLine", [(PZX + 0.5, 0.7, 3.7), (PZX + 0.5, 0.7, 2.6), (VX - 2.45, 0.7, 2.6), (VX - 2.45, 0.7, 3.4)], 0.22, M_PRI)

# ================= steam generator (far half), U-tubes, secondary water, bubbles =================
sgo = [(0.02, 1.0), (1.2, 1.1), (1.6, 1.6), (1.6, 9.0), (2.1, 11.0), (2.1, 17.0)] + [(2.1 * math.cos(math.radians(a)), 17.0 + 2.1 * math.sin(math.radians(a))) for a in range(15, 91, 15)][:-1] + [(0.02, 19.1)]
sgi = [(0.02, 18.95)] + [(1.95 * math.cos(math.radians(a)), 17.0 + 1.95 * math.sin(math.radians(a))) for a in range(75, 0, -15)] + [(1.95, 17.0), (1.95, 11.05), (1.45, 9.05), (1.45, 1.7), (1.1, 1.25), (0.02, 1.15)]
SG = lathe("SteamGenerator", sgo + sgi, M_SG, a0=0.0, ang=math.pi, seg=36, loc=(SGX, 0, 0))
tsb = bmesh.new(); add_cyl(tsb, 1.46, 0.45, "Z", (0, 0, 3.45), 32); cut_front(tsb, 0.0); o = mesh_obj("TubeSheet", tsb, M_STEEL); o.location = (SGX, 0, 0)
ubm = bmesh.new()
for yy in (0.25, 0.6, 0.95, 1.25):
    for d in (0.28, 0.56, 0.84, 1.12):
        if math.hypot(d, yy) > 1.38: continue
        top = 9.0 + d * 0.5; prev = None
        pts = [(-d, yy, 3.7), (-d, yy, top)] + [(-d * math.cos(math.radians(a)), yy, top + d * math.sin(math.radians(a))) for a in range(15, 166, 15)] + [(d, yy, top), (d, yy, 3.7)]
        for a, b in zip(pts, pts[1:]): add_seg(ubm, a, b, 0.075, seg=8)
UT = mesh_obj("UTubes", ubm, M_UT); UT.location = (SGX, 0, 0)
swb = bmesh.new(); add_cyl(swb, 1.43, 7.3, "Z", (0, 0, 3.65), 32); cut_front(swb, 0.0); o = mesh_obj("SGWater", swb, M_WATER2); o.location = (SGX, 0, 3.7)
BUB_WINS = [(C["boils"] - 0.25, T_IN0 + 2.5), (C["boils3"] - 0.1, T_TURB), (T_LOOPS, T_CTA)]
bub_me = None
for k in range(46):
    if bub_me is None:
        bm = bmesh.new(); add_ball(bm, (0, 0, 0), 0.11, seg=8); bo = mesh_obj("Bubble0", bm, M_BUB); bub_me = bo.data
    else:
        bo = bpy.data.objects.new(f"Bubble{k}", bub_me); CL.objects.link(bo)
    bx, by, ph, sp = SGX + random.uniform(-1.25, 1.25), random.uniform(0.12, 1.3), random.random(), random.uniform(2.2, 3.4)
    bake_fn(bo, "location", 0, lambda t, bx=bx: bx + 0.06 * math.sin(t * 7 + bx))
    bo.location.y = by
    bake_fn(bo, "location", 2, lambda t, ph=ph, sp=sp: 3.9 + ((t * sp / 8.4 + ph) % 1.0) * 8.4)
    s_ = random.uniform(0.6, 1.5); bo.scale = (s_, s_, s_)
    windows(bo, BUB_WINS)
# primary loop: hot leg (front, y 0.7), cold leg (back, y 1.6) with the coolant pump
HOT_PTS = [(VX + 2.45, 0.75, 9.4), (1.6, 0.75, 9.4), (1.6, 0.75, 2.3), (SGX - 1.5, 0.75, 2.3)]
COLD_PTS = [(SGX - 1.5, 1.6, 1.9), (-0.4, 1.6, 1.9), (-0.4, 1.6, 5.2), (VX + 2.45, 1.6, 5.2)]
pipe("HotLeg", HOT_PTS, 0.42, M_PRI); pipe("ColdLeg", COLD_PTS, 0.38, M_PRI)
full_cyl("CoolantPump", 0.62, -0.4, 1.6, 2.4, 4.2, M_STEEL); full_cyl("CoolantPumpMotor", 0.48, -0.4, 1.6, 4.2, 5.0, M_CASE)
# secondary: steam line SG top -> through the wall -> turbine; feedwater condenser -> SG
STEAM_PTS = [(SGX, 1.0, 18.9), (SGX, 1.0, 20.6), (25.6, 1.0, 20.6), (25.6, 1.0, 10.2), (27.6, 1.0, 10.2)]
FEED_PTS = [(29.0, 2.6, 0.9), (9.2, 2.6, 0.9), (9.2, 2.6, 13.0), (SGX + 2.05, 2.6, 13.0)]
pipe("SteamLine", STEAM_PTS, 0.46, M_SEC); pipe("Feedwater", FEED_PTS, 0.34, M_SEC)
full_cyl("FeedPump", 0.55, 19.0, 2.6, 0.2, 1.7, M_CASE)

# ================= turbine hall: turbine (cut casing), rotor, generator, condenser =================
box("HallFloor", 21, 56, 0, 12, 0, 0.3, M_FLOOR)
box("HallBack", 21, 56, 11.5, 12.0, 0, 20, M_HALL)
box("HallRoof", 21, 56, 5.0, 12.0, 19.6, 20.0, M_HALL)
for x in (21.0, 55.6): box(f"HallEnd{x}", x, x + 0.4, 6.0, 12.0, 0, 20, M_HALL)
TX0, TX1, TY, TZ = 26.7, 41.3, 2.4, 8.0
for x0, x1 in ((25.4, 26.8), (40.6, 42.0)): box(f"Pedestal{x0}", x0, x1, 0.6, 4.2, 0.3, 5.9, M_CONC)
box("GenPedestal", 42.4, 48.8, 0.6, 4.2, 0.3, 6.1, M_CONC)
casp = [(1.85, -7.3), (2.0, -7.3), (3.05, 7.3), (2.9, 7.3)]
CASE = lathe("TurbineCasing", casp, M_CASE, a0=0.0, ang=math.pi, seg=40, loc=((TX0 + TX1) / 2, TY, TZ))
CASE.rotation_euler = (0, math.radians(90), 0)
ROT = empty("Rotor", ((TX0 + TX1) / 2, TY, TZ))
rbm = bmesh.new(); add_seg(rbm, (-8.4, 0, 0), (14.0, 0, 0), 0.32, seg=20)
for i in range(8):
    xi = -6.2 + i * 1.75; Ri = 1.0 + i * 0.25
    add_cyl(rbm, 0.55 + i * 0.05, 0.42, "X", (xi, 0, 0), 24)
    for b in range(28):
        a = 2 * math.pi * b / 28; d = Vector((0, math.cos(a), math.sin(a)))
        add_bar(rbm, Vector((xi, 0, 0)) + d * 0.5, Vector((xi, 0, 0)) + d * Ri, 0.07)
mesh_obj("RotorMesh", rbm, M_TURB, ROT)
def rot_speed(t): return 1.2 + 7.0 * ease((t - C["blasts"]) / 1.4)
ang, angs = 0.0, []
for t in TS: angs.append(ang); ang += rot_speed(t) / FPS
bake(ROT, "rotation_euler", 0, angs)
gbm2 = bmesh.new(); add_cyl(gbm2, 1.95, 5.6, "X", (45.6, TY, TZ), 40); add_cyl(gbm2, 2.15, 0.35, "X", (43.0, TY, TZ), 40); add_cyl(gbm2, 2.15, 0.35, "X", (48.2, TY, TZ), 40)
GEN = mesh_obj("Generator", gbm2, M_GEN)
cyl("Exciter", 0.9, 1.6, "X", (49.4, TY, TZ), M_CASE)
# condenser: open-front box under the turbine, cooling-water tubes (cyan), hotwell water
for nm, a in (("CondBack", (28, 40, 5.0, 5.2, 0.3, 5.4)), ("CondL", (28, 28.2, 2.4, 5.2, 0.3, 5.4)), ("CondR", (39.8, 40, 2.4, 5.2, 0.3, 5.4)),
              ("CondBottom", (28, 40, 2.4, 5.2, 0.3, 0.5)), ("CondTop", (28, 40, 2.4, 5.2, 5.2, 5.4))):
    box(nm, *a, M_STEEL)
ctb = bmesh.new()
for yy in (2.9, 3.6, 4.3):
    for zz in (1.7, 2.5, 3.3, 4.1): add_seg(ctb, (28.2, yy, zz), (39.8, yy, zz), 0.2, seg=12)
CTUBES = mesh_obj("CondenserTubes", ctb, M_COOL)
box("Hotwell", 28.2, 39.8, 2.4, 5.0, 0.5, 1.1, M_WATER2)
# power out: transformer, pylon, wires
box("Transformer", 51.0, 54.0, 1.2, 4.2, 0.3, 3.6, M_CASE)
for k in range(3): full_cyl(f"Bushing{k}", 0.12, 51.8 + k * 0.7, 2.7, 3.6, 4.6, M_STEEL)
pyl = bmesh.new(); PYX, PYY = 62.0, -6.0
for sx in (-1, 1):
    for sy in (-1, 1): add_bar(pyl, (PYX + sx * 2.6, PYY + sy * 2.6, 0), (PYX + sx * 0.6, PYY + sy * 0.6, 24.5), 0.22)
for z in (5, 10, 15, 20):
    w_ = 2.6 - 2.0 * z / 24.5
    for a, b in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        add_bar(pyl, (PYX + a[0] * w_, PYY + a[1] * w_, z), (PYX + b[0] * w_, PYY + b[1] * w_, z), 0.12)
add_bar(pyl, (PYX - 6, PYY, 22.5), (PYX + 6, PYY, 22.5), 0.3)
mesh_obj("Pylon", pyl, M_STEEL)
wbm3 = bmesh.new()
for k, x in enumerate((-5.6, 0.0, 5.6)):
    add_seg(wbm3, (51.8 + k * 0.7, 2.7, 4.6), (PYX + x, PYY, 22.2), 0.06, seg=6)
    add_seg(wbm3, (PYX + x, PYY, 22.2), (PYX + x + 160, PYY - 20, 24.0), 0.06, seg=6)
add_seg(wbm3, (48.4, TY, TZ + 1.9), (52.5, 2.7, 3.6), 0.12, seg=8)
WIRES = mesh_obj("PowerWires", wbm3, M_WIRE)

# ================= cooling tower, plume, cooling-water loop =================
TWX, TWY = 76.0, 14.0
rz = lambda z: math.sqrt(10.5 ** 2 + 0.1546 * (z - 34.0) ** 2)
zs = [2.5 + i * 2.0 for i in range(23)] + [46.0]
tprof = [(rz(z), z) for z in zs] + [(rz(z) - 0.45, z) for z in reversed(zs)]
TOWER = lathe("CoolingTower", tprof, M_TOWER, a0=0.0, ang=2 * math.pi, seg=72, loc=(TWX, TWY, 0))
cbm2 = bmesh.new()
for k in range(36):
    a = 2 * math.pi * k / 36; a2 = a + 2 * math.pi / 36; r0 = rz(2.5) - 0.2
    add_bar(cbm2, (TWX + r0 * math.cos(a), TWY + r0 * math.sin(a), 0), (TWX + r0 * math.cos(a2), TWY + r0 * math.sin(a2), 2.7), 0.35)
mesh_obj("TowerColumns", cbm2, M_TOWER)
pnd = bmesh.new(); add_cyl(pnd, rz(0) + 0.6, 0.5, "Z", (TWX, TWY, 0.25), 72); mesh_obj("TowerBasin", pnd, M_CONC)
pw2 = bmesh.new(); add_cyl(pw2, rz(0) - 0.2, 0.1, "Z", (TWX, TWY, 0.5), 72); mesh_obj("TowerPond", pw2, M_POND)
PLUME = []
for k in range(11):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0); o = mesh_obj(f"Plume{k}", bm, M_PLUME)
    ph = k / 11.0
    def pl_u(t, ph=ph): return (t / 13.0 + ph) % 1.0
    bake_fn(o, "location", 0, lambda t, ph=ph: TWX + 14.0 * pl_u(t, ph) ** 1.3)
    bake_fn(o, "location", 1, lambda t, ph=ph: TWY + 3.0 * math.sin(6.28 * ph))
    bake_fn(o, "location", 2, lambda t, ph=ph: 46.0 + 4.0 + 52.0 * pl_u(t, ph))
    for ax in range(3): bake_fn(o, "scale", ax, lambda t, ph=ph: 9.5 + 9.0 * pl_u(t, ph))
    PLUME.append(o)
COOL_IN = [(TWX - 16.6, 7.6, 0.9), (41.0, 7.6, 0.9), (41.0, 4.0, 0.9), (39.8, 4.0, 0.9)]          # cold water from the tower basin to the condenser
COOL_OUT = [(39.8, 3.0, 4.6), (40.7, 3.0, 4.6), (40.7, 6.4, 4.6), (TWX - 13.0, 6.4, 4.6), (TWX - 13.0, 6.4, 7.0)]   # warm water up to the tower sprays
pipe("CoolIn", COOL_IN, 0.5, M_COOL); pipe("CoolOut", COOL_OUT, 0.5, M_COOL)

# ================= houses + trees (CTA, scenery) =================
def house(name, x, y, w, d, h, rot=0.0):
    par = empty(name, (x, y, 0)); par.rotation_euler = (0, 0, rot)
    box(name + "Walls", -w / 2, w / 2, -d / 2, d / 2, 0, h, M_HOUSE, par)
    bm = bmesh.new(); rh = 0.45 * w
    vs = [bm.verts.new(v) for v in ((-w / 2 - 0.4, -d / 2 - 0.4, h), (w / 2 + 0.4, -d / 2 - 0.4, h), (0, -d / 2 - 0.4, h + rh),
                                     (-w / 2 - 0.4, d / 2 + 0.4, h), (w / 2 + 0.4, d / 2 + 0.4, h), (0, d / 2 + 0.4, h + rh))]
    for f in ((0, 1, 2), (3, 5, 4), (0, 2, 5, 3), (1, 4, 5, 2), (0, 3, 4, 1)): bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); mesh_obj(name + "Roof", bm, M_ROOF, par)
    for wx in (-w / 4, w / 4): box(name + f"Win{wx}", wx - 0.6, wx + 0.6, -d / 2 - 0.05, -d / 2 + 0.02, h * 0.45, h * 0.75, M_WIN, par)
house("HouseA", -17.0, -100.0, 9.0, 8.0, 3.2, 0.12); house("HouseB", -6.0, -94.0, 10.0, 8.0, 3.4, -0.15); house("HouseC", -32.0, -94.0, 8.0, 7.0, 3.0, 0.1)
def tree(name, x, y, s=1.0):
    full_cyl(name + "T", 0.25 * s, x, y, 0, 2.2 * s, M_TRUNK)
    bm = bmesh.new(); add_cyl(bm, 2.1 * s, 6.0 * s, "Z", (x, y, 2.0 * s + 3.0 * s), 12, r2=0.0); mesh_obj(name + "C", bm, M_LEAF)
random.seed(5)
for k in range(26):
    x, y = random.uniform(-90, 150), random.uniform(40, 120)
    tree(f"Tree{k}", x, y, random.uniform(1.2, 2.0))
for k, (x, y) in enumerate(((-44, -104), (-52, -100), (14, -88), (-66, -70), (-34, -60))): tree(f"YardTree{k}", x, y, 1.1)

# ================= studio set SET (x = 400): pellet + heap of coal (10x real size) =================
SX, SY = 400.0, 0.0
S = lambda x, y, z: (SX + x, SY + y, z)
box("SetFloor", SX - 90, SX + 90, -80, 60, -0.2, 0.0, M_STUDIO_F)
box("SetWall", SX - 90, SX + 90, 34, 35, 0, 70, M_STUDIO_W)
pbm = bmesh.new(); add_cyl(pbm, 0.41, 1.0, "Z", (0, 0, 0.5), 40)
PELLET = mesh_obj("Pellet", pbm, M_PELLET); PELLET.location = S(0, 0, 0.002)
try: PELLET.data.shade_smooth(); PELLET.data.set_sharp_from_angle(angle=math.radians(40))
except Exception: pass
bv = PELLET.modifiers.new("Bevel", "BEVEL"); bv.width = 0.05; bv.segments = 3
bake_fn(PELLET, "rotation_euler", 2, lambda t: 0.25 * t)
hbm = bmesh.new(); random.seed(9)
for k in range(900):
    a = random.uniform(0, 2 * math.pi); u = math.sqrt(random.random()); rr = 10.0 * u
    z = 11.0 * (1 - rr / 10.0) * random.uniform(0.75, 1.0)
    res = bmesh.ops.create_icosphere(hbm, subdivisions=1, radius=random.uniform(0.45, 1.05))
    bmesh.ops.scale(hbm, verts=res["verts"], vec=(random.uniform(0.7, 1.3), random.uniform(0.7, 1.3), random.uniform(0.6, 1.0)))
    bmesh.ops.rotate(hbm, verts=res["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(random.uniform(0, 3), 3, "Z"))
    bmesh.ops.translate(hbm, verts=res["verts"], vec=(rr * math.cos(a), rr * math.sin(a), z))
HEAP = mesh_obj("CoalHeap", hbm, M_COAL); HEAP.location = S(-10.5, 13.0, 0.0)
for ax in range(3): bake_fn(HEAP, "scale", ax, lambda t: pop(t, T_HEAP, 0.35))
windows(HEAP, [(T_HEAP, T_ROD0)])
skl = bpy.data.lights.new("SetKey", "AREA"); skl.energy = 9000; skl.size = 30; skl.color = (1.0, 0.92, 0.82)
sk = bpy.data.objects.new("SetKey", skl); scene.collection.objects.link(sk); sk.location = S(8, -14, 30); sk.rotation_euler = (math.radians(35), 0, math.radians(25))
srl = bpy.data.lights.new("SetRim", "AREA"); srl.energy = 2500; srl.size = 6; srl.color = (1.0, 0.75, 0.4)
sr = bpy.data.objects.new("SetRim", srl); scene.collection.objects.link(sr); sr.location = S(-4, 6, 3); sr.rotation_euler = (math.radians(-70), 0, math.radians(200))
glow(B_PEL, [(0, 0.0)] + pulse(C["energy"], 1.2, 0.0, 0.2, 1.0, 0.6))

# ================= rod set ROD (x = 600): glass tube fills with pellets, sealed into a rod, then a 17 x 17 assembly =================
RX, RY = 600.0, 0.0
RD = lambda x, y, z: (RX + x, RY + y, z)
box("RodFloor", RX - 90, RX + 90, -80, 60, -0.2, 0.0, M_STUDIO_F)
box("RodWall", RX - 90, RX + 90, 40, 41, 0, 90, M_STUDIO_W)
gbm3 = bmesh.new(); add_cyl(gbm3, 0.475, 13.4, "Z", (0, 0, 6.7), 32)
GTUBE = mesh_obj("GlassTube", gbm3, M_GLASS); GTUBE.location = RD(0, 0, 0.0)
windows(GTUBE, [(0, T_METAL)])
zbm = bmesh.new(); add_cyl(zbm, 0.475, 13.4, "Z", (0, 0, 6.7), 32); add_cyl(zbm, 0.475, 0.6, "Z", (0, 0, 13.7), 32, r2=0.3)
ZROD = mesh_obj("FuelRod", zbm, M_ZR); ZROD.location = RD(0, 0, 0)
windows(ZROD, [(T_METAL, DUR)])
glow(B_ZR, [(0, 0.0)] + pulse(C["fuel"], 2.5, 0.0, 0.15, 0.7, 0.5))
pel_me = PELLET.data
for k, t0 in enumerate(DROP_T):
    o = bpy.data.objects.new(f"RodPellet{k}", pel_me); CL.objects.link(o)
    o.location = RD(0, 0, 0.05 + k * 1.02)
    bake_fn(o, "location", 2, lambda t, k=k, t0=t0: 0.05 + k * 1.02 + drop(t, t0, 16.0, 0.4))
    windows(o, [(t0, T_METAL)])
cbm3 = bmesh.new(); add_cyl(cbm3, 0.475, 0.6, "Z", (0, 0, 0.3), 32, r2=0.3)
CAP = mesh_obj("EndCap", cbm3, M_ZR); CAP.location = RD(0, 0, 13.4)
bake_fn(CAP, "location", 2, lambda t: 13.4 + drop(t, T_CAP, 6.0, 0.3))
windows(CAP, [(T_CAP, T_METAL)])
GUIDE = {(2, 5), (2, 8), (2, 11), (3, 3), (3, 13), (5, 2), (5, 5), (5, 8), (5, 11), (5, 14), (8, 2), (8, 5), (8, 8), (8, 11), (8, 14),
         (11, 2), (11, 5), (11, 8), (11, 11), (11, 14), (13, 3), (13, 13), (14, 5), (14, 8), (14, 11)}
HERO = (8, 7); PITCH = 1.26
rodme = None
for i in range(17):
    bm = bmesh.new(); n_ = 0
    for j in range(17):
        if (i, j) == HERO: continue
        x, y = (i - HERO[0]) * PITCH, (j - HERO[1]) * PITCH
        if (i, j) in GUIDE: add_cyl(bm, 0.6, 14.6, "Z", (x, y, 7.3), 12, mi=1)
        else: add_cyl(bm, 0.475, 13.4, "Z", (x, y, 6.7), 12); add_cyl(bm, 0.475, 0.6, "Z", (x, y, 13.7), 12, r2=0.3)
    o = mesh_obj(f"AssemblyRow{i}", bm, [M_ZR, M_GRID]); o.location = RD(0, 0, 0)
    bake_fn(o, "location", 2, lambda t, t0=ROW_T[i]: -18.0 * (1.0 - ease((t - t0) / 0.45)))
    windows(o, [(ROW_T[i], T_CORE0)])
gbm4 = bmesh.new(); H_ = 8.5 * PITCH + 0.7
lo_, hi_ = (-HERO[0] * PITCH - 0.7, (16 - HERO[0]) * PITCH + 0.7), (-HERO[1] * PITCH - 0.7, (16 - HERO[1]) * PITCH + 0.7)
for z in (3.0, 9.0):
    add_box(gbm4, lo_[0], hi_[0], lo_[1], lo_[1] + 0.12, z, z + 0.6); add_box(gbm4, lo_[0], hi_[0], hi_[1] - 0.12, hi_[1], z, z + 0.6)
    add_box(gbm4, lo_[0], lo_[0] + 0.12, lo_[1], hi_[1], z, z + 0.6); add_box(gbm4, hi_[0] - 0.12, hi_[0], lo_[1], hi_[1], z, z + 0.6)
GRIDS = mesh_obj("SpacerGrids", gbm4, M_GRID); GRIDS.location = RD(0, 0, 0)
windows(GRIDS, [(T_NOZ, T_CORE0)])
nbm = bmesh.new()
add_box(nbm, lo_[0], hi_[0], lo_[1], lo_[1] + 0.5, 0, 1.0); add_box(nbm, lo_[0], hi_[0], hi_[1] - 0.5, hi_[1], 0, 1.0)
add_box(nbm, lo_[0], lo_[0] + 0.5, lo_[1], hi_[1], 0, 1.0); add_box(nbm, hi_[0] - 0.5, hi_[0], lo_[1], hi_[1], 0, 1.0)
NOZ = mesh_obj("TopNozzle", nbm, M_GRID); NOZ.location = RD(0, 0, 14.6)
bake_fn(NOZ, "location", 2, lambda t: 14.6 + drop(t, T_NOZ, 10.0, 0.4))
windows(NOZ, [(T_NOZ, T_CORE0)])
rkl = bpy.data.lights.new("RodKey", "AREA"); rkl.energy = 14000; rkl.size = 40; rkl.color = (1.0, 0.93, 0.85)
rk = bpy.data.objects.new("RodKey", rkl); scene.collection.objects.link(rk); rk.location = RD(14, -18, 40); rk.rotation_euler = (math.radians(30), 0, math.radians(35))
rrl = bpy.data.lights.new("RodRim", "AREA"); rrl.energy = 6000; rrl.size = 12; rrl.color = (0.6, 0.8, 1.0)
rr_ = bpy.data.objects.new("RodRim", rrl); scene.collection.objects.link(rr_); rr_.location = RD(-14, 20, 20); rr_.rotation_euler = (math.radians(-60), 0, math.radians(215))

# ================= micro set MICRO (x = -400): a neutron splits a uranium nucleus =================
MX = -400.0
MZ = 40.0
M = lambda x, y, z: (MX + x, y, MZ + z)
box("MicroWall", MX - 70, MX + 70, 25, 26, MZ - 45, MZ + 45, M_STUDIO_W)
NUC = empty("Nucleus", M(0, 0, 0))
HL, HR = empty("HalfL", (0, 0, 0), NUC), empty("HalfR", (0, 0, 0), NUC)
random.seed(21); pts_ = []
while len(pts_) < 44:
    p = Vector((random.uniform(-1.4, 1.4), random.uniform(-1.4, 1.4), random.uniform(-1.4, 1.4)))
    if p.length < 1.45 and all((p - q).length > 0.42 for q in pts_): pts_.append(p)
for half, sel in ((HL, lambda p: p.x < 0), (HR, lambda p: p.x >= 0)):
    for kp, p in enumerate([p for p in pts_ if sel(p)]):
        bm = bmesh.new(); add_ball(bm, p, 0.36, seg=14)
        mesh_obj(f"Nucleon{half.name}{kp}", bm, M_PROT if kp % 2 == 0 else M_NEUT, half).data.shade_smooth()
for ax, sc in ((0, 1.28), (1, 0.92), (2, 0.92)):
    bake_fn(NUC, "scale", ax, lambda t, sc=sc: 1.0 + (sc - 1.0) * ease((t - T_HIT) / max(0.1, T_SPLIT - T_HIT)) * (1.0 if t < T_SPLIT else 0.0))
for half, dv, rv in ((HL, Vector((-3.0, 0.6, 1.4)), -0.8), (HR, Vector((3.0, -0.4, -1.2)), 0.7)):
    for ax in range(3): bake_fn(half, "location", ax, lambda t, dv=dv, ax=ax: dv[ax] * (1 - math.exp(-max(0.0, t - T_SPLIT) * 2.2)))
    bake_fn(half, "rotation_euler", 1, lambda t, rv=rv: rv * max(0.0, t - T_SPLIT))
NIN = ball("NeutronIn", M(-12, 0, 0.3), 0.36, M_DOT_N)
bake_fn(NIN, "location", 0, lambda t: MX - 12.0 + 10.6 * lin((t - T_MIC0) / (T_HIT - T_MIC0)))
NIN.location.z = MZ + 0.3; bake_fn(NIN, "location", 2, lambda t: MZ + 0.3)
windows(NIN, [(T_MIC0, T_HIT + 0.05)])
for k, d in enumerate((Vector((0.2, -0.3, 1.0)), Vector((0.9, -0.2, -0.4)), Vector((-0.8, -0.4, -0.7)))):
    o = ball(f"NeutronOut{k}", M(0, 0, 0), 0.36, M_DOT_N); d = d.normalized()
    for ax in range(3): bake_fn(o, "location", ax, lambda t, d=d, ax=ax: (MX if ax == 0 else MZ if ax == 2 else 0.0) + d[ax] * 9.0 * max(0.0, t - T_SPLIT))
    windows(o, [(T_SPLIT, T_MIC1 + 0.2)])
glow(B_PROT, [(0, 0.0), (T_SPLIT - 0.01, 0.0), (T_SPLIT + 0.1, 1.6), (C["releasing"] + 0.3, 0.8), (C["heat"], 1.3), (T_MIC1 + 0.2, 1.3)])
glow(B_NEUT, [(0, 0.0), (T_SPLIT - 0.01, 0.0), (T_SPLIT + 0.1, 1.0), (C["releasing"] + 0.3, 0.5), (C["heat"], 0.8), (T_MIC1 + 0.2, 0.8)])
fl = bpy.data.lights.new("SplitFlash", "POINT"); fl.color = (1.0, 0.7, 0.3); fl.shadow_soft_size = 1.0
flo = bpy.data.objects.new("SplitFlash", fl); scene.collection.objects.link(flo); flo.location = M(0, -2.0, 0)
for t, v in ((0, 0.0), (T_SPLIT - 0.01, 0.0), (T_SPLIT + 0.06, 30000.0), (T_SPLIT + 0.5, 3000.0), (C["heat"], 6000.0), (T_MIC1 + 0.3, 6000.0)):
    fl.energy = v; fl.keyframe_insert("energy", frame=F(t))
mkl = bpy.data.lights.new("MicroKey", "AREA"); mkl.energy = 1800; mkl.size = 10
mk = bpy.data.objects.new("MicroKey", mkl); scene.collection.objects.link(mk); mk.location = M(5, -10, 8); mk.rotation_euler = (math.radians(50), 0, math.radians(30))

# ================= flow dots (primary red, secondary white, cooling cyan) =================
PRI_WINS = [(T_HOT, T_TURB), (C["touches"], T_CTA)]
dots("DotHot", lift(HOT_PTS, -0.55), 14, 4.0, PRI_WINS, M_DOT_R)
dots("DotCold", lift(COLD_PTS, -0.5), 12, 4.0, PRI_WINS, M_DOT_R)
dots("DotSteam", lift(STEAM_PTS, -0.6), 18, 7.0, [(C["second"], T_COND), (C["touches"], T_CTA)], M_DOT_W)
dots("DotFeed", lift(FEED_PTS, -0.5), 16, 5.0, [(C["pumped"] - 0.3, T_TOW), (C["touches"], T_CTA)], M_DOT_W)
dots("DotCoolIn", lift(COOL_IN, -0.62), 14, 6.0, [(C["third"], T_CTA)], M_DOT_C, 0.3)
dots("DotCoolOut", lift(COOL_OUT, -0.62), 14, 6.0, [(C["third"], T_CTA)], M_DOT_C, 0.3)

# ================= glows =================
# fuel: gold heat; red melt in the hook; dims with the control rods; red again when the loops are compared? (no: gold)
glow(B_FUEL, [(0, 0.9), (C["melt"] - 0.4, 0.9), (C["melt"], 3.2), (C["melt"] + 0.5, 2.0), (C["three"], 3.0), (C["y1979"], 2.0), (T_EXT - 0.02, 2.0),
              (T_EXT, 0.9), (C["heat"] - 0.3, 0.9), (C["heat"] + 0.15, 3.5), (C["control"], 1.6), (C["pushing"], 1.6), (C["slows"] + 0.3, 0.5),
              (C["stops2"], 0.5), (C["stops2"] + 0.5, 0.0), (T_WATER - 0.02, 0.0), (T_WATER, 0.9)])
ecol(B_FUEL, [(0, GOLD), (C["melt"] - 0.35, GOLD), (C["melt"] - 0.05, RED), (T_EXT - 0.02, RED), (T_EXT, GOLD)])
glow(B_CR, [(0, 0.0)] + pulse(C["soak"], 3.0, 0.0, 0.15, 0.9, 0.5))
glow(B_WATER, [(0, 0.0), (C["water2"] - 0.1, 0.0), (C["water2"] + 0.2, 0.9), (C["six"] - 0.1, 0.9), (C["six"] + 0.4, 1.6), (T_TURB, 1.6), (T_TURB + 0.02, 0.0),
               (C["touches"], 0.0), (C["touches"] + 0.3, 1.8), (T_CTA - 0.02, 1.8), (T_CTA, 0.0)])
ecol(B_WATER, [(0, CYAN), (C["six"] - 0.1, CYAN), (C["six"] + 0.3, ORANGE), (T_TURB, ORANGE), (C["touches"], RED)])
glow(B_PZR, [(0, 0.0)] + pulse(C["squeezed"], 1.4, 0.0, 0.2, max(0.3, T_HOT - C["squeezed"] - 0.9), 0.4))
glow(B_VES, [(0, 0.0)] + pulse(C["psi"] - 0.3, 1.8, 0.0, 0.15, 0.6, 0.5))
glow(B_PRI, [(0, 0.0), (T_HOT, 0.0), (C["hot"], 3.0), (T_TURB, 3.0), (T_TURB + 0.02, 0.0), (C["touches"], 0.0), (C["touches"] + 0.3, 3.5), (T_CTA - 0.02, 3.5), (T_CTA, 0.0)])
glow(B_UT, [(0, 0.0), (C["boils"] - 0.3, 0.0), (C["boils"], 1.6), (T_IN0 + 2.4, 0.0), (C["tubes2"] - 0.1, 0.0), (C["tubes2"] + 0.25, 2.0), (T_TURB, 2.0), (T_TURB + 0.02, 0.0),
            (C["touches"], 0.0), (C["touches"] + 0.3, 3.0), (T_CTA - 0.02, 3.0), (T_CTA, 0.0)])
glow(B_WATER2, [(0, 0.0), (C["second"] - 0.1, 0.0), (C["second"] + 0.3, 0.8), (T_TURB, 0.8), (T_TURB + 0.02, 0.0)])
glow(B_SEC, [(0, 0.0), (C["second"] - 0.1, 0.0), (C["second"] + 0.3, 2.2), (T_TOW, 2.2), (T_TOW + 0.02, 0.0), (C["touches"], 0.0), (C["touches"] + 0.3, 2.2), (T_CTA - 0.02, 2.2), (T_CTA, 0.0)])
glow(B_TURB, [(0, 0.0)] + pulse(C["blasts"], 1.6, 0.0, 0.2, 1.2, 0.6))
glow(B_GEN, [(0, 0.0), (C["generator2"] - 0.1, 0.0), (C["generator2"] + 0.25, 3.0), (T_COND, 3.0), (T_COND + 0.02, 0.0)])
glow(B_WIRE, [(0, 0.0), (C["electricity"] - 0.1, 0.0), (C["electricity"] + 0.2, 4.0), (T_COND, 4.0), (T_COND + 0.02, 0.0)])
glow(B_COOL, [(0, 0.0), (C["cooled"] - 0.1, 0.0), (C["cooled"] + 0.3, 3.0), (T_TOW, 3.0), (T_TOW + 0.02, 0.0), (C["third"], 0.0), (C["third"] + 0.3, 3.5), (T_CTA - 0.02, 3.5), (T_CTA, 0.0)])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-30.0, -66.0, 6.5), (20.0, 0.0, 18.0), 20),
    (T_IN0 - 0.05, (-24.0, -56.0, 6.0), (18.0, 0.0, 17.0), 20),
    (T_IN0, (-1.0, -24.0, 11.0), (0.5, 0.0, 12.0), 24, "cut"),
    (C["if"] - 0.05, (0.0, -22.0, 11.0), (0.8, 0.0, 11.8), 24),
    (C["if"], (-3.2, -10.5, 8.0), (-5.0, 0.0, 7.2), 24, "cut"),
    (T_EXT - 0.05, (-3.6, -9.0, 7.6), (-5.0, 0.0, 7.0), 24),
    (T_EXT, (8.0, -78.0, 15.0), (14.0, 0.0, 13.0), 22, "cut"),
    (T_SET0 - 0.05, (6.0, -70.0, 14.0), (11.0, 0.0, 12.0), 22),
    (T_SET0, S(1.7, -3.0, 1.2), S(0.0, 0.0, 0.45), 50, "cut"),
    (T_HEAP - 0.25, S(2.2, -4.2, 1.6), S(0.0, 0.0, 0.5), 50),
    (C["coal"] + 0.5, S(4.0, -30.0, 8.0), S(-7.0, 8.0, 5.0), 34),
    (T_ROD0 - 0.05, S(4.2, -29.5, 8.0), S(-7.0, 8.0, 5.0), 34),
    (T_ROD0, RD(4.0, -15.0, 8.0), RD(0.0, 0.0, 7.5), 35, "cut"),
    (C["over"], RD(4.4, -16.0, 9.0), RD(0.0, 0.0, 8.0), 35),
    (C["assembly"] + 0.4, RD(17.0, -30.0, 34.0), RD(0.0, -1.0, 6.0), 32),
    (T_CORE0 - 0.05, RD(17.5, -30.5, 34.5), RD(0.0, -1.0, 6.0), 32),
    (T_CORE0, (-3.0, -9.5, 7.5), (-5.0, 0.0, 6.5), 24, "cut"),
    (T_MIC0 - 0.05, (-3.3, -9.0, 7.3), (-5.0, 0.0, 6.5), 24),
    (T_MIC0, M(0.0, -13.0, 1.0), M(0.0, 0.0, 0.6), 40, "cut"),
    (T_MIC1 - 0.05, M(0.0, -15.0, 1.0), M(0.0, 0.0, 0.6), 40),
    (T_MIC1, (-3.6, -8.0, 8.6), (-5.0, 0.0, 7.6), 24, "cut"),
    (C["stops2"] + 0.6, (-3.9, -7.4, 8.0), (-5.0, 0.0, 7.0), 24),
    (T_WATER, (1.5, -30.0, 11.0), (1.0, 0.0, 12.5), 24, "cut"),
    (C["around"] - 0.2, (0.5, -28.0, 11.0), (0.5, 0.0, 12.3), 24),
    (C["around"] + 0.4, (-3.0, -14.0, 8.5), (-5.0, 0.0, 8.0), 24),
    (C["squeezed"] - 0.2, (-4.5, -15.0, 9.0), (-6.5, 0.0, 8.5), 24),
    (C["twentytwo"], (-7.0, -15.0, 9.5), (-8.5, 0.0, 9.0), 24),
    (T_HOT - 0.05, (-7.3, -15.5, 9.5), (-8.5, 0.0, 9.0), 24),
    (T_HOT, (0.5, -21.0, 9.0), (1.0, 0.0, 7.5), 24, "cut"),
    (C["steam"] - 0.2, (5.0, -13.0, 9.5), (6.0, 0.0, 9.0), 24),
    (C["clean"] + 0.3, (5.5, -12.0, 10.5), (6.0, 0.0, 10.0), 24),
    (T_TURB - 0.05, (5.6, -11.8, 10.6), (6.0, 0.0, 10.0), 24),
    (T_TURB, (30.0, -22.0, 12.5), (32.0, 0.0, 8.0), 24, "cut"),
    (C["generator2"] - 0.3, (38.0, -21.0, 11.5), (40.0, 0.0, 8.0), 24),
    (C["electricity"] + 0.3, (46.0, -34.0, 16.0), (52.0, 0.0, 12.0), 24),
    (T_COND - 0.05, (46.5, -34.5, 16.2), (52.0, 0.0, 12.0), 24),
    (T_COND, (33.0, -13.0, 4.6), (34.0, 2.0, 3.2), 24, "cut"),
    (C["pumped"] - 0.1, (32.0, -15.0, 5.0), (32.0, 2.0, 3.5), 24),
    (T_TOW - 0.05, (16.0, -62.0, 16.0), (14.0, 0.0, 8.0), 24),
    (T_TOW, (50.0, -62.0, 6.0), (72.0, 14.0, 30.0), 20, "cut"),
    (T_LOOPS - 0.05, (52.0, -58.0, 7.0), (72.0, 14.0, 32.0), 20),
    (T_LOOPS, (12.0, -70.0, 40.0), (24.0, 4.0, 6.0), 24, "cut"),
    (T_CTA - 0.05, (14.0, -66.0, 38.0), (24.0, 4.0, 6.0), 24),
    (T_CTA, (-22.0, -126.0, 2.8), (12.0, 0.0, 17.0), 26, "cut"),
    (DUR, (-21.0, -119.0, 3.0), (12.0, 0.0, 17.5), 26),
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
    amp = 0.04 if l0.length < 300 else 0.01
    cam_loc.append(l0 + Vector((amp * math.sin(t * 0.7), 0.0, amp * 0.8 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()

# ================= world + light: daylight plant =================
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
sun.rotation_euler = (math.radians(55), math.radians(-15), math.radians(-35))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.color = (1.0, 0.95, 0.88); fill_d.energy = 3000
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)
# inside the containment: a warm work light high in the dome (the far half shades the sun)
inl = bpy.data.lights.new("DomeLight", "AREA"); inl.size = 14; inl.energy = 3000; inl.color = (1.0, 0.94, 0.86)
ino = bpy.data.objects.new("DomeLight", inl); scene.collection.objects.link(ino); ino.location = (0.0, -6.0, 30.0)
hll = bpy.data.lights.new("HallLight", "AREA"); hll.size = 30; hll.energy = 4000; hll.color = (1.0, 0.95, 0.9)
hlo = bpy.data.objects.new("HallLight", hll); scene.collection.objects.link(hlo); hlo.location = (38.0, -2.0, 19.0)

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
try: scene.cycles.volume_step_rate = 4.0
except Exception: pass
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
    "pellet": lambda t: Vector(S(0.0, 0.0, 1.0)),
    "heap": lambda t: Vector(S(-10.5, 13.0, 9.5)),
    "rod": lambda t: Vector(RD(0.0, 0.0, 12.5)),
    "assembly": lambda t: Vector(RD(8.0 * PITCH, -7.0 * PITCH, 14.0)),
    "core": lambda t: Vector((VX + 1.2, 0.0, 6.0)),
    "rods": lambda t: Vector((VX - 1.2, 0.3, 10.4 + rods_z(t))),
    "vessel": lambda t: Vector((VX - 2.45, 0.0, 12.0)),
    "water": lambda t: Vector((VX + 1.6, 0.0, 10.5)),
    "pzr": lambda t: Vector((PZX - 0.9, 0.0, 12.5)),
    "hotleg": lambda t: Vector((1.6, 0.3, 6.0)),
    "sg": lambda t: Vector((SGX + 1.7, 0.0, 15.0)),
    "utubes": lambda t: Vector((SGX + 0.84, 0.6, 8.0)),
    "steamline": lambda t: Vector((18.0, 0.6, 20.6)),
    "turbine": lambda t: Vector((37.0, TY, TZ + 2.4)),
    "generator": lambda t: Vector((45.6, TY - 1.9, TZ + 0.5)),
    "wires": lambda t: Vector((PYX, PYY, 22.5)),
    "condenser": lambda t: Vector((36.0, 2.4, 3.0)),
    "feed": lambda t: Vector((20.0, 2.0, 0.9)),
    "tower": lambda t: Vector((TWX - 12.0, TWY - 6.0, 30.0)),
    "plume": lambda t: Vector((TWX + 4.0, TWY, 66.0)),
    "coolpipe": lambda t: Vector((50.0, 6.0, 4.6)),
    "containment": lambda t: Vector((-8.0, -10.0, 30.0)),
    "nucleus": lambda t: Vector(M(0.0, 0.0, 1.5)),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"cut": R3(T_CUT0, T_CUT1), "inside": round(T_IN0, 3), "ext": round(T_EXT, 3), "set": round(T_SET0, 3), "heap": round(T_HEAP, 3),
          "rodset": round(T_ROD0, 3), "drops": [round(x + 0.4, 3) for x in DROP_T], "cap": round(T_CAP + 0.3, 3), "metal": round(T_METAL, 3),
          "rows": [round(x + 0.45, 3) for x in ROW_T], "nozzle": round(T_NOZ + 0.4, 3), "core": round(T_CORE0, 3), "micro": R3(T_MIC0, T_MIC1),
          "hit": round(T_HIT, 3), "split": round(T_SPLIT, 3),
          "rods": [[round(a, 3), round(b, 3)] for a, b in ((C["slide"], C["in2"] + 0.2), (C["out"], C["out"] + 0.45), (C["pushing"], C["slows"] + 0.2), (C["stops2"] - 0.1, C["stops2"] + 0.5))],
          "water": round(T_WATER, 3), "hot": round(T_HOT, 3), "turbine": round(T_TURB, 3), "cond": round(T_COND, 3), "tower": round(T_TOW, 3),
          "loops": round(T_LOOPS, 3), "cta": round(T_CTA, 3)}
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
