# Instalação

## Requisitos

| Item | Mínimo | Recomendado |
|---|---|---|
| Python | 3.11 | 3.12 |
| RAM livre | ~2 GB (modelo 1.5B) | 3–4 GB (modelo 3B) |
| Disco | 1 GB por modelo | 3 GB |
| Sistema | Windows, Linux ou macOS | — |
| GPU | não é necessária | acelera bastante, se houver |

!!! info "Por que tão pouco?"
    O FLAI mede a RAM livre e ajusta o tamanho do contexto do modelo para caber. Em CPU, o
    `qwen2.5-coder:3b` gera ~14–16 tokens/s em um notebook comum.

## 1. Ollama

O Ollama roda os modelos localmente.

=== "Windows"

    Baixe e instale em [ollama.com/download](https://ollama.com/download).
    O FLAI encontra o executável sozinho (não precisa estar no PATH) e inicia o servidor
    em segundo plano, sem abrir janela.

=== "Linux"

    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

=== "macOS"

    Baixe o app em [ollama.com/download](https://ollama.com/download) ou use
    `brew install ollama`.

Confira:

```bash
ollama --version
```

## 2. FLAI e Fleting

```bash
pip install fleting flai-ia
```

Extras opcionais:

```bash
pip install "flai-ia[rag]"   # busca semântica com LangChain (embeddings via Ollama)
```

Sem o extra `rag`, o FLAI usa a API HTTP do Ollama e um divisor de texto interno. A busca
semântica continua disponível, só que mais simples.

## 3. Projeto Fleting

O FLAI trabalha **dentro** de um projeto Fleting (pasta com o arquivo `.fleting`):

```bash
fleting init meu_app
cd meu_app
```

## 4. Configurar a IA: `flai init`

```bash
flai init qwen2.5-coder:3b
```

O que acontece:

1. Mede RAM e CPU e verifica o Ollama (inicia o servidor se estiver parado).
2. Mostra os modelos recomendados para a sua RAM e baixa o escolhido.
3. Cria o modelo otimizado (`flai-coder` ou `flai-<modelo>:ctx<N>`) com contexto, tamanho de
   resposta e temperatura ajustados.
4. Salva `.flai/config.json` no projeto.

Modelos sugeridos pelo `init`:

| RAM disponível | Opções |
|---|---|
| < 4 GB | `qwen2.5-coder:1.5b`, `qwen2.5-coder:3b` |
| ≥ 4 GB | **`qwen2.5-coder:3b`** (recomendado), `qwen2.5-coder:1.5b`, `llama3.2:3b` |

## 5. Usar

```bash
flai shell
```

Na primeira mensagem o modelo já está carregado: o FLAI aquece o cache enquanto você digita.
Experimente:

```text
o que faz o usuarios_controller?
criar crud de produtos com os campos: nome, preco:float, estoque:int
sim
/contexto
/desfazer
```

## Instalação para desenvolvimento

```bash
git clone https://github.com/alexyucra/flai.git
cd flai
uv venv && uv pip install -e ".[rag]" pytest      # ou: python -m venv .venv && pip install -e .
.venv/Scripts/python -m pytest flai/test -q          # Windows
```

## Atualizar

```bash
pip install -U flai-ia fleting
ollama pull qwen2.5-coder:3b
```

Depois de trocar de modelo ou de RAM, use `/tokens refresh` no shell para recalcular o
contexto.
