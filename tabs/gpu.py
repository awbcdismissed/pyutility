from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from backend import SystemMonitor
from tabs.async_utils import start_background


class GPUTab(QWidget):
    def __init__(self, initial_data=None):
        super().__init__()
        self._gpu_cards = []
        self.setObjectName("gpuTab")
        self.layout_base = QVBoxLayout(self)
        self.layout_base.setContentsMargins(28, 24, 28, 28)
        self.layout_base.setSpacing(18)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Placas gráficas")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Estado, memória e desempenho dos adaptadores detetados")
        subtitle.setObjectName("pageSubtitle")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch()
        self.status = QLabel("A aguardar dados...")
        self.status.setObjectName("gpuStatus")
        header.addWidget(self.status, 0, Qt.AlignmentFlag.AlignBottom)
        self.layout_base.addLayout(header)

        self.summary_layout = QGridLayout()
        self.summary_layout.setSpacing(12)
        self.summary_cards = {
            "count": self._create_summary_card("ADAPTADORES", "-"),
            "load": self._create_summary_card("CARGA MÉDIA", "-"),
            "memory": self._create_summary_card("VRAM TOTAL", "-"),
        }
        self.summary_layout.addWidget(self.summary_cards["count"], 0, 0)
        self.summary_layout.addWidget(self.summary_cards["load"], 0, 1)
        self.summary_layout.addWidget(self.summary_cards["memory"], 0, 2)
        self.layout_base.addLayout(self.summary_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content = QWidget()
        self.container = QVBoxLayout(self.content)
        self.container.setContentsMargins(0, 0, 0, 0)
        self.container.setSpacing(12)
        self._empty_label = QLabel("A recolher informação das placas gráficas...")
        self._empty_label.setObjectName("gpuEmptyState")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setMinimumHeight(140)
        self.container.addWidget(self._empty_label)
        self.container.addStretch()
        self.scroll.setWidget(self.content)
        self.layout_base.addWidget(self.scroll)
        if initial_data is not None:
            self._display_data(initial_data)

    def update_data(self, gpus=None):
        if gpus is not None:
            self._display_data(gpus)
            return
        start_background(self, SystemMonitor.get_gpu_detailed_info, self._display_data, self._display_error)

    def _display_error(self, message):
        self._display_data([])
        self.status.setText("Leitura indisponível")
        self._empty_label.setText(f"Não foi possível ler as placas gráficas: {message}")

    def _display_data(self, gpus):
        gpus = gpus or []
        if not gpus:
            self._empty_label.setText("Nenhuma placa de vídeo detetada.")
            self._empty_label.show()
            for card in self._gpu_cards:
                card["frame"].hide()
            self._set_summary("0", "N/D", "N/D")
            self.status.setText("Sem adaptadores detetados")
            return

        self._empty_label.hide()
        while len(self._gpu_cards) < len(gpus):
            self._gpu_cards.append(self._create_gpu_card())
        for index, gpu in enumerate(gpus):
            card = self._gpu_cards[index]
            card["frame"].show()
            self._fill_gpu_card(card, gpu)
        for card in self._gpu_cards[len(gpus):]:
            card["frame"].hide()
        self._update_summary(gpus)
        self.status.setText(f"Atualizado agora · {len(gpus)} adaptador(es)")

    def _create_gpu_card(self):
        frame = QFrame()
        frame.setObjectName("gpuCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        identity = QVBoxLayout()
        identity.setSpacing(2)
        title = QLabel()
        title.setObjectName("gpuName")
        type_label = QLabel()
        type_label.setObjectName("gpuType")
        identity.addWidget(title)
        identity.addWidget(type_label)
        header.addLayout(identity)
        header.addStretch()
        driver = QLabel()
        driver.setObjectName("gpuDriver")
        driver.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        driver.setWordWrap(True)
        header.addWidget(driver, 0)
        layout.addLayout(header)

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(24)
        metrics.setVerticalSpacing(8)
        metric_labels = {}
        metric_captions = {}
        for index, (key, label) in enumerate((("load", "Carga"), ("temp", "Temperatura"), ("vram", "VRAM"), ("resolution", "Resolução"))):
            caption = QLabel(label.upper())
            caption.setObjectName("gpuMetricLabel")
            value = QLabel("N/D")
            value.setObjectName("gpuMetricValue")
            value.hide()
            caption.hide()
            column = index % 4
            metrics.addWidget(caption, 0, column)
            metrics.addWidget(value, 1, column)
            metric_labels[key] = value
            metric_captions[key] = caption
        layout.addLayout(metrics)

        progress = QProgressBar()
        progress.setObjectName("gpuLoadBar")
        progress.setRange(0, 100)
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.hide()
        layout.addWidget(progress)

        details_title = QLabel("INFORMAÇÃO COMPLETA")
        details_title.setObjectName("gpuMetricLabel")
        layout.addWidget(details_title)
        details_grid = QGridLayout()
        details_grid.setHorizontalSpacing(24)
        details_grid.setVerticalSpacing(6)
        detail_labels = {}
        detail_captions = {}
        detail_fields = (
            ("vram_free", "VRAM livre"),
            ("fan_speed", "Ventoinha"),
            ("power_draw", "Consumo"),
            ("power_limit", "Limite de energia"),
            ("clock_graphics", "Clock GPU"),
            ("clock_memory", "Clock memória"),
            ("gpu_id", "ID GPU"),
            ("uuid", "UUID"),
            ("serial", "Número de série"),
            ("display_active", "Ecrã ativo"),
        )
        for index, (key, label) in enumerate(detail_fields):
            cell = QVBoxLayout()
            caption = QLabel(label)
            caption.setObjectName("gpuMetricLabel")
            value = QLabel("N/D")
            value.setObjectName("gpuDetailValue")
            value.setWordWrap(True)
            value.hide()
            caption.hide()
            cell.addWidget(caption)
            cell.addWidget(value)
            details_grid.addLayout(cell, index // 2, index % 2)
            detail_labels[key] = value
            detail_captions[key] = caption
        layout.addLayout(details_grid)
        self.container.insertWidget(self.container.count() - 1, frame)
        return {
            "frame": frame,
            "title": title,
            "type": type_label,
            "driver": driver,
            "metrics": metric_labels,
            "metric_captions": metric_captions,
            "progress": progress,
            "details": detail_labels,
            "detail_captions": detail_captions,
        }

    def _fill_gpu_card(self, card, gpu):
        load = self._number(gpu.get("load"))
        used = self._text(gpu.get("vram_used"))
        total = self._text(gpu.get("vram_total"))
        card["title"].setText(self._text(gpu.get("name"), "GPU"))
        card["type"].setText(f"{self._text(gpu.get('vendor'))} · {self._text(gpu.get('type'))}")
        driver_value = self._text(gpu.get("driver_version"))
        card["driver"].setVisible(driver_value != "N/D")
        card["driver"].setText(f"Driver {driver_value}")

        self._set_metric(card, "load", self._has_value(gpu.get("load")), f"{load:.1f}%" if load is not None else "N/D")
        self._set_metric(card, "temp", self._has_value(gpu.get("temp")), self._text(gpu.get("temp")))
        has_vram = self._has_value(gpu.get("vram_total")) or self._has_value(gpu.get("vram_used"))
        self._set_metric(card, "vram", has_vram, f"{used} / {total}")
        self._set_metric(card, "resolution", self._has_value(gpu.get("resolution")), self._text(gpu.get("resolution")))

        has_load = self._has_value(gpu.get("load"))
        card["progress"].setVisible(has_load)
        if has_load:
            card["progress"].setValue(round(load) if load is not None else 0)
        else:
            card["progress"].setValue(0)

        for key, label in card["details"].items():
            value = gpu.get(key)
            if key == "display_active" and value is not None:
                value = "Sim" if value else "Não"
            visible = self._has_value(value) if key != "display_active" else value is not None
            caption = card["detail_captions"].get(key)
            if caption is not None:
                caption.setVisible(visible)
            label.setVisible(visible)
            if visible:
                label.setText(self._text(value))

    @staticmethod
    def _has_value(value):
        if value is None:
            return False
        text = str(value).strip()
        return text not in ("", "N/D", "N/A", "[Not Supported]")

    def _set_metric(self, card, key, visible, text):
        label = card["metrics"][key]
        caption = card["metric_captions"].get(key)
        if caption is not None:
            caption.setVisible(visible)
        label.setVisible(visible)
        if visible:
            label.setText(text)

    def _create_summary_card(self, caption, value):
        frame = QFrame()
        frame.setObjectName("gpuSummaryCard")
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        label = QLabel(caption)
        label.setObjectName("gpuSummaryLabel")
        value_label = QLabel(value)
        value_label.setObjectName("gpuSummaryValue")
        layout.addWidget(label)
        layout.addWidget(value_label)
        frame.value_label = value_label
        return frame

    def _set_summary(self, count, load, memory):
        for key, value in (("count", count), ("load", load), ("memory", memory)):
            self.summary_cards[key].value_label.setText(value)

    def _update_summary(self, gpus):
        loads = [self._number(gpu.get("load")) for gpu in gpus]
        loads = [load for load in loads if load is not None]
        totals = [self._number(gpu.get("vram_total")) for gpu in gpus]
        totals = [total for total in totals if total is not None]
        load = f"{sum(loads) / len(loads):.1f}%" if loads else "N/D"
        memory = f"{sum(totals):.0f} MB" if totals else "N/D"
        self._set_summary(str(len(gpus)), load, memory)

    @staticmethod
    def _text(value, fallback="N/D"):
        return fallback if value is None or not str(value).strip() else str(value)

    @staticmethod
    def _number(value):
        try:
            return float(str(value).replace("%", "").split()[0].replace(",", "."))
        except (TypeError, ValueError, IndexError):
            return None
