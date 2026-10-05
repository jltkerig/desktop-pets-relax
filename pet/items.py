"""The oak tree, the leaves it drops and its acorns."""
import math

from pet import sprites
from pet.things import Thing

GRAVITY = 700  # sprite pixels per second squared (scaled)


class Tree(Thing):
    """The oak, all year round: autumn colours, bare in winter (or snowy), budding in spring with flowers
    underneath, and vibrant green in summer. Click it and something falls out, depending on the season."""
    kind = "tree"
    draggable = True
    z = 5
    LOOKS = {"spring": "oak_spring", "summer": "oak_summer", "autumn": "oak"}

    def __init__(self, world, x, variant="oak"):
        super().__init__(world, x, world.ground, variant)
        self.variant = variant
        self.shaking = 0.0
        self.anim.name = self.look

    @property
    def look(self):
        """Which oak to show for the season (and, in winter, the weather)."""
        season = self.world.season
        if season == "winter":
            return "oak_snow" if self.world.snowy else "oak_winter"
        return self.LOOKS.get(season, "oak")

    @property
    def bare(self):
        return self.look in ("oak_winter", "oak_snow", "oak_spring")

    def update(self, dt):
        if self.anim.name != self.look:
            self.anim.name = self.look  # the season changed (they all sway in step, so no jump)
        self.shaking = max(0.0, self.shaking - dt)
        super().update(dt * (7 if self.shaking else 1 + self.world.wind * 6))  # shaken, or tossed by the wind

    def click(self):
        """Shake the tree. Autumn: a flurry of leaves, sometimes an acorn, now and then a spider on its thread.
        Winter: a branch falls (or, under snow, clumps of snow). Spring: a caterpillar drops out and runs off.
        Summer: a few green leaves, and a butterfly flies out."""
        from pet import visitors  # (visitors uses items, so not at the top)
        w, rng = self.world, self.world.rng
        self.shaking = 0.8
        look = self.look
        if look == "oak_winter":
            w.add(Twig(w, *self.branch_point()))
        elif look == "oak_snow":
            for _ in range(rng.randint(4, 7)):
                x, y = self.branch_point()
                w.add(SnowClump(w, x + rng.uniform(-6, 6) * w.scale, y))
        elif look == "oak_spring":
            w.add(visitors.Inchworm(w, *self.branch_point()))
        elif look == "oak_summer":
            for _ in range(rng.randint(2, 4)):
                w.add(Leaf(w, *self.crown_point(), "green"))
            w.add(visitors.Butterfly(w, *self.crown_point()))
        else:
            for _ in range(8):
                x, y = self.crown_point()
                w.add(Leaf(w, x, y, rng.choice(("red", "orange", "yellow", "brown"))))
            if rng.random() < 0.4 and len(w.nuts()) < 4:
                w.drop_acorn(self)
            if rng.random() < 0.3 and not w.of("spider"):
                w.add(visitors.Spider(w, *self.crown_bottom()))

    def crown_bottom(self):
        """A spot along the underside of the crown, for a spider to let itself down from."""
        s, rng = self.world.scale, self.world.rng
        return self.x + rng.uniform(-55, 55) * s, self.y - rng.uniform(100, 108) * s

    def branch_point(self):
        """Somewhere out along the branches (on a leafless oak, on an actual branch)."""
        if self.bare:
            x, y = self.world.rng.choice(self.perch_points())
            return x, y + self.world.rng.uniform(0, 30) * self.world.scale
        return self.crown_point()

    def crown_point(self):
        """A random spot in the crown, for leaves and acorns to start from."""
        s, rng = self.world.scale, self.world.rng
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.2, 0.9)
        return self.x + math.cos(a) * r * 80 * s, self.y - (143 - math.sin(a) * r * 52) * s

    def perch_points(self):
        """Branch spots where a bird can sit (screen coordinates of its feet). A leafless oak's are in its
        sprite's JSON (forks high up in the branches); a leafy one's are along the top of the crown."""
        s = self.world.scale
        m = sprites.meta(self.look)
        if m.get("perches"):
            ax, ay = m["anchor"]
            return [(self.x + (px - ax) * s, self.y - (ay - py) * s) for px, py in m["perches"]]
        return [(self.x - 45 * s, self.y - 188 * s), (self.x + 32 * s, self.y - 192 * s),
                (self.x + 68 * s, self.y - 176 * s), (self.x - 74 * s, self.y - 168 * s)]

    def base_range(self):
        """Where under the tree a fox can nap (between the roots and the crown's edge)."""
        s = self.world.scale
        return self.x - 60 * s, self.x + 60 * s


class Birch(Thing):
    """A slender white birch, out all year: bare (or snowy) in winter, catkins in spring, bright green in summer,
    golden in autumn. Click it and it shakes: leaves flutter down (golden ones in autumn), or in winter a twig
    falls, or clumps of snow. Birds perch in it. You can drag it."""
    kind = "birch"
    draggable = True
    z = 5

    def __init__(self, world, x):
        super().__init__(world, x, world.ground, "birch_summer")
        self.variant = "birch"
        self.shaking = 0.0
        self.anim.name = self.look
        self.anim.time = 1.3  # out of step with the oak

    @property
    def look(self):
        if self.world.snowed_over:
            return "birch_snow"
        return f"birch_{self.world.season}"

    def update(self, dt):
        if self.anim.name != self.look:
            self.anim.name = self.look
        self.shaking = max(0.0, self.shaking - dt)
        super().update(dt * (7 if self.shaking else 1 + self.world.wind * 7))  # a birch tosses in the wind

    def crown_point(self):
        """A random spot among the branches."""
        s, rng = self.world.scale, self.world.rng
        return self.x + rng.uniform(-34, 34) * s, self.y - rng.uniform(80, 160) * s

    def click(self):
        w, rng = self.world, self.world.rng
        self.shaking = 0.7
        season = w.season
        if season == "autumn":
            for _ in range(rng.randint(4, 7)):
                w.add(Leaf(w, *self.crown_point(), rng.choice(("yellow", "yellow", "orange"))))
        elif season in ("summer", "spring"):
            for _ in range(rng.randint(1, 3)):
                w.add(Leaf(w, *self.crown_point(), "green"))
        elif w.snowed_over:
            for _ in range(rng.randint(3, 5)):
                w.add(SnowClump(w, *self.crown_point()))
        else:
            w.add(Twig(w, *self.crown_point()))

    def perch_points(self):
        """Branch spots where a bird can sit (from the sprite's JSON), in screen coordinates."""
        s = self.world.scale
        m = sprites.meta(self.anim.name)
        ax, ay = m["anchor"]
        return [(self.x + (px - ax) * s, self.y - (ay - py) * s) for px, py in m.get("perches", [])]


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
        self.bitten = 0.0  # 0..1: how much of it has been chewed away

    def rect(self):
        s = self.world.scale
        size = max(2.0, self.SIZE * s * (1 - 0.75 * self.bitten))
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
        w = self.world
        chewer = next((f for f in w.of("fox") if f.step is not None and f.step.anim == "chew"
                       and abs(f.x - self.x) < 40 * w.scale), None)
        if chewer is not None:  # being chewed: smaller bite by bite, crumbs flying off
            self.bitten = min(1.0, self.bitten + dt / 4.0)
            if w.rng.random() < dt * 6:
                w.add(Crumb(w, self.x, self.y - 4 * w.scale))
            if self.bitten >= 1.0:
                for _ in range(6):
                    w.add(Crumb(w, self.x, self.y - 3 * w.scale))
                self.gone = True
                return
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
        self.hat_on = True  # the scarecrow's hat (the crows like to borrow it)
        self.bare_for = 0.0  # dandelions: seconds until new seed clocks have grown
        self.reacting = False  # playing its reaction to a click
        self.anim.name = self.look

    CLICKS = {"scarecrow": "surprised", "hoe": "wobble", "sled": "wobble", "xmas_tree": "sparkle",
              "daffodils": "bob", "tulips": "bob", "violets": "bob", "apple_barrel": "wobble", "well": "bucket",
              "pool": "ripple", "dahlias": "bob"}
    FLOWERS = ("daffodils", "tulips", "violets", "dahlias", "dandelions")
    SNOWY = ("sled", "xmas_tree")  # these get a coat of snow on snowy winter days

    @property
    def snow(self):
        return "_snow" if self.variant in self.SNOWY and self.world.snowed_over else ""

    @property
    def look(self):
        """The sprite it shows when nothing's happening."""
        if self.variant == "scarecrow" and not self.hat_on:
            return "scarecrow_nohat"
        if self.variant == "dandelions":  # seed clocks in spring (or bare stems once blown), flowers in summer
            if self.world.season == "spring":
                return "dandelions_spring_bare" if self.bare_for > 0 else "dandelions_spring"
            return "dandelions_summer"
        return self.variant + self.snow

    def react(self):
        """Its reaction to a click: the scarecrow looks surprised, the hoe and sled wobble, the Christmas tree's
        lights all blaze, flowers bob, the well's bucket goes down, the pool ripples."""
        if self.variant == "dandelions":
            if self.look == "dandelions_summer":
                self.anim.play("dandelions_summer_bob")
                self.reacting = True
            return
        reaction = self.CLICKS.get(self.variant)
        if reaction:
            hatless = "_nohat" if self.variant == "scarecrow" and not self.hat_on else ""
            self.anim.play(f"{self.variant}{self.snow}_{reaction}{hatless}")
            self.reacting = True

    def blow_seeds(self):
        """The dandelion clocks' seeds blow away on the breeze; the stems stand bare until new clocks grow."""
        w = self.world
        for x, y in self.flower_heads():
            for _ in range(w.rng.randint(5, 8)):
                w.add(Fluff(w, x + w.rng.uniform(-2, 2) * w.scale, y + w.rng.uniform(-2, 2) * w.scale))
        self.bare_for = w.rng.uniform(60, 120)
        self.anim.play(self.look)

    def click(self):
        self.react()
        w, s = self.world, self.world.scale
        if self.look == "dandelions_spring":
            self.blow_seeds()
        elif self.variant == "pool":
            w.splash(self, 8)
        elif self.variant in self.FLOWERS and self.flower_heads() and w.rng.random() < 0.4 and \
                len(w.of("butterfly")) < 4:
            from pet.visitors import Flutterby  # a butterfly that was resting in the flowers flies up
            x, y = w.rng.choice(self.flower_heads())
            w.add(Flutterby(w, x=x, y=y))
        elif self.variant == "apple_barrel" and sum(1 for a in w.of("acorn") if getattr(a, "produce", "") == "apple") < 6:
            side = w.rng.choice((-1, 1))  # an apple tumbles off the heap and rolls away
            fruit = w.add(Produce(w, self.x + side * 8 * s, self.y - 30 * s, "apple"))
            fruit.vx = side * w.rng.uniform(50, 90) * s

    def flower_heads(self):
        """Where the flowers in a flower bed are (screen coordinates), for butterflies to land on."""
        m = sprites.meta(self.anim.name if self.anim.name.startswith(self.variant) else self.variant)
        ax, ay = m["anchor"]
        s = self.world.scale
        return [(self.x + (px - ax) * s, self.y - (ay - py) * s) for px, py in m.get("perches", [])]

    def lose_hat(self):
        self.hat_on = False
        self.react()  # oi!

    def get_hat_back(self):
        self.hat_on = True
        self.anim.play(self.look)

    def update(self, dt):
        super().update(dt * (1 + self.world.wind * 4))
        self.bare_for = max(0.0, self.bare_for - dt)
        if self.anim.name != self.look and (self.anim.done or not self.reacting):
            self.anim.play(self.look)  # back to normal (or the weather or season changed its look)
            self.reacting = False


class Note(Thing):
    """A music note floating up from a singing bird."""
    kind = "note"
    z = 36

    def __init__(self, world, x, y, double=False):
        super().__init__(world, x, y, "note_double" if double else "note")
        self.age = 0.0
        self.start_x = x
        self.drift = world.rng.uniform(-6, 6)

    def update(self, dt):
        self.age += dt
        s = self.world.scale
        self.y -= 14 * s * dt
        self.x = self.start_x + (math.sin(self.age * 3) * 3 + self.drift * self.age) * s
        self.alpha = max(0.0, 1.0 - self.age / 1.8)
        if self.age > 1.8:
            self.gone = True


class Hat(Thing):
    """The scarecrow's hat, dropped by a startled crow. Click it (or let the crows) to put it back. Left lying
    there, it finds its own way home after a couple of minutes."""
    kind = "hat"
    z = 26
    LIES_FOR = 120

    def __init__(self, world, x, y, scarecrow):
        super().__init__(world, x, y, "scarecrow_hat")
        self.scarecrow = scarecrow
        self.vy = 0.0
        self.age = 0.0

    def click(self):
        self.return_home()

    def return_home(self):
        if not self.scarecrow.gone:
            self.scarecrow.get_hat_back()
        self.gone = True

    def update(self, dt):
        super().update(dt)
        self.age += dt
        if self.scarecrow.gone:
            self.gone = True  # it goes away with the scarecrow
        elif self.age > self.LIES_FOR and not self.world.of("crow"):
            self.alpha -= dt / 2
            if self.alpha <= 0:
                self.return_home()
        if self.y < self.world.ground:
            self.vy += GRAVITY * 0.35 * self.world.scale * dt  # a hat floats down rather than drops
            self.y = min(self.world.ground, self.y + self.vy * dt)
            self.x += math.sin(self.y * 0.05) * 20 * self.world.scale * dt


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
        snow = "_snow" if self.world.season == "winter" and self.world.snowy else ""  # snowed over, like the oak
        self.anim.name = (f"den{snow}_both" if len(palettes) > 1 else f"den{snow}_{palettes[0]}" if palettes
                          else f"den{snow}")
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
        "stump": [(0, 15)],  # the flat, sawn top
        "woodstack": [(-21, 8), (-16, 16), (0, 24)],  # up the shoulders of the rows of logs
        "slide": [(-18, 12), (-18, 24), (-16, 36)],  # up the ladder to the platform (then down the chute)
    }
    HAY = ("haystack", "haystack_row", "haystack_steps")
    SNOWY = ("stump", "woodstack")  # these wear snow on snowy winter days

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
        elif self.variant in self.SNOWY and w.snowed_over:  # a knock: the snow on top tumbles off
            top = self.levels[-1][1]
            for _ in range(3):
                w.add(SnowClump(w, self.x + w.rng.uniform(-8, 8) * w.scale, self.y - (top + 1) * w.scale))

    def update(self, dt):
        if self.variant in self.SNOWY:
            self.anim.name = self.variant + ("_snow" if self.world.snowed_over else "")
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
    """An ear of corn from the harvest. The foxes bat it about like an acorn; it fades after a while. You can
    pick it up with the mouse and drop it somewhere else (it falls and bounces where you let go)."""
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
        return not self.taken and not self.carried  # not out of a squirrel's arms

    def pick_up(self):
        self.held = True
        self.taken = True  # squirrels and crows leave it alone while it's in your hand

    def drop(self):
        """Let go: it falls from there, bounces, and is fresh again (it won't fade for a while)."""
        self.held, self.taken = False, False
        self.on_ground, self.bounced = False, False
        self.vx = self.vy = 0.0
        self.age = 0.0

    def update(self, dt):
        if self.carried or self.held:
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


class Produce(CornCob):
    """Something from the garden lying on the ground, like a corn cob: an apple, a tomato, a radish or a lettuce.
    The foxes bat it about, crows peck at it, you can pick it up and drop it, and after a while it fades."""

    def __init__(self, world, x, y, sprite, bit="apple_bit"):
        super().__init__(world, x, y)
        self.anim = sprites.Anim(sprite)
        self.produce = sprite
        self.bit = bit  # what flies off when a crow pecks it


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


class Message(Thing):
    """A Discord message a fox has "stolen": only a picture of it, copied off the screen, while the spot it
    came from is covered over. It drops down to the fox, gets carried off and played with, and then flies
    back into place. If anything goes wrong (the window moves, say) it simply vanishes and the cover goes."""
    kind = "message"
    z = 27

    def __init__(self, world, key, home):
        super().__init__(world, home[0], home[1], "acorn")  # the sprite is unused; the window draws the picture
        self.key = key
        self.home = home           # where it belongs, along the strip (its bottom centre)
        self.size = (60.0, 14.0)   # replaced by the picture's real size once it's copied
        self.state = "home"        # home, falling, carried, ground, returning
        self.carried_by = None
        self.ground_time = 0.0
        self.away = 0.0            # seconds since it was taken
        self.limit = 70.0          # it always goes home by itself after this long (shorter for a quick theft)
        self.alpha = 0.0           # invisible until it's actually pulled out

    def rect(self):
        w, h = self.size
        return self.x - w / 2, self.y - h, w, h

    def _fly(self, x, y, dt, speed=520):
        dx, dy = x - self.x, y - self.y
        dist = (dx * dx + dy * dy) ** 0.5
        step = speed * self.world.scale / 2 * dt
        if dist <= step:
            self.x, self.y = x, y
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def mouth(self, fox):
        s = self.world.scale
        return fox.x + fox.facing * 26 * s, fox.y - 10 * s

    def update(self, dt):
        w = self.world
        self.away += dt
        if self.away > self.limit and self.state != "returning":
            # whatever the fox got distracted by, the message goes back in the end
            if self.carried_by is not None and self.carried_by.carrying is self:
                self.carried_by.carrying = None
            self.state, self.carried_by = "returning", None
            self.alpha = 1.0
        if self.state == "falling":
            self.alpha = 1.0
            fox = self.carried_by
            if fox is None or fox.gone:
                self.state = "ground"
            elif self._fly(*self.mouth(fox), dt, speed=700):
                self.state = "carried"
        elif self.state == "carried":
            fox = self.carried_by
            if fox is None or fox.gone or fox.held:
                self.state, self.carried_by = "ground", None
            else:
                self.x, self.y = self.mouth(fox)
                self.facing = fox.facing
        elif self.state == "ground":
            self.carried_by = None
            self.y = min(w.ground, self.y + 300 * w.scale * dt)
            self.ground_time += dt
            if self.ground_time > 25:  # left lying about: it makes its own way home
                self.state = "returning"
        elif self.state == "returning":
            self.carried_by = None
            if self._fly(*self.home, dt, speed=380):
                w.message_home(self)
