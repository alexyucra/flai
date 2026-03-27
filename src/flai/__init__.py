"""
FLAI - Framework Local de AI
"""

from importlib.metadata import version

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
LOCALE_DIR = "i18n"
LOCALE_PATH = Path(__file__).parent / LOCALE_DIR
DOMAIN = "flai"

__version__ = version("flai")
__author__ = "Alex Yucra"
