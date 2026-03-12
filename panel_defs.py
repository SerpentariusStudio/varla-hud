"""
Panel definitions for Varla-HUD.

Provides:
  get_columns(page_key)          -> list[ColumnDef]
  extract_items(page_key, data)  -> list[PanelItem]
  build_staged_filter(panels, char_data) -> StagedFilter
    (also applies inline edits back to char_data and its sub-objects)
"""

from dataclasses import dataclass, field
from typing import Any

from dual_panel import ColumnDef, PanelItem
from models import (
    CharacterData, ATTRIBUTE_NAMES, SKILL_NAMES, PCMISCSTAT_NAMES,
    get_skill_display_name,
)

# ── Inventory type filters ────────────────────────────────────────────────────

_INV_FILTERS = {
    "weapons":       {"Weapon", "Ammunition"},
    "gear":          {"Armor", "Clothing"},
    "alchemy_inv":   {"Potion", "Ingredient", "Apparatus"},
    "miscellaneous": {"Misc", "Book", "Key", "Light"},
    "all_items":     None,
}

# ── Spell range filters ───────────────────────────────────────────────────────

_SPELL_RANGES = {
    "spell_self":   "Self",
    "spell_touch":  "Touch",
    "spell_target": "Target",
    "spell_all":    None,
}

# ── Column definitions ────────────────────────────────────────────────────────

_C = ColumnDef  # shorthand

_CHAR_INFO_COLS = [
    _C("field", "Field",  180),
    _C("value", "Value",  250, editable=True),
]

_ATTRIBUTE_COLS = [
    _C("name",     "Attribute", 160),
    _C("base",     "Base",       80, editable=True, numeric=True, min_val=0, max_val=255),
    _C("__copy__", "→",          28, copy_action=True),
    _C("current",  "Current",    80, editable=True, numeric=True, min_val=0, max_val=255),
]

_SKILL_COLS = [
    _C("name",     "Skill",     160),
    _C("base",     "Base",       80, editable=True, numeric=True, min_val=0, max_val=200),
    _C("__copy__", "→",          28, copy_action=True),
    _C("current",  "Current",    80, editable=True, numeric=True, min_val=0, max_val=200),
]

_FACTION_COLS = [
    _C("name",    "Name",    220),
    _C("rank",    "Rank",     60, editable=True, numeric=True, min_val=-1, max_val=10),
    _C("title",   "Title",   160),
    _C("form_id", "FormID",  110),
]

_DETAILS_COLS = [
    _C("category", "Category", 110),
    _C("field",    "Field",    200),
    _C("value",    "Value",    130, editable=True),
]

_INV_COLS = [
    _C("name",      "Name",       220),
    _C("type",      "Type",       100),
    _C("qty",       "Qty",         55, editable=True, numeric=True, min_val=0, max_val=99999),
    _C("cond_cur",  "HP",          65, editable=True, numeric=True, min_val=0, max_val=99999),
    _C("cond_max",  "HP Max",      75, editable=True, numeric=True, min_val=0, max_val=99999),
    _C("chrg_cur",  "Charge",      70, editable=True, numeric=True, min_val=0, max_val=99999),
    _C("chrg_max",  "Chrg Max",    80, editable=True, numeric=True, min_val=0, max_val=99999),
    _C("equipped",  "Eq.",         40),
    _C("form_id",   "FormID",     110),
]

_SPELL_COLS = [
    _C("name",       "Name",    220),
    _C("spell_type", "Type",     80),
    _C("cost",       "Cost",     65, editable=True, numeric=True, min_val=0, max_val=99999),
    _C("effects",    "Effects", 320),
    _C("form_id",    "FormID",  110),
]

_ACTIVE_EFF_COLS = [
    _C("effect",    "Effect",    160),
    _C("magnitude", "Magnitude",  90),
    _C("duration",  "Duration",   90),
    _C("state",     "State",      90),
    _C("source",    "Source",    220),
]

_ACTIVE_QUEST_COLS = [
    _C("name",      "Name",      220),
    _C("stage",     "Stage",      65, editable=True, numeric=True, min_val=0, max_val=999),
    _C("editor_id", "EditorID",  160),
    _C("flags",     "Flags",      80),
    _C("form_id",   "FormID",    110),
]

_COMPLETED_QUEST_COLS = [
    _C("name",        "Name",       220),
    _C("editor_id",   "EditorID",   160),
    _C("final_stage", "Final Stage", 90),
    _C("form_id",     "FormID",     110),
]

_GLOBAL_COLS = [
    _C("name",     "Name",   220),
    _C("value",    "Value",  110, editable=True, numeric=True,
       min_val=-1e9, max_val=1e9, decimals=2),
    _C("var_type", "Type",    60),
    _C("form_id",  "FormID", 110),
]

_GAME_TIME_COLS = [
    _C("field", "Field",  160),
    _C("value", "Value",  120, editable=True, numeric=True,
       min_val=0, max_val=99999, decimals=3),
]

_PLUGIN_COLS = [
    _C("name",  "Plugin", 420),
    _C("index", "Index",   60),
]

_WORLD_STATE_COLS = [
    _C("category", "Category", 110),
    _C("field",    "Field",    160),
    _C("value",    "Value",    200, editable=True),
]


def get_columns(page_key: str) -> list[ColumnDef]:
    """Return column definitions for the given page key."""
    if page_key == "char_info":         return _CHAR_INFO_COLS
    if page_key == "attributes":        return _ATTRIBUTE_COLS
    if page_key == "skills":            return _SKILL_COLS
    if page_key == "factions":          return _FACTION_COLS
    if page_key == "details":           return _DETAILS_COLS
    if page_key in _INV_FILTERS:        return _INV_COLS
    if page_key in _SPELL_RANGES:       return _SPELL_COLS
    if page_key == "magic_active_effects": return _ACTIVE_EFF_COLS
    if page_key == "active_quests":     return _ACTIVE_QUEST_COLS
    if page_key == "completed_quests":  return _COMPLETED_QUEST_COLS
    if page_key == "globals":           return _GLOBAL_COLS
    if page_key == "game_time":         return _GAME_TIME_COLS
    if page_key == "plugins":           return _PLUGIN_COLS
    if page_key == "world_state":       return _WORLD_STATE_COLS
    # Fallback: generic key-value
    return [_C("field", "Field", 200), _C("value", "Value", 200)]


# ── Item extractors ───────────────────────────────────────────────────────────

def extract_items(page_key: str, data: CharacterData) -> list[PanelItem]:
    """Convert CharacterData into a list of PanelItems for the given page."""
    if page_key == "char_info":         return _extract_char_info(data)
    if page_key == "attributes":        return _extract_attributes(data)
    if page_key == "skills":            return _extract_skills(data)
    if page_key == "factions":          return _extract_factions(data)
    if page_key == "details":           return _extract_details(data)
    if page_key in _INV_FILTERS:        return _extract_inventory(data, _INV_FILTERS[page_key])
    if page_key in _SPELL_RANGES:       return _extract_spells(data, _SPELL_RANGES[page_key])
    if page_key == "magic_active_effects": return _extract_active_effects(data)
    if page_key == "active_quests":     return _extract_active_quests(data)
    if page_key == "completed_quests":  return _extract_completed_quests(data)
    if page_key == "globals":           return _extract_globals(data)
    if page_key == "game_time":         return _extract_game_time(data)
    if page_key == "plugins":           return _extract_plugins(data)
    if page_key == "world_state":       return _extract_world_state(data)
    return []


# ── Individual extractors ─────────────────────────────────────────────────────

def _extract_char_info(d: CharacterData) -> list[PanelItem]:
    c = d.character
    a = d.appearance
    fields = [
        ("name",      "Name",      c.name),
        ("race",      "Race",      c.race),
        ("class_name","Class",     c.class_name),
        ("birthsign", "Birthsign", c.birthsign),
        ("level",     "Level",     c.level),
        ("sex",       "Sex",       c.sex),
    ]
    # Appearance fields (only if data present)
    if a.hair or a.eyes:
        fields += [
            ("hair",               "Hair",               a.hair),
            ("eyes",               "Eyes",               a.eyes),
            ("hair_color",         "Hair Color",         a.hair_color),
            ("hair_length",        "Hair Length",        a.hair_length),
            ("facegen_geometry",   "FaceGen Geometry",   a.facegen_geometry),
            ("facegen_asymmetry",  "FaceGen Asymmetry",  a.facegen_asymmetry),
            ("facegen_texture",    "FaceGen Texture",    a.facegen_texture),
            ("facegen_geometry2",  "FaceGen Geometry 2", a.facegen_geometry2),
            ("facegen_asymmetry2", "FaceGen Asymmetry 2",a.facegen_asymmetry2),
            ("facegen_texture2",   "FaceGen Texture 2",  a.facegen_texture2),
        ]
    return [
        PanelItem(uid=f"ci.{k}", values={"field": label, "value": str(v)})
        for k, label, v in fields
    ]


def _extract_attributes(d: CharacterData) -> list[PanelItem]:
    items = []
    for attr in ATTRIBUTE_NAMES:
        base = d.attributes.get(attr, 0)
        current = d.skills_current.get(attr, base)  # skills_current may hold attr info too
        items.append(PanelItem(
            uid=f"attr.{attr}",
            values={"name": attr, "base": str(base), "current": str(current)},
        ))
    return items


def _extract_skills(d: CharacterData) -> list[PanelItem]:
    items = []
    for skill in SKILL_NAMES:
        base    = d.skills.get(skill, 0)
        current = d.skills_current.get(skill, base)
        display = get_skill_display_name(skill)
        items.append(PanelItem(
            uid=f"skill.{skill}",
            values={"name": display, "base": str(base), "current": str(current)},
        ))
    return items


def _extract_factions(d: CharacterData) -> list[PanelItem]:
    return [
        PanelItem(
            uid=f"faction.{f.form_id}",
            values={
                "name": f.name, "rank": str(f.rank),
                "title": f.title, "form_id": f.form_id,
            },
            source=f,
        )
        for f in d.factions
    ]


def _extract_details(d: CharacterData) -> list[PanelItem]:
    items: list[PanelItem] = []

    def add(uid_suffix, category, field_name, value):
        items.append(PanelItem(
            uid=f"detail.{uid_suffix}",
            values={"category": category, "field": field_name, "value": str(value)},
        ))

    v = d.vitals
    add("health_cur",   "Vitals", "Health Current",  v.health_current)
    add("health_base",  "Vitals", "Health Base",     v.health_base)
    add("magicka_cur",  "Vitals", "Magicka Current", v.magicka_current)
    add("magicka_base", "Vitals", "Magicka Base",    v.magicka_base)
    add("fatigue_cur",  "Vitals", "Fatigue Current", v.fatigue_current)
    add("fatigue_base", "Vitals", "Fatigue Base",    v.fatigue_base)
    add("encumbrance",  "Vitals", "Encumbrance",     v.encumbrance)

    add("fame",   "Reputation", "Fame",   d.fame)
    add("infamy", "Reputation", "Infamy", d.infamy)
    add("bounty", "Reputation", "Bounty", d.bounty)

    r = d.magic_resistances
    for key, label, val in [
        ("res_fire",    "Fire Resist",           r.fire),
        ("res_frost",   "Frost Resist",          r.frost),
        ("res_shock",   "Shock Resist",          r.shock),
        ("res_magic",   "Magic Resist",          r.magic),
        ("res_disease", "Disease Resist",        r.disease),
        ("res_poison",  "Poison Resist",         r.poison),
        ("res_para",    "Paralysis Resist",      r.paralysis),
        ("res_normal",  "Normal Weapons Resist", r.normal_weapons),
    ]:
        add(key, "Resistances", label, val)

    for idx, name in sorted(PCMISCSTAT_NAMES.items()):
        val = d.pc_misc_stats.get(idx, 0)
        add(f"misc_{idx}", "Misc Stats", name, val)

    return items


def _extract_inventory(d: CharacterData, type_filter) -> list[PanelItem]:
    items = []
    for inv in d.items:
        if type_filter and inv.item_type not in type_filter:
            continue
        cond_cur = "" if inv.condition_current < 0 else str(int(inv.condition_current))
        cond_max = "" if inv.condition_max    < 0 else str(int(inv.condition_max))
        chrg_cur = "" if inv.enchant_current  < 0 else str(int(inv.enchant_current))
        chrg_max = "" if inv.enchant_max      < 0 else str(int(inv.enchant_max))
        items.append(PanelItem(
            uid=f"inv.{inv.form_id}",
            values={
                "name":     inv.name,
                "type":     inv.item_type,
                "qty":      str(inv.quantity),
                "cond_cur": cond_cur,
                "cond_max": cond_max,
                "chrg_cur": chrg_cur,
                "chrg_max": chrg_max,
                "equipped": "Yes" if inv.equipped else "",
                "form_id":  inv.form_id,
            },
            source=inv,
        ))
    return items


def _extract_spells(d: CharacterData, range_filter) -> list[PanelItem]:
    items = []
    for spell in d.spells:
        if range_filter:
            if not any(e.range == range_filter for e in spell.effects):
                continue
        eff_parts = [
            f"{e.name}({e.magnitude}/{e.duration}/{e.area})"
            for e in spell.effects[:3]
        ]
        if len(spell.effects) > 3:
            eff_parts.append(f"+{len(spell.effects) - 3}")
        items.append(PanelItem(
            uid=f"spell.{spell.form_id}",
            values={
                "name":       spell.name,
                "spell_type": spell.spell_type,
                "cost":       str(spell.magicka_cost),
                "effects":    ", ".join(eff_parts),
                "form_id":    spell.form_id,
            },
            source=spell,
        ))
    return items


def _extract_active_effects(d: CharacterData) -> list[PanelItem]:
    return [
        PanelItem(
            uid=f"ame.{i}.{e.source_form_id}.{e.effect_code}",
            values={
                "effect":    e.effect_code,
                "magnitude": str(e.magnitude),
                "duration":  str(e.duration),
                "state":     e.state,
                "source":    e.source_name,
            },
            source=e,
        )
        for i, e in enumerate(d.active_magic_effects)
    ]


def _extract_active_quests(d: CharacterData) -> list[PanelItem]:
    return [
        PanelItem(
            uid=f"aq.{q.form_id or q.editor_id}",
            values={
                "name":      q.name or q.editor_id,
                "stage":     str(q.stage),
                "editor_id": q.editor_id,
                "flags":     q.flags,
                "form_id":   q.form_id,
            },
            source=q,
        )
        for q in d.current_quests
    ]


def _extract_completed_quests(d: CharacterData) -> list[PanelItem]:
    return [
        PanelItem(
            uid=f"cq.{q.form_id or q.editor_id}",
            values={
                "name":        q.name or q.editor_id,
                "editor_id":   q.editor_id,
                "final_stage": str(q.final_stage),
                "form_id":     q.form_id,
            },
            source=q,
        )
        for q in d.completed_quests_enriched
    ]


def _extract_globals(d: CharacterData) -> list[PanelItem]:
    return [
        PanelItem(
            uid=f"gv.{g.form_id}",
            values={
                "name":     g.name,
                "value":    str(g.value),
                "var_type": g.var_type,
                "form_id":  g.form_id,
            },
            source=g,
        )
        for g in d.global_variables
    ]


def _extract_game_time(d: CharacterData) -> list[PanelItem]:
    gt = d.game_time
    fields = [
        ("days_passed", "Days Passed", gt.days_passed),
        ("game_year",   "Year",        gt.game_year),
        ("game_month",  "Month",       gt.game_month),
        ("game_day",    "Day",         gt.game_day),
        ("game_hour",   "Hour",        gt.game_hour),
    ]
    return [
        PanelItem(uid=f"gt.{k}", values={"field": label, "value": str(v)})
        for k, label, v in fields
    ]


def _extract_plugins(d: CharacterData) -> list[PanelItem]:
    return [
        PanelItem(uid=f"plugin.{i}", values={"name": p, "index": str(i)})
        for i, p in enumerate(d.plugins)
    ]


def _extract_world_state(d: CharacterData) -> list[PanelItem]:
    items = []
    pos = d.player_position
    for k, label, val in [
        ("x",       "X",           pos.x),
        ("y",       "Y",           pos.y),
        ("z",       "Z",           pos.z),
        ("rot_x",   "Rot X",       pos.rot_x),
        ("rot_y",   "Rot Y",       pos.rot_y),
        ("rot_z",   "Rot Z",       pos.rot_z),
        ("scale",   "Scale",       pos.scale),
        ("cell",    "Cell",        pos.parent_cell),
        ("cell_fid","Cell FormID", pos.parent_cell_form_id),
    ]:
        items.append(PanelItem(
            uid=f"ws.{k}",
            values={"category": "Position", "field": label, "value": str(val)},
        ))
    w = d.weather
    for k, label, val in [
        ("weather",     "Weather",        w.current_weather),
        ("weather_fid", "Weather FormID", w.current_weather_form_id),
        ("climate_fid", "Climate FormID", w.climate_form_id),
    ]:
        items.append(PanelItem(
            uid=f"ws.{k}",
            values={"category": "Weather", "field": label, "value": str(val)},
        ))
    return items


# ── Staged filter ─────────────────────────────────────────────────────────────

@dataclass
class StagedFilter:
    """Tells SaveDumpWriter which items/sections to include in the output."""
    inventory_ids:     set = field(default_factory=set)
    spell_ids:         set = field(default_factory=set)
    attribute_names:   set = field(default_factory=set)
    skill_names:       set = field(default_factory=set)
    faction_ids:       set = field(default_factory=set)
    global_ids:        set = field(default_factory=set)
    active_quest_ids:  set = field(default_factory=set)   # form_ids
    plugin_indices:    set = field(default_factory=set)
    appearance_fields: set = field(default_factory=set)   # e.g. {"eyes", "hair"}

    include_char_info:        bool = False
    include_details:          bool = False
    include_game_time:        bool = False
    include_active_effects:   bool = False
    include_world_state:      bool = False
    include_completed_quests: bool = False


def build_staged_filter(panels: dict, char_data: CharacterData) -> StagedFilter:
    """
    Collect staged items from all panels, apply inline edits to source objects,
    update char_data with staged items, and return a StagedFilter for the writer.
    """
    sf = StagedFilter()

    # ── char_info ─────────────────────────────────────────────────────────
    _BASIC_CHAR_KEYS = {"name", "race", "class_name", "birthsign", "level", "sex"}
    staged_ci = panels.get("char_info", None)
    if staged_ci:
        items = staged_ci.get_staged_items()
        if items:
            for pi in items:
                key = pi.uid[3:]   # strip "ci."
                val = pi.values.get("value", "")
                if key in _BASIC_CHAR_KEYS:
                    sf.include_char_info = True
                    if key == "name":          char_data.character.name       = val
                    elif key == "race":        char_data.character.race       = val
                    elif key == "class_name":  char_data.character.class_name = val
                    elif key == "birthsign":   char_data.character.birthsign  = val
                    elif key == "level":
                        try: char_data.character.level = int(val)
                        except ValueError: pass
                    elif key == "sex":         char_data.character.sex = val
                elif hasattr(char_data.appearance, key):
                    sf.appearance_fields.add(key)
                    setattr(char_data.appearance, key, val)

    # ── attributes ────────────────────────────────────────────────────────
    if "attributes" in panels:
        staged = panels["attributes"].get_staged_items()
        if staged:
            char_data.attributes = {}
            for pi in staged:
                name = pi.uid[5:]   # strip "attr."
                sf.attribute_names.add(name)
                try: char_data.attributes[name] = int(pi.values.get("base", 0))
                except (ValueError, TypeError): pass
                try: char_data.skills_current[name] = int(pi.values.get("current", pi.values.get("base", 0)))
                except (ValueError, TypeError): pass

    # ── skills ────────────────────────────────────────────────────────────
    if "skills" in panels:
        staged = panels["skills"].get_staged_items()
        if staged:
            char_data.skills = {}
            for pi in staged:
                storage_name = pi.uid[6:]   # strip "skill."
                sf.skill_names.add(storage_name)
                try: char_data.skills[storage_name] = int(pi.values.get("base", 0))
                except (ValueError, TypeError): pass
                try: char_data.skills_current[storage_name] = int(pi.values.get("current", pi.values.get("base", 0)))
                except (ValueError, TypeError): pass

    # ── factions ──────────────────────────────────────────────────────────
    if "factions" in panels:
        staged = panels["factions"].get_staged_items()
        if staged:
            char_data.factions = []
            for pi in staged:
                if pi.source:
                    try: pi.source.rank = int(pi.values.get("rank", pi.source.rank))
                    except ValueError: pass
                    char_data.factions.append(pi.source)
                    sf.faction_ids.add(pi.source.form_id)

    # ── details (vitals, resistances, misc stats, fame) ───────────────────
    if "details" in panels:
        staged = panels["details"].get_staged_items()
        if staged:
            sf.include_details = True
            for pi in staged:
                key = pi.uid[7:]   # strip "detail."
                try:
                    val_f = float(pi.values.get("value", 0))
                    val_i = int(val_f)
                except (ValueError, TypeError):
                    continue
                v = char_data.vitals
                r = char_data.magic_resistances
                mapping = {
                    "health_cur":   lambda: setattr(v, "health_current",  val_f),
                    "health_base":  lambda: setattr(v, "health_base",     val_f),
                    "magicka_cur":  lambda: setattr(v, "magicka_current", val_f),
                    "magicka_base": lambda: setattr(v, "magicka_base",    val_f),
                    "fatigue_cur":  lambda: setattr(v, "fatigue_current", val_f),
                    "fatigue_base": lambda: setattr(v, "fatigue_base",    val_f),
                    "encumbrance":  lambda: setattr(v, "encumbrance",     val_f),
                    "fame":         lambda: setattr(char_data, "fame",    val_i),
                    "infamy":       lambda: setattr(char_data, "infamy",  val_i),
                    "bounty":       lambda: setattr(char_data, "bounty",  val_i),
                    "res_fire":     lambda: setattr(r, "fire",            val_f),
                    "res_frost":    lambda: setattr(r, "frost",           val_f),
                    "res_shock":    lambda: setattr(r, "shock",           val_f),
                    "res_magic":    lambda: setattr(r, "magic",           val_f),
                    "res_disease":  lambda: setattr(r, "disease",         val_f),
                    "res_poison":   lambda: setattr(r, "poison",          val_f),
                    "res_para":     lambda: setattr(r, "paralysis",       val_f),
                    "res_normal":   lambda: setattr(r, "normal_weapons",  val_f),
                }
                if key in mapping:
                    mapping[key]()
                elif key.startswith("misc_"):
                    try:
                        idx = int(key[5:])
                        char_data.pc_misc_stats[idx] = val_i
                    except ValueError:
                        pass

    # ── inventory (collect from all 5 pages, dedup by form_id) ────────────
    seen_inv: dict[str, PanelItem] = {}
    for page_key in ("weapons", "gear", "alchemy_inv", "miscellaneous", "all_items"):
        if page_key in panels:
            for pi in panels[page_key].get_staged_items():
                fid = pi.values.get("form_id", "")
                if fid and fid not in seen_inv:
                    seen_inv[fid] = pi
    if seen_inv:
        char_data.items = []
        for fid, pi in seen_inv.items():
            sf.inventory_ids.add(fid)
            if pi.source:
                try: pi.source.quantity = int(pi.values.get("qty", pi.source.quantity))
                except ValueError: pass
                for src_attr, key, default in [
                    ("condition_current", "cond_cur", -1),
                    ("condition_max",     "cond_max", -1),
                    ("enchant_current",   "chrg_cur", -1),
                    ("enchant_max",       "chrg_max", -1),
                ]:
                    raw = pi.values.get(key, "")
                    if raw:
                        try: setattr(pi.source, src_attr, float(raw))
                        except ValueError: pass
                char_data.items.append(pi.source)

    # ── spells (collect from all 4 pages, dedup by form_id) ───────────────
    seen_spells: dict[str, PanelItem] = {}
    for page_key in ("spell_self", "spell_touch", "spell_target", "spell_all"):
        if page_key in panels:
            for pi in panels[page_key].get_staged_items():
                fid = pi.values.get("form_id", "")
                if fid and fid not in seen_spells:
                    seen_spells[fid] = pi
    if seen_spells:
        char_data.spells = []
        for fid, pi in seen_spells.items():
            sf.spell_ids.add(fid)
            if pi.source:
                try: pi.source.magicka_cost = int(pi.values.get("cost", pi.source.magicka_cost))
                except ValueError: pass
                char_data.spells.append(pi.source)

    # ── active magic effects ───────────────────────────────────────────────
    if "magic_active_effects" in panels:
        staged = panels["magic_active_effects"].get_staged_items()
        if staged:
            sf.include_active_effects = True
            char_data.active_magic_effects = [pi.source for pi in staged if pi.source]

    # ── active quests ─────────────────────────────────────────────────────
    if "active_quests" in panels:
        staged = panels["active_quests"].get_staged_items()
        if staged:
            char_data.current_quests = []
            for pi in staged:
                if pi.source:
                    try: pi.source.stage = int(pi.values.get("stage", pi.source.stage))
                    except ValueError: pass
                    char_data.current_quests.append(pi.source)
                    sf.active_quest_ids.add(pi.source.form_id)

    # ── completed quests ──────────────────────────────────────────────────
    if "completed_quests" in panels:
        staged = panels["completed_quests"].get_staged_items()
        if staged:
            sf.include_completed_quests = True
            char_data.completed_quests_enriched = [pi.source for pi in staged if pi.source]

    # ── globals ───────────────────────────────────────────────────────────
    if "globals" in panels:
        staged = panels["globals"].get_staged_items()
        if staged:
            char_data.global_variables = []
            for pi in staged:
                if pi.source:
                    sf.global_ids.add(pi.source.form_id)
                    try: pi.source.value = float(pi.values.get("value", pi.source.value))
                    except ValueError: pass
                    char_data.global_variables.append(pi.source)

    # ── game time ─────────────────────────────────────────────────────────
    if "game_time" in panels:
        staged = panels["game_time"].get_staged_items()
        if staged:
            sf.include_game_time = True
            for pi in staged:
                key = pi.uid[3:]   # strip "gt."
                try:
                    val = float(pi.values.get("value", 0))
                    gt = char_data.game_time
                    if key == "days_passed": gt.days_passed = val
                    elif key == "game_year":  gt.game_year  = int(val)
                    elif key == "game_month": gt.game_month = int(val)
                    elif key == "game_day":   gt.game_day   = int(val)
                    elif key == "game_hour":  gt.game_hour  = val
                except ValueError:
                    pass

    # ── plugins ───────────────────────────────────────────────────────────
    if "plugins" in panels:
        staged = panels["plugins"].get_staged_items()
        if staged:
            for pi in staged:
                try: sf.plugin_indices.add(int(pi.values.get("index", -1)))
                except ValueError: pass

    # ── world state ───────────────────────────────────────────────────────
    if "world_state" in panels:
        staged = panels["world_state"].get_staged_items()
        if staged:
            sf.include_world_state = True
            pos = char_data.player_position
            w   = char_data.weather
            for pi in staged:
                key = pi.uid[3:]   # strip "ws."
                try:
                    val_s = pi.values.get("value", "")
                    val_f = float(val_s)
                    if key == "x":       pos.x = val_f
                    elif key == "y":     pos.y = val_f
                    elif key == "z":     pos.z = val_f
                    elif key == "rot_x": pos.rot_x = val_f
                    elif key == "rot_y": pos.rot_y = val_f
                    elif key == "rot_z": pos.rot_z = val_f
                    elif key == "scale": pos.scale = val_f
                except ValueError:
                    if key == "cell":       pos.parent_cell          = pi.values.get("value", "")
                    elif key == "cell_fid": pos.parent_cell_form_id  = pi.values.get("value", "")
                    elif key == "weather":  w.current_weather        = pi.values.get("value", "")

    return sf
