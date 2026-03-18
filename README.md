# FLAI - Framework Local de AI 

> Sua Inteligência Artificial Privada para Desenvolvimento de Software

## 🌟 Introdução
FLAI (Framework Local de AI) é uma solução revolucionária que traz o poder da inteligência artificial diretamente para sua máquina local, eliminando a dependência de APIs externas e garantindo privacidade total. Desenvolvido especificamente para projetos Fleting (Python + Flet), o FLAI transforma a maneira como você desenvolve, analisa e refatora código.

### Por que FLAI?

- 🔒 100% Privado: Seus códigos nunca saem da sua máquina
- ⚡ Sem Latência: Execução local elimina delays de rede
- 💰 Zero Custos: Nenhuma assinatura ou créditos necessários
- 🔄 Offline: Funciona mesmo sem internet

## 🏗️ Arquitetura Técnica
Visão Geral do Sistema

```
┌─────────────────────────────────────────────┐
│           FLAI Architecture                 │
├─────────────────────────────────────────────┤
│  ┌────────────┐    ┌────────────┐           │
│  │   User     │◄──►│   FLAI     │           │
│  │  Interface │    │   Shell    │           │
│  └────────────┘    └────────────┘           │
│         │                   │               │
│         ▼                   ▼               │
│  ┌────────────┐    ┌────────────┐           │
│  │  Fleting   │    │  Ollama    │           │
│  │  Project   │    │  Manager   │           │
│  └────────────┘    └────────────┘           │
│         │                   │               │
│         └───────────────────┼───────────────┘
│                             ▼               │
│                      ┌────────────┐         │
│                      │   Local    │         │
│                      │   LLM      │         │
│                      │  (     )   │         │
│                      └────────────┘         │
└─────────────────────────────────────────────┘
```

### Componentes Principais
1. Ollama Manager
```py
class OllamaManager:
    """
    Gerenciador inteligente que detecta e executa Ollama automaticamente
    Funciona sem necessidade de configurar PATH do sistema
    """
    - find_ollama(): Busca em múltiplos locais do sistema
    - start_server(): Inicia servidor em background
    - run_model(): Executa modelos via API local
    - ensure_ready(): Prepara tudo automaticamente
```



