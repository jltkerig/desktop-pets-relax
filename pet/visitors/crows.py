"""Crows: they come in groups, perch on things (the scarecrow most of all), chat, play with what's lying
about, peck corn, and sometimes borrow the scarecrow's hat."""
from pet.items import Hat, Kernel, StrawBit
from .base import Bubble, HeadPerch, Perch, Visitor


# where a crow can sit on each kind of item, in sprite pixels from its anchor
SCARECROW_ARMS = [(-14, 51), (14, 51)]               # the two outstretched arms (and his head: HeadPerch)
DEN_PERCHES = [(-2, 32), (-20, 27), (18, 26)]        # the tops of the mound's lumps
PROP_PERCHES = {"sled": [(-8, 10), (8, 10)], "xmas_tree": [(0, 43)],  # along the sled; on the star
                "well": [(0, 59)], "apple_barrel": [(-4, 27), (5, 26)]}  # the roof's peak; on the apples
PUMPKIN_HEIGHT = {"s": 0.75, "m": 1.0, "l": 1.3}
PUMPKIN_SHAPE_HEIGHT = {"round": 1.0, "tall": 1.32, "squat": 0.74}


def scarecrow_of(world):
    return next((p for p in world.of("prop") if p.variant == "scarecrow"), None)


def crow_perches(world):
    """Every spot up off the ground where a crow could land: the oak's branches and the tops of things."""
    s = world.scale
    spots = []
    for thing in world.things:
        if thing.gone or thing.alpha < 1:
            continue
        if thing.kind in ("tree", "birch"):
            spots += [Perch(thing, (x - thing.x) / s, (thing.y - y) / s) for x, y in thing.perch_points()]
        elif thing.kind == "prop" and thing.variant == "scarecrow":
            spots += [HeadPerch(thing)] + [Perch(thing, dx, dy) for dx, dy in SCARECROW_ARMS]
        elif thing.kind == "prop" and thing.variant in PROP_PERCHES:
            spots += [Perch(thing, dx, dy) for dx, dy in PROP_PERCHES[thing.variant]]
        elif thing.kind == "climb" and thing.available:
            spots += [Perch(thing, dx, dy) for dx, dy in thing.levels]
        elif thing.kind == "den":
            spots += [Perch(thing, dx, dy) for dx, dy in DEN_PERCHES]
        elif thing.kind == "pumpkin" and thing.huge:
            spots.append(Perch(thing, 0, 28.3 * PUMPKIN_SHAPE_HEIGHT[thing.shape]))
        elif thing.kind == "pumpkin" and thing.ripe:
            top = 12.8 * PUMPKIN_HEIGHT[thing.size] * PUMPKIN_SHAPE_HEIGHT[thing.shape]
            spots.append(Perch(thing, 0, top))
    return [p for p in spots if p.ok() and 20 < p.pos(world)[0] < world.width - 20]


FAVOURITES = {"scarecrow": 6, "oak": 3, "birch": 2}  # how much more a crow likes sitting there than elsewhere


def favourite(perches, rng):
    """Pick a perch, much preferring the scarecrow (crows love him), and the oak's branches after him."""
    weighted = [p for p in perches for _ in range(FAVOURITES.get(getattr(p.holder, "variant", None), 1))]
    return rng.choice(weighted) if weighted else None


CAWS = ("caw_bubble", "caw_bubble", "caw2_bubble", "kraa_bubble", "cawq_bubble")
TALKING = ("sit", "inspect", "play", "walk", "strut")  # what a crow can be doing and still chat


class CrowParty:
    """Two or more crows visiting together: they land near each other, talk among themselves, and leave
    together. On a long visit they come down to look at the things lying about and play with them. They
    love the scarecrow (and his hat) and corn cobs above all."""

    def __init__(self, world, count):
        rng = world.rng
        self.world = world
        self.side = rng.choice((-1, 1))  # which edge they come in from (-1: the left)
        self.long = rng.random() < 0.7
        self.stay = rng.uniform(120, 240) if self.long else rng.uniform(35, 60)
        self.timer = 0.0
        self.chat_in = rng.uniform(2, 5)
        self.leaving = False
        self.spots = self._landing_spots(count)
        self.members = [Crow(world, self, spot, delay=i * rng.uniform(0.3, 0.8)) for i, spot in enumerate(self.spots)]

    def ground_spot_near(self, x):
        w, rng = self.world, self.world.rng
        x += rng.uniform(25, 80) * w.scale * rng.choice((-1, 1))
        return Perch(x=w.clamp_x(x, 30.0))

    def _landing_spots(self, count):
        """The first crow picks a spot (by some corn on the ground, up on something, or anywhere on the
        ground); the rest land close by."""
        w, rng = self.world, self.world.rng
        high = crow_perches(w)
        cobs = w.cobs_on_ground()
        hats = w.of("hat")
        if hats or (cobs and rng.random() < 0.7):  # a dropped hat, or corn: land right by it
            thing = hats[0] if hats else rng.choice(cobs)
            first = Perch(x=w.clamp_x(thing.x + rng.choice((-1, 1)) * 16 * w.scale, 30.0))
        elif high and rng.random() < 0.75:
            first = favourite(high, rng)
        else:
            first = Perch(x=rng.uniform(0.15, 0.85) * w.width)
        fx = first.pos(w)[0]
        near = [p for p in high if p is not first and abs(p.pos(w)[0] - fx) < 140 * w.scale]
        rng.shuffle(near)
        spots = [first]
        while len(spots) < count:
            spots.append(near.pop() if near and rng.random() < 0.7 else self.ground_spot_near(fx))
        return spots

    def centre(self):
        here = [c.x for c in self.members if not c.gone]
        return sum(here) / len(here) if here else self.world.width / 2

    def chatty(self):
        return [c for c in self.members if not c.gone and c.state in TALKING and c.reply_in is None]

    def tick(self, caller, dt):
        if caller is not next((c for c in self.members if not c.gone), None):
            return
        rng = self.world.rng
        self.timer += dt
        if not self.leaving and self.timer > self.stay:
            caller.caw()  # time to go: one calls, and they all take off
            self.leave(delay=True)
            return
        self.chat_in -= dt
        if self.chat_in <= 0 and not self.leaving:  # one starts a conversation with the nearest other
            self.chat_in = rng.uniform(4, 10)
            talkers = self.chatty()
            if len(talkers) >= 2:
                speaker = rng.choice(talkers)
                partner = min((c for c in talkers if c is not speaker), key=lambda c: abs(c.x - speaker.x))
                speaker.say(partner, rounds=rng.randint(1, 4))

    def react(self, crow):
        """Something exciting (the hat!): the others call out about it."""
        for c in self.chatty():
            if c is not crow and self.world.rng.random() < 0.8:
                c.reply_in, c.reply_to, c.reply_rounds = self.world.rng.uniform(0.3, 1.0), crow, 0

    def leave(self, delay=False):
        if self.leaving:
            return
        self.leaving = True
        exit_x = -60.0 if self.world.rng.random() < 0.5 else self.world.width + 60.0
        for c in self.members:
            c.take_off(exit_x, self.world.rng.uniform(0.2, 1.0) if delay else 0.0, startled=not delay)

    def startle(self, crow):
        """A click, or a fox dashing at them: a caw, and the whole party flies off at once."""
        if not self.leaving:
            crow.caw("kraa_bubble")
            self.leave()

    def taken(self, thing):
        """Is another crow busy with it? A corn cob has room for two."""
        busy = sum(1 for c in self.members if not c.gone and c.item is thing)
        return busy >= (2 if getattr(thing, "is_cob", False) else 1)

    def hat_taken(self):
        return any(c.hat for c in self.members if not c.gone)


class Crow(Visitor):
    """One crow in a party (see CrowParty). Sits about on branches, on things or on the ground, hopping,
    cocking its head and chatting with the others; on a long visit it walks up to things and plays with them:
    pecking kernels off corn cobs, rolling acorns, flipping leaves, tugging straw out of the haystack, tapping
    pumpkins, carrying an acorn up to a perch and dropping it, or pinching the scarecrow's hat, strutting
    about in it, and putting it back."""
    kind = "crow"
    z = 28
    FLY = 120
    WALK = 22
    HAT_POSES = ("fly", "perch", "hop", "walk", "peck", "tilt", "caw")

    def __init__(self, world, party, perch, delay):
        rng = world.rng
        start = -40.0 if party.side < 0 else world.width + 40.0
        super().__init__(world, start, world.height * rng.uniform(0.2, 0.45), "crow_fly")
        self.party = party
        self.perch = perch
        self.delay = delay
        self.state = "arrive"
        self.timer = 0.0
        self.settle = rng.uniform(4, 9)  # how long it sits before getting curious (on a long visit)
        self.item = None                 # the thing it's going to look at or play with
        self.carrying = None             # an acorn in its beak
        self.hat = False                 # wearing the scarecrow's hat
        self.scarecrow = None            # whose hat it is
        self.hat_age = self.hat_for = 0.0
        self.leave_after = None          # (exit x) once the hat's back
        self.reply_in = None             # about to answer another crow
        self.reply_to = None
        self.reply_rounds = 0
        self.strut_to = None
        self.exit = (start, 0.0)
        self.anim.time = rng.uniform(0, 1)

    def pose(self, name):
        if name == "fly" and self.carrying is not None:
            name = "carry"
        self.anim.play(f"crow_hat_{name}" if self.hat and name in self.HAT_POSES else f"crow_{name}")

    # -- things that happen to it ----------------------------------------------------------------------

    def click(self):
        self.party.startle(self)

    def caw(self, word=None):
        w = self.world
        if self.state in TALKING:
            self.pose("caw")
        w.add(Bubble(w, self, word or w.rng.choice(CAWS), rise=26 if not self.hat else 30))

    def say(self, partner, rounds=0, word=None):
        """Caw at another crow (turning to face it); it answers, and so on, for a few rounds."""
        if self.state in TALKING and abs(partner.x - self.x) > 2:
            self.facing = 1 if partner.x > self.x else -1
        self.caw(word)
        if rounds > 0 and not partner.gone:
            partner.reply_in, partner.reply_to, partner.reply_rounds = self.world.rng.uniform(0.6, 1.3), self, rounds - 1

    def take_off(self, exit_x, delay, startled=False):
        self.drop()
        exit_ = (exit_x, self.world.height * self.world.rng.uniform(0.05, 0.25))
        if self.hat and not startled and self._scarecrow_ok():
            self.leave_after = exit_  # puts the hat back first, then goes
            return self._return_hat()
        if self.hat:  # startled: it lets go of the hat, which floats down
            s = self.world.scale
            if self._scarecrow_ok():
                self.world.add(Hat(self.world, self.x, self.y - 12 * s, self.scarecrow))
            self.hat = False
        self.state, self.timer, self.delay = "leave", 0.0, delay
        self.exit = exit_

    def drop(self):
        """Let go of the acorn it's carrying: it falls from its beak."""
        acorn = self.carrying
        if acorn is None:
            return
        s = self.world.scale
        acorn.x, acorn.y = self.x + self.facing * 9 * s, self.y - 11 * s
        acorn.alpha, acorn.taken, acorn.on_ground, acorn.bounced = 1.0, False, False, False
        acorn.vx, acorn.vy = self.facing * 10 * s, 0.0
        self.carrying = None

    # -- what it does ----------------------------------------------------------------------------------

    def _sit(self, perch):
        self.perch = perch
        self.state, self.timer = "sit", 0.0
        self.pose("perch")

    def _fly(self, perch, state="fly"):
        self.perch = perch
        self.state = state
        self.pose("fly")

    def _scarecrow_ok(self):
        return self.scarecrow is not None and not self.scarecrow.gone

    def _go_for_hat(self, scarecrow):
        self.scarecrow = scarecrow
        self.item = scarecrow
        self._fly(HeadPerch(scarecrow), state="to_hat")

    def _return_hat(self):
        self._fly(HeadPerch(self.scarecrow), state="to_return")

    def _something_to_look_at(self):
        """A thing lying about near the party that no other crow is busy with. Corn cobs above all."""
        w = self.world
        centre = self.party.centre()
        picks = []
        for t in w.things:
            if t.gone or t.alpha < 1 or self.party.taken(t) or (abs(t.x - centre) > 320 * w.scale and t.kind != "hat"):
                continue
            if t.kind == "acorn" and t.on_ground and not t.taken:
                picks += [t] * (6 if getattr(t, "is_cob", False) else 2)
            elif t.kind == "hat" and not self.hat:
                return t  # the hat, lying there! straight for it
            elif t.kind == "leaf" and not t.falling:
                picks.append(t)
            elif t.kind in ("pumpkin", "prop", "den") or (t.kind == "climb" and t.variant == "haystack"):
                picks.append(t)
        return w.rng.choice(picks) if picks else None

    def _play_with(self, thing):
        """Peck at it, nudge it, tug at it. True if it picked the thing up."""
        w, rng, s = self.world, self.world.rng, self.world.scale
        if thing.gone:
            return False
        if getattr(thing, "is_cob", False):  # corn (or an apple, a tomato...)! peck bits off
            for _ in range(2):
                w.add(Kernel(w, thing.x + rng.uniform(-3, 3) * s, thing.y - 4 * s, getattr(thing, "bit", "kernel")))
            thing.kernels += 1
            if rng.random() < 0.2:
                thing.vx = self.facing * rng.uniform(20, 40) * s
        elif thing.kind == "acorn":
            if not thing.taken and self.carrying is None and not self.hat and rng.random() < 0.45:
                thing.taken, thing.alpha = True, 0.0  # up into its beak
                self.carrying = thing
                return True
            thing.vx = self.facing * rng.uniform(40, 80) * s  # a shove with the beak: it rolls
        elif thing.kind == "hat":
            if not self.hat and self.carrying is None:  # finders keepers (for a while)
                thing.gone = True
                self.hat, self.scarecrow = True, thing.scarecrow
                self.hat_age, self.hat_for = 0.0, rng.uniform(10, 25)
                self.pose("peck")
                self.party.react(self)
        elif thing.kind == "leaf":
            thing.landed_for = None  # flipped up: it flutters down again
            thing.y -= 8 * s
            thing.alpha = 1.0
        elif thing.kind == "pumpkin":
            thing.anim.time += 0.7  # a tap: a little rustle
        elif thing.kind == "climb":
            for _ in range(3):  # a beakful of straw tugged out
                w.add(StrawBit(w, self.x + self.facing * 8 * s, self.y - rng.uniform(4, 10) * s))
        elif thing.kind == "prop":
            thing.click()  # the scarecrow looks surprised; the hoe wobbles
        return False

    def _carry_off(self):
        """Up to a perch with the acorn it just picked up (to drop it from there)."""
        w = self.world
        up = [p for p in crow_perches(w) if abs(p.pos(w)[0] - self.x) < 300 * w.scale]
        self.item = None
        self._fly(w.rng.choice(up) if up else Perch(x=self.x))

    def _somewhere_to_show_off(self):
        """Away from the scarecrow, with his hat on: a branch, the top of something, or the ground."""
        w, rng = self.world, self.world.rng
        up = [p for p in crow_perches(w) if p.holder is not self.scarecrow and abs(p.pos(w)[0] - self.x) < 300 * w.scale]
        return rng.choice(up) if up and rng.random() < 0.6 else self.party.ground_spot_near(self.x)

    def _flee_check(self):
        """A fox charging at a crow on the ground or low down sends the whole party off. One just wandering
        close makes that crow flutter out of its way."""
        w = self.world
        if self.y < w.ground - 40 * w.scale or self.state in ("fly", "down", "to_hat", "to_return", "tug"):
            return
        for fox in w.of("fox"):
            if fox.step is None or abs(fox.x - self.x) > 50 * w.scale:
                continue
            towards = (self.x - fox.x) * fox.facing > 0
            if fox.step.anim in ("run", "pounce", "dive") and towards:
                self.party.startle(self)
                return
            if fox.step.anim in ("walk", "trot") and towards and abs(fox.x - self.x) < 30 * w.scale:
                self.item = None
                away = 1 if self.x > fox.x else -1
                x = w.clamp_x(self.x + away * w.rng.uniform(50, 90) * w.scale, 30.0)
                self._fly(Perch(x=x))
                return

    def update(self, dt):
        super().update(dt)
        self.party.tick(self, dt)
        self.timer += dt
        w, rng, s = self.world, self.world.rng, self.world.scale
        if self.hat and not self._scarecrow_ok():
            self.hat = False  # the scarecrow was put away, hat and all
            self.pose("perch")
        if self.state not in ("arrive", "leave"):
            self._flee_check()
        if self.reply_in is not None and self.state in TALKING:
            self.reply_in -= dt
            if self.reply_in <= 0:
                self.reply_in = None
                if self.reply_to is not None and not self.reply_to.gone:
                    self.say(self.reply_to, self.reply_rounds)
        if self.state in ("walk", "strut") and self.anim.done:
            self.pose("walk")  # done cawing, walking on
        if self.state == "arrive":
            if self.timer < self.delay:
                return
            if not self.perch.ok():
                self.perch = self.party.ground_spot_near(self.x)
            if self.fly_to(*self.perch.pos(w), dt, speed=self.FLY):
                self._sit(self.perch)
        elif self.state == "fly":  # off to another spot (with an acorn, maybe)
            if not self.perch.ok():
                self.perch = self.party.ground_spot_near(self.x)
            if self.fly_to(*self.perch.pos(w), dt, speed=self.FLY):
                self._sit(self.perch)
                if self.carrying is not None:
                    self.drop()  # plonk: down it goes (onto a napping fox, sometimes)
                    self.pose("tilt")
        elif self.state == "to_hat":
            if not self._scarecrow_ok() or not self.scarecrow.hat_on or self.party.hat_taken():
                self.item = None
                return self._sit(Perch(x=self.x)) if self.y >= w.ground - 1 else self._fly(self.party.ground_spot_near(self.x))
            if self.fly_to(*self.perch.pos(w), dt, speed=self.FLY):
                self.state, self.timer = "tug", 0.0
                self.pose("peck")
        elif self.state == "tug":  # tugging at the brim...
            self.x, self.y = self.perch.pos(w)
            if self.timer > 1.5:
                self.item = None
                if self._scarecrow_ok() and self.scarecrow.hat_on and not self.party.hat_taken():
                    self.scarecrow.lose_hat()  # ...got it!
                    self.hat = True
                    self.hat_age, self.hat_for = 0.0, rng.uniform(20, 40)
                    self.party.react(self)
                    return self._fly(self._somewhere_to_show_off())
                self._sit(self.perch)
        elif self.state == "to_return":
            if not self._scarecrow_ok():
                self.hat = False
                return self._sit(Perch(x=self.x))
            if self.fly_to(*self.perch.pos(w), dt, speed=self.FLY):
                if not self.scarecrow.hat_on:
                    self.scarecrow.get_hat_back()  # there you go, good as new
                self.hat = False
                self._sit(self.perch)
                self.pose("peck")
                if self.leave_after is not None:
                    self.state, self.timer, self.delay = "leave", 0.0, 0.3
                    self.exit, self.leave_after = self.leave_after, None
        elif self.state == "sit":
            if not self.perch.ok():  # its perch was knocked over or carried off: down to the ground
                return self._fly(self.party.ground_spot_near(self.x))
            self.x, self.y = self.perch.pos(w)
            if self.anim.done or (self.anim.name.endswith("_hop") and self.anim.time > 0.4):
                self.pose("perch")
            if self.hat:
                self.hat_age += dt
                if self.hat_age > self.hat_for and self._scarecrow_ok() and not self.party.leaving:
                    return self._return_hat()
                if not self.perch.high and rng.random() < dt * 0.35:  # strutting about in it
                    self.strut_to = w.clamp_x(self.x + rng.uniform(-40, 40) * s, 30.0)
                    self.state = "strut"
                    self.pose("walk")
                    return
            elif self.party.long and not self.party.leaving and self.timer > self.settle:
                self.settle = rng.uniform(5, 12)
                scarecrow = scarecrow_of(w)
                if scarecrow is not None and scarecrow.hat_on and not self.party.hat_taken() and \
                        self.carrying is None and rng.random() < 0.3:
                    return self._go_for_hat(scarecrow)
                self.item = self._something_to_look_at()
                if self.item is not None:
                    if self.perch.high:  # flutter down beside it first
                        side = 1 if self.x < self.item.x else -1
                        return self._fly(Perch(x=self.item.x - side * 14 * s), state="down")
                    self.state = "walk"
                    self.pose("walk")
                    return
                self.timer = 0.0
            roll = rng.random()
            if roll < dt * 0.3:
                self.pose("hop")
                self.facing = -self.facing
            elif roll < dt * 0.35:
                self.caw()
            elif roll < dt * 0.5:
                self.pose("tilt")
        elif self.state == "strut":
            if self.move_to(self.strut_to, self.WALK, dt):
                self._sit(Perch(x=self.x))
        elif self.state == "down":
            if self.fly_to(*self.perch.pos(w), dt, speed=self.FLY):
                self.perch = Perch(x=self.x)
                self.state = "walk"
                self.pose("walk")
        elif self.state == "walk":
            item = self.item
            if item is None or item.gone or item.alpha < 1:
                return self._sit(Perch(x=self.x))
            side = 1 if self.x < item.x else -1
            if self.move_to(item.x - side * 12 * s, self.WALK, dt):
                self.facing = side
                self.state, self.timer = "inspect", 0.0
                self.pose("tilt")
        elif self.state == "inspect" and self.timer > 1.6:  # a long, thoughtful look first
            self.state, self.timer = "play", 0.0
            corn = getattr(self.item, "is_cob", False)
            self.play_for = rng.uniform(6, 12) if corn else rng.uniform(2.5, 4.0)
            self.pose("peck")
            if self._play_with(self.item):
                return self._carry_off()
        elif self.state == "play":
            if self.item is not None and self.timer > 0.8 and \
                    rng.random() < dt * (2.0 if getattr(self.item, "is_cob", False) else 0.8):
                if self._play_with(self.item):  # another go
                    return self._carry_off()
            if self.anim.done:
                self.pose("peck")
            if self.timer > self.play_for:
                self.item = None
                if rng.random() < 0.5:  # back up to sit with the others (on the scarecrow, by choice)
                    up = [p for p in crow_perches(w) if abs(p.pos(w)[0] - self.party.centre()) < 160 * s]
                    if up:
                        return self._fly(favourite(up, rng))
                self._sit(Perch(x=self.x))
        elif self.state == "leave":
            if self.timer < self.delay:
                return
            self.pose("fly")
            if self.fly_to(*self.exit, dt, speed=150):
                self.gone = True


def crow_party(world):
    """Two to four crows, landing near each other."""
    return CrowParty(world, world.rng.choice((2, 2, 3, 4))).members
