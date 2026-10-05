"""Seasons and what belongs to each, the sprites, day and night, the oak and birch through the year,
winter and spring things, flowers."""
import datetime
import os
import unittest
from pathlib import Path

from helpers import item, make_world, run, season_world  # first: sets up a scratch user-data folder
from PIL import Image
from pet import save, seasons, sprites


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


if __name__ == "__main__":
    unittest.main()
