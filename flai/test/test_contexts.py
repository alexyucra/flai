"""
Testes do gerenciador de documentações (ContextManager) e do painel web.

Sem rede: embeddings falsos. O teste opcional `test_flet_docs_real` baixa a
documentação do Flet na versão instalada (FLAI_TEST_NETWORK=1).
"""
import os

import pytest

from flai.core.context.context_manager import ContextManager, ContextType
from flai.test.test_rag import fake_embed


@pytest.fixture
def project(tmp_path):
    (tmp_path / ".fleting").write_text("x")
    (tmp_path / "app" / "controllers").mkdir(parents=True)
    (tmp_path / "app" / "controllers" / "login_controller.py").write_text(
        "class LoginController:\n    def autenticar_usuario(self, senha): ...\n")
    docs = tmp_path / "minha_doc"
    docs.mkdir()
    (docs / "botoes.md").write_text("# Button\nUse ft.Button com on_click para botoes clicaveis.\n")
    (docs / "dialogos.md").write_text("# Dialogos\npage.show_dialog abre AlertDialog; pop_dialog fecha.\n")
    return tmp_path


def cm(project):
    return ContextManager(project, embed_fn=fake_embed)


def test_defaults_are_created_with_installed_versions(project):
    m = cm(project)
    assert {"project_code", "fleting_docs", "flet_docs"} <= set(m.sources)
    flet = m.sources["flet_docs"]
    assert flet.type == ContextType.GIT_REPO and flet.ref and flet.ref.startswith("v1.")
    assert "website/docs/controls" in flet.paths
    assert (project / ".flai/contexts/fleting_docs/source.md").read_text(encoding="utf-8").startswith("# Fleting")


def test_legacy_defaults_are_dropped(project):
    m = cm(project)
    cfg = m.config_file.read_text(encoding="utf-8")
    m.config_file.write_text(cfg + "- id: flet_components\n  name: x\n  description: x\n"
                             "  type: git_repo\n  location: https://github.com/flet-dev/flet\n",
                             encoding="utf-8")
    assert "flet_components" not in cm(project).sources


def test_add_edit_toggle_remove_persist(project):
    m = cm(project)
    assert m.add_context("minha_doc", "Minha doc", "Guia", "local_file",
                         str(project / "minha_doc"), priority=2)
    assert m.update_source("minha_doc", priority=4, name="Guia interno")
    assert m.set_enabled("minha_doc", False)
    again = cm(project)  # recarrega do config.yaml
    src = again.sources["minha_doc"]
    assert (src.priority, src.name, src.enabled) == (4, "Guia interno", False)
    assert again.remove_context("minha_doc") and "minha_doc" not in cm(project).sources
    assert not again.remove_context("project_code")  # código do projeto é fixo


@pytest.mark.parametrize("kwargs", [
    dict(source_id="../x", source_type="local_file", location="."),
    dict(source_id="ok", source_type="url", location="file:///etc/passwd"),
    dict(source_id="ok", source_type="git_repo", location="https://github.com/a/b", paths="../../etc"),
])
def test_add_rejects_unsafe_input(project, kwargs):
    m = cm(project)
    assert not m.add_context(name="x", description="x", **kwargs)
    assert m.last_error


def test_each_source_has_its_own_index(project):
    m = cm(project)
    m.add_context("minha_doc", "Minha doc", "Guia", "local_file", str(project / "minha_doc"))
    assert m.index_context("minha_doc") and m.index_context("project_code")
    assert (project / ".flai/contexts/minha_doc/vectordb/index.json").exists()
    assert (project / ".flai/vectordb/index.json").exists()
    # reindexar o projeto não apaga a documentação (bug antigo)
    m.index_context("project_code")
    hits = m.search_contexts("show_dialog alertdialog pop_dialog fecha", ["minha_doc"], k=1)
    assert hits and hits[0]["source"] == "dialogos.md"


def test_prompt_parts_respect_enabled_and_priority(project):
    m = cm(project)
    m.add_context("minha_doc", "Minha doc", "Guia", "local_file", str(project / "minha_doc"), priority=2)
    m.index_context("minha_doc")
    m.index_context("fleting_docs")
    parts = m.get_prompt_parts("button on_click botoes clicaveis", k=2)
    assert parts and parts[0].startswith("[Fleting") or parts[0].startswith("[Minha doc")
    assert any("[Minha doc › botoes.md]" in p for p in parts)
    m.set_enabled("minha_doc", False)
    assert not any("Minha doc" in p for p in m.get_prompt_parts("button on_click botoes", k=2))


def test_version_drift_updates_git_ref(project, monkeypatch):
    m = cm(project)
    m.sources["flet_docs"].ref = "v0.25.0"
    m.sources["flet_docs"].rag_indexed = True
    drifts = m.check_versions()
    assert any(d["id"] == "flet_docs" and d["from"] == "v0.25.0" for d in drifts)
    assert m.sources["flet_docs"].ref.startswith("v1.") and not m.sources["flet_docs"].rag_indexed


@pytest.mark.skipif(os.getenv("FLAI_TEST_NETWORK") != "1", reason="defina FLAI_TEST_NETWORK=1")
def test_flet_docs_real_download(project):
    m = cm(project)
    assert m.update_context("flet_docs", force=True), m.last_error
    content = project / ".flai/contexts/flet_docs/content/website/docs/controls"
    assert content.exists() and any(content.rglob("*.md*"))
    assert not (project / ".flai/contexts/flet_docs/content/sdk").exists()  # só as pastas pedidas


# ------------------------------------------------------------ painel web
class FakePage:
    """Page mínima: registra diálogos e executa threads na hora."""
    def __init__(self):
        self.controls, self.dialogs, self.title = [], [], ""

    def add(self, *c):
        self.controls.extend(c)

    def update(self):
        pass

    def show_dialog(self, d):
        self.dialogs.append(d)

    def pop_dialog(self):
        if self.dialogs:
            self.dialogs.pop()

    def run_thread(self, fn, *a):
        fn(*a)


def test_web_panel_renders_all_pages_with_flet_1(project, monkeypatch):
    pytest.importorskip("flet")
    from flet.controls.base_control import BaseControl
    monkeypatch.setattr(BaseControl, "update", lambda self: None)  # sem Page real
    import flai.core.context.context_manager as ccm
    real = ccm.ContextManager
    monkeypatch.setattr("flai.web.server.ContextManager",
                        lambda p: real(p, embed_fn=fake_embed), raising=False)
    from flai.web.server import FLAIWebServer

    srv = FLAIWebServer(project, port=8765)
    srv.context_manager = real(project, embed_fn=fake_embed)
    page = FakePage()
    srv.main(page)
    for name in ("dashboard", "agents", "intents", "contexts", "rag", "mcp", "settings"):
        srv.navigate_to(name)

    # fluxo de documentações pelo painel
    srv.show_context_dialog(None)
    assert page.dialogs and page.dialogs[-1].title.value == "Adicionar documentação"
    page.pop_dialog()
    srv.context_manager.add_context("minha_doc", "Minha doc", "Guia", "local_file",
                                    str(project / "minha_doc"))
    srv.index_context("minha_doc")
    assert srv.context_manager.sources["minha_doc"].rag_indexed
    srv.toggle_context("minha_doc", False)
    assert not srv.context_manager.sources["minha_doc"].enabled
    srv.check_context_versions()
    srv.delete_context("minha_doc")
    page.dialogs[-1].actions[1].on_click(None)  # confirma "Excluir"
    assert "minha_doc" not in srv.context_manager.sources


def test_web_panel_binds_loopback_only(project):
    pytest.importorskip("flet")
    from flai.web.server import FLAIWebServer
    assert FLAIWebServer(project, host="0.0.0.0").host == "127.0.0.1"
