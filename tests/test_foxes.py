"""The foxes: moods and choices, clicks and petting, zoomies, two foxes together, chewing, climbing,
and the games they play with the newer things."""
import datetime
import unittest

from helpers import make_world, run, season_world  # first: sets up a scratch user-data folder
from pet.fox import Step
from pet.items import Acorn


class Foxes(unittest.TestCase):
    def test_an_acorn_landing_on_a_sleeping_fox_wakes_it_happily(self):
        world, clock = make_world(orange=True, grey=False)
        world.settings["items"]["den"]["out"] = False  # napping out in the open, under the oak
        world.rebuild()
        fox = world.of("fox")[0]
        fox.do(Step("sleep", 999))
        run(world, clock, 0.1)
        self.assertTrue(fox.asleep)
        left, top, w, _ = fox.rect()
        world.add(Acorn(world, left + w * 0.6, top - 200))
        run(world, clock, 2.0)
        self.assertFalse(fox.asleep)
        seen = [fox.step.anim if fox.step else None] + [s.anim for s in fox.plan]
        self.assertTrue({"wake", "happy", "tilt"} & set(seen), seen)

    def test_foxes_only_ever_play_happy_animations(self):
        world, clock = make_world()
        for fox in world.of("fox"):
            for _ in range(30):
                fox.poke()
                fox.pet()
        sad = {"grumpy", "angry", "hiss", "growl", "annoyed"}
        for fox in world.of("fox"):
            self.assertFalse(sad & ({s.anim for s in fox.plan} | {fox.step.anim if fox.step else ""}))

    def test_a_dropped_fox_falls_and_lands(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.pick_up()
        fox.y = world.ground - 300
        fox.drop()
        run(world, clock, 2.0)
        self.assertEqual(fox.y, world.ground)
        self.assertFalse(fox.held)

    def test_a_sleepy_fox_naps_under_the_oak_when_the_den_is_put_away(self):
        world, clock = make_world(orange=True, grey=False, hour=23)
        world.settings["items"]["den"]["out"] = False
        world.rebuild()
        fox = world.of("fox")[0]
        fox.energy = 0.1
        fox.plan.clear()
        fox.step = None
        run(world, clock, 40)
        left, right = world.tree().base_range()
        self.assertTrue(fox.asleep)
        self.assertTrue(left <= fox.x <= right)

    def test_twenty_busy_minutes_run_without_errors(self):
        world, clock = make_world(seed=11)
        world.timers = {"leaf": 0, "acorn": 0, "visitor": 0}
        run(world, clock, 20 * 60, fps=15)
        self.assertEqual(len(world.of("fox")), 2)


class Zoomies(unittest.TestCase):
    def test_zoomies_run_to_the_far_end_and_partway_back(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.x = 300.0
        fox.do(*fox._zoomies())
        xs = []
        for _ in range(20 * 30):
            run(world, clock, 1 / 30)
            if fox.step is not None and fox.step.anim == "run":
                xs.append(fox.x)
        self.assertGreater(max(xs), world.width - 100)       # reached the far end
        self.assertLess(xs[-1], world.width - 300)          # and dashed back


class Climbing(unittest.TestCase):
    def test_a_fox_climbs_the_barrels_sits_on_top_and_leaps_off(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        barrels = [t for t in world.of("climb") if t.variant == "barrels"][0]
        world.climb(fox, barrels)
        on_top = None
        for _ in range(40 * 30):
            run(world, clock, 1 / 30)
            if fox.step is not None and fox.step.anim == "look":
                on_top = fox.y
        self.assertAlmostEqual(on_top, world.ground - 60 * world.scale, delta=1)  # looked around from the top barrel
        self.assertEqual(fox.y, world.ground)                                     # and jumped back down

    def test_a_fox_left_up_high_hops_down_before_doing_anything_else(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.plan.clear()
        fox.step = None
        fox.y = world.ground - 30 * world.scale
        run(world, clock, 2)
        self.assertEqual(fox.y, world.ground)

    def test_haystacks_are_out_in_summer_and_autumn_and_barrels_all_year(self):
        for season, hay in (("winter", False), ("spring", False), ("summer", True), ("autumn", True)):
            world, _ = make_world(season, orange=False, grey=False)
            kinds = {t.variant for t in world.of("climb")}
            self.assertIn("barrels", kinds, season)
            self.assertEqual("haystack" in kinds, hay, season)


class Clicks(unittest.TestCase):
    def setUp(self):
        self.world, self.clock = make_world(orange=False, grey=False)

    def item(self, kind, variant=None):
        return [t for t in self.world.of(kind) if variant is None or getattr(t, "variant", None) == variant][0]

    def test_the_scarecrow_looks_surprised_then_settles(self):
        scarecrow = self.item("prop", "scarecrow")
        scarecrow.click()
        self.assertEqual(scarecrow.anim.name, "scarecrow_surprised")
        run(self.world, self.clock, 2)
        self.assertEqual(scarecrow.anim.name, "scarecrow")

    def test_a_ripe_pumpkin_wilts_and_a_sprout_grows_back(self):
        self.clock[0] += datetime.timedelta(hours=2)
        run(self.world, self.clock, 0.1)
        pumpkin = self.world.of("pumpkin")[0]
        pumpkin.click()
        self.assertTrue(pumpkin.anim.name.startswith("pumpkin_wilt_"))
        run(self.world, self.clock, 2)
        self.assertEqual(pumpkin.stage, 0)
        self.assertEqual(pumpkin.record["planted"], pumpkin.planted)

    def test_ripe_corn_drops_a_cob_from_every_stalk(self):
        self.clock[0] += datetime.timedelta(hours=1)
        run(self.world, self.clock, 0.1)
        corn = self.item("corn")
        corn.click()
        run(self.world, self.clock, 3)
        self.assertEqual(self.item("corn").stage, 0)
        cobs = [a for a in self.world.of("acorn") if a.anim.name == "corncob"]
        self.assertEqual(len(cobs), len(corn.STALKS))
        self.assertTrue(all(c.on_ground for c in cobs))

    def test_the_barrels_fall_over_vanish_and_come_back(self):
        barrels = self.item("climb", "barrels")
        barrels.click()
        run(self.world, self.clock, 4)
        self.assertEqual(barrels.state, "away")
        self.assertFalse(barrels.available)
        run(self.world, self.clock, 30)
        self.assertEqual(barrels.state, "standing")
        self.assertEqual(barrels.alpha, 1.0)

    def test_the_haystack_rebuilds_in_another_shape(self):
        hay = self.item("climb", "haystack")
        before = hay.layout
        hay.click()
        self.assertNotEqual(hay.layout, before)
        self.assertTrue(self.world.of("straw"))
        self.assertEqual(self.world.settings["items"]["haystack"]["layout"], hay.layout)

    def test_knocking_on_an_empty_den_brings_out_a_frog_that_ribbits_and_leaves(self):
        self.world.den().click()
        self.assertEqual(len(self.world.of("frog")), 1)
        ribbited = False
        for _ in range(40 * 30):
            run(self.world, self.clock, 1 / 30)
            ribbited = ribbited or bool(self.world.of("bubble"))
        self.assertTrue(ribbited)
        self.assertFalse(self.world.of("frog"))

    def test_shaking_the_oak_brings_down_leaves(self):
        self.item("tree").click()
        self.assertGreaterEqual(len(self.world.of("leaf")), 8)


class FoxesTogether(unittest.TestCase):
    def test_a_lone_fox_has_no_social_options(self):
        world, _ = make_world(orange=True, grey=False)
        self.assertEqual(world.of("fox")[0]._social_options(), [])

    def test_two_foxes_greet_with_a_boop(self):
        world, clock = make_world()
        a, b = world.of("fox")
        a.x, b.x = 800.0, 1100.0
        world.greet(a, b)
        booped = set()
        for _ in range(20 * 30):
            run(world, clock, 1 / 30)
            for f in (a, b):
                if f.step is not None and f.step.anim == "boop":
                    booped.add(f.palette)
        self.assertEqual(booped, {"orange", "grey"})
        self.assertIsNone(a.busy_with)

    def test_grooming_and_tagging_along_bring_them_together(self):
        for action in ("groom_friend", "tag_along"):
            world, clock = make_world(seed=6)
            a, b = world.of("fox")
            a.x, b.x = 700.0, 1200.0
            getattr(world, action)(a, b)
            closest = abs(a.x - b.x)
            for _ in range(30 * 30):
                run(world, clock, 1 / 30)
                closest = min(closest, abs(a.x - b.x))
            self.assertLess(closest, 60 * world.scale, action)  # they came together

    def test_a_sleepy_fox_snuggles_up_to_a_sleeping_friend(self):
        world, clock = make_world(hour=23)
        world.settings["items"]["den"]["out"] = False
        world.rebuild()
        a, b = world.of("fox")
        b.do(Step("sleep", 9999))
        run(world, clock, 0.1)  # the friend has settled down to sleep
        a.energy = 0.1
        a.plan.clear()
        a.step = None
        run(world, clock, 60)
        self.assertTrue(a.asleep)
        self.assertLess(abs(a.x - b.x), 50 * world.scale)

    def test_foxes_watch_a_friend_with_the_zoomies(self):
        world, clock = make_world(seed=2)
        a, b = world.of("fox")
        a.do(Step("idle", 999))  # sitting quietly, so it doesn't go and greet the other first
        b.do(*b._zoomies())
        run(world, clock, 1.5)
        self.assertIs(world.friend_showing_off(a), b)
        world.watch_friend(a, b)
        self.assertEqual(a.plan[0].anim, "watch")


class Chewing(unittest.TestCase):
    def test_a_fox_can_chew_up_its_dug_up_icon(self):
        world, clock = make_world(orange=True, grey=False)
        world.taskbar_spots = [700.0]
        fox = world.of("fox")[0]
        world._after_treasure = lambda: [Step("sniff"), Step("chew", 5.0), Step("happy", 1.0)]  # it decides to chew
        world.dig_for_treasure(fox)
        smallest, crumbs = None, False
        for _ in range(60 * 30):
            run(world, clock, 1 / 30)
            treasure = world.of("treasure")
            if treasure:
                smallest = treasure[0].rect()[2]
            crumbs = crumbs or bool(world.of("crumb"))
        self.assertTrue(crumbs)
        self.assertFalse(world.of("treasure"))  # all gone
        self.assertLess(smallest, 12 * world.scale)


class FoxesAndNewThings(unittest.TestCase):
    def test_a_fox_pounces_at_a_low_butterfly_and_it_gets_away(self):
        from pet.visitors import Butterfly
        world, clock = season_world("spring", orange=True)
        fox = world.of("fox")[0]
        fox.plan.clear()
        bug = world.add(Butterfly(world, fox.x + 90, world.ground - 30))
        bug.state = "flutter"
        self.assertIs(world.floater_near(fox), bug)
        before = bug.y
        world.chase_floater(fox, bug)
        self.assertEqual(fox.plan[1].anim, "pounce")
        fox.plan[1].then()  # the moment it lands
        self.assertLess(bug.y, before)  # up out of reach

    def test_floaters_up_high_are_left_alone(self):
        from pet.items import Fluff
        world, _ = season_world("spring", orange=True)
        fox = world.of("fox")[0]
        world.add(Fluff(world, fox.x + 40, world.ground - 300))
        self.assertIsNone(world.floater_near(fox))

    def test_a_fox_nibbles_a_tomato_yum(self):
        from pet.items import Produce
        world, clock = season_world("summer", orange=True)
        fox = world.of("fox")[0]
        fox.plan.clear()
        food = world.add(Produce(world, fox.x + 100, world.ground, "tomato", "apple_bit"))
        food.on_ground = True
        self.assertIs(world.produce_near(fox, 600), food)
        world.nibble(fox, food)
        self.assertTrue(food.taken)  # nobody else gets it
        self.assertIsNone(world.produce_near(fox, 600))
        for _ in range(8 * 30):
            run(world, clock, 1 / 30)
            if food.gone:
                break
        self.assertTrue(food.gone)
        self.assertTrue(any(b.anim.name == "yum_bubble" for b in world.of("bubble")))

    def test_a_radish_is_bleh(self):
        from pet.items import Produce
        world, clock = season_world("spring", orange=True)
        fox = world.of("fox")[0]
        fox.plan.clear()
        food = world.add(Produce(world, fox.x + 100, world.ground, "radish", "leaf_bit"))
        food.on_ground = True
        world.nibble(fox, food)
        for _ in range(8 * 30):
            run(world, clock, 1 / 30)
            if food.gone:
                break
        self.assertTrue(food.gone)
        self.assertTrue(any(b.anim.name == "bleh_bubble" for b in world.of("bubble")))

    def test_every_third_daytime_nap_is_under_the_birch(self):
        world, _ = season_world("summer", orange=True)
        fox = world.of("fox")[0]
        birch = world.of("birch")[0]
        spots = [world.nap_spot(fox) for _ in range(6)]
        self.assertEqual(spots[2], birch.x + 14 * world.scale)
        self.assertEqual(spots[5], birch.x + 14 * world.scale)
        self.assertNotEqual(spots[0], spots[2])

    def test_paw_prints_in_the_snow(self):
        world, clock = season_world("winter", orange=True)
        world.settings["snow"] = True
        fox = world.of("fox")[0]
        fox.plan.clear()
        fox.do(Step("trot", to_x=fox.x + 300, speed=90))
        run(world, clock, 4)
        prints = world.of("print")
        self.assertGreater(len(prints), 5)
        world.settings["snow"] = False  # it melts, and so do the prints
        run(world, clock, 0.2)
        self.assertFalse(world.of("print"))

    def test_no_paw_prints_without_snow(self):
        world, clock = season_world("autumn", orange=True)
        fox = world.of("fox")[0]
        fox.plan.clear()
        fox.do(Step("trot", to_x=fox.x + 300, speed=90))
        run(world, clock, 4)
        self.assertFalse(world.of("print"))


if __name__ == "__main__":
    unittest.main()
