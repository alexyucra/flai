import psutil
import platform
import sys

def get_os():
    """Retorna o nome do sistema operacional em minúsculas"""
    return platform.system().lower()

def get_system_info():
    """Informações detalhadas do sistema"""
    try:
        ram_gb = round(psutil.virtual_memory().total / 1024**3)
    except:
        ram_gb = 0
    try:
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        ram_available = psutil.virtual_memory().available / (1024**3)

        recommendations = []
    
        if ram_available < 2:
            recommendations.append("⚠️  RAM baja (<2GB). Usando configuración optimizada.")
            recommendations.append("   • Modelo: phi3:mini con contexto reducido")
            recommendations.append("   • Respuestas más cortas")
        elif ram_available < 4:
            recommendations.append("ℹ️  RAM moderada (2-4GB).")
            recommendations.append("   • Modelo: phi3:mini normal")
        else:
            recommendations.append("✅ RAM suficiente (>4GB).")
            recommendations.append("   • Cualquier modelo funcionará bien")

        checklist = {
            "Sistema suportado": get_os() in ["linux", "darwin", "windows"],
            "RAM suficiente": ram_gb >= 8,
            "Python >= 3.10": True,
        }
        
        return {
            "cpu": {
                "count": cpu_count,
                "percent": cpu_percent
            },
            "ram": {
                "total_gb": round(ram.total / 1024**3, 1),
                "available_gb": round(ram.available / 1024**3, 1),
                "percent": ram.percent
            },
            "disk": {
                "total_gb": round(disk.total / 1024**3, 1),
                "free_gb": round(disk.free / 1024**3, 1),
                "percent": disk.percent
            },
            "os": {
                "name": platform.system(),
                "version": platform.version(),
                "release": platform.release()
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation()
            },
            "recommendations": recommendations,
            "checklist": checklist,
        }
    except Exception as e:
        return {"error": str(e)}