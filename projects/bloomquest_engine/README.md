# BloomQuest Engine

BloomQuest Engine is a Python-based, AI-friendly 2D top-down game-making engine built from premade grid-snapped parts, emojis, simple shapes, editable text fields, and reusable actions.

Read the full project treatment in [TREATMENT.md](TREATMENT.md).

## Planned Structure

```text
bloomquest_engine/
├── README.md
├── TREATMENT.md
├── main.py
├── engine/
├── editor/
├── data/
│   ├── rooms/
│   ├── parts/
│   └── projects/
├── assets/
├── docs/
└── exports/
```

## Core Rules

- 128 x 128 grid maps
- Fixed tile size
- Snap always enabled
- Four primary layers
- Premade working parts
- Simple editable names, descriptions, values, and actions
- Human-readable JSON
- Same engine commands for humans and AI
