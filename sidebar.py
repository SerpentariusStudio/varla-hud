"""
Sidebar navigation widget for Varla-HUD.
Replaces the 21-tab QTabWidget with a grouped category sidebar.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea, QFrame
from PySide6.QtCore import Signal, Qt

from theme import COLORS


# ── Sidebar Structure ────────────────────────────────────────────────────────

SIDEBAR_STRUCTURE = [
    {
        "label": "Character",
        "items": [
            {"key": "character",   "label": "Character Info"},
            {"key": "attributes",  "label": "Attributes"},
            {"key": "skills",      "label": "Skills"},
            {"key": "statistics",  "label": "Statistics"},
            {"key": "skill_xp",   "label": "Skill XP"},
            {"key": "quick_keys", "label": "Quick Keys"},
        ],
    },
    {
        "label": "Combat",
        "items": [
            {"key": "vitals",           "label": "Vitals"},
            {"key": "resistances",      "label": "Resistances"},
            {"key": "active_effects",   "label": "Active Effects"},
            {"key": "status_modifiers", "label": "Status & Modifiers"},
            {"key": "combat_analytics", "label": "Combat Analytics"},
        ],
    },
    {
        "label": "Inventory",
        "items": [
            {"key": "items",            "label": "Items"},
            {"key": "spells",           "label": "Spells"},
            {"key": "spells_to_remove", "label": "Spells to Remove"},
            {"key": "bank",             "label": "Bank"},
            {"key": "equipment",        "label": "Equipment"},
            {"key": "economy",          "label": "Economy"},
            {"key": "special_items",    "label": "Special Items"},
        ],
    },
    {
        "label": "World",
        "items": [
            {"key": "factions",         "label": "Factions"},
            {"key": "completed_quests", "label": "Completed Quests"},
            {"key": "active_quests",    "label": "Active Quests"},
            {"key": "current_quests",   "label": "Current Quests"},
            {"key": "world_state",      "label": "World State"},
        ],
    },
    {
        "label": "Analytics",
        "items": [
            {"key": "magic_analysis", "label": "Magic Analysis"},
            {"key": "alchemy",        "label": "Alchemy"},
        ],
    },
    {
        "label": "Data",
        "items": [
            {"key": "globals",   "label": "Globals"},
            {"key": "game_time", "label": "Game Time"},
            {"key": "plugins",   "label": "Plugins"},
        ],
    },
    {
        "label": "Meta",
        "items": [
            {"key": "favorites",  "label": "Favorites"},
            {"key": "exceptions", "label": "Exceptions"},
            {"key": "summary",    "label": "Summary"},
        ],
    },
]


class SidebarWidget(QWidget):
    """Sidebar navigation with category headers and clickable page items."""

    page_selected = Signal(str)  # emits the page key

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = {}  # key -> QPushButton
        self._active_key = None
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['sidebar_bg']};")

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {COLORS['sidebar_bg']};")

        container = QWidget()
        container.setStyleSheet(f"background-color: {COLORS['sidebar_bg']};")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        for category in SIDEBAR_STRUCTURE:
            # Category header
            header = QLabel(f"  {category['label'].upper()}")
            header.setStyleSheet(f"""
                color: {COLORS["sidebar_category"]};
                font-size: 9pt;
                font-weight: bold;
                padding: 10px 8px 2px 8px;
                background-color: transparent;
                letter-spacing: 1px;
            """)
            layout.addWidget(header)

            # Gold separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFixedHeight(1)
            separator.setStyleSheet(f"background-color: {COLORS['sidebar_separator']};")
            layout.addWidget(separator)

            # Page items
            for item in category["items"]:
                btn = QPushButton(item["label"])
                btn.setProperty("sidebarItem", True)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda checked, k=item["key"]: self._on_click(k))
                layout.addWidget(btn)
                self._buttons[item["key"]] = btn

        layout.addStretch()
        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

    def _on_click(self, key: str):
        self.set_active(key)
        self.page_selected.emit(key)

    def set_active(self, key: str):
        """Highlight the selected sidebar item."""
        # Clear previous
        if self._active_key and self._active_key in self._buttons:
            self._buttons[self._active_key].setProperty("sidebarActive", False)
            self._buttons[self._active_key].style().unpolish(self._buttons[self._active_key])
            self._buttons[self._active_key].style().polish(self._buttons[self._active_key])

        # Set new
        self._active_key = key
        if key in self._buttons:
            self._buttons[key].setProperty("sidebarActive", True)
            self._buttons[key].style().unpolish(self._buttons[key])
            self._buttons[key].style().polish(self._buttons[key])
