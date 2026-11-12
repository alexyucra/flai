# Assistente do FLAI: como a conversa funciona

O `flai shell` funciona como um assistente: lembra da conversa, lê e altera o projeto
(sempre com diff e confirmação), verifica o resultado e sugere o próximo passo.

Código: `flai/core/assistant/` (`session.py`, `tools.py`, `assistant.py`), integrado em
`flai/core/agents/router_agent.py` e `flai/cli/repl_unified.py`.

## Fluxo de uma mensagem

```
mensagem
  ├─ "fleting ..."  ou comando exato (criar crud de X, criar página X, ajuda, sair)
  │      → atalho determinístico, instantâneo (sem LLM)
  ├─ "sim" / "não" para uma sugestão pendente
  │      → vira o comando sugerido ("crie a listagem de usuarios na usuarios_view")
  └─ todo o resto → assistente:
         system fixo + mapa do código     (em cache no Ollama)
         + histórico (últimas 6 trocas)
         + pergunta + contexto do turno   (foco, arquivo citado, RAG)
         → modelo decide: responder ou chamar ferramentas (até 5 passos)
```

## Exemplo

```
💬 Você: criar crud de usuarios com os campos: nome, email, ativo:bool
📋 Plano ... ⚠️ Executar o plano? [s/N]: s
🔎 Verificação ✅ ✅ ✅
Quer que eu crie a listagem de usuarios na usuarios_view?

💬 Você: sim
🔧 criar_listagem(entidade=usuarios)
✏️ editar app/views/pages/usuarios_view.py   (diff)
⚠️ Aplicar alteração? [s/N]: s

💬 Você: o que faz o usuarios_controller?      → lê o arquivo e responde
💬 Você: e o model dele?                        → foco = usuarios → usuarios_model.py
💬 Você: adicione nele um método contar          → escrever_metodo + diff
💬 Você: /desfazer                               → reverte
```

## Ferramentas

| Ferramenta | O que faz | Segurança |
|---|---|---|
| `listar_arquivos`, `ler_arquivo`, `buscar_no_codigo` | leitura | só dentro do projeto; `.flai`, `.git`, `data`, venv bloqueados |
| `escrever_metodo` | cria **ou substitui** um método inteiro numa classe (indentação via `ast`) | diff + confirmação + backup |
| `editar_arquivo` | troca um trecho (aceita diferenças de indentação) | idem |
| `criar_arquivo` | arquivo novo / reescrita | idem |
| `criar_listagem` | gerador: `listar()` no controller + `render()` com `ft.DataTable` (colunas da migration) | idem |
| `criar_crud` | página + migration com `CREATE TABLE` + migrate (plano, verificação) | 1 confirmação |
| `fleting` | CLI Fleting (allowlist) | comandos sensíveis pedem confirmação |
| `verificar_projeto` | sintaxe de todos os `.py` | só leitura |

Toda escrita em `.py` é **compilada antes** de chegar ao usuário. Se der erro de sintaxe,
o erro volta ao modelo para ele corrigir, e o arquivo nunca fica quebrado. Se nada for
aplicado, a resposta termina com "⚠️ Alteração NÃO aplicada", mesmo que o modelo diga o
contrário.

## Comandos do shell

| Comando | |
|---|---|
| `/contexto` | foco, memória, pergunta pendente, arquivos alterados |
| `/desfazer` | reverte a última alteração (pilha em `.flai/backups/`) |
| `/clear` | limpa a memória da conversa |
| `/tokens` | RAM, contexto e tokens |
| ↑ / Tab | histórico (`.flai/input_history`) e autocompletar (prompt_toolkit) |

## Por que assim (modelo de 3B na CPU)

Medido com `qwen2.5-coder:3b`, contexto de 8192 tokens, só CPU:

| Técnica | Efeito medido |
|---|---|
| Aquecimento do cache na inicialização | 1ª pergunta: prompt em ~2 s (antes 13 s) |
| Prefixo estável (system + mapa + ferramentas fixas) | perguntas seguintes: ~1,5–3 s de prompt |
| Ferramentas indicadas por pedido (dica no fim) | o 3B passou a escolher a ferramenta certa; a lista fixa preserva o cache |
| `escrever_metodo` em vez de editar trechos | adicionar método funcionou em todos os testes com o modelo; com `editar_arquivo` ele errava a indentação com frequência |
| Geradores determinísticos (`criar_crud`, `criar_listagem`) | tarefas de várias etapas que o 3B não faz sozinho de forma confiável |
| "sim" → comando direto | o modelo executa a sugestão em vez de perguntar de novo |
| Temperatura 0.1 + bloqueio de chamadas repetidas | menos loops |

Limites conhecidos:

- O cache é refeito quando o mapa do código muda (depois de criar ou alterar métodos),
  o que custa ~10 s uma vez.
- Edições livres grandes (reescrever telas inteiras) ainda falham às vezes. Nesses casos o
  FLAI recusa a alteração e avisa, sem quebrar nada.
- Contexto mínimo recomendado: **4096**. Abaixo disso o histórico e o contexto são cortados.
  Use **8192** (cabe na RAM: o KV cache do 3B é ~36 KB/token).

## Testes

```powershell
.venv\Scripts\python -m pytest flai/test/test_assistant.py -q          # sem LLM
$env:FLAI_TEST_MODEL="qwen2.5-coder:3b"; .venv\Scripts\python -m pytest flai/test/test_e2e_fleting_ollama.py -q
```
