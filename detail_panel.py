"""
Varla Detail Panel - Always-visible right panel for item/spell details and Varla actions.
Shows selected item details, favorite/exception toggles, bank button, and per-item notes.
Spell view includes editable fields for magicka cost and per-effect properties.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFormLayout, QFrame, QSizePolicy, QSpinBox, QComboBox,
    QGroupBox, QScrollArea
)
from PySide6.QtCore import Signal, Qt

from theme import COLORS


class VarlaDetailPanel(QWidget):
    """Right-side detail panel showing selected item info and Varla actions."""

    # Signals
    favorite_toggled = Signal(str, str)    # (category, identifier)
    exception_toggled = Signal(str, str)   # (category, identifier)
    bank_requested = Signal(str, str, str) # (category, form_id, name)
    note_changed = Signal(str, str)        # (identifier, text)
    spell_modified = Signal(str, dict)     # (form_id, modified_fields)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailPanel")
        self.setMinimumWidth(300)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self._current_category = ""
        self._current_identifier = ""
        self._current_form_id = ""
        self._current_name = ""
        self._is_favorite = False
        self._is_exception = False
        self._note_updating = False  # prevent signal loops
        self._spell_updating = False  # prevent signal loops during spell populate
        self._current_spell = None  # reference to current spell object
        self._effect_widgets = []  # list of dicts with effect edit widgets

        self._build_ui()
        self.clear()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Placeholder message (shown when nothing selected)
        self.placeholder_label = QLabel("Select an item to see details")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 11pt;
            font-style: italic;
            padding: 40px 20px;
        """)
        layout.addWidget(self.placeholder_label)

        # Detail content container (hidden until item selected)
        self.detail_container = QWidget()
        detail_outer_layout = QVBoxLayout(self.detail_container)
        detail_outer_layout.setContentsMargins(0, 0, 0, 0)
        detail_outer_layout.setSpacing(0)

        # Scroll area wrapping all detail content
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.NoFrame)
        detail_scroll_widget = QWidget()
        detail_layout = QVBoxLayout(detail_scroll_widget)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(8)

        # Title
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet(f"""
            font-size: 13pt;
            font-weight: bold;
            color: {COLORS['accent_gold']};
            padding-bottom: 4px;
        """)
        detail_layout.addWidget(self.title_label)

        # Form ID
        self.form_id_label = QLabel()
        self.form_id_label.setStyleSheet(f"""
            font-size: 9pt;
            color: {COLORS['text_muted']};
            font-family: 'Courier New', monospace;
        """)
        detail_layout.addWidget(self.form_id_label)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background-color: {COLORS['border_primary']};")
        detail_layout.addWidget(sep1)

        # Detail form area (for non-spell fields)
        self.detail_form = QFormLayout()
        self.detail_form.setContentsMargins(0, 4, 0, 4)
        self.detail_form.setSpacing(6)
        detail_layout.addLayout(self.detail_form)

        # We'll create labels dynamically for each field
        self._detail_labels = {}

        # Spell edit area (hidden unless viewing a spell)
        self.spell_edit_container = QWidget()
        spell_edit_layout = QVBoxLayout(self.spell_edit_container)
        spell_edit_layout.setContentsMargins(0, 4, 0, 4)
        spell_edit_layout.setSpacing(6)

        # Magicka cost
        cost_layout = QHBoxLayout()
        cost_layout.addWidget(QLabel("Magicka Cost:"))
        self.spell_cost_spin = QSpinBox()
        self.spell_cost_spin.setRange(0, 99999)
        self.spell_cost_spin.valueChanged.connect(self._on_spell_cost_changed)
        cost_layout.addWidget(self.spell_cost_spin)
        cost_layout.addStretch()
        spell_edit_layout.addLayout(cost_layout)

        # Spell type label
        self.spell_type_label = QLabel()
        spell_edit_layout.addWidget(self.spell_type_label)

        # Effects container (will hold per-effect edit rows)
        self.effects_group = QGroupBox("Effects")
        self.effects_layout = QVBoxLayout(self.effects_group)
        self.effects_layout.setSpacing(4)
        spell_edit_layout.addWidget(self.effects_group)

        self.spell_edit_container.hide()
        detail_layout.addWidget(self.spell_edit_container)

        # Separator before actions
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background-color: {COLORS['border_primary']};")
        detail_layout.addWidget(sep2)

        # Action buttons row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)

        self.fav_btn = QPushButton("☆ Favorite")
        self.fav_btn.setObjectName("detailFavBtn")
        self.fav_btn.setCursor(Qt.PointingHandCursor)
        self.fav_btn.clicked.connect(self._on_favorite_clicked)
        actions_layout.addWidget(self.fav_btn)

        self.exc_btn = QPushButton("△ Exception")
        self.exc_btn.setObjectName("detailExcBtn")
        self.exc_btn.setCursor(Qt.PointingHandCursor)
        self.exc_btn.clicked.connect(self._on_exception_clicked)
        actions_layout.addWidget(self.exc_btn)

        detail_layout.addLayout(actions_layout)

        # Bank button
        self.bank_btn = QPushButton("Bank Item")
        self.bank_btn.setObjectName("detailBankBtn")
        self.bank_btn.setCursor(Qt.PointingHandCursor)
        self.bank_btn.clicked.connect(self._on_bank_clicked)
        detail_layout.addWidget(self.bank_btn)

        # Separator before notes
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setFixedHeight(1)
        sep3.setStyleSheet(f"background-color: {COLORS['border_primary']};")
        detail_layout.addWidget(sep3)

        # Notes section
        notes_header = QLabel("Notes")
        notes_header.setStyleSheet(f"""
            font-weight: bold;
            font-size: 10pt;
            color: {COLORS['text_secondary']};
        """)
        detail_layout.addWidget(notes_header)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add notes for this item...")
        self.notes_edit.setMaximumHeight(120)
        self.notes_edit.textChanged.connect(self._on_note_changed)
        detail_layout.addWidget(self.notes_edit)

        detail_layout.addStretch()
        detail_scroll.setWidget(detail_scroll_widget)
        detail_outer_layout.addWidget(detail_scroll)
        layout.addWidget(self.detail_container)

    def clear(self):
        """Reset to placeholder state."""
        self._current_category = ""
        self._current_identifier = ""
        self._current_form_id = ""
        self._current_name = ""
        self._is_favorite = False
        self._is_exception = False
        self._current_spell = None
        self.placeholder_label.show()
        self.detail_container.hide()

    def _show_detail(self, title, form_id, category, identifier, fields,
                     is_fav=False, is_exc=False, show_bank=True, note_text=""):
        """Common method to display item/spell/etc details."""
        self._current_category = category
        self._current_identifier = identifier
        self._current_form_id = form_id
        self._current_name = title
        self._is_favorite = is_fav
        self._is_exception = is_exc

        self.placeholder_label.hide()
        self.detail_container.show()

        self.title_label.setText(title)
        self.form_id_label.setText(form_id if form_id else "")
        self.form_id_label.setVisible(bool(form_id))

        # Clear old detail fields
        while self.detail_form.count():
            item = self.detail_form.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._detail_labels.clear()

        # Hide spell edit area by default
        self.spell_edit_container.hide()
        self._current_spell = None

        # Add new fields
        for field_name, field_value in fields.items():
            label = QLabel(str(field_value))
            label.setWordWrap(True)
            self.detail_form.addRow(f"{field_name}:", label)
            self._detail_labels[field_name] = label

        # Update action buttons
        self._update_fav_btn()
        self._update_exc_btn()
        self.bank_btn.setVisible(show_bank)

        # Update notes
        self._note_updating = True
        self.notes_edit.setText(note_text)
        self._note_updating = False

    def _update_fav_btn(self):
        if self._is_favorite:
            self.fav_btn.setText("★ Favorited")
            self.fav_btn.setStyleSheet(f"""
                background-color: {COLORS['favorite_row']};
                color: {COLORS['favorite_text']};
                font-weight: bold;
                border: 1px solid {COLORS['star_active']};
            """)
        else:
            self.fav_btn.setText("☆ Favorite")
            self.fav_btn.setStyleSheet("")

    def _update_exc_btn(self):
        if self._is_exception:
            self.exc_btn.setText("⚠ Exception")
            self.exc_btn.setStyleSheet(f"""
                background-color: {COLORS['exception_row']};
                color: {COLORS['exception_text']};
                font-weight: bold;
                border: 1px solid {COLORS['exception_active']};
            """)
        else:
            self.exc_btn.setText("△ Exception")
            self.exc_btn.setStyleSheet("")

    def _on_favorite_clicked(self):
        self._is_favorite = not self._is_favorite
        self._update_fav_btn()
        self.favorite_toggled.emit(self._current_category, self._current_identifier)

    def _on_exception_clicked(self):
        self._is_exception = not self._is_exception
        self._update_exc_btn()
        self.exception_toggled.emit(self._current_category, self._current_identifier)

    def _on_bank_clicked(self):
        self.bank_requested.emit(
            self._current_category, self._current_form_id, self._current_name
        )

    def _on_note_changed(self):
        if not self._note_updating and self._current_identifier:
            self.note_changed.emit(
                self._current_identifier, self.notes_edit.toPlainText()
            )

    # ── Spell edit callbacks ─────────────────────────────────────────────

    def _on_spell_cost_changed(self, value):
        """Handle magicka cost spinbox change."""
        if self._spell_updating or not self._current_spell:
            return
        self._current_spell.magicka_cost = value
        self.spell_modified.emit(self._current_form_id, {"magicka_cost": value})

    def _on_effect_changed(self, effect_idx):
        """Handle a spell effect property change."""
        if self._spell_updating or not self._current_spell:
            return
        if effect_idx >= len(self._current_spell.effects) or effect_idx >= len(self._effect_widgets):
            return

        ew = self._effect_widgets[effect_idx]
        eff = self._current_spell.effects[effect_idx]

        eff.magnitude = ew["mag_spin"].value()
        eff.duration = ew["dur_spin"].value()
        eff.area = ew["area_spin"].value()
        eff.range = ew["range_combo"].currentText()

        self.spell_modified.emit(self._current_form_id, {
            "effects": [
                {"idx": effect_idx, "magnitude": eff.magnitude,
                 "duration": eff.duration, "area": eff.area, "range": eff.range}
            ]
        })

    def _build_effect_widgets(self, spell):
        """Build editable widgets for each spell effect."""
        # Clear existing
        self._effect_widgets.clear()
        while self.effects_layout.count():
            child = self.effects_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for idx, eff in enumerate(spell.effects):
            frame = QFrame()
            frame.setStyleSheet(f"border: 1px solid {COLORS['border_primary']}; padding: 4px;")
            eff_layout = QVBoxLayout(frame)
            eff_layout.setContentsMargins(4, 4, 4, 4)
            eff_layout.setSpacing(2)

            # Effect name label
            name_label = QLabel(f"{eff.name}")
            name_label.setStyleSheet(f"font-weight: bold; border: none; color: {COLORS['text_secondary']};")
            eff_layout.addWidget(name_label)

            # Row 1: Magnitude + Duration
            row1 = QHBoxLayout()
            row1.addWidget(QLabel("Mag:"))
            mag_spin = QSpinBox()
            mag_spin.setRange(0, 9999)
            mag_spin.setValue(eff.magnitude)
            mag_spin.valueChanged.connect(lambda v, i=idx: self._on_effect_changed(i))
            row1.addWidget(mag_spin)

            row1.addWidget(QLabel("Dur:"))
            dur_spin = QSpinBox()
            dur_spin.setRange(0, 9999)
            dur_spin.setValue(eff.duration)
            dur_spin.valueChanged.connect(lambda v, i=idx: self._on_effect_changed(i))
            row1.addWidget(dur_spin)
            eff_layout.addLayout(row1)

            # Row 2: Area + Range
            row2 = QHBoxLayout()
            row2.addWidget(QLabel("Area:"))
            area_spin = QSpinBox()
            area_spin.setRange(0, 9999)
            area_spin.setValue(eff.area)
            area_spin.valueChanged.connect(lambda v, i=idx: self._on_effect_changed(i))
            row2.addWidget(area_spin)

            row2.addWidget(QLabel("Range:"))
            range_combo = QComboBox()
            range_combo.addItems(["Self", "Touch", "Target"])
            if eff.range in ("Self", "Touch", "Target"):
                range_combo.setCurrentText(eff.range)
            range_combo.currentTextChanged.connect(lambda v, i=idx: self._on_effect_changed(i))
            row2.addWidget(range_combo)
            eff_layout.addLayout(row2)

            self.effects_layout.addWidget(frame)
            self._effect_widgets.append({
                "mag_spin": mag_spin,
                "dur_spin": dur_spin,
                "area_spin": area_spin,
                "range_combo": range_combo,
            })

    # ── Public show methods ──────────────────────────────────────────────────

    def show_item(self, item, fav_set, exc_set, note_text=""):
        """Show inventory item details."""
        fields = {
            "Type": item.item_type or "Unknown",
            "Quantity": str(item.quantity),
            "Equipped": "Yes" if item.equipped else "No",
        }
        if item.condition_current >= 0:
            fields["Condition"] = f"{item.condition_current:g} / {item.condition_max:g}"
        if item.enchant_current >= 0:
            fields["Charge"] = f"{item.enchant_current:g} / {item.enchant_max:g}"
        self._show_detail(
            title=item.name,
            form_id=item.form_id,
            category="items",
            identifier=item.form_id,
            fields=fields,
            is_fav=item.form_id in fav_set,
            is_exc=item.form_id in exc_set,
            show_bank=True,
            note_text=note_text,
        )

    def show_spell(self, spell, fav_set, exc_set, note_text=""):
        """Show spell details with editable fields for cost and effects."""
        # Use _show_detail for common UI (title, form ID, actions, notes)
        # but with minimal fields since we show editable widgets instead
        fields = {}  # We'll use the spell edit container instead

        self._show_detail(
            title=spell.name,
            form_id=spell.form_id,
            category="spells",
            identifier=spell.form_id,
            fields=fields,
            is_fav=spell.form_id in fav_set,
            is_exc=spell.form_id in exc_set,
            show_bank=True,
            note_text=note_text,
        )

        # Now show the spell edit area
        self._current_spell = spell
        self._spell_updating = True

        self.spell_type_label.setText(f"Type: {spell.spell_type or 'Unknown'}")
        self.spell_cost_spin.setValue(spell.magicka_cost)
        self._build_effect_widgets(spell)

        self.spell_edit_container.show()
        self._spell_updating = False

    def show_attribute(self, name, value, fav_set, exc_set, note_text=""):
        """Show attribute details."""
        fields = {
            "Value": str(value),
        }
        self._show_detail(
            title=name,
            form_id="",
            category="attributes",
            identifier=name,
            fields=fields,
            is_fav=name in fav_set,
            is_exc=name in exc_set,
            show_bank=False,
            note_text=note_text,
        )

    def show_faction(self, faction, fav_set, exc_set, note_text=""):
        """Show faction details."""
        fields = {
            "Rank": str(faction.rank),
        }
        if faction.title:
            fields["Title"] = faction.title
        self._show_detail(
            title=faction.name,
            form_id=faction.form_id,
            category="factions",
            identifier=faction.form_id,
            fields=fields,
            is_fav=faction.form_id in fav_set,
            is_exc=faction.form_id in exc_set,
            show_bank=False,
            note_text=note_text,
        )

    def show_quest(self, quest, fav_set, exc_set, note_text=""):
        """Show quest details."""
        fields = {}
        if hasattr(quest, 'stage'):
            fields["Stage"] = str(quest.stage)
        if hasattr(quest, 'editor_id') and quest.editor_id:
            fields["Editor ID"] = quest.editor_id
        if hasattr(quest, 'flags') and quest.flags:
            fields["Flags"] = quest.flags
        identifier = getattr(quest, 'form_id', '') or getattr(quest, 'editor_id', '')
        self._show_detail(
            title=getattr(quest, 'name', '') or getattr(quest, 'editor_id', ''),
            form_id=getattr(quest, 'form_id', ''),
            category="quests",
            identifier=identifier,
            fields=fields,
            is_fav=identifier in fav_set,
            is_exc=identifier in exc_set,
            show_bank=False,
            note_text=note_text,
        )

    def show_skill(self, name, value, fav_set, exc_set, note_text=""):
        """Show skill details."""
        fields = {
            "Value": str(value),
        }
        self._show_detail(
            title=name,
            form_id="",
            category="skills",
            identifier=name,
            fields=fields,
            is_fav=name in fav_set,
            is_exc=name in exc_set,
            show_bank=False,
            note_text=note_text,
        )
