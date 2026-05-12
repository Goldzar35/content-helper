from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QCheckBox, QScrollArea, QComboBox,
    QFrame, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

from .theme import (
    BG_ELEVATED, BG_MAIN, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CATEGORY_DISPLAY, CATEGORY_KEYS,
    STAGE_COLORS, STAGE_KEYS, STAGES, ACCENT, ACCENT_TEXT,
)


# ── Field box ─────────────────────────────────────────────────────────────────

class FieldBox(QFrame):
    """Dark elevated card wrapping a single checklist field."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FieldBox")
        self.setStyleSheet(
            "QFrame#FieldBox {"
            "  background: #1c1c1c;"
            "  border: 1px solid #282828;"
            "  border-radius: 8px;"
            "}"
        )
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(14, 10, 14, 12)
        self._lay.setSpacing(6)

    def add(self, w: QWidget):
        self._lay.addWidget(w)


# ── Collapsible section ───────────────────────────────────────────────────────

class CollapsibleSection(QWidget):
    def __init__(self, title: str, color: str, expanded: bool = True, parent=None):
        super().__init__(parent)
        self._title    = title
        self._color    = color
        self._expanded = expanded
        self.setStyleSheet("background:transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 0)
        root.setSpacing(10)

        # Header row: colored dot + title + expand arrow
        hdr = QWidget()
        hdr.setStyleSheet("background:transparent;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(0, 0, 0, 0)
        hdr_lay.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setStyleSheet(
            f"color:{color}; font-size:8px; background:transparent;"
        )
        self._dot.setFixedWidth(14)

        self._title_lbl = QLabel(title.upper())
        self._title_lbl.setStyleSheet(
            f"color:{color}; font-size:10px; font-weight:700; "
            "letter-spacing:1.2px; background:transparent;"
        )

        # Line separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background:{color}; max-height:1px; border:none;")

        self._toggle_btn = QPushButton("▾" if expanded else "▸")
        self._toggle_btn.setFixedSize(22, 22)
        self._toggle_btn.setStyleSheet(
            f"background:transparent; border:none; color:{color}; font-size:12px;"
        )
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle)

        hdr_lay.addWidget(self._dot)
        hdr_lay.addWidget(self._title_lbl)
        hdr_lay.addWidget(line, stretch=1)
        hdr_lay.addWidget(self._toggle_btn)
        root.addWidget(hdr)

        # Content
        self._body = QWidget()
        self._body.setStyleSheet("background:transparent;")
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(0, 0, 0, 0)
        self._body_lay.setSpacing(8)
        self._body.setVisible(expanded)
        root.addWidget(self._body)

    def _toggle(self):
        self._expanded = not self._expanded
        self._body.setVisible(self._expanded)
        self._toggle_btn.setText("▾" if self._expanded else "▸")

    def add_widget(self, w: QWidget):
        self._body_lay.addWidget(w)


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
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(self._auto_save)
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
            "background:transparent; border:none; color:#666; font-size:13px; padding:0; min-width:60px;"
        )
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self._save_and_back)

        self._breadcrumb = QLabel()
        self._breadcrumb.setStyleSheet("color:#4a4a4a; font-size:12px; background:transparent;")

        self._del_btn = QPushButton("Delete")
        self._del_btn.setStyleSheet(
            "background:transparent; border:none; color:#8a3a3a; font-size:13px; padding:0; min-width:50px;"
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

        is_review    = v.stage == "review"
        is_completed = v.stage == "completed"
        readonly     = is_completed

        # ── Title ─────────────────────────────────────────────────────────
        self._title_edit = QLineEdit(v.title)
        self._title_edit.setPlaceholderText("Video title…")
        self._title_edit.setReadOnly(readonly)
        self._title_edit.setStyleSheet(
            "QLineEdit {"
            "  font-size:22px; font-weight:700; border:none;"
            "  border-style:solid; border-width:0 0 1px 0;"
            "  border-color:transparent transparent #252525 transparent;"
            "  border-radius:0; padding:6px 0; background:transparent;"
            "}"
        )
        if not readonly:
            self._title_edit.textChanged.connect(self._save_timer.start)
        lay.addWidget(self._title_edit)
        lay.addSpacing(16)

        # ── Category + Stage ──────────────────────────────────────────────
        meta = QWidget()
        meta.setStyleSheet("background:transparent;")
        m = QHBoxLayout(meta)
        m.setContentsMargins(0, 0, 0, 0)
        m.setSpacing(20)

        self._cat_combo = self._make_labeled_combo(
            "Category",
            [(CATEGORY_DISPLAY[k], k) for k in CATEGORY_KEYS],
            CATEGORY_KEYS.index(v.category) if v.category in CATEGORY_KEYS else 0,
        )
        if readonly:
            self._cat_combo[1].setEnabled(False)
        else:
            self._cat_combo[1].currentIndexChanged.connect(self._save_timer.start)

        # Stage is read-only — changed via fling only
        stage_wrap = QWidget()
        stage_wrap.setStyleSheet("background:transparent;")
        sw = QVBoxLayout(stage_wrap)
        sw.setContentsMargins(0, 0, 0, 0)
        sw.setSpacing(4)
        stage_cap = QLabel("Stage")
        stage_cap.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{TEXT_MUTED};"
            "text-transform:uppercase; letter-spacing:0.8px; background:transparent;"
        )
        stage_badge = QLabel(STAGES[stage_idx])
        stage_badge.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{stage_col}; background:transparent;"
        )
        sw.addWidget(stage_cap)
        sw.addWidget(stage_badge)

        m.addWidget(self._cat_combo[0])
        m.addWidget(stage_wrap)
        m.addStretch()
        lay.addWidget(meta)
        lay.addSpacing(32)

        # ── Review / Completed: all pipeline stages expanded ──────────────
        if is_review or is_completed:
            pipeline_keys = ["ideas", "planning", "filming", "editing", "posting"]
            pipeline_stages = STAGES[:5]
            for i, key in enumerate(pipeline_keys):
                fields = self.db.get_fields_for_stage(key)
                if not fields:
                    continue
                sec = CollapsibleSection(pipeline_stages[i], STAGE_COLORS.get(key, "#555"), expanded=True)
                for field in fields:
                    self._add_field_to_section(sec, field, readonly=readonly)
                lay.addWidget(sec)
                lay.addSpacing(8)
            lay.addStretch()
            return

        # ── Current stage fields ──────────────────────────────────────────
        current_fields = self.db.get_fields_for_stage(v.stage)
        current_sec = CollapsibleSection(STAGES[stage_idx], stage_col, expanded=True)
        if current_fields:
            for field in current_fields:
                self._add_field_to_section(current_sec, field)
        else:
            empty = QLabel("No fields for this stage — add some in Settings ⚙")
            empty.setStyleSheet(f"color:{TEXT_MUTED}; font-size:13px; background:transparent;")
            current_sec.add_widget(empty)
        lay.addWidget(current_sec)

        # ── Review: previous stages (collapsed) ──────────────────────────
        if stage_idx > 0:
            lay.addSpacing(28)
            review_lbl = QLabel("Review")
            review_lbl.setStyleSheet(
                f"font-size:10px; font-weight:700; color:{TEXT_MUTED};"
                "letter-spacing:1.4px; text-transform:uppercase; background:transparent;"
            )
            lay.addWidget(review_lbl)
            lay.addSpacing(8)

            for i in range(stage_idx - 1, -1, -1):
                prev_key    = STAGE_KEYS[i]
                prev_fields = self.db.get_fields_for_stage(prev_key)
                if not prev_fields:
                    continue
                sec = CollapsibleSection(STAGES[i], STAGE_COLORS.get(prev_key, "#555"), expanded=False)
                for field in prev_fields:
                    self._add_field_to_section(sec, field)
                lay.addWidget(sec)
                lay.addSpacing(4)

        lay.addStretch()

    def _make_labeled_combo(self, label_text: str, items: list, current_idx: int):
        """Returns (wrapper QWidget, QComboBox)."""
        wrap = QWidget()
        wrap.setStyleSheet("background:transparent;")
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            f"font-size:10px; font-weight:600; color:{TEXT_MUTED};"
            "text-transform:uppercase; letter-spacing:0.8px; background:transparent;"
        )
        combo = QComboBox()
        for text, data in items:
            combo.addItem(text, data)
        combo.setCurrentIndex(current_idx)
        wl.addWidget(lbl)
        wl.addWidget(combo)
        return wrap, combo

    def _add_field_to_section(self, section: CollapsibleSection, field, readonly: bool = False):
        box = FieldBox(self)

        if field.field_type == "checkbox":
            cb = QCheckBox(field.label)
            cb.setChecked(bool(self.video.checklist_values.get(field.id, False)))
            cb.setEnabled(not readonly)
            cb.setStyleSheet(
                "QCheckBox { font-size:13px; color:#d0d0d0; background:transparent; }"
            )
            if not readonly:
                cb.stateChanged.connect(self._save_timer.start)
            box.add(cb)
            self._field_widgets[field.id] = cb
        else:
            lbl = QLabel(field.label.upper())
            lbl.setStyleSheet(
                "font-size:9px; font-weight:700; color:#4a4a4a; letter-spacing:1px; background:transparent;"
            )
            box.add(lbl)

            val = str(self.video.checklist_values.get(field.id, ""))
            if field.field_type == "textarea":
                w = QTextEdit()
                w.setPlainText(val)
                w.setPlaceholderText(f"Add {field.label.lower()}…")
                w.setMinimumHeight(72)
                w.setMaximumHeight(150)
                w.setReadOnly(readonly)
                w.setStyleSheet(
                    "QTextEdit { background:transparent; border:none;"
                    "  border-radius:0; padding:2px 0; font-size:13px; color:#e0e0e0; }"
                )
                if not readonly:
                    w.textChanged.connect(self._save_timer.start)
            else:
                w = QLineEdit(val)
                w.setPlaceholderText(f"Add {field.label.lower()}…")
                w.setReadOnly(readonly)
                w.setStyleSheet(
                    "QLineEdit { background:transparent; border:none;"
                    "  border-radius:0; padding:2px 0; font-size:13px; color:#e0e0e0; }"
                )
                if not readonly:
                    w.textChanged.connect(self._save_timer.start)
            box.add(w)
            self._field_widgets[field.id] = w

        section.add_widget(box)

    # ── Save / Delete ─────────────────────────────────────────────────────────

    def _collect_values(self):
        if not self.video or self.video.stage == "completed":
            return
        self.video.title    = self._title_edit.text().strip() or self.video.title
        self.video.category = self._cat_combo[1].currentData()
        for fid, widget in self._field_widgets.items():
            if isinstance(widget, QCheckBox):
                self.video.checklist_values[fid] = widget.isChecked()
            elif isinstance(widget, QTextEdit):
                self.video.checklist_values[fid] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                self.video.checklist_values[fid] = widget.text()

    def _auto_save(self):
        self._collect_values()
        if self.video:
            self.db.update_video(self.video)

    def _save_and_back(self):
        self._save_timer.stop()
        self._auto_save()
        self.video_saved.emit()
        self.back_requested.emit()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self._save_and_back()
        else:
            super().keyPressEvent(e)

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
