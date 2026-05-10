"""
Varla — Design System theme.
Parchment-on-dark, ornate, save-editor "glow up".

Token names (ink/brass/parchment/ember) come from the design handoff in
Varla/design_handoff_varla_glowup/. Legacy keys from the old amber/leather
palette are kept as aliases so other modules that still reference them
(e.g. preview/load-order tints) continue to work.
"""

from PySide6.QtGui import QColor


# ── Tokens ──────────────────────────────────────────────────────────────────
# Core palette — direct port of the design CSS variables.

INK_ABYSS      = "#0b0804"   # deepest bg, outside chrome
INK_VOID       = "#120d06"   # app bg
INK_LEATHER    = "#1a1208"   # panel bg
INK_LEATHER_2  = "#221708"   # raised panel / header
INK_OAK        = "#2a1c0c"   # border dark
INK_OAK_2      = "#3a2912"   # border mid

BRASS_DEEP     = "#6b4a1a"
BRASS          = "#9a6f2a"
BRASS_LIT      = "#c79443"
BRASS_BRIGHT   = "#e5b564"

PARCHMENT      = "#e7d2a0"
PARCHMENT_DIM  = "#b89a6a"
PARCHMENT_DIMR = "#8a7048"
PARCHMENT_MUTE = "#6b553a"

EMBER          = "#d87a2a"   # stage / active accent
EMBER_BRIGHT   = "#f0a050"
INK_BLOOD      = "#7a1f1a"   # destructive
INK_BLOOD_LIT  = "#b24a3a"

VERDIGRIS      = "#5a8a6e"   # magic / effect
SAPPHIRE       = "#3d5a8a"   # info


# ── Semantic colour map ──────────────────────────────────────────────────────
# Keys mirror the historical theme.COLORS dict so existing call-sites keep
# working; new keys are added for the glow-up. Use the constants above for
# new code, the dict for legacy compatibility.

COLORS = {
    # ── New (Varla glow-up) ──────────────────────────────────────────────
    "ink_abyss":        INK_ABYSS,
    "ink_void":         INK_VOID,
    "ink_leather":      INK_LEATHER,
    "ink_leather_2":    INK_LEATHER_2,
    "ink_oak":          INK_OAK,
    "ink_oak_2":        INK_OAK_2,
    "brass_deep":       BRASS_DEEP,
    "brass":            BRASS,
    "brass_lit":        BRASS_LIT,
    "brass_bright":     BRASS_BRIGHT,
    "parchment":        PARCHMENT,
    "parchment_dim":    PARCHMENT_DIM,
    "parchment_dimmer": PARCHMENT_DIMR,
    "parchment_mute":   PARCHMENT_MUTE,
    "ember":            EMBER,
    "ember_bright":     EMBER_BRIGHT,
    "ink_blood":        INK_BLOOD,
    "ink_blood_lit":    INK_BLOOD_LIT,
    "verdigris":        VERDIGRIS,
    "sapphire":         SAPPHIRE,

    # ── Legacy aliases (mapped onto the new palette) ─────────────────────
    "bg_primary":          INK_VOID,
    "bg_secondary":        INK_LEATHER,
    "bg_tertiary":         INK_LEATHER_2,
    "bg_input":            INK_ABYSS,
    "bg_hover":            INK_OAK,
    "bg_pressed":          INK_VOID,
    "bg_selected":         INK_OAK_2,

    "accent_gold":         BRASS_LIT,
    "accent_gold_dim":     BRASS_DEEP,
    "accent_gold_bright":  BRASS_BRIGHT,
    "accent_amber":        BRASS,
    "accent_copper":       EMBER,
    "accent":              BRASS_LIT,

    "text_primary":        PARCHMENT,
    "text_secondary":      PARCHMENT_DIM,
    "text_muted":          PARCHMENT_DIMR,
    "text_disabled":       PARCHMENT_MUTE,
    "text_bright":         "#f0d6a0",

    "border_primary":      INK_OAK,
    "border_light":        INK_OAK_2,
    "border_dark":         "#000000",
    "border_gold":         BRASS_DEEP,

    "btn_primary_bg":      INK_OAK,
    "btn_primary_hover":   INK_OAK_2,
    "btn_primary_pressed": INK_LEATHER,
    "btn_danger_bg":       INK_BLOOD,
    "btn_danger_hover":    INK_BLOOD_LIT,
    "btn_danger_pressed":  "#4a110e",
    "btn_danger_border":   INK_BLOOD_LIT,
    "btn_success_bg":      "#3a5828",
    "btn_success_hover":   "#4a6838",
    "btn_success_pressed": "#2a4818",
    "btn_action_bg":       INK_OAK,
    "btn_action_hover":    INK_OAK_2,
    "btn_action_pressed":  INK_LEATHER,

    "table_row_1":         INK_VOID,
    "table_row_2":         "#160f07",
    "table_header_bg":     INK_OAK,
    "table_header_text":   PARCHMENT_DIM,
    "table_grid":          INK_OAK,
    "table_selection":     "#332210",

    "favorite_row":        "#3a3518",
    "exception_row":       "#283828",
    "favorite_text":       BRASS_BRIGHT,
    "exception_text":      "#80b060",

    "star_active":         BRASS_BRIGHT,
    "star_inactive":       PARCHMENT_MUTE,
    "exception_active":    "#80b060",
    "exception_inactive":  PARCHMENT_MUTE,

    "tristate_neutral_bg":   INK_LEATHER,
    "tristate_neutral_fg":   PARCHMENT_DIMR,
    "tristate_approved_bg":  "#283828",
    "tristate_approved_fg":  "#80b060",
    "tristate_rejected_bg":  "#382020",
    "tristate_rejected_fg":  "#c06060",

    "scrollbar_bg":        INK_ABYSS,
    "scrollbar_handle":    INK_OAK_2,
    "scrollbar_hover":     "#4a3918",

    "sidebar_bg":          INK_ABYSS,
    "sidebar_item":        PARCHMENT,
    "sidebar_item_hover":  "#f0d6a0",
    "sidebar_item_active": BRASS_BRIGHT,
    "sidebar_category":    BRASS_LIT,
    "sidebar_separator":   INK_OAK,

    "nav_tab_bg":          INK_ABYSS,
    "nav_tab_text":        PARCHMENT_MUTE,
    "nav_tab_active_bg":   INK_LEATHER,
    "nav_tab_active_text": BRASS_BRIGHT,
    "nav_tab_hover_bg":    INK_LEATHER,

    "nav_sub_bg":          INK_LEATHER,
    "nav_sub_btn_bg":      "transparent",
    "nav_sub_btn_active_bg": INK_OAK,
    "nav_sub_underline":   BRASS_LIT,

    "detail_bg":           INK_LEATHER,
    "detail_border":       INK_OAK_2,

    "statusbar_bg":        INK_ABYSS,
    "statusbar_text":      PARCHMENT_MUTE,

    "toolbar_bg":          INK_ABYSS,
    "toolbar_border":      INK_OAK,

    "groupbox_border":     INK_OAK_2,
    "groupbox_title":      BRASS_LIT,

    "dialog_bg":           INK_LEATHER,
    "preview_approve":     "#283828",
    "preview_reject":      "#382020",
    "preview_select":      "#202838",

    "lom_green_bg":        "#283828",
    "lom_red_bg":           "#382020",
    "lom_green_fg":        "#80b060",
    "lom_gray_fg":         PARCHMENT_DIMR,
    "lom_info_bg":         INK_LEATHER_2,
    "lom_instruction_bg": "#222818",
}


# ── Global QSS Stylesheet ───────────────────────────────────────────────────
# Display font: EB Garamond if installed, otherwise system serif fallback.
# Body font: Inter Tight if installed, otherwise system sans-serif.
# Mono font: JetBrains Mono if installed, otherwise Consolas / system mono.

FF_DISPLAY = "'EB Garamond', 'Cormorant Garamond', 'Garamond', Georgia, serif"
FF_SCRIPT  = "'IM Fell English SC', 'EB Garamond', Georgia, serif"
FF_BODY    = "'Inter Tight', 'Segoe UI', 'Noto Sans', sans-serif"
FF_MONO    = "'JetBrains Mono', 'Consolas', 'Courier New', monospace"


WARM_MEDIEVAL_QSS = f"""

/* ─── Main Window / Generic ─── */
QMainWindow {{
    background-color: {INK_VOID};
    color: {PARCHMENT};
}}

QWidget {{
    background-color: {INK_VOID};
    color: {PARCHMENT};
    font-family: {FF_BODY};
    font-size: 10pt;
}}

QLabel {{
    color: {PARCHMENT};
    background-color: transparent;
}}

/* ─── Menu Bar (native QMenuBar) ─── */
QMenuBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_LEATHER_2}, stop:1 {INK_LEATHER});
    color: {PARCHMENT_DIM};
    border: none;
    border-bottom: 1px solid {INK_OAK_2};
    font-family: {FF_DISPLAY};
    font-size: 14px;
    padding: 2px 6px;
}}

QMenuBar::item {{
    background: transparent;
    color: {PARCHMENT_DIM};
    padding: 6px 12px;
    border-radius: 2px;
    spacing: 2px;
}}

QMenuBar::item:selected, QMenuBar::item:pressed {{
    background-color: {INK_OAK};
    color: {PARCHMENT};
}}

/* ─── Menu drop-downs ─── */
QMenu {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT};
    border: 1px solid {INK_OAK_2};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px;
    border-radius: 2px;
    background: transparent;
}}

QMenu::item:selected {{
    background-color: {INK_OAK_2};
    color: {BRASS_BRIGHT};
}}

QMenu::separator {{
    height: 1px;
    background-color: {INK_OAK};
    margin: 4px 8px;
}}

/* ─── Toolbar (legacy, kept for INI editor / dialogs) ─── */
QToolBar {{
    background-color: {INK_ABYSS};
    border-bottom: 1px solid {INK_OAK};
    spacing: 6px;
    padding: 4px;
}}

QToolBar QLabel {{
    color: {PARCHMENT};
    padding: 0 4px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {INK_OAK_2};
    margin: 4px 6px;
}}

/* ─── Buttons (default — used by dialogs) ─── */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    color: {PARCHMENT};
    border: 1px solid {INK_OAK_2};
    border-top-color: {INK_OAK_2};
    border-bottom-color: {INK_ABYSS};
    border-radius: 2px;
    padding: 5px 12px;
    font-family: {FF_BODY};
    font-size: 12px;
    min-height: 20px;
}}

QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    color: {BRASS_BRIGHT};
    border-color: {BRASS_DEEP};
}}

QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_LEATHER}, stop:1 {INK_OAK});
}}

QPushButton:disabled {{
    color: {PARCHMENT_MUTE};
    background-color: {INK_LEATHER};
    border-color: {INK_OAK};
}}

/* Variants by objectName */
QPushButton#deleteBtn, QPushButton#dangerBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_BLOOD}, stop:1 #4a110e);
    color: #f0d6b8;
    border: 1px solid {INK_BLOOD_LIT};
}}

QPushButton#deleteBtn:hover, QPushButton#dangerBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_BLOOD_LIT}, stop:1 {INK_BLOOD});
    color: #ffffff;
}}

QPushButton#loadLatestBtn,
QPushButton#loadBtn,
QPushButton#generateBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    color: {PARCHMENT};
    border: 1px solid {BRASS_DEEP};
    font-weight: 600;
    padding: 6px 12px;
}}

QPushButton#loadLatestBtn:hover,
QPushButton#loadBtn:hover,
QPushButton#generateBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRASS_DEEP}, stop:1 {INK_OAK_2});
    color: {BRASS_BRIGHT};
}}

/* ─── Line Edits / SpinBoxes / ComboBoxes ─── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {INK_ABYSS};
    color: {PARCHMENT};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    padding: 4px 8px;
    selection-background-color: {BRASS_DEEP};
    selection-color: {PARCHMENT};
}}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {BRASS_DEEP};
    border-width: 1px;
}}

QSpinBox::up-button, QDoubleSpinBox::up-button {{
    background-color: {INK_OAK};
    border-left: 1px solid {INK_OAK_2};
    border-bottom: 1px solid {INK_OAK_2};
    width: 14px;
}}

QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {INK_OAK};
    border-left: 1px solid {INK_OAK_2};
    width: 14px;
}}

QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {INK_OAK_2};
}}

QComboBox::drop-down {{
    border-left: 1px solid {INK_OAK_2};
    background-color: {INK_OAK};
    width: 18px;
}}

QComboBox QAbstractItemView {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT};
    border: 1px solid {INK_OAK_2};
    selection-background-color: {INK_OAK_2};
    selection-color: {BRASS_BRIGHT};
}}

/* ─── Tables ─── */
QTableWidget, QTableView {{
    background-color: {INK_VOID};
    alternate-background-color: {INK_LEATHER};
    color: {PARCHMENT};
    gridline-color: {INK_OAK};
    border: 1px solid {INK_OAK_2};
    selection-background-color: {INK_OAK_2};
    selection-color: {BRASS_BRIGHT};
    font-family: {FF_BODY};
    font-size: 12px;
}}

QTableWidget::item, QTableView::item {{
    padding: 4px 8px;
    border: none;
}}

QTableWidget::item:hover, QTableView::item:hover {{
    background-color: rgba(154, 111, 42, 0.08);
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {INK_OAK_2};
    color: {BRASS_BRIGHT};
}}

QHeaderView {{
    background-color: {INK_OAK};
}}

QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    color: {PARCHMENT_DIM};
    padding: 6px 10px;
    border: none;
    border-right: 1px solid {INK_OAK};
    border-bottom: 1px solid {BRASS_DEEP};
    font-family: {FF_DISPLAY};
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 1px;
}}

QHeaderView::section:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
}}

/* ─── Scroll Bars ─── */
QScrollBar:vertical {{
    background-color: {INK_ABYSS};
    width: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    min-height: 30px;
    border: 1px solid {INK_OAK};
    border-radius: 2px;
    margin: 1px;
}}

QScrollBar::handle:vertical:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4a3918, stop:1 {INK_OAK_2});
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {INK_ABYSS};
    height: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    min-width: 30px;
    border: 1px solid {INK_OAK};
    border-radius: 2px;
    margin: 1px;
}}

QScrollBar::handle:horizontal:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a3918, stop:1 {INK_OAK_2});
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ─── GroupBox ─── */
QGroupBox {{
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    margin-top: 12px;
    padding-top: 16px;
    font-family: {FF_DISPLAY};
    color: {BRASS_LIT};
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: {BRASS_LIT};
}}

/* ─── Text Edit / List Widget ─── */
QTextEdit {{
    background-color: {INK_ABYSS};
    color: {PARCHMENT};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    selection-background-color: {BRASS_DEEP};
    font-family: {FF_MONO};
    font-size: 11px;
}}

QListWidget {{
    background-color: {INK_VOID};
    color: {PARCHMENT};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
}}

QListWidget::item {{
    padding: 4px;
}}

QListWidget::item:selected {{
    background-color: {INK_OAK_2};
    color: {BRASS_BRIGHT};
}}

QListWidget::item:hover {{
    background-color: {INK_OAK};
}}

/* ─── Tab Widget (sub-dialog tabs only — not the primary nav) ─── */
QTabWidget::pane {{
    background-color: {INK_LEATHER};
    border: 1px solid {INK_OAK_2};
    border-top: none;
}}

QTabBar::tab {{
    background-color: {INK_OAK};
    color: {PARCHMENT_DIM};
    border: 1px solid {INK_OAK_2};
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 2px;
    border-top-right-radius: 2px;
    font-family: {FF_BODY};
}}

QTabBar::tab:selected {{
    background-color: {INK_LEATHER};
    color: {BRASS_LIT};
    border-bottom: 2px solid {BRASS_LIT};
}}

QTabBar::tab:hover:!selected {{
    background-color: {INK_OAK_2};
    color: {PARCHMENT};
}}

/* ─── Scroll Area ─── */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

/* ─── ToolTip ─── */
QToolTip {{
    background-color: {INK_VOID};
    color: {BRASS_BRIGHT};
    border: 1px solid {BRASS_DEEP};
    border-radius: 2px;
    padding: 7px 14px;
    font-family: {FF_DISPLAY};
    font-size: 12pt;
    letter-spacing: 1px;
}}

/* ─── Status Bar (native) ─── */
QStatusBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_ABYSS}, stop:1 {INK_VOID});
    color: {PARCHMENT_DIMR};
    border-top: 1px solid {INK_OAK_2};
    font-family: {FF_BODY};
    font-size: 11px;
}}

/* ─── Splitter ─── */
QSplitter::handle {{
    background-color: {INK_OAK};
    width: 1px;
}}

QSplitter::handle:hover {{
    background-color: {BRASS_DEEP};
}}

/* ─── CheckBox ─── */
QCheckBox {{
    color: {PARCHMENT};
    spacing: 8px;
    background-color: transparent;
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    background-color: {INK_ABYSS};
}}

QCheckBox::indicator:checked {{
    background-color: {BRASS_DEEP};
    border-color: {BRASS};
}}

QCheckBox::indicator:hover {{
    border-color: {BRASS_DEEP};
}}

/* ─── Dialogs ─── */
QDialog {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT};
}}

QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

QFormLayout QLabel {{
    color: {PARCHMENT_DIM};
    font-weight: 500;
}}

QMessageBox {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT};
}}

QMessageBox QLabel {{
    color: {PARCHMENT};
}}

QInputDialog {{
    background-color: {INK_LEATHER};
}}

#gameModeCombo {{
    font-family: {FF_DISPLAY};
    font-size: 12pt;
    padding: 4px 8px;
    min-width: 200px;
}}

QLabel#pathDisplay {{
    background-color: {INK_ABYSS};
    padding: 5px;
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    color: {PARCHMENT_DIM};
    font-family: {FF_MONO};
}}

QLabel#appTitle {{
    color: {BRASS_LIT};
    font-family: {FF_DISPLAY};
    font-size: 16pt;
    font-weight: 600;
    background-color: transparent;
    letter-spacing: 2px;
}}

QLabel#bankHeader {{
    font-family: {FF_DISPLAY};
    font-weight: 600;
    font-size: 12pt;
    color: {BRASS};
}}

/* ─── Sidebar buttons (legacy) ─── */
QPushButton[sidebarItem="true"] {{
    background-color: transparent;
    color: {PARCHMENT};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    text-align: left;
    padding: 7px 12px 7px 16px;
    font-weight: normal;
    font-size: 10pt;
}}

QPushButton[sidebarItem="true"]:hover {{
    background-color: {INK_OAK};
    color: {BRASS_BRIGHT};
    border-left: 3px solid {BRASS_LIT};
}}

QPushButton[sidebarActive="true"] {{
    background-color: {INK_OAK};
    color: {BRASS_BRIGHT};
    border-left: 3px solid {BRASS_LIT};
    font-weight: 600;
}}

/* ─── Top Tab Bar (primary nav) ─── */
#topTabBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_ABYSS}, stop:1 {INK_VOID});
    border-top: none;
    border-bottom: 1px solid #000000;
}}

QPushButton#topTabBtn {{
    background-color: transparent;
    color: {PARCHMENT_DIMR};
    border: none;
    border-right: 1px solid {INK_OAK};
    border-radius: 0;
    padding: 0 14px;
    font-family: {FF_DISPLAY};
    font-size: 14pt;
    font-weight: 500;
    letter-spacing: 2px;
    text-align: center;
}}

QPushButton#topTabBtn:hover {{
    background-color: rgba(154, 111, 42, 0.06);
    color: {PARCHMENT_DIM};
}}

QPushButton#topTabBtn[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(201, 148, 67, 0.20),
        stop:0.8 rgba(26, 18, 8, 0));
    color: {BRASS_BRIGHT};
}}

/* ─── Sub Navigation Bar (chapter pills) ─── */
#subNavBar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_LEATHER}, stop:1 {INK_VOID});
    border-bottom: 1px solid {INK_OAK};
}}

QPushButton#subNavBtn {{
    background-color: transparent;
    color: {PARCHMENT_DIM};
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 4px 12px 4px 8px;
    font-family: {FF_DISPLAY};
    font-size: 11pt;
    font-weight: 400;
    letter-spacing: 1px;
    text-align: left;
    min-height: 24px;
}}

QPushButton#subNavBtn:hover {{
    background-color: {INK_LEATHER};
    border-color: {INK_OAK_2};
    color: {PARCHMENT};
}}

QPushButton#subNavBtn[active="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    border-color: {BRASS_DEEP};
    color: {BRASS_BRIGHT};
}}

QLabel#chapterNum {{
    background-color: {INK_ABYSS};
    border: 1px solid {INK_OAK_2};
    border-radius: 9px;
    color: {PARCHMENT_DIMR};
    font-family: {FF_MONO};
    font-size: 9pt;
    min-width: 16px;
    max-width: 16px;
    min-height: 16px;
    max-height: 16px;
    qproperty-alignment: AlignCenter;
}}

QLabel#chapterNumActive {{
    background-color: {BRASS_DEEP};
    border: 1px solid {BRASS};
    border-radius: 9px;
    color: #f0d6b8;
    font-family: {FF_MONO};
    font-size: 9pt;
    min-width: 16px;
    max-width: 16px;
    min-height: 16px;
    max-height: 16px;
    qproperty-alignment: AlignCenter;
}}

/* ─── Doc Strip (was options bar) ─── */
QFrame#options_bar, QFrame#docStrip {{
    background-color: {INK_ABYSS};
    border-top: 1px solid {INK_OAK};
    border-bottom: 1px solid #000000;
}}

QLabel#options_label, QLabel#docLabel {{
    color: {PARCHMENT_DIMR};
    font-family: {FF_DISPLAY};
    font-size: 10pt;
    letter-spacing: 2px;
}}

QLabel#options_path, QLabel#docPath {{
    background-color: {INK_VOID};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    color: {PARCHMENT_DIM};
    font-family: {FF_MONO};
    font-size: 10pt;
    padding: 3px 10px;
}}

QFrame#options_sep, QFrame#docSep {{
    color: {INK_OAK};
    background-color: {INK_OAK};
    max-width: 1px;
}}

/* Compact ghost buttons used by the doc strip */
QPushButton#options_btn, QPushButton#docGhostBtn {{
    background: transparent;
    color: {PARCHMENT_DIM};
    border: 1px solid transparent;
    border-radius: 2px;
    padding: 3px 10px;
    font-family: {FF_BODY};
    font-size: 11px;
    min-height: 18px;
}}

QPushButton#options_btn:hover, QPushButton#docGhostBtn:hover {{
    background-color: {INK_LEATHER};
    border-color: {INK_OAK_2};
    color: {PARCHMENT};
}}

QPushButton#options_fmt_btn {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT_DIM};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    font-family: {FF_BODY};
    font-size: 11px;
    padding: 3px 10px;
}}

QPushButton#options_fmt_btn:hover {{
    background-color: {INK_OAK};
    color: {BRASS_BRIGHT};
    border-color: {BRASS_DEEP};
}}

QPushButton#options_fmt_btn:checked {{
    background-color: {INK_OAK_2};
    color: {BRASS_BRIGHT};
    border-color: {BRASS_DEEP};
    font-weight: 600;
}}

QPushButton#options_export_btn {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT_DIMR};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    font-family: {FF_BODY};
    font-size: 11px;
    padding: 3px 10px;
}}

QPushButton#options_export_btn:hover {{
    background-color: {INK_OAK};
    color: {PARCHMENT};
    border-color: {BRASS_DEEP};
}}

QPushButton#options_export_btn:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRASS_LIT}, stop:1 {BRASS});
    color: {INK_LEATHER};
    border-color: {BRASS_BRIGHT};
    font-weight: 600;
}}

/* Primary "Write target.txt" style action button */
QPushButton#docPrimaryBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRASS_LIT}, stop:1 {BRASS});
    color: {INK_LEATHER};
    border: 1px solid {BRASS_BRIGHT};
    border-top-color: #f0d6a0;
    border-bottom-color: {BRASS_DEEP};
    border-radius: 2px;
    padding: 4px 14px;
    font-family: {FF_BODY};
    font-size: 11px;
    font-weight: 700;
    min-height: 18px;
}}

QPushButton#docPrimaryBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {BRASS_BRIGHT}, stop:1 {BRASS_LIT});
    color: {INK_ABYSS};
}}

QPushButton#docPrimaryBtn:disabled {{
    background-color: {INK_LEATHER};
    color: {PARCHMENT_MUTE};
    border-color: {INK_OAK_2};
}}

/* ─── Detail Panel ─── */
#detailPanel {{
    background-color: {INK_LEATHER};
    border-left: 1px solid {INK_OAK_2};
}}

QPushButton#detailFavBtn,
QPushButton#detailExcBtn {{
    padding: 6px 10px;
}}

QPushButton#detailBankBtn {{
    background-color: {INK_OAK_2};
    color: {PARCHMENT};
    padding: 8px;
    border: 1px solid {BRASS_DEEP};
}}

QPushButton#detailBankBtn:hover {{
    background-color: {BRASS_DEEP};
    color: {BRASS_BRIGHT};
}}

/* ─── Dual Panel Widgets ─── */
QFrame#varlaPanel {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_LEATHER}, stop:1 {INK_VOID});
    border: 1px solid {INK_OAK_2};
}}

QFrame#varlaPanelHeader {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    border-bottom: 1px solid {INK_OAK_2};
}}

QFrame#varlaPanelHeader[panelKind="staged"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    border-bottom: 1px solid {BRASS_DEEP};
}}

QLabel#panelHeader {{
    color: {BRASS_LIT};
    font-family: {FF_DISPLAY};
    font-size: 13pt;
    font-weight: 500;
    background-color: transparent;
    letter-spacing: 3px;
}}

QLabel#panelHeader[panelKind="staged"] {{
    color: {EMBER_BRIGHT};
}}

QLabel#counterLabel {{
    background-color: {INK_ABYSS};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    color: {PARCHMENT_DIM};
    font-family: {FF_MONO};
    font-size: 10pt;
    padding: 2px 8px;
}}

QLabel#counterLabel[panelKind="staged"] {{
    color: {EMBER};
    border-color: {BRASS_DEEP};
}}

QFrame#varlaSearchRow {{
    background-color: {INK_VOID};
    border-bottom: 1px solid {INK_OAK};
}}

QLineEdit#searchBar {{
    background-color: {INK_ABYSS};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    padding: 5px 10px;
    color: {PARCHMENT};
    font-family: {FF_BODY};
    font-size: 12px;
}}

QLineEdit#searchBar:focus {{
    border-color: {BRASS_DEEP};
}}

QPushButton#viewToggleBtn {{
    background-color: {INK_OAK};
    color: {PARCHMENT_DIM};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    font-family: {FF_DISPLAY};
    font-size: 11pt;
    padding: 0;
    min-height: 22px;
}}

QPushButton#viewToggleBtn:checked {{
    background-color: {INK_OAK_2};
    color: {BRASS_BRIGHT};
    border-color: {BRASS_DEEP};
}}

QPushButton#viewToggleBtn:hover {{
    background-color: {INK_OAK_2};
    color: {PARCHMENT};
}}

/* ─── Transfer column (centre) ─── */
QFrame#xferColumn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_ABYSS}, stop:0.5 {INK_VOID}, stop:1 {INK_ABYSS});
    border-left: 1px solid {INK_OAK};
    border-right: 1px solid {INK_OAK};
}}

QLabel#xferGroupLabel {{
    color: {PARCHMENT_MUTE};
    font-family: {FF_DISPLAY};
    font-size: 9pt;
    letter-spacing: 2px;
    background-color: transparent;
    qproperty-alignment: AlignCenter;
}}

QPushButton#xferBtn {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    color: {PARCHMENT_DIM};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    font-family: {FF_DISPLAY};
    font-size: 11pt;
    font-weight: 500;
    letter-spacing: 1px;
    padding: 6px 4px;
}}

QPushButton#xferBtn:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    border-color: {BRASS};
    color: {BRASS_BRIGHT};
}}

QPushButton#xferBtn:disabled {{
    color: {PARCHMENT_MUTE};
    border-color: {INK_OAK};
    background-color: {INK_LEATHER};
}}

QPushButton#xferBtnStrong {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    color: {BRASS_BRIGHT};
    border: 1px solid {BRASS_DEEP};
    border-radius: 2px;
    font-family: {FF_DISPLAY};
    font-size: 11pt;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 6px 4px;
}}

QPushButton#xferBtnStrong:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK_2}, stop:1 {INK_OAK});
    border-color: {BRASS};
    color: #f0d6b8;
}}

QPushButton#xferBtnDanger {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_OAK}, stop:1 {INK_LEATHER});
    color: #c08878;
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    font-family: {FF_DISPLAY};
    font-size: 11pt;
    font-weight: 500;
    letter-spacing: 1px;
    padding: 6px 4px;
}}

QPushButton#xferBtnDanger:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4a1a14, stop:1 #2a1208);
    border-color: {INK_BLOOD_LIT};
    color: #f0d6b8;
}}

/* legacy transferBtn alias */
QPushButton#transferBtn {{
    background-color: {INK_OAK};
    color: {PARCHMENT_DIM};
    border: 1px solid {INK_OAK_2};
    border-radius: 2px;
    padding: 4px 8px;
    font-family: {FF_BODY};
    font-size: 10pt;
}}

QPushButton#transferBtn:hover {{
    background-color: {INK_OAK_2};
    color: {BRASS_BRIGHT};
    border-color: {BRASS_DEEP};
}}

/* ─── Varla custom status bar (replacement) ─── */
QFrame#varlaStatus {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {INK_ABYSS}, stop:1 {INK_VOID});
    border-top: 1px solid {INK_OAK_2};
}}

QLabel#statusKey {{
    color: {PARCHMENT_MUTE};
    font-family: {FF_BODY};
    font-size: 10pt;
    letter-spacing: 1px;
    background-color: transparent;
}}

QLabel#statusVal {{
    color: {PARCHMENT_DIM};
    font-family: {FF_MONO};
    font-size: 10pt;
    background-color: transparent;
}}

QLabel#statusValEmber {{
    color: {EMBER};
    font-family: {FF_MONO};
    font-size: 10pt;
    background-color: transparent;
}}

QFrame#statusSep {{
    background-color: {INK_OAK_2};
    max-width: 1px;
    min-width: 1px;
}}
"""


# ── Helpers ─────────────────────────────────────────────────────────────────

def apply_theme(widget_or_app):
    """Apply the dark medieval theme QSS to a QApplication or QWidget."""
    widget_or_app.setStyleSheet(WARM_MEDIEVAL_QSS)


def get_qcolor(name: str) -> QColor:
    """Return a QColor from the COLORS dict by key name."""
    hex_color = COLORS.get(name, "#ffffff")
    return QColor(hex_color)
