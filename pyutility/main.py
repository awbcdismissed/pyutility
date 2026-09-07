import os
import sys
import ctypes
import time
import requests
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QSplashScreen,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QTimer, Qt, QEvent
from PyQt6.QtGui import QPalette, QColor, QPixmap, QGuiApplication

from tabs.dashboard import DashboardTab
from tabs.cpu import CPUTab
from tabs.gpu import GPUTab
from tabs.processes import ProcessTab
from tabs.history import HistoryTab
from tabs.speedtest import SpeedTesterTab
from tabs.mic import MicTab
from tabs.install import InstallTab
from tabs.system import SystemTab
from tabs.wifi import WifiTab
from tabs.startup import StartupTab
from tabs.security import SecurityTab
from tabs.backup import BackupTab
from tabs.logs import LogsTab
from tabs.drivers import DriversTab
from tabs.devices import DevicesTab
from tabs.i18n import LANGUAGES, translate_text, translate_widget_tree
from tabs.animations import AnimationController

LOGO_URL = "https://i.postimg.cc/dQNsp0tf/PAP-Logo.jpg"


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin():
    if os.name != "nt":
        return

    if is_admin():
        return

    script = os.path.abspath(sys.argv[0])
    params = " ".join(f'"{arg}"' if " " in arg else arg for arg in sys.argv[1:])
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    launcher = pyw if os.path.exists(pyw) else sys.executable

    try:
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            launcher,
            f'"{script}" {params}'.strip(),
            None,
            1,
        )
    except Exception as exc:
        print(f"[ERROR] Failed to relaunch with admin privileges: {exc}")
    raise SystemExit(0)


def build_blank_logo(size=600):
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(30, 30, 30))
    return pixmap


def load_logo_from_url(size=600):
    last_error = None
    for _ in range(5):
        try:
            response = requests.get(LOGO_URL, timeout=8)
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}"
                continue
            image = QPixmap()
            if image.loadFromData(response.content):
                return image.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            last_error = "The URL did not return a valid image"
        except requests.RequestException as exc:
            last_error = str(exc)
    raise RuntimeError(f"Could not load the application logo from {LOGO_URL}: {last_error}")


def create_splash_screen(pixmap):
    splash = QSplashScreen(pixmap)
    splash.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
    splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

    splash.setGeometry(
        QGuiApplication.primaryScreen().availableGeometry().center().x() - 300,
        QGuiApplication.primaryScreen().availableGeometry().center().y() - 300,
        600,
        600,
    )

    opacity = splash.graphicsEffect()
    if opacity is None:
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        opacity = QGraphicsOpacityEffect(splash)
        splash.setGraphicsEffect(opacity)

    opacity.setOpacity(0.0)
    splash.show()

    fade_timer = QTimer(splash)
    fade_timer.setSingleShot(False)
    fade_timer.timeout.connect(lambda: None)

    opacity_value = 0.0
    step = 0.08
    direction = 1

    def animate():
        nonlocal opacity_value, direction
        opacity_value += step * direction
        if opacity_value >= 1.0:
            opacity_value = 1.0
            direction = -1
        elif opacity_value <= 0.0:
            opacity_value = 0.0
            direction = 1
        opacity.setOpacity(opacity_value)

    fade_timer.timeout.connect(animate)
    fade_timer.start(25)

    splash._fade_timer = fade_timer
    splash._fade_direction = direction
    splash._fade_step = step
    splash._fade_opacity = opacity_value
    return splash


class ModernMonitorApp(QMainWindow):
    def __init__(self, initial_gpu_data=None):
        super().__init__()
        self.motion = AnimationController(QApplication.instance())
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle("PyUtility")
        self.setMinimumSize(900, 600)

        self.statusBar().showMessage("Feito por Martim Oliveira 12ºGEI - 2026")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        layout.addWidget(self.tabs)

        # Criar abas
        self.tab_dashboard = DashboardTab()
        self.tab_dashboard.theme_changed.connect(self.change_theme)
        self.tab_dashboard.language_changed.connect(self.change_language)
        self.tab_cpu = CPUTab()
        self.tab_gpu = GPUTab(initial_gpu_data)
        self.tab_processes = ProcessTab()
        self.tab_speedtest = SpeedTesterTab()
        self.tab_mic = MicTab()
        self.tab_install = InstallTab()
        self.tab_system = SystemTab()
        self.tab_wifi = WifiTab()
        self.tab_startup = StartupTab()
        self.tab_security = SecurityTab()
        self.tab_backup = BackupTab()
        self.tab_logs = LogsTab()
        self.tab_drivers = DriversTab()
        self.tab_devices = DevicesTab()
        self.tab_history = HistoryTab()

        # Adicionar abas
        self.tabs.addTab(self.tab_dashboard, "Início")
        self.tabs.addTab(self.tab_cpu, "CPU")
        self.tabs.addTab(self.tab_gpu, "GPU")
        self.tabs.addTab(self.tab_processes, "Processos")
        self.tabs.addTab(self.tab_history, "Histórico")
        self.tabs.addTab(self.tab_speedtest, "Teste de velocidade")
        self.tabs.addTab(self.tab_mic, "Manutenção")
        self.tabs.addTab(self.tab_install, "Instalar")
        self.tabs.addTab(self.tab_system, "Sistema")
        self.tabs.addTab(self.tab_wifi, "Wi-Fi")
        self.tabs.addTab(self.tab_startup, "Arranque")
        self.tabs.addTab(self.tab_security, "Segurança")
        self.tabs.addTab(self.tab_backup, "Cópias de segurança")
        self.tabs.addTab(self.tab_logs, "Registos")
        self.tabs.addTab(self.tab_drivers, "Controladores")
        self.tabs.addTab(self.tab_devices, "Dispositivos")
        self.current_language = "pt"
        self.tabs.currentChanged.connect(lambda index: self.motion.animate_tab(self.tabs, index))
        QTimer.singleShot(0, lambda: self.motion.animate_tab(self.tabs, self.tabs.currentIndex()))

        self.preload_tab_data()

        # Refresh Timer (2s)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_active_tab)
        self.timer.start(2000)

    def preload_tab_data(self):
        for tab in (
            self.tab_dashboard,
            self.tab_cpu,
            self.tab_processes,
            self.tab_history,
            self.tab_speedtest,
            self.tab_mic,
            self.tab_install,
            self.tab_system,
            self.tab_wifi,
            self.tab_startup,
            self.tab_security,
            self.tab_backup,
            self.tab_logs,
            self.tab_drivers,
            self.tab_devices,
        ):
            try:
                tab.update_data()
            except Exception:
                pass

    def refresh_active_tab(self):
        idx = self.tabs.currentIndex()
        map_tabs = {
            0: self.tab_dashboard, 1: self.tab_cpu, 2: self.tab_gpu,
            3: self.tab_processes, 4: self.tab_history, 5: self.tab_speedtest,
            6: self.tab_mic, 7: self.tab_install, 8: self.tab_system,
            9: self.tab_wifi, 10: self.tab_startup, 11: self.tab_security,
            12: self.tab_backup, 13: self.tab_logs, 14: self.tab_drivers,
            15: self.tab_devices
        }
        if idx in map_tabs:
            map_tabs[idx].update_data()

    def change_theme(self, theme):
        if theme in ("Tema claro", "Light theme"):
            self.setStyleSheet("""
                QWidget { background: #f4f6f8; color: #202124; }
                QTabWidget::pane, QFrame#homeCard { background: #ffffff; border: 1px solid #d8dee5; }
                QTabWidget::pane { border: none; }
                QTabBar { margin-top: 10px; }
                QLineEdit, QComboBox, QTableWidget, QTextEdit { background: white; color: #202124; border: 1px solid #c5ccd4; }
                QPushButton { background: #e7edf3; color: #202124; border: 1px solid #c5ccd4; }
                QPushButton:hover { background: #d5e3ef; }
                QTabBar::tab { background: #e7edf3; color: #45515d; }
                QTabBar::tab:selected { background: #2878bd; color: white; }
                QLabel#homeTitle { color: #1769aa; }
                QLabel#homeSubtitle, QLabel#dateLabel { color: #687582; }
            """)
        else:
            self.setStyleSheet("""
                QWidget { background: #282828; color: white; }
                QTabWidget::pane, QFrame#homeCard { background: #202428; border: 1px solid #454d55; }
                QTabWidget::pane { border: none; }
                QTabBar { margin-top: 10px; }
                QLineEdit, QComboBox, QTableWidget, QTextEdit { background: #191919; color: white; border: 1px solid #46515b; }
                QPushButton { background: #303840; color: #f1f5f8; border: 1px solid #4c5965; }
                QPushButton:hover { background: #3d5263; }
                QTabBar::tab { background: #30363d; color: #b9c4cf; }
                QTabBar::tab:selected { background: #2878bd; color: white; }
                QLabel#homeTitle { color: #58a6d8; }
                QLabel#homeSubtitle, QLabel#dateLabel { color: #9daab5; }
            """)

    def change_language(self, language):
        if language not in LANGUAGES:
            return
        self.current_language = language
        translate_widget_tree(self, language)
        for index in range(self.tabs.count()):
            self.tabs.setTabText(index, translate_text(self.tabs.tabText(index), language))
        self.statusBar().showMessage(translate_text(
            "Feito por Martim Oliveira 12ºGEI - 2026", language
        ))


def apply_dark_theme(app):
    app.setStyle("Fusion")
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window, QColor(40, 40, 40))
    p.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    p.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
    p.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    p.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    app.setPalette(p)
    app.setStyleSheet("""
        QWidget { font-size: 13px; }
        QTabWidget::pane { border: 1px solid #454d55; border-radius: 6px; background: #202428; }
        QTabWidget::pane { border: none; }
        QTabBar { margin-top: 10px; }
        QTabBar::tab { padding: 9px 16px; margin-right: 3px; color: #b9c4cf; background: #30363d; border: 0; border-radius: 5px; }
        QTabBar::tab:selected { color: white; background: #2878bd; }
        QTabBar::tab:hover { background: #3d4852; }
        QPushButton { padding: 7px 12px; border: 1px solid #4c5965; border-radius: 5px; background: #303840; color: #f1f5f8; }
        QPushButton:hover { background: #3d5263; }
        QPushButton:disabled { color: #7d8790; }
        QLineEdit, QComboBox, QTableWidget, QTextEdit { border: 1px solid #46515b; border-radius: 5px; padding: 5px; }
        QHeaderView::section { padding: 6px; background: #303840; color: #dbe5ed; border: 0; }
        QProgressBar { border: 1px solid #46515b; border-radius: 5px; text-align: center; height: 18px; }
        QProgressBar::chunk { background: #2878bd; border-radius: 4px; }
        QFrame#homeCard { border: 1px solid #454d55; border-radius: 8px; background: #202428; }
        QLabel#homeTitle { color: #58a6d8; font-size: 28px; font-weight: 700; }
        QLabel#homeSubtitle { color: #9daab5; font-size: 14px; }
        QLabel#clockLabel { color: #f1f5f8; font-size: 52px; font-weight: 700; }
        QLabel#dateLabel { color: #9daab5; font-size: 15px; }
        QTextEdit { padding: 8px; }
    """)


if __name__ == "__main__":
    ensure_admin()

    app = QApplication(sys.argv)
    apply_dark_theme(app)

    splash = create_splash_screen(load_logo_from_url())
    splash.show()
    app.processEvents()
    window = ModernMonitorApp()

    def close_splash():
        effect = splash.graphicsEffect()
        if effect is not None:
            current = effect.opacity()
            target = 0.0
            step = 0.10

            def fade_out():
                nonlocal current
                current -= step
                if current <= target:
                    effect.setOpacity(target)
                    splash.close()
                    window.showMaximized()
                    return
                effect.setOpacity(current)
                QTimer.singleShot(25, fade_out)

            effect.setOpacity(1.0)
            QTimer.singleShot(25, fade_out)
        else:
            splash.close()
            window.showMaximized()

    startup_started = time.monotonic()

    def initial_data_ready():
        tabs = (
            window.tab_dashboard,
            window.tab_cpu,
            window.tab_gpu,
            window.tab_processes,
            window.tab_history,
            window.tab_system,
            window.tab_wifi,
            window.tab_startup,
            window.tab_security,
            window.tab_drivers,
            window.tab_devices,
        )
        active_threads = []
        for tab in tabs:
            for attribute in ("_async_thread", "_refresh_thread"):
                thread = getattr(tab, attribute, None)
                if thread is not None and thread.isRunning():
                    active_threads.append(thread)
        timed_out = time.monotonic() - startup_started >= 9.0
        if not active_threads or timed_out:
            close_splash()
            return
        QTimer.singleShot(50, initial_data_ready)

    QTimer.singleShot(0, initial_data_ready)

    sys.exit(app.exec())