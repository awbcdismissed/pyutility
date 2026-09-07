from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from backend import SystemMonitor


class GPUDataWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def run(self):
        try:
            self.finished.emit(SystemMonitor.get_gpu_detailed_info())
        except Exception as exc:
            self.failed.emit(str(exc))


class GPUTab(QWidget):
    def __init__(self, initial_data=None):
        super().__init__()
        self._refresh_thread = None
        self._refresh_worker = None
        self.layout_base = QVBoxLayout(self)
        self.layout_base.setContentsMargins(12, 8, 12, 8)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.content = QWidget()
        self.container = QVBoxLayout(self.content)
        self.container.setContentsMargins(0, 0, 0, 0)
        self.container.setSpacing(8)
        self.container.addStretch()
        self.scroll.setWidget(self.content)
        self.layout_base.addWidget(self.scroll)
        if initial_data is None:
            self.container.addWidget(QLabel("A recolher informação das placas gráficas..."))
            self.update_data()
        else:
            self.update_data(initial_data)

    def update_data(self, gpus=None):
        if gpus is None:
            if self._refresh_thread is not None and self._refresh_thread.isRunning():
                return

            self._refresh_thread = QThread(self)
            worker = GPUDataWorker()
            self._refresh_worker = worker
            worker.moveToThread(self._refresh_thread)
            self._refresh_thread.started.connect(worker.run)
            worker.finished.connect(self._display_data)
            worker.failed.connect(self._display_error)
            worker.finished.connect(self._refresh_thread.quit)
            worker.finished.connect(worker.deleteLater)
            worker.failed.connect(self._refresh_thread.quit)
            worker.failed.connect(worker.deleteLater)
            self._refresh_thread.finished.connect(self._refresh_finished)
            self._refresh_thread.finished.connect(self._refresh_thread.deleteLater)
            self._refresh_thread.start()
            return

        self._display_data(gpus)

    def _refresh_finished(self):
        self._refresh_thread = None
        self._refresh_worker = None

    def _display_error(self, message):
        self._display_data([])
        self.container.addWidget(QLabel(f"Não foi possível ler a GPU: {message}"))

    def _display_data(self, gpus):
        # Limpar widgets antigos
        while self.container.count():
            item = self.container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not gpus:
            self.container.addWidget(QLabel("Nenhuma placa de vídeo detetada."))
            return

        for gpu in gpus:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame { 
                    background-color: #333; 
                    border: 1px solid #444; 
                    border-radius: 12px; 
                    padding: 10px; 
                    margin-bottom: 10px;
                }
            """)
            flayout = QVBoxLayout(frame)
            flayout.setContentsMargins(12, 8, 12, 8)
            flayout.setSpacing(4)

            titulo = QLabel(gpu.get('name', 'GPU'))
            titulo.setStyleSheet("font-weight: bold; color: #2a82da; font-size: 15px; border: none;")
            
            tipo = QLabel(f"Fabricante/Série: {gpu['type']}")
            tipo.setStyleSheet("color: #aaa; border: none;")

            driver = QLabel(f"Driver: {gpu.get('driver_version', 'N/D')}")
            driver.setStyleSheet("color: #bbb; border: none;")

            load = gpu.get('load', 'N/D')
            load_text = f"{load}%" if load != 'N/D' else 'N/D'
            stats = QLabel(
                f"Carga: {load_text} | Temp: {gpu.get('temp', 'N/D')} | "
                f"VRAM livre: {gpu.get('vram_free', 'N/D')} | Ventoinha: {gpu.get('fan_speed', 'N/D')}"
            )
            stats.setWordWrap(True)
            stats.setStyleSheet("color: #eee; font-size: 13px; border: none;")

            vram = QLabel(
                f"VRAM: {gpu.get('vram_used', 'N/D')} / {gpu.get('vram_total', 'N/D')} | "
                f"UUID: {gpu.get('uuid', 'N/D')}"
            )
            vram.setWordWrap(True)
            vram.setStyleSheet("color: #bbb; border: none;")

            resolution = QLabel(f"Resolução: {gpu.get('resolution', 'N/D')}")
            resolution.setWordWrap(True)
            resolution.setStyleSheet("color: #bbb; border: none;")

            advanced = QLabel(
                f"Energia: {gpu.get('power_draw', 'N/D')} / {gpu.get('power_limit', 'N/D')} | "
                f"Clock GPU: {gpu.get('clock_graphics', 'N/D')} | Clock memória: {gpu.get('clock_memory', 'N/D')}"
            )
            advanced.setWordWrap(True)
            advanced.setStyleSheet("color: #999; border: none;")

            flayout.addWidget(titulo)
            flayout.addWidget(tipo)
            flayout.addWidget(driver)
            flayout.addWidget(stats)
            flayout.addWidget(vram)
            flayout.addWidget(resolution)
            flayout.addWidget(advanced)
            
            self.container.addWidget(frame)