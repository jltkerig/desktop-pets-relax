"""Things that grow or are harvested: pumpkins (and the single ones put out to decorate), watermelons,
corn, the vegetable rows (tomatoes, radishes, lettuce, cattails), corn cobs and fallen fruit."""
from pet import sprites
from pet.things import Thing
from .base import Acorn, Fluff, Kernel, PumpkinBit


class Pumpkin(Thing):
    """A pumpkin that grows from a sprout to a big ripe pumpkin while you work.

    Its stage comes from when it was planted, so it keeps growing between runs (the time is saved).
    """
    kind = "pumpkin"
    draggable = True
    z = 6
    STAGE_SECONDS = 10 * 60  # about 40 minutes from sprout to ripe
    STAGES = 5
    GIANT_CHANCE = 0.15      # now and then one just keeps on growing...
    GIANT, BURST = 5, 6      # ...into a giant, and then too big: it splits open
    CROP = "pumpkin"         # its sprites: pumpkin_<stage>_<size>_<shape>, pumpkin_wilt_<size>_<shape>
    SHAPES = ("round", "tall", "squat")
    WILT = "wilt"            # what a ripe one does when clicked

    def __init__(self, world, x, planted, pace=1.0, record=None, size="m", shape="round", jack=False,
                 giant=False):
        self.size = size if size in ("s", "m", "l") else "m"
        self.shape = shape if shape in self.SHAPES else self.SHAPES[0]
        self.jack = bool(jack)  # this one turns out to be a jack-o'-lantern when ripe
        self.giant = bool(giant)
        self.bursting = False
        super().__init__(world, x, world.ground, f"{self.CROP}_0_{self.size}_{self.shape}")
        self.planted = planted
        self.pace = pace
        self.record = record  # its entry in the saved patch, kept up to date when it is moved
        self.wilting = False
        self.anim.time = world.rng.uniform(0, 2)

    @property
    def stage(self):
        """0 sprout .. 4 ripe; a giant goes on to 5 (huge) and 6 (too big: it bursts). A jack-o'-lantern
        stops growing, giant or not."""
        age = self.world.now().timestamp() - self.planted
        last = (self.GIANT if self.jack else self.BURST) if self.giant else self.STAGES - 1
        return max(0, min(last, int(age / (self.STAGE_SECONDS * self.pace))))

    @property
    def ripe(self):
        return self.stage >= 3

    @property
    def huge(self):
        return self.stage == self.GIANT

    def click(self):
        if self.stage == self.STAGES - 1 and not self.wilting and not self.bursting:
            self.wilting = True
            self.anim.play(f"{self.CROP}_{self.WILT}_{self.size}_{self.shape}")
        else:
            self.anim.time += 0.7  # a little rustle (a giant is far too heavy to do more)

    def carve(self):
        """The hoe carves a face in a ripe pumpkin: it's a jack-o'-lantern now. True if it could."""
        if self.stage < self.STAGES - 1 or self.jack or self.wilting or self.bursting:
            return False
        self.jack = True
        if self.record is not None:
            self.record["jack"] = True
            self.world.dirty = True
        s = self.world.scale
        for _ in range(10):
            self.world.add(PumpkinBit(self.world, self.x + self.world.rng.uniform(-10, 10) * s, self.y - 12 * s))
        return True

    def _burst(self):
        """Too big! It splits open and seeds and bits fly out; then a fresh sprout comes up."""
        self.bursting = True
        self.anim.play(f"pumpkin_burst_{self.shape}")
        w, s = self.world, self.world.scale
        for _ in range(16):
            w.add(PumpkinBit(w, self.x + w.rng.uniform(-24, 24) * s, self.y - w.rng.uniform(8, 30) * s))

    def _replant(self):
        """After wilting or bursting: a fresh sprout, maybe a different size or shape this time."""
        w = self.world
        self.wilting = False
        self.planted = w.now().timestamp()
        self.size = w.rng.choice(("s", "m", "l"))
        self.shape = w.rng.choice(self.SHAPES)
        self.jack = w.rng.random() < 0.2 and self.CROP == "pumpkin"
        self.giant = w.rng.random() < self.GIANT_CHANCE
        self.bursting = False
        if self.record is not None:
            self.record.update(planted=self.planted, size=self.size, shape=self.shape, jack=self.jack,
                               giant=self.giant)
            w.dirty = True

    def update(self, dt):
        if self.wilting or self.bursting:
            super().update(dt)
            if self.anim.done:
                self._replant()
            return
        stage = self.stage
        if stage == self.BURST:
            return self._burst()
        if stage == self.GIANT:
            name = f"pumpkin_giant_{self.shape}" + ("_jack" if self.jack else "")
        else:
            name = f"{self.CROP}_{stage}_{self.size}_{self.shape}" + ("_jack" if self.jack and stage == 4 else "")
        if self.anim.name != name:
            self.anim.name = name
        super().update(dt)


class DecoPumpkin(Thing):
    """A single ripe pumpkin (or jack-o'-lantern) put out to decorate: pick it up and put it anywhere. Let go
    over a haystack, the barrels, the stump or the woodstack and it sits on top (and moves with it); anywhere
    else it drops to the ground. Kept in settings["decorations"]."""
    kind = "deco"
    draggable = True
    is_deco = True
    z = 9  # in front of what it sits on

    def __init__(self, world, x, y, size="m", shape="round", jack=False):
        self.size = size if size in ("s", "m", "l") else "m"
        self.shape = shape if shape in Pumpkin.SHAPES else "round"
        self.jack = bool(jack)
        super().__init__(world, x, y, self.sprite())
        self.held = False
        self.holder, self.dx, self.level = None, 0.0, None  # sitting on: a climbable, sideways offset, which level
        self.vy = 0.0
        self.huge = False  # (for the night glow: never giant)

    def sprite(self):
        return f"pumpkin_4_{self.size}_{self.shape}" + ("_jack" if self.jack else "")

    def pick_up(self):
        self.held = True
        self.holder = self.level = None
        self.vy = 0.0

    def drop(self):
        self.held = False
        self.world.place_deco(self)

    def click(self):
        if self.vy == 0 and not self.held:
            self.vy = -110 * self.world.scale  # a little hop

    def carve(self):
        """The hoe carves it a face. True if it could."""
        if self.jack:
            return False
        self.jack = True
        self.anim.name = self.sprite()
        s = self.world.scale
        for _ in range(10):
            self.world.add(PumpkinBit(self.world, self.x + self.world.rng.uniform(-10, 10) * s, self.y - 12 * s))
        self.world.save_decos()
        return True

    def floor(self):
        """The y it rests at: the top of what it's on, or the ground."""
        h = self.holder
        if h is not None and (h.gone or not h.available):
            self.holder = self.level = None  # the haystack was put away, or the barrels fell: down it comes
            h = None
        if h is None:
            return self.world.ground
        return h.y - h.levels[self.level][1] * self.world.scale

    def update(self, dt):
        super().update(dt)
        if self.held:
            return
        s = self.world.scale
        if self.holder is not None:
            self.x = self.holder.x + self.dx * s
        floor = self.floor()
        if self.y < floor or self.vy < 0:
            self.vy += 1200 * s * dt
            self.y += self.vy * dt
        if self.y >= floor:
            self.y = floor
            self.vy = -self.vy * 0.25 if self.vy > 120 * s else 0.0  # a small bump, then it settles


class Melon(Pumpkin):
    """A watermelon that grows over time like the pumpkins do: a sprout, a vine with a yellow flower, then a
    striped melon getting bigger until it's ripe. Click a ripe one and it splits open, red and juicy, and a new
    one is sown."""
    kind = "melon"
    CROP = "melon"
    SHAPES = ("round", "long")
    WILT = "split"
    GIANT_CHANCE = 0.0

    def __init__(self, world, x, planted, pace=1.0, record=None, size="m", shape="round", jack=False, giant=False):
        super().__init__(world, x, planted, pace, record, size, shape)  # never a jack-o'-lantern, never a giant

    def click(self):
        was = self.wilting
        super().click()
        if self.wilting and not was:  # juicy bits flying
            w, s = self.world, self.world.scale
            for _ in range(8):
                w.add(Kernel(w, self.x + w.rng.uniform(-8, 8) * s, self.y - 10 * s, "apple_bit"))

    def carve(self):
        return False  # the hoe's for pumpkins


class Crop(Thing):
    """A row of something that grows over time like the corn: tomato plants, radishes, lettuce or cattails. Its
    stage comes from when it was planted (saved), so it keeps growing between runs. Click it when it's ripe to
    harvest it: tomatoes drop off, a radish or a lettuce pops out of the ground, cattails burst into fluff that
    blows away on the wind. Then it's sown again."""
    kind = "crop"
    draggable = True
    z = 5
    STAGES = 5
    SECONDS = {"tomatoes": 10 * 60, "radishes": 6 * 60, "lettuce": 7 * 60, "cattails": 10 * 60}
    RIPE = {"tomatoes": 4, "radishes": 4, "lettuce": 4, "cattails": 3}
    # where the harvest comes from: (x from the middle, height) in sprite pixels, as drawn
    YIELD = {"tomatoes": [(-26, 19), (-23, 15), (-9, 19), (-6, 15), (8, 19), (11, 15), (25, 19), (28, 15)],
             "radishes": [(-23, 1), (-14, 1), (-5, 1), (4, 1), (13, 1), (22, 1)],
             "lettuce": [(-20, 4), (-6, 4), (8, 4), (22, 4)],
             "cattails": [(-19, 45), (-10, 52), (-1, 47), (8, 55), (17, 49)]}
    PRODUCE = {"tomatoes": ("tomato", "apple_bit"), "radishes": ("radish", "leaf_bit"),
               "lettuce": ("lettuce_head", "leaf_bit")}

    def __init__(self, world, x, planted, name):
        super().__init__(world, x, world.ground, f"{name}_0")
        self.variant = name
        self.planted = planted
        self.bursting = False
        self.anim.time = world.rng.uniform(0, 2)

    @property
    def stage(self):
        age = self.world.now().timestamp() - self.planted
        return max(0, min(self.STAGES - 1, int(age / self.SECONDS[self.variant])))

    @property
    def ripe(self):
        return self.stage >= self.RIPE[self.variant]

    def click(self):
        if self.ripe and not self.bursting:
            self.harvest()
        else:
            self.anim.time += 0.9  # a rustle

    def harvest(self):
        w, s, rng = self.world, self.world.scale, self.world.rng
        spots = [(self.x + dx * s, self.y - h * s) for dx, h in self.YIELD[self.variant]]
        if self.variant == "cattails":  # the heads burst, and their fluff blows away on the wind
            for x, y in spots:
                for _ in range(rng.randint(8, 12)):
                    w.add(Fluff(w, x + rng.uniform(-2, 2) * s, y + rng.uniform(-4, 4) * s, "cattail_fluff"))
            self.bursting = True
            self.anim.play("cattails_burst")
            return
        sprite, bit = self.PRODUCE[self.variant]
        for x, y in spots:
            if self.variant == "tomatoes" and rng.random() < 0.3:
                continue  # not every tomato is quite ripe
            thing = w.add(Produce(w, x, y, sprite, bit))
            if self.variant != "tomatoes":  # pulled up: it pops out of the ground
                thing.vy = -rng.uniform(140, 200) * s
                thing.y -= 2 * s
                thing.vx = rng.uniform(-40, 40) * s
        w.plant_crop(self.variant, replant=True)

    def update(self, dt):
        if self.bursting:
            super().update(dt)
            if self.anim.done:
                self.world.plant_crop(self.variant, replant=True)
            return
        name = f"{self.variant}_{self.stage}"
        if self.anim.name != name:
            self.anim.name = name
        super().update(dt * (1 + self.world.wind * 4))


class Corn(Thing):
    """A row of corn that grows from shoots to tall stalks with ears, then dries golden for autumn.

    Like the pumpkins, its stage comes from when it was planted, so it keeps growing between runs.
    """
    kind = "corn"
    draggable = True
    z = 5
    STAGE_SECONDS = 10 * 60
    STAGES = 5
    STALKS = [(-50, 0.82), (-32, 1.0), (-14, 0.9), (4, 1.06), (22, 0.88), (40, 0.97)]  # as drawn: x from the middle,
    STALK_HEIGHT = 86                                                                # and height share

    def ears(self):
        """Where the ear of corn on each stalk hangs (screen x, y)."""
        s = self.world.scale
        return [(self.x + dx * s, self.y - self.STALK_HEIGHT * share * 0.5 * s) for dx, share in self.STALKS]

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
        super().update(dt * (1 + self.world.wind * 5))  # the stalks thrash in a gale


class CornCob(Acorn):
    """An ear of corn from the harvest. The foxes bat it about like an acorn; it fades after a while. You can
    pick it up with the mouse and drop it somewhere else (it falls and bounces where you let go), or throw it
    for the foxes to chase."""
    is_cob = True

    def __init__(self, world, x, y):
        super().__init__(world, x, y)
        self.carried = False  # in a squirrel's arms
        self.held = False     # picked up with the mouse
        self.anim = sprites.Anim("corncob")
        self.kernels = 0      # pecked off by crows
        self.age = 0.0

    @property
    def draggable(self):
        return not self.carried  # anything but out of a squirrel's arms (you can snatch it from under its nose)

    def contains(self, px, py):
        """A little bigger than the picture, so it's easy to grab."""
        if self.alpha <= 0:
            return False
        left, top, w, h = self.rect()
        pad = 5 * self.world.scale
        return left - pad <= px < left + w + pad and top - pad <= py < top + h + pad

    def pick_up(self):
        self.held = True
        self.taken = True  # squirrels and crows leave it alone while it's in your hand

    def drop(self):
        """Let go: it falls from there, bounces, and is fresh again (it won't fade for a while)."""
        self.throw(0.0, 0.0)

    def throw(self, vx, vy):
        """Let go, flying at (vx, vy) screen pixels per second; a fox runs after it if it's thrown hard."""
        s = self.world.scale
        top = 2400 * s / 2
        self.held, self.taken = False, False
        self.on_ground, self.bounced = False, False
        self.vx, self.vy = max(-top, min(top, vx)), max(-top, min(top, vy))
        self.age = 0.0
        if abs(vx) + abs(vy) > 250 * s:
            self.world.cob_thrown(self)

    def update(self, dt):
        if self.carried or self.held:
            return
        super().update(dt)
        self.age += dt
        if self.age > 90:
            self.alpha -= dt / 4
            if self.alpha <= 0:
                self.gone = True


class Produce(CornCob):
    """Something from the garden lying on the ground, like a corn cob: an apple, a tomato, a radish or a lettuce.
    The foxes bat it about, crows peck at it, you can pick it up and drop it, and after a while it fades."""

    def __init__(self, world, x, y, sprite, bit="apple_bit"):
        super().__init__(world, x, y)
        self.anim = sprites.Anim(sprite)
        self.produce = sprite
        self.bit = bit  # what flies off when a crow pecks it
