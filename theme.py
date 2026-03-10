"""
Dark Medieval Theme for Varla-HUD
Oblivion Remastered in-game menu inspired dark stone/leather palette.
"""

from PySide6.QtGui import QColor


# ── Color Palette ────────────────────────────────────────────────────────────
# Dark stone/leather backgrounds with cream/gold text and warm accents.

COLORS = {
    # Backgrounds — dark stone/leather tones
    "bg_primary":       "#1e1a14",   # dark brown-black (main bg)
    "bg_secondary":     "#2a2218",   # slightly lighter stone
    "bg_tertiary":      "#342c20",   # aged leather
    "bg_input":         "#3a3228",   # input fields — dark warm
    "bg_hover":         "#4a3e30",   # hover highlight
    "bg_pressed":       "#2a2218",   # pressed state
    "bg_selected":      "#4a4030",   # selected / highlighted row

    # Accent colors — brighter gold for contrast on dark
    "accent_gold":      "#c8a030",   # bright gold for headers/titles
    "accent_gold_dim":  "#a08028",   # muted gold for borders
    "accent_gold_bright": "#d4b040", # bright accent for emphasis
    "accent_amber":     "#c89030",   # amber
    "accent_copper":    "#b07030",   # copper tone

    # Text — cream/gold on dark
    "text_primary":     "#d4c8a0",   # cream text
    "text_secondary":   "#b0a480",   # softer cream
    "text_muted":       "#8a7a5a",   # faded
    "text_disabled":    "#6a5a3a",   # very faded
    "text_bright":      "#e0d4b0",   # bright cream (for emphasis)

    # Borders — warm dark tones
    "border_primary":   "#5a4a30",   # standard border
    "border_light":     "#6a5a40",   # lighter border
    "border_dark":      "#3a3020",   # dark frame border
    "border_gold":      "#c8a030",   # accent gold border

    # Buttons — warm dark panels
    "btn_primary_bg":   "#4a3e2e",   # brown button
    "btn_primary_hover": "#5a4e3e",  # lighter on hover
    "btn_primary_pressed": "#3a2e1e", # darker on press
    "btn_danger_bg":    "#6a2820",   # dark red
    "btn_danger_hover": "#7a3830",   # lighter red
    "btn_danger_pressed": "#5a1810", # darker red
    "btn_danger_border": "#7a3028",  # red border
    "btn_success_bg":   "#3a5828",   # muted olive-green
    "btn_success_hover": "#4a6838",  # lighter olive
    "btn_success_pressed": "#2a4818", # darker olive
    "btn_action_bg":    "#3a3020",   # dark brown (load/action)
    "btn_action_hover": "#4a4030",   # lighter
    "btn_action_pressed": "#2a2010", # darker

    # Table rows — dark alternating
    "table_row_1":      "#2a2218",   # darker row
    "table_row_2":      "#322a1e",   # slightly lighter alternating
    "table_header_bg":  "#3a3020",   # dark header
    "table_header_text": "#d4c8a0",  # cream text on header
    "table_grid":       "#3a3020",   # subtle grid lines
    "table_selection":  "#4a4030",   # warm selection

    # Special row highlights
    "favorite_row":     "#3a3518",   # dark golden tint
    "exception_row":    "#283828",   # dark sage tint
    "favorite_text":    "#d4b040",   # gold text
    "exception_text":   "#80b060",   # green text

    # Star & exception widgets
    "star_active":      "#d4b040",   # bright gold star
    "star_inactive":    "#6a5a3a",   # faded
    "exception_active": "#80b060",   # green warning
    "exception_inactive": "#6a5a3a", # faded

    # Tri-state
    "tristate_neutral_bg":   "#2a2218",
    "tristate_neutral_fg":   "#8a7a5a",
    "tristate_approved_bg":  "#283828",  # dark green
    "tristate_approved_fg":  "#80b060",  # green text
    "tristate_rejected_bg":  "#382020",  # dark red
    "tristate_rejected_fg":  "#c06060",  # red text

    # Scrollbar
    "scrollbar_bg":     "#1e1a14",   # dark bg
    "scrollbar_handle": "#4a3e2e",   # warm handle
    "scrollbar_hover":  "#5a4e3e",   # lighter on hover

    # Sidebar (kept for backward compat, but now using nav widgets)
    "sidebar_bg":       "#1a1610",   # darkest
    "sidebar_item":     "#d4c8a0",   # cream text
    "sidebar_item_hover": "#e0d4b0", # bright cream
    "sidebar_item_active": "#e0d4b0", # warm highlighted
    "sidebar_category": "#c8a030",   # gold headers
    "sidebar_separator": "#3a3020",  # dark separator

    # Navigation — top tab bar
    "nav_tab_bg":       "#1a1610",   # dark strip
    "nav_tab_text":     "#b0a480",   # cream text
    "nav_tab_active_bg": "#342c20",  # parchment undertone
    "nav_tab_active_text": "#d4b040", # bright gold
    "nav_tab_hover_bg": "#2a2218",   # subtle hover

    # Navigation — sub-nav bar
    "nav_sub_bg":       "#222018",   # dark background
    "nav_sub_btn_bg":   "transparent",
    "nav_sub_btn_active_bg": "#342c20",
    "nav_sub_underline": "#c8a030",  # gold underline on active

    # Detail panel
    "detail_bg":        "#262018",   # slightly lighter than main
    "detail_border":    "#4a3e2e",   # aged parchment border

    # Status bar
    "statusbar_bg":     "#1a1610",   # dark strip
    "statusbar_text":   "#b0a480",   # cream text

    # Toolbar — dark frame
    "toolbar_bg":       "#1a1610",   # dark frame
    "toolbar_border":   "#2a2218",   # slightly lighter border

    # GroupBox
    "groupbox_border":  "#4a3e2e",   # warm border
    "groupbox_title":   "#c8a030",   # gold title

    # Dialog / Preview
    "dialog_bg":        "#2a2218",   # dark
    "preview_approve":  "#283828",   # dark green
    "preview_reject":   "#382020",   # dark red
    "preview_select":   "#202838",   # dark blue

    # Load order manager
    "lom_green_bg":     "#283828",   # dark green
    "lom_red_bg":       "#382020",   # dark red
    "lom_green_fg":     "#80b060",   # green text
    "lom_gray_fg":      "#8a7a5a",   # faded
    "lom_info_bg":      "#2a2818",   # warm info
    "lom_instruction_bg": "#222818", # dark green-tint
}


# ── Global QSS Stylesheet ───────────────────────────────────────────────────

WARM_MEDIEVAL_QSS = f"""

/* ─── Main Window ─── */
QMainWindow {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
}}

QWidget {{
    background-color: {COLORS["bg_primary"]};
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 10pt;
}}

/* ─── Labels ─── */
QLabel {{
    color: {COLORS["text_primary"]};
    background-color: transparent;
}}

/* ─── Toolbar ─── */
QToolBar {{
    background-color: {COLORS["toolbar_bg"]};
    border-bottom: 2px solid {COLORS["toolbar_border"]};
    spacing: 6px;
    padding: 4px;
}}

QToolBar QLabel {{
    color: {COLORS["text_bright"]};
    padding: 0 4px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {COLORS["border_light"]};
    margin: 4px 6px;
}}

/* ─── Buttons ─── */
QPushButton {{
    background-color: {COLORS["btn_primary_bg"]};
    color: {COLORS["text_bright"]};
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: bold;
    min-height: 22px;
}}

QPushButton:hover {{
    background-color: {COLORS["btn_primary_hover"]};
    border-color: {COLORS["border_primary"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["btn_primary_pressed"]};
}}

QPushButton:disabled {{
    color: {COLORS["text_disabled"]};
    background-color: {COLORS["bg_tertiary"]};
    border-color: {COLORS["border_light"]};
}}

/* Special button styles via object name */
QPushButton#deleteBtn {{
    background-color: {COLORS["btn_danger_bg"]};
    color: {COLORS["text_bright"]};
    border: 2px solid {COLORS["btn_danger_border"]};
    font-size: 13pt;
    padding: 8px 16px;
}}

QPushButton#deleteBtn:hover {{
    background-color: {COLORS["btn_danger_hover"]};
    border-color: #8a4030;
}}

QPushButton#deleteBtn:pressed {{
    background-color: {COLORS["btn_danger_pressed"]};
}}

QPushButton#dangerBtn {{
    background-color: {COLORS["btn_danger_bg"]};
    color: {COLORS["text_bright"]};
    border: 1px solid {COLORS["btn_danger_border"]};
}}

QPushButton#dangerBtn:hover {{
    background-color: {COLORS["btn_danger_hover"]};
}}

QPushButton#loadLatestBtn {{
    background-color: {COLORS["btn_action_bg"]};
    color: {COLORS["text_bright"]};
    font-weight: bold;
    padding: 5px 10px;
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 3px;
}}

QPushButton#loadLatestBtn:hover {{
    background-color: {COLORS["btn_action_hover"]};
}}

QPushButton#loadLatestBtn:pressed {{
    background-color: {COLORS["btn_action_pressed"]};
}}

QPushButton#loadBtn {{
    background-color: {COLORS["btn_action_bg"]};
    color: {COLORS["text_bright"]};
    font-weight: bold;
    padding: 10px;
    border: 1px solid {COLORS["border_dark"]};
}}

QPushButton#loadBtn:hover {{
    background-color: {COLORS["btn_action_hover"]};
}}

QPushButton#generateBtn {{
    background-color: {COLORS["btn_success_bg"]};
    color: {COLORS["text_bright"]};
    font-weight: bold;
    padding: 10px;
    border: 1px solid #2a4818;
}}

QPushButton#generateBtn:hover {{
    background-color: {COLORS["btn_success_hover"]};
}}

QPushButton#generateBtn:pressed {{
    background-color: {COLORS["btn_success_pressed"]};
}}

/* ─── Line Edits & SpinBoxes ─── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 3px;
    padding: 4px 8px;
    selection-background-color: {COLORS["accent_gold_dim"]};
    selection-color: {COLORS["text_bright"]};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {COLORS["border_gold"]};
    border-width: 2px;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background-color: {COLORS["bg_tertiary"]};
    border-left: 1px solid {COLORS["border_primary"]};
    border-bottom: 1px solid {COLORS["border_primary"]};
    width: 16px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS["bg_tertiary"]};
    border-left: 1px solid {COLORS["border_primary"]};
    width: 16px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {COLORS["bg_hover"]};
}}

QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    width: 7px;
    height: 7px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 7px;
    height: 7px;
}}

/* ─── ComboBox dropdown ─── */
QComboBox::drop-down {{
    border-left: 1px solid {COLORS["border_primary"]};
    background-color: {COLORS["bg_tertiary"]};
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_primary"]};
    selection-background-color: {COLORS["bg_selected"]};
    selection-color: {COLORS["text_bright"]};
}}

/* ─── Tables ─── */
QTableWidget, QTableView {{
    background-color: {COLORS["table_row_1"]};
    alternate-background-color: {COLORS["table_row_2"]};
    color: {COLORS["text_primary"]};
    gridline-color: {COLORS["table_grid"]};
    border: 2px solid {COLORS["border_dark"]};
    selection-background-color: {COLORS["table_selection"]};
    selection-color: {COLORS["text_bright"]};
}}

QTableWidget::item, QTableView::item {{
    padding: 6px 4px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {COLORS["table_selection"]};
    color: {COLORS["text_bright"]};
}}

QHeaderView {{
    background-color: {COLORS["table_header_bg"]};
}}

QHeaderView::section {{
    background-color: {COLORS["table_header_bg"]};
    color: {COLORS["table_header_text"]};
    padding: 6px;
    border: 1px solid {COLORS["border_dark"]};
    font-weight: bold;
}}

QHeaderView::section:hover {{
    background-color: {COLORS["bg_hover"]};
}}

/* ─── Scroll Bars ─── */
QScrollBar:vertical {{
    background-color: {COLORS["scrollbar_bg"]};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["scrollbar_handle"]};
    min-height: 30px;
    border-radius: 4px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["scrollbar_hover"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {COLORS["scrollbar_bg"]};
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS["scrollbar_handle"]};
    min-width: 30px;
    border-radius: 4px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS["scrollbar_hover"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ─── Group Box ─── */
QGroupBox {{
    border: 1px solid {COLORS["groupbox_border"]};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: {COLORS["groupbox_title"]};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: {COLORS["groupbox_title"]};
}}

/* ─── Text Edit ─── */
QTextEdit {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 3px;
    selection-background-color: {COLORS["accent_gold_dim"]};
    font-family: 'Courier New', monospace;
    font-size: 10pt;
}}

/* ─── List Widget ─── */
QListWidget {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 3px;
}}

QListWidget::item {{
    padding: 4px;
}}

QListWidget::item:selected {{
    background-color: {COLORS["table_selection"]};
    color: {COLORS["text_bright"]};
}}

QListWidget::item:hover {{
    background-color: {COLORS["bg_hover"]};
}}

/* ─── Tab Widget (used in sub-dialogs like preview changes) ─── */
QTabWidget::pane {{
    background-color: {COLORS["bg_secondary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-top: none;
}}

QTabBar::tab {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS["bg_secondary"]};
    color: {COLORS["accent_gold"]};
    border-bottom: 2px solid {COLORS["accent_gold"]};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_primary"]};
}}

/* ─── Scroll Area ─── */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ─── Menu ─── */
QMenu {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_primary"]};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: 3px;
}}

QMenu::item:selected {{
    background-color: {COLORS["bg_selected"]};
    color: {COLORS["text_bright"]};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS["border_primary"]};
    margin: 4px 8px;
}}

/* ─── ToolTip ─── */
QToolTip {{
    background-color: {COLORS["bg_input"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_dark"]};
    padding: 4px 8px;
}}

/* ─── Options Bar ─── */
QFrame#options_bar {{
    background-color: {COLORS["bg_secondary"]};
    border-bottom: 1px solid {COLORS["border_dark"]};
}}

QLabel#options_label {{
    color: {COLORS["text_secondary"]};
    font-size: 11px;
}}

QLabel#options_path {{
    color: {COLORS["text_primary"]};
    font-size: 11px;
    font-style: italic;
}}

QFrame#options_sep {{
    color: {COLORS["border_dark"]};
}}

QPushButton#options_btn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_primary"]};
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 3px;
    font-size: 11px;
    padding: 1px 4px;
}}

QPushButton#options_btn:hover {{
    background-color: {COLORS["btn_primary_hover"]};
    border-color: {COLORS["border_primary"]};
}}

QPushButton#options_fmt_btn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 3px;
    font-size: 11px;
    padding: 1px 4px;
}}

QPushButton#options_fmt_btn:hover {{
    background-color: {COLORS["btn_primary_hover"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["border_primary"]};
}}

QPushButton#options_fmt_btn:checked {{
    background-color: {COLORS["btn_primary_bg"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["border_primary"]};
    font-weight: bold;
}}

/* ─── [SaveDump] Export Toggle (options bar) ─── */
QPushButton#options_export_btn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_disabled"]};
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 3px;
    font-size: 11px;
    font-weight: bold;
    padding: 1px 4px;
}}

QPushButton#options_export_btn:hover {{
    border-color: {COLORS["accent_gold_dim"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton#options_export_btn:checked {{
    background-color: {COLORS["accent_gold_dim"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["accent_gold"]};
    font-weight: bold;
}}

/* ─── Status Bar ─── */
QStatusBar {{
    background-color: {COLORS["statusbar_bg"]};
    color: {COLORS["statusbar_text"]};
    border-top: 2px solid {COLORS["toolbar_border"]};
}}

/* ─── Splitter ─── */
QSplitter::handle {{
    background-color: {COLORS["border_dark"]};
    width: 2px;
}}

QSplitter::handle:hover {{
    background-color: {COLORS["accent_gold_dim"]};
}}

/* ─── Check Box ─── */
QCheckBox {{
    color: {COLORS["text_primary"]};
    spacing: 8px;
    background-color: transparent;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 3px;
    background-color: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent_gold_dim"]};
    border-color: {COLORS["border_gold"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["border_gold"]};
}}

/* ─── Dialog ─── */
QDialog {{
    background-color: {COLORS["dialog_bg"]};
    color: {COLORS["text_primary"]};
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

/* ─── Form Layout Labels ─── */
QFormLayout QLabel {{
    color: {COLORS["text_secondary"]};
    font-weight: bold;
}}

/* ─── Message Box ─── */
QMessageBox {{
    background-color: {COLORS["dialog_bg"]};
    color: {COLORS["text_primary"]};
}}

QMessageBox QLabel {{
    color: {COLORS["text_primary"]};
}}

/* ─── Input Dialog ─── */
QInputDialog {{
    background-color: {COLORS["dialog_bg"]};
}}

/* ─── Game Mode Combo ─── */
#gameModeCombo {{
    font-size: 11pt;
    font-weight: bold;
    padding: 4px 8px;
    min-width: 200px;
}}

/* ─── Path Display Labels ─── */
QLabel#pathDisplay {{
    background-color: {COLORS["bg_input"]};
    padding: 5px;
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 3px;
    color: {COLORS["text_secondary"]};
}}

/* ─── App Title ─── */
QLabel#appTitle {{
    color: {COLORS["accent_gold"]};
    font-size: 16pt;
    font-weight: bold;
    background-color: transparent;
}}

/* ─── Bank Header ─── */
QLabel#bankHeader {{
    font-weight: bold;
    font-size: 12pt;
    color: {COLORS["accent_amber"]};
}}

/* ─── Sidebar item buttons (legacy, kept for compat) ─── */
QPushButton[sidebarItem="true"] {{
    background-color: transparent;
    color: {COLORS["sidebar_item"]};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: left;
    padding: 7px 12px 7px 16px;
    font-weight: normal;
    font-size: 10pt;
}}

QPushButton[sidebarItem="true"]:hover {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["sidebar_item_hover"]};
    border-left: 3px solid {COLORS["sidebar_category"]};
}}

QPushButton[sidebarActive="true"] {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["sidebar_item_active"]};
    border-left: 3px solid {COLORS["sidebar_category"]};
    font-weight: bold;
}}

/* ─── Top Tab Bar ─── */
#topTabBar {{
    background-color: {COLORS["nav_tab_bg"]};
    border-bottom: 2px solid {COLORS["border_dark"]};
}}

QPushButton#topTabBtn {{
    background-color: {COLORS["nav_tab_bg"]};
    color: {COLORS["nav_tab_text"]};
    border: none;
    border-bottom: 3px solid transparent;
    border-radius: 0;
    padding: 10px 20px;
    font-size: 11pt;
    font-weight: bold;
    letter-spacing: 1px;
}}

QPushButton#topTabBtn:hover {{
    background-color: {COLORS["nav_tab_hover_bg"]};
    color: {COLORS["text_bright"]};
}}

QPushButton#topTabBtn[active="true"] {{
    background-color: {COLORS["nav_tab_active_bg"]};
    color: {COLORS["nav_tab_active_text"]};
    border-bottom: 3px solid {COLORS["accent_gold"]};
}}

/* ─── Sub Navigation Bar ─── */
#subNavBar {{
    background-color: {COLORS["nav_sub_bg"]};
    border-bottom: 1px solid {COLORS["border_dark"]};
}}

QPushButton#subNavBtn {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
    padding: 4px 8px;
    font-weight: normal;
    min-height: 54px;
}}

QPushButton#subNavBtn:hover {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_bright"]};
}}

QPushButton#subNavBtn[active="true"] {{
    background-color: {COLORS["nav_sub_btn_active_bg"]};
    color: {COLORS["text_bright"]};
    border-bottom: 2px solid {COLORS["nav_sub_underline"]};
}}

/* ─── Detail Panel ─── */
#detailPanel {{
    background-color: {COLORS["detail_bg"]};
    border-left: 2px solid {COLORS["detail_border"]};
}}

QPushButton#detailFavBtn {{
    padding: 6px 10px;
}}

QPushButton#detailExcBtn {{
    padding: 6px 10px;
}}

QPushButton#detailBankBtn {{
    background-color: {COLORS["btn_action_bg"]};
    padding: 8px;
}}

QPushButton#detailBankBtn:hover {{
    background-color: {COLORS["btn_action_hover"]};
}}

/* ─── Dual Panel Widgets ─── */
QLabel#panelHeader {{
    color: {COLORS["accent_gold"]};
    font-size: 10pt;
    font-weight: bold;
    background-color: transparent;
}}

QPushButton#viewToggleBtn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border_dark"]};
    border-radius: 3px;
    font-size: 11pt;
    padding: 0;
}}

QPushButton#viewToggleBtn:checked {{
    background-color: {COLORS["accent_gold_dim"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["accent_gold"]};
}}

QPushButton#viewToggleBtn:hover {{
    background-color: {COLORS["bg_hover"]};
    color: {COLORS["text_primary"]};
}}

QPushButton#transferBtn {{
    background-color: {COLORS["bg_tertiary"]};
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border_primary"]};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 9pt;
}}

QPushButton#transferBtn:hover {{
    background-color: {COLORS["btn_action_bg"]};
    color: {COLORS["text_bright"]};
    border-color: {COLORS["accent_gold_dim"]};
}}
"""


# ── Helper Functions ─────────────────────────────────────────────────────────

def apply_theme(widget_or_app):
    """Apply the dark medieval theme QSS to a QApplication or QWidget."""
    widget_or_app.setStyleSheet(WARM_MEDIEVAL_QSS)


def get_qcolor(name: str) -> QColor:
    """Return a QColor from the COLORS dict by key name."""
    hex_color = COLORS.get(name, "#ffffff")
    return QColor(hex_color)
