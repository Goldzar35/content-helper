from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal

from .card import VideoCard
from .theme import TEXT_SECONDARY, TEXT_MUTED, STAGE_COLORS, STAGE_KEYS


class StagePage(QWidget):
    card_clicked  = pyqtSignal(str)   # video_id
    stage_changed = pyqtSignal()      # any card was flung → refresh

    def __init__(self, stage_key: str, db, parent=None):
        super().__init__(parent)
        self.stage_key = stage_key
        self.db = db

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._grid    = QGridLayout(self._content)
        self._grid.setContentsMargins(28, 28, 28, 28)
        self._grid.setSpacing(16)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._content)
        root.addWidget(scroll)

        self._cols = 3
        self.refresh()

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._clear_grid()
        videos = self.db.get_videos_by_stage(self.stage_key)
        fields = self.db.get_fields()

        if not videos:
            self._show_empty()
            return

        col = 0
        for i, video in enumerate(videos):
            row = i // self._cols
            col = i % self._cols
            card = VideoCard(video, fields, self._content)
            card.clicked.connect(self.card_clicked.emit)
            card.advance_sig.connect(self._on_advance)
            card.retreat_sig.connect(self._on_retreat)
            self._grid.addWidget(card, row, col)

        # Fill remaining columns so grid stays left-aligned
        next_col = col + 1
        if next_col < self._cols:
            spacer = QWidget()
            spacer.setSizePolicy(
                spacer.sizePolicy().horizontalPolicy(),
                spacer.sizePolicy().verticalPolicy(),
            )
            self._grid.addWidget(spacer, len(videos) // self._cols, next_col,
                                 1, self._cols - next_col)

    # ── Private ───────────────────────────────────────────────────────────────

    def _clear_grid(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_empty(self):
        color = STAGE_COLORS.get(self.stage_key, "#555")
        lbl = QLabel(f"No videos here yet.\nClick  +  to add one.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 14px; line-height: 1.6;"
            f"background: transparent;"
        )
        self._grid.addWidget(lbl, 0, 0, 1, self._cols)

    def _on_advance(self, vid: str):
        self.db.advance_stage(vid)
        self.refresh()
        self.stage_changed.emit()

    def _on_retreat(self, vid: str):
        self.db.retreat_stage(vid)
        self.refresh()
        self.stage_changed.emit()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        from .card import CARD_W
        available = event.size().width() - 56  # margins
        new_cols = max(1, available // (CARD_W + 16))
        if new_cols != self._cols:
            self._cols = new_cols
            self.refresh()
