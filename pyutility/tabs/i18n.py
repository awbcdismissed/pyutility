from PyQt6.QtWidgets import QComboBox, QLineEdit, QProgressBar, QTabWidget, QTableWidget, QTreeWidget, QTextEdit, QWidget


LANGUAGES = {
    "pt": "Português",
    "en": "English",
}

_TRANSLATIONS = {
    "Início": "Home",
    "Processos": "Processes",
    "Histórico": "History",
    "Teste de velocidade": "Speed test",
    "Manutenção": "Maintenance",
    "Instalar": "Install",
    "Sistema": "System",
    "Arranque": "Startup",
    "Segurança": "Security",
    "Cópias de segurança": "Backups",
    "Registos": "Logs",
    "Controladores": "Drivers",
    "Dispositivos": "Devices",
    "Navegadores": "Browsers",
    "Comunicação": "Communication",
    "Desenvolvimento": "Development",
    "Documentos": "Documents",
    "Jogos": "Games",
    "Ferramentas Microsoft": "Microsoft tools",
    "Ferramentas multimédia": "Multimedia tools",
    "Ferramentas profissionais": "Professional tools",
    "Ferramentas autónomas": "Self-hosted tools",
    "Utilitários": "Utilities",
    "Tema:": "Theme:",
    "Idioma:": "Language:",
    "Tema escuro": "Dark theme",
    "Tema claro": "Light theme",
    "Sobre o programa": "About the program",
    "O PyUtility acompanha o estado do computador num só lugar. Explore as abas para consultar componentes, segurança, processos e ferramentas de manutenção.": "PyUtility monitors your computer in one place. Explore the tabs to view components, security, processes, and maintenance tools.",
    "Sistema:": "System:",
    "Computador:": "Computer:",
    "Processador:": "Processor:",
    "Fabricante:": "Manufacturer:",
    "Arquitetura:": "Architecture:",
    "Núcleos físicos:": "Physical cores:",
    "Frequência Atual:": "Current frequency:",
    "Frequência Máxima:": "Maximum frequency:",
    "Sockets:": "Sockets:",
    "A recolher informação das placas gráficas...": "Collecting graphics card information...",
    "Nenhuma placa de vídeo detetada.": "No graphics card detected.",
    "Carregando...": "Loading...",
    "a medir...": "measuring...",
    "Falha no teste": "Test failed",
    "Não presente": "Not present",
    "Sem permissões para terminar este processo.": "You do not have permission to end this process.",
    "Pesquisar processo pelo nome...": "Search process by name...",
    "Terminar Processo": "End process",
    "Registo de Aplicações em Foco (Atualização a cada 10s):": "Focused application history (updates every 10s):",
    "Teste de velocidade da rede": "Network speed test",
    "Testar velocidade": "Test speed",
    "Pronto para testar.": "Ready to test.",
    "A medir ping, download e upload... isto pode demorar 20-40s.": "Measuring ping, download, and upload... this may take 20-40s.",
    "Teste concluído.": "Test completed.",
    "Limpe o sistema, faça verificações e exporte um relatório.": "Clean the system, run checks, and export a report.",
    "Limpeza do disco": "Disk cleanup",
    "Limpar ficheiros temporários": "Clean temporary files",
    "Limpar cache DNS": "Flush DNS cache",
    "Verificar ficheiros do sistema": "Check system files",
    "Abrir Windows Update": "Open Windows Update",
    "Exportar relatório HTML": "Export HTML report",
    "Pronto.": "Ready.",
    "A executar... isto pode demorar alguns segundos.": "Running... this may take a few seconds.",
    "A recolher informação do computador...": "Collecting computer information...",
    "Concluído: ": "Completed: ",
    "Instalar aplicações": "Install applications",
    "Escolha uma categoria e uma aplicação para instalar.": "Choose a category and an application to install.",
    "A instalar... isto pode demorar alguns segundos.": "Installing... this may take a few seconds.",
    "Saúde do Sistema": "System health",
    "A recolher estado do computador...": "Collecting computer status...",
    "Temperaturas: indisponíveis neste sistema": "Temperatures: unavailable on this system",
    "Unidade": "Drive",
    "Montagem": "Mount point",
    "Formato": "Filesystem",
    "Total": "Total",
    "Usado": "Used",
    "Livre": "Free",
    "Atenção": "Warning",
    "Destino:": "Destination:",
    "Destino vazio": "Empty destination",
    "Indisponível": "Unavailable",
    "Inativo": "Inactive",
    "Wi-Fi / Rede": "Wi-Fi / Network",
    "A recolher ligação Wi-Fi...": "Collecting Wi-Fi connection...",
    "Testar latência": "Test latency",
    "Programas no arranque do Windows": "Windows startup programs",
    "Programas ativos": "Active programs",
    "Programas desativados": "Disabled programs",
    "Estado de Segurança": "Security status",
    "Antivírus: a verificar...": "Antivirus: checking...",
    "Portas em escuta": "Listening ports",
    "Processos: a verificar...": "Processes: checking...",
    "Backup / Restore da configuração": "Configuration backup / restore",
    "Escolha uma operação.": "Choose an operation.",
    "Criar backup": "Create backup",
    "Restaurar backup": "Restore backup",
    "Eventos recentes do sistema": "Recent system events",
    "Atualizar logs": "Refresh logs",
    "Exportar TXT / CSV": "Export TXT / CSV",
    "Drivers instalados": "Installed drivers",
    "Os drivers são listados pelo Windows.": "Drivers are listed by Windows.",
    "Verificar drivers": "Check drivers",
    "Abrir pesquisa oficial do fabricante": "Open manufacturer's official search",
    "Guardar backup": "Save backup",
    "Abrir backup": "Open backup",
    "Exportar logs": "Export logs",
    "Guardar relatório HTML": "Save HTML report",
    "Ficheiro HTML (*.html)": "HTML file (*.html)",
    "Texto (*.txt);;CSV (*.csv)": "Text (*.txt);;CSV (*.csv)",
    "Dispositivos ligados ao computador": "Devices connected to the computer",
    "A pesquisar dispositivos...": "Searching for devices...",
    "A atualizar o dispositivo...": "Updating device...",
    "Abrir propriedades": "Open properties",
    "Pesquisar HWID no browser": "Search HWID in browser",
    "Nome": "Name",
    "Descrição": "Description",
    "Tipo": "Type",
    "Estado": "Status",
    "Endereço": "Address",
    "Porta": "Port",
    "Âmbito": "Scope",
    "Origem": "Source",
    "Comando": "Command",
    "Hora": "Time",
    "Latência": "Latency",
    "Dispositivo": "Device",
    "ID de hardware": "Hardware ID",
    "Local (IP:Porta)": "Local (IP:Port)",
    "Remoto (Destino)": "Remote (Destination)",
    "Ativo": "Active",
    "Desativado": "Disabled",
    "Ativar": "Enable",
    "Desativar": "Disable",
    "Feito por Martim Oliveira 12ºGEI - 2026": "Created by Martim Oliveira 12ºGEI - 2026",
    "A pesquisar": "Searching",
    "IP Local: Carregando...": "Local IP: Loading...",
    "IP Público: Carregando...": "Public IP: Loading...",
    "Download:": "Download:",
    "Upload:": "Upload:",
    "Ping:": "Ping:",
    "Mbps": "Mbps",
    "CPU: %p%": "CPU: %p%",
    "Memória: %p%": "Memory: %p%",
}

_PREFIX_TRANSLATIONS = {
    "Sistema: ": "System: ",
    "Computador: ": "Computer: ",
    "Fabricante/Série: ": "Manufacturer/series: ",
    "Driver: ": "Driver: ",
    "Carga: ": "Load: ",
    "Temperatura: ": "Temperature: ",
    "VRAM livre: ": "Free VRAM: ",
    "Ventoinha: ": "Fan: ",
    "Resolução: ": "Resolution: ",
    "Energia: ": "Power: ",
    "Clock GPU: ": "GPU clock: ",
    "Clock memória: ": "Memory clock: ",
    "Aplicação ativa: ": "Active application: ",
    "Download: ": "Download: ",
    "Upload: ": "Upload: ",
    "Ping: ": "Ping: ",
    "Temperaturas: ": "Temperatures: ",
    "Disco ": "Disk ",
    "Interface: ": "Interface: ",
    "SSID: ": "SSID: ",
    "Sinal: ": "Signal: ",
    "Canal: ": "Channel: ",
    "Banda: ": "Band: ",
    "Temp: ": "Temperature: ",
    "VRAM: ": "VRAM: ",
    "UUID: ": "UUID: ",
    "Memória disponível: ": "Available memory: ",
    "Não foi possível ler o estado do sistema: ": "Could not read system status: ",
    " drivers encontrados.": " drivers found.",
    "Sucesso: ": "Success: ",
    "Erro: ": "Error: ",
    "Não foi possível ler a GPU: ": "Could not read GPU: ",
    "Antivírus Microsoft Defender: ": "Microsoft Defender antivirus: ",
    "Processos com uso elevado de CPU: ": "Processes with high CPU usage: ",
    "Dispositivos encontrados.": "devices found.",
    " dispositivos encontrados.": " devices found.",
    "Problema ": "Problem ",
    "IP Local: ": "Local IP: ",
    "IP Público: ": "Public IP: ",
    "Ligações Ativas / Portas em Escuta:": "Active Connections / Listening Ports:",
    "A medir": "Measuring",
    "Não presente": "Not present",
    "Instalar ": "Install ",
}

_REVERSE_TRANSLATIONS = {english: portuguese for portuguese, english in _TRANSLATIONS.items()}
_REVERSE_PREFIX_TRANSLATIONS = {english: portuguese for portuguese, english in _PREFIX_TRANSLATIONS.items()}
_PHRASE_TRANSLATIONS = {
    " drivers encontrados.": " drivers found.",
    " dispositivos encontrados.": " devices found.",
    " de ": " of ",
    " | Discos monitorizados: ": " | Monitored disks: ",
}
_REVERSE_PHRASE_TRANSLATIONS = {english: portuguese for portuguese, english in _PHRASE_TRANSLATIONS.items()}


def translate_text(text, language):
    if not text:
        return text
    translations = _TRANSLATIONS if language == "en" else _REVERSE_TRANSLATIONS
    prefixes = _PREFIX_TRANSLATIONS if language == "en" else _REVERSE_PREFIX_TRANSLATIONS
    translated = translations.get(text)
    if translated is not None:
        return translated
    for source, target in prefixes.items():
        if text.startswith(source):
            text = target + text[len(source):]
            break
    phrases = _PHRASE_TRANSLATIONS if language == "en" else _REVERSE_PHRASE_TRANSLATIONS
    for source, target in phrases.items():
        if source in text:
            text = text.replace(source, target)
    return text


def translate_widget_tree(root: QWidget, language):
    for widget in [root, *root.findChildren(QWidget)]:
        if isinstance(widget, QComboBox) and widget.objectName() == "languageSelector":
            continue
        if isinstance(widget, QComboBox):
            current = widget.currentIndex()
            for index in range(widget.count()):
                widget.setItemText(index, translate_text(widget.itemText(index), language))
            widget.setCurrentIndex(current)
        elif isinstance(widget, QLineEdit):
            widget.setPlaceholderText(translate_text(widget.placeholderText(), language))
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(translate_text(widget.toPlainText(), language))
        elif isinstance(widget, QProgressBar):
            widget.setFormat(translate_text(widget.format(), language))
        elif hasattr(widget, "text") and hasattr(widget, "setText"):
            widget.setText(translate_text(widget.text(), language))
        if isinstance(widget, QTableWidget):
            for column in range(widget.columnCount()):
                header = widget.horizontalHeaderItem(column)
                if header:
                    header.setText(translate_text(header.text(), language))
        if isinstance(widget, QTreeWidget):
            for column in range(widget.columnCount()):
                widget.headerItem().setText(column, translate_text(widget.headerItem().text(column), language))
            for index in range(widget.topLevelItemCount()):
                group = widget.topLevelItem(index)
                for child_index in range(group.childCount()):
                    child = group.child(child_index)
                    child.setText(1, translate_text(child.text(1), language))
        if isinstance(widget, QTabWidget):
            for index in range(widget.count()):
                widget.setTabText(index, translate_text(widget.tabText(index), language))
