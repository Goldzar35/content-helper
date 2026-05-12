from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QGridLayout, QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal

from .card import VideoCard, CARD_W
from .theme import TEXT_MUTED, STAGE_COLORS


class StagePage(QWidget):
    card_clicked      = pyqtSignal(str)   # video_id — open detail
    advance_requested = pyqtSignal(str)   # video_id — move to next stage
    retreat_requested = pyqtSignal(str)   # video_id — move to prev stage

    def __init__(self, stage_key: str, db, parent=None):
        super().__init__(parent)
        self.stage_key = stage_key
        self.db = db
        self._cols = 3

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background:transparent; border:none;")

        self._content = QWidget()
        self._content.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._content)
        self._grid.setContentsMargins(28, 28, 28, 28)
        self._grid.setSpacing(16)
        self._grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        scroll.setWidget(self._content)
        root.addWidget(scroll)

        self.refresh()

    # ── Public ────────────────────────────────────────────────────────────────

    def refresh(self):
        self._clear_grid()
        videos = self.db.get_videos_by_stage(self.stage_key)
        fields = self.db.get_fields_for_stage(self.stage_key)

        if not videos:
            self._show_empty()
            return

        for i, video in enumerate(videos):
            row = i // self._cols
            col = i % self._cols
            card = VideoCard(video, fields, self._content)
            card.clicked.connect(self.card_clicked.emit)
            card.advance_sig.connect(self.advance_requested.emit)
            card.retreat_sig.connect(self.retreat_requested.emit)
            self._grid.addWidget(card, row, col)

    # ── Private ───────────────────────────────────────────────────────────────

    def _clear_grid(self):
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)   # immediate removal from widget tree
                w.deleteLater()

    def _show_empty(self):
        lbl = QLabel("No videos here yet.\nClick  +  to add one.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color:{TEXT_MUTED}; font-size:14px; background:transparent;"
        )
        self._grid.addWidget(lbl, 0, 0, 1, self._cols)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        available = event.size().width() - 56
        new_cols  = max(1, available // (CARD_W + 16))
        if new_cols != self._cols:
            self._cols = new_cols
            self.refresh()
