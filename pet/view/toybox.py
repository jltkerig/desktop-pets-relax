"""The tray icon's menu: the foxes, then things to do, the weather, visitors and mischief, and the settings
(season, size, the sky) in their own submenus. The items to put out are in the Toy Box window
(toybox_window.py), which opens when you click the tray icon."""
from pathlib import Path

from PySide6.QtCore import QProcess
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from pet import __version__, save, seasons, sprites, updates
from .toybox_window import MISCHIEF, ToyBoxWindow


class ToyBox:
    """The tray icon and its menu."""

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
        self.updates = updates.Checker(__version__).start()  # is there a newer Pixel Fox on GitHub?
        self.tray.activated.connect(self._clicked)

    def _clicked(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):  # a left click
            self.window.open()

    def build(self):
        """The menu, made fresh each time it opens (so it only offers what makes sense right now)."""
        m = self.menu
        m.clear()
        newer = self.updates.available()
        title = m.addAction(f"Pixel Fox {__version__}" + (f"  (version {newer} is out)" if newer else ""))
        title.setEnabled(False)
        m.addAction("Open the toy box (things to put out)...", self.window.open)
        m.addSection("Foxes")
        for palette, label in (("orange", "Orange fox"), ("grey", "Grey fox")):
            self._check(m, label, self.settings["foxes"].get(palette, False),
                        lambda on, p=palette: self._set_fox(p, on))
        m.addSeparator()
        self._things_to_do(m.addMenu("Things to do"))
        self._weather_menu(m.addMenu("Weather"))
        visit = m.addMenu("Invite a visitor")
        for kind in seasons.VISITORS.get(self.world.season, ()) + ("owl",):
            visit.addAction(seasons.VISITOR_LABELS.get(kind, kind.title()),
                            lambda k=kind: self.world.invite_visitor(k))
        self._mischief_menu(m.addMenu("Mischief"))
        self._settings_menu(m.addMenu("Settings"))
        m.addSeparator()
        self._check(m, "Pause", self.world.paused, self._set_paused)
        m.addAction(f"Update to {newer} and restart" if newer else "Check for updates and restart", self._update)
        m.addAction("Quit", self.quit)

    def _things_to_do(self, menu):
        """Zoomies, and the garden and seasonal jobs that fit what's out right now."""
        w = self.world
        menu.addAction("Zoomies!", self._zoomies)
        if w.tree() is not None and w.season == "autumn":
            menu.addAction("Shake down an acorn", lambda: w.drop_acorn(w.tree()))
        if w.decos_in_season():
            menu.addAction("Add a pumpkin (to decorate with)", lambda: w.add_deco())
            menu.addAction("Add a jack-o'-lantern", lambda: w.add_deco(jack=True))
            if w.of("deco"):
                menu.addAction("Clear away the decorating pumpkins", w.clear_decos)
        garden = [(kind, label, action) for kind, label, action in (
            ("pumpkin", "Plant new pumpkins", self._replant), ("corn", "Plant new corn", self._replant_corn),
            ("melon", "Plant new watermelons", self._replant_melons), ("crop", "Replant the garden", self._replant_crops))
            if w.of(kind)]
        if garden:
            menu.addSection("Garden")
            for _, label, action in garden:
                menu.addAction(label, action)

    def _weather_menu(self, menu):
        w = self.world
        menu.addAction("Make it rain", lambda: w.make_it("rain"))
        menu.addAction("Make it snow", lambda: w.make_it("snow"))
        menu.addAction("Make it blustery", lambda: w.blustery())
        menu.addSeparator()
        self._check(menu, self._weather_label(), self.settings.get("weather", True), self._set_weather)
        if w.season == "winter":
            self._check(menu, "Snow on the oak", w.snowy, self._set_snow)

    def _mischief_menu(self, menu):
        """Mischief to start now, then what the foxes are allowed to get up to by themselves."""
        w = self.world
        if w.mischief("discord"):
            menu.addAction("Steal a Discord message", self._steal_discord)
        if w.taskbar_spots and w.mischief("treasure"):
            menu.addAction("Dig up a taskbar treasure", self._dig)
        if w.folder_spots and w.mischief("folders"):
            menu.addAction("Move a desktop folder", self._move_a_folder)
        if self.settings.get("folder_homes"):
            menu.addAction("Put the desktop folders back", self.desktop.put_folders_back)
        menu.addSection("Allowed")
        for key, label in MISCHIEF:
            self._check(menu, label, bool(self.settings.get("mischief", {}).get(key, True)),
                        lambda on, k=key: self._set_mischief(k, on))

    def _settings_menu(self, menu):
        season_menu = menu.addMenu("Season")
        group = QActionGroup(season_menu)
        current = self.settings.get("season", "auto")
        auto_label = f"Automatic (now {seasons.season_for(self.world.now().date()).title()})"
        for key, label in (("auto", auto_label), ("winter", "Winter"), ("spring", "Spring"), ("summer", "Summer"),
                           ("autumn", "Autumn")):
            action = season_menu.addAction(label, lambda k=key: self._set_season(k))
            action.setCheckable(True)
            action.setChecked(current == key)
            group.addAction(action)
        size_menu = menu.addMenu("Size")
        sizes = QActionGroup(size_menu)
        for value in (1, 2, 3):
            action = size_menu.addAction(f"{value}x", lambda v=value: self._set_scale(v))
            action.setCheckable(True)
            action.setChecked(self.world.scale == value)
            sizes.addAction(action)
        self._check(menu, "Sun and moon clock in the sky (sun 6 AM-6 PM, moon 6 PM-6 AM)",
                    self.settings.get("sky", True), self._set_sky)

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
        if self.window.isVisible():
            self.window.refresh()

    def _set_fox(self, palette, on):
        self.settings["foxes"][palette] = on
        self._changed()

    def _set_item(self, name, on):
        self._set_items([name], on)

    def _set_items(self, names, on):
        """Put these items out (or take them in), all at once."""
        for name in names:
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

    def _update(self):
        """Close, then start again through start.ps1, which updates first (a moment later, once this has gone)."""
        start = Path(__file__).resolve().parents[2] / "start.ps1"
        QProcess.startDetached("powershell", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                                              "-Command", f"Start-Sleep -Seconds 2; & '{start}'"])
        self.app.quit()

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
