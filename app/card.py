import time

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import (
    Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal,
    QAbstractAnimation, QRectF,
)
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics, QPainterPath

from .theme import (
    BG_CARD, BG_CARD_HOVER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    CATEGORY_COLORS, CATEGORY_DISPLAY, STAGE_COLORS, TEXT_MUTED,
)

CARD_W = 260
CARD_H = 150
FLING_THRESHOLD = 380   # px/s
DRAG_THRESHOLD  = 10    # px before drag mode activates


class ProgressRing(QWidget):
    def __init__(self, progress: float = 0.0, color: str = "#0d99ff", parent=None):
        super().__init__(parent)
        self.progress = progress
        self.color = color
        self.setFixedSize(38, 38)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(4, 4, 30, 30)

        # Track
        p.setPen(QPen(QColor("#333333"), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)

        # Arc
        if self.progress > 0:
            span = int(-360 * 16 * self.progress)
            p.setPen(QPen(QColor(self.color), 3, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawArc(rect, 90 * 16, span)

        # Percent label
        p.setPen(QColor(TEXT_PRIMARY if self.progress < 1.0 else self.color))
        f = QFont("Inter, -apple-system", 7)
        f.setBold(True)
        p.setFont(f)
        pct = f"{int(self.progress * 100)}%"
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, pct)


class VideoCard(QFrame):
    clicked      = pyqtSignal(str)   # video_id
    advance_sig  = pyqtSignal(str)   # video_id — move to next stage
    retreat_sig  = pyqtSignal(str)   # video_id — move to previous stage

    def __init__(self, video, fields, parent=None):
        super().__init__(parent)
        self.video  = video
        self.fields = fields
        self._ghost = None
        self._ghost_orig_pos = QPoint()
        self._drag_start     = None
        self._positions      = []    # [(time, global_x)]
        self._is_dragging    = False
        self._anim           = None

        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()
        self._apply_style()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Top row: category tag + progress ring
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        cat_key = self.video.category
        cat_color = CATEGORY_COLORS.get(cat_key, "#888")
        tag = QLabel(CATEGORY_DISPLAY.get(cat_key, cat_key))
        tag.setStyleSheet(
            f"background:{cat_color}22; color:{cat_color}; border:1px solid {cat_color}55;"
            f"border-radius:10px; padding:2px 8px; font-size:11px; font-weight:600;"
        )
        tag.setFixedHeight(20)

        progress = self.video.progress(self.fields)
        stage_color = STAGE_COLORS.get(self.video.stage, "#888")
        ring = ProgressRing(progress, stage_color)

        top.addWidget(tag)
        top.addStretch()
        top.addWidget(ring)
        layout.addLayout(top)

        layout.addStretch()

        # Title
        title_lbl = QLabel(self.video.title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"font-size:15px; font-weight:600; color:{TEXT_PRIMARY}; background:transparent;"
        )
        title_lbl.setMaximumHeight(42)
        layout.addWidget(title_lbl)

        # Bottom row: stage hint
        hint = QLabel("swipe → next stage  ·  ← prev")
        hint.setStyleSheet(f"font-size:10px; color:{TEXT_MUTED}; background:transparent;")
        layout.addWidget(hint)

    def _apply_style(self):
        cat_color = CATEGORY_COLORS.get(self.video.category, BORDER)
        self.setStyleSheet(
            f"""
            VideoCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-left: 3px solid {cat_color};
                border-radius: 10px;
            }}
            VideoCard:hover {{
                background-color: {BG_CARD_HOVER};
                border: 1px solid #444;
                border-left: 3px solid {cat_color};
            }}
            """
        )

    # ── Mouse / Fling ─────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start  = e.pos()
            self._is_dragging = False
            self._positions   = [(time.time(), e.globalPosition().x())]

    def mouseMoveEvent(self, e):
        if self._drag_start is None:
            return
        dx = e.pos().x() - self._drag_start.x()

        if not self._is_dragging:
            if abs(dx) > DRAG_THRESHOLD:
                self._is_dragging = True
                self._spawn_ghost()
            else:
                return

        if self._ghost:
            gx = self._ghost_orig_pos.x() + dx
            self._ghost.move(gx, self._ghost_orig_pos.y())
            self._positions.append((time.time(), e.globalPosition().x()))
            if len(self._positions) > 8:
                self._positions.pop(0)

    def mouseReleaseEvent(self, e):
        if self._drag_start is None:
            return

        if not self._is_dragging:
            self._drag_start = None
            self.clicked.emit(self.video.id)
            return

        velocity = self._velocity()

        if velocity > FLING_THRESHOLD:
            self._fling(forward=True)
        elif velocity < -FLING_THRESHOLD:
            self._fling(forward=False)
        else:
            self._snap_back()

        self._drag_start  = None
        self._is_dragging = False

    # ── Ghost helpers ─────────────────────────────────────────────────────────

    def _spawn_ghost(self):
        if self._ghost:
            self._ghost.deleteLater()

        pixmap = self.grab()
        ghost  = QLabel(self.window())
        ghost.setPixmap(pixmap)
        ghost.resize(self.size())
        ghost.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # Map card top-left to window coordinates
        pos = self.mapTo(self.window(), QPoint(0, 0))
        ghost.move(pos)
        self._ghost_orig_pos = pos
        ghost.show()
        ghost.raise_()
        self._ghost = ghost

    def _velocity(self) -> float:
        if len(self._positions) < 2:
            return 0.0
        recent = self._positions[-min(4, len(self._positions)):]
        t1, x1 = recent[0]
        t2, x2 = recent[-1]
        dt = t2 - t1
        return (x2 - x1) / dt if dt > 0.001 else 0.0

    def _fling(self, forward: bool):
        if not self._ghost:
            return
        win_w = self.window().width()
        if forward:
            end = QPoint(win_w + 60, self._ghost.y())
        else:
            end = QPoint(-self.width() - 60, self._ghost.y())

        self._anim = QPropertyAnimation(self._ghost, b"pos")
        self._anim.setStartValue(self._ghost.pos())
        self._anim.setEndValue(end)
        self._anim.setDuration(320)
        self._anim.setEasingCurve(QEasingCurve.Type.OutQuart)
        self._anim.finished.connect(lambda: self._on_fling_done(forward))
        self._anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

    def _snap_back(self):
        if not self._ghost:
            return
        self._anim = QPropertyAnimation(self._ghost, b"pos")
        self._anim.setStartValue(self._ghost.pos())
        self._anim.setEndValue(self._ghost_orig_pos)
        self._anim.setDuration(280)
        self._anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self._anim.finished.connect(self._cleanup_ghost)
        self._anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

    def _on_fling_done(self, forward: bool):
        self._cleanup_ghost()
        if forward:
            self.advance_sig.emit(self.video.id)
        else:
            self.retreat_sig.emit(self.video.id)

    def _cleanup_ghost(self):
        if self._ghost:
            self._ghost.deleteLater()
            self._ghost = None
