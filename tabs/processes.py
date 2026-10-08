from PyQt6.QtWidgets import QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from gui.widgets import PyTableWidget
from PyQt6.QtCore import Qt
from backend import SystemMonitor
from tabs.async_utils import start_background
from tabs.ui_helpers import make_button, make_line_edit, update_table

class ProcessTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Barra de Ferramentas (Pesquisa e Botão Terminar)
        self.toolbar = QHBoxLayout()
        self.search_bar = make_line_edit("Pesquisar processo pelo nome...")
        self.search_bar.textChanged.connect(self.filter_table)
        
        self.btn_kill = make_button("Terminar Processo", danger=True)
        self.btn_kill.clicked.connect(self.kill_selected_process)

        self.toolbar.addWidget(self.search_bar)
        self.toolbar.addWidget(self.btn_kill)
        self.layout.addLayout(self.toolbar)

        # Tabela de Processos
        self.table = PyTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["PID", "Nome", "CPU (%)", "RAM (%)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(PyTableWidget.SelectionBehavior.SelectRows)
        self.layout.addWidget(self.table)

    def update_data(self):
        # Atualiza a lista apenas se a barra de pesquisa estiver vazia para evitar saltos
        if self.search_bar.text() != "":
            return

        start_background(self, SystemMonitor.get_processes, self._display_data)

    def _display_data(self, processes):
        processes = sorted(processes, key=lambda p: p['cpu_percent'] or 0, reverse=True)[:50] # Top 50 para otimização

        update_table(self.table, len(processes), 4, [
            (proc['pid'], proc['name'], f"{proc['cpu_percent']:.1f}", f"{proc['memory_percent']:.1f}")
            for proc in processes
        ])

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
            self.btn_kill.setEnabled(False)
            started = start_background(
                self,
                lambda: SystemMonitor.kill_process(pid),
                lambda ok: self._kill_finished(pid, ok),
            )
            if not started:
                self.btn_kill.setEnabled(True)

    def _kill_finished(self, pid, ok):
        self.btn_kill.setEnabled(True)
        if ok:
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0) and self.table.item(row, 0).text() == str(pid):
                    self.table.removeRow(row)
                    return
        QMessageBox.warning(self, "Erro", "Sem permissões para terminar este processo.")