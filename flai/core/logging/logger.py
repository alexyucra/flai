"""
Logger configurável para FLAI
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Configuração padrão
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger_initialized = False
_log_file = None

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True
):
    """
    Configura o sistema de logging
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR)
        log_file: Caminho para arquivo de log (opcional)
        console_output: Se deve exibir no console
    """
    global _logger_initialized, _log_file
    
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configura logger root
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove handlers existentes
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        _log_file = log_file
    
    _logger_initialized = True
    
    # Log inicial
    logger = get_logger("flai")
    logger.info(f"Logging inicializado - Nível: {log_level}")
    if log_file:
        logger.info(f"Arquivo de log: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Retorna logger para um módulo específico
    
    Args:
        name: Nome do logger (geralmente __name__)
    
    Returns:
        Logger configurado
    """
    if not _logger_initialized:
        setup_logging()
    
    return logging.getLogger(name)


def log_error(logger: logging.Logger, message: str, exc_info: bool = True):
    """Log de erro com exception info opcional"""
    logger.error(message, exc_info=exc_info)


def log_warning(logger: logging.Logger, message: str):
    """Log de warning"""
    logger.warning(message)


def log_info(logger: logging.Logger, message: str):
    """Log de info"""
    logger.info(message)


def log_debug(logger: logging.Logger, message: str):
    """Log de debug"""
    logger.debug(message)


def get_log_file() -> Optional[Path]:
    """Retorna caminho do arquivo de log atual"""
    return _log_file