# Pixel Fox

Two pixel foxes, one orange and one grey, live along the top of your taskbar. They wander, nap,
play together and chase leaves. You can pet them, pick them up and give them toys. The seasons change
what's around them. In autumn there's an oak tree dropping colourful leaves and acorns, plus a squirrel,
a blue jay and a woolly bear caterpillar who come by.

## Start

Double-click **Pixel Fox.cmd** (or run `.\start.ps1` in PowerShell).

It installs PySide6 and Pillow the first time (just for you, if installing for everyone isn't allowed),
then runs with no console window. Starting it again while it's running does nothing.

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
  **Invite a visitor** (squirrel, blue jay, caterpillar, geese).
- **Season:** follows the date (northern hemisphere), or preview any season.
- **Size:** 1x, 2x or 3x.
- **Pause**, and **Quit**.

## Playing with them

- **Pet:** move the cursor back and forth over a fox. It only ever reacts happily.
- **Click:** a happy hop. A napping fox wakes up and stretches.
- **Drag a fox:** you pick it up, and it lands when you let go.
- **Drag the oak:** you can move it anywhere along the bottom of the screen, and it remembers the spot.
- **Rest the cursor near the bottom of the screen:** a playful fox may crouch, wiggle and pounce on it.

Clicks on empty parts of the screen go straight through to your desktop and windows.

## How it works

```
pixelfox.py        start here
pet/world.py       everything on the desktop, what appears when, how things meet
pet/fox.py         a fox's moods (playful, bored, sleepy; no hunger) and how it picks what to do
pet/items.py       the oak, falling leaves, acorns, the squirrel's dirt mound
pet/visitors.py    the squirrel, the blue jay and the woolly bear caterpillar
pet/seasons.py     which season it is and what belongs to it
pet/view.py        the see-through window, the mouse, the tray menu
pet/save.py        user-data/world.json: what's out and where
art/make_art.py    draws every sprite into art/sprites/ (python art/make_art.py --preview to see them all)
tests/             python -m unittest discover -s tests
```

## Your own art

Every sprite is a PNG strip in `art/sprites/` with a JSON file of the same name. The JSON gives the frame
size, the number of frames, milliseconds per frame, whether it loops, and the anchor point (where it
touches the ground). To use better art, replace the PNG and its JSON; no code changes are needed. Foxes
face right, and the app mirrors them to face left. Run `art/make_art.py` again only if you want the drawn
art back.
