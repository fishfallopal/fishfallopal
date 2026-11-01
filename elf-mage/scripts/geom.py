"""Geometry helpers for procedural character modelling with Blender's bpy module."""
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

TAU = 2.0 * math.pi


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(e0, e1, x):
    t = clamp((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def spow(x, p):
    return math.copysign(abs(x) ** p, x)


def hex_to_linear(h, alpha=1.0):
    h = h.lstrip("#")
    out = []
    for i in range(3):
        c = int(h[2 * i:2 * i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], alpha)


# --------------------------------------------------------------------------- curves
def catmull_rom(points, samples=8):
    P = [Vector(p) for p in points]
    ext = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(samples):
            t = k / samples
            out.append(0.5 * ((2 * p1) + (p2 - p0) * t
                              + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(P[-1].copy())
    return out


def resample(points, n):
    """Uniform arc-length resampling. Returns (points, total_length)."""
    d = [0.0]
    for i in range(1, len(points)):
        d.append(d[-1] + (points[i] - points[i - 1]).length)
    total = d[-1]
    out, j = [], 0
    for k in range(n):
        s = total * k / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        seg = d[j + 1] - d[j]
        t = 0.0 if seg < 1e-12 else (s - d[j]) / seg
        out.append(points[j].lerp(points[j + 1], clamp(t, 0.0, 1.0)))
    return out, total


def smooth_path(points, iterations=2, fix_ends=True):
    pts = [p.copy() for p in points]
    for _ in range(iterations):
        new = [p.copy() for p in pts]
        for i in range(1, len(pts) - 1):
            new[i] = pts[i] * 0.5 + (pts[i - 1] + pts[i + 1]) * 0.25
        if not fix_ends:
            new[-1] = pts[-1] * 0.5 + pts[-2] * 0.5
        pts = new
    return pts


def path_frames(points, ref_fn):
    """Frames (T, N, B) along a polyline. N follows ref_fn(i, p) projected off T."""
    frames = []
    n = len(points)
    for i in range(n):
        if i == 0:
            T = points[1] - points[0]
        elif i == n - 1:
            T = points[-1] - points[-2]
        else:
            T = points[i + 1] - points[i - 1]
        T.normalize()
        R = Vector(ref_fn(i, points[i]))
        N = R - T * R.dot(T)
        if N.length < 1e-9:
            N = T.orthogonal()
        N.normalize()
        frames.append((T, N, T.cross(N)))
    return frames


class Pchip:
    """Monotone cubic (Fritsch-Carlson) interpolation of row tables, any column count."""

    def __init__(self, x, y):
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        if y.ndim == 1:
            y = y[:, None]
        order = np.argsort(x)
        x, y = x[order], y[order]
        h = np.diff(x)
        d = np.diff(y, axis=0) / h[:, None]
        m = np.zeros_like(y)
        m[0], m[-1] = d[0], d[-1]
        for i in range(1, len(x) - 1):
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            for j in range(y.shape[1]):
                a, b = d[i - 1, j], d[i, j]
                m[i, j] = 0.0 if a * b <= 0 else (w1 + w2) / (w1 / a + w2 / b)
        self.x, self.y, self.m = x, y, m

    def __call__(self, xq):
        x, y, m = self.x, self.y, self.m
        xq = float(np.clip(xq, x[0], x[-1]))
        i = int(np.clip(np.searchsorted(x, xq) - 1, 0, len(x) - 2))
        h = x[i + 1] - x[i]
        t = (xq - x[i]) / h
        h00 = 2 * t ** 3 - 3 * t ** 2 + 1
        h10 = t ** 3 - 2 * t ** 2 + t
        h01 = -2 * t ** 3 + 3 * t ** 2
        h11 = t ** 3 - t ** 2
        return h00 * y[i] + h10 * h * m[i] + h01 * y[i + 1] + h11 * h * m[i + 1]


# --------------------------------------------------------------------------- rings
def se_xy(phi, w, front, back, ym=0.0, pf=2.0, pb=2.0):
    """Superellipse section point. phi=0 -> +x, phi=+90deg -> back (+y), -90deg -> front.
    front/back are absolute y coordinates of the front (negative) and back extremes,
    ym is the y of the widest point."""
    c, s = math.cos(phi), math.sin(phi)
    if s >= 0:
        e = 2.0 / pb
        return w * spow(c, e), ym + (back - ym) * abs(s) ** e
    e = 2.0 / pf
    return w * spow(c, e), ym - (ym - front) * abs(s) ** e


def tube_ring(center, N, B, rn, rb_neg, rb_pos, n, p=2.0, phase=0.0, bulge=None):
    pts = []
    e = 2.0 / p
    for k in range(n):
        phi = phase + TAU * k / n
        c, s = math.cos(phi), math.sin(phi)
        a = rn * spow(c, e)
        b = (rb_pos if s >= 0 else rb_neg) * spow(s, e)
        if bulge:
            b += bulge(phi, c, s)
        pts.append(center + N * a + B * b)
    return pts


def loft(rings, closed=True, cap_start=False, cap_end=False, start_pt=None, end_pt=None):
    n = len(rings[0])
    verts = [Vector(p) for r in rings for p in r]
    faces = []
    m = n if closed else n - 1
    for i in range(len(rings) - 1):
        a, b = i * n, (i + 1) * n
        for j in range(m):
            j2 = (j + 1) % n
            faces.append((a + j, a + j2, b + j2, b + j))
    if cap_start:
        c = Vector(start_pt) if start_pt is not None else sum(rings[0], Vector()) / n
        ci = len(verts)
        verts.append(c)
        for j in range(n):
            faces.append((ci, (j + 1) % n, j))
    if cap_end:
        c = Vector(end_pt) if end_pt is not None else sum(rings[-1], Vector()) / n
        ci = len(verts)
        verts.append(c)
        base = (len(rings) - 1) * n
        for j in range(n):
            faces.append((ci, base + j, base + (j + 1) % n))
    return verts, faces


def grid_faces(rows, cols, wrap=False):
    faces = []
    m = cols if wrap else cols - 1
    for i in range(rows - 1):
        for j in range(m):
            j2 = (j + 1) % cols
            faces.append((i * cols + j, i * cols + j2, (i + 1) * cols + j2, (i + 1) * cols + j))
    return faces


def tube_along(points, radius_fn, n=12, ref=(1, 0, 0), p=2.0, cap_start=True, cap_end=True,
               tip_point=None, ref_fn=None):
    """Tube following a polyline. radius_fn(t) -> (rn, rb_neg, rb_pos)."""
    frames = path_frames(points, ref_fn or (lambda i, q: ref))
    rings = []
    for i, (P, (T, N, B)) in enumerate(zip(points, frames)):
        t = i / (len(points) - 1)
        rn, rbn, rbp = radius_fn(t)
        rings.append(tube_ring(P, N, B, rn, rbn, rbp, n, p))
    return loft(rings, True, cap_start, cap_end, None, tip_point)


def ellipsoid(center, radii, rot=None, nu=12, nv=8):
    """UV ellipsoid as quads + pole fans. rot: Matrix(3x3)."""
    rot = rot or Matrix.Identity(3)
    rings = []
    for i in range(1, nv):
        th = math.pi * i / nv
        ring = []
        for j in range(nu):
            ph = TAU * j / nu
            local = Vector((radii[0] * math.sin(th) * math.cos(ph),
                            radii[1] * math.sin(th) * math.sin(ph),
                            -radii[2] * math.cos(th)))
            ring.append(Vector(center) + rot @ local)
        rings.append(ring)
    bottom = Vector(center) + rot @ Vector((0, 0, -radii[2]))
    top = Vector(center) + rot @ Vector((0, 0, radii[2]))
    return loft(rings, True, True, True, bottom, top)


def basis_from(z_axis, x_hint):
    z = Vector(z_axis).normalized()
    x = Vector(x_hint)
    x = (x - z * x.dot(z)).normalized()
    y = z.cross(x)
    return Matrix((x, y, z)).transposed()


# --------------------------------------------------------------------------- colliders
class Capsule:
    def __init__(self, a, b, r):
        self.a, self.b, self.r = Vector(a), Vector(b), r

    def push(self, p, margin):
        ab = self.b - self.a
        t = clamp((p - self.a).dot(ab) / max(ab.length_squared, 1e-12), 0.0, 1.0)
        c = self.a + ab * t
        d = p - c
        lim = self.r + margin
        if d.length < lim:
            if d.length < 1e-9:
                d = ab.orthogonal()
            return c + d.normalized() * lim
        return p


class Ellipsoid:
    def __init__(self, center, radii):
        self.c, self.r = Vector(center), Vector(radii)

    def push(self, p, margin):
        q = Vector(((p.x - self.c.x) / (self.r.x + margin), (p.y - self.c.y) / (self.r.y + margin),
                    (p.z - self.c.z) / (self.r.z + margin)))
        if q.length < 1.0:
            q = q.normalized() if q.length > 1e-9 else Vector((0, 0, 1))
            return Vector((self.c.x + q.x * (self.r.x + margin), self.c.y + q.y * (self.r.y + margin),
                           self.c.z + q.z * (self.r.z + margin)))
        return p


class ProfileBody:
    """Stack of superellipse sections (z, w, front, back, ym[, pf, pb]) used as a collider."""

    def __init__(self, rows, extra=None):
        rows = sorted(rows, key=lambda r: r[0])
        self.zmin, self.zmax = rows[0][0], rows[-1][0]
        self.f = Pchip([r[0] for r in rows], [list(r[1:]) + [2.0] * (6 - len(r)) for r in rows])
        self.extra = extra  # optional fn(phi, z) -> extra outward offset (e.g. folds)

    def section(self, z):
        v = self.f(z)
        return v[0], v[1], v[2], v[3], v[4], v[5]

    def push(self, p, margin):
        if p.z < self.zmin - 0.002 or p.z > self.zmax + 0.002:
            return p
        w, front, back, ym, pf, pb = self.section(p.z)
        y = p.y - ym
        if y >= 0:
            ry, e = back - ym, pb
        else:
            ry, e = ym - front, pf
        phi = math.atan2(p.y - ym, p.x)
        extra = self.extra(phi, p.z) if self.extra else 0.0
        w2, ry2 = w + margin + extra, ry + margin + extra
        val = (abs(p.x) / w2) ** e + (abs(y) / ry2) ** e
        if val < 1.0:
            s = val ** (-1.0 / e)
            return Vector((p.x * s, ym + y * s, p.z))
        return p


def push_points(points, colliders, margin, iterations=3):
    pts = [Vector(p) for p in points]
    for _ in range(iterations):
        for i, p in enumerate(pts):
            for c in colliders:
                p = c.push(p, margin if not isinstance(margin, (list, tuple)) else margin[i])
            pts[i] = p
    return pts


# --------------------------------------------------------------------------- mesh objects
class MeshBuilder:
    def __init__(self):
        self.verts, self.faces, self.mats = [], [], []

    def add(self, verts, faces, mat=0):
        o = len(self.verts)
        self.verts.extend(Vector(v) for v in verts)
        if isinstance(mat, int):
            self.mats.extend([mat] * len(faces))
        else:
            self.mats.extend(mat)
        self.faces.extend(tuple(i + o for i in f) for f in faces)
        return o

    def mirrored(self, axis=0):
        mb = MeshBuilder()
        vs = []
        for v in self.verts:
            v = v.copy()
            v[axis] = -v[axis]
            vs.append(v)
        mb.add(vs, [tuple(reversed(f)) for f in self.faces], self.mats)
        return mb


def make_object(name, verts, faces, materials, collection, mat_indices=None, subsurf=(1, 2),
                smooth=True, recalc=True, parent=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(clean_customdata=False)
    if recalc:
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
    for m in materials:
        me.materials.append(m)
    if mat_indices is not None and len(materials) > 1:
        me.polygons.foreach_set("material_index", list(mat_indices))
    if smooth:
        me.shade_smooth()
    me.update()
    ob = bpy.data.objects.new(name, me)
    collection.objects.link(ob)
    if subsurf:
        md = ob.modifiers.new("Subdivision", 'SUBSURF')
        md.levels, md.render_levels = subsurf
        md.uv_smooth = 'PRESERVE_BOUNDARIES'
    if parent is not None:
        ob.parent = parent
    return ob


def from_builder(name, mb, materials, collection, **kw):
    return make_object(name, mb.verts, mb.faces, materials, collection, mat_indices=mb.mats, **kw)


def orient_outward(ob, center_fn):
    """Flip all faces if, on average, normals point toward center_fn(face_center)."""
    me = ob.data
    total = 0.0
    for poly in me.polygons:
        c = Vector(poly.center)
        total += poly.normal.dot(c - Vector(center_fn(c)))
    if total < 0:
        me.flip_normals()
        me.update()


def add_solidify(ob, thickness, offset=-1.0, material_offset=0, rim=True):
    md = ob.modifiers.new("Solidify", 'SOLIDIFY')
    md.thickness = thickness
    md.offset = offset
    md.use_even_offset = True
    md.use_rim = rim
    md.material_offset = material_offset
    md.material_offset_rim = 0
    # keep subdivision after solidify
    for m in list(ob.modifiers):
        if m.type == 'SUBSURF':
            with bpy.context.temp_override(object=ob):
                bpy.ops.object.modifier_move_to_index(modifier=m.name, index=len(ob.modifiers) - 1)
    return md


def apply_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ob_eval = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ob_eval, preserve_all_data_layers=True, depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    me.name = old.name
    bpy.data.meshes.remove(old)
    return ob
