from PyQt6.QtWidgets import QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from backend import SystemMonitor


class BackupTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Backup / Restore da configuração"))
        self.status = QLabel("Escolha uma operação.")
        layout.addWidget(self.status)
        backup = QPushButton("Criar backup")
        backup.clicked.connect(self.create_backup)
        layout.addWidget(backup)
        restore = QPushButton("Restaurar backup")
        restore.clicked.connect(self.restore_backup)
        layout.addWidget(restore)
        layout.addStretch()

    def create_backup(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar backup", "pamonitor-backup.zip", "Backup ZIP (*.zip)")
        if path:
            ok, message = SystemMonitor.create_config_backup(path)
            self.status.setText(message if ok else f"Erro: {message}")

    def restore_backup(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir backup", "", "Backup ZIP (*.zip)")
        if path:
            ok, message = SystemMonitor.restore_config_backup(path)
            self.status.setText(message if ok else f"Erro: {message}")

    def update_data(self):
        pass