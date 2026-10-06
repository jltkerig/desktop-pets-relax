"""The tray menu (grouped into submenus), the Toy Box's put-all-out and take-all-in, redrawing only what
changed each frame, and the small world helpers (clamp_x, spot_for, the snowy-day guess)."""
import os
import unittest
from unittest import mock

from helpers import make_world, run  # first: sets up a scratch user-data folder
from pet import save, seasons

try:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication
    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class Helpers(unittest.TestCase):
    def test_clamp_x_keeps_things_on_the_strip(self):
        world, _ = make_world()
        self.assertEqual(world.clamp_x(-500), 40.0)
        self.assertEqual(world.clamp_x(10 ** 6, 60.0), world.width - 60.0)
        self.assertEqual(world.clamp_x(700), 700)

    def test_spot_for_uses_the_saved_spot_only_if_it_is_on_the_strip(self):
        world, _ = make_world()
        world.settings["items"]["oak"]["x"] = 500
        self.assertEqual(world.spot_for("oak", 1.0), 500)
        world.settings["items"]["oak"]["x"] = world.width + 10
        self.assertEqual(world.spot_for("oak", 1.0), 1.0)
        self.assertEqual(world.spot_for("no such thing", 2.0), 2.0)

    def test_the_snowy_day_guess_is_the_same_all_day_and_worked_out_once(self):
        world, clock = make_world("winter")
        world.settings["snow"] = "auto"
        first = world.snowy
        with mock.patch("pet.world.core.random.Random") as rng:
            for _ in range(50):
                self.assertEqual(world.snowy, first)
            rng.assert_not_called()


@unittest.skipUnless(HAVE_QT, "needs PySide6")
class Drawing(unittest.TestCase):
    def stage(self, world):
        from pet.view.stage import Stage
        stage = Stage.__new__(Stage)
        stage.world = world
        return stage

    def test_only_what_changed_is_redrawn(self):
        world, clock = make_world("autumn", orange=True, grey=False)
        stage = self.stage(world)
        before = stage.looks()
        tree = world.tree()
        fox = world.of("fox")[0]
        fox.x += 30
        after = stage.looks()
        changed = {t for t in before.keys() | after.keys() if before.get(t) != after.get(t)}
        self.assertIn(fox, changed)
        self.assertNotIn(tree, changed)

    def test_things_that_come_and_go_are_redrawn(self):
        world, clock = make_world("autumn", orange=True, grey=False)
        stage = self.stage(world)
        before = stage.looks()
        world.drop_acorn(world.tree())
        after = stage.looks()
        new = after.keys() - before.keys()
        self.assertTrue(new)

    def test_still_things_are_not_redrawn_while_the_foxes_play(self):
        world, clock = make_world("winter", orange=True, grey=True)
        world.settings["snow"] = True
        for name in ("snowman", "pond", "woodstack", "sled"):
            world.settings["items"].setdefault(name, {"x": None})["out"] = True
        world.rebuild()
        run(world, clock, 1 / 30)  # (the woodstack and stump put on their snow)
        still = [t for t in world.things if t.kind in ("yard", "climb", "prop")
                 and t.variant not in ("pond", "xmas_tree")]  # (the ice glints, the lights twinkle)
        self.assertGreaterEqual(len(still), 4)
        stage = self.stage(world)
        redrawn = set()
        for _ in range(60):
            before = stage.looks()
            run(world, clock, 1 / 30)
            after = stage.looks()
            redrawn |= {t for t in before.keys() | after.keys() if before.get(t) != after.get(t)}
        self.assertTrue(set(world.of("fox")) & redrawn)
        self.assertFalse([t.variant for t in still if t in redrawn])


@unittest.skipUnless(HAVE_QT, "needs PySide6")
class Menu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def toybox(self, season="summer"):
        from pet.view.toybox import ToyBox
        world, clock = make_world(season, orange=True, grey=False)
        desktop = mock.Mock()
        desktop.world, desktop.settings = world, world.settings
        desktop.weather.current.return_value = None
        patches = [mock.patch("pet.updates.Checker.start", lambda self: self),
                   mock.patch("pet.updates.Checker.available", lambda self: None, create=True),
                   mock.patch.object(save, "store", lambda settings: None)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        toybox = ToyBox(self.app, desktop)
        self.addCleanup(toybox.tray.hide)
        toybox.build()
        return toybox

    def labels(self, menu):
        return [a.text() for a in menu.actions() if not a.isSeparator()]

    def submenu(self, menu, label):
        return next(a.menu() for a in menu.actions() if a.text() == label)

    def test_the_top_of_the_menu_is_short_and_grouped(self):
        menu = self.toybox().menu
        top = self.labels(menu)
        for group in ("Things to do", "Weather", "Invite a visitor", "Mischief", "Settings"):
            self.assertIn(group, top)
        self.assertLess(len(top), 18)
        self.assertNotIn("Sprinkler", top)  # the items are in the Toy Box window

    def test_the_submenus_hold_what_they_say(self):
        menu = self.toybox("winter").menu
        self.assertIn("Zoomies!", self.labels(self.submenu(menu, "Things to do")))
        weather = self.labels(self.submenu(menu, "Weather"))
        self.assertIn("Make it snow", weather)
        self.assertIn("Snow on the oak", weather)
        self.assertIn("Cardinals and chickadees", self.labels(self.submenu(menu, "Invite a visitor")))
        settings = self.submenu(menu, "Settings")
        self.assertIn("Season", self.labels(settings))
        self.assertIn("Size", self.labels(settings))

    def test_mischief_can_be_turned_off_from_the_menu(self):
        toybox = self.toybox()
        mischief = self.submenu(toybox.menu, "Mischief")
        self.assertIn("Steal a Discord message", self.labels(mischief))
        allow = next(a for a in mischief.actions() if a.text().startswith("Steal Discord messages"))
        allow.setChecked(False)
        self.assertFalse(toybox.settings["mischief"]["discord"])
        toybox.build()
        self.assertNotIn("Steal a Discord message", self.labels(self.submenu(toybox.menu, "Mischief")))

    def test_put_all_out_and_take_all_in(self):
        from pet.view.toybox_window import tab_items
        toybox = self.toybox("summer")
        names = tab_items("summer")
        toybox._set_items(names, True)
        out = {t.variant for t in toybox.world.of("yard")}
        self.assertTrue({"sprinkler", "hammock", "sunflowers"} <= out)
        toybox._set_items(names, False)
        self.assertFalse(any(toybox.settings["items"][n]["out"] for n in names))
        self.assertFalse(toybox.world.of("yard"))

    def test_long_tabs_use_two_columns(self):
        from pet.view.toybox_window import ONE_COLUMN, tab_items
        toybox = self.toybox("summer")
        self.assertGreater(len(tab_items("summer")), ONE_COLUMN)
        page = toybox.window.tabs.widget(toybox.window.tab_of["summer"])
        grid = page.layout().itemAt(0).layout()
        self.assertEqual(grid.columnCount(), 2)


if __name__ == "__main__":
    unittest.main()
