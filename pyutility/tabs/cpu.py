from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from backend import SystemMonitor
from tabs.async_utils import start_background

class CPUTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.labels = {
            "Processador:": QLabel("-"),
            "Fabricante:": QLabel("-"),
            "Arquitetura:": QLabel("-"),
            "Núcleos físicos:": QLabel("-"),
            "Threads:": QLabel("-"),
            "Frequência Atual:": QLabel("-"),
            "Frequência Máxima:": QLabel("-"),
            "Sockets:": QLabel("-")
        }

        for i, (key, lbl) in enumerate(self.labels.items()):
            name_lbl = QLabel(key)
            name_lbl.setStyleSheet("color: #aaa; font-weight: bold;")
            self.grid.addWidget(name_lbl, i, 0)
            self.grid.addWidget(lbl, i, 1)
        
        layout.addStretch()

        self._is_loaded = False

    def _safe_set_text(self, label_key, value, fallback="N/D"):
        text = value if value is not None and str(value).strip() else fallback
        label = self.labels.get(label_key)
        if label is not None:
            label.setText(str(text))

    def update_data(self):
        start_background(self, SystemMonitor.get_cpu_detailed_info, self._display_data)

    def _display_data(self, d):
        d = d or {}
        self._safe_set_text("Processador:", d.get("processor", "N/D"))
        self._safe_set_text("Fabricante:", d.get("vendor", "N/D"))
        self._safe_set_text("Arquitetura:", d.get("architecture", "N/D"))
        self._safe_set_text("Núcleos físicos:", d.get("cores_physical", 0))
        self._safe_set_text("Threads:", d.get("threads", 0))
        self._safe_set_text("Frequência Atual:", d.get("freq_current", "N/D"))
        self._safe_set_text("Frequência Máxima:", d.get("freq_max", "N/D"))
        self._safe_set_text("Sockets:", d.get("socket_count", 1))
        self._is_loaded = True