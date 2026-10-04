"""Everything on the desktop and the rules between them. No Qt here, so it can be tested."""
import datetime
import random

from pet import seasons
from pet.fox import TROT, WALK, Fox, Step
from pet.items import Acorn, Leaf, Prop, Pumpkin, Treasure, Tree
from pet.visitors import Goose, Jay, Squirrel, Woolly, migrating_v

LEAF_COLOURS = ("red", "orange", "yellow", "brown")


class World:
    def __init__(self, width, height, settings, rng=None, clock=None):
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
        self.dirty = False  # settings changed here (pumpkins planted); the window saves them
        self.taskbar_spots = []   # x of each taskbar icon, filled in by the window
        self.images = {}          # treasure key -> picture of the icon (set by the window)
        self.grab_requests = []   # (treasure key, x) the window should copy the icon for
        self._treasures = 0
        self.rebuild()

    # -- setup -----------------------------------------------------------------------------------------

    def now(self):
        return self.clock()

    @property
    def season(self):
        chosen = self.settings.get("season", "auto")
        return seasons.season_for(self.now().date()) if chosen == "auto" else chosen

    def add(self, thing):
        self.things.append(thing)
        return thing

    def of(self, kind):
        return [t for t in self.things if t.kind == kind and not t.gone]

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
        props = {"scarecrow"}
        for thing in self.of("prop"):
            if thing.variant not in wanted_items:
                thing.gone = True
        for name in wanted_items & props:
            if not any(t.variant == name for t in self.of("prop")):
                x = self.settings["items"][name].get("x")
                if not (isinstance(x, (int, float)) and 0 < x < self.width):
                    patch = self.settings["items"].get("pumpkins", {}).get("patch") or []
                    xs = [p["x"] for p in patch if isinstance(p, dict) and isinstance(p.get("x"), (int, float))]
                    x = (max(xs) + 70 * self.scale) if xs else self.width * 0.32  # next to the pumpkin patch
                    x = min(self.width - 40.0, x)
                self.add(Prop(self, x, name))
        for name in wanted_items - {"pumpkins"} - props:
            if not any(t.variant == name for t in self.of("tree")):
                x = self.settings["items"][name].get("x")
                x = x if isinstance(x, (int, float)) and 0 < x < self.width else self.width * 0.72
                self.add(Tree(self, x, name))
        if "oak" not in wanted_items:  # autumn leftovers go when the tree does
            for thing in self.things:
                if thing.kind in ("leaf", "acorn", "squirrel", "jay"):
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

    def grow_pumpkins(self, replant=False):
        """Put out the pumpkin patch: the saved pumpkins, or three new sprouts."""
        item = self.settings["items"].setdefault("pumpkins", {"out": True, "x": None, "patch": []})
        for thing in self.of("pumpkin"):
            thing.gone = True
        patch = [p for p in item.get("patch", []) if isinstance(p, dict)
                 and isinstance(p.get("x"), (int, float)) and isinstance(p.get("planted"), (int, float))]
        sizes = ["s", "m", "l"]
        shapes = ["round", "tall", "squat"]
        for record in patch:  # pumpkins saved before sizes and shapes existed get them now
            if record.get("size") not in sizes:
                record["size"] = self.rng.choice(sizes)
                self.dirty = True
            if record.get("shape") not in shapes:
                record["shape"] = self.rng.choice(shapes)
                record["jack"] = self.rng.random() < 0.2
                self.dirty = True
        if replant or not patch:
            centre = item.get("x") if isinstance(item.get("x"), (int, float)) else self.width * 0.25
            now = self.now().timestamp()
            patch = [{"x": round(max(40, min(self.width - 40, centre + (i - 1) * 46 * self.scale))),
                      "planted": now - self.rng.uniform(0, 90), "pace": round(self.rng.uniform(0.85, 1.2), 2),
                      "size": size, "shape": self.rng.choice(shapes), "jack": self.rng.random() < 0.2}
                     for i, size in enumerate(self.rng.sample(sizes, 3))]  # one of each, in any order
            self.dirty = True
        item["patch"] = patch
        for record in patch:
            x = max(20.0, min(self.width - 20.0, float(record["x"])))
            self.add(Pumpkin(self, x, record["planted"], float(record.get("pace", 1.0)), record, record["size"],
                             record["shape"], record.get("jack", False)))

    # -- every frame -------------------------------------------------------------------------------------

    def update(self, dt, cursor=None):
        if self.paused:
            return
        dt = min(dt, 0.1)  # after a stall, don't jump ahead
        if cursor is not None:
            moved = abs(cursor[0] - self.cursor[0]) + abs(cursor[1] - self.cursor[1]) > 3
            self.cursor_still = 0.0 if moved else self.cursor_still + dt
            self.cursor = cursor
        self._spawn(dt)
        for thing in list(self.things):
            thing.update(dt)
        self.things = [t for t in self.things if not t.gone]

    def _spawn(self, dt):
        rng, tree = self.rng, self.tree()
        for key in self.timers:
            self.timers[key] -= dt
        if tree is not None and self.timers["leaf"] <= 0:
            self.timers["leaf"] = rng.uniform(0.7, 2.6)
            if len(self.of("leaf")) < 28:
                x, y = tree.crown_point()
                self.add(Leaf(self, x, y, rng.choice(LEAF_COLOURS)))
        if tree is not None and self.timers["acorn"] <= 0:
            self.timers["acorn"] = rng.uniform(40, 120)
            if len(self.of("acorn")) < 4:
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
        choices = [k for k in allowed if not self.of(k)]
        acorns = [a for a in self.of("acorn") if a.on_ground and not a.taken]
        if "squirrel" in choices and not acorns:
            choices.remove("squirrel")
        if "jay" in choices and self.tree() is None:
            choices.remove("jay")
        if "geese" in choices and self.of("goose"):
            choices.remove("geese")
        if "migrants" in choices and self.of("migrant"):
            choices.remove("migrants")
        if kind is not None:
            choices = [kind] if kind in choices else []
        if not choices:
            return None
        pick = self.rng.choice(choices)
        if pick == "squirrel":
            return self.add(Squirrel(self, self.rng.choice(acorns)))
        if pick == "jay":
            return self.add(Jay(self, self.tree()))
        if pick == "migrants":
            return [self.add(goose) for goose in migrating_v(self)][0]
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

    def nap_spot(self, fox):
        """Under the oak if there is one (that's where acorns fall), else where it is."""
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

    def visitor_to_watch(self, fox):
        for kind in ("squirrel", "jay", "woolly", "goose"):
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
               Step("pounce", to_x=leaf.x, leap=24, then=lambda: self.catch_leaf(fox, leaf)), Step("happy", 1.0))

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
               Step("playbow", 1.0), Step("roll", 1.6), Step("happy", 1.2))
        return True

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
