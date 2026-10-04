# Changelog

Every change to Pixel Fox gets a new version here, newest first. The version is also in
`pet/__init__.py` (`__version__`) and shows in the tray icon's tooltip. See `CLAUDE.md`.

## 1.2.0

- **Updates itself:** starting Pixel Fox (Pixel Fox.cmd or start.ps1) first checks GitHub for a newer version
  and installs it, then starts. A git clone is updated with `git pull`; a downloaded ZIP by downloading the
  newest ZIP over the top. Settings in `user-data` are kept. Offline or anything going wrong: it just starts
  the version you have. Skipped while Pixel Fox is running, or if a file named `no-update` is in its folder,
  or with `.\start.ps1 -NoUpdate`. See `update.ps1`.

## 1.1.2

- `CLAUDE.md`: Claude sessions push straight to `main`; a pull request (merged at once) only if that's refused.

## 1.1.1

- `CLAUDE.md`: Claude sessions merge their work into `main` through a pull request, so no extra branches
  are left behind (GitHub deletes them on merge).

## 1.1.0

- **Wild turkeys** (autumn): a flock of 3 to 6 runs in from one edge, stops together to look around,
  peck and gobble (with a GOBBLE! bubble, and often answered by the others), then dashes on. After a
  few stops they run off the far side. The foxes notice the gobbling the same way they notice a goose's honk.
- **Crows** (all year): a party of 2 to 4 flies in and lands close together, on the oak's branches, on
  items (the scarecrow's hat and arms, the haystack, the barrels, the den, ripe pumpkins) or on the ground.
  They hop, caw and cock their heads. On a long visit they come down to look at things and play with them:
  rolling acorns and corn cobs, flipping leaves, tugging straw from the haystack, tapping pumpkins, startling
  the scarecrow, or carrying an acorn up to a perch and dropping it. They leave together, or straight away
  if you click one or a fox dashes at them.
- New sprites: `turkey_*`, `crow_*`, `gobble_bubble`, `caw_bubble`.
- "Invite a visitor" lists **Wild turkeys** and **Crows**.
- Version tracking: `pet.__version__`, this changelog and `CLAUDE.md`.

## 1.0.0

- Everything before version tracking began (up to commit `69589a8`, "Stolen Discord messages always go
  home, and a cover can never get stuck"): the two foxes, the seasons, the toy box, the oak, the autumn items
  and the squirrel, blue jay, woolly bear, geese and frog visitors.
