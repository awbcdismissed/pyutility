from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHeaderView
from gui.widgets import PyTableWidget
from backend import SystemMonitor
from tabs.async_utils import start_background
from tabs.ui_helpers import update_table

class NetworkTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Informações de IP
        self.lbl_local = QLabel("IP Local: Carregando...")
        self.lbl_public = QLabel("IP Público: Carregando...")
        self.lbl_local.setStyleSheet("font-weight: bold; font-size: 13px;")
        self.lbl_public.setStyleSheet("font-weight: bold; font-size: 13px; color: #2a82da;")
        
        self.layout.addWidget(self.lbl_local)
        self.layout.addWidget(self.lbl_public)
        self.layout.addSpacing(10)

        # Tabela de Conexões Ativas
        self.lbl_table = QLabel("Ligações Ativas / Portas em Escuta:")
        self.layout.addWidget(self.lbl_table)

        self.table = PyTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Local (IP:Porta)", "Remoto (Destino)", "Estado"])
        
        # Ajustar colunas para preencher o espaço
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.layout.addWidget(self.table)

    def update_data(self):
        start_background(self, SystemMonitor.get_network_info, self._display_data)

    def _display_data(self, data):
        
        self.lbl_local.setText(f"IP Local: {data['local']}")
        self.lbl_public.setText(f"IP Público: {data['public']}")

        conns = data['conns']
        update_table(self.table, len(conns), 3, [
            (connection['local'], connection['remote'], connection['status'])
            for connection in conns
        ])