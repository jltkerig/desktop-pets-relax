"""Spring things: flower beds (daffodils, tulips, violets) and the stone well."""
import math
import random

from pixelkit import COMMON, Canvas
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
    }
