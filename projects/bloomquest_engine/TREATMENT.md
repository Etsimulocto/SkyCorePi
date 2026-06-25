# BloomQuest Engine
## Project Treatment v0.1

### Vision

BloomQuest Engine is a lightweight, AI-friendly 2D top-down game creation system inspired by classic adventure games. Instead of requiring programming knowledge, creators build games by dragging prebuilt parts onto a grid, editing simple properties, and connecting events through easy-to-understand actions.

**If you can build with LEGO, you can build a game.**

## Design Goals

- No coding required for most projects.
- Simple enough for children and beginners.
- Powerful enough for advanced users through modular expansion.
- AI can create and edit projects using the same data model as humans.
- Every object is self-describing.
- Everything saves as readable JSON.

## Engine Philosophy

The engine does not hardcode special knowledge of a coin, tree, door, enemy, or chest. Every part is assembled from reusable behaviors.

Example: Coin

- Collectible
- Counter +1
- Play Sound
- Destroy Self

Example: Heart

- Collectible
- Restore Health
- Destroy Self

Example: Tree

- Solid
- Decorative
- Optional interaction

Because parts are built from behaviors instead of one-off logic, creators can add new parts without changing the engine core.

## Grid System

Everything snaps to a fixed grid.

Default project settings:

- Map size: 128 x 128 cells
- Tile size: 32 x 32 pixels
- Snap: always enabled
- Camera: scroll and zoom

No free placement is required in the first version. This keeps maps predictable, readable, and easy for both humans and AI to edit.

## Layer System

BloomQuest uses four primary layers.

### Layer 0 — Map

Terrain, ground, water, walls, roads, floors, sand, lava, and other base tiles.

### Layer 1 — Scene Objects

Trees, rocks, signs, doors, chests, houses, bridges, furniture, and decorations.

### Layer 2 — Actors

Player, NPCs, enemies, animals, and bosses.

### Layer 3 — Weapons and Effects

Weapons, projectiles, particles, lighting, weather, explosions, and animations.

Each layer can be visible, hidden, locked, or editable.

## Every Part

Every part follows the same basic structure:

- Emoji or icon
- Display name
- Description
- Layer
- Grid position
- Width and height
- Properties
- Behaviors
- Tags
- User action or interaction

Because every part follows one structure, the editor only needs one reusable property panel.

## Premade Parts

The engine ships with a growing library of ready-to-use parts.

### Terrain

Grass, dirt, water, wall, floor, sand, lava, ice, path, bridge.

### Scene Objects

Tree, rock, sign, door, locked door, chest, house, cave, crate, switch.

### Actors

Player, villager, merchant, wizard, slime, bat, skeleton, ghost, boss.

### Items

Coin, heart, key, sword, shield, potion, bomb, arrow, gem.

### Effects

Sparkle, smoke, fire, lightning, explosion, splash, rain, fog.

Every premade part works immediately after placement. Users only edit small fields such as name, text, value, health, damage, target room, or timer.

## Simple Property Editing

Instead of scripting, users edit plain fields:

- Name
- Description
- Dialogue text
- Health
- Damage
- Counter value
- Target room
- Target coordinates
- Timer duration
- Sound
- Animation
- Visible
- Solid
- Enabled

Examples:

A sign only needs display text.

A door only needs a destination room and destination coordinates.

A coin only needs a counter name and amount.

An enemy only needs health, damage, speed, and behavior preset.

## Event Builder

Events use readable blocks.

Example:

WHEN player touches coin

THEN increase Coins by 1

THEN play coin sound

THEN destroy coin

Another example:

WHEN player uses door

THEN load Room 2

THEN place player at X 6, Y 14

The first version should use dropdowns, text fields, and numeric fields rather than a full visual scripting system.

## Global Counters

Built-in counters include:

- Health
- Coins
- Score
- Lives
- Keys
- Bombs
- Arrows
- Magic
- Experience
- Level
- Timer

Creators can also add custom counters.

Supported operations:

- Add
- Subtract
- Set
- Compare
- Reset

## AI-First Architecture

The GUI is one client of the engine. AI is another client.

Both use the same commands and the same project data.

Core commands include:

- create_room
- paint_tile
- place_part
- move_part
- delete_part
- change_property
- add_behavior
- connect_door
- change_counter
- save_project
- load_project
- play_test
- undo
- redo

This allows natural-language requests such as:

- Create a forest room.
- Place ten trees around the lake.
- Replace every slime with skeletons.
- Make every chest worth 50 coins.
- Connect this cave to Room 4.

The AI should edit structured data directly rather than imitate mouse movement.

## File Format

Projects are stored as human-readable JSON.

Primary data folders:

- rooms
- parts
- dialogue
- quests
- settings
- counters

No proprietary binary project format is required.

## Technical Foundation

- Language: Python
- Rendering and game loop: pygame-ce
- Project storage: JSON
- Utility windows and launcher: Tkinter where useful
- Image support: Pillow when needed
- Optional future scripting: Lua

## First Milestone

The first working build should support:

- Open a 128 x 128 grid map
- Paint simple colored tiles
- Drag and drop emoji parts
- Use four layers
- Select and edit a part
- Add a name and description
- Configure one simple action
- Save and load a room as JSON
- Enter play-test mode
- Move a player around the room
- Collect a coin
- Open a door

## Long-Term Vision

BloomQuest Engine is not intended to compete with professional game engines. Its purpose is to become the easiest way to build classic top-down adventure games while remaining understandable by both humans and AI.

The editor should feel less like programming software and more like opening a box of digital LEGO bricks.

Drag.

Drop.

Name.

Connect.

Play.

The long-term goal is for anyone to build a Zelda-style adventure in an afternoon, even if they have never programmed before.
