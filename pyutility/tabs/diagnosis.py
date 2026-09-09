from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from diagnostics import (
    DiagnosticEngine,
    HistoryStore,
    SystemSnapshotCollector,
)
from tabs.async_utils import start_background
from tabs.i18n import translate_text


class DiagnosisTab(QWidget):
    def __init__(self):
        super().__init__()
        self.collector = SystemSnapshotCollector()
        self.history = HistoryStore()
        self.engine = DiagnosticEngine()
        self.snapshot = None
        self.analysis = {}
        self.baseline = None
        self.language = "pt"

        layout = QVBoxLayout(self)
        title = QLabel("Diagnóstico inteligente")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2a82da;")
        layout.addWidget(title)
        self.status = QLabel("A recolher o estado do computador...")
        layout.addWidget(self.status)

        overview = QHBoxLayout()
        score_box = QGroupBox("Saúde do PC")
        score_layout = QVBoxLayout(score_box)
        self.score = QLabel("--/100")
        self.score.setStyleSheet("font-size: 28px; font-weight: bold; color: #58a6d8;")
        self.score_detail = QLabel("Sem dados")
        score_layout.addWidget(self.score)
        score_layout.addWidget(self.score_detail)
        overview.addWidget(score_box, 1)

        metrics_box = QGroupBox("Medição atual")
        metrics_layout = QGridLayout(metrics_box)
        self.cpu = QLabel("CPU: N/D")
        self.memory = QLabel("RAM: N/D")
        self.disk = QLabel("Disco: N/D")
        self.temperature = QLabel("Temperatura: Informação não disponível")
        for row, label in enumerate((self.cpu, self.memory, self.disk, self.temperature)):
            metrics_layout.addWidget(label, row, 0)
        overview.addWidget(metrics_box, 2)
        layout.addLayout(overview)

        actions = QHBoxLayout()
        refresh = QPushButton("Atualizar diagnóstico")
        refresh.clicked.connect(self.update_data)
        self.baseline_button = QPushButton("Guardar estado antes da manutenção")
        self.baseline_button.clicked.connect(self.save_baseline)
        self.compare_button = QPushButton("Comparar com estado atual")
        self.compare_button.clicked.connect(self.compare_baseline)
        actions.addWidget(refresh)
        actions.addWidget(self.baseline_button)
        actions.addWidget(self.compare_button)
        layout.addLayout(actions)

        self.findings = QTextEdit()
        self.findings.setReadOnly(True)
        self.findings.setPlaceholderText("Os problemas encontrados aparecerão aqui.")
        layout.addWidget(self.findings, 1)

        self.process_table = QTableWidget(0, 4)
        self.process_table.setHorizontalHeaderLabels(["Processo", "CPU %", "RAM %", "Avaliação"])
        self.process_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(QLabel("Processos relevantes"))
        layout.addWidget(self.process_table, 1)

        self.trends = QLabel("Tendências: ainda sem dados suficientes.")
        self.trends.setWordWrap(True)
        layout.addWidget(self.trends)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(15000)
        self.update_data()

    def update_data(self):
        start_background(self, self._collect_and_analyze, self._display_data, self._show_error)

    def set_language(self, language):
        self.language = language
        if self.snapshot:
            self._display_data((self.snapshot, self.analysis))

    def _translate(self, text):
        return translate_text(text, self.language)

    def _collect_and_analyze(self):
        snapshot = self.collector.collect()
        samples = self.history.append(snapshot)
        analysis = self.engine.analyze(snapshot, samples)
        return snapshot, analysis

    def _show_error(self, message):
        self.status.setText(self._translate(f"Diagnóstico indisponível: {message}"))

    def _display_data(self, result):
        self.snapshot, self.analysis = result
        score = self.analysis.get("score", 0)
        breakdown = self.analysis.get("breakdown", {})
        self.score.setText(f"{score}/100")
        self.score_detail.setText(self._translate(" | ".join(f"{name}: {value}/20" for name, value in breakdown.items() if value is not None)))
        self.status.setText(self._translate("Atualizado; as conclusões são regras locais e podem indicar, mas não provam, uma falha."))
        self.cpu.setText(self._translate(f"CPU: {self.snapshot.get('cpu_percent', 0):.1f}%"))
        self.memory.setText(self._translate(f"RAM: {self.snapshot.get('memory_percent', 0):.1f}% ({self.snapshot.get('memory_available_gb', 0):.1f} GB disponíveis)"))
        disks = self.snapshot.get("disks", [])
        self.disk.setText(self._translate("Disco: " + (", ".join(f"{item['mountpoint']} {item['percent']:.0f}%" for item in disks) or "Informação não disponível")))
        temperatures = self.snapshot.get("temperatures", [])
        self.temperature.setText(self._translate("Temperatura: " + (", ".join(f"{item['sensor']} {item['current']:.1f}°C" for item in temperatures) or "Informação não disponível")))
        self._display_findings()
        self._display_processes()
        self._display_trends()

    def _display_findings(self):
        findings = self.analysis.get("findings", [])
        alerts = self.analysis.get("alerts", [])
        lines = ["ALERTAS NOVOS (com cooldown):"] + [f"- {item['title']}: {item['detail']} Recomendação: {item['recommendation']}" for item in alerts]
        lines.append("\nPROBLEMAS E RECOMENDAÇÕES:")
        lines.extend(f"- [{item['severity']}] {item['title']}: {item['detail']} {item['recommendation']}" for item in findings)
        self.findings.setPlainText(self._translate("\n".join(lines) if findings else "Não foram encontrados problemas evidentes nos dados atuais."))

    def _display_processes(self):
        processes = (self.snapshot or {}).get("processes", [])[:15]
        self.process_table.setRowCount(len(processes))
        for row, process in enumerate(processes):
            cpu = process.get("cpu_percent", 0)
            memory = process.get("memory_percent", 0)
            assessment = "Normal"
            if cpu >= 90 or memory >= 25:
                assessment = "Necessita de atenção"
            elif cpu >= 60 or memory >= 12:
                assessment = "Elevado consumo"
            values = (process.get("name", "Desconhecido"), f"{cpu:.1f}", f"{memory:.1f}", self._translate(assessment))
            for column, value in enumerate(values):
                self.process_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _display_trends(self):
        trend = self.analysis.get("trend", {})
        if not trend.get("sufficient"):
            self.trends.setText(self._translate(f"Tendências: {trend.get('message', 'Informação não disponível')}"))
            return
        self.trends.setText(self._translate(
            f"Tendências: {trend['message']} CPU: {trend.get('cpu', 0):+.1f} pontos; "
            f"RAM: {trend.get('memory', 0):+.1f} pontos."
        ))

    def save_baseline(self):
        if self.snapshot:
            self.baseline = self.snapshot
            self.status.setText(self._translate("Estado antes da manutenção guardado. Execute uma manutenção e compare depois."))

    def compare_baseline(self):
        if not self.baseline or not self.snapshot:
            self.status.setText(self._translate("Guarde primeiro um estado antes da manutenção."))
            return
        before = self.baseline
        after = self.snapshot
        comparisons = []
        for label, key in (("CPU", "cpu_percent"), ("RAM", "memory_percent")):
            old = before.get(key)
            new = after.get(key)
            if old is not None and new is not None:
                change = ((new - old) / old * 100) if old else 0
                comparisons.append(f"{label}: {old:.1f}% -> {new:.1f}% ({change:+.1f}%)")
        self.findings.append(self._translate("\nCOMPARAÇÃO ANTES/DEPOIS:\n" + ("\n".join(comparisons) or "Informação não disponível")))

