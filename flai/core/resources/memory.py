"""
ResourceGuard — limita o contexto do modelo local pela RAM disponível.

Memória que o Ollama usa para um modelo:
    pesos (tamanho do arquivo do modelo)
  + KV cache  = num_ctx * 2 (K e V) * camadas * cabeças_kv * dim_cabeça * 2 bytes (f16)
  + buffers de cálculo (aprox. fixo + proporcional)

O FLAI:
  1. mede a RAM livre (psutil) e o "peso" do modelo (/api/show, /api/tags);
  2. calcula o maior num_ctx que cabe com folga para o sistema;
  3. usa um modelo derivado (`flai-<base>:ctx<N>`) com esse contexto reduzido;
  4. antes de cada pergunta estima os tokens do prompt, corta o contexto se
     necessário e avisa quando vale aumentar `context_tokens` na configuração —
     sugerindo só valores que a RAM suporta.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

GB = 1024 ** 3
MB = 1024 ** 2

# Folga deixada para o sistema operacional e outros programas
OS_RESERVE_BYTES = int(1.5 * GB)
# Folga mínima aceita quando a RAM está apertada (roda com aviso em vez de bloquear)
MIN_OS_RESERVE_BYTES = int(0.25 * GB)
# Buffers de cálculo do llama.cpp (aprox.; medido ~0,3 GB no qwen2.5-coder:3b)
COMPUTE_OVERHEAD_BYTES = int(0.4 * GB)
# KV cache por token quando o modelo não informa a arquitetura
FALLBACK_KV_BYTES_PER_TOKEN = 128 * 1024

MIN_CTX = 512
CTX_STEP = 512
# Média de caracteres por token para código/português (estimativa conservadora)
CHARS_PER_TOKEN = 3.2


def estimate_tokens(text: str) -> int:
    """Estimativa rápida de tokens (sem tokenizer). Arredonda para cima."""
    if not text:
        return 0
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def _round_down(value: int, step: int = CTX_STEP) -> int:
    return max(0, (value // step) * step)


def _round_up(value: int, step: int = CTX_STEP) -> int:
    return int(math.ceil(value / step) * step)


def optimized_model_name(base_model: str, num_ctx: int) -> str:
    """Nome do modelo derivado: qwen2.5-coder:7b + 2048 -> flai-qwen2.5-coder-7b:ctx2048"""
    base = base_model.split("/")[-1]
    if base.endswith(":latest"):
        base = base[: -len(":latest")]
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", base).strip("-").lower()
    return f"flai-{slug}:ctx{num_ctx}"


@dataclass
class RamSnapshot:
    total_bytes: int
    available_bytes: int

    @property
    def total_gb(self) -> float:
        return self.total_bytes / GB

    @property
    def available_gb(self) -> float:
        return self.available_bytes / GB

    @classmethod
    def take(cls) -> "RamSnapshot":
        import psutil
        vm = psutil.virtual_memory()
        return cls(total_bytes=int(vm.total), available_bytes=int(vm.available))


@dataclass
class ModelFootprint:
    name: str
    weights_bytes: int
    kv_bytes_per_token: int
    max_context: int
    loaded_bytes: int = 0  # memória já ocupada se o modelo estiver carregado

    @classmethod
    def from_ollama(cls, name: str, show: Dict, size_bytes: int, loaded_bytes: int = 0) -> "ModelFootprint":
        info = (show or {}).get("model_info", {}) or {}

        def pick(suffix: str) -> Optional[int]:
            for k, v in info.items():
                if k.endswith(suffix) and isinstance(v, (int, float)):
                    return int(v)
            return None

        layers = pick(".block_count")
        heads = pick(".attention.head_count")
        kv_heads = pick(".attention.head_count_kv") or heads
        emb = pick(".embedding_length")
        key_len = pick(".attention.key_length")
        val_len = pick(".attention.value_length")
        ctx = pick(".context_length") or 4096

        if layers and kv_heads and (key_len or (emb and heads)):
            k_dim = key_len or emb // heads
            v_dim = val_len or k_dim
            kv = layers * kv_heads * (k_dim + v_dim) * 2  # f16
        else:
            kv = FALLBACK_KV_BYTES_PER_TOKEN
        return cls(name=name, weights_bytes=int(size_bytes or 0), kv_bytes_per_token=int(kv),
                   max_context=int(ctx), loaded_bytes=int(loaded_bytes or 0))


@dataclass
class TokenPlan:
    """Limites efetivos para a sessão."""
    model: str
    configured_ctx: int
    effective_ctx: int
    max_safe_ctx: int
    num_predict: int
    ram: RamSnapshot
    footprint: ModelFootprint
    fits: bool
    warnings: List[str] = field(default_factory=list)

    @property
    def prompt_budget(self) -> int:
        """Tokens disponíveis para o prompt (contexto menos a resposta)."""
        return max(0, self.effective_ctx - self.num_predict)

    def summary(self) -> str:
        return (f"RAM livre {self.ram.available_gb:.1f}/{self.ram.total_gb:.1f} GB · "
                f"modelo {self.footprint.weights_bytes / GB:.1f} GB · "
                f"contexto {self.effective_ctx} tokens (configurado {self.configured_ctx}, "
                f"máx. seguro {self.max_safe_ctx}) · resposta até {self.num_predict}")


@dataclass
class PromptCheck:
    prompt_tokens: int
    needed_ctx: int
    effective_ctx: int
    truncated: bool
    suggested_ctx: Optional[int]
    ram_allows: bool
    message: Optional[str]


class ResourceGuard:
    """Calcula limites de contexto seguros e valida cada prompt."""

    def __init__(self, ram_provider: Callable[[], RamSnapshot] = RamSnapshot.take,
                 os_reserve: int = OS_RESERVE_BYTES):
        self.ram_provider = ram_provider
        self.os_reserve = os_reserve

    # ------------------------------------------------------------ cálculo
    def max_safe_ctx(self, fp: ModelFootprint, ram: RamSnapshot) -> int:
        # Se o modelo já está carregado, a memória dele já saiu de "available"
        budget = ram.available_bytes + fp.loaded_bytes - self.os_reserve
        budget -= fp.weights_bytes + COMPUTE_OVERHEAD_BYTES
        if budget <= 0:
            return 0
        ctx = _round_down(int(budget / max(fp.kv_bytes_per_token, 1)))
        return min(ctx, fp.max_context)

    def plan(self, fp: ModelFootprint, configured_ctx: int, num_predict: int) -> TokenPlan:
        ram = self.ram_provider()
        safe = self.max_safe_ctx(fp, ram)
        warnings: List[str] = []
        fits = safe >= MIN_CTX
        if not fits and self.os_reserve > MIN_OS_RESERVE_BYTES:
            # A folga do sistema é uma preferência, não um limite: com pouca RAM, roda
            # com folga mínima (o Windows ainda pode paginar) e avisa, em vez de bloquear.
            tight = ResourceGuard(lambda: ram, MIN_OS_RESERVE_BYTES).max_safe_ctx(fp, ram)
            if tight >= MIN_CTX:
                safe, fits = tight, True
                warnings.append(f"Pouca RAM livre ({ram.available_gb:.1f} GB): rodando com folga mínima. "
                                "Feche programas se o sistema ficar lento.")

        if not fits:
            effective = MIN_CTX
            need_gb = (fp.weights_bytes + COMPUTE_OVERHEAD_BYTES + self.os_reserve
                       + MIN_CTX * fp.kv_bytes_per_token - fp.loaded_bytes) / GB
            warnings.append(
                f"RAM insuficiente para '{fp.name}': livre {ram.available_gb:.1f} GB, "
                f"necessário ~{need_gb:.1f} GB. Feche programas ou use um modelo menor "
                "(ex.: qwen2.5-coder:1.5b, deepseek-coder:1.3b)."
            )
        else:
            effective = min(_round_down(configured_ctx) or MIN_CTX, safe)
            if effective < configured_ctx:
                warnings.append(
                    f"context_tokens={configured_ctx} não cabe na RAM livre "
                    f"({ram.available_gb:.1f} GB); usando {effective}."
                )

        predict = min(num_predict, max(effective // 2, 128))
        if fits and predict < num_predict:
            warnings.append(f"max_tokens reduzido de {num_predict} para {predict} (metade do contexto).")

        return TokenPlan(model=fp.name, configured_ctx=configured_ctx, effective_ctx=effective,
                         max_safe_ctx=safe, num_predict=predict, ram=ram, footprint=fp,
                         fits=fits, warnings=warnings)

    def check_prompt(self, plan: TokenPlan, prompt_tokens: int) -> PromptCheck:
        needed = prompt_tokens + plan.num_predict
        if needed <= plan.effective_ctx:
            return PromptCheck(prompt_tokens, needed, plan.effective_ctx, False, None, True, None)

        suggested = _round_up(needed)
        ram_allows = suggested <= plan.max_safe_ctx
        if ram_allows:
            msg = (f"Prompt com ~{prompt_tokens} tokens + resposta {plan.num_predict} excede o contexto "
                   f"de {plan.effective_ctx}. O contexto foi cortado. Aumente \"context_tokens\" em "
                   f".flai/config.json para {suggested} (a RAM livre permite até {plan.max_safe_ctx}).")
        else:
            msg = (f"Prompt com ~{prompt_tokens} tokens excede o contexto de {plan.effective_ctx} e a RAM "
                   f"livre ({plan.ram.available_gb:.1f} GB) não permite aumentar além de {plan.max_safe_ctx}. "
                   "O contexto foi cortado. Faça perguntas mais específicas, libere memória ou use um modelo menor.")
        return PromptCheck(prompt_tokens, needed, plan.effective_ctx, True, suggested, ram_allows, msg)

    # --------------------------------------------------------- montagem
    @staticmethod
    def fit_context(fixed: str, context_parts: List[str], budget_tokens: int) -> tuple[str, bool]:
        """Inclui partes do contexto em ordem até o orçamento; corta a última se preciso."""
        remaining = budget_tokens - estimate_tokens(fixed)
        kept: List[str] = []
        truncated = False
        for part in context_parts:
            cost = estimate_tokens(part)
            if cost <= remaining:
                kept.append(part)
                remaining -= cost
                continue
            truncated = True
            if remaining > 64:
                kept.append(part[: int(remaining * CHARS_PER_TOKEN)] + "\n[... cortado por limite de tokens]")
            break
        return "\n".join(kept), truncated
