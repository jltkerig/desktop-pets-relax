"""The oak through the four seasons (and what falls from it), the birch, leaves and acorns."""
import math
import random

from pixelkit import COMMON, Canvas
from .common import _daffodil_head, _px, _rot_pts, _twig


# -- the oak -----------------------------------------------------------------------------------------

OAK_W, OAK_H = 220, 232
OAK_GROUND = 229          # the trunk's base row
OAK_X = 110               # the trunk's centre column
OAK_CROWN = (110, 86)     # centre of the crown


def _branch(c, x1, y1, x2, y2, width):
    """A straight, chunky pixel branch: light along its top edge, dark along the bottom."""
    steps = int(max(abs(x2 - x1), abs(y2 - y1))) + 1
    for i in range(steps + 1):
        x = round(x1 + (x2 - x1) * i / steps)
        y = round(y1 + (y2 - y1) * i / steps)
        w = max(2, round(width - (width - 2) * i / steps))  # thinner toward the end
        for k in range(w):
            level = 2 if k == 0 else 0 if k == w - 1 else 1
            _px(c, x, y + k, "bark", level)


def _oak_trunk(c, rng, sway, top=120, branches=True):
    """The oak's trunk, roots, bark and (if branches) the big branches up into a leafy crown. A leafless oak
    stops the trunk lower (top) and forks it into its own V of limbs instead."""
    # the trunk: straight stepped sides, tapering upward, with a flared base
    for y in range(top, OAK_GROUND + 1):
        rise = OAK_GROUND - y
        half = 12 - min(rise, 70) * 0.06            # 12 wide at the base, narrowing to about 8
        if rise < 10:
            half += (10 - rise) * 0.7                # the flare into the roots
        half = int(half)
        left, right = OAK_X - half, OAK_X + half
        for x in range(left, right + 1):
            band = (x - left) / max(1, right - left)
            level = 3 if band < 0.12 else 2 if band < 0.35 else 1 if band < 0.72 else 0
            _px(c, x, y, "bark", level)
    # roots: stepped lumps spreading out on the ground
    for side in (-1, 1):
        for i in range(9):
            x = OAK_X + side * (13 + i)
            top = OAK_GROUND - max(0, 5 - i // 2)
            for y in range(top, OAK_GROUND + 1):
                _px(c, x, y, "bark", 2 if y == top else 0 if side > 0 else 1)
    # bark: broken vertical furrows and a few lighter flecks
    for x, y1, y2 in ((OAK_X - 5, 132, 168), (OAK_X - 5, 176, 214), (OAK_X - 1, 126, 160), (OAK_X - 1, 168, 222),
                      (OAK_X + 3, 140, 196), (OAK_X + 6, 150, 220), (OAK_X - 8, 186, 224)):
        for y in range(y1, y2):
            if c.mat[y][x] == "bark":
                c.fixed[y][x] = 0
    for _ in range(26):
        x, y = rng.randrange(OAK_X - 9, OAK_X + 4), rng.randrange(130, 224)
        if c.mat[y][x] == "bark" and c.fixed[y][x] != 0:
            c.fixed[y][x] = 3 if c.fixed[y][x] >= 2 else 2
    # branches reaching up into the crown
    for x1, y1, x2, y2, w in (() if not branches else ((OAK_X - 3, 152, OAK_X - 44, 104, 5), (OAK_X + 3, 146, OAK_X + 46, 100, 5),
                              (OAK_X, 136, OAK_X - 6, 86, 5), (OAK_X - 30, 120, OAK_X - 60, 100, 3),
                              (OAK_X + 30, 116, OAK_X + 62, 96, 3))):
        _branch(c, x1, y1, x2 + sway, y2, w)


def _limb(c, x1, y1, x2, y2, w1, w2):
    """A thick, tapering limb going up from (x1, y1) (w1 wide) to (x2, y2) (w2 wide), lit like the trunk: light
    on the left, dark on the right, with a rounded end."""
    for y in range(int(y2), int(y1) + 1):
        t = (y1 - y) / max(1, y1 - y2)
        cx, half = x1 + (x2 - x1) * t, (w1 + (w2 - w1) * t) / 2
        left, right = int(round(cx - half)), int(round(cx + half))
        for x in range(left, right + 1):
            band = (x - left) / max(1, right - left)
            _px(c, x, y, "bark", 3 if band < 0.15 else 2 if band < 0.4 else 1 if band < 0.75 else 0)
    c.ellipse(x2, y2, w2 / 2, w2 / 2 * 0.8, "bark", bias=0.1)


# a leafless oak's trunk forks into a thick V: (base x, base y, top x, top y, base width, top width) for each arm
BARE_FORK = [(OAK_X - 4, 132, OAK_X - 30, 92, 10, 6), (OAK_X + 4, 132, OAK_X + 28, 90, 10, 6)]


# the crown's colours: (cut-off, leaf colour) from the top of the crown to the bottom
CROWN_COLOURS = {
    "autumn": ((0.3, "leaf_yellow"), (0.62, "leaf_orange"), (0.8, "leaf_red"), (9.0, "leaf_brown")),
    "summer": ((0.3, "leaf_summer_light"), (0.58, "leaf_green"), (0.8, "leaf_summer_dark"), (9.0, "leaf_summer_blue")),
}


def _leaf_at(px, py, leaf):
    """Where (px, py) falls on a leaf, or None if it's off it. leaf: (x, y, half length, half width, angle in
    radians the tip points to, lobes). A leaf is pointed at the tip, fuller toward its base; lobes > 0 gives it a
    wavy oak edge. Returns (u, v): u -1 at the stalk .. 1 at the tip, v -1 .. 1 across (0 on the middle vein)."""
    x, y, length, width, angle, lobes = leaf
    dx, dy = px - x, py - y
    ca, sa = math.cos(angle), math.sin(angle)
    u, across = (dx * ca + dy * sa) / length, -dx * sa + dy * ca
    if not -1.0 <= u <= 1.0:
        return None
    half = width * (1 - u * u) ** 0.7 * (1.12 - 0.32 * u)  # pointed tip, rounder base
    if lobes:
        half *= 0.86 + 0.2 * abs(math.cos(u * math.pi * lobes / 2))  # oak lobes
    if half <= 0 or abs(across) > half:
        return None
    return u, across / half


def _leaf_light(u, v, angle, size):
    """How a leaf is lit: the half facing up-left catches the light, a darker vein down the middle (on leaves big
    enough to show one), and a slightly darker rim."""
    facing = -math.sin(angle) * 0.6 - math.cos(angle) * 0.4  # which side of the vein faces the light
    lum = 0.2 + (0.22 if v * facing > 0 else -0.12) - 0.25 * max(0.0, abs(v) - 0.7) / 0.3 - 0.1 * max(0.0, u)
    if size >= 6 and abs(v) < 0.14 and -0.85 < u < 0.8:
        lum -= 0.3
    return lum


def oak(sway=0.0, seed=7, season="autumn"):
    """220 x 232. Flat pixel-art trunk and branches; a big leafy crown. sway moves the crown a little.
    season: "autumn" (gold, orange, red and brown) or "summer" (vibrant greens, shading to blue, green acorns)."""
    c = Canvas(OAK_W, OAK_H)
    rng = random.Random(seed)
    _oak_trunk(c, rng, sway)
    # the crown: dozens of overlapping clumps of leaves, each lit on its own (bright top-left, shaded
    # bottom-right), the lower ones in front; darker underneath and to the right, like one big rounded tree
    cx0, cy0 = OAK_CROWN[0] + sway, OAK_CROWN[1]
    rx0, ry0 = 76, 52
    clumps = []  # big oak leaves: (x, y, half length, half width, angle, lobes)
    for _ in range(2500):  # scatter leaves of mixed sizes over the crown's oval, tips spraying outward
        a, d = rng.uniform(0, 2 * math.pi), math.sqrt(rng.random())
        x, y = cx0 + math.cos(a) * d * rx0, cy0 + math.sin(a) * d * ry0 * (0.9 if math.sin(a) > 0 else 1.0)
        r = rng.choice((rng.uniform(9, 12), rng.uniform(7, 9), rng.uniform(5, 7))) * (1.0 - 0.15 * d * d)
        if all(math.hypot(x - lx, (y - ly) * 1.2) > (r + ll) * 0.4 for lx, ly, ll, *_ in clumps):
            out = math.atan2((y - cy0) * 1.4, x - cx0) if d > 0.15 else rng.uniform(-math.pi, 0)
            angle = out + rng.uniform(-0.6, 0.6)
            clumps.append((x, y, r * 1.05, r * 0.6, angle, 3))
    clumps.sort(key=lambda k: k[1])  # top ones first: lower leaves overlap them, in front
    holes = [(OAK_X - 38 + sway * 0.5, 112, 4.0, 3.0), (OAK_X + 40 + sway * 0.5, 107, 3.6, 2.8),
             (OAK_X - 4 + sway * 0.5, 120, 3.2, 2.6), (cx0 + 30, cy0 - 18, 2.6, 2.0)]

    def clump_colour(k, lx, ly):
        top = max(0.0, min(1.0, (ly - (cy0 - ry0)) / (2 * ry0)))  # 0 at the top of the crown, 1 at the bottom
        side = (lx - cx0) / rx0
        drift = (math.sin(lx * 0.07 + ly * 0.03 + 1.1) + math.sin(ly * 0.09 - lx * 0.02 + 2.0)) * 0.16
        v = top * 0.5 + side * 0.08 + drift + rng.uniform(-0.1, 0.1) + 0.16  # patches drift across, not stripes
        cuts = CROWN_COLOURS[season]
        mat = next(m for cut, m in cuts if v < cut)
        if mat == cuts[-1][1] and ly < cy0 + ry0 * 0.45:
            mat = cuts[-2][1]  # the deepest shade only underneath, where the shadow is
        return mat

    colours = [clump_colour(k, lx, ly) for k, (lx, ly, *_) in enumerate(clumps)]
    owner = {}
    for y in range(0, 160):
        for x in range(0, OAK_W):
            px_, py_ = x + 0.5, y + 0.5
            if any(((px_ - hx) / hrx) ** 2 + ((py_ - hy) / hry) ** 2 <= 1 for hx, hy, hrx, hry in holes):
                continue
            for k in range(len(clumps) - 1, -1, -1):  # the front-most leaf here
                if abs(px_ - clumps[k][0]) > clumps[k][2] or abs(py_ - clumps[k][1]) > clumps[k][2]:
                    continue
                at = _leaf_at(px_, py_, clumps[k])
                if at is not None:
                    owner[(x, y)] = (k, at)
                    break
            else:  # a gap between clumps, inside the crown: the deep shade in among the leaves
                if ((px_ - cx0) / (rx0 * 0.92)) ** 2 + ((py_ - cy0) / (ry0 * 0.88)) ** 2 <= 1:
                    owner[(x, y)] = (-1, None)
    deep = CROWN_COLOURS[season][-1][1]
    for (x, y), (k, at) in owner.items():
        if k < 0:
            c.mat[y][x], c.lum[y][x], c.fixed[y][x] = deep, -1.0, None
            continue
        u, v = at
        gx, gy = (x + 0.5 - cx0) / rx0, (y + 0.5 - cy0) / ry0
        lum = _leaf_light(u, v, clumps[k][4], clumps[k][2]) \
            - 0.32 * max(0.0, gx * 0.45 + gy * 0.75) + 0.12 * max(0.0, -gx * 0.5 - gy * 0.6)  # rounded crown
        # a dark edge where this leaf lies over the one behind it
        if any(0 <= owner.get((x + dx, y + dy), (k,))[0] < k for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1))):
            lum -= 0.5
        c.mat[y][x], c.lum[y][x], c.fixed[y][x] = colours[k], lum, None
    # keep only the crown piece joined to the middle (no floating crumbs)
    seen, stack = set(), [(int(cx0), int(cy0))]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < OAK_W and 0 <= y < 160) or not (c.mat[y][x] or "").startswith("leaf"):
            continue
        seen.add((x, y))
        stack.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    for y in range(160):
        for x in range(OAK_W):
            if (c.mat[y][x] or "").startswith("leaf") and (x, y) not in seen:
                c.mat[y][x] = None
    # a jagged, leafy edge: nibble some edge pixels away and push others out a pixel
    edge = [(x, y) for y in range(1, 159) for x in range(1, OAK_W - 1)
            if c.mat[y][x] and c.mat[y][x].startswith("leaf")
            and any(c.mat[y + dy][x + dx] is None for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for x, y in edge:
        roll = rng.random()
        if roll < 0.22:
            c.mat[y][x] = None
        elif roll < 0.45:
            dx, dy = rng.choice(((1, 0), (-1, 0), (0, -1), (1, -1), (-1, -1)))
            if c.mat[y + dy][x + dx] is None:
                c.mat[y + dy][x + dx], c.lum[y + dy][x + dx], c.fixed[y + dy][x + dx] = c.mat[y][x], c.lum[y][x], None
    if season == "summer":  # green acorns here and there, hanging under the leaves
        arng = random.Random(seed + 100)
        for _ in range(9):
            x, y = arng.randrange(50, 172), arng.randrange(60, 130)
            if (c.mat[y][x] or "").startswith("leaf") and (c.mat[y + 6][x] or "").startswith("leaf"):
                c.ellipse(x + sway * 0.3, y + 1.6, 1.4, 1.8, "acorn_green")
                c.ellipse(x + sway * 0.3, y, 1.7, 1.0, "cap")
        _pansies(c, OAK_GROUND, OAK_X, 92)  # pansies growing round the foot of the tree
    return c.to_image()


COMMON.update({
    "leaf_summer_light": ("#4c8a1c", "#6cae26", "#8ccc3a", "#b4e466", "#28500c"),
    "leaf_summer_dark": ("#1e4a1c", "#2e6a26", "#3e8634", "#5ea84c", "#0e2a0c"),
    "leaf_summer_blue": ("#1a3a3e", "#245458", "#2e6c6c", "#4a8c84", "#0c2224"),  # cool blue shade underneath
    "acorn_green": ("#4e6a1a", "#6c8c24", "#8cac36", "#b0cc5c", "#28380a"),
    "leaf_spring": ("#5a8a1e", "#7cb02c", "#9cd040", "#c4ec78", "#2e4e0c"),
    "bud": ("#7a2a2a", "#a8443a", "#cc6a50", "#e8987a", "#401010"),
    "snow": ("#a8b8cc", "#d4deea", "#eef3f8", "#ffffff", "#6c7c90"),
    "violet": ("#3a1e6a", "#5a32a0", "#7c50c8", "#a87ce6", "#1e0c3a"),
    "daffodil": ("#b8860c", "#e8b81a", "#f8d838", "#fff080", "#6a4a04"),
    "daffodil_cup": ("#b8500c", "#e07418", "#f49a2c", "#fcc060", "#5a2604"),
    "stalk": ("#2e5a14", "#447e1e", "#5c9e2a", "#80c048", "#183208"),
})


def bare_oak_shape(seed=7):
    """The branching of a leafless oak (the same in every frame and every bare season), worked out without any
    sway: a list of (x1, y1, x2, y2, width) segments, the twig tips, and fork points high in the crown where a
    bird can sit."""
    rng = random.Random(seed + 31)
    segments, tips, forks = [], [], []
    cx, cy, rx, ry = OAK_CROWN[0], OAK_CROWN[1] - 6, 92, 74  # stay inside roughly the autumn crown's outline

    def inside(x, y):
        return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1

    def grow(x, y, angle, length, width, depth):
        x2, y2 = x + math.cos(angle) * length, y - math.sin(angle) * length
        if not inside(x2, y2) or depth == 0:
            # the end: a little fan of fine twigs
            for turn in rng.sample((-0.45, 0.0, 0.45), 2):
                a = angle + turn + rng.uniform(-0.15, 0.15)
                l = rng.uniform(4, 8)
                segments.append((x, y, x + math.cos(a) * l, y - math.sin(a) * l, 1))
                tips.append((x + math.cos(a) * l, y - math.sin(a) * l))
            return
        segments.append((x, y, x2, y2, width))
        if width >= 2 and y2 < 80:
            forks.append((x2, y2))
        # carry on, bending a little upward toward the light
        bend = (math.pi / 2 - angle) * 0.12
        grow(x2, y2, angle + bend + rng.uniform(-0.25, 0.25), length * rng.uniform(0.82, 0.92),
             max(1, width - 1), depth - 1)
        if rng.random() < (0.75 if width >= 3 else 0.45):  # and a side branch
            side = rng.choice((-1, 1))
            grow(x2, y2, angle + side * rng.uniform(0.45, 0.85), length * rng.uniform(0.6, 0.75),
                 max(1, width - 1), depth - 1)

    (lx1, ly1, lx2, ly2, _, _), (rx1, ry1, rx2, ry2, _, _) = BARE_FORK
    left_mid, right_mid = ((lx1 + lx2) / 2, (ly1 + ly2) / 2), ((rx1 + rx2) / 2, (ry1 + ry2) / 2)
    for (sx, sy), angle, width in (((lx2, ly2), 2.45, 5), ((lx2, ly2), 1.95, 5), ((lx2, ly2), 1.3, 4),
                                   ((rx2, ry2), 1.85, 4), ((rx2, ry2), 1.15, 5), ((rx2, ry2), 0.7, 5),
                                   (left_mid, 2.8, 4), (right_mid, 0.35, 4)):
        grow(sx, sy, angle + rng.uniform(-0.08, 0.08), rng.uniform(21, 25), width, 7)
    # perches: a few forks spread across the top of the crown
    perches = []
    for x, y in sorted(forks, key=lambda p: p[1]):
        if all(abs(x - px) > 24 for px, _ in perches):
            perches.append((x, y))
        if len(perches) == 5:
            break
    return segments, tips, perches


BARE_SEGMENTS, BARE_TIPS, BARE_PERCHES = bare_oak_shape()


def oak_bare(sway=0.0, seed=7, snow=False, spring=False):
    """220 x 232: the oak without its leaves: a winter tree of bare, branching limbs and twigs. snow: snow
    lying along the branches and in a drift round the roots. spring: buds, small new leaves and tiny acorns on
    the twigs, and violets and daffodils growing underneath."""
    c = Canvas(OAK_W, OAK_H)
    rng = random.Random(seed)
    _oak_trunk(c, rng, sway, top=132, branches=False)

    def lean(y):
        return sway * max(0.0, (140 - y) / 140) * 1.6  # higher up sways more

    for x1, y1, x2, y2, w1, w2 in BARE_FORK:  # the trunk forks into a thick V
        _limb(c, x1 + lean(y1), y1, x2 + lean(y2), y2, w1, w2)

    for x1, y1, x2, y2, width in BARE_SEGMENTS:
        if width >= 2:
            _branch(c, x1 + lean(y1), y1, x2 + lean(y2), y2, width)
        else:
            _twig(c, x1 + lean(y1), y1, x2 + lean(y2), y2)
    tips = [(x + lean(y), y) for x, y in BARE_TIPS]
    if spring:
        for x, y in tips:
            roll = rng.random()
            if roll < 0.45:  # small new leaves, fresh and pale
                c.ellipse(x + rng.uniform(-1, 1), y - 1, rng.uniform(1.6, 2.6), rng.uniform(1.0, 1.6), "leaf_spring",
                          angle=rng.uniform(-40, 40))
            elif roll < 0.85:  # a fat bud
                c.ellipse(x, y, 1.0, 1.2, "bud")
            elif roll < 0.93:  # a tiny new acorn
                c.ellipse(x, y + 1.4, 0.9, 1.1, "acorn_green")
                c.pixel(x, y, "cap", 1)
        # violets and daffodils growing round the roots
        frng = random.Random(seed + 7)
        for _ in range(18):
            fx = OAK_X + frng.choice((-1, 1)) * frng.uniform(20, 92)
            if frng.random() < 0.55:  # a violet: a low clump of heart-shaped leaves and purple flowers
                c.ellipse(fx - 1.5, OAK_GROUND - 1.2, 2.2, 1.6, "stalk")
                c.ellipse(fx + 1.8, OAK_GROUND - 1.0, 2.0, 1.4, "stalk", bias=-0.2)
                for k, (dx, h) in enumerate(((-1.5, 5), (1.5, 6.5))[: 1 + (frng.random() < 0.6)]):
                    _twig(c, fx + dx, OAK_GROUND - 2, fx + dx + sway * 0.2, OAK_GROUND - h, "stalk", 1)
                    for a in range(5):
                        ang = a / 5 * 2 * math.pi - math.pi / 2
                        c.ellipse(fx + dx + sway * 0.2 + math.cos(ang) * 1.3, OAK_GROUND - h - 1 + math.sin(ang) * 1.1,
                                  0.9, 0.9, "violet")
                    c.pixel(fx + dx + sway * 0.2, OAK_GROUND - h - 1, "daffodil", 3)
            else:  # a daffodil: a tall stem and leaf, six petals, and an orange trumpet
                h = frng.uniform(11, 16)
                top = OAK_GROUND - h
                _twig(c, fx, OAK_GROUND, fx + sway * 0.4, top, "stalk", 1)
                _twig(c, fx - 1, OAK_GROUND, fx - 3, OAK_GROUND - h * 0.7, "stalk", 2)
                _twig(c, fx + 1, OAK_GROUND, fx + 2, OAK_GROUND - h * 0.5, "stalk", 1)
                _daffodil_head(c, fx + sway * 0.4, top, 0.85)
    if snow:
        # snow lying along the tops of the branches
        for y in range(1, 228):
            for x in range(OAK_W):
                if c.mat[y][x] == "bark" and c.mat[y - 1][x] is None and (y < 200 or rng.random() < 0.15):
                    if rng.random() < 0.8:
                        _px(c, x, y - 1, "snow", 3 if rng.random() < 0.5 else 2)
                        if rng.random() < 0.35 and y > 2 and c.mat[y - 2][x] is None:
                            _px(c, x, y - 2, "snow", 3)
        # a deep, lumpy drift round the roots
        for x in range(OAK_W):
            d = abs(x - OAK_X) / 100
            if d > 1:
                continue
            depth = int(round((1 - d * d) ** 0.7 * 9 + math.sin(x * 0.21) * 1.2 + math.sin(x * 0.07 + 1) * 1.0 + 1))
            for k in range(depth):
                _px(c, x, OAK_GROUND - k, "snow", 3 if k == depth - 1 else 2 if k > depth - 3 else 1)
    return c.to_image()


# -- small things --------------------------------------------------------------------------------------

# An oak leaf outline (stem at the bottom, tip at the top), in leaf units: rounded lobes down each side.
OAK_LEAF_OUTLINE = [(0, -5.0), (1.2, -4.2), (1.0, -3.4), (2.0, -2.6), (1.6, -1.6), (2.5, -0.6), (1.9, 0.4),
                    (2.4, 1.4), (1.4, 2.2), (0.6, 2.9), (0, 3.2), (-0.6, 2.9), (-1.4, 2.2), (-2.4, 1.4),
                    (-1.9, 0.4), (-2.5, -0.6), (-1.6, -1.6), (-2.0, -2.6), (-1.0, -3.4), (-1.2, -4.2)]


def leaf(mat, spin):
    """12 x 12 oak leaf in the tree's colours. spin 0..5 tumbles it: it turns, and narrows as it tips
    edge-on, so it flutters down rather than spinning like a coin."""
    c = Canvas(12, 12)
    angle = math.radians(-35 + spin * 28)
    squash = 0.45 + 0.55 * abs(math.cos(spin * math.pi / 3))  # edge-on every few frames
    size = 1.05

    def place(x, y):
        x *= squash
        return (6 + (x * math.cos(angle) - y * math.sin(angle)) * size,
                6 + (x * math.sin(angle) + y * math.cos(angle)) * size)

    outline = [place(x, y) for x, y in OAK_LEAF_OUTLINE]
    c.polygon(outline, mat, lum=0.45)
    # the half on the far side of the vein is a shade darker, as if the leaf is slightly folded
    half = [place(x, y) for x, y in OAK_LEAF_OUTLINE if x >= 0] + [place(0, 3.2), place(0, -5.0)]
    c.polygon(half, mat, lum=0.15)
    # the vein and the stem
    for i in range(9):
        x, y = place(0, -4.2 + i * 0.95)
        c.pixel(x, y, mat, 0)
    for i in range(3):
        x, y = place(0, 3.4 + i * 0.7)
        c.pixel(x, y, "leaf_brown", 0)
    return c.to_image(outline=False)


def acorn(roll=0):
    """10 x 12 acorn; roll 0..3 rotates it when kicked."""
    c = Canvas(12, 12)
    a = roll * 90
    rad = math.radians(a)
    def at(dx, dy):
        return 6 + dx * math.cos(rad) - dy * math.sin(rad), 6 + dx * math.sin(rad) + dy * math.cos(rad)
    nx, ny = at(0, 1)
    c.ellipse(nx, ny, 2.9, 3.5, "acorn", angle=a)
    cx_, cy_ = at(0, -1.8)
    c.ellipse(cx_, cy_, 3.4, 2.0, "cap", angle=a)
    sx, sy = at(0, -4.2)
    c.capsule(cx_, cy_ - 0.5, sx, sy, 0.6, 0.5, "cap", bias=-0.3)
    return c.to_image()


def dirt_mound(size):
    c = Canvas(16, 8)
    c.ellipse(8, 7, 3 + size * 4, 1 + size * 2.2, "dirt")
    return c.to_image()


# -- the oak through the year: what falls from it, and the small creatures on it --------------------------

COMMON.update({
    "inchworm": ("#3e6a14", "#5a9020", "#7cb432", "#a6d65e", "#203a08"),
    "monarch": ("#a8400a", "#e06a14", "#f48c28", "#fbb456", "#5a1e04"),
    "beetle_brown": ("#3a2008", "#5c3412", "#82501e", "#a8723a", "#1e1004"),
    "ladybug": ("#8a0e0e", "#c41a16", "#e8322a", "#f6705e", "#4a0606"),
    "bug_black": ("#08080a", "#141418", "#22222a", "#363640", "#020203"),
    "cicada": ("#2a3a14", "#3e5a1c", "#5a7c2a", "#7ea046", "#141e08"),
    "wing_clear": ("#8aa0a8", "#b4c8cc", "#d4e2e4", "#f0f8f8", "#5a6e74"),
    "silk": ("#c8ccd0", "#e4e8ec", "#f4f6f8", "#ffffff", "#9a9ea4"),
})


def twig(spin=0):
    """16 x 16: a small fallen branch with a fork and a couple of side twigs, turning as it falls."""
    c = Canvas(16, 16)
    a = spin * math.pi / 4
    main = _rot_pts([(2, 8), (14, 8)], a, 8, 8)
    fork = _rot_pts([(9, 8), (13, 4)], a, 8, 8)
    side = _rot_pts([(5, 8), (7, 11)], a, 8, 8)
    c.capsule(*main[0], *main[1], 1.0, 0.6, "bark")
    c.capsule(*fork[0], *fork[1], 0.7, 0.4, "bark")
    c.capsule(*side[0], *side[1], 0.6, 0.4, "bark")
    return c.to_image()


def snow_clump(spin=0):
    """8 x 8: a clump of snow falling off a branch."""
    c = Canvas(8, 8)
    for dx, dy, r in ((0, 0, 2.4), (1.6 if spin else -1.4, -0.8, 1.6), (-1.2 if spin else 1.4, 1.0, 1.5)):
        c.ellipse(4 + dx, 4 + dy, r, r * 0.9, "snow")
    return c.to_image()


def snow_puff(t=0.0):
    """16 x 8: snow landing: a puff of powder that settles into a little heap."""
    c = Canvas(16, 8)
    rng = random.Random(3)
    c.ellipse(8, 7, 3 + t * 2, 1.2 + (1 - t) * 0.8, "snow")
    for _ in range(int(8 * (1 - t)) + 1):
        a = rng.uniform(math.pi, 2 * math.pi)
        d = rng.uniform(2, 3 + t * 5)
        c.pixel(8 + math.cos(a) * d * 1.3, 6 + math.sin(a) * d * (1 - t * 0.5), "snow", 3)
    return c.to_image(outline=False)


COMMON.update({
    "wing_white": ("#a8aca0", "#d8dcd2", "#f2f4ee", "#ffffff", "#5e625a"),
    "wing_sulphur": ("#b8a414", "#e0cc28", "#f4e450", "#fcf490", "#5e540a"),
    "wing_azure": ("#3a5aa8", "#5a82d0", "#82a8ec", "#b4cef8", "#1c2c5a"),
})


# -- the birch: white bark, branches that droop at the tips, a light and airy crown -------------------------

COMMON.update({
    "birch_bark": ("#9a968c", "#c8c4ba", "#e6e2d8", "#f8f6f0", "#5a5650"),
    "birch_twig": ("#3a2420", "#56362e", "#724a3e", "#8e6252", "#1e100c"),
    "catkin": ("#8a6a24", "#b08c34", "#ccaa4a", "#e2c66e", "#4a3610"),
})
BIRCH_W, BIRCH_H, BIRCH_X, BIRCH_GROUND = 110, 196, 52, 193


def birch_shape(seed=5):
    """The birch's branching (the same in every frame and season), without any sway: limbs as (x1, y1, x2, y2,
    width), drooping twigs as (x1, y1, x2, y2), the twig tips, and spots high up where a bird can sit."""
    rng = random.Random(seed)
    limbs, twigs, tips, perches = [], [], [], []
    top_y = 18
    for k in range(14):  # limbs from the upper trunk, alternating sides (not quite evenly), reaching out and up
        y = 130 - k * 8 + rng.uniform(-2, 2)
        side = 1 if k % 2 else -1
        x = BIRCH_X + (BIRCH_GROUND - y) * 0.03
        reach = rng.uniform(32, 52) * (1 - k / 16) ** 0.6 * (0.75 if k < 2 else 1)
        angle = math.radians(rng.uniform(20, 44) + k * 2)
        ex, ey = x + side * math.cos(angle) * reach, y - math.sin(angle) * reach
        limbs.append((x, y, ex, ey, 2 if k < 6 else 1))
        if k > 3 and ey < 70:
            perches.append((ex, ey))
        for j in range(rng.randint(3, 5)):  # fine twigs hanging down from along the limb
            f = rng.uniform(0.35, 1.0)
            tx, ty = x + (ex - x) * f, y + (ey - y) * f
            length = rng.uniform(7, 15)
            droop = math.radians(rng.uniform(-80, -45))
            dx, dy = side * math.cos(droop) * length * 0.5, -math.sin(droop) * length
            twigs.append((tx, ty, tx + dx, ty + dy))
            tips.append((tx + dx, ty + dy))
            tips.append((tx + dx * 0.5, ty + dy * 0.5))
    perches = sorted(perches, key=lambda p: p[1])[:4]
    return limbs, twigs, tips, perches, top_y


BIRCH_LIMBS, BIRCH_TWIGS, BIRCH_TIPS, BIRCH_PERCHES, BIRCH_TOP = birch_shape()


def birch(season="summer", sway=0.0, snow=False):
    """110 x 196: a slender birch with white bark and black markings. season: winter (bare, purplish twigs),
    spring (catkins and a few pale new leaves), summer (light, bright green), autumn (golden yellow). snow:
    snow along the branches and round the foot."""
    c = Canvas(BIRCH_W, BIRCH_H)
    rng = random.Random(9)

    def lean(y):
        return sway * max(0.0, (130 - y) / 130) * 1.8

    # the trunk: white, tapering, leaning very slightly, with black marks and a rough dark foot
    for y in range(BIRCH_TOP, BIRCH_GROUND + 1):
        half = 1.5 + (y - BIRCH_TOP) / (BIRCH_GROUND - BIRCH_TOP) * 4.5
        if BIRCH_GROUND - y < 6:
            half += (6 - (BIRCH_GROUND - y)) * 0.5
        cx = BIRCH_X + (BIRCH_GROUND - y) * 0.03 + lean(y)
        left, right = int(round(cx - half)), int(round(cx + half))
        for x in range(left, right + 1):
            band = (x - left) / max(1, right - left)
            _px(c, x, y, "birch_bark", 3 if band < 0.3 else 2 if band < 0.65 else 1 if band < 0.9 else 0)
    for _ in range(46):  # the black markings: short horizontal dashes
        y = rng.randrange(BIRCH_TOP + 6, BIRCH_GROUND - 6)
        cx = BIRCH_X + (BIRCH_GROUND - y) * 0.03 + lean(y)
        w = rng.choice((1, 2, 2, 3))
        x0 = int(round(cx + rng.uniform(-3, 2)))
        for x in range(x0, x0 + w):
            if c.mat[y][x] == "birch_bark":
                _px(c, x, y, "bug_black", rng.choice((0, 1)))
    for y in range(BIRCH_GROUND - 7, BIRCH_GROUND + 1):  # the dark, cracked foot of an old birch
        for x in range(BIRCH_W):
            if c.mat[y][x] == "birch_bark" and rng.random() < 0.55:
                _px(c, x, y, "birch_twig", rng.choice((0, 1)))
    for x1, y1, x2, y2, w in BIRCH_LIMBS:
        if w >= 2:
            _branch(c, x1 + lean(y1), y1, x2 + lean(y2), y2, 2)
        else:
            _twig(c, x1 + lean(y1), y1, x2 + lean(y2), y2, "birch_twig", 1)
    for x1, y1, x2, y2 in BIRCH_TWIGS:
        _twig(c, x1 + lean(y1), y1, x2 + lean(y2) * 1.3, y2, "birch_twig", 1)
    leaves = {"summer": ("leaf_summer_light", "leaf_green", "leaf_summer_light"),
              "autumn": ("leaf_yellow", "leaf_yellow", "leaf_orange")}.get(season)
    lrng = random.Random(21)
    if leaves:
        _birch_leaves(c, lrng, leaves, lean)
    for x, y in BIRCH_TIPS:
        lx = x + lean(y) * 1.3
        if leaves:
            continue
        if season == "spring":
            if lrng.random() < 0.5:  # a catkin dangling
                _twig(c, lx, y, lx + 0.4, y + 4, "catkin", 2)
                c.pixel(lx + 0.4, y + 4, "catkin", 3)
            elif lrng.random() < 0.6:
                c.ellipse(lx, y, 1.2, 0.9, "leaf_spring")
    if season == "summer":
        _pansies(c, BIRCH_GROUND, BIRCH_X, 46, seed=8)  # pansies round its foot
    if snow:
        for y in range(1, BIRCH_GROUND - 8):
            for x in range(BIRCH_W):
                if c.mat[y][x] in ("birch_twig", "bark") and c.mat[y - 1][x] is None and lrng.random() < 0.6:
                    _px(c, x, y - 1, "snow", 3)
        for x in range(BIRCH_W):
            d = abs(x - BIRCH_X) / 40
            if d < 1:
                for k in range(int((1 - d * d) * 5) + 1):
                    _px(c, x, BIRCH_GROUND - k, "snow", 3 if k == int((1 - d * d) * 5) else 2)
    return c.to_image()


def _birch_leaves(c, rng, leaves, lean):
    """A light, airy birch crown: small pointed leaves hanging along each limb and round the twigs, each lit on
    its own, with sky and white bark showing between them."""
    clumps = []  # (x, y, half length, half width, angle, lobes)

    def leaf(x, y, size):
        angle = math.pi / 2 + rng.uniform(-0.75, 0.75)  # hanging down, every which way a little
        clumps.append((x, y, size, size * 0.55, angle, 0))

    for x1, y1, x2, y2, _ in BIRCH_LIMBS:
        n = int(math.hypot(x2 - x1, y2 - y1) / 3.5)
        for k in range(n + 1):
            f = 0.3 + 0.7 * k / max(1, n)
            x, y = x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
            for _ in range(2):
                leaf(x + lean(y) + rng.uniform(-3, 3), y + rng.uniform(0, 4), rng.uniform(3.2, 4.6))
    for x, y in BIRCH_TIPS:
        leaf(x + lean(y) * 1.3 + rng.uniform(-1.5, 1.5), y + rng.uniform(-1, 2), rng.uniform(2.8, 3.8))
    clumps.sort(key=lambda k: k[1])  # higher ones behind, lower ones in front
    top, bottom = min(k[1] for k in clumps), max(k[1] for k in clumps)
    mats = [leaves[0] if (k[1] - top) / max(1, bottom - top) + rng.uniform(-0.25, 0.25) < 0.45 else
            rng.choice(leaves[1:]) for k in clumps]
    owner = {}
    for k, lf in enumerate(clumps):
        lx, ly, size = lf[0], lf[1], lf[2]
        for y in range(int(ly - size) - 1, int(ly + size) + 2):
            for x in range(int(lx - size) - 1, int(lx + size) + 2):
                if 0 <= x < c.w and 0 <= y < c.h:
                    at = _leaf_at(x + 0.5, y + 0.5, lf)
                    if at is not None:
                        owner[(x, y)] = (k, at)
    for (x, y), (k, (u, v)) in owner.items():
        lum = _leaf_light(u, v, clumps[k][4], clumps[k][2])
        if any(owner.get((x + dx, y + dy), (k,))[0] < k for dx, dy in ((0, -1), (-1, 0), (1, 0))):
            lum -= 0.45  # a dark edge where it lies over another leaf
        c.mat[y][x], c.lum[y][x], c.fixed[y][x] = mats[k], lum, None


def _pansies(c, ground, centre, spread, seed=3):
    """Pansies growing low round the foot of a tree: purple and yellow faces among small leaves."""
    rng = random.Random(seed)
    for _ in range(14):
        x = centre + rng.choice((-1, 1)) * rng.uniform(12, spread)
        c.ellipse(x, ground - 1, 2.0, 1.2, "stalk")
        face = rng.choice(("pansy_purple", "pansy_yellow", "pansy_purple"))
        fx, fy = x + rng.uniform(-1, 1), ground - 3
        c.ellipse(fx, fy, 1.6, 1.4, face)
        c.pixel(fx - 0.6, fy - 1, "pansy_purple" if face == "pansy_yellow" else "violet", 3)  # upper petals
        c.pixel(fx, fy, "bug_black", 0)  # the dark face in the middle
        c.pixel(fx, fy + 0.6, "pansy_yellow", 3)


LEAF_COLOURS = ("leaf_red", "leaf_orange", "leaf_yellow", "leaf_brown", "leaf_green")


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        **{f"leaf_{colour.split('_')[1]}": ([leaf(colour, s) for s in range(6)], 150, True, (6, 6))
           for colour in LEAF_COLOURS},
        "oak": ([oak(s) for s in (0, 1, 1, 0, -1, -1)], 600, True, (OAK_X, OAK_GROUND)),
        "oak_summer": ([oak(s, season="summer") for s in (0, 1, 1, 0, -1, -1)], 600, True, (OAK_X, OAK_GROUND)),
        "oak_winter": ([oak_bare(s) for s in (0, 1, 1, 0, -1, -1)], 600, True, (OAK_X, OAK_GROUND),
                       {"perches": BARE_PERCHES}),
        "oak_snow": ([oak_bare(s, snow=True) for s in (0, 1, 1, 0, -1, -1)], 600, True, (OAK_X, OAK_GROUND),
                     {"perches": BARE_PERCHES}),
        "oak_spring": ([oak_bare(s, spring=True) for s in (0, 1, 1, 0, -1, -1)], 600, True, (OAK_X, OAK_GROUND),
                       {"perches": BARE_PERCHES}),
        "acorn": ([acorn(r) for r in range(4)], 90, True, (6, 9)),
        "dirt_mound": ([dirt_mound(s) for s in (0.2, 0.5, 0.8, 1.0)], 200, False, (8, 7)),
        "twig": ([twig(k) for k in range(8)], 90, True, (8, 9)),
        "snow_clump": ([snow_clump(k) for k in range(2)], 120, True, (4, 4)),
        "snow_puff": ([snow_puff(t) for t in (0.0, 0.3, 0.6, 1.0)], 110, False, (8, 7)),
        **{f"birch_{season}": ([birch(season, s) for s in (0, 1, 1, 0, -1, -1)], 650, True, (BIRCH_X, BIRCH_GROUND),
                               {"perches": BIRCH_PERCHES})
           for season in ("winter", "spring", "summer", "autumn")},
        "birch_snow": ([birch("winter", s, snow=True) for s in (0, 1, 1, 0, -1, -1)], 650, True, (BIRCH_X, BIRCH_GROUND),
                       {"perches": BIRCH_PERCHES}),
    }
