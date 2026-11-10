"""
Gerenciador Dinâmico de Agentes para FLAI
Permite registrar, configurar e executar agentes dinamicamente
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
import yaml
import importlib
import sys
import json
from datetime import datetime
import traceback

import asyncio
import importlib.util
from flai.core.async_utils import run_async
from flai.core.security import (
    safe_name,
    safe_join,
    validate_module_path,
    UnsafePathError,
    UnsafeModuleError,
)
from flai.core.security.modules import custom_agents_allowed

class AgentPriority(Enum):
    """Prioridade do agente na pipeline"""
    CRITICAL = 0  # Executa primeiro, não pode falhar
    HIGH = 1      # Executa antes da maioria
    NORMAL = 2    # Execução padrão
    LOW = 3       # Executa depois
    LOWEST = 4    # Executa por último (fallback)

class AgentType(Enum):
    """Tipo de agente"""
    BUILTIN = "builtin"      # Nativo do FLAI
    CUSTOM = "custom"        # Criado pelo usuário
    EXTERNAL = "external"    # Carregado de pacote externo
    
@dataclass
class AgentDefinition:
    """Definição completa de um agente"""
    name: str
    description: str
    type: AgentType
    module_path: str         # Caminho do módulo (ex: flai.core.agents.crud_agent)
    class_name: str          # Nome da classe (ex: CRUDAgent)
    priority: AgentPriority = AgentPriority.NORMAL
    enabled: bool = True
    auto_load: bool = True    # Carregar automaticamente na inicialização
    dependencies: List[str] = field(default_factory=list)  # Agentes que precisa antes
    triggers: List[str] = field(default_factory=list)      # Intenções que este agente trata
    config: Dict[str, Any] = field(default_factory=dict)   # Configuração específica
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "module_path": self.module_path,
            "class_name": self.class_name,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "auto_load": self.auto_load,
            "dependencies": self.dependencies,
            "triggers": self.triggers,
            "config": self.config,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentDefinition':
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            type=AgentType(data.get("type", "builtin")),
            module_path=data["module_path"],
            class_name=data["class_name"],
            priority=AgentPriority(data.get("priority", 2)),
            enabled=data.get("enabled", True),
            auto_load=data.get("auto_load", True),
            dependencies=data.get("dependencies", []),
            triggers=data.get("triggers", []),
            config=data.get("config", {}),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

class BaseAgent:
    """Classe base para todos os agentes"""
    
    def __init__(self, project_path: Path, config: Dict = None):
        self.project_path = project_path
        self.config = config or {}
        self.name = self.__class__.__name__
    
    def can_handle(self, intent: str, context: Dict = None) -> bool:
        """Verifica se este agente pode lidar com a intenção"""
        return False
    
    async def execute(self, intent: str, entity: str = None, 
                      fields: List[str] = None, context: Dict = None) -> Dict:
        """Executa o agente com os parâmetros fornecidos"""
        raise NotImplementedError
    
    def get_capabilities(self) -> List[str]:
        """Retorna lista de capacidades/intenções que este agente suporta"""
        return []
    
    def get_priority(self) -> AgentPriority:
        """Retorna prioridade deste agente"""
        return AgentPriority.NORMAL

class AgentManager:
    """Gerencia todos os agentes do FLAI"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.agents_dir = self.project_path / ".flai" / "agents"
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_model = self._load_project_config()
        self.config_file = self.agents_dir / "config.yaml"
        self.agents: Dict[str, AgentDefinition] = {}
        self.loaded_agents: Dict[str, BaseAgent] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        
        # Cache de handlers
        self._intent_to_agent: Dict[str, str] = {}
        
        self._load_agents()
        self._ensure_default_agents()
    
    def _load_agents(self):
        """Carrega definições dos agentes"""
        # Carrega agentes builtin
        builtin_dir = self.agents_dir / "builtin"
        if builtin_dir.exists():
            for agent_file in builtin_dir.glob("*.yaml"):
                self._load_agent_from_file(agent_file)
        
        # Carrega agentes customizados
        custom_dir = self.agents_dir / "custom"
        if custom_dir.exists():
            for agent_file in custom_dir.glob("*.yaml"):
                self._load_agent_from_file(agent_file)
            for agent_dir in custom_dir.iterdir():
                if agent_dir.is_dir():
                    config_file = agent_dir / "config.yaml"
                    if config_file.exists():
                        self._load_agent_from_file(config_file)
        
        # Carrega configuração principal
        if self.config_file.exists():
            try:
                config = yaml.safe_load(self.config_file.read_text(encoding='utf-8'))
                for name, agent_data in config.get("agents", {}).items():
                    if name not in self.agents:
                        self.agents[name] = AgentDefinition.from_dict(agent_data)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
        
        self._build_intent_cache()

    def _load_project_config(self) -> Dict:
        """
        Carrega configuração do projeto Flai.
        """

        config_file = (self.project_path / ".flai" / "config.json")

        if not config_file.exists():
            return {}

        try:

            with open(config_file, "r", encoding="utf-8") as f:

                return json.load(f)

        except Exception:

            return {}

    def _load_agent_from_file(self, file_path: Path):
        """Carrega definição de agente de um arquivo"""
        try:
            data = yaml.safe_load(file_path.read_text(encoding='utf-8'))
            agent = AgentDefinition.from_dict(data)
            self.agents[agent.name] = agent
        except Exception as e:
            print(f"Erro ao carregar {file_path}: {e}")
    
    def _save_agent(self, agent: AgentDefinition):
        """Salva definição de agente em arquivo"""
        if agent.type == AgentType.BUILTIN:
            agent_dir = self.agents_dir / "builtin"
        else:
            agent_dir = self.agents_dir / "custom"
        
        agent_dir.mkdir(exist_ok=True)
        agent_file = safe_join(agent_dir, f"{safe_name(agent.name)}.yaml")
        agent_file.write_text(yaml.dump(agent.to_dict()), encoding='utf-8')
        
        self.agents[agent.name] = agent
        self._build_intent_cache()
    
    def _delete_agent_file(self, agent_name: str):
        """Remove arquivo de agente"""
        agent_file = safe_join(self.agents_dir, "custom", f"{safe_name(agent_name)}.yaml")
        if agent_file.exists():
            agent_file.unlink()
    
    def _ensure_default_agents(self):
        """Cria agentes padrão se não existirem"""
        defaults = [
            AgentDefinition(
                name="crud_agent",
                description="Cria CRUDs completos para entidades",
                type=AgentType.BUILTIN,
                module_path="flai.core.agents.crud_agent",
                class_name="CRUDAgent",
                priority=AgentPriority.NORMAL,
                triggers=["create_crud"],
                config={
                    "auto_migrate": True,
                    "create_tests": False
                }
            ),
            AgentDefinition(
                name="form_agent",
                description="Cria formulários Flet",
                type=AgentType.BUILTIN,
                module_path="flai.core.agents.form_agent",
                class_name="FormAgent",
                priority=AgentPriority.NORMAL,
                triggers=["create_form"]
            ),
            AgentDefinition(
                name="project_agent",
                description="Analisa estrutura do projeto",
                type=AgentType.BUILTIN,
                module_path="flai.core.agents.project_agent",
                class_name="ProjectAgent",
                priority=AgentPriority.NORMAL,
                triggers=["analyze", "where", "search"]
            ),
            AgentDefinition(
                name="db_agent",
                description="Gerencia banco de dados e migrations",
                type=AgentType.BUILTIN,
                module_path="flai.core.agents.db_agent",
                class_name="DBAgent",
                priority=AgentPriority.NORMAL,
                triggers=["create_model", "migrate"]
            ),
            AgentDefinition(
                name="rag_agent",
                description="Busca semântica no código",
                type=AgentType.BUILTIN,
                module_path="flai.core.agents.rag_agent",
                class_name="RAGAgent",
                priority=AgentPriority.LOW,
                triggers=["search_semantic", "where"],
                config={
                    "auto_index": True,
                    "max_results": 5
                }
            ),
            AgentDefinition(
                name="llm_fallback_agent",
                description="Responde usando LLM quando nenhum agente específico atende",
                type=AgentType.BUILTIN,
                module_path="flai.core.agents.llm_agent",
                class_name="LLMAgent",
                priority=AgentPriority.LOWEST,
                triggers=["*"],  # Coringa: responde a qualquer intent não tratada
                config=self.config_model
                # config={
                #     "model": "flai-coder",
                #     "temperature": 0.7
                # }
            )
        ]
        
        for default in defaults:
            if default.name not in self.agents:
                self.add_agent(default)
    
    def _build_intent_cache(self):
        """Constrói cache de intent -> agente"""
        self._intent_to_agent = {}
        
        for agent in self.agents.values():
            if not agent.enabled:
                continue
            
            for trigger in agent.triggers:
                if trigger == "*":
                    continue  # Coringa tratado separadamente
                if trigger not in self._intent_to_agent:
                    self._intent_to_agent[trigger] = []
                self._intent_to_agent[trigger].append(agent.name)
    
    def add_agent(self, agent_def: AgentDefinition) -> bool:
        """Adiciona um novo agente"""
        if agent_def.name in self.agents:
            return False
        
        agent_def.created_at = datetime.now().isoformat()
        agent_def.updated_at = datetime.now().isoformat()
        
        self._save_agent(agent_def)
        return True
    
    def update_agent(self, agent_name: str, **kwargs) -> bool:
        """Atualiza um agente existente"""
        if agent_name not in self.agents:
            return False
        
        agent = self.agents[agent_name]
        
        for key, value in kwargs.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        agent.updated_at = datetime.now().isoformat()
        
        self._save_agent(agent)
        self._build_intent_cache()
        return True
    
    def delete_agent(self, agent_name: str) -> bool:
        """Remove um agente"""
        if agent_name not in self.agents:
            return False
        
        # Não permite deletar agentes builtin
        if self.agents[agent_name].type == AgentType.BUILTIN:
            return False
        
        del self.agents[agent_name]
        self._delete_agent_file(agent_name)
        self._build_intent_cache()
        return True
    
    def enable_agent(self, agent_name: str, enabled: bool = True) -> bool:
        """Habilita ou desabilita um agente"""
        return self.update_agent(agent_name, enabled=enabled)
    
    def get_agent(self, agent_name: str) -> Optional[AgentDefinition]:
        """Retorna definição de um agente"""
        return self.agents.get(agent_name)
    
    def list_agents(self, enabled_only: bool = True) -> List[AgentDefinition]:
        """Lista todos os agentes"""
        agents = self.agents.values()
        if enabled_only:
            agents = [a for a in agents if a.enabled]
        return sorted(agents, key=lambda x: x.priority.value)
    
    def load_agent_instance(self, agent_name: str) -> Optional[BaseAgent]:
        """Carrega a instância de um agente (cache)"""
        if agent_name in self.agent_instances:
            return self.agent_instances[agent_name]
        
        agent_def = self.agents.get(agent_name)
        if not agent_def or not agent_def.enabled:
            return None
        
        try:
            if agent_def.type == AgentType.CUSTOM:
                # SEC-01: código Python do projeto só roda com opt-in explícito
                if not custom_agents_allowed():
                    print(
                        f"Agente customizado '{agent_name}' ignorado: "
                        "defina FLAI_ALLOW_CUSTOM_AGENTS=1 para permitir."
                    )
                    return None
                module = self._load_custom_module(agent_name)
            else:
                module = importlib.import_module(validate_module_path(agent_def.module_path))
            agent_class = getattr(module, agent_def.class_name)
            
            # Instancia o agente
            agent_instance = agent_class(self.project_path, agent_def.config)
            self.agent_instances[agent_name] = agent_instance
            self.loaded_agents[agent_name] = agent_instance
            
            return agent_instance
        except Exception as e:
            print(f"Erro ao carregar agente {agent_name}: {e}")
            traceback.print_exc()
            return None
    
    def _load_custom_module(self, agent_name: str):
        """Carrega .flai/agents/custom/<nome>/agent.py pelo caminho do arquivo."""
        name = safe_name(agent_name)
        agent_file = safe_join(self.agents_dir, "custom", name, "agent.py")
        if not agent_file.exists():
            raise FileNotFoundError(f"Arquivo do agente não encontrado: {agent_file}")
        spec = importlib.util.spec_from_file_location(f"flai_custom_agent_{name}", agent_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def get_agent_for_intent(self, intent: str) -> List[BaseAgent]:
        """Retorna lista de agentes que podem lidar com a intenção"""
        agents = []
        
        # Busca agentes específicos para esta intenção
        agent_names = self._intent_to_agent.get(intent, [])
        
        # Ordena por prioridade
        agent_names.sort(key=lambda x: self.agents[x].priority.value if x in self.agents else 999)
        
        for agent_name in agent_names:
            agent = self.load_agent_instance(agent_name)
            if agent:
                agents.append(agent)
        
        # Adiciona agentes curinga (triggers = ["*"]) como fallback
        for agent_def in self.agents.values():
            if agent_def.enabled and "*" in agent_def.triggers:
                agent = self.load_agent_instance(agent_def.name)
                if agent and agent not in agents:
                    agents.append(agent)
        
        return agents
    def execute_pipeline_sync(self, intent: str, entity: str = None,
                              fields: List[str] = None,
                              context: Dict = None) -> Dict:
        """
        Versão síncrona do execute_pipeline
        
        Args:
            intent: Intenção detectada
            entity: Entidade extraída
            fields: Campos extraídos
            context: Contexto adicional
        
        Returns:
            Resultado da pipeline
        """
        return run_async(
            self.execute_pipeline(intent, entity, fields, context),
            timeout=60
        )
    
    async def execute_pipeline(self, intent: str, entity: str = None,
                                fields: List[str] = None,
                                context: Dict = None) -> Dict:
        """
        Versão assíncrona - mantida para compatibilidade
        """
        agents = self.get_agent_for_intent(intent)
        
        if not agents:
            return {
                "success": False,
                "error": f"Nenhum agente disponível para intent '{intent}'",
                "type": "error"
            }
        
        for agent in agents:
            if agent.can_handle(intent, context):
                try:
                    result = await agent.execute(intent, entity, fields, context)
                    if result and result.get("success", True):
                        return result
                except Exception as e:
                    print(f"Erro no agente {agent.name}: {e}")
                    continue
        
        return {
            "success": False,
            "error": f"Nenhum agente conseguiu processar a intent '{intent}'",
            "type": "error"
        }
    
    def register_custom_agent(self, agent_code: str, agent_name: str) -> bool:
        """
        Registra um agente customizado a partir de código Python
        
        Args:
            agent_code: Código fonte do agente
            agent_name: Nome do agente
        """
        agent_name = safe_name(agent_name)
        custom_dir = safe_join(self.agents_dir, "custom", agent_name)
        custom_dir.mkdir(parents=True, exist_ok=True)
        
        # Salva o código do agente
        agent_file = custom_dir / "agent.py"
        agent_file.write_text(agent_code, encoding='utf-8')
        
        # Cria configuração
        config = {
            "name": agent_name,
            "description": f"Custom agent: {agent_name}",
            "type": "custom",
            # Carregado por arquivo em _load_custom_module (não via import_module)
            "module_path": f"custom.{agent_name}.agent",
            "class_name": f"{agent_name.capitalize()}Agent",
            "priority": 2,
            "enabled": True,
            "auto_load": True,
            "dependencies": [],
            "triggers": [],
            "config": {}
        }
        
        config_file = custom_dir / "config.yaml"
        config_file.write_text(yaml.dump(config), encoding='utf-8')
        
        # Carrega o agente
        self._load_agent_from_file(config_file)
        
        return agent_name in self.agents
    
    def get_agent_stats(self) -> Dict:
        """Retorna estatísticas dos agentes"""
        stats = {
            "total_agents": len(self.agents),
            "enabled_agents": len([a for a in self.agents.values() if a.enabled]),
            "builtin_agents": len([a for a in self.agents.values() if a.type == AgentType.BUILTIN]),
            "custom_agents": len([a for a in self.agents.values() if a.type == AgentType.CUSTOM]),
            "loaded_agents": len(self.loaded_agents),
            "intents_covered": len(self._intent_to_agent),
            "by_priority": {}
        }
        
        for priority in AgentPriority:
            count = len([a for a in self.agents.values() if a.priority == priority])
            stats["by_priority"][priority.name] = count
        
        return stats