"""
Navigation widgets for Varla-HUD.
Replaces sidebar with Oblivion Remastered-style top tabs + sub-nav bar.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QPixmap

from theme import COLORS


# ── Navigation Structure ─────────────────────────────────────────────────────

NAVIGATION_STRUCTURE = {
    "character": {
        "label": "Character",
        "sub_pages": [
            {"key": "char_info", "label": "Character Info"},
            {"key": "attributes", "label": "Attributes"},
            {"key": "skills", "label": "Skills"},
            {"key": "factions", "label": "Factions"},
            {"key": "details", "label": "Details"},
        ],
    },
    "inventory": {
        "label": "Inventory",
        "sub_pages": [
            {"key": "weapons", "label": "Weapons"},
            {"key": "gear", "label": "Gear"},
            {"key": "alchemy_inv", "label": "Alchemy"},
            {"key": "miscellaneous", "label": "Miscellaneous"},
            {"key": "all_items", "label": "All Items"},
        ],
    },
    "magic": {
        "label": "Magic",
        "sub_pages": [
            {"key": "spell_self", "label": "Self"},
            {"key": "spell_touch", "label": "Touch"},
            {"key": "spell_target", "label": "Target"},
            {"key": "spell_all", "label": "All"},
            {"key": "magic_active_effects", "label": "Active Effects"},
        ],
    },
    "quests": {
        "label": "Quests",
        "sub_pages": [
            {"key": "active_quests", "label": "Active Quests"},
            {"key": "completed_quests", "label": "Completed Quests"},
        ],
    },
    "varla": {
        "label": "Varla",
        "sub_pages": [
            {"key": "globals", "label": "Globals"},
            {"key": "game_time", "label": "Game Time"},
            {"key": "plugins", "label": "Plugins"},
            {"key": "world_state", "label": "World State"},
        ],
    },
}

TAB_ORDER = ["character", "inventory", "magic", "quests", "varla"]

# Resolve placeholder icon path
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
PLACEHOLDER_ICON = os.path.join(_ICON_DIR, "placeholder.png")


class TopTabBar(QWidget):
    """Horizontal row of top-level tab buttons (Character | Inventory | Magic | Quests | Varla)."""

    tab_changed = Signal(str)  # emits tab key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topTabBar")
        self._buttons = {}
        self._active_tab = None
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for tab_key in TAB_ORDER:
            tab_info = NAVIGATION_STRUCTURE[tab_key]
            btn = QPushButton(tab_info["label"])
            btn.setObjectName("topTabBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(40)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked, k=tab_key: self._on_click(k))
            layout.addWidget(btn)
            self._buttons[tab_key] = btn

    def _on_click(self, tab_key: str):
        self.set_active(tab_key)
        self.tab_changed.emit(tab_key)

    def set_active(self, tab_key: str):
        """Highlight the active tab."""
        if self._active_tab and self._active_tab in self._buttons:
            btn = self._buttons[self._active_tab]
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._active_tab = tab_key
        if tab_key in self._buttons:
            btn = self._buttons[tab_key]
            btn.setProperty("active", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)


class SubNavBar(QWidget):
    """Horizontal row of sub-page icon buttons for the current tab."""

    page_selected = Signal(str)  # emits page key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("subNavBar")
        self._buttons = {}
        self._active_key = None
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)

    def set_tab(self, tab_key: str):
        """Rebuild sub-nav buttons for the given tab."""
        # Clear existing buttons
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._buttons.clear()
        self._active_key = None

        if tab_key not in NAVIGATION_STRUCTURE:
            return

        sub_pages = NAVIGATION_STRUCTURE[tab_key]["sub_pages"]

        for page in sub_pages:
            btn = QPushButton()
            btn.setObjectName("subNavBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("active", False)

            # Icon + text layout
            btn_layout = QVBoxLayout()
            btn_layout.setContentsMargins(8, 6, 8, 6)
            btn_layout.setSpacing(2)
            btn_layout.setAlignment(Qt.AlignCenter)

            icon_label = QLabel()
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            if os.path.exists(PLACEHOLDER_ICON):
                pixmap = QPixmap(PLACEHOLDER_ICON).scaled(
                    24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                icon_label.setPixmap(pixmap)
            else:
                icon_label.setText("\u25C6")  # diamond fallback
            btn_layout.addWidget(icon_label)

            text_label = QLabel(page["label"])
            text_label.setAlignment(Qt.AlignCenter)
            text_label.setAttribute(Qt.WA_TransparentForMouseEvents)
            text_label.setStyleSheet(f"font-size: 8pt; background: transparent;")
            btn_layout.addWidget(text_label)

            btn.setLayout(btn_layout)
            btn.setMinimumWidth(80)
            btn.setFixedHeight(60)
            btn.clicked.connect(lambda checked, k=page["key"]: self._on_click(k))
            self._layout.addWidget(btn)
            self._buttons[page["key"]] = btn

        self._layout.addStretch()

    def _on_click(self, page_key: str):
        self.set_active(page_key)
        self.page_selected.emit(page_key)

    def set_active(self, page_key: str):
        """Highlight the active sub-page button."""
        if self._active_key and self._active_key in self._buttons:
            btn = self._buttons[self._active_key]
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._active_key = page_key
        if page_key in self._buttons:
            btn = self._buttons[page_key]
            btn.setProperty("active", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def get_first_page_key(self, tab_key: str) -> str:
        """Return the first sub-page key for a tab."""
        if tab_key in NAVIGATION_STRUCTURE:
            pages = NAVIGATION_STRUCTURE[tab_key]["sub_pages"]
            if pages:
                return pages[0]["key"]
        return ""


class NavigationWidget(QWidget):
    """Composite navigation: TopTabBar + SubNavBar. Emits page_selected(str)."""

    page_selected = Signal(str)  # emits the sub-page key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navigationWidget")
        self._current_tab = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.top_tab_bar = TopTabBar()
        layout.addWidget(self.top_tab_bar)

        self.sub_nav_bar = SubNavBar()
        layout.addWidget(self.sub_nav_bar)

        # Connections
        self.top_tab_bar.tab_changed.connect(self._on_tab_changed)
        self.sub_nav_bar.page_selected.connect(self._on_page_selected)

    def _on_tab_changed(self, tab_key: str):
        """When top tab changes, rebuild sub-nav and select first sub-page."""
        self._current_tab = tab_key
        self.sub_nav_bar.set_tab(tab_key)
        first_key = self.sub_nav_bar.get_first_page_key(tab_key)
        if first_key:
            self.sub_nav_bar.set_active(first_key)
            self.page_selected.emit(first_key)

    def _on_page_selected(self, page_key: str):
        """Forward sub-nav page selection."""
        self.page_selected.emit(page_key)

    def set_active_page(self, page_key: str):
        """Programmatically set the active page (finds tab automatically)."""
        for tab_key, tab_info in NAVIGATION_STRUCTURE.items():
            for page in tab_info["sub_pages"]:
                if page["key"] == page_key:
                    if self._current_tab != tab_key:
                        self._current_tab = tab_key
                        self.top_tab_bar.set_active(tab_key)
                        self.sub_nav_bar.set_tab(tab_key)
                    self.sub_nav_bar.set_active(page_key)
                    return

    def initialize(self):
        """Set up the initial state - select first tab and first sub-page."""
        first_tab = TAB_ORDER[0]
        self.top_tab_bar.set_active(first_tab)
        self._on_tab_changed(first_tab)
