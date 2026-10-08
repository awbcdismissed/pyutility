import webbrowser

from PyQt6.QtWidgets import QHeaderView, QLabel, QVBoxLayout, QWidget
from gui.widgets import PyTableWidget

from backend import SystemMonitor
from tabs.async_utils import start_background
from tabs.ui_helpers import make_button, update_table


class DriversTab(QWidget):
    def __init__(self, initial_data=None):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Drivers instalados"))
        self.info = QLabel("Os drivers são listados pelo Windows.")
        layout.addWidget(self.info)
        self.table = PyTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Nome", "Descrição", "Tipo", "Estado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        refresh = make_button("Verificar drivers")
        refresh.clicked.connect(self.update_data)
        layout.addWidget(refresh)
        search = make_button("Abrir pesquisa oficial do fabricante")
        search.clicked.connect(lambda: webbrowser.open("https://support.microsoft.com/windows/update-drivers-manually-in-windows"))
        layout.addWidget(search)
        if initial_data is not None:
            self._display_data(initial_data)

    def update_data(self):
        start_background(self, SystemMonitor.get_driver_info, self._display_data)

    def _display_data(self, drivers):
        self.info.setText(f"{len(drivers)} drivers encontrados.")
        update_table(self.table, len(drivers), 4, [
            tuple(driver[key] for key in ("name", "display_name", "type", "state"))
            for driver in drivers
        ])