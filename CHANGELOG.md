# Changelog

Every change to Pixel Fox gets a new version here, newest first. The version is also in
`pet/__init__.py` (`__version__`) and shows in the tray icon's tooltip. See `CLAUDE.md`.

## 1.6.0

- **Screen saver:** `Pixel Fox.scr`. Right-click it and choose **Install**, then pick it in Windows' screen saver
  settings. It fills every monitor with your foxes and the things you've put out, drawn bigger, over a sky that
  follows the time of day (stars at night) and ground with grass that changes colour with the seasons (only the
  odd tip pokes through the snow). **Only a mouse click or a key press closes it**; moving the mouse doesn't, and
  the pointer is hidden. It can run while the desktop pets are running too. No desktop mischief in it, and
  nothing it does is saved. The little preview in Windows' settings stays empty.
- `start.ps1` remembers where Python is (`python-path.txt`) so the screen saver starts straight away.

## 1.5.1

- **Winter oak:** the trunk now forks into a thick V of two limbs instead of ending flat at the top, with a
  fuller, more even crown of branches above it (the snowy and spring oaks too).
- **The den in winter:** on snowy days the den is snowed over too, the grass buried under it.
- **Sleeping foxes in the den** show their ears as well as their snouts poking out of the doorway.

## 1.5.0

- **An oak for every season**, out all year and changing in place when the season does:
  - **Winter:** bare, branching limbs and twigs. On some days it's snowy instead: snow along the branches and a
    drift round the roots. Choose for yourself with **Snow on the oak** in the tray menu (winter only).
  - **Spring:** buds, small new leaves and tiny acorns, with violets and daffodils growing underneath.
  - **Summer:** vibrant green, shading to blue underneath, with green acorns here and there. A green leaf falls
    now and then, but rarely. Sometimes a **June beetle** or a **ladybug** climbs the trunk and flies off.
  - **Autumn:** as before. Now and then a **cicada** lands on the trunk and buzzes (the foxes notice).
- **Clicking the oak:**
  - Winter: a single branch falls, lies there a while and fades. Snowy: clumps of snow fall and puff on the ground.
  - Spring: a caterpillar drops out and runs off.
  - Summer: a few green leaves fall and a butterfly flies out.
  - Autumn: as before, and sometimes a spider lets itself down on a thread and climbs back up.
- Acorns and coloured leaves fall in autumn only. Birds perch on real branches of the leafless oak.
- Sprite JSON files can carry extra data: the leafless oaks list their `perches`.

## 1.4.0

- **Crows stay longer and talk to each other:** visits last about 35 seconds to 4 minutes. They chat back and
  forth, turning to face each other ("CAW!", "CAW CAW!", "KRAA!", "CAW?"). Only a fox charging at them scares
  the party off; one wandering close just makes a crow flutter out of the way.
- **Crows love the scarecrow:** they land on him much more than anywhere else. Now and then one tugs his hat
  off, struts about wearing it while the others call out, then puts it back (always before they leave). Startle
  a crow wearing it and it drops the hat: click the hat to put it back, or the next crows will, or it finds its
  own way home after a couple of minutes.
- **Crows love corn:** corn cobs on the ground bring crows far more often, and they land right by them and peck
  the kernels off (two crows can share a cob).
- **Corn harvest:** clicking ripe corn drops an ear from every stalk (six), and the crows soon come.
- **Giant pumpkins:** about one pumpkin in seven keeps growing past ripe into a giant, then gets too big and
  splits open, seeds and bits flying, before a new sprout comes up. A carved giant stays a giant jack-o'-lantern.
- **The hoe carves pumpkins:** drag the hoe onto a ripe (or giant) pumpkin and let go to carve a jack-o'-lantern.
- **The den:** sleeping foxes show their snouts poking out of the doorway, not their tails.
- Acorns keep falling from the oak however much corn is lying about.

## 1.3.0

- **Pixel Fox.exe:** double-click it to start Pixel Fox with no console window. It runs `start.ps1` from its
  own folder (so it updates itself first, like Pixel Fox.cmd), and shows a message pointing at Pixel Fox.cmd
  if starting fails. It has the fox face as its icon, so it can be pinned to the taskbar or Start.
  Source and build script in `launcher/`.

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
