"""Face texture (eyes, brows, mouth, blush) painted with PIL in head-space metres.

The texture covers the planar front projection x in [X0, X1], z in [Z0, Z1]; the head mesh
uses the same mapping for its UVs, so features can be placed in world units."""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

X0, X1 = -0.08, 0.08
Z0, Z1 = 1.255, 1.415

EYE_X, EYE_Z = 0.0315, 1.364
SKIN = "#F7DECE"


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class Canvas:
    def __init__(self, size, ss=2):
        self.size, self.ss = size, ss
        self.W = size * ss
        self.img = Image.new("RGBA", (self.W, self.W), _rgb(SKIN) + (255,))

    def px(self, x, z):
        return ((x - X0) / (X1 - X0) * self.W, (Z1 - z) / (Z1 - Z0) * self.W)

    def m(self, metres):
        return metres / (X1 - X0) * self.W

    def layer(self):
        return Image.new("RGBA", (self.W, self.W), (0, 0, 0, 0))

    def comp(self, layer, mask=None):
        if mask is not None:
            a = np.asarray(layer.getchannel("A"), np.float32) * (np.asarray(mask, np.float32) / 255.0)
            layer.putalpha(Image.fromarray(a.astype(np.uint8)))
        self.img = Image.alpha_composite(self.img, layer)

    def result(self):
        return self.img.convert("RGB").resize((self.size, self.size), Image.LANCZOS)


def bezier(p0, p1, p2, p3, n=120):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def stroke(cv, draw, pts, widths, color):
    """Variable-width stroke. widths: list of (t, width_m) keys."""
    ts = [k[0] for k in widths]
    ws = [k[1] for k in widths]
    dense = []
    for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
        steps = max(1, int(math.hypot(xb - xa, zb - za) / 0.00005))
        dense.extend((xa + (xb - xa) * j / steps, za + (zb - za) * j / steps) for j in range(steps))
    dense.append(pts[-1])
    pts = dense
    n = len(pts)
    for i, (x, z) in enumerate(pts):
        w = float(np.interp(i / max(n - 1, 1), ts, ws))
        r = max(cv.m(w) * 0.5, 0.6)
        cx, cy = cv.px(x, z)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def ellipse(cv, draw, cx, cz, rx, rz, color):
    x0, y0 = cv.px(cx - rx, cz + rz)
    x1, y1 = cv.px(cx + rx, cz - rz)
    draw.ellipse([x0, y0, x1, y1], fill=color)


def eye(cv, side):
    """side=+1 character's left eye (image right), -1 right eye. Highlights stay image-left."""
    ex, ez = EYE_X * side, EYE_Z
    sx = lambda dx: ex + dx * side  # mirror offsets horizontally

    upper = bezier((sx(-0.0158), ez + 0.0005), (sx(-0.0120), ez + 0.0132),
                   (sx(0.0075), ez + 0.0172), (sx(0.0178), ez + 0.0045))
    lower = bezier((sx(0.0165), ez - 0.0010), (sx(0.0140), ez - 0.0122),
                   (sx(-0.0090), ez - 0.0128), (sx(-0.0150), ez - 0.0030))

    # sclera mask
    mask = Image.new("L", (cv.W, cv.W), 0)
    ImageDraw.Draw(mask).polygon([cv.px(*p) for p in upper + lower], fill=255)

    lay = cv.layer()
    ImageDraw.Draw(lay).polygon([cv.px(*p) for p in upper + lower], fill=_rgb("#FBF8F6") + (255,))
    cv.comp(lay)

    # iris with vertical gradient
    icx, icz = sx(0.0003), ez - 0.0004
    irx, irz = 0.0103, 0.0134
    x0, y0 = cv.px(icx - irx, icz + irz)
    x1, y1 = cv.px(icx + irx, icz - irz)
    x0, y0, x1, y1 = int(x0), int(y0), int(x1) + 1, int(y1) + 1
    h = y1 - y0
    stops = [(0.0, "#3B1B0B"), (0.28, "#6E3510"), (0.55, "#B9691A"), (0.80, "#EBA93C"), (1.0, "#F8D57E")]
    t = np.linspace(0, 1, h)
    grad = np.zeros((h, x1 - x0, 4), np.uint8)
    for ch in range(3):
        col = np.interp(t, [s[0] for s in stops], [_rgb(s[1])[ch] for s in stops])
        grad[:, :, ch] = col[:, None]
    yy, xx = np.mgrid[0:h, 0:x1 - x0]
    cxp, cyp = (x1 - x0) / 2, h / 2
    inside = ((xx - cxp) / ((x1 - x0) / 2)) ** 2 + ((yy - cyp) / (h / 2)) ** 2 <= 1.0
    grad[:, :, 3] = np.where(inside, 255, 0)
    lay = cv.layer()
    lay.paste(Image.fromarray(grad, "RGBA"), (x0, y0))
    d = ImageDraw.Draw(lay)
    # limbal ring
    ring = cv.layer()
    rd = ImageDraw.Draw(ring)
    ellipse(cv, rd, icx, icz, irx, irz, _rgb("#2C1409") + (255,))
    ellipse(cv, rd, icx, icz, irx - 0.0008, irz - 0.0008, (0, 0, 0, 0))
    lay = Image.alpha_composite(lay, ring)
    d = ImageDraw.Draw(lay)
    # lower inner glow crescent
    glow = cv.layer()
    gd = ImageDraw.Draw(glow)
    ellipse(cv, gd, icx, icz - 0.0030, irx * 0.72, irz * 0.55, _rgb("#FFE79A") + (120,))
    ellipse(cv, gd, icx, icz - 0.0005, irx * 0.78, irz * 0.62, (0, 0, 0, 0))
    lay = Image.alpha_composite(lay, glow)
    d = ImageDraw.Draw(lay)
    # pupil
    ellipse(cv, d, icx, icz + 0.0006, 0.0041, 0.0060, _rgb("#26110A") + (255,))
    cv.comp(lay, mask)

    # upper lid shadow over sclera and iris
    lay = cv.layer()
    stroke(cv, ImageDraw.Draw(lay), upper, [(0, 0.0030), (0.5, 0.0062), (1, 0.0040)], _rgb("#7E6A78") + (95,))
    cv.comp(lay, mask)

    # highlights (always toward image-left)
    lay = cv.layer()
    d = ImageDraw.Draw(lay)
    ellipse(cv, d, icx - 0.0040, icz + 0.0040, 0.0031, 0.0037, (255, 255, 255, 255))
    ellipse(cv, d, icx + 0.0043, icz - 0.0062, 0.0014, 0.0014, (255, 255, 255, 235))
    ellipse(cv, d, icx - 0.0014, icz - 0.0074, 0.0007, 0.0007, (255, 255, 255, 220))
    cv.comp(lay, mask)

    lay = cv.layer()
    d = ImageDraw.Draw(lay)
    ink = _rgb("#2A1711") + (255,)
    # upper lash line + wing
    stroke(cv, d, upper, [(0, 0.0007), (0.3, 0.0019), (0.75, 0.0027), (1, 0.0031)], ink)
    wing = bezier((sx(0.0170), ez + 0.0052), (sx(0.0190), ez + 0.0060), (sx(0.0205), ez + 0.0072),
                  (sx(0.0222), ez + 0.0092), 30)
    stroke(cv, d, wing, [(0, 0.0026), (1, 0.0004)], ink)
    for (a, b) in (((0.0176, 0.0068), (0.0228, 0.0112)),):
        lash = bezier((sx(a[0]), ez + a[1]), (sx(a[0] + 0.002), ez + a[1] + 0.002),
                      (sx(b[0] - 0.001), ez + b[1] - 0.0005), (sx(b[0]), ez + b[1]), 20)
        stroke(cv, d, lash, [(0, 0.0010), (1, 0.0002)], ink)
    # lower lash (outer half)
    stroke(cv, d, lower[:70], [(0, 0.0008), (1, 0.0002)], _rgb("#4A2A20") + (230,))
    # double eyelid crease
    crease = bezier((sx(-0.0085), ez + 0.0186), (sx(-0.002), ez + 0.0216),
                    (sx(0.0090), ez + 0.0206), (sx(0.0142), ez + 0.0152), 60)
    stroke(cv, d, crease, [(0, 0.0002), (0.5, 0.0006), (1, 0.0002)], _rgb("#C08A78") + (200,))
    # eyebrow
    brow = bezier((sx(-0.0140), ez + 0.0330), (sx(-0.0060), ez + 0.0378),
                  (sx(0.0080), ez + 0.0384), (sx(0.0178), ez + 0.0322), 80)
    stroke(cv, d, brow, [(0, 0.0017), (0.45, 0.0012), (1, 0.0004)], _rgb("#8A3E22") + (255,))
    cv.comp(lay)


def make_face_texture(path, size=2048):
    cv = Canvas(size)

    # blush
    alpha = Image.new("L", (cv.W, cv.W), 0)
    d = ImageDraw.Draw(alpha)
    for s in (-1, 1):
        x0, y0 = cv.px(0.040 * s - 0.0125, 1.3350 + 0.0058)
        x1, y1 = cv.px(0.040 * s + 0.0125, 1.3350 - 0.0058)
        d.ellipse([x0, y0, x1, y1], fill=110)
    alpha = alpha.filter(ImageFilter.GaussianBlur(cv.m(0.0022)))
    lay = Image.new("RGBA", (cv.W, cv.W), _rgb("#F39A8C") + (0,))
    lay.putalpha(alpha)
    cv.comp(lay)
    lay = cv.layer()
    d = ImageDraw.Draw(lay)
    for s in (-1, 1):
        for cx in (0.034, 0.040, 0.046):
            hatch = bezier((cx * s - 0.0016, 1.3332), (cx * s - 0.0005, 1.3345),
                           (cx * s + 0.0005, 1.3358), (cx * s + 0.0016, 1.3372), 20)
            stroke(cv, d, hatch, [(0, 0.0003), (0.5, 0.0006), (1, 0.0003)], _rgb("#E07A6C") + (150,))
    cv.comp(lay)

    eye(cv, 1)
    eye(cv, -1)

    lay = cv.layer()
    d = ImageDraw.Draw(lay)
    # nose hint
    nose = bezier((0.0011, 1.3352), (0.0006, 1.3345), (0.0, 1.3336), (-0.0007, 1.3328), 20)
    stroke(cv, d, nose, [(0, 0.0004), (0.5, 0.0009), (1, 0.0004)], _rgb("#D39684") + (220,))
    # mouth: gentle smile
    mouth = bezier((-0.0082, 1.3062), (-0.0040, 1.3028), (0.0040, 1.3028), (0.0082, 1.3062), 80)
    stroke(cv, d, mouth, [(0, 0.0004), (0.25, 0.0009), (0.5, 0.0011), (0.75, 0.0009), (1, 0.0004)],
           _rgb("#8C3A31") + (255,))
    lip = bezier((-0.0026, 1.3006), (-0.001, 1.2999), (0.001, 1.2999), (0.0026, 1.3006), 20)
    stroke(cv, d, lip, [(0, 0.0003), (0.5, 0.0007), (1, 0.0003)], _rgb("#E19A90") + (150,))
    cv.comp(lay)

    img = cv.result()
    img.save(path)
    return path


if __name__ == "__main__":
    import sys
    make_face_texture(sys.argv[1] if len(sys.argv) > 1 else "face.png")
