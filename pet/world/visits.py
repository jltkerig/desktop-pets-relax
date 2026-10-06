"""Who turns up, and when: falling leaves and acorns, and visitors by season (the owl at night)."""
from pet import seasons
from pet.fox import Step, ZOOM
from pet.items import Acorn, Leaf
from pet.visitors import (
    Beetle, Cicada, Flutterby, Frog, Goose, Jay, Owl, Squirrel, Woolly, bunnies, crow_party, migrating_v,
    songbirds, turkey_flock, winter_birds)
from .core import LEAF_COLOURS


class Visits:
    """Part of World (see pet/world/__init__.py)."""

    def _spawn(self, dt):
        rng, tree = self.rng, self.tree()
        for key in self.timers:
            self.timers[key] -= dt
        if tree is not None and self.timers["leaf"] <= 0:
            if self.season == "autumn":
                # the wind strips leaves off the oak much faster
                self.timers["leaf"] = rng.uniform(0.7, 2.6) / (1 + self.wind * 6)
                if len(self.of("leaf")) < 28 + int(self.wind * 30):
                    x, y = tree.crown_point()
                    self.add(Leaf(self, x, y, rng.choice(LEAF_COLOURS)))
            elif self.season == "summer":  # a green leaf now and then, but rarely
                self.timers["leaf"] = rng.uniform(40, 120) / (1 + self.wind * 4)
                self.add(Leaf(self, *tree.crown_point(), "green"))
            else:
                self.timers["leaf"] = 30.0  # bare branches: no leaves to fall
        if self.wind > 0.4 and self.season == "autumn" and rng.random() < dt * self.wind * 1.5 and \
                len(self.of("leaf")) < 60:
            # leaves blowing in from somewhere off the screen, on the upwind side
            x = -20.0 if self.wind_dir > 0 else self.width + 20.0
            self.add(Leaf(self, x, self.ground - rng.uniform(40, 260) * self.scale, rng.choice(LEAF_COLOURS)))
        if tree is not None and self.timers["acorn"] <= 0 and self.season == "autumn":
            self.timers["acorn"] = rng.uniform(40, 120)
            if len(self.nuts()) < 4:
                self.drop_acorn(tree)
        if self.timers["visitor"] <= 0:
            self.timers["visitor"] = rng.uniform(50, 160)
            self.invite_visitor()

    def drop_acorn(self, tree):
        """An acorn falls; a fox napping under the tree is a likely target."""
        sleeper = next((f for f in self.of("fox") if f.asleep and self._under(tree, f.x)), None)
        if sleeper is not None and self.rng.random() < 0.6:
            head = sleeper.x + 12 * self.scale * sleeper.facing
            x, y = head, tree.y - 100 * self.scale
        else:
            x, y = tree.crown_point()
        return self.add(Acorn(self, x, y))

    def invite_visitor(self, kind=None):
        allowed = seasons.VISITORS.get(self.season, ())
        if (self.daylight() == "night" and kind is None) or kind == "owl":
            allowed = ("owl",)  # the squirrel, the birds and the rest are tucked up at night: only the owl's about
        choices = [k for k in allowed if not self.of(k)]
        if "owl" in choices and not (self.of("tree") or self.of("birch")):
            choices.remove("owl")  # it needs a tree to sit in
        acorns = [a for a in self.of("acorn") if a.on_ground and not a.taken]
        if "squirrel" in choices and not acorns:
            choices.remove("squirrel")
        for needs_oak in ("jay", "junebug", "ladybug", "cicada"):
            if needs_oak in choices and self.tree() is None:
                choices.remove(needs_oak)
        for bug in ("junebug", "ladybug", "cicada"):
            if bug in choices and (self.of("beetle") or self.of("cicada")):
                choices.remove(bug)  # one little creature on the trunk at a time
        if "geese" in choices and self.of("goose"):
            choices.remove("geese")
        if "migrants" in choices and self.of("migrant"):
            choices.remove("migrants")
        if "turkeys" in choices and self.of("turkey"):
            choices.remove("turkeys")
        if "crows" in choices and self.of("crow"):
            choices.remove("crows")
        if "butterflies" in choices and self.of("butterfly"):
            choices.remove("butterflies")
        if "songbirds" in choices and self.of("songbird"):
            choices.remove("songbirds")
        if "winterbirds" in choices and self.of("songbird"):
            choices.remove("winterbirds")
        if "bunnies" in choices and self.of("bunny"):
            choices.remove("bunnies")
        if kind is not None:
            choices = [kind] if kind in choices else []
        if not choices:
            return None
        pick = self.rng.choice(choices)
        if kind is None and "crows" in choices and self.cobs_on_ground() and self.rng.random() < 0.8:
            pick = "crows"  # corn lying about: the crows are never far away
        if pick == "owl":
            return self.add(Owl(self))
        if pick == "squirrel":
            # squirrels much prefer acorns; a corn cob only now and then, or if there's nothing else
            nuts = [a for a in acorns if not getattr(a, "is_cob", False)]
            cobs = [a for a in acorns if getattr(a, "is_cob", False)]
            pool = nuts if nuts and (not cobs or self.rng.random() < 0.85) else cobs
            return self.add(Squirrel(self, self.rng.choice(pool)))
        if pick == "jay":
            return self.add(Jay(self, self.tree()))
        if pick == "migrants":
            return [self.add(goose) for goose in migrating_v(self)][0]
        if pick == "turkeys":
            return [self.add(turkey) for turkey in turkey_flock(self)][0]
        if pick == "crows":
            return [self.add(crow) for crow in crow_party(self)][0]
        if pick == "butterflies":
            return [self.add(Flutterby(self)) for _ in range(self.rng.randint(1, 3))][0]
        if pick == "songbirds":
            return [self.add(bird) for bird in songbirds(self)][0]
        if pick in ("junebug", "ladybug"):
            return self.add(Beetle(self, self.tree(), pick))
        if pick == "cicada":
            return self.add(Cicada(self, self.tree()))
        if pick == "winterbirds":
            return [self.add(bird) for bird in winter_birds(self)][0]
        if pick == "bunnies":
            return [self.add(bunny) for bunny in bunnies(self)][0]
        if pick == "frog":  # by the water if there is some: the pool, the cattails, a puddle
            water = [p for p in self.of("prop") if p.variant == "pool"] + \
                [c for c in self.of("crop") if c.variant == "cattails"] + self.of("puddle")
            spot = self.rng.choice(water).x + self.rng.uniform(-50, 50) * self.scale if water else \
                self.rng.uniform(0.2, 0.8) * self.width
            return self.add(Frog(self, max(30.0, min(self.width - 30.0, spot)), visiting=True))
        if pick == "geese":
            foxes = self.of("fox")
            centre = self.rng.choice(foxes).x if foxes else self.width * 0.5
            gaggle = []
            for i in range(self.rng.randint(2, 3)):
                land = centre + (90 + i * 34) * self.scale * self.rng.choice((-1, 1))
                land = max(50.0, min(self.width - 50.0, land))
                gaggle.append(self.add(Goose(self, land, delay=i * 0.7)))
            return gaggle[0]
        return self.add(Woolly(self))

    def honk(self, goose):
        """Foxes near a honking goose react, happily."""
        for fox in self.of("fox"):
            if abs(fox.x - goose.x) < 500 * self.scale / 2:
                fox.hear_honk(goose.x)

    def chase_squirrel(self, squirrel):
        """A squirrel ran off with the corn cob: the nearest awake fox gives chase."""
        foxes = [f for f in self.of("fox") if not f.asleep and not f.held and not f.up_high and not f.vy]
        if not foxes:
            return
        fox = min(foxes, key=lambda f: abs(f.x - squirrel.x))
        fox.do(Step("tilt", face=squirrel.x), Step("run", follow=squirrel, speed=ZOOM * 0.8),
               Step("hop"), Step("happy", 1.2))

    def visitor_to_watch(self, fox):
        for kind in ("squirrel", "jay", "woolly", "goose", "frog", "turkey", "crow", "inchworm", "butterfly",
                     "beetle", "cicada", "spider", "songbird", "owl", "bunny"):
            for v in self.of(kind):
                if v not in fox.watched and abs(v.x - fox.x) < 600 * self.scale / 2 and 0 < v.x < self.width:
                    return v
        return None
