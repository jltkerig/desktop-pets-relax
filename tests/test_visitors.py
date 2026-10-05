"""Visitors: squirrels, geese, turkeys, crows (and the scarecrow)."""
import datetime
import unittest

from helpers import crows_with_scarecrow, make_world, run  # first: sets up a scratch user-data folder
from pet import seasons
from pet.fox import Step
from pet.items import Acorn


class Visitors(unittest.TestCase):
    def test_the_squirrel_needs_an_acorn_on_the_ground_and_buries_it(self):
        world, clock = make_world(orange=False, grey=False)
        self.assertIsNone(world.invite_visitor("squirrel"))
        acorn = world.add(Acorn(world, 900, world.ground))
        acorn.on_ground = True
        squirrel = world.invite_visitor("squirrel")
        self.assertIsNotNone(squirrel)
        run(world, clock, 40)
        self.assertTrue(acorn.gone)
        self.assertTrue(world.of("mound"))
        self.assertTrue(squirrel.gone)

    def test_the_jay_needs_the_oak(self):
        world, _ = make_world("autumn")
        self.assertIsNotNone(world.invite_visitor("jay"))
        world.settings["items"]["oak"]["out"] = False
        world.rebuild()
        self.assertIsNone(world.invite_visitor("jay"))

    def test_the_caterpillar_crosses_and_leaves(self):
        world, clock = make_world(orange=False, grey=False)
        woolly = world.invite_visitor("woolly")
        run(world, clock, 1920 / (woolly.SPEED * world.scale) + 20, fps=10)
        self.assertTrue(woolly.gone)


class Geese(unittest.TestCase):
    def test_a_v_of_geese_flies_south_right_to_left_and_leaves(self):
        world, clock = make_world(orange=False, grey=False)
        world.invite_visitor("migrants")
        flock = world.of("migrant")
        self.assertIn(len(flock), (5, 7, 9))
        start = [g.x for g in flock]
        run(world, clock, 3)
        self.assertTrue(all(g.x < x for g, x in zip(flock, start)))
        run(world, clock, 200, fps=10)
        self.assertFalse(world.of("migrant"))

    def test_geese_land_honk_at_the_foxes_and_fly_on(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.do(Step("idle", 999))
        world.invite_visitor("geese")
        honked = reacted = False
        for _ in range(200 * 30):  # a long visit
            run(world, clock, 1 / 30)
            honked = honked or bool(world.of("bubble"))
            reacted = reacted or (fox.step is not None and fox.step.anim in ("tilt", "hop"))
        self.assertTrue(honked)
        self.assertTrue(reacted)
        self.assertFalse(world.of("goose"))  # they flew on


class SquirrelAndCob(unittest.TestCase):
    def test_squirrels_prefer_acorns_to_corn_cobs(self):
        from pet.items import CornCob
        picks = []
        for seed in range(40):
            world, clock = make_world(orange=False, grey=False, seed=seed)
            for thing in (Acorn(world, 600, world.ground), CornCob(world, 900, world.ground)):
                thing.on_ground = True
                world.add(thing)
            squirrel = world.invite_visitor("squirrel")
            picks.append(getattr(squirrel.acorn, "is_cob", False))
        self.assertGreater(picks.count(False), 28)  # mostly acorns
        self.assertGreater(picks.count(True), 0)    # but a cob now and then

    def test_a_fox_chases_the_squirrel_that_took_the_cob_and_gets_it_back(self):
        from pet.items import CornCob
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.do(Step("idle", 999))
        cob = CornCob(world, fox.x + 300, world.ground)
        cob.on_ground = True
        world.add(cob)
        squirrel = world.add(__import__("pet.visitors", fromlist=["Squirrel"]).Squirrel(world, cob))
        chased = False
        for _ in range(40 * 30):
            run(world, clock, 1 / 30)
            chased = chased or (fox.step is not None and fox.step.follow is squirrel)
        self.assertTrue(chased)
        self.assertFalse(cob.gone)       # not buried: the squirrel dropped it
        self.assertEqual(cob.alpha, 1.0)
        self.assertFalse(cob.carried)


class Turkeys(unittest.TestCase):
    def test_turkeys_come_in_threes_or_more_stop_to_look_and_gobble_then_run_off(self):
        world, clock = make_world(orange=False, grey=False)
        flock = world.invite_visitor("turkeys").flock
        self.assertGreaterEqual(len(world.of("turkey")), 3)
        self.assertIsNone(world.invite_visitor("turkeys"))  # one flock at a time
        stopped = gobbled = False
        for _ in range(240 * 10):
            run(world, clock, 0.1, fps=10)
            stopped = stopped or flock.state == "stop"
            gobbled = gobbled or any(b.anim.name == "gobble_bubble" for b in world.of("bubble"))
            if not world.of("turkey"):
                break
        self.assertTrue(stopped)
        self.assertTrue(gobbled)
        self.assertFalse(world.of("turkey"))

    def test_a_flock_is_mostly_hens_with_a_tom_or_two(self):
        for seed in range(12):
            world, clock = make_world(orange=False, grey=False, seed=seed)
            world.invite_visitor("turkeys")
            turkeys = world.of("turkey")
            hens = [t for t in turkeys if t.hen]
            self.assertGreaterEqual(len(turkeys) - len(hens), 1)  # at least one tom
            self.assertGreaterEqual(len(hens), len(turkeys) - len(turkeys) // 3)
            self.assertTrue(all(t.anim.name.startswith("turkey_hen_") for t in hens))

    def test_hens_cluck_and_toms_gobble(self):
        world, clock = make_world(orange=False, grey=False)
        world.invite_visitor("turkeys")
        hen = next(t for t in world.of("turkey") if t.hen)
        tom = next(t for t in world.of("turkey") if not t.hen)
        hen.gobble(answering=True)
        tom.gobble(answering=True)
        bubbles = {b.goose: b.anim.name for b in world.of("bubble")}
        self.assertEqual(bubbles[hen], "cluck_bubble")
        self.assertEqual(bubbles[tom], "gobble_bubble")
        self.assertEqual(hen.anim.name, "turkey_hen_call")

    def test_turkeys_are_an_autumn_visitor(self):
        self.assertIn("turkeys", seasons.VISITORS["autumn"])
        self.assertNotIn("turkeys", seasons.VISITORS["winter"])


class Crows(unittest.TestCase):
    def test_crows_come_in_pairs_or_more_and_land_near_each_other(self):
        for seed in range(6):
            world, clock = make_world(seed=seed, orange=False, grey=False)
            world.invite_visitor("crows")
            crows = world.of("crow")
            self.assertGreaterEqual(len(crows), 2)
            run(world, clock, 15, fps=20)
            sitting = [c for c in crows if c.state == "sit"]
            if len(sitting) >= 2:
                xs = [c.x for c in sitting]
                self.assertLess(max(xs) - min(xs), 400 * world.scale)

    def test_crows_land_in_the_oak_on_items_and_on_the_ground(self):
        from pet.visitors import CrowParty
        where = set()
        for seed in range(20):
            world, _ = make_world(seed=seed, orange=False, grey=False)
            for spot in CrowParty(world, 3).spots:
                where.add(spot.holder.kind if spot.holder else "ground")
        self.assertIn("tree", where)
        self.assertIn("ground", where)
        self.assertTrue(where & {"prop", "climb", "den", "pumpkin"})

    def test_crows_that_stay_a_while_look_at_things_and_play_with_them(self):
        played = False
        for seed in range(10):
            world, clock = make_world(seed=seed, orange=False, grey=False)
            for x in (800, 950, 1100):
                world.add(Acorn(world, x, world.ground)).on_ground = True
            party = world.invite_visitor("crows").party
            if not party.long:
                continue
            states = set()
            for _ in range(320 * 10):
                run(world, clock, 0.1, fps=10)
                states |= {c.state for c in world.of("crow")}
                if not world.of("crow"):
                    break
            played = played or {"inspect", "play"} <= states
            self.assertFalse(world.of("crow"))
            self.assertTrue(all(a.alpha == 1 and not a.taken for a in world.nuts()))  # no acorn left in a beak
        self.assertTrue(played)

    def test_a_click_sends_the_whole_party_off(self):
        world, clock = make_world(orange=False, grey=False)
        world.invite_visitor("crows")
        run(world, clock, 15, fps=20)
        world.of("crow")[0].click()
        self.assertTrue(all(c.state == "leave" for c in world.of("crow")))
        run(world, clock, 30, fps=20)
        self.assertFalse(world.of("crow"))

    def test_crows_are_about_all_year(self):
        for season in seasons.SEASONS:
            self.assertIn("crows", seasons.VISITORS[season])
        world, _ = make_world("winter", orange=False, grey=False)
        self.assertIsNotNone(world.invite_visitor("crows"))


class CrowsAndTheScarecrow(unittest.TestCase):
    def test_a_crow_pinches_the_hat_wears_it_and_puts_it_back(self):
        world, clock, scarecrow, party = crows_with_scarecrow()
        party.members[0]._go_for_hat(scarecrow)
        wore = hatless = False
        for _ in range(90 * 10):
            run(world, clock, 0.1, fps=10)  # (another crow may beat it to the hat: any crow will do)
            wore = wore or any(c.hat and c.anim.name.startswith("crow_hat_") for c in party.members)
            hatless = hatless or (not scarecrow.hat_on and scarecrow.anim.name.endswith("_nohat"))
            if wore and scarecrow.hat_on:
                break
        self.assertTrue(wore)
        self.assertTrue(hatless)
        self.assertTrue(scarecrow.hat_on)
        self.assertFalse(any(c.hat for c in party.members))

    def test_crows_put_the_hat_back_before_they_leave(self):
        world, clock, scarecrow, party = crows_with_scarecrow(seed=2)
        party.members[0]._go_for_hat(scarecrow)
        for _ in range(200):
            run(world, clock, 0.1, fps=10)
            if party.hat_taken():
                break
        self.assertTrue(party.hat_taken())
        party.stay = 0  # time to go
        run(world, clock, 60, fps=10)
        self.assertFalse(world.of("crow"))
        self.assertTrue(scarecrow.hat_on)

    def test_a_startled_crow_drops_the_hat_and_a_click_puts_it_back(self):
        world, clock, scarecrow, party = crows_with_scarecrow(seed=3)
        thief = party.members[0]
        thief._go_for_hat(scarecrow)
        for _ in range(200):
            run(world, clock, 0.1, fps=10)
            if thief.hat:
                break
        thief.click()  # shoo!
        run(world, clock, 5, fps=10)
        hats = world.of("hat")
        self.assertEqual(len(hats), 1)
        self.assertFalse(scarecrow.hat_on)
        self.assertEqual(hats[0].y, world.ground)  # floated down
        hats[0].click()
        self.assertTrue(scarecrow.hat_on)
        self.assertFalse(world.of("hat"))

    def test_crows_land_on_the_scarecrow_more_than_anywhere(self):
        import collections
        from pet.visitors import CrowParty
        landed = collections.Counter()  # the first crow's spot, by what it's on (the ground is many spots)
        for seed in range(200):
            world, _ = make_world(seed=seed, orange=False, grey=False)
            holder = CrowParty(world, 2).spots[0].holder
            if holder is not None:
                landed[getattr(holder, "variant", holder.kind)] += 1
        self.assertEqual(landed.most_common(1)[0][0], "scarecrow", landed)


class CrowsTalking(unittest.TestCase):
    def test_crows_answer_each_other(self):
        world, clock, _, party = crows_with_scarecrow(seed=4)
        speakers = set()
        for _ in range(60 * 10):
            run(world, clock, 0.1, fps=10)
            speakers |= {b.goose for b in world.of("bubble")}
            if len(speakers) >= 2:
                break
        self.assertGreaterEqual(len(speakers), 2)

    def test_crows_stay_a_good_while(self):
        from pet.visitors import CrowParty
        world, _ = make_world(orange=False, grey=False)
        stays = [CrowParty(world, 2).stay for _ in range(40)]
        self.assertGreaterEqual(min(stays), 35)
        self.assertGreater(max(stays), 120)


class CrowsAndCorn(unittest.TestCase):
    def test_corn_on_the_ground_brings_the_crows(self):
        from pet.items import CornCob
        crows = 0
        for seed in range(20):
            world, _ = make_world(seed=seed, orange=False, grey=False)
            world.add(CornCob(world, 900, world.ground)).on_ground = True
            world.invite_visitor()
            crows += bool(world.of("crow"))
        self.assertGreaterEqual(crows, 12)  # usually around 16 of 20

    def test_harvesting_corn_soon_brings_the_crows(self):
        world, clock = make_world(orange=False, grey=False)
        clock[0] += datetime.timedelta(hours=1)
        run(world, clock, 0.1)
        world.harvest(world.of("corn")[0])
        self.assertLessEqual(world.timers["visitor"], 25)

    def test_crows_peck_the_kernels_off_a_cob(self):
        from pet.items import CornCob
        world, clock = make_world(seed=5, orange=False, grey=False)
        cob = world.add(CornCob(world, 900, world.ground))
        cob.on_ground = True
        party = world.invite_visitor("crows").party
        party.long, party.stay = True, 10 ** 6
        run(world, clock, 90, fps=10)
        # the cob, or any apple they've knocked out of the apple barrel to peck at instead
        self.assertGreater(sum(getattr(a, "kernels", 0) for a in world.of("acorn")), 0)

    def test_corn_cobs_dont_stop_acorns_falling(self):
        from pet.items import CornCob
        world, _ = make_world(orange=False, grey=False)
        for i in range(6):
            world.add(CornCob(world, 300 + i * 40, world.ground)).on_ground = True
        self.assertEqual(world.nuts(), [])


if __name__ == "__main__":
    unittest.main()
