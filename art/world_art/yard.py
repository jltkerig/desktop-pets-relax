"""All-year yard things: the fox den, the oak barrels and haystacks the foxes climb."""
import math
import random

from pixelkit import COMMON, Canvas
from .common import _rock


# -- the hoe and the den -------------------------------------------------------------------------------

COMMON.update({
    "handle": ("#6a4622", "#8e6232", "#ae7e46", "#c89c62", "#36220e"),
    "iron": ("#3a3c42", "#5a5e66", "#80848c", "#b0b4ba", "#1c1d20"),
    "earth": ("#4a3420", "#694a2e", "#86603c", "#a07a50", "#28190c"),
    "den_dark": ("#100a06", "#1c120c", "#2a1c12", "#3a281a", "#080503"),
    "grass": ("#3e5a1c", "#5a7c26", "#789e34", "#9cbe54", "#1e300a"),
})


COMMON.update({
    "stone": ("#4c4844", "#6e6862", "#928a82", "#b8b0a6", "#26231f"),
    "stone_dark": ("#3a3632", "#55504a", "#706a62", "#8c857c", "#1c1a17"),
    "moss": ("#3a5418", "#557422", "#71922e", "#94b04c", "#1c2c08"),
})


def den(occupants=(), snow=False):
    """112 x 56: a fox den. A lumpy earth mound set with stones: a big flat rock over the doorway,
    boulders on either side, pebbles and crumbly dirt clumps, grass and a root. occupants: fox palettes
    asleep inside, shown as sleepy snouts and ears poking out of the doorway. snow: snow lying over the top."""
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
    c.ellipse(door_x, ground, 13, 18, "den_dark", clip=lambda x, y: y <= ground)
    c.ellipse(door_x, ground - 3, 9, 12, "den_dark", bias=-0.4, clip=lambda x, y: y <= ground)
    # stones: a flat lintel over the door, boulders either side, smaller rocks and pebbles round the base
    _rock(c, rng, door_x, ground - 20, 15, 4.2, "stone", moss=True)
    _rock(c, rng, door_x - 17, ground - 5, 6.5, 6, "stone")
    _rock(c, rng, door_x + 17, ground - 4, 7, 5.5, "stone_dark", moss=True)
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
    if snow:  # a blanket of snow over the top of the mound and its stones (not in the doorway), grass buried
        srng = random.Random(11)
        for y in range(c.h):
            for x in range(c.w):
                if c.mat[y][x] in ("grass", "handle") and y < ground - 2:
                    c.mat[y][x] = None
        for x in range(c.w):
            top = next((y for y in range(c.h) if c.mat[y][x] is not None), None)
            if top is None or top > ground - 3:
                continue
            depth = 2 + (srng.random() < 0.5) + (1 if 30 < x < 85 else 0)
            for k in range(depth):
                y = top - 1 + k
                if 0 <= y < c.h:
                    c.mat[y][x], c.fixed[y][x] = "snow", (3 if k == 0 else 2 if k < depth - 1 else 1)
    # sleeping foxes: heads resting on their paws in the doorway, ears up against the dark burrow, snouts out
    sleepers = occupants[:2]
    for i, palette in enumerate(sleepers):
        two = len(sleepers) > 1
        side = (-1 if i == 0 else 1) if two else 1  # which way the snout points (out of the doorway)
        hx, hy = door_x + (side * 5.0 if two else -2.0), ground - 6.0
        sub = Canvas(112, 56, palette)
        for px_ in (2.0, 5.5):  # front paws, side by side under the chin
            sub.ellipse(hx + side * px_, ground - 1.0, 2.0, 1.2, "dark")
        for ex in (-2.6, 2.2):  # two tall pointed ears standing up, pale inside, dark at the tips
            bx = hx + ex
            lean = 0.7 if ex > 0 else -0.7
            sub.polygon([(bx - 2.0, hy - 2.0), (bx + 2.0, hy - 2.0), (bx + lean, hy - 10.0)], "fur", lum=0.55)
            for k in (4, 5, 6):
                sub.pixel(bx + lean * k / 10, hy - k, "white", 2 if k < 6 else 1)
            sub.pixel(bx + lean, hy - 9.5, "dark", 0)
            sub.pixel(bx + lean * 0.9, hy - 8.5, "dark", 1)
        sub.ellipse(hx, hy, 4.6, 3.6, "fur")                                              # the head
        sub.polygon([(hx + side * 1.5, hy - 1.2), (hx + side * 9.2, hy + 1.8), (hx + side * 9.2, hy + 3.4),
                     (hx + side * 1.5, hy + 3.4)], "fur", lum=0.6)                         # the snout, tapering
        sub.capsule(hx + side * 2.5, hy + 3.0, hx + side * 8.2, hy + 3.2, 0.9, 0.6, "white")  # pale under the muzzle
        for dx, dy in ((9.4, 2.0), (9.4, 3.0), (10.2, 2.0), (10.2, 3.0)):                  # the black nose
            sub.pixel(hx + side * dx, hy + dy, "nose", 0)
        sub.pixel(hx + side * 9.4, hy + 2.0, "white", 2)  # a shine on the nose, so it shows against the dark
        for dx, dy in ((0.6, -0.6), (1.6, -0.1), (2.6, -0.1), (3.4, -0.6)):  # a closed eye: a curved line
            sub.pixel(hx + side * dx, hy + dy, "dark", 0)
        c.ramps = {**c.ramps, **{f"{palette}_{k}": v for k, v in sub.ramps.items()}}
        for y in range(56):
            for x in range(112):
                if sub.mat[y][x] is not None:
                    c.mat[y][x], c.lum[y][x], c.fixed[y][x] = f"{palette}_{sub.mat[y][x]}", sub.lum[y][x], sub.fixed[y][x]
    return c.to_image()


# -- climbing things: oak barrels and haystacks ----------------------------------------------------------

COMMON.update({
    "oak_wood": ("#5a3418", "#7e4a22", "#a0662e", "#c08446", "#2c1808"),
    "hoop": ("#2a2a2e", "#44444a", "#66666e", "#8e8e96", "#121214"),
    "hay": ("#9a7a24", "#c4a03a", "#dcbc56", "#efd888", "#584010"),
    "twine": ("#6a4c22", "#8a6630", "#a88244", "#c4a066", "#36260e"),
})


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


COMMON.update({
    "frog": ("#2e5a1e", "#44802a", "#62a238", "#8ac25a", "#162e0c"),
    "frog_belly": ("#a8b06a", "#cad08a", "#e2e6aa", "#f4f6d0", "#5a5e2e"),
})


# -- a woodstack, an apple barrel, a stone well --------------------------------------------------------------

COMMON.update({
    "log_end": ("#a07a44", "#c49a5c", "#dcb878", "#eed29e", "#5a4022"),
    "apple": ("#7a0e10", "#b41a1a", "#dc3228", "#f06a54", "#420606"),
    "apple_green": ("#4e7a14", "#6ea020", "#90c034", "#b8dc62", "#283e08"),
    "well_stone": ("#5a5a5e", "#7e7e84", "#a2a2a8", "#c6c6cc", "#2e2e32"),
    "shingle": ("#4a2a1a", "#6a3c24", "#8a5232", "#a86e48", "#24140a"),
    "water": ("#1e4a8a", "#2e6ab8", "#4a8cdc", "#86b8f0", "#0e2448"),
})


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        "barrels": ([barrels()], 1000, False, (35, 62)),
        **{name: ([hay(name)], 1000, False, layout[1]) for name, layout in HAY_LAYOUTS.items()},
        "barrels_fall": (barrels_falling(), 90, False, (55, 62)),
        "den": ([den()], 1000, False, (56, 54)),
        "den_orange": ([den(("orange",))], 1000, False, (56, 54)),
        "den_grey": ([den(("grey",))], 1000, False, (56, 54)),
        "den_both": ([den(("orange", "grey"))], 1000, False, (56, 54)),
        "den_snow": ([den(snow=True)], 1000, False, (56, 54)),
        "den_snow_orange": ([den(("orange",), snow=True)], 1000, False, (56, 54)),
        "den_snow_grey": ([den(("grey",), snow=True)], 1000, False, (56, 54)),
        "den_snow_both": ([den(("orange", "grey"), snow=True)], 1000, False, (56, 54)),
    }
