"""Autumn things: pumpkins (growing, giant, bursting, jack-o'-lanterns), the scarecrow and his hat, the corn
field and cobs, the hoe, the apple barrel."""
import math
import random

from pixelkit import COMMON, Canvas
from .common import _barrel


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


def hoe():
    """24 x 60: a garden hoe stuck in the ground, leaning a little."""
    c = Canvas(24, 60)
    c.capsule(14, 58, 9, 6, 1.1, 1.0, "handle")
    c.capsule(9, 6, 9, 4, 1.4, 1.4, "handle")
    c.polygon([(8, 4), (16, 3), (17, 9), (13, 8)], "iron", lum=0.55)   # the blade
    c.capsule(9, 5, 13, 4.5, 0.8, 0.8, "iron", bias=-0.3)              # its neck
    c.ellipse(14, 58.5, 3.5, 1.2, "dirt")
    return c.to_image()


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


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        **{f"pumpkin_{s}_{k}_{shape}": ([pumpkin(s, sw, g, shape) for sw in (0, 1, 0, -1)], 700, True, (20, 30))
           for s in range(5) for k, g in PUMPKIN_SIZES.items() for shape in PUMPKIN_SHAPES},
        **{f"pumpkin_4_{k}_{shape}_jack": ([pumpkin(4, sw, g, shape, jack=True) for sw in (0, 1, 0, -1)], 260, True,
                                           (20, 30))
           for k, g in PUMPKIN_SIZES.items() for shape in PUMPKIN_SHAPES},
        **{f"corn_{s}": ([corn(s, sw) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 300, True, (60, 98)) for s in range(5)},
        "hoe_wobble": ([hoe_tilt(a) for a in (0, 7, -6, 4, -3, 1, 0)], 80, False, (14, 58)),
        "corncob": ([corncob(r) for r in range(4)], 90, True, (7, 10)),
        "apple": ([apple(k) for k in range(4)], 110, True, (4, 7)),
        "apple_barrel": ([apple_barrel()], 1000, False, (15, 33)),
        "apple_barrel_wobble": ([apple_barrel(f) for f in (1.0, 0.9, 1.0, 0.95, 1.0)], 80, False, (15, 33)),
        "scarecrow_nohat": ([scarecrow(sw, hat=False) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 260, True, (24, 85)),
        "scarecrow_surprised_nohat": ([scarecrow(0, True, hat=False) for _ in range(7)], 110, False, (24, 85)),
        "scarecrow_hat": ([scarecrow_hat()], 1000, False, (12, 11)),
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
        "scarecrow": ([scarecrow(sw) for sw in (0, 1, 2, 1, 0, -1, -2, -1)], 260, True, (24, 85)),
    }
