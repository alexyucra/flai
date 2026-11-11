# Comandos (CLI)

Todos os comandos rodam a partir da raiz de um projeto Fleting (ou com `--project/-p`).

| Comando | Para quê |
|---|---|
| [`flai init`](#flai-init) | Configura a IA local no projeto |
| [`flai shell`](#flai-shell) | Assistente interativo (comando principal) |
| [`flai rag`](#flai-rag) | Índice de busca semântica do código |
| [`flai context`](#flai-context) | Documentações usadas pela IA (Flet, Fleting, as suas) |
| [`flai history`](#flai-history) | Sessões de conversa salvas |
| [`flai config`](#flai-config) | Painel web e configuração pelo terminal |
| [`flai agent`](#flai-agent) | Agentes registrados |
| [`flai intent`](#flai-intent) | Intenções (atalhos) e teste de frases |

---

## `flai init`

```bash
flai init [MODELO] [--path/-p CAMINHO] [--verbose/-v]
```

Detecta o hardware, inicia o Ollama, baixa o modelo, cria a versão otimizada e grava
`.flai/config.json`. Veja [Instalação](instalacao.md#4-configurar-a-ia-flai-init).

```bash
flai init qwen2.5-coder:3b
flai init qwen2.5-coder:1.5b -p ../outro_projeto
```

---

## `flai shell`

```bash
flai shell [--project/-p CAMINHO] [--model/-m MODELO] [--session/-s NOME]
```

Abre o assistente. Ao iniciar, ele mostra o plano de recursos:

```text
🧠 RAM livre 3.0/15.6 GB · modelo 1.8 GB · contexto 8192 tokens (configurado 8192,
   máx. seguro 16896) · resposta até 768
⚙️ Modelo filtrado: flai-qwen2.5-coder-3b:ctx8192 (base qwen2.5-coder:3b)
```

### O que escrever

| Você escreve | O que acontece |
|---|---|
| `criar crud de produtos com os campos: nome, preco:float` | Gerador de CRUD (plano → confirmação → execução → verificação) |
| `criar página contato` / `criar model cliente` | `fleting create page/model` |
| `fleting list pages`, `fleting db status`, `fleting doctor` | CLI Fleting direto (allowlist) |
| `o que faz o usuarios_controller?` | O assistente lê o arquivo e responde |
| `e o model dele?` | Usa o foco da conversa (`usuarios`) |
| `adicione no controller um método contar` | `escrever_metodo` → diff → confirmação |
| `crie a listagem de usuarios na usuarios_view` | Gerador de listagem (`ft.DataTable`) |
| `verifique o projeto` | Checa a sintaxe de todos os `.py` |
| `sim` / `não` | Responde à sugestão que o assistente acabou de fazer |
| `crie a documentação do projeto` | Resposta longa (até 2048 tokens) |
| `ajuda`, `sair` | Atalhos exatos |

### Comandos com `/`

| Comando | Descrição |
|---|---|
| `/contexto` | Foco atual, arquivos recentes, memória, pergunta pendente e arquivos alterados |
| `/desfazer` | Reverte a última alteração de arquivo (pode repetir: é uma pilha) |
| `/clear` | Limpa o histórico e a memória da conversa |
| `/tokens` | RAM, contexto, orçamento e tokens da última resposta |
| `/tokens refresh` | Recalcula o contexto com a RAM atual |
| `/history` | Últimas trocas da sessão |
| `/export [arquivo.md]` | Exporta a conversa para Markdown |
| `/rag index` | (Re)indexa o projeto |
| `/rag search <consulta>` | Busca semântica no código |
| `/help` | Ajuda completa |
| `/exit` | Sai |

### Teclado

- **↑ / ↓**: histórico de entradas (salvo em `.flai/input_history`, sobrevive entre sessões).
- **Tab**: autocompleta comandos `/`, `criar crud de`, `fleting` e nomes das entidades.
- **Ctrl+C** durante a resposta: interrompe a geração e mantém o que já saiu.

### Confirmações

Toda escrita mostra o diff e pergunta:

```text
✏️ editar app/controllers/usuarios_controller.py
@@ -11,2 +11,5 @@
     def get_title(self):
         return "Usuarios"
+
+    def listar(self):
+        return self.model.all()
⚠️ Aplicar alteração em app/controllers/usuarios_controller.py? [s/N]:
```

Responder qualquer coisa diferente de `s`/`sim` cancela. O arquivo não é alterado e o
assistente pergunta o que ajustar.

---

## `flai rag`

```bash
flai rag index|search|stats|clear [--query/-q TEXTO] [--project/-p CAMINHO]
```

```bash
flai rag index
flai rag search -q "validação de email"
flai rag stats
```

O índice fica em `.flai/vectordb/`. Os embeddings usam `nomic-embed-text` pelo Ollama.

---

## `flai context`

Gerencia as **documentações** que entram no contexto da IA, além do código do projeto:
a documentação do Flet na versão instalada, a do Fleting e documentos seus.

```bash
flai context list
flai context add flet_docs -n "Flet 1.0.5" -t git_repo \
     -l https://github.com/flet-dev/flet --ref v1.0.5 --paths <pasta-da-doc> -p 1 --index
flai context add regras -n "Regras da empresa" -t local_file -l ./docs/regras.md --index
flai context index flet_docs
flai context search "page.show_dialog"
flai context check                # compara versões cadastradas com as instaladas
flai context enable|disable|remove <id>
```

| Tipo | `--location` |
|---|---|
| `local_file` | arquivo ou pasta |
| `git_repo` | URL https do repositório (+ `--ref` tag/branch e `--paths` subpastas) |
| `url` | página https (até 5 MB) |

`--priority 1` é a mais importante: entra primeiro no orçamento de tokens. A configuração
fica em `.flai/contexts/config.yaml` e cada fonte tem índice próprio.

---

## `flai history`

```bash
flai history                       # lista sessões em .flai/sessions/
flai history -s NOME -e saida.md   # exporta uma sessão
```

---

## `flai config`

```bash
flai config [start|show|set|unset|init|list|edit] [CHAVE] [VALOR]
            [--port 8080] [--no-browser] [--project/-p CAMINHO] [--force/-f]
```

| Comando | O que faz |
|---|---|
| `flai config` ou `flai config start` | Abre o painel web local (agentes, intenções, documentações, RAG) |
| `flai config show [chave]` | Mostra a configuração (ou uma chave) |
| `flai config list` | O mesmo que `show` |
| `flai config set <chave> <valor>` | Altera uma chave, com validação de tipo (`int`, `float`, `bool`) |
| `flai config unset <chave>` | Remove uma chave (volta ao padrão) |
| `flai config init [--force]` | Cria `.flai/config.json` padrão (`--force` sobrescreve) |
| `flai config edit` | Abre o arquivo no editor do sistema |

```bash
flai config set context_tokens 8192
flai config set temperature 0.2
flai config show model
```

---

## `flai agent`

```bash
flai agent list                 # agentes, tipo, triggers e status
flai agent show crud_agent      # detalhes e capacidades
flai agent enable|disable <nome>
flai agent create               # agente customizado
flai agent stats
```

Agentes embutidos: `crud_agent`, `db_agent`, `form_agent`, `project_agent`, `rag_agent` e
`llm_fallback_agent`.

---

## `flai intent`

Intenções são os **atalhos determinísticos** do shell (ex.: `criar crud de X`). O que não
casar com uma intenção vai para o [assistente](assistente.md).

```bash
flai intent list
flai intent show create_crud
flai intent test "criar crud de produtos"     # ✅ create_crud · entidade: produtos
flai intent add | remove | enable | disable <nome>
flai intent pattern-add <nome> "<regex>"
flai intent keyword-add <nome> <palavra>
flai intent export -o intents.yaml [-f yaml|json]
flai intent import -i intents.yaml [--force]
```

!!! tip "Use regex ancorados para comandos"
    Padrões sem âncora casam em qualquer lugar da frase (`r"q"` casava com "verifi**q**ue").
    Para comandos de controle, use `^...$`.
