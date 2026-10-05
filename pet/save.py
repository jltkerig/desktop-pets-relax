"""What's out on the desktop and where, kept in user-data/world.json between runs."""
import json
import os
from pathlib import Path

def _user_dir():
    """user-data next to the app, or %LOCALAPPDATA%\\PixelFox if the app's folder is read-only."""
    if os.environ.get("PIXELFOX_USER_DIR"):
        return Path(os.environ["PIXELFOX_USER_DIR"])
    beside = Path(__file__).resolve().parents[1] / "user-data"
    try:
        beside.mkdir(parents=True, exist_ok=True)
        probe = beside / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return beside
    except OSError:
        return Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "PixelFox"


USER_DIR = _user_dir()
WORLD_FILE = USER_DIR / "world.json"

DEFAULTS = {
    "foxes": {"orange": True, "grey": True},
    # x None: placed automatically. The pumpkin patch keeps each pumpkin's place and planting time.
    "items": {"oak": {"out": True, "x": None}, "pumpkins": {"out": True, "x": None, "patch": []},
              "scarecrow": {"out": True, "x": None}, "corn": {"out": True, "x": None, "planted": None},
              "hoe": {"out": True, "x": None}, "den": {"out": True, "x": None},
              "barrels": {"out": True, "x": None}, "haystack": {"out": True, "x": None},
              "sled": {"out": True, "x": None}, "stump": {"out": True, "x": None},
              "xmas_tree": {"out": True, "x": None}, "daffodils": {"out": True, "x": None},
              "tulips": {"out": True, "x": None}, "violets": {"out": True, "x": None},
              "birch": {"out": True, "x": None}, "woodstack": {"out": True, "x": None},
              "apple_barrel": {"out": True, "x": None}, "well": {"out": True, "x": None},
              "radishes": {"out": True, "x": None, "planted": None},
              "lettuce": {"out": True, "x": None, "planted": None},
              "slide": {"out": True, "x": None}, "pool": {"out": True, "x": None},
              "watermelons": {"out": True, "x": None, "patch": []},
              "tomatoes": {"out": True, "x": None, "planted": None},
              "dahlias": {"out": True, "x": None}, "dandelions": {"out": True, "x": None},
              "cattails": {"out": True, "x": None, "planted": None}},
    # Discord message stealing, taskbar treasure digging, moving folder icons about on the desktop
    "mischief": {"discord": True, "treasure": True, "folders": True},
    "decorations": [],   # pumpkins put out to decorate: {x, size, shape, jack, and on/level/dx if on something}
    "folder_homes": {},  # where each desktop folder icon was before a fox first moved it: name -> [x, y]
    "season": "auto",
    "snow": "auto",  # snow on the winter oak: "auto" (some days), or true / false as chosen from the tray menu
    "scale": 2,
    "weather": True,  # rain and snow (and snowy winter days) from the local weather; see pet/weather.py
}


def load(path=None):
    path = Path(path or WORLD_FILE)
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    data = json.loads(json.dumps(DEFAULTS))  # a deep copy
    if isinstance(saved, dict):
        for key in ("season", "scale", "snow", "weather"):
            if key in saved:
                data[key] = saved[key]
        for key in ("foxes", "items", "mischief"):
            if isinstance(saved.get(key), dict):
                for name, value in saved[key].items():
                    if name in data[key] and isinstance(value, type(data[key][name])):
                        data[key][name] = value
    decos = saved.get("decorations") if isinstance(saved, dict) else None
    if isinstance(decos, list):
        data["decorations"] = [d for d in decos if isinstance(d, dict) and isinstance(d.get("x"), (int, float))][:60]
    homes = saved.get("folder_homes") if isinstance(saved, dict) else None
    if isinstance(homes, dict):
        data["folder_homes"] = {name: [int(p[0]), int(p[1])] for name, p in homes.items()
                                if isinstance(name, str) and isinstance(p, list) and len(p) == 2
                                and all(isinstance(v, (int, float)) for v in p)}
    if data["season"] not in ("auto", "winter", "spring", "summer", "autumn"):
        data["season"] = "auto"
    if data["scale"] not in (1, 2, 3):
        data["scale"] = 2
    if data["snow"] not in ("auto", True, False):
        data["snow"] = "auto"
    if data["weather"] not in (True, False):
        data["weather"] = True
    return data


def store(data, path=None):
    path = Path(path or WORLD_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
