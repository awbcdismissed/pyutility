import ctypes
import os
import sys
import time
import traceback

from PyQt6.QtCore import QPoint, QTimer, Qt
from PyQt6.QtWidgets import QApplication, QInputDialog, QLabel, QMainWindow, QMessageBox, QProgressBar, QVBoxLayout, QWidget


def _write_startup_log(message):
    log_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.getcwd()), "PyUtility")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "startup_debug.log")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(message)
        if not message.endswith("\n"):
            log_file.write("\n")
    return log_path

from gui.core.functions import Functions
from gui.core.json_settings import Settings
from gui.uis.windows.main_window.functions_main_window import MainFunctions
from gui.uis.windows.main_window.setup_main_window import SetupMainWindow
from gui.uis.windows.main_window.ui_main import UI_MainWindow
from backend import SystemMonitor
from diagnostics import DiagnosticEngine, HistoryStore, SystemSnapshotCollector
from tabs.backup import BackupTab
from tabs.cpu import CPUTab
from tabs.dashboard import DashboardTab
from tabs.devices import DevicesTab
from tabs.diagnosis import DiagnosisTab
from tabs.drivers import DriversTab
from tabs.gpu import GPUTab
from tabs.i18n import LANGUAGES, translate_text, translate_widget_tree
from tabs.install import InstallTab
from tabs.logs import LogsTab
from tabs.mic import MicTab
from tabs.network import NetworkTab
from tabs.processes import ProcessTab
from tabs.security import SecurityTab
from tabs.startup import StartupTab
from tabs.system import SystemTab
from tabs.wifi import WifiTab


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def ensure_admin():
    if os.name != "nt" or is_admin():
        return
    script = os.path.abspath(sys.argv[0])
    params = " ".join(f'"{arg}"' if " " in arg else arg for arg in sys.argv[1:])
    launcher = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(launcher):
        launcher = sys.executable
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", launcher, f'"{script}" {params}'.strip(), None, 1
    )
    raise SystemExit(0)


def preload_initial_data(progress_callback=None):
    initial_data = {}
    collectors = {
        "cpu": SystemMonitor.get_cpu_detailed_info,
        "gpu": SystemMonitor.get_gpu_detailed_info,
        "system": SystemMonitor.get_system_health_info,
        "drivers": SystemMonitor.get_driver_info,
    }
    total_steps = len(collectors) + 2
    step = 0

    for key, collector in collectors.items():
        step += 1
        if progress_callback:
            progress_callback(step, total_steps, f"A carregar {key.upper()}...")
        try:
            initial_data[key] = collector()
        except Exception:
            trace = traceback.format_exc()
            _write_startup_log(f"[{key}] startup collector failed:\n{trace}")
            print(f"[PyUtility] startup collector failed for {key}:\n{trace}", file=sys.stderr)
            initial_data[key] = None

    if progress_callback:
        progress_callback(step + 1, total_steps, "A gerar diagnóstico inicial...")
    try:
        collector = SystemSnapshotCollector()
        snapshot = collector.collect()
        history = HistoryStore()
        samples = history.append(snapshot)
        analysis = DiagnosticEngine().analyze(snapshot, samples)
        initial_data["diagnosis"] = (snapshot, analysis)
    except Exception:
        trace = traceback.format_exc()
        _write_startup_log(f"[diagnosis] startup collector failed:\n{trace}")
        print(f"[PyUtility] startup diagnosis failed:\n{trace}", file=sys.stderr)
        initial_data["diagnosis"] = None

    if progress_callback:
        progress_callback(total_steps, total_steps, "A preparar a aplicação...")
    return initial_data


class StartupSplash(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(420, 150)

        container = QWidget(self)
        container.setObjectName("splash_container")
        container.setStyleSheet(
            """
            QWidget#splash_container {
                background: #101827;
                border: 1px solid #2d3748;
                border-radius: 14px;
            }
            QLabel { color: #e5e7eb; }
            QProgressBar {
                border: 1px solid #374151;
                border-radius: 8px;
                background: #111827;
                color: #f8fafc;
                text-align: center;
                min-height: 18px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #8b5cf6);
                border-radius: 7px;
            }
            """
        )

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("PyUtility")
        title.setStyleSheet("font-size: 22px; font-weight: 700; letter-spacing: 1px;")
        subtitle = QLabel("A iniciar o sistema...")
        subtitle.setStyleSheet("font-size: 11px; color: #9ca3af;")
        self.status_label = QLabel("A preparar a aplicação...")
        self.status_label.setStyleSheet("font-size: 12px; color: #d1d5db;")
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(container)

    def set_status(self, text, value):
        self.status_label.setText(text)
        self.progress.setValue(value)
        self.repaint()
        QApplication.processEvents()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self.move(
            geometry.center().x() - self.width() // 2,
            geometry.center().y() - self.height() // 2,
        )

    def finish(self, window=None):
        self.hide()
        if window is not None and hasattr(window, "show"):
            try:
                window.show()
            except Exception:
                pass
        QApplication.processEvents()


class ModernMonitorApp(QMainWindow):
    menu_items = [
        ("icon_send.svg", "btn_home", "Início"),
        ("icon_send.svg", "btn_cpu", "CPU"),
        ("icon_send.svg", "btn_gpu", "GPU"),
        ("icon_send.svg", "btn_processes", "Processos"),
        ("icon_send.svg", "btn_maintenance", "Manutenção"),
        ("icon_send.svg", "btn_install", "Instalar"),
        ("icon_send.svg", "btn_system", "Sistema"),
        ("icon_send.svg", "btn_network", "Rede"),
        ("icon_send.svg", "btn_wifi", "Wi-Fi"),
        ("icon_send.svg", "btn_startup", "Arranque"),
        ("icon_send.svg", "btn_security", "Segurança"),
        ("icon_send.svg", "btn_backup", "Cópias de segurança"),
        ("icon_send.svg", "btn_logs", "Registos"),
        ("icon_send.svg", "btn_drivers", "Controladores"),
        ("icon_send.svg", "btn_devices", "Dispositivos"),
        ("icon_send.svg", "btn_diagnosis", "Diagnóstico"),
    ]

    def __init__(self, initial_data=None):
        super().__init__()
        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)
        self.settings = Settings().items
        self.hide_grips = True
        self.skip_examples = True
        self.dragPos = QPoint()
        SetupMainWindow.add_left_menus = [
            {
                "btn_icon": icon,
                "btn_id": object_name,
                "btn_text": text,
                "btn_tooltip": text,
                "show_top": True,
                "is_active": index == 0,
            }
            for index, (icon, object_name, text) in enumerate(self.menu_items)
        ] + [
            {"btn_icon": "icon_info.svg", "btn_id": "btn_info", "btn_text": "Informação", "btn_tooltip": "Informação", "show_top": False, "is_active": False},
            {"btn_icon": "icon_settings.svg", "btn_id": "btn_settings", "btn_text": "Definições", "btn_tooltip": "Definições", "show_top": False, "is_active": False},
        ]
        SetupMainWindow.setup_gui(self)
        self._build_monitor_pages(initial_data or {})
        self.current_language = "pt"
        self.show_status("Estado: pronto")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_active_tab)
        self.ui.load_pages.pages.currentChanged.connect(self._page_changed)
        self._last_page_refresh = {}
        self._page_refresh_request = None
        self._page_refresh_timer = QTimer(self)
        self._page_refresh_timer.setSingleShot(True)
        self._page_refresh_timer.setInterval(120)
        self._page_refresh_timer.timeout.connect(self._refresh_requested_page)
        self._page_changed(self.ui.load_pages.pages.currentIndex())

    def _build_monitor_pages(self, initial_data):
        self.tab_dashboard = DashboardTab()
        self.tab_dashboard.language_changed.connect(self.change_language)
        self.tab_cpu = CPUTab(initial_data.get("cpu"))
        self.tab_gpu = GPUTab(initial_data.get("gpu"))
        self.tab_processes = ProcessTab()
        self.tab_mic = MicTab()
        self.tab_install = InstallTab()
        self.tab_system = SystemTab(initial_data.get("system"))
        self.tab_network = NetworkTab()
        self.tab_wifi = WifiTab()
        self.tab_startup = StartupTab()
        self.tab_security = SecurityTab()
        self.tab_backup = BackupTab()
        self.tab_logs = LogsTab()
        self.tab_drivers = DriversTab(initial_data.get("drivers"))
        self.tab_devices = DevicesTab()
        self.tab_diagnosis = DiagnosisTab(initial_data.get("diagnosis"))
        self.monitor_pages = [
            self.tab_dashboard, self.tab_cpu, self.tab_gpu, self.tab_processes,
            self.tab_mic, self.tab_install, self.tab_system, self.tab_network,
            self.tab_wifi, self.tab_startup, self.tab_security, self.tab_backup,
            self.tab_logs, self.tab_drivers, self.tab_devices, self.tab_diagnosis,
        ]
        pages = self.ui.load_pages.pages
        while pages.count():
            pages.removeWidget(pages.widget(0))
        for page in self.monitor_pages:
            pages.addWidget(page)
        pages.setCurrentWidget(self.tab_dashboard)

    def _page_changed(self, index):
        intervals = {
            self.tab_dashboard: 2000,
            self.tab_cpu: 5000,
            self.tab_gpu: 5000,
            self.tab_processes: 3000,
            self.tab_system: 10000,
            self.tab_network: 10000,
            self.tab_wifi: 10000,
            self.tab_security: 15000,
            self.tab_diagnosis: 30000,
        }
        current = self.ui.load_pages.pages.widget(index)
        self._last_page_refresh[current] = 0.0
        self.timer.setInterval(intervals.get(current, 0))
        if self.timer.interval() > 0:
            self.timer.start()
        else:
            self.timer.stop()
        # Let QStackedWidget finish the visual switch before starting a collector.
        # Repeated tab switching then coalesces into one refresh request.
        self._page_refresh_request = current
        self._page_refresh_timer.start()

    def _refresh_requested_page(self):
        current = self.ui.load_pages.pages.currentWidget()
        if current is not self._page_refresh_request:
            return
        update_data = getattr(current, "update_data", None)
        if not callable(update_data):
            return
        now = time.monotonic()
        last_refresh = self._last_page_refresh.get(current, 0.0)
        if now - last_refresh < max(self.timer.interval() / 1000, 1.0):
            return
        self._last_page_refresh[current] = now
        update_data()

    def _open_special_panel(self, object_name):
        self.ui.left_menu.select_only_one_tab(object_name)
        if not MainFunctions.left_column_is_visible(self):
            MainFunctions.toggle_left_column(self)
        menu = self.ui.left_column.menus.menu_2 if object_name == "btn_info" else self.ui.left_column.menus.menu_1
        title = "Informação" if object_name == "btn_info" else "Definições"
        icon_path = Functions.set_svg_icon("icon_info.svg") if object_name == "btn_info" else Functions.set_svg_icon("icon_settings.svg")
        MainFunctions.set_left_column_menu(self, menu, title, icon_path)

    def _search_page(self, query):
        normalized = query.strip().lower()
        if not normalized:
            return

        if normalized in {"info", "informacao", "informação"}:
            self._open_special_panel("btn_info")
            return

        if normalized in {"settings", "definicoes", "definições", "configuracao", "configuração"}:
            self._open_special_panel("btn_settings")
            return

        for index, (_, object_name, label) in enumerate(self.menu_items):
            if normalized in object_name.lower() or normalized in label.lower():
                self.ui.left_menu.select_only_one(object_name)
                MainFunctions.set_page(self, self.monitor_pages[index])
                return

        self.show_status(f"Página não encontrada para: {query}")

    def btn_clicked(self, button=None):
        button = button or SetupMainWindow.setup_btns(self)
        if button is None:
            return
        object_name = button.objectName()
        page_names = [name for _, name, _ in self.menu_items]
        if object_name in page_names:
            index = page_names.index(object_name)
            self.ui.left_menu.select_only_one(object_name)
            MainFunctions.set_page(self, self.monitor_pages[index])
            return
        if object_name == "btn_close_left_column":
            self.ui.left_menu.deselect_all_tab()
            if MainFunctions.left_column_is_visible(self):
                MainFunctions.toggle_left_column(self)
            return
        if object_name in ("btn_info", "btn_settings"):
            self._open_special_panel(object_name)
            return
        if object_name == "btn_top_settings":
            self._open_special_panel("btn_settings")
            return
        if object_name == "btn_search":
            search_text, ok = QInputDialog.getText(
                self,
                "Pesquisar",
                "Digite o nome de uma página ou item:",
                text=""
            )
            if ok:
                self._search_page(search_text)
            return

    def btn_released(self):
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()
        event.accept()

    def resizeEvent(self, event):
        SetupMainWindow.resize_grips(self)
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.timer.stop()
        self._page_refresh_timer.stop()

        def stop_thread(thread):
            if thread is None or not hasattr(thread, "isRunning"):
                return
            if not thread.isRunning():
                return
            thread.quit()
            if not thread.wait(250):
                try:
                    thread.terminate()
                except Exception:
                    pass
                thread.wait(250)

        for tab in getattr(self, "monitor_pages", []):
            for thread in list(getattr(tab, "_background_threads", set())):
                stop_thread(thread)
            stop_thread(getattr(tab, "_async_thread", None))
            stop_thread(getattr(tab, "_refresh_thread", None))
            stop_thread(getattr(tab, "thread", None))

        super().closeEvent(event)

    def preload_tab_data(self):
        return None

    def refresh_active_tab(self):
        current_tab = self.ui.load_pages.pages.currentWidget()
        update_data = getattr(current_tab, "update_data", None)
        if callable(update_data):
            update_data()

    def change_theme(self, theme):
        self.ui.central_widget.setProperty("monitor_theme", theme)

    def show_status(self, message):
        self.ui.credits.copyright_label.setText(message)

    def change_language(self, language):
        if language not in LANGUAGES:
            return
        self.current_language = language
        translate_widget_tree(self, language)
        for tab in self.monitor_pages:
            set_language = getattr(tab, "set_language", None)
            if callable(set_language):
                set_language(language)
        self.show_status(translate_text("Estado: pronto", language))


if __name__ == "__main__":
    ensure_admin()
    app = QApplication(sys.argv)
    app.setApplicationName("PyUtility")

    splash = StartupSplash()
    splash.center_on_screen()
    splash.show()
    app.processEvents()

    def on_progress(step, total, text):
        percent = int((step / total) * 100) if total else 0
        splash.set_status(text, percent)

    try:
        initial_data = preload_initial_data(progress_callback=on_progress)
        window = ModernMonitorApp(initial_data)
        window.showMaximized()
        splash.finish(window)
        splash.close()
    except Exception:
        splash.close()
        trace = traceback.format_exc()
        _write_startup_log(f"[fatal startup] uncaught exception:\n{trace}")
        traceback.print_exc()
        error_box = QMessageBox()
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setWindowTitle("PyUtility")
        error_box.setText("Ocorreu um erro ao iniciar a aplicação.\nVerifique a consola ou o ficheiro de diagnóstico em %LOCALAPPDATA%\\PyUtility\\startup_debug.log")
        error_box.exec()
        raise

    sys.exit(app.exec())
