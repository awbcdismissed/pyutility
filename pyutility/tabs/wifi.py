from PyQt6.QtCore import QDateTime, QTimer
from PyQt6.QtWidgets import QFormLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from backend import SystemMonitor
from tabs.async_utils import start_background


class WifiTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        title = QLabel("Wi-Fi / Rede")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2a82da;")
        layout.addWidget(title)
        self.details = QLabel("A recolher ligação Wi-Fi...")
        layout.addWidget(self.details)
        form = QFormLayout()
        self.host = QLineEdit("1.1.1.1")
        self.ping_button = QPushButton("Testar latência")
        self.ping_button.clicked.connect(self.test_ping)
        form.addRow("Destino:", self.host)
        form.addRow(self.ping_button)
        layout.addLayout(form)
        self.ping_result = QLabel()
        layout.addWidget(self.ping_result)
        self.history = QTableWidget(0, 2)
        self.history.setHorizontalHeaderLabels(["Hora", "Latência"])
        layout.addWidget(self.history)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)
        self.update_data()

    def update_data(self):
        start_background(self, SystemMonitor.get_wifi_info, self._display_data)

    def _display_data(self, data):
        self.details.setText(
            f"Interface: {data['interface']} | SSID: {data['ssid']} | "
            f"Sinal: {data['signal']} | Canal: {data['channel']} | Banda: {data['band']}"
        )

    def test_ping(self):
        self.ping_button.setEnabled(False)
        started = start_background(self, lambda: SystemMonitor.ping_host(self.host.text()), self._display_ping)
        if not started:
            self.ping_button.setEnabled(True)

    def _display_ping(self, result):
        latency = f"{result['latency_ms']} ms" if result["latency_ms"] is not None else result["status"]
        self.ping_result.setText(f"{result['host']}: {latency}")
        row = self.history.rowCount()
        self.history.insertRow(row)
        self.history.setItem(row, 0, QTableWidgetItem(QDateTime.currentDateTime().toString("hh:mm:ss")))
        self.history.setItem(row, 1, QTableWidgetItem(latency))
        self.ping_button.setEnabled(True)
