# Solução de problemas

## Ollama

??? question "`Ollama não está pronto` / `could not connect to a running Ollama instance`"
    O servidor não está rodando. O FLAI tenta iniciá-lo sozinho. Se não conseguir:
    ```bash
    ollama serve          # deixe este terminal aberto
    ```
    Confira em outro terminal com `ollama list`.

??? question "O servidor some depois que um script termina"
    Quando é o FLAI que inicia o Ollama, ele encerra o servidor ao sair. Para manter o servidor
    sempre ligado, inicie-o você mesmo (`ollama serve` ou o app do Ollama) antes do
    `flai shell`.

??? question "`model not found`"
    ```bash
    ollama pull qwen2.5-coder:3b
    ```
    O FLAI não baixa modelos durante a conversa, só no `flai init`.

## Memória e velocidade

??? question "`RAM insuficiente para 'qwen2.5-coder:3b'`"
    O modelo não cabe nem com folga mínima. Opções:

    - feche programas pesados (navegador, IDE) e rode `/tokens refresh`;
    - use `qwen2.5-coder:1.5b` em `.flai/config.json`;
    - ative `OLLAMA_KV_CACHE_TYPE=q8_0` e `OLLAMA_FLASH_ATTENTION=1`.

??? question "`Pouca RAM livre: rodando com folga mínima`"
    Funciona, mas o sistema pode ficar lento ou usar disco (swap). Feche programas se
    perceber travamentos.

??? question "A primeira resposta demora ~10 s; as seguintes, ~2 s"
    Normal. O system prompt é processado uma vez e fica em cache. Ele é reprocessado quando o
    mapa do código muda (depois de criar ou alterar métodos) ou quando o modelo é
    descarregado (`FLAI_KEEP_ALIVE`, padrão 10 min).

??? question "Resposta lenta"
    Na CPU a geração fica em ~14–16 tokens/s com o 3B. A linha `📊` mostra prompt, resposta e
    tok/s. Peça respostas por partes; documentação longa leva 1–2 min.

??? question "`⚠️ Resposta cortada`"
    Pedidos comuns têm limite de ~768 tokens e documentação de 2048. Peça por partes
    ("documente app/controllers") ou aumente `context_tokens`.

## Assistente

??? question "`⚠️ Contexto de 2048 tokens é pequeno para o assistente`"
    Use `"context_tokens": 8192` (ou no mínimo 4096) em `.flai/config.json`. No 3B, 8192
    custa só ~300 MB de RAM.

??? question "O modelo respondeu sem ler o arquivo / inventou código"
    Cite o arquivo pelo nome (`usuarios_controller`) para que ele entre inteiro no contexto,
    ou pergunte "leia o arquivo X e ...". Confira o foco com `/contexto`.

??? question "`⚠️ Alteração NÃO aplicada`"
    A proposta tinha erro de sintaxe (e o modelo não conseguiu corrigir) ou você cancelou.
    O arquivo está intacto. Reformule de forma mais específica, por exemplo pedindo um
    método inteiro: "reescreva o método render da usuarios_view para ...".

??? question "Desfazer uma alteração"
    `/desfazer` (pode repetir). Os backups ficam em `.flai/backups/`.

??? question "O `sim` fez outra coisa"
    O `sim` executa a **última** sugestão (veja em `/contexto` → pergunta pendente). Se não
    houver sugestão pendente, ele vai como mensagem comum. Escreva o pedido completo quando
    houver dúvida.

## CRUD e Fleting

??? question "`Já existe migration pendente com código`"
    Há uma migration da entidade ainda não aplicada e que não está vazia. Revise o arquivo em
    `migrations/` e rode `fleting db migrate`. O FLAI não sobrescreve código seu.

??? question "Aviso de migration duplicada vazia"
    Apague o arquivo indicado (`migrations/00X_<entidade>.py` só com `pass`).

??? question "`Fleting não encontrado`"
    Instale no **mesmo** Python do FLAI: `pip install fleting`.

## Windows

??? question "`UnicodeEncodeError: 'charmap' codec can't encode character`"
    O console está em cp1252 e não exibe emojis. Use o Windows Terminal ou defina UTF-8:
    ```powershell
    $env:PYTHONIOENCODING = "utf-8"
    chcp 65001
    ```

## Diagnóstico

```bash
flai shell          # mostra o plano de RAM/contexto na abertura
/tokens             # dentro do shell: orçamento e última resposta
/contexto           # foco, memória e alterações
ollama ps           # modelo carregado, RAM usada, CPU/GPU
ollama run flai-qwen2.5-coder-3b:ctx8192 --verbose "oi"   # velocidades
```

Logs: `~/.flai/logs/flai.log`.
