from PyQt6.QtCore import QDateTime, QTimer, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout, QWidget
from backend import SystemMonitor
from tabs.async_utils import start_background

class DashboardTab(QWidget):
    theme_changed = pyqtSignal(str)
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("PyUtility")
        title.setObjectName("homeTitle")
        subtitle = QLabel("PAP 2026 - Martim Oliveira 12ºGEI")
        subtitle.setObjectName("homeSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        header.addWidget(QLabel("Tema:"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Tema escuro", "Tema claro"])
        self.theme_selector.currentTextChanged.connect(self.theme_changed)
        header.addWidget(self.theme_selector)
        header.addWidget(QLabel("Idioma:"))
        self.language_selector = QComboBox()
        self.language_selector.setObjectName("languageSelector")
        self.language_selector.addItem("Português", "pt")
        self.language_selector.addItem("English", "en")
        self.language_selector.currentIndexChanged.connect(
            lambda index: self.language_changed.emit(self.language_selector.itemData(index))
        )
        header.addWidget(self.language_selector)
        layout.addLayout(header)

        content = QHBoxLayout()
        content.setSpacing(18)
        clock_frame = QFrame()
        clock_frame.setObjectName("homeCard")
        clock_layout = QVBoxLayout(clock_frame)
        self.clock = QLabel()
        self.clock.setObjectName("clockLabel")
        self.date = QLabel()
        self.date.setObjectName("dateLabel")
        self.lbl_os = QLabel("Sistema: -")
        self.lbl_host = QLabel("Computador: -")
        clock_layout.addStretch()
        clock_layout.addWidget(self.clock)
        clock_layout.addWidget(self.date)
        clock_layout.addSpacing(18)
        clock_layout.addWidget(self.lbl_os)
        clock_layout.addWidget(self.lbl_host)
        clock_layout.addStretch()
        content.addWidget(clock_frame, 1)

        description_frame = QFrame()
        description_frame.setObjectName("homeCard")
        description_layout = QVBoxLayout(description_frame)
        description_layout.addWidget(QLabel("Sobre o programa"))
        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setPlainText(
            "O PyUtility acompanha o estado do computador num só lugar. "
            "Explore as abas para consultar componentes, segurança, "
            "processos e ferramentas de manutenção."
        )
        description_layout.addWidget(self.description)
        content.addWidget(description_frame, 1)
        layout.addLayout(content)
        layout.addStretch()

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

    def update_data(self):
        start_background(self, SystemMonitor.get_dashboard_info, self._display_data)

    def _display_data(self, d):
        self.lbl_os.setText(f"Sistema: {d.get('os', 'N/D')}")
        self.lbl_host.setText(f"Computador: {d.get('hostname', 'N/D')}")

    def update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock.setText(now.toString("HH:mm:ss"))
        self.date.setText(now.toString("dddd, dd 'de' MMMM 'de' yyyy"))