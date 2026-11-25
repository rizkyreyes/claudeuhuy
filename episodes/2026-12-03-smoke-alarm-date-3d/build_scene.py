# Smoke alarm expiration date (3d-39): "Every smoke alarm in your house has an expiration date."
# Stake: past it, there's a real chance it stays quiet in a fire. Twist it down, flip it: the date on the back = date of manufacture,
# not installation; ten years from that date it's done (NFPA 72). Inside: a small dark chamber (air in, light out). Photoelectric:
# LED aimed away from the light sensor; smoke scatters light onto the sensor -> horn. Ionization: a speck of americium ionizes the air
# between two charged plates -> weak current; smoke grabs the ions, current drops -> alarm. Over the years dust, bugs, grease and damp
# air get in and coat the sensor/plates; sensitivity drops no matter how often you test it. Code: 10 years (study: ~3 in 10 expected
# to fail by then, CPSC). NFPA: almost 3 in 5 home fire deaths with no alarm or one that didn't work. Read the date, replace the whole alarm.
# Illustrative, 1 unit = 1 cm. Sets: hallway (x ~0, ceiling z 240), studio cutaway alarm at x = 600 (face down, section y = 0, keep y >= 0),
# row of ten alarms at x = 1200. Generic alarm, no brand, no text, no people.
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
random.seed(39)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("every","Every"),("smoke","smoke"),("alarm","alarm"),("expiration","expiration"),("date","date."),("and","And"),("past","past"),
  ("chance","chance"),("quiet","quiet"),("fire","fire."),("twist","Twist"),("down","down"),("flip","flip"),("over","over."),("the","The"),
  ("date2","date"),("back","back"),("made","made,"),("not","not"),("went","went"),("up","up."),("ten","Ten"),("years","years"),("date3","date,"),
  ("done","done."),("inside","Inside"),("small","small"),("dark","dark"),("chamber","chamber"),("air","air"),("but","but"),("light","light."),
  ("photo","photoelectric"),("tiny","tiny"),("light2","light"),("shines","shines"),("across","across"),("aimed","aimed"),("away","away"),
  ("sensor","sensor."),("clean","Clean"),("sensor2","sensor"),("nothing","nothing."),("smoke2","Smoke"),("drifts","drifts"),
  ("particles","particles"),("bounce","bounce"),("onto","onto"),("sensor3","sensor,"),("horn","horn"),("off","off."),("ionization","Ionization"),
  ("use","use"),("speck","speck"),("radioactive","radioactive"),("americium","americium."),("charges","charges"),("plates","plates,"),
  ("weak","weak"),("current","current"),("flows","flows."),("smoke3","Smoke"),("grabs","grabs"),("charged","charged"),("current2","current"),
  ("drops","drops,"),("screams","screams."),("but2","But"),("years2","years,"),("dust","dust,"),("bugs","bugs,"),("grease","grease"),
  ("damp","damp"),("drift","drift"),("chamber2","chamber."),("coat","coat"),("sensor4","sensor"),("plates2","plates."),("sensor5","sensor"),
  ("slowly","slowly"),("loses","loses"),("sensitivity","sensitivity,"),("matter","matter"),("test","test"),("thats","That's"),("code","code"),
  ("ten2","ten"),("years3","years."),("the2","The"),("study","study"),("expected","expected"),("three","three"),("ten3","ten"),("fail","fail"),
  ("then","then."),("and2","And"),("matters","matters."),("almost","Almost"),("three2","three"),("five","five"),("home","home"),
  ("deaths","deaths"),("no","no"),("alarm2","alarm,"),("one","one"),("didnt","didn't"),("work","work."),("so","So"),("pull","pull"),
  ("down2","down"),("read","read"),("date4","date."),("over2","Over"),("ten4","ten"),("years4","years?"),("replace","Replace"),
  ("whole","whole"),("alarm3","alarm."),("when","When"),("check","check"),("date5","date"),("yours","yours?"),("tell","Tell"),
  ("comments","comments.")]
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
CL = coll("SmokeAlarm")
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
X0, X1 = 600.0, 1200.0                       # studio cutaway set, row-of-ten set
CEIL = 240.0
REST_Z = CEIL - 0.8                          # alarm top (local z 0) under the 0.8 cm base plate
LOW_Z = 215.0                                # alarm pulled down + flipped
# ---------- beat windows ----------
SM1 = (C["and"], C["twist"])                 # smoke under the ceiling, alarm silent
SM2 = (C["and2"], C["so"])
PHOTO_W = [(0.0, C["ionization"]), (C["but2"], C["plates2"] - 0.06), (C["sensor5"] - 0.06, DUR)]
ION_W = [(C["ionization"], C["but2"]), (C["plates2"] - 0.06, C["sensor5"] - 0.06)]
PUFF_W = [(C["smoke2"] - 0.1, C["ionization"], "photo"), (C["smoke3"] - 0.1, C["but2"], "ion"), (C["sensor5"] - 0.1, C["thats"], "weak")]
HORN_T = [(C["horn"], C["ionization"] - 0.1), (C["screams"] - 0.15, C["but2"] - 0.05), (C["test"] + 0.12, C["thats"] - 0.05)]

# ---------- materials ----------
M_SEC, B_SEC = mat("CutFace", (0.90, 0.38, 0.06), rough=0.5, emit_rgb=(1.0, 0.40, 0.08)); B_SEC.inputs["Emission Strength"].default_value = 0.12
GOLD, CYAN, RED, ORANGE, GREEN = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.15), (0.25, 1.0, 0.35)
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
    bm = bmesh.new(); add_box(bm, x0, x1, max(y0, ycut), y1, z0, z1)
    o = mesh_obj(name, bm, [m_, M_SEC]); mark_caps(o, ycut); return o
def half_lathe(name, prof, m_, loc, seg=48):
    """Lathe over y >= 0 (angle 0..pi); the two cut faces at y = 0 get the orange section material."""
    o = lathe(name, prof, m_, a0=0.0, ang=math.pi, seg=seg, loc=loc)
    me = o.data; me.materials.append(M_SEC)
    for p in me.polygons:
        if all(abs(me.vertices[v].co.y) < 1e-3 for v in p.vertices): p.material_index = 1
    return o
def lathe_full(name, prof, m_, seg=64, loc=(0, 0, 0)):
    o = lathe(name, prof, m_, a0=0.0, ang=2 * math.pi, seg=seg, loc=loc)
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4); bm.to_mesh(o.data); bm.free()
    return o
M_OLD, B_OLD = mat("OldEnamel", (0.84, 0.79, 0.64), rough=0.45, emit_rgb=RED)            # ten-year-old, yellowed plastic
M_NEW, B_NEW = mat("NewEnamel", (0.93, 0.93, 0.94), rough=0.35, emit_rgb=CYAN)
M_WHITE, _ = mat("StudioShell", (0.86, 0.84, 0.78), rough=0.4)
M_VENT, _ = mat("Vent", (0.05, 0.05, 0.055), rough=0.6)
M_LABEL, B_LABEL = mat("Label", (0.95, 0.95, 0.92), rough=0.6, emit_rgb=GOLD)
M_INK, _ = mat("LabelInk", (0.08, 0.08, 0.09), rough=0.6)
M_DATE, B_DATE = mat("DateLine", (0.08, 0.08, 0.09), rough=0.6, emit_rgb=GOLD)
M_BLACK, _ = mat("Chamber", (0.015, 0.015, 0.018), rough=0.55)
M_PCB, _ = mat("PCB", (0.05, 0.28, 0.14), rough=0.4)
M_CHIP, _ = mat("Chip", (0.03, 0.03, 0.035), rough=0.3)
M_SOLDER, _ = mat("Solder", (0.75, 0.75, 0.78), rough=0.2, metallic=1.0)
M_BATT, _ = mat("Battery", (0.06, 0.10, 0.22), rough=0.4)
M_BATTT, _ = mat("BatteryTop", (0.75, 0.62, 0.30), rough=0.25, metallic=1.0)
M_BRASS, B_BRASS = mat("HornBrass", (0.80, 0.60, 0.28), rough=0.25, metallic=1.0, emit_rgb=GOLD)
M_HORNC, _ = mat("HornCup", (0.85, 0.85, 0.82), rough=0.4)
M_LEDH, _ = mat("LEDHousing", (0.10, 0.10, 0.12), rough=0.3)
M_LEDT, B_LEDT = emit_mat("LEDTip", CYAN, 0.0)
M_DIODE, B_DIODE = mat("Diode", (0.05, 0.05, 0.06), rough=0.25, emit_rgb=GOLD)
M_BEAM, B_BEAM = emit_mat("Beam", CYAN, 0.0)
M_RAY, B_RAY = emit_mat("Ray", (0.55, 0.97, 1.0), 0.0)
M_CUP, _ = mat("IonCup", (0.62, 0.63, 0.66), rough=0.25, metallic=1.0)
M_PLUS, B_PLUS = mat("PlateTop", (0.65, 0.65, 0.68), rough=0.2, metallic=1.0, emit_rgb=RED)
M_MINUS, B_MINUS = mat("PlateBottom", (0.65, 0.65, 0.68), rough=0.2, metallic=1.0, emit_rgb=CYAN)
M_AM, B_AM = mat("Americium", (0.35, 0.36, 0.30), rough=0.3, metallic=0.6, emit_rgb=(0.75, 1.0, 0.25))
M_IONP, B_IONP = emit_mat("IonPlus", GOLD, 5.0)
M_IONM, B_IONM = emit_mat("IonMinus", CYAN, 5.0)
M_CUR, B_CUR = emit_mat("Current", GOLD, 6.0)
M_WIRE, _ = mat("Wire", (0.55, 0.30, 0.12), rough=0.3, metallic=1.0)
M_SMOKE, B_SMOKE = mat("SmokePuff", (0.42, 0.42, 0.44), rough=1.0, alpha=0.75)
M_FILM, _ = mat("Grime", (0.36, 0.31, 0.24), rough=0.95, noise=12)
M_GREASE, _ = mat("Grease", (0.75, 0.45, 0.08), rough=0.08)
M_DAMP, _ = mat("Damp", (0.55, 0.80, 1.0), rough=0.05)
M_BUG, _ = mat("Bug", (0.05, 0.04, 0.03), rough=0.35)
for _m in (M_GREASE, M_DAMP):
    _b = bsdf_of(_m); _b.inputs["Transmission Weight"].default_value = 0.6; _b.inputs["IOR"].default_value = 1.33
M_FLOOR = tiles("FloorBoards", (0.36, 0.24, 0.15), (0.31, 0.20, 0.12), 0.012, plane="XY")
M_WALL, _ = mat("HallWall", (0.62, 0.60, 0.56), rough=0.85)
M_CEIL, _ = mat("Ceiling", (0.88, 0.88, 0.86), rough=0.9)
M_TRIM, _ = mat("Trim", (0.92, 0.92, 0.90), rough=0.5)
M_RUG, _ = mat("Rug", (0.32, 0.08, 0.07), rough=1.0, noise=4)
M_FRAME, _ = mat("Frame", (0.08, 0.06, 0.05), rough=0.4)
M_ART, _ = mat("Art", (0.20, 0.35, 0.45), rough=0.8, noise=1.2)
M_FIREGLOW, B_FIREGLOW = emit_mat("FireGlow", (1.0, 0.45, 0.12), 0.0)
M_LAMP, B_LAMP = emit_mat("CeilingLamp", (1.0, 0.92, 0.80), 6.0)
M_TABLE, _ = mat("Table", (0.07, 0.07, 0.08), rough=0.35)
M_STUDIO, _ = mat("StudioFloor", (0.035, 0.04, 0.05), rough=0.6)

# ================= alarm parts (local: top/back z = 0, face down to z = -4.05) =================
BODY = [(0.001, 0.0), (6.6, 0.0), (6.8, -0.3), (6.8, -2.4), (6.0, -3.6), (3.0, -4.0), (0.001, -4.05)]
SHELL = [(0.001, 0.0), (6.6, 0.0), (6.8, -0.3), (6.8, -2.4), (6.0, -3.6), (3.0, -4.0), (0.001, -4.0), (0.001, -3.8), (2.9, -3.8),
         (5.8, -3.4), (6.6, -2.35), (6.6, -0.3), (6.45, -0.2), (0.001, -0.2)]
def vent_bm(a0=0.0, a1=2 * math.pi, n=22, half=False):
    bm = bmesh.new()
    for k in range(n):
        a = a0 + (a1 - a0) * (k + 0.5) / n
        if half and (a < 0.18 or a > math.pi - 0.18): continue
        vs = add_box(bm, -0.25, 0.25, -0.08, 0.08, -2.15, -1.0)
        bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a + math.pi / 2, 3, "Z"))
        bmesh.ops.translate(bm, verts=vs, vec=(6.78 * math.cos(a), 6.78 * math.sin(a), 0))
    return bm
ME_BODY = lathe_full("_BodyTmp", BODY, M_OLD, seg=72).data
ME_VENT = mesh_obj("_VentTmp", vent_bm(), M_VENT).data
ME_BTN = cyl("_BtnTmp", 0.9, 0.4, "Z", (0, 0, -4.2), M_OLD, seg=32).data
ME_LABEL = box("_LabelTmp", -3.0, 3.0, -1.8, 1.8, 0.0, 0.06, M_LABEL).data
_bm = bmesh.new()
for (x0, x1, y0, y1) in [(-2.4, 2.4, 1.25, 1.45), (-2.4, 2.2, -0.45, -0.2), (-2.4, 1.6, -1.25, -1.0), (1.3, 2.4, 0.4, 1.0)]: add_box(_bm, x0, x1, y0, y1, 0.06, 0.075)
ME_INK = mesh_obj("_InkTmp", _bm, M_INK).data
ME_DATE = box("_DateTmp", -2.4, 1.0, 0.35, 1.0, 0.06, 0.08, M_DATE).data
for _n in ("_BodyTmp", "_VentTmp", "_BtnTmp", "_LabelTmp", "_InkTmp", "_DateTmp"): bpy.data.objects.remove(bpy.data.objects[_n])
def assembly(name, body_mat, led_rgb, loc=(0, 0, 0), rot=(0, 0, 0), label=True):
    """Whole alarm: the body mesh is the root (rigid-body friendly); vent band, test button, LED, label are children."""
    root = bpy.data.objects.new(name, ME_BODY); CL.objects.link(root); root.location = loc; root.rotation_euler = rot
    root.material_slots[0].link = "OBJECT"; root.material_slots[0].material = body_mat
    kids = []
    for nm, me in [("Vent", ME_VENT), ("Btn", ME_BTN)] + ([("Label", ME_LABEL), ("Ink", ME_INK), ("Date", ME_DATE)] if label else []):
        o = bpy.data.objects.new(f"{name}{nm}", me); CL.objects.link(o); par(o, root); kids.append(o)
        if nm == "Btn": o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = body_mat
    lm, lb = emit_mat(f"{name}LED", led_rgb, 0.0)
    led = obj_from(f"{name}LED", sphere_mesh(f"{name}LEDMe", 0.2, 2), lm, (0.0, -4.5, -3.85)); par(led, root)
    return root, lb

# ================= hallway set =================
box("HallFloor", -120, 120, -320, 200, -2, 0, M_FLOOR)
box("HallCeiling", -120, 120, -320, 200, CEIL, CEIL + 4, M_CEIL)
box("WallL", -122, -120, -320, 200, 0, CEIL, M_WALL)
box("WallR", 120, 122, -320, 200, 0, CEIL, M_WALL)
box("BackWallA", -120, 30, 200, 203, 0, CEIL, M_WALL)
box("BackWallB", 30, 110, 200, 203, 208, CEIL, M_WALL)
box("BackWallC", 110, 120, 200, 203, 0, CEIL, M_WALL)
for nm, (x0, x1, z0, z1) in {"DoorL": (27, 30, 0, 211), "DoorR": (110, 113, 0, 211), "DoorT": (27, 113, 208, 211)}.items():
    box(nm, x0, x1, 199, 203.5, z0, z1, M_TRIM)
box("BaseL", -119.5, -118.5, -320, 200, 0, 10, M_TRIM); box("BaseR", 118.5, 119.5, -320, 200, 0, 10, M_TRIM)
box("Rug", -45, 45, -160, 185, 0, 0.4, M_RUG)
box("FrameL", -119.8, -118.6, 30, 110, 120, 180, M_FRAME); box("ArtL", -118.7, -118.4, 34, 106, 124, 176, M_ART)
box("FrameR", 118.6, 119.8, -120, -50, 125, 175, M_FRAME); box("ArtR", 118.4, 118.7, -116, -54, 129, 171, M_ART)
FIREBOX = box("FireGlowPlane", 20, 125, 235, 237, 0, 230, M_FIREGLOW)
box("NextRoomFloor", 20, 125, 203, 240, -2, 0, M_FLOOR)
lamp = cyl("CeilingLamp", 15.0, 3.0, "Z", (0, 120, CEIL - 1.5), M_LAMP, seg=48)
glow(B_FIREGLOW, [(0.0, 0.0), (SM1[0] - 0.05, 0.0), (SM1[0] + 0.6, 6.0), (SM1[1] - 0.05, 6.0), (SM1[1], 0.0),
                  (SM2[0] - 0.05, 0.0), (SM2[0] + 0.6, 6.0), (SM2[1] - 0.05, 6.0), (SM2[1], 0.0)])
glow(B_LAMP, [(0.0, 6.0), (SM1[0] - 0.05, 6.0), (SM1[0], 2.0), (SM1[1] - 0.05, 2.0), (SM1[1], 6.0),
              (SM2[0] - 0.05, 6.0), (SM2[0], 2.0), (SM2[1] - 0.05, 2.0), (SM2[1], 6.0)])
BASE = cyl("CeilingBase", 6.2, 0.8, "Z", (0, 0, CEIL - 0.4), M_OLD, seg=64)
# smoke layer under the ceiling: a volume slab that grows down + particle wisps
_bm = bmesh.new(); add_box(_bm, -119, 119, -318, 199, -85, -0.1)
SMOKEV = mesh_obj("SmokeLayer", _bm, None); SMOKEV.location = (0, 0, CEIL)
m_sv = bpy.data.materials.new("SmokeVolume")
try: m_sv.use_nodes = True
except Exception: pass
_nt = m_sv.node_tree; _out = next(n for n in _nt.nodes if n.type == "OUTPUT_MATERIAL")
for n in list(_nt.nodes):
    if n.type != "OUTPUT_MATERIAL": _nt.nodes.remove(n)
_pv = _nt.nodes.new("ShaderNodeVolumePrincipled"); _pv.inputs["Color"].default_value = (0.62, 0.60, 0.58, 1)
_nt.links.new(_pv.outputs[0], _out.inputs["Volume"])
keyval(_pv.inputs["Density"], [(0.0, 0.0), (SM1[0], 0.001), (SM1[0] + 2.5, 0.006), (SM1[1], 0.006), (SM1[1] + 0.05, 0.0),
                               (SM2[0], 0.002), (SM2[0] + 2.5, 0.007), (SM2[1], 0.007), (SM2[1] + 0.05, 0.0)])
SMOKEV.data.materials.append(m_sv)
bake_scale(SMOKEV, lambda t: (1, 1, 0.15 + 0.85 * max(ease((t - SM1[0]) / 3.0) if SM1[0] <= t < SM1[1] else 0.0,
                                                   ease((t - SM2[0]) / 3.0) if SM2[0] <= t < SM2[1] else 0.0)))
windows(SMOKEV, [SM1, SM2])
_bm = bmesh.new(); bmesh.ops.create_grid(_bm, x_segments=8, y_segments=8, size=1.0)
bmesh.ops.scale(_bm, verts=_bm.verts, vec=(110, 120, 1)); bmesh.ops.translate(_bm, verts=_bm.verts, vec=(0, 60, 0))
bmesh.ops.reverse_faces(_bm, faces=_bm.faces)
SMOKE_EM = mesh_obj("SmokeEmitter", _bm, None); SMOKE_EM.location = (0, 0, CEIL - 12)
fx.particles(SMOKE_EM, "dust", F(SM1[0]), F(SM2[1]), count=2400)
try:
    ps_ = SMOKE_EM.particle_systems[0].settings
    ps_.particle_size = 2.4; ps_.size_random = 0.7; ps_.lifetime = 150; ps_.normal_factor = 8.0; ps_.factor_random = 6.0
    ps_.effector_weights.gravity = 0.0; ps_.brownian_factor = 4.0
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.30, 0.29, 0.28, 1); b_.inputs["Alpha"].default_value = 0.45; b_.inputs["Roughness"].default_value = 1.0
    ps_.instance_object.data.shade_smooth()
    SMOKE_EM.show_instancer_for_render = False
except Exception as e: print("[fx] smoke tune skipped:", e)
windows(SMOKE_EM, [SM1, SM2])

# ---------- the old alarm (keyed): twist down, flip, back up for the stat beat, down again before "Replace" ----------
AL, B_ALLED = assembly("OldAlarm", M_OLD, GREEN, (0, 0, REST_Z))
T_DROP = C["replace"]
ZK = [(0.0, REST_Z), (C["down"] - 0.1, REST_Z), (C["over"] + 0.2, LOW_Z), (20.0, LOW_Z), (20.05, REST_Z), (C["down2"] - 0.15, REST_Z), (C["date4"], LOW_Z)]
RZK = [(0.0, 0.0), (C["twist"], 0.0), (C["down"] + 0.1, 0.75), (20.0, 0.75), (20.05, 0.0), (C["pull"], 0.0), (C["down2"] + 0.1, 0.75)]
RXK = [(0.0, 0.0), (C["flip"] - 0.05, 0.0), (C["over"] + 0.45, math.pi), (20.0, math.pi), (20.05, 0.0), (C["down2"], 0.0), (C["read"] + 0.2, math.pi)]
fz, frz, frx = PW(ZK), PW(RZK), PW(RXK)
bake_loc(AL, lambda t: (0.0, 0.0, fz(t)))
bake_rot(AL, lambda t: (frx(t), 0.0, frz(t)))
windows(AL, [(0.0, C["no"]), (C["one"], T_DROP)])
# LED: green blink while it "works" (hook), dark while the smoke rolls in, a slow red blink while the date is read
_k = [(0.0, 0.0, GREEN)]
t_ = 0.2
while t_ < C["and"] - 0.3: _k += [(t_, 0.0, GREEN), (t_ + 0.05, 6.0, GREEN), (t_ + 0.25, 6.0, GREEN), (t_ + 0.3, 0.0, GREEN)]; t_ += 1.1
glowc(B_ALLED, _k + [(C["and"], 0.0, GREEN), (C["over2"], 0.0, RED), (C["over2"] + 0.1, 5.0, RED), (C["replace"], 5.0, RED)])
# label date line: gold on "date"/"made", red on "Over ten years?"
glowc(B_DATE, [(0.0, 0.0, GOLD), (C["date2"] - 0.05, 0.0, GOLD), (C["date2"] + 0.15, 3.0, GOLD), (C["ten"] + 1.0, 3.0, GOLD), (C["done"], 3.0, RED),
               (C["inside"], 0.0, RED), (C["read"] - 0.05, 0.0, GOLD), (C["read"] + 0.15, 3.0, GOLD), (C["over2"] - 0.05, 3.0, GOLD), (C["over2"] + 0.1, 4.0, RED)])
glowc(B_OLD, [(0.0, 0.0, RED), (C["done"] - 0.05, 0.0, RED), (C["done"] + 0.1, 0.35, RED), (C["inside"], 0.0, RED),
              (C["over2"] - 0.05, 0.0, RED), (C["over2"] + 0.15, 0.35, RED), (T_DROP + 1.5, 0.35, RED)])
# ten-year ring: 10 segments light one by one over "Ten years from that date", all red on "done"
RING = []
for k in range(10):
    a = math.radians(90 + k * 36)
    bm = bmesh.new(); vs = add_box(bm, -1.55, 1.55, -0.3, 0.3, -0.3, 0.3)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a + math.pi / 2, 3, "Z"))
    bmesh.ops.translate(bm, verts=vs, vec=(9.0 * math.cos(a), 9.0 * math.sin(a), -2.0))
    m_, b_ = emit_mat(f"Ring{k}", GOLD, 0.0); o = mesh_obj(f"TenRing{k}", bm, m_); par(o, AL); RING.append(o)
    t_on = C["ten"] + (C["date3"] + 0.3 - C["ten"]) * k / 9
    glowc(b_, [(0.0, 0.0, GOLD), (t_on - 0.02, 0.0, GOLD), (t_on + 0.08, 5.0, GOLD), (C["done"] - 0.05, 5.0, GOLD), (C["done"] + 0.05, 7.0, RED), (C["inside"], 0.0, RED)])
    windows(o, [(C["ten"] - 0.05, C["inside"])])
# rigid-body copy that falls on "Replace", and the new alarm that pops onto the base
RB, B_RBLED = assembly("OldAlarmRB", M_OLD, RED, (0, 0, LOW_Z), (math.pi, 0, 0.75))
glowc(B_RBLED, [(0.0, 5.0, RED)])
FLOOR_RB = box("FloorRB", -120, 120, -320, 200, -10, 0, None); FLOOR_RB.hide_render = True; FLOOR_RB.display_type = "WIRE"
fx.rigid([RB], passive=[FLOOR_RB], mass=0.3, friction=0.6, bounce=0.25)
try:
    rb = RB.rigid_body; rb.kinematic = True; RB.keyframe_insert("rigid_body.kinematic", frame=1)
    RB.keyframe_insert("rigid_body.kinematic", frame=F(T_DROP)); rb.kinematic = False; RB.keyframe_insert("rigid_body.kinematic", frame=F(T_DROP) + 1)
except Exception as e: print("[build] RB kinematic skipped", e)
for o in [RB] + list(RB.children): windows_r(o, [(T_DROP, DUR)])
NEW, B_NEWLED = assembly("NewAlarm", M_NEW, GREEN, (0, 0, REST_Z), label=False)
T_NEW = C["whole"] - 0.1
bake_scale(NEW, lambda t: (pop(t, T_NEW, 0.3),) * 3)
windows(NEW, [(T_NEW, DUR)])
glowc(B_NEWLED, [(0.0, 0.0, GREEN), (T_NEW + 0.3, 0.0, GREEN), (T_NEW + 0.45, 4.0, GREEN)])
glowc(B_NEW, [(0.0, 0.0, CYAN), (T_NEW, 0.0, CYAN), (T_NEW + 0.2, 0.6, CYAN), (C["when"], 0.0, CYAN)])
NEWRING = torus("NewGlowRing", 8.6, 0.25, emit_mat("NewRing", CYAN, 5.0)[0], (0, 0, REST_Z - 2.0))
bake_scale(NEWRING, lambda t: (pop(t, T_NEW + 0.15, 0.35),) * 3)
windows(NEWRING, [(T_NEW + 0.15, C["when"])])

# ================= studio cutaway alarm (x = X0, face down, section y = 0) =================
box("StudioFloor", X0 - 400, X0 + 400, -300, 400, -60, -59, M_STUDIO)
box("StudioBack", X0 - 400, X0 + 400, 150, 152, -60, 200, M_STUDIO)
SH = half_lathe("CutShell", SHELL, M_WHITE, (X0, 0, 0), seg=64)
SHB = half_lathe("CutBasePlate", [(0.001, 0.0), (6.2, 0.0), (6.2, 0.8), (0.001, 0.8)], M_WHITE, (X0, 0, 0), seg=64)
VH = mesh_obj("CutVents", vent_bm(0.0, math.pi, 22, half=True), M_VENT); VH.location = (X0, 0, 0)
# the front half of the cover slides off toward the camera on "Inside"
FRONT = lathe("FrontShell", SHELL, M_WHITE, a0=math.pi, ang=math.pi, seg=64, loc=(X0, 0, 0))
VF = mesh_obj("FrontVents", vent_bm(math.pi, 2 * math.pi, 22), M_VENT); par(VF, FRONT)
_ft = C["inside"] + 0.15
bake_loc(FRONT, lambda t: (X0, -26.0 * ease((t - _ft) / 0.9), -3.0 * ease((t - _ft) / 0.9)))
windows(FRONT, [(0.0, _ft + 1.0)])
BTN = half_lathe("CutButton", [(0.001, -3.95), (0.9, -3.95), (0.9, -4.35), (0.001, -4.35)], M_WHITE, (X0, 0, 0), seg=32)
_pt = C["test"]
bake_loc(BTN, lambda t: (X0, 0, 0.15 * (ease((t - _pt) / 0.12) - ease((t - _pt - 0.35) / 0.15))))
LEDS, B_LEDS = emit_mat("StudioLED", RED, 0.0)
obj_from("StudioLED", sphere_mesh("StudioLEDMe", 0.2, 2), LEDS, (X0, 4.5, -3.85))
_k = [(0.0, 0.0, RED)]
for a, b in HORN_T:
    t_ = a
    while t_ < b - 0.1: _k += [(t_, 0.0, RED), (t_ + 0.04, 8.0, RED), (t_ + 0.18, 8.0, RED), (t_ + 0.22, 0.0, RED)]; t_ += 0.4
glowc(B_LEDS, _k)
# circuit board, chips, battery, horn
sec_box("PCB", X0 - 5.6, X0 + 5.6, 0, 5.2, -1.15, -0.95, M_PCB)
for k, (x, y, w, d) in enumerate([(-3.2, 2.6, 1.4, 1.0), (3.4, 3.4, 1.0, 1.0), (2.6, 1.0, 0.7, 0.5), (-1.0, 4.2, 0.9, 0.6), (4.6, 1.6, 0.5, 0.9)]):
    sec_box(f"Chip{k}", X0 + x - w / 2, X0 + x + w / 2, max(0.0, y - d / 2), y + d / 2, -1.4, -1.15, M_CHIP)
for k in range(14):
    x, y = random.uniform(-5.2, 5.2), random.uniform(0.3, 4.8)
    if abs(x) < 2.5 and y < 2.5: continue
    cyl(f"Solder{k}", 0.1, 0.08, "Z", (X0 + x, y, -1.19), M_SOLDER, seg=8)
sec_box("Battery", X0 - 5.4, X0 - 3.3, 0, 1.6, -3.2, -1.2, M_BATT)
sec_box("BatteryTop", X0 - 5.4, X0 - 3.3, 0, 1.6, -1.35, -1.2, M_BATTT)
HORNC = half_lathe("HornCup", [(1.2, -1.2), (1.35, -1.2), (1.35, -3.3), (1.2, -3.3)], M_HORNC, (X0 + 3.9, 0, 0), seg=32)
HORN = half_lathe("HornDisc", [(0.001, -2.9), (1.15, -2.9), (1.15, -3.0), (0.001, -3.0)], M_BRASS, (X0 + 3.9, 0, 0), seg=32)
half_lathe("HornCeramic", [(0.001, -2.86), (0.7, -2.86), (0.7, -2.9), (0.001, -2.9)], M_HORNC, (X0 + 3.9, 0, 0), seg=32)
def horn_on(t): return any(a <= t < b for a, b in HORN_T)
bake_loc(HORN, lambda t: (X0 + 3.9, 0.0, (0.04 * math.sin(t * 2 * math.pi * 9.0) if horn_on(t) else 0.0)))
_k = [(0.0, 0.0, GOLD)]
for a, b in HORN_T: _k += [(a - 0.02, 0.0, GOLD), (a + 0.08, 2.5, GOLD), (b - 0.05, 2.5, GOLD), (b + 0.05, 0.0, GOLD)]
glowc(B_BRASS, _k)
# ---------- photoelectric chamber: dark wall, labyrinth vanes, LED + beam, light trap, light sensor ----------
CZ0, CZ1, CR = -3.45, -1.45, 2.2
BZ = -2.45                                    # beam height
PHOTO = []
PHOTO.append(half_lathe("ChamberWall", [(2.1, CZ0), (CR, CZ0), (CR, CZ1), (2.1, CZ1)], M_BLACK, (X0, 0, 0), seg=48))
PHOTO.append(half_lathe("ChamberLid", [(0.001, CZ1), (CR, CZ1), (CR, CZ1 + 0.1), (0.001, CZ1 + 0.1)], M_BLACK, (X0, 0, 0), seg=48))
PHOTO.append(half_lathe("ChamberFloor", [(0.001, CZ0 - 0.1), (CR, CZ0 - 0.1), (CR, CZ0), (0.001, CZ0)], M_BLACK, (X0, 0, 0), seg=48))
bm = bmesh.new()
VANES = []
for k in range(11):
    a = math.radians(14 + k * 15.2)
    vs = add_box(bm, -0.42, 0.42, -0.04, 0.04, CZ0, CZ1)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a + math.radians(55), 3, "Z"))
    bmesh.ops.translate(bm, verts=vs, vec=(1.72 * math.cos(a), 1.72 * math.sin(a), 0)); VANES.append(a)
VANE_O = mesh_obj("Labyrinth", bm, M_BLACK); VANE_O.location = (X0, 0, 0); PHOTO.append(VANE_O)
LEDP = (-1.25, 0.55, BZ); TRAP = (1.35, 0.55, BZ); DIODE = (0.15, 1.25, BZ)
PHOTO.append(cyl("LEDBody", 0.2, 0.45, "X", (X0 + LEDP[0] - 0.2, LEDP[1], BZ), M_LEDH, seg=16))
PHOTO.append(obj_from("LEDTip", sphere_mesh("LEDTipMe", 0.17, 2), M_LEDT, (X0 + LEDP[0] + 0.05, LEDP[1], BZ)))
PHOTO.append(box("LightTrap", X0 + TRAP[0], X0 + TRAP[0] + 0.3, TRAP[1] - 0.3, TRAP[1] + 0.3, BZ - 0.3, BZ + 0.3, M_BLACK))
PHOTO.append(box("DiodeBody", X0 + DIODE[0] - 0.3, X0 + DIODE[0] + 0.3, DIODE[1], DIODE[1] + 0.35, BZ - 0.3, BZ + 0.3, M_LEDH))
DLENS = cyl("DiodeLens", 0.2, 0.06, "Y", (X0 + DIODE[0], DIODE[1] - 0.02, BZ), M_DIODE, seg=24); PHOTO.append(DLENS)
BEAM = cyl("Beam", 0.09, TRAP[0] - LEDP[0] - 0.1, "X", (X0 + (LEDP[0] + TRAP[0]) / 2 + 0.05, LEDP[1], BZ), M_BEAM, seg=16); PHOTO.append(BEAM)
glow(B_LEDT, [(0.0, 0.0), (C["light2"] - 0.05, 0.0), (C["light2"] + 0.15, 6.0)])
glow(B_BEAM, [(0.0, 0.0), (C["light2"] - 0.05, 0.0), (C["light2"] + 0.25, 3.0)])
glowc(B_DIODE, [(0.0, 0.0, GOLD), (C["sensor"] - 0.05, 0.0, GOLD), (C["sensor"] + 0.15, 0.6, GOLD), (C["clean"], 0.0, GOLD),
                (C["onto"] - 0.05, 0.0, GOLD), (C["onto"] + 0.2, 4.0, GOLD), (C["ionization"] - 0.1, 4.0, GOLD), (C["ionization"], 0.0, GOLD),
                (C["sensor4"] - 0.05, 0.0, GOLD), (C["sensor4"] + 0.15, 1.0, RED), (C["plates2"], 0.0, RED),
                (C["sensitivity"] - 0.3, 0.0, GOLD), (C["sensitivity"], 0.5, GOLD), (C["thats"], 0.5, GOLD)])
for o in PHOTO: windows(o, PHOTO_W)
# ---------- ionization chamber: metal cup, + / - plates, americium speck, ions, the current loop ----------
ION = []
ION.append(half_lathe("IonCup", [(1.45, CZ0), (1.55, CZ0), (1.55, CZ1), (1.45, CZ1)], M_CUP, (X0, 0, 0), seg=48))
ION.append(half_lathe("PlateTop", [(0.001, -1.95), (1.3, -1.95), (1.3, -1.85), (0.001, -1.85)], M_PLUS, (X0, 0, 0), seg=48))
ION.append(half_lathe("PlateBottom", [(0.001, -3.05), (1.3, -3.05), (1.3, -2.95), (0.001, -2.95)], M_MINUS, (X0, 0, 0), seg=48))
AMS = half_lathe("AmericiumSpeck", [(0.001, -2.95), (0.28, -2.95), (0.28, -2.88), (0.001, -2.88)], M_AM, (X0, 0, 0), seg=24); ION.append(AMS)
WIRE_PTS = [(X0 + 1.3, 0.35, -1.9), (X0 + 2.6, 0.35, -1.9), (X0 + 2.6, 0.35, -3.0), (X0 + 1.3, 0.35, -3.0)]
ION.append(poly_obj("CurrentWire", WIRE_PTS, 0.05, M_WIRE))
glowc(B_AM, [(0.0, 0.0, (0.75, 1.0, 0.25)), (C["speck"] - 0.05, 0.0, (0.75, 1.0, 0.25)), (C["speck"] + 0.2, 4.0, (0.75, 1.0, 0.25))])
glowc(B_PLUS, [(0.0, 0.0, RED), (C["plates"] - 0.05, 0.0, RED), (C["plates"] + 0.15, 1.2, RED), (C["but2"], 1.2, RED)])
glowc(B_MINUS, [(0.0, 0.0, CYAN), (C["plates"] - 0.05, 0.0, CYAN), (C["plates"] + 0.15, 1.2, CYAN), (C["but2"], 1.2, CYAN)])
for o in ION: windows(o, ION_W)
# grime on the plates (shown on "the plates")
for nm, z in (("GrimeTop", -1.98), ("GrimeBot", -2.92)):
    g = half_lathe(nm, [(0.001, z), (1.25, z), (1.25, z + 0.05), (0.001, z + 0.05)], M_FILM, (X0, 0, 0), seg=48); windows(g, [ION_W[1]])

# ---------- smoke puffs (shared by the photo + ion + weak-sensor beats) ----------
NP = 9
PUFFS, PUFF_FN = [], []
for i in range(NP):
    a = math.radians(random.uniform(25, 155)); start = Vector((7.6 * math.cos(a), max(0.4, 7.6 * math.sin(a)), random.uniform(-2.6, -1.8)))
    tgt_photo = Vector((random.uniform(-0.8, 1.0), LEDP[1] + random.uniform(-0.15, 0.15), BZ + random.uniform(-0.12, 0.12)))
    tgt_ion = Vector((random.uniform(-1.0, 1.0), random.uniform(0.3, 1.0), random.uniform(-2.8, -2.1)))
    delay = i * 0.12; r = random.uniform(0.09, 0.16); ph = random.uniform(0, 6.28)
    def fn(t, start=start, tp=tgt_photo, ti=tgt_ion, delay=delay, ph=ph):
        for a0, a1, kind in PUFF_W:
            if a0 <= t < a1:
                u = ease((t - a0 - delay) / 1.6); tg = ti if kind == "ion" else tp
                p = start.lerp(tg, u) + Vector((0.05 * math.sin(3 * t + ph), 0.03 * math.cos(2 * t + ph), 0.04 * math.sin(2.5 * t + ph)))
                return (X0 + p.x, p.y, p.z), u
        return (X0 + start.x, start.y, start.z), 0.0
    o = obj_from(f"Puff{i}", sphere_mesh(f"PuffMe{i}", r, 2), M_SMOKE)
    bake_loc(o, lambda t, fn=fn: tuple(fn(t)[0]))
    wins = [(a0, a1) for a0, a1, kind in PUFF_W if kind != "weak" or i < 3]
    windows(o, wins); PUFFS.append(o); PUFF_FN.append(fn)
# scattered light: a thin ray from each puff that sits in the beam to the light sensor
DV = Vector((X0 + DIODE[0], DIODE[1] - 0.05, BZ))
_bm = bmesh.new(); add_cyl(_bm, 0.035, 1.0, "Z", (0, 0, 0.5), 8); ME_RAY = bpy.data.meshes.new("RayMe"); _bm.to_mesh(ME_RAY); _bm.free(); ME_RAY.materials.append(M_RAY)
for i in range(NP):
    ray = obj_from(f"Ray{i}", ME_RAY)
    def rfn(t, i=i):
        p, u = PUFF_FN[i](t); p = Vector(p); d = DV - p
        on = u > 0.85 and ((C["bounce"] - 0.1 <= t < C["ionization"]) or (C["sensor5"] <= t < C["thats"] and i < 3))
        e = d.to_track_quat("Z", "Y").to_euler()
        return p, (e.x, e.y, e.z), (1.0, 1.0, d.length) if on else (0.0, 0.0, 0.0)
    vals = [rfn(t) for t in TS]
    for ax in range(3):
        bake(ray, "location", ax, [v[0][ax] for v in vals]); bake(ray, "rotation_euler", ax, [v[1][ax] for v in vals]); bake(ray, "scale", ax, [v[2][ax] for v in vals])
    windows(ray, [(C["bounce"] - 0.1, C["ionization"]), (C["sensor5"], C["thats"])])
glow(B_RAY, [(0.0, 6.0), (C["sensor5"] - 0.05, 6.0), (C["sensor5"], 1.2)])
# ions: + drift up to the top plate, - down to the bottom plate; after "grabs" they cling to the smoke puffs
NI = 16
for i in range(NI):
    plus = i % 2 == 0; x0_, y0_ = random.uniform(-1.1, 1.1), random.uniform(0.15, 1.0); ph = random.uniform(0, 1)
    def ifn(t, plus=plus, x0_=x0_, y0_=y0_, ph=ph, i=i):
        u = (t * 0.9 + ph) % 1.0; z = -2.9 + 0.95 * u if plus else -2.0 - 0.95 * u
        p = Vector((X0 + x0_, y0_, z))
        g = ease((t - C["grabs"] - 0.05 * (i % 5)) / 0.6)
        if g > 0 and t < C["but2"]:
            q = Vector(PUFF_FN[i % NP](t)[0]) + Vector((0.12 * math.cos(i), -0.12, 0.12 * math.sin(i)))
            p = p.lerp(q, g)
        return tuple(p)
    o = obj_from(f"Ion{i}", sphere_mesh(f"IonMe{i}", 0.05, 1), M_IONP if plus else M_IONM)
    bake_loc(o, ifn); windows(o, [(C["charges"], C["but2"])])
# current beads around the wire loop: steady, then crawl after "drops"
WP = Path(WIRE_PTS + [WIRE_PTS[0]])
def cur_speed(t): return 2.2 * (1.0 - 0.8 * ease((t - C["drops"]) / 0.5))
_s, _acc = [], 0.0
for t in TS: _s.append(_acc); _acc += cur_speed(t) / FPS
for i in range(8):
    o = obj_from(f"Cur{i}", sphere_mesh(f"CurMe{i}", 0.07, 1), M_CUR)
    vals = [tuple(WP.at((s + i * WP.L / 8) % WP.L)) for s in _s]
    for ax in range(3): bake(o, "location", ax, [v[ax] for v in vals])
    windows(o, [(C["weak"] - 0.1, C["but2"])])
glow(B_CUR, [(0.0, 6.0), (C["drops"], 6.0), (C["drops"] + 0.5, 1.5)])
# ---------- contamination: dust (particles), bugs, grease, damp; then the grime coat ----------
_bm = bmesh.new(); add_box(_bm, -0.05, 0.05, -0.8, 0.8, -0.5, 0.5)
DUST_EM = mesh_obj("DustEmitter", _bm, None); DUST_EM.location = (X0 - 5.0, 1.4, -2.4)
fx.particles(DUST_EM, "dust", F(C["dust"] - 0.1), F(C["coat"]), count=260)
try:
    ps_ = DUST_EM.particle_systems[0].settings
    ps_.particle_size = 0.035; ps_.size_random = 0.7; ps_.lifetime = 90; ps_.normal_factor = 0.0; ps_.factor_random = 0.3
    ps_.object_align_factor = (2.0, 0.0, 0.0); ps_.effector_weights.gravity = 0.0; ps_.brownian_factor = 0.3
    b_ = ps_.instance_object.data.materials[0].node_tree.nodes.get("Principled BSDF")
    b_.inputs["Base Color"].default_value = (0.75, 0.68, 0.55, 1); b_.inputs["Emission Color"].default_value = (1.0, 0.85, 0.6, 1); b_.inputs["Emission Strength"].default_value = 0.6
    DUST_EM.show_instancer_for_render = False
except Exception as e: print("[fx] dust tune skipped:", e)
windows(DUST_EM, [(C["dust"] - 0.1, C["thats"])])
def bug(name):
    bm = bmesh.new()
    for c_, s_ in [((0, 0, 0), (0.22, 0.09, 0.08)), ((0.26, 0, 0.01), (0.08, 0.07, 0.07))]:
        vs = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)["verts"]
        bmesh.ops.scale(bm, verts=vs, vec=s_); bmesh.ops.translate(bm, verts=vs, vec=c_)
    for k in range(3):
        for sgn in (-1, 1):
            x = -0.12 + 0.12 * k; add_seg(bm, (x, 0, 0), (x + 0.04 * (k - 1), sgn * 0.2, -0.08), 0.012, 4)
    add_seg(bm, (0.32, 0, 0.03), (0.45, 0.07, 0.08), 0.008, 4); add_seg(bm, (0.32, 0, 0.03), (0.45, -0.07, 0.08), 0.008, 4)
    return mesh_obj(name, bm, M_BUG)
for k, (start, end, yy) in enumerate([((-7.0, 1.2, -2.3), (-0.9, 1.4, CZ0 + 0.1), 0.0), ((-7.0, 2.4, -2.0), (-1.3, 1.9, CZ0 + 0.1), 0.25)]):
    b = bug(f"Bug{k}")
    P0, P1 = Vector((X0 + start[0], start[1], start[2])), Vector((X0 + end[0], end[1], end[2])); t0 = C["bugs"] - 0.15 + yy
    bake_loc(b, lambda t, P0=P0, P1=P1, t0=t0: tuple(P0.lerp(P1, ease((t - t0) / 1.4)) + Vector((0, 0.04 * math.sin(30 * t), 0))))
    ang = math.atan2(P1.y - P0.y, P1.x - P0.x); b.rotation_euler = (0, 0, ang)
    windows(b, [(t0, C["plates2"] - 0.06), (C["sensor5"] - 0.06, DUR)])
def droplets(name, n, m_, t0, rmin, rmax, targets):
    out = []
    for k in range(n):
        a = math.radians(random.uniform(30, 150)); s = Vector((X0 + 7.4 * math.cos(a), max(0.5, 7.4 * math.sin(a)), random.uniform(-2.8, -1.8)))
        e = Vector(targets[k % len(targets)]); d = t0 + 0.08 * k
        o = obj_from(f"{name}{k}", sphere_mesh(f"{name}Me{k}", random.uniform(rmin, rmax), 2), m_)
        bake_loc(o, lambda t, s=s, e=e, d=d: tuple(s.lerp(e, ease((t - d) / 1.2))))
        bake_scale(o, lambda t, d=d: (1.0, 1.0, 1.0 - 0.45 * ease((t - d - 1.1) / 0.3)))
        windows(o, [(t0, C["plates2"] - 0.06), (C["sensor5"] - 0.06, DUR)]); out.append(o)
    return out
VANE_PTS = [(X0 + 1.72 * math.cos(a) - 0.1, 1.72 * math.sin(a) - 0.12, random.uniform(-3.1, -1.8)) for a in VANES]
droplets("Grease", 6, M_GREASE, C["grease"] - 0.1, 0.07, 0.12, VANE_PTS[::2])
droplets("Damp", 8, M_DAMP, C["damp"] - 0.1, 0.04, 0.08, VANE_PTS[1::2] + [(X0 + DIODE[0] + 0.15, DIODE[1] - 0.12, BZ + 0.15)])
# grime film: thin grimy skins on the labyrinth + over the light sensor lens, growing on "coat"
GR = mesh_obj("GrimeVanes", bmesh.new(), M_FILM)
GR.data = VANE_O.data.copy(); GR.data.materials.clear(); GR.data.materials.append(M_FILM); GR.location = (X0, 0, 0)
sd = GR.modifiers.new("Skin", "SOLIDIFY"); sd.thickness = 0.03; sd.offset = 1.0
GLENS = cyl("GrimeLens", 0.24, 0.05, "Y", (X0 + DIODE[0], DIODE[1] - 0.07, BZ), M_FILM, seg=24)
bake_scale(GLENS, lambda t: (ease((t - C["coat"]) / 0.8),) * 3)
for o in (GR, GLENS): windows(o, [(C["coat"], C["plates2"] - 0.06), (C["sensor5"] - 0.06, DUR)])
# Geometry Nodes scatter: dust specks settled on the chamber floor
FLOORS = half_lathe("DustFloor", [(0.001, CZ0 + 0.001), (2.05, CZ0 + 0.001), (2.05, CZ0 + 0.01), (0.001, CZ0 + 0.01)], M_BLACK, (X0, 0, 0), seg=32)
SPECK = obj_from("SpeckInst", sphere_mesh("SpeckMe", 0.025, 1), M_FILM)      # GN instances the mesh (object scale is ignored)
fx.scatter(FLOORS, SPECK, density=40.0, scale_min=0.6, scale_max=1.6, seed=3)
windows(FLOORS, [(C["coat"], C["plates2"] - 0.06), (C["sensor5"] - 0.06, DUR)])

# ================= row of ten alarms (x = X1): three go dark/red on "three in ten" =================
box("RowTable", X1 - 140, X1 + 140, -120, 160, -2, 0, M_TABLE)
box("RowBack", X1 - 300, X1 + 300, 220, 222, -60, 300, M_STUDIO)
FAIL = {1, 5, 8}
for k in range(10):
    x, y = X1 - 36 + 18 * (k % 5), 0.0 + 20 * (k // 5)
    r_, lb = assembly(f"Row{k}", M_NEW if k not in FAIL else M_OLD, GREEN, (x, y, 0.0), (math.pi, 0, random.uniform(-0.4, 0.4)), label=False)
    if k in FAIL:
        tf = C["three"] + 0.15 * sorted(FAIL).index(k)
        glowc(lb, [(0.0, 3.0, GREEN), (tf - 0.02, 3.0, GREEN), (tf + 0.08, 0.0, RED), (C["fail"] - 0.05, 0.0, RED), (C["fail"] + 0.05, 6.0, RED)])
        halo = torus(f"RowHalo{k}", 8.2, 0.25, emit_mat(f"RowHaloM{k}", RED, 5.0)[0], (x, y, 0.3))
        bake_scale(halo, lambda t, tf=tf: (pop(t, tf, 0.25),) * 3)
        windows(halo, [(tf, C["and2"])])
    else:
        glowc(lb, [(0.0, 3.0, GREEN)])

# ================= lights + world =================
fx.hdri("interior", strength=0.3, rotation_deg=60.0, show_background=False)
fx.glare(threshold=1.0, strength=0.5, size=7)
def area(name, loc, rot, size, energy, rgb=(1, 1, 1)):
    d_ = bpy.data.lights.new(name, "AREA"); d_.size = size; d_.energy = energy; d_.color = rgb
    o = bpy.data.objects.new(name, d_); scene.collection.objects.link(o); o.location = loc; o.rotation_euler = rot; return o, d_
_, HALLKEY = area("HallKey", (40, -120, 90), (math.radians(120), 0, math.radians(15)), 120, 6.0e4, (1.0, 0.93, 0.85))
_, HALLFILL = area("HallFill", (-80, -60, 120), (math.radians(115), 0, math.radians(-50)), 100, 1.5e4, (0.75, 0.82, 1.0))
FIRE_L = bpy.data.lights.new("FireLight", "POINT"); FIRE_L.color = (1.0, 0.45, 0.12); FIRE_L.shadow_soft_size = 20
_fl = bpy.data.objects.new("FireLight", FIRE_L); scene.collection.objects.link(_fl); _fl.location = (70, 225, 100)
for t, v in [(0.0, 0.0), (SM1[0] - 0.05, 0.0), (SM1[0] + 0.6, 2.5e5), (SM1[1] - 0.05, 2.5e5), (SM1[1], 0.0), (SM2[0] - 0.05, 0.0), (SM2[0] + 0.6, 2.5e5), (SM2[1] - 0.05, 2.5e5), (SM2[1], 0.0)]:
    FIRE_L.energy = v; FIRE_L.keyframe_insert("energy", frame=F(t))
for t, v in [(0.0, 6.0e4), (SM1[0] - 0.05, 6.0e4), (SM1[0], 3.0e4), (SM1[1] - 0.05, 3.0e4), (SM1[1], 6.0e4), (SM2[0] - 0.05, 6.0e4), (SM2[0], 3.0e4), (SM2[1] - 0.05, 3.0e4), (SM2[1], 6.0e4)]:
    HALLKEY.energy = v; HALLKEY.keyframe_insert("energy", frame=F(t))
area("StudioKey", (X0 - 30, -40, 25), (math.radians(60), 0, math.radians(-35)), 30, 2.4e3, (1.0, 0.95, 0.9))
area("StudioRim", (X0 + 35, 30, 20), (math.radians(-60), 0, math.radians(130)), 30, 1.5e3, (0.6, 0.75, 1.0))
area("StudioLow", (X0, -25, -30), (math.radians(150), 0, 0), 25, 8.0e2, (1.0, 0.9, 0.8))
area("ChamberFill", (X0, -6, -2.4), (math.radians(90), 0, 0), 4, 6.0, (1.0, 0.97, 0.92))
area("RowKey", (X1 - 40, -90, 140), (math.radians(40), 0, math.radians(-15)), 120, 4.0e4, (1.0, 0.95, 0.9))
area("RowRim", (X1 + 60, 150, 80), (math.radians(-50), 0, math.radians(150)), 80, 1.2e4, (0.6, 0.75, 1.0))

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.05; cam_d.clip_end = 3000
CH = (X0, 0.8, -2.45)                         # chamber centre (in the section)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (9, -34, 216), (0, 0, 235.5), 40),                                     # hook: the old alarm on the ceiling, LED blinking
    (C["and"] - 0.05, (6, -27, 220), (0, 0, 235.5), 42),
    (C["and"], (30, -150, 175), (5, 20, 225), 26, "cut"),                        # stake: smoke rolls under the ceiling, the alarm stays quiet
    (C["quiet"], (20, -120, 185), (2, 10, 230), 28),
    (C["fire"], (14, -70, 200), (0, 0, 234), 30),
    (C["twist"] - 0.05, (12, -62, 204), (0, 0, 234), 30),
    (C["twist"], (8, -48, 196), (0, 0, 233), 34, "cut"),                          # twist it down, flip it over
    (C["over"] + 0.5, (5, -40, 192), (0, 0, 216), 34),
    (C["the"] - 0.05, (5, -38, 193), (0, 0, 216), 34),
    (C["the"], (1.5, -16, 198), (0, 0, 214.8), 42, "cut"),                        # the date on the back
    (C["ten"] - 0.05, (1.0, -13, 200), (0, 0, 214.8), 42),
    (C["ten"], (4, -44, 196), (0, 0, 215.5), 32, "cut"),                          # ten years: the ring fills
    (C["inside"] - 0.05, (3, -40, 198), (0, 0, 215.5), 32),
    (C["inside"], (X0 + 3, -27, -10), (X0, 0, -2.2), 34, "cut"),                  # the cutaway: front cover slides off
    (C["chamber"] - 0.1, (X0 + 2, -22, -9), (X0, 0.5, -2.3), 34),
    (C["air"], (X0 + 0.3, -9.0, -3.6), CH, 34),                                  # the dark chamber
    (C["photo"] - 0.05, (X0, -8.2, -3.4), CH, 34),
    (C["photo"], (X0 - 0.5, -7.6, -3.2), CH, 34),
    (C["clean"] - 0.05, (X0 - 0.2, -7.0, -3.0), CH, 34),
    (C["clean"], (X0 + 0.6, -6.6, -2.0), CH, 34, "cut"),                          # clean air: nothing; smoke drifts in
    (C["horn"] - 0.05, (X0 + 0.4, -6.2, -2.2), CH, 34),
    (C["horn"], (X0 + 2.0, -19, -6.5), (X0 + 1.8, 1.0, -2.3), 34, "cut"),          # the horn goes off
    (C["ionization"] - 0.05, (X0 + 2.0, -18, -6.2), (X0 + 1.8, 1.0, -2.3), 34),
    (C["ionization"], (X0 + 0.6, -8.6, -3.4), (X0 + 0.6, 0.5, -2.45), 34, "cut"),  # ionization chamber
    (C["screams"] - 0.05, (X0 + 0.7, -7.6, -3.0), (X0 + 0.6, 0.5, -2.45), 34),
    (C["screams"], (X0 + 2.0, -19, -6.5), (X0 + 1.8, 1.0, -2.3), 34, "cut"),
    (C["but2"] - 0.05, (X0 + 2.0, -18, -6.2), (X0 + 1.8, 1.0, -2.3), 34),
    (C["but2"], (X0 - 2.5, -14, -4.6), (X0 - 1.6, 1.0, -2.4), 34, "cut"),          # dust, bugs, grease, damp air drift in
    (C["coat"] - 0.05, (X0 - 1.5, -12, -4.0), (X0 - 0.8, 1.0, -2.4), 34),
    (C["coat"], (X0 + 0.2, -7.4, -3.2), CH, 34, "cut"),                           # the coat
    (C["plates2"] - 0.06, (X0 + 0.1, -7.0, -3.0), CH, 34),
    (C["plates2"] - 0.06, (X0 + 0.6, -7.6, -3.0), (X0 + 0.6, 0.5, -2.45), 34, "cut"),  # ... and the plates
    (C["sensor5"] - 0.06, (X0 + 0.6, -7.4, -3.0), (X0 + 0.6, 0.5, -2.45), 34),
    (C["sensor5"] - 0.06, (X0 - 0.2, -7.2, -2.2), CH, 34, "cut"),                  # weak sensor: dim rays
    (C["test"] - 0.3, (X0, -6.8, -2.4), CH, 34),
    (C["test"] - 0.3, (X0 + 1.5, -18, -10), (X0 + 1.0, 1.0, -3.2), 34, "cut"),     # the test button still beeps
    (C["thats"] - 0.05, (X0 + 1.5, -17, -9.5), (X0 + 1.0, 1.0, -3.2), 34),
    (C["thats"], (X0 + 6, -40, -16), (X0, 0, -2.0), 32, "cut"),                    # the code: ten years
    (C["the2"] - 0.05, (X0 + 8, -52, -20), (X0, 0, -2.0), 32),
    (C["the2"], (X1 + 6, -118, 98), (X1, 10, 2), 30, "cut"),                        # the study: three in ten
    (C["and2"] - 0.05, (X1 + 2, -108, 90), (X1, 10, 2), 30),
    (C["and2"], (30, -150, 175), (5, 20, 225), 26, "cut"),                        # it matters: smoke again
    (C["no"] - 0.05, (20, -115, 188), (2, 10, 230), 28),
    (C["no"], (6, -55, 205), (0, 0, 236), 32, "cut"),                             # no alarm ... or one that didn't work
    (C["so"] - 0.05, (5, -50, 207), (0, 0, 236), 32),
    (C["so"], (8, -55, 194), (0, 0, 233), 32, "cut"),                             # pull it down, read the date
    (C["read"] + 0.2, (4, -42, 194), (0, 0, 216), 34),
    (C["date4"], (1.5, -16, 198), (0, 0, 214.8), 42, "cut"),
    (C["replace"] - 0.05, (1.0, -14, 199), (0, 0, 214.8), 42),
    (C["replace"], (10, -230, 120), (0, 30, 118), 24, "cut"),                     # replace the whole alarm: old one drops, new one pops in
    (C["when"] - 0.05, (8, -215, 125), (0, 30, 125), 24),
    (C["when"], (8, -60, 205), (0, 0, 236), 30, "cut"),                           # CTA: the new alarm
    (DUR, (6, -85, 198), (0, 0, 236), 30),
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
bake_scalar(cam_d, "dof.aperture_fstop", [max(4.0, min(22.0, 0.5 * (cl - ct).length)) for cl, ct in zip(cam_loc, cam_tgt)])
fill_d = bpy.data.lights.new("CamFill", "AREA"); fill_d.size = 10; fill_d.color = (0.95, 0.95, 1.0)
bake_scalar(fill_d, "energy", [max(2.0, min(1.5e4, 0.25 * (cl - ct).length ** 2)) for cl, ct in zip(cam_loc, cam_tgt)])
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
fx.bake_rigid(F(T_DROP) - 1, F(C["when"]) + 10)

# ================= export cues, events and projected anchors for the typography =================
def W(o, p=(0, 0, 0)): return ("obj", o, p)
AP = {
    "alarm": W(AL, (0, 0, -2.0)), "label": W(AL, (-0.7, 0.7, 0.08)), "base": (0.0, 0.0, CEIL - 0.8), "ring": W(AL, (0, 9.0, -2.0)),
    "led": (X0 + LEDP[0], LEDP[1], BZ), "beam": (X0 + 0.6, LEDP[1], BZ), "sensor": (X0 + DIODE[0], DIODE[1], BZ), "chamber": (X0 - 1.6, 1.2, -1.6),
    "horn": (X0 + 3.9, 0.5, -3.0), "am": (X0, 0.15, -2.9), "plate_top": (X0 - 0.9, 0.2, -1.9), "plate_bot": (X0 - 0.9, 0.2, -3.0),
    "current": (X0 + 2.6, 0.35, -2.45), "test": (X0, 0.4, -4.35), "vents": (X0 - 6.8, 1.5, -1.6), "row_fail": (X1 - 18.0, 0.0, 4.0),
    "new": (0.0, 0.0, CEIL - 3.0), "old_drop": W(RB, (0, 0, -2.0)),
}
anchors = {k: [] for k in AP}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, p_ in AP.items():
        p_v = p_[1].matrix_world @ Vector(p_[2]) if isinstance(p_[0], str) else Vector(p_)
        p = world_to_camera_view(scene, cam, p_v)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
RR = lambda a, b: [round(a, 3), round(b, 3)]
events = {"smoke1": RR(*SM1), "smoke2": RR(*SM2), "photo": [RR(a, b) for a, b in PHOTO_W], "ion": [RR(a, b) for a, b in ION_W],
          "puffs": [RR(a, b) for a, b, k in PUFF_W], "horn": [RR(a, b) for a, b in HORN_T], "cuts": [round(s[0], 3) for s in SHOTS if len(s) > 4],
          "twist": round(C["twist"], 3), "drop": round(C["down"] - 0.1, 3), "flip": round(C["flip"] - 0.05, 3), "cover_off": round(_ft, 3),
          "light_on": round(C["light2"], 3), "ion_grab": round(C["grabs"], 3), "current_drop": round(C["drops"], 3), "coat": round(C["coat"], 3),
          "test_press": round(C["test"], 3), "fall": round(T_DROP, 3), "new_pop": round(T_NEW, 3), "pull": round(C["pull"], 3),
          "flip2": round(C["down2"], 3), "fails": [round(C["three"] + 0.15 * k, 3) for k in range(3)], "ring_on": RR(C["ten"], C["date3"] + 0.3)}
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
