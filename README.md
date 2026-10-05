# Pixel Fox

![Pixel Fox: an autumn scene along the taskbar](docs/showcase.png)

Two pixel foxes, one orange and one grey, live along the top of your taskbar. They wander, nap,
play together and chase leaves. You can pet them, pick them up and give them toys. The seasons change
what's around them. The oak changes with the seasons: bare (or snowy) in winter, budding with flowers
underneath in spring, deep green in summer. In autumn it drops colourful leaves and acorns, and there's a squirrel,
a blue jay, a woolly bear caterpillar, geese and a flock of wild turkeys who come by. Crows visit all year
round: they perch in the tree, on things or on the ground, and if they stay a while they play with what's
lying about.

## Start

Double-click **Pixel Fox.exe** (or **Pixel Fox.cmd**, or run `.\start.ps1` in PowerShell).

**Screen saver:** right-click **Pixel Fox.scr** and choose **Install** (it stays in the Pixel Fox folder), then
pick it in Windows' screen saver settings. Start Pixel Fox once first, so it knows where Python is. Only a mouse
click or a key press closes the screen saver; moving the mouse doesn't.

Pixel Fox.exe starts it with no window at all. Right-click it to pin it to the taskbar or Start, or to make a
desktop shortcut; keep the .exe itself in the Pixel Fox folder. If it can't start, it tells you, and
Pixel Fox.cmd shows what went wrong.

It installs PySide6 and Pillow the first time (just for you, if installing for everyone isn't allowed),
then runs with no console window. Starting it again while it's running does nothing.

**Updates:** each time you start it, it first checks GitHub for a newer version and installs it, keeping
your settings. If you're offline it just starts the version you have. To turn this off, put an empty file
named `no-update` in the Pixel Fox folder. The current version shows when you hover over the tray icon.

## Works on

- **Windows 10 and Windows 11**, with **Python 3.9 or newer**, from python.org, the Microsoft Store or the
  `py` launcher. The start script finds it, and tries each one first so the Store's placeholder is never used.
- **Any number of monitors**, any sizes and scaling. The screens are joined left to right as Windows
  arranges them. Foxes walk from one to the next, and items always sit wholly on one screen.
  Plugging in, unplugging or rearranging a monitor while it runs is picked up straight away.
- **Taskbar anywhere:** at the bottom, the pets stand on it. At the top or a side, or when auto-hidden,
  they stand on the bottom of the screen.
- **Taskbar icons for treasure digging:** found the Windows 10 way, the Windows 11 way, or from the whole
  taskbar as a fallback. If none of those works, the foxes just don't dig for treasure.
- **Settings** are kept in `user-data` next to the app, or in `%LOCALAPPDATA%\PixelFox` if the app's folder
  can't be written to (for example in Program Files).

## The toy box

Click the fox icon in the system tray to open the **Toy Box** window. Tick or untick each fox and item to
put it out or away. Items from another season show in italics and come out when their season does.
Right-click the icon for the menu:

- **Foxes** and this season's items, as checkboxes.
- **Shake down an acorn**, **Plant new pumpkins / corn**, **Dig up a taskbar treasure**, **Zoomies!**, and
  **Invite a visitor** (squirrel, blue jay, caterpillar, geese, wild turkeys, crows, cicada, June beetle,
  ladybug, depending on the season). In winter, **Snow on the oak** turns the snow on or off.
- **Season:** follows the date (northern hemisphere), or preview any season.
- **Size:** 1x, 2x or 3x.
- **Pause**, and **Quit**.

## Playing with them

- **Pet:** move the cursor back and forth over a fox. It only ever reacts happily.
- **Click:** a happy hop. A napping fox wakes up and stretches.
- **Drag a fox:** you pick it up, and it lands when you let go.
- **Spring:** daffodils, tulips and violets that butterflies land on, and songbirds that sing.
- **Winter:** a sled to rock, a tree stump the foxes climb, and a little Christmas tree whose lights blaze when
  clicked.
- **Click the oak:** something different falls out each season: a branch, snow, a caterpillar, a butterfly,
  autumn leaves (and now and then a spider on its thread).
- **Drag the oak:** you can move it anywhere along the bottom of the screen, and it remembers the spot.
- **Drag the hoe onto a ripe pumpkin:** it carves a jack-o'-lantern.
- **Click ripe corn:** an ear drops from every stalk, and the crows will soon be round for it.
- **Crows** chat, play with what's lying about, and sometimes borrow the scarecrow's hat. Click one to shoo them;
  if it drops the hat, click the hat to put it back.
- **Rest the cursor near the bottom of the screen:** a playful fox may crouch, wiggle and pounce on it.

Clicks on empty parts of the screen go straight through to your desktop and windows.

## How it works

```
Pixel Fox.exe      double-click to start (runs start.ps1; source in launcher/)
Pixel Fox.scr      the screen saver (runs pixelfox.py --scr; pet/saver.py draws it)
pixelfox.py        start here
start.ps1          checks for updates (update.ps1), installs what's needed, starts it
pet/world.py       everything on the desktop, what appears when, how things meet
pet/fox.py         a fox's moods (playful, bored, sleepy; no hunger) and how it picks what to do
pet/items.py       the oak (all four seasons), falling leaves, branches, snow, acorns, pumpkins, the scarecrow's hat
pet/visitors.py    the squirrel, blue jay, woolly bear, geese, frog, wild turkeys and crows
pet/seasons.py     which season it is and what belongs to it
pet/view.py        the see-through window, the mouse, the tray menu
pet/save.py        user-data/world.json: what's out and where
art/make_art.py    draws every sprite into art/sprites/ (python art/make_art.py --preview to see them all)
tests/             python -m unittest discover -s tests
CHANGELOG.md       what changed in each version (the version is in pet/__init__.py)
```

## Your own art

Every sprite is a PNG strip in `art/sprites/` with a JSON file of the same name. The JSON gives the frame
size, the number of frames, milliseconds per frame, whether it loops, and the anchor point (where it
touches the ground). To use better art, replace the PNG and its JSON; no code changes are needed. Foxes
face right, and the app mirrors them to face left. Run `art/make_art.py` again only if you want the drawn
art back.
