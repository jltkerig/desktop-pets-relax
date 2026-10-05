"""Shared set-up for the tests. Import this first in every test file: it points saving at a scratch
folder (never your real user-data) and stops the tests asking the internet about the weather,
before anything from pet is imported."""
import datetime
import os
import random
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["PIXELFOX_USER_DIR"] = tempfile.mkdtemp(prefix="pixelfox-test-")  # never the real user-data


from pet import save  # noqa: E402  
from pet.world import World  # noqa: E402
from pet import weather  # noqa: E402

REAL_FETCH = weather.fetch
weather.fetch = lambda lat, lon: None  # tests never ask the internet about the weather
from pet import updates  # noqa: E402
updates.fetch = lambda timeout=10: None  # nor about updates

assert "pixelfox-test-" in str(save.USER_DIR), "tests must never use the real user-data folder"


def make_world(season="autumn", hour=14, seed=3, **foxes):
    settings = save.load(Path(os.environ["PIXELFOX_USER_DIR"]) / "missing.json")
    settings["season"] = season
    if foxes:
        settings["foxes"] = foxes
    clock = [datetime.datetime(2026, 10, 4, hour, 0)]
    world = World(1920, 1040, settings, rng=random.Random(seed), clock=lambda: clock[0])
    world.timers = {"leaf": 10 ** 9, "acorn": 10 ** 9, "visitor": 10 ** 9}  # nothing turns up by itself
    return world, clock

def run(world, clock, seconds, fps=30):
    for _ in range(int(seconds * fps)):
        clock[0] += datetime.timedelta(seconds=1 / fps)
        world.update(1 / fps, (-1000.0, -1000.0))

def crows_with_scarecrow(seed=1):
    """A world with the scarecrow out (no foxes to scare anyone) and a party of crows, settled in."""
    world, clock = make_world(seed=seed, orange=False, grey=False)
    scarecrow = next(p for p in world.of("prop") if p.variant == "scarecrow")
    party = world.invite_visitor("crows").party
    party.long, party.stay = True, 10 ** 6
    run(world, clock, 15, fps=20)
    return world, clock, scarecrow, party

def season_world(season, seed=3, **foxes):
    world, clock = make_world(season, seed=seed, **{"orange": False, "grey": False, **foxes})
    world.settings["snow"] = False
    run(world, clock, 0.1)
    return world, clock

def item(world, variant):
    return next(t for t in world.things if getattr(t, "variant", None) == variant)

def loose_ball(world, x=300.0, height=200):
    import types
    from pet.items import Treasure
    ball = world.add(Treasure(world, types.SimpleNamespace(x=x), "ball"))
    ball.carried_by = None
    ball.x, ball.y = x, world.ground - height
    return ball

def qt_available():
    try:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        return True
    except Exception:  # PySide6 or its system libraries missing: only the Qt-free tests run
        return False
