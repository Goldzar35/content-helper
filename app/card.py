import time

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import (
    Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal,
    QAbstractAnimation, QRectF, QParallelAnimationGroup,
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QPainterPath,
    QPixmap, QTransform,
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect

from .theme import (
    BG_CARD, BG_CARD_HOVER, BORDER, TEXT_PRIMARY, TEXT_SECONDARY,
    CATEGORY_COLORS, CATEGORY_DISPLAY, STAGE_COLORS, TEXT_MUTED,
)

CARD_W = 260
CARD_H = 150
FLING_THRESHOLD = 380   # px/s
DRAG_THRESHOLD  = 10    # px


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

        p.setPen(QPen(QColor("#333333"), 3, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)

        if self.progress > 0:
            span = int(-360 * 16 * self.progress)
            p.setPen(QPen(QColor(self.color), 3, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawArc(rect, 90 * 16, span)

        p.setPen(QColor(TEXT_PRIMARY if self.progress < 1.0 else self.color))
        f = QFont("-apple-system", 7)
        f.setBold(True)
        p.setFont(f)
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.progress * 100)}%")


class VideoCard(QFrame):
    clicked      = pyqtSignal(str)
    advance_sig  = pyqtSignal(str)
    retreat_sig  = pyqtSignal(str)

    def __init__(self, video, fields, parent=None):
        super().__init__(parent)
        self.video  = video
        self.fields = fields
        self._ghost          = None
        self._ghost_orig_pos = QPoint()
        self._drag_start     = None
        self._positions      = []
        self._is_dragging    = False
        self._anim_group     = None   # kept alive to prevent GC

        self.setFixedSize(CARD_W, CARD_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build_ui()
        self._apply_style()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)

        cat_key   = self.video.category
        cat_color = CATEGORY_COLORS.get(cat_key, "#888")
        tag = QLabel(CATEGORY_DISPLAY.get(cat_key, cat_key))
        tag.setStyleSheet(
            f"background:{cat_color}22; color:{cat_color}; border:1px solid {cat_color}55;"
            f"border-radius:10px; padding:2px 8px; font-size:11px; font-weight:600;"
        )
        tag.setFixedHeight(20)

        stage_color = STAGE_COLORS.get(self.video.stage, "#888")
        ring = ProgressRing(self.video.progress(self.fields), stage_color)

        top.addWidget(tag)
        top.addStretch()
        top.addWidget(ring)
        layout.addLayout(top)

        layout.addStretch()

        title_lbl = QLabel(self.video.title)
        title_lbl.setWordWrap(True)
        title_lbl.setStyleSheet(
            f"font-size:15px; font-weight:600; color:{TEXT_PRIMARY}; background:transparent;"
        )
        title_lbl.setMaximumHeight(44)
        layout.addWidget(title_lbl)

        hint = QLabel("← swipe to move stage →")
        hint.setStyleSheet(f"font-size:10px; color:{TEXT_MUTED}; background:transparent;")
        layout.addWidget(hint)

    def _apply_style(self):
        cat_color = CATEGORY_COLORS.get(self.video.category, BORDER)
        self.setStyleSheet(
            f"VideoCard {{"
            f"  background-color:{BG_CARD};"
            f"  border:1px solid {BORDER};"
            f"  border-left:3px solid {cat_color};"
            f"  border-radius:10px;"
            f"}}"
            f"VideoCard:hover {{"
            f"  background-color:{BG_CARD_HOVER};"
            f"  border:1px solid #444;"
            f"  border-left:3px solid {cat_color};"
            f"}}"
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
            self._ghost.move(self._ghost_orig_pos.x() + dx, self._ghost_orig_pos.y())
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

        # Grab the card as a pixmap — tilt it slightly for a "picked up" feel
        src = self.grab()
        angle = 4  # degrees
        transform = QTransform().rotate(angle)
        tilted = src.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        ghost = QLabel(self.window())
        ghost.setPixmap(tilted)
        ghost.resize(tilted.size())
        ghost.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        pos = self.mapTo(self.window(), QPoint(0, 0))
        # Offset slightly so tilt looks natural (centered)
        offset_x = (tilted.width() - src.width()) // 2
        offset_y = (tilted.height() - src.height()) // 2
        ghost.move(pos.x() - offset_x, pos.y() - offset_y)
        self._ghost_orig_pos = ghost.pos()
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
        end   = QPoint(win_w + 80, self._ghost.y()) if forward \
                else QPoint(-self.width() - 80, self._ghost.y())

        # Parallel: slide + fade out
        effect = QGraphicsOpacityEffect(self._ghost)
        self._ghost.setGraphicsEffect(effect)

        pos_anim = QPropertyAnimation(self._ghost, b"pos")
        pos_anim.setStartValue(self._ghost.pos())
        pos_anim.setEndValue(end)
        pos_anim.setDuration(380)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutQuart)

        fade_anim = QPropertyAnimation(effect, b"opacity")
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.setDuration(380)
        fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        group = QParallelAnimationGroup()
        group.addAnimation(pos_anim)
        group.addAnimation(fade_anim)
        group.finished.connect(lambda: self._on_fling_done(forward))
        self._anim_group = group   # prevent GC
        group.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

    def _snap_back(self):
        if not self._ghost:
            return
        anim = QPropertyAnimation(self._ghost, b"pos")
        anim.setStartValue(self._ghost.pos())
        anim.setEndValue(self._ghost_orig_pos)
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.OutBack)
        anim.finished.connect(self._cleanup_ghost)
        self._anim_group = anim
        anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

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
