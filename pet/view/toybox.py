"""The tray icon's menu and the Toy Box window: foxes and items to put out, things to do, the season,
size, weather, sky and mischief settings."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import (QCheckBox, QGroupBox, QLabel, QMenu, QPushButton, QSystemTrayIcon, QTabWidget,
                               QVBoxLayout, QWidget)

from pet import __version__, save, seasons, sprites


class ToyBoxWindow(QWidget):
    """A small window listing every fox and item with a checkbox: tick what you want on the desktop.
    Opens when you click the fox icon in the tray."""

    def __init__(self, toybox):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.toybox = toybox
        self.setWindowTitle("Toy Box")
        self.setWindowIcon(toybox.tray.icon())
        self.layout_ = QVBoxLayout(self)
        self.boxes = {}  # (kind, name) -> its checkboxes (an item out in two seasons is on both seasons' tabs)
        foxes = QGroupBox("Foxes")
        fox_layout = QVBoxLayout(foxes)
        for palette, label in (("orange", "Orange fox"), ("grey", "Grey fox")):
            box = QCheckBox(label)
            box.toggled.connect(lambda on, p=palette: toybox._set_fox(p, on))
            fox_layout.addWidget(box)
            self.boxes[("fox", palette)] = [box]
        self.layout_.addWidget(foxes)
        # the items, on tabs: the ones out all year, then each season's
        self.tabs = QTabWidget()
        self.tabs.setUsesScrollButtons(False)  # wide enough to show every tab
        self.tab_of = {}
        for key, title in (("all", "All year"),) + tuple((s, s.title()) for s in seasons.SEASONS):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            names = [n for n, item in seasons.ITEMS.items()
                     if (key == "all") == (len(item["seasons"]) == len(seasons.SEASONS))
                     and (key == "all" or key in item["seasons"])]
            for name in sorted(names, key=lambda n: seasons.ITEMS[n]["label"]):
                box = QCheckBox(seasons.ITEMS[name]["label"])
                box.toggled.connect(lambda on, n=name: toybox._set_item(n, on))
                page_layout.addWidget(box)
                self.boxes.setdefault(("item", name), []).append(box)
            page_layout.addStretch(1)
            self.tab_of[key] = self.tabs.addTab(page, title)
        self.layout_.addWidget(self.tabs)
        mischief = QGroupBox("Mischief")
        mischief_layout = QVBoxLayout(mischief)
        for key, label in (("discord", "Steal Discord messages (and put them back)"),
                           ("treasure", "Dig up taskbar icons"),
                           ("folders", "Move folders about on the desktop")):
            box = QCheckBox(label)
            box.toggled.connect(lambda on, k=key: toybox._set_mischief(k, on))
            mischief_layout.addWidget(box)
            self.boxes[("mischief", key)] = [box]
        self.layout_.addWidget(mischief)
        self.note = QLabel()
        self.note.setWordWrap(True)
        self.layout_.addWidget(self.note)
        close = QPushButton("Close")
        close.clicked.connect(self.hide)
        self.layout_.addWidget(close)

    def refresh(self):
        """Show the current settings (without firing the checkboxes' handlers)."""
        settings, season = self.toybox.settings, self.toybox.world.season
        for (kind, name), boxes in self.boxes.items():
            if kind == "fox":
                on = bool(settings["foxes"].get(name))
            elif kind == "mischief":
                on = bool(settings.get("mischief", {}).get(name, True))
            else:
                on = bool(settings["items"].get(name, {}).get("out"))
            for box in boxes:
                box.blockSignals(True)
                box.setChecked(on)
                box.blockSignals(False)
        for key, index in self.tab_of.items():
            title = "All year" if key == "all" else key.title()
            self.tabs.setTabText(index, f"{title} (now)" if key == season else title)
        self.note.setText(f"It's {season} now. Things ticked on another season's tab come out when their season "
                          f"does.")

    def open(self):
        self.refresh()
        self.tabs.setCurrentIndex(self.tab_of[self.toybox.world.season])  # this season's things first
        self.adjustSize()
        self.show()
        self.raise_()
        self.activateWindow()


class ToyBox:
    """The tray icon's menu: which foxes and items are out, the season, pause and quit."""

    def __init__(self, app, desktop):
        self.app, self.desktop = app, desktop
        self.world, self.settings = desktop.world, desktop.settings
        icon = QIcon(str(sprites.SPRITE_DIR / "tray_icon.png"))
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip(f"Pixel Fox {__version__}")
        self.menu = QMenu()
        self.menu.aboutToShow.connect(self.build)
        self.tray.setContextMenu(self.menu)
        self.tray.show()
        self.window = ToyBoxWindow(self)
        self.tray.activated.connect(self._clicked)

    def _clicked(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):  # a left click
            self.window.open()

    def build(self):
        m = self.menu
        m.clear()
        m.addAction("Open the toy box...", self.window.open)
        m.addSection("Foxes")
        for palette, label in (("orange", "Orange fox"), ("grey", "Grey fox")):
            self._check(m, label, self.settings["foxes"].get(palette, False),
                        lambda on, p=palette: self._set_fox(p, on))
        items = seasons.items_for(self.world.season)
        all_year = [n for n in items if len(seasons.ITEMS[n]["seasons"]) == len(seasons.SEASONS)]
        for title, names in (("All year", all_year),
                             (f"This season ({self.world.season.title()})", [n for n in items if n not in all_year])):
            m.addSection(title)
            for name in sorted(names, key=lambda n: seasons.ITEMS[n]["label"]):
                item = self.settings["items"].setdefault(name, {"out": False, "x": None})
                self._check(m, seasons.ITEMS[name]["label"], item.get("out", False),
                            lambda on, n=name: self._set_item(n, on))
        m.addSection("Things to do")
        if self.world.tree() is not None and self.world.season == "autumn":
            m.addAction("Shake down an acorn", lambda: self.world.drop_acorn(self.world.tree()))
        if self.world.season == "winter":
            snow = m.addAction("Snow on the oak")
            snow.setCheckable(True)
            snow.setChecked(self.world.snowy)
            snow.toggled.connect(self._set_snow)
        if self.world.of("pumpkin"):
            m.addAction("Plant new pumpkins", self._replant)
        if self.world.decos_in_season():
            m.addAction("Add a pumpkin (to decorate with)", lambda: self.world.add_deco())
            m.addAction("Add a jack-o'-lantern", lambda: self.world.add_deco(jack=True))
            if self.world.of("deco"):
                m.addAction("Clear away the decorating pumpkins", self.world.clear_decos)
        if self.world.of("corn"):
            m.addAction("Plant new corn", self._replant_corn)
        if self.world.of("melon"):
            m.addAction("Plant new watermelons", self._replant_melons)
        if self.world.of("crop"):
            m.addAction("Replant the garden", self._replant_crops)
        if self.world.taskbar_spots:
            m.addAction("Dig up a taskbar treasure", self._dig)
        if self.world.folder_spots and self.world.mischief("folders"):
            m.addAction("Move a desktop folder", self._move_a_folder)
        if self.settings.get("folder_homes"):
            m.addAction("Put the desktop folders back", self.desktop.put_folders_back)
        m.addAction("Zoomies!", self._zoomies)
        m.addAction("Make it blustery", lambda: self.world.blustery())
        m.addAction("Make it rain", lambda: self.world.make_it("rain"))
        m.addAction("Make it snow", lambda: self.world.make_it("snow"))
        m.addAction("Steal a Discord message", self._steal_discord)
        visit = m.addMenu("Invite a visitor")
        for kind in seasons.VISITORS.get(self.world.season, ()) + ("owl",):
            label = {"jay": "Blue jay", "woolly": "Woolly bear caterpillar", "migrants": "Geese flying south",
                     "geese": "Geese stopping by to honk", "squirrel": "Squirrel",
                     "turkeys": "Wild turkeys", "crows": "Crows", "junebug": "June beetle",
                     "ladybug": "Ladybug", "cicada": "Cicada", "butterflies": "Butterflies",
                     "songbirds": "Songbirds", "owl": "Owl (it usually comes at night)"}.get(kind, kind.title())
            visit.addAction(label, lambda k=kind: self.world.invite_visitor(k))

        m.addSeparator()
        season_menu = m.addMenu("Season")
        group = QActionGroup(season_menu)
        current = self.settings.get("season", "auto")
        auto_label = f"Automatic (now {seasons.season_for(self.world.now().date()).title()})"
        for key, label in (("auto", auto_label), ("winter", "Winter"), ("spring", "Spring"), ("summer", "Summer"),
                           ("autumn", "Autumn")):
            action = season_menu.addAction(label, lambda k=key: self._set_season(k))
            action.setCheckable(True)
            action.setChecked(current == key)
            group.addAction(action)
        self._check(m, self._weather_label(), self.settings.get("weather", True), self._set_weather)
        self._check(m, "Sun and moon clock in the sky (sun 6 AM-6 PM, moon 6 PM-6 AM)",
                    self.settings.get("sky", True), self._set_sky)
        size_menu = m.addMenu("Size")
        sizes = QActionGroup(size_menu)
        for value in (1, 2, 3):
            action = size_menu.addAction(f"{value}x", lambda v=value: self._set_scale(v))
            action.setCheckable(True)
            action.setChecked(self.world.scale == value)
            sizes.addAction(action)
        self._check(m, "Pause", self.world.paused, self._set_paused)
        m.addSeparator()
        m.addAction("Quit", self.quit)

    def _check(self, menu, label, checked, on_toggle):
        action = QAction(label, menu)
        action.setCheckable(True)
        action.setChecked(checked)
        action.toggled.connect(on_toggle)
        menu.addAction(action)
        return action

    def _changed(self):
        save.store(self.settings)
        self.world.rebuild()
        self.desktop.update()
        if self.window.isVisible():
            self.window.refresh()

    def _set_mischief(self, key, on):
        self.settings.setdefault("mischief", {})[key] = on
        save.store(self.settings)
        if key == "discord" and not on:
            self.world.discord_spot = None

    def _set_fox(self, palette, on):
        self.settings["foxes"][palette] = on
        self._changed()

    def _set_item(self, name, on):
        self.settings["items"].setdefault(name, {"out": on, "x": None})["out"] = on
        self._changed()

    def _steal_discord(self):
        """Look for a Discord message now and send a fox after it (if one is showing)."""
        self.desktop.look_for_discord()
        foxes = [f for f in self.world.of("fox") if not f.held and not f.asleep]
        if self.world.discord_spot is None:
            self.tray.showMessage("Pixel Fox", "No Discord message in view to steal (is Discord open and visible?)")
        elif foxes:
            self.world.steal_message(min(foxes, key=lambda f: abs(f.x - self.world.discord_spot["x"])))

    def _zoomies(self):
        foxes = [f for f in self.world.of("fox") if not f.held]
        if foxes:
            fox = self.world.rng.choice(foxes)
            fox.do(*fox._zoomies())

    def _dig(self):
        foxes = [f for f in self.world.of("fox") if not f.held]
        if foxes:
            self.world.dig_for_treasure(self.world.rng.choice(foxes))

    def _replant_corn(self):
        self.world.plant_corn(replant=True)
        save.store(self.settings)

    def _replant_melons(self):
        self.world.grow_melons(replant=True)
        save.store(self.settings)

    def _replant_crops(self):
        for crop in list(self.world.of("crop")):
            self.world.plant_crop(crop.variant, replant=True)
        save.store(self.settings)

    def _set_sky(self, on):
        self.settings["sky"] = bool(on)
        save.store(self.settings)
        self.desktop.sky.place()

    def _weather_label(self):
        report = self.desktop.weather.current() if self.settings.get("weather", True) else None
        now = {None: "", "rain": " (raining now)", "snow": " (snowing now)"}[report.falling if report else None]
        return "Local weather (rain and snow)" + now

    def _set_weather(self, on):
        self.settings["weather"] = bool(on)
        save.store(self.settings)
        if on:
            self.desktop.weather.refresh()

    def _set_snow(self, on):
        self.settings["snow"] = bool(on)
        save.store(self.settings)

    def _move_a_folder(self):
        foxes = [f for f in self.world.of("fox") if not f.held and f.dragging_folder is None]
        if foxes and not self.world.of("folder") and self.world.folder_spots:
            fox = self.world.rng.choice(foxes)
            spot = min(self.world.folder_spots, key=lambda f: abs(f["x"] - fox.x))
            self.world.move_folder(fox, spot, by_itself=False)

    def _replant(self):
        self.world.grow_pumpkins(replant=True)
        save.store(self.settings)

    def _set_season(self, key):
        self.settings["season"] = key
        self._changed()

    def _set_scale(self, value):
        self.settings["scale"] = value
        self.world.scale = value
        self._changed()

    def _set_paused(self, on):
        self.world.paused = on

    def quit(self):
        tree = self.world.tree()
        if tree is not None:
            self.settings["items"][tree.variant]["x"] = round(tree.x)
        save.store(self.settings)
        self.tray.hide()
        self.app.quit()
