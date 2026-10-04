"""A tiny shaded-pixel renderer: rounded shapes lit from the top left, then a coloured outline.

Shapes are painted in order (later ones on top). Each pixel remembers its material and how much light
it gets; at the end the light is turned into one of four shades (shadow, base, light, highlight) from
the material's ramp, and every empty pixel touching the sprite gets that material's outline colour.
"""
import math

from PIL import Image

LIGHT = (-0.5, -0.62, 0.6)
_len = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _len for c in LIGHT)

# Each ramp: shadow, base, light, highlight, outline.
PALETTES = {
    "orange": {
        "fur": ("#8e3413", "#c9561c", "#ea7d2e", "#f7a95c", "#4a1a0a"),
        "white": ("#b8a594", "#e3d5c6", "#f6eee4", "#ffffff", "#6b5646"),
        "dark": ("#20120c", "#382017", "#55321f", "#6e452c", "#120804"),
        "nose": ("#120c0a", "#22160f", "#3a2a22", "#6b5a52", "#0a0604"),
        "eye": ("#140a06", "#140a06", "#140a06", "#140a06", "#140a06"),
        "shine": ("#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"),
        "mouth": ("#3a0f10", "#5a1a1c", "#7a2a2a", "#8a3a3a", "#2a0808"),
        "tongue": ("#b2475a", "#d9667a", "#ee8a9a", "#f7b0bc", "#6a1f2c"),
        "tip": ("#b8a594", "#e3d5c6", "#f6eee4", "#ffffff", "#6b5646"),  # white tail tip
        "side": ("#8e3413", "#c9561c", "#ea7d2e", "#f7a95c", "#4a1a0a"),  # same as fur on a red fox
    },
    # A gray fox: grizzled grey back, rusty sides and neck, white throat, black-tipped tail.
    "grey": {
        "fur": ("#45464c", "#6b6c72", "#8f9096", "#b9babf", "#222327"),
        "white": ("#b2aca4", "#dcd6cc", "#f0ebe3", "#ffffff", "#5e5850"),
        "dark": ("#141212", "#24201e", "#3a3430", "#4e4742", "#080606"),
        "nose": ("#120c0a", "#22160f", "#3a2a22", "#6b5a52", "#0a0604"),
        "eye": ("#140a06", "#140a06", "#140a06", "#140a06", "#140a06"),
        "shine": ("#ffffff", "#ffffff", "#ffffff", "#ffffff", "#ffffff"),
        "mouth": ("#3a0f10", "#5a1a1c", "#7a2a2a", "#8a3a3a", "#2a0808"),
        "tongue": ("#b2475a", "#d9667a", "#ee8a9a", "#f7b0bc", "#6a1f2c"),
        "tip": ("#0e0c0c", "#1c1818", "#2c2626", "#3c3434", "#040303"),  # black tail tip
        "side": ("#3e3f45", "#5f6066", "#83848a", "#a9aaaf", "#1e1f23"),  # legs: grey, a shade darker than the back
    },
}

COMMON = {
    "bark": ("#3e2616", "#5c3a22", "#7a5132", "#956a46", "#24150b"),
    "leaf_red": ("#7c1c14", "#b22e1c", "#d8492a", "#ef7448", "#4a0f0a"),
    "leaf_orange": ("#9a4310", "#d66a16", "#f08f2a", "#f9b55a", "#5a2606"),
    "leaf_yellow": ("#a07a12", "#d6a91e", "#f0cc3a", "#fbe57a", "#5e440a"),
    "leaf_green": ("#3e5a1a", "#5c7f24", "#7ea232", "#a6c45a", "#24360c"),
    "leaf_brown": ("#5a3418", "#7c4c24", "#9c6634", "#bb8550", "#33190a"),
    "acorn": ("#6a3e14", "#9a5e22", "#c07e36", "#dca05a", "#3a1f08"),
    "cap": ("#3e2a16", "#5e4226", "#7e5a36", "#9c7650", "#21140a"),
    "squirrel": ("#5a3424", "#8a5236", "#ad6c48", "#c88a64", "#2e1810"),
    "bird": ("#7a1414", "#b21e1e", "#d83a32", "#f06454", "#3e0808"),
    "beak": ("#9a6a10", "#d69a1e", "#f0c040", "#fbe080", "#4e3406"),
    "cat_black": ("#141010", "#241c1a", "#342a26", "#463a34", "#080606"),
    "cat_orange": ("#8a3c0e", "#c25e16", "#e08028", "#f2a650", "#4a1e06"),
    "dirt": ("#3a2614", "#5a3c22", "#78543a", "#94704e", "#22160a"),
    "grey": ("#4a4a50", "#6e6e78", "#9696a0", "#c2c2cc", "#24242a"),
}


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rot(x, y, cx, cy, degrees):
    a = math.radians(degrees)
    dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)


class Canvas:
    def __init__(self, width, height, palette="orange"):
        self.w, self.h = width, height
        self.ramps = {**COMMON, **PALETTES[palette]}
        self.mat = [[None] * width for _ in range(height)]
        self.lum = [[0.0] * width for _ in range(height)]
        self.fixed = [[None] * width for _ in range(height)]  # a shade index that ignores lighting

    def _put(self, x, y, mat, lum=None, level=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y][x] = mat
            self.lum[y][x] = 0.0 if lum is None else lum
            self.fixed[y][x] = level

    @staticmethod
    def _shade(nx, ny, bias):
        d = nx * nx + ny * ny
        nz = math.sqrt(max(0.0, 1.0 - d))
        lum = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2] + bias
        # a darker rim on the shadow side, so overlapping shapes stay readable
        if d > 0.72 and nx * LIGHT[0] + ny * LIGHT[1] < -0.1:
            lum -= 0.45
        return lum

    def ellipse(self, cx, cy, rx, ry, mat, angle=0.0, bias=0.0, clip=None):
        """A lit ellipse. clip(x, y) -> bool can keep only part of it (e.g. the lower half)."""
        reach = int(max(rx, ry)) + 2
        a = math.radians(-angle)
        ca, sa = math.cos(a), math.sin(a)
        for y in range(int(cy) - reach, int(cy) + reach + 1):
            for x in range(int(cx) - reach, int(cx) + reach + 1):
                px, py = x + 0.5 - cx, y + 0.5 - cy
                lx, ly = px * ca - py * sa, px * sa + py * ca
                nx, ny = lx / rx, ly / ry
                if nx * nx + ny * ny <= 1.0 and (clip is None or clip(x, y)):
                    # turn the local normal back to screen space so light comes from the same side
                    sx, sy = nx * ca + ny * sa, -nx * sa + ny * ca
                    self._put(x, y, mat, self._shade(sx, sy, bias))

    def capsule(self, x1, y1, x2, y2, r1, r2, mat, bias=0.0, clip=None):
        """A lit rounded stick from (x1, y1) to (x2, y2), radius r1 at the start and r2 at the end."""
        reach = int(max(r1, r2)) + 2
        dx, dy = x2 - x1, y2 - y1
        length2 = dx * dx + dy * dy or 1e-9
        for y in range(int(min(y1, y2)) - reach, int(max(y1, y2)) + reach + 1):
            for x in range(int(min(x1, x2)) - reach, int(max(x1, x2)) + reach + 1):
                px, py = x + 0.5, y + 0.5
                t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / length2))
                qx, qy = x1 + dx * t, y1 + dy * t
                r = r1 + (r2 - r1) * t
                ox, oy = px - qx, py - qy
                if ox * ox + oy * oy <= r * r and (clip is None or clip(x, y)):
                    self._put(x, y, mat, self._shade(ox / r, oy / r, bias))

    def chain(self, points, radii, mats, bias=0.0):
        """A tapering tube through points (a tail). mats[i] is the material of segment i."""
        for i in range(len(points) - 1):
            (x1, y1), (x2, y2) = points[i], points[i + 1]
            self.capsule(x1, y1, x2, y2, radii[i], radii[i + 1], mats[i], bias)

    def polygon(self, points, mat, lum=0.3, bias=0.0):
        """A flat-lit polygon (ears)."""
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
            for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
                if _inside(x + 0.5, y + 0.5, points):
                    # a little gradient: lighter toward the top left of the shape
                    g = -0.012 * ((x - min(xs)) + (y - min(ys)))
                    self._put(x, y, mat, lum + bias + g)

    def pixel(self, x, y, mat, level=1):
        self._put(int(x), int(y), mat, level=level)

    def to_image(self, outline=True):
        img = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        px = img.load()
        for y in range(self.h):
            for x in range(self.w):
                mat = self.mat[y][x]
                if mat is None:
                    continue
                level = self.fixed[y][x]
                if level is None:
                    lum = self.lum[y][x]
                    level = 0 if lum < 0.12 else 1 if lum < 0.5 else 2 if lum < 0.8 else 3
                px[x, y] = hex_rgb(self.ramps[mat][level]) + (255,)
        if outline:
            out = img.copy()
            opx = out.load()
            for y in range(self.h):
                for x in range(self.w):
                    if self.mat[y][x] is not None:
                        continue
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < self.w and 0 <= ny < self.h and self.mat[ny][nx] is not None:
                            opx[x, y] = hex_rgb(self.ramps[self.mat[ny][nx]][4]) + (255,)
                            break
            img = out
        return img


def _inside(x, y, points):
    inside = False
    j = len(points) - 1
    for i in range(len(points)):
        xi, yi = points[i]
        xj, yj = points[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi:
            inside = not inside
        j = i
    return inside


def bezier(p0, p1, p2, steps):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / (steps - 1) for i in range(steps))]
