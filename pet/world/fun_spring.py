"""Spring games (and summer, after rain): splashing in puddles (and walking muddy paw prints about), and chasing
the baby bunnies, who are always far too quick."""
from pet.fox import Step, TROT, ZOOM


class SpringFun:
    """Part of World (see pet/world/__init__.py)."""

    MUDDY_FOR = 25  # seconds of muddy paw prints after a splash

    def splash_puddle(self, fox, puddle):
        """A hop into the puddle (splash!), a happy stomp about in it, a hop out, and muddy paws for a while."""
        s = self.scale
        side = -1 if fox.x < puddle.x else 1
        start = self.clamp_x(puddle.x + side * 34 * s)
        out = self.clamp_x(puddle.x - side * 40 * s)

        def splash(drops, muddy=False):
            def go():
                if not puddle.gone and abs(fox.x - puddle.x) < puddle.half_width + 12 * s:
                    puddle.splash(drops)
                    if muddy:
                        fox.muddy = self.MUDDY_FOR
            return go

        fox.do(Step("trot", to_x=start, speed=TROT), Step("crouch", 0.4, face=puddle.x),
               Step("hop", to_x=puddle.x, leap=12, then=splash(10, muddy=True)),
               Step("happy", 1.0, then=splash(6)), Step("bat", then=splash(6)),
               Step("hop", to_x=out, leap=10, then=splash(4)), Step("scratch"), Step("happy", 0.8))

    def chase_bunnies(self, fox, bunny):
        """A crouch, a wiggle, and a dash at the bunnies. They're off like a shot, and the fox is delighted."""
        fox.do(Step("crouch", 0.8, face=bunny.x), Step("run", follow=bunny, speed=ZOOM * 0.8),
               Step("tilt", face=bunny.x), Step("playbow", 1.0), Step("happy", 1.0))
