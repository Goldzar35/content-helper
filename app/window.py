from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QAbstractAnimation
from PyQt6.QtGui import QFont

from .database import Database
from .stage_page import StagePage
from .detail_view import DetailView
from .new_video_dialog import NewVideoDialog
from .settings_dialog import SettingsDialog
from .theme import (
    BG_MAIN, BG_ELEVATED, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, ACCENT, STAGE_COLORS, STAGE_KEYS, STAGES, GLOBAL_QSS,
)

# Stacked widget indexes
_STAGE_OFFSET = 0   # 0..4 are the five stage pages
_DETAIL_IDX   = 5


class TabButton(QPushButton):
    def __init__(self, label: str, color: str, parent=None):
        super().__init__(label, parent)
        self.color = color
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply(False)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self._apply(checked)

    def _apply(self, active: bool):
        border_color = self.color if active else "transparent"
        text_color   = TEXT_PRIMARY if active else TEXT_SECONDARY
        weight       = "600" if active else "500"
        self.setStyleSheet(
            f"QPushButton {{"
            f"  background:transparent;"
            f"  border-style:solid;"
            f"  border-width:0 0 2px 0;"
            f"  border-color:transparent transparent {border_color} transparent;"
            f"  color:{text_color};"
            f"  font-size:13px; font-weight:{weight};"
            f"  padding:0px 18px;"
            f"  height:48px; min-width:90px;"
            f"}}"
            f"QPushButton:hover {{ color:{TEXT_PRIMARY}; }}"
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Content Helper")
        self.setMinimumSize(900, 640)
        self.resize(1200, 760)

        central = QWidget()
        central.setStyleSheet(f"background-color: {BG_MAIN};")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_topbar())
        root.addWidget(self._build_stack())

        self.setStyleSheet(GLOBAL_QSS)
        self._switch_stage(0)

    # ── Top bar ───────────────────────────────────────────────────────────────

    def _build_topbar(self):
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border-bottom: 1px solid {BORDER};"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(0)

        # App name
        app_name = QLabel("Content Helper")
        app_name.setStyleSheet(
            f"font-size:14px; font-weight:700; color:{TEXT_PRIMARY}; "
            "background:transparent; padding-right:24px;"
        )
        lay.addWidget(app_name)

        # Stage tabs
        self._tab_buttons: list[TabButton] = []
        for i, (key, label) in enumerate(zip(STAGE_KEYS, STAGES)):
            color = STAGE_COLORS[key]
            btn = TabButton(label, color)
            btn.clicked.connect(lambda _, idx=i: self._switch_stage(idx))
            self._tab_buttons.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        # Settings
        settings_btn = QPushButton("⚙")
        settings_btn.setStyleSheet(
            f"background:transparent; border:none; color:{TEXT_SECONDARY}; "
            "font-size:18px; padding:0 8px;"
        )
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.clicked.connect(self._open_settings)
        lay.addWidget(settings_btn)

        # New video
        new_btn = QPushButton("  +  New Video")
        new_btn.setStyleSheet(
            f"background:{ACCENT}; color:#fff; border:none; border-radius:7px; "
            "font-size:13px; font-weight:600; padding:7px 16px; margin-left:8px;"
        )
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self._new_video)
        lay.addWidget(new_btn)

        return bar

    # ── Stack ─────────────────────────────────────────────────────────────────

    def _build_stack(self):
        self._stack = QStackedWidget()
        self._stage_pages: list[StagePage] = []

        for key in STAGE_KEYS:
            page = StagePage(key, self.db)
            page.card_clicked.connect(self._open_detail)
            page.stage_changed.connect(self._on_stage_changed)
            self._stage_pages.append(page)
            self._stack.addWidget(page)

        self._detail = DetailView(self.db)
        self._detail.back_requested.connect(self._close_detail)
        self._detail.video_saved.connect(self._refresh_all)
        self._detail.video_deleted.connect(self._refresh_all)
        self._stack.addWidget(self._detail)   # index 5

        return self._stack

    # ── Navigation ────────────────────────────────────────────────────────────

    def _switch_stage(self, idx: int):
        self._current_stage_idx = idx
        for i, btn in enumerate(self._tab_buttons):
            btn.setChecked(i == idx)
        self._fade_to(idx)

    def _fade_to(self, idx: int):
        old = self._stack.currentWidget()
        self._stack.setCurrentIndex(idx)
        new = self._stack.currentWidget()

        if old is new:
            return

        # Quick opacity fade on incoming widget
        effect = QGraphicsOpacityEffect(new)
        new.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(160)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda: new.setGraphicsEffect(None))
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _open_detail(self, video_id: str):
        self._detail.load(video_id)
        self._fade_to(_DETAIL_IDX)

    def _close_detail(self):
        idx = getattr(self, "_current_stage_idx", 0)
        self._stage_pages[idx].refresh()
        self._switch_stage(idx)

    # ── Signals ───────────────────────────────────────────────────────────────

    def _on_stage_changed(self):
        self._refresh_all()

    def _refresh_all(self):
        for page in self._stage_pages:
            page.refresh()
        self._update_tab_counts()

    def _update_tab_counts(self):
        for i, (key, label) in enumerate(zip(STAGE_KEYS, STAGES)):
            videos = self.db.get_videos_by_stage(key)
            count  = len(videos)
            text   = f"{label}  {count}" if count else label
            self._tab_buttons[i].setText(text)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _new_video(self):
        dlg = NewVideoDialog(self)
        if dlg.exec():
            title, category = dlg.get_values()
            video = self.db.create_video(title, category)
            self._refresh_all()
            # Switch to Ideas and open the new video immediately
            self._switch_stage(0)
            self._stage_pages[0].refresh()
            self._open_detail(video.id)

    def _open_settings(self):
        dlg = SettingsDialog(self.db, self)
        dlg.exec()
        self._refresh_all()

    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)
