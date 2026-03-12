"""
Data Models for Oblivion Character Data
Comprehensive models for all character data types.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class CharacterInfo:
    """Character basic information."""
    name: str = "Hero of Kvatch"
    race: str = "none"
    class_name: str = "Warrior"
    birthsign: str = "Warrior"
    level: int = 50
    sex: str = ""


@dataclass
class SpellEffect:
    """Single spell effect."""
    name: str = ""
    magnitude: int = 0
    duration: int = 0
    area: int = 0
    range: str = ""  # "Self", "Touch", "Target"
    effect_code: str = ""  # e.g. "REHE", "SABS"


@dataclass
class Spell:
    """Represents a spell from the export log."""
    form_id: str
    name: str
    magicka_cost: int = 0
    spell_type: str = ""  # "Spell", "Power", "Ability"
    effects: List[SpellEffect] = field(default_factory=list)
    is_player_created: bool = False


@dataclass
class InventoryItem:
    """Represents an inventory item from the export log."""
    form_id: str
    name: str
    quantity: int
    item_type: str = ""  # "Weapon", "Armor", "Potion", "Ingredient", etc.
    equipped: bool = False
    condition_current: float = -1   # -1 = not applicable (e.g. potions have no durability)
    condition_max: float = -1
    enchant_current: float = -1     # -1 = not applicable
    enchant_max: float = -1


@dataclass
class Faction:
    """Represents a faction membership."""
    form_id: str
    name: str
    rank: int
    title: str = ""


@dataclass
class ActiveQuest:
    """Represents the currently active quest."""
    form_id: str
    editor_id: str = ""
    name: str = ""
    stage: int = 0
    flags: str = ""


@dataclass
class CurrentQuest:
    """Represents a quest in progress with its stage."""
    editor_id: str
    stage: int = 0
    name: str = ""
    form_id: str = ""
    flags: str = ""


@dataclass
class CompletedQuest:
    """Represents a completed quest with enriched data."""
    editor_id: str
    name: str = ""
    form_id: str = ""
    final_stage: int = 0


@dataclass
class PCMiscStat:
    """Player miscellaneous statistic."""
    index: int
    name: str
    value: int = 0


# PCMiscStat names lookup (skipping index 1)
PCMISCSTAT_NAMES = {
    0: "Days in Prison",
    2: "Skill Increases",
    3: "Training Sessions",
    4: "Largest Bounty",
    5: "Creatures Killed",
    6: "People Killed",
    7: "Places Discovered",
    8: "Locks Picked",
    9: "Picks Broken",
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
    22: "Days as a Vampire",
    23: "Last Day as Vampire",
    24: "People Fed On",
    25: "Jokes Told",
    26: "Diseases Contracted",
    27: "Nirnroots Found",
    28: "Items Stolen",
    29: "Items Pickpocketed",
    30: "Trespasses",
    31: "Assaults",
    32: "Murders",
    33: "Horses Stolen"
}


# Attribute names
ATTRIBUTE_NAMES = [
    "Strength", "Willpower", "Intelligence", "Endurance",
    "Speed", "Agility", "Personality", "Luck"
]


# Skill names (no spaces for storage/export)
SKILL_NAMES = [
    "Armorer", "Athletics", "Blade", "Block", "Blunt", "HandToHand",
    "HeavyArmor", "Alchemy", "Alteration", "Conjuration", "Destruction",
    "Illusion", "Mysticism", "Restoration", "Acrobatics", "LightArmor",
    "Marksman", "Mercantile", "Security", "Sneak", "Speechcraft"
]


# Skill display names (with spaces for UI)
SKILL_DISPLAY_NAMES = {
    "HandToHand": "Hand to Hand",
    "HeavyArmor": "Heavy Armor",
    "LightArmor": "Light Armor"
}


def get_skill_display_name(skill_name: str) -> str:
    """Get display name for skill (with spaces if applicable)."""
    return SKILL_DISPLAY_NAMES.get(skill_name, skill_name)


def get_skill_storage_name(display_name: str) -> str:
    """Get storage name from display name (remove spaces)."""
    reverse_map = {v: k for k, v in SKILL_DISPLAY_NAMES.items()}
    return reverse_map.get(display_name, display_name)


@dataclass
class Vitals:
    """Player vitals (health, magicka, fatigue, encumbrance)."""
    health_current: float = 0
    health_base: float = 0
    magicka_current: float = 0
    magicka_base: float = 0
    fatigue_current: float = 0
    fatigue_base: float = 0
    encumbrance: float = 0


@dataclass
class MagicResistances:
    """Magic resistance percentages."""
    fire: float = 0
    frost: float = 0
    shock: float = 0
    magic: float = 0
    disease: float = 0
    poison: float = 0
    paralysis: float = 0
    normal_weapons: float = 0


@dataclass
class MagicEffects:
    """Active magic effect percentages/flags."""
    spell_absorption: float = 0
    spell_reflect: float = 0
    reflect_damage: float = 0
    chameleon: float = 0
    invisibility: float = 0
    stunted_magicka: int = 0


@dataclass
class GlobalVariable:
    """A game global variable."""
    form_id: str
    name: str
    value: float
    var_type: str = "short"  # 'short', 'long', 'float'


@dataclass
class GameTime:
    """Game time information."""
    days_passed: float = 0
    game_year: int = 433
    game_month: int = 1
    game_day: int = 1
    game_hour: float = 0


@dataclass
class ActiveMagicEffect:
    """An active magic effect on the player."""
    effect_code: str = ""
    magnitude: float = 0
    duration: float = 0
    state: str = ""
    source_name: str = ""
    source_form_id: str = ""


@dataclass
class PlayerPosition:
    """Player position and rotation in the world."""
    x: float = 0
    y: float = 0
    z: float = 0
    rot_x: float = 0
    rot_y: float = 0
    rot_z: float = 0
    scale: float = 1.0
    parent_cell: str = ""
    parent_cell_form_id: str = ""


@dataclass
class WeatherInfo:
    """Weather and sky information."""
    current_weather: str = ""
    current_weather_form_id: str = ""
    climate_form_id: str = ""
    sky_mode: int = 0


@dataclass
class SkillXPProgress:
    """XP progress for a single skill."""
    skill_name: str = ""
    current_xp: float = 0
    needed_xp: float = 0
    percentage: int = 0
    gained_this_level: float = 0


@dataclass
class TrainingProgress:
    """Training session progress for current level."""
    sessions_used: int = 0
    sessions_max: int = 5


@dataclass
class QuickKeySlot:
    """A quick key assignment."""
    slot_number: int = 0
    name: str = ""
    form_id: str = ""
    slot_type: str = ""


@dataclass
class StatusEffects:
    """Status effects and additional actor values."""
    aggression: int = 0
    confidence: int = 0
    energy: int = 0
    responsibility: int = 0
    nighteye_bonus: float = 0
    attack_bonus: float = 0
    defend_bonus: float = 0
    casting_penalty: float = 0
    blindness: float = 0
    paralysis: float = 0
    silence: float = 0
    confusion: float = 0
    detect_item_range: float = 0
    swim_speed_multiplier: float = 0
    water_breathing: float = 0
    water_walking: float = 0
    detect_life_range: float = 0
    telekinesis: float = 0
    vampirism: float = 0
    darkness: float = 0
    resist_water_damage: float = 0


@dataclass
class ActorValueModifier:
    """Actor value modifier entry."""
    actor_value: str = ""
    fortify_max: float = 0
    script_modifier: float = 0
    damage_modifier: float = 0


@dataclass
class ItemCondition:
    """Item durability condition."""
    name: str = ""
    current_hp: int = 0
    max_hp: int = 0
    percentage: int = 0


@dataclass
class EnchantmentCharge:
    """Enchantment charge status for a weapon."""
    name: str = ""
    current_charge: int = 0
    max_charge: int = 0
    percentage: int = 0
    status: str = ""


@dataclass
class StolenItem:
    """A stolen item in inventory."""
    name: str = ""
    quantity: int = 0
    owner_name: str = ""
    owner_form_id: str = ""


@dataclass
class GoldEconomy:
    """Gold and economic summary."""
    current_gold: int = 0
    stores_invested: int = 0
    houses_owned: int = 0
    horses_owned: int = 0
    largest_bounty: int = 0


@dataclass
class Appearance:
    """Character appearance / FaceGen data."""
    hair: str = ""
    eyes: str = ""
    hair_color: str = ""
    hair_length: str = ""
    facegen_geometry: str = ""
    facegen_asymmetry: str = ""
    facegen_texture: str = ""
    facegen_geometry2: str = ""
    facegen_asymmetry2: str = ""
    facegen_texture2: str = ""


@dataclass
class CharacterData:
    """Complete character data."""
    character: CharacterInfo = field(default_factory=CharacterInfo)
    attributes: Dict[str, int] = field(default_factory=lambda: {attr: 40 for attr in ATTRIBUTE_NAMES})
    skills: Dict[str, int] = field(default_factory=lambda: {skill: 25 for skill in SKILL_NAMES})
    skills_current: Dict[str, int] = field(default_factory=dict)
    fame: int = 0
    infamy: int = 0
    bounty: int = 0
    pc_misc_stats: Dict[int, int] = field(default_factory=dict)
    factions: List[Faction] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)
    completed_quests_enriched: List[CompletedQuest] = field(default_factory=list)
    active_quest: Optional[ActiveQuest] = None
    current_quests: List[CurrentQuest] = field(default_factory=list)
    items: List[InventoryItem] = field(default_factory=list)
    spells: List[Spell] = field(default_factory=list)
    spells_to_remove: List[Spell] = field(default_factory=list)
    # New fields from save dump
    vitals: Vitals = field(default_factory=Vitals)
    magic_resistances: MagicResistances = field(default_factory=MagicResistances)
    magic_effects: MagicEffects = field(default_factory=MagicEffects)
    global_variables: List[GlobalVariable] = field(default_factory=list)
    game_time: GameTime = field(default_factory=GameTime)
    active_magic_effects: List[ActiveMagicEffect] = field(default_factory=list)
    player_position: PlayerPosition = field(default_factory=PlayerPosition)
    weather: WeatherInfo = field(default_factory=WeatherInfo)
    plugins: List[str] = field(default_factory=list)
    # Tier 1 structured data
    skill_xp_progress: List['SkillXPProgress'] = field(default_factory=list)
    level_up_progress: str = ""
    training_progress: 'TrainingProgress' = field(default_factory=TrainingProgress)
    quick_keys: List['QuickKeySlot'] = field(default_factory=list)
    status_effects: 'StatusEffects' = field(default_factory=StatusEffects)
    actor_value_modifiers: List['ActorValueModifier'] = field(default_factory=list)
    item_conditions: List['ItemCondition'] = field(default_factory=list)
    enchantment_charges: List['EnchantmentCharge'] = field(default_factory=list)
    stolen_items: List['StolenItem'] = field(default_factory=list)
    gold_economy: 'GoldEconomy' = field(default_factory=GoldEconomy)
    appearance: 'Appearance' = field(default_factory=Appearance)
    racial_abilities: List[str] = field(default_factory=list)
    class_details: str = ""
    equipped_items_detail: str = ""
    # Tier 2 raw section capture
    raw_sections: Dict[str, str] = field(default_factory=dict)
    # Save dump round-trip metadata
    dump_format: str = ""  # "remastered" or "classic" - set by parser
    raw_dump_text: str = ""  # Original dump file text for faithful round-trip writing
