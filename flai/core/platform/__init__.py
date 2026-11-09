"""Detecção e compatibilidade entre plataformas"""

from .detect import (
    get_platform,
    is_windows,
    is_linux,
    is_macos,
    get_path_separator,
    get_user_config_dir,
    get_user_cache_dir,
    get_user_log_dir,
    normalize_path,
    Platform
)

__all__ = [
    "get_platform",
    "is_windows", 
    "is_linux",
    "is_macos",
    "get_path_separator",
    "get_user_config_dir",
    "get_user_cache_dir",
    "get_user_log_dir",
    "normalize_path",
    "Platform"
]