"""What every visitor shares: Visitor (walking, flying in), speech bubbles, and perches (spots to sit on)."""
import math

from pet.things import Thing


class Visitor(Thing):
    z = 22

    def leave_x(self):
        """The nearer screen edge, just off screen."""
        return -40.0 if self.x < self.world.width / 2 else self.world.width + 40.0

    def move_to(self, x, speed, dt):
        """Step toward x; True once there."""
        distance = x - self.x
        if abs(distance) > 1:
            self.facing = 1 if distance > 0 else -1
        move = speed * self.world.scale * dt
        if abs(distance) <= move:
            self.x = x
            return True
        self.x += move if distance > 0 else -move
        return False

    def fly_to(self, x, y, dt, speed=110):
        """Fly straight toward (x, y); True once there."""
        dx, dy = x - self.x, y - self.y
        dist = math.hypot(dx, dy)
        step = speed * self.world.scale * dt
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        if dist <= step:
            self.x, self.y = x, y
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False


class Bubble(Thing):
    """A HONK! speech bubble over a goose for a moment."""
    kind = "bubble"
    z = 40

    def __init__(self, world, goose, sprite="honk_bubble", rise=30):
        super().__init__(world, goose.x, goose.y, sprite)
        self.goose = goose
        self.rise = rise
        self.life = 1.1

    def update(self, dt):
        s = self.world.scale
        self.x = self.goose.x + self.goose.facing * 8 * s
        self.y = self.goose.y - self.rise * s
        self.life -= dt
        if self.life <= 0 or self.goose.gone:
            self.gone = True


class Perch:
    """Somewhere a crow can sit: a spot on something (sideways from its middle and up from its base, in
    sprite pixels, so it moves along when the thing is dragged), or a spot on the ground."""

    def __init__(self, holder=None, dx=0.0, dy=0.0, x=0.0):
        self.holder, self.dx, self.dy, self.x = holder, dx, dy, x

    @property
    def high(self):
        return self.holder is not None

    def pos(self, world):
        if self.holder is None:
            return self.x, world.ground
        s = world.scale
        return self.holder.x + self.dx * s, self.holder.y - self.dy * s

    def ok(self):
        """Still there to sit on (not taken away, knocked over or wilting)."""
        h = self.holder
        return h is None or (not h.gone and h.alpha >= 1 and getattr(h, "available", True) and
                             not getattr(h, "wilting", False) and not getattr(h, "bursting", False))


class HeadPerch(Perch):
    """The top of the scarecrow's head: on his hat, or (once a crow has pinched it) on the straw."""

    def __init__(self, scarecrow):
        super().__init__(scarecrow, 0, 0)

    def pos(self, world):
        self.dy = 72 if self.holder.hat_on else 66
        return super().pos(world)


# -- small creatures on the oak, through the year -------------------------------------------------------

GRAVITY = 700  # sprite pixels per second squared (scaled), as for acorns
