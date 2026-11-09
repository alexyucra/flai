# Documentação Oficial do FLAI

FLAI (Framework Local de IA) é uma ferramenta de linha de comando que integra modelos de linguagem locais (via Ollama) ao ecossistema de desenvolvimento Fleting (Python + Flet). 

Ele permite analisar projetos, gerar código (CRUD, formulários) e interagir com o código-fonte através de um assistente de IA privado e offline.

## Índice

1. Visão Geral
2. Arquitetura do Projeto
3. Pré-requisitos e Instalação
4. Guia de Uso

- Comando init
- Comando shell
- Comando chat

5. Funcionalidades Principais

- REPL Interativo (Núcleo)
- Geração de Código (CRUD e Formulários)
- Análise e Busca no Projeto
- Gerenciamento do Ollama
- Sistema de Agentes (Router)

6. Estrutura de Diretórios e Arquivos

- Projeto Fleting
- Diretório .flai (Dados)
- Código Fonte do FLAI (ia/)

7. Estratégia de Otimização para Hardware Local

8. Contribuindo e Próximos Passos

___ 
## 1. Visão Geral

O FLAI foi projetado para desenvolvedores que desejam usar IA localmente, sem depender de APIs externas, garantindo privacidade e controle. Ele se integra nativamente com projetos Fleting, fornecendo um assistente contextualizado que entende a estrutura MVC (Models, Controllers, Views) do seu projeto.

### Principais características:

- 🤖 Modelos Locais: Usa Ollama para executar modelos como Llama 3.2, Phi-3 e DeepSeek Coder.
- 🚀 Geração de Código: Cria automaticamente CRUDs e formulários Flet.
- 🔍 Análise Contextual: Escaneia o projeto e fornece contexto preciso para a IA.
- 💾 Offline e Privado: Toda a execução é local.
- 🧠 REPL Inteligente: Interface conversacional com roteamento de intenções.
- ⚡ Otimizado para Hardware: Detecta recursos da máquina e otimiza o modelo.

## 2. Arquitetura do Projeto
A estrutura combina um projeto Fleting padrão com o diretório de dados .flai e o código-fonte do framework FLAI.

```shell
meu_projeto_fleting/          # ⬅️ Raiz do seu projeto Fleting
├── app/                      # Código Flet (MVC)
├── .fleting                  # Arquivo marcador (identifica o projeto)
├── .flai/                    # Diretório de dados do FLAI (criado pelo init)
│   ├── vectordb/             # Banco vetorial (ChromaDB - RAG)
│   ├── sessions/             # Históricos de conversa
│   └── config.yaml           # Configuração do projeto (modelo ativo, etc.)
│
└── ia/                       # ⬅️ Código fonte do framework FLAI
    └── flai/
        ├── cli/              # Interface de linha de comando
        ├── commands/         # Comandos: init, shell, chat
        ├── core/             # Núcleo: agentes, intent, executores
        ├── utils/            # Utilitários: scanner, context, ollama_manager
        ├── helpers/          # Scripts auxiliares (otimização)
        └── templates/        # Templates para geração de código
```

## 3. Pré-requisitos e Instalação

- Python 3.10+ e pip.

- Ollama instalado no sistema(manualmente):

  - Windows: Baixe o instalador em ollama.com

  - Linux/macOS: curl -fsSL https://ollama.com/install.sh | sh

  - (Opcional, para RAG): Instalar dependências LangChain.

```bash
pip install langchain langchain-community chromadb
```

Projeto Fleting: O FLAI é executado dentro de um projeto Fleting (que deve conter o arquivo .fleting na raiz).


## 4. Guia de Uso
Todos os comandos são executados no terminal, a partir da raiz do seu projeto Fleting.
```shell
cd meu_projeto_fleting/
pip install flet
pip install fleting
pip install flai-ia

ls 
├── .fleting                  # Arquivo marcador (identifica o projeto)
├── .flai/                    # Diretório de dados do FLAI (criado pelo init)

fleting init app
cd app

app> flai init ia
app> flai shell


```

### Comando init

Prepara o ambiente de IA local, detecta hardware, faz o download do modelo e o otimiza.

```bash
flai init ia
```

**O que acontece?**

- Verifica RAM, CPU e se o Ollama está instalado.

- Inicia o servidor do Ollama (se não estiver rodando).

- Baixa o modelo escolhido.

- Executa o script optimize_model.ps1 (no Windows) para criar um modelo otimizado (ex: flai-coder) com parâmetros ajustados (contexto, batch, etc.).

- Salva as configurações em .flai/config.json.

### Comando shell

Inicia um shell interativo (REPL) com um assistente de IA restrito ao projeto atual. Este é o comando principal para usar o FLAI.

```bash
flai shell 
```

Dentro do Shell:
Você pode usar comandos de linguagem natural. A IA só tem acesso aos arquivos do projeto listados no contexto.

- Comando de Exemplo	Ação
  - criar crud de produtos com nome, preco	Gera CRUD completo para a entidade "produtos"
  - criar form de contato	Gera um formulário Flet
  - analise o controller user	Mostra e analisa o código do controller
  - onde está a função de autenticação?	Busca no código por palavras-chave
  - ajuda ou ?	Exibe a ajuda com todos os comandos
  - sair ou exit	Sai do shell

### Comando chat
Uma versão mais simples do chat, sem o roteador de intenções. Útil para conversas mais livres ou quando o roteador falha.

```bash
flai chat
```

## 5. Funcionalidades Principais

### 1. Arquitetura e Estrutura

|Componente	|Status	|Observação|
|-----------|-------|----------|
|Estrutura de diretórios	|✅ OK	|Organizada e modular|
|Sistema de registro (registry)	|✅ OK	|Singleton por projeto implementado|
|Injeção de dependência	|✅ OK	|Componentes compartilhados via registro|
|Importações	|✅ OK	|Sem sys.path.insert() agora|

### 2. Core Components
|Componente	|Status	|Observação|
|-----------|-------|----------|
|RouterAgent	|✅ OK|	Com type hints e suporte a HelpAgent|
|HelpAgent	  |✅ OK|	Diagnóstico inteligente implementado|
|IntentParser	|✅ OK|	Com suporte a help contextual|
|AgentManager	|✅ OK|	Singleton, pipeline sync/async|
|LLMAgent	    |✅ OK|	Fallback com validação|
|RAGManager	  |✅ OK|	Indexação e busca funcional|
|IntegratedRAG	|✅ OK|	Singleton por projeto|
|ContextManager	|✅ OK|	Múltiplas fontes de contexto|
|KnowledgeManager	|✅ OK|	Entidades e packs|

### 3. Segurança
|Item	|Status	|Observação|
|-----|-------|----------|
| ShellExecutor seguro	|✅ OK|	Comandos permitidos listados|
| Sanitização de input	|✅ OK|	Em shell_unified.py|
| Validação de modelos	|✅ OK|	Regex para nomes de modelo|
| Path traversal prevention	|✅ OK|	normalize_path()|

### 4. Cross-Platform
|Plataforma	|Status	|Observação|
|-----------|-------|----------|
|Windows	|✅ OK|	PowerShell script, paths|
|Linux	|✅ OK|	Bash script, paths|
|macOS	|✅ OK|	Bash script, paths|

### 5. Logging e Erros
|Item	|Status	|Observação|
|-----|-------|----------|
|Sistema de logging unificado	|✅ OK|	flai/core/logging/|
|Decoradores de erro	|✅ OK|	handle_errors, retry_on_failure|
|Tratamento de exceções	|✅ OK|	Com logging apropriado|


##
REPL Interativo (Núcleo)
Implementado em flai/cli/repl.py e flai/commands/shell.py.

Fornece um prompt 💬 Você:.

Utiliza o RouterAgent para classificar a intenção e executar a ação correta (criar CRUD, analisar código, etc.).

Mantém o contexto da conversa limitado ao diretório do projeto, garantindo segurança e foco.

Geração de Código (CRUD e Formulários)
CRUD Agent: Orquestra a criação de uma página, um model e executa as migrations via comandos do Fleting.

Form Agent: Gera código Python/Flet para formulários UI, baseado em uma lista de campos.

Os geradores são "puros" (não usam LangChain) e baseiam-se em templates de string.

Exemplo de saída de um comando criar crud:

log
🚀 Criando CRUD para: produtos
📄 Criando página...
✅ Página criada
🗄️ Criando model...
✅ Model criado
🔄 Executando migrations...
✅ CRUD 'produtos' criado com sucesso!
Análise e Busca no Projeto
Project Agent: Mapeia a estrutura do projeto (models, controllers, pages).

Intent Parser: Usa expressões regulares para extrair intenções e entidades de texto livre.

Busca: Permite localizar código fonte com palavras-chave.

Gerenciamento do Ollama
OllamaManager (em utils/ollama_manager.py):

Detecta a instalação do Ollama em múltiplos caminhos (Windows, Linux, macOS).

Inicia o servidor em background (sem janelas no Windows).

Gerencia download e cache de modelos.

Fornece métodos run_model (via API HTTP) e run_model_cli (fallback).

Usa um sistema de cache para evitar verificações repetidas de sistema.

Sistema de Agentes (Router)
Arquitetura que separa a lógica de intenção da execução:

RouterAgent (core/agents/router_agent.py):

Recebe a entrada do usuário.

Chama o IntentParser para classificar a intenção.

Roteia para o agente específico (CRUDAgent, FormAgent, ProjectAgent, DBAgent).

Intent Parser (core/intent/):

IntentPatterns: Define regex para intenções como create_crud, create_form, analyze, where, help, exit.

IntentParser: Orquestra o parsing e extrai entidades e campos.

Executors (core/executors/):

FletingExecutor: Encapsula comandos do CLI do Fleting (fleting create page, fleting db make).

ShellExecutor: Permite executar comandos shell arbitrários (com cautela).

Estrutura de Diretórios e Arquivos
Projeto Fleting
app/ → Código principal do aplicativo Flet (seguindo MVC).

.fleting → Arquivo que sinaliza que este diretório é a raiz de um projeto Fleting.

Diretório .flai (Dados)
vectordb/ → Índice vetorial do ChromaDB (se o RAG LangChain estiver ativo).

sessions/ → Futuro: armazenará sessões de conversa.

config.json → Configuração do projeto:

json
{
  "model": "flai-coder",
  "project_path": "/caminho/do/projeto",
  "setup_date": "2023-10-27T10:00:00",
  "ollama_path": "C:/Program Files/Ollama/ollama.exe",
  "optimized_for_low_ram": false,
  "status": "ready"
}
Código Fonte do FLAI (ia/)
flai/cli/ → CLI com Typer/Click, menus de ajuda e console rich.

flai/commands/ → Implementação dos comandos init, shell, chat.

flai/core/ → Lógica central (agentes, intenção, executores, RAG).

flai/utils/ → Funções auxiliares (scanner de projeto, sistema, cache, manager do Ollama).

flai/helpers/ → Scripts extras (ex: optimize_model.ps1).

flai/templates/ → Templates para geração de código (CRUD, forms).

Estratégia de Otimização para Hardware Local
O FLAI é especialmente inteligente para rodar bem em máquinas com recursos limitados (como ThinkPads antigos ou laptops de entrada).

Detecção de Hardware: Ao rodar flai init, o sistema mede a RAM total e disponível.

Recomendação de Modelo: Baseado na RAM, recomenda modelos:

< 4 GB: deepseek-coder:1.3b (modelo ultra-leve).

4-8 GB: llama3.2:3b, phi3:mini ou deepseek-coder:1.3b.

8 GB: Modelos maiores como codellama:7b.

Otimização Pós-Download: No Windows, o script optimize_model.ps1 cria um novo Modelfile com parâmetros otimizados:

dockerfile
FROM deepseek-coder:1.3b
PARAMETER num_ctx 1024
PARAMETER num_batch 128
PARAMETER num_predict 256
PARAMETER temperature 0.8
PARAMETER repeat_penalty 1.1
Isso cria um modelo chamado flai-coder, que reduz o uso de memória e acelera as respostas.

Cache de Verificações: O OllamaManager utiliza um cache para evitar verificações repetidas do sistema, acelerando inícios subsequentes.

Contribuindo e Próximos Passos
O FLAI é um projeto open-source em evolução. De acordo com o arquivo de especificação, as seguintes funcionalidades estão planejadas para a "Fase 2":

Completa implementação do RAG com LangChain: Indexação semântica de todo o código do projeto.

MCP (Model Context Protocol): Builders de contexto mais estruturados.

Geração de Controllers e Views: Além de CRUD e forms.

Sistema de Memória: Histórico de conversa persistente em sessions/.

Como contribuir:

Clone o repositório.

Crie um ambiente virtual: python -m venv venv

Instale as dependências: pip install -r requirements.txt

Implemente uma funcionalidade pendente (consulte a checklist no arquivo flai-ia.md).

Envie um Pull Request.

Documentação gerada com base no código-fonte em flai-ia.md. Para mais informações, consulte os comentários no código ou acesse o canal do YouTube @LatinDev.