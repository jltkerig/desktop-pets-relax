"""Things that stand about: props (scarecrow, hoe, sled, Christmas tree, flower beds, apple barrel, well,
pool...), the scarecrow's hat, songbird notes, the den and its z's, and the things foxes climb."""
import math

from pet import sprites
from pet.things import Thing
from .base import Fluff, GRAVITY, SnowClump, StrawBit
from .garden import Produce


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
