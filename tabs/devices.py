import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QHeaderView, QLabel, QMenu, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from backend import SystemMonitor
from tabs.async_utils import start_background


class DevicesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dispositivos ligados ao computador"))
        self.info = QLabel("A pesquisar dispositivos...")
        layout.addWidget(self.info)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Dispositivo", "Estado", "ID de hardware"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_menu)
        layout.addWidget(self.tree)

    def update_data(self):
        start_background(self, SystemMonitor.get_devices, self._display_data)

    def _display_data(self, devices):
        self.tree.clear()
        groups = {}
        for device in devices:
            groups.setdefault(device["class"], []).append(device)
        for device_class, entries in sorted(groups.items()):
            group = QTreeWidgetItem([device_class, f"{len(entries)} dispositivo(s)", ""])
            group.setData(0, Qt.ItemDataRole.UserRole, None)
            self.tree.addTopLevelItem(group)
            for device in sorted(entries, key=lambda entry: entry["name"].lower()):
                status = device["status"]
                if not device["present"]:
                    status = "Não presente"
                if device["problem"]:
                    status = f"Problema {device['problem']}"
                child = QTreeWidgetItem([device["name"], status, device["instance_id"]])
                child.setData(0, Qt.ItemDataRole.UserRole, device)
                group.addChild(child)
            group.setExpanded(True)
        self.info.setText(f"{len(devices)} dispositivos encontrados.")

    def show_menu(self, position):
        item = self.tree.itemAt(position)
        device = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if not device:
            return
        menu = QMenu(self)
        properties = QAction("Abrir propriedades", self)
        properties.triggered.connect(lambda: SystemMonitor.open_device_properties(device["instance_id"]))
        menu.addAction(properties)
        enabled = device["status"].lower() == "ok" and device["present"]
        toggle = QAction("Desativar" if enabled else "Ativar", self)
        toggle.triggered.connect(lambda: self.toggle_device(device, not enabled))
        menu.addAction(toggle)
        search = QAction("Pesquisar HWID no browser", self)
        search.triggered.connect(lambda: webbrowser.open(
            "https://www.google.com/search?q=" + device["instance_id"].replace(" ", "+")
        ))
        menu.addAction(search)
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def toggle_device(self, device, enabled):
        self.info.setText("A atualizar o dispositivo...")
        start_background(
            self,
            lambda: SystemMonitor.set_device_enabled(device["instance_id"], enabled),
            self._toggle_finished,
        )

    def _toggle_finished(self, result):
        ok, message = result
        self.info.setText(message if ok else f"Erro: {message}")
        if ok:
            self.update_data()