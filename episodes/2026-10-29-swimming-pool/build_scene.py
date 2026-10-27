# Swimming-Pool-3D: a backyard concrete (gunite / shotcrete) pool built step by step in a yard cross-section, Blender Cycles.
# Every cue is a word in the VO.
# Set A (origin): yard cut at y = 0 through the pool's long axis. Finished pool in the hook (front half mirrored, drops away on
#   "open"), then the build: dig (excavator), steel cage, plumbing, sprayed shell, curing mist, tile, coping + deck, plaster,
#   fill, the pump loop, the empty pool floating up on high groundwater, the relief valve.
# Set C (x = -1000): concrete beam demo (squeezed is fine, pulled cracks, steel inside holds).
# Set B (x = 2000): a generic early-1900s museum facade being replastered by a two-chamber cement gun on a cart (no people).
# Reveals use boolean cutters baked per frame; the excavator, spray, pulses, drops and arrows are baked per frame.
# Sizes are illustrative, none are spoken. Textures + HDRI: Poly Haven CC0 (run `node fetch_polyhaven.js` first).
# Run from the episode folder:
#   blender -b -y -P build_scene.py -- --save scene.blend [--stills f1,f2 --pct 25 --samples 8 --out checks] [--anim --out frames] [--cpu]
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(HERE, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
PH_DIR = os.path.join(HERE, "assets", "polyhaven")
MANIFEST = json.load(open(os.path.join(PH_DIR, "manifest.json")))
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 0.75, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(29)

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
for name, word in [("how", "how"), ("backyard", "backyard"), ("swimming", "swimming"), ("built", "built"), ("lets", "let's"),
                   ("cut", "cut"), ("open", "open"), ("first", "first"), ("crew", "crew"), ("digs", "digs"), ("hole", "hole"),
                   ("bigger", "bigger"), ("pool", "pool"), ("next", "next"), ("cage", "cage"), ("steel", "steel"), ("bars", "bars"),
                   ("floor", "floor"), ("walls", "walls"), ("steps", "steps"), ("concrete", "concrete"), ("great", "great"),
                   ("squeezed", "squeezed"), ("but", "but"), ("cracks", "cracks"), ("pulled", "pulled"), ("steel2", "steel"),
                   ("takes", "takes"), ("pulling", "pulling"), ("then", "then"), ("plumbing", "plumbing"), ("main", "main"),
                   ("drain", "drain"), ("deep", "deep"), ("skimmer", "skimmer"), ("waterline", "waterline"), ("return", "return"),
                   ("jets", "jets"), ("now", "now"), ("fun", "fun"), ("hose", "hose"), ("blasts", "blasts"), ("concrete2", "concrete"),
                   ("steel3", "steel"), ("dry", "dry"), ("gunite", "gunite"), ("wet", "wet"), ("shotcrete", "shotcrete"),
                   ("crew2", "crew"), ("smooths", "smooths"), ("shell", "shell"), ("hand", "hand"), ("then2", "then"),
                   ("wet2", "wet"), ("cures", "cures"), ("tile", "tile"), ("waterline2", "waterline"), ("coping", "coping"),
                   ("edge", "edge"), ("plaster", "plaster"), ("seals", "seals"), ("inside", "inside"), ("because", "because"),
                   ("bare", "bare"), ("concrete3", "concrete"), ("slowly", "slowly"), ("seep", "seep"), ("through", "through"),
                   ("fill", "fill"), ("loop", "loop"), ("starts", "starts"), ("pump", "pump"), ("pulls", "pulls"),
                   ("drain2", "drain"), ("skimmer2", "skimmer"), ("pushes", "pushes"), ("filter", "filter"), ("sends", "sends"),
                   ("jets2", "jets"), ("heres", "here's"), ("scary", "scary"), ("drain3", "drain"), ("groundwater", "groundwater"),
                   ("high", "high"), ("float", "float"), ("ground", "ground"), ("thats", "that's"), ("many", "many"),
                   ("relief", "relief"), ("valve", "valve"), ("lets2", "lets"), ("groundwater2", "groundwater"), ("in", "in"),
                   ("and", "and"), ("gun", "gun"), ("taxidermist", "taxidermist"), ("carl", "carl"), ("akeley", "akeley"),
                   ("built2", "built"), ("hundred", "hundred"), ("years", "years"), ("replaster", "replaster"),
                   ("museum", "museum"), ("chicago", "chicago"), ("would", "would"), ("concrete4", "concrete"),
                   ("above", "above-ground"), ("tell", "tell"), ("comments", "comments")]:
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
    for t0, t1 in wins: vis(obj, F(t0), False); vis(obj, F(t1), True)
def fcurves_of(ad):
    act = ad.action
    try: return act.fcurves
    except AttributeError:
        from bpy_extras import anim_utils
        return anim_utils.action_get_channelbag_for_slot(act, ad.action_slot).fcurves
def fcurve(owner, path, index):
    owner.keyframe_insert(path, index=index, frame=1)
    return fcurves_of(owner.animation_data).find(path, index=max(0, index))
def bake(owner, path, index, values):
    """values[f-1] for every frame, linear (fast path: foreach_set instead of keyframe_insert)."""
    fc = fcurve(owner, path, index)
    fc.keyframe_points.clear(); fc.keyframe_points.add(len(values))
    co = []
    for i, v in enumerate(values): co += [i + 1, v]
    fc.keyframe_points.foreach_set("co", co)
    fc.keyframe_points.foreach_set("interpolation", [1] * len(values))      # LINEAR
    fc.update(); return fc
def bake_vec(owner, path, vecs):
    for ax in range(3): bake(owner, path, ax, [v[ax] for v in vecs])
def bake_value(node, values):
    """Bake a Value node's output (material / world node trees)."""
    nt = node.id_data; p = f'nodes["{node.name}"].outputs[0].default_value'
    node.outputs[0].default_value = values[0]
    nt.keyframe_insert(p, frame=1)
    fc = fcurves_of(nt.animation_data).find(p, index=0)
    fc.keyframe_points.clear(); fc.keyframe_points.add(len(values)); co = []
    for i, v in enumerate(values): co += [i + 1, v]
    fc.keyframe_points.foreach_set("co", co); fc.keyframe_points.foreach_set("interpolation", [1] * len(values)); fc.update()
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("SwimmingPool")
CUTTERS = coll("Cutters"); CUTTERS.hide_render = True
TS = [(fr - 1) / FPS for fr in range(1, FRAMES + 1)]

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
def mat(name, rgb, rough=0.4, metallic=0.0, emit_rgb=(1.0, 0.74, 0.27), noise=0.0, bump=0.0):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = rough
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord"); n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise; n.inputs["Detail"].default_value = 6; nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[3].default_value = rough * 0.7; mr.inputs[4].default_value = rough * 1.4
        nt.links.new(n.outputs["Fac"], mr.inputs[0]); nt.links.new(mr.outputs[0], b.inputs["Roughness"])
        if bump:
            bp = nt.nodes.new("ShaderNodeBump"); bp.name = "Bump"; bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.03
            nt.links.new(n.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
def img(path, color=True):
    im = bpy.data.images.load(path, check_existing=True)
    if not color: im.colorspace_settings.name = "Non-Color"
    return im
def tex_set(nt, asset, size_m, vec_src, blend=0.25):
    """Box-projected PBR set -> dict(col, rough, nrm) output sockets."""
    L = nt.links; files = MANIFEST[asset]
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / size_m,) * 3
    L.new(vec_src, mp.inputs["Vector"])
    out = {}
    for mapname, keyname, color in [("Diffuse", "col", True), ("Rough", "rough", False), ("nor_gl", "nrm", False)]:
        if mapname not in files: continue
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(os.path.join(PH_DIR, asset, files[mapname]), color)
        t.projection = "BOX"; t.projection_blend = blend
        L.new(mp.outputs["Vector"], t.inputs["Vector"]); out[keyname] = t.outputs["Color"]
    return out
def mix_col(nt, fac, a, b):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = "RGBA"
    nt.links.new(fac, m.inputs["Factor"]); nt.links.new(a, m.inputs[6]); nt.links.new(b, m.inputs[7]); return m.outputs[2]
def pbr_mat(name, asset, size_m, value=1.0, emit_rgb=(1.0, 0.74, 0.27)):
    m, nt, b = new_mat(name); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry"); t = tex_set(nt, asset, size_m, g.outputs["Position"])
    hv = nt.nodes.new("ShaderNodeHueSaturation"); hv.inputs["Value"].default_value = value; L.new(t["col"], hv.inputs["Color"])
    L.new(hv.outputs["Color"], b.inputs["Base Color"])
    bw = nt.nodes.new("ShaderNodeRGBToBW"); L.new(t["rough"], bw.inputs[0]); L.new(bw.outputs[0], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); L.new(t["nrm"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Emission Color"].default_value = (*emit_rgb, 1); b.inputs["Emission Strength"].default_value = 0.0
    return m, b
GW_NODES = []
def ground_mat(name):
    """World-space: up-facing faces at the lawn height = grass, everything else = soil darkening with depth.
    A 'water table' value tints the soil cyan below it (the scary beat)."""
    m, nt, b = new_mat(name); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry"); pos = g.outputs["Position"]
    grass = tex_set(nt, "grass_ground", 2.0, pos); soil = tex_set(nt, "excavated_soil_wall", 2.2, pos)
    gh = nt.nodes.new("ShaderNodeHueSaturation"); gh.inputs["Hue"].default_value = 0.62; gh.inputs["Saturation"].default_value = 1.5
    gh.inputs["Value"].default_value = 0.85; L.new(grass["col"], gh.inputs["Color"]); grass["col"] = gh.outputs["Color"]
    sp = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(pos, sp.inputs[0])
    sn = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Normal"], sn.inputs[0])
    up = nt.nodes.new("ShaderNodeMath"); up.operation = "GREATER_THAN"; up.inputs[1].default_value = 0.7; L.new(sn.outputs[2], up.inputs[0])
    hi = nt.nodes.new("ShaderNodeMath"); hi.operation = "GREATER_THAN"; hi.inputs[1].default_value = -0.08; L.new(sp.outputs[2], hi.inputs[0])
    isg = nt.nodes.new("ShaderNodeMath"); isg.operation = "MULTIPLY"; L.new(up.outputs[0], isg.inputs[0]); L.new(hi.outputs[0], isg.inputs[1])
    dk = nt.nodes.new("ShaderNodeMapRange"); dk.inputs[1].default_value = -7.0; dk.inputs[2].default_value = -0.5
    dk.inputs[3].default_value = 0.35; dk.inputs[4].default_value = 1.0; L.new(sp.outputs[2], dk.inputs[0])
    sc = nt.nodes.new("ShaderNodeMix"); sc.data_type = "RGBA"; sc.blend_type = "MULTIPLY"; sc.inputs["Factor"].default_value = 1.0
    L.new(soil["col"], sc.inputs[6]); dkc = nt.nodes.new("ShaderNodeCombineColor"); [L.new(dk.outputs[0], dkc.inputs[i]) for i in range(3)]
    L.new(dkc.outputs[0], sc.inputs[7])
    col = mix_col(nt, isg.outputs[0], sc.outputs[2], grass["col"])
    rough = mix_col(nt, isg.outputs[0], soil["rough"], grass["rough"])
    bw = nt.nodes.new("ShaderNodeRGBToBW"); L.new(rough, bw.inputs[0]); L.new(bw.outputs[0], b.inputs["Roughness"])
    nrm = mix_col(nt, isg.outputs[0], soil["nrm"], grass["nrm"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); L.new(nrm, nm.inputs["Color"]); L.new(nm.outputs["Normal"], b.inputs["Normal"])
    # water table: soil below the level turns dark blue and glows cyan a little
    gw = nt.nodes.new("ShaderNodeValue"); gw.name = "WaterTable"; gw.outputs[0].default_value = -100.0; GW_NODES.append(gw)
    wob = nt.nodes.new("ShaderNodeTexNoise"); wob.inputs["Scale"].default_value = 1.2; L.new(pos, wob.inputs["Vector"])
    zz = nt.nodes.new("ShaderNodeMath"); zz.operation = "MULTIPLY_ADD"; zz.inputs[1].default_value = 0.25
    L.new(wob.outputs["Fac"], zz.inputs[0]); L.new(sp.outputs[2], zz.inputs[2])
    wet = nt.nodes.new("ShaderNodeMath"); wet.operation = "LESS_THAN"; L.new(zz.outputs[0], wet.inputs[0]); L.new(gw.outputs[0], wet.inputs[1])
    wetc = nt.nodes.new("ShaderNodeMix"); wetc.data_type = "RGBA"; wetc.blend_type = "MULTIPLY"; L.new(wet.outputs[0], wetc.inputs["Factor"])
    L.new(col, wetc.inputs[6]); wetc.inputs[7].default_value = (0.25, 0.55, 1.0, 1)
    L.new(wetc.outputs[2], b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (0.25, 0.9, 1.0, 1)
    em = nt.nodes.new("ShaderNodeMath"); em.operation = "MULTIPLY"; em.inputs[1].default_value = 0.35; L.new(wet.outputs[0], em.inputs[0])
    L.new(em.outputs[0], b.inputs["Emission Strength"])
    return m, b
GOLD, CYAN, RED = (1.0, 0.70, 0.22), (0.25, 0.90, 1.0), (1.0, 0.18, 0.12)
M_GROUND, _ = ground_mat("Ground")
M_DECK, B_DECK = pbr_mat("Deck", "brushed_concrete", 1.5, 1.15)
M_TILE, B_TILE = pbr_mat("WaterlineTile", "blue_floor_tiles_01", 0.6, 1.0)
M_SHELL, B_SHELL = mat("Shotcrete", (0.28, 0.27, 0.25), 0.9, 0.0, GOLD, 14, 0.9)
M_SHELL_N = M_SHELL.node_tree
M_PLASTER, B_PLASTER = mat("Plaster", (0.86, 0.90, 0.92), 0.35, 0.0, (1.0, 1.0, 1.0), 20)
M_COPING, B_COPING = mat("Coping", (0.78, 0.72, 0.62), 0.6, 0.0, GOLD, 12)
M_REBAR, B_REBAR = mat("Rebar", (0.30, 0.16, 0.08), 0.55, 0.7, GOLD)
M_PVC, B_PVC = mat("PVC", (0.88, 0.88, 0.86), 0.35, 0.0, GOLD)
M_RET, B_RET = mat("ReturnPVC", (0.88, 0.88, 0.86), 0.35, 0.0, CYAN)
M_GRATE, B_GRATE = mat("DrainGrate", (0.10, 0.12, 0.14), 0.4, 0.2, GOLD)
M_SKIM, B_SKIM = mat("Skimmer", (0.92, 0.92, 0.90), 0.4, 0.0, GOLD)
M_JET, B_JET = mat("Jets", (0.85, 0.85, 0.85), 0.3, 0.6, CYAN)
M_VALVE, B_VALVE = mat("ReliefValve", (0.75, 0.75, 0.72), 0.35, 0.3, GOLD)
M_PUMP, B_PUMP = mat("Pump", (0.18, 0.32, 0.55), 0.35, 0.2, GOLD)
M_MOTOR, _ = mat("Motor", (0.22, 0.22, 0.24), 0.4, 0.6)
M_FILTER, B_FILTER = mat("Filter", (0.85, 0.85, 0.82), 0.3, 0.0, GOLD)
M_PAD, _ = mat("EquipmentPad", (0.55, 0.55, 0.53), 0.85, 0.0, GOLD, 25)
M_WATER, B_WATER = mat("PoolWater", (0.55, 0.85, 0.95), 0.03, 0.0, CYAN)
B_WATER.inputs["Transmission Weight"].default_value = 0.92; B_WATER.inputs["IOR"].default_value = 1.33
M_WATER.node_tree.nodes.new("ShaderNodeVolumeAbsorption")
_va = M_WATER.node_tree.nodes["Volume Absorption"]; _va.inputs["Color"].default_value = (0.35, 0.8, 0.95, 1); _va.inputs["Density"].default_value = 0.25
M_WATER.node_tree.links.new(_va.outputs[0], next(n for n in M_WATER.node_tree.nodes if n.type == "OUTPUT_MATERIAL").inputs["Volume"])
_wn = M_WATER.node_tree; _wtc = _wn.nodes.new("ShaderNodeTexCoord"); _wno = _wn.nodes.new("ShaderNodeTexNoise"); _wno.noise_dimensions = "4D"
_wno.inputs["Scale"].default_value = 2.5; _wn.links.new(_wtc.outputs["Object"], _wno.inputs["Vector"])
_wbp = _wn.nodes.new("ShaderNodeBump"); _wbp.inputs["Strength"].default_value = 0.25; _wbp.inputs["Distance"].default_value = 0.02
_wn.links.new(_wno.outputs["Fac"], _wbp.inputs["Height"]); _wn.links.new(_wbp.outputs["Normal"], B_WATER.inputs["Normal"])
key(_wno.inputs["W"], "default_value", 1, 0.0, "LINEAR"); key(_wno.inputs["W"], "default_value", FRAMES, DUR * 0.35, "LINEAR")
M_GHOST, B_GHOST = mat("GhostOutline", CYAN, 0.4, 0.0, CYAN); B_GHOST.inputs["Emission Strength"].default_value = 5.0
M_SPRAY, _ = mat("SprayBits", (0.55, 0.54, 0.50), 0.9)
M_MIST, B_MIST = mat("CureMist", (0.7, 0.9, 1.0), 0.2, 0.0, CYAN); B_MIST.inputs["Emission Strength"].default_value = 1.5
M_SEEP, B_SEEP = mat("SeepDrops", CYAN, 0.3, 0.0, CYAN); B_SEEP.inputs["Emission Strength"].default_value = 4.0
M_IN, B_IN = mat("PulseSuction", GOLD, 0.4, 0.0, GOLD); B_IN.inputs["Emission Strength"].default_value = 4.0
M_OUT, B_OUT = mat("PulseReturn", CYAN, 0.4, 0.0, CYAN); B_OUT.inputs["Emission Strength"].default_value = 4.0
M_ARROW, B_ARROW = mat("PressureArrows", CYAN, 0.4, 0.0, CYAN); B_ARROW.inputs["Emission Strength"].default_value = 4.0
M_DIRT, _ = mat("DirtChunks", (0.20, 0.14, 0.09), 0.9)
M_EXC, B_EXC = mat("ExcavatorPaint", (0.95, 0.62, 0.08), 0.35, 0.1, GOLD)
M_DARK, _ = mat("DarkSteel", (0.05, 0.05, 0.05), 0.6, 0.4)
M_GLASS, _ = mat("CabGlass", (0.15, 0.2, 0.25), 0.1, 0.0)
M_HEDGE, _ = mat("Hedge", (0.06, 0.20, 0.05), 0.8, 0.0, GOLD, 18)
M_FENCE, _ = mat("Fence", (0.55, 0.42, 0.30), 0.7, 0.0, GOLD, 6)
# Set C
M_BEAM, B_BEAM = mat("Beam", (0.40, 0.39, 0.36), 0.85, 0.0, RED, 18, 0.5)
M_STUDIO, _ = mat("StudioFloor", (0.05, 0.055, 0.06), 0.6)
M_SQZ, B_SQZ = mat("SqueezeArrows", GOLD, 0.4, 0.0, GOLD); B_SQZ.inputs["Emission Strength"].default_value = 4.0
M_PULL, B_PULL = mat("PullArrows", RED, 0.4, 0.0, RED); B_PULL.inputs["Emission Strength"].default_value = 4.0
M_CRACK, B_CRACK = mat("CrackGlow", RED, 0.4, 0.0, RED); B_CRACK.inputs["Emission Strength"].default_value = 6.0
# Set B
M_FACADE, B_FACADE = mat("FacadeOld", (0.22, 0.19, 0.15), 0.9, 0.0, GOLD, 4, 0.8)
M_PATCH, B_PATCH = mat("FacadeFresh", (0.80, 0.77, 0.70), 0.8, 0.0, GOLD, 10)
M_GUN, B_GUN = mat("CementGun", (0.20, 0.24, 0.20), 0.45, 0.6, GOLD)
M_WOOD, _ = mat("CartWood", (0.35, 0.22, 0.12), 0.7, 0.0, GOLD, 8)
M_HOSE, B_HOSE = mat("Hose", (0.05, 0.05, 0.05), 0.5, 0.0, GOLD)
M_STREET, _ = mat("Cobbles", (0.25, 0.24, 0.22), 0.8, 0.0, GOLD, 30, 0.6)

# ---------- geometry helpers ----------
def mesh_obj(name, bm, mats, parent=None, link=True, coll_=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in (mats if isinstance(mats, (list, tuple)) else [mats]):
        if m_: me.materials.append(m_)
    o = bpy.data.objects.new(name, me)
    if link: (coll_ or CL).objects.link(o)
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o
def add_box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
    bmesh.ops.scale(bm, verts=vs, vec=(x1 - x0, y1 - y0, z1 - z0))
    bmesh.ops.translate(bm, verts=vs, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def box(name, x0, x1, y0, y1, z0, z1, m_, parent=None, coll_=None):
    bm = bmesh.new(); add_box(bm, x0, x1, y0, y1, z0, z1); return mesh_obj(name, bm, m_, parent, coll_=coll_)
def add_cyl(bm, r, depth, axis, center, seg=32, mi=0, r2=None):
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r2 is None else r2, depth=depth); vs = res["verts"]
    if axis == "X": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    if axis == "Y": bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, verts=vs, vec=center)
    for f in {f for v in vs for f in v.link_faces}: f.material_index = mi
    return vs
def add_prism_y(bm, poly, y0, y1, mi=0):
    """Extrude a simple (possibly concave) polygon given in (x, z) between y0 and y1; caps are triangulated."""
    from mathutils.geometry import tessellate_polygon
    a = [bm.verts.new((x, y0, z)) for x, z in poly]; b = [bm.verts.new((x, y1, z)) for x, z in poly]
    fs = []
    for i, j, k in tessellate_polygon([[Vector((x, z, 0.0)) for x, z in poly]]):     # robust for concave outlines
        fs.append(bm.faces.new((a[i], a[j], a[k]))); fs.append(bm.faces.new((b[i], b[k], b[j])))
    n = len(poly)
    for i in range(n): fs.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in fs: f.material_index = mi
    bmesh.ops.recalc_face_normals(bm, faces=fs)
def prism(name, poly, y0, y1, m_, parent=None, coll_=None):
    bm = bmesh.new(); add_prism_y(bm, poly, y0, y1); return mesh_obj(name, bm, m_, parent, coll_=coll_)
def bevel_mod(o, w=0.01, seg=2):
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = w; bv.segments = seg; bv.limit_method = "ANGLE"
def curve_obj(name, pts, depth, m_, res=3, link=True, parent=None):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = res
    cu.use_fill_caps = True
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    if m_: cu.materials.append(m_)
    o = bpy.data.objects.new(name, cu)
    if link: CL.objects.link(o)
    if parent: o.parent = parent; o.matrix_parent_inverse = Matrix.Identity(4)
    return o
def sphere_mesh(name, r, m_, sub=2):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(m_); return me
def arrow_mesh(name, length, m_, r=0.05, head=0.16):
    """Arrow along +X starting at the origin."""
    bm = bmesh.new(); add_cyl(bm, r, length - head, "X", ((length - head) / 2, 0, 0), 16)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r * 2.6, radius2=0.0, depth=head); vs = res["verts"]
    bmesh.ops.rotate(bm, verts=vs, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y")); bmesh.ops.translate(bm, verts=vs, vec=(length - head / 2, 0, 0))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(m_); return me
def cutter(name, x0, x1, y0, y1, z0, z1):
    """Unit box with its origin at (0,0,0) scaled/moved per frame; used as a boolean INTERSECT cutter."""
    o = box(name, x0, x1, y0, y1, z0, z1, None, coll_=CUTTERS); o.display_type = "WIRE"; o.hide_render = True; return o
def boolean(o, cut, op="INTERSECT"):
    md = o.modifiers.new("Reveal", "BOOLEAN"); md.object = cut; md.operation = op
    for s in ("MANIFOLD", "FLOAT", "FAST", "EXACT"):
        try: md.solver = s; break
        except Exception: continue
    return md

# ---------- easing, piecewise curves, paths ----------
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
def path_fn(pts):
    """Point at arc-length fraction u (0..1) along a polyline."""
    P = [Vector(p) for p in pts]; L = [0.0]
    for a, b in zip(P, P[1:]): L.append(L[-1] + (b - a).length)
    def at(u):
        s = max(0.0, min(1.0, u)) * L[-1]
        for i in range(len(P) - 1):
            if s <= L[i + 1] or i == len(P) - 2:
                seg = max(1e-6, L[i + 1] - L[i]); return P[i].lerp(P[i + 1], (s - L[i]) / seg)
    return at, L[-1]
def offset_line(pts, d):
    """Offset an open (x, z) polyline by d along its right normal (outward for the pool profile), mitred corners."""
    P = [Vector(p) for p in pts]; out = []
    for i in range(len(P)):
        ns = []
        if i > 0: t = (P[i] - P[i - 1]).normalized(); ns.append(Vector((t.y, -t.x)))
        if i < len(P) - 1: t = (P[i + 1] - P[i]).normalized(); ns.append(Vector((t.y, -t.x)))
        n = (ns[0] + ns[-1]).normalized(); c = max(0.3, n.dot(ns[0]))
        out.append(tuple(P[i] + n * (d / c)))
    return out

# ---------- time windows ----------
T_OPEN, T_DIG = C["open"], C["first"] - 0.05          # cut-open, then the build starts (hard cut)
T_BEAM0, T_BEAM1 = C["concrete"] - 0.05, C["then"] - 0.05
T_B0, T_B1 = C["and"] - 0.05, C["would"] - 0.05        # museum set
T_CTA = C["would"] - 0.05
FIN = [(0.0, T_DIG), (T_CTA, DUR + 1)]                 # the finished pool on screen
def after(t0): return [(0.0, T_DIG), (t0, T_B1), (T_CTA, DUR + 1)] if t0 < T_B0 else FIN   # built at t0, stays (the museum set is far away anyway)

# ---------- Set A: pool profile (x, z), cut at y = 0, pool interior y 0..PY ----------
PY, SH, WL = 2.6, 0.25, -0.15                           # half-width shown behind the cut, shell thickness, water level
P_IN = [(-5.0, 0.0), (-5.0, -0.3), (-4.6, -0.3), (-4.6, -0.6), (-4.2, -0.6), (-4.2, -1.0), (-1.0, -1.0), (1.5, -2.4), (5.0, -2.4), (5.0, 0.0)]
P_SMOOTH = [(-5.0, 0.0), (-5.0, -1.0), (-1.0, -1.0), (1.5, -2.4), (5.0, -2.4), (5.0, 0.0)]   # without the steps
P_OUT = offset_line(P_SMOOTH, SH)
P_OUT[0] = (P_OUT[0][0], 0.0); P_OUT[-1] = (P_OUT[-1][0], 0.0)
P_HOLE = offset_line(P_SMOOTH, SH + 0.32); P_HOLE[0] = (P_HOLE[0][0], 0.0); P_HOLE[-1] = (P_HOLE[-1][0], 0.0)
P_PL = offset_line(P_IN, -0.035); P_PL[0] = (P_PL[0][0], 0.0); P_PL[-1] = (P_PL[-1][0], 0.0)   # plaster inner face
PYO, PYH = PY + SH, PY + SH + 0.32                       # back of the shell, back of the hole
GX0, GX1, GY1, GZ0 = -60.0, 60.0, 24.0, -60.0
X_PAD = 8.6                                              # equipment pad centre
POOL = bpy.data.objects.new("PoolGroup", None); CL.objects.link(POOL)       # lifts out of the ground on "float"

# ground with the excavation hole (front block y 0..PYH has the hole; behind it solid)
ground_poly = [(GX0, 0.0), (GX0, GZ0), (GX1, GZ0), (GX1, 0.0)] + P_HOLE[::-1]
GROUND = prism("Ground_Hole", ground_poly, 0.0, PYH, M_GROUND)
box("Ground_Back", GX0, GX1, PYH, GY1, GZ0, 0.0, M_GROUND)
# backfill between hole and shell (after the shell is built)
bm = bmesh.new(); add_prism_y(bm, P_HOLE + P_OUT[::-1], 0.0, PYO)
add_box(bm, P_HOLE[0][0], P_HOLE[-1][0], PYO, PYH, min(z for _, z in P_HOLE), 0.0)
BACKFILL = mesh_obj("Backfill", bm, M_GROUND)
# hedge + fence at the back of the yard, trees of boxes kept simple
box("Fence", -18.0, 18.0, 9.0, 9.12, 0.0, 1.8, M_FENCE)
for i, hx in enumerate([-12.5, -9.0, 10.5, 13.5]):
    box(f"Hedge{i}", hx - 1.4, hx + 1.4, 7.6, 8.8, 0.0, 1.1 + 0.2 * (i % 2), M_HEDGE)

# dirt plug: fills the hole until the dig; its top drops with the cutter
DIRT = prism("DirtPlug", [(P_HOLE[0][0], 0.0)] + P_HOLE[1:-1] + [(P_HOLE[-1][0], 0.0)], 0.0, PYH, M_GROUND)
CUT_DIG = cutter("CutDig", -1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
boolean(DIRT, CUT_DIG)
T_D0, T_D1 = C["digs"] - 0.15, C["pool"] + 0.45
dig_top = PW([(0, 0.02), (T_D0, 0.02), (T_D1, -3.4)])
for ax, v in ((0, 0.0), (1, PYH / 2)): CUT_DIG.location[ax] = v
CUT_DIG.scale = (12.0, PYH / 2 + 0.6, 1.0)
bake(CUT_DIG, "location", 2, [(-8.0 + dig_top(t)) / 2 for t in TS]); bake(CUT_DIG, "scale", 2, [(dig_top(t) + 8.0) / 2 for t in TS])
windows(DIRT, [(T_DIG, T_D1 + 0.1)])
# ghost outline of the pool inside the bigger hole (on "bigger")
GHOST = curve_obj("GhostOutline", [(x, -0.03, z) for x, z in P_OUT], 0.025, M_GHOST)
windows(GHOST, [(C["bigger"] - 0.1, C["next"])])

# excavator (generic, no driver visible): tracks, cab, boom + arm + bucket digging into the hole
EXC = bpy.data.objects.new("Excavator", None); CL.objects.link(EXC); EXC.location = (6.9, 1.6, 0.0)
box("ExcTracks", -1.3, 1.3, -1.0, 1.0, 0.0, 0.6, M_DARK, EXC)
SWING = bpy.data.objects.new("ExcSwing", None); CL.objects.link(SWING); SWING.parent = EXC; SWING.location = (0, 0, 0.6)
box("ExcBody", -1.1, 1.2, -0.9, 0.9, 0.0, 0.9, M_EXC, SWING); box("ExcCab", -0.9, 0.1, -0.9, -0.05, 0.9, 2.0, M_EXC, SWING)
box("ExcCabGlass", -0.92, 0.12, -0.93, -0.88, 1.15, 1.85, M_GLASS, SWING)
BOOM = bpy.data.objects.new("ExcBoom", None); CL.objects.link(BOOM); BOOM.parent = SWING; BOOM.location = (-0.9, 0.35, 0.7)
box("ExcBoomBeam", -3.0, 0.0, -0.15, 0.15, -0.15, 0.15, M_EXC, BOOM)
ARM = bpy.data.objects.new("ExcArm", None); CL.objects.link(ARM); ARM.parent = BOOM; ARM.location = (-3.0, 0, 0)
box("ExcArmBeam", -0.12, 0.12, -0.12, 0.12, -2.4, 0.0, M_EXC, ARM)
BUCKET = bpy.data.objects.new("ExcBucket", None); CL.objects.link(BUCKET); BUCKET.parent = ARM; BUCKET.location = (0, 0, -2.4)
bm = bmesh.new(); add_prism_y(bm, [(0.0, 0.1), (-0.65, 0.1), (-0.55, -0.45), (0.0, -0.35)], -0.38, 0.38); mesh_obj("ExcBucketShell", bm, M_DARK, BUCKET)
for o in (SWING, BOOM, ARM, BUCKET): o.rotation_mode = "XYZ"
cyc = lambda t, p: 0.5 - 0.5 * math.cos(2 * math.pi * t / p)
bake(BOOM, "rotation_euler", 1, [math.radians(-28 + 22 * cyc(t, 1.6) + 10 * lin((t - T_D0) / (T_D1 - T_D0))) for t in TS])
bake(ARM, "rotation_euler", 1, [math.radians(-10 + 25 * cyc(t + 0.4, 1.6)) for t in TS])
bake(BUCKET, "rotation_euler", 1, [math.radians(-20 + 60 * cyc(t + 0.8, 1.6)) for t in TS])
windows(EXC, [(T_DIG, C["next"] + 0.4)])
# dirt chunks flying up out of the hole
ME_DIRT = sphere_mesh("DirtChunk", 0.09, M_DIRT, 1)
for i in range(24):
    o = bpy.data.objects.new(f"Dirt{i}", ME_DIRT); CL.objects.link(o); o.scale = (random.uniform(0.8, 1.8),) * 3
    per, ph = random.uniform(0.9, 1.4), random.random(); x0 = random.uniform(-4.5, 4.5); y0 = random.uniform(0.1, 1.0)
    pts = []
    for t in TS:
        u = ((t / per) + ph) % 1.0; z0 = dig_top(t)
        pts.append(Vector((x0 + (6.5 - x0) * u * 0.35, y0 - 0.1, z0 + 2.6 * u - 2.4 * u * u)))
    bake_vec(o, "location", pts); windows(o, [(T_D0, T_D1)])

# ---------- steel cage (rebar) ----------
REBAR = []
P_RB = offset_line(P_SMOOTH, SH * 0.5); P_RB[0] = (P_RB[0][0], -0.08); P_RB[-1] = (P_RB[-1][0], -0.08)
at_rb, L_rb = path_fn([(x, 0, z) for x, z in P_RB])
def rb_part(x, z):
    if z > -0.95 and (x < -4.9 or x > 4.9): return "walls"
    return "floor"
T_STEEL = {"floor": C["floor"] - 0.9, "walls": C["walls"] - 0.25, "steps": C["steps"] - 0.25}
bars = []
# longitudinal bars (follow the profile) at several y, split into floor / wall pieces
for k, yy in enumerate([0.05 + 0.32 * j for j in range(int((PYO - 0.1) / 0.32) + 1)]):
    for part, sel in (("floor", lambda p: p[0] >= -5.0 and p[0] <= 5.0 and p[1] <= -0.95), ("walls", None)):
        if part == "floor":
            pts = [(x, yy, z) for x, z in P_RB if -5.2 <= x <= 5.2 and z < -0.9]
            pts = [(P_RB[1][0], yy, P_RB[1][1])] + pts[1:-1] + [(P_RB[-2][0], yy, P_RB[-2][1])] if len(pts) > 2 else pts
        else:
            for side, (a, b) in (("L", (P_RB[0], P_RB[1])), ("R", (P_RB[-2], P_RB[-1]))):
                bars.append(("walls", k * 0.03 + (0 if side == "L" else 0.15), [(a[0], yy, a[1]), (b[0], yy, b[1])]))
            continue
        bars.append(("floor", k * 0.04, pts))
# transverse bars (along y) every 0.35 m along the profile
n_tr = int(L_rb / 0.35)
for j in range(n_tr + 1):
    p = at_rb(j / n_tr); part = rb_part(p.x, p.z)
    bars.append((part, (p.x + 5.5) / 11 * 0.7, [(p.x, 0.02, p.z), (p.x, PY + SH * 0.5, p.z)]))
# back wall grid
for j in range(14):
    x = -4.9 + j * (9.8 / 13); zb = (-1.0 if x < -1.0 else -2.4 if x > 1.5 else -1.0 - 1.4 * (x + 1.0) / 2.5) - SH * 0.5
    bars.append(("walls", 0.3 + j * 0.04, [(x, PY + SH * 0.5, zb), (x, PY + SH * 0.5, -0.08)]))
for j, z in enumerate([-0.2, -0.55, -0.9, -1.25, -1.6, -1.95, -2.3]):
    xa = -4.9 if z > -1.0 else -1.0 + 2.5 * ((-1.0 - z) / 1.4)
    bars.append(("walls", 0.5 + j * 0.05, [(xa, PY + SH * 0.5, z), (4.9, PY + SH * 0.5, z)]))
# steps: bars along the treads
for k, (xa, xb, z) in enumerate([(-5.0, -4.6, -0.42), (-4.6, -4.2, -0.72), (-5.0, -4.2, -0.9)]):
    for j in range(5):
        yy = 0.1 + j * 0.6
        bars.append(("steps", k * 0.12 + j * 0.03, [(xa, yy, z), (xb, yy, z)]))
    bars.append(("steps", 0.2 + k * 0.1, [((xa + xb) / 2, 0.02, z), ((xa + xb) / 2, PY, z)]))
for i, (part, d, pts) in enumerate(bars):
    o = curve_obj(f"Rebar_{part}_{i}", pts, 0.022, M_REBAR, 2, parent=POOL); REBAR.append(o)
    t0 = T_STEEL[part] + d
    windows(o, [(t0, C["blasts"] + 6.0)])       # buried in the shell once it is sprayed (hidden as the shell covers it)
    key(o, "scale", F(t0), (1, 1, 1))
# ---------- shell (shotcrete), swept in behind the nozzle ----------
SHELL_POLY = [(P_OUT[0][0], 0.0)] + P_OUT[1:-1] + [(P_OUT[-1][0], 0.0)] + P_IN[::-1]
bm = bmesh.new(); add_prism_y(bm, SHELL_POLY, 0.0, PY)
add_prism_y(bm, [(P_OUT[0][0], 0.0)] + P_OUT[1:-1] + [(P_OUT[-1][0], 0.0)], PY, PYO)      # back wall
SHELL = mesh_obj("Shell", bm, M_SHELL, POOL)
CUT_SH = cutter("CutShell", -1.0, 1.0, -1.0, 1.0, -1.0, 1.0)
MD_SH = boolean(SHELL, CUT_SH)
T_S0, T_S1 = C["blasts"] - 0.1, C["shotcrete"] + 0.9
sweep = PW([(0, -6.0), (T_S0, -6.0), (T_S1, 6.0)])
spray_x = lambda t: -6.0 if t < T_DIG else sweep(t) if t < T_S1 + 0.1 else 6.0
CUT_SH.location = (0, PYO / 2, -1.0); CUT_SH.scale = (1.0, PYO / 2 + 0.5, 3.0)
bake(CUT_SH, "location", 0, [(-7.0 + (7.0 if t < T_DIG or t > T_S1 + 0.1 else spray_x(t))) / 2 for t in TS])
bake(CUT_SH, "scale", 0, [(7.0 + (7.0 if t < T_DIG or t > T_S1 + 0.1 else spray_x(t))) / 2 for t in TS])
windows(SHELL, after(T_S0))
for fr_, on in ((1, False), (F(T_S0 - 0.05), True), (F(T_S1 + 0.15), False)):     # the boolean only while the shell is being sprayed
    key(MD_SH, "show_render", fr_, on, "CONSTANT"); key(MD_SH, "show_viewport", fr_, on, "CONSTANT")
for o in REBAR:   # hide each bar once the shell has swept past it
    xm = sum(p.co.x for p in o.data.splines[0].points) / len(o.data.splines[0].points)
    tx = next((t for t in TS if t > T_S0 and spray_x(t) > xm + 0.4), T_S1)
    vis(o, F(tx), True)
# rough sprayed surface, troweled smooth on "smooths"
bump = M_SHELL_N.nodes["Bump"].inputs["Strength"]
key(bump, "default_value", 1, 0.25); key(bump, "default_value", F(T_DIG), 0.9, "CONSTANT")
key(bump, "default_value", F(C["smooths"] - 0.1), 0.9); key(bump, "default_value", F(C["hand"] + 0.3), 0.25)
# nozzle + hose (no person) riding along the sweep, spraying grey bits onto the steel
NOZ = bpy.data.objects.new("Nozzle", None); CL.objects.link(NOZ)
bm = bmesh.new(); add_cyl(bm, 0.09, 0.6, "Z", (0, 0, 0.3), 16, r2=0.06); mesh_obj("NozzleTip", bm, M_DARK, NOZ)
noz_pts = [Vector((max(-5.2, min(5.2, spray_x(t) - 0.3)), 0.8 + 0.25 * math.sin(t * 2.2), 1.6 + 0.15 * math.sin(t * 3.1))) for t in TS]
bake_vec(NOZ, "location", noz_pts)
def hooked_hose(name, fixed, tail, ob, radius=0.06):
    """Hose curve: fixed world points, then tail points (local to ob) hooked onto the moving nozzle."""
    o = curve_obj(name, fixed + tail, radius, M_HOSE)
    md = o.modifiers.new("Hook", "HOOK"); md.object = ob
    md.vertex_indices_set(list(range(len(fixed), len(fixed) + len(tail)))); return o
HOSE = hooked_hose("SprayHose", [(-14.0, 2.0, 0.2), (-8.0, 1.0, 1.0)], [(0, 0, 1.4), (0, 0, 0.5)], NOZ)
T_NZ = (C["hose"] - 0.15, T_S1 + 0.2)
windows(NOZ, [T_NZ]); windows(HOSE, [T_NZ])
ME_SPR = sphere_mesh("SprayBit", 0.075, M_SPRAY, 1)
for i in range(48):
    o = bpy.data.objects.new(f"Spray{i}", ME_SPR); CL.objects.link(o)
    per, ph = random.uniform(0.35, 0.55), random.random(); jy, jx = random.uniform(-0.6, 0.6), random.uniform(-0.6, 0.5)
    pts = []
    for fr, t in enumerate(TS):
        u = ((t / per) + ph) % 1.0; n0 = noz_pts[fr]; xx = n0.x + 0.3 + jx
        zt = next((z for (x0, z0), (x1, z1) in zip(P_IN, P_IN[1:]) for z in [z0 + (z1 - z0) * ((xx - x0) / (x1 - x0)) if x1 != x0 else min(z0, z1)] if min(x0, x1) <= xx <= max(x0, x1)), -1.0)
        tgt = Vector((xx, max(0.15, n0.y + jy), zt + 0.05))
        pts.append(n0.lerp(tgt, u))
    bake_vec(o, "location", pts); windows(o, [(T_S0, T_S1)])
# curing: soft mist puffs over the shell
ME_MIST = sphere_mesh("MistPuff", 0.12, M_MIST, 2)
T_CU0, T_CU1 = C["then2"], C["tile"] - 0.1
for i in range(26):
    o = bpy.data.objects.new(f"Mist{i}", ME_MIST); CL.objects.link(o)
    x0 = random.uniform(-4.8, 4.8); zf = -1.0 if x0 < -1.0 else -2.4 if x0 > 1.5 else -1.0 - 1.4 * (x0 + 1.0) / 2.5
    per, ph = random.uniform(1.0, 1.6), random.random(); y0 = random.uniform(0.3, 2.3)
    pts, sc = [], []
    for t in TS:
        u = ((t / per) + ph) % 1.0; pts.append(Vector((x0, y0, zf + 1.4 - 1.3 * u))); sc.append(0.6 + 0.8 * u)
    bake_vec(o, "location", pts)
    for ax in range(3): bake(o, "scale", ax, sc)
    windows(o, [(T_CU0, T_CU1)])
# ---------- finishes: tile band, coping + deck, plaster ----------
tile = bmesh.new()
add_box(tile, -5.0, 5.0, PY - 0.02, PY, -0.3, 0.0); add_box(tile, 4.98, 5.0, 0.0, PY, -0.3, 0.0); add_box(tile, -5.0, -4.98, 0.0, PY, -0.3, 0.0)
TILE = mesh_obj("WaterlineTile", tile, M_TILE, POOL)
windows(TILE, after(C["tile"] - 0.1))
cp = bmesh.new()
add_box(cp, P_OUT[0][0] - 0.05, P_OUT[-1][0] + 0.05, PY - 0.06, PYO + 0.1, 0.0, 0.08)
add_box(cp, P_OUT[0][0] - 0.05, -4.94, 0.0, PY, 0.0, 0.08); add_box(cp, 4.94, P_OUT[-1][0] + 0.05, 0.0, PY, 0.0, 0.08)
COPING = mesh_obj("Coping", cp, M_COPING, POOL); bevel_mod(COPING, 0.015, 2)
windows(COPING, after(C["coping"] - 0.1))
dk = bmesh.new()
add_box(dk, -7.2, P_OUT[0][0] - 0.05, 0.0, PYO + 1.6, 0.0, 0.05); add_box(dk, P_OUT[-1][0] + 0.05, 7.0, 0.0, PYO + 1.6, 0.0, 0.05)
add_box(dk, P_OUT[0][0] - 0.05, P_OUT[-1][0] + 0.05, PYO + 0.1, PYO + 1.6, 0.0, 0.05)
DECK = mesh_obj("Deck", dk, M_DECK)
windows(DECK, after(C["edge"] - 0.1))
windows(BACKFILL, after(C["coping"] - 0.1))
pl = bmesh.new()
add_prism_y(pl, P_IN + P_PL[::-1], 0.0, PY - 0.02)
add_prism_y(pl, [(x, z) for x, z in P_PL], PY - 0.055, PY - 0.02)
PLASTER = mesh_obj("Plaster", pl, M_PLASTER, POOL)
T_PL = C["plaster"] - 0.1
windows(PLASTER, [(0.0, T_DIG), (T_PL, C["bare"] - 0.05), (C["fill"] - 0.2, T_B1), (T_CTA, DUR + 1)])
# seeping drops through the bare shell into the soil (red glow on the shell while bare)
ME_SEEP = sphere_mesh("SeepDrop", 0.07, M_SEEP, 1)
T_SE0, T_SE1 = C["bare"], C["fill"] - 0.2
for i in range(18):
    o = bpy.data.objects.new(f"Seep{i}", ME_SEEP); CL.objects.link(o)
    side = random.random()
    if side < 0.5: a = Vector((random.uniform(2.0, 4.8), 0.03, -2.38)); b = a + Vector((random.uniform(-0.2, 0.2), 0, -0.9))
    else: a = Vector((4.98, 0.03, random.uniform(-2.2, -0.6))); b = a + Vector((0.9, 0, random.uniform(-0.3, 0.1)))
    per, ph = random.uniform(1.2, 1.8), random.random()
    bake_vec(o, "location", [a.lerp(b, ((t / per) + ph) % 1.0) for t in TS]); windows(o, [(T_SE0, T_SE1)])
# ---------- water (boolean against a level cutter) ----------
WATER = prism("PoolWater", P_PL, 0.0, PY - 0.055, M_WATER, POOL)
CUT_W = cutter("CutWater", -1.0, 1.0, -1.0, 1.0, -1.0, 1.0); CUT_W.location = (0, 0, 0); CUT_W.scale = (8.0, 6.0, 1.0)
boolean(WATER, CUT_W)
T_F0, T_F1 = C["fill"] - 0.1, C["loop"] + 0.2
T_E0, T_E1 = C["drain3"] - 0.1, C["groundwater"] + 0.9
T_V0, T_V1 = C["lets2"], C["in"] + 0.6
def wlev(t):
    if t < T_DIG or t >= T_CTA: return WL
    if t < T_F0: return -3.0
    if t < T_E0: return -3.0 + (WL + 3.0) * ease((t - T_F0) / (T_F1 - T_F0))
    if t < C["thats"] - 0.05: return WL + (-2.6 - WL) * ease((t - T_E0) / (T_E1 - T_E0))
    return -2.6 + 0.5 * ease((t - T_V0) / (T_V1 - T_V0))
bake(CUT_W, "location", 2, [(-8.0 + wlev(t)) / 2 for t in TS]); bake(CUT_W, "scale", 2, [(wlev(t) + 8.0) / 2 for t in TS])
windows(WATER, [(0.0, T_DIG), (T_F0, T_B0), (T_CTA, DUR + 1)])

# ---------- plumbing: main drain + relief valve, skimmer, return jets, pipes, pump + filter ----------
X_DR = 3.4
bm = bmesh.new(); add_cyl(bm, 0.28, 0.03, "Z", (X_DR, 0.35, -2.385), 32); DRAIN = mesh_obj("MainDrain", bm, M_GRATE, POOL)
bm = bmesh.new(); add_cyl(bm, 0.12, 0.3, "Z", (X_DR, 0.35, -2.55), 24); mesh_obj("DrainSump", bm, M_PVC, POOL)
bm = bmesh.new(); add_cyl(bm, 0.07, 0.16, "Z", (X_DR - 0.55, 0.02, -2.72), 20); add_cyl(bm, 0.1, 0.05, "Z", (X_DR - 0.55, 0.02, -2.62), 20)
VALVE = mesh_obj("ReliefValve", bm, M_VALVE, POOL)
SK_X0, SK_X1 = 5.0, 5.55
bm = bmesh.new()
add_box(bm, SK_X0 - 0.02, SK_X1, 0.0, 0.03, -0.55, 0.0); add_box(bm, SK_X0 - 0.02, SK_X1, 0.5, 0.53, -0.55, 0.0)
add_box(bm, SK_X1 - 0.03, SK_X1, 0.0, 0.53, -0.55, 0.0); add_box(bm, SK_X0 - 0.02, SK_X1, 0.0, 0.53, -0.58, -0.55)
add_box(bm, SK_X0 - 0.02, SK_X1, 0.0, 0.53, 0.0, 0.03)
SKIM = mesh_obj("Skimmer", bm, M_SKIM, POOL)
JETS = []
for i, (x, y, z, ax) in enumerate([(-2.2, PY - 0.02, -0.5, "Y"), (1.8, PY - 0.02, -0.5, "Y"), (-5.0, 0.6, -0.55, "X")]):
    bm = bmesh.new(); add_cyl(bm, 0.07, 0.12, ax, (x + (0.04 if ax == "X" else 0), y, z), 20); JETS.append(mesh_obj(f"ReturnJet{i}", bm, M_JET, POOL))
# pipes in the cut plane (half proud of the cut face so they read)
P_SUC_DR = [(X_DR, 0.0, -2.55), (X_DR, 0.0, -2.92), (6.0, 0.0, -2.92), (6.0, 0.0, -0.75), (7.9, 0.0, -0.75), (7.9, 0.0, 0.3), (7.9, 0.45, 0.3)]
P_SUC_SK = [(5.3, 0.0, -0.58), (5.3, 0.0, -0.75), (7.9, 0.0, -0.75)]
P_PF = [(8.25, 0.45, 0.32), (9.0, 0.45, 0.32)]
P_RET = [(9.3, 0.45, 0.25), (9.75, 0.45, 0.25), (9.75, 0.0, 0.25), (9.75, 0.0, -3.25), (-5.75, 0.0, -3.25), (-5.75, 0.0, -0.55), (-4.98, 0.0, -0.55)]
PIPES = [curve_obj("SuctionDrainPipe", P_SUC_DR, 0.06, M_PVC), curve_obj("SuctionSkimPipe", P_SUC_SK, 0.06, M_PVC),
         curve_obj("PumpFilterPipe", P_PF, 0.06, M_PVC), curve_obj("ReturnPipe", P_RET, 0.06, M_RET)]
DRAIN_LEAD = curve_obj("DrainLead", [(X_DR, 0.35, -2.55), (X_DR, 0.0, -2.55)], 0.06, M_PVC, parent=POOL)
VALVE_LEAD = curve_obj("ValveLead", [(X_DR - 0.55, 0.02, -2.64), (X_DR - 0.55, 0.02, -2.55), (X_DR, 0.02, -2.55)], 0.04, M_PVC, parent=POOL)
# equipment pad, pump, filter (generic shapes, no brands)
PAD = box("EquipPad", X_PAD - 1.2, X_PAD + 1.4, 0.0, 1.4, 0.0, 0.12, M_PAD)
EQ = bpy.data.objects.new("Equipment", None); CL.objects.link(EQ)
bm = bmesh.new(); add_cyl(bm, 0.22, 0.42, "Z", (7.9, 0.45, 0.42), 28); add_cyl(bm, 0.24, 0.05, "Z", (7.9, 0.45, 0.65), 28)
PUMP = mesh_obj("PumpHousing", bm, M_PUMP, EQ)
bm = bmesh.new(); add_cyl(bm, 0.2, 0.55, "X", (7.5, 0.45, 0.35), 28); mesh_obj("PumpMotor", bm, M_MOTOR, EQ)
bm = bmesh.new(); add_cyl(bm, 0.34, 1.0, "Z", (9.3, 0.45, 0.62), 36); FILTER = mesh_obj("FilterTank", bm, M_FILTER, EQ)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=36, v_segments=12, radius=0.34)
bmesh.ops.scale(bm, verts=bm.verts, vec=(1, 1, 0.5)); bmesh.ops.translate(bm, verts=bm.verts, vec=(9.3, 0.45, 1.12)); mesh_obj("FilterDome", bm, M_FILTER, EQ)
bm = bmesh.new(); add_cyl(bm, 0.05, 0.2, "Z", (9.3, 0.45, 1.36), 12); mesh_obj("FilterGauge", bm, M_DARK, EQ)
T_PLB = C["plumbing"] - 0.1
for o in [DRAIN, VALVE, DRAIN_LEAD, VALVE_LEAD, bpy.data.objects["DrainSump"]]: windows(o, after(C["drain"] - 0.15))
windows(SKIM, after(C["skimmer"] - 0.15))
for o in JETS: windows(o, after(C["jets"] - 0.2))
windows(PIPES[0], after(C["drain"] - 0.15)); windows(PIPES[1], after(C["skimmer"] - 0.15))
windows(PIPES[2], after(T_PLB)); windows(PIPES[3], after(C["jets"] - 0.2))
windows(EQ, after(T_PLB)); windows(PAD, after(T_PLB))

# ---------- the loop: suction (gold) from drain + skimmer to the pump, filter, return (cyan) to the jets ----------
at_sd, L_sd = path_fn([(X_DR, -0.1, -2.42)] + [(x, -0.08, z) for x, _, z in P_SUC_DR])
at_ss, L_ss = path_fn([(5.25, -0.08, -0.25)] + [(x, -0.08, z) for x, _, z in P_SUC_SK] + [(7.9, -0.08, 0.3)])
at_pf, L_pf = path_fn([(7.9, -0.05, 0.42), (8.3, -0.05, 0.32), (9.3, -0.05, 0.32), (9.3, -0.05, 0.9)])
at_rt, L_rt = path_fn([(9.3, -0.08, 0.25)] + [(x, -0.08, z) for x, _, z in P_RET[2:]] + [(-3.8, -0.08, -0.55)])
ME_PIN, ME_POUT = sphere_mesh("PulseInMesh", 0.075, M_IN), sphere_mesh("PulseOutMesh", 0.075, M_OUT)
T_LP0 = C["loop"] - 0.1
W_LOOP = [(T_LP0, C["heres"] - 0.05), (T_CTA + 0.2, DUR + 1)]
for name, (at, L), n, me, speed, wins in [("SucDrain", (at_sd, L_sd), 12, ME_PIN, 2.4, [(C["pulls"] - 0.2, C["heres"] - 0.05), (T_CTA + 0.2, DUR + 1)]),
                                           ("SucSkim", (at_ss, L_ss), 7, ME_PIN, 2.4, [(C["skimmer2"] - 0.2, C["heres"] - 0.05), (T_CTA + 0.2, DUR + 1)]),
                                           ("PumpFilter", (at_pf, L_pf), 5, ME_PIN, 1.6, [(C["pushes"] - 0.1, C["heres"] - 0.05), (T_CTA + 0.2, DUR + 1)]),
                                           ("Return", (at_rt, L_rt), 22, ME_POUT, 3.4, [(C["sends"] - 0.1, C["heres"] - 0.05), (T_CTA + 0.2, DUR + 1)])]:
    for i in range(n):
        o = bpy.data.objects.new(f"Pulse{name}{i}", me); CL.objects.link(o)
        bake_vec(o, "location", [at(((t * speed / L) + i / n) % 1.0) for t in TS]); windows(o, wins)
# return jets pushing water back in (cyan streaks from the back-wall jets)
ME_JS = sphere_mesh("JetStreak", 0.05, M_OUT, 1)
for j, (x, y, z) in enumerate([(-2.2, PY - 0.08, -0.5), (1.8, PY - 0.08, -0.5)]):
    for i in range(6):
        o = bpy.data.objects.new(f"JetStream{j}_{i}", ME_JS); CL.objects.link(o); ph = i / 6
        bake_vec(o, "location", [Vector((x + 1.4 * (((t * 1.2) + ph) % 1.0), y - 1.6 * (((t * 1.2) + ph) % 1.0), z - 0.25 * (((t * 1.2) + ph) % 1.0))) for t in TS])
        windows(o, [(C["jets2"] - 0.4, C["heres"] - 0.05), (T_CTA + 0.2, DUR + 1)])

# ---------- the scary part: groundwater rises, the empty pool floats up; then the relief valve ----------
T_GW0, T_GW1 = C["groundwater"] - 0.2, C["high"] + 0.4
gw = PW([(0, -100.0), (T_GW0 - 0.01, -100.0), (T_GW0, -6.5), (T_GW1, -0.9), (T_B0 - 0.01, -0.9), (T_B0, -100.0)])   # -100 = off (below the ground block)
for n in GW_NODES: bake_value(n, [gw(t) for t in TS])
T_FL0, T_FL1 = C["float"] - 0.1, C["ground"] + 0.5
lift = PW([(0, 0.0), (T_FL0, 0.0), (T_FL1, 1.7)])
tilt = PW([(0, 0.0), (T_FL0, 0.0), (T_FL1, math.radians(3.5))])
bake(POOL, "location", 2, [lift(t) if t < C["thats"] - 0.05 else 0.0 for t in TS])
bake(POOL, "rotation_euler", 1, [tilt(t) if t < C["thats"] - 0.05 else 0.0 for t in TS])
ME_PA = arrow_mesh("PressureArrowMesh", 1.0, M_ARROW, 0.05, 0.25)
for i, x in enumerate([-4.0, -2.0, 0.0, 2.0, 4.0]):
    o = bpy.data.objects.new(f"UpliftArrow{i}", ME_PA); CL.objects.link(o); o.rotation_euler = (0, math.radians(-90), 0)
    zb = (-1.0 if x < -1.0 else -2.4 if x > 1.5 else -1.0 - 1.4 * (x + 1.0) / 2.5) - SH - 1.4
    bake(o, "location", 2, [zb + lift(t) + 0.15 * math.sin(t * 6 + i) for t in TS]); o.location[0] = x; o.location[1] = -0.1
    windows(o, [(C["high"] - 0.1, C["thats"] - 0.05)])
# relief valve: groundwater pushes up through the valve into the pool (cyan pulses)
at_v, L_v = path_fn([(X_DR - 0.55, -0.1, -3.6), (X_DR - 0.55, -0.1, -2.65), (X_DR - 0.55, -0.1, -2.3), (X_DR - 0.3, 0.3, -1.6)])
for i in range(8):
    o = bpy.data.objects.new(f"ValveFlow{i}", ME_POUT); CL.objects.link(o)
    bake_vec(o, "location", [at_v(((t * 1.6 / L_v) + i / 8) % 1.0) for t in TS]); windows(o, [(C["lets2"] - 0.1, T_B0)])

# ---------- front half (mirror) for the hook: drops away on "open" ----------
FRONT = bpy.data.objects.new("FrontHalf", None); CL.objects.link(FRONT); FRONT.scale = (1, -1, 1)
for src in [GROUND, SHELL, PLASTER, TILE, COPING, DECK, BACKFILL, WATER, bpy.data.objects["Ground_Back"]]:
    o = src.copy(); CL.objects.link(o); o.parent = FRONT; o.matrix_parent_inverse = Matrix.Identity(4)
    o.animation_data_clear()
    for md in list(o.modifiers):
        if md.type == "BOOLEAN" and md.object is CUT_DIG: o.modifiers.remove(md)
FRONT_LOC = PW([(0, 0.0), (T_OPEN - 0.05, 0.0), (T_OPEN + 0.8, -14.0)])
bake(FRONT, "location", 2, [FRONT_LOC(t) for t in TS]); bake(FRONT, "location", 1, [-1.2 * lin((t - T_OPEN) / 0.8) for t in TS])
windows(FRONT, [(0.0, T_OPEN + 0.85)])

# ---------- Set C: the beam demo (x = -1000) ----------
OC = -1000.0
box("C_Floor", OC - 14, OC + 14, -8, 6, -0.6, -0.5, M_STUDIO); box("C_Backdrop", OC - 14, OC + 14, 6.0, 6.2, -0.6, 14.0, M_STUDIO)
BL, BR = box("C_BeamL", -1.5, 0.0, -0.22, 0.22, 0.0, 0.44, M_BEAM), box("C_BeamR", 0.0, 1.5, -0.22, 0.22, 0.0, 0.44, M_BEAM)   # origin at the crack
bevel_mod(BL, 0.01, 1); bevel_mod(BR, 0.01, 1)
T_SQ, T_PU, T_ST = C["squeezed"] - 0.2, C["pulled"] - 0.15, C["steel2"] - 0.1
gap = PW([(0, 0.0), (T_PU, 0.0), (T_PU + 0.35, 0.32)])
sq = PW([(0, 0.0), (T_SQ, 0.0), (T_SQ + 0.3, 0.03), (C["but"], 0.03), (C["but"] + 0.25, 0.0)])
bake(BL, "location", 0, [OC - gap(t) + sq(t) for t in TS]); bake(BR, "location", 0, [OC + gap(t) - sq(t) for t in TS])
bake(BL, "rotation_euler", 1, [math.radians(4) * lin((t - T_PU) / 0.35) for t in TS]); bake(BR, "rotation_euler", 1, [math.radians(-4) * lin((t - T_PU) / 0.35) for t in TS])
windows(BL, [(T_BEAM0, T_ST)]); windows(BR, [(T_BEAM0, T_ST)])
CRACK = box("C_Crack", OC - 0.04, OC + 0.04, -0.24, 0.24, 0.0, 0.44, M_CRACK); windows(CRACK, [(T_PU, T_PU + 0.35)])
B2 = box("C_BeamSteel", OC - 1.5, OC + 1.5, -0.22, 0.22, 0.0, 0.44, M_BEAM); bevel_mod(B2, 0.01, 1)
B2_CUT = cutter("C_BeamCutaway", OC - 2, OC + 2, -1.0, 0.0, 0.3, 1.0)       # cut a notch off the front-top so the bar reads
boolean(B2, B2_CUT, "DIFFERENCE")
RB2 = curve_obj("C_SteelBar", [(OC - 1.7, -0.05, 0.16), (OC + 1.7, -0.05, 0.16)], 0.04, M_REBAR)
windows(B2, [(T_ST, T_BEAM1)]); windows(RB2, [(T_ST, T_BEAM1)])
ME_CA = arrow_mesh("BeamArrowMesh", 0.9, M_SQZ, 0.05, 0.25); ME_CP = arrow_mesh("PullArrowMesh", 0.9, M_PULL, 0.05, 0.25)
for side in (-1, 1):
    a = bpy.data.objects.new(f"C_SqueezeArrow{side}", ME_CA); CL.objects.link(a)
    a.location = (OC + side * 2.6, 0, 0.22); a.rotation_euler = (0, 0, 0 if side < 0 else math.pi)
    bake(a, "location", 0, [OC + side * (2.3 - 0.25 * ease((t - T_SQ) / 0.3)) for t in TS]); windows(a, [(T_SQ, C["but"])])
    p = bpy.data.objects.new(f"C_PullArrow{side}", ME_CP); CL.objects.link(p)
    p.location = (OC + side * 1.7, 0, 0.22); p.rotation_euler = (0, 0, math.pi if side < 0 else 0)
    bake(p, "location", 0, [OC + side * (1.7 + 0.2 * ease((t - T_PU + 0.1) / 0.3) + (0.32 if t > T_PU and t < T_ST else 0)) for t in TS])
    windows(p, [(C["cracks"] - 0.1, T_BEAM1)])

# ---------- Set B: early-1900s museum facade + two-chamber cement gun (x = 2000) ----------
OX = 2000.0
box("B_Street", OX - 20, OX + 20, -14, 14, -0.1, 0.0, M_STREET)
box("B_FacadeWall", OX - 7, OX + 7, 3.0, 4.0, 0.0, 8.0, M_FACADE)
bm = bmesh.new(); add_prism_y(bm, [(OX - 7.6, 8.0), (OX + 7.6, 8.0), (OX, 10.4)], 2.4, 3.6); mesh_obj("B_Pediment", bm, M_FACADE)
box("B_Entablature", OX - 7.6, OX + 7.6, 2.4, 3.6, 7.2, 8.0, M_FACADE)
for i in range(6):
    bm = bmesh.new(); add_cyl(bm, 0.38, 6.6, "Z", (OX - 5.5 + i * 2.2, 2.9, 0.6 + 3.3), 32); mesh_obj(f"B_Column{i}", bm, M_FACADE)
for k in range(3): box(f"B_Step{k}", OX - 7.8 + k * 0.3, OX + 7.8 - k * 0.3, 1.6 + k * 0.3, 3.2, 0.2 * k, 0.2 * (k + 1), M_FACADE)
PATCH = box("B_FreshPlaster", OX - 6.9, OX + 6.9, 2.97, 3.0, 0.62, 7.2, M_PATCH)
CUT_P = cutter("B_PatchCutter", -1.0, 1.0, -1.0, 1.0, -1.0, 1.0); CUT_P.location = (OX, 3.0, 0.0); CUT_P.scale = (8.0, 1.0, 1.0)
boolean(PATCH, CUT_P)
T_PA0, T_PA1 = C["gun"] - 0.2, C["would"] - 0.1
ptop = PW([(0, 0.62), (T_PA0, 0.62), (T_PA1, 7.2)])
bake(CUT_P, "location", 2, [(0.0 + ptop(t)) / 2 for t in TS]); bake(CUT_P, "scale", 2, [max(0.01, ptop(t) / 2) for t in TS])
GUN = bpy.data.objects.new("B_CementGun", None); CL.objects.link(GUN); GUN.location = (OX + 3.0, -3.0, 0.0)
box("B_CartDeck", -0.9, 0.9, -0.6, 0.6, 0.45, 0.6, M_WOOD, GUN)
for wx in (-0.7, 0.7):
    for wy in (-0.65, 0.65):
        bm = bmesh.new(); add_cyl(bm, 0.38, 0.08, "Y", (wx, wy, 0.38), 24); mesh_obj(f"B_Wheel{wx}{wy}", bm, M_DARK, GUN)
bm = bmesh.new(); add_cyl(bm, 0.42, 0.9, "Z", (0, 0, 1.05), 32); add_cyl(bm, 0.42, 0.9, "Z", (0, 0, 2.0), 32)
add_cyl(bm, 0.46, 0.06, "Z", (0, 0, 1.52), 32); add_cyl(bm, 0.25, 0.12, "Z", (0, 0, 2.5), 24)
mesh_obj("B_GunChambers", bm, M_GUN, GUN)
bm = bmesh.new(); add_cyl(bm, 0.12, 0.05, "Y", (0.0, -0.44, 1.9), 20); mesh_obj("B_Gauge", bm, M_PLASTER, GUN)
B_NOZ = [Vector((OX - 3.0 + 4.5 * cyc(t, 3.0), 1.2, 1.2 + 5.2 * lin((t - T_PA0) / (T_PA1 - T_PA0)))) for t in TS]
B_NOZZLE = bpy.data.objects.new("B_Nozzle", None); CL.objects.link(B_NOZZLE); bake_vec(B_NOZZLE, "location", B_NOZ)
bm = bmesh.new(); add_cyl(bm, 0.07, 0.45, "Y", (0, 0, 0), 16, r2=0.05); mesh_obj("B_NozzleTip", bm, M_DARK, B_NOZZLE)
hooked_hose("B_GunHose", [(OX + 3.0, -3.0, 2.5), (OX + 2.4, -2.6, 0.2), (OX - 0.5, -0.8, 0.2)], [(0, -0.9, -0.2), (0, -0.25, 0)], B_NOZZLE, 0.07)
for i in range(22):
    o = bpy.data.objects.new(f"B_Spray{i}", ME_SPR); CL.objects.link(o); per, ph = random.uniform(0.3, 0.5), random.random()
    jx, jz = random.uniform(-0.5, 0.5), random.uniform(-0.4, 0.4)
    bake_vec(o, "location", [B_NOZ[fr].lerp(Vector((B_NOZ[fr].x + jx, 2.9, B_NOZ[fr].z + jz)), ((t / per) + ph) % 1.0) for fr, t in enumerate(TS)])
    windows(o, [(T_PA0, T_PA1)])

# ---------- highlights ----------
def pulse(bsdf, t0, peak=2.5, hold=0.9, rgb=None):
    s = bsdf.inputs["Emission Strength"]
    if rgb: bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
    key(s, "default_value", F(t0 - 0.15), 0.0); key(s, "default_value", F(t0 + 0.12), peak)
    key(s, "default_value", F(t0 + hold), peak * 0.6); key(s, "default_value", F(t0 + hold + 0.5), 0.0)
def hold_glow(bsdf, t0, t1, peak, base=0.0):
    s = bsdf.inputs["Emission Strength"]
    key(s, "default_value", F(t0 - 0.15), base); key(s, "default_value", F(t0 + 0.15), peak)
    key(s, "default_value", F(t1), peak); key(s, "default_value", F(t1 + 0.4), base)
hold_glow(B_REBAR, C["steel"], C["concrete"] - 0.1, 1.2)
hold_glow(B_GRATE, C["drain"], C["skimmer"] - 0.1, 3.0)
hold_glow(B_SKIM, C["skimmer"], C["return"] - 0.1, 1.2)
hold_glow(B_JET, C["return"], C["now"], 3.0)
hold_glow(B_SHELL, C["dry"], C["shotcrete"] + 0.6, 0.25)
hold_glow(B_TILE, C["tile"], C["coping"] - 0.1, 0.6)
hold_glow(B_COPING, C["coping"], C["plaster"] - 0.1, 0.8)
hold_glow(B_PLASTER, C["plaster"], C["because"], 0.6)
pulse(B_SHELL, C["bare"], 0.5, 1.6, RED)
hold_glow(B_PUMP, C["pump"], C["filter"] - 0.1, 1.5)
hold_glow(B_FILTER, C["filter"], C["sends"], 0.8)
hold_glow(B_RET, C["sends"], C["heres"], 1.5)
hold_glow(B_VALVE, C["relief"], C["and"], 4.0)
hold_glow(B_GUN, C["gun"], C["taxidermist"], 1.2)
hold_glow(B_PATCH, C["replaster"], C["chicago"] + 0.3, 0.35)
s = B_SHELL.inputs["Emission Strength"]
key(s, "default_value", F(C["float"] - 0.2), 0.0); key(s, "default_value", F(C["float"] + 0.1), 0.0)
B_SHELL.inputs["Emission Color"].default_value = (*GOLD, 1)
key(B_SHELL.inputs["Emission Color"], "default_value", F(C["bare"] - 0.2), (*GOLD, 1), "CONSTANT")
key(B_SHELL.inputs["Emission Color"], "default_value", F(C["bare"] - 0.15), (*RED, 1), "CONSTANT")
key(B_SHELL.inputs["Emission Color"], "default_value", F(C["fill"]), (*RED, 1), "CONSTANT")
pulse(B_SHELL, C["float"], 0.5, 1.2, None)

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 35
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 11; cam_d.dof.focus_object = TGT
cam_d.clip_start = 0.05; cam_d.clip_end = 600
SHOTS = [  # (time, cam, target, lens[, "cut"])
    (0.0, (-4.5, -9.5, 6.0), (0.0, 1.2, -0.7), 22),
    (C["built"], (-3.0, -9.0, 4.0), (0.0, 1.0, -0.9), 22),
    (C["open"] - 0.1, (0.0, -14.0, 2.6), (0.0, 1.0, -1.3), 22),
    (T_DIG, (3.6, -13.5, 3.8), (3.2, 1.0, -1.0), 22, "cut"),
    (C["bigger"] - 0.2, (0.0, -13.0, 2.4), (0.0, 1.0, -1.4), 22),
    (C["next"], (-1.0, -11.5, 4.0), (0.0, 1.2, -1.4), 22),
    (C["floor"] - 0.2, (1.5, -7.5, 0.9), (2.2, 1.2, -2.2), 24),
    (C["walls"] - 0.1, (3.5, -7.5, 1.4), (4.6, 1.4, -1.3), 24),
    (C["steps"] + 0.15, (-4.0, -6.0, 0.9), (-4.5, 1.0, -0.7), 24),
    (T_BEAM0, (OC + 0.5, -6.2, 1.5), (OC, 0.0, 0.2), 22, "cut"),
    (C["steel2"], (OC + 0.3, -6.4, 1.4), (OC, 0.0, 0.2), 22),
    (T_BEAM1, (1.5, -13.5, 1.8), (2.0, 0.8, -1.3), 22, "cut"),
    (C["drain"] - 0.2, (3.2, -5.8, -0.9), (3.3, 0.5, -2.4), 24),
    (C["skimmer"] - 0.2, (5.0, -5.4, 0.6), (5.4, 0.3, -0.4), 24),
    (C["return"] - 0.2, (-1.0, -9.0, 0.8), (-2.5, 1.8, -0.6), 22),
    (C["now"], (0.0, -12.5, 3.0), (0.0, 1.0, -1.2), 22),
    (C["hose"] - 0.1, (-3.0, -9.0, 2.6), (-2.8, 1.0, -1.0), 22),
    (C["steel3"], (0.0, -9.5, 2.2), (0.0, 1.0, -1.5), 22),
    (C["shotcrete"], (3.0, -9.5, 2.2), (3.0, 1.0, -1.8), 22),
    (C["smooths"] - 0.2, (2.0, -6.0, 0.6), (2.6, 1.3, -1.8), 24),
    (C["then2"], (0.0, -11.5, 2.6), (0.0, 1.0, -1.2), 22),
    (C["tile"] - 0.2, (3.0, -7.0, 0.8), (3.4, 2.4, -0.3), 24),
    (C["coping"] - 0.2, (-3.0, -8.0, 2.8), (-2.2, 2.2, 0.0), 24),
    (C["plaster"] - 0.2, (0.0, -10.5, 1.6), (0.0, 1.2, -1.3), 22),
    (C["because"] - 0.1, (4.2, -6.4, -0.5), (4.6, 0.4, -1.9), 24),
    (C["fill"] - 0.2, (0.0, -12.5, 2.4), (0.0, 1.0, -1.2), 22),
    (C["pump"] - 0.2, (5.5, -11.0, 2.2), (5.8, 0.4, -1.0), 22),
    (C["pushes"] + 0.2, (8.4, -5.8, 1.6), (8.7, 0.5, 0.4), 26),
    (C["sends"] + 0.4, (0.0, -12.5, 1.6), (0.0, 1.0, -1.3), 22),
    (C["heres"] - 0.1, (0.0, -13.5, 3.0), (0.0, 1.0, -1.5), 22),
    (C["groundwater"] - 0.2, (0.0, -16.0, 1.2), (0.0, 1.0, -2.6), 22),
    (C["float"] - 0.2, (0.0, -15.0, 1.0), (0.0, 1.0, -1.6), 22),
    (C["thats"] - 0.05, (3.0, -7.0, -1.3), (3.0, 0.3, -2.6), 24, "cut"),
    (C["lets2"], (2.6, -6.4, -1.6), (2.9, 0.3, -2.8), 24),
    (T_B0, (OX - 5.0, -15.0, 3.5), (OX - 0.5, 2.0, 3.4), 22, "cut"),
    (C["akeley"] - 0.2, (OX + 1.0, -9.0, 2.6), (OX + 0.8, 0.5, 2.6), 24),
    (C["museum"] - 0.2, (OX, -17.0, 4.6), (OX, 2.0, 4.6), 22),
    (T_CTA, (-6.0, -12.0, 6.5), (0.0, 1.2, -0.9), 22, "cut"),
    (C["end"], (-7.5, -14.5, 8.0), (0.0, 1.2, -0.9), 22),
]
cam_loc, cam_tgt, cam_lens = [], [], []
for t in TS:
    k = max(i for i, s in enumerate(SHOTS) if s[0] <= t + 1e-6)
    l0, g0, n0 = Vector(SHOTS[k][1]), Vector(SHOTS[k][2]), SHOTS[k][3]
    if k + 1 < len(SHOTS) and not (len(SHOTS[k + 1]) > 4 and SHOTS[k + 1][4] == "cut"):
        t1 = SHOTS[k + 1][0]; tr = 0.7 if (t1 - SHOTS[k][0]) > 1.4 else (t1 - SHOTS[k][0]) * 0.5
        if t > t1 - tr:
            u = ease((t - (t1 - tr)) / tr)
            l0, g0, n0 = l0.lerp(Vector(SHOTS[k + 1][1]), u), g0.lerp(Vector(SHOTS[k + 1][2]), u), n0 + (SHOTS[k + 1][3] - n0) * u
    cam_loc.append(l0 + Vector((0.06 * math.sin(t * 0.7), 0.0, 0.04 * math.sin(t * 0.9 + 1.0)))); cam_tgt.append(g0); cam_lens.append(n0)
for ax in range(3):
    bake(cam, "location", ax, [v[ax] for v in cam_loc]); bake(TGT, "location", ax, [v[ax] for v in cam_tgt])
bake(cam_d, "lens", -1, cam_lens)

# ---------- world + lights: daylight sky (Poly Haven HDRI) + sun; Set C keeps a darker studio feel via its own key ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
bg = next(n for n in wn if n.type == "BACKGROUND"); wout = next(n for n in wn if n.type == "OUTPUT_WORLD")
wtc = wn.new("ShaderNodeTexCoord"); mapw = wn.new("ShaderNodeMapping"); mapw.inputs["Rotation"].default_value = (0, 0, math.radians(110))
wl.new(wtc.outputs["Generated"], mapw.inputs["Vector"])
env = wn.new("ShaderNodeTexEnvironment"); env.image = img(os.path.join(PH_DIR, "kloofendal_48d_partly_cloudy_puresky", MANIFEST["kloofendal_48d_partly_cloudy_puresky"]["hdr"]))
wl.new(mapw.outputs["Vector"], env.inputs["Vector"]); wl.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.65
sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 2.6; sun_d.angle = math.radians(2.5); sun_d.color = (1.0, 0.95, 0.88)
sun = bpy.data.objects.new("Sun", sun_d); scene.collection.objects.link(sun); sun.rotation_euler = Vector((0.45, 0.55, -0.75)).to_track_quat("-Z", "Y").to_euler()       # from the front-left, above the camera side
def area(name, loc, size, power, rgb=(1, 1, 1), target=None):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = target; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
    return o
def target(name, loc):
    o = bpy.data.objects.new(name, None); scene.collection.objects.link(o); o.location = loc; return o
area("SectionFill", (0.0, -12.0, 1.0), 10.0, 1200, (0.9, 0.95, 1.0), target("LT_Section", (0, 0, -1.5)))     # lights the cut face (the sun is behind it)
area("PadFill", (9.0, -6.0, 3.0), 4.0, 500, (1.0, 0.95, 0.9), target("LT_Pad", (8.6, 0.5, 0.4)))
area("C_Key", (OC - 3.0, -5.0, 4.0), 4.0, 650, (1.0, 0.95, 0.88), target("LT_C", (OC, 0, 0.2)))
area("CamFill", (0, 0, 0), 2.5, 60, (1.0, 0.96, 0.9), TGT).parent = cam

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
scene.cycles.max_bounces = 8; scene.cycles.transmission_bounces = 8; scene.cycles.volume_bounces = 1
scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = False
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"; scene.view_settings.exposure = -0.2
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
prefs.keyframe_new_interpolation_type = "BEZIER"

# ---------- export cues, events and projected anchors for the typography ----------
ANCH = {"hole": (None, Vector((-2.5, 0.0, -1.25))), "excavator": (EXC, Vector((0.0, -0.9, 2.2))),
        "cage_floor": (None, Vector((3.0, 0.0, -2.52))), "cage_wall": (None, Vector((3.2, PY + SH * 0.5, -1.25))),
        "steps": (None, Vector((-4.6, 0.0, -0.45))), "drain": (POOL, Vector((X_DR, 0.35, -2.38))), "skimmer": (POOL, Vector((5.25, 0.0, -0.3))),
        "jet": (POOL, Vector((-2.2, PY - 0.05, -0.5))), "nozzle": (NOZ, Vector((0.0, 0.0, 0.0))), "shell": (POOL, Vector((-2.5, 0.0, -1.12))),
        "tile": (POOL, Vector((3.0, PY, -0.15))), "coping": (POOL, Vector((-2.0, PY + 0.1, 0.08))), "plaster": (POOL, Vector((-2.4, 0.3, -1.0))),
        "seep": (None, Vector((5.3, 0.0, -1.4))), "pump": (None, Vector((7.9, 0.2, 0.62))), "filter": (None, Vector((9.3, 0.1, 1.0))),
        "jet_left": (None, Vector((-5.0, 0.0, -0.55))), "water": (POOL, Vector((0.0, 0.0, -0.6))), "groundwater": (None, Vector((-8.0, 0.0, -2.5))),
        "pool_lift": (POOL, Vector((0.0, 0.0, -0.4))), "valve": (POOL, Vector((X_DR - 0.55, 0.0, -2.68))), "gun": (GUN, Vector((0.0, -0.45, 2.3))),
        "patch": (None, Vector((OX - 1.5, 2.95, 3.0))), "beam_crack": (None, Vector((OC, -0.22, 0.44))), "beam_bar": (None, Vector((OC + 1.6, -0.05, 0.16)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, (ob, local) in ANCH.items():
        w = local if ob is None else ob.matrix_world @ local
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)])
events = {"open": round(T_OPEN + 0.1, 3), "dig": [round(T_D0, 3), round(T_D1, 3)], "spray": [round(T_S0, 3), round(T_S1, 3)],
          "beam_crack": round(T_PU, 3), "squeeze": round(T_SQ, 3), "steel_beam": round(T_ST, 3), "cure": [round(T_CU0, 3), round(T_CU1, 3)],
          "seep": [round(T_SE0, 3), round(T_SE1, 3)], "fill": [round(T_F0, 3), round(T_F1, 3)], "loop": [round(T_LP0, 3), round(C["heres"] - 0.05, 3)],
          "drain_out": [round(T_E0, 3), round(T_E1, 3)], "float": [round(T_FL0, 3), round(T_FL1, 3)], "valve_flow": [round(C["lets2"] - 0.1, 3), round(T_B0, 3)],
          "set_c": [round(T_BEAM0, 3), round(T_BEAM1, 3)], "set_b": [round(T_B0, 3), round(T_B1, 3)], "gun_spray": [round(T_PA0, 3), round(T_PA1, 3)],
          "cta": round(T_CTA, 3)}
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
