"""Shared by the newer seasonal things: YardThing (something that stands in the yard, which you can drag about
and click), and Ball (a toy you pick up with the mouse and throw, that bounces about while a fox chases it).
The seasonal things themselves are in winter.py, spring.py and summer.py."""
from pet import sprites
from pet.things import Thing


class YardThing(Thing):
    """Something standing in the yard (the snowman, the bird feeder, the sprinkler...). You can drag it about
    (its spot is remembered, like the other items), and a click plays its "<look>_wobble" sprite if it has one.
    Its look can change with the weather: SNOWY things wear "<variant>_snow" on snowy winter days."""
    kind = "yard"
    draggable = True
    z = 7
    SNOWY = False

    def __init__(self, world, x, variant):
        super().__init__(world, x, world.ground, variant)
        self.variant = variant
        self.reacting = False  # playing its reaction to a click
        self.anim.name = self.look

    @property
    def look(self):
        """The sprite it shows when nothing's happening."""
        return self.variant + ("_snow" if self.SNOWY and self.world.snowed_over else "")

    def react(self, name="wobble"):
        sprite = f"{self.look}_{name}"
        if sprites.exists(sprite):
            self.anim.play(sprite)
            self.reacting = True

    def click(self):
        self.react()

    def update(self, dt):
        super().update(dt)
        if self.anim.name != self.look and (self.anim.done or not self.reacting):
            self.anim.play(self.look)  # back to normal (or the weather changed its look)
            self.reacting = False


class Ball(Thing):
    """A toy to throw: pick it up with the mouse and fling it. It flies, bounces off the ground and the edges of
    the screen, and rolls to a stop, and a fox races after it (see World.toy_thrown). Subclasses change how
    heavy and bouncy it is, and what happens when it lands (a snowball bursts)."""
    kind = "ball"
    z = 27
    draggable = True
    carryable = True  # the Stage picks it up when dragged, and throws it when let go
    is_ball = True    # a fox following it stops once it's low enough to grab
    GRAVITY = 1100    # sprite pixels per second squared
    BOUNCE = 0.7      # how much of its speed it keeps at each bounce
    TOP_SPEED = 2400  # (screen pixels per second at scale 2)

    def __init__(self, world, x, y, sprite):
        super().__init__(world, x, y, sprite)
        self.held = False
        self.vx = self.vy = 0.0
        self.chased_by = None

    def low(self):
        """Near enough the ground for a fox to grab."""
        return self.y > self.world.ground - 34 * self.world.scale

    @property
    def moving(self):
        return self.held or self.y < self.floor() - 1 or abs(self.vx) > 4 * self.world.scale or self.vy != 0

    def pick_up(self):
        self.held = True
        self.vx = self.vy = 0.0

    def drop(self):
        self.throw(0.0, 0.0)

    def throw(self, vx, vy):
        """Let go of it, flying at (vx, vy) screen pixels per second."""
        top = self.TOP_SPEED * self.world.scale / 2
        self.held = False
        self.vx, self.vy = max(-top, min(top, vx)), max(-top, min(top, vy))
        self.world.toy_thrown(self)

    def landed(self, speed):
        """It hit the ground at this speed (screen pixels per second). False: it's gone (burst)."""
        return True

    def floor(self):
        """Where it comes to rest (the ground; the beach ball floats in the kiddie pool)."""
        return self.world.ground

    def update(self, dt):
        if self.held:
            return
        w, s = self.world, self.world.scale
        half = self.rect()[2] / 2
        floor = self.floor()
        if self.y < floor or self.vy != 0:
            self.vy += self.GRAVITY * s * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y >= floor and self.vy >= 0:  # a bounce, smaller each time, until it just rolls
            speed = self.vy
            self.y = floor
            if not self.landed(speed):
                self.gone = True
                return
            if speed > 90 * s:
                self.vy = -speed * self.BOUNCE
                self.vx *= 0.88
            else:
                self.vy = 0.0
                self.vx *= max(0.0, 1 - 2.2 * dt)
                if abs(self.vx) < 4 * s:
                    self.vx = 0.0
        if self.x < half:  # off the edges of the screen
            self.x, self.vx = half, abs(self.vx) * self.BOUNCE
        elif self.x > w.width - half:
            self.x, self.vx = w.width - half, -abs(self.vx) * self.BOUNCE
        top = self.rect()[3]
        if self.y - top < 0 and self.vy < 0:
            self.y, self.vy = top, -self.vy * self.BOUNCE
        super().update(dt)
