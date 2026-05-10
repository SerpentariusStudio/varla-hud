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
from translations import tr

# ── Categories shown in order ─────────────────────────────────────────────────

_CATEGORIES = [
    ("char_info",            "CHARACTER INFO"),
    ("details",              "CHARACTER DETAILS"),
    ("all_items",            "INVENTORY"),
    ("spell_all",            "SPELLS"),
    ("magic_active_effects", "ACTIVE MAGIC EFFECTS"),
    ("active_quests",        "ACTIVE QUESTS"),
    ("completed_quests",     "COMPLETED QUESTS"),
    ("quest_vars",           "QUEST VARIABLES"),
    ("skills",               "SKILLS"),
    ("attributes",           "ATTRIBUTES"),
    ("factions",             "FACTIONS"),
    ("globals",              "GLOBAL VARIABLES"),
    ("game_time",            "GAME TIME"),
    ("world_state",          "WORLD STATE"),
    ("plugins",              "PLUGINS"),
]

_UID_TO_CAT = {
    "ci.":       "CHARACTER INFO",
    "detail.":   "CHARACTER DETAILS",
    "inv.":      "INVENTORY",
    "spell.":    "SPELLS",
    "ame.":      "ACTIVE MAGIC EFFECTS",
    "aq.":       "ACTIVE QUESTS",
    "cq.":       "COMPLETED QUESTS",
    "sq.":       "QUEST VARIABLES",
    "skill.":    "SKILLS",
    "attr.":     "ATTRIBUTES",
    "faction.":  "FACTIONS",
    "gv.":       "GLOBAL VARIABLES",
    "gt.":       "GAME TIME",
    "ws.":       "WORLD STATE",
    "plugin.":   "PLUGINS",
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
    if uid.startswith("detail."):
        return v.get("field", ""), str(v.get("value", "")), v.get("category", "")
    if uid.startswith("ame."):
        return v.get("effect", ""), f"Mag {v.get('magnitude', '')}  Dur {v.get('duration', '')}", v.get("source", "")
    if uid.startswith("sq."):
        name = v.get("name", "") or v.get("editor_id", "")
        return name, f"{v.get('status', '')} · {v.get('__vars__', '0')} vars", v.get("form_id", "")
    if uid.startswith("gt."):
        return v.get("field", ""), str(v.get("value", "")), ""
    if uid.startswith("ws."):
        return v.get("field", ""), str(v.get("value", "")), v.get("category", "")
    if uid.startswith("plugin."):
        return v.get("name", ""), f"Index {v.get('index', '')}", ""
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
        self.setWindowTitle(tr("Import — Select items to export to target.txt"))
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
        left_top.addWidget(QLabel(tr("Available")))
        self._left_search = QLineEdit()
        self._left_search.setPlaceholderText(tr("Search..."))
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
            (tr("All →"),  self._move_all_right),
            (tr("Sel →"),  self._move_selected_right),
            (tr("← Sel"),  self._move_selected_left),
            (tr("← All"),  self._move_all_left),
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
        right_top.addWidget(QLabel(tr("Staged for target.txt")))
        self._right_search = QLineEdit()
        self._right_search.setPlaceholderText(tr("Search..."))
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
        write_btn = QPushButton(tr("Write target.txt"))
        write_btn.setFixedHeight(32)
        write_btn.clicked.connect(self._write_target)
        bot.addWidget(write_btn)
        close_btn = QPushButton(tr("Close"))
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
        # Allow writing if the only thing the user changed is a quest script
        # var (edited via the Vars dialog) — those don't appear as a staged
        # row but they're meaningful changes.
        has_dirty_vars = any(
            any(v.is_dirty for v in vlist)
            for vlist in self._char_data.quest_script_vars.values()
        )
        if not staged and not has_dirty_vars:
            QMessageBox.information(
                self, "Nothing staged",
                "Move at least one item to the right panel first, "
                "or edit a quest's script variables."
            )
            return

        sf = WriterSF()
        cq_sources = []
        skill_items: dict = {}    # storage_name -> PanelItem
        attr_items:  dict = {}    # attr_name     -> PanelItem
        ci_items:    dict = {}    # field key     -> PanelItem
        detail_items: list = []   # PanelItems for character details
        gt_items:    list = []    # PanelItems for game time
        ws_items:    list = []    # PanelItems for world state
        ame_sources: list = []    # active magic effect source objects

        _BASIC_CHAR_KEYS = {"name", "race", "class_name", "birthsign", "level", "sex"}
        for uid in staged:
            pi = self._all_items.get(uid)
            fid = pi.values.get("form_id", "") if pi else ""
            if uid.startswith("ci."):
                key = uid[3:]
                if key in _BASIC_CHAR_KEYS:
                    sf.include_char_info = True
                else:
                    sf.appearance_fields.add(key)
                if pi:
                    ci_items[key] = pi
            elif uid.startswith("inv."):
                if fid: sf.inventory_ids.add(fid)
                # Sync inline edits (qty / condition / charge) onto the source
                if pi and pi.source:
                    try: pi.source.quantity = int(pi.values.get("qty", pi.source.quantity))
                    except (ValueError, TypeError): pass
                    for src_attr, key in [
                        ("condition_current", "cond_cur"),
                        ("condition_max",     "cond_max"),
                        ("enchant_current",   "chrg_cur"),
                        ("enchant_max",       "chrg_max"),
                    ]:
                        raw = pi.values.get(key, "")
                        if raw != "":
                            try: setattr(pi.source, src_attr, float(raw))
                            except (ValueError, TypeError): pass
            elif uid.startswith("spell."):
                if fid: sf.spell_ids.add(fid)
                if pi and pi.source:
                    try: pi.source.magicka_cost = int(pi.values.get("cost", pi.source.magicka_cost))
                    except (ValueError, TypeError): pass
            elif uid.startswith("aq."):
                if fid: sf.active_quest_ids.add(fid)
                if pi and pi.source:
                    try: pi.source.stage = int(pi.values.get("stage", pi.source.stage))
                    except (ValueError, TypeError): pass
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
                if pi and pi.source:
                    try: pi.source.rank = int(pi.values.get("rank", pi.source.rank))
                    except (ValueError, TypeError): pass
            elif uid.startswith("gv."):
                if fid: sf.global_ids.add(fid)
                if pi and pi.source:
                    try: pi.source.value = float(pi.values.get("value", pi.source.value))
                    except (ValueError, TypeError): pass
            elif uid.startswith("detail."):
                sf.include_details = True
                if pi: detail_items.append(pi)
            elif uid.startswith("ame."):
                sf.include_active_effects = True
                if pi and pi.source: ame_sources.append(pi.source)
            elif uid.startswith("sq."):
                # Quest variable rows: marking the quest as included.
                # Vars themselves only get written if they were edited via
                # the dialog (is_dirty is true) — see auto-stage scan below.
                if fid: sf.quest_script_var_ids.add(fid)
            elif uid.startswith("gt."):
                sf.include_game_time = True
                if pi: gt_items.append(pi)
            elif uid.startswith("ws."):
                sf.include_world_state = True
                if pi: ws_items.append(pi)
            elif uid.startswith("plugin."):
                try: sf.plugin_indices.add(int(pi.values.get("index", -1)) if pi else -1)
                except (ValueError, TypeError): pass

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
            a = self._char_data.appearance
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
                elif hasattr(a, key):
                    setattr(a, key, val)

        if cq_sources:
            sf.include_completed_quests = True
            self._char_data.completed_quests_enriched = cq_sources

        if ame_sources:
            self._char_data.active_magic_effects = ame_sources

        # Sync edited details back onto vitals / resistances / pc_misc_stats.
        # Mirrors the dispatch in panel_defs.build_staged_filter so the Import
        # window honours inline edits made on the Details panel.
        if detail_items:
            v = self._char_data.vitals
            r = self._char_data.magic_resistances
            cd = self._char_data
            mapping = {
                "health_cur":   ("vitals", "health_current",  float),
                "health_base":  ("vitals", "health_base",     float),
                "magicka_cur":  ("vitals", "magicka_current", float),
                "magicka_base": ("vitals", "magicka_base",    float),
                "fatigue_cur":  ("vitals", "fatigue_current", float),
                "fatigue_base": ("vitals", "fatigue_base",    float),
                "encumbrance":  ("vitals", "encumbrance",     float),
                "fame":         ("char",   "fame",            int),
                "infamy":       ("char",   "infamy",          int),
                "bounty":       ("char",   "bounty",          int),
                "res_fire":     ("res",    "fire",            float),
                "res_frost":    ("res",    "frost",           float),
                "res_shock":    ("res",    "shock",           float),
                "res_magic":    ("res",    "magic",           float),
                "res_disease":  ("res",    "disease",         float),
                "res_poison":   ("res",    "poison",          float),
                "res_para":     ("res",    "paralysis",       float),
                "res_normal":   ("res",    "normal_weapons",  float),
            }
            obj_for = {"vitals": v, "res": r, "char": cd}
            for pi in detail_items:
                key = pi.uid[7:]   # strip "detail."
                raw = pi.values.get("value", "")
                if key in mapping:
                    target, attr, conv = mapping[key]
                    try:
                        setattr(obj_for[target], attr, conv(float(raw)))
                    except (ValueError, TypeError):
                        pass
                elif key.startswith("misc_"):
                    try:
                        idx = int(key[5:])
                        cd.pc_misc_stats[idx] = int(float(raw))
                    except (ValueError, TypeError):
                        pass

        if gt_items:
            gt = self._char_data.game_time
            for pi in gt_items:
                key = pi.uid[3:]   # strip "gt."
                try:
                    val = float(pi.values.get("value", 0))
                    if key == "days_passed": gt.days_passed = val
                    elif key == "game_year":  gt.game_year  = int(val)
                    elif key == "game_month": gt.game_month = int(val)
                    elif key == "game_day":   gt.game_day   = int(val)
                    elif key == "game_hour":  gt.game_hour  = val
                except (ValueError, TypeError):
                    pass

        if ws_items:
            pos = self._char_data.player_position
            w = self._char_data.weather
            for pi in ws_items:
                key = pi.uid[3:]   # strip "ws."
                raw = pi.values.get("value", "")
                # Numeric fields first
                try:
                    val_f = float(raw)
                    if key == "x":       pos.x = val_f; continue
                    elif key == "y":     pos.y = val_f; continue
                    elif key == "z":     pos.z = val_f; continue
                    elif key == "rot_x": pos.rot_x = val_f; continue
                    elif key == "rot_y": pos.rot_y = val_f; continue
                    elif key == "rot_z": pos.rot_z = val_f; continue
                    elif key == "scale": pos.scale = val_f; continue
                except (ValueError, TypeError):
                    pass
                # String fields
                if key == "cell":          pos.parent_cell         = raw
                elif key == "cell_fid":    pos.parent_cell_form_id = raw
                elif key == "weather":     w.current_weather       = raw
                elif key == "weather_fid": w.current_weather_form_id = raw
                elif key == "climate_fid": w.climate_form_id       = raw

        # Quest-var auto-include policy:
        #   - If the user was offered any sq. rows in the Import window
        #     (i.e., any quest_vars row was staged in the main window),
        #     RESPECT their explicit staging — only the rows on the right
        #     panel get included. The dispatch loop above already added
        #     them to sf.quest_script_var_ids.
        #   - Only when no sq. row is present at all (the user edited a var
        #     via the dialog without ever staging the quest) do we auto-
        #     include the quest so dialog edits don't silently disappear.
        sq_was_offered = any(uid.startswith("sq.") for uid in self._all_items)
        if not sq_was_offered:
            for fid, vlist in self._char_data.quest_script_vars.items():
                if any(v.is_dirty for v in vlist):
                    sf.quest_script_var_ids.add(fid)

        target_path = self._dump_path.parent / "target.txt"
        try:
            raw = self._char_data.raw_dump_text or ""
            is_legacy = self._char_data.dump_format == "classic" and "=== " not in raw[:500]
            if is_legacy:
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
