"""
RAG Retriever - Busca semântica no código
"""
from pathlib import Path
from typing import List, Dict, Any, Optional

class Retriever:
    """Recuperador de contexto semântico"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.index_path = project_path / ".flai" / "vectordb"
        self._vectorstore = None
    
    def _init_vectorstore(self):
        """Inicializa vector store (LangChain)"""
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_ollama import OllamaEmbeddings
            
            if self.index_path.exists():
                self._vectorstore = Chroma(
                    persist_directory=str(self.index_path),
                    embedding_function=OllamaEmbeddings(model="nomic-embed-text")
                )
            return self._vectorstore is not None
        except ImportError:
            return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca documentos similares
        
        Args:
            query: Texto da busca
            k: Número de resultados
        
        Returns:
            Lista de documentos com conteúdo e metadados
        """
        if not self._init_vectorstore():
            return []
        
        try:
            results = self._vectorstore.similarity_search(query, k=k)
            return [
                {
                    "content": doc.page_content[:500],
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in results
            ]
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []
    
    def search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Busca com scores de similaridade"""
        if not self._init_vectorstore():
            return []
        
        try:
            return self._vectorstore.similarity_search_with_score(query, k=k)
        except Exception:
            return []
    
    def get_context_for_prompt(self, query: str, max_tokens: int = 2000) -> str:
        """Gera contexto formatado para prompt"""
        results = self.search(query, k=3)
        if not results:
            return ""
        
        context = "## Contexto relevante do código:\n\n"
        for i, result in enumerate(results, 1):
            context += f"### {i}. {result['source']}\n"
            context += f"```python\n{result['content']}\n```\n\n"
        
        return context[:max_tokens]
