# flai/core/rag/rag_manager.py
"""
RAG Manager - Gerencia toda a operação de RAG (Indexação + Busca)
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

class RAGManager:
    """Gerencia RAG com LangChain e ChromaDB"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.index_path = project_path / ".flai" / "vectordb"
        self._vectorstore = None
        self._embeddings = None
        self._is_available = None
        
    def is_available(self) -> bool:
        """Verifica se LangChain está disponível"""
        if self._is_available is not None:
            return self._is_available
            
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_ollama import OllamaEmbeddings
            self._is_available = True
            return True
        except ImportError:
            self._is_available = False
            return False
    
    def _init_embeddings(self):
        """Inicializa embeddings"""
        if not self.is_available():
            return None
            
        try:
            from langchain_ollama import OllamaEmbeddings
            if self._embeddings is None:
                self._embeddings = OllamaEmbeddings(
                    model="nomic-embed-text",
                    base_url="http://localhost:11434"
                )
            return self._embeddings
        except Exception as e:
            print(f"⚠️ Erro ao inicializar embeddings: {e}")
            return None
    
    def _init_vectorstore(self):
        """Inicializa vector store"""
        if not self.is_available():
            return None
            
        try:
            from langchain_community.vectorstores import Chroma
            
            if self._vectorstore is None and self.index_path.exists():
                embeddings = self._init_embeddings()
                if embeddings:
                    self._vectorstore = Chroma(
                        persist_directory=str(self.index_path),
                        embedding_function=embeddings
                    )
            return self._vectorstore
        except Exception as e:
            print(f"⚠️ Erro ao inicializar vectorstore: {e}")
            return None
    
    def index_project(self, verbose: bool = True) -> bool:
        """
        Indexa todo o projeto para busca semântica
        
        Args:
            verbose: Mostrar progresso
            
        Returns:
            True se indexado com sucesso
        """
        if not self.is_available():
            if verbose:
                print("⚠️ LangChain não instalado. Execute: pip install langchain langchain-community chromadb")
            return False
        
        try:
            from langchain_community.document_loaders import DirectoryLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_community.vectorstores import Chroma
            
            if verbose:
                print("📚 Carregando documentos do projeto...")
            
            # Carrega arquivos Python e Markdown
            loader = DirectoryLoader(
                str(self.project_path),
                glob="**/*.{py,md}",
                recursive=True,
                silent_errors=True
            )
            documents = loader.load()
            
            if verbose:
                print(f"✅ Carregados {len(documents)} documentos")
                print("✂️  Dividindo em chunks...")
            
            # Divide em chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            
            if verbose:
                print(f"✅ Criados {len(chunks)} chunks")
                print("🔢 Gerando embeddings e indexando...")
            
            # Cria vector store
            self.index_path.mkdir(parents=True, exist_ok=True)
            embeddings = self._init_embeddings()
            
            if not embeddings:
                if verbose:
                    print("❌ Falha ao inicializar embeddings")
                return False
            
            self._vectorstore = Chroma.from_documents(
                chunks,
                embeddings,
                persist_directory=str(self.index_path)
            )
            self._vectorstore.persist()
            
            if verbose:
                print(f"✅ Indexação concluída! Índice salvo em: {self.index_path}")
            
            # Salva metadados
            metadata = {
                "indexed_at": datetime.now().isoformat(),
                "total_documents": len(documents),
                "total_chunks": len(chunks),
                "project_path": str(self.project_path)
            }
            
            with open(self.index_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            if verbose:
                print(f"❌ Erro ao indexar: {e}")
            return False
    
    def search(self, query: str, k: int = 5, verbose: bool = False) -> List[Dict[str, Any]]:
        """
        Busca documentos similares
        
        Args:
            query: Texto da busca
            k: Número de resultados
            verbose: Mostrar logs
            
        Returns:
            Lista de resultados com conteúdo e metadados
        """
        vectorstore = self._init_vectorstore()
        
        if not vectorstore:
            if verbose:
                print("⚠️ Vectorstore não disponível")
            return []
        
        try:
            if verbose:
                print(f"🔍 Buscando: '{query}'")
            
            results = vectorstore.similarity_search_with_score(query, k=k)
            
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "source": doc.metadata.get("source", "unknown")
                })
            
            if verbose:
                print(f"✅ Encontrados {len(formatted_results)} resultados")
            
            return formatted_results
            
        except Exception as e:
            if verbose:
                print(f"❌ Erro na busca: {e}")
            return []
    
    def get_context_for_prompt(self, query: str, max_tokens: int = 1500, k: int = 3) -> str:
        """
        Gera contexto formatado para prompt da IA
        
        Args:
            query: Consulta do usuário
            max_tokens: Máximo de tokens no contexto
            k: Número de resultados
            
        Returns:
            String formatada com contexto relevante
        """
        results = self.search(query, k=k)
        
        if not results:
            return ""
        
        context_parts = ["## 📚 Contexto Relevante do Código\n"]
        total_chars = 0
        
        for i, result in enumerate(results, 1):
            source = result['source']
            content = result['content'][:500]  # Limita cada chunk
            
            part = f"\n### {i}. 📄 `{Path(source).name}`\n"
            part += f"**Similaridade:** {(1 - result['score']):.2%}\n"
            part += f"```python\n{content}\n```\n"
            
            if total_chars + len(part) > max_tokens:
                break
                
            context_parts.append(part)
            total_chars += len(part)
        
        return "\n".join(context_parts)
    
    def add_file(self, file_path: Path, verbose: bool = False) -> bool:
        """
        Adiciona um arquivo específico ao índice (incremental)
        
        Args:
            file_path: Caminho do arquivo
            verbose: Mostrar logs
            
        Returns:
            True se adicionado com sucesso
        """
        if not self.is_available():
            return False
        
        try:
            from langchain_community.document_loaders import TextLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            if verbose:
                print(f"📄 Adicionando arquivo: {file_path.name}")
            
            # Carrega apenas este arquivo
            loader = TextLoader(str(file_path), encoding='utf-8')
            documents = loader.load()
            
            # Divide em chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_documents(documents)
            
            # Adiciona ao vectorstore existente
            vectorstore = self._init_vectorstore()
            if vectorstore:
                vectorstore.add_documents(chunks)
                vectorstore.persist()
                
                if verbose:
                    print(f"✅ Arquivo adicionado: {len(chunks)} chunks")
                return True
            
            return False
            
        except Exception as e:
            if verbose:
                print(f"❌ Erro ao adicionar arquivo: {e}")
            return False
    
    def clear_index(self, verbose: bool = False) -> bool:
        """Limpa o índice RAG"""
        import shutil
        
        try:
            if self.index_path.exists():
                shutil.rmtree(self.index_path)
                if verbose:
                    print(f"🗑️ Índice removido: {self.index_path}")
            self._vectorstore = None
            return True
        except Exception as e:
            if verbose:
                print(f"❌ Erro ao limpar índice: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do índice"""
        stats = {
            "exists": self.index_path.exists(),
            "is_available": self.is_available(),
            "path": str(self.index_path)
        }
        
        metadata_path = self.index_path / "metadata.json"
        if metadata_path.exists():
            try:
                with open(metadata_path) as f:
                    stats.update(json.load(f))
            except:
                pass
        
        return stats

