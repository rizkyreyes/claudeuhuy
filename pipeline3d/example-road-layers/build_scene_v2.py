# Road-Layers-3D v2: Cycles + Poly Haven PBR textures, scanned stones with rigid-body physics,
# HDRI skies, grass blades, 3D trees, depth of field. Cues locked to the voice-over words.
# Usage (background):
#   blender -b -y -P build_scene_v2.py -- --save <file.blend> [--stills f1,f2,... --pct 50 --samples 64 --out dir] [--anim --out dir]
import bpy, bmesh, json, math, os, random, sys
import numpy as np
from mathutils import Vector, Matrix

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default

HERE = os.path.dirname(os.path.abspath(__file__))
PH_DIR = os.path.join(HERE, "..", "assets", "polyhaven")
MANIFEST = json.load(open(os.path.join(PH_DIR, "manifest.json"), encoding="utf-8"))
WORDS = json.load(open(os.path.join(HERE, "..", "audio", "words-trim.json"), encoding="utf-8"))["words"]
FPS, VO_OFFSET, DUR = 30, 0.15, 15.0
FRAMES = int(DUR * FPS)
random.seed(7)

# ---------- cue lookup: next occurrence of a word after the previous cue ----------
_cursor = [0]
def cue(word):
    for i in range(_cursor[0], len(WORDS)):
        if WORDS[i]["word"].lower().strip(".,?!'") == word.lower():
            _cursor[0] = i + 1
            return WORDS[i]["start"] + VO_OFFSET
    raise ValueError("cue word not found after cursor: " + word)
F = lambda t: max(1, round(t * FPS) + 1)          # project seconds -> frame (frame 1 = 0 s)

T_WHY = cue("why"); T_LETS = cue("let's"); T_FIRST = cue("first"); T_SOIL = cue("soil"); T_DUG = cue("dug")
T_PACKED = cue("packed"); T_DOWN = cue("down"); T_THEN = cue("then"); T_LAYER = cue("layer"); T_BIG = cue("big")
T_ONTOP = cue("on"); T_CRUSHED = cue("crushed"); T_GRAVEL = cue("gravel"); T_FINALLY = cue("finally")
T_HOT = cue("hot"); T_ASPHALT = cue("asphalt"); T_ROLLED = cue("rolled"); T_FLAT = cue("flat")
CUT = F(T_LETS)
CUES = {k: v for k, v in globals().items() if k.startswith("T_")}

# ---------- reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
prefs = bpy.context.preferences.edit

def key(owner, path, frame, value=None, interp="BEZIER", index=-1):
    prefs.keyframe_new_interpolation_type = interp
    if value is not None:
        if index >= 0: getattr(owner, path)[index] = value
        else: setattr(owner, path, value)
    owner.keyframe_insert(path, frame=frame, index=index)

def _vis(obj, frame, hidden, viewport=True):
    for o in [obj] + list(obj.children_recursive):
        key(o, "hide_render", frame, hidden, "CONSTANT")
        if viewport: key(o, "hide_viewport", frame, hidden, "CONSTANT")

def hide_until(obj, frame, hide_after=None, viewport=True):
    _vis(obj, 1, True, viewport); _vis(obj, frame, False, viewport)
    if hide_after: _vis(obj, hide_after, True, viewport)

def show_until(obj, frame):
    _vis(obj, 1, False); _vis(obj, frame, True)

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    return m, nt, bsdf

def flat_mat(name, rgb, rough=0.8, metal=0.0, alpha=1.0):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Alpha"].default_value = alpha
    return m

def img(path, color=True):
    im = bpy.data.images.load(path, check_existing=True)
    if not color: im.colorspace_settings.name = "Non-Color"
    return im

def tex_set(nt, asset, size_m, vec_src, blend=0.25):
    """Box-projected PBR set -> dict(col, rough, nrm, disp) output sockets."""
    L = nt.links; files = MANIFEST[asset]
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / size_m,) * 3
    L.new(vec_src, mp.inputs["Vector"])
    out = {}
    for mapname, keyname, color in [("Diffuse", "col", True), ("Rough", "rough", False), ("nor_gl", "nrm", False), ("Displacement", "disp", False)]:
        if mapname not in files: continue
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = img(os.path.join(PH_DIR, asset, files[mapname]), color)
        t.projection = "BOX"; t.projection_blend = blend
        L.new(mp.outputs["Vector"], t.inputs["Vector"]); out[keyname] = t.outputs["Color"]
    return out

def mix_col(nt, fac, a, b):
    m = nt.nodes.new("ShaderNodeMix"); m.data_type = "RGBA"
    nt.links.new(fac, m.inputs["Factor"]); nt.links.new(a, m.inputs[6]); nt.links.new(b, m.inputs[7]); return m.outputs[2]

def hsv(nt, col, h=0.5, s=1.0, v=1.0):
    n = nt.nodes.new("ShaderNodeHueSaturation")
    n.inputs["Hue"].default_value, n.inputs["Saturation"].default_value, n.inputs["Value"].default_value = h, s, v
    nt.links.new(col, n.inputs["Color"]); return n.outputs["Color"]

def finish(nt, b, col, rough, nrm, disp, rough_mul=1.0, nrm_strength=1.0, bump=0.04):
    L = nt.links
    L.new(col, b.inputs["Base Color"])
    rm = nt.nodes.new("ShaderNodeMath"); rm.operation = "MULTIPLY"; rm.inputs[1].default_value = rough_mul
    sep = nt.nodes.new("ShaderNodeRGBToBW"); L.new(rough, sep.inputs[0]); L.new(sep.outputs[0], rm.inputs[0])
    L.new(rm.outputs[0], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = nrm_strength; L.new(nrm, nm.inputs["Color"])
    if disp is not None:
        bw = nt.nodes.new("ShaderNodeRGBToBW"); L.new(disp, bw.inputs[0])
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = bump; bp.inputs["Strength"].default_value = 0.6
        L.new(bw.outputs[0], bp.inputs["Height"]); L.new(nm.outputs["Normal"], bp.inputs["Normal"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    else:
        L.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Specular IOR Level"].default_value = 0.3

def pbr_mat(name, asset, size_m, world=False, rough_mul=1.0, tint=None, value=1.0):
    m, nt, b = new_mat(name)
    if world:
        g = nt.nodes.new("ShaderNodeNewGeometry"); vec = g.outputs["Position"]
    else:
        tc = nt.nodes.new("ShaderNodeTexCoord"); vec = tc.outputs["Object"]
    t = tex_set(nt, asset, size_m, vec)
    col = hsv(nt, t["col"], 0.5, tint or 1.0, value) if (tint or value != 1.0) else t["col"]
    finish(nt, b, col, t["rough"], t["nrm"], t.get("disp"), rough_mul)
    return m, b

def ground_mat(name, top_asset, top_size, grass=True):
    """World-space: top faces = grass (or trench floor), sides = soil strata by depth."""
    m, nt, b = new_mat(name); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry"); pos = g.outputs["Position"]
    top = tex_set(nt, top_asset, top_size, pos)
    soil = tex_set(nt, "excavated_soil_wall", 2.0, pos)
    red = tex_set(nt, "red_laterite_soil_stones", 2.0, pos)
    sp = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(pos, sp.inputs[0])
    sn = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Normal"], sn.inputs[0])
    wob = nt.nodes.new("ShaderNodeTexNoise"); wob.inputs["Scale"].default_value = 0.8; L.new(pos, wob.inputs["Vector"])
    zw = nt.nodes.new("ShaderNodeMath"); zw.operation = "MULTIPLY_ADD"; zw.inputs[1].default_value = 0.5
    L.new(wob.outputs["Fac"], zw.inputs[0]); L.new(sp.outputs[2], zw.inputs[2])
    deep = nt.nodes.new("ShaderNodeMath"); deep.operation = "LESS_THAN"; deep.inputs[1].default_value = -1.55
    L.new(zw.outputs[0], deep.inputs[0])
    darker = nt.nodes.new("ShaderNodeMapRange"); darker.inputs[1].default_value = -4.5; darker.inputs[2].default_value = -1.6
    darker.inputs[3].default_value = 0.35; darker.inputs[4].default_value = 1.05; L.new(sp.outputs[2], darker.inputs[0])
    red_col = nt.nodes.new("ShaderNodeMix"); red_col.data_type = "RGBA"; red_col.blend_type = "MULTIPLY"; red_col.inputs["Factor"].default_value = 1.0
    L.new(red["col"], red_col.inputs[6])
    dk = nt.nodes.new("ShaderNodeCombineColor"); [L.new(darker.outputs[0], dk.inputs[i]) for i in range(3)]
    L.new(dk.outputs[0], red_col.inputs[7])
    side_col = mix_col(nt, deep.outputs[0], soil["col"], red_col.outputs[2])
    side_r = mix_col(nt, deep.outputs[0], soil["rough"], red["rough"])
    side_n = mix_col(nt, deep.outputs[0], soil["nrm"], red["nrm"])
    side_d = mix_col(nt, deep.outputs[0], soil["disp"], red["disp"])
    is_top = nt.nodes.new("ShaderNodeMath"); is_top.operation = "GREATER_THAN"; is_top.inputs[1].default_value = 0.5
    L.new(sn.outputs[2], is_top.inputs[0])
    top_col = hsv(nt, top["col"], 0.56, 1.45, 0.85) if grass else top["col"]
    finish(nt, b, mix_col(nt, is_top.outputs[0], side_col, top_col), mix_col(nt, is_top.outputs[0], side_r, top["rough"]),
           mix_col(nt, is_top.outputs[0], side_n, top["nrm"]), mix_col(nt, is_top.outputs[0], side_d, top["disp"]), bump=0.06)
    return m

M_GROUND = ground_mat("Ground", "leafy_grass", 2.0)
M_SOIL = ground_mat("SoilOnly", "brown_mud_dry", 1.3, grass=False)
M_STONE, _ = pbr_mat("StoneLayer", "dry_river_pebbles", 2.6)
M_GRAVEL, _ = pbr_mat("GravelLayer", "dry_river_pebbles", 0.85, value=1.05, tint=0.6)
M_ASPH, ASPH_BSDF = pbr_mat("Asphalt", "asphalt_track", 2.0, value=3.5)      # fresh: no cracks
ASPH_BSDF.inputs["Emission Color"].default_value = (1.0, 0.3, 0.06, 1)
M_ASPH_WET, _ = pbr_mat("AsphaltWetCracked", "asphalt_02", 3.0, rough_mul=0.25, value=0.55)
M_COMPACT, _ = pbr_mat("Compacted", "brown_mud_dry", 1.3, world=True, value=0.75)
M_CRACK = flat_mat("Crack", (0.004, 0.004, 0.004), 0.9)
M_WATER = flat_mat("Water", (0.02, 0.025, 0.03), 0.02)
M_RAIN = flat_mat("Rain", (0.85, 0.88, 0.95), 0.1, alpha=0.35)
M_YELLOW = flat_mat("MachinePaint", (0.85, 0.52, 0.02), 0.35)
M_STEEL = flat_mat("Steel", (0.55, 0.56, 0.58), 0.38, metal=1.0)
M_DARK = flat_mat("Rubber", (0.02, 0.02, 0.022), 0.6)
M_WALL = flat_mat("Plaster", (0.72, 0.66, 0.55), 0.9)
M_ROOF = flat_mat("RoofTile", (0.42, 0.12, 0.05), 0.75)
M_WHITE = flat_mat("OutlineWhite", (0.9, 0.9, 0.88), 0.6)

# ---------- geometry helpers ----------
def box(name, x0, x1, y0, y1, z0, z1, mat, pivot=None, coll=None, bevel=0.0):
    pivot = Vector(pivot if pivot else ((x0 + x1) / 2, y0, z0))
    v = [Vector((x, y, z)) - pivot for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in v], [], f); me.update()
    if mat: me.materials.append(mat)
    ob = bpy.data.objects.new(name, me); ob.location = pivot
    (coll or scene.collection).objects.link(ob)
    if bevel:
        bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = bevel; bv.segments = 3; bv.limit_method = "ANGLE"
        me.shade_smooth()
        try: me.set_sharp_from_angle(angle=math.radians(40))
        except Exception: pass
    return ob

def coll(name, parent=None):
    c = bpy.data.collections.new(name); (parent or scene.collection).children.link(c); return c

C_GROUND, C_ROAD, C_LOOSE, C_HOOK, C_PROPS, C_PHYS = coll("Ground"), coll("RoadLayers"), coll("LooseStones"), coll("HookRain"), coll("Props"), coll("PhysicsColliders")

def import_gltf(asset):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PH_DIR, asset, MANIFEST[asset]["gltf"]))
    return [o for o in bpy.data.objects if o not in before]

# ---------- ground (road trench x -2.2..2.2, depth 1.0) ----------
RW, YL, GX, GY = 2.2, 120.0, 60.0, 160.0
Z_SUB, Z_STONE, Z_GRAV, Z_TOP = -1.0, -0.55, -0.22, 0.02
box("Ground_L", -GX, -RW, 0, GY, -14, 0, M_GROUND, coll=C_GROUND)
box("Ground_R", RW, GX, 0, GY, -14, 0, M_GROUND, coll=C_GROUND)
box("Ground_Under", -RW, RW, 0, GY, -14, Z_SUB, M_SOIL, coll=C_GROUND)
box("Ground_RoadEnd", -RW, RW, YL, GY, Z_SUB, 0, M_GROUND, coll=C_GROUND)

# soil to be dug: chunks along the road, lifted out from far to near on "dug"
CHUNKS = []
for i, (y0, y1) in enumerate([(30, YL), (12, 30), (4, 12), (0, 4)]):
    ch = box(f"Soil_Dug_{i}", -RW, RW, y0, y1, Z_SUB, 0, M_GROUND, coll=C_GROUND)
    hide_until(ch, CUT); CHUNKS.append(ch)
    t0 = T_DUG - 0.1 + 0.05 * i
    key(ch, "location", F(t0), interp="BEZIER", index=2)
    key(ch, "location", F(t0 + 0.35), ch.location.z + 1.6, "BEZIER", 2)
    key(ch, "scale", F(t0), (1, 1, 1), "BEZIER")
    key(ch, "scale", F(t0 + 0.35), (0.05, 0.05, 0.05), "BEZIER")
    _vis(ch, F(t0 + 0.36), True)

# road outline: white marking lines draw in on "First", gone once the soil is dug
for sx in (-1, 1):
    ln = box(f"Outline_{sx:+d}", sx * RW - 0.05, sx * RW + 0.05, 0, YL, 0.0, 0.015, M_WHITE, coll=C_GROUND)
    hide_until(ln, F(T_FIRST), F(T_DUG + 0.1))
    key(ln, "scale", F(T_FIRST), (1, 0.0, 1), "BEZIER")
    key(ln, "scale", F(T_FIRST + 0.5), (1, 1, 1), "BEZIER")

def layer(name, z0, z1, mat, hook_mat, t_grow, grow_s, axis="z", from_back=False):
    pivot = (0, YL if from_back else 0, z0)
    ob = box(name, -RW, RW, 0, YL, z0, z1, mat, pivot=pivot, coll=C_ROAD)
    full = (1, 1, 1); zero = (1, 1, 0.0) if axis == "z" else (1, 0.0, 1)
    key(ob, "scale", F(t_grow), zero, "BEZIER")
    key(ob, "scale", F(t_grow + grow_s), full, "BEZIER")
    hide_until(ob, F(t_grow))
    hk = box("Hook_" + name, -RW, RW, 0, YL, z0, z1, hook_mat, coll=C_HOOK)
    show_until(hk, CUT)
    return ob

L_STONE = layer("Layer_BigStones", Z_SUB, Z_STONE, M_STONE, M_STONE, T_LAYER, 0.6)
L_GRAV = layer("Layer_Gravel", Z_STONE, Z_GRAV, M_GRAVEL, M_GRAVEL, T_CRUSHED, 0.6)
L_ASPH = layer("Layer_Asphalt", Z_GRAV, Z_TOP, M_ASPH, M_ASPH_WET, T_HOT, 1.0, axis="y", from_back=True)
for fr, s in [(F(T_HOT), 0.0), (F(T_HOT + 0.4), 0.35), (F(T_FLAT + 0.3), 0.0)]:
    key(ASPH_BSDF.inputs["Emission Strength"], "default_value", fr, s, "BEZIER")

skin = box("Subgrade_Compacted", -RW, RW, 0, YL, Z_SUB - 0.001, Z_SUB + 0.012, M_COMPACT, coll=C_ROAD)
hide_until(skin, F(T_PACKED + 0.05))

# ---------- grass blades (particle instances) on both verges ----------
def blade_mesh():
    bm = bmesh.new(); w, h = 0.035, 1.0
    pts = [(-w, 0, 0), (w, 0, 0), (-w * 0.7, 0.45 * h, 0.02), (w * 0.7, 0.45 * h, 0.02), (0, h, 0.07)]   # hair NOR maps local +Y to the surface normal
    vs = [bm.verts.new(p) for p in pts]
    bm.faces.new((vs[0], vs[1], vs[3], vs[2])); bm.faces.new((vs[2], vs[3], vs[4]))
    me = bpy.data.meshes.new("GrassBlade"); bm.to_mesh(me); bm.free(); return me
M_BLADE, nt_b, b_b = None, None, None
M_BLADE, nt_b, b_b = new_mat("GrassBlade")
oi = nt_b.nodes.new("ShaderNodeObjectInfo")
gr = nt_b.nodes.new("ShaderNodeValToRGB"); el = gr.color_ramp.elements
el[0].color = (0.06, 0.15, 0.02, 1); el[1].color = (0.20, 0.27, 0.05, 1); e = el.new(0.6); e.color = (0.11, 0.22, 0.03, 1)
nt_b.links.new(oi.outputs["Random"], gr.inputs[0]); nt_b.links.new(gr.outputs[0], b_b.inputs["Base Color"])
b_b.inputs["Roughness"].default_value = 0.6
try:
    b_b.inputs["Subsurface Weight"].default_value = 0.0
    b_b.inputs["Transmission Weight"].default_value = 0.15
except Exception: pass
blade = bpy.data.objects.new("GrassBladeSrc", blade_mesh()); blade.data.materials.append(M_BLADE)
C_SRC = coll("Sources"); C_SRC.objects.link(blade); blade.hide_render = True; blade.location = (0, -50, -50)

def grass_patch(name, x0, x1, y0, y1, count, parent=None):
    pl = box(name, x0, x1, y0, y1, 0.0, 0.0001, None, pivot=((x0 + x1) / 2, (y0 + y1) / 2, 0.0), coll=C_GROUND)
    pl.display_type = "WIRE"
    ps_mod = pl.modifiers.new("Grass", "PARTICLE_SYSTEM"); ps = ps_mod.particle_system.settings
    ps.type = "HAIR"; ps.use_advanced_hair = True; ps.count = count; ps.hair_length = 1.0
    ps.emit_from = "FACE"; ps.use_emit_random = True; ps.distribution = "RAND"
    ps.render_type = "OBJECT"; ps.instance_object = blade
    ps.particle_size = 0.13; ps.size_random = 0.5
    ps.use_rotations = True; ps.rotation_mode = "NOR"; ps.phase_factor_random = 2.0; ps.rotation_factor_random = 0.12
    pl.show_instancer_for_render = False
    ps_mod.particle_system.seed = random.randint(0, 9999)
    if parent: pl.parent = parent; pl.matrix_parent_inverse = parent.matrix_world.inverted()
    return pl
grass_patch("GrassBlades_L_near", -9, -RW - 0.02, 0.0, 12, 170000)
grass_patch("GrassBlades_R_near", RW + 0.02, 9, 0.0, 12, 170000)
grass_patch("GrassBlades_L_far", -14, -RW - 0.02, 12, 34, 130000)
grass_patch("GrassBlades_R_far", RW + 0.02, 14, 12, 34, 130000)
for i, ch in enumerate(CHUNKS[2:]):            # chunks visible near the camera also carry blades
    y0, y1 = [(4, 12), (0, 4)][i]
    gp = grass_patch(f"GrassBlades_Chunk{i}", -RW + 0.02, RW - 0.02, y0, y1, int(9500 * (y1 - y0)), parent=ch)
    hide_until(gp, CUT, F(T_DUG - 0.1 + 0.05 * (i + 2) + 0.36))       # same window as its soil chunk

# ---------- scanned stones + rigid-body physics ----------
stone_objs = import_gltf("namaqualand_stones_01")
stone_meshes = []
for o in stone_objs:
    if o.type != "MESH": continue
    me = o.data.copy(); me.transform(o.matrix_world)
    vs = np.array([v.co[:] for v in me.vertices]); c = (vs.min(0) + vs.max(0)) / 2; ext = (vs.max(0) - vs.min(0)).max()
    me.transform(Matrix.Translation(Vector(-c))); me.transform(Matrix.Scale(1 / ext, 4))    # unit size, centred
    stone_meshes.append(me)
for o in stone_objs: bpy.data.objects.remove(o)

bpy.ops.rigidbody.world_add()
rbw = scene.rigidbody_world
rbw.point_cache.frame_start, rbw.point_cache.frame_end = 1, FRAMES
try: rbw.substeps_per_frame = 10; rbw.solver_iterations = 20
except Exception: pass

def rb(ob, kind, shape, groups, friction=0.8, bounce=0.1):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.rigidbody.object_add(type=kind)
    ob.select_set(False)
    r = ob.rigid_body; r.collision_shape = shape; r.friction = friction; r.restitution = bounce
    r.collision_collections = [i in groups for i in range(20)]
    r.use_margin = True; r.collision_margin = 0.002
    return r

# colliders (invisible): floors at the layer tops, trench walls, a front wall at the section face
for nm, dims, groups in [("Col_StoneFloor", (-RW, RW, 0, 10, Z_SUB - 0.3, Z_STONE), [0]),
                         ("Col_GravelFloor", (-RW, RW, 0, 10, Z_SUB - 0.3, Z_GRAV), [1]),
                         ("Col_WallL", (-RW - 0.5, -RW, 0, 10, Z_SUB - 0.3, 1.5), [0, 1]),
                         ("Col_WallR", (RW, RW + 0.5, 0, 10, Z_SUB - 0.3, 1.5), [0, 1]),
                         ("Col_Front", (-RW, RW, -0.4, 0.0, Z_SUB - 0.3, 1.5), [0, 1])]:
    c = box(nm, *dims, None, coll=C_PHYS); c.hide_render = True; c.display_type = "WIRE"
    rb(c, "PASSIVE", "BOX", groups, friction=0.9, bounce=0.05)

def falling(name, me, size, x, y, z_land, t_release, h, groups):
    ob = bpy.data.objects.new(name, me); C_LOOSE.objects.link(ob)
    ob.scale = (size,) * 3
    ob.location = (x, y, z_land + h)
    ob.rotation_euler = (random.uniform(0, 6.3), random.uniform(0, 6.3), random.uniform(0, 6.3))
    r = rb(ob, "ACTIVE", "CONVEX_HULL", groups, friction=0.85, bounce=0.15)
    r.mass = size * 10
    r.kinematic = True; ob.keyframe_insert("rigid_body.kinematic", frame=1)
    r.kinematic = False; ob.keyframe_insert("rigid_body.kinematic", frame=F(t_release))
    hide_until(ob, F(t_release), viewport=False)
    return ob

g = 9.81
H_BIG, H_PEB = 2.0, 1.5
for i in range(46):
    s = random.uniform(0.2, 0.32)
    land_t = T_BIG + 0.15 + random.uniform(0, 0.9)
    falling(f"BigStone_{i:02d}", stone_meshes[i % len(stone_meshes)], s, random.uniform(-RW + 0.3, RW - 0.3),
            random.uniform(0.35, 6.0), Z_STONE + s * 0.3, land_t - math.sqrt(2 * H_BIG / g), H_BIG, [0])
for i in range(150):
    s = random.uniform(0.06, 0.1)
    land_t = T_CRUSHED + 0.18 + random.uniform(0, 0.9)
    falling(f"Gravel_{i:03d}", stone_meshes[(i + 2) % len(stone_meshes)], s, random.uniform(-RW + 0.15, RW - 0.15),
            random.uniform(0.2, 4.5), Z_GRAV + s * 0.3, land_t - math.sqrt(2 * H_PEB / g), H_PEB, [1])
for ob in C_LOOSE.objects:
    cover = T_CRUSHED + 0.6 if ob.name.startswith("BigStone") else T_HOT + 1.0
    key(ob, "hide_render", F(cover), True, "CONSTANT")

# ---------- compactor plate: two thumps on "packed" / "down" ----------
cp = box("Compactor_Plate", -0.55, 0.55, 0.9, 2.0, 0, 0.16, M_STEEL, pivot=(0, 1.45, 0), coll=C_PROPS, bevel=0.015)
body = box("Compactor_Body", -0.35, 0.35, 1.15, 1.75, 0.16, 0.72, M_YELLOW, pivot=(0, 1.45, 0.16), coll=C_PROPS, bevel=0.04)
body.parent = cp; body.location = (0, 0, 0.16)
handle = box("Compactor_Handle", -0.03, 0.03, 1.41, 1.49, 0.72, 1.6, M_DARK, pivot=(0, 1.45, 0.72), coll=C_PROPS, bevel=0.01)
handle.parent = cp; handle.location = (0, 0, 0.72); handle.rotation_euler = (math.radians(-25), 0, 0)
hide_until(cp, F(T_PACKED - 0.3), F(T_DOWN + 0.75))
floor = Z_SUB + 0.012
key(cp, "location", F(T_PACKED - 0.3), (0.0, 1.45, floor + 3.0), "BEZIER")
for t in [T_PACKED, T_DOWN]:
    key(cp, "location", F(t - 0.22), (0.0, 1.45, floor + 0.55), "BEZIER")
    key(cp, "location", F(t), (0.0, 1.45, floor), "LINEAR")
key(cp, "location", F(T_DOWN + 0.35), (0.0, 1.45, floor + 0.5), "BEZIER")
key(cp, "location", F(T_DOWN + 0.7), (0.0, 1.45, floor + 3.5), "BEZIER")

# ---------- steam roller on "rolled" ----------
RL = bpy.data.objects.new("Roller", None); C_PROPS.objects.link(RL)
def drum(name, y, r, w):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r, radius2=r, depth=w)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(M_STEEL); me.shade_smooth()
    try: me.set_sharp_from_angle(angle=math.radians(40))
    except Exception: pass
    d = bpy.data.objects.new(name, me); C_PROPS.objects.link(d); d.parent = RL; d.location = (0, y, r)
    bv = d.modifiers.new("Bevel", "BEVEL"); bv.width = 0.02; bv.segments = 3; bv.limit_method = "ANGLE"
    return d
RF, RR = drum("Roller_FrontDrum", -1.1, 0.55, 1.9), drum("Roller_RearDrum", 1.2, 0.5, 1.9)
for nm, dims, mat, bev in [("Roller_Body", (-0.8, 0.8, -0.6, 1.9, 0.55, 1.35), M_YELLOW, 0.06),
                           ("Roller_Cab", (-0.6, 0.6, 0.6, 1.6, 1.35, 2.25), M_YELLOW, 0.04),
                           ("Roller_Roof", (-0.75, 0.75, 0.45, 1.75, 2.25, 2.33), M_DARK, 0.02),
                           ("Roller_Frame", (-1.0, 1.0, -1.5, -0.7, 0.9, 1.12), M_DARK, 0.02)]:
    bb = box(nm, *dims, mat, pivot=(0, 0, 0), coll=C_PROPS, bevel=bev); bb.parent = RL
y_start, y_end = 16.0, 4.2
t_a, t_b = T_ROLLED - 0.25, DUR + 0.2
hide_until(RL, F(t_a))
key(RL, "location", F(t_a), (0, y_start, Z_TOP), "LINEAR")
key(RL, "location", F(t_b), (0, y_end, Z_TOP), "LINEAR")
for d, r in [(RF, 0.55), (RR, 0.5)]:
    key(d, "rotation_euler", F(t_a), 0.0, "LINEAR", 0)
    key(d, "rotation_euler", F(t_b), (y_start - y_end) / r, "LINEAR", 0)

# ---------- hook: cracks, pothole water, rain (0 -> CUT) ----------
def crack_curve(name, pts, depth=0.014):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = 1
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for p, c in zip(sp.points, pts): p.co = (*c, 1)
    cu.materials.append(M_CRACK)
    ob = bpy.data.objects.new(name, cu); C_HOOK.objects.link(ob); show_until(ob, CUT); return ob
def jag(x0, y0, x1, y1, n, amp, z, seed):
    rnd = random.Random(seed)
    return [(x0 + (x1 - x0) * i / n + rnd.uniform(-amp, amp), y0 + (y1 - y0) * i / n + rnd.uniform(-amp, amp), z) for i in range(n + 1)]
PH = Vector((0.55, 1.7, Z_TOP))
crack_curve("Crack_A", jag(PH.x + 0.45, PH.y, 1.9, 5.5, 14, 0.07, Z_TOP + 0.002, 1))
crack_curve("Crack_B", jag(PH.x - 0.4, PH.y + 0.1, -1.6, 3.8, 12, 0.06, Z_TOP + 0.002, 2))
crack_curve("Crack_C", jag(PH.x, PH.y - 0.35, 0.2, 0.0, 7, 0.05, Z_TOP + 0.002, 3))
crack_curve("Crack_Face", [(0.2 + random.uniform(-0.04, 0.04), -0.008, Z_TOP - (Z_TOP - Z_GRAV - 0.15) * i / 7) for i in range(8)], 0.016)
def disc(name, sx, sy, z, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1, depth=depth, location=(PH.x, PH.y, z))
    o = bpy.context.active_object; o.name = name; o.scale = (sx, sy, 1); o.data.materials.append(mat)
    for c in o.users_collection: c.objects.unlink(o)
    C_HOOK.objects.link(o); show_until(o, CUT); return o
disc("Pothole_Rim", 0.62, 0.46, Z_TOP + 0.001, 0.006, M_CRACK)
disc("Pothole_Water", 0.5, 0.36, Z_TOP + 0.003, 0.008, M_WATER)

bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.004, depth=0.5)
drop_mesh = bpy.context.active_object.data; drop_mesh.materials.append(M_RAIN)
bpy.data.objects.remove(bpy.context.active_object)
TOP, H = 5.0, 5.0
for i in range(380):
    ob = bpy.data.objects.new(f"Rain_{i:03d}", drop_mesh); C_HOOK.objects.link(ob)
    ob.location = (random.uniform(-4.5, 4.5), random.uniform(-2.5, 10.0), 0)
    fc = ob.driver_add("location", 2); fc.driver.type = "SCRIPTED"; fc.driver.use_self = False
    fc.driver.expression = f"{TOP} - ((frame*0.36 + {random.uniform(0, H):.3f}) % {H})"
    show_until(ob, CUT)

# ---------- scenery: 3D trees + simple houses ----------
tree_objs = import_gltf("island_tree_02")
C_TREE = coll("TreeSource", C_SRC)
for o in tree_objs:
    for c in list(o.users_collection): c.objects.unlink(o)
    C_TREE.objects.link(o)
bpy.context.view_layer.update()
pts = np.array([(o.matrix_world @ Vector(c))[:] for o in tree_objs if o.type == "MESH" for c in o.bound_box])
tmin, tmax = pts.min(0), pts.max(0); tree_h = tmax[2] - tmin[2]
C_TREE.instance_offset = Vector(((tmin[0] + tmax[0]) / 2, (tmin[1] + tmax[1]) / 2, tmin[2]))
lc = bpy.context.view_layer.layer_collection.children["Sources"]; lc.exclude = True
for i in range(14):
    side = -1 if i % 2 else 1
    e = bpy.data.objects.new(f"Tree_{i:02d}", None); C_PROPS.objects.link(e)
    e.instance_type = "COLLECTION"; e.instance_collection = C_TREE
    e.location = (side * random.uniform(5.5, 13), random.uniform(10, 55), 0)
    s = random.uniform(5.0, 7.5) / tree_h; e.scale = (s, s, s); e.rotation_euler = (0, 0, random.uniform(0, 6.3))
for i, (x, y) in enumerate([(-7.5, 6.0), (8.0, 21.0)]):
    box(f"House_{i}_Walls", x - 1.7, x + 1.7, y - 1.6, y + 1.6, 0, 2.6, M_WALL, coll=C_PROPS, bevel=0.03)
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=2.75, depth=1.4, location=(x, y + 1.6, 3.3), rotation=(0, 0, math.radians(45)))
    roof = bpy.context.active_object; roof.name = f"House_{i}_Roof"; roof.data.materials.append(M_ROOF)
    for c in roof.users_collection: c.objects.unlink(roof)
    C_PROPS.objects.link(roof)

# ---------- world: two HDRIs (overcast hook -> sunny), sun placed camera-left ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
for n in list(wn):
    if n.type == "BACKGROUND": wn.remove(n)
wout = next(n for n in wn if n.type == "OUTPUT_WORLD")
tcw = wn.new("ShaderNodeTexCoord"); mapw = wn.new("ShaderNodeMapping"); wl.new(tcw.outputs["Generated"], mapw.inputs["Vector"])
def env(asset, strength):
    im = img(os.path.join(PH_DIR, asset, MANIFEST[asset]["hdr"]))
    t = wn.new("ShaderNodeTexEnvironment"); t.image = im; wl.new(mapw.outputs["Vector"], t.inputs["Vector"])
    bgn = wn.new("ShaderNodeBackground"); bgn.inputs["Strength"].default_value = strength; wl.new(t.outputs["Color"], bgn.inputs["Color"])
    return im, bgn
sunny_im, bg_sun = env("kloofendal_48d_partly_cloudy_puresky", 1.0)
_, bg_over = env("kloofendal_overcast_puresky", 0.7)
mixw = wn.new("ShaderNodeMixShader"); wl.new(bg_over.outputs[0], mixw.inputs[1]); wl.new(bg_sun.outputs[0], mixw.inputs[2])
wl.new(mixw.outputs[0], wout.inputs["Surface"])
key(mixw.inputs["Fac"], "default_value", 1, 0.0, "CONSTANT")
key(mixw.inputs["Fac"], "default_value", CUT - 1, 0.0, "CONSTANT")
key(mixw.inputs["Fac"], "default_value", CUT, 1.0, "CONSTANT")
# locate the sun in the sunny HDRI and rotate it to come from camera-left, slightly front
w_, h_ = sunny_im.size
px = np.empty(w_ * h_ * 4, dtype=np.float32); sunny_im.pixels.foreach_get(px); px = px.reshape(h_, w_, 4)
lum = px[..., 0] * 0.2126 + px[..., 1] * 0.7152 + px[..., 2] * 0.0722
vy, ux = np.unravel_index(np.argmax(lum), lum.shape)
u, v = (ux + 0.5) / w_, (vy + 0.5) / h_
phi, el_ = (u - 0.5) * 2 * math.pi, (v - 0.5) * math.pi
az_src = math.atan2(math.sin(phi), -math.cos(phi))
az_dst = math.atan2(-0.45, -0.9)
mapw.inputs["Rotation"].default_value = (0, 0, az_src - az_dst + math.pi)
print("HDRI sun elevation deg", round(math.degrees(el_), 1), "rotation", round(math.degrees(az_src - az_dst), 1))

# ---------- camera with depth of field ----------
cam_d = bpy.data.cameras.new("Camera"); cam_d.lens = 27; cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 4.0
def aim(loc, target):
    return (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
A_LOC, A_TGT, A2_LOC = (2.3, -3.0, 2.3), (0.4, 2.6, -0.35), (1.9, -2.6, 2.0)
B_LOC, B_TGT, B2_LOC = (0.0, -6.0, 2.7), (0.0, 4.0, -1.2), (0.0, -5.3, 2.45)
key(cam, "location", 1, A_LOC, "LINEAR"); key(cam, "rotation_euler", 1, tuple(aim(A_LOC, A_TGT)), "LINEAR")
key(cam, "location", CUT - 1, A2_LOC, "CONSTANT"); key(cam, "rotation_euler", CUT - 1, tuple(aim(A2_LOC, A_TGT)), "CONSTANT")
key(cam, "location", CUT, B_LOC, "LINEAR"); key(cam, "rotation_euler", CUT, tuple(aim(B_LOC, B_TGT)), "LINEAR")
key(cam, "location", FRAMES, B2_LOC, "LINEAR"); key(cam, "rotation_euler", FRAMES, tuple(aim(B2_LOC, B_TGT)), "LINEAR")
focus_hook = (Vector(A_LOC) - PH).length
focus_main = (Vector(B_LOC) - Vector((0, 1.8, -0.6))).length
key(cam_d.dof, "focus_distance", 1, focus_hook, "LINEAR"); key(cam_d.dof, "focus_distance", CUT - 1, (Vector(A2_LOC) - PH).length, "LINEAR")
key(cam_d.dof, "focus_distance", CUT, focus_main, "LINEAR"); key(cam_d.dof, "focus_distance", FRAMES, (Vector(B2_LOC) - Vector((0, 1.8, -0.6))).length, "LINEAR")

# ---------- render settings: Cycles + OptiX ----------
r = scene.render
r.engine = "CYCLES"
cp_ = bpy.context.preferences.addons["cycles"].preferences
for dev_type in ("OPTIX", "CUDA"):
    try:
        cp_.compute_device_type = dev_type; cp_.get_devices()
        if any(d.type == dev_type for d in cp_.devices): break
    except Exception: continue
for d in cp_.devices: d.use = d.type == cp_.compute_device_type
scene.cycles.device = "GPU"
print("Cycles devices:", [(d.name, d.type, d.use) for d in cp_.devices])
scene.cycles.samples = int(arg("--samples", "96"))
scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
try: scene.cycles.denoiser = "OPTIX"
except Exception: pass
scene.cycles.max_bounces = 8; scene.cycles.diffuse_bounces = 3; scene.cycles.glossy_bounces = 3
scene.cycles.transparent_max_bounces = 24; scene.cycles.caustics_reflective = False; scene.cycles.caustics_refractive = False
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = True
try: r.motion_blur_shutter = 0.4
except Exception: pass
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
prefs.keyframe_new_interpolation_type = "BEZIER"

with open(os.path.join(HERE, "cues.json"), "w") as fh:
    json.dump({k: round(v, 3) for k, v in CUES.items()} | {"CUT_frame": CUT, "frames": FRAMES, "fps": FPS, "vo_offset": VO_OFFSET}, fh, indent=1)

# ---------- bake physics, save, render ----------
bpy.context.view_layer.update()
try:
    with bpy.context.temp_override(scene=scene, point_cache=rbw.point_cache):
        bpy.ops.ptcache.bake(bake=True)
    print("rigid body baked")
except Exception as ex:
    print("bake via operator failed:", ex, "- stepping frames instead")
    for fr in range(1, FRAMES + 1): scene.frame_set(fr)

save = arg("--save")
if save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))

out = arg("--out")
if "--stills" in ARGS:
    r.resolution_percentage = int(arg("--pct", "50"))
    import time
    for fr in [int(x) for x in arg("--stills").split(",")]:
        scene.frame_set(fr); r.filepath = os.path.join(out, f"still_{fr:04d}.png")
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("STILL", fr, "seconds", round(time.time() - t0, 1))
if "--anim" in ARGS:
    r.filepath = os.path.join(out, "f_")
    bpy.ops.render.render(animation=True)
print("CUES", json.dumps({k: round(v, 2) for k, v in CUES.items()}), "CUT", CUT)
