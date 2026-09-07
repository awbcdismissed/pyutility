import webbrowser

from PyQt6.QtWidgets import QHeaderView, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from backend import SystemMonitor
from tabs.async_utils import start_background


class DriversTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Drivers instalados"))
        self.info = QLabel("Os drivers são listados pelo Windows.")
        layout.addWidget(self.info)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nome", "Descrição", "Tipo", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        refresh = QPushButton("Verificar drivers")
        refresh.clicked.connect(self.update_data)
        layout.addWidget(refresh)
        search = QPushButton("Abrir pesquisa oficial do fabricante")
        search.clicked.connect(lambda: webbrowser.open("https://support.microsoft.com/windows/update-drivers-manually-in-windows"))
        layout.addWidget(search)
        self.update_data()

    def update_data(self):
        start_background(self, SystemMonitor.get_driver_info, self._display_data)

    def _display_data(self, drivers):
        self.info.setText(f"{len(drivers)} drivers encontrados.")
        self.table.setRowCount(len(drivers))
        for row, driver in enumerate(drivers):
            for column, key in enumerate(("name", "display_name", "type", "state")):
                self.table.setItem(row, column, QTableWidgetItem(driver[key]))