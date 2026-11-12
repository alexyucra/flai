# Qwen2.5-Coder 3B no FLAI: introspecção e ajuste para RAM limitada

Este guia explica como inspecionar o modelo `qwen2.5-coder:3b`, como derivar dele o modelo
do FLAI e quais parâmetros mudam velocidade, qualidade e consumo de RAM.

> Valores marcados com **(ref.)** vêm da ficha técnica pública do Qwen2.5-Coder-3B.
> A seção 1.1 traz o que foi medido na máquina de desenvolvimento (15,6 GB de RAM, só CPU).

### 1.1 Medido nesta máquina (11/11/2026)

`ollama show flai-qwen2.5-coder-3b:ctx4096`:

```
architecture qwen2 · parameters 3.1B · context length 32768 · embedding length 2048
quantization Q4_K_M · capabilities: completion, tools, insert
num_ctx 4096 · num_predict 768 · temperature 0.2 · top_p 0.9 · repeat_penalty 1.05
```

`ollama ps`: **2,2 GB carregado, 100% CPU**, contexto 4096 (o arquivo tem 1,9 GB).

| Pedido no `flai shell` | Prompt | Resposta | Primeiro token | Total |
|---|---|---|---|---|
| `analise os models` | 518 | 245 | — (sem streaming) | 20 s |
| `analise o controller usuarios` | 648 | 340 | **5,6 s** | 27 s |
| `crie documentação do projeto` | 520 | 1794 | — (sem streaming) | 129 s |

Velocidade de geração: **~14–16 tokens/s**. O tempo total é dominado pelo tamanho da
**resposta**: uma documentação completa leva cerca de 2 minutos na CPU. Por isso o FLAI
mostra a resposta em streaming, e o texto começa a aparecer em segundos.

> O system prompt embutido no modelo base é o padrão do Qwen ("You are Qwen…"). O FLAI
> envia o próprio system prompt em cada requisição, então isso não interfere.

---

## 1. Introspecção: o que olhar no modelo

```powershell
ollama pull qwen2.5-coder:3b
ollama show qwen2.5-coder:3b               # arquitetura, parâmetros, contexto, quantização
ollama show qwen2.5-coder:3b --modelfile   # template de chat e PARAMETERs padrão
ollama show qwen2.5-coder:3b --verbose     # metadados GGUF (camadas, cabeças, vocabulário)
ollama ps                                  # o que está carregado agora, tamanho e CPU/GPU
```

Pela API (útil para o FLAI ler automaticamente):

```powershell
curl http://localhost:11434/api/show -d '{\"model\":\"qwen2.5-coder:3b\"}'
```

### Ficha do modelo (ref.)

| Item | Valor | Por que importa |
|---|---|---|
| Parâmetros | ~3,1 B | Define o tamanho dos pesos na RAM |
| Camadas | 36 | Entra no cálculo do KV cache |
| Cabeças de atenção | 16 de query / **2 de KV** (GQA) | Com 2 cabeças KV, o cache é muito pequeno |
| Dimensão por cabeça | 128 | KV cache |
| Contexto máximo | 32.768 tokens | Limite teórico; na prática quem limita é a RAM |
| Vocabulário | ~151 mil tokens | Tokeniza bem PT-BR e código |
| Quantização padrão do Ollama | Q4_K_M | ~1,9 GB em disco e na RAM |
| Template | ChatML (`<\|im_start\|>…`) | O Ollama aplica sozinho em `/api/chat` e `/api/generate` |

### Quanto de RAM o modelo usa

```
RAM total ≈ pesos + KV cache + buffers (~200–400 MB)
KV cache por token (fp16) = 2 (K e V) × 36 camadas × 2 cabeças KV × 128 × 2 bytes ≈ 36 KB
```

| `num_ctx` | KV cache | RAM total aproximada (Q4_K_M) |
|---|---|---|
| 2048 | ~75 MB | ~2,3 GB |
| **4096** (padrão FLAI) | ~150 MB | ~2,4 GB |
| 8192 | ~300 MB | ~2,6 GB |
| 16384 | ~600 MB | ~2,9 GB |
| 32768 | ~1,2 GB | ~3,5 GB |

Conclusão: no 3B, aumentar o contexto custa pouca RAM, graças ao GQA. Com 3,7 GB livres,
**8192 tokens cabem com folga**. O que fica caro é o **tempo de processar o prompt**, já que
na CPU cada token de prompt custa tempo. Por isso o FLAI usa 4096 como padrão.

---

## 2. Derivar o modelo do FLAI ("destilar" via Modelfile)

No Ollama, "derivar" significa criar um modelo novo `FROM` o base, fixando parâmetros e
system prompt. Os pesos não mudam, mas o modelo já sai configurado.

`Modelfile.flai`:

```dockerfile
FROM qwen2.5-coder:3b

PARAMETER num_ctx 4096
PARAMETER num_predict 768
PARAMETER num_batch 256
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.05
PARAMETER stop "<|im_end|>"

SYSTEM """Você é o FLAI, assistente de desenvolvimento para projetos Fleting (Python + Flet, MVC).
Responda em português, de forma objetiva. Use apenas o contexto do projeto fornecido."""
```

```powershell
ollama create flai-coder -f Modelfile.flai
ollama run flai-coder "explique o arquivo configs/routes.py"
```

O FLAI já faz isso de forma automática: `ensure_optimized_model` cria
`flai-qwen2.5-coder-3b:ctx<N>` com o contexto que a RAM permite, e o
`optimize_model.ps1` cria `flai-coder` com os valores acima.

### Destilação de verdade (opcional, fora do Ollama)

Para ensinar o modelo a seguir as convenções do Fleting, o caminho é **LoRA/QLoRA** sobre
`Qwen/Qwen2.5-Coder-3B-Instruct`:

1. Montar um dataset de pares *pergunta → resposta ideal* (de centenas a alguns milhares),
   gerado a partir dos projetos reais e revisado por pessoas.
2. Treinar o QLoRA (por exemplo com Unsloth ou PEFT). Precisa de GPU (~8 GB de VRAM) e não
   roda nesta máquina.
3. Mesclar o adaptador, converter para GGUF (`llama.cpp/convert_hf_to_gguf.py`), quantizar
   para `Q4_K_M` e usar `FROM ./flai-coder-q4_k_m.gguf` no Modelfile.

Antes de treinar, esgote prompt e contexto (seção 4). Na maior parte dos casos o ganho vem
de colocar o contexto certo no prompt, não de treinar.

---

## 3. O que ajustar: parâmetros e efeito

| Parâmetro | Padrão FLAI | Mais rápido / menos RAM | Mais qualidade | Efeito |
|---|---|---|---|---|
| Quantização | Q4_K_M | `q3_K_M` (~1,6 GB) | `q5_K_M` (~2,3 GB), `q8_0` (~3,3 GB) | Abaixo de Q4 o código sai pior |
| `num_ctx` | 4096 | 2048 | 8192 | RAM do KV cache e tempo de prompt |
| `num_predict` | 768 | 256–512 | 1024–2048 | Tamanho máximo da resposta (e tempo) |
| `num_batch` | 256 | 128 (menos RAM de pico) | 512 (prompt mais rápido) | Tokens de prompt processados por vez |
| `num_thread` | automático | nº de **núcleos físicos** | — | Mais threads que núcleos físicos fica mais lento |
| `temperature` | 0.2 | — | 0.1–0.3 para código | Valores altos inventam API |
| `top_p` | 0.9 | — | — | Corta tokens improváveis |
| `repeat_penalty` | 1.05 | — | 1.0–1.1 | Acima de 1.1 atrapalha código, que é repetitivo |
| `keep_alive` | `10m` | `0` libera a RAM na hora | `30m` | Evita recarregar ~2 GB a cada pergunta |

Para usar a quantização Q5:

```powershell
ollama pull qwen2.5-coder:3b-instruct-q5_K_M
```

### Variáveis de ambiente do servidor Ollama (RAM limitada)

```powershell
setx OLLAMA_FLASH_ATTENTION 1      # menos memória na atenção
setx OLLAMA_KV_CACHE_TYPE q8_0     # KV cache pela metade (exige flash attention)
setx OLLAMA_NUM_PARALLEL 1         # 1 requisição por vez (cada slot reserva KV cache)
setx OLLAMA_MAX_LOADED_MODELS 1    # nunca 2 modelos na RAM (ex.: chat + embeddings)
setx FLAI_KEEP_ALIVE 10m           # lido pelo FLAI em cada geração
```

Reinicie o `ollama serve` depois de alterar.

---

## 4. Respostas mais rápidas e melhores: o que o FLAI faz

**Roteamento.** Comandos fixos (`criar crud de X`, `fleting create page X`) continuam
determinísticos e instantâneos. Todo o resto vai para o modelo:

- `help` e `exit` só disparam quando a frase inteira é o comando (`ajuda`, `sair`, `q`).
- Intenção desconhecida, ou keyword com confiança abaixo de 0.3, vai para o LLM com o
  contexto do projeto.

- `analise ...` também vai para o modelo, com o arquivo citado no contexto.

**Tamanho da resposta adaptativo.** `max_tokens` (768) vale para perguntas curtas. Pedidos
longos (documente, explique, analise, gere, revise, verifique) usam o espaço livre do
contexto, até 2048 tokens, para não cortar a resposta no meio.

**Streaming.** O texto aparece token a token. `Ctrl+C` interrompe a geração e mantém o que já
saiu. A linha final mostra tokens e velocidade (`tok/s`).

**Contexto enviado ao modelo**, em ordem de prioridade (o que não cabe é cortado):

1. Resumo do projeto (páginas, models, controllers, migrations)
2. **Mapa do código**: cada `.py` de `app/` e `configs/` com classes e métodos (via `ast`).
   Custa poucas centenas de tokens e permite explicar ou documentar o projeto inteiro.
3. Arquivo citado na pergunta, na íntegra
4. Trechos do RAG (se o langchain estiver instalado)
5. Documentação Fleting/Flet

**Dicas de uso:**

- Peça uma coisa por vez: "documente `app/controllers`" funciona melhor que "documente tudo".
- Cite o arquivo pelo nome (`usuarios_view`) para que ele entre inteiro no contexto.
- Se aparecer "⚠️ Resposta cortada", peça por partes ou aumente `context_tokens` (8192 cabe na
  RAM; o tempo de prompt sobe um pouco).
- O mapa do código traz só nomes de classes e métodos. Para o modelo descrever o comportamento
  real, cite o arquivo: sem o conteúdo, ele pode generalizar.

### Configuração recomendada (`.flai/config.json`)

```json
{
  "model": "qwen2.5-coder:3b",
  "temperature": 0.2,
  "max_tokens": 768,
  "context_tokens": 4096,
  "use_optimized_model": true
}
```

---

## 5. Medir antes de ajustar

```powershell
ollama run flai-coder --verbose "explique o MVC do Fleting em 3 linhas"
```

A saída mostra:

- `load duration`: alto em toda pergunta indica que `keep_alive` está curto ou que falta RAM
  (swap).
- `prompt eval rate` (tokens/s): ritmo de leitura do contexto. Contexto grande demais pesa
  aqui.
- `eval rate` (tokens/s): ritmo de geração. Em CPU comum, o 3B Q4 gera algo como 8–20 tok/s.

O FLAI também mostra, ao fim de cada resposta,
`📊 tokens: prompt X + resposta Y / contexto N`. Se X ficar perto de N, o contexto está
sendo cortado.

| Sintoma | Ajuste |
|---|---|
| Demora vários segundos antes de começar | Subir `keep_alive`; checar `ollama ps` |
| "RAM insuficiente" com o modelo já carregado | Corrigido: o guard agora desconta a RAM dos derivados `flai-*` carregados |
| Demora proporcional ao tamanho da pergunta | Reduzir `num_ctx` ou citar arquivos específicos |
| Resposta cortada | Subir `max_tokens` |
| Inventa funções do Flet | Baixar `temperature`; garantir a doc do Flet no contexto |
| Sistema travando / swap | `q3_K_M`, `num_ctx` 2048, `OLLAMA_KV_CACHE_TYPE=q8_0`, fechar o navegador |
