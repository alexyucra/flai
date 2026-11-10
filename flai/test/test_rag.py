"""
Testes do RAG local (índice JSON + embeddings).

- Unitários: embedding falso determinístico (sem Ollama).
- Integração: LangChain (langchain-ollama + langchain-text-splitters) com
  `nomic-embed-text` no Ollama local; pulados se indisponíveis.

    uv run pytest flai/test/test_rag.py -v
"""
import hashlib
import math
import re

import pytest

from flai.core.rag.rag_manager import RAGManager, simple_split

DIM = 64


def fake_embed(texts):
    """Bag-of-words com hashing: textos com as mesmas palavras ficam próximos."""
    out = []
    for t in texts:
        v = [0.0] * DIM
        for w in re.findall(r"[a-z_]{3,}", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % DIM] += 1.0
        out.append(v if any(v) else [1.0] + [0.0] * (DIM - 1))
    return out


@pytest.fixture
def project(tmp_path):
    (tmp_path / ".fleting").write_text("x")
    ctrl = tmp_path / "app" / "controllers"
    ctrl.mkdir(parents=True)
    (ctrl / "produtos_controller.py").write_text(
        "class ProdutosController:\n    def listar_produtos(self):\n        return estoque_produtos\n")
    (ctrl / "login_controller.py").write_text(
        "class LoginController:\n    def autenticar_usuario(self, senha):\n        return validar_senha(senha)\n")
    (tmp_path / "README.md").write_text("Projeto de loja com produtos e login.\n")
    # Devem ser ignorados
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib.py").write_text("ignorar = True\n")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "dump.py").write_text("ignorar = True\n")
    return tmp_path


def test_simple_split_overlap_and_size():
    text = "".join(f"linha {i}\n" for i in range(200))
    chunks = simple_split(text, chunk_size=100, overlap=20)
    assert len(chunks) > 5 and all(len(c) <= 120 for c in chunks)
    assert chunks[1].startswith(chunks[0][-20:])


def test_index_search_and_skip_dirs(project):
    rag = RAGManager(project, embed_fn=fake_embed)
    assert rag.index_project(verbose=False)
    stats = rag.get_index_stats()
    assert stats["exists"] and stats["total_documents"] == 3

    hits = rag.search("autenticar usuario senha", k=2)
    assert hits[0]["source"] == "app/controllers/login_controller.py"
    assert 0 <= hits[0]["score"] < hits[1]["score"]  # distância menor = mais parecido
    sources = {c["source"] for c in rag._load()["chunks"]}
    assert not any(s.startswith((".venv", "data")) for s in sources)


def test_incremental_reindex_and_removed_files(project):
    calls = []

    def counting_embed(texts):
        calls.append(len(texts))
        return fake_embed(texts)

    rag = RAGManager(project, embed_fn=counting_embed)
    rag.index_project(verbose=False)
    first = sum(calls)
    rag.index_project(verbose=False)  # nada mudou: não reembeda
    assert sum(calls) == first

    (project / "README.md").unlink()
    rag.index_project(verbose=False)
    assert "README.md" not in rag._load()["files"]


def test_index_persists_and_reloads(project):
    RAGManager(project, embed_fn=fake_embed).index_project(verbose=False)
    again = RAGManager(project, embed_fn=fake_embed)
    hit = again.search("class produtoscontroller listar_produtos estoque_produtos", k=1)[0]
    assert hit["source"].endswith("produtos_controller.py")


def test_context_for_prompt_respects_budget(project):
    rag = RAGManager(project, embed_fn=fake_embed)
    rag.index_project(verbose=False)
    ctx = rag.get_context_for_prompt("produtos", max_tokens=60, k=3)
    assert ctx.startswith("## 📚 Contexto do código") and len(ctx) <= 60 * 3 + 40


def test_clear_index(project):
    rag = RAGManager(project, embed_fn=fake_embed)
    rag.index_project(verbose=False)
    assert rag.clear_index() and not rag.get_index_stats()["exists"]


# --------------------------------------------------------------- integração
def _has_embed_model():
    try:
        import requests
        names = {m["name"] for m in requests.get("http://127.0.0.1:11434/api/tags", timeout=3)
                 .json().get("models", [])}
        return "nomic-embed-text:latest" in names or "nomic-embed-text" in names
    except Exception:
        return False


@pytest.mark.skipif(not _has_embed_model(), reason="Ollama com nomic-embed-text indisponível")
def test_langchain_ollama_semantic_search(project):
    pytest.importorskip("langchain_ollama")
    pytest.importorskip("langchain_text_splitters")
    rag = RAGManager(project)
    assert rag.index_project(verbose=False), rag.last_error
    assert rag.backend == "langchain-ollama"

    hits = rag.search("onde fica a verificação de senha do usuário?", k=3)
    assert hits[0]["source"] == "app/controllers/login_controller.py"
    vec = rag._load()["chunks"][0]["vector"]
    assert len(vec) == 768 and math.isclose(sum(x * x for x in vec), 1.0, rel_tol=1e-3)
