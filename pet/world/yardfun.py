"""The newer seasonal things in the world: putting them out (from rebuild), what happens to them every frame
(puddles after rain, muddy paws, foxes chasing the kite), the choices they add to a fox's list of things to do,
and the foxes chasing toys you throw. The games themselves are in fun_winter, fun_spring and fun_summer."""
from pet.fox import Step, TROT, ZOOM
from pet.items import (
    BeachBall, Feeder, FireflyJar, Gifts, Hammock, Kite, Nest, Pond, Puddle, Snowball, SnowballPile, Snowman,
    Sprinkler, Sunflowers, WateringCan)

# the yard things: their class, and where each goes the first time (a share of the width of all the monitors)
YARD_ITEMS = {
    "snowman": (Snowman, 0.18), "snowballs": (SnowballPile, 0.225), "pond": (Pond, 0.105), "feeder": (Feeder, 0.81),
    "gifts": (Gifts, 0.345), "sprinkler": (Sprinkler, 0.615), "hammock": (Hammock, 0.265),
    "firefly_jar": (FireflyJar, 0.775), "sunflowers": (Sunflowers, 0.925),
}


class YardFun:
    """Part of World (see pet/world/__init__.py)."""

    def put_out_fun(self, wanted):
        """Put out (or take in) the newer seasonal things, as the settings and season ask."""
        s = self.scale
        for name, (cls, share) in YARD_ITEMS.items():
            have = [t for t in self.of("yard") if t.variant == name]
            if name in wanted and not have:
                x = self.settings["items"].get(name, {}).get("x")
                if not (isinstance(x, (int, float)) and 0 < x < self.width):
                    x = max(40.0, min(self.width - 40.0, self.width * share))
                self.add(cls(self, x, name))
            elif name not in wanted:
                for thing in have:
                    if getattr(thing, "hider", None) is not None:
                        thing.hider.leave_den()  # out of the presents first
                    thing.gone = True
        balls = [b for b in self.of("ball") if isinstance(b, BeachBall)]
        if "beachball" in wanted and not balls:
            pool = next((p for p in self.of("prop") if p.variant == "pool"), None)
            x = pool.x + 52 * s if pool is not None else self.width * 0.7
            self.add(BeachBall(self, max(40.0, min(self.width - 40.0, x))))
        elif "beachball" not in wanted:
            for ball in balls:
                ball.gone = True
        if self.season != "winter":
            for ball in self.of("ball"):
                if isinstance(ball, Snowball):
                    ball.gone = True
        cans = self.of("can")
        if "watering_can" in wanted and not cans:
            x = self.settings["items"].get("watering_can", {}).get("x")
            if not (isinstance(x, (int, float)) and 0 < x < self.width):
                x = self.width * 0.235
            self.add(WateringCan(self, x))
        elif "watering_can" not in wanted:
            for can in cans:
                can.gone = True
        tree = self.tree()
        nests = self.of("nest")
        if "nest" in wanted and tree is not None and not nests:
            self.add(Nest(self, tree))
        elif "nest" not in wanted or tree is None:
            for nest in nests:
                nest.gone = True
        kites = self.of("kite")
        if "kite" in wanted and not kites:
            self.add(Kite(self))
        elif "kite" not in wanted:
            for kite in kites:
                kite.gone = True
        if self.season == "winter":
            for puddle in self.of("puddle"):
                puddle.gone = True

    def fun(self, dt):
        """Every frame: puddles form in the rain, muddy paws dry off, foxes chase the kite you're flying."""
        rng, s = self.rng, self.scale
        if self.falling == "rain" and self.season != "winter":
            self._puddle_in = getattr(self, "_puddle_in", 8.0) - dt
            puddles = self.of("puddle")
            if self._puddle_in <= 0:
                self._puddle_in = rng.uniform(15, 35)
                x = rng.uniform(60, self.width - 60)
                if len(puddles) < 4 and all(abs(p.x - x) > 70 * s for p in puddles):
                    self.add(Puddle(self, x, small=rng.random() < 0.5))
        for fox in self.of("fox"):
            if getattr(fox, "muddy", 0) > 0:
                fox.muddy = max(0.0, fox.muddy - dt)
        for kite in self.of("kite"):
            if kite.held:
                chaser = kite.chaser
                if chaser is None or chaser.gone or chaser.step is None or chaser.step.follow is not kite:
                    kite.chaser = None
                    if rng.random() < dt * 1.5:
                        self.chase_kite(kite)

    def free_foxes(self):
        """Foxes awake and free to play (not held, asleep, carrying something, up high, or hidden)."""
        return [f for f in self.of("fox") if not f.asleep and not f.held and not f.vy and f.carrying is None
                and f.alpha > 0 and not f.up_high and f.dragging_folder is None]

    def season_options(self, fox):
        """More things a fox might do, with the newer seasonal things about: (weight, make) pairs for its
        choice list (only the ones that apply, so the rest of the list is drawn just as before)."""
        p, season, s = fox.playful, self.season, self.scale
        options = []

        def near(things, reach):
            close = [t for t in things if abs(t.x - fox.x) < reach * s / 2]
            return min(close, key=lambda t: abs(t.x - fox.x)) if close else None

        def yard(name):
            return [t for t in self.of("yard") if t.variant == name]

        def act(action, *args):
            def make():
                action(fox, *args)
                return []  # the plan is already set
            return make
        if season == "winter":
            snowman = near([t for t in yard("snowman") if t.nose_on], 700)
            if snowman is not None:
                options.append((p * 1.0, act(self.steal_nose, snowman)))
            pond = near(yard("pond"), 900)
            if pond is not None:
                options.append((p * 0.9, act(self.skate, pond)))
            bird = near([b for b in self.of("songbird") if b.state in ("perch", "peck", "sing")], 900)
            if bird is not None:
                options.append((p * 2.5, act(self.stalk_birds, bird)))
            gifts = near([g for g in yard("gifts") if g.hider is None], 900)
            if gifts is not None:
                options.append((p * 0.8, act(self.hide_in_gifts, gifts)))
        elif season == "spring":
            puddle = near(self.of("puddle"), 800)
            if puddle is not None:
                options.append((p * 2.0, act(self.splash_puddle, puddle)))
            bunny = near([b for b in self.of("bunny") if b.state == "graze"], 1000)
            if bunny is not None:
                options.append((p * 3.0, act(self.chase_bunnies, bunny)))
        elif season == "summer":
            sprinkler = near([t for t in yard("sprinkler") if t.on], 900)
            if sprinkler is not None:
                options.append((p * 1.5, act(self.run_through_sprinkler, sprinkler)))
            ball = near([b for b in self.of("ball") if isinstance(b, BeachBall) and not b.held and not b.moving], 800)
            if ball is not None:
                options.append((p * 1.5, act(self.boop_beachball, ball)))
            frog = near([f for f in self.of("frog") if f.visiting and f.state == "sit"], 800)
            if frog is not None:
                options.append((p * 2.5, act(self.pounce_frog, frog)))
            puddle = near(self.of("puddle"), 800)
            if puddle is not None:
                options.append((p * 1.5, act(self.splash_puddle, puddle)))
        return options

    def toy_thrown(self, ball):
        """You threw a snowball or the beach ball: the nearest free fox races after it."""
        s = self.scale
        if abs(ball.vx) + abs(ball.vy) < 200 * s:
            return None  # just put down
        free = self.free_foxes()
        if not free:
            return None
        fox = min(free, key=lambda f: abs(f.x - ball.x))
        fox.busy_with = None
        ball.chased_by = fox
        if isinstance(ball, Snowball):  # it bursts as it lands: a pounce and a dig in the snow where it went
            fox.do(Step("tilt", 0.25, face=ball.x), Step("run", follow=ball, speed=ZOOM * 0.75),
                   Step("pounce", 0.5), Step("dig", 1.2), Step("happy", 1.0), Step("playbow", 1.0))
        else:
            fox.do(Step("tilt", 0.25, face=ball.x), Step("run", follow=ball, speed=ZOOM * 0.75),
                   Step("boop", face=ball.x, then=lambda: self.boop_ball(fox, ball)), Step("happy", 1.0),
                   Step("playbow", 1.0))
        return fox

    def boop_ball(self, fox, ball):
        """A nose under the ball: up it goes."""
        s = self.scale
        if not ball.gone and not ball.held and abs(ball.x - fox.x) < 50 * s:
            ball.vy = -self.rng.uniform(380, 480) * s
            ball.vx = fox.facing * self.rng.uniform(60, 140) * s
            ball.y = min(ball.y, ball.floor() - 1)

    def snowball_hit(self, fox):
        """A snowball burst on a fox: it doesn't mind a bit (a sleepy one wakes up cheerful)."""
        if fox.asleep:
            fox.bonk()
        elif not fox.held:
            fox.do(Step("tilt"), Step("scratch"), Step("happy", 1.0), Step("playbow", 1.0))

    def chase_kite(self, kite):
        """You're flying the kite: a fox runs along under it, hoping to catch the tail."""
        free = self.free_foxes()
        if not free:
            return None
        fox = min(free, key=lambda f: abs(f.x - kite.x))
        kite.chaser = fox
        fox.do(Step("tilt", 0.3, face=kite.x), Step("run", follow=kite, speed=TROT * 1.6),
               Step("hop", face=kite.x), Step("happy", 1.0))
        return fox
