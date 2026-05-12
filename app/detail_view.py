from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QCheckBox, QScrollArea, QComboBox,
    QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from .theme import (
    BG_ELEVATED, BG_MAIN, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CATEGORY_DISPLAY, CATEGORY_KEYS,
    STAGE_COLORS, STAGE_KEYS, STAGES, ACCENT,
)


# ── Collapsible section widget ────────────────────────────────────────────────

class CollapsibleSection(QWidget):
    def __init__(self, title: str, color: str, expanded: bool = True, parent=None):
        super().__init__(parent)
        self._title    = title
        self._color    = color
        self._expanded = expanded
        self.setStyleSheet("background:transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 0)
        root.setSpacing(0)

        # Toggle header
        self._btn = QPushButton()
        self._btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn.clicked.connect(self._toggle)
        root.addWidget(self._btn)

        # Content area
        self._body = QWidget()
        self._body.setStyleSheet("background:transparent;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(12, 10, 0, 8)
        self._body_lay.setSpacing(14)
        self._body.setVisible(expanded)
        root.addWidget(self._body)

        self._update_btn()

    def _toggle(self):
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        self._update_btn()

    def _update_btn(self):
        arrow = "▾" if self._expanded else "▸"
        self._btn.setText(f"  {arrow}  {self._title}")
        bg = f"{self._color}12" if self._expanded else "transparent"
        self._btn.setStyleSheet(
            f"QPushButton {{"
            f"  background:{bg};"
            f"  border:none;"
            f"  border-left:2px solid {self._color};"
            f"  color:{self._color};"
            f"  font-size:11px; font-weight:700;"
            f"  text-align:left;"
            f"  letter-spacing:0.6px;"
            f"  padding:7px 12px;"
            f"  text-transform:uppercase;"
            f"}}"
            f"QPushButton:hover {{ background:{self._color}1e; }}"
        )

    def add_widget(self, w: QWidget):
        self._body_lay.addWidget(w)

    def add_stretch(self):
        self._body_lay.addStretch()


# ── Main detail view ──────────────────────────────────────────────────────────

class DetailView(QWidget):
    back_requested = pyqtSignal()
    video_deleted  = pyqtSignal()
    video_saved    = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db    = db
        self.video = None
        self._field_widgets = {}
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet(f"background-color:{BG_MAIN};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header bar
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(
            f"background-color:{BG_ELEVATED}; border-bottom:1px solid {BORDER};"
        )
        h = QHBoxLayout(header)
        h.setContentsMargins(20, 0, 20, 0)

        self._back_btn = QPushButton("← Back")
        self._back_btn.setStyleSheet(
            "background:transparent; border:none; color:#777; font-size:13px; padding:0; min-width:60px;"
        )
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self._save_and_back)

        self._breadcrumb = QLabel()
        self._breadcrumb.setStyleSheet("color:#555; font-size:12px; background:transparent;")

        self._del_btn = QPushButton("Delete")
        self._del_btn.setStyleSheet(
            "background:transparent; border:none; color:#ef4444; font-size:13px; padding:0; min-width:50px;"
        )
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.clicked.connect(self._confirm_delete)

        h.addWidget(self._back_btn)
        h.addWidget(self._breadcrumb)
        h.addStretch()
        h.addWidget(self._del_btn)
        root.addWidget(header)

        # Scroll body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:transparent; border:none;")

        body = QWidget()
        body.setStyleSheet(f"background-color:{BG_MAIN};")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(40, 32, 40, 48)
        self._body_layout.setSpacing(0)

        scroll.setWidget(body)
        root.addWidget(scroll)

    # ── Load ─────────────────────────────────────────────────────────────────

    def load(self, video_id: str):
        self.video = self.db.get_video(video_id)
        if not self.video:
            return
        self._field_widgets.clear()
        self._rebuild_body()

    def _rebuild_body(self):
        lay = self._body_layout
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        v         = self.video
        stage_idx = STAGE_KEYS.index(v.stage) if v.stage in STAGE_KEYS else 0
        stage_col = STAGE_COLORS.get(v.stage, ACCENT)

        self._breadcrumb.setText(f"{STAGES[stage_idx]}  ›  {v.title}")

        # ── Title ─────────────────────────────────────────────────────────
        self._title_edit = QLineEdit(v.title)
        self._title_edit.setPlaceholderText("Video title…")
        self._title_edit.setStyleSheet(
            "font-size:22px; font-weight:700; border:none;"
            "border-bottom:1px solid #2a2a2a; border-radius:0;"
            "padding:6px 0; background:transparent;"
        )
        lay.addWidget(self._title_edit)
        lay.addSpacing(14)

        # ── Category + Stage ──────────────────────────────────────────────
        meta = QWidget()
        meta.setStyleSheet("background:transparent;")
        m = QHBoxLayout(meta)
        m.setContentsMargins(0, 0, 0, 0)
        m.setSpacing(20)

        self._cat_combo = self._make_combo(
            [(CATEGORY_DISPLAY[k], k) for k in CATEGORY_KEYS],
            CATEGORY_KEYS.index(v.category) if v.category in CATEGORY_KEYS else 0,
            "Category",
        )
        self._stage_combo = self._make_combo(
            [(STAGES[i], k) for i, k in enumerate(STAGE_KEYS)],
            stage_idx,
            "Stage",
        )

        m.addWidget(self._cat_combo[0])
        m.addWidget(self._stage_combo[0])
        m.addStretch()
        lay.addWidget(meta)
        lay.addSpacing(28)

        # ── Current stage section ─────────────────────────────────────────
        current_fields = self.db.get_fields_for_stage(v.stage)
        current_sec = CollapsibleSection(
            f"{STAGES[stage_idx]}",
            stage_col,
            expanded=True,
        )
        if current_fields:
            for field in current_fields:
                self._add_field_to_section(current_sec, field)
        else:
            empty = QLabel("No fields configured for this stage.\nAdd some in Settings ⚙")
            empty.setStyleSheet(f"color:{TEXT_MUTED}; font-size:13px; background:transparent;")
            current_sec.add_widget(empty)
        lay.addWidget(current_sec)

        # ── Review sections (previous stages, collapsed) ──────────────────
        if stage_idx > 0:
            lay.addSpacing(24)
            review_lbl = QLabel("Review")
            review_lbl.setStyleSheet(
                f"font-size:10px; font-weight:700; color:{TEXT_MUTED}; letter-spacing:1.2px;"
                "text-transform:uppercase; background:transparent;"
            )
            lay.addWidget(review_lbl)
            lay.addSpacing(6)

            # Most recent previous stage first
            for i in range(stage_idx - 1, -1, -1):
                prev_key    = STAGE_KEYS[i]
                prev_color  = STAGE_COLORS.get(prev_key, "#555")
                prev_fields = self.db.get_fields_for_stage(prev_key)
                if not prev_fields:
                    continue
                sec = CollapsibleSection(STAGES[i], prev_color, expanded=False)
                for field in prev_fields:
                    self._add_field_to_section(sec, field)
                lay.addWidget(sec)
                lay.addSpacing(4)

        lay.addStretch()

    def _make_combo(self, items: list, current_idx: int, label_text: str):
        """Returns (wrapper QWidget, QComboBox)."""
        wrap = QWidget()
        wrap.setStyleSheet("background:transparent;")
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(4)

        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{TEXT_MUTED}; "
            "text-transform:uppercase; letter-spacing:0.8px; background:transparent;"
        )
        combo = QComboBox()
        for text, data in items:
            combo.addItem(text, data)
        combo.setCurrentIndex(current_idx)

        wl.addWidget(lbl)
        wl.addWidget(combo)
        return wrap, combo

    def _add_field_to_section(self, section: CollapsibleSection, field):
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        if field.field_type == "checkbox":
            cb = QCheckBox(field.label)
            cb.setChecked(bool(self.video.checklist_values.get(field.id, False)))
            lay.addWidget(cb)
            self._field_widgets[field.id] = cb
        else:
            lbl = QLabel(field.label)
            lbl.setStyleSheet(
                f"font-size:11px; color:{TEXT_SECONDARY}; background:transparent;"
            )
            lay.addWidget(lbl)
            val = str(self.video.checklist_values.get(field.id, ""))
            if field.field_type == "textarea":
                w = QTextEdit()
                w.setPlainText(val)
                w.setPlaceholderText(f"{field.label}…")
                w.setMinimumHeight(78)
                w.setMaximumHeight(160)
            else:
                w = QLineEdit(val)
                w.setPlaceholderText(f"{field.label}…")
            lay.addWidget(w)
            self._field_widgets[field.id] = w

        section.add_widget(container)

    # ── Save / Delete ─────────────────────────────────────────────────────────

    def _collect_values(self):
        if not self.video:
            return
        self.video.title    = self._title_edit.text().strip() or self.video.title
        self.video.category = self._cat_combo[1].currentData()
        self.video.stage    = self._stage_combo[1].currentData()
        for fid, widget in self._field_widgets.items():
            if isinstance(widget, QCheckBox):
                self.video.checklist_values[fid] = widget.isChecked()
            elif isinstance(widget, QTextEdit):
                self.video.checklist_values[fid] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                self.video.checklist_values[fid] = widget.text()

    def _save_and_back(self):
        self._collect_values()
        if self.video:
            self.db.update_video(self.video)
        self.video_saved.emit()
        self.back_requested.emit()

    def _confirm_delete(self):
        if not self.video:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Video")
        msg.setText(f'Delete "{self.video.title}"?')
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.setStyleSheet("QMessageBox { background:#1e1e1e; } QPushButton { min-width:80px; }")
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.delete_video(self.video.id)
            self.video = None
            self.video_deleted.emit()
            self.back_requested.emit()
