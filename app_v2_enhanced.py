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
    QPushButton, QLabel, QFrame, QDialog, QRadioButton, QButtonGroup,
    QDialogButtonBox,
)
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtCore import Qt

from theme import apply_theme, COLORS
from navigation import NavigationWidget, NAVIGATION_STRUCTURE, TAB_ORDER
from dual_panel import DualPanelWidget
from panel_defs import get_columns, extract_items, build_staged_filter
from models import CharacterData
from save_dump_parser import parse_save_dump
from save_dump_writer import SaveDumpWriter
from import_window import ImportWindow
from import_generator import ImportLogGenerator
import settings as app_settings
from translations import tr, load_language, set_language, LANGUAGES, current_language

# Default save dump directories per game version
_DUMP_DIRS = {
    "classic":    Path.home() / "Documents" / "My Games" / "Oblivion" / "OBSE",
    "remastered": Path.home() / "Documents" / "My Games" / "Oblivion Remastered" / "OBSE",
}


class GameFormatDialog(QDialog):
    """Startup dialog to choose between Oblivion versions."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Select Game Version"))
        self.setFixedSize(360, 200)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel(tr("Which version of Oblivion are you using?"))
        title.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(title)

        self._group = QButtonGroup(self)
        saved = app_settings.get("game_format") or "auto"

        self._auto_rb = QRadioButton(tr("Auto-detect"))
        self._rem_rb = QRadioButton(tr("Oblivion Remastered (obse64)"))
        self._cls_rb = QRadioButton(tr("Oblivion Classic (xOBSE)"))

        self._group.addButton(self._auto_rb)
        self._group.addButton(self._rem_rb)
        self._group.addButton(self._cls_rb)

        if saved == "remastered":
            self._rem_rb.setChecked(True)
        elif saved == "classic":
            self._cls_rb.setChecked(True)
        else:
            self._auto_rb.setChecked(True)

        layout.addWidget(self._auto_rb)
        layout.addWidget(self._rem_rb)
        layout.addWidget(self._cls_rb)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def selected_format(self) -> str:
        if self._rem_rb.isChecked():
            return "remastered"
        if self._cls_rb.isChecked():
            return "classic"
        return "auto"


class VarlaHUD(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Varla-HUD")
        self.resize(1400, 900)

        app_settings.load()
        load_language()

        self._char_data: Optional[CharacterData] = None
        self._dump_path: Optional[Path] = None
        self._panels: dict[str, DualPanelWidget] = {}
        self._page_map: dict[str, int] = {}

        self._show_format_dialog()
        self._build_menu()
        self._build_ui()
        apply_theme(self)

    def _show_format_dialog(self):
        dlg = GameFormatDialog(self)
        dlg.exec()
        fmt = dlg.selected_format()
        app_settings.set("game_format", fmt)

    # ── Menu ─────────────────────────────────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        file_menu = mb.addMenu(tr("&File"))

        open_act = QAction(tr("&Open Save Dump..."), self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self._open_dump)
        file_menu.addAction(open_act)

        self._open_default_act = QAction(tr("Open &Default Path"), self)
        self._open_default_act.setShortcut(QKeySequence("Ctrl+R"))
        self._open_default_act.triggered.connect(self._open_default_dump)
        file_menu.addAction(self._open_default_act)

        file_menu.addSeparator()

        self._import_act = QAction(tr("&Import..."), self)
        self._import_act.setShortcut(QKeySequence.Save)
        self._import_act.setEnabled(False)
        self._import_act.triggered.connect(self._open_import_window)
        file_menu.addAction(self._import_act)

        self._save_as_act = QAction(tr("Save &As..."), self)
        self._save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._save_as_act.setEnabled(False)
        self._save_as_act.triggered.connect(self._save_dump_as)
        file_menu.addAction(self._save_as_act)

        file_menu.addSeparator()

        quit_act = QAction(tr("&Quit"), self)
        quit_act.setShortcut(QKeySequence.Quit)
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # ── Settings menu ────────────────────────────────────────────────
        settings_menu = mb.addMenu(tr("&Settings"))

        game_fmt_act = QAction(tr("&Game Version..."), self)
        game_fmt_act.triggered.connect(self._change_game_format)
        settings_menu.addAction(game_fmt_act)

        ini_act = QAction(tr("&INI Editor..."), self)
        ini_act.triggered.connect(self._open_ini_editor)
        settings_menu.addAction(ini_act)

        # ── Language submenu ──
        lang_menu = settings_menu.addMenu(tr("&Language"))
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        for code, name in LANGUAGES.items():
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(code == current_language())
            act.triggered.connect(lambda checked, c=code: self._change_language(c))
            lang_group.addAction(act)
            lang_menu.addAction(act)


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
                panel.clear_target_requested.connect(self._clear_target)
                idx = self._stack.addWidget(panel)
                self._page_map[page_key] = idx
                self._panels[page_key] = panel

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage(tr("Open a save dump to begin (File → Open Save Dump)."))

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
        path_label = QLabel(tr("Default dump path:"))
        path_label.setObjectName("options_label")
        layout.addWidget(path_label)

        self._default_path_lbl = QLabel(self._get_default_path_display())
        self._default_path_lbl.setObjectName("options_path")
        self._default_path_lbl.setMinimumWidth(200)
        layout.addWidget(self._default_path_lbl)

        change_btn = QPushButton(tr("Change..."))
        change_btn.setObjectName("options_btn")
        change_btn.setFixedWidth(70)
        change_btn.clicked.connect(self._change_default_path)
        layout.addWidget(change_btn)

        clear_btn = QPushButton(tr("Clear"))
        clear_btn.setObjectName("options_btn")
        clear_btn.setFixedWidth(50)
        clear_btn.clicked.connect(self._clear_default_path)
        layout.addWidget(clear_btn)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("options_sep")
        layout.addWidget(sep)

        # Import filter toggle
        filter_lbl = QLabel(tr("Ctrl+S:"))
        filter_lbl.setObjectName("options_label")
        layout.addWidget(filter_lbl)

        skip = bool(app_settings.get("skip_import_filter"))
        self._export_toggle_btn = QPushButton(tr("Direct Save") if skip else tr("Import Filter"))
        self._export_toggle_btn.setObjectName("options_export_btn")
        self._export_toggle_btn.setCheckable(True)
        self._export_toggle_btn.setChecked(skip)
        self._export_toggle_btn.setFixedWidth(110)
        self._export_toggle_btn.setToolTip(
            tr("Import Filter: Ctrl+S opens the Import window to\n"
            "select which staged items to export to target.txt.\n\n"
            "Direct Save: Ctrl+S writes all staged items directly\n"
            "to target.txt without the Import window.")
        )
        self._export_toggle_btn.clicked.connect(self._toggle_skip_filter)
        layout.addWidget(self._export_toggle_btn)

        layout.addStretch()
        return bar

    def _dump_path_key(self) -> str:
        """Return the settings key for the default dump path based on game format."""
        fmt = app_settings.get("game_format") or "auto"
        if fmt == "classic":
            return "default_dump_path_classic"
        if fmt == "remastered":
            return "default_dump_path_remastered"
        return "default_dump_path"

    def _get_default_path_display(self) -> str:
        p = app_settings.get(self._dump_path_key()) or ""
        return p if p else "(not set)"

    def _change_default_path(self):
        current = app_settings.get(self._dump_path_key()) or ""
        start = str(Path(current).parent) if current else ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Set Default Dump Path", start, "Text Files (*.txt);;All Files (*)"
        )
        if path:
            app_settings.set(self._dump_path_key(), path)
            self._default_path_lbl.setText(path)

    def _clear_default_path(self):
        app_settings.set(self._dump_path_key(), "")
        self._default_path_lbl.setText("(not set)")

    def _toggle_skip_filter(self, checked: bool):
        app_settings.set("skip_import_filter", checked)
        self._export_toggle_btn.setText(tr("Direct Save") if checked else tr("Import Filter"))

    def _change_game_format(self):
        dlg = GameFormatDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            fmt = dlg.selected_format()
            app_settings.set("game_format", fmt)
            self._default_path_lbl.setText(self._get_default_path_display())
            if self._dump_path:
                self._reload_dump_with_format(fmt)

    def _change_language(self, lang_code: str):
        set_language(lang_code)
        QMessageBox.information(
            self, "Language",
            "Language changed. Please restart the application for the change to take full effect."
        )

    def _open_ini_editor(self):
        import subprocess, sys as _sys
        editor_path = Path(__file__).parent / "varla_ini_editor.py"
        fmt = app_settings.get("game_format") or "auto"
        cmd = [_sys.executable, str(editor_path)]
        if fmt in ("classic", "remastered"):
            cmd += ["--format", fmt]
        subprocess.Popen(cmd)

    def _reload_dump_with_format(self, fmt: str):
        try:
            char_data = parse_save_dump(self._dump_path)
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Failed to re-parse:\n{e}")
            return
        if fmt != "auto":
            char_data.dump_format = fmt
        self._char_data = char_data
        self._populate_all_panels()
        self._status.showMessage(
            f"Reloaded: {self._dump_path.name}  [{char_data.dump_format}]"
        )

    # ── Navigation ───────────────────────────────────────────────────────

    def _show_page(self, page_key: str):
        idx = self._page_map.get(page_key)
        if idx is not None:
            self._stack.setCurrentIndex(idx)

    # ── File operations ──────────────────────────────────────────────────

    def _open_default_dump(self):
        path = app_settings.get(self._dump_path_key()) or ""
        if not path or not Path(path).exists():
            # Fall back to format-appropriate save_dump.txt
            fmt = app_settings.get("game_format") or "auto"
            fmt_dir = _DUMP_DIRS.get(fmt)
            if fmt_dir:
                candidate = fmt_dir / "save_dump.txt"
                if candidate.exists():
                    self._load_path(str(candidate))
                    return
            QMessageBox.warning(
                self, "No Default Path",
                "No default dump path is set or the file no longer exists.\n"
                "Use the options bar to set one."
            )
            return
        self._load_path(path)

    def _open_dump(self):
        # Pick start directory: format-specific OBSE dir takes priority,
        # fall back to saved default dump path
        fmt = app_settings.get("game_format") or "auto"
        fmt_dir = _DUMP_DIRS.get(fmt)
        if fmt_dir and fmt_dir.exists():
            start_dir = str(fmt_dir)
        else:
            default = app_settings.get(self._dump_path_key()) or ""
            if default and Path(default).parent.exists():
                start_dir = str(Path(default).parent)
            else:
                start_dir = ""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Save Dump", start_dir, "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        self._load_path(path)

    def _load_path(self, path: str):
        try:
            char_data = parse_save_dump(Path(path))
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to parse save dump:\n{e}")
            return

        # If user chose a specific game version, override the detected format
        # so the writer produces the correct output
        fmt = app_settings.get("game_format") or "auto"
        if fmt != "auto":
            char_data.dump_format = fmt

        self._char_data = char_data
        self._dump_path = Path(path)
        self._populate_all_panels()

        # Auto-set default dump path if not configured yet for this format
        key = self._dump_path_key()
        if not app_settings.get(key):
            app_settings.set(key, path)
            self._default_path_lbl.setText(path)

        self._import_act.setEnabled(True)
        self._save_as_act.setEnabled(True)
        detected = char_data.dump_format or "auto"
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

        # Check if user wants to skip the import filter and save directly
        if app_settings.get("skip_import_filter"):
            # Warn if nothing is staged
            if not any(p.get_staged_items() for p in self._panels.values()):
                QMessageBox.information(
                    self, tr("Nothing staged"),
                    tr("Stage some items in the right panel first, then press Ctrl+S."))
                return
            self._save_dump()
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
        # Use ImportLogGenerator only for legacy --- --- format dumps;
        # modern xOBSE (=== ===) uses SaveDumpWriter (dump format target.txt)
        raw = (self._char_data.raw_dump_text or "") if self._char_data else ""
        is_legacy = self._char_data and self._char_data.dump_format == "classic" and "=== " not in raw[:500]
        if is_legacy:
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


    def _clear_target(self):
        # Derive target path from loaded dump (same logic as _save_dump)
        if self._dump_path:
            target_path = self._dump_path.parent / "target.txt"
        else:
            fmt = app_settings.get("game_format") or "classic"
            target_dir = _DUMP_DIRS.get(fmt)
            if not target_dir:
                self._status.showMessage(tr("No dump loaded and game format is auto — cannot determine target path."))
                return
            target_path = target_dir / "target.txt"
        try:
            target_path.write_text("", encoding="utf-8")
            self._status.showMessage(f"Cleared: {target_path}")
        except Exception as e:
            QMessageBox.critical(self, "Clear Target Error", f"Failed to clear target:\n{e}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Varla-HUD")
    window = VarlaHUD()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
