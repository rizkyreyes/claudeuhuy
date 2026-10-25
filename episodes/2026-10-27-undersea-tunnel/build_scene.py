# Undersea-Tunnel-3D: slurry TBM cutaway under the seabed + a Channel Tunnel diorama, Blender Cycles. Every cue is a word in the VO.
# Set A (origin): seabed section (water / sand / soaked ground), a slurry TBM advancing along +x, lining rings built in its tail.
# Set B (x = 2000): Channel section, chalk / chalk marl / clay, two drives growing toward each other, British machine steered down.
# Machine position X(t), ring appearance, erector angle, jacks, cutter spin, chips and pipe pulses are baked per frame.
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
random.seed(11)

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
for name, word in [("how", "how"), ("dig", "dig"), ("tunnel", "tunnel"), ("sea", "sea"), ("without", "without"), ("sea2", "sea"),
                   ("coming", "coming"), ("machine", "machine"), ("builds", "builds"), ("digs", "digs"), ("lets", "let's"),
                   ("open", "open"), ("front", "front"), ("giant", "giant"), ("cutting", "cutting"), ("wheel", "wheel"),
                   ("slowly", "slowly"), ("steel", "steel"), ("discs", "discs"), ("roll", "roll"), ("rock", "rock"),
                   ("crush", "crush"), ("chips", "chips"), ("but", "but"), ("sea3", "sea"), ("ground", "ground"),
                   ("soaked", "soaked"), ("open2", "open"), ("face", "face"), ("water", "water"), ("rushes", "rushes"),
                   ("so", "so"), ("chamber", "chamber"), ("filled", "filled"), ("pressurized", "pressurized"),
                   ("slurry", "slurry"), ("pushes", "pushes"), ("mud", "mud"), ("holds", "holds"), ("muck", "muck"),
                   ("pumped", "pumped"), ("surface", "surface"), ("cleaned", "cleaned"), ("sent", "sent"),
                   ("behind", "behind"), ("steel2", "steel"), ("shield", "shield"), ("inside", "inside"), ("arm", "arm"),
                   ("picks", "picks"), ("curved", "curved"), ("concrete", "concrete"), ("pieces", "pieces"),
                   ("bolts", "bolts"), ("ring", "ring"), ("then", "then"), ("hydraulic", "hydraulic"), ("jacks", "jacks"),
                   ("push", "push"), ("new", "new"), ("machine2", "machine"), ("shoves", "shoves"), ("forward", "forward"),
                   ("dig2", "dig"), ("build", "build"), ("ring2", "ring"), ("push2", "push"), ("over", "over"),
                   ("over2", "over"), ("every", "every"), ("piece", "piece"), ("rubber", "rubber"), ("gasket", "gasket"),
                   ("edge", "edge"), ("squeezed", "squeezed"), ("tight", "tight"), ("keep", "keep"), ("sea4", "sea"),
                   ("grout", "grout"), ("fills", "fills"), ("gap", "gap"), ("rings", "rings"), ("under", "under"),
                   ("english", "english"), ("channel", "channel"), ("eleven", "eleven"), ("boring", "boring"),
                   ("machines", "machines"), ("job", "job"), ("stayed", "stayed"), ("layer", "layer"), ("chalky", "chalky"),
                   ("rock2", "rock"), ("barely", "barely"), ("water2", "water"), ("through", "through"), ("y1990", "1990"),
                   ("two", "two"), ("sides", "sides"), ("met", "met"), ("then2", "then"), ("british", "british"),
                   ("machines2", "machines"), ("steered", "steered"), ("rock3", "rock"), ("buried", "buried"),
                   ("would", "would"), ("ride", "ride"), ("train", "train"), ("sea5", "sea"), ("tell", "tell"),
                   ("comments", "comments")]:
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
CL = coll("UnderseaTunnel")

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
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise; nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough * 0.7; mr.inputs[4].default_value = rough * 1.4
        nt.links.new(n.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
def strata_mat(name, bands, scale=2.5):
    """Ground coloured by world height: bands = [(z, rgb), ...] low to high, with noise so the layers read as soil, not paint."""
    m, nt, b = new_mat(name)
    geo = nt.nodes.new("ShaderNodeNewGeometry"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 6
    nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath"); add.operation = "MULTIPLY_ADD"; add.inputs[1].default_value = 0.35
    nt.links.new(nz.outputs["Fac"], add.inputs[0]); nt.links.new(sep.outputs["Z"], add.inputs[2])
    z0, z1 = bands[0][0], bands[-1][0]
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = z0; mr.inputs[2].default_value = z1
    nt.links.new(add.outputs[0], mr.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position = 0.0; el[0].color = (*bands[0][1], 1); el[1].position = 1.0; el[1].color = (*bands[-1][1], 1)
    for z, rgb in bands[1:-1]:
        e = el.new((z - z0) / (z1 - z0)); e.color = (*rgb, 1)
    ramp.color_ramp.interpolation = "EASE"
    nt.links.new(mr.outputs[0], ramp.inputs[0])
    hue = nt.nodes.new("ShaderNodeMixRGB"); hue.blend_type = "MULTIPLY"; hue.inputs[0].default_value = 0.35
    nt.links.new(ramp.outputs[0], hue.inputs[1]); nt.links.new(nz.outputs["Color"], hue.inputs[2])
    nt.links.new(hue.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.92
    b.inputs["Emission Color"].default_value = (0.25, 0.9, 1.0, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
M_GROUND, B_GROUND = strata_mat("Ground", [(-12.0, (0.05, 0.05, 0.055)), (-5.0, (0.12, 0.10, 0.08)), (2.0, (0.20, 0.16, 0.11)),
                                           (6.4, (0.26, 0.21, 0.14)), (7.3, (0.50, 0.40, 0.25)), (8.0, (0.62, 0.52, 0.34))], 1.6)
M_WATER, B_WATER = mat("Sea", (0.12, 0.48, 0.70), 0.08, 0.0, (0.10, 0.45, 0.75)); B_WATER.inputs["Emission Strength"].default_value = 0.35
wb = M_WATER.node_tree.nodes["Principled BSDF"]; wb.inputs["Transmission Weight"].default_value = 0.85; wb.inputs["IOR"].default_value = 1.33
wb.inputs["Alpha"].default_value = 0.75
M_SHIELD, B_SHIELD = mat("Shield", (0.70, 0.50, 0.10), 0.35, 0.85, GOLD, 40)
M_STEEL, _ = mat("Steel", (0.42, 0.43, 0.45), 0.35, 1.0, GOLD, 40)
M_CUTTER, B_CUTTER = mat("Cutterhead", (0.62, 0.43, 0.08), 0.4, 0.7, GOLD, 30)
M_DISC, B_DISC = mat("DiscCutters", (0.75, 0.76, 0.78), 0.25, 1.0, GOLD)
M_DARK, _ = mat("DarkSteel", (0.06, 0.065, 0.07), 0.55, 0.6)
M_DRIVE, _ = mat("MainDrive", (0.08, 0.20, 0.32), 0.45, 0.2)
M_SLURRY, B_SLURRY = mat("Slurry", (0.06, 0.038, 0.02), 0.12, 0.0, GOLD, 8)
M_CHIP, _ = mat("Chips", (0.30, 0.29, 0.27), 0.9)
M_SEG, B_SEG = mat("Segments", (0.55, 0.55, 0.53), 0.85, 0.0, GOLD, 25)
M_HERO, B_HERO = mat("HeroSegments", (0.60, 0.60, 0.58), 0.8, 0.0, GOLD, 25)
M_GASKET, B_GASKET = mat("Gasket", (0.015, 0.015, 0.017), 0.6, 0.0, GOLD)
M_GROUT, B_GROUT = mat("Grout", (0.40, 0.40, 0.42), 0.9, 0.0, GOLD)
M_ERECT, B_ERECT = mat("Erector", (0.85, 0.32, 0.06), 0.4, 0.3, GOLD)
M_JACK, B_JACK = mat("Jacks", (0.80, 0.82, 0.85), 0.15, 1.0, GOLD)
M_PIPE_D, B_PIPE_D = mat("PipeDischarge", (0.25, 0.18, 0.10), 0.5, 0.2, GOLD)
M_PIPE_F, B_PIPE_F = mat("PipeFeed", (0.10, 0.22, 0.30), 0.5, 0.2, CYAN)
M_ARROW_W, B_ARROW_W = mat("ArrowWater", CYAN, 0.4, 0.0, CYAN); B_ARROW_W.inputs["Emission Strength"].default_value = 4.0
M_ARROW_S, B_ARROW_S = mat("ArrowSlurry", GOLD, 0.4, 0.0, GOLD); B_ARROW_S.inputs["Emission Strength"].default_value = 4.0
M_PULSE_D, B_PULSE_D = mat("PulseMuck", GOLD, 0.4, 0.0, GOLD); B_PULSE_D.inputs["Emission Strength"].default_value = 5.0
M_PULSE_F, B_PULSE_F = mat("PulseFeed", CYAN, 0.4, 0.0, CYAN); B_PULSE_F.inputs["Emission Strength"].default_value = 5.0
M_LAMP, B_LAMP = mat("TunnelLamps", (1, 0.95, 0.85), 0.4, 0.0, (1.0, 0.92, 0.75)); B_LAMP.inputs["Emission Strength"].default_value = 6.0
# Channel diorama
M_CHALK, B_CHALK = mat("Chalk", (0.78, 0.77, 0.72), 0.85, 0.0, CYAN, 3)
M_MARL, B_MARL = mat("ChalkMarl", (0.22, 0.32, 0.40), 0.85, 0.0, CYAN, 3)
M_CLAY, _ = mat("GaultClay", (0.14, 0.13, 0.12), 0.9, 0.0, CYAN, 3)
M_SAND, _ = mat("Seabed", (0.52, 0.45, 0.32), 0.9)
M_LAND, _ = mat("Land", (0.20, 0.30, 0.14), 0.9)
M_TUBE, B_TUBE = mat("DriveTube", GOLD, 0.4, 0.3, GOLD); B_TUBE.inputs["Emission Strength"].default_value = 1.2
M_MINI, B_MINI = mat("MiniTBM", (0.70, 0.50, 0.10), 0.35, 0.85, RED)

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
def add_cyl_x(bm, r, x0, x1, cy=0.0, cz=0.0, seg=48, mi=0):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(x1 - x0)); vs = res["verts"]
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, verts=vs, vec=((x0 + x1) / 2, cy, cz))
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def add_sector(bm, r0, r1, a0, a1, x0, x1, n=16, mi=0):
    """Annular sector around the x axis: angle a measured from +y toward +z (y = r cos a, z = r sin a), degrees."""
    ring = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n); ca, sa = math.cos(a), math.sin(a)
        ring.append([bm.verts.new((x, r * ca, r * sa)) for x, r in ((x0, r0), (x0, r1), (x1, r1), (x1, r0))])
    fs = []
    for i in range(n):
        A, B = ring[i], ring[i + 1]
        for k in range(4): fs.append(bm.faces.new((A[k], A[(k + 1) % 4], B[(k + 1) % 4], B[k])))
    fs.append(bm.faces.new(ring[0][::-1])); fs.append(bm.faces.new(ring[-1]))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def add_prism_y(bm, poly, y0, y1, mi=0):
    """Extrude a polygon given in (x, z) between y0 and y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y1, z)) for x, z in poly]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(poly)
    for i in range(n): fs.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def add_prism_x(bm, poly, x0, x1, mi=0):
    """Extrude a polygon given in (y, z) between x0 and x1."""
    a = [bm.verts.new((x0, y, z)) for y, z in poly]; b = [bm.verts.new((x1, y, z)) for y, z in poly]
    fs = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(poly)
    for i in range(n): fs.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def bevel_mod(o, w=0.01, seg=2):
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = w; bv.segments = seg; bv.limit_method = "ANGLE"
def curve_obj(name, pts, cyclic, depth, m_, res=2, link=True):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    sp.use_cyclic_u = cyclic
    if m_: cu.materials.append(m_)
    o = bpy.data.objects.new(name, cu)
    if link: CL.objects.link(o)
    return o
def arrow_mesh(name, length, r, m_):
    """Arrow along +x from 0 to length."""
    bm = bmesh.new(); add_cyl_x(bm, r, 0, length * 0.68, 0, 0, 16)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r * 2.4, radius2=0.0, depth=length * 0.32); vs = res["verts"]
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, verts=vs, vec=(length * 0.84, 0, 0))
    o = mesh_obj(name, bm, m_, link=False); return o.data

# ---------- easing and the machine's position X(t) ----------
def ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def lin(p): return max(0.0, min(1.0, p))
W, LS = 1.5, 9.5                      # ring width; shield length (cutter face at X, tail at X - LS)
RB, RSH, RSO, RO, RI = 3.62, 3.48, 3.56, 3.30, 3.00   # bore, shield inner/outer, ring outer/inner
T_HOOK_END = C["lets"] - 0.1
XKEYS = [(0.0, 0.0, lin), (T_HOOK_END, 4 * W, lin), (C["inside"] - 0.3, 5 * W, lin), (C["push"], 5 * W, lin),
         (C["forward"] + 0.2, 6 * W, ease), (C["push2"], 6 * W, lin), (C["push2"] + 0.45, 7 * W, ease),
         (C["over"] + 0.25, 7 * W, lin), (C["over"] + 0.65, 8 * W, ease), (C["every"], 8 * W, lin), (DUR + 0.1, 8 * W + 0.9, lin)]
def Xm(t):
    if t <= XKEYS[0][0]: return XKEYS[0][1]
    for (t0, x0, _), (t1, x1, fn) in zip(XKEYS, XKEYS[1:]):
        if t <= t1: return x0 + (x1 - x0) * fn((t - t0) / (t1 - t0)) if t1 > t0 else x1
    return XKEYS[-1][1]
XS = [Xm((fr - 1) / FPS) for fr in range(1, FRAMES + 1)]
def X(t): return XS[min(FRAMES - 1, max(0, int(round(t * FPS))))]
def t_reach(x):
    for fr, v in enumerate(XS):
        if v >= x - 1e-6: return fr / FPS
    return DUR + 1

# ---------- Set A: seabed section ----------
Z_SEABED, Z_SEA = 8.0, 13.0
GX0, GX1 = -64.0, 46.0
poly = [(0.0, -12.0), (12.0, -12.0), (12.0, Z_SEABED), (0.0, Z_SEABED)]
poly += [(RB * math.sin(math.radians(a)), RB * math.cos(math.radians(a))) for a in range(0, 181, 6)]
bm = bmesh.new(); add_prism_x(bm, poly, GX0, GX1); GROUND = mesh_obj("GroundSection", bm, M_GROUND)
bm = bmesh.new(); add_prism_x(bm, [(0.0, -RB)] + [(RB * math.sin(math.radians(a)), -RB * math.cos(math.radians(a))) for a in range(6, 175, 6)] + [(0.0, RB)], 0.0, 1.0)
PLUG = mesh_obj("GroundAhead", bm, M_GROUND)             # unexcavated ground in front of the cutterhead
bake(PLUG, "location", 0, [x + 0.30 for x in XS]); bake(PLUG, "scale", 0, [GX1 - x - 0.30 for x in XS])
bm = bmesh.new(); add_box(bm, GX0, GX1, 0.0, 12.0, Z_SEABED, Z_SEA); SEA = mesh_obj("Sea", bm, M_WATER)
bm = bmesh.new(); add_box(bm, GX0, GX1, 0.0, 12.0, Z_SEA - 0.02, Z_SEA); SURF = mesh_obj("SeaSurface", bm, M_WATER)

# ---------- TBM (parent empty at the cutter face, moves along x) ----------
TBM = bpy.data.objects.new("TBM", None); CL.objects.link(TBM)
bake(TBM, "location", 0, XS)
def part(name, bm, mats, parent=TBM):
    return mesh_obj(name, bm, mats, parent)
# cutterhead: face disc, 6 spokes, disc cutters; rotates about x
bm = bmesh.new(); add_cyl_x(bm, RB - 0.04, -0.25, 0.05, 0, 0, 72, 0)
for k in range(6):
    vs = add_box(bm, 0.05, 0.22, -0.16, 0.16, 0.3, RB - 0.08, 0)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(k * math.pi / 3, 3, "X"))
add_cyl_x(bm, 0.55, 0.05, 0.30, 0, 0, 32, 0)
for k in range(6):                                                                   # muck openings (dark slots between spokes)
    vs = add_box(bm, 0.051, 0.06, -0.22, 0.22, 1.2, RB - 0.4, 2)
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(k * math.pi / 3 + math.pi / 6, 3, "X"))
CUT = part("Cutterhead", bm, [M_CUTTER, M_DISC, M_DARK]); bevel_mod(CUT, 0.015)
bm = bmesh.new()
for k in range(6):
    phi = k * math.pi / 3
    for j, r in enumerate([0.7, 1.15, 1.6, 2.05, 2.5, 2.95, 3.35]):
        if (j + k) % 2 and r < 3.3: continue
        cy, cz = r * math.cos(phi + 0.18 * (j % 2)), r * math.sin(phi + 0.18 * (j % 2))
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.17, radius2=0.17, depth=0.07); vs = res["verts"]
        tang = Vector((0, -math.sin(phi), math.cos(phi)))                            # disc axis tangential, so it rolls around the face
        z = Vector((0, 0, 1)); ax = z.cross(tang); ang = z.angle(tang)
        if ax.length > 1e-6: bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(ang, 3, ax.normalized()))
        bmesh.ops.translate(bm, verts=vs, vec=(0.30, cy, cz))
DISCS = mesh_obj("DiscCutters", bm, M_DISC, CUT)
SPIN = [0.0]
for fr in range(2, FRAMES + 1): SPIN.append(SPIN[-1] + 0.55 / FPS)                 # slow, steady turn (~5 rpm look)
bake(CUT, "rotation_euler", 0, SPIN)
# shield: back half stays, front half lifts away on "open"
bm = bmesh.new(); add_sector(bm, RSH, RSO, -90, 90, -LS, -0.25, 48); SH_B = part("ShieldBack", bm, M_SHIELD)
bm = bmesh.new(); add_sector(bm, RSH, RSO, 90, 270, -LS, -0.25, 48); SH_F = part("ShieldFront", bm, M_SHIELD)
for k in range(1, 6):                                                                # stiffener rings on the shield skin
    bm = bmesh.new(); add_sector(bm, RSH - 0.18, RSH, -90, 90, -1.0 - k * 1.55, -0.85 - k * 1.55, 32); part(f"Stiffener{k}", bm, M_DARK)
# bulkhead, main drive, chamber
bm = bmesh.new(); add_cyl_x(bm, RSH, -2.05, -1.85, 0, 0, 64); BULK = part("Bulkhead", bm, M_DARK)
bm = bmesh.new(); add_cyl_x(bm, 1.25, -3.1, -2.05, 0, 0, 48); add_cyl_x(bm, 0.5, -3.6, -3.1, 0, 0, 32)
DRIVE = part("MainDrive", bm, M_DRIVE); bevel_mod(DRIVE, 0.02)
bm = bmesh.new(); add_sector(bm, 0.001, RSH - 0.03, -90, 90, -1.84, -0.27, 40)          # back half only: the cut face shows the fill level
SLURRY = part("SlurryChamber", bm, M_SLURRY)
# slurry fill: origin at the chamber floor, scale z from 0 to 1
for v in SLURRY.data.vertices: v.co.z += RSH - 0.03
SLURRY.location = (0, 0, -(RSH - 0.03))
# pipes: discharge (muck out) and feed (slurry in), along the tunnel floor to the back of the frame
PIPE_L = 70.0
Y_PD, Y_PF = 0.75, 1.55
zf = lambda y: -math.sqrt(RI * RI - y * y) + 0.32
bm = bmesh.new(); add_cyl_x(bm, 0.2, -PIPE_L, -1.85, Y_PD, zf(Y_PD), 24); PIPE_D = part("PipeDischarge", bm, M_PIPE_D)
bm = bmesh.new(); add_cyl_x(bm, 0.16, -PIPE_L, -1.85, Y_PF, zf(Y_PF), 24); PIPE_F = part("PipeFeed", bm, M_PIPE_F)
# back-up gantry frames behind the shield
for k in range(5):
    x = -LS - 3.0 - k * 3.2
    bm = bmesh.new(); add_box(bm, x - 0.12, x + 0.12, 2.2, 2.4, -2.2, 1.6); add_box(bm, x - 0.12, x + 0.12, 0.2, 2.4, 1.5, 1.7)
    add_box(bm, x - 1.6, x + 1.6, 1.0, 2.4, 1.15, 1.3, 1)
    part(f"Gantry{k}", bm, [M_DARK, M_STEEL])
# erector: pivot at the tunnel axis in the tail, arm along local +y
ERP = bpy.data.objects.new("ErectorPivot", None); CL.objects.link(ERP); ERP.parent = TBM; ERP.matrix_parent_inverse = Matrix.Identity(4)
ERP.location = (-LS + W / 2, 0, 0)
bm = bmesh.new(); add_cyl_x(bm, 0.65, -0.35, 0.35, 0, 0, 40, 0)
add_box(bm, -0.18, 0.18, 0.4, RI - 0.55, -0.22, 0.22, 0); add_box(bm, -0.55, 0.55, RI - 0.6, RI - 0.42, -0.35, 0.35, 1)
add_box(bm, -0.12, 0.12, 0.0, 0.5, -0.12, 0.12, 1)
ERECT = mesh_obj("Erector", bm, [M_ERECT, M_STEEL], ERP); bevel_mod(ERECT, 0.02)
# thrust jacks: barrels fixed in the shield, rods reach back to the newest ring's front face
JACK_A = [-60, -20, 20, 60]
JACK_X0 = -LS + W + 0.25                                                              # barrel rear (local x)
JACKS = []
for a in JACK_A:
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a)); r = (RI + RO) / 2
    bm = bmesh.new(); add_cyl_x(bm, 0.12, JACK_X0, JACK_X0 + 1.8, r * ca, r * sa, 24); part(f"JackBarrel{a}", bm, M_DARK)
    bm = bmesh.new(); add_cyl_x(bm, 0.07, -1.0, 0.0, 0, 0, 20)
    rod = part(f"JackRod{a}", bm, M_JACK); rod.location = (JACK_X0, r * ca, r * sa)
    bm = bmesh.new(); add_box(bm, -0.05, 0.05, -0.16, 0.16, -0.16, 0.16)
    shoe = mesh_obj(f"JackShoe{a}", bm, M_JACK); shoe.location = (0, r * ca, r * sa)
    JACKS.append((rod, shoe))

# ---------- lining rings (fixed in the world once built) ----------
SEG_A = [-60, 0, 60]
def seg_mesh(name, m_):
    bm = bmesh.new()
    add_sector(bm, RI, RO, -29.4, 29.4, 0.0, W - 0.045, 20, 0)
    add_sector(bm, RI - 0.012, RO - 0.05, -30.0, 30.0, W - 0.045, W - 0.005, 20, 1)   # ring-joint gasket (front face)
    add_sector(bm, RI - 0.012, RO - 0.05, 29.4, 30.0, 0.0, W - 0.045, 2, 1)           # long-joint gasket
    o = mesh_obj(name, bm, [m_, M_GASKET], link=False); bevel_mod(o, 0.01, 1); return o.data
ME_SEG, ME_HSEG = seg_mesh("SegmentMesh", M_SEG), seg_mesh("HeroSegmentMesh", M_HERO)
ring_x = lambda k: k * W - LS                                                          # ring k spans [ring_x, ring_x + W]
K_MIN, K_MAX = int(math.ceil((GX0 + 2 - (-LS)) / W)), 8
HERO_K = 5
T_SEG_HERO = [C["pieces"] + 0.05, C["bolts"] + 0.35, C["ring"] + 0.25]
RING_T = {}
for k in range(1, K_MAX + 1): RING_T[k] = t_reach(k * W)
RING_T[6], RING_T[7], RING_T[8] = C["build"], C["over"] + 0.1, C["over2"] + 0.1
def seg_times(k):
    if k <= 0: return [0.0, 0.0, 0.0]
    if k == HERO_K: return T_SEG_HERO
    t = RING_T[k]; return [t - 0.2, t - 0.1, t]
SEGS = {}
for k in range(K_MIN, K_MAX + 1):
    for j, a in enumerate(SEG_A):
        o = bpy.data.objects.new(f"Ring{k:+03d}_Seg{j}", ME_HSEG if k == HERO_K else ME_SEG); CL.objects.link(o)
        o.location = (ring_x(k), 0, 0); o.rotation_euler = (math.radians(a), 0, 0)
        t = seg_times(k)[j]
        if t > 0.01: vis(o, 1, True); vis(o, F(t), False)
        SEGS[(k, j)] = o
def newest_front(t):
    k_done = max([k for k in range(K_MIN, K_MAX + 1) if seg_times(k)[0] <= t + 1e-6])
    return ring_x(k_done) + W
# jacks: rod length = barrel rear (world) - newest ring front face
rod_len = []
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS; rod_len.append(max(0.05, XS[fr - 1] + JACK_X0 - newest_front(t)))
for rod, shoe in JACKS:
    bake(rod, "scale", 0, rod_len)
    bake(shoe, "location", 0, [XS[i] + JACK_X0 - rod_len[i] for i in range(FRAMES)])
# erector angle: goes to each segment's angle as it is placed, back to the bottom after a ring
EKEYS = [(0.0, -60.0)]
for k in range(1, K_MAX + 1):
    ts = seg_times(k); pre = ts[0] - (0.9 if k == HERO_K else 0.12)
    EKEYS.append((pre, -60.0))
    for tj, a in zip(ts, SEG_A): EKEYS.append((tj, a))
    EKEYS.append((ts[-1] + (0.6 if k == HERO_K else 0.15), -60.0))
EKEYS.sort()
def eang(t):
    if t <= EKEYS[0][0]: return EKEYS[0][1]
    for (t0, a0), (t1, a1) in zip(EKEYS, EKEYS[1:]):
        if t <= t1: return a0 + (a1 - a0) * ease((t - t0) / (t1 - t0)) if t1 > t0 else a1
    return EKEYS[-1][1]
bake(ERP, "rotation_euler", 0, [math.radians(eang((fr - 1) / FPS)) for fr in range(1, FRAMES + 1)])
# hero ring: the erector carries each segment and pushes it out onto the ring
CARRIED = []
for j, a in enumerate(SEG_A):
    o = bpy.data.objects.new(f"Carried_Seg{j}", ME_HSEG); CL.objects.link(o)
    o.parent = ERP; o.matrix_parent_inverse = Matrix.Identity(4)
    t_on = C["picks"] - 0.2 if j == 0 else T_SEG_HERO[j - 1]
    t_off = T_SEG_HERO[j]
    vis(o, 1, True); vis(o, F(t_on), False); vis(o, F(t_off), True)
    o.location = (-W / 2, 0, 0)
    ys = []
    for fr in range(1, FRAMES + 1):
        t = (fr - 1) / FPS; u = ease((t - (t_off - 0.45)) / 0.4)
        ys.append(-0.4 * (1 - u))
    # radial offset along the arm (local +y of the pivot)
    bake(o, "location", 1, ys); CARRIED.append(o)
# grout: shell between the rings and the ground, grows back from the tail on "grout"
bm = bmesh.new(); add_sector(bm, RO + 0.005, RB - 0.01, -90, 90, -1.0, 0.0, 40); GROUT = mesh_obj("Grout", bm, M_GROUT)
T_G = C["grout"]
bake(GROUT, "location", 0, [XS[i] - LS for i in range(FRAMES)])
bake(GROUT, "scale", 0, [max(0.001, (XS[i] - LS - GX0) * ease(((i) / FPS - T_G) / 1.6)) for i in range(FRAMES)])
vis(GROUT, 1, True); vis(GROUT, F(T_G), False)
# tunnel lamps along the finished lining (for the CTA)
bm = bmesh.new()
for k in range(K_MIN, 1):
    x = ring_x(k) + W / 2; add_box(bm, x - 0.35, x + 0.35, 2.05, 2.15, 2.0, 2.08)
LAMPS = mesh_obj("TunnelLamps", bm, M_LAMP)

# ---------- chips, water / slurry arrows, pipe pulses ----------
bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.09); ME_CHIP = bpy.data.meshes.new("Chip"); bm.to_mesh(ME_CHIP); bm.free()
ME_CHIP.materials.append(M_CHIP)
T_CH0, T_CH1 = C["crush"] - 0.3, C["filled"]
for i in range(26):
    o = bpy.data.objects.new(f"Chip{i}", ME_CHIP); CL.objects.link(o)
    o.scale = (random.uniform(0.6, 1.6),) * 3; o.rotation_euler = (random.random() * 6, random.random() * 6, 0)
    y0, z0, ph, per = random.uniform(-2.0, 2.0), random.uniform(-1.5, 2.8), random.random(), random.uniform(0.9, 1.4)
    px, py, pz = [], [], []
    for fr in range(1, FRAMES + 1):
        t = (fr - 1) / FPS; u = ((t / per) + ph) % 1.0
        z = z0 - (z0 + 3.2) * u * u
        px.append(XS[fr - 1] - 0.45 - 0.9 * u); py.append(y0); pz.append(max(-3.3, z))
    bake(o, "location", 0, px); bake(o, "location", 1, py); bake(o, "location", 2, pz)
    vis(o, 1, True); vis(o, F(T_CH0), False); vis(o, F(T_CH1), True)
ME_AR = arrow_mesh("ArrowMesh", 1.1, 0.07, M_ARROW_W)
T_W0, T_W1, T_S0, T_S1 = C["open2"] - 0.1, C["pushes"] + 0.5, C["pushes"], C["muck"] - 0.1
W_ARROWS = []
for i, z in enumerate([-2.4, -1.0, 0.4, 1.8, 3.0]):
    o = bpy.data.objects.new(f"WaterArrow{i}", ME_AR); CL.objects.link(o)
    o.rotation_euler = (0, 0, math.pi)                                                  # points -x, toward the face
    ph = i * 0.27; px = []
    for fr in range(1, FRAMES + 1):
        t = (fr - 1) / FPS; u = ((t * 0.9) + ph) % 1.0
        back = ease((t - C["pushes"]) / 0.6) * 2.5                                       # pushed away once the slurry pushes back
        px.append(XS[fr - 1] + 3.6 - 1.6 * u + back)
    bake(o, "location", 0, px); o.location[1] = -0.35; o.location[2] = z
    vis(o, 1, True); vis(o, F(T_W0), False); vis(o, F(T_W1), True); W_ARROWS.append(o)
ME_AR2 = arrow_mesh("ArrowMeshSlurry", 0.9, 0.07, M_ARROW_S)
for i, z in enumerate([-2.0, -0.6, 0.8, 2.2]):
    o = bpy.data.objects.new(f"SlurryArrow{i}", ME_AR2); CL.objects.link(o)
    ph = i * 0.31; px = []
    for fr in range(1, FRAMES + 1):
        t = (fr - 1) / FPS; u = ((t * 1.1) + ph) % 1.0
        px.append(XS[fr - 1] + 0.35 + 0.9 * u)
    bake(o, "location", 0, px); o.location[1] = -0.35; o.location[2] = z
    vis(o, 1, True); vis(o, F(T_S0), False); vis(o, F(T_S1), True)
bm = bmesh.new(); add_cyl_x(bm, 0.24, -0.45, 0.45, 0, 0, 16); ME_PUL = bpy.data.meshes.new("Pulse"); bm.to_mesh(ME_PUL); bm.free()
T_P0, T_P1 = C["muck"] - 0.1, C["behind"] - 0.1
for i in range(10):
    for kind, y_, rr, m_, sgn in (("Muck", Y_PD, 1.0, M_PULSE_D, -1), ("Feed", Y_PF, 0.75, M_PULSE_F, 1)):
        me = ME_PUL.copy(); me.materials.append(m_)
        o = bpy.data.objects.new(f"Pulse{kind}{i}", me); CL.objects.link(o); o.scale = (1, rr, rr)
        px = []
        for fr in range(1, FRAMES + 1):
            t = (fr - 1) / FPS; u = ((t * 0.22) + i / 10) % 1.0
            px.append(XS[fr - 1] - 2.2 - 40.0 * (u if sgn < 0 else 1 - u))
        bake(o, "location", 0, px); o.location[1] = y_; o.location[2] = zf(y_)
        vis(o, 1, True); vis(o, F(T_P0), False); vis(o, F(T_P1), True)

# ---------- Set A visibility + cut open ----------
key(SH_F, "location", F(C["open"] - 0.1), (0, 0, 0)); key(SH_F, "location", F(C["open"] + 0.8), (0, -9.0, 2.5))
vis(SH_F, 1, False); vis(SH_F, F(C["open"] + 0.85), True)
vis(SLURRY, 1, True); vis(SLURRY, F(C["filled"] - 0.25), False)
key(SLURRY, "scale", 1, (1, 1, 0.01)); key(SLURRY, "scale", F(C["filled"] - 0.25), (1, 1, 0.01)); key(SLURRY, "scale", F(C["slurry"] + 0.3), (1, 1, 1))

# ---------- Set B: Channel section diorama (x offset 2000) ----------
OX = 2000.0
def Sx(u):      # ground / seabed surface
    if u < -17: return 5.0
    if u < -15.5: return 5.0 + (-0.8 - 5.0) * ease((u + 17) / 1.5)
    if u < 15.5: return -0.8 - 1.3 * math.cos(math.pi * u / 31.0) + 0.15 * math.sin(u * 0.9)
    if u < 17: return -0.8 + (3.6 + 0.8) * ease((u - 15.5) / 1.5)
    return 3.6
def Mtop(u): return -3.6 - 0.9 * math.cos(math.pi * u / 34.0) + 0.35 * math.sin(u / 4.0)
def Mbot(u): return Mtop(u) - 3.0 - 0.3 * math.sin(u / 6.0 + 1.0)
def Zt(u): return Mtop(u) - 1.45 - 0.1 * math.sin(u / 6.0 + 1.0)
US = [-22 + 44 * i / 160 for i in range(161)]
def layer(name, top, bot, m_, y1=6.0):
    pts = [(OX + u, top(u)) for u in US] + [(OX + u, bot(u)) for u in reversed(US)]
    bm = bmesh.new(); add_prism_y(bm, pts, 0.0, y1); return mesh_obj(name, bm, m_)
CH_CHALK = layer("ChChalk", lambda u: Sx(u) - (0.25 if abs(u) < 15.5 else 0.6), Mtop, M_CHALK)
CH_MARL = layer("ChChalkMarl", Mtop, Mbot, M_MARL)
CH_CLAY = layer("ChClay", Mbot, lambda u: -13.0, M_CLAY)
CH_SAND = layer("ChSeabed", lambda u: Sx(u), lambda u: Sx(u) - (0.25 if abs(u) < 15.5 else 0.6), M_SAND)
bm = bmesh.new(); add_box(bm, OX - 22, OX - 16.6, 0.0, 6.0, 5.0, 5.15); add_box(bm, OX + 16.6, OX + 22, 0.0, 6.0, 3.6, 3.75); mesh_obj("ChLand", bm, M_LAND)
sea_pts = [(OX + u, 1.6) for u in [-16.3 + 32.6 * i / 60 for i in range(61)]] + [(OX + u, Sx(u) - 0.01) for u in reversed([-16.3 + 32.6 * i / 60 for i in range(61)])]
bm = bmesh.new(); add_prism_y(bm, sea_pts, 0.0, 6.0); CH_SEA = mesh_obj("ChSea", bm, M_WATER)
U_MEET, U_UK, U_FR = 2.0, -17.5, 17.5
uk_pts = [(OX + u, 0.0, Zt(u)) for u in [U_UK + (U_MEET - U_UK) * i / 120 for i in range(121)]]
fr_pts = [(OX + u, 0.0, Zt(u)) for u in [U_FR + (U_MEET - U_FR) * i / 120 for i in range(121)]]
TUBE_UK = curve_obj("DriveUK", uk_pts, False, 0.42, M_TUBE, 3); TUBE_FR = curve_obj("DriveFR", fr_pts, False, 0.42, M_TUBE, 3)
T_CH = C["under"] - 0.25; T_MEET = C["met"] + 0.1
for tube in (TUBE_UK, TUBE_FR):
    cu = tube.data
    key(cu, "bevel_factor_end", F(T_CH), 0.55, "LINEAR"); key(cu, "bevel_factor_end", F(T_MEET), 1.0, "LINEAR")
M_MINI_FR, _ = mat("MiniTBM_FR", (0.70, 0.50, 0.10), 0.35, 0.85)
def mini_tbm(name, m_):
    bm = bmesh.new(); add_cyl_x(bm, 0.5, -1.3, 0.0, 0, 0, 32, 0); add_cyl_x(bm, 0.54, 0.0, 0.12, 0, 0, 32, 1)
    return mesh_obj(name, bm, [m_, M_CUTTER])
MINI_UK, MINI_FR = mini_tbm("MiniTBM_UK", M_MINI), mini_tbm("MiniTBM_FR", M_MINI_FR)
MINI_FR.rotation_euler = (0, 0, math.pi)
def tip(pts, f):
    i = min(len(pts) - 1, max(0, int(round(f * (len(pts) - 1))))); return Vector(pts[i])
mu, mf = [[], [], []], [[], [], []]; rot_uk = []
T_ST0, T_ST1 = C["steered"] - 0.05, C["buried"] + 0.1
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS; f = 0.55 + 0.45 * lin((t - T_CH) / (T_MEET - T_CH))
    a, b = tip(uk_pts, f) + Vector((-0.6, 0, 0)), tip(fr_pts, f) + Vector((0.6, 0, 0))
    s = ease((t - T_ST0) / (T_ST1 - T_ST0))                                             # British machine turns down into the rock
    a = a + Vector((-0.2 + 1.9 * s, 0, -1.75 * s)) if s > 0 else a
    rot_uk.append(-math.radians(42) * s)
    for ax in range(3): mu[ax].append(a[ax]); mf[ax].append(b[ax])
for ax in range(3): bake(MINI_UK, "location", ax, mu[ax]); bake(MINI_FR, "location", ax, mf[ax])
bake(MINI_UK, "rotation_euler", 1, [-r for r in rot_uk])
# a little rubble plug closes over the buried machine
bm = bmesh.new(); add_box(bm, -0.9, 0.9, -0.05, 1.2, -0.8, 0.8); RUBBLE = mesh_obj("BuriedFill", bm, M_CLAY)
RUBBLE.location = (OX + U_MEET + 0.9, -0.62, Zt(U_MEET) - 1.75); RUBBLE.rotation_euler = (0, math.radians(42), 0)
vis(RUBBLE, 1, True); vis(RUBBLE, F(C["buried"] + 0.35), False)
key(RUBBLE, "scale", F(C["buried"] + 0.35), (0.2, 0.2, 0.2)); key(RUBBLE, "scale", F(C["buried"] + 0.75), (1, 1, 1))

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
pulse(B_CUTTER, C["cutting"], 0.6, 1.4); hold_glow(B_DISC, C["discs"], C["chips"] + 0.6, 1.6)
hold_glow(B_SLURRY, C["pressurized"], C["holds"] + 0.4, 0.05)
hold_glow(B_PIPE_D, C["pumped"], C["sent"] + 0.5, 1.5); pulse(B_PIPE_F, C["sent"], 2.0, 0.6)
hold_glow(B_SHIELD, C["shield"] - 0.1, C["inside"] + 0.2, 0.7)
hold_glow(B_ERECT, C["arm"], C["ring"] + 0.4, 0.25); hold_glow(B_HERO, C["concrete"], C["ring"] + 0.6, 0.35)
hold_glow(B_JACK, C["jacks"], C["forward"] + 0.3, 2.0)
hold_glow(B_GASKET, C["rubber"], C["grout"] - 0.4, 6.0)
s = B_GROUT.inputs["Emission Strength"]; key(s, "default_value", F(T_G), 4.0); key(s, "default_value", F(C["under"] - 0.6), 3.0); key(s, "default_value", F(C["under"] - 0.2), 0.0)
hold_glow(B_MARL, C["layer"], C["through"] + 0.5, 0.9)
s = B_MINI.inputs["Emission Strength"]; key(s, "default_value", F(C["buried"] - 0.1), 0.0); key(s, "default_value", F(C["buried"] + 0.2), 2.5)
key(s, "default_value", F(C["would"] - 0.3), 1.2)

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 35
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 9; cam_d.dof.focus_object = TGT
cam_d.clip_start = 0.05; cam_d.clip_end = 400
TL5 = ring_x(HERO_K) + W / 2                                                             # hero ring centre (world x)
J56 = ring_x(-6) + W                                                                  # joint between hero ring and the next
SHOTS = [  # (time, mode, cam, target, lens[, "cut"])  mode "m" = relative to the machine face X(t), "w" = world
    (0.0, "m", (7.0, -21.0, 5.0), (-6.0, 0.0, 3.2), 22),
    (C["machine"], "m", (6.0, -18.5, 3.8), (-5.0, 0.0, 1.6), 22),
    (C["lets"], "m", (-3.5, -13.5, 1.6), (-4.0, 0.0, 0.0), 24),
    (C["front"], "m", (5.6, -7.2, 1.8), (0.1, 0.0, 0.2), 26),
    (C["steel"], "m", (3.4, -4.6, 2.2), (0.3, 0.0, 0.9), 28),
    (C["chips"] - 0.2, "m", (-0.2, -7.0, 0.2), (-0.8, 0.0, -0.6), 28),
    (C["but"], "m", (2.5, -15.5, 3.2), (2.0, 0.0, 2.0), 24),
    (C["open2"] - 0.1, "m", (2.8, -10.0, 1.0), (1.8, 0.0, 0.4), 26),
    (C["so"], "m", (-0.4, -8.6, 0.6), (-0.6, 0.0, 0.0), 26),
    (C["pushes"], "m", (1.6, -9.6, 0.8), (1.2, 0.0, 0.2), 26),
    (C["muck"] - 0.1, "m", (-9.0, -9.5, 3.2), (-13.0, 1.0, -2.0), 24),
    (C["sent"], "m", (-6.0, -9.0, 2.6), (-11.0, 1.0, -2.0), 24),
    (C["behind"], "m", (-5.0, -13.0, 1.8), (-5.0, 0.0, 0.0), 24),
    (C["inside"] - 0.2, "w", (TL5 - 2.6, -6.4, -0.6), (TL5 + 0.2, 0.8, 0.1), 24),
    (C["ring"] + 0.4, "w", (TL5 - 3.2, -6.8, -0.3), (TL5 + 0.4, 0.8, 0.2), 24),
    (C["then"], "w", (TL5 - 1.2, -7.6, 1.2), (TL5 + 1.8, 0.8, 0.6), 24),
    (C["dig2"] - 0.1, "w", (TL5 - 1.0, -17.0, 2.5), (TL5 + 2.5, 0.0, 0.0), 22),
    (C["every"] - 0.1, "w", (J56 - 1.8, -1.6, -1.0), (J56 + 0.2, 2.0, 1.1), 26),
    (C["squeezed"], "w", (J56 - 1.3, -1.3, -0.9), (J56 + 0.1, 2.2, 1.0), 28),
    (C["grout"] - 0.1, "m", (-LS - 4.0, -5.2, 4.2), (-LS - 6.0, 0.0, 3.3), 26),
    (C["rings"] + 0.2, "m", (-LS - 5.0, -5.6, 4.3), (-LS - 7.5, 0.0, 3.2), 26),
    (C["under"] - 0.15, "w", (OX - 6.0, -34.0, 6.0), (OX - 1.0, 0.0, -2.5), 24, "cut"),
    (C["eleven"] + 0.2, "w", (OX - 4.5, -31.0, 5.0), (OX - 0.5, 0.0, -3.0), 24),
    (C["layer"] - 0.1, "w", (OX - 5.0, -22.0, 1.5), (OX - 4.0, 0.0, -4.8), 24),
    (C["y1990"] - 0.1, "w", (OX + U_MEET, -21.0, 0.5), (OX + U_MEET, 0.0, -5.2), 24),
    (C["met"] + 0.4, "w", (OX + U_MEET - 0.5, -18.0, 0.0), (OX + U_MEET, 0.0, -5.4), 26),
    (C["british"], "w", (OX + U_MEET - 2.0, -17.0, -0.5), (OX + U_MEET + 0.4, 0.0, -6.0), 26),
    (C["would"] - 0.1, "w", (-LS + 2 * W - 8.0, -2.2, -0.9), (-LS - 30.0, 1.2, 0.6), 20, "cut"),
    (C["end"], "w", (-LS + 2 * W - 10.5, -2.0, -0.8), (-LS - 32.0, 1.2, 0.6), 20),
]
cam_loc, cam_tgt, cam_lens = [], [], []
def shot_at(k, t):
    s = SHOTS[k]
    o = Vector((X(t), 0, 0)) if s[1] == "m" else Vector((0, 0, 0))
    return o + Vector(s[2]), o + Vector(s[3]), s[4]
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = shot_at(k, t)
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 5 and SHOTS[k + 1][5] == "cut"):
        t1 = SHOTS[k + 1][0]; tr = 0.7 if (t1 - SHOTS[k][0]) > 1.4 else (t1 - SHOTS[k][0]) * 0.5
        if t > t1 - tr:
            l1, g1, n1 = shot_at(k + 1, t); u = ease((t - (t1 - tr)) / tr)
            l0, g0, n0 = l0.lerp(l1, u), g0.lerp(g1, u), n0 + (n1 - n0) * u
    cam_loc.append(l0); cam_tgt.append(g0); cam_lens.append(n0)
for i in range(FRAMES):
    t = i / FPS; cam_loc[i] = cam_loc[i] + Vector((0.07 * math.sin(t * 0.7), 0.0, 0.05 * math.sin(t * 0.9 + 1.0)))
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
gr = wn.new("ShaderNodeValToRGB"); e = gr.color_ramp.elements; e[0].color = (0.004, 0.006, 0.009, 1); e[1].color = (0.025, 0.04, 0.055, 1)
wl.new(grad.outputs["Fac"], gr.inputs[0])
bg_dark = wn.new("ShaderNodeBackground"); wl.new(gr.outputs[0], bg_dark.inputs["Color"])
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.12
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_ref.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
def area(name, loc, size, power, rgb=(1, 1, 1), target=None, parent=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    if parent: o.parent = parent
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
LT_A = bpy.data.objects.new("LightTargetA", None); scene.collection.objects.link(LT_A); LT_A.parent = TBM; LT_A.location = (-3.0, 0, 0)
LT_B = bpy.data.objects.new("LightTargetB", None); scene.collection.objects.link(LT_B); LT_B.location = (OX, 0, -3)
area("KeyA", (-6.0, -12.0, 9.0), 9.0, 2200, (1.0, 0.95, 0.88), LT_A, TBM)
area("RimA", (6.0, 9.0, 5.0), 6.0, 900, (0.70, 0.82, 1.0), LT_A, TBM)
area("FillA", (2.0, -10.0, -4.0), 7.0, 700, (1.0, 0.9, 0.82), LT_A, TBM)
area("TunnelFillA", (-LS - 14.0, -6.0, 0.5), 6.0, 900, (1.0, 0.93, 0.85), LT_A, TBM)
area("KeyB", (OX - 12.0, -30.0, 18.0), 16.0, 9000, (1.0, 0.95, 0.88), LT_B)
area("FillB", (OX + 14.0, -26.0, -2.0), 12.0, 3500, (0.75, 0.85, 1.0), LT_B)
area("CamFill", (0, 0, 0), 2.5, 70, (1.0, 0.96, 0.9), TGT, cam)

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

# ---------- export cues, events and projected anchors for the typography ----------
ra = (RI + RO) / 2
ANCH = {"cutter": (TBM, Vector((0.2, -0.3, 2.4))), "discs": (TBM, Vector((0.32, -1.8, 1.4))), "chamber": (TBM, Vector((-1.0, -0.4, -1.6))),
        "face_ahead": (TBM, Vector((1.6, -0.35, 1.2))), "slurry": (TBM, Vector((-1.0, -0.5, 0.6))),
        "pipe": (TBM, Vector((-9.0, Y_PD, zf(Y_PD) + 0.2))), "shield": (TBM, Vector((-5.0, -0.2, RSO))),
        "erector": (ERP, Vector((0.0, RI - 0.6, 0.0))), "segment": (None, Vector((TL5, ra * math.cos(math.radians(60)), ra * math.sin(math.radians(60))))),
        "jack": (TBM, Vector((JACK_X0 - 0.3, ra * math.cos(math.radians(60)), ra * math.sin(math.radians(60))))),
        "gasket": (None, Vector((J56, RI * math.cos(math.radians(25)), RI * math.sin(math.radians(25))))),
        "grout": (TBM, Vector((-LS - 6.0, 0.0, (RO + RB) / 2))), "sea": (None, Vector((0.0, 0.0, Z_SEABED + 2.5))),
        "marl": (None, Vector((OX - 8.0, 0.0, (Mtop(-8.0) + Mbot(-8.0)) / 2 + 0.6))), "meet": (None, Vector((OX + U_MEET, 0.0, Zt(U_MEET)))),
        "uk": (None, Vector((OX - 19.0, 0.0, 5.2))), "fr": (None, Vector((OX + 19.0, 0.0, 3.8))), "uk_tbm": (MINI_UK, Vector((-0.6, -0.5, 0.0)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, (ob, local) in ANCH.items():
        w = local if ob is None else ob.matrix_world @ local
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)])
ring_events = sorted(set(round(t, 3) for k in range(1, K_MAX + 1) for t in seg_times(k)))
push_events = [[round(a, 3), round(b, 3)] for (a, _, _), (b, _, _) in zip(XKEYS, XKEYS[1:]) if b - a < 4.0 and Xm(b) - Xm(a) > 0.5]
events = {"segment_clunk": ring_events, "push": push_events, "open": round(C["open"] + 0.1, 3), "meet": round(T_MEET, 3),
          "channel": [round(C["under"] - 0.15, 3), round(C["would"] - 0.1, 3)], "grout": round(T_G, 3)}
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS", events, "DUR", DUR, "FRAMES", FRAMES)

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
