"""The oak tree, the leaves it drops and its acorns."""
import math

from pet import sprites
from pet.things import Thing

GRAVITY = 700  # sprite pixels per second squared (scaled)


class Tree(Thing):
    kind = "tree"
    draggable = True
    z = 5

    def __init__(self, world, x, variant="oak"):
        super().__init__(world, x, world.ground, variant)
        self.variant = variant
        self.shaking = 0.0

    def update(self, dt):
        self.shaking = max(0.0, self.shaking - dt)
        super().update(dt * (7 if self.shaking else 1))  # a shake makes the crown rustle fast

    def click(self):
        """Shake the tree: a flurry of leaves, and sometimes an acorn."""
        w = self.world
        self.shaking = 0.8
        for _ in range(8):
            x, y = self.crown_point()
            w.add(Leaf(w, x, y, w.rng.choice(("red", "orange", "yellow", "brown"))))
        if w.rng.random() < 0.4 and len(w.of("acorn")) < 4:
            w.drop_acorn(self)

    def crown_point(self):
        """A random spot in the crown, for leaves and acorns to start from."""
        s, rng = self.world.scale, self.world.rng
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.2, 0.9)
        return self.x + math.cos(a) * r * 80 * s, self.y - (143 - math.sin(a) * r * 52) * s

    def perch_points(self):
        """Branch spots where a bird can sit (screen coordinates of its feet)."""
        s = self.world.scale
        # spots along the top of the crown
        return [(self.x - 45 * s, self.y - 188 * s), (self.x + 32 * s, self.y - 192 * s),
                (self.x + 68 * s, self.y - 176 * s), (self.x - 74 * s, self.y - 168 * s)]

    def base_range(self):
        """Where under the tree a fox can nap (between the roots and the crown's edge)."""
        s = self.world.scale
        return self.x - 60 * s, self.x + 60 * s


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


class Pumpkin(Thing):
    """A pumpkin that grows from a sprout to a big ripe pumpkin while you work.

    Its stage comes from when it was planted, so it keeps growing between runs (the time is saved).
    """
    kind = "pumpkin"
    draggable = True
    z = 6
    STAGE_SECONDS = 10 * 60  # about 40 minutes from sprout to ripe
    STAGES = 5

    def __init__(self, world, x, planted, pace=1.0, record=None, size="m", shape="round", jack=False):
        self.size = size if size in ("s", "m", "l") else "m"
        self.shape = shape if shape in ("round", "tall", "squat") else "round"
        self.jack = bool(jack)  # this one turns out to be a jack-o'-lantern when ripe
        super().__init__(world, x, world.ground, f"pumpkin_0_{self.size}_{self.shape}")
        self.planted = planted
        self.pace = pace
        self.record = record  # its entry in the saved patch, kept up to date when it is moved
        self.anim.time = world.rng.uniform(0, 2)

    @property
    def stage(self):
        age = self.world.now().timestamp() - self.planted
        return max(0, min(self.STAGES - 1, int(age / (self.STAGE_SECONDS * self.pace))))

    @property
    def ripe(self):
        return self.stage >= 3

    def click(self):
        if self.stage >= 3 and not getattr(self, "wilting", False):
            self.wilting = True
            self.anim.play(f"pumpkin_wilt_{self.size}_{self.shape}")
        else:
            self.anim.time += 0.7  # a little rustle

    def _replant(self):
        """After wilting: a fresh sprout, maybe a different size or shape this time."""
        w = self.world
        self.wilting = False
        self.planted = w.now().timestamp()
        self.size = w.rng.choice(("s", "m", "l"))
        self.shape = w.rng.choice(("round", "tall", "squat"))
        self.jack = w.rng.random() < 0.2
        if self.record is not None:
            self.record.update(planted=self.planted, size=self.size, shape=self.shape, jack=self.jack)
            w.dirty = True

    def update(self, dt):
        if getattr(self, "wilting", False):
            super().update(dt)
            if self.anim.done:
                self._replant()
            return
        name = f"pumpkin_{self.stage}_{self.size}_{self.shape}" + ("_jack" if self.jack and self.stage == 4 else "")
        if self.anim.name != name:
            self.anim.name = name
        super().update(dt)


class Treasure(Thing):
    """A picture of a taskbar icon that a fox "dug up". Only a picture: nothing on the computer is touched.

    The window fills in world.images[key] with the copied icon. Carried in the fox's mouth, then dropped,
    and it fades away after a while.
    """
    kind = "treasure"
    z = 27
    SIZE = 12  # sprite pixels square (the icon is shrunk to this, so it looks pixelated like everything else)

    def __init__(self, world, fox, key):
        super().__init__(world, fox.x, world.ground, "acorn")  # the sprite is unused; the window draws the icon
        self.key = key
        self.carried_by = fox
        self.on_ground_for = 0.0

    def rect(self):
        s = self.world.scale
        size = self.SIZE * s
        return self.x - size / 2, self.y - size, size, size

    def update(self, dt):
        fox = self.carried_by
        if fox is not None and not fox.gone:
            s = self.world.scale
            self.facing = fox.facing
            self.x = fox.x + fox.facing * 25 * s
            self.y = fox.y - 13 * s  # in its mouth
            return
        self.carried_by = None
        self.y = min(self.world.ground, self.y + 400 * self.world.scale * dt)  # drops to the ground
        self.on_ground_for += dt
        if self.on_ground_for > 35:
            self.alpha -= dt / 4
            if self.alpha <= 0:
                self.gone = True


class Prop(Thing):
    """Something that just stands there looking nice (the scarecrow, the hoe). You can drag it."""
    kind = "prop"
    draggable = True
    z = 7

    def __init__(self, world, x, variant):
        super().__init__(world, x, world.ground, variant)
        self.variant = variant

    CLICKS = {"scarecrow": "scarecrow_surprised", "hoe": "hoe_wobble"}

    def click(self):
        reaction = self.CLICKS.get(self.variant)
        if reaction:
            self.anim.play(reaction)

    def update(self, dt):
        super().update(dt)
        if self.anim.name != self.variant and self.anim.done:
            self.anim.play(self.variant)  # back to normal


class Corn(Thing):
    """A row of corn that grows from shoots to tall stalks with ears, then dries golden for autumn.

    Like the pumpkins, its stage comes from when it was planted, so it keeps growing between runs.
    """
    kind = "corn"
    draggable = True
    z = 5
    STAGE_SECONDS = 10 * 60
    STAGES = 5

    def __init__(self, world, x, planted):
        super().__init__(world, x, world.ground, "corn_0")
        self.variant = "corn"
        self.planted = planted
        self.anim.time = world.rng.uniform(0, 2)

    @property
    def stage(self):
        age = self.world.now().timestamp() - self.planted
        return max(0, min(self.STAGES - 1, int(age / self.STAGE_SECONDS)))

    def click(self):
        if self.stage >= 3:
            self.world.harvest(self)
        else:
            self.anim.time += 0.9  # a rustle

    def update(self, dt):
        name = f"corn_{self.stage}"
        if self.anim.name != name:
            self.anim.name = name
        super().update(dt)


class Den(Thing):
    """The foxes' den: a grassy mound with a burrow. Sleepy foxes curl up inside it."""
    kind = "den"
    draggable = True
    z = 3

    def __init__(self, world, x):
        super().__init__(world, x, world.ground, "den")
        self.variant = "den"
        self.sleepers = []  # foxes asleep inside
        self.z_timer = 0.0

    def entrance_x(self):
        return self.x + 4 * self.world.scale

    def click(self):
        if self.sleepers:
            for fox in list(self.sleepers):  # a knock on the den: sleepy foxes pop out
                fox.poke()
        elif not self.world.of("frog"):
            from pet.visitors import Frog
            self.world.add(Frog(self.world, self.entrance_x()))

    def update(self, dt):
        self.sleepers = [f for f in self.sleepers if not f.gone and f.in_den]
        palettes = sorted({f.palette for f in self.sleepers})
        self.anim.name = ("den_both" if len(palettes) > 1 else f"den_{palettes[0]}" if palettes else "den")
        if self.sleepers:
            self.z_timer -= dt
            if self.z_timer <= 0:
                self.z_timer = 1.6
                self.world.add(Zzz(self.world, self.entrance_x() + 10 * self.world.scale, self.y - 24 * self.world.scale))


class Zzz(Thing):
    """A little z drifting up from the den while the foxes sleep."""
    kind = "zzz"
    z = 35

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "zzz")
        self.age = 0.0
        self.start_x = x

    def update(self, dt):
        self.age += dt
        s = self.world.scale
        self.y -= 9 * s * dt
        self.x = self.start_x + math.sin(self.age * 2.2) * 3 * s
        self.alpha = max(0.0, 1.0 - self.age / 2.6)
        if self.age > 2.6:
            self.gone = True


class Climbable(Thing):
    """Something the foxes climb: a pile of oak barrels or a haystack. levels are the spots a fox can stand
    on, as (sideways from the middle, height) in sprite pixels, from the lowest up."""
    kind = "climb"
    draggable = True
    z = 8
    LEVELS = {
        "barrels": [(-22, 22), (-11, 41), (0, 60)],  # the tops of the barrels, row by row
        "haystack": [(-16, 15), (0, 31)],
        "haystack_row": [(-32, 15), (0, 15)],
        "haystack_steps": [(-32, 15), (0, 31), (32, 47)],
    }
    HAY = ("haystack", "haystack_row", "haystack_steps")

    def __init__(self, world, x, variant, layout=None):
        self.variant = variant
        self.layout = layout if layout in self.LEVELS and variant == "haystack" else variant
        super().__init__(world, x, world.ground, self.layout)
        self.levels = self.LEVELS[self.layout]
        self.state = "standing"  # barrels: standing, falling, fading, away, returning
        self.timer = 0.0

    @property
    def available(self):
        return self.state == "standing"

    def _drop_climbers(self):
        for fox in self.world.of("fox"):
            if fox.up_high and abs(fox.x - self.x) < 80 * self.world.scale:
                fox.drop()  # whoops: it lands on its feet, happily

    def click(self):
        w = self.world
        if self.variant == "barrels" and self.state == "standing":
            self._drop_climbers()
            self.state = "falling"
            self.anim.play("barrels_fall")
        elif self.variant == "haystack":
            self._drop_climbers()
            for _ in range(14):
                w.add(StrawBit(w, self.x + w.rng.uniform(-40, 40) * w.scale, self.y - w.rng.uniform(4, 30) * w.scale))
            choices = [h for h in self.HAY if h != self.layout]
            self.layout = w.rng.choice(choices)
            self.anim.play(self.layout)
            self.levels = self.LEVELS[self.layout]
            w.settings["items"].setdefault("haystack", {"out": True, "x": None})["layout"] = self.layout
            w.dirty = True

    def update(self, dt):
        super().update(dt)
        self.timer += dt
        if self.state == "falling" and self.anim.done:
            self.state, self.timer = "fading", 0.0
        elif self.state == "fading":
            self.alpha = max(0.0, 1 - self.timer / 1.5)
            if self.alpha <= 0:
                self.state, self.timer = "away", 0.0
        elif self.state == "away" and self.timer > 25:
            self.state, self.timer = "returning", 0.0
            self.anim.play("barrels")
        elif self.state == "returning":
            self.alpha = min(1.0, self.timer / 1.5)
            if self.alpha >= 1:
                self.state = "standing"


class CornCob(Acorn):
    """An ear of corn from the harvest. The foxes bat it about like an acorn; it fades after a while."""
    is_cob = True

    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.carried = False  # in a squirrel's arms
        self.anim = sprites.Anim("corncob")
        self.age = 0.0

    def update(self, dt):
        if self.carried:
            return
        super().update(dt)
        self.age += dt
        if self.age > 90:
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
