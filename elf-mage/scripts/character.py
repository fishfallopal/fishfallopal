"""Procedural builder for an original anime-style elf herbalist mage.

Everything is generated from analytic profiles (superellipse sections, swept tubes, clumps),
so the model is reproducible from code. Units are metres, Z up, the character faces -Y."""
import math
import os

import bpy
import numpy as np
from mathutils import Matrix, Vector

import face_texture
from geom import (TAU, Capsule, Ellipsoid, MeshBuilder, Pchip, ProfileBody, add_solidify, add_subsurf,
                  apply_modifiers, catmull_rom, clamp, ellipsoid, from_builder, grid_faces, hex_to_linear,
                  lerp, loft, make_object, orient_outward, path_frames, push_points, resample, se_xy,
                  smooth_path, smoothstep, spow, tube_ring)

R = math.radians
V = Vector

PALETTE = dict(
    skin="#F7DECE", hair="#B4532F", blouse="#EFE7D6", trim="#2E5B47", corset="#6B4129",
    piping="#3E2618", lace="#EFE7D6", belt="#3E2A1D", bronze="#B8853F", amber="#E39A27",
    cape="#2E5A46", lining="#21402F", leggings="#3A302C", boots="#8C5B37", boot_cuff="#A06C43",
    sole="#3A2A20", strap="#4B3122", wood="#6A4A2F", crystal="#7DE6E0", leaf="#5E9A4A",
    glass="#CDEFE3", potion="#4FBF7A", cork="#B88A5A", ribbon="#2E5A46", pouch="#5C3B25",
)

# ----------------------------------------------------------------------------- profiles
# (z, half width, front y, back y, y of widest point, front squareness, back squareness)
HEAD_ROWS = [
    (1.2665, 0.013, -0.0712, -0.042, -0.055, 2.0, 2.0),
    (1.2705, 0.024, -0.0745, -0.022, -0.042, 2.0, 2.0),
    (1.2770, 0.035, -0.0775, 0.008, -0.025, 2.0, 2.0),
    (1.2860, 0.045, -0.0805, 0.036, -0.012, 2.1, 2.0),
    (1.2970, 0.055, -0.0833, 0.058, -0.004, 2.2, 2.1),
    (1.3100, 0.065, -0.0858, 0.074, 0.000, 2.3, 2.1),
    (1.3250, 0.074, -0.0878, 0.085, 0.002, 2.4, 2.1),
    (1.3400, 0.081, -0.0893, 0.092, 0.003, 2.5, 2.1),
    (1.3550, 0.085, -0.0900, 0.097, 0.004, 2.6, 2.1),
    (1.3750, 0.0875, -0.0900, 0.100, 0.005, 2.6, 2.1),
    (1.3950, 0.088, -0.0890, 0.101, 0.006, 2.5, 2.1),
    (1.4150, 0.087, -0.0870, 0.100, 0.007, 2.4, 2.1),
    (1.4350, 0.083, -0.0830, 0.097, 0.008, 2.3, 2.05),
    (1.4550, 0.075, -0.0750, 0.090, 0.009, 2.2, 2.0),
    (1.4720, 0.064, -0.0640, 0.080, 0.010, 2.1, 2.0),
    (1.4850, 0.051, -0.0480, 0.067, 0.010, 2.0, 2.0),
    (1.4930, 0.036, -0.0300, 0.050, 0.010, 2.0, 2.0),
    (1.4975, 0.020, -0.0100, 0.030, 0.010, 2.0, 2.0),
]
CHIN_PT = V((0.0, -0.060, 1.2642))
CROWN_PT = V((0.0, 0.010, 1.5000))

# The head is authored in "head-local" metres (matching the face texture) and scaled up around
# the jaw for slightly larger anime proportions.
HEAD_SCALE = 1.08
HEAD_PIVOT = V((0.0, 0.0, 1.27))


def hz(z):
    return HEAD_PIVOT.z + (z - HEAD_PIVOT.z) * HEAD_SCALE


def ht(p):
    return HEAD_PIVOT + (V(p) - HEAD_PIVOT) * HEAD_SCALE


def ht_inv(p):
    return HEAD_PIVOT + (V(p) - HEAD_PIVOT) / HEAD_SCALE


def _scaled_rows(rows):
    s, py, pz = HEAD_SCALE, HEAD_PIVOT.y, HEAD_PIVOT.z
    return [(pz + (z - pz) * s, w * s, py + (f - py) * s, py + (b - py) * s, py + (m - py) * s, pf, pb)
            for z, w, f, b, m, pf, pb in rows]

TORSO_ROWS = [
    (0.735, 0.100, -0.066, 0.078, 0.004, 2.3, 2.2),
    (0.775, 0.122, -0.071, 0.087, 0.006, 2.4, 2.3),
    (0.815, 0.132, -0.073, 0.090, 0.006, 2.4, 2.3),
    (0.860, 0.126, -0.069, 0.082, 0.005, 2.4, 2.3),
    (0.910, 0.110, -0.064, 0.070, 0.003, 2.3, 2.2),
    (0.960, 0.101, -0.062, 0.064, 0.002, 2.3, 2.2),
    (1.005, 0.104, -0.067, 0.063, 0.002, 2.3, 2.2),
    (1.045, 0.113, -0.078, 0.065, 0.003, 2.3, 2.2),
    (1.080, 0.120, -0.081, 0.067, 0.004, 2.3, 2.2),
    (1.110, 0.126, -0.075, 0.069, 0.005, 2.4, 2.3),
    (1.135, 0.132, -0.066, 0.069, 0.006, 2.5, 2.4),
    (1.160, 0.138, -0.058, 0.066, 0.007, 2.6, 2.5),
    (1.180, 0.135, -0.052, 0.062, 0.008, 2.6, 2.5),
    (1.195, 0.120, -0.047, 0.058, 0.008, 2.5, 2.4),
    (1.207, 0.098, -0.042, 0.054, 0.008, 2.4, 2.3),
    (1.217, 0.074, -0.038, 0.050, 0.008, 2.2, 2.2),
    (1.226, 0.052, -0.034, 0.046, 0.008, 2.1, 2.1),
    (1.236, 0.037, -0.030, 0.042, 0.008, 2.0, 2.0),
]

SKIRT_ROWS = [
    (0.505, 0.235, -0.183, 0.189, 0.006, 2.2, 2.2),
    (0.560, 0.223, -0.170, 0.177, 0.006, 2.2, 2.2),
    (0.620, 0.209, -0.155, 0.163, 0.006, 2.2, 2.2),
    (0.680, 0.194, -0.138, 0.147, 0.006, 2.2, 2.2),
    (0.740, 0.178, -0.120, 0.130, 0.006, 2.2, 2.2),
    (0.800, 0.161, -0.101, 0.111, 0.006, 2.2, 2.2),
    (0.840, 0.148, -0.089, 0.099, 0.005, 2.2, 2.2),
    (0.880, 0.134, -0.080, 0.088, 0.004, 2.2, 2.2),
    (0.925, 0.116, -0.071, 0.075, 0.003, 2.2, 2.2),
]

CORSET_ROWS = [
    (0.828, 0.151, -0.098, 0.105, 0.005, 2.3, 2.2),
    (0.868, 0.143, -0.087, 0.096, 0.005, 2.3, 2.2),
    (0.900, 0.132, -0.080, 0.086, 0.004, 2.3, 2.2),
    (0.930, 0.121, -0.074, 0.077, 0.003, 2.3, 2.2),
    (0.965, 0.110, -0.070, 0.0715, 0.003, 2.3, 2.2),
    (1.005, 0.1115, -0.0745, 0.0705, 0.003, 2.3, 2.2),
    (1.045, 0.120, -0.0855, 0.0725, 0.004, 2.3, 2.2),
    (1.070, 0.125, -0.0885, 0.0735, 0.004, 2.3, 2.2),
]

# cape rows: z, half width, back y, side y, front y, squareness, half angle (deg), side drop, fold amp
CAPE_ROWS = [
    (1.248, 0.050, 0.052, 0.010, -0.028, 2.0, 124, 0.008, 0.000),
    (1.240, 0.082, 0.062, 0.012, -0.040, 2.2, 117, 0.016, 0.000),
    (1.228, 0.118, 0.070, 0.014, -0.050, 2.4, 110, 0.024, 0.000),
    (1.212, 0.154, 0.076, 0.016, -0.058, 2.6, 103, 0.030, 0.000),
    (1.194, 0.184, 0.080, 0.018, -0.062, 2.8, 96, 0.032, 0.002),
    (1.164, 0.202, 0.082, 0.022, -0.060, 2.8, 90, 0.026, 0.004),
    (1.115, 0.212, 0.084, 0.030, -0.050, 2.7, 84, 0.016, 0.006),
    (1.050, 0.218, 0.088, 0.036, -0.040, 2.6, 80, 0.006, 0.008),
    (0.960, 0.224, 0.098, 0.042, -0.030, 2.5, 79, 0.000, 0.011),
    (0.850, 0.234, 0.132, 0.046, -0.020, 2.4, 81, 0.000, 0.014),
    (0.720, 0.250, 0.172, 0.050, -0.010, 2.3, 84, 0.000, 0.018),
    (0.580, 0.268, 0.207, 0.052, 0.000, 2.2, 87, 0.000, 0.021),
    (0.450, 0.286, 0.232, 0.052, 0.000, 2.2, 89, 0.000, 0.024),
    (0.340, 0.300, 0.250, 0.050, 0.000, 2.2, 90, 0.000, 0.026),
]
CAPE = Pchip([r[0] for r in CAPE_ROWS], [r[1:] for r in CAPE_ROWS])

LEG_CENTER = Pchip([0.09, 0.26, 0.43, 0.60, 0.78],
                   [[0.068, 0.016], [0.069, 0.004], [0.070, -0.010], [0.072, -0.004], [0.073, 0.002]])
LEG_RAD = Pchip([0.085, 0.13, 0.19, 0.26, 0.33, 0.40, 0.44, 0.50, 0.58, 0.68, 0.78],
                [[0.028, 0.030, 0.030], [0.030, 0.031, 0.033], [0.035, 0.034, 0.040], [0.041, 0.038, 0.050],
                 [0.044, 0.040, 0.054], [0.043, 0.043, 0.048], [0.044, 0.046, 0.044], [0.048, 0.048, 0.049],
                 [0.054, 0.054, 0.055], [0.062, 0.062, 0.064], [0.068, 0.068, 0.072]])

HEAD_LOCAL = ProfileBody(HEAD_ROWS)
HEAD = ProfileBody(_scaled_rows(HEAD_ROWS))
TORSO = ProfileBody(TORSO_ROWS)
CORSET = ProfileBody(CORSET_ROWS)


def skirt_amp(z):
    return 0.016 * clamp((0.905 - z) / 0.40, 0.0, 1.0) ** 1.4


def skirt_fold(phi):
    return math.sin(16 * phi + 0.35 * math.sin(3 * phi + 0.5))


SKIRT = ProfileBody(SKIRT_ROWS, extra=lambda phi, z: skirt_amp(z))
CAPE_BODY = ProfileBody([(r[0], r[1], r[4], r[2], r[3], r[5], r[5]) for r in CAPE_ROWS])


def belt_z(phi):
    return 0.80 + 0.022 * math.cos(phi)


# ----------------------------------------------------------------------------- helpers
def section_point(body, z, phi, offset=0.0):
    w, front, back, ym, pf, pb = body.section(z)
    x, y = se_xy(phi, w + offset, front - offset, back + offset, ym, pf, pb)
    return V((x, y, z))


def head_point(z, phi):
    return section_point(HEAD, z, phi)


def head_normal(z, phi):
    e = 1e-4
    dp = head_point(z, phi + e) - head_point(z, phi - e)
    dz = head_point(z + e, phi) - head_point(z - e, phi)
    n = dp.cross(dz)
    return n.normalized()


def scalp(z, phi, off):
    return head_point(z, phi) + head_normal(z, phi) * off


def arm_geometry(side=1):
    S = V((0.145, 0.006, 1.160))
    d1 = V((math.sin(R(18)), -0.03, -math.cos(R(18)))).normalized()
    E = S + d1 * 0.235
    d2 = V((math.sin(R(12)), -0.16, -math.cos(R(12)))).normalized()
    W = E + d2 * 0.205
    d3 = (d2 + V((0.05, 0.03, 0.0))).normalized()
    if side < 0:
        S, E, W, d1, d2, d3 = (V((-p.x, p.y, p.z)) for p in (S, E, W, d1, d2, d3))
    return S, E, W, d1, d2, d3


def mirror_geo(verts, faces):
    return [V((-v.x, v.y, v.z)) for v in verts], [tuple(reversed(f)) for f in faces]


def rounded_tube(points, rfn, n=10, ref_fn=None, flat=1.0, cap_start=True):
    """Tube with a hemispherical end. rfn(t) -> radius. flat scales the N axis."""
    frames = path_frames(points, ref_fn or (lambda i, p: (1, 0, 0)))
    rings = []
    for i, (P, (T, N, B)) in enumerate(zip(points, frames)):
        r = rfn(i / (len(points) - 1))
        rings.append(tube_ring(P, N, B, r * flat, r, r, n))
    P, (T, N, B) = points[-1], frames[-1]
    r = rfn(1.0)
    for a, s in ((0.40, 0.92), (0.75, 0.66), (0.95, 0.31)):
        rings.append(tube_ring(P + T * (a * r), N, B, r * s * flat, r * s, r * s, n))
    return loft(rings, True, cap_start, True, None, P + T * r)


def loop_tube(points, r, n=8):
    """Closed tube along a closed polyline (points not repeated)."""
    m = len(points)
    rings = []
    for i in range(m):
        T = (points[(i + 1) % m] - points[i - 1]).normalized()
        up = V((0, 0, 1))
        N = (up - T * up.dot(T))
        if N.length < 1e-6:
            N = T.orthogonal()
        N.normalize()
        B = T.cross(N)
        rings.append(tube_ring(points[i], N, B, r, r, r, n))
    verts = [p for ring in rings for p in ring]
    faces = []
    for i in range(m):
        a, b = i * n, ((i + 1) % m) * n
        for j in range(n):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    return verts, faces


def torus_geo(center, axis, radius, tube, n_major=24, n_minor=8, x_hint=(1, 0, 0), scale=(1, 1)):
    z = V(axis).normalized()
    x = V(x_hint)
    x = (x - z * x.dot(z)).normalized()
    y = z.cross(x)
    pts = [V(center) + x * (radius * scale[0] * math.cos(TAU * k / n_major))
           + y * (radius * scale[1] * math.sin(TAU * k / n_major)) for k in range(n_major)]
    return loop_tube(pts, tube, n_minor)


def leaf_geo(base, axis, normal, length, width, thick, n_len=12, n_ring=10, bend=0.0):
    a = V(axis).normalized()
    nrm = V(normal)
    nrm = (nrm - a * nrm.dot(a)).normalized()
    b = nrm.cross(a)
    rings = []
    for i in range(1, n_len):
        t = i / n_len
        w = width * math.sin(math.pi * t) ** 0.8 * (1 - 0.3 * t)
        h = thick * (0.45 + 0.55 * math.sin(math.pi * t))
        C = V(base) + a * (t * length) + nrm * (bend * math.sin(math.pi * t))
        ring = []
        for k in range(n_ring):
            ph = TAU * k / n_ring
            c, s = math.cos(ph), math.sin(ph)
            ring.append(C + b * (w * c) + nrm * (h * s + (0.5 * h * (1 - c * c) if s > 0 else 0.0)))
        rings.append(ring)
    return loft(rings, True, True, True, V(base), V(base) + a * length)


def surface_frame(grid, i, j):
    rows, cols = len(grid), len(grid[0])
    du = grid[i][min(j + 1, cols - 1)] - grid[i][max(j - 1, 0)]
    dv = grid[min(i + 1, rows - 1)][j] - grid[max(i - 1, 0)][j]
    return du.normalized(), dv.normalized(), du.cross(dv).normalized()


# ----------------------------------------------------------------------------- materials
def make_materials(face_image):
    M = {}

    def mk(key, name, rough=0.75, metal=0.0, emit=0.0, image=None, hexc=None):
        hexc = hexc or PALETTE[key]
        mat = bpy.data.materials.new(name)
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        col = hex_to_linear(hexc)
        bsdf.inputs['Base Color'].default_value = col
        bsdf.inputs['Roughness'].default_value = rough
        bsdf.inputs['Metallic'].default_value = metal
        if emit:
            bsdf.inputs['Emission Color'].default_value = col
            bsdf.inputs['Emission Strength'].default_value = emit
        if image is not None:
            tex = nt.nodes.new('ShaderNodeTexImage')
            tex.image = image
            tex.location = (-420, 260)
            nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        mat.diffuse_color = col
        mat['toon_hex'] = hexc
        mat['toon_emit'] = emit
        M[key] = mat
        return mat

    mk('face', 'Skin_Face', 0.6, image=face_image, hexc=PALETTE['skin'])
    mk('skin', 'Skin', 0.6)
    mk('hair', 'Hair', 0.45)
    mk('blouse', 'Blouse', 0.85)
    mk('trim', 'Trim_Green', 0.8)
    mk('corset', 'Corset_Leather', 0.55)
    mk('piping', 'Leather_Dark', 0.6)
    mk('lace', 'Lace', 0.85)
    mk('belt', 'Belt', 0.55)
    mk('bronze', 'Bronze', 0.35, 0.8)
    mk('amber', 'Amber_Gem', 0.15, 0.0, emit=0.15)
    mk('cape', 'Cape', 0.85)
    mk('lining', 'Cape_Lining', 0.85)
    mk('leggings', 'Leggings', 0.8)
    mk('boots', 'Boots', 0.5)
    mk('boot_cuff', 'Boot_Cuff', 0.7)
    mk('sole', 'Sole', 0.8)
    mk('strap', 'Strap', 0.55)
    mk('wood', 'Wood', 0.8)
    mk('crystal', 'Crystal', 0.1, 0.0, emit=2.5)
    mk('leaf', 'Leaf', 0.7)
    mk('glass', 'Glass', 0.1)
    mk('potion', 'Potion', 0.2, 0.0, emit=0.3)
    mk('cork', 'Cork', 0.9)
    mk('ribbon', 'Ribbon', 0.7)
    mk('pouch', 'Pouch', 0.6)
    return M


# ----------------------------------------------------------------------------- body
def build_head(coll, M):
    zs = list(np.linspace(1.2665, 1.42, 38)) + list(np.linspace(1.42, 1.4975, 13))[1:]
    rings = []
    n = 64
    for z in zs:
        ring = []
        for k in range(n):
            p = section_point(HEAD_LOCAL, z, TAU * k / n)
            if p.y < -0.06:
                gx = math.exp(-(p.x / 0.0062) ** 2)
                dz = z - 1.3335
                gz = math.exp(-(dz / 0.0045) ** 2) if dz < 0 else math.exp(-(dz / 0.0150) ** 2)
                p.y -= 0.0058 * gx * gz
                p.y -= 0.0012 * math.exp(-(p.x / 0.011) ** 2) * math.exp(-((z - 1.3035) / 0.0055) ** 2)
            ring.append(ht(p))
        rings.append(ring)
    verts, faces = loft(rings, True, True, True, ht(CHIN_PT), ht(CROWN_PT))
    ob = make_object("Head", verts, faces, [M['face']], coll, subsurf=(1, 1))
    apply_modifiers(ob)
    me = ob.data
    # planar front projection (in head-local units) for the face texture; the rest samples skin
    uv = me.uv_layers.new(name="UVMap")
    X0, X1, Z0, Z1 = face_texture.X0, face_texture.X1, face_texture.Z0, face_texture.Z1
    co = [ht_inv(v.co) for v in me.vertices]
    data = [0.0] * (2 * len(me.loops))
    for poly in me.polygons:
        inside = poly.normal.y < -0.35 and all(
            abs(co[i].x) < 0.078 and Z0 + 0.003 < co[i].z < Z1 - 0.003 for i in poly.vertices)
        for li in poly.loop_indices:
            p = co[me.loops[li].vertex_index]
            if inside:
                data[2 * li], data[2 * li + 1] = (p.x - X0) / (X1 - X0), (p.z - Z0) / (Z1 - Z0)
            else:
                data[2 * li], data[2 * li + 1] = 0.004, 0.004
    uv.data.foreach_set("uv", data)
    # anime-style face shading: blend vertex normals toward a smooth ellipsoid
    normals = []
    for v, p in zip(me.vertices, co):
        prox = V((p.x / 0.088 ** 2, (p.y - 0.02) / 0.098 ** 2, (p.z - 1.372) / 0.115 ** 2)).normalized()
        w = smoothstep(0.0, -0.05, p.y) * smoothstep(1.287, 1.318, p.z)
        normals.append(v.normal.lerp(prox, w).normalized())
    me.normals_split_custom_set_from_vertices(normals)
    md = add_subsurf(ob, 0, 1)
    md.use_custom_normals = True
    return ob


def ear_geo():
    k = HEAD_SCALE
    z0, ph0 = hz(1.352), R(4)
    R0 = head_point(z0, ph0) - head_normal(z0, ph0) * 0.004
    u = V((0.80, 0.30, 0.52)).normalized()
    w = V((0.30, -0.95, 0.05))
    w = (w - u * w.dot(u)).normalized()
    up = u.cross(w).normalized()
    if up.z < 0:
        up = -up
    L = 0.090 * k
    rings = []
    for t in [-0.10, -0.04] + [i / 15 * 0.97 for i in range(16)]:
        tt = max(t, 0.0)
        top = 0.021 * k * (1 - tt) ** 0.85 * (1 + 0.28 * math.sin(math.pi * tt))
        bot = -0.016 * k * (1 - tt) ** 1.25 - 0.005 * k * math.exp(-((tt - 0.06) / 0.07) ** 2)
        mid = 0.5 * (top + bot) + 0.006 * k * tt * tt
        half = 0.5 * (top - bot)
        tau = 0.0042 * (1 - tt) ** 0.7 + 0.0007
        cup = 0.0040 * k * (1 - tt) ** 0.8
        C = R0 + u * (t * L)
        ring = []
        for j in range(12):
            ph = TAU * j / 12
            c, s = math.cos(ph), math.sin(ph)
            ring.append(C + up * (mid + half * c) + w * (tau * s + cup * c * c + 0.0018 * (1 - tt) * max(0.0, c) ** 8))
        rings.append(ring)
    return loft(rings, True, True, True, None, R0 + u * L + up * (0.006 * k))


def build_ears(coll, M):
    v, f = ear_geo()
    obs = [make_object("Ear.L", v, f, [M['skin']], coll)]
    v, f = mirror_geo(v, f)
    obs.append(make_object("Ear.R", v, f, [M['skin']], coll))
    return obs


def build_neck(coll, M):
    rings = []
    for z in np.linspace(1.195, 1.305, 8):
        y = lerp(0.012, 0.004, (z - 1.195) / 0.11)
        rings.append([V((x, yy, z)) for x, yy in
                      (se_xy(TAU * k / 32, 0.0305, y - 0.031, y + 0.034, y) for k in range(32))])
    v, f = loft(rings, True)
    return make_object("Neck", v, f, [M['skin']], coll)


def build_torso(coll, M):
    rings = [[section_point(TORSO, z, TAU * k / 64) for k in range(64)] for z in np.linspace(0.735, 1.236, 42)]
    v, f = loft(rings, True, True, False)
    return make_object("Blouse_Torso", v, f, [M['blouse']], coll)


def build_collar(coll, M):
    rings = []
    for z, w, extra in ((1.218, 0.0365, 0.0), (1.231, 0.0368, 0.0), (1.244, 0.0375, 0.0008), (1.256, 0.0390, 0.002)):
        y = 0.009
        rings.append([V((x, yy, z)) for x, yy in
                      (se_xy(TAU * k / 48, w, y - w - extra, y + 0.039 + extra, y) for k in range(48))])
    v, f = loft(rings, True)
    ob = make_object("Collar", v, f, [M['blouse']], coll, subsurf=None)
    add_solidify(ob, 0.0022, -1.0)
    add_subsurf(ob, 1, 2)
    return ob


def build_arms(coll, M):
    obs = []
    rad = Pchip([0, .08, .22, .42, .53, .75, 1.0], [.041, .0445, .0465, .041, .0365, .033, .0295])
    for side, tag in ((1, "L"), (-1, "R")):
        S, E, W, d1, d2, d3 = arm_geometry(side)
        pts, _ = resample(catmull_rom([S - d1 * 0.03, S, S + d1 * 0.11, E, E + d2 * 0.10, W + d2 * 0.004], 8), 30)
        frames = path_frames(pts, lambda i, p: (side, 0, 0))
        rings = []
        for i, (P, (T, N, B)) in enumerate(zip(pts, frames)):
            r = float(rad(i / 29)[0])
            rings.append(tube_ring(P, N, B, r, r, r, 24))
        v, f = loft(rings, True)
        obs.append(make_object(f"Sleeve.{tag}", v, f, [M['blouse']], coll))
        # bell cuff with a green edge band
        pts, _ = resample(catmull_rom([W - d2 * 0.022, W - d2 * 0.006, W + d3 * 0.012, W + d3 * 0.026], 6), 8)
        crad = Pchip([0, 0.3, 0.7, 1.0], [0.0318, 0.0336, 0.0388, 0.0428])
        frames = path_frames(pts, lambda i, p: (side, 0, 0))
        rings = []
        for i, (P, (T, N, B)) in enumerate(zip(pts, frames)):
            r = float(crad(i / 7)[0])
            rings.append(tube_ring(P, N, B, r, r, r, 24))
        v, f = loft(rings, True)
        mats = [0] * (24 * 5) + [1] * (24 * 2)
        ob = make_object(f"Cuff.{tag}", v, f, [M['blouse'], M['trim']], coll, mat_indices=mats, subsurf=None)
        add_solidify(ob, 0.002, -1.0)
        add_subsurf(ob, 1, 2)
        obs.append(ob)
    return obs


def hand_builder():
    S, E, W, d1, d2, d3 = arm_geometry(1)
    L = d3
    P = V((-1.0, 0.35, 0.0))
    P = (P - L * P.dot(L)).normalized()
    TH = P.cross(L).normalized()

    def to_w(l, th, p):
        return W + L * l + TH * th + P * p

    mb = MeshBuilder()
    prof = Pchip([-0.012, 0.0, 0.03, 0.06, 0.074],
                 [[0.0215, 0.0100, 0.0105], [0.0235, 0.0105, 0.0112], [0.0285, 0.0102, 0.0118],
                  [0.0325, 0.0095, 0.0108], [0.0318, 0.0088, 0.0095]])
    rings = []
    for l in np.linspace(-0.012, 0.074, 12):
        hw, back, palm = prof(l)
        ring = []
        for k in range(16):
            ph = TAU * k / 16
            c, s = math.cos(ph), math.sin(ph)
            ring.append(to_w(l, hw * spow(c, 2 / 2.6), (palm if s >= 0 else back) * spow(s, 2 / 2.6)))
        rings.append(ring)
    mb.add(*loft(rings, True, True, True, to_w(-0.014, 0, 0), to_w(0.079, 0, 0)))

    fingers = [
        (0.0215, 0.069, (0.025, 0.016, 0.014), 0.0076, 5, (10, 20, 12)),
        (0.0072, 0.073, (0.028, 0.018, 0.015), 0.0080, 1, (12, 22, 14)),
        (-0.0072, 0.071, (0.026, 0.017, 0.014), 0.0076, -3, (14, 24, 15)),
        (-0.0205, 0.065, (0.020, 0.013, 0.012), 0.0067, -8, (16, 26, 16)),
    ]
    for th, lr, lens, r0, spread, curls in fingers:
        d = Matrix.Rotation(R(spread), 3, P) @ L
        J = to_w(lr, th, 0.0)
        joints = [to_w(lr - 0.014, th, 0.0), J]
        for seg, curl in zip(lens, curls):
            axis = d.cross(P).normalized()
            d = (Matrix.Rotation(R(curl), 3, axis) @ d).normalized()
            J = J + d * seg
            joints.append(J)
        pts, _ = resample(catmull_rom(joints, 6), 14)
        mb.add(*rounded_tube(pts, lambda t, r0=r0: r0 * (1.0 - 0.18 * t), 10, lambda i, p: P, flat=0.86))
    # thumb
    d = (L * 0.50 + TH * 0.62 + P * 0.45).normalized()
    J = to_w(0.004, 0.017, 0.003)
    joints = [J - d * 0.006, J]
    for seg, curl in zip((0.030, 0.021, 0.017), (6, 12, 14)):
        axis = d.cross(P).normalized()
        d = (Matrix.Rotation(R(curl), 3, axis) @ d).normalized()
        J = J + d * seg
        joints.append(J)
    pts, _ = resample(catmull_rom(joints, 6), 14)
    mb.add(*rounded_tube(pts, lambda t: 0.0108 - 0.0024 * t, 10, lambda i, p: P, flat=0.9))
    return mb


def build_hands(coll, M):
    mb = hand_builder()
    return [from_builder("Hand.L", mb, [M['skin']], coll), from_builder("Hand.R", mb.mirrored(), [M['skin']], coll)]


def leg_ring(z, grow=0.0, n=32, side=1):
    cx, cy = LEG_CENTER(z)
    w, fr, br = LEG_RAD(z)
    pts = []
    for k in range(n):
        ph = TAU * k / n
        c, s = math.cos(ph), math.sin(ph)
        x = (w + grow) * c
        y = (br + grow) * s if s >= 0 else (fr + grow) * s
        pts.append(V((side * cx + x, cy + y, z)))
    return pts


def build_legs(coll, M):
    obs = []
    for side, tag in ((1, "L"), (-1, "R")):
        rings = [leg_ring(z, side=side) for z in np.linspace(0.09, 0.78, 34)]
        v, f = loft(rings, True)
        obs.append(make_object(f"Leggings.{tag}", v, f, [M['leggings']], coll))
    return obs


def foot_geo(side=1):
    rows = [  # y offset from ankle, half width, bottom z, top z
        (0.040, 0.020, 0.032, 0.070), (0.030, 0.027, 0.028, 0.098), (0.010, 0.031, 0.026, 0.110),
        (-0.020, 0.033, 0.022, 0.104), (-0.055, 0.036, 0.017, 0.085), (-0.090, 0.038, 0.013, 0.066),
        (-0.120, 0.037, 0.012, 0.055), (-0.145, 0.032, 0.012, 0.048), (-0.162, 0.024, 0.013, 0.042),
        (-0.172, 0.012, 0.016, 0.036)]
    ax, ay = LEG_CENTER(0.09)
    rot = Matrix.Rotation(R(7 * side), 3, 'Z')
    A = V((ax * side, ay, 0.0))

    def place(p):
        return A + rot @ (p - A)

    rings = []
    for y, hw, zb, zt in rows:
        zc, hh = (zb + zt) / 2, (zt - zb) / 2
        ring = []
        for k in range(20):
            ph = TAU * k / 20
            c, s = math.cos(ph), math.sin(ph)
            e = 2 / 2.2 if s >= 0 else 2 / 4.0
            ring.append(place(V((A.x + hw * spow(c, e), ay + y, zc + hh * spow(s, e)))))
        rings.append(ring)
    foot = loft(rings, True, True, True, place(V((A.x, ay + 0.047, 0.050))), place(V((A.x, ay - 0.176, 0.026))))
    # sole + heel block in one piece
    srows = [(0.046, 0.022, 0.0, 0.034), (0.030, 0.0295, 0.0, 0.030), (0.004, 0.032, 0.0, 0.028),
             (-0.020, 0.033, 0.009, 0.024), (-0.055, 0.0385, 0.003, 0.019), (-0.090, 0.0405, 0.0, 0.015),
             (-0.120, 0.0395, 0.0, 0.014), (-0.145, 0.0345, 0.0, 0.014), (-0.164, 0.026, 0.0, 0.015),
             (-0.177, 0.012, 0.002, 0.017)]
    rings = []
    for y, hw, zb, zt in srows:
        zc, hh = (zb + zt) / 2, (zt - zb) / 2
        ring = []
        for k in range(20):
            ph = TAU * k / 20
            c, s = math.cos(ph), math.sin(ph)
            ring.append(place(V((A.x + hw * spow(c, 0.5), ay + y, zc + hh * spow(s, 0.5)))))
        rings.append(ring)
    sole = loft(rings, True, True, True, place(V((A.x, ay + 0.050, 0.017))), place(V((A.x, ay - 0.181, 0.009))))
    return foot, sole


def build_boots(coll, M):
    obs = []
    for side, tag in ((1, "L"), (-1, "R")):
        mb = MeshBuilder()
        rings = [leg_ring(z, 0.0075 + 0.003 * smoothstep(0.30, 0.40, z), 32, side) for z in np.linspace(0.07, 0.405, 22)]
        mb.add(*loft(rings, True))
        foot, sole = foot_geo(side)
        mb.add(*foot)
        obs.append(from_builder(f"Boot.{tag}", mb, [M['boots']], coll))
        obs.append(make_object(f"Boot_Sole.{tag}", *sole, [M['sole']], coll, subsurf=(1, 1)))
        # fold-over cuff
        rings = []
        for z, g in ((0.322, 0.0115), (0.330, 0.0155), (0.36, 0.0175), (0.39, 0.0195), (0.413, 0.0215)):
            ring = leg_ring(z, g, 32, side)
            rings.append([p + V((0, 0, 0.004 * math.sin(3 * TAU * k / 32))) for k, p in enumerate(ring)])
        v, f = loft(rings, True)
        ob = make_object(f"Boot_Cuff.{tag}", v, f, [M['boot_cuff']], coll, subsurf=None)
        add_solidify(ob, 0.003, -1.0)
        add_subsurf(ob, 1, 2)
        obs.append(ob)
        # straps with buckles
        mb = MeshBuilder()
        bk = MeshBuilder()
        for zc in (0.165, 0.245):
            rings = [leg_ring(zc - 0.0065, 0.0080, 32, side), leg_ring(zc - 0.0065, 0.0112, 32, side),
                     leg_ring(zc + 0.0065, 0.0112, 32, side), leg_ring(zc + 0.0065, 0.0080, 32, side)]
            v, f = loft(rings + [rings[0]], True)
            mb.add(v, f)
            ph = R(-25) if side > 0 else R(180 + 25)
            cx, cy = LEG_CENTER(zc)
            w, fr, br = LEG_RAD(zc)
            nrm = V((math.cos(ph), math.sin(ph), 0.0))
            cen = V((side * cx, cy, zc)) + V((nrm.x * (w + 0.0135), nrm.y * (fr + 0.0135), 0))
            tang = V((0, 0, 1)).cross(nrm)
            frame = [cen + tang * (0.0085 * spow(math.cos(TAU * k / 16), 0.5)) +
                     V((0, 0, 0.0075 * spow(math.sin(TAU * k / 16), 0.5))) for k in range(16)]
            bk.add(*loop_tube(frame, 0.0014, 6))
        obs.append(from_builder(f"Boot_Straps.{tag}", mb, [M['strap']], coll, subsurf=(1, 1)))
        obs.append(from_builder(f"Boot_Buckles.{tag}", bk, [M['bronze']], coll, subsurf=(0, 1)))
    return obs


# ----------------------------------------------------------------------------- outfit
def build_skirt(coll, M):
    zs = [0.505, 0.513, 0.522, 0.531, 0.537, 0.543] + list(np.linspace(0.555, 0.925, 31))
    n = 128
    rings = []
    for z in zs:
        amp = skirt_amp(z)
        wave = smoothstep(0.62, 0.505, z)
        ring = []
        for k in range(n):
            ph = TAU * k / n
            p = section_point(SKIRT, z, ph)
            ym = SKIRT.section(z)[3]
            radial = V((p.x, p.y - ym, 0)).normalized()
            fold = skirt_fold(ph)
            p += radial * (amp * fold)
            p.z += wave * 0.0065 * fold
            ring.append(p)
        rings.append(ring)
    v, f = loft(rings, True)
    mats = []
    for i in range(len(zs) - 1):
        green = zs[i] < 0.5305 or (0.536 < zs[i] < 0.5425)
        mats.extend([1 if green else 0] * n)
    ob = make_object("Skirt", v, f, [M['blouse'], M['trim']], coll, mat_indices=mats, subsurf=None, recalc=False)
    add_solidify(ob, 0.0035, -1.0)
    add_subsurf(ob, 1, 2)
    return ob


def corset_point(phi, t):
    zb = 0.868 - 0.034 * max(0.0, -math.sin(phi)) ** 6
    zt = 1.044 + 0.014 * max(0.0, math.sin(phi)) ** 2
    return section_point(CORSET, lerp(zb, zt, t), phi)


def front_point(body, z, x, offset=0.0):
    """Point on the front of a profile body at height z with the given x."""
    lo, hi = -math.pi / 2, -math.pi / 2 + (math.pi / 2 if x > 0 else -math.pi / 2)
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if abs(section_point(body, z, mid, offset).x) < abs(x):
            lo = mid
        else:
            hi = mid
    return section_point(body, z, 0.5 * (lo + hi), offset)


def build_corset(coll, M):
    obs = []
    n, rows = 96, 14
    rings = [[corset_point(TAU * k / n, i / (rows - 1)) for k in range(n)] for i in range(rows)]
    v, f = loft(rings, True)
    ob = make_object("Corset", v, f, [M['corset']], coll, subsurf=None, recalc=False)
    add_solidify(ob, 0.003, -1.0)
    add_subsurf(ob, 1, 2)
    obs.append(ob)
    # piping along both edges
    mb = MeshBuilder()
    for t in (0.0, 1.0):
        pts = []
        for k in range(n):
            ph = TAU * k / n
            p = corset_point(ph, t)
            ym = CORSET.section(p.z)[3]
            pts.append(p + V((p.x, p.y - ym, 0)).normalized() * 0.0012)
        mb.add(*loop_tube(pts, 0.0022, 8))
    obs.append(from_builder("Corset_Piping", mb, [M['piping']], coll, subsurf=(1, 1)))
    # lacing: eyelets, crossed laces and a small bow
    eyes = MeshBuilder()
    lace = MeshBuilder()
    zs = np.linspace(0.874, 1.022, 6)
    left = [front_point(CORSET, z, 0.0115, 0.0035) for z in zs]
    right = [front_point(CORSET, z, -0.0115, 0.0035) for z in zs]
    for p in left + right:
        eyes.add(*ellipsoid(p, (0.0024, 0.0024, 0.0024), nu=8, nv=6))
    for k in range(5):
        for a, b, lift in ((left[k], right[k + 1], 0.0018), (right[k], left[k + 1], 0.0008)):
            mid = (a + b) * 0.5 + V((0, -1, 0)) * lift
            pts, _ = resample(catmull_rom([a, mid, b], 6), 10)
            lace.add(*rounded_tube(pts, lambda t: 0.0014, 6))
    knot = front_point(CORSET, 1.030, 0.0, 0.006)
    lace.add(*ellipsoid(knot, (0.0032, 0.0028, 0.0030), nu=8, nv=6))
    for s in (1, -1):
        loop = [knot + V((s * 0.003, -0.001, 0.001)), knot + V((s * 0.011, -0.003, 0.009)),
                knot + V((s * 0.018, -0.002, 0.006)), knot + V((s * 0.012, -0.002, -0.001)),
                knot + V((s * 0.004, -0.001, -0.001))]
        pts, _ = resample(catmull_rom(loop, 6), 18)
        lace.add(*rounded_tube(pts, lambda t: 0.0017, 6))
        tail = [knot, knot + V((s * 0.004, -0.004, -0.015)), knot + V((s * 0.006, -0.003, -0.032)),
                knot + V((s * 0.005, -0.002, -0.044))]
        pts, _ = resample(catmull_rom(tail, 6), 14)
        lace.add(*rounded_tube(pts, lambda t: 0.0016, 6))
    obs.append(from_builder("Corset_Eyelets", eyes, [M['bronze']], coll, subsurf=(0, 1)))
    obs.append(from_builder("Corset_Laces", lace, [M['lace']], coll, subsurf=(0, 1)))
    return obs


def belt_section_point(phi, z, off):
    p = section_point(SKIRT, z, phi)
    ym = SKIRT.section(z)[3]
    return p + V((p.x, p.y - ym, 0)).normalized() * (skirt_amp(z) + off)


def build_belt(coll, M):
    obs = []
    n = 96
    rings = []
    for dz in (-0.011, 0.0, 0.011):
        rings.append([belt_section_point(TAU * k / n, belt_z(TAU * k / n) + dz, 0.0016) for k in range(n)])
    v, f = loft(rings, True)
    ob = make_object("Belt", v, f, [M['belt']], coll, subsurf=None, recalc=False)
    orient_outward(ob, lambda c: V((0, 0.005, c.z)))
    add_solidify(ob, 0.004, 1.0)
    add_subsurf(ob, 1, 2)
    obs.append(ob)

    def belt_frame(phi):
        z = belt_z(phi)
        p = belt_section_point(phi, z, 0.0056)
        p2 = belt_section_point(phi + 0.01, belt_z(phi + 0.01), 0.0056)
        tang = (p2 - p).normalized()
        nrm = tang.cross(V((0, 0, 1))).normalized()
        if nrm.dot(V((p.x, p.y, 0))) < 0:
            nrm = -nrm
        return p, tang, nrm

    # buckle
    p, tang, nrm = belt_frame(R(-68))
    up = nrm.cross(tang).normalized()
    if up.z < 0:
        up = -up
    frame = [p + nrm * 0.0025 + tang * (0.0135 * spow(math.cos(TAU * k / 20), 0.5))
             + up * (0.0130 * spow(math.sin(TAU * k / 20), 0.5)) for k in range(20)]
    mb = MeshBuilder()
    mb.add(*loop_tube(frame, 0.0022, 8))
    pts, _ = resample([p + nrm * 0.0028 + up * 0.012, p + nrm * 0.0042 - up * 0.004], 6)
    mb.add(*rounded_tube(pts, lambda t: 0.0012, 6))
    obs.append(from_builder("Belt_Buckle", mb, [M['bronze']], coll, subsurf=(1, 1)))

    # pouch on the right-back hip
    p, tang, nrm = belt_frame(R(150))
    mb, flap, btn = MeshBuilder(), MeshBuilder(), MeshBuilder()
    top = p + nrm * 0.0185 + V((0, 0, -0.004))
    rings = []
    for i, h in enumerate(np.linspace(0, 0.064, 10)):
        shrink = 1.0 - 0.35 * smoothstep(0.050, 0.064, h)
        ring = []
        for k in range(20):
            ph = TAU * k / 20
            c, s = math.cos(ph), math.sin(ph)
            ring.append(top + tang * (0.027 * shrink * spow(c, 0.5)) + nrm * (0.0145 * shrink * spow(s, 0.5))
                        + V((0, 0, -h)))
        rings.append(ring)
    mb.add(*loft(rings, True, True, True, top, top + V((0, 0, -0.066))))
    rings = []
    for h in np.linspace(-0.002, 0.030, 8):
        wfac = 1.0 if h < 0.018 else math.sqrt(max(0.0, 1 - ((h - 0.018) / 0.013) ** 2))
        ring = []
        for k in range(16):
            ph = TAU * k / 16
            c, s = math.cos(ph), math.sin(ph)
            ring.append(top + nrm * (0.0158 + 0.0018 * s) + tang * (0.0285 * max(wfac, 0.05) * spow(c, 0.6))
                        + V((0, 0, -h)) + nrm * (0.0016 * (1 - c * c)))
        rings.append(ring)
    flap.add(*loft(rings, True, True, True))
    btn.add(*ellipsoid(top + nrm * 0.0195 + V((0, 0, -0.024)), (0.0038, 0.0038, 0.0038), nu=10, nv=6))
    obs.append(from_builder("Pouch", mb, [M['pouch']], coll, subsurf=(1, 2)))
    obs.append(from_builder("Pouch_Flap", flap, [M['belt']], coll, subsurf=(1, 2)))
    obs.append(from_builder("Pouch_Button", btn, [M['bronze']], coll, subsurf=(0, 1)))

    # potion vial on the left front hip
    p, tang, nrm = belt_frame(R(-30))
    axis = (V((0, 0, 1)) + nrm * 0.12).normalized()
    base = p + nrm * 0.022 + V((0, 0, -0.062))
    prof = [(0.0, 0.0), (0.002, 0.010), (0.006, 0.0145), (0.016, 0.0165), (0.026, 0.0155), (0.032, 0.011),
            (0.036, 0.0065), (0.044, 0.0060), (0.046, 0.0075), (0.049, 0.0072)]
    ref = tang
    b2 = axis.cross(ref).normalized()
    ref = b2.cross(axis).normalized()
    glass, potion, cork, strap = MeshBuilder(), MeshBuilder(), MeshBuilder(), MeshBuilder()
    rings_g, rings_p = [], []
    for h, r in prof[1:]:
        ring = [base + axis * h + ref * (r * math.cos(TAU * k / 16)) + b2 * (r * math.sin(TAU * k / 16)) for k in range(16)]
        (rings_p if h <= 0.026 else rings_g).append(ring)
    rings_g.insert(0, rings_p[-1])
    potion.add(*loft(rings_p, True, True, False, base, None))
    glass.add(*loft(rings_g, True, False, False))
    rings = [[base + axis * h + ref * (0.0058 * math.cos(TAU * k / 12)) + b2 * (0.0058 * math.sin(TAU * k / 12))
              for k in range(12)] for h in (0.045, 0.056)]
    cork.add(*loft(rings, True, True, True, base + axis * 0.045, base + axis * 0.0585))
    strap.add(*torus_geo(base + axis * 0.040, axis, 0.0072, 0.0012, 20, 6))
    pts, _ = resample([base + axis * 0.040 + nrm * 0.004, p + nrm * 0.006 + V((0, 0, -0.004))], 6)
    strap.add(*rounded_tube(pts, lambda t: 0.0016, 6))
    obs.append(from_builder("Vial_Potion", potion, [M['potion']], coll, subsurf=(1, 1)))
    obs.append(from_builder("Vial_Glass", glass, [M['glass']], coll, subsurf=(1, 1)))
    obs.append(from_builder("Vial_Cork", cork, [M['cork']], coll, subsurf=(1, 1)))
    obs.append(from_builder("Vial_Strap", strap, [M['belt']], coll, subsurf=(0, 1)))
    return obs


def body_colliders(arms=True, legs=True, skirt=True, cape=False):
    cols = [TORSO, CORSET, Capsule((0, 0.012, 1.19), (0, 0.004, 1.30), 0.034),
            Capsule((0, 0.009, 1.215), (0, 0.009, 1.255), 0.041)]
    if skirt:
        cols.append(SKIRT)
    if arms:
        for side in (1, -1):
            S, E, W, d1, d2, d3 = arm_geometry(side)
            cols += [Capsule(S, E, 0.046), Capsule(E, W, 0.037), Capsule(W, W + d3 * 0.03, 0.044),
                     Capsule(W + d3 * 0.03, W + d3 * 0.12, 0.030)]
    if legs:
        for side in (1, -1):
            cols.append(Capsule((side * 0.072, 0, 0.75), (side * 0.069, 0.01, 0.10), 0.055))
    if cape:
        cols.append(CAPE_BODY)
    return cols


def cape_point(z0, phi):
    Rx, yb, ys, yf, p, Phi, drop, A = (float(x) for x in CAPE(z0))
    s, c = math.sin(phi), math.cos(phi)
    e = 2.0 / p
    x = Rx * spow(s, e)
    y = ys + ((yb - ys) if c >= 0 else (yf - ys)) * abs(c) ** e
    z = z0 - drop * s * s
    if A > 0:
        radial = V((x, y - ys, 0.0)).normalized()
        d = A * (math.sin(10 * phi + 0.4) + 0.3 * math.sin(23 * phi + 1.3))
        x += radial.x * d
        y += radial.y * d
    z += 0.010 * math.sin(10 * phi + 0.4) * smoothstep(0.50, 0.34, z0)
    return V((x, y, z))


def cape_grid():
    z_rows = list(np.linspace(1.248, 1.164, 12)) + list(np.linspace(1.164, 0.34, 39))[1:]
    cols = 72
    grid = []
    for z0 in z_rows:
        Phi = R(float(CAPE(z0)[5]))
        grid.append([cape_point(z0, Phi * (2 * j / (cols - 1) - 1)) for j in range(cols)])
    colliders = body_colliders()
    pouch_c = None
    p = belt_section_point(R(150), belt_z(R(150)), 0.0)
    pouch_c = Ellipsoid(p + V((p.x, p.y, 0)).normalized() * 0.018 + V((0, 0, -0.035)), (0.04, 0.04, 0.05))
    colliders.append(pouch_c)
    for it in range(4):
        for i, row in enumerate(grid):
            for j, q in enumerate(row):
                for c in colliders:
                    q = c.push(q, 0.009)
                row[j] = q
        if it < 3:
            new = [[q.copy() for q in row] for row in grid]
            for i in range(1, len(grid) - 1):
                for j in range(1, cols - 1):
                    avg = (grid[i - 1][j] + grid[i + 1][j] + grid[i][j - 1] + grid[i][j + 1]) * 0.25
                    new[i][j] = grid[i][j].lerp(avg, 0.5)
            grid = new
    return grid


def build_cape(coll, M):
    grid = cape_grid()
    rows, cols = len(grid), len(grid[0])
    verts = [q for row in grid for q in row]
    ob = make_object("Cape", verts, grid_faces(rows, cols), [M['cape'], M['lining']], coll, subsurf=None, recalc=False)
    orient_outward(ob, lambda c: V((0, 0.03, c.z)))
    add_solidify(ob, 0.004, -1.0, material_offset=1)
    add_subsurf(ob, 1, 2)
    return ob, grid


def hood_roll_path():
    pts, radii = [], []
    for k in range(25):
        ph = R(-110 + 220 * k / 24)
        s, c = math.sin(ph), math.cos(ph)
        e = 2 / 2.2
        x = 0.080 * spow(s, e)
        y = 0.012 + ((0.066 - 0.012) if c >= 0 else (-0.034 - 0.012)) * abs(c) ** e
        z = 1.256 - 0.020 * s * s
        pts.append(V((x, y, z)))
        a = abs(math.degrees(ph))
        radii.append(0.010 + 0.013 * max(0.0, math.cos(ph)) ** 2 if a <= 90 else 0.010 * max(0.25, 1 - (a - 90) / 26))
    return pts, radii


def build_hood(coll, M):
    pts, radii = hood_roll_path()
    cols = body_colliders(arms=False, legs=False, skirt=False)
    pts = [push_points([p], cols, r + 0.003)[0] for p, r in zip(pts, radii)]
    pts = smooth_path(pts, 2)
    rfn = Pchip(np.linspace(0, 1, len(radii)), radii)
    dense, _ = resample(catmull_rom(pts, 6), 60)
    frames = path_frames(dense, lambda i, p: (p.x, p.y - 0.012, 0.0))
    rings = []
    for i, (P, (T, N, B)) in enumerate(zip(dense, frames)):
        r = float(rfn(i / 59)[0])
        rings.append(tube_ring(P, N, B, r, r * 0.8, r * 0.8, 14))
    v, f = loft(rings, True, True, True)
    roll = make_object("Hood_Roll", v, f, [M['cape']], coll)
    # hood body lying on the back, tapering to a soft point
    zs = np.linspace(1.238, 1.0, 16)
    centers = []
    for z in zs:
        Rx, yb, ys, yf, p, Phi, drop, A = (float(x) for x in CAPE(z))
        centers.append(V((0.0, yb + 0.006 + A * 0.4, z)))
    wfn = Pchip([0, 0.15, 0.45, 0.75, 0.92, 1.0], [0.072, 0.080, 0.068, 0.042, 0.018, 0.004])
    hfn = Pchip([0, 0.15, 0.45, 0.75, 1.0], [0.015, 0.018, 0.016, 0.011, 0.003])
    rings = []
    for i, P in enumerate(centers):
        t = i / (len(centers) - 1)
        w, h = float(wfn(t)[0]), float(hfn(t)[0])
        ring = []
        for k in range(20):
            ph = TAU * k / 20
            c, s = math.cos(ph), math.sin(ph)
            yy = h * s if s >= 0 else 0.35 * h * s
            ring.append(P + V((w * spow(c, 0.85), yy + h * 0.9 + 0.012 * (1 - c * c) * (1 - t), 0.0)))
        rings.append(ring)
    v, f = loft(rings, True, True, True, None, centers[-1] + V((0, 0.004, -0.012)))
    body = make_object("Hood", v, f, [M['cape'], M['lining']], coll)
    return [roll, body]


def build_brooches(coll, M, grid):
    obs = []
    rows, cols = len(grid), len(grid[0])
    zr = [row[cols // 2].z for row in grid]
    i = min(range(rows), key=lambda k: abs(zr[k] - 1.212))
    leaf, gem = MeshBuilder(), MeshBuilder()
    gems = []
    for side in (1, -1):
        j = cols - 4 if side > 0 else 3
        du, dv, nrm = surface_frame(grid, i, j)
        if nrm.dot(V((side, -0.6, 0.6))) < 0:
            nrm = -nrm
        base = grid[i][j] + nrm * 0.004
        axis = V((-side * 0.75, -0.35, -0.55))
        axis = (axis - nrm * axis.dot(nrm)).normalized()
        leaf.add(*leaf_geo(base - axis * 0.006, axis, nrm, 0.036, 0.0115, 0.0018, bend=0.002))
        side_axis = axis.cross(nrm).normalized()
        leaf.add(*leaf_geo(base + axis * 0.004, (side_axis * side * 0.8 + axis * 0.6).normalized(), nrm,
                           0.022, 0.0075, 0.0015, bend=0.001))
        g = base + nrm * 0.0035
        gem.add(*ellipsoid(g, (0.0050, 0.0050, 0.0034), basis_matrix(nrm), nu=12, nv=8))
        gems.append(g)
    obs.append(from_builder("Brooch_Leaves", leaf, [M['bronze']], coll, subsurf=(1, 1)))
    # chain across the chest with a teardrop pendant
    a, b = gems
    mid = front_point(TORSO, 1.126, 0.0, 0.006)
    ctrl = 2 * mid - (a + b) * 0.5
    pts = [a * (1 - t) ** 2 + ctrl * 2 * t * (1 - t) + b * t * t for t in np.linspace(0, 1, 50)]
    pts = push_points(pts, body_colliders(arms=False, legs=False, skirt=False), 0.0045)
    pts = smooth_path(pts, 3)
    chain = MeshBuilder()
    chain.add(*rounded_tube(pts, lambda t: 0.0013, 6))
    low = min(pts, key=lambda p: p.z)
    chain.add(*ellipsoid(low + V((0, -0.002, -0.003)), (0.0026, 0.0026, 0.0026), nu=8, nv=6))
    obs.append(from_builder("Chain", chain, [M['bronze']], coll, subsurf=(0, 1)))
    gem.add(*ellipsoid(low + V((0, -0.003, -0.011)), (0.0042, 0.0034, 0.0068), nu=12, nv=8))
    obs.append(from_builder("Gems", gem, [M['amber']], coll, subsurf=(1, 1)))
    return obs


def basis_matrix(z_axis):
    z = V(z_axis).normalized()
    x = z.orthogonal().normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


# ----------------------------------------------------------------------------- hair
def hair_ref(i, p):
    c = V((0.0, 0.008, 1.385))
    if p.z > 1.385:
        return (p - c).normalized()
    v = V((p.x, p.y - 0.008, 0.0))
    return v.normalized() if v.length > 1e-6 else V((0, 1, 0))


def clump_geo(path, width, thick, n=10, taper_start=0.4, tip_pow=1.4, curve=0.45, root=0.75):
    frames = path_frames(path, hair_ref)
    m = len(path)
    rings = []
    for i, (P, (T, N, B)) in enumerate(zip(path, frames)):
        t = i / (m - 1)
        if t > 0.985:
            break
        if t < 0.12:
            s = lerp(root, 1.0, smoothstep(0.0, 0.12, t))
        elif t < taper_start:
            s = 1.0
        else:
            s = ((1 - t) / (1 - taper_start)) ** tip_pow
        s = max(s, 0.04)
        w, h = width * s, thick * max(s, 0.2) ** 0.6
        ring = []
        for k in range(n):
            ph = TAU * k / n
            c, sn = math.cos(ph), math.sin(ph)
            ring.append(P + B * (w * c) + N * (h * sn - curve * h * c * c))
        rings.append(ring)
    return loft(rings, True, True, True, None, path[-1])


def skull_path(z0, phi0, z1, phi1, off0, off1, n=10, phi_pow=1.0, z_pow=1.0):
    pts = []
    for i in range(n):
        s = i / (n - 1)
        pts.append(scalp(lerp(z0, z1, s ** z_pow), lerp(phi0, phi1, s ** phi_pow), lerp(off0, off1, s)))
    return pts


def fall_path(start, z_end, flare=0.010, flick=0.012, inward=0.0, forward=0.0, n=10):
    rad = V((start.x, start.y - 0.008, 0.0)).normalized()
    pts = []
    for i in range(1, n + 1):
        s = i / n
        z = lerp(start.z, z_end, s)
        h = flare * s ** 1.5 + flick * smoothstep(0.65, 1.0, s) ** 1.5 - inward * s * s
        pts.append(V((start.x, start.y, z)) + rad * h + V((0, -forward * s * s, 0.004 * smoothstep(0.8, 1.0, s) * (flick > 0))))
    return pts


def finish_path(ctrl, colliders, margin, n=26, smooth=2):
    pts, _ = resample(catmull_rom(ctrl, 6), n)
    for _ in range(2):
        pts = push_points(pts, colliders, margin, 2)
        pts = smooth_path(pts, smooth)
    return push_points(pts, colliders, margin, 2)


def hair_colliders():
    cols = [HEAD, CAPE_BODY] + body_colliders(arms=False, legs=False, skirt=False)
    pts, radii = hood_roll_path()
    for a, b, r in zip(pts[:-1], pts[1:], radii):
        cols.append(Capsule(a, b, r + 0.004))
    return cols


def build_hair(coll, M):
    mb = MeshBuilder()
    cols = hair_colliders()
    head_only = [HEAD]

    # scalp cap
    hl = Pchip([-90, -60, -35, -15, 0, 20, 45, 90], [1.448, 1.430, 1.395, 1.372, 1.366, 1.345, 1.312, 1.292])
    rings = []
    for i in range(14):
        t = (i + 1) / 14
        ring = []
        for k in range(64):
            ph = TAU * k / 64
            ang = math.degrees(math.atan2(math.sin(ph), abs(math.cos(ph))))
            z = lerp(1.4985, float(hl(ang)[0]), t ** 0.95)
            ring.append(scalp(z, ph, lerp(0.0062, 0.0030, t ** 2)))
        rings.append(ring)
    cap_v, cap_f = loft(rings, True, True, False, V((0, 0.010, 1.5066)), None)
    cap = make_object("Hair_Cap", cap_v, cap_f, [M['hair']], coll, recalc=True)
    orient_outward(cap, lambda c: V((0, 0.006, 1.39)))

    # bangs, swept from a part on the character's left
    bangs = [(-58, -46, 1.394, 0.019, 0.0055), (-62, -59, 1.387, 0.024, 0.0065), (-64, -71, 1.384, 0.026, 0.007),
             (-66, -83, 1.379, 0.026, 0.007), (-70, -95, 1.382, 0.027, 0.007), (-74, -107, 1.388, 0.026, 0.007),
             (-80, -119, 1.392, 0.025, 0.0065), (-88, -131, 1.396, 0.024, 0.006), (-96, -142, 1.383, 0.022, 0.006),
             (-50, -34, 1.386, 0.018, 0.0055)]
    for ph0, ph1, z1, w, h in bangs:
        ctrl = skull_path(1.489, R(ph0), z1, R(ph1), 0.011, 0.0058, 9, phi_pow=1.4, z_pow=0.9)
        path = finish_path(ctrl, head_only, h + 0.0015, 24, 1)
        mb.add(*clump_geo(path, w * 0.5, h * 0.5, 10, 0.45, 1.3, 0.5, 0.8))

    # side locks framing the face (mirrored)
    side = MeshBuilder()
    locks = [((1.470, -40), (1.372, -24), 0.0085, 1.272, 0.012, 0.016, 0.026, 0.0065),
             ((1.466, -28), (1.360, -13), 0.0085, 1.292, 0.006, 0.010, 0.022, 0.006),
             ((1.474, -52), (1.392, -36), 0.0080, 1.330, 0.004, 0.006, 0.020, 0.0055)]
    for (z0, p0), (z1, p1), off, zend, inward, fwd, w, h in locks:
        ctrl = skull_path(z0, R(p0), z1, R(p1), 0.010, off, 7)
        ctrl += fall_path(ctrl[-1], zend, 0.004, 0.0, inward, fwd, 6)
        path = finish_path(ctrl, head_only, h * 0.5 + 0.0015, 26)
        side.add(*clump_geo(path, w * 0.5, h * 0.5, 10, 0.35, 1.5, 0.45, 0.8))
    mb.add(side.verts, side.faces)
    ms = side.mirrored()
    mb.add(ms.verts, ms.faces)

    # back hair: under and outer layers falling to the shoulders, tips flicking outward
    for ph in np.linspace(22, 158, 9):
        ctrl = skull_path(1.44, R(ph), 1.322, R(ph), 0.010, 0.016, 7)
        zend = 1.165 - 0.012 * math.sin(R(ph))
        ctrl += fall_path(ctrl[-1], zend, 0.006, 0.010, 0.0, 0.0, 8)
        path = finish_path(ctrl, cols, 0.0075, 26)
        mb.add(*clump_geo(path, 0.016, 0.0042, 10, 0.4, 1.4, 0.45, 0.8))
    for k, ph in enumerate(np.linspace(8, 172, 12)):
        jitter = 0.010 * math.sin(k * 2.3)
        ctrl = skull_path(1.493, R(ph * 0.6 + 36), 1.335, R(ph), 0.012, 0.021, 8, phi_pow=0.8)
        zend = 1.140 + jitter - 0.010 * math.sin(R(ph))
        if ph < 30 or ph > 150:
            zend += 0.03
        ctrl += fall_path(ctrl[-1], zend, 0.010, 0.016, 0.0, 0.0, 9)
        path = finish_path(ctrl, cols, 0.0085, 28)
        mb.add(*clump_geo(path, 0.0175, 0.0048, 10, 0.45, 1.3, 0.5, 0.8))
    # side-top clumps covering the temples and above the ears
    for ph0, ph1, z1 in ((-30, -8, 1.385), (-14, 6, 1.382), (210, 188, 1.385), (194, 174, 1.382)):
        ctrl = skull_path(1.492, R(ph0), z1, R(ph1), 0.011, 0.012, 9)
        path = finish_path(ctrl, head_only, 0.006, 22)
        mb.add(*clump_geo(path, 0.0135, 0.0042, 10, 0.5, 1.3, 0.45, 0.8))
    # ahoge
    ahoge = [V((0.004, 0.012, 1.503)), V((0.010, 0.000, 1.528)), V((0.020, -0.022, 1.538)),
             V((0.028, -0.040, 1.530)), V((0.030, -0.048, 1.519))]
    pts, _ = resample(catmull_rom(ahoge, 6), 20)
    mb.add(*clump_geo(pts, 0.0055, 0.0018, 8, 0.3, 1.2, 0.3, 0.9))
    hair = from_builder("Hair", mb, [M['hair']], coll, subsurf=(1, 2))
    return [cap, hair]


def build_braid(coll, M):
    obs = []
    cols = hair_colliders() + [CORSET]
    ctrl = [scalp(1.338, R(38), 0.012), V((0.098, 0.040, 1.276)), V((0.110, 0.008, 1.242)),
            V((0.106, -0.040, 1.210)), V((0.095, -0.084, 1.150)), V((0.089, -0.101, 1.080)), V((0.087, -0.099, 1.000))]
    path = finish_path(ctrl, cols, 0.011, 60, 3)
    path, total = resample(path, 120)
    frames = path_frames(path, lambda i, p: (p - V((0.0, 0.02, 1.12))))
    mb = MeshBuilder()
    s, step, i_lobe = 0.022, 0.0128, 0
    end = total - 0.012
    while s < end:
        idx = min(int(s / total * 119), 119)
        P, (T, N, B) = path[idx], frames[idx]
        k = s / total
        taper = lerp(1.0, 0.78, k)
        sign = 1 if i_lobe % 2 == 0 else -1
        c = P + B * (0.0042 * sign * taper)
        a = (T + B * (-sign * math.tan(R(32)))).normalized()
        bb = N.cross(a).normalized()
        rot = Matrix((bb, N, a)).transposed()
        mb.add(*ellipsoid(c, (0.0064 * taper, 0.0058 * taper, 0.0128 * taper), rot, 12, 8))
        s += step
        i_lobe += 1
    # root blend clump
    mb.add(*clump_geo(path[:14], 0.010, 0.006, 10, 0.6, 1.0, 0.3, 1.0))
    obs.append(from_builder("Braid", mb, [M['hair']], coll, subsurf=(1, 1)))
    # tie + bow
    idx = 117
    P, (T, N, B) = path[idx], frames[idx]
    tie = MeshBuilder()
    tie.add(*torus_geo(P, T, 0.0072, 0.0026, 20, 8, x_hint=B))
    knot = P + N * 0.006
    tie.add(*ellipsoid(knot, (0.0035, 0.003, 0.0035), nu=10, nv=6))
    for sgn in (1, -1):
        rot = Matrix((B * sgn, N, T)).transposed()
        tie.add(*ellipsoid(knot + B * (sgn * 0.0085) + T * 0.002, (0.0075, 0.0022, 0.0048), rot, 12, 8))
        tail = [knot, knot + B * (sgn * 0.004) + T * 0.010 + N * 0.001, knot + B * (sgn * 0.006) + T * 0.022]
        pts, _ = resample(catmull_rom(tail, 6), 12)
        tie.add(*clump_geo(pts, 0.0034, 0.0010, 8, 0.6, 0.6, 0.2, 1.0))
    obs.append(from_builder("Braid_Ribbon", tie, [M['ribbon']], coll, subsurf=(1, 1)))
    # tuft below the tie
    tuft = MeshBuilder()
    for k in range(6):
        ang = (k - 2.5) / 2.5
        ln = 0.034 + 0.010 * (1 - abs(ang))
        tip = P + T * ln + B * (0.009 * ang) + N * (0.002 * math.sin(k))
        pts, _ = resample(catmull_rom([P - T * 0.004, P + T * 0.010 + B * (0.003 * ang), tip], 6), 14)
        tuft.add(*clump_geo(pts, 0.0048, 0.0026, 8, 0.3, 1.3, 0.3, 1.0))
    obs.append(from_builder("Braid_Tuft", tuft, [M['hair']], coll, subsurf=(1, 2)))
    return obs


# ----------------------------------------------------------------------------- staff
STAFF_BASE = V((-0.50, 0.06, 0.0))


def build_staff(coll, M):
    obs = []
    x0, y0 = STAFF_BASE.x, STAFF_BASE.y

    def center(z):
        return V((x0 + 0.006 * math.sin(z * 7.0), y0 + 0.005 * math.sin(z * 5.0 + 1.0), z))

    def radius(z):
        r = 0.0145 + 0.0012 * math.sin(z * 23.0)
        for zk in (0.42, 0.88):
            r += 0.0032 * math.exp(-((z - zk) / 0.02) ** 2)
        return r + 0.005 * smoothstep(1.20, 1.27, z)

    zs = np.linspace(0.0, 1.27, 72)
    pts = [center(z) for z in zs]
    frames = path_frames(pts, lambda i, p: (1, 0, 0))
    rings = [tube_ring(P, N, B, radius(P.z), radius(P.z), radius(P.z), 12) for P, (T, N, B) in zip(pts, frames)]
    v, f = loft(rings, True, True, True)
    wood = MeshBuilder()
    wood.add(v, f)
    top = center(1.25)
    cz = 1.352
    for k in range(3):
        a0 = TAU * k / 3
        bpts = []
        for s in np.linspace(0, 1, 18):
            ang = a0 + 3.3 * s
            rr = 0.010 + 0.024 * math.sin(math.pi * min(s * 1.05, 1.0)) ** 0.8
            if s > 0.85:
                rr += 0.02 * (s - 0.85)
            bpts.append(V((top.x + rr * math.cos(ang), top.y + rr * math.sin(ang), 1.245 + 0.20 * s)))
        bpts, _ = resample(catmull_rom(bpts, 4), 40)
        wood.add(*rounded_tube(bpts, lambda t: 0.0085 * (1 - t) + 0.0024, 10,
                               lambda i, p: (p.x - top.x, p.y - top.y, 0.0)))
    obs.append(from_builder("Staff_Wood", wood, [M['wood']], coll, subsurf=(1, 2)))
    # crystal (flat-shaded hexagonal bipyramid)
    c = V((top.x, top.y, cz))
    verts = [c + V((0, 0, 0.056))]
    for zz in (0.012, -0.012):
        verts += [c + V((0.021 * math.cos(TAU * k / 6), 0.021 * math.sin(TAU * k / 6), zz)) for k in range(6)]
    verts.append(c + V((0, 0, -0.040)))
    faces = [(0, 1 + k, 1 + (k + 1) % 6) for k in range(6)]
    faces += [(1 + k, 7 + k, 7 + (k + 1) % 6, 1 + (k + 1) % 6) for k in range(6)]
    faces += [(13, 7 + (k + 1) % 6, 7 + k) for k in range(6)]
    obs.append(make_object("Staff_Crystal", verts, faces, [M['crystal']], coll, subsurf=None, smooth=False))
    # leaves sprouting from the cage
    leaves = MeshBuilder()
    for ang, zz, ln in ((0.6, 1.30, 0.045), (2.9, 1.33, 0.038), (4.6, 1.285, 0.032)):
        base = V((top.x + 0.03 * math.cos(ang), top.y + 0.03 * math.sin(ang), zz))
        out = V((math.cos(ang), math.sin(ang), 0.55)).normalized()
        nrm = V((0, 0, 1)).cross(out).cross(out).normalized() * -1
        leaves.add(*leaf_geo(base, out, nrm, ln, ln * 0.32, 0.0016, bend=0.004))
    obs.append(from_builder("Staff_Leaves", leaves, [M['leaf']], coll, subsurf=(1, 1)))
    # leather grip wrap and bronze ferrule
    grip = MeshBuilder()
    hel = []
    for z in np.linspace(0.80, 0.98, 120):
        a = z / 0.012 * TAU
        r = radius(z) + 0.0016
        cc = center(z)
        hel.append(V((cc.x + r * math.cos(a), cc.y + r * math.sin(a), z)))
    grip.add(*rounded_tube(hel, lambda t: 0.0024, 6, lambda i, p: (p.x - x0, p.y - y0, 0)))
    for z in (0.795, 0.985):
        grip.add(*torus_geo(center(z), (0, 0, 1), radius(z) + 0.002, 0.0026, 20, 6))
    obs.append(from_builder("Staff_Grip", grip, [M['belt']], coll, subsurf=(0, 1)))
    rings = [tube_ring(center(z), V((1, 0, 0)), V((0, 1, 0)), r, r, r, 16)
             for z, r in ((0.0, 0.0150), (0.004, 0.0170), (0.032, 0.0172), (0.040, 0.0160))]
    v, f = loft(rings, True, True, True, center(-0.002), center(0.042))
    obs.append(make_object("Staff_Ferrule", v, f, [M['bronze']], coll, subsurf=(1, 1)))
    return obs, c


# ----------------------------------------------------------------------------- assembly
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    return scene


def build(out_dir):
    scene = reset_scene()
    tex_dir = os.path.join(out_dir, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    face_path = face_texture.make_face_texture(os.path.join(tex_dir, "face.png"))
    face_img = bpy.data.images.load(face_path)
    face_img.pack()
    M = make_materials(face_img)

    root = bpy.data.collections.new("ElfMage")
    scene.collection.children.link(root)
    c_body = bpy.data.collections.new("Body")
    c_hair = bpy.data.collections.new("Hair")
    c_outfit = bpy.data.collections.new("Outfit")
    c_acc = bpy.data.collections.new("Accessories")
    for c in (c_body, c_hair, c_outfit, c_acc):
        root.children.link(c)
    c_staff = bpy.data.collections.new("Staff")
    scene.collection.children.link(c_staff)

    build_head(c_body, M)
    build_ears(c_body, M)
    build_neck(c_body, M)
    build_hands(c_body, M)
    build_torso(c_outfit, M)
    build_collar(c_outfit, M)
    build_arms(c_outfit, M)
    build_legs(c_outfit, M)
    build_boots(c_outfit, M)
    build_skirt(c_outfit, M)
    build_corset(c_outfit, M)
    build_belt(c_acc, M)
    _, grid = build_cape(c_outfit, M)
    build_hood(c_outfit, M)
    build_brooches(c_acc, M, grid)
    build_hair(c_hair, M)
    build_braid(c_hair, M)
    staff_objs, crystal_center = build_staff(c_staff, M)

    rig = bpy.data.objects.new("ElfMage_Root", None)
    root.objects.link(rig)
    for c in (c_body, c_hair, c_outfit, c_acc):
        for ob in c.objects:
            ob.parent = rig
    staff_root = bpy.data.objects.new("Staff_Root", None)
    c_staff.objects.link(staff_root)
    for ob in staff_objs:
        ob.parent = staff_root
    scene["crystal_center"] = list(crystal_center)
    return scene
