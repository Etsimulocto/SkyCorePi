# SkyCorePi

Local Raspberry Pi interface for a private AI maker console.

## Current goal

Build a lightweight Pi-native web interface that can:

- talk to a local Ollama model
- load character/personality files
- save user themes and project cards
- run small Python utilities
- grow into GPIO / hardware control panels

## Starter stack

- Raspberry Pi OS / Debian Bookworm
- Python 3
- Flask
- Ollama
- Local model: llama3.2:3b

## Planned folders

```text
SkyCorePi/
├── app.py
├── requirements.txt
├── characters/
├── docs/
├── hardware/
├── projects/
├── scripts/
├── static/
├── templates/
├── themes/
└── users/
```

## First milestone

Browser UI → Flask → Ollama → local model response → browser UI.
