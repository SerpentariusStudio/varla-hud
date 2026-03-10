"""
Save Dump Parser for obse64 save data dump format.
Parses the === SECTION === delimited format from obse64.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from .character_models import (
    CharacterData, CharacterInfo, Spell, SpellEffect, InventoryItem,
    Faction, ActiveQuest, CurrentQuest, CompletedQuest,
    PCMISCSTAT_NAMES, ATTRIBUTE_NAMES, SKILL_NAMES,
    Vitals, MagicResistances, MagicEffects, GlobalVariable,
    GameTime, ActiveMagicEffect, PlayerPosition, WeatherInfo
)

# Mapping from save dump misc stat names (lowercased) to PCMISCSTAT index
MISC_STAT_NAME_TO_INDEX = {
    "days in prison": 0,
    "skill increases": 2,
    "training sessions": 3,
    "largest bounty": 4,
    "creatures killed": 5,
    "people killed": 6,
    "places discovered": 7,
    "locks picked": 8,
    "lockpicks broken": 9,
    "souls trapped": 10,
    "ingredients eaten": 11,
    "potions made": 12,
    "oblivion gates shut": 13,
    "horses owned": 14,
    "houses owned": 15,
    "stores invested in": 16,
    "books read": 17,
    "skill books read": 18,
    "artifacts found": 19,
    "hours slept": 20,
    "hours waited": 21,
    "days as a vampire": 22,
    "last day as a vampire": 23,
    "people fed on": 24,
    "jokes told": 25,
    "diseases contracted": 26,
    "nirnroots found": 27,
    "items stolen": 28,
    "items pickpocketed": 29,
    "trespasses": 30,
    "assaults": 31,
    "murders": 32,
    "horses stolen": 33,
    "days passed": 1,
}

# Mapping from classic xOBSE item type codes (hex string) to readable names
CLASSIC_ITEM_TYPE_MAP = {
    "01": "Ammunition",
    "13": "Apparatus",
    "14": "Armor",
    "15": "Book",
    "16": "Clothing",
    "19": "Ingredient",
    "1a": "Light",
    "1b": "Misc",
    "21": "Weapon",
    "27": "Key",
    "28": "Potion",
}

# Mapping from classic skill display names (with spaces) to storage names
CLASSIC_SKILL_NAME_MAP = {
    "Hand To Hand": "HandToHand",
    "Heavy Armor": "HeavyArmor",
    "Light Armor": "LightArmor",
}

# Short type codes used in classic global variables
CLASSIC_GLOBAL_TYPE_MAP = {
    "s": "short",
    "l": "long",
    "f": "float",
}


class SaveDumpParser:
    """Parser for obse64 save data dump files."""

    def __init__(self, dump_path: Path):
        self.dump_path = dump_path
        self.lines: List[str] = []
        self.sections: Dict[str, Tuple[int, int]] = {}

    def parse(self) -> CharacterData:
        """Parse the complete save dump file."""
        with open(self.dump_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
        self.lines = [line.rstrip() for line in raw_text.splitlines()]

        self._index_sections()

        data = CharacterData()

        # Store dump metadata for round-trip writing
        data.dump_format = "remastered"
        data.raw_dump_text = raw_text

        data.character = self._parse_character_info()
        data.player_position = self._parse_position()
        data.fame, data.infamy, data.bounty = self._parse_fame_infamy_bounty()
        data.game_time = self._parse_game_time()
        data.global_variables = self._parse_global_variables()
        data.pc_misc_stats = self._parse_misc_statistics()
        data.active_quest = self._parse_active_quest()
        data.current_quests = self._parse_active_quests_list()
        data.completed_quests, data.completed_quests_enriched = self._parse_completed_quests()
        data.factions = self._parse_factions()
        data.attributes = self._parse_attributes()
        data.vitals = self._parse_derived_stats()
        data.skills = self._parse_skills()
        data.magic_resistances, data.magic_effects = self._parse_magic_resistances_effects()
        data.spells = self._parse_spells()
        data.items = self._parse_inventory()
        data.weather = self._parse_weather()
        data.plugins = self._parse_plugin_list()
        data.active_magic_effects = self._parse_active_magic_effects()

        return data

    def _index_sections(self):
        """Build an index of section start/end positions."""
        section_pattern = re.compile(r'^=== (.+?) ===$')
        section_starts = []

        for i, line in enumerate(self.lines):
            m = section_pattern.match(line.strip())
            if m:
                section_starts.append((m.group(1), i))

        # Each section ends where the next one begins (or EOF)
        for idx, (name, start) in enumerate(section_starts):
            if idx + 1 < len(section_starts):
                end = section_starts[idx + 1][1]
            else:
                end = len(self.lines)
            self.sections[name] = (start, end)

    def _get_section_lines(self, section_name: str) -> List[str]:
        """Get the lines for a given section (excluding the header)."""
        if section_name not in self.sections:
            return []
        start, end = self.sections[section_name]
        return self.lines[start + 1:end]

    def _parse_character_info(self) -> CharacterInfo:
        """Parse PLAYER CHARACTER and CHARACTER INFO sections."""
        info = CharacterInfo()

        # From PLAYER CHARACTER section
        for line in self._get_section_lines("PLAYER CHARACTER"):
            line = line.strip()
            if line.startswith("Player Name:"):
                info.name = line.split(":", 1)[1].strip()

        # From CHARACTER INFO section
        for line in self._get_section_lines("CHARACTER INFO"):
            line = line.strip()
            if line.startswith("Level:"):
                try:
                    info.level = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Race:"):
                # Format: "Race: LOC_FN_DarkElf (0x000191C1)"
                raw = line.split(":", 1)[1].strip()
                info.race = raw.split("(")[0].strip()
            elif line.startswith("Class:"):
                raw = line.split(":", 1)[1].strip()
                info.class_name = raw.split("(")[0].strip()
            elif line.startswith("Birthsign:"):
                raw = line.split(":", 1)[1].strip()
                info.birthsign = raw.split("(")[0].strip()

        return info

    def _parse_position(self) -> PlayerPosition:
        """Parse POSITION & ROTATION section."""
        pos = PlayerPosition()
        for line in self._get_section_lines("POSITION & ROTATION"):
            line = line.strip()
            if line.startswith("Position X:"):
                try:
                    pos.x = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Position Y:"):
                try:
                    pos.y = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Position Z:"):
                try:
                    pos.z = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Rotation X:"):
                try:
                    # Format: "Rotation X: 0.1713 (radians) / 9.82 (degrees)"
                    val = line.split(":", 1)[1].strip().split("(")[0].strip()
                    pos.rot_x = float(val)
                except ValueError:
                    pass
            elif line.startswith("Rotation Y:"):
                try:
                    val = line.split(":", 1)[1].strip().split("(")[0].strip()
                    pos.rot_y = float(val)
                except ValueError:
                    pass
            elif line.startswith("Rotation Z:"):
                try:
                    val = line.split(":", 1)[1].strip().split("(")[0].strip()
                    pos.rot_z = float(val)
                except ValueError:
                    pass
            elif line.startswith("Scale:"):
                try:
                    pos.scale = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Parent Cell:"):
                # Format: "Parent Cell: LOC_FN_KvatchTentSavlianMatius (0x0002A5C5)"
                raw = line.split(":", 1)[1].strip()
                m = re.match(r'(.+?)\s*\((0x[0-9A-Fa-f]+)\)', raw)
                if m:
                    pos.parent_cell = m.group(1).strip()
                    pos.parent_cell_form_id = m.group(2)
                else:
                    pos.parent_cell = raw

        return pos

    def _parse_fame_infamy_bounty(self) -> tuple:
        """Parse FAME / INFAMY / BOUNTY section."""
        fame = 0
        infamy = 0
        bounty = 0
        for line in self._get_section_lines("FAME / INFAMY / BOUNTY"):
            line = line.strip()
            if line.startswith("Fame:"):
                try:
                    fame = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Infamy:"):
                try:
                    infamy = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Bounty:"):
                try:
                    bounty = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return fame, infamy, bounty

    def _parse_game_time(self) -> GameTime:
        """Parse GAME TIME section."""
        gt = GameTime()
        for line in self._get_section_lines("GAME TIME"):
            line = line.strip()
            if line.startswith("Days Passed:"):
                try:
                    gt.days_passed = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Game Date:"):
                # Format: "Game Date: Year 433, Month 8, Day 14"
                raw = line.split(":", 1)[1].strip()
                m = re.match(r'Year\s+(\d+),\s*Month\s+(\d+),\s*Day\s+(\d+)', raw)
                if m:
                    gt.game_year = int(m.group(1))
                    gt.game_month = int(m.group(2))
                    gt.game_day = int(m.group(3))
            elif line.startswith("Game Time:"):
                # Format: "Game Time: 18:14 (18.24)"
                raw = line.split(":", 1)[1].strip()
                m = re.search(r'\((\d+\.?\d*)\)', raw)
                if m:
                    gt.game_hour = float(m.group(1))

        return gt

    def _parse_global_variables(self) -> List[GlobalVariable]:
        """Parse GLOBAL VARIABLES section."""
        variables = []
        for line in self._get_section_lines("GLOBAL VARIABLES"):
            line = line.strip()
            if not line or line.startswith("Total Globals:"):
                continue
            # Format: "  PCInfamy (0x0A000CE7) = 0.00 [short]"
            m = re.match(r'(\w+)\s+\((0x[0-9A-Fa-f]+)\)\s*=\s*([\d.\-]+)\s*\[(\w+)\]', line)
            if m:
                variables.append(GlobalVariable(
                    name=m.group(1),
                    form_id=m.group(2),
                    value=float(m.group(3)),
                    var_type=m.group(4)
                ))
        return variables

    def _parse_misc_statistics(self) -> Dict[int, int]:
        """Parse MISC STATISTICS section."""
        stats = {}
        for line in self._get_section_lines("MISC STATISTICS"):
            line = line.strip()
            if not line:
                continue
            # Format: "Days In Prison: 0"
            if ":" in line:
                parts = line.rsplit(":", 1)
                if len(parts) == 2:
                    name = parts[0].strip().lower()
                    try:
                        value = int(parts[1].strip())
                        idx = MISC_STAT_NAME_TO_INDEX.get(name)
                        if idx is not None:
                            stats[idx] = value
                    except ValueError:
                        pass

        # Fill missing stats with defaults
        for idx in PCMISCSTAT_NAMES.keys():
            if idx not in stats:
                stats[idx] = 0

        return stats

    def _parse_active_quest(self) -> Optional[ActiveQuest]:
        """Parse ACTIVE QUEST section."""
        form_id = ""
        editor_id = ""
        name = ""
        stage = 0
        flags = ""

        for line in self._get_section_lines("ACTIVE QUEST"):
            line = line.strip()
            if line.startswith("Quest Form ID:"):
                form_id = line.split(":", 1)[1].strip()
            elif line.startswith("Quest Name:"):
                name = line.split(":", 1)[1].strip()
            elif line.startswith("Quest Editor ID:"):
                editor_id = line.split(":", 1)[1].strip()
            elif line.startswith("Quest Flags:"):
                flags = line.split(":", 1)[1].strip()
            elif line.startswith("Current Stage:"):
                try:
                    stage = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass

        if form_id or editor_id:
            return ActiveQuest(
                form_id=form_id,
                editor_id=editor_id,
                name=name,
                stage=stage,
                flags=flags
            )
        return None

    def _parse_active_quests_list(self) -> List[CurrentQuest]:
        """Parse ACTIVE QUESTS (Started, Not Completed) section."""
        quests = []
        section_lines = self._get_section_lines("ACTIVE QUESTS (Started, Not Completed)")

        current_name = ""
        current_form_id = ""
        current_editor_id = ""
        current_stage = 0
        current_flags = ""
        in_quest = False

        for line in section_lines:
            line = line.strip()
            if not line:
                continue

            # Quest header: "[0] LOC_FN_AltarWatersEdgeFix (0x0B0106F8)"
            m = re.match(r'\[\d+\]\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)', line)
            if m:
                # Save previous quest if any
                if in_quest and current_editor_id:
                    quests.append(CurrentQuest(
                        editor_id=current_editor_id,
                        stage=current_stage,
                        name=current_name,
                        form_id=current_form_id,
                        flags=current_flags
                    ))

                current_name = m.group(1)
                if current_name == "<no name>":
                    current_name = ""
                current_form_id = m.group(2)
                current_editor_id = ""
                current_stage = 0
                current_flags = ""
                in_quest = True
                continue

            if in_quest:
                if line.startswith("Editor ID:"):
                    current_editor_id = line.split(":", 1)[1].strip()
                elif line.startswith("Current Stage:"):
                    try:
                        current_stage = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.startswith("Flags:"):
                    current_flags = line.split(":", 1)[1].strip()

        # Don't forget the last quest
        if in_quest and current_editor_id:
            quests.append(CurrentQuest(
                editor_id=current_editor_id,
                stage=current_stage,
                name=current_name,
                form_id=current_form_id,
                flags=current_flags
            ))

        return quests

    def _parse_completed_quests(self) -> Tuple[List[str], List[CompletedQuest]]:
        """Parse COMPLETED QUESTS section. Returns (simple list, enriched list)."""
        simple_list = []
        enriched_list = []

        section_lines = self._get_section_lines("COMPLETED QUESTS")

        current_name = ""
        current_form_id = ""
        current_editor_id = ""
        current_final_stage = 0
        in_quest = False

        for line in section_lines:
            line = line.strip()
            if not line:
                continue

            # Quest header: "[0] LOC_FN_MS48 (0x000224D8)"
            m = re.match(r'\[\d+\]\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)', line)
            if m:
                # Save previous quest if any
                if in_quest and current_editor_id:
                    simple_list.append(current_editor_id)
                    enriched_list.append(CompletedQuest(
                        editor_id=current_editor_id,
                        name=current_name,
                        form_id=current_form_id,
                        final_stage=current_final_stage
                    ))

                current_name = m.group(1)
                if current_name == "<no name>":
                    current_name = ""
                current_form_id = m.group(2)
                current_editor_id = ""
                current_final_stage = 0
                in_quest = True
                continue

            if in_quest:
                if line.startswith("Editor ID:"):
                    current_editor_id = line.split(":", 1)[1].strip()
                elif line.startswith("Final Stage:"):
                    try:
                        current_final_stage = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass

        # Don't forget the last quest
        if in_quest and current_editor_id:
            simple_list.append(current_editor_id)
            enriched_list.append(CompletedQuest(
                editor_id=current_editor_id,
                name=current_name,
                form_id=current_form_id,
                final_stage=current_final_stage
            ))

        return simple_list, enriched_list

    def _parse_factions(self) -> List[Faction]:
        """Parse FACTIONS section."""
        factions = []

        for line in self._get_section_lines("FACTIONS"):
            line = line.strip()
            if not line or line.startswith("Number of Factions:"):
                continue

            # Format: "[0] LOC_FN_PlayerFaction (0x0001DBCD) - Rank: 0"
            m = re.match(r'\[\d+\]\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)\s*-\s*Rank:\s*(-?\d+)', line)
            if m:
                factions.append(Faction(
                    form_id=m.group(2),
                    name=m.group(1),
                    rank=int(m.group(3)),
                    title=""
                ))

        return factions

    def _parse_attributes(self) -> Dict[str, int]:
        """Parse ATTRIBUTES section."""
        attributes = {}

        for line in self._get_section_lines("ATTRIBUTES"):
            line = line.strip()
            if not line or line.startswith("Format:"):
                continue

            # Format: "  Strength: 75 (Base: 75)"
            m = re.match(r'(\w+):\s*\d+\s*\(Base:\s*(\d+)\)', line)
            if m:
                attr_name = m.group(1)
                base_value = int(m.group(2))
                if attr_name in ATTRIBUTE_NAMES:
                    attributes[attr_name] = base_value

        # Fill missing attributes with defaults
        for attr in ATTRIBUTE_NAMES:
            if attr not in attributes:
                attributes[attr] = 40

        return attributes

    def _parse_derived_stats(self) -> Vitals:
        """Parse DERIVED STATS section."""
        vitals = Vitals()

        for line in self._get_section_lines("DERIVED STATS"):
            line = line.strip()
            if not line or line.startswith("Format:"):
                continue

            # Format: "Health: 259 / 259 (Base: 259) [0 | 0 | 0]"
            if line.startswith("Health:"):
                m = re.match(r'Health:\s*([\d.]+)\s*/\s*[\d.]+\s*\(Base:\s*([\d.]+)\)', line)
                if m:
                    vitals.health_current = float(m.group(1))
                    vitals.health_base = float(m.group(2))
            elif line.startswith("Magicka:"):
                m = re.match(r'Magicka:\s*([\d.]+)\s*/\s*[\d.]+\s*\(Base:\s*([\d.]+)\)', line)
                if m:
                    vitals.magicka_current = float(m.group(1))
                    vitals.magicka_base = float(m.group(2))
            elif line.startswith("Fatigue:"):
                m = re.match(r'Fatigue:\s*([\d.]+)\s*/\s*[\d.]+\s*\(Base:\s*([\d.]+)\)', line)
                if m:
                    vitals.fatigue_current = float(m.group(1))
                    vitals.fatigue_base = float(m.group(2))
            elif line.startswith("Encumbrance:"):
                m = re.match(r'Encumbrance:\s*([\d.]+)', line)
                if m:
                    vitals.encumbrance = float(m.group(1))

        return vitals

    def _parse_skills(self) -> Dict[str, int]:
        """Parse SKILLS section."""
        skills = {}

        for line in self._get_section_lines("SKILLS"):
            line = line.strip()
            if not line or line.startswith("Format:") or line.endswith("Skills:"):
                continue

            # Format: "  Armorer: 34 (Base: 34)"
            m = re.match(r'(\w+):\s*\d+\s*\(Base:\s*(\d+)\)', line)
            if m:
                skill_name = m.group(1)
                base_value = int(m.group(2))
                if skill_name in SKILL_NAMES:
                    skills[skill_name] = base_value

        # Fill missing skills with defaults
        for skill in SKILL_NAMES:
            if skill not in skills:
                skills[skill] = 25

        return skills

    def _parse_magic_resistances_effects(self) -> Tuple[MagicResistances, MagicEffects]:
        """Parse MAGIC RESISTANCES & EFFECTS section."""
        resistances = MagicResistances()
        effects = MagicEffects()

        in_resistances = False
        in_effects = False

        for line in self._get_section_lines("MAGIC RESISTANCES & EFFECTS"):
            line = line.strip()
            if not line:
                continue

            if line == "Resistances:":
                in_resistances = True
                in_effects = False
                continue
            elif line == "Magic Effects:":
                in_resistances = False
                in_effects = True
                continue

            if in_resistances:
                # Format: "  Resist Fire: 75%"
                m = re.match(r'Resist\s+(.+?):\s*([\d.\-]+)%?', line)
                if m:
                    name = m.group(1).lower()
                    value = float(m.group(2))
                    if name == "fire":
                        resistances.fire = value
                    elif name == "frost":
                        resistances.frost = value
                    elif name == "shock":
                        resistances.shock = value
                    elif name == "magic":
                        resistances.magic = value
                    elif name == "disease":
                        resistances.disease = value
                    elif name == "poison":
                        resistances.poison = value
                    elif name == "paralysis":
                        resistances.paralysis = value
                    elif name == "normal weapons":
                        resistances.normal_weapons = value

            elif in_effects:
                # Format: "  Spell Absorption: 50%"
                if line.startswith("Spell Absorption:"):
                    m = re.search(r'([\d.\-]+)%?', line.split(":", 1)[1])
                    if m:
                        effects.spell_absorption = float(m.group(1))
                elif line.startswith("Spell Reflect:"):
                    m = re.search(r'([\d.\-]+)%?', line.split(":", 1)[1])
                    if m:
                        effects.spell_reflect = float(m.group(1))
                elif line.startswith("Reflect Damage:"):
                    m = re.search(r'([\d.\-]+)%?', line.split(":", 1)[1])
                    if m:
                        effects.reflect_damage = float(m.group(1))
                elif line.startswith("Chameleon:"):
                    m = re.search(r'([\d.\-]+)%?', line.split(":", 1)[1])
                    if m:
                        effects.chameleon = float(m.group(1))
                elif line.startswith("Invisibility:"):
                    m = re.search(r'([\d.\-]+)', line.split(":", 1)[1])
                    if m:
                        effects.invisibility = float(m.group(1))
                elif line.startswith("Stunted Magicka:"):
                    m = re.search(r'(\d+)', line.split(":", 1)[1])
                    if m:
                        effects.stunted_magicka = int(m.group(1))

        return resistances, effects

    def _parse_spells(self) -> List[Spell]:
        """Parse SPELLS section."""
        spells = []

        for line in self._get_section_lines("SPELLS"):
            line = line.strip()
            if not line or line.startswith("Number of Spells:"):
                continue

            # Spell header: "[0] LOC_FN_PwRaceDarkElfGuardian (0x00047AD5)"
            m = re.match(r'\[\d+\]\s+(.+?)\s+\((0x[0-9A-Fa-f]+)\)', line)
            if m:
                spell_name = m.group(1)
                spell_form_id = m.group(2)
                # The next line should have type and cost
                # We'll store temporarily and update when we see the detail line
                spells.append(Spell(
                    form_id=spell_form_id,
                    name=spell_name,
                    magicka_cost=0,
                    spell_type=""
                ))
                continue

            # Detail line: "     Type: Power, Cost: 0"
            if line.startswith("Type:") and spells:
                m = re.match(r'Type:\s*(\w+),\s*Cost:\s*(\d+)', line)
                if m:
                    spells[-1].spell_type = m.group(1)
                    try:
                        cost = int(m.group(2))
                        # Cap overflow values (4294967295 = uint32 max from bad data)
                        if cost > 100000:
                            cost = 0
                        spells[-1].magicka_cost = cost
                    except ValueError:
                        pass
                continue

            # Effect line with range in parens: "  Drain Health [DRHE] (Touch) Mag: 5 Dur: 10s"
            if spells:
                em = re.match(
                    r'(.+?)\s+\[\w+\]\s+\((Self|Touch|Target)\)\s+Mag:\s*(\d+)\s+Dur:\s*(\d+)',
                    line
                )
                if em:
                    spells[-1].effects.append(SpellEffect(
                        name=em.group(1).strip(),
                        magnitude=int(em.group(3)),
                        duration=int(em.group(4)),
                        area=0,
                        range=em.group(2)
                    ))
                    continue
                # Alternate effect format: "[0] Drain Health - Mag: 5, Dur: 10, Area: 0, Range: Touch, Cost: 10.50"
                em2 = re.match(
                    r'\[\d+\]\s+(.+?)\s+-\s+Mag:\s*(\d+),\s*Dur:\s*(\d+),\s*Area:\s*(\d+),\s*Range:\s*(Self|Touch|Target)',
                    line
                )
                if em2:
                    spells[-1].effects.append(SpellEffect(
                        name=em2.group(1).strip(),
                        magnitude=int(em2.group(2)),
                        duration=int(em2.group(3)),
                        area=int(em2.group(4)),
                        range=em2.group(5)
                    ))

        return spells

    def _parse_inventory(self) -> List[InventoryItem]:
        """Parse INVENTORY section."""
        items = []

        for line in self._get_section_lines("INVENTORY"):
            line = line.strip()
            if not line or line.startswith("Total Weight:") or line.startswith("Armor Weight:") or line.startswith("Items:") or line.startswith("Total unique"):
                continue

            # Format: "[0] LOC_FN_ScrollStandardSummonClannfearExpert x1 (0x00015AD9) [Book]"
            # Or:     "[31] LOC_FN_DremoraClaymoreEnchAbsorbMagicka x1 (0x000149EF) [Weapon] [EQUIPPED]"
            # Extended: "[0] Iron Sword x1 (0x00012EB7) [Weapon] HP:80/100 Charge:50/200"
            m = re.match(
                r'\[\d+\]\s+(.+?)\s+x(-?\d+)\s+\((0x[0-9A-Fa-f]+)\)\s*\[(\w[\w\s]*)\](?:\s*\[EQUIPPED\])?',
                line
            )
            if m:
                item_name = m.group(1)
                quantity = int(m.group(2))
                form_id = m.group(3)
                item_type = m.group(4).strip()
                equipped = "[EQUIPPED]" in line

                item = InventoryItem(
                    form_id=form_id,
                    name=item_name,
                    quantity=quantity,
                    item_type=item_type,
                    equipped=equipped
                )

                # Parse optional HP: and Charge: suffixes
                hp_match = re.search(r'HP:([\d.]+)/([\d.]+)', line)
                charge_match = re.search(r'Charge:([\d.]+)/([\d.]+)', line)
                if hp_match:
                    item.condition_current = float(hp_match.group(1))
                    item.condition_max = float(hp_match.group(2))
                if charge_match:
                    item.enchant_current = float(charge_match.group(1))
                    item.enchant_max = float(charge_match.group(2))

                items.append(item)

        return items

    def _parse_weather(self) -> WeatherInfo:
        """Parse WEATHER / SKY section."""
        weather = WeatherInfo()
        for line in self._get_section_lines("WEATHER / SKY"):
            line = line.strip()
            if line.startswith("Current Weather:"):
                raw = line.split(":", 1)[1].strip()
                m = re.search(r'\((0x[0-9A-Fa-f]+)\)', raw)
                if m:
                    weather.current_weather_form_id = m.group(1)
                    weather.current_weather = raw.split("(")[0].strip()
            elif line.startswith("Climate:"):
                raw = line.split(":", 1)[1].strip()
                m = re.search(r'\((0x[0-9A-Fa-f]+)\)', raw)
                if m:
                    weather.climate_form_id = m.group(1)
            elif line.startswith("Sky Mode:"):
                try:
                    weather.sky_mode = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return weather

    def _parse_plugin_list(self) -> List[str]:
        """Parse PLUGIN LIST section."""
        plugins = []
        for line in self._get_section_lines("PLUGIN LIST"):
            line = line.strip()
            if not line or line.startswith("Plugin Count:") or line.startswith("Loaded Plugins:"):
                continue
            # Format: "  [ 0] Oblivion.esm"
            m = re.match(r'\[\s*\d+\]\s+(.+)', line)
            if m:
                plugins.append(m.group(1).strip())
        return plugins

    def _parse_active_magic_effects(self) -> List[ActiveMagicEffect]:
        """Parse ACTIVE MAGIC EFFECTS section."""
        effects = []
        section_lines = self._get_section_lines("ACTIVE MAGIC EFFECTS")

        current_effect = None
        for line in section_lines:
            line = line.strip()
            if not line or line.startswith("Total active"):
                continue

            # Effect line: "[0] STMA  Mag=1.0  Dur=0.0  State=Removed"
            m = re.match(r'\[\d+\]\s+(\w+)\s+Mag=([\d.\-]+)\s+Dur=([\d.\-]+)\s+State=(\w+)', line)
            if m:
                current_effect = ActiveMagicEffect(
                    effect_code=m.group(1),
                    magnitude=float(m.group(2)),
                    duration=float(m.group(3)),
                    state=m.group(4)
                )
                effects.append(current_effect)
                continue

            # Source line: "     Source: <no name> (0x00000000)  Caster: 0x00000000"
            if line.startswith("Source:") and current_effect:
                m = re.match(r'Source:\s*(.+?)\s*\((0x[0-9A-Fa-f]+)\)', line)
                if m:
                    source_name = m.group(1)
                    if source_name == "<no name>":
                        source_name = ""
                    current_effect.source_name = source_name
                    current_effect.source_form_id = m.group(2)

        return effects


class ClassicSaveDumpParser:
    """Parser for xOBSE (classic Oblivion) save data dump files."""

    def __init__(self, dump_path: Path):
        self.dump_path = dump_path
        self.lines: List[str] = []
        self.sections: Dict[str, Tuple[int, int]] = {}
        self.equipped_form_ids: set = set()

    def parse(self) -> CharacterData:
        """Parse the complete save dump file."""
        with open(self.dump_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
        self.lines = [line.rstrip() for line in raw_text.splitlines()]

        self._index_sections()

        data = CharacterData()

        # Store dump metadata for round-trip writing
        data.dump_format = "classic"
        data.raw_dump_text = raw_text

        data.character = self._parse_character_info()
        data.player_position = self._parse_position()
        data.attributes = self._parse_attributes()
        data.skills = self._parse_skills()
        data.vitals = self._parse_derived_stats()
        data.fame, data.infamy, data.bounty = self._parse_fame_infamy_bounty()
        data.game_time = self._parse_game_time()
        data.global_variables = self._parse_global_variables()
        data.pc_misc_stats = self._parse_misc_statistics()
        data.active_quest = self._parse_active_quest()
        self.equipped_form_ids = self._parse_equipped_items()
        data.spells = self._parse_spells()
        data.items = self._parse_inventory()
        data.factions = self._parse_factions()
        data.active_magic_effects = self._parse_active_effects()
        data.plugins = self._parse_plugins()

        return data

    def _index_sections(self):
        """Build index of section positions using --- markers."""
        section_pattern = re.compile(r'^--- (.+?) ---$')
        section_starts = []

        for i, line in enumerate(self.lines):
            m = section_pattern.match(line.strip())
            if m:
                section_starts.append((m.group(1), i))

        for idx, (name, start) in enumerate(section_starts):
            if idx + 1 < len(section_starts):
                end = section_starts[idx + 1][1]
            else:
                end = len(self.lines)
            self.sections[name] = (start, end)

    def _get_section_lines(self, section_name: str) -> List[str]:
        """Get the lines for a given section (excluding the header)."""
        if section_name not in self.sections:
            return []
        start, end = self.sections[section_name]
        return self.lines[start + 1:end]

    def _parse_character_info(self) -> CharacterInfo:
        """Parse Player Character and Character Info sections."""
        info = CharacterInfo()

        # From "Player Character" section
        for line in self._get_section_lines("Player Character"):
            line = line.strip()
            if line.startswith("Name:"):
                info.name = line.split(":", 1)[1].strip()

        # From "Character Info" section
        for line in self._get_section_lines("Character Info"):
            line = line.strip()
            if line.startswith("Level:"):
                try:
                    info.level = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Race:"):
                # Format: "Race: Argonian (ID: 00023FE9)"
                raw = line.split(":", 1)[1].strip()
                info.race = raw.split("(")[0].strip()
            elif line.startswith("Class:"):
                # Format: "Class: Scout (ID: 0002378A)"
                raw = line.split(":", 1)[1].strip()
                info.class_name = raw.split("(")[0].strip()
            elif line.startswith("Gender:"):
                info.sex = line.split(":", 1)[1].strip()

        return info

    def _parse_position(self) -> PlayerPosition:
        """Parse Position & Rotation section."""
        pos = PlayerPosition()
        for line in self._get_section_lines("Position & Rotation"):
            line = line.strip()
            if line.startswith("Position:"):
                # Format: "Position: 2108.88, 2117.82, 7680.95"
                raw = line.split(":", 1)[1].strip()
                parts = [p.strip() for p in raw.split(",")]
                try:
                    if len(parts) >= 3:
                        pos.x = float(parts[0])
                        pos.y = float(parts[1])
                        pos.z = float(parts[2])
                except ValueError:
                    pass
            elif line.startswith("Rotation:"):
                # Format: "Rotation: -0.5200, -0.0000, 4.1452"
                raw = line.split(":", 1)[1].strip()
                parts = [p.strip() for p in raw.split(",")]
                try:
                    if len(parts) >= 3:
                        pos.rot_x = float(parts[0])
                        pos.rot_y = float(parts[1])
                        pos.rot_z = float(parts[2])
                except ValueError:
                    pass
            elif line.startswith("Scale:"):
                try:
                    pos.scale = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Cell:"):
                # Format: "Cell: Savlian Matius's Tent  (ID: 0002A5C5)"
                raw = line.split(":", 1)[1].strip()
                m = re.match(r'(.+?)\s+\(ID:\s*([0-9A-Fa-f]+)\)', raw)
                if m:
                    pos.parent_cell = m.group(1).strip()
                    pos.parent_cell_form_id = "0x" + m.group(2)
                else:
                    pos.parent_cell = raw

        return pos

    def _parse_attributes(self) -> Dict[str, int]:
        """Parse Attributes section."""
        attributes = {}

        for line in self._get_section_lines("Attributes"):
            line = line.strip()
            if not line:
                continue
            # Format: "Strength       : 45 (base: 45)"
            m = re.match(r'([\w\s]+?)\s*:\s*\d+\s*\(base:\s*(\d+)\)', line)
            if m:
                attr_name = m.group(1).strip()
                base_value = int(m.group(2))
                if attr_name in ATTRIBUTE_NAMES:
                    attributes[attr_name] = base_value

        for attr in ATTRIBUTE_NAMES:
            if attr not in attributes:
                attributes[attr] = 40

        return attributes

    def _parse_skills(self) -> Dict[str, int]:
        """Parse Skills section."""
        skills = {}

        for line in self._get_section_lines("Skills"):
            line = line.strip()
            if not line or line.startswith("Major Skill") or line.startswith("Can Level"):
                continue
            # Format: "Armorer        : 30 (base: 30)  exp: 4.5 / 19.1"
            m = re.match(r'([\w\s]+?)\s*:\s*\d+\s*\(base:\s*(\d+)\)', line)
            if m:
                skill_display = m.group(1).strip()
                base_value = int(m.group(2))
                # Map display name to storage name
                skill_name = CLASSIC_SKILL_NAME_MAP.get(skill_display, skill_display)
                if skill_name in SKILL_NAMES:
                    skills[skill_name] = base_value

        for skill in SKILL_NAMES:
            if skill not in skills:
                skills[skill] = 25

        return skills

    def _parse_derived_stats(self) -> Vitals:
        """Parse Derived Stats section."""
        vitals = Vitals()

        for line in self._get_section_lines("Derived Stats"):
            line = line.strip()
            if not line:
                continue
            # Format: "Health:  80 / 80"
            if line.startswith("Health:"):
                m = re.match(r'Health:\s*([\d.]+)\s*/\s*([\d.]+)', line)
                if m:
                    vitals.health_current = float(m.group(1))
                    vitals.health_base = float(m.group(2))
            elif line.startswith("Magicka:"):
                m = re.match(r'Magicka:\s*([\d.]+)\s*/\s*([\d.]+)', line)
                if m:
                    vitals.magicka_current = float(m.group(1))
                    vitals.magicka_base = float(m.group(2))
            elif line.startswith("Fatigue:"):
                m = re.match(r'Fatigue:\s*([\d.]+)\s*/\s*([\d.]+)', line)
                if m:
                    vitals.fatigue_current = float(m.group(1))
                    vitals.fatigue_base = float(m.group(2))
            elif line.startswith("Encumbrance:"):
                m = re.match(r'Encumbrance:\s*([\d.]+)', line)
                if m:
                    vitals.encumbrance = float(m.group(1))

        return vitals

    def _parse_fame_infamy_bounty(self) -> tuple:
        """Parse Fame / Infamy / Bounty section."""
        fame = 0
        infamy = 0
        bounty = 0
        for line in self._get_section_lines("Fame / Infamy / Bounty"):
            line = line.strip()
            if line.startswith("Fame:"):
                try:
                    fame = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Infamy:"):
                try:
                    infamy = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Bounty:"):
                try:
                    bounty = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return fame, infamy, bounty

    def _parse_game_time(self) -> GameTime:
        """Parse Game Time section."""
        gt = GameTime()
        for line in self._get_section_lines("Game Time"):
            line = line.strip()
            if line.startswith("Year:"):
                try:
                    gt.game_year = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Month:"):
                try:
                    gt.game_month = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Day:"):
                try:
                    gt.game_day = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Hour:"):
                try:
                    gt.game_hour = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("Days Passed:"):
                try:
                    gt.days_passed = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
        return gt

    def _parse_global_variables(self) -> List[GlobalVariable]:
        """Parse Global Variables section."""
        variables = []
        for line in self._get_section_lines("Global Variables"):
            line = line.strip()
            if not line or line.startswith("Total:"):
                continue
            # Format: "[0A000CE7] PCInfamy                       (s) = 0.0000"
            m = re.match(
                r'\[([0-9A-Fa-f]+)\]\s+(\w+)\s+\((\w)\)\s*=\s*([\d.\-]+)',
                line
            )
            if m:
                form_id = "0x" + m.group(1).upper()
                name = m.group(2)
                var_type = CLASSIC_GLOBAL_TYPE_MAP.get(m.group(3), "short")
                value = float(m.group(4))
                variables.append(GlobalVariable(
                    form_id=form_id,
                    name=name,
                    value=value,
                    var_type=var_type
                ))
        return variables

    def _parse_misc_statistics(self) -> Dict[int, int]:
        """Parse Misc Statistics section."""
        stats = {}
        for line in self._get_section_lines("Misc Statistics"):
            line = line.strip()
            if not line:
                continue
            # Format: "Days in Prison                : 0"
            if ":" in line:
                parts = line.rsplit(":", 1)
                if len(parts) == 2:
                    name = parts[0].strip().lower()
                    try:
                        value = int(parts[1].strip())
                        idx = MISC_STAT_NAME_TO_INDEX.get(name)
                        if idx is not None:
                            stats[idx] = value
                    except ValueError:
                        pass

        for idx in PCMISCSTAT_NAMES.keys():
            if idx not in stats:
                stats[idx] = 0

        return stats

    def _parse_active_quest(self) -> Optional[ActiveQuest]:
        """Parse Active Quest section."""
        lines = self._get_section_lines("Active Quest")
        for line in lines:
            line = line.strip()
            if line == "(none)" or not line:
                continue
            # If there's actual quest data, try to parse it
            # Classic format may just show "(none)" or minimal info
            m = re.match(r'\[([0-9A-Fa-f]+)\]\s+(.+)', line)
            if m:
                return ActiveQuest(
                    form_id="0x" + m.group(1).upper(),
                    editor_id=m.group(2).strip(),
                    name=m.group(2).strip(),
                    stage=0
                )
        return None

    def _parse_equipped_items(self) -> set:
        """Parse Equipped Items section to get set of equipped form IDs."""
        equipped = set()
        for line in self._get_section_lines("Equipped Items"):
            line = line.strip()
            if not line:
                continue
            # Format: "[0] Steel Claymore (ID: 000229B8, Type: 21)"
            m = re.match(r'\[\d+\]\s+.+?\(ID:\s*([0-9A-Fa-f]+)', line)
            if m:
                equipped.add(m.group(1).upper())
        return equipped

    def _parse_spells(self) -> List[Spell]:
        """Parse Known Spells section."""
        spells = []
        for line in self._get_section_lines("Known Spells"):
            line = line.strip()
            if not line or line.startswith("Total:"):
                continue
            # Format: "[00000136] Heal Minor Wounds                        (Spell)"
            m = re.match(r'\[([0-9A-Fa-f]+)\]\s+(.+?)\s+\((\w+)\)\s*$', line)
            if m:
                form_id = "0x" + m.group(1).upper()
                name = m.group(2).strip()
                spell_type = m.group(3)
                spells.append(Spell(
                    form_id=form_id,
                    name=name,
                    magicka_cost=0,
                    spell_type=spell_type
                ))
        return spells

    def _parse_inventory(self) -> List[InventoryItem]:
        """Parse Inventory section."""
        items = []
        for line in self._get_section_lines("Inventory"):
            line = line.strip()
            if not line or line.startswith("Total:"):
                continue
            # Format: "[000229B8] Steel Claymore                           x1 (Type: 21)"
            m = re.match(
                r'\[([0-9A-Fa-f]+)\]\s+(.+?)\s+x(-?\d+)\s+\(Type:\s*([0-9A-Fa-f]+)\)',
                line
            )
            if m:
                form_id_raw = m.group(1).upper()
                form_id = "0x" + form_id_raw
                name = m.group(2).strip()
                quantity = int(m.group(3))
                type_code = m.group(4).lower()
                item_type = CLASSIC_ITEM_TYPE_MAP.get(type_code, f"Type {m.group(4)}")
                equipped = form_id_raw in self.equipped_form_ids

                item = InventoryItem(
                    form_id=form_id,
                    name=name,
                    quantity=quantity,
                    item_type=item_type,
                    equipped=equipped
                )

                # Parse optional HP: and Charge: suffixes
                hp_match = re.search(r'HP:([\d.]+)/([\d.]+)', line)
                charge_match = re.search(r'Charge:([\d.]+)/([\d.]+)', line)
                if hp_match:
                    item.condition_current = float(hp_match.group(1))
                    item.condition_max = float(hp_match.group(2))
                if charge_match:
                    item.enchant_current = float(charge_match.group(1))
                    item.enchant_max = float(charge_match.group(2))

                items.append(item)
        return items

    def _parse_factions(self) -> List[Faction]:
        """Parse Factions section."""
        factions = []
        for line in self._get_section_lines("Factions"):
            line = line.strip()
            if not line or line.startswith("Total:"):
                continue
            # Format: "[0700173E] Frostcrag Spire Atronach Faction         Rank: 0"
            m = re.match(r'\[([0-9A-Fa-f]+)\]\s+(.+?)\s+Rank:\s*(-?\d+)', line)
            if m:
                form_id = "0x" + m.group(1).upper()
                name = m.group(2).strip()
                rank = int(m.group(3))
                factions.append(Faction(
                    form_id=form_id,
                    name=name,
                    rank=rank,
                    title=""
                ))
        return factions

    def _parse_active_effects(self) -> List[ActiveMagicEffect]:
        """Parse Active Effects section."""
        effects = []
        for line in self._get_section_lines("Active Effects"):
            line = line.strip()
            if not line or line.startswith("Total:"):
                continue
            # Format: "[0] Resist Disease  mag: 50.0  dur: 0.0  elapsed: 14878.9  from: Argonian Disease Resistance  (type: 4)"
            m = re.match(
                r'\[\d+\]\s+(.+?)\s+mag:\s*([\d.\-]+)\s+dur:\s*([\d.\-]+)'
                r'\s+elapsed:\s*[\d.\-]+\s+from:\s+(.+?)\s+\(type:\s*\d+\)',
                line
            )
            if m:
                effect_name = m.group(1).strip()
                magnitude = float(m.group(2))
                duration = float(m.group(3))
                source_name = m.group(4).strip()
                effects.append(ActiveMagicEffect(
                    effect_code=effect_name,
                    magnitude=magnitude,
                    duration=duration,
                    state="Active",
                    source_name=source_name,
                    source_form_id=""
                ))
        return effects

    def _parse_plugins(self) -> List[str]:
        """Parse Loaded Plugins section."""
        plugins = []
        for line in self._get_section_lines("Loaded Plugins"):
            line = line.strip()
            if not line or line.startswith("Loaded Mod Count:"):
                continue
            # Format: "[00] Oblivion.esm"
            m = re.match(r'\[([0-9A-Fa-f]+)\]\s+(.+)', line)
            if m:
                plugins.append(m.group(2).strip())
        return plugins


def is_classic_save_dump_format(file_path: Path) -> bool:
    """Check if a file is in the xOBSE (classic Oblivion) save dump format."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(5):
                line = f.readline()
                if "xOBSE Save Dump" in line:
                    return True
    except (IOError, OSError):
        pass
    return False


def is_save_dump_format(file_path: Path) -> bool:
    """Check if a file is in any supported save dump format (remastered or classic)."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(5):
                line = f.readline()
                if "OBLIVION REMASTERED - SAVE DATA DUMP" in line:
                    return True
                if "xOBSE Save Dump" in line:
                    return True
    except (IOError, OSError):
        pass
    return False


def parse_save_dump(dump_path: Path) -> CharacterData:
    """Parse a save dump file (auto-detects classic vs remastered) and return CharacterData."""
    if is_classic_save_dump_format(dump_path):
        parser = ClassicSaveDumpParser(dump_path)
    else:
        parser = SaveDumpParser(dump_path)
    return parser.parse()
