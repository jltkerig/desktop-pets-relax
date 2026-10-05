"""Small things that fall, roll, fly off or drift about: acorns, leaves, twigs, snow clumps, crumbs,
straw, kernels, pumpkin bits, water drops and seed fluff."""
import math

from pet import sprites
from pet.things import Thing


GRAVITY = 700  # sprite pixels per second squared (scaled)


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
        w = self.world
        s = w.scale
        blow = w.wind * w.wind_dir
        if self.falling:
            super().update(dt * (1 + w.wind * 2))  # tumbles faster in the wind
            self.phase += dt * (2.2 + w.wind * 3)
            self.x += (math.cos(self.phase) * self.sway + blow * 150) * s * dt
            self.y += (self.fall - w.wind * 6 * math.sin(self.phase * 1.7)) * s * dt
            if self.y >= w.ground - 1:
                self.y = w.ground - 1
                self.landed_for = 0.0
            if self.x < -40 or self.x > w.width + 40:
                self.gone = True  # blown away off the screen
        else:
            if w.wind > 0.55 and w.rng.random() < dt * w.wind * 1.2:
                self.landed_for = None             # a gust picks it up again
                self.y -= 6 * s
                self.alpha = 1.0
                return
            self.landed_for += dt
            if self.landed_for > self.rest:
                self.alpha -= dt / 3
                if self.alpha <= 0:
                    self.gone = True

    def landing_x(self):
        """Roughly where it will come down (for a fox lining up a pounce)."""
        return self.x


class Twig(Thing):
    """A dead branch knocked off the winter oak: it tumbles down, lies there a while, and fades away."""
    kind = "twig"
    z = 30

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "twig")
        self.vy = 0.0
        self.vx = world.rng.uniform(-20, 20)
        self.landed_for = None
        self.rest = world.rng.uniform(15, 25)

    def update(self, dt):
        w, s = self.world, self.world.scale
        if self.landed_for is None:
            super().update(dt)  # turning over as it falls
            self.vy = min(self.vy + GRAVITY * 0.6 * s * dt, 260 * s)
            self.x += self.vx * s * dt
            self.y += self.vy * dt
            if self.y >= w.ground:
                self.y, self.landed_for = w.ground, 0.0
                self.anim.time = 0.0  # it settles lying flat
        else:
            self.landed_for += dt
            if self.landed_for > self.rest:
                self.alpha -= dt / 3
                if self.alpha <= 0:
                    self.gone = True


class SnowClump(Thing):
    """A clump of snow shaken off the oak's branches: it drops, lands with a puff, and melts away."""
    kind = "snow"
    z = 31

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "snow_clump")
        self.vy = world.rng.uniform(-20, 10)
        self.landed_for = None
        self.delay = world.rng.uniform(0, 0.5)  # not all at once

    def update(self, dt):
        w, s = self.world, self.world.scale
        super().update(dt)
        if self.delay > 0:
            self.delay -= dt
            return
        if self.landed_for is None:
            self.vy += GRAVITY * s * dt
            self.y += self.vy * dt
            if self.y >= w.ground:
                self.y, self.landed_for = w.ground, 0.0
                self.anim.play("snow_puff")
        else:
            self.landed_for += dt
            if self.landed_for > 4:
                self.alpha -= dt / 2
                if self.alpha <= 0:
                    self.gone = True


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


class StrawBit(Thing):
    """A wisp of straw puffing out of a haystack being rebuilt."""
    kind = "straw"
    z = 34

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "straw_bit")
        rng = world.rng
        self.vx = rng.uniform(-90, 90)
        self.vy = rng.uniform(-200, -90)
        self.age = 0.0
        self.anim.time = rng.uniform(0, 1)

    def update(self, dt):
        super().update(dt)
        s = self.world.scale
        self.age += dt
        self.vy += 300 * dt
        self.x += self.vx * s / 2 * dt
        self.y = min(self.world.ground, self.y + self.vy * s / 2 * dt)
        self.alpha = max(0.0, 1 - self.age / 1.6)
        if self.age > 1.6:
            self.gone = True


class Kernel(StrawBit):
    """A kernel of corn pecked off a cob by a crow (or a bit of apple, tomato or lettuce: sprite)."""
    kind = "crumb"

    def __init__(self, world, x, y, sprite="kernel"):
        super().__init__(world, x, y)
        self.anim = sprites.Anim(sprite)
        self.vx *= 0.4
        self.vy *= 0.5


class Droplet(StrawBit):
    """A drop of water splashed out of the kiddie pool (or the well)."""
    kind = "drop"

    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.anim = sprites.Anim("droplet")


class Fluff(Thing):
    """A seed on its tuft of fluff (a dandelion's or a cattail's), drifting off on the wind: it floats up and
    away, bobbing, carried by the breeze (and much faster in a gale), then it's gone."""
    kind = "fluff"
    z = 33

    def __init__(self, world, x, y, sprite="fluff"):
        super().__init__(world, x, y, sprite)
        rng = world.rng
        self.anim.time = rng.uniform(0, 1)
        self.vx = rng.uniform(-14, 14)
        self.vy = rng.uniform(-22, -8)
        self.phase = rng.uniform(0, 6.3)
        self.life = rng.uniform(8, 16)
        self.age = 0.0

    def update(self, dt):
        super().update(dt)
        w, s = self.world, self.world.scale
        self.age += dt
        self.phase += dt * 2
        drift = 18 + w.wind * 160  # a light breeze always, more when it's blustery
        self.x += (self.vx + drift * w.wind_dir + math.sin(self.phase) * 10) * s * dt
        self.y += (self.vy + math.cos(self.phase * 1.3) * 8) * s * dt
        self.vy = min(4.0, self.vy + 2 * dt)  # rising at first, then drifting level, sinking a little
        self.alpha = max(0.0, min(1.0, (self.life - self.age) / 2))
        if self.age > self.life or self.x < -20 or self.x > w.width + 20 or self.y < -20:
            self.gone = True


class PumpkinBit(StrawBit):
    """A chunk of pumpkin flying off: carved out by the hoe, or from a giant splitting open."""
    kind = "crumb"

    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.anim = sprites.Anim("pumpkin_bit")


class Crumb(StrawBit):
    """A chewed-off bit of a dug-up icon, flying off and fading."""
    kind = "crumb"

    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.anim = sprites.Anim("crumb")
        self.vx *= 0.6
        self.vy *= 0.6
