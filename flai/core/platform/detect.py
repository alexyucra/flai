"""
Detecção de plataforma e utilitários cross-platform
"""
import sys
import os
from pathlib import Path
from enum import Enum
from typing import Optional

class Platform(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "darwin"
    UNKNOWN = "unknown"

def get_platform() -> Platform:
    """Detecta a plataforma atual"""
    system = sys.platform.lower()
    
    if system.startswith("win"):
        return Platform.WINDOWS
    elif system.startswith("linux"):
        return Platform.LINUX
    elif system.startswith("darwin"):
        return Platform.MACOS
    else:
        return Platform.UNKNOWN

def is_windows() -> bool:
    """Verifica se está no Windows"""
    return get_platform() == Platform.WINDOWS

def is_linux() -> bool:
    """Verifica se está no Linux"""
    return get_platform() == Platform.LINUX

def is_macos() -> bool:
    """Verifica se está no macOS"""
    return get_platform() == Platform.MACOS

def get_path_separator() -> str:
    """Retorna o separador de caminhos da plataforma"""
    return "\\" if is_windows() else "/"

def normalize_path(path: str) -> str:
    """
    Normaliza caminho para o formato da plataforma
    
    Converte / para \\ no Windows e vice-versa
    """
    if is_windows():
        return str(Path(path)).replace("/", "\\")
    else:
        return str(Path(path)).replace("\\", "/")

def get_user_config_dir(app_name: str = "flai") -> Path:
    """
    Retorna diretório de configuração do usuário
    
    - Windows: %APPDATA%\\flai
    - Linux: ~/.config/flai
    - macOS: ~/Library/Application Support/flai
    """
    if is_windows():
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    elif is_macos():
        base = Path.home() / "Library/Application Support"
    else:  # Linux
        base = Path.home() / ".config"
    
    config_dir = base / app_name
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_user_cache_dir(app_name: str = "flai") -> Path:
    """
    Retorna diretório de cache do usuário
    
    - Windows: %LOCALAPPDATA%\\flai\\cache
    - Linux: ~/.cache/flai
    - macOS: ~/Library/Caches/flai
    """
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        cache_dir = base / app_name / "cache"
    elif is_macos():
        base = Path.home() / "Library/Caches"
        cache_dir = base / app_name
    else:  # Linux
        base = Path.home() / ".cache"
        cache_dir = base / app_name
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def get_user_log_dir(app_name: str = "flai") -> Path:
    """
    Retorna diretório de logs do usuário
    
    - Windows: %LOCALAPPDATA%\\flai\\logs
    - Linux: ~/.local/share/flai/logs
    - macOS: ~/Library/Logs/flai
    """
    if is_windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
        log_dir = base / app_name / "logs"
    elif is_macos():
        base = Path.home() / "Library/Logs"
        log_dir = base / app_name
    else:  # Linux
        base = Path.home() / ".local/share"
        log_dir = base / app_name / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_system_temp_dir() -> Path:
    """Retorna diretório temporário do sistema"""
    import tempfile
    return Path(tempfile.gettempdir())