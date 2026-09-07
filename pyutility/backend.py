import os
import sys
import json
import stat
import shutil
import time
import psutil
import platform
import socket
import requests
import subprocess
import ctypes
import re
import zipfile
from datetime import datetime
from html import escape

try:
    import GPUtil
except ImportError:
    GPUtil = None

class SystemMonitor:
    @staticmethod
    def is_admin():
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    @staticmethod
    def build_admin_powershell_command(command):
        if not command:
            raise ValueError("PowerShell command cannot be empty.")
        escaped = command.replace('"', '`"')
        return (
            "Start-Process powershell.exe -Verb RunAs -Wait "
            f"-ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"{escaped}\"'"
        )

    @staticmethod
    def run_elevated_powershell(command):
        powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
        admin_script = SystemMonitor.build_admin_powershell_command(command)
        return subprocess.run(
            [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", admin_script],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    @staticmethod
    def get_dashboard_info():
        try:
            uname = platform.uname()
            return {
                "os": f"{uname.system} {uname.release}",
                "hostname": uname.node,
                "cpu_usage": psutil.cpu_percent(interval=0.25),
                "ram_usage": psutil.virtual_memory().percent,
                "gpu_name": "Múltiplas (Ver aba GPU)",
                "gpu_usage": 0,
                "temps": "N/D"
            }
        except:
            return {"os": "Erro", "hostname": "Erro", "cpu_usage": 0, "ram_usage": 0}

    @staticmethod
    def get_cpu_detailed_info():
        freq = psutil.cpu_freq()
        processor_name = platform.processor() or platform.uname().processor or "N/D"
        physical = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 0
        logical = psutil.cpu_count(logical=True) or physical or 0

        cpu_info = {
            "processor": processor_name,
            "vendor": "N/D",
            "architecture": platform.machine() or "N/D",
            "cores_physical": physical,
            "threads": logical,
            "socket_count": 1,
            "freq_current": f"{freq.current:.0f} MHz" if freq else "N/D",
            "freq_max": f"{freq.max:.0f} MHz" if freq else "N/D",
            "cache_l2": "N/D",
            "temp": "N/D",
            "power_plan": "N/D",
        }

        try:
            powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            cmd = (
                "Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | "
                "Select-Object -First 1 Name,Manufacturer,Architecture,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,SocketDesignation | "
                "ConvertTo-Json -Compress"
            )
            res = subprocess.run(
                [powershell, "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
                timeout=5,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                if isinstance(data, dict):
                    cpu_info["processor"] = data.get("Name") or cpu_info["processor"]
                    cpu_info["vendor"] = data.get("Manufacturer") or cpu_info["vendor"]
                    cpu_info["architecture"] = data.get("Architecture") or cpu_info["architecture"]
                    cpu_info["cores_physical"] = data.get("NumberOfCores") or cpu_info["cores_physical"]
                    cpu_info["threads"] = data.get("NumberOfLogicalProcessors") or cpu_info["threads"]
                    cpu_info["socket_count"] = 1 if not data.get("SocketDesignation") else 1
                    if data.get("MaxClockSpeed"):
                        cpu_info["freq_max"] = f"{int(data['MaxClockSpeed'])} MHz"
        except Exception:
            pass

        return cpu_info

    @staticmethod
    def get_gpu_detailed_info():
        gpus = []

        try:
            powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
            cmd = (
                "Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue | "
                "Select-Object Name,Manufacturer,AdapterRAM,DriverVersion,CurrentHorizontalResolution,CurrentVerticalResolution | "
                "ConvertTo-Json -Compress"
            )
            res = subprocess.run(
                [powershell, "-NoProfile", "-Command", cmd],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                data = json.loads(res.stdout.strip())
                entries = data if isinstance(data, list) else [data]
                for item in entries:
                    if not item:
                        continue
                    ram = item.get("AdapterRAM") or 0
                    ram_mb = int(ram) // (1024 * 1024) if ram else 0
                    name = item.get("Name") or "GPU"
                    manufacturer = item.get("Manufacturer") or "N/D"
                    name_upper = name.upper()
                    if "AMD" in name_upper or "RADEON" in name_upper:
                        gpu_type = "AMD Radeon"
                    elif "NVIDIA" in name_upper or "NVIDIA" in manufacturer.upper():
                        gpu_type = "NVIDIA Dedicada"
                    else:
                        gpu_type = manufacturer.strip() if manufacturer != "N/D" else "Integrada/Outra"
                    horizontal = item.get("CurrentHorizontalResolution") or "N/D"
                    vertical = item.get("CurrentVerticalResolution") or "N/D"
                    gpus.append({
                        "name": name,
                        "vendor": manufacturer,
                        "type": gpu_type,
                        "vram_total": f"{ram_mb} MB" if ram_mb else "Dinâmica (Sistema)",
                        "vram_used": "N/D",
                        "load": "N/D",
                        "temp": "N/D",
                        "driver_version": item.get("DriverVersion") or "N/D",
                        "resolution": f"{horizontal}x{vertical}",
                    })
        except Exception:
            pass

        if GPUtil is not None:
            try:
                for gpu in GPUtil.getGPUs():
                    live_data = {
                        "name": gpu.name or "GPU",
                        "vendor": "NVIDIA" if "nvidia" in (gpu.name or "").lower() else "N/D",
                        "type": "NVIDIA Dedicada" if "nvidia" in (gpu.name or "").lower() else "GPU",
                        "vram_total": f"{gpu.memoryTotal:.0f} MB" if gpu.memoryTotal is not None else "N/D",
                        "vram_used": f"{gpu.memoryUsed:.0f} MB" if gpu.memoryUsed is not None else "N/D",
                        "vram_free": f"{gpu.memoryFree:.0f} MB" if gpu.memoryFree is not None else "N/D",
                        "load": f"{gpu.load * 100:.1f}" if gpu.load is not None else "N/D",
                        "temp": f"{gpu.temperature:.1f}°C" if gpu.temperature is not None else "N/D",
                        "driver_version": "N/D",
                        "resolution": "N/D",
                        "gpu_id": str(gpu.id),
                        "uuid": gpu.uuid or "N/D",
                        "serial": getattr(gpu, "serial", None) or "N/D",
                        "display_active": getattr(gpu, "display_active", None),
                        "fan_speed": f"{gpu.fan:.1f}%" if getattr(gpu, "fan", None) is not None else "N/D",
                        "power_draw": f"{gpu.powerDraw:.1f} W" if getattr(gpu, "powerDraw", None) is not None else "N/D",
                        "power_limit": f"{gpu.powerLimit:.1f} W" if getattr(gpu, "powerLimit", None) is not None else "N/D",
                        "clock_graphics": f"{gpu.gpu_clock:.0f} MHz" if getattr(gpu, "gpu_clock", None) is not None else "N/D",
                        "clock_memory": f"{gpu.memory_clock:.0f} MHz" if getattr(gpu, "memory_clock", None) is not None else "N/D",
                    }
                    matching = next(
                        (item for item in gpus if item["name"].lower() in live_data["name"].lower()
                         or live_data["name"].lower() in item["name"].lower()),
                        None,
                    )
                    if matching is None:
                        gpus.append(live_data)
                    else:
                        matching.update({key: value for key, value in live_data.items() if value != "N/D"})
            except Exception:
                pass

        try:
            res = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu,driver_version", "--format=csv,noheader,nounits"],
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=3,
            )
            lines = [line.strip() for line in res.splitlines() if line.strip()]
            for i, line in enumerate(lines):
                d = [p.strip() for p in line.split(',')]
                if len(d) < 6:
                    continue
                if i < len(gpus):
                    gpus[i]["name"] = d[0]
                    gpus[i]["vram_total"] = f"{d[1]} MB"
                    gpus[i]["vram_used"] = f"{d[2]} MB"
                    gpus[i]["load"] = d[3]
                    gpus[i]["temp"] = f"{d[4]}°C"
                    gpus[i]["driver_version"] = d[5]
                    gpus[i]["type"] = "NVIDIA Dedicada"
                else:
                    gpus.append({
                        "name": d[0],
                        "vendor": "NVIDIA",
                        "type": "NVIDIA Dedicada",
                        "vram_total": f"{d[1]} MB",
                        "vram_used": f"{d[2]} MB",
                        "load": d[3],
                        "temp": f"{d[4]}°C",
                        "driver_version": d[5],
                        "resolution": "N/D",
                    })
        except Exception:
            pass

        if not gpus:
            try:
                cmd = "powershell -NoProfile -Command \"Get-CimInstance Win32_VideoController | Select-Object Name\""
                res_ps = subprocess.check_output(
                    cmd,
                    encoding="utf-8",
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=3,
                )
                lines = [l.strip() for l in res_ps.strip().split('\n') if l.strip()]
                for name in lines[1:]:
                    if not any(gpu['name'].lower() in name.lower() for gpu in gpus):
                        g_type = "AMD Radeon" if "AMD" in name.upper() or "RADEON" in name.upper() else "Integrada/Outra"
                        gpus.append({
                            "name": name,
                            "vendor": "N/D",
                            "type": g_type,
                            "vram_total": "Dinâmica (Sistema)",
                            "vram_used": "N/D",
                            "load": "0",
                            "temp": "N/D",
                            "driver_version": "N/D",
                            "resolution": "N/D",
                        })
            except Exception:
                pass

        return gpus

    @staticmethod
    def save_system_report(path):
        def value(item, key, fallback="N/D"):
            result = item.get(key, fallback) if isinstance(item, dict) else fallback
            return fallback if result is None or str(result).strip() == "" else result

        def cell(item):
            return f"<td>{escape(str(item))}</td>"

        def powershell_data(command):
            try:
                output = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", command],
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
                data = json.loads(output) if output.strip() else []
                return data if isinstance(data, list) else [data]
            except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
                return []

        def detail_rows(item, fields):
            return "".join(
                f"<tr>{cell(label)}{cell(value(item, key))}</tr>"
                for key, label in fields
            )

        try:
            uname = platform.uname()
            memory = psutil.virtual_memory()
            boot_time = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
            cpu = SystemMonitor.get_cpu_detailed_info() or {}
            gpus = SystemMonitor.get_gpu_detailed_info() or []
            network = SystemMonitor.get_network_info() or {}
            processes = SystemMonitor.get_processes() or []
            devices = SystemMonitor.get_devices() or []
            system_data = powershell_data(
                "Get-CimInstance Win32_ComputerSystemProduct | "
                "Select-Object Vendor,Name,Version,IdentifyingNumber,UUID | ConvertTo-Json -Compress"
            )
            board_data = powershell_data(
                "Get-CimInstance Win32_BaseBoard | "
                "Select-Object Manufacturer,Product,Version,SerialNumber | ConvertTo-Json -Compress"
            )
            bios_data = powershell_data(
                "Get-CimInstance Win32_BIOS | "
                "Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate,SerialNumber,Version | ConvertTo-Json -Compress"
            )
            cpu_hardware = powershell_data(
                "Get-CimInstance Win32_Processor | "
                "Select-Object Name,Manufacturer,MaxClockSpeed,CurrentClockSpeed,L2CacheSize,L3CacheSize,NumberOfCores,NumberOfLogicalProcessors,SocketDesignation | ConvertTo-Json -Compress"
            )
            os_data = powershell_data(
                "Get-CimInstance Win32_OperatingSystem | "
                "Select-Object Caption,Version,BuildNumber,OSArchitecture,SerialNumber,InstallDate | ConvertTo-Json -Compress"
            )
            memory_modules = powershell_data(
                "Get-CimInstance Win32_PhysicalMemory | "
                "Select-Object DeviceLocator,Manufacturer,PartNumber,Capacity,Speed,SerialNumber,SMBIOSMemoryType | ConvertTo-Json -Compress"
            )
            physical_drives = powershell_data(
                "Get-CimInstance Win32_DiskDrive | "
                "Select-Object Model,SerialNumber,InterfaceType,MediaType,Size,FirmwareRevision,Status | ConvertTo-Json -Compress"
            )
            adapters = powershell_data(
                "Get-CimInstance Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True' | "
                "Select-Object Description,MACAddress,IPAddress,DefaultIPGateway,DHCPEnabled | ConvertTo-Json -Compress"
            )
            batteries = powershell_data(
                "Get-CimInstance Win32_Battery | "
                "Select-Object Name,Manufacturer,DeviceID,EstimatedChargeRemaining,BatteryStatus,DesignVoltage | ConvertTo-Json -Compress"
            )
            monitors = powershell_data(
                "Get-CimInstance Win32_DesktopMonitor | "
                "Select-Object Name,MonitorManufacturer,MonitorType,ScreenHeight,ScreenWidth,PNPDeviceID | ConvertTo-Json -Compress"
            )
            audio_devices = powershell_data(
                "Get-CimInstance Win32_SoundDevice | "
                "Select-Object Name,Manufacturer,Status,PNPDeviceID | ConvertTo-Json -Compress"
            )

            def size_text(value_bytes):
                try:
                    return f"{int(value_bytes) / (1024 ** 3):.1f} GB"
                except (TypeError, ValueError):
                    return "N/D"

            disk_rows = []
            seen_disks = set()
            for partition in psutil.disk_partitions(all=False):
                if partition.mountpoint in seen_disks:
                    continue
                seen_disks.add(partition.mountpoint)
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_rows.append(
                        "<tr>" + "".join(cell(item) for item in (
                            partition.device,
                            partition.mountpoint,
                            partition.fstype or "N/D",
                            f"{usage.total / (1024 ** 3):.1f} GB",
                            f"{usage.used / (1024 ** 3):.1f} GB",
                            f"{usage.free / (1024 ** 3):.1f} GB",
                            f"{usage.percent:.1f}%",
                        )) + "</tr>"
                    )
                except (OSError, PermissionError):
                    continue

            gpu_rows = []
            for gpu in gpus:
                gpu_rows.append(
                    "<tr>" + "".join(cell(value(gpu, key)) for key in (
                        "name", "type", "driver_version", "load", "temp",
                        "vram_used", "vram_total", "resolution",
                    )) + "</tr>"
                )

            process_rows = []
            for process in sorted(
                processes,
                key=lambda item: float(item.get("cpu_percent") or 0),
                reverse=True,
            )[:30]:
                process_rows.append(
                    "<tr>" + "".join(cell(value(process, key)) for key in (
                        "pid", "name", "cpu_percent", "memory_percent",
                    )) + "</tr>"
                )

            connection_rows = []
            for connection in network.get("conns", [])[:50]:
                connection_rows.append(
                    "<tr>" + "".join(cell(value(connection, key)) for key in (
                        "local", "remote", "status",
                    )) + "</tr>"
                )

            device_rows = []
            for device in devices:
                device_rows.append(
                    "<tr>" + "".join(cell(value(device, key)) for key in (
                        "name", "class", "status", "instance_id", "problem",
                    )) + "</tr>"
                )

            module_rows = []
            for module in memory_modules:
                module_rows.append(
                    "<tr>" + "".join(cell(item) for item in (
                        value(module, "DeviceLocator"), value(module, "Manufacturer"),
                        value(module, "PartNumber"), size_text(module.get("Capacity")),
                        value(module, "Speed"), value(module, "SerialNumber"),
                    )) + "</tr>"
                )

            drive_rows = []
            for drive in physical_drives:
                drive_rows.append(
                    "<tr>" + "".join(cell(item) for item in (
                        value(drive, "Model"), value(drive, "SerialNumber"),
                        value(drive, "InterfaceType"), value(drive, "MediaType"),
                        size_text(drive.get("Size")), value(drive, "FirmwareRevision"),
                        value(drive, "Status"),
                    )) + "</tr>"
                )

            adapter_rows = []
            for adapter in adapters:
                adapter_rows.append(
                    "<tr>" + "".join(cell(item) for item in (
                        value(adapter, "Description"), value(adapter, "MACAddress"),
                        ", ".join(adapter.get("IPAddress") or []),
                        ", ".join(adapter.get("DefaultIPGateway") or []),
                        value(adapter, "DHCPEnabled"),
                    )) + "</tr>"
                )

            battery_rows = []
            for battery in batteries:
                battery_rows.append(
                    "<tr>" + "".join(cell(value(battery, key)) for key in (
                        "Name", "Manufacturer", "DeviceID", "EstimatedChargeRemaining",
                        "BatteryStatus", "DesignVoltage",
                    )) + "</tr>"
                )

            report = f"""<!DOCTYPE html>
<html lang="pt-PT"><head><meta charset="utf-8">
<title>Relatório do sistema - {escape(uname.node)}</title>
<style>
body {{ font-family: Segoe UI, Arial, sans-serif; color: #202124; margin: 32px; }}
h1 {{ color: #1769aa; margin-bottom: 4px; }} h2 {{ color: #1769aa; border-bottom: 2px solid #d8e8f5; padding-bottom: 6px; margin-top: 28px; }}
.meta {{ color: #5f6368; margin-bottom: 24px; }} table {{ border-collapse: collapse; width: 100%; margin: 10px 0 20px; }}
th, td {{ border: 1px solid #d7dce1; padding: 7px 9px; text-align: left; font-size: 13px; }}
th {{ background: #eaf3fa; color: #174a6e; }} tr:nth-child(even) {{ background: #f7f9fb; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }}
.card {{ border: 1px solid #d7dce1; padding: 12px; }} .label {{ color: #5f6368; font-size: 12px; }} .number {{ font-size: 20px; font-weight: 600; }}
</style></head><body>
<h1>Relatório completo do computador</h1>
<div class="meta">Gerado em {escape(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}</div>
<h2>Sistema</h2><table><tr><th>Campo</th><th>Valor</th></tr>
<tr>{cell("Sistema operativo")}{cell(f"{uname.system} {uname.release} ({uname.version})")}</tr>
<tr>{cell("Computador")}{cell(uname.node)}</tr><tr>{cell("Arquitetura")}{cell(uname.machine)}</tr>
<tr>{cell("Processador")}{cell(value(cpu, "processor"))}</tr><tr>{cell("Arranque")}{cell(boot_time)}</tr></table>
<h2>Identificação e firmware</h2>
<table><tr><th>Campo</th><th>Valor</th></tr>
{detail_rows(system_data[0] if system_data else {}, (("Vendor", "Fabricante"), ("Name", "Modelo"), ("Version", "Versão"), ("IdentifyingNumber", "Número de identificação"), ("UUID", "UUID")))}
{detail_rows(os_data[0] if os_data else {}, (("Caption", "Edição do Windows"), ("Version", "Versão"), ("BuildNumber", "Build"), ("OSArchitecture", "Arquitetura"), ("SerialNumber", "Número de série"), ("InstallDate", "Data de instalação")))}
</table>
<table><tr><th>Motherboard</th><th>Valor</th></tr>
{detail_rows(board_data[0] if board_data else {}, (("Manufacturer", "Fabricante"), ("Product", "Modelo"), ("Version", "Versão"), ("SerialNumber", "Número de série")))}
</table>
<table><tr><th>BIOS</th><th>Valor</th></tr>
{detail_rows(bios_data[0] if bios_data else {}, (("Manufacturer", "Fabricante"), ("SMBIOSBIOSVersion", "Versão"), ("ReleaseDate", "Data de lançamento"), ("SerialNumber", "Número de série"), ("Version", "Versão do sistema")))}
</table>
<div class="cards"><div class="card"><div class="label">CPU atual</div><div class="number">{escape(str(psutil.cpu_percent(interval=0.25)))}%</div></div>
<div class="card"><div class="label">Memória usada</div><div class="number">{escape(str(memory.percent))}%</div></div>
<div class="card"><div class="label">Núcleos / threads</div><div class="number">{escape(str(value(cpu, "cores_physical")))} / {escape(str(value(cpu, "threads")))}</div></div></div>
<h2>CPU</h2><table><tr><th>Fabricante</th><th>Arquitetura</th><th>Frequência atual</th><th>Frequência máxima</th></tr>
<tr>{cell(value(cpu, "vendor"))}{cell(value(cpu, "architecture"))}{cell(value(cpu, "freq_current"))}{cell(value(cpu, "freq_max"))}</tr></table>
<table><tr><th>Modelo</th><th>Clock atual</th><th>Clock máximo</th><th>L2</th><th>L3</th><th>Socket</th></tr>
{detail_rows(cpu_hardware[0] if cpu_hardware else {}, (("Name", "Modelo"), ("CurrentClockSpeed", "Clock atual (MHz)"), ("MaxClockSpeed", "Clock máximo (MHz)"), ("L2CacheSize", "Cache L2 (KB)"), ("L3CacheSize", "Cache L3 (KB)"), ("SocketDesignation", "Socket")))}
</table>
<h2>GPU</h2><table><tr><th>Nome</th><th>Tipo</th><th>Driver</th><th>Carga</th><th>Temperatura</th><th>VRAM usada</th><th>VRAM total</th><th>Resolução</th></tr>
{"".join(gpu_rows) or '<tr><td colspan="8">Nenhuma placa de vídeo detetada.</td></tr>'}</table>
<h2>Memória e discos</h2><table><tr><th>Total</th><th>Usada</th><th>Livre</th><th>Percentagem usada</th></tr>
<tr>{cell(f"{memory.total / (1024 ** 3):.1f} GB")}{cell(f"{memory.used / (1024 ** 3):.1f} GB")}{cell(f"{memory.available / (1024 ** 3):.1f} GB")}{cell(f"{memory.percent:.1f}%")}</tr></table>
<table><tr><th>Dispositivo</th><th>Ponto de montagem</th><th>Formato</th><th>Total</th><th>Usado</th><th>Livre</th><th>Uso</th></tr>
{"".join(disk_rows) or '<tr><td colspan="7">Nenhum disco disponível.</td></tr>'}</table>
<h2>Unidades físicas</h2><table><tr><th>Modelo</th><th>Número de série</th><th>Interface</th><th>Tipo</th><th>Tamanho</th><th>Firmware</th><th>Estado</th></tr>
{"".join(drive_rows) or '<tr><td colspan="7">Nenhuma unidade física disponível.</td></tr>'}</table>
<h2>Rede</h2><table><tr><th>IP local</th><th>IP público</th></tr><tr>{cell(value(network, "local"))}{cell(value(network, "public"))}</tr></table>
<table><tr><th>Adaptador</th><th>MAC</th><th>IP</th><th>Gateway</th><th>DHCP</th></tr>
{"".join(adapter_rows) or '<tr><td colspan="5">Nenhum adaptador disponível.</td></tr>'}</table>
<table><tr><th>Local</th><th>Remoto</th><th>Estado</th></tr>{"".join(connection_rows) or '<tr><td colspan="3">Sem ligações disponíveis.</td></tr>'}</table>
<h2>Bateria</h2><table><tr><th>Nome</th><th>Fabricante</th><th>ID</th><th>Carga</th><th>Estado</th><th>Voltagem</th></tr>
{"".join(battery_rows) or '<tr><td colspan="6">Nenhuma bateria detetada.</td></tr>'}</table>
<h2>Monitor</h2><table><tr><th>Nome</th><th>Fabricante</th><th>Tipo</th><th>Resolução</th><th>ID PnP</th></tr>
{"".join("<tr>" + "".join(cell(item) for item in (value(monitor, "Name"), value(monitor, "MonitorManufacturer"), value(monitor, "MonitorType"), f"{value(monitor, 'ScreenWidth')}x{value(monitor, 'ScreenHeight')}", value(monitor, "PNPDeviceID"))) + "</tr>" for monitor in monitors) or '<tr><td colspan="5">Nenhum monitor disponível.</td></tr>'}</table>
<h2>Áudio</h2><table><tr><th>Dispositivo</th><th>Fabricante</th><th>Estado</th><th>ID PnP</th></tr>
{"".join("<tr>" + "".join(cell(value(audio, key)) for key in ("Name", "Manufacturer", "Status", "PNPDeviceID")) + "</tr>" for audio in audio_devices) or '<tr><td colspan="4">Nenhum dispositivo de áudio disponível.</td></tr>'}</table>
<h2>Dispositivos Plug and Play</h2><table><tr><th>Dispositivo</th><th>Classe</th><th>Estado</th><th>ID de instância</th><th>Problema</th></tr>
{"".join(device_rows) or '<tr><td colspan="5">Nenhum dispositivo disponível.</td></tr>'}</table>
<h2>Processos com maior uso de CPU</h2><table><tr><th>PID</th><th>Nome</th><th>CPU %</th><th>Memória %</th></tr>
{"".join(process_rows) or '<tr><td colspan="4">Sem processos disponíveis.</td></tr>'}</table>
</body></html>"""

            with open(path, "w", encoding="utf-8") as report_file:
                report_file.write(report)
            return True, f"Relatório guardado em {path}"
        except Exception as exc:
            return False, f"Não foi possível gerar o relatório: {exc}"

    @staticmethod
    def get_system_health_info():
        disks = []
        seen_mountpoints = set()
        for partition in psutil.disk_partitions(all=False):
            if partition.mountpoint in seen_mountpoints:
                continue
            seen_mountpoints.add(partition.mountpoint)
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device or partition.mountpoint,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype or "N/D",
                    "total_gb": usage.total / (1024 ** 3),
                    "used_gb": usage.used / (1024 ** 3),
                    "free_gb": usage.free / (1024 ** 3),
                    "percent": usage.percent,
                    "smart": "Não disponível",
                })
            except (OSError, PermissionError):
                continue

        temperatures = []
        try:
            for sensor_name, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    if entry.current is not None:
                        temperatures.append({
                            "sensor": entry.label or sensor_name,
                            "current": entry.current,
                            "high": entry.high,
                            "critical": entry.critical,
                        })
        except (AttributeError, OSError):
            pass

        memory = psutil.virtual_memory()
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.25),
            "memory_percent": memory.percent,
            "memory_total_gb": memory.total / (1024 ** 3),
            "memory_available_gb": memory.available / (1024 ** 3),
            "disks": disks,
            "temperatures": temperatures,
        }

    @staticmethod
    def get_wifi_info():
        result = {"ssid": "N/D", "signal": "N/D", "channel": "N/D", "band": "N/D", "interface": "N/D"}
        try:
            output = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
            patterns = {
                "ssid": r"^\s*SSID\s*:\s*(.+)$",
                "signal": r"^\s*Signal\s*:\s*(.+)$",
                "channel": r"^\s*Channel\s*:\s*(.+)$",
                "band": r"^\s*Radio type\s*:\s*(.+)$",
                "interface": r"^\s*Name\s*:\s*(.+)$",
            }
            for line in output.splitlines():
                for key, pattern in patterns.items():
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        result[key] = match.group(1).strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return result

    @staticmethod
    def ping_host(host):
        if not host or not host.strip():
            return {"host": "", "latency_ms": None, "status": "Destino vazio"}
        try:
            output = subprocess.check_output(
                ["ping", "-n", "1", "-w", "1500", host.strip()],
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=3,
            )
            match = re.search(r"[=<]\s*(\d+)\s*ms", output, re.IGNORECASE)
            return {"host": host.strip(), "latency_ms": int(match.group(1)) if match else None, "status": "Online"}
        except (OSError, subprocess.SubprocessError):
            return {"host": host.strip(), "latency_ms": None, "status": "Offline"}

    @staticmethod
    def get_startup_items():
        items = []
        try:
            import winreg
            locations = (
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "Utilizador"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "Computador"),
            )
            for root, key_path, scope in locations:
                try:
                    with winreg.OpenKey(root, key_path) as key:
                        for index in range(winreg.QueryInfoKey(key)[1]):
                            name, command, _ = winreg.EnumValue(key, index)
                            items.append({"name": name, "command": command, "scope": scope, "source": "Registo", "enabled": True})
                except OSError:
                    pass
                try:
                    with winreg.OpenKey(root, key_path + "-Disabled") as key:
                        for index in range(winreg.QueryInfoKey(key)[1]):
                            name, command, _ = winreg.EnumValue(key, index)
                            items.append({"name": name, "command": command, "scope": scope, "source": "Registo", "enabled": False})
                except OSError:
                    pass
        except ImportError:
            pass
        for scope, folder in (("Utilizador", os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")),
                              ("Computador", os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs\Startup"))):
            try:
                for name in os.listdir(folder):
                    enabled = not name.endswith(".disabled")
                    items.append({"name": name, "command": os.path.join(folder, name), "scope": scope, "source": "Pasta Startup", "enabled": enabled})
            except OSError:
                continue
        return items

    @staticmethod
    def set_startup_item_enabled(item, enabled):
        try:
            if item.get("source") == "Registo":
                import winreg
                root = winreg.HKEY_CURRENT_USER if item.get("scope") == "Utilizador" else winreg.HKEY_LOCAL_MACHINE
                active_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                disabled_path = r"Software\Microsoft\Windows\CurrentVersion\Run-Disabled"
                if enabled:
                    with winreg.OpenKey(root, disabled_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as source:
                        command, _ = winreg.QueryValueEx(source, item["name"])
                        with winreg.CreateKeyEx(root, active_path, 0, winreg.KEY_WRITE) as target:
                            winreg.SetValueEx(target, item["name"], 0, winreg.REG_SZ, command)
                        winreg.DeleteValue(source, item["name"])
                else:
                    with winreg.OpenKey(root, active_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as source:
                        command, _ = winreg.QueryValueEx(source, item["name"])
                        with winreg.CreateKeyEx(root, disabled_path, 0, winreg.KEY_WRITE) as target:
                            winreg.SetValueEx(target, item["name"], 0, winreg.REG_SZ, command)
                        winreg.DeleteValue(source, item["name"])
                return True, "Item de arranque atualizado."

            path = item.get("command", "")
            if enabled and path.endswith(".disabled"):
                os.rename(path, path[:-9])
            elif not enabled and os.path.exists(path):
                os.rename(path, path + ".disabled")
            return True, "Item de arranque atualizado."
        except (OSError, PermissionError, KeyError) as exc:
            return False, str(exc)

    @staticmethod
    def get_devices():
        devices = []
        try:
            command = (
                "Get-PnpDevice -PresentOnly:$false -ErrorAction SilentlyContinue | "
                "Select-Object FriendlyName,Class,Status,InstanceId,Present,ProblemCode | "
                "ConvertTo-Json -Compress"
            )
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", command],
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            data = json.loads(output) if output.strip() else []
            for item in data if isinstance(data, list) else [data]:
                if item:
                    devices.append({
                        "name": item.get("FriendlyName") or "Dispositivo sem nome",
                        "class": item.get("Class") or "Outros",
                        "status": item.get("Status") or "Desconhecido",
                        "instance_id": item.get("InstanceId") or "",
                        "present": item.get("Present", True),
                        "problem": item.get("ProblemCode", 0) or 0,
                    })
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            pass
        return devices

    @staticmethod
    def set_device_enabled(instance_id, enabled):
        command_name = "Enable-PnpDevice" if enabled else "Disable-PnpDevice"
        command = f"{command_name} -InstanceId '{instance_id.replace(chr(39), chr(39) * 2)}' -Confirm:$false"
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            if result.returncode == 0:
                return True, "Dispositivo atualizado."
            return False, result.stderr.strip() or "O Windows recusou a operação."
        except (OSError, subprocess.SubprocessError) as exc:
            return False, str(exc)

    @staticmethod
    def open_device_properties(instance_id):
        try:
            subprocess.Popen(
                ["rundll32.exe", "devmgr.dll,DeviceProperties_RunDLL", instance_id],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True, "Propriedades abertas."
        except OSError:
            try:
                subprocess.Popen(["devmgmt.msc"], creationflags=subprocess.CREATE_NO_WINDOW)
                return True, "Gestor de Dispositivos aberto."
            except OSError as exc:
                return False, str(exc)

    @staticmethod
    def get_security_info():
        antivirus = "Indisponível"
        try:
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", "(Get-MpComputerStatus).AntivirusEnabled"],
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            ).strip().lower()
            antivirus = "Ativo" if output == "true" else "Inativo"
        except (OSError, subprocess.SubprocessError):
            pass
        listening = []
        try:
            for connection in psutil.net_connections(kind="inet"):
                if connection.status == psutil.CONN_LISTEN and connection.laddr:
                    listening.append({"address": connection.laddr.ip, "port": connection.laddr.port, "pid": connection.pid or "N/D"})
        except (psutil.Error, OSError):
            pass
        return {"antivirus": antivirus, "listening": listening[:100], "processes": SystemMonitor.get_processes()}

    @staticmethod
    def create_config_backup(path):
        try:
            config_names = ("settings.json", "config.json")
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                included = []
                for name in config_names:
                    if os.path.isfile(name):
                        archive.write(name, name)
                        included.append(name)
                archive.writestr("backup-info.txt", "PAMonitor configuration backup\n" + "\n".join(included))
            return True, f"Backup criado em {path}"
        except (OSError, zipfile.BadZipFile) as exc:
            return False, str(exc)

    @staticmethod
    def restore_config_backup(path):
        allowed = {"settings.json", "config.json"}
        try:
            with zipfile.ZipFile(path, "r") as archive:
                members = [member for member in archive.namelist() if member in allowed]
                for member in members:
                    with archive.open(member) as source, open(member, "wb") as target:
                        shutil.copyfileobj(source, target)
            return True, f"Backup restaurado ({len(members)} ficheiro(s))."
        except (OSError, zipfile.BadZipFile) as exc:
            return False, str(exc)

    @staticmethod
    def get_recent_logs(limit=50):
        try:
            output = subprocess.check_output(
                ["wevtutil", "qe", "System", f"/c:{limit}", "/rd:true", "/f:text"],
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=8,
            )
            return output.strip() or "Sem eventos recentes."
        except (OSError, subprocess.SubprocessError) as exc:
            return f"Logs do Windows indisponíveis: {exc}"

    @staticmethod
    def export_recent_logs(path):
        try:
            with open(path, "w", encoding="utf-8") as log_file:
                log_file.write(SystemMonitor.get_recent_logs())
            return True, f"Logs exportados para {path}"
        except OSError as exc:
            return False, str(exc)

    @staticmethod
    def get_driver_info():
        drivers = []
        try:
            output = subprocess.check_output(
                ["driverquery", "/fo", "csv", "/nh"],
                text=True,
                encoding="mbcs",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            for line in output.splitlines():
                fields = next(__import__("csv").reader([line]), [])
                if len(fields) >= 4:
                    drivers.append({"name": fields[0], "display_name": fields[1], "type": fields[2], "state": fields[3]})
        except (OSError, subprocess.SubprocessError, UnicodeError):
            pass
        return drivers

    @staticmethod
    def get_processes():
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try: procs.append(p.info)
            except: continue
        return procs

    @staticmethod
    def kill_process(pid):
        try:
            if pid is None:
                return False

            proc = psutil.Process(pid)
            if not proc.is_running():
                return True

            proc.terminate()
            try:
                proc.wait(timeout=2)
                return True
            except psutil.TimeoutExpired:
                pass

            if os.name == "nt":
                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(pid), "/F", "/T"],
                        capture_output=True,
                        text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        check=False,
                    )
                    return True
                except Exception:
                    pass

            try:
                proc.kill()
                return True
            except Exception:
                return False
        except Exception:
            return False

    @staticmethod
    def get_network_info():
        try:
            local = socket.gethostbyname(socket.gethostname())
            public = requests.get('https://api.ipify.org', timeout=0.5).text
        except: local, public = "127.0.0.1", "Offline"
        
        conns = []
        try:
            for conn in psutil.net_connections(kind='inet')[:20]:
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "LISTENING"
                conns.append({"local": laddr, "remote": raddr, "status": conn.status})
        except: pass
        return {"local": local, "public": public, "conns": conns}

    @staticmethod
    def get_active_window_process():
        try:
            procs = sorted(psutil.process_iter(['name', 'cpu_percent']), 
                           key=lambda x: x.info['cpu_percent'], reverse=True)
            for p in procs:
                n = p.info['name']
                if n and n not in ['System Idle Process', 'idle', 'python.exe', 'pythonw.exe']:
                    return n
            return "Ambiente de Trabalho"
        except: return "N/D"

    @staticmethod
    def _median(values):
        if not values:
            return 0.0
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2 == 0:
            return (ordered[mid - 1] + ordered[mid]) / 2.0
        return ordered[mid]

    @staticmethod
    def ensure_console_streams():
        if sys.stdout is None:
            sys.stdout = open(os.devnull, "w", encoding="utf-8")
        if sys.stderr is None:
            sys.stderr = open(os.devnull, "w", encoding="utf-8")

    @staticmethod
    def run_speed_test(iterations=3):
        SystemMonitor.ensure_console_streams()
        print(f"[DEBUG][SpeedTest] starting run_speed_test(iterations={iterations})")
        result = {
            "download_mbps": 0.0,
            "upload_mbps": 0.0,
            "ping_ms": 0,
            "status": "Erro",
            "error": ""
        }

        try:
            import speedtest

            print("[DEBUG][SpeedTest] speedtest-cli imported successfully")
            samples = []
            for i in range(iterations):
                print(f"[DEBUG][SpeedTest] iteration {i + 1}/{iterations} starting")
                st = speedtest.Speedtest()
                st.get_best_server()
                ping = float(st.results.ping or 0)
                download_bps = float(st.download())
                upload_bps = float(st.upload())

                sample = {
                    "ping_ms": ping,
                    "download_mbps": download_bps / 1_000_000,
                    "upload_mbps": upload_bps / 1_000_000
                }
                samples.append(sample)
                print(f"[DEBUG][SpeedTest] iteration {i + 1}/{iterations} sample -> ping={ping}ms, download={sample['download_mbps']:.2f}Mbps, upload={sample['upload_mbps']:.2f}Mbps")

            if samples:
                result["ping_ms"] = SystemMonitor._median([s["ping_ms"] for s in samples])
                result["download_mbps"] = SystemMonitor._median([s["download_mbps"] for s in samples])
                result["upload_mbps"] = SystemMonitor._median([s["upload_mbps"] for s in samples])
                result["status"] = "OK"
                print(f"[DEBUG][SpeedTest] median result -> ping={result['ping_ms']}ms, download={result['download_mbps']:.2f}Mbps, upload={result['upload_mbps']:.2f}Mbps")
                return result

        except Exception as exc:
            result["error"] = str(exc)
            print(f"[DEBUG][SpeedTest] exception: {exc}")

        print(f"[DEBUG][SpeedTest] returning failed result: {result}")
        return result

    @staticmethod
    def ensure_chocolatey():
        print("[DEBUG][Misc] checking if Chocolatey is installed")
        try:
            res = subprocess.run(["choco", "--version"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if res.returncode == 0:
                print("[DEBUG][Misc] Chocolatey already installed")
                return True, "Chocolatey já está instalado."
        except Exception as exc:
            print(f"[DEBUG][Misc] choco not found: {exc}")
            pass

        script = (
            "Set-ExecutionPolicy Bypass -Scope Process -Force; "
            "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; "
            "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        )

        try:
            print("[DEBUG][Misc] attempting to install Chocolatey with UAC elevation")
            if not SystemMonitor.is_admin():
                proc = SystemMonitor.run_elevated_powershell(script)
            else:
                powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
                proc = subprocess.run([powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if proc.returncode == 0:
                print("[DEBUG][Misc] Chocolatey installed successfully")
                return True, "Chocolatey foi instalado com sucesso."
            err = proc.stderr.strip() or proc.stdout.strip() or "Falha ao instalar o Chocolatey."
            print(f"[DEBUG][Misc] Chocolatey install failed: {err}")
            return False, err
        except Exception as exc:
            print(f"[DEBUG][Misc] error while installing Chocolatey: {exc}")
            return False, str(exc)

    @staticmethod
    def install_choco_package(package_name, command=None):
        print(f"[DEBUG][Misc] install_choco_package called for package: {package_name}, command={command}")
        ok, message = SystemMonitor.ensure_chocolatey()
        if not ok:
            print(f"[DEBUG][Misc] cannot install {package_name}: {message}")
            return False, message

        try:
            if command:
                install_command = command.strip()
            else:
                install_command = f'choco install "{package_name}" --yes --no-progress'

            print(f"[DEBUG][Misc] running elevated command: {install_command}")
            if not SystemMonitor.is_admin():
                proc = SystemMonitor.run_elevated_powershell(install_command)
            elif command:
                powershell = r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"
                proc = subprocess.run(
                    [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", install_command],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                proc = subprocess.run(
                    ["choco", "install", package_name, "--yes", "--no-progress"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            if proc.returncode == 0:
                print(f"[DEBUG][Misc] package {package_name} install succeeded")
                return True, f"{package_name} foi instalado com sucesso."
            err = proc.stderr.strip() or proc.stdout.strip() or "Erro ao instalar o pacote."
            print(f"[DEBUG][Misc] package {package_name} install failed: {err}")
            return False, err
        except Exception as exc:
            print(f"[DEBUG][Misc] exception while installing {package_name}: {exc}")
            return False, str(exc)

    @staticmethod
    def safe_remove_path(path):
        try:
            if not os.path.exists(path):
                return True

            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path, ignore_errors=True)
                return not os.path.exists(path)

            mode = os.stat(path).st_mode
            if not mode & stat.S_IWRITE:
                os.chmod(path, mode | stat.S_IWRITE)

            os.remove(path)
            return not os.path.exists(path)
        except Exception:
            return False

    @staticmethod
    def clean_temp_folders():
        print("[DEBUG][Misc] starting clean_temp_folders")
        paths = []
        for key in ("TEMP", "TMP"):
            value = os.environ.get(key)
            if value:
                paths.append(value)

        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            paths.append(os.path.join(user_profile, "AppData", "Local", "Temp"))

        print(f"[DEBUG][Misc] temp paths discovered: {paths}")
        seen = set()
        cleaned = 0
        ignored = []

        for path in paths:
            if not path or path in seen or not os.path.exists(path):
                continue
            seen.add(path)

            try:
                with os.scandir(path) as entries:
                    for entry in entries:
                        full_path = entry.path
                        try:
                            if entry.is_dir(follow_symlinks=False):
                                if not SystemMonitor.safe_remove_path(full_path):
                                    raise OSError(f"Could not remove directory: {full_path}")
                            else:
                                if not SystemMonitor.safe_remove_path(full_path):
                                    raise OSError(f"Could not remove file: {full_path}")
                            cleaned += 1
                            print(f"[DEBUG][Misc] removed: {full_path}")
                        except Exception as exc:
                            message = str(exc)
                            if "WinError 32" in message or "being used by another process" in message or "used by another process" in message:
                                ignored.append(full_path)
                                print(f"[DEBUG][Misc] ignored in-use temp file: {full_path}")
                                continue
                            print(f"[DEBUG][Misc] failed to remove {full_path}: {exc}")
            except Exception as exc:
                message = str(exc)
                if "WinError 32" in message or "being used by another process" in message:
                    ignored.append(path)
                    print(f"[DEBUG][Misc] ignored in-use temp directory: {path}")
                    continue
                print(f"[DEBUG][Misc] failed to iterate {path}: {exc}")

        if ignored:
            print(f"[DEBUG][Misc] clean_temp_folders finished with ignored in-use files: {ignored[:3]}")
            return True, f"Limpesa concluída ({cleaned} itens removidos; alguns ficheiros em uso foram ignorados)."

        print(f"[DEBUG][Misc] clean_temp_folders finished successfully: {cleaned} items removed")
        return True, f"Pastas temporárias limpas com sucesso ({cleaned} itens removidos)."

    @staticmethod
    def run_disk_cleanup():
        cleanmgr = r"C:\Windows\System32\cleanmgr.exe"
        print(f"[DEBUG][Misc] run_disk_cleanup checking path: {cleanmgr}")
        if not os.path.exists(cleanmgr):
            print("[DEBUG][Misc] cleanmgr not found")
            return False, "Disk Cleanup não foi encontrado no sistema."

        try:
            print("[DEBUG][Misc] launching cleanmgr /sagerun:1")
            subprocess.run([cleanmgr, "/sagerun:1"], creationflags=subprocess.CREATE_NO_WINDOW)
            print("[DEBUG][Misc] cleanmgr launched successfully")
            return True, "Disk Cleanup foi iniciado."
        except Exception as exc:
            print(f"[DEBUG][Misc] exception while running cleanmgr: {exc}")
            return False, str(exc)

    @staticmethod
    def flush_dns_cache():
        try:
            result = subprocess.run(
                ["ipconfig", "/flushdns"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return True, "Cache DNS limpa com sucesso."
            return False, result.stderr.strip() or "Não foi possível limpar o cache DNS."
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def check_system_files():
        try:
            result = subprocess.run(
                ["sfc", "/scannow"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                return True, "Verificação dos ficheiros do sistema concluída."
            return False, result.stdout.strip() or result.stderr.strip() or "A verificação dos ficheiros do sistema falhou."
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def open_windows_update():
        try:
            os.startfile("ms-settings:windowsupdate")
            return True, "Windows Update aberto."
        except (AttributeError, OSError) as exc:
            return False, str(exc)