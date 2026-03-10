"""
Load Order Manager for Oblivion Character Data Import Manager
Handles parsing Wrye Bash load order files and remapping form IDs
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QComboBox, QGroupBox, QTextEdit, QSplitter,
    QTabWidget, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from theme import COLORS, get_qcolor


def parse_load_order_file(file_path: Path) -> Dict[str, int]:
    """
    Parse a Wrye Bash load order export file.

    Args:
        file_path: Path to the load order file

    Returns:
        Dictionary mapping mod names to their hex indices

    Example:
        {
            "Oblivion.esm": 0x00,
            "Unofficial Oblivion Patch.esp": 0x01,
            "DLCShiveringIsles.esp": 0x03,
            ...
        }
    """
    load_order = {}
    index = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Only process lines with asterisk (active mods)
            if line.startswith('*'):
                mod_name = line[1:].strip()  # Remove asterisk
                load_order[mod_name] = index
                index += 1

    return load_order


def get_mod_prefix_from_index(index: int) -> str:
    """Convert mod index to hex prefix (e.g., 0 -> "00", 7 -> "07", 15 -> "0F")."""
    return f"{index:02X}"


def get_index_from_form_id(form_id: str) -> str:
    """Extract the mod index prefix from a form ID (first 2 characters)."""
    if len(form_id) >= 2:
        return form_id[:2].upper()
    return "00"


def remap_form_id(form_id: str, old_index: str, new_index: str) -> str:
    """
    Remap a form ID from one mod index to another.

    Args:
        form_id: The original form ID (e.g., "07004B9B")
        old_index: The old mod index (e.g., "07")
        new_index: The new mod index (e.g., "0C")

    Returns:
        The remapped form ID (e.g., "0C004B9B")
    """
    if len(form_id) >= 8 and form_id[:2].upper() == old_index.upper():
        return new_index.upper() + form_id[2:]
    return form_id


class LoadOrderManagerDialog(QDialog):
    """Dialog for managing load order and remapping form IDs."""

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.load_order = {}
        self.mod_mapping = {}  # Maps old hex -> new hex

        self.init_ui()

    def init_ui(self):
        """Initialize the UI."""
        self.setWindowTitle("Load Order Manager")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header = QLabel("Load Order Manager - Remap Form IDs to Current Load Order")
        header.setStyleSheet(f"font-size: 14pt; font-weight: bold; padding: 10px; color: {COLORS['accent_gold']};")
        layout.addWidget(header)

        # Instructions
        instructions = QLabel(
            "This tool helps you fix 'broken load order' issues where items/spells have outdated mod indices.\n"
            "1. Load your Wrye Bash exported load order file\n"
            "2. Review detected non-vanilla form IDs and their current mod assignments\n"
            "3. Select the correct mod for each form ID\n"
            "4. Apply changes to update all form IDs in your data"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"padding: 10px; background-color: {COLORS['lom_instruction_bg']}; border-radius: 5px; color: {COLORS['text_secondary']};")
        layout.addWidget(instructions)

        # Load order file selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Load Order File:"))
        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setObjectName("pathDisplay")
        file_layout.addWidget(self.file_path_label, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_load_order_file)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tab 1: Load Order Overview
        self.create_load_order_tab()

        # Tab 2: Form ID Remapping
        self.create_remapping_tab()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_btn = QPushButton("Apply Remapping")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self.apply_remapping)
        self.apply_btn.setObjectName("generateBtn")
        button_layout.addWidget(self.apply_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def create_load_order_tab(self):
        """Create the load order overview tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        layout.addWidget(QLabel("Current Load Order (from file):"))

        self.load_order_table = QTableWidget()
        self.load_order_table.setColumnCount(3)
        self.load_order_table.setHorizontalHeaderLabels(["Hex Index", "Mod Name", "Type"])
        self.load_order_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.load_order_table)

        self.tab_widget.addTab(tab, "Load Order")

    def create_remapping_tab(self):
        """Create the form ID remapping tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        info = QLabel(
            "The table below shows all non-vanilla form IDs in your data (form IDs not starting with '00').\n"
            "Select the correct mod for each entry to remap the form IDs."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"padding: 5px; background-color: {COLORS['lom_info_bg']}; border-radius: 5px; color: {COLORS['text_secondary']};")
        layout.addWidget(info)

        self.remapping_table = QTableWidget()
        self.remapping_table.setColumnCount(6)
        self.remapping_table.setHorizontalHeaderLabels([
            "Current Form ID", "Name", "Type", "Current Mod Index", "New Mod", "New Form ID"
        ])
        self.remapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.remapping_table)

        self.tab_widget.addTab(tab, "Remap Form IDs")

    def browse_load_order_file(self):
        """Browse for a load order file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Wrye Bash Load Order File",
            str(Path.home() / "Downloads"),
            "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            self.load_load_order_file(Path(file_path))

    def load_load_order_file(self, file_path: Path):
        """Load and parse a load order file."""
        try:
            self.load_order = parse_load_order_file(file_path)
            self.file_path_label.setText(str(file_path))

            # Update load order table
            self.populate_load_order_table()

            # Update remapping table
            self.populate_remapping_table()

            self.apply_btn.setEnabled(True)

            QMessageBox.information(
                self,
                "Load Order Loaded",
                f"Successfully loaded {len(self.load_order)} mods from load order file."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load load order file:\n{str(e)}"
            )

    def populate_load_order_table(self):
        """Populate the load order overview table."""
        self.load_order_table.setRowCount(len(self.load_order))

        for row, (mod_name, index) in enumerate(sorted(self.load_order.items(), key=lambda x: x[1])):
            # Hex index
            hex_index = get_mod_prefix_from_index(index)
            index_item = QTableWidgetItem(hex_index)
            index_item.setTextAlignment(Qt.AlignCenter)
            if index == 0:
                index_item.setBackground(get_qcolor("lom_green_bg"))
            self.load_order_table.setItem(row, 0, index_item)

            # Mod name
            name_item = QTableWidgetItem(mod_name)
            self.load_order_table.setItem(row, 1, name_item)

            # Type
            mod_type = "Master" if mod_name.endswith('.esm') else "Plugin"
            type_item = QTableWidgetItem(mod_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.load_order_table.setItem(row, 2, type_item)

    def populate_remapping_table(self):
        """Populate the form ID remapping table."""
        # Collect all non-vanilla form IDs from the data
        non_vanilla_items = []

        # Get current preset data
        if self.data_manager.current_preset_name:
            preset_data = self.data_manager.presets.get(self.data_manager.current_preset_name, {})
        else:
            # Use the character_data directly
            preset_data = {}
            if hasattr(self.data_manager.character_data, 'items'):
                preset_data['items'] = [
                    {'formId': item.form_id, 'name': item.name, 'quantity': item.quantity}
                    for item in self.data_manager.character_data.items
                ]
            if hasattr(self.data_manager.character_data, 'spells'):
                preset_data['spells'] = [
                    {'formId': spell.form_id, 'name': spell.name, 'magickaCost': spell.magicka_cost}
                    for spell in self.data_manager.character_data.spells
                ]

        # Process items
        for item in preset_data.get('items', []):
            form_id = item.get('formId', '')
            if form_id and not form_id.startswith('00'):
                non_vanilla_items.append({
                    'form_id': form_id,
                    'name': item.get('name', 'Unknown'),
                    'type': 'Item'
                })

        # Process spells
        for spell in preset_data.get('spells', []):
            form_id = spell.get('formId', '')
            if form_id and not form_id.startswith('00'):
                non_vanilla_items.append({
                    'form_id': form_id,
                    'name': spell.get('name', 'Unknown'),
                    'type': 'Spell'
                })

        # Process favorites
        for form_id in preset_data.get('favorites', []):
            if form_id and not form_id.startswith('00'):
                # Check if already added
                if not any(item['form_id'] == form_id for item in non_vanilla_items):
                    non_vanilla_items.append({
                        'form_id': form_id,
                        'name': 'Favorited Item',
                        'type': 'Favorite'
                    })

        # Populate table
        self.remapping_table.setRowCount(len(non_vanilla_items))

        for row, item in enumerate(non_vanilla_items):
            form_id = item['form_id']
            mod_index = get_index_from_form_id(form_id)

            # Current Form ID
            form_id_item = QTableWidgetItem(form_id)
            form_id_item.setTextAlignment(Qt.AlignCenter)
            self.remapping_table.setItem(row, 0, form_id_item)

            # Name
            name_item = QTableWidgetItem(item['name'])
            self.remapping_table.setItem(row, 1, name_item)

            # Type
            type_item = QTableWidgetItem(item['type'])
            type_item.setTextAlignment(Qt.AlignCenter)
            self.remapping_table.setItem(row, 2, type_item)

            # Current Mod Index
            current_mod_item = QTableWidgetItem(mod_index)
            current_mod_item.setTextAlignment(Qt.AlignCenter)
            current_mod_item.setBackground(get_qcolor("lom_red_bg"))
            self.remapping_table.setItem(row, 3, current_mod_item)

            # New Mod (ComboBox)
            mod_combo = QComboBox()
            mod_combo.addItem("-- Keep Current --", mod_index)

            for mod_name, mod_idx in sorted(self.load_order.items(), key=lambda x: x[1]):
                hex_idx = get_mod_prefix_from_index(mod_idx)
                mod_combo.addItem(f"{hex_idx} - {mod_name}", hex_idx)

            mod_combo.currentIndexChanged.connect(lambda idx, r=row: self.update_new_form_id(r))
            self.remapping_table.setCellWidget(row, 4, mod_combo)

            # New Form ID (will be updated when combo changes)
            new_form_id_item = QTableWidgetItem(form_id)
            new_form_id_item.setTextAlignment(Qt.AlignCenter)
            new_form_id_item.setForeground(get_qcolor("lom_gray_fg"))
            self.remapping_table.setItem(row, 5, new_form_id_item)

    def update_new_form_id(self, row: int):
        """Update the new form ID preview when mod selection changes."""
        current_form_id = self.remapping_table.item(row, 0).text()
        mod_combo = self.remapping_table.cellWidget(row, 4)

        new_mod_index = mod_combo.currentData()
        old_mod_index = get_index_from_form_id(current_form_id)

        new_form_id = remap_form_id(current_form_id, old_mod_index, new_mod_index)

        new_form_id_item = self.remapping_table.item(row, 5)
        new_form_id_item.setText(new_form_id)

        # Color code: green if changed, gray if same
        if new_form_id != current_form_id:
            new_form_id_item.setBackground(get_qcolor("lom_green_bg"))
            new_form_id_item.setForeground(get_qcolor("lom_green_fg"))
        else:
            new_form_id_item.setBackground(get_qcolor("table_row_1"))
            new_form_id_item.setForeground(get_qcolor("lom_gray_fg"))

    def apply_remapping(self):
        """Apply the form ID remapping to the data."""
        # Build remapping dictionary
        remapping = {}

        for row in range(self.remapping_table.rowCount()):
            old_form_id = self.remapping_table.item(row, 0).text()
            new_form_id = self.remapping_table.item(row, 5).text()

            if old_form_id != new_form_id:
                remapping[old_form_id] = new_form_id

        if not remapping:
            QMessageBox.information(self, "No Changes", "No form IDs were changed.")
            return

        # Apply remapping to data
        changes_made = self.apply_remapping_to_data(remapping)

        # Also update in-memory favorites and exceptions
        self.apply_remapping_to_memory(remapping)

        # Save data
        self.data_manager.save_presets()

        # Reload the current preset to reflect changes in the UI
        if self.data_manager.current_preset_name:
            self.data_manager.load_preset_by_name(self.data_manager.current_preset_name)

        QMessageBox.information(
            self,
            "Remapping Applied",
            f"Successfully remapped {changes_made} form IDs.\n\n"
            "The changes have been saved and applied to the current session.\n"
            "All tables and views have been updated."
        )

        self.close()

    def apply_remapping_to_data(self, remapping: Dict[str, str]) -> int:
        """
        Apply form ID remapping to all data in data.json.

        Args:
            remapping: Dictionary mapping old form IDs to new form IDs

        Returns:
            Number of changes made
        """
        changes = 0

        # Apply to all presets
        for preset_name, preset_data in self.data_manager.presets.items():
            # Remap items
            if 'items' in preset_data:
                for item in preset_data['items']:
                    if item.get('formId') in remapping:
                        item['formId'] = remapping[item['formId']]
                        changes += 1

            # Remap spells
            if 'spells' in preset_data:
                for spell in preset_data['spells']:
                    if spell.get('formId') in remapping:
                        spell['formId'] = remapping[spell['formId']]
                        changes += 1

            # Remap spellsToRemove
            if 'spellsToRemove' in preset_data:
                for spell in preset_data['spellsToRemove']:
                    if spell.get('formId') in remapping:
                        spell['formId'] = remapping[spell['formId']]
                        changes += 1

            # Remap favorites
            if 'favorites' in preset_data:
                preset_data['favorites'] = [
                    remapping.get(fid, fid) for fid in preset_data['favorites']
                ]

            # Remap favoritesByCategory
            if 'favoritesByCategory' in preset_data:
                for category in ['items', 'spells']:
                    if category in preset_data['favoritesByCategory']:
                        preset_data['favoritesByCategory'][category] = [
                            remapping.get(fid, fid) for fid in preset_data['favoritesByCategory'][category]
                        ]

            # Remap exceptions
            if 'exceptions' in preset_data:
                preset_data['exceptions'] = [
                    remapping.get(fid, fid) for fid in preset_data['exceptions']
                ]

            # Remap exceptionsByCategory
            if 'exceptionsByCategory' in preset_data:
                for category in ['items', 'spells']:
                    if category in preset_data['exceptionsByCategory']:
                        preset_data['exceptionsByCategory'][category] = [
                            remapping.get(fid, fid) for fid in preset_data['exceptionsByCategory'][category]
                        ]

            # Remap bank items
            if 'bank' in preset_data and 'items' in preset_data['bank']:
                for item in preset_data['bank']['items']:
                    if item.get('formId') in remapping:
                        item['formId'] = remapping[item['formId']]
                        changes += 1

            # Remap bank spells
            if 'bank' in preset_data and 'spells' in preset_data['bank']:
                for spell in preset_data['bank']['spells']:
                    if spell.get('formId') in remapping:
                        spell['formId'] = remapping[spell['formId']]
                        changes += 1

        return changes

    def apply_remapping_to_memory(self, remapping: Dict[str, str]):
        """
        Apply form ID remapping to in-memory data structures.
        This ensures that when the user saves, the remapped IDs are used.

        Args:
            remapping: Dictionary mapping old form IDs to new form IDs
        """
        # Update in-memory favorites
        for category in ['items', 'spells', 'spells_to_remove']:
            if category in self.data_manager.favorites:
                self.data_manager.favorites[category] = {
                    remapping.get(fid, fid) for fid in self.data_manager.favorites[category]
                }

        # Update in-memory exceptions
        for category in ['items', 'spells', 'spells_to_remove']:
            if category in self.data_manager.exceptions:
                self.data_manager.exceptions[category] = {
                    remapping.get(fid, fid) for fid in self.data_manager.exceptions[category]
                }

        # Update in-memory bank
        if hasattr(self.data_manager, 'bank'):
            # Remap bank items
            new_bank_items = {}
            for form_id, item_data in self.data_manager.bank.get('items', {}).items():
                new_form_id = remapping.get(form_id, form_id)
                new_bank_items[new_form_id] = item_data
            if 'items' in self.data_manager.bank:
                self.data_manager.bank['items'] = new_bank_items

            # Remap bank spells
            new_bank_spells = {}
            for form_id, spell_data in self.data_manager.bank.get('spells', {}).items():
                new_form_id = remapping.get(form_id, form_id)
                new_bank_spells[new_form_id] = spell_data
            if 'spells' in self.data_manager.bank:
                self.data_manager.bank['spells'] = new_bank_spells

        # Update character_data if loaded
        if hasattr(self.data_manager.character_data, 'items'):
            for item in self.data_manager.character_data.items:
                if hasattr(item, 'form_id') and item.form_id in remapping:
                    item.form_id = remapping[item.form_id]

        if hasattr(self.data_manager.character_data, 'spells'):
            for spell in self.data_manager.character_data.spells:
                if hasattr(spell, 'form_id') and spell.form_id in remapping:
                    spell.form_id = remapping[spell.form_id]
