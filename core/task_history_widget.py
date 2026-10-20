"""Read-only task history, fetched off the Qt thread."""
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem, QPushButton


class TaskHistoryWidget(QWidget):
    loaded = pyqtSignal(object, str)

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = Path(database)
        self.busy = False
        layout = QVBoxLayout(self)
        self.note = QLabel('Histórico das ferramentas executadas.'); self.note.setWordWrap(True)
        layout.addWidget(self.note)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Tarefa', 'Estado', 'Início', 'Duração'])
        self.tree.setMinimumHeight(200); layout.addWidget(self.tree)
        refresh = QPushButton('Atualizar'); refresh.clicked.connect(self.refresh); layout.addWidget(refresh)
        self.loaded.connect(self.render)
        self.timer = QTimer(self); self.timer.timeout.connect(self.refresh); self.timer.start(2000)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def refresh(self):
        if self.busy or not self.isVisible(): return
        self.busy = True
        def read():
            rows, error = [], ''
            try:
                if self.database.exists():
                    with sqlite3.connect(self.database.resolve().as_uri()+'?mode=ro', uri=True, timeout=1) as db:
                        db.row_factory = sqlite3.Row
                        rows = [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY started DESC LIMIT 40')]
            except Exception:
                error = 'Histórico indisponível. Tente atualizar.'
            try: self.loaded.emit(rows, error)
            except RuntimeError: pass  # window closed during read
        threading.Thread(target=read, daemon=True).start()

    def render(self, rows, error):
        self.busy = False
        self.tree.clear()
        labels = dict(running='Em andamento', succeeded='Concluída', failed='Falhou', cancelled='Cancelada', timed_out='Tempo esgotado')
        for row in rows:
            duration = f"{row['ended']-row['started']:.1f} s" if row['ended'] else '—'
            item = QTreeWidgetItem([row['name'], labels.get(row['state'], row['state']), datetime.fromtimestamp(row['started']).strftime('%H:%M:%S'), duration])
            item.setToolTip(1, row['detail']); self.tree.addTopLevelItem(item)
        self.note.setText(error or ('Nenhuma tarefa registrada.' if not rows else 'Estado registrado em disco. Passe o mouse sobre o estado para detalhes.'))
        self.tree.resizeColumnToContents(0)
