"""Data models for the Oblivion Import Manager."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import copy


@dataclass
class Item:
    """Represents an inventory item."""
    form_id: str
    name: str = "name missing"
    quantity: int = 1

    def __post_init__(self):
        # Ensure form_id is uppercase and 8 characters
        self.form_id = self.form_id.upper().zfill(8)


@dataclass
class Spell:
    """Represents a spell (spells never have quantities)."""
    form_id: str
    name: str = "name missing"

    def __post_init__(self):
        # Ensure form_id is uppercase and 8 characters
        self.form_id = self.form_id.upper().zfill(8)


@dataclass
class Preset:
    """
    Represents a character configuration (preset).
    Presets are essentially "characters" - they contain everything for that character.
    """
    name: str
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())
    favorites: List[str] = field(default_factory=list)  # List of form IDs
    exceptions: List[str] = field(default_factory=list)  # List of form IDs
    items: List[dict] = field(default_factory=list)  # List of {"formId": str, "name": str, "quantity": int}
    spells: List[dict] = field(default_factory=list)  # List of {"formId": str, "name": str}

    # Extended fields (raw dicts/lists for JSON round-trip)
    character: Optional[dict] = None          # {name, race, class, birthsign, level}
    attributes: Optional[dict] = None         # {Strength: 55, ...}
    skills: Optional[dict] = None             # {Blade: 100, ...}
    statistics: Optional[dict] = None         # {fame, infamy, bounty, pcMiscStats}
    factions: Optional[list] = None           # [{formId, name, rank, title}]
    quests: Optional[list] = None             # completed quest editor IDs
    active_quest: Optional[dict] = None       # {formId, editorId, stage}
    current_quests: Optional[list] = None     # [{editorId, stage}]
    spells_to_remove: Optional[list] = None   # [{formId, name, ...}]
    bank: Optional[dict] = None
    favorites_by_category: Optional[dict] = None
    exceptions_by_category: Optional[dict] = None
    game_mode: Optional[str] = None
    vitals: Optional[dict] = None
    magic_resistances: Optional[dict] = None
    global_variables: Optional[list] = None
    game_time: Optional[dict] = None
    plugins: Optional[list] = None

    def to_dict(self) -> dict:
        """Convert preset to dictionary for JSON serialization."""
        result = {
            "lastUsed": self.last_used,
            "favorites": self.favorites,
            "exceptions": self.exceptions,
            "items": self.items,
            "spells": self.spells
        }

        # Write all extended fields if they exist
        _extended_fields = {
            "character": self.character,
            "attributes": self.attributes,
            "skills": self.skills,
            "statistics": self.statistics,
            "factions": self.factions,
            "quests": self.quests,
            "activeQuest": self.active_quest,
            "currentQuests": self.current_quests,
            "spellsToRemove": self.spells_to_remove,
            "bank": self.bank,
            "favoritesByCategory": self.favorites_by_category,
            "exceptionsByCategory": self.exceptions_by_category,
            "gameMode": self.game_mode,
            "vitals": self.vitals,
            "magicResistances": self.magic_resistances,
            "globalVariables": self.global_variables,
            "gameTime": self.game_time,
            "plugins": self.plugins,
        }
        for key, value in _extended_fields.items():
            if value is not None:
                result[key] = value

        return result

    @classmethod
    def from_dict(cls, name: str, data: dict) -> 'Preset':
        """Create preset from dictionary."""
        return cls(
            name=name,
            last_used=data.get("lastUsed", datetime.now().isoformat()),
            favorites=data.get("favorites", []),
            exceptions=data.get("exceptions", []),
            items=data.get("items", []),
            spells=data.get("spells", []),
            # Extended fields
            character=data.get("character", None),
            attributes=data.get("attributes", None),
            skills=data.get("skills", None),
            statistics=data.get("statistics", None),
            factions=data.get("factions", None),
            quests=data.get("quests", None),
            active_quest=data.get("activeQuest", None),
            current_quests=data.get("currentQuests", None),
            spells_to_remove=data.get("spellsToRemove", None),
            bank=data.get("bank", None),
            favorites_by_category=data.get("favoritesByCategory", None),
            exceptions_by_category=data.get("exceptionsByCategory", None),
            game_mode=data.get("gameMode", None),
            vitals=data.get("vitals", None),
            magic_resistances=data.get("magicResistances", None),
            global_variables=data.get("globalVariables", None),
            game_time=data.get("gameTime", None),
            plugins=data.get("plugins", None),
        )

    def deep_copy_extended(self) -> dict:
        """Return a deep copy of all extended fields as a dict."""
        fields = {}
        for attr in [
            'character', 'attributes', 'skills', 'statistics', 'factions',
            'quests', 'active_quest', 'current_quests', 'spells_to_remove',
            'bank', 'favorites_by_category', 'exceptions_by_category',
            'game_mode', 'vitals', 'magic_resistances', 'global_variables',
            'game_time', 'plugins',
        ]:
            val = getattr(self, attr)
            fields[attr] = copy.deepcopy(val) if val is not None else None
        return fields

    def get_items(self) -> List[Item]:
        """Convert stored items to Item objects."""
        return [
            Item(
                form_id=item["formId"],
                name=item.get("name", "name missing"),
                quantity=item.get("quantity", 1)
            )
            for item in self.items
        ]

    def get_spells(self) -> List[Spell]:
        """Convert stored spells to Spell objects."""
        return [
            Spell(
                form_id=spell["formId"],
                name=spell.get("name", "name missing")
            )
            for spell in self.spells
        ]

    def update_items(self, items: List[Item]):
        """Update items from Item objects."""
        self.items = [
            {
                "formId": item.form_id,
                "name": item.name,
                "quantity": item.quantity
            }
            for item in items
        ]

    def update_spells(self, spells: List[Spell]):
        """Update spells from Spell objects."""
        self.spells = [
            {
                "formId": spell.form_id,
                "name": spell.name
            }
            for spell in spells
        ]

    def is_favorite(self, form_id: str) -> bool:
        """Check if form ID is favorited."""
        return form_id.upper() in [fid.upper() for fid in self.favorites]

    def is_exception(self, form_id: str) -> bool:
        """Check if form ID is excepted."""
        return form_id.upper() in [fid.upper() for fid in self.exceptions]

    def toggle_favorite(self, form_id: str):
        """Toggle favorite status for a form ID."""
        form_id_upper = form_id.upper()
        existing = [fid for fid in self.favorites if fid.upper() == form_id_upper]

        if existing:
            self.favorites = [fid for fid in self.favorites if fid.upper() != form_id_upper]
        else:
            self.favorites.append(form_id_upper)

    def toggle_exception(self, form_id: str):
        """Toggle exception status for a form ID."""
        form_id_upper = form_id.upper()
        existing = [fid for fid in self.exceptions if fid.upper() == form_id_upper]

        if existing:
            self.exceptions = [fid for fid in self.exceptions if fid.upper() != form_id_upper]
        else:
            self.exceptions.append(form_id_upper)


@dataclass
class AppData:
    """Application data structure."""
    presets: dict[str, Preset] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)  # form_id -> note text
    settings: dict = field(default_factory=lambda: {
        "exportLogPath": str(Path.home() / "Documents" / "My Games" / "Oblivion" / "OBSE" / "save_dump.txt"),
        "importLogPath": r"C:\Steam\steamapps\common\Oblivion\Data\ConScribe Logs\Per-Mod\varla-test.log",
        "currentPreset": None
    })

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "presets": {name: preset.to_dict() for name, preset in self.presets.items()},
            "notes": self.notes,
            "settings": self.settings
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'AppData':
        """Create from dictionary."""
        presets = {
            name: Preset.from_dict(name, preset_data)
            for name, preset_data in data.get("presets", {}).items()
        }

        return cls(
            presets=presets,
            notes=data.get("notes", {}),
            settings=data.get("settings", {})
        )

    def get_most_recent_preset(self) -> Optional[Preset]:
        """Get the most recently used preset."""
        if not self.presets:
            return None

        return max(self.presets.values(), key=lambda p: p.last_used)

    def get_note(self, form_id: str) -> str:
        """Get note for form ID (notes are global across presets)."""
        return self.notes.get(form_id.upper(), "")

    def set_note(self, form_id: str, note: str):
        """Set note for form ID."""
        form_id_upper = form_id.upper()
        if note.strip():
            self.notes[form_id_upper] = note[:500]  # Max 500 chars
        elif form_id_upper in self.notes:
            del self.notes[form_id_upper]
