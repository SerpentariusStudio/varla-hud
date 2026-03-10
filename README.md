# Varla-HUD

A save dump editor for **Oblivion Remastered** (and classic Oblivion).

Load a save dump text file, browse and edit your character's data through a dual-panel interface, then save the modified dump back out.

## Features

- **Dual-panel drag & drop** — left panel shows everything in your save, right panel is your staged changes
- **Character editing** — attributes, skills, factions, and details
- **Inventory management** — weapons, gear, alchemy ingredients, misc items with editable quantity/condition/charge
- **Magic** — browse and edit spells (self/touch/target), manage active effects
- **Quests** — view and edit active/completed quest stages
- **Import/Export** — generate OBSE import logs to bring changes into the game
- **Dark medieval theme**
- Supports both Remastered and Classic save dump formats

## Requirements

- Python 3.10+
- PySide6

## Setup

```
pip install -r requirements.txt
```

## Usage

```
python app_v2_enhanced.py
```

Then use **File > Open** to load a save dump text file.

## How to get a save dump

You need the [Varla OBSE plugin](https://www.nexusmods.com/oblivionremastered/mods/55948) to generate save dump files from within the game.

## License

MIT
