"""
Simple i18n module for Varla-HUD.

Translates static UI text only (menus, buttons, labels, tooltips).
Does NOT translate data content (dump values, table rows, etc.).

Usage:
    from translations import tr
    label = QLabel(tr("Default dump path:"))
"""

import settings as app_settings

LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "es": "Español",
    "de": "Deutsch",
    "ja": "日本語",
}

# ── Translation dictionaries ────────────────────────────────────────────────
# Keys are English strings. Values are translated strings.

_FR = {
    # ── Menu bar ──
    "&File": "&Fichier",
    "&Open Save Dump...": "&Ouvrir un dump de sauvegarde...",
    "Open &Default Path": "Ouvrir le chemin par &défaut",
    "&Import...": "&Importer...",
    "Save &As...": "Enregistrer &sous...",
    "&Quit": "&Quitter",
    "&Settings": "&Paramètres",
    "&Game Version...": "&Version du jeu...",
    "&INI Editor...": "Éditeur &INI...",
    "&Language": "&Langue",

    # ── Game format dialog ──
    "Select Game Version": "Sélectionner la version du jeu",
    "Which version of Oblivion are you using?": "Quelle version d'Oblivion utilisez-vous ?",
    "Auto-detect": "Détection automatique",
    "Oblivion Remastered (obse64)": "Oblivion Remastered (obse64)",
    "Oblivion Classic (xOBSE)": "Oblivion Classic (xOBSE)",

    # ── Options bar ──
    "Default dump path:": "Chemin du dump par défaut :",
    "Change...": "Changer...",
    "Clear": "Effacer",
    "Ctrl+S:": "Ctrl+S :",
    "Direct Save": "Sauvegarde directe",
    "Import Filter": "Filtre d'import",

    # ── Options bar tooltip ──
    "Import Filter: Ctrl+S opens the Import window to\n"
    "select which staged items to export to target.txt.\n\n"
    "Direct Save: Ctrl+S writes all staged items directly\n"
    "to target.txt without the Import window.":
        "Filtre d'import : Ctrl+S ouvre la fenêtre d'import pour\n"
        "sélectionner les éléments à exporter vers target.txt.\n\n"
        "Sauvegarde directe : Ctrl+S écrit tous les éléments\n"
        "directement dans target.txt sans la fenêtre d'import.",

    # ── Transfer buttons ──
    "All →": "Tout →",
    "Sel →": "Sél →",
    "← Sel": "← Sél",
    "← All": "← Tout",
    "Clear Target": "Vider la cible",

    # ── Navigation tabs ──
    "Character": "Personnage",
    "Inventory": "Inventaire",
    "Magic": "Magie",
    "Quests": "Quêtes",
    "Varla": "Varla",

    # ── Character sub-pages ──
    "Character Info": "Info personnage",
    "Attributes": "Attributs",
    "Skills": "Compétences",
    "Factions": "Factions",
    "Details": "Détails",

    # ── Inventory sub-pages ──
    "Weapons": "Armes",
    "Gear": "Équipement",
    "Alchemy": "Alchimie",
    "Miscellaneous": "Divers",
    "All Items": "Tous les objets",

    # ── Magic sub-pages ──
    "Self": "Soi",
    "Touch": "Toucher",
    "Target": "Cible",
    "All": "Tout",
    "Active Effects": "Effets actifs",

    # ── Quests sub-pages ──
    "Active Quests": "Quêtes actives",
    "Completed Quests": "Quêtes terminées",

    # ── Varla sub-pages ──
    "Globals": "Globales",
    "Game Time": "Temps de jeu",
    "Plugins": "Plugins",
    "World State": "État du monde",

    # ── Import window ──
    "Import — Select items to export to target.txt": "Import — Sélectionner les éléments à exporter vers target.txt",
    "Available": "Disponible",
    "Staged for target.txt": "Prêt pour target.txt",
    "Write target.txt": "Écrire target.txt",
    "Close": "Fermer",

    # ── Status bar messages ──
    "Open a save dump to begin (File → Open Save Dump).": "Ouvrez un dump de sauvegarde pour commencer (Fichier → Ouvrir).",

    # ── Dual panel ──
    "Available ({count})": "Disponible ({count})",
    "Staged ({count})": "Prêt ({count})",
    "Search...": "Rechercher...",
}

_ES = {
    "&File": "&Archivo",
    "&Open Save Dump...": "&Abrir volcado de guardado...",
    "Open &Default Path": "Abrir ruta por &defecto",
    "&Import...": "&Importar...",
    "Save &As...": "Guardar &como...",
    "&Quit": "&Salir",
    "&Settings": "&Configuración",
    "&Game Version...": "&Versión del juego...",
    "&INI Editor...": "Editor &INI...",
    "&Language": "&Idioma",

    "Select Game Version": "Seleccionar versión del juego",
    "Which version of Oblivion are you using?": "¿Qué versión de Oblivion estás usando?",
    "Auto-detect": "Detección automática",
    "Oblivion Remastered (obse64)": "Oblivion Remastered (obse64)",
    "Oblivion Classic (xOBSE)": "Oblivion Classic (xOBSE)",

    "Default dump path:": "Ruta del volcado por defecto:",
    "Change...": "Cambiar...",
    "Clear": "Limpiar",
    "Ctrl+S:": "Ctrl+S:",
    "Direct Save": "Guardado directo",
    "Import Filter": "Filtro de importación",
    "Import Filter: Ctrl+S opens the Import window to\n"
    "select which staged items to export to target.txt.\n\n"
    "Direct Save: Ctrl+S writes all staged items directly\n"
    "to target.txt without the Import window.":
        "Filtro de importación: Ctrl+S abre la ventana de importación\n"
        "para seleccionar los elementos a exportar a target.txt.\n\n"
        "Guardado directo: Ctrl+S escribe todos los elementos\n"
        "directamente en target.txt sin la ventana de importación.",

    "All →": "Todo →",
    "Sel →": "Sel →",
    "← Sel": "← Sel",
    "← All": "← Todo",
    "Clear Target": "Vaciar objetivo",

    "Character": "Personaje",
    "Inventory": "Inventario",
    "Magic": "Magia",
    "Quests": "Misiones",
    "Varla": "Varla",

    "Character Info": "Info del personaje",
    "Attributes": "Atributos",
    "Skills": "Habilidades",
    "Factions": "Facciones",
    "Details": "Detalles",

    "Weapons": "Armas",
    "Gear": "Equipo",
    "Alchemy": "Alquimia",
    "Miscellaneous": "Miscelánea",
    "All Items": "Todos los objetos",

    "Self": "Propio",
    "Touch": "Toque",
    "Target": "Objetivo",
    "All": "Todos",
    "Active Effects": "Efectos activos",

    "Active Quests": "Misiones activas",
    "Completed Quests": "Misiones completadas",

    "Globals": "Globales",
    "Game Time": "Tiempo de juego",
    "Plugins": "Plugins",
    "World State": "Estado del mundo",

    "Import — Select items to export to target.txt": "Importar — Seleccionar elementos a exportar a target.txt",
    "Available": "Disponible",
    "Staged for target.txt": "Preparado para target.txt",
    "Write target.txt": "Escribir target.txt",
    "Close": "Cerrar",

    "Open a save dump to begin (File → Open Save Dump).": "Abra un volcado de guardado para comenzar (Archivo → Abrir).",
    "Available ({count})": "Disponible ({count})",
    "Staged ({count})": "Preparado ({count})",
    "Search...": "Buscar...",
}

_DE = {
    "&File": "&Datei",
    "&Open Save Dump...": "Speicherabbild &öffnen...",
    "Open &Default Path": "&Standardpfad öffnen",
    "&Import...": "&Importieren...",
    "Save &As...": "Speichern &unter...",
    "&Quit": "&Beenden",
    "&Settings": "&Einstellungen",
    "&Game Version...": "&Spielversion...",
    "&INI Editor...": "&INI-Editor...",
    "&Language": "&Sprache",

    "Select Game Version": "Spielversion auswählen",
    "Which version of Oblivion are you using?": "Welche Version von Oblivion verwenden Sie?",
    "Auto-detect": "Automatisch erkennen",
    "Oblivion Remastered (obse64)": "Oblivion Remastered (obse64)",
    "Oblivion Classic (xOBSE)": "Oblivion Classic (xOBSE)",

    "Default dump path:": "Standard-Dump-Pfad:",
    "Change...": "Ändern...",
    "Clear": "Löschen",
    "Ctrl+S:": "Strg+S:",
    "Direct Save": "Direktspeicherung",
    "Import Filter": "Importfilter",
    "Import Filter: Ctrl+S opens the Import window to\n"
    "select which staged items to export to target.txt.\n\n"
    "Direct Save: Ctrl+S writes all staged items directly\n"
    "to target.txt without the Import window.":
        "Importfilter: Strg+S öffnet das Importfenster zur\n"
        "Auswahl der zu exportierenden Elemente nach target.txt.\n\n"
        "Direktspeicherung: Strg+S schreibt alle Elemente\n"
        "direkt in target.txt ohne das Importfenster.",

    "All →": "Alle →",
    "Sel →": "Ausw →",
    "← Sel": "← Ausw",
    "← All": "← Alle",
    "Clear Target": "Ziel leeren",

    "Character": "Charakter",
    "Inventory": "Inventar",
    "Magic": "Magie",
    "Quests": "Quests",
    "Varla": "Varla",

    "Character Info": "Charakterinfo",
    "Attributes": "Attribute",
    "Skills": "Fertigkeiten",
    "Factions": "Fraktionen",
    "Details": "Details",

    "Weapons": "Waffen",
    "Gear": "Ausrüstung",
    "Alchemy": "Alchemie",
    "Miscellaneous": "Verschiedenes",
    "All Items": "Alle Gegenstände",

    "Self": "Selbst",
    "Touch": "Berührung",
    "Target": "Ziel",
    "All": "Alle",
    "Active Effects": "Aktive Effekte",

    "Active Quests": "Aktive Quests",
    "Completed Quests": "Abgeschlossene Quests",

    "Globals": "Globale",
    "Game Time": "Spielzeit",
    "Plugins": "Plugins",
    "World State": "Weltzustand",

    "Import — Select items to export to target.txt": "Import — Elemente zum Exportieren nach target.txt auswählen",
    "Available": "Verfügbar",
    "Staged for target.txt": "Bereit für target.txt",
    "Write target.txt": "target.txt schreiben",
    "Close": "Schließen",

    "Open a save dump to begin (File → Open Save Dump).": "Öffnen Sie ein Speicherabbild (Datei → Öffnen).",
    "Available ({count})": "Verfügbar ({count})",
    "Staged ({count})": "Bereit ({count})",
    "Search...": "Suchen...",
}

_JA = {
    "&File": "ファイル(&F)",
    "&Open Save Dump...": "セーブダンプを開く(&O)...",
    "Open &Default Path": "デフォルトパスを開く(&D)",
    "&Import...": "インポート(&I)...",
    "Save &As...": "名前を付けて保存(&A)...",
    "&Quit": "終了(&Q)",
    "&Settings": "設定(&S)",
    "&Game Version...": "ゲームバージョン(&G)...",
    "&INI Editor...": "INIエディタ(&I)...",
    "&Language": "言語(&L)",

    "Select Game Version": "ゲームバージョンの選択",
    "Which version of Oblivion are you using?": "どのバージョンのOblivionを使用していますか？",
    "Auto-detect": "自動検出",
    "Oblivion Remastered (obse64)": "Oblivion Remastered (obse64)",
    "Oblivion Classic (xOBSE)": "Oblivion Classic (xOBSE)",

    "Default dump path:": "デフォルトダンプパス：",
    "Change...": "変更...",
    "Clear": "クリア",
    "Ctrl+S:": "Ctrl+S：",
    "Direct Save": "直接保存",
    "Import Filter": "インポートフィルタ",
    "Import Filter: Ctrl+S opens the Import window to\n"
    "select which staged items to export to target.txt.\n\n"
    "Direct Save: Ctrl+S writes all staged items directly\n"
    "to target.txt without the Import window.":
        "インポートフィルタ：Ctrl+Sでインポートウィンドウを開き、\n"
        "target.txtにエクスポートする項目を選択します。\n\n"
        "直接保存：Ctrl+Sで全ての項目を\n"
        "インポートウィンドウなしでtarget.txtに書き込みます。",

    "All →": "全て →",
    "Sel →": "選択 →",
    "← Sel": "← 選択",
    "← All": "← 全て",
    "Clear Target": "ターゲットをクリア",

    "Character": "キャラクター",
    "Inventory": "所持品",
    "Magic": "魔法",
    "Quests": "クエスト",
    "Varla": "ヴァーラ",

    "Character Info": "キャラクター情報",
    "Attributes": "能力値",
    "Skills": "スキル",
    "Factions": "派閥",
    "Details": "詳細",

    "Weapons": "武器",
    "Gear": "装備",
    "Alchemy": "錬金術",
    "Miscellaneous": "雑貨",
    "All Items": "全アイテム",

    "Self": "自己",
    "Touch": "接触",
    "Target": "対象",
    "All": "全て",
    "Active Effects": "有効な効果",

    "Active Quests": "進行中のクエスト",
    "Completed Quests": "完了したクエスト",

    "Globals": "グローバル",
    "Game Time": "ゲーム時間",
    "Plugins": "プラグイン",
    "World State": "ワールド状態",

    "Import — Select items to export to target.txt": "インポート — target.txtにエクスポートする項目を選択",
    "Available": "利用可能",
    "Staged for target.txt": "target.txt用に準備済み",
    "Write target.txt": "target.txtに書き込む",
    "Close": "閉じる",

    "Open a save dump to begin (File → Open Save Dump).": "セーブダンプを開いて開始してください（ファイル → 開く）。",
    "Available ({count})": "利用可能 ({count})",
    "Staged ({count})": "準備済み ({count})",
    "Search...": "検索...",
}

_TRANSLATIONS = {
    "en": {},
    "fr": _FR,
    "es": _ES,
    "de": _DE,
    "ja": _JA,
}

_current_lang = "en"


def current_language() -> str:
    return _current_lang


def set_language(lang_code: str) -> None:
    global _current_lang
    if lang_code in _TRANSLATIONS:
        _current_lang = lang_code
        app_settings.set("language", lang_code)


def load_language() -> None:
    """Load saved language from settings."""
    global _current_lang
    saved = app_settings.get("language")
    if saved and saved in _TRANSLATIONS:
        _current_lang = saved


def tr(text: str, **kwargs) -> str:
    """Translate a UI string. Pass keyword args for {placeholders}."""
    if _current_lang != "en":
        table = _TRANSLATIONS.get(_current_lang, {})
        text = table.get(text, text)
    if kwargs:
        text = text.format(**kwargs)
    return text
