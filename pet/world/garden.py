"""Growing and harvesting: the pumpkin and watermelon patches, single pumpkins put out to decorate (on the
haystack, under a tree...), the corn field, the vegetable rows, and the hoe carving pumpkins."""
from pet import seasons
from pet.items import Corn, CornCob, Crop, DecoPumpkin, Melon, Pumpkin


class Garden:
    """Part of World (see pet/world/__init__.py)."""

    def decos_in_season(self):
        return "pumpkins" in seasons.items_for(self.season)

    def put_out_decos(self):
        """The decorating pumpkins you've put out, in their places (only in pumpkin season)."""
        if not self.decos_in_season():
            for d in self.of("deco"):
                d.gone = True
            return
        if self.of("deco"):
            return
        s = self.scale
        for record in self.settings.get("decorations", []):
            holder = next((c for c in self.of("climb") if c.variant == record.get("on")), None)
            level = record.get("level")
            x = float(record.get("x", self.width / 2))
            deco = self.add(DecoPumpkin(self, x, self.ground, record.get("size"), record.get("shape"),
                                        record.get("jack")))
            if holder is not None and isinstance(level, int) and 0 <= level < len(holder.levels):
                deco.holder, deco.level, deco.dx = holder, level, float(record.get("dx", 0.0))
                deco.x = holder.x + deco.dx * s
                deco.y = deco.floor()
            deco.x = self.clamp_x(deco.x, 10.0)

    def add_deco(self, jack=False, x=None):
        """A single ripe pumpkin (or a jack-o'-lantern) to decorate with: it drops in onto the ground."""
        if not self.decos_in_season():
            return None
        x = x if x is not None else self.width * self.rng.uniform(0.3, 0.7)
        deco = self.add(DecoPumpkin(self, x, self.ground - 120 * self.scale, self.rng.choice(("s", "m", "l")),
                                    self.rng.choice(Pumpkin.SHAPES), jack))
        self.save_decos()
        return deco

    def surface_under(self, x, y):
        """Something to sit on where a pumpkin is let go at (x, y): (climbable, level) or None. Let go above a
        top, it lands on the first top below; let go on the thing itself (over a bale, say), it goes on top."""
        s = self.scale
        if y >= self.ground - 2 * s:
            return None  # let go down on the ground
        best = None
        for c in self.of("climb"):
            if not c.available or c.variant == "slide":
                continue
            column = [(i, c.y - h * s) for i, (dx, h) in enumerate(c.levels) if abs(x - (c.x + dx * s)) <= 14 * s]
            if not column:
                continue
            on = [(i, top) for i, top in column if top - 8 * s <= y <= top + 18 * s]  # let go on that bale/barrel
            below = [(i, top) for i, top in column if top >= y - 8 * s]                # or somewhere above it
            i, top = min(on or below or column, key=lambda it: it[1])  # the highest of those
            if best is None or top < best[2]:
                best = (c, i, top)
        return best[:2] if best else None

    def place_deco(self, deco):
        """You let go of a decorating pumpkin: onto whatever's below it, or down to the ground."""
        s = self.scale
        found = self.surface_under(deco.x, deco.y)
        if found is not None:
            holder, level = found
            spot = holder.x + holder.levels[level][0] * s
            deco.x = max(spot - 10 * s, min(spot + 10 * s, deco.x))  # stay on top, not hanging off the edge
            deco.holder, deco.level, deco.dx = holder, level, (deco.x - holder.x) / s
        else:
            deco.holder = deco.level = None
        deco.x = self.clamp_x(deco.x, 10.0)
        self.save_decos()

    def pick_pumpkin(self, pumpkin):
        """A ripe pumpkin lifted out of the patch: it's picked (to decorate with), and a new sprout comes up."""
        if pumpkin.kind != "pumpkin" or pumpkin.stage != Pumpkin.STAGES - 1 or pumpkin.wilting or pumpkin.bursting \
                or not self.decos_in_season():
            return None
        deco = self.add(DecoPumpkin(self, pumpkin.x, pumpkin.y, pumpkin.size, pumpkin.shape, pumpkin.jack))
        pumpkin._replant()
        self.save_decos()
        return deco

    def save_decos(self):
        records = []
        for d in self.of("deco"):
            if d.gone:
                continue
            r = {"x": round(d.x), "size": d.size, "shape": d.shape, "jack": d.jack}
            if d.holder is not None:
                r.update(on=d.holder.variant, level=d.level, dx=round(d.dx, 1))
            records.append(r)
        self.settings["decorations"] = records
        self.dirty = True

    def clear_decos(self):
        for d in self.of("deco"):
            d.gone = True
        self.settings["decorations"] = []
        self.dirty = True

    def plant_corn(self, replant=False):
        """Put out the corn field: the saved one, still growing, or a freshly planted row."""
        item = self.settings["items"].setdefault("corn", {"out": True, "x": None, "planted": None})
        for thing in self.of("corn"):
            thing.gone = True
        if replant or not isinstance(item.get("planted"), (int, float)):
            item["planted"] = self.now().timestamp()
            self.dirty = True
        x = self.spot_for("corn", self.width * 0.12)  # (at first off to the left, away from the oak)
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
        x = self.spot_for(name, self.width * self.CROP_SPOTS[name])
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
            patch = [{"x": round(self.clamp_x(centre + (i - 1) * 46 * self.scale)),
                      "planted": now - self.rng.uniform(0, 90), "pace": round(self.rng.uniform(0.85, 1.2), 2),
                      "size": size, "shape": self.rng.choice(shapes), "jack": self.rng.random() < 0.2,
                      "giant": self.rng.random() < cls.GIANT_CHANCE}
                     for i, size in enumerate(self.rng.sample(sizes, 3))]  # one of each, in any order
            self.dirty = True
        item["patch"] = patch
        for record in patch:
            x = self.clamp_x(float(record["x"]), 20.0)
            self.add(cls(self, x, record["planted"], float(record.get("pace", 1.0)), record, record["size"],
                         record["shape"], record.get("jack", False), record.get("giant", False)))

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
            near = [p for p in self.of("pumpkin") + self.of("deco") if abs(p.x - thing.x) < 30 * self.scale
                    and (p.kind == "pumpkin" or p.y >= self.ground - 2)]  # (not one up on a haystack)
            pumpkin = min(near, key=lambda p: abs(p.x - thing.x)) if near else None
            if pumpkin is not None:
                thing.react()  # a thunk, carved or not
                if not pumpkin.carve():
                    pumpkin.anim.time += 0.7

    def pumpkin_near(self, fox, reach):
        ripe = [p for p in self.of("pumpkin") if p.ripe and abs(p.x - fox.x) < reach * self.scale / 2]
        return min(ripe, key=lambda p: abs(p.x - fox.x)) if ripe else None
