import datetime
import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["PIXELFOX_USER_DIR"] = tempfile.mkdtemp(prefix="pixelfox-test-")  # never the real user-data

from PIL import Image  # noqa: E402

from pet import save, seasons, sprites  # noqa: E402
from pet.fox import Step  # noqa: E402
from pet.items import Acorn  # noqa: E402
from pet.world import World  # noqa: E402

assert "pixelfox-test-" in str(save.USER_DIR), "tests must never use the real user-data folder"


def make_world(season="autumn", hour=14, seed=3, **foxes):
    settings = save.load(Path(os.environ["PIXELFOX_USER_DIR"]) / "missing.json")
    settings["season"] = season
    if foxes:
        settings["foxes"] = foxes
    clock = [datetime.datetime(2026, 10, 4, hour, 0)]
    world = World(1920, 1040, settings, rng=random.Random(seed), clock=lambda: clock[0])
    world.timers = {"leaf": 10 ** 9, "acorn": 10 ** 9, "visitor": 10 ** 9}  # nothing turns up by itself
    return world, clock


def run(world, clock, seconds, fps=30):
    for _ in range(int(seconds * fps)):
        clock[0] += datetime.timedelta(seconds=1 / fps)
        world.update(1 / fps, (-1000.0, -1000.0))


class Seasons(unittest.TestCase):
    def test_months_map_to_northern_seasons(self):
        self.assertEqual(seasons.season_for(datetime.date(2026, 10, 4)), "autumn")
        self.assertEqual(seasons.season_for(datetime.date(2026, 12, 25)), "winter")
        self.assertEqual(seasons.season_for(datetime.date(2026, 4, 1)), "spring")
        self.assertEqual(seasons.season_for(datetime.date(2026, 7, 4)), "summer")

    def test_the_oak_is_out_in_autumn_only(self):
        world, _ = make_world("autumn")
        self.assertIsNotNone(world.tree())
        world.settings["season"] = "winter"
        world.rebuild()
        self.assertIsNone(world.tree())


class Sprites(unittest.TestCase):
    def test_every_sprite_json_matches_its_png(self):
        names = sorted(p.stem for p in sprites.SPRITE_DIR.glob("*.json"))
        self.assertGreater(len(names), 40)
        for name in names:
            m = sprites.meta(name)
            with Image.open(sprites.SPRITE_DIR / f"{name}.png") as img:
                self.assertEqual(img.size, (m["frame_width"] * m["frames"], m["frame_height"]), name)

    def test_both_foxes_have_every_animation_the_fox_uses(self):
        used = {"idle", "look", "walk", "trot", "stretch", "yawn", "scratch", "sleep", "wake", "tilt", "petted",
                "held", "land", "crouch", "pounce", "dig", "bat", "watch", "happy", "sniff", "playbow", "roll",
                "hop", "boop", "groom", "run", "dive"}
        for palette in ("orange", "grey"):
            for anim in used:
                self.assertTrue(sprites.exists(f"fox_{palette}_{anim}"), f"fox_{palette}_{anim}")

    def test_a_non_looping_animation_finishes_on_its_last_frame(self):
        anim = sprites.Anim("fox_orange_yawn")
        anim.update(sprites.duration("fox_orange_yawn") + 0.01)
        self.assertTrue(anim.done)
        self.assertEqual(anim.frame, sprites.meta("fox_orange_yawn")["frames"] - 1)


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


class Saving(unittest.TestCase):
    def test_round_trip_and_bad_values(self):
        path = Path(os.environ["PIXELFOX_USER_DIR"]) / "world.json"
        data = save.load(path)
        data["items"]["oak"]["x"] = 700
        data["foxes"]["grey"] = False
        save.store(data, path)
        again = save.load(path)
        self.assertEqual(again["items"]["oak"]["x"], 700)
        self.assertFalse(again["foxes"]["grey"])
        path.write_text(json.dumps({"season": "monsoon", "scale": 9, "foxes": "nope"}), encoding="utf-8")
        fixed = save.load(path)
        self.assertEqual((fixed["season"], fixed["scale"]), ("auto", 2))
        self.assertTrue(fixed["foxes"]["orange"])


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


class Treasure(unittest.TestCase):
    def test_a_fox_digs_up_an_icon_runs_off_with_it_and_drops_it(self):
        world, clock = make_world(orange=True, grey=False)
        world.taskbar_spots = [700.0]
        fox = world.of("fox")[0]
        self.assertTrue(world.dig_for_treasure(fox))
        carried = False
        for _ in range(40 * 30):
            run(world, clock, 1 / 30)
            treasure = world.of("treasure")
            carried = carried or bool(treasure and treasure[0].carried_by is fox)
        self.assertTrue(carried)
        self.assertEqual(world.grab_requests[0][1], 700.0)  # the window copies that icon's picture
        self.assertIsNone(world.of("treasure")[0].carried_by)  # dropped after running off
        self.assertIsNone(fox.carrying)

    def test_no_taskbar_icons_means_no_digging(self):
        world, _ = make_world(orange=True, grey=False)
        self.assertFalse(world.dig_for_treasure(world.of("fox")[0]))


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
        self.assertFalse(world.of("prop"))

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

    def test_ripe_corn_is_harvested_into_a_cob(self):
        self.clock[0] += datetime.timedelta(hours=1)
        run(self.world, self.clock, 0.1)
        self.item("corn").click()
        run(self.world, self.clock, 3)
        self.assertEqual(self.item("corn").stage, 0)
        cobs = [a for a in self.world.of("acorn") if a.anim.name == "corncob"]
        self.assertEqual(len(cobs), 1)
        self.assertTrue(cobs[0].on_ground)

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


class Monitors(unittest.TestCase):
    def test_monitors_join_left_to_right_whatever_order_windows_lists_them(self):
        from pet import screens
        slices, width, height = screens.layout([(2560, 0, 1920, 1040), (0, 0, 2560, 1400), (-1280, 200, 1280, 984)])
        self.assertEqual([s["x"] for s in slices], [-1280, 0, 2560])        # left monitor first
        self.assertEqual([s["offset"] for s in slices], [0, 1280, 3840])
        self.assertEqual((width, height), (5760, 1400))
        self.assertEqual(screens.slice_at(slices, 2000)["x"], 0)
        self.assertEqual(screens.slice_at(slices, 99999)["x"], 2560)          # past the end: the last one

    def test_one_monitor_and_stacked_monitors_work_too(self):
        from pet import screens
        self.assertEqual(screens.layout([(0, 0, 1366, 728)])[1:], (1366, 728))
        slices, width, _ = screens.layout([(0, -1080, 1920, 1040), (0, 0, 1920, 1040)])  # one above the other
        self.assertEqual(width, 3840)
        self.assertEqual(screens.layout([])[1:], (0, 0))

    def test_unplugging_a_monitor_keeps_everything_on_screen_and_on_the_ground(self):
        world, clock = make_world()
        fox = world.of("fox")[0]
        fox.x = 1800.0
        world.resize(1280, 700)
        self.assertEqual(world.ground, 698)
        self.assertLessEqual(fox.x, 1280 - 20)
        self.assertTrue(all(t.y <= world.ground for t in world.things))
        run(world, clock, 30)  # and it all carries on
        self.assertEqual(len(world.of("fox")), 2)


class Seams(unittest.TestCase):
    def test_items_never_straddle_two_monitors(self):
        settings = save.load(Path(os.environ["PIXELFOX_USER_DIR"]) / "missing.json")
        settings["season"] = "autumn"
        settings["items"]["den"]["x"] = 2560  # right on the gap
        clock = [datetime.datetime(2026, 10, 4, 14, 0)]
        world = World(5120, 1400, settings, rng=random.Random(1), clock=lambda: clock[0], seams=[2560])
        for thing in world.things:
            if thing.kind in World.ITEM_KINDS:
                left, _, w, _ = thing.rect()
                self.assertFalse(left < 2560 < left + w, thing.kind)
        den = world.den()
        world.set_seams([den.x])  # monitors rearranged so a gap now runs through the den
        left, _, w, _ = den.rect()
        self.assertFalse(left < world.seams[0] < left + w)


if __name__ == "__main__":
    unittest.main()
