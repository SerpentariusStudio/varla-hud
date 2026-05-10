"""
Navigation widgets for Varla-HUD — "glow up" reskin.

TopTabBar:    Ornate primary tabs (◆ LABEL ◆) with brass rails painted top/bottom
              and an active-tab accent line at the bottom edge.
SubNavBar:    Horizontal "chapter pill" bar — [num][icon][label] per page.
NavigationWidget combines them and emits page_selected(str).
"""

import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSizePolicy, QFrame,
    QToolTip,
)
from PySide6.QtCore import Signal, Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QPen

from theme import (
    COLORS,
    BRASS_DEEP, BRASS, BRASS_LIT, BRASS_BRIGHT,
    INK_OAK, PARCHMENT_DIMR,
)
from translations import tr


# ── Navigation Structure ─────────────────────────────────────────────────────

NAVIGATION_STRUCTURE = {
    "character": {
        "label": "Character",
        "sub_pages": [
            {"key": "char_info",   "label": "Character Info"},
            {"key": "attributes",  "label": "Attributes"},
            {"key": "skills",      "label": "Skills"},
            {"key": "factions",    "label": "Factions"},
            {"key": "details",     "label": "Details"},
        ],
    },
    "inventory": {
        "label": "Inventory",
        "sub_pages": [
            {"key": "weapons",       "label": "Weapons"},
            {"key": "gear",          "label": "Gear"},
            {"key": "alchemy_inv",   "label": "Alchemy"},
            {"key": "miscellaneous", "label": "Miscellaneous"},
            {"key": "all_items",     "label": "All Items"},
        ],
    },
    "magic": {
        "label": "Magic",
        "sub_pages": [
            {"key": "spell_self",           "label": "Self"},
            {"key": "spell_touch",          "label": "Touch"},
            {"key": "spell_target",         "label": "Target"},
            {"key": "spell_all",            "label": "All"},
            {"key": "magic_active_effects", "label": "Active Effects"},
        ],
    },
    "quests": {
        "label": "Quests",
        "sub_pages": [
            {"key": "active_quests",    "label": "Active Quests"},
            {"key": "completed_quests", "label": "Completed Quests"},
            {"key": "quest_vars",       "label": "Quest Variables"},
        ],
    },
    "varla": {
        "label": "Varla",
        "sub_pages": [
            {"key": "globals",     "label": "Globals"},
            {"key": "game_time",   "label": "Game Time"},
            {"key": "plugins",     "label": "Plugins"},
            {"key": "world_state", "label": "World State"},
        ],
    },
}

TAB_ORDER = ["character", "inventory", "magic", "quests", "varla"]

# Resolve placeholder icon path
_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")
PLACEHOLDER_ICON = os.path.join(_ICON_DIR, "placeholder.png")


# ── Top Tab Bar ──────────────────────────────────────────────────────────────

class TopTabBar(QWidget):
    """
    Ornate primary tab bar.

    - 44px tall
    - Top + bottom 1px brass rails painted in paintEvent
    - Each tab cell shows "◆ LABEL ◆" in EB Garamond uppercase
    - Active tab gets a 2px brass accent line at the bottom edge
    """

    tab_changed = Signal(str)  # emits tab key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topTabBar")
        self.setFixedHeight(44)
        self._buttons: dict[str, QPushButton] = {}
        self._active_tab: str | None = None
        self._build_ui()

    # ── construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for tab_key in TAB_ORDER:
            tab_info = NAVIGATION_STRUCTURE[tab_key]
            label = tr(tab_info["label"])
            # ornament (Unicode lozenge) flanks the label
            btn = QPushButton(f"◆  {label.upper()}  ◆")
            btn.setObjectName("topTabBtn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(44)
            btn.setProperty("active", False)
            btn.clicked.connect(lambda checked, k=tab_key: self._on_click(k))
            layout.addWidget(btn)
            self._buttons[tab_key] = btn

    # ── public API ────────────────────────────────────────────────────────

    def set_active(self, tab_key: str):
        """Highlight the active tab."""
        if self._active_tab and self._active_tab in self._buttons:
            self._set_btn_active(self._buttons[self._active_tab], False)
        self._active_tab = tab_key
        if tab_key in self._buttons:
            self._set_btn_active(self._buttons[tab_key], True)
        self.update()  # repaint accent line

    # ── helpers ───────────────────────────────────────────────────────────

    def _on_click(self, tab_key: str):
        self.set_active(tab_key)
        self.tab_changed.emit(tab_key)

    @staticmethod
    def _set_btn_active(btn: QPushButton, active: bool):
        btn.setProperty("active", active)
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    # ── paint: brass rails + active-tab bottom accent ─────────────────────

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing, False)
            w = self.width()
            h = self.height()

            # Top brass rail (transparent → brass-deep 20% → brass 50% → brass-deep 80% → transparent)
            top = QLinearGradient(0, 0, w, 0)
            top.setColorAt(0.0,  QColor(0, 0, 0, 0))
            top.setColorAt(0.20, QColor(BRASS_DEEP))
            top.setColorAt(0.50, QColor(BRASS))
            top.setColorAt(0.80, QColor(BRASS_DEEP))
            top.setColorAt(1.0,  QColor(0, 0, 0, 0))
            p.setOpacity(0.5)
            p.fillRect(QRect(0, 0, w, 1), top)

            # Bottom brass rail (single-stop centred)
            bot = QLinearGradient(0, 0, w, 0)
            bot.setColorAt(0.0, QColor(0, 0, 0, 0))
            bot.setColorAt(0.5, QColor(BRASS_DEEP))
            bot.setColorAt(1.0, QColor(0, 0, 0, 0))
            p.fillRect(QRect(0, h - 1, w, 1), bot)
            p.setOpacity(1.0)

            # Active tab accent line (2px) spanning ~10%-90% of tab width
            if self._active_tab and self._active_tab in self._buttons:
                btn = self._buttons[self._active_tab]
                geo = btn.geometry()
                inset = int(geo.width() * 0.10)
                x1 = geo.x() + inset
                line_w = geo.width() - 2 * inset
                accent = QLinearGradient(x1, 0, x1 + line_w, 0)
                accent.setColorAt(0.0, QColor(0, 0, 0, 0))
                accent.setColorAt(0.20, QColor(BRASS_LIT))
                accent.setColorAt(0.50, QColor(BRASS_BRIGHT))
                accent.setColorAt(0.80, QColor(BRASS_LIT))
                accent.setColorAt(1.0, QColor(0, 0, 0, 0))
                p.fillRect(QRect(x1, h - 2, line_w, 2), accent)
        finally:
            p.end()


# ── Sub-nav (Chapter Pills) ──────────────────────────────────────────────────

class _ChapterPill(QPushButton):
    """
    A pill containing [num badge][icon label][text label].

    Implemented as a single QPushButton so QSS pseudo-states (hover, active)
    apply to the whole pill, with a child layout for the inner widgets.
    """

    def __init__(self, num: int, icon_glyph: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("subNavBtn")
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("active", False)
        self.setMinimumHeight(28)
        self.setFlat(True)
        # Tooltip mirrors the inline label so it stays readable if the bar
        # is ever cramped (small windows, future icon-only mode, etc.).
        self.setToolTip(label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 3, 12, 3)
        layout.setSpacing(8)

        self._num_lbl = QLabel(f"{num:02d}")
        self._num_lbl.setObjectName("chapterNum")
        self._num_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(self._num_lbl)

        self._icon_lbl = QLabel(icon_glyph)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._icon_lbl.setStyleSheet(
            f"color: {COLORS['parchment_dim']}; "
            f"background: transparent; font-size: 11pt;"
        )
        layout.addWidget(self._icon_lbl)

        self._text_lbl = QLabel(label)
        self._text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._text_lbl.setStyleSheet(
            "background: transparent; color: inherit;"
        )
        layout.addWidget(self._text_lbl)

    def set_active(self, active: bool):
        self.setProperty("active", active)
        # bump num badge to its "active" QSS variant by switching object name
        self._num_lbl.setObjectName("chapterNumActive" if active else "chapterNum")
        self._num_lbl.style().unpolish(self._num_lbl)
        self._num_lbl.style().polish(self._num_lbl)
        self.style().unpolish(self)
        self.style().polish(self)

    def enterEvent(self, event):
        # Qt's default tooltip wake-up delay (~700ms) is not configurable via
        # QSS, so we trigger the tooltip ourselves on cursor enter for an
        # instant response. We anchor it just below the pill so it doesn't
        # cover the row.
        tip = self.toolTip()
        if tip:
            anchor = self.mapToGlobal(QPoint(0, self.height() + 2))
            QToolTip.showText(anchor, tip, self, self.rect())
        super().enterEvent(event)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)


# Friendly icon glyph per page key (Unicode fallback if no SVG icons).
_PAGE_ICON = {
    "char_info":              "✴",   # ✴ heavy star
    "attributes":             "❖",   # ❖
    "skills":                 "⚘",   # ⚘
    "factions":               "⚔",   # ⚔
    "details":                "⁂",   # ⁂
    "weapons":                "⚔",   # ⚔
    "gear":                   "⛊",   # ⛊
    "alchemy_inv":            "⚚",   # ⚚
    "miscellaneous":          "❖",   # ❖
    "all_items":              "⧉",   # ⧉
    "spell_self":             "✴",   # ✴
    "spell_touch":            "✋",   # ✋
    "spell_target":           "⌖",   # ⌖
    "spell_all":              "❦",   # ❦
    "magic_active_effects":   "⚛",   # ⚛
    "active_quests":          "❒",   # ❒
    "completed_quests":       "✓",   # ✓
    "quest_vars":             "ƒ",   # ƒ — script-variable / function
    "globals":                "⌖",   # ⌖
    "game_time":              "⧖",   # ⧖
    "plugins":                "❖",   # ❖
    "world_state":            "✵",   # ✵
}


class SubNavBar(QWidget):
    """Horizontal chapter-pill row for the active tab's sub-pages."""

    page_selected = Signal(str)  # emits page key

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("subNavBar")
        self.setFixedHeight(40)
        self._buttons: dict[str, _ChapterPill] = {}
        self._active_key: str | None = None
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 4, 10, 4)
        self._layout.setSpacing(6)

    def set_tab(self, tab_key: str):
        """Rebuild chapter pills for the given tab."""
        # Clear existing buttons
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._buttons.clear()
        self._active_key = None

        if tab_key not in NAVIGATION_STRUCTURE:
            return

        for idx, page in enumerate(NAVIGATION_STRUCTURE[tab_key]["sub_pages"], 1):
            glyph = _PAGE_ICON.get(page["key"], "◆")
            pill = _ChapterPill(idx, glyph, tr(page["label"]))
            pill.clicked.connect(lambda checked, k=page["key"]: self._on_click(k))
            self._layout.addWidget(pill)
            self._buttons[page["key"]] = pill

        self._layout.addStretch()

    def _on_click(self, page_key: str):
        self.set_active(page_key)
        self.page_selected.emit(page_key)

    def set_active(self, page_key: str):
        if self._active_key and self._active_key in self._buttons:
            self._buttons[self._active_key].set_active(False)
        self._active_key = page_key
        if page_key in self._buttons:
            self._buttons[page_key].set_active(True)

    def get_first_page_key(self, tab_key: str) -> str:
        if tab_key in NAVIGATION_STRUCTURE:
            pages = NAVIGATION_STRUCTURE[tab_key]["sub_pages"]
            if pages:
                return pages[0]["key"]
        return ""


# ── Composite widget ─────────────────────────────────────────────────────────

class NavigationWidget(QWidget):
    """TopTabBar + SubNavBar. Emits page_selected(str)."""

    page_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("navigationWidget")
        self._current_tab: str | None = None

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
        self._current_tab = tab_key
        self.sub_nav_bar.set_tab(tab_key)
        first_key = self.sub_nav_bar.get_first_page_key(tab_key)
        if first_key:
            self.sub_nav_bar.set_active(first_key)
            self.page_selected.emit(first_key)

    def _on_page_selected(self, page_key: str):
        self.page_selected.emit(page_key)

    def set_active_page(self, page_key: str):
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
        first_tab = TAB_ORDER[0]
        self.top_tab_bar.set_active(first_tab)
        self._on_tab_changed(first_tab)
