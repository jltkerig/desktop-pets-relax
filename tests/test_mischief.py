"""Mischief: taskbar treasure (bouncy balls), Discord messages, desktop folders."""
import json
import os
import tempfile
import unittest
from pathlib import Path

from helpers import loose_ball, make_world, run, season_world  # first: sets up a scratch user-data folder
from pet import save
from pet.fox import Step


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


if __name__ == "__main__":
    unittest.main()
