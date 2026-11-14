"""fx.py — standard Blender "power-ups" for every 3D episode (Rizky, 15 Nov 2026: use them all).

Use in build_scene.py:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "pipeline3d"))
    import fx
    fx.hdri("sunset", strength=1.0)              # 1. HDRI sky/light (Blender bundled or Poly Haven id)
    fx.glare(threshold=0.9)                      # 2. bloom/glare + filmic-ish grade in the compositor
    fx.particles(emitter_obj, kind="dust")       # 3. dust | sparks | rain | mud, frame range optional
    fx.rigid(objs, passive=[ground]); fx.bake_rigid(1, 120)   # 4. real falling/collapsing
    fx.fluid_domain(dom, flow_obj, eff=[pipe], res=96)        # 5. Mantaflow water for 1-2 short shots
    fx.scatter(surface, instance_obj, density=20)  # 6. Geometry Nodes scatter (rocks, trees, houses)
    fx.engine("eevee") / fx.engine("cycles")     # 7. EEVEE Next for simple shots (5-10x faster)
Every function is defensive: if the Blender API differs it prints a warning and the scene still renders.
"""
import bpy, os, glob

HERE = os.path.dirname(os.path.abspath(__file__))


def _warn(what, e):
    print(f"[fx] {what} skipped: {e}")


# 1. HDRI -------------------------------------------------------------------
def hdri(name="sunset", strength=1.0, rotation_deg=0.0, show_background=True):
    """name = Blender bundled (city courtyard forest interior night studio sunrise sunset)
    or a Poly Haven id already in pipeline3d/assets/polyhaven/<id>/ (fetch_polyhaven.js), or a file path."""
    try:
        path = name if os.path.isfile(name) else None
        if not path:
            hits = glob.glob(os.path.join(HERE, "assets", "polyhaven", name, "*.hdr")) + \
                   glob.glob(os.path.join(HERE, "assets", "polyhaven", name, "*.exr"))
            path = hits[0] if hits else None
        if not path:
            base = os.path.dirname(bpy.app.binary_path)
            hits = glob.glob(os.path.join(base, "*", "datafiles", "studiolights", "world", name + ".exr"))
            path = hits[0] if hits else None
        if not path:
            raise FileNotFoundError(name)
        w = bpy.context.scene.world or bpy.data.worlds.new("World")
        bpy.context.scene.world = w
        w.use_nodes = True
        nt = w.node_tree; nt.nodes.clear()
        tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
        env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(path, check_existing=True)
        bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = strength
        out = nt.nodes.new("ShaderNodeOutputWorld")
        mp.inputs["Rotation"].default_value[2] = rotation_deg * 3.14159265 / 180
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], env.inputs["Vector"])
        nt.links.new(env.outputs["Color"], bg.inputs["Color"])
        if show_background:
            nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
        else:  # light from HDRI, camera sees a plain colour
            mix = nt.nodes.new("ShaderNodeMixShader"); lp = nt.nodes.new("ShaderNodeLightPath")
            plain = nt.nodes.new("ShaderNodeBackground"); plain.inputs["Color"].default_value = (0.02, 0.02, 0.03, 1)
            nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs["Fac"])
            nt.links.new(bg.outputs["Background"], mix.inputs[1]); nt.links.new(plain.outputs["Background"], mix.inputs[2])
            nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
        print(f"[fx] hdri {os.path.basename(path)}")
    except Exception as e:
        _warn("hdri", e)


# 2. Compositor glare / grade ---------------------------------------------
def glare(threshold=0.9, strength=0.6, size=7, look=None):
    sc = bpy.context.scene
    try:
        if look:
            sc.view_settings.look = look
    except Exception as e:
        _warn("look", e)
    try:
        if hasattr(sc, "compositing_node_group"):          # Blender 5.x
            nt = sc.compositing_node_group or bpy.data.node_groups.new("FX Compositor", "CompositorNodeTree")
            sc.compositing_node_group = nt
            nt.nodes.clear()
            rl = nt.nodes.new("CompositorNodeRLayers"); g = nt.nodes.new("CompositorNodeGlare")
            out = nt.nodes.new("NodeGroupOutput")
            if not nt.interface.items_tree:
                nt.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            _set_glare(g, threshold, strength, size)
            nt.links.new(rl.outputs["Image"], g.inputs["Image"]); nt.links.new(g.outputs["Image"], out.inputs[0])
        else:                                               # Blender 4.x
            sc.use_nodes = True; nt = sc.node_tree; nt.nodes.clear()
            rl = nt.nodes.new("CompositorNodeRLayers"); g = nt.nodes.new("CompositorNodeGlare")
            out = nt.nodes.new("CompositorNodeComposite")
            _set_glare(g, threshold, strength, size)
            nt.links.new(rl.outputs["Image"], g.inputs["Image"]); nt.links.new(g.outputs["Image"], out.inputs["Image"])
        print("[fx] glare on")
    except Exception as e:
        _warn("glare", e)


def _set_glare(g, threshold, strength, size):
    for attr, val in (("glare_type", "BLOOM"), ("threshold", threshold), ("size", size), ("mix", strength - 1)):
        try: setattr(g, attr, val)
        except Exception: pass
    for sock, val in (("Type", "Bloom"), ("Threshold", threshold), ("Strength", strength), ("Size", size / 9)):
        try: g.inputs[sock].default_value = val
        except Exception: pass


# 3. Particles --------------------------------------------------------------
_PRESETS = {  # count, lifetime, size, velocity normal, gravity, colour (emission), emission strength
    "dust":   (400, 60, 0.02, 0.6, 0.1, (0.55, 0.45, 0.35, 1), 0.0),
    "sparks": (250, 18, 0.012, 4.0, 1.0, (1.0, 0.55, 0.15, 1), 25.0),
    "rain":   (3000, 40, 0.008, -6.0, 1.0, (0.7, 0.8, 1.0, 1), 0.0),
    "mud":    (300, 40, 0.04, 2.5, 1.0, (0.25, 0.17, 0.1, 1), 0.0),
}


def particles(emitter, kind="dust", start=1, end=None, count=None):
    try:
        n, life, size, vel, grav, col, emis = _PRESETS[kind]
        end = end or bpy.context.scene.frame_end
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1)
        dot = bpy.context.active_object; dot.name = f"fx_{kind}_dot"; dot.hide_render = False
        dot.location = (0, 0, -1000)
        m = bpy.data.materials.new(f"fx_{kind}"); m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value = col
        if emis:
            b.inputs["Emission Color"].default_value = col; b.inputs["Emission Strength"].default_value = emis
        dot.data.materials.append(m)
        mod = emitter.modifiers.new(f"fx_{kind}", "PARTICLE_SYSTEM"); ps = mod.particle_system.settings
        ps.count = count or n; ps.frame_start = start; ps.frame_end = end; ps.lifetime = life
        ps.normal_factor = vel; ps.factor_random = 0.5; ps.effector_weights.gravity = grav
        ps.render_type = "OBJECT"; ps.instance_object = dot; ps.particle_size = size; ps.size_random = 0.6
        emitter.show_instancer_for_render = True
        print(f"[fx] particles {kind} on {emitter.name}")
        return mod
    except Exception as e:
        _warn("particles", e)


# 4. Rigid body -------------------------------------------------------------
def rigid(active_objs, passive=(), mass=1.0, friction=0.6, bounce=0.1):
    try:
        if not bpy.context.scene.rigidbody_world:
            bpy.ops.rigidbody.world_add()
        for o, kind in [(o, "ACTIVE") for o in active_objs] + [(o, "PASSIVE") for o in passive]:
            bpy.context.view_layer.objects.active = o
            if not o.rigid_body:
                bpy.ops.rigidbody.object_add()
            o.rigid_body.type = kind; o.rigid_body.mass = mass
            o.rigid_body.friction = friction; o.rigid_body.restitution = bounce
            o.rigid_body.collision_shape = "CONVEX_HULL" if kind == "ACTIVE" else "MESH"
        print(f"[fx] rigid {len(active_objs)} active, {len(passive)} passive")
    except Exception as e:
        _warn("rigid", e)


def bake_rigid(start, end):
    try:
        pc = bpy.context.scene.rigidbody_world.point_cache
        pc.frame_start, pc.frame_end = start, end
        bpy.ops.ptcache.bake_all(bake=True)
    except Exception as e:
        _warn("bake_rigid", e)


# 5. Mantaflow liquid -------------------------------------------------------
def fluid_domain(domain, flow, eff=(), res=96, start=1, end=None, cache_dir=None):
    """Liquid sim. Keep it to 1-2 short shots: bake cost grows fast with res."""
    try:
        end = end or bpy.context.scene.frame_end
        d = domain.modifiers.new("fx_fluid", "FLUID"); d.fluid_type = "DOMAIN"
        ds = d.domain_settings; ds.domain_type = "LIQUID"; ds.resolution_max = res
        ds.use_mesh = True; ds.cache_frame_start = start; ds.cache_frame_end = end
        ds.cache_type = "ALL"
        ds.cache_directory = cache_dir or os.path.join(bpy.path.abspath("//"), "cache_fluid")
        f = flow.modifiers.new("fx_flow", "FLUID"); f.fluid_type = "FLOW"
        f.flow_settings.flow_type = "LIQUID"; f.flow_settings.flow_behavior = "INFLOW"
        for o in eff:
            e = o.modifiers.new("fx_eff", "FLUID"); e.fluid_type = "EFFECTOR"
        print(f"[fx] fluid domain {domain.name} res {res}")
    except Exception as e:
        _warn("fluid", e)


def bake_fluid(domain):
    try:
        bpy.context.view_layer.objects.active = domain
        bpy.ops.fluid.bake_all()
    except Exception as e:
        _warn("bake_fluid", e)


# 6. Geometry Nodes scatter ---------------------------------------------------
def scatter(surface, instance_obj, density=10.0, scale_min=0.6, scale_max=1.4, seed=0):
    try:
        ng = bpy.data.node_groups.new(f"fx_scatter_{instance_obj.name}", "GeometryNodeTree")
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        N = ng.nodes; L = ng.links
        gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
        dist = N.new("GeometryNodeDistributePointsOnFaces"); dist.inputs["Density"].default_value = density
        dist.inputs["Seed"].default_value = seed
        oi = N.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = instance_obj
        inst = N.new("GeometryNodeInstanceOnPoints")
        def _sock(node, socks, name, typ):
            return next(s for s in socks if s.name == name and s.type == typ)
        rnd = N.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT"
        _sock(rnd, rnd.inputs, "Min", "VALUE").default_value = scale_min
        _sock(rnd, rnd.inputs, "Max", "VALUE").default_value = scale_max
        rot = N.new("FunctionNodeRandomValue"); rot.data_type = "FLOAT_VECTOR"
        _sock(rot, rot.inputs, "Max", "VECTOR").default_value = (0, 0, 6.283)
        join = N.new("GeometryNodeJoinGeometry")
        L.new(gi.outputs[0], dist.inputs["Mesh"]); L.new(dist.outputs["Points"], inst.inputs["Points"])
        L.new(oi.outputs["Geometry"], inst.inputs["Instance"])
        L.new(_sock(rnd, rnd.outputs, "Value", "VALUE"), inst.inputs["Scale"])
        L.new(_sock(rot, rot.outputs, "Value", "VECTOR"), inst.inputs["Rotation"])
        L.new(gi.outputs[0], join.inputs[0]); L.new(inst.outputs[0], join.inputs[0])
        L.new(join.outputs[0], go.inputs[0])
        mod = surface.modifiers.new("fx_scatter", "NODES"); mod.node_group = ng
        instance_obj.hide_render = True; instance_obj.hide_viewport = True
        print(f"[fx] scatter {instance_obj.name} on {surface.name}")
        return mod
    except Exception as e:
        _warn("scatter", e)


# 7. Engine -------------------------------------------------------------------
def engine(which="cycles"):
    sc = bpy.context.scene
    try:
        if which == "eevee":
            sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in \
                [i.identifier for i in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
            try:
                sc.eevee.use_raytracing = True; sc.eevee.use_shadows = True
            except Exception: pass
        else:
            sc.render.engine = "CYCLES"
        print(f"[fx] engine {sc.render.engine}")
    except Exception as e:
        _warn("engine", e)
