# Door-Lock-3D: pin-tumbler lock cutaway, Blender Cycles. Every cue is a word in the voice-over.
# Pins are driven by the key's real bitting profile, frame by frame.
# Usage: blender -b -y -P build_lock.py -- --save lock.blend [--stills f1,f2 --pct 50 --samples 32 --out dir] [--anim --out dir]
import bpy, bmesh, json, math, os, random, sys
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
arg = lambda n, d=None: ARGS[ARGS.index(n) + 1] if n in ARGS else d
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
WORDS = json.load(open(os.path.join(ROOT, "assets", "vo", "audio_meta.json"), encoding="utf-8"))["scenes"][0]["words"]
PH_DIR = os.path.abspath(os.path.join(ROOT, "..", "Road-Layers-3D", "work", "assets", "polyhaven"))
FPS, VO = 30, 0.30
DUR = round(WORDS[-1]["end"] + VO + 0.75, 2)
FRAMES = int(round(DUR * FPS))
F = lambda t: max(1, int(round(t * FPS)) + 1)
random.seed(3)

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
for name, word in [("how", "how"), ("door", "door"), ("lets", "let's"), ("half", "half"), ("this", "this"),
                   ("shell", "shell"), ("plug", "plug"), ("turns", "turns"), ("drilled", "drilled"), ("five", "five"),
                   ("chambers", "chambers"), ("each", "each"), ("spring", "spring"), ("top", "top"), ("bottom", "bottom"),
                   ("springs", "springs"), ("crosses", "crosses"), ("gap", "gap"), ("shear", "shear"), ("while", "while"),
                   ("jammed", "jammed"), ("nothing", "nothing"), ("slide", "slide"), ("cut", "cut"), ("height", "height"),
                   ("watch", "watch"), ("right", "right"), ("lands", "lands"), ("all", "all"), ("same", "same"),
                   ("plug2", "plug"), ("cam", "cam"), ("bolt", "bolt"), ("opens", "opens"), ("turn", "turn"),
                   ("snap", "snap"), ("locked", "locked"), ("try", "try"), ("wrong", "wrong"), ("one", "one"),
                   ("high", "high"), ("crosses2", "crosses"), ("shut", "shut"), ("idea", "idea"), ("four", "four"),
                   ("ancient", "ancient"), ("wood", "wood"), ("eighteen", "eighteen"), ("yale", "yale"),
                   ("shrank", "shrank"), ("pocket", "pocket"), ("so", "so"), ("five2", "five"), ("line", "line"),
                   ("key3", "key"), ("match", "match"), ("follow", "follow")]:
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
def coll(name):
    c = bpy.data.collections.new(name); scene.collection.children.link(c); return c
CL = coll("Lock")

# ---------- materials ----------
def new_mat(name):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    return m, m.node_tree, b
WOOD_FACTORS = []
def metal(name, rgb, rough=0.28, metallic=1.0, wood=True):
    """Metal with a keyable emission and an optional crossfade to procedural wood (history beat)."""
    m, nt, b = new_mat(name); L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 40; L.new(tc.outputs["Object"], n.inputs["Vector"])
    rr = nt.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = rough * 0.75; rr.inputs[4].default_value = rough * 1.35
    L.new(n.outputs["Fac"], rr.inputs[0])
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = metallic
    L.new(rr.outputs[0], b.inputs["Roughness"])
    b.inputs["Emission Color"].default_value = (1.0, 0.55, 0.15, 1); b.inputs["Emission Strength"].default_value = 0.0
    if wood:
        out = next(x for x in nt.nodes if x.type == "OUTPUT_MATERIAL")
        wb = nt.nodes.new("ShaderNodeBsdfPrincipled")
        wave = nt.nodes.new("ShaderNodeTexWave"); wave.wave_type = "RINGS"; wave.inputs["Scale"].default_value = 1.6
        wave.inputs["Distortion"].default_value = 6.0; wave.inputs["Detail"].default_value = 4.0
        L.new(tc.outputs["Object"], wave.inputs["Vector"])
        wr = nt.nodes.new("ShaderNodeValToRGB"); e = wr.color_ramp.elements
        e[0].color = (0.16, 0.08, 0.035, 1); e[1].color = (0.42, 0.24, 0.11, 1)
        L.new(wave.outputs["Fac"], wr.inputs[0]); L.new(wr.outputs[0], wb.inputs["Base Color"]); wb.inputs["Roughness"].default_value = 0.6
        mix = nt.nodes.new("ShaderNodeMixShader"); mix.inputs[0].default_value = 0.0
        L.new(b.outputs[0], mix.inputs[1]); L.new(wb.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], out.inputs["Surface"])
        WOOD_FACTORS.append(mix.inputs[0])
    return m, b
BRASS = (0.80, 0.56, 0.24); STEEL = (0.62, 0.63, 0.66); NICKEL = (0.72, 0.71, 0.66)
M_SHELL, B_SHELL = metal("Shell", BRASS, 0.3)
M_PLUG, B_PLUG = metal("Plug", (0.86, 0.62, 0.28), 0.24)
M_SPRING, _ = metal("Spring", STEEL, 0.25)
M_KEY, B_KEY = metal("Key", NICKEL, 0.2, wood=False)
M_WKEY, B_WKEY = metal("WrongKey", (0.55, 0.36, 0.30), 0.22, wood=False)
M_BOLT, _ = metal("Bolt", STEEL, 0.3)
M_DRIVER = [metal(f"Driver{i}", STEEL, 0.22) for i in range(5)]
M_KPIN = [metal(f"KeyPin{i}", BRASS, 0.22) for i in range(5)]
def flat(name, rgb, rough=0.5, emit=0.0, emit_rgb=None):
    m, nt, b = new_mat(name)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    if emit: b.inputs["Emission Color"].default_value = (*(emit_rgb or rgb), 1); b.inputs["Emission Strength"].default_value = emit
    return m, b
M_DOOR, _ = flat("DoorPaint", (0.03, 0.11, 0.08), 0.42)
M_SHEAR, B_SHEAR = flat("ShearGlow", (0.2, 0.9, 1.0), 0.4, 6.0, (0.25, 0.95, 1.0))
M_FRAME, _ = flat("DoorFrame", (0.20, 0.13, 0.08), 0.6)

# ---------- geometry helpers ----------
def mesh_obj(name, bm, mat, parent=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    if mat: me.materials.append(mat)
    o = bpy.data.objects.new(name, me); CL.objects.link(o)
    if parent: o.parent = parent
    return o
def cyl(name, r, x0, x1, axis="X", seg=64, mat=None, center=(0, 0, 0)):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=abs(x1 - x0))
    rot = {"X": Matrix.Rotation(math.radians(90), 3, "Y"), "Y": Matrix.Rotation(math.radians(90), 3, "X"), "Z": Matrix.Identity(3)}[axis]
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=rot)
    off = {"X": Vector(((x0 + x1) / 2, 0, 0)), "Y": Vector((0, (x0 + x1) / 2, 0)), "Z": Vector((0, 0, (x0 + x1) / 2))}[axis]
    bmesh.ops.translate(bm, verts=bm.verts, vec=off + Vector(center))
    return mesh_obj(name, bm, mat)
def boxm(name, x0, x1, y0, y1, z0, z1, mat=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, verts=bm.verts, vec=(x1 - x0, y1 - y0, z1 - z0))
    bmesh.ops.translate(bm, verts=bm.verts, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return mesh_obj(name, bm, mat)
def boolean(target, cutter, op="DIFFERENCE"):
    md = target.modifiers.new("b", "BOOLEAN"); md.operation = op; md.object = cutter; md.solver = "EXACT"
    dg = bpy.context.evaluated_depsgraph_get(); ev = target.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev); target.modifiers.clear()
    old = target.data; target.data = me; bpy.data.meshes.remove(old)
def delete(o): bpy.data.objects.remove(o, do_unlink=True)
def smooth(o, angle=35):
    o.data.shade_smooth()
    try: o.data.set_sharp_from_angle(angle=math.radians(angle))
    except Exception: pass
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.012; bv.segments = 2; bv.limit_method = "ANGLE"

# ---------- lock dimensions ----------
RP, RS, LEN = 1.0, 1.55, 6.0
PX = [1.0, 2.0, 3.0, 4.0, 5.0]
RC, RPIN = 0.27, 0.235
CH_TOP = 3.25
LK = [0.95, 0.70, 1.15, 0.80, 1.05]          # key-pin lengths (the bitting)
LD = 0.85                                      # driver pins: all the same length
Z_REST = -0.25                                 # key-pin tip height with no key
SHEAR = RP
TIP_IN = 5.85                                  # key tip x when fully inserted

LOCK = bpy.data.objects.new("LockRoot", None); CL.objects.link(LOCK)          # at the origin: no parent offsets
PIV = bpy.data.objects.new("PlugPivot", None); CL.objects.link(PIV)

def cutter_half(sign):     # y>=0 (back half, kept) or y<0 (front half, slides away)
    return boxm("cut", -3, 10, 0 if sign > 0 else -6, 6 if sign > 0 else 0, -6, 6)

def build_shell():
    sh = cyl("Shell", RS, 0.0, LEN, "X", 96, M_SHELL)
    tw = boxm("tower", 0.25, LEN - 0.25, -0.62, 0.62, 0.0, 3.5)
    boolean(sh, tw, "UNION"); delete(tw)
    bore = cyl("bore", RP + 0.006, -0.5, LEN + 0.5, "X", 96); boolean(sh, bore); delete(bore)
    for x in PX:
        ch = cyl("ch", RC, 0.9, CH_TOP, "Z", 40, center=(x, 0, 0)); boolean(sh, ch); delete(ch)
    return sh
def build_plug():
    pl = cyl("Plug", RP, 0.0, LEN, "X", 96, M_PLUG)
    kw = boxm("kw", -0.5, LEN - 0.12, -0.14, 0.14, -0.82, 0.56); boolean(pl, kw); delete(kw)
    for x in PX:
        ch = cyl("ch", RC, 0.0, 1.2, "Z", 40, center=(x, 0, 0)); boolean(pl, ch); delete(ch)
    return pl
shell_full, plug_full = build_shell(), build_plug()
halves = {}
for base in (shell_full, plug_full):
    for sign, tag in ((1, "Back"), (-1, "Front")):
        h = base.copy(); h.data = base.data.copy(); h.name = f"{base.name}_{tag}"; CL.objects.link(h)
        c = cutter_half(sign); boolean(h, c, "INTERSECT"); delete(c); smooth(h)
        halves[(base.name, tag)] = h
delete(shell_full); delete(plug_full)
SHELL_B, SHELL_F = halves[("Shell", "Back")], halves[("Shell", "Front")]
PLUG_B, PLUG_F = halves[("Plug", "Back")], halves[("Plug", "Front")]
for o in (SHELL_B, SHELL_F): o.parent = LOCK; o.matrix_parent_inverse = Matrix.Identity(4)
PIV.parent = LOCK                                          # pivot sits on the plug axis (world origin)
for o in (PLUG_B, PLUG_F): o.parent = PIV

# pins (full cylinders; key pins pointed) + springs
def pin_mesh(name, length, pointed, mat):
    bm = bmesh.new()
    if pointed:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=RPIN, radius2=RPIN, depth=length - 0.12)
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, (length - 0.12) / 2 + 0.12))
        tip = bmesh.new(); bmesh.ops.create_cone(tip, cap_ends=True, segments=40, radius1=0.05, radius2=RPIN, depth=0.12)
        bmesh.ops.translate(tip, verts=tip.verts, vec=(0, 0, 0.06))
        me_t = bpy.data.meshes.new("t"); tip.to_mesh(me_t); tip.free(); bm.from_mesh(me_t); bpy.data.meshes.remove(me_t)
    else:
        bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=RPIN, radius2=RPIN, depth=length)
        bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, length / 2))
    o = mesh_obj(name, bm, mat); smooth(o, 50); return o          # origin at the pin's bottom
def spring_mesh(name):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.035; cu.bevel_resolution = 3
    sp = cu.splines.new("POLY"); turns, n = 9, 9 * 24; sp.points.add(n)
    for k in range(n + 1):
        a = 2 * math.pi * turns * k / n
        sp.points[k].co = (0.19 * math.cos(a), 0.19 * math.sin(a), -k / n, 1)     # hangs down from origin, length 1
    cu.materials.append(M_SPRING)
    o = bpy.data.objects.new(name, cu); CL.objects.link(o); return o
DRIVERS, KPINS, SPRINGS = [], [], []
for i, x in enumerate(PX):
    kp = pin_mesh(f"KeyPin_{i+1}", LK[i], True, M_KPIN[i][0]); kp.parent = PIV; kp.location = (x, 0, Z_REST)
    dp = pin_mesh(f"DriverPin_{i+1}", LD, False, M_DRIVER[i][0]); dp.parent = LOCK; dp.matrix_parent_inverse = Matrix.Identity(4)
    dp.location = (x, 0, Z_REST + LK[i])
    sp = spring_mesh(f"Spring_{i+1}"); sp.parent = LOCK; sp.matrix_parent_inverse = Matrix.Identity(4)
    sp.location = (x, 0, CH_TOP)
    KPINS.append(kp); DRIVERS.append(dp); SPRINGS.append(sp)

# ---------- keys: blade profile = the bitting ----------
CUT_H = [SHEAR - l for l in LK]
def profile(u, cuts):
    """Blade top height at key-local u (tip at 0, bow toward -u)."""
    if u > 0 or u < -6.6: return None
    top = 0.45
    for i, x in enumerate(PX):
        ui = x - TIP_IN
        top = min(top, cuts[i] + max(0.0, abs(u - ui) - 0.09))
    top = min(top, -0.4 + (-u) * 1.45)                     # tip ramp lifts pins as the key enters
    return top
def key_obj(name, cuts, mat):
    us = [min(0.0, round(-6.6 + k * 0.02, 4)) for k in range(int(round(6.6 / 0.02)) + 1)]
    outline = [(-6.6, -0.75), (-0.22, -0.75), (0.0, -0.55)] + [(u, profile(u, cuts)) for u in reversed(us)] + [(-6.6, 0.45)]
    bm = bmesh.new(); vs = [bm.verts.new((u, 0.0, z)) for u, z in outline]; bm.faces.new(vs)
    o = mesh_obj(name, bm, mat); sd = o.modifiers.new("Solid", "SOLIDIFY"); sd.thickness = 0.22; sd.offset = 0.0
    bv = o.modifiers.new("Bevel", "BEVEL"); bv.width = 0.015; bv.segments = 2
    bow = cyl(name + "_Bow", 1.15, -0.14, 0.14, "Y", 64, mat, center=(-7.65, 0, -0.1)); smooth(bow); bow.parent = o
    hole = cyl("h", 0.28, -0.4, 0.4, "Y", 32, center=(-8.25, 0, -0.1)); boolean(bow, hole); delete(hole)
    return o
WRONG = list(CUT_H); WRONG[2] += 0.24                      # cut 3 too shallow -> pin 3 sits too high
KEY = key_obj("Key_Right", CUT_H, M_KEY); KEY.parent = PIV
WKEY = key_obj("Key_Wrong", WRONG, M_WKEY); WKEY.parent = PIV

# cam (tailpiece) + bolt + door frame (keeper)
CAM = boxm("Cam", LEN + 0.02, LEN + 0.42, -0.25, 0.25, -1.75, 0.15, M_BOLT); CAM.parent = PIV; smooth(CAM)
BOLT = boxm("Bolt", 0, 2.8, -0.42, 0.42, -0.45, 0.45, M_BOLT); BOLT.parent = LOCK; smooth(BOLT)
BOLT.matrix_parent_inverse = Matrix.Identity(4)
FRAMEP = boxm("Keeper", 8.4, 9.2, -1.4, 1.4, -3.6, -0.4, M_FRAME); FRAMEP.parent = LOCK; smooth(FRAMEP)
FRAMEP.matrix_parent_inverse = Matrix.Identity(4)
BOLT_OUT, BOLT_IN = Vector((6.0, 0, -2.0)), Vector((4.6, 0, -2.0))
SHEAR_BAR = boxm("ShearLine", 0.12, LEN - 0.12, -0.31, -0.29, SHEAR - 0.018, SHEAR + 0.018, M_SHEAR)
SHEAR_BAR.parent = LOCK; SHEAR_BAR.matrix_parent_inverse = Matrix.Identity(4)

# door (hook only) + escutcheon
DOOR = boxm("Door", 0.0, 0.5, -7, 7, -9, 9, M_DOOR)
hole = cyl("dh", RS + 0.02, -1, 1, "X", 96); boolean(DOOR, hole); delete(hole)
ESC = bpy.data.objects.new("Escutcheon", bpy.data.meshes.new("esc")); CL.objects.link(ESC)
bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=RS + 0.45, radius2=RS + 0.3, depth=0.12)
bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(-90), 3, "Y"))
bmesh.ops.translate(bm, verts=bm.verts, vec=(-0.06, 0, 0)); bm.to_mesh(ESC.data); bm.free(); ESC.data.materials.append(M_SHELL)
eh = cyl("eh", RS - 0.02, -1, 1, "X", 96); boolean(ESC, eh); delete(eh); smooth(ESC)
for o in (DOOR, ESC): vis(o, 1, False); vis(o, F(C["lets"]) , True)

# ---------- state timeline (seconds) ----------
def ease(p): p = max(0.0, min(1.0, p)); return p * p * (3 - 2 * p)
def seg(t, a, b, v0, v1, fn=ease): return v0 + (v1 - v0) * fn(max(0.0, min(1.0, (t - a) / (b - a)))) if b > a else v1
def right_tip(t):
    """Right-key tip x over time (None = key not shown)."""
    if t < C["door"] - 1.1: return None
    if t < C["lets"]: return seg(t, C["door"] - 1.1, C["door"], -3.4, -0.6)          # hook: flies to the keyway
    if t < C["slide"] - 0.4: return None
    if t < C["slide"]: return -1.2
    if t < C["snap"] - 0.15: return seg(t, C["slide"] + 0.15, C["height"] - 0.2, -1.2, TIP_IN, lambda p: p)
    if t < C["try"] - 0.3: return seg(t, C["snap"] - 0.15, C["snap"] + 0.35, TIP_IN, -1.6)
    if t < C["so"]: return None
    return seg(t, C["so"], C["so"] + 0.55, -1.2, TIP_IN)
def wrong_tip(t):
    if t < C["try"] - 0.3 or t > C["idea"] + 0.6: return None
    if t < C["try"]: return -1.6
    if t < C["idea"]: return seg(t, C["wrong"], C["one"] + 0.3, -1.6, TIP_IN, lambda p: p)
    return seg(t, C["idea"], C["idea"] + 0.6, TIP_IN, -2.2)
def plug_angle(t):
    a = 0.0
    if C["plug2"] <= t < C["snap"]:
        a = seg(t, C["plug2"] + 0.1, C["plug2"] + 0.9, 0, -88) if t < C["turn"] else seg(t, C["turn"] + 0.1, C["turn"] + 0.7, -88, 0)
    for t0 in (C["jammed"], C["shut"] - 0.25):                           # blocked twitches
        if t0 <= t < t0 + 0.36: a = -4.0 * math.sin((t - t0) / 0.36 * math.pi * 2)
    if C["plug"] <= t < C["plug"] + 0.5: a = -6.0 * math.sin((t - C["plug"]) / 0.5 * math.pi)   # "the part that turns"
    return a
def pins_raise_from_rest(t):
    """Before 'springs push down' the stacks are shown lifted (no spring tension yet), then they drop."""
    return seg(t, C["springs"], C["springs"] + 0.45, 0.55, 0.0, lambda p: p * p) if t < C["springs"] + 0.45 else 0.0
def lock_scale(t):
    if t < C["shrank"]: return 1.0
    if t < C["so"] - 0.2: return seg(t, C["shrank"], C["pocket"] + 0.3, 1.0, 0.32)
    return seg(t, C["so"] - 0.2, C["so"] + 0.4, 0.32, 1.0)
def wood_mix(t):
    if t < C["four"] - 0.2: return 0.0
    if t < C["eighteen"]: return seg(t, C["four"] - 0.2, C["four"] + 0.7, 0, 1)
    return seg(t, C["eighteen"], C["eighteen"] + 0.6, 1, 0)

def key_pin_tip(i, t):
    z = Z_REST + pins_raise_from_rest(t)
    for tipf, cuts in ((right_tip, CUT_H), (wrong_tip, WRONG)):
        tip = tipf(t)
        if tip is None or tip < PX[i] - 0.05: continue           # the blade has not reached this pin yet
        if t < C["slide"] - 0.5: continue                        # hook key is outside the lock
        h = profile(PX[i] - tip, cuts)
        if h is not None: z = max(z, h)
    return z

# ---------- bake per-frame animation ----------
click_events = {"right": [], "wrong": [], "snap": []}
prev = [None] * 5; prev_v = [0.0] * 5
for fr in range(1, FRAMES + 1):
    t = (fr - 1) / FPS
    for i in range(5):
        z = key_pin_tip(i, t)
        KPINS[i].location.z = z; KPINS[i].keyframe_insert("location", index=2, frame=fr)
        dz_bottom = z + LK[i]
        DRIVERS[i].location.z = dz_bottom; DRIVERS[i].keyframe_insert("location", index=2, frame=fr)
        top = dz_bottom + LD
        SPRINGS[i].scale.z = max(0.12, CH_TOP - top); SPRINGS[i].keyframe_insert("scale", index=2, frame=fr)
        if prev[i] is not None:
            v = z - prev[i]
            if prev_v[i] < -0.004 and v >= -0.0005:            # pin just settled into a cut / onto rest
                who = "wrong" if wrong_tip(t) is not None and t > C["try"] else ("snap" if C["snap"] - 0.3 < t < C["try"] else "right")
                click_events[who].append(round(t, 3))
            prev_v[i] = v
        prev[i] = z
    rt, wt = right_tip(t), wrong_tip(t)
    for k, tip in ((KEY, rt), (WKEY, wt)):
        hidden = tip is None
        k.hide_render = hidden; k.keyframe_insert("hide_render", frame=fr)
        if not hidden:
            k.location = (tip, 0, 0) if t >= C["lets"] else (tip, -0.0, 0.0)
            k.keyframe_insert("location", frame=fr)
    PIV.rotation_euler.x = math.radians(plug_angle(t)); PIV.keyframe_insert("rotation_euler", index=0, frame=fr)
    s = lock_scale(t); LOCK.scale = (s, s, s); LOCK.keyframe_insert("scale", frame=fr)
    for f_in in WOOD_FACTORS:
        f_in.default_value = wood_mix(t); f_in.keyframe_insert("default_value", frame=fr)
    # bolt follows the cam
    a = abs(plug_angle(t)) / 88.0 if C["plug2"] <= t < C["snap"] else 0.0
    BOLT.location = BOLT_OUT.lerp(BOLT_IN, ease(min(1.0, a * 1.1))); BOLT.keyframe_insert("location", frame=fr)

# split: front halves slide toward the camera and away on "half"
for o in (SHELL_F, PLUG_F):
    vis(o, 1, False)
    base = o.location.copy()
    key(o, "location", F(C["half"] - 0.05), tuple(base), "BEZIER")
    key(o, "location", F(C["half"] + 0.75), tuple(base + Vector((0, -9.0, 0.6))), "BEZIER")
    vis(o, F(C["half"] + 0.8), True)

# highlights (emission keys)
def pulse(bsdf, t0, peak=2.5, hold=0.9, rgb=None):
    s = bsdf.inputs["Emission Strength"]
    if rgb: bsdf.inputs["Emission Color"].default_value = (*rgb, 1)
    key(s, "default_value", F(t0 - 0.15), 0.0); key(s, "default_value", F(t0 + 0.12), peak)
    key(s, "default_value", F(t0 + hold), peak * 0.6); key(s, "default_value", F(t0 + hold + 0.5), 0.0)
pulse(B_SHELL, C["shell"], 1.2); pulse(B_PLUG, C["plug"], 1.2)
step = (C["chambers"] - C["drilled"]) / 5
for i in range(5):                                           # chambers light up left to right
    pulse(M_DRIVER[i][1], C["drilled"] + 0.2 + i * step, 2.0, 0.5); pulse(M_KPIN[i][1], C["drilled"] + 0.2 + i * step, 2.0, 0.5)
pulse(M_DRIVER[2][1], C["top"], 3.0, 0.8, (0.5, 0.8, 1.0)); pulse(M_KPIN[2][1], C["bottom"], 3.0, 0.8)
for i in range(5): pulse(M_DRIVER[i][1], C["jammed"], 4.0, 1.0, (1.0, 0.12, 0.08))
pulse(M_KPIN[2][1], C["high"], 5.0, 1.6, (1.0, 0.12, 0.08))
pulse(B_KEY, C["key3"], 2.0, 0.6, (1.0, 0.9, 0.6))
# shear line: wipes in on "shear", visible through the alignment, back for the recap
SH = SHEAR_BAR
vis(SH, 1, True); vis(SH, F(C["shear"] - 0.1), False); vis(SH, F(C["plug2"] + 0.2), True); vis(SH, F(C["so"] + 0.5), False)
key(SH, "scale", F(C["shear"] - 0.1), (0.0, 1, 1)); key(SH, "scale", F(C["shear"] + 0.5), (1, 1, 1))
key(SH, "scale", F(C["so"] + 0.5), (0.0, 1, 1)); key(SH, "scale", F(C["line"]), (1, 1, 1))
ss = B_SHEAR.inputs["Emission Strength"]
key(ss, "default_value", F(C["lands"] - 0.2), 6.0); key(ss, "default_value", F(C["lands"] + 0.2), 22.0); key(ss, "default_value", F(C["same"] + 0.4), 8.0)
key(ss, "default_value", F(C["line"] - 0.1), 8.0); key(ss, "default_value", F(C["line"] + 0.2), 22.0); key(ss, "default_value", F(C["line"] + 0.8), 9.0)

# ---------- camera (location + tracked target) ----------
TGT = bpy.data.objects.new("CamTarget", None); scene.collection.objects.link(TGT)
cam_d = bpy.data.cameras.new("Camera"); cam_d.sensor_fit = "VERTICAL"; cam_d.sensor_height = 36; cam_d.lens = 50
cam = bpy.data.objects.new("Camera", cam_d); scene.collection.objects.link(cam); scene.camera = cam
tc = cam.constraints.new("TRACK_TO"); tc.target = TGT; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 11; cam_d.dof.focus_object = TGT
SHOTS = [  # (time, camera loc, target, lens)
    (0.0, (-6.2, -6.6, 1.7), (-0.6, 0.0, 0.25), 38),
    (C["door"], (-5.0, -5.4, 1.3), (-0.4, 0.0, 0.2), 38),
    (C["lets"], (-4.8, -5.2, 1.3), (0.2, 0.0, 0.3), 38),
    (C["half"], (-3.0, -14.0, 2.2), (2.2, 0.0, 0.9), 45),
    (C["this"], (3.0, -17.5, 1.1), (3.0, 0.0, 0.95), 50),
    (C["each"], (3.0, -16.8, 1.1), (3.0, 0.0, 0.95), 50),
    (C["spring"] - 0.1, (3.0, -11.5, 2.0), (3.0, 0.0, 1.7), 50),
    (C["springs"] - 0.2, (3.0, -11.0, 1.9), (3.0, 0.0, 1.6), 50),
    (C["shear"], (3.0, -16.0, 1.2), (3.0, 0.0, 1.05), 50),
    (C["slide"] - 0.3, (3.0, -16.5, 1.1), (3.0, 0.0, 1.0), 50),
    (C["slide"] + 0.2, (1.6, -20.0, 0.8), (1.6, 0.0, 0.85), 50),
    (C["watch"], (2.4, -18.5, 0.9), (2.4, 0.0, 0.95), 50),
    (C["right"], (3.0, -10.5, 1.2), (3.0, 0.0, 1.05), 50),
    (C["same"] + 0.3, (3.0, -11.0, 1.15), (3.0, 0.0, 1.0), 50),
    (C["cam"], (5.3, -18.5, -0.4), (5.3, 0.0, -0.3), 50),
    (C["turn"], (4.6, -18.5, 0.0), (4.6, 0.0, 0.1), 50),
    (C["try"], (2.0, -19.0, 0.9), (2.0, 0.0, 0.9), 50),
    (C["high"], (3.0, -11.5, 1.4), (3.0, 0.0, 1.2), 50),
    (C["idea"], (3.0, -16.5, 1.3), (3.0, 0.0, 1.0), 50),
    (C["four"] + 0.6, (-5.5, -15.0, 6.0), (3.0, 0.0, 0.9), 50),
    (C["eighteen"], (-4.5, -15.5, 4.8), (3.0, 0.0, 0.9), 50),
    (C["pocket"] + 0.3, (3.0, -24.0, 1.2), (3.0, 0.0, 0.9), 50),
    (C["so"] + 0.4, (2.0, -19.5, 0.95), (2.0, 0.0, 0.95), 50),
    (C["follow"], (2.2, -19.0, 1.1), (2.2, 0.0, 0.95), 50),
    (C["end"], (9.5, -16.0, 4.5), (3.0, 0.0, 0.9), 50),
]
for t, loc, tgt, lens in SHOTS:
    key(cam, "location", F(t), loc); key(TGT, "location", F(t), tgt); key(cam_d, "lens", F(t), lens)

# ---------- world + lights: studio dark backdrop, HDRI only in reflections ----------
world = bpy.data.worlds.new("World"); scene.world = world
try: world.use_nodes = True
except Exception: pass
wn, wl = world.node_tree.nodes, world.node_tree.links
for n in list(wn):
    if n.type == "BACKGROUND": wn.remove(n)
wout = next(n for n in wn if n.type == "OUTPUT_WORLD")
env = wn.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(os.path.join(PH_DIR, "kloofendal_overcast_puresky", "kloofendal_overcast_puresky_4k.hdr"), check_existing=True)
bg_env = wn.new("ShaderNodeBackground"); bg_env.inputs["Strength"].default_value = 0.6; wl.new(env.outputs["Color"], bg_env.inputs["Color"])
grad_tc = wn.new("ShaderNodeTexCoord"); grad = wn.new("ShaderNodeTexGradient"); grad.gradient_type = "SPHERICAL"
wl.new(grad_tc.outputs["Window"], grad.inputs["Vector"])
gr = wn.new("ShaderNodeValToRGB"); e = gr.color_ramp.elements; e[0].color = (0.004, 0.005, 0.007, 1); e[1].color = (0.035, 0.04, 0.05, 1)
wl.new(grad.outputs["Fac"], gr.inputs[0])
bg_dark = wn.new("ShaderNodeBackground"); wl.new(gr.outputs[0], bg_dark.inputs["Color"])
lp = wn.new("ShaderNodeLightPath"); mix = wn.new("ShaderNodeMixShader")
wl.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); wl.new(bg_env.outputs[0], mix.inputs[1]); wl.new(bg_dark.outputs[0], mix.inputs[2])
wl.new(mix.outputs[0], wout.inputs["Surface"])
def area(name, loc, size, power, rgb=(1, 1, 1)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = power; d.color = rgb
    o = bpy.data.objects.new(name, d); scene.collection.objects.link(o); o.location = loc
    tc_ = o.constraints.new("TRACK_TO"); tc_.target = LOCK; tc_.track_axis = "TRACK_NEGATIVE_Z"; tc_.up_axis = "UP_Y"
area("Key", (-4.0, -12.0, 9.0), 7.0, 2600, (1.0, 0.96, 0.9))
area("Rim", (9.0, 9.0, 7.0), 5.0, 2200, (0.75, 0.85, 1.0))
area("Fill", (10.0, -10.0, -3.0), 6.0, 700, (1.0, 0.92, 0.85))
area("Top", (3.0, -2.0, 14.0), 4.0, 900)

# ---------- render settings ----------
r = scene.render; r.engine = "CYCLES"
cp = bpy.context.preferences.addons["cycles"].preferences
for dev in ("OPTIX", "CUDA"):
    try:
        cp.compute_device_type = dev; cp.get_devices()
        if any(d.type == dev for d in cp.devices): break
    except Exception: continue
for d in cp.devices: d.use = d.type == cp.compute_device_type
scene.cycles.device = "GPU"
scene.cycles.samples = int(arg("--samples", "64")); scene.cycles.use_adaptive_sampling = True; scene.cycles.adaptive_threshold = 0.02
scene.cycles.use_denoising = True
try: scene.cycles.denoiser = "OPTIX"
except Exception: pass
scene.cycles.max_bounces = 10; scene.cycles.glossy_bounces = 6
r.use_persistent_data = True
r.resolution_x, r.resolution_y, r.resolution_percentage = 1080, 1920, 100
r.fps = FPS; scene.frame_start, scene.frame_end = 1, FRAMES
r.use_motion_blur = True; r.motion_blur_shutter = 0.4
r.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
try: scene.view_settings.look = "AgX - Medium High Contrast"
except Exception: pass
prefs.keyframe_new_interpolation_type = "BEZIER"

# ---------- export cues, click events and projected anchors for the typography ----------
ANCH = {"shell": (SHELL_B, Vector((0.5, 0.3, 3.3))), "plug": (PLUG_B, Vector((1.2, 0.3, -0.7))),
        "spring": (SPRINGS[2], Vector((0.0, 0.0, -0.45))), "top_pin": (DRIVERS[2], Vector((0.0, -0.2, LD / 2))),
        "bottom_pin": (KPINS[2], Vector((0.0, -0.2, LK[2] / 2))), "shear": (SHEAR_BAR, Vector((5.2, -0.3, SHEAR))),
        "cam": (CAM, Vector((LEN + 0.2, 0, -1.4))), "bolt": (BOLT, Vector((2.2, 0, 0))), "lock": (LOCK, Vector((0, 0, 0))),
        "keyway": (PLUG_B, Vector((0.0, 0.0, -0.1)))}
anchors = {k: [] for k in ANCH}
for fr in range(1, FRAMES + 1):
    scene.frame_set(fr)
    for k, (ob, local) in ANCH.items():
        w = ob.matrix_world @ local
        if k == "shear": w = LOCK.matrix_world @ local
        p = world_to_camera_view(scene, cam, w)
        anchors[k].append([round(p.x * 1080, 1), round((1 - p.y) * 1920, 1)])
json.dump({"fps": FPS, "frames": FRAMES, "duration": DUR, "vo_offset": VO, "cues": C, "clicks": click_events, "anchors": anchors},
          open(os.path.join(HERE, "timeline.json"), "w"))
print("CUES", {k: round(v, 2) for k, v in C.items()})
print("CLICKS", {k: len(v) for k, v in click_events.items()}, "DUR", DUR, "FRAMES", FRAMES)

save = arg("--save")
if save: bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(save))
out = arg("--out")
if "--stills" in ARGS:
    r.resolution_percentage = int(arg("--pct", "50"))
    import time
    for fr in [int(x) for x in arg("--stills").split(",")]:
        scene.frame_set(fr); r.filepath = os.path.join(out, f"still_{fr:04d}.png")
        t0 = time.time(); bpy.ops.render.render(write_still=True); print("STILL", fr, round(time.time() - t0, 1))
if "--anim" in ARGS:
    r.filepath = os.path.join(out, "f_"); bpy.ops.render.render(animation=True)
