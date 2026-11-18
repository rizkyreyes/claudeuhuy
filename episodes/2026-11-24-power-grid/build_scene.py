# Power grid (3d-31): how electricity gets to your outlet. Claim-first hook ("The electricity in your outlet traveled here at hundreds of
# thousands of volts."): close on a wall outlet in a cut-open wall, a cyan pulse runs down the cable -> what-if: the wires glow red, sparks,
# the plate and drywall chips fall (rigid body) -> aerial of the whole route with 3 gold markers (step-up, substation, pole can) -> power
# plant, the hall front wall cut away: spinning generator -> step-up transformer next door, tank cut open: iron core + two copper coils,
# oil fills the tank (Mantaflow, laptop bake) -> the output coil's turns light up from the bottom, 765,000 -> one span close-up: fat red
# current beads + red-hot wire turn into thin cyan beads, 4 heat blocks drop to 1 ("a quarter") -> low flyover along the tower line ->
# studio: conductor cutaway (steel core strands + two aluminum layers) -> insulator string close-up, discs ripple -> substation yard ->
# down the street pole line -> pole can, cut open: center-tapped secondary, gold + cyan halves -> house interior: outlet gets the gold
# half, dryer outlet gets both -> aerial, 5% -> fly back into the house to the first frame (loop: "...even though" -> hook).
# Illustrative (1 unit = 1 m): generic plant, single-phase transformer cutaways (real step-up units are usually three-phase), generic lattice
# towers 75 m apart (real spans are longer), conductor and current beads drawn oversized. No logos, no people.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu] [--bake-fluid]
import bpy, bmesh, json, math, os, random, sys
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
CUES = [("the", "The"), ("outlet", "outlet"), ("hundreds", "hundreds"), ("volts", "volts."), ("let", "Let"), ("house", "house,"),
        ("wire", "wire"), ("walls", "walls"), ("fail", "fail."), ("so", "So"), ("voltage0", "voltage"), ("three", "three"), ("way", "way."),
        ("starts", "starts"), ("plant", "plant,"), ("generator", "generator"), ("lower", "lower"), ("next", "Next"), ("stepup", "step-up"),
        ("transformer", "transformer"), ("inside", "Inside,"), ("copper", "copper"), ("coils", "coils"), ("iron", "iron"), ("core", "core."),
        ("output", "output"), ("turns", "turns,"), ("climbs", "climbs,"), ("seven", "seven"), ("volts2", "volts."), ("why", "Why"),
        ("same", "Same"), ("higher", "higher"), ("less", "less"), ("current", "current."), ("wires", "wires"), ("heat", "heat,"),
        ("square", "square"), ("double", "Double"), ("quarter", "quarter."), ("now", "Now"), ("cross", "cross"), ("miles", "miles."),
        ("the2", "The"), ("bare", "bare."), ("aluminum", "Aluminum,"), ("steel", "steel"), ("air", "Air"), ("insulation", "insulation,"),
        ("insulator", "insulator"), ("towers", "towers."), ("near", "Near"), ("substation", "substation"), ("under", "under"),
        ("sends", "sends"), ("street", "street."), ("then", "Then"), ("gray", "gray"), ("pole", "pole"), ("job", "job:"), ("two", "two"),
        ("split", "split"), ("halves", "halves"), ("one", "one"), ("twenty", "twenty."), ("your", "Your"), ("outlet2", "outlet"),
        ("half", "half."), ("your2", "Your"), ("dryer", "dryer"), ("both", "both."), ("only", "Only"), ("five", "five"), ("lost", "lost"),
        ("trip", "trip."), ("and", "And"), ("none", "none"), ("high", "high"), ("reaches", "reaches"), ("even", "even"), ("though", "though")]
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
CL = coll("Grid")
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



# ================= extra helpers =================
FLUID_BAKE = "--bake-fluid" in ARGS
def add_seg(bm, p0, p1, r, seg=8, mi=0):
    """Round tube segment between two points."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    if L < 1e-6: return
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=L); vs = res["verts"]
    M = Matrix.Translation((p0 + p1) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=M, verts=vs)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
def add_poly(bm, pts, r, seg=8, mi=0):
    for a, b in zip(pts, pts[1:]): add_seg(bm, a, b, r, seg, mi)
def sag_pts(a, b, sag, n=14):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, 4 * sag * (i / n) * (1 - i / n))) for i in range(n + 1)]
def poly_obj(name, pts, r, m_, seg=8):
    bm = bmesh.new(); add_poly(bm, pts, r, seg); return mesh_obj(name, bm, m_)
class Path:
    def __init__(self, pts):
        self.p = [Vector(x) for x in pts]; self.s = [0.0]
        for a, b in zip(self.p, self.p[1:]): self.s.append(self.s[-1] + (b - a).length)
        self.L = self.s[-1]
    def at(self, s):
        import bisect
        s = max(0.0, min(self.L, s)); i = min(len(self.p) - 2, max(0, bisect.bisect_right(self.s, s) - 1))
        seg = self.s[i + 1] - self.s[i]
        return self.p[i].lerp(self.p[i + 1], (s - self.s[i]) / seg if seg > 0 else 0)
def sphere_mesh(name, r, sub=2):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    try: me.shade_smooth()
    except Exception: pass
    return me
def obj_from(name, me, m_=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, me); CL.objects.link(o); o.location = loc
    if m_ and not me.materials: me.materials.append(m_)
    return o
def beads(name, path, n, r, m_, wins, speed, scale_fn=None, loop_period=None):
    """n glowing beads running along a Path, visible only inside wins. loop_period makes t=0 and t=DUR identical."""
    me = sphere_mesh(name, r); me.materials.append(m_); out = []
    gap = path.L / n
    for i in range(n):
        o = obj_from(f"{name}{i}", me)
        def fn(t, i=i):
            if loop_period: u = (t % loop_period) / loop_period; s = (u + i / n) % 1.0 * path.L
            else: s = (i * gap + speed * t) % path.L
            return tuple(path.at(s))
        bake_loc(o, fn)
        if scale_fn: bake_scale(o, lambda t, i=i: (scale_fn(t, i),) * 3)
        windows(o, wins); out.append(o)
    return out
def emit_mat(name, rgb, strength):
    m, b = mat(name, (0.02, 0.02, 0.02), rough=0.5, emit_rgb=rgb); b.inputs["Emission Strength"].default_value = strength; return m, b

# ================= timing =================
T_HOOK = (0.0, C["let"]); T_FAIL = (C["let"], C["so"]); T_AIR1 = (C["so"], C["starts"]); T_PLANT = (C["starts"], C["next"])
T_XF = (C["next"], C["why"]); T_IN = (C["inside"], C["why"]); T_DEMO = (C["why"], C["now"]); T_FLY = (C["now"], C["the2"])
T_COND = (C["the2"], C["air"]); T_INS = (C["air"], C["near"]); T_SUB = (C["near"], C["then"]); T_CAN = (C["then"], C["your"])
T_ROOM = (C["your"], C["only"]); T_AIR2 = (C["only"], C["and"]); T_BACK = (C["and"], DUR)

# ================= materials =================
M_GRASS, _ = mat("Grass", (0.11, 0.21, 0.07), rough=0.9, noise=0.08)
M_ROAD, _ = mat("Asphalt", (0.035, 0.035, 0.038), rough=0.85, noise=0.6)
M_GRAVEL, _ = mat("Gravel", (0.30, 0.29, 0.27), rough=0.95, noise=3.0)
M_CONC, _ = mat("Concrete", (0.50, 0.50, 0.48), rough=0.8, noise=0.9)
M_GALV, _ = mat("Galvanized", (0.58, 0.60, 0.62), rough=0.35, metallic=0.85)
M_DARK, _ = mat("DarkSteel", (0.12, 0.13, 0.14), rough=0.45, metallic=0.7)
M_IRON, B_IRON = mat("IronCore", (0.20, 0.22, 0.25), rough=0.4, metallic=0.75, emit_rgb=(0.30, 0.92, 1.0))
M_PAINT, _ = mat("TankPaint", (0.17, 0.19, 0.20), rough=0.5, metallic=0.2)
M_PORC, _ = mat("Porcelain", (0.36, 0.20, 0.12), rough=0.15)
M_GLASSI, B_GLASSI = mat("InsulatorGlass", (0.18, 0.42, 0.36), rough=0.08, emit_rgb=(0.30, 0.92, 1.0))
M_HALL, _ = mat("HallWall", (0.66, 0.64, 0.58), rough=0.7)
M_ROOF, _ = mat("HallRoof", (0.18, 0.19, 0.20), rough=0.7)
M_STACK, _ = mat("Stack", (0.62, 0.60, 0.56), rough=0.7)
M_RED, _ = mat("PoleRed", (0.55, 0.10, 0.08), rough=0.5)
M_BLUE, _ = mat("PoleBlue", (0.08, 0.16, 0.50), rough=0.5)
M_CU, B_CU = mat("Copper", (0.85, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_AL, B_AL = mat("Aluminum", (0.80, 0.82, 0.85), rough=0.25, metallic=1.0, emit_rgb=(1.0, 1.0, 1.0))
M_STEELC, B_STEELC = mat("SteelCore", (0.35, 0.36, 0.38), rough=0.35, metallic=0.9, emit_rgb=(0.30, 0.92, 1.0))
M_WIRE, B_WIRE = mat("LineWire", (0.55, 0.57, 0.60), rough=0.3, metallic=0.9, emit_rgb=(0.30, 0.92, 1.0))
M_WOOD, _ = mat("PoleWood", (0.24, 0.16, 0.10), rough=0.85, noise=4.0)
M_SIDING, _ = mat("Siding", (0.80, 0.76, 0.68), rough=0.6)
M_SHINGLE, _ = mat("Shingle", (0.20, 0.10, 0.08), rough=0.8, noise=2.0)
M_DRY, _ = mat("Drywall", (0.86, 0.84, 0.80), rough=0.85)
M_STUD, _ = mat("Stud", (0.72, 0.53, 0.32), rough=0.75, noise=6.0)
M_FLOOR, _ = mat("FloorWood", (0.45, 0.30, 0.18), rough=0.4, noise=3.0)
M_WHITE, _ = mat("OutletWhite", (0.90, 0.89, 0.86), rough=0.3)
M_BOX, _ = mat("OutletBox", (0.10, 0.25, 0.60), rough=0.4)
M_SLOT, _ = mat("Slot", (0.01, 0.01, 0.01), rough=0.6)
M_CABLE, B_CABLE = mat("Cable", (0.85, 0.72, 0.25), rough=0.5, emit_rgb=(1.0, 0.30, 0.24))
M_HOT, B_HOT = mat("HotGold", (0.25, 0.20, 0.08), rough=0.4, emit_rgb=(0.98, 0.74, 0.27))
M_HOT2, B_HOT2 = mat("HotCyan", (0.08, 0.18, 0.22), rough=0.4, emit_rgb=(0.30, 0.92, 1.0))
M_NEU, B_NEU = mat("Neutral", (0.85, 0.85, 0.85), rough=0.4, emit_rgb=(1.0, 1.0, 1.0))
M_TRIP, _ = mat("Triplex", (0.10, 0.10, 0.11), rough=0.5)
M_DRYER, _ = mat("Dryer", (0.92, 0.92, 0.93), rough=0.25)
M_DOOR, _ = mat("DryerDoor", (0.10, 0.12, 0.14), rough=0.05, metallic=0.4)
M_GOLDG, B_GOLDG = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 6.0)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 6.0)
M_REDG, B_REDG = emit_mat("RedGlow", (1.0, 0.15, 0.08), 6.0)
M_LEAVES, _ = mat("Leaves", (0.07, 0.17, 0.05), rough=0.8, noise=1.5)
M_TRUNK, _ = mat("Trunk", (0.20, 0.13, 0.08), rough=0.9)
M_CYC, _ = mat("Cyc", (0.025, 0.03, 0.04), rough=0.6)
M_OIL, B_OIL, _V = water_sec("Oil", glow_rgb=(0.98, 0.74, 0.27), vol_rgb=(0.85, 0.55, 0.12), dens=0.05)

# ================= ground, road =================
def plane(name, x0, x1, y0, y1, z, m_):
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]; bm.faces.new(vs)
    return mesh_obj(name, bm, m_)
GROUND = plane("Ground", -2600, 3800, -2600, 2600, 0.0, M_GRASS)
ROAD = box("Road", 985, 1330, -17.0, -9.0, -0.02, 0.03, M_ROAD)
bm = bmesh.new()
for k in range(40):
    x = 990 + k * 8.5; add_box(bm, x, x + 4.0, -13.1, -12.9, 0.03, 0.035)
DASH = mesh_obj("RoadDash", bm, M_WHITE)
DRIVE = box("Driveway", 1207.5, 1211.0, -9.0, 6.0, -0.01, 0.025, M_CONC)

# ================= power plant (x -45..12) =================
HALL = (-45.0, 12.0, -15.0, 15.0, 0.0, 18.0)
bm = bmesh.new()
add_box(bm, -45.0, 12.0, 14.4, 15.0, 0, 18)           # back wall
add_box(bm, -45.0, -44.4, -15.0, 15.0, 0, 18)          # left wall
add_box(bm, 11.4, 12.0, -15.0, 15.0, 0, 18)            # right wall
HALL_W = mesh_obj("HallWalls", bm, M_HALL)
HALL_ROOF = box("HallRoof", -45.5, 12.5, -15.5, 15.5, 18.0, 18.8, M_ROOF)
HALL_FRONT = box("HallFront", -45.0, 12.0, -15.0, -14.4, 0, 18, M_HALL)
HALL_FLOOR = box("HallFloor", -45.0, 12.0, -15.0, 15.0, -0.02, 0.05, M_CONC)
STACK = full_cyl("Stack", 3.2, -30.0, 26.0, 0.0, 62.0, M_STACK, seg=40)
STACK_BAND = full_cyl("StackBand", 3.25, -30.0, 26.0, 56.0, 59.0, M_RED, seg=40)
BOILER = box("BoilerHouse", -70.0, -46.0, -12.0, 16.0, 0, 34, M_HALL)
BOILER_R = box("BoilerRoof", -70.5, -45.5, -12.5, 16.5, 34, 34.8, M_ROOF)
GZ = 4.2
TURB = cyl("SteamTurbine", 2.4, 13.0, "X", (-31.0, 0, GZ), M_GALV, seg=40)
TURB2 = cyl("SteamTurbineCone", 2.0, 2.0, "X", (-23.5, 0, GZ), M_GALV, seg=40)
SHAFT = cyl("Shaft", 0.45, 40.0, "X", (-15.0, 0, GZ), M_GALV, seg=24)
PED = box("GenPedestal", -40.0, -6.0, -3.2, 3.2, 0.05, 1.4, M_CONC)
# generator: stator half-cylinder (front cut away), copper bars on the cut ring, spinning rotor with red/blue poles
STATOR = lathe("Stator", tube_prof(2.25, 3.2, -4.5, 4.5), M_IRON, a0=0.0, ang=math.pi, seg=48)
STATOR.rotation_euler = (0, math.radians(90), 0); STATOR.location = (-13.0, 0, GZ)

bm = bmesh.new()
for k in range(13):
    a = math.radians(180.0 * (k + 0.5) / 13.0)
    y, z = 2.45 * math.sin(a), 2.45 * math.cos(a)
    add_box(bm, -4.9, 4.9, y - 0.14, y + 0.14, z - 0.16, z + 0.16)
for k in range(13):                                      # end turns (copper loops outside the iron)
    a = math.radians(180.0 * (k + 0.5) / 13.0)
    for sx in (-1, 1):
        add_seg(bm, (sx * 4.9, 2.45 * math.sin(a), 2.45 * math.cos(a)), (sx * 5.3, 2.0 * math.sin(a), 2.0 * math.cos(a)), 0.13, 6)
GEN_CU = mesh_obj("StatorCopper", bm, M_CU); GEN_CU.location = (-13.0, 0, GZ)
ROTOR = cyl("Rotor", 1.9, 8.2, "X", (0, 0, 0), M_DARK, seg=48); ROTOR.location = (-13.0, 0, GZ)
bm = bmesh.new()
for k in range(4):
    a = k * math.pi / 2; c = Vector((0, 1.95 * math.cos(a), 1.95 * math.sin(a)))
    r_ = bmesh.ops.create_cube(bm, size=1.0); vs = r_["verts"]
    bmesh.ops.scale(bm, verts=vs, vec=(7.6, 0.25, 1.4)); bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "X"))
    bmesh.ops.translate(bm, verts=vs, vec=c)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = k % 2
POLES = mesh_obj("RotorPoles", bm, [M_RED, M_BLUE], parent=ROTOR)
bake_fn(ROTOR, "rotation_euler", 0, lambda t: 2 * math.pi * 1.2 * t)
EXC = cyl("GenHousingEnd", 3.4, 0.6, "X", (-17.8, 0, GZ), M_PAINT, seg=48)
# isolated-phase bus duct: generator -> through the hall wall -> transformer low-voltage side
bm = bmesh.new(); add_poly(bm, [(-8.0, 0, GZ), (-4.0, 0, 7.5), (24.5, 0, 7.5)], 0.45, 16)
BUS = mesh_obj("BusDuct", bm, M_PAINT)

# ================= transformers =================
def transformer(name, cx, cy, s=1.0, cut=False):
    """Oil tank + radiator fins + bushings. cut=True: separate front wall (hidden for the cutaway)."""
    hx, hy, h = 4.0 * s, 2.5 * s, 6.0 * s; z0 = 0.5 * s
    parts = {}
    parts["pad"] = box(name + "Pad", cx - hx - 2 * s, cx + hx + 2 * s, cy - hy - 2 * s, cy + hy + 3 * s, 0, z0, M_CONC)
    bm = bmesh.new(); w = 0.15 * s
    add_box(bm, cx - hx, cx + hx, cy + hy - w, cy + hy, z0, z0 + h)       # back
    add_box(bm, cx - hx, cx - hx + w, cy - hy, cy + hy, z0, z0 + h)       # left
    add_box(bm, cx + hx - w, cx + hx, cy - hy, cy + hy, z0, z0 + h)       # right
    add_box(bm, cx - hx, cx + hx, cy - hy, cy + hy, z0 - 0.01, z0 + w)     # bottom
    add_box(bm, cx - hx - 0.1 * s, cx + hx + 0.1 * s, cy - hy - 0.1 * s, cy + hy + 0.1 * s, z0 + h, z0 + h + 0.3 * s)  # lid
    parts["tank"] = mesh_obj(name + "Tank", bm, M_PAINT)
    parts["front"] = box(name + "Front", cx - hx, cx + hx, cy - hy, cy - hy + 0.15 * s, z0, z0 + h, M_PAINT)
    bm = bmesh.new()
    for k in range(14):
        x = cx - hx + 0.5 * s + k * (2 * hx - 1.0 * s) / 13
        add_box(bm, x - 0.04 * s, x + 0.04 * s, cy + hy, cy + hy + 1.6 * s, z0 + 0.6 * s, z0 + h - 0.6 * s)
    add_seg(bm, (cx - hx, cy + hy + 0.8 * s, z0 + h - 0.5 * s), (cx + hx, cy + hy + 0.8 * s, z0 + h - 0.5 * s), 0.15 * s)
    add_seg(bm, (cx - hx, cy + hy + 0.8 * s, z0 + 0.5 * s), (cx + hx, cy + hy + 0.8 * s, z0 + 0.5 * s), 0.15 * s)
    parts["fins"] = mesh_obj(name + "Fins", bm, M_PAINT)
    bm = bmesh.new(); tops = []
    for k, yy in enumerate((-1.5, 0.0, 1.5)):
        bx, by, bz = cx + 2.2 * s, cy + yy * s, z0 + h + 0.3 * s
        add_cyl(bm, 0.18 * s, 3.2 * s, "Z", (bx, by, bz + 1.6 * s), seg=16)
        for j in range(9): add_cyl(bm, 0.34 * s, 0.08 * s, "Z", (bx, by, bz + 0.4 * s + j * 0.32 * s), seg=16)
        tops.append(Vector((bx, by, bz + 3.3 * s)))
    lows = []
    for k, yy in enumerate((-1.2, 0.0, 1.2)):
        bx, by, bz = cx - 2.6 * s, cy + yy * s, z0 + h + 0.3 * s
        add_cyl(bm, 0.16 * s, 1.0 * s, "Z", (bx, by, bz + 0.5 * s), seg=16)
        for j in range(3): add_cyl(bm, 0.28 * s, 0.07 * s, "Z", (bx, by, bz + 0.25 * s + j * 0.28 * s), seg=16)
        lows.append(Vector((bx, by, bz + 1.0 * s)))
    parts["bush"] = mesh_obj(name + "Bushings", bm, M_PORC)
    return parts, tops, lows
XF, XF_TOPS, XF_LOWS = transformer("StepUp", 30.0, 0.0, 1.0, cut=True)
XC = Vector((30.0, 0.0, 0.5))
# inside: iron core (two legs + yokes) with a primary (few thick turns) and a secondary (many thin turns)
LEG1, LEG2 = 27.6, 32.4
bm = bmesh.new()
add_box(bm, LEG1 - 0.5, LEG1 + 0.5, -0.5, 0.5, 1.0, 6.0); add_box(bm, LEG2 - 0.5, LEG2 + 0.5, -0.5, 0.5, 1.0, 6.0)
add_box(bm, LEG1 - 0.5, LEG2 + 0.5, -0.5, 0.5, 1.0, 1.8); add_box(bm, LEG1 - 0.5, LEG2 + 0.5, -0.5, 0.5, 5.2, 6.0)
CORE = mesh_obj("IronCore", bm, M_IRON)
def coil(name, cx, z0, z1, n, r_major, r_minor, m_):
    bm = bmesh.new()
    for k in range(n):
        z = z0 + (z1 - z0) * (k + 0.5) / n
        pts = [(cx + r_major * math.cos(2 * math.pi * j / 28), r_major * math.sin(2 * math.pi * j / 28), z) for j in range(29)]
        add_poly(bm, pts, r_minor, 8)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
PRIM = coil("PrimaryCoil", LEG1, 2.0, 5.0, 6, 0.95, 0.17, M_CU)
# secondary: level mask (emission where local z < keyed level) = the voltage "climbing" turn by turn
M_SEC, B_SEC = mat("SecondaryCopper", (0.85, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
nt = M_SEC.node_tree
tcn = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tcn.outputs["Object"], sep.inputs[0])
LEVEL_KEYS = [(0, -1.0), (C["turns"], -1.0), (C["seven"] + 0.6, 6.5), (DUR, 6.5)]
lvl = VALUE(nt, "SecLevel", LEVEL_KEYS)
ltn = MATH(nt, "LESS_THAN", sep.outputs["Z"], lvl); sc_ = MATH(nt, "MULTIPLY", ltn, 7.0)
nt.links.new(sc_, B_SEC.inputs["Emission Strength"])
SEC = coil("SecondaryCoil", LEG2, 1.95, 5.05, 22, 0.95, 0.065, M_SEC)
OIL = box("OilLevel", 26.2, 33.8, -2.3, 2.3, 0.65, 6.3, M_OIL)
bake_scale(OIL, lambda t: (1, 1, 0.0001 if t < C["inside"] else max(0.0001, min(1.0, (t - C["inside"]) / 3.4))))
OIL.location = (0, 0, 0)
# shift oil origin to its bottom so the scale grows upwards
for v in OIL.data.vertices: v.co.z -= 0.65
OIL.location = (0, 0, 0.65)
FL_DOM = box("OilDomain", 26.2, 33.8, -2.3, 2.3, 0.65, 6.3, M_OIL)
FL_IN = cyl("OilInflow", 0.35, 0.4, "Z", (29.0, 1.6, 6.0), M_OIL, seg=12)
fx.fluid_domain(FL_DOM, FL_IN, eff=[CORE], res=64, start=F(C["inside"] - 0.3), end=F(C["inside"] + 3.6), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_IN.hide_render = True
if FLUID_BAKE: windows(FL_DOM, [(C["inside"] - 0.3, C["why"])]); windows(OIL, [])
else: windows(FL_DOM, []); windows(OIL, [(C["inside"], C["why"])])
windows(XF["front"], [(0, C["inside"]), (C["why"], DUR)])
for o in (PRIM, SEC, CORE): windows(o, [(C["next"], C["why"])])
glow(B_CU, [(0, 0.0), *pulse(C["generator"] + 0.1, 3.0, hold=1.2), *pulse(C["copper"], 4.0, hold=1.6), (DUR, 0.0)])
glow(B_IRON, [(0, 0.0), *pulse(C["iron"], 2.5, hold=0.6), (DUR, 0.0)])

# ================= transmission line: 12 lattice towers 75 m apart =================
TOWER_X = [80.0 + 75.0 * i for i in range(12)]
def w_at(z): return 4.0 + (1.3 - 4.0) * min(z, 34.0) / 34.0 if z <= 34 else 1.3 + (0.6 - 1.3) * (z - 34) / 4.0
bm = bmesh.new(); BW = 0.16
levels = [0.0, 5.5, 11.0, 16.0, 21.0, 25.0, 28.0, 31.5, 35.0, 38.0]
for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
    add_poly(bm, [(sx * w_at(z), sy * w_at(z), z) for z in levels], BW * 1.4, 6)
for za, zb in zip(levels, levels[1:]):
    wa, wb = w_at(za), w_at(zb)
    for face in range(4):
        c = [(wa, wa), (wa, -wa), (-wa, -wa), (-wa, wa)]; d = [(wb, wb), (wb, -wb), (-wb, -wb), (-wb, wb)]
        a0, a1 = c[face], c[(face + 1) % 4]; b0, b1 = d[face], d[(face + 1) % 4]
        add_seg(bm, (*a0, za), (*b1, zb), BW, 4); add_seg(bm, (*a1, za), (*b0, zb), BW, 4)
        add_seg(bm, (*b0, zb), (*b1, zb), BW, 4)
ARM_LOW, ARM_UP = 28.0, 35.0
for side in (-1, 1):                                         # lower arms to y = +-9.5
    w = w_at(ARM_LOW)
    for xx in (-w, w):
        add_seg(bm, (xx, side * w, ARM_LOW), (0, side * 9.5, ARM_LOW), BW, 4)
        add_seg(bm, (xx, side * w, ARM_LOW + 3.0), (0, side * 9.5, ARM_LOW), BW, 4)
w = w_at(ARM_UP)
for xx in (-w, w):
    add_seg(bm, (xx, w, ARM_UP), (0, 6.5, ARM_UP), BW, 4); add_seg(bm, (xx, w, ARM_UP + 2.2), (0, 6.5, ARM_UP), BW, 4)
add_seg(bm, (0, 0, 38.0), (0, 0, 40.0), BW * 1.6, 6)
TOWER_ME = bpy.data.meshes.new("TowerMesh"); bm.to_mesh(TOWER_ME); bm.free(); TOWER_ME.materials.append(M_GALV)
TOWERS = [obj_from(f"Tower{i}", TOWER_ME, loc=(x, 0, 0)) for i, x in enumerate(TOWER_X)]
bm = bmesh.new()
for x in TOWER_X:
    for sx in (-1, 1):
        for sy in (-1, 1): add_box(bm, x + sx * 4.0 - 0.8, x + sx * 4.0 + 0.8, sy * 4.0 - 0.8, sy * 4.0 + 0.8, -0.1, 0.5)
FOOT = mesh_obj("TowerFootings", bm, M_CONC)
INS_L = 3.0; NDISC = 12
def ins_string(bm, top):
    top = Vector(top); add_seg(bm, top, top - Vector((0, 0, INS_L)), 0.035, 6)
    for j in range(NDISC): add_cyl(bm, 0.16, 0.06, "Z", top - Vector((0, 0, 0.35 + j * (INS_L - 0.6) / (NDISC - 1))), seg=20)
PHASES = [(-9.5, ARM_LOW), (9.5, ARM_LOW), (6.5, ARM_UP)]
INS_TOWER = 6                       # this tower's front string is built from separate discs (ripple close-up)
bm = bmesh.new()
for i, x in enumerate(TOWER_X):
    for k, (py, pz) in enumerate(PHASES):
        if i == INS_TOWER and k == 0: continue
        ins_string(bm, (x, py, pz))
INS = mesh_obj("InsulatorStrings", bm, M_GLASSI)
xI, yI, zI = TOWER_X[INS_TOWER], PHASES[0][0], PHASES[0][1]
bm = bmesh.new(); add_seg(bm, (xI, yI, zI), (xI, yI, zI - INS_L), 0.035, 6); INS_ROD = mesh_obj("InsRod", bm, M_GALV)
DISCS = []
for j in range(NDISC):
    zc = zI - 0.35 - j * (INS_L - 0.6) / (NDISC - 1)
    d_ = cyl(f"Disc{j}", 0.16, 0.06, "Z", (0, 0, 0), M_GLASSI, seg=24); d_.location = (xI, yI, zc)
    bake_scale(d_, lambda t, j=j: (1 + 0.45 * math.sin(math.pi * lin((t - C["insulator"] - 0.07 * j) / 0.35)),) * 2 + (1.0,))
    DISCS.append(d_)
glow(B_GLASSI, [(0, 0.0), *pulse(C["insulator"], 1.2, hold=1.2), (DUR, 0.0)])
def attach(i, k):
    py, pz = PHASES[k]; return Vector((TOWER_X[i], py, pz - INS_L))
# substation dead-end gantry at x 948, conductors land at z 14
GX = 948.0
SUB_IN = [Vector((GX, py, 14.0)) for py, pz in PHASES]
bm = bmesh.new()
for i in range(len(TOWER_X) - 1):
    for k in range(3): add_poly(bm, sag_pts(attach(i, k), attach(i + 1, k), 3.6), 0.12, 6)
for k in range(3):
    add_poly(bm, sag_pts(attach(len(TOWER_X) - 1, k), SUB_IN[k], 2.4), 0.12, 6)
    a0 = XF_TOPS[k]; add_poly(bm, sag_pts(a0, attach(0, k), 2.0), 0.12, 6)
LINES = mesh_obj("LineConductors", bm, M_WIRE)
glow(B_WIRE, [(0, 0.0), (T_AIR1[0] - 0.01, 0.0), (T_AIR1[0] + 0.4, 1.6), (T_AIR1[1] - 0.05, 1.6), (T_AIR1[1], 0.0),
              (T_FLY[0] - 0.01, 0.0), (T_FLY[0] + 0.3, 1.6), (T_FLY[1] - 0.05, 1.6), (T_FLY[1], 0.0),
              (T_AIR2[0] - 0.01, 0.0), (T_AIR2[0] + 0.4, 1.6), (T_AIR2[1] - 0.05, 1.6), (T_AIR2[1], 0.0), (DUR, 0.0)])
# demo span (tower 2 -> 3, front phase): red-hot overlay, current beads, 4 heat blocks -> 1
DEMO_A, DEMO_B = attach(2, 0), attach(3, 0)
DEMO_PTS = sag_pts(DEMO_A, DEMO_B, 3.6, n=24)
HOTW = poly_obj("HotWire", DEMO_PTS, 0.17, M_REDG)
glow(B_REDG, [(0, 0.0), (C["why"] - 0.01, 0.0), (C["why"] + 0.3, 2.2), (C["less"], 2.2), (C["less"] + 0.8, 0.0),
              (C["heat"] - 0.05, 0.0), (C["heat"] + 0.3, 2.2), (C["double"] + 0.6, 2.2), (C["quarter"], 0.5), (C["now"], 0.5), (C["now"] + 0.01, 0.0), (DUR, 0.0)])
windows(HOTW, [T_DEMO])
DEMO_PATH = Path(DEMO_PTS)
def demo_scale(t, i):
    big = 1.0 - ease((t - C["less"]) / 0.6)
    keep = (i % 3 == 0)
    return 1.0 * big + (0.45 if keep else 0.0) * (1 - big)
M_BEADR, B_BEADR = emit_mat("BeadRedCyan", (1.0, 0.15, 0.08), 4.0)
DEMO_BEADS = beads("DemoBead", DEMO_PATH, 30, 0.45, M_BEADR, [T_DEMO], speed=9.0, scale_fn=demo_scale)
glow(B_BEADR, [(0, 4.0), (DUR, 4.0)])
# bead colour red -> cyan on "less": mix in the emission colour via a keyed value
try:
    ntb = M_BEADR.node_tree; mixc = ntb.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"
    mixc.inputs[6].default_value = (1.0, 0.15, 0.08, 1); mixc.inputs[7].default_value = (0.30, 0.92, 1.0, 1)
    keyval(mixc.inputs[0], [(0, 0.0), (C["less"], 0.0), (C["less"] + 0.6, 1.0), (DUR, 1.0)])
    ntb.links.new(mixc.outputs[2], B_BEADR.inputs["Emission Color"])
except Exception as e: print("[build] bead colour mix skipped", e)
MID = DEMO_PATH.at(DEMO_PATH.L * 0.5)
M_HEATB, B_HEATB = mat("HeatBlock", (0.45, 0.03, 0.02), rough=0.4, emit_rgb=(1.0, 0.22, 0.12)); B_HEATB.inputs["Emission Strength"].default_value = 0.35
HEAT = []
for j in range(4):
    hb = box(f"HeatBlock{j}", -0.7, 0.7, -0.7, 0.7, -0.7, 0.7, M_HEATB); base = MID + Vector((-3.6 + 2.4 * j, -2.2, 3.4))
    t_in = C["square"] + 0.12 * j
    def hfn(t, j=j, base=base):
        if j > 0 and t > C["quarter"]: return tuple(base - Vector((0, 0, 6.0 * lin((t - C["quarter"] - 0.05 * j) / 0.5) ** 2)))
        return tuple(base)
    bake_loc(hb, hfn)
    bake_scale(hb, lambda t, j=j, t_in=t_in: (pop(t, t_in) * (1.0 if (j == 0 or t < C["quarter"]) else max(0.0, 1 - lin((t - C["quarter"]) / 0.55))),) * 3)
    windows(hb, [(C["square"], C["now"])]); HEAT.append(hb)

# ================= substation (x 940..1002) =================
SUB_PAD = box("SubPad", 938, 1003, -20, 20, -0.02, 0.12, M_GRAVEL)
bm = bmesh.new()
for x in range(938, 1004, 5):
    for y in (-20, 20): add_seg(bm, (x, y, 0), (x, y, 2.6), 0.05, 6)
for y in range(-20, 21, 5):
    for x in (938, 1003): add_seg(bm, (x, y, 0), (x, y, 2.6), 0.05, 6)
for zz in (0.3, 1.4, 2.5):
    add_poly(bm, [(938, -20, zz), (1003, -20, zz), (1003, 20, zz), (938, 20, zz), (938, -20, zz)], 0.025, 4)
FENCE = mesh_obj("SubFence", bm, M_GALV)
bm = bmesh.new()
for yy in (-12.0, 12.0): add_box(bm, GX - 0.5, GX + 0.5, yy - 0.5, yy + 0.5, 0, 15.5)
add_box(bm, GX - 0.4, GX + 0.4, -12.5, 12.5, 14.6, 15.4)
for yy in (-7.0, 7.0): add_box(bm, 997.5, 998.3, yy - 0.4, yy + 0.4, 0, 11.6)
add_box(bm, 997.4, 998.4, -7.5, 7.5, 11.0, 11.6)
for xx in (955, 975, 990):                               # bus support stands
    for yy in (-9.5, 0.0, 6.5): add_box(bm, xx - 0.15, xx + 0.15, yy - 0.15, yy + 0.15, 0, 7.0)
GANTRY = mesh_obj("SubGantry", bm, M_GALV)
SUBX1, SUBX2 = [], []
P1, T1, L1 = transformer("SubXfmrA", 966.0, -6.0, 0.6); P2, T2, L2 = transformer("SubXfmrB", 966.0, 8.0, 0.6)
bm = bmesh.new()
for k in range(3):
    add_poly(bm, [SUB_IN[k], Vector((955, PHASES[k][0], 7.0)), T1[k]], 0.07, 6)
    add_poly(bm, [L1[k], Vector((990, -1.0 + k, 7.0)), Vector((997.9, -1.0 + k * 1.0, 11.3))], 0.06, 6)
for k in range(3): add_seg(bm, (955, PHASES[k][0], 7.0), (955, PHASES[k][0], 7.3), 0.12, 8)
SUB_BUS = mesh_obj("SubBus", bm, M_WIRE)

# ================= street: wood poles, primary + neutral, pole can, houses =================
POLE_X = [1015.0 + 35.0 * k for k in range(9)]
POLE_Y = -6.0
bm = bmesh.new()
for x in POLE_X:
    add_cyl(bm, 0.16, 12.0, "Z", (x, POLE_Y, 6.0), seg=12)
    add_box(bm, x - 0.06, x + 0.06, POLE_Y - 1.0, POLE_Y + 1.0, 10.9, 11.05)
POLES_W = mesh_obj("WoodPoles", bm, M_WOOD)
PRI_Z, NEU_Z = 11.45, 9.5
bm = bmesh.new()
for x in POLE_X:
    add_cyl(bm, 0.07, 0.45, "Z", (x, POLE_Y - 0.8, 11.25), seg=10)
    add_cyl(bm, 0.07, 0.45, "Z", (x, POLE_Y + 0.8, 11.25), seg=10)
    add_cyl(bm, 0.07, 0.45, "Z", (x, POLE_Y, PRI_Z - 0.1 + 0.25), seg=10)
POLE_INS = mesh_obj("PinInsulators", bm, M_PORC)
bm = bmesh.new()
pri_pts = [Vector((997.9, 0.0, 11.3))] + [Vector((x, POLE_Y, PRI_Z + 0.2)) for x in POLE_X]
for a, b in zip(pri_pts, pri_pts[1:]): add_poly(bm, sag_pts(a, b, 0.5, n=8), 0.04, 6)
for a, b in zip(POLE_X, POLE_X[1:]): add_poly(bm, sag_pts((a, POLE_Y + 0.2, NEU_Z), (b, POLE_Y + 0.2, NEU_Z), 0.5, n=8), 0.035, 6)
for a, b in zip(POLE_X, POLE_X[1:]):
    for yy in (-0.8, 0.8): add_poly(bm, sag_pts((a, POLE_Y + yy, 11.5), (b, POLE_Y + yy, 11.5), 0.5, n=8), 0.04, 6)
DIST = mesh_obj("DistWires", bm, M_WIRE)
CAN_X = POLE_X[5]                                        # 1190
CANC = Vector((CAN_X - 0.62, POLE_Y, 8.2)); CAN_R, CAN_H = 0.38, 1.0
CAN_FULL = cyl("PoleCan", CAN_R, CAN_H, "Z", tuple(CANC), M_PAINT, seg=40)
bm = bmesh.new(); add_cyl(bm, CAN_R, CAN_H, "Z", (0, 0, 0), seg=40)
geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, 0), plane_no=(0, 1, 0), clear_inner=True)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
CAN_HALF = mesh_obj("PoleCanHalf", bm, M_PAINT); CAN_HALF.location = CANC
CAN_LID = cyl("PoleCanLid", CAN_R + 0.03, 0.06, "Z", tuple(CANC + Vector((0, 0, CAN_H / 2 + 0.03))), M_PAINT, seg=40)
CAN_BRK = box("PoleCanBracket", CAN_X - 0.25, CAN_X - 0.12, POLE_Y - 0.15, POLE_Y + 0.15, 7.8, 8.7, M_DARK)
CAN_BUSH = cyl("PoleCanBushing", 0.06, 0.35, "Z", tuple(CANC + Vector((0, 0, CAN_H / 2 + 0.22))), M_PORC, seg=12)
bm = bmesh.new(); add_poly(bm, [CANC + Vector((0, 0, CAN_H / 2 + 0.4)), CANC + Vector((0.1, 0, CAN_H / 2 + 1.6)), Vector((CAN_X, POLE_Y, PRI_Z + 0.2))], 0.025, 6)
CAN_TAP = mesh_obj("PrimaryTap", bm, M_WIRE)
# can inside: small iron core, primary (many thin turns, cyan) above, secondary halves (gold upper, cyan lower) with a white center tap
cz = CANC.z
CAN_CORE = box("CanCore", CANC.x - 0.2, CANC.x + 0.2, POLE_Y + 0.0, POLE_Y + 0.12, cz - 0.38, cz + 0.38, M_IRON)
def ring_stack(name, cx, cy, z0, z1, n, rmaj, rmin, m_):
    bm = bmesh.new()
    for k in range(n):
        z = z0 + (z1 - z0) * (k + 0.5) / n
        pts = [(cx + rmaj * math.cos(2 * math.pi * j / 24), cy + 0.06 + rmaj * 0.55 * math.sin(2 * math.pi * j / 24), z) for j in range(25)]
        add_poly(bm, pts, rmin, 6)
    return mesh_obj(name, bm, m_)
M_CANPRI, B_CANPRI = mat("CanPrimary", (0.85, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
M_SECA, B_SECA = mat("CanSecGold", (0.85, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_SECB, B_SECB = mat("CanSecCyan", (0.85, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.30, 0.92, 1.0))
CAN_PRI = ring_stack("CanPrimaryCoil", CANC.x, POLE_Y, cz + 0.08, cz + 0.36, 14, 0.24, 0.009, M_CANPRI)
CAN_SA = ring_stack("CanSecUpper", CANC.x, POLE_Y, cz - 0.10, cz + 0.05, 3, 0.25, 0.022, M_SECA)
CAN_SB = ring_stack("CanSecLower", CANC.x, POLE_Y, cz - 0.30, cz - 0.15, 3, 0.25, 0.022, M_SECB)
glow(B_CANPRI, [(0, 0.0), *pulse(C["pole"], 4.0, hold=1.4), (DUR, 0.0)])
glow(B_SECA, [(0, 0.0), (C["two"] - 0.01, 0.0), (C["two"] + 0.25, 5.0), (C["split"], 5.0), (C["halves"] - 0.2, 5.0), (C["halves"] + 0.2, 6.5),
              (C["your"], 6.5), (C["your"] + 0.01, 0.0), (DUR, 0.0)])
glow(B_SECB, [(0, 0.0), (C["two"] - 0.01, 0.0), (C["two"] + 0.25, 5.0), (C["split"], 5.0), (C["halves"] - 0.2, 5.0), (C["halves"] + 0.2, 6.5),
              (C["your"], 6.5), (C["your"] + 0.01, 0.0), (DUR, 0.0)])
CAN_IN = [CAN_CORE, CAN_PRI, CAN_SA, CAN_SB]
for o in CAN_IN: windows(o, [(C["gray"], C["your"])])
windows(CAN_FULL, [(0, C["gray"] + 0.6), (C["your"], DUR)]); windows(CAN_HALF, [(C["gray"] + 0.6, C["your"])])
# hero house (x 1194..1206, y 6..14), front wall faces the road (-y)
HX0, HX1, HY0, HY1, HZ = 1194.0, 1206.0, 6.0, 14.0, 3.0
bm = bmesh.new()
add_box(bm, HX0, HX0 + 0.2, HY0, HY1, 0, HZ); add_box(bm, HX1 - 0.2, HX1, HY0, HY1, 0, HZ)
add_box(bm, HX0, HX1, HY1 + 0.10, HY1 + 0.30, 0, HZ)                         # back wall exterior layer (sheathing + siding)
HOUSE_W = mesh_obj("HouseWalls", bm, M_SIDING)
HOUSE_FRONT = box("HouseFront", HX0, HX1, HY0, HY0 + 0.2, 0, HZ, M_SIDING)
HOUSE_FLOOR = box("HouseFloor", HX0, HX1, HY0, HY1, 0.0, 0.12, M_FLOOR)
HOUSE_CEIL = box("HouseCeiling", HX0, HX1, HY0, HY1, HZ - 0.02, HZ + 0.05, M_DRY)
bm = bmesh.new()
v = [bm.verts.new(p) for p in ((HX0 - 0.4, HY0 - 0.5, HZ), (HX1 + 0.4, HY0 - 0.5, HZ), (HX1 + 0.4, HY1 + 0.6, HZ), (HX0 - 0.4, HY1 + 0.6, HZ),
                               (HX0 - 0.4, (HY0 + HY1) / 2, HZ + 2.4), (HX1 + 0.4, (HY0 + HY1) / 2, HZ + 2.4))]
for f in ((v[0], v[1], v[5], v[4]), (v[2], v[3], v[4], v[5]), (v[0], v[4], v[3]), (v[1], v[2], v[5])): bm.faces.new(f)
bmesh.ops.solidify(bm, geom=list(bm.faces), thickness=0.12)
HOUSE_ROOF = mesh_obj("HouseRoof", bm, M_SHINGLE)
# back wall inside: drywall around a cut-open stud bay window (x 1197.0..1202.2, z 0.12..2.7)
WX0, WX1, WZ0, WZ1, WY = 1197.72, 1201.5, 0.12, 2.7, HY1 - 0.02
bm = bmesh.new()
add_box(bm, HX0 + 0.2, WX0, WY - 0.015, WY, 0.12, HZ); add_box(bm, WX1, HX1 - 0.2, WY - 0.015, WY, 0.12, HZ)
add_box(bm, WX0, WX1, WY - 0.015, WY, WZ1, HZ)
DRY = mesh_obj("Drywall", bm, M_DRY)
DRY_EDGE = []
bm = bmesh.new()
for x in (1197.78, 1198.6, 1199.4, 1200.2, 1201.0, 1201.44):
    add_box(bm, x - 0.02, x + 0.02, WY, WY + 0.09, 0.12, WZ1)
add_box(bm, WX0, WX1, WY, WY + 0.09, WZ1 - 0.04, WZ1)
add_box(bm, WX0, WX1, WY, WY + 0.09, 0.12, 0.16)
STUDS = mesh_obj("Studs", bm, M_STUD)
M_OSB, _ = mat("OSB", (0.30, 0.20, 0.10), rough=0.85, noise=18.0)
BACK_SHEATH = box("Sheathing", WX0, WX1, WY + 0.09, WY + 0.105, 0.12, WZ1, M_OSB)
OX, OZ = 1198.1, 0.42                                       # the 120 V outlet
DX, DZ = 1200.6, 0.55                                       # the 240 V dryer outlet
def outlet(name, x, z, big=False):
    s = 1.35 if big else 1.0; parts = []
    parts.append(box(name + "Box", x - 0.035 * s, x + 0.035 * s, WY - 0.0, WY + 0.06, z - 0.055 * s, z + 0.055 * s, M_BOX))
    parts.append(box(name + "Plate", x - 0.04 * s, x + 0.04 * s, WY - 0.012, WY - 0.002, z - 0.065 * s, z + 0.065 * s, M_WHITE))
    bm = bmesh.new()
    if big:
        add_box(bm, x - 0.018, x - 0.012, WY - 0.0135, WY - 0.011, z - 0.005, z + 0.025)
        add_box(bm, x + 0.012, x + 0.018, WY - 0.0135, WY - 0.011, z - 0.005, z + 0.025)
        add_box(bm, x - 0.004, x + 0.004, WY - 0.0135, WY - 0.011, z - 0.03, z - 0.015)
    else:
        for zz in (z + 0.028, z - 0.028):
            add_box(bm, x - 0.012, x - 0.009, WY - 0.0135, WY - 0.011, zz - 0.007, zz + 0.007)
            add_box(bm, x + 0.009, x + 0.012, WY - 0.0135, WY - 0.011, zz - 0.008, zz + 0.008)
            add_box(bm, x - 0.003, x + 0.003, WY - 0.0135, WY - 0.011, zz - 0.016, zz - 0.012)
    parts.append(mesh_obj(name + "Slots", bm, M_SLOT))
    return parts
OUT1 = outlet("Outlet", OX, OZ); OUT2 = outlet("DryerOutlet", DX, DZ, big=True)
PLATE = OUT1[1]
# cables in the stud bay: outlet cable (gold hot + white neutral), dryer cable (gold + cyan hots)
CAB1 = [(OX, WY + 0.045, WZ1), (OX, WY + 0.045, OZ + 0.06)]
CAB2 = [(DX, WY + 0.045, WZ1), (DX, WY + 0.045, DZ + 0.08)]
CABLE1 = poly_obj("Cable1", CAB1, 0.009, M_CABLE); CABLE2 = poly_obj("Cable2", CAB2, 0.011, M_CABLE)
CORE1 = poly_obj("Cable1Hot", [(OX - 0.004, WY + 0.035, WZ1), (OX - 0.004, WY + 0.035, OZ + 0.06)], 0.004, M_HOT)
CORE2 = poly_obj("Cable2HotA", [(DX - 0.005, WY + 0.033, WZ1), (DX - 0.005, WY + 0.033, DZ + 0.08)], 0.005, M_HOT)
CORE3 = poly_obj("Cable2HotB", [(DX + 0.005, WY + 0.033, WZ1), (DX + 0.005, WY + 0.033, DZ + 0.08)], 0.005, M_HOT2)
glow(B_HOT, [(0, 0.0), (C["your"] - 0.01, 0.0), (C["outlet2"] + 0.1, 6.0), (C["only"], 6.0), (C["only"] + 0.01, 0.0), (DUR, 0.0)])
glow(B_HOT2, [(0, 0.0), (C["dryer"] - 0.01, 0.0), (C["dryer"] + 0.25, 6.0), (C["only"], 6.0), (C["only"] + 0.01, 0.0), (DUR, 0.0)])
glow(B_CABLE, [(0, 0.0), (C["let"] + 0.1, 0.0), (C["let"] + 0.6, 4.0), (C["so"] - 0.1, 4.0), (C["so"], 0.0), (DUR, 0.0)])
DRYER = box("Dryer", 1201.0, 1201.85, HY1 - 0.85, HY1 - 0.08, 0.12, 1.08, M_DRYER)
DRYER_DOOR = cyl("DryerDoor", 0.25, 0.03, "Y", (1201.42, HY1 - 0.86, 0.6), M_DOOR, seg=32)
DRYER_CORD = poly_obj("DryerCord", [(DX, WY - 0.02, DZ - 0.02), (DX + 0.2, WY - 0.2, 0.2), (1201.05, HY1 - 0.4, 0.4)], 0.012, M_TRIP)
CEIL_LIGHT_D = bpy.data.lights.new("RoomLight", "AREA"); CEIL_LIGHT_D.size = 3.0; CEIL_LIGHT_D.energy = 120; CEIL_LIGHT_D.color = (1.0, 0.92, 0.82)
CEIL_LIGHT = bpy.data.objects.new("RoomLight", CEIL_LIGHT_D); scene.collection.objects.link(CEIL_LIGHT); CEIL_LIGHT.location = (1199.8, 11.2, HZ - 0.1)
# service drop: can -> house (gold hot, white neutral, cyan hot)
DROP_A = CANC + Vector((0.0, 0.25, 0.0)); DROP_B = Vector((1196.0, HY0 - 0.05, 2.75))
DROP = []
for k, (m_, dz) in enumerate(((M_HOT, 0.05), (M_NEU, 0.0), (M_HOT2, -0.05))):
    DROP.append(poly_obj(f"Drop{k}", sag_pts(DROP_A + Vector((0, 0, dz - 0.2 + 0.1 * k)), DROP_B + Vector((0, 0, dz)), 0.5, n=12), 0.02, m_))
glow(B_NEU, [(0, 0.0), *pulse(C["split"], 2.0, hold=1.4), (DUR, 0.0)])
# fail what-if: plate pops, drywall chips fall (rigid body), sparks
CHIPS = []
for j in range(9):
    side = j % 3
    if side == 0: cx_, cz_ = WX0 - 0.08, 0.5 + 0.25 * j
    elif side == 1: cx_, cz_ = WX0 + 0.3 + 0.55 * j, WZ1 + 0.06
    else: cx_, cz_ = WX1 + 0.08, 0.4 + 0.22 * j
    ch = box(f"Chip{j}", -0.07, 0.07, -0.008, 0.008, -0.05, 0.05, M_DRY); ch.location = (cx_, WY - 0.03, min(cz_, WZ1 + 0.1))
    ch.rotation_euler = (random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)); CHIPS.append(ch)
PLATE2 = box("PlateFly", -0.04, 0.04, -0.005, 0.005, -0.065, 0.065, M_WHITE); PLATE2.location = (OX, WY - 0.03, OZ)
fx.rigid(CHIPS + [PLATE2], passive=[HOUSE_FLOOR], mass=0.3, friction=0.5, bounce=0.2)
try:
    PLATE2.rigid_body.kinematic = False
    for ch in CHIPS + [PLATE2]: ch.rigid_body.collision_margin = 0.004
except Exception: pass
windows(PLATE, [(0, C["let"] + 0.3), (C["so"], DUR)])
for o in CHIPS + [PLATE2]: windows(o, [(C["let"] + 0.3, C["so"])])
SPARK_E = sphere_mesh("SparkEmitter", 0.03, 1); SPARK = obj_from("SparkEmitter", SPARK_E, M_GOLDG, loc=(OX, WY - 0.03, OZ))
fx.particles(SPARK, "sparks", F(C["let"] + 0.3), F(C["so"] - 0.3), count=260)
windows(SPARK, [(C["let"] + 0.3, C["so"])])
SPARK2 = obj_from("SparkEmitter2", SPARK_E, M_GOLDG, loc=(DX, WY - 0.03, DZ))
fx.particles(SPARK2, "sparks", F(C["wire"]), F(C["so"] - 0.3), count=160)
windows(SPARK2, [(C["wire"], C["so"])])
RED_ROOM = bpy.data.lights.new("RedFlash", "POINT"); RED_ROOM.color = (1.0, 0.35, 0.2); RED_ROOM.shadow_soft_size = 0.2
RR_O = bpy.data.objects.new("RedFlash", RED_ROOM); scene.collection.objects.link(RR_O); RR_O.location = (OX + 0.3, WY - 0.4, OZ + 0.2)
keyval_l = [(0, 0.0), (C["let"] + 0.25, 0.0), (C["let"] + 0.35, 10.0), (C["let"] + 0.9, 3.0), (C["wire"], 8.0), (C["fail"], 4.0), (C["so"] - 0.05, 4.0), (C["so"], 0.0), (DUR, 0.0)]
for t_, v_ in keyval_l: RED_ROOM.energy = v_; RED_ROOM.keyframe_insert("energy", frame=F(t_))
# hook beads: cyan pulse running down the outlet cable into the outlet (period chosen so frame 1 == last frame)
PER = DUR / max(1, round(DUR / 1.1))
HOOK_PATH = Path([(OX + 0.012, WY + 0.03, WZ1), (OX + 0.012, WY + 0.03, OZ + 0.05)])
HOOK_BEADS = beads("HookBead", HOOK_PATH, 5, 0.011, M_CYANG, [(0, C["let"] + 0.2), (C["and"], DUR)], speed=0, loop_period=PER)
for o in (HOUSE_FRONT,): windows(o, [(C["so"], C["your"]), (C["only"], C["and"] + 0.5)])
# 3 route markers (aerial 1): step-up, substation, pole can
MARK = []
for j, p in enumerate((Vector((30, 0, 0)), Vector((968, 0, 0)), Vector((CAN_X, POLE_Y, 0)))):
    bm = bmesh.new(); add_cyl(bm, 4.0, 60.0, "Z", (0, 0, 30.0 + 14.0), seg=16); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=24.0)
    for vv in bm.verts:
        if vv.co.length < 24.1: vv.co.z += 96.0
    mk = mesh_obj(f"Marker{j}", bm, M_GOLDG); mk.location = p
    bake_scale(mk, lambda t, j=j: (pop(t, C["three"] + 0.3 * j, 0.3),) * 3)
    windows(mk, [(C["three"], C["starts"])]); MARK.append(mk)
# route beads (aerials + flyover): plant -> line -> substation -> street -> can -> house
route = [XF_TOPS[0]] + sag_pts(XF_TOPS[0], attach(0, 0), 2.0, 6)[1:]
for i in range(len(TOWER_X) - 1): route += sag_pts(attach(i, 0), attach(i + 1, 0), 3.6, 6)[1:]
route += sag_pts(attach(11, 0), SUB_IN[0], 2.4, 6)[1:] + [Vector((955, PHASES[0][0], 7.3)), T1[0], L1[0], Vector((997.9, -1.0, 11.3))]
route += [Vector((x, POLE_Y, PRI_Z + 0.2)) for x in POLE_X[:6]] + [CANC + Vector((0, 0, CAN_H / 2 + 0.4)), CANC, DROP_A, DROP_B]
ROUTE = Path(route)
ROUTE_BEADS = beads("RouteBead", ROUTE, 70, 1.5, M_CYANG, [T_AIR1, T_FLY, T_AIR2], speed=60.0)

# ================= fx: scatter (trees, houses), engine =================
def tree_inst():
    bm = bmesh.new(); add_cyl(bm, 0.25, 3.0, "Z", (0, 0, 1.5), seg=8, mi=1)
    r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=2.4, radius2=0.0, depth=7.0)
    bmesh.ops.translate(bm, verts=r_["verts"], vec=(0, 0, 5.5))
    o = mesh_obj("TreeInst", bm, [M_LEAVES, M_TRUNK]); return o
def house_inst():
    bm = bmesh.new(); add_box(bm, -4, 4, -4.5, 4.5, 0, 3.2)
    v = [bm.verts.new(p) for p in ((-4.4, -5.0, 3.2), (4.4, -5.0, 3.2), (4.4, 5.0, 3.2), (-4.4, 5.0, 3.2), (0, -5.0, 5.4), (0, 5.0, 5.4))]
    for f in ((v[0], v[4], v[5], v[3]), (v[1], v[2], v[5], v[4]), (v[0], v[1], v[4]), (v[3], v[5], v[2])):
        bm.faces.new(f).material_index = 1
    return mesh_obj("HouseInst", bm, [M_SIDING, M_SHINGLE])
TREE = tree_inst(); HOUSEI = house_inst()
for k, (x0, x1, y0, y1, d) in enumerate(((-120, 935, 30, 420, 0.0009), (-120, 935, -420, -30, 0.0007), (-600, 3200, 420, 1400, 0.0004),
                                          (1320, 2600, -900, 420, 0.0004), (-600, 935, -1400, -420, 0.0003))):
    s_ = plane(f"TreeScatter{k}", x0, x1, y0, y1, -0.05, M_GRASS)
    fx.scatter(s_, TREE, density=d, scale_min=0.6, scale_max=1.5, seed=5 + k)
for k, (x0, x1, y0, y1, d) in enumerate(((1015, 1188, 18, 70, 0.0016), (1212, 1320, 18, 70, 0.0016), (1010, 1320, -80, -22, 0.0012))):
    s_ = plane(f"HouseScatter{k}", x0, x1, y0, y1, -0.05, M_GRASS)
    fx.scatter(s_, HOUSEI, density=d, scale_min=0.85, scale_max=1.15, seed=21 + k)
TREE.location = (0, 0, -500); HOUSEI.location = (0, 0, -500)

# ================= studio: conductor cutaway (x 3000) =================
STUDIO = Vector((3000.0, 0.0, 0.0))
bm = bmesh.new()
add_box(bm, -30, 30, -30, 30, -0.1, 0.0)
add_box(bm, -30, 30, 18, 18.5, 0, 40)
CYC = mesh_obj("StudioCyc", bm, M_CYC); CYC.location = STUDIO
SC = STUDIO + Vector((0, 0, 3.0))
def strand(bm, r_lay, a0, r_s, x0, x1, pitch, mi):
    pts = []
    n = 40
    for j in range(n + 1):
        x = x0 + (x1 - x0) * j / n; a = a0 + 2 * math.pi * (x - x0) / pitch if r_lay > 0 else 0
        pts.append((x, r_lay * math.cos(a), r_lay * math.sin(a)))
    add_poly(bm, pts, r_s, 10, mi)
bm = bmesh.new(); strand(bm, 0, 0, 0.12, -3.0, 3.6, 1, 0)
for k in range(6): strand(bm, 0.245, k * math.pi / 3, 0.12, -3.0, 3.6, 5.0, 0)
STEELCORE = mesh_obj("SteelCoreStrands", bm, M_STEELC); STEELCORE.location = SC
bm = bmesh.new()
for k in range(12): strand(bm, 0.50, k * math.pi / 6, 0.13, -3.0, 2.4, -6.0, 0)
for k in range(18): strand(bm, 0.76, k * math.pi / 9, 0.13, -3.0, 1.2, 7.0, 0)
ALUM = mesh_obj("AluminumStrands", bm, M_AL); ALUM.location = SC
for o in (STEELCORE, ALUM):
    try: o.data.shade_smooth()
    except Exception: pass
bake_fn(STEELCORE, "rotation_euler", 0, lambda t: 0.25 * (t - C["the2"])); bake_fn(ALUM, "rotation_euler", 0, lambda t: 0.25 * (t - C["the2"]))
glow(B_AL, [(0, 0.0), *pulse(C["aluminum"], 0.8, hold=0.4), (DUR, 0.0)])
glow(B_STEELC, [(0, 0.0), *pulse(C["steel"], 2.5, hold=0.5), (DUR, 0.0)])
for nm, lc, en, sz in (("KeyL", (-6, -8, 9), 2500, 6), ("RimL", (4, 10, 6), 1800, 5), ("FillL", (8, -6, 2), 700, 6)):
    ld = bpy.data.lights.new("Studio" + nm, "AREA"); ld.energy = en; ld.size = sz
    lo = bpy.data.objects.new("Studio" + nm, ld); scene.collection.objects.link(lo); lo.location = STUDIO + Vector(lc)
    tcs = lo.constraints.new("TRACK_TO"); tcs.target = STEELCORE; tcs.track_axis = "TRACK_NEGATIVE_Z"; tcs.up_axis = "UP_Y"

# ================= world: HDRI light + own sky gradient =================
fx.hdri("courtyard", strength=0.7, rotation_deg=60.0, show_background=False)
try:
    wn, wl = scene.world.node_tree.nodes, scene.world.node_tree.links
    plain = next(n for n in wn if n.type == "BACKGROUND" and abs(n.inputs["Color"].default_value[0] - 0.02) < 1e-3)
    grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "LINEAR"
    tcw = wn.new("ShaderNodeTexCoord"); mp = wn.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, math.radians(90), 0)
    wl.new(tcw.outputs["Generated"], mp.inputs["Vector"]); wl.new(mp.outputs["Vector"], grad.inputs["Vector"])
    cr = wn.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.98, 0.78, 0.55, 1); e[1].position = 0.40; e[1].color = (0.22, 0.45, 0.80, 1)
    wl.new(grad.outputs["Fac"], cr.inputs[0]); wl.new(cr.outputs[0], plain.inputs["Color"]); plain.inputs["Strength"].default_value = 1.0
    print("[build] sky gradient on")
except Exception as e: print("[build] sky gradient skipped", e)
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 2.8; sun_d.color = (1.0, 0.88, 0.72); sun_d.angle = math.radians(1.5)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(52), 0, math.radians(-40))
fx.glare(threshold=1.0, strength=0.55, size=7)
windows(HALL_FRONT, [(0, C["generator"]), (C["next"], DUR)])
hl_d = bpy.data.lights.new("HallLight", "AREA"); hl_d.size = 18; hl_d.energy = 3000; hl_d.color = (0.9, 0.95, 1.0)
HL = bpy.data.objects.new("HallLight", hl_d); scene.collection.objects.link(HL); HL.location = (-16, -3, 16.5)
xl_d = bpy.data.lights.new("TankLight", "AREA"); xl_d.size = 3; xl_d.energy = 0; xl_d.color = (1.0, 0.95, 0.88)
XL = bpy.data.objects.new("TankLight", xl_d); scene.collection.objects.link(XL); XL.location = (30, -4.5, 6.2)
XL.rotation_euler = (math.radians(55), 0, 0)
for t_, v_ in [(0, 0.0), (C["inside"] - 0.01, 0.0), (C["inside"], 250.0), (C["why"] - 0.01, 250.0), (C["why"], 0.0), (DUR, 0.0)]:
    xl_d.energy = v_; xl_d.keyframe_insert("energy", frame=F(t_))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.02; cam_d.clip_end = 9000
HOOK_SHOT = ((OX + 0.45, WY - 1.15, OZ + 0.3), (OX + 0.05, WY + 0.03, OZ + 0.3), 30)
V = lambda a, b=(0, 0, 0): tuple(Vector(a) + Vector(b))
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, *HOOK_SHOT),
    (C["let"] - 0.05, (OX + 0.7, WY - 1.8, OZ + 0.6), (OX + 0.1, WY + 0.03, OZ + 0.55), 30),
    (C["let"], (OX + 1.3, WY - 2.2, 0.95), (OX + 0.3, WY, 0.5), 26, "cut"),
    (C["so"] - 0.05, (OX + 1.1, WY - 1.9, 0.9), (OX + 0.3, WY, 0.5), 26),
    (C["so"], (560.0, -1000.0, 900.0), (600.0, 0.0, 10.0), 17, "cut"),
    (C["starts"] - 0.05, (590.0, -930.0, 830.0), (605.0, 0.0, 10.0), 17),
    (C["starts"], (-78.0, -98.0, 40.0), (-15.0, 0.0, 9.0), 24, "cut"),
    (C["generator"] - 0.05, (-66.0, -84.0, 34.0), (-15.0, 0.0, 8.0), 24),
    (C["generator"], (-5.0, -12.0, 7.0), (-14.0, 0.0, 4.2), 22, "cut"),
    (C["next"] - 0.05, (-7.0, -10.5, 6.2), (-14.0, 0.0, 4.2), 22),
    (C["next"], (13.0, -25.0, 7.5), (30.0, 0.0, 4.8), 24, "cut"),
    (C["inside"] - 0.05, (17.0, -21.0, 6.8), (30.0, 0.0, 4.6), 24),
    (C["inside"], (30.0, -11.0, 4.0), (30.0, 0.0, 3.5), 24, "cut"),
    (C["output"] - 0.05, (30.0, -9.4, 3.8), (30.0, 0.0, 3.5), 24),
    (C["output"], (34.0, -5.4, 3.6), (32.4, 0.0, 3.5), 26, "cut"),
    (C["why"] - 0.05, (33.4, -4.6, 4.0), (32.4, 0.0, 3.6), 26),
    (C["why"], V(MID, (-7.0, -15.0, 1.2)), V(MID, (0.0, -1.0, 1.4)), 26, "cut"),
    (C["now"] - 0.05, V(MID, (-3.0, -13.5, 1.2)), V(MID, (1.0, -1.0, 1.4)), 26),
    (C["now"], (150.0, -36.0, 48.0), (420.0, -5.0, 22.0), 26, "cut"),
    (C["the2"] - 0.05, (470.0, -36.0, 46.0), (760.0, -5.0, 22.0), 26),
    (C["the2"], V(SC, (5.6, -6.8, 1.8)), V(SC, (1.5, 0.0, 0.0)), 30, "cut"),
    (C["air"] - 0.05, V(SC, (4.6, -6.0, 1.4)), V(SC, (1.5, 0.0, 0.0)), 30),
    (C["air"], (xI - 1.6, yI - 3.4, zI - 1.0), (xI, yI, zI - 1.6), 30, "cut"),
    (C["near"] - 0.05, (xI - 1.2, yI - 2.9, zI - 1.2), (xI, yI, zI - 1.6), 30),
    (C["near"], (928.0, -58.0, 30.0), (970.0, 0.0, 5.0), 24, "cut"),
    (C["sends"] - 0.05, (936.0, -52.0, 26.0), (970.0, 0.0, 5.0), 24),
    (C["sends"], (1003.0, -21.0, 7.5), (1120.0, -6.0, 7.0), 28, "cut"),
    (C["then"] - 0.05, (1045.0, -20.0, 7.8), (1165.0, -6.0, 7.6), 28),
    (C["then"], (1186.2, -11.8, 7.4), (CANC.x, POLE_Y, 8.4), 30, "cut"),
    (C["two"] - 0.05, (1187.8, -10.0, 7.9), (CANC.x, POLE_Y, 8.3), 30),
    (C["two"], (CANC.x + 0.15, POLE_Y - 2.3, cz + 0.15), (CANC.x, POLE_Y, cz - 0.02), 30, "cut"),
    (C["your"] - 0.05, (CANC.x + 0.1, POLE_Y - 1.95, cz + 0.1), (CANC.x, POLE_Y, cz - 0.02), 30),
    (C["your"], (1199.7, WY - 3.9, 1.35), (1199.6, WY, 0.7), 20, "cut"),
    (C["only"] - 0.05, (1199.6, WY - 3.5, 1.25), (1199.6, WY, 0.7), 20),
    (C["only"], (1480.0, -440.0, 270.0), (600.0, 0.0, 0.0), 24, "cut"),
    (C["and"] - 0.05, (1420.0, -400.0, 240.0), (620.0, 0.0, 0.0), 24),
    (C["and"], (1199.0, -75.0, 28.0), (1199.0, 10.0, 2.0), 26, "cut"),
    (C["even"], (1198.6, -8.0, 5.0), (1198.8, WY, 1.2), 26),
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
scene.view_settings.exposure = float(arg("--exposure", "-0.6"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["let"] + 0.3), F(C["so"]))
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "outlet": (OX - 0.05, WY - 0.02, OZ), "cable": (OX, WY + 0.04, 1.7), "dryer_outlet": (DX + 0.05, WY - 0.02, DZ + 0.02),
    "dryer": (1201.42, HY1 - 0.9, 1.1), "plant": (-30.0, -15.0, 20.0), "generator": (-13.0, 0.5, GZ + 3.4),
    "stepup": (30.0, -2.6, 7.2), "core": (30.0, -0.6, 5.7), "primary": (LEG1 - 1.15, -0.4, 3.4), "secondary": (LEG2 + 1.0, -0.6, 4.6),
    "wire": tuple(MID + Vector((2.0, 0, 0))), "steel": tuple(SC + Vector((3.3, 0, 0.25))), "aluminum": tuple(SC + Vector((0.3, -0.8, 0.6))),
    "insulator": (xI + 0.25, yI, zI - 1.3), "tower": (TOWER_X[INS_TOWER], 0, 30.0), "substation": (968.0, -6.0, 7.0),
    "polecan": (CANC.x - CAN_R, POLE_Y, cz + 0.3), "sec_upper": (CANC.x - 0.27, POLE_Y + 0.1, cz - 0.02), "sec_lower": (CANC.x - 0.27, POLE_Y + 0.1, cz - 0.22),
    "neutral": (CANC.x + 0.2, POLE_Y + 0.25, cz - 0.1), "m_stepup": (30.0, 0.0, 104.0), "m_sub": (968.0, 0.0, 104.0), "m_can": (CAN_X, POLE_Y, 104.0),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "fail": RR(*T_FAIL), "plate_pop": round(C["let"] + 0.3, 3), "aerial1": RR(*T_AIR1), "plant": RR(*T_PLANT),
          "gen_spin": RR(C["generator"], C["next"]), "stepup": RR(*T_XF), "tank_open": round(C["inside"], 3), "oil_fill": RR(C["inside"], C["inside"] + 3.4),
          "turns_light": RR(C["turns"], C["seven"] + 0.6), "demo": RR(*T_DEMO), "less_current": round(C["less"], 3),
          "heat_blocks": [round(C["square"] + 0.12 * j, 3) for j in range(4)], "heat_drop": round(C["quarter"], 3), "flyover": RR(*T_FLY),
          "conductor": RR(*T_COND), "insulator": RR(*T_INS), "disc_ripple": [round(C["insulator"] + 0.07 * j, 3) for j in range(NDISC)],
          "substation": RR(*T_SUB), "street": RR(C["sends"], C["then"]), "can": RR(*T_CAN), "can_open": round(C["gray"] + 0.6, 3),
          "halves": round(C["halves"], 3), "room": RR(*T_ROOM), "outlet_on": round(C["outlet2"], 3), "dryer_on": round(C["dryer"], 3),
          "aerial2": RR(*T_AIR2), "back": RR(*T_BACK), "markers": [round(C["three"] + 0.3 * j, 3) for j in range(3)]}
if "--debug" in ARGS:
    scene.frame_set(350)
    for mk in MARK: print("MARK", mk.name, tuple(mk.scale), mk.hide_render, tuple(mk.matrix_world.translation), len(mk.data.vertices))
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
