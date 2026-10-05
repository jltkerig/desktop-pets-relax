"""Two foxes together: greeting, grooming, tagging along, snuggling, playing chase."""
from pet.fox import Step, TROT, WALK


class Friends:
    """Part of World (see pet/world/__init__.py)."""

    def friend_to_play(self, fox):
        for other in self.of("fox"):
            if other is not fox and not other.asleep and not other.held and other.busy_with is None and \
                    abs(other.x - fox.x) < 420 * self.scale / 2 and other.playful > 0.35:
                return other
        return None


    SHOWING_OFF = ("run", "pounce", "dive", "roll", "playbow", "dig", "hop", "bat")

    def friends(self, fox):
        """The other foxes out (any number), nearest first."""
        return sorted((f for f in self.of("fox") if f is not fox), key=lambda f: abs(f.x - fox.x))

    def free_friend(self, fox, reach=1400):
        """An awake friend that isn't busy with something else, within reach (sprite pixels)."""
        for other in self.friends(fox):
            if not other.asleep and not other.held and not other.vy and not other.up_high and \
                    other.busy_with is None and other.carrying is None and abs(other.x - fox.x) < reach * self.scale / 2:
                return other
        return None

    def friend_showing_off(self, fox):
        """A friend nearby doing something worth watching (zoomies, a pounce, a roll...)."""
        for other in self.friends(fox):
            if other.step is not None and other.step.anim in self.SHOWING_OFF and \
                    abs(other.x - fox.x) < 1200 * self.scale / 2:
                return other
        return None

    def sleeping_friend(self, fox):
        """A friend asleep out in the open (not in the den), to curl up beside."""
        for other in self.friends(fox):
            if other.asleep and not other.in_den:
                return other
        return None

    def _together(self, a, b):
        a.busy_with, b.busy_with = b, a

        def apart():
            if a.busy_with is b:
                a.busy_with = None
            if b.busy_with is a:
                b.busy_with = None
        return apart

    def _beside(self, fox, friend):
        """Where fox should stand to be next to friend, facing it, on the side it's coming from."""
        side = -1 if fox.x < friend.x else 1
        return max(40.0, min(self.width - 40.0, friend.x + side * 34 * self.scale))

    def _walk_time(self, fox, x):
        """Seconds for fox to walk to x (so a friend knows how long to wait)."""
        return abs(x - fox.x) / (WALK * self.scale) + 0.4

    def greet(self, fox, friend):
        """Walk over and boop noses; both wag happily."""
        apart = self._together(fox, friend)
        spot = self._beside(fox, friend)
        friend.do(Step("look", face=fox.x), Step("idle", self._walk_time(fox, spot), face=fox.x), Step("boop", face=fox.x),
                  Step("happy", 1.2, face=fox.x))
        fox.do(Step("walk", to_x=spot, speed=WALK), Step("boop", face=friend.x), Step("happy", 1.2, face=friend.x),
               Step("idle", 1.5, face=friend.x, then=apart))

    def groom_friend(self, fox, friend):
        """Sit beside the friend and lick its fur; it leans in, eyes closed."""
        apart = self._together(fox, friend)
        spot = self._beside(fox, friend)
        friend.do(Step("idle", self._walk_time(fox, spot), face=fox.x), Step("petted", 5.0, face=fox.x), Step("happy", 1.0))
        fox.do(Step("walk", to_x=spot, speed=WALK), Step("groom", 5.0, face=friend.x),
               Step("idle", 2.0, face=friend.x, then=apart))

    def tag_along(self, fox, friend):
        """Follow the friend on a little stroll, then sit down beside it."""
        apart = self._together(fox, friend)
        stroll = max(60.0, min(self.width - 60.0, friend.x + self.rng.choice((-1, 1)) * self.rng.uniform(120, 260) * self.scale))
        friend.do(Step("walk", to_x=stroll, speed=WALK), Step("idle", 8.0), Step("look"))
        fox.do(Step("look", face=friend.x), Step("trot", follow=friend, speed=TROT),
               Step("idle", 4.0, face=friend.x, then=apart))

    def watch_friend(self, fox, friend):
        """Sit and watch the friend's antics, head tilting."""
        fox.do(Step("watch", self.rng.uniform(3, 6), face=friend.x), Step("tilt", face=friend.x), Step("happy", 0.8))

    def snuggle(self, fox, friend):
        """Curl up to sleep right beside a sleeping friend."""
        night = self.daylight() == "night"
        spot = self._beside(fox, friend)
        fox.do(Step("walk", to_x=spot, speed=WALK), Step("yawn"),
               Step("sleep", self.rng.uniform(150, 360) * (3 if night else 1), face=friend.x))

    def play_together(self, fox, friend):
        """A play bow, then a chase: the friend runs off, the fox follows, they meet with a nose boop."""
        fox.busy_with, friend.busy_with = friend, fox
        away = 1 if friend.x >= fox.x else -1
        run_to = max(60.0, min(self.width - 60.0, friend.x + away * self.rng.uniform(140, 260) * self.scale))
        meet = run_to - away * 30 * self.scale

        def done():
            fox.busy_with = friend.busy_with = None

        friend.do(Step("tilt", face=fox.x), Step("playbow", 1.2, face=fox.x),
                  Step("trot", to_x=run_to, speed=TROT * 1.1), Step("idle", 0.6, face=fox.x),
                  Step("boop", face=fox.x), Step("happy", 1.2, face=fox.x))
        fox.do(Step("playbow", 1.4, face=friend.x), Step("trot", to_x=meet, speed=TROT),
               Step("boop", face=run_to), Step("roll", 1.6), Step("happy", 1.0, then=done))
