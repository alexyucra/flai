"""
Regressão: todo comando anunciado em `flai --help` (print_help) precisa existir no CLI.
Antes, 'flai intent', 'flai agent' e 'flai config init/show/set...' apareciam na ajuda
mas respondiam "No such command".
"""
import inspect
import re

import pytest
from click.testing import CliRunner

from flai.cli import cli as cli_module


def _advertised_commands():
    """Extrai os 'flai <cmd> [sub]' listados no código de print_help."""
    src = inspect.getsource(cli_module.print_help)
    cmds = set()
    for full in re.findall(r'\("flai ([^"]+)",', src):
        words = [w for w in full.split() if re.fullmatch(r"[a-z][a-z-]*", w)]
        cmds.add(tuple(words[:2]))
    return sorted(cmds)


ADVERTISED = _advertised_commands()


def test_help_lists_commands():
    assert ("intent", "list") in ADVERTISED and ("config", "init") in ADVERTISED


@pytest.mark.parametrize("words", ADVERTISED, ids=lambda w: " ".join(w))
def test_advertised_command_exists(words):
    top = words[0]
    assert top in cli_module.cli.commands, f"'flai {top}' anunciado na ajuda mas não registrado"
    result = CliRunner().invoke(cli_module.cli, [top, "--help"])
    assert "No such command" not in result.output, result.output
    if len(words) > 1:
        sub = words[1]
        if top == "config":
            assert sub in cli_module.CONFIG_ACTIONS, f"'flai config {sub}' não é uma ação válida"
        elif top in ("rag",):
            pass  # 'rag' usa click.Choice: validado pelo próprio --help
        elif top == "init":
            pass  # 'flai init ia': 'ia' é o argumento MODEL
        else:
            # apps Typer (context, agent, intent): o subcomando aparece na ajuda do grupo
            assert re.search(rf"\b{re.escape(sub)}\b", result.output), \
                f"'flai {top} {sub}' não existe:\n{result.output}"


def test_config_requires_key_for_set():
    result = CliRunner().invoke(cli_module.cli, ["config", "set"])
    assert result.exit_code == 2 and "flai config set <chave> <valor>" in result.output


def test_config_init_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli_module.cli, ["config", "init"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / ".flai" / "config.json").exists()
