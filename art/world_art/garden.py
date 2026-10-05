"""The vegetable garden: tomatoes, radishes, lettuce and watermelons."""
import math
import random

from pixelkit import COMMON, Canvas
from .common import _twig
from .autumn import PUMPKIN_SIZES


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


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        **{f"tomatoes_{s}": ([tomatoes(s, sw) for sw in (0, 1, 0, -1)], 500, True, (36, 42)) for s in range(5)},
        **{f"radishes_{s}": ([radishes(s, sw) for sw in (0, 1, 0, -1)], 520, True, (29, 15)) for s in range(5)},
        **{f"lettuce_{s}": ([lettuce(s, sw) for sw in (0, 1, 0, -1)], 560, True, (29, 15)) for s in range(5)},
        "tomato": ([tomato(k) for k in range(4)], 110, True, (4, 7)),
        "radish": ([radish(k) for k in range(4)], 110, True, (5, 8)),
        "lettuce_head": ([lettuce_head(k) for k in range(4)], 140, True, (5, 9)),
        **{f"melon_{s}_{k}_{shape}": ([melon(s, sw, g, shape) for sw in (0, 1, 0, -1)], 700, True, (20, 30))
           for s in range(5) for k, g in PUMPKIN_SIZES.items() for shape in MELON_SHAPES},
        **{f"melon_split_{k}_{shape}": ([melon_split(g, shape, t) for t in (0.1, 0.25, 0.4, 0.6, 0.75, 0.9, 1.0)], 140,
                                        False, (20, 30))
           for k, g in PUMPKIN_SIZES.items() for shape in MELON_SHAPES},
    }
