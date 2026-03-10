"""
Varla-HUD — Oblivion Remastered Save Dump Editor

Dual-panel drag-and-drop architecture:
  Left panel  = all items from the loaded save dump (source)
  Right panel = staged items that get written to the output dump on save
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QStackedWidget, QStatusBar,
    QPushButton, QLabel, QFrame,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt

from theme import apply_theme, COLORS
from navigation import NavigationWidget, NAVIGATION_STRUCTURE, TAB_ORDER
from dual_panel import DualPanelWidget
from panel_defs import get_columns, extract_items, build_staged_filter
from models import CharacterData
from save_dump_parser import parse_save_dump, SaveDumpParser, ClassicSaveDumpParser
from save_dump_writer import SaveDumpWriter
from import_window import ImportWindow
from import_generator import ImportLogGenerator
from varla_ini_editor import DEFAULT_INI_PATH, parse_ini, write_ini
import settings as app_settings


class VarlaHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Varla-HUD")
        self.resize(1400, 900)

        app_settings.load()

        self._char_data: Optional[CharacterData] = None
        self._dump_path: Optional[Path] = None
        self._panels: dict[str, DualPanelWidget] = {}
        self._page_map: dict[str, int] = {}

        self._build_menu()
        self._build_ui()
        apply_theme(self)

    # ── Menu ─────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu("&File")

        open_act = QAction("&Open Save Dump...", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self._open_dump)
        file_menu.addAction(open_act)

        self._open_default_act = QAction("Open &Default Path", self)
        self._open_default_act.setShortcut(QKeySequence("Ctrl+R"))
        self._open_default_act.triggered.connect(self._open_default_dump)
        file_menu.addAction(self._open_default_act)

        file_menu.addSeparator()

        self._import_act = QAction("&Import...", self)
        self._import_act.setShortcut(QKeySequence.Save)
        self._import_act.setEnabled(False)
        self._import_act.triggered.connect(self._open_import_window)
        file_menu.addAction(self._import_act)

        self._save_as_act = QAction("Save &As...", self)
        self._save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._save_as_act.setEnabled(False)
        self._save_as_act.triggered.connect(self._save_dump_as)
        file_menu.addAction(self._save_as_act)

        file_menu.addSeparator()

        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

    # ── UI ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Navigation bar (top tabs + sub-nav)
        self._nav = NavigationWidget()
        self._nav.page_selected.connect(self._show_page)
        root.addWidget(self._nav)

        # Options toolbar strip
        root.addWidget(self._build_options_bar())

        # Page stack — one DualPanelWidget per sub-page
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        for tab_key in TAB_ORDER:
            for page in NAVIGATION_STRUCTURE[tab_key]["sub_pages"]:
                page_key = page["key"]
                cols = get_columns(page_key)
                panel = DualPanelWidget(columns=cols)
                idx = self._stack.addWidget(panel)
                self._page_map[page_key] = idx
                self._panels[page_key] = panel

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Open a save dump to begin (File → Open Save Dump).")

        # Show first page
        self._nav.initialize()

    def _build_options_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("options_bar")
        bar.setFixedHeight(32)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(6)

        # Default path section
        path_label = QLabel("Default dump path:")
        path_label.setObjectName("options_label")
        layout.addWidget(path_label)

        self._default_path_lbl = QLabel(self._get_default_path_display())
        self._default_path_lbl.setObjectName("options_path")
        self._default_path_lbl.setMinimumWidth(200)
        layout.addWidget(self._default_path_lbl)

        change_btn = QPushButton("Change...")
        change_btn.setObjectName("options_btn")
        change_btn.setFixedWidth(70)
        change_btn.clicked.connect(self._change_default_path)
        layout.addWidget(change_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("options_btn")
        clear_btn.setFixedWidth(50)
        clear_btn.clicked.connect(self._clear_default_path)
        layout.addWidget(clear_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("options_sep")
        layout.addWidget(sep)

        # Game format section
        fmt_label = QLabel("Game format:")
        fmt_label.setObjectName("options_label")
        layout.addWidget(fmt_label)

        current_fmt = app_settings.get("game_format") or "auto"

        self._fmt_auto_btn = QPushButton("Auto-detect")
        self._fmt_auto_btn.setObjectName("options_fmt_btn")
        self._fmt_auto_btn.setCheckable(True)
        self._fmt_auto_btn.setFixedWidth(90)
        self._fmt_auto_btn.clicked.connect(lambda: self._set_game_format("auto"))
        layout.addWidget(self._fmt_auto_btn)

        self._fmt_rem_btn = QPushButton("Remastered")
        self._fmt_rem_btn.setObjectName("options_fmt_btn")
        self._fmt_rem_btn.setCheckable(True)
        self._fmt_rem_btn.setFixedWidth(90)
        self._fmt_rem_btn.clicked.connect(lambda: self._set_game_format("remastered"))
        layout.addWidget(self._fmt_rem_btn)

        self._fmt_cls_btn = QPushButton("Classic (xOBSE)")
        self._fmt_cls_btn.setObjectName("options_fmt_btn")
        self._fmt_cls_btn.setCheckable(True)
        self._fmt_cls_btn.setFixedWidth(120)
        self._fmt_cls_btn.clicked.connect(lambda: self._set_game_format("classic"))
        layout.addWidget(self._fmt_cls_btn)

        self._update_format_buttons(current_fmt)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setObjectName("options_sep")
        layout.addWidget(sep2)

        # [SaveDump] export master toggle
        export_lbl = QLabel("[SaveDump]")
        export_lbl.setObjectName("options_label")
        layout.addWidget(export_lbl)

        self._export_toggle_btn = QPushButton("Export: ON")
        self._export_toggle_btn.setObjectName("options_export_btn")
        self._export_toggle_btn.setCheckable(True)
        self._export_toggle_btn.setFixedWidth(100)
        self._export_toggle_btn.setToolTip(
            "bExportEnabled in varla.ini — master switch.\n"
            "OFF prevents any dump from being written on save,\n"
            "protecting your existing save_dump.txt."
        )
        self._export_toggle_btn.clicked.connect(self._toggle_export_enabled)
        layout.addWidget(self._export_toggle_btn)
        self._refresh_export_btn()

        layout.addStretch()
        return bar

    def _get_default_path_display(self) -> str:
        p = app_settings.get("default_dump_path") or ""
        return p if p else "(not set)"

    def _change_default_path(self):
        current = app_settings.get("default_dump_path") or ""
        start = str(Path(current).parent) if current else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Set Default Dump Path", start, "Text Files (*.txt);;All Files (*)"
        )
        if path:
            app_settings.set("default_dump_path", path)
            self._default_path_lbl.setText(path)

    def _clear_default_path(self):
        app_settings.set("default_dump_path", "")
        self._default_path_lbl.setText("(not set)")

    def _refresh_export_btn(self):
        try:
            values = parse_ini(DEFAULT_INI_PATH)
            enabled = values.get("bExportEnabled", 1) == 1
        except Exception:
            enabled = True
        self._export_toggle_btn.setChecked(enabled)
        self._export_toggle_btn.setText("Export: ON" if enabled else "Export: OFF")

    def _toggle_export_enabled(self, checked: bool):
        self._export_toggle_btn.setText("Export: ON" if checked else "Export: OFF")
        try:
            values = parse_ini(DEFAULT_INI_PATH)
            values["bExportEnabled"] = 1 if checked else 0
            write_ini(DEFAULT_INI_PATH, values)
        except Exception as e:
            self._status.showMessage(f"Could not update varla.ini: {e}", 5000)

    def _set_game_format(self, fmt: str):
        app_settings.set("game_format", fmt)
        self._update_format_buttons(fmt)
        if self._dump_path:
            self._reload_dump_with_format(fmt)

    def _update_format_buttons(self, fmt: str):
        self._fmt_auto_btn.setChecked(fmt == "auto")
        self._fmt_rem_btn.setChecked(fmt == "remastered")
        self._fmt_cls_btn.setChecked(fmt == "classic")

    def _reload_dump_with_format(self, fmt: str):
        try:
            if fmt == "classic":
                char_data = ClassicSaveDumpParser(self._dump_path).parse()
            elif fmt == "remastered":
                char_data = SaveDumpParser(self._dump_path).parse()
            else:
                char_data = parse_save_dump(self._dump_path)
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to re-parse with {fmt} format:\n{e}")
            return
        self._char_data = char_data
        self._populate_all_panels()
        self._status.showMessage(
            f"Reloaded: {self._dump_path.name}  [{char_data.dump_format or fmt}]"
        )

    # ── Navigation ───────────────────────────────────────────────────────

    def _show_page(self, page_key: str):
        idx = self._page_map.get(page_key)
        if idx is not None:
            self._stack.setCurrentIndex(idx)

    # ── File operations ──────────────────────────────────────────────────

    def _open_default_dump(self):
        path = app_settings.get("default_dump_path") or ""
        if not path or not Path(path).exists():
            QMessageBox.warning(
                self, "No Default Path",
                "No default dump path is set or the file no longer exists.\n"
                "Use the options bar to set one."
            )
            return
        self._load_path(path)

    def _open_dump(self):
        default = app_settings.get("default_dump_path") or ""
        start_dir = str(Path(default).parent) if default else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Save Dump", start_dir, "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        self._load_path(path)

    def _load_path(self, path: str):
        fmt = app_settings.get("game_format") or "auto"
        try:
            if fmt == "classic":
                char_data = ClassicSaveDumpParser(Path(path)).parse()
            elif fmt == "remastered":
                char_data = SaveDumpParser(Path(path)).parse()
            else:
                char_data = parse_save_dump(Path(path))
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to parse save dump:\n{e}")
            return

        self._char_data = char_data
        self._dump_path = Path(path)
        self._populate_all_panels()

        self._import_act.setEnabled(True)
        self._save_as_act.setEnabled(True)
        detected = char_data.dump_format or fmt
        self._status.showMessage(f"Loaded: {path}  [{detected}]")
        self.setWindowTitle(f"Varla-HUD — {Path(path).name}")

    def _populate_all_panels(self):
        if not self._char_data:
            return
        for page_key, panel in self._panels.items():
            items = extract_items(page_key, self._char_data)
            panel.set_items(items)

    def _open_import_window(self):
        if not self._char_data or not self._dump_path:
            return
        # Collect all staged PanelItems from the main panels (deduped by uid)
        staged: list = []
        seen: set = set()
        for panel in self._panels.values():
            for pi in panel.get_staged_items():
                if pi.uid not in seen:
                    seen.add(pi.uid)
                    staged.append(pi)
        if not staged:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "Nothing staged",
                "Stage some items in the main panels first, then open Import."
            )
            return
        win = ImportWindow(staged, self._char_data, self._dump_path, parent=self)
        win.exec()

    def _save_dump(self):
        if not self._dump_path:
            self._save_dump_as()
            return
        target_path = self._dump_path.parent / "target.txt"
        if self._char_data and self._char_data.dump_format == "classic":
            self._save_dump_classic(target_path)
        else:
            self._do_save(target_path)

    def _save_dump_classic(self, target_path: Path):
        """Write target.txt in classic xOBSE command format."""
        if not self._char_data:
            return
        if target_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = target_path.with_suffix(f".{ts}.bak")
            shutil.copy2(target_path, backup)
        try:
            sf = build_staged_filter(self._panels, self._char_data)
            cd = self._char_data

            from models import CharacterData as _CD
            filtered = _CD()
            filtered.character = cd.character
            filtered.dump_format = "classic"

            export_options = {
                "character": False, "attributes": False, "skills": False,
                "statistics": False, "factions": False, "items": False,
                "spells": False, "completedQuests": False,
                "vitals": False, "resistances": False,
                "globalVariables": False, "gameTime": False,
            }
            if sf.include_char_info:
                export_options["character"] = True
            if sf.attribute_names:
                export_options["attributes"] = True
                filtered.attributes = {k: v for k, v in cd.attributes.items()
                                        if k in sf.attribute_names}
            if sf.skill_names:
                export_options["skills"] = True
                filtered.skills = {k: v for k, v in cd.skills.items()
                                    if k in sf.skill_names}
            if sf.inventory_ids:
                export_options["items"] = True
                filtered.items = [i for i in cd.items if i.form_id in sf.inventory_ids]
            if sf.spell_ids:
                export_options["spells"] = True
                filtered.spells = [s for s in cd.spells if s.form_id in sf.spell_ids]
            if sf.faction_ids:
                export_options["factions"] = True
                filtered.factions = [f for f in cd.factions if f.form_id in sf.faction_ids]
            if sf.global_ids:
                export_options["globalVariables"] = True
                filtered.global_variables = [gv for gv in cd.global_variables
                                              if gv.form_id in sf.global_ids]
            if sf.active_quest_ids:
                export_options["completedQuests"] = True
                filtered.current_quests = [q for q in cd.current_quests
                                            if q.form_id in sf.active_quest_ids]
            if sf.include_completed_quests:
                export_options["completedQuests"] = True
                if cd.completed_quests_enriched:
                    filtered.completed_quests = [q.form_id for q in cd.completed_quests_enriched if q.form_id]
                else:
                    filtered.completed_quests = list(cd.completed_quests)
            if sf.include_details:
                export_options["statistics"] = True
                filtered.fame = cd.fame
                filtered.infamy = cd.infamy
                filtered.bounty = cd.bounty
                filtered.pc_misc_stats = cd.pc_misc_stats
            if sf.include_game_time:
                export_options["gameTime"] = True
                filtered.game_time = cd.game_time

            gen = ImportLogGenerator(filtered)
            gen.generate(target_path, export_options)
            self._status.showMessage(f"Saved: {target_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{e}")

    def _save_dump_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Modified Dump",
            str(self._dump_path or ""),
            "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        self._dump_path = Path(path)
        self._do_save(self._dump_path)

    def _do_save(self, output_path: Path):
        if not self._char_data:
            return

        # Timestamped backup before overwriting
        if output_path.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = output_path.with_suffix(f".{ts}.bak")
            shutil.copy2(output_path, backup)

        try:
            sf = build_staged_filter(self._panels, self._char_data)
            writer = SaveDumpWriter(self._char_data)
            writer.write(output_path, staged_filter=sf)
            self._status.showMessage(f"Saved: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save:\n{e}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Varla-HUD")
    window = VarlaHUD()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
