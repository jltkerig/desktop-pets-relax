"""Winter things: the snowman (and his carrot nose, which the foxes pinch), the pile of snowballs (and the
snowballs you throw), the frozen pond, the bird feeder, and the gift boxes the foxes hide in."""
from .base import Kernel, SnowClump
from .garden import Produce
from .play import Ball, YardThing


class Snowman(YardThing):
    """A snowman with a carrot nose. A fox may pinch the carrot and run off with it; drop it (or throw it) back
    on his face, or click it, and it goes back on. If it gets lost (eaten!), he finds a new one after a while.
    On a winter day without snow he slumps a little, melting."""
    z = 7
    NOSE = (6, 33)  # where his nose is: sideways from his middle, and up, in sprite pixels
    NEW_NOSE_AFTER = 45  # seconds after his carrot is lost for good

    def __init__(self, world, x, variant="snowman"):
        self.nose_on = True
        self.carrot = None
        self.noseless_for = 0.0
        super().__init__(world, x, variant)

    @property
    def look(self):
        return "snowman" + ("" if self.world.snowy else "_melty") + ("" if self.nose_on else "_nonose")

    def nose_point(self):
        s = self.world.scale
        return self.x + self.NOSE[0] * s, self.y - self.NOSE[1] * s

    def take_nose(self, fox):
        """A fox pinches the carrot: it's in its mouth now."""
        if not self.nose_on:
            return None
        self.nose_on = False
        self.carrot = self.world.add(Carrot(self.world, *self.nose_point(), self))
        self.carrot.carried_by, fox.carrying = fox, self.carrot
        self.react()
        return self.carrot

    def nose_back(self):
        if self.carrot is not None:
            self.carrot.gone = True
            if self.carrot.carried_by is not None and self.carrot.carried_by.carrying is self.carrot:
                self.carrot.carried_by.carrying = None
        self.carrot, self.nose_on, self.noseless_for = None, True, 0.0
        self.react()

    def update(self, dt):
        if not self.nose_on and (self.carrot is None or self.carrot.gone):
            self.noseless_for += dt  # lost (or eaten): a new carrot turns up after a while
            if self.noseless_for > self.NEW_NOSE_AFTER:
                self.carrot = None
                self.nose_back()
        super().update(dt)


class Carrot(Produce):
    """The snowman's nose, pinched by a fox: carried about in its mouth, then dropped. You can pick it up and
    throw it like a corn cob; let it go near his face (or click it) and it's back on. The foxes might eat it."""

    def __init__(self, world, x, y, snowman):
        super().__init__(world, x, y, "carrot", "carrot_bit")
        self.snowman = snowman
        self.carried_by = None  # a fox, with it in its mouth

    @property
    def draggable(self):
        return self.carried_by is None and not self.carried

    def click(self):
        if not self.snowman.gone:
            self.snowman.nose_back()

    def throw(self, vx, vy):
        super().throw(vx, vy)
        nx, ny = self.snowman.nose_point()
        s = self.world.scale
        if not self.snowman.gone and abs(self.x - nx) < 18 * s and abs(self.y - ny) < 18 * s:
            self.snowman.nose_back()  # right back where it belongs

    def update(self, dt):
        fox = self.carried_by
        if fox is not None:
            if fox.gone or fox.held or fox.carrying is not self:
                self.carried_by = None
                if fox.carrying is self:
                    fox.carrying = None
            else:
                s = self.world.scale
                self.facing = fox.facing
                self.x, self.y = fox.x + fox.facing * 24 * s, fox.y - 12 * s
                self.on_ground, self.vx, self.vy = False, 0.0, 0.0
                return
        super().update(dt)


class SnowballPile(YardThing):
    """A heap of snowballs. Drag one up off the top to throw it (drag sideways to move the heap), or click it
    and a snowball pops up into the air."""
    z = 8

    def top(self):
        return self.x, self.y - 14 * self.world.scale

    def lift(self):
        """A snowball off the top, into your hand."""
        return self.world.add(Snowball(self.world, *self.top()))

    def click(self):
        w, s = self.world, self.world.scale
        ball = w.add(Snowball(w, *self.top()))
        ball.throw(w.rng.uniform(-160, 160) * s, -w.rng.uniform(380, 480) * s)


class Snowball(Ball):
    """A snowball: thrown, it flies, and bursts into a puff of snow when it lands (or hits a fox, who doesn't
    mind a bit)."""
    GRAVITY = 1000

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "snowball")

    def burst(self):
        w, s = self.world, self.world.scale
        for dx in (-3, 3):
            puff = w.add(SnowClump(w, self.x + dx * s, min(self.y, w.ground)))
            puff.delay, puff.vy, puff.landed_for = 0.0, 0.0, 0.0
            puff.anim.play("snow_puff")
        self.gone = True

    def landed(self, speed):
        self.burst()
        return False

    def update(self, dt):
        if not self.held:
            for fox in self.world.of("fox"):
                if fox.alpha > 0 and not fox.held and fox.contains(self.x, self.y - 3 * self.world.scale):
                    self.world.snowball_hit(fox)
                    self.burst()
                    return
        super().update(dt)


class Pond(YardThing):
    """A frozen pond: a flat oval of ice. Foxes skid across it. Click it and the light glints over the ice."""
    z = 2

    def click(self):
        self.react("glint")


class Feeder(YardThing):
    """A bird feeder on a post. In winter, cardinals and chickadees come to it (see visitors/winter.py), and the
    foxes stalk them. Click it and it swings, spilling a little seed."""
    z = 7
    SNOWY = True
    PERCHES = [(-8, 30), (8, 30)]  # the ends of its seed tray (sideways, up), for the birds

    def click(self):
        w, s = self.world, self.world.scale
        self.react()
        for _ in range(4):
            w.add(Kernel(w, self.x + w.rng.uniform(-8, 8) * s, self.y - 29 * s, "seed_bit"))


class Gifts(YardThing):
    """Presents under the tree. A fox may dive into the big box and hide, its tail sticking out; click the
    presents and out it pops."""
    z = 9

    def __init__(self, world, x, variant="gifts"):
        self.hider = None  # the fox hiding inside
        super().__init__(world, x, variant)

    @property
    def look(self):
        return f"gifts_{self.hider.palette}" if self.hider is not None else "gifts"

    def click(self):
        if self.hider is not None:
            self.hider.poke()  # surprise!
        else:
            self.react()

    def update(self, dt):
        if self.hider is not None and (self.hider.gone or self.hider.hiding_in is not self):
            self.hider = None
        super().update(dt)
