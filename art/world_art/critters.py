"""Animals and insects: squirrel, jay, woolly bear, geese, frog, turkeys, crows, songbirds, butterflies,
beetles, cicada, spider, inchworm, owl and fireflies."""
import math

from pixelkit import COMMON, Canvas, bezier
from .common import _twig


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


# -- geese ---------------------------------------------------------------------------------------------

COMMON.update({
    "goose": ("#4a3c30", "#6c5a48", "#8c7862", "#ab9882", "#241c14"),
    "goose_black": ("#0c0a0a", "#1a1616", "#2a2424", "#3e3636", "#040303"),
    "goose_pale": ("#a8a090", "#cfc8b8", "#e8e2d4", "#ffffff", "#5c564a"),
    "bubble": ("#d8d8d8", "#ffffff", "#ffffff", "#ffffff", "#2a2a2a"),
})


def goose(pose="walk", t=0.0):
    """32 x 32 Canada goose facing right. pose: walk, honk (neck up, beak open), fly."""
    c = Canvas(32, 32)
    s = math.sin(t * 2 * math.pi)
    if pose == "fly":
        y = 16
        c.capsule(9, y, 3, y - 1, 2.2, 1.6, "goose_pale")              # white rump and tail
        c.ellipse(14, y, 7.5, 3.6, "goose")
        c.ellipse(15, y + 2, 5.0, 1.6, "goose_pale", bias=-0.2)
        c.capsule(20, y - 1, 27, y - 3, 1.5, 1.2, "goose_black")         # neck stretched forward
        c.ellipse(28, y - 3.4, 2.2, 1.7, "goose_black")
        c.ellipse(27.6, y - 2.3, 1.2, 0.8, "goose_pale")                 # chin strap
        c.capsule(29.5, y - 3.2, 31.2, y - 2.8, 0.7, 0.5, "goose_black")
        wy = y - 1 - s * 8
        c.polygon([(10, y - 1), (17, y - 1), (13 - s, wy - 1), (9, wy)], "goose", lum=0.6)
        return c.to_image()
    step = s if pose == "walk" else 0.0
    # legs
    c.capsule(14, 22, 13 - step * 2, 29, 0.6, 0.6, "goose_black")
    c.capsule(17, 22, 18 + step * 2, 29, 0.6, 0.6, "goose_black")
    c.capsule(13 - step * 2, 29.5, 15.5 - step * 2, 29.5, 0.6, 0.6, "goose_black")
    c.capsule(18 + step * 2, 29.5, 20.5 + step * 2, 29.5, 0.6, 0.6, "goose_black")
    # body, folded wing, white rump
    c.capsule(8, 18, 4, 16, 2.2, 1.4, "goose_pale")
    c.ellipse(15, 18 + abs(step) * 0.5, 8.0, 5.0, "goose", angle=-8)
    c.ellipse(16, 21, 5.5, 2.0, "goose_pale", bias=-0.2)
    c.ellipse(13, 17, 5.5, 3.0, "goose", bias=-0.25, angle=-10)
    # neck and head: tall when honking
    if pose == "honk":
        top = (24, 3 + t * 2)
        c.capsule(21, 15, top[0], top[1] + 3, 1.7, 1.4, "goose_black")
        c.ellipse(top[0] + 1, top[1] + 1, 2.4, 1.9, "goose_black", angle=-25)
        c.ellipse(top[0] + 0.4, top[1] + 2.2, 1.2, 0.8, "goose_pale")
        open_by = 1.2 if t < 0.6 else 0.3
        c.capsule(top[0] + 3, top[1], top[0] + 6, top[1] - 2.0, 0.6, 0.5, "goose_black")
        c.capsule(top[0] + 3, top[1] + 0.8, top[0] + 6, top[1] + 0.8 + open_by - 1.0, 0.5, 0.4, "goose_black")
        c.pixel(top[0] + 1, top[1], "eye")
    else:
        bob = s * 1.2
        c.capsule(21, 15, 24 + bob * 0.5, 7 + abs(bob) * 0.4, 1.7, 1.4, "goose_black")
        hx, hy = 25 + bob * 0.5, 6 + abs(bob) * 0.4
        c.ellipse(hx, hy, 2.4, 1.8, "goose_black")
        c.ellipse(hx - 0.4, hy + 1.1, 1.2, 0.8, "goose_pale")
        c.capsule(hx + 2, hy + 0.2, hx + 4.5, hy + 0.5, 0.7, 0.5, "goose_black")
    return c.to_image()


def goose_far(t=0.0):
    """12 x 8 distant goose silhouette for a migrating V, flying left (drawn facing right; mirrored)."""
    c = Canvas(14, 10)
    s = math.sin(t * 2 * math.pi)
    c.capsule(2, 5, 10, 5, 1.2, 0.9, "goose_black")
    c.ellipse(11.5, 4.8, 1.2, 1.0, "goose_black")
    c.capsule(6.5, 5, 4.5, 5 - s * 4.2, 1.1, 0.6, "goose")  # wing beating up and down
    c.capsule(7.5, 5, 6.0, 5 - s * 3.6, 0.9, 0.5, "goose", bias=-0.3)
    return c.to_image(outline=False)


def frog(pose="sit", t=0.0):
    """18 x 16 frog facing right. sit puffs its throat; hop stretches out its legs."""
    c = Canvas(18, 16)
    if pose == "hop":
        s = math.sin(t * math.pi)
        y = 9 - s * 4
        c.capsule(5, y + 2, 1, y + 4 + s * 2, 1.0, 0.8, "frog", -0.25)    # back legs kicking out
        c.ellipse(9, y, 5.5, 3.2, "frog", angle=-12 * s)
        c.capsule(12, y + 2, 15, y + 5, 0.8, 0.7, "frog")                  # front legs reaching
        hx, hy = 13, y - 2
    else:
        puff = math.sin(t * math.pi) * 1.4
        c.capsule(4, 13, 9, 14, 1.4, 1.0, "frog", -0.25)                   # folded back leg
        c.ellipse(9, 11, 5.5, 3.6, "frog")
        c.ellipse(12, 13 - puff * 0.3, 2.0 + puff, 1.4 + puff * 0.8, "frog_belly")  # the throat puffing
        c.capsule(12, 12, 13, 14.5, 0.8, 0.7, "frog")
        hx, hy = 13, 8
    c.ellipse(hx, hy, 3.4, 2.4, "frog")
    for ex in (-1.6, 1.4):  # bulging eyes on top
        c.ellipse(hx + ex, hy - 2.2, 1.3, 1.2, "frog", bias=0.2)
        c.pixel(hx + ex + 0.4, hy - 2.4, "eye")
    c.capsule(hx + 1, hy + 1, hx + 3, hy + 0.6, 0.3, 0.3, "frog", -0.6)   # a wide smile
    return c.to_image()


# -- wild turkeys and crows ------------------------------------------------------------------------------

COMMON.update({
    "turkey": ("#2a1a10", "#4a2e1a", "#6e4626", "#946436", "#140c06"),
    "turkey_bar": ("#8a6a3a", "#b8925a", "#d4b47c", "#ecd6a4", "#4a3618"),
    "turkey_head": ("#5a6e9a", "#7e96c4", "#a6bce0", "#cad8f0", "#2e3a56"),
    "wattle": ("#7a1414", "#b02020", "#d63a32", "#ee6a5a", "#3e0808"),
    "turkey_leg": ("#7a5e5a", "#a08480", "#c4a8a2", "#dccac4", "#3e2e2c"),
    "turkey_hen": ("#3e2c1c", "#604630", "#866443", "#a8875e", "#1e140c"),
    "turkey_hen_bar": ("#9a8460", "#bca47c", "#d6c09a", "#ecdcbc", "#5a4a30"),
    "turkey_hen_head": ("#6a7280", "#8e98a8", "#b2bac6", "#d2d8e0", "#3a3e48"),
    "crow": ("#08080c", "#14141c", "#22222e", "#363a4e", "#020204"),
    "crow_sheen": ("#1a2238", "#283456", "#3a4a78", "#5468a0", "#0a0e1a"),
})


def turkey(pose="stand", t=0.0, hen=False):
    """40 x 40 wild turkey facing right. pose: run, stand, look (head up, glancing back), gobble (tail
    fanned, head thrust out, wattle shaking), peck (head down at the ground), call (a hen's cluck: head
    forward, beak open). hen: a hen, smaller and plainer: lighter brown, a greyish feathered head, no red
    wattle, no beard, and she doesn't fan her tail."""
    c = Canvas(40, 40)
    s = math.sin(t * 2 * math.pi)
    run = pose == "run"
    ground = 38
    body, bar, head = ("turkey_hen", "turkey_hen_bar", "turkey_hen_head") if hen else \
        ("turkey", "turkey_bar", "turkey_head")
    small = 0.86 if hen else 1.0
    # legs: long strides when running, planted otherwise
    stride = s * 4 if run else 0.0
    body_y = (24 if hen else 22) - (abs(s) * 1.5 if run else 0.0)
    for lx, d in ((17, stride), (21, -stride)):
        c.capsule(lx, body_y + 5, lx + d, ground - 1, 0.7, 0.6, "turkey_leg")
        c.capsule(lx + d, ground, lx + d + 3, ground, 0.6, 0.5, "turkey_leg")
    # the tail: a big barred fan when a tom gobbles, otherwise folded down behind
    if pose == "gobble" and not hen:
        fan = 0.7 + 0.3 * t
        for i in range(7):
            a = math.radians(-160 + i * 22 * fan)
            tip = (12 + math.cos(a) * 14, body_y - 2 + math.sin(a) * 14)
            c.capsule(12, body_y, tip[0], tip[1], 1.6, 2.6, body, 0.1)
            c.ellipse(tip[0], tip[1], 2.2, 2.2, bar, bias=0.1)
    else:
        droop = 3 if run else 6
        c.capsule(12, body_y, 4 if hen else 3, body_y + droop, 2.6 * small, 2.0 * small, body, -0.2)
        c.capsule(5, body_y + droop - 1, 2, body_y + droop + 1, 1.4, 1.2, bar)
    # body: round, bronze for a tom and soft brown for a hen, with pale barring on the folded wing
    tilt = -18 if run else 0
    c.ellipse(19, body_y, 10.0 * small, 7.5 * small, body, angle=tilt)
    c.ellipse(18, body_y - 1, 7.0 * small, 4.5 * small, body, bias=-0.2, angle=tilt)
    for bx in ((13, 15, 17, 19, 21) if hen else (13, 16, 19)):
        c.capsule(bx, body_y + 2, bx + (1.5 if hen else 2), body_y + 3, 0.5, 0.5, bar)
    if hen:  # pale scalloping all over her back too
        for bx, by in ((15, body_y - 3), (19, body_y - 4), (23, body_y - 2), (17, body_y)):
            c.pixel(bx, by, bar, 2)
    # neck and head: where the head is depends on what it's doing
    lift = 3 if hen else 0  # a hen stands a little lower
    if pose == "peck":
        hx, hy = 31 + s * 0.5, ground - 4 + abs(s) * 2
    elif pose in ("gobble", "call"):
        hx, hy = 32 + s * 0.8, body_y - 4
    elif pose == "look":
        hx, hy = 27 - max(0.0, s) * 4, 7 + abs(s) + lift  # head up high, turning back over its shoulder
    elif run:
        hx, hy = 33, body_y - 8
    else:
        hx, hy = 28 + s * 0.5, 9 + lift
    if hen:  # a feathered brown neck, only her face bare and greyish
        c.capsule(24, body_y - 3, hx - 1, hy + 2, 2.8, 1.8, body, bias=-0.1)
        c.ellipse(hx, hy, 2.2, 2.0, head)
        c.capsule(hx - 1.5, hy - 1.4, hx + 0.6, hy - 1.7, 0.7, 0.5, body)  # a feathered brown cap
    else:
        c.capsule(25, body_y - 3, hx - 1, hy + 2, 2.2, 1.2, head, bias=-0.1)  # a bare, bluish neck
        c.ellipse(hx, hy, 2.4, 2.2, head)
    if not hen:
        wobble = s * 1.2 if pose == "gobble" else 0.0
        c.capsule(hx + 0.5, hy + 1.5, hx + 0.5 + wobble, hy + 4.5, 1.0, 1.3, "wattle")  # the red wattle
        c.capsule(hx + 1.5, hy - 1.2, hx + 3.2, hy + 1.8, 0.5, 0.5, "wattle")           # the snood over the beak
    c.capsule(hx + 2, hy + 0.2, hx + 4, hy + 0.8, 0.6, 0.4, "beak")
    if pose in ("gobble", "call") and t < 0.7:
        c.capsule(hx + 2, hy + 1.4, hx + 4, hy + 2.4, 0.5, 0.4, "beak")  # beak open
    c.pixel(hx + 0.5, hy - 0.8, "eye")
    if not hen:  # the tom's "beard" hanging from his chest
        c.capsule(27, body_y - 1, 28, body_y + 4, 0.6, 0.4, "turkey", -0.3)
    return c.to_image()


def crow(pose="perch", t=0.0, acorn_in_beak=False, hat=False):
    """24 x 24 American crow facing right. pose: fly, perch, hop, walk, peck, caw, tilt (head cocked,
    looking at something). hat: wearing the scarecrow's hat, which it has pinched."""
    c = Canvas(24, 24)
    s = math.sin(t * 2 * math.pi)
    if pose == "fly":
        c.capsule(7, 12, 1, 12 + s, 1.6, 2.2, "crow", -0.3)  # a fanned tail
        c.ellipse(12, 12, 6.0, 3.0, "crow")
        wing_y = 12 - s * 7
        c.polygon([(9, 11), (14, 11), (9 - s, wing_y - 1), (5, wing_y)], "crow_sheen", lum=0.4)
        hx, hy = 18, 10.5
    else:
        hop = max(0.0, s) * 2.5 if pose == "hop" else 0.0
        step = s * 1.5 if pose == "walk" else 0.0
        lean = 20 if pose == "peck" else 0
        by = 14 - hop
        c.capsule(12 + step, by + 3, 11 + step * 1.5, 22 - hop, 0.5, 0.5, "crow")   # legs
        c.capsule(14 - step, by + 3, 14 - step * 1.5, 22 - hop, 0.5, 0.5, "crow")
        c.capsule(9, by + 1, 3, by + 5, 1.8, 1.4, "crow", -0.3)  # tail
        c.ellipse(12, by, 5.5, 4.0, "crow", angle=lean - 15)
        c.polygon([(8, by - 2), (14, by - 2), (7, by + 3)], "crow_sheen", lum=0.3)  # folded wing
        if pose == "peck":
            hx, hy = 18, 19 + abs(s) * 2 - hop
        elif pose == "caw":
            hx, hy = 17 + t * 1.5, 8 - t - hop  # head stretched forward and up
        elif pose == "tilt":
            hx, hy = 16.5, 9.5 - hop
        else:
            hx, hy = 16, 9 - hop
    c.ellipse(hx, hy, 3.0, 2.7, "crow")
    if pose == "caw" and t < 0.7:  # beak wide open
        c.polygon([(hx + 2, hy - 0.8), (hx + 6, hy - 2.2), (hx + 2.4, hy + 0.4)], "crow", lum=0.5)
        c.polygon([(hx + 2, hy + 0.8), (hx + 5.4, hy + 2.4), (hx + 2.4, hy + 1.6)], "crow", lum=0.5)
    else:
        c.polygon([(hx + 2.2, hy - 0.9), (hx + 5.6, hy + 0.4), (hx + 2.2, hy + 1.2)], "crow", lum=0.6)
    if acorn_in_beak:
        c.ellipse(hx + 5.2, hy + 1.2, 1.4, 1.6, "acorn")
        c.ellipse(hx + 5.2, hy - 0.2, 1.5, 0.8, "cap")
    eye_y = hy - (1.4 if pose == "tilt" else 0.8)
    c.pixel(hx + 0.8, eye_y, "white", 2)  # a glint, so the eye shows against the black
    if hat:  # far too big for it, tipped back on its head
        c.capsule(hx - 4.5, hy - 2.2, hx + 3.5, hy - 2.8, 0.9, 0.8, "hat")
        c.ellipse(hx - 0.6, hy - 4.4, 2.8, 2.1, "hat")
        c.capsule(hx - 3, hy - 3.4, hx + 2, hy - 3.6, 0.5, 0.5, "plaid_red")
    return c.to_image()


def inchworm(pose="crawl", t=0.0):
    """14 x 8: a little green inchworm. crawl: looping along, back end up to front; fall: curled up."""
    c = Canvas(14, 8)
    if pose == "fall":
        c.ellipse(7, 4, 3.0, 2.6, "inchworm")
        c.ellipse(7, 4, 1.4, 1.1, "inchworm", bias=-0.5)
        c.pixel(9, 3, "eye")
        return c.to_image()
    arch = math.sin(t * math.pi)  # 0 flat .. 1 a tall loop
    length = 10 - arch * 4
    left = 2 + (10 - length) * (t if t < 0.5 else 1 - t) * 2
    pts = [(left + length * i / 6, 6 - math.sin(i / 6 * math.pi) * arch * 4) for i in range(7)]
    c.chain(pts, [1.3] * 7, ["inchworm"] * 7)
    c.pixel(pts[-1][0] + 0.5, pts[-1][1] - 0.5, "eye")
    return c.to_image()


BUTTERFLIES = {"monarch": "monarch", "white": "wing_white", "sulphur": "wing_sulphur", "azure": "wing_azure"}


def butterfly(t=0.0, kind="monarch", span=None):
    """14 x 12: a butterfly seen from above (resting on a flower), wings opening and closing (wide open .. edge on). kind: monarch (orange
    and black), white (a cabbage white), sulphur (lemon yellow) or azure (sky blue). span: how open the wings
    are (otherwise from t)."""
    c = Canvas(14, 12)
    mat = BUTTERFLIES[kind]
    if span is None:
        span = 0.25 + 0.75 * abs(math.cos(t * math.pi))
    for side in (-1, 1):
        upper = [(7, 5), (7 + side * 6.2 * span, 1.2), (7 + side * 6.0 * span, 5.6)]
        lower = [(7, 6), (7 + side * 4.4 * span, 6.4), (7 + side * 3.2 * span, 10)]
        c.polygon(upper, mat, lum=0.6)
        c.polygon(lower, mat, lum=0.45)
        if span > 0.5 and kind == "monarch":  # black edges with white dots, black veins
            c.pixel(7 + side * 5.6 * span, 2, "bug_black", 0)
            c.pixel(7 + side * 5.6 * span, 4.4, "bug_black", 0)
            c.pixel(7 + side * 4.8 * span, 2.8, "white", 3)
            c.pixel(7 + side * 3 * span, 3.6, "bug_black", 0)
            c.pixel(7 + side * 2.6 * span, 8, "bug_black", 0)
        elif span > 0.5 and kind == "white":  # black wing tips and a spot
            c.pixel(7 + side * 5.8 * span, 1.6, "bug_black", 0)
            c.pixel(7 + side * 3.6 * span, 3.4, "bug_black", 1)
        elif span > 0.5:  # a dark edge and an eyespot
            c.pixel(7 + side * 5.8 * span, 2.2, mat, 0)
            c.pixel(7 + side * 3.0 * span, 7.6, "star" if kind == "azure" else "ladybug", 2)
    c.capsule(7, 3.5, 7, 9, 0.6, 0.5, "bug_black")  # body
    for side in (-1, 1):
        c.capsule(7, 3.5, 7 + side * 1.8, 0.8, 0.2, 0.2, "bug_black")  # antennae
    return c.to_image()


def butterfly_flying(t=0.0, kind="monarch"):
    """18 x 16: a butterfly in flight, seen from the side and facing right: a slim body held level, and big
    wings clapping together up over its back, then sweeping down below it (their patterned faces show then)."""
    c = Canvas(18, 16)
    mat = BUTTERFLIES[kind]
    up = 0.5 + 0.5 * math.cos(t * 2 * math.pi)  # 1: wings straight up together .. 0: swept down
    a = math.radians(-92 + 120 * (1 - up))      # the wings' angle from level (negative: up)
    rx, ry = 9.0, 8.0                           # where they join the body

    def wing(length, back, lum, pattern):
        dx, dy = math.cos(a), math.sin(a)
        tip = (rx + dx * length * 0.5 + 1.0 - back, ry + dy * length)
        hind = (rx - 3.6 - back, ry + dy * length * 0.5 + (1.6 if dy < 0 else -0.4))
        c.polygon([(rx + 1.4, ry), (tip[0] + 1.2, tip[1] + 0.4 * dy), tip, (tip[0] - 2.6, tip[1] - 0.2 * dy),
                   hind, (rx - 2.2, ry)], mat, lum=lum)
        if pattern and up < 0.8:  # the near wing's markings show as it opens out
            mx, my = (rx + tip[0]) / 2 - 0.5, (ry + tip[1]) / 2
            if kind == "monarch":
                c.pixel(tip[0], tip[1], "bug_black", 0)
                c.pixel(mx, my, "bug_black", 0)
                c.pixel(tip[0] - 1.6, tip[1] - 0.3 * dy, "white", 3)
            elif kind == "white":
                c.pixel(tip[0], tip[1], "bug_black", 0)
            else:
                c.pixel(mx, my, "star" if kind == "azure" else "ladybug", 2)

    wing(6.6, 1.4, 0.45, False)                       # the far wing, a little behind
    c.capsule(5.0, ry + 0.6, 11.4, ry - 0.2, 0.5, 0.6, "bug_black")  # the slim body, level
    c.pixel(12.4, ry - 1.4, "bug_black", 0)          # antennae, short and forward
    c.pixel(13.4, ry - 2.4, "bug_black", 0)
    wing(7.6, 0.0, 0.7, True)                         # the near wing, in front
    return c.to_image()


def beetle(kind="junebug", pose="crawl", t=0.0):
    """10 x 12: a June beetle or a ladybug, head up, climbing the trunk. fly: wing cases up, wings out."""
    c = Canvas(10, 12)
    body = "beetle_brown" if kind == "junebug" else "ladybug"
    step = math.sin(t * 2 * math.pi)
    for side in (-1, 1):  # legs, three a side, scrabbling
        for k, y in enumerate((5, 7, 9)):
            reach = 3.0 + (step if (k % 2) ^ (side > 0) else -step) * 0.8
            c.capsule(5 + side * 1.5, y, 5 + side * reach, y + (k - 1) * 1.2, 0.35, 0.3, "bug_black")
    if pose == "fly":
        for side in (-1, 1):  # the wing cases lifted, and the thin wings whirring behind
            c.ellipse(5 + side * (3.5 + abs(step)), 8, 2.4, 3.2, "wing_clear", angle=side * 25)
            c.ellipse(5 + side * 2.4, 6, 1.8, 2.6, body, angle=side * 35)
    c.ellipse(5, 7.5, 2.6, 3.4 if kind == "junebug" else 2.9, body)
    if kind == "ladybug":
        for dx, dy in ((-1.2, 6.5), (1.2, 6.5), (-1.4, 8.8), (1.4, 8.8), (0, 10)):
            c.pixel(5 + dx, dy, "bug_black", 0)
        c.ellipse(5, 3.6, 1.6, 1.2, "bug_black")  # the head
        c.pixel(4.4, 3.4, "white", 3)
        c.pixel(5.6, 3.4, "white", 3)
    else:
        c.capsule(5, 5, 5, 10.5, 0.3, 0.3, "beetle_brown", bias=-0.6)  # the line down its back
        c.ellipse(5, 3.6, 1.6, 1.3, "beetle_brown", bias=-0.2)
    for side in (-1, 1):
        c.capsule(5 + side * 0.8, 2.8, 5 + side * 2.2, 1.2, 0.25, 0.2, "bug_black")  # feelers
    return c.to_image()


def cicada(pose="sit", t=0.0):
    """10 x 14: a cicada on the trunk, head up. buzz: its body thrums. (Flying: cicada_flying.)"""
    c = Canvas(10, 14)
    shake = (0.5 if int(t * 8) % 2 else -0.5) if pose == "buzz" else 0.0
    if pose == "fly":
        for side in (-1, 1):
            c.ellipse(5 + side * 3.5, 7 + math.sin(t * 2 * math.pi) * 1.5, 2.6, 4.4, "wing_clear", angle=side * 30)
    else:  # clear wings folded like a roof over its back
        for side in (-1, 1):
            c.polygon([(5 + shake, 4), (5 + side * 3.2 + shake, 7), (5 + side * 2.2 + shake, 13), (5 + shake, 12)],
                      "wing_clear", lum=0.5 if side < 0 else 0.7)
    c.ellipse(5 + shake, 7, 2.0, 3.2, "cicada")
    c.ellipse(5 + shake, 3.2, 2.6, 1.6, "cicada", bias=0.1)  # the broad head
    for side in (-1, 1):
        c.pixel(5 + side * 2.2 + shake, 3, "ladybug", 2)  # red eyes
    return c.to_image()


def cicada_flying(t=0.0):
    """16 x 12: a cicada in flight, seen from the side and facing right: a stout body held level, the broad head
    in front with a red eye, legs tucked under, and clear wings beating in a blur above its back."""
    c = Canvas(16, 12)
    beat = math.sin(t * 2 * math.pi)
    for k, lum in ((0, 0.5), (1, 0.75)):  # the far wing, then the near one, swept up and down
        tip_y = 2.5 - beat * 2.4 + k * 0.6
        c.polygon([(9.5, 6), (3.5 - k, tip_y + 0.5), (1.5 - k * 0.5, tip_y + 2.5), (7.5, 7)], "wing_clear", lum=lum)
    c.ellipse(7.5, 7.2, 4.6, 2.1, "cicada")                  # the body, level
    for x in (4.5, 6.0, 7.5):                                # rings along the abdomen
        c.pixel(x, 8, "cicada", 0)
    c.ellipse(12.2, 6.8, 1.9, 1.8, "cicada", bias=0.1)       # the broad head
    c.pixel(12.8, 6, "ladybug", 2)                           # a red eye
    for x in (8.5, 10.0):                                    # legs tucked up underneath
        c.pixel(x, 9.4, "cicada", 0)
    return c.to_image()


def spider(t=0.0):
    """13 x 11: a little garden spider hanging from its thread, long legs wiggling."""
    c = Canvas(13, 11)
    wig = math.sin(t * 2 * math.pi) * 0.7
    cx = 6.5
    for side in (-1, 1):  # four long, bent legs a side: out to a knee, then down
        for k, (ky, fy) in enumerate(((2.0, 0.5), (2.8, 3.0), (3.6, 6.0), (4.2, 9.0))):
            knee = (cx + side * (3.4 + (k in (1, 2)) * 0.8), ky - 1.6 + (wig if k % 2 else -wig))
            foot = (cx + side * (5.6 - abs(k - 1.5) * 0.4), fy + (wig if k % 2 else -wig) * 0.5)
            _twig(c, cx, 3.6, *knee, "bug_black", 1)
            _twig(c, *knee, *foot, "bug_black", 0)
    c.ellipse(cx, 6.2, 2.0, 2.3, "beetle_brown", bias=-0.2)  # the round abdomen
    c.pixel(cx, 6, "daffodil", 2)                             # a little gold mark
    c.ellipse(cx, 3.4, 1.3, 1.1, "bug_black")
    return c.to_image(outline=False)  # thin legs, no outline to thicken them


def silk():
    """1 x 6: a length of spider silk (the thread is a stack of these)."""
    from PIL import Image
    img = Image.new("RGBA", (1, 6), (236, 240, 244, 210))
    return img


SONGBIRDS = {  # back, breast, head, beak
    "robin": ("robin_back", "robin_breast", "bug_black", "beak"),
    "bluebird": ("bluebird", "robin_breast", "bluebird", "bug_black"),
    "goldfinch": ("goldfinch", "goldfinch", "goldfinch", "daffodil_cup"),
}


def songbird(kind="robin", pose="perch", t=0.0):
    """20 x 20: a small songbird facing right: a robin (orange breast), a bluebird or a goldfinch (yellow, black
    wings and cap). pose: perch, hop, fly, sing (head up, beak open), peck, worm (a robin tugging up a worm)."""
    c = Canvas(20, 20)
    back, breast, head, beak = SONGBIRDS[kind]
    s = math.sin(t * 2 * math.pi)
    wing = "bug_black" if kind == "goldfinch" else back
    if pose == "fly":
        c.capsule(6, 10, 1, 9 + s, 1.4, 1.0, back, -0.3)
        c.ellipse(10, 10, 4.6, 2.8, back)
        c.ellipse(11, 11.4, 3.4, 1.4, breast, bias=0.1)
        c.polygon([(8, 9), (12, 9), (8 - s, 9 - s * 5.5), (5, 9 - s * 5)], wing, lum=0.5)
        hx, hy = 14.5, 8.5
    else:
        hop = max(0.0, s) * 2 if pose == "hop" else 0.0
        bow = (2.5 + abs(s) * 1.5) if pose in ("peck", "worm") else 0.0
        by = 12 - hop
        c.capsule(8, by + 1, 3, by + 4, 1.3, 1.0, back, -0.3)                  # tail
        c.capsule(10, by + 3, 9.5, 18 - hop, 0.4, 0.4, "bark")                  # legs
        c.capsule(12, by + 3, 12.5, 18 - hop, 0.4, 0.4, "bark")
        c.ellipse(10.5, by, 4.4, 3.6, back, angle=-10)
        c.ellipse(12, by + 1.2, 3.0, 2.6, breast, bias=0.15)                    # the breast
        c.polygon([(7.5, by - 1.5), (11.5, by - 1.5), (7, by + 2.5)], wing, lum=0.35)  # folded wing
        if kind == "goldfinch":
            c.pixel(9, by, "white", 3)  # white wing bar
        if pose == "sing":
            hx, hy = 14.5, 6.5 - hop
        else:
            hx, hy = 14 + bow * 0.6, 8 - hop + bow * 2
    c.ellipse(hx, hy, 2.6, 2.4, head)
    if kind == "goldfinch":
        c.ellipse(hx - 0.4, hy - 1.2, 1.6, 0.9, "bug_black")  # black cap
    if kind == "robin":
        c.pixel(hx + 0.2, hy - 1.2, "white", 3)  # the white ring round its eye
    open_ = pose == "sing" and t < 0.75
    if open_:
        c.capsule(hx + 2, hy - 0.6, hx + 4.4, hy - 1.8, 0.4, 0.3, beak)
        c.capsule(hx + 2, hy + 0.4, hx + 4.0, hy + 1.2, 0.4, 0.3, beak)
    else:
        c.capsule(hx + 2, hy, hx + 4.2, hy + 0.3, 0.5, 0.3, beak)
    if pose == "worm":  # a wiggly pink worm stretching from its beak to the ground
        stretch = 2 + abs(s) * 3
        c.chain([(hx + 4, hy + 0.5 + k * stretch / 4 + (0.5 if k % 2 else -0.5)) for k in range(5)], [0.5] * 5,
                ["tulip_pink"] * 5)
    c.pixel(hx + 0.6, hy - 0.6, "eye")
    return c.to_image()


def owl(pose="perch", t=0.0):
    """20 x 22: a great horned owl, facing you: ear tufts, a pale face disc and big yellow eyes. pose: perch
    (blinks now and then), hoot (puffs up, beak open), turn (head swivelled round), fly."""
    c = Canvas(20, 22)
    if pose == "fly":
        s = math.sin(t * 2 * math.pi)
        c.ellipse(10, 11, 4, 3.2, "owl")
        for side in (-1, 1):
            c.polygon([(10, 10), (10 + side * 9, 10 - s * 6), (10 + side * 8, 13 - s * 3), (10, 13)], "owl", lum=0.5)
        c.ellipse(10, 7, 3, 2.6, "owl_face")
        for side in (-1, 1):
            c.pixel(10 + side * 1.2, 7, "owl_eye", 3)
        return c.to_image()
    puff = 1.0 if pose == "hoot" else 0.0
    c.ellipse(10, 14, 5.2 + puff, 6, "owl")                    # the body, barred
    for y in range(10, 20, 2):
        for x in range(6, 15, 2):
            if c.mat[y][x] == "owl":
                c.pixel(x + (y // 2) % 2, y, "owl", 0)
    c.ellipse(10, 15.5, 3, 3.6, "owl_face", bias=-0.1)          # pale front
    c.capsule(8, 20.5, 12, 20.5, 0.6, 0.6, "owl_eye")           # feet on the branch
    hx = 10 + (2.5 if pose == "turn" else 0)
    c.ellipse(hx, 7, 4.6, 4.0, "owl")                           # the head, with ear tufts
    for side in (-1, 1):
        c.polygon([(hx + side * 1.5, 4), (hx + side * 4.5, 0.5), (hx + side * 3.8, 5)], "owl", lum=0.5)
    if pose != "turn":
        c.ellipse(hx, 7.5, 3.6, 3.0, "owl_face")                # the face disc
        blink = pose == "perch" and t > 0.85
        for side in (-1, 1):
            if blink:
                c.pixel(hx + side * 1.6, 7, "owl", 0)
                c.pixel(hx + side * 1.6 + side, 7, "owl", 0)
            else:
                c.ellipse(hx + side * 1.6, 7, 1.2, 1.2, "owl_eye")
                c.pixel(hx + side * 1.6, 7, "bug_black", 0)
        c.pixel(hx, 9, "owl", 0)                                # beak
        if pose == "hoot":
            c.pixel(hx, 10, "owl", 0)
    return c.to_image()


def firefly(lit=True):
    """5 x 5: a firefly, its tail lit up (or dark, between blinks)."""
    c = Canvas(5, 5)
    c.pixel(1, 2, "bug_black", 1)
    if lit:
        for dx, dy in ((2, 2), (3, 2), (2, 1), (2, 3), (3, 1), (3, 3)):
            c.pixel(dx, dy, "firefly", 3 if (dx, dy) == (2, 2) else 2)
    else:
        c.pixel(2, 2, "firefly", 0)
    return c.to_image(outline=False)


def sprites():
    """This file's sprites: name -> (frames, ms per frame, loop, anchor[, extra])."""
    return {
        "squirrel_run": ([squirrel("run", i / 4) for i in range(4)], 70, True, (16, 29)),
        "squirrel_carry": ([squirrel("run", i / 4, acorn_in_mouth=True) for i in range(4)], 70, True, (16, 29)),
        "squirrel_sit": ([squirrel("sit", i / 4) for i in range(4)], 160, True, (16, 29)),
        "squirrel_dig": ([squirrel("dig", i / 4) for i in range(4)], 90, True, (16, 29)),
        "jay_fly": ([jay("fly", i / 4) for i in range(4)], 80, True, (12, 20)),
        "jay_perch": ([jay("perch", i / 4) for i in range(2)], 500, True, (12, 22)),
        "jay_hop": ([jay("hop", i / 4) for i in range(4)], 110, True, (12, 22)),
        "woolly": ([woolly(i / 6) for i in range(6)], 140, True, (12, 8)),
        "goose_walk": ([goose("walk", i / 4) for i in range(4)], 140, True, (16, 30)),
        "goose_honk": ([goose("honk", f) for f in (0.0, 0.3, 0.5, 0.8)], 110, False, (16, 30)),
        "goose_fly": ([goose("fly", i / 4) for i in range(4)], 110, True, (16, 22)),
        "goose_far": ([goose_far(i / 4) for i in range(4)], 140, True, (7, 5)),
        "frog_sit": ([frog("sit", f) for f in (0.0, 0.5, 1.0, 0.5)], 160, True, (9, 15)),
        "frog_hop": ([frog("hop", f) for f in (0.0, 0.35, 0.7, 1.0)], 90, True, (9, 15)),
        "turkey_run": ([turkey("run", i / 4) for i in range(4)], 70, True, (20, 38)),
        "turkey_stand": ([turkey("stand", i / 4) for i in range(2)], 600, True, (20, 38)),
        "turkey_look": ([turkey("look", f) for f in (0.0, 0.25, 0.25, 0.0, 0.0)], 260, True, (20, 38)),
        "turkey_gobble": ([turkey("gobble", f) for f in (0.0, 0.25, 0.5, 0.75, 1.0, 1.0)], 110, False, (20, 38)),
        "turkey_peck": ([turkey("peck", i / 4) for i in range(4)], 120, True, (20, 38)),
        "turkey_hen_run": ([turkey("run", i / 4, hen=True) for i in range(4)], 70, True, (20, 38)),
        "turkey_hen_stand": ([turkey("stand", i / 4, hen=True) for i in range(2)], 600, True, (20, 38)),
        "turkey_hen_look": ([turkey("look", f, hen=True) for f in (0.0, 0.25, 0.25, 0.0, 0.0)], 260, True, (20, 38)),
        "turkey_hen_call": ([turkey("call", f, hen=True) for f in (0.0, 0.25, 0.5, 0.75, 1.0)], 110, False, (20, 38)),
        "turkey_hen_peck": ([turkey("peck", i / 4, hen=True) for i in range(4)], 120, True, (20, 38)),
        "crow_fly": ([crow("fly", i / 4) for i in range(4)], 85, True, (12, 20)),
        "crow_carry": ([crow("fly", i / 4, acorn_in_beak=True) for i in range(4)], 85, True, (12, 20)),
        "crow_perch": ([crow("perch", i / 4) for i in range(2)], 600, True, (12, 22)),
        "crow_hop": ([crow("hop", i / 4) for i in range(4)], 100, True, (12, 22)),
        "crow_walk": ([crow("walk", i / 4) for i in range(4)], 140, True, (12, 22)),
        "crow_peck": ([crow("peck", i / 4) for i in range(4)], 110, True, (12, 22)),
        "crow_tilt": ([crow("tilt", i / 4) for i in range(2)], 500, True, (12, 22)),
        "crow_caw": ([crow("caw", f) for f in (0.0, 0.3, 0.6, 0.9)], 120, False, (12, 22)),
        "owl_perch": ([owl("perch", t) for t in (0, 0.2, 0.4, 0.6, 0.8, 0.9)], 500, True, (10, 21)),
        "owl_hoot": ([owl("hoot", t) for t in (0, 0.5)], 300, True, (10, 21)),
        "owl_turn": ([owl("turn")], 1000, False, (10, 21)),
        "owl_fly": ([owl("fly", i / 4) for i in range(4)], 90, True, (10, 13)),
        "firefly": ([firefly(True), firefly(False), firefly(False), firefly(True)], 260, True, (2, 2)),
        "inchworm": ([inchworm("crawl", t) for t in (0.0, 0.25, 0.5, 0.75)], 160, True, (7, 7)),
        "inchworm_fall": ([inchworm("fall")], 1000, False, (7, 6)),
        "butterfly": ([butterfly_flying(t) for t in (0.0, 0.25, 0.5, 0.75)], 70, True, (9, 8)),
        "junebug_crawl": ([beetle("junebug", "crawl", t) for t in (0.0, 0.25, 0.5, 0.75)], 120, True, (5, 11)),
        "junebug_fly": ([beetle("junebug", "fly", t) for t in (0.0, 0.25, 0.5, 0.75)], 50, True, (5, 11)),
        "ladybug_crawl": ([beetle("ladybug", "crawl", t) for t in (0.0, 0.25, 0.5, 0.75)], 120, True, (5, 11)),
        "ladybug_fly": ([beetle("ladybug", "fly", t) for t in (0.0, 0.25, 0.5, 0.75)], 50, True, (5, 11)),
        "cicada_sit": ([cicada("sit")], 1000, False, (5, 13)),
        "cicada_buzz": ([cicada("buzz", t) for t in (0.0, 0.125, 0.25, 0.375)], 40, True, (5, 13)),
        "cicada_fly": ([cicada_flying(t) for t in (0.0, 0.25, 0.5, 0.75)], 50, True, (8, 11)),
        "spider": ([spider(t) for t in (0.0, 0.25, 0.5, 0.75)], 140, True, (6, 2)),
        "silk": ([silk()], 1000, False, (0, 0)),
        **{f"butterfly_{kind}": ([butterfly_flying(t, kind) for t in (0.0, 0.25, 0.5, 0.75)], 70, True, (9, 8))
           for kind in ("white", "sulphur", "azure")},
        **{f"butterfly_{kind}_rest": ([butterfly(kind=kind, span=sp) for sp in (1.0, 0.8, 0.45, 0.3, 0.45, 0.8)], 260,
                                      True, (7, 10))
           for kind in BUTTERFLIES},
        **{f"{kind}_{pose}": ([songbird(kind, pose, i / n) for i in range(n)], ms, True, (10, 18))
           for kind in SONGBIRDS
           for pose, n, ms in (("perch", 2, 600), ("hop", 4, 90), ("fly", 4, 70), ("sing", 4, 140), ("peck", 4, 110))},
        "robin_worm": ([songbird("robin", "worm", i / 4) for i in range(4)], 160, True, (10, 18)),
        "crow_hat_fly": ([crow("fly", i / 4, hat=True) for i in range(4)], 85, True, (12, 20)),
        "crow_hat_perch": ([crow("perch", i / 4, hat=True) for i in range(2)], 600, True, (12, 22)),
        "crow_hat_hop": ([crow("hop", i / 4, hat=True) for i in range(4)], 100, True, (12, 22)),
        "crow_hat_walk": ([crow("walk", i / 4, hat=True) for i in range(4)], 140, True, (12, 22)),
        "crow_hat_peck": ([crow("peck", i / 4, hat=True) for i in range(4)], 110, True, (12, 22)),
        "crow_hat_tilt": ([crow("tilt", i / 4, hat=True) for i in range(2)], 500, True, (12, 22)),
        "crow_hat_caw": ([crow("caw", f, hat=True) for f in (0.0, 0.3, 0.6, 0.9)], 120, False, (12, 22)),
    }
