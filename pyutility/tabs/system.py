from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHeaderView, QLabel, QProgressBar, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from backend import SystemMonitor
from tabs.async_utils import start_background


class SystemTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("Saúde do Sistema")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2a82da;")
        layout.addWidget(title)

        self.summary = QLabel("A recolher estado do computador...")
        layout.addWidget(self.summary)
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFormat("CPU: %p%")
        self.memory_bar = QProgressBar()
        self.memory_bar.setFormat("Memória: %p%")
        layout.addWidget(self.cpu_bar)
        layout.addWidget(self.memory_bar)

        self.disk_table = QTableWidget(0, 7)
        self.disk_table.setHorizontalHeaderLabels([
            "Unidade", "Montagem", "Formato", "Total", "Usado", "Livre", "Estado",
        ])
        self.disk_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.disk_table)

        self.temperature = QLabel("Temperaturas: indisponíveis neste sistema")
        layout.addWidget(self.temperature)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(5000)
        self.update_data()

    def update_data(self):
        start_background(self, SystemMonitor.get_system_health_info, self._display_data, self._show_error)

    def _show_error(self, message):
        self.summary.setText(f"Não foi possível ler o estado do sistema: {message}")

    def _display_data(self, data):

        self.cpu_bar.setValue(round(data["cpu_percent"]))
        self.memory_bar.setValue(round(data["memory_percent"]))
        self.summary.setText(
            f"Memória disponível: {data['memory_available_gb']:.1f} GB de "
            f"{data['memory_total_gb']:.1f} GB | Discos monitorizados: {len(data['disks'])}"
        )

        disks = data["disks"]
        self.disk_table.setRowCount(len(disks))
        for row, disk in enumerate(disks):
            values = (
                disk["device"], disk["mountpoint"], disk["filesystem"],
                f"{disk['total_gb']:.1f} GB", f"{disk['used_gb']:.1f} GB",
                f"{disk['free_gb']:.1f} GB", "OK" if disk["percent"] < 90 else "Atenção",
            )
            for column, text in enumerate(values):
                self.disk_table.setItem(row, column, QTableWidgetItem(str(text)))

        temperatures = data["temperatures"]
        if temperatures:
            self.temperature.setText("Temperaturas: " + " | ".join(
                f"{item['sensor']}: {item['current']:.1f}°C" for item in temperatures
            ))