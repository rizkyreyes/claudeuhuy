# Skyscraper-Foundations-3D: why skyscrapers don't sink. Studio cutaway dioramas in Blender Cycles. Every cue is a word in the VO.
# Set A (origin): a block of ground cut open at y = -6 (topsoil, sand, silt, soft clay, bedrock box below z -26) with a glass tower on a concrete raft.
#   Front row of 7 bored piles on the cut face (x -6..6). The hero pile (x 0) is drilled on screen: auger, slurry, steel cage, tremie pipe, concrete
#   rising and pushing the slurry out into a tank. The other piles appear as a time-lapse, pile heads pop up over the whole footprint (7 x 7 grid).
#   Bedrock drops away for the friction beat, the raft lands, the tower rises, everything settles a little and evenly.
# Set B (x = 2000): a cube of soil grains with water in between, a weight lands and squeezes it.
# Set C (x = 4000): a generic round stone bell tower on a shallow foundation over soft clay; it sinks and leans. Not a model of the real tower, just the idea.
# No people anywhere. Sizes are illustrative; only "about ten feet" and "about twelve feet" are spoken.
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
random.seed(11)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
C = {}
for name, word in [("why", "why"), ("skyscrapers", "skyscrapers"), ("sink", "sink"), ("ground", "ground"), ("lets", "let's"), ("cut", "cut"), ("open", "open"),
                   ("soil", "soil"), ("solid", "solid"), ("grains", "grains"), ("water", "water"), ("under", "under"), ("weight", "weight"),
                   ("squeezes", "squeezes"), ("together", "together"), ("put", "put"), ("heavy", "heavy"), ("tower", "tower"), ("shallow", "shallow"),
                   ("base", "base"), ("gives", "gives"), ("way", "way"), ("thats", "that's"), ("pisa", "pisa"), ("its", "its"), ("foundation", "foundation"),
                   ("ten", "ten"), ("feet", "feet"), ("deep", "deep"), ("soft", "soft"), ("clay", "clay"), ("started", "started"), ("leaning", "leaning"),
                   ("built", "built"), ("so", "so"), ("skyscrapers2", "skyscrapers"), ("reach", "reach"), ("down", "down"), ("first", "first"),
                   ("drill", "drill"), ("bores", "bores"), ("hole", "hole"), ("filled", "filled"), ("slurry", "slurry"), ("pushes", "pushes"),
                   ("walls", "walls"), ("cave", "cave"), ("steel", "steel"), ("cage", "cage"), ("drops", "drops"), ("then", "then"),
                   ("concrete", "concrete"), ("pumped", "pumped"), ("bottom", "bottom"), ("pipe", "pipe"), ("heavy2", "heavy"), ("concrete2", "concrete"),
                   ("rises", "rises"), ("pushes2", "pushes"), ("slurry2", "slurry"), ("up", "up"), ("out", "out"), ("thats2", "that's"), ("one", "one"),
                   ("pile", "pile"), ("tower2", "tower"), ("need", "need"), ("hundreds", "hundreds"), ("some", "some"), ("piles", "piles"),
                   ("stand", "stand"), ("solid2", "solid"), ("bedrock", "bedrock"), ("legs", "legs"), ("table", "table"), ("when", "when"),
                   ("rock", "rock"), ("deep2", "deep"), ("piles2", "piles"), ("hold", "hold"), ("friction", "friction"), ("instead", "instead"),
                   ("soil2", "soil"), ("grips", "grips"), ("length", "length"), ("pile2", "pile"), ("then2", "then"), ("thick", "thick"),
                   ("concrete3", "concrete"), ("raft", "raft"), ("ties", "ties"), ("piles3", "piles"), ("together2", "together"), ("spreads", "spreads"),
                   ("load", "load"), ("under2", "under"), ("burj", "burj"), ("khalifa", "khalifa"), ("raft2", "raft"), ("twelve", "twelve"),
                   ("feet2", "feet"), ("thick2", "thick"), ("heres", "here's"), ("twist", "twist"), ("every", "every"), ("building", "building"),
                   ("sinks", "sinks"), ("little", "little"), ("goal", "goal"), ("sink2", "sink"), ("tiny", "tiny"), ("evenly", "evenly"),
                   ("would", "would"), ("trust", "trust"), ("friction2", "friction"), ("tower3", "tower"), ("tell", "tell"), ("comments", "comments"),
                   ("if", "if"), ("useful", "useful"), ("follow", "follow")]:
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
TS = [(fr - 1) / FPS for fr in range(1, FRAMES + 1)]
def bake_fn(owner, path, index, fn): return bake(owner, path, index, [fn(t) for t in TS])
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("Foundations")

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
def layered(name, stops, zmin=-60.0, grain=1.0, emit_below=None):
    """Soil material coloured by WORLD z, so every piece (block, plugs, notches) lines up. stops = [(z_top_of_layer, rgb), ...] top first."""
    m, nt, b = new_mat(name); N, L = nt.nodes, nt.links
    geo = N.new("ShaderNodeNewGeometry"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(geo.outputs["Position"], sep.inputs[0])
    wob = N.new("ShaderNodeTexNoise"); wob.inputs["Scale"].default_value = 0.08; L.new(geo.outputs["Position"], wob.inputs["Vector"])
    wm = N.new("ShaderNodeMath"); wm.operation = "MULTIPLY_ADD"; L.new(wob.outputs["Fac"], wm.inputs[0]); wm.inputs[1].default_value = 1.2; wm.inputs[2].default_value = -0.6
    zz = N.new("ShaderNodeMath"); zz.operation = "ADD"; L.new(sep.outputs["Z"], zz.inputs[0]); L.new(wm.outputs[0], zz.inputs[1])
    mr = N.new("ShaderNodeMapRange"); mr.inputs[1].default_value = zmin; mr.inputs[2].default_value = 0.0; L.new(zz.outputs[0], mr.inputs[0])
    ramp = N.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"; L.new(mr.outputs[0], ramp.inputs[0])
    el = ramp.color_ramp.elements
    bounds = [(zmin, stops[-1][1])] + [(stops[i + 1][0], stops[i][1]) for i in range(len(stops) - 1)]
    el[0].position = 0.0; el[0].color = (*bounds[0][1], 1)
    el[1].position = (bounds[1][0] - zmin) / -zmin if len(bounds) > 1 else 0.99; el[1].color = (*bounds[1][1], 1)
    for zt, rgb in bounds[2:]:
        e = el.new((zt - zmin) / -zmin); e.color = (*rgb, 1)
    gn = N.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = 3.5 * grain; gn.inputs["Detail"].default_value = 8.0
    L.new(geo.outputs["Position"], gn.inputs["Vector"])
    gm = N.new("ShaderNodeMapRange"); gm.inputs[3].default_value = 0.72; gm.inputs[4].default_value = 1.25; L.new(gn.outputs["Fac"], gm.inputs[0])
    mul = N.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1.0
    L.new(ramp.outputs[0], mul.inputs[6])
    cmb = N.new("ShaderNodeCombineColor"); L.new(gm.outputs[0], cmb.inputs[0]); L.new(gm.outputs[0], cmb.inputs[1]); L.new(gm.outputs[0], cmb.inputs[2])
    L.new(cmb.outputs[0], mul.inputs[7]); L.new(mul.outputs[2], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.35; L.new(gn.outputs["Fac"], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Emission Strength"].default_value = 0.0
    if emit_below is not None:   # emission colour only below a z (e.g. the soft clay), strength keyed with glow()
        lt = N.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; L.new(zz.outputs[0], lt.inputs[0]); lt.inputs[1].default_value = emit_below[0]
        em = N.new("ShaderNodeMix"); em.data_type = "RGBA"; L.new(lt.outputs[0], em.inputs[0])
        em.inputs[6].default_value = (0, 0, 0, 1); em.inputs[7].default_value = (*emit_below[1], 1); L.new(em.outputs[2], b.inputs["Emission Color"])
    return m, b
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
TOPSOIL, SAND, SILT, CLAY = (0.12, 0.075, 0.045), (0.56, 0.42, 0.24), (0.40, 0.33, 0.22), (0.15, 0.17, 0.21)
GRASS = (0.10, 0.15, 0.05)
M_SOIL_A, B_SOIL_A = layered("SoilA", [(0.0, GRASS), (-0.35, TOPSOIL), (-1.6, SAND), (-8.0, SILT), (-15.0, CLAY)])
M_SOIL_C, B_SOIL_C = layered("SoilC", [(0.0, GRASS), (-0.35, TOPSOIL), (-1.2, SILT), (-6.0, CLAY)], emit_below=(-6.0, RED))
M_ROCK, B_ROCK = mat("Bedrock", (0.30, 0.29, 0.30), 0.8, 0.0, GOLD, 6)
M_CONC, B_CONC = mat("PileConcrete", (0.72, 0.71, 0.67), 0.85, 0.0, GOLD, 22)
M_RAFT, B_RAFT = mat("RaftConcrete", (0.50, 0.49, 0.47), 0.85, 0.0, GOLD, 18)
M_SLURRY, B_SLURRY = mat("Slurry", (0.30, 0.19, 0.09), 0.12, 0.0, (0.9, 0.7, 0.4), 0, 0.82)
M_STEEL, B_STEEL = mat("Rebar", (0.55, 0.30, 0.18), 0.5, 0.8, GOLD)
M_PIPE, _ = mat("Tremie", (0.75, 0.77, 0.80), 0.3, 1.0)
M_RIG, _ = mat("RigYellow", (0.85, 0.55, 0.05), 0.45, 0.4)
M_RIGD, _ = mat("RigDark", (0.08, 0.08, 0.09), 0.6, 0.5)
M_AUGER, _ = mat("Auger", (0.45, 0.46, 0.48), 0.3, 1.0)
M_TANK, _ = mat("Tank", (0.15, 0.30, 0.45), 0.5, 0.4)
M_GHOST, B_GHOST = mat("GhostPile", CYAN, 0.5, 0.0, CYAN); B_GHOST.inputs["Emission Strength"].default_value = 3.5
M_ARROW, B_ARROW = mat("ArrowCyan", CYAN, 0.5, 0.0, CYAN); B_ARROW.inputs["Emission Strength"].default_value = 5.0
M_ARROWG, B_ARROWG = mat("ArrowGold", GOLD, 0.5, 0.0, GOLD); B_ARROWG.inputs["Emission Strength"].default_value = 5.0
M_LINE, B_LINE = mat("LevelLine", CYAN, 0.5, 0.0, CYAN); B_LINE.inputs["Emission Strength"].default_value = 6.0
M_HEAD, B_HEAD = mat("PileHead", (0.70, 0.68, 0.62), 0.8, 0.0, GOLD); B_HEAD.inputs["Emission Strength"].default_value = 0.0
M_GRAIN, _ = mat("Grain", (0.62, 0.46, 0.26), 0.7, 0.0, GOLD, 30)
M_WATER, B_WATER = mat("PoreWater", (0.15, 0.45, 0.85), 0.05, 0.0, (0.2, 0.55, 1.0), 0, 0.35); B_WATER.inputs["Emission Strength"].default_value = 0.4
M_DROP, B_DROP = mat("WaterDrop", (0.25, 0.6, 1.0), 0.05, 0.0, (0.25, 0.6, 1.0)); B_DROP.inputs["Emission Strength"].default_value = 1.5
M_WEIGHT, _ = mat("Weight", (0.10, 0.10, 0.11), 0.35, 0.9)
M_PED, _ = mat("Pedestal", (0.05, 0.055, 0.065), 0.6, 0.2)
M_MARBLE, _ = mat("Marble", (0.86, 0.84, 0.78), 0.45, 0.0, GOLD, 9)
M_STONE, _ = mat("FoundationStone", (0.50, 0.47, 0.42), 0.85, 0.0, GOLD, 14)
M_ROOF, _ = mat("Roof", (0.30, 0.25, 0.22), 0.6)
def glass_mat():
    m, nt, b = new_mat("Curtainwall"); N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    ad = N.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(sep.outputs["X"], ad.inputs[0]); L.new(sep.outputs["Y"], ad.inputs[1])
    cmb = N.new("ShaderNodeCombineXYZ"); L.new(ad.outputs[0], cmb.inputs[0]); L.new(sep.outputs["Z"], cmb.inputs[1])
    br = N.new("ShaderNodeTexBrick"); L.new(cmb.outputs[0], br.inputs["Vector"])
    br.inputs["Scale"].default_value = 0.33; br.inputs["Mortar Size"].default_value = 0.035; br.inputs["Brick Width"].default_value = 1.0
    br.inputs["Row Height"].default_value = 0.5; br.offset = 0.0; br.squash = 1.0
    br.inputs["Color1"].default_value = (0.035, 0.06, 0.10, 1); br.inputs["Color2"].default_value = (0.75, 0.55, 0.30, 1)
    br.inputs["Mortar"].default_value = (0.55, 0.58, 0.62, 1); br.inputs["Bias"].default_value = -0.75
    L.new(br.outputs["Color"], b.inputs["Base Color"])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(br.outputs["Fac"], inv.inputs[1])
    rr = N.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.08; rr.inputs[4].default_value = 0.5; L.new(br.outputs["Fac"], rr.inputs[0])
    L.new(rr.outputs[0], b.inputs["Roughness"]); b.inputs["Metallic"].default_value = 0.5
    L.new(br.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.35
    return m, b
M_GLASS, B_GLASS = glass_mat()

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

# ================= SET A: the skyscraper ground block =================
YF = -6.0                                    # the cutaway face
PX = [-6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0]  # front-row pile x
PR = 0.62                                    # pile / hole radius
ZB = -26.0                                   # bedrock top (pile tips)
RAFT_T = 3.7                                 # raft thickness (about twelve feet)
HERO = 3                                     # PX index of the drilled pile
T_FIRST = C["first"] - 0.1

# timing for the hero pile
T_D0, T_D1 = C["drill"] - 0.1, C["hole"] + 0.35            # auger bores
T_S0, T_S1 = C["filled"] - 0.1, C["slurry"] + 0.3          # slurry fills
T_R0, T_R1 = C["hole"] + 0.5, C["slurry"] + 0.5            # auger withdraws
T_CAGE = C["cage"] - 0.1                                    # cage drops (1.0 s)
T_P0, T_P1 = C["pumped"] - 0.2, C["bottom"] + 0.35         # tremie pipe lowered
T_C0, T_C1 = C["pipe"] + 0.1, C["out"] + 0.25              # concrete rises (bottom to top)
T_ONE = C["thats2"] + 0.2
DEPTH = PW([(0, 0.0), (T_D0, 0.0), (T_D1, -ZB)])
SLURRY_TOP = PW([(0, ZB), (T_S0, ZB), (T_S1, 0.0)])
CONC = PW([(0, ZB), (T_C0, ZB), (T_C0 + 0.6, ZB + 3.0), (T_C1, 0.0)])
# other piles: time-lapse after "need"
T_TL = C["tower2"] - 0.1
OTHER = [i for i in range(len(PX)) if i != HERO]
TL_ORDER = {i: k for k, i in enumerate(sorted(OTHER, key=lambda i: abs(PX[i])))}
def other_depth(i): t0 = T_TL + 0.18 * TL_ORDER[i]; return PW([(0, 0.0), (t0, 0.0), (t0 + 0.35, -ZB)])
def other_conc(i): t0 = T_TL + 0.18 * TL_ORDER[i] + 0.3; return PW([(0, ZB), (t0, ZB), (t0 + 0.4, 0.0)])

# bedrock drops away for the friction beat
T_BR0, T_BR1 = C["rock"] - 0.05, C["deep2"] + 0.55
BR_Z = PW([(0, 0.0), (T_BR0, 0.0), (T_BR1, -16.0)])
# raft lands, tower rises, everything settles
T_RAFT = C["raft"] - 0.35
T_TW0, T_TW1 = C["spreads"] - 0.1, C["load"] + 0.5
TOWER_S = PW([(0, 1.0), (T_FIRST - 0.02, 1.0), (T_FIRST, 0.0), (T_TW0, 0.0), (T_TW1, 1.0)])
T_SINK0, T_SINK1 = C["sinks"] - 0.15, C["little"] + 0.45
SINK = PW([(0, 0.0), (T_SINK0, 0.0), (T_SINK1, -0.55)])

GA = empty("SetA")
BLOCK_X = 15.0
blk = box("GroundA", -BLOCK_X, BLOCK_X, YF, 12.0, ZB, 0.0, M_SOIL_A)
# hole cutters: one per front-row pile, each grows down with its drill depth (animated boolean, so a hole exists only where it was drilled)
CUTC = bpy.data.collections.new("HoleCutters"); scene.collection.children.link(CUTC)
mod = blk.modifiers.new("Holes", "BOOLEAN"); mod.operation = "DIFFERENCE"; mod.operand_type = "COLLECTION"; mod.collection = CUTC
try: mod.solver = "EXACT"
except Exception: pass
deep = box("DeepClay", -BLOCK_X + 0.01, BLOCK_X - 0.01, YF + 0.01, 12.0 - 0.01, -70.0, ZB, M_SOIL_A)
rock = box("Bedrock", -BLOCK_X - 0.03, BLOCK_X + 0.03, YF - 0.03, 12.03, ZB - 30.0, ZB, M_ROCK)
bake_fn(rock, "location", 2, BR_Z)
glow(B_ROCK, pulse(C["bedrock"], 0.35, 0.0, 0.2, 1.2, 0.6))

SINKO = empty("SinkA")
bake_fn(SINKO, "location", 2, SINK)

# per-slot pieces: plug (soil left in the hole), concrete, (hero) slurry
plugs, concs = {}, {}
for i, x in enumerate(PX):
    dep = DEPTH if i == HERO else other_depth(i)
    con = CONC if i == HERO else other_conc(i)
    bm = bmesh.new(); add_cyl(bm, PR + 0.02, 1.0, "Z", (0, 0, -0.5), 32)
    me = bpy.data.meshes.new(f"Cut{i}"); bm.to_mesh(me); bm.free()
    cu = bpy.data.objects.new(f"Cut{i}", me); CUTC.objects.link(cu); cu.location = (x, YF, 0.5); cu.display_type = "WIRE"; cu.hide_render = True
    bake_fn(cu, "scale", 2, lambda t, dep=dep: 0.001 if dep(t) < 0.05 else min(-ZB + 0.4, dep(t) + 0.5))
    plugs[i] = cu
    cc = half_cyl(f"Pile{i}", PR + 0.025, 0, YF, YF, 0.0, 1.0, M_CONC, SINKO)
    cc.location = (x, YF, ZB)
    bake_fn(cc, "scale", 2, lambda t, con=con: max(0.001, con(t) - ZB))
    t_on = T_C0 if i == HERO else T_TL + 0.18 * TL_ORDER[i] + 0.3
    windows(cc, [(t_on, DUR)])
    concs[i] = cc
glow(B_CONC, pulse(T_ONE, 1.4, 0.0, 0.2, 0.9, 0.5) + pulse(C["grips"], 0.9, 0.0, 0.3, 1.2, 0.6) + pulse(C["ties"], 0.9, 0.0, 0.2, 0.8, 0.5))

# hero: slurry column (from max(hole bottom, concrete top) up to the slurry top)
HX = PX[HERO]
sl = half_cyl("Slurry", PR - 0.03, HX, YF, YF + 0.02, 0.0, 1.0, M_SLURRY)
def slurry_lo(t): return max(-DEPTH(t), CONC(t))
bake_fn(sl, "location", 2, slurry_lo)
bake_fn(sl, "scale", 2, lambda t: max(0.001, SLURRY_TOP(t) - slurry_lo(t)))
windows(sl, [(T_S0, T_C1)])

# drill rig: crawler, mast, boom, kelly bar + auger
RIG = empty("Rig")
box("RigBody", HX + 1.6, HX + 6.4, YF + 0.6, YF + 4.6, 0.6, 2.6, M_RIG, RIG)
box("RigTrackF", HX + 1.2, HX + 6.8, YF + 0.4, YF + 1.4, 0.0, 0.9, M_RIGD, RIG)
box("RigTrackB", HX + 1.2, HX + 6.8, YF + 3.8, YF + 4.8, 0.0, 0.9, M_RIGD, RIG)
box("RigCab", HX + 4.6, HX + 6.2, YF + 0.7, YF + 2.4, 2.6, 4.2, M_RIGD, RIG)
box("RigMast", HX + 1.3, HX + 1.9, YF + 1.6, YF + 2.4, 0.8, 17.0, M_RIG, RIG)
box("RigBoom", HX - 0.4, HX + 1.9, YF + 1.6, YF + 2.4, 16.4, 17.0, M_RIG, RIG)
bm = bmesh.new(); add_bar(bm, (HX + 1.6, YF + 2.0, 1.5), (HX + 1.6, YF + 2.0, 12.0), 0.15); add_bar(bm, (HX + 4.0, YF + 2.6, 2.6), (HX + 1.6, YF + 2.0, 10.0), 0.18)
mesh_obj("RigStay", bm, M_RIGD, RIG)
windows(RIG, [(T_FIRST, T_TL - 0.05)])
AUG_Z = PW([(0, 1.0), (T_D0, 1.0), (T_D1, ZB + 0.2), (T_R0, ZB + 0.2), (T_R1, 3.0)])   # bottom of the auger
KELLY = empty("Kelly", (HX, YF, 0))
bm = bmesh.new()
add_cyl(bm, 0.12, 1.0, "Z", (0, 0, 0.5), 12)
kelly = mesh_obj("KellyBar", bm, M_AUGER, KELLY)
bake_fn(kelly, "location", 2, lambda t: AUG_Z(t) + 3.0)
bake_fn(kelly, "scale", 2, lambda t: max(0.01, 16.4 - (AUG_Z(t) + 3.0)))
AUG = empty("AugerRoot", (0, 0, 0), KELLY)
bm = bmesh.new(); add_cyl(bm, 0.16, 3.0, "Z", (0, 0, 1.5), 12)
for k in range(30):     # helical flight made of small blades
    a = k * 0.62; z = 0.08 + k * 0.095
    p0 = (0.14 * math.cos(a), 0.14 * math.sin(a), z); p1 = (0.56 * math.cos(a), 0.56 * math.sin(a), z + 0.06)
    add_bar(bm, p0, p1, 0.16)
mesh_obj("Auger", bm, M_AUGER, AUG)
bake_fn(AUG, "location", 2, AUG_Z)
bake_fn(AUG, "rotation_euler", 2, lambda t: 9.0 * max(0.0, min(t, T_R1) - T_D0) if t > T_D0 else 0.0)
windows(KELLY, [(T_FIRST, T_CAGE - 0.05)])

# wall-push arrows (slurry pressure on the walls)
bm = bmesh.new()
for z in (-5.0, -12.0, -19.0):
    add_arrow(bm, (HX - 0.15, z), (-1, 0), 1.25, 0.55, YF - 0.08); add_arrow(bm, (HX + 0.15, z), (1, 0), 1.25, 0.55, YF - 0.08)
wall_arrows = mesh_obj("WallArrows", bm, M_ARROW)
T_WA = C["pushes"] - 0.05
wall_arrows.location = (0, 0, 0)
bake_fn(wall_arrows, "scale", 0, lambda t: max(0.001, pop(t, T_WA, 0.3) * (1 + 0.06 * math.sin(10 * (t - T_WA)))))
windows(wall_arrows, [(T_WA, C["steel"] - 0.15)])

# steel cage (half cage on the cut face)
bm = bmesh.new()
CAGE_R, CAGE_L = PR - 0.14, -ZB - 0.4
for k in range(9):
    a = math.pi * k / 8
    add_bar(bm, (CAGE_R * math.cos(a), CAGE_R * math.sin(a), 0), (CAGE_R * math.cos(a), CAGE_R * math.sin(a), CAGE_L), 0.06)
for z in [0.4 + 1.2 * k for k in range(int(CAGE_L / 1.2))]:
    for k in range(8):
        a0, a1 = math.pi * k / 8, math.pi * (k + 1) / 8
        add_bar(bm, (CAGE_R * math.cos(a0), CAGE_R * math.sin(a0), z), (CAGE_R * math.cos(a1), CAGE_R * math.sin(a1), z), 0.05)
cage = mesh_obj("Cage", bm, M_STEEL)
cage.location = (HX, YF + 0.04, 0)
CAGE_Z = lambda t: (ZB + 0.3) + (CAGE_L + 6.0) * (1 - ease((t - T_CAGE) / 1.0)) if t < T_CAGE + 1.0 else ZB + 0.3
bake_fn(cage, "location", 2, CAGE_Z)
windows(cage, [(T_CAGE, T_TL - 0.05)])
glow(B_STEEL, pulse(C["cage"] + 0.05, 1.5, 0.0, 0.15, 0.6, 0.5))

# tremie pipe (lowered to the bottom, raised while the concrete rises, tip kept below the concrete top)
PIPE_L = 30.0
pipe = half_cyl("Tremie", 0.17, HX, YF + 0.02, YF + 0.02, -PIPE_L, 0.0, M_PIPE, seg=16)     # origin at the pipe top
hopper = half_cyl("Hopper", 0.55, 0, 0, 0.0, 0.0, 0.9, M_PIPE, seg=20)
hopper.parent = pipe; hopper.matrix_parent_inverse = Matrix.Identity(4); hopper.location = (0, 0, 0)
def pipe_top(t):
    tip_down = ZB + 0.6
    if t < T_P1: return PIPE_L + tip_down + 12.0 * (1 - ease((t - T_P0) / (T_P1 - T_P0)))
    tip = min(max(tip_down, CONC(t) - 2.5), 2.0)
    return tip + PIPE_L
bake_fn(pipe, "location", 2, pipe_top)
windows(pipe, [(T_P0, C["out"] + 0.3)])

# slurry pushed up and out: blobs arcing from the hole into a tank
tank = box("SlurryTank", HX - 5.6, HX - 3.4, YF + 0.6, YF + 2.6, 0.0, 1.6, M_TANK)
windows(tank, [(C["concrete2"] - 0.2, T_TL - 0.05)])
BLOBS = []
for k in range(12):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.22 + 0.06 * random.random())
    o = mesh_obj(f"SlurryBlob{k}", bm, M_SLURRY)
    t0 = C["rises"] + 0.05 + k * 0.2
    def bpos(t, t0=t0):
        u = lin((t - t0) / 0.75)
        return Vector((HX - 4.5 * u, YF + 0.5 + 1.1 * u, 0.4 + 2.8 * math.sin(math.pi * u) + 1.0 * (1 - u)))
    for ax in range(3): bake_fn(o, "location", ax, lambda t, ax=ax, bp=bpos: bp(t)[ax])
    windows(o, [(t0, t0 + 0.75)])
# hero pile glow handled on the shared concrete material (see glow(B_CONC, ...))

# ghost piles: the idea of reaching down (cyan, grow from the surface)
bm = bmesh.new()
for x in PX: add_cyl(bm, PR + 0.06, 1.0, "Z", (x, YF, -0.5), 24)
ghost = mesh_obj("GhostPiles", bm, M_GHOST)
T_GH0, T_GH1 = C["reach"] - 0.05, C["down"] + 0.45
bake_fn(ghost, "scale", 2, lambda t: max(0.001, -ZB * ease((t - T_GH0) / (T_GH1 - T_GH0))))
windows(ghost, [(T_GH0, T_FIRST)])

# pile heads over the whole footprint (pop in a wave for "hundreds")
heads = []
for gx in PX:
    for gy in (-4.0, -2.0, 0.0, 2.0, 4.0, 6.0):
        bm = bmesh.new(); add_cyl(bm, PR, 0.12, "Z", (0, 0, 0.04), 24)
        o = mesh_obj(f"Head{gx}_{gy}", bm, M_HEAD, SINKO); o.location = (gx, gy, 0)
        t0 = T_TL + 0.15 + 0.035 * ((gx + 6) + (gy + 4) * 1.4)
        for ax in (0, 1, 2): bake_fn(o, "scale", ax, lambda t, t0=t0: max(0.001, pop(t, t0, 0.2)))
        windows(o, [(t0, T_RAFT + 0.5)])
        heads.append(o)
glow(B_HEAD, pulse(T_TL + 0.4, 1.0, 0.0, 0.3, 1.0, 0.6))

# end bearing: tips on the bedrock (gold discs + up arrows)
bm = bmesh.new()
for x in PX: add_cyl(bm, PR + 0.05, 0.18, "Z", (x, YF + 0.02, ZB + 0.09), 24)
tips = mesh_obj("Tips", bm, M_ARROWG)
bm = bmesh.new()
for x in PX: add_arrow(bm, (x, ZB - 3.2), (0, 1), 2.9, 0.75, YF - 0.12)
up_arrows = mesh_obj("BearingArrows", bm, M_ARROWG)
T_TIP = C["bedrock"] - 0.05
windows(tips, [(T_TIP, T_BR0 - 0.05)]); windows(up_arrows, [(C["legs"] - 0.1, T_BR0 - 0.05)])
bake_fn(up_arrows, "location", 2, lambda t: 0.25 * math.sin(6 * t))

# friction: chevrons pointing up on both sides of every front pile
bm = bmesh.new()
for x in PX:
    for z in (-4.0, -9.0, -14.0, -19.0, -24.0):
        add_arrow(bm, (x - PR - 0.35, z - 0.9), (0, 1), 1.8, 0.45, YF - 0.08); add_arrow(bm, (x + PR + 0.35, z - 0.9), (0, 1), 1.8, 0.45, YF - 0.08)
fr_arrows = mesh_obj("FrictionArrows", bm, M_ARROW)
T_FR = C["friction"] - 0.05
bake_fn(fr_arrows, "scale", 0, lambda t: max(0.001, pop(t, T_FR, 0.3)))
bake_fn(fr_arrows, "location", 2, lambda t: 0.3 * math.sin(5 * (t - T_FR)) if t > T_FR + 0.3 else 0.0)
windows(fr_arrows, [(T_FR, C["then2"] - 0.1)])
glow(B_ARROW, [(1, 5.0)])

# raft + tower (children of SinkA)
RAFTX, RAFTY0, RAFTY1 = 7.6, YF, 7.6
raft = box("Raft", -RAFTX, RAFTX, RAFTY0 - 0.03, RAFTY1, -0.7, RAFT_T, M_RAFT, SINKO)
bake_fn(raft, "location", 2, lambda t: drop(t, T_RAFT, 9.0, 0.5) if t > T_FIRST else 0.0)
windows(raft, [(0, T_FIRST), (T_RAFT - 0.02, DUR)])
glow(B_RAFT, pulse(C["ties"] - 0.05, 1.1, 0.0, 0.2, 0.9, 0.5) + pulse(C["twelve"] - 0.1, 0.8, 0.0, 0.2, 0.8, 0.5))
# load arrows: raft spreads the tower load into the piles
bm = bmesh.new()
for x in PX: add_arrow(bm, (x, RAFT_T - 0.4), (0, -1), 3.0, 0.8, YF - 0.12)
for x in (-3.0, 0.0, 3.0): add_arrow(bm, (x, RAFT_T + 4.5), (0, -1), 3.6, 1.3, YF - 0.12)
load_arrows = mesh_obj("LoadArrows", bm, M_ARROWG, SINKO)
T_LD = C["spreads"] - 0.05
bake_fn(load_arrows, "location", 2, lambda t: -0.35 * lin((t - T_LD) / 0.4) + 0.25 * math.sin(6 * (t - T_LD)) if t > T_LD else 0.0)
windows(load_arrows, [(T_LD, C["burj"] - 0.1)])
TOWER = empty("Tower", (0, 0, RAFT_T), SINKO)
bake_fn(TOWER, "scale", 2, lambda t: max(0.001, TOWER_S(t)))
box("TowerMain", -6.0, 6.0, -5.0, 6.0, 0.0, 54.0, M_GLASS, TOWER)
box("TowerTop", -4.2, 4.2, -3.4, 4.4, 54.0, 61.0, M_GLASS, TOWER)
box("TowerLobby", -6.2, 6.2, -5.2, 6.2, 0.0, 0.6, M_RAFT, TOWER)
for z in (18.0, 36.0, 54.0): box(f"TowerBand{z}", -6.08, 6.08, -5.08, 6.08, z - 0.4, z + 0.4, M_RAFT, TOWER)
cyl("Spire", 0.35, 9.0, "Z", (0, 0.5, 65.5), M_PIPE, TOWER, 12)
windows(TOWER, [(0, T_FIRST), (T_TW0 + 0.02, DUR)])
# level lines for "sinks a little, and evenly"
lvl0 = box("LevelOld", -RAFTX - 1.4, RAFTX + 1.4, YF - 0.22, YF - 0.12, RAFT_T - 0.05, RAFT_T + 0.05, M_LINE)
windows(lvl0, [(T_SINK0 - 0.3, C["would"] - 0.1)])
lvl1 = box("LevelNew", -RAFTX - 1.4, RAFTX + 1.4, YF - 0.22, YF - 0.12, RAFT_T - 0.05, RAFT_T + 0.05, M_ARROWG, SINKO)
windows(lvl1, [(C["evenly"] - 0.15, C["would"] - 0.1)])
# depth bracket for "about twelve feet thick"
bm = bmesh.new(); add_box(bm, RAFTX + 0.5, RAFTX + 0.62, YF - 0.2, YF - 0.1, 0.0, RAFT_T)
add_box(bm, RAFTX + 0.2, RAFTX + 0.92, YF - 0.2, YF - 0.1, -0.06, 0.06); add_box(bm, RAFTX + 0.2, RAFTX + 0.92, YF - 0.2, YF - 0.1, RAFT_T - 0.06, RAFT_T + 0.06)
brk = mesh_obj("RaftBracket", bm, M_LINE, SINKO)
windows(brk, [(C["twelve"] - 0.15, C["heres"] - 0.1)])
# front cover that drops away on "cut it open"
cover = box("FrontCover", -BLOCK_X - 0.1, BLOCK_X + 0.1, YF - 0.4, YF - 0.06, -60.0, 0.02, M_SOIL_A)
T_CV0, T_CV1 = C["cut"] - 0.05, C["open"] + 0.45
bake_fn(cover, "location", 2, lambda t: -75.0 * ease((t - T_CV0) / (T_CV1 - T_CV0)) ** 1.6)
bake_fn(cover, "location", 1, lambda t: -6.0 * ease((t - T_CV0) / (T_CV1 - T_CV0)))
windows(cover, [(0, T_CV1 + 0.05)])
cmat, cb = mat("CoverDirt", (0.16, 0.11, 0.07), 0.95, 0.0, GOLD, 4); cover.data.materials[0] = cmat

# ================= SET B: soil grains + water, squeezed =================
OX = 2000.0
box("PedestalB", OX - 3.4, OX + 3.4, -3.4, 3.4, -1.2, 0.0, M_PED)
bm = bmesh.new()
N_G, SP = 6, 0.72
packed = []
for ix in range(N_G):
    for iy in range(N_G):
        for iz in range(N_G):
            c = Vector((OX + (ix - (N_G - 1) / 2) * SP + random.uniform(-0.1, 0.1), (iy - (N_G - 1) / 2) * SP + random.uniform(-0.1, 0.1),
                        0.36 + iz * SP + random.uniform(-0.08, 0.08)))
            r_ = 0.30 + random.uniform(-0.05, 0.04)
            res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r_)
            bmesh.ops.translate(bm, verts=res["verts"], vec=c)
            packed.append((res["verts"], c))
grains = mesh_obj("Grains", bm, M_GRAIN)
SQ = 0.80
grains.shape_key_add(name="Basis"); sk = grains.shape_key_add(name="Packed", from_mix=False)
me = grains.data
sk_data = sk.data
# move each grain (not squash it): find each vertex's grain centre by rebuilding the order
idx = 0
for vs, c in packed:
    n = len(vs)
    nc = Vector((c.x, c.y, c.z * SQ))
    for k in range(n):
        sk_data[idx + k].co = me.vertices[idx + k].co - c + nc
    idx += n
T_SQ0, T_SQ1 = C["squeezes"] - 0.05, C["together"] + 0.4
bake_fn(grains.data.shape_keys, 'key_blocks["Packed"].value', -1, lambda t: ease((t - T_SQ0) / (T_SQ1 - T_SQ0)))
H_PACK = 0.36 + (N_G - 1) * SP + 0.36
water = box("PoreWater", OX - N_G * SP / 2 - 0.02, OX + N_G * SP / 2 + 0.02, -N_G * SP / 2 - 0.02, N_G * SP / 2 + 0.02, 0.0, H_PACK, M_WATER)
bake_fn(water, "scale", 2, lambda t: 1 - (1 - SQ) * ease((t - T_SQ0) / (T_SQ1 - T_SQ0)))
glow(B_WATER, [(1, 0.4)] + pulse(C["water"] - 0.05, 2.0, 0.4, 0.15, 0.6, 0.5))
WEIGHT = empty("WeightB", (OX, 0, 0))
box("WeightBlock", -2.6, 2.6, -2.6, 2.6, 0.0, 1.5, M_WEIGHT, WEIGHT)
T_WT = C["weight"] - 0.35
bake_fn(WEIGHT, "location", 2, lambda t: H_PACK + 0.02 + drop(t, T_WT, 7.0, 0.4) - H_PACK * (1 - SQ) * ease((t - T_SQ0) / (T_SQ1 - T_SQ0)))
for k in range(10):      # water squeezed out at the sides
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.12)
    o = mesh_obj(f"Squirt{k}", bm, M_DROP)
    ang = 2 * math.pi * k / 10 + 0.3; t0 = T_SQ0 + 0.05 * (k % 4)
    def sq(t, ang=ang, t0=t0):
        u = lin((t - t0) / 0.7)
        rr = N_G * SP / 2 + 0.1 + 2.2 * u
        return Vector((OX + rr * math.cos(ang), rr * math.sin(ang), H_PACK * 0.55 + 1.2 * math.sin(math.pi * u * 0.8) - 1.8 * u * u))
    for ax in range(3): bake_fn(o, "location", ax, lambda t, ax=ax, f=sq: f(t)[ax])
    windows(o, [(t0, t0 + 0.7)])

# ================= SET C: tower on a shallow base over soft clay =================
OX2 = 4000.0
YC = -6.0
TCY = -3.3                                    # tower axis y (just behind the cut face)
blkC = box("GroundC", OX2 - 16.0, OX2 + 16.0, YC, 10.0, -32.0, 0.0, M_SOIL_C)
PIV = empty("PisaPivot", (OX2, TCY, -3.0))
bm = bmesh.new(); add_cyl(bm, 3.4, 3.0, "Z", (0, 0, 1.5), 40); cut_front(bm, YC - TCY - 0.03)
mesh_obj("PisaFoundation", bm, M_STONE, PIV)
TW = empty("PisaTower", (0, 0, 3.0), PIV)
cyl("PisaDrum", 2.6, 18.0, "Z", (0, 0, 9.0), M_MARBLE, TW, 40)
for k in range(7): cyl(f"PisaLedge{k}", 2.85, 0.32, "Z", (0, 0, 2.6 + k * 2.4), M_MARBLE, TW, 40)
cyl("PisaBelfry", 2.0, 2.6, "Z", (0, 0, 19.3), M_MARBLE, TW, 32)
cyl("PisaRoof", 2.1, 0.5, "Z", (0, 0, 20.85), M_ROOF, TW, 32)
bm = bmesh.new()      # arcade columns ring (reads as a bell tower, not a chimney)
for k in range(7):
    for j in range(16):
        a = 2 * math.pi * j / 16
        add_cyl(bm, 0.12, 2.0, "Z", (2.72 * math.cos(a), 2.72 * math.sin(a), 3.6 + k * 2.4), 8)
mesh_obj("PisaColumns", bm, M_MARBLE, TW)
T_GV0, T_GV1 = C["gives"] - 0.1, C["way"] + 0.6
T_LN0, T_LN1 = C["started"] - 0.1, C["built"] + 0.5
TILT = PW([(0, 0.0), (T_GV0, 0.0), (T_GV1, 2.0), (T_LN0, 2.0), (T_LN1, 5.0)])
SINKC = PW([(0, 0.0), (T_GV0, 0.0), (T_GV1, -0.8), (T_LN0, -0.8), (T_LN1, -1.1)])
bake_fn(PIV, "rotation_euler", 1, lambda t: math.radians(TILT(t)))
bake_fn(PIV, "location", 2, lambda t: -3.0 + SINKC(t))
glow(B_SOIL_C, pulse(C["soft"] - 0.05, 0.22, 0.0, 0.2, 1.0, 0.6))
# "about ten feet deep" bracket on the cut face
bm = bmesh.new(); BXC = OX2 - 2.6
add_box(bm, BXC - 0.06, BXC + 0.06, YC - 0.2, YC - 0.1, -3.0, 0.0)
add_box(bm, BXC - 0.45, BXC + 0.45, YC - 0.2, YC - 0.1, -3.06, -2.94); add_box(bm, BXC - 0.45, BXC + 0.45, YC - 0.2, YC - 0.1, -0.06, 0.06)
brkC = mesh_obj("DepthBracketC", bm, M_LINE)
windows(brkC, [(C["ten"] - 0.15, C["started"] - 0.1)])
# compression arrows under the foundation (soft clay squeezed)
bm = bmesh.new()
for x in (-2.0, 0.0, 2.0): add_arrow(bm, (OX2 + x, -3.6), (0, -1), 2.4, 0.8, YC - 0.12)
sqC = mesh_obj("ClayArrows", bm, mat("ArrowRed", RED, 0.5, 0.0, RED)[0])
bpy.data.materials["ArrowRed"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 5.0
bake_fn(sqC, "location", 2, lambda t: 0.25 * math.sin(6 * t))
windows(sqC, [(C["gives"] - 0.1, C["thats"] - 0.05), (C["clay"] - 0.1, C["so"] - 0.1)])

# ================= camera =================
cam_d = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", cam_d); scene.collection.objects.link(cam); scene.camera = cam
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.clip_start = 0.1; cam_d.clip_end = 800
SZ = lambda k: (lambda t: k + SINK(t))
SHOTS = [  # (t, cam loc, target, lens[, "cut"])
    (0.0, (14.0, -112.0, 4.0), (0.0, 0.0, 16.0), 24),
    (C["cut"] - 0.15, (10.0, -92.0, -2.0), (0.0, 0.0, 6.0), 24),
    (C["open"] + 0.4, (8.0, -70.0, -10.0), (0.0, 0.0, -9.0), 24),
    (C["soil"] - 0.1, (OX + 6.0, -14.5, 7.5), (OX, 0.0, 2.6), 30, "cut"),
    (C["put"] - 0.2, (OX + 4.5, -12.0, 6.5), (OX, 0.0, 2.6), 30),
    (C["put"] - 0.1, (OX2 + 9.0, -50.0, 6.0), (OX2, 0.0, 2.0), 26, "cut"),
    (C["its"] - 0.2, (OX2 + 7.0, -44.0, 4.0), (OX2, 0.0, 1.5), 26),
    (C["its"] - 0.1, (OX2 + 5.0, -21.0, 0.5), (OX2, -4.0, -1.8), 28, "cut"),
    (C["started"] - 0.3, (OX2 + 4.0, -19.0, 0.0), (OX2, -4.0, -2.0), 28),
    (C["started"], (OX2 + 10.0, -46.0, 6.0), (OX2, 0.0, 4.0), 26),
    (C["so"] - 0.1, (14.0, -105.0, 8.0), (0.0, 0.0, 6.0), 24, "cut"),
    (T_FIRST - 0.05, (10.0, -90.0, 0.0), (0.0, 0.0, -4.0), 24),
    (T_FIRST, (7.0, -33.0, -2.0), (0.6, YF, -5.0), 26, "cut"),
    (C["pushes"] - 0.25, (6.0, -30.0, -5.0), (0.6, YF, -8.0), 26),
    (C["pushes"] - 0.1, (4.5, -20.0, -11.0), (0.0, YF, -12.0), 28, "cut"),
    (C["steel"] - 0.25, (3.5, -19.0, -11.5), (0.0, YF, -12.0), 28),
    (C["steel"] - 0.15, (7.0, -34.0, -4.0), (0.6, YF, -8.5), 26, "cut"),
    (C["heavy2"], (6.0, -31.0, -6.0), (0.0, YF, -9.0), 26),
    (C["thats2"] + 0.3, (6.0, -33.0, -5.0), (0.0, YF, -9.0), 26),
    (T_TL - 0.05, (16.0, -50.0, 22.0), (0.0, 0.0, -6.0), 24, "cut"),
    (C["some"] - 0.25, (13.0, -46.0, 18.0), (0.0, 0.0, -7.0), 24),
    (C["some"] - 0.15, (6.0, -26.0, -20.0), (0.0, YF, -24.0), 26, "cut"),
    (C["when"] - 0.2, (5.0, -24.0, -21.0), (0.0, YF, -24.0), 26),
    (C["when"] - 0.1, (9.0, -58.0, -16.0), (0.0, YF, -20.0), 24, "cut"),
    (C["friction"], (8.0, -52.0, -13.0), (0.0, YF, -14.0), 24),
    (C["then2"] - 0.25, (6.0, -48.0, -12.0), (0.0, YF, -13.0), 24),
    (C["then2"] - 0.15, (16.0, -44.0, 14.0), (0.0, 0.0, 0.5), 26, "cut"),
    (C["spreads"] - 0.2, (14.0, -40.0, 11.0), (0.0, 0.0, 0.5), 26),
    (C["burj"], (16.0, -108.0, 10.0), (0.0, 0.0, 18.0), 24),
    (C["twelve"] - 0.7, (15.0, -100.0, 12.0), (0.0, 0.0, 18.0), 24),
    (C["twelve"] - 0.6, (15.0, -26.0, 4.5), (6.0, YF, SZ(1.8)), 28, "cut"),
    (C["heres"] - 0.2, (14.0, -24.0, 4.0), (6.0, YF, SZ(1.8)), 28),
    (C["heres"] - 0.1, (10.0, -46.0, 9.0), (0.0, YF, SZ(3.0)), 26, "cut"),
    (C["evenly"], (8.0, -40.0, 7.0), (0.0, YF, SZ(3.0)), 26),
    (C["would"] - 0.1, (-24.0, -100.0, 6.0), (0.0, 0.0, 12.0), 24, "cut"),
    (C["end"], (22.0, -104.0, 12.0), (0.0, 0.0, 14.0), 24),
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
    cam_loc.append(l0 + Vector((0.05 * math.sin(t * 0.7), 0.0, 0.03 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
fc = fcurve(cam_d, "lens", -1)
fc.keyframe_points.clear(); fc.keyframe_points.add(FRAMES); co = []
for i, v in enumerate(cam_lens): co += [i + 1, v]
fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * FRAMES); fc.update()

# ================= world + lights: dark studio =================
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
bg_ref = wn.new("ShaderNodeBackground"); bg_ref.inputs["Color"].default_value = (0.55, 0.6, 0.68, 1); bg_ref.inputs["Strength"].default_value = 0.25
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_ref.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
def target(name, loc):
    o = bpy.data.objects.new(name, None); scene.collection.objects.link(o); o.location = loc; return o
def area(name, loc, size, power, rgb=(1, 1, 1), target_=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target_; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
sun = bpy.data.lights.new("Key", "SUN"); sun.energy = 2.2; sun.color = (1.0, 0.93, 0.82); sun.angle = math.radians(5)
so = bpy.data.objects.new("Key", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(55), math.radians(10), math.radians(-28))
sun2 = bpy.data.lights.new("Fill", "SUN"); sun2.energy = 0.8; sun2.color = (0.7, 0.82, 1.0)
so2 = bpy.data.objects.new("Fill", sun2); scene.collection.objects.link(so2); so2.rotation_euler = (math.radians(75), math.radians(-10), math.radians(150))
# the cut faces look along -Y; a big soft front light keeps the soil layers readable
LT_A = target("LT_FaceA", (0, YF, -12)); area("FaceA", (6.0, -40.0, 6.0), 30.0, 14000, (1.0, 0.95, 0.88), LT_A)
LT_B = target("LT_B", (OX, 0, 2)); area("KeyB", (OX - 7.0, -10.0, 10.0), 6.0, 1500, (1.0, 0.93, 0.82), LT_B)
area("RimB", (OX + 6.0, 8.0, 8.0), 5.0, 1800, (0.75, 0.85, 1.0), LT_B)
LT_C = target("LT_FaceC", (OX2, YC, -4)); area("FaceC", (OX2 + 6.0, -36.0, 8.0), 24.0, 8000, (1.0, 0.95, 0.88), LT_C)
area("CamFill", (0, 0, 0), 3.5, 120, (1.0, 0.96, 0.9), TGT).parent = cam

# ================= render settings =================
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

# ================= export cues, events and projected anchors for the typography =================
ANCH = {
    "grains": lambda t: Vector((OX - 1.4, -N_G * SP / 2, 1.2)),
    "water": lambda t: Vector((OX + 1.0, -N_G * SP / 2, 2.6 * (1 - (1 - SQ) * ease((t - T_SQ0) / (T_SQ1 - T_SQ0))))),
    "weight": lambda t: Vector((OX + 1.6, -2.6, H_PACK + 0.8 + drop(t, T_WT, 7.0, 0.4))),
    "c_found": lambda t: Vector((OX2 + 1.2, YC, -1.6 + SINKC(t))),
    "c_clay": lambda t: Vector((OX2 + 7.0, YC, -14.0)),
    "c_tower": lambda t: Vector((OX2 + 2.6, TCY - 2.0, 12.0)),
    "drill": lambda t: Vector((HX + 0.6, YF, 10.0)),
    "auger": lambda t: Vector((HX + 0.5, YF, AUG_Z(t) + 1.5)),
    "slurry": lambda t: Vector((HX, YF, max(-DEPTH(t), CONC(t)) * 0.5 + SLURRY_TOP(t) * 0.5)),
    "wall": lambda t: Vector((HX + PR, YF, -12.0)),
    "cage": lambda t: Vector((HX + 0.3, YF, CAGE_Z(t) + CAGE_L * 0.55)),
    "pipe": lambda t: Vector((HX, YF, -6.0)),
    "concrete": lambda t: Vector((HX + 0.3, YF, (ZB + CONC(t)) / 2)),
    "pile": lambda t: Vector((HX + 0.4, YF, -13.0)),
    "tank": lambda t: Vector((HX - 4.5, YF + 0.6, 1.6)),
    "heads": lambda t: Vector((4.0, 2.0, 0.1)),
    "bedrock": lambda t: Vector((5.0, YF, ZB - 1.5 + BR_Z(t))),
    "tip": lambda t: Vector((2.0, YF, ZB)),
    "friction": lambda t: Vector((2.0 + PR + 0.35, YF, -11.0)),
    "raft": lambda t: Vector((4.0, YF, SINK(t) + RAFT_T * 0.5 + (drop(t, T_RAFT, 9.0, 0.5) if t > T_FIRST else 0.0))),
    "raft_edge": lambda t: Vector((RAFTX + 0.6, YF, SINK(t) + RAFT_T * 0.5)),
    "tower": lambda t: Vector((5.0, -5.0, RAFT_T + 30.0 * TOWER_S(t) + SINK(t))),
    "level": lambda t: Vector((RAFTX + 1.2, YF, RAFT_T)),
}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr); tt = TS[fr - 1]
    for k, a in ANCH.items():
        p = world_to_camera_view(scene, cam, a(tt))
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)] if p.z > 0 else [-9999, -9999])
events = {"cover": [round(T_CV0, 3), round(T_CV1, 3)], "weight": round(T_WT + 0.4, 3), "squeeze": [round(T_SQ0, 3), round(T_SQ1, 3)],
          "give": [round(T_GV0, 3), round(T_GV1, 3)], "lean": [round(T_LN0, 3), round(T_LN1, 3)],
          "ghost": [round(T_GH0, 3), round(T_GH1, 3)], "drill": [round(T_D0, 3), round(T_D1, 3)], "withdraw": [round(T_R0, 3), round(T_R1, 3)],
          "slurry_fill": [round(T_S0, 3), round(T_S1, 3)], "wall_push": round(T_WA, 3), "cage": [round(T_CAGE, 3), round(T_CAGE + 1.0, 3)],
          "pipe": [round(T_P0, 3), round(T_P1, 3)], "concrete": [round(T_C0, 3), round(T_C1, 3)],
          "blobs": [round(C["rises"] + 0.05 + k * 0.2 + 0.75, 3) for k in range(12)], "one_pile": round(T_ONE, 3),
          "timelapse": [round(T_TL + 0.18 * k + 0.3, 3) for k in range(6)], "heads": [round(T_TL + 0.15, 3), round(T_TL + 0.15 + 0.035 * (12 + 14), 3)],
          "tips": round(T_TIP, 3), "bedrock_drop": [round(T_BR0, 3), round(T_BR1, 3)], "friction": round(T_FR, 3),
          "raft_land": round(T_RAFT + 0.5, 3), "tower_rise": [round(T_TW0, 3), round(T_TW1, 3)], "sink": [round(T_SINK0, 3), round(T_SINK1, 3)]}
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
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
