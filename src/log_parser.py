"""
Log Parser Module
Parses the Oblivion Static Log.log file to extract inventory items and spells.
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional

from .models import Item, Spell, Preset


def parse_static_log(log_path: Path) -> Tuple[List[Item], List[Spell]]:
    """
    Parse the Static Log.log file and extract inventory items and spells.

    Args:
        log_path: Path to the Static Log.log file

    Returns:
        Tuple of (items, spells)
    """
    items = []
    spells = []

    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # State machine variables
    in_inventory_section = False
    in_spells_section = False

    current_spell_id = None
    current_spell_name = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for inventory section start
        if line == "[inventory.csv]":
            in_inventory_section = True
            in_spells_section = False
            i += 1
            continue

        # Check for spells section start
        if line == "[spells.csv]":
            in_spells_section = True
            in_inventory_section = False
            i += 1
            continue

        # Check for section end
        if line.startswith("[") and line.endswith("]") and line not in ["[inventory.csv]", "[spells.csv]"]:
            in_inventory_section = False
            in_spells_section = False

        # Parse inventory items
        if in_inventory_section:
            # Look for item data pattern
            # COUNT - Count attempt: 91
            # NAME - name of the item: Gold
            # ITEMID - id of the item: 0000000F
            if line.startswith("COUNT - Count attempt:"):
                try:
                    quantity = int(line.split(":")[-1].strip())

                    # Look ahead for NAME and ITEMID
                    if i + 2 < len(lines):
                        name_line = lines[i + 1].strip()
                        itemid_line = lines[i + 2].strip()

                        if name_line.startswith("NAME - name of the item:") and itemid_line.startswith("ITEMID - id of the item:"):
                            name = name_line.split(":", 1)[-1].strip()
                            form_id = itemid_line.split(":")[-1].strip()

                            item = Item(
                                form_id=form_id,
                                name=name if name else "name missing",
                                quantity=quantity
                            )
                            items.append(item)

                            i += 3  # Skip the next 2 lines we just processed
                            continue
                except (ValueError, IndexError):
                    pass

        # Parse spells
        if in_spells_section:
            # Look for spell ID pattern
            if line == "This is the spell id":
                try:
                    if i + 1 < len(lines):
                        spell_id_line = lines[i + 1].strip()
                        current_spell_id = spell_id_line

                        # Look ahead for spell name
                        if i + 3 < len(lines) and lines[i + 2].strip() == "This is the spell name":
                            spell_name_line = lines[i + 3].strip()
                            current_spell_name = spell_name_line if spell_name_line else "name missing"

                            # Add the spell
                            if current_spell_id:
                                spell = Spell(
                                    form_id=current_spell_id,
                                    name=current_spell_name
                                )
                                spells.append(spell)

                            i += 4
                            continue
                except (ValueError, IndexError):
                    pass

        i += 1

    return items, spells


def generate_import_log(items: List[Item], spells: List[Spell], output_path: Path, exceptions: List[str] = None):
    """
    Generate import log file from items and spells.

    Args:
        items: List of Item objects to export
        spells: List of Spell objects to export
        output_path: Path where to write the import log
        exceptions: List of form IDs to exclude (optional)
    """
    exceptions = exceptions or []
    exception_ids = [fid.upper() for fid in exceptions]

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        # Write items
        for item in items:
            if item.form_id.upper() not in exception_ids:
                f.write(f"Item {item.form_id} {item.quantity}\n")

        # Write spells (no quantities)
        for spell in spells:
            if spell.form_id.upper() not in exception_ids:
                f.write(f"Spell {spell.form_id}\n")


def generate_full_import_log(items: List[Item], spells: List[Spell], output_path: Path,
                             preset: Optional[Preset] = None, exceptions: List[str] = None):
    """
    Generate a full import log including character data, attributes, skills, etc.

    Args:
        items: List of Item objects to export
        spells: List of Spell objects to export
        output_path: Path where to write the import log
        preset: Preset with extended character data (optional)
        exceptions: List of form IDs to exclude (optional)
    """
    exceptions = exceptions or []
    exception_ids = [fid.upper() for fid in exceptions]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    # Items
    for item in items:
        if item.form_id.upper() not in exception_ids:
            lines.append(f"Item {item.form_id} {item.quantity}")

    # Spells
    for spell in spells:
        if spell.form_id.upper() not in exception_ids:
            lines.append(f"Spell {spell.form_id}")

    if preset:
        # Spells to remove
        if preset.spells_to_remove:
            for sp in preset.spells_to_remove:
                lines.append(f"RemoveSpell {sp.get('formId', '')}")

        # Character info
        if preset.character:
            c = preset.character
            lines.append(f"Character Level {c.get('level', 1)}")
            lines.append(f'Character Name "{c.get("name", "")}"')
            lines.append(f'Character Class "{c.get("class", "")}"')
            lines.append(f'Character Birthsign "{c.get("birthsign", "")}"')

        # Attributes
        if preset.attributes:
            for attr_name, attr_value in preset.attributes.items():
                lines.append(f"Attribute {attr_name} {attr_value}")

        # Skills
        if preset.skills:
            for skill_name, skill_value in preset.skills.items():
                lines.append(f"Skill {skill_name} {skill_value}")

        # Statistics
        if preset.statistics:
            stats = preset.statistics
            lines.append(f"Fame {stats.get('fame', 0)}")
            lines.append(f"Infamy {stats.get('infamy', 0)}")
            bounty = min(stats.get('bounty', 0), 100000)
            lines.append(f"Bounty {bounty}")

            misc = stats.get("pcMiscStats", {})
            for idx_str in sorted(misc.keys(), key=lambda x: int(x)):
                if int(idx_str) != 1:
                    lines.append(f"PCMiscStat {idx_str} {misc[idx_str]}")

        # Factions
        if preset.factions:
            for faction in preset.factions:
                lines.append(f"Faction {faction.get('formId', '')} {faction.get('rank', 0)}")

        # Completed quests
        if preset.quests:
            for quest_id in preset.quests:
                lines.append(f"CompletedQuest {quest_id}")

        # Active quest
        if preset.active_quest:
            lines.append(f"ActiveQuest {preset.active_quest.get('editorId', '')}")

        # Current quests
        if preset.current_quests:
            for cq in preset.current_quests:
                lines.append(f"CurrentQuest {cq.get('editorId', '')} {cq.get('stage', 0)}")

        # Vitals
        if preset.vitals:
            v = preset.vitals
            if v.get("healthBase", 0) > 0:
                lines.append(f"Health {int(v['healthBase'])}")
            if v.get("magickaBase", 0) > 0:
                lines.append(f"Magicka {int(v['magickaBase'])}")
            if v.get("fatigueBase", 0) > 0:
                lines.append(f"Fatigue {int(v['fatigueBase'])}")

        # Magic resistances
        if preset.magic_resistances:
            r = preset.magic_resistances
            resist_map = {
                "fire": "Fire", "frost": "Frost", "shock": "Shock",
                "magic": "Magic", "disease": "Disease", "poison": "Poison",
                "paralysis": "Paralysis", "normalWeapons": "NormalWeapons"
            }
            for key, label in resist_map.items():
                val = r.get(key, 0)
                if val != 0:
                    lines.append(f"Resistance {label} {int(val)}")

        # Global variables
        if preset.global_variables:
            for gv in preset.global_variables:
                lines.append(f"Global {gv.get('formId', '')} {gv.get('value', 0)}")

        # Game time
        if preset.game_time:
            gt = preset.game_time
            if gt.get("daysPassed", 0) > 0:
                lines.append(f"GameTime {gt['daysPassed']}")
            lines.append(f"GameYear {gt.get('gameYear', 433)}")
            lines.append(f"GameMonth {gt.get('gameMonth', 1)}")
            lines.append(f"GameDay {gt.get('gameDay', 1)}")
            lines.append(f"GameHour {gt.get('gameHour', 0)}")

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')
        f.flush()
        os.fsync(f.fileno())
