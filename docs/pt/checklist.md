# Status e roadmap

Situação em **11/11/2026** (versão 0.1.x).

## Implementado

### Assistente

| Recurso | Status |
|---|---|
| Conversa com memória (últimas 6 trocas) | ✅ |
| Foco da sessão e arquivos recentes | ✅ |
| `sim`/`não` executa ou recusa a sugestão pendente | ✅ |
| Tool calling (10 ferramentas) com loop de até 5 passos | ✅ |
| Diff + confirmação + backup + `/desfazer` em toda escrita | ✅ |
| Validação de sintaxe antes do diff, com correção pelo modelo | ✅ |
| Aviso quando uma alteração não foi aplicada | ✅ |
| Streaming token a token, Ctrl+C mantém o parcial | ✅ |
| Cache de prefixo + aquecimento (1ª resposta rápida) | ✅ |
| prompt_toolkit: histórico (↑) e autocompletar (Tab) | ✅ |
| `/contexto`, `/desfazer`, `/tokens`, `/export` | ✅ |

### Geradores e Fleting

| Recurso | Status |
|---|---|
| CRUD: diagnóstico, plano, confirmação única, `CREATE TABLE`, verificação | ✅ |
| CRUD idempotente (não duplica migrations) | ✅ |
| Listagem com `ft.DataTable` a partir da migration | ✅ |
| CLI Fleting por allowlist com confirmação de comandos sensíveis | ✅ |
| Formulários (`criar form de X`) | ⚠️ gerador antigo, sem diff/confirmação |

### Modelo e recursos

| Recurso | Status |
|---|---|
| Plano de RAM/contexto (`ResourceGuard`) com KV cache real | ✅ |
| Modelo derivado `flai-<base>:ctx<N>` | ✅ |
| Folga mínima com aviso (não bloqueia) | ✅ |
| Respostas curtas; longas só para documentação | ✅ |
| `keep_alive` configurável | ✅ |

### Contexto

| Recurso | Status |
|---|---|
| Mapa do código via `ast` | ✅ |
| RAG do código (`flai rag`) | ✅ |
| Documentações gerenciadas (`flai context`, painel web) | ✅ |

### Qualidade

| Recurso | Status |
|---|---|
| Testes do assistente sem LLM (23) | ✅ |
| Testes de segurança | ✅ |
| Testes e2e com Fleting + Ollama | ✅ |
| Documentação MkDocs + deploy automático | ✅ |

## Problemas conhecidos

- Edições livres grandes (reescrever telas inteiras) ainda falham às vezes com modelos de
  3B. Nesses casos o FLAI recusa a alteração e avisa, sem quebrar nada.
- O cache do prompt é refeito depois de mudanças no código (~10 s, uma vez).
- `flai --help` em consoles cp1252 do Windows falha com emojis (use UTF-8; veja
  [Solução de problemas](solucao-de-problemas.md#windows)).

## Roadmap

- [ ] Formulário de cadastro com diff/confirmação (`criar_formulario`), sugerido após a listagem
- [ ] Ações de editar/excluir na listagem
- [ ] Sessões persistentes: retomar a memória da conversa entre execuções
- [ ] `verificar_projeto` também com `fleting doctor` e import das views
- [ ] Testes gerados para controllers/models
- [ ] Documentação em inglês e espanhol (como no Fleting)
