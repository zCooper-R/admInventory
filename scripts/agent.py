#!/usr/bin/env python3
"""
IT Inventory Agent — Python (cross-platform)
============================================================
Collects hardware info and sends to the IT Inventory API.
Works on Windows, Linux, macOS.

Requirements:
  pip install requests psutil

Configuration: set the variables in the CONFIGURATION block
or use environment variables:
  INVENTORY_API_URL, INVENTORY_API_KEY, INVENTORY_LOCATION_ID
============================================================
"""
import json
import logging
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("WARNING: psutil not installed. Some hardware info may be limited.")
    print("         Install with: pip install psutil")

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
API_URL     = os.environ.get("INVENTORY_API_URL",     "http://YOUR-SERVER-ADDRESS/api/v1/devices/sync/")
API_KEY     = os.environ.get("INVENTORY_API_KEY",     "change-me-before-production")
LOCATION_ID = os.environ.get("INVENTORY_LOCATION_ID", None)   # integer or None
LOG_FILE    = Path(os.environ.get("INVENTORY_LOG",    str(Path.home() / "it_inventory_agent.log")))
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def _run(cmd: list[str], default="") -> str:
    try:
        return subprocess.check_output(cmd, text=True, timeout=10).strip()
    except Exception:
        return default


def collect() -> dict:
    hostname = socket.gethostname()
    system   = platform.system()

    info = {
        "inventory_number": f"AUTO-{hostname}",
        "name":             hostname,
        "hostname":         hostname,
        "os":               f"{platform.system()} {platform.release()}".strip(),
        "serial_number":    "",
        "cpu":              "",
        "ram":              None,
        "storage_type":     "HDD",
        "storage_size":     None,
    }

    # ── CPU ──────────────────────────────────────────────────────────────────
    if system == "Windows":
        info["cpu"] = _run(
            ["wmic", "cpu", "get", "Name", "/value"],
        ).replace("Name=", "").strip()
        info["serial_number"] = _run(
            ["wmic", "bios", "get", "SerialNumber", "/value"],
        ).replace("SerialNumber=", "").strip()
        info["os"] = _run(
            ["wmic", "os", "get", "Caption", "/value"],
        ).replace("Caption=", "").strip()
    elif system == "Linux":
        try:
            cpu_info = Path("/proc/cpuinfo").read_text()
            for line in cpu_info.splitlines():
                if line.startswith("model name"):
                    info["cpu"] = line.split(":", 1)[1].strip()
                    break
        except Exception:
            pass
        info["serial_number"] = _run(["sudo", "dmidecode", "-s", "system-serial-number"])
    elif system == "Darwin":
        info["cpu"] = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        info["serial_number"] = _run(
            ["system_profiler", "SPHardwareDataType"],
        ).split("Serial Number")[-1].split(":")[1].strip() if "Serial" in _run(
            ["system_profiler", "SPHardwareDataType"]
        ) else ""

    # ── RAM ──────────────────────────────────────────────────────────────────
    if HAS_PSUTIL:
        info["ram"] = round(psutil.virtual_memory().total / (1024 ** 3))
    elif system == "Windows":
        raw = _run(["wmic", "computersystem", "get", "TotalPhysicalMemory", "/value"])
        try:
            info["ram"] = round(int(raw.replace("TotalPhysicalMemory=", "").strip()) / (1024 ** 3))
        except Exception:
            pass
    elif system == "Linux":
        try:
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal"):
                    info["ram"] = round(int(line.split()[1]) / (1024 ** 2))
                    break
        except Exception:
            pass

    # ── Disk ─────────────────────────────────────────────────────────────────
    if HAS_PSUTIL:
        disks = psutil.disk_partitions()
        total_gb = 0
        for d in disks:
            try:
                usage = psutil.disk_usage(d.mountpoint)
                total_gb += usage.total // (1024 ** 3)
            except Exception:
                pass
        if total_gb:
            info["storage_size"] = total_gb

    # Detect SSD on Linux via /sys
    if system == "Linux":
        ssd_found = hdd_found = False
        for dev_path in Path("/sys/block").glob("sd*"):
            rotational = (dev_path / "queue" / "rotational").read_text().strip()
            if rotational == "0":
                ssd_found = True
            else:
                hdd_found = True
        if ssd_found and hdd_found:
            info["storage_type"] = "Mixed"
        elif ssd_found:
            info["storage_type"] = "SSD"

    if LOCATION_ID:
        info["location_id"] = int(LOCATION_ID)

    # Clean up junk serial numbers
    junk = {"default string", "to be filled", "none", "system serial number", ""}
    if info.get("serial_number", "").lower() in junk:
        info["serial_number"] = ""

    return info


def sync(data: dict) -> bool:
    headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(API_URL, json=data, headers=headers, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        action = "CREATED" if result.get("created") else "UPDATED"
        device_id = result.get("device", {}).get("id", "?")
        log.info("SUCCESS (%s): Device ID %s", action, device_id)
        return True
    except requests.HTTPError as e:
        log.error("HTTP error: %s — %s", e.response.status_code, e.response.text[:200])
    except requests.ConnectionError:
        log.error("Cannot connect to %s — check network and server address", API_URL)
    except Exception as exc:
        log.error("Unexpected error: %s", exc)
    return False


if __name__ == "__main__":
    log.info("IT Inventory Agent starting")
    data = collect()
    log.info(
        "Collected: host=%s cpu=%s ram=%sGB storage=%s/%sGB os=%s",
        data["hostname"], data.get("cpu", "?"), data.get("ram"),
        data.get("storage_type"), data.get("storage_size"), data.get("os"),
    )
    success = sync(data)
    sys.exit(0 if success else 1)
