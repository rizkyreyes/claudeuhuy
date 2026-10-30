# Tower-Crane-Climb-3D: how a tower crane builds itself taller. Studio cutaway in Blender Cycles. Every cue is a word in the VO.
# Set A (origin): crane (lattice mast sections, slewing unit + cab, jib with trolley + hook, counter-jib + blocks, climbing frame with two hydraulic rams
#   and a section platform) next to a building under construction (floors + columns). A mobile crane erects the first pieces (hidden after "counterweights").
# Set B (x = 2000): a core shaft inside a building with the same crane top climbing inside it (collars on the floors).
# No people anywhere. Sizes are illustrative, none are spoken. Climbing frame, rams, top assembly, trolley, hook, section, floors are baked per frame.
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
DUR = round(WORDS[-1]["end"] + VO + 0.8, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(8)

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
for name, word in [("how", "how"), ("tower", "tower"), ("crane", "crane"), ("build", "build"), ("taller", "taller"), ("lets", "let's"), ("cut", "cut"), ("open", "open"),
                   ("starts", "starts"), ("small", "small"), ("mobile", "mobile"), ("stands", "stands"), ("base", "base"), ("few", "few"), ("mast", "mast"),
                   ("sections", "sections"), ("cab", "cab"), ("jib", "jib"), ("counterweights", "counterweights"), ("after", "after"), ("grows", "grows"),
                   ("building", "building"), ("heres", "here's"), ("trick", "trick"), ("under", "under"), ("cab2", "cab"), ("climbing", "climbing"), ("frame", "frame"),
                   ("wraps", "wraps"), ("mast2", "mast"), ("operator", "operator"), ("slides", "slides"), ("trolley", "trolley"), ("jib2", "jib"), ("balanced", "balanced"),
                   ("over", "over"), ("mast3", "mast"), ("then", "then"), ("hooks", "hooks"), ("new", "new"), ("mast4", "mast"), ("section", "section"),
                   ("now", "now"), ("frame2", "frame"), ("work", "work"), ("hydraulic", "hydraulic"), ("rams", "rams"), ("push", "push"), ("mast5", "mast"),
                   ("lift", "lift"), ("entire", "entire"), ("top", "top"), ("cab3", "cab"), ("jib3", "jib"), ("counterweights2", "counterweights"), ("all", "all"),
                   ("that", "that"), ("opens", "opens"), ("gap", "gap"), ("crane2", "crane"), ("slides2", "slides"), ("section2", "section"), ("in", "in"),
                   ("crew", "crew"), ("locks", "locks"), ("then2", "then"), ("rams2", "rams"), ("let", "let"), ("weight", "weight"), ("settles", "settles"),
                   ("longer", "longer"), ("mast6", "mast"), ("taller2", "taller"), ("repeats", "repeats"), ("climbs", "climbs"), ("one", "one"), ("strict", "strict"),
                   ("rule", "rule"), ("jib4", "jib"), ("swing", "swing"), ("twisting", "twisting"), ("damage", "damage"), ("mast7", "mast"), ("as", "as"),
                   ("rises", "rises"), ("steel", "steel"), ("ties", "ties"), ("anchor", "anchor"), ("building2", "building"), ("wind", "wind"), ("tip", "tip"),
                   ("some", "some"), ("cranes", "cranes"), ("inside", "inside"), ("elevator", "elevator"), ("shaft", "shaft"), ("so", "so"), ("machine", "machine"),
                   ("skyscraper", "skyscraper"), ("also", "also"), ("itself", "itself"), ("would", "would"), ("cab4", "cab"), ("city", "city"), ("tell", "tell"),
                   ("comments", "comments"), ("if", "if"), ("follow", "follow")]:
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
def bake_fn(owner, path, index, fn): return bake(owner, path, index, [fn(t) for t in TS])
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("TowerCrane")
TS = [(fr - 1) / FPS for fr in range(1, FRAMES + 1)]

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
def glow(bsdf, keys):
    """Emission strength keys [(t, value), ...] (linear between them)."""
    inp = bsdf.inputs["Emission Strength"]
    for t, v in keys:
        inp.default_value = v; inp.keyframe_insert("default_value", frame=F(t))
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
M_MAST, B_MAST = mat("MastYellow", (0.80, 0.52, 0.04), 0.45, 0.5, GOLD)
M_JIB, B_JIB = mat("JibYellow", (0.82, 0.55, 0.05), 0.45, 0.5, GOLD)
M_FRAME, B_FRAME = mat("ClimbFrame", (0.06, 0.22, 0.42), 0.4, 0.6, CYAN)
M_RAMB, B_RAMB = mat("RamBody", (0.20, 0.55, 0.70), 0.35, 0.7, CYAN)
M_ROD, B_ROD = mat("RamRod", (0.85, 0.86, 0.88), 0.15, 1.0, CYAN)
M_COLLAR, B_COLLAR = mat("Collar", (0.70, 0.12, 0.08), 0.5, 0.5, RED)
M_NEW, B_NEW = mat("NewSection", (0.88, 0.62, 0.08), 0.4, 0.5, GOLD)
M_CAB, _ = mat("CabShell", (0.85, 0.85, 0.82), 0.4, 0.2)
M_GLASS, B_GLASS = mat("CabGlass", (0.04, 0.07, 0.10), 0.1, 0.0, (1.0, 0.85, 0.6)); B_GLASS.inputs["Emission Strength"].default_value = 1.2
M_SLEW, _ = mat("Slew", (0.18, 0.19, 0.20), 0.5, 0.7)
M_CWB, B_CWB = mat("CounterBlock", (0.34, 0.34, 0.33), 0.85, 0.0, GOLD, 12)
M_ROPE, _ = mat("Wire", (0.75, 0.78, 0.80), 0.35, 1.0)
M_HOOK, B_HOOK = mat("Hook", (0.60, 0.10, 0.08), 0.4, 0.6, GOLD)
M_TROLLEY, _ = mat("Trolley", (0.15, 0.17, 0.20), 0.5, 0.7)
M_CONC, _ = mat("Concrete", (0.22, 0.22, 0.22), 0.9, 0.0, GOLD, 18)
M_SLAB, _ = mat("FloorSlab", (0.46, 0.45, 0.42), 0.88, 0.0, GOLD, 20)
M_COL, _ = mat("Column", (0.34, 0.34, 0.33), 0.85, 0.0, GOLD, 16)
M_GROUND, _ = mat("Ground", (0.10, 0.10, 0.10), 0.9, 0.0, GOLD, 10)
M_FOUND, _ = mat("Foundation", (0.40, 0.38, 0.35), 0.85, 0.0, GOLD, 25)
M_TIE, B_TIE = mat("Tie", (0.85, 0.87, 0.90), 0.3, 0.9, GOLD)
M_WIND, B_WIND = mat("Wind", (0.30, 0.90, 1.0), 0.3, 0.0, CYAN); B_WIND.inputs["Emission Strength"].default_value = 4.0
M_TRUCK, _ = mat("Truck", (0.80, 0.20, 0.08), 0.5, 0.4)
M_TIRE, _ = mat("Tire", (0.03, 0.03, 0.03), 0.9)
M_BOOM, _ = mat("Boom", (0.85, 0.30, 0.10), 0.45, 0.5)
M_CITY, _ = mat("City", (0.085, 0.10, 0.14), 0.75, 0.0, (1.0, 0.8, 0.5), 3)
M_CITY2, _ = mat("City2", (0.12, 0.11, 0.11), 0.8, 0.0, (1.0, 0.8, 0.5), 4)
M_CITY3, _ = mat("City3", (0.07, 0.09, 0.13), 0.7, 0.0, (1.0, 0.8, 0.5), 3)
M_WIN, _ = mat("WindowDark", (0.02, 0.03, 0.05), 0.15, 0.6)
M_WINLIT, B_WINLIT = mat("WindowLit", (1.0, 0.85, 0.6), 0.4, 0.0, (1.0, 0.78, 0.45)); B_WINLIT.inputs["Emission Strength"].default_value = 1.4
M_GLOW, B_GLOW = mat("GapGlow", (1.0, 0.8, 0.3), 0.5, 0.0, GOLD); B_GLOW.inputs["Emission Strength"].default_value = 8.0
M_LINE, B_LINE = mat("OldTop", (0.25, 0.9, 1.0), 0.5, 0.0, CYAN); B_LINE.inputs["Emission Strength"].default_value = 6.0

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
def unit_rope(name, r, m_, parent=None):
    """Unit rope hanging DOWN from its origin (z 0 .. -1): scale z = length."""
    bm = bmesh.new(); add_cyl(bm, r, 1.0, "Z", (0, 0, -0.5), 8); return mesh_obj(name, bm, m_, parent)
def unit_post(name, r, m_, parent=None):
    """Unit rod standing UP from its origin (z 0 .. 1): scale z = length."""
    bm = bmesh.new(); add_cyl(bm, r, 1.0, "Z", (0, 0, 0.5), 12); return mesh_obj(name, bm, m_, parent)

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
def drop(t, t0, h=7.0, d=0.55):
    """Vertical offset of a piece craned in at t0 (starts h above, settles with a tiny bounce)."""
    p = (t - t0) / d
    if p <= 0: return h
    if p >= 1: return 0.0 if t > t0 + d + 0.25 else 0.12 * math.sin(math.pi * (t - t0 - d) / 0.25)
    return h * (1 - ease(p))

# ---------- layout ----------
H, W = 3.0, 1.6                      # mast section height and width
JIB_L, CJIB_L = 19.0, 7.0
BX0, BX1, BY0, BY1 = 6.5, 16.5, -5.0, 5.0     # building footprint
FLOOR = 3.0
OX = 2000.0                          # Set B offset
TSLIDE0, TSLIDE1 = C["slides2"] + 0.0, C["in"] + 0.15
T_HIDE = C["starts"] - 0.2           # the mature crane vanishes here, the build-up begins (hard cut)
T_MOBILE0, T_MOBILE1 = C["mobile"] - 0.3, C["after"] + 0.1

# TOP (z of the underside of the slewing unit = top of the mast) over time
TOPZ = PW([(0, 18.0), (T_HIDE - 0.05, 18.0), (T_HIDE, 9.0), (C["grows"] - 0.4, 9.0), (C["grows"] + 0.1, 12.0), (C["grows"] + 0.25, 12.0), (C["grows"] + 0.7, 15.0),
           (C["grows"] + 0.85, 15.0), (C["grows"] + 1.3, 18.0),
           (C["lift"] - 0.1, 18.0), (C["opens"] - 0.6, 21.12), (C["rams2"] - 0.4, 21.12), (C["settles"] + 0.2, 21.0),
           (C["repeats"] - 0.3, 21.0), (C["repeats"] + 0.35, 24.0), (C["repeats"] + 0.55, 24.0), (C["climbs"] + 0.2, 27.0),
           (C["machine"] + 0.4, 27.0), (C["machine"] + 1.2, 30.0)])
COLLAR = PW([(0, 15.0), (C["rams2"] + 0.6, 15.0), (C["settles"] + 1.0, 18.0), (C["repeats"] + 0.35, 18.0),
             (C["repeats"] + 0.55, 21.0), (C["climbs"] + 0.2, 21.0), (C["climbs"] + 0.8, 24.0),
             (C["machine"] + 1.2, 24.0), (C["machine"] + 1.8, 27.0)])
TROLLEY_X = PW([(0, 12.0), (C["operator"] + 0.3, 12.0), (C["balanced"] + 0.2, 1.7)])
SEC_Z0 = 15.0                        # platform height before the first full climb = TOPZ - H
def plat_z(t): return TOPZ(t) - H
# the carried section (mast section index 6): ground -> hook -> platform -> slides in -> sits on the mast
T_PICK0, T_PICK1, T_LAND = C["then"] + 0.2, C["section"] + 0.2, C["now"] - 0.15
def hook_goal(t):
    """Hook block height (world z) and the carried section bottom z."""
    if t < T_PICK0 - 0.8: return None
    return None
def sec_pos(t):
    # returns (x, z_bottom) of the new section
    if t < T_PICK0: return (2.6, 0.2)
    if t < T_LAND: return (2.6, 0.2 + (plat_z(T_LAND) - 0.2) * ease((t - T_PICK0 - 0.2) / (T_LAND - T_PICK0 - 0.2)) if t > T_PICK0 + 0.2 else 0.2)
    x = 2.6 * (1 - ease((t - TSLIDE0) / (TSLIDE1 - TSLIDE0)))
    z = plat_z(t) if t < TSLIDE1 + 0.1 else max(18.0, plat_z(t))
    if t > TSLIDE1: z = max(18.0, plat_z(t))
    return (x, z)
def hook_z(t):
    """World z of the hook block."""
    jib_z = TOPZ(t) + 1.5
    rest = jib_z - 1.4
    if t < T_PICK0 - 0.9: return rest
    if t < T_PICK0 + 0.0: return rest + (3.6 - rest) * ease((t - (T_PICK0 - 0.9)) / 0.9)        # down to the section top (z 3.4)
    if t < T_LAND: return sec_pos(t)[1] + H + 0.4
    if t < T_LAND + 0.6: return plat_z(t) + H + 0.4 + (rest - (plat_z(t) + H + 0.4)) * ease((t - T_LAND) / 0.6)
    return rest

# ---------- ground, foundation, building, city ----------
G = empty("Ground")
box("GroundBlock", -70, 70, -60, 60, -30, -0.001, M_GROUND)
box("Foundation", -2.6, 2.6, -2.6, 2.6, -2.5, 0.0, M_FOUND)
box("Footing", -3.4, 3.4, -3.4, 3.4, -3.5, -2.5, M_FOUND)
box("BuildingPad", BX0 - 0.6, BX1 + 0.6, BY0 - 0.6, BY1 + 0.6, -1.2, 0.0, M_FOUND)
random.seed(21)
def city_building(name, cx, cy, w, d, h, body):
    """Tower with a window grid on the camera-facing (-y) and the +x/-x faces, a stepped top and rooftop plant."""
    bm = bmesh.new(); add_box(bm, cx - w, cx + w, cy - d, cy + d, 0, h, 0)
    if h > 40 and random.random() < 0.6: add_box(bm, cx - w * 0.7, cx + w * 0.7, cy - d * 0.7, cy + d * 0.7, h, h + random.uniform(3, 7), 0)
    add_box(bm, cx - w * 0.3, cx + w * 0.1, cy - d * 0.3, cy + d * 0.2, h, h + 1.6, 0)
    cols = max(3, int(w * 2 / 2.2)); rows = int((h - 3) / 3.0)
    for r_ in range(rows):
        for c_ in range(cols):
            x0 = cx - w + (c_ + 0.5) * (2 * w / cols); z0 = 2.5 + r_ * 3.0
            lit = 2 if random.random() < 0.16 else 1
            add_box(bm, x0 - 0.65, x0 + 0.65, cy - d - 0.06, cy - d, z0, z0 + 1.7, lit)
    for side in (-1, 1):
        for r_ in range(rows):
            for c_ in range(max(2, int(d * 2 / 2.4))):
                y0 = cy - d + (c_ + 0.5) * (2 * d / max(2, int(d * 2 / 2.4))); z0 = 2.5 + r_ * 3.0
                lit = 2 if random.random() < 0.22 else 1
                add_box(bm, cx + side * w, cx + side * (w + 0.06), y0 - 0.6, y0 + 0.6, z0, z0 + 1.7, lit)
    return mesh_obj(name, bm, [body, M_WIN, M_WINLIT])
for k in range(14):                  # distant city blocks with windows
    x = -62 + k * 10 + random.uniform(-2, 2); h_ = random.uniform(28, 64); w_ = random.uniform(4.5, 7.5); d_ = random.uniform(5, 8)
    city_building(f"City{k}", x, 34 + random.uniform(0, 12), w_, d_, h_, (M_CITY, M_CITY2, M_CITY3)[k % 3])
for k in range(6):                   # nearer, lower blocks fill the gaps between towers and the crane site
    x = -52 + k * 22 + random.uniform(-3, 3)
    city_building(f"CityNear{k}", x, 20 + random.uniform(0, 4), random.uniform(5, 8), random.uniform(5, 7), random.uniform(14, 26), (M_CITY2, M_CITY3, M_CITY)[k % 3])
random.seed(8)

def floor_prefab():
    bm = bmesh.new(); add_box(bm, BX0, BX1, BY0, BY1, 0.0, 0.35, 0)
    for cx in (BX0 + 0.5, BX1 - 0.5):
        for cy in (BY0 + 0.5, BY1 - 0.5): add_box(bm, cx - 0.22, cx + 0.22, cy - 0.22, cy + 0.22, 0.35, FLOOR, 1)
    return mesh_obj("FloorMesh", bm, [M_SLAB, M_COL], link=False).data
FLOOR_ME = floor_prefab()
FLOOR_T = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: C["rams2"] + 1.2, 5: C["repeats"] + 0.9, 6: C["climbs"] + 0.4, 7: C["machine"] + 0.6}
FLOOR_BUILD = {0: C["grows"] - 0.5, 1: C["grows"] - 0.2, 2: C["grows"] + 0.1, 3: C["grows"] + 0.4}      # rebuilt during the time-lapse
FLOORS = {}
for k in range(8):
    o = bpy.data.objects.new(f"Floor{k}", FLOOR_ME); CL.objects.link(o); o.location = (0, 0, FLOOR * k + 0.0)
    FLOORS[k] = o
    on = FLOOR_BUILD.get(k, FLOOR_T[k])
    wins = [(on, DUR)] if k > 3 else [(0, T_HIDE - 0.05), (on, DUR)]
    windows(o, wins)
    if k <= 3: bake_fn(o, "scale", 2, lambda t, on=on: 1.0 if t < T_HIDE else max(0.02, ease((t - on) / 0.35)))
    else: bake_fn(o, "scale", 2, lambda t, on=on: max(0.02, ease((t - on) / 0.45)))

# ---------- mast sections ----------
def mast_mesh():
    bm = bmesh.new(); hw = W / 2
    for sx in (-1, 1):
        for sy in (-1, 1): add_bar(bm, (sx * hw, sy * hw, 0), (sx * hw, sy * hw, H), 0.14)
    for z in (0.04, H - 0.04):
        for s in (-1, 1):
            add_bar(bm, (-hw, s * hw, z), (hw, s * hw, z), 0.08); add_bar(bm, (s * hw, -hw, z), (s * hw, hw, z), 0.08)
    n = 2
    for k in range(n):                # X-bracing as zig-zag diagonals on each face
        z0, z1 = H * k / n, H * (k + 1) / n; a, b = (-hw, hw) if k % 2 == 0 else (hw, -hw)
        for s in (-1, 1):
            add_bar(bm, (a, s * hw, z0), (b, s * hw, z1), 0.07); add_bar(bm, (s * hw, a, z0), (s * hw, b, z1), 0.07)
    return mesh_obj("MastMesh", bm, M_MAST, link=False).data
MAST_ME = mast_mesh()
MAST = []
MAST_ON = {0: C["stands"] - 0.1, 1: C["mast"] - 0.15, 2: C["mast"] + 0.35, 3: C["grows"] + 0.1, 4: C["grows"] + 0.7, 5: C["grows"] + 1.3,
           7: C["repeats"] + 0.25, 8: C["climbs"] + 0.1, 9: C["machine"] + 1.1}
for i in range(10):
    o = bpy.data.objects.new(f"Mast{i}", MAST_ME); CL.objects.link(o); o.location = (0, 0, H * i); MAST.append(o)
    if i == 6: continue                                 # the carried section is its own object
    if i < 6: windows(o, [(0, T_HIDE - 0.05), (MAST_ON[i], DUR)])
    else: windows(o, [(MAST_ON[i], DUR)])
    if i in (0, 1, 2): bake_fn(o, "location", 2, lambda t, i=i: H * i + (0 if t < T_HIDE else drop(t, MAST_ON[i] + 0.05)))
SEC = bpy.data.objects.new("NewSection", MAST_ME); CL.objects.link(SEC)
windows(SEC, [(C["then"] - 0.3, DUR)])
bake_fn(SEC, "location", 0, lambda t: sec_pos(t)[0]); bake_fn(SEC, "location", 2, lambda t: sec_pos(t)[1])
bake_fn(SEC, "scale", 2, lambda t: max(0.02, ease((t - (C["then"] - 0.3)) / 0.4)))
glow(B_NEW, [(0, 0), (T_LAND - 0.1, 0), (T_LAND + 0.3, 2.5), (C["lift"] - 0.2, 2.5), (C["lift"] + 0.3, 0), (C["opens"] - 0.4, 0), (C["opens"], 2.5), (C["in"] + 0.4, 2.5), (C["locks"] + 0.4, 0)])
SEC.data = MAST_ME.copy(); SEC.data.materials.clear(); SEC.data.materials.append(M_NEW)

# ---------- top assembly (slewing unit, cab, jib, counter-jib, climbing frame, rams) ----------
def jib_mesh(L, h=1.4, wy=0.7):
    bm = bmesh.new(); n = int(L / 1.4); p = L / n
    for y in (-wy / 2, wy / 2):
        add_bar(bm, (0, y, 0), (L, y, 0), 0.10); add_bar(bm, (0, y, h), (L * 0.97, y, h * 0.5), 0.09)
        for k in range(n + 1):
            x = p * k; hh = h - (h * 0.5) * (x / (L * 0.97)) if x < L * 0.97 else h * 0.5
            add_bar(bm, (x, y, 0), (x, y, hh), 0.05)
            if k < n:
                x2 = p * (k + 1); hh2 = h - (h * 0.5) * (x2 / (L * 0.97)) if x2 < L * 0.97 else h * 0.5
                add_bar(bm, (x, y, 0 if k % 2 == 0 else hh), (x2, y, hh2 if k % 2 == 0 else 0), 0.045)
    for k in range(0, n + 1, 2): add_bar(bm, (p * k, -wy / 2, 0), (p * k, wy / 2, 0), 0.05)
    return mesh_obj("JibMesh", bm, M_JIB, link=False).data
def frame_mesh():
    bm = bmesh.new(); hw = W / 2 + 0.28; zb, zt = -H - 0.3, 0.0
    for sx in (-1, 1):
        for sy in (-1, 1): add_bar(bm, (sx * hw, sy * hw, zb), (sx * hw, sy * hw, zt), 0.12)
    for z in (zb, zb + (zt - zb) / 2, zt):
        for s in (-1, 1): add_bar(bm, (-hw, s * hw, z), (hw, s * hw, z), 0.09); add_bar(bm, (s * hw, -hw, z), (s * hw, hw, z), 0.09)
    for s in (-1, 1):
        add_bar(bm, (-hw, s * hw, zb), (hw, s * hw, zt), 0.06); add_bar(bm, (s * hw, -hw, zb), (s * hw, hw, zt), 0.06)
    add_box(bm, hw, hw + 2.9, -1.2, 1.2, zb - 0.05, zb + 0.12)                       # platform for the new section
    for y in (-1.2, 1.2): add_bar(bm, (hw, y, zb + 0.12), (hw + 2.9, y, zb + 0.12 + 0.5), 0.05)
    return mesh_obj("FrameMesh", bm, M_FRAME, link=False).data
JIB_ME, CJIB_ME, FRAME_ME = jib_mesh(JIB_L), jib_mesh(CJIB_L, 1.1), frame_mesh()

def make_top(ox, tag, with_hook=True, jib_len=JIB_L):
    """Builds the top assembly at x offset ox. Returns dict of parts (all parented to TOP unless noted)."""
    P = {}
    P["TOP"] = TOP = empty(f"Top{tag}", (ox, 0, 0))
    P["SLEW"] = SL = empty(f"SlewUnit{tag}", (0, 0, 0), TOP)
    bm = bmesh.new(); add_cyl(bm, 1.25, 0.35, "Z", (0, 0, 0.18), 32)
    add_box(bm, -1.0, 1.0, -0.8, 0.8, 0.35, 0.75)
    for sx in (-0.6, 0.6): add_bar(bm, (sx, 0, 0.75), (0.2, 0, 7.4), 0.14)                       # A-frame legs
    mesh_obj(f"Turntable{tag}", bm, [M_SLEW], SL)
    bm = bmesh.new(); add_box(bm, -0.6, 0.6, -0.65, 0.65, 0.0, 1.3, 0); mesh_obj(f"CabShell{tag}", bm, [M_CAB], SL).location = (0.3, -2.0, 0.4)
    bm = bmesh.new(); add_box(bm, -0.5, 0.5, -0.67, -0.65, 0.3, 1.1, 0); mesh_obj(f"CabGlass{tag}", bm, [M_GLASS], SL).location = (0.3, -2.0, 0.4)
    P["JIB"] = JB = empty(f"Jib{tag}", (0.9, 0, 0.75), TOP)
    o = bpy.data.objects.new(f"JibTruss{tag}", JIB_ME if jib_len == JIB_L else jib_mesh(jib_len)); CL.objects.link(o); o.parent = JB
    P["CJIB"] = CJB = empty(f"CounterJib{tag}", (-0.9, 0, 0.75), TOP)
    o = bpy.data.objects.new(f"CJibTruss{tag}", CJIB_ME); CL.objects.link(o); o.parent = CJB; o.rotation_euler = (0, 0, math.pi)
    for k, (cx, cz) in enumerate(((-1.8, 0.3), (-3.1, 0.3), (-4.4, 0.3))):
        bm = bmesh.new(); add_box(bm, -0.6, 0.6, -0.55, 0.55, 0, 1.2, 0); b_ = mesh_obj(f"CWBlock{tag}{k}", bm, [M_CWB], CJB); b_.location = (cx, 0, cz)
    for nm, (x, z) in (("PendantJib", (jib_len * 0.62 + 0.9, 0.75 + 1.0)), ("PendantCJib", (-CJIB_L * 0.75 - 0.9, 0.75 + 0.9))):
        bm = bmesh.new(); add_bar(bm, (0.2, 0, 7.4), (x, 0, z), 0.06); mesh_obj(f"{nm}{tag}", bm, [M_ROPE], SL)
    if with_hook:
        P["TROLLEY"] = TR = empty(f"Trolley{tag}", (JIB_L * 0.6, 0, 0.0), JB)
        bm = bmesh.new(); add_box(bm, -0.5, 0.5, -0.45, 0.45, -0.25, 0.12); mesh_obj(f"TrolleyBox{tag}", bm, [M_TROLLEY], TR)
        P["CABLE"] = CBL = unit_rope(f"HookCable{tag}", 0.04, M_ROPE, TR); CBL.location = (0, 0, -0.25)
        bm = bmesh.new(); add_box(bm, -0.3, 0.3, -0.25, 0.25, -0.35, 0.0); add_cyl(bm, 0.18, 0.2, "Y", (0, 0, -0.55), 16)
        P["HOOK"] = HK = mesh_obj(f"HookBlock{tag}", bm, [M_HOOK], TR)
    P["FRAME"] = FR = bpy.data.objects.new(f"ClimbFrame{tag}", FRAME_ME); CL.objects.link(FR); FR.parent = TOP
    for s_, y_ in (("L", -(W / 2 + 0.28) - 0.02), ("R", (W / 2 + 0.28) + 0.02)):
        pass
    return P

TA_ = make_top(0.0, "A")
for nm in ("TOP",): pass
TOP_A = TA_["TOP"]
bake_fn(TOP_A, "location", 2, TOPZ)
# assembly drops (slew, jib, counter-jib) after the mobile crane lifts them in; they exist from the start (mature crane)
def piece_on(P_, t_on, windows_full=True):
    for part in (P_,):
        windows(part, [(0, T_HIDE - 0.05), (t_on, DUR)])
        bake_fn(part, "location", 2, lambda t, base=part.location.z: base + (0 if t < T_HIDE else drop(t, t_on)))
piece_on(TA_["SLEW"], C["cab"] - 0.1)
piece_on(TA_["JIB"], C["jib"] - 0.1)
piece_on(TA_["CJIB"], C["counterweights"] - 0.1)
TA_["JIB"].parent = TOP_A                                     # keep parent after the windows keyed children
# climbing frame + rams (only after "climbing frame", plus at the very start)
FR_A = TA_["FRAME"]; FR_A.location = (0, 0, 0)
windows(FR_A, [(0, T_HIDE - 0.05), (C["climbing"] - 0.2, DUR)])
bake_fn(FR_A, "scale", 2, lambda t: 1.0 if (t < T_HIDE or t > C["climbing"] + 0.3) else max(0.02, ease((t - (C["climbing"] - 0.2)) / 0.5)))
def rams(prefix, topz_fn, collar_fn, ox, wins, ys=(-1.28, 1.28)):
    out = []
    for k, (xr, yr) in enumerate(((-0.45, ys[0]), (0.45, ys[0]))):
        body = cyl(f"{prefix}RamBody{k}", 0.14, 2.4, "Z", (0, 0, 1.2), M_RAMB, seg=16); body.location = (ox + xr, yr, 15.0)
        rod = unit_post(f"{prefix}RamRod{k}", 0.075, M_ROD); rod.location = (ox + xr, yr, 17.4)
        clr = box(f"{prefix}Collar{k}", -0.5, 0.5, -0.12, 0.12, 0.0, 0.35, M_COLLAR); clr.location = (ox + xr, yr, 15.0)
        windows(body, wins); windows(rod, wins); windows(clr, wins)
        bake_fn(body, "location", 2, collar_fn)
        bake_fn(clr, "location", 2, lambda t: collar_fn(t) - 0.0)
        bake_fn(rod, "location", 2, lambda t: collar_fn(t) + 2.4)
        bake_fn(rod, "scale", 2, lambda t: max(0.05, topz_fn(t) - 0.25 - (collar_fn(t) + 2.4)))
        out += [body, rod, clr]
    return out
RAMS_A = rams("A", TOPZ, COLLAR, 0.0, [(0, T_HIDE - 0.05), (C["hydraulic"] - 0.4, DUR)])
# trolley, hook, hook cable (set A)
bake_fn(TA_["TROLLEY"], "location", 0, lambda t: TROLLEY_X(t))
bake_fn(TA_["CABLE"], "scale", 2, lambda t: max(0.1, (TOPZ(t) + 0.5) - hook_z(t)))
bake_fn(TA_["HOOK"], "location", 2, lambda t: hook_z(t) - (TOPZ(t) + 0.75))
# the gap glow (a translucent cyan frame outlining the empty section slot while it is open)
bm = bmesh.new(); hw_ = W / 2 + 0.12
for sx in (-1, 1):
    for sy in (-1, 1): add_bar(bm, (sx * hw_, sy * hw_, 0), (sx * hw_, sy * hw_, H), 0.07)
for z_ in (0, H):
    for s_ in (-1, 1): add_bar(bm, (-hw_, s_ * hw_, z_), (hw_, s_ * hw_, z_), 0.07); add_bar(bm, (s_ * hw_, -hw_, z_), (s_ * hw_, hw_, z_), 0.07)
GAP = mesh_obj("GapSlot", bm, [M_LINE]); GAP.location = (0, 0, 18.0)
windows(GAP, [(C["opens"] - 0.6, C["in"] + 0.1)])
# a thin cyan band at the old crane height, shown on "taller"
bm = bmesh.new()
for s_ in (-1, 1): add_bar(bm, (-4, s_ * 4, 0), (4, s_ * 4, 0), 0.08); add_bar(bm, (s_ * 4, -4, 0), (s_ * 4, 4, 0), 0.08)
OLD = mesh_obj("OldTopBand", bm, [M_LINE])
OLD.location = (0, 0, 21.0); windows(OLD, [(C["longer"] + 0.2, C["repeats"] + 0.15)])

# mobile crane that erects the first pieces
MOB = empty("MobileCrane")
bm = bmesh.new(); add_box(bm, -11.5, -4.5, -4.2, -1.8, 0.7, 1.8, 0); add_box(bm, -5.6, -4.3, -4.0, -2.0, 1.8, 3.1, 0)
mesh_obj("TruckBody", bm, [M_TRUCK], MOB)
for wx in (-10.4, -9.0, -6.6, -5.4):
    for wy in (-4.25, -1.75): cyl(f"Tire{wx}{wy}", 0.7, 0.45, "Y", (wx, wy, 0.7), M_TIRE, MOB)
bm = bmesh.new(); add_bar(bm, (-7.6, -3.0, 2.2), (0.0, -0.2, 22.0), 0.55); add_cyl(bm, 0.25, 0.8, "Y", (0.0, -0.2, 22.1), 16)
mesh_obj("Boom", bm, [M_BOOM], MOB)
MCABLE = unit_rope("MobileCable", 0.05, M_ROPE); MCABLE.location = (0, -0.2, 22.0)
windows(MOB, [(T_MOBILE0, T_MOBILE1)]); windows(MCABLE, [(T_MOBILE0, T_MOBILE1)])
def mob_cable_len(t):
    # follows the piece being craned in
    for t0, zt in ((C["stands"], H * 1), (C["mast"] - 0.15, H * 2), (C["mast"] + 0.35, H * 3), (C["cab"] - 0.1, 9.0 + 8.0), (C["jib"] - 0.1, 9.0 + 3.0), (C["counterweights"] - 0.1, 9.0 + 3.0)):
        if t0 - 0.35 <= t < t0 + 0.8: return 22.0 - (zt + drop(t, t0 + 0.05))
    return 22.0 - (H * 3 + 2.0)
bake_fn(MCABLE, "scale", 2, mob_cable_len)

# ---------- ties, wind ----------
TIES = []
for n_, (zt, t_on) in enumerate(((6.0, C["ties"] - 0.1), (12.0, C["ties"] + 0.35), (18.0, C["ties"] + 0.8))):
    for y_ in (-0.5, 0.5):
        bm = bmesh.new(); add_bar(bm, (0.8, y_, zt + 0.35), (BX0 + 0.3, y_ * 3.0, zt + 0.35), 0.30); add_box(bm, BX0 - 0.1, BX0 + 0.3, y_ * 3.0 - 0.5, y_ * 3.0 + 0.5, zt - 0.2, zt + 0.9)
        o = mesh_obj(f"Tie{n_}{y_}", bm, [M_TIE]); windows(o, [(t_on, DUR)]); TIES.append(o)
glow(B_TIE, [(0, 0), (C["ties"] - 0.1, 0), (C["ties"] + 0.4, 5.0), (C["tip"] + 0.5, 5.0), (C["tip"] + 1.0, 1.0)])
WINDS = []
for n_, (zw, dt) in enumerate(((26.5, 0.0), (28.5, 0.12), (24.5, 0.25))):
    bm = bmesh.new(); add_cyl(bm, 0.2, 2.4, "X", (0, 0, 0), 12); add_cyl(bm, 0.5, 0.9, "X", (1.6, 0, 0), 12, r2=0.0)
    o = mesh_obj(f"Wind{n_}", bm, [M_WIND]); windows(o, [(C["wind"] - 0.1 + dt, C["tip"] + 0.7)])
    bake_fn(o, "location", 0, lambda t, dt=dt: -14.0 + 7.0 * lin((t - (C["wind"] + dt)) / 0.55) if t < C["tip"] + dt - 0.1 else -7.5 - 4.0 * ease((t - (C["tip"] + dt - 0.1)) / 0.35))
    o.location = (-14, 0, zw); bake_fn(o, "location", 2, lambda t, zw=zw: zw + 0 * t); WINDS.append(o)
# slew wobble on the "can't swing" rule (the whole top turns, the mast gets a red warning glow)
SLEW_RZ = PW([(0, 0.0), (C["swing"] - 0.1, 0.0), (C["swing"] + 0.6, 0.30), (C["twisting"] - 0.2, 0.30), (C["twisting"] + 0.5, 0.0)])
bake_fn(TOP_A, "rotation_euler", 2, SLEW_RZ)
glow(B_MAST, [(0, 0), (C["itself"] - 0.1, 0), (C["itself"] + 0.15, 3.0), (C["itself"] + 1.2, 0)])
B_MAST.inputs["Emission Color"].default_value = (*GOLD, 1)
glow(B_JIB, [(0, 0), (C["balanced"] - 0.7, 0), (C["balanced"] - 0.2, 1.8), (C["then"] - 0.2, 1.8), (C["then"] + 0.3, 0), (C["itself"] - 0.1, 0), (C["itself"] + 0.15, 3.0), (C["itself"] + 1.2, 0)])
glow(B_FRAME, [(0, 0), (C["climbing"] - 0.1, 0), (C["climbing"] + 0.25, 3.5), (C["wraps"] + 0.4, 3.5), (C["wraps"] + 0.9, 0)])
glow(B_RAMB, [(0, 0), (C["rams"] - 0.1, 0), (C["rams"] + 0.2, 3.0), (C["lift"] + 3.5, 3.0), (C["let"] - 0.2, 3.0), (C["let"] + 0.4, 0)])
glow(B_ROD, [(0, 0), (C["push"] - 0.1, 0), (C["push"] + 0.2, 3.0), (C["entire"] + 4.0, 3.0), (C["let"], 0)])
glow(B_COLLAR, [(0, 0), (C["rams"] + 0.1, 0), (C["rams"] + 0.5, 4.0), (C["let"] - 0.2, 4.0), (C["let"] + 0.3, 0)])
glow(B_CWB, [(0, 0), (C["balanced"] - 0.7, 0), (C["balanced"] - 0.2, 2.0), (C["then"] - 0.2, 2.0), (C["then"] + 0.3, 0)])

# ---------- Set B: crane climbing inside a building core ----------
TB = make_top(OX, "B", with_hook=False)
TOPB = PW([(0, 15.0), (C["inside"] - 0.1, 15.0), (C["inside"] + 0.7, 18.0), (C["shaft"] - 0.8, 18.0), (C["shaft"] + 0.3, 21.0)])
COLLB = PW([(0, 12.0), (C["inside"] + 0.8, 12.0), (C["inside"] + 1.3, 15.0), (C["shaft"] - 0.8, 15.0), (C["shaft"] + 0.3, 15.0), (C["shaft"] + 0.7, 18.0)])
bake_fn(TB["TOP"], "location", 2, TOPB)
WINB = [(C["some"] - 0.25, C["so"] - 0.25)]
box("GroundB", OX - 40, OX + 40, -40, 40, -30, -0.001, M_GROUND)
box("FoundB", OX - 3.5, OX + 3.5, -3.5, 3.5, -2.0, 0.0, M_FOUND)
CORE = empty("CoreB", (OX, 0, 0))
for nm, (x0, x1, y0, y1) in (("Back", (-2.4, 2.4, 1.7, 2.4)), ("Left", (-2.4, -1.7, -1.7, 1.7)), ("Right", (1.7, 2.4, -1.7, 1.7))):
    box(f"Core{nm}", x0, x1, y0, y1, 0.0, 14.6, M_CONC, CORE)
for k in range(1, 6):
    bm = bmesh.new()
    add_box(bm, -6.0, -1.8, -5.0, 5.0, 0.0, 0.35, 0); add_box(bm, 1.8, 6.0, -5.0, 5.0, 0.0, 0.35, 0)
    add_box(bm, -1.8, 1.8, -5.0, -1.8, 0.0, 0.35, 0); add_box(bm, -1.8, 1.8, 1.8, 5.0, 0.0, 0.35, 0)
    s_ = mesh_obj(f"SlabB{k}", bm, [M_SLAB]); s_.location = (OX, 0, FLOOR * k - 0.35); windows(s_, WINB if k < 5 else [(C["inside"] + 1.0, WINB[0][1])])
MAST_B = []
for i in range(7):
    o = bpy.data.objects.new(f"MastB{i}", MAST_ME); CL.objects.link(o); o.location = (OX, 0, H * i); MAST_B.append(o)
    on = [(0, DUR), (0, DUR), (0, DUR), (0, DUR), (0, DUR), (C["inside"] + 0.5, DUR), (C["shaft"] - 0.3, DUR)][i][0]
    windows(o, [(max(on, C["some"] - 0.25), C["so"] - 0.25)])
for z_, nm in ((6.0, "0"), (9.0, "1")):
    for sy in (-1, 1):
        bm = bmesh.new(); add_box(bm, -1.3, 1.3, -0.12, 0.12, 0.0, 0.5, 0); c_ = mesh_obj(f"CollarB{nm}{sy}", bm, [M_COLLAR]); c_.location = (OX, sy * 1.1, z_ - 0.2)
        windows(c_, WINB)
RAMS_B = rams("B", TOPB, COLLB, OX, WINB, ys=(-1.28, 1.28))
windows(TB["TOP"], WINB); windows(TB["FRAME"], WINB)
glow(B_COLLAR, [(0, 0), (C["inside"] - 0.1, 0), (C["inside"] + 0.4, 3.0), (C["shaft"] + 1.0, 3.0), (C["so"] - 0.5, 0)])

# ---------- camera ----------
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36.0
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 16; cam_d.dof.focus_object = TGT
cam_d.clip_start = 0.1; cam_d.clip_end = 600
TZ = lambda k=0.0: (lambda t: TOPZ(t) + k)
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (-6.0, -34.0, 14.0), (3.5, 0.0, 14.5), 24),
    (C["cut"] - 0.2, (-3.0, -26.0, 13.0), (3.0, 0.0, 14.0), 26),
    (T_HIDE, (-9.0, -20.0, 5.0), (-2.0, 0.0, 4.5), 26, "cut"),
    (C["mobile"] + 0.5, (-12.0, -20.0, 9.0), (-1.0, 0.0, 9.0), 26),
    (C["cab"] - 0.1, (-10.0, -19.0, 12.0), (3.0, 0.0, 12.0), 24),
    (C["after"] + 0.2, (-14.0, -32.0, 11.0), (4.0, 0.0, 12.5), 24, "cut"),
    (C["heres"], (-4.0, -17.0, TZ(-1.5)), (1.0, 0.0, TZ(-1.8)), 28, "cut"),
    (C["operator"] - 0.2, (-12.0, -30.0, TZ(1.0)), (5.0, 0.0, TZ(0.5)), 26, "cut"),
    (C["then"] - 0.2, (-3.0, -19.0, 9.0), (2.6, 0.0, 9.0), 24, "cut"),
    (C["now"] - 0.1, (-7.0, -14.0, TZ(-2.0)), (1.0, 0.0, TZ(-2.4)), 30, "cut"),
    (C["entire"] - 0.2, (-12.0, -28.0, lambda t: TZ(0.0)(t) + 0.5), (3.0, 0.0, lambda t: TZ(0.0)(t)), 26),
    (C["that"], (-5.0, -12.5, lambda t: TZ(-3.0)(t)), (0.8, 0.0, lambda t: TZ(-3.4)(t)), 30, "cut"),
    (C["crane2"] + 0.1, (-6.0, -13.0, lambda t: TZ(-2.5)(t)), (1.4, 0.0, lambda t: TZ(-3.2)(t)), 28),
    (C["then2"] - 0.1, (-3.0, -13.0, lambda t: TZ(-6.0)(t)), (0.5, 0.0, lambda t: TZ(-4.6)(t)), 28, "cut"),
    (C["taller2"] - 0.2, (-16.0, -34.0, lambda t: TZ(-4.0)(t)), (2.5, 0.0, lambda t: TZ(-4.0)(t)), 24),
    (C["repeats"] - 0.1, (-18.0, -38.0, lambda t: TZ(-6.0)(t)), (3.0, 0.0, lambda t: TZ(-6.0)(t)), 24, "cut"),
    (C["one"] - 0.2, (-9.0, -22.0, lambda t: TZ(1.0)(t)), (3.0, 0.0, lambda t: TZ(-0.5)(t)), 28, "cut"),
    (C["as"] - 0.1, (-18.0, -38.0, 14.0), (5.0, 0.0, 13.5), 24, "cut"),
    (C["steel"] + 0.2, (-6.0, -22.0, 12.0), (4.0, 0.0, 12.0), 28),
    (C["some"] - 0.25, (OX - 8.0, -26.0, 12.0), (OX, 0.0, 10.5), 26, "cut"),
    (C["so"] - 0.25, (-20.0, -42.0, 16.0), (5.0, 0.0, 15.5), 24, "cut"),
    (C["would"] - 0.1, (-7.0, -17.0, lambda t: TZ(2.5)(t)), (1.5, 0.0, lambda t: TZ(2.3)(t)), 32, "cut"),
    (C["end"], (-10.0, -28.0, lambda t: TZ(5.0)(t)), (3.0, 0.0, lambda t: TZ(1.5)(t)), 28),
]
def ev(p, t): return Vector([c(t) if callable(c) else c for c in p])
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = ev(SHOTS[k][1], t), ev(SHOTS[k][2], t), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t1 = SHOTS[k + 1][0]; tr = 0.7 if (t1 - SHOTS[k][0]) > 1.4 else (t1 - SHOTS[k][0]) * 0.5
        if t > t1 - tr:
            u = ease((t - (t1 - tr)) / tr)
            l0, g0, n0 = l0.lerp(ev(SHOTS[k + 1][1], t), u), g0.lerp(ev(SHOTS[k + 1][2], t), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.05 * math.sin(t * 0.7), 0.0, 0.03 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
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
gr = wn.new("ShaderNodeValToRGB"); e = gr.color_ramp.elements; e[0].color = (0.006, 0.010, 0.018, 1); e[1].color = (0.05, 0.075, 0.11, 1)
wl.new(grad.outputs["Fac"], gr.inputs[0])
bg_dark = wn.new("ShaderNodeBackground"); wl.new(gr.outputs[0], bg_dark.inputs["Color"])
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.15
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_ref.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
def area(name, loc, size, power, rgb=(1, 1, 1), target=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
def target(name, loc):
    o = bpy.data.objects.new(name, None); scene.collection.objects.link(o); o.location = loc; return o
sun = bpy.data.lights.new("Key", "SUN"); sun.energy = 3.2; sun.color = (1.0, 0.93, 0.82); sun.angle = math.radians(5)
so = bpy.data.objects.new("Key", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(58), math.radians(8), math.radians(-34))
sun2 = bpy.data.lights.new("Fill", "SUN"); sun2.energy = 0.9; sun2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("Fill", sun2); scene.collection.objects.link(so2); so2.rotation_euler = (math.radians(75), math.radians(-10), math.radians(150))
LT_T = target("LT_Top", (0, 0, 24))
area("RimTop", (6.0, 14.0, 40.0), 8.0, 5000, (0.75, 0.85, 1.0), LT_T)
LT_C = target("LT_Cab", (0.3, -1.6, 28))
area("KeyCab", (-8.0, -14.0, 36.0), 6.0, 6000, (1.0, 0.92, 0.80), LT_C)
LT_BB = target("LT_B", (OX, 0, 12))
area("KeyB", (OX - 9.0, -16.0, 22.0), 9.0, 7000, (1.0, 0.92, 0.80), LT_BB)
area("FillB", (OX + 9.0, -12.0, 8.0), 7.0, 2500, (0.78, 0.86, 1.0), LT_BB)
area("RimB", (OX + 2.0, 10.0, 24.0), 6.0, 4000, (0.8, 0.88, 1.0), LT_BB)
area("CamFill", (0, 0, 0), 3.5, 90, (1.0, 0.96, 0.9), TGT).parent = cam

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
scene.cycles.max_bounces = 6; scene.cycles.transmission_bounces = 4
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
def Z(fn): return fn
ANCH = {
    "mast": lambda t: Vector((0.8, 0.0, 6.0)),
    "frame": lambda t: Vector((0.9, -1.0, TOPZ(t) - 1.5)),
    "ram": lambda t: Vector((0.45, -1.28, (COLLAR(t) + TOPZ(t)) / 2)),
    "trolley": lambda t: Vector((TROLLEY_X(t) + 0.9, 0.0, TOPZ(t) + 1.5)),
    "hook": lambda t: Vector((TROLLEY_X(t) + 0.9, 0.0, hook_z(t) - 0.5)),
    "section": lambda t: Vector((sec_pos(t)[0] + 0.6, -0.6, sec_pos(t)[1] + 1.5)),
    "platform": lambda t: Vector((2.5, -1.2, plat_z(t) + 0.1)),
    "gap": lambda t: Vector((0.7, -0.8, 18.0 + 1.6)),
    "cab": lambda t: Vector((0.3, -2.9, TOPZ(t) + 1.4)),
    "cweights": lambda t: Vector((-3.5, 0.0, TOPZ(t) + 2.0)),
    "jib": lambda t: Vector((12.0, 0.0, TOPZ(t) + 2.3)),
    "top": lambda t: Vector((0.3, 0.0, TOPZ(t) + 7.4)),
    "tie": lambda t: Vector((3.4, -1.0, 18.35)),
    "tie_lo": lambda t: Vector((3.4, -1.0, 12.35)),
    "wind": lambda t: Vector((-6.0, 0.0, 26.5)),
    "mobile": lambda t: Vector((-5.0, -3.0, 3.2)),
    "building": lambda t: Vector((BX1 - 0.6, BY0 + 0.5, 3.0)),
    "b_collar": lambda t: Vector((OX + 1.2, -1.2, 6.4)),
    "b_core": lambda t: Vector((OX - 2.0, -1.7, 9.0)),
    "b_frame": lambda t: Vector((OX + 0.9, -1.0, TOPB(t) - 1.5)),
    "end_top": lambda t: Vector((0.3, -1.8, TOPZ(t) + 2.4)),
}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        w = a(tt)
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"hide": round(T_HIDE, 3), "mobile": [round(T_MOBILE0, 3), round(T_MOBILE1, 3)],
          "drop_base": round(C["stands"] - 0.05, 3), "drop_m1": round(C["mast"] - 0.1, 3), "drop_m2": round(C["mast"] + 0.4, 3),
          "drop_slew": round(C["cab"] - 0.05, 3), "drop_jib": round(C["jib"] - 0.05, 3), "drop_cw": round(C["counterweights"] - 0.05, 3),
          "timelapse": [round(C["grows"] - 0.4, 3), round(C["building"] + 0.5, 3)],
          "frame_in": round(C["climbing"] - 0.2, 3), "trolley": [round(C["operator"] + 0.3, 3), round(C["balanced"] + 0.2, 3)],
          "pick": [round(T_PICK0 - 0.9, 3), round(T_LAND, 3)], "lift": [round(C["lift"] - 0.1, 3), round(C["opens"] - 0.6, 3)],
          "gap": round(C["opens"] - 0.6, 3), "slide": [round(TSLIDE0, 3), round(TSLIDE1, 3)], "lock": round(C["locks"] + 0.1, 3),
          "settle": [round(C["rams2"] - 0.4, 3), round(C["settles"] + 0.2, 3)],
          "repeat1": [round(C["repeats"] - 0.3, 3), round(C["repeats"] + 0.35, 3)], "repeat2": [round(C["repeats"] + 0.55, 3), round(C["climbs"] + 0.2, 3)],
          "swing": [round(C["swing"] - 0.1, 3), round(C["swing"] + 0.6, 3)], "ties": [round(C["ties"] - 0.1, 3), round(C["ties"] + 0.8, 3)],
          "wind": round(C["wind"], 3), "tip": round(C["tip"], 3), "set_b": [round(C["some"] - 0.25, 3), round(C["so"] - 0.25, 3)],
          "climb_b": [round(C["inside"] - 0.1, 3), round(C["inside"] + 0.7, 3), round(C["shaft"] - 0.8, 3), round(C["shaft"] + 0.3, 3)],
          "final_climb": [round(C["machine"] + 0.4, 3), round(C["machine"] + 1.2, 3)], "cta": round(C["would"] - 0.1, 3),
          "floors": [round(FLOOR_T[k], 3) for k in (4, 5, 6, 7)]}
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
