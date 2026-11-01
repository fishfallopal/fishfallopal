"""Re-import an exported GLB into an empty scene, print its contents and render a plain PBR preview."""
import math
import os
import sys

import addon_utils
import bpy
from mathutils import Vector


def main(glb, png=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    addon_utils.enable("io_scene_gltf2", default_set=True)
    bpy.ops.import_scene.gltf(filepath=glb)
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == 'MESH']
    tris = 0
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in meshes:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    print(f"[check] {os.path.basename(glb)}: {len(meshes)} meshes, {tris} tris, "
          f"{len(bpy.data.materials)} materials, images={[i.name for i in bpy.data.images]}")
    print(f"[check] bounds min={tuple(round(v, 3) for v in lo)} max={tuple(round(v, 3) for v in hi)}")
    if not png:
        return
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = (1.2, -3.2, 1.1)
    cam.rotation_euler = (Vector((-0.05, 0.0, 0.78)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 50
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
    scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("w")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.45, 0.47, 0.5, 1)
    bg.inputs[1].default_value = 1.0
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.render.resolution_x, scene.render.resolution_y = 600, 800
    scene.view_settings.view_transform = 'Standard'
    scene.render.filepath = png
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--"]
    main(args[0], args[1] if len(args) > 1 else None)
