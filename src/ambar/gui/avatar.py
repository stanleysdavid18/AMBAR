"""Avatar facial animado adaptado al sistema de estados existente."""

from math import sin
from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget
from ambar.core.state import SystemState


class ExpressionAdapter:
    _MAP = {
        SystemState.OFFLINE: "offline", SystemState.STARTING: "awake",
        SystemState.READY: "neutral", SystemState.SLEEPING: "sleeping",
        SystemState.LISTENING: "listening", SystemState.THINKING: "thinking",
        SystemState.SPEAKING: "speaking", SystemState.ERROR: "concerned",
    }

    @classmethod
    def expression_for(cls, state: SystemState) -> str:
        return cls._MAP.get(state, "neutral")


class AvatarWidget(QWidget):
    """Rostro 2D con ojos, pupilas, cejas, boca, parpadeo e idle motion."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expression, self._phase = "sleeping", 0
        self.setMinimumSize(210, 205)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._timer = QTimer(self)
        self._timer.setInterval(45)
        self._timer.timeout.connect(self._advance)
        self._timer.start()

    @property
    def expression(self): return self._expression

    def set_system_state(self, state): self.set_expression(ExpressionAdapter.expression_for(state))
    def set_expression(self, expression):
        self._expression = expression
        self.update()
    def _advance(self):
        self._phase = (self._phase + 1) % 480
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) * .82
        center = QPointF(self.width() / 2, self.height() / 2)
        breath = 1 + sin(self._phase / 26) * .012
        if self._expression in {"listening", "speaking"}: breath += sin(self._phase / 5) * .018
        radius = side * breath / 2
        glow = QLinearGradient(center.x() - radius, center.y() - radius, center.x() + radius, center.y() + radius)
        glow.setColorAt(0, QColor(206, 176, 255, 95)); glow.setColorAt(1, QColor(80, 52, 152, 15))
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(glow)
        painter.drawEllipse(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2))

        head_radius = radius * .60
        bob = sin(self._phase / 31) * head_radius * .025 if self._expression != "sleeping" else 0
        face_center = QPointF(center.x(), center.y() + bob)
        head = QRectF(face_center.x() - head_radius, face_center.y() - head_radius * .92, head_radius * 2, head_radius * 1.74)
        skin = QLinearGradient(head.topLeft(), head.bottomRight())
        skin.setColorAt(0, QColor("#f7c5be")); skin.setColorAt(1, QColor("#d990a0"))
        painter.setPen(QPen(QColor("#eeb9c1"), 2)); painter.setBrush(skin)
        painter.drawRoundedRect(head, head_radius * .70, head_radius * .70)
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor("#39254c"))
        hair = QRectF(head.left() + head_radius * .10, head.top() - head_radius * .08, head.width() - head_radius * .20, head_radius * .53)
        painter.drawRoundedRect(hair, head_radius * .42, head_radius * .42)

        blink = self._expression == "sleeping" or self._phase % 108 in {0, 1, 2, 3}
        eye_y, eye_dx, pupil_dx = face_center.y() - head_radius * .05, head_radius * .37, 0
        if self._expression == "thinking": pupil_dx = head_radius * .055
        elif self._expression == "listening": pupil_dx = sin(self._phase / 9) * head_radius * .035
        elif self._expression == "concerned": pupil_dx = -head_radius * .035
        eye_h = head_radius * (.035 if blink else .20)
        for direction in (-1, 1):
            eye = QRectF(face_center.x() + direction * eye_dx - head_radius * .16, eye_y - eye_h / 2, head_radius * .32, eye_h)
            painter.setBrush(QColor("#fbf4e9")); painter.drawEllipse(eye)
            if not blink:
                pupil = QRectF(eye.center().x() - head_radius * .065 + pupil_dx, eye.center().y() - head_radius * .065, head_radius * .13, head_radius * .13)
                painter.setBrush(QColor("#39254c")); painter.drawEllipse(pupil)

        brow_y = eye_y - head_radius * .25
        brow_tilt = {"thinking": -12, "listening": 5, "concerned": -20}.get(self._expression, 0)
        painter.setPen(QPen(QColor("#663e66"), max(2, head_radius * .045), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for direction in (-1, 1):
            painter.drawLine(QPointF(face_center.x() + direction * head_radius * .19, brow_y + direction * brow_tilt * .06), QPointF(face_center.x() + direction * head_radius * .49, brow_y - direction * brow_tilt * .06))

        mouth_y = face_center.y() + head_radius * .42
        painter.setPen(QPen(QColor("#853d5d"), max(2, head_radius * .047), Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        if self._expression == "speaking":
            opening = head_radius * (.15 + (self._phase % 8) / 45)
            painter.setBrush(QColor("#713654")); painter.drawEllipse(QRectF(face_center.x() - head_radius * .18, mouth_y - opening / 2, head_radius * .36, opening))
        elif self._expression in {"thinking", "concerned", "offline"}:
            painter.drawLine(QPointF(face_center.x() - head_radius * .17, mouth_y), QPointF(face_center.x() + head_radius * .17, mouth_y + (head_radius * .07 if self._expression == "concerned" else 0)))
        elif self._expression == "sleeping":
            painter.drawLine(QPointF(face_center.x() - head_radius * .11, mouth_y), QPointF(face_center.x() + head_radius * .11, mouth_y))
        else:
            path = QPainterPath(QPointF(face_center.x() - head_radius * .20, mouth_y - head_radius * .04))
            path.quadTo(QPointF(face_center.x(), mouth_y + head_radius * .16), QPointF(face_center.x() + head_radius * .20, mouth_y - head_radius * .04)); painter.drawPath(path)

        if self._expression == "listening":
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor("#7ff0d1"), 2))
            for scale in (.92, 1.06):
                ring = QRectF(center.x() - radius * scale, center.y() - radius * scale, radius * scale * 2, radius * scale * 2)
                painter.drawArc(ring, 218 * 16, 104 * 16)
