"""Persistent settings for Varla-HUD, stored in ~/.varla_hud_settings.json."""

import json
from pathlib import Path

_SETTINGS_PATH = Path.home() / ".varla_hud_settings.json"

_defaults = {
    "default_dump_path": "",            # legacy / auto
    "default_dump_path_classic": "",    # xOBSE
    "default_dump_path_remastered": "", # obse64
    "game_format": "auto",   # "auto" | "remastered" | "classic"
    "skip_import_filter": False,
    "language": "en",
}

_data: dict = {}


def load() -> None:
    global _data
    if _SETTINGS_PATH.exists():
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                _data = json.load(f)
        except Exception:
            _data = {}
    _data = {**_defaults, **_data}


def save() -> None:
    try:
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(_data, f, indent=2)
    except Exception:
        pass


def get(key: str):
    if not _data:
        load()
    return _data.get(key, _defaults.get(key))


def set(key: str, value) -> None:
    if not _data:
        load()
    _data[key] = value
    save()
