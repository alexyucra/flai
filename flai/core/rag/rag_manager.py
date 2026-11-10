"""
RAG Manager — busca semântica local e leve.

- Embeddings: Ollama (`nomic-embed-text` por padrão). Usa `langchain_ollama.OllamaEmbeddings`
  quando instalado; senão chama a API `/api/embed` diretamente.
- Chunks: `langchain_text_splitters.RecursiveCharacterTextSplitter` quando instalado;
  senão um divisor interno por linhas.
- Índice: arquivo JSON em `.flai/vectordb/index.json` (sem chromadb — poucos MB de
  dependências, adequado a máquinas com pouca RAM/disco).

API pública mantida: is_available, index_project, search, get_context_for_prompt,
add_file, clear_index, get_index_stats.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_EMBED_MODEL = "nomic-embed-text"
INDEX_EXTENSIONS = {".py", ".md"}
SKIP_DIRS = {".flai", ".venv", "venv", "env", "__pycache__", "node_modules", ".git",
             "data", "build", "dist", "assets", "logs"}
MAX_FILE_BYTES = 200 * 1024
EMBED_BATCH = 16


def _norm(v: List[float]) -> List[float]:
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def simple_split(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Divide por linhas respeitando chunk_size (caracteres) com sobreposição."""
    lines = text.splitlines(keepends=True)
    chunks, cur = [], ""
    for line in lines:
        while len(line) > chunk_size:  # linha gigante
            chunks.append(line[:chunk_size])
            line = line[chunk_size - overlap:]
        if len(cur) + len(line) > chunk_size and cur:
            chunks.append(cur)
            cur = cur[-overlap:] if overlap else ""
        cur += line
    if cur.strip():
        chunks.append(cur)
    return [c for c in chunks if c.strip()]


class RAGManager:
    """Indexa e busca o código do projeto com embeddings locais."""

    def __init__(self, project_path: Path, embed_model: Optional[str] = None,
                 chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None,
                 embed_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
                 root: Optional[Path] = None, index_path: Optional[Path] = None,
                 extensions: Optional[set] = None, skip_dirs: Optional[set] = None):
        """
        project_path: projeto Fleting (lê .flai/config.json)
        root:         pasta a indexar (padrão: o projeto; para documentações, a pasta baixada)
        index_path:   onde salvar o índice (padrão: .flai/vectordb)
        """
        self.project_path = Path(project_path)
        self.root = Path(root) if root else self.project_path
        self.extensions = extensions or INDEX_EXTENSIONS
        self.skip_dirs = SKIP_DIRS if skip_dirs is None else skip_dirs
        self.index_path = Path(index_path) if index_path else self.project_path / ".flai" / "vectordb"
        self.index_file = self.index_path / "index.json"
        cfg = self._load_rag_config()
        self.embed_model = embed_model or cfg.get("embedding_model", DEFAULT_EMBED_MODEL)
        self.chunk_size = int(chunk_size or cfg.get("chunk_size", 1000))
        self.chunk_overlap = int(chunk_overlap if chunk_overlap is not None else cfg.get("chunk_overlap", 200))
        self._embed_fn = embed_fn
        self._index: Optional[Dict[str, Any]] = None
        self.backend = "custom" if embed_fn else None
        self.last_error: Optional[str] = None

    # --------------------------------------------------------------- config
    def _load_rag_config(self) -> Dict[str, Any]:
        cfg_file = self.project_path / ".flai" / "config.json"
        try:
            return json.loads(cfg_file.read_text(encoding="utf-8")).get("rag", {}) or {}
        except Exception:
            return {}

    # ----------------------------------------------------------- embeddings
    def _embedder(self) -> Callable[[List[str]], List[List[float]]]:
        if self._embed_fn:
            return self._embed_fn
        try:
            from langchain_ollama import OllamaEmbeddings
            lc = OllamaEmbeddings(model=self.embed_model, base_url=OLLAMA_URL)
            self.backend = "langchain-ollama"
            self._embed_fn = lc.embed_documents
        except ImportError:
            self.backend = "ollama-http"
            self._embed_fn = self._embed_http
        return self._embed_fn

    def _embed_http(self, texts: List[str]) -> List[List[float]]:
        import requests
        r = requests.post(f"{OLLAMA_URL}/api/embed",
                          json={"model": self.embed_model, "input": texts}, timeout=300)
        if r.status_code != 200:
            raise RuntimeError(f"Ollama /api/embed {r.status_code}: {r.text[:200]}")
        return r.json()["embeddings"]

    @property
    def _prefixes(self) -> tuple:
        """nomic-embed-text foi treinado com prefixos de tarefa; melhora bastante a busca."""
        if "nomic" in self.embed_model and self.backend != "custom":
            return ("search_document: ", "search_query: ")
        return ("", "")

    @property
    def index_key(self) -> str:
        """Identifica modelo + formato; se mudar, o índice é refeito."""
        return self.embed_model + ("+prefix" if self._prefixes[0] else "")

    def _embed(self, texts: List[str], kind: str = "document") -> List[List[float]]:
        fn = self._embedder()
        prefix = self._prefixes[0 if kind == "document" else 1]
        texts = [prefix + t for t in texts]
        out: List[List[float]] = []
        for i in range(0, len(texts), EMBED_BATCH):
            out.extend(_norm(v) for v in fn(texts[i:i + EMBED_BATCH]))
        return out

    def _split(self, text: str) -> List[str]:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap,
                separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""])
            return [c for c in splitter.split_text(text) if c.strip()]
        except ImportError:
            return simple_split(text, self.chunk_size, self.chunk_overlap)

    # ---------------------------------------------------------------- índice
    def is_available(self) -> bool:
        """Disponível se o Ollama responde e o modelo de embedding existe."""
        if self._embed_fn and self.backend == "custom":
            return True
        try:
            import requests
            r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
            names = {m["name"] for m in r.json().get("models", [])}
            ok = self.embed_model in names or f"{self.embed_model}:latest" in names
            if not ok:
                self.last_error = (f"Modelo de embedding '{self.embed_model}' não instalado. "
                                   f"Execute: ollama pull {self.embed_model}")
            return ok
        except Exception as e:
            self.last_error = f"Ollama indisponível: {e}"
            return False

    def _load(self) -> Dict[str, Any]:
        if self._index is None:
            if self.index_file.exists():
                self._index = json.loads(self.index_file.read_text(encoding="utf-8"))
            else:
                self._index = {"model": self.index_key, "files": {}, "chunks": []}
        return self._index

    def save(self) -> None:
        """Persiste o índice (use após add_file)."""
        self._save()

    def _save(self) -> None:
        idx = self._load()
        idx["model"] = self.index_key
        idx["updated_at"] = datetime.now().isoformat()
        self.index_path.mkdir(parents=True, exist_ok=True)
        tmp = self.index_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(idx), encoding="utf-8")
        tmp.replace(self.index_file)
        meta = {"total_documents": len(idx["files"]), "total_chunks": len(idx["chunks"]),
                "embedding_model": self.embed_model, "backend": self.backend,
                "updated_at": idx["updated_at"]}
        (self.index_path / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def _project_files(self) -> List[Path]:
        files = []
        if not self.root.exists():
            return files
        for f in self.root.rglob("*"):
            rel = f.relative_to(self.root)
            if any(part in self.skip_dirs for part in rel.parts[:-1]):
                continue
            if f.is_file() and f.suffix in self.extensions and f.stat().st_size <= MAX_FILE_BYTES:
                files.append(f)
        return sorted(files)

    def _rel(self, file_path: Path) -> str:
        try:
            return Path(file_path).resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return Path(file_path).resolve().as_posix()

    def add_file(self, file_path: Path, verbose: bool = False) -> bool:
        """(Re)indexa um arquivo; ignora se o conteúdo não mudou."""
        file_path = Path(file_path)
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            self.last_error = str(e)
            return False
        idx = self._load()
        key = self._rel(file_path)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if idx["files"].get(key) == digest and idx.get("model") == self.index_key:
            return True
        chunks = self._split(text)
        vectors = self._embed(chunks) if chunks else []
        idx["chunks"] = [c for c in idx["chunks"] if c["source"] != key]
        idx["chunks"].extend({"source": key, "content": c, "vector": [round(x, 6) for x in v]}
                             for c, v in zip(chunks, vectors))
        idx["files"][key] = digest
        if verbose:
            print(f"  📄 {key}: {len(chunks)} chunks")
        return True

    def index_project(self, verbose: bool = True) -> bool:
        if not self.is_available():
            if verbose:
                print(f"⚠️ {self.last_error}")
            return False
        try:
            idx = self._load()
            self._embedder()  # define o backend antes de comparar o formato
            if idx.get("model") != self.index_key:  # modelo/formato trocou: refaz tudo
                self._index = {"model": self.index_key, "files": {}, "chunks": []}
                idx = self._index
            files = self._project_files()
            current = {self._rel(f) for f in files}
            for gone in set(idx["files"]) - current:  # arquivos removidos
                idx["files"].pop(gone, None)
                idx["chunks"] = [c for c in idx["chunks"] if c["source"] != gone]
            if verbose:
                print(f"📚 Indexando {len(files)} arquivos com '{self.embed_model}'...")
            for f in files:
                self.add_file(f, verbose=verbose)
            self._save()
            if verbose:
                print(f"✅ {len(idx['chunks'])} chunks indexados ({self.backend})")
            return True
        except Exception as e:
            self.last_error = str(e)
            if verbose:
                print(f"❌ Erro na indexação: {e}")
            return False

    def search(self, query: str, k: int = 5, verbose: bool = False) -> List[Dict[str, Any]]:
        """Retorna [{source, content, score}] — score = distância (0 = idêntico)."""
        idx = self._load()
        if not idx["chunks"] or not query.strip():
            return []
        try:
            q = self._embed([query], kind="query")[0]
        except Exception as e:
            self.last_error = str(e)
            if verbose:
                print(f"❌ Erro na busca: {e}")
            return []
        scored = sorted(((_dot(q, c["vector"]), c) for c in idx["chunks"]),
                        key=lambda t: t[0], reverse=True)[:k]
        return [{"source": c["source"], "content": c["content"], "score": round(1 - s, 4),
                 "similarity": round(s, 4)} for s, c in scored]

    def get_context_for_prompt(self, query: str, max_tokens: int = 1500, k: int = 3) -> str:
        parts, total = [], 0
        for r in self.search(query, k=k):
            part = f"### {r['source']}\n```python\n{r['content']}\n```"
            if total + len(part) > max_tokens * 3:  # ~3 caracteres por token
                break
            parts.append(part)
            total += len(part)
        return ("## 📚 Contexto do código\n" + "\n".join(parts)) if parts else ""

    def clear_index(self, verbose: bool = False) -> bool:
        try:
            if self.index_path.exists():
                shutil.rmtree(self.index_path)
            self._index = None
            return True
        except Exception as e:
            if verbose:
                print(f"❌ Erro ao limpar índice: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        stats = {"exists": self.index_file.exists(), "is_available": None,
                 "path": str(self.index_path), "embedding_model": self.embed_model}
        meta = self.index_path / "metadata.json"
        if meta.exists():
            try:
                stats.update(json.loads(meta.read_text(encoding="utf-8")))
            except Exception:
                pass
        return stats
