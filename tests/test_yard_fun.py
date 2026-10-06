"""The newer seasonal things and the games the foxes play with them: winter's snowman, snowballs, frozen pond,
bird feeder and presents; spring's puddles, bunnies, robin's nest, kite and watering can; summer's sprinkler,
beach ball, hammock, firefly jar, sunflowers and frog."""
import unittest

from helpers import make_world, run, season_world  # first: sets up a scratch user-data folder
from pet import save, seasons, sprites
from pet.fox import Step
from pet.items import BeachBall, Firefly, Puddle, Snowball


def yard(world, variant):
    return next(t for t in world.of("yard") if t.variant == variant)


def one_fox(season, **kw):
    world, clock = make_world(season, orange=True, grey=False, **kw)
    world.settings["snow"] = True
    fox = world.of("fox")[0]
    return world, clock, fox


def step(fox):
    return fox.step.anim if fox.step is not None else None


def run_until(world, clock, check, seconds=30, fps=30):
    for _ in range(int(seconds * fps)):
        run(world, clock, 1 / fps, fps)
        if check():
            return True
    return False


class PutOut(unittest.TestCase):
    NEW = {"winter": {"snowman", "snowballs", "pond", "feeder", "gifts"},
           "spring": {"nest", "kite", "watering_can"},
           "summer": {"sprinkler", "beachball", "hammock", "firefly_jar", "sunflowers", "watering_can"}}

    def test_each_season_has_its_new_things_and_no_others(self):
        for season in ("winter", "spring", "summer", "autumn"):
            world, _ = season_world(season)
            out = {t.variant for t in world.of("yard")}
            out |= {"beachball" for b in world.of("ball") if isinstance(b, BeachBall)}
            out |= {"watering_can" for _ in world.of("can")} | {"nest" for _ in world.of("nest")}
            out |= {"kite" for _ in world.of("kite")}
            self.assertEqual(out, self.NEW.get(season, set()), season)

    def test_every_new_item_has_a_season_a_default_and_sprites(self):
        for name in set().union(*self.NEW.values()):
            self.assertIn(name, seasons.ITEMS)
            self.assertIn(name, save.DEFAULTS["items"])
        for name in ("snowman", "snowballs", "pond", "feeder", "gifts", "gifts_grey", "nest_eggs", "kite_ground",
                     "watering_can_pour", "sprinkler_off", "beachball", "hammock_front", "firefly_jar_4",
                     "sunflowers_night", "bunny_hop", "cardinal_perch", "chickadee_fly", "puddle_rain", "mudprint"):
            self.assertTrue(sprites.exists(name), name)

    def test_taking_them_in_from_the_toy_box(self):
        world, _ = season_world("winter")
        world.settings["items"]["snowman"]["out"] = False
        world.rebuild()
        self.assertFalse([t for t in world.of("yard") if t.variant == "snowman"])
        world.settings["items"]["snowman"]["out"] = True
        world.rebuild()
        self.assertTrue(yard(world, "snowman"))

    def test_a_dragged_yard_thing_keeps_its_spot(self):
        world, _ = season_world("summer")
        world.settings["items"]["hammock"]["x"] = 700
        world.settings["items"]["hammock"]["out"] = False
        world.rebuild()
        world.settings["items"]["hammock"]["out"] = True
        world.rebuild()
        self.assertEqual(yard(world, "hammock").x, 700)


class Winter(unittest.TestCase):
    def test_a_fox_pinches_the_snowmans_nose_and_it_goes_back_on(self):
        world, clock, fox = one_fox("winter")
        snowman = yard(world, "snowman")
        world.steal_nose(fox, snowman)
        self.assertTrue(run_until(world, clock, lambda: not snowman.nose_on))
        carrot = snowman.carrot
        self.assertIs(fox.carrying, carrot)
        self.assertEqual(snowman.anim.name.split("_wobble")[0], "snowman_nonose")
        self.assertTrue(run_until(world, clock, lambda: fox.carrying is None))
        self.assertTrue(carrot.draggable)
        carrot.click()
        self.assertTrue(snowman.nose_on)
        self.assertTrue(carrot.gone)

    def test_dropping_the_carrot_on_his_face_puts_it_back(self):
        world, clock, fox = one_fox("winter")
        snowman = yard(world, "snowman")
        carrot = snowman.take_nose(fox)
        fox.pick_up()  # it lets go
        carrot.pick_up()
        carrot.x, carrot.y = snowman.nose_point()
        carrot.drop()
        self.assertTrue(snowman.nose_on)

    def test_a_lost_carrot_is_replaced(self):
        world, clock, fox = one_fox("winter")
        snowman = yard(world, "snowman")
        snowman.take_nose(fox).gone = True  # eaten!
        fox.carrying = None
        run(world, clock, 50, fps=10)
        self.assertTrue(snowman.nose_on)

    def test_he_slumps_on_a_day_without_snow(self):
        world, clock, _ = one_fox("winter")
        world.settings["snow"] = False
        run(world, clock, 0.2)
        self.assertEqual(yard(world, "snowman").anim.name, "snowman_melty")

    def test_snowballs_come_off_the_pile_and_burst_when_they_land(self):
        world, clock, fox = one_fox("winter")
        pile = yard(world, "snowballs")
        ball = pile.lift()
        ball.pick_up()
        ball.x, ball.y = pile.x + 300, world.ground - 200
        ball.throw(900, -400)
        self.assertIs(ball.chased_by, fox)
        self.assertTrue(run_until(world, clock, lambda: ball.gone, 10))
        self.assertTrue(any(c.anim.name == "snow_puff" for c in world.of("snow")))

    def test_clicking_the_pile_tosses_a_snowball_up(self):
        world, clock, _ = one_fox("winter")
        yard(world, "snowballs").click()
        balls = [b for b in world.of("ball") if isinstance(b, Snowball)]
        self.assertEqual(len(balls), 1)
        self.assertLess(balls[0].vy, 0)

    def test_a_snowball_bursts_on_a_fox_who_doesnt_mind(self):
        world, clock, fox = one_fox("winter")
        run(world, clock, 0.2)
        ball = world.add(Snowball(world, fox.x - 30, fox.y - 20))
        ball.vx = 300
        run(world, clock, 0.4)
        self.assertTrue(ball.gone)
        self.assertIn(step(fox), ("tilt", "scratch", "happy", "playbow"))

    def test_skidding_across_the_pond(self):
        world, clock, fox = one_fox("winter")
        pond = yard(world, "pond")
        world.skate(fox, pond)
        crossed, whee = [], []
        run_until(world, clock, lambda: crossed.append(fox.x) or whee.extend(world.of("bubble")) or step(fox) == "roll", 30)
        self.assertLess(min(crossed), pond.x)
        self.assertGreater(max(crossed), pond.x)
        self.assertTrue(any(b.anim.name == "whee_bubble" for b in whee))

    def test_cardinals_and_chickadees_come_to_the_feeder_and_scatter_when_stalked(self):
        world, clock = season_world("winter", orange=True)
        world.settings["snow"] = False
        feeder = yard(world, "feeder")
        world.invite_visitor("winterbirds")
        birds = world.of("songbird")
        self.assertTrue({b.species for b in birds} <= {"cardinal", "chickadee"})
        self.assertTrue(any(b.perch.holder is feeder for b in birds) or
                        all(abs(b.perch.x - feeder.x) < 60 for b in birds))
        fox = world.of("fox")[0]
        fox.energy, fox.plan = 1.0, fox.plan.__class__()
        run(world, clock, 12)
        bird = next(b for b in world.of("songbird") if b.state != "leave")
        world.stalk_birds(fox, bird)
        self.assertTrue(run_until(world, clock, lambda: all(b.state == "leave" or b.gone for b in birds), 30))

    def test_a_fox_hides_in_the_presents_and_pops_out_when_you_click(self):
        world, clock, fox = one_fox("winter")
        gifts = yard(world, "gifts")
        world.hide_in_gifts(fox, gifts)
        self.assertTrue(run_until(world, clock, lambda: gifts.hider is fox))
        self.assertEqual(fox.alpha, 0)
        run(world, clock, 0.1)
        self.assertEqual(gifts.anim.name, "gifts_orange")
        gifts.click()
        self.assertEqual(fox.alpha, 1)
        self.assertIsNone(gifts.hider)
        self.assertIsNone(fox.hiding_in)


class Spring(unittest.TestCase):
    def test_puddles_form_in_the_rain_and_dry_up_after(self):
        world, clock = season_world("spring")
        world.make_it("rain", minutes=3)
        run(world, clock, 150, fps=10)
        puddles = world.of("puddle")
        self.assertTrue(puddles)
        self.assertTrue(puddles[0].anim.name.endswith("_rain"))
        run(world, clock, 40 + Puddle.DRIES_IN, fps=10)
        self.assertFalse(world.of("puddle"))

    def test_no_puddles_in_winter(self):
        world, clock = season_world("winter")
        world.make_it("rain", minutes=3)
        run(world, clock, 120, fps=10)
        self.assertFalse(world.of("puddle"))

    def test_splashing_in_a_puddle_leaves_muddy_paw_prints(self):
        world, clock, fox = one_fox("spring")
        puddle = world.add(Puddle(world, fox.x + 200))
        world.make_it("rain", minutes=5)
        world.splash_puddle(fox, puddle)
        self.assertTrue(run_until(world, clock, lambda: fox.muddy > 0))
        self.assertTrue(world.of("drop"))
        fox.do(Step("walk", to_x=fox.x + 300, speed=30))
        run(world, clock, 5)
        self.assertTrue([p for p in world.of("print") if p.anim.name == "mudprint"])

    def test_bunnies_graze_and_are_far_too_quick_to_catch(self):
        world, clock = season_world("spring", orange=True)
        world.invite_visitor("bunnies")
        bunnies = world.of("bunny")
        self.assertIn(len(bunnies), (2, 3))
        self.assertTrue(run_until(world, clock, lambda: all(b.state == "graze" for b in bunnies), 40))
        fox = world.of("fox")[0]
        world.chase_bunnies(fox, bunnies[0])
        self.assertTrue(run_until(world, clock, lambda: all(b.gone for b in bunnies), 40))
        self.assertGreater(min(abs(b.x - fox.x) for b in bunnies), 30)

    def test_the_nest_sits_in_the_oak_shows_its_eggs_and_scolds_foxes(self):
        world, clock, fox = one_fox("spring")
        nest = world.of("nest")[0]
        tree = world.tree()
        tree.x += 100
        run(world, clock, 0.1)
        self.assertAlmostEqual(nest.x, tree.x + nest.SPOT[0] * world.scale)
        nest.click()
        self.assertEqual(nest.anim.name, "nest_eggs")
        run(world, clock, 3)
        fox.x = tree.x
        fox.do(Step("sniff"), Step("idle", 30))
        self.assertTrue(run_until(world, clock, lambda: any(b.anim.name == "tweet_bubble" for b in world.of("bubble")),
                                  20))

    def test_no_nest_without_the_oak(self):
        world, clock = season_world("spring")
        world.settings["items"]["oak"]["out"] = False
        world.rebuild()
        run(world, clock, 0.1)
        self.assertFalse(world.of("nest"))

    def test_the_kite_is_stuck_in_the_oak_until_shaken_loose(self):
        world, clock = season_world("spring")
        kite = world.of("kite")[0]
        self.assertEqual(kite.state, "stuck")
        self.assertLess(kite.y, world.ground - 200)
        kite.click()
        self.assertTrue(run_until(world, clock, lambda: kite.state == "ground", 30))
        self.assertEqual(kite.anim.name, "kite_ground")

    def test_flying_the_kite_gets_a_fox_running_after_it(self):
        world, clock, fox = one_fox("spring")
        kite = world.of("kite")[0]
        kite.pick_up()
        kite.x, kite.y = fox.x + 400, world.ground - 150
        self.assertTrue(run_until(world, clock, lambda: kite.chaser is fox, 10))
        self.assertEqual(fox.step.follow if step(fox) == "run" else kite, kite)
        kite.drop()
        self.assertTrue(run_until(world, clock, lambda: kite.state == "ground", 30))

    def test_watering_makes_the_garden_grow_faster(self):
        world, clock = season_world("spring")
        radishes = next(c for c in world.of("crop") if c.variant == "radishes")
        can = world.of("can")[0]
        can.pick_up()
        can.x, can.y = radishes.x - 18 * world.scale, radishes.y - 30
        before = radishes.planted
        run(world, clock, 5)
        self.assertEqual(can.anim.name, "watering_can_pour")
        self.assertLess(radishes.planted, before - 20)
        can.x = 10
        can.drop()
        run(world, clock, 2)
        self.assertEqual(can.y, world.ground)
        self.assertEqual(world.settings["items"]["watering_can"]["x"], 10)


class Summer(unittest.TestCase):
    def test_the_sprinkler_turns_off_and_on_and_foxes_dash_through_it(self):
        world, clock, fox = one_fox("summer")
        sprinkler = yard(world, "sprinkler")
        sprinkler.click()
        run(world, clock, 0.1)
        self.assertEqual(sprinkler.anim.name, "sprinkler_off")
        sprinkler.click()
        world.run_through_sprinkler(fox, sprinkler)
        start = fox.x
        self.assertTrue(run_until(world, clock, lambda: step(fox) == "happy", 30))
        self.assertTrue(world.of("drop"))  # a good shake
        self.assertNotEqual(start < sprinkler.x, fox.x < sprinkler.x)  # out the other side

    def test_a_thrown_beach_ball_gets_chased_and_nosed_up(self):
        world, clock, fox = one_fox("summer")
        ball = next(b for b in world.of("ball") if isinstance(b, BeachBall))
        ball.pick_up()
        ball.x, ball.y = fox.x + 200, world.ground - 100
        ball.throw(600, -300)
        self.assertIs(ball.chased_by, fox)
        bounced = []
        run_until(world, clock, lambda: bounced.append(ball.vy) or step(fox) == "happy", 30)
        self.assertTrue(any(v < -300 for v in bounced))

    def test_the_beach_ball_floats_in_the_pool(self):
        world, clock = season_world("summer")
        pool = next(p for p in world.of("prop") if p.variant == "pool")
        ball = next(b for b in world.of("ball") if isinstance(b, BeachBall))
        ball.x, ball.y = pool.x, world.ground - 150
        run(world, clock, 6)
        self.assertTrue(ball.floating)
        self.assertLess(ball.y, world.ground)

    def test_a_sleepy_fox_naps_in_the_hammock_and_hops_down_after(self):
        world, clock, fox = one_fox("summer", hour=13)
        hammock = yard(world, "hammock")
        fox.energy = 0.1
        fox.plan.clear()
        fox.step = None
        world.rng.random = lambda: 0.1  # (always takes the hammock)
        self.assertTrue(run_until(world, clock, lambda: fox.asleep, 60))
        self.assertTrue(fox.up_high)
        self.assertIs(hammock.occupant(), fox)
        self.assertAlmostEqual(fox.x, hammock.x)
        self.assertFalse(fox.in_den)
        fox.step.seconds = 0
        self.assertTrue(run_until(world, clock, lambda: not fox.up_high, 20))

    def test_fireflies_go_in_the_jar_and_out_again(self):
        world, clock, fox = one_fox("summer", hour=23)
        jar = yard(world, "firefly_jar")
        fly = world.add(Firefly(world))
        fly.x = jar.x + 100
        world.into_the_jar(fox, fly, jar)
        self.assertTrue(run_until(world, clock, lambda: jar.count == 1, 30))
        run(world, clock, 3)
        self.assertEqual(jar.anim.name, "firefly_jar_1")
        self.assertTrue([g for g in world.of("glow") if g.holder is jar])
        flies = len(world.of("firefly"))
        jar.click()
        self.assertEqual(jar.count, 0)
        self.assertEqual(len(world.of("firefly")), flies + 1)

    def test_sunflowers_follow_the_sun_and_sleep_at_night(self):
        world, clock = season_world("summer")
        flowers = yard(world, "sunflowers")
        looks = {}
        for hour in (7, 17, 22):
            clock[0] = clock[0].replace(hour=hour)
            run(world, clock, 0.1)
            looks[hour] = flowers.anim.name
        self.assertEqual(looks[7], "sunflowers_0")   # the sun's low on the left, and they're on the right
        self.assertEqual(looks[22], "sunflowers_night")
        self.assertGreater(int(looks[17][-1]), 0)
        self.assertTrue(flowers.flower_heads())

    def test_a_frog_comes_to_the_pool_and_leaps_away_from_a_pounce(self):
        world, clock, fox = one_fox("summer")
        frog = world.invite_visitor("frog")
        self.assertTrue(frog.visiting)
        self.assertTrue(run_until(world, clock, lambda: frog.state == "sit", 40))
        world.pounce_frog(fox, frog)
        self.assertTrue(run_until(world, clock, lambda: frog.gone, 40))

    def test_new_visitors_are_in_their_seasons(self):
        self.assertIn("winterbirds", seasons.VISITORS["winter"])
        self.assertIn("bunnies", seasons.VISITORS["spring"])
        self.assertIn("frog", seasons.VISITORS["summer"])


if __name__ == "__main__":
    unittest.main()


def bare_stage(world):
    """The Stage's mouse handling, without its windows (needs PySide6 to import)."""
    from pet.view.stage import Stage
    stage = Stage.__new__(Stage)
    stage.world, stage.settings = world, world.settings
    stage.press = stage.dragging = None
    stage.trail, stage.elapsed, stage.last_pet = [], 0.0, 0.0
    return stage


try:
    import PySide6  # noqa: F401
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "needs PySide6")
class TheMouse(unittest.TestCase):
    def test_dragging_up_off_the_pile_gives_you_a_snowball_to_throw(self):
        world, clock = season_world("winter")
        stage = bare_stage(world)
        pile = yard(world, "snowballs")
        x, y = pile.x, pile.y - 10
        stage.pressed(x, y)
        stage.moved(x, y - 30, True)
        ball = stage.dragging
        self.assertIsInstance(ball, Snowball)
        self.assertTrue(ball.held)
        stage.released()
        self.assertFalse(ball.held)

    def test_dragging_the_pile_sideways_moves_it(self):
        world, clock = season_world("winter")
        stage = bare_stage(world)
        pile = yard(world, "snowballs")
        x, y = pile.x, pile.y - 10
        stage.pressed(x, y)
        stage.moved(x + 100, y, True)
        stage.released()
        self.assertEqual(world.settings["items"]["snowballs"]["x"], round(x + 100))

    def test_the_nest_gets_its_click_not_the_oak(self):
        world, clock = season_world("spring")
        stage = bare_stage(world)
        nest = world.of("nest")[0]
        stage.pressed(nest.x, nest.y - 4)
        stage.released()
        self.assertEqual(nest.anim.name, "nest_eggs")

    def test_picking_up_and_letting_go_of_the_kite_and_the_watering_can(self):
        world, clock = season_world("spring")
        stage = bare_stage(world)
        for thing in (world.of("kite")[0], world.of("can")[0]):
            left, top, w, h = thing.rect()
            x, y = left + w / 2, top + h / 2
            stage.pressed(x, y)
            self.assertIs(stage.press[0], thing)
            stage.moved(x + 20, y - 20, True)
            self.assertTrue(thing.held)
            stage.released()
            self.assertFalse(thing.held)
