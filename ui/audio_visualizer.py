import math
import queue
from typing import Optional

import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QLinearGradient

from config import NUM_BARS, VIZ_FPS, BAR_GAIN


class AudioVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.num_bars = NUM_BARS
        self._values = [0.0] * self.num_bars
        self._velocities = [0.0] * self.num_bars
        self._queue: Optional[queue.Queue] = None

        self._timer = QTimer()
        self._timer.setInterval(1000 // VIZ_FPS)
        self._timer.timeout.connect(self._tick)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_audio_queue(self, q: queue.Queue):
        self._queue = q

    def start(self):
        self._values = [0.0] * self.num_bars
        self._velocities = [0.0] * self.num_bars
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self._values = [0.0] * self.num_bars
        self._velocities = [0.0] * self.num_bars
        self.update()

    def _tick(self):
        if not self._queue:
            return

        chunks = []
        while True:
            try:
                chunks.append(self._queue.get_nowait())
            except queue.Empty:
                break

        targets = [0.0] * self.num_bars
        if chunks:
            raw = chunks[-1]
            ch = raw[:, 0] if raw.ndim > 1 else raw
            ch = ch.astype(np.float32) / 32768.0
            fft = np.abs(np.fft.rfft(ch))
            bins = np.array_split(fft[:len(fft) // 2], self.num_bars)
            for i, b in enumerate(bins):
                if len(b):
                    targets[i] = min(float(np.mean(b)) * BAR_GAIN * 2.0, 1.0)

        dt = 1.0 / VIZ_FPS
        stiffness, damping = 35.0, 8.0
        for i in range(self.num_bars):
            diff = targets[i] - self._values[i]
            self._velocities[i] += diff * stiffness * dt
            self._velocities[i] *= max(0, 1.0 - damping * dt)
            self._values[i] += self._velocities[i] * dt
            if self._values[i] < 0.005:
                self._values[i] = 0.0
                self._velocities[i] = 0.0
            elif self._values[i] > 1.0:
                self._values[i] = 1.0

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            painter.end()
            return

        bar_w, gap = 1.8, 2.0
        total_w = self.num_bars * bar_w + (self.num_bars - 1) * gap
        x_off = (w - total_w) / 2.0
        center = self.num_bars / 2.0
        painter.setPen(Qt.PenStyle.NoPen)

        for i, val in enumerate(self._values):
            dist = abs(i - center + 0.5) / center
            taper = math.exp(-dist * dist * 1.2)
            bar_h = max(2.0, val * h * 1.6 * taper)
            x = x_off + i * (bar_w + gap)
            y = h / 2.0 - bar_h / 2.0

            if val > 0.02:
                gw = bar_w + 3.0
                gx = x - (gw - bar_w) / 2
                painter.setBrush(QColor(255, 255, 255, int(val * 40 * taper)))
                painter.drawRoundedRect(QRectF(gx, y - 1, gw, bar_h + 2), gw / 2, gw / 2)

            grad = QLinearGradient(x, y, x, y + bar_h)
            peak = int((100 + val * 155) * taper)
            edge = int(peak * 0.3)
            grad.setColorAt(0.0, QColor(255, 255, 255, edge))
            grad.setColorAt(0.35, QColor(255, 255, 255, peak))
            grad.setColorAt(0.65, QColor(255, 255, 255, peak))
            grad.setColorAt(1.0, QColor(255, 255, 255, edge))
            painter.setBrush(grad)
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), bar_w / 2, bar_w / 2)

        painter.end()
