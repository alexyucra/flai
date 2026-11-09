# flai/core/__init__.py
"""Módulo core do FLAI - Agents, Intent, Generators, Executors"""

from pathlib import Path
from typing import Optional

from flai.core.registry import register_component, get_component, ComponentRegistry
from flai.core.agents.agent_manager import AgentManager
from flai.core.rag.integrated_rag import IntegratedRAG
from flai.core.context.context_manager import ContextManager
from flai.core.intent.intent_manager import IntentManager
from flai.cli.utils.ollama_manager import get_ollama_manager

from flai.core.agents import RouterAgent, CRUDAgent, ProjectAgent, FormAgent, DBAgent
from flai.core.intent import IntentParser, IntentPatterns, IntentClassifier
# from flai.core.generators import CRUDGenerator, FormGenerator, ViewGenerator, ModelGenerator, ControllerGenerator
from flai.core.executors import FletingExecutor, ShellExecutor

# ============================================================
# REGISTRO DE FÁBRICAS DE COMPONENTES
# ============================================================

def _create_agent_manager(project_path: Path, **kwargs) -> AgentManager:
    """Fábrica para AgentManager"""
    return AgentManager(project_path)

def _create_rag(project_path: Path, **kwargs) -> IntegratedRAG:
    """Fábrica para IntegratedRAG"""
    auto_index = kwargs.get('auto_index', True)
    return IntegratedRAG(project_path, auto_index=auto_index)

def _create_context_manager(project_path: Path, **kwargs) -> ContextManager:
    """Fábrica para ContextManager"""
    return ContextManager(project_path)

def _create_intent_manager(project_path: Path, **kwargs) -> IntentManager:
    """Fábrica para IntentManager"""
    return IntentManager(project_path)

def _create_ollama(**kwargs) -> any:
    """Fábrica para OllamaManager"""
    return get_ollama_manager()

# Registrar componentes
register_component('agent_manager', _create_agent_manager)
register_component('rag', _create_rag)
register_component('context_manager', _create_context_manager)
register_component('intent_manager', _create_intent_manager)
register_component('ollama', _create_ollama)


# ============================================================
# FUNÇÕES DE ACESSO DIRETO (SIMPLIFICADAS)
# ============================================================

def get_rag(project_path: Path, auto_index: bool = True) -> IntegratedRAG:
    """Obtém instância única do RAG para o projeto"""
    return get_component('rag', project_path, auto_index=auto_index)

def get_agent_manager(project_path: Path) -> AgentManager:
    """Obtém instância única do AgentManager para o projeto"""
    return get_component('agent_manager', project_path)

def get_context_manager(project_path: Path) -> ContextManager:
    """Obtém instância única do ContextManager para o projeto"""
    return get_component('context_manager', project_path)

def get_intent_manager(project_path: Path) -> IntentManager:
    """Obtém instância única do IntentManager para o projeto"""
    return get_component('intent_manager', project_path)

def get_ollama():
    """Obtém instância única do OllamaManager"""
    return get_component('ollama')


# ============================================================
# EXPORTAÇÕES
# ============================================================

__all__ = [
    # Agents
    "RouterAgent",
    "CRUDAgent", 
    "ProjectAgent",
    "FormAgent",
    "DBAgent",
    # Intent
    "IntentParser",
    "IntentPatterns",
    "IntentClassifier",
    # Generators
    # "CRUDGenerator",
    # "FormGenerator",
    # "ViewGenerator",
    # "ModelGenerator",
    # "ControllerGenerator",
    # Executors
    "FletingExecutor",
    "ShellExecutor",
    # Registry
    'ComponentRegistry',
    'get_component',
    'register_component',
    'has_component',
    # Funções de acesso
    'get_rag',
    'get_agent_manager',      # ← JÁ ESTAVA
    'get_context_manager',    # ← JÁ ESTAVA
    'get_intent_manager',     # ← JÁ ESTAVA
    'get_ollama',             # ← JÁ ESTAVA
    # Classes originais
    'IntegratedRAG',
    'AgentManager',
    'ContextManager', 
    'IntentManager',
]
