"""
Import Log Generator
Generates the import log (varla-test.log) from character data.
"""

import os
from pathlib import Path
from models import CharacterData, PCMISCSTAT_NAMES


class ImportLogGenerator:
    """Generates import log for Oblivion."""

    def __init__(self, character_data: CharacterData):
        self.character_data = character_data

    def generate(self, output_path: Path, export_options: dict = None):
        """
        Generate import log file.

        Args:
            output_path: Path to save the import log
            export_options: Dict of export options (which sections to include)
        """
        if export_options is None:
            export_options = {
                "character": True,
                "attributes": True,
                "skills": True,
                "statistics": True,
                "factions": True,
                "items": True,
                "spells": True,
                "completedQuests": True,
                "vitals": True,
                "resistances": True,
                "globalVariables": True,
                "gameTime": True,
            }

        lines = []

        # Items
        if export_options.get("items", True):
            for item in self.character_data.items:
                lines.append(f"Item {item.form_id} {item.quantity}")

        # Spells (only form ID, no properties)
        if export_options.get("spells", True):
            for spell in self.character_data.spells:
                lines.append(f"Spell {spell.form_id}")

        # Spells to Remove (only form ID, using RemoveSpell keyword)
        if export_options.get("spells", True):
            for spell in self.character_data.spells_to_remove:
                lines.append(f"RemoveSpell {spell.form_id}")

        # Character info
        if export_options.get("character", True):
            char = self.character_data.character
            lines.append(f"Character Level {char.level}")
            lines.append(f'Character Name "{char.name}"')
            lines.append(f'Character Class "{char.class_name}"')
            lines.append(f'Character Birthsign "{char.birthsign}"')

        # Attributes
        if export_options.get("attributes", True):
            for attr_name, attr_value in self.character_data.attributes.items():
                lines.append(f"Attribute {attr_name} {attr_value}")

        # Skills (no spaces in skill names)
        if export_options.get("skills", True):
            for skill_name, skill_value in self.character_data.skills.items():
                lines.append(f"Skill {skill_name} {skill_value}")

        # Fame, Infamy, Bounty
        if export_options.get("statistics", True):
            lines.append(f"Fame {self.character_data.fame}")
            lines.append(f"Infamy {self.character_data.infamy}")

            # Auto-cap bounty at 100000
            bounty = min(self.character_data.bounty, 100000)
            lines.append(f"Bounty {bounty}")

            # PCMiscStats (skip index 1)
            for idx in sorted(self.character_data.pc_misc_stats.keys()):
                if idx != 1:  # Skip index 1 (DAYS PASSED)
                    value = self.character_data.pc_misc_stats[idx]
                    lines.append(f"PCMiscStat {idx} {value}")

        # Factions (Form ID and rank only, no name/title)
        if export_options.get("factions", True):
            for faction in self.character_data.factions:
                lines.append(f"Faction {faction.form_id} {faction.rank}")

        # Completed Quests
        if export_options.get("completedQuests", True):
            for quest_id in self.character_data.completed_quests:
                lines.append(f"CompletedQuest {quest_id}")

        # Active Quest
        # OBSE script should handle this with: SetActiveQuest <form_id>
        if export_options.get("completedQuests", True):  # Use same option as completed quests
            if self.character_data.active_quest:
                active_quest = self.character_data.active_quest
                lines.append(f"ActiveQuest {active_quest.editor_id}")

        # Current Quests (quests in progress with their stages)
        # OBSE script should handle this with: SetStage <quest_id> <stage>
        if export_options.get("completedQuests", True):  # Use same option as completed quests
            for current_quest in self.character_data.current_quests:
                lines.append(f"CurrentQuest {current_quest.editor_id} {current_quest.stage}")

        # Vitals (Health, Magicka, Fatigue as actor values)
        if export_options.get("vitals", True):
            v = self.character_data.vitals
            if v.health_base > 0:
                lines.append(f"Health {int(v.health_base)}")
            if v.magicka_base > 0:
                lines.append(f"Magicka {int(v.magicka_base)}")
            if v.fatigue_base > 0:
                lines.append(f"Fatigue {int(v.fatigue_base)}")

        # Magic Resistances
        if export_options.get("resistances", True):
            r = self.character_data.magic_resistances
            if r.fire != 0:
                lines.append(f"Resistance Fire {int(r.fire)}")
            if r.frost != 0:
                lines.append(f"Resistance Frost {int(r.frost)}")
            if r.shock != 0:
                lines.append(f"Resistance Shock {int(r.shock)}")
            if r.magic != 0:
                lines.append(f"Resistance Magic {int(r.magic)}")
            if r.disease != 0:
                lines.append(f"Resistance Disease {int(r.disease)}")
            if r.poison != 0:
                lines.append(f"Resistance Poison {int(r.poison)}")
            if r.paralysis != 0:
                lines.append(f"Resistance Paralysis {int(r.paralysis)}")
            if r.normal_weapons != 0:
                lines.append(f"Resistance NormalWeapons {int(r.normal_weapons)}")

        # Global Variables
        if export_options.get("globalVariables", True):
            for gv in self.character_data.global_variables:
                lines.append(f"Global {gv.form_id} {gv.value}")

        # Game Time
        if export_options.get("gameTime", True):
            gt = self.character_data.game_time
            if gt.days_passed > 0:
                lines.append(f"GameTime {gt.days_passed}")
            lines.append(f"GameYear {gt.game_year}")
            lines.append(f"GameMonth {gt.game_month}")
            lines.append(f"GameDay {gt.game_day}")
            lines.append(f"GameHour {gt.game_hour}")

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
            f.flush()  # Force write to disk
            os.fsync(f.fileno())  # Ensure OS writes to disk immediately


def generate_import_log(character_data: CharacterData, output_path: Path, export_options: dict = None):
    """Generate import log file from character data."""
    generator = ImportLogGenerator(character_data)
    generator.generate(output_path, export_options)
