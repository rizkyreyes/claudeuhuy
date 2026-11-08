# Swimming-pool cover v2: a dedicated hero scene (not the video's model). An EMPTY tiled concrete pool that groundwater has pushed
# up out of the yard: tilted shell standing ~1 m proud of the lawn, cracked deck slabs around it, a torn soil edge.
#   A: low 3/4 from the lawn, the whole lifted pool towering.        Title "EMPTY POOL / POPPED UP?!"
#   B: the yard is cut in front: soil section with the groundwater (blue) under the shell pushing it up.  "IT FLOATED / OUT OF THE GROUND"
#   C: high 3/4 from above the fence, the whole yard, the pool tilted out of a hole.  "THIS POOL / CAN FLOAT?!"
# Poly Haven CC0 textures + HDRI from assets/polyhaven. Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B|C --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, bmesh, math, os, sys, random
from mathutils import Vector
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT = arg("--opt", "A"); HERE = os.path.dirname(os.path.abspath(__file__)); PH = os.path.join(HERE, "assets", "polyhaven")
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene; random.seed(4)

def tex_mat(name, folder, scale, tint=None, rough_add=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    def img(fn, color=True):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(os.path.join(PH, folder, fn)); t.projection = "BOX"; t.projection_blend = 0.3
        if not color: t.image.colorspace_settings.name = "Non-Color"
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"]); return t
    d = img(f"{folder}_diff_2k.jpg")
    if tint:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs["Factor"].default_value = 1.0
        mx.inputs[7].default_value = (*tint, 1); nt.links.new(d.outputs["Color"], mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    else: nt.links.new(d.outputs["Color"], b.inputs["Base Color"])
    r = img(f"{folder}_rough_2k.jpg", False); nt.links.new(r.outputs["Color"], b.inputs["Roughness"])
    n = img(f"{folder}_nor_gl_2k.jpg", False); nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m
def flat(name, col, rough=0.5, metal=0.0, alpha=1.0, trans=0.0, ior=1.33):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior; return m
def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel: mo = o.modifiers.new("b", "BEVEL"); mo.width = bevel; mo.segments = 2
    o.data.materials.append(mat); return o
def boolean(o, cutter, op="DIFFERENCE"):
    m = o.modifiers.new("cut", "BOOLEAN"); m.object = cutter; m.operation = op; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier=m.name); cutter.hide_render = True; cutter.hide_viewport = True

M_GRASS = tex_mat("Grass", "grass_ground", 0.35, (0.45, 0.85, 0.35)); M_SOIL = tex_mat("Soil", "excavated_soil_wall", 0.4)
M_CONC = tex_mat("Deck", "brushed_concrete", 0.6, (0.95, 0.92, 0.86)); M_TILE = tex_mat("Tile", "blue_floor_tiles_01", 1.2)
M_PLASTER = flat("Plaster", (0.86, 0.93, 0.97), 0.35); M_SHELLX = flat("ShellCore", (0.55, 0.53, 0.50), 0.85)
M_GW = flat("Groundwater", (0.10, 0.45, 0.70), 0.05, trans=0.6); M_FENCE = flat("Fence", (0.82, 0.76, 0.66), 0.7)
M_MUD = flat("Mud", (0.10, 0.08, 0.06), 0.3)

L, W, D, T = 8.0, 4.0, 1.8, 0.25                     # pool inner length, width, depth, wall thickness
CUT_FRONT = OPT == "B"
# ---- yard: grass top over soil block with a hole where the pool was
yard = box("Yard", (40, 30, 14), (0, 4, -7), M_SOIL)
hole = box("HoleCut", (L + 2 * T + 0.6, W + 2 * T + 0.6, D + 2), (0, 0, -D / 2 + 0.2), M_SOIL); boolean(yard, hole)
if CUT_FRONT:
    fc = box("FrontCut", (60, 20, 20), (0, -10 + 0.0, -3), M_SOIL); boolean(yard, fc)
grass = box("Lawn", (40, 30, 0.06), (0, 4, 0.03), M_GRASS)
hole2 = box("HoleCut2", (L + 2 * T + 1.2, W + 2 * T + 1.2, 1), (0, 0, 0), M_GRASS); boolean(grass, hole2)
if CUT_FRONT: fc2 = box("FrontCut2", (60, 20, 2), (0, -10, 0), M_GRASS); boolean(grass, fc2)
# groundwater filling the bottom of the hole (pushed up) — darker, shiny
gw = box("Groundwater", (L + 2 * T + 0.55, W + 2 * T + 0.55 if not CUT_FRONT else W + 2 * T + 0.3, 0.9), (0, 0.0, -D - 0.2), M_GW)
if CUT_FRONT:
    band = box("WaterTable", (40, 0.02, 0.9), (0, -0.01, -D - 0.2), M_GW)       # water line in the soil section
    mud = box("MudLine", (40, 0.03, 0.05), (0, -0.02, -D + 0.25), M_MUD)
# ---- the pool shell (empty), lifted and tilted
pool = bpy.data.objects.new("Pool", None); scene.collection.objects.link(pool)
outer = box("ShellOuter", (L + 2 * T, W + 2 * T, D + T), (0, 0, -(D + T) / 2 + 0.0), M_SHELLX, bevel=0.03)
inner = box("ShellInner", (L, W, D + 1), (0, 0, 0.5 - 0.0 + -D / 2 + 0.25), M_SHELLX); boolean(outer, inner)
outer.data.materials.clear(); outer.data.materials.append(tex_mat("Shotcrete", "brushed_concrete", 0.5, (0.62, 0.60, 0.56)))
liner = box("Liner", (L, W, D), (0, 0, -D / 2 + 0.001), M_PLASTER); lc = box("LinerCut", (L - 0.04, W - 0.04, D + 1), (0, 0, 0.5 - D / 2 + 0.03), M_PLASTER); boolean(liner, lc); liner.parent = pool
for o in (outer,): o.parent = pool
coping = []
for (sx, sy, x, y) in [(L + 2 * T + 0.5, 0.45, 0, W / 2 + T), (L + 2 * T + 0.5, 0.45, 0, -W / 2 - T), (0.45, W + 2 * T, L / 2 + T, 0), (0.45, W + 2 * T, -L / 2 - T, 0)]:
    c = box("Coping", (sx, sy, 0.12), (x, y, 0.06), M_CONC, bevel=0.02); c.parent = pool
tile = box("TileBand", (L - 0.02, W - 0.02, 0.25), (0, 0, -0.14), M_TILE); hole3 = box("TileCut", (L - 0.1, W - 0.1, 1), (0, 0, -0.14), M_TILE); boolean(tile, hole3); tile.parent = pool
drain = box("MainDrain", (0.35, 0.35, 0.02), (1.5, 0, -D + 0.01), flat("Grate", (0.08, 0.09, 0.1), 0.4)); drain.parent = pool
steps = [box(f"Step{i}", (0.6, W - 0.02, 0.35 * (i + 1)), (-L / 2 + 0.3 + 0.6 * (2 - i), 0, -D + 0.175 * (i + 1)), M_PLASTER) for i in range(3)]
for s in steps: s.parent = pool
pool.location = (0, 0, 1.4); pool.rotation_euler = (math.radians(-5.0), math.radians(7.0), math.radians(0))
# ---- cracked deck slabs around the hole, a few tipped up
# neat paver deck: a clean ring of square slabs in a grid around the hole (gap 2 cm), flush on the lawn
P = 1.0; X0, Y0 = L / 2 + T + 0.3, W / 2 + T + 0.3
for ix in range(-7, 7):
    for iy in range(-5, 5):
        cx, cy = (ix + 0.5) * P, (iy + 0.5) * P
        if abs(cx) < X0 and abs(cy) < Y0: continue
        if abs(cx) > X0 + 2 * P or abs(cy) > Y0 + 2 * P: continue
        if CUT_FRONT and cy < -0.5: continue
        box(f"Paver{ix}_{iy}", (P - 0.03, P - 0.03, 0.08), (cx, cy, 0.07), M_CONC, bevel=0.01)
# fence + shrubs in the back
for k in range(9): box(f"Fence{k}", (2.3, 0.08, 1.9), (-9.2 + k * 2.3, 9.5, 0.95), M_FENCE)
M_LEAF = flat("Leaf", (0.12, 0.30, 0.10), 0.7)

# ---- world, light, camera
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "kloofendal_48d_partly_cloudy_puresky", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"]); nt.nodes["Background"].inputs["Strength"].default_value = 0.9
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 4.5; sun.color = (1.0, 0.86, 0.68); sun.angle = math.radians(1.5)
so = bpy.data.objects.new("Sun", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(58), 0, math.radians(-35))
camd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", camd); scene.collection.objects.link(cam); scene.camera = cam
tgt = bpy.data.objects.new("T", None); scene.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
camd.sensor_fit = "VERTICAL"; camd.sensor_height = 36
if OPT == "A": cam.location = (6.0, -7.0, 3.4); tgt.location = (0.0, 0.3, -0.2); camd.lens = 17
elif OPT == "B": cam.location = (3.0, -9.0, -0.6); tgt.location = (0.0, 0.0, -0.6); camd.lens = 17
else: cam.location = (6.0, -6.5, 7.0); tgt.location = (0.0, 0.4, -0.2); camd.lens = 18
camd.dof.use_dof = True; camd.dof.focus_object = tgt; camd.dof.aperture_fstop = 5.6
r = scene.render; r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128")); scene.cycles.use_denoising = True
dev = arg("--cycles-device", "OPTIX")
if dev.upper() != "CPU":
    try:
        p = bpy.context.preferences.addons["cycles"].preferences; p.compute_device_type = dev; p.get_devices()
        for d in p.devices: d.use = True
        scene.cycles.device = "GPU"
    except Exception as e: print("GPU fail", e)
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
out = os.path.abspath(arg("--out", os.path.join(HERE, "cover", f"hero_{OPT}.png"))); os.makedirs(os.path.dirname(out), exist_ok=True)
r.filepath = out; bpy.ops.render.render(write_still=True); print("COVER", OPT, out)
