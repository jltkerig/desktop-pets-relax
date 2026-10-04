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
    # bark texture: a few darker grooves
    for i in range(9):
        y = 128 + i * 7
        c.capsule(76 + (i % 3), y, 77 + (i % 3), y + 4, 0.7, 0.7, "bark", bias=-0.6)
    # the crown: overlapping clumps, back ones darker, colours mixed like an oak in October
    colours = ["leaf_orange"] * 5 + ["leaf_red"] * 4 + ["leaf_yellow"] * 4 + ["leaf_brown"] * 2 + ["leaf_green"] * 1
    clumps = []
    for _ in range(150):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, 1) ** 0.55
        cx = 80 + math.cos(a) * r * 64
        cy = 70 + math.sin(a) * r * 46
        clumps.append((cy, cx, rng.uniform(5.5, 9.5), rng.choice(colours)))
    for cy, cx, size, mat in sorted(clumps):  # back (higher) clumps first
        depth = (cy - 26) / 90  # lower clumps are nearer, so a little brighter
        c.ellipse(cx + sway * (1 - depth), cy, size, size * 0.8, mat, bias=-0.25 + depth * 0.25)
    # leafy speckle: scattered darker and lighter pixels break up the clumps
    for _ in range(900):
        x, y = rng.randrange(10, 150), rng.randrange(14, 124)
        if c.mat[y][x] and c.mat[y][x].startswith("leaf"):
            c.fixed[y][x] = rng.choice((0, 0, 2, 3))
    # loose leaf flecks on the crown's edge
    for _ in range(70):
        a = rng.uniform(0, 2 * math.pi)
        x = 80 + math.cos(a) * rng.uniform(55, 74) + sway
        y = 70 + math.sin(a) * rng.uniform(38, 54)
        c.ellipse(x, y, 1.6, 1.2, rng.choice(colours))
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
}
for colour in LEAF_COLOURS:
    SPRITES[f"leaf_{colour.split('_')[1]}"] = ([leaf(colour, s) for s in range(4)], 160, True, (4, 4))
