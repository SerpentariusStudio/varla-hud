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
    QStackedWidget, QSpinBox, QDoubleSpinBox, QStyle,
)
from PySide6.QtCore import (
    Qt, Signal, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel, QMimeData, QSize,
)
from PySide6.QtGui import QDrag, QPixmap, QIcon, QColor

from theme import COLORS

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


# ── Delegate (spinbox for numeric editable cells) ─────────────────────────────

class SpinDelegate(QStyledItemDelegate):
    def __init__(self, columns: list[ColumnDef], parent=None):
        super().__init__(parent)
        self._columns = columns

    def createEditor(self, parent, option, index):
        if index.column() < len(self._columns):
            col = self._columns[index.column()]
            if col.copy_action:
                return None  # no editor for copy button cells
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
        if index.column() < len(self._columns) and self._columns[index.column()].copy_action:
            self.initStyleOption(option, index)
            painter.save()
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.setPen(QColor(COLORS.get("accent", "#c8a84b")))
            f = painter.font()
            f.setBold(True)
            painter.setFont(f)
            painter.drawText(option.rect, Qt.AlignCenter, "→")
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

    def mousePressEvent(self, event):
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
        super().mousePressEvent(event)

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
            self._build_panel("left", "Available",
                              self._left_model, self._left_proxy)
        center_frame = self._build_center_buttons()
        right_frame, self._right_list, self._right_grid, self._right_stack = \
            self._build_panel("right", "Staged for Import",
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
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header row
        header = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setObjectName("panelHeader")
        header.addWidget(title_lbl)
        header.addStretch()

        counter = QLabel("0 items")
        counter.setObjectName("counterLabel")
        header.addWidget(counter)

        list_btn = QPushButton("≡")
        grid_btn = QPushButton("⊞")
        for btn in [list_btn, grid_btn]:
            btn.setFixedSize(26, 26)
            btn.setObjectName("viewToggleBtn")
            btn.setCheckable(True)
        list_btn.setChecked(True)
        header.addWidget(list_btn)
        header.addWidget(grid_btn)
        layout.addLayout(header)

        # Search bar
        search = QLineEdit()
        search.setPlaceholderText("Filter…")
        search.setObjectName("searchBar")
        search.setClearButtonEnabled(True)
        search.textChanged.connect(proxy.setFilterFixedString)
        layout.addWidget(search)

        # View stack
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

        # Counter update
        def update_counter():
            n = model.rowCount()
            counter.setText(f"{n} item{'s' if n != 1 else ''}")

        model.rowsInserted.connect(lambda *_: update_counter())
        model.rowsRemoved.connect(lambda *_: update_counter())
        model.modelReset.connect(update_counter)

        return frame, list_view, grid_view, stack

    def _build_center_buttons(self) -> QFrame:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setAlignment(Qt.AlignCenter)
        frame.setFixedWidth(90)
        for label, slot in [
            ("All →",  self._move_all_to_right),
            ("Sel →",  self._move_selected_to_right),
            ("← Sel",  self._move_selected_to_left),
            ("← All",  self._move_all_to_left),
        ]:
            btn = QPushButton(label)
            btn.setObjectName("transferBtn")
            btn.setFixedWidth(80)
            btn.clicked.connect(slot)
            layout.addWidget(btn)
        return frame

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
