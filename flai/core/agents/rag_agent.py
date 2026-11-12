# flai/core/agents/rag_agent.py
"""
Agente RAG para busca semântica no código
"""
from pathlib import Path
from typing import Dict, List

from flai.core.agents.agent_manager import BaseAgent, AgentPriority
from flai.core.rag.integrated_rag import IntegratedRAG

class RAGAgent(BaseAgent):
    """Agente especializado em busca semântica"""
    
    def __init__(self, project_path: Path, config: Dict = None):
        super().__init__(project_path, config)
        self.rag = IntegratedRAG(project_path, auto_index=False)
    
    def can_handle(self, intent: str, context: Dict = None) -> bool:
        """Verifica se pode lidar com a intenção"""
        # Busca semântica é útil para perguntas que começam com "onde", "como", "o que é"
        search_intents = ["where", "search_semantic", "analyze"]
        if intent in search_intents:
            return True
        
        # Também tenta se o usuário está perguntando sobre o código
        if context and context.get("user_query"):
            query = context["user_query"].lower()
            if any(word in query for word in ["onde", "cadê", "buscar", "encontrar"]):
                return True
        
        return False
    
    async def execute(self, intent: str, entity: str = None,
                      fields: List[str] = None, context: Dict = None) -> Dict:
        """Executa busca semântica"""
        
        # Determina a query de busca
        query = entity or (context.get("user_query") if context else "")
        
        if not query:
            return {
                "success": False,
                "error": "Nada para buscar",
                "type": "search_error"
            }
        
        # Realiza a busca
        results = self.rag.search(query, k=self.config.get("max_results", 5))
        
        if not results:
            return {
                "success": False,
                "message": f"Nenhum resultado encontrado para '{query}'",
                "type": "search_empty",
                "results": []
            }
        
        # Formata os resultados
        formatted_results = []
        for result in results:
            formatted_results.append({
                "source": result.get("source", "unknown"),
                "content": result.get("content", "")[:300],
                "score": result.get("score", 0)
            })
        
        return {
            "success": True,
            "type": "search_results",
            "content": {
                "query": query,
                "total": len(results),
                "results": formatted_results
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """Retorna capacidades do agente"""
        return ["where", "search_semantic", "analyze"]
    
    def get_priority(self) -> AgentPriority:
        return AgentPriority.LOW  # Prioridade baixa, apenas se outros falharem