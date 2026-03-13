"""
Save Dump Writer - Serializes CharacterData back to a complete save_dump.txt file.

Strategy: Use the original raw dump text as a template and patch in modified values
for editable sections, preserving all other sections (analytics, formatting) faithfully.
Supports both Remastered (=== SECTION ===) and Classic (--- SECTION ---) formats.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Set

from models import (
    CharacterData, PCMISCSTAT_NAMES, ATTRIBUTE_NAMES, SKILL_NAMES,
    get_skill_display_name
)

_DELETED_LINE = "\x00__VARLA_DELETED__\x00"  # sentinel for lines removed by exception filters


@dataclass
class StagedFilter:
    """Passed to SaveDumpWriter.write() to restrict output to staged items only."""
    inventory_ids:     Set[str] = field(default_factory=set)
    spell_ids:         Set[str] = field(default_factory=set)
    attribute_names:   Set[str] = field(default_factory=set)
    skill_names:       Set[str] = field(default_factory=set)
    faction_ids:       Set[str] = field(default_factory=set)
    global_ids:        Set[str] = field(default_factory=set)
    active_quest_ids:  Set[str] = field(default_factory=set)
    plugin_indices:    Set[int] = field(default_factory=set)
    appearance_fields: Set[str] = field(default_factory=set)

    include_char_info:        bool = False
    include_details:          bool = False
    include_game_time:        bool = False
    include_active_effects:   bool = False
    include_world_state:      bool = False
    include_completed_quests: bool = False

# Reverse mapping: PCMISCSTAT index -> dump stat name (title case)
MISC_STAT_INDEX_TO_DUMP_NAME = {
    0: "Days In Prison",
    2: "Skill Increases",
    3: "Training Sessions",
    4: "Largest Bounty",
    5: "Creatures Killed",
    6: "People Killed",
    7: "Places Discovered",
    8: "Locks Picked",
    9: "Lockpicks Broken",
    10: "Souls Trapped",
    11: "Ingredients Eaten",
    12: "Potions Made",
    13: "Oblivion Gates Shut",
    14: "Horses Owned",
    15: "Houses Owned",
    16: "Stores Invested In",
    17: "Books Read",
    18: "Skill Books Read",
    19: "Artifacts Found",
    20: "Hours Slept",
    21: "Hours Waited",
    22: "Days As A Vampire",
    23: "Last Day As A Vampire",
    24: "People Fed On",
    25: "Jokes Told",
    26: "Diseases Contracted",
    27: "Nirnroots Found",
    28: "Items Stolen",
    29: "Items Pickpocketed",
    30: "Trespasses",
    31: "Assaults",
    32: "Murders",
    33: "Horses Stolen",
}


class SaveDumpWriter:
    """Writes a complete save_dump.txt from CharacterData.

    Uses the original raw dump text as a base and patches in
    modified values for editable sections.
    """

    def __init__(self, character_data: CharacterData, spell_exceptions: set = None):
        self.data = character_data
        self.format = character_data.dump_format or "remastered"
        self.raw_text = character_data.raw_dump_text or ""
        self.spell_exceptions = spell_exceptions or set()
        self._sf: Optional[StagedFilter] = None   # set during write()

    def write(self, output_path: Path, staged_filter=None):
        """Write the complete modified dump to output_path.

        If staged_filter (StagedFilter) is provided, only items/sections that
        appear in the filter are written; everything else is removed.
        """
        if not self.raw_text:
            raise ValueError("No raw dump text available. Load a save dump first.")

        self._sf = staged_filter
        lines = self.raw_text.splitlines()

        # Auto-detect actual content format from delimiter style.
        # Modern xOBSE (classic game) uses === === headers with remastered-style
        # field formatting (e.g. "Base:" not "base:"), so regex patterns must
        # match the actual content regardless of the user's game_format setting.
        has_triple_equals = any(
            re.match(r'^=== [A-Z].+ ===$', ln.strip()) for ln in lines[:100]
        )
        if has_triple_equals:
            self.format = "remastered"

        # Generate missing sections that the user staged but aren't in the dump
        if staged_filter:
            lines = self._inject_missing_sections(lines, staged_filter)

        sections = self._index_sections(lines)

        if staged_filter:
            lines = self._remove_sections_by_filter(lines, sections, staged_filter)
            sections = self._index_sections(lines)

        # Patch editable sections in-place
        lines = self._patch_player_character(lines, sections)
        lines = self._patch_appearance(lines, sections)
        lines = self._patch_character_info(lines, sections)
        lines = self._patch_vitals(lines, sections)
        lines = self._patch_inventory(lines, sections)
        lines = self._patch_spells(lines, sections)
        lines = self._patch_attributes(lines, sections)
        lines = self._patch_skills(lines, sections)
        lines = self._patch_misc_statistics(lines, sections)
        lines = self._patch_fame_infamy_bounty(lines, sections)
        lines = self._patch_game_time(lines, sections)
        lines = self._patch_quests(lines, sections)
        lines = self._patch_factions(lines, sections)
        lines = self._patch_global_variables(lines, sections)
        lines = self._patch_active_magic_effects(lines, sections)

        # Remove lines marked for deletion (e.g. excepted spells) - done here to avoid index drift
        lines = [ln for ln in lines if ln != _DELETED_LINE]

        output_text = "\n".join(lines) + "\n"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_text)

    def _index_sections(self, lines: List[str]) -> Dict[str, tuple]:
        """Build section name -> (start_line, end_line) index."""
        # Use self.format (set during write()) to pick the right delimiter.
        # Scanning only lines[:100] broke after _remove_sections_by_filter
        # deleted early sections, pushing surviving headers past line 100.
        if self.format == "remastered":
            pattern = re.compile(r'^=== (.+?) ===$')
        else:
            pattern = re.compile(r'^--- (.+?) ---$')

        section_starts = []
        for i, line in enumerate(lines):
            m = pattern.match(line.strip())
            if m:
                section_starts.append((m.group(1), i))

        sections = {}
        for idx, (name, start) in enumerate(section_starts):
            if idx + 1 < len(section_starts):
                end = section_starts[idx + 1][1]
            else:
                end = len(lines)
            sections[name] = (start, end)

        return sections

    def _inject_missing_sections(self, lines: List[str], sf: "StagedFilter") -> List[str]:
        """Generate sections that the user staged but aren't in the raw dump.

        The xOBSE dump may not include every section (controlled by varla.ini).
        When the user stages data from a section that wasn't dumped, we need to
        synthesize that section so the writer can produce valid output.
        """
        sections = self._index_sections(lines)
        new_sections: List[str] = []
        delim = "===" if self.format == "remastered" else "---"

        # Attributes
        attr_names = {"ATTRIBUTES", "Attributes"}
        if sf.attribute_names and not any(n in sections for n in attr_names):
            sec_name = "ATTRIBUTES" if self.format == "remastered" else "Attributes"
            new_sections.append(f"{delim} {sec_name} {delim}")
            new_sections.append("Format: Current (Base)")
            for attr in ATTRIBUTE_NAMES:
                if attr in self.data.attributes:
                    val = self.data.attributes[attr]
                    cur = self.data.skills_current.get(attr, val)
                    if self.format == "remastered":
                        new_sections.append(f"  {attr}: {cur} (Base: {val})")
                    else:
                        new_sections.append(f"  {attr}: {cur} (base: {val})")
            new_sections.append("")

        # Skills
        skill_names = {"SKILLS", "Skills"}
        if sf.skill_names and not any(n in sections for n in skill_names):
            sec_name = "SKILLS" if self.format == "remastered" else "Skills"
            new_sections.append(f"{delim} {sec_name} {delim}")
            new_sections.append("Format: Current (Base)")
            for skill in SKILL_NAMES:
                if skill in self.data.skills:
                    val = self.data.skills[skill]
                    cur = self.data.skills_current.get(skill, val)
                    display = get_skill_display_name(skill)
                    if self.format == "remastered":
                        new_sections.append(f"  {display}: {cur} (Base: {val})")
                    else:
                        new_sections.append(f"  {display}: {cur} (base: {val})")
            new_sections.append("")

        if not new_sections:
            return lines

        # Insert before the END marker or at the end
        insert_pos = len(lines)
        for i, line in enumerate(lines):
            if "END OF SAVE DATA DUMP" in line:
                # Go back past the === line
                insert_pos = max(0, i - 1)
                break

        return lines[:insert_pos] + new_sections + lines[insert_pos:]

    def _remove_sections_by_filter(self, lines: List[str], sections: Dict, sf: "StagedFilter") -> List[str]:
        """Mark entire sections for deletion based on StagedFilter flags/sets."""

        def rm(name_rem, name_classic=None):
            # Try both name variants — modern xOBSE uses uppercase like remastered
            for key in (name_rem, name_classic):
                if key is None:
                    continue
                rng = sections.get(key)
                if rng:
                    start, end = rng
                    for j in range(start, end):
                        lines[j] = _DELETED_LINE
                    return

        if not sf.include_char_info:
            rm("PLAYER CHARACTER", "Player Character")
            rm("CHARACTER INFO", "Character Info")
        if not sf.include_char_info and not sf.appearance_fields:
            rm("APPEARANCE")

        if not sf.include_details:
            rm("DERIVED STATS", "Derived Stats")
            rm("MISC STATISTICS", "Misc Statistics")
            rm("FAME / INFAMY / BOUNTY", "Fame / Infamy / Bounty")

        if not sf.include_game_time:
            rm("GAME TIME", "Game Time")

        if not sf.include_active_effects:
            rm("ACTIVE MAGIC EFFECTS", "Active Effects")

        if not sf.include_completed_quests:
            rm("COMPLETED QUESTS", "Completed Quests")

        if not sf.include_world_state:
            for s in ["WEATHER", "CELL INFO", "LOCATION", "MAP MARKERS",
                      "Weather", "Cell Info", "Location", "Map Markers"]:
                rng = sections.get(s)
                if rng:
                    start, end = rng
                    for j in range(start, end):
                        lines[j] = _DELETED_LINE

        if not sf.inventory_ids:
            rm("INVENTORY", "Inventory")

        if not sf.spell_ids:
            rm("SPELLS", "Known Spells")

        if not sf.attribute_names:
            rm("ATTRIBUTES", "Attributes")

        if not sf.skill_names:
            rm("SKILLS", "Skills")

        if not sf.faction_ids:
            rm("FACTIONS", "Factions")

        if not sf.global_ids:
            rm("GLOBAL VARIABLES", "Global Variables")

        if not sf.active_quest_ids:
            rm("ACTIVE QUESTS (Started, Not Completed)", "Active Quests")

        # Whitelist pass: remove every section not explicitly kept by the filter.
        # This catches PLUGINS, analytics sections, and any other unrecognised sections.
        kept: set = set()
        if sf.include_char_info:
            kept.update(["PLAYER CHARACTER", "CHARACTER INFO",
                         "Player Character", "Character Info"])
        if sf.include_char_info or sf.appearance_fields:
            kept.add("APPEARANCE")
        if sf.include_details:
            kept.update(["DERIVED STATS", "MISC STATISTICS", "FAME / INFAMY / BOUNTY",
                         "Derived Stats", "Misc Statistics", "Fame / Infamy / Bounty"])
        if sf.include_game_time:
            kept.update(["GAME TIME", "Game Time"])
        if sf.include_active_effects:
            kept.update(["ACTIVE MAGIC EFFECTS", "Active Effects"])
        if sf.include_completed_quests:
            kept.update(["COMPLETED QUESTS", "Completed Quests"])
        if sf.include_world_state:
            kept.update(["WEATHER", "CELL INFO", "LOCATION", "MAP MARKERS",
                         "Weather", "Cell Info", "Location", "Map Markers"])
        if sf.inventory_ids:
            kept.update(["INVENTORY", "Inventory"])
        if sf.spell_ids:
            kept.update(["SPELLS", "Known Spells"])
        if sf.attribute_names:
            kept.update(["ATTRIBUTES", "Attributes"])
        if sf.skill_names:
            kept.update(["SKILLS", "Skills"])
        if sf.faction_ids:
            kept.update(["FACTIONS", "Factions"])
        if sf.global_ids:
            kept.update(["GLOBAL VARIABLES", "Global Variables"])
        if sf.active_quest_ids:
            kept.update(["ACTIVE QUESTS (Started, Not Completed)", "Active Quests",
                         "ACTIVE QUEST"])

        for sec_name, (start, end) in sections.items():
            if sec_name not in kept:
                for j in range(start, end):
                    lines[j] = _DELETED_LINE

        return lines

    def _get_section_range(self, sections: Dict, name: str):
        """Get (start, end) for a section, or None if not found.
        Tries the exact name first, then uppercase (for modern xOBSE dumps)."""
        rng = sections.get(name)
        if rng:
            return rng
        return sections.get(name.upper())

    # ── Inventory patching ───────────────────────────────────────────────

    def _patch_inventory(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch inventory section with modified quantities and condition/charge."""
        section_name = "INVENTORY" if self.format == "remastered" else "Inventory"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        # Build lookup by form_id
        item_lookup = {item.form_id: item for item in self.data.items}

        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                continue

            if self.format == "remastered":
                m = re.match(
                    r'(\s*\[\d+\]\s+.+?\s+x)-?\d+(\s+\()(0x[0-9A-Fa-f]+)(\)\s*\[\w[\w\s]*\](?:\s*\[EQUIPPED\])?)',
                    line
                )
                if m:
                    form_id = m.group(3)
                    if self._sf and self._sf.inventory_ids and form_id not in self._sf.inventory_ids:
                        lines[i] = _DELETED_LINE
                        continue
                    item = item_lookup.get(form_id)
                    if item:
                        # Rebuild the line with updated quantity
                        # Strip [EQUIPPED] from group(4) so we can add/remove it
                        type_tag = re.sub(r'\s*\[EQUIPPED\]', '', m.group(4))
                        new_line = f"{m.group(1)}{item.quantity}{m.group(2)}{m.group(3)}{type_tag}"
                        # Add [EQUIPPED] if item is equipped
                        if item.equipped:
                            new_line += " [EQUIPPED]"
                        # Strip old HP:/Charge: suffixes
                        new_line = re.sub(r'\s*HP:[\d.]+/[\d.]+', '', new_line)
                        new_line = re.sub(r'\s*Charge:[\d.]+/[\d.]+', '', new_line)
                        # Append new HP:/Charge: if applicable
                        if item.condition_current >= 0 and item.condition_max >= 0:
                            new_line += f" HP:{item.condition_current:g}/{item.condition_max:g}"
                        if item.enchant_current >= 0 and item.enchant_max >= 0:
                            new_line += f" Charge:{item.enchant_current:g}/{item.enchant_max:g}"
                        lines[i] = new_line
            else:
                # Classic format: "[000229B8] Steel Claymore  x1 (Type: 21)"
                m = re.match(
                    r'(\s*\[[0-9A-Fa-f]+\]\s+.+?\s+x)-?\d+(\s+\(Type:\s*[0-9A-Fa-f]+\))',
                    line
                )
                if m:
                    fid_m = re.search(r'\[([0-9A-Fa-f]+)\]', line)
                    if fid_m:
                        form_id = "0x" + fid_m.group(1).upper()
                        if self._sf and self._sf.inventory_ids and form_id not in self._sf.inventory_ids:
                            lines[i] = _DELETED_LINE
                            continue
                        item = item_lookup.get(form_id)
                        if item:
                            new_line = f"{m.group(1)}{item.quantity}{m.group(2)}"
                            # Strip and re-add HP:/Charge:
                            new_line = re.sub(r'\s*HP:[\d.]+/[\d.]+', '', new_line)
                            new_line = re.sub(r'\s*Charge:[\d.]+/[\d.]+', '', new_line)
                            if item.condition_current >= 0 and item.condition_max >= 0:
                                new_line += f" HP:{item.condition_current:g}/{item.condition_max:g}"
                            if item.enchant_current >= 0 and item.enchant_max >= 0:
                                new_line += f" Charge:{item.enchant_current:g}/{item.enchant_max:g}"
                            lines[i] = new_line

        return lines

    # ── Spells patching ──────────────────────────────────────────────────

    def _patch_spells(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch spell section with modified magicka cost and effect properties.
        Also removes entire spell blocks for form_ids in self.spell_exceptions."""
        section_name = "SPELLS" if self.format == "remastered" else "Known Spells"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        spell_lookup = {spell.form_id: spell for spell in self.data.spells}

        current_spell = None
        current_effect_idx = 0
        current_is_excepted = False

        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()
            if not stripped:
                continue

            if self.format == "remastered":
                # Spell header: "[0] Name (0xFORM) Type: Spell, Cost: 24"
                header_m = re.match(r'(\s*\[\d+\]\s+.+?\s+\()(0x[0-9A-Fa-f]+)(\).*)', stripped)
                if header_m:
                    form_id = header_m.group(2)
                    sf_excluded = bool(self._sf and self._sf.spell_ids and form_id not in self._sf.spell_ids)
                    current_is_excepted = (form_id in self.spell_exceptions) or sf_excluded
                    current_spell = spell_lookup.get(form_id) if not current_is_excepted else None
                    current_effect_idx = 0

                    if current_is_excepted:
                        lines[i] = _DELETED_LINE
                    elif current_spell:
                        cost_m = re.search(r'(Cost:\s*)[\d.]+', line)
                        if cost_m:
                            lines[i] = line[:cost_m.start()] + f"Cost: {current_spell.magicka_cost}" + line[cost_m.end():]
                    continue

                # Subsection headers (--- ... ---) reset the current spell context
                if re.match(r'^---\s+.+\s+---$', stripped):
                    current_spell = None
                    current_is_excepted = False
                    current_effect_idx = 0
                    continue

                # Effect/sub-lines belonging to an excepted spell (only indented lines)
                if current_is_excepted and line.startswith(' '):
                    lines[i] = _DELETED_LINE
                    continue

                # Effect line with detailed format
                if current_spell and current_effect_idx < len(current_spell.effects):
                    effect_m = re.match(
                        r'(\s*\[\d+\]\s+.+?\s+-\s+)Mag:\s*\d+,\s*Dur:\s*\d+,\s*Area:\s*\d+,\s*Range:\s*(\w+)',
                        line
                    )
                    if effect_m:
                        eff = current_spell.effects[current_effect_idx]
                        rest_m = re.search(r'(,\s*Cost:\s*[\d.]+)?$', line)
                        rest = rest_m.group(0) if rest_m else ""
                        lines[i] = f"{effect_m.group(1)}Mag: {eff.magnitude}, Dur: {eff.duration}, Area: {eff.area}, Range: {eff.range}{rest}"
                        current_effect_idx += 1
                        continue

                    # Simpler effect format
                    simple_m = re.match(
                        r'(\s+.+?\s+\[\w+\]\s+\()(\w+)(\)\s+)Mag:\s*(\d+)\s+Dur:\s*(\d+)',
                        line
                    )
                    if simple_m:
                        eff = current_spell.effects[current_effect_idx]
                        lines[i] = f"{simple_m.group(1)}{eff.range}{simple_m.group(3)}Mag: {eff.magnitude} Dur: {eff.duration}"
                        trail_m = re.search(r'(\s+\[.*\])$', line)
                        if trail_m:
                            lines[i] += trail_m.group(1)
                        current_effect_idx += 1

        return lines

    # ── Attributes patching ──────────────────────────────────────────────

    def _patch_attributes(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch attribute base values."""
        section_name = "ATTRIBUTES" if self.format == "remastered" else "Attributes"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("Format:"):
                continue

            if self.format == "remastered":
                # Format: "  Strength: 75 (Base: 75)"
                m = re.match(r'(\s*\w+:\s*)\d+(\s*\(Base:\s*)\d+(\).*)', line)
                if m:
                    attr_name = line.strip().split(":")[0].strip()
                    if self._sf and self._sf.attribute_names and attr_name not in self._sf.attribute_names:
                        lines[i] = _DELETED_LINE
                        continue
                    if attr_name in self.data.attributes:
                        val = self.data.attributes[attr_name]
                        lines[i] = f"{m.group(1)}{val}{m.group(2)}{val}{m.group(3)}"
            else:
                # Classic: "Strength       : 45 (base: 45)"
                m = re.match(r'(\s*[\w\s]+?\s*:\s*)\d+(\s*\(base:\s*)\d+(\).*)', line)
                if m:
                    attr_name = line.strip().split(":")[0].strip()
                    if self._sf and self._sf.attribute_names and attr_name not in self._sf.attribute_names:
                        lines[i] = _DELETED_LINE
                        continue
                    if attr_name in self.data.attributes:
                        val = self.data.attributes[attr_name]
                        lines[i] = f"{m.group(1)}{val}{m.group(2)}{val}{m.group(3)}"

        return lines

    # ── Skills patching ──────────────────────────────────────────────────

    def _patch_skills(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch skill base values."""
        section_name = "SKILLS" if self.format == "remastered" else "Skills"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        # Map multi-word display names (as they appear in the dump) to storage names
        display_to_storage = {
            "Hand To Hand": "HandToHand",
            "Heavy Armor": "HeavyArmor",
            "Light Armor": "LightArmor",
        }

        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("Format:") or stripped.endswith("Skills:"):
                continue
            if stripped.startswith("Major Skill") or stripped.startswith("Can Level"):
                continue

            if self.format == "remastered":
                # "  Armorer: 34 (Base: 34)" or "  Hand To Hand: 13 (Base: 13)"
                m = re.match(r'(\s*[\w ]+?:\s*)\d+(\s*\(Base:\s*)\d+(\).*)', line)
                if m:
                    skill_display = line.strip().split(":")[0].strip()
                    skill_name = display_to_storage.get(skill_display, skill_display)
                    if self._sf and self._sf.skill_names and skill_name not in self._sf.skill_names:
                        lines[i] = _DELETED_LINE
                        continue
                    if skill_name in self.data.skills:
                        base_val = self.data.skills[skill_name]
                        current_val = self.data.skills_current.get(skill_name, base_val)
                        lines[i] = f"{m.group(1)}{current_val}{m.group(2)}{base_val}{m.group(3)}"
            else:
                # "Armorer        : 30 (base: 30)  exp: 4.5 / 19.1"
                m = re.match(r'(\s*[\w\s]+?\s*:\s*)\d+(\s*\(base:\s*)\d+(\).*)', line)
                if m:
                    skill_display = line.strip().split(":")[0].strip()
                    skill_name = display_to_storage.get(skill_display, skill_display)
                    if self._sf and self._sf.skill_names and skill_name not in self._sf.skill_names:
                        lines[i] = _DELETED_LINE
                        continue
                    if skill_name in self.data.skills:
                        base_val = self.data.skills[skill_name]
                        current_val = self.data.skills_current.get(skill_name, base_val)
                        lines[i] = f"{m.group(1)}{current_val}{m.group(2)}{base_val}{m.group(3)}"

        return lines

    # ── Misc Statistics patching ─────────────────────────────────────────

    def _patch_misc_statistics(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch misc statistics values."""
        section_name = "MISC STATISTICS" if self.format == "remastered" else "Misc Statistics"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        # Build reverse lookup from stat name (lowercased) to index
        from save_dump_parser import MISC_STAT_NAME_TO_INDEX

        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()
            if not stripped or ":" not in stripped:
                continue

            parts = stripped.rsplit(":", 1)
            if len(parts) == 2:
                stat_name = parts[0].strip().lower()
                idx = MISC_STAT_NAME_TO_INDEX.get(stat_name)
                if idx is not None and idx in self.data.pc_misc_stats:
                    new_val = self.data.pc_misc_stats[idx]
                    # Preserve indentation and stat name, replace value
                    colon_pos = line.rfind(":")
                    lines[i] = line[:colon_pos + 1] + f" {new_val}"

        return lines

    # ── Fame / Infamy / Bounty patching ──────────────────────────────────

    def _patch_fame_infamy_bounty(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch fame, infamy, bounty values."""
        section_name = "FAME / INFAMY / BOUNTY" if self.format == "remastered" else "Fame / Infamy / Bounty"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith("Fame:"):
                colon_pos = line.find(":")
                lines[i] = line[:colon_pos + 1] + f" {self.data.fame}"
            elif stripped.startswith("Infamy:"):
                colon_pos = line.find(":")
                lines[i] = line[:colon_pos + 1] + f" {self.data.infamy}"
            elif stripped.startswith("Bounty:"):
                colon_pos = line.find(":")
                lines[i] = line[:colon_pos + 1] + f" {self.data.bounty}"

        return lines

    # ── Game Time patching ───────────────────────────────────────────────

    def _patch_game_time(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch game time values."""
        section_name = "GAME TIME" if self.format == "remastered" else "Game Time"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        gt = self.data.game_time

        for i in range(start + 1, end):
            line = lines[i]
            stripped = line.strip()

            if self.format == "remastered":
                if stripped.startswith("Days Passed:"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" {gt.days_passed}"
                elif stripped.startswith("Game Date:"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" Year {gt.game_year}, Month {gt.game_month}, Day {gt.game_day}"
            else:
                if stripped.startswith("Year:"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" {gt.game_year}"
                elif stripped.startswith("Month:"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" {gt.game_month}"
                elif stripped.startswith("Day:") and not stripped.startswith("Days"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" {gt.game_day}"
                elif stripped.startswith("Hour:"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" {gt.game_hour}"
                elif stripped.startswith("Days Passed:"):
                    colon_pos = line.find(":")
                    lines[i] = line[:colon_pos + 1] + f" {gt.days_passed}"

        return lines

    # ── Quests patching ──────────────────────────────────────────────────

    def _patch_quests(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch quest stages in active quests section."""
        if self.format == "remastered":
            # Patch active quest
            rng = self._get_section_range(sections, "ACTIVE QUEST")
            if rng and self.data.active_quest:
                start, end = rng
                for i in range(start + 1, end):
                    stripped = lines[i].strip()
                    if stripped.startswith("Current Stage:"):
                        colon_pos = lines[i].find(":")
                        lines[i] = lines[i][:colon_pos + 1] + f" {self.data.active_quest.stage}"

            # Patch current quests
            rng = self._get_section_range(sections, "ACTIVE QUESTS (Started, Not Completed)")
            if rng:
                start, end = rng
                quest_lookup = {q.form_id: q for q in self.data.current_quests}
                current_form_id = None
                current_quest_excluded = False

                for i in range(start + 1, end):
                    stripped = lines[i].strip()
                    # Quest header: "[0] Name (0xFORM)"
                    fid_m = re.search(r'\((0x[0-9A-Fa-f]+)\)', stripped)
                    if fid_m and re.match(r'\[\d+\]', stripped):
                        current_form_id = fid_m.group(1)
                        current_quest_excluded = bool(
                            self._sf and self._sf.active_quest_ids
                            and current_form_id not in self._sf.active_quest_ids
                        )
                        if current_quest_excluded:
                            lines[i] = _DELETED_LINE
                            continue
                    elif current_quest_excluded:
                        lines[i] = _DELETED_LINE
                        continue

                    if current_form_id and not current_quest_excluded and stripped.startswith("Current Stage:"):
                        quest = quest_lookup.get(current_form_id)
                        if quest:
                            colon_pos = lines[i].find(":")
                            lines[i] = lines[i][:colon_pos + 1] + f" {quest.stage}"

        return lines

    # ── Player Character patching ─────────────────────────────────────────

    def _patch_player_character(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch player name in PLAYER CHARACTER section."""
        section_name = "PLAYER CHARACTER" if self.format == "remastered" else "Player Character"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if stripped.startswith("Player Name:"):
                colon_pos = lines[i].find(":")
                lines[i] = lines[i][:colon_pos + 1] + f" {self.data.character.name}"

        return lines

    # ── Appearance patching ──────────────────────────────────────────────

    # Mapping from appearance field storage key to dump line prefix
    _APPEARANCE_PREFIX_MAP = {
        "hair":               "Hair:",
        "eyes":               "Eyes:",
        "hair_color":         "HairColor:",
        "hair_length":        "HairLength:",
        "facegen_geometry":   "FaceGenGeometry:",
        "facegen_asymmetry":  "FaceGenAsymmetry:",
        "facegen_texture":    "FaceGenTexture:",
        "facegen_geometry2":  "FaceGenGeometry2:",
        "facegen_asymmetry2": "FaceGenAsymmetry2:",
        "facegen_texture2":   "FaceGenTexture2:",
    }

    def _patch_appearance(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch appearance data (hair, eyes, FaceGen) in APPEARANCE section.
        If a staged filter is active, only keep lines for staged fields."""
        rng = self._get_section_range(sections, "APPEARANCE")
        if not rng:
            return lines

        a = self.data.appearance
        sf = self._sf

        # Build set of prefixes to keep (if filtering) and values to patch
        if sf and sf.appearance_fields:
            kept_prefixes = set()
            for field_key in sf.appearance_fields:
                prefix = self._APPEARANCE_PREFIX_MAP.get(field_key)
                if prefix:
                    kept_prefixes.add(prefix)
        else:
            kept_prefixes = None  # keep all

        start, end = rng
        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if not stripped:
                continue
            matched = False
            for field_key, prefix in self._APPEARANCE_PREFIX_MAP.items():
                if stripped.startswith(prefix):
                    matched = True
                    if kept_prefixes is not None and prefix not in kept_prefixes:
                        lines[i] = _DELETED_LINE
                    else:
                        value = getattr(a, field_key, "")
                        if value:
                            colon_pos = lines[i].find(":")
                            lines[i] = lines[i][:colon_pos + 1] + f" {value}"
                    break
            # Delete unrecognised appearance lines when filtering
            if not matched and kept_prefixes is not None:
                lines[i] = _DELETED_LINE

        return lines

    # ── Character Info patching ───────────────────────────────────────────

    def _patch_character_info(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch level, race, class, birthsign in CHARACTER INFO section."""
        section_name = "CHARACTER INFO" if self.format == "remastered" else "Character Info"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if stripped.startswith("Level:"):
                colon_pos = lines[i].find(":")
                lines[i] = lines[i][:colon_pos + 1] + f" {self.data.character.level}"
            elif stripped.startswith("Race:"):
                # Preserve form ID if present: "Race: DarkElf (0x000191C1)"
                m = re.search(r'(\s*\(0x[0-9A-Fa-f]+\))', lines[i])
                suffix = m.group(1) if m else ""
                colon_pos = lines[i].find(":")
                lines[i] = lines[i][:colon_pos + 1] + f" {self.data.character.race}{suffix}"
            elif stripped.startswith("Class:"):
                m = re.search(r'(\s*\(0x[0-9A-Fa-f]+\))', lines[i])
                suffix = m.group(1) if m else ""
                colon_pos = lines[i].find(":")
                lines[i] = lines[i][:colon_pos + 1] + f" {self.data.character.class_name}{suffix}"
            elif stripped.startswith("Birthsign:"):
                m = re.search(r'(\s*\(0x[0-9A-Fa-f]+\))', lines[i])
                suffix = m.group(1) if m else ""
                colon_pos = lines[i].find(":")
                lines[i] = lines[i][:colon_pos + 1] + f" {self.data.character.birthsign}{suffix}"

        return lines

    # ── Vitals patching ───────────────────────────────────────────────────

    def _patch_vitals(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch vitals (health, magicka, fatigue) in DERIVED STATS section."""
        section_name = "DERIVED STATS" if self.format == "remastered" else "Derived Stats"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        vitals = self.data.vitals

        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if stripped.startswith("Health:"):
                m = re.match(r'(\s*Health:\s*)[\d.]+(\s*/\s*)[\d.]+(\s*\(Base:\s*)[\d.]+(\).*)', lines[i])
                if m:
                    lines[i] = f"{m.group(1)}{vitals.health_current:g}{m.group(2)}{vitals.health_current:g}{m.group(3)}{vitals.health_base:g}{m.group(4)}"
            elif stripped.startswith("Magicka:"):
                m = re.match(r'(\s*Magicka:\s*)[\d.]+(\s*/\s*)[\d.]+(\s*\(Base:\s*)[\d.]+(\).*)', lines[i])
                if m:
                    lines[i] = f"{m.group(1)}{vitals.magicka_current:g}{m.group(2)}{vitals.magicka_current:g}{m.group(3)}{vitals.magicka_base:g}{m.group(4)}"
            elif stripped.startswith("Fatigue:"):
                m = re.match(r'(\s*Fatigue:\s*)[\d.]+(\s*/\s*)[\d.]+(\s*\(Base:\s*)[\d.]+(\).*)', lines[i])
                if m:
                    lines[i] = f"{m.group(1)}{vitals.fatigue_current:g}{m.group(2)}{vitals.fatigue_current:g}{m.group(3)}{vitals.fatigue_base:g}{m.group(4)}"
            elif stripped.startswith("Encumbrance:"):
                m = re.match(r'(\s*Encumbrance:\s*)[\d.]+', lines[i])
                if m:
                    rest = lines[i][m.end():]
                    lines[i] = f"{m.group(1)}{vitals.encumbrance:g}{rest}"

        return lines

    # ── Factions patching ─────────────────────────────────────────────────

    def _patch_factions(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch faction ranks."""
        section_name = "FACTIONS" if self.format == "remastered" else "Factions"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        faction_lookup = {f.form_id: f for f in self.data.factions}

        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if not stripped:
                continue

            if self.format == "remastered":
                # "[0] Name (0xFORM) - Rank: 0"
                m = re.search(r'\((0x[0-9A-Fa-f]+)\)', stripped)
                if m:
                    form_id = m.group(1)
                    if self._sf and self._sf.faction_ids and form_id not in self._sf.faction_ids:
                        lines[i] = _DELETED_LINE
                        continue
                    faction = faction_lookup.get(form_id)
                    if faction:
                        rank_m = re.search(r'(Rank:\s*)-?\d+', lines[i])
                        if rank_m:
                            lines[i] = lines[i][:rank_m.start()] + f"Rank: {faction.rank}" + lines[i][rank_m.end():]
            else:
                # "[FORM] Name  Rank: 0"
                fid_m = re.match(r'\s*\[([0-9A-Fa-f]+)\]', stripped)
                if fid_m:
                    form_id = "0x" + fid_m.group(1).upper()
                    if self._sf and self._sf.faction_ids and form_id not in self._sf.faction_ids:
                        lines[i] = _DELETED_LINE
                        continue
                    faction = faction_lookup.get(form_id)
                    if faction:
                        rank_m = re.search(r'(Rank:\s*)-?\d+', lines[i])
                        if rank_m:
                            lines[i] = lines[i][:rank_m.start()] + f"Rank: {faction.rank}" + lines[i][rank_m.end():]

        return lines

    # ── Global Variables patching ─────────────────────────────────────────

    def _patch_global_variables(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch global variable values."""
        section_name = "GLOBAL VARIABLES" if self.format == "remastered" else "Global Variables"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        gv_lookup = {gv.form_id: gv for gv in self.data.global_variables}

        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if not stripped or stripped.startswith("Total"):
                continue

            if self.format == "remastered":
                # "  PCInfamy (0x0A000CE7) = 0.00 [short]"
                m = re.search(r'\((0x[0-9A-Fa-f]+)\)\s*=\s*([\d.\-]+)', lines[i])
                if m:
                    form_id = m.group(1)
                    if self._sf and self._sf.global_ids and form_id not in self._sf.global_ids:
                        lines[i] = _DELETED_LINE
                        continue
                    gv = gv_lookup.get(form_id)
                    if gv:
                        eq_pos = lines[i].find("=", m.start())
                        # Find the value portion and type suffix
                        val_m = re.search(r'=\s*[\d.\-]+', lines[i][m.start():])
                        if val_m:
                            abs_start = m.start() + val_m.start()
                            abs_end = m.start() + val_m.end()
                            lines[i] = lines[i][:abs_start] + f"= {gv.value}" + lines[i][abs_end:]
            else:
                # "[FORM] Name (t) = value"
                fid_m = re.match(r'\s*\[([0-9A-Fa-f]+)\]', stripped)
                if fid_m:
                    form_id = "0x" + fid_m.group(1).upper()
                    if self._sf and self._sf.global_ids and form_id not in self._sf.global_ids:
                        lines[i] = _DELETED_LINE
                        continue
                    gv = gv_lookup.get(form_id)
                    if gv:
                        val_m = re.search(r'(=\s*)[\d.\-]+', lines[i])
                        if val_m:
                            lines[i] = lines[i][:val_m.start()] + f"= {gv.value}" + lines[i][val_m.end():]

        return lines

    # ── Active Magic Effects patching ─────────────────────────────────────

    def _patch_active_magic_effects(self, lines: List[str], sections: Dict) -> List[str]:
        """Patch active magic effect magnitudes and durations."""
        section_name = "ACTIVE MAGIC EFFECTS" if self.format == "remastered" else "Active Effects"
        rng = self._get_section_range(sections, section_name)
        if not rng:
            return lines

        start, end = rng
        effect_idx = 0

        for i in range(start + 1, end):
            stripped = lines[i].strip()
            if not stripped or stripped.startswith("Total"):
                continue

            if effect_idx >= len(self.data.active_magic_effects):
                break

            if self.format == "remastered":
                # "[0] STMA  Mag=1.0  Dur=0.0  State=Removed"
                m = re.match(r'(\s*\[\d+\]\s+\w+\s+)Mag=([\d.\-]+)\s+Dur=([\d.\-]+)(\s+State=\w+)', lines[i])
                if m:
                    eff = self.data.active_magic_effects[effect_idx]
                    lines[i] = f"{m.group(1)}Mag={eff.magnitude}  Dur={eff.duration}{m.group(4)}"
                    effect_idx += 1
            else:
                # "[0] Effect  mag: 1.0  dur: 0.0  elapsed: 0.0  from: Source (type: 0)"
                m = re.match(
                    r'(\s*\[\d+\]\s+.+?\s+)mag:\s*[\d.\-]+(\s+dur:\s*)[\d.\-]+(\s+elapsed:.*)',
                    lines[i]
                )
                if m:
                    eff = self.data.active_magic_effects[effect_idx]
                    lines[i] = f"{m.group(1)}mag: {eff.magnitude}{m.group(2)}{eff.duration}{m.group(3)}"
                    effect_idx += 1

        return lines
