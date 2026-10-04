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

def oak(sway=0.0, seed=7):
    """160 x 200. sway shifts the crown a pixel or two (it breathes in the wind)."""
    c = Canvas(160, 200)
    rng = random.Random(seed)
    # roots and trunk
    c.capsule(80, 196, 80, 120, 11, 7, "bark")
    for dx in (-14, 13):
        c.capsule(80, 192, 80 + dx, 198, 5, 2.5, "bark")
    for x1, y1, x2, y2, r in ((79, 140, 50, 100, 4.0), (81, 132, 112, 96, 4.0), (80, 120, 74, 78, 4.5),
                              (60, 112, 40, 92, 2.5), (104, 104, 124, 88, 2.5)):
        c.capsule(x1, y1, x2 + sway, y2, r, r * 0.6, "bark")
    # bark texture: long vertical furrows, broken in a few places
    for x, y1, y2 in ((75, 126, 160), (75, 166, 190), (79, 122, 148), (79, 154, 186), (83, 130, 172), (86, 140, 188),
                      (72, 150, 184)):
        for y in range(y1, y2):
            if 0 <= x < 160 and c.mat[y][x] == "bark":
                c.fixed[y][x] = 0
    # the crown: one leafy mass with a bumpy oak outline, lit as a single rounded shape
    cx0, cy0, rx0, ry0 = 80 + sway, 70, 62, 44
    lumps = [(cx0, cy0, rx0, ry0)]
    for i in range(14):  # bumps around the edge give the oak its lobed silhouette
        a = i / 14 * 2 * math.pi + rng.uniform(-0.15, 0.15)
        lumps.append((cx0 + math.cos(a) * rx0 * 0.86, cy0 + math.sin(a) * ry0 * 0.86 - (4 if math.sin(a) < 0 else 0),
                      rng.uniform(13, 18), rng.uniform(11, 15)))
    def in_crown(x, y):
        return any(((x - lx) / lrx) ** 2 + ((y - ly) / lry) ** 2 <= 1 for lx, ly, lrx, lry in lumps)
    # leaf colours come in small clusters, warmer toward the bottom, more yellow on top
    cell = {}
    def colour(x, y):
        key = ((x + (y // 3) % 2) // 4, y // 3)
        if key not in cell:
            # smooth patches of colour (overlapping waves) with a little randomness on top
            kx, ky = key[0] * 4, key[1] * 3
            wave = (math.sin(kx * 0.09 + 1.3) + math.sin(ky * 0.13 + 0.4) + math.sin((kx + ky) * 0.05 + 2.1)) / 6 + 0.5
            r = min(0.999, max(0.0, wave * 0.8 + rng.random() * 0.2))
            top = (y - (cy0 - ry0)) / (2 * ry0)  # 0 at the top, 1 at the bottom
            if r < 0.06:
                cell[key] = ("leaf_green", rng.uniform(-0.2, 0.05))
            elif r < 0.06 + 0.32 * (1 - top):
                cell[key] = ("leaf_yellow", rng.uniform(-0.1, 0.15))
            elif r < 0.75:
                cell[key] = ("leaf_orange", rng.uniform(-0.1, 0.15))
            elif r < 0.93:
                cell[key] = ("leaf_red", rng.uniform(-0.1, 0.15))
            else:
                cell[key] = ("leaf_brown", rng.uniform(-0.15, 0.05))
        return cell[key]
    for y in range(0, 130):
        for x in range(0, 160):
            if not in_crown(x + 0.5, y + 0.5):
                continue
            nx, ny = (x + 0.5 - cx0) / (rx0 + 16), (y + 0.5 - cy0) / (ry0 + 14)
            mat, jitter = colour(x, y)
            lum = Canvas._shade(max(-1, min(1, nx)), max(-1, min(1, ny)), jitter)
            if rng.random() < 0.05:  # little gaps of shadow between the leaves
                lum -= 0.35
            c.mat[y][x], c.lum[y][x], c.fixed[y][x] = mat, lum, None
    return c.to_image()


# -- small things --------------------------------------------------------------------------------------

def leaf(mat, spin):
    """8 x 8 leaf; spin 0..3 turns it as it falls."""
    c = Canvas(8, 8)
    angle = spin * 45
    c.ellipse(4, 4, 3.2, 1.8 + (0.8 if spin % 2 else 0), mat, angle=angle)
    x2 = 4 + 2.6 * math.cos(math.radians(angle))
    y2 = 4 + 2.6 * math.sin(math.radians(angle))
    c.capsule(4, 4, x2, y2, 0.4, 0.3, mat, bias=-0.7)  # the stem/vein
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


def _pumpkin_body(c, cx, base, size, mat):
    """A ribbed pumpkin sitting on the ground: side ribs first (darker), the front rib last."""
    w, h = 9.0 * size, 6.4 * size
    cy = base - h
    for dx, rx, bias in ((-0.55, 0.5, -0.25), (0.55, 0.5, -0.25), (-0.28, 0.55, -0.08), (0.28, 0.55, -0.08),
                         (0.0, 0.5, 0.08)):
        c.ellipse(cx + dx * w, cy, rx * w, h, mat, bias=bias)
    return cy - h


def pumpkin(stage, sway=0.0):
    """40 x 32. Stages: 0 sprout, 1 vine with a flower, 2 small green, 3 yellow-orange, 4 big ripe."""
    c = Canvas(40, 32)
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
    top = _pumpkin_body(c, 20, ground + 0.5, size, mat)
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


def tray_icon():
    """32 x 32 fox face for the tray."""
    import fox_art
    c = Canvas(32, 32)
    fox_art.head(c, 13, 18, tilt=0, eyes="open")
    return c.to_image()


LEAF_COLOURS = ("leaf_red", "leaf_orange", "leaf_yellow", "leaf_brown")

SPRITES = {
    "oak": ([oak(s) for s in (0, 1, 1, 0, -1, -1)], 600, True, (80, 197)),
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
    **{f"pumpkin_{s}": ([pumpkin(s, sw) for sw in (0, 1, 0, -1)], 700, True, (20, 30)) for s in range(5)},
}
for colour in LEAF_COLOURS:
    SPRITES[f"leaf_{colour.split('_')[1]}"] = ([leaf(colour, s) for s in range(4)], 160, True, (4, 4))
