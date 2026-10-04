"""Creatures that drop by on their own: the squirrel, the blue jay, the woolly bear caterpillar, geese,
wild turkeys and crows."""
import math

from pet.items import Mound, StrawBit
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
                             not getattr(h, "wilting", False))


# where a crow can sit on each kind of item, in sprite pixels from its anchor
SCARECROW_PERCHES = [(0, 66), (-14, 51), (14, 51)]  # the hat and the two outstretched arms
DEN_PERCHES = [(-2, 32), (-20, 27), (18, 26)]        # the tops of the mound's lumps
PUMPKIN_HEIGHT = {"s": 0.75, "m": 1.0, "l": 1.3}
PUMPKIN_SHAPE_HEIGHT = {"round": 1.0, "tall": 1.32, "squat": 0.74}


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
            spots += [Perch(thing, dx, dy) for dx, dy in SCARECROW_PERCHES]
        elif thing.kind == "climb" and thing.available:
            spots += [Perch(thing, dx, dy) for dx, dy in thing.levels]
        elif thing.kind == "den":
            spots += [Perch(thing, dx, dy) for dx, dy in DEN_PERCHES]
        elif thing.kind == "pumpkin" and thing.ripe:
            top = 12.8 * PUMPKIN_HEIGHT[thing.size] * PUMPKIN_SHAPE_HEIGHT[thing.shape]
            spots.append(Perch(thing, 0, top))
    return [p for p in spots if p.ok() and 20 < p.pos(world)[0] < world.width - 20]


class CrowParty:
    """Two or more crows visiting together: they land near each other, and leave together. On a long visit
    they come down to look at the things lying about and play with them."""

    def __init__(self, world, count):
        rng = world.rng
        self.world = world
        self.side = rng.choice((-1, 1))  # which edge they come in from (-1: the left)
        self.long = rng.random() < 0.6
        self.stay = rng.uniform(45, 90) if self.long else rng.uniform(12, 22)
        self.timer = 0.0
        self.leaving = False
        self.spots = self._landing_spots(count)
        self.members = [Crow(world, self, spot, delay=i * rng.uniform(0.3, 0.8)) for i, spot in enumerate(self.spots)]

    def ground_spot_near(self, x):
        w, rng = self.world, self.world.rng
        x += rng.uniform(25, 80) * w.scale * rng.choice((-1, 1))
        return Perch(x=max(30.0, min(w.width - 30.0, x)))

    def _landing_spots(self, count):
        """The first crow picks a spot (up on something, or on the ground); the rest land close by."""
        w, rng = self.world, self.world.rng
        high = crow_perches(w)
        if high and rng.random() < 0.75:
            first = rng.choice(high)
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

    def tick(self, caller, dt):
        if caller is not next((c for c in self.members if not c.gone), None):
            return
        self.timer += dt
        if not self.leaving and self.timer > self.stay:
            caller.caw()  # time to go: one calls, and they all take off
            self.leave(delay=True)

    def leave(self, delay=False):
        if self.leaving:
            return
        self.leaving = True
        exit_x = -60.0 if self.world.rng.random() < 0.5 else self.world.width + 60.0
        for c in self.members:
            c.take_off(exit_x, self.world.rng.uniform(0.2, 1.0) if delay else 0.0)

    def startle(self, crow):
        """A click, or a fox dashing at them: a caw, and the whole party flies off at once."""
        if not self.leaving:
            crow.caw()
            self.leave()

    def taken(self, thing):
        return any(c.item is thing for c in self.members if not c.gone)


class Crow(Visitor):
    """One crow in a party (see CrowParty). Sits about on branches, on things or on the ground, hopping, cawing
    and cocking its head; on a long visit it walks up to things and plays with them: rolling acorns and corn
    cobs, flipping leaves, tugging straw out of the haystack, tapping pumpkins, or carrying an acorn up to a
    perch and dropping it."""
    kind = "crow"
    z = 28
    FLY = 120
    WALK = 22

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
        self.exit = (start, 0.0)
        self.anim.time = rng.uniform(0, 1)

    # -- things that happen to it ----------------------------------------------------------------------

    def click(self):
        self.party.startle(self)

    def caw(self):
        w = self.world
        if self.state in ("sit", "inspect", "play", "walk"):
            self.anim.play("crow_caw")
        w.add(Bubble(w, self, "caw_bubble", rise=26))

    def take_off(self, exit_x, delay):
        self.drop()
        self.state, self.timer, self.delay = "leave", 0.0, delay
        self.exit = (exit_x, self.world.height * self.world.rng.uniform(0.05, 0.25))

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
        self.anim.play("crow_perch")

    def _fly(self, perch, state="fly"):
        self.perch = perch
        self.state = state
        self.anim.play("crow_carry" if self.carrying else "crow_fly")

    def _something_to_look_at(self):
        """A thing lying about near the party that no other crow is busy with."""
        w = self.world
        centre = self.party.centre()
        picks = []
        for t in w.things:
            if t.gone or t.alpha < 1 or self.party.taken(t) or abs(t.x - centre) > 320 * w.scale:
                continue
            if t.kind == "acorn" and t.on_ground and not t.taken:
                picks += [t, t]  # the favourite
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
        if thing.kind == "acorn":
            if not getattr(thing, "is_cob", False) and not thing.taken and self.carrying is None and \
                    rng.random() < 0.45:
                thing.taken, thing.alpha = True, 0.0  # up into its beak
                self.carrying = thing
                return True
            thing.vx = self.facing * rng.uniform(40, 80) * s  # a shove with the beak: it rolls
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

    def _flee_check(self):
        """A fox dashing up to a crow on the ground or low down sends the whole party off."""
        if self.y < self.world.ground - 40 * self.world.scale:
            return
        for fox in self.world.of("fox"):
            dashing = fox.step is not None and fox.step.anim in ("run", "trot", "pounce", "dive", "hop")
            if dashing and abs(fox.x - self.x) < 50 * self.world.scale:
                self.party.startle(self)
                return

    def update(self, dt):
        super().update(dt)
        self.party.tick(self, dt)
        self.timer += dt
        w, rng, s = self.world, self.world.rng, self.world.scale
        if self.state not in ("arrive", "leave"):
            self._flee_check()
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
                    self.anim.play("crow_tilt")
        elif self.state == "sit":
            if not self.perch.ok():  # its perch was knocked over or carried off: down to the ground
                return self._fly(self.party.ground_spot_near(self.x))
            self.x, self.y = self.perch.pos(w)
            if self.anim.done or (self.anim.name == "crow_hop" and self.anim.time > 0.4):
                self.anim.play("crow_perch")
            if self.party.long and not self.party.leaving and self.timer > self.settle:
                self.item = self._something_to_look_at()
                if self.item is not None:
                    self.settle = rng.uniform(5, 12)
                    if self.perch.high:  # flutter down beside it first
                        side = 1 if self.x < self.item.x else -1
                        return self._fly(Perch(x=self.item.x - side * 14 * s), state="down")
                    self.state = "walk"
                    self.anim.play("crow_walk")
                    return
                self.timer = 0.0
            roll = rng.random()
            if roll < dt * 0.35:
                self.anim.play("crow_hop")
                self.facing = -self.facing
            elif roll < dt * 0.45:
                self.caw()
            elif roll < dt * 0.6:
                self.anim.play("crow_tilt")
        elif self.state == "down":
            if self.fly_to(*self.perch.pos(w), dt, speed=self.FLY):
                self.perch = Perch(x=self.x)
                self.state = "walk"
                self.anim.play("crow_walk")
        elif self.state == "walk":
            item = self.item
            if item is None or item.gone or item.alpha < 1:
                return self._sit(Perch(x=self.x))
            side = 1 if self.x < item.x else -1
            if self.move_to(item.x - side * 12 * s, self.WALK, dt):
                self.facing = side
                self.state, self.timer = "inspect", 0.0
                self.anim.play("crow_tilt")
        elif self.state == "inspect" and self.timer > 1.6:  # a long, thoughtful look first
            self.state, self.timer = "play", 0.0
            self.play_for = rng.uniform(2.5, 4.0)
            self.anim.play("crow_peck")
            if self._play_with(self.item):
                return self._carry_off()
        elif self.state == "play":
            if self.item is not None and rng.random() < dt * 0.8 and self.timer > 0.8:
                if self._play_with(self.item):  # another go
                    return self._carry_off()
            if self.timer > self.play_for:
                self.item = None
                if rng.random() < 0.5:  # back up to sit with the others
                    up = [p for p in crow_perches(w) if abs(p.pos(w)[0] - self.party.centre()) < 160 * s]
                    if up:
                        return self._fly(rng.choice(up))
                self._sit(Perch(x=self.x))
        elif self.state == "leave":
            if self.timer < self.delay:
                return
            self.anim.play("crow_fly")
            if self.fly_to(*self.exit, dt, speed=150):
                self.gone = True


def crow_party(world):
    """Two to four crows, landing near each other."""
    return CrowParty(world, world.rng.choice((2, 2, 3, 4))).members
