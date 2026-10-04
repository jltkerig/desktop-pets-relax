"""The fox, drawn from a pose. Faces right; the app mirrors it to face left. Frames are 64 x 64."""
import math

from pixelkit import Canvas, bezier, rot

SIZE = 64      # the fox is drawn in a 64 x 64 space...
ROOM = 10      # ...with this much extra room on the left for the tail to stream out behind
WIDTH = SIZE + ROOM
GROUND = 61    # paws rest on this row


def head(c, cx, cy, tilt=0.0, eyes="open", mouth=0.0, ear=0.0, ears_down=False, look=0.0):
    """Head centred at (cx, cy), facing right. tilt in degrees (positive = chin down)."""
    def p(x, y):
        return rot(cx + x, cy + y, cx, cy, tilt)

    # ears (far one first, a little darker); ear flick tips the near ear back
    lift = -3 if ears_down else 0
    far = [p(-5, -4), p(-3 - (2 if ears_down else 0), -13 - lift), p(0, -5)]
    c.polygon(far, "fur", lum=0.25, bias=-0.25)
    tip_far = [p(-3.6 - (2 if ears_down else 0), -10.5 - lift), p(-3 - (2 if ears_down else 0), -13 - lift), p(-2, -10.5 - lift)]
    c.polygon(tip_far, "dark", lum=0.3)
    flick = ear * 2.5
    near = [p(-1, -5), p(2.5 - flick - (3 if ears_down else 0), -14.5 - lift + abs(flick) * 0.4), p(5.5, -4.5)]
    c.polygon(near, "fur", lum=0.55)
    inner = [p(0.5, -5.5), p(2.6 - flick - (3 if ears_down else 0), -11.5 - lift), p(4, -5.2)]
    c.polygon(inner, "white", lum=0.15)
    tip = [p(1.6 - flick - (3 if ears_down else 0), -12 - lift), p(2.5 - flick - (3 if ears_down else 0), -14.5 - lift), p(3.6 - flick - (3 if ears_down else 0), -12 - lift)]
    c.polygon(tip, "dark", lum=0.4)

    # skull, cheek ruff, snout
    hx, hy = p(0, 0)
    c.ellipse(hx, hy, 6.8, 5.9, "fur", angle=tilt)
    ch = p(1.0, 3.6)
    c.ellipse(ch[0], ch[1], 5.2, 2.4, "white", angle=tilt - 8)
    s1, s2 = p(3.0, 1.0), p(12.5, 1.9)
    c.capsule(s1[0], s1[1], s2[0], s2[1], 3.4, 1.3, "fur")      # a long, tapering snout
    j1, j2 = p(3.5, 3.4), p(11.5, 3.0)
    c.capsule(j1[0], j1[1], j2[0], j2[1], 1.9, 0.8, "white")    # the white jaw underneath
    if mouth > 0:
        mx, my = p(7.0, 4.2 + mouth * 1.5)
        c.ellipse(mx, my, 3.6, 0.8 + mouth * 2.4, "mouth", angle=tilt + 4)
        tx, ty = p(6.6, 5.0 + mouth * 2.2)
        c.ellipse(tx, ty, 2.2, 0.7 + mouth * 0.9, "tongue", angle=tilt)
    nx, ny = p(13.2, 1.5)
    c.ellipse(nx, ny, 1.4, 1.2, "nose")
    c.pixel(nx - 0.6, ny - 0.8, "shine", 3)

    # eye (look shifts the pupil: -1 back, +1 forward)
    ex, ey = p(3.6 + look * 0.6, -1.2)
    ex, ey = round(ex), round(ey)
    if eyes == "open":
        for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            c.pixel(ex + dx, ey + dy, "eye")
        c.pixel(ex + (1 if look >= 0 else 0), ey, "shine", 3)
    elif eyes == "wide":
        for dx, dy in ((0, -1), (1, -1), (0, 0), (1, 0), (0, 1), (1, 1)):
            c.pixel(ex + dx, ey + dy, "eye")
        c.pixel(ex + 1, ey - 1, "shine", 3)
    elif eyes == "happy":  # ^ shape
        c.pixel(ex - 1, ey + 1, "eye")
        c.pixel(ex, ey, "eye")
        c.pixel(ex + 1, ey, "eye")
        c.pixel(ex + 2, ey + 1, "eye")
    else:  # closed: a soft line
        for dx in (-1, 0, 1, 2):
            c.pixel(ex + dx, ey + 1, "eye")


def neck(c, base, head_at, thick=1.0):
    """Joins the head to the body: a furry neck, with a soft white bib from the chest up to the jaw."""
    hx, hy = head_at
    bx, by = base
    c.capsule(bx, by, hx - 1.5, hy + 2.0, 4.2 * thick, 3.6 * thick, "fur")
    # the bib: one soft oval between the chest and the jaw (not a thin stripe)
    tx, ty = bx + 2.0 * thick, by + 1.5
    jx, jy = hx + 1.0, hy + 4.0
    mx, my = (tx + jx) / 2, (ty + jy) / 2
    length = math.hypot(jx - tx, jy - ty)
    angle = math.degrees(math.atan2(jy - ty, jx - tx)) + 90
    c.ellipse(mx, my, 2.9 * thick, max(2.5, length / 2 + 1.2), "white", angle=angle)


def leg(c, hip, paw, r_top=2.3, r_paw=1.7, far=False):
    bias = -0.28 if far else 0.0
    c.capsule(hip[0], hip[1], paw[0], paw[1], r_top, r_paw, "side", bias)
    # dark "socks" on the lower half
    mid = (hip[0] + (paw[0] - hip[0]) * 0.5, hip[1] + (paw[1] - hip[1]) * 0.5)
    c.capsule(mid[0], mid[1], paw[0], paw[1], r_paw + 0.25, r_paw, "dark", bias)


def tail(c, base, ctrl, tip, thick=4.3, far=False):
    """A brush-shaped tail: swells from the root to its fullest a little past the middle, then tapers
    steadily into a white tip that ends in a soft point."""
    n = 16
    pts = bezier(base, ctrl, tip, n)
    root, peak = 2.4 + thick * 0.35, 2.4 + thick
    radii = []
    for i in range(n):
        f = i / (n - 1)
        if f < 0.55:
            radii.append(root + (peak - root) * math.sin(math.pi / 2 * f / 0.55))
        else:
            radii.append(0.5 + (peak - 0.5) * (1 - ((f - 0.55) / 0.45) ** 1.5))
    mats = ["fur"] * 11 + ["tip"] * (n - 1 - 11)
    c.chain(pts, radii, mats, bias=-0.2 if far else 0.0)


def fox(pose="stand", **k):
    """Returns a 64 x 64 PIL image. See the pose functions below for the knobs each takes."""
    c = Canvas(WIDTH, SIZE, k.pop("palette", "orange"), shift=ROOM)
    POSES[pose](c, **k)
    return c.to_image(flat=True)


# -- poses -----------------------------------------------------------------------------------------

def stand(c, step=0.0, bob=0.0, tail_lift=0.0, swish=0.0, eyes="open", head_dx=0.0, head_dy=0.0, tilt=0.0,
          mouth=0.0, ear=0.0, stride=5.0, paw_lift=None, look=0.0, crouch=0.0):
    """step: walk cycle 0..1. crouch 0..1 lowers the body (pounce wind-up)."""
    y = 42 + bob + crouch * 6
    s = math.sin(step * 2 * math.pi)
    s2 = math.sin(step * 2 * math.pi + math.pi)

    def lift(phase):
        return max(0.0, math.sin(phase)) * 2.2 if stride else 0.0

    # far legs
    leg(c, (39, y + 3), (40 + stride * s2 * 0.6, GROUND - lift(step * 2 * math.pi + math.pi)), far=True)
    leg(c, (21, y + 3), (19 + stride * s * 0.6, GROUND - lift(step * 2 * math.pi)), far=True)
    # body
    c.ellipse(30, y, 15.0, 6.6 - crouch * 1.0, "fur", angle=-3 + crouch * 6)
    c.ellipse(41, y + 1.5, 4.2, 4.6, "white", angle=-10)
    c.ellipse(36, y + 4.5, 4.0, 1.8, "white", bias=-0.25, clip=lambda px, py: py >= y + 3.5)
    # tail: grows out of the rump, held out behind and a little up
    tail(c, (19, y - 1.5), (4, y - 2 - tail_lift * 4 + swish), (-8 + swish * 0.3, y - 7 - tail_lift * 7 + swish * 1.5),
         thick=3.8)
    # near legs
    leg(c, (24, y + 3), (23 + stride * s2 * 0.6, GROUND - lift(step * 2 * math.pi + math.pi)))
    if paw_lift is not None:  # one front paw reaching forward (batting)
        leg(c, (41, y + 2), (47 + paw_lift * 4, GROUND - 3 - paw_lift * 5), r_paw=2.3)
    else:
        leg(c, (41, y + 3), (43 + stride * s * 0.6, GROUND - lift(step * 2 * math.pi)))
    hx, hy = 47 + head_dx, y - 12 + head_dy + crouch * 3
    neck(c, (40, y - 3), (hx, hy))
    head(c, hx, hy, tilt=tilt, eyes=eyes, mouth=mouth, ear=ear, look=look)


def sit(c, eyes="open", tilt=0.0, mouth=0.0, ear=0.0, swish=0.0, head_dx=0.0, head_dy=0.0, look=0.0,
        scratch=None, breathe=0.0, ears_down=False, groom=None):
    """scratch: None, or 0..1 phase of the hind paw scratching behind the ear."""
    # haunch and body leaning back
    c.ellipse(28, 51, 8.6, 7.4 + breathe * 0.3, "fur")
    c.ellipse(32, 44, 7.4, 12.5 + breathe * 0.4, "fur", angle=-16)
    c.ellipse(37, 44, 3.8, 7.4, "white", angle=-12)
    if scratch is None:
        c.capsule(22, 59, 31, 59.5, 2.6, 2.3, "dark")  # hind paw on the ground
    # front legs
    leg(c, (38, 47), (38.5, GROUND), far=True)
    if groom is None:
        leg(c, (41, 47), (42, GROUND))
    else:  # paw up at the mouth, moving a little as it licks
        g = math.sin(groom * 2 * math.pi)
        leg(c, (41, 46), (45 + g, 36 + g), r_top=2.8, r_paw=2.3)
    # tail curled along the ground in front of the paws
    tail(c, (22, 57), (36 + swish, 64), (50 + swish * 1.5, 58 - abs(swish) * 0.5), thick=3.6)
    hx, hy = 40 + head_dx, 26 + head_dy - breathe * 0.4
    if scratch is not None:
        a = math.sin(scratch * 2 * math.pi) * 2.2
        leg(c, (27, 49), (35 + a, 33 + a * 0.6), r_top=3.0, r_paw=2.2)
    neck(c, (34, 38), (hx, hy), thick=1.25)  # sitting: a fuller neck flowing into the shoulders
    head(c, hx, hy, tilt=tilt, eyes=eyes, mouth=mouth, ear=ear, look=look, ears_down=ears_down)


def curl(c, breathe=0.0, eyes="closed", lift=0.0):
    """Asleep, curled up with the tail over the nose. lift raises the head (waking)."""
    c.ellipse(31, 54 - breathe * 0.4, 17.0, 7.2 + breathe * 0.5, "fur")
    c.ellipse(26, 56, 11, 3.2, "white", bias=-0.3, clip=lambda px, py: py >= 56)
    c.capsule(40, 59, 47, 59.5, 2.5, 2.2, "dark")  # tucked front paws
    head(c, 44, 50 - lift * 6, tilt=12 - lift * 14, eyes=eyes, ears_down=lift < 0.5)
    if lift < 0.5:
        tail(c, (14, 51), (22, 65), (51, 57), thick=5.0, far=True)  # over the nose


def held(c, swing=0.0, eyes="happy"):
    """Dangling while picked up."""
    tail(c, (31, 44), (30 + swing * 2, 54), (28 + swing * 4, 61), thick=4.2)
    leg(c, (27, 42), (26 + swing, 56), far=True)
    leg(c, (36, 42), (36 + swing, 56), far=True)
    c.ellipse(32, 36, 7.8, 12.5, "fur", angle=swing * 2)
    c.ellipse(35, 32, 4.5, 7.0, "white", angle=swing * 2)
    leg(c, (29, 30), (27 + swing, 41))
    leg(c, (37, 30), (38 + swing, 41))
    neck(c, (33, 27), (33, 16))
    head(c, 33, 16, tilt=8, eyes=eyes, ear=swing * 0.3)


def leap(c, rise=0.0, eyes="wide", reach=1.0):
    """In the air: body stretched, front paws reaching. rise lifts it (0..1)."""
    y = 40 - rise * 12
    leg(c, (20, y + 2), (11, y + 8), far=True)
    leg(c, (23, y + 2), (14, y + 10))
    c.ellipse(29, y, 16.0, 6.0, "fur", angle=-14 * reach)
    tail(c, (17, y + 1), (7, y + 3), (1, y - 2), thick=4.0)
    c.ellipse(38, y + 1, 3.6, 3.4, "white", angle=-20)
    leg(c, (39, y - 1), (50, y - 2 + 4 * (1 - reach)), far=True)
    leg(c, (41, y), (53, y + 3 * (1 - reach)))
    neck(c, (40, y - 2), (47, y - 10))
    head(c, 47, y - 10, tilt=-10 * reach, eyes=eyes)


def bow(c, wiggle=0.0, eyes="open", stretch=1.0, mouth=0.0):
    """Play bow / stretch: front low with paws forward, rear up, tail high."""
    leg(c, (20, 44), (18, GROUND), far=True)
    leg(c, (23, 44), (22 + wiggle * 0.3, GROUND))
    c.ellipse(29, 46, 14.5, 6.2, "fur", angle=16 * stretch)
    tail(c, (17, 42), (9 + wiggle, 32), (7 + wiggle * 1.6, 23), thick=4.2)
    c.ellipse(39, 51, 5.0, 4.0, "white", angle=10)
    c.capsule(38, 55, 52, 59.5, 2.8, 2.2, "fur", -0.28)
    c.capsule(46, 59, 52, 59.5, 2.6, 2.2, "dark", -0.28)
    c.capsule(40, 56, 55, 59.5, 2.8, 2.2, "fur")
    c.capsule(49, 59, 55, 59.5, 2.6, 2.2, "dark")
    neck(c, (39, 46), (47, 44 + (1 - stretch) * -4))
    head(c, 47, 44 + (1 - stretch) * -4, tilt=6, eyes=eyes, mouth=mouth)


def dig(c, phase=0.0):
    """Nose down, front paws scrabbling; dirt flies out behind."""
    a = math.sin(phase * 2 * math.pi)
    leg(c, (20, 44), (18, GROUND), far=True)
    leg(c, (23, 44), (22, GROUND))
    c.ellipse(30, 46, 14.5, 6.3, "fur", angle=14)
    tail(c, (18, 42), (9, 34), (6 + a, 27), thick=4.2)
    leg(c, (39, 50), (45 + a * 3, GROUND - max(0, a) * 3), far=True)
    leg(c, (41, 51), (46 - a * 3, GROUND - max(0, -a) * 3))
    neck(c, (40, 47), (49, 47))
    head(c, 49, 47, tilt=22, eyes="closed")
    for i, (dx, dy) in enumerate(((-30, -6), (-34, -10), (-27, -12), (-37, -4))):
        if (int(phase * 4) + i) % 2 == 0:
            c.ellipse(46 + dx - a * 2, GROUND + dy, 1.3, 1.1, "dirt")
    c.ellipse(48, GROUND + 1.5, 6, 1.6, "dirt")


def back(c, kick=0.0, eyes="happy"):
    """Rolling on its back, paws in the air, wriggling."""
    k = math.sin(kick * 2 * math.pi)
    tail(c, (16, 56), (8, 60), (2, 54 + k), thick=4.6)
    leg(c, (24, 52), (20 + k, 40), far=True)
    leg(c, (38, 52), (42 - k, 40), far=True)
    c.ellipse(31, 54, 14.5, 6.8, "fur", angle=k * 3)
    c.ellipse(32, 51, 10.0, 3.2, "white")
    leg(c, (27, 51), (25 - k, 41))
    leg(c, (36, 51), (38 + k, 41))
    head(c, 48, 52, tilt=-70 + k * 6, eyes=eyes)


def arc(c, angle=0.0, eyes="happy", tuck=1.0):
    """A mousing leap: the body tilted by angle (degrees; positive is nose up), front paws tucked to the
    chest, hind legs trailing, tail streaming behind."""
    cx, cy = 31, 34
    a = math.radians(-angle)

    def p(x, y):  # a point on the body, turned with it
        return cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)

    leg(c, p(-9, 3), p(-18, 8), far=True)
    leg(c, p(-7, 3), p(-16, 10))
    c.ellipse(cx, cy, 14.0, 6.0, "fur", angle=-angle)
    c.ellipse(*p(-1, 4.2), 7.0, 1.8, "white", angle=-angle, bias=-0.25)
    tail(c, p(-11, -1), p(-22, 1), p(-31, -4), thick=4.0)
    # front paws tucked up under the chin, like a cat's
    leg(c, p(8, 3), p(12 + 2 * (1 - tuck), 7 - 3 * tuck), far=True)
    leg(c, p(10, 3), p(14 + 2 * (1 - tuck), 6 - 3 * tuck))
    hx, hy = p(17, -6)
    neck(c, p(10, -2), (hx, hy))
    head(c, hx, hy, tilt=-angle, eyes=eyes, ear=0.4)


def dive(c, wiggle=0.0, puff=0.0):
    """Nose-first in the ground after a pounce: rump and tail up, tail wagging, a puff of leaves."""
    leg(c, (20, 40), (17, GROUND), far=True)
    leg(c, (23, 40), (22, GROUND))
    c.ellipse(31, 46, 14.0, 6.0, "fur", angle=40)
    tail(c, (21, 39), (14 + wiggle, 26), (12 + wiggle * 2.2, 15), thick=4.2)
    leg(c, (38, 52), (44, GROUND), far=True)
    leg(c, (40, 53), (46, GROUND))
    neck(c, (40, 52), (47, 58))
    head(c, 47, 60, tilt=70, eyes="closed")  # its face is buried; only the back of the head shows
    for y in range(GROUND + 1, 64):          # tuck what would show below the ground away
        for x in range(c.w):
            c.mat[y][x] = None
    for i, (dx, dy) in enumerate(((-6, -3), (5, -4), (-2, -7), (8, -1), (-9, -1))):
        if puff > i * 0.18:
            c.ellipse(48 + dx * (0.6 + puff * 0.6), GROUND + dy * (0.5 + puff), 1.2, 1.0,
                      ("dirt", "tip", "fur")[i % 3])


POSES = {"stand": stand, "sit": sit, "curl": curl, "held": held, "leap": leap, "bow": bow, "dig": dig, "back": back, "arc": arc, "dive": dive}


# -- animations: name -> (frames as pose kwargs, milliseconds per frame, loop) -----------------------

def _walk(stride, n):
    return [dict(pose="stand", step=i / n, bob=abs(math.sin(i / n * 2 * math.pi)) * -0.8, stride=stride,
                 swish=math.sin(i / n * 2 * math.pi) * 1.2) for i in range(n)]


ANIMATIONS = {
    "idle": ([dict(pose="sit", swish=s, eyes=e, ear=ear) for s, e, ear in
              ((0, "open", 0), (1, "open", 0), (2, "open", 0), (1, "open", 0), (0, "closed", 0), (-1, "open", 0),
               (-1, "open", 1), (0, "open", 0))], 220, True),
    "look": ([dict(pose="sit", look=l, head_dx=d, tilt=t) for l, d, t in
              ((0, 0, 0), (-1, -1, -4), (-1, -2, -6), (-1, -2, -6), (0, -1, -2), (1, 0, 2), (1, 1, 4), (1, 1, 4))],
             260, False),
    "walk": (_walk(5.0, 8), 110, True),
    "trot": (_walk(7.5, 6), 80, True),
    # zoomies: a flat-out sprint, long strides, ears back, tail streaming
    "run": ([dict(pose="stand", step=i / 6, bob=-abs(math.sin(i / 6 * 2 * math.pi)) * 2.2, stride=10.0,
                  swish=math.sin(i / 6 * 2 * math.pi) * 2.5, tail_lift=-0.4, ear=-0.8, eyes="happy", head_dx=1.5,
                  head_dy=2) for i in range(6)], 55, True),
    "stretch": ([dict(pose="bow", stretch=s, eyes=e, mouth=m) for s, e, m in
                 ((0.4, "open", 0), (0.7, "closed", 0), (1.0, "closed", 0.4), (1.0, "closed", 0.7), (1.0, "closed", 0.4),
                  (0.7, "open", 0))], 180, False),
    "yawn": ([dict(pose="sit", mouth=m, eyes="closed" if m > 0.3 else "open", tilt=-m * 14) for m in
              (0, 0.3, 0.7, 1.0, 1.0, 0.7, 0.3, 0)], 160, False),
    "scratch": ([dict(pose="sit", scratch=i / 6, eyes="happy", tilt=8, ear=-0.6) for i in range(6)] * 2, 70, False),
    "sleep": ([dict(pose="curl", breathe=b) for b in (0, 0.5, 1, 1, 0.5, 0)], 380, True),
    "wake": ([dict(pose="curl", eyes="wide", lift=0.2), dict(pose="curl", eyes="wide", lift=0.6),
              dict(pose="leap", rise=0.4, eyes="wide", reach=0.2), dict(pose="sit", eyes="wide", head_dy=-1),
              dict(pose="sit", eyes="happy"), dict(pose="sit", eyes="happy", tilt=6)], 140, False),
    "tilt": ([dict(pose="sit", tilt=t, ear=e) for t, e in ((0, 0), (8, 0.4), (14, 0.6), (14, 0.6), (8, 0.3), (0, 0))],
             160, False),
    "petted": ([dict(pose="sit", eyes="happy", tilt=t, swish=s, ears_down=True) for t, s in
                ((4, -2), (8, 0), (4, 2), (0, 0), (4, -2), (8, 0))], 130, True),
    "held": ([dict(pose="held", swing=s) for s in (0, 1, 2, 1, 0, -1, -2, -1)], 120, True),
    "land": ([dict(pose="bow", stretch=0.3, eyes="wide"), dict(pose="stand", crouch=0.6, eyes="open", stride=0),
              dict(pose="stand", crouch=0.2, eyes="happy", stride=0), dict(pose="sit", eyes="happy")], 110, False),
    "crouch": ([dict(pose="stand", crouch=1.0, stride=0, eyes="wide", swish=w, head_dx=1, step=st) for w, st in
                ((-3, 0.0), (3, 0.06), (-3, 0.0), (3, 0.94))], 100, True),
    "pounce": ([dict(pose="arc", angle=a, eyes=e, tuck=t) for a, e, t in
                ((38, "wide", 0.3), (26, "wide", 0.7), (10, "happy", 1.0), (-12, "happy", 1.0), (-34, "wide", 0.8),
                 (-52, "wide", 0.5))], 85, False),
    # landing nose-first in the leaves, rump up, tail wagging, then a happy pop back out
    "dive": ([dict(pose="dive", wiggle=w, puff=p) for w, p in ((0, 0.3), (2, 0.7), (-2, 1.0), (2, 1.0), (-2, 0.8),
                                                              (0, 0.5))], 120, False),
    "dig": ([dict(pose="dig", phase=i / 4) for i in range(4)], 90, True),
    "bat": ([dict(pose="stand", stride=0, crouch=0.4, paw_lift=p, eyes=e) for p, e in
             ((0, "open"), (0.5, "wide"), (1, "wide"), (0.4, "open"), (0, "happy"))], 110, False),
    "watch": ([dict(pose="sit", swish=s, look=1, head_dx=1, ear=e) for s, e in
               ((0, 0), (1, 0), (2, -0.3), (1, 0), (0, 0), (-1, 0))], 240, True),
    "happy": ([dict(pose="sit", eyes="happy", swish=s, head_dy=d) for s, d in ((0, 0), (2, -1), (0, -2), (-2, -1))],
              120, True),
    # invented extras
    "sniff": ([dict(pose="stand", stride=0, head_dy=d, tilt=18, eyes=e, swish=s) for d, e, s in
               ((7, "open", 0), (8, "closed", 1), (7, "open", 0), (8, "closed", -1), (7, "open", 0), (6, "open", 0))],
              150, False),
    "playbow": ([dict(pose="bow", wiggle=w, eyes="happy", stretch=0.8) for w in (-3, 0, 3, 0)], 110, True),
    "roll": ([dict(pose="back", kick=i / 6) for i in range(6)], 120, True),
    "hop": ([dict(pose="stand", crouch=0.6, stride=0, eyes="happy"), dict(pose="leap", rise=0.3, eyes="happy", reach=0.3),
             dict(pose="leap", rise=0.5, eyes="happy", reach=0.2), dict(pose="leap", rise=0.2, eyes="happy", reach=0.3),
             dict(pose="stand", crouch=0.4, stride=0, eyes="happy")], 90, False),
    "boop": ([dict(pose="stand", stride=0, head_dx=d, eyes=e, tilt=4) for d, e in
              ((0, "open"), (2, "open"), (4, "closed"), (4, "happy"), (2, "happy"), (0, "happy"))], 140, False),
    "groom": ([dict(pose="sit", groom=i / 6, eyes="closed", tilt=24 + (i % 2) * 4, mouth=0.25 if i % 2 else 0.0,
                    head_dy=3) for i in range(6)], 150, True),
}
