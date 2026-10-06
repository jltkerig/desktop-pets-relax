# Notes for Claude

## Save tokens: read the map, then only the file you need

The code is split into small files by subject (most under 500 lines), each starting with a docstring saying
what's in it. Don't read whole packages: find the file below, read it (or grep for the name), change it.

| Where | What |
|---|---|
| `pet/world/` | The world, no Qt. `World` (in `__init__.py`) is built from: `core` (what's out: `rebuild`, season/snow, `add`/`of`, `update` each frame, and the helpers `clamp_x(x, margin)` to keep an x on the strip and `spot_for(name, default)` for an item's saved spot), `garden` (pumpkin/melon patches, decorating pumpkins, corn, vegetable rows, hoe), `visits` (leaves, acorns, which visitors turn up), `foxplay` (a fox alone: naps, chasing, pool, nibbling, climbing, fetching thrown balls/cobs), `friends` (two foxes), `mischief` (taskbar treasure, Discord, desktop folders), `outdoors` (wind, rain/snow, night glows, fireflies, paw prints), `yardfun` (the newer seasonal things: putting them out, puddles, the kite, toys thrown, extra fox choices via `season_options`), `fun_winter` / `fun_spring` / `fun_summer` (the games foxes play with them). All methods share `self`. |
| `pet/fox.py` | A fox's moods, its plan of `Step`s, and `choose()` (the weighted list of things to do). |
| `pet/items/` | Things: `base` (small falling bits), `garden` (Pumpkin, DecoPumpkin, Melon, Crop, Corn, CornCob, Produce), `trees` (Tree, Birch), `yard` (Prop, Hat, Den, Climbable...), `toys` (Treasure ball, Message, Folder), `sky` (Glow, Firefly, PawPrint, RainDrop, SnowFlake), `play` (YardThing: base for the newer draggable yard things; Ball: a throwable toy), `winter` (Snowman, Carrot, SnowballPile, Snowball, Pond, Feeder, Gifts), `spring` (Puddle, MudPrint, Nest, Kite, WateringCan), `summer` (Sprinkler, BeachBall, Hammock, FireflyJar, Sunflowers). |
| `pet/visitors/` | Creatures: `base` (Visitor, Bubble, Perch), `autumn` (squirrel, jay, woolly, geese, frog, turkeys), `crows`, `bugs` (inchworm, butterfly, beetles, cicada, spider), `spring` (flower butterflies, songbirds, bunnies), `winter` (cardinals and chickadees at the feeder), `night` (owl). |
| `pet/view/` | Qt: `frames` (sprite frames, drag settings), `windows` (monitor windows, sun/moon window), `stage` (main loop, mouse, taskbar, Discord, folders), `toybox` (tray menu: Things to do / Weather / Invite a visitor / Mischief / Settings submenus), `toybox_window` (the Toy Box window: foxes, items by season tab, mischief), `discord_pics`. |
| `pet/seasons.py` | Which items and visitors belong to each season, and the visitors' menu names (`VISITOR_LABELS`). `pet/save.py`: settings file and its defaults. |
| `pet/sky.py`, `pet/weather.py`, `pet/daylight.py`, `pet/updates.py` | Sun/moon clock, local weather, night/day, checking GitHub for a newer version (tray menu). `pet/desktop_icons.py`, `pet/discord.py`: Windows-only helpers. |
| `art/world_art/` | Sprite drawing, one file per theme: `common`, `trees` (oak and birch), `foliage` (leafy crowns built from lit leaf clusters, used by `trees`), `critters`, `autumn`, `yard`, `winter`, `spring`, `summer`, `garden`, `sky`. Each has `sprites()` listing its sprites. `art/fox_art.py`: the foxes. |
| `tests/` | One file per topic (`test_foxes`, `test_seasons`, `test_garden`, `test_visitors`, `test_mischief`, `test_weather_sky`, `test_app`, `test_yard_fun` for the newer seasonal things, `test_menu_and_drawing` for the tray menu, Toy Box and redrawing). Every file imports `helpers` first (scratch user-data folder, no internet). |

**Adding a new yard thing** (something to drag about and click): subclass `YardThing` in `pet/items/<season>.py`,
add it to `YARD_ITEMS` in `pet/world/yardfun.py` (class and first spot), to `seasons.ITEMS` and `save.DEFAULTS`,
and give foxes a game with it in `season_options` plus a method in `fun_<season>.py`. Things you pick up and
throw set `carryable = True` and have `pick_up()` and `throw(vx, vy)` (the Stage does the rest).

**Adding something new:** put it in the file for its subject (a new summer item: `pet/items/yard.py` or
`garden.py`, its art in `art/world_art/summer.py` and that file's `sprites()`, its season in `seasons.py`,
its tests in the matching test file). If a file grows past ~600 lines, split it by subject the same way and
update this table. Import from the package (`from pet.items import Pumpkin`); add new names to the package's
`__init__.py`.

**Drawing:** each frame `Stage.tick` compares how every thing looks (`Stage.looks()`: rect, sprite, frame,
facing, alpha) with the last frame and redraws only the parts that changed. If you add something whose look
changes some other way (not through its sprite, frame, place or alpha), call `Stage.update()` to redraw it all.

**Changelog:** read only the top few entries (`head -40 CHANGELOG.md`), not the whole file.

## Versions: check them first, bump them always

- The current version is `__version__` in `pet/__init__.py`. `CHANGELOG.md` lists every version, newest
  first, with what changed. The tray icon's tooltip shows it too ("Pixel Fox 1.1.0").
- **Before you start:** compare `pet.__version__` with the version you (or the user) last knew, and read the
  changelog entries newer than that.
- **With every change you commit:** bump `__version__` (major.minor.patch: patch for fixes, minor for new
  features such as a new visitor or item, major for a big rework) and add a `## <version>` section at the top
  of `CHANGELOG.md` saying what changed. `tests/test_app.py` checks the two match.
- This matters for more than record keeping: `update.ps1` (run by `start.ps1`) only installs an update when
  the version on GitHub's `main` is higher than the one on the computer. Forget the bump and nobody gets it.
  Keep `__version__ = "x.y.z"` in exactly that form; the updater reads it with a pattern.

## Branches: push straight to main, no other branches

- The owner wants `main` to be the only branch. Commit and push straight to `main`
  (`git push origin HEAD:main`), even if the session told you to use a `claude/...` branch.
- Only if pushing to `main` is refused: push your branch, open a pull request into `main` and merge it
  yourself straight away. The repo has "Automatically delete head branches" turned on, so GitHub removes the
  branch once it's merged. Cloud sessions can't delete branches themselves, so never leave one unmerged.
- The owner may ask you to hold commits locally ("don't push until I say"): then commit, and push only when
  told.

## Working on it

- Run the tests with `python -m unittest discover -s tests` (needs Pillow; PySide6 only to run the app).
  `test_a_location_can_be_set_by_hand` fails on machines whose clock is set to UTC (cloud sandboxes); that's
  the environment, not the code.
- Sprites are drawn by code in `art/` and saved to `art/sprites/` (a PNG strip and a JSON per sprite).
  `python art/make_art.py` redraws them all; commit the PNG and JSON files it writes. After a refactor of
  the art code, `git status art/sprites` should show nothing changed.
- `Pixel Fox.exe` and `Pixel Fox.scr` (the screen saver) are both built from `launcher/launcher.c` by
  `launcher/build.sh` (MinGW-w64 cross compiler). They only start `start.ps1` / `pixelfox.py`, so they rarely
  need rebuilding; if you change launcher.c, rebuild and commit both.
- The screen saver (`pet/saver.py`) has tests that need PySide6; they're skipped where it isn't installed.
- `pet/world/` and everything it uses has no Qt, so it can be tested. Keep Qt in `pet/view/` (and saver.py).
- `pet/weather.py` asks Open-Meteo for the local weather on a background thread. The tests replace
  `weather.fetch` so they never touch the internet; keep it that way. Cloud sandboxes may block
  `api.open-meteo.com` anyway, and the app is built to carry on quietly without a report.
- The sun and moon are a clock (`pet/sky.py`): sun 6 AM-6 PM, moon 6 PM-6 AM, by the hour, not astronomy
  (the owner wants to read the time from them).
- The fox's choice list in `pet/fox.py` draws from the world's rng: add new choices at the end with weight 0
  when they don't apply, so existing tests keep their random sequences.
- Tree art: the owner prefers the original oak and birch (before 1.16.0). Ask before reworking them, and
  show a picture first.
