"""Summer things: the sprinkler, the beach ball, the hammock (and its near edge, drawn in front of a fox lying in
it), the jar the foxes put fireflies in, and the sunflowers that turn to follow the sun."""
from pet import sky, sprites
from pet.things import Thing
from .play import Ball, YardThing
from .sky import Firefly


class Sprinkler(YardThing):
    """A garden sprinkler, swinging its fan of water from side to side. Foxes dash through it and shake
    themselves off. Click it to turn it off (or on)."""
    z = 9
    REACH = 40  # how far its water lands either side, in sprite pixels

    def __init__(self, world, x, variant="sprinkler"):
        self.on = True
        super().__init__(world, x, variant)

    @property
    def look(self):
        return "sprinkler" if self.on else "sprinkler_off"

    def contains(self, px, py):
        """Only the sprinkler itself (on the ground), not the spray, can be clicked or dragged."""
        s = self.world.scale
        return abs(px - self.x) <= 12 * s and self.y - 10 * s <= py <= self.y + 2 * s

    def click(self):
        self.on = not self.on


class BeachBall(Ball):
    """A big, light, bouncy beach ball. Throw it and a fox chases it and noses it back up into the air. It
    floats on the water in the kiddie pool."""
    GRAVITY = 650
    BOUNCE = 0.8
    TOP_SPEED = 1900

    def __init__(self, world, x):
        super().__init__(world, x, world.ground, "beachball_still")

    def pool(self):
        s = self.world.scale
        return next((p for p in self.world.of("prop") if p.variant == "pool" and abs(p.x - self.x) < 22 * s), None)

    def floor(self):
        pool = self.pool()
        return pool.y - 4 * self.world.scale if pool is not None else self.world.ground

    @property
    def floating(self):
        return self.pool() is not None and not self.moving

    def update(self, dt):
        name = "beachball" if self.moving else "beachball_still"
        if self.anim.name != name:
            self.anim.play(name)
        super().update(dt)


class Hammock(YardThing):
    """A striped hammock between two posts. On a summer day a sleepy fox climbs in for a nap (its near edge is a
    separate thing, HammockFront, drawn in front of the fox so it lies down inside). It sways gently."""
    z = 7

    def __init__(self, world, x, variant="hammock"):
        super().__init__(world, x, variant)
        self.front = world.add(HammockFront(world, self))

    def bed(self):
        """Where a fox lies in it (x, the y of its paws)."""
        return self.x, self.y - 7 * self.world.scale

    def occupant(self):
        s = self.world.scale
        return next((f for f in self.world.of("fox") if f.up_high and abs(f.x - self.x) < 12 * s), None)

    def update(self, dt):
        super().update(dt)
        self.anim.update(dt * self.world.wind * 2)  # it swings more in the wind


class HammockFront(Thing):
    """The near edge of the hammock, drawn in front of a fox napping in it. Never clicked: it's part of the
    hammock."""
    kind = "hammock_front"
    z = 21

    def __init__(self, world, hammock):
        super().__init__(world, hammock.x, hammock.y, "hammock_front")
        self.hammock = hammock

    def contains(self, px, py):
        return False

    def update(self, dt):
        h = self.hammock
        if h.gone:
            self.gone = True
            return
        self.x, self.y, self.alpha = h.x, h.y, h.alpha
        self.anim.time = h.anim.time


class FireflyJar(YardThing):
    """A jar for fireflies, out on summer nights. A fox that catches a firefly may pop it in (up to four),
    and they blink away inside, glowing. Click the jar to let them all go; at dawn they go by themselves."""
    z = 8
    HOLDS = 4

    def __init__(self, world, x, variant="firefly_jar"):
        self.count = 0
        super().__init__(world, x, variant)

    @property
    def look(self):
        return f"firefly_jar_{min(self.count, self.HOLDS)}"

    @property
    def full(self):
        return self.count >= self.HOLDS

    def add_firefly(self):
        self.count = min(self.HOLDS, self.count + 1)

    def release(self):
        """Open the lid: out they fly, blinking."""
        w, s = self.world, self.world.scale
        for _ in range(self.count):
            fly = w.add(Firefly(w))
            fly.x, fly.y = self.x + w.rng.uniform(-6, 6) * s, self.y - 14 * s
            fly.home_y = self.y - w.rng.uniform(30, 80) * s
            fly.alpha = 1.0
            fly.leaving = not w.dark  # by day they head off home
        self.count = 0

    def click(self):
        self.release()

    def update(self, dt):
        if self.count and not self.world.dark:
            self.release()
        super().update(dt)


class Sunflowers(YardThing):
    """Three tall sunflowers whose heads turn to follow the sun across the sky through the day (by the same
    clock as the sun in the sky: up at 6 AM on the left, down at 6 PM on the right). At night they hang their
    heads. Butterflies land on them; click them and they rustle."""
    z = 6

    def __init__(self, world, x, variant="sunflowers"):
        self._looked = None  # (minute, look): worked out once a minute
        super().__init__(world, x, variant)

    @property
    def look(self):
        w = self.world
        minute = w.now().replace(second=0, microsecond=0)
        key = (minute, round(self.x / (w.width * 0.05)))
        if self._looked is None or self._looked[0] != key:
            body, across, _, _, _ = sky.placement(w.now())
            if body != "sun":
                face = "night"
            else:  # toward where the sun is, along all the monitors
                lean = (across * w.width - self.x) / (w.width * 0.15)
                face = max(0, min(4, int(round(2 + lean))))
            self._looked = (key, f"sunflowers_{face}")
        return self._looked[1]

    def flower_heads(self):
        """Where its flower heads are (screen coordinates), for butterflies to land on."""
        m = sprites.meta(self.anim.name)
        ax, ay = m["anchor"]
        s = self.world.scale
        return [(self.x + (px - ax) * s, self.y - (ay - py) * s) for px, py in m.get("perches", [])]

    def react(self, name="wobble"):
        self.anim.time += 0.9  # a rustle

    def update(self, dt):
        super().update(dt * (1 + self.world.wind * 4))
