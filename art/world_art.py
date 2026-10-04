"""Everything that isn't a fox: the oak, its leaves and acorns, and the autumn visitors.

SPRITES: name -> (frames, ms per frame, loop, anchor). The anchor is the frame point that sits on the
item's position (the trunk base, a paw on the ground...).
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


def oak(sway=0.0, seed=7):
    """220 x 232. Flat pixel-art trunk and branches; a big leafy crown. sway moves the crown a little."""
    c = Canvas(OAK_W, OAK_H)
    rng = random.Random(seed)
    # the trunk: straight stepped sides, tapering upward, with a flared base
    for y in range(120, OAK_GROUND + 1):
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
    for x1, y1, x2, y2, w in ((OAK_X - 3, 152, OAK_X - 44, 104, 5), (OAK_X + 3, 146, OAK_X + 46, 100, 5),
                              (OAK_X, 136, OAK_X - 6, 86, 5), (OAK_X - 30, 120, OAK_X - 60, 100, 3),
                              (OAK_X + 30, 116, OAK_X + 62, 96, 3)):
        _branch(c, x1, y1, x2 + sway, y2, w)
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
            cuts = ((0.3, "leaf_yellow"), (0.62, "leaf_orange"), (0.8, "leaf_red"), (9.0, "leaf_brown"))
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


def scarecrow(sway=0.0, surprised=False, hat_up=0.0):
    """48 x 88: a friendly scarecrow on a post, swaying a little. Faces you. surprised: wide eyes and an
    O mouth; hat_up lifts the hat off its head."""
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
    # a floppy straw hat
    hy_hat = hy - hat_up
    c.capsule(hx - 10, hy_hat - 6, hx + 10, hy_hat - 5, 1.6, 1.4, "hat")
    c.ellipse(hx, hy_hat - 9, 5.8, 4.2, "hat")
    c.capsule(hx - 5.5, hy_hat - 7, hx + 5.5, hy_hat - 7, 0.8, 0.8, "plaid_red")  # hat band
    for dx in (-8, -5, 6, 9):  # straw hair under the brim
        c.capsule(hx + dx * 0.7, hy - 4, hx + dx, hy - 1, 0.5, 0.4, "straw")
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


def den(occupants=()):
    """112 x 56: a fox den. A lumpy earth mound set with stones: a big flat rock over the doorway,
    boulders on either side, pebbles and crumbly dirt clumps, grass and a root. occupants: fox palettes
    asleep inside, shown as tail tips curled in the doorway."""
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
    # sleeping foxes: their tail tips curled in the doorway
    colours = {"orange": ("fur", "white"), "grey": ("fur", "tip")}
    for i, palette in enumerate(occupants[:2]):
        base_x = door_x - 5 + i * 9
        sub = Canvas(112, 56, palette)
        fur, tipmat = colours.get(palette, ("fur", "white"))
        sub.capsule(base_x, ground - 2, base_x + 5, ground - 6, 2.6, 2.4, fur)
        sub.capsule(base_x + 5, ground - 6, base_x + 7, ground - 9, 2.2, 1.0, tipmat)
        c.ramps = {**c.ramps, **{f"{palette}_{k}": v for k, v in sub.ramps.items()}}
        for y in range(56):
            for x in range(112):
                if sub.mat[y][x] is not None:
                    c.mat[y][x], c.lum[y][x], c.fixed[y][x] = f"{palette}_{sub.mat[y][x]}", sub.lum[y][x], None
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


PIXEL_LETTERS = {
    "H": ["101", "101", "111", "101", "101"], "O": ["111", "101", "101", "101", "111"],
    "N": ["1001", "1101", "1011", "1001", "1001"], "K": ["101", "110", "100", "110", "101"],
    "!": ["1", "1", "1", "0", "1"], "R": ["110", "101", "110", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "B": ["110", "101", "110", "101", "110"], "T": ["111", "010", "010", "010", "010"],
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


def tray_icon():
    """32 x 32 fox face for the tray."""
    import fox_art
    c = Canvas(32, 32)
    fox_art.head(c, 13, 18, tilt=0, eyes="open")
    return c.to_image()


LEAF_COLOURS = ("leaf_red", "leaf_orange", "leaf_yellow", "leaf_brown")

SPRITES = {
    "oak": ([oak(s) for s in (0, 1, 1, 0, -1, -1)], 600, True, (OAK_X, OAK_GROUND)),
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
    "straw_bit": ([straw_bit(s) for s in range(4)], 90, True, (3, 3)),
    "barrels_fall": (barrels_falling(), 90, False, (55, 62)),
    "hoe_wobble": ([hoe_tilt(a) for a in (0, 7, -6, 4, -3, 1, 0)], 80, False, (14, 58)),
    "corncob": ([corncob(r) for r in range(4)], 90, True, (7, 10)),
    "frog_sit": ([frog("sit", f) for f in (0.0, 0.5, 1.0, 0.5)], 160, True, (9, 15)),
    "frog_hop": ([frog("hop", f) for f in (0.0, 0.35, 0.7, 1.0)], 90, True, (9, 15)),
    "ribbit_bubble": ([word_bubble("RIBBIT")], 1000, False, (4, 13)),
    "scarecrow_surprised": ([scarecrow(0, True, u) for u in (2, 5, 6, 5, 3, 1, 0)], 110, False, (24, 85)),
    **{f"pumpkin_wilt_{k}_{shape}": ([pumpkin_wilt(g, shape, w) for w in (0.0, 0.3, 0.55, 0.8, 1.0)], 160, False,
                                     (20, 30))
       for k, g in PUMPKIN_SIZES.items() for shape in PUMPKIN_SHAPES},
    "hoe": ([hoe()], 1000, False, (14, 58)),
    "den": ([den()], 1000, False, (56, 54)),
    "den_orange": ([den(("orange",))], 1000, False, (56, 54)),
    "den_grey": ([den(("grey",))], 1000, False, (56, 54)),
    "den_both": ([den(("orange", "grey"))], 1000, False, (56, 54)),
    "zzz": ([zzz()], 1000, False, (5, 9)),
    "scarecrow": ([scarecrow(sw) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 260, True, (24, 85)),
}
for colour in LEAF_COLOURS:
    SPRITES[f"leaf_{colour.split('_')[1]}"] = ([leaf(colour, s) for s in range(6)], 150, True, (6, 6))
