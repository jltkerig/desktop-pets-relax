"""Autumn visitors (and the frog): the squirrel, the blue jay, the woolly bear, geese flying over and
dropping in, the frog, and flocks of wild turkeys."""
import math

from pet.items import Mound
from .base import Bubble, Visitor


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
            if self.acorn.gone or getattr(self.acorn, "held", False):
                self.state = "leave"  # gone, or you snatched it first
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
    """A flock of wild turkeys (mostly hens, and a tom or two) and their shared plan: dash to the next stopping place, stop there together to
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
        # mostly hens, with a tom or two among them
        toms = set(rng.sample(range(count), rng.randint(1, max(1, count // 3))))
        self.hens = [i not in toms for i in range(count)]
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
        self.hen = flock.hens[index]
        self.look = "turkey_hen" if self.hen else "turkey"
        self.anim.play(f"{self.look}_run")
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
        self.anim.play(f"{self.look}_run")

    def gobble(self, answering=False):
        w = self.world
        if self.hen:  # a hen doesn't gobble: she clucks
            self.anim.play("turkey_hen_call")
            self.act_left = 1.0
            w.add(Bubble(w, self, "cluck_bubble", rise=36))
        else:
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
                    self.anim.play(f"{self.look}_stand")
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
                self.anim.play(f"{self.look}_look")
                if rng.random() < 0.5:
                    self.facing = -self.facing
                self.act_left = rng.uniform(1.3, 2.6)
            elif roll < 0.75:
                self.anim.play(f"{self.look}_peck")
                self.act_left = rng.uniform(1.0, 2.5)
            elif roll < 0.87:
                self.anim.play(f"{self.look}_stand")
                self.act_left = rng.uniform(0.8, 1.8)
            else:
                self.gobble()


def turkey_flock(world):
    """Three to six wild turkeys running in together."""
    return TurkeyFlock(world, world.rng.randint(3, 6)).members
