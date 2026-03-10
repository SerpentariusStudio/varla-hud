"""Data manager for handling data.json persistence."""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models import AppData, Preset


class DataManager:
    """Manages loading and saving application data to/from data.json."""

    def __init__(self, data_file_path: str = "data.json"):
        self.data_file_path = Path(data_file_path)
        self.app_data: AppData = AppData()

    def load(self) -> AppData:
        """Load data from data.json file."""
        if not self.data_file_path.exists():
            # Create default data file
            self.app_data = AppData()
            self.save()
            return self.app_data

        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)

            self.app_data = AppData.from_dict(data_dict)
            return self.app_data

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading data.json: {e}")
            # Return default data on error
            self.app_data = AppData()
            return self.app_data

    def save(self):
        """Save current app data to data.json file."""
        try:
            # Ensure parent directory exists
            self.data_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.app_data.to_dict(), f, indent=2, ensure_ascii=False)

        except (IOError, OSError) as e:
            raise IOError(f"Failed to save data.json: {e}")

    def get_current_preset(self) -> Optional[Preset]:
        """Get the currently active preset."""
        current_name = self.app_data.settings.get("currentPreset")

        if current_name and current_name in self.app_data.presets:
            return self.app_data.presets[current_name]

        # No current preset set, try to get most recent
        return self.app_data.get_most_recent_preset()

    def set_current_preset(self, preset_name: str):
        """Set the currently active preset."""
        if preset_name in self.app_data.presets:
            self.app_data.settings["currentPreset"] = preset_name
            # Update last used timestamp
            self.app_data.presets[preset_name].last_used = datetime.now().isoformat()
            self.save()

    def create_preset(self, preset_name: str, preset: Preset) -> bool:
        """
        Create a new preset.

        Returns:
            True if created successfully, False if name already exists
        """
        if preset_name in self.app_data.presets:
            return False

        self.app_data.presets[preset_name] = preset
        self.set_current_preset(preset_name)
        return True

    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """
        Rename a preset.

        Returns:
            True if renamed successfully, False if old name doesn't exist or new name already exists
        """
        if old_name not in self.app_data.presets or new_name in self.app_data.presets:
            return False

        preset = self.app_data.presets.pop(old_name)
        preset.name = new_name
        self.app_data.presets[new_name] = preset

        # Update current preset if it was the renamed one
        if self.app_data.settings.get("currentPreset") == old_name:
            self.app_data.settings["currentPreset"] = new_name

        self.save()
        return True

    def delete_preset(self, preset_name: str) -> bool:
        """
        Delete a preset.

        Returns:
            True if deleted successfully, False if preset doesn't exist
        """
        if preset_name not in self.app_data.presets:
            return False

        del self.app_data.presets[preset_name]

        # If this was the current preset, clear it
        if self.app_data.settings.get("currentPreset") == preset_name:
            # Try to set to most recent preset
            most_recent = self.app_data.get_most_recent_preset()
            if most_recent:
                self.app_data.settings["currentPreset"] = most_recent.name
            else:
                self.app_data.settings["currentPreset"] = None

        self.save()
        return True

    def duplicate_preset(self, preset_name: str, new_name: str) -> bool:
        """
        Duplicate a preset with a new name.

        Returns:
            True if duplicated successfully, False if source doesn't exist or new name already exists
        """
        if preset_name not in self.app_data.presets or new_name in self.app_data.presets:
            return False

        source_preset = self.app_data.presets[preset_name]

        # Create a deep copy including extended fields
        extended = source_preset.deep_copy_extended()
        new_preset = Preset(
            name=new_name,
            last_used=datetime.now().isoformat(),
            favorites=source_preset.favorites.copy(),
            exceptions=source_preset.exceptions.copy(),
            items=[item.copy() for item in source_preset.items],
            spells=[spell.copy() for spell in source_preset.spells],
            **extended
        )

        self.app_data.presets[new_name] = new_preset
        self.save()
        return True

    def get_export_log_path(self) -> str:
        """Get the export log path from settings."""
        default = os.path.join(
            os.path.expanduser("~"),
            "Documents", "My Games", "Oblivion", "OBSE", "save_dump.txt"
        )
        return self.app_data.settings.get("exportLogPath", default)

    def set_export_log_path(self, path: str):
        """Set the export log path."""
        self.app_data.settings["exportLogPath"] = path
        self.save()

    def get_import_log_path(self) -> str:
        """Get the import log path from settings."""
        return self.app_data.settings.get(
            "importLogPath",
            r"C:\Steam\steamapps\common\Oblivion\Data\ConScribe Logs\Per-Mod\varla-test.log"
        )

    def set_import_log_path(self, path: str):
        """Set the import log path."""
        self.app_data.settings["importLogPath"] = path
        self.save()

    def get_save_dump_path(self) -> str:
        """Get the save dump path from settings."""
        default = os.path.join(
            os.path.expanduser("~"),
            "Documents", "My Games", "Oblivion Remastered", "OBSE", "save_dump.txt"
        )
        return self.app_data.settings.get("saveDumpPath", default)

    def set_save_dump_path(self, path: str):
        """Set the save dump path."""
        self.app_data.settings["saveDumpPath"] = path
        self.save()
