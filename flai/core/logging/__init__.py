"""Sistema de logging unificado do FLAI"""

from .logger import setup_logging, get_logger, log_error, log_warning, log_info, log_debug

__all__ = ["setup_logging", "get_logger", "log_error", "log_warning", "log_info", "log_debug"]