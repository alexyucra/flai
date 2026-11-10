"""Allowlist de módulos carregáveis como agentes (auditoria SEC-01)."""
import os
import re

BUILTIN_AGENT_PREFIX = "flai.core.agents."
_MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")


class UnsafeModuleError(ValueError):
    """Módulo fora da allowlist."""


def custom_agents_allowed() -> bool:
    """Agentes customizados (código Python do projeto) ficam desativados por padrão."""
    return os.getenv("FLAI_ALLOW_CUSTOM_AGENTS", "0") == "1"


def validate_module_path(module_path: str) -> str:
    """Aceita apenas módulos internos `flai.core.agents.*`."""
    if not isinstance(module_path, str) or not _MODULE_RE.fullmatch(module_path):
        raise UnsafeModuleError(f"module_path inválido: {module_path!r}")
    if not module_path.startswith(BUILTIN_AGENT_PREFIX):
        raise UnsafeModuleError(
            f"module_path fora da allowlist ({BUILTIN_AGENT_PREFIX}*): {module_path!r}"
        )
    return module_path
