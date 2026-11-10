"""
Teste E2E: FLAI + CLI Fleting + Ollama local (sem rede).

Requer: `fleting` instalado no mesmo Python e Ollama rodando com o modelo
indicado em FLAI_TEST_MODEL (padrão: qwen2.5-coder:7b). Caso contrário, é pulado.

    uv run pytest flai/test/test_e2e_fleting_ollama.py -v -s
"""
import asyncio
import os
import subprocess

import pytest

from flai.core.executors.fleting_executor import find_fleting_binary

MODEL = os.getenv("FLAI_TEST_MODEL", "qwen2.5-coder:7b")


def _ollama_models():
    try:
        import requests
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
        return {m["name"] for m in r.json().get("models", [])}
    except Exception:
        return set()


FLETING = find_fleting_binary()
pytestmark = pytest.mark.skipif(FLETING is None, reason="fleting não instalado")


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    work = tmp_path_factory.mktemp("e2e")
    subprocess.run([FLETING, "init", "loja"], cwd=work, capture_output=True,
                   env={**os.environ, "PYTHONIOENCODING": "utf-8"}, timeout=120)
    proj = work / "loja"
    assert (proj / ".fleting").exists(), "fleting init falhou"
    return proj


@pytest.fixture(scope="module")
def router(project):
    from flai.core.agents.router_agent import RouterAgent
    asked = []
    r = RouterAgent(project, model=MODEL, confirm=lambda q: asked.append(q) or True)
    r.asked = asked
    return r


def route(router, text):
    return asyncio.run(router.route(text))


def test_crud_full_flow(router, project):
    r = route(router, "criar crud de produtos com nome, preco")
    assert r["success"], r
    assert (project / "app/views/pages/produtos_view.py").exists()
    assert list((project / "migrations").glob("*_produtos.py"))
    assert (project / "data/fleting.db").exists()
    assert any("db migrate" in q for q in router.asked)


def test_create_page_and_list(router, project):
    assert route(router, "criar página clientes")["success"]
    assert (project / "app/controllers/clientes_controller.py").exists()
    r = route(router, "fleting list pages")
    assert r["success"] and "clientes" in r["content"]


def test_name_normalization_and_blocking(router, project):
    assert route(router, "fleting create page Ordem-Compra")["success"]
    assert (project / "app/views/pages/ordem_compra_view.py").exists()
    assert not route(router, "fleting create page ../../evil")["success"]
    assert not route(router, "fleting run")["success"]


@pytest.mark.skipif(MODEL not in _ollama_models(), reason=f"Ollama/modelo {MODEL} indisponível")
def test_local_llm_with_token_plan(router):
    plan = router.prepare_model(context_tokens=2048, max_tokens=256)
    if not plan.fits:
        pytest.skip("RAM insuficiente: " + " ".join(plan.warnings))
    assert router.model.startswith("flai-")          # modelo filtrado criado/usado
    r = route(router, "o que faz o produtos_controller?")
    assert r["type"] == "llm_response" and r["success"], r
    assert r["tokens"]["prompt"] > 0
    assert r["tokens"]["prompt"] + r["tokens"]["output"] <= plan.effective_ctx
