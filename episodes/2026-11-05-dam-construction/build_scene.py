# Dam-Construction-3D: how a concrete dam is built across a river. Canyon cutaway in Blender Cycles. Every cue is a word in the VO.
# One set: a river canyon block (river flows from +x to -x, camera on -y).
#   Cut 1 ("open"): the near rock slab drops at the near tunnel's axis, so the diversion tunnel reads as a groove in the cut face.
#   Cofferdams are end-dumped from the far bank, the river turns into the tunnel, the riverbed between the cofferdams drains.
#   Cut 2 ("now"): everything in front of the river centre line drops, the section at y = 0 shows sediment, bedrock, grout curtain and the dam profile.
#   The dam goes up as a grid of blocks (layers) with cooling pipes, then becomes one monolith; the tunnel inlet is plugged and the reservoir fills.
# No people anywhere. Sizes are illustrative (not to scale, not any real dam); only numbers spoken in the VO appear in the typography.
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
random.seed(12)

# ---------- word cues, chained: next occurrence after the previous cue ----------
norm = lambda s: "".join(ch for ch in s.lower() if ch.isalnum())
_last = [-1.0]
def TA(word):
    for w in WORDS:
        t = round(VO + w["start"], 3)
        if t > _last[0] + 0.01 and norm(w["text"]) == norm(word):
            _last[0] = t; return t
    raise ValueError(f'cue "{word}" after {_last[0]} not found')
CUES = [("build", "build"), ("move", "move"), ("river", "river"), ("cut", "cut"), ("open", "open"), ("crews", "crews"), ("blast", "blast"),
        ("tunnels", "tunnels"), ("walls", "walls"), ("hoover", "hoover"), ("four", "four"), ("then", "then"), ("trucks", "trucks"),
        ("dump", "dump"), ("rock", "rock"), ("upstream", "upstream"), ("cofferdam", "cofferdam"), ("within", "within"), ("day", "day"),
        ("turns", "turns"), ("tunnels2", "tunnels"), ("second", "second"), ("downstream", "downstream"), ("riverbed", "riverbed"),
        ("drains", "drains"), ("now", "now"), ("dig", "dig"), ("bedrock", "bedrock"), ("drill", "drill"), ("holes", "holes"),
        ("pump", "pump"), ("liquid", "liquid"), ("hardens", "hardens"), ("curtain", "curtain"), ("sneak", "sneak"),
        ("underneath", "underneath"), ("next", "next"), ("concrete", "concrete"), ("never", "never"), ("once", "once"),
        ("concrete2", "concrete"), ("heats", "heats"), ("hardens2", "hardens"), ("hoover2", "hoover"), ("single", "single"),
        ("pour", "pour"), ("hundred", "hundred"), ("years", "years"), ("cool", "cool"), ("cracked", "cracked"), ("so", "so"),
        ("blocks", "blocks"), ("inside", "inside"), ("layer", "layer"), ("pipes", "pipes"), ("cold", "cold"), ("pulls", "pulls"),
        ("heat", "heat"), ("out", "out"), ("hoover3", "hoover"), ("five", "five"), ("miles", "miles"), ("then2", "then"),
        ("pipes2", "pipes"), ("gaps", "gaps"), ("filled", "filled"), ("solid", "solid"), ("wall", "wall"), ("water", "water"),
        ("pressure", "pressure"), ("depth", "depth"), ("thin", "thin"), ("top", "top"), ("huge", "huge"), ("bottom", "bottom"),
        ("finally", "finally"), ("tunnels3", "tunnels"), ("plugged", "plugged"), ("outlets", "outlets"), ("river2", "river"),
        ("fills", "fills"), ("valley", "valley"), ("would", "would"), ("walk", "walk"), ("tall", "tall"), ("tell", "tell"),
        ("comments", "comments"), ("next2", "next"), ("water2", "water"), ("heater", "heater"), ("follow", "follow")]
C = {}
for name, word in CUES: C[name] = TA(word)
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
def pulse(t, t0, hold=1.0, peak=1.0):
    if t < t0 - 0.1: return 0.0
    if t < t0 + 0.15: return seg(t, t0 - 0.1, t0 + 0.15, 0.0, peak)
    if t < t0 + hold: return peak
    return seg(t, t0 + hold, t0 + hold + 0.45, peak, 0.0)

def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CG, CD, CP = coll("Ground"), coll("Dam"), coll("Props")

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
GOLD, CYAN, RED, HOT = (0.98, 0.74, 0.27), (0.30, 0.92, 1.0), (1.0, 0.30, 0.24), (1.0, 0.28, 0.04)
M_WATER = water_mat("RiverWater")
M_ROCK = rock_mat("CanyonRock", (0.26, 0.14, 0.08), (0.52, 0.33, 0.20))
M_BED = rock_mat("Bedrock", (0.16, 0.14, 0.13), (0.32, 0.29, 0.27), band_scale=0.08)
M_SED = soil("Sediment", (0.20, 0.14, 0.09), (0.36, 0.27, 0.17), 1.1, stones=0.10)
M_FILL = soil("RockFill", (0.30, 0.27, 0.24), (0.52, 0.47, 0.42), 2.6, stones=0.22)
M_CONC = flat("Concrete", (0.58, 0.57, 0.54), 0.75, 0.0, HOT, 0.45, noise=0.12)
M_DAM = flat("DamConcrete", (0.66, 0.65, 0.62), 0.7, 0.0, GOLD, 1.2, noise=0.10)
M_HOT = flat("HotConcrete", (0.30, 0.20, 0.16), 0.7, 0.0, HOT, 0.8, noise=0.25)
M_PLUG = flat("PlugConcrete", (0.62, 0.61, 0.58), 0.75, 0.0, GOLD, 3.0, noise=0.12)
M_PIPE = flat("CoolPipe", (0.55, 0.57, 0.6), 0.3, 1.0, CYAN, 3.0)
M_HOLE = flat("DrillHole", (0.03, 0.03, 0.03), 0.9)
M_TRUCK = flat("TruckYellow", (0.95, 0.68, 0.06), 0.4, 0.1)
M_TIRE = flat("Tire", (0.03, 0.03, 0.03), 0.8)
M_STEEL = flat("RigSteel", (0.85, 0.55, 0.06), 0.4, 0.2, GOLD, 2.0)
M_STREAK = flat("FlowStreak", (0.9, 0.97, 1.0), 0.3, 0.0, (0.85, 0.97, 1.0), 1.5)
M_CURTAIN = flat("GroutCurtain", (0.05, 0.25, 0.3), 0.4, 0.0, CYAN, 4.0)
M_GLOW_C = flat("ArrowCyan", (0.02, 0.05, 0.06), 0.5, 0.0, CYAN, 3.0)
M_GLOW_R = flat("ArrowRed", (0.06, 0.01, 0.01), 0.5, 0.0, RED, 2.2)
M_GLOW_G = flat("ArrowGold", (0.06, 0.04, 0.0), 0.5, 0.0, GOLD, 3.5)

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

# ---------- canyon layout (metres, illustrative; river flows +x -> -x, section planes y = YC and y = 0, camera on -y) ----------
XA = 60.0                                           # model half length along the river
W = 12.0                                            # valley half width (walls at |y| = W)
YC = -15.0                                          # cut 1: near tunnel axis
YE = 40.0                                           # model half depth
Z_TOP, Z_W, Z_BED, Z_ROCK, Z_DEEP = 30.0, 3.0, 0.0, -4.0, -30.0   # canyon rim, river surface, riverbed, bedrock top, model bottom
T_R, T_Z, X_IN, X_OUT = 2.6, 3.6, 26.0, -36.0
Z_BENCH = T_Z + T_R + 2.3                           # near bench height after cut 1     # tunnel radius, axis height, inlet x, outlet x
X_CU, X_CD = 18.0, -28.0                            # cofferdam centres (upstream / downstream)

# band A (front of the near tunnel axis): drops on "open"
BAND_A = box("NearRock_A", -XA, XA, -30.0, YC, Z_DEEP, Z_TOP, M_ROCK)
BAND_BT = box("NearRock_BTop", -XA, XA, YC, -W, Z_BENCH, Z_TOP, M_ROCK)      # near wall above the bench: drops with band A
# band B (near tunnel axis to the valley): holds the tunnel groove + connectors; drops on "now"
BAND_B = box("NearRock_B", -XA, XA, YC, -W, Z_DEEP, Z_BENCH, M_ROCK)
for nm, a, b_ in (("tun", (X_OUT, YC, T_Z), (X_IN, YC, T_Z)),):
    ct = cyl("cut", T_R, a, b_, None, axis="X"); boolean(BAND_B, ct); delete(ct)
for x in (X_IN, X_OUT):
    ct = cyl("cut", T_R, (x, YC - 0.5, T_Z), (x, -W + 0.5, T_Z), None, axis="Y"); boolean(BAND_B, ct); delete(ct)
# tunnel filler (rock) shrinks toward the outlet while the tunnel is blasted; tunnel water grows from the inlet
TUN_FILL = cyl("TunnelFiller", T_R - 0.01, (X_OUT, YC, T_Z), (X_IN, YC, T_Z), M_ROCK, axis="X", pivot=(X_OUT, YC, T_Z), keep_y=YC + 0.01)
TUN_WATER = cyl("TunnelWater", T_R - 0.25, (X_OUT, YC, T_Z), (X_IN, YC, T_Z), M_WATER, axis="X", pivot=(X_IN, YC, T_Z), keep_y=YC + 0.03)
# far wall (band E) with the far tunnel's inlet/outlet portals
BAND_E = box("FarRock_E", -XA, XA, W, YE, Z_DEEP, Z_TOP, M_ROCK)
for x in (X_IN, X_OUT):
    ct = cyl("cut", T_R, (x, W - 0.5, T_Z), (x, W + 4.0, T_Z), None, axis="Y"); boolean(BAND_E, ct); delete(ct)
PORTAL_FILL = [cyl(f"PortalFill{x:+.0f}", T_R - 0.01, (x, W - 0.01, T_Z), (x, W + 4.0, T_Z), M_ROCK, axis="Y") for x in (X_IN, X_OUT)]
# valley: bedrock + sediment, front (band C, drops on "now") and back (band D) halves
BED_C = box("Bedrock_C", -XA, XA, -W, 0, Z_DEEP, Z_ROCK, M_BED)
BED_D = box("Bedrock_D", -XA, XA, 0, W, Z_DEEP, Z_ROCK, M_BED)
SED_C = box("Sediment_C", -XA, XA, -W, 0, Z_ROCK, Z_BED, M_SED)
X_DIG0, X_DIG1 = -20.0, 6.0
SED_D = [box("Sediment_D_dn", -XA, X_DIG0, 0, W, Z_ROCK, Z_BED, M_SED), box("Sediment_D_up", X_DIG1, XA, 0, W, Z_ROCK, Z_BED, M_SED)]
CHUNKS = []
for i in range(4):
    x0 = X_DIG0 + (X_DIG1 - X_DIG0) * i / 4; x1 = X_DIG0 + (X_DIG1 - X_DIG0) * (i + 1) / 4
    CHUNKS.append(box(f"DigChunk_{i}", x0, x1, 0.0, W, Z_ROCK, Z_BED, M_SED, pivot=((x0 + x1) / 2, W / 2, Z_ROCK)))
# river water segments, front (y<0) and back halves; the mid segment drains between the cofferdams
WSEG = {}
for nm, x0, x1 in (("up", X_CU, XA), ("mid", X_CD, X_CU), ("dn", -XA, X_CD)):
    WSEG[nm] = (box(f"Water_{nm}_F", x0, x1, -W + 0.02, 0, Z_BED, Z_W, M_WATER, pivot=(0, 0, Z_BED)),
                box(f"Water_{nm}_B", x0, x1, 0, W - 0.02, Z_BED, Z_W, M_WATER, pivot=(0, 0, Z_BED)))
# reservoir: sweeps from the upstream cofferdam to the dam face, then rises
RES = box("Reservoir", 2.4, XA, 0.02, W + 0.5, Z_ROCK, 22.0, M_WATER, pivot=(XA, 0, Z_ROCK))

# ---------- cofferdams: rock-fill trapezoids end-dumped from the far bank ----------
def coffer(name, xc):
    poly = [(xc - 3.6, Z_BED - 0.05), (xc + 3.6, Z_BED - 0.05), (xc + 1.6, Z_W + 1.8), (xc - 1.6, Z_W + 1.8)]
    back = prism(name + "_B", poly, 0.0, W, M_FILL, CG, pivot=(xc, W, Z_BED))
    front = prism(name + "_F", poly, -W, 0.0, M_FILL, CG, pivot=(xc, 0.0, Z_BED))
    return back, front
COF_U, COF_D = coffer("CofferdamUp", X_CU), coffer("CofferdamDown", X_CD)
T_CU0, T_CU1 = C["dump"] - 0.1, C["within"] + 0.6
T_CD0, T_CD1 = C["second"] - 0.1, C["downstream"] + 1.0
def coffer_front(t, t0, t1): return seg(t, t0, t1, W, -W, lin)       # y of the advancing tip
# dump truck on the advancing tip of the upstream cofferdam
TRUCK = empty("Truck")
parent(box("Truck_Cab", -0.9, 0.9, 0.5, 1.9, 0.5, 2.0, M_TRUCK, CP), TRUCK)
TRUCK_BED = empty("Truck_BedPivot"); parent(TRUCK_BED, TRUCK); TRUCK_BED.location = (0, -2.3, 0.9)
parent(box("Truck_Bed", -1.0, 1.0, 0.0, 2.6, 0.0, 1.0, M_TRUCK, CP), TRUCK_BED)
for i, (wx, wy) in enumerate(((-0.95, -1.6), (0.95, -1.6), (-0.95, 1.2), (0.95, 1.2))):
    parent(cyl(f"Truck_Wheel{i}", 0.42, (wx - 0.18, wy, 0.42), (wx + 0.18, wy, 0.42), M_TIRE, CP, axis="X", seg_n=16), TRUCK)
BOULDERS = []
for i in range(10):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=random.uniform(0.45, 0.8))
    for v in bm.verts: v.co *= random.uniform(0.8, 1.15)
    o = mesh_obj(f"Boulder_{i}", bm, M_FILL, CP); o["ph"] = random.random(); o["dx"] = random.uniform(-1.6, 1.6); BOULDERS.append(o)

# ---------- grout: drill rig, drill hole, grout fill, curtain, seepage arrow ----------
X_GC = 3.0
RIG = empty("DrillRig")
parent(box("Rig_Base", X_GC - 0.8, X_GC + 0.8, 0.6, 2.4, Z_ROCK, Z_ROCK + 0.7, M_STEEL, CP), RIG)
parent(box("Rig_Mast", X_GC - 0.15, X_GC + 0.15, 0.85, 1.15, Z_ROCK + 0.7, Z_ROCK + 7.0, M_STEEL, CP), RIG)
parent(box("Rig_Rod", X_GC - 0.05, X_GC + 0.05, -0.05, 0.05, Z_ROCK - 0.3, Z_ROCK + 6.5, M_TIRE, CP), RIG)
Z_HOLE = -18.0
HOLE = cyl("DrillHole", 0.2, (X_GC, 0.0, Z_HOLE), (X_GC, 0.0, Z_ROCK), M_HOLE, CP, pivot=(X_GC, 0.0, Z_ROCK), seg_n=16)
GROUT = cyl("GroutFill", 0.22, (X_GC, 0.0, Z_HOLE), (X_GC, 0.0, Z_ROCK), M_GLOW_C, CP, pivot=(X_GC, 0.0, Z_ROCK), seg_n=16)
CURTAIN = box("GroutCurtain", X_GC - 0.6, X_GC + 0.6, -0.03, W, Z_HOLE, Z_ROCK - 0.02, M_CURTAIN, CP, pivot=(X_GC, 0, Z_ROCK))
SEEP = arrow("SeepArrow", M_GLOW_R, 7.0, 0.16); SEEP.rotation_euler = (0, 0, math.pi)

# ---------- the dam: profile, blocks, pipes, monolith ----------
PROFILE = [(-18.0, Z_ROCK), (4.0, Z_ROCK), (2.5, 26.0), (0.7, 26.0)]
def face_up_x(z): return 4.0 + (z - Z_ROCK) * (2.5 - 4.0) / (26.0 - Z_ROCK)
def face_dn_x(z): return -18.0 + (z - Z_ROCK) * (0.7 + 18.0) / (26.0 - Z_ROCK)
def clip(poly, x0, x1, z0, z1):
    def clip_edge(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            if inside(b):
                if not inside(a): out.append(inter(a, b))
                out.append(b)
            elif inside(a): out.append(inter(a, b))
        return out
    def ix(xv):
        return lambda a, b: (xv, a[1] + (b[1] - a[1]) * (xv - a[0]) / (b[0] - a[0]))
    def iz(zv):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (zv - a[1]) / (b[1] - a[1]), zv)
    pts = poly[:]
    for ins, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)), (lambda p: p[1] >= z0, iz(z0)), (lambda p: p[1] <= z1, iz(z1))):
        pts = clip_edge(pts, ins, inter)
        if len(pts) < 3: return None
    return pts
def area(p): return abs(sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))) / 2
X_E = [-18.0, -13.5, -9.0, -4.5, 0.0, 4.0]
Y_E = [0.0, 4.0, 8.0, 12.0]
Z_E = [Z_ROCK + 3.0 * k for k in range(11)]          # 10 lifts, 3 m each (illustrative)
GAP = 0.12
BLOCKS = []
for k in range(10):
    for i in range(5):
        for j in range(3):
            pc = clip(PROFILE, X_E[i] + GAP / 2, X_E[i + 1] - GAP / 2, Z_E[k] + (GAP / 2 if k else 0.0), Z_E[k + 1] - GAP / 2)
            if not pc or area(pc) < 0.4: continue
            y0 = Y_E[j] + (0.0 if j == 0 else GAP / 2); y1 = Y_E[j + 1] - (0.0 if j == 2 else GAP / 2)
            cx = sum(p[0] for p in pc) / len(pc)
            o = prism(f"Block_{k}_{i}_{j}", pc, y0, y1, M_CONC, CD, pivot=(cx, (y0 + y1) / 2, Z_E[k]))
            o["k"], o["i"], o["j"] = k, i, j; BLOCKS.append(o)
PH1_T0, PH1_T1 = C["so"] - 0.05, C["inside"] - 0.15           # lifts 0-3
PH3_T0, PH3_T1 = C["hoover3"] - 0.1, C["then2"] - 0.25        # lifts 4-9
for o in BLOCKS:
    k, i, j = o["k"], o["i"], o["j"]
    stag = 0.45 * ((i + j) % 2) + 0.15 * j
    if k < 4: o["t"] = PH1_T0 + (PH1_T1 - PH1_T0 - 0.3) * (k + stag) / 4.6
    else: o["t"] = PH3_T0 + (PH3_T1 - PH3_T0 - 0.3) * (k - 4 + stag) / 6.6
MONO_HOT = prism("Monolith_Hot", PROFILE, 0.0, W, M_HOT, CD, pivot=(-7.0, W / 2, Z_ROCK))
DAM = prism("Dam_Solid", PROFILE, 0.0, W, M_DAM, CD)
OUTLINE = [bar_xz(f"Outline_{n}", PROFILE[n], PROFILE[(n + 1) % 4], -0.08, M_GLOW_G, 0.22) for n in range(4)]
CRACKS = []
for c_i, (x0, z0) in enumerate(((-3.0, 24.0), (-9.5, 14.0), (-1.0, 9.0))):
    pts = [(x0, z0)]
    for s in range(6):
        x, z = pts[-1]; pts.append((x + random.uniform(-1.4, 1.0), z - random.uniform(1.6, 2.6)))
    pts = [(min(max(x, face_dn_x(z) + 0.4), face_up_x(z) - 0.4), max(z, Z_ROCK + 0.5)) for x, z in pts]
    CRACKS.append([bar_xz(f"Crack_{c_i}_{s}", pts[s], pts[s + 1], -0.07, M_GLOW_R, 0.42) for s in range(len(pts) - 1)])
# cooling pipes: a serpentine on top of lift 3 (close-up), x-ray lines on the section face for every lift
Z_PIPE = Z_E[4] + 0.12
xl, xr = face_dn_x(Z_E[4]) + 0.8, face_up_x(Z_E[4]) - 0.8
pts = []
for n, yv in enumerate([1.0, 3.0, 5.0, 7.0, 9.0, 11.0]):
    pts += [(xl, yv), (xr, yv)] if n % 2 == 0 else [(xr, yv), (xl, yv)]
cu = bpy.data.curves.new("CoolPipeSerp", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.14; cu.bevel_resolution = 3
sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
for n, (x, y) in enumerate(pts): sp.points[n].co = (x, y, Z_PIPE, 1)
cu.materials.append(M_PIPE)
SERP = bpy.data.objects.new("CoolPipeSerp", cu); CP.objects.link(SERP); SERP["glow"] = 0.0
XRAY = []
for k in range(10):
    zc = Z_E[k] + 1.5
    XRAY.append(bar_xz(f"XrayPipe_{k}", (face_dn_x(zc) + 0.7, zc), (face_up_x(zc) - 0.6, zc), -0.06, M_PIPE, 0.16))
    XRAY[-1]["k"] = k
JOINTS = []
for xv in X_E[1:-1]:
    zt = min(26.0, Z_ROCK + (xv + 18.0) / (0.7 + 18.0) * (26.0 - Z_ROCK))
    JOINTS.append(bar_xz(f"JointV_{xv:+.1f}", (xv, Z_ROCK), (xv, zt), -0.05, M_GLOW_C, 0.14))
for zv in Z_E[1:-1]:
    JOINTS.append(bar_xz(f"JointH_{zv:+.0f}", (face_dn_x(zv), zv), (face_up_x(zv), zv), -0.05, M_GLOW_C, 0.14))
# water pressure arrows on the upstream face (longer = deeper) and the thin/huge brackets
PRESS = []
for n, z in enumerate((22.0, 16.0, 10.0, 4.0, -1.0)):
    L = 1.6 + (26.0 - z) / 30.0 * 7.5
    a = arrow(f"Press_{n}", M_GLOW_C, L, 0.15 + 0.03 * n); a.rotation_euler = (0, 0, math.pi)
    a.location = (face_up_x(z) + 0.25 + L, -0.4, z); a["n"] = n; PRESS.append(a)
BR_TOP = [bar_xz("BracketTop", (0.7, 27.0), (2.5, 27.0), -0.2, M_GLOW_G, 0.25), bar_xz("BracketTopL", (0.7, 26.5), (0.7, 27.5), -0.2, M_GLOW_G, 0.2),
          bar_xz("BracketTopR", (2.5, 26.5), (2.5, 27.5), -0.2, M_GLOW_G, 0.2)]
BR_BOT = [bar_xz("BracketBot", (-18.0, -5.2), (4.0, -5.2), -0.2, M_GLOW_G, 0.3), bar_xz("BracketBotL", (-18.0, -5.9), (-18.0, -4.5), -0.2, M_GLOW_G, 0.25),
          bar_xz("BracketBotR", (4.0, -5.9), (4.0, -4.5), -0.2, M_GLOW_G, 0.25)]
# tunnel plug (far inlet), outlet flow arrow, hook route arrow
PLUG = cyl("TunnelPlug", T_R - 0.02, (X_IN, W - 0.05, T_Z), (X_IN, W + 3.5, T_Z), M_PLUG, CP, axis="Y", pivot=(X_IN, W + 3.5, T_Z))
OUT_ARROW = arrow("OutletArrow", M_GLOW_C, 5.0, 0.2); OUT_ARROW.rotation_euler = (0, 0, -math.pi / 2); OUT_ARROW.location = (X_OUT, W - 0.3, Z_W + 0.6)
ROUTE = [arrow("RouteArrow_in", M_GLOW_G, 7.0, 0.3), arrow("RouteArrow_out", M_GLOW_G, 7.0, 0.3)]
ROUTE[0].location = (X_IN + 6, -3.0, Z_W + 1.2); ROUTE[0].rotation_euler = (0, 0, math.radians(180 + 40))
ROUTE[1].location = (X_OUT + 2, -9.0, Z_W + 1.2); ROUTE[1].rotation_euler = (0, 0, math.radians(180 - 40))
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.4)
BLAST = mesh_obj("BlastFlash", bm, M_GLOW_G, CP)
# flow streaks: river surface + tunnel
STREAKS = []
for i in range(46):
    o = box(f"Streak_{i}", -0.9, 0.9, -0.05, 0.05, -0.015, 0.015, M_STREAK, CP); o["y"] = random.uniform(-W + 1.0, W - 1.0); o["ph"] = random.random()
    STREAKS.append(o)
TSTREAKS = []
for i in range(12):
    o = box(f"TStreak_{i}", -0.9, 0.9, -0.03, 0.03, -0.05, 0.05, M_STREAK, CP); o["z"] = T_Z + random.uniform(-1.3, 1.1); o["ph"] = random.random()
    TSTREAKS.append(o)

# ---------- per-frame bake ----------
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

T_CUT1, T_CUT2 = C["open"] - 0.1, C["now"] - 0.05
T_TUN0, T_TUN1 = C["blast"] - 0.1, C["walls"] + 0.5
T_FLOW0, T_FLOW1 = C["turns"] - 0.1, C["tunnels2"] + 0.6
T_DRAIN0, T_DRAIN1 = C["riverbed"], C["drains"] + 0.9
T_SWEEP0, T_SWEEP1, T_RISE1 = C["river2"] - 0.1, C["fills"], C["valley"] + 0.7
events = {"blast": [], "boulder_splash": [], "cofferdam_close": [round(T_CU1, 3), round(T_CD1, 3)], "cut": [round(T_CUT1, 3), round(T_CUT2, 3)],
          "chunk_lift": [], "drill": round(C["drill"], 3), "block_land": [], "crack": round(C["cracked"], 3), "plug": round(C["plugged"], 3)}
for k in range(6): events["blast"].append(round(T_TUN0 + (T_TUN1 - T_TUN0) * k / 5, 3))
for i in range(4): events["chunk_lift"].append(round(C["dig"] - 0.05 + 0.32 * i, 3))
for o in BLOCKS: events["block_land"].append(round(o["t"] + 0.3, 3))
events["block_land"] = sorted(set(round(x, 1) for x in events["block_land"]))

FRONT_C = [BED_C, SED_C, WSEG["up"][0], WSEG["mid"][0], WSEG["dn"][0], COF_U[1], COF_D[1]]
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS
    # cut 1: band A drops; cut 2: band B + front of the valley drop
    dz = seg(t, T_CUT1, T_CUT1 + 0.85, 0.0, -70.0, lambda p: lin(p) ** 2); rec(BAND_A, "location", 2, fr, dz); setvis(BAND_A, fr, t > T_CUT1 + 0.85)
    rec(BAND_BT, "location", 2, fr, -dz); setvis(BAND_BT, fr, t > T_CUT1 + 0.85)
    dz = seg(t, T_CUT2, T_CUT2 + 0.85, 0.0, -70.0, lambda p: lin(p) ** 2)
    rec(BAND_B, "location", 2, fr, dz); setvis(BAND_B, fr, t > T_CUT2 + 0.85)
    rec(BED_C, "location", 2, fr, dz); rec(SED_C, "location", 2, fr, dz)
    setvis(BED_C, fr, t > T_CUT2 + 0.85); setvis(SED_C, fr, t > T_CUT2 + 0.85)
    # tunnel filler + water
    tf = seg(t, T_TUN0, T_TUN1, 1.0, 0.0, lin); setvis(TUN_FILL, fr, tf <= 0.002 or t > T_CUT2 + 0.85)
    rec(TUN_FILL, "scale", 0, fr, max(0.002, tf)); rec(TUN_FILL, "location", 2, fr, T_Z + dz)
    tw = seg(t, T_FLOW0, T_FLOW1, 0.0, 1.0, lin); setvis(TUN_WATER, fr, tw <= 0.002 or t > T_CUT2 + 0.85)
    rec(TUN_WATER, "scale", 0, fr, max(0.002, tw)); rec(TUN_WATER, "location", 2, fr, T_Z + dz)
    for p in PORTAL_FILL: setvis(p, fr, t > T_TUN0 + 0.6)
    xf = X_IN + (X_OUT - X_IN) * (1 - tf)
    bon = T_TUN0 <= t < T_TUN1
    setvis(BLAST, fr, not bon)
    if bon:
        setloc(BLAST, fr, (xf, YC - 0.6, T_Z)); fl = 0.5 + 0.5 * abs(math.sin(t * 23.0)); setscale(BLAST, fr, (fl,) * 3); rec(BLAST, '["glow"]', -1, fr, 0.6 + fl)
    # cofferdams
    for (cb, cf), (t0, t1) in ((COF_U, (T_CU0, T_CU1)), (COF_D, (T_CD0, T_CD1))):
        yf = coffer_front(t, t0, t1)
        sb = (W - yf) / W; setvis(cb, fr, t < t0); rec(cb, "scale", 1, fr, max(0.002, min(1.0, sb)))
        sf = -yf / W; setvis(cf, fr, sf <= 0.002 or t > T_CUT2 + 0.85); rec(cf, "scale", 1, fr, max(0.002, min(1.0, sf)))
        rec(cf, "location", 2, fr, Z_BED + dz)
        g = pulse(t, C["cofferdam"], 1.0, 0.0)
    # truck + boulders on the upstream cofferdam
    yf = coffer_front(t, T_CU0, T_CU1)
    ton = C["trucks"] - 0.25 <= t < T_CU1 - 0.2
    setvis(TRUCK, fr, not ton)
    if ton:
        setloc(TRUCK, fr, (X_CU, yf + 2.6 + seg(t, C["trucks"] - 0.25, C["trucks"] + 0.3, 6.0, 0.0, out3), Z_W + 1.8))
        rec(TRUCK_BED, "rotation_euler", 0, fr, math.radians(32 + 10 * math.sin(t * 6.0)) if t > C["dump"] - 0.1 else 0.0)
    for b in BOULDERS:
        don = C["dump"] - 0.1 <= t < T_CU1 - 0.2
        ph = ((t - C["dump"]) / 0.8 + b["ph"]) % 1.0
        setvis(b, fr, not don)
        if don:
            setloc(b, fr, (X_CU + b["dx"], yf - 0.2 - 0.8 * ph, Z_W + 2.6 - 3.0 * ph * ph)); rec(b, "rotation_euler", 0, fr, ph * 4.0)
    # river segments
    for nm, (wf, wb) in WSEG.items():
        if nm == "mid":
            lv = seg(t, T_DRAIN0, T_DRAIN1, Z_W, Z_BED + 0.05)
            gone = t > T_DRAIN1
        else:
            lv = Z_W; gone = nm == "up" and t >= T_SWEEP0 + 0.05
        s = max(0.002, (lv - Z_BED) / (Z_W - Z_BED))
        rec(wb, "scale", 2, fr, s); setvis(wb, fr, gone)
        rec(wf, "scale", 2, fr, s); rec(wf, "location", 2, fr, Z_BED + dz); setvis(wf, fr, gone or t > T_CUT2 + 0.85)
    # cofferdam tip glow
    for cb, cf in (COF_U,):
        for o in (cb, cf): rec(o, '["glow"]', -1, fr, 0.0)
    # dig chunks
    for i, ch in enumerate(CHUNKS):
        t0 = C["dig"] - 0.05 + 0.32 * i
        if t < t0: setvis(ch, fr, False); rec(ch, "location", 2, fr, Z_ROCK); setscale(ch, fr, (1, 1, 1))
        elif t < t0 + 0.6:
            setvis(ch, fr, False); rec(ch, "location", 2, fr, Z_ROCK + seg(t, t0, t0 + 0.6, 0.0, 14.0)); s = seg(t, t0 + 0.2, t0 + 0.6, 1.0, 0.05); setscale(ch, fr, (s, s, s))
        else: setvis(ch, fr, True)
    rec(BED_D, '["glow"]', -1, fr, 0.0)
    # drill rig, hole, grout, curtain, seepage
    ron = C["drill"] - 0.3 <= t < C["hardens"] + 0.2
    setvis(RIG, fr, not ron)
    if ron: rec(RIG, "location", 2, fr, seg(t, C["drill"] - 0.3, C["drill"] + 0.1, 8.0, 0.0, out3) + seg(t, C["drill"], C["holes"] + 0.6, 0.0, -0.0) + 0.02 * math.sin(t * 70))
    hz = seg(t, C["drill"], C["holes"] + 0.7, 0.0, 1.0, lin); setvis(HOLE, fr, t < C["drill"] or t > C["next"]); rec(HOLE, "scale", 2, fr, max(0.002, hz))
    gz = seg(t, C["pump"], C["liquid"] + 0.9, 0.0, 1.0, lin); setvis(GROUT, fr, t < C["pump"] or t > C["next"]); rec(GROUT, "scale", 2, fr, max(0.002, gz))
    rec(GROUT, '["glow"]', -1, fr, 0.5 + 0.5 * pulse(t, C["liquid"], 0.8))
    cv = seg(t, C["hardens"], C["curtain"] + 0.3, 0.0, 1.0)
    setvis(CURTAIN, fr, cv <= 0.002 or t > C["concrete"] + 0.3); rec(CURTAIN, "scale", 2, fr, max(0.002, cv))
    rec(CURTAIN, '["glow"]', -1, fr, 0.35 + 0.65 * pulse(t, C["curtain"], 0.9) + 0.5 * pulse(t, C["underneath"], 0.6))
    son = C["sneak"] - 0.1 <= t < C["next"] - 0.1
    setvis(SEEP, fr, not son)
    if son:
        L = seg(t, C["sneak"] - 0.1, C["underneath"] + 0.2, 0.05, 1.0, out3); rec(SEEP, "scale", 0, fr, max(0.02, L))
        setloc(SEEP, fr, (X_GC + 0.9 + 7.0, -0.35, -10.0)); rec(SEEP, '["glow"]', -1, fr, 0.7 + 0.3 * math.sin(t * 9))
    # outline, hot monolith, cracks
    setvis_out = not (C["concrete"] - 0.1 <= t < C["heats"] + 0.2)
    for o in OUTLINE: setvis(o, fr, setvis_out); rec(o, '["glow"]', -1, fr, 0.5 + 0.5 * pulse(t, C["concrete"], 0.8) + 0.6 * pulse(t, C["once"], 0.5))
    mon = C["concrete2"] - 0.1 <= t < C["so"] - 0.05
    setvis(MONO_HOT, fr, not mon)
    rec(MONO_HOT, "scale", 2, fr, max(0.002, seg(t, C["concrete2"] - 0.1, C["hardens2"] + 0.3, 0.0, 1.0)))
    rec(MONO_HOT, '["glow"]', -1, fr, seg(t, C["heats"] - 0.1, C["hardens2"] + 0.4, 0.15, 1.0) * (0.85 + 0.15 * math.sin(t * 5.0)) if mon else 0.0)
    for c_i, cr in enumerate(CRACKS):
        for s_i, o in enumerate(cr):
            ts = C["cracked"] - 0.05 + 0.04 * s_i + 0.06 * c_i
            setvis(o, fr, not (ts <= t < C["so"] - 0.05)); rec(o, '["glow"]', -1, fr, 0.6 + 0.6 * pulse(t, C["cracked"], 0.4))
    # blocks
    for o in BLOCKS:
        t0 = o["t"]; on = t0 <= t < C["solid"]
        setvis(o, fr, not on)
        if on: rec(o, "scale", 2, fr, max(0.002, seg(t, t0, t0 + 0.3, 0.0, 1.0, out3)))
        if o["k"] < 4: hg = seg(t, t0, t0 + 0.3, 0.0, 0.9) * (1.0 - seg(t, C["pulls"], C["out"] + 0.6, 0.0, 1.0))
        else: hg = seg(t, t0, t0 + 0.3, 0.0, 0.7) * (1.0 - seg(t, t0 + 0.5, t0 + 1.4, 0.0, 1.0))
        rec(o, '["glow"]', -1, fr, max(0.0, hg))
    # pipes
    son = C["layer"] - 0.2 <= t < PH3_T0 + 0.6
    setvis(SERP, fr, not son)
    rec(cu, "bevel_factor_end", -1, fr, seg(t, C["layer"] - 0.2, C["pipes"] + 0.5, 0.0, 1.0, lin))
    rec(SERP, '["glow"]', -1, fr, 0.15 + 0.85 * seg(t, C["cold"] - 0.1, C["cold"] + 0.3, 0.0, 1.0) * (0.75 + 0.25 * math.sin(t * 8)))
    for o in XRAY:
        k = o["k"]; t0 = (C["hoover3"] + 0.08 * k) if k < 4 else next(b["t"] for b in BLOCKS if b["k"] == k) + 0.3
        setvis(o, fr, not (t0 <= t < C["filled"] + 0.35)); rec(o, '["glow"]', -1, fr, 0.7 + 0.3 * pulse(t, C["miles"], 0.6))
    for o in JOINTS:
        setvis(o, fr, not (C["gaps"] - 0.1 <= t < C["solid"] + 0.4))
        rec(o, '["glow"]', -1, fr, seg(t, C["gaps"] - 0.1, C["gaps"] + 0.2, 0.0, 1.0) * (1.0 - seg(t, C["filled"], C["solid"] + 0.3, 0.0, 0.85)))
    setvis(DAM, fr, t < C["solid"]); rec(DAM, '["glow"]', -1, fr, 0.5 * pulse(t, C["solid"], 0.5) + 0.35 * pulse(t, C["tall"], 0.8))
    # pressure arrows + brackets
    for a in PRESS:
        n = a["n"]; t0 = C["pressure"] - 0.1 + 0.18 * n; on = t0 <= t < C["finally"] - 0.1
        setvis(a, fr, not on)
        if on: rec(a, "scale", 0, fr, max(0.02, seg(t, t0, t0 + 0.4, 0.0, 1.0, out3)))
        rec(a, '["glow"]', -1, fr, 0.7 + 0.3 * pulse(t, C["depth"] + 0.1 * n, 0.4))
    for o in BR_TOP: setvis(o, fr, not (C["thin"] - 0.05 <= t < C["finally"] - 0.1)); rec(o, '["glow"]', -1, fr, 0.6 + 0.6 * pulse(t, C["top"], 0.4))
    for o in BR_BOT: setvis(o, fr, not (C["huge"] - 0.05 <= t < C["finally"] - 0.1)); rec(o, '["glow"]', -1, fr, 0.6 + 0.6 * pulse(t, C["bottom"], 0.4))
    # plug, outlet arrow, reservoir
    setvis(PLUG, fr, t < C["plugged"] - 0.1); rec(PLUG, "scale", 1, fr, max(0.002, seg(t, C["plugged"] - 0.1, C["plugged"] + 0.4, 0.0, 1.0, out3)))
    rec(PLUG, '["glow"]', -1, fr, pulse(t, C["plugged"], 0.9, 0.8))
    oon = C["outlets"] - 0.1 <= t < C["would"]
    setvis(OUT_ARROW, fr, not oon)
    if oon: rec(OUT_ARROW, "scale", 0, fr, max(0.02, seg(t, C["outlets"] - 0.1, C["outlets"] + 0.4, 0.0, 1.0, out3))); rec(OUT_ARROW, '["glow"]', -1, fr, 1.0)
    ron = t >= T_SWEEP0
    setvis(RES, fr, not ron)
    sx = seg(t, T_SWEEP0, T_SWEEP1, (XA - X_CU) / (XA - 2.4), 1.0)
    sz = seg(t, T_SWEEP1, T_RISE1, (Z_W - Z_ROCK) / (22.0 - Z_ROCK), 1.0)
    rec(RES, "scale", 0, fr, sx); rec(RES, "scale", 2, fr, sz)
    # hook route arrows
    for n, a in enumerate(ROUTE):
        t0 = C["move"] - 0.1 + 0.25 * n; on = t0 <= t < T_CUT1
        setvis(a, fr, not on)
        if on: rec(a, "scale", 0, fr, max(0.02, seg(t, t0, t0 + 0.5, 0.0, 1.0, out3))); rec(a, '["glow"]', -1, fr, 0.8 + 0.2 * math.sin(t * 8))
    # flow streaks
    closed = t >= T_CU1
    for o in STREAKS:
        x = XA - ((t * 4.5 + o["ph"] * 2 * XA) % (2 * XA)); y = o["y"]
        if not closed: wet = True
        else: wet = (x > X_IN + 1.0) or (x < X_OUT - 1.0)
        if t >= T_CUT2 and y < 0.3: wet = False
        if t >= T_SWEEP0: wet = False
        if X_CU - 3.8 < x < X_CU + 3.8 and t > T_CU0 + (W - y) / (2 * W) * (T_CU1 - T_CU0): wet = False
        if X_CD - 3.8 < x < X_CD + 3.8 and t > T_CD0 + (W - y) / (2 * W) * (T_CD1 - T_CD0): wet = False
        if t < 0.0: wet = False
        setvis(o, fr, not wet)
        if wet: setloc(o, fr, (x, y, Z_W + 0.03))
    for o in TSTREAKS:
        x = X_IN - ((t * 7.0 + o["ph"] * (X_IN - X_OUT)) % (X_IN - X_OUT))
        on = T_FLOW0 <= t < T_CUT2 and x > X_IN - (X_IN - X_OUT) * seg(t, T_FLOW0, T_FLOW1, 0.0, 1.0, lin)
        setvis(o, fr, not on)
        if on: setloc(o, fr, (x, YC - 0.05, o["z"]))
write_tracks(); TRACKS.clear()

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 30
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tcn = cam.constraints.new("TRACK_TO"); tcn.target = TGT; tcn.track_axis = "TRACK_NEGATIVE_Z"; tcn.up_axis = "UP_Y"
cam_d.clip_end = 800
SEC = ((-6.0, -62.0, 12.0), (-6.0, 0.0, 10.5), 35)             # the whole dam section
SHOTS = [  # (time, camera loc, target, lens)
    (0.0, (-100.0, -6.0, 40.0), (0.0, 0.0, 2.0), 30),
    (C["river"], (-92.0, -8.0, 40.0), (0.0, 0.0, 2.0), 30),
    (C["cut"], (-80.0, -30.0, 44.0), (0.0, -2.0, 3.0), 30),
    (C["open"] + 0.9, (14.0, -44.0, 14.0), (14.0, -13.0, 3.6), 26),
    (C["blast"], (16.0, -42.0, 13.0), (16.0, -13.0, 3.6), 26),
    (C["walls"] + 0.5, (-24.0, -42.0, 13.0), (-24.0, -13.0, 3.6), 26),
    (C["four"] + 0.4, (-4.0, -60.0, 26.0), (-4.0, -10.0, 3.0), 26),
    (C["trucks"], (-14.0, -42.0, 60.0), (13.0, 2.0, 1.0), 32),
    (C["cofferdam"], (-6.0, -36.0, 48.0), (15.0, 2.0, 2.0), 32),
    (C["within"] + 0.4, (-34.0, -60.0, 58.0), (-4.0, -4.0, 2.0), 30),
    (C["second"] + 0.3, (-38.0, -50.0, 54.0), (-14.0, 0.0, 1.0), 30),
    (C["drains"] + 0.5, (-30.0, -60.0, 56.0), (-4.0, 0.0, 1.0), 30),
    (C["now"] + 0.1, (-28.0, -60.0, 48.0), (-6.0, 0.0, 1.0), 30),
    (C["now"] + 1.0, (-8.0, -50.0, 8.0), (-7.0, 0.0, -1.0), 35),
    (C["bedrock"], (-7.0, -45.0, 6.0), (-7.0, 0.0, -2.0), 35),
    (C["drill"], (4.0, -32.0, -3.0), (4.0, 0.0, -8.0), 35),
    (C["curtain"], (5.0, -42.0, -3.0), (5.0, 0.0, -8.0), 35),
    (C["underneath"] + 0.3, (7.0, -44.0, -3.0), (6.0, 0.0, -8.0), 35),
    (C["next"] + 0.3, SEC[0], SEC[1], 35),
    (C["hundred"], (-6.0, -57.0, 11.0), (-6.0, 0.0, 10.5), 35),
    (C["cracked"] + 0.4, (-5.0, -53.0, 10.0), (-6.0, 0.0, 10.0), 35),
    (C["so"] + 0.4, (-36.0, -48.0, 30.0), (-6.0, 6.0, 5.0), 32),
    (C["inside"] + 0.2, (-16.0, -18.0, 24.0), (-4.0, 6.0, 8.0), 32),
    (C["out"], (-13.0, -15.0, 21.0), (-3.0, 6.0, 8.0), 32),
    (C["hoover3"] + 0.4, (-6.0, -64.0, 12.0), (-6.0, 0.0, 11.0), 35),
    (C["then2"], (-6.0, -60.0, 12.0), (-6.0, 0.0, 11.0), 35),
    (C["solid"] + 0.2, (-38.0, -52.0, 30.0), (-6.0, 6.0, 10.0), 32),
    (C["water"] + 0.3, (0.0, -60.0, 12.0), (0.0, 0.0, 11.0), 35),
    (C["huge"], (-6.0, -62.0, 10.0), (-6.0, 0.0, 9.5), 35),
    (C["finally"] + 0.3, (-40.0, -62.0, 46.0), (4.0, 6.0, 8.0), 30),
    (C["plugged"] + 0.3, (-4.0, -46.0, 34.0), (20.0, 10.0, 5.0), 32),
    (C["river2"], (-42.0, -62.0, 46.0), (2.0, 6.0, 8.0), 30),
    (C["would"], (-38.0, -54.0, 40.0), (0.0, 6.0, 9.0), 30),
    (C["end_t"], (-12.0, -62.0, 36.0), (2.0, 6.0, 9.0), 30),
]
for t, loc, tgt, lens in SHOTS:
    fr = F(t)
    setloc(cam, fr, loc); setloc(TGT, fr, tgt); rec(cam_d, "lens", -1, fr, lens)
write_tracks("BEZIER")

# ground the diorama stands on (keeps the horizon from reading as a void)
GROUND = box("DesertGround", -900, 900, -900, 900, Z_DEEP - 1.0, Z_DEEP - 0.05, soil("DesertSoil", (0.30, 0.22, 0.15), (0.42, 0.32, 0.22), 0.05), CG)

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
fill_d = bpy.data.lights.new("SectionFill", "AREA"); fill_d.size = 40; fill_d.energy = 1200; fill_d.color = (1.0, 0.95, 0.88)
fill = bpy.data.objects.new("SectionFill", fill_d); scene.collection.objects.link(fill); fill.location = (-10, -45, 14)
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
ANCH = {"tunnel": (None, Vector((-22.0, YC, T_Z + T_R))), "portal_in": (None, Vector((X_IN, W, T_Z + T_R))),
        "cofferdam": (None, Vector((X_CU, 0.0, Z_W + 1.8))), "cofferdam2": (None, Vector((X_CD, 0.0, Z_W + 1.8))),
        "riverbed": (None, Vector((-5.0, 0.0, Z_BED + 0.1))), "bedrock": (None, Vector((-12.0, 0.0, Z_ROCK - 1.0))),
        "curtain": (None, Vector((X_GC, 0.0, -12.0))), "dam_top": (None, Vector((1.6, 0.0, 26.0))), "dam_base": (None, Vector((-7.0, 0.0, Z_ROCK))),
        "pipes": (None, Vector((xl, 1.0, Z_PIPE))), "xray": (None, Vector((-6.0, 0.0, Z_E[5] + 1.5))),
        "plug": (None, Vector((X_IN, W, T_Z + T_R))), "outlet": (None, Vector((X_OUT, W, T_Z + T_R))), "reservoir": (None, Vector((34.0, 4.0, 22.0))),
        "dam_crest": (None, Vector((1.6, 6.0, 26.0)))}
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
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
