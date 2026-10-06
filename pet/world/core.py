"""The world's core: what's out (rebuild from the settings and season), the season and snow, adding and
finding things, and the update every frame. The topic files add the rest to World (see __init__.py)."""
import datetime
import random

from pet import daylight, seasons
from pet.fox import Fox
from pet.items import Birch, Climbable, Den, Prop, Tree

LEAF_COLOURS = ("red", "orange", "yellow", "brown")


class Core:
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
        self.folder_spots = []      # folder icons on the desktop {name, x, y (bottom), w, h}, set by the window
        self.folder_requests = []   # ("move" | "drop", name, x, y, w, h) for the window to move the real icon
        self.folder_rest = 0.0      # seconds until a fox may move another folder by itself
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

    ITEM_KINDS = ("tree", "prop", "corn", "den", "climb", "pumpkin", "birch", "melon", "crop", "yard")

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
        self.put_out_decos()
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
        self.put_out_fun(wanted_items)  # the newer seasonal things (after the trees: the nest and kite need one)
        for palette, out in self.settings["foxes"].items():
            have = [f for f in self.of("fox") if f.palette == palette]
            if out and not have:
                start = self.width * (0.55 if palette == "orange" else 0.4) + self.rng.uniform(-60, 60)
                self.add(Fox(self, start, palette))
            elif not out:
                for fox in have:
                    fox.gone = True
        self.things = [t for t in self.things if not t.gone]


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
        self.fun(dt)
        self.folder_rest = max(0.0, self.folder_rest - dt)
        self.things = [t for t in self.things if not t.gone]


    def drawing_order(self):
        return sorted(self.things, key=lambda t: t.z)

    def thing_at(self, x, y, draggable_only=False):
        for thing in reversed(self.drawing_order()):
            if (not draggable_only or thing.draggable) and thing.contains(x, y):
                return thing
        return None
