"""Spring and summer visitors: butterflies that rest on the flowers, songbirds that sing, and baby bunnies."""
import math

from pet.items import Note
from .base import Perch, Visitor
from .crows import crow_perches


# -- spring: butterflies among the flowers, and songbirds --------------------------------------------------

def flower_heads(world):
    """Every flower head in the flower beds that are out (screen coordinates)."""
    spots = []
    for thing in world.of("prop"):
        if thing.variant in ("daffodils", "tulips", "violets", "dahlias", "dandelions"):
            spots += thing.flower_heads()
    for thing in world.of("yard"):
        if thing.variant == "sunflowers":
            spots += thing.flower_heads()
    return spots


class Flutterby(Visitor):
    """A spring butterfly: it flutters in, lands on the flowers to rest a while (wings slowly opening and
    closing), flutters about some more, and goes on its way. With no flowers out, it just wanders through."""
    kind = "butterfly"
    z = 32
    KINDS = ("monarch", "white", "white", "sulphur", "azure")

    def __init__(self, world, species=None, x=None, y=None):
        rng, s = world.rng, world.scale
        self.species = species or rng.choice(self.KINDS)
        self.fly_sprite = "butterfly" if self.species == "monarch" else f"butterfly_{self.species}"
        if x is None:
            x = rng.choice((-20.0, world.width + 20.0))
            y = world.ground - rng.uniform(60, 160) * s
        super().__init__(world, x, y, self.fly_sprite)
        self.anim.time = rng.uniform(0, 1)
        self.visits = rng.randint(2, 4)
        self.state = "flutter"
        self.timer = 0.0
        self.phase = rng.uniform(0, 6.3)
        self.target = None
        self.rest_for = 0.0

    def _next_target(self):
        w, rng, s = self.world, self.world.rng, self.world.scale
        heads = flower_heads(w)
        if self.visits <= 0:
            return (rng.choice((-30.0, w.width + 30.0)), w.ground - rng.uniform(100, 220) * s), False
        if heads:
            near = [h for h in heads if abs(h[0] - self.x) < 600 * s] or heads
            return rng.choice(near), True
        return (w.clamp_x(self.x + rng.uniform(-200, 200) * s, 20.0),
                w.ground - rng.uniform(40, 140) * s), False

    def update(self, dt):
        super().update(dt)
        w, rng, s = self.world, self.world.rng, self.world.scale
        self.timer += dt
        self.phase += dt * 6
        if self.state == "flutter":
            if self.target is None:
                self.target, self.landing = self._next_target()
            tx, ty = self.target
            if self.landing:  # the flower may have been dragged: aim at where it is now
                heads = flower_heads(w)
                if heads:
                    tx, ty = min(heads, key=lambda h: abs(h[0] - tx) + abs(h[1] - ty))
                    self.target = (tx, ty)
                else:
                    self.landing = False
            wobble = math.sin(self.phase) * 30 * s  # bobbing up and down as it flies
            if self.fly_to(tx, ty + (0 if self.landing and abs(self.x - tx) < 20 * s else wobble * 0.3), dt,
                           speed=55) or (abs(self.x - tx) < 2 and abs(self.y - ty) < 4 * s):
                if self.landing:
                    self.x, self.y = tx, ty  # right on the flower
                    self.state, self.timer = "rest", 0.0
                    self.rest_for = rng.uniform(3, 8)
                    self.visits -= 1
                    self.anim.play(f"butterfly_{self.species}_rest")
                elif self.visits <= 0 and (self.x < -20 or self.x > w.width + 20):
                    self.gone = True
                else:
                    if self.visits > 0 and not flower_heads(w):
                        self.visits -= 1  # wandering about with nowhere to land
                    self.target = None
            if self.state == "flutter":  # bobbing in the air (not once it's landed)
                self.y += math.sin(self.phase) * 12 * s * dt
        elif self.state == "rest":
            heads = flower_heads(w)
            if heads:  # sitting on its flower, wherever the bed is moved to
                self.x, self.y = min(heads, key=lambda h: abs(h[0] - self.x) + abs(h[1] - self.y))
            fox_near = any(abs(f.x - self.x) < 40 * s and f.step is not None and f.step.anim != "watch"
                           for f in w.of("fox"))
            if self.timer > self.rest_for or fox_near or not heads:
                self.state, self.target = "flutter", None
                self.anim.play(self.fly_sprite)

    def click(self):
        self.visits = 0  # shoo
        self.state, self.target = "flutter", None
        self.anim.play(self.fly_sprite)


class SongBird(Visitor):
    """A robin, bluebird or goldfinch dropping by in spring: it perches in the oak or on something (or hops
    about on the ground), sings now and then, with music notes floating up, and the foxes stop to listen.
    A robin on the ground sometimes tugs a worm out. Click it, or dash a fox at it, and it flies off."""
    kind = "songbird"
    z = 27

    def __init__(self, world, species, delay=0.0):
        rng = world.rng
        start = rng.choice((-30.0, world.width + 30.0))
        super().__init__(world, start, world.ground - rng.uniform(150, 260) * world.scale, f"{species}_fly")
        self.species = species
        self.delay = delay
        self.state = "arrive"
        self.timer = 0.0
        self.stay = rng.uniform(35, 70)
        self.sing_in = rng.uniform(1.5, 4)
        self.perch = self._choose_perch()
        self.exit = (rng.choice((-40.0, world.width + 40.0)), world.ground - 300 * world.scale)

    def _choose_perch(self):
        w, rng = self.world, self.world.rng
        spots = crow_perches(w)
        trees = [p for p in spots if getattr(p.holder, "kind", None) in ("tree", "birch")]
        if self.species == "robin" and rng.random() < 0.55 or not spots:  # robins like the ground
            return Perch(x=rng.uniform(0.1, 0.9) * w.width)
        return rng.choice(trees) if trees and rng.random() < 0.6 else rng.choice(spots)

    def sing(self):
        w, rng, s = self.world, self.world.rng, self.world.scale
        self.state, self.timer = "sing", 0.0
        self.anim.play(f"{self.species}_sing")
        for k in range(rng.randint(2, 3)):
            w.add(Note(w, self.x + self.facing * (8 + k * 3) * s, self.y - (16 + k * 2) * s, double=rng.random() < 0.4))
        if rng.random() < 0.5:
            w.honk(self)  # the foxes prick up their ears and listen

    def fly_off(self):
        if self.state != "leave":
            self.state = "leave"
            self.anim.play(f"{self.species}_fly")

    def click(self):
        self.fly_off()

    def update(self, dt):
        super().update(dt)
        w, rng, s = self.world, self.world.rng, self.world.scale
        self.timer += dt
        if self.state == "arrive":
            if self.timer < self.delay:
                return
            if not self.perch.ok():
                self.perch = Perch(x=self.x)
            if self.fly_to(*self.perch.pos(w), dt, speed=120):
                self.state, self.timer = "perch", 0.0
                self.anim.play(f"{self.species}_perch")
            return
        if self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=140):
                self.gone = True
            return
        if not self.perch.ok():
            return self.fly_off()
        if self.state != "hop":
            self.x, self.y = self.perch.pos(w)
        self.stay -= dt
        on_ground = not self.perch.high
        if on_ground and any(abs(f.x - self.x) < 40 * s and f.step is not None and
                             f.step.anim in ("run", "trot", "pounce", "dive") for f in w.of("fox")):
            return self.fly_off()
        if self.stay <= 0:
            return self.fly_off()
        if self.state == "perch":
            self.sing_in -= dt
            if self.sing_in <= 0:
                self.sing_in = rng.uniform(3, 7)
                return self.sing()
            roll = rng.random()
            if roll < dt * 0.3:
                self.facing = -self.facing
            elif on_ground and roll < dt * 0.8:  # hopping about, pecking, maybe a worm
                if self.species == "robin" and rng.random() < 0.35:
                    self.state, self.timer = "worm", 0.0
                    self.anim.play("robin_worm")
                elif rng.random() < 0.5:
                    self.state, self.timer = "peck", 0.0
                    self.anim.play(f"{self.species}_peck")
                else:
                    self.hop_to = w.clamp_x(self.x + rng.uniform(-30, 30) * s, 30.0)
                    self.state = "hop"
                    self.anim.play(f"{self.species}_hop")
        elif self.state in ("sing", "peck", "worm"):
            if self.timer > {"sing": 1.2, "peck": 1.5, "worm": 2.6}[self.state]:
                self.state = "perch"
                self.anim.play(f"{self.species}_perch")
        elif self.state == "hop":
            if self.move_to(self.hop_to, 30, dt):
                self.perch = Perch(x=self.x)
                self.state = "perch"
                self.anim.play(f"{self.species}_perch")


def songbirds(world):
    """One songbird, or a pair of the same kind."""
    species = world.rng.choice(("robin", "robin", "bluebird", "goldfinch"))
    return [SongBird(world, species, delay=i * 1.5) for i in range(world.rng.choice((1, 1, 2)))]


# -- spring: baby bunnies ----------------------------------------------------------------------------------

class Bunny(Visitor):
    """A baby bunny: it hops in, nibbles the grass, sits with its nose twitching, hops about a bit, and goes.
    If a fox dashes at it, it's off like a shot (much too quick to catch). Click it and it hops away too."""
    kind = "bunny"
    z = 23
    FLEE_SPEED = 150  # quicker than a fox's sprint

    def __init__(self, world, spot, side, delay=0.0):
        super().__init__(world, -20.0 if side < 0 else world.width + 20.0, world.ground, "bunny_hop")
        self.spot = world.clamp_x(spot, 30.0)
        self.delay = delay
        self.state = "arrive"  # arrive, graze, flee
        self.timer = 0.0
        self.stay = world.rng.uniform(40, 80)
        self.hop_to = None
        self.doing_for = 0.0

    def flee(self):
        if self.state != "flee":
            self.state = "flee"
            self.anim.play("bunny_hop")
            self.facing = -1 if self.x < self.world.width / 2 else 1

    def click(self):
        self.flee()

    def scared(self):
        s = self.world.scale
        return any(abs(f.x - self.x) < 70 * s and f.step is not None and
                   f.step.anim in ("run", "trot", "pounce", "dive") for f in self.world.of("fox"))

    def update(self, dt):
        super().update(dt)
        w, rng = self.world, self.world.rng
        self.timer += dt
        if self.state == "arrive":
            if self.timer < self.delay:
                return
            if self.move_to(self.spot, 60, dt):
                self.state, self.doing_for = "graze", 0.0
            return
        if self.state == "flee":
            if self.move_to(self.leave_x(), self.FLEE_SPEED, dt):
                self.gone = True
            return
        self.stay -= dt
        if self.stay <= 0 or self.scared():
            return self.flee()
        if self.hop_to is not None:
            if self.move_to(self.hop_to, 40, dt):
                self.hop_to, self.doing_for = None, 0.0
            return
        self.doing_for -= dt
        if self.doing_for <= 0:  # something new: nibble, sit, or a little hop
            roll = rng.random()
            if roll < 0.45:
                self.anim.play("bunny_nibble")
                self.doing_for = rng.uniform(2, 4)
            elif roll < 0.8:
                self.anim.play("bunny_sit")
                self.doing_for = rng.uniform(1, 3)
            else:
                self.anim.play("bunny_hop")
                self.hop_to = w.clamp_x(self.x + rng.uniform(-30, 30) * w.scale, 30.0)


def bunnies(world):
    """Two or three baby bunnies, hopping in together from one side."""
    rng, s = world.rng, world.scale
    side = rng.choice((-1, 1))
    centre = rng.uniform(0.2, 0.8) * world.width
    return [Bunny(world, centre + (i * 22 - 20) * s, side, delay=i * 0.6) for i in range(rng.randint(2, 3))]
