"""Gestão de RAM e limites de tokens para o modelo local."""

from .memory import (
    RamSnapshot,
    ModelFootprint,
    TokenPlan,
    PromptCheck,
    ResourceGuard,
    estimate_tokens,
    optimized_model_name,
)

__all__ = [
    "RamSnapshot",
    "ModelFootprint",
    "TokenPlan",
    "PromptCheck",
    "ResourceGuard",
    "estimate_tokens",
    "optimized_model_name",
]
