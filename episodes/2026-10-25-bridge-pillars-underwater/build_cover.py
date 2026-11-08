# Bridge-pillars cover v2: a dedicated hero scene (not the video's model). A wide river cut open like an aquarium section.
#   A: a steel-sheet cofferdam standing in the river, pumped bone dry inside (wet concrete floor, a pump, hoses), the river
#      level high outside its walls.                                   Title "BONE DRY / UNDER A RIVER?!"
#   B: the finished pier: a concrete column through the water into a footing on piles driven deep into the riverbed.  "WHAT HOLDS / THIS PILLAR UP?"
#   C: the whole bridge across the river at golden hour, its piers going down through the cut water to the piles.  "BUILT INSIDE / THE RIVER?!"
# Textures + HDRI: Poly Haven CC0 (re-used from the swimming-pool episode's assets). Run from the episode folder:
#   blender -b -y -P build_cover.py -- --opt A|B|C --pct 100 --samples 128 --out cover/hero_A.png --cycles-device OPTIX
import bpy, math, os, sys, random
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
OPT = arg("--opt", "A"); HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "..", "2026-10-29-swimming-pool", "assets", "polyhaven")
bpy.ops.wm.read_factory_settings(use_empty=True); scene = bpy.context.scene; random.seed(7)

def tex_mat(name, folder, scale, tint=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale,) * 3
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
def flat(name, col, rough=0.5, metal=0.0, trans=0.0, ior=1.33, emit=None, es=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    b.inputs["Transmission Weight"].default_value = trans; b.inputs["IOR"].default_value = ior
    if emit: b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = es
    return m
def box(name, size, loc, mat, rot=(0, 0, 0), bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel: mo = o.modifiers.new("b", "BEVEL"); mo.width = bevel; mo.segments = 2
    o.data.materials.append(mat); return o
def cyl(name, r, h, loc, mat, v=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=v); o = bpy.context.object; o.name = name; o.data.materials.append(mat)
    bpy.ops.object.shade_smooth(); return o

M_CONC = tex_mat("Concrete", "brushed_concrete", 0.4, (0.92, 0.90, 0.86)); M_WET = tex_mat("WetConcrete", "brushed_concrete", 0.4, (0.55, 0.53, 0.50))
M_SOIL = tex_mat("Riverbed", "excavated_soil_wall", 0.25, (0.75, 0.62, 0.50)); M_BANK = tex_mat("Bank", "grass_ground", 0.3, (0.45, 0.85, 0.35))
M_WATER = flat("River", (0.03, 0.22, 0.30), 0.04, trans=0.55); M_SURF = flat("Surface", (0.10, 0.40, 0.50), 0.02, trans=0.85)
M_SHEET = flat("SheetPile", (0.30, 0.32, 0.34), 0.45, 0.85); M_GOLD = flat("Wale", (0.95, 0.65, 0.15), 0.35, 0.7)
M_PUMP = flat("Pump", (0.15, 0.35, 0.65), 0.4, 0.2); M_HOSE = flat("Hose", (0.05, 0.05, 0.05), 0.6)
M_DECK = flat("Asphalt", (0.07, 0.07, 0.08), 0.8); M_RAIL = flat("Rail", (0.8, 0.8, 0.8), 0.3, 0.8)

RIVER_TOP, BED = 0.0, -9.0
# riverbed block (cut at y = 0 → section face shows), soil below; water block above it up to the surface
Y0 = 5.1 if OPT == "A" else 3.5          # section plane: through the middle of the subject, which stands whole in front of it
bed = box("Riverbed", (140, 30, 80), (0, Y0 + 15, BED - 40), M_SOIL)
water = box("Water", (90, 30, -BED), (0, Y0 + 15, BED / 2), M_WATER)
for side in (-1, 1): box(f"Bank{side}", (20, 30, 12), (side * 52, 15, -4), M_BANK)
sx = 0.0
if OPT == "A":
    # cofferdam: square ring of steel sheets standing above the water, interior dry down to a wet concrete seal
    S, H = 9.0, 13.0
    inside = box("DryCut", (S - 0.3, S - 0.3, 40), (sx, S / 2 + 0.6, BED + 20 + 0.6), M_WATER)
    for o in (water,):
        m = o.modifiers.new("dry", "BOOLEAN"); m.object = inside; m.operation = "DIFFERENCE"; m.solver = "EXACT"
        bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier="dry")
    inside.hide_render = True
    n = 34
    for k in range(n):                                      # corrugated sheet walls (back + sides; the front is the cut)
        u = k / (n - 1)
        for (x, y, rz) in [(sx - S / 2 + u * S, S + 0.6, 0), (sx - S / 2, 0.6 + u * S, math.pi / 2), (sx + S / 2, 0.6 + u * S, math.pi / 2)]:
            box("Sheet", (S / n + 0.05, 0.12, H), (x, y, BED + H / 2 - 2.5 + 0.0), M_SHEET, rot=(0, 0, rz + (0.12 if k % 2 else -0.12)))
    for z in (RIVER_TOP + 1.5, BED + 6):                    # gold wales (bracing frames)
        box("WaleB", (S, 0.35, 0.45), (sx, S + 0.3, z), M_GOLD); box("WaleL", (0.35, S, 0.45), (sx - S / 2 + 0.3, 0.6 + S / 2, z), M_GOLD)
        box("WaleR", (0.35, S, 0.45), (sx + S / 2 - 0.3, 0.6 + S / 2, z), M_GOLD); box("Strut", (S, 0.3, 0.3), (sx, 0.6 + S / 2, z), M_GOLD)
    box("Seal", (S - 0.3, S - 0.3, 1.2), (sx, 0.6 + S / 2, BED + 0.6), M_WET)
    for i in range(3):
        for j in range(2): cyl("PileStub", 0.35, 0.6, (sx - 2.5 + i * 2.5, 3.0 + j * 4.0, BED + 1.5), M_CONC)
    pump = box("Pump", (1.4, 1.0, 1.0), (sx + 2.6, 2.4, BED + 1.7), M_PUMP, bevel=0.08)
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0)); hc = bpy.context.object; hc.data.bevel_depth = 0.12; hc.data.materials.append(M_HOSE)
    p = hc.data.splines[0].bezier_points; p[0].co = (sx + 2.6, 2.6, BED + 2.2); p[0].handle_right = (sx + 3.2, 4, BED + 6); p[0].handle_left = (sx + 2, 1, BED)
    p[1].co = (sx + 3.6, 9.0, RIVER_TOP + 3.6); p[1].handle_left = (sx + 3.6, 9.0, RIVER_TOP); p[1].handle_right = (sx + 3.6, 9.0, RIVER_TOP + 5)
    cam_loc, tgt_loc, lens = (10.0, -12.0, 2.0), (sx, 5.0, BED + 5.0), 18
else:
    def pier(x):
        box("Footing", (7, 6, 2.2), (x, 3.5, BED - 1.1), M_CONC, bevel=0.05)
        for i in range(3):
            for j in range(2): cyl("Pile", 0.45, 14, (x - 2.4 + i * 2.4, 2.0 + j * 3.0, BED - 2.2 - 7), M_CONC)
        cyl("Column", 1.6, 22.5 if OPT == "B" else 21.5, (x, 3.5, BED + 11.0), M_CONC, 32)
        box("Cap", (9, 3.6, 1.6), (x, 3.5, 13.0 if OPT == "B" else 12.0), M_CONC, bevel=0.05)
    xs = [0.0] if OPT == "B" else [-20.0, 0.0, 20.0]
    for x in xs: pier(x)
    deck_z = (13.0 if OPT == "B" else 12.0) + 1.6
    box("Girder", (100, 3.0, 1.6), (0, 3.5, deck_z), M_CONC); box("Deck", (100, 9.0, 0.5), (0, 3.5, deck_z + 1.05), M_DECK)
    for y in (-1.0, 8.0): box("Rail", (100, 0.15, 0.9), (0, y, deck_z + 1.75), M_RAIL)
    if OPT == "B": cam_loc, tgt_loc, lens = (11.0, -16.0, -3.0), (0.0, 3.5, -5.0), 18
    else: cam_loc, tgt_loc, lens = (22.0, -34.0, -2.0), (0.0, 3.5, -3.0), 20
box("SurfaceLine", (90, 0.06, 0.08), (0, Y0 - 0.03, RIVER_TOP - 0.04), flat("Line", (0.7, 0.95, 1.0), 0.2, emit=(0.4, 0.9, 1.0), es=3.0))
w = bpy.data.worlds.new("W"); scene.world = w; w.use_nodes = True; nt = w.node_tree
env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "kloofendal_48d_partly_cloudy_puresky", "kloofendal_48d_partly_cloudy_puresky_2k.hdr"))
nt.links.new(env.outputs["Color"], nt.nodes["Background"].inputs["Color"]); nt.nodes["Background"].inputs["Strength"].default_value = 0.8
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 4.0; sun.color = (1.0, 0.82, 0.62); sun.angle = math.radians(1.5)
so = bpy.data.objects.new("Sun", sun); scene.collection.objects.link(so); so.rotation_euler = (math.radians(62), 0, math.radians(-30))
fill = bpy.data.lights.new("Fill", "AREA"); fill.energy = 4000; fill.size = 20; fo = bpy.data.objects.new("Fill", fill); scene.collection.objects.link(fo)
fo.location = (cam_loc[0], cam_loc[1] + 4, BED + 2); fo.rotation_euler = (math.radians(90), 0, 0)
camd = bpy.data.cameras.new("Cam"); cam = bpy.data.objects.new("Cam", camd); scene.collection.objects.link(cam); scene.camera = cam
tgt = bpy.data.objects.new("T", None); scene.collection.objects.link(tgt)
tc = cam.constraints.new("TRACK_TO"); tc.target = tgt; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
camd.sensor_fit = "VERTICAL"; camd.sensor_height = 36; cam.location = cam_loc; tgt.location = tgt_loc; camd.lens = lens
r = scene.render; r.engine = "CYCLES"; r.resolution_x, r.resolution_y = 1080, 1920; r.resolution_percentage = int(arg("--pct", "100"))
scene.cycles.samples = int(arg("--samples", "128")); scene.cycles.use_denoising = True; scene.cycles.transmission_bounces = 8
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
