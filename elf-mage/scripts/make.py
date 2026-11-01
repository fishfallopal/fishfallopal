"""Build the elf mage model, export it (GLB/FBX/.blend) and render previews.

Usage (Blender 5.0 as a Python module):
    python elf-mage/scripts/make.py --export --render final
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import character  # noqa: E402
import render  # noqa: E402

ROOT = os.path.dirname(HERE)


def mesh_stats():
    dg = bpy.context.evaluated_depsgraph_get()
    tris = verts = 0
    for ob in bpy.context.scene.objects:
        if ob.type != 'MESH':
            continue
        me = ob.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        verts += len(me.vertices)
        ob.evaluated_get(dg).to_mesh_clear()
    return verts, tris


def export(out_dir):
    import addon_utils
    os.makedirs(out_dir, exist_ok=True)
    addon_utils.enable("io_scene_gltf2", default_set=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(out_dir, "elf_mage.glb"), export_format='GLB',
                              export_apply=True, export_yup=True, use_selection=False,
                              export_cameras=False, export_lights=False)
    addon_utils.enable("io_scene_fbx", default_set=True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out_dir, "elf_mage.fbx"), use_mesh_modifiers=True,
                             path_mode='COPY', embed_textures=True, apply_scale_options='FBX_SCALE_ALL',
                             object_types={'EMPTY', 'MESH'})
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "elf_mage.blend"), compress=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "model"))
    ap.add_argument("--renders", default=os.path.join(ROOT, "renders"))
    ap.add_argument("--export", action="store_true")
    ap.add_argument("--render", choices=["none", "preview", "final"], default="preview")
    ap.add_argument("--views", default="front,three_quarter,side,back")
    ap.add_argument("--extras", default="hero,face")
    args = ap.parse_args([a for a in sys.argv[1:] if a != "--"])

    t0 = time.time()
    scene = character.build(args.out)
    verts, tris = mesh_stats()
    print(f"[make] built in {time.time() - t0:.1f}s: {verts} verts, {tris} tris (viewport levels)")
    if args.export:
        export(args.out)
        print(f"[make] exported to {args.out}")
    if args.render != "none":
        t1 = time.time()
        views = [v for v in args.views.split(",") if v]
        extras = [e for e in args.extras.split(",") if e]
        paths = render.render_all(scene, args.renders, args.render, views, extras)
        if all(k in paths for k in ("front", "three_quarter", "side", "back")):
            render.compose_sheet(paths, os.path.join(args.renders, "turnaround.png"))
        print(f"[make] rendered {list(paths)} in {time.time() - t1:.1f}s")


if __name__ == "__main__":
    main()
