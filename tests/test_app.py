"""The app around the world: saving, monitors and seams, the screen saver, the version."""
import datetime
import json
import os
import random
import unittest
from pathlib import Path

from helpers import ROOT, make_world, qt_available, run  # first: sets up a scratch user-data folder
from pet import save
from pet.world import World


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



class Updates(unittest.TestCase):
    def test_reading_versions_and_spotting_a_newer_one(self):
        from pet import updates
        self.assertEqual(updates.parse('__version__ = "1.16.1"'), (1, 16, 1))
        self.assertIsNone(updates.parse("nothing here"))
        checker = updates.Checker("1.16.1", fetcher=lambda: (1, 17, 0))
        self.assertIsNone(checker.available())  # not checked yet
        checker.check()
        self.assertEqual(checker.available(), "1.17.0")
        same = updates.Checker("1.17.0", fetcher=lambda: (1, 17, 0))
        same.check()
        self.assertIsNone(same.available())
        offline = updates.Checker("1.16.1", fetcher=lambda: None)
        offline.check()
        self.assertIsNone(offline.available())

    def test_the_updater_closes_a_running_copy_rather_than_skipping(self):
        script = (ROOT / "update.ps1").read_text(encoding="utf-8")
        self.assertIn("Stop-Process", script)
        self.assertIn('-notlike "*--scr*"', script)  # never the screen saver


if __name__ == "__main__":
    unittest.main()
