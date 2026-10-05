"""Winter things: the sled, the tree stump, the little Christmas tree, the woodstack."""
import math
import random

from pixelkit import COMMON, Canvas, bezier
from .common import _px, _twig


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


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        "woodstack": ([woodstack()], 1000, False, (30, 35)),
        "woodstack_snow": ([woodstack(snow=True)], 1000, False, (30, 35)),
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
    }
