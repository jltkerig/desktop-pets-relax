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
                "hop", "boop", "groom"}
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

    def test_a_sleepy_fox_naps_under_the_oak(self):
        world, clock = make_world(orange=True, grey=False, hour=23)
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
        self.assertEqual(first.anim.name, "pumpkin_4")

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
        for _ in range(60 * 30):
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


if __name__ == "__main__":
    unittest.main()
