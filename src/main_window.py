"""Main application window for Oblivion Import Manager."""

import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QMenu, QInputDialog, QMessageBox, QToolBar, QHeaderView, QSpinBox,
    QFileDialog, QCheckBox, QDialog, QDialogButtonBox, QRadioButton,
    QButtonGroup, QComboBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from .models import Item, Spell, Preset, AppData
from .data_manager import DataManager
from .log_parser import parse_static_log, generate_import_log, generate_full_import_log
from .save_dump_parser import SaveDumpParser, ClassicSaveDumpParser, is_save_dump_format, is_classic_save_dump_format
from .character_models import (
    ATTRIBUTE_NAMES, SKILL_NAMES, PCMISCSTAT_NAMES,
    get_skill_display_name
)


class DragSelectCheckbox(QCheckBox):
    """Checkbox that supports drag-to-select functionality."""

    drag_state = None  # Class variable to track drag state across all checkboxes
    is_dragging = False  # Class variable to track if we're in drag mode
    all_checkboxes = []  # Keep track of all checkbox instances

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.already_processed = False  # Instance variable to prevent double-processing
        DragSelectCheckbox.all_checkboxes.append(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Set drag state to the opposite of current state
            DragSelectCheckbox.drag_state = not self.isChecked()
            DragSelectCheckbox.is_dragging = True
            self.setChecked(DragSelectCheckbox.drag_state)
            self.already_processed = True
            # Reset all other checkboxes' processed flags
            for cb in DragSelectCheckbox.all_checkboxes:
                if cb is not self:
                    cb.already_processed = False
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            DragSelectCheckbox.drag_state = None
            DragSelectCheckbox.is_dragging = False
            # Reset all checkboxes' processed state for next drag
            for cb in DragSelectCheckbox.all_checkboxes:
                cb.already_processed = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        # If we're dragging and mouse is over this checkbox, apply the drag state
        if DragSelectCheckbox.is_dragging and not self.already_processed:
            if self.rect().contains(event.pos()):
                self.setChecked(DragSelectCheckbox.drag_state)
                self.already_processed = True
        super().mouseMoveEvent(event)

    def enterEvent(self, event):
        # If dragging, apply the drag state
        if DragSelectCheckbox.is_dragging and not self.already_processed:
            self.setChecked(DragSelectCheckbox.drag_state)
            self.already_processed = True
        super().enterEvent(event)


class CheckboxCellWidget(QWidget):
    """Container widget for checkboxes that properly handles mouse events for drag selection."""

    def __init__(self, checkbox, parent=None):
        super().__init__(parent)
        self.checkbox = checkbox
        self.setMouseTracking(True)

        layout = QHBoxLayout()
        layout.addWidget(checkbox)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def mousePressEvent(self, event):
        # Forward to checkbox
        self.checkbox.mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # Forward to checkbox
        self.checkbox.mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        # Forward to checkbox
        self.checkbox.mouseMoveEvent(event)

    def enterEvent(self, event):
        # Trigger checkbox's enter event
        self.checkbox.enterEvent(event)
        super().enterEvent(event)


class StarWidget(QWidget):
    """Custom widget for favorite star icon."""

    clicked = Signal()

    def __init__(self, is_favorite: bool = False):
        super().__init__()
        self.is_favorite = is_favorite
        self.setFixedSize(30, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen, QBrush
        from PySide6.QtCore import QPointF
        import math

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Star points
        center_x, center_y = 15, 15
        outer_radius = 10
        inner_radius = 4
        num_points = 5

        points = []
        for i in range(num_points * 2):
            angle = math.pi / 2 + (i * math.pi / num_points)
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + radius * math.cos(angle)
            y = center_y - radius * math.sin(angle)
            points.append(QPointF(x, y))

        # Draw star
        if self.is_favorite:
            painter.setBrush(QBrush(QColor(255, 215, 0)))  # Gold
            painter.setPen(QPen(QColor(255, 215, 0), 2))
        else:
            painter.setBrush(QBrush(QColor(200, 200, 200)))  # Gray
            painter.setPen(QPen(QColor(150, 150, 150), 1))

        from PySide6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF(points))

    def toggle(self):
        """Toggle favorite state."""
        self.is_favorite = not self.is_favorite
        self.update()


class ExceptionIndicator(QWidget):
    """Widget showing exception status with triangle icon."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(30, 30)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF
        from PySide6.QtCore import QPointF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw triangle
        painter.setBrush(QBrush(QColor(144, 238, 144)))  # Pale green
        painter.setPen(QPen(QColor(100, 200, 100), 2))

        points = [
            QPointF(15, 5),   # Top
            QPointF(25, 23),  # Bottom right
            QPointF(5, 23)    # Bottom left
        ]
        painter.drawPolygon(QPolygonF(points))

        # Draw exclamation mark
        painter.setPen(QPen(QColor(50, 150, 50), 2))
        painter.drawLine(15, 10, 15, 17)  # Line
        painter.drawPoint(15, 20)  # Dot


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.data_manager = DataManager("data.json")
        self.data_manager.load()

        self.current_preset: Optional[Preset] = None
        self.current_items: List[Item] = []
        self.current_spells: List[Spell] = []

        self.exception_mode_active = False

        self.init_ui()
        self.load_initial_preset()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Oblivion Import Manager")
        self.setMinimumSize(1200, 800)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Main tabs: Main | Favorites | Exceptions | Presets
        self.main_tabs = QTabWidget()
        layout.addWidget(self.main_tabs)

        # Create tab contents
        self.main_view_widget = self.create_main_view()
        self.character_view_widget = self.create_character_view()
        self.favorites_view_widget = self.create_favorites_view()
        self.exceptions_view_widget = self.create_exceptions_view()
        self.presets_view_widget = self.create_presets_view()

        self.main_tabs.addTab(self.main_view_widget, "Main")
        self.main_tabs.addTab(self.character_view_widget, "Character")
        self.main_tabs.addTab(self.favorites_view_widget, "Favorites")
        self.main_tabs.addTab(self.exceptions_view_widget, "Exceptions")
        self.main_tabs.addTab(self.presets_view_widget, "Presets")

        # Status bar
        self.statusBar().showMessage("Ready")

    def create_menu_bar(self):
        """Create the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        change_export_action = QAction("Change Export Log Path", self)
        change_export_action.triggered.connect(self.change_export_log_path)
        file_menu.addAction(change_export_action)

        change_import_action = QAction("Change Import Log Path", self)
        change_import_action.triggered.connect(self.change_import_log_path)
        file_menu.addAction(change_import_action)

        change_save_dump_action = QAction("Change Save Dump Path", self)
        change_save_dump_action.triggered.connect(self.change_save_dump_path)
        file_menu.addAction(change_save_dump_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Preset menu
        preset_menu = menu_bar.addMenu("Preset")

        save_preset_action = QAction("Save as Preset", self)
        save_preset_action.triggered.connect(self.save_as_preset)
        preset_menu.addAction(save_preset_action)

        rename_preset_action = QAction("Rename Current Preset", self)
        rename_preset_action.triggered.connect(self.rename_current_preset)
        preset_menu.addAction(rename_preset_action)

        delete_preset_action = QAction("Delete Current Preset", self)
        delete_preset_action.triggered.connect(self.delete_current_preset)
        preset_menu.addAction(delete_preset_action)

        duplicate_preset_action = QAction("Duplicate Current Preset", self)
        duplicate_preset_action.triggered.connect(self.duplicate_current_preset)
        preset_menu.addAction(duplicate_preset_action)

        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")

        import_fav_exc_action = QAction("Import Favorites/Exceptions from Another Preset", self)
        import_fav_exc_action.triggered.connect(self.import_favorites_exceptions)
        tools_menu.addAction(import_fav_exc_action)

        generate_import_action = QAction("Generate Import Log", self)
        generate_import_action.triggered.connect(self.generate_import_log_file)
        tools_menu.addAction(generate_import_action)

    def create_toolbar(self):
        """Create the toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # Exception Mode toggle
        self.exception_mode_btn = QPushButton("Exception Mode: OFF")
        self.exception_mode_btn.setCheckable(True)
        self.exception_mode_btn.clicked.connect(self.toggle_exception_mode)
        toolbar.addWidget(self.exception_mode_btn)

        toolbar.addSeparator()

        # Current preset indicator
        toolbar.addWidget(QLabel("Current Preset: "))
        self.current_preset_label = QLabel("None")
        self.current_preset_label.setStyleSheet("font-weight: bold; padding: 5px;")
        toolbar.addWidget(self.current_preset_label)

    def create_main_view(self) -> QWidget:
        """Create the Main view (Items & Spells sub-tabs)."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Sub-tabs for Items and Spells
        self.main_subtabs = QTabWidget()
        layout.addWidget(self.main_subtabs)

        # Items tab
        items_widget = QWidget()
        items_layout = QVBoxLayout()
        items_widget.setLayout(items_layout)

        # Search and filter for items
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.items_search = QLineEdit()
        self.items_search.setPlaceholderText("Form ID, Name, Quantity, or Note")
        self.items_search.textChanged.connect(self.filter_items_table)
        search_layout.addWidget(self.items_search)

        self.items_favorites_only = QCheckBox("Show Favorites Only")
        self.items_favorites_only.stateChanged.connect(self.filter_items_table)
        search_layout.addWidget(self.items_favorites_only)

        self.items_hide_exceptions = QCheckBox("Hide Exceptions")
        self.items_hide_exceptions.stateChanged.connect(self.filter_items_table)
        search_layout.addWidget(self.items_hide_exceptions)

        items_add_btn = QPushButton("+")
        items_add_btn.setFixedWidth(40)
        items_add_btn.setToolTip("Add Item Manually")
        items_add_btn.clicked.connect(self.add_item_manually)
        search_layout.addWidget(items_add_btn)

        items_layout.addLayout(search_layout)

        # Items table
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["★", "⚠", "Form ID", "Name", "Quantity", "Notes"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.items_table.setColumnWidth(0, 40)
        self.items_table.setColumnWidth(1, 40)
        self.items_table.setColumnWidth(4, 100)
        self.items_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.items_table.customContextMenuRequested.connect(self.show_items_context_menu)
        self.items_table.cellClicked.connect(self.handle_items_cell_click)
        items_layout.addWidget(self.items_table)

        self.main_subtabs.addTab(items_widget, "Items")

        # Spells tab
        spells_widget = QWidget()
        spells_layout = QVBoxLayout()
        spells_widget.setLayout(spells_layout)

        # Search and filter for spells
        spell_search_layout = QHBoxLayout()
        spell_search_layout.addWidget(QLabel("Search:"))
        self.spells_search = QLineEdit()
        self.spells_search.setPlaceholderText("Form ID, Name, or Note")
        self.spells_search.textChanged.connect(self.filter_spells_table)
        spell_search_layout.addWidget(self.spells_search)

        self.spells_favorites_only = QCheckBox("Show Favorites Only")
        self.spells_favorites_only.stateChanged.connect(self.filter_spells_table)
        spell_search_layout.addWidget(self.spells_favorites_only)

        self.spells_hide_exceptions = QCheckBox("Hide Exceptions")
        self.spells_hide_exceptions.stateChanged.connect(self.filter_spells_table)
        spell_search_layout.addWidget(self.spells_hide_exceptions)

        spells_add_btn = QPushButton("+")
        spells_add_btn.setFixedWidth(40)
        spells_add_btn.setToolTip("Add Spell Manually")
        spells_add_btn.clicked.connect(self.add_spell_manually)
        spell_search_layout.addWidget(spells_add_btn)

        spells_layout.addLayout(spell_search_layout)

        # Spells table
        self.spells_table = QTableWidget()
        self.spells_table.setColumnCount(5)
        self.spells_table.setHorizontalHeaderLabels(["★", "⚠", "Form ID", "Name", "Notes"])
        self.spells_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.spells_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.spells_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.spells_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.spells_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.spells_table.setColumnWidth(0, 40)
        self.spells_table.setColumnWidth(1, 40)
        self.spells_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.spells_table.customContextMenuRequested.connect(self.show_spells_context_menu)
        self.spells_table.cellClicked.connect(self.handle_spells_cell_click)
        spells_layout.addWidget(self.spells_table)

        self.main_subtabs.addTab(spells_widget, "Spells")

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        load_export_btn = QPushButton("Load from Export Log")
        load_export_btn.clicked.connect(self.load_from_export_log)
        btn_layout.addWidget(load_export_btn)
        load_save_dump_btn = QPushButton("Load from Save Dump")
        load_save_dump_btn.clicked.connect(self.load_from_save_dump)
        btn_layout.addWidget(load_save_dump_btn)
        layout.addLayout(btn_layout)

        return widget

    def create_favorites_view(self) -> QWidget:
        """Create the Favorites view."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Header and search
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Favorites for Current Preset"))
        header_layout.addStretch()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.favorites_search = QLineEdit()
        self.favorites_search.setPlaceholderText("Form ID, Name, or Type")
        self.favorites_search.textChanged.connect(self.filter_favorites_table)
        search_layout.addWidget(self.favorites_search)

        layout.addLayout(header_layout)
        layout.addLayout(search_layout)

        # Favorites table
        self.favorites_table = QTableWidget()
        self.favorites_table.setColumnCount(4)
        self.favorites_table.setHorizontalHeaderLabels(["Form ID", "Name", "Type", "Notes"])
        self.favorites_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.favorites_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.favorites_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.favorites_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.favorites_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_table.customContextMenuRequested.connect(self.show_favorites_context_menu)
        self.favorites_table.cellDoubleClicked.connect(self.handle_favorites_double_click)
        layout.addWidget(self.favorites_table)

        # Info label
        info_label = QLabel("Double-click a favorite to add it to the main view")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)

        return widget

    def create_exceptions_view(self) -> QWidget:
        """Create the Exceptions view."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Header and search
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Exceptions for Current Preset"))
        header_layout.addStretch()

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.exceptions_search = QLineEdit()
        self.exceptions_search.setPlaceholderText("Form ID, Name, or Type")
        self.exceptions_search.textChanged.connect(self.filter_exceptions_table)
        search_layout.addWidget(self.exceptions_search)

        layout.addLayout(header_layout)
        layout.addLayout(search_layout)

        # Exceptions table
        self.exceptions_table = QTableWidget()
        self.exceptions_table.setColumnCount(3)
        self.exceptions_table.setHorizontalHeaderLabels(["Form ID", "Name", "Type (Item/Spell)"])
        self.exceptions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.exceptions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.exceptions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.exceptions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.exceptions_table.customContextMenuRequested.connect(self.show_exceptions_context_menu)
        layout.addWidget(self.exceptions_table)

        # Info label
        info_label = QLabel("Right-click to remove exceptions")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)

        return widget

    def create_presets_view(self) -> QWidget:
        """Create the Presets view."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("All Presets"))
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Presets table
        self.presets_table = QTableWidget()
        self.presets_table.setColumnCount(4)
        self.presets_table.setHorizontalHeaderLabels(["Preset Name", "Last Used", "Items", "Spells"])
        self.presets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.presets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.presets_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.presets_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.presets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.presets_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.presets_table.customContextMenuRequested.connect(self.show_presets_context_menu)
        self.presets_table.cellDoubleClicked.connect(self.handle_preset_double_click)
        layout.addWidget(self.presets_table)

        # Info label
        info_label = QLabel("Double-click a preset to load it | Right-click for options")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)

        return widget

    def create_character_view(self) -> QWidget:
        """Create the Character Info view."""
        from PySide6.QtWidgets import QScrollArea, QFormLayout, QGroupBox

        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Scroll area for all character content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)

        # Empty state message
        self.character_empty_label = QLabel("No character data — use 'Load from Save Dump' to populate")
        self.character_empty_label.setStyleSheet("color: gray; font-style: italic; font-size: 12pt; padding: 20px;")
        self.character_empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(self.character_empty_label)

        # Character Summary group
        char_group = QGroupBox("Character Summary")
        char_form = QFormLayout()
        char_group.setLayout(char_form)
        self.char_name_label = QLabel("-")
        self.char_race_label = QLabel("-")
        self.char_class_label = QLabel("-")
        self.char_birthsign_label = QLabel("-")
        self.char_level_label = QLabel("-")
        char_form.addRow("Name:", self.char_name_label)
        char_form.addRow("Race:", self.char_race_label)
        char_form.addRow("Class:", self.char_class_label)
        char_form.addRow("Birthsign:", self.char_birthsign_label)
        char_form.addRow("Level:", self.char_level_label)
        self.char_summary_group = char_group
        char_group.setVisible(False)
        scroll_layout.addWidget(char_group)

        # Vitals group
        vitals_group = QGroupBox("Vitals")
        vitals_form = QFormLayout()
        vitals_group.setLayout(vitals_form)
        self.vitals_health_label = QLabel("-")
        self.vitals_magicka_label = QLabel("-")
        self.vitals_fatigue_label = QLabel("-")
        vitals_form.addRow("Health:", self.vitals_health_label)
        vitals_form.addRow("Magicka:", self.vitals_magicka_label)
        vitals_form.addRow("Fatigue:", self.vitals_fatigue_label)
        self.vitals_group = vitals_group
        vitals_group.setVisible(False)
        scroll_layout.addWidget(vitals_group)

        # Attributes table
        attr_group = QGroupBox("Attributes")
        attr_layout = QVBoxLayout()
        attr_group.setLayout(attr_layout)
        self.attributes_table = QTableWidget()
        self.attributes_table.setColumnCount(2)
        self.attributes_table.setHorizontalHeaderLabels(["Attribute", "Value"])
        self.attributes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.attributes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.attributes_table.setMaximumHeight(280)
        attr_layout.addWidget(self.attributes_table)
        self.attr_group = attr_group
        attr_group.setVisible(False)
        scroll_layout.addWidget(attr_group)

        # Skills table
        skills_group = QGroupBox("Skills")
        skills_layout = QVBoxLayout()
        skills_group.setLayout(skills_layout)
        self.skills_table = QTableWidget()
        self.skills_table.setColumnCount(2)
        self.skills_table.setHorizontalHeaderLabels(["Skill", "Value"])
        self.skills_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.skills_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.skills_table.setMaximumHeight(600)
        skills_layout.addWidget(self.skills_table)
        self.skills_group = skills_group
        skills_group.setVisible(False)
        scroll_layout.addWidget(skills_group)

        # Statistics group
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)
        stats_form = QFormLayout()
        self.stats_fame_label = QLabel("-")
        self.stats_infamy_label = QLabel("-")
        self.stats_bounty_label = QLabel("-")
        stats_form.addRow("Fame:", self.stats_fame_label)
        stats_form.addRow("Infamy:", self.stats_infamy_label)
        stats_form.addRow("Bounty:", self.stats_bounty_label)
        stats_layout.addLayout(stats_form)
        self.misc_stats_table = QTableWidget()
        self.misc_stats_table.setColumnCount(2)
        self.misc_stats_table.setHorizontalHeaderLabels(["Statistic", "Value"])
        self.misc_stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.misc_stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.misc_stats_table.setMaximumHeight(400)
        stats_layout.addWidget(self.misc_stats_table)
        self.stats_group = stats_group
        stats_group.setVisible(False)
        scroll_layout.addWidget(stats_group)

        # Factions table
        factions_group = QGroupBox("Factions")
        factions_layout = QVBoxLayout()
        factions_group.setLayout(factions_layout)
        self.factions_table = QTableWidget()
        self.factions_table.setColumnCount(2)
        self.factions_table.setHorizontalHeaderLabels(["Name", "Rank"])
        self.factions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.factions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.factions_table.setMaximumHeight(200)
        factions_layout.addWidget(self.factions_table)
        self.factions_group = factions_group
        factions_group.setVisible(False)
        scroll_layout.addWidget(factions_group)

        # Quest summary
        quests_group = QGroupBox("Quests")
        quests_form = QFormLayout()
        quests_group.setLayout(quests_form)
        self.quest_active_label = QLabel("-")
        self.quest_completed_label = QLabel("-")
        self.quest_current_label = QLabel("-")
        quests_form.addRow("Active Quest:", self.quest_active_label)
        quests_form.addRow("Completed:", self.quest_completed_label)
        quests_form.addRow("In Progress:", self.quest_current_label)
        self.quests_group = quests_group
        quests_group.setVisible(False)
        scroll_layout.addWidget(quests_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        return widget

    def populate_character_info_tab(self):
        """Populate the Character tab from preset extended data."""
        preset = self.current_preset
        has_data = preset and preset.character is not None

        self.character_empty_label.setVisible(not has_data)
        for group in [self.char_summary_group, self.vitals_group, self.attr_group,
                       self.skills_group, self.stats_group, self.factions_group, self.quests_group]:
            group.setVisible(has_data)

        if not has_data:
            return

        # Character summary
        char = preset.character
        self.char_name_label.setText(str(char.get("name", "-")))
        self.char_race_label.setText(str(char.get("race", "-")))
        self.char_class_label.setText(str(char.get("class", "-")))
        self.char_birthsign_label.setText(str(char.get("birthsign", "-")))
        self.char_level_label.setText(str(char.get("level", "-")))

        # Vitals
        if preset.vitals:
            v = preset.vitals
            self.vitals_health_label.setText(str(int(v.get("healthBase", 0))))
            self.vitals_magicka_label.setText(str(int(v.get("magickaBase", 0))))
            self.vitals_fatigue_label.setText(str(int(v.get("fatigueBase", 0))))
            self.vitals_group.setVisible(True)
        else:
            self.vitals_group.setVisible(False)

        # Attributes
        if preset.attributes:
            self.attributes_table.setRowCount(0)
            for attr_name in ATTRIBUTE_NAMES:
                row = self.attributes_table.rowCount()
                self.attributes_table.insertRow(row)
                name_item = QTableWidgetItem(attr_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.attributes_table.setItem(row, 0, name_item)
                val_item = QTableWidgetItem(str(preset.attributes.get(attr_name, "-")))
                val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.attributes_table.setItem(row, 1, val_item)
            self.attr_group.setVisible(True)
        else:
            self.attr_group.setVisible(False)

        # Skills
        if preset.skills:
            self.skills_table.setRowCount(0)
            combat_skills = ["Armorer", "Athletics", "Blade", "Block", "Blunt", "HandToHand", "HeavyArmor"]
            magic_skills = ["Alchemy", "Alteration", "Conjuration", "Destruction", "Illusion", "Mysticism", "Restoration"]
            stealth_skills = ["Acrobatics", "LightArmor", "Marksman", "Mercantile", "Security", "Sneak", "Speechcraft"]

            for group_name, skill_list in [("Combat", combat_skills), ("Magic", magic_skills), ("Stealth", stealth_skills)]:
                # Group header
                row = self.skills_table.rowCount()
                self.skills_table.insertRow(row)
                header_item = QTableWidgetItem(f"--- {group_name} ---")
                header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                from PySide6.QtGui import QFont
                font = QFont()
                font.setBold(True)
                header_item.setFont(font)
                self.skills_table.setItem(row, 0, header_item)
                self.skills_table.setItem(row, 1, QTableWidgetItem(""))

                for skill_name in skill_list:
                    row = self.skills_table.rowCount()
                    self.skills_table.insertRow(row)
                    display_name = get_skill_display_name(skill_name)
                    name_item = QTableWidgetItem(display_name)
                    name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.skills_table.setItem(row, 0, name_item)
                    val_item = QTableWidgetItem(str(preset.skills.get(skill_name, "-")))
                    val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    self.skills_table.setItem(row, 1, val_item)
            self.skills_group.setVisible(True)
        else:
            self.skills_group.setVisible(False)

        # Statistics
        if preset.statistics:
            stats = preset.statistics
            self.stats_fame_label.setText(str(stats.get("fame", 0)))
            self.stats_infamy_label.setText(str(stats.get("infamy", 0)))
            self.stats_bounty_label.setText(str(stats.get("bounty", 0)))

            misc = stats.get("pcMiscStats", {})
            self.misc_stats_table.setRowCount(0)
            for idx_str, stat_name in sorted(PCMISCSTAT_NAMES.items()):
                row = self.misc_stats_table.rowCount()
                self.misc_stats_table.insertRow(row)
                name_item = QTableWidgetItem(stat_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.misc_stats_table.setItem(row, 0, name_item)
                val_item = QTableWidgetItem(str(misc.get(str(idx_str), 0)))
                val_item.setFlags(val_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.misc_stats_table.setItem(row, 1, val_item)
            self.stats_group.setVisible(True)
        else:
            self.stats_group.setVisible(False)

        # Factions
        if preset.factions:
            self.factions_table.setRowCount(0)
            for faction in preset.factions:
                row = self.factions_table.rowCount()
                self.factions_table.insertRow(row)
                name_item = QTableWidgetItem(faction.get("name", ""))
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.factions_table.setItem(row, 0, name_item)
                rank_item = QTableWidgetItem(str(faction.get("rank", 0)))
                rank_item.setFlags(rank_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.factions_table.setItem(row, 1, rank_item)
            self.factions_group.setVisible(True)
        else:
            self.factions_group.setVisible(False)

        # Quests
        if preset.active_quest or preset.quests or preset.current_quests:
            if preset.active_quest:
                aq = preset.active_quest
                self.quest_active_label.setText(f"{aq.get('editorId', '-')}")
            else:
                self.quest_active_label.setText("-")
            self.quest_completed_label.setText(str(len(preset.quests)) if preset.quests else "0")
            self.quest_current_label.setText(str(len(preset.current_quests)) if preset.current_quests else "0")
            self.quests_group.setVisible(True)
        else:
            self.quests_group.setVisible(False)

    def load_initial_preset(self):
        """Load the initial preset on startup."""
        preset = self.data_manager.get_current_preset()

        if preset:
            self.current_preset = preset
            self.current_items = preset.get_items()
            self.current_spells = preset.get_spells()
            self.current_preset_label.setText(preset.name)
            self.populate_items_table()
            self.populate_spells_table()
            self.populate_favorites_table()
            self.populate_exceptions_table()
            self.populate_presets_table()
            self.populate_character_info_tab()
            self.statusBar().showMessage(f"Loaded preset: {preset.name}")
        else:
            self.current_preset_label.setText("None")
            self.populate_presets_table()  # Still show available presets
            self.populate_character_info_tab()
            self.statusBar().showMessage("No preset loaded")

    def populate_items_table(self):
        """Populate the items table."""
        self.items_table.setRowCount(0)

        # Sort: favorites first
        sorted_items = sorted(self.current_items, key=lambda item: (
            not (self.current_preset and self.current_preset.is_favorite(item.form_id)),
            item.name.lower()
        ))

        for item in sorted_items:
            self.add_item_to_table(item)

    def add_item_to_table(self, item: Item):
        """Add a single item to the items table."""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        # Star column
        is_fav = self.current_preset and self.current_preset.is_favorite(item.form_id)
        star = StarWidget(is_fav)
        star.clicked.connect(lambda i=item: self.toggle_item_favorite(i))
        self.items_table.setCellWidget(row, 0, star)

        # Exception indicator column
        is_exc = self.current_preset and self.current_preset.is_exception(item.form_id)
        if is_exc:
            exc_indicator = ExceptionIndicator()
            self.items_table.setCellWidget(row, 1, exc_indicator)

        # Form ID
        form_id_item = QTableWidgetItem(item.form_id)
        form_id_item.setFlags(form_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 2, form_id_item)

        # Name
        name_item = QTableWidgetItem(item.name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.items_table.setItem(row, 3, name_item)

        # Quantity (editable spinbox)
        qty_spinbox = QSpinBox()
        qty_spinbox.setMinimum(1)
        qty_spinbox.setMaximum(999999)
        qty_spinbox.setValue(item.quantity)
        qty_spinbox.valueChanged.connect(lambda val, i=item: self.update_item_quantity(i, val))
        self.items_table.setCellWidget(row, 4, qty_spinbox)

        # Notes (editable)
        note_text = self.data_manager.app_data.get_note(item.form_id)
        note_item = QTableWidgetItem(note_text)
        self.items_table.setItem(row, 5, note_item)

    def populate_spells_table(self):
        """Populate the spells table."""
        self.spells_table.setRowCount(0)

        # Sort: favorites first
        sorted_spells = sorted(self.current_spells, key=lambda spell: (
            not (self.current_preset and self.current_preset.is_favorite(spell.form_id)),
            spell.name.lower()
        ))

        for spell in sorted_spells:
            self.add_spell_to_table(spell)

    def add_spell_to_table(self, spell: Spell):
        """Add a single spell to the spells table."""
        row = self.spells_table.rowCount()
        self.spells_table.insertRow(row)

        # Star column
        is_fav = self.current_preset and self.current_preset.is_favorite(spell.form_id)
        star = StarWidget(is_fav)
        star.clicked.connect(lambda s=spell: self.toggle_spell_favorite(s))
        self.spells_table.setCellWidget(row, 0, star)

        # Exception indicator column
        is_exc = self.current_preset and self.current_preset.is_exception(spell.form_id)
        if is_exc:
            exc_indicator = ExceptionIndicator()
            self.spells_table.setCellWidget(row, 1, exc_indicator)

        # Form ID
        form_id_item = QTableWidgetItem(spell.form_id)
        form_id_item.setFlags(form_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.spells_table.setItem(row, 2, form_id_item)

        # Name
        name_item = QTableWidgetItem(spell.name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.spells_table.setItem(row, 3, name_item)

        # Notes (editable)
        note_text = self.data_manager.app_data.get_note(spell.form_id)
        note_item = QTableWidgetItem(note_text)
        self.spells_table.setItem(row, 4, note_item)

    def populate_favorites_table(self):
        """Populate the favorites table."""
        self.favorites_table.setRowCount(0)

        if not self.current_preset:
            return

        # Get all favorited items and spells
        favorited_items = [item for item in self.current_items if self.current_preset.is_favorite(item.form_id)]
        favorited_spells = [spell for spell in self.current_spells if self.current_preset.is_favorite(spell.form_id)]

        # Add items
        for item in favorited_items:
            row = self.favorites_table.rowCount()
            self.favorites_table.insertRow(row)

            form_id_item = QTableWidgetItem(item.form_id)
            form_id_item.setFlags(form_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 0, form_id_item)

            name_item = QTableWidgetItem(item.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem("Item")
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 2, type_item)

            note_text = self.data_manager.app_data.get_note(item.form_id)
            note_item = QTableWidgetItem(note_text)
            note_item.setFlags(note_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 3, note_item)

        # Add spells
        for spell in favorited_spells:
            row = self.favorites_table.rowCount()
            self.favorites_table.insertRow(row)

            form_id_item = QTableWidgetItem(spell.form_id)
            form_id_item.setFlags(form_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 0, form_id_item)

            name_item = QTableWidgetItem(spell.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem("Spell")
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 2, type_item)

            note_text = self.data_manager.app_data.get_note(spell.form_id)
            note_item = QTableWidgetItem(note_text)
            note_item.setFlags(note_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.favorites_table.setItem(row, 3, note_item)

    def populate_exceptions_table(self):
        """Populate the exceptions table."""
        self.exceptions_table.setRowCount(0)

        if not self.current_preset:
            return

        # Get all excepted items and spells
        excepted_items = [item for item in self.current_items if self.current_preset.is_exception(item.form_id)]
        excepted_spells = [spell for spell in self.current_spells if self.current_preset.is_exception(spell.form_id)]

        # Add items
        for item in excepted_items:
            row = self.exceptions_table.rowCount()
            self.exceptions_table.insertRow(row)

            form_id_item = QTableWidgetItem(item.form_id)
            form_id_item.setFlags(form_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exceptions_table.setItem(row, 0, form_id_item)

            name_item = QTableWidgetItem(item.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exceptions_table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem("Item")
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exceptions_table.setItem(row, 2, type_item)

        # Add spells
        for spell in excepted_spells:
            row = self.exceptions_table.rowCount()
            self.exceptions_table.insertRow(row)

            form_id_item = QTableWidgetItem(spell.form_id)
            form_id_item.setFlags(form_id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exceptions_table.setItem(row, 0, form_id_item)

            name_item = QTableWidgetItem(spell.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exceptions_table.setItem(row, 1, name_item)

            type_item = QTableWidgetItem("Spell")
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.exceptions_table.setItem(row, 2, type_item)

    def populate_presets_table(self):
        """Populate the presets table."""
        self.presets_table.setRowCount(0)

        for preset_name, preset in self.data_manager.app_data.presets.items():
            row = self.presets_table.rowCount()
            self.presets_table.insertRow(row)

            # Preset name
            name_item = QTableWidgetItem(preset_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # Bold if current preset
            if self.current_preset and preset_name == self.current_preset.name:
                from PySide6.QtGui import QFont
                font = QFont()
                font.setBold(True)
                name_item.setFont(font)
            self.presets_table.setItem(row, 0, name_item)

            # Last used (format nicely)
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(preset.last_used)
                last_used_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                last_used_str = preset.last_used
            last_used_item = QTableWidgetItem(last_used_str)
            last_used_item.setFlags(last_used_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.presets_table.setItem(row, 1, last_used_item)

            # Item count
            items_count_item = QTableWidgetItem(str(len(preset.items)))
            items_count_item.setFlags(items_count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.presets_table.setItem(row, 2, items_count_item)

            # Spell count
            spells_count_item = QTableWidgetItem(str(len(preset.spells)))
            spells_count_item.setFlags(spells_count_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.presets_table.setItem(row, 3, spells_count_item)

    def toggle_exception_mode(self, checked: bool):
        """Toggle exception mode on/off."""
        self.exception_mode_active = checked
        if checked:
            self.exception_mode_btn.setText("Exception Mode: ON")
            self.exception_mode_btn.setStyleSheet("background-color: #90EE90;")
            self.statusBar().showMessage("Exception Mode: Click items/spells to toggle exceptions")
        else:
            self.exception_mode_btn.setText("Exception Mode: OFF")
            self.exception_mode_btn.setStyleSheet("")
            self.statusBar().showMessage("Exception Mode disabled")

    def handle_items_cell_click(self, row: int, col: int):
        """Handle cell click in items table."""
        if self.exception_mode_active and self.current_preset:
            # Get form ID from row
            form_id_item = self.items_table.item(row, 2)
            if form_id_item:
                form_id = form_id_item.text()
                self.current_preset.toggle_exception(form_id)
                self.data_manager.save()
                self.populate_items_table()
                self.populate_exceptions_table()
                self.filter_items_table()

    def handle_spells_cell_click(self, row: int, col: int):
        """Handle cell click in spells table."""
        if self.exception_mode_active and self.current_preset:
            # Get form ID from row
            form_id_item = self.spells_table.item(row, 2)
            if form_id_item:
                form_id = form_id_item.text()
                self.current_preset.toggle_exception(form_id)
                self.data_manager.save()
                self.populate_spells_table()
                self.populate_exceptions_table()
                self.filter_spells_table()

    def toggle_item_favorite(self, item: Item):
        """Toggle favorite status for an item."""
        if self.current_preset:
            self.current_preset.toggle_favorite(item.form_id)
            self.data_manager.save()
            self.populate_items_table()
            self.populate_favorites_table()
            self.filter_items_table()

    def toggle_spell_favorite(self, spell: Spell):
        """Toggle favorite status for a spell."""
        if self.current_preset:
            self.current_preset.toggle_favorite(spell.form_id)
            self.data_manager.save()
            self.populate_spells_table()
            self.populate_favorites_table()
            self.filter_spells_table()

    def update_item_quantity(self, item: Item, new_quantity: int):
        """Update item quantity."""
        item.quantity = new_quantity

    def filter_items_table(self):
        """Filter items table based on search and favorites filter."""
        search_text = self.items_search.text().lower()
        favorites_only = self.items_favorites_only.isChecked()
        hide_exceptions = self.items_hide_exceptions.isChecked()

        for row in range(self.items_table.rowCount()):
            form_id_item = self.items_table.item(row, 2)
            name_item = self.items_table.item(row, 3)
            note_item = self.items_table.item(row, 5)

            if not form_id_item or not name_item:
                continue

            form_id = form_id_item.text().lower()
            name = name_item.text().lower()
            note = note_item.text().lower() if note_item else ""

            # Check hide exceptions filter
            if hide_exceptions and self.current_preset:
                if self.current_preset.is_exception(form_id):
                    self.items_table.setRowHidden(row, True)
                    continue

            # Check favorites filter
            if favorites_only and self.current_preset:
                if not self.current_preset.is_favorite(form_id):
                    self.items_table.setRowHidden(row, True)
                    continue

            # Check search filter
            if search_text:
                # Try quantity match
                qty_widget = self.items_table.cellWidget(row, 4)
                qty_match = False
                if qty_widget and isinstance(qty_widget, QSpinBox):
                    try:
                        search_qty = int(search_text)
                        qty_match = qty_widget.value() == search_qty
                    except ValueError:
                        pass

                matches = (
                    search_text in form_id or
                    search_text in name or
                    search_text in note or
                    qty_match
                )
                self.items_table.setRowHidden(row, not matches)
            else:
                self.items_table.setRowHidden(row, False)

    def filter_spells_table(self):
        """Filter spells table based on search and favorites filter."""
        search_text = self.spells_search.text().lower()
        favorites_only = self.spells_favorites_only.isChecked()
        hide_exceptions = self.spells_hide_exceptions.isChecked()

        for row in range(self.spells_table.rowCount()):
            form_id_item = self.spells_table.item(row, 2)
            name_item = self.spells_table.item(row, 3)
            note_item = self.spells_table.item(row, 4)

            if not form_id_item or not name_item:
                continue

            form_id = form_id_item.text().lower()
            name = name_item.text().lower()
            note = note_item.text().lower() if note_item else ""

            # Check hide exceptions filter
            if hide_exceptions and self.current_preset:
                if self.current_preset.is_exception(form_id):
                    self.spells_table.setRowHidden(row, True)
                    continue

            # Check favorites filter
            if favorites_only and self.current_preset:
                if not self.current_preset.is_favorite(form_id):
                    self.spells_table.setRowHidden(row, True)
                    continue

            # Check search filter
            if search_text:
                matches = (
                    search_text in form_id or
                    search_text in name or
                    search_text in note
                )
                self.spells_table.setRowHidden(row, not matches)
            else:
                self.spells_table.setRowHidden(row, False)

    def show_items_context_menu(self, pos):
        """Show context menu for items table."""
        row = self.items_table.rowAt(pos.y())
        if row < 0:
            return

        form_id_item = self.items_table.item(row, 2)
        if not form_id_item:
            return

        form_id = form_id_item.text()

        menu = QMenu(self)

        # Favorite action
        if self.current_preset and self.current_preset.is_favorite(form_id):
            fav_action = menu.addAction("Remove from Favorites")
        else:
            fav_action = menu.addAction("Add to Favorites")

        # Exception action
        if self.current_preset and self.current_preset.is_exception(form_id):
            exc_action = menu.addAction("Remove Exception")
        else:
            exc_action = menu.addAction("Add Exception")

        action = menu.exec(self.items_table.viewport().mapToGlobal(pos))

        if action == fav_action and self.current_preset:
            self.current_preset.toggle_favorite(form_id)
            self.data_manager.save()
            self.populate_items_table()
            self.populate_favorites_table()
            self.filter_items_table()

        elif action == exc_action and self.current_preset:
            self.current_preset.toggle_exception(form_id)
            self.data_manager.save()
            self.populate_items_table()
            self.populate_exceptions_table()
            self.filter_items_table()

    def show_spells_context_menu(self, pos):
        """Show context menu for spells table."""
        row = self.spells_table.rowAt(pos.y())
        if row < 0:
            return

        form_id_item = self.spells_table.item(row, 2)
        if not form_id_item:
            return

        form_id = form_id_item.text()

        menu = QMenu(self)

        # Favorite action
        if self.current_preset and self.current_preset.is_favorite(form_id):
            fav_action = menu.addAction("Remove from Favorites")
        else:
            fav_action = menu.addAction("Add to Favorites")

        # Exception action
        if self.current_preset and self.current_preset.is_exception(form_id):
            exc_action = menu.addAction("Remove Exception")
        else:
            exc_action = menu.addAction("Add Exception")

        action = menu.exec(self.spells_table.viewport().mapToGlobal(pos))

        if action == fav_action and self.current_preset:
            self.current_preset.toggle_favorite(form_id)
            self.data_manager.save()
            self.populate_spells_table()
            self.populate_favorites_table()
            self.filter_spells_table()

        elif action == exc_action and self.current_preset:
            self.current_preset.toggle_exception(form_id)
            self.data_manager.save()
            self.populate_spells_table()
            self.populate_exceptions_table()
            self.filter_spells_table()

    def filter_favorites_table(self):
        """Filter favorites table based on search."""
        search_text = self.favorites_search.text().lower()

        for row in range(self.favorites_table.rowCount()):
            form_id_item = self.favorites_table.item(row, 0)
            name_item = self.favorites_table.item(row, 1)
            type_item = self.favorites_table.item(row, 2)

            if not form_id_item or not name_item or not type_item:
                continue

            form_id = form_id_item.text().lower()
            name = name_item.text().lower()
            item_type = type_item.text().lower()

            if search_text:
                matches = (
                    search_text in form_id or
                    search_text in name or
                    search_text in item_type
                )
                self.favorites_table.setRowHidden(row, not matches)
            else:
                self.favorites_table.setRowHidden(row, False)

    def filter_exceptions_table(self):
        """Filter exceptions table based on search."""
        search_text = self.exceptions_search.text().lower()

        for row in range(self.exceptions_table.rowCount()):
            form_id_item = self.exceptions_table.item(row, 0)
            name_item = self.exceptions_table.item(row, 1)
            type_item = self.exceptions_table.item(row, 2)

            if not form_id_item or not name_item or not type_item:
                continue

            form_id = form_id_item.text().lower()
            name = name_item.text().lower()
            item_type = type_item.text().lower()

            if search_text:
                matches = (
                    search_text in form_id or
                    search_text in name or
                    search_text in item_type
                )
                self.exceptions_table.setRowHidden(row, not matches)
            else:
                self.exceptions_table.setRowHidden(row, False)

    def show_favorites_context_menu(self, pos):
        """Show context menu for favorites table."""
        row = self.favorites_table.rowAt(pos.y())
        if row < 0:
            return

        form_id_item = self.favorites_table.item(row, 0)
        if not form_id_item or not self.current_preset:
            return

        form_id = form_id_item.text()

        menu = QMenu(self)
        remove_action = menu.addAction("Remove from Favorites")
        action = menu.exec(self.favorites_table.viewport().mapToGlobal(pos))

        if action == remove_action:
            self.current_preset.toggle_favorite(form_id)
            self.data_manager.save()
            self.populate_items_table()
            self.populate_spells_table()
            self.populate_favorites_table()
            self.filter_items_table()
            self.filter_spells_table()
            self.filter_favorites_table()

    def handle_favorites_double_click(self, row: int, col: int):
        """Handle double-click on favorites table to add item to main view."""
        form_id_item = self.favorites_table.item(row, 0)
        type_item = self.favorites_table.item(row, 2)

        if not form_id_item or not type_item:
            return

        form_id = form_id_item.text()
        item_type = type_item.text()

        # Check if item/spell already exists in current view
        if item_type == "Item":
            exists = any(item.form_id.upper() == form_id.upper() for item in self.current_items)
            if not exists:
                # Add with default values
                new_item = Item(form_id=form_id, name="name missing", quantity=1)
                self.current_items.append(new_item)
                self.populate_items_table()
                self.filter_items_table()
                self.statusBar().showMessage(f"Added item {form_id} to main view")
                # Switch to Items tab
                self.main_tabs.setCurrentIndex(0)  # Main tab
                self.main_subtabs.setCurrentIndex(0)  # Items sub-tab
            else:
                self.statusBar().showMessage(f"Item {form_id} already exists in main view")
        else:  # Spell
            exists = any(spell.form_id.upper() == form_id.upper() for spell in self.current_spells)
            if not exists:
                new_spell = Spell(form_id=form_id, name="name missing")
                self.current_spells.append(new_spell)
                self.populate_spells_table()
                self.filter_spells_table()
                self.statusBar().showMessage(f"Added spell {form_id} to main view")
                # Switch to Spells tab
                self.main_tabs.setCurrentIndex(0)  # Main tab
                self.main_subtabs.setCurrentIndex(1)  # Spells sub-tab
            else:
                self.statusBar().showMessage(f"Spell {form_id} already exists in main view")

    def show_exceptions_context_menu(self, pos):
        """Show context menu for exceptions table."""
        row = self.exceptions_table.rowAt(pos.y())
        if row < 0:
            return

        form_id_item = self.exceptions_table.item(row, 0)
        if not form_id_item or not self.current_preset:
            return

        form_id = form_id_item.text()

        menu = QMenu(self)
        remove_action = menu.addAction("Remove Exception")
        action = menu.exec(self.exceptions_table.viewport().mapToGlobal(pos))

        if action == remove_action:
            self.current_preset.toggle_exception(form_id)
            self.data_manager.save()
            self.populate_items_table()
            self.populate_spells_table()
            self.populate_exceptions_table()
            self.filter_items_table()
            self.filter_spells_table()
            self.filter_exceptions_table()

    def show_presets_context_menu(self, pos):
        """Show context menu for presets table."""
        row = self.presets_table.rowAt(pos.y())
        if row < 0:
            return

        preset_name_item = self.presets_table.item(row, 0)
        if not preset_name_item:
            return

        preset_name = preset_name_item.text()

        menu = QMenu(self)
        load_action = menu.addAction("Load Preset")
        menu.addSeparator()
        rename_action = menu.addAction("Rename")
        duplicate_action = menu.addAction("Duplicate")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.presets_table.viewport().mapToGlobal(pos))

        if action == load_action:
            self.load_preset(preset_name)
        elif action == rename_action:
            self.rename_preset_by_name(preset_name)
        elif action == duplicate_action:
            self.duplicate_preset_by_name(preset_name)
        elif action == delete_action:
            self.delete_preset_by_name(preset_name)

    def handle_preset_double_click(self, row: int, col: int):
        """Handle double-click on preset to load it."""
        preset_name_item = self.presets_table.item(row, 0)
        if preset_name_item:
            self.load_preset(preset_name_item.text())

    def load_preset(self, preset_name: str):
        """Load a preset by name."""
        if preset_name not in self.data_manager.app_data.presets:
            return

        # Check if current preset has unsaved changes (simplified check)
        # For now, just confirm if switching
        if self.current_preset and self.current_preset.name != preset_name:
            reply = QMessageBox.question(
                self,
                "Load Preset",
                f"Load preset '{preset_name}'? Current changes will be saved first.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Save current preset
            self.current_preset.update_items(self.current_items)
            self.current_preset.update_spells(self.current_spells)
            self.data_manager.save()

        # Load new preset
        preset = self.data_manager.app_data.presets[preset_name]
        self.current_preset = preset
        self.current_items = preset.get_items()
        self.current_spells = preset.get_spells()
        self.current_preset_label.setText(preset.name)
        self.data_manager.set_current_preset(preset_name)

        # Refresh all views
        self.populate_items_table()
        self.populate_spells_table()
        self.populate_favorites_table()
        self.populate_exceptions_table()
        self.populate_presets_table()
        self.populate_character_info_tab()

        self.statusBar().showMessage(f"Loaded preset: {preset_name}")

        # Switch to Main tab
        self.main_tabs.setCurrentIndex(0)

    def rename_preset_by_name(self, preset_name: str):
        """Rename a preset by name."""
        new_name, ok = QInputDialog.getText(
            self, "Rename Preset",
            "New Name:",
            text=preset_name
        )

        if ok and new_name:
            if self.data_manager.rename_preset(preset_name, new_name):
                # Update current preset reference if it was renamed
                if self.current_preset and self.current_preset.name == preset_name:
                    self.current_preset.name = new_name
                    self.current_preset_label.setText(new_name)
                self.populate_presets_table()
                QMessageBox.information(self, "Success", f"Preset renamed to '{new_name}'")
            else:
                QMessageBox.warning(self, "Error", "Failed to rename preset. Name may already exist.")

    def duplicate_preset_by_name(self, preset_name: str):
        """Duplicate a preset by name."""
        new_name, ok = QInputDialog.getText(
            self, "Duplicate Preset",
            "New Name:",
            text=f"{preset_name} (Copy)"
        )

        if ok and new_name:
            if self.data_manager.duplicate_preset(preset_name, new_name):
                self.populate_presets_table()
                QMessageBox.information(self, "Success", f"Preset duplicated as '{new_name}'")
            else:
                QMessageBox.warning(self, "Error", "Failed to duplicate preset. Name may already exist.")

    def delete_preset_by_name(self, preset_name: str):
        """Delete a preset by name."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete preset '{preset_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.data_manager.delete_preset(preset_name):
                # If deleted current preset, clear it
                if self.current_preset and self.current_preset.name == preset_name:
                    self.current_preset = None
                    self.current_preset_label.setText("None")
                    self.current_items = []
                    self.current_spells = []
                    self.populate_items_table()
                    self.populate_spells_table()
                    self.populate_favorites_table()
                    self.populate_exceptions_table()

                self.populate_presets_table()
                QMessageBox.information(self, "Success", f"Preset '{preset_name}' deleted.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete preset.")

    def load_from_export_log(self):
        """Load items and spells from export log."""
        export_path = Path(self.data_manager.get_export_log_path())

        if not export_path.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"Export log not found at:\n{export_path}\n\nUse File menu to change the path."
            )
            return

        try:
            new_items, new_spells = parse_static_log(export_path)

            # If preset is loaded, show changes preview
            if self.current_preset and (self.current_items or self.current_spells):
                if not self.show_changes_preview(new_items, new_spells):
                    # User cancelled
                    return

            # Apply the changes
            self.current_items = new_items
            self.current_spells = new_spells
            self.populate_items_table()
            self.populate_spells_table()
            self.statusBar().showMessage(f"Loaded {len(new_items)} items and {len(new_spells)} spells from export log")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Export Log",
                f"Failed to parse export log:\n{str(e)}"
            )

    def show_changes_preview(self, new_items: List[Item], new_spells: List[Spell]) -> bool:
        """
        Show a preview dialog of changes between current and new items/spells.
        Returns True if user accepts, False if cancelled.
        """
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Preview Changes from Export Log")
        dialog.setMinimumSize(900, 700)

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("Select which changes to apply:")
        header_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        # Select All / Deselect All buttons
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        header_layout.addWidget(select_all_btn)
        header_layout.addWidget(deselect_all_btn)

        # Select/Deselect Highlighted buttons
        select_highlighted_btn = QPushButton("Select Highlighted")
        deselect_highlighted_btn = QPushButton("Deselect Highlighted")
        select_highlighted_btn.setStyleSheet("background-color: #90EE90;")
        deselect_highlighted_btn.setStyleSheet("background-color: #FFB6C1;")
        header_layout.addWidget(select_highlighted_btn)
        header_layout.addWidget(deselect_highlighted_btn)

        layout.addLayout(header_layout)

        # Store reference to highlighted selection functions
        self.dialog_select_highlighted = None
        self.dialog_deselect_highlighted = None

        # Tab widget for Items and Spells
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Analyze items changes
        items_added, items_removed, items_changed = self.analyze_changes(
            self.current_items, new_items, is_spell=False
        )

        # Analyze spells changes
        spells_added, spells_removed, spells_changed = self.analyze_changes(
            self.current_spells, new_spells, is_spell=True
        )

        # Store checkboxes and tables for selection tracking
        self.changes_checkboxes = []
        self.changes_tables = []  # Store all tables for highlighted selection

        # Items tab
        items_widget, items_checkboxes, items_tables = self.create_changes_tab_with_checkboxes(
            items_added, items_removed, items_changed, is_spell=False
        )
        self.changes_checkboxes.extend(items_checkboxes)
        self.changes_tables.extend(items_tables)
        tabs.addTab(items_widget, f"Items Changes ({len(items_added) + len(items_removed) + len(items_changed)})")

        # Spells tab
        spells_widget, spells_checkboxes, spells_tables = self.create_changes_tab_with_checkboxes(
            spells_added, spells_removed, spells_changed, is_spell=True
        )
        self.changes_checkboxes.extend(spells_checkboxes)
        self.changes_tables.extend(spells_tables)
        tabs.addTab(spells_widget, f"Spells Changes ({len(spells_added) + len(spells_removed) + len(spells_changed)})")

        # Connect select/deselect all buttons
        select_all_btn.clicked.connect(lambda: self.toggle_all_changes(True))
        deselect_all_btn.clicked.connect(lambda: self.toggle_all_changes(False))

        # Connect select/deselect highlighted buttons
        select_highlighted_btn.clicked.connect(lambda: self.toggle_highlighted_changes(tabs, True))
        deselect_highlighted_btn.clicked.connect(lambda: self.toggle_highlighted_changes(tabs, False))

        # Summary label
        total_changes = (len(items_added) + len(items_removed) + len(items_changed) +
                        len(spells_added) + len(spells_removed) + len(spells_changed))

        summary_label = QLabel(
            f"Total: {len(items_added) + len(spells_added)} added, "
            f"{len(items_removed) + len(spells_removed)} removed, "
            f"{len(items_changed) + len(spells_changed)} changed"
        )
        summary_label.setStyleSheet("font-weight: bold; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(summary_label)

        # Warning if no changes
        if total_changes == 0:
            no_changes_label = QLabel("No changes detected. The export log matches the current preset.")
            no_changes_label.setStyleSheet("color: green; font-style: italic;")
            layout.addWidget(no_changes_label)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog and process results
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return False

        # Apply selected changes
        self.apply_selected_changes(new_items, new_spells, items_added, items_removed, items_changed,
                                    spells_added, spells_removed, spells_changed, items_checkboxes, spells_checkboxes)
        return True

    def analyze_changes(self, current_list, new_list, is_spell: bool):
        """
        Analyze changes between current and new items/spells.
        Returns: (added, removed, changed)
        """
        added = []
        removed = []
        changed = []

        # Create lookup dictionaries
        current_dict = {item.form_id.upper(): item for item in current_list}
        new_dict = {item.form_id.upper(): item for item in new_list}

        # Find added and changed
        for form_id, new_item in new_dict.items():
            if form_id not in current_dict:
                added.append(new_item)
            else:
                current_item = current_dict[form_id]
                # For items, check if quantity changed
                if not is_spell and hasattr(new_item, 'quantity') and hasattr(current_item, 'quantity'):
                    if new_item.quantity != current_item.quantity:
                        changed.append({
                            'item': new_item,
                            'old_qty': current_item.quantity,
                            'new_qty': new_item.quantity
                        })

        # Find removed
        for form_id, current_item in current_dict.items():
            if form_id not in new_dict:
                removed.append(current_item)

        return added, removed, changed

    def create_changes_tab_with_checkboxes(self, added, removed, changed, is_spell: bool):
        """Create a tab showing added/removed/changed items or spells with checkboxes."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        checkboxes = []
        tables = []  # Track all tables created in this tab

        # Added section
        if added:
            # Header with select/deselect buttons
            added_header = QHBoxLayout()
            added_label = QLabel(f"✅ Added ({len(added)}):")
            added_label.setStyleSheet("font-weight: bold; color: green; font-size: 11pt;")
            added_header.addWidget(added_label)
            added_header.addStretch()

            select_added_btn = QPushButton("Select All Added")
            deselect_added_btn = QPushButton("Deselect All Added")
            select_added_btn.setMaximumWidth(150)
            deselect_added_btn.setMaximumWidth(150)
            added_header.addWidget(select_added_btn)
            added_header.addWidget(deselect_added_btn)
            layout.addLayout(added_header)

            added_table = QTableWidget()
            if is_spell:
                added_table.setColumnCount(3)
                added_table.setHorizontalHeaderLabels(["Apply", "Form ID", "Name"])
            else:
                added_table.setColumnCount(4)
                added_table.setHorizontalHeaderLabels(["Apply", "Form ID", "Name", "Quantity"])

            added_table.setRowCount(len(added))
            added_checkboxes = []
            for i, item in enumerate(added):
                # Checkbox with drag select support
                checkbox = DragSelectCheckbox()
                checkbox.setChecked(True)
                checkbox_widget = CheckboxCellWidget(checkbox)
                added_table.setCellWidget(i, 0, checkbox_widget)
                checkboxes.append({'checkbox': checkbox, 'type': 'add', 'data': item})
                added_checkboxes.append(checkbox)

                added_table.setItem(i, 1, QTableWidgetItem(item.form_id))
                added_table.setItem(i, 2, QTableWidgetItem(item.name))
                if not is_spell:
                    added_table.setItem(i, 3, QTableWidgetItem(str(item.quantity)))

            # Connect category buttons
            select_added_btn.clicked.connect(lambda: self.set_checkboxes_state(added_checkboxes, True))
            deselect_added_btn.clicked.connect(lambda: self.set_checkboxes_state(added_checkboxes, False))

            added_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            added_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            added_table.setColumnWidth(0, 60)
            added_table.setMaximumHeight(250)
            added_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            added_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
            layout.addWidget(added_table)
            tables.append({'table': added_table, 'checkboxes': added_checkboxes})

        # Removed section
        if removed:
            # Header with select/deselect buttons
            removed_header = QHBoxLayout()
            removed_label = QLabel(f"❌ Removed ({len(removed)}):")
            removed_label.setStyleSheet("font-weight: bold; color: red; font-size: 11pt;")
            removed_header.addWidget(removed_label)
            removed_header.addStretch()

            select_removed_btn = QPushButton("Select All Removed")
            deselect_removed_btn = QPushButton("Deselect All Removed")
            select_removed_btn.setMaximumWidth(150)
            deselect_removed_btn.setMaximumWidth(150)
            removed_header.addWidget(select_removed_btn)
            removed_header.addWidget(deselect_removed_btn)
            layout.addLayout(removed_header)

            removed_table = QTableWidget()
            if is_spell:
                removed_table.setColumnCount(3)
                removed_table.setHorizontalHeaderLabels(["Apply", "Form ID", "Name"])
            else:
                removed_table.setColumnCount(4)
                removed_table.setHorizontalHeaderLabels(["Apply", "Form ID", "Name", "Quantity"])

            removed_table.setRowCount(len(removed))
            removed_checkboxes = []
            for i, item in enumerate(removed):
                # Checkbox with drag select support
                checkbox = DragSelectCheckbox()
                checkbox.setChecked(True)
                checkbox_widget = CheckboxCellWidget(checkbox)
                removed_table.setCellWidget(i, 0, checkbox_widget)
                checkboxes.append({'checkbox': checkbox, 'type': 'remove', 'data': item})
                removed_checkboxes.append(checkbox)

                removed_table.setItem(i, 1, QTableWidgetItem(item.form_id))
                removed_table.setItem(i, 2, QTableWidgetItem(item.name))
                if not is_spell:
                    removed_table.setItem(i, 3, QTableWidgetItem(str(item.quantity)))

            # Connect category buttons
            select_removed_btn.clicked.connect(lambda: self.set_checkboxes_state(removed_checkboxes, True))
            deselect_removed_btn.clicked.connect(lambda: self.set_checkboxes_state(removed_checkboxes, False))

            removed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            removed_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            removed_table.setColumnWidth(0, 60)
            removed_table.setMaximumHeight(250)
            removed_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            removed_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
            layout.addWidget(removed_table)
            tables.append({'table': removed_table, 'checkboxes': removed_checkboxes})

        # Changed section (only for items with quantities)
        if changed and not is_spell:
            # Header with select/deselect buttons
            changed_header = QHBoxLayout()
            changed_label = QLabel(f"🔄 Changed Quantities ({len(changed)}):")
            changed_label.setStyleSheet("font-weight: bold; color: orange; font-size: 11pt;")
            changed_header.addWidget(changed_label)
            changed_header.addStretch()

            select_changed_btn = QPushButton("Select All Changed")
            deselect_changed_btn = QPushButton("Deselect All Changed")
            select_changed_btn.setMaximumWidth(150)
            deselect_changed_btn.setMaximumWidth(150)
            changed_header.addWidget(select_changed_btn)
            changed_header.addWidget(deselect_changed_btn)
            layout.addLayout(changed_header)

            changed_table = QTableWidget()
            changed_table.setColumnCount(5)
            changed_table.setHorizontalHeaderLabels(["Apply", "Form ID", "Name", "Old Qty", "New Qty"])

            changed_table.setRowCount(len(changed))
            changed_checkboxes = []
            for i, change in enumerate(changed):
                # Checkbox with drag select support
                checkbox = DragSelectCheckbox()
                checkbox.setChecked(True)
                checkbox_widget = CheckboxCellWidget(checkbox)
                changed_table.setCellWidget(i, 0, checkbox_widget)
                checkboxes.append({'checkbox': checkbox, 'type': 'change', 'data': change})
                changed_checkboxes.append(checkbox)

                changed_table.setItem(i, 1, QTableWidgetItem(change['item'].form_id))
                changed_table.setItem(i, 2, QTableWidgetItem(change['item'].name))
                changed_table.setItem(i, 3, QTableWidgetItem(str(change['old_qty'])))
                changed_table.setItem(i, 4, QTableWidgetItem(str(change['new_qty'])))

            # Connect category buttons
            select_changed_btn.clicked.connect(lambda: self.set_checkboxes_state(changed_checkboxes, True))
            deselect_changed_btn.clicked.connect(lambda: self.set_checkboxes_state(changed_checkboxes, False))

            changed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            changed_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
            changed_table.setColumnWidth(0, 60)
            changed_table.setMaximumHeight(250)
            changed_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            changed_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
            layout.addWidget(changed_table)
            tables.append({'table': changed_table, 'checkboxes': changed_checkboxes})

        # If no changes in this category
        if not added and not removed and not changed:
            no_changes_label = QLabel("No changes in this category.")
            no_changes_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(no_changes_label)

        layout.addStretch()
        return widget, checkboxes, tables

    def toggle_all_changes(self, checked: bool):
        """Toggle all change checkboxes."""
        for cb_info in self.changes_checkboxes:
            cb_info['checkbox'].setChecked(checked)

    def set_checkboxes_state(self, checkboxes: list, checked: bool):
        """Set state for a specific list of checkboxes."""
        for checkbox in checkboxes:
            checkbox.setChecked(checked)

    def toggle_highlighted_changes(self, tabs_widget, checked: bool):
        """Toggle checkboxes for highlighted/selected rows in all tables."""
        # Iterate through all tables
        for table_info in self.changes_tables:
            table = table_info['table']
            checkboxes = table_info['checkboxes']

            # Get selected rows
            selected_rows = set(index.row() for index in table.selectedIndexes())

            # Toggle checkboxes for selected rows
            for row in selected_rows:
                if row < len(checkboxes):
                    checkboxes[row].setChecked(checked)

    def apply_selected_changes(self, new_items, new_spells, items_added, items_removed, items_changed,
                               spells_added, spells_removed, spells_changed, items_checkboxes, spells_checkboxes):
        """Apply only the selected changes from the preview dialog."""
        # Start with a copy of current items/spells
        result_items = list(self.current_items)
        result_spells = list(self.current_spells)

        # Process items checkboxes
        for cb_info in items_checkboxes:
            if not cb_info['checkbox'].isChecked():
                continue  # Skip unchecked changes

            if cb_info['type'] == 'add':
                # Add new item
                result_items.append(cb_info['data'])

            elif cb_info['type'] == 'remove':
                # Remove item
                result_items = [item for item in result_items
                               if item.form_id.upper() != cb_info['data'].form_id.upper()]

            elif cb_info['type'] == 'change':
                # Update quantity
                for item in result_items:
                    if item.form_id.upper() == cb_info['data']['item'].form_id.upper():
                        item.quantity = cb_info['data']['new_qty']
                        break

        # Process spells checkboxes
        for cb_info in spells_checkboxes:
            if not cb_info['checkbox'].isChecked():
                continue  # Skip unchecked changes

            if cb_info['type'] == 'add':
                # Add new spell
                result_spells.append(cb_info['data'])

            elif cb_info['type'] == 'remove':
                # Remove spell
                result_spells = [spell for spell in result_spells
                                if spell.form_id.upper() != cb_info['data'].form_id.upper()]

        # Update current items and spells
        self.current_items = result_items
        self.current_spells = result_spells

    def add_item_manually(self):
        """Open dialog to manually add an item."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Item Manually")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Form ID input
        layout.addWidget(QLabel("Form ID:"))
        form_id_input = QLineEdit()
        form_id_input.setPlaceholderText("e.g., 0000000F")
        layout.addWidget(form_id_input)

        # Quantity input
        layout.addWidget(QLabel("Quantity:"))
        qty_input = QSpinBox()
        qty_input.setMinimum(1)
        qty_input.setMaximum(999999)
        qty_input.setValue(1)
        layout.addWidget(qty_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            form_id = form_id_input.text().strip()
            if form_id:
                item = Item(form_id=form_id, name="name missing", quantity=qty_input.value())
                self.current_items.append(item)
                self.populate_items_table()
                self.filter_items_table()
                self.statusBar().showMessage(f"Added item {form_id}")

    def add_spell_manually(self):
        """Open dialog to manually add a spell."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Spell Manually")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Form ID input
        layout.addWidget(QLabel("Form ID:"))
        form_id_input = QLineEdit()
        form_id_input.setPlaceholderText("e.g., 00000A3C")
        layout.addWidget(form_id_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            form_id = form_id_input.text().strip()
            if form_id:
                spell = Spell(form_id=form_id, name="name missing")
                self.current_spells.append(spell)
                self.populate_spells_table()
                self.filter_spells_table()
                self.statusBar().showMessage(f"Added spell {form_id}")

    def save_as_preset(self):
        """Save current state as a new preset."""
        if not self.current_items and not self.current_spells:
            QMessageBox.warning(self, "No Data", "Load data from export log first.")
            return

        name, ok = QInputDialog.getText(self, "Save as Preset", "Preset Name:")
        if ok and name:
            # Create new preset
            preset = Preset(name=name)
            preset.update_items(self.current_items)
            preset.update_spells(self.current_spells)

            # Copy favorites/exceptions from current preset if exists
            if self.current_preset:
                preset.favorites = self.current_preset.favorites.copy()
                preset.exceptions = self.current_preset.exceptions.copy()

            if self.data_manager.create_preset(name, preset):
                self.current_preset = preset
                self.current_preset_label.setText(name)
                QMessageBox.information(self, "Success", f"Preset '{name}' created successfully!")
            else:
                QMessageBox.warning(self, "Error", f"Preset '{name}' already exists.")

    def rename_current_preset(self):
        """Rename the current preset."""
        if not self.current_preset:
            QMessageBox.warning(self, "No Preset", "No preset is currently loaded.")
            return

        new_name, ok = QInputDialog.getText(
            self, "Rename Preset",
            "New Name:",
            text=self.current_preset.name
        )

        if ok and new_name:
            old_name = self.current_preset.name
            if self.data_manager.rename_preset(old_name, new_name):
                self.current_preset.name = new_name
                self.current_preset_label.setText(new_name)
                QMessageBox.information(self, "Success", f"Preset renamed to '{new_name}'")
            else:
                QMessageBox.warning(self, "Error", "Failed to rename preset. Name may already exist.")

    def delete_current_preset(self):
        """Delete the current preset."""
        if not self.current_preset:
            QMessageBox.warning(self, "No Preset", "No preset is currently loaded.")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete preset '{self.current_preset.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            name = self.current_preset.name
            if self.data_manager.delete_preset(name):
                self.current_preset = None
                self.current_preset_label.setText("None")
                self.current_items = []
                self.current_spells = []
                self.populate_items_table()
                self.populate_spells_table()
                QMessageBox.information(self, "Success", f"Preset '{name}' deleted.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete preset.")

    def duplicate_current_preset(self):
        """Duplicate the current preset."""
        if not self.current_preset:
            QMessageBox.warning(self, "No Preset", "No preset is currently loaded.")
            return

        new_name, ok = QInputDialog.getText(
            self, "Duplicate Preset",
            "New Name:",
            text=f"{self.current_preset.name} (Copy)"
        )

        if ok and new_name:
            if self.data_manager.duplicate_preset(self.current_preset.name, new_name):
                QMessageBox.information(self, "Success", f"Preset duplicated as '{new_name}'")
            else:
                QMessageBox.warning(self, "Error", "Failed to duplicate preset. Name may already exist.")

    def import_favorites_exceptions(self):
        """Import favorites/exceptions from another preset."""
        QMessageBox.information(self, "Coming Soon", "This feature will be implemented soon!")

    def generate_import_log_file(self):
        """Generate the import log file."""
        if not self.current_items and not self.current_spells:
            QMessageBox.warning(self, "No Data", "No items or spells to export.")
            return

        import_path = Path(self.data_manager.get_import_log_path())
        exceptions = self.current_preset.exceptions if self.current_preset else []

        # Check if extended data is available
        has_extended = (self.current_preset and self.current_preset.character is not None)

        use_full = False
        if has_extended:
            reply = QMessageBox.question(
                self,
                "Export Type",
                "Character data is available. Generate full import log?\n\n"
                "Full: Items, Spells, Attributes, Skills, Stats, Factions, Quests, etc.\n"
                "Basic: Items and Spells only.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            use_full = (reply == QMessageBox.StandardButton.Yes)

        try:
            if use_full:
                generate_full_import_log(
                    self.current_items, self.current_spells, import_path,
                    preset=self.current_preset, exceptions=exceptions
                )
            else:
                generate_import_log(self.current_items, self.current_spells, import_path, exceptions)

            item_count = sum(1 for item in self.current_items if item.form_id.upper() not in [e.upper() for e in exceptions])
            spell_count = sum(1 for spell in self.current_spells if spell.form_id.upper() not in [e.upper() for e in exceptions])

            export_type = "Full import" if use_full else "Import"
            QMessageBox.information(
                self,
                "Success",
                f"{export_type} log generated successfully!\n\n"
                f"Items: {item_count}\n"
                f"Spells: {spell_count}\n"
                f"{'(+ character data, attributes, skills, stats, quests)' if use_full else ''}\n\n"
                f"Saved to:\n{import_path}"
            )
            self.statusBar().showMessage(f"{export_type} log saved to {import_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to generate import log:\n{str(e)}"
            )

    def change_export_log_path(self):
        """Change the export log path."""
        current_path = self.data_manager.get_export_log_path()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Export Log",
            str(Path(current_path).parent),
            "Log Files (*.log);;All Files (*.*)"
        )

        if file_path:
            self.data_manager.set_export_log_path(file_path)
            QMessageBox.information(self, "Success", f"Export log path updated to:\n{file_path}")

    def change_import_log_path(self):
        """Change the import log path."""
        current_path = self.data_manager.get_import_log_path()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Import Log Path",
            str(Path(current_path).parent),
            "Log Files (*.log);;All Files (*.*)"
        )

        if file_path:
            self.data_manager.set_import_log_path(file_path)
            QMessageBox.information(self, "Success", f"Import log path updated to:\n{file_path}")

    def change_save_dump_path(self):
        """Change the save dump path."""
        current_path = self.data_manager.get_save_dump_path()
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Save Dump File",
            str(Path(current_path).parent),
            "Text Files (*.txt);;All Files (*.*)"
        )

        if file_path:
            self.data_manager.set_save_dump_path(file_path)
            QMessageBox.information(self, "Success", f"Save dump path updated to:\n{file_path}")

    def load_from_save_dump(self):
        """Load character data from OBSE64 save dump file."""
        dump_path = Path(self.data_manager.get_save_dump_path())

        if not dump_path.exists():
            # Let user pick a file
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Save Dump File",
                str(dump_path.parent) if dump_path.parent.exists() else "",
                "Text Files (*.txt);;All Files (*.*)"
            )
            if not file_path:
                return
            dump_path = Path(file_path)
            self.data_manager.set_save_dump_path(file_path)

        try:
            # Auto-detect format: classic xOBSE vs remastered OBSE64
            if is_classic_save_dump_format(str(dump_path)):
                parser = ClassicSaveDumpParser(str(dump_path))
            else:
                parser = SaveDumpParser(str(dump_path))
            char_data = parser.parse()

            # Convert CharacterData items to Item objects
            new_items = [
                Item(form_id=inv_item.form_id, name=inv_item.name, quantity=inv_item.quantity)
                for inv_item in char_data.items
            ]
            # Convert CharacterData spells to Spell objects
            new_spells = [
                Spell(form_id=sp.form_id, name=sp.name)
                for sp in char_data.spells
            ]

            # If preset is loaded, show changes preview
            if self.current_preset and (self.current_items or self.current_spells):
                if not self.show_changes_preview(new_items, new_spells):
                    return

            # Apply items/spells
            self.current_items = new_items
            self.current_spells = new_spells

            # Store extended data on current preset
            if self.current_preset:
                preset = self.current_preset

                # Character info
                c = char_data.character
                preset.character = {
                    "name": c.name, "race": c.race, "class": c.class_name,
                    "birthsign": c.birthsign, "level": c.level
                }

                # Attributes and skills
                preset.attributes = dict(char_data.attributes)
                preset.skills = dict(char_data.skills)

                # Statistics
                preset.statistics = {
                    "fame": char_data.fame,
                    "infamy": char_data.infamy,
                    "bounty": char_data.bounty,
                    "pcMiscStats": {str(k): v for k, v in char_data.pc_misc_stats.items()}
                }

                # Factions
                preset.factions = [
                    {"formId": f.form_id, "name": f.name, "rank": f.rank, "title": f.title}
                    for f in char_data.factions
                ]

                # Quests
                preset.quests = list(char_data.completed_quests)
                if char_data.active_quest:
                    aq = char_data.active_quest
                    preset.active_quest = {
                        "formId": aq.form_id, "editorId": aq.editor_id, "stage": aq.stage
                    }
                else:
                    preset.active_quest = None

                preset.current_quests = [
                    {"editorId": cq.editor_id, "stage": cq.stage}
                    for cq in char_data.current_quests
                ]

                # Spells to remove
                preset.spells_to_remove = [
                    {"formId": sp.form_id, "name": sp.name}
                    for sp in char_data.spells_to_remove
                ]

                # Vitals
                v = char_data.vitals
                preset.vitals = {
                    "healthBase": v.health_base, "magickaBase": v.magicka_base,
                    "fatigueBase": v.fatigue_base, "encumbrance": v.encumbrance
                }

                # Magic resistances
                r = char_data.magic_resistances
                preset.magic_resistances = {
                    "fire": r.fire, "frost": r.frost, "shock": r.shock,
                    "magic": r.magic, "disease": r.disease, "poison": r.poison,
                    "paralysis": r.paralysis, "normalWeapons": r.normal_weapons
                }

                # Global variables
                preset.global_variables = [
                    {"formId": gv.form_id, "name": gv.name, "value": gv.value, "type": gv.var_type}
                    for gv in char_data.global_variables
                ]

                # Game time
                gt = char_data.game_time
                preset.game_time = {
                    "daysPassed": gt.days_passed, "gameYear": gt.game_year,
                    "gameMonth": gt.game_month, "gameDay": gt.game_day,
                    "gameHour": gt.game_hour
                }

                # Plugins
                preset.plugins = list(char_data.plugins)

                # Save to disk
                preset.update_items(self.current_items)
                preset.update_spells(self.current_spells)
                self.data_manager.save()

            # Refresh views
            self.populate_items_table()
            self.populate_spells_table()
            self.populate_favorites_table()
            self.populate_exceptions_table()
            self.populate_character_info_tab()

            char_name = char_data.character.name
            char_level = char_data.character.level
            self.statusBar().showMessage(
                f"Loaded: {char_name} (Lv.{char_level}) - "
                f"{len(new_items)} items, {len(new_spells)} spells"
            )

            # Switch to Character tab to show loaded data
            self.main_tabs.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Save Dump",
                f"Failed to parse save dump:\n{str(e)}"
            )

    def closeEvent(self, event):
        """Handle application close event."""
        # Save current preset if exists
        if self.current_preset:
            self.current_preset.update_items(self.current_items)
            self.current_preset.update_spells(self.current_spells)

            # Save notes from tables
            for row in range(self.items_table.rowCount()):
                form_id_item = self.items_table.item(row, 2)
                note_item = self.items_table.item(row, 5)
                if form_id_item and note_item:
                    self.data_manager.app_data.set_note(form_id_item.text(), note_item.text())

            for row in range(self.spells_table.rowCount()):
                form_id_item = self.spells_table.item(row, 2)
                note_item = self.spells_table.item(row, 4)
                if form_id_item and note_item:
                    self.data_manager.app_data.set_note(form_id_item.text(), note_item.text())

            self.data_manager.save()

        # If no presets exist, prompt to save
        elif not self.data_manager.app_data.presets and (self.current_items or self.current_spells):
            reply = QMessageBox.question(
                self,
                "Save Preset",
                "Would you like to save the current data as a preset?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_as_preset()

        event.accept()
