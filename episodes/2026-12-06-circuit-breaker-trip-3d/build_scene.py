# Circuit breaker trip (3d-49a): "A circuit breaker isn't there to protect your TV. It's there to keep the wires in your walls from catching fire."
# Stake: wiring, cords and lights start ~32,620 US home fires a year (NFPA 2015-2019). A standard thermal-magnetic breaker: current runs through a
# bimetal strip; an overload heats it, the two metals expand at different rates, it bends, pushes the latch, the spring snaps the contacts open.
# A short circuit (hot touches neutral/ground) sends thousands of amps: the coil becomes an electromagnet, yanks a plunger, trips the latch
# instantly. The arc between the parting contacts is pushed into the arc chute's splitter plates, split, cooled, put out. Most breakers stop in
# the middle when tripped; reset = OFF, then ON. Trip-free: holding the handle ON doesn't stop it tripping. A bigger breaker on the same wire
# lets the wire overheat before it trips.
# Illustrative, 1 unit = 1 cm. Sets: living-room wall cut open (x ~ 0: TV, panel, cable, heater + hair dryer) and a studio cutaway of one
# breaker at x = 600 (drawn ~2x, section plane y = 0, the front half only in the exterior shots). Generic parts, no brand, no text, no people.
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
DUR = round(WORDS[-1]["end"] + VO + 1.0, 2)   # CTA ending (19-20 Nov): complete question + "Tell me in the comments.", then ~1 s fade
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(49)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("a","A"),("breaker","breaker"),("protect","protect"),("tv","TV."),("its","It's"),("wires","wires"),("walls","walls"),("catching","catching"),
  ("fire","fire."),("us","US,"),("wiring","wiring,"),("cords","cords"),("lights","lights"),("thirty","thirty-two"),("fires","fires"),("every","Every"),
  ("watches","watches"),("two","two"),("trouble","trouble."),("inside","Inside,"),("current","current"),("strip","strip"),("two2","two"),("metals","metals"),
  ("bonded","bonded"),("plug","Plug"),("heater","heater"),("dryer","dryer"),("circuit","circuit,"),("climbs","climbs."),("strip2","strip"),("heats","heats"),
  ("wire","wire."),("expand","expand"),("speeds","speeds,"),("bends","bends."),("once","Once"),("pushes","pushes"),("latch","latch,"),("spring","spring"),
  ("snaps","snaps"),("apart","apart,"),("power","power"),("cut","cut."),("second","second"),("short","short"),("hot","hot"),("touches","touches"),
  ("ground","ground."),("thousands","Thousands"),("amps","amps"),("rush","rush"),("that","That"),("coil","coil"),("magnet","magnet,"),("yanks","yanks"),
  ("plunger","plunger"),("trips","trips"),("instantly","instantly."),("pulling","Pulling"),("apart2","apart"),("arc","arc."),("pushed","pushed"),
  ("stack","stack"),("plates","plates"),("split","split"),("kill","kill"),("on","On"),("handle","handle"),("middle","middle."),("push","Push"),
  ("off","off,"),("back","back"),("on2","on."),("cheat","cheat:"),("hold","hold"),("on3","on,"),("still","still"),("trips2","trips."),("if","If"),
  ("keeps","keeps"),("never","never"),("swap","swap"),("bigger","bigger"),("wire2","wire"),("same","same,"),("cook","cook"),("reacts","reacts."),
  ("which","Which"),("panel","panel"),("most","most?"),("tell","Tell"),("comments","comments.")]
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
CL = coll("Breaker")
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

# ================= helpers for this episode =================
def rbox_bm(x0, x1, y0, y1, z0, z1, r, seg=4):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=r, segments=seg, profile=0.5, affect="EDGES")
    return bm
def rbox(name, x0, x1, y0, y1, z0, z1, r, m_, seg=4):
    o = mesh_obj(name, rbox_bm(x0, x1, y0, y1, z0, z1, r, seg), m_)
    try: o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(35))
    except Exception: pass
    return o
def cut_back(bm, y_cut, fill=True):
    """Keep only y <= y_cut (the removable front half)."""
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, y_cut, 0), plane_no=(0, 1, 0), clear_outer=True)
    if fill:
        oe = [e for e in bm.edges if len(e.link_faces) < 2]
        if oe: bmesh.ops.edgeloop_fill(bm, edges=oe)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
def solidify(o, th):
    md = o.modifiers.new("Solid", "SOLIDIFY"); md.thickness = th; md.offset = -1.0; md.use_even_offset = True; return md
def torus(name, R, r, m_, loc, segU=40, segV=16):
    prof = [(R + r * math.cos(2 * math.pi * k / segV), r * math.sin(2 * math.pi * k / segV)) for k in range(segV)]
    bm = bmesh.new()
    rings = [[bm.verts.new(((rr) * math.cos(2 * math.pi * i / segU), (rr) * math.sin(2 * math.pi * i / segU), zz)) for rr, zz in prof] for i in range(segU)]
    for i in range(segU):
        a, b = rings[i], rings[(i + 1) % segU]
        for k in range(segV): bm.faces.new([a[k], a[(k + 1) % segV], b[(k + 1) % segV], b[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    o = mesh_obj(name, bm, m_); o.location = loc
    try: o.data.shade_smooth()
    except Exception: pass
    return o
def tube(name, pts, r, m_, seg=14, half=False):
    pts = chaikin([Vector(p) for p in pts], 3)
    bm = sweep_bm(pts, [r] * len(pts), seg, cap=not half)
    if half: cut_front(bm, 0.0, fill=False)
    o = mesh_obj(name, bm, m_)
    try: o.data.shade_smooth()
    except Exception: pass
    return o, pts
def bake_rot(o, fn):
    vals = [fn(t) for t in TS]
    for ax in range(3): bake(o, "rotation_euler", ax, [v[ax] for v in vals])
def winding_mat(name, rgb, scale, emit_rgb):
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); wv = N.new("ShaderNodeTexWave"); wv.wave_type = "RINGS" if False else "BANDS"
    wv.bands_direction = "X"; wv.inputs["Scale"].default_value = scale; L.new(tc.outputs["Object"], wv.inputs["Vector"])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 0.55; mr.inputs[4].default_value = 1.0
    L.new(wv.outputs["Fac"], mr.inputs[0])
    mx = mix_rgb(nt, mr.outputs[0], tuple(c * 0.45 for c in rgb), rgb); L.new(mx, b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.3
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b







# ================= this episode =================
scene.gravity = (0.0, 0.0, -981.0)          # cm world
X0, BZ = 600.0, 20.0                          # studio cutaway breaker set: local origin (X0, 0, BZ)
GOLD, CYAN, RED, ORANGE, GREEN = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.15), (0.25, 1.0, 0.35)
HOT = (1.0, 0.32, 0.08)
WHITEHOT = (0.85, 0.92, 1.0)

# ---------- state windows ----------
# cutaway breaker (set B): contacts closed / open, handle angle, trips
T_TRIP1 = C["snaps"]                          # thermal trip (bimetal -> latch -> spring)
T_RESET1 = C["second"]                        # unseen reset at the cut back to the house
T_TRIP2 = C["instantly"] - 0.15               # magnetic trip (short circuit)
T_RESET2 = C["on2"]                           # handle pushed off, then back on (exterior shot)
T_HOLD = C["hold"]                            # handle held ON from here
T_TRIP3 = C["trips2"] - 0.2                   # trip-free: contacts open with the handle held ON
OPEN_D = 0.22                                 # seconds for the spring to snap the arm open
ARM_OPEN = -math.radians(28.0)                # CCW: the moving contact lifts off the fixed one
LAT_TRIP = -math.radians(20.0)                # CCW: latch top slides out from under the arm tail
H_ON, H_MID, H_OFF = math.radians(24.0), 0.0, math.radians(-24.0)
def arm_ang(t):
    a = 0.0
    if T_TRIP1 <= t < T_RESET1: a = ARM_OPEN * ease((t - T_TRIP1) / OPEN_D)
    elif T_TRIP2 <= t < T_RESET2: a = ARM_OPEN * ease((t - T_TRIP2) / (OPEN_D * 2.5))      # slower on screen: the arc gets its moment
    elif t >= T_TRIP3: a = ARM_OPEN * ease((t - T_TRIP3) / OPEN_D)
    return a
def handle_ang(t):
    if t < T_TRIP1: return H_ON
    if t < T_RESET1: return H_ON + (H_MID - H_ON) * ease((t - T_TRIP1) / 0.18)
    if t < T_TRIP2: return H_ON
    if t < C["off"]: return H_ON + (H_MID - H_ON) * ease((t - T_TRIP2) / 0.25)
    if t < C["on2"]: return H_MID + (H_OFF - H_MID) * ease((t - C["off"]) / 0.22)
    return H_OFF + (H_ON - H_OFF) * ease((t - C["on2"]) / 0.22)                          # held ON through the trip-free beat
def latch_ang(t):
    a = 0.0
    if T_TRIP1 - 0.35 <= t < T_RESET1: a = LAT_TRIP * ease((t - (T_TRIP1 - 0.35)) / 0.35)
    elif C["yanks"] <= t < C["off"]: a = LAT_TRIP * ease((t - C["yanks"]) / 0.2)
    elif t >= T_TRIP3 - 0.3: a = LAT_TRIP * ease((t - (T_TRIP3 - 0.3)) / 0.3)
    return a
BEND_MAX = math.radians(15.0)
def bend_ang(t):
    """bimetal: bends a little on 'bends', far enough on 'once' to push the latch, cools after the cut."""
    if T_RESET1 <= t < T_HOLD: return 0.0
    if t >= T_HOLD: return BEND_MAX * ease((t - T_HOLD) / (T_TRIP3 - T_HOLD))
    return BEND_MAX * (0.4 * ease((t - C["expand"]) / (C["bends"] + 0.4 - C["expand"])) + 0.6 * ease((t - C["once"]) / (T_TRIP1 - 0.35 - C["once"])))

# ---------- materials ----------
M_SEC, B_SEC = mat("CutFace", (0.90, 0.38, 0.06), rough=0.5, emit_rgb=(1.0, 0.40, 0.08)); B_SEC.inputs["Emission Strength"].default_value = 0.10
def glowc(bsdf, keys):
    s_in, c_in = bsdf.inputs["Emission Strength"], bsdf.inputs["Emission Color"]
    for t, s, rgb in keys:
        s_in.default_value = s; s_in.keyframe_insert("default_value", frame=F(t))
        c_in.default_value = (*rgb, 1); c_in.keyframe_insert("default_value", frame=F(t))
M_BODY, _ = mat("BreakerBody", (0.035, 0.037, 0.042), rough=0.45)
M_BODYF, _ = mat("BreakerFront", (0.05, 0.052, 0.058), rough=0.4)
M_HANDLE, B_HANDLE = mat("Handle", (0.04, 0.04, 0.045), rough=0.35, emit_rgb=GOLD)
M_COPPER, B_COPPER = mat("Copper", (0.80, 0.42, 0.20), rough=0.25, metallic=1.0, emit_rgb=CYAN)
M_SILVER, B_SILVER = mat("ContactSilver", (0.85, 0.86, 0.88), rough=0.15, metallic=1.0, emit_rgb=GOLD)
M_STEEL, B_STEEL = mat("Steel", (0.62, 0.63, 0.66), rough=0.3, metallic=1.0, emit_rgb=GOLD)
M_PLATE, B_PLATE = mat("ArcPlate", (0.50, 0.52, 0.55), rough=0.35, metallic=1.0, emit_rgb=CYAN)
M_BIM1, B_BIM1 = mat("BimetalBrass", (0.86, 0.62, 0.30), rough=0.25, metallic=1.0, emit_rgb=GOLD)
M_BIM2, B_BIM2 = mat("BimetalSteel", (0.72, 0.73, 0.76), rough=0.25, metallic=1.0, emit_rgb=GOLD)
M_COIL, B_COIL = winding_mat("CoilWinding", (0.80, 0.42, 0.20), 9.0, CYAN)
M_SPRING, B_SPRING = mat("Spring", (0.75, 0.76, 0.78), rough=0.2, metallic=1.0, emit_rgb=GOLD)
M_BEAD, B_BEAD = emit_mat("Current", CYAN, 3.0)
M_ARC, B_ARC = emit_mat("Arc", (0.75, 0.85, 1.0), 40.0)
M_RING, F_RING = ghost("FieldRing", CYAN)
M_PRESS, B_PRESS = emit_mat("HoldPress", GOLD, 1.6)
M_STUDIO, _ = mat("StudioFloor", (0.03, 0.035, 0.045), rough=0.55)
M_BACK, _ = mat("Backdrop", (0.04, 0.05, 0.07), rough=0.8)
# house set
M_PAINT, _ = mat("WallPaint", (0.36, 0.38, 0.40), rough=0.85, noise=40)
M_DRY, _ = mat("DrywallCore", (0.80, 0.78, 0.72), rough=0.95, noise=80)
M_CAV, _ = mat("CavityBack", (0.16, 0.14, 0.12), rough=0.95, noise=30)
M_WOOD, _ = mat("Stud", (0.62, 0.45, 0.26), rough=0.7, noise=6)
M_FLOOR = tiles("FloorBoards", (0.30, 0.20, 0.12), (0.26, 0.17, 0.10), 0.05, plane="XY")
M_RUG, _ = mat("Rug", (0.10, 0.13, 0.18), rough=1.0, noise=30)
M_TUFT, _ = mat("RugTuft", (0.13, 0.17, 0.23), rough=1.0)
M_SHEATH, B_SHEATH = mat("CableSheath", (0.90, 0.88, 0.80), rough=0.5, emit_rgb=GOLD)
M_SCORCH, _ = mat("Scorch", (0.10, 0.06, 0.03), rough=0.9, noise=12)
M_PANEL, B_PANEL = mat("PanelSteel", (0.55, 0.57, 0.60), rough=0.35, metallic=0.8, emit_rgb=GOLD)
M_PIN, _ = mat("PanelInside", (0.22, 0.23, 0.25), rough=0.5, metallic=0.5)
M_BRK, B_BRK = mat("PanelBreaker", (0.04, 0.04, 0.045), rough=0.4, emit_rgb=GOLD)
M_BRKH, B_BRKH = mat("TargetHandle", (0.04, 0.04, 0.045), rough=0.35, emit_rgb=GOLD)
M_BIG, B_BIG = mat("BiggerBreaker", (0.05, 0.05, 0.055), rough=0.4, emit_rgb=RED)
M_TV, _ = mat("TVBody", (0.02, 0.02, 0.025), rough=0.3)
M_SCREEN, B_SCREEN = mat("TVScreen", (0.01, 0.01, 0.012), rough=0.1, emit_rgb=(0.25, 0.55, 1.0))
M_CONSOLE, _ = mat("Console", (0.20, 0.13, 0.08), rough=0.5, noise=5)
M_PLASTIC, _ = mat("ApplianceWhite", (0.86, 0.86, 0.84), rough=0.35)
M_GRILL, B_GRILL = mat("HeaterGrill", (0.10, 0.10, 0.10), rough=0.5, emit_rgb=HOT)
M_DRYER, B_DRYER = mat("DryerBody", (0.12, 0.13, 0.16), rough=0.35, emit_rgb=ORANGE)
M_CORD, _ = mat("Cord", (0.03, 0.03, 0.03), rough=0.5)
M_PLATEW, _ = mat("OutletPlate", (0.92, 0.91, 0.88), rough=0.3)
M_FLAME, B_FLAME = emit_mat("Flame", (1.0, 0.45, 0.10), 0.0)
M_NAIL, _ = mat("Nail", (0.55, 0.56, 0.58), rough=0.3, metallic=1.0)
M_FLASH, B_FLASH = emit_mat("ShortFlash", WHITEHOT, 0.0)

# =====================================================================
# SET B: the breaker cut in half (studio, x = X0). Local XZ profile, section plane y = 0, internals y -0.6..0.35
# =====================================================================
BRK = empty("BreakerRoot", (X0, 0.0, BZ))
def L(o): return par(o, BRK)
def P(x, z, y=0.0): return (x, y, z)
part = lambda o, p: par(o, p)
# back half shell: back plate + rim (the rim's front face = the cut face)
L(rbox("BackPlate", -7.0, 6.0, 0.35, 1.4, 0.0, 14.0, 0.4, M_BODY))
for nm, x0, x1, z0, z1 in [("RimL", -7.0, -6.4, 0.0, 14.0), ("RimR", 5.4, 6.0, 0.0, 14.0), ("RimB", -7.0, 6.0, 0.0, 0.6), ("RimT", -7.0, 6.0, 13.4, 14.0)]:
    bm = bmesh.new(); add_box(bm, x0, x1, 0.0, 0.35, z0, z1); o = mesh_obj(nm, bm, [M_BODY, M_SEC]); L(o)
    for f in o.data.polygons:
        if f.normal.y < -0.9: f.material_index = 1
for k in range(4):                                                # vents beside the arc chute (arc gases out)
    L(box(f"Vent{k}", 5.35, 6.05, -0.05, 0.36, 3.5 + k * 0.9, 3.9 + k * 0.9, M_STEEL))
FRONT = L(rbox("FrontHalf", -7.0, 6.0, -1.4, 0.0, 0.0, 14.0, 0.4, M_BODYF))
EXT_W = [(C["on"], C["cheat"])]
windows(FRONT, EXT_W)
# line side: stab jaw onto the bus bar + strap to the fixed contact
L(box("BusBar", 2.4, 6.6, -0.6, 0.6, -2.6, -1.6, M_COPPER))
for xx in (3.9, 5.1): L(box(f"Jaw{xx}", xx - 0.2, xx + 0.2, -0.3, 0.3, -1.8, 0.9, M_COPPER))
L(box("LineStrap", 1.0, 4.7, -0.3, 0.3, 2.2, 2.7, M_COPPER))
L(box("LineRiser", 4.3, 4.7, -0.3, 0.3, 0.6, 2.7, M_COPPER))
FC = (1.6, 2.95)
L(cyl("FixedContact", 0.42, 0.5, "Z", P(FC[0], FC[1]), M_SILVER, seg=20))
# arc chute: horizontal splitter plates stacked to the right of the contacts
PLATES_Z = [3.45 + 0.45 * k for k in range(8)]
for k, zz in enumerate(PLATES_Z):
    L(box(f"ArcPlate{k}", 2.6, 5.2, -0.32, 0.32, zz - 0.07, zz + 0.07, M_PLATE))
L(box("ChuteSide", 5.2, 5.35, -0.32, 0.32, 3.1, 7.0, M_BODY))
# moving contact arm: pivot A, closed contact on top of the fixed one, a tail left of the pivot rests on the latch
A = (-3.0, 6.2)
ARM = empty("ArmPivot", P(*A), BRK)
MCL = (FC[0] - A[0], (FC[1] + 0.5) - A[1])
TAIL = (-1.2, 0.95)
bm = bmesh.new(); add_bar(bm, (0, 0, 0), (MCL[0], 0, MCL[1]), 0.6); add_bar(bm, (0, 0, 0), (TAIL[0], 0, TAIL[1]), 0.5)
part(mesh_obj("Arm", bm, M_COPPER), ARM)
part(cyl("MovingContact", 0.40, 0.45, "Z", (MCL[0], 0.0, MCL[1] - 0.05), M_SILVER, seg=20), ARM)
part(box("ArmTab", TAIL[0] - 0.25, TAIL[0] + 0.25, -0.62, -0.2, TAIL[1] - 0.2, TAIL[1] + 0.25, M_STEEL), ARM)
part(cyl("ArmPin", 0.35, 0.9, "Y", (0, -0.1, 0), M_STEEL, seg=16), ARM)
bake_rot(ARM, lambda t: (0.0, arm_ang(t), 0.0))
def arm_pt(local, t):
    a = arm_ang(t); x, z = local
    return (A[0] + x * math.cos(a) + z * math.sin(a), A[1] - x * math.sin(a) + z * math.cos(a))
# handle (pivot H) out through the top + a link down to the arm
Hp = (-1.0, 11.6)
HND = empty("HandlePivot", P(*Hp), BRK)
part(rbox("HandleLever", -0.6, 0.6, -0.5, 0.5, 0.0, 4.5, 0.25, M_HANDLE), HND)
part(cyl("HandleHub", 1.2, 1.0, "Y", (0, 0, 0), M_HANDLE, seg=24), HND)
bake_rot(HND, lambda t: (0.0, handle_ang(t), 0.0))
# latch: vertical lever, pivot in the middle; top tip under the arm tail, bottom pushed by the bimetal / pulled by the plunger
PL = (-4.2, 5.5)
TAILW = arm_pt(TAIL, 0.0)
LAT = empty("LatchPivot", P(*PL), BRK)
part(box("LatchLever", -0.2, 0.2, -0.62, -0.3, -1.6, TAILW[1] - 0.2 - PL[1], M_STEEL), LAT)
part(cyl("LatchPin", 0.28, 0.7, "Y", (0, -0.45, 0), M_STEEL, seg=14), LAT)
bake_rot(LAT, lambda t: (0.0, latch_ang(t), 0.0))
def lat_bottom(t):
    a = latch_ang(t); return (PL[0] + (-1.6) * math.sin(a), PL[1] + (-1.6) * math.cos(a))
# spring: pulls the arm open (attached right of the pivot, anchored above)
SP_ANCH = (0.2, 10.2)
SP_ARM_L = (2.1, -1.0)
def helix_bm(L_=1.0, r=0.32, turns=9, wire=0.07):
    pts = [Vector((r * math.cos(2 * math.pi * turns * i / 180), r * math.sin(2 * math.pi * turns * i / 180), L_ * i / 180)) for i in range(181)]
    return sweep_bm(pts, [wire] * len(pts), seg=8)
SPRING = mesh_obj("Spring", helix_bm(), M_SPRING); par(SPRING, BRK)
def spring_xf(t):
    p0 = Vector(arm_pt(SP_ARM_L, t)); p1 = Vector(SP_ANCH)
    d = Vector((p1.x - p0.x, 0, p1.y - p0.y))
    return (p0.x, -0.05, p0.y), tuple(d.to_track_quat("Z", "Y").to_euler()), (1.0, 1.0, d.length)
_sx = [spring_xf(t) for t in TS]
for ax in range(3):
    bake(SPRING, "location", ax, [v[0][ax] for v in _sx]); bake(SPRING, "rotation_euler", ax, [v[1][ax] for v in _sx]); bake(SPRING, "scale", ax, [v[2][ax] for v in _sx])
L(cyl("SpringAnchor", 0.35, 0.7, "Y", P(*SP_ANCH), M_STEEL, seg=12))
# magnetic trip: horizontal coil right of the latch bottom; its plunger is pinned to the latch and gets yanked into the coil
CZ, CX0, CX1 = 3.9, -3.5, -1.3
CX = (CX0 + CX1) / 2
COIL = L(lathe("Coil", tube_prof(0.5, 0.95, CX0, CX1), M_COIL, a0=0.0, ang=2 * math.pi, seg=40, loc=(0, 0, 0)))
COIL.rotation_euler = (0, math.pi / 2, 0); COIL.location = (0, 0, CZ)        # lathe axis Z -> X
L(box("CoilFrame", CX0 - 0.1, CX1 + 0.1, 0.0, 0.35, CZ - 1.1, CZ + 1.1, M_STEEL))
PLUNG = L(cyl("Plunger", 0.34, 2.6, "X", (1.3, 0, 0), M_STEEL, seg=18))     # local x 0..2.6
bake_loc(PLUNG, lambda t: (lat_bottom(t)[0] + 0.15, -0.1, CZ))
RINGS = []
for k in range(2):
    o = L(torus(f"FieldRing{k}", 1.0, 0.06, M_RING, P(CX, CZ, -0.2))); o.rotation_euler = (math.pi / 2, 0, 0)
    bake_scale(o, lambda t, k=k: (1.4 * (1.0 + 0.6 * (((t - C["magnet"]) * 1.4 + k / 2) % 1.0)), 1.0 + 0.6 * (((t - C["magnet"]) * 1.4 + k / 2) % 1.0), 1.0))
    RINGS.append(o)
keyval(F_RING, [(0.0, 0.0), (C["magnet"] - 0.3, 0.0), (C["magnet"] - 0.1, 1.0), (C["yanks"] + 0.6, 1.0), (C["yanks"] + 1.0, 0.0)])
# bimetal strip: brass over steel, fixed at the bottom, tip bends right into the latch bottom
BIMP = (-5.4, 0.8)
BIM = empty("BimetalBase", P(*BIMP), BRK)
part(box("BimBrass", -0.36, 0.0, -0.4, 0.4, 0.0, 3.4, M_BIM1), BIM)
part(box("BimSteel", 0.0, 0.36, -0.4, 0.4, 0.0, 3.4, M_BIM2), BIM)
L(box("BimMount", -6.1, -4.9, -0.4, 0.4, 0.6, 1.0, M_COPPER))
bake_rot(BIM, lambda t: (0.0, bend_ang(t), 0.0))
# braids + load lug (house wire exits on the left)
for nm, pts in [("BraidArmCoil", [(A[0], -0.5, A[1]), (-1.0, -0.5, 5.6), (CX1 + 0.3, -0.5, CZ)]),
                ("BraidCoilBim", [(CX0 - 0.1, -0.5, CZ - 0.7), (-4.6, -0.5, 2.0), (BIMP[0] + 0.2, -0.5, 1.0)]),
                ("BraidBimLug", [(BIMP[0] - 0.3, -0.5, 3.9), (-6.0, -0.5, 7.0), (-5.0, -0.5, 11.2)])]:
    o, _ = tube(nm, pts, 0.16, M_COPPER, seg=8); L(o)
L(box("LoadLug", -6.2, -4.2, -0.45, 0.45, 11.0, 12.6, M_COPPER))
L(cyl("LugScrew", 0.45, 0.9, "Y", P(-5.2, 12.6), M_STEEL, seg=16))
HW_PTS = [(-5.6, 0.0, 11.8), (-8.0, 0.0, 11.8), (-11.0, 0.0, 10.5), (-16.0, 0.0, 9.0)]
o, _ = tube("HouseWire", HW_PTS, 0.32, M_COPPER, seg=12); L(o)
o, _ = tube("HouseWireJacket", HW_PTS[1:], 0.46, M_SHEATH, seg=12); L(o)
# current beads: line stab -> contacts -> arm -> coil -> bimetal -> lug -> house wire
CP = Path([P(4.5, -1.6, -0.7), P(4.5, 2.45, -0.7), P(FC[0], 2.45, -0.7), P(FC[0], 3.3, -0.7), P(A[0], A[1], -0.7), P(-1.0, 5.6, -0.7),
           P(CX1 + 0.3, CZ, -0.7), P(CX0, CZ, -1.15), P(-4.6, 2.0, -0.7), P(BIMP[0], 1.0, -0.7), P(BIMP[0], 3.9, -0.7), P(-6.0, 7.0, -0.7),
           P(-5.0, 11.2, -0.7), P(-8.0, 11.8, -0.7), P(-16.0, 9.0, -0.7)])
NORMAL_W = [(C["inside"] - 0.2, C["plug"]), (C["strip2"], T_TRIP1)]
SHORT_W = [(C["thousands"] - 0.1, T_TRIP2 + 0.1)]
bn = beads("Bead", CP, 34, 0.15, M_BEAD, NORMAL_W, speed=4.5)
for o in bn: par(o, BRK)
M_BEADH, B_BEADH = emit_mat("CurrentShort", WHITEHOT, 6.0)
bh = beads("BeadShort", CP, 60, 0.15, M_BEADH, SHORT_W, speed=16.0)
for o in bh: par(o, BRK)
# glows
glowc(B_BIM1, [(0.0, 0.0, GOLD), (C["strip"] - 0.05, 0.0, GOLD), (C["strip"] + 0.2, 1.4, GOLD), (C["metals"] + 0.3, 0.5, GOLD),
               (C["heats"] - 0.05, 0.5, HOT), (C["heats"] + 0.5, 2.5, HOT), (T_TRIP1 + 1.0, 2.0, HOT), (T_RESET1 - 0.05, 0.0, HOT), (T_HOLD, 0.0, HOT), (T_TRIP3, 2.0, HOT), (DUR, 0.5, HOT)])
glowc(B_BIM2, [(0.0, 0.0, GOLD), (C["two2"] - 0.05, 0.0, GOLD), (C["two2"] + 0.2, 1.2, GOLD), (C["metals"] + 0.3, 0.4, GOLD),
               (C["heats"] - 0.05, 0.4, HOT), (C["heats"] + 0.5, 2.2, HOT), (T_TRIP1 + 1.0, 1.8, HOT), (T_RESET1 - 0.05, 0.0, HOT), (T_HOLD, 0.0, HOT), (T_TRIP3, 1.8, HOT), (DUR, 0.4, HOT)])
glowc(B_STEEL, [(0.0, 0.0, GOLD), (C["latch"] - 0.1, 0.0, GOLD), (C["latch"] + 0.1, 0.6, GOLD), (C["spring"] + 0.3, 0.0, GOLD)])
glowc(B_SPRING, [(0.0, 0.0, GOLD), (C["spring"] - 0.1, 0.0, GOLD), (C["spring"] + 0.1, 2.0, GOLD), (C["apart"] + 0.3, 0.0, GOLD)])
glowc(B_SILVER, [(0.0, 0.0, GOLD), (T_TRIP1 - 0.02, 0.0, GOLD), (T_TRIP1 + 0.03, 6.0, GOLD), (T_TRIP1 + 0.4, 0.0, GOLD)])
glowc(B_COIL, [(0.0, 0.0, CYAN), (C["thousands"], 0.0, CYAN), (C["coil"] - 0.1, 0.4, CYAN), (C["coil"] + 0.2, 3.0, CYAN), (C["instantly"] + 0.5, 3.0, CYAN), (C["instantly"] + 1.2, 0.0, CYAN)])
glowc(B_HANDLE, [(0.0, 0.0, GOLD), (C["handle"] - 0.05, 0.0, GOLD), (C["handle"] + 0.15, 1.6, GOLD), (C["middle"] + 0.5, 1.2, GOLD), (C["push"] + 0.3, 0.6, GOLD), (C["cheat"], 0.0, GOLD)])
glowc(B_PLATE, [(0.0, 0.0, CYAN), (C["pushed"], 0.0, CYAN), (C["stack"] + 0.1, 1.2, CYAN), (C["kill"] + 0.4, 0.6, CYAN), (C["on"], 0.0, CYAN)])
# the arc: one bolt between the parting contacts, pushed into the chute, split into small arcs between the plates, then killed
def bolt_bm(n=10, amp=0.13, seed=1):
    rnd = random.Random(seed)
    pts = [Vector((rnd.uniform(-amp, amp) if 0 < i < n else 0.0, rnd.uniform(-amp, amp) * 0.5 if 0 < i < n else 0.0, i / n)) for i in range(n + 1)]
    return sweep_bm(pts, [0.06] * len(pts), seg=6)
ARC_T0, ARC_P, ARC_S, ARC_K = T_TRIP2 + 0.05, C["pushed"], C["split"], C["kill"]
BOLTS = []
for k in range(3):
    o = mesh_obj(f"ArcBolt{k}", bolt_bm(12, 0.18, 10 + k), M_ARC); par(o, BRK); BOLTS.append(o)
    def bxf(t, k=k):
        fc = Vector((FC[0], 0, FC[1] + 0.2)); mc = Vector(arm_pt((MCL[0], MCL[1] - 0.3), t)); mc = Vector((mc.x, 0, mc.y))
        u = ease((t - ARC_P) / (ARC_S - ARC_P))                       # slide into the chute along the runners
        p0 = fc.lerp(Vector((3.9, 0, PLATES_Z[0] - 0.3)), u); p1 = mc.lerp(Vector((3.9, 0, PLATES_Z[-1] + 0.3)), u)
        d = p1 - p0; ang = d.to_track_quat("Z", "Y").to_euler()
        jit = 0.04 * math.sin(t * 90 + k * 2.1)
        return (p0.x + jit, -0.05 + 0.02 * k, p0.z), tuple(ang), (1.0 + 0.3 * math.sin(t * 70 + k), 1.0, max(0.01, d.length))
    vv = [bxf(t) for t in TS]
    for ax in range(3):
        bake(o, "location", ax, [v[0][ax] for v in vv]); bake(o, "rotation_euler", ax, [v[1][ax] for v in vv]); bake(o, "scale", ax, [v[2][ax] for v in vv])
    windows(o, [(ARC_T0, ARC_S)])
SMALL = []
for k in range(len(PLATES_Z) - 1):
    o = mesh_obj(f"ArcSplit{k}", bolt_bm(5, 0.09, 30 + k), M_ARC); par(o, BRK)
    o.location = (3.9 + 0.1 * math.sin(k), -0.05, PLATES_Z[k] + 0.07); o.scale = (1, 1, 0.45 - 0.14)
    windows(o, [(ARC_S, ARC_K + 0.35 + 0.05 * k)]); SMALL.append(o)
glowc(B_ARC, [(0.0, 40.0, (0.75, 0.85, 1.0)), (ARC_S, 40.0, (0.75, 0.85, 1.0)), (ARC_K - 0.1, 22.0, (0.65, 0.78, 1.0)), (ARC_K + 0.5, 0.0, (0.5, 0.6, 1.0))])
# arc light
ARCL_d = bpy.data.lights.new("ArcLight", "POINT"); ARCL_d.color = (0.7, 0.82, 1.0); ARCL_d.shadow_soft_size = 0.5
ARCL = bpy.data.objects.new("ArcLight", ARCL_d); scene.collection.objects.link(ARCL); ARCL.location = (X0 + 2.8, -3.0, BZ + 4.6)
bake_scalar(ARCL_d, "energy", [0.0 if not (ARC_T0 <= t < ARC_K + 0.5) else 500.0 * (1 - 0.8 * lin((t - ARC_K) / 0.5)) * (0.75 + 0.25 * math.sin(t * 80)) for t in TS])
# hot gas puff out of the vents when the arc dies + contact sparks on the thermal trip
VEM = obj_from("VentEm", sphere_mesh("VentEmMe", 0.4, 1), None, (X0 + 6.4, 0.0, BZ + 4.8)); VEM.hide_render = True
pm_v = fx.particles(VEM, "dust", F(C["split"]), F(C["kill"] + 0.8), count=260)
try:
    ps_ = pm_v.particle_system.settings; ps_.particle_size = 0.22; ps_.normal_factor = 6.0; ps_.lifetime = 30; ps_.effector_weights.gravity = -0.02; ps_.brownian_factor = 1.2
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.6, 0.65, 0.75, 1); b_.inputs["Alpha"].default_value = 0.35
except Exception as e: print("[fx] vent puff tune skipped:", e)
SPK = obj_from("ContactSparkEm", sphere_mesh("ContactSparkMe", 0.2, 1), None, (X0 + FC[0], -0.6, BZ + FC[1] + 0.4)); SPK.hide_render = True
pm_c = fx.particles(SPK, "sparks", F(T_TRIP1), F(T_TRIP1 + 0.2), count=60)
try:
    ps_ = pm_c.particle_system.settings; ps_.particle_size = 0.05; ps_.normal_factor = 14.0; ps_.lifetime = 12; ps_.effector_weights.gravity = 0.4
except Exception as e: print("[fx] contact spark tune skipped:", e)
# trip-free beat: a gold block presses the handle ON
bmp = bmesh.new(); add_box(bmp, -1.0, 1.0, -0.8, 0.8, 0.0, 1.0)
PRESS = mesh_obj("HoldPress", bmp, M_PRESS); par(PRESS, BRK)
def press_xf(t):
    a = handle_ang(t); tip = Vector((Hp[0] + 4.6 * math.sin(a), 0, Hp[1] + 4.6 * math.cos(a)))
    drop_ = (1 - ease((t - T_HOLD + 0.3) / 0.3)) * 3.0
    return (tip.x + 0.4, -0.2, tip.z - 0.3 + drop_)
bake_loc(PRESS, press_xf); windows(PRESS, [(T_HOLD - 0.3, C["if"])])
# studio set
box("StudioFloorB", X0 - 200, X0 + 200, -200, 200, -2.0, 0.0, M_STUDIO)
box("BackdropB", X0 - 200, X0 + 200, 40, 42, -2, 150, M_BACK)
box("PlinthB", X0 - 9, X0 + 9, -5, 5, 0.0, BZ - 2.6, M_BODY)
fx.scatter(bpy.data.objects["StudioFloorB"], obj_from("Grit", sphere_mesh("GritMe", 0.12, 1), M_BODY), density=0.4, scale_min=0.4, scale_max=1.4, seed=3)

# =====================================================================
# SET A: living-room wall, cut open (x ~ 0). Wall y 0..10, room side y < 0, floor z 0
# =====================================================================
DRY_T = 1.3
WIN = (-40.0, 60.0, 60.0, 200.0)               # drywall cut window x0, x1, z0, z1
WX0, WX1, WZ0, WZ1 = WIN
def wall_piece(nm, x0, x1, z0, z1):
    bm = bmesh.new(); add_box(bm, x0, x1, -DRY_T, 0.0, z0, z1); o = mesh_obj(nm, bm, [M_PAINT, M_DRY])
    for f in o.data.polygons:
        c = f.center
        if abs(f.normal.y) < 0.5 and (abs(c.x - WX0) < 0.01 or abs(c.x - WX1) < 0.01 or abs(c.z - WZ0) < 0.01 or abs(c.z - WZ1) < 0.01): f.material_index = 1
    return o
wall_piece("DryL", -260, WX0, 0, 250); wall_piece("DryR", WX1, 260, 0, 250)
wall_piece("DryB", WX0, WX1, 0, WZ0); wall_piece("DryT", WX0, WX1, WZ1, 250)
box("DryBack", -260, 260, 8.9, 10.2, 0, 250, M_CAV)
for xs in (-80, -40, 0, 40, 80):
    box(f"Stud{xs}", xs - 1.9, xs + 1.9, 0.0, 8.9, 0, 250, M_WOOD)
box("PlateBottom", -260, 260, 0.0, 8.9, 0, 3.8, M_WOOD)
box("FloorA", -400, 400, -400, 0, -2, 0, M_FLOOR)
box("Baseboard", -260, 260, -2.6, -DRY_T, 0, 9, M_PLATEW)
RUG = box("Rug", -60, 120, -110, -20, 0.0, 0.6, M_RUG)
bmt = bmesh.new(); add_cyl(bmt, 0.35, 1.4, "Z", (0, 0, 0.7), seg=5, r2=0.05); TUFT = mesh_obj("Tuft", bmt, M_TUFT)
fx.scatter(RUG, TUFT, density=0.12, scale_min=0.5, scale_max=1.2, seed=11)
# the cable: panel -> through the studs -> down to the outlet
CAB_Z = 165.0
CAB_PTS = [(-62, 4.5, CAB_Z), (40, 4.5, CAB_Z), (50, 4.5, CAB_Z - 2), (52, 4.5, CAB_Z - 12), (52, 4.5, 44)]
CABLE, CAB_SM = tube("Cable", CAB_PTS, 0.95, M_SHEATH, seg=14)
SPOT = Vector((14.0, 4.5, CAB_Z))                  # where it overheats / where the nail goes in
SCORCH = cyl("ScorchBand", 1.0, 7.0, "X", tuple(SPOT), M_SCORCH, seg=14)
windows(SCORCH, [(C["wire2"] + 1.2, C["which"])])
box("OutletBox", 48.5, 55.5, 0.0, 6.5, 30, 42, M_PANEL)
box("OutletPlate", 48.0, 56.0, -DRY_T - 0.3, -DRY_T, 29, 43, M_PLATEW)
# panel: recessed steel box with the door open, 2 columns x 7 breakers
PX0, PX1, PZ0, PZ1 = -100.0, -64.0, 115.0, 195.0
box("PanelBack", PX0, PX1, 7.0, 8.0, PZ0, PZ1, M_PIN)
for nm, a, b, c, d in [("PanL", PX0 - 1, PX0, PZ0, PZ1), ("PanR", PX1, PX1 + 1, PZ0, PZ1)]: box(nm, a, b, -DRY_T - 0.4, 8.0, c, d, M_PANEL)
for nm, c, d in [("PanB", PZ0 - 1, PZ0), ("PanT", PZ1, PZ1 + 1)]: box(nm, PX0 - 1, PX1 + 1, -DRY_T - 0.4, 8.0, c, d, M_PANEL)
DOOR = empty("DoorHinge", (PX0 - 1, -DRY_T - 0.4, PZ0))
part(box("PanelDoor", 0.0, PX1 - PX0 + 2, -0.5, 0.0, 0.0, PZ1 - PZ0 + 1, M_PANEL), DOOR); DOOR.rotation_euler = (0, 0, math.radians(-115))
box("DeadFront", PX0, PX1, -DRY_T - 0.3, -DRY_T, PZ0, PZ1, M_PANEL)
BR_ROWS = [PZ1 - 12 - 8.2 * i for i in range(7)]
BR_CX = (-87.0, -77.0)
TARGET = (1, 2)                                    # right column, third row
PB_H = {}
for ci, cx in enumerate(BR_CX):
    for ri, zz in enumerate(BR_ROWS):
        if (ci, ri) == TARGET: continue
        box(f"PBrk{ci}{ri}", cx - 4.5, cx + 4.5, -DRY_T - 1.2, -DRY_T, zz - 3.6, zz + 3.6, M_BRK)
        box(f"PBrkH{ci}{ri}", cx - 0.8, cx + 0.8, -DRY_T - 3.0, -DRY_T - 1.2, zz - 1.8, zz + 1.8, M_BRK)
TX, TZ = BR_CX[TARGET[0]], BR_ROWS[TARGET[1]]
# target breaker: body (rigid body falls out on "swap"), its handle trips on the hook, again on "keeps"
TB = box("TargetBreaker", -4.5, 4.5, -2.6, 0.0, -3.6, 3.6, M_BRKH); TB.location = (TX, -DRY_T + 1.4, TZ)
TBH_P = empty("TargetHandlePivot", (0, -2.6, 0), TB)
part(box("TargetHandle", -0.8, 0.8, -1.9, 0.0, -1.8, 1.8, M_BRKH), TBH_P)
def tb_handle(t):
    if t < C["keeps"]: return math.radians(-20)
    k = (t - C["keeps"]) % 0.9
    return math.radians(-20) + math.radians(20) * (ease(k / 0.12) if k < 0.5 else 1 - ease((k - 0.5) / 0.2))
bake_rot(TBH_P, lambda t: (0.0, 0.0, tb_handle(t)))
T_PULL = C["swap"] - 0.35
bake_loc(TB, lambda t: (TX, -DRY_T + 1.4 - 7.0 * ease((t - T_PULL) / 0.35), TZ))
TB_FLOOR = box("FloorRB", -150, 50, -150, 0, -4.0, 0.0, None); TB_FLOOR.hide_render = True; TB_FLOOR.display_type = "WIRE"
fx.rigid([TB], passive=[TB_FLOOR], mass=0.3, friction=0.6, bounce=0.25)
try:
    TB.rigid_body.kinematic = True; TB.rigid_body.keyframe_insert("kinematic", frame=F(C["swap"]))
    TB.rigid_body.kinematic = False; TB.rigid_body.keyframe_insert("kinematic", frame=F(C["swap"]) + 1)
except Exception as e: print("target kinematic key skipped", e)
glowc(B_BRKH, [(0.0, 0.0, GOLD), (C["every"] - 0.05, 0.0, GOLD), (C["every"] + 0.2, 0.5, GOLD), (C["inside"], 0.0, GOLD), (C["if"], 0.0, GOLD), (C["keeps"], 0.6, RED), (C["swap"] + 0.6, 0.0, RED)])
BIG = box("BiggerBreaker", -4.5, 4.5, -2.6, 0.0, -3.6, 3.6, M_BIG)
part(box("BiggerHandle", -0.8, 0.8, -4.5, -2.6, -1.8, 1.8, M_BIG), BIG)
bake_loc(BIG, lambda t: (TX, -DRY_T + 1.4 - 9.0 * (1 - ease((t - C["bigger"]) / 0.4)), TZ))
windows(BIG, [(C["bigger"], C["which"])])
glowc(B_BIG, [(0.0, 0.0, RED), (C["bigger"], 0.0, RED), (C["bigger"] + 0.3, 0.7, RED), (C["wire2"], 0.3, RED)])
glowc(B_PANEL, [(0.0, 0.0, GOLD), (C["which"] - 0.05, 0.0, GOLD), (C["which"] + 0.4, 0.5, GOLD), (DUR, 0.5, GOLD)])
# TV on a console (hook), heater + hair dryer on the rug, cords to the outlet
box("ConsoleA", 95, 215, -55, -10, 0, 52, M_CONSOLE)
box("TVStand", 148, 162, -36, -24, 52, 56, M_TV)
box("TVNeck", 153, 157, -32, -29, 56, 64, M_TV)
box("TVBody", 110, 200, -33, -29, 62, 114, M_TV)
SCREEN = box("TVScreen", 111.5, 198.5, -33.15, -33.0, 63.5, 112.5, M_SCREEN)
glowc(B_SCREEN, [(0.0, 0.7, (0.25, 0.55, 1.0)), (C["tv"] - 0.1, 0.7, (0.25, 0.55, 1.0)), (C["tv"] + 0.05, 0.0, (0.25, 0.55, 1.0)), (C["tv"] + 0.25, 0.7, (0.4, 0.6, 1.0)), (DUR, 0.7, (0.4, 0.6, 1.0))])
HEAT = rbox("HeaterBody", 0, 34, -78, -58, 0.6, 52, 3.0, M_PLASTIC)
GR = box("HeaterGrill", 3, 31, -78.5, -78.0, 6, 46, M_GRILL)
glowc(B_GRILL, [(0.0, 0.0, HOT), (C["heater"] - 0.1, 0.0, HOT), (C["heater"] + 0.4, 3.0, HOT), (C["power"] - 0.05, 3.0, HOT), (C["power"] + 0.35, 0.0, HOT),
                (C["if"], 0.0, HOT), (C["keeps"] + 0.2, 3.0, HOT), (DUR, 3.0, HOT)])
DRY = empty("HairDryer", (84, -50, 0.6))
part(rbox("DryerBarrel", -11, 9, -3.5, 3.5, 10.0, 17.0, 3.0, M_DRYER), DRY)
part(rbox("DryerGrip", -5, 0, -2.4, 2.4, 0.0, 11.0, 1.8, M_DRYER), DRY)
part(cyl("DryerNozzle", 2.6, 4.0, "X", (11, 0, 13.5), M_CORD, seg=18), DRY)
DRY.rotation_euler = (0, 0, math.radians(-30))
glowc(B_DRYER, [(0.0, 0.0, ORANGE), (C["dryer"] - 0.1, 0.0, ORANGE), (C["dryer"] + 0.3, 0.8, ORANGE), (C["power"], 0.8, ORANGE), (C["power"] + 0.3, 0.0, ORANGE)])
for nm, pts in [("CordHeater", [(17, -58, 8), (20, -40, 1.2), (45, -12, 1.2), (50, -3.5, 33)]),
                ("CordDryer", [(80, -48, 3), (66, -30, 1.2), (55, -10, 1.2), (54, -3.5, 38)])]:
    tube(nm, pts, 0.45, M_CORD, seg=8)
# cable glow: gold trace on "wires", red-hot on "fire", warm with the overload, red when it cooks
glowc(B_SHEATH, [(0.0, 0.0, GOLD), (C["wires"] - 0.1, 0.0, GOLD), (C["wires"] + 0.3, 1.6, GOLD), (C["catching"] - 0.1, 1.6, GOLD), (C["fire"], 4.0, HOT),
                 (C["every"], 4.0, HOT), (C["every"] + 0.3, 0.0, HOT), (C["climbs"] - 0.6, 0.0, ORANGE), (C["climbs"] + 0.2, 1.6, ORANGE), (C["strip2"], 1.6, ORANGE),
                 (C["strip2"] + 0.1, 0.0, ORANGE), (C["wire2"], 0.0, HOT), (C["cook"], 4.5, HOT), (C["which"], 4.5, HOT), (C["which"] + 0.6, 0.0, HOT)])
# overload beads inside the cable (house side)
CABP = Path([tuple(v) for v in CAB_SM])
cb = beads("CabBead", CABP, 26, 0.5, M_BEAD, [(C["plug"], C["strip2"]), (C["keeps"], C["which"])], speed=60.0)
# fire stake: flames licking at the hot spot + smoke; the cook beat: smoke + melted insulation dripping (Mantaflow)
FLAMES = []
for k in range(4):
    bmf = bmesh.new(); add_cyl(bmf, 1.2, 4.5, "Z", (0, 0, 2.25), seg=10, r2=0.05)
    o = mesh_obj(f"Flame{k}", bmf, M_FLAME); o.location = (SPOT.x - 3 + 2 * k, 3.2, CAB_Z + 0.4)
    bake_scale(o, lambda t, k=k: (1.0, 1.0, 0.6 + 0.45 * abs(math.sin(t * 9 + k * 1.7)) + 0.2 * math.sin(t * 23 + k)))
    windows(o, [(C["catching"], C["every"])]); FLAMES.append(o)
glowc(B_FLAME, [(0.0, 0.0, ORANGE), (C["catching"], 0.0, ORANGE), (C["fire"], 6.0, ORANGE), (C["every"], 6.0, ORANGE)])
SMK = obj_from("SmokeEm", sphere_mesh("SmokeEmMe", 1.0, 1), None, tuple(SPOT + Vector((0, -1.0, 1.0)))); SMK.hide_render = True
for t0, t1 in [(C["catching"], C["every"]), (C["cook"] - 0.6, C["which"] + 0.3)]:
    pm_s = fx.particles(SMK, "dust", F(t0), F(t1), count=300)
    try:
        ps_ = pm_s.particle_system.settings; ps_.particle_size = 1.6; ps_.size_random = 0.7; ps_.normal_factor = 5.0; ps_.lifetime = 50
        ps_.effector_weights.gravity = -0.03; ps_.brownian_factor = 2.0
        b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
        b_.inputs["Base Color"].default_value = (0.18, 0.18, 0.19, 1); b_.inputs["Alpha"].default_value = 0.45; b_.inputs["Emission Strength"].default_value = 0.0
    except Exception as e: print("[fx] smoke tune skipped:", e)
# short circuit: a picture nail driven through the cable, hot touches neutral: flash + sparks
NAIL = empty("Nail", (SPOT.x, -DRY_T, CAB_Z))
part(cyl("NailHead", 0.75, 0.25, "Y", (0, -0.12, 0), M_NAIL, seg=16), NAIL)
part(cyl("NailShank", 0.17, 7.0, "Y", (0, 3.5, 0), M_NAIL, seg=10), NAIL)
bake_loc(NAIL, lambda t: (SPOT.x, -DRY_T - 7.5 * (1 - ease((t - C["short"]) / (C["touches"] - C["short"]))), CAB_Z))
windows(NAIL, [(C["short"] - 0.1, C["thousands"])])
FLASH = sphere_mesh("FlashMe", 0.9, 2); FLO = obj_from("ShortFlash", FLASH, M_FLASH, tuple(SPOT + Vector((0, -0.8, 0))))
windows(FLO, [(C["touches"] + 0.1, C["thousands"])])
glowc(B_FLASH, [(0.0, 0.0, WHITEHOT), (C["touches"] + 0.1, 0.0, WHITEHOT), (C["touches"] + 0.2, 14.0, WHITEHOT), (C["ground"], 4.0, WHITEHOT), (C["thousands"], 0.0, WHITEHOT)])
SSP = obj_from("ShortSparkEm", sphere_mesh("ShortSparkMe", 0.8, 1), None, tuple(SPOT + Vector((0, -1.0, 0)))); SSP.hide_render = True
pm_ss = fx.particles(SSP, "sparks", F(C["touches"] + 0.15), F(C["ground"] + 0.4), count=160)
try:
    ps_ = pm_ss.particle_system.settings; ps_.particle_size = 0.12; ps_.normal_factor = 60.0; ps_.lifetime = 14; ps_.effector_weights.gravity = 0.6
except Exception as e: print("[fx] short spark tune skipped:", e)
FLL_d = bpy.data.lights.new("ShortLight", "POINT"); FLL_d.color = (0.8, 0.88, 1.0); FLL_d.shadow_soft_size = 1.0
FLL = bpy.data.objects.new("ShortLight", FLL_d); scene.collection.objects.link(FLL); FLL.location = tuple(SPOT + Vector((0, -6, 2)))
bake_scalar(FLL_d, "energy", [0.0 if not (C["touches"] + 0.1 <= t < C["thousands"]) else 3.0e3 * max(0.1, 1 - (t - C["touches"]) / 1.2) * (0.7 + 0.3 * math.sin(t * 60)) for t in TS])
FIREL_d = bpy.data.lights.new("FireLight", "POINT"); FIREL_d.color = (1.0, 0.5, 0.15); FIREL_d.shadow_soft_size = 2.0
FIREL = bpy.data.objects.new("FireLight", FIREL_d); scene.collection.objects.link(FIREL); FIREL.location = tuple(SPOT + Vector((0, -5, 4)))
bake_scalar(FIREL_d, "energy", [(1.5e3 * (0.8 + 0.2 * math.sin(t * 17)) if C["fire"] - 0.3 <= t < C["every"] else (6.0e2 * ease((t - C["cook"]) / 0.8) if C["cook"] - 0.2 <= t < C["which"] + 0.5 else 0.0)) for t in TS])
# Mantaflow: melted insulation dripping off the cooking cable (laptop --bake-fluid; hidden without the cache)
FL_DOM = box("FluidDomain", SPOT.x - 5, SPOT.x + 5, 1.0, 8.0, CAB_Z - 14, CAB_Z + 1.5, None); FL_DOM.display_type = "WIRE"
FL_IN = obj_from("FluidInflow", sphere_mesh("FluidInMe", 0.5, 2), None, tuple(SPOT + Vector((0, 0, -0.9)))); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
fx.fluid_domain(FL_DOM, FL_IN, eff=[], res=48, start=F(C["cook"]), end=F(C["cook"] + 2.5), cache_dir=os.path.join(HERE, "cache_fluid"))
M_MELT, B_MELT = mat("MeltedPlastic", (0.12, 0.08, 0.05), rough=0.2, emit_rgb=HOT); B_MELT.inputs["Emission Strength"].default_value = 1.2
FL_DOM.data.materials.append(M_MELT)
windows(FL_DOM, [(C["cook"], C["which"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True

# ================= lights + world =================
fx.hdri("interior", strength=0.25, rotation_deg=60.0, show_background=False)
fx.glare(threshold=1.0, strength=0.55, size=7)
def area(name, loc, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; return o, d_
def aim(o, target):
    d = Vector(target) - o.location; o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
for nm, loc, tgt, size, en, rgb in [
        ("KeyA", (60, -220, 230), (0, 0, 120), 150, 3.5e4, (1.0, 0.92, 0.82)), ("FillA", (-180, -160, 140), (0, 0, 100), 150, 1.0e4, (0.75, 0.82, 1.0)),
        ("CavityA", (10, -60, 200), (10, 4, 165), 40, 2.5e3, (1.0, 0.95, 0.9)), ("PanelA", (-60, -60, 170), (-82, 0, 155), 40, 2.0e3, (1.0, 0.95, 0.9)),
        ("KeyB", (X0 - 25, -40, BZ + 25), (X0, 0, BZ + 7), 25, 4.5e3, (1.0, 0.95, 0.9)), ("RimB", (X0 + 30, 25, BZ + 20), (X0, 0, BZ + 7), 25, 3.0e3, (0.6, 0.75, 1.0)),
        ("LowB", (X0 + 10, -30, BZ - 8), (X0, 0, BZ + 4), 20, 1.2e3, (1.0, 0.9, 0.8))]:
    o, _ = area(nm, loc, size, en, rgb); aim(o, tgt)

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 4000
def cB(dx, dy, dz): return (X0 + dx, dy, BZ + dz)
SP = tuple(SPOT)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (175, -215, 105), (150, -31, 82), 30),                                   # hook: the TV, slow push-in
    (C["its"] - 0.05, (165, -185, 100), (152, -31, 84), 32),
    (C["its"], (40, -95, 175), (10, 4, 165), 30, "cut"),                           # wall cut open: the cable glows gold
    (C["catching"], (22, -34, 171), (13, 4, 165), 35),
    (C["us"], (21, -32, 171), (13, 4, 165), 35),
    (C["us"] + 0.01, (10, -170, 150), (5, 0, 145), 30, "cut"),                     # pull-out for the counter: the wall still burning
    (C["every"] - 0.05, (5, -190, 148), (5, 0, 140), 30),
    (C["every"], (-60, -55, 162), (-82, 0, 157), 32, "cut"),                       # the panel, target breaker glows
    (C["inside"] - 0.05, (-66, -45, 160), (-82, 0, 157), 34),
    (C["inside"], cB(10, -34, 12), cB(0.0, 0, 6.5), 35, "cut"),                    # the breaker cut in half, current flowing
    (C["strip"], cB(4, -26, 8), cB(-3.0, 0, 5.0), 40),
    (C["plug"] - 0.05, cB(3, -24, 7.5), cB(-3.5, 0, 4.5), 42),
    (C["plug"], (50, -255, 70), (44, -30, 66), 32, "cut"),                         # house: heater + hair dryer on one circuit
    (C["climbs"], (47, -240, 74), (42, -30, 70), 32),
    (C["strip2"] - 0.05, (46, -236, 75), (42, -30, 71), 32),
    (C["strip2"], cB(-2.0, -15, 4.5), cB(-4.8, 0, 3.0), 45, "cut"),                # bimetal close-up: heats, bends
    (C["once"] - 0.05, cB(-2.4, -14, 4.5), cB(-4.8, 0, 3.2), 45),
    (C["once"], cB(3, -24, 8), cB(-1.2, 0, 5.2), 40, "cut"),                       # latch, spring, contacts snap apart
    (C["snaps"], cB(4, -22, 7.0), cB(-0.5, 0, 5.0), 42),
    (C["power"] - 0.05, cB(4.5, -23, 7.0), cB(-0.5, 0, 5.0), 42),
    (C["power"], (55, -140, 55), (25, -60, 30), 30, "cut"),                        # the heater goes dark
    (C["second"] - 0.05, (52, -130, 55), (25, -60, 30), 30),
    (C["second"], (32, -60, 172), (14, 2, 165), 34, "cut"),                        # short circuit: a nail through the cable
    (C["touches"], (24, -30, 168), (14, 2, 165), 40),
    (C["thousands"] - 0.05, (23, -28, 168), (14, 2, 165), 40),
    (C["thousands"], cB(8, -30, 10), cB(0.0, 0, 6.0), 36, "cut"),                  # white-hot current rush, coil, plunger
    (C["coil"], cB(0, -18, 6), cB(-2.8, 0, 4.6), 42),
    (C["instantly"] - 0.3, cB(0.5, -20, 6.5), cB(-2.0, 0, 4.8), 42),
    (C["instantly"] - 0.29, cB(8, -17, 6.5), cB(2.6, 0, 4.8), 42, "cut"),          # contacts part: the arc
    (C["pushed"], cB(8, -15, 6.5), cB(3.0, 0, 5.0), 45),
    (C["kill"] + 0.5, cB(9, -17, 7.0), cB(3.0, 0, 5.0), 45),
    (C["on"], cB(-16, -30, 14), cB(0.0, 0, 8.5), 38, "cut"),                       # exterior: handle in the middle, off, on
    (C["push"], cB(-10, -26, 18), cB(-1.0, 0, 11), 40),
    (C["cheat"] - 0.05, cB(-8, -25, 18), cB(-1.0, 0, 11), 40),
    (C["cheat"], cB(6, -30, 13), cB(-0.5, 0, 8.0), 36, "cut"),                     # trip-free: handle held ON, contacts open anyway
    (C["if"] - 0.05, cB(5, -27, 11), cB(0.0, 0, 7.0), 38),
    (C["if"], (-55, -60, 160), (-80, 0, 150), 32, "cut"),                          # panel: it keeps tripping, swapped for a bigger one
    (C["bigger"], (-58, -75, 150), (-78, -10, 140), 30),
    (C["wire2"] - 0.05, (-58, -78, 150), (-78, -10, 140), 30),
    (C["wire2"], (36, -58, 172), (14, 3, 163), 34, "cut"),                         # the same wire cooks
    (C["which"] - 0.05, (26, -40, 168), (14, 3, 163), 38),
    (C["which"], (-62, -72, 160), (-82, 0, 155), 30, "cut"),                       # CTA: the panel, pull-out
    (DUR, (-50, -135, 152), (-75, 0, 148), 30),
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
bake_scalar(cam_d, "dof.aperture_fstop", [max(5.6, min(22.0, 0.6 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 6; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0, min(6.0e3, 0.10 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (2, 3, 0)
for o_ in scene.objects:
    if o_.type == "LIGHT":
        try: o_.visible_camera = False
        except Exception: pass
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
scene.view_settings.exposure = float(arg("--exposure", "-0.2"))
prefs.keyframe_new_interpolation_type = "BEZIER"

# ================= simulations =================
fx.bake_rigid(F(C["swap"]) - 2, F(C["wire2"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "tv": (155.0, -33.5, 88.0), "cable": tuple(SPOT + Vector((0, -0.8, 0.7))), "panel": (-82.0, -2.0, 157.0), "target": W(TB, (0, -4.5, 0)),
    "heater": (17.0, -70.0, 54.0), "dryer": W(DRY, (0, 0, 18)), "nail": W(NAIL, (0, -0.2, 0)), "bigger": W(BIG, (0, -4.6, 0)),
    "strip": W(BIM, (0, -0.4, 3.2)), "latch": W(LAT, (0, -0.65, 1.0)), "spring": W(SPRING, (0, 0, 0.5)), "contacts": W(BRK, (FC[0], -0.5, FC[1] + 0.3)),
    "coil": W(BRK, (CX, -0.5, CZ + 0.9)), "plunger": W(PLUNG, (0.4, -0.4, 0)), "chute": W(BRK, (3.9, -0.4, 5.0)), "handle": W(HND, (0, -0.55, 3.9)),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
flicks = []
t_ = C["keeps"]
while t_ < C["swap"] - 0.35: flicks.append(round(t_, 3)); t_ += 0.9
events = {"cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4], "tv_off": round(C["tv"], 3), "fire": RR(C["catching"], C["every"]),
          "trip_thermal": round(T_TRIP1, 3), "trip_magnetic": round(T_TRIP2, 3), "trip_free": round(T_TRIP3, 3), "latch1": round(T_TRIP1 - 0.45, 3),
          "plunger": round(C["yanks"], 3), "arc": RR(ARC_T0, ARC_K + 0.5), "arc_split": round(ARC_S, 3), "arc_kill": round(ARC_K, 3),
          "handle_off": round(C["off"], 3), "handle_on": round(C["on2"], 3), "press": round(T_HOLD, 3), "nail": RR(C["short"], C["touches"]),
          "flash": round(C["touches"] + 0.15, 3), "heater_on": round(C["heater"], 3), "dryer_on": round(C["dryer"], 3), "heater_off": round(C["power"], 3),
          "flicks": flicks, "pull": round(T_PULL, 3), "drop": round(C["swap"], 3), "bigger_in": round(C["bigger"], 3), "cook": RR(C["cook"] - 0.6, C["which"]),
          "beads_normal": [RR(a, b) for a, b in NORMAL_W], "beads_short": [RR(a, b) for a, b in SHORT_W]}
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
    r.filepath = os.path.join(out, f"f_"); bpy.ops.render.render(animation=True)
