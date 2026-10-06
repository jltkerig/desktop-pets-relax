"""The Toy Box window: every fox and item with a checkbox (the items on a tab for all year and one for each
season), and the mischief settings. Opens when you click the fox icon in the tray (see toybox.py)."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton, QTabWidget,
                               QVBoxLayout, QWidget)

from pet import __version__, seasons

MISCHIEF = (("discord", "Steal Discord messages (and put them back)"),
            ("treasure", "Dig up taskbar icons"),
            ("folders", "Move folders about on the desktop"))
ONE_COLUMN = 7  # a tab with more items than this lays them out in two columns


def tab_items(key):
    """The items on a tab ("all": the ones out all year; else a season's own), sorted by label."""
    names = [n for n, item in seasons.ITEMS.items()
             if (key == "all") == (len(item["seasons"]) == len(seasons.SEASONS))
             and (key == "all" or key in item["seasons"])]
    return sorted(names, key=lambda n: seasons.ITEMS[n]["label"])


class ToyBoxWindow(QWidget):
    """A small window listing every fox and item with a checkbox: tick what you want on the desktop."""

    def __init__(self, toybox):
        super().__init__(None, Qt.Tool | Qt.WindowStaysOnTopHint)
        self.toybox = toybox
        self.setWindowTitle(f"Toy Box - Pixel Fox {__version__}")
        self.setWindowIcon(toybox.tray.icon())
        self.layout_ = QVBoxLayout(self)
        self.boxes = {}  # (kind, name) -> its checkboxes (an item out in two seasons is on both seasons' tabs)
        foxes = QGroupBox("Foxes")
        fox_layout = QHBoxLayout(foxes)
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
            self.tab_of[key] = self.tabs.addTab(self._tab(key), title)
        self.layout_.addWidget(self.tabs)
        mischief = QGroupBox("Mischief")
        mischief_layout = QVBoxLayout(mischief)
        for key, label in MISCHIEF:
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

    def _tab(self, key):
        """One tab: its items' checkboxes (in two columns if there are many), and put-all-out / take-all-in."""
        page = QWidget()
        page_layout = QVBoxLayout(page)
        grid = QGridLayout()
        names = tab_items(key)
        columns = 2 if len(names) > ONE_COLUMN else 1
        rows = (len(names) + columns - 1) // columns
        for i, name in enumerate(names):  # down the first column, then the second
            box = QCheckBox(seasons.ITEMS[name]["label"])
            box.toggled.connect(lambda on, n=name: self.toybox._set_item(n, on))
            grid.addWidget(box, i % rows, i // rows)
            self.boxes.setdefault(("item", name), []).append(box)
        page_layout.addLayout(grid)
        page_layout.addStretch(1)
        buttons = QHBoxLayout()
        for label, on in (("Put all out", True), ("Take all in", False)):
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, o=on: self.toybox._set_items(names, o))
            buttons.addWidget(button)
        buttons.addStretch(1)
        page_layout.addLayout(buttons)
        return page

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
