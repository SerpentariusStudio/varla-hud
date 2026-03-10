"""
Varla INI Editor — A user-friendly GUI for editing varla.ini settings.
Standalone PySide6 application with grouped toggles, presets, and search.
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QPushButton, QCheckBox, QGroupBox,
    QFrame, QLineEdit, QMessageBox, QFileDialog, QComboBox,
    QGridLayout, QSizePolicy, QToolTip, QStatusBar,
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QColor, QPalette

# ---------------------------------------------------------------------------
# Theme (reuses color palette from theme.py)
# ---------------------------------------------------------------------------
from theme import COLORS, WARM_MEDIEVAL_QSS

# Extra QSS overrides specific to this editor
EDITOR_QSS = WARM_MEDIEVAL_QSS + f"""
/* ─── Toggle Switch (custom styled checkbox) ─── */
QCheckBox#iniToggle {{
    spacing: 10px;
    background-color: transparent;
    padding: 4px 0;
}}

QCheckBox#iniToggle::indicator {{
    width: 36px;
    height: 20px;
    border-radius: 10px;
    border: 2px solid {COLORS["border_primary"]};
    background-color: {COLORS["bg_input"]};
}}

QCheckBox#iniToggle::indicator:checked {{
    background-color: {COLORS["accent_gold_dim"]};
    border-color: {COLORS["accent_gold"]};
}}

QCheckBox#iniToggle::indicator:hover {{
    border-color: {COLORS["accent_gold_bright"]};
}}

/* ─── Preset Buttons ─── */
QPushButton#presetBtn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: normal;
    font-size: 9pt;
}}

QPushButton#presetBtn:hover {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["accent_gold_dim"]};
}}

QPushButton#presetBtn[active="true"] {{
    background-color: {COLORS["accent_gold_dim"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["accent_gold"]};
    font-weight: bold;
}}

/* ─── Group toggle-all buttons ─── */
QPushButton#groupToggleBtn {{
    background-color: transparent;
    color: {COLORS["text_muted"]};
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 3px;
    padding: 2px 8px;
    font-size: 8pt;
    min-height: 18px;
}}

QPushButton#groupToggleBtn:hover {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_primary"]};
}}

/* ─── Search Bar ─── */
QLineEdit#searchBar {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 12px;
    padding: 6px 14px;
    font-size: 10pt;
}}

QLineEdit#searchBar:focus {{
    border-color: {COLORS["accent_gold"]};
    border-width: 2px;
}}

/* ─── Header label ─── */
QLabel#editorTitle {{
    color: {COLORS["accent_gold"]};
    font-size: 16pt;
    font-weight: bold;
    background-color: transparent;
}}

QLabel#editorSubtitle {{
    color: {COLORS["text_muted"]};
    font-size: 9pt;
    background-color: transparent;
}}

/* ─── Category Header ─── */
QLabel#categoryHeader {{
    color: {COLORS["accent_gold"]};
    font-size: 11pt;
    font-weight: bold;
    background-color: transparent;
    padding: 0;
}}

/* ─── Setting description ─── */
QLabel#settingDesc {{
    color: {COLORS["text_muted"]};
    font-size: 8pt;
    background-color: transparent;
    padding: 0;
    margin: 0;
}}

/* ─── Setting name ─── */
QLabel#settingName {{
    color: {COLORS["text_primary"]};
    font-size: 10pt;
    background-color: transparent;
    padding: 0;
}}

/* ─── Dirty indicator ─── */
QLabel#dirtyDot {{
    color: {COLORS["accent_amber"]};
    background-color: transparent;
    font-size: 14pt;
}}

/* ─── Counter label ─── */
QLabel#counterLabel {{
    color: {COLORS["text_secondary"]};
    font-size: 9pt;
    background-color: transparent;
}}

/* ─── [SaveDump] Export master toggle ─── */
QPushButton#exportToggleBtn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_disabled"]};
    border: 2px solid {COLORS["border_dark"]};
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 9pt;
    font-weight: bold;
}}

QPushButton#exportToggleBtn:checked {{
    background-color: {COLORS["accent_gold_dim"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["accent_gold"]};
}}

QPushButton#exportToggleBtn:hover {{
    border-color: {COLORS["accent_gold_bright"]};
    color: {COLORS["text_secondary"]};
}}
"""

# ---------------------------------------------------------------------------
# Setting definitions — friendly names, descriptions, and grouping
# ---------------------------------------------------------------------------

# Each entry: (ini_key, friendly_name, description)
SETTING_GROUPS = {
    "Player Character Data": {
        "description": "Core character info included in every save dump. "
                       "Most of these should stay ON for Varla-HUD to work.",
        "icon": "C",  # placeholder for a future icon
        "settings": [
            ("bDumpSaveFormat", "Save Format", "Include save file format version"),
            ("bDumpPlayerCharacter", "Player Character", "Name, race, class, level, and base info"),
            ("bDumpPosition", "Position", "World coordinates, cell, and facing direction"),
            ("bDumpCharacterInfo", "Character Info", "Health, magicka, fatigue, bounty, etc."),
            ("bDumpFameInfamy", "Fame & Infamy", "Current fame and infamy values"),
            ("bDumpGameTime", "Game Time", "In-game date, time, and play duration"),
            ("bDumpGlobalVars", "Global Variables", "Story-tracking global script variables"),
            ("bDumpMiscStats", "Misc Stats", "Locks picked, potions made, creatures killed, etc."),
            ("bDumpActiveQuest", "Active Quest", "Currently tracked quest objective"),
            ("bDumpQuestList", "Quest List", "Full list of all quests and their stages"),
            ("bDumpQuestScriptVars", "Quest Script Vars", "Script variables attached to quests"),
            ("bDumpFactions", "Factions", "Guild memberships and faction ranks"),
            ("bDumpAttributes", "Attributes", "Strength, Intelligence, etc. (base + modifiers)"),
            ("bDumpDerivedStats", "Derived Stats", "Calculated stats like spell effectiveness"),
            ("bDumpSkills", "Skills", "All skill levels (base + modifiers)"),
            ("bDumpMagicResist", "Magic Resistance", "Resist fire, frost, shock, magic, etc."),
            ("bDumpSpells", "Spells", "Known spells with effects, cost, range"),
            ("bDumpInventory", "Inventory", "All carried items, equipment, gold"),
            ("bDumpCellItems", "Cell Items", "Items in the player's current cell"),
            ("bDumpWeather", "Weather", "Current weather state"),
            ("bDumpPluginList", "Plugin List", "Active mods and load order"),
            ("bDumpSkillProgress", "Skill Progress", "XP progress toward next skill level"),
            ("bDumpQuickKeys", "Quick Keys", "Hotkey assignments (1-8)"),
            ("bDumpStatusEffects", "Status Effects", "Active buffs, debuffs, diseases, etc."),
            ("bDumpAVModifiers", "AV Modifiers", "Actor Value modifier breakdown"),
            ("bDumpActiveMagicEffects", "Active Magic Effects", "All active spell effects with durations"),
            ("bDumpInventoryDetail", "Inventory Detail", "Extended item info (condition, enchant charge)"),
            ("bDumpMapMarkers", "Map Markers", "All discovered/undiscovered map markers"),
            ("bDumpDialogTopics", "Dialog Topics", "Known dialog topics the player has encountered"),
        ],
    },
    "Save File Internals": {
        "description": "Low-level save file data. Only useful for debugging save corruption "
                       "or developing tools. Safe to leave OFF.",
        "icon": "S",
        "settings": [
            ("bDumpDetailedGlobalData", "Detailed Global Data", "Raw global data tables from the save"),
            ("bDumpChangedForms", "Changed Forms", "All modified game objects since last save"),
            ("bDumpCreatedForms", "Created Forms", "Dynamically created objects (enchanted items, etc.)"),
            ("bDumpRawPlayerData", "Raw Player Data", "Unprocessed binary player record"),
            ("bDumpGlobalDataSections", "Global Data Sections", "Save file global data section headers"),
            ("bDumpIDArrays", "ID Arrays", "FormID reference arrays from save"),
            ("bDumpChangeFlagAnalysis", "Change Flag Analysis", "Bit-level analysis of change flags"),
        ],
    },
    "World / Cell Data": {
        "description": "Data about the game world, cells, and NPCs. "
                       "Produces large output. Leave OFF unless needed.",
        "icon": "W",
        "settings": [
            ("bDumpCellExtended", "Cell Extended", "Detailed cell properties and ownership"),
            ("bDumpCellRefs", "Cell References", "All objects placed in the current cell"),
            ("bDumpWorldSpace", "World Space", "Worldspace metadata and dimensions"),
            ("bDumpActiveRegions", "Active Regions", "Currently active regions and weather zones"),
            ("bDumpProcessLists", "Process Lists", "NPC AI schedules and active packages"),
        ],
    },
    "Raw Debug Data": {
        "description": "Memory dumps and low-level object data. "
                       "Produces very large output. Only for OBSE plugin developers.",
        "icon": "D",
        "settings": [
            ("bDumpPlayerRawData", "Player Raw Data", "Raw memory dump of player object"),
            ("bDumpPlayerMemory", "Player Memory", "Hexadecimal memory region dump"),
            ("bDumpExtraDataTypes", "Extra Data Types", "All ExtraData entries on the player"),
            ("bDumpPlayerExtraDetail", "Player Extra Detail", "Decoded ExtraData with field names"),
            ("bDumpNPCRawData", "NPC Raw Data", "Raw data for nearby NPCs"),
            ("bDumpAppearanceData", "Appearance Data", "Player appearance/race/body data from save"),
        ],
    },
    "Weather / Climate": {
        "description": "Detailed weather and climate internals. "
                       "Only needed for weather-related mod development.",
        "icon": "W",
        "settings": [
            ("bDumpSkyColors", "Sky Colors", "Current sky gradient color values"),
            ("bDumpWeatherRaw", "Weather Raw", "Internal weather object data"),
            ("bDumpClimateRaw", "Climate Raw", "Climate template data"),
        ],
    },
    "Game Data Enumerations": {
        "description": "Enumerate game database records (forms). "
                       "Produces huge output — use sparingly for reference/modding.",
        "icon": "G",
        "settings": [
            ("bDumpAllGlobals", "All Globals", "Every global variable in the game"),
            ("bDumpFormListMapping", "Form List Mapping", "FormID to type mapping table"),
            ("bDumpFormListCounts", "Form List Counts", "Count of each form type"),
            ("bDumpBirthSignRaw", "Birthsigns", "All birthsign definitions"),
            ("bDumpGameSettings", "Game Settings", "GMSTs (gameplay tuning values)"),
            ("bDumpModDetails", "Mod Details", "Detailed mod/plugin metadata"),
            ("bDumpMagicEffects", "Magic Effects", "All magic effect definitions"),
            ("bDumpRaceRaw", "Races", "Race definitions with attributes and abilities"),
            ("bDumpEffectSettings", "Effect Settings", "Magic effect base settings"),
            ("bDumpEnchantments", "Enchantments", "All enchantment records"),
            ("bDumpDataHandlerProbe", "DataHandler Probe", "Raw DataHandler internal state"),
            ("bDumpSounds", "Sounds", "Sound descriptor records"),
        ],
    },
    "DataHandler Form Lists": {
        "description": "Enumerate every record of a specific type from the game's DataHandler. "
                       "Each one can produce thousands of lines. Use individually as needed.",
        "icon": "F",
        "settings": [
            ("bDumpAllRaces", "All Races", "Every race form"),
            ("bDumpAllClasses", "All Classes", "Every class form"),
            ("bDumpAllFactions", "All Factions", "Every faction form"),
            ("bDumpAllHairForms", "All Hair", "Every hair form"),
            ("bDumpAllEyeForms", "All Eyes", "Every eye form"),
            ("bDumpAllScripts", "All Scripts", "Every script form"),
            ("bDumpAllLandTextures", "All Land Textures", "Every landscape texture"),
            ("bDumpAllIngredients", "All Ingredients", "Every ingredient form"),
            ("bDumpAllSpells", "All Spells", "Every spell form"),
            ("bDumpAllActivators", "All Activators", "Every activator form"),
            ("bDumpAllApparatus", "All Apparatus", "Every alchemy apparatus"),
            ("bDumpAllArmor", "All Armor", "Every armor form"),
            ("bDumpAllBooks", "All Books", "Every book form"),
            ("bDumpAllClothing", "All Clothing", "Every clothing form"),
            ("bDumpAllContainers", "All Containers", "Every container form"),
            ("bDumpAllDoors", "All Doors", "Every door form"),
            ("bDumpAllLights", "All Lights", "Every light form"),
            ("bDumpAllMisc", "All Misc Items", "Every miscellaneous item"),
            ("bDumpAllFlora", "All Flora", "Every flora (harvestable plant)"),
            ("bDumpAllFurniture", "All Furniture", "Every furniture marker"),
            ("bDumpAllWeapons", "All Weapons", "Every weapon form"),
            ("bDumpAllAmmo", "All Ammo", "Every ammo (arrow/bolt) form"),
            ("bDumpAllNPCs", "All NPCs", "Every NPC form"),
            ("bDumpAllCreatures", "All Creatures", "Every creature form"),
            ("bDumpAllLeveledCreatures", "All Leveled Creatures", "Every leveled creature list"),
            ("bDumpAllSoulGems", "All Soul Gems", "Every soul gem form"),
            ("bDumpAllKeys", "All Keys", "Every key form"),
            ("bDumpAllAlchemyItems", "All Alchemy Items", "Every potion/poison form"),
            ("bDumpAllSigilStones", "All Sigil Stones", "Every sigil stone form"),
            ("bDumpAllLeveledItems", "All Leveled Items", "Every leveled item list"),
            ("bDumpAllLeveledSpells", "All Leveled Spells", "Every leveled spell list"),
            ("bDumpAllDialogs", "All Dialogs", "Every dialog topic"),
            ("bDumpAllQuests", "All Quests", "Every quest form"),
            ("bDumpAllPackages", "All Packages", "Every AI package form"),
            ("bDumpAllCombatStyles", "All Combat Styles", "Every combat style form"),
            ("bDumpAllLoadScreens", "All Load Screens", "Every loading screen"),
            ("bDumpAllWaterForms", "All Water Forms", "Every water type"),
            ("bDumpAllEffectShaders", "All Effect Shaders", "Every visual effect shader"),
            ("bDumpAllGMST", "All GMSTs", "Every game setting"),
            ("bDumpAllSkillForms", "All Skill Forms", "Every skill definition"),
            ("bDumpAllEffectDefs", "All Effect Defs", "Every magic effect definition"),
            ("bDumpAllStatics", "All Statics", "Every static mesh form"),
            ("bDumpAllGrass", "All Grass", "Every grass form"),
            ("bDumpAllTrees", "All Trees", "Every tree form"),
            ("bDumpAllSubSpaces", "All SubSpaces", "Every subspace form"),
            ("bDumpAllSNDG", "All SNDG", "Every sound generator form"),
            ("bDumpAllWeatherForms", "All Weather Forms", "Every weather definition"),
            ("bDumpAllClimateForms", "All Climate Forms", "Every climate definition"),
            ("bDumpAllRegionForms", "All Region Forms", "Every region definition"),
            ("bDumpAllCellForms", "All Cell Forms", "Every cell form"),
            ("bDumpAllREFR", "All REFR", "Every placed object reference"),
            ("bDumpAllACHR", "All ACHR", "Every placed NPC reference"),
            ("bDumpAllACRE", "All ACRE", "Every placed creature reference"),
            ("bDumpAllPathGrids", "All Path Grids", "Every pathfinding grid"),
            ("bDumpAllWorldSpaceForms", "All WorldSpaces", "Every worldspace form"),
            ("bDumpAllLandForms", "All Land Forms", "Every landscape form"),
            ("bDumpAllTLOD", "All TLOD", "Every terrain LOD record"),
            ("bDumpAllRoads", "All Roads", "Every road form"),
            ("bDumpAllDialogInfos", "All Dialog Infos", "Every dialog info record"),
            ("bDumpAllIdles", "All Idles", "Every idle animation form"),
            ("bDumpAllANIO", "All ANIO", "Every animated object form"),
            ("bDumpAllTOFT", "All TOFT", "Every TOFT form"),
            ("bDumpAllSounds", "All Sounds", "Every sound form"),
            ("bDumpAllEnchantments", "All Enchantments", "Every enchantment form"),
            ("bDumpAllBirthSigns", "All Birth Signs", "Every birthsign form"),
            ("bDumpFormTypeSummary", "Form Type Summary", "Count and summary of every form type"),
            ("bDumpInteriorCells", "Interior Cells", "List of all interior cells"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

PRESETS = {
    "Varla-HUD (Recommended)": {
        "description": "Settings needed for Varla-HUD to work correctly. "
                       "This is the default configuration.",
        "values": {
            # Turn ON all Player Character Data except weather
            "bDumpSaveFormat": 1, "bDumpPlayerCharacter": 1, "bDumpPosition": 1,
            "bDumpCharacterInfo": 1, "bDumpFameInfamy": 1, "bDumpGameTime": 1,
            "bDumpGlobalVars": 1, "bDumpMiscStats": 1, "bDumpActiveQuest": 1,
            "bDumpQuestList": 1, "bDumpQuestScriptVars": 1, "bDumpFactions": 1,
            "bDumpAttributes": 1, "bDumpDerivedStats": 1, "bDumpSkills": 1,
            "bDumpMagicResist": 1, "bDumpSpells": 1, "bDumpInventory": 1,
            "bDumpCellItems": 1, "bDumpWeather": 0, "bDumpPluginList": 1,
            "bDumpSkillProgress": 1, "bDumpQuickKeys": 1, "bDumpStatusEffects": 1,
            "bDumpAVModifiers": 1, "bDumpActiveMagicEffects": 1,
            "bDumpInventoryDetail": 1,
            # Turn OFF everything else (implicit: any key not listed stays 0)
        },
    },
    "Minimal": {
        "description": "Bare minimum for basic character info. "
                       "Fastest dump, smallest file.",
        "values": {
            "bDumpSaveFormat": 1, "bDumpPlayerCharacter": 1,
            "bDumpCharacterInfo": 1, "bDumpAttributes": 1, "bDumpSkills": 1,
            "bDumpInventory": 1, "bDumpSpells": 1, "bDumpQuestList": 1,
        },
    },
    "Everything ON": {
        "description": "Dump every possible piece of data. "
                       "WARNING: Produces very large files and may be slow!",
        "values": "__ALL_ON__",
    },
    "Everything OFF": {
        "description": "Turn off all dump settings. "
                       "Useful as a starting point for custom configs.",
        "values": "__ALL_OFF__",
    },
}

# ---------------------------------------------------------------------------
# INI File Parser
# ---------------------------------------------------------------------------

DEFAULT_INI_PATH = (
    r"E:\SteamLibrary\steamapps\common\Oblivion Remastered"
    r"\OblivionRemastered\Binaries\Win64\OBSE\varla.ini"
)


def parse_ini(path: str) -> dict[str, int]:
    """Parse the INI file and return {key: 0|1} for boolean settings."""
    values = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(";") or line.startswith("[") or not line:
                continue
            m = re.match(r"^(\w+)\s*=\s*(\d+)", line)
            if m:
                values[m.group(1)] = int(m.group(2))
    return values


def write_ini(path: str, values: dict[str, int]) -> None:
    """Write values back to the INI file, preserving comments and structure."""
    lines = []
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        m = re.match(r"^(\w+)\s*=\s*\d+", stripped)
        if m:
            key = m.group(1)
            if key in values:
                new_lines.append(f"{key}={values[key]}\n")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


# ---------------------------------------------------------------------------
# Custom Widgets
# ---------------------------------------------------------------------------

class SettingRow(QWidget):
    """A single setting toggle with name, description, and checkbox."""

    toggled = Signal(str, bool)  # (ini_key, new_state)

    def __init__(self, ini_key: str, friendly_name: str, description: str,
                 checked: bool = False, parent=None):
        super().__init__(parent)
        self.ini_key = ini_key
        self._setup_ui(friendly_name, description, checked)

    def _setup_ui(self, name: str, desc: str, checked: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(10)

        # Toggle checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("iniToggle")
        self.checkbox.setChecked(checked)
        self.checkbox.setFixedWidth(56)
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        # Text column
        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)

        name_label = QLabel(name)
        name_label.setObjectName("settingName")
        text_col.addWidget(name_label)

        desc_label = QLabel(desc)
        desc_label.setObjectName("settingDesc")
        desc_label.setWordWrap(True)
        text_col.addWidget(desc_label)

        layout.addLayout(text_col, 1)

        # INI key label (small, faded)
        key_label = QLabel(self.ini_key)
        key_label.setObjectName("settingDesc")
        key_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        key_label.setFixedWidth(200)
        layout.addWidget(key_label)

    def _on_toggled(self, state: bool):
        self.toggled.emit(self.ini_key, state)

    def set_checked(self, checked: bool, silent: bool = False):
        if silent:
            self.checkbox.blockSignals(True)
        self.checkbox.setChecked(checked)
        if silent:
            self.checkbox.blockSignals(False)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def matches_search(self, text: str) -> bool:
        text = text.lower()
        return (text in self.ini_key.lower() or
                text in self.findChild(QLabel, "settingName").text().lower() or
                text in self.findChildren(QLabel, "settingDesc")[0].text().lower())


class CategorySection(QWidget):
    """A collapsible group of settings."""

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        self.title = title
        self._rows: list[SettingRow] = []
        self._collapsed = False
        self._setup_ui(title, description)

    def _setup_ui(self, title: str, description: str):
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 8)
        self._main_layout.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; "
            f"border: 1px solid {COLORS['border_dark']}; "
            f"border-radius: 4px;"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        # Collapse button
        self._collapse_btn = QPushButton("-")
        self._collapse_btn.setFixedSize(24, 24)
        self._collapse_btn.setStyleSheet(
            f"background-color: {COLORS['bg_tertiary']}; "
            f"color: {COLORS['text_primary']}; "
            f"border: 1px solid {COLORS['border_primary']}; "
            f"border-radius: 3px; font-weight: bold; font-size: 12pt; padding: 0;"
        )
        self._collapse_btn.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self._collapse_btn)

        # Title + description
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName("categoryHeader")
        text_col.addWidget(title_label)

        desc_label = QLabel(description)
        desc_label.setObjectName("settingDesc")
        desc_label.setWordWrap(True)
        text_col.addWidget(desc_label)

        header_layout.addLayout(text_col, 1)

        # Counter
        self._counter = QLabel("0 / 0")
        self._counter.setObjectName("counterLabel")
        header_layout.addWidget(self._counter)

        # Group toggle buttons
        btn_all = QPushButton("All ON")
        btn_all.setObjectName("groupToggleBtn")
        btn_all.clicked.connect(lambda: self._set_all(True))
        header_layout.addWidget(btn_all)

        btn_none = QPushButton("All OFF")
        btn_none.setObjectName("groupToggleBtn")
        btn_none.clicked.connect(lambda: self._set_all(False))
        header_layout.addWidget(btn_none)

        self._main_layout.addWidget(header)

        # Content area (the rows go here)
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        self._main_layout.addWidget(self._content)

    def add_row(self, row: SettingRow):
        self._rows.append(row)
        self._content_layout.addWidget(row)
        row.toggled.connect(lambda *_: self._update_counter())

    def _update_counter(self):
        visible = [r for r in self._rows if not r.isHidden()]
        on = sum(1 for r in visible if r.is_checked())
        total = len(visible)
        self._counter.setText(f"{on} / {total}")

    def _set_all(self, state: bool):
        for row in self._rows:
            if not row.isHidden():
                row.set_checked(state)
        self._update_counter()

    def _toggle_collapse(self):
        self._collapsed = not self._collapsed
        self._content.setVisible(not self._collapsed)
        self._collapse_btn.setText("+" if self._collapsed else "-")

    def filter_rows(self, text: str):
        """Show/hide rows based on search text. Returns number of visible rows."""
        visible = 0
        for row in self._rows:
            if not text or row.matches_search(text):
                row.setVisible(True)
                visible += 1
            else:
                row.setVisible(False)
        # Hide entire section if no rows match
        self.setVisible(visible > 0 or not text)
        self._update_counter()
        return visible

    def update_counter(self):
        self._update_counter()


# ---------------------------------------------------------------------------
# Main Window
# ---------------------------------------------------------------------------

class VarlaIniEditor(QMainWindow):
    """Main editor window."""

    def __init__(self, ini_path: str = DEFAULT_INI_PATH):
        super().__init__()
        self.ini_path = ini_path
        self._original_values: dict[str, int] = {}
        self._setting_rows: dict[str, SettingRow] = {}
        self._sections: list[CategorySection] = []
        self._dirty = False

        self.setWindowTitle("Varla INI Editor")
        self.setMinimumSize(750, 600)
        self.resize(900, 750)

        self._setup_ui()
        self._load_ini()

    # ── UI Setup ──────────────────────────────────────────────────────────

    def _setup_ui(self):
        self.setStyleSheet(EDITOR_QSS)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ──
        top_bar = QWidget()
        top_bar.setStyleSheet(
            f"background-color: {COLORS['nav_tab_bg']}; "
            f"border-bottom: 2px solid {COLORS['border_dark']};"
        )
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("Varla INI Editor")
        title.setObjectName("editorTitle")
        top_layout.addWidget(title)

        self._dirty_dot = QLabel("")
        self._dirty_dot.setObjectName("dirtyDot")
        top_layout.addWidget(self._dirty_dot)

        top_layout.addStretch()

        # INI path display
        path_label = QLabel("INI:")
        path_label.setObjectName("settingDesc")
        top_layout.addWidget(path_label)

        self._path_label = QLabel(self.ini_path)
        self._path_label.setObjectName("settingDesc")
        self._path_label.setMaximumWidth(400)
        self._path_label.setToolTip(self.ini_path)
        top_layout.addWidget(self._path_label)

        browse_btn = QPushButton("Browse...")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_ini)
        top_layout.addWidget(browse_btn)

        # Separator
        top_sep = QFrame()
        top_sep.setFrameShape(QFrame.Shape.VLine)
        top_sep.setFixedHeight(22)
        top_sep.setStyleSheet(f"color: {COLORS['border_dark']};")
        top_layout.addWidget(top_sep)

        # [SaveDump] export master toggle
        export_sec_label = QLabel("[SaveDump]")
        export_sec_label.setObjectName("editorSubtitle")
        top_layout.addWidget(export_sec_label)

        self._export_btn = QPushButton("Export: ON")
        self._export_btn.setObjectName("exportToggleBtn")
        self._export_btn.setCheckable(True)
        self._export_btn.setChecked(True)
        self._export_btn.setFixedWidth(105)
        self._export_btn.setToolTip(
            "bExportEnabled — master switch.\n"
            "OFF prevents any dump from being written on save,\n"
            "protecting your existing save_dump.txt."
        )
        self._export_btn.clicked.connect(self._on_export_toggled)
        top_layout.addWidget(self._export_btn)

        root.addWidget(top_bar)

        # ── Toolbar: search + presets ──
        toolbar = QWidget()
        toolbar.setStyleSheet(
            f"background-color: {COLORS['bg_secondary']}; "
            f"border-bottom: 1px solid {COLORS['border_dark']};"
        )
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 8, 16, 8)

        # Search
        self._search = QLineEdit()
        self._search.setObjectName("searchBar")
        self._search.setPlaceholderText("Search settings...")
        self._search.setClearButtonEnabled(True)
        self._search.setMaximumWidth(300)
        self._search.textChanged.connect(self._on_search)
        tb_layout.addWidget(self._search)

        tb_layout.addSpacing(20)

        # Presets
        presets_label = QLabel("Presets:")
        presets_label.setObjectName("settingName")
        tb_layout.addWidget(presets_label)

        self._preset_buttons: dict[str, QPushButton] = {}
        for preset_name, preset_data in PRESETS.items():
            btn = QPushButton(preset_name)
            btn.setObjectName("presetBtn")
            btn.setToolTip(preset_data["description"])
            btn.clicked.connect(lambda checked=False, n=preset_name: self._apply_preset(n))
            tb_layout.addWidget(btn)
            self._preset_buttons[preset_name] = btn

        tb_layout.addStretch()

        root.addWidget(toolbar)

        # ── Scrollable settings area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        content = QWidget()
        self._settings_layout = QVBoxLayout(content)
        self._settings_layout.setContentsMargins(16, 12, 16, 12)
        self._settings_layout.setSpacing(12)

        self._build_setting_groups()

        self._settings_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        # ── Bottom bar ──
        bottom = QWidget()
        bottom.setStyleSheet(
            f"background-color: {COLORS['nav_tab_bg']}; "
            f"border-top: 2px solid {COLORS['border_dark']};"
        )
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(16, 8, 16, 8)

        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("settingDesc")
        bottom_layout.addWidget(self._status_label)

        bottom_layout.addStretch()

        # Revert button
        revert_btn = QPushButton("Revert Changes")
        revert_btn.setObjectName("dangerBtn")
        revert_btn.clicked.connect(self._revert)
        bottom_layout.addWidget(revert_btn)

        # Save button
        save_btn = QPushButton("Save")
        save_btn.setObjectName("generateBtn")
        save_btn.setFixedWidth(120)
        save_btn.clicked.connect(self._save)
        bottom_layout.addWidget(save_btn)

        root.addWidget(bottom)

    def _build_setting_groups(self):
        """Build all category sections and setting rows."""
        for group_name, group_data in SETTING_GROUPS.items():
            section = CategorySection(
                group_name, group_data["description"]
            )
            for ini_key, friendly_name, desc in group_data["settings"]:
                row = SettingRow(ini_key, friendly_name, desc)
                row.toggled.connect(self._on_setting_changed)
                section.add_row(row)
                self._setting_rows[ini_key] = row
            self._sections.append(section)
            self._settings_layout.addWidget(section)

    # ── INI Load / Save ───────────────────────────────────────────────────

    def _load_ini(self):
        """Load values from the INI file into the UI."""
        if not os.path.exists(self.ini_path):
            self._status_label.setText(f"File not found: {self.ini_path}")
            return

        try:
            values = parse_ini(self.ini_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read INI:\n{e}")
            return

        self._original_values = dict(values)

        # Master export toggle
        export_enabled = values.get("bExportEnabled", 1) == 1
        self._export_btn.blockSignals(True)
        self._export_btn.setChecked(export_enabled)
        self._export_btn.setText("Export: ON" if export_enabled else "Export: OFF")
        self._export_btn.blockSignals(False)

        for key, row in self._setting_rows.items():
            row.set_checked(values.get(key, 0) == 1, silent=True)

        for section in self._sections:
            section.update_counter()

        self._set_dirty(False)
        self._status_label.setText(f"Loaded {len(values)} settings")

    def _save(self):
        """Write current settings to the INI file."""
        values = self._gather_values()
        try:
            write_ini(self.ini_path, values)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save INI:\n{e}")
            return

        self._original_values = dict(values)
        self._set_dirty(False)
        self._status_label.setText("Saved successfully!")
        QTimer.singleShot(3000, lambda: self._status_label.setText("Ready"))

    def _revert(self):
        """Revert all settings to the last saved state."""
        if not self._dirty:
            return
        reply = QMessageBox.question(
            self, "Revert Changes",
            "Discard all unsaved changes and reload from file?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._load_ini()

    def _gather_values(self) -> dict[str, int]:
        """Collect all current toggle values."""
        values = {"bExportEnabled": 1 if self._export_btn.isChecked() else 0}
        for key, row in self._setting_rows.items():
            values[key] = 1 if row.is_checked() else 0
        return values

    # ── Event Handlers ────────────────────────────────────────────────────

    def _on_export_toggled(self, checked: bool):
        self._export_btn.setText("Export: ON" if checked else "Export: OFF")
        self._set_dirty(True)

    def _on_setting_changed(self, key: str, state: bool):
        self._set_dirty(True)
        # Update preset highlight
        self._update_preset_highlight()

    def _set_dirty(self, dirty: bool):
        self._dirty = dirty
        self._dirty_dot.setText("*" if dirty else "")
        title = "Varla INI Editor"
        if dirty:
            title += " *"
        self.setWindowTitle(title)

    def _on_search(self, text: str):
        for section in self._sections:
            section.filter_rows(text)

    def _browse_ini(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select varla.ini", os.path.dirname(self.ini_path),
            "INI Files (*.ini);;All Files (*.*)",
        )
        if path:
            self.ini_path = path
            self._path_label.setText(path)
            self._path_label.setToolTip(path)
            self._load_ini()

    # ── Presets ───────────────────────────────────────────────────────────

    def _apply_preset(self, preset_name: str):
        preset = PRESETS[preset_name]
        values = preset["values"]

        if values == "__ALL_ON__":
            for row in self._setting_rows.values():
                row.set_checked(True)
        elif values == "__ALL_OFF__":
            for row in self._setting_rows.values():
                row.set_checked(False)
        else:
            # Set explicit values, default everything else to 0
            all_keys = set(self._setting_rows.keys())
            for key in all_keys:
                self._setting_rows[key].set_checked(values.get(key, 0) == 1)

        for section in self._sections:
            section.update_counter()

        self._set_dirty(True)
        self._update_preset_highlight()
        self._status_label.setText(f'Applied preset: "{preset_name}"')

    def _update_preset_highlight(self):
        """Highlight the active preset button if current values match."""
        current = self._gather_values()
        all_keys = set(self._setting_rows.keys())

        for name, btn in self._preset_buttons.items():
            preset_vals = PRESETS[name]["values"]
            match = False

            if preset_vals == "__ALL_ON__":
                match = all(v == 1 for v in current.values())
            elif preset_vals == "__ALL_OFF__":
                match = all(v == 0 for v in current.values())
            else:
                expected = {k: preset_vals.get(k, 0) for k in all_keys}
                match = current == expected

            btn.setProperty("active", "true" if match else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ── Close guard ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._dirty:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if reply == QMessageBox.Save:
                self._save()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Varla INI Editor")

    window = VarlaIniEditor()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
