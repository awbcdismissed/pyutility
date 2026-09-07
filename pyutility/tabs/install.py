from PyQt6.QtCore import QThread, QObject, pyqtSignal
from PyQt6.QtWidgets import QGridLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from backend import SystemMonitor


class InstallWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, package_name, command=None):
        super().__init__()
        self.package_name = package_name
        self.command = command

    def run(self):
        result = SystemMonitor.install_choco_package(self.package_name, self.command)
        self.finished.emit(*result)


class InstallTab(QWidget):
    CATEGORIES = {
        "Navegadores": [
            ("Google Chrome", "googlechrome"),
            ("Mozilla Firefox", "firefox"),
            ("Brave", "brave"),
            ("Opera", "opera"),
        ],
        "Comunicação": [
            ("Discord", "discord"),
            ("Telegram", "telegram"),
            ("Zoom", "zoom"),
            ("Microsoft Teams", "microsoft-teams"),
        ],
        "Desenvolvimento": [
            ("Visual Studio Code", "vscode"),
            ("Git", "git"),
            ("Python", "python"),
            ("Node.js LTS", "nodejs-lts"),
        ],
        "Documentos": [
            ("LibreOffice", "libreoffice-fresh"),
            ("7-Zip", "7zip"),
            ("PDF24 Creator", "pdf24"),
            ("Notepad++", "notepadplusplus"),
        ],
        "Jogos": [
            ("Steam", "steam"),
            ("Epic Games Launcher", "epicgameslauncher"),
            ("GOG Galaxy", "goggalaxy"),
            ("Battle.net", "battle.net"),
            ("Ubisoft Connect", "ubisoft-connect"),
            ("EA app", "ea-app"),
        ],
        "Ferramentas Microsoft": [
            ("PowerToys", "powertoys"),
            (".NET Desktop Runtime", "dotnet-desktopruntime"),
            ("Microsoft Edge", "microsoft-edge"),
            ("Windows Terminal", "microsoft-windows-terminal"),
        ],
        "Ferramentas multimédia": [
            ("Spotify", "spotify"),
            ("VLC Media Player", "vlc"),
            ("Audacity", "audacity"),
            ("OBS Studio", "obs-studio"),
        ],
        "Ferramentas profissionais": [
            ("Revo Uninstaller", "revo-uninstaller"),
            ("Everything Search", "everything"),
            ("HWiNFO", "hwinfo"),
        ],
        "Ferramentas autónomas": [
            ("Docker Desktop", "docker-desktop"),
            ("MobaXterm", "mobaxterm"),
            ("PuTTY", "putty"),
            ("FileZilla", "filezilla"),
        ],
        "Utilitários": [
            ("Display Driver Uninstaller (DDU)", "ddu", "choco install ddu --version=18.0.8.1 --yes --no-progress"),
            ("Snappy Driver Installer", "snappy-driver-installer"),
            ("Registry Cleaner", "regcleaner"),
            ("CrystalDiskInfo", "crystaldiskinfo"),
            ("CCleaner", "ccleaner"),
        ],
    }

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        layout = QVBoxLayout(self)
        title = QLabel("Instalar aplicações")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2a82da;")
        layout.addWidget(title)
        self.status = QLabel("Escolha uma categoria e uma aplicação para instalar.")
        layout.addWidget(self.status)

        self.categories = QTabWidget()
        for category, applications in self.CATEGORIES.items():
            self.categories.addTab(self._create_category(applications), category)
        layout.addWidget(self.categories)

    def _create_category(self, applications):
        page = QWidget()
        grid = QGridLayout(page)
        for index, application in enumerate(applications):
            label, package_name, *command = application
            button = QPushButton(f"Instalar {label}")
            button.clicked.connect(
                lambda checked=False, package=package_name, custom_command=command:
                self.install_package(package, custom_command[0] if custom_command else None)
            )
            grid.addWidget(button, index // 2, index % 2)
        grid.setRowStretch((len(applications) + 1) // 2, 1)
        return page

    def install_package(self, package_name, command=None):
        self.set_buttons_enabled(False)
        self.status.setText("A instalar... isto pode demorar alguns segundos.")
        self.thread = QThread(self)
        self.worker = InstallWorker(package_name, command)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_install_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def set_buttons_enabled(self, enabled):
        for button in self.findChildren(QPushButton):
            button.setEnabled(enabled)

    def on_install_finished(self, ok, message):
        self.status.setText(f"Sucesso: {message}" if ok else f"Erro: {message[:150]}")
        self.set_buttons_enabled(True)

    def update_data(self):
        pass
