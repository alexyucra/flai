"""Validação de URLs de fontes de contexto (auditoria SEC-04)."""
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"https"}


class UnsafeURLError(ValueError):
    """URL não permitida."""


def validate_remote_url(url: str) -> str:
    """Permite apenas https:// com host. Bloqueia file://, ext::, opções git (-...)."""
    if not isinstance(url, str) or not url or url.startswith("-"):
        raise UnsafeURLError(f"URL inválida: {url!r}")
    if "::" in url.split("/", 1)[0]:
        raise UnsafeURLError(f"Transporte git não permitido: {url!r}")
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES or not parsed.hostname:
        raise UnsafeURLError(f"Apenas URLs https:// são permitidas: {url!r}")
    return url
