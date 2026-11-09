"""
RAG Embeddings - Wrapper para embeddings
"""
from typing import List, Optional

class Embeddings:
    """Wrapper para embeddings com fallback"""
    
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self._embeddings = None
        self._available = None
    
    def _init_embeddings(self):
        """Inicializa embeddings com LangChain"""
        if self._available is not None:
            return self._available
        
        try:
            from langchain_ollama import OllamaEmbeddings
            self._embeddings = OllamaEmbeddings(model=self.model)
            self._available = True
        except ImportError:
            self._available = False
        
        return self._available
    
    def embed_query(self, text: str) -> Optional[List[float]]:
        """Gera embedding para consulta"""
        if not self._init_embeddings():
            return None
        
        try:
            return self._embeddings.embed_query(text)
        except Exception:
            return None
    
    def embed_documents(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Gera embeddings para documentos"""
        if not self._init_embeddings():
            return None
        
        try:
            return self._embeddings.embed_documents(texts)
        except Exception:
            return None
    
    def is_available(self) -> bool:
        """Verifica se embeddings estão disponíveis"""
        self._init_embeddings()
        return self._available
