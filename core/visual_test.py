"""Offline test bench for the production orb; no microphone or API is opened."""
from __future__ import annotations
import sys
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                            QComboBox, QSlider, QLabel, QCheckBox)
from core.ember_bridge import LiveEmber


class OrbPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 400)
        self.renderer = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#05060a'))
        if self.renderer and self.renderer.image is not None:
            side = min(self.width(), self.height())
            area = QRectF((self.width()-side)/2, (self.height()-side)/2, side, side)
            painter.drawImage(area, self.renderer.image)


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle('JARVIS — Teste visual da esfera')
    window.resize(720, 800)
    layout = QVBoxLayout(window)
    layout.addWidget(QLabel('Render real • amplitude manual de teste • sem microfone/API'))
    preview = OrbPreview()
    layout.addWidget(preview, 1)
    controls = QHBoxLayout()
    state = QComboBox()
    for label, value in [('Espera','IDLE'), ('Escutando','LISTENING'), ('Processando','THINKING'),
                         ('Falando','SPEAKING'), ('Executando','EXECUTING'), ('Erro','ERROR')]:
        state.addItem(label, value)
    quality = QComboBox()
    for name in ('economy', 'balanced', 'premium'):
        quality.addItem(name)
    quality.setCurrentText('balanced')
    muted = QCheckBox('Silenciado')
    controls.addWidget(state); controls.addWidget(quality); controls.addWidget(muted)
    layout.addLayout(controls)
    layout.addWidget(QLabel('Amplitude de teste'))
    amplitude = QSlider(Qt.Orientation.Horizontal)
    amplitude.setRange(0, 100)
    layout.addWidget(amplitude)
    status = QLabel('Iniciando renderizador…')
    status.setWordWrap(True)
    layout.addWidget(status)

    def replace_renderer():
        if preview.renderer:
            preview.renderer.close()
        renderer = LiveEmber(window, quality=quality.currentText())
        renderer.updated.connect(preview.update)
        renderer.fault.connect(status.setText)
        preview.renderer = renderer
        status.setText('Teste visual local; desempenho e áudio real devem ser verificados no PC.')

    replace_renderer()
    quality.currentIndexChanged.connect(replace_renderer)
    timer = QTimer(window)
    def update():
        preview.renderer.update_state(state.currentData(), amplitude.value()/100., muted.isChecked())
    timer.timeout.connect(update)
    timer.start(33)
    app.aboutToQuit.connect(lambda: preview.renderer.close())
    window.show()
    app.exec()
