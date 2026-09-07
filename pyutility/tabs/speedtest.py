from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout
from PyQt6.QtCore import QThread, QObject, pyqtSignal

from backend import SystemMonitor


class SpeedTestWorker(QObject):
    finished = pyqtSignal(dict)

    def run(self):
        print("[DEBUG][SpeedTab] SpeedTestWorker.run started")
        result = SystemMonitor.run_speed_test(iterations=3)
        print(f"[DEBUG][SpeedTab] SpeedTestWorker.run finished with result: {result}")
        self.finished.emit(result)


class SpeedTesterTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.title = QLabel("Teste de velocidade da rede")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2a82da;")
        self.layout.addWidget(self.title)

        self.btn_test = QPushButton("Testar velocidade")
        self.btn_test.clicked.connect(self.run_test)
        self.layout.addWidget(self.btn_test)

        self.status = QLabel("Pronto para testar.")
        self.layout.addWidget(self.status)

        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        self.lbl_download = QLabel("Download: --")
        self.lbl_upload = QLabel("Upload: --")
        self.lbl_ping = QLabel("Ping: --")

        self.grid.addWidget(QLabel("Download:"), 0, 0)
        self.grid.addWidget(self.lbl_download, 0, 1)
        self.grid.addWidget(QLabel("Upload:"), 1, 0)
        self.grid.addWidget(self.lbl_upload, 1, 1)
        self.grid.addWidget(QLabel("Ping:"), 2, 0)
        self.grid.addWidget(self.lbl_ping, 2, 1)

        self.layout.addStretch()

    def update_data(self):
        pass

    def run_test(self):
        print("[DEBUG][SpeedTab] run_test button clicked")
        self.btn_test.setEnabled(False)
        self.status.setText("A medir ping, download e upload... isto pode demorar 20-40s.")
        self.lbl_download.setText("Download: a medir...")
        self.lbl_upload.setText("Upload: a medir...")
        self.lbl_ping.setText("Ping: a medir...")

        self.thread = QThread(self)
        self.worker = SpeedTestWorker()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_test_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        print("[DEBUG][SpeedTab] starting QThread for speed test")
        self.thread.start()

    def on_test_finished(self, result):
        print(f"[DEBUG][SpeedTab] on_test_finished received result: {result}")
        if result["status"] == "OK":
            self.lbl_download.setText(f"Download: {result['download_mbps']:.2f} Mbps")
            self.lbl_upload.setText(f"Upload: {result['upload_mbps']:.2f} Mbps")
            self.lbl_ping.setText(f"Ping: {result['ping_ms']:.2f} ms")
            self.status.setText("Teste concluído.")
        else:
            self.lbl_download.setText("Download: N/D")
            self.lbl_upload.setText("Upload: N/D")
            self.lbl_ping.setText("Ping: N/D")
            self.status.setText(f"Erro: {result.get('error', 'Falha no teste')[:100]}")

        self.btn_test.setEnabled(True)
