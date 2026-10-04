# Notes for Claude

## Versions: check them first, bump them always

- The current version is `__version__` in `pet/__init__.py`. `CHANGELOG.md` lists every version, newest
  first, with what changed. The tray icon's tooltip shows it too ("Pixel Fox 1.1.0").
- **Before you start:** read `CHANGELOG.md` and compare `pet.__version__` with the version you (or the
  user) last knew. Anything newer than that is described there, so you know what's changed since.
- **With every change you commit:** bump `__version__` (major.minor.patch: patch for fixes, minor for new
  features such as a new visitor or item, major for a big rework) and add a `## <version>` section at the top
  of `CHANGELOG.md` saying what changed. `tests/test_pixelfox.py` checks the two match.

## Branches: always end up on main, with nothing left over

- The owner wants `main` to be the only branch. Don't leave work sitting on another branch.
- Cloud sessions can push but can't delete branches. So: push your branch, open a pull request into `main`,
  and merge it yourself straight away. The repo has "Automatically delete head branches" turned on, so GitHub
  removes the branch once it's merged.
- If you can push straight to `main` instead, that's fine too.

## Working on it

- Run the tests with `python -m unittest discover -s tests` (needs Pillow; PySide6 only to run the app).
- Sprites are drawn by code in `art/` and saved to `art/sprites/` (a PNG strip and a JSON per sprite).
  `python art/make_art.py` redraws them all; commit the PNG and JSON files it writes.
- `pet/world.py` and everything it uses has no Qt, so it can be tested. Keep Qt in `pet/view.py`.
