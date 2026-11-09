# flai/core/agents/agent_pipeline.py
"""
Pipeline de processamento de agentes
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio

@dataclass
class PipelineStep:
    """Passo do pipeline de processamento"""
    agent_name: str
    timeout: int = 30
    required: bool = False  # Se falhar, interrompe pipeline?

class AgentPipeline:
    """Gerencia pipelines de processamento"""
    
    def __init__(self, agent_manager, pipeline_name: str = "default"):
        self.agent_manager = agent_manager
        self.pipeline_name = pipeline_name
        self.steps: List[PipelineStep] = []
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Carrega pipeline da configuração"""
        # Pipeline padrão baseado em prioridade
        agents = self.agent_manager.list_agents(enabled_only=True)
        
        # Ordena por prioridade
        for agent in agents:
            self.steps.append(PipelineStep(
                agent_name=agent.name,
                timeout=30,
                required=False
            ))
    
    async def execute(self, intent: str, entity: str = None,
                      fields: List[str] = None,
                      context: Dict = None) -> Dict:
        """Executa pipeline"""
        
        for step in self.steps:
            agent_def = self.agent_manager.get_agent(step.agent_name)
            if not agent_def or not agent_def.enabled:
                continue
            
            # Verifica se agente pode lidar com esta intenção
            if intent not in agent_def.triggers and "*" not in agent_def.triggers:
                continue
            
            # Carrega e executa agente
            agent = self.agent_manager.load_agent_instance(step.agent_name)
            if not agent:
                continue
            
            try:
                # Executa com timeout
                result = await asyncio.wait_for(
                    agent.execute(intent, entity, fields, context),
                    timeout=step.timeout
                )
                
                if result and result.get("success", False):
                    return result
                    
            except asyncio.TimeoutError:
                print(f"Timeout no agente {step.agent_name}")
                if step.required:
                    return {
                        "success": False,
                        "error": f"Timeout no agente {step.agent_name}",
                        "type": "pipeline_error"
                    }
            except Exception as e:
                print(f"Erro no agente {step.agent_name}: {e}")
                if step.required:
                    return {
                        "success": False,
                        "error": str(e),
                        "type": "pipeline_error"
                    }
        
        return {
            "success": False,
            "error": f"Nenhum agente conseguiu processar a intent '{intent}'",
            "type": "pipeline_error"
        }