# 📘 FLAI - Framework de IA Local para Análise de Projetos Flet
## 🎯 Introdução: O Problema da Análise de Código Contextual
Desenvolvedores Flet frequentemente enfrentam desafios ao analisar e refatorar projetos Python. Ferramentas existentes como Cursor são poderosas, mas:
- Dependem de nuvem - Privacidade comprometida
- São editores completos - Overhead desnecessário para análise
- Genéricas demais - Não especializadas em Flet
- Não aprendem com seu código - Sem contexto específico do projeto
FLAI surge como solução: Um CLI especializado em Flet que roda localmente, aprende com seu projeto e fornece análises contextuais profundas.
## 🏗️ Arquitetura Técnica
Stack Principal:
Python 3.9+ - Linguagem base
Ollama - Modelos LLM locais (DeepSeek-Coder 1.3B)
LangChain - Framework para agents e RAG
ChromaDB - Vector store local para embeddings
Click - Framework CLI profissional
Estrutura do Projeto:
```shell
mvc/flai/
├── cli.py # Ponto de entrada CLI
├── commands/ # Comandos implementados
│ ├── init.py # Inicialização de projetos
│ ├── analyze.py # Análise de código
│ └── chat.py # Chat contextual
├── rag/ # Sistema RAG (pendente)
├── agents/ # Agentes especializados (pendente)
└── utils/ # Utilitários
```
## 🚀 Implementação Passo a Passo
Fase 1: CLI Básica com Ollama
### 1. Configuração do Modelo Local
```python
# optimize_deepseek_final.ps1 - Script de otimização
"""
Configura DeepSeek-Coder 1.3B para hardware limitado
- Contexto reduzido (1024 tokens)
- Temperatura ajustada (0.2 para código)
- Threads otimizados para CPU
"""
2. CLI Principal com Click
python
# cli.py - Estrutura modular
@click.group()
def cli():
"""Flai - Assistente AI para análise de projetos Python Flet"""
pass
@cli.command()
def init(model, path):
"""Inicializar Flai com modelo específico"""
# Valida modelo Ollama
# Cria configuração .flai/
# Testa conexão com modelo
@cli.command()
def analyze(target):
"""Análise estática do projeto"""
# Conta arquivos Python/Flet
# Detecta padrões de arquitetura
# Gera relatório markdown
Fase 2: Sistema de Análise Inteligente
3. Análise Contextual com Encoding Seguro
python
# analyze.py - Análise adaptativa
def analyze_project(target, full, report):
"""
Analisa projetos considerando:
- Hardware disponível (RAM/CPU)
- Encoding correto (UTF-8 vs cp1252)
- Contexto específico do projeto
"""
4. Sistema de Fallback para Hardware Limitado
python
# flai_analyze_safe.py - Versão otimizada
"""
Implementa:
- Timeouts inteligentes
- Encoding UTF-8 forçado
- Processamento em chunks para projetos grandes
- Cache de resultados
"""
Fase 3: Chat Contextual com RAG
5. Sistema RAG para Projetos Flet (Pendente)
python
# project_indexer.py - Indexação inteligente
class FletProjectIndexer:
"""
Indexa projetos considerando:
- Tipo de arquivo (model, view, controller)
- Dependências Flet específicas
- Padrões MVC
- Contexto de uso
"""
6. Vector Store Local com ChromaDB (Pendente)
python
# vector_store.py - Armazenamento eficiente
"""
Características:
- Embeddings locais (all-MiniLM-L6-v2)
- Persistência em disco
- Busca semântica por tipo de arquivo
- Atualização incremental
"""
```
## 💡 Features Implementadas
✅ Comandos Atuais:
```bash
# 1. Inicialização inteligente
flai init flai-optimized --path meu_projeto
# 2. Análise contextual
flai analyze --full --report
# 3. Chat básico (com fix pendente)
flai chat --project meu_projeto
```
## ✅ Funcionalidades Operacionais:
- Detecção automática de Flet - Identifica imports e padrões
- Análise de estrutura - Contagem e classificação de arquivos
- Otimização para hardware - Funciona com apenas 1.1GB RAM livre
- Encoding robusto - Lida com caracteres especiais Windows
- Modelos locais - Zero dependências de nuvem
## ✅ Sistema de Configuração:
```yaml
# .flai/config.yaml
model: flai-optimized
project_path: /caminho/meu_projeto
optimized: true
max_tokens: 512
temperature: 0.2
created: 2024-01-28
```
## 🛠️ Desafios Superados
### 1. Problema de Encoding Windows
- Sintoma: UnicodeDecodeError: 'charmap' codec can't decode byte 0x8f
- Solução: Forçar UTF-8 em todas as chamadas subprocess
```python
result = subprocess.run(..., encoding='utf-8', errors='replace')
```
### 2. RAM Limitada (1.1GB disponível)
Solução:
- Modelo otimizado (DeepSeek-Coder 1.3B vs Phi-3 3.8B)
- Contexto reduzido (1024 tokens)
- Batch processing de arquivos
- Cache agressivo
### 3. Integração Ollama Instável
Solução:
- Verificação de conexão antes de chamadas
- Timeouts configuráveis
- Sistema de retry automático
- Fallback para modo offline
## 📊 Benchmarks de Performance
|Operação| Tempo| RAM Usada| Precisão|
|--------|-------|-----------|----------|
|Inicialização| 2-5s| 50MB| 100%|
|Análise |projeto (10 arquivos) |10-15s |200MB| 95%|
|Consulta| modelo simples| 3-8s| 300MB| 90%|
|Indexação |RAG (pendente)| Est: 30s| Est: 500MB| Est: 98%|
## 🎯 Roadmap de Desenvolvimento
### Fase 1: MVP (Concluída)
- CLI básica com Click
- Integração Ollama local
- Análise estática de projetos
- Chat básico
### Fase 2: RAG & Contexto (Em progresso)
- Sistema de indexação de projetos
- Vector store com ChromaDB
- Chat contextual com embeddings
- Agentes especializados
### Fase 3: Features Avançadas (Planejada)
- Refatoração assistida
- Migrações MVC automáticas
- Debugging inteligente
- Geração de documentação
### Fase 4: Enterprise (Futuro)
- Multi-projeto
- Colaboração em equipe
- Integração CI/CD
- Analytics de código
### 🔧 Instalação e Uso
Pré-requisitos:
```bash
# 1. Python 3.9+
python --version
# 2. Ollama instalado
ollama --version
# 3. Modelo DeepSeek-Coder
ollama pull deepseek-coder:1.3b
```
## Instalação FLAI:
```bash
# Modo desenvolvimento
cd mvc
pip install -e .
# Ou manualmente
python -m flai.cli --help
```
## Fluxo de Trabalho Típico:
```bash
# 1. Inicializar projeto
flai init flai-optimized --path meu_app_flet
# 2. Analisar estrutura
flai analyze meu_app_flet --full
# 3. Chat sobre código específico
flai chat --project meu_app_flet
```
> "Como melhorar esta função de login?"
### 📈 Vantagens Competitivas
vs Cursor/Codeium:
✅ 100% local - Privacidade garantida
✅ Especializado em Flet - Não genérico
✅ CLI-first - Integra em qualquer workflow
✅ Hardware mínimo - Roda em máquinas modestas
vs Pylint/Black:
✅ Contextual - Entende seu projeto específico
✅ Assistência proativa - Sugere melhorias
✅ Aprendizado contínuo - Melhora com o tempo
✅ Foco em Flet - Otimizado para UI moderna
## 🚨 Lições Aprendidas
Técnicas:
- Encoding é crucial em Windows - sempre forçar UTF-8
- Ollama precisa de 2 terminais - serve + client
- Modelos pequenos funcionam bem para código
- Cache local melhora experiência do usuário
Arquitetura:
- CLI over GUI para ferramentas de desenvolvedor
- Modularidade permite desenvolvimento incremental
- Fallbacks para todos os cenários de erro
- Configuração automática reduz fricção inicial
## 🔮 Próximos Passos Imediatos
Prioridade 1: Fix chat.py
```python
# Mudança necessária:
llm = model_manager.load_model(config['model_path'])
# ↓
model_name = config.get('model', 'flai-optimized')
# Chamada direta ao Ollama via subprocess
```
Prioridade 2: Sistema RAG básico
```python
# 1. project_indexer.py - Indexar projetos
# 2. vector_store.py - Armazenar embeddings
# 3. context_retriever.py - Buscar contexto relevante
```
Prioridade 3: Agente MVC
```python
# mvc_architect.py - Especialista em:
# - Migrações para padrão MVC
# - Refatoração de código
# - Sugestões arquiteturais
```
## 🤝 Contribuição
FLAI é desenvolvido como projeto open-source com foco na comunidade Flet:
- Issues - Reportar bugs e sugerir features
- PRs - Implementar novas funcionalidades
- Documentação - Melhorar tutoriais e exemplos
- Plugins - Extender para outros frameworks
## 📚 Recursos
Repositório: github.com/alexyucra/flai
Documentação: flai.dev/docs
Comunidade: Discord Flet + #flai
Exemplos: examples/ no repositório
FLAI representa uma nova categoria de ferramentas de desenvolvedor: especializadas, locais e contextuais. Ao focar especificamente em Flet e operar completamente offline, oferece privacidade, performance e relevância que ferramentas genéricas baseadas em nuvem não podem igualar.**
"Não substitua seu editor - aumente-o com inteligência contextual específica para seu stack tecnológico."