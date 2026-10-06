"""Summer games: dashing through the sprinkler (and shaking off), nosing the beach ball about, a nap in the
hammock, popping fireflies into the jar, and pouncing at the frog."""
from pet.fox import Step, TROT, WALK, ZOOM
from pet.items import Droplet


class SummerFun:
    """Part of World (see pet/world/__init__.py)."""

    def run_through_sprinkler(self, fox, sprinkler):
        """A dash through the spray, a hop over the sprinkler, out the other side, and a good shake."""
        s = self.scale
        side = -1 if fox.x < sprinkler.x else 1
        start = max(40.0, min(self.width - 40.0, sprinkler.x + side * 64 * s))
        end = max(40.0, min(self.width - 40.0, sprinkler.x - side * 64 * s))
        fox.do(Step("trot", to_x=start, speed=TROT), Step("crouch", 0.4, face=sprinkler.x),
               Step("run", to_x=sprinkler.x + side * 14 * s, speed=TROT * 1.6),
               Step("hop", to_x=sprinkler.x - side * 14 * s, leap=14), Step("run", to_x=end, speed=TROT * 1.6),
               Step("scratch", then=lambda: self.shake_off(fox)), Step("happy", 1.0))

    def shake_off(self, fox):
        """A wet fox shakes itself: water flies off all round."""
        s = self.scale
        for _ in range(10):
            self.add(Droplet(self, fox.x + self.rng.uniform(-14, 14) * s, fox.y - self.rng.uniform(6, 20) * s))

    def boop_beachball(self, fox, ball):
        """Up to the beach ball, a nose under it to send it flying, a chase, and another boop."""
        s = self.scale
        side = -1 if fox.x < ball.x else 1
        fox.do(Step("trot", to_x=max(40.0, min(self.width - 40.0, ball.x + side * 22 * s)), speed=TROT),
               Step("boop", face=ball.x, then=lambda: self.boop_ball(fox, ball)),
               Step("run", follow=ball, speed=ZOOM * 0.6),
               Step("boop", face=ball.x, then=lambda: self.boop_ball(fox, ball)), Step("happy", 1.0),
               Step("playbow", 1.0))

    def hammock_for(self, fox):
        """A free hammock for a sleepy fox's nap (on a summer day, now and then), or None."""
        hammocks = [t for t in self.of("yard") if t.variant == "hammock" and t.occupant() is None]
        if not hammocks or self.season != "summer" or self.daylight() == "night":
            return None
        hammock = min(hammocks, key=lambda h: abs(h.x - fox.x))
        if abs(hammock.x - fox.x) > 1400 * self.scale / 2 or self.rng.random() > 0.6:
            return None
        return hammock

    def nap_in_hammock(self, fox, hammock):
        """Over to the hammock, a hop up into it, a yawn, and a long nap, swaying. (Afterwards, being up off the
        ground, it hops down: see Fox.choose.)"""
        s = self.scale
        side = -1 if fox.x < hammock.x else 1
        bx, by = hammock.bed()
        fox.do(Step("walk", to_x=max(40.0, min(self.width - 40.0, hammock.x + side * 34 * s)), speed=WALK),
               Step("crouch", 0.4, face=hammock.x), Step("hop", to_x=bx, to_y=by, leap=12), Step("yawn"),
               Step("sleep", self.rng.uniform(150, 360)))

    def jar_for(self, firefly):
        """The firefly jar near a caught firefly, if it has room."""
        jars = [t for t in self.of("yard") if t.variant == "firefly_jar" and not t.full
                and abs(t.x - firefly.x) < 500 * self.scale]
        return jars[0] if jars else None

    def into_the_jar(self, fox, firefly, jar):
        """Caught it! Carried carefully over to the jar and popped in."""
        s = self.scale
        firefly.gone = True
        firefly.glow.gone = True
        side = -1 if fox.x < jar.x else 1
        fox.do(Step("trot", to_x=max(40.0, min(self.width - 40.0, jar.x + side * 22 * s)), speed=TROT),
               Step("boop", face=jar.x, then=jar.add_firefly), Step("happy", 1.2), Step("watch", 2.0, face=jar.x))

    def pounce_frog(self, fox, frog):
        """A crouch, a wiggle and a pounce: the frog leaps away just in time."""
        x = max(40.0, min(self.width - 40.0, frog.x))
        fox.do(Step("crouch", 0.8, face=frog.x), Step("pounce", to_x=x, leap=24, then=frog.startle), Step("land"),
               Step("happy", 1.0), Step("tilt", face=frog.x))
