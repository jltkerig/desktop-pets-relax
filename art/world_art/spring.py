"""Spring things: flower beds (daffodils, tulips, violets), the stone well, rain puddles (and muddy paw prints),
baby bunnies, the robin's nest in the oak, a kite, and the watering can."""
import math
import random

from pixelkit import COMMON, Canvas, rot
from .common import _daffodil_head, _px, _rock, _twig


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


# -- spring fun: puddles, bunnies, the robin's nest, a kite, the watering can --------------------------------

COMMON.update({
    "puddle": ("#4a6a8a", "#6a8eae", "#90b2cc", "#c4dcec", "#34485c"),
    "mud": ("#3a2614", "#4e3420", "#644530", "#7a5840", "#22160a"),
    "bunny": ("#6a5038", "#94704e", "#b8926a", "#d8b892", "#36261a"),
    "nest": ("#4e3618", "#74522a", "#98723e", "#bc9862", "#2a1c0a"),
    "egg_blue": ("#4e8e9c", "#76b4c4", "#a0d4e0", "#d0eef4", "#2a5660"),
    "can": ("#1e5a3c", "#2a7a50", "#3a9a68", "#6cc092", "#0e2e1e"),
})


def puddle(size=40, ripple=None, splash=0.0):
    """size x 6: a rain puddle reflecting the sky. ripple: (t) rings from raindrops landing in it. splash: water
    jumping up out of it (a fox hopping in, or a click)."""
    h = 6 + (8 if splash else 0)
    c = Canvas(size, h)
    g = h - 6
    c.ellipse(size / 2, g + 3.4, size / 2 - 1, 2.0, "puddle", bias=0.2)
    for x in range(3, size - 3, 5):  # sky glinting in it
        c.pixel(x + 1, g + 3, "puddle", 3)
    if ripple is not None:
        rng = random.Random(int(ripple * 10) + size)
        for _ in range(size // 12):
            cx, r = rng.uniform(5, size - 5), 1 + ripple * 3
            for a in range(0, 360, 40):
                c.pixel(cx + math.cos(math.radians(a)) * r, g + 3.4 + math.sin(math.radians(a)) * r * 0.35, "puddle", 3)
    if splash:
        for k in range(7):
            a = math.radians(200 + k * 23)
            d = 2 + splash * 6
            c.pixel(size / 2 + math.cos(a) * d * 1.8, g + 2 + math.sin(a) * d, "puddle", 3 if k % 2 else 2)
    return c.to_image()


def mudprint():
    """6 x 3: a muddy paw print."""
    c = Canvas(6, 3)
    for x, y in ((1, 2), (2, 2), (2, 1), (1, 0), (3, 0)):
        c.pixel(x, y, "mud", 1)
    return c.to_image(outline=False)


def bunny(pose="sit", t=0.0):
    """16 x 14: a baby bunny facing right: soft brown, long ears, a white cotton tail. pose: sit (nose
    twitching), nibble (head down at the grass), hop."""
    c = Canvas(16, 14)
    s = math.sin(t * 2 * math.pi)
    if pose == "hop":
        up = max(0.0, s) * 3
        c.ellipse(7, 9 - up, 5.2, 2.8, "bunny", angle=-10 * s)
        c.capsule(3, 10 - up, 1, 12 - up + s, 1.0, 0.8, "bunny", bias=-0.2)  # back legs kicking
        c.capsule(10, 10 - up, 12, 12.5 - up, 0.7, 0.6, "bunny")
        hx, hy = 12, 6.5 - up
    else:
        down = (2.5 + abs(s) * 0.5) if pose == "nibble" else 0.0
        c.ellipse(7, 10, 4.6, 3.4, "bunny")
        c.capsule(9, 12.5, 11, 13, 0.7, 0.6, "bunny")
        hx, hy = 11.5 + down * 0.3, 7.5 + down
    c.ellipse(2.6, 9 if pose != "hop" else 8, 1.5, 1.4, "white", bias=0.3)  # the cotton tail
    c.ellipse(hx, hy, 2.8, 2.4, "bunny")
    flop = 1 if pose == "nibble" else 0
    for k, (ex, lean) in enumerate(((-0.8, -1.4), (0.6, -0.4))):  # ears, one a little behind the other
        c.capsule(hx + ex, hy - 1.5, hx + ex + lean - flop * 2, hy - 6 + flop * 2, 0.8, 0.6, "bunny", bias=-0.2 if k == 0 else 0)
    c.pixel(hx + 0.6 - flop * 0.5, hy - 3.5 + flop, "tulip_pink", 2)
    c.pixel(hx + 1, hy - 0.6, "eye")
    nose = 0.4 if pose == "sit" and s > 0.3 else 0.0  # twitch
    c.pixel(hx + 2.6, hy + 0.4 - nose, "tulip_pink", 2)
    return c.to_image()


def nest(pose="sit", t=0.0):
    """30 x 18: a robin's nest of woven twigs in the oak, the robin sitting on it. pose: sit (looking about),
    scold (up on its toes, beak wide open), eggs (hopped up onto the rim: three blue eggs inside)."""
    c = Canvas(30, 18)
    rng = random.Random(5)
    eggs = pose == "eggs"
    if eggs:
        for k, ex in enumerate((11, 15, 19)):
            c.ellipse(ex, 10.5, 1.8, 1.5, "egg_blue", bias=0.2)
    else:  # the robin, snug in the nest
        up = 2 if pose == "scold" else 0
        c.capsule(9, 9 - up, 5, 6 - up, 1.4, 0.9, "robin_back", bias=-0.2)  # tail
        c.ellipse(14, 9 - up, 5.4, 3.6, "robin_back")
        c.ellipse(17, 10 - up, 3.4, 2.8, "robin_breast", bias=0.15)
        turn = 1 if pose == "sit" and t > 0.5 else 0
        hx, hy = 19 - turn, 5.5 - up * 1.5
        c.ellipse(hx, hy, 2.7, 2.4, "robin_back")
        c.pixel(hx + 0.4, hy - 1.2, "white", 3)
        c.pixel(hx + 0.8, hy - 0.6, "eye")
        if pose == "scold" and t < 0.6:
            c.capsule(hx + 2, hy - 0.6, hx + 4.4, hy - 2.0, 0.4, 0.3, "beak")
            c.capsule(hx + 2, hy + 0.4, hx + 4.2, hy + 1.4, 0.4, 0.3, "beak")
        else:
            c.capsule(hx + 2, hy, hx + 4.4 - turn * 2, hy + 0.3, 0.5, 0.3, "beak")
    c.ellipse(15, 13, 12, 4.2, "nest", bias=0.1, clip=lambda x, y: y >= 11)  # the bowl of the nest
    for _ in range(26):  # woven twigs poking out
        x = rng.uniform(4, 26)
        y = rng.uniform(11, 16)
        _twig(c, x, y, x + rng.uniform(-3, 3), y + rng.uniform(-1.5, 1.5), "nest", rng.choice((0, 2, 3)))
    if eggs:  # the robin up on the rim, watching over them
        c.ellipse(25, 7, 3.0, 2.4, "robin_back")
        c.ellipse(26, 8, 1.8, 1.6, "robin_breast")
        c.ellipse(27, 4.2, 2.0, 1.8, "robin_back")
        c.pixel(27.5, 3.8, "eye")
        c.capsule(28.5, 4.4, 30, 4.6, 0.4, 0.3, "beak")
        c.capsule(25, 9, 25, 11, 0.3, 0.3, "bark")
    return c.to_image()


KITE_COLOURS = ("sled_runner", "star", "sled_runner", "star")


def kite(t=0.0, flap=0.0):
    """26 x 44: a diamond kite (red and yellow, crossed sticks), its long tail with bows flapping below it.
    flap: how hard the wind is tugging (the kite twists a little)."""
    c = Canvas(26, 44)
    cx, cy = 13, 10
    twist = math.sin(t * 2 * math.pi) * flap * 1.5
    top, right, bottom, left = (cx + twist * 0.5, 1), (21 - twist, cy), (cx - twist * 0.5, 20), (5 + twist, cy)
    for k, (a, b) in enumerate(((top, right), (right, bottom), (bottom, left), (left, top))):
        c.polygon([(cx, cy), a, b], KITE_COLOURS[k], lum=0.55 if k % 2 else 0.35)
    _twig(c, top[0], top[1], bottom[0], bottom[1], "post", 1)
    _twig(c, left[0], left[1], right[0], right[1], "post", 1)
    prev = bottom
    for k in range(1, 9):  # the tail: a string waving below, with little bows
        y = 20 + k * 3
        x = cx + math.sin(t * 2 * math.pi + k * 0.8) * (1 + k * 0.45)
        _twig(c, prev[0], prev[1], x, y, "twine", 1)
        if k % 3 == 0:
            c.ellipse(x - 1.4, y, 1.3, 0.8, KITE_COLOURS[k % 4], bias=0.2)
            c.ellipse(x + 1.4, y, 1.3, 0.8, KITE_COLOURS[k % 4], bias=0.2)
        prev = (x, y)
    return c.to_image()


def kite_ground():
    """34 x 8: the kite lying on the grass, its tail trailing out along the ground."""
    c = Canvas(34, 8)
    pts = [(10, 1), (19, 5), (10, 7), (1, 5)]
    for k in range(4):
        c.polygon([(10, 5), pts[k], pts[(k + 1) % 4]], KITE_COLOURS[k], lum=0.55 if k % 2 else 0.35)
    _twig(c, 10, 1, 10, 7, "post", 1)
    _twig(c, 1, 5, 19, 5, "post", 1)
    for x in range(19, 33):
        c.pixel(x, 6 + (x // 3) % 2, "twine", 1)
    for bx in (24, 30):
        c.ellipse(bx, 6, 1.2, 0.8, "sled_runner", bias=0.2)
    return c.to_image()


def watering_can(tilt=0.0, t=0.0):
    """34 x 32: a green tin watering can, a long spout with a sprinkler rose. tilt: tipped forward, pouring,
    with drops falling from the rose (t moves them down)."""
    c = Canvas(34, 32)
    lift = 5 if tilt else 14  # (tipped up, the rose comes down: room below it for the drops)
    P = lambda x, y: rot(x, y + lift, 15, 30, tilt)  # drawn upright, then tipped round the bottom of the can
    c.capsule(*P(14, 13), *P(23, 6), 0.9, 0.8, "can")  # the spout
    rx, ry = P(23.5, 5.5)
    c.ellipse(rx, ry, 1.6, 1.2, "can", angle=-40 + tilt, bias=0.3)  # its rose
    c.polygon([P(4, 16), P(15, 16), P(15, 7), P(4, 7)], "can", lum=0.45)
    c.capsule(*P(4, 9), *P(1, 11), 0.8, 0.8, "can", bias=-0.1)  # the handle at the back
    c.capsule(*P(1, 11), *P(4, 14), 0.8, 0.8, "can", bias=-0.1)
    c.capsule(*P(5, 7), *P(14, 7), 0.6, 0.6, "hoop")  # the rim
    if tilt:
        for k in range(6):  # drops falling from the rose
            d = (t * 6 + k * 2.5) % 9
            c.pixel(rx - 1 + k % 3, min(31, ry + 2 + d), "water", 3 if k % 2 else 2)
    return c.to_image()

def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        "well": ([well()], 1000, False, (23, 62)),
        "well_bucket": ([well(b) for b in (0.0, 0.25, 0.5, 0.75, 1.0)] + [well(1.0, s) for s in (0.3, 0.7, 1.0)] +
                        [well(b) for b in (0.9, 0.7, 0.45, 0.2, 0.0)], 110, False, (23, 62)),
        **{kind: ([flower_bed(kind, sw) for sw in (0, 1, 0, -1)], 520, True, (22, 22), {"perches": heads})
           for kind, heads in FLOWER_BEDS.items()},
        **{f"{kind}_bob": ([flower_bed(kind, sw) for sw in (2, -2, 1.5, -1.2, 0.6, 0)], 90, False, (22, 22),
                           {"perches": heads})
           for kind, heads in FLOWER_BEDS.items()},
        "puddle": ([puddle(40)], 1000, False, (20, 5)),
        "puddle_s": ([puddle(26)], 1000, False, (13, 5)),
        "puddle_rain": ([puddle(40, r / 4) for r in range(4)], 140, True, (20, 5)),
        "puddle_s_rain": ([puddle(26, r / 4) for r in range(4)], 140, True, (13, 5)),
        "puddle_splash": ([puddle(40, None, sp) for sp in (0.3, 0.7, 1.0, 0.6)] + [puddle(40)] * 0, 90, False, (20, 13)),
        "puddle_s_splash": ([puddle(26, None, sp) for sp in (0.3, 0.7, 1.0, 0.6)], 90, False, (13, 13)),
        "mudprint": ([mudprint()], 1000, False, (3, 2)),
        "bunny_sit": ([bunny("sit", t) for t in (0, 0.25, 0.5, 0.75)], 200, True, (8, 13)),
        "bunny_nibble": ([bunny("nibble", t) for t in (0, 0.25, 0.5, 0.75)], 150, True, (8, 13)),
        "bunny_hop": ([bunny("hop", t) for t in (0, 0.25, 0.5, 0.75)], 80, True, (8, 13)),
        "nest": ([nest("sit", t) for t in (0, 0.25, 0.5, 0.75)], 700, True, (15, 17)),
        "nest_scold": ([nest("scold", t) for t in (0, 0.3, 0.7)], 120, True, (15, 17)),
        "nest_eggs": ([nest("eggs")], 2500, False, (15, 17)),
        "kite": ([kite(t, 0.4) for t in (0, 0.25, 0.5, 0.75)], 150, True, (13, 10)),
        "kite_gusty": ([kite(t, 1.0) for t in (0, 0.25, 0.5, 0.75)], 70, True, (13, 10)),
        "kite_ground": ([kite_ground()], 1000, False, (17, 7)),
        "watering_can": ([watering_can()], 1000, False, (10, 30)),
        "watering_can_pour": ([watering_can(40, t / 4) for t in range(4)], 90, True, (10, 30)),
    }
