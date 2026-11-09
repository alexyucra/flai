"""
RAG Indexer - Indexa código do projeto para busca semântica
LangChain opcional - requer `pip install langchain chromadb`
"""
from pathlib import Path
from typing import List, Optional

class Indexer:
    """Indexador de código para RAG"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.index_path = project_path / ".flai" / "vectordb"
        self._initialized = False
    
    def _init_langchain(self):
        """Inicializa LangChain (opcional)"""
        try:
            from langchain_community.document_loaders import DirectoryLoader
            from langchain_community.vectorstores import Chroma
            from langchain_ollama import OllamaEmbeddings
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            self.loader_cls = DirectoryLoader
            self.vectorstore_cls = Chroma
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            self._initialized = True
            return True
        except ImportError:
            print("⚠️ LangChain não instalado. Execute: pip install langchain langchain-community chromadb")
            return False
    
    def index_project(self) -> bool:
        """Indexa todo o projeto"""
        if not self._init_langchain():
            return False
        
        try:
            # Carrega arquivos Python
            loader = self.loader_cls(str(self.project_path), glob="**/*.py")
            documents = loader.load()
            
            # Divide em chunks
            chunks = self.splitter.split_documents(documents)
            
            # Cria vector store
            self.index_path.mkdir(parents=True, exist_ok=True)
            vectorstore = self.vectorstore_cls.from_documents(
                chunks,
                self.embeddings,
                persist_directory=str(self.index_path)
            )
            vectorstore.persist()
            
            print(f"✅ Indexados {len(documents)} arquivos, {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"Erro ao indexar: {e}")
            return False
    
    def add_file(self, file_path: Path) -> bool:
        """Adiciona arquivo ao índice"""
        # TODO: Implementar atualização incremental
        return self.index_project()
    
    def clear(self) -> bool:
        """Limpa índice"""
        import shutil
        if self.index_path.exists():
            shutil.rmtree(self.index_path)
            self.index_path.mkdir(parents=True)
        return True
