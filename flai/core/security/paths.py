"""Validação de nomes e caminhos (auditoria SEC-03)."""
import re
from pathlib import Path

_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class UnsafePathError(ValueError):
    """Nome ou caminho fora do permitido."""


def safe_name(name: str) -> str:
    """Aceita apenas letras, números, '_' e '-' (1 a 64 caracteres)."""
    if not isinstance(name, str) or not _NAME_RE.fullmatch(name):
        raise UnsafePathError(f"Nome inválido: {name!r}. Use apenas letras, números, '_' ou '-'.")
    return name


def safe_join(base: Path, *parts: str) -> Path:
    """Junta caminhos garantindo que o resultado permanece dentro de `base`."""
    base = Path(base).resolve()
    target = base.joinpath(*parts).resolve()
    if not target.is_relative_to(base):
        raise UnsafePathError(f"Caminho fora de {base}: {target}")
    return target
