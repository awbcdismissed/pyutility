from PyQt6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget
from tabs.ui_helpers import make_button

from backend import SystemMonitor
from tabs.async_utils import start_background


class BackupTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Backup / Restore da configuração"))
        self.status = QLabel("Escolha uma operação.")
        layout.addWidget(self.status)
        self.backup_button = make_button("Criar backup")
        self.backup_button.clicked.connect(self.create_backup)
        layout.addWidget(self.backup_button)
        self.restore_button = make_button("Restaurar backup")
        self.restore_button.clicked.connect(self.restore_backup)
        layout.addWidget(self.restore_button)
        layout.addStretch()

    def create_backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar backup", "pamonitor-backup.zip", "Backup ZIP (*.zip)")
        if path:
            self._set_buttons_enabled(False)
            self.status.setText("A criar backup...")
            started = start_background(
                self,
                lambda: SystemMonitor.create_config_backup(path),
                self._operation_finished,
            )
            if not started:
                self._set_buttons_enabled(True)

    def restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir backup", "", "Backup ZIP (*.zip)")
        if path:
            self._set_buttons_enabled(False)
            self.status.setText("A restaurar backup...")
            started = start_background(
                self,
                lambda: SystemMonitor.restore_config_backup(path),
                self._operation_finished,
            )
            if not started:
                self._set_buttons_enabled(True)

    def _set_buttons_enabled(self, enabled):
        self.backup_button.setEnabled(enabled)
        self.restore_button.setEnabled(enabled)

    def _operation_finished(self, result):
        ok, message = result
        self.status.setText(message if ok else f"Erro: {message}")
        self._set_buttons_enabled(True)

    def update_data(self):
        pass