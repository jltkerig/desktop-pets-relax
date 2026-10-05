"""Wind, rain and snow, night, the sun and the moon."""
import datetime
import json
import os
import unittest
from pathlib import Path

from helpers import REAL_FETCH, item, make_world, run, season_world  # first: sets up a scratch user-data folder
from pet import save, weather


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


class SunAndMoon(unittest.TestCase):
    def at(self, hour, minute=0, day=5):
        return datetime.datetime(2026, 10, day, hour, minute)

    def test_the_sun_tells_the_time_from_6am_to_6pm(self):
        from pet import sky
        rise, nine, noon, three, late = (sky.placement(self.at(h)) for h in (6, 9, 12, 15, 17))
        self.assertEqual({rise[0], nine[0], noon[0], three[0], late[0]}, {"sun"})
        self.assertEqual((rise[1], rise[2]), (0.0, 0.0))           # 6 AM: rising on the far left
        self.assertAlmostEqual(nine[1], 0.25)
        self.assertEqual((noon[1], round(noon[2], 6)), (0.5, 1.0))  # noon: at the top, in the middle
        self.assertAlmostEqual(three[1], 0.75)
        self.assertGreater(late[1], 0.9)                            # 5 PM: nearly set, on the right
        self.assertAlmostEqual(nine[2], three[2])                   # an even arc

    def test_the_moon_from_6pm_to_6am(self):
        from pet import sky
        evening, midnight, early = (sky.placement(self.at(h)) for h in (18, 0, 3))
        self.assertEqual({evening[0], midnight[0], early[0]}, {"moon"})
        self.assertEqual(evening[1], 0.0)
        self.assertEqual(midnight[1], 0.5)
        self.assertAlmostEqual(early[1], 0.75)

    def test_moon_phases_and_never_invisible(self):
        from pet import sky
        utc = datetime.timezone.utc
        self.assertEqual(sky.phase_frame(datetime.datetime(2026, 10, 10, 12, tzinfo=utc)), 0)  # new
        self.assertEqual(sky.phase_frame(datetime.datetime(2026, 10, 18, 12, tzinfo=utc)), 2)  # first quarter
        self.assertEqual(sky.phase_frame(datetime.datetime(2026, 10, 26, 12, tzinfo=utc)), 4)  # full
        new_moon_night = datetime.datetime(2026, 10, 10, 22, 0)
        self.assertIn(sky.placement(new_moon_night)[3], (1, 7))  # shown as a thin crescent, not nothing

    def test_away_from_windows_the_desktop_layer_does_nothing(self):
        from pet import desktop_layer
        if desktop_layer.ON_WINDOWS:
            self.skipTest("only checks the non-Windows fallback")
        self.assertFalse(desktop_layer.just_above_desktop(1234))

    def test_the_sky_setting(self):
        path = Path(os.environ["PIXELFOX_USER_DIR"]) / "sky.json"
        self.assertTrue(save.load(path)["sky"])
        path.write_text(json.dumps({"sky": False}))
        self.assertFalse(save.load(path)["sky"])


if __name__ == "__main__":
    unittest.main()
