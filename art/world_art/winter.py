"""Winter things: the sled, the tree stump, the little Christmas tree, the woodstack, the snowman (and his
carrot), snowballs, the frozen pond, the bird feeder, and gift boxes."""
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


# -- winter fun: a snowman, snowballs, a frozen pond, a bird feeder, gift boxes ------------------------------

COMMON.update({
    "coal": ("#141418", "#24242a", "#34343c", "#4a4a54", "#08080a"),
    "carrot": ("#a8400c", "#d8661a", "#f0882e", "#f8b062", "#5a1e04"),
    "ice": ("#6e9cbc", "#9cc4de", "#c4e0f2", "#eef8ff", "#3a6484"),
    "seed": ("#6a4a22", "#94703a", "#b89052", "#d8b47a", "#36240e"),
    "gift_red": ("#7a1018", "#b01c26", "#d8343c", "#f06a6a", "#3e060a"),
    "gift_green": ("#14502a", "#1e7038", "#2e904c", "#5ab474", "#082814"),
    "gift_blue": ("#1e3a7a", "#2e56aa", "#4878d0", "#7ea4ec", "#0e1c3e"),
})
SNOWMAN_NOSE = (21, 12)  # the tip of his carrot nose (frame x, y): a carrot dropped near here goes back on


def snowman(nose=True, melt=0.0, tilt=0.0):
    """30 x 46: a snowman: three snowballs, coal eyes, smile and buttons, twig arms, a red scarf and a carrot
    nose. melt: slumping a little on a day without snow (a puddle round his base). tilt rocks him (clicked)."""
    c = Canvas(30, 46)
    lean = lambda y: tilt * (45 - y) / 45  # rocking: the top moves most
    sink = melt * 3
    c.ellipse(15 + lean(37), 37 + sink * 0.3, 9 + melt * 2, 8 - melt * 1.5, "snow", bias=0.15)
    c.ellipse(15 + lean(23), 23 + sink, 7, 6, "snow", bias=0.2)
    hx, hy = 15 + lean(11) + melt, 11 + sink * 1.3
    c.ellipse(hx, hy, 5, 5, "snow", bias=0.25)
    for side, (x2, y2) in ((-1, (2, 14)), (1, (28, 15))):  # twig arms, with little twig fingers
        x1 = 15 + side * 6 + lean(22)
        _twig(c, x1, 21 + sink, x2 + lean(15), y2 + sink, "bark", 1)
        _twig(c, x2 + lean(15), y2 + sink, x2 + lean(15) - side, y2 - 3 + sink, "bark", 1)
    c.capsule(hx - 5, hy + 5, hx + 5, hy + 5, 1.3, 1.3, "sled_runner", bias=0.1)  # the scarf
    c.capsule(hx + 3, hy + 6, hx + 4, hy + 11, 1.0, 0.9, "sled_runner", bias=-0.1)
    for ex in (-2, 2):
        c.pixel(hx + ex, hy - 1, "coal", 1)
    for k, mx in enumerate((-2, -1, 0, 1, 2)):  # a coal smile
        c.pixel(hx + mx, hy + 2 + (0 if abs(mx) == 2 else 1), "coal", 1)
    for by in (20, 24):
        c.pixel(15 + lean(by), by + sink, "coal", 2)
    if nose:
        c.capsule(hx + 1, hy + 0.5, hx + 6, hy + 1.2, 1.0, 0.3, "carrot")
    if melt:
        for x in range(1, 29):
            c.pixel(x, 45, "water", 2 if x % 4 else 3)
    return c.to_image()


def carrot():
    """9 x 4: the snowman's carrot nose, lying on the ground (or in a fox's mouth)."""
    c = Canvas(9, 4)
    c.capsule(1.5, 2, 7.5, 2, 1.2, 0.3, "carrot")
    c.pixel(0, 1, "stalk", 2)
    c.pixel(0, 3, "stalk", 1)
    return c.to_image()


def snowball():
    """8 x 8: a snowball."""
    c = Canvas(8, 8)
    c.ellipse(4, 4, 3.3, 3.1, "snow", bias=0.2)
    return c.to_image()


SNOWBALL_PILE = [(5, 11), (12, 11), (19, 11), (8.5, 6), (15.5, 6), (12, 1.5)]


def snowball_pile():
    """26 x 16: a little pyramid of snowballs, ready to throw."""
    c = Canvas(26, 16)
    for x, y in SNOWBALL_PILE:
        c.ellipse(x + 1, y + 3, 3.4, 3.2, "snow", bias=0.2)
    for x in range(1, 25):
        c.pixel(x, 15, "snow", 1)
    return c.to_image()


def pond(t=0.0, glint=0.0):
    """96 x 12: a frozen pond: a flat oval of pale blue ice with snow round its edge and light gleaming across
    it. glint: a sparkle sweeping over the ice (when clicked)."""
    c = Canvas(96, 12)
    c.ellipse(48, 7, 46, 4.0, "ice", bias=0.25)
    for x in range(3, 93):  # streaks of light on the ice, drifting
        k = (x + int(t * 12)) % 23
        if k in (0, 1) and 4 < x < 90:
            c.pixel(x, 6 + (x % 3 == 0), "ice", 3)
    for x in range(2, 94):  # snow banked round the rim
        dx = (x - 48) / 46
        top = 7 - 4.0 * math.sqrt(max(0.0, 1 - dx * dx))
        if x % 3:
            c.pixel(x, top, "snow", 3)
        c.pixel(x, 7 + 4.0 * math.sqrt(max(0.0, 1 - dx * dx)), "snow", 2)
    if glint:
        gx = 6 + glint * 84
        for d in range(-3, 4):
            c.pixel(gx + d, 7 - d * 0.6, "ice", 3)
        for a in range(0, 360, 90):
            c.pixel(gx + math.cos(math.radians(a)) * 3, 5 + math.sin(math.radians(a)) * 2, "snow", 3)
    return c.to_image()


FEEDER_PERCHES = [(-8, 30), (8, 30)]  # the ends of the seed tray (sideways, up), for birds to sit on


def feeder(snow=False, tilt=0.0):
    """30 x 52: a wooden bird feeder on a post: a little house full of seed with a red roof, and a tray along
    the bottom for the birds to stand on. tilt: swinging (clicked)."""
    c = Canvas(30, 52)
    sx = lambda y: tilt * (24 - y) / 12 if y < 24 else 0
    c.capsule(15, 51, 15, 23, 1.3, 1.1, "post")
    c.capsule(5 + sx(22), 22, 25 + sx(22), 22, 1.0, 1.0, "sled_wood", bias=0.1)  # the tray
    c.polygon([(8 + sx(20), 21), (22 + sx(20), 21), (22 + sx(12), 12), (8 + sx(12), 12)], "sled_wood", lum=0.4)
    c.ellipse(15 + sx(17), 17, 4.2, 2.6, "seed", bias=0.1)  # seed behind the window
    for x in range(10, 21, 2):
        c.pixel(x + sx(21), 21, "seed", 2)  # seed spilling onto the tray
    c.polygon([(5 + sx(13), 13), (25 + sx(13), 13), (15 + sx(4), 4)], "sled_runner", lum=0.5)  # the roof
    if snow:
        for x in range(6, 25):
            c.pixel(x + sx(12), 12 - (10 - abs(x - 15)) * 0.85, "snow", 3)
        c.ellipse(15, 51, 6, 1.0, "snow", bias=0.3)
    return c.to_image()


def gifts(palette=None, t=0.0, wobble=0.0):
    """44 x 26: presents under the tree: a big red box with a gold ribbon and bow, a green one with a red
    ribbon, and a little blue one on top. palette: a fox hiding in the big box (its lid pushed up, ears and
    eyes peeking out, its tail sticking out of the side); t wiggles it."""
    c = Canvas(44, 26, palette=palette or "orange")
    w = wobble * math.sin(t * 2 * math.pi)
    c.polygon([(23, 25), (37, 25), (37, 14), (23, 14)], "gift_green", lum=0.4)  # the green box
    c.capsule(30, 14, 30, 25, 0.8, 0.8, "gift_red")
    c.polygon([(26 + w, 14), (36 + w, 14), (36 + w, 7), (26 + w, 7)], "gift_blue", lum=0.5)  # the little one
    c.capsule(31 + w, 7, 31 + w, 14, 0.6, 0.6, "star")
    if palette:  # its tail sticking out of the side, swishing
        swish = math.sin(t * 2 * math.pi) * 2
        c.chain([(20, 21), (25, 20 - swish), (29, 18 - swish * 1.5), (31, 17 - swish * 1.8)], [1.8, 2.2, 1.9, 1.1],
                ["fur", "fur", "tip"])
    c.polygon([(3, 25), (21, 25), (21, 12), (3, 12)], "gift_red", lum=0.45)  # the big box
    c.capsule(12, 12, 12, 25, 0.9, 0.9, "star")
    c.capsule(3, 18, 21, 18, 0.7, 0.7, "star", bias=-0.1)
    lift = (5.5 + math.sin(t * 2 * math.pi) * 1.0) if palette else 0
    if palette:  # its face peeking out from under the lid it has pushed up
        c.ellipse(12, 11.5, 5.0, 3.2, "fur", clip=lambda x, y: y < 12)
        c.ellipse(12, 11.8, 2.2, 1.3, "white", clip=lambda x, y: y < 12)
        for side in (-1, 1):
            c.pixel(12 + side * 2.2, 9.5 - (1 if t > 0.6 else 0) * 0, "eye")
        c.pixel(12, 11, "nose", 1)
    ly = 12 - lift
    c.polygon([(2 + w, ly + 1), (22 + w, ly + 1), (22 + w, ly - 2), (2 + w, ly - 2)], "gift_red", lum=0.6)  # its lid
    c.capsule(12 + w, ly - 2, 12 + w, ly + 1, 0.9, 0.9, "star")
    for side in (-1, 1):  # the bow
        c.ellipse(12 + w + side * 2.4, ly - 3.6, 2.2, 1.4, "star", angle=side * 25, bias=0.2)
    c.pixel(12 + w, ly - 3, "star", 1)
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
        "snowman": ([snowman()], 1000, False, (15, 45)),
        "snowman_nonose": ([snowman(nose=False)], 1000, False, (15, 45)),
        "snowman_melty": ([snowman(melt=1.0)], 1000, False, (15, 45)),
        "snowman_melty_nonose": ([snowman(nose=False, melt=1.0)], 1000, False, (15, 45)),
        **{f"snowman{look}_wobble": ([snowman(nose, melt, tilt=a) for a in (0, 2, -1.5, 1, -0.5, 0)], 80, False, (15, 45))
           for look, nose, melt in (("", True, 0.0), ("_nonose", False, 0.0), ("_melty", True, 1.0),
                                    ("_melty_nonose", False, 1.0))},
        "carrot": ([carrot()], 1000, False, (4, 3)),
        "snowball": ([snowball()], 1000, False, (4, 7)),
        "snowballs": ([snowball_pile()], 1000, False, (13, 15)),
        "pond": ([pond(t) for t in (0, 0.33, 0.66, 1.0)], 500, True, (48, 10)),
        "pond_glint": ([pond(0, g / 6) for g in range(7)], 70, False, (48, 10)),
        "feeder": ([feeder()], 1000, False, (15, 51)),
        "feeder_snow": ([feeder(snow=True)], 1000, False, (15, 51)),
        "feeder_wobble": ([feeder(tilt=a) for a in (0, 2, -1.5, 1, -0.5, 0)], 90, False, (15, 51)),
        "feeder_snow_wobble": ([feeder(True, a) for a in (0, 2, -1.5, 1, -0.5, 0)], 90, False, (15, 51)),
        "gifts": ([gifts()], 1000, False, (22, 25)),
        "gifts_wobble": ([gifts(None, t, 1.5) for t in (0, 0.25, 0.5, 0.75, 1.0)], 80, False, (22, 25)),
        **{f"gifts_{p}": ([gifts(p, t) for t in (0, 0.25, 0.5, 0.75)], 160, True, (22, 25)) for p in ("orange", "grey")},
    }
