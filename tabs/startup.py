from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMenu,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from gui.widgets import PyTableWidget

from backend import SystemMonitor
from tabs.async_utils import start_background
from tabs.ui_helpers import update_table


class StartupTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Programas no arranque do Windows"))
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.table = self._create_table("Programas ativos", splitter)
        self.disabled_table = self._create_table("Programas desativados", splitter)
        splitter.setSizes([1, 1])
        layout.addWidget(splitter)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)

    def update_data(self):
        start_background(self, SystemMonitor.get_startup_items, self._display_data)

    def _display_data(self, items):
        active_items = [item for item in items if item.get("enabled", True)]
        disabled_items = [item for item in items if not item.get("enabled", True)]
        self._populate_table(self.table, active_items)
        self._populate_table(self.disabled_table, disabled_items)

    def _create_table(self, title, parent):
        container = QWidget(parent)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(QLabel(title))
        table = PyTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Nome", "Âmbito", "Origem", "Estado", "Comando"])
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda position: self.show_menu(table, position))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        container_layout.addWidget(table)
        parent.addWidget(container)
        return table

    def _populate_table(self, table, items):
        values = [
            (item["name"], item["scope"], item["source"],
             "Ativo" if item.get("enabled", True) else "Desativado", item["command"])
            for item in items
        ]
        update_table(table, len(values), 5, values)
        for row, item in enumerate(items):
            table.item(row, 0).setData(Qt.ItemDataRole.UserRole, item)

    def show_menu(self, table, position):
        row = table.rowAt(position.y())
        if row < 0:
            return
        item = table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        action_text = "Desativar" if item.get("enabled", True) else "Ativar"
        toggle = QAction(action_text, self)
        toggle.triggered.connect(lambda: self.toggle_item(item))
        menu.addAction(toggle)
        menu.exec(table.viewport().mapToGlobal(position))

    def toggle_item(self, item):
        enabled = not item.get("enabled", True)
        self._toggle_item = item
        self.window().show_status("A atualizar o arranque...")
        started = start_background(
            self,
            lambda: SystemMonitor.set_startup_item_enabled(item, enabled),
            self._toggle_finished,
        )
        if not started:
            return

    def _toggle_finished(self, result):
        ok, message = result
        if not ok:
            self.window().show_status(f"Erro: {message}")
        self.update_data()