import time
from typing import Optional
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal
from config import DOUBLE_TAP_INTERVAL


class HotkeyListener(QObject):
    """Global hotkey listener.

    Hold Ctrl+Option  → push-to-talk recording
    Double-tap Ctrl   → hands-free toggle
    """

    pressed = pyqtSignal()
    released = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._ctrl = False
        self._alt = False
        self._recording = False
        self._hands_free = False
        self._last_ctrl_press = 0.0
        self._tap_count = 0
        self._listener: Optional[keyboard.Listener] = None

    def start(self):
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        is_ctrl = key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)
        is_alt = key in (keyboard.Key.alt, keyboard.Key.alt_l,
                         keyboard.Key.alt_r, keyboard.Key.alt_gr)

        if is_ctrl:
            self._ctrl = True
            now = time.time()

            if self._hands_free and self._recording:
                self._hands_free = False
                self._recording = False
                self.released.emit()
                return

            if now - self._last_ctrl_press < DOUBLE_TAP_INTERVAL:
                self._tap_count += 1
            else:
                self._tap_count = 1
            self._last_ctrl_press = now

            if self._tap_count >= 2 and not self._recording:
                self._tap_count = 0
                self._hands_free = True
                self._recording = True
                self.pressed.emit()
                return

        elif is_alt:
            self._alt = True

        if self._ctrl and self._alt and not self._recording:
            self._recording = True
            self._hands_free = False
            self.pressed.emit()

    def _on_release(self, key):
        is_ctrl = key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)
        is_alt = key in (keyboard.Key.alt, keyboard.Key.alt_l,
                         keyboard.Key.alt_r, keyboard.Key.alt_gr)

        if is_ctrl:
            self._ctrl = False
        elif is_alt:
            self._alt = False

        if self._recording and not self._hands_free:
            if not (self._ctrl and self._alt):
                self._recording = False
                self.released.emit()
