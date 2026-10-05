"""Growing and harvesting: pumpkins (and decorating with them), corn and cobs, the vegetable garden,
the den and hoe, and the newer yard items."""
import datetime
import json
import os
import random
import unittest
from pathlib import Path

from helpers import item, make_world, run, season_world  # first: sets up a scratch user-data folder
from pet import save, seasons, sprites
from pet.fox import Step
from pet.world import World


class Pumpkins(unittest.TestCase):
    def test_pumpkins_grow_from_sprout_to_ripe_and_stop(self):
        world, clock = make_world(orange=False, grey=False)
        pumpkins = world.of("pumpkin")
        self.assertEqual(len(pumpkins), 3)
        self.assertTrue(all(p.stage == 0 for p in pumpkins))
        first = pumpkins[0]
        seen = set()
        for _ in range(12):
            clock[0] += datetime.timedelta(minutes=10)
            world.update(0.1)
            seen.add(first.stage)
        self.assertTrue({1, 2, 3, 4} <= seen, seen)
        self.assertTrue(first.ripe)
        self.assertTrue(first.anim.name.startswith(f"pumpkin_4_{first.size}_{first.shape}"))

    def test_the_patch_keeps_growing_after_a_restart(self):
        world, clock = make_world(orange=False, grey=False)
        planted = sorted(p["planted"] for p in world.settings["items"]["pumpkins"]["patch"])
        self.assertTrue(world.dirty)  # new sprouts get saved
        again = World(1920, 1040, world.settings, rng=random.Random(5), clock=lambda: clock[0])
        self.assertEqual(sorted(p.planted for p in again.of("pumpkin")), planted)

    def test_replanting_starts_new_sprouts(self):
        world, clock = make_world(orange=False, grey=False)
        clock[0] += datetime.timedelta(hours=2)
        world.update(0.1)
        self.assertTrue(all(p.ripe for p in world.of("pumpkin")))
        world.grow_pumpkins(replant=True)
        world.update(0.1)
        self.assertTrue(all(p.stage == 0 for p in world.of("pumpkin")))
        self.assertEqual(len(world.of("pumpkin")), 3)

    def test_pumpkins_are_autumn_only(self):
        world, _ = make_world("winter")
        self.assertFalse(world.of("pumpkin"))


class Field(unittest.TestCase):
    def test_new_pumpkins_come_in_three_sizes(self):
        world, _ = make_world(orange=False, grey=False)
        self.assertEqual(sorted(p.size for p in world.of("pumpkin")), ["l", "m", "s"])

    def test_the_scarecrow_stands_next_to_the_pumpkin_patch(self):
        world, _ = make_world(orange=False, grey=False)
        scarecrow = [t for t in world.of("prop") if t.variant == "scarecrow"]
        self.assertEqual(len(scarecrow), 1)
        rightmost = max(p.x for p in world.of("pumpkin"))
        self.assertTrue(0 < scarecrow[0].x - rightmost <= 80 * world.scale)
        world.settings["season"] = "spring"
        world.rebuild()
        self.assertFalse([t for t in world.of("prop") if t.variant == "scarecrow"])  # autumn only

    def test_a_fox_chases_and_catches_a_falling_leaf(self):
        from pet.items import Leaf
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.do(Step("idle", 999))
        leaf = world.add(Leaf(world, fox.x + 150, world.ground - 150, "red"))
        leaf.sway = 0  # straight down, to keep the test simple
        world.chase_leaf(fox, leaf)
        pounced = False
        for _ in range(8 * 30):
            run(world, clock, 1 / 30)
            pounced = pounced or (fox.step is not None and fox.step.anim == "pounce")
        self.assertTrue(pounced)
        self.assertTrue(leaf.gone)  # caught under its paws


class CornField(unittest.TestCase):
    def test_corn_grows_through_five_stages_and_keeps_its_planting_time(self):
        world, clock = make_world(orange=False, grey=False)
        field = world.of("corn")
        self.assertEqual(len(field), 1)
        corn = field[0]
        seen = set()
        for _ in range(10):
            world.update(0.1)
            seen.add(corn.anim.name)
            clock[0] += datetime.timedelta(minutes=10)
        self.assertEqual(seen, {f"corn_{s}" for s in range(5)})
        planted = world.settings["items"]["corn"]["planted"]
        again = World(1920, 1040, world.settings, rng=random.Random(9), clock=lambda: clock[0])
        self.assertEqual(again.of("corn")[0].planted, planted)


class DenAndHoe(unittest.TestCase):
    def test_a_sleepy_fox_curls_up_in_the_den_and_comes_out_when_it_wakes(self):
        world, clock = make_world(orange=True, grey=False, hour=23)
        fox = world.of("fox")[0]
        den = world.den()
        self.assertIsNotNone(den)
        fox.energy = 0.1
        fox.plan.clear()
        fox.step = None
        run(world, clock, 40)
        self.assertTrue(fox.in_den)
        self.assertEqual(den.anim.name, "den_orange")
        self.assertTrue(world.of("zzz"))
        self.assertFalse(fox.contains(fox.x, fox.y - 10))  # hidden inside
        fox.poke()
        self.assertFalse(fox.in_den)
        self.assertEqual(fox.alpha, 1.0)

    def test_the_hoe_leans_by_the_pumpkins(self):
        world, _ = make_world(orange=False, grey=False)
        hoe = [t for t in world.of("prop") if t.variant == "hoe"][0]
        leftmost = min(p.x for p in world.of("pumpkin"))
        self.assertTrue(0 < leftmost - hoe.x <= 40 * world.scale)

    def test_the_den_stays_out_all_year(self):
        for season in ("winter", "spring", "summer", "autumn"):
            world, _ = make_world(season, orange=False, grey=False)
            self.assertIsNotNone(world.den(), season)


class BigPumpkinsAndTheHoe(unittest.TestCase):
    def setUp(self):
        self.world, self.clock = make_world(orange=False, grey=False)
        self.pumpkin = self.world.of("pumpkin")[0]
        self.hoe = next(p for p in self.world.of("prop") if p.variant == "hoe")

    def ripen(self, minutes=45):
        self.clock[0] += datetime.timedelta(minutes=minutes * self.pumpkin.pace)
        run(self.world, self.clock, 0.1)

    def test_a_giant_pumpkin_grows_too_big_and_bursts_then_starts_again(self):
        self.pumpkin.giant, self.pumpkin.jack = True, False
        self.ripen(55)
        self.assertTrue(self.pumpkin.huge)
        self.assertTrue(self.pumpkin.anim.name.startswith("pumpkin_giant_"))
        self.ripen(10)
        self.assertTrue(self.pumpkin.bursting)
        self.assertTrue(self.world.of("crumb"))  # bits and seeds flying
        run(self.world, self.clock, 3)
        self.assertFalse(self.pumpkin.bursting)
        self.assertEqual(self.pumpkin.stage, 0)  # a fresh sprout

    def test_most_pumpkins_stop_at_ripe(self):
        self.pumpkin.giant = False
        self.ripen(120)
        self.assertEqual(self.pumpkin.stage, 4)

    def test_dropping_the_hoe_on_a_ripe_pumpkin_carves_a_jack_o_lantern(self):
        self.pumpkin.jack, self.pumpkin.giant = False, False
        self.ripen()
        self.hoe.x = self.pumpkin.x + 5
        self.world.dropped(self.hoe)
        run(self.world, self.clock, 0.1)
        self.assertTrue(self.pumpkin.jack)
        self.assertTrue(self.pumpkin.record["jack"])
        self.assertTrue(self.pumpkin.anim.name.endswith("_jack"))
        self.assertEqual(self.hoe.anim.name, "hoe_wobble")

    def test_the_hoe_does_nothing_to_an_unripe_pumpkin(self):
        self.pumpkin.jack = False
        self.hoe.x = self.pumpkin.x
        self.world.dropped(self.hoe)
        self.assertFalse(self.pumpkin.jack)

    def test_a_carved_giant_stays_a_giant_jack_o_lantern(self):
        self.pumpkin.giant, self.pumpkin.jack = True, False
        self.ripen(55)
        self.assertTrue(self.pumpkin.carve())
        self.ripen(60)
        run(self.world, self.clock, 0.1)
        self.assertFalse(self.pumpkin.bursting)
        self.assertTrue(self.pumpkin.anim.name.startswith("pumpkin_giant_") and self.pumpkin.anim.name.endswith("_jack"))


class DenSnouts(unittest.TestCase):
    def test_sleeping_foxes_show_their_snouts_in_the_doorway(self):
        from PIL import Image
        empty = Image.open(sprites.SPRITE_DIR / "den.png").convert("RGBA")
        full = Image.open(sprites.SPRITE_DIR / "den_orange.png").convert("RGBA")
        changed = [(x, y) for x in range(empty.width) for y in range(empty.height)
                   if empty.getpixel((x, y)) != full.getpixel((x, y))]
        self.assertTrue(changed)
        self.assertTrue(all(y >= 37 for _, y in changed))  # in the doorway, ears below the stone over it
        self.assertTrue(any(y <= 40 for _, y in changed))  # ears standing up
        self.assertTrue(any(y >= 52 for _, y in changed))  # chin on its paws on the ground

    def test_the_den_is_snowed_over_when_the_oak_is(self):
        world, clock = make_world("winter", orange=False, grey=False)
        world.settings["snow"] = True
        run(world, clock, 0.1)
        self.assertEqual(world.den().anim.name, "den_snow")
        world.settings["snow"] = False
        run(world, clock, 0.1)
        self.assertEqual(world.den().anim.name, "den")
        world.settings["season"] = "autumn"
        world.settings["snow"] = True  # snow only ever lies in winter
        run(world, clock, 0.1)
        self.assertEqual(world.den().anim.name, "den")


class CornCobInHand(unittest.TestCase):
    def test_a_cob_can_be_picked_up_and_dropped_somewhere_else(self):
        from pet.items import CornCob
        world, clock = season_world("autumn")
        cob = world.add(CornCob(world, 500, world.ground))
        cob.on_ground = True
        self.assertTrue(cob.draggable)
        cob.pick_up()
        cob.x, cob.y = 1200.0, world.ground - 300  # carried across, up in the air
        run(world, clock, 1)
        self.assertEqual((cob.x, cob.y), (1200.0, world.ground - 300))  # it stays in your hand
        cob.drop()
        run(world, clock, 3)
        self.assertTrue(cob.on_ground)
        self.assertEqual(cob.y, world.ground)
        self.assertFalse(cob.taken)

    def test_a_cob_in_a_squirrels_arms_cant_be_grabbed(self):
        from pet.items import CornCob
        world, _ = season_world("autumn")
        cob = world.add(CornCob(world, 500, world.ground))
        cob.taken = True  # a squirrel is on its way to it: you can still snatch it
        self.assertTrue(cob.draggable)
        cob.carried = True  # in its arms: no
        self.assertFalse(cob.draggable)

    def test_snatching_a_cob_from_a_squirrel_sends_it_off(self):
        from pet.items import CornCob
        from pet.visitors import Squirrel
        world, clock = season_world("autumn")
        cob = world.add(CornCob(world, 900, world.ground))
        cob.on_ground = True
        squirrel = world.add(Squirrel(world, cob))
        cob.pick_up()
        run(world, clock, 0.2)
        self.assertEqual(squirrel.state, "leave")

    def test_a_thrown_cob_flies_and_a_fox_chases_it(self):
        from pet.items import CornCob
        world, clock = season_world("autumn", orange=True)
        fox = world.of("fox")[0]
        cob = world.add(CornCob(world, 500, world.ground - 100))
        cob.pick_up()
        cob.throw(600, -300)
        self.assertFalse(cob.held)
        self.assertEqual(fox.step.anim if fox.step else fox.plan[0].anim, "tilt")
        batted = False
        for _ in range(30 * 12):
            run(world, clock, 1 / 30)
            batted = batted or (fox.step is not None and fox.step.anim == "bat")
        self.assertGreater(cob.x, 560)
        self.assertTrue(batted)

    def test_a_gentle_drop_doesnt_send_a_fox(self):
        from pet.items import CornCob
        world, clock = season_world("autumn", orange=True)
        fox = world.of("fox")[0]
        fox.plan.clear()
        fox.step = None
        cob = world.add(CornCob(world, 500, world.ground - 50))
        cob.pick_up()
        cob.drop()
        self.assertFalse(fox.plan)


class DecoratingPumpkins(unittest.TestCase):
    def world(self):
        world, clock = season_world("autumn")
        return world, clock

    def test_add_a_pumpkin_and_it_drops_onto_the_ground(self):
        world, clock = self.world()
        deco = world.add_deco()
        run(world, clock, 2)
        self.assertEqual(deco.y, world.ground)
        self.assertTrue(deco.anim.name.startswith("pumpkin_4_"))
        self.assertEqual(len(world.settings["decorations"]), 1)

    def test_put_one_on_the_haystack_and_it_moves_with_it(self):
        world, clock = self.world()
        hay = next(c for c in world.of("climb") if c.variant == "haystack")
        deco = world.add_deco()
        deco.pick_up()
        dx, h = hay.levels[-1]
        deco.x, deco.y = hay.x + dx * world.scale, hay.y - (h + 30) * world.scale  # let go above the top
        deco.drop()
        run(world, clock, 2)
        self.assertIs(deco.holder, hay)
        self.assertEqual(deco.y, hay.y - h * world.scale)
        self.assertEqual(world.settings["decorations"][0]["on"], "haystack")
        hay.x += 100
        run(world, clock, 0.1)
        self.assertAlmostEqual(deco.x, hay.x + dx * world.scale, delta=10 * world.scale)

    def test_let_go_under_a_tree_it_sits_on_the_ground(self):
        world, clock = self.world()
        tree = world.tree()
        deco = world.add_deco()
        deco.pick_up()
        deco.x, deco.y = tree.x, world.ground - 200
        deco.drop()
        run(world, clock, 2)
        self.assertIsNone(deco.holder)
        self.assertEqual((deco.x, deco.y), (tree.x, world.ground))

    def test_decorations_come_back_next_time_and_only_in_autumn(self):
        world, clock = self.world()
        hay = next(c for c in world.of("climb") if c.variant == "haystack")
        deco = world.add_deco(jack=True)
        deco.pick_up()
        deco.x, deco.y = hay.x + hay.levels[0][0] * world.scale, world.ground - 200
        deco.drop()
        saved = json.loads(json.dumps(world.settings))
        again = World(1920, 1040, saved, rng=random.Random(1), clock=world.clock)
        decos = again.of("deco")
        self.assertEqual(len(decos), 1)
        self.assertTrue(decos[0].jack)
        self.assertEqual(decos[0].holder.variant, "haystack")
        saved["season"] = "winter"
        self.assertFalse(World(1920, 1040, saved, rng=random.Random(1), clock=world.clock).of("deco"))

    def test_lifting_a_ripe_pumpkin_out_of_the_patch_picks_it(self):
        world, clock = self.world()
        pumpkin = world.of("pumpkin")[0]
        pumpkin.planted = world.now().timestamp() - pumpkin.STAGE_SECONDS * pumpkin.pace * 4.5
        pumpkin.giant = False
        self.assertEqual(pumpkin.stage, 4)
        looks = (pumpkin.size, pumpkin.shape, pumpkin.jack)
        deco = world.pick_pumpkin(pumpkin)
        self.assertIsNotNone(deco)
        self.assertEqual((deco.size, deco.shape, deco.jack), looks)  # the same pumpkin, picked
        self.assertEqual(pumpkin.stage, 0)  # a new sprout where it was
        sprout = world.of("pumpkin")[1]
        self.assertIsNone(world.pick_pumpkin(sprout) if sprout.stage < 4 else None)

    def test_the_hoe_carves_a_decorating_pumpkin_and_it_glows_at_night(self):
        world, clock = self.world()
        deco = world.add_deco(x=300)
        run(world, clock, 2)
        hoe = next(p for p in world.of("prop") if p.variant == "hoe")
        hoe.x = deco.x
        world.dropped(hoe)
        self.assertTrue(deco.jack)
        self.assertTrue(deco.anim.name.endswith("_jack"))
        clock[0] = clock[0].replace(hour=23)
        run(world, clock, 1)
        self.assertTrue(any(g.holder is deco for g in world.of("glow")))

    def test_clear_them_away(self):
        world, clock = self.world()
        world.add_deco()
        world.add_deco()
        world.clear_decos()
        run(world, clock, 0.1)
        self.assertFalse(world.of("deco"))
        self.assertEqual(world.settings["decorations"], [])


class NewItems(unittest.TestCase):
    def test_a_fox_climbs_the_woodstack_in_winter(self):
        world, clock = season_world("winter", orange=True)
        stack = item(world, "woodstack")
        world.settings["snow"] = True
        run(world, clock, 0.1)
        self.assertEqual(stack.anim.name, "woodstack_snow")
        fox = world.of("fox")[0]
        world.climb(fox, stack)
        highest = world.ground
        for _ in range(200):
            run(world, clock, 0.1, fps=10)
            highest = min(highest, fox.y)
        self.assertLessEqual(highest, world.ground - 23 * world.scale)

    def test_clicking_the_apple_barrel_rolls_out_an_apple_but_not_endlessly(self):
        world, clock = season_world("autumn")
        barrel = item(world, "apple_barrel")
        barrel.click()
        apples = [a for a in world.of("acorn") if getattr(a, "produce", "") == "apple"]
        self.assertEqual(len(apples), 1)
        run(world, clock, 3)
        self.assertTrue(apples[0].on_ground)
        for _ in range(20):
            barrel.click()
        self.assertLessEqual(len([a for a in world.of("acorn") if getattr(a, "produce", "") == "apple"]), 6)

    def test_the_wells_bucket_goes_down_and_comes_back(self):
        world, clock = season_world("spring")
        well = item(world, "well")
        well.click()
        self.assertEqual(well.anim.name, "well_bucket")
        run(world, clock, 3)
        self.assertEqual(well.anim.name, "well")

    def test_a_fox_slides_down_the_slide(self):
        world, clock = season_world("summer", orange=True)
        slide = item(world, "slide")
        fox = world.of("fox")[0]
        world.climb(fox, slide)
        highest, slid = world.ground, False
        for _ in range(300):
            run(world, clock, 0.1, fps=10)
            highest = min(highest, fox.y)
            slid = slid or (fox.step is not None and fox.step.anim == "crouch" and fox.x > slide.x + 10 * world.scale
                            and fox.y < world.ground - 5 * world.scale)
        self.assertLessEqual(highest, world.ground - 35 * world.scale)  # up on the platform
        self.assertTrue(slid)                                          # and down the chute
        self.assertEqual(fox.y, world.ground)
        self.assertGreater(fox.x, slide.x)                             # it ends up at the bottom, on the right

    def test_a_fox_splashes_in_the_kiddie_pool(self):
        world, clock = season_world("summer", orange=True)
        pool = item(world, "pool")
        fox = world.of("fox")[0]
        world.paddle(fox, pool)
        splashed = False
        for _ in range(200):
            run(world, clock, 0.1, fps=10)
            splashed = splashed or bool(world.of("drop"))
        self.assertTrue(splashed)
        self.assertEqual(fox.y, world.ground)
        pool.click()
        self.assertEqual(pool.anim.name, "pool_ripple")

    def test_all_the_new_items_are_in_the_toy_box_and_saved(self):
        defaults = save.load(Path(os.environ["PIXELFOX_USER_DIR"]) / "missing.json")["items"]
        for name in ("birch", "woodstack", "apple_barrel", "well", "slide", "pool", "watermelons", "tomatoes",
                     "radishes", "lettuce", "dahlias", "dandelions", "cattails"):
            self.assertIn(name, seasons.ITEMS)
            self.assertIn(name, defaults)


class Garden(unittest.TestCase):
    def grow(self, world, clock, minutes):
        clock[0] += datetime.timedelta(minutes=minutes)
        run(world, clock, 0.1)

    def test_watermelons_grow_like_pumpkins_and_split_open_when_ripe(self):
        world, clock = season_world("summer")
        melons = world.of("melon")
        self.assertEqual(len(melons), 3)
        melon = melons[0]
        self.assertEqual(melon.stage, 0)
        self.grow(world, clock, 60)
        self.assertEqual(melon.stage, 4)
        self.assertTrue(melon.anim.name.startswith("melon_4_"))
        melon.click()
        self.assertTrue(melon.anim.name.startswith("melon_split_"))
        run(world, clock, 2)
        self.assertEqual(melon.stage, 0)  # a new one sown
        self.assertEqual(melon.record["planted"], melon.planted)
        self.assertFalse(melon.carve())   # the hoe's for pumpkins

    def test_ripe_tomatoes_drop_off_the_plants(self):
        world, clock = season_world("summer")
        self.grow(world, clock, 50)
        plants = item(world, "tomatoes")
        self.assertEqual(plants.anim.name, "tomatoes_4")
        plants.click()
        run(world, clock, 3)
        tomatoes = [a for a in world.of("acorn") if getattr(a, "produce", "") == "tomato"]
        self.assertGreaterEqual(len(tomatoes), 3)
        self.assertTrue(all(t.on_ground for t in tomatoes))
        self.assertEqual(item(world, "tomatoes").stage, 0)

    def test_radishes_and_lettuce_pop_out_of_the_ground(self):
        world, clock = season_world("spring")
        self.grow(world, clock, 40)
        for name, produce in (("radishes", "radish"), ("lettuce", "lettuce_head")):
            row = item(world, name)
            self.assertTrue(row.ripe, name)
            row.click()
            popped = [a for a in world.of("acorn") if getattr(a, "produce", "") == produce]
            self.assertTrue(popped, name)
            self.assertTrue(all(p.vy < 0 for p in popped))  # flying up out of the ground
        run(world, clock, 4)
        self.assertTrue(all(a.on_ground for a in world.of("acorn")))

    def test_unripe_crops_just_rustle(self):
        world, _ = season_world("spring")
        item(world, "radishes").click()
        self.assertFalse(world.of("acorn"))

    def test_cattails_burst_into_fluff_that_blows_away(self):
        world, clock = season_world("summer")
        self.grow(world, clock, 35)
        tails = item(world, "cattails")
        self.assertTrue(tails.ripe)
        tails.click()
        fluff = world.of("fluff")
        self.assertGreaterEqual(len(fluff), 30)
        start = sum(f.x for f in fluff) / len(fluff)
        run(world, clock, 4)
        self.assertGreater(abs(sum(f.x for f in world.of("fluff")) / len(world.of("fluff")) - start), 20)  # drifting
        self.assertEqual(item(world, "cattails").stage, 0)
        run(world, clock, 20)
        self.assertFalse(world.of("fluff"))


if __name__ == "__main__":
    unittest.main()
