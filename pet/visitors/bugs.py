"""Bugs on and around the oak: the inchworm, the butterfly from the summer oak, June beetles and ladybugs,
the cicada, the autumn spider on its thread."""
import math

from pet.things import Thing
from .base import Bubble, GRAVITY, Visitor


class Inchworm(Visitor):
    """A spring caterpillar shaken out of the oak: it drops, lands, and loops off as fast as it can."""
    kind = "inchworm"
    z = 24
    SPEED = 28

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "inchworm_fall")
        self.vy = 0.0
        self.state = "fall"

    def update(self, dt):
        super().update(dt)
        w = self.world
        if self.state == "fall":
            self.vy += GRAVITY * 0.7 * w.scale * dt
            self.y = min(w.ground, self.y + self.vy * dt)
            if self.y >= w.ground:
                self.state = "run"
                self.anim.play("inchworm")
        elif self.move_to(self.leave_x(), self.SPEED, dt):
            self.gone = True


class Butterfly(Visitor):
    """A butterfly that was resting in the summer oak: shaken out, it flutters up and away."""
    kind = "butterfly"
    z = 32

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "butterfly")
        rng = world.rng
        self.dir = rng.choice((-1, 1))
        self.phase = rng.uniform(0, 6.3)
        self.anim.time = rng.uniform(0, 1)

    def update(self, dt):
        super().update(dt)
        s = self.world.scale
        self.phase += dt * 5
        self.x += (self.dir * 45 + math.sin(self.phase * 0.7) * 30) * s * dt  # a wandering, fluttery path
        self.y += (-22 + math.sin(self.phase) * 40) * s * dt
        if self.x < -30 or self.x > self.world.width + 30 or self.y < -30:
            self.gone = True


class Beetle(Visitor):
    """A June beetle or a ladybug that climbs the summer oak's trunk, stops, then opens its wings and flies off."""
    kind = "beetle"
    z = 24
    CLIMB = 9  # sprite pixels a second

    def __init__(self, world, tree, species):
        rng = world.rng
        self.species = species  # "junebug" or "ladybug"
        super().__init__(world, tree.x + rng.uniform(-5, 5) * world.scale, world.ground, f"{species}_crawl")
        self.tree = tree
        self.offset = self.x - tree.x
        self.top = rng.uniform(80, 98)  # how high up the trunk it gets (sprite pixels)
        self.state = "climb"
        self.timer = 0.0
        self.rest_at = rng.uniform(25, 60)  # it stops for a breather on the way up
        self.dir = rng.choice((-1, 1))

    def update(self, dt):
        w, s, rng = self.world, self.world.scale, self.world.rng
        self.timer += dt
        if self.tree.gone and self.state != "fly":
            self.state = "fly"
            self.anim.play(f"{self.species}_fly")
        if self.state == "climb":
            super().update(dt)
            self.x = self.tree.x + self.offset  # stays on the trunk if the oak is dragged
            height = (w.ground - self.y) / s
            if self.rest_at and height > self.rest_at:
                self.rest_at, self.state, self.timer = None, "rest", 0.0
            elif height >= self.top:
                self.state, self.timer = "ready", 0.0
            else:
                self.y -= self.CLIMB * s * dt
        elif self.state == "rest":
            self.x = self.tree.x + self.offset
            if self.timer > rng.uniform(1.5, 3):
                self.state = "climb"
        elif self.state == "ready":
            self.x = self.tree.x + self.offset
            if self.timer > 1.2:
                self.state = "fly"
                self.anim.play(f"{self.species}_fly")
        else:  # away it goes, buzzing up and out
            super().update(dt)
            self.x += self.dir * 60 * s * dt
            self.y -= (40 + math.sin(self.timer * 9) * 25) * s * dt
            if self.x < -30 or self.x > w.width + 30 or self.y < -30:
                self.gone = True


class Cicada(Visitor):
    """An autumn cicada: it flies in, lands on the oak's trunk, buzzes loudly a few times, and flies off."""
    kind = "cicada"
    z = 24

    def __init__(self, world, tree):
        rng = world.rng
        start = rng.choice((-30.0, world.width + 30.0))
        super().__init__(world, start, world.ground - rng.uniform(150, 250) * world.scale, "cicada_fly")
        self.tree = tree
        self.offset = rng.uniform(-4, 4) * world.scale
        self.height = rng.uniform(40, 80)  # where on the trunk it lands (sprite pixels up)
        self.state = "arrive"
        self.timer = 0.0
        self.buzzes = rng.randint(3, 5)
        self.exit = (rng.choice((-40.0, world.width + 40.0)), world.ground - 300 * world.scale)

    def spot(self):
        return self.tree.x + self.offset, self.world.ground - self.height * self.world.scale

    def update(self, dt):
        super().update(dt)
        w, rng = self.world, self.world.rng
        self.timer += dt
        if self.tree.gone and self.state != "leave":
            self.state = "leave"
            self.anim.play("cicada_fly")
        if self.state == "arrive":
            if self.fly_to(*self.spot(), dt, speed=90):
                self.state, self.timer = "quiet", 0.0
                self.anim.play("cicada_sit")
                self.wait = rng.uniform(1, 2)
        elif self.state == "quiet":
            self.x, self.y = self.spot()
            if self.timer > self.wait:
                if self.buzzes > 0:  # BZZZZZ!
                    self.buzzes -= 1
                    self.state, self.timer = "buzz", 0.0
                    self.anim.play("cicada_buzz")
                    w.add(Bubble(w, self, "buzz_bubble", rise=20))
                    w.honk(self)  # the foxes prick up their ears
                else:
                    self.state = "leave"
                    self.anim.play("cicada_fly")
        elif self.state == "buzz":
            self.x, self.y = self.spot()
            if self.timer > 2.5:
                self.state, self.timer = "quiet", 0.0
                self.anim.play("cicada_sit")
                self.wait = rng.uniform(2, 4)
        elif self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=110):
                self.gone = True


class Silk(Thing):
    """One short length of a spider's thread (a thread is a column of these)."""
    kind = "silk"
    z = 4  # behind the oak, so the thread disappears up into the crown

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "silk")


class Spider(Visitor):
    """A spider shaken out of the autumn oak: it lets itself down on a thread, dangles, and climbs back up."""
    kind = "spider"
    z = 24

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "spider")
        rng = world.rng
        self.top = y
        self.drop_to = y + rng.uniform(45, 85) * world.scale
        self.state = "down"
        self.timer = 0.0
        self.dangle = rng.uniform(2, 4)
        self.silk = []

    def _thread(self):
        """Keep the thread reaching from the crown down to the spider."""
        step = 6 * self.world.scale
        want = max(0, int((self.y - self.top) / step) + 1)
        while len(self.silk) < want:
            self.silk.append(self.world.add(Silk(self.world, self.x, self.top + len(self.silk) * step)))
        while len(self.silk) > want:
            self.silk.pop().gone = True
        for piece in self.silk:
            piece.x = self.x

    def update(self, dt):
        super().update(dt)
        s = self.world.scale
        self.timer += dt
        if self.state == "down":
            self.y = min(self.drop_to, self.y + 30 * s * dt)
            if self.y >= self.drop_to:
                self.state, self.timer = "dangle", 0.0
        elif self.state == "dangle":
            self.x += math.sin(self.timer * 3) * 3 * s * dt  # a little swing
            if self.timer > self.dangle:
                self.state = "up"
        else:
            self.y -= 18 * s * dt  # climbing back up, hand over hand
            if self.y <= self.top:
                self.gone = True
        self._thread()
        if self.gone:
            for piece in self.silk:
                piece.gone = True
