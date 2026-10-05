"""Questions a fox asks and the games it plays on its own: where to nap, leaves and acorns to chase, the
cursor to pounce on, the pool, butterflies and fluff, fruit to nibble, things to climb, balls and cobs
you throw."""
from pet import sprites
from pet.fox import Step, TROT, ZOOM
from pet.items import Kernel


class FoxPlay:
    """Part of World (see pet/world/__init__.py)."""

    def _under(self, tree, x):
        left, right = tree.base_range()
        return left <= x <= right

    def den(self):
        dens = self.of("den")
        return dens[0] if dens else None

    def nap_spot(self, fox):
        """The den if there is one (it curls up inside), else under the oak, else where it is. Now and then in the
        daytime, for a change, a nap in the dappled shade under the birch."""
        fox.naps = getattr(fox, "naps", 0) + 1
        birch = next(iter(self.of("birch")), None)
        if birch is not None and fox.naps % 3 == 0 and self.daylight() == "day":
            return birch.x + (14 if fox.palette == "orange" else -14) * self.scale
        den = self.den()
        if den is not None:
            return den.entrance_x()
        tree = self.tree()
        if tree is None:
            return None
        if self._under(tree, fox.x):
            return fox.x
        left, right = tree.base_range()
        return self.rng.uniform(left, right)

    def sleeping_fox_under(self, acorn):
        for fox in self.of("fox"):
            if fox.asleep:
                left, top, w, _ = fox.rect()
                if left + w * 0.3 <= acorn.x <= left + w * 0.8 and acorn.y >= top + 34 * self.scale:
                    return fox
        return None

    def nearest_fox(self, x):
        foxes = self.of("fox")
        return min(foxes, key=lambda f: abs(f.x - x)) if foxes else None

    def acorn_near(self, fox, reach):
        acorns = [a for a in self.of("acorn") if a.on_ground and not a.taken and abs(a.x - fox.x) < reach * self.scale / 2]
        return min(acorns, key=lambda a: abs(a.x - fox.x)) if acorns else None

    def leaf_near(self, fox, reach):
        leaves = [l for l in self.of("leaf") if l.falling and not getattr(l, "chased", False)
                  and abs(l.x - fox.x) < reach * self.scale / 2 and l.y > self.ground - 170 * self.scale]
        return min(leaves, key=lambda l: abs(l.x - fox.x)) if leaves else None

    def chase_leaf(self, fox, leaf):
        """Run under a falling leaf, crouch, and pounce on it as it comes down."""
        leaf.chased = True
        side = 1 if leaf.x >= fox.x else -1
        under = max(40.0, min(self.width - 40.0, leaf.x - side * 22 * self.scale))
        fox.do(Step("trot", to_x=under, speed=TROT * 1.15), Step("crouch", self.rng.uniform(0.3, 0.7), face=leaf.x),
               Step("pounce", to_x=leaf.x, leap=30, then=lambda: self.catch_leaf(fox, leaf)), Step("dive"),
               Step("hop"), Step("happy", 1.0))

    def catch_leaf(self, fox, leaf):
        """The pounce lands: a leaf close by is caught (it disappears under the paws)."""
        if not leaf.gone and abs(leaf.x - fox.x) < 40 * self.scale:
            leaf.gone = True
        leaf.chased = False

    def cursor_to_pounce(self, fox):
        """The cursor resting near the ground, not too far away: something to pounce on."""
        x, y = self.cursor
        if self.cursor_still > 1.5 and self.ground - 90 * self.scale < y <= self.ground + 2 and \
                40 * self.scale < abs(x - fox.x) < 260 * self.scale:
            return x
        return None

    def cob_thrown(self, cob):
        """You threw a corn cob (or an apple...): the nearest fox that's free races after it and bats it about."""
        free = [f for f in self.of("fox") if not f.asleep and not f.held and not f.vy and f.carrying is None
                and f.alpha > 0 and not f.up_high and f.dragging_folder is None]
        if not free:
            return None
        fox = min(free, key=lambda f: abs(f.x - cob.x))
        fox.busy_with = None

        def bat():
            if not cob.gone and not cob.held and abs(cob.x - fox.x) < 50 * self.scale:
                cob.on_ground, cob.bounced = False, True
                cob.vx, cob.vy = fox.facing * self.rng.uniform(70, 130) * self.scale, -90 * self.scale

        fox.do(Step("tilt", 0.25, face=cob.x), Step("run", follow=cob, speed=ZOOM * 0.75),
               Step("pounce", 0.5, face=cob.x), Step("bat", face=cob.x, then=bat), Step("happy", 1.0),
               Step("playbow", 1.0))
        return fox

    def ball_thrown(self, ball):
        """You threw a dug-up icon: the nearest fox that's awake and free races after it to fetch it."""
        free = [f for f in self.of("fox") if not f.asleep and not f.held and not f.vy and f.carrying is None
                and f.alpha > 0 and not f.up_high]
        if not free:
            return None
        if ball.chased_by in free:
            fox = ball.chased_by
        else:
            fox = min(free, key=lambda f: abs(f.x - ball.x))
        ball.chased_by = fox
        fox.busy_with = None
        fox.do(Step("tilt", 0.25, face=ball.x), Step("run", follow=ball, speed=ZOOM * 0.75,
                                                       then=lambda: self.catch_ball(fox, ball, tries=1)))
        return fox

    def catch_ball(self, fox, ball, tries):
        """Got there: grab it (and bring it back to where it was thrown from), or keep chasing."""
        if ball.gone or ball.held or ball.carried_by is not None or ball.chased_by is not fox:
            return
        if abs(ball.x - fox.x) > 50 * self.scale or not ball.low():
            if tries < 4:  # it bounced off again: after it!
                fox.do(Step("run", follow=ball, speed=ZOOM * 0.75,
                            then=lambda: self.catch_ball(fox, ball, tries + 1)))
            else:
                ball.chased_by = None
                fox.do(Step("tilt", face=ball.x), Step("happy", 0.8))
            return
        ball.carried_by, fox.carrying, ball.chased_by = fox, ball, None
        ball.vx = ball.vy = 0.0
        home = ball.thrown_from if ball.thrown_from is not None else fox.x
        fox.do(Step("hop", face=ball.x), Step("trot", to_x=home, speed=TROT * 1.2),
               Step("idle", 0.4, then=lambda: self.drop_treasure(fox)), Step("playbow", 1.0), Step("happy", 1.0),
               Step("watch", 2.5))

    def pool_near(self, fox, reach):
        near = [p for p in self.of("prop") if p.variant == "pool" and abs(p.x - fox.x) < reach * self.scale / 2]
        return near[0] if near else None

    def splash(self, pool, drops=10):
        """Water splashing up out of the kiddie pool: drops flying, ripples spreading."""
        from pet.items import Droplet
        s = self.scale
        pool.react()
        for _ in range(drops):
            self.add(Droplet(self, pool.x + self.rng.uniform(-18, 18) * s, pool.y - 8 * s))

    def paddle(self, fox, pool):
        """A hot fox in the kiddie pool: a hop in, a happy splash about, a roll, a hop out and a shake."""
        s, rng = self.scale, self.rng
        side = -1 if fox.x < pool.x else 1
        edge = pool.x + side * 40 * s
        water = self.ground - 3 * s  # standing in the water, a little lower than the rim
        out = max(60.0, min(self.width - 60.0, pool.x - side * rng.uniform(50, 80) * s))
        fox.do(Step("trot", to_x=edge, speed=TROT), Step("crouch", 0.4, face=pool.x),
               Step("hop", to_x=pool.x + side * 6 * s, to_y=water, leap=14, then=lambda: self.splash(pool, 12)),
               Step("happy", 1.2, then=lambda: self.splash(pool, 8)), Step("bat", then=lambda: self.splash(pool, 6)),
               Step("happy", 1.0), Step("crouch", 0.3, face=out),
               Step("hop", to_x=out, to_y=self.ground, leap=14, then=lambda: self.splash(pool, 5)),
               Step("scratch"), Step("happy", 0.8))

    def floater_near(self, fox):
        """A butterfly flying low, or a bit of seed fluff drifting past, close enough for a fox to pounce at."""
        s = self.scale
        near = [t for t in self.of("butterfly") + self.of("fluff") + self.of("firefly")
                if abs(t.x - fox.x) < 160 * s and t.y > self.ground - 70 * s and getattr(t, "state", "") != "rest"]
        return min(near, key=lambda t: abs(t.x - fox.x)) if near else None

    def chase_floater(self, fox, thing):
        """A crouch, a wiggle, and a leap at it. It always gets away (the butterfly flutters up, the fluff floats
        off), and the fox is delighted anyway."""
        x = max(40.0, min(self.width - 40.0, thing.x))
        fox.do(Step("crouch", 0.5, face=thing.x),
               Step("pounce", to_x=x, leap=26, then=lambda: self._dodge(thing)),
               Step("land"), Step("happy", 1.0), Step("tilt", face=thing.x))

    def _dodge(self, thing):
        s = self.scale
        if thing.kind == "butterfly":
            thing.state, thing.target = "flutter", None
            thing.y -= 24 * s
        elif thing.kind == "firefly":
            thing.home_y -= 30 * s  # up and away, still blinking
        else:
            thing.vy = -30.0  # the fluff puffs up out of reach

    def produce_near(self, fox, reach):
        """Something tasty lying on the ground nearby: an apple, a tomato, a lettuce (or a radish)."""
        food = [a for a in self.of("acorn") if getattr(a, "produce", None) and a.on_ground and not a.taken
                and abs(a.x - fox.x) < reach * self.scale / 2]
        return min(food, key=lambda a: abs(a.x - fox.x)) if food else None

    def nibble(self, fox, food):
        """Trot over, sniff, munch. Yum! (A radish, though: bleh! a shake of the head.)"""
        from pet.visitors import Bubble
        s = self.scale
        food.taken = True  # spoken for
        side = 1 if fox.x < food.x else -1
        spot = max(40.0, min(self.width - 40.0, food.x - side * 16 * s))
        radish = food.produce == "radish"

        def eat():
            if food.gone or getattr(food, "held", False) or abs(food.x - fox.x) > 40 * s:
                return  # you took it away (or threw it): never mind
            for _ in range(4):
                self.add(Kernel(self, food.x + self.rng.uniform(-3, 3) * s, food.y - 3 * s, food.bit))
            food.gone = True
            bubble = self.add(Bubble(self, fox, "bleh_bubble" if radish else "yum_bubble", rise=34))
            bubble.life = 1.8  # long enough to read

        after = [Step("scratch"), Step("look")] if radish else [Step("happy", 1.2)]
        fox.do(Step("trot", to_x=spot, speed=TROT), Step("sniff", face=food.x), Step("chew", 1.6, then=eat), *after)

    def climbable_near(self, fox, reach):
        near = [t for t in self.of("climb") if t.available and abs(t.x - fox.x) < reach * self.scale / 2]
        return self.rng.choice(near) if near else None

    def climb(self, fox, thing):
        """Hop up the pile one level at a time, enjoy the view from the top, then leap off. (The slide: up the
        ladder, and whee, down the chute.)"""
        s, rng = self.scale, self.rng
        slide = thing.variant == "slide"
        side = -1 if fox.x < thing.x or slide else 1  # climb up the side it's on (the slide's ladder is on the left)
        path = [(thing.x + side * abs(dx) * s if dx else thing.x, self.ground - h * s) for dx, h in thing.levels]
        start = path[0][0] + side * 30 * s
        steps = [Step("trot", to_x=start, speed=TROT), Step("crouch", 0.4, face=thing.x)]
        for x, y in path:
            steps.append(Step("hop", to_x=x, to_y=y, leap=12))
        if slide:
            m = sprites.meta("slide")
            ax, ay = m["anchor"]
            chute = [(thing.x + (px - ax) * s, thing.y - (ay - py) * s) for px, py in m["chute"]]
            steps += [Step("happy", 0.8), Step("crouch", 0.3, face=chute[-1][0])]
            for x, y in chute:  # sliding down, sitting tight, faster and faster
                steps.append(Step("crouch", to_x=x, to_y=y, leap=0.01))
            fox.do(*steps, Step("land"), Step("happy", 1.2), Step("roll", 1.0), Step("happy", 0.8))
            return
        top_x = path[-1][0]
        steps += [Step("look"), Step("happy", 1.4), Step("tilt"), Step("idle", rng.uniform(2, 5))]
        if rng.random() < 0.5:
            steps.append(Step("playbow", 1.0))
        land = max(60.0, min(self.width - 60.0, top_x - side * rng.uniform(70, 120) * s))
        steps += [Step("crouch", 0.5, face=land), Step("pounce", to_x=land, to_y=self.ground, leap=18),
                  Step("land"), Step("happy", 1.0)]
        fox.do(*steps)

    def wander_target(self, fox):
        reach = self.rng.uniform(80, 360) * self.scale / 2
        x = fox.x + reach * self.rng.choice((-1, 1))
        return max(60.0, min(self.width - 60.0, x))

    def kick(self, acorn, fox):
        if acorn.gone or acorn.taken:
            return
        acorn.vx = fox.facing * self.rng.uniform(90, 170) * self.scale
        acorn.on_ground = True
