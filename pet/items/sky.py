"""Night and weather: glows, fireflies, paw prints in the snow, raindrops and snowflakes."""
import math

from pet.things import Thing


class Glow(Thing):
    """A soft glow of light behind something lit up at night (a jack-o'-lantern, the Christmas tree's lights, a
    firefly), following it about and fading in and out with the dark."""
    kind = "glow"
    z = 29

    def __init__(self, world, holder, sprite, dy=None):
        super().__init__(world, holder.x, holder.y, sprite)
        self.holder, self.dy = holder, dy  # dy: how far up its middle is (None: halfway up the holder)
        self.z = holder.z - 0.5  # a halo behind it, not a veil over it
        self.alpha = 0.0
        self.fading = False
        self.anim.time = getattr(holder.anim, "time", 0.0)

    def update(self, dt):
        super().update(dt)
        h = self.holder
        if self.dy is None:
            _, top, _, height = h.rect()
            self.x, self.y = h.x, top + height / 2
        else:
            self.x, self.y = h.x, h.y - self.dy * self.world.scale
        if h.gone or self.fading:
            self.alpha -= dt / 1.5
            if self.alpha <= 0:
                self.gone = True
        else:
            self.alpha = min(1.0, self.alpha + dt / 1.5)


class Firefly(Thing):
    """A firefly on a summer night, drifting slowly over the grass and blinking its light on and off."""
    kind = "firefly"
    z = 30

    def __init__(self, world):
        rng, s = world.rng, world.scale
        super().__init__(world, rng.uniform(20, world.width - 20), world.ground - rng.uniform(15, 90) * s, "firefly")
        self.anim.time = rng.uniform(0, 2)
        self.home_y = self.y
        self.vx = rng.uniform(-10, 10)
        self.phase = rng.uniform(0, 6.3)
        self.leaving = False
        self.alpha = 0.0
        self.glow = world.add(Glow(world, self, "glow_firefly"))
        self.glow.anim.time = self.anim.time  # blinking together

    def update(self, dt):
        super().update(dt)
        s = self.world.scale
        self.phase += dt * 0.9
        if self.world.rng.random() < dt * 0.3:
            self.vx = self.world.rng.uniform(-12, 12)
        self.x = self.world.clamp_x(self.x + self.vx * s * dt, 10.0)
        self.y = self.home_y + math.sin(self.phase) * 14 * s
        if self.leaving:
            self.alpha -= dt / 2
            if self.alpha <= 0:
                self.gone = True
        else:
            self.alpha = min(1.0, self.alpha + dt / 2)


class PawPrint(Thing):
    """A fox's paw print in the snow, slowly filling in again."""
    kind = "print"
    z = 2

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "pawprint")
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.alpha = max(0.0, 1.0 - self.age / 40)
        if self.age > 40 or not self.world.snowed_over:
            self.gone = True


class RainDrop(Thing):
    """A drop of rain, slanting down with the wind, that splashes when it hits the ground."""
    kind = "rain"
    z = 36

    def __init__(self, world):
        rng, s = world.rng, world.scale
        lean = world.wind * world.wind_dir
        super().__init__(world, rng.uniform(-60, world.width + 60) - lean * 120 * s, -rng.uniform(4, 60) * s,
                         "raindrop")
        self.ground = world.ground - rng.uniform(0, 4) * s  # some land a little nearer, some a little further
        self.vy = rng.uniform(330, 400) * s
        self.vx = (lean * 150 + 12) * s
        self.alpha = rng.uniform(0.5, 0.85)

    def update(self, dt):
        super().update(dt)
        if self.anim.name == "rain_splash":
            if self.anim.done:
                self.gone = True
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y >= self.ground:
            self.y = self.ground
            self.anim.play("rain_splash")


class SnowFlake(Thing):
    """A snowflake drifting down, swaying (and blown along when it's windy), that settles and melts away."""
    kind = "snowflake"
    z = 36

    def __init__(self, world):
        rng, s = world.rng, world.scale
        super().__init__(world, rng.uniform(-80, world.width + 80), -rng.uniform(4, 60) * s,
                         rng.choice(("snowflake", "snowflake", "snowflake_big")))
        self.ground = world.ground - rng.uniform(0, 3) * s
        self.vy = rng.uniform(22, 40) * s
        self.phase = rng.uniform(0, 6.3)
        self.sway = rng.uniform(6, 14) * s
        self.settled = 0.0

    def update(self, dt):
        super().update(dt)
        w, s = self.world, self.world.scale
        if self.settled:
            self.settled += dt
            self.alpha = max(0.0, 1 - self.settled / 3)
            if self.settled >= 3:
                self.gone = True
            return
        self.phase += dt * 1.6
        self.x += (math.cos(self.phase) * self.sway * 1.6 + w.wind * w.wind_dir * 140 * s) * dt
        self.y += self.vy * dt
        if self.y >= self.ground:
            self.y = self.ground
            self.settled = 1e-6
