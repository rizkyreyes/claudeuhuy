# Oil-Rig-Legs-3D: how a fixed oil platform (steel jacket) is built and stands in the ocean, then the deep-water tension leg platform.
# Ocean cutaway in Blender Cycles. Every cue is a word in the VO.
# One set: a sea block (section plane y = 0, camera on -y), a fabrication quay on the left (x < -95), the site at x = 0.
#   Hook: the jacket lies on a barge at the site and swings upright (preview); "cut": the opaque near half of the ocean drops away.
#   Yard: the jacket lies on the quay, is skidded onto the barge and towed; at the site it is launched off the stern, floats,
#   the legs are flooded, it upends about its top and settles on the seabed. Piles slide through sleeves, a hammer drives them,
#   grout fills the sleeve gap, a crane ship sets the deck. Waves pass through the frame. "Deeper": the seabed drops away and a
#   tension leg platform floats in its place, tendons down to piled templates.
# No people anywhere. Sizes are illustrative (not to scale, not any real platform); only numbers spoken in the VO appear in the typography.
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
DUR = round(WORDS[-1]["end"] + VO + 0.75, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(14)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("legs", "legs"), ("built", "built"), ("lying", "lying"), ("flipped", "flipped"), ("upright", "upright"), ("lets", "let's"),
        ("cut", "cut"), ("open", "open"), ("tower", "tower"), ("steel", "steel"), ("tubes", "tubes"), ("jacket", "jacket"),
        ("its", "it's"), ("welded", "welded"), ("land", "land"), ("flat", "flat"), ("skidded", "skidded"), ("barge", "barge"),
        ("towed", "towed"), ("at", "at"), ("site", "site"), ("tips", "tips"), ("back", "back"), ("splash", "splash"),
        ("legs2", "legs"), ("sealed", "sealed"), ("air", "air"), ("floats", "floats"), ("then", "then"), ("crews", "crews"),
        ("flood", "flood"), ("bottom", "bottom"), ("heavy", "heavy"), ("sinks", "sinks"), ("swings", "swings"),
        ("upright2", "upright"), ("settles", "settles"), ("seabed", "seabed"), ("but", "but"), ("mud", "mud"),
        ("steel2", "steel"), ("piles", "piles"), ("slide", "slide"), ("sleeves", "sleeves"), ("hammer", "hammer"),
        ("drives", "drives"), ("deep", "deep"), ("seabed2", "seabed"), ("then2", "then"), ("grout", "grout"), ("cement", "cement"),
        ("fills", "fills"), ("gap", "gap"), ("locks", "locks"), ("only", "only"), ("crane", "crane"), ("ship", "ship"),
        ("lift", "lift"), ("deck", "deck"), ("high", "high"), ("waves", "waves"), ("open2", "open"), ("frame", "frame"),
        ("waves2", "waves"), ("through", "through"), ("fixed", "fixed"), ("fifteen", "fifteen"), ("feet", "feet"),
        ("deeper", "deeper"), ("many", "many"), ("stand", "stand"), ("float", "float"), ("tendons", "tendons"),
        ("anchored", "anchored"), ("seabed3", "seabed"), ("pull", "pull"), ("hull", "hull"), ("harder", "harder"),
        ("rise", "rise"), ("barely", "barely"), ("up", "up"), ("would", "would"), ("ocean", "ocean"), ("tell", "tell"),
        ("comments", "comments"), ("next", "next"), ("sink", "sink"), ("smell", "smell"), ("follow", "follow")]
C = {}
for name, word in CUES: C[name] = TA(word)
C["end_t"] = DUR; C["end"] = DUR

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- baking: one value per frame, written as linear/constant keys with duplicates dropped ----------
TRACKS = {}
def rec(owner, path, index, fr, value):
    TRACKS.setdefault((owner.name, id(owner), path, index), [owner, path, index, {}])[3][fr] = float(value)
def write_tracks(interp_override=None):
    for (_, _, path, index), (owner, _, _, vals) in TRACKS.items():
        if owner.animation_data is None: owner.animation_data_create()
        act = owner.animation_data.action
        if act is None: act = bpy.data.actions.new(owner.name + "_bake"); owner.animation_data.action = act
        fc = act.fcurve_ensure_for_datablock(owner, path, index=index) if index >= 0 else act.fcurve_ensure_for_datablock(owner, path)
        frs = sorted(vals); keep = []
        for i, fr in enumerate(frs):
            v = vals[fr]
            if 0 < i < len(frs) - 1 and abs(v - vals[frs[i - 1]]) < 1e-5 and abs(v - vals[frs[i + 1]]) < 1e-5: continue
            keep.append((fr, v))
        fc.keyframe_points.add(len(keep)); fc.keyframe_points.foreach_set("co", [c for k in keep for c in k])
        interp = "CONSTANT" if path.startswith("hide") else (interp_override or "LINEAR")
        for kp in fc.keyframe_points:
            kp.interpolation = interp
            if interp == "BEZIER": kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
        fc.update()

def ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def lin(p): return max(0.0, min(1.0, p))
def out3(p): p = max(0.0, min(1.0, p)); return 1 - (1 - p) ** 3
def seg(t, a, b, v0, v1, fn=ease): return v0 + (v1 - v0) * fn((t - a) / (b - a)) if b > a else (v1 if t >= a else v0)
def pulse(t, t0, hold=1.0, peak=1.0):
    if t < t0 - 0.1: return 0.0
    if t < t0 + 0.15: return seg(t, t0 - 0.1, t0 + 0.15, 0.0, peak)
    if t < t0 + hold: return peak
    return seg(t, t0 + hold, t0 + hold + 0.45, peak, 0.0)

def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CG, CD, CP = coll("Ground"), coll("Rig"), coll("Props")

# ---------- materials (procedural: the cloud run has no texture downloads) ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
def glow_link(nt, b, rgb, k):
    """Emission strength = object custom property 'glow' * k (baked per object)."""
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "glow"
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = k
    nt.links.new(at.outputs["Fac"], mm.inputs[0]); nt.links.new(mm.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*rgb, 1)
def noise_tint(nt, b, rgb, noise, scale=6):
    tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 1 - noise; mr.inputs[4].default_value = 1 + noise
    nt.links.new(n.outputs["Fac"], mr.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
    mx.inputs[6].default_value = (*rgb, 1); cc = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3): nt.links.new(mr.outputs[0], cc.inputs[i])
    nt.links.new(cc.outputs[0], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
def flat(name, rgb, rough=0.5, metal=0.0, glow=None, k=3.0, noise=0.0, alpha=None):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if noise: noise_tint(nt, b, rgb, noise)
    if glow: glow_link(nt, b, glow, k)
    if alpha is not None: b.inputs["Alpha"].default_value = alpha
    return m
def rock_mat(name, rgb_a, rgb_b, band_scale=0.12, value=1.0):
    """World-space layered rock: horizontal strata (wave on z, distorted) mixed with noise, plus bump."""
    m, nt, b = new_mat(name); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"
    wv.inputs["Scale"].default_value = band_scale; wv.inputs["Distortion"].default_value = 6.0; wv.inputs["Detail"].default_value = 4
    L.new(g.outputs["Position"], wv.inputs["Vector"])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.35; n.inputs["Detail"].default_value = 10
    L.new(g.outputs["Position"], n.inputs["Vector"])
    mixf = nt.nodes.new("ShaderNodeMath"); mixf.operation = "MULTIPLY_ADD"; mixf.inputs[1].default_value = 0.55
    L.new(wv.outputs["Fac"], mixf.inputs[0]); L.new(n.outputs["Fac"], mixf.inputs[2])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].color = (*[c * value for c in rgb_a], 1); e[1].color = (*[c * value for c in rgb_b], 1); e[0].position = 0.35; e[1].position = 0.95
    L.new(mixf.outputs[0], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.92
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 2.5; n2.inputs["Detail"].default_value = 8
    L.new(g.outputs["Position"], n2.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.35; L.new(n2.outputs["Fac"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def soil(name, rgb_a, rgb_b, scale, stones=0.0):
    m, nt, b = new_mat(name); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = scale; n.inputs["Detail"].default_value = 8
    L.new(g.outputs["Position"], n.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements; e[0].color = (*rgb_a, 1); e[1].color = (*rgb_b, 1)
    e[0].position = 0.35; e[1].position = 0.65
    L.new(n.outputs["Fac"], ramp.inputs[0]); col = ramp.outputs[0]
    if stones:
        v = nt.nodes.new("ShaderNodeTexVoronoi"); v.inputs["Scale"].default_value = scale * 3.2; L.new(g.outputs["Position"], v.inputs["Vector"])
        st = nt.nodes.new("ShaderNodeMath"); st.operation = "LESS_THAN"; st.inputs[1].default_value = stones; L.new(v.outputs["Distance"], st.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(st.outputs[0], mx.inputs["Factor"]); L.new(col, mx.inputs[6])
        mx.inputs[7].default_value = (0.42, 0.40, 0.37, 1); col = mx.outputs[2]
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; L.new(n.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def water_mat(name):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.75, 0.92, 0.95, 1); b.inputs["Roughness"].default_value = 0.05
    b.inputs["IOR"].default_value = 1.333; b.inputs["Transmission Weight"].default_value = 1.0
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.35, 0.68, 0.70, 1); va.inputs["Density"].default_value = 0.035
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.45, 0.72, 0.75, 1); vs.inputs["Density"].default_value = 0.015
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Volume"])
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.4
    n.inputs["Detail"].default_value = 6; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.15; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
def shadow_pass(nt, b, tint=(0.85, 0.95, 1.0)):
    """Shadow rays pass through (tinted) so the sun reaches everything under the surface."""
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
    lp = nt.nodes.new("ShaderNodeLightPath"); tr = nt.nodes.new("ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (*tint, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0]); nt.links.new(b.outputs[0], mx.inputs[1]); nt.links.new(tr.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
def sea_mat(name):
    """Section water: clear tinted transmission (IOR 1.0, so nothing behind it bends) + a light blue volume for depth fade."""
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (0.55, 0.85, 0.95, 1); b.inputs["Roughness"].default_value = 0.0
    b.inputs["IOR"].default_value = 1.0; b.inputs["Transmission Weight"].default_value = 1.0
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.20, 0.55, 0.75, 1); va.inputs["Density"].default_value = 0.010
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.25, 0.60, 0.80, 1); vs.inputs["Density"].default_value = 0.004
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Volume"])
    shadow_pass(nt, b)
    return m
def surf_mat(name, rgb=(0.05, 0.22, 0.32), rough=0.08, shadow=True):
    """Sea surface seen from above: dark blue glossy with a wave bump."""
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.18
    n.inputs["Detail"].default_value = 8; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.25; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    if shadow: shadow_pass(nt, b, (0.80, 0.92, 1.0))
    return m
def strata_mat(name):
    """Seabed section: mud on top, clay, dense sand, by world height (shifted with the object so the drop keeps the layers)."""
    m, nt, b = new_mat(name); L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.6; n.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], n.inputs["Vector"])
    mz = nt.nodes.new("ShaderNodeMath"); mz.operation = "MULTIPLY_ADD"; mz.inputs[1].default_value = 3.0
    L.new(n.outputs["Fac"], mz.inputs[0]); L.new(sep.outputs["Z"], mz.inputs[2])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = -40.0; mr.inputs[2].default_value = 1.0
    L.new(mz.outputs[0], mr.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB"); e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.72, 0.58, 0.34, 1)                 # dense sand (deep)
    e1 = e.new(0.55); e1.color = (0.72, 0.58, 0.34, 1)
    e2 = e.new(0.60); e2.color = (0.46, 0.31, 0.16, 1)                      # clay
    e3 = e.new(0.88); e3.color = (0.46, 0.31, 0.16, 1)
    e4 = e.new(0.92); e4.color = (0.20, 0.16, 0.12, 1)                      # soft mud
    e[1].position = 1.0; e[1].color = (0.20, 0.16, 0.12, 1)
    L.new(mr.outputs[0], ramp.inputs[0])
    n2 = nt.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = 3.0; n2.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 0.35
    L.new(ramp.outputs[0], mx.inputs[6]); L.new(n2.outputs["Color"], mx.inputs[7])
    br = nt.nodes.new("ShaderNodeBrightContrast"); br.inputs["Bright"].default_value = 0.06
    L.new(mx.outputs[2], br.inputs[0]); L.new(br.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.95
    L.new(br.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 0.1   # section face stays readable when the sun is blocked
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.3; L.new(n2.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m
GOLD, CYAN, RED, HOT = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.45, 0.08)
M_SEA = sea_mat("SeaWater")
M_SURF = surf_mat("SeaSurface")
M_OCEAN = surf_mat("OceanOpaque", (0.03, 0.14, 0.22), 0.12, shadow=False)
M_SEABED = strata_mat("Seabed")
M_QUAY = flat("QuayConcrete", (0.50, 0.49, 0.46), 0.8, noise=0.15)
M_LAND = soil("QuayFill", (0.30, 0.25, 0.19), (0.42, 0.36, 0.28), 0.5, stones=0.08)
M_JACKET = flat("JacketSteel", (0.95, 0.62, 0.06), 0.45, 0.15, GOLD, 1.6)
M_RUNNER = flat("LaunchRunner", (0.20, 0.20, 0.22), 0.6, 0.3)
M_SLEEVE = flat("PileSleeve", (0.90, 0.90, 0.92), 0.35, 0.2, GOLD, 2.0)
M_PILE = flat("PileSteel", (0.32, 0.33, 0.35), 0.45, 0.8, CYAN, 1.5)
M_HAMMER = flat("Hammer", (0.85, 0.12, 0.08), 0.4, 0.3)
M_GROUT = flat("Grout", (0.62, 0.60, 0.55), 0.6, 0.0, GOLD, 2.5, noise=0.2)
M_FLOOD = flat("FloodGlow", (0.02, 0.10, 0.14), 0.3, 0.0, CYAN, 0.9)
M_CAP = flat("SealCap", (0.10, 0.07, 0.02), 0.4, 0.0, GOLD, 4.0)
M_BARGE = flat("BargeHull", (0.22, 0.24, 0.27), 0.55, 0.4, noise=0.1)
M_DECKP = flat("BargeDeck", (0.40, 0.18, 0.12), 0.7, 0.1, noise=0.15)
M_TUG = flat("TugRed", (0.75, 0.10, 0.08), 0.45, 0.2)
M_WHITE = flat("WhitePaint", (0.82, 0.83, 0.84), 0.5, 0.1)
M_MOD_A = flat("ModuleBlue", (0.15, 0.35, 0.62), 0.5, 0.1)
M_MOD_B = flat("ModuleGrey", (0.55, 0.56, 0.58), 0.5, 0.2)
M_MOD_C = flat("ModuleYellow", (0.92, 0.70, 0.10), 0.5, 0.1)
M_DECKST = flat("DeckSteel", (0.30, 0.31, 0.33), 0.5, 0.6, GOLD, 1.4)
M_HULL = flat("TLPHull", (0.88, 0.86, 0.80), 0.5, 0.2, GOLD, 1.0)
M_TENDON = flat("Tendon", (0.30, 0.32, 0.35), 0.4, 0.8, CYAN, 3.0)
M_TEMPL = flat("Template", (0.35, 0.34, 0.32), 0.6, 0.5)
M_CABLE = flat("Cable", (0.05, 0.05, 0.05), 0.5, 0.5)
M_SPRAY = flat("Spray", (0.85, 0.95, 1.0), 0.2, 0.0, (0.8, 0.95, 1.0), 0.6)
M_MUD = flat("MudPuff", (0.30, 0.26, 0.20), 0.9)
M_SPARK = flat("WeldSpark", (1.0, 0.8, 0.4), 0.5, 0.0, (1.0, 0.75, 0.35), 25.0)
M_STREAK = flat("WaveStreak", (0.9, 0.97, 1.0), 0.3, 0.0, (0.85, 0.97, 1.0), 2.0)
M_GLOW_C = flat("ArrowCyan", (0.02, 0.05, 0.06), 0.5, 0.0, CYAN, 3.0)
M_GLOW_R = flat("ArrowRed", (0.06, 0.01, 0.01), 0.5, 0.0, RED, 2.2)
M_GLOW_G = flat("ArrowGold", (0.06, 0.04, 0.0), 0.5, 0.0, GOLD, 3.5)
M_WINDOW = flat("Windows", (0.05, 0.05, 0.06), 0.3, 0.0, (1.0, 0.85, 0.55), 1.5)

# ---------- geometry helpers ----------
def mesh_obj(name, bm, mat, col):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if mat: me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["glow"] = 0.0
    return o
def box_bm(x0, x1, y0, y1, z0, z1, pivot=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(x1 - x0, y1 - y0, z1 - z0))
    bmesh.ops.translate(bm, verts=bm.verts, vec=((x0 + x1) / 2 - pivot[0], (y0 + y1) / 2 - pivot[1], (z0 + z1) / 2 - pivot[2]))
    return bm
def box(name, x0, x1, y0, y1, z0, z1, mat, col=CG, pivot=None):
    pivot = pivot or (0, 0, 0)
    o = mesh_obj(name, box_bm(x0, x1, y0, y1, z0, z1, pivot), mat, col); o.location = pivot; return o
def prism_bm(poly, y0, y1, pivot=(0, 0, 0)):
    """Convex polygon in the x-z plane extruded from y0 to y1."""
    bm = bmesh.new()
    a = [bm.verts.new((x - pivot[0], y0 - pivot[1], z - pivot[2])) for x, z in poly]
    b = [bm.verts.new((x - pivot[0], y1 - pivot[1], z - pivot[2])) for x, z in poly]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    n = len(poly)
    for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return bm
def prism(name, poly, y0, y1, mat, col=CD, pivot=None):
    pivot = pivot or (0, 0, 0)
    o = mesh_obj(name, prism_bm(poly, y0, y1, pivot), mat, col); o.location = pivot; return o
def cut_keep(bm, y0, keep_pos=True):
    """Keep y >= y0 (or y <= y0) and close the cut."""
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, y0, 0), plane_no=(0, 1 if keep_pos else -1, 0), clear_inner=True)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if edges: bmesh.ops.edgenet_fill(bm, edges=edges)
def cyl_bm(r, length, axis="Z", seg_n=48):
    """Cylinder centred at the origin along an axis."""
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg_n, radius1=r, radius2=r, depth=length)
    if axis == "X": bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    if axis == "Y": bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    return bm
def cyl(name, r, p0, p1, mat, col=CG, axis="Z", pivot=None, keep_y=None, seg_n=48):
    """Cylinder between two points on one axis; optional keep y >= keep_y; origin at pivot."""
    p0, p1 = Vector(p0), Vector(p1); c = (p0 + p1) / 2; L = (p1 - p0).length
    pivot = Vector(pivot) if pivot else c
    bm = cyl_bm(r, L, axis, seg_n); bmesh.ops.translate(bm, verts=bm.verts, vec=c - pivot)
    if keep_y is not None: cut_keep(bm, keep_y - pivot.y)
    o = mesh_obj(name, bm, mat, col); o.location = pivot
    o.data.shade_smooth()
    try: o.data.set_sharp_from_angle(angle=math.radians(40))
    except Exception: pass
    return o
def boolean(target, cutter, op="DIFFERENCE"):
    md = target.modifiers.new("b", "BOOLEAN"); md.operation = op; md.object = cutter; md.solver = "EXACT"
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.clear(); old = target.data; target.data = me; bpy.data.meshes.remove(old)
def delete(o): bpy.data.objects.remove(o, do_unlink=True)
def empty(name, col=CP):
    e = bpy.data.objects.new(name, None); col.objects.link(e); return e
def parent(child, par): child.parent = par; child.matrix_parent_inverse = Matrix.Identity(4)
def bar_xz(name, p0, p1, y, mat, w=0.16, col=CP):
    """Thin bar in the x-z plane between two points, at depth y (for outlines, cracks, x-ray lines)."""
    p0, p1 = Vector((p0[0], 0, p0[1])), Vector((p1[0], 0, p1[1])); d = p1 - p0; L = d.length
    o = box(name, -L / 2 - w / 2, L / 2 + w / 2, -0.03, 0.03, -w / 2, w / 2, mat, col)
    o.rotation_euler = (0, -math.atan2(d.z, d.x), 0); o.location = ((p0.x + p1.x) / 2, y, (p0.z + p1.z) / 2); return o
def arrow(name, mat, length=1.6, r=0.14):
    """Arrow along local +X, origin at the tail."""
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=r, radius2=r, depth=length - 0.6)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=((length - 0.6) / 2, 0, 0))
    hd = bmesh.new(); bmesh.ops.create_cone(hd, cap_ends=True, segments=16, radius1=r * 2.6, radius2=0.0, depth=0.6)
    bmesh.ops.rotate(hd, verts=hd.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(hd, verts=hd.verts, vec=(length - 0.3, 0, 0))
    me_h = bpy.data.meshes.new("h"); hd.to_mesh(me_h); hd.free(); bm.from_mesh(me_h); bpy.data.meshes.remove(me_h)
    return mesh_obj(name, bm, mat, CP)

def tube_into(bm, p0, p1, r, seg_n=12):
    """Append a capped cylinder from p0 to p1 into bm."""
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    if L < 1e-4: return
    t = bmesh.new(); bmesh.ops.create_cone(t, cap_ends=True, segments=seg_n, radius1=r, radius2=r, depth=L)
    q = Vector((0, 0, 1)).rotation_difference(d.normalized())
    bmesh.ops.rotate(t, verts=t.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(t, verts=t.verts, vec=(p0 + p1) / 2)
    me = bpy.data.meshes.new("t"); t.to_mesh(me); t.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
def smooth(o, ang=40):
    o.data.shade_smooth()
    try: o.data.set_sharp_from_angle(angle=math.radians(ang))
    except Exception: pass
def local_obj(name, bm, mat, par, basis=None, col=CD):
    o = mesh_obj(name, bm, mat, col); parent(o, par)
    if basis is not None: o.matrix_basis = basis
    return o

# ---------- layout (metres, illustrative). Sea: surface z = D, seabed z = 0, section plane y = 0, camera on -y ----------
D = 55.0                       # water depth (illustrative; the VO's 1,500 ft is the real-world limit)
XQ = -95.0                     # quay edge (land for x < XQ)
XS0, XS1 = -260.0, 260.0       # sea block extent in x
YS1 = 90.0                     # sea block back face
ZB = -140.0                    # seabed block bottom
H, B0, B1 = 64.0, 12.0, 6.0    # jacket height, half width at base / top (battered legs)
JY = 12.0                      # jacket centre line y (front legs on the section plane y = 0)
LEG_R, BR_R = 0.9, 0.38
LEVELS = [0.0, 14.0, 28.0, 42.0, 54.0, 64.0]
XR = 14.2                      # launch runner line (local x) on the +x face; lying pose rests on it
SLV = 14.4                     # pile sleeve centre (local |x|)
def hw(z): return B0 + (B1 - B0) * z / H
def leg(sx, sy, z): return Vector((sx * hw(z), sy * hw(z), z))

# sea: opaque near half (drops on "cut"), clear far half, waves skin, far horizon
SEA_F = box("Sea_Near", XQ, XS1, -160.0, 0.0, -60.0, D, M_OCEAN, CG, pivot=(0, 0, D))
SEA_B = box("Sea_Far", XQ, XS1, 0.0, YS1, -100.0, D, M_SEA, CG, pivot=(0, 0, D))
def wave_plane(name, x0, x1, y0, y1, z, mat, sub=60):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=sub, y_segments=max(4, sub // 3), size=0.5)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(x1 - x0, y1 - y0, 1)); bmesh.ops.translate(bm, verts=bm.verts, vec=((x0 + x1) / 2, (y0 + y1) / 2, z))
    o = mesh_obj(name, bm, mat, CG)
    wm = o.modifiers.new("wave", "WAVE"); wm.height = 0.6; wm.width = 9.0; wm.speed = 0.35; wm.narrowness = 1.2
    wm.use_normal = False; wm.start_position_x = -400; wm.start_position_y = 60; wm.falloff_radius = 0; wm.time_offset = 0
    wm.use_x = True; wm.use_y = False
    o.data.shade_smooth(); return o, wm
SURF, WAVE = wave_plane("Sea_Surface", XQ, XS1, 0.0, YS1, D + 0.02, M_SURF, 160)
HORIZON = box("Sea_Horizon", -2000, 2000, YS1, 3000, -600.0, D - 0.02, M_OCEAN, CG)
HORIZON_FRONT = box("Sea_HorizonFront", -2000, 2000, -3000, -160.0, D - 2.0, D - 0.02, M_OCEAN, CG)
# seabed block (drops on "deeper"); its near face is the section
SEABED = box("Seabed", XQ, XS1, -0.3, YS1, ZB, 0.0, M_SEABED, CG, pivot=(0, 0, 0))   # front face just ahead of the sea block so its tint does not cover the section
SEABED_F = box("Seabed_Near", XQ, XS1, -160.0, 0.0, ZB, -60.0, M_SEABED, CG, pivot=(0, 0, 0))   # under the opaque near sea
# quay (fabrication yard on land)
Z_Q = D + 4.0
QUAY = box("Quay", -420.0, XQ, -30.0, YS1, ZB, Z_Q - 1.2, M_LAND, CG)
QUAY_TOP = box("Quay_Slab", -420.0, XQ, -30.0, YS1, Z_Q - 1.2, Z_Q, M_QUAY, CG)
for k in range(3):   # skid beams on the quay
    box(f"Quay_Skid{k}", -230.0, XQ, JY - 12.0 + 12.0 * k - 0.6, JY - 12.0 + 12.0 * k + 0.6, Z_Q, Z_Q + 0.6, M_RUNNER, CG)

# ---------- the jacket: legs, levels, X-braces, launch runners, pile sleeves (jacket-local, origin at base centre) ----------
JK = empty("Jacket", CD)
bm = bmesh.new()
for sx in (-1, 1):
    for sy in (-1, 1): tube_into(bm, leg(sx, sy, -1.0), leg(sx, sy, H + 2.0), LEG_R, 16)
for i, z in enumerate(LEVELS):
    c = [leg(-1, -1, z), leg(1, -1, z), leg(1, 1, z), leg(-1, 1, z)]
    for k in range(4): tube_into(bm, c[k], c[(k + 1) % 4], BR_R + 0.08)
    if i < len(LEVELS) - 1:
        z1 = LEVELS[i + 1]; c1 = [leg(-1, -1, z1), leg(1, -1, z1), leg(1, 1, z1), leg(-1, 1, z1)]
        for k in range(4):
            tube_into(bm, c[k], c1[(k + 1) % 4], BR_R); tube_into(bm, c[(k + 1) % 4], c1[k], BR_R)
        tube_into(bm, c[0], c[2], BR_R * 0.8) if i % 2 == 0 else tube_into(bm, c[1], c[3], BR_R * 0.8)
for sy in (-1, 1):   # launch runners on the +x face, from level 1 up, with struts back to the leg
    tube_into(bm, (XR, sy * hw(8.0), 8.0), (XR, sy * hw(H), H), 0.6)
    for z in LEVELS[1:]: tube_into(bm, leg(1, sy, z), (XR, sy * hw(z), z), 0.35)
    tube_into(bm, leg(1, sy, 8.0), (XR, sy * hw(8.0), 8.0), 0.35)
for sx in (-1, 1):   # sleeve brackets
    for sy in (-1, 1):
        for z in (1.0, 7.0): tube_into(bm, leg(sx, sy, z), (sx * (SLV - 1.55), sy * B0, z), 0.3)
JLAT = local_obj("Jacket_Lattice", bm, M_JACKET, JK); smooth(JLAT)
# pile sleeves: tubes (outer 1.15, inner 0.95), z 0..8; the front pair is cut on the section plane (keep y >= 0)
SLEEVES = {}
for sx in (-1, 1):
    for sy in (-1, 1):
        o = cyl(f"Sleeve_{sx:+d}{sy:+d}", 1.6, (sx * SLV, sy * B0, 0.0), (sx * SLV, sy * B0, 8.0), M_SLEEVE, CD, pivot=(0, 0, 0), seg_n=32)
        ct = cyl("c", 1.3, (sx * SLV, sy * B0, -1.0), (sx * SLV, sy * B0, 9.0), None, CD, pivot=(0, 0, 0), seg_n=32); boolean(o, ct); delete(ct)
        if sy < 0:
            ct = box("c2", sx * SLV - 2, sx * SLV + 2, sy * B0 - 3, sy * B0, -1, 9, None, CD); boolean(o, ct); delete(ct)
        o.location = (0, 0, 0)   # mesh already in jacket-local coordinates
        parent(o, JK); SLEEVES[(sx, sy)] = o
# flood fill (x-ray cyan sleeve over the lower legs) and seal caps on the leg ends
FLOODS, CAPS = [], []
for sx in (-1, 1):
    for sy in (-1, 1):
        a, b_ = leg(sx, sy, -1.0), leg(sx, sy, 34.0); d = b_ - a
        fb = bmesh.new(); tube_into(fb, (0, 0, 0), (0, 0, d.length), LEG_R + 0.12, 16)
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        o = local_obj(f"Flood_{sx:+d}{sy:+d}", fb, M_FLOOD, JK, Matrix.Translation(a) @ q.to_matrix().to_4x4()); o["glow"] = 1.0; FLOODS.append(o)
        for z in (-1.2, H + 2.2):
            p = leg(sx, sy, z); cb = bmesh.new(); tube_into(cb, (0, 0, -0.25), (0, 0, 0.25), LEG_R + 0.25, 16)
            CAPS.append(local_obj(f"Cap_{sx:+d}{sy:+d}_{z:.0f}", cb, M_CAP, JK, Matrix.Translation(p) @ q.to_matrix().to_4x4()))

# ---------- barge, tug ----------
BL, BW = 84.0, 30.0
BARGE = empty("Barge", CP)
parent(box("Barge_Hull", -BL / 2, BL / 2, JY - BW / 2, JY + BW / 2, -6.0, 3.4, M_BARGE, CP), BARGE)
parent(box("Barge_Deck", -BL / 2, BL / 2, JY - BW / 2, JY + BW / 2, 3.4, 3.6, M_DECKP, CP), BARGE)
for k in range(2):
    parent(box(f"Barge_Skid{k}", -BL / 2, BL / 2 - 4, JY - B0 + 24.0 * k - 0.7, JY - B0 + 24.0 * k + 0.7, 3.6, 4.4, M_RUNNER, CP), BARGE)
Z_BD = 4.4                      # barge skid top above the barge origin (origin floats at the waterline)
ROCKER = box("Barge_Rocker", -BL / 2 - 1.0, -BL / 2 + 9.0, JY - 14.5, JY + 14.5, 3.6, 5.2, M_RUNNER, CP, pivot=(-BL / 2, JY, 4.4))
parent(ROCKER, BARGE); ROCKER.location = (-BL / 2, JY, 4.4)
TUG = empty("Tug", CP)
parent(box("Tug_Hull", -9.0, 9.0, JY - 4.5, JY + 4.5, -3.0, 2.5, M_TUG, CP), TUG)
parent(box("Tug_House", -6.0, 1.0, JY - 3.0, JY + 3.0, 2.5, 7.0, M_WHITE, CP), TUG)
TOWLINE = cyl("TowLine", 0.12, (0, 0, 0), (1, 0, 0), M_CABLE, CP, axis="X", pivot=(0, 0, 0), seg_n=8)

# ---------- piles, hammer, grout ----------
PILE_L = 42.5; Z_PILE_REST = -4.0; Z_PILE_DRIVEN = -34.0          # pile tip z when resting / driven (top = tip + PILE_L)
PILES = {}
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * SLV, JY + sy * B0
        PILES[(sx, sy)] = cyl(f"Pile_{sx:+d}{sy:+d}", 0.72, (x, y, 0.0), (x, y, PILE_L), M_PILE, CP, pivot=(x, y, 0.0), seg_n=32)
HAMMERS = []
for sx in (-1, 1):
    hm = empty(f"Hammer_{sx:+d}")
    parent(cyl(f"Hammer_{sx:+d}_Body", 1.3, (0, 0, 0.0), (0, 0, 7.0), M_HAMMER, CP, pivot=(0, 0, 0)), hm)
    parent(cyl(f"Hammer_{sx:+d}_Top", 0.6, (0, 0, 7.0), (0, 0, 9.0), M_RUNNER, CP, pivot=(0, 0, 0)), hm)
    HAMMERS.append((hm, (sx, -1)))
GROUTS = []
for sx in (-1, 1):
    x, y = sx * SLV, JY - B0
    g = cyl(f"Grout_{sx:+d}", 1.29, (x, y, 0.0), (x, y, 8.0), M_GROUT, CP, pivot=(x, y, 0.0), seg_n=32)
    ct = cyl("c", 0.74, (x, y, -1.0), (x, y, 9.0), None, CP, seg_n=32); boolean(g, ct); delete(ct)
    ct = box("c2", x - 2, x + 2, y - 3, y, -1, 9, None, CP); boolean(g, ct); delete(ct)
    g.location = (x, y, 0.0); GROUTS.append(g)
# (cyl with pivot already offsets the mesh; the boolean keeps that, so the origin stays at the sleeve base)

# ---------- topsides (deck): two decks, legs, modules, derrick, flare boom, helideck ----------
def topsides(name):
    root = empty(name, CD)
    parts = [box(f"{name}_Cellar", -17, 17, -15, 15, 0.0, 1.2, M_DECKST, CD), box(f"{name}_Main", -18, 18, -16, 16, 9.0, 10.2, M_DECKST, CD)]
    for sx in (-1, 1):
        for sy in (-1, 1): parts.append(cyl(f"{name}_Col{sx:+d}{sy:+d}", 0.8, (sx * 15, sy * 13, 1.2), (sx * 15, sy * 13, 9.0), M_DECKST, CD, seg_n=12))
    parts += [box(f"{name}_ModA", -16, -2, -14, 0, 1.2, 7.5, M_MOD_A, CD), box(f"{name}_ModB", 2, 16, -14, -2, 1.2, 6.5, M_MOD_B, CD),
              box(f"{name}_ModC", -16, -4, 2, 14, 10.2, 17.0, M_MOD_C, CD), box(f"{name}_Quarters", 4, 17, 2, 15, 10.2, 22.0, M_WHITE, CD),
              box(f"{name}_Win", 3.9, 17.1, 1.9, 15.1, 13.0, 13.8, M_WINDOW, CD), box(f"{name}_Win2", 3.9, 17.1, 1.9, 15.1, 17.0, 17.8, M_WINDOW, CD),
              box(f"{name}_Heli", 3, 18, 0, 16, 22.0, 22.6, M_MOD_C, CD)]
    db = bmesh.new()   # derrick: a tapered lattice tower
    for sx in (-1, 1):
        for sy in (-1, 1): tube_into(db, (-8 + sx * 3.0, -8 + sy * 3.0, 10.2), (-8 + sx * 1.0, -8 + sy * 1.0, 38.0), 0.22, 8)
    for z in (16.0, 22.0, 28.0, 34.0):
        h = 3.0 - 2.0 * (z - 10.2) / 27.8; c = [(-8 - h, -8 - h, z), (-8 + h, -8 - h, z), (-8 + h, -8 + h, z), (-8 - h, -8 + h, z)]
        for k in range(4): tube_into(db, c[k], c[(k + 1) % 4], 0.15, 6)
    parts.append(mesh_obj(f"{name}_Derrick", db, M_DECKST, CD))
    fb = bmesh.new(); tube_into(fb, (-18, 10, 10.5), (-34, 10, 24.0), 0.45, 8); parts.append(mesh_obj(f"{name}_Flare", fb, M_DECKST, CD))
    for p in parts:
        parent(p, root)
        if "Win" in p.name: p["glow"] = 1.0
    return root
DECK = topsides("Deck")
# crane ship: hull, house, crane pedestal + boom (yaw/elevation), hook cable
SHIP = empty("CraneShip", CP)
parent(box("Ship_Hull", -10.0, 70.0, -16.0, 16.0, -7.0, 5.0, M_BARGE, CP), SHIP)
parent(box("Ship_Deck", -10.0, 70.0, -16.0, 16.0, 5.0, 5.3, M_DECKP, CP), SHIP)
parent(box("Ship_House", 52.0, 68.0, -13.0, 13.0, 5.3, 20.0, M_WHITE, CP), SHIP)
parent(cyl("Ship_Pedestal", 4.0, (0, 0, 5.3), (0, 0, 12.0), M_TUG, CP, seg_n=24), SHIP)
BOOM_L, BOOM_EL = 78.0, math.radians(47)
BOOM = empty("Ship_BoomPivot", CP); parent(BOOM, SHIP); BOOM.location = (0, 0, 12.0)
bb = bmesh.new()
for sy in (-1, 1):
    for sz in (-1, 1): tube_into(bb, (0, sy * 2.2, sz * 1.4), (BOOM_L, sy * 0.6, sz * 0.4), 0.3, 8)
for k in range(1, 12):
    u = k / 12; w = 2.2 - 1.6 * u; hh = 1.4 - 1.0 * u; x = BOOM_L * u
    tube_into(bb, (x, -w, -hh), (x, w, hh), 0.15, 6); tube_into(bb, (x, -w, hh), (x, w, -hh), 0.15, 6)
BOOM_M = mesh_obj("Ship_Boom", bb, M_TUG, CP); parent(BOOM_M, BOOM); BOOM_M.rotation_euler = (0, -BOOM_EL, 0)
CABLE = cyl("Hook_Cable", 0.18, (0, 0, -1.0), (0, 0, 0.0), M_CABLE, CP, pivot=(0, 0, 0), seg_n=8)
SHIP_POS = Vector((44.0, JY, D - 0.5))

# ---------- tension leg platform (deep water) ----------
TLP = empty("TLP", CD)
TL_COL = [(sx * 14.0, JY + sy * 14.0) for sx in (-1, 1) for sy in (-1, 1)]
Z_HB, Z_HT = D - 28.0, D + 9.0         # hull column bottom / top
for i, (x, y) in enumerate(TL_COL):
    parent(cyl(f"TLP_Col{i}", 5.0, (x, y, Z_HB), (x, y, Z_HT), M_HULL, CD, seg_n=40), TLP)
for (a, b_) in ((0, 1), (2, 3), (0, 2), (1, 3)):
    (xa, ya), (xb, yb) = TL_COL[a], TL_COL[b_]
    parent(box(f"TLP_Pontoon{a}{b_}", min(xa, xb) - 3.0, max(xa, xb) + 3.0, min(ya, yb) - 3.0, max(ya, yb) + 3.0, Z_HB, Z_HB + 6.0, M_HULL, CD), TLP)
TDECK = topsides("TLPDeck"); parent(TDECK, TLP); TDECK.location = (0, JY, Z_HT)
Z_SB_DEEP = -95.0                       # seabed after the drop
TENDONS, TEMPLATES = [], []
for i, (x, y) in enumerate(TL_COL):
    for dx in (-2.2, 2.2):
        t = cyl(f"Tendon_{i}_{dx:+.0f}", 0.45, (x + dx, y, Z_HB - 1.0), (x + dx, y, Z_HB), M_TENDON, CD, pivot=(x + dx, y, Z_HB), seg_n=12)
        TENDONS.append(t)
    tp = empty(f"Template_{i}", CP)
    parent(box(f"Template_{i}_Box", x - 5, x + 5, y - 4, y + 4, 0.0, 3.0, M_TEMPL, CP), tp)
    for dx in (-3.5, 3.5): parent(cyl(f"Template_{i}_Pile{dx:+.0f}", 0.6, (x + dx, y, -26.0), (x + dx, y, 0.5), M_PILE, CP, seg_n=12), tp)
    TEMPLATES.append(tp)
# arrows: buoyancy (gold, up) on the front columns, tendon pull (cyan, down)
UP_ARROWS = [arrow(f"Buoy_{i}", M_GLOW_G, 14.0, 0.5) for i in range(2)]
DN_ARROWS = [arrow(f"Pull_{i}", M_GLOW_C, 14.0, 0.5) for i in range(2)]
for a in UP_ARROWS: a.rotation_euler = (0, -math.pi / 2, 0)
for a in DN_ARROWS: a.rotation_euler = (0, math.pi / 2, 0)
LEVEL_LINE = box("LevelLine", -30.0, 30.0, -0.2, 0.2, -0.2, 0.2, M_GLOW_G, CP)
# depth bracket (fixed platforms work to ~1,500 ft): gold bar + ticks at x = -34
BRACKET = empty("DepthBracket", CP)
for p in (box("Br_Bar", -0.4, 0.4, -0.4, 0.4, 0.0, D, M_GLOW_G, CP), box("Br_T0", -3.0, 3.0, -0.4, 0.4, -0.4, 0.4, M_GLOW_G, CP),
          box("Br_T1", -3.0, 3.0, -0.4, 0.4, D - 0.4, D + 0.4, M_GLOW_G, CP)): parent(p, BRACKET)
BRACKET.location = (-36.0, -1.0, 0.0)

# ---------- particles: weld sparks, splash, mud, wave streaks ----------
def blob(name, r, mat, sub=1):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); return mesh_obj(name, bm, mat, CP)
SPARKS = []
for i in range(36):
    o = blob(f"Spark_{i}", 0.55, M_SPARK); o["glow"] = 1.0
    lv = random.choice(LEVELS[:-1]); sx, sy = random.choice((-1, 1)), random.choice((-1, 1))
    o["p"] = tuple(leg(sx, sy, lv)); o["t"] = random.uniform(0.0, 1.0); SPARKS.append(o)
SPLASH = []
for i in range(80):
    o = blob(f"Splash_{i}", random.uniform(0.5, 1.1), M_SPRAY); o["glow"] = 1.0
    o["x"] = random.uniform(-20.0, 16.0); o["y"] = random.uniform(-1.0, 26.0); o["vx"] = random.uniform(-6, 6); o["vz"] = random.uniform(9, 22)
    o["dt"] = random.uniform(0.0, 0.35); SPLASH.append(o)
MUD = []
for i in range(48):
    o = blob(f"Mud_{i}", random.uniform(1.0, 2.2), M_MUD)
    sx, sy = random.choice((-1, 1)), random.choice((-1, 1)); a = random.uniform(0, 2 * math.pi)
    o["x"], o["y"] = sx * B0, JY + sy * B0; o["ax"], o["ay"] = math.cos(a), math.sin(a); o["sp"] = random.uniform(4, 9); MUD.append(o)
STREAKS = []
for i in range(30):
    o = box(f"Streak_{i}", -3.0, 3.0, -0.12, 0.12, -0.12, 0.12, M_STREAK, CP); o["glow"] = 1.0
    o["y"] = random.uniform(1.0, 24.0); o["z"] = random.uniform(D - 22.0, D - 1.5); o["ph"] = random.random(); STREAKS.append(o)

def setvis(o, fr, hidden):
    for x in [o] + list(o.children_recursive):
        rec(x, "hide_render", -1, fr, hidden); rec(x, "hide_viewport", -1, fr, hidden)
def setloc(o, fr, v):
    for i in range(3): rec(o, "location", i, fr, v[i])
def setscale(o, fr, v):
    for i in range(3): rec(o, "scale", i, fr, v[i])
def setglow(o, fr, g):
    for x in [o] + list(o.children_recursive):
        if x.type in ("MESH", "CURVE"): rec(x, '["glow"]', -1, fr, g)

def setrot(o, fr, v):
    for i in range(3): rec(o, "rotation_euler", i, fr, v[i])
def R_y(th, p):
    c, s = math.cos(th), math.sin(th); return Vector((p[0] * c + p[2] * s, p[1], -p[0] * s + p[2] * c))

# ---------- timing ----------
T_FLIP0, T_FLIP1 = C["flipped"] - 0.05, C["sea"] if "sea" in C else C["upright"] + 0.95
T_CUT0, T_CUT1 = C["cut"] - 0.05, C["open"] + 0.15
T_YARD = C["its"] - 0.08                       # hard cut to the yard
T_SKID0, T_SKID1 = C["skidded"] - 0.15, C["towed"] - 0.05
T_TOW0, T_TOW1 = C["towed"] - 0.05, C["at"] - 0.05
T_SITE = C["at"] - 0.05                        # hard cut to the site
T_TIP0, T_TIP1 = C["tips"] - 0.1, C["splash"] - 0.25
T_SPLASH = C["splash"] - 0.2
T_FLOAT = C["splash"] + 0.55
T_FLOOD0, T_FLOOD1 = C["flood"] - 0.1, C["heavy"] - 0.1
T_SINK0, T_SWING0, T_UP1 = C["heavy"] - 0.1, C["swings"] - 0.15, C["upright2"] + 0.6
T_SET0, T_SET1 = C["settles"] - 0.1, C["seabed"] + 0.25
T_PILE0, T_PILE1 = C["slide"] - 0.1, C["sleeves"] + 0.7
T_HAM_IN = C["hammer"] - 0.3
BLOWS = [C["drives"] + 0.05 + k * (C["seabed2"] + 0.35 - C["drives"]) / 8 for k in range(9)]
T_HAM_OUT = C["then2"] - 0.1
T_GROUT0, T_GROUT1 = C["fills"] - 0.05, C["locks"] + 0.2
T_SHIP_IN0, T_SHIP_IN1 = C["only"] - 0.2, C["crane"] + 0.1
T_LIFT0, T_LIFT1 = C["lift"] - 0.05, C["lift"] + 0.5
T_SWG0, T_SWG1 = C["lift"] + 0.35, C["deck"] + 0.55
T_LOW0, T_LOW1 = C["deck"] + 0.45, C["high"] + 0.1
T_WAVE0, T_WAVE1 = C["open2"] - 0.2, C["fixed"] - 0.1
T_BR0, T_BR1 = C["fixed"] - 0.05, C["deeper"] - 0.1
T_DEEP = C["deeper"] - 0.05
T_DROP0, T_DROP1 = C["deeper"] + 0.05, C["many"] + 0.3
T_TLP0, T_TLP1 = C["many"] - 0.2, C["float"] + 0.2
T_TEN0, T_TEN1 = C["tendons"] - 0.2, C["seabed3"] + 0.2
T_TEMPL = C["anchored"] - 0.1
T_PULL = C["pull"] - 0.05
T_RISE = C["harder"] - 0.05
T_BARELY = C["barely"] - 0.1

# barge positions (origin at the waterline, x = centre)
BX_YARD = XQ + 0.5 + BL / 2
BX_SITE = 14.0 + BL / 2
Z_LY_BARGE = D + Z_BD + XR + 1.8          # jacket origin height when lying on the barge skids
Z_LY_QUAY = Z_Q + 0.6 + XR + 1.8
BASE_ON_BARGE = lambda bx: bx - BL / 2 + 2.0
Z_FLOAT = D - 3.0
FLOAT_BASE_X = -H

def jacket_pose(t):
    """(location, theta about y, visible). theta = 90 deg: lying, top toward +x; 0: upright."""
    up = (Vector((0.0, JY, 0.0)), 0.0)
    if t < T_FLIP0:
        return Vector((BASE_ON_BARGE(BX_SITE), JY, Z_LY_BARGE)), math.pi / 2
    if t < T_YARD:
        p = ease((t - T_FLIP0) / (T_FLIP1 - T_FLIP0))
        th = math.pi / 2 * (1 - p)
        a = Vector((BASE_ON_BARGE(BX_SITE), JY, Z_LY_BARGE)); top0 = a + R_y(math.pi / 2, (0, 0, H)); top1 = Vector((0, JY, H))
        top = top0.lerp(top1, out3(p)); return top - R_y(th, (0, 0, H)), th
    if t < T_SKID0:
        return Vector((-172.0, JY, Z_LY_QUAY)), math.pi / 2
    if t < T_TOW0:
        x = seg(t, T_SKID0, T_SKID1, -172.0, BASE_ON_BARGE(BX_YARD)); z = seg(t, T_SKID0, T_SKID1, Z_LY_QUAY, Z_LY_BARGE)
        return Vector((x, JY, z)), math.pi / 2
    if t < T_SITE:
        bx = seg(t, T_TOW0, T_TOW1, BX_YARD, BX_YARD + 22.0, lin)
        return Vector((BASE_ON_BARGE(bx), JY, Z_LY_BARGE + barge_bob(t))), math.pi / 2
    if t < T_TIP0:
        return Vector((BASE_ON_BARGE(BX_SITE), JY, Z_LY_BARGE + barge_bob(t))), math.pi / 2
    # launch: slide base-first off the stern; tilt about the stern rocker once past the centre
    Pc = Vector((BX_SITE - BL / 2, JY, D + Z_BD))
    s_end, phi_end = 60.0, math.radians(26)
    def tip_pose(s):
        phi = phi_end * ease((s - 26.0) / (s_end - 26.0)); th = math.pi / 2 - phi
        u = Pc.x - BASE_ON_BARGE(BX_SITE) + s
        return Pc - R_y(th, (XR + 0.6, 0.0, u)), th
    if t < T_TIP1:
        s = seg(t, T_TIP0, T_TIP1, 0.0, s_end, lambda p: max(0.0, min(1.0, p)) ** 1.6)
        return tip_pose(s)
    float_loc = Vector((FLOAT_BASE_X, JY, Z_FLOAT))
    if t < T_FLOAT:
        l0, th0 = tip_pose(s_end); p = ease((t - T_TIP1) / (T_FLOAT - T_TIP1))
        loc = l0.lerp(float_loc, out3(p)); loc.z -= 7.0 * math.sin(math.pi * min(1.0, p * 1.15))
        return loc, th0 + (math.pi / 2 - th0) * out3(p)
    if t < T_SINK0:
        return float_loc + Vector((0, 0, 0.5 * math.sin((t - T_FLOAT) * 2.2))), math.pi / 2
    if t < T_SET0:
        th = math.pi / 2 - math.radians(32) * ease((t - T_SINK0) / (T_SWING0 - T_SINK0))
        if t >= T_SWING0: th = (math.pi / 2 - math.radians(32)) * (1 - ease((t - T_SWING0) / (T_UP1 - T_SWING0)))
        q = 1 - th / (math.pi / 2)
        top = Vector((0.0, JY, Z_FLOAT + (H - 2.0 - Z_FLOAT) * q))
        return top - R_y(th, (0, 0, H)), th
    if t < T_DEEP:
        return Vector((0.0, JY, seg(t, T_SET0, T_SET1, 2.0, 0.0))), 0.0
    return up
def barge_bob(t): return 0.35 * math.sin(t * 1.7)
def barge_pos(t):
    """(x, z offset, pitch, visible)"""
    if t < T_CUT1 + 0.6: return BX_SITE, barge_bob(t), 0.0, True
    if t < T_YARD: return BX_SITE, 0.0, 0.0, False
    if t < T_TOW0: return BX_YARD, barge_bob(t), 0.0, True
    if t < T_SITE: return seg(t, T_TOW0, T_TOW1, BX_YARD, BX_YARD + 22.0, lin), barge_bob(t), 0.0, True
    if t < T_TIP1 + 0.3:
        pitch = math.radians(2.5) * ease((t - T_TIP0) / (T_TIP1 - T_TIP0)) if t > T_TIP0 else 0.0
        return BX_SITE, barge_bob(t), -pitch, True
    if t < C["heavy"]: return BX_SITE + 40.0 * ease((t - (T_TIP1 + 0.3)) / 4.5), barge_bob(t) + 0.8 * math.exp(-(t - T_TIP1)), 0.0, True
    return BX_SITE + 200.0, 0.0, 0.0, False

events = {"weld": [], "skid": [round(T_SKID0, 3)], "tow": [round(T_TOW0, 3)], "launch": [round(T_TIP0, 3)], "splash": [round(T_SPLASH, 3)],
          "flood": [round(T_FLOOD0, 3)], "upend": [round(T_SINK0, 3), round(T_SWING0, 3)], "settle": [round(T_SET1 - 0.2, 3)],
          "pile_slide": [round(T_PILE0, 3)], "hammer_in": [round(T_HAM_IN + 0.3, 3)], "blow": [round(b, 3) for b in BLOWS[:8]],
          "grout": [round(T_GROUT0, 3)], "ship_in": [round(T_SHIP_IN0, 3)], "lift": [round(T_LIFT0, 3)], "deck_land": [round(T_LOW1 - 0.05, 3)],
          "cut": [round(T_CUT0, 3), round(T_YARD, 3), round(T_SITE, 3), round(T_DEEP, 3)], "drop": [round(T_DROP0, 3)],
          "tendon": [round(T_TEN0, 3)], "template": [round(T_TEMPL, 3)], "pull": [round(T_PULL, 3)]}

WELD_T0, WELD_T1 = C["welded"] - 0.1, C["flat"] + 0.3
for sp in SPARKS:
    sp["tw"] = WELD_T0 + sp["t"] * (WELD_T1 - WELD_T0 - 0.3)
events["weld"] = sorted(set(round(sp["tw"], 1) for sp in SPARKS))[::3]

for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS
    # sea near half: drops on "cut"
    setvis(SEA_F, fr, t >= T_CUT1 + 0.05); setvis(SEABED_F, fr, t >= T_CUT1 + 0.05)
    dz = -170.0 * ease((t - T_CUT0) / (T_CUT1 - T_CUT0)) if t >= T_CUT0 else 0.0
    rec(SEA_F, "location", 2, fr, D + dz); rec(SEABED_F, "location", 2, fr, dz)
    # waves
    wh = 0.6
    if T_WAVE0 <= t < T_WAVE1: wh = seg(t, T_WAVE0, T_WAVE0 + 0.6, 0.6, 2.2) if t < T_WAVE1 - 0.6 else seg(t, T_WAVE1 - 0.6, T_WAVE1, 2.2, 0.8)
    if t >= T_BARELY: wh = seg(t, T_BARELY, T_BARELY + 0.5, 0.8, 2.6) if t < C["would"] else seg(t, C["would"], C["would"] + 1.0, 2.6, 1.0)
    rec(SURF, 'modifiers["wave"].height', -1, fr, wh)
    # jacket
    loc, th = jacket_pose(t); jvis = t < T_DEEP and not (T_CUT1 + 0.6 <= t < T_YARD and False)
    setvis(JK, fr, not jvis); setloc(JK, fr, loc); setrot(JK, fr, (0.0, th, 0.0))
    rec(JLAT, '["glow"]', -1, fr, pulse(t, C["tubes"] - 0.3, 1.2, 0.9) + pulse(t, C["frame"] - 0.1, 1.4, 0.9) + pulse(t, C["jacket"] - 0.05, 0.9, 0.6))
    for o in FLOODS:
        on = T_FLOOD0 <= t < T_SET1
        setvis(o, fr, not on)
        if on: rec(o, "scale", 2, fr, max(0.02, seg(t, T_FLOOD0, T_FLOOD1, 0.0, 1.0)))
        rec(o, '["glow"]', -1, fr, 1.0 if t < T_SET0 else seg(t, T_SET0, T_SET1, 1.0, 0.0))
    for o in CAPS:
        g = pulse(t, C["sealed"] - 0.05, C["floats"] - C["sealed"] + 0.2, 1.0)
        setvis(o, fr, g < 0.01); rec(o, '["glow"]', -1, fr, g)
    for o in SLEEVES.values(): rec(o, '["glow"]', -1, fr, pulse(t, C["sleeves"] - 0.05, 0.9, 0.9))
    # barge + tug + tow line
    bx, bz, bp, bvis = barge_pos(t)
    setvis(BARGE, fr, not bvis); setloc(BARGE, fr, (bx, 0.0, D + bz)); setrot(BARGE, fr, (0.0, bp, 0.0))
    rocker = math.radians(26) * ease((t - (T_TIP0 + 0.9)) / (T_TIP1 - T_TIP0 - 0.9)) if T_TIP0 + 0.9 < t < C["heavy"] else 0.0
    setrot(ROCKER, fr, (0.0, -rocker, 0.0))
    tvis = bvis and t >= T_TOW0 - 0.6
    tx = bx + BL / 2 + 34.0
    setvis(TUG, fr, not tvis); setloc(TUG, fr, (tx, 0.0, D + 0.2 * math.sin(t * 2.1 + 1)))
    setvis(TOWLINE, fr, not tvis)
    if tvis:
        a, b_ = Vector((bx + BL / 2, JY, D + 3.0)), Vector((tx - 9.0, JY, D + 2.0))
        setloc(TOWLINE, fr, a); rec(TOWLINE, "scale", 0, fr, (b_ - a).length); setrot(TOWLINE, fr, (0.0, -math.atan2(b_.z - a.z, b_.x - a.x), 0.0))
    # weld sparks (yard)
    for sp in SPARKS:
        on = T_YARD <= t < T_SKID0 and sp["tw"] <= t < sp["tw"] + 0.35
        setvis(sp, fr, not on)
        if on:
            lp = Vector(sp["p"]); jl, jt = jacket_pose(t); w = jl + R_y(jt, lp)
            setloc(sp, fr, (w.x, w.y - 1.2, w.z)); s_ = 0.6 + 0.6 * math.sin((t - sp["tw"]) * 40) ** 2; setscale(sp, fr, (s_, s_, s_))
    # splash
    for o in SPLASH:
        tt = t - T_SPLASH - o["dt"]
        on = 0.0 <= tt < 1.6 and T_SITE <= t < T_FLOOD0
        z = D + o["vz"] * tt - 9.81 * tt * tt
        if z < D - 0.5: on = False
        setvis(o, fr, not on)
        if on: setloc(o, fr, (o["x"] + o["vx"] * tt, o["y"], z)); s_ = max(0.05, 1.0 - tt / 1.6); setscale(o, fr, (s_, s_, s_))
    # mud puff on landing
    T_M = T_SET1 - 0.3
    for o in MUD:
        tt = t - T_M; on = 0.0 <= tt < 2.6 and t < T_DEEP
        setvis(o, fr, not on)
        if on:
            r_ = o["sp"] * out3(tt / 2.6) + 1.0
            setloc(o, fr, (o["x"] + o["ax"] * r_, max(0.5, o["y"] + o["ay"] * r_), 0.8 + 2.5 * out3(tt / 2.6)))
            s_ = max(0.05, 1.2 * (1 - tt / 2.6)); setscale(o, fr, (s_, s_, s_))
    # piles + hammers
    for key, o in PILES.items():
        on = T_PILE0 <= t < T_DEEP
        setvis(o, fr, not on)
        if not on: continue
        if t < T_PILE1: z = seg(t, T_PILE0, T_PILE1, Z_PILE_REST + 60.0, Z_PILE_REST, out3)
        else:
            k = sum(1 for b in BLOWS[:8] if t >= b); z = Z_PILE_REST + (Z_PILE_DRIVEN - Z_PILE_REST) * k / 8
            if k < 8 and t >= BLOWS[0]:
                b = BLOWS[k]; z += (Z_PILE_DRIVEN - Z_PILE_REST) / 8 * ease((t - (b - 0.08)) / 0.08) if t > b - 0.08 else 0.0
        rec(o, "location", 2, fr, z)
        rec(o, '["glow"]', -1, fr, pulse(t, C["piles"] - 0.05, 0.8, 0.8) + pulse(t, C["deep"] - 0.05, 0.9, 0.7))
    for hm, key in HAMMERS:
        on = T_HAM_IN <= t < T_HAM_OUT + 0.6
        setvis(hm, fr, not on)
        if not on: continue
        pz = PILES[key].location.z
        k = sum(1 for b in BLOWS[:8] if t >= b); pz = Z_PILE_REST + (Z_PILE_DRIVEN - Z_PILE_REST) * k / 8
        top = pz + PILE_L
        lift = 0.0
        if BLOWS[0] - 0.2 <= t < BLOWS[7] + 0.2:
            ph = min(abs(t - b) for b in BLOWS[:8]); lift = 1.6 * min(1.0, ph / 0.12)
        z = top + lift
        if t < T_HAM_IN + 0.3: z = seg(t, T_HAM_IN, T_HAM_IN + 0.3, top + 30.0, top, out3)
        if t >= T_HAM_OUT: z = seg(t, T_HAM_OUT, T_HAM_OUT + 0.6, top, top + 40.0)
        setloc(hm, fr, (key[0] * SLV, JY + key[1] * B0, z))
    for g in GROUTS:
        on = T_GROUT0 <= t < T_DEEP
        setvis(g, fr, not on)
        if on: rec(g, "scale", 2, fr, max(0.02, seg(t, T_GROUT0, T_GROUT1, 0.0, 1.0, lin)))
        rec(g, '["glow"]', -1, fr, 0.7 * pulse(t, C["locks"] - 0.05, 0.9, 1.0) + (0.5 if T_GROUT0 <= t < T_GROUT1 else 0.0))
    # crane ship + deck
    svis = T_SHIP_IN0 <= t < T_WAVE1 + 0.0
    sx_ = seg(t, T_SHIP_IN0, T_SHIP_IN1, SHIP_POS.x + 60.0, SHIP_POS.x, out3)
    setvis(SHIP, fr, not svis); setloc(SHIP, fr, (sx_, SHIP_POS.y, SHIP_POS.z + 0.25 * math.sin(t * 1.3)))
    psi = seg(t, T_SWG0, T_SWG1, 0.0, math.pi)
    rec(BOOM, "rotation_euler", 2, fr, psi)
    piv = Vector((sx_, SHIP_POS.y, SHIP_POS.z + 12.0))
    tip = piv + BOOM_L * Vector((math.cos(BOOM_EL) * math.cos(psi), math.cos(BOOM_EL) * math.sin(psi), math.sin(BOOM_EL)))
    Z_DK_SHIP, Z_DK_AIR, Z_DK_TOP = SHIP_POS.z + 5.3, D + 32.0, H + 2.0
    if t < T_LIFT0: dz_ = Z_DK_SHIP
    elif t < T_LOW0: dz_ = seg(t, T_LIFT0, T_LIFT1, Z_DK_SHIP, Z_DK_AIR)
    else: dz_ = seg(t, T_LOW0, T_LOW1, Z_DK_AIR, Z_DK_TOP)
    dvis = T_SHIP_IN0 <= t < T_DEEP
    dpos = Vector((tip.x, tip.y, dz_)) if t < T_LOW1 else Vector((0.0, JY, Z_DK_TOP))
    setvis(DECK, fr, not dvis); setloc(DECK, fr, dpos)
    cvis = svis and t < T_LOW1 + 0.4
    setvis(CABLE, fr, not cvis)
    if cvis:
        hook = dpos + Vector((0, 0, 24.0)); setloc(CABLE, fr, tip); rec(CABLE, "scale", 2, fr, max(0.1, tip.z - hook.z))
    # wave streaks (through the open frame)
    for o in STREAKS:
        on = T_WAVE0 <= t < T_WAVE1
        x = -60.0 + ((t * 22.0 + o["ph"] * 120.0) % 120.0)
        setvis(o, fr, not on)
        if on: setloc(o, fr, (x, o["y"], o["z"] + wh * 0.6 * math.sin(x / 9.0 - t * 2.0)))
    # depth bracket
    bon = T_BR0 <= t < T_BR1
    setvis(BRACKET, fr, not bon)
    if bon: rec(BRACKET, "scale", 2, fr, max(0.02, seg(t, T_BR0, T_BR0 + 0.6, 0.0, 1.0, out3)))
    # deep water: seabed drops, TLP
    rec(SEABED, "location", 2, fr, seg(t, T_DROP0, T_DROP1, 0.0, Z_SB_DEEP) if t >= T_DROP0 else 0.0)
    tlv = t >= T_TLP0
    setvis(TLP, fr, not tlv)
    bob = 0.0
    if tlv:
        amp = 1.6 if t < T_PULL else seg(t, T_PULL, T_PULL + 0.6, 1.6, 0.08)
        bob = amp * math.sin((t - T_TLP0) * 1.6)
        zin = seg(t, T_TLP0, T_TLP1, 26.0, 0.0, out3)
        setloc(TLP, fr, (0.0, 0.0, zin + bob))
        rec(TLP.children[0], '["glow"]', -1, fr, 0.0)
    for o in TLP.children_recursive:
        if o.type == "MESH" and o.name.startswith("TLP_"): rec(o, '["glow"]', -1, fr, pulse(t, C["hull"] - 0.05, 0.9, 0.8) + pulse(t, C["float"] - 0.05, 0.8, 0.6))
    for o in TENDONS:
        on = t >= T_TEN0
        setvis(o, fr, not on)
        full = (Z_HB + bob) - (Z_SB_DEEP + 3.0)
        if on:
            rec(o, "location", 2, fr, Z_HB + bob)
            rec(o, "scale", 2, fr, max(0.1, seg(t, T_TEN0, T_TEN1, 1.0, full)))
        rec(o, '["glow"]', -1, fr, pulse(t, C["tendons"] - 0.05, 1.0, 0.7) + (0.25 + 0.15 * math.sin(t * 6) if T_PULL <= t < C["would"] else 0.0) + pulse(t, C["pull"] - 0.05, 1.2, 0.6))
    for tp in TEMPLATES:
        on = t >= T_TEMPL
        setvis(tp, fr, not on)
        if on: setloc(tp, fr, (0.0, 0.0, Z_SB_DEEP + seg(t, T_TEMPL, T_TEMPL + 0.4, 20.0, 0.0, out3)))
    for i, a in enumerate(UP_ARROWS):
        on = T_RISE <= t < C["would"]
        setvis(a, fr, not on)
        if on:
            x = TL_COL[i * 2][0] if False else (-14.0 if i == 0 else 14.0)
            setloc(a, fr, (x, -2.0 - 5.6, Z_HB - 2.0 + bob)); rec(a, "scale", 0, fr, max(0.02, seg(t, T_RISE, T_RISE + 0.4, 0.0, 1.0, out3)))
            rec(a, '["glow"]', -1, fr, 0.9 + 0.1 * math.sin(t * 8))
    for i, a in enumerate(DN_ARROWS):
        on = T_PULL <= t < C["would"]
        setvis(a, fr, not on)
        if on:
            x = -14.0 if i == 0 else 14.0
            setloc(a, fr, (x - 6.5, -2.0 - 5.6, Z_HB - 4.0 + bob)); rec(a, "scale", 0, fr, max(0.02, seg(t, T_PULL, T_PULL + 0.4, 0.0, 1.0, out3)))
            rec(a, '["glow"]', -1, fr, 0.9 + 0.1 * math.sin(t * 8 + 1))
    lon = T_BARELY <= t < C["would"]
    setvis(LEVEL_LINE, fr, not lon)
    if lon: setloc(LEVEL_LINE, fr, (0.0, -8.0, Z_HT + bob)); rec(LEVEL_LINE, '["glow"]', -1, fr, 0.8)
write_tracks(); TRACKS.clear()

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 30
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tcn = cam.constraints.new("TRACK_TO"); tcn.target = TGT; tcn.track_axis = "TRACK_NEGATIVE_Z"; tcn.up_axis = "UP_Y"
cam_d.clip_end = 5000
WIDE = ((-4.0, -112.0, 38.0), (-2.0, 12.0, 30.0), 30)
SHOTS = [  # (time, camera loc, target, lens); consecutive equal times = hard cut
    (0.0, (8.0, -62.0, D + 42.0), (46.0, 12.0, D + 12.0), 30),
    (C["flipped"] - 0.1, (2.0, -70.0, D + 40.0), (38.0, 12.0, D + 10.0), 30),
    (C["upright"] + 0.9, (-6.0, -88.0, D + 36.0), (6.0, 12.0, D - 2.0), 30),
    (C["cut"] - 0.1, (-8.0, -95.0, D + 30.0), (2.0, 12.0, D - 6.0), 30),
    (C["open"] + 0.6, WIDE[0], WIDE[1], 30),
    (C["tower"], (-2.0, -100.0, 36.0), (0.0, 12.0, 32.0), 30),
    (C["jacket"] + 0.6, (6.0, -86.0, 40.0), (0.0, 12.0, 34.0), 30),
    (T_YARD - 0.02, (8.0, -84.0, 40.0), (0.0, 12.0, 34.0), 30),
    (T_YARD, (-214.0, -52.0, Z_Q + 34.0), (-134.0, 12.0, Z_Q + 12.0), 30),
    (C["flat"], (-208.0, -58.0, Z_Q + 32.0), (-128.0, 12.0, Z_Q + 12.0), 30),
    (T_SKID0, (-200.0, -64.0, Z_Q + 32.0), (-118.0, 12.0, Z_Q + 12.0), 30),
    (T_SKID1, (-90.0, -84.0, Z_Q + 26.0), (-60.0, 12.0, D + 8.0), 30),
    (T_SITE - 0.02, (-70.0, -86.0, Z_Q + 24.0), (-36.0, 12.0, D + 8.0), 30),
    (T_SITE, (-10.0, -96.0, D + 16.0), (26.0, 12.0, D + 4.0), 30),
    (T_TIP0, (-14.0, -98.0, D + 14.0), (18.0, 12.0, D + 2.0), 30),
    (T_FLOAT, (-40.0, -98.0, D + 10.0), (-24.0, 12.0, D - 4.0), 30),
    (C["sealed"], (-64.0, -66.0, D + 6.0), (-54.0, 12.0, D - 4.0), 30),
    (C["air"] + 0.2, (-60.0, -68.0, D + 6.0), (-50.0, 12.0, D - 4.0), 30),
    (C["floats"] + 0.3, (-36.0, -74.0, D + 4.0), (-30.0, 12.0, D - 5.0), 30),
    (C["flood"], (-52.0, -64.0, D - 4.0), (-44.0, 12.0, D - 6.0), 30),
    (T_SINK0, (-34.0, -112.0, 30.0), (-22.0, 12.0, 30.0), 30),
    (T_UP1, (-6.0, -112.0, 34.0), (-2.0, 12.0, 30.0), 30),
    (C["seabed"], (-4.0, -84.0, 14.0), (0.0, 12.0, 8.0), 30),
    (C["mud"] + 0.2, (-10.0, -70.0, 10.0), (-4.0, 12.0, 4.0), 30),
    (C["slide"], (-10.0, -84.0, 18.0), (-4.0, 12.0, 6.0), 30),
    (C["hammer"], (-16.0, -86.0, 6.0), (-6.0, 12.0, -2.0), 30),
    (C["seabed2"] + 0.4, (-14.0, -82.0, 0.0), (-6.0, 12.0, -10.0), 30),
    (C["grout"] - 0.1, (-16.0, -17.0, 6.0), (-14.4, 0.5, 3.6), 35),
    (C["locks"] + 0.4, (-15.6, -15.0, 5.5), (-14.4, 0.5, 3.6), 35),
    (C["only"] - 0.25, (-16.0, -17.0, 6.0), (-14.4, 0.5, 3.6), 35),
    (C["only"] - 0.2, (20.0, -150.0, 66.0), (26.0, 12.0, 58.0), 30),
    (C["lift"], (16.0, -150.0, 70.0), (24.0, 12.0, 64.0), 30),
    (C["deck"] + 0.4, (6.0, -140.0, 70.0), (6.0, 12.0, 64.0), 30),
    (C["waves"], (-4.0, -122.0, 64.0), (0.0, 12.0, 58.0), 30),
    (T_WAVE0, (-24.0, -66.0, D + 4.0), (-2.0, 12.0, D - 8.0), 28),
    (T_WAVE1 - 0.2, (-14.0, -70.0, D + 2.0), (2.0, 12.0, D - 8.0), 28),
    (T_BR0, (-12.0, -128.0, 44.0), (-8.0, 12.0, 38.0), 30),
    (T_DEEP - 0.02, (-10.0, -124.0, 44.0), (-8.0, 12.0, 38.0), 30),
    (T_DEEP, (-10.0, -124.0, 44.0), (-8.0, 12.0, 38.0), 30),
    (T_DROP1, (-6.0, -178.0, 10.0), (0.0, 12.0, -6.0), 30),
    (C["float"] + 0.3, (-6.0, -172.0, 8.0), (0.0, 12.0, -12.0), 30),
    (T_TEN1, (-4.0, -176.0, -16.0), (0.0, 12.0, -42.0), 30),
    (T_PULL - 0.1, (-8.0, -100.0, D + 2.0), (0.0, 12.0, D - 16.0), 30),
    (C["barely"], (-4.0, -96.0, D + 4.0), (0.0, 12.0, D - 12.0), 30),
    (C["would"], (-40.0, -150.0, D + 30.0), (0.0, 12.0, D - 18.0), 30),
    (C["next"], (10.0, -156.0, D + 26.0), (0.0, 12.0, D - 18.0), 30),
    (C["end_t"], (46.0, -146.0, D + 24.0), (0.0, 12.0, D - 18.0), 30),
]
prev = None
for t, loc, tgt, lens in SHOTS:
    fr = F(t)
    if prev is not None and fr <= prev: fr = prev + 1       # hard cut: next frame
    setloc(cam, fr, loc); setloc(TGT, fr, tgt); rec(cam_d, "lens", -1, fr, lens); prev = fr
write_tracks("BEZIER")
# ---------- world + light: daylight sky, sun from camera-left front ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND")
try:
    sky = wn.new("ShaderNodeTexSky")
    for st_ in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try: sky.sky_type = st_; break
        except Exception: continue
    try: sky.sun_elevation = math.radians(38); sky.sun_rotation = math.radians(200)
    except Exception: pass
    wl.new(sky.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.22
except Exception:
    bg.inputs["Color"].default_value = (0.45, 0.62, 0.85, 1); bg.inputs["Strength"].default_value = 0.8
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 2.6; sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(48), math.radians(-30), math.radians(-25))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 60; fill_d.energy = 9000; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill); parent(fill, cam); fill.location = (14, 18, 0)

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
scene.cycles.max_bounces = 10; scene.cycles.transmission_bounces = 8; scene.cycles.volume_bounces = 1
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = False
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass


# ---------- export cues, mechanical events and projected anchors for the typography ----------
ANCH = {"jacket": (JK, Vector((-9.0, -9.0, 18.0))), "leg_end": (JK, leg(-1, -1, -1.2)), "flood": (JK, leg(-1, -1, 14.0)),
        "barge": (BARGE, Vector((-10.0, JY - BW / 2, 3.4))), "quay": (None, Vector((-140.0, -30.0, Z_Q))),
        "seabed": (None, Vector((-34.0, 0.0, 0.0))), "mud": (None, Vector((-24.0, 0.0, 0.0))),
        "sleeve": (None, Vector((-SLV, 0.0, 7.0))), "pile": (None, Vector((-SLV, 0.0, -24.0))), "grout": (None, Vector((-SLV, 0.0, 4.0))),
        "hammer": (HAMMERS[0][0], Vector((0.0, 0.0, 6.0))), "deck": (DECK, Vector((-16.0, -16.0, 9.0))),
        "ship": (SHIP, Vector((4.0, -16.0, 6.0))), "tendon": (None, Vector((-16.2, -2.0, -40.0))),
        "hull": (TLP, Vector((-14.0, -7.0, D - 6.0))), "template": (None, Vector((-14.0, -6.0, Z_SB_DEEP + 14.0))),
        "jacket_top": (JK, Vector((-6.0, -6.0, H)))}
if not os.environ.get("COVER"):   # build_cover.py re-uses this scene and skips the export
    anchors = {k: [] for k in ANCH}
    for fr in range(1, FRAMES + 1):
        scene.frame_set(fr)
        for k, (ob, local) in ANCH.items():
            w = local if ob is None else ob.matrix_world @ local
            p = world_to_camera_view(scene, cam, w)
            anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)])
    json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "events": events, "anchors": anchors},
              open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("EVENTS", {k: (len(v) if isinstance(v, list) else v) for k, v in events.items()}, "DUR", DUR, "FRAMES", FRAMES)

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
    scene.frame_start = int(arg("--start", "1"))  # resume an interrupted final render
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
