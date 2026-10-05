"""Everything that isn't a fox: the oak, its leaves and acorns, and the autumn visitors.

SPRITES: name -> (frames, ms per frame, loop, anchor[, extra]). The anchor is the frame point that sits on the
item's position (the trunk base, a paw on the ground...). extra: more to write into the sprite's JSON, such as
"perches" (frame points where a bird can sit).
"""
import math
import random

from pixelkit import COMMON, Canvas, bezier

COMMON.update({
    "jay": ("#22406e", "#3462a0", "#4e86c8", "#86b2e4", "#101e36"),
    "woolly_dark": ("#100a08", "#1e1410", "#2e221c", "#40322a", "#060403"),
    "woolly_rust": ("#6e300e", "#9a4a1a", "#c0682c", "#d88a4c", "#3a1606"),
})


# -- the oak -----------------------------------------------------------------------------------------

OAK_W, OAK_H = 220, 232
OAK_GROUND = 229          # the trunk's base row
OAK_X = 110               # the trunk's centre column
OAK_CROWN = (110, 86)     # centre of the crown


def _px(c, x, y, mat, level):
    if 0 <= x < c.w and 0 <= y < c.h:
        c.mat[y][x], c.fixed[y][x] = mat, level


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


def oak(sway=0.0, seed=7, season="autumn"):
    """220 x 232. Flat pixel-art trunk and branches; a big leafy crown. sway moves the crown a little.
    season: "autumn" (gold, orange, red and brown) or "summer" (vibrant greens, shading to blue, green acorns)."""
    c = Canvas(OAK_W, OAK_H)
    rng = random.Random(seed)
    _oak_trunk(c, rng, sway)
    # the crown: one leafy mass with a bumpy oak outline, lit as a single rounded shape
    cx0, cy0 = OAK_CROWN[0] + sway, OAK_CROWN[1]
    rx0, ry0 = 74, 50  # the core; lobes of different sizes make the outline
    lumps = [(cx0, cy0, rx0, ry0)]
    for i in range(20):  # big and small lobes, unevenly spaced, so the silhouette is irregular
        a = i / 20 * 2 * math.pi + rng.uniform(-0.2, 0.2)
        reach = rng.uniform(0.78, 1.08)
        lumps.append((cx0 + math.cos(a) * rx0 * reach, cy0 + math.sin(a) * ry0 * reach - (5 if math.sin(a) < 0 else 0),
                      rng.uniform(11, 27), rng.uniform(9, 20)))
    lobes = list(lumps)
    def in_lobes(x, y):
        return any(((x - lx) / lrx) ** 2 + ((y - ly) / lry) ** 2 <= 1 for lx, ly, lrx, lry in lobes)
    for _ in range(26):  # small leafy tufts sitting on the edge, half poking out
        a = rng.uniform(0, 2 * math.pi)
        if math.sin(a) > 0.75:
            continue  # not hanging below the crown's middle, where the trunk is
        d = 0.0
        while in_lobes(cx0 + math.cos(a) * d * 1.4, cy0 + math.sin(a) * d) and d < 120:
            d += 1  # walk out from the centre to the edge
        lumps.append((cx0 + math.cos(a) * d * 1.4, cy0 + math.sin(a) * d, rng.uniform(3, 6), rng.uniform(2.5, 4.5)))
    notches = []  # bites out of the edge give it corners
    for _ in range(9):
        a = rng.uniform(0, 2 * math.pi)
        d = 0.0
        while in_lobes(cx0 + math.cos(a) * d * 1.4, cy0 + math.sin(a) * d) and d < 120:
            d += 1
        notches.append((cx0 + math.cos(a) * (d * 1.4 + 2), cy0 + math.sin(a) * (d + 1.5), rng.uniform(4, 7), rng.uniform(3, 5)))
    holes = [(cx0 - 30 + rng.uniform(-4, 4), cy0 + 18, 3.6, 2.6), (cx0 + 36 + rng.uniform(-4, 4), cy0 - 10, 3.0, 2.2),
             (cx0 + 6, cy0 + 30, 2.6, 2.0)]
    def inside(x, y, shapes):
        return any(((x - lx) / lrx) ** 2 + ((y - ly) / lry) ** 2 <= 1 for lx, ly, lrx, lry in shapes)
    def in_crown(x, y):
        return inside(x, y, lumps) and not inside(x, y, notches) and not inside(x, y, holes)
    # calm colour: broad patches that flow from golden on top, through orange, to deep red and brown below
    cell = {}
    def colour(x, y):
        key = ((x + 3 * ((y // 4) % 2)) // 6, y // 4)  # leaf clusters about 6 x 4, staggered like brickwork
        if key not in cell:
            kx, ky = key[0] * 6, key[1] * 4
            top = max(0.0, min(1.0, (ky - (cy0 - ry0 - 20)) / (2 * ry0 + 40)))  # 0 at the top, 1 at the bottom
            side = (kx - cx0) / (rx0 + 30)                                     # -1 left .. 1 right
            wave = (math.sin(kx * 0.045 + 1.3) + math.sin(ky * 0.06 + 0.4)) / 4  # gentle, wide drifts
            v = top * 0.42 + side * 0.06 + wave * 1.1 + 0.12 + rng.uniform(-0.07, 0.07)
            v = 0.5 + (v - 0.5) * 0.7  # fewer extremes: mostly warm orange and red, a little gold and brown
            cuts = CROWN_COLOURS[season]
            mat = next(m for cut, m in cuts if v < cut)
            # near a boundary, mix the two colours in a checkerboard so the change is soft
            for cut, m in cuts[:-1]:
                if abs(v - cut) < 0.045 and (key[0] + key[1]) % 2:
                    nxt = cuts[[c_ for c_, _ in cuts].index(cut) + 1][1]
                    mat = nxt if v < cut else m
            cell[key] = (mat, rng.uniform(-0.04, 0.04))
        return cell[key]
    for y in range(0, 160):
        for x in range(0, OAK_W):
            if not in_crown(x + 0.5, y + 0.5):
                continue
            nx, ny = (x + 0.5 - cx0) / (rx0 + 16), (y + 0.5 - cy0) / (ry0 + 14)
            mat, jitter = colour(x, y)
            lum = Canvas._shade(max(-1, min(1, nx)), max(-1, min(1, ny)), jitter)
            if rng.random() < 0.012:  # an occasional small shadow between leaves
                lum -= 0.25
            c.mat[y][x], c.lum[y][x], c.fixed[y][x] = mat, lum, None
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

def _daffodil_head(c, x, y, size=1.0):
    """A daffodil flower at (x, y), seen from the side and facing right: a round ring of yellow petals with a
    few pointed tips poking out of its edge, and an orange trumpet sticking out of the front with a flared rim.
    Placed pixel by pixel, so it stays crisp at this size."""
    cx, cy = int(round(x)), int(round(y))
    big = size >= 1
    r2 = 5.5 if big else 2.5  # the petal ring, centred a little behind the trumpet
    reach = 2 if big else 1
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if dx * dx + dy * dy <= r2:
                _px(c, cx - 1 + dx, cy + dy, "daffodil", 3 if dy < 0 else 2 if dy == 0 else 1)
    # pointed petal tips poking out past the ring: up, down, and back (two at the back on the big ones)
    _px(c, cx - 1, cy - reach - 1, "daffodil", 3)
    _px(c, cx - 1, cy + reach + 1, "daffodil", 1)
    for ty in ((-1, 1) if big else (0,)):
        _px(c, cx - 2 - reach, cy + ty, "daffodil", 2)
    _px(c, cx, cy, "daffodil_cup", 1)  # the trumpet, sticking out of the front...
    _px(c, cx + 1, cy, "daffodil_cup", 2)
    for dy in ((-1, 0, 1) if big else (0, 1)):  # ...with a frilly, flared rim
        _px(c, cx + 2, cy + dy, "daffodil_cup", 3 if dy <= 0 else 2)


def _twig(c, x1, y1, x2, y2, mat="bark", level=1):
    """A 1-pixel twig."""
    steps = int(max(abs(x2 - x1), abs(y2 - y1))) + 1
    for i in range(steps + 1):
        _px(c, round(x1 + (x2 - x1) * i / steps), round(y1 + (y2 - y1) * i / steps), mat, level)


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


# -- visitors ----------------------------------------------------------------------------------------

def squirrel(pose="run", t=0.0, acorn_in_mouth=False):
    """32 x 32, faces right."""
    c = Canvas(32, 32)
    s = math.sin(t * 2 * math.pi)
    if pose == "run":
        y = 22 - abs(s) * 2
        tail_pts = bezier((9, y), (2, y - 6 - s * 2), (6, y - 14 - s), 7)
        c.chain(tail_pts, [2.5, 3.6, 4.4, 4.6, 4.2, 3.4, 2.0][:len(tail_pts)] + [2.0] * 10, ["squirrel"] * 20)
        c.capsule(11, y + 2, 7 - s * 3, 29, 2.0, 1.4, "squirrel", -0.3)
        c.ellipse(14, y, 6.5, 4.2 - s * 0.6, "squirrel", angle=-6 - s * 4)
        c.ellipse(15, y + 2, 4, 1.6, "white", bias=-0.2)
        c.capsule(18, y + 2, 21 + s * 3, 29, 1.6, 1.2, "squirrel")
        hx, hy = 21, y - 4
    elif pose == "sit":  # upright, nibbling or holding
        tail_pts = bezier((10, 27), (2, 20), (7, 6), 7)
        c.chain(tail_pts, [2.6, 3.6, 4.4, 4.8, 4.6, 4.0, 3.0][:len(tail_pts)] + [2.0] * 10, ["squirrel"] * 20)
        c.ellipse(15, 23, 5.2, 6.8, "squirrel", angle=-10)
        c.ellipse(17, 24, 2.6, 4.5, "white", bias=-0.1)
        c.capsule(13, 28, 19, 29.5, 1.8, 1.5, "squirrel")
        hx, hy = 18, 14 + s * 0.6
    else:  # dig: nose down, paws working
        y = 23
        tail_pts = bezier((9, y), (3, y - 10), (9, y - 16), 7)
        c.chain(tail_pts, [2.5, 3.5, 4.2, 4.5, 4.2, 3.2, 2.0][:len(tail_pts)] + [2.0] * 10, ["squirrel"] * 20)
        c.ellipse(14, y + 1, 6, 4, "squirrel", angle=20)
        c.capsule(19, y + 3, 22 + s * 2, 29, 1.6, 1.2, "squirrel")
        hx, hy = 21, y + 3
        if (t * 4) % 2 < 1:
            c.ellipse(6, 27, 1, 1, "dirt")
            c.ellipse(4, 24, 1, 1, "dirt")
    if pose == "sit":
        c.capsule(19, 20, 21, 18, 1.2, 1.1, "squirrel")  # paws up to the mouth
    c.ellipse(hx, hy, 4.0, 3.4, "squirrel")
    c.ellipse(hx + 3, hy + 0.8, 2.2, 1.6, "squirrel")
    c.polygon([(hx - 2, hy - 2), (hx - 1, hy - 6), (hx + 1, hy - 2.5)], "squirrel", lum=0.5)
    c.pixel(hx + 1, hy - 1, "eye")
    c.pixel(hx + 5, hy, "nose")
    if acorn_in_mouth or pose == "sit":
        c.ellipse(hx + 4.5, hy + 2.5, 1.6, 1.9, "acorn")
        c.ellipse(hx + 4.5, hy + 1.2, 1.8, 1.0, "cap")
    return c.to_image()


def jay(pose="perch", t=0.0):
    """24 x 24 blue jay, faces right."""
    c = Canvas(24, 24)
    s = math.sin(t * 2 * math.pi)
    if pose == "fly":
        c.ellipse(12, 12, 6.0, 3.2, "jay")
        c.ellipse(13, 13.5, 4, 1.4, "white", bias=-0.2)
        wing_y = 12 - s * 6
        c.polygon([(9, 11), (13, 11), (8 - s, wing_y - 1), (5, wing_y)], "jay", lum=0.7)
        c.capsule(6, 12, 1, 10 + s, 1.6, 1.2, "jay", -0.3)  # tail
        hx, hy = 18, 10
    else:  # perch / hop
        hop = max(0.0, s) * 2 if pose == "hop" else 0.0
        c.capsule(9, 15 - hop, 3, 20 - hop, 1.6, 1.3, "jay", -0.3)  # tail
        c.ellipse(12, 14 - hop, 5.0, 4.0, "jay", angle=-15)
        c.ellipse(14, 16 - hop, 3, 2.2, "white", bias=-0.1)
        c.polygon([(9, 12 - hop), (14, 12 - hop), (8, 17 - hop)], "jay", lum=0.2)
        c.capsule(12, 18 - hop, 12, 22, 0.5, 0.5, "dark")
        c.capsule(14, 18 - hop, 14, 22, 0.5, 0.5, "dark")
        hx, hy = 16, 9 - hop
    c.ellipse(hx, hy, 3.2, 2.9, "jay")
    c.polygon([(hx - 2, hy - 2), (hx - 4, hy - 6), (hx + 1, hy - 2.6)], "jay", lum=0.6)  # crest
    c.ellipse(hx + 0.6, hy + 1.6, 2.4, 1.2, "white")
    c.capsule(hx - 2, hy + 3, hx + 2, hy + 3, 0.6, 0.6, "dark")  # black collar
    c.polygon([(hx + 2.4, hy - 0.6), (hx + 5.4, hy + 0.4), (hx + 2.4, hy + 1.2)], "dark", lum=0.3)
    c.pixel(hx + 1, hy - 1, "eye")
    return c.to_image()


def woolly(t=0.0):
    """24 x 10 woolly bear caterpillar: black ends, rusty middle, fuzzy. Crawls right."""
    c = Canvas(24, 10)
    n = 9
    for i in range(n):
        x = 3 + i * 2.1 + (math.sin(t * 2 * math.pi - i * 0.7) * 0.6)
        y = 6.5 - max(0.0, math.sin(t * 2 * math.pi - i * 0.7)) * 1.6
        mat = "woolly_dark" if i < 2 or i > n - 3 else "woolly_rust"
        c.ellipse(x, y, 1.8, 2.0, mat)
    # fuzz: bristle pixels along the top
    for i in range(n):
        x = 3 + i * 2.1
        y = 6.5 - max(0.0, math.sin(t * 2 * math.pi - i * 0.7)) * 1.6
        mat = "woolly_dark" if i < 2 or i > n - 3 else "woolly_rust"
        c.pixel(x, y - 3, mat, 3 if i % 2 else 2)
    return c.to_image()


# -- pumpkins ----------------------------------------------------------------------------------------

COMMON.update({
    "pumpkin": ("#93380a", "#d0600f", "#ef8722", "#fbb556", "#4e1e04"),
    "pumpkin_young": ("#8a6a10", "#c49a1c", "#e2bd34", "#f2d872", "#4a3806"),
    "pumpkin_green": ("#38501a", "#557624", "#759a32", "#9cbc58", "#1e2e0a"),
    "vine": ("#2c4a14", "#43681e", "#5f8a2c", "#86ae4c", "#16280a"),
    "stem": ("#4a3a16", "#6e5826", "#8e7638", "#ae9652", "#271e0a"),
    "flower": ("#b07c0e", "#e0a818", "#f6cc3a", "#fde67e", "#5e3e04"),
})


PUMPKIN_SHAPES = {"round": (1.0, 1.0), "tall": (0.78, 1.32), "squat": (1.28, 0.74)}


def _pumpkin_body(c, cx, base, size, mat, shape="round", squash=(1.0, 1.0)):
    """A ribbed pumpkin sitting on the ground: side ribs first (darker), the front rib last."""
    wide, high = PUMPKIN_SHAPES[shape]
    wide, high = wide * squash[0], high * squash[1]
    w, h = 9.0 * size * wide, 6.4 * size * high
    cy = base - h
    for dx, rx, bias in ((-0.55, 0.5, -0.25), (0.55, 0.5, -0.25), (-0.28, 0.55, -0.08), (0.28, 0.55, -0.08),
                         (0.0, 0.5, 0.08)):
        c.ellipse(cx + dx * w, cy, rx * w, h, mat, bias=bias)
    return cy - h


PUMPKIN_SIZES = {"s": 0.75, "m": 1.0, "l": 1.3}


COMMON.update({"glow": ("#c26a0a", "#f0a018", "#ffd040", "#fff2a0", "#6a3204")})


def jack_face(c, cx, cy, size, flicker):
    """Carved triangle eyes, a nose and a toothy grin, glowing from the candle inside."""
    lit = 2 if flicker else 3
    def tri(x, y, w, h):
        for row in range(int(h) + 1):
            half = w * row / max(1, h) / 2
            for dx in range(int(-half), int(half) + 1):
                c.pixel(x + dx, y + row, "glow", lit)
    s = size
    tri(cx - 3.6 * s, cy - 3.4 * s, 4.0 * s, 2.8 * s)
    tri(cx + 3.6 * s, cy - 3.4 * s, 4.0 * s, 2.8 * s)
    tri(cx, cy - 0.6 * s, 1.6 * s, 1.4 * s)
    for dx in range(int(-6 * s), int(6 * s) + 1):  # the grin, curving up at the ends, with two teeth
        y = cy + 2.4 * s - (abs(dx) / (6 * s)) ** 2 * 2 * s
        for dy in range(int(1.6 * s) + 1):
            if not (abs(dx - 2 * s) < 0.8 and dy == 0) and not (abs(dx + 2 * s) < 0.8 and dy == 0):
                c.pixel(cx + dx, y + dy, "glow", lit if dy else 1)


def pumpkin(stage, sway=0.0, grow=1.0, shape="round", jack=False):
    """44 x 36. Stages: 0 sprout, 1 vine with a flower, 2 small green, 3 yellow-orange, 4 ripe.
    grow scales the pumpkin itself (small, medium or large pumpkins)."""
    c = Canvas(44, 36)
    ground = 30
    if stage == 0:  # a sprout: a little stem with two seed leaves
        c.ellipse(20, ground + 0.5, 3.5, 1.2, "dirt")
        tip = (20 + sway * 0.5, ground - 6)
        c.capsule(20, ground, tip[0], tip[1], 0.8, 0.7, "vine")
        c.ellipse(tip[0] - 2.4, tip[1] - 0.6, 2.4, 1.3, "vine", angle=-20)
        c.ellipse(tip[0] + 2.4, tip[1] - 0.6, 2.4, 1.3, "vine", angle=20)
        return c.to_image()
    # the vine along the ground, with leaves (grows longer each stage)
    reach = (4, 13, 15, 16, 17)[stage]
    c.capsule(20 - reach, ground, 20 + reach * 0.8, ground - 0.5, 0.9, 0.8, "vine")
    leaves = [(-reach + 2, 1.0), (reach * 0.7, 1.0)] if stage else [(-2.5, 0.8), (2.5, 0.8)]
    if stage >= 2:
        leaves.append((-reach * 0.5, 1.2))
    for dx, size in leaves:
        lx, ly = 20 + dx, ground - 3.2 * size + sway * 0.4
        c.ellipse(lx, ly, 3.4 * size, 2.6 * size, "vine", angle=-20 if dx < 0 else 20)
        c.capsule(lx, ly + 1.5 * size, lx, ground, 0.5, 0.5, "vine", bias=-0.3)
    if stage == 0:
        c.capsule(20, ground, 20 + sway * 0.5, ground - 5, 0.8, 0.7, "vine")
        return c.to_image()
    if stage == 1:  # a yellow flower on a curl of vine
        c.capsule(22, ground, 23 + sway * 0.5, ground - 9, 0.7, 0.6, "vine")
        fx, fy = 23 + sway * 0.5, ground - 11
        for a in range(5):
            ang = a / 5 * 2 * math.pi
            c.ellipse(fx + math.cos(ang) * 2.0, fy + math.sin(ang) * 2.0, 1.6, 1.6, "flower")
        c.pixel(fx, fy, "stem", 1)
        return c.to_image()
    size, mat = {2: (0.55, "pumpkin_green"), 3: (0.8, "pumpkin_young"), 4: (1.15, "pumpkin")}[stage]
    size *= grow
    top = _pumpkin_body(c, 20, ground + 0.5, size, mat, shape if stage >= 3 else "round")
    if jack and stage == 4:
        jack_face(c, 20, top + PUMPKIN_SHAPES[shape][1] * 6.4 * size, size * 0.95 * min(1.0, PUMPKIN_SHAPES[shape][1]) ** 0.5,
                  flicker=sway != 0)
    # the stem, and a curly tendril on the ripe one
    c.capsule(20, top + 2, 21 + size, top - 1.5 * size, 1.2 * size, 0.9 * size, "stem")
    if stage == 4:
        for i in range(6):
            a = i * 1.1
            c.pixel(23 + math.cos(a) * 2 + i * 0.6, top - 2 + math.sin(a) * 1.6, "vine", 2)
    return c.to_image()


COMMON.update({
    "pulp": ("#c88a2a", "#e6b04a", "#f4cc72", "#fbe6aa", "#6e4a10"),
    "seed": ("#b8ae8a", "#ded6b4", "#f2ecd2", "#ffffff", "#6e664a"),
})
GIANT = 2.3  # how much bigger than a ripe medium pumpkin a giant one gets


def pumpkin_giant(shape="round", sway=0.0, jack=False):
    """72 x 56: a pumpkin that kept on growing. Too big: it creaks and sags a little."""
    c = Canvas(72, 56)
    ground = 50
    cx = 34
    c.capsule(cx - 30, ground, cx + 28, ground - 0.5, 1.1, 1.0, "vine")
    for dx, size in ((-26, 1.4), (24, 1.3), (-14, 1.6)):
        lx, ly = cx + dx, ground - 4 * size + sway * 0.4
        c.ellipse(lx, ly, 3.6 * size, 2.8 * size, "vine", angle=-20 if dx < 0 else 20)
    sag = (1.04, 0.96)  # its own weight squashes it
    top = _pumpkin_body(c, cx, ground + 0.5, GIANT, "pumpkin", shape, squash=sag)
    if jack:
        high = PUMPKIN_SHAPES[shape][1] * sag[1]
        jack_face(c, cx, top + high * 6.4 * GIANT, GIANT * 0.95 * min(1.0, high) ** 0.5, flicker=sway != 0)
    c.capsule(cx, top + 3, cx + 2, top - 3, 2.2, 1.6, "stem")
    return c.to_image()


def pumpkin_burst(shape="round", t=0.0):
    """72 x 56: a giant pumpkin splitting open. t: 0 a crack starts at the top .. 1 split in two, seeds out."""
    c = Canvas(72, 56)
    ground = 50
    cx = 34
    wide, high = PUMPKIN_SHAPES[shape]
    c.capsule(cx - 30, ground, cx + 28, ground - 0.5, 1.1, 1.0, "vine")
    if t < 0.6:  # a jagged crack running down from the stem
        top = _pumpkin_body(c, cx, ground + 0.5, GIANT, "pumpkin", shape, squash=(1.04, 0.96))
        length = (ground - top) * t / 0.6
        y, x, k = top + 1, cx, 0
        while y < top + 1 + length:
            c.pixel(x, y, "stem", 0)
            c.pixel(x + 1, y, "stem", 0)
            x += 1 if k % 3 == 0 else -1 if k % 3 == 1 else 0
            y += 1
            k += 1
        c.capsule(cx, top + 3, cx + 2, top - 3, 2.2, 1.6, "stem")
        return c.to_image()
    # split: two halves rolled apart, the pulpy, seedy inside showing, seeds spilled on the ground
    open_by = (t - 0.6) / 0.4
    rng = random.Random(9)
    sq = 0.92 - open_by * 0.2
    for side in (-1, 1):
        hx = cx + side * (4 + open_by * 7)
        half = Canvas(72, 56)
        hy_top = _pumpkin_body(half, hx, ground + 0.5, GIANT * 0.85, "pumpkin", shape, squash=(0.9, sq))
        cut = hx - side * 1
        for y in range(56):
            for x in range(72):
                if half.mat[y][x] is not None and (x - cut) * side >= 0:
                    c.mat[y][x], c.lum[y][x] = half.mat[y][x], half.lum[y][x]
        h = ground - hy_top
        c.ellipse(cut + side * 2.5, ground - h * 0.48, 3.2, h * 0.42, "pulp", bias=0.2)  # the cut face
        for _ in range(7):
            c.pixel(cut + side * rng.uniform(1, 4), ground - h * rng.uniform(0.2, 0.75), "seed", 2)
    for _ in range(int(6 + open_by * 14)):
        sx, sy = cx + rng.uniform(-6, 6) * (0.6 + open_by), ground - rng.uniform(0, 2)
        c.pixel(sx, sy, "seed", rng.choice((1, 2)))
    return c.to_image()


def chip(mat, spin, size=1.0):
    """6 x 6: a little flying bit of something (a corn kernel, a chunk of pumpkin), turning over."""
    c = Canvas(6, 6)
    a = math.radians(spin * 45)
    c.ellipse(3, 3, 1.5 * size, 1.0 * size, mat, angle=math.degrees(a))
    return c.to_image(outline=False)


# -- geese ---------------------------------------------------------------------------------------------

COMMON.update({
    "goose": ("#4a3c30", "#6c5a48", "#8c7862", "#ab9882", "#241c14"),
    "goose_black": ("#0c0a0a", "#1a1616", "#2a2424", "#3e3636", "#040303"),
    "goose_pale": ("#a8a090", "#cfc8b8", "#e8e2d4", "#ffffff", "#5c564a"),
    "bubble": ("#d8d8d8", "#ffffff", "#ffffff", "#ffffff", "#2a2a2a"),
})


def goose(pose="walk", t=0.0):
    """32 x 32 Canada goose facing right. pose: walk, honk (neck up, beak open), fly."""
    c = Canvas(32, 32)
    s = math.sin(t * 2 * math.pi)
    if pose == "fly":
        y = 16
        c.capsule(9, y, 3, y - 1, 2.2, 1.6, "goose_pale")              # white rump and tail
        c.ellipse(14, y, 7.5, 3.6, "goose")
        c.ellipse(15, y + 2, 5.0, 1.6, "goose_pale", bias=-0.2)
        c.capsule(20, y - 1, 27, y - 3, 1.5, 1.2, "goose_black")         # neck stretched forward
        c.ellipse(28, y - 3.4, 2.2, 1.7, "goose_black")
        c.ellipse(27.6, y - 2.3, 1.2, 0.8, "goose_pale")                 # chin strap
        c.capsule(29.5, y - 3.2, 31.2, y - 2.8, 0.7, 0.5, "goose_black")
        wy = y - 1 - s * 8
        c.polygon([(10, y - 1), (17, y - 1), (13 - s, wy - 1), (9, wy)], "goose", lum=0.6)
        return c.to_image()
    step = s if pose == "walk" else 0.0
    # legs
    c.capsule(14, 22, 13 - step * 2, 29, 0.6, 0.6, "goose_black")
    c.capsule(17, 22, 18 + step * 2, 29, 0.6, 0.6, "goose_black")
    c.capsule(13 - step * 2, 29.5, 15.5 - step * 2, 29.5, 0.6, 0.6, "goose_black")
    c.capsule(18 + step * 2, 29.5, 20.5 + step * 2, 29.5, 0.6, 0.6, "goose_black")
    # body, folded wing, white rump
    c.capsule(8, 18, 4, 16, 2.2, 1.4, "goose_pale")
    c.ellipse(15, 18 + abs(step) * 0.5, 8.0, 5.0, "goose", angle=-8)
    c.ellipse(16, 21, 5.5, 2.0, "goose_pale", bias=-0.2)
    c.ellipse(13, 17, 5.5, 3.0, "goose", bias=-0.25, angle=-10)
    # neck and head: tall when honking
    if pose == "honk":
        top = (24, 3 + t * 2)
        c.capsule(21, 15, top[0], top[1] + 3, 1.7, 1.4, "goose_black")
        c.ellipse(top[0] + 1, top[1] + 1, 2.4, 1.9, "goose_black", angle=-25)
        c.ellipse(top[0] + 0.4, top[1] + 2.2, 1.2, 0.8, "goose_pale")
        open_by = 1.2 if t < 0.6 else 0.3
        c.capsule(top[0] + 3, top[1], top[0] + 6, top[1] - 2.0, 0.6, 0.5, "goose_black")
        c.capsule(top[0] + 3, top[1] + 0.8, top[0] + 6, top[1] + 0.8 + open_by - 1.0, 0.5, 0.4, "goose_black")
        c.pixel(top[0] + 1, top[1], "eye")
    else:
        bob = s * 1.2
        c.capsule(21, 15, 24 + bob * 0.5, 7 + abs(bob) * 0.4, 1.7, 1.4, "goose_black")
        hx, hy = 25 + bob * 0.5, 6 + abs(bob) * 0.4
        c.ellipse(hx, hy, 2.4, 1.8, "goose_black")
        c.ellipse(hx - 0.4, hy + 1.1, 1.2, 0.8, "goose_pale")
        c.capsule(hx + 2, hy + 0.2, hx + 4.5, hy + 0.5, 0.7, 0.5, "goose_black")
    return c.to_image()


def goose_far(t=0.0):
    """12 x 8 distant goose silhouette for a migrating V, flying left (drawn facing right; mirrored)."""
    c = Canvas(14, 10)
    s = math.sin(t * 2 * math.pi)
    c.capsule(2, 5, 10, 5, 1.2, 0.9, "goose_black")
    c.ellipse(11.5, 4.8, 1.2, 1.0, "goose_black")
    c.capsule(6.5, 5, 4.5, 5 - s * 4.2, 1.1, 0.6, "goose")  # wing beating up and down
    c.capsule(7.5, 5, 6.0, 5 - s * 3.6, 0.9, 0.5, "goose", bias=-0.3)
    return c.to_image(outline=False)


def honk_bubble():
    """A little speech bubble that says HONK! in a hand-made pixel font."""
    letters = {
        "H": ["101", "101", "111", "101", "101"],
        "O": ["111", "101", "101", "101", "111"],
        "N": ["1001", "1101", "1011", "1001", "1001"],
        "K": ["101", "110", "100", "110", "101"],
        "!": ["1", "1", "1", "0", "1"],
    }
    from PIL import Image
    w, h = 30, 14
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    edge, fill, ink = (42, 42, 42, 255), (255, 255, 255, 255), (30, 30, 30, 255)
    for y in range(1, h - 4):
        for x in range(1, w - 1):
            px[x, y] = fill
    for x in range(1, w - 1):
        px[x, 0], px[x, h - 4] = edge, edge
    for y in range(1, h - 4):
        px[0, y], px[w - 1, y] = edge, edge
    for (x, y) in ((4, h - 3), (5, h - 3), (4, h - 2)):  # the tail of the bubble
        px[x, y] = edge
    px[5, h - 4] = fill
    x0 = 3
    for ch in "HONK!":
        for row, bits in enumerate(letters[ch]):
            for col, bit in enumerate(bits):
                if bit == "1":
                    px[x0 + col, 2 + row] = ink
        x0 += len(letters[ch][0]) + 1
    return img


# -- the scarecrow -------------------------------------------------------------------------------------

COMMON.update({
    "post": ("#4a3420", "#6a4a2e", "#8a643e", "#a67e54", "#26180c"),
    "sack": ("#8a7350", "#b09a70", "#cbb88e", "#e2d4b0", "#4a3c26"),
    "straw": ("#9a7a1e", "#c8a232", "#e2c050", "#f2dc86", "#55400c"),
    "plaid_red": ("#6e1a16", "#a02822", "#c2402e", "#da6650", "#3a0a08"),
    "plaid_dark": ("#2a1414", "#3e2020", "#542e2a", "#6c403a", "#140808"),
    "denim": ("#2c3a5a", "#3e5280", "#566ea0", "#7c92bc", "#141c30"),
    "hat": ("#6a4e1e", "#8e6c2c", "#ae8a3e", "#c8a65a", "#36260c"),
    "patch": ("#4a6a2a", "#628a38", "#7ea64c", "#9cc06a", "#24360e"),
})


def scarecrow(sway=0.0, surprised=False, hat_up=0.0, hat=True):
    """48 x 88: a friendly scarecrow on a post, swaying a little. Faces you. surprised: wide eyes and an
    O mouth; hat_up lifts the hat off its head. hat=False: the crows have run off with it."""
    c = Canvas(48, 88)
    s = sway * 0.6
    # the post and cross-bar
    c.capsule(24, 86, 24, 26, 1.6, 1.4, "post")
    c.capsule(8 + s * 0.3, 36, 40 + s * 0.3, 36, 1.3, 1.3, "post")
    # trousers, then the shirt over the cross-bar
    c.capsule(20 + s * 0.2, 56, 19 + s * 0.2, 70, 3.0, 2.6, "denim")
    c.capsule(28 + s * 0.2, 56, 29 + s * 0.2, 70, 3.0, 2.6, "denim")
    c.ellipse(28.5 + s * 0.2, 62, 1.6, 1.6, "patch")  # a patched knee
    for x in (18 + s * 0.2, 30 + s * 0.2):  # straw poking out of the trouser legs
        for dx in (-1.5, 0, 1.5):
            c.capsule(x, 71, x + dx, 75, 0.5, 0.4, "straw")
    c.ellipse(24 + s * 0.4, 47, 8.5, 10.5, "plaid_red")
    for sleeve in (-1, 1):
        c.capsule(24 + s * 0.4, 39, 24 + sleeve * 13 + s * 0.3, 37, 3.2, 2.6, "plaid_red")
        hand = 24 + sleeve * 17 + s * 0.3
        for dy in (-1.5, 0, 1.5):  # straw hands
            c.capsule(24 + sleeve * 15 + s * 0.3, 37, hand + sleeve * 1.5, 37 + dy, 0.6, 0.4, "straw")
    # plaid: darker stripes across the shirt and sleeves
    for y in range(c.h):
        for x in range(c.w):
            if c.mat[y][x] == "plaid_red" and (x % 5 == 0 or y % 5 == 0):
                c.mat[y][x] = "plaid_dark"
    # buttons down the front
    for y in (42, 47, 52):
        c.pixel(24 + s * 0.4, y, "straw", 3)
    # head: a burlap sack with a stitched smile, a rope at the neck
    hx, hy = 24 + s, 26
    c.ellipse(hx, hy, 6.5, 7.0, "sack")
    c.capsule(hx - 3, hy + 6.5, hx + 3, hy + 6.5, 0.8, 0.8, "straw")
    if surprised:
        for ex in (-3, 2):  # wide button eyes with a glint
            for dx in (0, 1, 2):
                for dy in (-2, -1, 0):
                    c.pixel(hx + ex + dx, hy + dy, "plaid_dark", 0)
            c.pixel(hx + ex + 1, hy - 2, "bubble", 3)
        for dx, dy in ((-1, 2), (0, 2), (1, 2), (-2, 3), (2, 3), (-2, 4), (2, 4), (-1, 5), (0, 5), (1, 5)):
            c.pixel(hx + dx, hy + dy, "plaid_dark", 0)  # an O mouth
    else:
        for ex in (-2.5, 2.5):  # button eyes
            c.pixel(hx + ex, hy - 1, "plaid_dark", 1)
            c.pixel(hx + ex + 1, hy - 1, "plaid_dark", 1)
            c.pixel(hx + ex, hy, "plaid_dark", 1)
            c.pixel(hx + ex + 1, hy, "plaid_dark", 1)
        for i, dx in enumerate(range(-3, 4)):  # stitched smile
            c.pixel(hx + dx, hy + 3 + (0 if abs(dx) < 2 else -1), "plaid_dark", 0 if i % 2 else 1)
    c.pixel(hx, hy + 1, "pumpkin", 2)  # a little orange nose
    if hat:
        _straw_hat(c, hx, hy - hat_up)
    else:  # a tuft of straw sticking up out of the sack where the hat should be
        for dx in (-3, -1, 1, 3):
            c.capsule(hx + dx * 0.6, hy - 6, hx + dx * 1.3, hy - 10 - abs(dx) * 0.3, 0.5, 0.4, "straw")
    for dx in (-8, -5, 6, 9):  # straw hair under the brim
        c.capsule(hx + dx * 0.7, hy - 4, hx + dx, hy - 1, 0.5, 0.4, "straw")
    return c.to_image()


def _straw_hat(c, hx, hy, k=1.0):
    """The scarecrow's floppy straw hat, sitting on a head centred at (hx, hy). k scales it."""
    c.capsule(hx - 10 * k, hy - 6 * k, hx + 10 * k, hy - 5 * k, 1.6 * k, 1.4 * k, "hat")
    c.ellipse(hx, hy - 9 * k, 5.8 * k, 4.2 * k, "hat")
    c.capsule(hx - 5.5 * k, hy - 7 * k, hx + 5.5 * k, hy - 7 * k, 0.8 * k, 0.8 * k, "plaid_red")  # hat band


def scarecrow_hat():
    """24 x 12: the scarecrow's hat on its own, lying where a crow dropped it."""
    c = Canvas(24, 12)
    _straw_hat(c, 12, 16)
    return c.to_image()


# -- the corn field ------------------------------------------------------------------------------------

COMMON.update({
    "corn_leaf": ("#2e5214", "#46761e", "#62962c", "#8ab84c", "#16300a"),
    "corn_dry": ("#8a6a26", "#b08e3a", "#ccac52", "#e4cc7e", "#4a360e"),
    "cob": ("#b88a10", "#e0b21e", "#f4d040", "#fbe88a", "#5e4206"),
    "husk": ("#5c7a26", "#7c9c34", "#9cba4e", "#c0d67a", "#2c400e"),
})

CORN_STALKS = [(10, 0.82), (28, 1.0), (46, 0.9), (64, 1.06), (82, 0.88), (100, 0.97)]  # x, height share


def corn(stage, sway=0.0):
    """120 x 100: a row of six corn stalks. Stages: 0 shoots, 1 knee-high, 2 tall, 3 tassels and ears,
    4 dried golden for autumn. sway rustles the tops."""
    c = Canvas(120, 100)
    ground = 98
    c.capsule(2, ground + 0.5, 118, ground + 0.5, 1.4, 1.4, "dirt")
    full = (12, 34, 70, 86, 86)[stage]
    green, leafy = ("corn_dry", "corn_dry") if stage == 4 else ("corn_leaf", "corn_leaf")
    for i, (x, share) in enumerate(CORN_STALKS):
        h = full * share
        lean = sway * (0.5 + 0.5 * (i % 2)) * (h / 86)
        top = (x + lean, ground - h)
        c.capsule(x, ground, top[0], top[1], 1.6 if stage else 1.0, 1.0, green)
        # long leaves arching out and drooping, alternating sides up the stalk
        for k in range(1 if stage == 0 else 4 if stage < 2 else 6):
            y = ground - h * (0.22 + 0.13 * k)
            side = 1 if (k + i) % 2 else -1
            reach = (6 if stage == 0 else 11) * (1.0 - 0.06 * k)
            mid = (x + lean * (1 - y / ground) + side * reach * 0.6, y - 4)
            tip = (x + lean * (1 - y / ground) + side * reach, y + 2 + (3 if stage == 4 else 0))
            c.capsule(x + lean * (1 - y / ground), y, mid[0], mid[1], 1.2, 0.9, leafy)
            c.capsule(mid[0], mid[1], tip[0], tip[1], 0.9, 0.4, leafy, bias=-0.15)
        if stage >= 3:
            # the tassel on top, and an ear of corn halfway up, its husk peeled back a little
            for dx in (-2.5, 0, 2.5):
                c.capsule(top[0], top[1], top[0] + dx + sway * 0.5, top[1] - 6, 0.6, 0.4, "straw")
            ey = ground - h * 0.5
            side = -1 if i % 2 else 1
            c.ellipse(x + side * 3 + lean * 0.5, ey, 1.9, 4.2, "cob", angle=side * 18)
            c.capsule(x + side * 2 + lean * 0.5, ey + 4, x + side * 4.5 + lean * 0.5, ey - 1, 1.0, 0.6, "husk" if stage == 3 else "corn_dry")
    return c.to_image()


# -- the hoe and the den -------------------------------------------------------------------------------

COMMON.update({
    "handle": ("#6a4622", "#8e6232", "#ae7e46", "#c89c62", "#36220e"),
    "iron": ("#3a3c42", "#5a5e66", "#80848c", "#b0b4ba", "#1c1d20"),
    "earth": ("#4a3420", "#694a2e", "#86603c", "#a07a50", "#28190c"),
    "den_dark": ("#100a06", "#1c120c", "#2a1c12", "#3a281a", "#080503"),
    "grass": ("#3e5a1c", "#5a7c26", "#789e34", "#9cbe54", "#1e300a"),
})


def hoe():
    """24 x 60: a garden hoe stuck in the ground, leaning a little."""
    c = Canvas(24, 60)
    c.capsule(14, 58, 9, 6, 1.1, 1.0, "handle")
    c.capsule(9, 6, 9, 4, 1.4, 1.4, "handle")
    c.polygon([(8, 4), (16, 3), (17, 9), (13, 8)], "iron", lum=0.55)   # the blade
    c.capsule(9, 5, 13, 4.5, 0.8, 0.8, "iron", bias=-0.3)              # its neck
    c.ellipse(14, 58.5, 3.5, 1.2, "dirt")
    return c.to_image()


COMMON.update({
    "stone": ("#4c4844", "#6e6862", "#928a82", "#b8b0a6", "#26231f"),
    "stone_dark": ("#3a3632", "#55504a", "#706a62", "#8c857c", "#1c1a17"),
    "moss": ("#3a5418", "#557422", "#71922e", "#94b04c", "#1c2c08"),
})


def _rock(c, rng, cx, cy, w, h, mat="stone", moss=False):
    """An irregular, faceted stone: a jagged outline lit from the top left, a darker underside."""
    pts = []
    for i in range(8):
        a = i / 8 * 2 * math.pi + rng.uniform(-0.25, 0.25)
        r = rng.uniform(0.82, 1.08)
        pts.append((cx + math.cos(a) * w * r, cy + math.sin(a) * h * r * (0.8 if math.sin(a) > 0 else 1.0)))
    c.polygon(pts, mat, lum=0.42)
    # a lit facet on the top left and a shadow band underneath give it weight
    c.polygon([(cx - w * 0.75, cy - h * 0.1), (cx - w * 0.2, cy - h * 0.85), (cx + w * 0.35, cy - h * 0.7),
               (cx - w * 0.05, cy - h * 0.05)], mat, lum=0.82)
    for y in range(int(cy + h * 0.35), int(cy + h) + 1):
        for x in range(int(cx - w) - 1, int(cx + w) + 2):
            if 0 <= x < c.w and 0 <= y < c.h and c.mat[y][x] == mat:
                c.fixed[y][x] = 0
    if moss:
        for x in range(int(cx - w * 0.6), int(cx + w * 0.3)):
            for y in range(int(cy - h * 1.1), int(cy - h * 0.3)):
                if 0 <= x < c.w and 0 <= y < c.h and c.mat[y][x] == mat and c.mat[y - 1][x] is None:
                    c.mat[y][x], c.fixed[y][x] = "moss", 2
                    if c.mat[y + 1][x] == mat and rng.random() < 0.6:
                        c.mat[y + 1][x], c.fixed[y + 1][x] = "moss", 1


def den(occupants=(), snow=False):
    """112 x 56: a fox den. A lumpy earth mound set with stones: a big flat rock over the doorway,
    boulders on either side, pebbles and crumbly dirt clumps, grass and a root. occupants: fox palettes
    asleep inside, shown as sleepy snouts and ears poking out of the doorway. snow: snow lying over the top."""
    c = Canvas(112, 56)
    rng = random.Random(4)
    ground = 54
    door_x = 60
    # the mound: one lumpy shape, lit as a single form
    lumps = [(56, ground, 46, 30), (36, ground - 16, 18, 12), (74, ground - 14, 20, 13), (54, ground - 24, 14, 9)]
    for y in range(c.h):
        for x in range(c.w):
            if y <= ground and any(((x + 0.5 - lx) / rx) ** 2 + ((y + 0.5 - ly) / ry) ** 2 <= 1 for lx, ly, rx, ry in lumps):
                nx, ny = (x + 0.5 - 56) / 50, (y + 0.5 - ground + 6) / 34
                c.mat[y][x] = "earth"
                c.lum[y][x] = Canvas._shade(max(-1, min(1, nx)), max(-1, min(1, ny)), rng.uniform(-0.05, 0.05))
    # crumbly texture: darker crumbs and lighter grit
    for _ in range(140):
        x, y = rng.randrange(8, 104), rng.randrange(20, ground)
        if c.mat[y][x] == "earth":
            c.fixed[y][x] = rng.choice((0, 0, 2))
    # dirt clumps: little clods sitting on the slope
    for cx, cy, r in ((24, 42, 2.6), (32, 33, 2.0), (80, 36, 2.4), (88, 44, 2.8), (46, 28, 1.8), (70, 26, 1.8),
                      (98, 50, 2.2), (14, 50, 2.0)):
        c.ellipse(cx, cy, r, r * 0.75, "earth", bias=0.25)
    # the doorway: a dark burrow, with packed earth worn smooth at the lip
    c.ellipse(door_x, ground, 11, 14, "den_dark", clip=lambda x, y: y <= ground)
    c.ellipse(door_x, ground - 3, 7, 9, "den_dark", bias=-0.4, clip=lambda x, y: y <= ground)
    # stones: a flat lintel over the door, boulders either side, smaller rocks and pebbles round the base
    _rock(c, rng, door_x, ground - 15, 13, 4.2, "stone", moss=True)
    _rock(c, rng, door_x - 15, ground - 5, 6.5, 6, "stone")
    _rock(c, rng, door_x + 15, ground - 4, 7, 5.5, "stone_dark", moss=True)
    _rock(c, rng, 22, ground - 3, 6, 4, "stone_dark")
    _rock(c, rng, 92, ground - 3, 7, 4.5, "stone")
    _rock(c, rng, 38, ground - 22, 4.5, 3.2, "stone", moss=True)
    _rock(c, rng, 78, ground - 22, 4, 3, "stone_dark")
    for px_, py_, r in ((8, ground - 1, 1.6), (100, ground - 1, 1.8), (44, ground - 1, 1.4), (76, ground - 1, 1.5),
                        (106, ground - 2, 1.2), (30, ground - 1, 1.2)):
        c.ellipse(px_, py_, r, r * 0.8, "stone")
    # scattered earth kicked out of the burrow
    for dx in (-16, -11, -7, 8, 12, 17):
        c.ellipse(door_x + dx, ground + 0.5, 1.4, 0.8, "earth", bias=0.15)
    # a root poking out of the mound, and grass along the top
    c.capsule(84, 30, 92, 25, 0.8, 0.5, "handle")
    c.capsule(92, 25, 95, 27, 0.5, 0.4, "handle")
    for gx, gy in ((20, 34), (28, 25), (44, 22), (52, 21), (66, 21), (82, 27), (92, 34)):
        top = gy
        while top < ground and c.mat[top][gx] is None:
            top += 1  # stand the tuft on the mound's surface
        for dx, hgt in ((-1.6, 4), (0, 6), (1.6, 4.5)):
            c.capsule(gx, top + 1, gx + dx, top - hgt, 0.6, 0.35, "grass")
    if snow:  # a blanket of snow over the top of the mound and its stones (not in the doorway), grass buried
        srng = random.Random(11)
        for y in range(c.h):
            for x in range(c.w):
                if c.mat[y][x] in ("grass", "handle") and y < ground - 2:
                    c.mat[y][x] = None
        for x in range(c.w):
            top = next((y for y in range(c.h) if c.mat[y][x] is not None), None)
            if top is None or top > ground - 3:
                continue
            depth = 2 + (srng.random() < 0.5) + (1 if 30 < x < 85 else 0)
            for k in range(depth):
                y = top - 1 + k
                if 0 <= y < c.h:
                    c.mat[y][x], c.fixed[y][x] = "snow", (3 if k == 0 else 2 if k < depth - 1 else 1)
    # sleeping foxes: their snouts and ears poking out of the doorway, chins on their paws, eyes shut
    sleepers = occupants[:2]
    for i, palette in enumerate(sleepers):
        side = (-1 if i == 0 else 1) if len(sleepers) > 1 else 1
        hx, hy = door_x + side * (4 if len(sleepers) > 1 else 0) - side * 2, ground - 4
        sub = Canvas(112, 56, palette)
        sub.ellipse(hx + side * 4, ground - 0.8, 2.4, 1.1, "dark")                         # a front paw
        for ex in (-2.6, 1.6):  # two tall, pointed ears, pale inside and dark at the tips
            bx = hx + side * ex
            sub.polygon([(bx - 1.8, hy - 1.5), (bx + 1.8, hy - 1.5), (bx + side * 0.8, hy - 8)], "fur", lum=0.55)
            sub.pixel(bx + side * 0.3, hy - 3.5, "white", 1)
            sub.pixel(bx + side * 0.8, hy - 7.5, "dark", 0)
            sub.pixel(bx + side * 0.8, hy - 6.5, "dark", 1)
        sub.ellipse(hx, hy, 4.2, 3.4, "fur")                                               # the top of the head
        sub.capsule(hx + side * 1, hy + 0.5, hx + side * 6.5, hy + 1.8, 2.3, 1.2, "fur")   # the snout
        sub.ellipse(hx + side * 3.5, hy + 2.6, 3.2, 1.1, "white", bias=-0.1)              # pale chin
        for dx, dy in ((7, 1), (7, 2), (8, 1)):                                            # the nose tip
            sub.pixel(hx + side * dx, hy + dy, "nose", 0)
        for dx in (0.5, 1.5):  # a closed eye: a little dark line
            sub.pixel(hx + side * dx, hy - 1, "dark", 0)
        c.ramps = {**c.ramps, **{f"{palette}_{k}": v for k, v in sub.ramps.items()}}
        for y in range(56):
            for x in range(112):
                if sub.mat[y][x] is not None:
                    c.mat[y][x], c.lum[y][x], c.fixed[y][x] = f"{palette}_{sub.mat[y][x]}", sub.lum[y][x], sub.fixed[y][x]
    return c.to_image()


def zzz(t=0.0):
    """10 x 10: a small floating z for a den with sleepers."""
    from PIL import Image
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    px = img.load()
    ink = (250, 246, 230, 255)
    edge = (60, 50, 40, 255)
    for (x, y) in ((2, 2), (3, 2), (4, 2), (5, 2), (5, 3), (4, 4), (3, 5), (2, 6), (3, 6), (4, 6), (5, 6)):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if px[x + dx, y + dy][3] == 0:
                px[x + dx, y + dy] = edge
    for (x, y) in ((2, 2), (3, 2), (4, 2), (5, 2), (5, 3), (4, 4), (3, 5), (2, 6), (3, 6), (4, 6), (5, 6)):
        px[x, y] = ink
    return img


# -- climbing things: oak barrels and haystacks ----------------------------------------------------------

COMMON.update({
    "oak_wood": ("#5a3418", "#7e4a22", "#a0662e", "#c08446", "#2c1808"),
    "hoop": ("#2a2a2e", "#44444a", "#66666e", "#8e8e96", "#121214"),
    "hay": ("#9a7a24", "#c4a03a", "#dcbc56", "#efd888", "#584010"),
    "twine": ("#6a4c22", "#8a6630", "#a88244", "#c4a066", "#36260e"),
})

BARREL_W, BARREL_H = 22, 22


def _barrel(c, left, bottom):
    """One upright oak barrel: bulging staves with dark seams, two iron hoops, a lighter top rim."""
    top = bottom - BARREL_H
    for y in range(top, bottom + 1):
        f = (y - top) / BARREL_H                      # 0 at the top rim, 1 at the base
        bulge = round(math.sin(math.pi * f) * 1.6)    # barrels bulge in the middle
        x0, x1 = left - bulge, left + BARREL_W - 1 + bulge
        for x in range(x0, x1 + 1):
            band = (x - x0) / max(1, x1 - x0)
            level = 3 if band < 0.12 else 2 if band < 0.38 else 1 if band < 0.75 else 0
            mat = "oak_wood"
            if (x - left) % 5 == 0 and 0.05 < f < 0.95:
                level = max(0, level - 1)             # the seams between staves
            if abs(f - 0.22) < 0.05 or abs(f - 0.78) < 0.05:
                mat = "hoop"
            if 0 <= x < c.w and 0 <= y < c.h:
                c.mat[y][x], c.fixed[y][x] = mat, level
    for x in range(left + 1, left + BARREL_W - 1):   # the top rim
        if 0 <= x < c.w:
            c.mat[top][x], c.fixed[top][x] = "oak_wood", 3


BARREL_R = 11  # barrels lie on their sides; this is the radius of the round end you see


def barrel_end(spin=0.0):
    """24 x 24: one barrel seen end-on: a head of straight oak boards set just inside a shiny iron rim,
    with a little bung. spin turns the boards (for rolling)."""
    c = Canvas(24, 24)
    cx = cy = 12.0
    ca, sa = math.cos(spin), math.sin(spin)
    for y in range(24):
        for x in range(24):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > BARREL_R:
                continue
            light = -(dx + dy) / (BARREL_R * 1.4)               # lit from the top left
            if d > BARREL_R - 1.8:                               # the iron rim
                c.mat[y][x], c.fixed[y][x] = "hoop", 3 if light > 0.45 else 2 if light > 0.0 else 1 if light > -0.5 else 0
                continue
            if d > BARREL_R - 2.8:                               # the head sits a little inside the rim
                c.mat[y][x], c.fixed[y][x] = "oak_wood", 0
                continue
            across = dx * ca + dy * sa                           # position across the boards
            seam = int(across + 20) % 5 == 0                     # straight seams between the boards
            level = 3 if light > 0.45 else 2 if light > -0.15 else 1
            if seam:
                level = max(0, level - 2)
            c.mat[y][x], c.fixed[y][x] = "oak_wood", level
    for bx, by in ((12, 12), (13, 12), (12, 13), (13, 13)):     # the bung
        c.mat[by][bx], c.fixed[by][bx] = "hoop", 1
    c.mat[12][12], c.fixed[12][12] = "hoop", 3
    return c.to_image()


def barrel_spots():
    """Centres of the six barrels in the pile (3, 2, 1), nestled like a honeycomb, in a 70 x 64 frame."""
    spots, ground, step = [], 62, BARREL_R * math.sqrt(3)
    for row, count in enumerate((3, 2, 1)):
        y = ground - BARREL_R - row * step
        for i in range(count):
            spots.append((35 + (i - (count - 1) / 2) * 2 * BARREL_R, y))
    return spots


def barrels():
    """70 x 64: oak barrels on their sides, stacked three, two, one."""
    from PIL import Image
    img = Image.new("RGBA", (70, 64), (0, 0, 0, 0))
    one = barrel_end()
    for x, y in barrel_spots():
        img.alpha_composite(one, (int(round(x - 12)), int(round(y - 12))))
    return img


BALE_W, BALE_H = 30, 15


def _bale(c, rng, left, bottom):
    """A square hay bale with some depth: a lighter top face, the front face in straw strokes, a shaded
    right side, rounded corners, two twine bands wrapping over the top, and a few stray straws."""
    top = bottom - BALE_H
    lid = 3                                     # rows of the top face
    for y in range(top, bottom + 1):
        for x in range(left, left + BALE_W):
            corner = (x in (left, left + BALE_W - 1)) and (y in (top, bottom))
            if corner or not (0 <= x < c.w and 0 <= y < c.h):
                continue
            if y < top + lid:
                level = 3 if (x + y) % 3 else 2          # the sunlit top
            elif x >= left + BALE_W - 3:
                level = 0 if (x + y) % 2 else 1           # the side in shade
            else:
                stroke = (x * 2 + y * 3 + (y // 2) * 5) % 7    # straw laid in short diagonal strokes
                level = 2 if stroke == 0 else 0 if stroke == 4 else 1
                if y >= bottom - 1:
                    level = 0
            mat = "hay"
            if (x - left) in (7, 8, 21, 22):
                mat = "twine"
                level = 2 if y < top + lid else 1 if (x - left) in (7, 21) else 0
            c.mat[y][x], c.fixed[y][x] = mat, level
    for _ in range(9):                            # stray straws poking out of the top and sides
        x = rng.randrange(left + 1, left + BALE_W - 1)
        for k in range(rng.randint(1, 3)):
            y = top - 1 - k
            if 0 <= x + k < c.w and 0 <= y < c.h:
                c.mat[y][x + k], c.fixed[y][x + k] = "hay", 3


def haystack():
    """66 x 36: two hay bales with a third on top."""
    c = Canvas(66, 36)
    rng = random.Random(11)
    _bale(c, rng, 2, 34)
    _bale(c, rng, 34, 34)
    _bale(c, rng, 18, 34 - BALE_H - 1)
    return c.to_image()


COMMON.update({
    "pumpkin_rot": ("#5a3010", "#7e4a1c", "#9c642a", "#b47e40", "#2e1606"),
    "vine_dry": ("#4a3e1c", "#6a5a28", "#8a7838", "#a89452", "#26200c"),
})


def pumpkin_wilt(grow, shape, w):
    """A ripe pumpkin wilting when clicked: w 0..1 slumps it lower and wider and turns it brown."""
    c = Canvas(44, 36)
    ground = 30
    reach = 17
    vine = "vine" if w < 0.4 else "vine_dry"
    c.capsule(20 - reach, ground, 20 + reach * 0.8, ground - 0.5, 0.9, 0.8, vine)
    for dx in (-reach + 2, reach * 0.7, -reach * 0.5):
        lx, ly = 20 + dx, ground - 3.2 + w * 2.4  # leaves droop to the ground
        c.ellipse(lx, ly, 3.4, 2.6 - w * 1.2, vine, angle=(-20 if dx < 0 else 20) * (1 - w))
    size = 1.15 * grow
    mat = "pumpkin" if w < 0.5 else "pumpkin_rot"
    top = _pumpkin_body(c, 20, ground + 0.5, size, mat, shape, squash=(1 + 0.25 * w, 1 - 0.45 * w))
    c.capsule(20, top + 2, 21 + size + w * 3, top - 1.5 * size + w * 2.5, 1.2 * size, 0.9 * size, "stem")  # stem flops
    return c.to_image()


def corncob(roll=0):
    """14 x 14 ear of corn with its husk, rolling when batted (roll 0..3)."""
    c = Canvas(14, 14)
    a = math.radians(roll * 45)
    def at(dx, dy):
        return 7 + dx * math.cos(a) - dy * math.sin(a), 7 + dx * math.sin(a) + dy * math.cos(a)
    c.ellipse(*at(0, 0), 2.2, 5.0, "cob", angle=math.degrees(a))
    for side in (-1, 1):
        c.capsule(*at(side * 1.2, 4.2), *at(side * 3.0, 6.0), 1.0, 0.5, "husk")
    for i in range(-3, 4):  # rows of kernels
        x, y = at(0, i * 1.2)
        c.pixel(x, y, "cob", 3 if i % 2 else 2)
    return c.to_image()


def hoe_tilt(angle):
    """The hoe rocking about its base by angle (degrees)."""
    c = Canvas(24, 60)
    a = math.radians(angle)
    def at(x, y):  # turn around the base (14, 58)
        return 14 + (x - 14) * math.cos(a) - (y - 58) * math.sin(a), 58 + (x - 14) * math.sin(a) + (y - 58) * math.cos(a)
    c.capsule(*at(14, 58), *at(9, 6), 1.1, 1.0, "handle")
    c.capsule(*at(9, 6), *at(9, 4), 1.4, 1.4, "handle")
    c.polygon([at(8, 4), at(16, 3), at(17, 9), at(13, 8)], "iron", lum=0.55)
    c.ellipse(14, 58.5, 3.5, 1.2, "dirt")
    return c.to_image()


def _single_barrel():
    return barrel_end()


def barrels_falling():
    """The pile toppling: the barrels tumble down and roll apart, turning as they go. 110 x 64."""
    from PIL import Image
    starts = [(x + 20, y) for x, y in barrel_spots()]
    ends = [(10, 51, 1.0), (40, 51, -0.6), (70, 51, 1.2), (24, 51, -1.0), (96, 51, 1.5), (56, 51, 0.8)]
    frames = []
    for f in range(8):
        k = f / 7
        frame = Image.new("RGBA", (110, 64), (0, 0, 0, 0))
        for (sx, sy), (ex, ey, roll) in zip(starts, ends):
            x = sx + (ex - sx) * k
            y = sy + (ey - sy) * min(1.0, k * 1.6) - math.sin(math.pi * min(1.0, k * 1.6)) * 4
            frame.alpha_composite(barrel_end(spin=roll * k * 6), (int(round(x - 12)), int(round(y - 12))))
        frames.append(frame)
    return frames


HAY_LAYOUTS = {
    # canvas size, anchor, bales (left, bottom)
    "haystack": ((66, 36), (33, 34), [(2, 34), (34, 34), (18, 18)]),
    "haystack_row": ((98, 18), (49, 16), [(2, 16), (34, 16), (66, 16)]),
    "haystack_steps": ((98, 50), (49, 48), [(2, 48), (34, 48), (66, 48), (34, 32), (66, 32), (66, 16)]),
}


def hay(layout):
    (cw, ch), _, bales = HAY_LAYOUTS[layout]
    c = Canvas(cw, ch)
    rng = random.Random(11)
    for left, bottom in bales:
        _bale(c, rng, left, bottom)
    return c.to_image()


def crumb(i):
    """A tiny chewed-off bit of a dug-up icon."""
    c = Canvas(5, 5)
    c.ellipse(2.5, 2.5, 1.4 - i * 0.3, 1.1, "grey")
    return c.to_image()


def straw_bit(spin):
    c = Canvas(6, 6)
    a = math.radians(spin * 45)
    c.capsule(3 - 2 * math.cos(a), 3 - 2 * math.sin(a), 3 + 2 * math.cos(a), 3 + 2 * math.sin(a), 0.5, 0.4, "hay")
    return c.to_image(outline=False)


COMMON.update({
    "frog": ("#2e5a1e", "#44802a", "#62a238", "#8ac25a", "#162e0c"),
    "frog_belly": ("#a8b06a", "#cad08a", "#e2e6aa", "#f4f6d0", "#5a5e2e"),
})


def frog(pose="sit", t=0.0):
    """18 x 16 frog facing right. sit puffs its throat; hop stretches out its legs."""
    c = Canvas(18, 16)
    if pose == "hop":
        s = math.sin(t * math.pi)
        y = 9 - s * 4
        c.capsule(5, y + 2, 1, y + 4 + s * 2, 1.0, 0.8, "frog", -0.25)    # back legs kicking out
        c.ellipse(9, y, 5.5, 3.2, "frog", angle=-12 * s)
        c.capsule(12, y + 2, 15, y + 5, 0.8, 0.7, "frog")                  # front legs reaching
        hx, hy = 13, y - 2
    else:
        puff = math.sin(t * math.pi) * 1.4
        c.capsule(4, 13, 9, 14, 1.4, 1.0, "frog", -0.25)                   # folded back leg
        c.ellipse(9, 11, 5.5, 3.6, "frog")
        c.ellipse(12, 13 - puff * 0.3, 2.0 + puff, 1.4 + puff * 0.8, "frog_belly")  # the throat puffing
        c.capsule(12, 12, 13, 14.5, 0.8, 0.7, "frog")
        hx, hy = 13, 8
    c.ellipse(hx, hy, 3.4, 2.4, "frog")
    for ex in (-1.6, 1.4):  # bulging eyes on top
        c.ellipse(hx + ex, hy - 2.2, 1.3, 1.2, "frog", bias=0.2)
        c.pixel(hx + ex + 0.4, hy - 2.4, "eye")
    c.capsule(hx + 1, hy + 1, hx + 3, hy + 0.6, 0.3, 0.3, "frog", -0.6)   # a wide smile
    return c.to_image()


# -- wild turkeys and crows ------------------------------------------------------------------------------

COMMON.update({
    "turkey": ("#2a1a10", "#4a2e1a", "#6e4626", "#946436", "#140c06"),
    "turkey_bar": ("#8a6a3a", "#b8925a", "#d4b47c", "#ecd6a4", "#4a3618"),
    "turkey_head": ("#5a6e9a", "#7e96c4", "#a6bce0", "#cad8f0", "#2e3a56"),
    "wattle": ("#7a1414", "#b02020", "#d63a32", "#ee6a5a", "#3e0808"),
    "turkey_leg": ("#7a5e5a", "#a08480", "#c4a8a2", "#dccac4", "#3e2e2c"),
    "crow": ("#08080c", "#14141c", "#22222e", "#363a4e", "#020204"),
    "crow_sheen": ("#1a2238", "#283456", "#3a4a78", "#5468a0", "#0a0e1a"),
})


def turkey(pose="stand", t=0.0):
    """40 x 40 wild turkey facing right. pose: run, stand, look (head up, glancing back), gobble (tail
    fanned, head thrust out, wattle shaking), peck (head down at the ground)."""
    c = Canvas(40, 40)
    s = math.sin(t * 2 * math.pi)
    run = pose == "run"
    ground = 38
    # legs: long strides when running, planted otherwise
    stride = s * 4 if run else 0.0
    body_y = 22 - (abs(s) * 1.5 if run else 0.0)
    for lx, d in ((17, stride), (21, -stride)):
        c.capsule(lx, body_y + 5, lx + d, ground - 1, 0.7, 0.6, "turkey_leg")
        c.capsule(lx + d, ground, lx + d + 3, ground, 0.6, 0.5, "turkey_leg")
    # the tail: a big barred fan when gobbling, otherwise folded down behind
    if pose == "gobble":
        fan = 0.7 + 0.3 * t
        for i in range(7):
            a = math.radians(-160 + i * 22 * fan)
            tip = (12 + math.cos(a) * 14, body_y - 2 + math.sin(a) * 14)
            c.capsule(12, body_y, tip[0], tip[1], 1.6, 2.6, "turkey", 0.1)
            c.ellipse(tip[0], tip[1], 2.2, 2.2, "turkey_bar", bias=0.1)
    else:
        droop = 3 if run else 6
        c.capsule(12, body_y, 3, body_y + droop, 2.6, 2.0, "turkey", -0.2)
        c.capsule(5, body_y + droop - 1, 2, body_y + droop + 1, 1.4, 1.2, "turkey_bar")
    # body: round and bronze, with pale barring on the folded wing
    tilt = -18 if run else 0
    c.ellipse(19, body_y, 10.0, 7.5, "turkey", angle=tilt)
    c.ellipse(18, body_y - 1, 7.0, 4.5, "turkey", bias=-0.2, angle=tilt)
    for bx in (13, 16, 19):
        c.capsule(bx, body_y + 2, bx + 2, body_y + 3, 0.5, 0.5, "turkey_bar")
    # neck and head: where the head is depends on what it's doing
    if pose == "peck":
        hx, hy = 31 + s * 0.5, ground - 4 + abs(s) * 2
    elif pose == "gobble":
        hx, hy = 32 + s * 0.8, body_y - 4
    elif pose == "look":
        hx, hy = 27 - max(0.0, s) * 4, 7 + abs(s)  # head up high, turning back over its shoulder
    elif run:
        hx, hy = 33, body_y - 8
    else:
        hx, hy = 28 + s * 0.5, 9
    c.capsule(25, body_y - 3, hx - 1, hy + 2, 2.2, 1.2, "turkey_head", bias=-0.1)  # a bare, bluish neck
    c.ellipse(hx, hy, 2.4, 2.2, "turkey_head")
    wobble = s * 1.2 if pose == "gobble" else 0.0
    c.capsule(hx + 0.5, hy + 1.5, hx + 0.5 + wobble, hy + 4.5, 1.0, 1.3, "wattle")  # the red wattle
    c.capsule(hx + 1.5, hy - 1.2, hx + 3.2, hy + 1.8, 0.5, 0.5, "wattle")           # the snood over the beak
    c.capsule(hx + 2, hy + 0.2, hx + 4, hy + 0.8, 0.6, 0.4, "beak")
    if pose == "gobble" and t < 0.7:
        c.capsule(hx + 2, hy + 1.4, hx + 4, hy + 2.4, 0.5, 0.4, "beak")  # beak open
    c.pixel(hx + 0.5, hy - 0.8, "eye")
    # the "beard" hanging from the chest
    c.capsule(27, body_y - 1, 28, body_y + 4, 0.6, 0.4, "turkey", -0.3)
    return c.to_image()


def crow(pose="perch", t=0.0, acorn_in_beak=False, hat=False):
    """24 x 24 American crow facing right. pose: fly, perch, hop, walk, peck, caw, tilt (head cocked,
    looking at something). hat: wearing the scarecrow's hat, which it has pinched."""
    c = Canvas(24, 24)
    s = math.sin(t * 2 * math.pi)
    if pose == "fly":
        c.capsule(7, 12, 1, 12 + s, 1.6, 2.2, "crow", -0.3)  # a fanned tail
        c.ellipse(12, 12, 6.0, 3.0, "crow")
        wing_y = 12 - s * 7
        c.polygon([(9, 11), (14, 11), (9 - s, wing_y - 1), (5, wing_y)], "crow_sheen", lum=0.4)
        hx, hy = 18, 10.5
    else:
        hop = max(0.0, s) * 2.5 if pose == "hop" else 0.0
        step = s * 1.5 if pose == "walk" else 0.0
        lean = 20 if pose == "peck" else 0
        by = 14 - hop
        c.capsule(12 + step, by + 3, 11 + step * 1.5, 22 - hop, 0.5, 0.5, "crow")   # legs
        c.capsule(14 - step, by + 3, 14 - step * 1.5, 22 - hop, 0.5, 0.5, "crow")
        c.capsule(9, by + 1, 3, by + 5, 1.8, 1.4, "crow", -0.3)  # tail
        c.ellipse(12, by, 5.5, 4.0, "crow", angle=lean - 15)
        c.polygon([(8, by - 2), (14, by - 2), (7, by + 3)], "crow_sheen", lum=0.3)  # folded wing
        if pose == "peck":
            hx, hy = 18, 19 + abs(s) * 2 - hop
        elif pose == "caw":
            hx, hy = 17 + t * 1.5, 8 - t - hop  # head stretched forward and up
        elif pose == "tilt":
            hx, hy = 16.5, 9.5 - hop
        else:
            hx, hy = 16, 9 - hop
    c.ellipse(hx, hy, 3.0, 2.7, "crow")
    if pose == "caw" and t < 0.7:  # beak wide open
        c.polygon([(hx + 2, hy - 0.8), (hx + 6, hy - 2.2), (hx + 2.4, hy + 0.4)], "crow", lum=0.5)
        c.polygon([(hx + 2, hy + 0.8), (hx + 5.4, hy + 2.4), (hx + 2.4, hy + 1.6)], "crow", lum=0.5)
    else:
        c.polygon([(hx + 2.2, hy - 0.9), (hx + 5.6, hy + 0.4), (hx + 2.2, hy + 1.2)], "crow", lum=0.6)
    if acorn_in_beak:
        c.ellipse(hx + 5.2, hy + 1.2, 1.4, 1.6, "acorn")
        c.ellipse(hx + 5.2, hy - 0.2, 1.5, 0.8, "cap")
    eye_y = hy - (1.4 if pose == "tilt" else 0.8)
    c.pixel(hx + 0.8, eye_y, "white", 2)  # a glint, so the eye shows against the black
    if hat:  # far too big for it, tipped back on its head
        c.capsule(hx - 4.5, hy - 2.2, hx + 3.5, hy - 2.8, 0.9, 0.8, "hat")
        c.ellipse(hx - 0.6, hy - 4.4, 2.8, 2.1, "hat")
        c.capsule(hx - 3, hy - 3.4, hx + 2, hy - 3.6, 0.5, 0.5, "plaid_red")
    return c.to_image()


PIXEL_LETTERS = {
    "H": ["101", "101", "111", "101", "101"], "O": ["111", "101", "101", "101", "111"],
    "N": ["1001", "1101", "1011", "1001", "1001"], "K": ["101", "110", "100", "110", "101"],
    "!": ["1", "1", "1", "0", "1"], "R": ["110", "101", "110", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "B": ["110", "101", "110", "101", "110"], "T": ["111", "010", "010", "010", "010"],
    "G": ["111", "100", "101", "101", "111"], "L": ["100", "100", "100", "100", "111"],
    "E": ["111", "100", "110", "100", "111"], "C": ["111", "100", "100", "100", "111"],
    "A": ["010", "101", "111", "101", "101"], "W": ["10001", "10001", "10101", "10101", "01010"],
    "?": ["111", "001", "011", "000", "010"], " ": ["0", "0", "0", "0", "0"],
    "Z": ["111", "001", "010", "100", "111"],
}


def word_bubble(text):
    """A little speech bubble with text in a hand-made pixel font."""
    from PIL import Image
    width = sum(len(PIXEL_LETTERS[ch][0]) + 1 for ch in text) + 5
    w, h = width, 14
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    edge, fill, ink = (42, 42, 42, 255), (255, 255, 255, 255), (30, 30, 30, 255)
    for y in range(1, h - 4):
        for x in range(1, w - 1):
            px[x, y] = fill
    for x in range(1, w - 1):
        px[x, 0], px[x, h - 4] = edge, edge
    for y in range(1, h - 4):
        px[0, y], px[w - 1, y] = edge, edge
    for (x, y) in ((4, h - 3), (5, h - 3), (4, h - 2)):
        px[x, y] = edge
    px[5, h - 4] = fill
    x0 = 3
    for ch in text:
        for row, bits in enumerate(PIXEL_LETTERS[ch]):
            for col, bit in enumerate(bits):
                if bit == "1":
                    px[x0 + col, 2 + row] = ink
        x0 += len(PIXEL_LETTERS[ch][0]) + 1
    return img


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


def _rot_pts(points, angle, cx, cy):
    ca, sa = math.cos(angle), math.sin(angle)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in points]


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


def inchworm(pose="crawl", t=0.0):
    """14 x 8: a little green inchworm. crawl: looping along, back end up to front; fall: curled up."""
    c = Canvas(14, 8)
    if pose == "fall":
        c.ellipse(7, 4, 3.0, 2.6, "inchworm")
        c.ellipse(7, 4, 1.4, 1.1, "inchworm", bias=-0.5)
        c.pixel(9, 3, "eye")
        return c.to_image()
    arch = math.sin(t * math.pi)  # 0 flat .. 1 a tall loop
    length = 10 - arch * 4
    left = 2 + (10 - length) * (t if t < 0.5 else 1 - t) * 2
    pts = [(left + length * i / 6, 6 - math.sin(i / 6 * math.pi) * arch * 4) for i in range(7)]
    c.chain(pts, [1.3] * 7, ["inchworm"] * 7)
    c.pixel(pts[-1][0] + 0.5, pts[-1][1] - 0.5, "eye")
    return c.to_image()


BUTTERFLIES = {"monarch": "monarch", "white": "wing_white", "sulphur": "wing_sulphur", "azure": "wing_azure"}


def butterfly(t=0.0, kind="monarch", span=None):
    """14 x 12: a butterfly seen from the front, wings beating (wide open .. edge on). kind: monarch (orange
    and black), white (a cabbage white), sulphur (lemon yellow) or azure (sky blue). span: how open the wings
    are (otherwise from t)."""
    c = Canvas(14, 12)
    mat = BUTTERFLIES[kind]
    if span is None:
        span = 0.25 + 0.75 * abs(math.cos(t * math.pi))
    for side in (-1, 1):
        upper = [(7, 5), (7 + side * 6.2 * span, 1.2), (7 + side * 6.0 * span, 5.6)]
        lower = [(7, 6), (7 + side * 4.4 * span, 6.4), (7 + side * 3.2 * span, 10)]
        c.polygon(upper, mat, lum=0.6)
        c.polygon(lower, mat, lum=0.45)
        if span > 0.5 and kind == "monarch":  # black edges with white dots, black veins
            c.pixel(7 + side * 5.6 * span, 2, "bug_black", 0)
            c.pixel(7 + side * 5.6 * span, 4.4, "bug_black", 0)
            c.pixel(7 + side * 4.8 * span, 2.8, "white", 3)
            c.pixel(7 + side * 3 * span, 3.6, "bug_black", 0)
            c.pixel(7 + side * 2.6 * span, 8, "bug_black", 0)
        elif span > 0.5 and kind == "white":  # black wing tips and a spot
            c.pixel(7 + side * 5.8 * span, 1.6, "bug_black", 0)
            c.pixel(7 + side * 3.6 * span, 3.4, "bug_black", 1)
        elif span > 0.5:  # a dark edge and an eyespot
            c.pixel(7 + side * 5.8 * span, 2.2, mat, 0)
            c.pixel(7 + side * 3.0 * span, 7.6, "star" if kind == "azure" else "ladybug", 2)
    c.capsule(7, 3.5, 7, 9, 0.6, 0.5, "bug_black")  # body
    for side in (-1, 1):
        c.capsule(7, 3.5, 7 + side * 1.8, 0.8, 0.2, 0.2, "bug_black")  # antennae
    return c.to_image()


COMMON.update({
    "wing_white": ("#a8aca0", "#d8dcd2", "#f2f4ee", "#ffffff", "#5e625a"),
    "wing_sulphur": ("#b8a414", "#e0cc28", "#f4e450", "#fcf490", "#5e540a"),
    "wing_azure": ("#3a5aa8", "#5a82d0", "#82a8ec", "#b4cef8", "#1c2c5a"),
})


def beetle(kind="junebug", pose="crawl", t=0.0):
    """10 x 12: a June beetle or a ladybug, head up, climbing the trunk. fly: wing cases up, wings out."""
    c = Canvas(10, 12)
    body = "beetle_brown" if kind == "junebug" else "ladybug"
    step = math.sin(t * 2 * math.pi)
    for side in (-1, 1):  # legs, three a side, scrabbling
        for k, y in enumerate((5, 7, 9)):
            reach = 3.0 + (step if (k % 2) ^ (side > 0) else -step) * 0.8
            c.capsule(5 + side * 1.5, y, 5 + side * reach, y + (k - 1) * 1.2, 0.35, 0.3, "bug_black")
    if pose == "fly":
        for side in (-1, 1):  # the wing cases lifted, and the thin wings whirring behind
            c.ellipse(5 + side * (3.5 + abs(step)), 8, 2.4, 3.2, "wing_clear", angle=side * 25)
            c.ellipse(5 + side * 2.4, 6, 1.8, 2.6, body, angle=side * 35)
    c.ellipse(5, 7.5, 2.6, 3.4 if kind == "junebug" else 2.9, body)
    if kind == "ladybug":
        for dx, dy in ((-1.2, 6.5), (1.2, 6.5), (-1.4, 8.8), (1.4, 8.8), (0, 10)):
            c.pixel(5 + dx, dy, "bug_black", 0)
        c.ellipse(5, 3.6, 1.6, 1.2, "bug_black")  # the head
        c.pixel(4.4, 3.4, "white", 3)
        c.pixel(5.6, 3.4, "white", 3)
    else:
        c.capsule(5, 5, 5, 10.5, 0.3, 0.3, "beetle_brown", bias=-0.6)  # the line down its back
        c.ellipse(5, 3.6, 1.6, 1.3, "beetle_brown", bias=-0.2)
    for side in (-1, 1):
        c.capsule(5 + side * 0.8, 2.8, 5 + side * 2.2, 1.2, 0.25, 0.2, "bug_black")  # feelers
    return c.to_image()


def cicada(pose="sit", t=0.0):
    """10 x 14: a cicada on the trunk, head up. buzz: its body thrums. fly: wings out."""
    c = Canvas(10, 14)
    shake = (0.5 if int(t * 8) % 2 else -0.5) if pose == "buzz" else 0.0
    if pose == "fly":
        for side in (-1, 1):
            c.ellipse(5 + side * 3.5, 7 + math.sin(t * 2 * math.pi) * 1.5, 2.6, 4.4, "wing_clear", angle=side * 30)
    else:  # clear wings folded like a roof over its back
        for side in (-1, 1):
            c.polygon([(5 + shake, 4), (5 + side * 3.2 + shake, 7), (5 + side * 2.2 + shake, 13), (5 + shake, 12)],
                      "wing_clear", lum=0.5 if side < 0 else 0.7)
    c.ellipse(5 + shake, 7, 2.0, 3.2, "cicada")
    c.ellipse(5 + shake, 3.2, 2.6, 1.6, "cicada", bias=0.1)  # the broad head
    for side in (-1, 1):
        c.pixel(5 + side * 2.2 + shake, 3, "ladybug", 2)  # red eyes
    return c.to_image()


def spider(t=0.0):
    """13 x 11: a little garden spider hanging from its thread, long legs wiggling."""
    c = Canvas(13, 11)
    wig = math.sin(t * 2 * math.pi) * 0.7
    cx = 6.5
    for side in (-1, 1):  # four long, bent legs a side: out to a knee, then down
        for k, (ky, fy) in enumerate(((2.0, 0.5), (2.8, 3.0), (3.6, 6.0), (4.2, 9.0))):
            knee = (cx + side * (3.4 + (k in (1, 2)) * 0.8), ky - 1.6 + (wig if k % 2 else -wig))
            foot = (cx + side * (5.6 - abs(k - 1.5) * 0.4), fy + (wig if k % 2 else -wig) * 0.5)
            _twig(c, cx, 3.6, *knee, "bug_black", 1)
            _twig(c, *knee, *foot, "bug_black", 0)
    c.ellipse(cx, 6.2, 2.0, 2.3, "beetle_brown", bias=-0.2)  # the round abdomen
    c.pixel(cx, 6, "daffodil", 2)                             # a little gold mark
    c.ellipse(cx, 3.4, 1.3, 1.1, "bug_black")
    return c.to_image(outline=False)  # thin legs, no outline to thicken them


def silk():
    """1 x 6: a length of spider silk (the thread is a stack of these)."""
    from PIL import Image
    img = Image.new("RGBA", (1, 6), (236, 240, 244, 210))
    return img


# -- winter things: a sled, a tree stump, a little Christmas tree -------------------------------------------

COMMON.update({
    "sled_wood": ("#7a4a1e", "#a8662a", "#c8843c", "#e0a65e", "#3e240c"),
    "sled_runner": ("#7a1414", "#b01e1e", "#d4382c", "#ee6a58", "#3e0808"),
    "stump_top": ("#9a7440", "#c09456", "#d8b072", "#ecd09a", "#5a4020"),
    "fungus": ("#8a5a24", "#b47a34", "#d09a4e", "#e8bc78", "#4a2e0e"),
    "fir": ("#103a20", "#18522c", "#246c3a", "#3a8a52", "#061e10"),
    "star": ("#b88a0c", "#e8b81a", "#f8d838", "#fff4a0", "#6a4a04"),
})
LIGHT_COLOURS = ("ladybug", "star", "jay", "leaf_summer_light", "violet")  # red, gold, blue, green, purple


def sled(snow=False, tilt=0.0):
    """44 x 18: a wooden sled on red runners that curl up at the front. tilt rocks it (when clicked)."""
    c = Canvas(44, 18)
    lift = lambda x: tilt * (x - 22) / 22  # rocking: one end up, the other down
    # the runners: along the bottom, curling up and back over at the front (right)
    for y_off in (0, 0):
        c.capsule(4, 15 + lift(4), 34, 15 + lift(34), 1.0, 1.0, "sled_runner")
    pts = bezier((34, 15 + lift(34)), (42, 15 + lift(42)), (39, 7 + lift(39)), 6)
    c.chain(pts, [1.0] * 6, ["sled_runner"] * 6)
    for x in (10, 22, 32):  # struts up to the deck
        c.capsule(x, 14 + lift(x), x, 10 + lift(x), 0.7, 0.7, "sled_runner", bias=-0.2)
    # the deck: three wooden slats
    for k, y in enumerate((8.0, 9.6)):
        c.capsule(5, y + lift(5), 36, y + lift(36), 1.0, 1.0, "sled_wood", bias=0.15 - k * 0.2)
    c.capsule(36, 8.8 + lift(36), 39, 6.6 + lift(39), 0.9, 0.8, "sled_wood")  # the curl of the deck at the front
    if snow:
        for x in range(6, 36):
            if x % 7 != 3:
                c.pixel(x, 6.6 + lift(x), "snow", 3 if x % 3 else 2)
    return c.to_image()


def stump(snow=False):
    """36 x 26: an old oak stump, its top cut flat and ringed, roots spreading, a shelf fungus on its side."""
    c = Canvas(36, 26)
    ground = 24
    for side in (-1, 1):  # roots
        c.capsule(18 + side * 8, ground - 4, 18 + side * 15, ground, 2.2, 1.2, "bark", bias=-0.1)
    for y in range(9, ground - 1):  # the trunk: straight sides, sawn off flat at the top
        half = 8.4 + (y - 9) * 0.04
        left, right = int(round(18 - half)), int(round(18 + half))
        for x in range(left, right + 1):
            band = (x - left) / max(1, right - left)
            _px(c, x, y, "bark", 3 if band < 0.12 else 2 if band < 0.35 else 1 if band < 0.75 else 0)
    for x in (13, 16, 21, 24):  # bark furrows
        for y in range(10, ground - 2):
            if c.mat[y][x] == "bark" and y % 5 != 0:
                c.fixed[y][x] = 0
    c.ellipse(18, 8.5, 8.6, 3.0, "stump_top", bias=0.3)  # the cut top
    for r in (6.0, 3.6, 1.4):  # growth rings
        for a in range(0, 360, 12):
            x, y = 18 + math.cos(math.radians(a)) * r, 8.5 + math.sin(math.radians(a)) * r * 0.34
            c.pixel(x, y, "stump_top", 0)
    c.ellipse(26.5, 15, 3.0, 1.3, "fungus", bias=0.2)  # a little shelf fungus
    c.ellipse(26, 18, 2.2, 1.0, "fungus", bias=0.2)
    if snow:  # a cushion of snow on top and a little drift at the foot
        c.ellipse(18, 7.6, 8.8, 2.6, "snow", bias=0.4)
        c.ellipse(16, 6.4, 5.0, 1.6, "snow", bias=0.5)
        for x in range(4, 33):
            if c.mat[ground][x] is not None or abs(x - 18) < 15:
                c.pixel(x, ground, "snow", 2)
                if abs(x - 18) > 9 and x % 2:
                    c.pixel(x, ground - 1, "snow", 3)
    return c.to_image()


def xmas_tree(t=0.0, snow=False, sparkle=False):
    """32 x 48: a small fir decked out for Christmas: a gold star on top, coloured lights that twinkle (t steps
    them round), and a red pot. sparkle: every light blazing and the star shining (when clicked)."""
    c = Canvas(32, 48)
    ground = 46
    c.capsule(12, ground, 20, ground, 2.6, 2.6, "sled_runner")      # a red pot
    c.capsule(16, ground - 4, 16, ground - 8, 1.4, 1.4, "bark")      # the trunk
    tiers = [(16, 40, 13, 9), (16, 31, 11, 9), (16, 23, 8.5, 8), (16, 15, 6, 7)]  # (x, bottom, half width, height)
    for x, bottom, half, h in tiers:  # each tier a drooping triangle of branches
        c.polygon([(x - half, bottom), (x + half, bottom), (x, bottom - h - 4)], "fir", lum=0.45)
        for k in range(int(half * 2)):  # a ragged, needly lower edge
            if k % 2:
                c.pixel(x - half + k, bottom + 1, "fir", 1)
        if snow:
            for k in range(int(half * 2) - 2):
                if k % 3:
                    c.pixel(x - half + 1 + k, bottom - 1 - abs(k - half) * 0.15, "snow", 3)
    if snow:
        c.ellipse(16, 8.5, 2.5, 1.2, "snow", bias=0.4)
    # the lights, strung round in a spiral; t moves the bright ones along
    lights = [(9, 37), (13, 35), (19, 36), (23, 38), (11, 28), (16, 27), (21, 29), (12, 21), (19, 20), (15, 14),
              (8, 39), (25, 39), (17, 32)]
    for i, (x, y) in enumerate(lights):
        lit = sparkle or (i + int(t * 4)) % 3 == 0
        c.pixel(x, y, LIGHT_COLOURS[i % len(LIGHT_COLOURS)], 3 if lit else 1)
        if lit and sparkle:
            c.pixel(x, y - 1, LIGHT_COLOURS[i % len(LIGHT_COLOURS)], 2)
    # the star on top
    sx, sy = 16, 6
    points = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = 3.6 if k % 2 == 0 else 1.5
        points.append((sx + math.cos(a) * r, sy + math.sin(a) * r))
    c.polygon(points, "star", lum=0.9 if sparkle else 0.6)
    if sparkle:  # rays of light round the star
        for a in range(0, 360, 45):
            c.pixel(sx + math.cos(math.radians(a)) * 5.5, sy + math.sin(math.radians(a)) * 5.5, "star", 3)
    return c.to_image()


# -- spring: flower beds, songbirds ---------------------------------------------------------------------------

COMMON.update({
    "tulip_red": ("#8a1020", "#c01e30", "#e03a48", "#f4707a", "#4a0610"),
    "tulip_pink": ("#a8406a", "#d0608c", "#ec88ac", "#f8b8d0", "#5a1e38"),
    "tulip_yellow": ("#b8900c", "#e4bc1c", "#f6d840", "#fcee88", "#5e4806"),
    "robin_back": ("#3e342c", "#5a4c40", "#766656", "#94846e", "#1e1812"),
    "robin_breast": ("#9a3e14", "#c85a20", "#e47a36", "#f4a060", "#4e1c06"),
    "bluebird": ("#1e3a8a", "#2e56b8", "#4878dc", "#78a2f0", "#0e1c48"),
    "goldfinch": ("#b8980c", "#e4c418", "#f8e030", "#fcf080", "#5e4c04"),
    "note": ("#1a1a24", "#2a2a38", "#3c3c50", "#5a5a74", "#0a0a10"),
})

# the flower heads in each bed (frame x, y), so butterflies can land on them: written to the sprite's JSON
FLOWER_BEDS = {
    "daffodils": [(8, 9), (15, 5), (22, 8), (29, 4), (36, 10)],
    "tulips": [(7, 8), (14, 4), (21, 7), (28, 3), (35, 8)],
    "violets": [(6, 14), (11, 12), (17, 13), (23, 11), (29, 13), (34, 14)],
}
TULIP_COLOURS = ("tulip_red", "tulip_pink", "tulip_yellow", "tulip_red", "violet")


def flower_bed(kind, sway=0.0):
    """44 x 24: a clump of spring flowers. kind: daffodils (yellow, orange trumpets), tulips (red, pink, yellow
    and purple cups) or violets (a low mound of heart-shaped leaves dotted with small purple flowers)."""
    c = Canvas(44, 24)
    ground = 22
    rng = random.Random({"daffodils": 1, "tulips": 2, "violets": 3}[kind])
    heads = FLOWER_BEDS[kind]
    if kind == "violets":
        for x in range(4, 40, 3):  # the leaves, in a low mound
            c.ellipse(x + rng.uniform(-1, 1), ground - 2 - rng.uniform(0, 3) * (1 - abs(x - 22) / 22),
                      2.6, 2.0, "stalk", bias=rng.uniform(-0.2, 0.2))
        for x, y in heads:
            hx = x + sway * 0.4
            _twig(c, x, ground - 3, hx, y + 1, "stalk", 1)
            for a in range(5):
                ang = a / 5 * 2 * math.pi - math.pi / 2
                c.ellipse(hx + math.cos(ang) * 1.4, y + math.sin(ang) * 1.2, 1.0, 1.0, "violet")
            c.pixel(hx, y, "daffodil", 3)
        return c.to_image()
    for k, (x, y) in enumerate(heads):  # long leaves first, then a stem and a flower for each
        side = -1 if k % 2 else 1
        _twig(c, x, ground, x + side * 3, ground - (ground - y) * 0.6, "stalk", 2)
        _twig(c, x - side, ground, x - side * 2, ground - (ground - y) * 0.45, "stalk", 1)
    for k, (x, y) in enumerate(heads):
        lean = sway * (1 - y / ground) * 1.4
        hx = x + lean
        _twig(c, x, ground, hx, y + 2, "stalk", 1)
        if kind == "daffodils":
            _daffodil_head(c, hx, y)
        else:  # a tulip: a closed cup of petals
            mat = TULIP_COLOURS[k % len(TULIP_COLOURS)]
            c.ellipse(hx, y, 2.4, 2.8, mat)
            c.polygon([(hx - 2.4, y - 0.5), (hx - 1.2, y - 3.6), (hx, y - 1.4), (hx + 1.2, y - 3.6), (hx + 2.4, y - 0.5)],
                      mat, lum=0.7)
    for x in range(2, 42):  # a little earth at the foot
        c.pixel(x, ground + 1, "dirt", 1 if x % 3 else 2)
    return c.to_image()


SONGBIRDS = {  # back, breast, head, beak
    "robin": ("robin_back", "robin_breast", "bug_black", "beak"),
    "bluebird": ("bluebird", "robin_breast", "bluebird", "bug_black"),
    "goldfinch": ("goldfinch", "goldfinch", "goldfinch", "daffodil_cup"),
}


def songbird(kind="robin", pose="perch", t=0.0):
    """20 x 20: a small songbird facing right: a robin (orange breast), a bluebird or a goldfinch (yellow, black
    wings and cap). pose: perch, hop, fly, sing (head up, beak open), peck, worm (a robin tugging up a worm)."""
    c = Canvas(20, 20)
    back, breast, head, beak = SONGBIRDS[kind]
    s = math.sin(t * 2 * math.pi)
    wing = "bug_black" if kind == "goldfinch" else back
    if pose == "fly":
        c.capsule(6, 10, 1, 9 + s, 1.4, 1.0, back, -0.3)
        c.ellipse(10, 10, 4.6, 2.8, back)
        c.ellipse(11, 11.4, 3.4, 1.4, breast, bias=0.1)
        c.polygon([(8, 9), (12, 9), (8 - s, 9 - s * 5.5), (5, 9 - s * 5)], wing, lum=0.5)
        hx, hy = 14.5, 8.5
    else:
        hop = max(0.0, s) * 2 if pose == "hop" else 0.0
        bow = (2.5 + abs(s) * 1.5) if pose in ("peck", "worm") else 0.0
        by = 12 - hop
        c.capsule(8, by + 1, 3, by + 4, 1.3, 1.0, back, -0.3)                  # tail
        c.capsule(10, by + 3, 9.5, 18 - hop, 0.4, 0.4, "bark")                  # legs
        c.capsule(12, by + 3, 12.5, 18 - hop, 0.4, 0.4, "bark")
        c.ellipse(10.5, by, 4.4, 3.6, back, angle=-10)
        c.ellipse(12, by + 1.2, 3.0, 2.6, breast, bias=0.15)                    # the breast
        c.polygon([(7.5, by - 1.5), (11.5, by - 1.5), (7, by + 2.5)], wing, lum=0.35)  # folded wing
        if kind == "goldfinch":
            c.pixel(9, by, "white", 3)  # white wing bar
        if pose == "sing":
            hx, hy = 14.5, 6.5 - hop
        else:
            hx, hy = 14 + bow * 0.6, 8 - hop + bow * 2
    c.ellipse(hx, hy, 2.6, 2.4, head)
    if kind == "goldfinch":
        c.ellipse(hx - 0.4, hy - 1.2, 1.6, 0.9, "bug_black")  # black cap
    if kind == "robin":
        c.pixel(hx + 0.2, hy - 1.2, "white", 3)  # the white ring round its eye
    open_ = pose == "sing" and t < 0.75
    if open_:
        c.capsule(hx + 2, hy - 0.6, hx + 4.4, hy - 1.8, 0.4, 0.3, beak)
        c.capsule(hx + 2, hy + 0.4, hx + 4.0, hy + 1.2, 0.4, 0.3, beak)
    else:
        c.capsule(hx + 2, hy, hx + 4.2, hy + 0.3, 0.5, 0.3, beak)
    if pose == "worm":  # a wiggly pink worm stretching from its beak to the ground
        stretch = 2 + abs(s) * 3
        c.chain([(hx + 4, hy + 0.5 + k * stretch / 4 + (0.5 if k % 2 else -0.5)) for k in range(5)], [0.5] * 5,
                ["tulip_pink"] * 5)
    c.pixel(hx + 0.6, hy - 0.6, "eye")
    return c.to_image()


def note(double=False):
    """8 x 10: a music note (or two joined) floating up from a singing bird."""
    c = Canvas(8, 10)
    c.ellipse(2, 8, 1.6, 1.2, "note", angle=-20)
    _twig(c, 3, 8, 3, 1, "note", 1)
    if double:
        c.ellipse(6, 7, 1.6, 1.2, "note", angle=-20)
        _twig(c, 7, 7, 7, 0, "note", 1)
        _twig(c, 3, 1, 7, 0, "note", 1)
        _twig(c, 3, 2, 7, 1, "note", 1)
    else:
        _twig(c, 3, 1, 5, 3, "note", 1)
    return c.to_image()


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
    for x, y in BIRCH_TIPS:
        lx = x + lean(y) * 1.3
        if leaves:  # small leaves in loose clusters along the hanging twigs
            for _ in range(5):
                c.ellipse(lx + lrng.uniform(-2.5, 2.5), y + lrng.uniform(-3, 2), lrng.uniform(1.0, 1.8), 1.0,
                          lrng.choice(leaves), angle=lrng.uniform(-40, 40))
        elif season == "spring":
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


# -- a woodstack, an apple barrel, a stone well --------------------------------------------------------------

COMMON.update({
    "log_end": ("#a07a44", "#c49a5c", "#dcb878", "#eed29e", "#5a4022"),
    "apple": ("#7a0e10", "#b41a1a", "#dc3228", "#f06a54", "#420606"),
    "apple_green": ("#4e7a14", "#6ea020", "#90c034", "#b8dc62", "#283e08"),
    "well_stone": ("#5a5a5e", "#7e7e84", "#a2a2a8", "#c6c6cc", "#2e2e32"),
    "shingle": ("#4a2a1a", "#6a3c24", "#8a5232", "#a86e48", "#24140a"),
    "water": ("#1e4a8a", "#2e6ab8", "#4a8cdc", "#86b8f0", "#0e2448"),
})
WOODSTACK_ROWS = [(5, 31), (4, 23), (3, 15)]  # logs in each row and the row's centre height, from the bottom


def woodstack(snow=False):
    """60 x 36: split firewood stacked in rows, log ends out: pale wood with rings and a rim of bark."""
    c = Canvas(60, 36)
    rng = random.Random(4)
    r = 4.4
    for count, cy in WOODSTACK_ROWS:
        for k in range(count):
            cx = 30 + (k - (count - 1) / 2) * 9.6 + rng.uniform(-0.6, 0.6)
            c.ellipse(cx, cy, r, r * 0.95, "bark", bias=-0.1)                  # the bark rim
            c.ellipse(cx - 0.3, cy - 0.3, r - 1.3, (r - 1.3) * 0.95, "log_end", bias=0.25)
            for ring in (2.0, 0.9):                                           # growth rings
                for a in range(0, 360, 30):
                    c.pixel(cx - 0.3 + math.cos(math.radians(a)) * ring, cy - 0.3 + math.sin(math.radians(a)) * ring,
                            "log_end", 1)
            if rng.random() < 0.5:  # a split down the middle of some
                _twig(c, cx - 0.3, cy - 2.4, cx + 0.5, cy + 2.0, "log_end", 0)
    if snow:  # snow lying on the top of each row's logs
        for x in range(c.w):
            top = next((y for y in range(c.h) if c.mat[y][x] is not None), None)
            if top is not None:
                for k in range(2 + (x % 3 == 0)):
                    if top - 1 + k < c.h:
                        _px(c, x, top - 1 + k, "snow", 3 if k == 0 else 2)
        for count, cy in WOODSTACK_ROWS[1:]:  # and in the gaps on the shoulders of the rows below
            half = count * 4.8 + 2
            for x in range(int(30 - half - 5), int(30 - half + 1)):
                _px(c, x, int(cy + 4), "snow", 3)
            for x in range(int(30 + half - 1), int(30 + half + 5)):
                _px(c, x, int(cy + 4), "snow", 3)
    return c.to_image()


def apple(spin=0):
    """8 x 8: a red apple with a stem and a leaf, turning over as it rolls."""
    c = Canvas(8, 8)
    a = spin * math.pi / 2
    c.ellipse(4, 4.4, 2.9, 2.7, "apple")
    c.pixel(4 - math.sin(a) * 1.2, 2.4 + (1 - math.cos(a)) * 1.6, "apple", 3)  # its shine, turning round
    sx, sy = 4 + math.sin(a) * 2.2, 4.4 - math.cos(a) * 2.6
    c.pixel(sx, sy, "bark", 1)                          # the stem
    c.pixel(sx + math.cos(a), sy + math.sin(a), "leaf_summer_light", 2)
    return c.to_image()


def apple_barrel(full=1.0):
    """30 x 34: an oak barrel heaped with apples, mostly red, a few green. full: how high the heap is (it
    goes down as apples roll out, and fills up again)."""
    c = Canvas(30, 34)
    _barrel(c, 4, 33)
    rng = random.Random(6)
    n = int(8 + full * 12)
    for k in range(n):  # apples heaped in a mound over the rim, the top ones last
        layer = k / n
        x = 15 + rng.uniform(-10, 10) * (1 - layer * 0.65)
        y = 12.5 - full * layer * 6 + rng.uniform(-0.6, 0.6)
        mat = "apple_green" if rng.random() < 0.2 else "apple"
        c.ellipse(x, y, 2.4, 2.2, mat)
        c.pixel(x - 0.8, y - 0.9, mat, 3)
        if rng.random() < 0.35:
            c.pixel(x + 0.3, y - 2.2, "bark", 1)
    return c.to_image()


def well(bucket=0.0, splash=0.0):
    """46 x 64: a round stone well with two wooden posts, a little shingled roof, a crank and a bucket on a rope.
    bucket: 0 hanging up under the roof .. 1 down in the well (hidden). splash: water splashing up at the rim."""
    c = Canvas(46, 64)
    ground = 62
    rng = random.Random(8)
    # the posts and the cross-beam with its crank
    c.capsule(9, ground - 10, 9, 14, 1.4, 1.4, "post")
    c.capsule(37, ground - 10, 37, 14, 1.4, 1.4, "post")
    c.capsule(9, 18, 37, 18, 1.0, 1.0, "post", bias=0.1)
    c.capsule(37, 18, 42, 18, 0.7, 0.7, "hoop")
    c.capsule(42, 18, 42, 22, 0.6, 0.6, "hoop")
    # the roof: two slopes of shingles
    for y in range(4, 15):
        half = (y - 4) * 2.0 + 2
        for x in range(int(23 - half), int(23 + half) + 1):
            level = 2 if x < 23 else 1
            if (y + (x // 4) * 2) % 4 == 0:
                level -= 1  # the rows of shingles
            _px(c, x, y, "shingle", max(0, level))
    # the rope and the bucket
    by = 22 + bucket * 30
    if bucket < 0.95:
        _twig(c, 23, 18, 23, by - 2, "twine", 2)
        for y in range(int(by - 2), int(by + 4)):
            half = 3.0 - (y - by) * 0.15
            for x in range(int(23 - half), int(23 + half) + 1):
                _px(c, x, y, "oak_wood", 2 if x < 23 else 1)
        _twig(c, 20, int(by - 2), 26, int(by - 2), "hoop", 2)
        if bucket < 0.05 and splash == 0:  # back up, full of water
            _twig(c, 21, int(by - 1), 25, int(by - 1), "water", 3)
    # the stone ring of the well, in front of the bucket
    top = ground - 18
    for y in range(top, ground + 1):
        for x in range(4, 43):
            _px(c, x, y, "well_stone", 1)
    for row, y in enumerate(range(top, ground + 1, 4)):  # courses of stones, staggered like brickwork
        for x0 in range(4 - (row % 2) * 4, 43, 8):
            _rock(c, rng, x0 + 4, y + 2, 3.8, 1.9, "well_stone")
    for x in range(3, 44):  # the cap stones round the rim
        _px(c, x, top - 1, "well_stone", 3 if x % 5 else 2)
        _px(c, x, top, "well_stone", 2)
    if splash:  # water splashing up out of the well
        for k in range(9):
            a = math.radians(200 + k * 17)
            d = 4 + splash * 8
            c.pixel(23 + math.cos(a) * d * 1.2, top - 2 + math.sin(a) * d, "water", 3 if k % 2 else 2)
    return c.to_image()


# -- summer fun: a slide and a kiddie pool --------------------------------------------------------------------

COMMON.update({
    "slide_chute": ("#b88a0c", "#e4b81c", "#f8d838", "#fcf088", "#5e4606"),
    "slide_frame": ("#8a1414", "#b41e1e", "#d83a32", "#ee6a58", "#460808"),
    "pool_ring": ("#1e5aa8", "#2e7ad0", "#4c9cec", "#8cc4f8", "#0e2c58"),
    "pool_water": ("#4aa0d8", "#70bce8", "#9ad4f4", "#c8ecfc", "#1e5a84"),
})


def slide(sway=0.0):
    """64 x 48: a little garden slide: a red ladder up to a platform, and a bright yellow chute curving down to
    the ground on the right."""
    c = Canvas(64, 48)
    ground = 46
    for x in (12, 18):  # the ladder's rails
        c.capsule(x, ground, x, 10, 0.8, 0.8, "slide_frame")
    for y in range(ground - 4, 12, -6):  # rungs
        _twig(c, 12, y, 18, y, "slide_frame", 2)
    c.capsule(12, 10, 25, 10, 1.0, 1.0, "slide_frame")      # the platform
    c.capsule(12, 10, 12, 4, 0.6, 0.6, "slide_frame")       # its little rails
    c.capsule(25, 10, 25, 5, 0.6, 0.6, "slide_frame")
    c.capsule(12, 4, 25, 4, 0.5, 0.5, "slide_frame")
    c.capsule(40, ground, 40, 28, 0.8, 0.8, "slide_frame")  # a leg under the chute
    pts = bezier((25, 11), (44, 16), (60, 44), 14)          # the chute: a curved, shiny yellow slope
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        c.capsule(x1, y1, x2, y2, 1.8, 1.8, "slide_chute", bias=0.2)
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):           # its raised red edge
        c.capsule(x1, y1 - 1.8, x2, y2 - 1.8, 0.5, 0.5, "slide_frame")
    c.capsule(58, 44, 63, 45, 1.4, 1.2, "slide_chute")      # the lip at the bottom
    return c.to_image()


# the slide's chute, from the top (frame x, y) to the bottom: where a fox goes when it slides down
SLIDE_CHUTE = [(25, 9), (34, 11), (42, 15), (49, 22), (55, 31), (60, 42)]


def pool(t=0.0, ripple=0.0):
    """64 x 18: a round inflatable kiddie pool: a puffy blue ring, water glinting inside. ripple: rings spreading
    across the water (when clicked)."""
    c = Canvas(64, 18)
    c.ellipse(32, 12, 30, 5.6, "pool_ring", bias=0.1)            # the outer ring, puffy
    c.ellipse(32, 10, 29, 4.0, "pool_ring", bias=0.35)          # its top
    c.ellipse(32, 9.6, 25, 2.8, "pool_water", bias=0.2)         # the water inside
    rng = random.Random(3)
    for k in range(7):  # glints moving across the water
        x = 12 + (k * 7 + t * 9) % 40
        c.pixel(x, 9 + rng.choice((-1, 0, 1)), "pool_water", 3)
    if ripple:
        for r in (ripple * 18, ripple * 9):
            if r > 2:
                for a in range(0, 360, 10):
                    x, y = 32 + math.cos(math.radians(a)) * r, 9.6 + math.sin(math.radians(a)) * r * 0.13
                    if ((x - 32) / 25) ** 2 + ((y - 9.6) / 2.8) ** 2 < 1:
                        c.pixel(x, y, "pool_water", 3)
    for x in range(6, 58, 9):  # the valve and seam marks on the ring
        c.pixel(x, 13, "pool_ring", 3)
    return c.to_image()


def droplet(k=0):
    """3 x 3: a drop of water flying off a splash."""
    c = Canvas(3, 3)
    c.pixel(1, 1, "water", 3 if k else 2)
    c.pixel(1, 2, "water", 1)
    return c.to_image(outline=False)


# -- more flowers: dahlias, dandelions, pansies; cattails ----------------------------------------------------

COMMON.update({
    "dahlia_magenta": ("#7a1450", "#a82070", "#d03c94", "#ec78bc", "#3e0828"),
    "dahlia_orange": ("#a8400c", "#d86018", "#f0842c", "#f8b060", "#541e04"),
    "dahlia_red": ("#7a0e1c", "#a81a2a", "#cc3440", "#e86870", "#40060c"),
    "dahlia_leaf": ("#1a3e14", "#28561e", "#38702a", "#56904a", "#0c200a"),
    "fluff": ("#c8c8bc", "#e4e4da", "#f4f4ee", "#ffffff", "#8a8a80"),
    "cattail": ("#4a2a12", "#663c1a", "#844e24", "#a26a38", "#24140a"),
    "pansy_purple": ("#3a1a6a", "#5226a0", "#7040c4", "#9a6ee0", "#1c0a38"),
    "pansy_yellow": ("#b8980c", "#e4c418", "#f8e030", "#fcf080", "#5e4c04"),
})
DAHLIA_HEADS = [(8, 9), (16, 4), (24, 8), (31, 3), (37, 9)]
DAHLIA_COLOURS = ("dahlia_magenta", "dahlia_orange", "dahlia_red", "daffodil", "dahlia_magenta")


def dahlias(sway=0.0):
    """44 x 26: a clump of dahlias: big round pom-pom flowers of many layered petals, in magenta, orange, red
    and yellow, over dark leaves."""
    c = Canvas(44, 26)
    ground = 24
    rng = random.Random(12)
    for x in range(5, 41, 4):  # dark, toothed leaves low down
        c.ellipse(x + rng.uniform(-1, 1), ground - rng.uniform(3, 7), 2.6, 1.8, "dahlia_leaf", angle=rng.uniform(-30, 30))
    for k, (x, y) in enumerate(DAHLIA_HEADS):
        hx = x + sway * (1 - y / ground) * 1.4
        _twig(c, x, ground, hx, y + 3, "stalk", 1)
        mat = DAHLIA_COLOURS[k]
        c.ellipse(hx, y, 3.4, 3.0, mat, bias=-0.1)  # outer petals...
        for a in range(0, 360, 45):                 # ...pointed petal tips round the edge...
            c.pixel(hx + math.cos(math.radians(a)) * 3.8, y + math.sin(math.radians(a)) * 3.4, mat, 1)
        c.ellipse(hx, y - 0.3, 2.2, 1.9, mat, bias=0.3)  # ...rings of petals getting lighter toward the middle
        c.ellipse(hx, y - 0.5, 1.0, 0.9, mat, bias=0.6)
    for x in range(2, 42):
        c.pixel(x, ground + 1, "dirt", 1 if x % 3 else 2)
    return c.to_image()


DANDELION_HEADS = [(6, 6), (13, 3), (20, 7), (27, 4), (34, 6)]


def dandelions(season="summer", sway=0.0, bare=False):
    """40 x 16: dandelions: jagged leaves in rosettes on the ground, and on tall stems either bright yellow
    flowers (summer) or white seed-heads, the clocks (spring). bare: the seeds have blown away (stems only)."""
    c = Canvas(40, 16)
    ground = 14
    for x in (6, 17, 29):  # rosettes of toothed leaves
        for side in (-1, 1):
            for k in range(3):
                tx = x + side * (3 + k * 1.6)
                c.pixel(tx, ground - 1 - (k % 2), "stalk", 2 if k % 2 else 1)
            _twig(c, x, ground, x + side * 6, ground - 1, "stalk", 1)
    for x, y in DANDELION_HEADS:
        hx = x + sway * (1 - y / ground) * 1.2
        _twig(c, x, ground, hx, y + 1, "stalk", 2)
        if season == "summer":
            c.ellipse(hx, y, 2.0, 1.7, "daffodil", bias=0.1)  # a shaggy yellow flower
            for a in range(0, 360, 60):
                c.pixel(hx + math.cos(math.radians(a)) * 2.4, y + math.sin(math.radians(a)) * 2.0, "daffodil", 3)
            c.pixel(hx, y, "daffodil_cup", 2)
        elif not bare:  # a seed clock: a fluffy white ball
            c.ellipse(hx, y, 2.4, 2.2, "fluff", bias=0.2)
            for a in range(0, 360, 40):
                c.pixel(hx + math.cos(math.radians(a)) * 2.8, y + math.sin(math.radians(a)) * 2.6, "fluff", 2)
        else:
            c.pixel(hx, y, "stalk", 3)  # just the bare tip of the stem
    return c.to_image(outline=not (season == "spring" and not bare))


def fluff(k=0, mat="fluff"):
    """5 x 5: a seed on its tuft of fluff, drifting on the wind (a dandelion's or a cattail's)."""
    c = Canvas(5, 5)
    for a in range(0, 360, 60):
        x, y = 2 + math.cos(math.radians(a + k * 30)) * 1.6, 1.6 + math.sin(math.radians(a + k * 30)) * 1.2
        c.pixel(x, y, mat, 3)
    c.pixel(2, 3, "cattail" if mat == "fluff" else mat, 1)
    return c.to_image(outline=False)


CATTAILS = [(6, 0.86), (15, 1.0), (24, 0.9), (33, 1.06), (42, 0.94)]  # x, height share
CATTAIL_HEIGHT = 52


def cattails(stage, sway=0.0, burst=0.0):
    """50 x 60: a stand of cattails. Stages: 0 shoots, 1 tall grassy leaves, 2 green heads, 3 brown velvety heads
    (ripe), 4 the heads gone fluffy. burst: the fluff exploding off them (when clicked)."""
    c = Canvas(50, 60)
    ground = 58
    full = (10, 30, 48, CATTAIL_HEIGHT, CATTAIL_HEIGHT)[stage]
    for i, (x, share) in enumerate(CATTAILS):
        h = full * share
        lean = sway * (h / CATTAIL_HEIGHT) * (0.6 + 0.4 * (i % 2))
        top = (x + lean, ground - h)
        for side in (-1, 1):  # long, flat, grassy leaves
            _twig(c, x, ground, x + side * 3 + lean * 0.7, ground - h * 0.75, "stalk", 2 if side < 0 else 1)
        _twig(c, x, ground, top[0], top[1], "stalk", 1)
        if stage >= 2:
            hy = top[1] + 7
            mat = "stalk" if stage == 2 else "cattail"
            c.capsule(top[0], hy - 5, top[0] + lean * 0.05, hy + 3, 1.6, 1.6, mat, bias=0.1)  # the head
            _twig(c, top[0], hy - 5, top[0], hy - 8, "stalk", 2)                              # its spike
            if stage == 4 or burst:  # gone to fluff
                for k in range(6 + int(burst * 6)):
                    a = random.Random(i * 10 + k).uniform(0, 2 * math.pi)
                    d = 2.2 + burst * random.Random(i * 10 + k + 5).uniform(2, 8)
                    c.pixel(top[0] + math.cos(a) * d, hy - 1 + math.sin(a) * d * 1.5, "fluff", 3)
    return c.to_image()


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


# -- the vegetable garden: tomatoes, radishes, lettuce, watermelons --------------------------------------------

COMMON.update({
    "tomato": ("#8a1010", "#c41c16", "#e8382a", "#f6745e", "#480606"),
    "tomato_green": ("#4e7a1a", "#6e9e26", "#8ebe3a", "#b4dc66", "#283e0a"),
    "radish": ("#9a1a40", "#c82a5a", "#e6487a", "#f488aa", "#500a20"),
    "lettuce": ("#5a9420", "#7cb82c", "#9ed444", "#c4ec7a", "#2e520c"),
    "melon": ("#1a4a14", "#26641c", "#347e28", "#4c9a3c", "#0c260a"),
    "melon_light": ("#5a8a2a", "#78aa3a", "#98c650", "#bcdc7a", "#2e4a12"),
    "melon_flesh": ("#a8162c", "#d82a3c", "#f04a58", "#f88a90", "#560a14"),
})
TOMATO_PLANTS = [10, 27, 44, 61]  # x of each plant (on its stake)


def tomatoes(stage, sway=0.0):
    """72 x 44: a row of four tomato plants tied to stakes. Stages: 0 seedlings, 1 small plants, 2 bushy with
    yellow flowers, 3 green tomatoes, 4 ripe red tomatoes."""
    c = Canvas(72, 44)
    ground = 42
    rng = random.Random(14)
    height = (6, 16, 28, 34, 34)[stage]
    for x in TOMATO_PLANTS:
        if stage >= 1:
            _twig(c, x + 3, ground, x + 3, ground - 36, "post", 2)  # the stake
        _twig(c, x, ground, x + sway * 0.5, ground - height, "stalk", 1)
        for k in range(1 + stage * 2):  # leafy branches
            y = ground - height * rng.uniform(0.25, 1.0)
            side = rng.choice((-1, 1))
            lx = x + side * rng.uniform(2, 6) + sway * (1 - y / ground)
            c.ellipse(lx, y, 2.2, 1.5, "leaf_summer_dark" if k % 2 else "stalk", angle=side * 25)
        if stage == 2:
            for _ in range(3):
                c.pixel(x + rng.uniform(-4, 4), ground - height * rng.uniform(0.4, 0.9), "daffodil", 3)
        if stage >= 3:
            mat = "tomato" if stage == 4 else "tomato_green"
            for dx, dy in ((-3, 0.55), (3, 0.45), (0, 0.7)):  # a truss of tomatoes
                tx, ty = x + dx + sway * 0.4, ground - height * dy
                c.ellipse(tx, ty, 2.1, 1.9, mat)
                c.pixel(tx - 0.7, ty - 0.8, mat, 3)
                c.pixel(tx, ty - 2, "stalk", 2)
    for x in range(2, 70):
        c.pixel(x, ground + 1, "dirt", 1 if x % 3 else 2)
    return c.to_image()


ROW_PLANTS = {"radishes": [6, 15, 24, 33, 42, 51], "lettuce": [9, 23, 37, 51]}


def radishes(stage, sway=0.0):
    """58 x 18: a row of radishes. Stages: 0 sprouts, 1 small leaves, 2 bigger leaves, 3 red shoulders showing,
    4 fat red radishes pushing up (ripe)."""
    c = Canvas(58, 18)
    ground = 15
    for x in ROW_PLANTS["radishes"]:
        size = (0.4, 0.7, 1.0, 1.1, 1.2)[stage]
        for side in (-1, 0, 1):  # a little fan of leaves
            tip = (x + side * 3.5 * size + sway * 0.4, ground - 7 * size - (1 if side == 0 else 0))
            _twig(c, x, ground, *tip, "stalk", 2 if side else 1)
            if stage >= 1:
                c.ellipse(tip[0], tip[1], 1.6 * size, 1.1 * size, "lettuce", angle=side * 30)
        if stage >= 3:
            c.ellipse(x, ground + 0.4, 1.8 + (stage - 3), 1.4 + (stage - 3) * 0.5, "radish", bias=0.2)
    for x in range(1, 57):
        c.pixel(x, ground + 1, "dirt", 1 if x % 3 else 2)
        c.pixel(x, ground + 2, "dirt", 0)
    return c.to_image()


def lettuce(stage, sway=0.0):
    """58 x 18: a row of lettuces. Stages: 0 sprouts, 1 small rosettes, 2 bigger, 3 heads forming, 4 full,
    frilly heads (ripe)."""
    c = Canvas(58, 18)
    ground = 15
    for x in ROW_PLANTS["lettuce"]:
        size = (0.3, 0.55, 0.8, 1.0, 1.2)[stage]
        for k, (dx, dy, mat) in enumerate(((-3.5, 1.5, "stalk"), (3.5, 1.5, "stalk"), (-2, -0.5, "lettuce"),
                                           (2, -0.5, "lettuce"), (0, -2.5, "lettuce"))):
            c.ellipse(x + dx * size + sway * 0.2 * (k > 1), ground - 3 * size + dy * size, 3.0 * size, 2.6 * size,
                      mat, bias=0.1 * k)
        if stage >= 3:
            for a in range(0, 360, 45):  # frilly edges
                c.pixel(x + math.cos(math.radians(a)) * 4.5 * size, ground - 3 * size + math.sin(math.radians(a)) * 3 * size,
                        "lettuce", 3)
    for x in range(1, 57):
        c.pixel(x, ground + 1, "dirt", 1 if x % 3 else 2)
        c.pixel(x, ground + 2, "dirt", 0)
    return c.to_image()


def tomato(roll=0):
    """8 x 8: a ripe tomato, rolling."""
    c = Canvas(8, 8)
    c.ellipse(4, 4.4, 2.8, 2.5, "tomato")
    a = roll * math.pi / 2
    c.pixel(4 - math.sin(a) * 1.2, 3 + (1 - math.cos(a)), "tomato", 3)
    for dx in (-1, 0, 1):  # the green star of a calyx, turning
        c.pixel(4 + math.sin(a) * 2 + dx * math.cos(a), 4.4 - math.cos(a) * 2.2 + dx * math.sin(a), "stalk", 2)
    return c.to_image()


def radish(roll=0):
    """10 x 10: a pulled radish: a round red root with a white tip and a tuft of leaves."""
    c = Canvas(10, 10)
    a = roll * math.pi / 2
    def at(dx, dy):
        return 5 + dx * math.cos(a) - dy * math.sin(a), 5.5 + dx * math.sin(a) + dy * math.cos(a)
    c.ellipse(*at(0, 1), 2.4, 2.4, "radish", bias=0.2)
    c.pixel(*at(0, 3.6), "white", 2)
    for dx in (-1.6, 0, 1.6):
        c.capsule(*at(0, -1), *at(dx, -4.2), 0.6, 0.8, "lettuce")
    return c.to_image()


def lettuce_head(roll=0):
    """10 x 10: a whole head of lettuce, frilly and green."""
    c = Canvas(10, 10)
    c.ellipse(5, 6, 4.0, 3.4, "lettuce", bias=0.1)
    c.ellipse(5, 5.2, 2.6, 2.2, "lettuce", bias=0.4)
    for k in range(8):
        ang = math.radians(k * 45 + roll * 22)
        c.pixel(5 + math.cos(ang) * 4.2, 6 + math.sin(ang) * 3.4, "stalk", 2)
    return c.to_image()


MELON_SHAPES = {"round": (1.0, 1.0), "long": (1.45, 0.82)}


def _melon_body(c, cx, base, size, shape, flesh=0.0):
    """A watermelon lying on the ground: dark green with pale stripes."""
    wide, high = MELON_SHAPES[shape]
    w, h = 9.0 * size * wide, 6.2 * size * high
    cy = base - h
    c.ellipse(cx, cy, w, h, "melon", bias=0.05)
    for k in range(-3, 4):  # pale stripes running along it
        sx = cx + k * w / 4
        for y in range(int(cy - h), int(cy + h) + 1):
            dx = math.sin((y - cy) / h * 1.4) * 1.2
            x = sx + dx * (1 - abs(k) / 4)
            if ((x - cx) / w) ** 2 + ((y - cy) / h) ** 2 < 0.92:
                c.pixel(x, y, "melon_light", 2)
    return cy - h


def melon(stage, sway=0.0, grow=1.0, shape="round"):
    """44 x 36. Stages: 0 sprout, 1 vine with a yellow flower, 2 small striped melon, 3 bigger, 4 big and ripe.
    grow scales it (small, medium or large)."""
    c = Canvas(44, 36)
    ground = 30
    reach = (4, 13, 15, 16, 17)[stage]
    c.capsule(20 - reach, ground, 20 + reach * 0.8, ground - 0.5, 0.8, 0.7, "vine")
    for dx in ((-reach + 2, reach * 0.7) if stage else (-2.5, 2.5)):  # lobed leaves
        lx, ly = 20 + dx, ground - 3 + sway * 0.4
        c.ellipse(lx, ly, 3.0, 2.2, "vine", angle=-20 if dx < 0 else 20)
        c.pixel(lx, ly - 1, "vine", 3)
    if stage == 0:
        c.capsule(20, ground, 20 + sway * 0.5, ground - 5, 0.8, 0.7, "vine")
        return c.to_image()
    if stage == 1:
        for a in range(5):
            ang = a / 5 * 2 * math.pi
            c.ellipse(23 + math.cos(ang) * 1.6, ground - 7 + math.sin(ang) * 1.6, 1.2, 1.2, "daffodil")
        return c.to_image()
    size = {2: 0.5, 3: 0.8, 4: 1.1}[stage] * grow
    top = _melon_body(c, 20, ground + 0.5, size, shape)
    c.capsule(20, top + 1, 21, top - 1.5, 0.6, 0.5, "stem")
    return c.to_image()


def melon_split(grow, shape, t):
    """A ripe watermelon clicked: it cracks and falls open in two halves, red flesh and black seeds, then the
    halves sink away."""
    c = Canvas(44, 36)
    ground = 30
    c.capsule(3, ground, 34, ground - 0.5, 0.8, 0.7, "vine")
    size = 1.1 * grow
    wide, high = MELON_SHAPES[shape]
    w, h = 9.0 * size * wide, 6.2 * size * high
    if t < 0.3:
        _melon_body(c, 20, ground + 0.5, size, shape)
        for y in range(int(ground - 2 * h * t / 0.3), int(ground)):  # a crack down the middle
            c.pixel(20, y, "melon_flesh", 2)
        return c.to_image()
    open_ = min(1.0, (t - 0.3) / 0.4)
    sink = max(0.0, (t - 0.7) / 0.3)
    for side in (-1, 1):  # two halves, rocked open, flesh up
        hx = 20 + side * (3 + open_ * 4)
        c.ellipse(hx, ground - h * 0.5 * (1 - sink * 0.6), w * 0.5, h * 0.55 * (1 - sink * 0.6), "melon")
        c.ellipse(hx, ground - h * 0.85 * (1 - sink * 0.6), w * 0.45, h * 0.3 * (1 - sink * 0.6), "melon_flesh", bias=0.3)
        for k in range(4):
            c.pixel(hx - w * 0.25 + k * w * 0.16, ground - h * 0.85 * (1 - sink * 0.6), "bug_black", 0)
    return c.to_image()


def tray_icon():
    """32 x 32 fox face for the tray."""
    import fox_art
    c = Canvas(32, 32)
    fox_art.head(c, 13, 18, tilt=0, eyes="open")
    return c.to_image()


LEAF_COLOURS = ("leaf_red", "leaf_orange", "leaf_yellow", "leaf_brown", "leaf_green")

SPRITES = {
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
    "squirrel_run": ([squirrel("run", i / 4) for i in range(4)], 70, True, (16, 29)),
    "squirrel_carry": ([squirrel("run", i / 4, acorn_in_mouth=True) for i in range(4)], 70, True, (16, 29)),
    "squirrel_sit": ([squirrel("sit", i / 4) for i in range(4)], 160, True, (16, 29)),
    "squirrel_dig": ([squirrel("dig", i / 4) for i in range(4)], 90, True, (16, 29)),
    "jay_fly": ([jay("fly", i / 4) for i in range(4)], 80, True, (12, 20)),
    "jay_perch": ([jay("perch", i / 4) for i in range(2)], 500, True, (12, 22)),
    "jay_hop": ([jay("hop", i / 4) for i in range(4)], 110, True, (12, 22)),
    "woolly": ([woolly(i / 6) for i in range(6)], 140, True, (12, 8)),
    "tray_icon": ([tray_icon()], 1000, False, (16, 31)),
    "goose_walk": ([goose("walk", i / 4) for i in range(4)], 140, True, (16, 30)),
    "goose_honk": ([goose("honk", f) for f in (0.0, 0.3, 0.5, 0.8)], 110, False, (16, 30)),
    "goose_fly": ([goose("fly", i / 4) for i in range(4)], 110, True, (16, 22)),
    "goose_far": ([goose_far(i / 4) for i in range(4)], 140, True, (7, 5)),
    "honk_bubble": ([honk_bubble()], 1000, False, (4, 13)),
    **{f"pumpkin_{s}_{k}_{shape}": ([pumpkin(s, sw, g, shape) for sw in (0, 1, 0, -1)], 700, True, (20, 30))
       for s in range(5) for k, g in PUMPKIN_SIZES.items() for shape in PUMPKIN_SHAPES},
    **{f"pumpkin_4_{k}_{shape}_jack": ([pumpkin(4, sw, g, shape, jack=True) for sw in (0, 1, 0, -1)], 260, True,
                                       (20, 30))
       for k, g in PUMPKIN_SIZES.items() for shape in PUMPKIN_SHAPES},
    **{f"corn_{s}": ([corn(s, sw) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 300, True, (60, 98)) for s in range(5)},
    "barrels": ([barrels()], 1000, False, (35, 62)),
    **{name: ([hay(name)], 1000, False, layout[1]) for name, layout in HAY_LAYOUTS.items()},
    "crumb": ([crumb(i) for i in range(2)], 120, True, (2, 2)),
    "straw_bit": ([straw_bit(s) for s in range(4)], 90, True, (3, 3)),
    "barrels_fall": (barrels_falling(), 90, False, (55, 62)),
    "hoe_wobble": ([hoe_tilt(a) for a in (0, 7, -6, 4, -3, 1, 0)], 80, False, (14, 58)),
    "corncob": ([corncob(r) for r in range(4)], 90, True, (7, 10)),
    "frog_sit": ([frog("sit", f) for f in (0.0, 0.5, 1.0, 0.5)], 160, True, (9, 15)),
    "frog_hop": ([frog("hop", f) for f in (0.0, 0.35, 0.7, 1.0)], 90, True, (9, 15)),
    "ribbit_bubble": ([word_bubble("RIBBIT")], 1000, False, (4, 13)),
    "turkey_run": ([turkey("run", i / 4) for i in range(4)], 70, True, (20, 38)),
    "turkey_stand": ([turkey("stand", i / 4) for i in range(2)], 600, True, (20, 38)),
    "turkey_look": ([turkey("look", f) for f in (0.0, 0.25, 0.25, 0.0, 0.0)], 260, True, (20, 38)),
    "turkey_gobble": ([turkey("gobble", f) for f in (0.0, 0.25, 0.5, 0.75, 1.0, 1.0)], 110, False, (20, 38)),
    "turkey_peck": ([turkey("peck", i / 4) for i in range(4)], 120, True, (20, 38)),
    "gobble_bubble": ([word_bubble("GOBBLE!")], 1000, False, (4, 13)),
    "crow_fly": ([crow("fly", i / 4) for i in range(4)], 85, True, (12, 20)),
    "crow_carry": ([crow("fly", i / 4, acorn_in_beak=True) for i in range(4)], 85, True, (12, 20)),
    "crow_perch": ([crow("perch", i / 4) for i in range(2)], 600, True, (12, 22)),
    "crow_hop": ([crow("hop", i / 4) for i in range(4)], 100, True, (12, 22)),
    "crow_walk": ([crow("walk", i / 4) for i in range(4)], 140, True, (12, 22)),
    "crow_peck": ([crow("peck", i / 4) for i in range(4)], 110, True, (12, 22)),
    "crow_tilt": ([crow("tilt", i / 4) for i in range(2)], 500, True, (12, 22)),
    "crow_caw": ([crow("caw", f) for f in (0.0, 0.3, 0.6, 0.9)], 120, False, (12, 22)),
    "caw_bubble": ([word_bubble("CAW!")], 1000, False, (4, 13)),
    "twig": ([twig(k) for k in range(8)], 90, True, (8, 9)),
    "snow_clump": ([snow_clump(k) for k in range(2)], 120, True, (4, 4)),
    "snow_puff": ([snow_puff(t) for t in (0.0, 0.3, 0.6, 1.0)], 110, False, (8, 7)),
    "inchworm": ([inchworm("crawl", t) for t in (0.0, 0.25, 0.5, 0.75)], 160, True, (7, 7)),
    "inchworm_fall": ([inchworm("fall")], 1000, False, (7, 6)),
    "butterfly": ([butterfly(t) for t in (0.0, 0.25, 0.5, 0.75)], 70, True, (7, 7)),
    "junebug_crawl": ([beetle("junebug", "crawl", t) for t in (0.0, 0.25, 0.5, 0.75)], 120, True, (5, 11)),
    "junebug_fly": ([beetle("junebug", "fly", t) for t in (0.0, 0.25, 0.5, 0.75)], 50, True, (5, 11)),
    "ladybug_crawl": ([beetle("ladybug", "crawl", t) for t in (0.0, 0.25, 0.5, 0.75)], 120, True, (5, 11)),
    "ladybug_fly": ([beetle("ladybug", "fly", t) for t in (0.0, 0.25, 0.5, 0.75)], 50, True, (5, 11)),
    "cicada_sit": ([cicada("sit")], 1000, False, (5, 13)),
    "cicada_buzz": ([cicada("buzz", t) for t in (0.0, 0.125, 0.25, 0.375)], 40, True, (5, 13)),
    "cicada_fly": ([cicada("fly", t) for t in (0.0, 0.25, 0.5, 0.75)], 50, True, (5, 13)),
    "buzz_bubble": ([word_bubble("BZZZZZ!")], 1000, False, (4, 13)),
    "spider": ([spider(t) for t in (0.0, 0.25, 0.5, 0.75)], 140, True, (6, 2)),
    "silk": ([silk()], 1000, False, (0, 0)),
    **{f"birch_{season}": ([birch(season, s) for s in (0, 1, 1, 0, -1, -1)], 650, True, (BIRCH_X, BIRCH_GROUND),
                           {"perches": BIRCH_PERCHES})
       for season in ("winter", "spring", "summer", "autumn")},
    "birch_snow": ([birch("winter", s, snow=True) for s in (0, 1, 1, 0, -1, -1)], 650, True, (BIRCH_X, BIRCH_GROUND),
                   {"perches": BIRCH_PERCHES}),
    "woodstack": ([woodstack()], 1000, False, (30, 35)),
    "woodstack_snow": ([woodstack(snow=True)], 1000, False, (30, 35)),
    "apple": ([apple(k) for k in range(4)], 110, True, (4, 7)),
    "apple_bit": ([chip("apple", s, 0.9) for s in range(4)], 90, True, (3, 3)),
    "apple_barrel": ([apple_barrel()], 1000, False, (15, 33)),
    "apple_barrel_wobble": ([apple_barrel(f) for f in (1.0, 0.9, 1.0, 0.95, 1.0)], 80, False, (15, 33)),
    "well": ([well()], 1000, False, (23, 62)),
    "well_bucket": ([well(b) for b in (0.0, 0.25, 0.5, 0.75, 1.0)] + [well(1.0, s) for s in (0.3, 0.7, 1.0)] +
                    [well(b) for b in (0.9, 0.7, 0.45, 0.2, 0.0)], 110, False, (23, 62)),
    "slide": ([slide()], 1000, False, (32, 46), {"chute": SLIDE_CHUTE}),
    "pool": ([pool(t) for t in (0, 0.33, 0.66)], 300, True, (32, 16)),
    "pool_ripple": ([pool(0, r) for r in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0)], 90, False, (32, 16)),
    "droplet": ([droplet(k) for k in range(2)], 100, True, (1, 1)),
    "dahlias": ([dahlias(sw) for sw in (0, 1, 0, -1)], 560, True, (22, 24), {"perches": DAHLIA_HEADS}),
    "dahlias_bob": ([dahlias(sw) for sw in (2, -2, 1.5, -1.2, 0.6, 0)], 90, False, (22, 24), {"perches": DAHLIA_HEADS}),
    **{f"dandelions_{season}": ([dandelions(season, sw) for sw in (0, 1, 0, -1)], 520, True, (20, 14),
                                {"perches": DANDELION_HEADS})
       for season in ("spring", "summer")},
    "dandelions_spring_bare": ([dandelions("spring", sw, bare=True) for sw in (0, 1, 0, -1)], 520, True, (20, 14)),
    "dandelions_summer_bob": ([dandelions("summer", sw) for sw in (2, -2, 1.5, -1, 0.5, 0)], 90, False, (20, 14),
                              {"perches": DANDELION_HEADS}),
    "fluff": ([fluff(k) for k in range(4)], 160, True, (2, 2)),
    "cattail_fluff": ([fluff(k, "log_end") for k in range(4)], 160, True, (2, 2)),
    **{f"cattails_{s}": ([cattails(s, sw) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 300, True, (25, 58)) for s in range(5)},
    "cattails_burst": ([cattails(3, 0, b) for b in (0.2, 0.5, 0.8, 1.0)] + [cattails(0, 0)], 110, False, (25, 58)),
    **{f"tomatoes_{s}": ([tomatoes(s, sw) for sw in (0, 1, 0, -1)], 500, True, (36, 42)) for s in range(5)},
    **{f"radishes_{s}": ([radishes(s, sw) for sw in (0, 1, 0, -1)], 520, True, (29, 15)) for s in range(5)},
    **{f"lettuce_{s}": ([lettuce(s, sw) for sw in (0, 1, 0, -1)], 560, True, (29, 15)) for s in range(5)},
    "tomato": ([tomato(k) for k in range(4)], 110, True, (4, 7)),
    "radish": ([radish(k) for k in range(4)], 110, True, (5, 8)),
    "lettuce_head": ([lettuce_head(k) for k in range(4)], 140, True, (5, 9)),
    "leaf_bit": ([chip("lettuce", s, 1.0) for s in range(4)], 90, True, (3, 3)),
    **{f"melon_{s}_{k}_{shape}": ([melon(s, sw, g, shape) for sw in (0, 1, 0, -1)], 700, True, (20, 30))
       for s in range(5) for k, g in PUMPKIN_SIZES.items() for shape in MELON_SHAPES},
    **{f"melon_split_{k}_{shape}": ([melon_split(g, shape, t) for t in (0.1, 0.25, 0.4, 0.6, 0.75, 0.9, 1.0)], 140,
                                    False, (20, 30))
       for k, g in PUMPKIN_SIZES.items() for shape in MELON_SHAPES},
    **{f"butterfly_{kind}": ([butterfly(t, kind) for t in (0.0, 0.25, 0.5, 0.75)], 70, True, (7, 7))
       for kind in ("white", "sulphur", "azure")},
    **{f"butterfly_{kind}_rest": ([butterfly(kind=kind, span=sp) for sp in (1.0, 0.8, 0.45, 0.3, 0.45, 0.8)], 260,
                                  True, (7, 10))
       for kind in BUTTERFLIES},
    **{kind: ([flower_bed(kind, sw) for sw in (0, 1, 0, -1)], 520, True, (22, 22), {"perches": heads})
       for kind, heads in FLOWER_BEDS.items()},
    **{f"{kind}_bob": ([flower_bed(kind, sw) for sw in (2, -2, 1.5, -1.2, 0.6, 0)], 90, False, (22, 22),
                       {"perches": heads})
       for kind, heads in FLOWER_BEDS.items()},
    **{f"{kind}_{pose}": ([songbird(kind, pose, i / n) for i in range(n)], ms, True, (10, 18))
       for kind in SONGBIRDS
       for pose, n, ms in (("perch", 2, 600), ("hop", 4, 90), ("fly", 4, 70), ("sing", 4, 140), ("peck", 4, 110))},
    "robin_worm": ([songbird("robin", "worm", i / 4) for i in range(4)], 160, True, (10, 18)),
    "note": ([note()], 1000, False, (4, 9)),
    "note_double": ([note(True)], 1000, False, (4, 9)),
    "sled": ([sled()], 1000, False, (22, 16)),
    "sled_snow": ([sled(snow=True)], 1000, False, (22, 16)),
    "sled_wobble": ([sled(tilt=a) for a in (0, 2, -1.5, 1, -0.5, 0)], 80, False, (22, 16)),
    "sled_snow_wobble": ([sled(snow=True, tilt=a) for a in (0, 2, -1.5, 1, -0.5, 0)], 80, False, (22, 16)),
    "stump": ([stump()], 1000, False, (18, 24)),
    "stump_snow": ([stump(snow=True)], 1000, False, (18, 24)),
    "xmas_tree": ([xmas_tree(t) for t in (0, 0.25, 0.5)], 450, True, (16, 46)),
    "xmas_tree_snow": ([xmas_tree(t, snow=True) for t in (0, 0.25, 0.5)], 450, True, (16, 46)),
    "xmas_tree_sparkle": ([xmas_tree(t, sparkle=k % 2 == 0) for k, t in enumerate((0, 0, 0, 0, 0, 0.25))], 120,
                          False, (16, 46)),
    "xmas_tree_snow_sparkle": ([xmas_tree(t, snow=True, sparkle=k % 2 == 0) for k, t in enumerate((0, 0, 0, 0, 0, 0.25))],
                               120, False, (16, 46)),
    "caw2_bubble": ([word_bubble("CAW CAW!")], 1000, False, (4, 13)),
    "kraa_bubble": ([word_bubble("KRAA!")], 1000, False, (4, 13)),
    "cawq_bubble": ([word_bubble("CAW?")], 1000, False, (4, 13)),
    "crow_hat_fly": ([crow("fly", i / 4, hat=True) for i in range(4)], 85, True, (12, 20)),
    "crow_hat_perch": ([crow("perch", i / 4, hat=True) for i in range(2)], 600, True, (12, 22)),
    "crow_hat_hop": ([crow("hop", i / 4, hat=True) for i in range(4)], 100, True, (12, 22)),
    "crow_hat_walk": ([crow("walk", i / 4, hat=True) for i in range(4)], 140, True, (12, 22)),
    "crow_hat_peck": ([crow("peck", i / 4, hat=True) for i in range(4)], 110, True, (12, 22)),
    "crow_hat_tilt": ([crow("tilt", i / 4, hat=True) for i in range(2)], 500, True, (12, 22)),
    "crow_hat_caw": ([crow("caw", f, hat=True) for f in (0.0, 0.3, 0.6, 0.9)], 120, False, (12, 22)),
    "scarecrow_nohat": ([scarecrow(sw, hat=False) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 260, True, (24, 85)),
    "scarecrow_surprised_nohat": ([scarecrow(0, True, hat=False) for _ in range(7)], 110, False, (24, 85)),
    "scarecrow_hat": ([scarecrow_hat()], 1000, False, (12, 11)),
    "kernel": ([chip("cob", s, 0.9) for s in range(4)], 90, True, (3, 3)),
    "pumpkin_bit": ([chip("pumpkin", s, 1.2) for s in range(4)], 90, True, (3, 3)),
    **{f"pumpkin_giant_{shape}": ([pumpkin_giant(shape, sw) for sw in (0, 1, 0, -1)], 900, True, (34, 50))
       for shape in PUMPKIN_SHAPES},
    **{f"pumpkin_giant_{shape}_jack": ([pumpkin_giant(shape, sw, jack=True) for sw in (0, 1, 0, -1)], 260, True,
                                       (34, 50))
       for shape in PUMPKIN_SHAPES},
    **{f"pumpkin_burst_{shape}": ([pumpkin_burst(shape, t) for t in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 1.0, 1.0)],
                                  130, False, (34, 50))
       for shape in PUMPKIN_SHAPES},
    "scarecrow_surprised": ([scarecrow(0, True, u) for u in (2, 5, 6, 5, 3, 1, 0)], 110, False, (24, 85)),
    **{f"pumpkin_wilt_{k}_{shape}": ([pumpkin_wilt(g, shape, w) for w in (0.0, 0.3, 0.55, 0.8, 1.0)], 160, False,
                                     (20, 30))
       for k, g in PUMPKIN_SIZES.items() for shape in PUMPKIN_SHAPES},
    "hoe": ([hoe()], 1000, False, (14, 58)),
    "den": ([den()], 1000, False, (56, 54)),
    "den_orange": ([den(("orange",))], 1000, False, (56, 54)),
    "den_grey": ([den(("grey",))], 1000, False, (56, 54)),
    "den_both": ([den(("orange", "grey"))], 1000, False, (56, 54)),
    "den_snow": ([den(snow=True)], 1000, False, (56, 54)),
    "den_snow_orange": ([den(("orange",), snow=True)], 1000, False, (56, 54)),
    "den_snow_grey": ([den(("grey",), snow=True)], 1000, False, (56, 54)),
    "den_snow_both": ([den(("orange", "grey"), snow=True)], 1000, False, (56, 54)),
    "zzz": ([zzz()], 1000, False, (5, 9)),
    "scarecrow": ([scarecrow(sw) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 260, True, (24, 85)),
}
for colour in LEAF_COLOURS:
    SPRITES[f"leaf_{colour.split('_')[1]}"] = ([leaf(colour, s) for s in range(6)], 150, True, (6, 6))
