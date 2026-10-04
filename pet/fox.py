"""A fox: its moods and what it decides to do next. Only ever happy: no grumpy reactions.

The fox works through a short plan of steps (play an animation, walk somewhere, leap...). When the plan
runs out it picks the next thing to do from its moods and what's around it.
"""
import datetime
import math
from collections import deque

from pet import sprites
from pet.things import Thing

WALK, TROT, ZOOM = 34, 80, 230  # speed in sprite pixels per second (scaled by the world's scale)


class Step:
    def __init__(self, anim, seconds=None, to_x=None, speed=0.0, leap=0.0, then=None, face=None):
        self.anim = anim          # animation name without the fox_<palette>_ prefix
        self.seconds = seconds    # None: one pass of the animation (or until arriving, when moving)
        self.to_x = to_x          # walk/trot/leap to this x
        self.speed = speed
        self.leap = leap          # arc height (sprite pixels) for a leap
        self.then = then          # a function run when the step finishes
        self.face = face          # an x to turn toward when the step starts
        self.elapsed = 0.0
        self.start_x = None


class Fox(Thing):
    kind = "fox"
    draggable = True
    z = 20

    def __init__(self, world, x, palette="orange", name=None):
        super().__init__(world, x, world.ground, f"fox_{palette}_idle")
        self.palette = palette
        self.name = name or palette
        self.energy = 0.8     # sleepy below about 0.3
        self.boredom = 0.2    # rises while nothing happens, falls with play
        self.playful = 0.6
        self.plan = deque()
        self.step = None
        self.held = False
        self.vy = 0.0         # falling after being dropped
        self.asleep = False
        self.just_woke = False
        self.watched = set()  # visitors it has already sat and watched
        self.busy_with = None  # another fox it is playing with
        self.carrying = None   # a dug-up treasure in its mouth
        self.rng = world.rng

    # -- what other things call ------------------------------------------------------------------------

    def anim_name(self, short):
        return f"fox_{self.palette}_{short}"

    def do(self, *steps, interrupt=True):
        """Replace (or extend) the plan."""
        if interrupt:
            self.plan.clear()
            self.step = None
            self.asleep = False
        self.plan.extend(steps)

    def bonk(self):
        """An acorn landed on its head."""
        if self.asleep:
            self.do(Step("wake"), Step("happy", 1.6), Step("tilt"))
            self.just_woke = True
            self.energy = max(self.energy, 0.45)
        elif not self.held:
            self.do(Step("tilt"), Step("happy", 1.0))

    def hear_honk(self, goose_x):
        """A goose honked nearby: a head tilt and a happy hop. A sleeping fox wakes up cheerful."""
        if self.held or self.vy:
            return
        if self.asleep:
            self.do(Step("wake"), Step("tilt", face=goose_x), Step("happy", 1.0, face=goose_x))
            self.just_woke = True
        elif self.step is None or self.step.anim not in ("tilt", "hop", "pounce", "trot"):
            self.do(Step("tilt", face=goose_x), Step("hop", face=goose_x), Step("watch", 2.0, face=goose_x))

    def pet(self):
        """The cursor is stroking it: happy wiggles. A sleeping fox keeps sleeping (still content)."""
        if self.held or self.asleep or self.vy:
            return
        if self.step and self.step.anim == "petted":
            self.step.seconds = max(self.step.seconds, self.step.elapsed + 1.2)
            return
        self.do(Step("petted", 1.6), Step("happy", 0.8))
        self.boredom = max(0.0, self.boredom - 0.05)

    def poke(self):
        """A click: a happy hop (or a sleepy stretch if it was napping)."""
        if self.held:
            return
        if self.asleep:
            self.do(Step("wake"), Step("stretch"), Step("happy", 1.0))
        else:
            self.do(Step("hop"), Step("happy", 1.0))

    def pick_up(self):
        if self.carrying is not None:  # it lets go of its treasure
            self.carrying.carried_by = None
            self.carrying = None
        self.held = True
        self.do(Step("held", 10 ** 9))

    def drop(self):
        self.held = False
        self.vy = 0.1
        self.do(Step("held", 10 ** 9))

    # -- every frame -------------------------------------------------------------------------------------

    def update(self, dt):
        self._moods(dt)
        if self.held:
            self.anim.play(self.anim_name("held"))
            self.anim.update(dt)
            return
        if self.vy:  # falling after a drop
            self.vy += 900 * self.world.scale * dt
            self.y += self.vy * dt
            if self.y >= self.world.ground:
                self.y, self.vy = self.world.ground, 0.0
                self.do(Step("land"), Step("happy", 0.8))
            self.anim.play(self.anim_name("held"))
            self.anim.update(dt)
            return
        self._notice_leaves(dt)
        if self.step is None:
            if not self.plan:
                self.choose()
            self.step = self.plan.popleft()
            self._start(self.step)
        self._run(self.step, dt)

    CALM = ("idle", "look", "walk", "sniff", "watch", "tilt", "scratch", "groom", "happy", "dig")

    def _notice_leaves(self, dt):
        """A leaf drifting down nearby catches its eye: off it goes after it."""
        if self.asleep or self.carrying is not None or self.busy_with is not None:
            return
        if self.step is not None and self.step.anim not in self.CALM:
            return
        if self.rng.random() < dt * (0.3 + self.playful * 0.9):
            leaf = self.world.leaf_near(self, 700)
            if leaf is not None:
                self.world.chase_leaf(self, leaf)

    def _moods(self, dt):
        hour = self.world.now().hour
        night = hour >= 22 or hour < 7
        if self.asleep:
            self.energy = min(1.0, self.energy + dt * (0.006 if night else 0.012))
            self.boredom = max(0.0, self.boredom - dt * 0.004)
        else:
            self.energy = max(0.0, self.energy - dt * (0.0035 if night else 0.0012))
            playing = self.step is not None and self.step.anim in ("pounce", "bat", "playbow", "roll", "hop", "trot", "boop",
                                                                    "run")
            self.boredom = max(0.0, min(1.0, self.boredom + dt * (-0.02 if playing else 0.0025)))
        self.playful = max(0.0, min(1.0, 0.25 + self.energy * 0.6 - (0.3 if night else 0.0) + self.boredom * 0.3))

    def _start(self, step):
        self.anim.play(self.anim_name(step.anim))
        self.anim.time = 0.0
        self.anim.done = False
        step.start_x = self.x
        if step.face is not None and abs(step.face - self.x) > 2:
            self.facing = 1 if step.face > self.x else -1
        if step.to_x is not None and abs(step.to_x - self.x) > 1:
            self.facing = 1 if step.to_x > self.x else -1
        self.asleep = step.anim == "sleep"

    def _run(self, step, dt):
        step.elapsed += dt
        self.anim.update(dt)
        finished = False
        if step.leap and step.to_x is not None:
            total = sprites.duration(self.anim.name)
            t = min(1.0, step.elapsed / total)
            self.x = step.start_x + (step.to_x - step.start_x) * t
            self.y = self.world.ground - math.sin(math.pi * t) * step.leap * self.world.scale
            finished = t >= 1.0
            if finished:
                self.y = self.world.ground
        elif step.to_x is not None:
            distance = step.to_x - self.x
            move = step.speed * self.world.scale * dt
            if abs(distance) <= move:
                self.x = step.to_x
                finished = True
            else:
                self.x += move if distance > 0 else -move
        elif step.seconds is not None:
            finished = step.elapsed >= step.seconds
        else:
            finished = self.anim.done
        self.x = max(20.0, min(self.world.width - 20.0, self.x))
        if finished:
            if step.anim == "sleep":
                self.asleep = False
                self.just_woke = True
            if step.then:
                step.then()
            self.step = None

    def _zoomies(self):
        """A burst of energy: a wiggle, a sprint to the far end of the screen, a dash partway back, a happy roll."""
        w = self.world
        far = w.width - 60.0 if self.x < w.width / 2 else 60.0
        back = far + (-1 if far > self.x else 1) * self.rng.uniform(0.25, 0.5) * w.width
        return [Step("crouch", 0.5), Step("hop"), Step("run", to_x=far, speed=ZOOM),
                Step("bat", face=back), Step("run", to_x=back, speed=ZOOM * 0.9),
                Step("roll", self.rng.uniform(1.2, 2.2)), Step("happy", 1.0)]

    def _tail_chase(self):
        return _spin_steps(self.x, self.world.scale, self.rng.randint(3, 5)) + [Step("happy", 1.0)]

    # -- deciding what to do next ------------------------------------------------------------------------

    def choose(self):
        w, rng = self.world, self.rng
        if self.busy_with and (self.busy_with.gone or self.busy_with.asleep):
            self.busy_with = None
        night = w.now().hour >= 22 or w.now().hour < 7
        if self.just_woke:
            self.just_woke = False
            self.plan.extend([Step("stretch"), Step("yawn") if rng.random() < 0.5 else Step("idle", 2.0)])
            return
        if self.energy < 0.28 or (night and self.energy < 0.55):
            spot = w.nap_spot(self)
            if spot is not None and abs(spot - self.x) > 30:
                self.plan.append(Step("walk", to_x=spot, speed=WALK))
            self.plan.extend([Step("yawn"), Step("sleep", rng.uniform(60, 150) * (2 if night else 1))])
            return

        # something worth watching?
        visitor = w.visitor_to_watch(self)
        if visitor is not None:
            self.watched.add(visitor)
            self.plan.extend([Step("watch", rng.uniform(4, 7), face=visitor.x), Step("tilt", face=visitor.x)])
            return

        # bored? dig at a taskbar icon for treasure
        if w.taskbar_spots and self.boredom > 0.3 and rng.random() < 0.15 and w.dig_for_treasure(self):
            return  # dig_for_treasure filled in the plan

        # a ripe pumpkin to inspect
        pumpkin = w.pumpkin_near(self, 700)
        if pumpkin is not None and rng.random() < 0.25:
            side = -1 if pumpkin.x > self.x else 1
            self.plan.extend([Step("walk", to_x=pumpkin.x + side * 30 * w.scale, speed=WALK),
                              Step("sniff", face=pumpkin.x), Step("boop", face=pumpkin.x),
                              Step("tilt", face=pumpkin.x), Step("happy", 1.0)])
            return

        # play: acorns, falling leaves, the cursor, the other fox
        if rng.random() < self.playful:
            acorn = w.acorn_near(self, 500)
            if acorn is not None and rng.random() < 0.6:
                side = -1 if acorn.x > self.x else 1
                stand = acorn.x + side * 26 * w.scale
                self.plan.extend([Step("trot", to_x=stand, speed=TROT), Step("sniff", face=acorn.x),
                                  Step("bat", face=acorn.x, then=lambda: w.kick(acorn, self)), Step("happy", 1.0)])
                return
            leaf = w.leaf_near(self, 700)
            if leaf is not None:
                w.chase_leaf(self, leaf)
                return
            cursor = w.cursor_to_pounce(self)
            if cursor is not None and rng.random() < 0.5:
                self.plan.extend([Step("crouch", rng.uniform(1.0, 2.0), face=cursor),
                                  Step("pounce", to_x=cursor, leap=26), Step("hop"), Step("happy", 1.0)])
                return
            friend = w.friend_to_play(self)
            if friend is not None and rng.random() < 0.55:
                w.play_together(self, friend)
                return

        options = [
            (4.0, lambda: [Step("idle", rng.uniform(3, 8))]),
            (2.0, lambda: [Step("look")]),
            (3.0 + self.boredom * 3, lambda: [Step("walk", to_x=w.wander_target(self), speed=WALK)]),
            (1.5 + self.boredom * 2, lambda: [Step("sniff"), Step("sniff")]),
            (1.0, lambda: [Step("scratch")]),
            (1.0, lambda: [Step("tilt")]),
            (1.0 + self.boredom * 2.5, lambda: [Step("dig", rng.uniform(1.5, 3.0)), Step("sniff")]),
            (0.6 + (1 - self.energy) * 2, lambda: [Step("yawn")]),
            (self.playful * 1.5, lambda: [Step("roll", rng.uniform(1.5, 3.0)), Step("happy", 0.8)]),
            (self.playful * 1.0, lambda: [Step("hop"), Step("happy", 0.6)]),
            (self.playful * 1.2, lambda: [Step("trot", to_x=w.wander_target(self), speed=TROT)]),
            (0.5, lambda: [Step("stretch")]),
            (self.playful * self.energy * 1.4, lambda: self._zoomies()),
            (1.0, lambda: [Step("groom", rng.uniform(2.0, 4.0)), Step("idle", 1.5)]),
            (self.playful * 0.6, lambda: self._tail_chase()),
        ]
        total = sum(weight for weight, _ in options)
        pick = rng.uniform(0, total)
        for weight, make in options:
            pick -= weight
            if pick <= 0:
                self.plan.extend(make())
                return
        self.plan.append(Step("idle", 3.0))


def _spin_steps(x, scale, turns):
    """Short dashes back and forth: from the side, chasing its own tail looks like this."""
    steps = []
    for i in range(turns * 2):
        steps.append(Step("trot", to_x=x + (9 if i % 2 == 0 else -9) * scale, speed=TROT * 1.4))
    return steps


def now():
    return datetime.datetime.now()
