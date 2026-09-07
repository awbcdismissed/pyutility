from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget
from PyQt6.QtCore import QTimer, QDateTime
from backend import SystemMonitor
from tabs.async_utils import start_background

class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.info = QLabel("Registo de Aplicações em Foco (Atualização a cada 10s):")
        self.info.setStyleSheet("font-weight: bold; color: #2a82da;")
        layout.addWidget(self.info)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("background-color: #222; border-radius: 5px; padding: 5px;")
        layout.addWidget(self.list_widget)

        # Timer específico para o histórico (10 segundos)
        self.h_timer = QTimer()
        self.h_timer.timeout.connect(self.update_data)
        self.h_timer.start(10000) 

    def update_data(self):
        start_background(self, SystemMonitor.get_active_window_process, self._add_process)

    def _add_process(self, proc):
        if proc:
            time_now = QDateTime.currentDateTime().toString("hh:mm:ss")
            self.list_widget.insertItem(0, f"[{time_now}] Aplicação ativa: {proc}")
            if self.list_widget.count() > 100:
                self.list_widget.takeItem(100)