from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QCheckBox, QScrollArea, QComboBox,
    QFrame, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from .theme import (
    BG_ELEVATED, BG_MAIN, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    CATEGORY_COLORS, CATEGORY_DISPLAY, CATEGORY_KEYS, STAGE_COLORS,
    STAGE_KEYS, STAGES, ACCENT,
)


class DetailView(QWidget):
    back_requested  = pyqtSignal()
    video_deleted   = pyqtSignal()
    video_saved     = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.video = None
        self._field_widgets = {}   # field_id -> widget
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background-color: {BG_MAIN};")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border-bottom: 1px solid {BORDER};"
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        self._back_btn = QPushButton("← Back")
        self._back_btn.setStyleSheet(
            "background:transparent; border:none; color:#888; font-size:13px;"
            "padding:0; min-width:60px;"
        )
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self._save_and_back)

        self._breadcrumb = QLabel()
        self._breadcrumb.setStyleSheet(
            "color:#666; font-size:12px; background:transparent;"
        )

        self._del_btn = QPushButton("Delete")
        self._del_btn.setStyleSheet(
            "background:transparent; border:none; color:#ef4444; font-size:13px;"
            "padding:0; min-width:50px;"
        )
        self._del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._del_btn.clicked.connect(self._confirm_delete)

        h_lay.addWidget(self._back_btn)
        h_lay.addWidget(self._breadcrumb)
        h_lay.addStretch()
        h_lay.addWidget(self._del_btn)
        root.addWidget(header)

        # ── Scroll body ───────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")

        body = QWidget()
        body.setStyleSheet(f"background-color: {BG_MAIN};")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(40, 32, 40, 40)
        self._body_layout.setSpacing(20)

        scroll.setWidget(body)
        root.addWidget(scroll)

    # ── Load video ────────────────────────────────────────────────────────────

    def load(self, video_id: str):
        self.video = self.db.get_video(video_id)
        if not self.video:
            return
        self._field_widgets.clear()
        self._rebuild_body()

    def _rebuild_body(self):
        # Clear existing body widgets
        layout = self._body_layout
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        v = self.video
        stage_label = STAGES[STAGE_KEYS.index(v.stage)] if v.stage in STAGE_KEYS else v.stage
        self._breadcrumb.setText(f"{stage_label}  ›  {v.title}")

        # Title
        self._add_section_label("Title")
        title_edit = QLineEdit(v.title)
        title_edit.setPlaceholderText("Video title…")
        title_edit.setStyleSheet(
            "font-size:20px; font-weight:600; border:none; border-bottom:1px solid #333;"
            "border-radius:0; padding:6px 0; background:transparent;"
        )
        self._title_edit = title_edit
        self._body_layout.addWidget(title_edit)

        # Category + Stage row
        meta_row = QHBoxLayout()
        meta_row.setSpacing(16)

        self._add_section_label("Category")
        cat_combo = QComboBox()
        for key in CATEGORY_KEYS:
            cat_combo.addItem(CATEGORY_DISPLAY[key], key)
        idx = CATEGORY_KEYS.index(v.category) if v.category in CATEGORY_KEYS else 0
        cat_combo.setCurrentIndex(idx)
        self._cat_combo = cat_combo

        stage_label_w = QLabel("Stage")
        stage_label_w.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{TEXT_SECONDARY}; text-transform:uppercase;"
            "letter-spacing:0.8px; background:transparent;"
        )
        stage_combo = QComboBox()
        for i, key in enumerate(STAGE_KEYS):
            stage_combo.addItem(STAGES[i], key)
        sidx = STAGE_KEYS.index(v.stage) if v.stage in STAGE_KEYS else 0
        stage_combo.setCurrentIndex(sidx)
        self._stage_combo = stage_combo

        meta = QWidget()
        meta.setStyleSheet("background:transparent;")
        m_lay = QHBoxLayout(meta)
        m_lay.setContentsMargins(0, 0, 0, 0)
        m_lay.setSpacing(24)

        c_wrap = QVBoxLayout()
        c_wrap.setSpacing(4)
        c_lbl = QLabel("Category")
        c_lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{TEXT_SECONDARY}; text-transform:uppercase; background:transparent;"
        )
        c_wrap.addWidget(c_lbl)
        c_wrap.addWidget(cat_combo)

        s_wrap = QVBoxLayout()
        s_wrap.setSpacing(4)
        s_lbl = QLabel("Stage")
        s_lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{TEXT_SECONDARY}; text-transform:uppercase; background:transparent;"
        )
        s_wrap.addWidget(s_lbl)
        s_wrap.addWidget(stage_combo)

        m_lay.addLayout(c_wrap)
        m_lay.addLayout(s_wrap)
        m_lay.addStretch()
        self._body_layout.addWidget(meta)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"color: {BORDER}; background:{BORDER}; max-height:1px;")
        self._body_layout.addWidget(div)

        # Checklist fields
        fields = self.db.get_fields()
        for field in fields:
            self._add_field_widget(field)

        self._body_layout.addStretch()

    def _add_section_label(self, text: str):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{TEXT_SECONDARY}; "
            "text-transform:uppercase; letter-spacing:0.8px; background:transparent;"
        )
        self._body_layout.addWidget(lbl)

    def _add_field_widget(self, field):
        container = QWidget()
        container.setStyleSheet("background:transparent;")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        if field.field_type == "checkbox":
            cb = QCheckBox(field.label)
            cb.setChecked(bool(self.video.checklist_values.get(field.id, False)))
            lay.addWidget(cb)
            self._field_widgets[field.id] = cb
        else:
            lbl = QLabel(field.label)
            lbl.setStyleSheet(
                f"font-size:12px; color:{TEXT_SECONDARY}; background:transparent;"
            )
            lay.addWidget(lbl)

            val = str(self.video.checklist_values.get(field.id, ""))
            if field.field_type == "textarea":
                widget = QTextEdit()
                widget.setPlainText(val)
                widget.setPlaceholderText(f"{field.label}…")
                widget.setMinimumHeight(90)
                widget.setMaximumHeight(180)
            else:
                widget = QLineEdit(val)
                widget.setPlaceholderText(f"{field.label}…")

            lay.addWidget(widget)
            self._field_widgets[field.id] = widget

        self._body_layout.addWidget(container)

    # ── Save / Delete ─────────────────────────────────────────────────────────

    def _collect_values(self):
        if not self.video:
            return
        self.video.title    = self._title_edit.text().strip() or self.video.title
        self.video.category = self._cat_combo.currentData()
        self.video.stage    = self._stage_combo.currentData()

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
        msg.setText(f'Delete "{self.video.title}"? This cannot be undone.')
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        msg.setStyleSheet(
            "QMessageBox { background:#1e1e1e; color:#f0f0f0; }"
            "QPushButton { min-width:80px; }"
        )
        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.db.delete_video(self.video.id)
            self.video = None
            self.video_deleted.emit()
            self.back_requested.emit()
