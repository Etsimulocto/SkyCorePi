# BloomQuest Engine Manual

## What BloomQuest Is

BloomQuest is a simple 2D top-down game-making engine. You build games by placing premade parts on a grid, editing small text and number fields, connecting rooms with doors, and pressing Play.

## Quick Start

1. Open BloomQuest with `python main.py`.
2. Choose a layer.
3. Choose a premade part from the left panel.
4. Left-click the grid to place it.
5. Click the same placed part again to edit it.
6. Press Apply Changes.
7. Press Ctrl+S to save.
8. Place one Player part.
9. Press F5 or click Play.

## Editor Controls

- Left click: place or select the active-layer part
- Shift + left click: select the topmost part at a cell
- Right click: erase the active-layer part
- Arrow keys: move the editor camera
- Mouse wheel over map: scroll vertically
- Mouse wheel over part list: scroll parts
- Mouse wheel over properties: scroll fields
- Ctrl+S: save the current room
- Ctrl+L: reload the current room
- Delete: delete selected part
- F5: enter Play Mode
- Esc: close BloomQuest from Edit Mode

## Play Controls

- WASD or arrow keys: move
- E: interact with signs, villagers, chests, and other use-actions
- Esc: return to Edit Mode

## Layers

### Map
Ground, water, floors, walls, and terrain.

### Scene Objects
Trees, rocks, signs, doors, chests, buildings, and decorations.

### Enemies / Player
Player, NPCs, enemies, animals, and bosses.

### Weapons / Effects
Weapons, projectiles, sparkles, explosions, smoke, weather, and visual effects.

## Rooms

Use the Rooms menu to create, duplicate, and open rooms.

Room files are saved in:

`data/rooms/`

Each room is a readable JSON file such as:

`room_001.json`

Doors use three fields:

- Target Room
- Target X
- Target Y

Example:

- Target Room: `room_002`
- Target X: `4`
- Target Y: `7`

## Actions

### none
The part has no action.

### show_text
Displays Text / Dialogue when used.

### add_counter
Adds Value / Amount to the named Counter.

### teleport
Moves the player to Target Room and Target X/Y.

### damage_player
Removes Value / Amount from health.

### heal_player
Adds Value / Amount to health.

### timer
Reserved for timed actions.

## Save Behavior

Editor changes save to the current room JSON file.

Play Mode uses copies of rooms. Collecting coins or removing items during testing does not damage the editor version.
