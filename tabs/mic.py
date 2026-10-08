from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFileDialog
from PyQt6.QtCore import QThread, QObject, pyqtSignal
from datetime import datetime
from gui.widgets import PyPushButton

from backend import SystemMonitor
from tabs.ui_helpers import make_button


class ToolWorker(QObject):
    finished = pyqtSignal(str, bool, str)

    def __init__(self, action, package_name=None, command=None, report_path=None):
        super().__init__()
        self.action = action
        self.package_name = package_name
        self.command = command
        self.report_path = report_path

    def run(self):
        print(f"[DEBUG][Mic] ToolWorker.run started for action={self.action}")
        try:
            if self.action == "disk_cleanup":
                ok, msg = SystemMonitor.run_disk_cleanup()
            elif self.action == "temp_clean":
                ok, msg = SystemMonitor.clean_temp_folders()
            elif self.action == "flush_dns":
                ok, msg = SystemMonitor.flush_dns_cache()
            elif self.action == "check_system_files":
                ok, msg = SystemMonitor.check_system_files()
            elif self.action == "windows_update":
                ok, msg = SystemMonitor.open_windows_update()
            elif self.action == "system_report":
                ok, msg = SystemMonitor.save_system_report(self.report_path)
            else:
                ok, msg = False, "Ação desconhecida."
        except Exception as exc:
            ok, msg = False, str(exc)

        print(f"[DEBUG][Mic] ToolWorker.run finished for action={self.action}: ok={ok}, msg={msg}")
        self.finished.emit(self.action, ok, msg)


class MicTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        title = QLabel("Manutenção")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2a82da;")
        self.layout.addWidget(title)

        self.info = QLabel("Limpe o sistema, faça verificações e exporte um relatório.")
        self.layout.addWidget(self.info)

        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        self.disk_btn = make_button("Limpeza do disco")
        self.disk_btn.clicked.connect(lambda: self.run_action("disk_cleanup"))
        self.grid.addWidget(self.disk_btn, 0, 0)

        self.temp_btn = make_button("Limpar ficheiros temporários")
        self.temp_btn.clicked.connect(lambda: self.run_action("temp_clean"))
        self.grid.addWidget(self.temp_btn, 0, 1)

        self.dns_btn = make_button("Limpar cache DNS")
        self.dns_btn.clicked.connect(lambda: self.run_action("flush_dns"))
        self.grid.addWidget(self.dns_btn, 1, 0)

        self.system_files_btn = make_button("Verificar ficheiros do sistema")
        self.system_files_btn.clicked.connect(lambda: self.run_action("check_system_files"))
        self.grid.addWidget(self.system_files_btn, 1, 1)

        self.update_btn = make_button("Abrir Windows Update")
        self.update_btn.clicked.connect(lambda: self.run_action("windows_update"))
        self.grid.addWidget(self.update_btn, 2, 0, 1, 2)

        self.report_btn = make_button("Exportar relatório HTML")
        self.report_btn.clicked.connect(self.export_system_report)
        self.grid.addWidget(self.report_btn, 3, 0, 1, 2)

        self.status = QLabel("Pronto.")
        self.status.setStyleSheet("color: #ddd; margin-top: 12px;")
        self.layout.addWidget(self.status)
        self.layout.addStretch()

    def run_action(self, action, package_name=None, command=None):
        print(f"[DEBUG][Mic] run_action called: action={action}, package={package_name}, command={command}")
        self.set_buttons_enabled(False)
        self.status.setText("A executar... isto pode demorar alguns segundos.")

        self.thread = QThread(self)
        self.worker = ToolWorker(action, package_name, command)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_action_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker)

        self.thread.start()

    def export_system_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar relatório HTML",
            datetime.now().strftime("%Y-%m-%d_%H-%M-%S.html"),
            "Ficheiro HTML (*.html)",
        )
        if not path:
            return

        self.set_buttons_enabled(False)
        self.status.setText("A recolher informação do computador...")
        self.thread = QThread(self)
        self.worker = ToolWorker("system_report", report_path=path)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_action_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker)
        self.thread.start()

    def _clear_worker(self):
        self.thread = None
        self.worker = None

    def set_buttons_enabled(self, enabled):
        for btn in self.findChildren(PyPushButton):
            btn.setEnabled(enabled)

    def on_action_finished(self, action, ok, msg):
        print(f"[DEBUG][Mic] on_action_finished: action={action}, ok={ok}, msg={msg}")
        if ok:
            self.status.setText(f"Concluído: {msg}")
        else:
            self.status.setText(f"Erro: {msg[:150]}")

        self.set_buttons_enabled(True)

    def update_data(self):
        pass
