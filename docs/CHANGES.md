# What the mod changes

The original game can only be played with a Wii Remote and Nunchuk, pointing at the screen and making gestures. This mod lets you play the whole game with the **Classic Controller**, with twin-stick controls in the style of *Metroid Prime Remastered*.

## Button mapping

### In game
| Classic Controller | Action | Original (Wii Remote + Nunchuk) |
|---|---|---|
| Left stick | Move | Nunchuk stick |
| Right stick | Look / aim | Point the Wii Remote at the screen |
| R or A | Fire (hold to charge) | A |
| L | Lock on | Z |
| L + X | Grapple lasso: with a target locked, X throws, hold to pull | Thrust the Nunchuk forward, pull back |
| ZR | Missile | D-pad down |
| ZL | Visor menu | Hold − and point |
| B | Jump · shake when the game asks you to | B · shake the controller |
| Y | Morph ball | C |
| B (morph ball) | Spring ball (jump) | Flick the Wii Remote up |
| X (morph ball) | Boost ball (hold to charge, release) | B |
| + (press) | Pause / map | 1 |
| + (hold 1 s in a cutscene) | Skip cutscene | (not in the original) |
| − (hold) | Hypermode | Hold + |
| D-pad up | Objective hint | 2 |
| D-pad down | Screenshot | D-pad up |
| HOME | HOME menu | HOME |

### In menus (main menu, dialogs, consoles)
| Classic Controller | Action |
|---|---|
| Left stick | Moves the cursor |
| A | Select |
| Right stick | Does nothing (so the cursor never moves by accident) |

### Pause screen and map
| Classic Controller | Action |
|---|---|
| Left stick | Moves the cursor |
| Right stick | Rotates the map (or the model in the inventory) |
| L + left stick | Pans the map (the cursor stays still) |
| D-pad up / down | Zoom in / out |
| − | Objective hint |
| + | Close |

### Visor menu (ZL)
| Classic Controller | Action |
|---|---|
| Right stick | Push towards a visor: the cursor jumps to it |
| Release the stick | The cursor stays on that visor; after 0.7 s without touching the stick it goes back to the centre (standard visor) |

## Quality-of-life improvements
- **Modern shooter camera:** the reticle stays in the centre and the right stick turns the camera, with no pointer involved (based on PrimeHack).
- **No gestures:** everything that needed moving the controller is done with buttons or sticks.
  - Grapple lasso with L + X.
  - Shake with B.
  - Spring ball with B and boost ball with X in morph ball.
  - Levers and locks with the left stick: pull out = back, turn = sideways, push in = forward (the opposite direction undoes it).
  - Combination wheels with the left stick left/right.
  - The Wii Remote's motion sensor is frozen so nothing triggers on its own.
- **Comfortable menu cursor:** moved with the left stick, slow near the centre and fast at full tilt. It follows the stick's exact direction, moves at the same speed horizontally and vertically (16:9), doesn't vanish or recentre when you let go, and doesn't leave the screen.
- **Consoles and interaction screens** (ship, code entry, levers): the left stick moves Samus's hand and it stays where you leave it. The mod detects these screens using the game's own state, so they never trigger by mistake.
- **Magnetic visor menu:** push the right stick towards a visor and the cursor jumps to it and stays there when you let go; after 0.7 s untouched it returns to the centre.
- **Two-stick map:** rotate with the right stick, pan with L + left stick, zoom with the D-pad.
- **Skip cutscenes:** hold + for a second to skip any cutscene, even the first time you see it (Classic Controller or Wii Remote).
- **No Nunchuk warnings:** the game no longer asks you to connect the Nunchuk.
- **Normal Wii HOME menu:** while it is open the mod doesn't touch the controller, so it works as usual (Wii Remote pointer).
- **Pause without conflicts:** + opens the pause screen as soon as you press it; during a cutscene, holding it skips the cutscene instead.

## Limitations
- Only the European release (RM3P01) is supported.
- The in-game button icons still show the Wii Remote.
