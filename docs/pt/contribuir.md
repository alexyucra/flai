# Contribuir

Toda ajuda é bem-vinda: código, testes, documentação, exemplos e relatos de uso em hardware
diferente.

## Ambiente

```bash
git clone https://github.com/<seu-usuario>/flai.git
cd flai
uv venv
uv pip install -e ".[rag]" pytest
```

Sem `uv`: `python -m venv .venv` e `pip install -e ".[rag]" pytest`.

## Testes

```bash
# rápidos, sem LLM
.venv/Scripts/python -m pytest flai/test/test_assistant.py flai/test/test_security_controls.py \
    flai/test/test_resources.py flai/test/test_contexts.py -q

# ponta a ponta: Fleting real + Ollama local
FLAI_TEST_MODEL=qwen2.5-coder:3b .venv/Scripts/python -m pytest flai/test/test_e2e_fleting_ollama.py -q
```

(No Linux/macOS, `.venv/bin/python`.)

## Documentação

A documentação usa [MkDocs Material](https://squidfunk.github.io/mkdocs-material/):

```bash
pip install -e ".[docs]"
mkdocs serve            # http://127.0.0.1:8000, recarrega ao salvar
mkdocs build --strict   # o mesmo que o CI roda
```

Ao fazer push na `master`, o workflow `.github/workflows/deploy-docs.yml` publica no
GitHub Pages (`mkdocs gh-deploy`).

## Onde mexer

| Quero... | Arquivo |
|---|---|
| nova ferramenta do assistente | `flai/core/assistant/tools.py` (`TOOL_SPECS`, `t_<nome>`, `TOOL_TRIGGERS`) |
| mudar regras do assistente | `ASSISTANT_RULES` em `flai/core/assistant/assistant.py` |
| novo atalho determinístico | `flai/core/intent/patterns.py` + `RouterAgent.route` |
| novo gerador | siga `CRUDAgent` / `ToolBox.t_criar_listagem` |
| comando `fleting` permitido | `ALLOWED_COMMANDS` / `SENSITIVE_COMMANDS` em `fleting_executor.py` |
| novo comando `/` do shell | `_handle_command` em `flai/cli/repl_unified.py` |

### Regras para ferramentas

1. Caminhos sempre por `self._path()` (confinamento + pastas protegidas).
2. Escrita sempre por `self._write()` (sintaxe → diff → confirmação → backup).
3. Saída curta e acionável. Em caso de erro, diga ao modelo **o que fazer** (o modelo lê).
4. Acrescente o gatilho em `TOOL_TRIGGERS` e testes em `test_assistant.py`.

## Pull requests

1. Crie uma branch: `git checkout -b feature/minha-melhoria`.
2. Inclua testes e atualize a documentação em `docs/`.
3. Rode a suíte rápida e o `mkdocs build --strict`.
4. Abra o PR descrevendo o problema, a solução e como testou (modelo e RAM usados).
