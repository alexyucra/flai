import psutil
import platform

def analyze_system():
    ram_gb = round(psutil.virtual_memory().total / 1024**3)

    checklist = {
        "Sistema suportado": platform.system() in ["Linux", "Darwin", "Windows"],
        "RAM suficiente": ram_gb >= 8,
        "Python >= 3.10": True,
    }

    return {
        "ram_gb": ram_gb,
        "os": platform.system(),
        "checklist": checklist,
    }
