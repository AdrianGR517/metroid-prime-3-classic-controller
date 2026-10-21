# Installation guide

## Requirements
- **Metroid Prime 3: Corruption**, European PAL release (game ID **RM3P01**). Other releases (US RM3E01, Japanese, Metroid Prime Trilogy) do **not** work.
- **Dolphin**, or a **Wii** with **USB Loader GX**.

## Files
| File | Use |
|---|---|
| `codes/RM3P01.ini` | Both codes, already enabled, for Dolphin |
| `codes/RM3P01.gct` | Both codes together, for the Wii |
| `codes/RM3P01.txt` | Both codes as text for USB Loader GX's cheat manager |
| `codes/classic_controller.txt` | Main Classic Controller code (to paste by hand) |
| `codes/skip_cutscenes.txt` | Skip-cutscenes code (to paste by hand) |

## Dolphin
1. **Enable cheats:** *Config → General → Enable Cheats*.
2. **Copy the codes:** put `RM3P01.ini` in `Documents/Dolphin Emulator/GameSettings/`. Back up any existing `RM3P01.ini` first, as it will be overwritten.
   - Alternative: right-click the game → *Properties → Gecko Codes → Add*, paste `classic_controller.txt` as "Classic Controller", then `skip_cutscenes.txt` as "Skip cutscenes". Tick both.
3. **Set up the controller:** *Controllers → Wii Remote 1: Emulated Wii Remote → Configure*, set **Extension** to **Classic Controller** and map its buttons to your pad.
4. In *Properties → Gecko Codes*, check that **Classic Controller v1.0** and **Skip cutscenes (hold + 1 s)** are ticked. Don't enable other versions of the code at the same time.

To use the HOME menu in Dolphin, map the emulated Wii Remote's *Point* directions (in *Motion Simulation*) to the mouse cursor.

## Wii (USB Loader GX)
1. Copy `RM3P01.gct` to `SD:/codes/RM3P01.gct` (create the `codes` folder at the root of the SD card if needed).
2. In USB Loader GX, open the game's settings → *Game Load* → **Ocarina: On**.
3. Check that the GCT path in *Custom Paths* is `sd:/codes/`.
4. Plug the Classic Controller into the Wii Remote and start the game. Don't touch the sticks while it loads.

**If the loader says it can't find the cheat file:** copy `RM3P01.txt` to `SD:/txtcodes/RM3P01.txt`, open the game's cheat manager in USB Loader GX, tick both codes and choose *Create GCT*.
**If the codes have no effect:** try another *Hook Type* in the game's settings (e.g. VBI or AXNextFrame).

## Controls
See the table in the [README](../README.md) or the image in `docs/controls.png`.

**Levers and locks:** pull out = stick back, turn = sideways, push in = forward.

## Known issues
- **Stick "stuck" after boot:** don't touch the sticks while the game starts or when returning from a save. The Wii takes that position as the centre. If it happens, let go of the sticks and reconnect the controller.
- **A jumps and B fires:** check the game's own control options (a downloaded save can bring them swapped).
- **The in-game icons still show Wii Remote buttons.**
- **Cutscenes don't skip:** make sure the skip-cutscenes code is enabled. Dolphin has no room for other large codes alongside these two.
