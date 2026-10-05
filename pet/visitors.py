"""Creatures that drop by on their own: the squirrel, the blue jay, the woolly bear caterpillar, geese,
wild turkeys and crows."""
import math

from pet.items import Hat, Kernel, Mound, Note, StrawBit
from pet.things import Thing


class Visitor(Thing):
    z = 22

    def leave_x(self):
        """The nearer screen edge, just off screen."""
        return -40.0 if self.x < self.world.width / 2 else self.world.width + 40.0

    def move_to(self, x, speed, dt):
        """Step toward x; True once there."""
        distance = x - self.x
        if abs(distance) > 1:
            self.facing = 1 if distance > 0 else -1
        move = speed * self.world.scale * dt
        if abs(distance) <= move:
            self.x = x
            return True
        self.x += move if distance > 0 else -move
        return False

    def fly_to(self, x, y, dt, speed=110):
        """Fly straight toward (x, y); True once there."""
        dx, dy = x - self.x, y - self.y
        dist = math.hypot(dx, dy)
        step = speed * self.world.scale * dt
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        if dist <= step:
            self.x, self.y = x, y
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False


class Squirrel(Visitor):
    """Runs in, takes an acorn off the ground, buries it somewhere else, and runs off. If it takes a corn
    cob instead, it's slowed by the weight, and a fox may chase it until it drops the cob and flees."""
    kind = "squirrel"
    SPEED = 120
    CARRY_COB = 55  # a corn cob is heavy for a squirrel

    def __init__(self, world, acorn):
        edge = -30.0 if acorn.x > world.width / 2 or world.rng.random() < 0.5 else world.width + 30.0
        super().__init__(world, edge, world.ground, "squirrel_run")
        self.acorn = acorn
        self.has_cob = getattr(acorn, "is_cob", False)
        acorn.taken = True
        self.state = "to_acorn"
        self.timer = 0.0
        self.bury_x = None

    def update(self, dt):
        super().update(dt)
        self.timer += dt
        rng, w = self.world.rng, self.world
        if self.state == "to_acorn":
            if self.acorn.gone:
                self.state = "leave"
            elif self.move_to(self.acorn.x, self.SPEED, dt):
                self.state, self.timer = "nibble", 0.0
                self.anim.play("squirrel_sit")
                if self.has_cob:  # the cob is carried along (hidden in its arms), so it can be dropped
                    self.acorn.alpha = 0.0
                    self.acorn.carried = True
                    w.chase_squirrel(self)
                else:
                    self.acorn.gone = True  # picked up
        elif self.state == "nibble" and self.timer > 1.4:
            away = rng.uniform(160, 420) * w.scale * rng.choice((-1, 1))
            self.bury_x = max(40.0, min(w.width - 40.0, self.x + away))
            self.state = "carry"
            self.anim.play("squirrel_carry")
        elif self.state == "carry":
            chaser = next((f for f in w.of("fox") if f.step is not None and f.step.follow is self), None)
            if chaser is not None and abs(chaser.x - self.x) < 34 * w.scale:
                self.drop_prize()  # caught up with! it lets go and runs for it
                self.state = "leave"
                self.anim.play("squirrel_run")
            elif self.move_to(self.bury_x, self.CARRY_COB if self.has_cob else self.SPEED, dt):
                self.state, self.timer = "dig", 0.0
                self.anim.play("squirrel_dig")
        elif self.state == "dig" and self.timer > 2.2:
            w.add(Mound(w, self.x + 10 * w.scale * self.facing))
            if self.has_cob:
                self.acorn.gone = True  # buried after all
            self.state = "pat"
            self.timer = 0.0
            self.anim.play("squirrel_sit")
        elif self.state == "pat" and self.timer > 0.8:
            self.state = "leave"
            self.anim.play("squirrel_run")
        elif self.state == "leave":
            if self.move_to(self.leave_x(), self.SPEED * 1.2, dt):
                self.gone = True

    def drop_prize(self):
        """Let go of the corn cob where it is."""
        cob = self.acorn
        if self.has_cob and not cob.gone:
            cob.x, cob.y = self.x + self.facing * 8 * self.world.scale, self.world.ground
            cob.alpha, cob.carried, cob.taken, cob.on_ground = 1.0, False, False, True
            cob.vx = self.facing * 40 * self.world.scale
        self.has_cob = False


class Jay(Visitor):
    """Flies in, sits on a branch of the oak, hops about, flies away."""
    kind = "jay"
    z = 28

    def __init__(self, world, tree):
        rng = world.rng
        start = rng.choice((-30.0, world.width + 30.0))
        super().__init__(world, start, world.ground - rng.uniform(300, 500) * world.scale / 2, "jay_fly")
        self.tree = tree
        self.state = "arrive"
        self.timer = 0.0
        self.perch = rng.choice(tree.perch_points())
        self.stay = rng.uniform(5, 12)

    def fly_to(self, x, y, dt, speed=110):
        dx, dy = x - self.x, y - self.y
        dist = math.hypot(dx, dy)
        step = speed * self.world.scale * dt
        if dx:
            self.facing = 1 if dx > 0 else -1
        if dist <= step:
            self.x, self.y = x, y
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def update(self, dt):
        super().update(dt)
        self.timer += dt
        rng = self.world.rng
        if self.tree.gone and self.state != "leave":
            self.state = "leave"
        if self.state == "arrive" and self.fly_to(*self.perch, dt):
            self.state, self.timer = "perch", 0.0
            self.anim.play("jay_perch")
        elif self.state == "perch":
            if self.timer > self.stay:
                self.state = "leave"
                self.anim.play("jay_fly")
                self.exit = (rng.choice((-40.0, self.world.width + 40.0)), self.y - 300 * self.world.scale)
            elif rng.random() < dt * 0.4:
                self.anim.play("jay_hop")
                self.facing = -self.facing
            elif self.anim.name == "jay_hop" and self.anim.time > 0.45:
                self.anim.play("jay_perch")
        elif self.state == "leave":
            target = getattr(self, "exit", (-40.0, -40.0))
            if self.fly_to(*target, dt, speed=140):
                self.gone = True


class Woolly(Visitor):
    """A fuzzy woolly bear caterpillar inching across the bottom of the screen."""
    kind = "woolly"
    z = 24
    SPEED = 7

    def __init__(self, world):
        left = world.rng.random() < 0.5
        super().__init__(world, -20.0 if left else world.width + 20.0, world.ground, "woolly")
        self.facing = 1 if left else -1
        self.target = world.width + 30.0 if left else -30.0

    def update(self, dt):
        super().update(dt)
        if self.move_to(self.target, self.SPEED, dt):
            self.gone = True


class Migrant(Visitor):
    """One goose in a V high up, flying south: right to left across the screen."""
    kind = "migrant"
    z = 2  # far away, so behind everything

    def __init__(self, world, x, y, speed):
        super().__init__(world, x, y, "goose_far")
        self.facing = -1
        self.speed = speed
        self.base_y = y
        self.anim.time = world.rng.uniform(0, 1)
        self.phase = world.rng.uniform(0, 6.3)

    def update(self, dt):
        super().update(dt)
        self.phase += dt * 1.3
        self.x -= self.speed * self.world.scale * dt
        self.y = self.base_y + math.sin(self.phase) * 2 * self.world.scale
        if self.x < -60:
            self.gone = True


def migrating_v(world):
    """A V of 5 to 9 geese entering from the right, high on the screen."""
    rng, s = world.rng, world.scale
    count = rng.choice((5, 7, 9))
    lead_x = world.width + 40.0
    lead_y = world.height * rng.uniform(0.12, 0.35)
    speed = rng.uniform(38, 50)
    geese = [Migrant(world, lead_x, lead_y, speed)]
    for i in range(1, count // 2 + 1):  # two trailing arms behind the leader
        for arm in (-1, 1):
            if len(geese) < count:
                geese.append(Migrant(world, lead_x + i * 13 * s, lead_y + arm * i * 7 * s, speed))
    return geese


class Bubble(Thing):
    """A HONK! speech bubble over a goose for a moment."""
    kind = "bubble"
    z = 40

    def __init__(self, world, goose, sprite="honk_bubble", rise=30):
        super().__init__(world, goose.x, goose.y, sprite)
        self.goose = goose
        self.rise = rise
        self.life = 1.1

    def update(self, dt):
        s = self.world.scale
        self.x = self.goose.x + self.goose.facing * 8 * s
        self.y = self.goose.y - self.rise * s
        self.life -= dt
        if self.life <= 0 or self.goose.gone:
            self.gone = True


class Goose(Visitor):
    """A Canada goose that drops in on its way south, waddles about honking at the foxes, then flies on."""
    kind = "goose"
    z = 23

    def __init__(self, world, land_x, delay):
        rng = world.rng
        super().__init__(world, world.width + 40 + delay * 60, world.height * rng.uniform(0.25, 0.4), "goose_fly")
        self.facing = -1
        self.land_x = land_x
        self.delay = delay
        self.state = "arrive"
        self.timer = 0.0
        self.honks = rng.randint(6, 10)  # they stay a good while: waddling about, honking now and then
        self.waddle_to = land_x
        self.linger = 4.0
        self.exit = (-60.0, 0.0)

    def fly_to(self, x, y, dt, speed=130):
        dx, dy = x - self.x, y - self.y
        dist = math.hypot(dx, dy)
        step = speed * self.world.scale * dt
        if abs(dx) > 1:
            self.facing = 1 if dx > 0 else -1
        if dist <= step:
            self.x, self.y = x, y
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def update(self, dt):
        super().update(dt)
        self.timer += dt
        w, rng = self.world, self.world.rng
        if self.state == "arrive":
            if self.timer < self.delay:
                return
            if self.fly_to(self.land_x, w.ground, dt):
                self.state, self.timer = "waddle", 0.0
                self.anim.play("goose_walk")
                self.waddle_to = max(40.0, min(w.width - 40.0, self.land_x + rng.uniform(-40, 40) * w.scale))
        elif self.state == "waddle":
            if self.move_to(self.waddle_to, 10, dt) or self.timer > self.linger:
                fox = w.nearest_fox(self.x)
                if fox is not None and abs(fox.x - self.x) > 2:
                    self.facing = 1 if fox.x > self.x else -1
                self.state, self.timer = "honk", 0.0
                self.anim.play("goose_honk")
                w.add(Bubble(w, self))
                w.honk(self)
        elif self.state == "honk":
            if self.timer > 1.4:
                self.honks -= 1
                if self.honks > 0:
                    self.state, self.timer = "waddle", 0.0
                    self.anim.play("goose_walk")
                    self.waddle_to = max(40.0, min(w.width - 40.0, self.x + rng.uniform(-45, 45) * w.scale))
                    self.linger = rng.uniform(3, 8)
                else:
                    self.state = "leave"
                    self.anim.play("goose_fly")
                    self.exit = (-60.0, w.height * rng.uniform(0.1, 0.3))  # on south: right to left
        elif self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=150):
                self.gone = True


class Frog(Visitor):
    """A frog that hops out of the den when you knock, ribbits a couple of times, and hops away."""
    kind = "frog"
    z = 24

    def __init__(self, world, x):
        super().__init__(world, x, world.ground, "frog_sit")
        self.facing = world.rng.choice((-1, 1))
        self.state = "out"
        self.timer = 0.0
        self.ribbits = world.rng.randint(2, 3)
        self.hop_to = x + self.facing * 30 * world.scale

    def update(self, dt):
        super().update(dt)
        self.timer += dt
        w = self.world
        if self.state == "out":  # one hop out of the doorway
            self.anim.play("frog_hop")
            if self.move_to(self.hop_to, 40, dt):
                self.state, self.timer = "sit", 0.0
                self.anim.play("frog_sit")
        elif self.state == "sit" and self.timer > 1.0:
            if self.ribbits > 0:
                self.ribbits -= 1
                self.timer = 0.0
                w.add(Bubble(w, self, "ribbit_bubble", rise=18))
            else:
                self.state = "away"
                self.anim.play("frog_hop")
        elif self.state == "away":
            if self.move_to(self.leave_x(), 45, dt):
                self.gone = True


class TurkeyFlock:
    """A flock of wild turkeys and their shared plan: dash to the next stopping place, stop there together to
    look around, peck and gobble, then dash on, and finally run off the far side of the screen."""

    def __init__(self, world, count):
        rng, w = world.rng, world
        self.world = world
        self.dir = rng.choice((-1, 1))  # 1: in from the left, running right
        stops = rng.randint(2, 4)
        span = w.width / (stops + 1)
        xs = [(i + 1) * span + rng.uniform(-0.25, 0.25) * span for i in range(stops)]
        self.stops = xs if self.dir > 0 else [w.width - x for x in xs]
        self.leg = 0
        self.state = "run"
        self.timer = 0.0
        self.stop_for = 0.0
        self.members = [Turkey(world, self, i) for i in range(count)]

    @property
    def last_leg(self):
        return self.leg >= len(self.stops)

    def target(self, turkey):
        if self.last_leg:  # off the far side, each at its own pace
            return self.world.width + 60.0 if self.dir > 0 else -60.0
        return max(30.0, min(self.world.width - 30.0, self.stops[self.leg] + turkey.offset))

    def tick(self, caller, dt):
        """Run once a frame, by the first turkey still about."""
        if caller is not next((t for t in self.members if not t.gone), None):
            return
        if self.state == "run" and not self.last_leg and all(t.state == "stopped" for t in self.members):
            self.state, self.timer = "stop", 0.0
            self.stop_for = self.world.rng.uniform(6, 12)
        elif self.state == "stop":
            self.timer += dt
            if self.timer > self.stop_for:
                self.leg += 1
                self.state = "run"
                for t in self.members:
                    t.run()

    def answer(self, gobbler):
        """One turkey gobbled: some of the others gobble back."""
        for t in self.members:
            if t is not gobbler and t.state == "stopped" and t.answer_in is None and self.world.rng.random() < 0.5:
                t.answer_in = self.world.rng.uniform(0.4, 1.1)


class Turkey(Visitor):
    """One wild turkey in a flock (see TurkeyFlock): runs in, stops to look around and gobble, runs on."""
    kind = "turkey"
    z = 23

    def __init__(self, world, flock, index):
        rng, s = world.rng, world.scale
        edge = -40.0 if flock.dir > 0 else world.width + 40.0
        super().__init__(world, edge - flock.dir * index * 34 * s, world.ground, "turkey_run")
        self.flock = flock
        self.facing = flock.dir
        self.offset = -flock.dir * (index * 30 + rng.uniform(-8, 8)) * s  # strung out behind the leader
        self.speed = rng.uniform(130, 170)
        self.state = "run"
        self.timer = 0.0
        self.act_left = 0.0
        self.answer_in = None
        self.anim.time = rng.uniform(0, 1)

    def run(self):
        self.state = "run"
        self.answer_in = None
        self.anim.play("turkey_run")

    def gobble(self, answering=False):
        w = self.world
        self.anim.play("turkey_gobble")
        self.act_left = 1.5
        w.add(Bubble(w, self, "gobble_bubble", rise=40))
        if not answering:
            w.honk(self)  # the foxes notice, same as a goose's honk
            self.flock.answer(self)

    def update(self, dt):
        super().update(dt)
        self.flock.tick(self, dt)
        rng = self.world.rng
        if self.state == "run":
            target = self.flock.target(self)
            if self.move_to(target, self.speed, dt):
                if self.flock.last_leg:
                    self.gone = True
                else:
                    self.state, self.timer = "stopped", 0.0
                    self.act_left = rng.uniform(0.2, 0.8)
                    self.anim.play("turkey_stand")
        elif self.state == "stopped":
            self.timer += dt
            if self.answer_in is not None:
                self.answer_in -= dt
                if self.answer_in <= 0:
                    self.answer_in = None
                    self.gobble(answering=True)
                    return
            self.act_left -= dt
            if self.act_left > 0:
                return
            roll = rng.random()
            if roll < 0.45:  # look around: head up, glancing about, sometimes turning the other way
                self.anim.play("turkey_look")
                if rng.random() < 0.5:
                    self.facing = -self.facing
                self.act_left = rng.uniform(1.3, 2.6)
            elif roll < 0.75:
                self.anim.play("turkey_peck")
                self.act_left = rng.uniform(1.0, 2.5)
            elif roll < 0.87:
                self.anim.play("turkey_stand")
                self.act_left = rng.uniform(0.8, 1.8)
            else:
                self.gobble()


def turkey_flock(world):
    """Three to six wild turkeys running in together."""
    return TurkeyFlock(world, world.rng.randint(3, 6)).members


class Perch:
    """Somewhere a crow can sit: a spot on something (sideways from its middle and up from its base, in
    sprite pixels, so it moves along when the thing is dragged), or a spot on the ground."""

    def __init__(self, holder=None, dx=0.0, dy=0.0, x=0.0):
        self.holder, self.dx, self.dy, self.x = holder, dx, dy, x

    @property
    def high(self):
        return self.holder is not None

    def pos(self, world):
        if self.holder is None:
            return self.x, world.ground
        s = world.scale
        return self.holder.x + self.dx * s, self.holder.y - self.dy * s

    def ok(self):
        """Still there to sit on (not taken away, knocked over or wilting)."""
        h = self.holder
        return h is None or (not h.gone and h.alpha >= 1 and getattr(h, "available", True) and
                             not getattr(h, "wilting", False) and not getattr(h, "bursting", False))


class HeadPerch(Perch):
    """The top of the scarecrow's head: on his hat, or (once a crow has pinched it) on the straw."""

    def __init__(self, scarecrow):
        super().__init__(scarecrow, 0, 0)

    def pos(self, world):
        self.dy = 72 if self.holder.hat_on else 66
        return super().pos(world)


# where a crow can sit on each kind of item, in sprite pixels from its anchor
SCARECROW_ARMS = [(-14, 51), (14, 51)]               # the two outstretched arms (and his head: HeadPerch)
DEN_PERCHES = [(-2, 32), (-20, 27), (18, 26)]        # the tops of the mound's lumps
PROP_PERCHES = {"sled": [(-8, 10), (8, 10)], "xmas_tree": [(0, 43)]}  # along the sled; on the star
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
        if thing.kind == "tree":
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


FAVOURITES = {"scarecrow": 6, "oak": 3}  # how much more a crow likes sitting there than anywhere else


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
        return Perch(x=max(30.0, min(w.width - 30.0, x)))

    def _landing_spots(self, count):
        """The first crow picks a spot (by some corn on the ground, up on something, or anywhere on the
        ground); the rest land close by."""
        w, rng = self.world, self.world.rng
        high = crow_perches(w)
        cobs = w.cobs_on_ground()
        hats = w.of("hat")
        if hats or (cobs and rng.random() < 0.7):  # a dropped hat, or corn: land right by it
            thing = hats[0] if hats else rng.choice(cobs)
            first = Perch(x=max(30.0, min(w.width - 30.0, thing.x + rng.choice((-1, 1)) * 16 * w.scale)))
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
        if getattr(thing, "is_cob", False):  # corn! peck the kernels off
            for _ in range(2):
                w.add(Kernel(w, thing.x + rng.uniform(-3, 3) * s, thing.y - 4 * s))
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
                x = max(30.0, min(w.width - 30.0, self.x + away * w.rng.uniform(50, 90) * w.scale))
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
                    self.strut_to = max(30.0, min(w.width - 30.0, self.x + rng.uniform(-40, 40) * s))
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


# -- small creatures on the oak, through the year -------------------------------------------------------

GRAVITY = 700  # sprite pixels per second squared (scaled), as for acorns


class Inchworm(Visitor):
    """A spring caterpillar shaken out of the oak: it drops, lands, and loops off as fast as it can."""
    kind = "inchworm"
    z = 24
    SPEED = 28

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "inchworm_fall")
        self.vy = 0.0
        self.state = "fall"

    def update(self, dt):
        super().update(dt)
        w = self.world
        if self.state == "fall":
            self.vy += GRAVITY * 0.7 * w.scale * dt
            self.y = min(w.ground, self.y + self.vy * dt)
            if self.y >= w.ground:
                self.state = "run"
                self.anim.play("inchworm")
        elif self.move_to(self.leave_x(), self.SPEED, dt):
            self.gone = True


class Butterfly(Visitor):
    """A butterfly that was resting in the summer oak: shaken out, it flutters up and away."""
    kind = "butterfly"
    z = 32

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "butterfly")
        rng = world.rng
        self.dir = rng.choice((-1, 1))
        self.phase = rng.uniform(0, 6.3)
        self.anim.time = rng.uniform(0, 1)

    def update(self, dt):
        super().update(dt)
        s = self.world.scale
        self.phase += dt * 5
        self.x += (self.dir * 45 + math.sin(self.phase * 0.7) * 30) * s * dt  # a wandering, fluttery path
        self.y += (-22 + math.sin(self.phase) * 40) * s * dt
        if self.x < -30 or self.x > self.world.width + 30 or self.y < -30:
            self.gone = True


class Beetle(Visitor):
    """A June beetle or a ladybug that climbs the summer oak's trunk, stops, then opens its wings and flies off."""
    kind = "beetle"
    z = 24
    CLIMB = 9  # sprite pixels a second

    def __init__(self, world, tree, species):
        rng = world.rng
        self.species = species  # "junebug" or "ladybug"
        super().__init__(world, tree.x + rng.uniform(-5, 5) * world.scale, world.ground, f"{species}_crawl")
        self.tree = tree
        self.offset = self.x - tree.x
        self.top = rng.uniform(80, 98)  # how high up the trunk it gets (sprite pixels)
        self.state = "climb"
        self.timer = 0.0
        self.rest_at = rng.uniform(25, 60)  # it stops for a breather on the way up
        self.dir = rng.choice((-1, 1))

    def update(self, dt):
        w, s, rng = self.world, self.world.scale, self.world.rng
        self.timer += dt
        if self.tree.gone and self.state != "fly":
            self.state = "fly"
            self.anim.play(f"{self.species}_fly")
        if self.state == "climb":
            super().update(dt)
            self.x = self.tree.x + self.offset  # stays on the trunk if the oak is dragged
            height = (w.ground - self.y) / s
            if self.rest_at and height > self.rest_at:
                self.rest_at, self.state, self.timer = None, "rest", 0.0
            elif height >= self.top:
                self.state, self.timer = "ready", 0.0
            else:
                self.y -= self.CLIMB * s * dt
        elif self.state == "rest":
            self.x = self.tree.x + self.offset
            if self.timer > rng.uniform(1.5, 3):
                self.state = "climb"
        elif self.state == "ready":
            self.x = self.tree.x + self.offset
            if self.timer > 1.2:
                self.state = "fly"
                self.anim.play(f"{self.species}_fly")
        else:  # away it goes, buzzing up and out
            super().update(dt)
            self.x += self.dir * 60 * s * dt
            self.y -= (40 + math.sin(self.timer * 9) * 25) * s * dt
            if self.x < -30 or self.x > w.width + 30 or self.y < -30:
                self.gone = True


class Cicada(Visitor):
    """An autumn cicada: it flies in, lands on the oak's trunk, buzzes loudly a few times, and flies off."""
    kind = "cicada"
    z = 24

    def __init__(self, world, tree):
        rng = world.rng
        start = rng.choice((-30.0, world.width + 30.0))
        super().__init__(world, start, world.ground - rng.uniform(150, 250) * world.scale, "cicada_fly")
        self.tree = tree
        self.offset = rng.uniform(-4, 4) * world.scale
        self.height = rng.uniform(40, 80)  # where on the trunk it lands (sprite pixels up)
        self.state = "arrive"
        self.timer = 0.0
        self.buzzes = rng.randint(3, 5)
        self.exit = (rng.choice((-40.0, world.width + 40.0)), world.ground - 300 * world.scale)

    def spot(self):
        return self.tree.x + self.offset, self.world.ground - self.height * self.world.scale

    def update(self, dt):
        super().update(dt)
        w, rng = self.world, self.world.rng
        self.timer += dt
        if self.tree.gone and self.state != "leave":
            self.state = "leave"
            self.anim.play("cicada_fly")
        if self.state == "arrive":
            if self.fly_to(*self.spot(), dt, speed=90):
                self.state, self.timer = "quiet", 0.0
                self.anim.play("cicada_sit")
                self.wait = rng.uniform(1, 2)
        elif self.state == "quiet":
            self.x, self.y = self.spot()
            if self.timer > self.wait:
                if self.buzzes > 0:  # BZZZZZ!
                    self.buzzes -= 1
                    self.state, self.timer = "buzz", 0.0
                    self.anim.play("cicada_buzz")
                    w.add(Bubble(w, self, "buzz_bubble", rise=20))
                    w.honk(self)  # the foxes prick up their ears
                else:
                    self.state = "leave"
                    self.anim.play("cicada_fly")
        elif self.state == "buzz":
            self.x, self.y = self.spot()
            if self.timer > 2.5:
                self.state, self.timer = "quiet", 0.0
                self.anim.play("cicada_sit")
                self.wait = rng.uniform(2, 4)
        elif self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=110):
                self.gone = True


class Silk(Thing):
    """One short length of a spider's thread (a thread is a column of these)."""
    kind = "silk"
    z = 4  # behind the oak, so the thread disappears up into the crown

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "silk")


class Spider(Visitor):
    """A spider shaken out of the autumn oak: it lets itself down on a thread, dangles, and climbs back up."""
    kind = "spider"
    z = 24

    def __init__(self, world, x, y):
        super().__init__(world, x, y, "spider")
        rng = world.rng
        self.top = y
        self.drop_to = y + rng.uniform(45, 85) * world.scale
        self.state = "down"
        self.timer = 0.0
        self.dangle = rng.uniform(2, 4)
        self.silk = []

    def _thread(self):
        """Keep the thread reaching from the crown down to the spider."""
        step = 6 * self.world.scale
        want = max(0, int((self.y - self.top) / step) + 1)
        while len(self.silk) < want:
            self.silk.append(self.world.add(Silk(self.world, self.x, self.top + len(self.silk) * step)))
        while len(self.silk) > want:
            self.silk.pop().gone = True
        for piece in self.silk:
            piece.x = self.x

    def update(self, dt):
        super().update(dt)
        s = self.world.scale
        self.timer += dt
        if self.state == "down":
            self.y = min(self.drop_to, self.y + 30 * s * dt)
            if self.y >= self.drop_to:
                self.state, self.timer = "dangle", 0.0
        elif self.state == "dangle":
            self.x += math.sin(self.timer * 3) * 3 * s * dt  # a little swing
            if self.timer > self.dangle:
                self.state = "up"
        else:
            self.y -= 18 * s * dt  # climbing back up, hand over hand
            if self.y <= self.top:
                self.gone = True
        self._thread()
        if self.gone:
            for piece in self.silk:
                piece.gone = True


# -- spring: butterflies among the flowers, and songbirds --------------------------------------------------

def flower_heads(world):
    """Every flower head in the flower beds that are out (screen coordinates)."""
    spots = []
    for thing in world.of("prop"):
        if thing.variant in ("daffodils", "tulips", "violets"):
            spots += thing.flower_heads()
    return spots


class Flutterby(Visitor):
    """A spring butterfly: it flutters in, lands on the flowers to rest a while (wings slowly opening and
    closing), flutters about some more, and goes on its way. With no flowers out, it just wanders through."""
    kind = "butterfly"
    z = 32
    KINDS = ("monarch", "white", "white", "sulphur", "azure")

    def __init__(self, world, species=None, x=None, y=None):
        rng, s = world.rng, world.scale
        self.species = species or rng.choice(self.KINDS)
        self.fly_sprite = "butterfly" if self.species == "monarch" else f"butterfly_{self.species}"
        if x is None:
            x = rng.choice((-20.0, world.width + 20.0))
            y = world.ground - rng.uniform(60, 160) * s
        super().__init__(world, x, y, self.fly_sprite)
        self.anim.time = rng.uniform(0, 1)
        self.visits = rng.randint(2, 4)
        self.state = "flutter"
        self.timer = 0.0
        self.phase = rng.uniform(0, 6.3)
        self.target = None
        self.rest_for = 0.0

    def _next_target(self):
        w, rng, s = self.world, self.world.rng, self.world.scale
        heads = flower_heads(w)
        if self.visits <= 0:
            return (rng.choice((-30.0, w.width + 30.0)), w.ground - rng.uniform(100, 220) * s), False
        if heads:
            near = [h for h in heads if abs(h[0] - self.x) < 600 * s] or heads
            return rng.choice(near), True
        return (max(20.0, min(w.width - 20.0, self.x + rng.uniform(-200, 200) * s)),
                w.ground - rng.uniform(40, 140) * s), False

    def update(self, dt):
        super().update(dt)
        w, rng, s = self.world, self.world.rng, self.world.scale
        self.timer += dt
        self.phase += dt * 6
        if self.state == "flutter":
            if self.target is None:
                self.target, self.landing = self._next_target()
            tx, ty = self.target
            if self.landing:  # the flower may have been dragged: aim at where it is now
                heads = flower_heads(w)
                if heads:
                    tx, ty = min(heads, key=lambda h: abs(h[0] - tx) + abs(h[1] - ty))
                    self.target = (tx, ty)
                else:
                    self.landing = False
            wobble = math.sin(self.phase) * 30 * s  # bobbing up and down as it flies
            if self.fly_to(tx, ty + (0 if self.landing and abs(self.x - tx) < 20 * s else wobble * 0.3), dt,
                           speed=55) or (abs(self.x - tx) < 2 and abs(self.y - ty) < 4 * s):
                if self.landing:
                    self.x, self.y = tx, ty  # right on the flower
                    self.state, self.timer = "rest", 0.0
                    self.rest_for = rng.uniform(3, 8)
                    self.visits -= 1
                    self.anim.play(f"butterfly_{self.species}_rest")
                elif self.visits <= 0 and (self.x < -20 or self.x > w.width + 20):
                    self.gone = True
                else:
                    if self.visits > 0 and not flower_heads(w):
                        self.visits -= 1  # wandering about with nowhere to land
                    self.target = None
            if self.state == "flutter":  # bobbing in the air (not once it's landed)
                self.y += math.sin(self.phase) * 12 * s * dt
        elif self.state == "rest":
            heads = flower_heads(w)
            if heads:  # sitting on its flower, wherever the bed is moved to
                self.x, self.y = min(heads, key=lambda h: abs(h[0] - self.x) + abs(h[1] - self.y))
            fox_near = any(abs(f.x - self.x) < 40 * s and f.step is not None and f.step.anim != "watch"
                           for f in w.of("fox"))
            if self.timer > self.rest_for or fox_near or not heads:
                self.state, self.target = "flutter", None
                self.anim.play(self.fly_sprite)

    def click(self):
        self.visits = 0  # shoo
        self.state, self.target = "flutter", None
        self.anim.play(self.fly_sprite)


class SongBird(Visitor):
    """A robin, bluebird or goldfinch dropping by in spring: it perches in the oak or on something (or hops
    about on the ground), sings now and then, with music notes floating up, and the foxes stop to listen.
    A robin on the ground sometimes tugs a worm out. Click it, or dash a fox at it, and it flies off."""
    kind = "songbird"
    z = 27

    def __init__(self, world, species, delay=0.0):
        rng = world.rng
        start = rng.choice((-30.0, world.width + 30.0))
        super().__init__(world, start, world.ground - rng.uniform(150, 260) * world.scale, f"{species}_fly")
        self.species = species
        self.delay = delay
        self.state = "arrive"
        self.timer = 0.0
        self.stay = rng.uniform(35, 70)
        self.sing_in = rng.uniform(1.5, 4)
        self.perch = self._choose_perch()
        self.exit = (rng.choice((-40.0, world.width + 40.0)), world.ground - 300 * world.scale)

    def _choose_perch(self):
        w, rng = self.world, self.world.rng
        spots = crow_perches(w)
        trees = [p for p in spots if getattr(p.holder, "kind", None) == "tree"]
        if self.species == "robin" and rng.random() < 0.55 or not spots:  # robins like the ground
            return Perch(x=rng.uniform(0.1, 0.9) * w.width)
        return rng.choice(trees) if trees and rng.random() < 0.6 else rng.choice(spots)

    def sing(self):
        w, rng, s = self.world, self.world.rng, self.world.scale
        self.state, self.timer = "sing", 0.0
        self.anim.play(f"{self.species}_sing")
        for k in range(rng.randint(2, 3)):
            w.add(Note(w, self.x + self.facing * (8 + k * 3) * s, self.y - (16 + k * 2) * s, double=rng.random() < 0.4))
        if rng.random() < 0.5:
            w.honk(self)  # the foxes prick up their ears and listen

    def fly_off(self):
        if self.state != "leave":
            self.state = "leave"
            self.anim.play(f"{self.species}_fly")

    def click(self):
        self.fly_off()

    def update(self, dt):
        super().update(dt)
        w, rng, s = self.world, self.world.rng, self.world.scale
        self.timer += dt
        if self.state == "arrive":
            if self.timer < self.delay:
                return
            if not self.perch.ok():
                self.perch = Perch(x=self.x)
            if self.fly_to(*self.perch.pos(w), dt, speed=120):
                self.state, self.timer = "perch", 0.0
                self.anim.play(f"{self.species}_perch")
            return
        if self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=140):
                self.gone = True
            return
        if not self.perch.ok():
            return self.fly_off()
        if self.state != "hop":
            self.x, self.y = self.perch.pos(w)
        self.stay -= dt
        on_ground = not self.perch.high
        if on_ground and any(abs(f.x - self.x) < 40 * s and f.step is not None and
                             f.step.anim in ("run", "trot", "pounce", "dive") for f in w.of("fox")):
            return self.fly_off()
        if self.stay <= 0:
            return self.fly_off()
        if self.state == "perch":
            self.sing_in -= dt
            if self.sing_in <= 0:
                self.sing_in = rng.uniform(3, 7)
                return self.sing()
            roll = rng.random()
            if roll < dt * 0.3:
                self.facing = -self.facing
            elif on_ground and roll < dt * 0.8:  # hopping about, pecking, maybe a worm
                if self.species == "robin" and rng.random() < 0.35:
                    self.state, self.timer = "worm", 0.0
                    self.anim.play("robin_worm")
                elif rng.random() < 0.5:
                    self.state, self.timer = "peck", 0.0
                    self.anim.play(f"{self.species}_peck")
                else:
                    self.hop_to = max(30.0, min(w.width - 30.0, self.x + rng.uniform(-30, 30) * s))
                    self.state = "hop"
                    self.anim.play(f"{self.species}_hop")
        elif self.state in ("sing", "peck", "worm"):
            if self.timer > {"sing": 1.2, "peck": 1.5, "worm": 2.6}[self.state]:
                self.state = "perch"
                self.anim.play(f"{self.species}_perch")
        elif self.state == "hop":
            if self.move_to(self.hop_to, 30, dt):
                self.perch = Perch(x=self.x)
                self.state = "perch"
                self.anim.play(f"{self.species}_perch")


def songbirds(world):
    """One songbird, or a pair of the same kind."""
    species = world.rng.choice(("robin", "robin", "bluebird", "goldfinch"))
    return [SongBird(world, species, delay=i * 1.5) for i in range(world.rng.choice((1, 1, 2)))]
