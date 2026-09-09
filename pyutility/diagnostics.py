import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass, asdict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import psutil

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_MODEL_PREFERENCES = (
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama-4-scout-17b-16e-instruct",
    "qwen/qwen3-32b",
)
IGNORED_PROCESS_NAMES = {"system idle process", "idle"}


def _safe_float(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _format_process_name(process):
    return process.get("name") or f"PID {process.get('pid', '?')}"


class SystemSnapshotCollector:
    """Collects a small, privacy-conscious snapshot without requiring admin rights."""

    def collect(self):
        memory = psutil.virtual_memory()
        disks = []
        seen = set()
        for partition in self._safe_partitions():
            mountpoint = partition.mountpoint
            if mountpoint in seen:
                continue
            seen.add(mountpoint)
            try:
                usage = psutil.disk_usage(mountpoint)
                disks.append({
                    "mountpoint": mountpoint,
                    "total_gb": round(usage.total / 1024 ** 3, 2),
                    "free_gb": round(usage.free / 1024 ** 3, 2),
                    "percent": _safe_float(usage.percent),
                })
            except (OSError, PermissionError):
                continue

        temperatures = []
        try:
            sensors = psutil.sensors_temperatures() or {}
            for sensor_name, entries in sensors.items():
                for entry in entries:
                    current = _safe_float(getattr(entry, "current", None))
                    if current is not None:
                        temperatures.append({
                            "sensor": getattr(entry, "label", None) or sensor_name,
                            "current": current,
                            "high": _safe_float(getattr(entry, "high", None)),
                            "critical": _safe_float(getattr(entry, "critical", None)),
                        })
        except (AttributeError, OSError, psutil.Error):
            pass

        processes = []
        for process in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = process.info
                process_name = (info.get("name") or "").strip().lower()
                if process_name in IGNORED_PROCESS_NAMES:
                    continue
                processes.append({
                    "pid": info.get("pid"),
                    "name": info.get("name") or "Desconhecido",
                    "cpu_percent": _safe_float(info.get("cpu_percent")) or 0.0,
                    "memory_percent": _safe_float(info.get("memory_percent")) or 0.0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        processes.sort(key=lambda item: (item["cpu_percent"], item["memory_percent"]), reverse=True)

        disk_io = self._safe_disk_io()
        startup_items = self._safe_startup_items()
        cpu_info = self._safe_cpu_info()
        return {
            "timestamp": time.time(),
            "cpu_percent": _safe_float(psutil.cpu_percent(interval=0.15)) or 0.0,
            "cpu_info": cpu_info,
            "memory_percent": _safe_float(memory.percent) or 0.0,
            "memory_available_gb": round(memory.available / 1024 ** 3, 2),
            "disks": disks,
            "temperatures": temperatures,
            "processes": processes[:40],
            "startup_count": len(startup_items) if startup_items is not None else None,
            "startup_items": startup_items or [],
            "disk_read_mb": disk_io[0],
            "disk_write_mb": disk_io[1],
        }

    @staticmethod
    def _safe_partitions():
        try:
            return psutil.disk_partitions(all=False)
        except (OSError, psutil.Error):
            return []

    @staticmethod
    def _safe_disk_io():
        try:
            counters = psutil.disk_io_counters()
            if counters is None:
                return None, None
            return round(counters.read_bytes / 1024 ** 2, 2), round(counters.write_bytes / 1024 ** 2, 2)
        except (OSError, psutil.Error):
            return None, None

    @staticmethod
    def _safe_startup_items():
        try:
            from backend import SystemMonitor

            items = SystemMonitor.get_startup_items()
            return [
                {
                    "name": item.get("name", "Desconhecido"),
                    "scope": item.get("scope", "N/D"),
                    "source": item.get("source", "N/D"),
                    "enabled": bool(item.get("enabled", True)),
                }
                for item in items
            ]
        except (ImportError, OSError, AttributeError, TypeError):
            return None

    @staticmethod
    def _safe_cpu_info():
        try:
            from backend import SystemMonitor

            data = SystemMonitor.get_cpu_detailed_info()
            return {
                "processor": data.get("processor", "N/D"),
                "architecture": data.get("architecture", "N/D"),
                "cores_physical": data.get("cores_physical"),
                "threads": data.get("threads"),
                "freq_current": data.get("freq_current", "N/D"),
                "freq_max": data.get("freq_max", "N/D"),
            }
        except (ImportError, OSError, AttributeError, TypeError):
            return {}


class HistoryStore:
    _write_lock = threading.Lock()

    def __init__(self, path=None, max_samples=500):
        default_path = os.path.join(
            os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
            "PyUtility",
            "diagnostics_history.json",
        )
        self.path = path or default_path
        self.max_samples = max_samples

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as history_file:
                data = json.load(history_file)
            return data if isinstance(data, list) else []
        except (OSError, ValueError, TypeError):
            return []

    def append(self, snapshot):
        with self._write_lock:
            samples = self.load()
            samples.append(snapshot)
            samples = samples[-self.max_samples:]
            try:
                directory = os.path.dirname(self.path)
                if directory:
                    os.makedirs(directory, exist_ok=True)
                temporary = f"{self.path}.tmp"
                with open(temporary, "w", encoding="utf-8") as history_file:
                    json.dump(samples, history_file, ensure_ascii=True)
                os.replace(temporary, self.path)
            except OSError:
                pass
        return samples


@dataclass
class Finding:
    title: str
    detail: str
    severity: str
    recommendation: str


class DiagnosticEngine:
    def __init__(self, cooldown_seconds=600):
        self.cooldown_seconds = cooldown_seconds
        self._last_alerts = {}

    def analyze(self, snapshot, history=None):
        snapshot = snapshot or {}
        history = history or []
        findings = []
        cpu = snapshot.get("cpu_percent", 0) or 0
        memory = snapshot.get("memory_percent", 0) or 0
        if cpu >= 90:
            process = (snapshot.get("processes") or [{}])[0]
            findings.append(Finding(
                "CPU elevada",
                f"A utilização está em {cpu:.0f}%; {_format_process_name(process)} é o processo com maior consumo observado.",
                "Anormal",
                "Verificar se o processo responsável termina uma tarefa ou permanece elevado.",
            ))
        if memory >= 85:
            process = max(snapshot.get("processes") or [{}], key=lambda item: item.get("memory_percent", 0))
            findings.append(Finding(
                "Memória elevada",
                f"A RAM está a {memory:.0f}%; {_format_process_name(process)} usa cerca de {process.get('memory_percent', 0):.1f}%.",
                "Necessita de atenção",
                "Fechar aplicações que não estão a ser usadas e verificar a tendência da memória.",
            ))
        for disk in snapshot.get("disks", []):
            if (disk.get("percent") or 0) >= 90:
                findings.append(Finding(
                    "Pouco espaço disponível",
                    f"A unidade {disk.get('mountpoint', 'N/D')} está {disk.get('percent', 0):.0f}% ocupada.",
                    "Necessita de atenção",
                    "Recomenda-se libertar espaço antes que aplicações e atualizações sejam afetadas.",
                ))
        for temperature in snapshot.get("temperatures", []):
            current = temperature.get("current") or 0
            limit = temperature.get("critical") or temperature.get("high") or 85
            if current >= limit or current >= 85:
                findings.append(Finding(
                    "Temperatura elevada",
                    f"{temperature.get('sensor', 'Sensor')} regista {current:.1f}°C.",
                    "Necessita de atenção",
                    "Verificar ventilação e o sistema de refrigeração.",
                ))
        if snapshot.get("startup_count") is not None and snapshot["startup_count"] > 12:
            findings.append(Finding(
                "Muitos programas no arranque",
                f"Foram encontrados {snapshot['startup_count']} itens de arranque no registo principal.",
                "Elevado consumo",
                "Rever a aba Arranque e desativar apenas programas que reconheça e não precise.",
            ))
        trend = self._trend(history, "memory_percent")
        if trend is not None and trend > 8 and len(history) >= 5:
            findings.append(Finding(
                "Tendência de memória crescente",
                f"A média recente de RAM subiu aproximadamente {trend:.0f} pontos percentuais.",
                "Possível causa",
                "Recomenda-se observar as aplicações em repouso e repetir a medição mais tarde.",
            ))
        cpu_trend = self._trend(history, "cpu_percent")
        if cpu_trend is not None and cpu_trend > 15 and len(history) >= 5:
            findings.append(Finding(
                "Tendência de CPU elevada",
                f"A média recente de CPU subiu aproximadamente {cpu_trend:.0f} pontos percentuais.",
                "Possível causa",
                "Recomenda-se confirmar a tendência com mais medições e observar os processos no topo.",
            ))
        score, breakdown = self.health_score(snapshot)
        alerts = self._alerts(findings)
        return {
            "findings": [asdict(item) for item in findings],
            "alerts": alerts,
            "score": score,
            "breakdown": breakdown,
            "trend": self.trends(history),
        }

    def health_score(self, snapshot):
        cpu = snapshot.get("cpu_percent", 0) or 0
        memory = snapshot.get("memory_percent", 0) or 0
        disks = snapshot.get("disks", [])
        temperatures = snapshot.get("temperatures", [])
        processes = snapshot.get("processes", [])
        disk_percent = max((item.get("percent", 0) or 0 for item in disks), default=0)
        temperature = max((item.get("current", 0) or 0 for item in temperatures), default=None)
        breakdown = {
            "Temperatura": self._band_score(temperature, 20, 60, 85),
            "RAM": self._band_score(memory, 20, 60, 90, reverse=True),
            "Armazenamento": self._band_score(disk_percent, 20, 70, 95, reverse=True),
            "Desempenho": self._band_score(cpu, 20, 70, 95, reverse=True),
            "Processos": max(0, 20 - sum(1 for item in processes[:10] if item.get("cpu_percent", 0) >= 80) * 3),
            "Arranque": self._startup_score(snapshot.get("startup_count")),
        }
        available = [value for value in breakdown.values() if value is not None]
        score = round(sum(available) / sum(20 for value in breakdown.values() if value is not None) * 100) if available else 0
        return score, breakdown

    @staticmethod
    def _startup_score(count):
        if count is None:
            return None
        return round(20 if count <= 6 else max(0, 20 - (count - 6) * 1.5))

    @staticmethod
    def _band_score(value, maximum, good, bad, reverse=False):
        if value is None:
            return None
        return round(maximum if value <= good else maximum * max(0, (bad - value) / (bad - good)))

    def trends(self, history):
        if len(history) < 5:
            return {"sufficient": False, "message": "Ainda não existem dados suficientes para identificar tendências."}
        return {
            "sufficient": True,
            "message": "Tendências baseadas nas últimas amostras; podem indicar uma alteração e não provam, por si só, uma falha.",
            "cpu": self._trend(history, "cpu_percent"),
            "memory": self._trend(history, "memory_percent"),
        }

    @staticmethod
    def _trend(history, key):
        values = [item.get(key) for item in history if item.get(key) is not None]
        if len(values) < 5:
            return None
        split = max(1, len(values) // 2)
        return round(sum(values[-split:]) / split - sum(values[:split]) / split, 2)

    def _alerts(self, findings):
        now = time.time()
        alerts = []
        for finding in findings:
            key = finding.title
            if now - self._last_alerts.get(key, 0) >= self.cooldown_seconds:
                alerts.append(finding.__dict__)
                self._last_alerts[key] = now
        return alerts


class LocalMaintenanceAssistant:
    def answer(self, question, snapshot, analysis, conversation=None):
        text = (question or "").lower()
        findings = analysis.get("findings", [])
        if any(word in text for word in ("lento", "lentidão", "devagar", "slow")):
            if snapshot.get("memory_percent", 0) >= 85:
                process = max(snapshot.get("processes") or [{}], key=lambda item: item.get("memory_percent", 0))
                return (f"A RAM está a {snapshot['memory_percent']:.0f}% e {_format_process_name(process)} "
                        f"usa aproximadamente {process.get('memory_percent', 0):.1f}%. Isto pode estar a contribuir para a lentidão. "
                        "Feche aplicações que não esteja a utilizar e volte a medir.")
            if snapshot.get("cpu_percent", 0) >= 90:
                process = (snapshot.get("processes") or [{}])[0]
                return (f"A CPU está a {snapshot['cpu_percent']:.0f}%; {_format_process_name(process)} é o principal consumidor observado. "
                        "Isto pode contribuir para a lentidão. Verifique se o consumo se mantém após alguns minutos.")
        if findings:
            return findings[0]["detail"] + " " + findings[0]["recommendation"]
        return "Não foi encontrada uma causa evidente nos dados atuais. Recomenda-se recolher mais amostras e verificar as tendências antes de concluir que existe um problema."


class AIProviderError(RuntimeError):
    """Raised when an optional remote AI provider cannot answer safely."""


class AIProvider:
    def answer(self, question, snapshot, analysis, conversation=None):
        raise NotImplementedError


class GroqProvider(AIProvider):
    """Small client for Groq's OpenAI-compatible chat API, with no SDK dependency."""

    def __init__(self, api_key, model=DEFAULT_GROQ_MODEL, timeout=12):
        self.api_key = self._clean_api_key(api_key)
        self.model = model.strip() if model and model.strip() else DEFAULT_GROQ_MODEL
        self.timeout = timeout

    @property
    def available(self):
        return bool(self.api_key)

    @staticmethod
    def _clean_api_key(api_key):
        key = (api_key or "").strip()
        if key.lower().startswith("bearer "):
            key = key[7:].strip()
        if len(key) >= 2 and key[0] == key[-1] and key[0] in ('"', "'", "`"):
            key = key[1:-1].strip()
        return key

    def answer(self, question, snapshot, analysis, conversation=None):
        if not self.available:
            raise AIProviderError("GROQ_API_KEY não está configurada.")

        context = _build_ai_context(snapshot, analysis)
        conversation_text = "\n".join(
            f"{item.get('role', 'user')}: {item.get('text', '')[:1200]}"
            for item in (conversation or [])[-8:]
            if item.get("text")
        )
        system_prompt = (
            "És um assistente de manutenção de computadores. Responde em português de Portugal, "
            "como uma resposta retomada e natural, não como uma lista genérica de dicas. "
            "Usa apenas os dados fornecidos e cita os valores concretos que sustentam a conclusão: "
            "CPU, RAM, discos, temperaturas, processos, arranque, score, alertas e tendências. "
            "Começa com 'Resumo' em 1-2 frases. Depois usa exatamente estas secções: "
            "'O que observei', 'O que pode significar', 'O que recomendo' e 'Limitações'. "
            "Relaciona a resposta com as mensagens anteriores quando isso for relevante. "
            "Distingue factos observados de hipóteses, não declares malware, não inventes métricas "
            "e diz claramente quando os dados não permitem concluir algo. "
            "Se o utilizador perguntar pelo espaço usado por aplicação, explica que o snapshot só tem "
            "espaço total por unidade e não inventes uma atribuição por processo. "
            "Não sugiras apagar ficheiros, terminar processos ou alterar configurações críticas "
            "sem confirmação explícita. Mantém detalhe suficiente para ser útil, mas evita repetir o JSON.\n\n"
        )
        user_prompt = (
            f"Pergunta do utilizador:\n{question.strip() or 'Faça uma análise geral do estado atual.'}\n\n"
            f"Conversa recente (pode estar vazia):\n{conversation_text or 'Sem conversa anterior.'}\n\n"
            f"Dados reais recolhidos localmente:\n{context}"
        )
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }).encode("utf-8")
        try:
            data = self._chat_completion(payload)
        except AIProviderError as error:
            if "não está disponível" not in str(error):
                raise
            data = self._try_available_models(payload)

        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise AIProviderError("A resposta da API Groq não contém texto utilizável.") from exc
        if not text:
            raise AIProviderError("A API Groq devolveu uma resposta vazia.")
        return text

    def _try_available_models(self, payload):
        models = self._discover_models()
        if not models:
            raise AIProviderError(
                f"O modelo Groq '{self.model}' não está disponível e não foi possível encontrar outro modelo acessível."
            )
        last_error = None
        for model in models:
            try:
                data = self._chat_completion(payload, model=model)
                self.model = model
                return data
            except AIProviderError as error:
                if "não está disponível" not in str(error):
                    raise
                last_error = error
        raise AIProviderError(f"Nenhum modelo Groq acessível respondeu: {last_error}")

    def _chat_completion(self, payload, model=None):
        model = model or self.model
        if model != self.model:
            payload_data = json.loads(payload.decode("utf-8"))
            payload_data["model"] = model
            payload = json.dumps(payload_data).encode("utf-8")
        url = "https://api.groq.com/openai/v1/chat/completions"
        request = Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "PyUtility/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429:
                raise AIProviderError(f"A API Groq atingiu o limite temporário de pedidos: {self._error_detail(exc)}") from exc
            if exc.code in (401, 403):
                raise AIProviderError(f"A API Groq recusou o pedido: {self._error_detail(exc)}") from exc
            if exc.code == 404:
                raise AIProviderError(f"O modelo Groq '{model}' não está disponível: {self._error_detail(exc)}") from exc
            raise AIProviderError(f"A API Groq devolveu HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise AIProviderError(f"Não foi possível contactar a API Groq: {exc}") from exc

    def _discover_models(self):
        request = Request(
            "https://api.groq.com/openai/v1/models",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "PyUtility/1.0",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise AIProviderError(f"Não foi possível listar os modelos Groq: {self._error_detail(exc)}") from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise AIProviderError(f"Não foi possível listar os modelos Groq: {exc}") from exc

        available = []
        for item in data.get("data", []) if isinstance(data, dict) else []:
            model_id = item.get("id")
            if model_id:
                available.append(model_id)
        preferred = [model for model in GROQ_MODEL_PREFERENCES if model in available]
        return preferred + [model for model in available if model not in preferred]

    @staticmethod
    def _error_detail(error):
        try:
            raw = error.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            if isinstance(data, dict):
                detail = data.get("error", data)
                if isinstance(detail, dict):
                    message = detail.get("message") or detail.get("type") or detail.get("code")
                    if message:
                        return str(message)
            if raw[:300]:
                return raw[:300]
            reason = getattr(error, "reason", None)
            return f"HTTP {error.code}" + (f" ({reason})" if reason else "")
        except (AttributeError, OSError, ValueError):
            reason = getattr(error, "reason", None)
            code = getattr(error, "code", "desconhecido")
            return f"HTTP {code}" + (f" ({reason})" if reason else "")


def _build_ai_context(snapshot, analysis):
    snapshot = snapshot or {}
    processes = [
        {
            "name": item.get("name", "Desconhecido"),
            "cpu_percent": item.get("cpu_percent"),
            "memory_percent": item.get("memory_percent"),
        }
        for item in (snapshot.get("processes") or [])[:15]
    ]
    context = {
        "cpu_percent": snapshot.get("cpu_percent"),
        "cpu_info": snapshot.get("cpu_info", {}),
        "memory_percent": snapshot.get("memory_percent"),
        "memory_available_gb": snapshot.get("memory_available_gb"),
        "disks": snapshot.get("disks", []),
        "temperatures": snapshot.get("temperatures", []),
        "processes": processes,
        "startup_count": snapshot.get("startup_count"),
        "startup_items": snapshot.get("startup_items", [])[:20],
        "disk_read_mb": snapshot.get("disk_read_mb"),
        "disk_write_mb": snapshot.get("disk_write_mb"),
        "local_findings": analysis.get("findings", []),
        "health_score": analysis.get("score"),
        "health_breakdown": analysis.get("breakdown", {}),
        "trends": analysis.get("trend", {}),
    }
    return json.dumps(context, ensure_ascii=False, separators=(",", ":"))


class MaintenanceAssistant:
    """AI facade: remote provider when configured, deterministic fallback otherwise."""

    def __init__(self, provider=None, local=None):
        self.provider = provider
        self.local = local or LocalMaintenanceAssistant()

    def answer(self, question, snapshot, analysis, conversation=None):
        if self.provider is not None:
            try:
                try:
                    text = self.provider.answer(question, snapshot, analysis, conversation)
                except TypeError:
                    text = self.provider.answer(question, snapshot, analysis)
                return {
                    "text": text,
                    "source": "AI Groq",
                    "error": None,
                }
            except AIProviderError as exc:
                return {
                    "text": self.local.answer(question, snapshot, analysis),
                    "source": "Diagnóstico local",
                    "error": str(exc),
                }
        return {
            "text": self.local.answer(question, snapshot, analysis),
            "source": "Diagnóstico local",
            "error": "Configure uma chave Groq para ativar a IA online.",
        }