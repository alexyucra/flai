# flai/core/agents/llm_agent.py
"""
Agente LLM - Responde usando o modelo de linguagem diretamente
"""
from pathlib import Path
from typing import Dict, List, Optional, Any

from flai.core.agents.agent_manager import BaseAgent, AgentPriority
from flai.cli.utils.ollama_manager import get_ollama_manager

class LLMAgent(BaseAgent):
    """Agente fallback que usa LLM diretamente"""
    
    def __init__(self, project_path: Path, config: Dict = None):
        super().__init__(project_path, config)
        self.ollama = get_ollama_manager()
        self.model = config.get("model", "flai-coder")
        self.temperature = config.get("temperature", 0.7)
    
    def can_handle(self, intent: str, context: Dict = None) -> bool:
        """Este agente é o fallback, tenta lidar com qualquer coisa"""
        return True  # Último recurso
    
    async def execute(self, intent: str, entity: str = None,
                      fields: List[str] = None, context: Dict = None) -> Dict:
        """Responde usando LLM"""
        
        # Constrói o prompt
        user_query = context.get("user_query", "") if context else ""
        
        if not user_query:
            user_query = f"Intenção: {intent}, Entidade: {entity}, Campos: {fields}"
        
        # Chamada ao LLM
        response = self.ollama.quick_run(self.model, user_query)
        
        return {
            "success": True,
            "type": "llm_response",
            "content": response
        }
    
    def get_priority(self) -> AgentPriority:
        return AgentPriority.LOWEST  # Prioridade mais baixa (fallback)