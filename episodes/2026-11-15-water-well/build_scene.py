# Water-Well-3D: how a hole in your yard becomes a water well. Build-up format ("THIS IS A BUCKET"): bucket on a rope -> suction pump
# (stops at ~33 ft above the water) -> electric submersible pump at the bottom pushes -> walls cave in -> casing -> slotted screen
# (water in, sand out) -> rain runs down the outside -> grout seal -> pump would start with every tap -> pressure tank (cushion of air)
# -> pull-out to the whole yard -> bucket under the outdoor spigot (echo of the first object).
# Blender Cycles, real-world set: a yard with a house, cut at y = 0 like an ant farm (soil layers, water table, aquifer), camera on -y.
# Illustrative scale: 1 unit = 1 m. Water table at z = -16 m (~52 ft), well bottom at z = -43 m (~140 ft, the USGS median for domestic
# wells), suction limit drawn 10 m (~33 ft) above the water; bore, casing, pump and tank are drawn wider than real (bore r 0.9 m) so they
# read on a phone. Soil layers, grout depth and tank size are illustrative.
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
CUES = [("if", "If"), ("water", "water."), ("getting", "Getting"), ("hard", "hard"), ("suction", "suction"), ("thirtythree", "thirty-three"),
        ("feet", "feet."), ("and", "And"), ("wrong", "wrong,"), ("rainwater", "rainwater"), ("runs", "runs"), ("drink", "drink."),
        ("lets", "Let's"), ("this", "This"), ("bucket", "bucket"), ("fine", "Fine,"), ("shallow", "shallow."), ("typical", "typical"),
        ("hundred", "hundred"), ("forty", "forty"), ("deep", "deep."), ("so", "So"), ("suction2", "suction"), ("doesnt", "doesn't"),
        ("lowers", "lowers"), ("pressure", "pressure"), ("air", "air"), ("pushes", "pushes"), ("up", "up."), ("but", "But"), ("air2", "air"),
        ("thirtythree2", "thirty-three"), ("so2", "So"), ("drop", "drop"), ("electric", "electric"), ("bottom", "bottom,"), ("under", "under"),
        ("push", "push"), ("now", "Now"), ("walls", "walls"), ("cave", "cave"), ("line", "line"), ("pipe", "pipe:"), ("casing", "casing."),
        ("at", "At"), ("screen", "screen"), ("slots", "slots"), ("lets2", "lets"), ("sand", "sand"), ("but2", "But"), ("rain", "rain"),
        ("outside", "outside,"), ("bacteria", "bacteria."), ("gap", "gap"), ("sealed", "sealed"), ("grout", "grout."), ("last", "Last"),
        ("pump", "pump"), ("start", "start"), ("every", "every"), ("tap", "tap,"), ("wear", "wear"), ("out", "out."), ("so3", "So"),
        ("pressure2", "pressure"), ("tank", "tank"), ("cushion", "cushion"), ("air3", "air."), ("fills", "fills"), ("shuts", "shuts"),
        ("air4", "air"), ("pushes2", "pushes"), ("faucets", "faucets."), ("more", "More"), ("twentythree", "twenty-three"),
        ("million", "million"), ("households", "households"), ("would", "Would"), ("drink2", "drink"), ("ground", "ground?"),
        ("tell", "Tell"), ("next", "Next"), ("pipe2", "pipe"), ("river", "river"), ("follow", "Follow")]
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
CL = coll("WaterWell")
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
T_A1, T_B0, T_C0, T_W0 = C["suction"], C["and"], C["lets"], C["this"]          # hook shots A (bucket), B (suction), C (rain), wide
T_DEEP0, T_DEEP1 = C["typical"], C["deep"] + 0.3                               # bore deepens 20 m -> 43 m
T_SU0, T_SU1 = C["so"], C["so2"]                                               # suction beat
T_PD0, T_PD1 = C["drop"], C["bottom"] + 0.2                                    # pump drops to the bottom
T_CAVE = C["cave"] - 0.05
T_CS0, T_CS1 = C["line"], C["casing"] + 0.25                                   # casing slides in
T_SC0, T_SC1 = C["at"], C["but2"]                                              # screen beat
T_GR0, T_GR1 = C["sealed"], C["grout"] + 0.35                                  # grout fills the gap
T_CTA = C["would"]
WT, BOT, SUC_TOP = -16.0, -43.0, -6.0                                          # water table, well bottom, suction limit (10 m above the water)
RB, RCI, RCO = 0.9, 0.55, 0.62                                                 # bore, casing inner / outer radius
PUMP_TOP = -32.4
TX, TZ0, TZ1, TR = 15.0, -2.95, -1.45, 0.55                                     # pressure tank x, inner bottom/top, radius
SPX, SPY, SPZ = 14.2, 2.35, 0.75                                               # outdoor spigot
def in_any(t, wins): return any(a <= t < b for a, b in wins)
def bore_depth(t):
    if T_C0 <= t < T_DEEP0: return 20.0
    if T_DEEP0 <= t < T_DEEP1: return 20.0 + 23.0 * ease((t - T_DEEP0) / (T_DEEP1 - T_DEEP0))
    return -BOT

# ================= materials =================
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
M_TOP = soil_mat("Topsoil", (0.10, 0.06, 0.035), (0.16, 0.10, 0.06), 2.0)
M_CLAY = soil_mat("Clay", (0.34, 0.17, 0.08), (0.46, 0.25, 0.12), 0.8)
M_AQ = soil_mat("SandGravel", (0.42, 0.33, 0.20), (0.58, 0.47, 0.30), 1.6, wet=True)
M_ROCK = soil_mat("Bedrock", (0.20, 0.20, 0.21), (0.34, 0.33, 0.33), 0.5)
M_GRASS = ground("Grass", (0.10, 0.22, 0.05), (0.20, 0.36, 0.08), 0.6)
M_CONC, _ = mat("Concrete", (0.55, 0.54, 0.52), 0.85, noise=3.0)
M_CASE, B_CASE = mat("Casing", (0.80, 0.81, 0.80), 0.35, emit_rgb=(0.98, 0.74, 0.27))
M_SCREEN, B_SCREEN = mat("Screen", (0.62, 0.64, 0.66), 0.3, 0.9, emit_rgb=(0.30, 0.92, 1.0))
M_PUMP, B_PUMP = mat("Pump", (0.70, 0.72, 0.74), 0.25, 0.95)
M_MOTOR, _ = mat("Motor", (0.12, 0.13, 0.14), 0.4, 0.6)
M_PIPE, B_PIPE = mat("DropPipe", (0.10, 0.10, 0.11), 0.45, emit_rgb=(0.30, 0.92, 1.0))
M_SPIPE, B_SPIPE = mat("SuctionPipe", (0.30, 0.31, 0.33), 0.4, 0.8, emit_rgb=(0.30, 0.92, 1.0))
M_IRON, _ = mat("CastIron", (0.05, 0.12, 0.08), 0.45, 0.6)
M_WOOD, _ = mat("Wood", (0.36, 0.22, 0.11), 0.7, noise=6.0)
M_ROPE, _ = mat("Rope", (0.55, 0.45, 0.30), 0.9)
M_BUCKET, B_BUCKET = mat("Bucket", (0.62, 0.64, 0.66), 0.35, 0.9)
M_GROUT, B_GROUT = mat("Grout", (0.22, 0.22, 0.24), 0.9, emit_rgb=(0.98, 0.74, 0.27), noise=8.0)
M_DIRT, B_DIRT = mat("DirtyWater", (0.35, 0.12, 0.06), 0.3, emit_rgb=(1.0, 0.30, 0.24))
M_TANK, B_TANK = mat("Tank", (0.10, 0.28, 0.62), 0.35, 0.5, emit_rgb=(0.30, 0.92, 1.0))
M_BLAD, _ = mat("Bladder", (0.04, 0.04, 0.045), 0.6)
M_SIDING, _ = mat("Siding", (0.86, 0.85, 0.80), 0.6)
M_ROOF, _ = mat("Roof", (0.16, 0.15, 0.15), 0.8)
M_TRIM, _ = mat("Trim", (0.95, 0.95, 0.95), 0.5)
M_WIN, B_WIN = mat("Window", (0.05, 0.08, 0.12), 0.08, emit_rgb=(1.0, 0.86, 0.6))
M_DOOR, _ = mat("Door", (0.30, 0.10, 0.07), 0.5)
M_BRASS, _ = mat("Brass", (0.75, 0.55, 0.25), 0.3, 1.0)
M_BARK, _ = mat("Bark", (0.18, 0.11, 0.06), 0.9)
M_LEAF, _ = mat("Leaf", (0.07, 0.20, 0.05), 0.8, noise=4.0)
M_GOLD, B_GOLDBAR = mat("GoldBar", (0.98, 0.74, 0.27), 0.4, emit_rgb=(0.98, 0.74, 0.27)); B_GOLDBAR.inputs["Emission Strength"].default_value = 1.2
M_REDL, B_REDL = mat("RedLine", (1.0, 0.30, 0.24), 0.4, emit_rgb=(1.0, 0.30, 0.24)); B_REDL.inputs["Emission Strength"].default_value = 2.0
M_CYAN, B_CYAN = mat("CyanDot", (0.30, 0.92, 1.0), 0.3, emit_rgb=(0.30, 0.92, 1.0)); B_CYAN.inputs["Emission Strength"].default_value = 4.0
M_SANDG, _ = mat("SandGrain", (0.85, 0.66, 0.30), 0.6, emit_rgb=(0.98, 0.74, 0.27))
M_RAIN, B_RAIN = mat("Rain", (0.75, 0.85, 0.95), 0.1, emit_rgb=(0.8, 0.9, 1.0)); B_RAIN.inputs["Emission Strength"].default_value = 1.6
M_WATER, B_WATER, _ = water_sec("WellWater", dens=0.05)
M_TWATER, B_TWATER, _ = water_sec("TankWater", dens=0.08)
M_COL, B_COL, _ = water_sec("SuctionWater", dens=0.12)
M_STREAM, B_STREAM = mat("Stream", (0.55, 0.80, 0.95), 0.05, emit_rgb=(0.6, 0.9, 1.0)); B_STREAM.inputs["Emission Strength"].default_value = 0.5
M_AIR, A_AIR = ghost("TankAir", (0.98, 0.74, 0.27))
M_LOWP, A_LOWP = ghost("LowPressure", (0.30, 0.92, 1.0))

# ================= ground: soil layers cut at y = 0, bore + basement booleans =================
BORE = cyl("BoreCutter", RB, 1.0, "Z", (0, 0, -0.5), None, seg=48); BORE.location = (0, 0, 1.0)
BASE = box("BasementCutter", 11.9, 22.1, -1.0, 9.9, -3.2, 0.6, None)
for c in (BORE, BASE): c.hide_render = True; c.display_type = "WIRE"
bake_fn(BORE, "scale", 2, lambda t: bore_depth(t) + 1.0)
def layer(name, z0, z1, m_):
    o = box(name, -45.0, 55.0, 0.0, 70.0, z0, z1, m_)
    for c in (BORE, BASE):
        md = o.modifiers.new("cut_" + c.name, "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = c
        try: md.solver = "EXACT"
        except Exception: pass
    return o
layer("Grass", -0.02, 0.10, M_GRASS); layer("TopsoilL", -1.5, -0.02, M_TOP); layer("ClayL", -12.0, -1.5, M_CLAY)
layer("AquiferL", -48.0, -12.0, M_AQ); layer("BedrockL", -70.0, -48.0, M_ROCK)
bpy.data.objects["BedrockL"].modifiers.clear()
FARG = box("FarGrass", -600, 600, 70.0, 600, -2.0, 0.10, M_GRASS)
box("SideGrassL", -600, -45.0, 0.0, 70.0, -2.0, 0.10, M_GRASS); box("SideGrassR", 55.0, 600, 0.0, 70.0, -2.0, 0.10, M_GRASS)
# well water (half cylinder behind the cut, top = water table, bottom follows the bore)
WW = half_cyl("WellWater", RB - 0.01, 0.0, 0.0, 0.015, 0.0, 1.0, M_WATER); WW.location = (0, 0, -1.0)
bake_fn(WW, "location", 2, lambda t: -bore_depth(t) + 0.02); bake_fn(WW, "scale", 2, lambda t: (bore_depth(t) + WT) - 0.04)
glow(B_WATER, [(0, 0)] + pulse(C["drink"] - 0.4, 1.2, up=0.3, hold=0.6) + pulse(C["bacteria"] - 0.2, 1.2, up=0.3, hold=0.5))
B_WATER.inputs["Emission Color"].default_value = (1.0, 0.30, 0.24, 1)
# basement: concrete box open toward the camera
box("BsmtFloor", 11.9, 22.1, 0.0, 9.9, -3.2, -3.0, M_CONC); box("BsmtBack", 11.9, 22.1, 9.7, 9.9, -3.2, 0.0, M_CONC)
box("BsmtL", 11.9, 12.1, 0.0, 9.9, -3.2, 0.0, M_CONC); box("BsmtR", 21.9, 22.1, 0.0, 9.9, -3.2, 0.0, M_CONC)
box("BsmtCeil", 11.9, 22.1, 0.0, 9.9, -0.25, 0.0, M_CONC)
box("BsmtGrass", 11.9, 22.1, 0.0, 2.6, -0.02, 0.10, M_GRASS); box("BsmtSoil", 11.9, 22.1, 0.0, 2.6, -0.25, -0.02, M_TOP)
# ================= house (front wall at y = 2.5), spigot, trees =================
box("HouseBody", 12.0, 22.0, 2.5, 12.0, 0.0, 4.6, M_SIDING)
bm = bmesh.new()
v = [bm.verts.new(p) for p in [(11.7, 2.2, 4.6), (22.3, 2.2, 4.6), (22.3, 7.25, 7.2), (11.7, 7.25, 7.2), (11.7, 12.3, 4.6), (22.3, 12.3, 4.6)]]
bm.faces.new([v[0], v[1], v[2], v[3]]); bm.faces.new([v[3], v[2], v[5], v[4]])
bm.faces.new([v[0], v[3], v[4]]); bm.faces.new([v[1], v[5], v[2]])
mesh_obj("Roof", bm, M_ROOF)
for x in (13.0, 19.0):
    box(f"Win{x}", x, x + 1.6, 2.44, 2.52, 1.2, 2.8, M_WIN); box(f"WinTrim{x}", x - 0.1, x + 1.7, 2.46, 2.5, 1.1, 2.9, M_TRIM)
box("Door", 16.2, 17.4, 2.44, 2.52, 0.0, 2.3, M_DOOR); box("DoorTrim", 16.1, 17.5, 2.46, 2.5, 0.0, 2.4, M_TRIM)
box("Step", 16.0, 17.6, 1.8, 2.5, 0.0, 0.18, M_CONC)
SPIG = empty("Spigot", (SPX, SPY, SPZ))
cyl("SpigotPipe", 0.03, 0.25, "Y", (0, 0.05, 0), M_BRASS, SPIG); cyl("SpigotBody", 0.045, 0.12, "Z", (0, -0.08, -0.02), M_BRASS, SPIG)
cyl("SpigotSpout", 0.028, 0.08, "Z", (0, -0.08, -0.11), M_BRASS, SPIG); cyl("SpigotWheel", 0.07, 0.015, "Z", (0, -0.08, 0.07), M_IRON, SPIG)
for (tx, ty, s) in [(-9.0, 9.0, 1.0), (-16.0, 16.0, 1.3), (30.0, 12.0, 1.1), (4.0, 24.0, 1.4), (-3.0, 40.0, 1.6), (40.0, 30.0, 1.5)]:
    cyl(f"Trunk{tx}", 0.22 * s, 3.2 * s, "Z", (tx, ty, 1.6 * s), M_BARK)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=2.2 * s)
    for vv in bm.verts: vv.co += Vector((random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25), random.uniform(-0.25, 0.25))) * s
    o = mesh_obj(f"Crown{tx}", bm, M_LEAF); o.location = (tx, ty, 4.4 * s)
# yard bucket under the spigot (fills in the CTA)
def bucket_mesh(name, r=0.32, h=0.42):
    o = lathe(name, [(r * 0.78, 0.0), (r, h), (r - 0.012, h), (r * 0.78 - 0.012, 0.012), (0.0, 0.012), (0.0, 0.0)], M_BUCKET, 0, 2 * math.pi, 40)
    return o
YB = bucket_mesh("YardBucket", 0.16, 0.24); YB.location = (SPX, SPY - 0.15, 0.10)
YBW = cyl("YardBucketWater", 0.13, 1.0, "Z", (0, 0, 0.5), M_TWATER); YBW.parent = YB; YBW.matrix_parent_inverse = Matrix.Identity(4)
YBW.location = (0, 0, 0.012)
def ybw(t): return 0.002 + 0.20 * lin((t - T_CTA - 0.4) / 8.0)
bake_fn(YBW, "scale", 2, ybw)
# ================= hook / beat 1: bucket on a rope + windlass =================
BK_WIN = [(0.0, T_A1), (T_W0, T_SU0)]
WL = empty("Windlass")
for x in (-1.5, 1.5): box(f"Post{x}", x - 0.08, x + 0.08, 0.22, 0.38, 0.0, 2.4, M_WOOD, WL)
cyl("Crossbar", 0.07, 3.3, "X", (0, 0.3, 2.3), M_WOOD, WL)
windows(WL, BK_WIN)
def bucket_z(t):
    if t < T_A1: return PW([(0.0, -9.0), (1.2, -9.0), (3.6, WT - 0.15), (4.4, WT - 0.15), (5.4, WT + 1.2)])(t)
    return PW([(T_W0, 1.2), (C["fine"] + 0.1, WT - 0.15), (C["shallow"] + 0.2, WT - 0.15), (T_DEEP0, -11.0)])(t)
BUCK = bucket_mesh("Bucket"); BUCK.location = (0, 0.32, 0)
cyl("BucketBail", 0.014, 0.66, "X", (0, 0, 0.52), M_IRON, BUCK)
BKW = cyl("BucketWater", 0.27, 1.0, "Z", (0, 0, 0.5), M_COL, BUCK); BKW.location = (0, 0, 0.02)
bake_fn(BKW, "scale", 2, lambda t: 0.25 if (t < T_A1 and t > 3.9) or (t >= T_W0 and t > C["fine"] + 0.3) else 0.001)
bake_fn(BUCK, "location", 2, bucket_z)
bake_fn(BUCK, "rotation_euler", 1, lambda t: 0.05 * math.sin(t * 1.9))
ROPE = cyl("Rope", 0.018, 1.0, "Z", (0, 0, -0.5), M_ROPE); ROPE.location = (0, 0.32, 2.3)
bake_fn(ROPE, "scale", 2, lambda t: max(0.01, 2.3 - bucket_z(t) - 0.52))
windows(BUCK, BK_WIN); windows(ROPE, BK_WIN)
# ================= suction pump (hand pitcher pump on a board) + suction pipe + rising water column =================
SU_WIN = [(T_A1, T_B0), (T_SU0, T_SU1)]
SP = empty("SuctionRig")
box("Board", -1.3, 1.3, 0.0, 1.1, 0.10, 0.20, M_WOOD, SP)
cyl("Stand", 0.11, 0.6, "Z", (0, 0.15, 0.5), M_IRON, SP); cyl("PumpBody", 0.22, 0.75, "Z", (0, 0.15, 1.15), M_IRON, SP)
cyl("PumpCap", 0.25, 0.08, "Z", (0, 0.15, 1.56), M_IRON, SP); cyl("Spout", 0.07, 0.5, "X", (-0.42, 0.15, 1.30), M_IRON, SP)
bm = bmesh.new(); add_bar(bm, (0.15, 0.15, 1.58), (0.95, 0.15, 2.05), 0.06); mesh_obj("Handle", bm, M_IRON, SP)
SPIPE = lathe("SuctionPipe", tube_prof(0.10, 0.13, -18.0, 0.2), M_SPIPE, 0.0, math.pi, 24)
SCOL = half_cyl("SuctionCol", 0.098, 0.0, 0.0, 0.004, 0.0, 1.0, M_COL); SCOL.location = (0, 0, -18.0)
def col_top(t):
    if T_A1 <= t < T_B0: return PW([(T_A1, WT), (T_A1 + 0.35, WT), (C["feet"] + 0.1, SUC_TOP)])(t)
    if T_SU0 <= t < T_SU1: return PW([(C["lowers"], WT), (C["up"] + 0.2, SUC_TOP + 1.5), (C["thirtythree2"] + 0.4, SUC_TOP)])(t)
    return WT
bake_fn(SCOL, "scale", 2, lambda t: col_top(t) + 18.0)
LOWP = half_cyl("LowPressure", 0.097, 0.0, 0.0, 0.006, 0.0, 1.0, M_LOWP); LOWP.location = (0, 0, 0.0)
bake_fn(LOWP, "location", 2, lambda t: col_top(t)); bake_fn(LOWP, "scale", 2, lambda t: max(0.01, 0.2 - col_top(t)))
keyval(A_LOWP, [(0, 0.0), (C["lowers"] - 0.05, 0.0), (C["lowers"] + 0.25, 0.8), (C["air"], 0.8), (C["air"] + 0.4, 0.25), (T_SU1, 0.25)])
REDL = box("SuctionLimit", -1.6, 1.6, -0.12, -0.04, SUC_TOP - 0.06, SUC_TOP + 0.06, M_REDL)
BRK = empty("SuctionBracket")
box("BrkBar", -2.08, -1.98, -0.12, -0.04, WT, SUC_TOP, M_GOLD, BRK)
box("BrkTop", -2.3, -1.76, -0.12, -0.04, SUC_TOP - 0.05, SUC_TOP + 0.05, M_GOLD, BRK); box("BrkBot", -2.3, -1.76, -0.12, -0.04, WT - 0.05, WT + 0.05, M_GOLD, BRK)
for o in (SP, SPIPE, SCOL, LOWP): windows(o, SU_WIN)
windows(REDL, [(C["thirtythree"], T_B0), (C["thirtythree2"], T_SU1)]); windows(BRK, [(C["thirtythree"] - 0.2, T_B0), (C["but"], T_SU1)])
# air presses on the water in the well: gold arrows down onto the water surface
ARRS = empty("AirArrows")
bm = bmesh.new()
for x in (-0.62, 0.42):
    add_arrow(bm, (x, WT + 1.6), (0, -1), 1.35, 0.32, y=-0.06)
mesh_obj("AirArrowMesh", bm, M_GOLD, ARRS)
bm = bmesh.new()
for x in (-6.0, -3.5, 3.5, 6.0): add_arrow(bm, (x, 2.2), (0, -1), 1.6, 0.42, y=-0.06)
mesh_obj("AirArrowSky", bm, M_GOLD, ARRS)
windows(ARRS, [(C["air"], C["but"])])
bake_fn(ARRS, "location", 2, lambda t: -0.25 * (0.5 + 0.5 * math.sin(t * 9.0)))
# ================= depth bar (140 ft) =================
DB = box("DepthBar", -2.75, -2.6, -0.12, -0.04, -1.0, 0.0, M_GOLD); DB.location = (0, 0, 0)
bake_fn(DB, "scale", 2, lambda t: max(0.01, bore_depth(t)) if t >= T_DEEP0 else 20.0)
windows(DB, [(C["hundred"] - 0.3, T_SU0)])
DBT = box("DepthTop", -3.0, -2.35, -0.12, -0.04, -0.05, 0.05, M_GOLD); windows(DBT, [(C["hundred"] - 0.3, T_SU0)])
# ================= submersible pump + drop pipe + pipe to the house =================
PUMP = empty("Pump")
cyl("PumpEnd", 0.30, 1.2, "Z", (0, 0, -0.6), M_PUMP, PUMP); cyl("PumpIntake", 0.27, 0.25, "Z", (0, 0, -1.33), M_MOTOR, PUMP)
cyl("PumpMotor", 0.30, 1.3, "Z", (0, 0, -2.1), M_PUMP, PUMP); cyl("PumpNose", 0.26, 0.1, "Z", (0, 0, -2.8), M_MOTOR, PUMP)
for k in range(6):
    cyl(f"IntakeSlot{k}", 0.285, 0.03, "Z", (0, 0, -1.25 - 0.035 * k), M_PUMP, PUMP)
PUMP.location = (0, 0, 2.0)
def pump_z(t): return PW([(T_PD0, 3.0), (T_PD1, PUMP_TOP)])(t)
bake_fn(PUMP, "location", 2, pump_z)
windows(PUMP, [(T_PD0, DUR)])
DROP = cyl("DropPipe", 0.10, 1.0, "Z", (0, 0, -0.5), M_PIPE); DROP.location = (0, 0, -2.0)
bake_fn(DROP, "scale", 2, lambda t: max(0.01, -2.0 - pump_z(t)))
windows(DROP, [(T_PD0 + 0.15, DUR)])
HP = cyl("HousePipe", 0.10, TX - 0.55, "X", ((TX - 0.55) / 2, 0.0, -2.0), M_PIPE)
ELB = cyl("Elbow", 0.13, 0.3, "Z", (0, 0, -2.0), M_PIPE)
windows(HP, [(T_PD0, DUR)]); windows(ELB, [(T_PD0, DUR)])
glow(B_PIPE, [(0, 0)] + pulse(C["push"] - 0.1, 1.5, up=0.2, hold=0.9, down=0.4))
# pump glow: gold = running, red = short cycling
PK = [(0, 0.0)] + pulse(C["push"] - 0.1, 2.0, up=0.15, hold=0.9, down=0.3)
for t0, t1 in [(C["start"], C["start"] + 0.32), (C["every"], C["every"] + 0.3), (C["tap"] + 0.15, C["tap"] + 0.42)]:
    PK += [(t0 - 0.01, 0.0), (t0 + 0.05, 2.2), (t1, 2.2), (t1 + 0.06, 0.0)]
PK += [(C["wear"] - 0.01, 0.0), (C["wear"] + 0.1, 3.0), (C["out"] + 0.5, 3.0), (C["out"] + 0.8, 0.0)]
PK += [(C["fills"] - 0.11, 0.0), (C["fills"] + 0.05, 2.0), (C["shuts"], 2.0), (C["shuts"] + 0.12, 0.0)]
glow(B_PUMP, PK)
EMR = B_PUMP.inputs["Emission Color"]
for t, col in [(0, (0.98, 0.74, 0.27)), (C["wear"] - 0.02, (0.98, 0.74, 0.27)), (C["wear"], (1.0, 0.30, 0.24)), (C["out"] + 0.85, (1.0, 0.30, 0.24)), (C["out"] + 0.9, (0.98, 0.74, 0.27))]:
    EMR.default_value = (*col, 1); EMR.keyframe_insert("default_value", frame=F(t))
# cyan flow dots: up the drop pipe, along the pipe to the house, tank -> spigot
def dots(name, pts, r=0.13):
    bm = bmesh.new()
    for p in pts:
        res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
        bmesh.ops.translate(bm, verts=res["verts"], vec=p)
    return mesh_obj(name, bm, M_CYAN)
SP_UP = 1.4
FUP = dots("FlowUp", [(0.0, -0.13, PUMP_TOP + k * SP_UP) for k in range(23)])
FH = dots("FlowHouse", [(0.6 + k * SP_UP, -0.13, -2.0) for k in range(10)])
FLOW_WIN = [(C["push"], T_CAVE), (C["fills"], C["shuts"] + 0.1), (C["more"], T_CTA), (T_CTA + 0.4, DUR)]
bake_fn(FUP, "location", 2, lambda t: (t * 3.5) % SP_UP)
bake_fn(FH, "location", 0, lambda t: (t * 3.5) % SP_UP)
windows(FUP, [(C["push"], T_CAVE), (C["fills"], C["shuts"] + 0.1), (C["more"], DUR)])
windows(FH, [(C["fills"], C["shuts"] + 0.1), (C["more"], DUR)])
# ================= cave-in chunks =================
CH = []
for k in range(16):
    side = -1 if k % 2 else 1
    x0 = side * random.uniform(0.55, 0.85); z0 = random.uniform(-30.0, -18.0)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.16, 0.30))
    for vv in bm.verts: vv.co *= random.uniform(0.75, 1.2)
    o = mesh_obj(f"Chunk{k}", bm, M_AQ if z0 < WT else M_CLAY); o.location = (x0, random.uniform(0.15, 0.6), z0)
    t0 = T_CAVE + 0.04 * k; zf = BOT + 0.3 + 0.25 * (k % 4)
    bake_fn(o, "location", 2, lambda t, z0=z0, t0=t0, zf=zf: z0 if t < t0 else max(zf, z0 - 0.5 * 30.0 * (t - t0) ** 2))
    bake_fn(o, "location", 0, lambda t, x0=x0, t0=t0: x0 * (1.0 if t < t0 else max(0.25, 1.0 - 1.5 * (t - t0))))
    windows(o, [(C["now"], T_CS1)]); CH.append(o)
# ================= casing + screen + well cap (one group, slides in from above) =================
CASE = empty("CasingGroup")
lathe("CasingShell", tube_prof(RCI, RCO, -36.0, 0.55), M_CASE, 0.0, math.pi, 40).parent = CASE
for k in range(15):
    z0 = -36.0 - k * 0.4
    lathe(f"ScreenBand{k}", tube_prof(RCI, RCO, z0 - 0.22, z0), M_SCREEN, 0.0, math.pi, 40).parent = CASE
for a in (0.0, math.pi / 2, math.pi):
    box(f"ScreenRib{a:.1f}", RCI * math.cos(a) - 0.04, RCI * math.cos(a) + 0.04, max(0.0, RCI * math.sin(a) - 0.04), RCI * math.sin(a) + 0.07,
        -42.1, -36.0, M_SCREEN, CASE)
lathe("CasingPlug", [(0.0, -42.3), (RCO, -42.3), (RCO, -42.1), (0.0, -42.1)], M_SCREEN, 0.0, math.pi, 40).parent = CASE
cyl("WellCap", RCO + 0.08, 0.22, "Z", (0, 0, 0.65), M_CASE, CASE)
cyl("CapVent", 0.05, 0.25, "Z", (0.3, 0.2, 0.85), M_CASE, CASE)
def case_off(t):
    if t < T_CS0: return 0.0
    return PW([(T_CS0, 44.0), (T_CS1, 0.0)])(t)
bake_fn(CASE, "location", 2, case_off)
windows(CASE, [(T_B0, T_C0), (T_CS0, DUR)])
glow(B_CASE, [(0, 0)] + pulse(C["casing"] - 0.1, 1.0, up=0.2, hold=0.6))
glow(B_SCREEN, [(0, 0)] + pulse(C["screen"] - 0.1, 1.6, up=0.2, hold=0.9))
# screen beat: water dots stream in through the slots, sand grains stop at the screen
SW, SS = [], []
for k in range(14):
    side = 1 if k % 2 else -1; z = -36.6 - (k // 2) * 0.75
    o = dots(f"InDot{k}", [(0, 0, 0)], 0.075); o.location = (side * 3.0, -0.08, z)
    ph = random.random()
    bake_fn(o, "location", 0, lambda t, side=side, ph=ph: side * (3.2 - 3.0 * (((t * 0.9) + ph) % 1.0)))
    windows(o, [(C["lets2"] - 0.2, T_SC1)]); SW.append(o)
for k in range(12):
    side = 1 if k % 2 else -1; z = -36.4 - (k // 2) * 0.95
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.085)
    o = mesh_obj(f"Grain{k}", bm, M_SANDG); o.location = (side * 2.6, -0.08, z)
    t0 = C["sand"] - 0.5 + 0.04 * k
    bake_fn(o, "location", 0, lambda t, side=side, t0=t0: side * (2.6 - (2.6 - (RCO + 0.1)) * ease((t - t0) / 0.7)))
    windows(o, [(C["sand"] - 0.5, T_SC1)]); SS.append(o)
# ================= rain + dirty water down the outside of the casing =================
bm = bmesh.new()
for k in range(260):
    x = random.uniform(-9.0, 9.0)
    if abs(x) < 1.4: x += 2.8 * (1 if x >= 0 else -1)
    y = random.uniform(0.6, 14.0); z = random.uniform(12.2, 36.0)
    add_box(bm, x - 0.022, x + 0.022, y - 0.022, y + 0.022, z, z + 0.6)
RAIN = mesh_obj("Rain", bm, M_RAIN)
bake_fn(RAIN, "location", 2, lambda t: -((t * 16.0) % 12.0))
RAIN_WIN = [(T_B0, T_C0), (T_SC1, T_GR1)]
windows(RAIN, RAIN_WIN)
DIRT = empty("DirtyStreaks")
for side in (1, -1):
    x = side * (RCO + RB) / 2
    box(f"Dirt{side}", x - 0.13, x + 0.13, 0.02, 0.2, -1.0, 0.0, M_DIRT, DIRT)
DIRT.location = (0, 0, 0.1)
def dirt_len(t):
    if T_B0 <= t < T_C0: return PW([(C["rainwater"], 0.01), (C["drink"], -WT)])(t)
    if t >= T_SC1: return PW([(C["rain"], 0.01), (C["bacteria"], -WT)])(t)
    return 0.01
bake_fn(DIRT, "scale", 2, dirt_len)
windows(DIRT, [(C["rainwater"] - 0.1, T_C0), (C["rain"] - 0.1, T_GR0 + 0.5)])
glow(B_DIRT, [(0, 2.6)])
PUD = cyl("Puddle", 1.1, 0.03, "Z", (0, 1.3, 0.12), M_DIRT); windows(PUD, [(C["rainwater"], T_C0), (C["rain"], T_GR0 + 0.5)])
# grout fills the gap from the top down
GROUT = lathe("Grout", tube_prof(RCO, RB - 0.005, -12.0, 0.0), M_GROUT, 0.0, math.pi, 40); GROUT.location = (0, 0, 0.1)
bake_fn(GROUT, "scale", 2, lambda t: max(0.002, ease((t - T_GR0) / (T_GR1 - T_GR0))))
windows(GROUT, [(T_GR0, DUR)])
glow(B_GROUT, [(0, 0)] + pulse(C["grout"] - 0.1, 1.0, up=0.2, hold=0.5))
# ================= pressure tank (cut in half), bladder, air, water; pipe up to the spigot =================
TANK = lathe("PressureTank", [(0.0, TZ0 - 0.05), (TR + 0.03, TZ0 - 0.05), (TR + 0.03, TZ1 + 0.05), (0.0, TZ1 + 0.05),
                               (0.0, TZ1), (TR, TZ1), (TR, TZ0), (0.0, TZ0)], M_TANK, 0.0, math.pi, 40, loc=(TX, 0, 0), smooth=False)
cyl("TankFoot", TR * 0.8, 0.12, "Z", (TX, 0.25, TZ0 - 0.11), M_TANK)
def tank_level(t):
    return PW([(0, -2.35), (C["fills"], -2.35), (C["shuts"] + 0.1, -1.85), (C["air4"], -1.85), (C["more"] + 0.3, -2.3),
               (T_CTA, -2.3), (DUR, -2.45)])(t)
TW = half_cyl("TankWater", TR - 0.01, TX, 0.0, 0.006, 0.0, 1.0, M_TWATER); TW.location = (TX, 0.0, TZ0)
bake_fn(TW, "scale", 2, lambda t: tank_level(t) - TZ0)
BLAD = half_cyl("Bladder", TR - 0.005, TX, 0.0, 0.004, 0.0, 0.03, M_BLAD); BLAD.location = (TX, 0, 0)
bake_fn(BLAD, "location", 2, lambda t: tank_level(t))
AIR = half_cyl("TankAir", TR - 0.012, TX, 0.0, 0.008, 0.0, 1.0, M_AIR); AIR.location = (TX, 0, 0)
bake_fn(AIR, "location", 2, lambda t: tank_level(t) + 0.03); bake_fn(AIR, "scale", 2, lambda t: max(0.01, TZ1 - tank_level(t) - 0.04))
keyval(A_AIR, [(0, 0.15), (C["cushion"] - 0.05, 0.15), (C["cushion"] + 0.2, 0.6), (C["fills"], 0.6), (C["shuts"], 1.0), (C["more"], 1.0), (C["more"] + 0.5, 0.25)])
glow(B_TANK, [(0, 0)] + pulse(C["tank"] - 0.1, 0.8, up=0.2, hold=0.6))
cyl("TankRiser", 0.06, -0.25 - TZ1, "Z", (TX + 0.25, 0.0, (TZ1 - 0.25) / 2), M_PIPE)
cyl("TankInlet", 0.07, 0.5, "Z", (TX - 0.55 - 0.0, 0.0, -2.2), M_PIPE)
STREAM = cyl("Stream", 0.016, 1.0, "Z", (0, 0, -0.5), M_STREAM); STREAM.location = (SPX, SPY - 0.08, SPZ - 0.15)
bake_fn(STREAM, "scale", 2, lambda t: (SPZ - 0.15) - (0.112 + ybw(t)))
TAPS = [(C["start"], C["start"] + 0.32), (C["every"], C["every"] + 0.3), (C["tap"] + 0.15, C["tap"] + 0.42), (C["wear"], C["out"] + 0.3),
        (C["air4"], C["more"] + 0.2), (T_CTA + 0.3, DUR)]
windows(STREAM, TAPS)
WHEEL = bpy.data.objects["SpigotWheel"]
bake_fn(WHEEL, "rotation_euler", 2, lambda t: 2.5 if in_any(t, TAPS) else 0.0)
# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (1.3, -5.5, -8.5), (0.0, 0.3, -9.8), 20),
    (T_A1 - 0.05, (1.0, -4.8, -14.2), (0.0, 0.3, -15.6), 20),
    (T_A1, (2.5, -17.0, -6.0), (0.0, 0.0, -8.5), 22, "cut"),
    (T_B0 - 0.05, (2.0, -15.0, -6.5), (0.0, 0.0, -9.0), 22),
    (T_B0, (-3.5, -14.0, -2.0), (0.3, 0.0, -5.5), 20, "cut"),
    (T_C0 - 0.05, (-2.5, -12.0, -3.0), (0.3, 0.0, -6.5), 20),
    (T_C0, (7.0, -34.0, -8.0), (7.0, 0.0, -9.0), 20, "cut"),
    (T_W0 - 0.05, (6.5, -31.0, -8.0), (7.0, 0.0, -9.0), 20),
    (T_W0, (1.6, -7.0, 0.5), (0.0, 0.3, -1.5), 20, "cut"),
    (C["fine"], (1.2, -5.2, -13.8), (0.0, 0.3, -15.3), 20),
    (T_DEEP0, (1.2, -5.5, -12.5), (0.0, 0.3, -14.0), 20),
    (T_DEEP1, (5.0, -30.0, -20.0), (1.0, 0.0, -21.0), 20),
    (T_SU0 - 0.05, (5.0, -29.0, -20.0), (1.0, 0.0, -21.0), 20),
    (T_SU0, (2.5, -17.0, -6.0), (0.0, 0.0, -8.5), 22, "cut"),
    (C["air"], (2.2, -16.0, -7.0), (0.0, 0.0, -9.0), 22),
    (C["pushes"], (1.2, -8.0, -12.5), (0.0, 0.0, -14.5), 22),
    (C["but"], (1.2, -8.0, -12.8), (0.0, 0.0, -14.5), 22),
    (C["thirtythree2"], (2.5, -18.0, -8.0), (0.0, 0.0, -10.0), 22),
    (T_SU1 - 0.05, (2.5, -18.5, -8.0), (0.0, 0.0, -10.0), 22),
    (T_SU1, (4.0, -30.0, -17.0), (0.0, 0.0, -17.0), 20, "cut"),
    (C["under"], (1.8, -12.0, -28.0), (0.0, 0.0, -30.0), 20),
    (C["now"] - 0.05, (1.6, -10.0, -27.0), (0.0, 0.0, -28.0), 20),
    (C["now"], (1.6, -9.0, -23.0), (0.0, 0.0, -24.0), 18, "cut"),
    (T_CS0, (2.0, -11.0, -22.0), (0.0, 0.0, -23.0), 18),
    (T_CS1, (4.0, -28.0, -17.0), (0.0, 0.0, -18.0), 20),
    (T_SC0 - 0.05, (4.0, -27.0, -17.0), (0.0, 0.0, -18.0), 20),
    (T_SC0, (1.4, -6.5, -38.5), (0.0, 0.0, -38.8), 20, "cut"),
    (T_SC1 - 0.05, (1.0, -5.5, -38.8), (0.0, 0.0, -38.8), 20),
    (T_SC1, (-3.5, -14.0, -2.5), (0.3, 0.0, -6.0), 20, "cut"),
    (C["gap"], (-3.0, -13.0, -3.0), (0.3, 0.0, -6.0), 20),
    (T_GR1, (-1.5, -9.0, -3.5), (0.4, 0.0, -5.5), 20),
    (C["last"] - 0.05, (-1.4, -8.6, -3.5), (0.4, 0.0, -5.5), 20),
    (C["last"], (9.0, -31.0, -15.0), (8.5, 0.0, -15.5), 20, "cut"),
    (C["so3"] - 0.05, (9.0, -30.0, -15.0), (8.5, 0.0, -15.5), 20),
    (C["so3"], (15.6, -6.5, -0.8), (14.9, 0.5, -1.3), 20, "cut"),
    (C["more"] - 0.05, (15.4, -5.8, -0.9), (14.9, 0.5, -1.3), 20),
    (C["more"], (14.0, -9.0, 0.5), (13.0, 0.0, -1.0), 20, "cut"),
    (T_CTA - 0.05, (8.5, -34.0, -12.0), (8.0, 0.0, -13.0), 20),
    (T_CTA, (13.6, 0.35, 0.72), (14.2, 2.2, 0.38), 32, "cut"),
    (DUR, (13.8, 0.75, 0.62), (14.2, 2.2, 0.36), 32),
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
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()
# ================= world + light: a yard in daylight =================
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
bl_d = bpy.data.lights.new("BasementLight", "POINT"); bl_d.energy = 400; bl_d.color = (1.0, 0.88, 0.7); bl_d.shadow_soft_size = 0.6
blo = bpy.data.objects.new("BasementLight", bl_d); scene.collection.objects.link(blo); blo.location = (17.0, 4.0, -0.8)

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
    "bucket": lambda t: Vector((0.25, 0.3, bucket_z(t) + 0.2)),
    "spipe": lambda t: Vector((0.13, -0.05, -10.0)),
    "limit": lambda t: Vector((1.6, -0.1, SUC_TOP)),
    "water": lambda t: Vector((-0.5, -0.05, WT - 1.5)),
    "pump": lambda t: Vector((0.3, -0.2, pump_z(t) - 1.2)),
    "casing": lambda t: Vector((RCO, -0.1, -20.0 + case_off(t))),
    "screen": lambda t: Vector((RCO, -0.1, -39.0 + case_off(t))),
    "grout": lambda t: Vector((-(RCO + RB) / 2, -0.05, -3.0)),
    "tank": lambda t: Vector((TX + TR, -0.1, -2.6)),
    "air": lambda t: Vector((TX - 0.2, -0.1, (tank_level(t) + TZ1) / 2)),
    "spigot": lambda t: Vector((SPX, SPY - 0.1, SPZ)),
    "aquifer": lambda t: Vector((-4.0, -0.05, -30.0)),
    "depth": lambda t: Vector((-2.7, -0.1, -bore_depth(t))),
}
anchors = {k: [] for k in ANCHP}
for fr in (range(1, FRAMES + 1) if not os.environ.get("COVER") else []):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCHP.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
R3 = lambda a, b: [round(a, 3), round(b, 3)]
events = {"dip1": 3.6, "dip2": round(C["fine"] + 0.1, 3), "col1": R3(T_A1 + 0.35, C["feet"] + 0.1), "col2": R3(C["lowers"], C["thirtythree2"] + 0.4),
          "deep": R3(T_DEEP0, T_DEEP1), "pumpdrop": R3(T_PD0, T_PD1), "cave": round(T_CAVE, 3), "casing": R3(T_CS0, T_CS1),
          "grout": R3(T_GR0, T_GR1), "taps": [R3(a, b) for a, b in TAPS], "rain": [R3(a, b) for a, b in RAIN_WIN], "cta": round(T_CTA, 3)}
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
