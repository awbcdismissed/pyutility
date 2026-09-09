import os
import re
from html import escape

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from diagnostics import (
    DEFAULT_GROQ_MODEL,
    DiagnosticEngine,
    GroqProvider,
    HistoryStore,
    LocalMaintenanceAssistant,
    MaintenanceAssistant,
    SystemSnapshotCollector,
)
from tabs.async_utils import start_background
from tabs.i18n import translate_text


class AIAssistantTab(QWidget):
    """Chat UI that asks Groq about a fresh, privacy-filtered system snapshot."""

    def __init__(self, collector=None, history=None, engine=None):
        super().__init__()
        self.collector = collector or SystemSnapshotCollector()
        self.history = history or HistoryStore()
        self.engine = engine or DiagnosticEngine()
        self.model = os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        self.assistant = MaintenanceAssistant(
            self._provider_from_environment(),
            LocalMaintenanceAssistant(),
        )
        self.messages = []
        self._waiting = False
        self.language = "pt"

        layout = QVBoxLayout(self)
        title = QLabel("AI Assistant")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2a82da;")
        layout.addWidget(title)
        subtitle = QLabel(
            "Pergunte sobre o seu computador. Cada pergunta usa uma medição atual e o diagnóstico local disponível."
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        settings = QGroupBox("Definições Groq")
        settings_layout = QVBoxLayout(settings)
        key_row = QHBoxLayout()
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Chave API da Groq")
        self.key_input.setClearButtonEnabled(True)
        self.apply_key_button = QPushButton("Aplicar chave")
        self.apply_key_button.clicked.connect(self.apply_key)
        key_row.addWidget(self.key_input)
        key_row.addWidget(self.apply_key_button)
        settings_layout.addLayout(key_row)
        self.key_status = QLabel(self._key_status())
        self.key_status.setWordWrap(True)
        settings_layout.addWidget(self.key_status)
        layout.addWidget(settings)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setPlaceholderText("A conversa aparecerá aqui.")
        layout.addWidget(self.chat, 1)

        self.status = QLabel("Pronto. A IA não executa comandos nem altera o computador.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ex.: Porque é que o meu PC está lento?")
        self.input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        self.clear_button = QPushButton("Limpar conversa")
        self.clear_button.clicked.connect(self.clear_conversation)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(self.send_button)
        input_row.addWidget(self.clear_button)
        layout.addLayout(input_row)

    def _provider_from_environment(self):
        key = os.environ.get("GROQ_API_KEY", "").strip()
        return GroqProvider(key, model=self.model) if key else None

    def update_data(self):
        # A recolha ocorre por pergunta para garantir contexto atual sem scans periódicos.
        return None

    def set_language(self, language):
        self.language = language
        self.key_status.setText(self._key_status())
        self.status.setText(self._translate("Pronto. A IA não executa comandos nem altera o computador."))

    def _translate(self, text):
        return translate_text(text, self.language)

    def _key_status(self):
        if self.assistant.provider is not None:
            return self._translate(f"Chave Groq configurada apenas nesta sessão. Modelo: {self.model}.")
        return self._translate("Sem chave Groq. O fallback local continua disponível.")

    def apply_key(self):
        key = self.key_input.text().strip()
        self.assistant.provider = GroqProvider(key, model=self.model) if key else None
        self.key_status.setText(self._translate(
            f"Chave Groq configurada apenas nesta sessão. Modelo: {self.model}."
            if key
            else "Chave removida. O fallback local continua disponível."
        ))
        self.status.setText(self._translate("Definições atualizadas. A chave nunca é mostrada na conversa nem guardada no histórico."))

    def send_message(self):
        question = self.input.text().strip()
        if not question or self._waiting:
            return
        self.input.clear()
        previous_messages = list(self.messages)
        self._add_message("Tu", question)
        self._waiting = True
        self.send_button.setEnabled(False)
        self.input.setEnabled(False)
        self.status.setText(self._translate("A recolher dados atuais e a analisar... "))
        started = start_background(
            self,
            lambda: self._answer_question(question, previous_messages),
            self._display_answer,
            self._display_error,
        )
        if not started:
            self._set_ready(self._translate("Já existe uma análise em curso. Aguarde alguns segundos."))

    def _answer_question(self, question, conversation):
        snapshot = self.collector.collect()
        samples = self.history.append(snapshot)
        analysis = self.engine.analyze(snapshot, samples)
        return self.assistant.answer(question, snapshot, analysis, conversation)

    def _display_answer(self, result):
        source = result.get("source", "Diagnóstico local")
        text = result.get("text", "Não foi possível obter uma resposta.")
        self._add_message(self._translate(source), self._translate(text) if source == "Diagnóstico local" else text)
        error = result.get("error")
        if error:
            self.status.setText(self._translate(f"Groq indisponível; foi usada a resposta local. Motivo: {error}"))
        else:
            self.status.setText(self._translate("Resposta baseada na medição atual do computador."))
        self._set_ready()

    def _display_error(self, message):
        self._add_message(self._translate("Sistema"), self._translate(f"Não foi possível concluir a análise: {message}"))
        self._set_ready(self._translate("A análise falhou. O resto da aplicação continua disponível."))

    def _set_ready(self, message=None):
        self._waiting = False
        self.send_button.setEnabled(True)
        self.input.setEnabled(True)
        if message:
            self.status.setText(message)
        self.input.setFocus()

    def _add_message(self, author, text):
        self.messages.append({"role": "model" if author not in ("Tu", "Sistema") else "user", "text": text})
        safe_author = escape(str(author))
        safe_text = escape(str(text))
        safe_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", safe_text)
        safe_text = safe_text.replace("\n", "<br>")
        self.chat.insertHtml(f"<p><strong>{safe_author}:</strong><br>{safe_text}</p>")
        self.chat.ensureCursorVisible()

    def clear_conversation(self):
        if self._waiting:
            return
        self.messages.clear()
        self.chat.clear()
        self.status.setText(self._translate("Conversa limpa. O próximo pedido recolherá novos dados."))
