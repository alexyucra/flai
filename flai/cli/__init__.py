# flai/cli/__init__.py
"""CLI do FLAI"""

import sys
from pathlib import Path

def setup_cli_logging(verbose: bool = False):
    """Configura logging para CLI"""
    from flai.core.logging import setup_logging
    
    log_level = "DEBUG" if verbose else "INFO"
    log_file = Path.home() / ".flai" / "logs" / "flai.log"
    
    setup_logging(
        log_level=log_level,
        log_file=log_file,
        console_output=True
    )

# Auto-configuração (opcional)
setup_cli_logging()

