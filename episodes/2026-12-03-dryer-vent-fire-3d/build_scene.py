# Dryer vent fire (3d-46a): "Lint left in your dryer is the number one reason dryers catch fire."
# Stake: the worst of it hides inside the wall. Heater warms the air, a fan pulls it through the tumbling clothes, every load sheds fibers,
# the screen catches a lot but not all; the rest ride the air into the duct that runs through the wall to the outside. Lint sticks to the
# sides (worst in floppy foil ducts that sag and kink), the pipe narrows, hot air can't get out, heat builds around the heater; the safety
# (high-limit) thermostat should cut it, but if it fails and the vent is blocked, lint near the heater can ignite and the fire has a duct
# full of fuel running through the wall. USFA 2008-2010: ~2,900 home dryer fires/yr, peak in January. Fixes: clean the screen every load,
# rigid metal duct (not plastic/foil), check the outside flap opens while it runs, slow drying = duct may be blocked.
# Illustrative, 1 unit = 1 cm: generic electric dryer (front panel removed, drum axis along y), foil duct behind it at y = 75 cut open
# (keep y >= 75), side wall at x 95..108 cut at y = 75, exterior hood + flap. No brand, no text, no people.
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
random.seed(46)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("lint","Lint"),("dryer","dryer"),("number","number"),("fire","fire."),("and","And"),("worst","worst"),("inside","inside"),
  ("wall","wall,"),("never","never"),("here","Here's"),("heater","heater"),("warms","warms"),("air","air,"),("fan","fan"),("pulls","pulls"),
  ("tumbling","tumbling"),("every","Every"),("load","load"),("sheds","sheds"),("fibers","fibers."),("screen","screen"),("catches","catches"),
  ("lot","lot"),("but","but"),("all","all."),("rest","rest"),("ride","ride"),("duct","duct,"),("pipe","pipe"),("wall2","wall"),
  ("outside","outside."),("lint2","Lint"),("sticks","sticks"),("sides","sides,"),("floppy","floppy"),("foil","foil"),("sag","sag"),
  ("kink","kink."),("load2","Load"),("narrower","narrower."),("now","Now"),("cant","can't"),("heat","Heat"),("builds","builds"),
  ("heater2","heater."),("safety","safety"),("thermostat","thermostat"),("cut","cut"),("power","power."),("but2","But"),("fails","fails,"),
  ("vent","vent"),("blocked","blocked,"),("lint3","lint"),("near","near"),("heater3","heater"),("catch","catch"),("fire2","fire."),
  ("and2","And"),("fire3","fire"),("pipe2","pipe"),("fuel","fuel,"),("running","running"),("wall3","wall."),("in","In"),("federal","federal"),
  ("departments","departments"),("two","two"),("thousand","thousand"),("nine","nine"),("hundred","hundred"),("home","home"),("year","year,"),("peak","peak"),
  ("january","January."),("so","So"),("clean","clean"),("screen2","screen"),("every2","every"),("load3","load."),("use","Use"),
  ("rigid","rigid"),("metal","metal"),("duct2","duct,"),("not","not"),("plastic","plastic"),("foil2","foil."),("go","Go"),
  ("outside2","outside"),("runs","runs,"),("check","check"),("flap","flap"),("opens","opens."),("if","If"),("clothes","clothes"),
  ("longer","longer"),("dry","dry,"),("duct3","duct"),("blocked2","blocked."),("when","When"),("last","last"),("clean2","clean"),
  ("duct4","duct?"),("tell","Tell"),("comments","comments.")]
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
CL = coll("DryerVent")
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
YD = 75.0                                    # duct + wall section plane (keep y >= 75 there)
DZ = 52.0                                    # drum axis height
# ---------- beat windows ----------
T_HOOK = (0.0, C["and"]); T_WALL = (C["and"], C["here"]); T_HOW = (C["here"], C["every"]); T_FIB = (C["every"], C["rest"])
T_DUCT = (C["rest"], C["lint2"]); T_STICK = (C["lint2"], C["now"]); T_BLOCK = (C["now"], C["safety"]); T_THERMO = (C["safety"], C["lint3"])
T_IGNITE = (C["lint3"], C["and2"]); T_SPREAD = (C["and2"], C["in"]); T_STATS = (C["in"], C["so"]); T_CLEAN = (C["so"], C["use"])
T_RIGID = (C["use"], C["go"]); T_FLAP = (C["go"], C["if"]); T_SLOW = (C["if"], C["when"]); T_CTA = (C["when"], DUR)
DIRTY = (0.0, C["so"])                        # foil duct + lint lining exist until "So clean the screen"
FIRE_W = (C["catch"], C["so"])

# ---------- materials ----------
M_SEC, B_SEC = mat("CutFace", (0.90, 0.38, 0.06), rough=0.5, emit_rgb=(1.0, 0.40, 0.08)); B_SEC.inputs["Emission Strength"].default_value = 0.12
GOLD, CYAN, RED, ORANGE = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.15)
def glowc(bsdf, keys):
    s_in, c_in = bsdf.inputs["Emission Strength"], bsdf.inputs["Emission Color"]
    for t, s, rgb in keys:
        s_in.default_value = s; s_in.keyframe_insert("default_value", frame=F(t))
        c_in.default_value = (*rgb, 1); c_in.keyframe_insert("default_value", frame=F(t))
def mark_caps(o, y_cut=0.0, eps=1e-3):
    me = o.data
    if len(me.materials) < 2: me.materials.append(M_SEC)
    for p in me.polygons:
        if all(abs(me.vertices[v].co.y + o.location.y - y_cut) < eps for v in p.vertices): p.material_index = 1
def sec_box(name, x0, x1, y0, y1, z0, z1, m_, ycut=0.0):
    """Box; faces lying on the section plane get the orange cut material."""
    bm = bmesh.new(); add_box(bm, x0, x1, max(y0, ycut), y1, z0, z1)
    o = mesh_obj(name, bm, [m_, M_SEC]); mark_caps(o, ycut); return o
M_ENAMEL, B_ENAMEL = mat("Enamel", (0.86, 0.87, 0.88), rough=0.3, emit_rgb=RED)
M_STEEL, _ = mat("DrumSteel", (0.62, 0.63, 0.65), rough=0.28, metallic=1.0, noise=30)
M_DARK, _ = mat("DarkMetal", (0.08, 0.08, 0.09), rough=0.45, metallic=0.6)
M_HOUSE, B_HOUSE = mat("HeaterHousing", (0.42, 0.43, 0.45), rough=0.35, metallic=1.0, emit_rgb=(1.0, 0.22, 0.06))
M_COIL, B_COIL = mat("Coil", (0.35, 0.18, 0.10), rough=0.4, metallic=1.0, emit_rgb=(1.0, 0.42, 0.10))
M_THERMO, B_THERMO = mat("Thermostat", (0.10, 0.10, 0.11), rough=0.4, emit_rgb=GOLD)
M_FAN, _ = mat("Fan", (0.18, 0.18, 0.2), rough=0.4)
M_SCREENF, B_SCREENF = mat("ScreenFrame", (0.20, 0.21, 0.23), rough=0.4, emit_rgb=GOLD)
# screen mesh: dark grid
M_MESH, nt_, b_ = new_mat("ScreenMesh")
_br = nt_.nodes.new("ShaderNodeTexBrick"); _tc = nt_.nodes.new("ShaderNodeTexCoord"); nt_.links.new(_tc.outputs["Object"], _br.inputs["Vector"])
_br.inputs["Scale"].default_value = 1.6; _br.inputs["Mortar Size"].default_value = 0.25; _br.offset = 0.0
_br.inputs["Color1"].default_value = (0.03, 0.03, 0.035, 1); _br.inputs["Color2"].default_value = (0.03, 0.03, 0.035, 1); _br.inputs["Mortar"].default_value = (0.55, 0.56, 0.58, 1)
nt_.links.new(_br.outputs["Color"], b_["Base Color"] if False else b_.inputs["Base Color"]); b_.inputs["Metallic"].default_value = 0.8; b_.inputs["Roughness"].default_value = 0.35
def lint_mat(name):
    """Grey felt; emission = Pulse (uniform) + Fire * (object X < Front) * noise -> keyable fire front."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    col = mix_rgb(nt, nz.outputs["Fac"], (0.40, 0.39, 0.37), (0.70, 0.68, 0.65)); L.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    try: b.inputs["Sheen Weight"].default_value = 0.6
    except Exception: pass
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6; L.new(nz.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    front = VALUE(nt, "Front", [(0.0, -500.0)]); fire = VALUE(nt, "Fire", [(0.0, 0.0)]); pulse_ = VALUE(nt, "Pulse", [(0.0, 0.0)])
    lt = MATH(nt, "LESS_THAN", sep.outputs["X"], front)
    fl = MATH(nt, "MULTIPLY", MATH(nt, "MULTIPLY", lt, fire), MATH(nt, "POWER", nz.outputs["Fac"], 2.0))
    em = MATH(nt, "ADD", fl, MATH(nt, "MULTIPLY", pulse_, nz.outputs["Fac"]))
    b.inputs["Emission Color"].default_value = (1.0, 0.36, 0.08, 1); L.new(em, b.inputs["Emission Strength"])
    return m, nt
def lint_keys(nt, name, keys):
    s = nt.nodes[name].outputs[0]
    for t, v in keys: s.default_value = v; s.keyframe_insert("default_value", frame=F(t))
M_LINT, NT_LINT = lint_mat("LintDuct")
M_LINTH, NT_LINTH = lint_mat("LintHeater")
M_LINTS, NT_LINTS = lint_mat("LintScreen")
M_LINTR, NT_LINTR = lint_mat("LintRigid")
M_FOIL, nt_f, b_f = new_mat("FoilDuct")
_wv = nt_f.nodes.new("ShaderNodeTexWave"); _tc2 = nt_f.nodes.new("ShaderNodeTexCoord"); nt_f.links.new(_tc2.outputs["Object"], _wv.inputs["Vector"])
_wv.wave_type = "BANDS"; _wv.bands_direction = "X"; _wv.inputs["Scale"].default_value = 0.35
_bp = nt_f.nodes.new("ShaderNodeBump"); _bp.inputs["Strength"].default_value = 0.7; nt_f.links.new(_wv.outputs["Fac"], _bp.inputs["Height"]); nt_f.links.new(_bp.outputs[0], b_f.inputs["Normal"])
b_f.inputs["Base Color"].default_value = (0.80, 0.80, 0.82, 1); b_f.inputs["Metallic"].default_value = 1.0; b_f.inputs["Roughness"].default_value = 0.22
b_f.inputs["Emission Color"].default_value = (*RED, 1); B_FOIL = b_f
M_RIGID, B_RIGID = mat("RigidDuct", (0.72, 0.74, 0.76), rough=0.18, metallic=1.0, emit_rgb=CYAN)
M_DRYW, _ = mat("Drywall", (0.86, 0.85, 0.82), rough=0.8)
M_STUD, _ = mat("Stud", (0.78, 0.60, 0.38), rough=0.7, noise=6)
M_INSUL, _ = mat("Insulation", (0.95, 0.62, 0.62), rough=0.95, noise=2)
M_SIDING, _ = mat("Siding", (0.30, 0.36, 0.42), rough=0.6)
M_ROOMW, _ = mat("RoomWall", (0.22, 0.24, 0.28), rough=0.8)
M_FLOOR = tiles("FloorTile", (0.30, 0.29, 0.28), (0.26, 0.25, 0.24), 0.04, plane="XY")
M_SNOW, _ = mat("Snow", (0.80, 0.84, 0.90), rough=0.6, noise=1.5)
M_SKY, B_SKY = emit_mat("NightSky", (0.04, 0.07, 0.14), 1.0)
M_HOOD, _ = mat("Hood", (0.85, 0.86, 0.86), rough=0.35)
M_FLAP, B_FLAP = mat("Flap", (0.80, 0.81, 0.82), rough=0.3, emit_rgb=CYAN)
M_BIN, _ = mat("Bin", (0.12, 0.30, 0.42), rough=0.5)
M_HOTB, B_HOTB = emit_mat("BeadHot", (1.0, 0.48, 0.16), 4.0)
M_AIRB, B_AIRB = emit_mat("BeadAir", (0.75, 0.90, 1.0), 2.5)
M_FIBER, _ = mat("Fiber", (0.75, 0.74, 0.72), rough=0.9)
M_FLAME, B_FLAME = emit_mat("Flame", (1.0, 0.45, 0.10), 9.0)
M_FLAMEC, B_FLAMEC = emit_mat("FlameCore", (1.0, 0.82, 0.35), 14.0)
FABRICS = [(0.10, 0.20, 0.45), (0.70, 0.12, 0.10), (0.85, 0.85, 0.82), (0.95, 0.70, 0.20), (0.15, 0.40, 0.25), (0.35, 0.35, 0.40), (0.55, 0.30, 0.55)]
M_CLOTH = []
for i, rgb in enumerate(FABRICS):
    m_, b_ = mat(f"Cloth{i}", rgb, rough=0.9, noise=3, emit_rgb=CYAN)
    try: b_.inputs["Sheen Weight"].default_value = 0.8
    except Exception: pass
    M_CLOTH.append((m_, b_))

def lathe_full(name, prof, m_, seg=64, loc=(0, 0, 0)):
    o = lathe(name, prof, m_, a0=0.0, ang=2 * math.pi, seg=seg, loc=loc)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    return o
# ================= room =================
box("Floor", -200, 95, -300, 120, -5, 0, M_FLOOR)
box("RoomBackWall", -200, 95, 110, 120, 0, 250, M_ROOMW)
# side wall x 95..108, cut at y = 75, hole for the duct (centre z 30, r 5.4) by splitting the slabs
HZ0, HZ1, HY = 30 - 5.6, 30 + 5.6, YD + 5.6
LAYERS = [("Drywall", 95.0, 96.3, M_DRYW), ("Insul", 96.3, 105.2, M_INSUL), ("Sheath", 105.2, 106.4, M_STUD), ("Siding", 106.4, 108.0, M_SIDING)]
for nm, x0, x1, m_ in LAYERS:
    sec_box(f"{nm}Lo", x0, x1, YD, 260, -5, HZ0, m_, ycut=YD)
    sec_box(f"{nm}Hi", x0, x1, YD, 260, HZ1, 250, m_, ycut=YD)
    sec_box(f"{nm}Mid", x0, x1, HY, 260, HZ0, HZ1, m_, ycut=YD)
sec_box("StudA", 96.3, 105.2, YD, YD + 3.8, 0, HZ0 - 0.1, M_STUD, ycut=YD)
sec_box("StudB", 96.3, 105.2, YD, YD + 3.8, HZ1 + 0.1, 245, M_STUD, ycut=YD)
sec_box("Plate", 96.3, 105.2, YD, 260, 0, 3.8, M_STUD, ycut=YD)
GROUND = box("Ground", 108, 700, -300, 700, -12, -5, M_SNOW)
SKY = box("SkyBackdrop", 108, 900, 690, 700, -12, 600, M_SKY)
box("SkyLeft", 880, 890, -300, 700, -12, 600, M_SKY)

# ================= dryer cabinet (front panel removed, cut at y = 0) =================
CAB = []
CAB.append(sec_box("CabLeft", -35, -33.8, 0, 65, 0, 95, M_ENAMEL))
CAB.append(sec_box("CabRight", 33.8, 35, 0, 65, 0, 95, M_ENAMEL))
CAB.append(sec_box("CabTopL", -35, -18, 0, 65, 93.8, 95, M_ENAMEL))
CAB.append(sec_box("CabTopR", 18, 35, 0, 65, 93.8, 95, M_ENAMEL))
CAB.append(sec_box("CabTopB", -18, 18, 8, 65, 93.8, 95, M_ENAMEL))     # slot for the screen at the front
CAB.append(sec_box("CabBack", -35, 35, 63.8, 65, 0, 95, M_ENAMEL))
CAB.append(sec_box("CabBase", -35, 35, 0, 65, 0, 1.2, M_DARK))
for k, (x, y) in enumerate([(-31, 3), (31, 3)]): cyl(f"Foot{k}", 2.0, 1.5, "Z", (x, y + 2, -0.2), M_DARK, seg=16)
# ================= drum (axis along y, rotates) =================
ROTY = Matrix.Rotation(math.radians(-90), 4, "X")       # lathe axis z -> world +y
DRUM = empty("DrumRot", (0, 0, DZ))
def ylathe(name, prof, m_, seg=64):
    o = lathe(name, prof, m_, a0=0.0, ang=2 * math.pi, seg=seg); o.data.transform(ROTY)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    return o
par(ylathe("DrumShell", [(29.4, 6.0), (30.0, 6.0), (30.0, 58.0), (29.4, 58.0)], M_STEEL), DRUM)
par(ylathe("DrumBack", [(0.01, 57.4), (29.4, 57.4), (29.4, 58.0), (0.01, 58.0)], M_STEEL), DRUM)
par(ylathe("DrumLip", [(22.0, 5.0), (30.0, 5.0), (30.0, 6.2), (22.0, 6.2)], M_STEEL), DRUM)
for k in range(3):
    a = k * 2 * math.pi / 3
    bm = bmesh.new(); add_box(bm, -2.0, 2.0, 8.0, 56.0, -29.6, -25.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "Y"))
    par(mesh_obj(f"Lifter{k}", bm, M_STEEL), DRUM)
OMEGA = 4.2
bake_fn(DRUM, "rotation_euler", 1, lambda t: -OMEGA * t)
# clothes tumble in the x-z plane: carried up the right side, then fall back
CLOTHES = []
for i in range(7):
    me = sphere_mesh(f"ClothMe{i}", 1.0, 3); o = obj_from(f"Cloth{i}", me, M_CLOTH[i][0])
    sx, sy, sz = random.uniform(7, 10), random.uniform(8, 12), random.uniform(4.5, 6.5)
    o.scale = (sx, sy, sz); yi = 18 + 5 * i
    ph = i / 7.0; P = 2 * math.pi / OMEGA * 1.15
    def cloth_pos(t, ph=ph, yi=yi, P=P):
        u = (t / P + ph) % 1.0; R = 21.0
        if u < 0.62:
            a = -math.pi / 2 + (u / 0.62) * (math.pi * 0.78)
            return (R * math.cos(a), yi, DZ + R * math.sin(a))
        a1 = -math.pi / 2 + math.pi * 0.78; x1, z1 = R * math.cos(a1), R * math.sin(a1)
        v = (u - 0.62) / 0.38
        return (x1 + (-x1 * 0.6) * v, yi, DZ + z1 + (-R - z1) * v * v)
    bake_loc(o, cloth_pos)
    bake_rot(o, lambda t, i=i: (0.3 * math.sin(1.7 * t + i), 2.1 * t + i, 0.5 * math.cos(1.3 * t + i)))
    CLOTHES.append(o)
# ================= heater housing (front face open at y = 12) + coil + thermostat =================
HX = 30.2
HEAT = [sec_box("HouseL", 27.0, 27.8, 12, 50, 14, 78, M_HOUSE, ycut=12), sec_box("HouseR", 32.6, 33.4, 12, 50, 14, 78, M_HOUSE, ycut=12),
        sec_box("HouseB", 27.0, 33.4, 49.2, 50, 14, 78, M_HOUSE, ycut=12), sec_box("HouseBot", 27.0, 33.4, 12, 50, 14, 14.8, M_HOUSE, ycut=12)]
pts = [(HX + 1.7 * math.cos(k * 0.5), 30 + 1.7 * math.sin(k * 0.5) * 3.0, 18 + k * 0.26) for k in range(0, 210)]
COIL = poly_obj("Coil", pts, 0.32, M_COIL, seg=6)
COIL2 = poly_obj("Coil2", [(HX + 1.7 * math.cos(k * 0.5 + 3.1), 40 + 1.7 * math.sin(k * 0.5 + 3.1) * 3.0, 18 + k * 0.26) for k in range(0, 210)], 0.32, M_COIL, seg=6)
THERMO = cyl("Thermostat", 1.9, 1.6, "Y", (HX, 11.4, 81.0), M_THERMO, seg=24)
box("ThermoBracket", HX - 2.6, HX + 2.6, 11.0, 14.0, 78.0, 79.4, M_DARK)
for dx in (-1.0, 1.0): cyl(f"ThermoPin{dx}", 0.3, 2.0, "Z", (HX + dx, 11.4, 83.2), M_STEEL, seg=8)
# lint that collects around the heater base (the fuel)
LINTH = []
random.seed(12)
for k in range(9):
    me = sphere_mesh(f"LintHMe{k}", 1.0, 2); o = obj_from(f"LintH{k}", me, M_LINTH)
    o.location = (random.uniform(26.0, 33.0), random.uniform(13.0, 34.0), random.uniform(1.6, 3.0) if k < 5 else random.uniform(15.0, 16.2))
    o.scale = (random.uniform(1.6, 2.8), random.uniform(1.6, 2.8), random.uniform(0.6, 1.0)); LINTH.append(o)
# ================= blower (bottom left) =================
FAN = empty("FanRot", (-20, 30, 10))
par(ylathe("FanHub", [(0.01, -3.0), (2.2, -3.0), (2.2, 3.0), (0.01, 3.0)], M_FAN, seg=24), FAN)
for k in range(10):
    bm = bmesh.new(); add_box(bm, -0.35, 0.35, -3.0, 3.0, 2.2, 7.0)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(k * 2 * math.pi / 10, 3, "Y") @ Matrix.Rotation(0.35, 3, "Y"))
    par(mesh_obj(f"Blade{k}", bm, M_FAN), FAN)
bake_fn(FAN, "rotation_euler", 1, lambda t: -14.0 * t)
FANRING = ylathe("FanScroll", [(7.6, 24.0), (8.4, 24.0), (8.4, 36.0), (7.6, 36.0)], M_DARK, seg=48); FANRING.location = (-20, 0, 10)
sec_box("Chute", -33.8, -31.6, 4, 40, 14, 92, M_DARK)
# ================= lint screen (top front, pulls up) =================
SCR = empty("ScreenLift", (0, 0, 0))
par(sec_box("ScreenFrameT", -16.5, 16.5, 4.0, 6.0, 92.0, 93.0, M_SCREENF), SCR)
par(sec_box("ScreenFrameB", -16.5, 16.5, 4.0, 6.0, 84.0, 85.0, M_SCREENF), SCR)
par(sec_box("ScreenFrameL", -16.5, -15.5, 4.0, 6.0, 84.0, 93.0, M_SCREENF), SCR)
par(sec_box("ScreenFrameR", 15.5, 16.5, 4.0, 6.0, 84.0, 93.0, M_SCREENF), SCR)
par(box("ScreenMesh", -15.5, 15.5, 4.9, 5.1, 85.0, 92.0, M_MESH), SCR)
par(box("ScreenHandle", -6.0, 6.0, 4.0, 6.0, 93.0, 95.5, M_SCREENF), SCR)
MAT = empty("LintMatPivot", (0, 4.9, 0)); par(MAT, SCR)
bm = bmesh.new(); add_box(bm, -15.2, 15.2, -1.0, 0.0, 85.3, 91.7)
bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=6, use_grid_fill=True)
for v in bm.verts:
    if v.co.y < -0.5: v.co.y -= random.uniform(0.0, 0.35)
LMAT = par(mesh_obj("LintMat", bm, M_LINTS), MAT)
def lift(t):
    if t < C["and"]: return (0.0, 0.0, 15.0 * ease(t / 0.9) - 0.0)
    if t < C["and"] + 0.6: return (0.0, 0.0, 15.0 * (1 - ease((t - C["and"]) / 0.6)))
    if C["so"] <= t < C["use"]: return (0.0, 0.0, 15.0 * ease((t - C["so"]) / 0.5))
    return (0.0, 0.0, 0.0)
bake_loc(SCR, lift)
MATTH = PW([(0, 1.0), (C["and"] + 0.6, 1.0), (C["here"], 0.05), (C["screen"], 0.05), (C["catches"] + 0.2, 0.55), (C["all"], 0.8),
            (C["so"], 0.8), (C["clean"] + 0.1, 0.8), (C["screen2"] + 0.2, 0.0), (C["use"], 0.0), (C["use"] + 0.01, 0.0)])
bake_scale(MAT, lambda t: (1.0, max(0.02, MATTH(t)), 1.0))
lint_keys(NT_LINTS, "Pulse", [(0.0, 0.0), (0.3, 4.0), (C["and"], 4.0), (C["and"] + 0.4, 0.0)])

# ================= duct (cut open at y = 75) =================
FOIL_P = chaikin([Vector(p) for p in [(25, 0, 12), (36, 0, 12), (48, 0, 8), (60, 0, 4.5), (72, 0, 7), (82, 0, 17), (90, 0, 27), (96, 0, 30)]], 3)
WALL_P = [Vector((96, 0, 30)), Vector((104, 0, 30)), Vector((112, 0, 30))]
FULL_P = FOIL_P + WALL_P[1:]
RIG_P = chaikin([Vector(p) for p in [(25, 0, 12), (40, 0, 12), (50, 0, 18), (56, 0, 28), (64, 0, 30), (96, 0, 30)]], 3) + WALL_P[1:]
def duct(name, pts, r, m_, th):
    o = half_pipe(name, pts, [r] * len(pts), m_, seg=40); o.location.y = YD; solidify(o, th); return o
FOIL = duct("FoilDuct", FOIL_P, 5.3, M_FOIL, 0.25)
SLEEVE = duct("WallSleeve", WALL_P, 5.3, M_RIGID, 0.3)
RIGID = duct("RigidDuct", RIG_P[:-2], 5.3, M_RIGID, 0.3)
windows(FOIL, [DIRTY]); windows(RIGID, [(C["rigid"], DUR)])
bake_scale(RIGID, lambda t: (1.0, 1.0, 1.0) if t > C["rigid"] + 0.35 else (1.0, 1.0, max(0.01, pop(t, C["rigid"], 0.3))))
def lining(name, pts, m_):
    o = half_pipe(name, pts, [5.05] * len(pts), m_, seg=40); o.location.y = YD
    md = solidify(o, 0.1); md.use_even_offset = False; md.use_quality_normals = True
    # make the felt grow INWARD whatever the sweep normals are
    me = o.data; p = me.polygons[len(me.polygons) // 2]; c = p.center
    i = min(range(len(pts)), key=lambda k: (pts[k] - Vector((c.x, 0, c.z))).length)
    outward = (c - Vector((pts[i].x, 0.0, pts[i].z))).dot(p.normal) > 0
    md.offset = 1.0 if outward else -1.0      # checked in CPU stills 25 Nov: the other sign grew the felt outward
    return o, md
LINE, LMD = lining("LintLining", FULL_P, M_LINT)
LINE_TH = PW([(0, 3.4), (C["here"] - 0.05, 3.4), (C["here"], 0.12), (C["lint2"], 0.12), (C["kink"] + 0.4, 1.5), (C["load2"], 1.6),
              (C["narrower"] + 0.3, 3.7), (C["so"], 3.7)])
bake_scalar(LINE, 'modifiers["Solid"].thickness', [max(0.05, LINE_TH(t)) for t in TS])
windows(LINE, [DIRTY])
LINR, LRMD = lining("LintLiningRigid", RIG_P, M_LINTR)
bake_scalar(LINR, 'modifiers["Solid"].thickness', [2.2 * ease((t - C["duct3"]) / 0.8) + 0.05 for t in TS])
windows(LINR, [(C["duct3"], C["when"])])
lint_keys(NT_LINTR, "Pulse", [(0.0, 0.0), (C["duct3"], 0.0), (C["duct3"] + 0.3, 1.5), (C["when"], 1.5)])
# danger pulse in the wall (hook 2) + fire front along the duct
lint_keys(NT_LINT, "Pulse", [(0.0, 0.0), (C["and"], 0.0), (C["and"] + 0.3, 2.5), (C["never"] + 0.4, 2.5), (C["here"], 0.0)])
FR0, FR1 = C["and2"], C["wall3"] + 0.4
front_x = lambda t: -100.0 if t < FR0 else 20.0 + (125.0 - 20.0) * lin((t - FR0) / (FR1 - FR0))
lint_keys(NT_LINT, "Front", [(0.0, -500.0), (FR0 - 0.02, -500.0), (FR0, 20.0), (FR1, 125.0)])
lint_keys(NT_LINT, "Fire", [(0.0, 0.0), (FR0 - 0.02, 0.0), (FR0 + 0.2, 6.0), (C["so"] - 0.05, 6.0), (C["so"], 0.0)])
lint_keys(NT_LINTH, "Front", [(0.0, 500.0)])
lint_keys(NT_LINTH, "Fire", [(0.0, 0.0), (C["catch"] - 0.02, 0.0), (C["catch"] + 0.25, 8.0), (C["so"] - 0.05, 8.0), (C["so"], 0.0)])
glowc(B_FOIL, [(0.0, 0.0, RED), (C["foil"] - 0.05, 0.0, RED), (C["foil"] + 0.15, 0.35, RED), (C["kink"] + 0.6, 0.0, RED),
               (C["plastic"] - 0.05, 0.0, RED), (C["plastic"] + 0.1, 0.0, RED)])
glowc(B_RIGID, [(0.0, 0.0, CYAN), (C["rigid"], 0.0, CYAN), (C["rigid"] + 0.2, 0.6, CYAN), (C["duct2"] + 0.6, 0.0, CYAN)])
# ================= exterior hood + flap =================
sec_box("HoodTop", 108, 118, YD, 84, 38, 39, M_HOOD, ycut=YD)
sec_box("HoodBack", 108, 118, 83, 84, 21, 39, M_HOOD, ycut=YD)
sec_box("HoodPlate", 108, 108.6, YD, 84, 18, 42, M_HOOD, ycut=YD)
FLAPP = empty("FlapPivot", (118.0, 0, 38.0))
par(sec_box("FlapPlate", -0.4, 0.4, YD, 83, -16.5, 0.0, M_FLAP, ycut=YD), FLAPP)
def flap_ang(t):
    blocked = C["now"] <= t < C["so"]
    if t < C["here"]: return -0.15
    if blocked: return -0.55 * (1 - ease((t - C["now"]) / 0.8))
    if C["go"] <= t < C["if"]: return -1.05 * ease((t - C["opens"] + 0.2) / 0.4) - 0.45 * (1 - ease((t - C["opens"] + 0.2) / 0.4)) + 0.06 * math.sin(14 * t)
    return -0.45 + 0.05 * math.sin(11 * t)
bake_fn(FLAPP, "rotation_euler", 1, flap_ang)
glowc(B_FLAP, [(0.0, 0.0, CYAN), (C["flap"] - 0.05, 0.0, CYAN), (C["flap"] + 0.15, 0.7, CYAN), (C["if"], 0.0, CYAN)])

# ================= air beads =================
HOT_P = Path(chaikin([Vector(p) for p in [(HX, 30, 16), (HX, 30, 76), (20, 52, 80), (6, 50, 64), (0, 30, 52), (-5, 14, 68), (0, 7, 88.5)]], 2))
AIR_P = Path(chaikin([Vector(p) for p in [(0, 7, 88.5), (-32.7, 8, 88), (-32.7, 8, 16), (-20, 24, 10), (10, 50, 6), (25, 62, 12), (25, 76.5, 12)]], 2)
             + [Vector((p.x, 76.5, p.z)) for p in FULL_P[1:]] + [Vector((119, 76.5, 26)), Vector((134, 76.5, 18))])
FLOW = [(C["heater"], C["now"]), (C["go"], DUR)]
def speed(t):
    if C["now"] <= t < C["so"]: return 6.0
    if C["duct3"] <= t < C["when"]: return 22.0
    return 70.0
S_CUM = [0.0]
for t in TS[1:]: S_CUM.append(S_CUM[-1] + speed(t) / FPS)
def run_beads(name, path, n, r, m_, wins, scale=1.0):
    me = sphere_mesh(name, r); me.materials.append(m_); out = []
    for i in range(n):
        o = obj_from(f"{name}{i}", me)
        vals = [tuple(path.at((S_CUM[k] + i * path.L / n) % path.L)) for k in range(len(TS))]
        for ax in range(3): bake(o, "location", ax, [v[ax] for v in vals])
        windows(o, wins); out.append(o)
    return out
run_beads("HotBead", HOT_P, 26, 0.9, M_HOTB, [(C["heater"], C["so"]), (C["go"], DUR)])
run_beads("AirBead", AIR_P, 70, 0.8, M_AIRB, FLOW)
# escaped fibers riding the air into the duct
FIB_P = Path(AIR_P.p)
fme = sphere_mesh("FiberMe", 0.55, 1); fme.materials.append(M_FIBER)
for i in range(16):
    o = obj_from(f"Fiber{i}", fme); o.scale = (1.8, 0.7, 0.7)
    vals = [tuple(FIB_P.at((S_CUM[k] * 0.8 + i * FIB_P.L / 16) % FIB_P.L)) for k in range(len(TS))]
    for ax in range(3): bake(o, "location", ax, [v[ax] for v in vals])
    windows(o, [(C["but"], C["now"])])

# ================= fire: flames at the heater + along the duct =================
def flame(name, loc, h, r, wins, phase):
    bm = bmesh.new(); add_cyl(bm, r, h, "Z", (0, 0, h / 2), seg=10, r2=0.05); o = mesh_obj(name, bm, M_FLAME); o.location = loc
    bm = bmesh.new(); add_cyl(bm, r * 0.5, h * 0.6, "Z", (0, 0, h * 0.3), seg=8, r2=0.05); par(mesh_obj(name + "C", bm, M_FLAMEC), o)
    t0 = wins[0][0]
    bake_scale(o, lambda t: (1.0, 1.0, max(0.02, ease((t - t0) / 0.5) * (1 + 0.25 * math.sin(2 * math.pi * 7.0 * t + phase) + 0.12 * math.sin(2 * math.pi * 13 * t + 2 * phase)))))
    windows(o, wins); return o
random.seed(5)
for k in range(12):
    flame(f"HFlame{k}", (random.uniform(26.0, 33.5), random.uniform(13.0, 34.0), random.uniform(1.4, 2.5) if k < 7 else 15.0),
          random.uniform(4.0, 9.0), random.uniform(1.0, 1.8), [FIRE_W], random.uniform(0, 6.28))
DPATH = Path(FULL_P)
for k in range(14):
    p = DPATH.at(4.0 + k * (DPATH.L - 6.0) / 13)
    t_pass = FR0 + (FR1 - FR0) * lin((p.x - 20.0) / 105.0)
    flame(f"DFlame{k}", (p.x, YD + 1.5, p.z - 1.8), random.uniform(3.0, 5.0), random.uniform(0.8, 1.3), [(t_pass, C["so"])], random.uniform(0, 6.28))
FIRE_L = bpy.data.lights.new("FireLight", "POINT"); FIRE_L.color = (1.0, 0.45, 0.15); FIRE_L.shadow_soft_size = 6
fl_o = bpy.data.objects.new("FireLight", FIRE_L); scene.collection.objects.link(fl_o); fl_o.location = (HX, 8.0, 14.0)
bake_scalar(FIRE_L, "energy", [0.0 if not (FIRE_W[0] <= t < FIRE_W[1]) else 6.0e4 * ease((t - FIRE_W[0]) / 0.4) * (1 + 0.2 * math.sin(40 * t)) for t in TS])
FIRE_L2 = bpy.data.lights.new("DuctFireLight", "POINT"); FIRE_L2.color = (1.0, 0.45, 0.15); FIRE_L2.shadow_soft_size = 8
fl2 = bpy.data.objects.new("DuctFireLight", FIRE_L2); scene.collection.objects.link(fl2)
bake_loc(fl2, lambda t: (max(25.0, min(110.0, front_x(t))), YD - 12.0, 22.0))
bake_scalar(FIRE_L2, "energy", [0.0 if not (FR0 <= t < C["so"]) else 4.0e4 * (1 + 0.2 * math.sin(33 * t)) for t in TS])
# sparks at ignition (particles)
SPK_EM = box("SparkEmitter", 26, 34, 13, 30, 3.0, 3.4, None); SPK_EM.hide_render = True
pm_spark = fx.particles(SPK_EM, "sparks", F(C["catch"]), F(C["fire3"] + 1.0), count=160)
try:
    ps_ = pm_spark.particle_system.settings; ps_.particle_size = 0.35; ps_.normal_factor = 90; ps_.factor_random = 0.8; ps_.lifetime = 20
    ps_.effector_weights.gravity = 0.15
except Exception as e: print("[fx] spark tune skipped:", e)
# fibers shed by the tumbling clothes (particles)
FIB_EM = cyl("FiberEmitter", 16.0, 1.0, "Y", (0, 30, DZ), None, seg=16); FIB_EM.hide_render = True
pm_fib = fx.particles(FIB_EM, "dust", F(C["every"]), F(C["rest"]), count=260)
try:
    ps_ = pm_fib.particle_system.settings; ps_.particle_size = 0.35; ps_.normal_factor = 14; ps_.factor_random = 1.2; ps_.lifetime = 45
    ps_.effector_weights.gravity = -0.05
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.85, 0.84, 0.82, 1); b_.inputs["Emission Color"].default_value = (0.9, 0.9, 0.9, 1)
    b_.inputs["Emission Strength"].default_value = 0.8
except Exception as e: print("[fx] fiber tune skipped:", e)
# January snow outside (particles)
bm = bmesh.new(); vs_ = [bm.verts.new(v) for v in [(112, 70, 200), (300, 70, 200), (300, 320, 200), (112, 320, 200)]]; bm.faces.new(vs_)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); SNOW_EM = mesh_obj("SnowEmitter", bm, None); SNOW_EM.hide_render = True
pm_snow = fx.particles(SNOW_EM, "rain", 1, F(DUR), count=1600)
try:
    ps_ = pm_snow.particle_system.settings; ps_.particle_size = 0.45; ps_.normal_factor = -22 if SNOW_EM.data.polygons[0].normal.z > 0 else 22; ps_.lifetime = 300; ps_.effector_weights.gravity = 0.02
    ps_.frame_start = -200
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.95, 0.97, 1.0, 1); b_.inputs["Emission Color"].default_value = (0.9, 0.95, 1.0, 1); b_.inputs["Emission Strength"].default_value = 1.2
except Exception as e: print("[fx] snow tune skipped:", e)
# ================= trash bin + lint chunks (rigid body) =================
BINX, BINY = -62.0, 30.0
BIN = lathe_full("Bin", [(12.0, 0.0), (13.0, 0.0), (14.0, 34.0), (13.0, 34.0), (12.0, 1.0), (0.01, 1.0), (0.01, 0.0)], M_BIN, seg=40)
BIN.location = (BINX, BINY, 0.0)
CHUNKS = []
random.seed(9)
for k in range(6):
    me = sphere_mesh(f"ChunkMe{k}", 1.0, 2); o = obj_from(f"LintChunk{k}", me, M_LINTS)
    o.location = (BINX + 4 + random.uniform(-3, 3), BINY + random.uniform(-4, 4), 72 + k * 6.0)
    o.scale = (random.uniform(4, 6), random.uniform(3, 4.5), random.uniform(0.9, 1.4)); o.rotation_euler = (random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), 0)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    try: bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    except Exception as e: print("[build] apply scale skipped", e)
    o.select_set(False); CHUNKS.append(o)
FLOOR_RB = box("FloorRB", -200, 95, -300, 120, -10, 0, None); FLOOR_RB.hide_render = True; FLOOR_RB.display_type = "WIRE"
fx.rigid(CHUNKS, passive=[FLOOR_RB, BIN], mass=0.2, friction=0.8, bounce=0.05)
T_TOSS = C["screen2"] + 0.1
for ch in CHUNKS:
    try:
        rb = ch.rigid_body; rb.kinematic = True; ch.keyframe_insert("rigid_body.kinematic", frame=1)
        ch.keyframe_insert("rigid_body.kinematic", frame=F(T_TOSS)); rb.kinematic = False; ch.keyframe_insert("rigid_body.kinematic", frame=F(T_TOSS) + 1)
    except Exception as e: print("[build] chunk kinematic skipped", e)
    windows_r(ch, [(T_TOSS, DUR)])
# ================= snowy yard: scattered shrubs + rocks (Geometry Nodes) =================
YARD = box("YardScatterSurface", 125, 520, 100, 640, -5.0, -4.9, None)
SHRUB = obj_from("ShrubInst", sphere_mesh("ShrubMe", 1.0, 2), M_SNOW); SHRUB.scale = (14, 14, 9)
fx.scatter(YARD, SHRUB, density=0.0004, scale_min=0.5, scale_max=1.5, seed=4)
YARD.hide_render = False
try: YARD.data.materials.append(M_SNOW)
except Exception: pass

# ---------- glows on the hero parts ----------
glowc(B_COIL, [(0.0, 0.0, ORANGE), (C["heater"] - 0.05, 0.0, ORANGE), (C["heater"] + 0.3, 5.0, ORANGE), (C["heat"], 5.0, ORANGE), (C["heater2"], 10.0, (1.0, 0.3, 0.06)),
               (C["so"] - 0.05, 10.0, (1.0, 0.3, 0.06)), (C["so"], 0.0, ORANGE), (C["go"], 4.0, ORANGE)])
glowc(B_HOUSE, [(0.0, 0.0, RED), (C["heat"], 0.0, RED), (C["heater2"] + 0.2, 0.9, RED), (C["so"] - 0.05, 0.9, RED), (C["so"], 0.0, RED)])
glowc(B_THERMO, [(0.0, 0.0, GOLD), (C["thermostat"] - 0.05, 0.0, GOLD), (C["thermostat"] + 0.15, 1.5, GOLD), (C["fails"] - 0.1, 1.5, GOLD),
                 (C["fails"], 2.5, RED), (C["lint3"], 2.5, RED), (C["lint3"] + 0.5, 0.0, RED)])
glowc(B_SCREENF, [(0.0, 0.0, GOLD), (C["screen"] - 0.05, 0.0, GOLD), (C["screen"] + 0.15, 0.8, GOLD), (C["all"] + 0.4, 0.0, GOLD),
                  (C["screen2"] - 0.05, 0.0, GOLD), (C["screen2"] + 0.15, 0.8, GOLD), (C["use"], 0.0, GOLD)])
for i, (m_, b_) in enumerate(M_CLOTH):
    glowc(b_, [(0.0, 0.0, CYAN), (C["clothes"] - 0.05, 0.0, CYAN), (C["clothes"] + 0.2, 0.25, CYAN), (C["duct3"], 0.25, CYAN), (C["duct3"] + 0.3, 0.0, CYAN)])

# ================= lights + world =================
fx.hdri("night", strength=0.25, rotation_deg=120.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, rot, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o
area("Key", (-60, -200, 220), (math.radians(45), 0, math.radians(-25)), 160, 1.4e5, (1.0, 0.95, 0.88))
area("Rim", (140, 40, 200), (math.radians(-40), 0, math.radians(120)), 120, 4.0e4, (0.6, 0.75, 1.0))
area("Low", (60, -120, 15), (math.radians(95), 0, 0), 90, 1.2e4, (1.0, 0.9, 0.8))
area("DuctKey", (70, 20, 70), (0, 0, 0), 60, 8.0e3, (1.0, 0.97, 0.92))
area("Moon", (300, -50, 300), (math.radians(30), 0, math.radians(70)), 200, 5.0e4, (0.55, 0.65, 1.0))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.5; cam_d.clip_end = 8000
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-30, -52, 118), (0, 5, 99), 36),                                   # hook: the screen slides up, lint glowing
    (C["and"] - 0.05, (-24, -44, 113), (0, 5, 99), 38),
    (C["and"], (128, -42, 52), (101, YD, 31), 36, "cut"),                      # the duct inside the wall, packed + glowing
    (C["here"] - 0.05, (122, -34, 48), (100, YD, 31), 38),
    (C["here"], (30, -270, 66), (30, 40, 52), 27, "cut"),                      # wide: dryer + duct + wall
    (C["heater"] - 0.05, (30, -255, 64), (30, 40, 52), 27),
    (C["heater"], (38, -80, 58), (HX, 25, 50), 36, "cut"),                     # heater coil
    (C["fan"] - 0.05, (37, -74, 56), (HX, 25, 50), 36),
    (C["fan"], (-8, -150, 50), (0, 30, DZ), 30, "cut"),                        # drum + clothes + fan
    (C["every"] - 0.05, (-4, -140, 50), (0, 30, DZ), 30),
    (C["every"], (-6, -85, 60), (0, 30, 60), 34, "cut"),                       # fibers flying
    (C["screen"] - 0.05, (-4, -78, 64), (0, 30, 64), 34),
    (C["screen"], (-14, -46, 98), (0, 5, 89), 36, "cut"),                      # the screen catches most
    (C["rest"] - 0.05, (-10, -42, 96), (0, 5, 89), 36),
    (C["rest"], (28, -95, 30), (32, YD, 14), 32, "cut"),                       # follow the rest into the duct ...
    (C["outside"], (110, -85, 40), (108, YD, 30), 32),                         # ... through the wall to the outside
    (C["lint2"] - 0.05, (112, -82, 40), (110, YD, 30), 32),
    (C["lint2"], (62, -62, 22), (60, YD, 10), 34, "cut"),                      # lint sticks, foil sags + kinks
    (C["load2"] - 0.05, (64, -56, 21), (62, YD, 10), 34),
    (C["load2"], (54, -30, 14), (60, YD, 7), 36, "cut"),                       # load after load: narrower
    (C["now"] - 0.05, (56, -26, 13), (60, YD, 7), 36),
    (C["now"], (125, -80, 42), (100, YD, 30), 32, "cut"),                      # hot air can't get out (flap shut)
    (C["heat"] - 0.05, (123, -76, 41), (100, YD, 30), 32),
    (C["heat"], (38, -80, 56), (HX, 25, 48), 36, "cut"),                       # heat builds around the heater
    (C["safety"] - 0.05, (37, -74, 56), (HX, 25, 50), 36),
    (C["safety"], (40, -46, 90), (HX, 12, 80), 40, "cut"),                     # the safety thermostat
    (C["lint3"] - 0.05, (38, -42, 87), (HX, 12, 79), 40),
    (C["lint3"], (36, -70, 26), (HX, 20, 10), 34, "cut"),                      # lint near the heater ignites
    (C["and2"] - 0.05, (35, -64, 25), (HX, 20, 10), 34),
    (C["and2"], (40, -95, 34), (42, YD, 12), 32, "cut"),                       # the fire runs down the duct ...
    (C["wall3"] + 0.3, (112, -90, 44), (100, YD, 30), 32),                      # ... into the wall
    (C["in"], (40, -340, 90), (45, 60, 55), 26, "cut"),                        # wide: the stat
    (C["january"], (110, -330, 100), (90, 80, 60), 26),                         # drift to the snowy night outside
    (C["so"] - 0.05, (118, -320, 100), (92, 80, 60), 26),
    (C["so"], (-38, -150, 82), (-30, 20, 72), 30, "cut"),                      # clean the screen -> lint in the bin
    (C["use"] - 0.05, (-36, -142, 80), (-30, 20, 70), 30),
    (C["use"], (60, -105, 32), (60, YD, 20), 32, "cut"),                       # rigid metal duct
    (C["go"] - 0.05, (58, -98, 31), (60, YD, 20), 32),
    (C["go"], (160, -62, 46), (116, YD, 30), 34, "cut"),                       # outside: the flap opens
    (C["if"] - 0.05, (154, -56, 44), (116, YD, 30), 34),
    (C["if"], (-6, -120, 52), (0, 30, DZ), 32, "cut"),                         # damp clothes ...
    (C["duct3"], (60, -100, 30), (60, YD, 20), 32, "cut"),                     # ... the duct might be blocked
    (C["when"] - 0.05, (60, -92, 30), (60, YD, 20), 32),
    (C["when"], (40, -280, 72), (40, 45, 50), 27, "cut"),                      # CTA: whole clean system
    (DUR, (40, -320, 80), (40, 45, 50), 27),
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
fx.bake_rigid(F(T_TOSS) - 1, F(C["use"]) + 10)

# ================= export cues, events and projected anchors for the typography =================
AP = {
    "screen": (0.0, 3.4, 88.5), "screen_up": (0.0, 3.4, 103.5), "wall_duct": (101.0, YD, 36.0), "heater": (HX, 12.0, 46.0),
    "coil": (HX, 22.0, 30.0), "drum": (0.0, 10.0, 70.0), "clothes": (0.0, 20.0, 40.0), "fan": (-20.0, 22.0, 10.0),
    "duct": (40.0, YD, 17.0), "foil": (60.0, YD, 0.0), "lining": (62.0, YD, 7.0), "flap": (118.5, YD, 30.0), "thermostat": (HX, 10.0, 81.0),
    "fire": (HX, 12.0, 8.0), "wall": (101.5, YD, 60.0), "bin": (BINX, BINY - 14, 34.0), "rigid": (52.0, YD, 22.0), "outside": (125.0, YD, 30.0),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = Vector(p_)
        if k == "screen_up": p_v = Vector(p_) + Vector((0, 0, SCR.location.z - 15.0))
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"hook": RR(*T_HOOK), "wall": RR(*T_WALL), "how": RR(*T_HOW), "fibers": RR(*T_FIB), "duct": RR(*T_DUCT), "stick": RR(*T_STICK),
          "block": RR(*T_BLOCK), "thermo": RR(*T_THERMO), "ignite": RR(*T_IGNITE), "spread": RR(*T_SPREAD), "stats": RR(*T_STATS),
          "clean": RR(*T_CLEAN), "rigid": RR(*T_RIGID), "flap": RR(*T_FLAP), "slow": RR(*T_SLOW), "cta": RR(*T_CTA),
          "cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4],
          "screen_up": [0.0, round(C["so"], 3)], "screen_down": [round(C["and"], 3)], "coil_on": round(C["heater"], 3),
          "drum": RR(C["fan"], C["screen"]), "flow": [RR(*w) for w in FLOW], "fiber_hits": RR(C["catches"], C["all"]),
          "narrow": RR(C["load2"], C["narrower"] + 0.3), "flap_shut": round(C["now"], 3), "heat_up": round(C["heater2"], 3),
          "thermo_click": round(C["thermostat"], 3), "thermo_fail": round(C["fails"], 3), "ignite_at": round(C["catch"], 3),
          "fire_run": RR(FR0, FR1), "toss": round(T_TOSS, 3), "rigid_pop": round(C["rigid"], 3), "flap_open": round(C["opens"] - 0.2, 3),
          "blocked_ghost": round(C["duct3"], 3)}
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
