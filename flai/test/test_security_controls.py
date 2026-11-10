"""Testes dos controles da auditoria (SEC-01, SEC-03, SEC-04, SEC-05, PRIV-01).

Não dependem de Ollama, Fleting ou rede. Rodar com: pytest flai/test/test_security_controls.py
"""
from pathlib import Path

import pytest

from flai.core.security import (
    safe_name, safe_join, UnsafePathError,
    validate_remote_url, UnsafeURLError,
    validate_module_path, UnsafeModuleError,
)
from flai.core.security.modules import custom_agents_allowed


# --- SEC-03 -----------------------------------------------------------------
@pytest.mark.parametrize("name", ["crud", "my_agent", "form-1", "A" * 64])
def test_safe_name_ok(name):
    assert safe_name(name) == name


@pytest.mark.parametrize("name", ["", "../x", "a/b", "a\\b", "..", "x.yaml", "a b", "A" * 65, None])
def test_safe_name_rejects(name):
    with pytest.raises(UnsafePathError):
        safe_name(name)


def test_safe_join_blocks_escape(tmp_path: Path):
    assert safe_join(tmp_path, "a", "b.txt") == (tmp_path / "a" / "b.txt").resolve()
    with pytest.raises(UnsafePathError):
        safe_join(tmp_path, "..", "fora.txt")


# --- SEC-04 -----------------------------------------------------------------
def test_url_ok():
    assert validate_remote_url("https://github.com/flet-dev/flet")


@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "http://example.com",
    "ext::sh -c touch% /tmp/pwn",
    "--upload-pack=touch /tmp/pwn",
    "ftp://example.com/x",
    "https://",
    "",
])
def test_url_rejects(url):
    with pytest.raises(UnsafeURLError):
        validate_remote_url(url)


# --- SEC-01 -----------------------------------------------------------------
def test_module_allowlist():
    assert validate_module_path("flai.core.agents.crud_agent")
    for bad in ["os", "subprocess", ".flai.agents.custom.x.agent", "flai.core.agentsX.evil"]:
        with pytest.raises(UnsafeModuleError):
            validate_module_path(bad)


def test_custom_agents_disabled_by_default(monkeypatch):
    monkeypatch.delenv("FLAI_ALLOW_CUSTOM_AGENTS", raising=False)
    assert custom_agents_allowed() is False
    monkeypatch.setenv("FLAI_ALLOW_CUSTOM_AGENTS", "1")
    assert custom_agents_allowed() is True


# --- SEC-05 -----------------------------------------------------------------
def test_shell_executor_rejects_strings_and_pip_options(tmp_path):
    from flai.core.executors.shell_executor import ShellExecutor
    ex = ShellExecutor(tmp_path)
    assert ex.run("echo hi")[0] == -1
    assert not hasattr(ex, "run_python")
    assert ex.install_package("-r http://evil/req.txt") is False
    assert ex.install_package("--index-url=http://evil") is False


def test_fleting_executor_rejects_injected_names(tmp_path, monkeypatch):
    from flai.core.executors import fleting_executor as fe
    called = []
    monkeypatch.setattr(fe.subprocess, "run", lambda *a, **k: called.append(a))
    ex = fe.FletingExecutor(tmp_path)
    assert ex.create_page("x --force") is False
    assert ex.create_model("../evil") is False
    assert called == []


# --- PRIV-01 ----------------------------------------------------------------
def test_flai_yml_is_reserved_and_external_provider_locked():
    import yaml
    from flai.source.langchain import llm

    cfg = yaml.safe_load(Path(llm.CONFIG_PATH).read_text(encoding="utf-8"))
    assert cfg["status"] == "reserved"
    assert cfg["ia"]["enabled"] is False
    assert llm.is_external_enabled(cfg) is False
    with pytest.raises(llm.ExternalProviderDisabled):
        llm.get_llm()


# --- Fleting CLI (allowlist, nomes, confirmação) ------------------------------
def test_fleting_name_rules():
    from flai.core.executors.fleting_executor import fleting_name, FletingNameError
    assert fleting_name("Ordem-Compra") == "ordem_compra"
    for bad in ["1abc", "class", "a b", "../x", "", "x;rm"]:
        with pytest.raises(FletingNameError):
            fleting_name(bad)


def test_fleting_allowlist_and_confirmation(tmp_path, monkeypatch):
    from flai.core.executors import fleting_executor as fe
    calls = []

    class R:
        returncode, stdout, stderr = 0, "ok", ""

    monkeypatch.setattr(fe.subprocess, "run", lambda args, **k: calls.append(args[1:]) or R())
    ex = fe.FletingExecutor(tmp_path, confirm=None)
    ex._binary = "fleting"
    assert ex.execute(["run"])[0] == 2                         # fora da allowlist
    assert ex.execute(["create", "page", "a", "--force"])[0] == 2  # args extras
    assert ex.execute(["db", "migrate"])[0] == 3               # sensível sem confirmação
    assert ex.execute(["create", "page", "Produtos"])[0] == 0
    assert calls == [["create", "page", "produtos"]]

    ex.confirm = lambda q: True
    assert ex.execute(["db", "migrate"])[0] == 0
    assert calls[-1] == ["db", "migrate"]
