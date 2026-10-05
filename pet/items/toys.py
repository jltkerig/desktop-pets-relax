"""The foxes' mischief prizes: dug-up taskbar icons (bouncy balls), stolen Discord messages, and the desktop
folder icons they drag about."""
from pet.things import Thing
from .base import Crumb


class Treasure(Thing):
    """A picture of a taskbar icon that a fox "dug up". Only a picture: nothing on the computer is touched.

    The window fills in world.images[key] with the copied icon. Carried in the fox's mouth, then dropped. It's a
    bouncy ball too: pick it up with the mouse and throw it, and it bounces about (off the ground and the edges
    of the screen) while a fox races after it to fetch it. It fades away after lying still for a while.
    """
    kind = "treasure"
    z = 27
    SIZE = 12  # sprite pixels square (the icon is shrunk to this, so it looks pixelated like everything else)
    is_ball = True
    GRAVITY = 1100   # sprite pixels per second squared
    BOUNCE = 0.72    # how much of its speed it keeps at each bounce
    FADE_AFTER = 60  # seconds lying still before it starts to fade

    def __init__(self, world, fox, key):
        super().__init__(world, fox.x, world.ground, "acorn")  # the sprite is unused; the window draws the icon
        self.key = key
        self.carried_by = fox
        self.held = False       # in your hand (the mouse)
        self.vx = self.vy = 0.0
        self.chased_by = None   # the fox running after it
        self.thrown_from = None  # where you threw it from (a fox brings it back there)
        self.on_ground_for = 0.0
        self.bitten = 0.0  # 0..1: how much of it has been chewed away

    def rect(self):
        s = self.world.scale
        size = max(2.0, self.SIZE * s * (1 - 0.75 * self.bitten))
        return self.x - size / 2, self.y - size, size, size

    @property
    def draggable(self):
        return self.carried_by is None and self.bitten < 0.5  # not out of a fox's mouth, nor half eaten

    @property
    def resting(self):
        return self.carried_by is None and not self.held and self.y >= self.world.ground and self.vy == 0 and \
            abs(self.vx) < 6 * self.world.scale

    def low(self):
        """Near enough the ground for a fox to grab."""
        return self.y > self.world.ground - 34 * self.world.scale

    def pick_up(self):
        self.held = True
        self.vx = self.vy = 0.0
        self.alpha = 1.0

    def drop(self):
        self.throw(0.0, 0.0)

    def throw(self, vx, vy):
        """Let go of it, flying at (vx, vy) screen pixels per second. A fox gives chase."""
        s, w = self.world.scale, self.world
        top = 2600 * s / 2
        self.held = False
        self.vx, self.vy = max(-top, min(top, vx)), max(-top, min(top, vy))
        self.on_ground_for = 0.0
        self.alpha = 1.0
        self.thrown_from = max(60.0, min(w.width - 60.0, self.x))
        w.ball_thrown(self)

    def click(self):
        """A tap sends it bouncing up into the air (and someone will chase it)."""
        if self.carried_by is None and not self.held:
            s = self.world.scale
            self.throw(self.world.rng.uniform(-90, 90) * s, -self.world.rng.uniform(320, 420) * s)

    def update(self, dt):
        w, s = self.world, self.world.scale
        fox = self.carried_by
        if fox is not None and not fox.gone:
            self.facing = fox.facing
            self.x = fox.x + fox.facing * 25 * s
            self.y = fox.y - 13 * s  # in its mouth
            self.vx = self.vy = 0.0
            return
        self.carried_by = None
        if self.held:
            return
        half = self.rect()[2] / 2
        self.vy += self.GRAVITY * s * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y >= w.ground:  # a bounce, smaller each time, until it just rolls
            self.y = w.ground
            if self.vy > 90 * s:
                self.vy = -self.vy * self.BOUNCE
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
        if self.y - 2 * half < 0 and self.vy < 0:
            self.y, self.vy = 2 * half, -self.vy * self.BOUNCE
        if not self.resting:
            self.on_ground_for = 0.0
            return
        self.on_ground_for += dt
        chewer = next((f for f in w.of("fox") if f.step is not None and f.step.anim == "chew"
                       and abs(f.x - self.x) < 40 * w.scale), None)
        if chewer is not None:  # being chewed: smaller bite by bite, crumbs flying off
            self.bitten = min(1.0, self.bitten + dt / 4.0)
            if w.rng.random() < dt * 6:
                w.add(Crumb(w, self.x, self.y - 4 * w.scale))
            if self.bitten >= 1.0:
                for _ in range(6):
                    w.add(Crumb(w, self.x, self.y - 3 * w.scale))
                self.gone = True
                return
        if self.on_ground_for > self.FADE_AFTER:
            self.alpha -= dt / 4
            if self.alpha <= 0:
                self.gone = True


class Folder(Thing):
    """A real folder icon on your desktop that a fox has got hold of. Nothing is drawn: the window moves the
    real icon to follow this (pet/desktop_icons.py). It tumbles down when the fox yanks it off its spot, is
    dragged along the ground in the fox's mouth, and stays where it's dropped.

    x is the middle of the icon's box (label and all), y its bottom; w and h its size, all in strip pixels."""
    kind = "folder"
    z = 1

    def __init__(self, world, name, x, y, w, h, bounds=None):
        super().__init__(world, x, y, "acorn")  # the sprite is unused
        self.name, self.w, self.h = name, float(w), float(h)
        self.bounds = bounds or (0.0, float(world.width))  # the monitor it's on, along the strip: it stays there
        self.home = None      # where Windows had it (its list-view position), so it can be put back
        self.state = "up"     # up (still in its place), falling, down (on the ground), dragged, dropped
        self.fox = None
        self.vy = 0.0
        self.alpha = 0.0      # never drawn
        self.moved = False    # has it left its place yet?

    def rect(self):
        return self.x - self.w / 2, self.y - self.h, self.w, self.h

    def contains(self, px, py):
        return False  # clicks go through to the real icon

    def floor(self):
        return self.world.ground - 2 * self.world.scale

    def update(self, dt):
        w, s = self.world, self.world.scale
        before = (self.x, self.y)
        if self.state == "falling":
            self.vy += 1400 * s * dt
            self.y += self.vy * dt
            if self.y >= self.floor():
                self.y = self.floor()
                if self.vy > 260 * s:
                    self.vy = -self.vy * 0.3  # a little bounce
                else:
                    self.vy, self.state = 0.0, "down"
        elif self.state == "dragged":
            fox = self.fox
            if fox is None or fox.gone or fox.held or getattr(fox, "dragging_folder", None) is not self:
                self.let_go()  # picked up, or got distracted: it lets go
            else:
                reach = 18 * s + self.w / 2
                left, right = self.bounds
                self.x = max(left + self.w / 2, min(right - self.w / 2, fox.x + fox.facing * reach))
                self.y = self.floor()
        if (self.x, self.y) != before:
            self.moved = True
            w.folder_requests.append(("move", self.name, self.x, self.y, self.w, self.h))

    def let_go(self):
        if self.fox is not None and getattr(self.fox, "dragging_folder", None) is self:
            self.fox.dragging_folder = None
        self.fox = None
        self.state = "dropped"
        self.gone = True
        if self.moved:
            self.world.folder_requests.append(("drop", self.name, self.x, self.y, self.w, self.h))


class Message(Thing):
    """A Discord message a fox has "stolen": only a picture of it, copied off the screen, while the spot it
    came from is covered over. It drops down to the fox, gets carried off and played with, and then flies
    back into place. If anything goes wrong (the window moves, say) it simply vanishes and the cover goes."""
    kind = "message"
    z = 27

    def __init__(self, world, key, home):
        super().__init__(world, home[0], home[1], "acorn")  # the sprite is unused; the window draws the picture
        self.key = key
        self.home = home           # where it belongs, along the strip (its bottom centre)
        self.size = (60.0, 14.0)   # replaced by the picture's real size once it's copied
        self.state = "home"        # home, falling, carried, ground, returning
        self.carried_by = None
        self.ground_time = 0.0
        self.away = 0.0            # seconds since it was taken
        self.limit = 60.0          # it always goes home by itself after this long (shorter for a quick theft)
        self.alpha = 0.0           # invisible until it's actually pulled out

    def rect(self):
        w, h = self.size
        return self.x - w / 2, self.y - h, w, h

    def _fly(self, x, y, dt, speed=520):
        dx, dy = x - self.x, y - self.y
        dist = (dx * dx + dy * dy) ** 0.5
        step = speed * self.world.scale / 2 * dt
        if dist <= step:
            self.x, self.y = x, y
            return True
        self.x += dx / dist * step
        self.y += dy / dist * step
        return False

    def mouth(self, fox):
        s = self.world.scale
        return fox.x + fox.facing * 26 * s, fox.y - 10 * s

    def update(self, dt):
        w = self.world
        self.away += dt
        if self.state == "home" and self.away > 20:
            w.message_home(self)  # the fox never came for it (it got distracted): nothing was taken after all
            return
        if self.away > self.limit and self.state != "returning":
            # whatever the fox got distracted by, the message goes back in the end
            if self.carried_by is not None and self.carried_by.carrying is self:
                self.carried_by.carrying = None
            self.state, self.carried_by = "returning", None
            self.alpha = 1.0
        if self.state == "falling":
            self.alpha = 1.0
            fox = self.carried_by
            if fox is None or fox.gone:
                self.state = "ground"
            elif self._fly(*self.mouth(fox), dt, speed=700):
                self.state = "carried"
        elif self.state == "carried":
            fox = self.carried_by
            if fox is None or fox.gone or fox.held:
                self.state, self.carried_by = "ground", None
            else:
                self.x, self.y = self.mouth(fox)
                self.facing = fox.facing
        elif self.state == "ground":
            self.carried_by = None
            self.y = min(w.ground, self.y + 300 * w.scale * dt)
            self.ground_time += dt
            if self.ground_time > 25:  # left lying about: it makes its own way home
                self.state = "returning"
        elif self.state == "returning":
            self.carried_by = None
            if self._fly(*self.home, dt, speed=380):
                w.message_home(self)
