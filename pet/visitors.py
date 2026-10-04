"""Creatures that drop by on their own: the squirrel, the blue jay and the woolly bear caterpillar."""
import math

from pet.items import Mound
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


class Squirrel(Visitor):
    """Runs in, takes an acorn off the ground, buries it somewhere else, and runs off."""
    kind = "squirrel"
    SPEED = 120

    def __init__(self, world, acorn):
        edge = -30.0 if acorn.x > world.width / 2 or world.rng.random() < 0.5 else world.width + 30.0
        super().__init__(world, edge, world.ground, "squirrel_run")
        self.acorn = acorn
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
                self.acorn.gone = True  # picked up
                self.state, self.timer = "nibble", 0.0
                self.anim.play("squirrel_sit")
        elif self.state == "nibble" and self.timer > 1.4:
            away = rng.uniform(160, 420) * w.scale * rng.choice((-1, 1))
            self.bury_x = max(40.0, min(w.width - 40.0, self.x + away))
            self.state = "carry"
            self.anim.play("squirrel_carry")
        elif self.state == "carry" and self.move_to(self.bury_x, self.SPEED, dt):
            self.state, self.timer = "dig", 0.0
            self.anim.play("squirrel_dig")
        elif self.state == "dig" and self.timer > 2.2:
            w.add(Mound(w, self.x + 10 * w.scale * self.facing))
            self.state = "pat"
            self.timer = 0.0
            self.anim.play("squirrel_sit")
        elif self.state == "pat" and self.timer > 0.8:
            self.state = "leave"
            self.anim.play("squirrel_run")
        elif self.state == "leave":
            if self.move_to(self.leave_x(), self.SPEED * 1.2, dt):
                self.gone = True


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

    def __init__(self, world, goose):
        super().__init__(world, goose.x, goose.y, "honk_bubble")
        self.goose = goose
        self.life = 1.1

    def update(self, dt):
        s = self.world.scale
        self.x = self.goose.x + self.goose.facing * 8 * s
        self.y = self.goose.y - 30 * s
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
        self.honks = rng.randint(2, 4)
        self.waddle_to = land_x
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
            if self.move_to(self.waddle_to, 14, dt) or self.timer > 4:
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
                    self.waddle_to = max(40.0, min(w.width - 40.0, self.x + rng.uniform(-30, 30) * w.scale))
                else:
                    self.state = "leave"
                    self.anim.play("goose_fly")
                    self.exit = (-60.0, w.height * rng.uniform(0.1, 0.3))  # on south: right to left
        elif self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=150):
                self.gone = True
