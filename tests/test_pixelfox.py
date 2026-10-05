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
from pet import weather  # noqa: E402

REAL_FETCH = weather.fetch
weather.fetch = lambda lat, lon: None  # tests never ask the internet about the weather

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

    def test_the_oak_is_out_all_year_dressed_for_the_season(self):
        looks = {}
        for season in seasons.SEASONS:
            world, _ = make_world(season)
            world.settings["snow"] = False
            self.assertIsNotNone(world.tree(), season)
            looks[season] = world.tree().look
        self.assertEqual(looks, {"autumn": "oak", "winter": "oak_winter", "spring": "oak_spring",
                                 "summer": "oak_summer"})

    def test_the_oak_changes_with_the_season_in_place(self):
        world, clock = make_world("autumn")
        tree = world.tree()
        world.settings["season"] = "summer"
        world.rebuild()
        run(world, clock, 0.1)
        self.assertIs(world.tree(), tree)
        self.assertEqual(tree.anim.name, "oak_summer")


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
                "hop", "boop", "groom", "run", "dive", "doze", "chew"}
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
        world._after_treasure = lambda: [Step("playbow", 1.0), Step("happy", 1.0)]  # it plays with it, no chewing
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


class DayAndNight(unittest.TestCase):
    def test_phases_follow_the_sun(self):
        from pet import daylight
        october = lambda h: datetime.datetime(2026, 10, 4, h, 0)
        self.assertEqual(daylight.phase(october(2)), "night")
        self.assertEqual(daylight.phase(october(13)), "day")
        self.assertEqual(daylight.phase(october(23)), "night")
        self.assertIn(daylight.phase(october(7)), ("dawn", "day", "night"))

    def test_a_location_can_be_set_by_hand(self):
        from pet import daylight
        noon = datetime.datetime(2026, 6, 21, 12, 0)
        here = {"location": {"lat": 39.5, "lon": -76.3}}  # a spot in this computer's own time zone
        self.assertEqual(daylight.phase(noon, here), "day")
        self.assertEqual(daylight.phase(noon.replace(hour=2), here), "night")

    def test_only_the_owl_turns_up_by_itself_at_night(self):
        world, clock = make_world(orange=False, grey=False, hour=23)
        self.assertEqual(world.invite_visitor().kind, "owl")
        self.assertIsNone(world.invite_visitor())                  # just the one owl
        self.assertIsNotNone(world.invite_visitor("woolly"))       # unless you invite someone
        world, clock = make_world(orange=False, grey=False, hour=13)
        for _ in range(20):
            visitor = world.invite_visitor()
            self.assertNotEqual(getattr(visitor, "kind", None), "owl")  # never by itself in the daytime
            for t in world.things:
                if t.kind not in world.ITEM_KINDS and t.kind != "fox":
                    t.gone = True

    def test_foxes_sleep_more_at_night(self):
        def asleep_share(hour):
            world, clock = make_world(seed=4, hour=hour)
            world.settings["items"]["den"]["out"] = False
            world.rebuild()
            slept = total = 0
            for _ in range(20 * 60 * 10):  # twenty minutes, a tenth of a second at a time
                run(world, clock, 0.1, fps=10)
                for fox in world.of("fox"):
                    total += 1
                    slept += fox.asleep or (fox.step is not None and fox.step.anim == "doze")
            return slept / total
        self.assertGreater(asleep_share(23), asleep_share(10))
        self.assertGreater(asleep_share(23), 0.5)


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


class DiscordMischief(unittest.TestCase):
    def setUp(self):
        self.world, self.clock = make_world(orange=True, grey=False)
        self.fox = self.world.of("fox")[0]
        self.world.discord_spot = {"x": 1400.0, "y": 600.0}

    def test_a_message_is_stolen_played_with_and_put_back(self):
        self.assertTrue(self.world.steal_message(self.fox))
        self.assertEqual(self.world.screen_requests, [("steal", "message1")])
        self.world.screen_requests.clear()
        states = set()
        for _ in range(120 * 30):
            run(self.world, self.clock, 1 / 30)
            for msg in self.world.of("message"):
                states.add(msg.state)
        self.assertTrue({"falling", "carried", "ground", "returning"} <= states, states)
        self.assertFalse(self.world.of("message"))                      # back home
        self.assertIn(("restore", "message1"), self.world.screen_requests)  # and the cover comes off

    def test_one_message_at_a_time_and_it_can_be_switched_off(self):
        self.assertTrue(self.world.steal_message(self.fox))
        self.assertFalse(self.world.steal_message(self.fox))
        world, _ = make_world(orange=True, grey=False)
        world.discord_spot = {"x": 1400.0, "y": 600.0}
        world.settings["mischief"]["discord"] = False
        self.assertFalse(world.steal_message(world.of("fox")[0]))

    def test_a_distracted_fox_means_nothing_is_taken(self):
        self.world.steal_message(self.fox)
        self.world.screen_requests.clear()
        self.fox.do(Step("idle", 60))  # something else caught its eye before it got there
        run(self.world, self.clock, 25)
        self.assertFalse(self.world.of("message"))
        self.assertIn(("restore", "message1"), self.world.screen_requests)  # no gap left behind

    def test_clicking_the_gap_sends_the_message_home(self):
        self.world.steal_message(self.fox)
        msg = self.world.of("message")[0]
        for _ in range(30 * 30):
            run(self.world, self.clock, 1 / 30)
            if msg.state == "carried":
                break
        self.assertEqual(msg.state, "carried")
        self.world.send_message_home("message1")
        self.assertEqual(msg.state, "returning")
        self.assertIsNone(self.fox.carrying)
        run(self.world, self.clock, 8)
        self.assertTrue(msg.gone)

    def test_the_cover_colour_is_discords_background(self):
        try:
            from PySide6.QtGui import QColor, QImage
            from pet.view import background_colour
        except ImportError:
            self.skipTest("needs PySide6")
        image = QImage(200, 40, QImage.Format_RGB32)
        image.fill(QColor(49, 51, 56))
        for x in range(20, 120):  # some text in the middle
            image.setPixelColor(x, 20, QColor(220, 220, 220))
        self.assertEqual(background_colour(image).getRgb()[:3], (49, 51, 56))
        image.fill(QColor(0, 0, 0))
        self.assertIsNone(background_colour(image))  # an all-black copy: the screen couldn't be read
        busy = QImage(200, 40, QImage.Format_RGB32)
        for x in range(200):
            for y in range(40):
                busy.setPixelColor(x, y, QColor((x * 7) % 256, (y * 13) % 256, (x + y) % 256))
        self.assertIsNone(background_colour(busy))  # a picture, not a plain background

    def test_only_the_words_are_taken(self):
        try:
            from PySide6.QtGui import QColor, QImage
            from pet.view import text_only
        except ImportError:
            self.skipTest("needs PySide6")
        image = QImage(300, 40, QImage.Format_RGB32)
        image.fill(QColor(49, 51, 56))
        for x in range(4, 36):  # an avatar at the left
            for y in range(4, 36):
                image.setPixelColor(x, y, QColor(88, 101, 242))
        for x in range(80, 200):  # a line of "text"
            for y in (18, 19, 22):
                if x % 3:
                    image.setPixelColor(x, y, QColor(220, 222, 225))
        words, crop = text_only(image, QColor(49, 51, 56), skip_left=44)
        self.assertGreaterEqual(crop.left(), 44)           # not the avatar
        self.assertLessEqual(crop.left(), 80)
        self.assertGreaterEqual(crop.right(), 199)
        self.assertLess(crop.width(), 140)                 # cropped to the words
        self.assertEqual(words.pixelColor(words.width() - 1, 0).alpha(), 0)  # background see-through
        blank = QImage(300, 40, QImage.Format_RGB32)
        blank.fill(QColor(49, 51, 56))
        self.assertIsNone(text_only(blank, QColor(49, 51, 56)))  # no words, nothing taken

    def test_if_the_window_changes_the_message_just_vanishes(self):
        self.world.steal_message(self.fox)
        self.world.cancel_message("message1")
        self.assertFalse(self.world.of("message"))
        self.assertIn(("restore", "message1"), self.world.screen_requests)


class DiscordInUse(unittest.TestCase):
    def test_while_you_chat_a_fox_soon_steals_and_returns_it_quickly(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.do(Step("sleep", 999))
        world.discord_spot = {"x": fox.x + 200, "y": 600.0}
        world.discord_active = True
        stolen_at = returned_at = None
        for i in range(240 * 30):
            run(world, clock, 1 / 30)
            if stolen_at is None and world.of("message"):
                stolen_at = i / 30
            if stolen_at is not None and returned_at is None and not world.of("message"):
                returned_at = i / 30
                break
        self.assertIsNotNone(stolen_at)                # it even woke from its nap for it
        self.assertLess(returned_at - stolen_at, 20)  # a quick heist

    def test_no_temptation_when_you_are_not_using_it(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        fox.do(Step("idle", 999))
        world.discord_spot = {"x": fox.x + 200, "y": 600.0}
        world.discord_active = False
        run(world, clock, 60)
        self.assertFalse(world.of("message"))


class Blustery(unittest.TestCase):
    def test_a_blustery_spell_gusts_then_dies_down(self):
        world, clock = make_world(orange=False, grey=False)
        self.assertEqual(world.wind, 0.0)
        world.blustery(minutes=2)
        strongest = 0.0
        for _ in range(130 * 10):
            run(world, clock, 0.1, fps=10)
            strongest = max(strongest, world.wind)
        self.assertGreater(strongest, 0.6)
        run(world, clock, 30, fps=10)
        self.assertLess(world.wind, 0.05)  # calm again

    def test_leaves_blow_downwind_and_more_of_them_fall(self):
        from pet.items import Leaf
        world, clock = make_world(orange=False, grey=False)
        world.timers["leaf"] = 0
        calm = world.add(Leaf(world, 900.0, 200.0, "red"))
        calm.sway = 0
        run(world, clock, 3, fps=10)
        calm_drift = calm.x - 900
        world.blustery(minutes=5)
        world.wind_dir = 1
        world._gust_phase = 20.0  # straight into the thick of it
        world.wind = 0.9
        windy = world.add(Leaf(world, 900.0, 200.0, "red"))
        windy.sway = 0
        run(world, clock, 3, fps=10)
        self.assertGreater(windy.x - 900, calm_drift + 200)
        self.assertGreater(len(world.of("leaf")), 5)

    def test_blustery_days_happen_by_themselves_sometimes(self):
        started = 0
        for seed in range(12):
            world, clock = make_world(orange=False, grey=False, seed=seed)
            self.assertGreater(world.weather_timer, 10 * 60)  # never straight away
            world.weather_timer = 0.5                          # skip ahead to the next chance of wind
            run(world, clock, 1, fps=10)
            started += world.blustery_left > 0
        self.assertTrue(2 <= started <= 11)  # some of the time, not every time


class MessageAlwaysGoesHome(unittest.TestCase):
    def test_a_distracted_fox_cannot_keep_a_message_forever(self):
        world, clock = make_world(orange=True, grey=False)
        fox = world.of("fox")[0]
        world.discord_spot = {"x": fox.x + 100, "y": 600.0}
        world.steal_message(fox)
        world.screen_requests.clear()
        run(world, clock, 8)
        fox.do(Step("sleep", 999))  # it wanders off to nap, message and all
        for _ in range(120 * 30):
            run(world, clock, 1 / 30)
            if not world.of("message"):
                break
        self.assertFalse(world.of("message"))
        self.assertIn(("restore", "message1"), world.screen_requests)


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


def crows_with_scarecrow(seed=1):
    """A world with the scarecrow out (no foxes to scare anyone) and a party of crows, settled in."""
    world, clock = make_world(seed=seed, orange=False, grey=False)
    scarecrow = next(p for p in world.of("prop") if p.variant == "scarecrow")
    party = world.invite_visitor("crows").party
    party.long, party.stay = True, 10 ** 6
    run(world, clock, 15, fps=20)
    return world, clock, scarecrow, party


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
        self.assertTrue(all(y >= 40 for _, y in changed))  # low down in the doorway, chin on the ground

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


class OakThroughTheYear(unittest.TestCase):
    def oak(self, season, snow=False):
        world, clock = make_world(season, orange=False, grey=False)
        world.settings["snow"] = snow
        run(world, clock, 0.1)
        return world, clock, world.tree()

    def test_winter_snow_comes_and_goes_or_can_be_chosen(self):
        world, clock, tree = self.oak("winter", snow="auto")
        days = set()
        for day in range(30):
            clock[0] = datetime.datetime(2027, 1, 1, 12) + datetime.timedelta(days=day)
            days.add(world.snowy)
        self.assertEqual(days, {True, False})
        world.settings["snow"] = True
        self.assertEqual(tree.look, "oak_snow")
        world.settings["snow"] = False
        self.assertEqual(tree.look, "oak_winter")

    def test_the_snow_choice_is_saved(self):
        path = Path(os.environ["PIXELFOX_USER_DIR"]) / "snow.json"
        settings = save.load(path)
        settings["snow"] = True
        save.store(settings, path)
        self.assertIs(save.load(path)["snow"], True)

    def test_clicking_the_bare_oak_drops_a_branch_that_fades(self):
        world, clock, tree = self.oak("winter")
        tree.click()
        twigs = world.of("twig")
        self.assertEqual(len(twigs), 1)
        run(world, clock, 5)
        self.assertEqual(twigs[0].y, world.ground)
        run(world, clock, 35)
        self.assertFalse(world.of("twig"))

    def test_clicking_the_snowy_oak_drops_clumps_of_snow(self):
        world, clock, tree = self.oak("winter", snow=True)
        tree.click()
        self.assertGreaterEqual(len(world.of("snow")), 4)
        run(world, clock, 3)
        self.assertTrue(all(c.anim.name == "snow_puff" for c in world.of("snow")))
        run(world, clock, 10)
        self.assertFalse(world.of("snow"))

    def test_clicking_the_spring_oak_drops_a_caterpillar_that_runs_off(self):
        world, clock, tree = self.oak("spring")
        tree.click()
        worm = world.of("inchworm")[0]
        run(world, clock, 3)
        self.assertEqual(worm.y, world.ground)
        self.assertEqual(worm.anim.name, "inchworm")
        run(world, clock, 120, fps=10)
        self.assertTrue(worm.gone)

    def test_clicking_the_summer_oak_drops_green_leaves_and_out_flies_a_butterfly(self):
        world, clock, tree = self.oak("summer")
        tree.click()
        self.assertTrue(all(l.anim.name == "leaf_green" for l in world.of("leaf")))
        self.assertGreaterEqual(len(world.of("leaf")), 2)
        fly = world.of("butterfly")[0]
        run(world, clock, 60, fps=10)
        self.assertTrue(fly.gone)

    def test_clicking_the_autumn_oak_sometimes_lets_down_a_spider(self):
        spun = False
        for seed in range(12):
            world, clock = make_world("autumn", seed=seed, orange=False, grey=False)
            world.tree().click()
            spiders = world.of("spider")
            if not spiders:
                continue
            spun = True
            run(world, clock, 2)
            self.assertTrue(world.of("silk"))  # hanging on its thread
            run(world, clock, 30)
            self.assertFalse(world.of("spider"))
            self.assertFalse(world.of("silk"))  # and the thread's gone with it
        self.assertTrue(spun)

    def test_only_autumn_drops_acorns_and_coloured_leaves(self):
        for season in ("winter", "spring", "summer"):
            world, clock, _ = self.oak(season)
            world.timers.update(leaf=0, acorn=0)
            run(world, clock, 30, fps=10)
            self.assertEqual(world.nuts(), [], season)
            self.assertTrue(all(l.anim.name == "leaf_green" for l in world.of("leaf")), season)

    def test_summer_leaves_fall_rarely(self):
        world, clock, _ = self.oak("summer")
        world.timers["leaf"] = 0
        run(world, clock, 60, fps=10)
        self.assertLessEqual(len(world.of("leaf")), 3)

    def test_a_june_beetle_or_ladybug_climbs_the_summer_oak_and_flies_off(self):
        for bug in ("junebug", "ladybug"):
            world, clock, tree = self.oak("summer")
            beetle = world.invite_visitor(bug)
            self.assertEqual(beetle.species, bug)
            highest = world.ground
            flew = False
            for _ in range(60 * 10):
                run(world, clock, 0.1, fps=10)
                highest = min(highest, beetle.y)
                flew = flew or beetle.anim.name == f"{bug}_fly"
                if beetle.gone:
                    break
            self.assertLess(highest, world.ground - 70 * world.scale)  # climbed well up the trunk
            self.assertTrue(flew)
            self.assertTrue(beetle.gone)

    def test_a_cicada_buzzes_on_the_autumn_oak(self):
        world, clock, _ = self.oak("autumn")
        cicada = world.invite_visitor("cicada")
        buzzed = False
        for _ in range(90 * 10):
            run(world, clock, 0.1, fps=10)
            buzzed = buzzed or any(b.anim.name == "buzz_bubble" for b in world.of("bubble"))
            if cicada.gone:
                break
        self.assertTrue(buzzed)
        self.assertTrue(cicada.gone)

    def test_tree_creatures_need_the_oak(self):
        world, _, _ = self.oak("summer")
        world.settings["items"]["oak"]["out"] = False
        world.rebuild()
        self.assertIsNone(world.invite_visitor("ladybug"))

    def test_birds_sit_on_real_branches_of_the_bare_oak(self):
        from PIL import Image
        for look in ("oak_winter", "oak_snow", "oak_spring"):
            m = sprites.meta(look)
            img = Image.open(sprites.SPRITE_DIR / f"{look}.png").convert("RGBA")
            self.assertGreaterEqual(len(m["perches"]), 4)
            for x, y in m["perches"]:
                near = [img.getpixel((round(x) + dx, round(y) + dy))[3] for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
                self.assertTrue(any(a > 0 for a in near), (look, x, y))


class WinterThings(unittest.TestCase):
    def winter(self, snow=False, orange=False):
        world, clock = make_world("winter", orange=orange, grey=False)
        world.settings["snow"] = snow
        run(world, clock, 0.1)
        return world, clock

    def thing(self, world, variant):
        return next(t for t in world.things if getattr(t, "variant", None) == variant)

    def test_the_sled_and_christmas_tree_come_out_in_winter_only_the_stump_all_year(self):
        world, _ = self.winter()
        for name in ("sled", "stump", "xmas_tree"):
            self.assertTrue(any(getattr(t, "variant", None) == name for t in world.things), name)
        for season in ("spring", "summer", "autumn"):
            world, _ = make_world(season, orange=False, grey=False)
            names = {getattr(t, "variant", None) for t in world.things}
            self.assertIn("stump", names, season)
            self.assertFalse(names & {"sled", "xmas_tree"}, season)

    def test_they_get_a_coat_of_snow_on_snowy_days(self):
        world, clock = self.winter(snow=True)
        self.assertEqual(self.thing(world, "sled").anim.name, "sled_snow")
        self.assertEqual(self.thing(world, "xmas_tree").anim.name, "xmas_tree_snow")
        self.assertEqual(self.thing(world, "stump").anim.name, "stump_snow")
        world.settings["snow"] = False
        run(world, clock, 0.1)
        self.assertEqual(self.thing(world, "sled").anim.name, "sled")
        self.assertEqual(self.thing(world, "stump").anim.name, "stump")

    def test_clicks_wobble_the_sled_and_light_up_the_tree(self):
        for snow in (False, True):
            world, clock = self.winter(snow=snow)
            sled, tree = self.thing(world, "sled"), self.thing(world, "xmas_tree")
            sled.click()
            tree.click()
            self.assertTrue(sled.anim.name.endswith("_wobble"))
            self.assertTrue(tree.anim.name.endswith("_sparkle"))
            run(world, clock, 2)
            self.assertEqual(sled.anim.name, sled.look)
            self.assertEqual(tree.anim.name, tree.look)

    def test_knocking_the_snowy_stump_tips_its_snow_off(self):
        world, _ = self.winter(snow=True)
        self.thing(world, "stump").click()
        self.assertTrue(world.of("snow"))

    def test_a_fox_hops_up_on_the_stump(self):
        world, clock = self.winter(orange=True)
        fox = world.of("fox")[0]
        stump = self.thing(world, "stump")
        world.climb(fox, stump)
        highest = world.ground
        for _ in range(200):
            run(world, clock, 0.1, fps=10)
            highest = min(highest, fox.y)
        self.assertLessEqual(highest, world.ground - 14 * world.scale)

    def test_crows_perch_on_the_sled_and_the_christmas_tree_star(self):
        from pet.visitors import crow_perches
        world, _ = self.winter()
        holders = {getattr(p.holder, "variant", None) for p in crow_perches(world)}
        self.assertTrue({"sled", "xmas_tree", "stump"} <= holders)


class Spring(unittest.TestCase):
    def spring(self, seed=3, **foxes):
        world, clock = make_world("spring", seed=seed, **{"orange": False, "grey": False, **foxes})
        run(world, clock, 0.1)
        return world, clock

    def bed(self, world, kind):
        return next(t for t in world.of("prop") if t.variant == kind)

    def test_daffodils_tulips_and_violets_come_out_in_spring(self):
        world, _ = self.spring()
        for kind in ("daffodils", "tulips", "violets"):
            self.assertGreaterEqual(len(self.bed(world, kind).flower_heads()), 5, kind)
        world, _ = make_world("summer", orange=False, grey=False)
        self.assertFalse([t for t in world.of("prop") if t.variant in ("daffodils", "tulips", "violets")])

    def test_butterflies_land_on_the_flowers_and_move_on(self):
        landed = False
        for seed in range(6):
            world, clock = self.spring(seed=seed)
            fly = world.invite_visitor("butterflies")
            heads = []
            for _ in range(120 * 10):
                run(world, clock, 0.1, fps=10)
                if fly.state == "rest":
                    landed = True
                    heads = [h for t in world.of("prop") if t.variant in t.FLOWERS for h in t.flower_heads()]
                    self.assertTrue(any(abs(fly.x - x) < 1 and abs(fly.y - y) < 1 for x, y in heads))
                    self.assertTrue(fly.anim.name.endswith("_rest"))
                if fly.gone:
                    break
            self.assertTrue(fly.gone, seed)
        self.assertTrue(landed)

    def test_clicking_flowers_bobs_them_and_sometimes_a_butterfly_flies_up(self):
        flew = False
        for seed in range(10):
            world, _ = self.spring(seed=seed)
            tulips = self.bed(world, "tulips")
            tulips.click()
            self.assertEqual(tulips.anim.name, "tulips_bob")
            flew = flew or bool(world.of("butterfly"))
        self.assertTrue(flew)

    def test_songbirds_sing_and_the_foxes_listen(self):
        sang = False
        for seed in range(6):
            world, clock = self.spring(seed=seed, orange=True)
            bird = world.invite_visitor("songbirds")
            for _ in range(100 * 10):
                run(world, clock, 0.1, fps=10)
                sang = sang or bool(world.of("note"))
                if bird.gone:
                    break
            self.assertTrue(bird.gone, seed)
        self.assertTrue(sang)

    def test_a_robin_on_the_ground_pulls_up_a_worm(self):
        from pet.visitors import Perch, SongBird
        wormed = False
        for seed in range(8):
            world, clock = self.spring(seed=seed)
            robin = world.add(SongBird(world, "robin"))
            robin.perch = Perch(x=900.0)
            for _ in range(70 * 10):
                run(world, clock, 0.1, fps=10)
                wormed = wormed or robin.anim.name == "robin_worm"
            if wormed:
                break
        self.assertTrue(wormed)

    def test_a_click_sends_a_songbird_off(self):
        world, clock = self.spring()
        bird = world.invite_visitor("songbirds")
        run(world, clock, 8)
        bird.click()
        run(world, clock, 20)
        self.assertTrue(bird.gone)


def season_world(season, seed=3, **foxes):
    world, clock = make_world(season, seed=seed, **{"orange": False, "grey": False, **foxes})
    world.settings["snow"] = False
    run(world, clock, 0.1)
    return world, clock


def item(world, variant):
    return next(t for t in world.things if getattr(t, "variant", None) == variant)


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
        cob.taken = True
        self.assertFalse(cob.draggable)


class BirchTree(unittest.TestCase):
    def test_the_birch_is_out_all_year_dressed_for_the_season(self):
        for season in seasons.SEASONS:
            world, _ = season_world(season)
            self.assertEqual(world.of("birch")[0].anim.name, f"birch_{season}")
        world, clock = season_world("winter")
        world.settings["snow"] = True
        run(world, clock, 0.1)
        self.assertEqual(world.of("birch")[0].anim.name, "birch_snow")

    def test_clicking_the_birch(self):
        world, _ = season_world("autumn")
        world.of("birch")[0].click()
        self.assertTrue(world.of("leaf"))
        self.assertTrue(all(l.anim.name in ("leaf_yellow", "leaf_orange") for l in world.of("leaf")))
        world, _ = season_world("winter")
        world.of("birch")[0].click()
        self.assertTrue(world.of("twig"))

    def test_birds_perch_in_the_birch(self):
        from pet.visitors import crow_perches
        world, _ = season_world("summer")
        self.assertTrue(any(getattr(p.holder, "kind", None) == "birch" for p in crow_perches(world)))


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


class MoreFlowers(unittest.TestCase):
    def test_dahlias_in_summer_and_autumn(self):
        for season in ("summer", "autumn"):
            world, _ = season_world(season)
            self.assertGreaterEqual(len(item(world, "dahlias").flower_heads()), 5)

    def test_spring_dandelion_clocks_blow_away_and_grow_back(self):
        world, clock = season_world("spring")
        dandelions = item(world, "dandelions")
        self.assertEqual(dandelions.anim.name, "dandelions_spring")
        dandelions.click()
        self.assertGreaterEqual(len(world.of("fluff")), 20)
        run(world, clock, 1)
        self.assertEqual(dandelions.anim.name, "dandelions_spring_bare")
        dandelions.click()  # nothing left to blow
        run(world, clock, 130, fps=10)
        self.assertEqual(dandelions.anim.name, "dandelions_spring")

    def test_summer_dandelions_are_yellow_flowers(self):
        world, clock = season_world("summer")
        dandelions = item(world, "dandelions")
        self.assertEqual(dandelions.anim.name, "dandelions_summer")
        dandelions.click()
        self.assertFalse(world.of("fluff"))
        self.assertEqual(dandelions.anim.name, "dandelions_summer_bob")

    def test_pansies_grow_under_the_summer_trees(self):
        from PIL import Image
        for look, ground in (("oak_summer", 229), ("birch_summer", 193)):
            img = Image.open(sprites.SPRITE_DIR / f"{look}.png").convert("RGB")
            purple = [(x, y) for x in range(img.width) for y in range(ground - 6, ground + 1)
                      if img.getpixel((x, y)) in ((0x52, 0x26, 0xa0), (0x70, 0x40, 0xc4), (0x9a, 0x6e, 0xe0))]
            self.assertTrue(purple, look)


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


class AtNight(unittest.TestCase):
    def night(self, season, hour=23):
        world, clock = make_world(season, hour=hour, orange=False, grey=False)
        world.settings["snow"] = False
        run(world, clock, 0.1)
        return world, clock

    def test_fireflies_on_a_summer_night(self):
        world, clock = self.night("summer")
        run(world, clock, 30)
        flies = world.of("firefly")
        self.assertTrue(flies)
        self.assertLessEqual(len(flies), 12)
        self.assertTrue(all(any(g.holder is f for g in world.of("glow")) for f in flies))  # each one glows

    def test_fireflies_leave_in_the_morning(self):
        world, clock = self.night("summer")
        run(world, clock, 30)
        clock[0] = clock[0].replace(hour=12)
        run(world, clock, 20)
        self.assertFalse(world.of("firefly"))
        self.assertFalse(world.of("glow"))

    def test_no_fireflies_in_the_daytime_or_out_of_summer(self):
        world, clock = self.night("summer", hour=13)
        run(world, clock, 30)
        self.assertFalse(world.of("firefly"))
        world, clock = self.night("autumn")
        run(world, clock, 30)
        self.assertFalse(world.of("firefly"))

    def test_jack_o_lanterns_glow_after_dark(self):
        from pet.items import Pumpkin
        world, clock = self.night("autumn")
        pumpkin = world.add(Pumpkin(world, 700, (clock[0] - datetime.timedelta(days=30)).timestamp(), jack=True))
        run(world, clock, 1)
        self.assertTrue(pumpkin.anim.name.endswith("_jack"))
        self.assertTrue(any(g.holder is pumpkin for g in world.of("glow")))
        clock[0] = clock[0].replace(hour=12)
        run(world, clock, 5)
        self.assertFalse(any(g.holder is pumpkin for g in world.of("glow")))

    def test_the_christmas_tree_lights_up(self):
        world, clock = self.night("winter")
        tree = item(world, "xmas_tree")
        run(world, clock, 1)
        self.assertTrue(any(g.holder is tree and g.anim.name == "glow_lights" for g in world.of("glow")))

    def test_the_owl_perches_hoots_and_leaves_at_dawn(self):
        world, clock = self.night("autumn")
        foxes_awake = [f.asleep for f in world.of("fox")]
        owl = world.invite_visitor("owl")
        run(world, clock, 30)
        self.assertEqual(owl.state, "perch")
        seen = set()
        for _ in range(40 * 30):  # it hoots or turns its head every 5-14 seconds
            run(world, clock, 1 / 30)
            seen.add(owl.anim.name)
            seen.update(b.anim.name for b in world.of("bubble"))
        self.assertTrue({"owl_hoot", "owl_turn", "hoo_bubble"} & seen)
        self.assertEqual([f.asleep for f in world.of("fox")], foxes_awake)  # it doesn't wake anyone
        clock[0] = clock[0].replace(hour=8)
        run(world, clock, 60)
        self.assertTrue(owl.gone or owl.state == "leave")

    def test_clicking_the_owl_sends_it_off(self):
        world, clock = self.night("spring")
        owl = world.invite_visitor("owl")
        run(world, clock, 30)
        owl.click()
        self.assertEqual(owl.state, "leave")


class LocalWeather(unittest.TestCase):
    def answer(self, code, rain=0.0, snowfall=0.0, depth=0.0):
        return {"current": {"weather_code": code, "rain": rain, "showers": 0.0, "snowfall": snowfall,
                            "snow_depth": depth, "precipitation": rain}}

    def test_reading_the_weather_report(self):
        self.assertIsNone(weather.parse(self.answer(0)).falling)
        self.assertEqual(weather.parse(self.answer(61, rain=0.6)).falling, "rain")
        self.assertFalse(weather.parse(self.answer(61, rain=0.6)).heavy)
        self.assertTrue(weather.parse(self.answer(65, rain=6)).heavy)
        report = weather.parse(self.answer(73, snowfall=0.4))
        self.assertEqual(report.falling, "snow")
        self.assertTrue(report.snow_on_ground)
        self.assertTrue(weather.parse(self.answer(2, depth=0.12)).snow_on_ground)  # yesterday's snow, still lying
        self.assertFalse(weather.parse(self.answer(2, depth=0.0)).snow_on_ground)
        self.assertIsNone(weather.parse({"nonsense": True}))
        self.assertIsNone(weather.parse("not even a dict"))

    def test_fetch_asks_open_meteo_for_a_rough_place_and_fails_quietly(self):
        import contextlib
        import io
        asked = []

        def opener(request, timeout):
            asked.append(request.full_url)
            return contextlib.closing(io.BytesIO(json.dumps(self.answer(63, rain=2)).encode()))

        report = REAL_FETCH(51.50735, -0.12776, opener=opener)
        self.assertEqual(report.falling, "rain")
        self.assertIn("api.open-meteo.com", asked[0])
        self.assertIn("latitude=51.5&longitude=-0.1&", asked[0])  # only roughly where you are

        def broken(request, timeout):
            raise OSError("no internet")

        self.assertIsNone(REAL_FETCH(51.5, -0.1, opener=broken))

    def test_the_watcher_keeps_the_latest_fresh_report(self):
        settings = {"weather": True, "location": {"lat": 45.0, "lon": -93.0}}
        reports = [weather.Report("snow")]
        watcher = weather.Watcher(settings, fetcher=lambda lat, lon: reports[0])
        watcher.check()
        self.assertEqual(watcher.current().falling, "snow")
        reports[0] = None  # offline: keep what we had
        watcher.check()
        self.assertEqual(watcher.current().falling, "snow")
        later = datetime.datetime.now() + datetime.timedelta(hours=4)
        self.assertIsNone(watcher.current(later))  # too old to trust
        settings["weather"] = False
        self.assertIsNone(watcher.current())  # switched off

    def test_the_weather_setting_is_saved_and_checked(self):
        path = Path(os.environ["PIXELFOX_USER_DIR"]) / "weather.json"
        self.assertTrue(save.load(path)["weather"])
        path.write_text(json.dumps({"weather": False}))
        self.assertFalse(save.load(path)["weather"])
        path.write_text(json.dumps({"weather": "sometimes"}))
        self.assertTrue(save.load(path)["weather"])

    def test_rain_falls_and_splashes(self):
        world, clock = season_world("summer")
        world.weather = weather.Report("rain")
        run(world, clock, 3)
        drops = world.of("rain")
        self.assertTrue(drops)
        self.assertTrue(any(d.anim.name == "rain_splash" for d in drops))
        world.weather = weather.Report(None)
        run(world, clock, 3)
        self.assertFalse(world.of("rain"))  # it's stopped

    def test_snow_falls_and_settles(self):
        world, clock = season_world("winter")
        world.weather = weather.Report("snow", snow_on_ground=True)
        run(world, clock, 25)
        flakes = world.of("snowflake")
        self.assertTrue(flakes)
        self.assertTrue(any(f.settled for f in flakes))

    def test_real_snow_on_the_ground_makes_a_snowy_winter_day(self):
        world, clock = season_world("winter")
        world.settings["snow"] = "auto"
        world.weather = weather.Report(None, snow_on_ground=True)
        self.assertTrue(world.snowed_over)
        world.weather = weather.Report(None, snow_on_ground=False)
        self.assertFalse(world.snowed_over)
        world.settings["snow"] = True  # what you chose from the tray menu still wins
        self.assertTrue(world.snowed_over)

    def test_make_it_rain_from_the_tray(self):
        world, clock = season_world("spring")
        world.make_it("rain", minutes=0.05)  # three seconds
        run(world, clock, 2)
        self.assertTrue(world.of("rain"))
        run(world, clock, 3)
        self.assertIsNone(world.falling)
        self.assertFalse(world.of("rain"))

    def test_no_fireflies_in_the_rain(self):
        world, clock = make_world("summer", hour=23, orange=False, grey=False)
        world.settings["snow"] = False
        world.weather = weather.Report("rain")
        run(world, clock, 30)
        self.assertFalse(world.of("firefly"))


def loose_ball(world, x=300.0, height=200):
    import types
    from pet.items import Treasure
    ball = world.add(Treasure(world, types.SimpleNamespace(x=x), "ball"))
    ball.carried_by = None
    ball.x, ball.y = x, world.ground - height
    return ball


class BouncyBalls(unittest.TestCase):
    def test_a_thrown_icon_bounces_and_settles(self):
        world, clock = season_world("autumn")  # no foxes to fetch it
        ball = loose_ball(world)
        ball.pick_up()
        self.assertTrue(ball.held)
        ball.throw(400, -300)
        heights = []
        for _ in range(30 * 8):
            run(world, clock, 1 / 30)
            heights.append(world.ground - ball.y)
        landed = [i for i in range(1, len(heights)) if heights[i] == 0 and heights[i - 1] > 0]
        self.assertGreater(len(landed), 2)  # bounce, bounce, bounce
        self.assertTrue(ball.resting)
        self.assertGreater(ball.x, 300)

    def test_it_bounces_off_the_edge_of_the_screen(self):
        world, clock = season_world("autumn")
        ball = loose_ball(world, x=world.width - 100)
        ball.throw(3000, 0)
        run(world, clock, 3)
        self.assertLess(ball.x, world.width - 5)
        self.assertGreater(ball.x, 0)

    def test_a_fox_fetches_it_back(self):
        world, clock = season_world("autumn", orange=True)
        fox = world.of("fox")[0]
        ball = loose_ball(world, x=500)
        ball.throw(700, -400)
        self.assertIs(ball.chased_by, fox)
        carried = False
        for _ in range(30 * 20):
            run(world, clock, 1 / 30)
            carried = carried or ball.carried_by is fox
        self.assertTrue(carried)
        self.assertIsNone(ball.carried_by)  # dropped
        self.assertLess(abs(ball.x - ball.thrown_from), 80 * world.scale)  # back where it was thrown from

    def test_a_tap_sends_it_up(self):
        world, clock = season_world("autumn")
        ball = loose_ball(world, height=0)
        ball.click()
        run(world, clock, 0.2)
        self.assertGreater(world.ground - ball.y, 10)

    def test_you_cant_grab_one_out_of_a_foxs_mouth(self):
        world, _ = season_world("autumn", orange=True)
        ball = loose_ball(world)
        ball.carried_by = world.of("fox")[0]
        self.assertFalse(ball.draggable)


class DesktopFolders(unittest.TestCase):
    def setup(self, height=600):
        world, clock = season_world("autumn", orange=True)
        world.folder_spots = [{"name": "Homework", "x": 400.0, "y": world.ground - height, "w": 76.0, "h": 70.0,
                               "home": [20, 300], "left": 0.0, "right": float(world.width)}]
        fox = world.of("fox")[0]
        fox.boredom = 1.0
        return world, clock, fox

    def test_a_fox_pulls_a_folder_down_drags_it_and_drops_it(self):
        world, clock, fox = self.setup()
        self.assertTrue(world.move_folder(fox))
        folder = world.of("folder")[0]
        self.assertEqual(folder.home, [20, 300])
        states, moves = set(), []
        for _ in range(30 * 60):
            run(world, clock, 1 / 30)
            states.add(folder.state)
            moves += [r for r in world.folder_requests if r[1] == "Homework"]
            world.folder_requests.clear()
            if folder.gone:
                break
        self.assertTrue({"falling", "dragged", "dropped"} <= states)
        self.assertEqual(moves[-1][0], "drop")
        _, _, x, y, _, _ = moves[-1]
        self.assertEqual(y, world.ground - 2 * world.scale)  # on the ground
        self.assertGreater(abs(x - 400), 60)                 # somewhere else
        self.assertIsNone(fox.dragging_folder)

    def test_not_another_one_for_a_while(self):
        world, clock, fox = self.setup()
        spot = dict(world.folder_spots[0])
        world.move_folder(fox)
        world.folder_spots = [spot]
        self.assertIsNone(world.folder_to_move(fox))  # one at a time, and then a rest
        run(world, clock, 70)
        self.assertIsNone(world.folder_to_move(fox))

    def test_mischief_off_means_no_folders_moved(self):
        world, clock, fox = self.setup()
        world.settings["mischief"]["folders"] = False
        self.assertIsNone(world.folder_to_move(fox))
        self.assertFalse(world.move_folder(fox))

    def test_picking_the_fox_up_makes_it_let_go(self):
        world, clock, fox = self.setup(height=10)
        world.move_folder(fox)
        folder = world.of("folder")[0]
        for _ in range(30 * 30):
            run(world, clock, 1 / 30)
            if folder.state == "dragged":
                break
        self.assertEqual(folder.state, "dragged")
        fox.pick_up()
        run(world, clock, 0.1)
        self.assertTrue(folder.gone)
        self.assertIsNone(fox.dragging_folder)

    def test_folder_homes_are_saved_and_checked(self):
        path = Path(os.environ["PIXELFOX_USER_DIR"]) / "homes.json"
        self.assertEqual(save.load(path)["folder_homes"], {})
        self.assertTrue(save.load(path)["mischief"]["folders"])
        path.write_text(json.dumps({"folder_homes": {"Homework": [20, 300], "bad": "x", "worse": [1]}}))
        self.assertEqual(save.load(path)["folder_homes"], {"Homework": [20, 300]})

    def test_away_from_windows_nothing_happens(self):
        from pet import desktop_icons
        if desktop_icons.ON_WINDOWS:
            self.skipTest("only checks the non-Windows fallbacks")
        self.assertIsNone(desktop_icons.find_listview())
        self.assertEqual(desktop_icons.folders(), [])
        self.assertEqual(desktop_icons.put_back({"Homework": [1, 2]}), 0)
        self.assertFalse(desktop_icons.Mover("Homework").ok)

    def test_only_real_folders_count(self):
        from pet import desktop_icons
        with tempfile.TemporaryDirectory() as desk:
            (Path(desk) / "Homework").mkdir()
            (Path(desk) / "notes.txt").write_text("hi")
            self.assertTrue(desktop_icons.is_folder("Homework", [desk]))
            self.assertFalse(desktop_icons.is_folder("notes.txt", [desk]))
            self.assertFalse(desktop_icons.is_folder("This PC", [desk]))
            self.assertFalse(desktop_icons.is_folder("..", [desk]))


def qt_available():
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PySide6.QtWidgets import QApplication  # noqa: F401
        return True
    except Exception:  # PySide6 or its system libraries missing: only the Qt-free tests run
        return False


@unittest.skipUnless(qt_available(), "needs PySide6")
class ScreenSaver(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_windows_switches(self):
        from pet import saver
        self.assertEqual(saver.mode(["/s"]), "run")
        self.assertEqual(saver.mode(["/S"]), "run")
        self.assertEqual(saver.mode(["/p", "1234"]), "preview")
        self.assertEqual(saver.mode(["/c:5678"]), "settings")
        self.assertEqual(saver.mode([]), "settings")  # double-clicked

    def test_bigger_and_no_mischief_and_nothing_saved(self):
        from pet import saver
        settings = save.load(Path(os.environ["PIXELFOX_USER_DIR"]) / "missing.json")
        copy_ = saver.saver_settings(settings, 1080)
        self.assertEqual(copy_["scale"], 3)
        self.assertFalse(any(copy_["mischief"].values()))
        self.assertTrue(any(settings["mischief"].values()))  # your own settings untouched

    def make(self):
        from pet import saver
        settings = save.load(Path(os.environ["PIXELFOX_USER_DIR"]) / "missing.json")
        return saver.Saver(self.app, settings)

    def mouse(self, win, kind, button):
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QMouseEvent
        point = QPointF(50, 50)
        self.app.sendEvent(win, QMouseEvent(kind, point, point, button, button, Qt.NoModifier))

    def test_moving_the_mouse_does_not_close_it_but_a_click_does(self):
        from PySide6.QtCore import QEvent, Qt
        running = self.make()
        win = running.windows[0]
        running.tick()
        self.mouse(win, QEvent.MouseMove, Qt.NoButton)
        self.assertTrue(running.timer.isActive())
        self.mouse(win, QEvent.MouseButtonPress, Qt.LeftButton)
        self.assertFalse(running.timer.isActive())

    def test_a_key_press_closes_it(self):
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QKeyEvent
        running = self.make()
        self.app.sendEvent(running.windows[0], QKeyEvent(QEvent.KeyPress, Qt.Key_A, Qt.NoModifier, "a"))
        self.assertFalse(running.timer.isActive())

    def test_it_draws_sky_ground_and_grass(self):
        running = self.make()
        running.tick()
        win = running.windows[0]
        img = win.grab().toImage()
        sky = img.pixelColor(5, 5)
        earth = img.pixelColor(5, win.height() - 5)
        self.assertNotEqual(sky.name(), earth.name())
        self.assertTrue(win.blades)
        running.close()


class Version(unittest.TestCase):
    def test_the_version_is_in_the_changelog(self):
        import pet
        self.assertRegex(pet.__version__, r"^\d+\.\d+\.\d+$")
        self.assertIn(f"## {pet.__version__}", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_the_updater_can_read_the_version(self):
        import pet
        import re
        script = (ROOT / "update.ps1").read_text(encoding="utf-8")
        pattern = re.search(r"-match '(.+?)'", script).group(1)  # the pattern update.ps1 uses
        found = re.search(pattern, (ROOT / "pet" / "__init__.py").read_text(encoding="utf-8"))
        self.assertEqual(found.group(1), pet.__version__)
        self.assertIn("Update-PixelFox", (ROOT / "start.ps1").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
