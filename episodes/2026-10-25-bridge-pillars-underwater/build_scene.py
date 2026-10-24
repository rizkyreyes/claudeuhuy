# Bridge-Pillar-Cofferdam-3D: river cross-section, Blender Cycles. Every cue is a word in the voice-over.
# Sheets, frame, mud, piles, tremie seal, water level and pillar are baked frame by frame from one state timeline.
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
#   (or with the PyPI bpy module: python build_scene.py -- ...)
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
random.seed(5)

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
for name, word in [("how", "how"), ("pillar", "pillar"), ("river", "river"), ("leave", "leave"), ("lets", "let's"), ("open", "open"),
                   ("first", "first"), ("frame", "frame"), ("place", "place"), ("around", "around"), ("sheets", "sheets"),
                   ("corners", "corners"), ("edges", "edges"), ("lock", "lock"), ("vibrating", "vibrating"), ("hammer", "hammer"),
                   ("drives", "drives"), ("riverbed", "riverbed"), ("this", "this"), ("box", "box"), ("cofferdam", "cofferdam"),
                   ("water", "water"), ("pushes", "pushes"), ("every", "every"), ("frame2", "frame"), ("holds", "holds"),
                   ("apart", "apart"), ("next", "next"), ("dig", "dig"), ("mud", "mud"), ("drive", "drive"), ("piles", "piles"),
                   ("ground", "ground"), ("but", "but"), ("pump", "pump"), ("dry", "dry"), ("yet", "yet"), ("water2", "water"),
                   ("push", "push"), ("below", "below"), ("so", "so"), ("pour", "pour"), ("concrete", "concrete"),
                   ("underwater", "underwater"), ("pipe", "pipe"), ("end", "end"), ("buried", "buried"), ("rises", "rises"),
                   ("up", "up"), ("this2", "this"), ("seal", "seal"), ("kentucky", "kentucky"), ("fifteen", "fifteen"),
                   ("thick", "thick"), ("weight", "weight"), ("floor", "floor"), ("down", "down"), ("once", "once"),
                   ("hardens", "hardens"), ("pumps", "pumps"), ("switch", "switch"), ("drops", "drops"), ("crew", "crew"),
                   ("stands", "stands"), ("dry2", "dry"), ("below2", "below"), ("river2", "river"), ("pour2", "pour"),
                   ("footing", "footing"), ("pillar2", "pillar"), ("rises2", "rises"), ("water3", "water"), ("then", "then"),
                   ("sheets2", "sheets"), ("pulled", "pulled"), ("river3", "river"), ("closes", "closes"), ("back", "back"),
                   ("romans", "romans"), ("two", "two"), ("rings", "rings"), ("wooden", "wooden"), ("posts", "posts"),
                   ("clay", "clay"), ("same", "same"), ("keep", "keep"), ("out", "out"), ("build", "build"), ("dry3", "dry"),
                   ("follow", "follow")]:
    C[name] = TA(word)
C["end_t"] = DUR

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
def win(t, a, b): return a <= t < b

def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CR, CS, CP = coll("River"), coll("Cofferdam"), coll("Props")

# ---------- materials (procedural: the cloud run has no texture downloads) ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
def glow_link(nt, b, rgb, k):
    """Emission strength = object custom property 'glow' * k (keyed per object)."""
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_type = "OBJECT"; at.attribute_name = "glow"
    mm = nt.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = k
    nt.links.new(at.outputs["Fac"], mm.inputs[0]); nt.links.new(mm.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Emission Color"].default_value = (*rgb, 1)
def flat(name, rgb, rough=0.5, metal=0.0, glow=None, k=3.0, noise=0.0):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 6
        nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = 1 - noise; mr.inputs[4].default_value = 1 + noise
        nt.links.new(n.outputs["Fac"], mr.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        mx.inputs[6].default_value = (*rgb, 1); cc = nt.nodes.new("ShaderNodeCombineColor")
        for i in range(3): nt.links.new(mr.outputs[0], cc.inputs[i])
        nt.links.new(cc.outputs[0], mx.inputs[7]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    if glow: glow_link(nt, b, glow, k)
    return m
def soil(name, rgb_a, rgb_b, scale, stones=0.0):
    """World-space soil: two tones mixed by noise, optional voronoi pebbles (reads well on the section face)."""
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
    b.inputs["Base Color"].default_value = (0.75, 0.92, 0.95, 1); b.inputs["Roughness"].default_value = 0.04
    b.inputs["IOR"].default_value = 1.333; b.inputs["Transmission Weight"].default_value = 1.0
    out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
    va = nt.nodes.new("ShaderNodeVolumeAbsorption"); va.inputs["Color"].default_value = (0.35, 0.62, 0.62, 1); va.inputs["Density"].default_value = 0.09
    vs = nt.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Color"].default_value = (0.55, 0.75, 0.72, 1); vs.inputs["Density"].default_value = 0.012
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(va.outputs[0], ad.inputs[0]); nt.links.new(vs.outputs[0], ad.inputs[1])
    nt.links.new(ad.outputs[0], out.inputs["Volume"])
    g = nt.nodes.new("ShaderNodeNewGeometry"); n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 0.35
    n.inputs["Detail"].default_value = 6; nt.links.new(g.outputs["Position"], n.inputs["Vector"])
    bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.12; nt.links.new(n.outputs["Fac"], bp.inputs["Height"])
    nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])          # small ripples break up mirror reflections
    return m
PH_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "pipeline3d", "assets", "polyhaven"))
PH = json.load(open(os.path.join(PH_DIR, "manifest.json"))) if os.path.exists(os.path.join(PH_DIR, "manifest.json")) else None
def ph_mat(name, side, side_size, top=None, top_size=2.0, top_hsv=(0.5, 1.0, 1.0), value=1.0):
    """World-space box-projected Poly Haven PBR: side faces = side asset, upward faces = top asset (if given)."""
    m, nt, b = new_mat(name); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry")
    def tset(asset, size):
        mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / size,) * 3; L.new(g.outputs["Position"], mp.inputs["Vector"])
        out = {}
        for mapname, k, col in (("Diffuse", "col", True), ("Rough", "rough", False), ("nor_gl", "nrm", False)):
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH_DIR, asset, PH[asset][mapname]), check_existing=True)
            if not col: t.image.colorspace_settings.name = "Non-Color"
            t.projection = "BOX"; t.projection_blend = 0.25; L.new(mp.outputs["Vector"], t.inputs["Vector"]); out[k] = t.outputs["Color"]
        return out
    sd = tset(side, side_size); col, rough, nrm = sd["col"], sd["rough"], sd["nrm"]
    if top:
        tp = tset(top, top_size)
        hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Hue"].default_value, hs.inputs["Saturation"].default_value, hs.inputs["Value"].default_value = top_hsv
        L.new(tp["col"], hs.inputs["Color"])
        sn = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Normal"], sn.inputs[0])
        up = nt.nodes.new("ShaderNodeMath"); up.operation = "GREATER_THAN"; up.inputs[1].default_value = 0.5; L.new(sn.outputs[2], up.inputs[0])
        def mix(a, c):
            mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(up.outputs[0], mx.inputs["Factor"]); L.new(a, mx.inputs[6]); L.new(c, mx.inputs[7]); return mx.outputs[2]
        col, rough, nrm = mix(col, hs.outputs["Color"]), mix(rough, tp["rough"]), mix(nrm, tp["nrm"])
    if value != 1.0:
        hv = nt.nodes.new("ShaderNodeHueSaturation"); hv.inputs["Value"].default_value = value; L.new(col, hv.inputs["Color"]); col = hv.outputs["Color"]
    L.new(col, b.inputs["Base Color"])
    bw = nt.nodes.new("ShaderNodeRGBToBW"); L.new(rough, bw.inputs[0]); L.new(bw.outputs[0], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); L.new(nrm, nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m
GOLD, CYAN, RED = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24)
M_WATER = water_mat("RiverWater")
if PH:      # laptop: real scanned textures
    M_MUD = ph_mat("SoftMud", "brown_mud_dry", 1.3, value=0.6)
    M_FIRM = ph_mat("FirmGround", "red_laterite_soil_stones", 2.0, value=0.95)
    M_GRASS = ph_mat("Bank", "excavated_soil_wall", 2.0, top="leafy_grass", top_size=2.0, top_hsv=(0.5, 1.2, 0.9))
else:       # cloud: procedural fallback
    M_MUD = soil("SoftMud", (0.12, 0.08, 0.05), (0.22, 0.15, 0.09), 1.2)
    M_FIRM = soil("FirmGround", (0.24, 0.19, 0.13), (0.36, 0.29, 0.20), 0.7, stones=0.12)
    M_GRASS = soil("Bank", (0.10, 0.18, 0.05), (0.20, 0.28, 0.08), 0.9)
print("soil materials:", "Poly Haven" if PH else "procedural")
M_SHEET = flat("SheetPile", (0.30, 0.31, 0.33), 0.45, 0.85, GOLD, 2.0, noise=0.25)
M_FRAME = flat("FrameSteel", (0.85, 0.55, 0.06), 0.4, 0.2, GOLD, 3.0)
M_PILE = flat("Pile", (0.45, 0.45, 0.46), 0.6, 0.0, GOLD, 2.0, noise=0.15)
M_PIPE = flat("TremiePipe", (0.55, 0.56, 0.58), 0.3, 1.0, GOLD, 4.0)
M_SEAL = flat("SealConcrete", (0.42, 0.43, 0.43), 0.8, 0.0, CYAN, 1.2, noise=0.2)
M_CONC = flat("Concrete", (0.55, 0.54, 0.52), 0.75, 0.0, GOLD, 1.0, noise=0.15)
M_DECK = flat("Deck", (0.5, 0.49, 0.47), 0.7, noise=0.1)
M_ASPH = flat("DeckAsphalt", (0.05, 0.05, 0.055), 0.8)
M_WOOD = flat("WoodPost", (0.36, 0.22, 0.10), 0.7, 0.0, GOLD, 1.5, noise=0.35)
M_CLAY = flat("Clay", (0.48, 0.26, 0.14), 0.9, 0.0, GOLD, 0.8, noise=0.3)
M_PUMP = flat("Pump", (0.10, 0.35, 0.65), 0.4, 0.3)
M_HOSE = flat("Hose", (0.03, 0.03, 0.03), 0.6)
M_MAN = flat("Mannequin", (0.85, 0.42, 0.10), 0.6)
M_HAT = flat("HardHat", (0.95, 0.85, 0.15), 0.35)
M_GLOW_C = flat("ArrowCyan", (0.02, 0.05, 0.06), 0.5, 0.0, CYAN, 8.0)
M_GLOW_R = flat("ArrowRed", (0.06, 0.01, 0.01), 0.5, 0.0, RED, 8.0)
M_GLOW_G = flat("ArrowGold", (0.06, 0.04, 0.0), 0.5, 0.0, GOLD, 8.0)

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
def box(name, x0, x1, y0, y1, z0, z1, mat, col=CR, pivot=None):
    pivot = pivot or (0, 0, 0)
    o = mesh_obj(name, box_bm(x0, x1, y0, y1, z0, z1, pivot), mat, col); o.location = pivot; return o
def cyl_bm(r, z0, z1, seg_n=48, cx=0.0, cy=0.0, pivot=(0, 0, 0), keep_y=None):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg_n, radius1=r, radius2=r, depth=z1 - z0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx - pivot[0], cy - pivot[1], (z0 + z1) / 2 - pivot[2]))
    if keep_y is not None: cut_keep_back(bm, keep_y - pivot[1])
    return bm
def cut_keep_back(bm, y0):
    """Keep only y >= y0 and close the cut (cross-section face)."""
    res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, y0, 0), plane_no=(0, 1, 0), clear_inner=True)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if edges: bmesh.ops.edgenet_fill(bm, edges=edges)
def cyl(name, r, z0, z1, mat, col=CR, cx=0.0, cy=0.0, pivot=None, keep_y=None, seg_n=48, smooth=True):
    pivot = pivot or (0, 0, 0)
    o = mesh_obj(name, cyl_bm(r, z0, z1, seg_n, cx, cy, pivot, keep_y), mat, col); o.location = pivot
    if smooth:
        o.data.shade_smooth()
        try: o.data.set_sharp_from_angle(angle=math.radians(40))
        except Exception: pass
    return o
def boolean(target, cutter, op="DIFFERENCE"):
    md = target.modifiers.new("b", "BOOLEAN"); md.operation = op; md.object = cutter; md.solver = "EXACT"
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
    target.modifiers.clear(); old = target.data; target.data = me; bpy.data.meshes.remove(old)
def delete(o): bpy.data.objects.remove(o, do_unlink=True)
def empty(name, col=CS):
    e = bpy.data.objects.new(name, None); col.objects.link(e); return e
def parent(child, par): child.parent = par; child.matrix_parent_inverse = Matrix.Identity(4)

# ---------- river layout (metres; section plane y = 0, camera on -y) ----------
Z_WATER, Z_BED, Z_MUD, Z_DEEP = 3.0, -2.0, -4.5, -26.0     # water surface, riverbed, bottom of soft mud, bottom of model
XR, XB, YB = 36.0, 250.0, 250.0                                # river half width, model half width, model depth
HW = 4.0                                                     # cofferdam half width (sheet line)
W_IN, W_OUT = 3.95, 4.30                                     # inner water / outer hole (the sheet band fills the gap)
Z_SEAL = -2.0                                                # top of the tremie seal (= old riverbed)
Z_FOOT = 0.0                                                 # top of the footing
Z_CAP0, Z_CAP1, Z_DECK1 = 9.0, 10.0, 11.2

def halves(name, x0, x1, z0, z1, mat, y_back=YB):
    return box(name + "_Back", x0, x1, 0, y_back, z0, z1, mat), box(name + "_Front", x0, x1, -YB, 0, z0, z1, mat)
WATER_B, WATER_F = halves("Water", -XR, XR, Z_BED, Z_WATER, M_WATER)
MUD_B, MUD_F = halves("Mud", -XR, XR, Z_MUD, Z_BED, M_MUD)
FIRM_B, FIRM_F = halves("FirmGround", -XB, XB, Z_DEEP, Z_MUD, M_FIRM)
BANKS = []
for s in (-1, 1):
    BANKS += list(halves(f"Bank{s:+d}", min(s * XR, s * XB), max(s * XR, s * XB), Z_MUD, 4.0, M_GRASS))
# after the sheets close: outer water / mud with a hole + inner water + inner mud chunks
WATER_HOLE = box("Water_Outer", -XR, XR, 0, YB, Z_BED, Z_WATER, M_WATER)
cut = box("cut", -W_OUT, W_OUT, -1, W_OUT, Z_BED - 1, Z_WATER + 1, None); boolean(WATER_HOLE, cut); delete(cut)
MUD_HOLE = box("Mud_Outer", -XR, XR, 0, YB, Z_MUD, Z_BED, M_MUD)
cut = box("cut", -W_OUT, W_OUT, -1, W_OUT, Z_MUD - 1, Z_BED + 1, None); boolean(MUD_HOLE, cut); delete(cut)
WATER_IN = box("Water_Inner", -W_IN, W_IN, 0, W_IN, Z_MUD, Z_WATER, M_WATER, CS, pivot=(0, 0, Z_MUD))
MUD_CH = [box(f"Mud_Inner_{i}", x0, x1, -0.02, W_IN, Z_MUD, Z_BED, M_MUD, CS, pivot=((x0 + x1) / 2, W_IN / 2, Z_MUD))
          for i, (x0, x1) in enumerate([(-W_IN, -2.0), (-2.0, 0.0), (0.0, 2.0), (2.0, W_IN)])]

# ---------- bridge: deck with a gap over our pier, two finished piers ----------
def pier(name, x, keep_back=True):
    o = cyl(name, 1.6, Z_MUD, Z_CAP0, M_CONC, CP, cx=x, keep_y=-0.03 if keep_back else None)
    cap = box(name + "_Cap", x - 3.2, x + 3.2, -0.03 if keep_back else -2.2, 2.2, Z_CAP0, Z_CAP1, M_CONC, CP)
    return o, cap
FAR_PIERS = []
for x in (-16.0, 16.0):
    back = list(pier(f"FarPier{x:+.0f}_Back", x))
    fr = cyl(f"FarPier{x:+.0f}_Front", 1.6, Z_MUD, Z_CAP0, M_CONC, CP, cx=x)
    cut = box("cut", x - 3, x + 3, -0.03, 3, Z_MUD - 1, Z_CAP0 + 1, None); boolean(fr, cut); delete(cut)
    frc = box(f"FarPier{x:+.0f}_CapFront", x - 3.2, x + 3.2, -2.2, -0.03, Z_CAP0, Z_CAP1, M_CONC, CP)
    FAR_PIERS.append((back, [fr, frc]))
DECK = []
for s in (-1, 1):
    x0, x1 = (-70.0, -6.0) if s < 0 else (6.0, 70.0)
    DECK.append((box(f"Deck{s:+d}_Back", x0, x1, 0, 4.0, Z_CAP1, Z_DECK1, M_DECK, CP), box(f"Deck{s:+d}_Front", x0, x1, -4.0, 0, Z_CAP1, Z_DECK1, M_DECK, CP)))
    for nm, y0, y1 in (("Back", 0, 3.6), ("Front", -3.6, 0)):
        a = box(f"Deck{s:+d}_Road{nm}", x0, x1, y0, y1, Z_DECK1, Z_DECK1 + 0.08, M_ASPH, CP); DECK[-1] += (a,)
DECK_MID = empty("DeckMid", CP)
for o in (box("DeckMid_Slab", -6.0, 6.0, 0, 4.0, Z_CAP1, Z_DECK1, M_DECK, CP), box("DeckMid_Road", -6.0, 6.0, 0, 3.6, Z_DECK1, Z_DECK1 + 0.08, M_ASPH, CP)):
    parent(o, DECK_MID)

# hook marker: gold square on the water where the new pier goes
MARK = empty("HookMarker", CP)
for i, (x0, x1, y0, y1) in enumerate([(-HW, HW, -HW - 0.12, -HW + 0.12), (-HW, HW, HW - 0.12, HW + 0.12), (-HW - 0.12, -HW + 0.12, -HW, HW), (HW - 0.12, HW + 0.12, -HW, HW)]):
    parent(box(f"Marker_{i}", x0, x1, y0, y1, Z_WATER + 0.02, Z_WATER + 0.08, M_GLOW_G, CP), MARK)

# ---------- cofferdam: steel frame (wales + corner struts) ----------
FRAME = empty("Frame")
FR_LEVELS = (1.5, 4.0)
def beam(name, p0, p1, w=0.42, h=0.5):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0; L = d.length
    o = box(name, -L / 2, L / 2, -w / 2, w / 2, -h / 2, h / 2, M_FRAME, CS)
    o.rotation_euler = (0, 0, math.atan2(d.y, d.x)); o.location = (p0 + p1) / 2; return o
WALES = []
for zl in FR_LEVELS:
    for o in (beam(f"Wale_Back_{zl}", (-3.75, 3.75, zl), (3.75, 3.75, zl)),
              beam(f"Wale_L_{zl}", (-3.75, -0.03, zl), (-3.75, 3.75, zl)), beam(f"Wale_R_{zl}", (3.75, -0.03, zl), (3.75, 3.75, zl)),
              beam(f"Strut_L_{zl}", (-3.55, 1.6, zl), (-1.6, 3.55, zl), 0.36, 0.42), beam(f"Strut_R_{zl}", (3.55, 1.6, zl), (1.6, 3.55, zl), 0.36, 0.42)):
        WALES.append(o); o.parent = FRAME
# guide posts the frame hangs on (temporary support piles)
for x in (-3.3, 3.3):
    p = cyl(f"GuidePost{x:+.1f}", 0.16, Z_MUD - 3.0, 5.2, M_FRAME, CS, cx=x, cy=3.3, seg_n=16); WALES.append(p); p.parent = FRAME

# ---------- sheet piles: corrugated panels, set from the corners, meet in the middle ----------
SW, SD, ST, SH = 0.8, 0.26, 0.05, 15.0          # sheet width, corrugation depth, steel thickness, length
Z_SHEET_SET, Z_SHEET_DRIVEN = -3.0, -10.0      # sheet bottom when set / when driven
def sheet_bm():
    prof = [(0.0, 0.0), (0.18, 0.0), (0.30, SD), (0.50, SD), (0.62, 0.0), (SW, 0.0)]
    bm = bmesh.new()
    top = [bm.verts.new((u - SW / 2, v, SH)) for u, v in prof]; bot = [bm.verts.new((u - SW / 2, v, 0.0)) for u, v in prof]
    for i in range(len(prof) - 1): bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
    return bm
SHEETS = []   # dict: obj, order key, wall, u
def add_sheet(wall, u):
    o = mesh_obj(f"Sheet_{wall}_{u:+.2f}", sheet_bm(), M_SHEET, CS)
    sd = o.modifiers.new("Solid", "SOLIDIFY"); sd.thickness = ST; sd.offset = 0.0
    if wall == "B": o.location = (u, HW, 0); o.rotation_euler = (0, 0, 0)
    elif wall == "L": o.location = (-HW, u, 0); o.rotation_euler = (0, 0, math.radians(90))
    else: o.location = (HW, u, 0); o.rotation_euler = (0, 0, math.radians(-90))
    SHEETS.append({"obj": o, "wall": wall, "u": u}); return o
for k in range(10): add_sheet("B", -HW + SW / 2 + k * SW)
for k in range(5):
    u = HW - SW / 2 - k * SW
    if k == 4: u = SW / 2 - 0.05         # the last side sheet straddles the section plane (its cut end reads on the face)
    add_sheet("L", u); add_sheet("R", u)
# local +Y (the corrugation) faces the river on every wall
# corner-first order: distance from the nearest back corner
def corner_rank(s):
    if s["wall"] == "B": return HW - abs(s["u"])
    return HW - s["u"]
ORDER = sorted(SHEETS, key=corner_rank)
T_SET0, T_SET1 = C["sheets"] - 0.2, C["corners"] + 0.55
for i, s in enumerate(ORDER):
    s["t_set"] = T_SET0 + (T_SET1 - T_SET0) * i / (len(ORDER) - 1)
T_DRV0, T_DRV1 = C["drives"] - 0.1, C["this"] - 0.15
DRIVE_ORDER = sorted(SHEETS, key=lambda s: (0 if s["wall"] == "B" else 1, s["u"] if s["wall"] == "B" else -s["u"]))
for i, s in enumerate(DRIVE_ORDER):
    s["t_drv"] = T_DRV0 + (T_DRV1 - 0.6 - T_DRV0) * i / (len(DRIVE_ORDER) - 1)

# vibrating hammer (sits on the sheet being driven)
HAM = empty("VibroHammer", CP)
parent(box("Hammer_Body", -0.55, 0.55, -0.45, 0.45, 0.0, 1.5, M_FRAME, CP), HAM)
parent(box("Hammer_Clamp", -0.25, 0.25, -0.2, 0.2, -0.35, 0.0, M_HOSE, CP), HAM)
parent(cyl("Hammer_Cable", 0.04, 1.5, 14.0, M_HOSE, CP, seg_n=8), HAM)

# ---------- foundation piles (half-cylinders on the section plane) ----------
PILE_X = (-2.4, 0.0, 2.4)
PILE_LEN, Z_PILE_END = 8.6, -12.4             # top ends at -3.8 (embedded in the seal)
PILES = [cyl(f"Pile_{i}", 0.38, 0.0, PILE_LEN, M_PILE, CS, cx=0.0, cy=0.0, pivot=(0, 0, 0), keep_y=-0.06) for i in range(3)]
for i, p in enumerate(PILES):
    p["t0"] = C["drive"] - 0.05 + i * 0.42

# ---------- tremie pipe + seal + footing + pillar ----------
PIPE = empty("Tremie", CS)
PIPE_X, PIPE_Y = 1.25, 0.9
parent(cyl("Tremie_Pipe", 0.22, 0.0, 13.0, M_PIPE, CS, cx=PIPE_X, cy=PIPE_Y, seg_n=24), PIPE)
hop = bmesh.new(); bmesh.ops.create_cone(hop, cap_ends=False, segments=24, radius1=0.25, radius2=0.95, depth=1.3)
bmesh.ops.translate(hop, verts=hop.verts, vec=(PIPE_X, PIPE_Y, 13.65)); hopper = mesh_obj("Tremie_Hopper", hop, M_PIPE, CS); parent(hopper, PIPE)
PIPE_TIP = PIPE.children[0]
SEAL = box("Seal", -W_IN, W_IN, -0.03, W_IN, Z_MUD, Z_SEAL, M_SEAL, CS, pivot=(0, 0, Z_MUD))
FOOT = box("Footing", -3.0, 3.0, -0.03, 3.0, Z_SEAL, Z_FOOT, M_CONC, CS, pivot=(0, 0, Z_SEAL))
COL = cyl("Pillar_Column", 1.6, Z_FOOT, Z_CAP0, M_CONC, CS, pivot=(0, 0, Z_FOOT), keep_y=-0.03)
CAP = box("Pillar_Cap", -3.2, 3.2, -0.03, 2.2, Z_CAP0, Z_CAP1, M_CONC, CS, pivot=(0, 0, Z_CAP0))

# ---------- props: arrows, pump, crew mannequins, river line, Roman rings ----------
def arrow(name, mat, length=1.6):
    """Arrow along local +X, origin at the tail."""
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=0.12, radius2=0.12, depth=length - 0.5)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=((length - 0.5) / 2, 0, 0))
    hd = bmesh.new(); bmesh.ops.create_cone(hd, cap_ends=True, segments=16, radius1=0.32, radius2=0.0, depth=0.5)
    bmesh.ops.rotate(hd, verts=hd.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    bmesh.ops.translate(hd, verts=hd.verts, vec=(length - 0.25, 0, 0))
    me_h = bpy.data.meshes.new("h"); hd.to_mesh(me_h); hd.free(); bm.from_mesh(me_h); bpy.data.meshes.remove(me_h)
    return mesh_obj(name, bm, mat, CP)
PRESS = []      # inward water pressure (cyan)
for s in (-1, 1):
    for j, z in enumerate((2.1, 0.4, -1.3)):
        a = arrow(f"Press_{s:+d}_{j}", M_GLOW_C, 1.9); a.location = (s * 7.2, 0.4, z); a.rotation_euler = (0, 0, 0 if s < 0 else math.pi)
        a["delay"] = 0.12 * j + (0.05 if s > 0 else 0.0); PRESS.append(a)
UPS = []        # water pushing up from below (red)
for j, x in enumerate((-2.4, 0.0, 2.4)):
    a = arrow(f"Up_{j}", M_GLOW_R, 2.0); a.location = (x + 1.2, 0.6, Z_MUD + 0.2); a.rotation_euler = (0, math.radians(-90), 0); a["delay"] = 0.12 * j; UPS.append(a)
DOWNS = []      # the seal's weight (gold)
for j, x in enumerate((-2.6, 0.0, 2.6)):
    a = arrow(f"Down_{j}", M_GLOW_G, 1.6); a.location = (x, 0.6, Z_SEAL + 2.2); a.rotation_euler = (0, math.radians(90), 0); a["delay"] = 0.1 * j; DOWNS.append(a)
PUMP = empty("Pump", CP)
parent(box("Pump_Body", 2.4, 3.6, 2.0, 3.0, 5.0, 5.8, M_PUMP, CP), PUMP)
parent(cyl("Pump_Hose", 0.12, Z_SEAL + 0.3, 5.0, M_HOSE, CP, cx=3.0, cy=2.5, seg_n=12), PUMP)
parent(beam("Pump_Outlet", (3.6, 2.5, 5.4), (7.0, 2.5, 5.4), 0.22, 0.22), PUMP); PUMP.children[-1].data.materials[0] = M_HOSE
CREW = []
for j, x in enumerate((-2.2, 1.9)):
    m = empty(f"Crew_{j}", CP)
    parent(cyl(f"Crew_{j}_Body", 0.24, 0.0, 1.35, M_MAN, CP, seg_n=20), m)
    hd = bmesh.new(); bmesh.ops.create_uvsphere(hd, u_segments=20, v_segments=12, radius=0.2); bmesh.ops.translate(hd, verts=hd.verts, vec=(0, 0, 1.58))
    parent(mesh_obj(f"Crew_{j}_Head", hd, M_MAN, CP), m)
    parent(cyl(f"Crew_{j}_Hat", 0.25, 1.68, 1.8, M_HAT, CP, seg_n=20), m)
    m.location = (x, 1.2, Z_SEAL); m.rotation_euler = (0, 0, 0.3 * (1 if j else -1)); CREW.append(m)
RLINE = [box(f"RiverLine{s:+d}", min(s * W_OUT, s * 14), max(s * W_OUT, s * 14), -0.06, -0.02, Z_WATER - 0.05, Z_WATER + 0.05, M_GLOW_C, CP) for s in (-1, 1)]
ROMAN_POSTS = []
for ring, (rad, n) in enumerate(((4.7, 11), (5.6, 13))):
    for k in range(n):
        a = math.pi * k / (n - 1)
        x, y = rad * math.cos(a), rad * math.sin(a)
        p = cyl(f"Roman_{ring}_{k}", 0.2, 0.0, 9.0, M_WOOD, CP, cx=0, cy=0, pivot=(0, 0, 0), seg_n=12, keep_y=(-0.03 - y) if y < 0.25 else None)
        p.location = (x, y, Z_MUD); p["rank"] = k / (n - 1) * 0.6 + ring * 0.5; ROMAN_POSTS.append(p)
clay_bm = bmesh.new(); bmesh.ops.create_cone(clay_bm, cap_ends=True, segments=64, radius1=5.45, radius2=5.45, depth=8.0)
inner = bmesh.new(); bmesh.ops.create_cone(inner, cap_ends=True, segments=64, radius1=4.85, radius2=4.85, depth=10.0)
CLAY = mesh_obj("Roman_Clay", clay_bm, M_CLAY, CP); ci = mesh_obj("ci", inner, None, CP); boolean(CLAY, ci); delete(ci)
cut = box("cut", -7, 7, -7, -0.03, -6, 6, None); boolean(CLAY, cut); delete(cut)
CLAY.location = (0, 0, Z_MUD); CLAY.data.transform(Matrix.Translation((0, 0, 4.0)))

# ---------- state timeline (seconds) -> per-frame bake ----------
def sheet_bottom(s, t):
    if t < s["t_set"]: return None
    z = seg(t, s["t_set"], s["t_set"] + 0.32, Z_SHEET_SET + 12.0, Z_SHEET_SET, out3)
    if t >= s["t_drv"]:
        z = seg(t, s["t_drv"], s["t_drv"] + 0.75, Z_SHEET_SET, Z_SHEET_DRIVEN, lin)
        if t < s["t_drv"] + 0.75: z += 0.035 * math.sin(t * 2 * math.pi * 24)           # vibration
    if t >= C["sheets2"]:
        i = DRIVE_ORDER.index(s); t0 = C["sheets2"] + 0.04 * i
        z = seg(t, t0, t0 + 0.9, Z_SHEET_DRIVEN, Z_SHEET_DRIVEN + 18.0)
        if t > t0 + 0.9: return None
    return z
def frame_z(t):
    if t < C["first"]: return None
    if t >= C["then"] + 0.9: return None
    z = seg(t, C["first"], C["place"] + 0.1, 11.0, 0.0)
    if t >= C["then"]: z = seg(t, C["then"], C["then"] + 0.9, 0.0, 14.0)
    return z
def hammer_state(t):
    if t < C["vibrating"] - 0.3 or t > T_DRV1 + 0.4: return None
    act = [s for s in DRIVE_ORDER if s["t_drv"] <= t]
    s = act[-1] if act else DRIVE_ORDER[0]
    top = (sheet_bottom(s, t) or Z_SHEET_SET) + SH
    o = s["obj"]; loc = Vector((o.location.x, o.location.y, top + 0.35))
    if t < C["hammer"]: loc.z += seg(t, C["vibrating"] - 0.3, C["hammer"], 9.0, 0.0)
    if t > T_DRV1: loc.z += seg(t, T_DRV1, T_DRV1 + 0.4, 0.0, 10.0)
    return loc
def inner_water_top(t):
    if t < C["pump"] - 0.1: return Z_WATER
    if t < C["so"]:
        return seg(t, C["pump"] - 0.1, C["dry"] + 0.3, Z_WATER, 1.2) if t < C["water2"] else seg(t, C["water2"], C["below"] + 0.4, 1.2, Z_WATER)
    if t < C["switch"]: return Z_WATER
    if t < C["river3"]: return seg(t, C["switch"] + 0.1, C["drops"] + 0.7, Z_WATER, Z_SEAL + 0.02, lin)
    return seg(t, C["river3"], C["back"] + 0.3, Z_SEAL + 0.02, Z_WATER)
def seal_top(t):
    if t < C["concrete"]: return None
    return seg(t, C["concrete"], C["up"] + 0.2, Z_MUD + 0.02, Z_SEAL, lambda p: lin(p) ** 0.85)
def pipe_tip_z(t):
    if t < C["so"] - 0.1 or t > C["hardens"] + 0.6: return None
    if t < C["pour"]: return seg(t, C["so"] - 0.1, C["pour"], Z_MUD + 14.0, Z_MUD + 0.15)
    st = seal_top(t)
    z = Z_MUD + 0.15 if st is None else max(Z_MUD + 0.15, st - 0.65)
    if t > C["once"]: z = seg(t, C["once"], C["hardens"] + 0.6, Z_SEAL - 0.65, Z_SEAL + 14.0)
    return z
def pile_bottom(p, t):
    t0 = p["t0"]
    if t < t0: return None
    z = seg(t, t0, t0 + 0.3, Z_MUD + 12.0, Z_MUD, out3)
    for k in range(3):                                         # three blows each
        tb = t0 + 0.38 + k * 0.22
        if t >= tb: z = seg(t, tb, tb + 0.08, Z_MUD - (Z_MUD - Z_PILE_END) * k / 3, Z_MUD - (Z_MUD - Z_PILE_END) * (k + 1) / 3, lin)
    return z
def mud_chunk(i, t):
    """(z offset, scale) of inner mud chunk i; None = gone."""
    t0 = C["dig"] - 0.05 + 0.22 * i
    if t < t0: return (0.0, 1.0)
    if t > t0 + 0.55: return None
    return (seg(t, t0, t0 + 0.55, 0.0, 9.0), seg(t, t0 + 0.15, t0 + 0.55, 1.0, 0.05))
SWAP_IN = T_SET1 + 0.35                                         # all sheets set: switch to holed river + inner water
SWAP_OUT = C["back"] + 0.35                                     # river closed again: back to one water body
def roman_scale(p, t):
    t0 = C["two"] + p["rank"] * 1.2
    if t < t0 or t > C["keep"] + 0.7: return 0.0
    v = seg(t, t0, t0 + 0.3, 0.0, 1.0, out3)
    if t > C["keep"]: v *= seg(t, C["keep"], C["keep"] + 0.7, 1.0, 0.0)
    return v
def pulse(t, t0, hold=1.0, peak=1.0):
    if t < t0 - 0.1: return 0.0
    if t < t0 + 0.15: return seg(t, t0 - 0.1, t0 + 0.15, 0.0, peak)
    if t < t0 + hold: return peak
    return seg(t, t0 + hold, t0 + hold + 0.45, peak, 0.0)

def setvis(o, fr, hidden):
    for x in [o] + list(o.children_recursive):
        rec(x, "hide_render", -1, fr, hidden); rec(x, "hide_viewport", -1, fr, hidden)
def setloc(o, fr, v):
    for i in range(3): rec(o, "location", i, fr, v[i])
def setscale(o, fr, v):
    for i in range(3): rec(o, "scale", i, fr, v[i])
def setglow(o, fr, g):
    for x in [o] + list(o.children_recursive):
        if x.type == "MESH": rec(x, '["glow"]', -1, fr, g)

events = {"sheet_set": [], "sheet_drive": [], "pile_blow": [], "frame_land": round(C["place"] + 0.1, 3), "mud_lift": [],
          "pile_land": [], "pump_on": round(C["switch"] + 0.1, 3), "deck_land": None}
for s in SHEETS: events["sheet_set"].append(round(s["t_set"] + 0.32, 3)); events["sheet_drive"].append(round(s["t_drv"], 3))
for p in PILES:
    events["pile_land"].append(round(p["t0"] + 0.3, 3))
    for k in range(3): events["pile_blow"].append(round(p["t0"] + 0.38 + k * 0.22 + 0.08, 3))
for i in range(4): events["mud_lift"].append(round(C["dig"] - 0.05 + 0.22 * i, 3))
T_DECK0, T_DECK1 = C["build"] - 0.15, C["dry3"] + 0.25
events["deck_land"] = round(T_DECK1, 3)

FRONTS_DOWN = [WATER_F, MUD_F, FIRM_F] + BANKS[1::2]                                   # drop away below
FRONTS_UP = [d[1] for d in DECK] + [d[3] for d in DECK] + [o for _, fr in FAR_PIERS for o in fr]   # lift away above
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS
    # front half splits off on "open": ground and water drop, deck and piers lift (a wipe in both directions)
    for o in FRONTS_DOWN + FRONTS_UP:
        dz = seg(t, C["open"] - 0.05, C["open"] + 0.85, 0.0, -45.0 if o in FRONTS_DOWN else 40.0, lambda p: lin(p) ** 2)
        rec(o, "location", 2, fr, dz); setvis(o, fr, t > C["open"] + 0.85)
    # hook marker
    setvis(MARK, fr, not (C["pillar"] - 0.1 <= t < C["open"])); setglow(MARK, fr, 0.4 + 0.6 * pulse(t, C["pillar"], 2.0))
    # river bodies swap while the sheets cover the seams
    split = SWAP_IN <= t < SWAP_OUT
    msplit = SWAP_IN <= t < C["sheets2"]                    # mud closes as soon as the sheets start to rise
    setvis(WATER_B, fr, split); setvis(MUD_B, fr, msplit)
    setvis(WATER_HOLE, fr, not split); setvis(MUD_HOLE, fr, not msplit); setvis(WATER_IN, fr, not split)
    wt = inner_water_top(t); rec(WATER_IN, "scale", 2, fr, max(0.002, (wt - Z_MUD) / (Z_WATER - Z_MUD)))
    for i, ch in enumerate(MUD_CH):
        st = mud_chunk(i, t)
        setvis(ch, fr, (not split) or st is None)
        if st: rec(ch, "location", 2, fr, Z_MUD + st[0]); setscale(ch, fr, (st[1],) * 3)
    # frame
    z = frame_z(t); setvis(FRAME, fr, z is None)
    if z is not None: rec(FRAME, "location", 2, fr, z)
    for w in WALES: rec(w, '["glow"]', -1, fr, pulse(t, C["frame"], 0.7) + pulse(t, C["holds"], 0.9, 1.3))
    # sheets
    for s in SHEETS:
        zb = sheet_bottom(s, t); o = s["obj"]; setvis(o, fr, zb is None)
        if zb is not None: rec(o, "location", 2, fr, zb)
        rec(o, '["glow"]', -1, fr, 0.9 * pulse(t, C["cofferdam"], 1.1) + 0.5 * pulse(t, C["lock"] - 0.05, 0.5))
    h = hammer_state(t); setvis(HAM, fr, h is None)
    if h is not None: setloc(HAM, fr, h + Vector((0.03 * math.sin(t * 2 * math.pi * 21), 0, 0)))
    # piles
    for p in PILES:
        zb = pile_bottom(p, t); setvis(p, fr, zb is None)
        if zb is not None: setloc(p, fr, (PILE_X[PILES.index(p)], 0.0, zb))
        rec(p, '["glow"]', -1, fr, pulse(t, C["piles"] + 0.1, 0.9))
    # tremie + seal
    pz = pipe_tip_z(t); setvis(PIPE, fr, pz is None)
    if pz is not None: rec(PIPE, "location", 2, fr, pz)
    rec(PIPE_TIP, '["glow"]', -1, fr, pulse(t, C["end"], 1.4)); rec(hopper, '["glow"]', -1, fr, pulse(t, C["end"], 1.4))
    st = seal_top(t); setvis(SEAL, fr, st is None)
    if st is not None: rec(SEAL, "scale", 2, fr, max(0.002, (st - Z_MUD) / (Z_SEAL - Z_MUD)))
    rec(SEAL, '["glow"]', -1, fr, pulse(t, C["seal"], 1.2, 1.6) + pulse(t, C["fifteen"], 1.1, 1.0))
    # footing + pillar
    fz = seg(t, C["footing"] - 0.1, C["footing"] + 0.55, 0.0, 1.0); setvis(FOOT, fr, t < C["footing"] - 0.1)
    rec(FOOT, "scale", 2, fr, max(0.002, fz)); rec(FOOT, '["glow"]', -1, fr, pulse(t, C["footing"], 0.6, 0.7))
    cz = seg(t, C["pillar2"] - 0.05, C["water3"] + 0.4, 0.0, 1.0); setvis(COL, fr, t < C["pillar2"] - 0.05)
    rec(COL, "scale", 2, fr, max(0.002, cz))
    kz = seg(t, C["water3"] + 0.35, C["water3"] + 0.75, 0.0, 1.0); setvis(CAP, fr, t < C["water3"] + 0.35); rec(CAP, "scale", 2, fr, max(0.002, kz))
    # arrows
    for a in PRESS:
        on = C["pushes"] - 0.05 + a["delay"] <= t < C["next"] - 0.2
        setvis(a, fr, not on)
        k = seg(t, C["pushes"] - 0.05 + a["delay"], C["pushes"] + 0.25 + a["delay"], 0.0, 1.0, out3) if on else 0.0
        setscale(a, fr, (max(0.01, k), 1, 1)); rec(a, '["glow"]', -1, fr, 0.7 + 0.3 * math.sin(t * 7 + a["delay"] * 9))
    for a in UPS:
        on = C["water2"] + a["delay"] <= t < C["so"] - 0.1
        setvis(a, fr, not on)
        if on: rec(a, "location", 2, fr, Z_MUD + 0.2 + seg(t, C["water2"] + a["delay"], C["below"] + 0.5, 0.0, 2.2))
        rec(a, '["glow"]', -1, fr, 1.0)
    for a in DOWNS:
        on = C["weight"] - 0.05 + a["delay"] <= t < C["once"] - 0.1
        setvis(a, fr, not on)
        if on: rec(a, "location", 2, fr, Z_SEAL + 2.4 - seg(t, C["weight"] + a["delay"], C["down"] + 0.2, 0.0, 0.5))
        rec(a, '["glow"]', -1, fr, 1.0)
    # pump, crew, river line
    pon = C["pumps"] - 0.1 <= t < C["then"]
    setvis(PUMP, fr, not pon)
    if pon: setloc(PUMP, fr, (0, 0, seg(t, C["pumps"] - 0.1, C["pumps"] + 0.3, 6.0, 0.0, out3) + (0.02 * math.sin(t * 90) if t > C["switch"] else 0.0)))
    for j, m in enumerate(CREW):
        on = C["crew"] - 0.1 + 0.15 * j <= t < C["footing"] - 0.05
        setvis(m, fr, not on)
        if on: rec(m, "location", 2, fr, Z_SEAL + seg(t, C["crew"] - 0.1 + 0.15 * j, C["crew"] + 0.25 + 0.15 * j, 3.0, 0.0, out3))
    for o in RLINE:
        setvis(o, fr, not (C["below2"] - 0.1 <= t < C["pour2"] - 0.1)); rec(o, '["glow"]', -1, fr, 0.6)
        rec(o, "scale", 0, fr, max(0.01, seg(t, C["below2"] - 0.1, C["below2"] + 0.4, 0.0, 1.0)))
    # Romans
    for p in ROMAN_POSTS:
        v = roman_scale(p, t); setvis(p, fr, v <= 0.001); rec(p, "scale", 2, fr, max(0.002, v))
        rec(p, '["glow"]', -1, fr, pulse(t, C["wooden"], 0.8, 0.8))
    cv = seg(t, C["clay"] - 0.05, C["clay"] + 0.5, 0.0, 1.0) * (seg(t, C["keep"], C["keep"] + 0.7, 1.0, 0.0) if t > C["keep"] else 1.0)
    setvis(CLAY, fr, cv <= 0.001); rec(CLAY, "scale", 2, fr, max(0.002, cv)); rec(CLAY, '["glow"]', -1, fr, pulse(t, C["clay"], 0.6, 0.8))
    # finished deck span lands on the new pillar
    dz = seg(t, T_DECK0, T_DECK1, 9.0, 0.0, out3); setvis(DECK_MID, fr, t < T_DECK0); rec(DECK_MID, "location", 2, fr, dz)
# side deck back halves: only in the hook and the final pull-back (in the close section shots they read as floating slabs)
for d in DECK:
    for o in (d[0], d[2]):
        setvis(o, 1, False); setvis(o, F(C["first"]), True); setvis(o, F(T_DECK0 - 0.8), False)
write_tracks(); TRACKS.clear()

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 35
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tcn = cam.constraints.new("TRACK_TO"); tcn.target = TGT; tcn.track_axis = "TRACK_NEGATIVE_Z"; tcn.up_axis = "UP_Y"
cam_d.clip_end = 600
SEC = ((0.0, -33.0, 1.0), (0.0, 0.0, 0.5), 35)            # the main section view
SHOTS = [  # (time, camera loc, target, lens)
    (0.0, (-9.0, -50.0, 9.0), (0.0, 0.0, 6.0), 30),
    (C["pillar"], (-8.0, -44.0, 10.0), (0.0, 0.0, 5.0), 30),
    (C["leave"], (-7.0, -36.0, 12.0), (0.0, 0.0, 3.5), 32),
    (C["open"] - 0.05, (-7.0, -34.0, 11.0), (0.0, 0.0, 2.5), 32),
    (C["open"] + 0.9, (-6.0, -34.0, 4.0), (0.0, 0.0, 0.5), 35),
    (C["first"], (-3.0, -33.0, 2.5), (0.0, 0.0, 1.5), 35),
    (C["around"], SEC[0], SEC[1], 35),
    (C["hammer"], (1.0, -27.0, 5.0), (0.0, 2.0, 3.0), 35),
    (C["riverbed"] + 0.4, (0.5, -30.0, 0.0), (0.0, 0.0, -1.5), 35),
    (C["cofferdam"], (-9.0, -27.0, 9.0), (0.0, 2.0, 0.5), 35),
    (C["water"], SEC[0], SEC[1], 35),
    (C["holds"], (0.0, -27.0, 4.0), (0.0, 2.0, 2.0), 35),
    (C["next"], (0.0, -27.0, -1.0), (0.0, 0.0, -2.5), 35),
    (C["piles"] + 0.4, (0.0, -32.0, -3.5), (0.0, 0.0, -5.0), 35),
    (C["but"], (0.0, -28.0, 0.0), (0.0, 0.0, -1.0), 35),
    (C["below"], (0.0, -25.0, -2.0), (0.0, 0.0, -3.0), 35),
    (C["pour"], (2.5, -26.0, 1.5), (0.5, 0.0, -1.0), 35),
    (C["buried"], (1.5, -16.0, -2.5), (1.0, 0.0, -3.3), 35),
    (C["up"], (0.5, -22.0, -1.0), (0.0, 0.0, -2.2), 35),
    (C["kentucky"], (0.0, -19.0, -2.6), (0.0, 0.0, -3.2), 35),
    (C["weight"], (0.0, -22.0, -1.0), (0.0, 0.0, -2.0), 35),
    (C["pumps"], (3.0, -29.0, 3.5), (0.5, 0.0, 1.0), 35),
    (C["drops"] + 0.8, (0.0, -28.0, 1.5), (0.0, 0.0, 0.5), 35),
    (C["crew"], (-1.0, -20.0, 0.5), (0.0, 0.0, -0.8), 35),
    (C["below2"], (-2.0, -27.0, 2.0), (0.0, 0.0, 1.0), 35),
    (C["footing"], (0.0, -30.0, 2.0), (0.0, 0.0, 1.5), 35),
    (C["water3"] + 0.6, (-4.0, -36.0, 6.0), (0.0, 0.0, 4.0), 35),
    (C["then"], (-4.0, -37.0, 6.0), (0.0, 0.0, 4.0), 35),
    (C["back"] + 0.4, (-2.0, -38.0, 4.0), (0.0, 0.0, 3.0), 35),
    (C["romans"], (-8.0, -30.0, 9.0), (0.0, 2.0, 1.5), 35),
    (C["clay"] + 0.4, (-6.0, -28.0, 7.0), (0.0, 2.0, 1.0), 35),
    (C["same"], (-10.0, -40.0, 9.0), (0.0, 1.0, 4.0), 33),
    (C["build"], (-12.0, -44.0, 10.0), (0.0, 1.0, 5.0), 32),
    (C["follow"], (-13.0, -46.0, 11.0), (0.0, 1.0, 5.5), 32),
    (C["end_t"], (6.0, -46.0, 12.0), (0.0, 1.0, 5.5), 32),
]
for t, loc, tgt, lens in SHOTS:
    fr = F(t)
    setloc(cam, fr, loc); setloc(TGT, fr, tgt); rec(cam_d, "lens", -1, fr, lens)
write_tracks("BEZIER")                     # smooth camera moves

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
# the physical sky is far too bright as a light source: camera rays see it, everything else gets a soft blue ambient
amb = wn.new("ShaderNodeBackground"); amb.inputs["Color"].default_value = (0.55, 0.68, 0.85, 1); amb.inputs["Strength"].default_value = 0.45
lp = wn.new("ShaderNodeLightPath"); mixw = wn.new("ShaderNodeMixShader")
cg = wn.new("ShaderNodeMath"); cg.operation = "MAXIMUM"; wl.new(lp.outputs["Is Camera Ray"], cg.inputs[0]); wl.new(lp.outputs["Is Glossy Ray"], cg.inputs[1])
wl.new(cg.outputs[0], mixw.inputs[0]); wl.new(amb.outputs[0], mixw.inputs[1]); wl.new(bg.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], next(n for n in wn if n.type == "OUTPUT_WORLD").inputs["Surface"])
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 2.4; sun_d.angle = math.radians(3)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(-28), math.radians(-25))
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 30; fill_d.energy = 1200; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill); fill.location = (-6, -30, 4)
fc_ = fill.constraints.new("TRACK_TO"); fc_.target = TGT; fc_.track_axis = "TRACK_NEGATIVE_Z"; fc_.up_axis = "UP_Y"

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
mid_sheet = next(s["obj"] for s in SHEETS if s["wall"] == "R" and s["u"] < 1.0)
ANCH = {"marker": (None, Vector((HW, -HW, Z_WATER))), "frame": (WALES[1], None), "sheet": (mid_sheet, Vector((0, 0, 11.0))),
        "hammer": (HAM, Vector((0, 0, 0.8))), "cofferdam": (None, Vector((-HW, 0, 5.0))), "mud": (None, Vector((-2.8, 0, -3.3))),
        "piles": (PILES[0], Vector((0, 0, PILE_LEN - 0.5))), "pipe_end": (PIPE, Vector((PIPE_X, PIPE_Y, 0.2))),
        "seal": (None, Vector((-W_IN, 0, (Z_MUD + Z_SEAL) / 2))), "seal_top": (None, Vector((W_IN, 0, Z_SEAL))),
        "seal_bottom": (None, Vector((W_IN, 0, Z_MUD))), "pump": (PUMP, Vector((3.0, 2.5, 5.8))), "water_out": (None, Vector((-5.6, 0, Z_WATER))),
        "footing": (None, Vector((-3.0, 0, (Z_SEAL + Z_FOOT) / 2))), "pillar": (None, Vector((1.6, 0, 6.0))), "romans": (None, Vector((-5.15, 0, 3.0))),
        "river": (None, Vector((0, 0, Z_WATER)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, (ob, local) in ANCH.items():
        if ob is None: w = local
        elif local is None: w = ob.matrix_world.translation.copy()
        else: w = ob.matrix_world @ local
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
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
