"""Shared bits for the world's sprites: speech bubbles and their letters, rocks, twigs, crumbs and other
small pieces used by several of the other files."""
import math

from pixelkit import COMMON, Canvas


COMMON.update({
    "jay": ("#22406e", "#3462a0", "#4e86c8", "#86b2e4", "#101e36"),
    "woolly_dark": ("#100a08", "#1e1410", "#2e221c", "#40322a", "#060403"),
    "woolly_rust": ("#6e300e", "#9a4a1a", "#c0682c", "#d88a4c", "#3a1606"),
})


def _px(c, x, y, mat, level):
    if 0 <= x < c.w and 0 <= y < c.h:
        c.mat[y][x], c.fixed[y][x] = mat, level

def _daffodil_head(c, x, y, size=1.0):
    """A daffodil flower at (x, y), seen from the side and facing right: a round ring of yellow petals with a
    few pointed tips poking out of its edge, and an orange trumpet sticking out of the front with a flared rim.
    Placed pixel by pixel, so it stays crisp at this size."""
    cx, cy = int(round(x)), int(round(y))
    big = size >= 1
    r2 = 5.5 if big else 2.5  # the petal ring, centred a little behind the trumpet
    reach = 2 if big else 1
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if dx * dx + dy * dy <= r2:
                _px(c, cx - 1 + dx, cy + dy, "daffodil", 3 if dy < 0 else 2 if dy == 0 else 1)
    # pointed petal tips poking out past the ring: up, down, and back (two at the back on the big ones)
    _px(c, cx - 1, cy - reach - 1, "daffodil", 3)
    _px(c, cx - 1, cy + reach + 1, "daffodil", 1)
    for ty in ((-1, 1) if big else (0,)):
        _px(c, cx - 2 - reach, cy + ty, "daffodil", 2)
    _px(c, cx, cy, "daffodil_cup", 1)  # the trumpet, sticking out of the front...
    _px(c, cx + 1, cy, "daffodil_cup", 2)
    for dy in ((-1, 0, 1) if big else (0, 1)):  # ...with a frilly, flared rim
        _px(c, cx + 2, cy + dy, "daffodil_cup", 3 if dy <= 0 else 2)


def _twig(c, x1, y1, x2, y2, mat="bark", level=1):
    """A 1-pixel twig."""
    steps = int(max(abs(x2 - x1), abs(y2 - y1))) + 1
    for i in range(steps + 1):
        _px(c, round(x1 + (x2 - x1) * i / steps), round(y1 + (y2 - y1) * i / steps), mat, level)


def chip(mat, spin, size=1.0):
    """6 x 6: a little flying bit of something (a corn kernel, a chunk of pumpkin), turning over."""
    c = Canvas(6, 6)
    a = math.radians(spin * 45)
    c.ellipse(3, 3, 1.5 * size, 1.0 * size, mat, angle=math.degrees(a))
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


def _rock(c, rng, cx, cy, w, h, mat="stone", moss=False):
    """An irregular, faceted stone: a jagged outline lit from the top left, a darker underside."""
    pts = []
    for i in range(8):
        a = i / 8 * 2 * math.pi + rng.uniform(-0.25, 0.25)
        r = rng.uniform(0.82, 1.08)
        pts.append((cx + math.cos(a) * w * r, cy + math.sin(a) * h * r * (0.8 if math.sin(a) > 0 else 1.0)))
    c.polygon(pts, mat, lum=0.42)
    # a lit facet on the top left and a shadow band underneath give it weight
    c.polygon([(cx - w * 0.75, cy - h * 0.1), (cx - w * 0.2, cy - h * 0.85), (cx + w * 0.35, cy - h * 0.7),
               (cx - w * 0.05, cy - h * 0.05)], mat, lum=0.82)
    for y in range(int(cy + h * 0.35), int(cy + h) + 1):
        for x in range(int(cx - w) - 1, int(cx + w) + 2):
            if 0 <= x < c.w and 0 <= y < c.h and c.mat[y][x] == mat:
                c.fixed[y][x] = 0
    if moss:
        for x in range(int(cx - w * 0.6), int(cx + w * 0.3)):
            for y in range(int(cy - h * 1.1), int(cy - h * 0.3)):
                if 0 <= x < c.w and 0 <= y < c.h and c.mat[y][x] == mat and c.mat[y - 1][x] is None:
                    c.mat[y][x], c.fixed[y][x] = "moss", 2
                    if c.mat[y + 1][x] == mat and rng.random() < 0.6:
                        c.mat[y + 1][x], c.fixed[y + 1][x] = "moss", 1


def zzz(t=0.0):
    """10 x 10: a small floating z for a den with sleepers."""
    from PIL import Image
    img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    px = img.load()
    ink = (250, 246, 230, 255)
    edge = (60, 50, 40, 255)
    for (x, y) in ((2, 2), (3, 2), (4, 2), (5, 2), (5, 3), (4, 4), (3, 5), (2, 6), (3, 6), (4, 6), (5, 6)):
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            if px[x + dx, y + dy][3] == 0:
                px[x + dx, y + dy] = edge
    for (x, y) in ((2, 2), (3, 2), (4, 2), (5, 2), (5, 3), (4, 4), (3, 5), (2, 6), (3, 6), (4, 6), (5, 6)):
        px[x, y] = ink
    return img

BARREL_W, BARREL_H = 22, 22


def _barrel(c, left, bottom):
    """One upright oak barrel: bulging staves with dark seams, two iron hoops, a lighter top rim."""
    top = bottom - BARREL_H
    for y in range(top, bottom + 1):
        f = (y - top) / BARREL_H                      # 0 at the top rim, 1 at the base
        bulge = round(math.sin(math.pi * f) * 1.6)    # barrels bulge in the middle
        x0, x1 = left - bulge, left + BARREL_W - 1 + bulge
        for x in range(x0, x1 + 1):
            band = (x - x0) / max(1, x1 - x0)
            level = 3 if band < 0.12 else 2 if band < 0.38 else 1 if band < 0.75 else 0
            mat = "oak_wood"
            if (x - left) % 5 == 0 and 0.05 < f < 0.95:
                level = max(0, level - 1)             # the seams between staves
            if abs(f - 0.22) < 0.05 or abs(f - 0.78) < 0.05:
                mat = "hoop"
            if 0 <= x < c.w and 0 <= y < c.h:
                c.mat[y][x], c.fixed[y][x] = mat, level
    for x in range(left + 1, left + BARREL_W - 1):   # the top rim
        if 0 <= x < c.w:
            c.mat[top][x], c.fixed[top][x] = "oak_wood", 3


def crumb(i):
    """A tiny chewed-off bit of a dug-up icon."""
    c = Canvas(5, 5)
    c.ellipse(2.5, 2.5, 1.4 - i * 0.3, 1.1, "grey")
    return c.to_image()


def straw_bit(spin):
    c = Canvas(6, 6)
    a = math.radians(spin * 45)
    c.capsule(3 - 2 * math.cos(a), 3 - 2 * math.sin(a), 3 + 2 * math.cos(a), 3 + 2 * math.sin(a), 0.5, 0.4, "hay")
    return c.to_image(outline=False)


PIXEL_LETTERS = {
    "H": ["101", "101", "111", "101", "101"], "O": ["111", "101", "101", "101", "111"],
    "N": ["1001", "1101", "1011", "1001", "1001"], "K": ["101", "110", "100", "110", "101"],
    "!": ["1", "1", "1", "0", "1"], "R": ["110", "101", "110", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "B": ["110", "101", "110", "101", "110"], "T": ["111", "010", "010", "010", "010"],
    "G": ["111", "100", "101", "101", "111"], "L": ["100", "100", "100", "100", "111"],
    "E": ["111", "100", "110", "100", "111"], "C": ["111", "100", "100", "100", "111"],
    "A": ["010", "101", "111", "101", "101"], "W": ["10001", "10001", "10101", "10101", "01010"],
    "?": ["111", "001", "011", "000", "010"], " ": ["0", "0", "0", "0", "0"],
    "Z": ["111", "001", "010", "100", "111"],
    "Y": ["101", "101", "010", "010", "010"], "U": ["101", "101", "101", "101", "111"],
    "M": ["10001", "11011", "10101", "10001", "10001"],
}


def word_bubble(text):
    """A little speech bubble with text in a hand-made pixel font."""
    from PIL import Image
    width = sum(len(PIXEL_LETTERS[ch][0]) + 1 for ch in text) + 5
    w, h = width, 14
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
    for (x, y) in ((4, h - 3), (5, h - 3), (4, h - 2)):
        px[x, y] = edge
    px[5, h - 4] = fill
    x0 = 3
    for ch in text:
        for row, bits in enumerate(PIXEL_LETTERS[ch]):
            for col, bit in enumerate(bits):
                if bit == "1":
                    px[x0 + col, 2 + row] = ink
        x0 += len(PIXEL_LETTERS[ch][0]) + 1
    return img


def _rot_pts(points, angle, cx, cy):
    ca, sa = math.cos(angle), math.sin(angle)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in points]


def note(double=False):
    """8 x 10: a music note (or two joined) floating up from a singing bird."""
    c = Canvas(8, 10)
    c.ellipse(2, 8, 1.6, 1.2, "note", angle=-20)
    _twig(c, 3, 8, 3, 1, "note", 1)
    if double:
        c.ellipse(6, 7, 1.6, 1.2, "note", angle=-20)
        _twig(c, 7, 7, 7, 0, "note", 1)
        _twig(c, 3, 1, 7, 0, "note", 1)
        _twig(c, 3, 2, 7, 1, "note", 1)
    else:
        _twig(c, 3, 1, 5, 3, "note", 1)
    return c.to_image()


# -- weather: rain and snow --------------------------------------------------------------------------------


def _dots(w, h, dots):
    """A small see-through image from {(x, y): (r, g, b, a)}."""
    from PIL import Image
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y), rgba in dots.items():
        img.putpixel((x, y), rgba)
    return img


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        "honk_bubble": ([honk_bubble()], 1000, False, (4, 13)),
        "crumb": ([crumb(i) for i in range(2)], 120, True, (2, 2)),
        "straw_bit": ([straw_bit(s) for s in range(4)], 90, True, (3, 3)),
        "ribbit_bubble": ([word_bubble("RIBBIT")], 1000, False, (4, 13)),
        "cluck_bubble": ([word_bubble("CLUCK!")], 1000, False, (4, 13)),
        "gobble_bubble": ([word_bubble("GOBBLE!")], 1000, False, (4, 13)),
        "caw_bubble": ([word_bubble("CAW!")], 1000, False, (4, 13)),
        "yum_bubble": ([word_bubble("YUM!")], 1000, False, (4, 13)),
        "bleh_bubble": ([word_bubble("BLEH!")], 1000, False, (4, 13)),
        "hoo_bubble": ([word_bubble("HOO HOO")], 1000, False, (4, 13)),
        "buzz_bubble": ([word_bubble("BZZZZZ!")], 1000, False, (4, 13)),
        "apple_bit": ([chip("apple", s, 0.9) for s in range(4)], 90, True, (3, 3)),
        "leaf_bit": ([chip("lettuce", s, 1.0) for s in range(4)], 90, True, (3, 3)),
        "note": ([note()], 1000, False, (4, 9)),
        "note_double": ([note(True)], 1000, False, (4, 9)),
        "caw2_bubble": ([word_bubble("CAW CAW!")], 1000, False, (4, 13)),
        "kraa_bubble": ([word_bubble("KRAA!")], 1000, False, (4, 13)),
        "cawq_bubble": ([word_bubble("CAW?")], 1000, False, (4, 13)),
        "kernel": ([chip("cob", s, 0.9) for s in range(4)], 90, True, (3, 3)),
        "pumpkin_bit": ([chip("pumpkin", s, 1.2) for s in range(4)], 90, True, (3, 3)),
        "zzz": ([zzz()], 1000, False, (5, 9)),
    }
