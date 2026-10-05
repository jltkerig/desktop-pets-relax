"""Night visitors: the owl in the oak or the birch."""
from .base import Bubble, Visitor


class Owl(Visitor):
    """A great horned owl that comes to the oak (or the birch) after dark: it perches on a branch, blinks, turns
    its head right round now and then, and hoots softly. It flies off at dawn, or if you click it."""
    kind = "owl"
    z = 27

    def __init__(self, world):
        rng, s = world.rng, world.scale
        start = rng.choice((-30.0, world.width + 30.0))
        super().__init__(world, start, world.ground - rng.uniform(220, 320) * s, "owl_fly")
        trees = world.of("tree") + world.of("birch")
        self.tree = rng.choice(trees) if trees else None
        self.perch = rng.choice([p for p in self.tree.perch_points()]) if self.tree else (start, self.y)
        self.offset = (self.perch[0] - self.tree.x, self.perch[1] - self.tree.y) if self.tree else (0.0, 0.0)
        self.state = "arrive"
        self.timer = 0.0
        self.stay = rng.uniform(4, 10) * 60
        self.next_act = rng.uniform(4, 10)
        self.exit = (rng.choice((-40.0, world.width + 40.0)), world.ground - 380 * s)

    def spot(self):
        return self.tree.x + self.offset[0], self.tree.y + self.offset[1]

    def click(self):
        self.fly_off()

    def fly_off(self):
        if self.state != "leave":
            self.state = "leave"
            self.anim.play("owl_fly")

    def update(self, dt):
        super().update(dt)
        w, rng = self.world, self.world.rng
        self.timer += dt
        if self.state != "leave" and (self.tree is None or self.tree.gone):
            return self.fly_off()
        if self.state == "arrive":
            if self.fly_to(*self.spot(), dt, speed=80):
                self.state, self.timer = "perch", 0.0
                self.anim.play("owl_perch")
        elif self.state == "perch":
            self.x, self.y = self.spot()
            if self.timer > self.stay or w.daylight() in ("day", "dawn") and self.timer > 20:
                return self.fly_off()
            self.next_act -= dt
            if self.anim.name != "owl_perch" and self.next_act < 0.5:
                self.anim.play("owl_perch")
            if self.next_act <= 0:
                self.next_act = rng.uniform(5, 14)
                if rng.random() < 0.55:  # a soft hoot
                    self.anim.play("owl_hoot")
                    w.add(Bubble(w, self, "hoo_bubble", rise=26))
                else:  # it swivels its head right round, then back
                    self.anim.play("owl_turn")
                    self.next_act = rng.uniform(1.5, 3)
        elif self.state == "leave":
            if self.fly_to(*self.exit, dt, speed=100):
                self.gone = True
