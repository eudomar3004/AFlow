#!/usr/bin/env python3
"""AFlow - Voz a texto para macOS usando Groq Whisper."""

import os
import sys
import signal
import subprocess
import threading

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QAction

from ui.pill_widget import PillWidget
from core.recorder import AudioRecorder
from core.transcriber import Transcriber
from core.hotkey import HotkeyListener
from core.clipboard import paste_text, save_frontmost_app
from db.database import TranscriptionDB
from web.server import start_web_server
from config import LOGO_PATH, APP_DATA_DIR, GROQ_API_KEY


_AGENT_LABEL = "so.ailoom.aflow"
_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{_AGENT_LABEL}.plist")


def _request_accessibility():
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
        AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": True})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# First-run dialog
# ---------------------------------------------------------------------------
class SetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFlow - Configuración inicial")
        self.setFixedWidth(420)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Ingresa tu Groq API Key para empezar:"))

        link = QLabel('<a href="https://console.groq.com/keys">Obtener gratis → console.groq.com/keys</a>')
        link.setOpenExternalLinks(True)
        layout.addWidget(link)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("gsk_...")
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.key_input)

        btn = QPushButton("Guardar y continuar")
        btn.clicked.connect(self._save)
        layout.addWidget(btn)

        self.setLayout(layout)

    def _save(self):
        key = self.key_input.text().strip()
        if not key.startswith("gsk_") or len(key) < 20:
            QMessageBox.warning(self, "Error", "La clave debe comenzar con 'gsk_' y tener al menos 20 caracteres.")
            return
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        with open(os.path.join(APP_DATA_DIR, ".env"), "w") as f:
            f.write(f"GROQ_API_KEY={key}\n")
        os.environ["GROQ_API_KEY"] = key
        self.accept()


# ---------------------------------------------------------------------------
# Launch at Login
# ---------------------------------------------------------------------------
def _launch_at_login_enabled() -> bool:
    return os.path.exists(_PLIST)


def _set_launch_at_login(enabled: bool):
    if enabled:
        exe = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>{_AGENT_LABEL}</string>
    <key>ProgramArguments</key><array><string>{exe}</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><false/>
</dict>
</plist>"""
        os.makedirs(os.path.dirname(_PLIST), exist_ok=True)
        with open(_PLIST, "w") as f:
            f.write(plist)
        subprocess.run(["launchctl", "load", _PLIST], capture_output=True)
    else:
        if os.path.exists(_PLIST):
            subprocess.run(["launchctl", "unload", _PLIST], capture_output=True)
            os.remove(_PLIST)


# ---------------------------------------------------------------------------
# System tray
# ---------------------------------------------------------------------------
def _build_tray(app: QApplication, port: int) -> QSystemTrayIcon:
    px = QPixmap(LOGO_PATH)
    icon = QIcon(px.scaled(22, 22, Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)) if not px.isNull() else QIcon()

    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()

    lbl = QAction("AFlow — Activo", menu)
    lbl.setEnabled(False)
    menu.addAction(lbl)
    menu.addSeparator()

    dash = QAction(f"Abrir Dashboard (:{port})", menu)
    dash.triggered.connect(lambda: subprocess.run(["open", f"http://localhost:{port}"], capture_output=True))
    menu.addAction(dash)
    menu.addSeparator()

    login = QAction("Iniciar con macOS", menu)
    login.setCheckable(True)
    login.setChecked(_launch_at_login_enabled())
    login.toggled.connect(_set_launch_at_login)
    menu.addAction(login)
    menu.addSeparator()

    quit_act = QAction("Salir", menu)
    quit_act.triggered.connect(app.quit)
    menu.addAction(quit_act)

    tray.setContextMenu(menu)
    tray.setToolTip("AFlow - Voz a Texto")
    tray.show()
    return tray


# ---------------------------------------------------------------------------
# App controller
# ---------------------------------------------------------------------------
class AFlowController(QObject):
    _transcription_done = pyqtSignal(str, float)
    _transcription_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self.db = TranscriptionDB()
        self.hotkey = HotkeyListener()
        self.pill = PillWidget()

        self.pill.visualizer.set_audio_queue(self.recorder.audio_queue)

        self.hotkey.pressed.connect(self._on_pressed, Qt.ConnectionType.QueuedConnection)
        self.hotkey.released.connect(self._on_released, Qt.ConnectionType.QueuedConnection)
        self._transcription_done.connect(self._on_done, Qt.ConnectionType.QueuedConnection)
        self._transcription_error.connect(self._on_error, Qt.ConnectionType.QueuedConnection)

    def start(self):
        self.hotkey.start()
        self.pill.show()
        self.pill.set_state(PillWidget.STATE_IDLE)

    @pyqtSlot()
    def _on_pressed(self):
        save_frontmost_app()
        self.recorder.start()
        self.pill.set_state(PillWidget.STATE_RECORDING)

    @pyqtSlot()
    def _on_released(self):
        duration = self.recorder.stop()
        self.pill.set_state(PillWidget.STATE_PROCESSING)
        if duration < 0.3:
            self.pill.set_state(PillWidget.STATE_IDLE)
            return
        wav = self.recorder.get_wav_buffer()
        rec_dur = self.recorder.get_duration()
        threading.Thread(target=self._worker, args=(wav, rec_dur), daemon=True).start()

    def _worker(self, wav, duration):
        try:
            text = self.transcriber.transcribe(wav)
            if text:
                self._transcription_done.emit(text, duration)
            else:
                self._transcription_error.emit("Sin texto detectado")
        except Exception as e:
            self._transcription_error.emit(str(e))

    @pyqtSlot(str, float)
    def _on_done(self, text: str, duration: float):
        paste_text(text)
        self.db.insert(text=text, duration_seconds=duration)
        self.pill.set_state(PillWidget.STATE_DONE)

    @pyqtSlot(str)
    def _on_error(self, _: str):
        self.pill.set_state(PillWidget.STATE_ERROR)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("AFlow")
    app.setQuitOnLastWindowClosed(False)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if not os.getenv("GROQ_API_KEY", ""):
        dialog = SetupDialog()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

    try:
        import AppKit
        AppKit.NSApp.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)
    except Exception:
        pass

    port = start_web_server()
    _request_accessibility()

    controller = AFlowController()
    controller.start()

    tray = _build_tray(app, port)  # noqa: F841

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
