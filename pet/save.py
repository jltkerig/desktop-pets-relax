"""What's out on the desktop and where, kept in user-data/world.json between runs."""
import json
import os
from pathlib import Path

USER_DIR = Path(os.environ.get("PIXELFOX_USER_DIR") or Path(__file__).resolve().parents[1] / "user-data")
WORLD_FILE = USER_DIR / "world.json"

DEFAULTS = {
    "foxes": {"orange": True, "grey": True},
    # x None: placed automatically. The pumpkin patch keeps each pumpkin's place and planting time.
    "items": {"oak": {"out": True, "x": None}, "pumpkins": {"out": True, "x": None, "patch": []},
              "scarecrow": {"out": True, "x": None}},
    "season": "auto",
    "scale": 2,
}


def load(path=None):
    path = Path(path or WORLD_FILE)
    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    data = json.loads(json.dumps(DEFAULTS))  # a deep copy
    if isinstance(saved, dict):
        for key in ("season", "scale"):
            if key in saved:
                data[key] = saved[key]
        for key in ("foxes", "items"):
            if isinstance(saved.get(key), dict):
                for name, value in saved[key].items():
                    if name in data[key] and isinstance(value, type(data[key][name])):
                        data[key][name] = value
    if data["season"] not in ("auto", "winter", "spring", "summer", "autumn"):
        data["season"] = "auto"
    if data["scale"] not in (1, 2, 3):
        data["scale"] = 2
    return data


def store(data, path=None):
    path = Path(path or WORLD_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
