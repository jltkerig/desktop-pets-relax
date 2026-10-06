"""Wind, rain and snow (the local weather, or a shower from the tray menu), and night: glows on lit things,
fireflies, and paw prints in the snow."""
import math

from pet.items import Firefly, Glow


class Outdoors:
    """Part of World (see pet/world/__init__.py)."""

    def blustery(self, minutes=None):
        """Start a blustery spell now (a few minutes of gusty wind)."""
        self.blustery_left = (minutes or self.rng.uniform(3, 8)) * 60
        self.wind_dir = self.rng.choice((-1, 1))
        self._gust_phase = 0.0

    def make_it(self, kind, minutes=None):
        """A shower of rain (or snow) for a few minutes, asked for from the tray menu."""
        self.shower = (kind, (minutes or 4) * 60)

    @property
    def falling(self):
        """What's coming down: "rain", "snow" or None (a shower you asked for, else the local weather)."""
        kind, left = self.shower
        if kind and left > 0:
            return kind
        return self.weather.falling if self.weather is not None else None

    @property
    def heavy(self):
        kind, left = self.shower
        if kind and left > 0:
            return False
        return bool(self.weather is not None and self.weather.heavy)

    def precipitation(self, dt):
        """Raindrops (or snowflakes) falling over everything, and splashing (or settling) on the ground."""
        from pet.items import RainDrop, SnowFlake
        kind, left = self.shower
        if kind and left > 0:
            self.shower = (kind, left - dt)
        falling = self.falling
        if falling is None:
            return
        width = self.width / 1920
        if falling == "rain":
            rate, cap, make = (240 if self.heavy else 90) * width, int(500 * width) + 20, RainDrop
        else:
            rate, cap, make = (45 if self.heavy else 18) * width, int(220 * width) + 20, SnowFlake
        if len(self.of(make.kind)) >= cap:
            return
        count = int(rate * dt) + (1 if self.rng.random() < rate * dt % 1 else 0)
        for _ in range(count):
            self.add(make(self))

    def _weather(self, dt):
        """Every so often (about once in an hour or two) the wind gets up for a few minutes, in gusts."""
        self.weather_timer -= dt
        if self.weather_timer <= 0:
            self.weather_timer = self.rng.uniform(20 * 60, 70 * 60)
            if self.blustery_left <= 0 and self.rng.random() < 0.6:
                self.blustery()
        if self.blustery_left > 0:
            self.blustery_left -= dt
            self._gust_phase = getattr(self, "_gust_phase", 0.0) + dt
            p = self._gust_phase
            # gusts come and go: a few slow waves on top of each other, never quite still
            gust = 0.55 + 0.25 * math.sin(p * 0.9) + 0.2 * math.sin(p * 2.3 + 1) + 0.1 * math.sin(p * 5.1)
            ease = min(1.0, p / 8, self.blustery_left / 8)  # builds up and dies away gently
            target = max(0.0, min(1.0, gust)) * ease
        else:
            target = 0.0
        self.wind += (target - self.wind) * min(1.0, dt * 2)

    @property
    def dark(self):
        return self.daylight() in ("night", "dusk")

    def lit_up(self):
        """What glows at night: jack-o'-lanterns and the Christmas tree. (thing, glow sprite, how high its middle is:
        None for halfway up)"""
        lit = []
        for p in self.of("pumpkin") + self.of("deco"):
            if p.anim.name.endswith("_jack"):
                lit.append((p, "glow_warm_big" if p.huge else "glow_warm", None))
        for p in self.of("prop"):
            if p.variant == "xmas_tree":
                lit.append((p, "glow_lights", None))
        for jar in self.of("yard"):
            if jar.variant == "firefly_jar" and jar.count:
                lit.append((jar, "glow_jar", 9))
        return lit

    def night_lights(self, dt):
        """After dark: glows over the jack-o'-lanterns and the Christmas lights, and fireflies over the grass on a
        summer night. They fade away at dawn."""
        glows = {g.holder: g for g in self.of("glow") if g.holder.kind != "firefly"}
        wanted = {thing: (sprite, dy) for thing, sprite, dy in self.lit_up()} if self.dark else {}
        for holder, g in glows.items():
            if holder not in wanted:
                g.fading = True
        for holder, (sprite, dy) in wanted.items():
            if holder not in glows:
                self.add(Glow(self, holder, sprite, dy))
        flies = [f for f in self.of("firefly") if not f.leaving]
        if self.dark and self.season == "summer" and not self.snowed_over and self.falling is None:
            if len(flies) < 12 and self.rng.random() < dt * 0.8:
                self.add(Firefly(self))
        else:
            for f in flies:
                f.leaving = True
                f.glow.fading = True

    def leave_paw_prints(self):
        """Foxes walking about on a snowy day leave a trail of paw prints, which slowly fade. (So do muddy foxes
        fresh from splashing in a puddle.)"""
        from pet.items import MudPrint, PawPrint
        snowy = self.snowed_over
        if not snowy and not any(getattr(f, "muddy", 0) > 0 for f in self.of("fox")):
            return
        s = self.scale
        for fox in self.of("fox"):
            if fox.alpha <= 0 or fox.held or fox.y < self.ground - 1 or not (snowy or getattr(fox, "muddy", 0) > 0):
                continue
            last = getattr(fox, "last_print", None)
            if last is None or abs(fox.x - last) > 11 * s:
                fox.last_print = fox.x
                if last is not None and len(self.of("print")) < 120:
                    self.add((PawPrint if snowy else MudPrint)(self, fox.x, self.ground))
