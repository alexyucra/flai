# Configuração

## `.flai/config.json`

Criado pelo `flai init` na raiz do projeto. Exemplo recomendado para o `qwen2.5-coder:3b`:

```json
{
  "model": "qwen2.5-coder:3b",
  "temperature": 0.2,
  "max_tokens": 768,
  "context_tokens": 8192,
  "use_optimized_model": true,
  "rag": {
    "enabled": true,
    "auto_index": true,
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "max_results": 5,
    "embedding_model": "nomic-embed-text"
  },
  "web_enabled": true,
  "web_port": 8080,
  "auto_save_history": true,
  "max_history_size": 1000,
  "log_level": "INFO"
}
```

| Chave | Padrão | Efeito |
|---|---|---|
| `model` | — | Modelo base do Ollama. Também aceita um derivado (`flai-...`); o FLAI descobre o base. |
| `context_tokens` | 2048 | Contexto pedido. O FLAI usa `min(context_tokens, máximo seguro pela RAM)`. **Assistente: mínimo 4096, recomendado 8192.** |
| `max_tokens` | 512 | Tamanho máximo das respostas comuns. Documentação usa até 2048 automaticamente. |
| `temperature` | 0.7 | Criatividade do modelo derivado. Para código, use 0.1–0.3. O loop de ferramentas usa 0.1. |
| `use_optimized_model` | `true` | Cria e usa `flai-<base>:ctx<N>` com os parâmetros acima. |
| `rag.*` | — | Indexação e busca semântica (veja [CLI › rag](cli.md#flai-rag)). |
| `web_port` | 8080 | Porta do painel `flai config`. |
| `auto_save_history` | `true` | Salva as conversas em `.flai/sessions/`. |

!!! note "Depois de alterar"
    Reinicie o `flai shell` ou use `/tokens refresh`. Se o contexto mudar, um novo modelo
    derivado é criado (`flai-qwen2.5-coder-3b:ctx8192`), uma única vez.

## Variáveis de ambiente

### FLAI

| Variável | Padrão | Efeito |
|---|---|---|
| `FLAI_KEEP_ALIVE` | `10m` | Quanto tempo o modelo fica carregado entre perguntas. `0` libera a RAM logo após cada resposta. Valores maiores (`30m`) evitam recarregar. |
| `FLAI_TEST_MODEL` | `qwen2.5-coder:7b` | Modelo usado nos testes e2e. |

### Servidor Ollama (RAM limitada)

```powershell
setx OLLAMA_FLASH_ATTENTION 1      # menos memória na atenção
setx OLLAMA_KV_CACHE_TYPE q8_0     # KV cache pela metade (exige flash attention)
setx OLLAMA_NUM_PARALLEL 1         # 1 requisição por vez
setx OLLAMA_MAX_LOADED_MODELS 1    # nunca dois modelos na RAM
```

Reinicie o `ollama serve` depois. Em Linux/macOS use `export VAR=valor`.

## Arquivos em `.flai/`

| Caminho | Conteúdo |
|---|---|
| `config.json` | configuração acima |
| `sessions/` | conversas em Markdown (`/export`, `flai history`) |
| `input_history` | histórico de entradas do shell (↑) |
| `backups/` | cópias antes de cada alteração (pilha do `/desfazer`) |
| `vectordb/` | índice RAG do código |
| `contexts/config.yaml` | documentações cadastradas (`flai context`) |
| `contexts/<id>/vectordb/` | índice de cada documentação |

!!! warning "Versionamento"
    Coloque `.flai/` no `.gitignore` do projeto. Os backups e índices são locais e podem
    ser grandes.
