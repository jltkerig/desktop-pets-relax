"""Spring things: rain puddles (and the muddy paw prints of foxes who've splashed in them), the robin's nest in
the oak, the kite that gets stuck in the tree, and the watering can."""
import math

from pet.things import Thing
from .base import Droplet


class Puddle(Thing):
    """A puddle left by the rain (not in winter). Raindrops ripple it; it slowly dries up once the rain stops.
    Click it, or let a fox hop in, and the water splashes up."""
    kind = "puddle"
    z = 2
    DRIES_IN = 240  # seconds after the rain stops

    def __init__(self, world, x, small=False):
        self.size = "puddle_s" if small else "puddle"
        super().__init__(world, x, world.ground, self.size)
        self.dry = 0.0  # seconds it's been drying
        self.splashing = False

    @property
    def half_width(self):
        return (13 if self.size == "puddle_s" else 20) * self.world.scale

    def splash(self, drops=8):
        w, s = self.world, self.world.scale
        self.anim.play(f"{self.size}_splash")
        self.splashing = True
        for _ in range(drops):
            w.add(Droplet(w, self.x + w.rng.uniform(-0.6, 0.6) * self.half_width, self.y - 2 * s))

    def click(self):
        self.splash()

    def update(self, dt):
        super().update(dt)
        raining = self.world.falling == "rain"
        self.dry = 0.0 if raining else self.dry + dt
        self.alpha = max(0.0, 1 - self.dry / self.DRIES_IN)
        if self.alpha <= 0:
            self.gone = True
        if self.splashing and not self.anim.done:
            return
        self.splashing = False
        self.anim.play(f"{self.size}_rain" if raining else self.size)


class MudPrint(Thing):
    """A muddy paw print, left by a fox who's been splashing in a puddle. It fades."""
    kind = "print"
    z = 2

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "mudprint")
        self.age = 0.0

    def update(self, dt):
        self.age += dt
        self.alpha = max(0.0, 1.0 - self.age / 30)
        if self.age > 30:
            self.gone = True


class Nest(Thing):
    """A robin's nest in a fork of the oak (spring), the robin sitting on it. Click it and she hops up to show
    you her three blue eggs. A fox nosing about under the tree gets a telling-off: TWEET!"""
    kind = "nest"
    z = 6
    SPOT = (38, 143)  # where it sits on the oak: sideways from the trunk, and up, in sprite pixels

    def __init__(self, world, tree):
        self.tree = tree
        super().__init__(world, tree.x, tree.y, "nest")
        self.calm_for = 0.0  # seconds before she'll scold again
        self.busy_for = 0.0  # seconds left showing her eggs, or scolding
        self.follow()

    def follow(self):
        s = self.world.scale
        self.x, self.y = self.tree.x + self.SPOT[0] * s, self.tree.y - self.SPOT[1] * s

    def click(self):
        self.anim.play("nest_eggs")
        self.busy_for = 2.5

    def scold(self, fox):
        from pet.fox import Step
        from pet.visitors import Bubble  # (visitors uses items, so not at the top)
        w = self.world
        self.anim.play("nest_scold")
        self.busy_for, self.calm_for = 1.8, w.rng.uniform(25, 50)
        bubble = w.add(Bubble(w, self, "tweet_bubble", rise=16))
        bubble.life = 1.6
        if fox.step is not None and fox.step.anim in fox.CALM and not fox.asleep:
            fox.do(Step("tilt", face=self.x), Step("watch", 1.5, face=self.x), Step("happy", 0.8))

    def update(self, dt):
        super().update(dt)
        w, s = self.world, self.world.scale
        if self.tree.gone:
            self.gone = True
            return
        self.follow()
        self.calm_for = max(0.0, self.calm_for - dt)
        if self.busy_for > 0:
            self.busy_for -= dt
            if self.busy_for <= 0:
                self.anim.play("nest")
            return
        if self.calm_for <= 0:
            near = [f for f in w.of("fox") if abs(f.x - self.tree.x) < 45 * s and f.alpha > 0 and not f.asleep
                    and not f.held]
            if near and w.rng.random() < dt * 0.5:
                self.scold(near[0])


class Kite(Thing):
    """A kite, stuck up in the oak (spring). The wind tugs at it; click it and it shakes loose and flutters
    down. Pick it up and fly it about with the mouse: its tail streams out behind and the foxes chase it. Let
    go and it glides down to the grass. A gust may carry it back up into the tree."""
    kind = "kite"
    z = 29
    draggable = True
    carryable = True
    SPOT = (-48, 160)  # where it's caught in the oak (sideways, up), in sprite pixels

    def __init__(self, world):
        super().__init__(world, world.width * 0.7, world.ground, "kite_ground")
        self.held = False
        self.vx = 0.0
        self.chaser = None  # the fox running after it
        self.state = "ground"
        self.last_x = self.x
        if self.holder() is not None:
            self.state = "stuck"
            self.x, self.y = self.stuck_spot()
            self.anim.name = "kite"

    def holder(self):
        return self.world.tree() or next(iter(self.world.of("birch")), None)

    def stuck_spot(self):
        tree, s = self.holder(), self.world.scale
        up = self.SPOT[1] if tree.kind == "tree" else 120
        return tree.x + self.SPOT[0] * s, tree.y - up * s

    @property
    def flying(self):
        return self.held or self.state in ("falling", "lifting")

    def pick_up(self):
        self.held = True
        self.state = "held"
        self.anim.play("kite_gusty")

    def drop(self):
        self.throw(0.0, 0.0)

    def throw(self, vx, vy):
        self.held = False
        self.state = "falling"
        self.vx = max(-300.0, min(300.0, vx * 0.3)) * self.world.scale / 2

    def click(self):
        if self.state == "stuck":
            self.state, self.vx = "falling", 0.0  # shaken loose

    def update(self, dt):
        super().update(dt)
        w, s = self.world, self.world.scale
        if self.held:
            if abs(self.x - self.last_x) > 1:
                self.facing = -1 if self.x > self.last_x else 1  # the tail streams out behind
            self.last_x = self.x
            return
        tree = self.holder()
        if self.state == "stuck":
            if tree is None:
                self.state = "falling"
                return
            self.x, self.y = self.stuck_spot()
            self.anim.play("kite_gusty" if w.wind > 0.4 else "kite")
        elif self.state == "falling":  # gliding down, swaying, carried by the wind
            self.anim.play("kite")
            self.vx *= max(0.0, 1 - 0.6 * dt)
            self.x += (self.vx + math.sin(self.y * 0.03) * 30 * s + w.wind * w.wind_dir * 80 * s) * dt
            self.x = max(20.0, min(w.width - 20.0, self.x))
            self.y += (34 - w.wind * 16) * s * dt
            if self.y >= w.ground - 8 * s:
                self.state, self.y = "ground", w.ground
                self.anim.play("kite_ground")
        elif self.state == "ground":
            if tree is not None and w.wind > 0.6 and w.rng.random() < dt * 0.03:
                self.state = "lifting"  # a gust picks it up and drops it right back in the tree
        elif self.state == "lifting":
            self.anim.play("kite_gusty")
            if tree is None:
                self.state = "falling"
                return
            tx, ty = self.stuck_spot()
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            step = 140 * s * dt
            if dist <= step:
                self.state = "stuck"
            else:
                self.x += dx / dist * step
                self.y += dy / dist * step


class WateringCan(Thing):
    """A watering can (spring and summer). Pick it up and hold it over the garden rows, the corn or the flowers:
    it tips and pours, and they grow faster (flowers bob happily). Let go and it drops where you leave it."""
    kind = "can"
    z = 26
    draggable = True
    carryable = True
    GROW = 6  # while watered, plants grow this many times faster (on top of the usual)

    def __init__(self, world, x):
        super().__init__(world, x, world.ground, "watering_can")
        self.variant = "watering_can"
        self.held = False
        self.vy = 0.0
        self.watering = None  # what it's pouring on
        self.drip = 0.0

    def pick_up(self):
        self.held = True

    def drop(self):
        self.throw(0.0, 0.0)

    def throw(self, vx, vy):
        self.held = False
        self.vy = 0.0
        self.watering = None

    def target(self):
        """What's right under the spout's rose: a crop row, the corn, a flower bed, the sunflowers."""
        s = self.world.scale
        rose = self.x + 18 * s
        for thing in self.world.things:
            if thing.gone or not (thing.kind in ("crop", "corn") or getattr(thing, "variant", "") in
                                  ("daffodils", "tulips", "violets", "dahlias", "dandelions", "sunflowers")):
                continue
            left, top, w, _ = thing.rect()
            if left <= rose <= left + w and top - 160 * s <= self.y <= thing.y:
                return thing
        return None

    def update(self, dt):
        super().update(dt)
        w, s = self.world, self.world.scale
        if self.held:
            self.watering = self.target()
            self.anim.play("watering_can_pour" if self.watering is not None else "watering_can")
            if self.watering is not None:
                self.pour(dt)
            return
        self.anim.play("watering_can")
        if self.y < w.ground:
            self.vy += 900 * s * dt
            self.y = min(w.ground, self.y + self.vy * dt)
            if self.y >= w.ground:
                self.vy = 0.0
                w.settings["items"].setdefault("watering_can", {"out": True, "x": None})["x"] = round(self.x)
                w.dirty = True

    def pour(self, dt):
        w, s, thing = self.world, self.world.scale, self.watering
        self.drip -= dt
        if self.drip <= 0:
            self.drip = 0.12
            drop = w.add(Droplet(w, self.x + 18 * s + w.rng.uniform(-2, 2) * s, self.y - 10 * s))
            drop.vx, drop.vy = drop.vx * 0.15, 40.0  # falling from the rose, not splashing up
        if hasattr(thing, "planted") and isinstance(thing.planted, (int, float)):
            thing.planted -= dt * self.GROW  # as if it had been planted earlier: it grows on faster
            item = w.settings["items"].get(thing.variant if thing.kind == "crop" else "corn")
            if isinstance(item, dict):
                item["planted"] = thing.planted
                w.dirty = w.dirty or w.rng.random() < dt  # saved now and then, not every frame
        elif hasattr(thing, "react") and not getattr(thing, "reacting", False) and w.rng.random() < dt * 0.8:
            thing.react()  # flowers bob, happily watered
