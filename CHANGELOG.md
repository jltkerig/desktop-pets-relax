# Changelog

Every change to Pixel Fox gets a new version here, newest first. The version is also in
`pet/__init__.py` (`__version__`) and shows in the tray icon's tooltip. See `CLAUDE.md`.

## 1.16.0

- **Lusher trees:** the summer and autumn oak is now a full, rounded crown of overlapping clumps of leaves, each
  lit on its own with deep shade in among them, colours drifting across in patches, and branches peeking
  through underneath. The birch has airy clusters of small leaves all along its branches (green in summer,
  gold and orange in autumn), with its white trunk showing between them.
- **Fixed: pumpkins wouldn't go on the haystack.** Let a decorating pumpkin go right on a bale (not only above
  it) and it sits on top; it picks the bale you let go over. A ripe pumpkin in the patch is picked whichever
  way you drag it (young ones still just slide along).

## 1.15.0

- **The sun and moon are a clock now**, so you can tell the time at a glance: the sun crosses the sky from 6 AM
  (low on the left) through noon (at the top, in the middle) to 6 PM (low on the right), then the moon does the
  same from 6 PM through midnight to 6 AM. There's always one of them up. The moon still shows tonight's phase,
  but never vanishes (a new moon shows as a thin crescent). The tray item is now **Sun and moon clock in the
  sky**.

## 1.14.2

- **Fixed: the sun and moon didn't show on the desktop.** Their window was put at the very bottom of the stack,
  which on Windows is underneath the desktop wallpaper itself. Now it's slotted in just above the desktop, behind
  every other window.
- The tray menu says what's in the sky: "Sun and moon in the sky (the moon's up)", or when the moon next rises
  if neither is up (the real moon is below the horizon about half the time; a waning moon rises late at night).

## 1.14.1

- Updating from a downloaded ZIP now removes the old single files left over from before 1.14.0 (copies made
  with git already lose them when they update).

## 1.14.0

- **Tidied the code into small files by subject**, so it's quicker to find your way round and change things
  (nothing you'd notice in the app works differently): the world (`pet/world/`), the things on the desktop
  (`pet/items/`), the visitors (`pet/visitors/`), the windows and tray (`pet/view/`), the art
  (`art/world_art/`, one file per theme) and the tests (one file per topic). `CLAUDE.md` has a map of where
  everything is. Every sprite still comes out exactly the same.

## 1.13.0

- **The sun by day and the moon by night**, behind all your windows: it rises on the left, arcs across the
  screen (across all your monitors side by side) and sets on the right, where the real sun and moon are for
  your area (the same place used for sunrise and sunset; mirrored in the southern hemisphere). The moon shows
  its real phase, from a thin crescent to full. Clicks go straight through it. It's in the screen saver's sky
  too (dimmed behind the clouds when it rains or snows). Turn it off with **Sun and moon in the sky** in the
  tray menu.
- Fixed a rare start-up error if the window was asked to draw before it was fully set up.

## 1.12.0

- **Decorate with pumpkins (autumn):** **Add a pumpkin** and **Add a jack-o'-lantern** in the tray menu drop a
  single ripe pumpkin in. Pick one up and put it anywhere: let go over the haystack (any bale), the barrels, the
  stump or the woodstack and it sits on top (and moves with it if you drag that); anywhere else, like under a
  tree, it lands on the ground. Lift a ripe pumpkin up out of the patch and it's picked to decorate with (a
  new sprout comes up in its place; sliding it sideways still just moves it along). They're saved, the hoe
  carves them, jack-o'-lanterns glow at night, and **Clear away the decorating pumpkins** puts them all away.
- **Corn cobs (and apples, tomatoes, lettuces) can be thrown:** fling one and it flies off as fast as you threw
  it and bounces; a fox races over and bats it about. They're easier to grab (a little margin round them), and
  you can snatch one even when a squirrel is heading for it (the squirrel gives up), or a fox is about to eat it.

## 1.11.6

- **Foxes asleep in the den look like foxes:** bigger heads resting on their paws, tall pointed ears (pale
  inside, dark tips) standing up against the dark burrow, closed eyes, and tapering snouts poking out with a
  black nose (with a little shine so it shows against the dark). With two inside, they face opposite ways. The
  doorway is a little taller and its stone a little higher to fit their ears.

## 1.11.5

- **A stolen Discord message is just the words:** the fox carries only the text (name, time and message),
  cropped close, with Discord's background see-through and a thin dark outline so it reads on any background.
  The avatar is left alone, the gap is only where the words were, and the message flies back to exactly that
  spot. If there are no words there, nothing is taken.

## 1.11.4

- **Fixed: a box left over Discord.** The patch that hides the gap where a message was "stolen" went up as soon
  as a fox set off to steal it, so if the fox got distracted on the way, a plain box sat over the message for
  over a minute with nothing taken. Now the patch only appears once the message is actually pulled out, and if
  no fox has come for it within 20 seconds the theft is called off. The patch's colour is taken from Discord's
  background all round the message (if there isn't a plain background there, nothing is stolen), Discord's
  layout is found correctly with display scaling above 100%, and the theft is called off if another window has
  moved in front of Discord. **Click the gap** and the message flies straight back.

## 1.11.3

- **Butterflies fly side-on** too: a slim body held level and big wings clapping together over the back, then
  sweeping down. (Resting on a flower they're still seen from above, wings slowly opening and closing.)

## 1.11.2

- The **cicada flies sideways**, seen from the side with its body level and its clear wings beating above its
  back, instead of flying along head-up as it sits on the trunk.

## 1.11.1

- **Turkey hens:** a flock is now mostly hens with a tom or two. Hens are smaller and plainer (soft brown with
  pale barring, a feathered neck and a small greyish face, no red wattle or beard), don't fan their tails, and
  cluck ("CLUCK!") instead of gobbling.

## 1.11.0

- **Dug-up taskbar icons are bouncy balls:** pick one up with the mouse and throw it. It flies off as fast as
  you threw it and bounces off the ground and the edges of the screen. A fox races after it, catches it on a low
  bounce and brings it back to where you threw it from. Tap one to bounce it up into the air.
- **The foxes move folders about on the desktop** (Windows): now and then a bored fox sits under a folder icon,
  leaps and pulls it down, drags it along the bottom of the screen and drops it somewhere else. It's the real
  icon moving, the same as dragging it yourself; the folder and what's in it are never touched. Only folders
  (not files or shortcuts), only on the main monitor, at most one every eight minutes or so, and not when the
  desktop is set to Auto arrange icons. Where each folder was is remembered: **Put the desktop folders back** in
  the tray menu moves them all back. **Move a desktop folder** sends a fox to do it now. Turn it off in the Toy
  Box under Mischief ("Move folders about on the desktop").

## 1.10.0

- **A tidier Toy Box:** tabs for All year, Winter, Spring, Summer and Autumn (this season's tab opens first and
  says "(now)"). The tray menu is in sections: All year, This season, and Things to do.
- **The foxes use the new things:** they pounce at butterflies and drifting seed fluff flying low (it always gets
  away), trot over to nibble an apple, tomato or lettuce lying about (YUM!), and pull a face at a radish
  (BLEH!). Now and then a daytime nap is in the shade under the birch.
- **Paw prints:** on a snowy day the foxes leave a trail of paw prints in the snow, which slowly fill in.
- **At night:** jack-o'-lanterns glow warm orange and the Christmas tree's lights cast a soft glow. On summer
  nights **fireflies** blink over the grass (not in the rain). A great horned **owl** comes to the oak or the
  birch after dark, blinks, turns its head right round and hoots softly (it doesn't wake anyone), and flies off
  at dawn or when clicked. It's the only visitor that comes by itself at night; you can also invite it.
- **Local weather:** rain and snow fall when it's raining or snowing where you are, and in winter a snowy day
  is one with real snow on the ground (unless you chose snow on or off yourself). It asks Open-Meteo (free, no
  account) every half hour, sending only a rough location (the city picked from your time zone, or the one you
  set, rounded to about 10 km). No internet, no problem: it just carries on as before. Turn it off with **Local
  weather (rain and snow)** in the tray menu. In the screen saver the sky clouds over while it rains or snows.
- Tray menu: **Make it rain** and **Make it snow** for a few minutes, whatever the weather.

## 1.9.0

- **Daffodils** look like daffodils: a round ring of petals with a few pointed tips, and an orange trumpet.
- **Corn cobs can be picked up** with the mouse and dropped somewhere else (they fall and bounce).
- **A birch tree**, out all year: white bark with black marks, drooping twigs; bare (or snowy) in winter,
  catkins in spring, bright green in summer, golden in autumn. Click it: golden leaves in autumn, green ones in
  spring and summer, a twig or clumps of snow in winter. Birds perch in it.
- **Winter:** a **woodstack** of split logs (the foxes climb it; snowy on snowy days).
- **Spring:** a **stone well** (click it and the bucket goes down and comes back up with a splash; birds sit on
  its roof), rows of **radishes** and **lettuce** that grow over time (click when ripe and they pop out of the
  ground), and **dandelion** seed clocks (click them and the seeds blow away on the breeze; new ones grow back).
- **Summer:** a **slide** (the foxes climb the ladder and slide down), a **kiddie pool** (the foxes splash about
  in it; click it for ripples), a **watermelon patch** that grows like the pumpkins (click a ripe one and it
  splits open), **tomato plants** that grow like the corn (ripe tomatoes drop off when clicked), **cattails**
  (click the ripe brown heads and they burst into fluff that drifts off on the wind), yellow **dandelions**,
  **pansies** round the foot of the oak and the birch, and a **dahlia** bed (summer and autumn).
- **Autumn:** an **apple barrel**: click it and an apple rolls out for the foxes to bat about. The crows like it
  too, and sometimes knock apples out themselves.
- Apples, tomatoes, radishes and lettuces lying about behave like corn cobs: the foxes bat them, crows peck them,
  you can pick them up, and they fade after a while.
- Tray menu: **Plant new watermelons** and **Replant the garden** when they're out.
- Everything has its own spot the first time it comes out, spread so they don't sit on top of each other.

## 1.8.1

- Daffodils have four pointed petals poking out round their orange trumpets (in the flower bed and under the
  spring oak), instead of round heads.

## 1.8.0

- **Spring flower beds** in the Toy Box: **daffodils**, **tulips** (red, pink, yellow and purple) and **violets**.
  They sway in the breeze; click one and it bobs, and sometimes a butterfly that was resting in it flies up.
- **Butterflies** (monarchs, cabbage whites, sulphurs and azures) flutter in, land on the flowers to rest with
  their wings slowly opening and closing, flutter about some more and go on their way. A fox coming close, or a
  click, sends them off.
- **Songbirds:** a robin, a bluebird or a goldfinch (sometimes a pair) perches in the budding oak, on something,
  or hops about on the ground, singing now and then with music notes floating up, and the foxes stop to listen.
  A robin on the ground sometimes tugs up a worm. Click one, or let a fox dash at it, and it flies off.
- "Invite a visitor" in spring: Butterflies, Songbirds.

## 1.7.1

- The tree stump is out all year round now, not just in winter (snowy on snowy winter days).
- Crows still favour the scarecrow, with the oak's branches a close second (with more places to land, they'd
  started to overlook both).

## 1.7.0

- **More for the winterscape**, in the Toy Box for winter (each can be put out or away, and dragged about):
  - **A sled:** wooden slats on red runners curling up at the front. Click it and it rocks.
  - **A tree stump:** flat, ringed top and a shelf fungus. The foxes hop up on it to enjoy the view; on a snowy
    day a knock tips the snow off its top.
  - **A small Christmas tree:** a gold star and coloured lights that twinkle. Click it and they all blaze.
  - On snowy days all three wear a coat of snow, and crows perch on them (the star is a favourite).

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
