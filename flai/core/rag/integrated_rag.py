
# flai/core/rag/integrated_rag.py
"""
Integração do RAG com o fluxo principal do FLAI
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from .rag_manager import RAGManager

class IntegratedRAG:
    """Interface integrada do RAG para uso pelos Agents"""
    
    def __init__(self, project_path: Path, auto_index: bool = True):
        self.project_path = project_path
        self.rag = RAGManager(project_path)
        self._is_indexed = False
        
        if auto_index and self.rag.is_available():
            self._ensure_indexed()
    
    def _ensure_indexed(self) -> bool:
        """Garante que o projeto está indexado"""
        if self._is_indexed:
            return True
        
        stats = self.rag.get_index_stats()
        
        if not stats["exists"]:
            print("📚 Indexando projeto para busca semântica...")
            if self.rag.index_project(verbose=False):
                self._is_indexed = True
                return True
            return False
        
        self._is_indexed = True
        return True
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Busca contexto relevante para a consulta"""
        if not self._ensure_indexed():
            return []
        
        return self.rag.search(query, k=k)
    
    def enhance_query(self, user_query: str) -> str:
        """
        Enriquece a consulta do usuário com contexto RAG
        
        Args:
            user_query: Consulta original do usuário
            
        Returns:
            Consulta enriquecida com contexto
        """
        context = self.rag.get_context_for_prompt(user_query, max_tokens=1000)
        
        if not context:
            return user_query
        
        enhanced = f"""
{context}

## 💬 Pergunta do Usuário
{user_query}

**Instrução:** Use o contexto acima para responder com precisão. Se o contexto não contiver a informação necessária, responda baseado no seu conhecimento geral.
"""
        return enhanced
    
    def add_file(self, file_path: Path) -> bool:
        """Adiciona arquivo ao índice (após criação/modificação)"""
        if not self._is_indexed:
            return False
        return self.rag.add_file(file_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do RAG"""
        return self.rag.get_index_stats()