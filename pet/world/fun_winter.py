"""Winter games: pinching the snowman's carrot nose, skidding across the frozen pond, stalking the birds at the
feeder, and hiding in the presents."""
from pet.fox import Step, TROT, WALK, _spin_steps


class WinterFun:
    """Part of World (see pet/world/__init__.py)."""

    def steal_nose(self, fox, snowman):
        """Up on its hind legs to pinch the carrot, off with it (very pleased), and down it goes somewhere else."""
        s, rng = self.scale, self.rng
        stand = max(40.0, min(self.width - 40.0, snowman.x + 30 * s))
        away = max(60.0, min(self.width - 60.0, stand + rng.choice((-1, 1)) * rng.uniform(120, 260) * s))

        def grab():
            if not fox.held and fox.carrying is None and abs(fox.x - stand) < 30 * s:
                snowman.take_nose(fox)

        def drop():
            carrot = fox.carrying
            if carrot is not None and getattr(carrot, "snowman", None) is snowman:
                carrot.carried_by, fox.carrying = None, None
                carrot.on_ground, carrot.vy = False, 0.0

        fox.do(Step("trot", to_x=stand, speed=TROT), Step("sniff", face=snowman.x),
               Step("hop", face=snowman.x, then=grab), Step("happy", 0.6),
               Step("trot", to_x=away, speed=TROT * 1.3), Step("playbow", 1.0), Step("idle", 0.4, then=drop),
               Step("bat"), Step("happy", 1.0))

    def skate(self, fox, pond):
        """A run-up, a hop onto the ice, and a long skid across it (WHEE!), a spin at the end, a happy roll."""
        from pet.visitors import Bubble
        s = self.scale
        side = -1 if fox.x < pond.x else 1
        start = max(40.0, min(self.width - 40.0, pond.x + side * 56 * s))
        mid, end = pond.x, max(40.0, min(self.width - 40.0, pond.x - side * 40 * s))

        def whee():
            bubble = self.add(Bubble(self, fox, "whee_bubble", rise=36))
            bubble.life = 1.4

        fox.do(Step("trot", to_x=start, speed=TROT), Step("crouch", 0.4, face=pond.x),
               Step("hop", to_x=pond.x + side * 40 * s, leap=8, then=whee),
               Step("crouch", to_x=mid, speed=TROT * 1.7), Step("crouch", to_x=end, speed=TROT * 1.1),
               *_spin_steps(end, s, 2), Step("roll", 1.2), Step("happy", 1.0))

    def stalk_birds(self, fox, bird):
        """Low and slow toward the birds at the feeder, a wiggle, a leap... and they all flutter off."""
        s = self.scale
        side = -1 if fox.x < bird.x else 1
        close = max(40.0, min(self.width - 40.0, bird.x + side * 60 * s))
        sneak = max(40.0, min(self.width - 40.0, bird.x + side * 150 * s))
        if abs(fox.x - bird.x) < abs(sneak - bird.x):
            sneak = fox.x

        def scatter():
            for b in self.of("songbird"):  # (any still flying in to perch there too)
                if min(abs(b.x - bird.x), abs(b.perch.pos(self)[0] - bird.x)) < 120 * s:
                    b.fly_off()

        fox.do(Step("trot", to_x=sneak, speed=TROT), Step("crouch", to_x=close, speed=WALK * 0.7),
               Step("crouch", 0.8, face=bird.x),
               Step("pounce", to_x=max(40.0, min(self.width - 40.0, bird.x)), leap=26, then=scatter),
               Step("land"), Step("happy", 1.0), Step("watch", 2.0, face=bird.x))

    def hide_in_gifts(self, fox, gifts):
        """A dive into the big present: hidden (tail sticking out, the lid bobbing), then out it pops."""
        s, rng = self.scale, self.rng
        side = -1 if fox.x < gifts.x else 1
        box = gifts.x - 10 * s  # the big box is on the left
        out = max(60.0, min(self.width - 60.0, gifts.x + side * rng.uniform(50, 80) * s))

        def hide():
            if gifts.gone or gifts.hider is not None or fox.held:
                return
            gifts.hider, fox.hiding_in = fox, gifts
            fox.alpha = 0.0

        fox.do(Step("trot", to_x=max(40.0, min(self.width - 40.0, gifts.x + side * 34 * s)), speed=TROT),
               Step("crouch", 0.5, face=box), Step("pounce", to_x=box, leap=20, then=hide),
               Step("idle", rng.uniform(5, 12), then=fox.leave_den), Step("hop", to_x=out, leap=16),
               Step("happy", 1.0), Step("playbow", 1.0))
