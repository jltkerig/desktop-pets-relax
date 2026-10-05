"""Night, weather and the sky: glows, paw prints, rain, snow, the sun and the moon."""
import math

from pixelkit import COMMON, Canvas
from .common import _dots


# -- night: glows, an owl, fireflies; paw prints in the snow ---------------------------------------------------

COMMON.update({
    "owl": ("#3e2e22", "#5e4632", "#806248", "#a48464", "#1e1610"),
    "owl_face": ("#9a8462", "#bca482", "#d6c2a0", "#ece0c6", "#5a4a32"),
    "owl_eye": ("#b8860c", "#e4b81c", "#f8d838", "#fcf088", "#5e4606"),
    "firefly": ("#a8b830", "#d4e040", "#f0f468", "#ffffb0", "#5a6014"),
    "print": ("#8a9ab0", "#a4b2c6", "#bcc8d8", "#d4dee8", "#5a6a80"),
})


def glow(w, h, rgb, strength=0.5):
    """w x h: a soft round glow of light (mostly see-through), to lay over something lit at night."""
    from PIL import Image
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    for y in range(h):
        for x in range(w):
            d = math.hypot((x + 0.5 - w / 2) / (w / 2), (y + 0.5 - h / 2) / (h / 2))
            if d < 1:
                a = (1 - d) ** 1.4 * strength
                a = round(a * 6) / 6  # in a few steps, so it stays pixel-art rather than a smooth blur
                if a > 0:
                    px[x, y] = rgb + (int(255 * a),)
    return img


def pawprint():
    """6 x 3: a fox's paw print pressed into the snow (a pad and toes, shadowed blue-grey)."""
    c = Canvas(6, 3)
    for x, y in ((1, 2), (2, 2), (2, 1), (1, 0), (3, 0)):
        c.pixel(x, y, "print", 1)
    return c.to_image(outline=False)


def raindrop():
    """2 x 8: a streak of falling rain, pale blue, clearer toward its tail, slanting a little."""
    dots = {}
    for y in range(8):
        dots[(1 if y < 4 else 0, y)] = (190, 214, 240, 70 + 22 * y)
    dots[(0, 7)] = (232, 244, 255, 255)
    return _dots(2, 8, dots)


def rain_splash(step):
    """7 x 4: a raindrop splashing on the ground: a little crown of droplets that spreads and fades."""
    a = (220, 170, 90)[step]
    rgb = (200, 222, 246)
    if step == 0:
        dots = {(3, 3): rgb + (a,), (2, 2): rgb + (a,), (4, 2): rgb + (a,)}
    elif step == 1:
        dots = {(1, 2): rgb + (a,), (5, 2): rgb + (a,), (2, 1): rgb + (a,), (4, 1): rgb + (a,), (3, 3): rgb + (a,)}
    else:
        dots = {(0, 3): rgb + (a,), (6, 3): rgb + (a,), (1, 1): rgb + (a,), (5, 1): rgb + (a,)}
    return _dots(7, 4, dots)


def snowflake(big=False):
    """A snowflake: 3 x 3 (a little cross), or 5 x 5 (a starry flake)."""
    white, soft = (250, 252, 255, 255), (226, 236, 248, 190)
    if not big:
        return _dots(3, 3, {(1, 1): white, (0, 1): soft, (2, 1): soft, (1, 0): soft, (1, 2): soft})
    dots = {(2, 2): white, (2, 1): white, (2, 3): white, (1, 2): white, (3, 2): white,
            (2, 0): soft, (2, 4): soft, (0, 2): soft, (4, 2): soft, (1, 1): soft, (3, 3): soft, (1, 3): soft,
            (3, 1): soft}
    return _dots(5, 5, dots)


# -- the sun and the moon -------------------------------------------------------------------------------------


def sun_disc(t=0.0):
    """26 x 26: the sun, a warm round disc with short rays all round that shimmer (t: which rays are long)."""
    from PIL import Image
    img = Image.new("RGBA", (26, 26), (0, 0, 0, 0))
    px = img.load()
    c, r = 12.5, 7.2
    for y in range(26):
        for x in range(26):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            if d <= r:
                f = d / r
                light = 1 - 0.55 * f - 0.25 * max(0.0, (dx + dy) / (2 * r))  # brighter at the top left
                px[x, y] = (255, int(200 + 50 * light), int(70 + 120 * light), 255)
            elif d <= r + 1.2:
                px[x, y] = (236, 150, 40, 255)  # a deeper orange rim
    for k in range(12):  # rays: alternate long and short, swapping as t changes
        a = k * math.pi / 6 + math.pi / 12
        long_ = (k + int(t * 2)) % 2 == 0
        for step in range(3 if long_ else 2):
            rr = r + 2.6 + step * 1.1
            x, y = int(round(c + math.cos(a) * rr)), int(round(c + math.sin(a) * rr))
            if 0 <= x < 26 and 0 <= y < 26:
                px[x, y] = (255, 214, 90, 255 - step * 50)
    return img


def moon_disc(frame=4):
    """22 x 22: the moon in one of 8 phases (0 new, 2 first quarter lit on the right, 4 full, 6 last quarter lit
    on the left), pale and cratered, the dark part just faintly showing."""
    from PIL import Image
    img = Image.new("RGBA", (22, 22), (0, 0, 0, 0))
    px = img.load()
    c, r = 10.5, 8.6
    theta = frame * 2 * math.pi / 8
    craters = ((-3.0, -2.5, 2.0), (2.5, 1.0, 2.4), (-1.0, 4.0, 1.5), (4.0, -3.5, 1.2), (-4.5, 2.0, 1.1))
    for y in range(22):
        for x in range(22):
            nx, ny = (x - c) / r, (y - c) / r
            if nx * nx + ny * ny > 1:
                continue
            w = math.sqrt(max(0.0, 1 - ny * ny))
            lit = nx > math.cos(theta) * w if theta <= math.pi else nx < -math.cos(theta) * w
            crater = any(math.hypot(x - c - cx, y - c - cy) < cr for cx, cy, cr in craters)
            if lit:
                shade = 0.92 - 0.12 * math.hypot(nx, ny) - (0.14 if crater else 0.0)
                px[x, y] = (int(250 * shade), int(246 * shade), int(222 * shade), 255)
            else:
                px[x, y] = (70, 78, 104, 110 if not crater else 125)  # the dark side, faintly
    return img


def tray_icon():
    """32 x 32 fox face for the tray."""
    import fox_art
    c = Canvas(32, 32)
    fox_art.head(c, 13, 18, tilt=0, eyes="open")
    return c.to_image()




def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        "tray_icon": ([tray_icon()], 1000, False, (16, 31)),
        "glow_warm": ([glow(44, 36, (255, 150, 40), s) for s in (0.9, 1.0, 0.82, 0.95)], 140, True, (22, 18)),
        "glow_warm_big": ([glow(96, 76, (255, 150, 40), s) for s in (0.9, 1.0, 0.82, 0.95)], 140, True, (48, 38)),
        "glow_lights": ([glow(64, 80, (255, 190, 70), s) for s in (0.8, 0.92, 0.72)], 450, True, (32, 40)),
        "glow_firefly": ([glow(14, 14, (230, 255, 120), s) for s in (0.7, 0.0, 0.0, 0.5)], 260, True, (7, 7)),
        "pawprint": ([pawprint()], 1000, False, (3, 2)),
        "sun": ([sun_disc(t) for t in (0.0, 0.5)], 900, True, (13, 13)),
        "moon": ([moon_disc(f) for f in range(8)], 1000, False, (11, 11)),
        "raindrop": ([raindrop()], 1000, True, (1, 7)),
        "rain_splash": ([rain_splash(i) for i in range(3)], 70, False, (3, 3)),
        "snowflake": ([snowflake()], 1000, True, (1, 2)),
        "snowflake_big": ([snowflake(True)], 1000, True, (2, 4)),
    }
