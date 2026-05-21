import math
from ctypes import c_void_p

import AppKit
import objc
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QPixmap

from ui.audio_visualizer import AudioVisualizer
from config import (
    PILL_WIDTH_IDLE, PILL_WIDTH_RECORDING, PILL_WIDTH_STATUS,
    PILL_HEIGHT, PILL_OPACITY, PILL_CORNER_RADIUS, LOGO_SIZE, LOGO_PATH,
)


class PillWidget(QWidget):
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PROCESSING = "processing"
    STATE_DONE = "done"
    STATE_ERROR = "error"

    def __init__(self):
        super().__init__()
        self._state = self.STATE_IDLE
        self._target_w = float(PILL_WIDTH_IDLE)
        self._current_w = float(PILL_WIDTH_IDLE)
        self._drag_pos = None
        self._bg = QColor(15, 15, 15, int(255 * PILL_OPACITY))

        self._logo = QPixmap(LOGO_PATH)
        if not self._logo.isNull():
            self._logo = self._logo.scaled(
                LOGO_SIZE, LOGO_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        self._show_check = False
        self._show_spin = False
        self._show_err = False
        self._spin_angle = 0

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedHeight(PILL_HEIGHT)
        self.setFixedWidth(PILL_WIDTH_IDLE)

        self.visualizer = AudioVisualizer(parent=self)
        self.visualizer.setVisible(False)

        self._anim = QTimer()
        self._anim.setInterval(16)
        self._anim.timeout.connect(self._step_width)

        self._spin_timer = QTimer()
        self._spin_timer.setInterval(50)
        self._spin_timer.timeout.connect(self._step_spinner)

        self._done_timer = QTimer()
        self._done_timer.setSingleShot(True)
        self._done_timer.timeout.connect(lambda: self.set_state(self.STATE_IDLE))

        self._place()

    def _place(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.center().x() - PILL_WIDTH_IDLE // 2
            y = geo.bottom() - 4 - PILL_HEIGHT
            self.move(x, y)

    def _native_setup(self):
        ns_view = objc.objc_object(c_void_p=c_void_p(self.winId().__int__()))
        ns_win = ns_view.window()
        ns_win.setLevel_(AppKit.NSFloatingWindowLevel)
        ns_win.setStyleMask_(ns_win.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel)
        ns_win.setHidesOnDeactivate_(False)
        ns_win.setCollectionBehavior_(
            AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
            | AppKit.NSWindowCollectionBehaviorStationary
            | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
        )

    def showEvent(self, event):
        super().showEvent(event)
        try:
            self._native_setup()
        except Exception as e:
            print(f"macOS native setup failed: {e}")

    def set_state(self, state: str):
        self._state = state
        self._show_check = self._show_spin = self._show_err = False
        self._spin_timer.stop()

        if state == self.STATE_IDLE:
            self._target_w = PILL_WIDTH_IDLE
            self.visualizer.setVisible(False)
            self.visualizer.stop()

        elif state == self.STATE_RECORDING:
            self._target_w = PILL_WIDTH_RECORDING
            self.visualizer.setVisible(True)
            self.visualizer.start()

        elif state == self.STATE_PROCESSING:
            self._target_w = PILL_WIDTH_STATUS
            self._show_spin = True
            self._spin_timer.start()
            self.visualizer.setVisible(False)
            self.visualizer.stop()

        elif state == self.STATE_DONE:
            self._target_w = PILL_WIDTH_STATUS
            self._show_check = True
            self.visualizer.setVisible(False)
            self.visualizer.stop()
            self._done_timer.start(800)

        elif state == self.STATE_ERROR:
            self._target_w = PILL_WIDTH_STATUS
            self._show_err = True
            self.visualizer.setVisible(False)
            self.visualizer.stop()
            self._done_timer.start(1200)

        if not self._anim.isActive():
            self._anim.start()
        self.update()

    def _step_spinner(self):
        self._spin_angle = (self._spin_angle + 30) % 360
        self.update()

    def _step_width(self):
        diff = self._target_w - self._current_w
        if abs(diff) < 1:
            self._current_w = self._target_w
            self._anim.stop()
        else:
            self._current_w += diff * 0.22

        left_x = self.x()
        self.setFixedWidth(int(self._current_w))
        self.move(left_x, self.y())
        self._layout()
        self.update()

    def _layout(self):
        w = int(self._current_w)
        logo_end = 6 + LOGO_SIZE + 4
        content_w = w - logo_end - 4
        if content_w > 0 and self.visualizer.isVisible():
            self.visualizer.setGeometry(logo_end, 2, content_w, PILL_HEIGHT - 4)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        path = QPainterPath()
        path.addRoundedRect(0.0, 0.0, float(w), float(h),
                            PILL_CORNER_RADIUS, PILL_CORNER_RADIUS)
        painter.fillPath(path, self._bg)

        painter.setPen(QPen(QColor(255, 255, 255, 12), 0.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(0, 0, w, h, PILL_CORNER_RADIUS, PILL_CORNER_RADIUS)

        if not self._logo.isNull():
            painter.drawPixmap(6, (h - LOGO_SIZE) // 2, self._logo)

        cx = 6 + LOGO_SIZE + 4 + (w - 6 - LOGO_SIZE - 4 - 4) // 2
        cy = h // 2

        if self._show_check:
            pen = QPen(QColor(80, 210, 120), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(cx - 4, cy, cx - 1, cy + 3)
            painter.drawLine(cx - 1, cy + 3, cx + 5, cy - 3)

        elif self._show_spin:
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(6):
                angle = math.radians(self._spin_angle + i * 60)
                dx = 5 * math.cos(angle)
                dy = 5 * math.sin(angle)
                alpha = max(220 - i * 35, 30)
                painter.setBrush(QColor(255, 255, 255, alpha))
                painter.drawEllipse(int(cx + dx) - 1, int(cy + dy) - 1, 2, 2)

        elif self._show_err:
            pen = QPen(QColor(255, 70, 70), 2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(cx - 3, cy - 3, cx + 3, cy + 3)
            painter.drawLine(cx - 3, cy + 3, cx + 3, cy - 3)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
