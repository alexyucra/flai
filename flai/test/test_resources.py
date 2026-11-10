"""Testes do ResourceGuard (RAM x contexto x tokens). Sem Ollama."""
from flai.core.resources import (
    ModelFootprint, RamSnapshot, ResourceGuard, estimate_tokens, optimized_model_name,
)
from flai.core.resources.memory import GB

# Metadados reais do qwen2.5-coder:7b (/api/show)
QWEN_SHOW = {"model_info": {
    "qwen2.attention.head_count": 28, "qwen2.attention.head_count_kv": 4,
    "qwen2.block_count": 28, "qwen2.context_length": 32768, "qwen2.embedding_length": 3584,
}}


def fp(loaded=0):
    return ModelFootprint.from_ollama("qwen2.5-coder:7b", QWEN_SHOW, int(4.7 * GB), loaded)


def guard(avail_gb, total_gb=16):
    return ResourceGuard(lambda: RamSnapshot(int(total_gb * GB), int(avail_gb * GB)))


def test_kv_cache_from_model_metadata():
    # 2 (K,V) * 28 camadas * 4 cabeças kv * 128 dim * 2 bytes
    assert fp().kv_bytes_per_token == 28 * 4 * 256 * 2


def test_plan_fits_configured_context_with_enough_ram():
    plan = guard(12).plan(fp(), configured_ctx=2048, num_predict=512)
    assert plan.fits and plan.effective_ctx == 2048 and plan.num_predict == 512
    assert plan.max_safe_ctx > 2048 and not plan.warnings


def test_plan_reduces_context_when_ram_is_low():
    plan = guard(7.0).plan(fp(), configured_ctx=32768, num_predict=512)
    assert plan.fits
    assert plan.effective_ctx < 32768 and plan.effective_ctx == plan.max_safe_ctx
    assert any("não cabe na RAM" in w for w in plan.warnings)


def test_plan_reports_insufficient_ram():
    plan = guard(4.0).plan(fp(), configured_ctx=2048, num_predict=512)
    assert not plan.fits
    assert "RAM insuficiente" in plan.warnings[0] and "modelo menor" in plan.warnings[0]


def test_loaded_model_memory_is_counted_back():
    # Com o modelo já carregado (5 GB em uso), a RAM livre menor não deve bloquear
    assert guard(3.0).plan(fp(loaded=int(5 * GB)), 2048, 512).fits


def test_prompt_over_context_suggests_increase_when_ram_allows():
    g = guard(12)
    plan = g.plan(fp(), 2048, 512)
    check = g.check_prompt(plan, prompt_tokens=3000)
    assert check.truncated and check.ram_allows
    assert check.suggested_ctx == 3584
    assert '"context_tokens"' in check.message and "3584" in check.message


def test_prompt_over_context_warns_when_ram_does_not_allow():
    g = guard(6.8)
    plan = g.plan(fp(), 2048, 512)
    check = g.check_prompt(plan, prompt_tokens=60000)
    assert check.truncated and not check.ram_allows
    assert "não permite aumentar" in check.message


def test_prompt_within_budget_has_no_message():
    g = guard(12)
    plan = g.plan(fp(), 2048, 512)
    assert g.check_prompt(plan, 1000).message is None


def test_fit_context_respects_budget():
    parts = ["a" * 320, "b" * 3200, "c" * 320]  # 100, 1000, 100 tokens
    text, cut = ResourceGuard.fit_context("", parts, budget_tokens=500)
    assert cut and text.startswith("a" * 320) and "cortado" in text
    assert estimate_tokens(text) <= 520


def test_optimized_model_name():
    assert optimized_model_name("qwen2.5-coder:7b", 2048) == "flai-qwen2.5-coder-7b:ctx2048"
    assert optimized_model_name("library/llama3.2:latest", 1024) == "flai-llama3.2:ctx1024"
