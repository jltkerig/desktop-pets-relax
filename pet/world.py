"""Everything on the desktop and the rules between them. No Qt here, so it can be tested."""
import datetime
import math
import random

from pet import daylight, seasons, sprites
from pet.fox import TROT, WALK, ZOOM, Fox, Step
from pet.items import (Acorn, Birch, Climbable, Corn, CornCob, Crop, Den, Firefly, Glow, Kernel, Leaf, Melon,
                       Message, Prop, Pumpkin, Treasure, Tree)
from pet.visitors import (Beetle, Cicada, Flutterby, Goose, Jay, Owl, Squirrel, Woolly, crow_party, migrating_v,
                          songbirds, turkey_flock)

LEAF_COLOURS = ("red", "orange", "yellow", "brown")


class World:
    def __init__(self, width, height, settings, rng=None, clock=None, seams=()):
        self.width, self.height = width, height
        self.ground = height - 2  # the taskbar's top edge (the window ends there)
        self.settings = settings
        self.scale = settings.get("scale", 2)
        self.rng = rng or random.Random()
        self.clock = clock or datetime.datetime.now
        self.things = []
        self.cursor = (-1000.0, -1000.0)
        self.cursor_still = 0.0
        self.timers = {"leaf": 1.0, "acorn": self.rng.uniform(20, 50), "visitor": self.rng.uniform(25, 60)}
        self.paused = False
        self.wind = 0.0             # 0 calm .. 1 a strong gust
        self.wind_dir = 1           # which way it blows: 1 left to right, -1 right to left
        self.blustery_left = 0.0    # seconds of blustery weather still to come
        self.weather_timer = self.rng.uniform(15 * 60, 60 * 60)  # until the next chance of a blustery spell
        self.seams = list(seams)
        self.dirty = False  # settings changed here (pumpkins planted); the window saves them
        self.weather = None         # the local weather report (pet/weather.py), set by the window; None: no idea
        self.shower = (None, 0.0)   # ("rain" | "snow", seconds left): a shower asked for from the tray menu
        # self.seams: where one monitor ends and the next begins, along the strip
        self.taskbar_spots = []   # x of each taskbar icon, filled in by the window
        self.images = {}          # treasure key -> picture of the icon (set by the window)
        self.grab_requests = []   # (treasure key, x) the window should copy the icon for
        self.discord_spot = None  # where a Discord message could be stolen from (set by the window), along the strip
        self.discord_active = False  # you're using Discord right now (it's in front and you're typing)
        self.screen_requests = []  # ("steal" | "restore", message key) for the window to act on
        self._treasures = 0
        self.rebuild()

    # -- setup -----------------------------------------------------------------------------------------

    def now(self):
        return self.clock()

    def daylight(self):
        """'night', 'dawn', 'day' or 'dusk' (from sunrise and sunset; worked out at most once a minute)."""
        minute = self.now().replace(second=0, microsecond=0)
        if getattr(self, "_daylight_at", None) != minute:
            self._daylight_at = minute
            self._daylight = daylight.phase(self.now(), self.settings)
        return self._daylight

    @property
    def season(self):
        chosen = self.settings.get("season", "auto")
        return seasons.season_for(self.now().date()) if chosen == "auto" else chosen

    @property
    def snowed_over(self):
        """Snow lying on everything: a snowy winter day."""
        return self.season == "winter" and self.snowy

    @property
    def snowy(self):
        """Is there snow on the oak? You can choose from the tray menu; otherwise, if the local weather is known,
        whether there's snow on the ground where you are, or else it snows on some winter days and not others
        (the same all day)."""
        chosen = self.settings.get("snow", "auto")
        if chosen in (True, False):
            return chosen
        if self.weather is not None:  # the real thing: is there snow on the ground where you are?
            return self.weather.snow_on_ground
        return random.Random(self.now().date().toordinal()).random() < 0.6

    def resize(self, width, height):
        """The monitors changed: stretch or shrink the strip, keep everything on the ground and on screen."""
        old_ground = self.ground
        self.width, self.height = width, height
        self.ground = height - 2
        for thing in self.things:
            thing.y += self.ground - old_ground
            thing.x = max(20.0, min(width - 20.0, thing.x))
        self.taskbar_spots = []

    ITEM_KINDS = ("tree", "prop", "corn", "den", "climb", "pumpkin", "birch", "melon", "crop")

    def add(self, thing):
        self.things.append(thing)
        if thing.kind in self.ITEM_KINDS:
            self.keep_off_seams(thing)
        return thing

    def keep_off_seams(self, thing):
        """An item across the gap between two monitors slides fully onto the one holding most of it."""
        for seam in self.seams:
            left, _, w, _ = thing.rect()
            if left < seam < left + w:
                if seam - left >= left + w - seam:
                    thing.x -= (left + w - seam) + 4   # mostly on the left monitor: all of it goes there
                else:
                    thing.x += (seam - left) + 4       # mostly on the right
        return thing

    def set_seams(self, seams):
        """The monitors changed: remember the gaps and move any item sitting across one."""
        self.seams = list(seams)
        for thing in self.things:
            if thing.kind in self.ITEM_KINDS and not thing.gone:
                self.keep_off_seams(thing)

    def of(self, kind):
        return [t for t in self.things if t.kind == kind and not t.gone]

    def nuts(self):
        """The acorns about (not the corn cobs, which are acorns of a sort too)."""
        return [a for a in self.of("acorn") if not getattr(a, "is_cob", False)]

    def cobs_on_ground(self):
        return [a for a in self.of("acorn") if getattr(a, "is_cob", False) and a.on_ground and not a.taken]

    def tree(self):
        trees = self.of("tree")
        return trees[0] if trees else None

    def rebuild(self):
        """Put out exactly what the settings and season ask for, keeping things that should stay."""
        season = self.season
        wanted_items = {name for name, item in self.settings["items"].items()
                        if item.get("out") and name in seasons.items_for(season)}
        for thing in self.of("tree"):
            if thing.variant not in wanted_items:
                thing.gone = True
        if "pumpkins" in wanted_items:
            if not self.of("pumpkin"):
                self.grow_pumpkins()
        else:
            for thing in self.of("pumpkin"):
                thing.gone = True
        if "corn" in wanted_items:
            if not self.of("corn"):
                self.plant_corn()
        else:
            for thing in self.of("corn"):
                thing.gone = True
        if "watermelons" in wanted_items:
            if not self.of("melon"):
                self.grow_melons()
        else:
            for thing in self.of("melon"):
                thing.gone = True
        for name in self.CROP_SPOTS:  # tomatoes, radishes, lettuce, cattails
            have = [t for t in self.of("crop") if t.variant == name]
            if name in wanted_items and not have:
                self.plant_crop(name)
            elif name not in wanted_items:
                for thing in have:
                    thing.gone = True
        if "den" in wanted_items:
            if not self.of("den"):
                x = self.settings["items"]["den"].get("x")
                if not (isinstance(x, (int, float)) and 0 < x < self.width):
                    x = self.width * 0.5
                self.add(Den(self, x))
        else:
            for thing in self.of("den"):
                for fox in thing.sleepers:
                    fox.leave_den()
                thing.gone = True
        climbables = {"barrels": 0.88, "haystack": 0.42, "stump": 0.04,  # where each goes the first time
                      "woodstack": 0.38, "slide": 0.355}
        for thing in self.of("climb"):
            if thing.variant not in wanted_items:
                thing.gone = True
        for name, share in climbables.items():
            if name in wanted_items and not any(t.variant == name for t in self.of("climb")):
                x = self.settings["items"][name].get("x")
                if not (isinstance(x, (int, float)) and 0 < x < self.width):
                    x = self.width * share
                self.add(Climbable(self, x, name, self.settings["items"][name].get("layout")))
        props = {"scarecrow", "hoe", "sled", "xmas_tree", "daffodils", "tulips", "violets", "apple_barrel", "well",
                 "pool", "dahlias", "dandelions"}
        first_spot = {"sled": 0.62, "xmas_tree": 0.3,  # where the seasonal things go the first time
                      "daffodils": 0.25, "tulips": 0.66, "violets": 0.78, "apple_barrel": 0.62, "well": 0.375,
                      "pool": 0.65, "dahlias": 0.8, "dandelions": 0.31}
        for thing in self.of("prop"):
            if thing.variant not in wanted_items:
                thing.gone = True
        for name in sorted(wanted_items & props):  # (sorted: the same order every run)
            if not any(t.variant == name for t in self.of("prop")):
                x = self.settings["items"][name].get("x")
                if not (isinstance(x, (int, float)) and 0 < x < self.width):
                    patch = self.settings["items"].get("pumpkins", {}).get("patch") or []
                    xs = [p["x"] for p in patch if isinstance(p, dict) and isinstance(p.get("x"), (int, float))]
                    if name in first_spot:
                        x = self.width * first_spot[name]
                    elif name == "hoe":  # leaning by the patch, on its left
                        x = (min(xs) - 34 * self.scale) if xs else self.width * 0.22
                    else:              # the scarecrow keeps watch on the right
                        x = (max(xs) + 70 * self.scale) if xs else self.width * 0.32
                    x = max(40.0, min(self.width - 40.0, x))
                self.add(Prop(self, x, name))
        if "oak" in wanted_items and not self.of("tree"):
            x = self.settings["items"]["oak"].get("x")
            x = x if isinstance(x, (int, float)) and 0 < x < self.width else self.width * 0.72
            self.add(Tree(self, x, "oak"))
        if "birch" in wanted_items:
            if not self.of("birch"):
                x = self.settings["items"]["birch"].get("x")
                x = x if isinstance(x, (int, float)) and 0 < x < self.width else self.width * 0.585
                self.add(Birch(self, x))
        else:
            for thing in self.of("birch"):
                thing.gone = True
        if "oak" not in wanted_items:  # autumn leftovers go when the tree does
            for thing in self.things:
                if thing.kind in ("leaf", "acorn", "squirrel", "jay", "twig", "snow", "inchworm", "butterfly",
                                  "beetle", "cicada", "spider", "silk"):
                    thing.gone = True
        for palette, out in self.settings["foxes"].items():
            have = [f for f in self.of("fox") if f.palette == palette]
            if out and not have:
                start = self.width * (0.55 if palette == "orange" else 0.4) + self.rng.uniform(-60, 60)
                self.add(Fox(self, start, palette))
            elif not out:
                for fox in have:
                    fox.gone = True
        self.things = [t for t in self.things if not t.gone]

    def plant_corn(self, replant=False):
        """Put out the corn field: the saved one, still growing, or a freshly planted row."""
        item = self.settings["items"].setdefault("corn", {"out": True, "x": None, "planted": None})
        for thing in self.of("corn"):
            thing.gone = True
        if replant or not isinstance(item.get("planted"), (int, float)):
            item["planted"] = self.now().timestamp()
            self.dirty = True
        x = item.get("x")
        if not (isinstance(x, (int, float)) and 0 < x < self.width):
            x = self.width * 0.12  # off to the left, away from the oak
        return self.add(Corn(self, x, item["planted"]))

    def plant_crop(self, name, replant=False):
        """Put out a row of tomatoes, radishes, lettuce or cattails: the saved one, still growing, or fresh."""
        item = self.settings["items"].setdefault(name, {"out": True, "x": None, "planted": None})
        for thing in self.of("crop"):
            if thing.variant == name:
                thing.gone = True
        if replant or not isinstance(item.get("planted"), (int, float)):
            item["planted"] = self.now().timestamp()
            self.dirty = True
        x = item.get("x")
        if not (isinstance(x, (int, float)) and 0 < x < self.width):
            x = self.width * self.CROP_SPOTS[name]
        return self.add(Crop(self, x, item["planted"], name))

    CROP_SPOTS = {"tomatoes": 0.11, "cattails": 0.965, "radishes": 0.11, "lettuce": 0.19}  # where they go at first

    def grow_pumpkins(self, replant=False):
        """Put out the pumpkin patch: the saved pumpkins, or three new sprouts."""
        self.grow_patch("pumpkins", Pumpkin, 0.25, replant)

    def grow_melons(self, replant=False):
        """Put out the watermelon patch: the saved melons, or three new sprouts."""
        self.grow_patch("watermelons", Melon, 0.215, replant)

    def grow_patch(self, name, cls, share, replant=False):
        """Put out a patch of pumpkins or watermelons (cls): the saved ones, still growing, or three sprouts."""
        item = self.settings["items"].setdefault(name, {"out": True, "x": None, "patch": []})
        for thing in self.of(cls.kind):
            thing.gone = True
        patch = [p for p in item.get("patch", []) if isinstance(p, dict)
                 and isinstance(p.get("x"), (int, float)) and isinstance(p.get("planted"), (int, float))]
        sizes = ["s", "m", "l"]
        shapes = list(cls.SHAPES)
        for record in patch:  # pumpkins saved before sizes and shapes existed get them now
            if record.get("size") not in sizes:
                record["size"] = self.rng.choice(sizes)
                self.dirty = True
            if record.get("shape") not in shapes:
                record["shape"] = self.rng.choice(shapes)
                record["jack"] = self.rng.random() < 0.2
                self.dirty = True
        if replant or not patch:
            centre = item.get("x") if isinstance(item.get("x"), (int, float)) else self.width * share
            now = self.now().timestamp()
            patch = [{"x": round(max(40, min(self.width - 40, centre + (i - 1) * 46 * self.scale))),
                      "planted": now - self.rng.uniform(0, 90), "pace": round(self.rng.uniform(0.85, 1.2), 2),
                      "size": size, "shape": self.rng.choice(shapes), "jack": self.rng.random() < 0.2,
                      "giant": self.rng.random() < cls.GIANT_CHANCE}
                     for i, size in enumerate(self.rng.sample(sizes, 3))]  # one of each, in any order
            self.dirty = True
        item["patch"] = patch
        for record in patch:
            x = max(20.0, min(self.width - 20.0, float(record["x"])))
            self.add(cls(self, x, record["planted"], float(record.get("pace", 1.0)), record, record["size"],
                         record["shape"], record.get("jack", False), record.get("giant", False)))

    # -- every frame -------------------------------------------------------------------------------------

    def update(self, dt, cursor=None):
        if self.paused:
            return
        dt = min(dt, 0.1)  # after a stall, don't jump ahead
        if cursor is not None:
            moved = abs(cursor[0] - self.cursor[0]) + abs(cursor[1] - self.cursor[1]) > 3
            self.cursor_still = 0.0 if moved else self.cursor_still + dt
            self.cursor = cursor
        self._weather(dt)
        self._spawn(dt)
        for thing in list(self.things):
            thing.update(dt)
        self.leave_paw_prints()
        self.night_lights(dt)
        self.precipitation(dt)
        self.things = [t for t in self.things if not t.gone]

    def blustery(self, minutes=None):
        """Start a blustery spell now (a few minutes of gusty wind)."""
        self.blustery_left = (minutes or self.rng.uniform(3, 8)) * 60
        self.wind_dir = self.rng.choice((-1, 1))
        self._gust_phase = 0.0

    def make_it(self, kind, minutes=None):
        """A shower of rain (or snow) for a few minutes, asked for from the tray menu."""
        self.shower = (kind, (minutes or 4) * 60)

    @property
    def falling(self):
        """What's coming down: "rain", "snow" or None (a shower you asked for, else the local weather)."""
        kind, left = self.shower
        if kind and left > 0:
            return kind
        return self.weather.falling if self.weather is not None else None

    @property
    def heavy(self):
        kind, left = self.shower
        if kind and left > 0:
            return False
        return bool(self.weather is not None and self.weather.heavy)

    def precipitation(self, dt):
        """Raindrops (or snowflakes) falling over everything, and splashing (or settling) on the ground."""
        from pet.items import RainDrop, SnowFlake
        kind, left = self.shower
        if kind and left > 0:
            self.shower = (kind, left - dt)
        falling = self.falling
        if falling is None:
            return
        width = self.width / 1920
        if falling == "rain":
            rate, cap, make = (240 if self.heavy else 90) * width, int(500 * width) + 20, RainDrop
        else:
            rate, cap, make = (45 if self.heavy else 18) * width, int(220 * width) + 20, SnowFlake
        if len(self.of(make.kind)) >= cap:
            return
        count = int(rate * dt) + (1 if self.rng.random() < rate * dt % 1 else 0)
        for _ in range(count):
            self.add(make(self))

    def _weather(self, dt):
        """Every so often (about once in an hour or two) the wind gets up for a few minutes, in gusts."""
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.weather_timer = self.rng.uniform(20 * 60, 70 * 60)
            if self.blustery_left <= 0 and self.rng.random() < 0.6:
                self.blustery()
        if self.blustery_left > 0:
            self.blustery_left -= dt
            self._gust_phase = getattr(self, "_gust_phase", 0.0) + dt
            p = self._gust_phase
            # gusts come and go: a few slow waves on top of each other, never quite still
            gust = 0.55 + 0.25 * math.sin(p * 0.9) + 0.2 * math.sin(p * 2.3 + 1) + 0.1 * math.sin(p * 5.1)
            ease = min(1.0, p / 8, self.blustery_left / 8)  # builds up and dies away gently
            target = max(0.0, min(1.0, gust)) * ease
        else:
            target = 0.0
        self.wind += (target - self.wind) * min(1.0, dt * 2)

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

    # -- questions a fox asks ----------------------------------------------------------------------------

    def _under(self, tree, x):
        left, right = tree.base_range()
        return left <= x <= right

    def den(self):
        dens = self.of("den")
        return dens[0] if dens else None

    def nap_spot(self, fox):
        """The den if there is one (it curls up inside), else under the oak, else where it is. Now and then in the
        daytime, for a change, a nap in the dappled shade under the birch."""
        fox.naps = getattr(fox, "naps", 0) + 1
        birch = next(iter(self.of("birch")), None)
        if birch is not None and fox.naps % 3 == 0 and self.daylight() == "day":
            return birch.x + (14 if fox.palette == "orange" else -14) * self.scale
        den = self.den()
        if den is not None:
            return den.entrance_x()
        tree = self.tree()
        if tree is None:
            return None
        if self._under(tree, fox.x):
            return fox.x
        left, right = tree.base_range()
        return self.rng.uniform(left, right)

    def sleeping_fox_under(self, acorn):
        for fox in self.of("fox"):
            if fox.asleep:
                left, top, w, _ = fox.rect()
                if left + w * 0.3 <= acorn.x <= left + w * 0.8 and acorn.y >= top + 34 * self.scale:
                    return fox
        return None

    def nearest_fox(self, x):
        foxes = self.of("fox")
        return min(foxes, key=lambda f: abs(f.x - x)) if foxes else None

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

    def harvest(self, corn):
        """Ripe corn clicked: an ear of corn drops from every stalk, and the field starts again. All that corn on
        the ground soon brings the crows."""
        for x, y in corn.ears():
            cob = self.add(CornCob(self, x, y))
            cob.vx = self.rng.uniform(-25, 25) * self.scale
        self.plant_corn(replant=True)
        if self.daylight() != "night" and "crows" in seasons.VISITORS.get(self.season, ()):
            self.timers["visitor"] = min(self.timers["visitor"], self.rng.uniform(8, 25))

    def dropped(self, thing):
        """Something you dragged was let go. The hoe, let go on a ripe pumpkin, carves it a face."""
        if thing.kind == "prop" and thing.variant == "hoe":
            near = [p for p in self.of("pumpkin") if abs(p.x - thing.x) < 30 * self.scale]
            pumpkin = min(near, key=lambda p: abs(p.x - thing.x)) if near else None
            if pumpkin is not None:
                thing.react()  # a thunk, carved or not
                if not pumpkin.carve():
                    pumpkin.anim.time += 0.7

    def visitor_to_watch(self, fox):
        for kind in ("squirrel", "jay", "woolly", "goose", "frog", "turkey", "crow", "inchworm", "butterfly",
                     "beetle", "cicada", "spider", "songbird", "owl"):
            for v in self.of(kind):
                if v not in fox.watched and abs(v.x - fox.x) < 600 * self.scale / 2 and 0 < v.x < self.width:
                    return v
        return None

    def acorn_near(self, fox, reach):
        acorns = [a for a in self.of("acorn") if a.on_ground and not a.taken and abs(a.x - fox.x) < reach * self.scale / 2]
        return min(acorns, key=lambda a: abs(a.x - fox.x)) if acorns else None

    def leaf_near(self, fox, reach):
        leaves = [l for l in self.of("leaf") if l.falling and not getattr(l, "chased", False)
                  and abs(l.x - fox.x) < reach * self.scale / 2 and l.y > self.ground - 170 * self.scale]
        return min(leaves, key=lambda l: abs(l.x - fox.x)) if leaves else None

    def chase_leaf(self, fox, leaf):
        """Run under a falling leaf, crouch, and pounce on it as it comes down."""
        leaf.chased = True
        side = 1 if leaf.x >= fox.x else -1
        under = max(40.0, min(self.width - 40.0, leaf.x - side * 22 * self.scale))
        fox.do(Step("trot", to_x=under, speed=TROT * 1.15), Step("crouch", self.rng.uniform(0.3, 0.7), face=leaf.x),
               Step("pounce", to_x=leaf.x, leap=30, then=lambda: self.catch_leaf(fox, leaf)), Step("dive"),
               Step("hop"), Step("happy", 1.0))

    def catch_leaf(self, fox, leaf):
        """The pounce lands: a leaf close by is caught (it disappears under the paws)."""
        if not leaf.gone and abs(leaf.x - fox.x) < 40 * self.scale:
            leaf.gone = True
        leaf.chased = False

    def cursor_to_pounce(self, fox):
        """The cursor resting near the ground, not too far away: something to pounce on."""
        x, y = self.cursor
        if self.cursor_still > 1.5 and self.ground - 90 * self.scale < y <= self.ground + 2 and \
                40 * self.scale < abs(x - fox.x) < 260 * self.scale:
            return x
        return None

    def friend_to_play(self, fox):
        for other in self.of("fox"):
            if other is not fox and not other.asleep and not other.held and other.busy_with is None and \
                    abs(other.x - fox.x) < 420 * self.scale / 2 and other.playful > 0.35:
                return other
        return None

    # -- foxes together ---------------------------------------------------------------------------------

    SHOWING_OFF = ("run", "pounce", "dive", "roll", "playbow", "dig", "hop", "bat")

    def friends(self, fox):
        """The other foxes out (any number), nearest first."""
        return sorted((f for f in self.of("fox") if f is not fox), key=lambda f: abs(f.x - fox.x))

    def free_friend(self, fox, reach=1400):
        """An awake friend that isn't busy with something else, within reach (sprite pixels)."""
        for other in self.friends(fox):
            if not other.asleep and not other.held and not other.vy and not other.up_high and \
                    other.busy_with is None and other.carrying is None and abs(other.x - fox.x) < reach * self.scale / 2:
                return other
        return None

    def friend_showing_off(self, fox):
        """A friend nearby doing something worth watching (zoomies, a pounce, a roll...)."""
        for other in self.friends(fox):
            if other.step is not None and other.step.anim in self.SHOWING_OFF and \
                    abs(other.x - fox.x) < 1200 * self.scale / 2:
                return other
        return None

    def sleeping_friend(self, fox):
        """A friend asleep out in the open (not in the den), to curl up beside."""
        for other in self.friends(fox):
            if other.asleep and not other.in_den:
                return other
        return None

    def _together(self, a, b):
        a.busy_with, b.busy_with = b, a

        def apart():
            if a.busy_with is b:
                a.busy_with = None
            if b.busy_with is a:
                b.busy_with = None
        return apart

    def _beside(self, fox, friend):
        """Where fox should stand to be next to friend, facing it, on the side it's coming from."""
        side = -1 if fox.x < friend.x else 1
        return max(40.0, min(self.width - 40.0, friend.x + side * 34 * self.scale))

    def _walk_time(self, fox, x):
        """Seconds for fox to walk to x (so a friend knows how long to wait)."""
        return abs(x - fox.x) / (WALK * self.scale) + 0.4

    def greet(self, fox, friend):
        """Walk over and boop noses; both wag happily."""
        apart = self._together(fox, friend)
        spot = self._beside(fox, friend)
        friend.do(Step("look", face=fox.x), Step("idle", self._walk_time(fox, spot), face=fox.x), Step("boop", face=fox.x),
                  Step("happy", 1.2, face=fox.x))
        fox.do(Step("walk", to_x=spot, speed=WALK), Step("boop", face=friend.x), Step("happy", 1.2, face=friend.x),
               Step("idle", 1.5, face=friend.x, then=apart))

    def groom_friend(self, fox, friend):
        """Sit beside the friend and lick its fur; it leans in, eyes closed."""
        apart = self._together(fox, friend)
        spot = self._beside(fox, friend)
        friend.do(Step("idle", self._walk_time(fox, spot), face=fox.x), Step("petted", 5.0, face=fox.x), Step("happy", 1.0))
        fox.do(Step("walk", to_x=spot, speed=WALK), Step("groom", 5.0, face=friend.x),
               Step("idle", 2.0, face=friend.x, then=apart))

    def tag_along(self, fox, friend):
        """Follow the friend on a little stroll, then sit down beside it."""
        apart = self._together(fox, friend)
        stroll = max(60.0, min(self.width - 60.0, friend.x + self.rng.choice((-1, 1)) * self.rng.uniform(120, 260) * self.scale))
        friend.do(Step("walk", to_x=stroll, speed=WALK), Step("idle", 8.0), Step("look"))
        fox.do(Step("look", face=friend.x), Step("trot", follow=friend, speed=TROT),
               Step("idle", 4.0, face=friend.x, then=apart))

    def watch_friend(self, fox, friend):
        """Sit and watch the friend's antics, head tilting."""
        fox.do(Step("watch", self.rng.uniform(3, 6), face=friend.x), Step("tilt", face=friend.x), Step("happy", 0.8))

    def snuggle(self, fox, friend):
        """Curl up to sleep right beside a sleeping friend."""
        night = self.daylight() == "night"
        spot = self._beside(fox, friend)
        fox.do(Step("walk", to_x=spot, speed=WALK), Step("yawn"),
               Step("sleep", self.rng.uniform(150, 360) * (3 if night else 1), face=friend.x))

    def play_together(self, fox, friend):
        """A play bow, then a chase: the friend runs off, the fox follows, they meet with a nose boop."""
        fox.busy_with, friend.busy_with = friend, fox
        away = 1 if friend.x >= fox.x else -1
        run_to = max(60.0, min(self.width - 60.0, friend.x + away * self.rng.uniform(140, 260) * self.scale))
        meet = run_to - away * 30 * self.scale

        def done():
            fox.busy_with = friend.busy_with = None

        friend.do(Step("tilt", face=fox.x), Step("playbow", 1.2, face=fox.x),
                  Step("trot", to_x=run_to, speed=TROT * 1.1), Step("idle", 0.6, face=fox.x),
                  Step("boop", face=fox.x), Step("happy", 1.2, face=fox.x))
        fox.do(Step("playbow", 1.4, face=friend.x), Step("trot", to_x=meet, speed=TROT),
               Step("boop", face=run_to), Step("roll", 1.6), Step("happy", 1.0, then=done))

    def pumpkin_near(self, fox, reach):
        ripe = [p for p in self.of("pumpkin") if p.ripe and abs(p.x - fox.x) < reach * self.scale / 2]
        return min(ripe, key=lambda p: abs(p.x - fox.x)) if ripe else None

    def treasure_spot(self, fox):
        """A taskbar icon to dig at, not too far away."""
        if not self.mischief("treasure"):
            return None
        near = [x for x in self.taskbar_spots if abs(x - fox.x) < 700 * self.scale / 2]
        spots = near or self.taskbar_spots
        return self.rng.choice(spots) if spots else None

    def dig_for_treasure(self, fox, spot=None):
        """Walk over an icon, dig, "find" a copy of it and run off with it."""
        spot = spot if spot is not None else self.treasure_spot(fox)
        if spot is None:
            return False
        side = 1 if spot >= fox.x else -1
        stand = spot - side * 24 * self.scale
        run_to = max(60.0, min(self.width - 60.0, stand - side * self.rng.uniform(160, 320) * self.scale))
        if abs(run_to - stand) < 80:
            run_to = max(60.0, min(self.width - 60.0, stand + side * 200 * self.scale))
        fox.do(Step("walk", to_x=stand, speed=WALK), Step("sniff", face=spot), Step("sniff", face=spot),
               Step("dig", self.rng.uniform(2.0, 3.2), face=spot, then=lambda: self.find_treasure(fox, spot)),
               Step("hop", face=spot), Step("trot", to_x=run_to, speed=TROT * 1.2, then=lambda: self.drop_treasure(fox)),
               *self._after_treasure())
        return True

    # -- Discord mischief -------------------------------------------------------------------------------

    def mischief(self, kind):
        return bool(self.settings.get("mischief", {}).get(kind, True))

    def steal_message(self, fox):
        """Sit under a Discord message, leap, pull it down, run off and play with it, then put it back."""
        spot = self.discord_spot
        if spot is None or self.of("message") or not self.mischief("discord"):
            return False
        self._treasures += 1
        key = f"message{self._treasures}"
        msg = self.add(Message(self, key, (spot["x"], spot["y"])))
        self.screen_requests.append(("steal", key))
        under = max(40.0, min(self.width - 40.0, spot["x"] - 20 * self.scale))
        side = 1 if under < self.width / 2 else -1
        away = max(60.0, min(self.width - 60.0, under + side * self.rng.uniform(220, 420) * self.scale))
        back = max(40.0, min(self.width - 40.0, spot["x"] - 20 * self.scale))

        def yank():
            if not msg.gone:
                msg.carried_by, msg.state = fox, "falling"
                fox.carrying = msg

        def drop():
            if msg.state == "carried":
                msg.state, msg.carried_by = "ground", None
                msg.ground_time = 0.0
            fox.carrying = None

        def pick_up():
            if not msg.gone and msg.state == "ground":
                msg.carried_by, msg.state = fox, "carried"
                fox.carrying = msg

        def send_home():
            fox.carrying = None
            if not msg.gone:
                msg.carried_by, msg.state = None, "returning"

        if self.discord_active:  # you're chatting: a quick grab, a victory hop, and straight back
            msg.limit = 25.0
            fox.do(Step("trot", to_x=under, speed=TROT), Step("crouch", 0.5, face=spot["x"]),
                   Step("hop", face=spot["x"], then=yank), Step("happy", 1.5), Step("hop"), Step("happy", 1.0),
                   Step("hop", face=spot["x"], then=send_home), Step("tilt", face=spot["x"]))
            return True
        fox.do(Step("walk", to_x=under, speed=WALK), Step("look", face=spot["x"]), Step("crouch", 0.8, face=spot["x"]),
               Step("hop", face=spot["x"], then=yank), Step("happy", 0.8),
               Step("trot", to_x=away, speed=TROT * 1.3, then=drop), Step("playbow", 1.0), Step("roll", 1.8),
               Step("happy", 1.0), Step("idle", self.rng.uniform(3, 6)),
               Step("walk", follow=msg, speed=WALK, then=pick_up),
               Step("walk", to_x=back, speed=WALK), Step("hop", face=spot["x"], then=send_home),
               Step("happy", 1.0), Step("tilt", face=spot["x"]))
        return True

    def message_home(self, msg):
        """The message is back in its place: take the cover away."""
        msg.gone = True
        self.screen_requests.append(("restore", msg.key))
        for fox in self.of("fox"):
            if fox.carrying is msg:
                fox.carrying = None

    def cancel_message(self, key):
        """Something changed on screen (the window moved, say): the stolen picture just vanishes."""
        for msg in self.of("message"):
            if msg.key == key:
                self.message_home(msg)

    def _after_treasure(self):
        """What it does with its prize: sometimes plays, sometimes settles down to chew it up."""
        if self.rng.random() < 0.5:
            return [Step("sniff"), Step("chew", self.rng.uniform(4.5, 6.0)), Step("happy", 1.2), Step("groom", 2.0)]
        return [Step("playbow", 1.0), Step("roll", 1.6), Step("happy", 1.2)]

    def find_treasure(self, fox, spot):
        self._treasures += 1
        key = f"treasure{self._treasures}"
        self.grab_requests.append((key, spot))
        fox.carrying = self.add(Treasure(self, fox, key))

    def drop_treasure(self, fox):
        treasure = getattr(fox, "carrying", None)
        if treasure is not None:
            treasure.carried_by = None
            fox.carrying = None

    def pool_near(self, fox, reach):
        near = [p for p in self.of("prop") if p.variant == "pool" and abs(p.x - fox.x) < reach * self.scale / 2]
        return near[0] if near else None

    def splash(self, pool, drops=10):
        """Water splashing up out of the kiddie pool: drops flying, ripples spreading."""
        from pet.items import Droplet
        s = self.scale
        pool.react()
        for _ in range(drops):
            self.add(Droplet(self, pool.x + self.rng.uniform(-18, 18) * s, pool.y - 8 * s))

    def paddle(self, fox, pool):
        """A hot fox in the kiddie pool: a hop in, a happy splash about, a roll, a hop out and a shake."""
        s, rng = self.scale, self.rng
        side = -1 if fox.x < pool.x else 1
        edge = pool.x + side * 40 * s
        water = self.ground - 3 * s  # standing in the water, a little lower than the rim
        out = max(60.0, min(self.width - 60.0, pool.x - side * rng.uniform(50, 80) * s))
        fox.do(Step("trot", to_x=edge, speed=TROT), Step("crouch", 0.4, face=pool.x),
               Step("hop", to_x=pool.x + side * 6 * s, to_y=water, leap=14, then=lambda: self.splash(pool, 12)),
               Step("happy", 1.2, then=lambda: self.splash(pool, 8)), Step("bat", then=lambda: self.splash(pool, 6)),
               Step("happy", 1.0), Step("crouch", 0.3, face=out),
               Step("hop", to_x=out, to_y=self.ground, leap=14, then=lambda: self.splash(pool, 5)),
               Step("scratch"), Step("happy", 0.8))

    def floater_near(self, fox):
        """A butterfly flying low, or a bit of seed fluff drifting past, close enough for a fox to pounce at."""
        s = self.scale
        near = [t for t in self.of("butterfly") + self.of("fluff") + self.of("firefly")
                if abs(t.x - fox.x) < 160 * s and t.y > self.ground - 70 * s and getattr(t, "state", "") != "rest"]
        return min(near, key=lambda t: abs(t.x - fox.x)) if near else None

    def chase_floater(self, fox, thing):
        """A crouch, a wiggle, and a leap at it. It always gets away (the butterfly flutters up, the fluff floats
        off), and the fox is delighted anyway."""
        x = max(40.0, min(self.width - 40.0, thing.x))
        fox.do(Step("crouch", 0.5, face=thing.x),
               Step("pounce", to_x=x, leap=26, then=lambda: self._dodge(thing)),
               Step("land"), Step("happy", 1.0), Step("tilt", face=thing.x))

    def _dodge(self, thing):
        s = self.scale
        if thing.kind == "butterfly":
            thing.state, thing.target = "flutter", None
            thing.y -= 24 * s
        elif thing.kind == "firefly":
            thing.home_y -= 30 * s  # up and away, still blinking
        else:
            thing.vy = -30.0  # the fluff puffs up out of reach

    def produce_near(self, fox, reach):
        """Something tasty lying on the ground nearby: an apple, a tomato, a lettuce (or a radish)."""
        food = [a for a in self.of("acorn") if getattr(a, "produce", None) and a.on_ground and not a.taken
                and abs(a.x - fox.x) < reach * self.scale / 2]
        return min(food, key=lambda a: abs(a.x - fox.x)) if food else None

    def nibble(self, fox, food):
        """Trot over, sniff, munch. Yum! (A radish, though: bleh! a shake of the head.)"""
        from pet.visitors import Bubble
        s = self.scale
        food.taken = True  # spoken for
        side = 1 if fox.x < food.x else -1
        spot = max(40.0, min(self.width - 40.0, food.x - side * 16 * s))
        radish = food.produce == "radish"

        def eat():
            if food.gone:
                return
            for _ in range(4):
                self.add(Kernel(self, food.x + self.rng.uniform(-3, 3) * s, food.y - 3 * s, food.bit))
            food.gone = True
            bubble = self.add(Bubble(self, fox, "bleh_bubble" if radish else "yum_bubble", rise=34))
            bubble.life = 1.8  # long enough to read

        after = [Step("scratch"), Step("look")] if radish else [Step("happy", 1.2)]
        fox.do(Step("trot", to_x=spot, speed=TROT), Step("sniff", face=food.x), Step("chew", 1.6, then=eat), *after)

    @property
    def dark(self):
        return self.daylight() in ("night", "dusk")

    def lit_up(self):
        """What glows at night: jack-o'-lanterns and the Christmas tree. (thing, glow sprite, how high its middle is:
        None for halfway up)"""
        lit = []
        for p in self.of("pumpkin"):
            if p.anim.name.endswith("_jack"):
                lit.append((p, "glow_warm_big" if p.huge else "glow_warm", None))
        for p in self.of("prop"):
            if p.variant == "xmas_tree":
                lit.append((p, "glow_lights", None))
        return lit

    def night_lights(self, dt):
        """After dark: glows over the jack-o'-lanterns and the Christmas lights, and fireflies over the grass on a
        summer night. They fade away at dawn."""
        glows = {g.holder: g for g in self.of("glow") if g.holder.kind != "firefly"}
        wanted = {thing: (sprite, dy) for thing, sprite, dy in self.lit_up()} if self.dark else {}
        for holder, g in glows.items():
            if holder not in wanted:
                g.fading = True
        for holder, (sprite, dy) in wanted.items():
            if holder not in glows:
                self.add(Glow(self, holder, sprite, dy))
        flies = [f for f in self.of("firefly") if not f.leaving]
        if self.dark and self.season == "summer" and not self.snowed_over and self.falling is None:
            if len(flies) < 12 and self.rng.random() < dt * 0.8:
                self.add(Firefly(self))
        else:
            for f in flies:
                f.leaving = True
                f.glow.fading = True

    def leave_paw_prints(self):
        """Foxes walking about on a snowy day leave a trail of paw prints, which slowly fade."""
        from pet.items import PawPrint
        if not self.snowed_over:
            return
        s = self.scale
        for fox in self.of("fox"):
            if fox.alpha <= 0 or fox.held or fox.y < self.ground - 1:
                continue
            last = getattr(fox, "last_print", None)
            if last is None or abs(fox.x - last) > 11 * s:
                fox.last_print = fox.x
                if last is not None and len(self.of("print")) < 120:
                    self.add(PawPrint(self, fox.x, self.ground))

    def climbable_near(self, fox, reach):
        near = [t for t in self.of("climb") if t.available and abs(t.x - fox.x) < reach * self.scale / 2]
        return self.rng.choice(near) if near else None

    def climb(self, fox, thing):
        """Hop up the pile one level at a time, enjoy the view from the top, then leap off. (The slide: up the
        ladder, and whee, down the chute.)"""
        s, rng = self.scale, self.rng
        slide = thing.variant == "slide"
        side = -1 if fox.x < thing.x or slide else 1  # climb up the side it's on (the slide's ladder is on the left)
        path = [(thing.x + side * abs(dx) * s if dx else thing.x, self.ground - h * s) for dx, h in thing.levels]
        start = path[0][0] + side * 30 * s
        steps = [Step("trot", to_x=start, speed=TROT), Step("crouch", 0.4, face=thing.x)]
        for x, y in path:
            steps.append(Step("hop", to_x=x, to_y=y, leap=12))
        if slide:
            m = sprites.meta("slide")
            ax, ay = m["anchor"]
            chute = [(thing.x + (px - ax) * s, thing.y - (ay - py) * s) for px, py in m["chute"]]
            steps += [Step("happy", 0.8), Step("crouch", 0.3, face=chute[-1][0])]
            for x, y in chute:  # sliding down, sitting tight, faster and faster
                steps.append(Step("crouch", to_x=x, to_y=y, leap=0.01))
            fox.do(*steps, Step("land"), Step("happy", 1.2), Step("roll", 1.0), Step("happy", 0.8))
            return
        top_x = path[-1][0]
        steps += [Step("look"), Step("happy", 1.4), Step("tilt"), Step("idle", rng.uniform(2, 5))]
        if rng.random() < 0.5:
            steps.append(Step("playbow", 1.0))
        land = max(60.0, min(self.width - 60.0, top_x - side * rng.uniform(70, 120) * s))
        steps += [Step("crouch", 0.5, face=land), Step("pounce", to_x=land, to_y=self.ground, leap=18),
                  Step("land"), Step("happy", 1.0)]
        fox.do(*steps)

    def wander_target(self, fox):
        reach = self.rng.uniform(80, 360) * self.scale / 2
        x = fox.x + reach * self.rng.choice((-1, 1))
        return max(60.0, min(self.width - 60.0, x))

    def kick(self, acorn, fox):
        if acorn.gone or acorn.taken:
            return
        acorn.vx = fox.facing * self.rng.uniform(90, 170) * self.scale
        acorn.on_ground = True

    # -- for the window ----------------------------------------------------------------------------------

    def drawing_order(self):
        return sorted(self.things, key=lambda t: t.z)

    def thing_at(self, x, y, draggable_only=False):
        for thing in reversed(self.drawing_order()):
            if (not draggable_only or thing.draggable) and thing.contains(x, y):
                return thing
        return None
