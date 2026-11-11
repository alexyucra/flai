"""
Testes do assistente conversacional (sem LLM): sessão, ferramentas, parsing e roteamento.

    .venv/Scripts/python -m pytest flai/test/test_assistant.py -q
"""
from pathlib import Path

import pytest

from flai.core.assistant import Session, ToolBox
from flai.core.assistant.assistant import Assistant, StreamGate, parse_text_tool_call
from flai.core.assistant.tools import select_tools
from flai.core.executors.fleting_executor import FletingExecutor

CONTROLLER = '''from app.models.usuarios_model import UsuariosModel

class UsuariosController:
    def __init__(self, model=None):
        self.model = model or UsuariosModel

    def get_title(self):
        return "Usuarios"
'''


@pytest.fixture
def proj(tmp_path):
    ctrl = tmp_path / "app" / "controllers" / "usuarios_controller.py"
    ctrl.parent.mkdir(parents=True)
    ctrl.write_text(CONTROLLER, encoding="utf-8")
    (tmp_path / ".flai").mkdir()
    (tmp_path / ".flai" / "config.json").write_text("{}", encoding="utf-8")
    return tmp_path


@pytest.fixture
def tb(proj):
    return ToolBox(proj, FletingExecutor(proj), confirm=lambda q: True, session=Session())


CTRL = "app/controllers/usuarios_controller.py"


def read(proj):
    return (proj / CTRL).read_text(encoding="utf-8")


# ----------------------------------------------------------------- ferramentas
def test_escrever_metodo_fixes_class_level_indentation(tb, proj):
    # erro típico do modelo: def sem indentação e corpo com 8 espaços
    out = tb.run("escrever_metodo", {"caminho": CTRL, "codigo": "def listar(self):\n        return self.model.all()"})
    assert out.startswith("OK"), out
    assert "    def listar(self):\n        return self.model.all()\n" in read(proj)


def test_escrever_metodo_replaces_existing(tb, proj):
    tb.run("escrever_metodo", {"caminho": CTRL, "codigo": 'def get_title(self):\n    return "Usuários"'})
    text = read(proj)
    assert text.count("def get_title") == 1 and '"Usuários"' in text


def test_invalid_syntax_is_rejected_without_writing_or_asking(proj):
    asked = []
    tb = ToolBox(proj, FletingExecutor(proj), confirm=lambda q: asked.append(q) or True)
    out = tb.run("editar_arquivo", {"caminho": CTRL, "buscar": 'return "Usuarios"', "substituir": 'return ("x"'})
    assert out.startswith("REJEITADO")
    assert read(proj) == CONTROLLER
    assert asked == []  # diff quebrado nem chega ao usuário
    assert tb.failed_writes == [CTRL]


def test_cancel_keeps_file_and_reports(proj):
    tb = ToolBox(proj, FletingExecutor(proj), confirm=lambda q: False)
    out = tb.run("escrever_metodo", {"caminho": CTRL, "codigo": "def x(self):\n    pass"})
    assert out.startswith("CANCELADO") and read(proj) == CONTROLLER


def test_editar_reindents_and_matches_loosely(tb, proj):
    out = tb.run("editar_arquivo", {"caminho": CTRL, "buscar": 'def get_title(self):\n  return "Usuarios"',
                                    "substituir": 'def get_title(self):\n    return "Lista"'})
    assert out.startswith("OK"), out
    assert '    def get_title(self):\n        return "Lista"' in read(proj)


def test_undo_stack(tb, proj):
    tb.run("escrever_metodo", {"caminho": CTRL, "codigo": "def a(self):\n    return 1"})
    tb.run("escrever_metodo", {"caminho": CTRL, "codigo": "def b(self):\n    return 2"})
    assert tb.backups.undo() and "def b" not in read(proj)
    assert tb.backups.undo() and read(proj) == CONTROLLER
    assert tb.backups.undo() is None


def test_undo_removes_created_file(tb, proj):
    tb.run("criar_arquivo", {"caminho": "app/novo.py", "conteudo": "x = 1"})
    assert (proj / "app/novo.py").exists()
    tb.backups.undo()
    assert not (proj / "app/novo.py").exists()


@pytest.mark.parametrize("path", ["../fora.py", ".flai/config.json", "data/x.db"])
def test_paths_are_confined(tb, path):
    assert tb.run("ler_arquivo", {"caminho": path}).startswith("ERRO")


def test_project_prefix_and_bare_names_resolve(tb, proj):
    assert tb.run("ler_arquivo", {"caminho": f"{proj.name}/{CTRL}"}).startswith(f"# {CTRL}")
    assert tb.run("ler_arquivo", {"caminho": "usuarios_controller"}).startswith(f"# {CTRL}")


def test_unknown_tool_and_string_args(tb):
    assert tb.run("rm_rf", {}).startswith("ERRO")
    assert tb.run("buscar_no_codigo", '{"texto": "get_title"}').startswith(CTRL)


# ------------------------------------------------------- seleção e parsing
@pytest.mark.parametrize("text,must,must_not", [
    ("o que faz o controller?", {"ler_arquivo"}, {"editar_arquivo", "escrever_metodo", "fleting"}),
    ("adicione um método salvar", {"escrever_metodo"}, {"editar_arquivo"}),
    ("crie a listagem de usuarios", {"criar_listagem"}, set()),
    ("criar crud de produtos", {"criar_crud"}, set()),
    ("verifique o projeto", {"verificar_projeto"}, set()),
])
def test_select_tools(text, must, must_not):
    names = {t["function"]["name"] for t in select_tools(text)}
    assert must <= names and not (must_not & names)


def test_parse_text_tool_calls_multiple_objects():
    text = ('{"name": "ler_arquivo", "arguments": {"caminho": "a.py"}}\n'
            '{"name": "editar_arquivo", "arguments": {"caminho": "a.py", "buscar": "x", "substituir": "y"}}')
    calls = parse_text_tool_call(text)
    assert [c["function"]["name"] for c in calls] == ["ler_arquivo", "editar_arquivo"]
    assert parse_text_tool_call('{"name": "nao_existe", "arguments": {}}') == []


def test_stream_gate_holds_json_and_passes_text():
    out = []
    g = StreamGate(out.append)
    for c in ['{"na', 'me": "ler_arquivo"}']:
        g(c)
    assert out == [] and g.held.startswith("{")
    out2 = []
    g2 = StreamGate(out2.append)
    for c in ["```py", "thon\nx = 1"]:
        g2(c)
    assert "".join(out2) == "```python\nx = 1"


def test_fit_drops_history_then_trims_context():
    msgs = [{"role": "system", "content": "s" * 100},
            {"role": "user", "content": "u" * 3000}, {"role": "assistant", "content": "a" * 3000},
            {"role": "user", "content": "pergunta\n## Contexto\n" + "c" * 6000}]
    out = Assistant._fit(list(msgs), budget=1000)
    assert out[0]["role"] == "system" and len(out) == 2
    assert out[-1]["content"].startswith("pergunta") and "cortado" in out[-1]["content"]


# ------------------------------------------------------------------- sessão
def test_session_focus_pending_and_repeat():
    s = Session()
    s.update_focus("e o usuarios_controller?", ["usuarios", "settings"])
    assert s.focus_entity == "usuarios"
    s.add_turn("x", "Feito.\nQuer que eu crie a listagem?")
    assert s.pending == "Quer que eu crie a listagem?"
    assert s.is_continuation("sim") and s.is_continuation("não") and not s.is_continuation("crie outra")
    s.add_turn("sim", "Pronto.\nQuer que eu crie a listagem?")  # repetiu a mesma sugestão
    assert s.pending is None


def test_session_keeps_last_turns():
    s = Session(max_turns=2)
    for i in range(5):
        s.add_turn(f"u{i}", f"a{i}")
    assert [m["content"] for m in s.history] == ["u3", "a3", "u4", "a4"]


def test_suggestion_to_command():
    from flai.core.agents.router_agent import RouterAgent
    f = RouterAgent._suggestion_to_command
    assert f("Quer que eu crie a listagem de usuarios na usuarios_view?") == \
        "crie a listagem de usuarios na usuarios_view"
    assert f("Posso rodar fleting doctor?") == "rodar fleting doctor"
