"""The oak (all four seasons, and what clicking it shakes out) and the birch."""
import math

from pet import sprites
from pet.things import Thing
from .base import Leaf, SnowClump, Twig


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
        return self.look in ("oak_winter", "oak_snow")

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
