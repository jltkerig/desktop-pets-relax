"""Leafy crowns for the trees, painted the way pixel artists do them: a crown is a heap of rounded leaf
clusters, each lit from the top left with a pattern of small leaf "scales" inside it, darker clusters behind,
and the whole crown lighter on top and shading to cool, deep colours underneath.

A tone list runs from the darkest (material, shade) to the lightest, and can cross materials (a deep
blue-green under a summer crown, a bright yellow-green on top)."""
import math

from pixelkit import COMMON

COMMON.update({
    "leaf_young": ("#4e7a1c", "#74a82a", "#98cc3e", "#c6ec7c", "#2a440c"),     # a spring crown's fresh green
    "leaf_birch": ("#3c6a16", "#5e9424", "#82ba34", "#b2de62", "#203c0a"),     # a birch's bright summer green
    "leaf_gold": ("#9c6a0c", "#d49a14", "#f2c42c", "#fde774", "#5a3c06"),      # a birch's autumn gold
})

# darkest to lightest: (material, shade)
TONES = {
    "summer": (("leaf_summer_blue", 0), ("leaf_summer_blue", 1), ("leaf_summer_dark", 1), ("leaf_summer_dark", 2),
               ("leaf_green", 2), ("leaf_summer_light", 1), ("leaf_summer_light", 2), ("leaf_summer_light", 3)),
    "spring": (("leaf_summer_dark", 1), ("leaf_young", 0), ("leaf_young", 1), ("leaf_young", 2),
               ("leaf_spring", 2), ("leaf_young", 3), ("leaf_spring", 3)),
    "gold": (("leaf_brown", 0), ("leaf_orange", 0), ("leaf_yellow", 0), ("leaf_yellow", 1), ("leaf_yellow", 2),
             ("leaf_yellow", 3)),
    "orange": (("leaf_red", 0), ("leaf_orange", 0), ("leaf_orange", 1), ("leaf_orange", 2), ("leaf_yellow", 2),
               ("leaf_yellow", 3)),
    "red": (("leaf_brown", 0), ("leaf_red", 0), ("leaf_red", 1), ("leaf_red", 2), ("leaf_orange", 2),
            ("leaf_orange", 3)),
    "russet": (("leaf_brown", 0), ("leaf_brown", 1), ("leaf_red", 1), ("leaf_brown", 2), ("leaf_orange", 2),
               ("leaf_brown", 3)),
    "birch": (("leaf_summer_dark", 1), ("leaf_birch", 0), ("leaf_birch", 1), ("leaf_birch", 2), ("leaf_birch", 3),
              ("leaf_summer_light", 3)),
    "birch_gold": (("leaf_orange", 0), ("leaf_gold", 0), ("leaf_gold", 1), ("leaf_gold", 2), ("leaf_gold", 3),
                   ("leaf_yellow", 3)),
}


class Cluster:
    """One rounded clump of leaves: centre, radius, which tones, back (darker, behind the branches) or front,
    and a little brightness of its own."""

    def __init__(self, x, y, r, tones, back=False, lift=0.0, phase=0.0, tall=1.0):
        self.x, self.y, self.r, self.tones, self.back, self.lift, self.phase = x, y, r, tones, back, lift, phase
        self.tall = tall  # taller than wide (a birch's hanging curtains of leaves)


def scatter(rng, cx, cy, rx, ry, count, rmin, rmax, flat_bottom=0.0, tries=4000):
    """Cluster centres and radii spread over an oval crown (a little flatter underneath if flat_bottom), not
    too crowded: [(x, y, r)]."""
    out = []
    for _ in range(tries):
        if len(out) >= count:
            break
        r = rng.uniform(rmin, rmax)
        a, d = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x = cx + math.cos(a) * d * (rx - r * 0.55)
        y = cy + math.sin(a) * d * (ry - r * 0.55)
        if y > cy and flat_bottom:
            y = cy + (y - cy) * (1 - flat_bottom)
        if all(math.hypot(x - ox, y - oy) > (r + orr) * 0.55 for ox, oy, orr in out):
            out.append((x, y, r))
    return out


def paint(c, clusters, top, bottom, sway=None, cell=(5, 4), keep=None):
    """Paint the clusters onto the canvas (back ones first, then front ones, each lot from the top down, so
    lower clusters sit in front of higher ones). top and bottom: the crown's top and bottom rows, for the
    light-to-dark shading down the crown. sway(y) -> how far the crown has moved at that height. keep(x, y,
    cluster): False leaves that pixel bare (gaps that show branches or sky)."""
    sway = sway or (lambda y: 0.0)
    cw, ch = cell
    for group in (True, False):
        for k in sorted((k for k in clusters if k.back == group), key=lambda k: k.y):
            cx, cy, r = k.x + sway(k.y), k.y, k.r
            lobes = max(4, int(r / 3.2))
            reach = int(r * 1.2 * max(1.0, k.tall)) + 2
            for y in range(int(cy) - reach, int(cy) + reach + 1):
                if not 0 <= y < c.h:
                    continue
                for x in range(int(cx) - reach, int(cx) + reach + 1):
                    if not 0 <= x < c.w:
                        continue
                    dx, dy = x + 0.5 - cx, (y + 0.5 - cy) / k.tall
                    dist = math.hypot(dx, dy)
                    ang = math.atan2(dy, dx)
                    edge = r * (1 + 0.07 * math.sin(lobes * ang + k.phase) + 0.03 * math.sin(lobes * 1.7 * ang + 1))
                    scale, middle = _leaf_scale(dx, dy, cw, ch, k.phase)
                    if dist > edge - 1.5 + 2.6 * middle or (keep is not None and not keep(x, y, k)):
                        continue  # (the edge is made of the small leaves' tips, so it's leafy, not smooth)
                    nx, ny = dx / r, dy / r
                    lit = -(0.62 * nx + 0.78 * ny)                    # the clump's own light, from the top left
                    height = 1 - (y - top) / max(1, bottom - top)     # 1 at the top of the crown, 0 underneath
                    v = 0.36 + 0.3 * lit + 0.14 * scale + 0.3 * height + k.lift - (0.2 if k.back else 0.0)
                    if dist > edge - 1.2 and lit < 0.1:
                        v -= 0.12                                     # a dark rim where it turns away
                    tones = k.tones
                    mat, level = tones[max(0, min(len(tones) - 1, int(v * len(tones))))]
                    c.mat[y][x], c.fixed[y][x] = mat, level


def _leaf_scale(dx, dy, cw, ch, seed):
    """The pattern of small leaves inside a cluster: loosely staggered little rounded leaves, each lit on its
    upper left with a dark lower rim, nudged about so the pattern doesn't line up like brickwork. Returns
    (brightness, how near the middle of its leaf)."""
    row = math.floor(dy / ch)
    shift = (row * 0.618 + seed) % 1.0 * cw          # each row starts somewhere different
    col = math.floor((dx + shift) / cw)
    h = (col * 73856093 ^ row * 19349663 ^ int(seed * 1000)) & 0xFFFF
    ox, oy = (h & 0xFF) / 255 - 0.5, (h >> 8) / 255 - 0.5   # this leaf's own little offset
    fu = (dx + shift) / cw - col - 0.5 - ox * 0.35
    fv = dy / ch - row - 0.5 - oy * 0.35
    d2 = fu * fu + fv * fv
    rim = d2 > 0.17 + 0.06 * oy
    shade = -(0.7 * fu + 0.9 * fv) - (0.5 if rim else 0.0) + ox * 0.15
    return shade, max(0.0, 1 - d2 / 0.2)  # (how near this leaf's middle: 1 in the middle, 0 at its edge)


def autumn_tones(rng, height, back=False):
    """An autumn cluster's colours: gold most often near the top, red lower down (and now and then a russet
    one, at the back, where it gives the crown depth without looking muddy)."""
    pick = rng.random() + (0.5 - height) * 0.7
    if back and rng.random() < 0.2:
        return TONES["russet"]
    return TONES["gold" if pick < 0.32 else "orange" if pick < 0.7 else "red"]

