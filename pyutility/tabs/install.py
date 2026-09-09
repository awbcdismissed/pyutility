from PyQt6.QtCore import QThread, QObject, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QGridLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from backend import SystemMonitor


SUPPORTED_APPS = [
    # Browsers
    {
        "name": "Google Chrome",
        "category": "Navegadores",
        "winget": 'winget install -e --id Google.Chrome --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install googlechrome --yes --no-progress',
    },
    {
        "name": "Mozilla Firefox",
        "category": "Navegadores",
        "winget": 'winget install -e --id Mozilla.Firefox --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install firefox --yes --no-progress',
    },
    {
        "name": "Brave",
        "category": "Navegadores",
        "winget": 'winget install -e --id Brave.Brave --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install brave --yes --no-progress',
    },
    {
        "name": "Opera",
        "category": "Navegadores",
        "winget": 'winget install -e --id Opera.Opera --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install opera --yes --no-progress',
    },
    # Communication
    {
        "name": "Discord",
        "category": "Comunicação",
        "winget": 'winget install -e --id Discord.Discord --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install discord --yes --no-progress',
    },
    {
        "name": "Telegram",
        "category": "Comunicação",
        "winget": 'winget install -e --id Telegram.TelegramDesktop --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install telegram --yes --no-progress',
    },
    {
        "name": "Zoom",
        "category": "Comunicação",
        "winget": 'winget install -e --id Zoom.Zoom.VDI --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install zoom --yes --no-progress',
    },
    {
        "name": "Microsoft Teams",
        "category": "Comunicação",
        "winget": 'winget install -e --id Microsoft.Teams.Free --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install microsoft-teams --yes --no-progress',
    },
    # Development
    {
        "name": "Visual Studio Code",
        "category": "Desenvolvimento",
        "winget": 'winget install -e --id Microsoft.VisualStudioCode --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install vscode --yes --no-progress',
    },
    {
        "name": "Git",
        "category": "Desenvolvimento",
        "winget": 'winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install git --yes --no-progress',
    },
    {
        "name": "Python",
        "category": "Desenvolvimento",
        "winget": 'winget install -e --id Python.Python3.13 --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install python --yes --no-progress',
    },
    {
        "name": "Node.js LTS",
        "category": "Desenvolvimento",
        "winget": 'winget install -e --id NodeJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install nodejs-lts --yes --no-progress',
    },
    # Documents
    {
        "name": "LibreOffice",
        "category": "Documentos",
        "winget": 'winget install -e --id LibreOffice.LibreOffice --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install libreoffice-fresh --yes --no-progress',
    },
    {
        "name": "7-Zip",
        "category": "Documentos",
        "winget": 'winget install -e --id 7-Zip.7-Zip --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install 7zip --yes --no-progress',
    },
    {
        "name": "PDF24 Creator",
        "category": "Documentos",
        "winget": 'winget install -e --id PDF24.PDF24.Creator --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install pdf24 --yes --no-progress',
    },
    {
        "name": "Notepad++",
        "category": "Documentos",
        "winget": 'winget install -e --id Notepad++.Notepad++ --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install notepadplusplus --yes --no-progress',
    },
    # Games
    {
        "name": "Steam",
        "category": "Jogos",
        "winget": 'winget install -e --id Steam.Steam --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install steam --yes --no-progress',
    },
    {
        "name": "Epic Games Launcher",
        "category": "Jogos",
        "winget": 'winget install -e --id EpicGames.EpicGamesLauncher --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install epicgameslauncher --yes --no-progress',
    },
    {
        "name": "GOG Galaxy",
        "category": "Jogos",
        "winget": 'winget install -e --id GOG.GOGGalaxy --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install goggalaxy --yes --no-progress',
    },
    {
        "name": "Battle.net",
        "category": "Jogos",
        "winget": 'winget install -e --id Battle.net.Battle.net --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install battle.net --yes --no-progress',
    },
    {
        "name": "Ubisoft Connect",
        "category": "Jogos",
        "winget": 'winget install -e --id Ubisoft.UbisoftConnect --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install ubisoft-connect --yes --no-progress',
    },
    {
        "name": "EA app",
        "category": "Jogos",
        "winget": 'winget install -e --id EA.EAApp --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install ea-app --yes --no-progress',
    },
    # Microsoft tools
    {
        "name": "PowerToys",
        "category": "Ferramentas Microsoft",
        "winget": 'winget install -e --id Microsoft.PowerToys --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install powertoys --yes --no-progress',
    },
    {
        "name": ".NET Desktop Runtime",
        "category": "Ferramentas Microsoft",
        "winget": 'winget install -e --id Microsoft.NETDesktopRuntime --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install dotnet-desktopruntime --yes --no-progress',
    },
    {
        "name": "Microsoft Edge",
        "category": "Ferramentas Microsoft",
        "winget": 'winget install -e --id Microsoft.Edge --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install microsoft-edge --yes --no-progress',
    },
    {
        "name": "Windows Terminal",
        "category": "Ferramentas Microsoft",
        "winget": 'winget install -e --id Microsoft.WindowsTerminal --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install microsoft-windows-terminal --yes --no-progress',
    },
    # Multimedia
    {
        "name": "Spotify",
        "category": "Ferramentas multimédia",
        "winget": 'winget install -e --id Spotify.Spotify --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install spotify --yes --no-progress',
    },
    {
        "name": "VLC Media Player",
        "category": "Ferramentas multimédia",
        "winget": 'winget install -e --id VideoLAN.VLC --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install vlc --yes --no-progress',
    },
    {
        "name": "Audacity",
        "category": "Ferramentas multimédia",
        "winget": 'winget install -e --id Audacity.Audacity --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install audacity --yes --no-progress',
    },
    {
        "name": "OBS Studio",
        "category": "Ferramentas multimédia",
        "winget": 'winget install -e --id OBSProject.OBSStudio --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install obs-studio --yes --no-progress',
    },
    # Professional tools
    {
        "name": "Revo Uninstaller",
        "category": "Ferramentas profissionais",
        "winget": 'winget install -e --id RevoUninstaller.RevoUninstaller --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install revo-uninstaller --yes --no-progress',
    },
    {
        "name": "Everything Search",
        "category": "Ferramentas profissionais",
        "winget": 'winget install -e --id Everything.Everything --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install everything --yes --no-progress',
    },
    {
        "name": "HWiNFO",
        "category": "Ferramentas profissionais",
        "winget": 'winget install -e --id REALiX.HWiNFO --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install hwinfo --yes --no-progress',
    },
    # Standalone tools
    {
        "name": "Docker Desktop",
        "category": "Ferramentas autónomas",
        "winget": 'winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install docker-desktop --yes --no-progress',
    },
    {
        "name": "MobaXterm",
        "category": "Ferramentas autónomas",
        "winget": 'winget install -e --id Mobatek.MobaXterm --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install mobaxterm --yes --no-progress',
    },
    {
        "name": "PuTTY",
        "category": "Ferramentas autónomas",
        "winget": 'winget install -e --id PuTTY.PuTTY --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install putty --yes --no-progress',
    },
    {
        "name": "FileZilla",
        "category": "Ferramentas autónomas",
        "winget": 'winget install -e --id FileZilla.FileZilla --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install filezilla --yes --no-progress',
    },
    # Utilities
    {
        "name": "Display Driver Uninstaller (DDU)",
        "category": "Utilitários",
        "winget": 'winget install -e --id Wagnardsoft.DisplayDriverUninstaller --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install ddu --yes --no-progress',
    },
    {
        "name": "Snappy Driver Installer",
        "category": "Utilitários",
        "winget": 'winget install -e --id samlab-ws.SnappyDriverInstaller --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install sdio --yes --no-progress',
    },
    {
        "name": "Registry Cleaner",
        "category": "Utilitários",
        "winget": 'winget install -e --id RevoUninstaller.RevoRegistryCleaner --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install  --yes --no-progress',
    },
    {
        "name": "CrystalDiskInfo",
        "category": "Utilitários",
        "winget": 'winget install -e --id CrystalDewWorld.CrystalDiskInfo --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install "crystaldiskinfo" --yes --no-progress',
    },
    {
        "name": "CCleaner",
        "category": "Utilitários",
        "winget": 'winget install -e --id Piriform.CCleaner.Slim --accept-source-agreements --accept-package-agreements',
        "chocolatey": 'choco install "ccleaner" --yes --no-progress',
    },
]


class InstallWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, package_name, manager, command=None):
        super().__init__()
        self.package_name = package_name
        self.manager = manager
        self.command = command

    def run(self):
        try:
            result = SystemMonitor.install_package(
                self.package_name,
                self.manager,
                self.command,
            )
        except Exception as exc:
            result = False, str(exc)
        self.finished.emit(*result)


class InstallTab(QWidget):
    SUPPORTED_APPS = SUPPORTED_APPS

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

        manager_layout = QGridLayout()
        manager_layout.addWidget(QLabel("Gestor de pacotes:"), 0, 0)
        self.manager_selector = QComboBox()
        self.manager_selector.addItems(["Winget", "Chocolatey"])
        manager_layout.addWidget(self.manager_selector, 0, 1)
        layout.addLayout(manager_layout)

        self.categories = QTabWidget()
        categories = {}
        for application in self.SUPPORTED_APPS:
            categories.setdefault(application["category"], []).append(application)
        for category, applications in categories.items():
            self.categories.addTab(self._create_category(applications), category)
        layout.addWidget(self.categories)

    def _create_category(self, applications):
        page = QWidget()
        grid = QGridLayout(page)
        for index, application in enumerate(applications):
            button = QPushButton(f"Instalar {application['name']}")
            button.clicked.connect(
                lambda checked=False, selected=application: self.install_package(selected)
            )
            grid.addWidget(button, index // 2, index % 2)
        grid.setRowStretch((len(applications) + 1) // 2, 1)
        return page

    def install_package(self, application):
        self.set_buttons_enabled(False)
        manager = self.manager_selector.currentText()
        self.status.setText(
            f"A verificar o {manager} e a preparar a instalação..."
        )
        self.thread = QThread(self)
        self.worker = InstallWorker(
            application["name"], manager, application[manager.lower()]
        )
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
