"""
DualPanelWidget — drag-and-drop left/right staging widget for Varla-HUD.

Left panel  : source items (all data from the loaded dump).
Right panel : staged items (what gets written on Save).

Features:
  - Drag-and-drop between panels (MIME: application/x-varla-items)
  - Double-click to move items between panels
  - Multi-select: Shift+click, Ctrl+click, rubber-band (grid mode)
  - List view  : QTableView with sortable columns and inline editing
  - Grid view  : QListView in icon mode with rubber-band selection
  - Per-panel search filter (all columns)
  - Centre transfer buttons: All →, Sel →, ← Sel, ← All
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableView, QListView, QAbstractItemView, QFrame, QLineEdit,
    QSplitter, QStyledItemDelegate, QSizePolicy,
    QStackedWidget, QSpinBox, QDoubleSpinBox, QStyle, QDialog,
    QComboBox,
)
from PySide6.QtCore import (
    Qt, Signal, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel, QMimeData, QSize, QRect,
    QPoint,
)
from PySide6.QtGui import QDrag, QPixmap, QIcon, QColor, QFont, QPainter, QPen

from theme import COLORS, BRASS_DEEP, BRASS, INK_OAK, INK_OAK_2, INK_LEATHER, INK_VOID
from translations import tr


# ── Corner-flourish frame ────────────────────────────────────────────────────

class _PanelFrame(QFrame):
    """
    A QFrame that paints 4 brass L-bracket flourishes at its corners
    (replacing the CSS ::before / ::after pseudo-elements from the design).
    """

    _CORNER = 14   # arm length
    _INSET  = 4    # gap from frame edge

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.Antialiasing, False)
            pen = QPen(QColor(BRASS_DEEP))
            pen.setWidth(1)
            p.setPen(pen)
            w = self.width() - 1
            h = self.height() - 1
            c = self._CORNER
            i = self._INSET

            # top-left
            p.drawLine(i, i, i + c, i)
            p.drawLine(i, i, i, i + c)
            # top-right
            p.drawLine(w - i, i, w - i - c, i)
            p.drawLine(w - i, i, w - i, i + c)
            # bottom-left
            p.drawLine(i, h - i, i + c, h - i)
            p.drawLine(i, h - i, i, h - i - c)
            # bottom-right
            p.drawLine(w - i, h - i, w - i - c, h - i)
            p.drawLine(w - i, h - i, w - i, h - i - c)
        finally:
            p.end()


# ── Transfer column with painted central rail ────────────────────────────────

class _XferColumn(QFrame):
    """Centre transfer column with a faint vertical brass rail in the middle."""

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        try:
            x = self.width() // 2
            top = 40
            bot = self.height() - 40
            if bot > top:
                pen = QPen(QColor(BRASS_DEEP))
                pen.setWidth(1)
                p.setPen(pen)
                p.setOpacity(0.4)
                p.drawLine(x, top, x, bot)
        finally:
            p.end()

# ── Constants ────────────────────────────────────────────────────────────────

VARLA_MIME = "application/x-varla-items"

_ICON_PATH = Path(__file__).parent / "icons" / "placeholder.png"


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class ColumnDef:
    """Column definition for a panel."""
    key: str
    label: str
    width: int = 120
    editable: bool = False
    numeric: bool = False
    min_val: float = 0
    max_val: float = 9999
    decimals: int = 0   # 0 = integer spinbox, >0 = double spinbox
    copy_action: bool = False  # renders "→" button that copies "base" → "current"
    vars_action: bool = False  # renders "Vars (N)" badge; click opens script-var dialog


@dataclass
class PanelItem:
    """A single item shown in a panel."""
    uid: str                # unique id within the page
    values: dict            # column_key -> display/edit value
    source: Any = None      # original model object (e.g. InventoryItem, Spell)

    def copy(self) -> "PanelItem":
        return PanelItem(uid=self.uid, values=dict(self.values), source=self.source)


# ── Proxy model (multi-column filter + numeric sort) ─────────────────────────

class MultiColumnFilter(QSortFilterProxyModel):
    """Filters rows by matching search text in ANY column, sorts numerics correctly."""

    def __init__(self, columns: list = None, parent=None):
        super().__init__(parent)
        self._columns = columns or []

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        pat = self.filterRegularExpression().pattern()
        if not pat:
            return True
        model = self.sourceModel()
        for col in range(model.columnCount()):
            idx = model.index(source_row, col, source_parent)
            if pat.lower() in str(model.data(idx, Qt.DisplayRole) or "").lower():
                return True
        return False

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        if self._columns and left.column() < len(self._columns):
            col = self._columns[left.column()]
            if col.numeric:
                try:
                    return float(left.data() or 0) < float(right.data() or 0)
                except (ValueError, TypeError):
                    pass
        return super().lessThan(left, right)


# ── Table model ───────────────────────────────────────────────────────────────

class PanelTableModel(QAbstractTableModel):
    """Holds PanelItem list, provides table data for both QTableView and QListView."""

    def __init__(self, columns: list[ColumnDef], editable_panel: bool = False, parent=None):
        super().__init__(parent)
        self._columns = columns
        self._items: list[PanelItem] = []
        self._editable_panel = editable_panel
        # Placeholder icon for grid view (DecorationRole column 0)
        if _ICON_PATH.exists():
            self._icon = QIcon(str(_ICON_PATH))
        else:
            pm = QPixmap(48, 48)
            pm.fill(QColor(COLORS.get("accent_gold_dim", "#6B5B2E")))
            self._icon = QIcon(pm)

    # ── Qt overrides ──────────────────────────────────────────────────────

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        item = self._items[index.row()]
        col = self._columns[index.column()]
        if role in (Qt.DisplayRole, Qt.EditRole):
            val = item.values.get(col.key, "")
            return "" if val is None else str(val)
        if role == Qt.DecorationRole and index.column() == 0:
            return self._icon
        if role == Qt.UserRole:
            return item.uid
        if role == Qt.UserRole + 1:
            return item
        return None

    def setData(self, index: QModelIndex, value, role=Qt.EditRole) -> bool:
        if not index.isValid() or not self._editable_panel:
            return False
        if role == Qt.EditRole:
            col = self._columns[index.column()]
            if col.editable:
                item = self._items[index.row()]
                if col.numeric:
                    try:
                        value = float(value) if col.decimals > 0 else int(float(value))
                    except (ValueError, TypeError):
                        return False
                item.values[col.key] = value
                self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
                return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        if self._editable_panel:
            col = self._columns[index.column()]
            if col.editable:
                f |= Qt.ItemIsEditable
        return f

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section].label
        return None

    def mimeTypes(self) -> list:
        return [VARLA_MIME]

    def mimeData(self, indices) -> QMimeData:
        rows = list({idx.row() for idx in indices})
        uids = [self._items[r].uid for r in rows if r < len(self._items)]
        mime = QMimeData()
        mime.setData(VARLA_MIME, json.dumps(uids).encode())
        return mime

    def supportedDragActions(self) -> Qt.DropActions:
        return Qt.CopyAction

    # ── Item management ───────────────────────────────────────────────────

    def set_items(self, items: list[PanelItem]):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def add_items(self, items: list[PanelItem]):
        if not items:
            return
        first = len(self._items)
        self.beginInsertRows(QModelIndex(), first, first + len(items) - 1)
        self._items.extend(items)
        self.endInsertRows()

    def remove_by_uids(self, uid_set: set):
        rows = [i for i, it in enumerate(self._items) if it.uid in uid_set]
        for row in reversed(rows):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()

    def take_by_uids(self, uid_set: set) -> list[PanelItem]:
        taken = [it for it in self._items if it.uid in uid_set]
        self.remove_by_uids(uid_set)
        return taken

    def get_all_items(self) -> list[PanelItem]:
        return list(self._items)

    def uid_set(self) -> set:
        return {it.uid for it in self._items}

    def clear(self):
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()


# ── Type-badge palette (per design tokens) ───────────────────────────────────
# Inventory item types and spell schools rendered as coloured pill badges.
_TYPE_BADGES = {
    # Inventory
    "Weapon":      ("#d88a6a", "#5a2a1a"),
    "Ammunition":  ("#c48a5a", "#5a3a1a"),
    "Ammo":        ("#c48a5a", "#5a3a1a"),
    "Armor":       ("#a0a8c0", "#2a3a5a"),
    "Armour":      ("#a0a8c0", "#2a3a5a"),
    "Clothing":    ("#c0a8c0", "#3a2a4a"),
    "Potion":      ("#a0c8a0", "#2a4a2a"),
    "Ingredient":  ("#c0c890", "#4a4a1a"),
    "Apparatus":   ("#a0b8c8", "#2a3a4a"),
    "Misc":        ("#b8a080", "#3a2a1a"),
    "Book":        ("#d8b890", "#4a2a1a"),
    "Key":         ("#e5b564", "#5a4a1a"),
    "Light":       ("#f0a050", "#5a3a1a"),
    # Spell schools
    "Alteration":  ("#a8c8b8", "#2a4a3a"),
    "Restoration": ("#d8c090", "#5a4a1a"),
    "Mysticism":   ("#b890d8", "#4a2a5a"),
    "Destruction": ("#e08866", "#5a2a1a"),
    "Conjuration": ("#a098c8", "#3a2a5a"),
    "Illusion":    ("#c8a8c8", "#4a2a4a"),
}

_BADGE_COLUMNS = {"type", "spell_type", "var_type"}


# ── Delegate (spinbox for numeric editable cells + type badges) ──────────────

class SpinDelegate(QStyledItemDelegate):
    def __init__(self, columns: list[ColumnDef], parent=None):
        super().__init__(parent)
        self._columns = columns

    def createEditor(self, parent, option, index):
        if index.column() < len(self._columns):
            col = self._columns[index.column()]
            if col.copy_action or col.vars_action:
                return None  # no editor for action button cells
            if col.editable and col.numeric:
                if col.decimals > 0:
                    sb = QDoubleSpinBox(parent)
                    sb.setDecimals(col.decimals)
                    sb.setRange(col.min_val, col.max_val)
                else:
                    sb = QSpinBox(parent)
                    sb.setRange(int(col.min_val), int(col.max_val))
                return sb
        return super().createEditor(parent, option, index)

    def paint(self, painter, option, index):
        if index.column() >= len(self._columns):
            super().paint(painter, option, index)
            return

        col = self._columns[index.column()]

        # ── copy-action arrow cell ───────────────────────────────────────
        if col.copy_action:
            self.initStyleOption(option, index)
            painter.save()
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(QColor(COLORS.get("brass_lit", "#c79443")))
            f = painter.font()
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(option.rect, Qt.AlignCenter, "→")
            painter.restore()
            return

        # ── vars-action button cell (script vars dialog launcher) ────────
        if col.vars_action:
            self.initStyleOption(option, index)
            painter.save()
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            text = str(index.data(Qt.DisplayRole) or "").strip()
            # Faded look when no vars (count == 0 or blank)
            has_vars = bool(text and text not in ("0", "—"))
            fg = QColor(COLORS.get("brass_lit", "#c79443") if has_vars
                        else COLORS.get("text_muted", "#7a6a4a"))
            border = QColor("#3a2912")
            m = 4
            pill_h = min(option.rect.height() - 2 * m, 18)
            pill_y = option.rect.y() + (option.rect.height() - pill_h) // 2
            pill_w = max(0, option.rect.width() - 2 * m)
            pill_rect = QRect(option.rect.x() + m, pill_y, pill_w, pill_h)
            painter.setPen(border)
            painter.setBrush(QColor("#0b0804"))
            painter.drawRoundedRect(pill_rect, 2, 2)
            painter.setPen(fg)
            label = f"Vars ({text or '0'})" if has_vars else "—"
            painter.drawText(pill_rect, Qt.AlignCenter, label)
            painter.restore()
            return

        # ── type-badge pill (Type / Spell Type / Var Type) ───────────────
        if col.key in _BADGE_COLUMNS:
            text = str(index.data(Qt.DisplayRole) or "").strip()
            if text:
                # Match the canonical badge keys case-insensitively
                key = next((k for k in _TYPE_BADGES if k.lower() == text.lower()), None)
                fg, border = _TYPE_BADGES.get(key, ("#b89a6a", "#3a2912"))
                painter.save()
                # selection / hover bg from default
                if option.state & QStyle.State_Selected:
                    painter.fillRect(option.rect, option.palette.highlight())
                # Draw the pill
                m = 4
                pill_h = min(option.rect.height() - 2 * m, 18)
                pill_y = option.rect.y() + (option.rect.height() - pill_h) // 2
                # Width: text + horizontal padding
                f = painter.font()
                f.setPointSize(max(8, f.pointSize() - 1))
                f.setCapitalization(QFont.Capitalization.AllUppercase)
                painter.setFont(f)
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(text.upper()) + 14
                pill_w = min(tw, option.rect.width() - 2 * m)
                pill_rect = QRect(option.rect.x() + m, pill_y, pill_w, pill_h)
                painter.setPen(QColor(border))
                painter.setBrush(QColor("#0b0804"))
                painter.drawRoundedRect(pill_rect, 2, 2)
                painter.setPen(QColor(fg))
                painter.drawText(pill_rect, Qt.AlignCenter, text.upper())
                painter.restore()
                return

        super().paint(painter, option, index)

    def setEditorData(self, editor, index):
        val = index.data(Qt.EditRole)
        try:
            if isinstance(editor, QDoubleSpinBox):
                editor.setValue(float(val or 0))
            elif isinstance(editor, QSpinBox):
                editor.setValue(int(float(val or 0)))
            else:
                super().setEditorData(editor, index)
        except (ValueError, TypeError):
            pass

    def setModelData(self, editor, model, index):
        if isinstance(editor, (QSpinBox, QDoubleSpinBox)):
            model.setData(index, editor.value(), Qt.EditRole)
        else:
            super().setModelData(editor, model, index)


# ── Paint mode (toolbar-button trigger → drag-paint a value onto rows) ──────

class _PaintValuePopup(QFrame):
    """Toolbar-button popup for arming paint mode.

    Lets the user pick which editable numeric column to paint, and the value
    to apply. After Confirm, paint mode is armed: the next click+drag on the
    staged view paints `value` onto every row hovered, then auto-disarms.
    """
    confirmed = Signal(int, float)  # column index, value

    def __init__(self, columns: list, parent=None):
        super().__init__(parent, Qt.Popup)
        self.setObjectName("paintPopup")
        self.setStyleSheet(
            "QFrame#paintPopup {"
            f"  background-color: {INK_VOID};"
            "   border: 1px solid #6a4f1c;"
            "   border-radius: 2px;"
            "}"
            "QFrame#paintPopup QLabel {"
            "   background: transparent;"
            f"  color: {COLORS.get('brass_lit', '#c79443')};"
            "   font-size: 10pt;"
            "}"
        )
        # Restrict to columns that are actually paintable
        self._paintable = [(i, c) for i, c in enumerate(columns) if c.editable and c.numeric]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        title = QLabel(tr("Paint value onto rows"))
        f = title.font(); f.setBold(True); title.setFont(f)
        layout.addWidget(title)

        col_row = QHBoxLayout()
        col_row.setSpacing(8)
        col_row.addWidget(QLabel(tr("Column:")))
        self._col_combo = QComboBox()
        for col_idx, col_def in self._paintable:
            self._col_combo.addItem(col_def.label, col_idx)
        col_row.addWidget(self._col_combo, 1)
        layout.addLayout(col_row)

        val_row = QHBoxLayout()
        val_row.setSpacing(8)
        val_row.addWidget(QLabel(tr("Value:")))
        # Both spinboxes are kept and swapped via QStackedWidget when the
        # column type changes (int vs float).
        self._val_stack = QStackedWidget()
        self._spin_int = QSpinBox()
        self._spin_float = QDoubleSpinBox()
        self._val_stack.addWidget(self._spin_int)
        self._val_stack.addWidget(self._spin_float)
        val_row.addWidget(self._val_stack, 1)
        layout.addLayout(val_row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setFixedHeight(24)
        cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(cancel_btn)
        confirm_btn = QPushButton(tr("Confirm"))
        confirm_btn.setFixedHeight(24)
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

        self._col_combo.currentIndexChanged.connect(self._sync_spinbox)
        self._sync_spinbox()

    def _current(self) -> tuple:
        idx = self._col_combo.currentIndex()
        if idx < 0 or idx >= len(self._paintable):
            return (-1, None)
        return self._paintable[idx]

    def _sync_spinbox(self):
        col_idx, col_def = self._current()
        if col_def is None:
            return
        if col_def.decimals > 0:
            self._spin_float.setDecimals(col_def.decimals)
            self._spin_float.setRange(col_def.min_val, col_def.max_val)
            self._val_stack.setCurrentWidget(self._spin_float)
            self._spin_float.setFocus()
            self._spin_float.selectAll()
        else:
            self._spin_int.setRange(int(col_def.min_val), int(col_def.max_val))
            self._val_stack.setCurrentWidget(self._spin_int)
            self._spin_int.setFocus()
            self._spin_int.selectAll()

    def _on_confirm(self):
        col_idx, col_def = self._current()
        if col_def is None:
            self.close()
            return
        if col_def.decimals > 0:
            value = float(self._spin_float.value())
        else:
            value = float(self._spin_int.value())
        self.confirmed.emit(col_idx, value)
        self.close()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._on_confirm()
            return
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_selected_uids(view) -> list[str]:
    """Return UIDs of selected rows from a QTableView or QListView."""
    proxy = view.model()
    if proxy is None:
        return []
    rows = {idx.row() for idx in view.selectionModel().selectedRows()}
    if isinstance(proxy, QSortFilterProxyModel):
        src = proxy.sourceModel()
        uids = []
        for proxy_row in rows:
            src_idx = proxy.mapToSource(proxy.index(proxy_row, 0))
            r = src_idx.row()
            if 0 <= r < len(src._items):
                uids.append(src._items[r].uid)
        return uids
    return [proxy._items[r].uid for r in rows if r < len(proxy._items)]


# ── List view (QTableView) ────────────────────────────────────────────────────

class PanelView(QTableView):
    """Table view with drag-drop and double-click-to-move."""
    move_requested = Signal(list)   # [uid, ...] — fired from source (double-click)
    drop_received  = Signal(list)   # [uid, ...] — fired on destination (drop)
    vars_action_requested = Signal(object)  # PanelItem — fired when a vars-action cell is clicked

    def __init__(self, panel_id: str, parent=None):
        super().__init__(parent)
        self.panel_id = panel_id
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.horizontalHeader().setHighlightSections(False)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
        )
        # Paint-mode state (only meaningful on the editable/staged view)
        self._paint_armed: bool = False
        self._paint_col: int = -1
        self._paint_value: float = 0.0
        self._paint_painted_uids: set = set()

    # ── Paint mode ────────────────────────────────────────────────────────

    def arm_paint(self, column: int, value: float):
        """Enter paint mode. Next press+drag paints `value` into `column`
        on every row hovered, then auto-disarms on release."""
        self._paint_armed = True
        self._paint_col = column
        self._paint_value = value
        self._paint_painted_uids.clear()
        self.viewport().setCursor(Qt.CrossCursor)

    def _disarm_paint(self):
        self._paint_armed = False
        self._paint_col = -1
        self._paint_painted_uids.clear()
        self.viewport().unsetCursor()

    def _paint_at(self, viewport_pos):
        idx = self.indexAt(viewport_pos)
        if not idx.isValid():
            return
        proxy = self.model()
        src_model = proxy.sourceModel() if isinstance(proxy, QSortFilterProxyModel) else proxy
        src_idx = proxy.mapToSource(idx) if isinstance(proxy, QSortFilterProxyModel) else idx
        row = src_idx.row()
        if row < 0 or row >= len(src_model._items):
            return
        uid = src_model._items[row].uid
        if uid in self._paint_painted_uids:
            return  # already painted in this drag pass
        self._paint_painted_uids.add(uid)
        if 0 <= self._paint_col < src_model.columnCount():
            target = src_model.index(row, self._paint_col)
            src_model.setData(target, self._paint_value, Qt.EditRole)

    def mousePressEvent(self, event):
        # Paint mode wins over every other left-click handler so the press
        # doesn't also start a selection / drag.
        if self._paint_armed and event.button() == Qt.LeftButton:
            self._paint_at(event.pos())
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            idx = self.indexAt(event.pos())
            if idx.isValid():
                proxy = self.model()
                src_model = proxy.sourceModel() if isinstance(proxy, QSortFilterProxyModel) else proxy
                src_idx = proxy.mapToSource(idx) if isinstance(proxy, QSortFilterProxyModel) else idx
                if src_idx.column() < len(src_model._columns):
                    col = src_model._columns[src_idx.column()]
                    if col.copy_action and src_model._editable_panel:
                        self._copy_base_to_current(src_model, src_idx.row())
                        return
                    if col.vars_action:
                        row = src_idx.row()
                        if 0 <= row < len(src_model._items):
                            self.vars_action_requested.emit(src_model._items[row])
                        return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._paint_armed and (event.buttons() & Qt.LeftButton):
            self._paint_at(event.pos())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._paint_armed and event.button() == Qt.LeftButton:
            self._disarm_paint()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _copy_base_to_current(self, src_model, row):
        cols = src_model._columns
        base_col = next((i for i, c in enumerate(cols) if c.key == "base"), -1)
        cur_col  = next((i for i, c in enumerate(cols) if c.key == "current"), -1)
        if base_col < 0 or cur_col < 0:
            return
        base_val = src_model.data(src_model.index(row, base_col), Qt.DisplayRole)
        src_model.setData(src_model.index(row, cur_col), base_val, Qt.EditRole)

    def mouseDoubleClickEvent(self, event):
        idx = self.indexAt(event.pos())
        if idx.isValid():
            proxy = self.model()
            src_model = proxy.sourceModel() if isinstance(proxy, QSortFilterProxyModel) else proxy
            src_idx = proxy.mapToSource(idx) if isinstance(proxy, QSortFilterProxyModel) else idx
            col = src_model._columns[src_idx.column()]
            # Open editor if this cell is editable
            if src_model._editable_panel and col.editable:
                super().mouseDoubleClickEvent(event)
                return
            # Only shift panels when double-clicking the name column (col 0)
            if src_idx.column() != 0:
                return
        uids = _get_selected_uids(self)
        if uids:
            self.move_requested.emit(uids)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(VARLA_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(VARLA_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(VARLA_MIME):
            uids = json.loads(bytes(event.mimeData().data(VARLA_MIME)).decode())
            self.drop_received.emit(uids)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ── Grid view (QListView icon mode) ──────────────────────────────────────────

class PanelGridView(QListView):
    """Icon-mode list view with rubber-band selection and drag-drop."""
    move_requested = Signal(list)
    drop_received  = Signal(list)

    def __init__(self, panel_id: str, parent=None):
        super().__init__(parent)
        self.panel_id = panel_id
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.CopyAction)
        self.setGridSize(QSize(110, 90))
        self.setIconSize(QSize(40, 40))
        self.setSpacing(4)
        self.setWordWrap(True)
        self.setUniformItemSizes(True)

    def mouseDoubleClickEvent(self, event):
        uids = _get_selected_uids(self)
        if uids:
            self.move_requested.emit(uids)
        super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(VARLA_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(VARLA_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(VARLA_MIME):
            uids = json.loads(bytes(event.mimeData().data(VARLA_MIME)).decode())
            self.drop_received.emit(uids)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


# ── DualPanelWidget ───────────────────────────────────────────────────────────

class DualPanelWidget(QWidget):
    """
    Two-panel staging widget.

    Left  = Available (all items from the dump).
    Right = Staged for Import (items that will be written on save).

    Items move via drag-drop, double-click, or the centre transfer buttons.
    The right panel allows inline editing of editable columns.
    """
    staged_changed = Signal()
    clear_target_requested = Signal()

    def __init__(self, columns: list[ColumnDef], parent=None):
        super().__init__(parent)
        self._columns = columns
        self._left_model  = PanelTableModel(columns, editable_panel=False)
        self._right_model = PanelTableModel(columns, editable_panel=True)
        self._left_proxy  = MultiColumnFilter(columns)
        self._left_proxy.setSourceModel(self._left_model)
        self._right_proxy = MultiColumnFilter(columns)
        self._right_proxy.setSourceModel(self._right_model)
        self._setup_ui()

    # ── UI construction ───────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        left_frame, self._left_list, self._left_grid, self._left_stack = \
            self._build_panel("left", tr("Available"),
                              self._left_model, self._left_proxy)
        center_frame = self._build_center_buttons()
        right_frame, self._right_list, self._right_grid, self._right_stack = \
            self._build_panel("right", tr("Staged for target.txt"),
                              self._right_model, self._right_proxy)

        splitter.addWidget(left_frame)
        splitter.addWidget(center_frame)
        splitter.addWidget(right_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        layout.addWidget(splitter)

    def _build_panel(self, panel_id: str, title: str,
                     model: PanelTableModel, proxy: MultiColumnFilter):
        # The panel itself is a corner-flourished frame
        is_staged = (panel_id == "right")
        kind = "staged" if is_staged else "available"

        frame = _PanelFrame()
        frame.setObjectName("varlaPanel")
        frame.setProperty("panelKind", kind)
        layout = QVBoxLayout(frame)
        # leave a 10px outer margin so the corner brackets are visible
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────
        header_bar = QFrame()
        header_bar.setObjectName("varlaPanelHeader")
        header_bar.setProperty("panelKind", kind)
        header_bar.setMinimumHeight(34)

        header = QHBoxLayout(header_bar)
        header.setContentsMargins(14, 6, 14, 6)
        header.setSpacing(10)

        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("panelHeader")
        title_lbl.setProperty("panelKind", kind)
        header.addWidget(title_lbl)
        header.addStretch()

        counter = QLabel("0 items")
        counter.setObjectName("counterLabel")
        counter.setProperty("panelKind", kind)
        header.addWidget(counter)

        # Paint button (staged panel only). Only shown when the page actually
        # has at least one editable numeric column to paint into.
        if is_staged and any(c.editable and c.numeric for c in self._columns):
            paint_btn = QPushButton("🖌")
            paint_btn.setObjectName("viewToggleBtn")
            paint_btn.setFixedSize(24, 22)
            paint_btn.setCursor(Qt.PointingHandCursor)
            paint_btn.setToolTip(tr(
                "Paint a value onto rows. After Confirm, click and drag over "
                "rows to apply the value; release to disarm."
            ))
            paint_btn.clicked.connect(
                lambda _checked, b=paint_btn: self._open_paint_popup(b)
            )
            header.addWidget(paint_btn)

        list_btn = QPushButton("≡")
        grid_btn = QPushButton("⊞")
        for btn in [list_btn, grid_btn]:
            btn.setFixedSize(24, 22)
            btn.setObjectName("viewToggleBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
        list_btn.setChecked(True)
        header.addWidget(list_btn)
        header.addWidget(grid_btn)
        layout.addWidget(header_bar)

        # ── Search row ────────────────────────────────────────────────────
        search_row = QFrame()
        search_row.setObjectName("varlaSearchRow")
        sr_layout = QHBoxLayout(search_row)
        sr_layout.setContentsMargins(12, 8, 12, 8)
        sr_layout.setSpacing(8)

        search = QLineEdit()
        search.setPlaceholderText(tr("Search..."))
        search.setObjectName("searchBar")
        search.setClearButtonEnabled(True)
        search.textChanged.connect(proxy.setFilterFixedString)
        sr_layout.addWidget(search, 1)
        layout.addWidget(search_row)

        # ── View stack ────────────────────────────────────────────────────
        stack = QStackedWidget()

        list_view = PanelView(panel_id)
        list_view.setModel(proxy)
        list_view.setItemDelegate(SpinDelegate(self._columns))
        for i, col in enumerate(self._columns):
            list_view.horizontalHeader().resizeSection(i, col.width)

        grid_view = PanelGridView(panel_id)
        grid_view.setModel(proxy)

        stack.addWidget(list_view)
        stack.addWidget(grid_view)
        layout.addWidget(stack, 1)

        # View toggle logic
        list_btn.clicked.connect(
            lambda: (stack.setCurrentIndex(0),
                     list_btn.setChecked(True), grid_btn.setChecked(False)))
        grid_btn.clicked.connect(
            lambda: (stack.setCurrentIndex(1),
                     grid_btn.setChecked(True), list_btn.setChecked(False)))

        # Move signals
        # double-click fires on the SOURCE panel → move to the OTHER side
        def on_move(uids):
            if panel_id == "left":
                self._move_to_right(uids)
            else:
                self._move_to_left(uids)

        # drop fires on the DESTINATION panel → move TO this side
        def on_drop(uids):
            if panel_id == "right":
                self._move_to_right(uids)
            else:
                self._move_to_left(uids)

        list_view.move_requested.connect(on_move)
        list_view.drop_received.connect(on_drop)
        grid_view.move_requested.connect(on_move)
        grid_view.drop_received.connect(on_drop)
        # Vars-action: forward to a panel-level dispatcher so the parent panel
        # can refresh the row count after the dialog closes.
        list_view.vars_action_requested.connect(
            lambda pi, m=model: self._open_vars_dialog(pi, m))

        # Counter update
        def update_counter():
            n = model.rowCount()
            if is_staged:
                counter.setText(f"{n}")
            else:
                counter.setText(f"{n} item{'s' if n != 1 else ''}")

        model.rowsInserted.connect(lambda *_: update_counter())
        model.rowsRemoved.connect(lambda *_: update_counter())
        model.modelReset.connect(update_counter)

        return frame, list_view, grid_view, stack

    def _build_center_buttons(self) -> QFrame:
        frame = _XferColumn()
        frame.setObjectName("xferColumn")
        frame.setFixedWidth(86)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        def _make_xfer(label: str, object_name: str, slot) -> QPushButton:
            b = QPushButton(label)
            b.setObjectName(object_name)
            b.setFixedWidth(64)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            return b

        # Group 1 — SEND RIGHT (All / Sel)
        lbl_right = QLabel(tr("SEND RIGHT"))
        lbl_right.setObjectName("xferGroupLabel")
        layout.addWidget(lbl_right)
        layout.addWidget(_make_xfer("⟫  All", "xferBtnStrong", self._move_all_to_right))
        layout.addWidget(_make_xfer("⟩  Sel", "xferBtn",       self._move_selected_to_right))

        layout.addSpacing(14)

        # Group 2 — SEND LEFT (Sel / All)
        lbl_left = QLabel(tr("SEND LEFT"))
        lbl_left.setObjectName("xferGroupLabel")
        layout.addWidget(lbl_left)
        layout.addWidget(_make_xfer("⟨  Sel", "xferBtn",       self._move_selected_to_left))
        layout.addWidget(_make_xfer("⟪  All", "xferBtnStrong", self._move_all_to_left))

        layout.addSpacing(14)

        # Group 3 — CLEAR (destructive)
        lbl_clear = QLabel(tr("CLEAR"))
        lbl_clear.setObjectName("xferGroupLabel")
        layout.addWidget(lbl_clear)
        clear_btn = _make_xfer(tr("Clear"), "xferBtnDanger", self.clear_target_requested.emit)
        layout.addWidget(clear_btn)

        layout.addStretch()
        return frame

    # ── Paint mode wiring ─────────────────────────────────────────────────

    def _open_paint_popup(self, anchor_widget: QWidget):
        """Show the paint popup anchored under `anchor_widget` (the toolbar
        button). Confirm arms paint mode on the staged view."""
        # Skip pages that have nothing paintable (no editable numeric cols)
        if not any(c.editable and c.numeric for c in self._columns):
            return
        popup = _PaintValuePopup(self._columns, parent=self)
        popup.confirmed.connect(
            lambda col, val: self._right_list.arm_paint(col, val)
        )
        popup.adjustSize()
        # Right-align the popup with the button so it doesn't overflow off-screen
        anchor = anchor_widget.mapToGlobal(QPoint(
            anchor_widget.width() - popup.width(),
            anchor_widget.height() + 2,
        ))
        popup.move(anchor)
        popup.show()

    # ── Quest script vars dialog ──────────────────────────────────────────

    def _open_vars_dialog(self, panel_item, model: PanelTableModel):
        """Open the QuestScriptVarDialog for the row's source quest.

        Mutates the quest's script_vars list in place; updates the row's
        displayed count if any value changes.
        """
        # Local import keeps dual_panel decoupled from the dialog module.
        from quest_vars_dialog import QuestScriptVarDialog

        source = panel_item.source
        script_vars = getattr(source, "script_vars", None)
        if script_vars is None:
            return

        quest_label = (
            getattr(source, "name", "") or
            getattr(source, "editor_id", "") or
            getattr(source, "form_id", "(quest)")
        )

        dlg = QuestScriptVarDialog(script_vars, quest_label, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.was_modified:
            # Re-render the row's "Vars" cell so the count reflects edits if any
            # vars were added/removed (currently we only edit values, but keep
            # this future-proof).
            for row, it in enumerate(model._items):
                if it.uid == panel_item.uid:
                    model.dataChanged.emit(
                        model.index(row, 0),
                        model.index(row, model.columnCount() - 1),
                    )
                    break
            self.staged_changed.emit()

    # ── Transfer operations ───────────────────────────────────────────────

    def _move_to_right(self, uids: list):
        uid_set = set(uids) - self._right_model.uid_set()
        items = self._left_model.take_by_uids(uid_set)
        if items:
            self._right_model.add_items(items)
            self.staged_changed.emit()

    def _move_to_left(self, uids: list):
        uid_set = set(uids) - self._left_model.uid_set()
        items = self._right_model.take_by_uids(uid_set)
        if items:
            self._left_model.add_items(items)
            self.staged_changed.emit()

    def _move_all_to_right(self):
        items = self._left_model.get_all_items()
        self._left_model.clear()
        new = [it for it in items if it.uid not in self._right_model.uid_set()]
        if new:
            self._right_model.add_items(new)
        if items:
            self.staged_changed.emit()

    def _move_all_to_left(self):
        items = self._right_model.get_all_items()
        self._right_model.clear()
        new = [it for it in items if it.uid not in self._left_model.uid_set()]
        if new:
            self._left_model.add_items(new)
        if items:
            self.staged_changed.emit()

    def _move_selected_to_right(self):
        view = self._left_list if self._left_stack.currentIndex() == 0 else self._left_grid
        self._move_to_right(_get_selected_uids(view))

    def _move_selected_to_left(self):
        view = self._right_list if self._right_stack.currentIndex() == 0 else self._right_grid
        self._move_to_left(_get_selected_uids(view))

    # ── Public API ────────────────────────────────────────────────────────

    def set_items(self, items: list[PanelItem]):
        """Populate the left panel. Clears both panels first."""
        self._left_model.set_items(items)
        self._right_model.clear()

    def get_staged_items(self) -> list[PanelItem]:
        """Return all items currently in the right (staged) panel."""
        return self._right_model.get_all_items()

    def clear(self):
        self._left_model.clear()
        self._right_model.clear()
