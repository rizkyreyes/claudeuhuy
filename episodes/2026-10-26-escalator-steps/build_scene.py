# Escalator-Steps-3D: escalator cutaway, Blender Cycles. Every cue is a word in the voice-over.
# Steps ride a chain loop; each step's back wheels run in a second track placed so the tread stays level.
# Step positions, wheel spin, sprockets, chain, handrail and the 1896 cleated belt are baked from one distance curve D(t).
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
random.seed(7)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]).startswith(norm(word)):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
C = {}
for name, word in [("why", "why"), ("flat", "flat"), ("every0", "every"), ("two", "two"), ("hidden", "hidden"), ("lets", "let's"),
                   ("open", "open"), ("chain", "chain"), ("loop", "loop"), ("side", "side"), ("top", "top"), ("motor", "motor"),
                   ("gears", "gears"), ("pull", "pull"), ("chains", "chains"), ("every", "every"), ("attached", "attached"),
                   ("look", "look"), ("side2", "side"), ("two2", "two"), ("wheels", "wheels"), ("front", "front"),
                   ("hooked", "hooked"), ("chain2", "chain"), ("back", "back"), ("follow", "follow"), ("second", "second"),
                   ("track", "track"), ("heres", "here's"), ("two3", "two"), ("tracks", "tracks"), ("same", "same"),
                   ("shape", "shape"), ("wherever", "wherever"), ("chain3", "chain"), ("second2", "second"), ("holds", "holds"),
                   ("back2", "back"), ("right", "right"), ("height", "height"), ("top2", "top"), ("stays", "stays"),
                   ("level", "level"), ("near", "near"), ("top3", "top"), ("both", "both"), ("level2", "level"), ("off", "off"),
                   ("steps", "steps"), ("line", "line"), ("flat2", "flat"), ("grooves", "grooves"), ("slide", "slide"),
                   ("next", "next"), ("thats", "that's"), ("melt", "melt"), ("floor", "floor"), ("then", "then"),
                   ("comb", "comb"), ("plate", "plate"), ("teeth", "teeth"), ("inside", "inside"), ("grooves2", "grooves"),
                   ("gap", "gap"), ("tiny", "tiny"), ("handrail", "handrail"), ("own", "own"), ("loop2", "loop"),
                   ("driven", "driven"), ("match", "match"), ("speed", "speed"), ("underneath", "underneath"),
                   ("empty", "empty"), ("loop3", "loop"), ("down", "down"), ("start", "start"), ("one", "one"),
                   ("coney", "coney"), ("y1896", "1896"), ("had", "had"), ("no", "no"), ("steps2", "steps"), ("ramp", "ramp"),
                   ("escalator", "escalator"), ("brand", "brand"), ("name", "name"), ("y1950", "1950"), ("otis", "otis"),
                   ("lost", "lost"), ("everyday", "everyday"), ("word", "word"), ("do", "do"), ("walk", "walk"),
                   ("stand", "stand"), ("ride", "ride"), ("tell", "tell"), ("comments", "comments")]:
    C[name] = TA(word)
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
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("Escalator")

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
def mat(name, rgb, rough=0.4, metallic=0.0, emit_rgb=(1.0, 0.74, 0.27), noise=0.0):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if noise:                                                    # brushed / worn variation in roughness
        tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise; nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough * 0.7; mr.inputs[4].default_value = rough * 1.4
        nt.links.new(n.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
M_TREAD, B_TREAD = mat("Tread", (0.62, 0.63, 0.65), 0.32, 1.0, GOLD, 60)
M_HERO, B_HERO = mat("HeroTread", (0.66, 0.66, 0.68), 0.30, 1.0, GOLD, 60)
M_YELLOW, B_YELLOW = mat("Demarcation", (0.95, 0.66, 0.05), 0.45)
M_BODY, _ = mat("StepBody", (0.12, 0.13, 0.14), 0.55, 0.6)
M_FW, B_FW = mat("FrontWheel", (0.10, 0.10, 0.11), 0.55, 0.0, GOLD)
M_BW, B_BW = mat("BackWheel", (0.10, 0.10, 0.11), 0.55, 0.0, CYAN)
M_HUB, _ = mat("Hub", (0.7, 0.7, 0.72), 0.3, 1.0)
M_CHAIN, B_CHAIN = mat("Chain", (0.45, 0.42, 0.36), 0.35, 1.0, GOLD, 80)
M_CRAIL, B_CRAIL = mat("ChainRail", (0.42, 0.43, 0.46), 0.35, 1.0, GOLD)
M_TRAIL, B_TRAIL = mat("TrailerRail", (0.42, 0.43, 0.46), 0.35, 1.0, CYAN)
M_GEAR, B_GEAR = mat("Gear", (0.28, 0.29, 0.31), 0.38, 1.0, GOLD, 50)
M_MOTOR, B_MOTOR = mat("Motor", (0.08, 0.20, 0.32), 0.45, 0.2, GOLD)
M_TRUSS, _ = mat("Truss", (0.05, 0.055, 0.06), 0.7, 0.3)
M_CLAD, _ = mat("Cladding", (0.45, 0.46, 0.48), 0.32, 1.0, GOLD, 30)
M_FLOORP, _ = mat("LandingPlate", (0.55, 0.56, 0.58), 0.35, 1.0, GOLD, 200)
M_COMB, B_COMB = mat("Comb", (0.95, 0.66, 0.05), 0.4, 0.0, GOLD)
M_SLAB, _ = mat("Slab", (0.07, 0.07, 0.075), 0.85)
M_RAIL_HR, B_HR = mat("Handrail", (0.02, 0.02, 0.025), 0.35, 0.0, GOLD)
M_CHEV, B_CHEV = mat("Chevron", GOLD, 0.4, 0.0, GOLD); B_CHEV.inputs["Emission Strength"].default_value = 3.0
M_BELT, B_BELT = mat("Belt", (0.16, 0.10, 0.06), 0.8)
M_CLEAT, _ = mat("Cleat", (0.20, 0.19, 0.18), 0.45, 1.0)
M_GLASS, _ = mat("Glass", (0.80, 0.88, 0.92), 0.18)
gb = M_GLASS.node_tree.nodes["Principled BSDF"]; gb.inputs["Transmission Weight"].default_value = 1.0; gb.inputs["IOR"].default_value = 1.45
gb.inputs["Alpha"].default_value = 0.35

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
    r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
    bmesh.ops.scale(bm, verts=vs, vec=(x1 - x0, y1 - y0, z1 - z0))
    bmesh.ops.translate(bm, verts=vs, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def add_cyl_y(bm, r, y0, y1, cx, cz, seg=32, mi=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(y1 - y0)); vs = res["verts"]
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, verts=vs, vec=(cx, (y0 + y1) / 2, cz))
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def add_prism_y(bm, poly, y0, y1, mi=0):
    """Extrude a polygon given in (x, z) between y0 and y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y1, z)) for x, z in poly]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(poly)
    for i in range(n): fs.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def bevel_mod(o, w=0.006, seg=2):
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = w; bv.segments = seg; bv.limit_method = "ANGLE"
def curve_obj(name, pts, cyclic, depth, m_, res=2, link=True):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = res
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = cyclic
    if m_: cu.materials.append(m_)
    o = bpy.data.objects.new(name, cu)
    if link: CL.objects.link(o)
    return o

# ---------- escalator path (chain-axle line, x up the escalator, z up) ----------
TH = math.radians(30); H = 3.0; R1, R2 = 1.0, 1.5; LB, LT = 1.6, 1.6; RS = 0.8
X1 = R1 * math.sin(TH); Z1 = R1 * (1 - math.cos(TH))
Z2 = H - R2 + R2 * math.cos(TH); X2 = X1 + (Z2 - Z1) / math.tan(TH)
XC = X2 + R2 * math.sin(TH); XE = XC + LT; XS = -LB
def ztop(x):
    if x <= 0: return 0.0
    if x <= X1: return R1 - math.sqrt(max(0.0, R1 * R1 - x * x))
    if x <= X2: return Z1 + (x - X1) * math.tan(TH)
    if x <= XC: return H - R2 + math.sqrt(max(0.0, R2 * R2 - (x - XC) ** 2))
    return H
LOOP = []                                    # closed polyline, top run left->right, around the drive, return right->left
nx = 900
for i in range(nx): x = XS + (XE - XS) * i / nx; LOOP.append((x, ztop(x)))
for i in range(60): a = math.pi / 2 - math.pi * i / 60; LOOP.append((XE + RS * math.cos(a), H - RS + RS * math.sin(a)))
for i in range(nx): x = XE - (XE - XS) * i / nx; LOOP.append((x, ztop(x) - 2 * RS))
for i in range(60): a = -math.pi / 2 - math.pi * i / 60; LOOP.append((XS + RS * math.cos(a), -RS + RS * math.sin(a)))
CUM = [0.0]
for i in range(1, len(LOOP) + 1):
    a, b = LOOP[i - 1], LOOP[i % len(LOOP)]; CUM.append(CUM[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
LLOOP = CUM[-1]
S_TOP_END = CUM[nx]                          # arc length where the top run ends (drive sprocket starts)
def P(s):
    s %= LLOOP
    lo, hi = 0, len(LOOP)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if CUM[mid] <= s: lo = mid
        else: hi = mid
    a, b = LOOP[lo], LOOP[(lo + 1) % len(LOOP)]; u = (s - CUM[lo]) / max(1e-9, CUM[lo + 1] - CUM[lo])
    return (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
NSTEP = int(round(LLOOP / 0.40)); PITCH = LLOOP / NSTEP
DT = PITCH * math.cos(TH); RISE = PITCH * math.sin(TH)
print("LOOP", round(LLOOP, 3), "steps", NSTEP, "pitch", round(PITCH, 4))

# ---------- step geometry (local origin = chain axle A; +x = up the escalator) ----------
TREAD_Z = 0.10; XF = 0.04; XB = XF - DT; RW = 0.05
A_LOC = Vector((0, 0, 0)); B_LOC = Vector((XB + 0.04, 0, TREAD_Z - RISE - 0.02))
YW_TREAD, Y_BRK, Y_FW, Y_BW, Y_CHAIN = 0.50, 0.45, 0.575, 0.665, 0.615
def build_step_mesh(name, tread_mat):
    bm = bmesh.new()
    add_box(bm, XB, XF, -YW_TREAD, YW_TREAD, TREAD_Z - 0.045, TREAD_Z - 0.015, 0)            # tread plate (groove floor)
    k = 0; y = -YW_TREAD + 0.012
    while y < YW_TREAD - 0.01:                                                                # cleats along travel
        on_edge = abs(y) > YW_TREAD - 0.06
        add_box(bm, XB, XF + 0.035, y - 0.007, y + 0.007, TREAD_Z - 0.016, TREAD_Z, 1 if on_edge else 0)
        y += 0.03; k += 1
    add_box(bm, XB, XB + 0.05, -YW_TREAD, YW_TREAD, TREAD_Z - 0.016, TREAD_Z - 0.001, 1)     # yellow back edge
    add_box(bm, XB - 0.012, XB, -YW_TREAD, YW_TREAD, TREAD_Z - RISE, TREAD_Z - 0.015, 0)      # riser
    y = -YW_TREAD + 0.027
    while y < YW_TREAD - 0.01:                                                                # riser cleats (vertical)
        add_box(bm, XB - 0.022, XB - 0.012, y - 0.006, y + 0.006, TREAD_Z - RISE + 0.01, TREAD_Z - 0.02, 0); y += 0.03
    brk = [(XB, TREAD_Z - 0.045), (XF, TREAD_Z - 0.045), (0.035, -0.035), (B_LOC.x + 0.03, B_LOC.z - 0.02), (XB, TREAD_Z - RISE)]
    for s in (-1, 1): add_prism_y(bm, brk, s * Y_BRK - 0.012, s * Y_BRK + 0.012, 2)
    add_cyl_y(bm, 0.016, -Y_CHAIN - 0.02, Y_CHAIN + 0.02, 0, 0, 16, 3)                        # step axle
    add_cyl_y(bm, 0.014, -Y_BW + 0.01, Y_BW - 0.01, B_LOC.x, B_LOC.z, 16, 3)                  # trailer axle
    o = mesh_obj(name, bm, [tread_mat, M_YELLOW, M_BODY, M_HUB], link=False); bevel_mod(o, 0.003, 1)
    return o.data
def build_wheel_mesh(name, y_c, wmat):
    bm = bmesh.new()
    for s in (-1, 1):
        add_cyl_y(bm, RW, s * y_c - 0.016, s * y_c + 0.016, 0, 0, 40, 0)
        add_cyl_y(bm, RW * 0.45, s * y_c - 0.019, s * y_c + 0.019, 0, 0, 24, 1)
        for k in range(3):                                                                     # spokes so the spin reads
            a = k * math.pi / 3; ca, sa = math.cos(a), math.sin(a)
            vs = add_box(bm, -RW * 0.85, RW * 0.85, s * y_c - 0.02, s * y_c + 0.02, -0.006, 0.006, 1)
            bmesh.ops.rotate(bm, verts=vs, cent=(0, s * y_c, 0), matrix=Matrix.Rotation(a, 3, "Y"))
    o = mesh_obj(name, bm, [wmat, M_HUB], link=False); return o.data
ME_STEP, ME_HERO = build_step_mesh("StepMesh", M_TREAD), build_step_mesh("HeroStepMesh", M_HERO)
ME_FW, ME_BW = build_wheel_mesh("FrontWheels", Y_FW, M_FW), build_wheel_mesh("BackWheels", Y_BW, M_BW)

# ---------- motion: distance curve D(t) ----------
def ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def seg(t, a, b, v0, v1, fn=ease): return v0 + (v1 - v0) * fn(max(0.0, min(1.0, (t - a) / (b - a)))) if b > a else v1
V_RUN, V_SLOW = 0.45, 0.20
def speed(t):
    if t < C["look"] - 0.6: return V_RUN
    if t < C["near"]: return seg(t, C["look"] - 0.6, C["look"] + 0.2, V_RUN, V_SLOW)
    return seg(t, C["near"], C["near"] + 0.8, V_SLOW, V_RUN)
DIST = [0.0]
for fr in range(2, FRAMES + 1): DIST.append(DIST[-1] + speed((fr - 1.5) / FPS) / FPS)
def D(t): return DIST[min(FRAMES - 1, max(0, int(round(t * FPS))))]

# hero step: the step that sits 1.6 m (along the path) into the incline when "Look" lands
S_INCL0 = next(CUM[i] for i in range(nx) if LOOP[i][0] >= X1)
d_look = D(C["look"])
HERO_I = min(range(NSTEP), key=lambda i: abs(((i * PITCH + d_look) % LLOOP) - (S_INCL0 + 1.6)))

STEPROOT = bpy.data.objects.new("Steps", None); CL.objects.link(STEPROOT)
STEPS = []
for i in range(NSTEP):
    body = bpy.data.objects.new(f"Step_{i:02d}", ME_HERO if i == HERO_I else ME_STEP); CL.objects.link(body)
    body.parent = STEPROOT
    fw = bpy.data.objects.new(f"Step_{i:02d}_FW", ME_FW); CL.objects.link(fw); fw.parent = body
    bw = bpy.data.objects.new(f"Step_{i:02d}_BW", ME_BW); CL.objects.link(bw); bw.parent = body; bw.location = B_LOC
    if i == HERO_I:                                                                             # hero wheels: own materials
        for w_, m_ in ((fw, M_FW), (bw, M_BW)):
            w_.data = w_.data.copy(); w_.data.materials[0] = m_
    STEPS.append((body, fw, bw))
HERO, HERO_FW, HERO_BW = STEPS[HERO_I]

# bake positions; wheel spin shares one action
xs = [[0.0] * FRAMES for _ in range(NSTEP)]; zs = [[0.0] * FRAMES for _ in range(NSTEP)]
comb_events = []
X_COMB_T, X_COMB_B = XE - 0.55, XS + 0.55
for fr in range(1, FRAMES + 1):
    d = DIST[fr - 1]
    for i in range(NSTEP):
        s = (i * PITCH + d) % LLOOP
        x, z = P(s); xs[i][fr - 1] = x; zs[i][fr - 1] = z
        if fr > 1 and s < S_TOP_END and xs[i][fr - 2] < X_COMB_T <= x: comb_events.append(round((fr - 1) / FPS, 3))
for i, (body, fw, bw) in enumerate(STEPS):
    bake(body, "location", 0, xs[i]); bake(body, "location", 2, zs[i])
spin = [d / RW for d in DIST]
bake(STEPS[0][1], "rotation_euler", 1, spin)
ACT_SPIN = STEPS[0][1].animation_data.action
for body, fw, bw in STEPS:
    for w_ in (fw, bw):
        if w_.animation_data is None or w_.animation_data.action is None:
            ad = w_.animation_data_create(); ad.action = ACT_SPIN
            try: ad.action_slot = ACT_SPIN.slots[0]
            except Exception: pass
def hero_pos(t):
    fr = min(FRAMES, max(1, F(t))); return Vector((xs[HERO_I][fr - 1], 0, zs[HERO_I][fr - 1]))

# ---------- chain, tracks, sprockets ----------
def loop_pts(off_x, off_z, y, only_runs=False):
    pts = []
    for i, (x, z) in enumerate(LOOP):
        if only_runs and not (i < nx or nx + 60 <= i < 2 * nx + 60): continue
        pts.append((x + off_x, y, z + off_z))
    return pts
LINK = PITCH / 2
for side in (-1, 1):
    ch_curve = curve_obj(f"ChainPath_{side}", [(x, side * Y_CHAIN, z) for x, z in LOOP], True, 0.0, None)
    bm = bmesh.new()
    add_box(bm, 0.0, LINK - 0.012, -0.006, 0.006, -0.036, 0.036, 0)                          # link plate
    add_cyl_y(bm, 0.016, -0.012, 0.012, 0.0, 0.0, 12, 0)                                       # pin
    ch = mesh_obj(f"Chain_{side}", bm, M_CHAIN)
    ar = ch.modifiers.new("Array", "ARRAY"); ar.count = 2 * NSTEP; ar.use_relative_offset = False
    ar.use_constant_offset = True; ar.constant_offset_displace = (LINK, 0, 0)
    cm = ch.modifiers.new("Curve", "CURVE"); cm.object = ch_curve; cm.deform_axis = "POS_X"
    bake(ch, "location", 0, [d % LLOOP for d in DIST])
    if side < 0: CHAIN_F = ch
RAILS = []
for side in (-1, 1):
    top = [(x, side * Y_FW, z - RW - 0.012) for x, z in LOOP[:nx]]
    ret = [(x, side * Y_FW, z - 2 * RS + RW + 0.012) for x, z in LOOP[:nx]]               # return wheels ride on top of their rail too
    for nm, pts in (("ChainRailTop", top), ("ChainRailRet", ret)):
        o = curve_obj(f"{nm}_{side}", pts, False, 0.012, M_CRAIL, 1); RAILS.append(o)
    trail = [(x + B_LOC.x, side * Y_BW, z + B_LOC.z - RW - 0.012) for x, z in LOOP]
    o = curve_obj(f"TrailerRail_{side}", trail, True, 0.012, M_TRAIL, 1); RAILS.append(o)
GEARS = []
def gear(name, cx, cz, r, teeth):
    bm = bmesh.new()
    for s in (-1, 1):
        add_cyl_y(bm, r - 0.03, s * Y_CHAIN - 0.012, s * Y_CHAIN + 0.012, 0, 0, 64, 0)
        for k in range(teeth):
            a = 2 * math.pi * k / teeth
            vs = add_box(bm, -0.018, 0.018, s * Y_CHAIN - 0.01, s * Y_CHAIN + 0.01, r - 0.04, r + 0.012, 0)
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "Y"))
        for k in range(5):                                                                      # spokes
            vs = add_box(bm, -0.025, 0.025, s * Y_CHAIN - 0.02, s * Y_CHAIN + 0.02, 0.05, r - 0.05, 0)
            bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(2 * math.pi * k / 5, 3, "Y"))
    add_cyl_y(bm, 0.06, -0.8, 0.62, 0, 0, 32, 1)                                                # shaft
    o = mesh_obj(name, bm, [M_GEAR, M_HUB]); o.location = (cx, 0, cz); GEARS.append(o); return o
GEAR_T = gear("DriveGear", XE, H - RS, RS, 24); GEAR_B = gear("ReturnGear", XS, -RS, RS, 24)
for g in GEARS: bake(g, "rotation_euler", 1, [d / RS for d in DIST])
# motor + drive belt at the top (front side, below the return run)
MOTOR_C = Vector((XE - 1.0, -0.95, H - RS))
bm = bmesh.new()
add_cyl_y(bm, 0.26, -0.75, 0.15, 0, 0, 48, 0)
for k in range(10):                                                                             # cooling fins
    add_box(bm, -0.28, 0.28, -0.7 + k * 0.08, -0.68 + k * 0.08, -0.03, 0.03, 0)
add_box(bm, -0.3, 0.3, -0.75, 0.15, -0.36, -0.26, 0)
add_box(bm, -0.06, 0.06, -0.5, 0.0, -0.62, -0.36, 0)                                            # bracket down to the return-run frame
MOTOR = mesh_obj("Motor", bm, M_MOTOR); MOTOR.location = (MOTOR_C.x, 0.15, MOTOR_C.z); bevel_mod(MOTOR, 0.01)
bm = bmesh.new(); add_cyl_y(bm, 0.11, -0.04, 0.04, 0, 0, 32, 0)
for k in range(4):
    vs = add_box(bm, -0.1, 0.1, -0.045, 0.045, -0.012, 0.012, 1)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(k * math.pi / 4, 3, "Y"))
MPUL = mesh_obj("MotorPulley", bm, [M_GEAR, M_HUB]); MPUL.location = (MOTOR_C.x, -0.84, MOTOR_C.z)
bm = bmesh.new(); add_cyl_y(bm, 0.24, -0.04, 0.04, 0, 0, 64, 0)
for k in range(6):
    vs = add_box(bm, -0.23, 0.23, -0.045, 0.045, -0.015, 0.015, 1)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(k * math.pi / 6, 3, "Y"))
DPUL = mesh_obj("DrivePulley", bm, [M_GEAR, M_HUB]); DPUL.location = (XE, -0.84, H - RS)
bake(DPUL, "rotation_euler", 1, [d / RS for d in DIST]); bake(MPUL, "rotation_euler", 1, [d / RS * 0.24 / 0.11 for d in DIST])
BELT_V = curve_obj("DriveBelt", [(p[0], p[1], p[2]) for p in
                   [(XE + 0.24 * math.cos(a), -0.84, H - RS + 0.24 * math.sin(a)) for a in [math.pi * (0.5 - i / 39) for i in range(40)]] +
                   [(MOTOR_C.x + 0.11 * math.cos(a), -0.84, MOTOR_C.z + 0.11 * math.sin(a)) for a in [math.pi * (-0.5 - i / 39) for i in range(40)]]],
                   True, 0.012, M_RAIL_HR, 1)

# ---------- landings: plates, combs, floor slabs ----------
def landing(name, x0, x1, z, comb_x, comb_dir):
    bm = bmesh.new()
    add_box(bm, x0, x1, -0.55, 0.55, z, z + 0.022, 0)
    o = mesh_obj(name, bm, M_FLOORP); bevel_mod(o, 0.004, 1)
    bm = bmesh.new()
    add_box(bm, comb_x - 0.04, comb_x + 0.04, -0.52, 0.52, z, z + 0.03, 0)
    y = -YW_TREAD + 0.012 + 0.015
    while y < YW_TREAD - 0.02:                                                                  # teeth sit in the tread grooves
        tip = comb_x - comb_dir * 0.16
        poly = [(comb_x - comb_dir * 0.03, z + 0.03), (comb_x - comb_dir * 0.03, z), (tip, TREAD_Z + z - 0.104 - 0.012), (tip, TREAD_Z + z - 0.104 - 0.004)]
        add_prism_y(bm, poly if comb_dir > 0 else poly[::-1], y - 0.0055, y + 0.0055, 0); y += 0.03
    comb = mesh_obj(name + "_Comb", bm, M_COMB)
    return o, comb
Z_FLOOR_B, Z_FLOOR_T = TREAD_Z + 0.004, H + TREAD_Z + 0.004
LAND_B, COMB_B = landing("LandingBottom", XS - 1.2, X_COMB_B - 0.04, Z_FLOOR_B, X_COMB_B, -1)
LAND_T, COMB_T = landing("LandingTop", X_COMB_T + 0.04, XE + 1.2, Z_FLOOR_T, X_COMB_T, 1)
bm = bmesh.new(); add_box(bm, XS - 6.0, XS - 1.2, -4.0, 3.0, Z_FLOOR_B - 0.35, Z_FLOOR_B + 0.022, 0)
add_box(bm, XE + 1.2, XE + 8.0, -4.0, 3.0, Z_FLOOR_T - 0.35, Z_FLOOR_T + 0.022, 0)
SLABS = mesh_obj("FloorSlabs", bm, M_SLAB)
bm = bmesh.new(); add_box(bm, XS - 6.0, XE + 8.0, -4.0, 3.0, -2.7, -2.6, 0)
PIT = mesh_obj("PitFloor", bm, M_SLAB)

# ---------- truss, cladding, balustrades, handrails ----------
def outline(top_off, bot_off, x0, x1, n=120):
    xs_ = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    return [(x, ztop(min(max(x, XS), XE)) + top_off) for x in xs_] + [(x, ztop(min(max(x, XS), XE)) + bot_off) for x in reversed(xs_)]
def panel(name, top_off, bot_off, x0, x1, y0, y1, m_):
    bm = bmesh.new(); add_prism_y(bm, outline(top_off, bot_off, x0, x1), y0, y1, 0)
    o = mesh_obj(name, bm, m_); return o
CLAD_F = panel("CladdingFront", TREAD_Z + 0.06, -2 * RS - 0.55, XS - RS - 0.35, XE + RS + 0.35, -0.80, -0.78, M_CLAD)
CLAD_B = panel("CladdingBack", TREAD_Z + 0.06, -2 * RS - 0.55, XS - RS - 0.35, XE + RS + 0.35, 0.78, 0.80, M_TRUSS)
SKIRT_F = panel("SkirtFront", TREAD_Z + 0.20, TREAD_Z - 0.05, XS - 0.9, XE + 0.9, -0.74, -0.72, M_CLAD)
SKIRT_B = panel("SkirtBack", TREAD_Z + 0.20, TREAD_Z - 0.05, XS - 0.9, XE + 0.9, 0.72, 0.74, M_CLAD)
GLASS_F = panel("GlassFront", TREAD_Z + 0.95, TREAD_Z + 0.20, XS - 0.8, XE + 0.8, -0.735, -0.725, M_GLASS)
GLASS_B = panel("GlassBack", TREAD_Z + 0.95, TREAD_Z + 0.20, XS - 0.8, XE + 0.8, 0.725, 0.735, M_GLASS)
truss = bmesh.new()                                                                              # back truss (stays as backdrop)
for x in [XS - 0.6 + k * 0.9 for k in range(int((XE - XS + 1.2) / 0.9) + 1)]:
    zt, zb = ztop(min(max(x, XS), XE)) - 0.25, ztop(min(max(x, XS), XE)) - 2 * RS - 0.45
    add_box(truss, x - 0.04, x + 0.04, 0.70, 0.76, zb, zt, 0)
TRUSS = mesh_obj("TrussBack", truss, M_TRUSS)
HR_Y = 0.73
def hr_loop(y):
    x0, x1, rr = XS - 0.95, XE + 0.95, 0.22
    zf = lambda x: ztop(min(max(x, XS + 0.4), XE - 0.4)) + TREAD_Z + 1.0
    pts = [(x0 + (x1 - x0) * i / 300, y, zf(x0 + (x1 - x0) * i / 300)) for i in range(301)]
    pts += [(x1 + rr * math.sin(math.pi * i / 24), y, zf(x1) - rr + rr * math.cos(math.pi * i / 24)) for i in range(1, 24)]
    pts += [(x1 - (x1 - x0) * i / 300, y, zf(x1 - (x1 - x0) * i / 300) - 2 * rr) for i in range(301)]
    pts += [(x0 - rr * math.sin(math.pi * i / 24), y, zf(x0) - rr - rr * math.cos(math.pi * i / 24)) for i in range(1, 24)]
    return pts
HR_PTS = hr_loop(-HR_Y)
HR_F = curve_obj("HandrailFront", HR_PTS, True, 0.04, M_RAIL_HR, 3)
HR_B = curve_obj("HandrailBack", hr_loop(HR_Y), True, 0.04, M_RAIL_HR, 3)
HR_LEN = sum(math.dist(HR_PTS[i], HR_PTS[(i + 1) % len(HR_PTS)]) for i in range(len(HR_PTS)))
# gold chevrons that ride the back handrail and the step edge (handrail beat only)
NCH = int(HR_LEN / 0.5); CH_SP = HR_LEN / NCH
bm = bmesh.new()
for s in (-1, 1):
    vs = add_box(bm, -0.06, 0.06, -0.03, 0.03, -0.006, 0.006, 0)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(s * math.radians(35), 3, "Y"))
    bmesh.ops.translate(bm, verts=vs, vec=(0, 0, s * 0.03))
CHEV = mesh_obj("HandrailChevrons", bm, M_CHEV)
hr_b_path = curve_obj("HandrailPathBack", [(x, HR_Y - 0.0, z + 0.045) for x, _, z in hr_loop(HR_Y)], True, 0.0, None)
ar = CHEV.modifiers.new("Array", "ARRAY"); ar.count = NCH; ar.use_relative_offset = False; ar.use_constant_offset = True
ar.constant_offset_displace = (CH_SP, 0, 0)
cm = CHEV.modifiers.new("Curve", "CURVE"); cm.object = hr_b_path; cm.deform_axis = "POS_X"
bake(CHEV, "location", 0, [d % HR_LEN for d in DIST])

# ---------- 1896 moving ramp (belt with cleats), shown only for the history beat ----------
bm = bmesh.new(); vs_l, vs_r = [], []
for x, z in LOOP[:nx]:
    vs_l.append(bm.verts.new((x, -0.5, z + TREAD_Z - 0.01))); vs_r.append(bm.verts.new((x, 0.5, z + TREAD_Z - 0.01)))
for i in range(len(vs_l) - 1): bm.faces.new((vs_l[i], vs_l[i + 1], vs_r[i + 1], vs_r[i]))
RAMP = mesh_obj("Ramp1896", bm, M_BELT); sd = RAMP.modifiers.new("Solid", "SOLIDIFY"); sd.thickness = 0.04
ramp_path = curve_obj("RampPath", [(x, 0, z + TREAD_Z - 0.01) for x, z in LOOP], True, 0.0, None)
NCL = int(LLOOP / 0.3); CL_SP = LLOOP / NCL
bm = bmesh.new(); add_box(bm, -0.02, 0.02, -0.48, 0.48, 0.0, 0.03, 0)
CLEATS = mesh_obj("Cleats1896", bm, M_CLEAT)
ar = CLEATS.modifiers.new("Array", "ARRAY"); ar.count = NCL; ar.use_relative_offset = False; ar.use_constant_offset = True
ar.constant_offset_displace = (CL_SP, 0, 0)
cm = CLEATS.modifiers.new("Curve", "CURVE"); cm.object = ramp_path; cm.deform_axis = "POS_X"
bake(CLEATS, "location", 0, [d % LLOOP for d in DIST])

# ---------- visibility ----------
T_HIST0, T_HIST1 = C["coney"] - 0.25, C["escalator"] - 0.1
for o in (RAMP, CLEATS): vis(o, 1, True); vis(o, F(T_HIST0), False); vis(o, F(T_HIST1), True)
for body, fw, bw in STEPS:
    for o in (body, fw, bw):
        key(o, "hide_render", 1, False, "CONSTANT"); key(o, "hide_render", F(T_HIST0), True, "CONSTANT")
        key(o, "hide_render", F(T_HIST1), False, "CONSTANT")
vis(CHEV, 1, True); vis(CHEV, F(C["handrail"] - 0.1), False); vis(CHEV, F(C["underneath"] + 0.2), True)
# cut open: front cladding, skirt, glass and handrail slide toward the camera and vanish
for o in (CLAD_F, SKIRT_F, GLASS_F, HR_F):
    vis(o, 1, False)
    key(o, "location", F(C["open"] - 0.1), (0, 0, 0)); key(o, "location", F(C["open"] + 0.8), (0, -7.5, 0.4))
    vis(o, F(C["open"] + 0.85), True)

# ---------- highlights ----------
def pulse(bsdf, t0, peak=2.5, hold=0.9, rgb=None):
    s = bsdf.inputs["Emission Strength"]
    if rgb: bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
    key(s, "default_value", F(t0 - 0.15), 0.0); key(s, "default_value", F(t0 + 0.12), peak)
    key(s, "default_value", F(t0 + hold), peak * 0.6); key(s, "default_value", F(t0 + hold + 0.5), 0.0)
def hold_glow(bsdf, t0, t1, peak):
    s = bsdf.inputs["Emission Strength"]
    key(s, "default_value", F(t0 - 0.15), 0.0); key(s, "default_value", F(t0 + 0.15), peak)
    key(s, "default_value", F(t1), peak); key(s, "default_value", F(t1 + 0.4), 0.0)
hold_glow(B_CHAIN, C["chain"], C["side"] + 0.6, 2.5)
pulse(B_MOTOR, C["motor"], 0.8, 0.8); pulse(B_GEAR, C["gears"], 0.3, 1.2)
pulse(B_CHAIN, C["chains"], 2.0, 0.6)
pulse(B_TREAD, C["every"], 0.5, 0.9)
pulse(B_HERO, C["look"], 0.7, 1.0)
hold_glow(B_FW, C["front"], C["back"] - 0.2, 4.0); pulse(B_CHAIN, C["chain2"], 2.0, 0.5)
hold_glow(B_BW, C["back"], C["heres"], 4.0); hold_glow(B_TRAIL, C["second"], C["heres"], 3.0)
hold_glow(B_CRAIL, C["two3"], C["level2"] + 0.8, 2.5); hold_glow(B_TRAIL, C["two3"] + 0.05, C["level2"] + 0.8, 3.0)
pulse(B_BW, C["back2"], 4.0, 1.0); pulse(B_HERO, C["level"], 0.9, 1.0)
pulse(B_TREAD, C["grooves"], 0.45, 1.6); pulse(B_COMB, C["comb"], 2.0, 3.0)

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 35
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 8; cam_d.dof.focus_object = TGT
cam_d.clip_start = 0.05
XM = (XS + XE) / 2
SHOTS = [  # (time, camera loc, target, lens) or (time, "hero", cam offset, target offset, lens)
    (0.0, (-4.2, -1.3, 2.3), (2.4, 0.0, 1.9), 26),
    (C["two"], (-3.4, -1.1, 2.1), (2.6, 0.0, 1.9), 26),
    (C["lets"], (-2.6, -2.6, 1.9), (2.4, 0.0, 1.4), 26),
    (C["open"] + 0.2, (XM, -9.6, 1.4), (XM, 0.0, 0.9), 24),
    (C["side"] + 0.2, (XM + 0.3, -9.2, 1.4), (XM + 0.3, 0.0, 0.9), 24),
    (C["top"] + 0.1, (XE + 0.9, -4.2, H - 0.2), (XE - 0.5, -0.3, H - 0.85), 26),
    (C["pull"], (XE + 0.6, -4.4, H), (XE - 0.6, 0.0, H - 0.75), 26),
    (C["every"], (XM, -9.0, 1.5), (XM, 0.0, 0.95), 24),
    (C["look"] - 0.3, "hero", (0.0, -2.3, 0.15), (-0.1, 0.0, 0.0), 32),
    (C["wheels"], "hero", (-0.1, -1.6, 0.05), (-0.12, 0.0, -0.04), 32),
    (C["follow"], "hero", (-0.15, -1.8, 0.05), (-0.15, 0.0, -0.05), 32),
    (C["heres"], "hero", (-0.3, -4.4, 0.3), (-0.2, 0.0, -0.05), 28),
    (C["level"] - 0.2, "hero", (0.0, -2.6, 0.25), (0.0, 0.0, 0.0), 30),
    (C["near"] + 0.1, (XC - 0.4, -3.6, H + 0.2), (XC - 0.4, 0.0, H - 0.25), 28),
    (C["off"] + 0.3, (XC + 0.2, -3.4, H + 0.25), (XC + 0.2, 0.0, H - 0.1), 28),
    (C["grooves"] - 0.2, (X_COMB_T - 1.3, -1.25, H + 1.25), (X_COMB_T - 0.45, 0.0, H + 0.05), 30),
    (C["melt"], (X_COMB_T - 1.15, -1.1, H + 1.05), (X_COMB_T - 0.3, 0.0, H + 0.08), 30),
    (C["comb"], (X_COMB_T - 0.75, -0.7, H + 0.55), (X_COMB_T - 0.05, 0.0, H + 0.1), 32),
    (C["tiny"] + 0.2, (X_COMB_T - 0.65, -0.6, H + 0.45), (X_COMB_T - 0.02, 0.0, H + 0.1), 32),
    (C["handrail"] - 0.1, (XM - 1.8, -7.4, 4.6), (XM, 0.0, 1.9), 26),
    (C["speed"] + 0.4, (XM - 1.2, -7.0, 4.3), (XM + 0.4, 0.0, 1.8), 26),
    (C["underneath"], (XM - 0.2, -4.8, -0.5), (XM - 0.2, 0.0, 0.25), 24),
    (C["start"] + 0.2, (XM - 0.9, -4.6, -0.4), (XM - 0.9, 0.0, 0.25), 24),
    (C["coney"] - 0.3, (-3.4, -5.6, 2.6), (2.4, 0.0, 1.2), 24),
    (C["ramp"] + 0.4, (-2.8, -5.2, 2.2), (2.6, 0.0, 1.3), 24),
    (C["escalator"], (XM + 6.0, -9.0, 4.5), (XM, 0.0, 1.2), 24),
    (C["word"] + 0.2, (XM + 5.0, -10.0, 3.5), (XM, 0.0, 1.2), 24),
    (C["do"], (-3.4, -4.4, 1.6), (1.8, 0.0, 1.1), 26),
    (C["end"], (-3.9, -2.8, 1.25), (1.6, 0.0, 1.05), 26),
]
cam_loc, cam_tgt, cam_lens = [], [], []
def shot_at(k, t):
    s = SHOTS[k]
    if s[1] == "hero":
        h = hero_pos(t); return h + Vector(s[2]), h + Vector(s[3]), s[4]
    return Vector(s[1]), Vector(s[2]), s[3]
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = shot_at(k, t)
    if k + 1 < len(SHOTS):
        t1 = SHOTS[k + 1][0]; tr = 0.7 if (t1 - SHOTS[k][0]) > 1.4 else (t1 - SHOTS[k][0]) * 0.5
        if t > t1 - tr:                                                   # ease into the next shot over its lead-in
            l1, g1, n1 = shot_at(k + 1, t); u = ease((t - (t1 - tr)) / tr)
            l0, g0, n0 = l0.lerp(l1, u), g0.lerp(g1, u), n0 + (n1 - n0) * u
    cam_loc.append(l0); cam_tgt.append(g0); cam_lens.append(n0)
# hold shots drift slightly so nothing is ever frozen
for i in range(FRAMES):
    t = i / FPS; cam_loc[i] = cam_loc[i] + Vector((0.06 * math.sin(t * 0.7), 0.0, 0.04 * math.sin(t * 0.9 + 1.0)))
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()

# ---------- world + lights: dark studio ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
for n in list(wn):
    if n.type == "BACKGROUND": wn.remove(n)
wout = next(n for n in wn if n.type == "OUTPUT_WORLD")
grad_tc = wn.new("ShaderNodeTexCoord"); grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
wl.new(grad_tc.outputs["Window"], grad.inputs["Vector"])
gr = wn.new("ShaderNodeValToRGB"); e = gr.color_ramp.elements; e[0].color = (0.004, 0.005, 0.007, 1); e[1].color = (0.03, 0.036, 0.048, 1)
wl.new(grad.outputs["Fac"], gr.inputs[0])
bg_dark = wn.new("ShaderNodeBackground"); wl.new(gr.outputs[0], bg_dark.inputs["Color"])
sky = wn.new("ShaderNodeTexGradient"); sky.gradient_type = "LINEAR"; wl.new(grad_tc.outputs["Generated"], sky.inputs["Vector"])
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.10
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_ref.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
LT_TGT = bpy.data.objects.new("LightTarget", None); scene.collection.objects.link(LT_TGT); LT_TGT.location = (XM, 0, 1.0)
def area(name, loc, size, power, rgb=(1, 1, 1), target=LT_TGT):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
area("Key", (XM - 4.0, -9.0, 8.0), 8.0, 1100, (1.0, 0.95, 0.88))
area("Rim", (XM + 6.0, 7.0, 6.0), 6.0, 1300, (0.70, 0.82, 1.0))
area("Fill", (XM + 3.0, -8.0, -2.0), 7.0, 380, (1.0, 0.9, 0.82))
area("Top", (XM, -1.0, 9.0), 5.0, 450)
area("CamFill", (0, 0, 0), 2.5, 60, (1.0, 0.96, 0.9), TGT).parent = cam            # soft light from the lens for close-ups

# ---------- render settings ----------
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
scene.cycles.max_bounces = 8; scene.cycles.transmission_bounces = 6
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

# ---------- export cues, mechanical events and projected anchors for the typography ----------
s_chain = S_INCL0 + 2.4; cx_, cz_ = P(s_chain)
ANCH = {"chain": (None, Vector((cx_, -Y_CHAIN, cz_))), "chain_top": (None, Vector((XE - 0.25, -Y_CHAIN, H - 0.03))),
        "motor": (MOTOR, Vector((0, -0.8, 0.26))), "gear": (None, Vector((XE - RS * 0.7, -0.55, H - RS - RS * 0.7))),
        "hero_tread_back": (HERO, Vector((XB, -0.5, TREAD_Z))), "hero_tread_front": (HERO, Vector((XF, -0.5, TREAD_Z))),
        "hero_fw": (HERO, Vector((0, -Y_FW, 0))), "hero_bw": (HERO, Vector((B_LOC.x, -Y_BW, B_LOC.z))),
        "chain_rail": (HERO, Vector((0.3, -Y_FW, -RW - 0.012))), "trailer_rail": (HERO, Vector((B_LOC.x - 0.3, -Y_BW, B_LOC.z - RW - 0.012))),
        "top_curve": (None, Vector((XC - 0.4, -0.6, ztop(XC - 0.4) + TREAD_Z))), "comb": (None, Vector((X_COMB_T + 0.02, -0.3, Z_FLOOR_T + 0.03))),
        "grooves": (None, Vector((X_COMB_T - 0.45, -0.2, H + TREAD_Z))), "handrail": (None, Vector((XM + 0.8, HR_Y, ztop(XM + 0.8) + TREAD_Z + 1.04))),
        "return": (None, Vector((XM - 0.8, -0.5, ztop(XM - 0.8) - 2 * RS + TREAD_Z))), "ramp": (None, Vector((XM, -0.5, ztop(XM) + TREAD_Z))),
        "escalator": (None, Vector((XM, 0, ztop(XM) + 1.2)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, (ob, local) in ANCH.items():
        w = local if ob is None else ob.matrix_world @ local
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)])
events = {"comb_clack": comb_events, "steps_hidden": [round(T_HIST0, 3), round(T_HIST1, 3)], "hero_index": HERO_I,
          "open": round(C["open"] + 0.1, 3)}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS comb", len(comb_events), "hero", HERO_I, "DUR", DUR, "FRAMES", FRAMES)

save = arg("--save")
if save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))
out = arg("--out", os.path.join(HERE, "checks"))
if "--stills" in ARGS:
    os.makedirs(out, exist_ok=True)
    r.resolution_percentage = int(arg("--pct", "25"))
    import time
    for fr in [int(x) for x in arg("--stills").split(",")]:
        scene.frame_set(fr); r.filepath = os.path.join(out, f"still_{fr:04d}.png")
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("STILL", fr, round(time.time() - t0, 1))
if "--anim" in ARGS:
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
