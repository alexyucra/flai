"""
Provedor de LLM EXTERNO (Groq) — RESERVADO, NÃO UTILIZADO nesta versão.

Auditoria PRIV-01: o FLAI usa somente o Ollama local até estar finalizado.
`flai/flai.yml` é apenas uma configuração de referência para um modelo novo
ou externo. `get_llm()` recusa a execução enquanto o bloqueio estiver ativo.
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from flai.source.langchain.monitor import IAMonitor

# flai/flai.yml (raiz do pacote)
PACKAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(PACKAGE_DIR, "flai.yml")

# Trava de desenvolvimento: só remova quando o FLAI estiver finalizado
# e o provedor externo tiver sido autorizado pela TI.
EXTERNAL_PROVIDERS_LOCKED = True


class ExternalProviderDisabled(RuntimeError):
    """Provedor externo desativado."""


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def is_external_enabled(cfg: dict | None = None) -> bool:
    if EXTERNAL_PROVIDERS_LOCKED:
        return False
    cfg = cfg if cfg is not None else load_config()
    return bool(cfg.get("ia", {}).get("enabled")) and cfg.get("status") != "reserved"


def get_llm(monitor: IAMonitor | None = None):
    cfg = load_config()
    if not is_external_enabled(cfg):
        raise ExternalProviderDisabled(
            "Provedor externo desativado: flai.yml é reservado e não é usado até o FLAI "
            "estar finalizado. Use o Ollama local."
        )

    # Imports tardios: dependências opcionais (extra "remote")
    from dotenv import load_dotenv
    from langchain_groq import ChatGroq

    load_dotenv(os.path.join(PACKAGE_DIR, ".env"))
    ia = cfg["ia"]
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model=ia["model"],
        temperature=ia.get("temperature", 0.2),
        max_tokens=ia.get("max_tokens", 800),
        callbacks=[monitor] if monitor else [],
    )
