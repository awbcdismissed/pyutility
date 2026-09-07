from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from backend import SystemMonitor
from tabs.async_utils import start_background

class ProcessTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Barra de Ferramentas (Pesquisa e Botão Terminar)
        self.toolbar = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Pesquisar processo pelo nome...")
        self.search_bar.textChanged.connect(self.filter_table)
        
        self.btn_kill = QPushButton("Terminar Processo")
        self.btn_kill.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold;")
        self.btn_kill.clicked.connect(self.kill_selected_process)

        self.toolbar.addWidget(self.search_bar)
        self.toolbar.addWidget(self.btn_kill)
        self.layout.addLayout(self.toolbar)

        # Tabela de Processos
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["PID", "Nome", "CPU (%)", "RAM (%)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.table)

    def update_data(self):
        # Atualiza a lista apenas se a barra de pesquisa estiver vazia para evitar saltos
        if self.search_bar.text() != "":
            return

        start_background(self, SystemMonitor.get_processes, self._display_data)

    def _display_data(self, processes):
        processes = sorted(processes, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:50] # Top 50 para otimização

        self.table.setRowCount(0)
        for row, proc in enumerate(processes):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(proc['pid'])))
            self.table.setItem(row, 1, QTableWidgetItem(proc['name']))
            self.table.setItem(row, 2, QTableWidgetItem(f"{proc['cpu_percent']:.1f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{proc['memory_percent']:.1f}"))

    def filter_table(self, text):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            self.table.setRowHidden(row, text.lower() not in item.text().lower())

    def kill_selected_process(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        pid = int(self.table.item(current_row, 0).text())
        name = self.table.item(current_row, 1).text()

        reply = QMessageBox.question(self, 'Confirmar', f'Deseja terminar o processo {name} (PID: {pid})?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if SystemMonitor.kill_process(pid):
                self.table.removeRow(current_row)
            else:
                QMessageBox.warning(self, "Erro", "Sem permissões para terminar este processo.")