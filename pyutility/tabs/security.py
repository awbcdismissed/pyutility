from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from backend import SystemMonitor
from tabs.async_utils import start_background


class SecurityTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Estado de Segurança"))
        self.antivirus = QLabel("Antivírus: a verificar...")
        layout.addWidget(self.antivirus)
        layout.addWidget(QLabel("Portas em escuta"))
        self.ports = QTableWidget(0, 3)
        self.ports.setHorizontalHeaderLabels(["Endereço", "Porta", "PID"])
        self.ports.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.ports)
        self.suspicious = QLabel("Processos: a verificar...")
        layout.addWidget(self.suspicious)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(10000)
        self.update_data()

    def update_data(self):
        start_background(self, SystemMonitor.get_security_info, self._display_data)

    def _display_data(self, data):
        self.antivirus.setText(f"Antivírus Microsoft Defender: {data['antivirus']}")
        self.ports.setRowCount(len(data["listening"]))
        for row, port in enumerate(data["listening"]):
            for column, key in enumerate(("address", "port", "pid")):
                self.ports.setItem(row, column, QTableWidgetItem(str(port[key])))
        suspicious = [item for item in data["processes"] if float(item.get("cpu_percent") or 0) > 80]
        self.suspicious.setText(f"Processos com uso elevado de CPU: {len(suspicious)}")