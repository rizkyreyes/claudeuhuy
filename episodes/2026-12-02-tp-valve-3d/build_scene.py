# T&P relief valve (3d-44a): "This little brass valve is all that stops your water heater from turning into a rocket."
# Stake: capped or stuck -> the tank can blast through the roof (what-if, red). Inside the tank: water heated under pressure, the thermostat
# cuts the heat at the set temperature; if it fails the heat keeps climbing, hot water expands, pressure climbs, water passes 212 F without
# boiling (superheated); if the tank splits it flashes to steam, over 1,000x bigger (droplet -> 10x scale = 1,000x volume). The valve
# watches both: a probe in the top 6 in of the tank, thermal element expands at ~210 F and lifts the disc off its seat; a spring holds the
# same disc shut until ~150 psi, then the water shoves it open. Discharge pipe ends near the floor; yearly test lever; never cap it.
# Illustrative, 1 unit = 1 cm: generic tank water heater (gas burner + flue), generic T&P valve (no brand, no text, no logo). No people.
# Section plane y = 0 (keep y >= 0, orange cut faces); the camera looks from -y. Valve parts enlarged x1.0 but drawn simple.
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
random.seed(44)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("this","This"),("brass","brass"),("valve","valve"),("water","water"),("heater","heater"),("rocket","rocket."),("if","If"),
  ("capped","capped"),("stuck","stuck,"),("tank","tank"),("blast","blast"),("roof","roof."),("inside","Inside"),("tank2","tank,"),
  ("heats","heats"),("pressure","pressure."),("normally","Normally"),("thermostat","thermostat"),("cuts","cuts"),("set","set."),
  ("but","But"),("thermostat2","thermostat"),("fails","fails,"),("keeps","keeps"),("climbing","climbing."),("hot","Hot"),
  ("expands","expands,"),("pressure2","pressure"),("climbs","climbs"),("under","Under"),("hotter","hotter"),("two","two"),
  ("twelve","twelve"),("boil","boil."),("thats","That's"),("superheated","superheated"),("if2","If"),("splits","splits,"),
  ("flashes","flashes"),("steam","steam,"),("thousand","thousand"),("bigger","bigger,"),("all","all"),("once","once."),("so","So"),
  ("valve2","valve"),("watches","watches"),("both","both."),("probe","probe"),("top","top"),("six","six"),("inches","inches"),
  ("hottest","hottest."),("at","At"),("two2","two"),("ten","ten"),("degrees","degrees,"),("element","element"),("expands2","expands"),
  ("lifts","lifts"),("disc","disc"),("seat","seat."),("hot2","Hot"),("rushes","rushes"),("out","out"),("superheat","superheat."),
  ("spring","spring"),("holds","holds"),("shut","shut,"),("pressure3","pressure"),("hits","hits"),("one","one"),("fifty","fifty"),
  ("psi","psi."),("then","Then"),("shoves","shoves"),("open","open."),("either","Either"),("drains","drains"),("pipe","pipe"),
  ("floor","floor."),("once2","Once"),("year","year,"),("lift","lift"),("test","test"),("lever","lever,"),("gush","gush"),
  ("never","Never"),("cap","cap"),("pipe2","pipe,"),("drips","drips."),("drip","drip"),("wrong","wrong,"),("plumber","plumber."),
  ("have","Have"),("tested","tested"),("tell","Tell"),("comments","comments.")]
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
CL = coll("TPValve")
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
VZ = 133.0                                   # T&P valve axis height (top 6 in of a tank whose water ends at z 141.4)
X_ST = 600.0                                 # steam demo set (droplet -> 10x radius = 1,000x volume)
# ---------- beat windows ----------
T_HOOK = (0.0, C["if"]); T_STAKE = (C["if"], C["inside"]); T_IN = (C["inside"], C["but"]); T_FAIL = (C["but"], C["under"])
T_SUPER = (C["under"], C["if2"]); T_STEAM = (C["if2"], C["so"]); T_PROBE = (C["so"], C["at"]); T_TEMP = (C["at"], C["spring"])
T_PRESS = (C["spring"], C["either"]); T_DRAIN = (C["either"], C["once2"]); T_TEST = (C["once2"], C["never"]); T_CAP = (C["never"], C["have"])
T_CTA = (C["have"], DUR)
FULLW = [(0.0, C["inside"])]                 # whole heater (hook, stake, rocket what-if)
SECW = [(C["inside"], DUR)]                  # section heater
T_L = C["blast"]; ACC = 800.0               # launch, cm/s^2
T_H = T_L + math.sqrt(2 * 90.0 / ACC)        # tank top (z 150) reaches the ceiling (z 240)

# ---------- materials ----------
M_SEC, B_SEC = mat("CutFace", (0.90, 0.38, 0.06), rough=0.5, emit_rgb=(1.0, 0.40, 0.08)); B_SEC.inputs["Emission Strength"].default_value = 0.12
M_JACKET, B_JACKET = mat("Jacket", (0.80, 0.80, 0.78), rough=0.35, emit_rgb=(1.0, 0.3, 0.24))
M_FOAM, _ = mat("Foam", (0.92, 0.78, 0.30), rough=0.8, noise=25)
M_TANK, B_TANK = mat("TankSteel", (0.30, 0.31, 0.33), rough=0.4, metallic=1.0, emit_rgb=(1.0, 0.3, 0.24))
M_GLASS, _ = mat("GlassLining", (0.10, 0.22, 0.30), rough=0.2)
M_FLUE, _ = mat("Flue", (0.12, 0.12, 0.13), rough=0.5, metallic=1.0)
M_BRASS, B_BRASS = mat("Brass", (0.85, 0.62, 0.22), rough=0.25, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_BRF, B_BRF = mat("BrassFull", (0.85, 0.62, 0.22), rough=0.25, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_DISC, B_DISC = mat("Disc", (0.15, 0.15, 0.16), rough=0.5, emit_rgb=(0.30, 0.92, 1.0))
M_SPRING, B_SPRING = mat("Spring", (0.70, 0.71, 0.74), rough=0.25, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_STEM, _ = mat("Stem", (0.75, 0.76, 0.78), rough=0.25, metallic=1.0)
M_PROBE, B_PROBE = mat("Probe", (0.72, 0.42, 0.20), rough=0.3, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_ELEM, B_ELEM = mat("Element", (0.80, 0.45, 0.22), rough=0.3, metallic=1.0, emit_rgb=(1.0, 0.45, 0.15))
M_LEVER, B_LEVER = mat("Lever", (0.85, 0.62, 0.22), rough=0.3, metallic=1.0, emit_rgb=(0.98, 0.74, 0.27))
M_COPPER, _ = mat("Copper", (0.80, 0.42, 0.25), rough=0.3, metallic=1.0)
M_PIPE, B_PIPE = mat("DischargePipe", (0.88, 0.86, 0.80), rough=0.35, emit_rgb=(0.98, 0.74, 0.27))
M_THERMO, B_THERMO = mat("Thermostat", (0.08, 0.08, 0.09), rough=0.4, emit_rgb=(0.98, 0.74, 0.27))
M_DIAL, _ = mat("Dial", (0.75, 0.10, 0.08), rough=0.4)
M_BURNER, _ = mat("Burner", (0.25, 0.25, 0.26), rough=0.5, metallic=1.0)
M_FLAME, B_FLAME = emit_mat("Flame", (0.35, 0.55, 1.0), 6.0)
M_FLAMET, B_FLAMET = emit_mat("FlameTip", (1.0, 0.55, 0.15), 3.0)
M_CAP, B_CAP = mat("RedCap", (0.75, 0.06, 0.05), rough=0.4, emit_rgb=(1.0, 0.3, 0.24))
M_ARROW, B_ARROW = emit_mat("PressArrow", (1.0, 0.30, 0.24), 3.0)
M_CRACK, B_CRACK = emit_mat("Crack", (1.0, 0.30, 0.24), 0.0)
M_BAND, B_BAND = emit_mat("TopBand", (0.30, 0.92, 1.0), 0.0)
M_FLOOR, _ = mat("Concrete", (0.32, 0.31, 0.30), rough=0.85, noise=4)
WALL_M, _ = mat("Wall", (0.10, 0.115, 0.14), rough=0.8)
M_CEIL, _ = mat("Ceiling", (0.55, 0.52, 0.48), rough=0.8, noise=3)
M_DRAIN, _ = mat("DrainGrate", (0.15, 0.15, 0.16), rough=0.4, metallic=1.0)
M_SED, _ = mat("Sediment", (0.55, 0.50, 0.40), rough=0.9)
M_HOTB, B_HOTB = emit_mat("BeadHot", (1.0, 0.45, 0.15), 4.0)
M_STREAM, B_STREAM = emit_mat("Stream", (1.0, 0.55, 0.25), 1.5)
M_DROP, B_DROP = water_sec("Droplet")[:2]
B_DROP.inputs["Emission Strength"].default_value = 0.4
M_STEAMG, F_STEAMG = ghost("SteamGhost", (0.92, 0.95, 1.0))
M_HOTG, F_HOTG = ghost("HotTopGhost", (1.0, 0.45, 0.12))
M_REF, F_REF = ghost("DropRef", (0.30, 0.92, 1.0))
M_WATER, B_WATER, VA_WATER = water_sec("TankWater", vol_rgb=(0.16, 0.46, 0.62), dens=0.012)

def glowc(bsdf, keys):
    """[(t, strength, rgb)] keys on emission strength + colour."""
    s_in, c_in = bsdf.inputs["Emission Strength"], bsdf.inputs["Emission Color"]
    for t, s, rgb in keys:
        s_in.default_value = s; s_in.keyframe_insert("default_value", frame=F(t))
        c_in.default_value = (*rgb, 1); c_in.keyframe_insert("default_value", frame=F(t))
GOLD, CYAN, RED, ORANGE = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.15)

def mark_caps(o, y_cut=0.0, eps=1e-3):
    me = o.data
    if len(me.materials) < 2: me.materials.append(M_SEC)
    for p in me.polygons:
        if all(abs(me.vertices[v].co.y + o.location.y - y_cut) < eps for v in p.vertices): p.material_index = 1
def lathe_sec(name, prof, m_, seg=48, loc=(0, 0, 0)):
    o = lathe(name, prof, [m_, M_SEC], seg=seg, loc=loc); mark_caps(o); return o
def lathe_full(name, prof, m_, seg=64, loc=(0, 0, 0)):
    o = lathe(name, prof, m_, a0=0.0, ang=2 * math.pi, seg=seg, loc=loc)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    return o
ROTX = Matrix.Rotation(math.radians(90), 4, "Y")        # lathe axis z -> world +x (profile z = world x)
def xlathe(name, prof, m_, full=False, seg=40, loc=(0, 0, VZ)):
    """Lathe around the valve axis (parallel to x). prof = [(r, x)]; half (y >= 0, orange caps) unless full."""
    o = (lathe_full(name, prof, m_, seg=seg) if full else lathe(name, prof, [m_, M_SEC], seg=seg))
    o.data.transform(ROTX)
    if not full: mark_caps(o)
    o.location = loc; return o
def ring_prof(r0, r1, a, b): return [(r0, a), (r1, a), (r1, b), (r0, b)]
def sec_box(name, x0, x1, y0, y1, z0, z1, m_):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1)
    if y0 < 0 < y1: cut_front(bm, 0.0)
    o = mesh_obj(name, bm, [m_, M_SEC]); mark_caps(o); return o

# ================= room: utility corner =================
FLOOR = box("Floor", -400, 400, -700, 120, -10, 0, M_FLOOR)
WALL = box("BackWall", -400, 400, 70, 82, 0, 240, WALL_M)
box("SideWall", -120, -108, -200, 82, 0, 240, WALL_M)
DRAIN = cyl("FloorDrain", 5.0, 0.4, "Z", (37.5, 8, 0.2), M_DRAIN, seg=32)
bm = bmesh.new()
for k in range(5): add_box(bm, 33.0 + 2.0 * k - 0.3, 33.0 + 2.0 * k + 0.3, 3.5, 12.5, 0.38, 0.5)
mesh_obj("DrainSlots", bm, mat("SlotDark", (0.01, 0.01, 0.01), rough=0.9)[0])
# ceiling / roof deck (intact, and with the hole the rocket punches)
CEIL = box("Ceiling", -260, 260, -260, 82, 240, 258, M_CEIL)
CEIL_H = box("CeilingHole", -260, 260, -260, 82, 240, 258, M_CEIL)
_hc = cyl("HoleCutter", 36.0, 40.0, "Z", (0, 0, 249), None, seg=40); _hc.hide_render = True; _hc.display_type = "WIRE"
boolean(CEIL_H, _hc)
windows(CEIL, [(0.0, T_H), (C["inside"], DUR)]); windows(CEIL_H, [(T_H, C["inside"])])
# cold in / hot out pipes from the ceiling (static; hidden once the tank leaves)
for x in (-12.0, 12.0):
    p_ = cyl(f"HousePipe{x:+.0f}", 1.4, 75.0, "Z", (x, 6.0, 202.5), M_COPPER, seg=16)
    windows(p_, [(0.0, T_L + 0.05), (C["inside"], DUR)])

# ================= whole heater (hook / stake / rocket) =================
ROCK = empty("Rocket", (0, 0, 0))
HF = lathe_full("HeaterFull", [(0, 4), (28.0, 4), (28.5, 5), (28.5, 146), (27.5, 147.5), (4.0, 147.5), (4.0, 148.5), (0, 148.5)], M_JACKET); par(HF, ROCK)
LEGS = []
for k in range(3):
    a = k * 2 * math.pi / 3 + 0.5
    LEGS.append(par(cyl(f"Leg{k}", 1.5, 4.0, "Z", (22 * math.cos(a), 22 * math.sin(a), 2.0), M_BURNER, seg=12), ROCK))
par(rbox("BurnerDoor", -8, 8, -29.2, -28.0, 8, 18, 0.6, M_THERMO), ROCK)
TH_F = par(rbox("ThermoFull", -14, -2, -31.5, -27.5, 20, 31, 0.8, M_THERMO), ROCK)
par(cyl("ThermoDialFull", 2.4, 1.0, "Y", (-8, -31.8, 26.5), M_DIAL, seg=24), ROCK)
for x in (-12.0, 12.0): par(cyl(f"PipeStub{x:+.0f}", 1.4, 18.0, "Z", (x, 6.0, 156.0), M_COPPER, seg=16), ROCK)
par(cyl("FlueCap", 5.0, 6.0, "Z", (0, 0, 151.5), M_FLUE, seg=24), ROCK)
VF = [xlathe("ValveInletF", ring_prof(0, 1.6, 27.0, 33.5), M_BRF, full=True),
      xlathe("ValveBodyF", [(0, 33.5), (3.3, 33.5), (3.3, 41.0), (0, 41.0)], M_BRF, full=True),
      xlathe("ValveBonnetF", [(0, 41.0), (2.2, 41.0), (2.2, 50.0), (0, 50.0)], M_BRF, full=True),
      cyl("ValveOutletF", 1.8, 6.0, "Z", (37.5, 0, VZ - 4.0), M_BRF, seg=24),
      cyl("ValveStemF", 0.35, 3.0, "X", (51.0, 0, VZ), M_STEM, seg=12)]
for o in VF: par(o, ROCK)
LEVER_F = empty("LeverPivotF", (50.6, 0, VZ + 2.4)); par(LEVER_F, ROCK)
bm = bmesh.new(); add_box(bm, -9.0, 0.6, -0.6, 0.6, 0.0, 0.5)
par(mesh_obj("LeverF", bm, M_LEVER), LEVER_F)
PIPE_F = par(cyl("DischargeF", 1.4, VZ - 7.0 - 15.0, "Z", (37.5, 0, (VZ - 7.0 + 15.0) / 2), M_PIPE, seg=24), ROCK)
CAP1 = par(cyl("CapF", 1.75, 2.4, "Z", (37.5, 0, 15.2), M_CAP, seg=24), ROCK)
bake_scale(CAP1, lambda t: (pop(t, C["capped"]),) * 3)
windows(ROCK, FULLW)
for o in ROCK.children_recursive: windows(o, FULLW)
def rocket_loc(t):
    if t < C["tank"]: return (0.0, 0.0, 0.0)
    if t < T_L: return (0.5 * math.sin(2 * math.pi * 23 * t) * ease((t - C["tank"]) / 0.3), 0.0, 0.3 * abs(math.sin(2 * math.pi * 17 * t)))
    d = t - T_L; return (0.0, 0.0, 0.5 * ACC * d * d)
bake_loc(ROCK, rocket_loc)
glowc(B_JACKET, [(0.0, 0.0, RED), (C["tank"], 0.0, RED), (C["tank"] + 0.25, 0.2, RED), (T_L, 0.35, RED), (C["inside"] - 0.05, 0.35, RED), (C["inside"], 0.0, RED)])
glowc(B_BRF, [(0.0, 0.0, GOLD), (C["valve"] - 0.05, 0.0, GOLD), (C["valve"] + 0.15, 0.35, GOLD), (C["water"], 0.35, GOLD), (C["water"] + 0.5, 0.08, GOLD),
              (C["stuck"] - 0.05, 0.0, RED), (C["stuck"] + 0.15, 0.45, RED), (C["tank"], 0.3, RED)])
glowc(B_CAP, [(0.0, 0.0, RED), (C["capped"], 0.0, RED), (C["capped"] + 0.2, 0.5, RED), (C["stuck"], 0.3, RED)])
# steam venting at the base when it blows (particles), and ceiling chunks (rigid body)
STEAM_EM = cyl("SteamEmitter", 20.0, 1.0, "Z", (0, 0, 3.0), None, seg=16); STEAM_EM.hide_render = True; par(STEAM_EM, ROCK)
pm_steam = fx.particles(STEAM_EM, "dust", F(T_L - 0.1), F(T_L + 0.9), count=500)
try:
    ps_ = pm_steam.particle_system.settings; ps_.particle_size = 4.0; ps_.normal_factor = 150; ps_.factor_random = 1.5; ps_.lifetime = 40
    ps_.effector_weights.gravity = 0.0
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.9, 0.92, 0.95, 1); b_.inputs["Emission Color"].default_value = (0.9, 0.92, 0.95, 1)
    b_.inputs["Emission Strength"].default_value = 0.6
except Exception as e: print("[fx] steam tune skipped:", e)
CHUNKS = []
random.seed(7)
for k in range(14):
    a = k * 2 * math.pi / 14 + random.uniform(-0.15, 0.15); rr = random.uniform(10, 32)
    cx, cy = rr * math.cos(a), rr * math.sin(a) * 0.8
    s = random.uniform(8, 14)
    ch = rbox(f"Chunk{k}", cx - s / 2, cx + s / 2, cy - s / 2, cy + s / 2, 241, 241 + random.uniform(4, 8), 0.8, M_CEIL)
    CHUNKS.append(ch)
FLOOR_RB = box("FloorRB", -400, 400, -700, 120, -10, 0, None); FLOOR_RB.hide_render = True; FLOOR_RB.display_type = "WIRE"
fx.rigid(CHUNKS, passive=[FLOOR_RB], mass=2.0, friction=0.6, bounce=0.2)
for ch in CHUNKS:
    try:
        rb = ch.rigid_body; rb.kinematic = True; ch.keyframe_insert("rigid_body.kinematic", frame=1)
        ch.keyframe_insert("rigid_body.kinematic", frame=F(T_H) + 1)
        rb.kinematic = False; ch.keyframe_insert("rigid_body.kinematic", frame=F(T_H) + 2)
    except Exception as e: print("[build] chunk kinematic skipped", e)
    windows_r(ch, [(T_H, C["inside"])])

# ================= section heater =================
SEC = []
SEC.append(lathe_sec("JacketSec", [(27.6, 4), (28.5, 4), (28.5, 147), (4.0, 147), (4.0, 146.2), (27.6, 146.2)], M_JACKET, seg=64))
SEC.append(lathe_sec("FoamSec", [(24.0, 13.4), (27.6, 13.4), (27.6, 146.2), (4.0, 146.2), (4.0, 142.0), (24.0, 142.0)], M_FOAM, seg=64))
SEC.append(lathe_sec("TankSec", [(4.0, 13.4), (24.0, 13.4), (24.0, 142.0), (4.0, 142.0), (4.0, 141.4), (23.4, 141.4), (23.4, 14.0), (4.0, 14.0)], M_TANK, seg=64))
SEC.append(lathe_sec("FlueSec", ring_prof(3.4, 4.0, 4.0, 152.0), M_FLUE, seg=32))
WATER = lathe("Water", [(4.05, 14.05), (23.35, 14.05), (23.35, 141.35), (4.05, 141.35)], M_WATER, seg=64); SEC.append(WATER)
SEC.append(lathe_sec("BottomSkirt", ring_prof(26.0, 28.5, 0.0, 4.0), M_JACKET, seg=48))
for k in range(3):
    a = k * 2 * math.pi / 3 + 0.5
    if math.sin(a) >= 0: SEC.append(cyl(f"LegS{k}", 1.5, 4.0, "Z", (22 * math.cos(a), 22 * math.sin(a), 2.0), M_BURNER, seg=12))
# burner + flames
SEC.append(lathe_sec("BurnerSec", [(0, 6.5), (13.0, 6.5), (13.0, 8.0), (0, 8.0)], M_BURNER, seg=48))
FLAME = empty("FlameScale", (0, 0, 8.0)); FLAMES = []
for k in range(14):
    a = k * math.pi / 13
    x, y = 10.5 * math.cos(a), 10.5 * math.sin(a) + 0.4
    for m_, r_, h_ in ((M_FLAME, 1.0, 3.2), (M_FLAMET, 0.55, 4.6)):
        bm = bmesh.new(); add_cyl(bm, r_, h_, "Z", (0, 0, h_ / 2), seg=10, r2=0.05)
        o = mesh_obj(f"Flame{k}_{h_}", bm, m_); o.location = (x, y, 0.0); par(o, FLAME); o.location = (x, y, 0.0)
        FLAMES.append(o)
SEC.append(FLAME)
FL_ON = PW([(0, 0.02), (C["heats"] - 0.1, 0.02), (C["heats"] + 0.3, 1.0), (C["set"] - 0.05, 1.0), (C["set"] + 0.25, 0.02),
            (C["fails"], 0.02), (C["fails"] + 0.3, 1.0), (C["keeps"], 1.0), (C["keeps"] + 0.4, 1.45), (C["so"], 1.45), (C["so"] + 0.1, 0.6)])
bake_scale(FLAME, lambda t: (1.0, 1.0, FL_ON(t) * (1 + 0.08 * math.sin(2 * math.pi * 9 * t))))
# thermostat (left side, on the back half) + its sensing rod
THERMO = rbox("Thermostat", -38.0, -28.0, 0.2, 9.0, 14.0, 27.0, 0.8, M_THERMO); SEC.append(THERMO)
DIAL = cyl("ThermoDial", 2.6, 1.0, "Y", (-33.0, -0.1, 22.0), M_DIAL, seg=24); SEC.append(DIAL)
bm = bmesh.new(); add_box(bm, -0.3, 0.3, -0.6, -0.4, 0.0, 2.2); DIALP = mesh_obj("DialPointer", bm, mat("White", (0.95, 0.95, 0.95), rough=0.3)[0])
DIALP.location = (-33.0, 0, 22.0); SEC.append(DIALP)
bake_rot(DIALP, lambda t: (0.0, PW([(0, 0.6), (C["thermostat"], 0.6), (C["set"], -0.4)])(t), 0.0))
SEC.append(cyl("ThermoRod", 0.6, 14.0, "X", (-21.0, 4.0, 20.0), M_STEM, seg=12))
SEC.append(tube("GasLine", [(-33, 4.0, 14.0), (-33, 4.0, 10.0), (-20, 4.0, 7.2), (-12, 4.0, 7.2)], 0.7, M_STEM)[0])
glowc(B_THERMO, [(0.0, 0.0, GOLD), (C["thermostat"] - 0.05, 0.0, GOLD), (C["thermostat"] + 0.15, 0.22, GOLD), (C["set"] + 0.4, 0.22, GOLD),
                 (C["set"] + 0.9, 0.0, GOLD), (C["thermostat2"] - 0.05, 0.0, RED), (C["fails"] + 0.1, 0.4, RED), (C["hot"], 0.4, RED), (C["hot"] + 0.5, 0.0, RED)])
# cold-water dip tube + hot outlet nipple inside the top
SEC.append(cyl("DipTube", 1.0, 112.0, "Z", (-12.0, 6.0, 86.0), mat("DipTubeWhite", (0.9, 0.9, 0.88), rough=0.4)[0], seg=16))
for x in (-12.0, 12.0): SEC.append(cyl(f"TopPipe{x:+.0f}", 1.4, 22.0, "Z", (x, 6.0, 154.0), M_COPPER, seg=16))
# sediment on the tank floor (Geometry Nodes scatter)
SED_FLOOR = lathe("SedimentBed", [(4.2, 14.0), (23.2, 14.0), (23.2, 14.3), (4.2, 14.3)], M_SED, seg=48); SEC.append(SED_FLOOR)
SED = obj_from("SedSeed", sphere_mesh("SedSeedMe", 0.45, 1), M_SED)
fx.scatter(SED_FLOOR, SED, density=0.35, scale_min=0.5, scale_max=1.4, seed=11)
# water temperature: cyan (cold) -> orange (hot) -> red-orange (superheated)
COLD_C, WARM_C, HOT_C, SUP_C = CYAN, (1.0, 0.55, 0.20), (1.0, 0.38, 0.12), (1.0, 0.26, 0.08)
glowc(B_WATER, [(0.0, 0.05, COLD_C), (C["heats"], 0.05, COLD_C), (C["pressure"], 0.08, WARM_C), (C["keeps"], 0.08, WARM_C),
                (C["climbing"] + 0.3, 0.10, HOT_C), (C["under"], 0.10, HOT_C), (C["hotter"] + 0.4, 0.16, SUP_C), (C["if2"], 0.16, SUP_C),
                (C["so"], 0.10, WARM_C), (C["have"], 0.10, WARM_C), (DUR, 0.06, WARM_C)])
# pressure arrows (red) pushing out on the walls
ARROWS = []
for k, (bx, bz, dx, dz) in enumerate([(9, 40, 1, 0), (9, 80, 1, 0), (9, 118, 1, 0), (-9, 60, -1, 0), (-9, 100, -1, 0), (-14, 125, 0, 1), (14, 30, 0, -1)]):
    bm = bmesh.new(); add_arrow(bm, (0, 0), (dx, dz), 9.0, 3.6, y=0.0)
    o = mesh_obj(f"PressArrow{k}", bm, M_ARROW); o.location = (bx, 0.6, bz); ARROWS.append(o)
    def sc(t, k=k):
        a1 = pop(t, C["pressure"] - 0.1 + 0.03 * k) * (1 - ease((t - C["pressure"] - 0.6) / 0.3))
        a2 = pop(t, C["expands"] + 0.03 * k) * (1 + 0.35 * ease((t - C["climbs"]) / 0.4))
        return (max(a1, a2) if t < C["hotter"] else max(0.0, 1.35 * (1 - ease((t - C["hotter"]) / 0.3)))) + 1e-3
    bake_scale(o, lambda t, sc=sc: (sc(t),) * 3)
    windows(o, [(C["pressure"] - 0.15, C["normally"]), (C["expands"] - 0.1, C["hotter"] + 0.35)])
# tank split (crack glows red on the left wall)
bm = bmesh.new(); pts = [(-23.9, 0.05, 92), (-24.1, 0.05, 86), (-23.8, 0.05, 81), (-24.2, 0.05, 74), (-23.9, 0.05, 68), (-24.1, 0.05, 61)]
add_poly(bm, pts, 0.55, seg=6); CRACK = mesh_obj("Crack", bm, M_CRACK); SEC.append(CRACK)
bake_scale(CRACK, lambda t: (1.0, 1.0, 1e-3 + ease((t - C["splits"]) / 0.35)))
CRACK.location = (0, 0, 0)
glowc(B_CRACK, [(0.0, 0.0, RED), (C["splits"] - 0.05, 0.0, RED), (C["splits"] + 0.1, 6.0, RED)])
windows(CRACK, [(C["splits"] - 0.05, C["flashes"])])
# hottest water at the top + the "top 6 inches" zone (z 126..141.4 = 15 cm)
HOTTOP = lathe("HotTop", [(4.1, 126.2), (23.3, 126.2), (23.3, 141.3), (4.1, 141.3)], M_HOTG, seg=48)
keyval(F_HOTG, [(0.0, 0.0), (C["top"] - 0.05, 0.0), (C["top"] + 0.3, 0.30), (C["hottest"] + 0.3, 0.45), (C["at"] + 0.5, 0.45), (C["at"] + 1.2, 0.0)])
BANDS = []
for z in (126.0, 141.4):
    o = lathe(f"TopBand{z:.0f}", [(23.0, z - 0.3), (23.6, z - 0.3), (23.6, z + 0.3), (23.0, z + 0.3)], M_BAND, seg=48); BANDS.append(o)
glowc(B_BAND, [(0.0, 0.0, CYAN), (C["top"] - 0.05, 0.0, CYAN), (C["top"] + 0.2, 5.0, CYAN), (C["at"] + 0.3, 5.0, CYAN), (C["at"] + 0.8, 0.0, CYAN)])
for o in [HOTTOP] + BANDS: windows(o, [(C["top"] - 0.1, C["at"] + 1.3)])

# ================= T&P valve (section, axis along +x at z = VZ) =================
# disc travel (cm, +x = open): temperature trip, pressure trip, yearly lever test
D_OPEN = 1.1
DISC_X = PW([(0, 0.0), (C["lifts"], 0.0), (C["lifts"] + 0.35, D_OPEN), (C["superheat"] + 0.5, D_OPEN), (C["spring"] - 0.1, 0.0),
             (C["shoves"], 0.0), (C["shoves"] + 0.3, D_OPEN), (C["floor"], D_OPEN), (C["once2"], 0.0),
             (C["lift"], 0.0), (C["lift"] + 0.3, D_OPEN), (C["gush"] + 1.0, D_OPEN), (C["never"] + 0.2, 0.0)])
VS = []
VS.append(xlathe("ValveInlet", ring_prof(1.1, 1.6, 24.0, 33.5), M_BRASS))
VS.append(xlathe("ValveSeat", ring_prof(1.1, 3.3, 33.5, 34.1), M_BRASS))
VS.append(xlathe("ValveBody", ring_prof(2.5, 3.3, 34.1, 40.4), M_BRASS))
VS.append(xlathe("ValveDivider", ring_prof(1.7, 3.3, 40.4, 41.0), M_BRASS))
VS.append(xlathe("ValveBonnet", ring_prof(1.6, 2.2, 41.0, 49.4), M_BRASS))
VS.append(xlathe("ValveEndCap", ring_prof(0.45, 2.2, 49.4, 50.0), M_BRASS))
VS.append(xlathe("JacketCollar", ring_prof(1.6, 2.6, 27.6, 29.0), M_BRASS))
OUT_V = lathe_sec("ValveOutlet", ring_prof(1.3, 1.8, VZ - 7.0, VZ - 2.6), M_BRASS, seg=32, loc=(37.5, 0, 0)); VS.append(OUT_V)
PIPE_S = lathe_sec("DischargeSec", ring_prof(1.0, 1.4, 15.0, VZ - 7.0), M_PIPE, seg=32, loc=(37.5, 0, 0)); VS.append(PIPE_S)
MOVE = empty("DiscMove", (0, 0, 0))
bake_loc(MOVE, lambda t: (DISC_X(t), 0.0, 0.0))
DISC = xlathe("Disc", [(0, 34.1), (1.75, 34.1), (1.75, 34.7), (0, 34.7)], M_DISC, full=True); par(DISC, MOVE); DISC.location = (0, 0, VZ)
STEM = cyl("Stem", 0.35, 17.5, "X", (43.4, 0, VZ), M_STEM, seg=12); par(STEM, MOVE)
PROBE = cyl("ProbeRod", 0.42, 22.0, "X", (23.1, 0, VZ), M_PROBE, seg=12); par(PROBE, MOVE)
ELEM = empty("ElementSwell", (9.0, 0, VZ)); par(ELEM, MOVE)
bm = bmesh.new(); add_cyl(bm, 0.95, 6.0, "X", (0, 0, 0), seg=24)
bmesh.ops.bevel(bm, geom=[e for e in bm.edges], offset=0.4, segments=3, profile=0.5, affect="EDGES")
EL = mesh_obj("Element", bm, M_ELEM); par(EL, ELEM)
bake_scale(ELEM, lambda t: (1.0 + 0.12 * ease((t - C["expands2"]) / 0.5) * (1 - ease((t - C["spring"]) / 0.5)),
                            1.0 + 0.30 * ease((t - C["expands2"]) / 0.5) * (1 - ease((t - C["spring"]) / 0.5)),
                            1.0 + 0.30 * ease((t - C["expands2"]) / 0.5) * (1 - ease((t - C["spring"]) / 0.5))))
for o in (DISC, STEM, PROBE, EL): VS.append(o)
# spring: fixed at the end cap (x 49.4), free end on the back of the disc (x 34.7 + travel)
SPR_L0 = 49.4 - 34.7
bm = bmesh.new(); turns, nseg = 9, 9 * 16
pts = [(-SPR_L0 * i / nseg, 1.25 * math.cos(2 * math.pi * turns * i / nseg), 1.25 * math.sin(2 * math.pi * turns * i / nseg)) for i in range(nseg + 1)]
add_poly(bm, pts, 0.22, seg=6)
SPRING = mesh_obj("Spring", bm, M_SPRING); SPRING.location = (49.4, 0, VZ); VS.append(SPRING)
bake_scale(SPRING, lambda t: ((49.4 - 34.7 - DISC_X(t)) / SPR_L0, 1.0, 1.0))
# test lever (pivot at the bonnet end; lifting pulls the stem)
LEVER = empty("LeverPivot", (50.6, 0, VZ + 2.4))
bm = bmesh.new(); add_box(bm, -9.0, 0.6, -0.6, 0.6, 0.0, 0.5); add_box(bm, 0.0, 0.6, -0.6, 0.6, -2.4, 0.5)
LEV = mesh_obj("Lever", bm, M_LEVER); par(LEV, LEVER); VS.append(LEV)
bake_rot(LEVER, lambda t: (0.0, PW([(0, 0.0), (C["lift"], 0.0), (C["lift"] + 0.3, 0.55), (C["gush"] + 1.0, 0.55), (C["never"] + 0.2, 0.0)])(t), 0.0))
glowc(B_BRASS, [(0.0, 0.0, GOLD), (C["valve2"] - 0.05, 0.0, GOLD), (C["valve2"] + 0.15, 0.3, GOLD), (C["both"] + 0.3, 0.3, GOLD), (C["both"] + 0.8, 0.0, GOLD),
                (C["have"], 0.0, GOLD), (C["have"] + 0.3, 0.3, GOLD)])
glowc(B_PROBE, [(0.0, 0.0, GOLD), (C["probe"] - 0.05, 0.0, GOLD), (C["probe"] + 0.15, 1.2, GOLD), (C["hottest"], 1.2, GOLD), (C["hottest"] + 0.5, 0.0, GOLD)])
glowc(B_ELEM, [(0.0, 0.0, ORANGE), (C["element"] - 0.05, 0.0, ORANGE), (C["element"] + 0.15, 1.5, ORANGE), (C["superheat"], 1.5, ORANGE), (C["spring"], 0.0, ORANGE)])
glowc(B_DISC, [(0.0, 0.0, CYAN), (C["disc"] - 0.05, 0.0, CYAN), (C["disc"] + 0.15, 2.0, CYAN), (C["seat"] + 0.6, 2.0, CYAN), (C["seat"] + 1.0, 0.0, CYAN),
               (C["shoves"] - 0.05, 0.0, CYAN), (C["shoves"] + 0.15, 2.0, CYAN), (C["open"] + 0.5, 0.0, CYAN)])
glowc(B_SPRING, [(0.0, 0.0, GOLD), (C["spring"] - 0.05, 0.0, GOLD), (C["spring"] + 0.15, 1.2, GOLD), (C["shut"] + 0.4, 1.2, GOLD), (C["shut"] + 0.8, 0.0, GOLD)])
glowc(B_LEVER, [(0.0, 0.0, GOLD), (C["test"] - 0.05, 0.0, GOLD), (C["test"] + 0.15, 1.2, GOLD), (C["gush"], 1.2, GOLD), (C["gush"] + 0.5, 0.0, GOLD)])
glowc(B_PIPE, [(0.0, 0.0, GOLD), (C["pipe"] - 0.05, 0.0, GOLD), (C["pipe"] + 0.15, 0.4, GOLD), (C["floor"] + 0.3, 0.4, GOLD), (C["floor"] + 0.7, 0.0, GOLD)])
# pressure push on the disc (red arrow in the inlet bore)
bm = bmesh.new(); add_arrow(bm, (0, 0), (1, 0), 5.5, 1.6, y=0.0)
PARROW = mesh_obj("DiscArrow", bm, M_ARROW); PARROW.location = (27.6, 0.0, VZ); VS.append(PARROW)
bake_scale(PARROW, lambda t: (1e-3 + pop(t, C["pressure3"]) * (1 + 0.25 * ease((t - C["hits"]) / 0.8)),) * 3)
windows(PARROW, [(C["pressure3"] - 0.05, C["either"])])
# hot water path when the disc is off its seat: tank -> seat -> chamber -> outlet -> pipe -> floor drain
FLOW = Path([(14, 0.6, VZ), (33.0, 0.6, VZ), (34.4, 0.6, VZ + 1.5), (37.5, 0.6, VZ + 1.2), (37.5, 0.6, VZ - 7.0), (37.5, 0.6, 15.0), (37.5, 3.0, 0.6)])
OPEN_W = [(C["lifts"] + 0.25, C["spring"] - 0.2), (C["shoves"] + 0.25, C["once2"]), (C["lift"] + 0.25, C["never"] + 0.1)]
beads("HotBead", FLOW, 26, 0.5, M_HOTB, OPEN_W, speed=60.0)
# stream out of the pipe end on the yearly test, and drips on "drips"
STREAM = cyl("PipeStream", 0.85, 15.0, "Z", (37.5, 0.0, 7.5), M_STREAM, seg=12)
windows(STREAM, [(C["gush"] - 0.2, C["never"] + 0.1)])
DRIP_EM = cyl("DripEmitter", 0.8, 0.3, "Z", (37.5, 0.0, 14.8), None, seg=10); DRIP_EM.hide_render = True
pm_drip = fx.particles(DRIP_EM, "rain", F(C["drips"]), F(C["have"]), count=12)
try:
    ps_ = pm_drip.particle_system.settings; ps_.particle_size = 0.55; ps_.normal_factor = -10; ps_.lifetime = 12; ps_.factor_random = 0.1
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Emission Color"].default_value = (0.30, 0.92, 1.0, 1); b_.inputs["Emission Strength"].default_value = 3.0
except Exception as e: print("[fx] drip tune skipped:", e)
CAP2 = cyl("CapGhost", 1.75, 2.4, "Z", (37.5, 0, 15.2), M_CAP, seg=24)
bake_scale(CAP2, lambda t: (pop(t, C["cap"]) * (1 - ease((t - C["drips"] + 0.25) / 0.25)) + 1e-3,) * 3)
windows(CAP2, [(C["cap"] - 0.05, C["drips"] + 0.1)])
glowc(B_CAP, [(C["inside"], 0.0, RED), (C["cap"], 0.0, RED), (C["cap"] + 0.15, 0.8, RED)])
# Mantaflow: the gush out of the pipe end hitting the floor drain (laptop --bake-fluid; hidden without the cache)
FL_DOM = box("FluidDomain", 20.0, 55.0, -10.0, 20.0, 0.0, 16.0, None); FL_DOM.display_type = "WIRE"
FL_IN = cyl("FluidInflow", 0.85, 0.8, "Z", (37.5, 0.0, 14.5), None, seg=10); FL_IN.display_type = "WIRE"; FL_IN.hide_render = True
fx.fluid_domain(FL_DOM, FL_IN, eff=[FLOOR_RB], res=64, start=F(C["gush"] - 0.2), end=F(C["gush"] + 2.8), cache_dir=os.path.join(HERE, "cache_fluid"))
FL_M = water_sec("FluidWater", glow_rgb=(1.0, 0.55, 0.25))[0]
FL_DOM.data.materials.append(FL_M)
windows(FL_DOM, [(C["gush"] - 0.2, C["never"])] if FLUID_BAKE else [])
if not FLUID_BAKE: FL_DOM.hide_render = True
for o in SEC + VS + [MOVE, LEVER]: windows(o, SECW)
for o in FLAMES: windows(o, SECW)

# ================= steam set: a droplet flashes into steam, 10x wider = 1,000x the volume =================
STC = Vector((X_ST, 0, 100))
DROPLET = obj_from("Droplet", sphere_mesh("DropletMe", 2.0, 3), M_DROP, loc=STC)
windows(DROPLET, [(T_STEAM[0], C["flashes"] + 0.1)])
REF = obj_from("DropletRef", sphere_mesh("DropRefMe", 2.0, 3), M_REF, loc=STC + Vector((0, -2.5, 0)))
keyval(F_REF, [(0.0, 0.0), (C["flashes"] + 0.3, 0.0), (C["steam"], 0.8)])
windows(REF, [(C["flashes"], T_STEAM[1])])
STEAMB = obj_from("SteamBall", sphere_mesh("SteamBallMe", 2.0, 4), M_STEAMG, loc=STC)
bake_scale(STEAMB, lambda t: (1.0 + 9.0 * ease((t - C["flashes"]) / 1.8),) * 3)
keyval(F_STEAMG, [(0.0, 0.0), (C["flashes"] - 0.05, 0.0), (C["flashes"] + 0.2, 0.55), (C["so"], 0.40)])
windows(STEAMB, [(C["flashes"], T_STEAM[1])])
ST_EM = obj_from("SteamBurstEm", sphere_mesh("SteamBurstMe", 6.0, 2), None, loc=STC); ST_EM.hide_render = True
pm_burst = fx.particles(ST_EM, "dust", F(C["once"] - 0.1), F(C["once"] + 0.3), count=260)
try:
    ps_ = pm_burst.particle_system.settings; ps_.particle_size = 1.4; ps_.normal_factor = 60; ps_.factor_random = 0.8; ps_.lifetime = 45
    ps_.effector_weights.gravity = 0.0
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.9, 0.92, 0.95, 1); b_.inputs["Emission Color"].default_value = (0.9, 0.92, 0.95, 1)
    b_.inputs["Emission Strength"].default_value = 0.8
except Exception as e: print("[fx] burst tune skipped:", e)
STAGE = cyl("SteamStage", 60.0, 2.0, "Z", (X_ST, 0, 60.0), mat("Stage", (0.05, 0.06, 0.08), rough=0.5)[0], seg=64)
ST_RING, B_STR = emit_mat("StageRing", CYAN, 2.0)
torus("StageGlow", 60.0, 0.4, ST_RING, (X_ST, 0, 61.0), segU=96, segV=8)

# ================= lights + world =================
fx.hdri("interior", strength=0.3, rotation_deg=200.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, rot, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("Key", (160, -220, 230), (math.radians(50), 0, math.radians(35)), 140, 1.2e5, (1.0, 0.95, 0.88))
area("Rim", (-80, 50, 170), (math.radians(-60), 0, math.radians(-120)), 100, 4.0e4, (0.6, 0.8, 1.0))
area("Low", (60, -140, 20), (math.radians(100), 0, math.radians(20)), 80, 1.5e4, (1.0, 0.9, 0.8))
area("ValveKey", (70, -60, 170), (math.radians(40), 0, math.radians(45)), 50, 1.2e4, (1.0, 0.96, 0.9))
area("StKey", (X_ST + 80, -120, 180), (math.radians(45), 0, math.radians(30)), 80, 2.0e4, (0.85, 0.92, 1.0))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.5; cam_d.clip_end = 8000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (58, -34, 141), (39, 0, 133), 38),
    (C["water"] - 0.05, (54, -30, 139), (39, 0, 133), 38),
    (C["water"], (70, -215, 120), (6, 0, 92), 34, "cut"),
    (C["if"] - 0.05, (58, -195, 116), (8, 0, 94), 34),
    (C["if"], (55, -34, 24), (37.5, 0, 15), 40, "cut"),
    (C["stuck"] - 0.05, (53, -31, 23), (37.5, 0, 15.5), 40),
    (C["stuck"], (58, -34, 141), (39, 0, 133), 38, "cut"),
    (C["tank"] - 0.05, (55, -31, 139), (39, 0, 133), 38),
    (C["tank"], (70, -440, 110), (0, 0, 120), 26, "cut"),
    (T_L, (68, -430, 110), (0, 0, 125), 26),
    (C["inside"] - 0.05, (60, -420, 105), (0, 0, 190), 26),
    (C["inside"], (22, -215, 80), (2, 0, 68), 32, "cut"),
    (C["normally"] - 0.05, (18, -200, 78), (2, 0, 68), 32),
    (C["normally"], (-12, -62, 30), (-30, 4, 19), 38, "cut"),
    (C["keeps"] - 0.05, (-14, -58, 29), (-28, 4, 19), 38),
    (C["keeps"], (12, -78, 34), (0, 2, 24), 38, "cut"),
    (C["hot"] - 0.05, (10, -72, 34), (0, 2, 26), 38),
    (C["hot"], (24, -215, 90), (2, 0, 80), 32, "cut"),
    (C["under"] - 0.05, (20, -200, 88), (2, 0, 80), 32),
    (C["under"], (14, -125, 100), (0, 0, 92), 34, "cut"),
    (C["if2"] - 0.05, (12, -112, 98), (0, 0, 90), 34),
    (C["if2"], (-2, -105, 84), (-16, 0, 76), 36, "cut"),
    (C["flashes"] - 0.05, (-4, -95, 82), (-18, 0, 76), 36),
    (C["flashes"], (X_ST + 12, -78, 108), (X_ST, 0, 100), 38, "cut"),
    (C["steam"] + 0.6, (X_ST + 20, -150, 112), (X_ST, 0, 100), 34),
    (C["so"] - 0.05, (X_ST + 22, -160, 114), (X_ST, 0, 100), 34),
    (C["so"], (34, -125, 136), (22, 0, 128), 34, "cut"),
    (C["at"] - 0.05, (30, -112, 135), (22, 0, 129), 34),
    (C["at"], (40, -50, 137), (38, 0, 133), 38, "cut"),
    (C["element"] - 0.05, (40, -48, 137), (38, 0, 133), 38),
    (C["element"], (14, -36, 136), (11, 0, 133), 38, "cut"),
    (C["lifts"] - 0.05, (13, -34, 136), (11, 0, 133), 38),
    (C["lifts"], (40, -44, 137), (37, 0, 133), 38, "cut"),
    (C["hot2"] - 0.05, (40, -42, 136), (37, 0, 133), 38),
    (C["hot2"], (60, -105, 112), (36, 0, 108), 34, "cut"),
    (C["spring"] - 0.05, (58, -100, 110), (36, 0, 108), 34),
    (C["spring"], (44, -50, 137), (41, 0, 133), 38, "cut"),
    (C["either"] - 0.05, (44, -46, 136), (40, 0, 133), 38),
    (C["either"], (62, -100, 120), (37.5, 0, 112), 34, "cut"),
    (C["floor"], (56, -80, 32), (37.5, 0, 16), 36),
    (C["once2"] - 0.05, (55, -76, 30), (37.5, 0, 16), 36),
    (C["once2"], (54, -40, 145), (45, 0, 135), 38, "cut"),
    (C["gush"] - 0.05, (52, -37, 144), (45, 0, 135), 38),
    (C["gush"], (58, -62, 28), (37.5, 0, 10), 38, "cut"),
    (C["drip"] - 0.05, (54, -55, 26), (37.5, 0, 11), 38),
    (C["drip"], (56, -110, 128), (34, 0, 124), 34, "cut"),
    (C["have"] - 0.05, (52, -100, 126), (34, 0, 124), 34),
    (C["have"], (62, -240, 116), (8, 0, 88), 32, "cut"),
    (DUR, (48, -205, 110), (8, 0, 90), 32),
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
bake_scalar(cam_d, "dof.aperture_fstop", [max(2.8, min(16.0, 0.08 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 30; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0e2, min(2.0e4, 0.25 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
fill = bpy.data.objects.new("CamFill", fill_d); scene.collection.objects.link(fill)
fill.parent = cam; fill.matrix_parent_inverse = Matrix.Identity(4); fill.location = (8, 10, 0)
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
fx.bake_rigid(1, F(C["inside"]) + 5)
if FLUID_BAKE: fx.bake_fluid(FL_DOM)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "valve_full": (38.0, -3.3, VZ), "heater": (0.0, -28.5, 90.0), "pipe_end": (37.5, 0.0, 14.0), "thermostat": (-33.0, 0.0, 27.0),
    "burner": (-6.0, 0.0, 9.0), "water": (-12.0, 0.0, 70.0), "crack": (-24.0, 0.0, 76.0), "probe": (17.0, 0.0, VZ + 0.4),
    "top6": (10.0, 0.0, 139.0), "element": (9.0, 0.0, VZ + 1.0), "disc": (34.4, 0.0, VZ + 1.8), "seat": (33.8, 0.0, VZ - 3.3),
    "spring": (45.0, 0.0, VZ + 2.2), "lever": (46.0, 0.0, VZ + 3.0), "pipe": (37.5, 0.0, 42.0), "valve": (38.0, 0.0, VZ + 3.3),
    "droplet": (X_ST, 0.0, 102.0), "steam": (X_ST, 0.0, 120.0),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p = world_to_camera_view(scene, cam, Vector(p_))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "stake": RR(*T_STAKE), "inside": RR(*T_IN), "fail": RR(*T_FAIL), "super": RR(*T_SUPER), "steam": RR(*T_STEAM),
          "probe": RR(*T_PROBE), "temp": RR(*T_TEMP), "press": RR(*T_PRESS), "drain": RR(*T_DRAIN), "test": RR(*T_TEST), "cap": RR(*T_CAP),
          "cta": RR(*T_CTA), "cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4],
          "cap_on": round(C["capped"], 3), "rumble": RR(C["tank"], T_L), "launch": round(T_L, 3), "ceiling_hit": round(T_H, 3),
          "flames_on": [round(C["heats"], 3), round(C["fails"], 3)], "flames_off": round(C["set"], 3), "crack": round(C["splits"], 3),
          "flash": round(C["flashes"], 3), "burst": round(C["once"], 3),
          "disc_open": [round(C["lifts"], 3), round(C["shoves"], 3), round(C["lift"], 3)],
          "disc_close": [round(C["spring"] - 0.1, 3), round(C["once2"], 3), round(C["never"] + 0.2, 3)],
          "flow": [RR(a, b) for a, b in OPEN_W], "gush": RR(C["gush"] - 0.2, C["never"] + 0.1), "drips": RR(C["drips"], C["have"]),
          "cap_ghost": round(C["cap"], 3)}
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
