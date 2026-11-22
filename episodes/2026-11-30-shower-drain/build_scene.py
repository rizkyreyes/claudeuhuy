# Shower drain (3d-xx): where shower water goes. Claim hook "Your shower drain is full of water, all the time." on a close cross-section
# of the drain -> P-trap U revealed -> stake what-if: no water seal, sewer gas rises into the bathroom -> shower on (rain particles + spray
# beads) -> old water pushed out, seal stays -> trap arm slope (1/4 inch per foot) -> slope demo studio: too flat (rigid gunk settles),
# too steep (water races ahead of solids) -> siphon: rushing slug pulls air, trap level drops -> vent stack up through the roof, air in
# -> exterior roof with the vent pipe -> whole house: shower + toilet + sink -> building drain -> city sewer / septic tank -> unused
# shower: seal evaporates (vapour particles), sewer gas into the guest bath -> CTA push-in.
# Illustrative, 1 unit = 10 cm: generic two-storey house, 2-inch trap and 3-inch stack (exaggerated ~3x). No logos, no people.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view


ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 1.0, 2)   # CTA ending (19-20 Nov): complete question + "Tell me in the comments.", then ~1 s fade
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(36)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("your", "Your"), ("shower", "shower"), ("drain", "drain"), ("full", "full"), ("water", "water,"), ("right", "Right"),
        ("under", "under"), ("floor", "floor,"), ("pipe", "pipe"), ("bends", "bends"), ("u", "U,"), ("u2", "U"), ("never", "never"),
        ("without", "Without"), ("sewer", "sewer"), ("gas", "gas"), ("street", "street"), ("rise", "rise"), ("bathroom", "bathroom."),
        ("heres", "Here's"), ("happens", "happens"), ("shower2", "shower."), ("water2", "Water"), ("drops", "drops"), ("grate", "grate,"),
        ("short", "short"), ("ubend", "U-bend,"), ("ptrap", "P-trap."), ("new", "New"), ("pushes", "pushes"), ("old", "old"),
        ("far", "far"), ("few", "few"), ("inches", "inches"), ("behind", "behind."), ("little", "little"), ("puddle", "puddle"),
        ("seal", "seal."), ("then", "Then"), ("runs", "runs"), ("slopes", "slopes"), ("quarter", "quarter"), ("foot", "foot."),
        ("too", "Too"), ("flat", "flat,"), ("gunk", "gunk"), ("settles", "settles."), ("too2", "Too"), ("steep", "steep,"),
        ("races", "races"), ("solids", "solids."), ("but", "But"), ("catch", "catch."), ("water3", "Water"), ("rushing", "rushing"),
        ("pulls", "pulls"), ("air", "air"), ("suction", "suction"), ("drain2", "drain"), ("trap", "trap"), ("dry", "dry."),
        ("so", "So"), ("every", "every"), ("trap2", "trap"), ("vent", "vent"), ("climbs", "climbs"), ("walls", "walls"),
        ("roof", "roof,"), ("letting", "letting"), ("air2", "air"), ("thats", "That's"), ("see", "see"), ("sticking", "sticking"),
        ("there", "there."), ("from", "From"), ("shower3", "shower"), ("joins", "joins"), ("toilet", "toilet"), ("sinks", "sinks"),
        ("one", "one"), ("big", "big"), ("drain3", "drain"), ("house", "house,"), ("city", "city"), ("sewer2", "sewer"),
        ("septic", "septic"), ("tank", "tank."), ("and_", "And"), ("shower4", "shower"), ("unused", "unused"), ("weeks", "weeks,"),
        ("seal2", "seal"), ("evaporates", "evaporates."), ("thats2", "That's"), ("guest", "guest"), ("bathroom2", "bathroom"),
        ("smell", "smell."), ("do", "Do"), ("nobody", "nobody"), ("uses", "uses?"), ("tell", "Tell"), ("comments", "comments.")]
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
CL = coll("ShowerDrain")
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


# ================= sweep tubes (one watertight mesh per pipe, for booleans) =================
def chaikin(pts, it=3):
    p = [Vector(x) for x in pts]
    for _ in range(it):
        q = [p[0]]
        for a, b in zip(p, p[1:]): q += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
        q.append(p[-1]); p = q
    return p
def sweep_bm(pts, radii, seg=28, cap=True):
    bm = bmesh.new(); rings = []
    n = len(pts); t_prev = None; nrm = None
    for i, p in enumerate(pts):
        t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
        if nrm is None:
            a = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0)); nrm = (a - t * a.dot(t)).normalized()
        else:
            nrm = (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm); r = radii[i]
        rings.append([bm.verts.new(p + r * (math.cos(2 * math.pi * k / seg) * nrm + math.sin(2 * math.pi * k / seg) * b)) for k in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new([r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]])
    if cap:
        bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm
def interp_r(pts, keys):
    """radius per point from (fraction of length, r) keys."""
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + (b - a).length)
    out = []
    for si in s:
        u = si / s[-1]
        for (u0, r0), (u1, r1) in zip(keys, keys[1:]):
            if u <= u1: out.append(r0 + (r1 - r0) * ((u - u0) / (u1 - u0) if u1 > u0 else 1)); break
        else: out.append(keys[-1][1])
    return out
def half_pipe(name, pts, radii, m_, seg=32):
    bm = sweep_bm(pts, radii, seg, cap=False); cut_front(bm, 0.0, fill=False)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def cutter(name, pts, radii, seg=28):
    o = mesh_obj(name, sweep_bm(pts, radii, seg, cap=True), None); o.hide_render = True; o.display_type = "WIRE"; return o
def boolean(target, cut, name="Cut"):
    md = target.modifiers.new(name, "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = cut
    try: md.solver = "EXACT"
    except Exception: pass
    return md



def windows_r(obj, wins):
    """render-only visibility (rigid bodies must stay in the sim)"""
    def kr(o, fr, h): key(o, "hide_render", fr, h, "CONSTANT")
    kr(obj, 1, True)
    for t0, t1 in wins:
        kr(obj, 1 if t0 <= 0 else F(t0), False)
        if t1 < DUR: kr(obj, F(t1), True)
# ================= materials =================
def strata(name, cols, scale=0.045, bump=0.35):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 4.0
    L.new(tc.outputs["Object"], wv.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.35; nz.inputs["Detail"].default_value = 8.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = N.new("ShaderNodeValToRGB"); e = cr.color_ramp.elements
    e[0].color = (*cols[0], 1); e[1].color = (*cols[-1], 1)
    for i, c_ in enumerate(cols[1:-1]):
        el = e.new((i + 1) / (len(cols) - 1)); el.color = (*c_, 1)
    L.new(wv.outputs["Fac"], cr.inputs[0])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[0].default_value = 0.25
    L.new(cr.outputs[0], mx.inputs[6]); L.new(nz.outputs["Fac"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.92
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m
def stone(name, rgb1, rgb2, scale, row=0.55, plane="XZ"):
    """dry-laid ashlar: brick texture (object coords) + noise + bump on the joints."""
    m = tiles(name, rgb1, rgb2, scale, plane); nt = m.node_tree; N, L = nt.nodes, nt.links
    br = next(n for n in N if n.type == "TEX_BRICK"); br.inputs["Row Height"].default_value = row; br.inputs["Mortar Size"].default_value = 0.012
    br.offset = 0.5; br.inputs["Mortar"].default_value = (0.20, 0.17, 0.13, 1)
    b = next(n for n in N if n.type == "BSDF_PRINCIPLED"); b.inputs["Roughness"].default_value = 0.85
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.5; L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; tc = N.new("ShaderNodeTexCoord"); L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mx = N.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[0].default_value = 0.18
    L.new(br.outputs["Color"], mx.inputs[6]); L.new(nz.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (0.98, 0.74, 0.27, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b


Y = Vector((0, 1, 0))
# ================= path + tube builders (path in the XZ plane, cut at y = 0, keep y >= 0) =================
def fillet_path(corners, R, n=12, step=1.5):
    c = [Vector(p) for p in corners]; pts = [c[0]]
    for i in range(1, len(c) - 1):
        a, b, d = c[i - 1], c[i], c[i + 1]
        d1, d2 = (b - a).normalized(), (d - b).normalized()
        p0, p1 = b - d1 * R, b + d2 * R
        last = pts[-1]; L_ = (p0 - last).length; k = max(1, int(L_ / step))
        pts += [last.lerp(p0, j / k) for j in range(1, k + 1)]
        for j in range(1, n + 1):
            u = j / n; pts.append((1 - u) ** 2 * p0 + 2 * (1 - u) * u * b + u * u * p1)
    last = pts[-1]; L_ = (c[-1] - last).length; k = max(1, int(L_ / step))
    pts += [last.lerp(c[-1], j / k) for j in range(1, k + 1)]
    return pts
def arclen(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]): s.append(s[-1] + (b - a).length)
    return s
def subpath(pts, s0, s1):
    P = Path(pts); s = arclen(pts)
    return [P.at(s0)] + [p for p, si in zip(pts, s) if s0 < si < s1] + [P.at(s1)]
def frame_at(pts, i):
    n = len(pts); t = (pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized()
    return t, Y.cross(t).normalized()
def pipe_wall(name, pts, r_in, r_out, m_, a0=0.0, a1=math.pi, seg=20, caps=True, link=True, s_off=0.0, s_tot=None):
    """Half tube (angles a0..a1 around the axis, y >= 0) with wall thickness; r_in = 0 -> solid half cylinder.
    UV.x = arc length / s_tot (for the liner reveal masks)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
    s = arclen(pts); tot = s_tot or s[-1]
    A = [a0 + (a1 - a0) * k / seg for k in range(seg + 1)]
    ring_o, ring_i, us = [], [], []
    for i, p in enumerate(pts):
        t, v = frame_at(pts, i)
        ring_o.append([bm.verts.new(p + r_out * (math.cos(a) * v + math.sin(a) * Y)) for a in A])
        ring_i.append([bm.verts.new(p + r_in * (math.cos(a) * v + math.sin(a) * Y)) for a in A] if r_in > 0 else
                      [bm.verts.new(p + r_out * math.cos(a0) * v), bm.verts.new(p + r_out * math.cos(a1) * v)])
        us.append((s_off + s[i]) / tot)
    faces = []
    def F4(vs, u):
        try:
            f = bm.faces.new(vs)
            for lp, uu in zip(f.loops, u): lp[uvl].uv = (uu, 0.5)
            faces.append(f)
        except ValueError: pass
    for i in range(len(pts) - 1):
        u0, u1 = us[i], us[i + 1]
        for k in range(seg):
            F4([ring_o[i][k], ring_o[i][k + 1], ring_o[i + 1][k + 1], ring_o[i + 1][k]], [u0, u0, u1, u1])
            if r_in > 0: F4([ring_i[i][k + 1], ring_i[i][k], ring_i[i + 1][k], ring_i[i + 1][k + 1]], [u0, u0, u1, u1])
        if r_in > 0:
            F4([ring_i[i][0], ring_o[i][0], ring_o[i + 1][0], ring_i[i + 1][0]], [u0, u0, u1, u1])
            F4([ring_o[i][seg], ring_i[i][seg], ring_i[i + 1][seg], ring_o[i + 1][seg]], [u0, u0, u1, u1])
        else:
            F4([ring_i[i][0], ring_i[i][1], ring_i[i + 1][1], ring_i[i + 1][0]], [u0, u0, u1, u1])
    if caps:
        for i in (0, len(pts) - 1):
            u = us[i]
            if r_in > 0:
                for k in range(seg): F4([ring_o[i][k], ring_o[i][k + 1], ring_i[i][k + 1], ring_i[i][k]], [u] * 4)
            else:
                F4(ring_o[i] + [], [u] * len(ring_o[i]))
    o = mesh_obj(name, bm, m_, link=link)
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(50))
    except Exception: pass
    return o
def half_torus(name, R, r, m_, segU=28, segV=14):
    """torus around local Z, only local y >= 0 kept (major angle 0..pi)."""
    bm = bmesh.new(); rings = []
    for i in range(segU + 1):
        a = math.pi * i / segU; c = Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c * (R + r * math.cos(2 * math.pi * j / segV)) + Vector((0, 0, r * math.sin(2 * math.pi * j / segV)))) for j in range(segV)])
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(segV): bm.faces.new([r0[j], r0[(j + 1) % segV], r1[(j + 1) % segV], r1[j]])
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def orient(t):
    """rotation with local Z -> tangent t (in XZ), local Y -> world Y."""
    t = Vector(t).normalized(); v = Y.cross(t).normalized()
    return Matrix((v, Y, t)).transposed().to_euler()
def bake_rot(o, fn):
    vals = [fn(t) for t in TS]
    for ax in range(3): bake(o, "rotation_euler", ax, [v[ax] for v in vals])


# ================= layout (1 unit = 10 cm, pipes exaggerated ~3x so they read on a phone) =================
R_IN, R_OUT = 0.55, 0.72          # shower drain / trap arm
RS_IN, RS_OUT = 0.80, 1.00        # stack + building drain
LEV_FULL, LEV_EMPTY, LEV_LOW = 26.72, 23.3, 24.25
X0 = 300.0                        # demo studio (slope test), far to the right
ARM = fillet_path([(-14, 0, 30.6), (-14, 0, 24.2), (-11.2, 0, 24.2), (-11.2, 0, 27.3), (4.0, 0, 26.4)], 1.35, n=14, step=0.5)
STACK = [Vector((4, 0, z)) for z in (-0.6, 79.0)]
TOI = fillet_path([(13, 0, 30.6), (13, 0, 26.0), (4.9, 0, 25.3)], 1.5, step=0.6)
SINK = fillet_path([(18, 0, 8.4), (18, 0, 4.6), (4.9, 0, 3.9)], 1.2, step=0.6)
BLD = fillet_path([(4, 0, 2.0), (4, 0, -3.4), (44, 0, -5.4), (56.6, 0, -10.8)], 2.0, step=0.8)
DOWN = [Vector((4, 0, z)) for z in (26.4, 14.0, 2.0)]

T_HOOK = (0.0, C["without"]); T_STAKE = (C["without"], C["heres"]); T_ON = (C["heres"], C["new"]); T_PUSH = (C["new"], C["then"])
T_SLOPE = (C["then"], C["too"]); T_FLAT = (C["too"], C["too2"]); T_STEEP = (C["too2"], C["but"]); T_SIPH = (C["but"], C["so"])
T_VENT = (C["so"], C["thats"]); T_ROOF = (C["thats"], C["from"]); T_HOUSE = (C["from"], C["and_"]); T_DRY = (C["and_"], C["thats2"])
T_SMELL = (C["thats2"], C["do"]); T_CTA = (C["do"], DUR)

# ================= materials =================
M_SOIL = strata("Soil", [(0.09, 0.055, 0.03), (0.17, 0.10, 0.05), (0.12, 0.075, 0.04), (0.21, 0.13, 0.07)], scale=0.06, bump=0.5)
M_CONC, _ = mat("Concrete", (0.50, 0.49, 0.46), rough=0.85, noise=0.8)
M_TILE = tiles("ShowerTile", (0.86, 0.88, 0.88), (0.80, 0.83, 0.84), 0.35, plane="XZ")
M_FLOOR = tiles("FloorTile", (0.30, 0.31, 0.33), (0.26, 0.27, 0.29), 0.45, plane="XY")
M_WALL, _ = mat("Wall", (0.80, 0.76, 0.68), rough=0.8)
M_WALL2, _ = mat("WallBlue", (0.36, 0.48, 0.56), rough=0.8)
M_WALLCUT, _ = mat("WallCut", (0.92, 0.90, 0.86), rough=0.9, noise=2.0)
M_WOOD, _ = mat("Wood", (0.52, 0.36, 0.20), rough=0.6, noise=3.0)
M_JOIST, _ = mat("Joist", (0.62, 0.46, 0.27), rough=0.7, noise=2.5)
M_DRY, _ = mat("Drywall", (0.85, 0.84, 0.82), rough=0.9)
M_CERAMIC, _ = mat("Ceramic", (0.95, 0.96, 0.97), rough=0.12)
M_CHROME, _ = mat("Chrome", (0.85, 0.86, 0.88), rough=0.08, metallic=1.0)
M_PVC, B_PVC = mat("PVC", (0.90, 0.90, 0.88), rough=0.32, emit_rgb=(0.30, 0.92, 1.0))
M_PVCS, B_PVCS = mat("PVCStack", (0.88, 0.88, 0.86), rough=0.32, emit_rgb=(0.30, 0.92, 1.0))
M_CAB, _ = mat("Cabinet", (0.18, 0.26, 0.32), rough=0.5)
M_COUNTER, _ = mat("Counter", (0.90, 0.90, 0.88), rough=0.2)
M_ROOF, _ = mat("Shingles", (0.16, 0.15, 0.15), rough=0.85, noise=6.0)
M_GRASS, _ = mat("Grass", (0.12, 0.24, 0.06), rough=0.9, noise=0.4)
M_TUFT, _ = mat("Tuft", (0.17, 0.34, 0.07), rough=0.9)
M_ASPH, _ = mat("Asphalt", (0.06, 0.06, 0.065), rough=0.9, noise=3.0)
M_STUDIO, _ = mat("Studio", (0.035, 0.04, 0.05), rough=0.6)
M_GUNK, _ = mat("Gunk", (0.25, 0.17, 0.08), rough=0.7, noise=5.0)
M_HAIR, _ = mat("Hair", (0.10, 0.07, 0.05), rough=0.6)
M_CYANG, B_CYANG = emit_mat("CyanGlow", (0.30, 0.92, 1.0), 7.0)
M_WHITEG, _ = emit_mat("WhiteGlow", (0.85, 0.95, 1.0), 5.0)
M_GOLDG, _ = emit_mat("GoldGlow", (0.98, 0.74, 0.27), 6.0)
M_GAS, B_GAS = emit_mat("SewerGas", (0.45, 0.95, 0.20), 3.5)
M_WINDOW, _ = emit_mat("Window", (1.0, 0.78, 0.55), 2.5)
M_GLASS, B_GLASS = mat("Glass", (0.92, 0.97, 1.0), rough=0.02)
B_GLASS.inputs["Transmission Weight"].default_value = 1.0; B_GLASS.inputs["IOR"].default_value = 1.45
M_WATER, B_WATER, _V = water_sec("TrapWater", dens=0.06)
glow(B_WATER, [(0, 0.6), (C["full"] - 0.05, 0.6), (C["full"] + 0.25, 3.0), (C["right"], 0.8)] + pulse(C["seal"], 4.0, base=0.8, hold=0.9)
     + pulse(C["seal2"], 3.0, base=0.8, hold=0.8))

# ================= ground, house shell =================
SOIL = box("Soil", -160, 160, 0, 60, -90, 0, M_SOIL)
GR_L = box("GrassL", -70, -31, 0, 60, 0, 0.45, M_GRASS); GR_R = box("GrassR", 31, 46, 0, 60, 0, 0.45, M_GRASS)
box("FarGrass", -900, 900, 60, 1400, -0.4, 0.3, M_GRASS)
box("Street", 46, 90, 0, 60, -0.8, 0.25, M_ASPH)
for i in range(6): box(f"Lane{i}", 52 + i * 7, 55.5 + i * 7, 8, 9, 0.25, 0.3, M_WHITEG)
SLAB = box("Slab", -31, 31, 0, 31, 0, 1.2, M_CONC)
box("WallBack", -31, 31, 30, 31, 1.2, 55, M_WALL)
box("WallUpBack", -30, 20, 29.8, 30, 30.5, 54, M_TILE)
box("WallL", -31, -30, 0, 31, 1.2, 55, M_WALLCUT); box("WallR", 30, 31, 0, 31, 1.2, 55, M_WALLCUT)
box("Partition", 20, 20.6, 0, 30, 30.5, 54, M_WALLCUT)
box("BedWall", 20.6, 30, 29.8, 30, 30.5, 54, M_WALL2)
box("Ceiling1", -30, 30, 0, 30, 21.6, 22.2, M_DRY)
DECK = box("Deck", -30, 30, 0, 30, 29.2, 30.2, M_WOOD)
TILEF = box("BathFloor", -30, 20, 0, 30, 30.2, 30.5, M_FLOOR)
bm = bmesh.new()
for i in range(15):
    x = -28.6 + i * 4.0
    if abs(x - 4) < 1.2: continue
    add_box(bm, x, x + 0.45, 0.6, 30, 22.2, 29.2)
JOISTS = mesh_obj("Joists", bm, M_JOIST)
CEIL2 = box("Ceiling2", -31, 31, 0, 31, 54, 55.2, M_DRY)
bm = bmesh.new(); prof = [(-35, 55.2), (35, 55.2), (0, 75.0)]
v0 = [bm.verts.new((x, -0.5, z)) for x, z in prof]; v1 = [bm.verts.new((x, 31.5, z)) for x, z in prof]
for k in range(3): bm.faces.new([v0[k], v0[(k + 1) % 3], v1[(k + 1) % 3], v1[k]])
bm.faces.new(list(reversed(v0))); bm.faces.new(v1); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
ROOF = mesh_obj("Roof", bm, M_ROOF)
box("WindowUp", 22, 28, 29.7, 29.75, 38, 48, M_WINDOW); box("WindowDown", -24, -14, 29.95, 30.0, 8, 17, M_WINDOW)
box("WallDownBack", -30, 30, 29.95, 30.0, 1.2, 21.6, M_WALL2)

# bathroom: shower corner (left), glass screen, toilet (right of the stack)
box("ShowerCurb", -9.4, -8.8, 0, 30, 30.5, 31.1, M_CERAMIC)
box("ShowerSide", -19.4, -18.8, 0, 30, 30.5, 54, M_TILE)
box("Glass", -9.2, -9.0, 0.5, 26, 31.1, 50, M_GLASS)
box("GlassRail", -9.3, -8.9, 0.5, 26, 50, 50.4, M_CHROME)
GRATE = half_cyl("Grate", 1.05, -14, 0.0, 0.0, 30.5, 30.62, M_CHROME, seg=40)
for i in range(5): box(f"Slot{i}", -14.75 + i * 0.35, -14.6 + i * 0.35, 0.05, 0.9, 30.6, 30.63, M_HAIR)
box("HeadArm", -18.8, -16.4, 2.6, 3.2, 47.3, 47.8, M_CHROME)
HEAD = cyl("Head", 0.9, 0.35, "X", (-16.2, 2.9, 47.2), M_CHROME, seg=32); HEAD.rotation_euler = (0, math.radians(-35), 0)
box("Valve", -18.8, -18.3, 2.4, 3.4, 40.0, 41.0, M_CHROME)
lathe("Bowl", [(0.0, 33.0), (2.0, 33.2), (2.2, 34.6), (1.9, 34.8), (1.6, 33.6), (0.0, 33.5)], M_CERAMIC, ang=2 * math.pi, loc=(13, 2.6, 0))
lathe("Pedestal", tube_prof(0.0, 1.2, 30.5, 33.1), M_CERAMIC, ang=2 * math.pi, loc=(13, 2.6, 0))
box("Tank", 11.2, 14.8, 4.6, 6.4, 34.6, 39.0, M_CERAMIC)
box("Mirror", -6.0, 0.0, 29.6, 29.7, 40, 47, M_CHROME)
# ground floor kitchen sink
box("SinkCab", 14.5, 22.0, 1.2, 8.0, 1.2, 8.6, M_CAB); box("Counter", 14.0, 30.0, 0.6, 8.4, 8.6, 9.3, M_COUNTER)
lathe("Basin", tube_prof(1.8, 2.0, 8.0, 9.35), M_CHROME, ang=2 * math.pi, loc=(18, 3.6, 0))
box("Fridge", 23.0, 29.5, 4.0, 10.0, 1.2, 19.0, M_CHROME)
box("Sofa", -26.0, -10.0, 3.0, 10.0, 1.2, 5.5, M_WALL2); box("SofaBack", -26.0, -10.0, 8.5, 10.5, 5.5, 9.0, M_WALL2)
box("Bed", 21.5, 29.5, 2.0, 18.0, 30.5, 33.5, M_DRY)

# ================= pipes (half tubes, cut at y = 0) =================
def stack_like(name, pts, ri, ro, m_):
    return pipe_wall(name, pts, ri, ro, m_, seg=24)
P_ARM = stack_like("TrapArm", ARM, R_IN, R_OUT, M_PVC)
P_STACK = stack_like("Stack", STACK, RS_IN, RS_OUT, M_PVCS)
P_TOI = stack_like("ToiletDrain", TOI, RS_IN, RS_OUT, M_PVCS)
P_SINK = stack_like("SinkDrain", SINK, R_IN, R_OUT, M_PVCS)
P_BLD = stack_like("BuildingDrain", BLD, RS_IN, RS_OUT, M_PVCS)
for nm, z in (("TeeArm", 26.4), ("TeeToi", 25.3), ("TeeSink", 3.9)):
    pipe_wall(nm, [Vector((4, 0, z - 1.4)), Vector((4, 0, z + 1.4))], RS_OUT, RS_OUT + 0.18, M_PVCS, seg=24)
pipe_wall("VentCap", [Vector((4, 0, 78.4)), Vector((4, 0, 79.0))], RS_OUT, RS_OUT + 0.25, M_ROOF, seg=24)
cuts = [cutter("CutArm", ARM, [R_OUT + 0.05] * len(ARM)), cutter("CutStack", STACK, [RS_OUT + 0.05] * 2),
        cutter("CutToi", TOI, [RS_OUT + 0.05] * len(TOI)), cutter("CutSink", SINK, [R_OUT + 0.05] * len(SINK)),
        cutter("CutBld", BLD, [RS_OUT + 0.05] * len(BLD))]
for tgt in (SOIL, SLAB, DECK, TILEF, JOISTS, CEIL2, ROOF, GRATE):
    for c_ in cuts: boolean(tgt, c_, c_.name)
# trap water: interior solid of the U, intersected with a level box (keyed height)
WP = [p for p in ARM if p.z <= 28.8 and p.x <= -10.0]
bm = sweep_bm(WP, [R_IN * 0.97] * len(WP), seg=28, cap=True); cut_front(bm, 0.0, fill=True)
WATER = mesh_obj("TrapWater", bm, M_WATER)
LEVBOX = box("LevelBox", -17, -9, -2, 3, -12, 0, None); LEVBOX.hide_render = True; LEVBOX.display_type = "WIRE"
md = WATER.modifiers.new("Level", "BOOLEAN"); md.operation = "INTERSECT"; md.object = LEVBOX
try: md.solver = "EXACT"
except Exception: pass
LEV = PW([(0, LEV_FULL), (C["without"] + 0.05, LEV_FULL), (C["without"] + 0.5, LEV_EMPTY), (C["heres"] - 0.3, LEV_EMPTY),
          (C["happens"], LEV_FULL), (C["suction"], LEV_FULL), (C["dry"] + 0.2, LEV_LOW + 0.35), (C["so"] + 0.1, LEV_LOW + 0.35),
          (C["vent"], LEV_FULL), (C["shower4"], LEV_FULL), (C["evaporates"] + 0.4, LEV_LOW)])
bake_fn(LEVBOX, "location", 2, LEV)
for nm, x0 in (("SealRing", -12.6),):
    pass

# ================= flows =================
def P(pts): return Path(pts)
SPRAY = [P([(-16.0 + dx, 2.6 + dy, 46.6), (-14.4 + dx * 0.4, 0.9 + dy * 0.3, 30.7)]) for dx, dy in ((0, 0), (0.5, 0.3), (-0.4, 0.5), (0.25, -0.2))]
for i, sp in enumerate(SPRAY):
    beads(f"Spray{i}", sp, 7, 0.09, M_CYANG, [(C["happens"], C["then"] + 0.3)], 32.0)
INLET = P([p for p in ARM if p.z <= 30.6 and p.x <= -12.0])
beads("NewWater", INLET, 6, 0.22, M_CYANG, [(C["drops"], C["then"] + 0.5)], 6.0)
OUTP = P([p for p in ARM if p.x >= -11.6 and p.z >= 25.6] + DOWN[1:] + BLD[3:])
beads("OldWater", P([p for p in ARM if p.x >= -11.4 and p.z >= 26.0]), 8, 0.2, M_WHITEG, [(C["pushes"], C["then"])], 5.0)
ARMP = P([p for p in ARM if p.x >= -11.0])
beads("ArmFlow", ARMP, 10, 0.2, M_CYANG, [(C["then"], C["too"])], 6.5)
beads("Slug", ARMP, 22, 0.32, M_CYANG, [(C["rushing"] - 0.2, C["so"])], 14.0)
GAS = P(list(reversed([p for p in ARM if p.z <= 30.6])) + [Vector((-14, -0.5, 34)), Vector((-13.4, -1.2, 39)), Vector((-12.6, -1.8, 45))])
GAS2 = P([Vector(p) for p in [(-14, 0, 25.4), (-14, 0, 30.6), (-14.4, -0.6, 35), (-15.2, -1.4, 40), (-16.0, -2.0, 46)]])
def gas_scale(path):
    return lambda t, i: 0.5 + 1.3 * lin((path_z(t, i, path) - 28.0) / 16.0)
def path_z(t, i, path): return 0.0
beads("Gas", GAS, 14, 0.42, M_GAS, [(C["sewer"] - 0.2, C["heres"] - 0.1)], 9.0)
beads("GasDry", GAS2, 10, 0.45, M_GAS, [(C["guest"] - 0.4, C["do"] + 0.2)], 5.0)
HOUSE_W = (C["from"], C["and_"] + 0.1)
beads("FlowShower", P([p for p in ARM] + DOWN[1:] + BLD[2:]), 26, 0.24, M_CYANG, [HOUSE_W], 16.0)
beads("FlowToilet", P(TOI + DOWN[1:] + BLD[2:]), 18, 0.3, M_GOLDG, [(C["toilet"], HOUSE_W[1])], 16.0)
beads("FlowSink", P(SINK + BLD[2:]), 14, 0.24, M_CYANG, [(C["sinks"], HOUSE_W[1])], 16.0)
# air arrows: siphon pull along the arm, vent air coming down the stack and in at the roof
bm = bmesh.new()
for k in range(3): add_arrow(bm, (-2.0 + k * 3.2, 27.9), (1, -0.05), 2.4, 0.8, y=-0.9)
AIR_ARM = mesh_obj("AirArm", bm, M_WHITEG)
bake_fn(AIR_ARM, "location", 0, lambda t: 3.0 * ((t - C["pulls"]) % 1.0))
windows(AIR_ARM, [(C["air"] - 0.1, C["so"])])
bm = bmesh.new()
for k in range(5): add_arrow(bm, (6.2, 77.0 - k * 9.5), (0, -1), 3.4, 1.1, y=-0.9)
AIR_STACK = mesh_obj("AirStack", bm, M_WHITEG)
bake_fn(AIR_STACK, "location", 2, lambda t: -3.0 * ((t - C["vent"]) % 1.2) / 1.2)
windows(AIR_STACK, [(C["letting"] - 0.6, C["from"])])
bm = bmesh.new(); add_arrow(bm, (4, 86.0), (0, -1), 5.0, 2.2, y=-1.5)
AIR_ROOF = mesh_obj("AirRoof", bm, M_GOLDG)
bake_fn(AIR_ROOF, "location", 2, lambda t: -2.5 * ((t - C["thats"]) % 0.9) / 0.9)
windows(AIR_ROOF, [(C["thats"], C["from"])])
glow(B_PVCS, [(0, 0.0)] + pulse(C["vent"], 1.2, hold=C["from"] - C["vent"] - 0.6))
glow(B_PVC, [(0, 0.0)] + pulse(C["then"], 0.8, hold=1.4))

# sewer main / septic tank
SEWER = cyl("SewerMain", 3.6, 60, "Y", (60, 30, -12), M_CONC, seg=48)
SEW_IN = cyl("SewerHole", 3.0, 62, "Y", (60, 30, -12), None, seg=48); SEW_IN.hide_render = True; SEW_IN.display_type = "WIRE"
boolean(SEWER, SEW_IN, "Hole"); boolean(SOIL, SEWER, "SewerCut")
SEWW = box("SewerWater", 57.4, 62.6, 0, 60, -14.8, -13.2, M_WATER)
SEPTIC = box("Septic", 52, 68, 0, 30, -11, -2.0, M_CONC)
SEPIN = box("SepticIn", 52.8, 67.2, -1, 29, -10.2, -2.8, None); SEPIN.hide_render = True; SEPIN.display_type = "WIRE"
boolean(SEPTIC, SEPIN, "Hollow")
SEPW = box("SepticWater", 52.8, 67.2, 0.05, 29, -10.2, -5.4, M_WATER)
SEPT_SOIL = box("SepticSoilCut", 51.8, 68.2, -1, 31, -11.2, -1.8, None); SEPT_SOIL.hide_render = True; SEPT_SOIL.display_type = "WIRE"
SOIL_SEPT = box("SoilFill", 46.5, 70, 0.02, 30, -26, -0.8, M_SOIL)
boolean(SOIL_SEPT, SEPT_SOIL, "SepticHole"); boolean(SOIL_SEPT, SEWER, "SewerHole2")
for c_ in cuts: boolean(SOIL_SEPT, c_, c_.name)
SEPT_T = C["septic"] - 0.1
for o in (SEPTIC, SEPW, SOIL_SEPT): windows(o, [(SEPT_T, C["and_"])])

# ================= slope demo studio (rigid gunk on a flat pipe, beads racing in a steep one) =================
box("StudioBack", X0 - 40, X0 + 40, 7, 8, -20, 30, M_STUDIO); box("StudioFloor", X0 - 40, X0 + 40, -6, 8, -4.2, -3.8, M_STUDIO)
FLATP = pipe_wall("FlatPipe", [Vector((X0 - 12, 0, 0)), Vector((X0 + 12, 0, 0))], 1.1, 1.35, M_PVC, seg=28)
STEEP = pipe_wall("SteepPipe", [Vector((X0 - 10, 0, 5.5)), Vector((X0 + 10, 0, -5.5))], 1.1, 1.35, M_PVC, seg=28)
windows(STEEP, [T_STEEP])
GUNK = []
for i in range(9):
    g = obj_from(f"Gunk{i}", sphere_mesh(f"GunkM{i}", 0.32 + 0.12 * random.random(), 1), M_GUNK,
                 loc=(X0 - 6 + i * 1.4 + random.uniform(-0.3, 0.3), 0.35 + random.uniform(0, 0.4), 2.2 + random.uniform(0, 2.5)))
    GUNK.append(g)
for i, g in enumerate(GUNK):
    x0_, y0_, z0_ = tuple(g.location); t0_ = C["too"] + 0.15 + 0.12 * i
    bake_loc(g, lambda t, x0_=x0_, y0_=y0_, t0_=t0_: (x0_ + 0.02 * max(0.0, t - t0_ - 0.6), y0_, -0.78 + drop(t, t0_, h=3.2, d=0.5)))
    windows(g, [T_FLAT])
windows(FLATP, [T_FLAT])
beads("FlatWater", P([(X0 - 12, 0.5, -0.75), (X0 + 12, 0.5, -0.75)]), 8, 0.22, M_CYANG, [T_FLAT], 1.0)
SP = P([(X0 - 10, 0.5, 4.6), (X0 + 10, 0.5, -6.4)])
beads("SteepWater", SP, 10, 0.24, M_CYANG, [T_STEEP], 14.0)
for i in range(4):
    g = obj_from(f"Solid{i}", sphere_mesh(f"SolidM{i}", 0.42, 1), M_GUNK)
    bake_loc(g, lambda t, i=i: tuple(SP.at(2.5 + i * 1.6 + 1.2 * max(0.0, t - C["too2"]))))
    windows(g, [T_STEEP])

# ================= fx: hdri sky, glare, particles (shower spray + vapour), scatter =================
fx.hdri("sunset", strength=0.75, rotation_deg=200.0, show_background=True)
fx.glare(threshold=1.0, strength=0.55, size=7)
bpy.ops.mesh.primitive_circle_add(vertices=16, radius=0.75, fill_type="NGON", location=(-16.05, 2.9, 46.95))
EMIT = bpy.context.active_object; EMIT.name = "SprayEmitter"; EMIT.rotation_euler = (0, math.radians(165), 0)
EMIT.hide_render = True
for c_ in list(EMIT.users_collection): c_.objects.unlink(EMIT)
CL.objects.link(EMIT)
pm = fx.particles(EMIT, "rain", F(C["happens"]), F(C["then"]), count=2600)
if pm:
    s = pm.particle_system.settings; s.normal_factor = 26.0; s.lifetime = 20; s.particle_size = 0.07; s.factor_random = 0.25
    s.render_type = "OBJECT"
    EMIT.show_instancer_for_render = False
    try:
        dm = s.instance_object.data.materials[0]; bsdf_of(dm).inputs["Emission Color"].default_value = (0.5, 0.9, 1.0, 1)
        bsdf_of(dm).inputs["Emission Strength"].default_value = 3.0
    except Exception as e: print("[build] spray glow", e)
VAP = cyl("VapourEmitter", 0.45, 0.05, "Z", (-14, 0.3, 25.6), None, seg=12); VAP.hide_render = True
vm = fx.particles(VAP, "dust", F(C["unused"]), F(C["evaporates"] + 0.6), count=160)
if vm:
    s = vm.particle_system.settings; s.particle_size = 0.07; s.normal_factor = 3.0; s.lifetime = 45
    s.effector_weights.gravity = -0.05; VAP.show_instancer_for_render = False
    try:
        dm = s.instance_object.data.materials[0]; bsdf_of(dm).inputs["Emission Color"].default_value = (0.8, 0.95, 1.0, 1)
        bsdf_of(dm).inputs["Emission Strength"].default_value = 2.5
    except Exception as e: print("[build] vapour glow", e)
bm = bmesh.new(); add_cyl(bm, 0.12, 1.4, "Z", (0, 0, 0.7), seg=5, r2=0.0); add_cyl(bm, 0.1, 1.0, "Z", (0.25, 0, 0.5), seg=5, r2=0.0)
TUFT = mesh_obj("TuftProto", bm, M_TUFT)
fx.scatter(GR_L, TUFT, density=3.0, scale_min=0.5, scale_max=1.3, seed=3)
fx.scatter(GR_R, TUFT, density=3.0, scale_min=0.5, scale_max=1.3, seed=4)

# ================= lights =================
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 3.0; sun_d.angle = math.radians(2.0); sun_d.color = (1.0, 0.80, 0.60)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = (math.radians(58), 0, math.radians(-35))
def area(name, loc, size, energy, rot=(0, 0, 0), color=(1.0, 0.92, 0.82)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = color
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return d
area("BathLight", (-6.0, 15.0, 53.0), 14.0, 2200.0)
area("ShowerLight", (-14.0, 12.0, 53.0), 5.0, 900.0, color=(0.95, 0.97, 1.0))
area("Kitchen", (8.0, 14.0, 21.0), 20.0, 1800.0)
area("Cavity", (-6.0, -6.0, 25.6), 18.0, 450.0, rot=(math.radians(90), 0, 0), color=(0.75, 0.88, 1.0))
area("UnderSlab", (25.0, -14.0, -6.0), 40.0, 1200.0, rot=(math.radians(90), 0, 0), color=(1.0, 0.85, 0.7))
area("StudioKey", (X0 - 8, -10, 12), 16.0, 2600.0, rot=(math.radians(50), 0, math.radians(-20)), color=(0.95, 0.97, 1.0))
area("StudioRim", (X0 + 12, 4, 8), 8.0, 1500.0, rot=(math.radians(-60), 0, math.radians(30)), color=(0.4, 0.85, 1.0))
GREEN_D = bpy.data.lights.new("GasGlow", "POINT"); GREEN_D.color = (0.45, 1.0, 0.25); GREEN_D.shadow_soft_size = 4.0
GREEN_O = bpy.data.objects.new("GasGlow", GREEN_D); scene.collection.objects.link(GREEN_O); GREEN_O.location = (-14.0, -4.0, 36.0)
for t_, v_ in [(0, 0.0), (C["sewer"] - 0.02, 0.0), (C["rise"], 9000.0), (C["heres"] - 0.05, 9000.0), (C["heres"], 0.0),
               (C["guest"] - 0.3, 0.0), (C["smell"], 7000.0), (C["do"] - 0.05, 7000.0), (C["do"], 0.0)]:
    GREEN_D.energy = v_; GREEN_D.keyframe_insert("energy", frame=F(t_))
RED_D = bpy.data.lights.new("DryRed", "POINT"); RED_D.color = (1.0, 0.25, 0.15); RED_D.shadow_soft_size = 2.0
RED_O = bpy.data.objects.new("DryRed", RED_D); scene.collection.objects.link(RED_O); RED_O.location = (-12.0, -4.0, 25.0)
for t_, v_ in [(0, 0.0), (C["suction"] - 0.02, 0.0), (C["dry"], 1500.0), (C["so"] - 0.05, 1500.0), (C["so"], 0.0),
               (C["seal2"], 0.0), (C["evaporates"] + 0.3, 1200.0), (C["thats2"] - 0.05, 1200.0), (C["thats2"], 0.0)]:
    RED_D.energy = v_; RED_D.keyframe_insert("energy", frame=F(t_))

# ================= camera (with depth of field on the close shots) =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 6000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-14.6, -10.5, 35.0), (-14.0, 1.0, 30.5), 30),
    (C["right"] - 0.1, (-14.2, -9.0, 31.6), (-13.6, 1.0, 28.4), 30),
    (C["u"], (-12.0, -7.4, 26.6), (-12.6, 1.0, 25.5), 32),
    (C["without"] - 0.05, (-11.7, -6.8, 26.3), (-12.6, 1.0, 25.5), 32),
    (C["without"], (-7.0, -36.0, 33.0), (-8.0, 0.0, 33.0), 26, "cut"),
    (C["heres"] - 0.05, (-8.0, -32.0, 34.0), (-9.0, 0.0, 33.5), 26),
    (C["heres"], (-12.5, -26.0, 41.0), (-14.0, 0.0, 39.0), 28, "cut"),
    (C["grate"], (-13.4, -15.0, 34.0), (-14.0, 0.0, 30.0), 28),
    (C["ubend"], (-12.0, -8.4, 27.4), (-12.6, 1.0, 25.6), 30),
    (C["new"], (-12.0, -6.6, 26.1), (-12.4, 1.0, 25.4), 32, "cut"),
    (C["then"] - 0.05, (-12.2, -6.0, 25.9), (-12.4, 1.0, 25.4), 32),
    (C["then"], (-6.0, -13.0, 29.5), (-5.0, 0.0, 26.8), 26, "cut"),
    (C["too"] - 0.05, (-1.0, -13.0, 29.5), (-0.5, 0.0, 26.8), 26),
    (C["too"], (X0, -12.0, 3.5), (X0, 0.0, 0.0), 30, "cut"),
    (C["too2"] - 0.05, (X0 + 1.0, -11.0, 3.0), (X0, 0.0, 0.0), 30),
    (C["too2"], (X0, -15.0, 3.0), (X0, 0.0, -0.4), 30, "cut"),
    (C["but"] - 0.05, (X0 + 1.0, -14.0, 2.5), (X0, 0.0, -0.4), 30),
    (C["but"], (-6.0, -19.0, 30.0), (-5.5, 0.0, 26.6), 26, "cut"),
    (C["so"] - 0.05, (-5.0, -17.0, 29.5), (-5.0, 0.0, 26.6), 26),
    (C["so"], (0.5, -15.0, 30.0), (3.0, 0.0, 28.5), 26, "cut"),
    (C["roof"], (2.0, -24.0, 66.0), (4.0, 0.0, 66.0), 26),
    (C["thats"] - 0.05, (2.0, -24.0, 69.0), (4.0, 0.0, 69.0), 26),
    (C["thats"], (30.0, -72.0, 100.0), (4.0, 10.0, 76.0), 34, "cut"),
    (C["from"] - 0.05, (25.0, -66.0, 95.0), (4.0, 10.0, 76.0), 34),
    (C["from"], (22.0, -150.0, 26.0), (22.0, 0.0, 26.0), 26, "cut"),
    (C["and_"] - 0.05, (24.0, -140.0, 24.0), (23.0, 0.0, 24.0), 26),
    (C["and_"], (-12.0, -7.6, 26.6), (-12.6, 1.0, 25.4), 32, "cut"),
    (C["thats2"] - 0.05, (-12.0, -6.8, 26.0), (-12.6, 1.0, 25.2), 32),
    (C["thats2"], (-9.0, -33.0, 36.0), (-10.0, 0.0, 35.0), 26, "cut"),
    (C["do"] - 0.05, (-9.5, -30.0, 36.5), (-10.5, 0.0, 35.5), 26),
    (C["do"], (-6.0, -48.0, 40.0), (-8.0, 0.0, 37.0), 26, "cut"),
    (DUR, (-10.0, -32.0, 38.0), (-11.0, 0.0, 36.5), 26),
]
def ev(p, t): return Vector(p(t)) if callable(p) else Vector(p)
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
cam_d.dof.use_dof = True; cam_d.dof.focus_object = TGT
FST = [max(0.25, min(16.0, 0.035 * (cl - ct).length ** 1.5)) for cl, ct in zip(cam_loc, cam_tgt)]
bake_scalar(cam_d, "dof.aperture_fstop", FST)
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 6; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(4.0, min(2.0e5, 14.0 * ((cl - ct).length / 5.0) ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (1.5, 2.0, 0)

# ================= render settings =================
fx.engine("cycles")
r = scene.render
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
scene.view_settings.exposure = float(arg("--exposure", "-0.3"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================


# ================= export cues, events and projected anchors for the typography =================
AP = {
    "grate": (-14.0, 0.0, 30.8), "trap": (-12.6, 0.0, 23.3), "seal": (-12.6, 0.0, 24.6), "arm": (-4.0, 0.0, 27.8),
    "stack": (4.0, 0.0, 44.0), "vent": (4.0, 0.0, 79.2), "toilet": (13.0, 0.0, 36.0), "sink": (18.0, 0.0, 10.0),
    "drain": (30.0, 0.0, -4.0), "sewer": (60.0, 0.0, -8.0), "septic": (60.0, 0.0, -1.5), "demo": (X0, 0.0, 1.6),
    "head": (-16.2, 2.9, 47.2),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); t = TS[fr - 1]
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "stake": RR(*T_STAKE), "on": RR(*T_ON), "push": RR(*T_PUSH), "slope": RR(*T_SLOPE),
          "flat": RR(*T_FLAT), "steep": RR(*T_STEEP), "siphon": RR(*T_SIPH), "vent": RR(*T_VENT), "roof": RR(*T_ROOF),
          "house": RR(*T_HOUSE), "septic": round(SEPT_T, 3), "dry": RR(*T_DRY), "smell": RR(*T_SMELL), "cta": RR(*T_CTA),
          "gas": round(C["sewer"], 3), "drain_dry": round(C["dry"], 3), "seal": round(C["seal"], 3)}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
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
