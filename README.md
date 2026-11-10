<div align="center">

# 🤖 FLAI

### Seu assistente de IA que roda no seu computador e programa com você em Fleting

**Converse em português. O FLAI cria páginas, models, migrations e explica o seu código,<br>sem enviar uma linha sequer para a nuvem.**

[![PyPI](https://img.shields.io/pypi/v/flai-ia?color=blue&label=PyPI)](https://pypi.org/project/flai-ia/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Ollama](https://img.shields.io/badge/IA-Ollama%20local-black)](https://ollama.com)
[![Fleting](https://img.shields.io/badge/framework-Fleting-purple)](https://alexyucra.github.io/Fleting/)

[Começar em 3 minutos](#-comece-em-3-minutos) · [Veja funcionando](#-veja-o-flai-em-ação) · [Recursos](#-o-que-o-flai-faz) · [Contribuir](#-contribua)

</div>

---

## 💡 Por que o FLAI?

Assistentes de IA na nuvem são ótimos, até você precisar trabalhar com **código privado**,
**sem internet** ou **sem pagar assinatura**. O FLAI nasceu para isso:

| | FLAI | Assistentes na nuvem |
|---|:---:|:---:|
| 🔒 Seu código fica na sua máquina | ✅ | ❌ |
| 💰 Custo | **Grátis** | Assinatura / créditos |
| 📡 Funciona offline (após baixar o modelo) | ✅ | ❌ |
| 🧩 Conhece a estrutura Fleting (MVC, rotas, migrations) | ✅ | Genérico |
| ⚙️ Executa a CLI do Fleting por você | ✅ | ❌ |
| 🧠 Ajusta-se à RAM do seu PC | ✅ | n/a |

---

## 🎬 Veja o FLAI em ação

```text
💬 Você: criar crud de produtos
🚀 Criando CRUD para: produtos
✅ fleting create page produtos
✅ fleting db init
✅ fleting db make produtos
⚠️ Executar 'fleting db migrate'? [s/N]: s
✅ fleting db migrate
🤖 FLAI: ✅ CRUD 'produtos' criado com sucesso!

💬 Você: o que faz o produtos_controller?
🤖 FLAI: O produtos_controller.py gerencia a lógica da página de produtos.
         A classe ProdutosController é inicializada com o ProdutosModel e
         expõe get_title(), que retorna o título "Produtos".
📊 tokens: prompt 1085 + resposta 97 / contexto 2048 · modelo flai-qwen2.5-coder-1.5b:ctx2048
```

> Saída real de um teste com `qwen2.5-coder:1.5b` rodando localmente.

---

## 🚀 Comece em 3 minutos

**1. Instale o [Ollama](https://ollama.com) e baixe dois modelos leves (~1,3 GB no total):**

```bash
ollama pull qwen2.5-coder:1.5b     # a IA que responde
ollama pull nomic-embed-text       # a busca inteligente no código
```

**2. Instale o FLAI:**

```bash
pip install "flai-ia[rag]"
# ou, com uv (mais rápido):
uv pip install "flai-ia[rag]"
```

**3. Crie um projeto e converse:**

```bash
fleting init minha_loja
cd minha_loja
flai init
flai shell -m qwen2.5-coder:1.5b
```

Pronto! Digite `criar crud de clientes` e veja a mágica acontecer. ✨

---

## ✨ O que o FLAI faz

### 🛠️ Gera código Fleting conversando
| Você diz | O FLAI faz |
|---|---|
| `criar crud de pedidos` | Página + model + controller + rota + migration, e aplica no banco |
| `criar página contato` | `fleting create page contato` |
| `criar model cliente` | `fleting create model cliente` |
| `fleting list pages` · `fleting db status` · `fleting doctor` | Roda a CLI do Fleting direto do chat |

### 🧠 Entende o seu projeto
- Pergunte com `?`: *"como adiciono um campo preço no model produtos?"*
- **Busca semântica (RAG)**: encontra o trecho certo pelo significado, não só pela palavra.
  Ex.: *"onde fica a verificação de senha?"* leva ao `login_controller.py`.
- Índice local leve, **sem banco vetorial pesado**.

### 💻 Roda bem até em PC modesto
- Mede a **RAM livre** e calcula o maior contexto seguro antes de carregar o modelo.
- Cria automaticamente um **modelo otimizado** (`flai-<modelo>:ctx<N>`) com contexto reduzido.
- Mostra os **tokens usados** e avisa quando vale aumentar a configuração, e só sugere valores que a sua RAM aguenta.
- Sem RAM suficiente? O FLAI avisa e recomenda um modelo menor, **em vez de travar o seu computador**.

### 🛡️ Seguro por padrão
- Pede confirmação antes de comandos que apagam arquivos ou rodam migrations.
- Bloqueia nomes perigosos (`../`), comandos fora da lista e URLs inseguras.
- Painel web acessível só pela sua máquina (`127.0.0.1`).
- Nenhum provedor de IA externo vem ativado.

---

## 🖥️ Qual modelo escolher?

| Modelo | Disco | RAM livre | Ideal para |
|---|---|---|---|
| `qwen2.5-coder:1.5b` | ~1 GB | ~3 GB | **Começar**, notebooks, uso diário |
| `qwen2.5-coder:7b` | ~4,7 GB | ~6,5 GB | Respostas mais elaboradas |

Não sabe quanto tem livre? Abra o `flai shell` e digite `/tokens`. O FLAI mostra tudo.

---

## ⌨️ Comandos do shell

| Comando | Para quê |
|---|---|
| `/help` | Ajuda completa |
| `/tokens` · `/tokens refresh` | RAM, contexto e uso de tokens |
| `/rag index` · `/rag search <texto>` | Indexar e buscar no código |
| `/history` · `/export` · `/clear` | Histórico da conversa |
| `/exit` | Sair |

Ajuste fino em `.flai/config.json`:

```json
{ "model": "qwen2.5-coder:1.5b", "context_tokens": 2048, "max_tokens": 512, "use_optimized_model": true }
```

---

## 🏗️ Como funciona

```text
 Você ──► FLAI Shell ──► Roteador de intenções
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
   CLI do Fleting      RAG (busca no código)   Guarda de RAM/tokens
   (create, db...)            │                    │
                              └──────► Ollama (IA local) ◄──┘
```

---

## 🗺️ Roadmap

- [x] CRUD completo via CLI do Fleting
- [x] IA local com controle de RAM e tokens
- [x] Busca semântica leve (RAG)
- [x] Travas de segurança e confirmações
- [ ] Campos do CRUD (`com nome, preco`) gerados direto no model
- [ ] Login no painel web
- [ ] Mais modelos e idiomas

Tem uma ideia? [Abra uma issue](https://github.com/alexyucra/flai/issues). Adoramos sugestões!

---

## 🤝 Contribua

O FLAI é **open source** e feito pela comunidade. Toda ajuda conta:

- ⭐ **Dê uma estrela** no repositório: ajuda muito o projeto a ser encontrado!
- 🐛 Reporte bugs e sugira recursos nas [issues](https://github.com/alexyucra/flai/issues).
- 🔧 Envie um PR: veja o [CONTRIBUTING.md](CONTRIBUTING.md).

Para desenvolver:

```bash
git clone https://github.com/alexyucra/flai.git && cd flai
uv venv --python 3.12 .venv
uv pip install -e ".[rag,dev]"
uv run pytest flai/test/test_security_controls.py flai/test/test_resources.py flai/test/test_rag.py -v
```

---

## 📚 Aprenda mais

- 📖 [Documentação do Fleting](https://alexyucra.github.io/Fleting/)
- 🎥 [Canal LatinDev no YouTube](https://www.youtube.com/@LatinDev) · [Curso completo de Fleting](https://youtu.be/sm3jWfd1ceU)
- 📂 [Documentação do FLAI](docs/)

---

<div align="center">

**Se o FLAI te ajudou, deixe uma ⭐ e compartilhe com outros devs!**

Feito com ❤️ por [Alex Yucra](https://github.com/alexyucra) e a comunidade · Licença [MIT](LICENSE)

</div>
