"""
Comprehensive Export Log Parser
Parses all sections of the Oblivion export log.
"""

from pathlib import Path
from typing import List
from models import (
    CharacterData, CharacterInfo, Spell, SpellEffect, InventoryItem,
    Faction, ActiveQuest, CurrentQuest, PCMiscStat, PCMISCSTAT_NAMES, ATTRIBUTE_NAMES, SKILL_NAMES
)


class ExportLogParser:
    """Parser for Oblivion export log (Static Log.log)."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.lines = []
        self.current_line = 0

    def parse(self) -> CharacterData:
        """Parse the complete export log."""
        with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
            self.lines = [line.rstrip() for line in f.readlines()]

        character_data = CharacterData()

        # Parse each section
        character_data.character = self.parse_player_info()
        character_data.attributes = self.parse_attributes()
        character_data.skills = self.parse_skills()
        character_data.spells = self.parse_spells()
        character_data.items = self.parse_inventory()
        character_data.fame, character_data.infamy, character_data.bounty = self.parse_fame_infamy_bounty()
        character_data.pc_misc_stats = self.parse_pc_misc_stats()
        character_data.factions = self.parse_factions()
        character_data.completed_quests = self.parse_quests()
        character_data.active_quest = self.parse_active_quest()
        character_data.current_quests = self.parse_current_quests()

        return character_data

    def find_section_start(self, marker: str, start_from: int = 0) -> int:
        """Find the line number where a section starts."""
        for i in range(start_from, len(self.lines)):
            if self.lines[i].strip() == marker:
                return i
        return -1

    def find_section_end(self, marker: str, start_from: int) -> int:
        """Find the line number where a section ends."""
        for i in range(start_from, len(self.lines)):
            if self.lines[i].strip() == marker:
                return i
        return -1

    def parse_player_info(self) -> CharacterInfo:
        """Parse Player info section."""
        start = self.find_section_start("Player info")
        if start == -1:
            return CharacterInfo()

        end = self.find_section_end("Player info END", start)
        if end == -1:
            end = len(self.lines)

        char_info = CharacterInfo()
        i = start + 1

        while i < end:
            line = self.lines[i].strip()

            if line == "name" and i + 1 < end:
                char_info.name = self.lines[i + 1].strip()
                i += 2
            elif line == "race" and i + 1 < end:
                char_info.race = self.lines[i + 1].strip()
                i += 2
            elif line == "class" and i + 1 < end:
                char_info.class_name = self.lines[i + 1].strip()
                i += 2
            elif line == "birthsign" and i + 1 < end:
                char_info.birthsign = self.lines[i + 1].strip()
                i += 2
            elif line == "level" and i + 1 < end:
                try:
                    char_info.level = int(float(self.lines[i + 1].strip()))
                except (ValueError, IndexError):
                    pass
                i += 2
            else:
                i += 1

        return char_info

    def parse_attributes(self) -> dict:
        """Parse Attributes section (CSV format: AttributeName,Value)."""
        start = self.find_section_start("Attributes")
        if start == -1:
            return {attr: 40 for attr in ATTRIBUTE_NAMES}

        end = self.find_section_end("Attributes END", start)
        if end == -1:
            end = len(self.lines)

        attributes = {}

        for i in range(start + 1, end):
            line = self.lines[i].strip()
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    attr_name = parts[0].strip()
                    try:
                        attr_value = int(float(parts[1].strip()))
                        attributes[attr_name] = attr_value
                    except ValueError:
                        pass

        # Fill missing attributes with defaults
        for attr in ATTRIBUTE_NAMES:
            if attr not in attributes:
                attributes[attr] = 40

        return attributes

    def parse_skills(self) -> dict:
        """Parse Skills section (CSV format: SkillName,Value)."""
        start = self.find_section_start("Skills")
        if start == -1:
            return {skill: 25 for skill in SKILL_NAMES}

        end = self.find_section_end("Skills END", start)
        if end == -1:
            end = len(self.lines)

        skills = {}

        for i in range(start + 1, end):
            line = self.lines[i].strip()
            if ',' in line:
                parts = line.split(',', 1)
                if len(parts) == 2:
                    skill_name = parts[0].strip()
                    try:
                        skill_value = int(float(parts[1].strip()))
                        skills[skill_name] = skill_value
                    except ValueError:
                        pass

        # Fill missing skills with defaults
        for skill in SKILL_NAMES:
            if skill not in skills:
                skills[skill] = 25

        return skills

    def parse_spells(self) -> List[Spell]:
        """Parse Spells section (verbose multi-line format)."""
        start = self.find_section_start("Spells")
        if start == -1:
            return []

        end = self.find_section_end("Spells END", start)
        if end == -1:
            end = len(self.lines)

        spells = []
        i = start + 1

        while i < end:
            line = self.lines[i].strip()

            if line == "This is the spell id":
                spell_id = None
                spell_name = None
                magicka_cost = 0
                effects = []

                # Get spell ID
                if i + 1 < end:
                    spell_id = self.lines[i + 1].strip()
                    i += 2

                # Get spell name
                if i < end and self.lines[i].strip() == "This is the spell name":
                    if i + 1 < end:
                        spell_name = self.lines[i + 1].strip()
                        i += 2

                # Skip "section for the spell properties"
                if i < end and self.lines[i].strip() == "section for the spell properties":
                    i += 1

                # Get magicka cost
                if i < end and self.lines[i].strip() == "this is the magicka cost":
                    if i + 1 < end:
                        try:
                            magicka_cost = int(float(self.lines[i + 1].strip()))
                        except (ValueError, IndexError):
                            pass
                        i += 2

                # Parse effects (may be multiple)
                while i < end:
                    line = self.lines[i].strip()

                    # Check if we've reached the next spell or end
                    if line in ["This is the spell id", "Spells END"]:
                        break

                    # Parse effect
                    if line.startswith("Effect Name"):
                        effect_name = line.split(":", 1)[-1].strip()
                        magnitude = 0
                        duration = 0
                        area = 0

                        # Get magnitude
                        if i + 1 < end and self.lines[i + 1].strip() == "This is the magnitude":
                            if i + 2 < end:
                                try:
                                    magnitude = int(float(self.lines[i + 2].strip()))
                                except (ValueError, IndexError):
                                    pass
                                i += 3

                        # Get duration
                        if i < end and self.lines[i].strip() == "This is the duration":
                            if i + 1 < end:
                                try:
                                    duration = int(float(self.lines[i + 1].strip()))
                                except (ValueError, IndexError):
                                    pass
                                i += 2

                        # Get area
                        if i < end and self.lines[i].strip() == "This is the area":
                            if i + 1 < end:
                                try:
                                    area = int(float(self.lines[i + 1].strip()))
                                except (ValueError, IndexError):
                                    pass
                                i += 2

                        effects.append(SpellEffect(
                            name=effect_name,
                            magnitude=magnitude,
                            duration=duration,
                            area=area
                        ))
                    else:
                        i += 1

                # Add spell if we have valid data
                if spell_id and spell_name:
                    spells.append(Spell(
                        form_id=spell_id,
                        name=spell_name,
                        magicka_cost=magicka_cost,
                        effects=effects
                    ))
            else:
                i += 1

        return spells

    def parse_inventory(self) -> List[InventoryItem]:
        """Parse Inventory section (COUNT/NAME/ITEMID format or Items format)."""
        # Try "Inventory" section first
        start = self.find_section_start("Inventory")
        end_marker = "Inventory END"

        # If not found, try "Items" section
        if start == -1:
            start = self.find_section_start("Items")
            end_marker = "Items END"

        if start == -1:
            return []

        end = self.find_section_end(end_marker, start)
        if end == -1:
            end = len(self.lines)

        items = []
        i = start + 1

        while i < end:
            line = self.lines[i].strip()

            # Stop if we hit PCMiscStat section
            if line == "now we move on to the player misc stats":
                break

            # Format 1: COUNT/NAME/ITEMID format
            if line.startswith("COUNT - Count attempt:"):
                try:
                    quantity = int(line.split(":")[-1].strip())

                    # Look ahead for NAME and ITEMID
                    if i + 2 < end:
                        name_line = self.lines[i + 1].strip()
                        itemid_line = self.lines[i + 2].strip()

                        if name_line.startswith("NAME - name of the item:") and itemid_line.startswith("ITEMID - id of the item:"):
                            name = name_line.split(":", 1)[-1].strip()
                            form_id = itemid_line.split(":")[-1].strip()

                            items.append(InventoryItem(
                                form_id=form_id,
                                name=name,
                                quantity=quantity
                            ))

                            i += 3
                            continue
                except (ValueError, IndexError):
                    pass

            # Format 2: "This is the formID" / "This is the item name" / "This is the number of said item" format
            elif line == "This is the formID":
                try:
                    if i + 5 < end:
                        form_id = self.lines[i + 1].strip()
                        name_marker = self.lines[i + 2].strip()
                        name = self.lines[i + 3].strip()
                        qty_marker = self.lines[i + 4].strip()
                        quantity = int(self.lines[i + 5].strip())

                        if name_marker == "This is the item name" and qty_marker == "This is the number of said item":
                            items.append(InventoryItem(
                                form_id=form_id,
                                name=name,
                                quantity=quantity
                            ))

                            i += 6
                            continue
                except (ValueError, IndexError):
                    pass

            i += 1

        return items

    def parse_pc_misc_stats(self) -> dict:
        """Parse PCMiscStat data (inside Inventory section, before Inventory END)."""
        start = self.find_section_start("now we move on to the player misc stats")
        if start == -1:
            return {idx: 0 for idx in PCMISCSTAT_NAMES.keys()}

        # Find Inventory END
        end = self.find_section_end("Inventory END", start)
        if end == -1:
            end = len(self.lines)

        pc_misc_stats = {}
        i = start + 1

        # Skip "the variables have been correctly initialized" line
        if i < end and self.lines[i].strip() == "the variables have been correctly initialized":
            i += 1

        while i < end:
            line = self.lines[i].strip()

            if line == "PCMiscStat index":
                if i + 3 < end:
                    try:
                        index_line = self.lines[i + 1].strip()
                        value_label = self.lines[i + 2].strip()
                        value_line = self.lines[i + 3].strip()

                        if value_label == "PCMiscStat value":
                            index = int(index_line)
                            value = int(value_line)

                            # Skip index 1 (DAYS PASSED - non-functional)
                            if index != 1:
                                pc_misc_stats[index] = value

                            i += 4
                            continue
                    except (ValueError, IndexError):
                        pass

            i += 1

        # Fill missing stats with defaults
        for idx in PCMISCSTAT_NAMES.keys():
            if idx not in pc_misc_stats:
                pc_misc_stats[idx] = 0

        return pc_misc_stats

    def parse_fame_infamy_bounty(self) -> tuple:
        """Parse Fame, Infamy, Bounty section."""
        start = self.find_section_start("Fame, Infamy, Bounty")
        if start == -1:
            return 0, 0, 0

        end = self.find_section_end("Fame, Infamy, Bounty END", start)
        if end == -1:
            end = len(self.lines)

        fame = 0
        infamy = 0
        bounty = 0

        i = start + 1
        while i < end:
            line = self.lines[i].strip()

            if line == "this is the fame" and i + 1 < end:
                try:
                    fame = int(self.lines[i + 1].strip())
                except (ValueError, IndexError):
                    pass
                i += 2
            elif line == "this is the infamy" and i + 1 < end:
                try:
                    infamy = int(self.lines[i + 1].strip())
                except (ValueError, IndexError):
                    pass
                i += 2
            elif line == "this is the bounty" and i + 1 < end:
                try:
                    bounty = int(self.lines[i + 1].strip())
                except (ValueError, IndexError):
                    pass
                i += 2
            else:
                i += 1

        return fame, infamy, bounty

    def parse_factions(self) -> List[Faction]:
        """Parse Factions section (FormID/Name/Rank/Title format or This is the faction id format)."""
        start = self.find_section_start("Factions")
        if start == -1:
            return []

        end = self.find_section_end("Factions END", start)
        if end == -1:
            end = len(self.lines)

        factions = []
        i = start + 1

        while i < end:
            line = self.lines[i].strip()

            # Format 1: FormID: format
            if line.startswith("FormID:"):
                form_id = line.split(":", 1)[-1].strip()

                # Check if next line is another FormID (rank < 0, skip)
                if i + 1 < end and self.lines[i + 1].strip().startswith("FormID:"):
                    i += 1
                    continue

                # Parse faction name and rank
                if i + 1 < end:
                    name_rank_line = self.lines[i + 1].strip()

                    if ", rank " in name_rank_line:
                        parts = name_rank_line.split(", rank ", 1)
                        faction_name = parts[0].strip()
                        try:
                            rank = int(parts[1].strip())
                        except ValueError:
                            rank = 0

                        # Parse title
                        title = ""
                        if i + 2 < end and self.lines[i + 2].strip().startswith("Title:"):
                            title = self.lines[i + 2].strip().split(":", 1)[-1].strip()
                            i += 3
                        else:
                            i += 2

                        factions.append(Faction(
                            form_id=form_id,
                            name=faction_name,
                            rank=rank,
                            title=title
                        ))
                        continue

            # Format 2: "This is the faction id" format
            elif line == "This is the faction id":
                try:
                    if i + 5 < end:
                        form_id = self.lines[i + 1].strip()
                        name_marker = self.lines[i + 2].strip()
                        name = self.lines[i + 3].strip()
                        rank_marker = self.lines[i + 4].strip()
                        rank = int(self.lines[i + 5].strip())

                        if name_marker == "This is the faction name" and rank_marker == "This is the faction rank":
                            factions.append(Faction(
                                form_id=form_id,
                                name=name,
                                rank=rank,
                                title=""
                            ))

                            i += 6
                            continue
                except (ValueError, IndexError):
                    pass

            i += 1

        return factions

    def parse_quests(self) -> List[str]:
        """Parse Completed Quests section (Completed Quest: QuestID format or quest id format)."""
        # Try "Completed Quests" first
        start = self.find_section_start("Completed Quests")
        end_marker = "Completed Quests END"

        # If not found, try "CompletedQuests"
        if start == -1:
            start = self.find_section_start("CompletedQuests")
            end_marker = "CompletedQuests END"

        if start == -1:
            return []

        end = self.find_section_end(end_marker, start)
        if end == -1:
            end = len(self.lines)

        quests = []
        i = start + 1

        while i < end:
            line = self.lines[i].strip()

            # Format 1: "Completed Quest:" format
            if line.startswith("Completed Quest:"):
                quest_id = line.split(":", 1)[-1].strip()
                quests.append(quest_id)
                i += 1

            # Format 2: "quest id" marker followed by the ID on next line
            elif line == "quest id":
                if i + 1 < end:
                    quest_id = self.lines[i + 1].strip()
                    quests.append(quest_id)
                    i += 2
                else:
                    i += 1
            else:
                i += 1

        return quests
    
    def parse_active_quest(self):
        """Parse Active Quest section (Active Quest: QuestID format).
        Active Quest
        This is the currently active quest
        0001E725
        Active Quest Editor ID: MQ03
        Active Quest END

        given the example above, we want to parse the editor ID "MQ03" and send it to the caller.

        """
        start = self.find_section_start("Active Quest")
        if start == -1:
            return None

        end = self.find_section_end("Active Quest END", start)
        if end == -1:
            end = len(self.lines)

        form_id = ""
        editor_id = ""

        for i in range(start + 1, end):
            line = self.lines[i].strip()

            if line.startswith("This is the currently active quest"):
                # Next line should be the form ID
                if i + 1 < end:
                    form_id = self.lines[i + 1].strip()
            elif line.startswith("Active Quest Editor ID:"):
                editor_id = line.split(":", 1)[-1].strip()

        if form_id:
            return ActiveQuest(form_id=form_id, editor_id=editor_id)
        return None

    def parse_current_quests(self) -> List[CurrentQuest]:
        """Parse Current Quests section.

        Current Quests
        Current Quest Editor ID: MidasDeadQuest
        current Quest Stage: 100
        Current Quest Editor ID: MidasSummonQuest
        current Quest Stage: 30
        Current Quests END
        """
        start = self.find_section_start("Current Quests")
        if start == -1:
            return []

        end = self.find_section_end("Current Quests END", start)
        if end == -1:
            end = len(self.lines)

        quests = []
        current_editor_id = ""

        for i in range(start + 1, end):
            line = self.lines[i].strip()

            if line.startswith("Current Quest Editor ID:"):
                current_editor_id = line.split(":", 1)[-1].strip()
            elif line.startswith("current Quest Stage:") and current_editor_id:
                try:
                    stage = int(line.split(":", 1)[-1].strip())
                    quests.append(CurrentQuest(editor_id=current_editor_id, stage=stage))
                    current_editor_id = ""  # Reset for next quest
                except ValueError:
                    pass

        return quests


def parse_export_log(log_path: Path) -> CharacterData:
    """Parse the export log (auto-detects format) and return CharacterData."""
    from save_dump_parser import is_save_dump_format, parse_save_dump

    if is_save_dump_format(log_path):
        return parse_save_dump(log_path)

    parser = ExportLogParser(log_path)
    return parser.parse()
