"""The base for everything on the desktop: a position, a facing, and the sprite it shows."""
from pet import sprites


class Thing:
    kind = "thing"
    draggable = False
    z = 0  # drawing order: higher is in front

    def __init__(self, world, x, y, sprite):
        self.world = world
        self.x, self.y = float(x), float(y)  # where the sprite's anchor sits on screen
        self.facing = 1  # 1 = right, -1 = left (sprites face right)
        self.anim = sprites.Anim(sprite)
        self.alpha = 1.0
        self.gone = False  # set to remove it from the world

    def update(self, dt):
        self.anim.update(dt)

    def rect(self):
        """(left, top, width, height) on screen."""
        m = sprites.meta(self.anim.name)
        s = self.world.scale
        ax, ay = m["anchor"]
        w, h = m["frame_width"] * s, m["frame_height"] * s
        left = self.x - ax * s if self.facing > 0 else self.x - (m["frame_width"] - ax) * s
        return left, self.y - ay * s, w, h

    def contains(self, px, py):
        if self.alpha <= 0:
            return False  # hidden (a fox inside the den)
        left, top, w, h = self.rect()
        return left <= px < left + w and top <= py < top + h
