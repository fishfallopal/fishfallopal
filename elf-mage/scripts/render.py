"""Cel-shaded Cycles renders (toon BSDF + flat ambient + Freestyle ink) and a turnaround sheet."""
import math
import os

import bpy
from mathutils import Vector

BG = "#6F747B"
INK = "#2B1D18"
VIEWS = {
    # name: (azimuth deg, elevation deg)
    "front": (0, 0),
    "three_quarter": (35, 0),
    "side": (90, 0),
    "back": (180, 0),
}


def _lin(h):
    h = h.lstrip("#")
    out = []
    for i in range(3):
        c = int(h[2 * i:2 * i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def toonify_materials(ambient=0.58, size=0.62, smooth=0.03):
    for mat in bpy.data.materials:
        if "toon_hex" not in mat:
            continue
        nt = mat.node_tree
        out = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeOutputMaterial')
        bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        base = bsdf.inputs['Base Color']
        src = base.links[0].from_socket if base.is_linked else None
        col = tuple(base.default_value)
        toon = nt.nodes.new('ShaderNodeBsdfToon')
        toon.component = 'DIFFUSE'
        toon.inputs['Size'].default_value = size
        toon.inputs['Smooth'].default_value = smooth
        em = nt.nodes.new('ShaderNodeEmission')
        em.inputs['Strength'].default_value = ambient + float(mat.get("toon_emit", 0.0))
        add = nt.nodes.new('ShaderNodeAddShader')
        for sock in (toon.inputs['Color'], em.inputs['Color']):
            if src is not None:
                nt.links.new(src, sock)
            else:
                sock.default_value = col
        nt.links.new(em.outputs[0], add.inputs[0])
        nt.links.new(toon.outputs[0], add.inputs[1])
        nt.links.new(add.outputs[0], out.inputs['Surface'])
        try:
            mat.cycles.emission_sampling = 'NONE'
        except AttributeError:
            pass


def setup_world(scene, bg=BG):
    world = bpy.data.worlds.new("Toon_World")
    scene.world = world
    if world.node_tree is None:
        world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    dark = nt.nodes.new('ShaderNodeBackground')
    dark.inputs['Color'].default_value = (0, 0, 0, 1)
    dark.inputs['Strength'].default_value = 0.0
    bgn = nt.nodes.new('ShaderNodeBackground')
    bgn.inputs['Color'].default_value = (*_lin(bg), 1)
    bgn.inputs['Strength'].default_value = 1.0
    lp = nt.nodes.new('ShaderNodeLightPath')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
    nt.links.new(dark.outputs[0], mix.inputs[1])
    nt.links.new(bgn.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])


def setup_freestyle(scene, thickness=1.4, color=INK):
    scene.render.use_freestyle = True
    scene.render.line_thickness_mode = 'ABSOLUTE'
    scene.render.line_thickness = 1.0
    vl = scene.view_layers[0]
    vl.use_freestyle = True
    fs = vl.freestyle_settings
    fs.crease_angle = math.radians(118)
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new("Ink")
    ls.select_by_visibility = True
    ls.select_by_edge_types = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.select_external_contour = True
    style = bpy.data.linestyles.new("Ink")
    style.color = _lin(color)
    style.thickness = thickness
    style.thickness_position = 'CENTER'
    ls.linestyle = style
    return style


def setup_render(scene, samples):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.max_bounces = 2
    scene.cycles.diffuse_bounces = 0
    scene.cycles.glossy_bounces = 0
    scene.cycles.transmission_bounces = 0
    scene.cycles.transparent_max_bounces = 4
    scene.cycles.filter_width = 1.2
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False


def ensure_rig(scene, crystal_center=None):
    cam = bpy.data.objects.get("Render_Camera")
    if cam is None:
        cam = bpy.data.objects.new("Render_Camera", bpy.data.cameras.new("Render_Camera"))
        scene.collection.objects.link(cam)
    scene.camera = cam
    sun = bpy.data.objects.get("Render_Sun")
    if sun is None:
        data = bpy.data.lights.new("Render_Sun", 'SUN')
        data.energy = 2.6
        data.angle = math.radians(1.0)
        sun = bpy.data.objects.new("Render_Sun", data)
        scene.collection.objects.link(sun)
    if crystal_center is not None and bpy.data.objects.get("Crystal_Glow") is None:
        data = bpy.data.lights.new("Crystal_Glow", 'POINT')
        data.energy = 1.2
        data.color = _lin("#7DE6E0")
        data.shadow_soft_size = 0.01
        glow = bpy.data.objects.new("Crystal_Glow", data)
        glow.location = crystal_center
        scene.collection.objects.link(glow)
    return cam, sun


def aim(scene, cam, sun, azimuth, elevation, target, dist, ortho, ortho_scale=1.72, lens=85):
    az, el = math.radians(azimuth), math.radians(elevation)
    tgt = Vector(target)
    loc = tgt + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist
    cam.location = loc
    fwd = (tgt - loc).normalized()
    cam.rotation_euler = fwd.to_track_quat('-Z', 'Y').to_euler()
    cam.data.type = 'ORTHO' if ortho else 'PERSP'
    cam.data.ortho_scale = ortho_scale
    cam.data.lens = lens
    cam.data.clip_start = 0.05
    cam.data.clip_end = 50
    right = fwd.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(fwd)
    travel = (fwd * 0.62 + right * 0.45 - up * 0.64).normalized()
    sun.rotation_euler = travel.to_track_quat('-Z', 'Y').to_euler()


def set_staff_visible(visible):
    coll = bpy.data.collections.get("Staff")
    if coll:
        for ob in coll.all_objects:
            ob.hide_render = not visible
    glow = bpy.data.objects.get("Crystal_Glow")
    if glow:
        glow.hide_render = not visible


def render_to(scene, path, res):
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def render_all(scene, out_dir, quality="preview", views=("front", "three_quarter", "side", "back"),
               extras=("hero", "face")):
    os.makedirs(out_dir, exist_ok=True)
    final = quality == "final"
    setup_render(scene, 32 if final else 10)
    toonify_materials()
    setup_world(scene)
    scale = 1.0 if final else 0.5
    setup_freestyle(scene, 1.5 if final else 1.0)
    cam, sun = ensure_rig(scene, scene.get("crystal_center"))
    paths = {}
    set_staff_visible(False)
    for name in views:
        az, el = VIEWS[name]
        aim(scene, cam, sun, az, el, (0, 0.02, 0.775), 6.0, True, 1.66)
        paths[name] = render_to(scene, os.path.join(out_dir, f"view_{name}.png"),
                                (int(1000 * scale), int(1600 * scale)))
    if "face" in extras:
        aim(scene, cam, sun, 24, 3, (0.004, -0.02, 1.372), 0.80, False, lens=85)
        paths["face"] = render_to(scene, os.path.join(out_dir, "closeup_face.png"),
                                  (int(1100 * scale), int(1100 * scale)))
    if "hero" in extras:
        set_staff_visible(True)
        aim(scene, cam, sun, 28, 7, (-0.12, 0.02, 0.80), 3.4, False, lens=55)
        paths["hero"] = render_to(scene, os.path.join(out_dir, "hero.png"),
                                  (int(1200 * scale), int(1600 * scale)))
        set_staff_visible(False)
    return paths


def compose_sheet(paths, out_path, title="Original Elf Mage — turnaround"):
    from PIL import Image, ImageDraw, ImageFont
    order = [k for k in ("front", "three_quarter", "side", "back") if k in paths]
    imgs = [Image.open(paths[k]).convert("RGB") for k in order]
    w, h = imgs[0].size
    crop = int(w * 0.17)
    tiles = [im.crop((crop, 0, w - crop, h)) for im in imgs]
    tw = tiles[0].size[0]
    pad = int(h * 0.06)
    sheet = Image.new("RGB", (tw * len(tiles), h + pad), tuple(int(BG[i:i + 2], 16) for i in (1, 3, 5)))
    for i, t in enumerate(tiles):
        sheet.paste(t, (i * tw, pad))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", int(pad * 0.5))
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", int(pad * 0.3))
    except OSError:
        font = small = ImageFont.load_default()
    d.text((int(pad * 0.4), int(pad * 0.18)), title, fill=(240, 240, 240), font=font)
    labels = {"front": "front", "three_quarter": "3/4", "side": "side", "back": "back"}
    for i, k in enumerate(order):
        d.text((i * tw + int(pad * 0.4), pad + int(pad * 0.2)), labels[k], fill=(225, 228, 232), font=small)
    sheet.save(out_path)
    return out_path
