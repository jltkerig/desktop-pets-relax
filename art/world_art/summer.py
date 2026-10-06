"""Summer things: the slide, the kiddie pool, dahlias, dandelions, cattails, the sprinkler, the beach ball, the
hammock, the firefly jar and the sunflowers."""
import math
import random

from pixelkit import COMMON, Canvas, bezier
from .common import _px, _twig
from .sky import glow


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


# -- summer fun: a sprinkler, a beach ball, a hammock, a firefly jar, sunflowers ------------------------------

COMMON.update({
    "sprinkler": ("#9a7a0c", "#c8a01c", "#e8c436", "#f8e47a", "#4e3c04"),
    "ball_red": ("#8a1418", "#c02028", "#e43c40", "#f47472", "#46080a"),
    "ball_blue": ("#1a4a9a", "#2a68c8", "#4a8ce8", "#86b6f6", "#0c244e"),
    "ball_yellow": ("#b8900c", "#e8bc1c", "#f8d83c", "#fcf090", "#5e4606"),
    "hammock_a": ("#8a2a1a", "#b8402a", "#d86040", "#ee9070", "#46140a"),
    "hammock_b": ("#a8946a", "#d0bc90", "#e8d8b4", "#f8f0dc", "#54482e"),
    "glass": ("#7a9aa8", "#a8c4d0", "#cce0e8", "#f0fafc", "#4a6470"),
    "sunflower": ("#b07a0a", "#e0a418", "#f4c430", "#fce27a", "#5a3c04"),
    "sunflower_disc": ("#2e1a0a", "#4a2c12", "#6a4220", "#865a32", "#160c04"),
})


def sprinkler(sweep=None):
    """100 x 44: a garden sprinkler: a yellow bar on a little sled base, throwing a fan of water up in an arch.
    sweep: -1 .. 1, which way the fan leans as it swings from side to side (None: turned off)."""
    c = Canvas(100, 44)
    c.capsule(42, 42, 58, 42, 1.0, 1.0, "grey")                    # the base
    c.capsule(44, 39, 56, 39, 1.2, 1.2, "sprinkler", bias=0.1)     # the bar with its holes
    for x in range(45, 56, 2):
        c.pixel(x, 38, "sprinkler", 0)
    c.capsule(50, 42, 50, 40, 0.8, 0.8, "grey")
    img = c.to_image()
    c = Canvas(100, 44)  # the water on a layer of its own, without outlines, so the drops look light
    if sweep is not None:
        for k in range(-3, 4):  # streams of drops arcing up and over
            vx = sweep * 34 + k * 6
            for i in range(1, 21):
                t = i / 20
                x, y = 50 + vx * t, 37 - 70 * t + 72 * t * t
                if (i + k) % 2 == 0 and 0 <= x < 100 and y < 43:
                    c.pixel(x, y, "water", 3 if i % 4 else 2)
    img.alpha_composite(c.to_image(outline=False))
    return img


BALL_COLOURS = ("ball_red", "white", "ball_blue", "ball_yellow", "white", "ball_red")


def beach_ball(spin=0.0):
    """13 x 13: a beach ball: bright red, white, blue and yellow panels round a white cap. spin turns it."""
    c = Canvas(13, 13)
    c.ellipse(6.5, 6.5, 5.6, 5.6, "white", bias=0.15)
    for y in range(13):
        for x in range(13):
            if c.mat[y][x] is not None:
                a = (math.atan2(y + 0.5 - 6.5, x + 0.5 - 6.5) / (2 * math.pi) + spin) % 1
                c.mat[y][x] = BALL_COLOURS[int(a * 6) % 6]
    c.ellipse(5.8, 5.8, 1.4, 1.4, "white", bias=0.4)  # the cap where the panels meet
    return c.to_image()


HAMMOCK_SAG = 31  # the fabric's lowest point (frame y), where a fox lies


def _hammock_curve(x, sway):
    mid = 42 + sway
    return 16 + (1 - ((x - mid) / 30) ** 2) * (HAMMOCK_SAG - 16)


def hammock(sway=0.0):
    """84 x 40: a striped hammock slung between two wooden posts. sway: swinging a little side to side. This is
    the back of it: hammock_front is the near edge, drawn in front of a fox lying in it."""
    c = Canvas(84, 40)
    for x1, x2 in ((5, 9), (79, 75)):  # the posts, leaning in a little
        c.capsule(x1, 39, x2, 6, 1.4, 1.2, "post")
    for x in range(12, 73):  # the far half of the fabric: stripes, in shadow
        top = _hammock_curve(x, sway) - 6
        for y in range(int(top), int(_hammock_curve(x, sway)) + 1):
            mat = "hammock_a" if (x // 4) % 2 else "hammock_b"
            _px(c, x, y, mat, 0 if y < top + 2 else 1)
    for side, (px_, x) in ((-1, (9, 12)), (1, (75, 72))):  # ropes from the posts to the ends
        _twig(c, px_, 8, x + sway * 0.3, _hammock_curve(x, sway) - 6, "twine", 2)
        _twig(c, px_, 8, x + sway * 0.3, _hammock_curve(x, sway), "twine", 1)
    return c.to_image()


def hammock_front(sway=0.0):
    """84 x 40: the near edge of the hammock (see hammock)."""
    c = Canvas(84, 40)
    for x in range(12, 73):
        bottom = _hammock_curve(x, sway) + 1
        for y in range(int(bottom) - 3, int(bottom) + 1):
            mat = "hammock_a" if (x // 4) % 2 else "hammock_b"
            _px(c, x, y, mat, 3 if y == int(bottom) - 3 else 2 if y < bottom - 1 else 1)
    return c.to_image()


def firefly_jar(count=0, t=0.0):
    """14 x 18: a glass jar with a punched tin lid; count fireflies inside (0 .. 4), blinking."""
    c = Canvas(14, 18)
    for y in range(4, 17):  # the glass: just its edges and a shine, so you see inside
        _px(c, 2, y, "glass", 1)
        _px(c, 11, y, "glass", 0)
    for x in range(2, 12):
        _px(c, x, 17, "glass", 1)
        _px(c, x, 4, "glass", 2)
    for y in range(6, 14):
        _px(c, 4, y, "glass", 3 if y % 3 else 2)
    c.capsule(2, 2.5, 11, 2.5, 1.2, 1.2, "hoop", bias=0.1)  # the lid
    for x in (4, 7, 10):
        c.pixel(x, 2, "hoop", 0)
    rng = random.Random(count)
    for k in range(count):
        x, y = rng.randint(5, 9), rng.randint(7, 15)
        lit = (k + int(t * 4)) % 3 != 0
        _px(c, x, y, "firefly", 3 if lit else 0)
        if lit:
            _px(c, x + 1, y, "firefly", 2)
    return c.to_image(outline=False)


SUNFLOWERS = [(10, 50), (22, 58), (34, 44)]  # x, height of each flower


def sunflower_heads(look):
    """Where each flower's head is (frame x, y) for a look (0 .. 4 facing left to right, or 'night')."""
    turn = 0 if look == "night" else (look - 2) / 2
    return [(x + turn * 2, 63 - h + (5 if look == "night" else 0)) for x, h in SUNFLOWERS]


def sunflowers(look=2, sway=0.0):
    """44 x 64: three tall sunflowers, their big heads turned toward the sun. look: 0 .. 4, facing far left ..
    straight out .. far right; 'night': heads hanging down, asleep."""
    c = Canvas(44, 64)
    ground = 63
    night = look == "night"
    turn = 0 if night else (look - 2) / 2
    for k, ((x, h), (hx, hy)) in enumerate(zip(SUNFLOWERS, sunflower_heads(look))):
        lean = sway * (h / 60)
        hx += lean
        _twig(c, x, ground, hx - turn, hy + 3, "stalk", 1)
        _twig(c, x + 1, ground, hx - turn + 1, hy + 3, "stalk", 2)
        for j, ly in enumerate(range(ground - 10, hy + 8, -11)):  # big leaves up the stalk
            side = 1 if (j + k) % 2 else -1
            c.ellipse(x + side * 3.5 + lean * (ground - ly) / h, ly, 3.0, 1.6, "dahlia_leaf", angle=side * 25)
        if night:  # hanging its head, the back of it toward you
            c.ellipse(hx + 1, hy + 1, 3.2, 4.2, "sunflower", bias=-0.1)
            for a in range(0, 360, 45):
                c.pixel(hx + 1 + math.cos(math.radians(a)) * 3.6, hy + 1 + math.sin(math.radians(a)) * 4.6, "sunflower", 1)
            c.ellipse(hx + 1, hy + 1, 1.6, 2.4, "dahlia_leaf")
            continue
        rx = 5.2 * (1 - 0.4 * abs(turn))  # turned away, the round face looks narrower
        for a in range(0, 360, 30):  # the petals, round the edge
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            c.ellipse(hx + ca * rx, hy + sa * 5.2, 1.6, 1.6, "sunflower", bias=0.1)
        c.ellipse(hx + turn * 1.2, hy, rx * 0.62, 3.2, "sunflower_disc", bias=0.1)
        for a in range(0, 360, 72):  # seeds glinting in the disc
            c.pixel(hx + turn * 1.2 + math.cos(math.radians(a)) * rx * 0.3, hy + math.sin(math.radians(a)) * 1.5,
                    "sunflower_disc", 3)
    return c.to_image()


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
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
        "sprinkler": ([sprinkler(a) for a in (-1, -0.66, -0.33, 0, 0.33, 0.66, 1, 0.66, 0.33, 0, -0.33, -0.66)], 140,
                      True, (50, 43)),
        "sprinkler_off": ([sprinkler()], 1000, False, (50, 43)),
        "beachball": ([beach_ball(k / 6) for k in range(6)], 80, True, (6, 12)),
        "beachball_still": ([beach_ball()], 1000, False, (6, 12)),
        "hammock": ([hammock(sw) for sw in (0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5)], 220, True, (42, 39)),
        "hammock_front": ([hammock_front(sw) for sw in (0, 0.5, 1, 0.5, 0, -0.5, -1, -0.5)], 220, True, (42, 39)),
        **{f"firefly_jar_{n}": ([firefly_jar(n, t) for t in (0, 0.25, 0.5)], 260, True, (7, 17)) for n in range(5)},
        "glow_jar": ([glow(34, 34, (230, 255, 120), s) for s in (0.7, 0.85, 0.6)], 260, True, (17, 17)),
        **{f"sunflowers_{look}": ([sunflowers(look, sw) for sw in (0, 1, 0, -1)], 600, True, (22, 63),
                                  {"perches": sunflower_heads(look)})
           for look in (0, 1, 2, 3, 4, "night")},
        "cattails_burst": ([cattails(3, 0, b) for b in (0.2, 0.5, 0.8, 1.0)] + [cattails(0, 0)], 110, False, (25, 58)),
    }
