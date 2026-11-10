# flai/core/context/context_manager.py
"""
Gerenciador de Múltiplos Contextos com RAG
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
import hashlib
from datetime import datetime
from flai.core.security import safe_name, safe_join, validate_remote_url

MAX_URL_BYTES = 5 * 1024 * 1024  # 5 MB
GIT_TIMEOUT = 300

class ContextType(Enum):
    """Tipo de fonte de contexto"""
    LOCAL_FILE = "local_file"
    GIT_REPO = "git_repo"
    PROJECT_CODE = "project_code"
    URL = "url"
    CUSTOM = "custom"

@dataclass
class ContextSource:
    """Representa uma fonte de contexto"""
    id: str
    name: str
    description: str
    type: ContextType
    location: str  # Caminho do arquivo, URL, ou repo git
    enabled: bool = True
    auto_update: bool = False
    update_frequency: str = "daily"  # daily, weekly, manual
    last_update: Optional[str] = None
    rag_indexed: bool = False
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type.value,
            "location": self.location,
            "enabled": self.enabled,
            "auto_update": self.auto_update,
            "update_frequency": self.update_frequency,
            "last_update": self.last_update,
            "rag_indexed": self.rag_indexed,
            "rag_chunk_size": self.rag_chunk_size,
            "rag_chunk_overlap": self.rag_chunk_overlap
        }

class ContextManager:
    """Gerencia múltiplas fontes de contexto com RAG"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.contexts_dir = self.project_path / ".flai" / "contexts"
        self.contexts_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.contexts_dir / "config.yaml"
        self.sources: Dict[str, ContextSource] = {}
        self._rag_available = None
        
        self._load_config()
        self._ensure_default_contexts()
    
    def _load_config(self):
        """Carrega configuração dos contextos"""
        if self.config_file.exists():
            try:
                data = yaml.safe_load(self.config_file.read_text(encoding='utf-8'))
                for source_data in data.get("sources", []):
                    source = ContextSource(
                        id=source_data["id"],
                        name=source_data["name"],
                        description=source_data["description"],
                        type=ContextType(source_data["type"]),
                        location=source_data["location"],
                        enabled=source_data.get("enabled", True),
                        auto_update=source_data.get("auto_update", False),
                        update_frequency=source_data.get("update_frequency", "daily"),
                        last_update=source_data.get("last_update"),
                        rag_indexed=source_data.get("rag_indexed", False),
                        rag_chunk_size=source_data.get("rag_chunk_size", 500),
                        rag_chunk_overlap=source_data.get("rag_chunk_overlap", 50)
                    )
                    self.sources[source.id] = source
            except Exception as e:
                print(f"Erro ao carregar contextos: {e}")
    
    def _save_config(self):
        """Salva configuração dos contextos"""
        config = {
            "sources": [s.to_dict() for s in self.sources.values()],
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat()
        }
        self.config_file.write_text(yaml.dump(config), encoding='utf-8')
    
    def _ensure_default_contexts(self):
        """Cria contextos padrão se não existirem"""
        defaults = [
            ContextSource(
                id="fleting_mvc",
                name="Arquitetura MVC do Fleting",
                description="Estrutura de diretórios e padrões do framework Fleting",
                type=ContextType.LOCAL_FILE,
                location=str(self.contexts_dir / "fleting_mvc" / "source.md")
            ),
            ContextSource(
                id="flet_components",
                name="Componentes Flet",
                description="Documentação dos componentes UI do Flet",
                type=ContextType.GIT_REPO,
                location="https://github.com/flet-dev/flet",
                auto_update=True,
                update_frequency="weekly"
            ),
            ContextSource(
                id="project_code",
                name="Código do Projeto",
                description="Análise semântica do código fonte do projeto",
                type=ContextType.PROJECT_CODE,
                location=str(self.project_path)
            )
        ]
        
        for default in defaults:
            if default.id not in self.sources:
                self.sources[default.id] = default
        
        self._save_config()
    
    def add_context(self, 
                    source_id: str,
                    name: str,
                    description: str,
                    source_type: str,
                    location: str,
                    **kwargs) -> bool:
        """Adiciona uma nova fonte de contexto"""
        try:
            safe_name(source_id)
            ctype = ContextType(source_type)
            if ctype in (ContextType.URL, ContextType.GIT_REPO):
                validate_remote_url(location)
            source = ContextSource(
                id=source_id,
                name=name,
                description=description,
                type=ContextType(source_type),
                location=location,
                enabled=kwargs.get("enabled", True),
                auto_update=kwargs.get("auto_update", False),
                update_frequency=kwargs.get("update_frequency", "manual"),
                rag_chunk_size=kwargs.get("chunk_size", 500),
                rag_chunk_overlap=kwargs.get("chunk_overlap", 50)
            )
            
            self.sources[source_id] = source
            self._save_config()
            
            # Cria diretório da fonte
            source_dir = safe_join(self.contexts_dir, source_id)
            source_dir.mkdir(exist_ok=True)

            return True
        except Exception as e:
            print(f"Erro ao adicionar contexto: {e}")
            return False
    
    def remove_context(self, source_id: str) -> bool:
        """Remove uma fonte de contexto"""
        if source_id in self.sources:
            del self.sources[source_id]
            self._save_config()
            return True
        return False
    
    def update_context(self, source_id: str, force: bool = False) -> bool:
        """Atualiza o conteúdo de uma fonte de contexto"""
        source = self.sources.get(source_id)
        if not source:
            return False
        
        if source.type == ContextType.GIT_REPO:
            return self._update_git_context(source)
        elif source.type == ContextType.LOCAL_FILE:
            return self._update_file_context(source)
        elif source.type == ContextType.PROJECT_CODE:
            return self._update_project_context(source)
        elif source.type == ContextType.URL:
            return self._update_url_context(source)
        
        return False
    
    def _update_git_context(self, source: ContextSource) -> bool:
        """Clona ou atualiza repositório git"""
        import subprocess
        
        try:
            validate_remote_url(source.location)
            source_dir = safe_join(self.contexts_dir, safe_name(source.id))
            source_dir.mkdir(exist_ok=True)
            # SEC-04: só transporte https; bloqueia ext::, file:// etc.
            git_safe = ["git", "-c", "protocol.allow=never", "-c", "protocol.https.allow=always"]

            # Se já existe, faz pull
            if (source_dir / ".git").exists():
                result = subprocess.run(
                    git_safe + ["pull", "--ff-only"],
                    cwd=source_dir,
                    capture_output=True,
                    text=True,
                    timeout=GIT_TIMEOUT,
                )
            else:
                # Clona o repositório
                result = subprocess.run(
                    git_safe + ["clone", "--depth", "1", "--", source.location, str(source_dir)],
                    capture_output=True,
                    text=True,
                    timeout=GIT_TIMEOUT,
                )
            
            if result.returncode == 0:
                source.last_update = datetime.now().isoformat()
                source.rag_indexed = False  # Marca para reindexar
                self._save_config()
                return True
            return False
        except Exception as e:
            print(f"Erro ao atualizar git: {e}")
            return False
    
    def _update_file_context(self, source: ContextSource) -> bool:
        """Verifica se arquivo local existe"""
        source_path = Path(source.location)
        if source_path.exists():
            source.last_update = datetime.now().isoformat()
            self._save_config()
            return True
        return False
    
    def _update_project_context(self, source: ContextSource) -> bool:
        """Escaneia o código do projeto"""
        source.last_update = datetime.now().isoformat()
        source.rag_indexed = False
        self._save_config()
        return True
    
    def _update_url_context(self, source: ContextSource) -> bool:
        """Baixa conteúdo de URL"""
        import urllib.request
        
        try:
            validate_remote_url(source.location)
            source_dir = safe_join(self.contexts_dir, safe_name(source.id))
            source_dir.mkdir(exist_ok=True)
            output_file = source_dir / "content.md"
            with urllib.request.urlopen(source.location, timeout=30) as response:
                raw = response.read(MAX_URL_BYTES + 1)
                if len(raw) > MAX_URL_BYTES:
                    raise ValueError(f"Conteúdo excede {MAX_URL_BYTES} bytes")
                content = raw.decode('utf-8', errors='replace')
                output_file.write_text(content, encoding='utf-8')
            
            source.last_update = datetime.now().isoformat()
            source.rag_indexed = False
            self._save_config()
            return True
        except Exception as e:
            print(f"Erro ao baixar URL: {e}")
            return False
    
    def index_context(self, source_id: str, verbose: bool = False) -> bool:
        """Indexa uma fonte de contexto para busca semântica (RAG)"""
        from flai.core.rag.rag_manager import RAGManager
        
        source = self.sources.get(source_id)
        if not source:
            return False
        
        # Atualiza o conteúdo primeiro
        self.update_context(source_id)
        
        # Prepara o diretório da fonte
        source_dir = self.contexts_dir / source.id
        
        # Indexa usando RAG
        rag = RAGManager(self.project_path)  # Usa o RAG existente
        
        # Coleciona todos os arquivos da fonte
        documents = []
        if source.type == ContextType.GIT_REPO:
            for file in source_dir.rglob("*.md"):
                documents.append(file)
            for file in source_dir.rglob("*.py"):
                documents.append(file)
        elif source.type == ContextType.LOCAL_FILE:
            doc_path = Path(source.location)
            if doc_path.exists():
                documents.append(doc_path)
        elif source.type == ContextType.PROJECT_CODE:
            for file in self.project_path.rglob("*.py"):
                if "__pycache__" not in str(file):
                    documents.append(file)
        elif source.type == ContextType.URL:
            doc_path = source_dir / "content.md"
            if doc_path.exists():
                documents.append(doc_path)
        
        if verbose:
            print(f"📚 Indexando {len(documents)} documentos para {source.name}...")
        
        # Indexa cada documento
        indexed_count = 0
        for doc in documents:
            if rag.add_file(doc, verbose=False):
                indexed_count += 1
        if indexed_count:
            rag.save()
        
        source.rag_indexed = True
        self._save_config()
        
        if verbose:
            print(f"✅ Indexados {indexed_count} documentos para '{source.name}'")
        
        return indexed_count > 0
    
    def search_contexts(self, query: str, source_ids: List[str] = None, k: int = 5) -> List[Dict]:
        """
        Busca semanticamente em todos os contextos (ou específicos)
        
        Args:
            query: Consulta do usuário
            source_ids: Lista de IDs de fontes para buscar (None = todas habilitadas)
            k: Número de resultados por fonte
        
        Returns:
            Lista de resultados com fonte, conteúdo e score
        """
        from flai.core.rag.rag_manager import RAGManager
        
        results = []
        
        # Determina quais fontes buscar
        if source_ids is None:
            sources = [s for s in self.sources.values() if s.enabled and s.rag_indexed]
        else:
            sources = [self.sources[sid] for sid in source_ids if sid in self.sources]
        
        rag = RAGManager(self.project_path)
        
        for source in sources:
            # Busca no índice específico da fonte
            source_dir = self.contexts_dir / source.id
            if source_dir.exists():
                # Usa o RAG para buscar nos documentos da fonte
                source_results = rag.search(query, k=k)
                
                for result in source_results:
                    results.append({
                        "source_id": source.id,
                        "source_name": source.name,
                        "content": result.get("content", ""),
                        "score": result.get("score", 0.0),
                        "file": result.get("source", "unknown")
                    })
        
        # Ordena por score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return results[:k*len(sources)]
    
    def get_context_prompt(self, query: str = "", max_contexts: int = 3) -> str:
        """
        Constrói prompt com contexto relevante das múltiplas fontes
        
        Args:
            query: Consulta do usuário (opcional, para busca semântica)
            max_contexts: Máximo de fontes de contexto a incluir
        
        Returns:
            Prompt formatado com todos os contextos
        """
        context_parts = []
        
        context_parts.append("# 📚 Contextos Disponíveis para o Assistente\n")
        
        # Se tem query, faz busca semântica
        if query:
            search_results = self.search_contexts(query, k=3)
            
            if search_results:
                context_parts.append("## 🔍 Contexto Relevante (Busca Semântica)\n")
                for result in search_results[:max_contexts]:
                    context_parts.append(f"### Fonte: {result['source_name']}\n")
                    context_parts.append(f"**Conteúdo relevante:**\n")
                    context_parts.append(f"{result['content'][:500]}\n")
        
        # Lista fontes disponíveis
        context_parts.append("## 📂 Fontes de Conhecimento Disponíveis\n")
        
        for source in self.sources.values():
            if source.enabled:
                status = "✅" if source.rag_indexed else "⏳"
                context_parts.append(f"{status} **{source.name}**")
                context_parts.append(f"   - {source.description}")
                if source.last_update:
                    context_parts.append(f"   - Atualizado: {source.last_update[:19]}")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def list_contexts(self) -> List[Dict]:
        """Lista todas as fontes de contexto disponíveis"""
        return [s.to_dict() for s in self.sources.values()]
    
    def get_fleting_mvc_context(self) -> str:
        """Retorna o contexto específico da arquitetura MVC do Fleting"""
        source = self.sources.get("fleting_mvc")
        if not source:
            return self._get_default_fleting_context()
        
        source_path = Path(source.location)
        if source_path.exists():
            return source_path.read_text(encoding='utf-8')
        
        return self._get_default_fleting_context()
    
    def _get_default_fleting_context(self) -> str:
        """Contexto padrão da arquitetura Fleting"""
        return """"""

