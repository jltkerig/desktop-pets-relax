"""The foxes' mischief: digging up taskbar icons, stealing Discord messages (and putting them back), and
moving desktop folder icons about."""
from pet.fox import Step, TROT, WALK
from pet.items import Message, Treasure


class Mischief:
    """Part of World (see pet/world/__init__.py)."""

    def treasure_spot(self, fox):
        """A taskbar icon to dig at, not too far away."""
        if not self.mischief("treasure"):
            return None
        near = [x for x in self.taskbar_spots if abs(x - fox.x) < 700 * self.scale / 2]
        spots = near or self.taskbar_spots
        return self.rng.choice(spots) if spots else None

    def dig_for_treasure(self, fox, spot=None):
        """Walk over an icon, dig, "find" a copy of it and run off with it."""
        spot = spot if spot is not None else self.treasure_spot(fox)
        if spot is None:
            return False
        side = 1 if spot >= fox.x else -1
        stand = spot - side * 24 * self.scale
        run_to = self.clamp_x(stand - side * self.rng.uniform(160, 320) * self.scale, 60.0)
        if abs(run_to - stand) < 80:
            run_to = self.clamp_x(stand + side * 200 * self.scale, 60.0)
        fox.do(Step("walk", to_x=stand, speed=WALK), Step("sniff", face=spot), Step("sniff", face=spot),
               Step("dig", self.rng.uniform(2.0, 3.2), face=spot, then=lambda: self.find_treasure(fox, spot)),
               Step("hop", face=spot), Step("trot", to_x=run_to, speed=TROT * 1.2, then=lambda: self.drop_treasure(fox)),
               *self._after_treasure())
        return True


    def mischief(self, kind):
        return bool(self.settings.get("mischief", {}).get(kind, True))

    def steal_message(self, fox):
        """Sit under a Discord message, leap, pull it down, run off and play with it, then put it back."""
        spot = self.discord_spot
        if spot is None or self.of("message") or not self.mischief("discord"):
            return False
        self._treasures += 1
        key = f"message{self._treasures}"
        msg = self.add(Message(self, key, (spot["x"], spot["y"])))
        self.screen_requests.append(("steal", key))
        under = self.clamp_x(spot["x"] - 20 * self.scale)
        side = 1 if under < self.width / 2 else -1
        away = self.clamp_x(under + side * self.rng.uniform(220, 420) * self.scale, 60.0)
        back = self.clamp_x(spot["x"] - 20 * self.scale)

        def yank():
            if not msg.gone:
                msg.carried_by, msg.state = fox, "falling"
                fox.carrying = msg

        def drop():
            if msg.state == "carried":
                msg.state, msg.carried_by = "ground", None
                msg.ground_time = 0.0
            fox.carrying = None

        def pick_up():
            if not msg.gone and msg.state == "ground":
                msg.carried_by, msg.state = fox, "carried"
                fox.carrying = msg

        def send_home():
            fox.carrying = None
            if not msg.gone:
                msg.carried_by, msg.state = None, "returning"

        if self.discord_active:  # you're chatting: a quick grab, a victory hop, and straight back
            msg.limit = 25.0
            fox.do(Step("trot", to_x=under, speed=TROT), Step("crouch", 0.5, face=spot["x"]),
                   Step("hop", face=spot["x"], then=yank), Step("happy", 1.5), Step("hop"), Step("happy", 1.0),
                   Step("hop", face=spot["x"], then=send_home), Step("tilt", face=spot["x"]))
            return True
        fox.do(Step("walk", to_x=under, speed=WALK), Step("look", face=spot["x"]), Step("crouch", 0.8, face=spot["x"]),
               Step("hop", face=spot["x"], then=yank), Step("happy", 0.8),
               Step("trot", to_x=away, speed=TROT * 1.3, then=drop), Step("playbow", 1.0), Step("roll", 1.8),
               Step("happy", 1.0), Step("idle", self.rng.uniform(3, 6)),
               Step("walk", follow=msg, speed=WALK, then=pick_up),
               Step("walk", to_x=back, speed=WALK), Step("hop", face=spot["x"], then=send_home),
               Step("happy", 1.0), Step("tilt", face=spot["x"]))
        return True

    def message_home(self, msg):
        """The message is back in its place: take the cover away."""
        msg.gone = True
        self.screen_requests.append(("restore", msg.key))
        for fox in self.of("fox"):
            if fox.carrying is msg:
                fox.carrying = None

    def send_message_home(self, key):
        """You clicked the gap: the message flies straight back."""
        for msg in self.of("message"):
            if msg.key == key and msg.state != "home":
                if msg.carried_by is not None and getattr(msg.carried_by, "carrying", None) is msg:
                    msg.carried_by.carrying = None
                msg.state, msg.carried_by, msg.alpha = "returning", None, 1.0

    def cancel_message(self, key):
        """Something changed on screen (the window moved, say): the stolen picture just vanishes."""
        for msg in self.of("message"):
            if msg.key == key:
                self.message_home(msg)

    def _after_treasure(self):
        """What it does with its prize: sometimes plays, sometimes settles down to chew it up."""
        if self.rng.random() < 0.5:
            return [Step("sniff"), Step("chew", self.rng.uniform(4.5, 6.0)), Step("happy", 1.2), Step("groom", 2.0)]
        return [Step("playbow", 1.0), Step("roll", 1.6), Step("happy", 1.2)]

    def find_treasure(self, fox, spot):
        self._treasures += 1
        key = f"treasure{self._treasures}"
        self.grab_requests.append((key, spot))
        fox.carrying = self.add(Treasure(self, fox, key))

    def drop_treasure(self, fox):
        treasure = getattr(fox, "carrying", None)
        if treasure is not None:
            treasure.carried_by = None
            fox.carrying = None


    def folder_to_move(self, fox):
        """A desktop folder icon a fox could go and move, if folder mischief is on and it's been a while."""
        if not self.folder_spots or not self.mischief("folders") or self.of("folder") or self.folder_rest > 0:
            return None
        return min(self.folder_spots, key=lambda f: abs(f["x"] - fox.x))

    def move_folder(self, fox, spot=None, by_itself=True):
        """Sit under a folder icon, leap and pull it down, drag it off along the ground and drop it there."""
        from pet.items import Folder
        spot = spot or self.folder_to_move(fox)
        if spot is None or fox.held or fox.asleep and by_itself:
            return False
        s = self.scale
        left, right = spot.get("left", 0.0), spot.get("right", float(self.width))
        folder = self.add(Folder(self, spot["name"], spot["x"], spot["y"], spot["w"], spot["h"], (left, right)))
        folder.home = spot.get("home")
        self.folder_spots = [f for f in self.folder_spots if f["name"] != spot["name"]]
        self.folder_rest = 8 * 60  # not another one for a good while
        side = 1 if spot["x"] >= fox.x else -1
        under = self.clamp_x(spot["x"] - side * 10 * s)
        high = folder.floor() - spot["y"]  # how far above the ground it is
        away = spot["x"] + side * self.rng.uniform(140, 320) * s
        if away > right - 60 or away < left + 60:
            away = spot["x"] - side * self.rng.uniform(140, 320) * s
        away = max(left + 60.0, min(right - 60.0, away))

        def yank():
            if folder.state == "up":
                folder.state = "falling"

        def grab():
            if folder.gone or folder.state not in ("down", "falling"):
                return
            folder.state, folder.fox, fox.dragging_folder = "dragged", fox, folder

        def drop():
            if folder.fox is fox:
                folder.let_go()

        if high > 30 * s:  # up out of reach: a leap to pull it down
            reach = [Step("watch", 1.0, face=spot["x"]), Step("crouch", 0.6, face=spot["x"]),
                     Step("pounce", to_x=under, leap=min(70.0, high / s * 0.4 + 20), then=yank), Step("land"),
                     Step("tilt", 0.8, face=spot["x"])]
        else:
            reach = [Step("sniff", face=spot["x"], then=yank)]
        fox.do(Step("walk", to_x=under, speed=WALK * 1.5), *reach,
               Step("walk", follow=folder, speed=WALK * 1.5), Step("sniff", 0.5, then=grab),
               Step("walk", to_x=away, speed=WALK * 1.6, then=drop), Step("happy", 1.0), Step("playbow", 1.0))
        return True
