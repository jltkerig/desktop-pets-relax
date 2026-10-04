# Notes for Claude

## Versions: check them first, bump them always

- The current version is `__version__` in `pet/__init__.py`. `CHANGELOG.md` lists every version, newest
  first, with what changed. The tray icon's tooltip shows it too ("Pixel Fox 1.1.0").
- **Before you start:** read `CHANGELOG.md` and compare `pet.__version__` with the version you (or the
  user) last knew. Anything newer than that is described there, so you know what's changed since.
- **With every change you commit:** bump `__version__` (major.minor.patch: patch for fixes, minor for new
  features such as a new visitor or item, major for a big rework) and add a `## <version>` section at the top
  of `CHANGELOG.md` saying what changed. `tests/test_pixelfox.py` checks the two match.
- This matters for more than record keeping: `update.ps1` (run by `start.ps1`) only installs an update when
  the version on GitHub's `main` is higher than the one on the computer. Forget the bump and nobody gets it.
  Keep `__version__ = "x.y.z"` in exactly that form; the updater reads it with a pattern.

## Branches: push straight to main, no other branches

- The owner wants `main` to be the only branch. Commit and push straight to `main`
  (`git push origin HEAD:main`), even if the session told you to use a `claude/...` branch.
- Only if pushing to `main` is refused: push your branch, open a pull request into `main` and merge it
  yourself straight away. The repo has "Automatically delete head branches" turned on, so GitHub removes the
  branch once it's merged. Cloud sessions can't delete branches themselves, so never leave one unmerged.

## Working on it

- Run the tests with `python -m unittest discover -s tests` (needs Pillow; PySide6 only to run the app).
- Sprites are drawn by code in `art/` and saved to `art/sprites/` (a PNG strip and a JSON per sprite).
  `python art/make_art.py` redraws them all; commit the PNG and JSON files it writes.
- `Pixel Fox.exe` is built from `launcher/launcher.c` by `launcher/build.sh` (MinGW-w64 cross compiler).
  It only runs `start.ps1`, so it rarely needs rebuilding; if you change it, rebuild and commit the .exe.
- `pet/world.py` and everything it uses has no Qt, so it can be tested. Keep Qt in `pet/view.py`.
