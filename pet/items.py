"""The oak tree, the leaves it drops and its acorns."""
import math

from pet.things import Thing

GRAVITY = 700  # sprite pixels per second squared (scaled)


class Tree(Thing):
    kind = "tree"
    draggable = True
    z = 5

    def __init__(self, world, x, variant="oak"):
        super().__init__(world, x, world.ground, variant)
        self.variant = variant

    def crown_point(self):
        """A random spot in the crown, for leaves and acorns to start from."""
        s, rng = self.world.scale, self.world.rng
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.2, 0.9)
        return self.x + math.cos(a) * r * 58 * s, self.y - (127 - math.sin(a) * r * 40) * s

    def perch_points(self):
        """Branch spots where a bird can sit (screen coordinates of its feet)."""
        s = self.world.scale
        return [(self.x - 40 * s, self.y - 100 * s), (self.x + 32 * s, self.y - 102 * s),
                (self.x - 6 * s, self.y - 120 * s)]

    def base_range(self):
        """Where under the tree a fox can nap (between the roots and the crown's edge)."""
        s = self.world.scale
        return self.x - 50 * s, self.x + 50 * s


class Leaf(Thing):
    kind = "leaf"
    z = 30

    def __init__(self, world, x, y, colour):
        super().__init__(world, x, y, f"leaf_{colour}")
        rng = world.rng
        self.anim.time = rng.uniform(0, 1)
        self.fall = rng.uniform(16, 30)       # sprite pixels per second
        self.sway = rng.uniform(8, 18)
        self.phase = rng.uniform(0, 2 * math.pi)
        self.landed_for = None
        self.rest = rng.uniform(25, 45)       # seconds on the ground before fading

    @property
    def falling(self):
        return self.landed_for is None

    def update(self, dt):
        s = self.world.scale
        if self.falling:
            super().update(dt)
            self.phase += dt * 2.2
            self.x += math.cos(self.phase) * self.sway * s * dt
            self.y += self.fall * s * dt
            if self.y >= self.world.ground - 1:
                self.y = self.world.ground - 1
                self.landed_for = 0.0
        else:
            self.landed_for += dt
            if self.landed_for > self.rest:
                self.alpha -= dt / 3
                if self.alpha <= 0:
                    self.gone = True

    def landing_x(self):
        """Roughly where it will come down (for a fox lining up a pounce)."""
        return self.x


class Acorn(Thing):
    kind = "acorn"
    z = 25

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "acorn")
        self.vx = 0.0
        self.vy = 0.0
        self.bounced = False
        self.on_ground = False
        self.taken = False  # a squirrel has claimed it

    def update(self, dt):
        s = self.world.scale
        if abs(self.vx) > 1:  # it only turns over while rolling
            self.anim.update(dt)
        if not self.on_ground:
            self.vy += GRAVITY * s * dt
            self.x += self.vx * dt
            self.y += self.vy * dt
            fox = self.world.sleeping_fox_under(self)
            if fox is not None and self.vy > 0:
                fox.bonk()
                self.vy = -self.vy * 0.35
                self.vx = (1 if self.x >= fox.x else -1) * 60 * s
                self.y = min(self.y, fox.rect()[1])
            if self.y >= self.world.ground:
                self.y = self.world.ground
                if not self.bounced and self.vy > 120 * s:
                    self.vy = -self.vy * 0.3
                    self.bounced = True
                else:
                    self.vy = 0.0
                    self.on_ground = True
        else:
            self.x += self.vx * dt
            self.vx *= max(0.0, 1 - 2.5 * dt)  # rolls to a stop
            if abs(self.vx) < 2:
                self.vx = 0.0
        if self.x < 6 or self.x > self.world.width - 6:
            self.vx = -self.vx * 0.5
            self.x = max(6.0, min(self.world.width - 6.0, self.x))


class Mound(Thing):
    """A little heap of dirt where a squirrel buried an acorn. Fades after a while."""
    kind = "mound"
    z = 4

    def __init__(self, world, x):
        super().__init__(world, x, world.ground, "dirt_mound")
        self.age = 0.0

    def update(self, dt):
        super().update(dt)
        self.age += dt
        if self.age > 40:
            self.alpha -= dt / 4
            if self.alpha <= 0:
                self.gone = True
