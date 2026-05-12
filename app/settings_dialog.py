import uuid

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QLineEdit, QComboBox, QCheckBox, QFrame,
)
from PyQt6.QtCore import Qt

from .theme import (
    BG_ELEVATED, BG_MAIN, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, ACCENT, ACCENT_TEXT,
)
from .models import ChecklistField


class FieldRow(QWidget):
    def __init__(self, field: ChecklistField, on_delete, parent=None):
        super().__init__(parent)
        self.field = field
        self.setStyleSheet("background:transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        self._label = QLineEdit(field.label)
        self._label.setFixedHeight(30)
        lay.addWidget(self._label, stretch=3)

        self._type = QComboBox()
        for t in ("text", "textarea", "checkbox"):
            self._type.addItem(t)
        self._type.setCurrentText(field.field_type)
        self._type.setFixedHeight(30)
        self._type.setFixedWidth(90)
        lay.addWidget(self._type)

        from .theme import STAGE_KEYS, STAGES
        _pipeline = STAGE_KEYS[:5]
        _pipeline_names = STAGES[:5]
        self._stage = QComboBox()
        for key, name in zip(_pipeline, _pipeline_names):
            self._stage.addItem(name, key)
        if field.stage and field.stage in _pipeline:
            self._stage.setCurrentIndex(_pipeline.index(field.stage))
        else:
            self._stage.setCurrentIndex(0)
        self._stage.setFixedHeight(30)
        self._stage.setFixedWidth(90)
        lay.addWidget(self._stage)

        self._active = QCheckBox()
        self._active.setChecked(field.active)
        self._active.setToolTip("Active")
        lay.addWidget(self._active)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setStyleSheet(
            "background:transparent; border:none; color:#555; font-size:13px;"
        )
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: on_delete(self))
        lay.addWidget(del_btn)

    def to_field(self, order: int) -> ChecklistField:
        return ChecklistField(
            id=self.field.id,
            label=self._label.text().strip() or self.field.label,
            field_type=self._type.currentText(),
            required=self.field.required,
            order=order,
            active=self._active.isChecked(),
            stage=self._stage.currentData(),
        )


class SettingsDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Settings — Checklist Fields")
        self.setMinimumSize(560, 520)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{BG_MAIN}; }}")
        self._rows: list[FieldRow] = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        hdr = QLabel("Checklist Fields")
        hdr.setStyleSheet(
            f"font-size:18px; font-weight:700; color:{TEXT_PRIMARY}; background:transparent;"
        )
        root.addWidget(hdr)

        sub = QLabel("These fields appear on every video's detail page. Toggle active/inactive to show or hide them.")
        sub.setWordWrap(True)
        sub.setStyleSheet(f"font-size:12px; color:{TEXT_SECONDARY}; background:transparent;")
        root.addWidget(sub)

        # Column headers
        hdr_row = QHBoxLayout()
        for text, stretch in [("Label", 3), ("Type", 0), ("", 0), ("", 0)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                f"font-size:10px; font-weight:600; color:{TEXT_MUTED}; text-transform:uppercase; background:transparent;"
            )
            if stretch:
                hdr_row.addWidget(lbl, stretch=stretch)
            else:
                hdr_row.addWidget(lbl)
        root.addLayout(hdr_row)

        # Scroll area for field rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent; border:none;")

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet(f"background:transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        root.addWidget(scroll, stretch=1)

        # Add field row
        add_row = QHBoxLayout()
        self._new_label = QLineEdit()
        self._new_label.setPlaceholderText("New field label…")
        self._new_label.setFixedHeight(30)

        self._new_type = QComboBox()
        for t in ("text", "textarea", "checkbox"):
            self._new_type.addItem(t)
        self._new_type.setFixedHeight(30)
        self._new_type.setFixedWidth(90)

        from .theme import STAGE_KEYS, STAGES
        self._new_stage = QComboBox()
        for key, name in zip(STAGE_KEYS[:5], STAGES[:5]):
            self._new_stage.addItem(name, key)
        self._new_stage.setFixedHeight(30)
        self._new_stage.setFixedWidth(90)

        add_btn = QPushButton("+ Add Field")
        add_btn.setStyleSheet(
            f"background:{ACCENT}22; color:{ACCENT}; border:1px solid {ACCENT}44; "
            "border-radius:6px; padding:5px 14px;"
        )
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_field)

        add_row.addWidget(self._new_label, stretch=1)
        add_row.addWidget(self._new_type)
        add_row.addWidget(self._new_stage)
        add_row.addWidget(add_btn)
        root.addLayout(add_row)

        # Save / Cancel
        btn_row = QHBoxLayout()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)

        save = QPushButton("Save Changes")
        save.setStyleSheet(
            f"background:{ACCENT}; color:{ACCENT_TEXT}; border:none; border-radius:6px;"
            "padding:8px 20px; font-weight:700;"
        )
        save.setCursor(Qt.CursorShape.PointingHandCursor)
        save.clicked.connect(self._save)

        btn_row.addStretch()
        btn_row.addWidget(cancel)
        btn_row.addWidget(save)
        root.addLayout(btn_row)

    def _load(self):
        for field in self.db.get_all_fields():
            self._append_row(field)

    def _append_row(self, field: ChecklistField):
        row = FieldRow(field, self._delete_row, self._list_widget)
        self._rows.append(row)
        # Insert before the stretch (last item)
        count = self._list_layout.count()
        self._list_layout.insertWidget(count - 1, row)

    def _delete_row(self, row: FieldRow):
        self._rows.remove(row)
        self._list_layout.removeWidget(row)
        row.deleteLater()

    def _add_field(self):
        label = self._new_label.text().strip()
        if not label:
            return
        field = ChecklistField(
            id=str(uuid.uuid4())[:8],
            label=label,
            field_type=self._new_type.currentText(),
            required=False,
            order=len(self._rows),
            active=True,
            stage=self._new_stage.currentData(),
        )
        self._append_row(field)
        self._new_label.clear()

    def _save(self):
        fields = [row.to_field(i) for i, row in enumerate(self._rows)]
        self.db.save_fields(fields)
        self.accept()
