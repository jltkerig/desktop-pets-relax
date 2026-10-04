# Pixel Fox

Two pixel foxes, one orange and one grey, live along the top of your taskbar. They wander, nap,
play together and chase leaves. You can pet them, pick them up and give them toys. The seasons change
what's around them. In autumn there's an oak tree dropping colourful leaves and acorns, plus a squirrel,
a blue jay and a woolly bear caterpillar who come by.

## Start

```powershell
.\start.ps1
```

It installs PySide6 and Pillow the first time, then runs with no console window. Right-click the fox
icon in the system tray for the **toy box**:

- **Foxes:** choose which foxes are out.
- **Toy box:** this season's items (autumn: the oak tree). There's also "Shake down an acorn" and "Invite a visitor".
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
