"""Registro central de componentes FLAI"""

from .component_registry import ComponentRegistry, get_component, register_component

__all__ = ["ComponentRegistry", "get_component", "register_component"]