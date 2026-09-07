from PyQt6.QtWidgets import QFileDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from backend import SystemMonitor
from tabs.async_utils import start_background


class LogsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Eventos recentes do sistema"))
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        layout.addWidget(self.viewer)
        refresh = QPushButton("Atualizar logs")
        refresh.clicked.connect(self.update_data)
        layout.addWidget(refresh)
        export = QPushButton("Exportar TXT / CSV")
        export.clicked.connect(self.export_logs)
        self.export_button = export
        layout.addWidget(export)
        self.update_data()

    def update_data(self):
        start_background(self, SystemMonitor.get_recent_logs, self.viewer.setPlainText)

    def export_logs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar logs", "eventos-sistema.txt", "Texto (*.txt);;CSV (*.csv)")
        if path:
            self.export_button.setEnabled(False)
            started = start_background(
                self,
                lambda: SystemMonitor.export_recent_logs(path),
                self._export_finished,
            )
            if not started:
                self.export_button.setEnabled(True)

    def _export_finished(self, result):
        ok, message = result
        self.viewer.append(message if ok else f"Erro: {message}")
        self.export_button.setEnabled(True)