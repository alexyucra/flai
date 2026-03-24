from typing import Dict, Tuple

import psutil
import platform

MIN_VERSION = 3.10
MIN_RAM = 8
OS_SUPORTED = ["Linux", "Darwin", "Windows"]


def _get_ram() -> int:
    return round(psutil.virtual_memory().total / 1024**3)

def _get_os() -> str:
    return platform.system()

def _get_version() -> float:
    major, minor, _ = platform.python_version_tuple()
    return float(major + '.' + minor)

def _system_values() -> Tuple[str, float, int]:
    return _get_os(), _get_version(), _get_ram()


def system_checklist() -> Dict[str, bool]:
    return {
        "Sistema suportado": _get_os() in OS_SUPORTED,
        "RAM suficiente": _get_ram() >= MIN_RAM,
        "Python >= 3.10": _get_version() >= MIN_VERSION ,
    }

def system_ram() -> int:
    return _get_ram()



def analyze_system() -> Dict[str, int | str | float]:
    os_family, version, ram_gb = _system_values()

    return {
        "ram_gb": ram_gb,
        "os": os_family,
        "python": version,
    }
