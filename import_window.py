"""Import Window — flat dual-panel for selecting which items go into target.txt.

Left  : all items from the loaded dump, grouped by category.
Right : items staged for the next target.txt write.

Double-click or use → / ← buttons to move items.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QTreeWidget,
    QTreeWidgetItem, QAbstractItemView, QWidget, QMessageBox,
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QColor, QFont

from models import CharacterData
from dual_panel import PanelItem
from save_dump_writer import SaveDumpWriter, StagedFilter as WriterSF
from import_generator import ImportLogGenerator
from theme import COLORS

# ── Categories shown in order ─────────────────────────────────────────────────

_CATEGORIES = [
    ("char_info",        "CHARACTER INFO"),
    ("all_items",        "INVENTORY"),
    ("spell_all",        "SPELLS"),
    ("active_quests",    "ACTIVE QUESTS"),
    ("completed_quests", "COMPLETED QUESTS"),
    ("skills",           "SKILLS"),
    ("attributes",       "ATTRIBUTES"),
    ("factions",         "FACTIONS"),
    ("globals",          "GLOBAL VARIABLES"),
]

_UID_TO_CAT = {
    "ci.":       "CHARACTER INFO",
    "inv.":      "INVENTORY",
    "spell.":    "SPELLS",
    "aq.":       "ACTIVE QUESTS",
    "cq.":       "COMPLETED QUESTS",
    "skill.":    "SKILLS",
    "attr.":     "ATTRIBUTES",
    "faction.":  "FACTIONS",
    "gv.":       "GLOBAL VARIABLES",
}


def _cat_label_for_uid(uid: str) -> str:
    for prefix, label in _UID_TO_CAT.items():
        if uid.startswith(prefix):
            return label
    return "OTHER"


def _item_columns(pi) -> tuple:
    """Return (Name, Info, FormID) strings for display."""
    uid = pi.uid
    v = pi.values
    if uid.startswith("ci."):
        return v.get("field", ""), str(v.get("value", "")), ""
    if uid.startswith("inv."):
        qty = v.get("qty", "")
        info = f"{v.get('type', '')}  x{qty}" if qty else v.get("type", "")
        return v.get("name", ""), info, v.get("form_id", "")
    if uid.startswith("spell."):
        return v.get("name", ""), v.get("spell_type", ""), v.get("form_id", "")
    if uid.startswith("aq."):
        name = v.get("name", "") or v.get("editor_id", "")
        return name, f"Stage {v.get('stage', '')}", v.get("form_id", "")
    if uid.startswith("cq."):
        name = v.get("name", "") or v.get("editor_id", "")
        return name, f"Final stage {v.get('final_stage', '')}", v.get("form_id", "")
    if uid.startswith("skill."):
        return v.get("name", ""), f"Base {v.get('base', '')}", ""
    if uid.startswith("attr."):
        return v.get("name", ""), f"Base {v.get('base', '')}", ""
    if uid.startswith("faction."):
        return v.get("name", ""), f"Rank {v.get('rank', '')}", v.get("form_id", "")
    if uid.startswith("gv."):
        return v.get("name", ""), str(v.get("value", "")), v.get("form_id", "")
    return v.get("name", uid), "", ""


class DnDTreeWidget(QTreeWidget):
    """QTreeWidget with drag-and-drop between left and right panels."""

    def __init__(self, is_left: bool, window: "ImportWindow"):
        super().__init__()
        self._is_left = is_left
        self._win = window
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.source() is not self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.source() is not self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        source = event.source()
        if source is self or not isinstance(source, QTreeWidget):
            event.ignore()
            return
        for item in source.selectedItems():
            uid = item.data(0, Qt.UserRole)
            if not uid:
                continue
            if self._is_left:
                # dropped onto left → move item from right back to left
                self._win._remove_from_right(uid)
                self._win._show_left_item(uid)
            else:
                # dropped onto right → stage item from left
                if uid not in self._win._staged_uids():
                    self._win._add_to_right(uid)
                    self._win._hide_left_item(uid)
        event.acceptProposedAction()


class ImportWindow(QDialog):
    """Flat dual-panel window for selecting items to write to target.txt.

    staged_items: PanelItems already on the right panel in the main window.
    """

    def __init__(self, staged_items: list, char_data: CharacterData, dump_path: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import — Select items to export to target.txt")
        self.resize(1200, 720)
        self._char_data = char_data
        self._dump_path = dump_path
        self._all_items: dict = {}   # uid -> PanelItem

        self._build_ui()
        self._populate_left(staged_items)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        target_path = self._dump_path.parent / "target.txt"
        hdr = QLabel(f"Source: {self._dump_path.name}   →   Target: {target_path}")
        hdr.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        root.addWidget(hdr)

        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, stretch=1)

        # ── Left ──────────────────────────────────────────────────────────
        left_w = QWidget()
        left_lay = QVBoxLayout(left_w)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(4)

        left_top = QHBoxLayout()
        left_top.addWidget(QLabel("Available"))
        self._left_search = QLineEdit()
        self._left_search.setPlaceholderText("Search…")
        self._left_search.textChanged.connect(lambda t: self._filter_tree(self._left_tree, t))
        left_top.addWidget(self._left_search)
        left_lay.addLayout(left_top)

        self._left_tree = self._make_tree(is_left=True)
        self._left_tree.itemDoubleClicked.connect(self._on_left_double_click)
        left_lay.addWidget(self._left_tree)
        splitter.addWidget(left_w)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_w = QWidget()
        btn_lay = QVBoxLayout(btn_w)
        btn_lay.setContentsMargins(4, 0, 4, 0)
        btn_lay.setAlignment(Qt.AlignVCenter)
        btn_lay.setSpacing(8)
        for label, slot in [
            ("All →",  self._move_all_right),
            ("Sel →",  self._move_selected_right),
            ("← Sel",  self._move_selected_left),
            ("← All",  self._move_all_left),
        ]:
            b = QPushButton(label)
            b.setFixedWidth(70)
            b.clicked.connect(slot)
            btn_lay.addWidget(b)
        splitter.addWidget(btn_w)

        # ── Right ─────────────────────────────────────────────────────────
        right_w = QWidget()
        right_lay = QVBoxLayout(right_w)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(4)

        right_top = QHBoxLayout()
        right_top.addWidget(QLabel("Staged for target.txt"))
        self._right_search = QLineEdit()
        self._right_search.setPlaceholderText("Search…")
        self._right_search.textChanged.connect(lambda t: self._filter_tree(self._right_tree, t))
        right_top.addWidget(self._right_search)
        right_lay.addLayout(right_top)

        self._right_tree = self._make_tree(is_left=False)
        self._right_tree.itemDoubleClicked.connect(self._on_right_double_click)
        right_lay.addWidget(self._right_tree)
        splitter.addWidget(right_w)

        splitter.setSizes([520, 80, 520])

        # ── Bottom bar ────────────────────────────────────────────────────
        bot = QHBoxLayout()
        bot.addStretch()
        write_btn = QPushButton("Write target.txt")
        write_btn.setFixedHeight(32)
        write_btn.clicked.connect(self._write_target)
        bot.addWidget(write_btn)
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(32)
        close_btn.clicked.connect(self.accept)
        bot.addWidget(close_btn)
        root.addLayout(bot)

    def _make_tree(self, is_left: bool) -> QTreeWidget:
        t = DnDTreeWidget(is_left, self)
        t.setColumnCount(3)
        t.setHeaderLabels(["Name", "Info", "FormID"])
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setUniformRowHeights(True)
        t.setAlternatingRowColors(True)
        t.header().setStretchLastSection(False)
        t.setColumnWidth(0, 260)
        t.setColumnWidth(1, 170)
        t.setColumnWidth(2, 110)
        return t

    # ── Populate ──────────────────────────────────────────────────────────────

    def _populate_left(self, staged_items: list):
        self._left_tree.clear()
        self._all_items.clear()
        accent = QColor(COLORS.get("accent", "#c8a84b"))

        # Group by category, preserving _CATEGORIES order
        cat_order = [label for _, label in _CATEGORIES]
        buckets: dict = {label: [] for label in cat_order}

        seen = set()
        for pi in staged_items:
            if pi.uid in seen:
                continue
            seen.add(pi.uid)
            self._all_items[pi.uid] = pi
            label = _cat_label_for_uid(pi.uid)
            if label not in buckets:
                buckets[label] = []
            buckets[label].append(pi)

        for cat_label in cat_order:
            items = buckets.get(cat_label, [])
            if not items:
                continue

            cat_node = QTreeWidgetItem(self._left_tree)
            cat_node.setText(0, f"{cat_label}  ({len(items)})")
            cat_node.setFlags(Qt.ItemIsEnabled)
            f = cat_node.font(0)
            f.setBold(True)
            cat_node.setFont(0, f)
            cat_node.setForeground(0, accent)
            cat_node.setData(0, Qt.UserRole + 1, cat_label)

            for pi in items:
                name, info, fid = _item_columns(pi)
                child = QTreeWidgetItem(cat_node, [name, info, fid])
                child.setData(0, Qt.UserRole, pi.uid)

            cat_node.setExpanded(True)

    # ── Tree filtering ────────────────────────────────────────────────────────

    def _filter_tree(self, tree: QTreeWidget, text: str):
        text = text.lower()
        for i in range(tree.topLevelItemCount()):
            cat = tree.topLevelItem(i)
            any_visible = False
            for j in range(cat.childCount()):
                child = cat.child(j)
                row = " ".join(child.text(c) for c in range(3)).lower()
                visible = not text or text in row
                child.setHidden(not visible)
                if visible:
                    any_visible = True
            cat.setHidden(bool(text) and not any_visible)

    # ── Right-panel helpers ───────────────────────────────────────────────────

    def _staged_uids(self) -> set:
        uids = set()
        for i in range(self._right_tree.topLevelItemCount()):
            cat = self._right_tree.topLevelItem(i)
            for j in range(cat.childCount()):
                uid = cat.child(j).data(0, Qt.UserRole)
                if uid:
                    uids.add(uid)
        return uids

    def _get_or_create_right_cat(self, cat_label: str) -> QTreeWidgetItem:
        for i in range(self._right_tree.topLevelItemCount()):
            node = self._right_tree.topLevelItem(i)
            if node.data(0, Qt.UserRole + 1) == cat_label:
                return node
        node = QTreeWidgetItem(self._right_tree)
        node.setFlags(Qt.ItemIsEnabled)
        f = node.font(0)
        f.setBold(True)
        node.setFont(0, f)
        node.setForeground(0, QColor(COLORS.get("accent", "#c8a84b")))
        node.setData(0, Qt.UserRole + 1, cat_label)
        node.setExpanded(True)
        self._refresh_right_cat_label(node)
        return node

    def _refresh_right_cat_label(self, node: QTreeWidgetItem):
        label = node.data(0, Qt.UserRole + 1) or ""
        node.setText(0, f"{label}  ({node.childCount()})")

    def _add_to_right(self, uid: str):
        pi = self._all_items.get(uid)
        if not pi:
            return
        cat_node = self._get_or_create_right_cat(_cat_label_for_uid(uid))
        name, info, fid = _item_columns(pi)
        child = QTreeWidgetItem(cat_node, [name, info, fid])
        child.setData(0, Qt.UserRole, uid)
        self._refresh_right_cat_label(cat_node)

    def _remove_from_right(self, uid: str):
        for i in range(self._right_tree.topLevelItemCount()):
            cat = self._right_tree.topLevelItem(i)
            for j in range(cat.childCount()):
                if cat.child(j).data(0, Qt.UserRole) == uid:
                    cat.takeChild(j)
                    if cat.childCount() == 0:
                        self._right_tree.takeTopLevelItem(i)
                    else:
                        self._refresh_right_cat_label(cat)
                    return

    def _hide_left_item(self, uid: str):
        for i in range(self._left_tree.topLevelItemCount()):
            cat = self._left_tree.topLevelItem(i)
            for j in range(cat.childCount()):
                if cat.child(j).data(0, Qt.UserRole) == uid:
                    cat.child(j).setHidden(True)
                    return

    def _show_left_item(self, uid: str):
        for i in range(self._left_tree.topLevelItemCount()):
            cat = self._left_tree.topLevelItem(i)
            for j in range(cat.childCount()):
                if cat.child(j).data(0, Qt.UserRole) == uid:
                    cat.child(j).setHidden(False)
                    return

    # ── Transfer operations ───────────────────────────────────────────────────

    def _on_left_double_click(self, item: QTreeWidgetItem, _col: int):
        uid = item.data(0, Qt.UserRole)
        if uid and uid not in self._staged_uids():
            self._add_to_right(uid)
            self._hide_left_item(uid)

    def _on_right_double_click(self, item: QTreeWidgetItem, _col: int):
        uid = item.data(0, Qt.UserRole)
        if uid:
            self._remove_from_right(uid)
            self._show_left_item(uid)

    def _move_selected_right(self):
        staged = self._staged_uids()
        for item in self._left_tree.selectedItems():
            uid = item.data(0, Qt.UserRole)
            if uid and uid not in staged:
                self._add_to_right(uid)
                self._hide_left_item(uid)

    def _move_selected_left(self):
        for item in self._right_tree.selectedItems():
            uid = item.data(0, Qt.UserRole)
            if uid:
                self._remove_from_right(uid)
                self._show_left_item(uid)

    def _move_all_right(self):
        staged = self._staged_uids()
        for i in range(self._left_tree.topLevelItemCount()):
            cat = self._left_tree.topLevelItem(i)
            for j in range(cat.childCount()):
                child = cat.child(j)
                uid = child.data(0, Qt.UserRole)
                if uid and uid not in staged and not child.isHidden():
                    self._add_to_right(uid)
                    child.setHidden(True)

    def _move_all_left(self):
        for uid in self._staged_uids():
            self._show_left_item(uid)
        self._right_tree.clear()

    # ── Write ─────────────────────────────────────────────────────────────────

    def _write_target(self):
        staged = self._staged_uids()
        if not staged:
            QMessageBox.information(
                self, "Nothing staged",
                "Move at least one item to the right panel first."
            )
            return

        sf = WriterSF()
        cq_sources = []
        skill_items: dict = {}   # storage_name -> PanelItem
        attr_items:  dict = {}   # attr_name     -> PanelItem
        ci_items:    dict = {}   # field key     -> PanelItem

        for uid in staged:
            pi = self._all_items.get(uid)
            fid = pi.values.get("form_id", "") if pi else ""
            if uid.startswith("ci."):
                sf.include_char_info = True
                if pi:
                    ci_items[uid[3:]] = pi
            elif uid.startswith("inv."):
                if fid: sf.inventory_ids.add(fid)
            elif uid.startswith("spell."):
                if fid: sf.spell_ids.add(fid)
            elif uid.startswith("aq."):
                if fid: sf.active_quest_ids.add(fid)
            elif uid.startswith("cq."):
                if pi and pi.source:
                    cq_sources.append(pi.source)
            elif uid.startswith("skill."):
                name = uid[6:]
                sf.skill_names.add(name)
                if pi: skill_items[name] = pi
            elif uid.startswith("attr."):
                name = uid[5:]
                sf.attribute_names.add(name)
                if pi: attr_items[name] = pi
            elif uid.startswith("faction."):
                if fid: sf.faction_ids.add(fid)
            elif uid.startswith("gv."):
                if fid: sf.global_ids.add(fid)

        # Sync edited base/current values into char_data so the writer uses them
        if skill_items:
            for name, pi in skill_items.items():
                try:
                    self._char_data.skills[name] = int(pi.values.get("base", 0))
                except (ValueError, TypeError):
                    pass
                try:
                    self._char_data.skills_current[name] = int(
                        pi.values.get("current", pi.values.get("base", 0)))
                except (ValueError, TypeError):
                    pass
        if attr_items:
            for name, pi in attr_items.items():
                try:
                    self._char_data.attributes[name] = int(pi.values.get("base", 0))
                except (ValueError, TypeError):
                    pass
                try:
                    self._char_data.skills_current[name] = int(
                        pi.values.get("current", pi.values.get("base", 0)))
                except (ValueError, TypeError):
                    pass

        if ci_items:
            c = self._char_data.character
            for key, pi in ci_items.items():
                val = pi.values.get("value", "")
                if key == "level":
                    try: c.level = int(val)
                    except (ValueError, TypeError): pass
                elif key == "name":
                    c.name = val
                elif key == "race":
                    c.race = val
                elif key == "class_name":
                    c.class_name = val
                elif key == "birthsign":
                    c.birthsign = val
                elif key == "sex":
                    c.sex = val

        if cq_sources:
            sf.include_completed_quests = True
            self._char_data.completed_quests_enriched = cq_sources

        target_path = self._dump_path.parent / "target.txt"
        try:
            if self._char_data.dump_format == "classic":
                self._write_target_classic(sf, target_path)
            else:
                writer = SaveDumpWriter(self._char_data)
                writer.write(target_path, staged_filter=sf)
            QMessageBox.information(
                self, "Done",
                f"Written {len(staged)} item(s) to:\n{target_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Write Error", f"Failed to write target.txt:\n{e}")

    def _write_target_classic(self, sf: "WriterSF", target_path):
        """Write target.txt in classic xOBSE command format using ImportLogGenerator."""
        cd = self._char_data

        # Build a filtered CharacterData containing only staged items
        filtered = CharacterData()
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
            filtered.items = [item for item in cd.items
                               if item.form_id in sf.inventory_ids]

        if sf.spell_ids:
            export_options["spells"] = True
            filtered.spells = [spell for spell in cd.spells
                                if spell.form_id in sf.spell_ids]

        if sf.faction_ids:
            export_options["factions"] = True
            filtered.factions = [f for f in cd.factions
                                  if f.form_id in sf.faction_ids]

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
            # Use staged enriched objects; fall back to raw form_id list
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
