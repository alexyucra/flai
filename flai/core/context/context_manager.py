# flai/core/context/context_manager.py
"""
Gerenciador de Documentações (fontes de contexto) do FLAI.

Cada fonte é cadastrada, atualizada e indexada por este gerenciador, a partir do
CLI (`flai context ...`) ou do painel web (`flai config` → Contextos). As fontes
podem mudar a qualquer momento: a configuração fica em `.flai/contexts/config.yaml`.

Tipos de fonte:
  project_code  código do projeto (índice principal .flai/vectordb)
  local_file    arquivo ou pasta local
  git_repo      repositório git, numa versão fixa (`ref`) e só nas pastas `paths`
  url           página baixada (https)

Cada fonte tem índice próprio em `.flai/contexts/<id>/vectordb/` e uma prioridade:
nas respostas da IA, fontes de prioridade menor entram primeiro no orçamento de tokens.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from flai.core.security import safe_name, safe_join, validate_remote_url

MAX_URL_BYTES = 5 * 1024 * 1024  # 5 MB
GIT_TIMEOUT = 600
DOC_EXTENSIONS = {".md", ".mdx", ".txt", ".py", ".rst"}
GIT_SAFE = ["git", "-c", "protocol.allow=never", "-c", "protocol.https.allow=always"]
PRIORITY_WEIGHT = 0.02   # bônus por nível de prioridade (desempate)
MIN_SIMILARITY = 0.45    # abaixo disso o trecho é ignorado
RELATIVE_CUTOFF = 0.10   # só trechos próximos do melhor resultado
LEGACY_IDS = {"flet_components", "fleting_mvc"}  # padrões antigos (versão errada / arquivo vazio)


class ContextType(Enum):
    LOCAL_FILE = "local_file"
    GIT_REPO = "git_repo"
    PROJECT_CODE = "project_code"
    URL = "url"


def installed_version(package: str) -> Optional[str]:
    try:
        from importlib.metadata import version
        return version(package)
    except Exception:
        return None


@dataclass
class ContextSource:
    id: str
    name: str
    description: str
    type: ContextType
    location: str
    enabled: bool = True
    priority: int = 2                       # 1 = mais importante
    ref: Optional[str] = None               # git: tag/branch (ex.: v1.0.5)
    paths: List[str] = field(default_factory=list)  # git: subpastas a baixar
    version_from: Optional[str] = None      # pacote cuja versão define o ref (ex.: flet)
    auto_update: bool = False
    update_frequency: str = "manual"
    last_update: Optional[str] = None
    fetched_ref: Optional[str] = None
    rag_indexed: bool = False
    rag_chunks: int = 0
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 150

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["type"] = self.type.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ContextSource":
        known = {f for f in cls.__dataclass_fields__}
        data = {k: v for k, v in d.items() if k in known}
        data["type"] = ContextType(d["type"])
        data["paths"] = list(d.get("paths") or [])
        return cls(**data)


class ContextManager:
    """Gerencia as fontes de documentação e seus índices de busca."""

    def __init__(self, project_path: Path, embed_fn=None):
        self.project_path = Path(project_path)
        self.contexts_dir = self.project_path / ".flai" / "contexts"
        self.contexts_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.contexts_dir / "config.yaml"
        self.sources: Dict[str, ContextSource] = {}
        self._embed_fn = embed_fn  # injeção para testes
        self.last_error: Optional[str] = None
        self._load_config()
        self._ensure_default_contexts()

    # ----------------------------------------------------------- config
    def _load_config(self) -> None:
        if not self.config_file.exists():
            return
        try:
            data = yaml.safe_load(self.config_file.read_text(encoding="utf-8")) or {}
            for item in data.get("sources", []):
                if item.get("id") in LEGACY_IDS:
                    continue
                try:
                    src = ContextSource.from_dict(item)
                    self.sources[src.id] = src
                except Exception as e:
                    print(f"⚠️ Fonte ignorada ({item.get('id')}): {e}")
        except Exception as e:
            print(f"Erro ao carregar contextos: {e}")

    def _save_config(self) -> None:
        config = {"version": "2.0.0", "updated_at": datetime.now().isoformat(),
                  "sources": [s.to_dict() for s in self.sources.values()]}
        self.config_file.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
                                    encoding="utf-8")

    def _ensure_default_contexts(self) -> None:
        flet_ver = installed_version("flet")
        defaults = [
            ContextSource(
                id="project_code", name="Código do Projeto", priority=1,
                description="Código-fonte do projeto Fleting atual",
                type=ContextType.PROJECT_CODE, location=".",
            ),
            ContextSource(
                id="fleting_docs", name="Fleting (CLI e estrutura MVC)", priority=2,
                description="Comandos do Fleting e onde ficam models, controllers, views e rotas",
                type=ContextType.LOCAL_FILE,
                location=str(self.contexts_dir / "fleting_docs" / "source.md"),
                version_from="fleting",
                # resumo curto: trechos menores evitam que ele "vença" toda busca
                rag_chunk_size=350, rag_chunk_overlap=50,
            ),
            ContextSource(
                id="flet_docs", name=f"Documentação Flet {flet_ver or ''}".strip(), priority=3,
                description="Controles, guias e receitas do Flet na versão instalada",
                type=ContextType.GIT_REPO, location="https://github.com/flet-dev/flet",
                ref=f"v{flet_ver}" if flet_ver else None, version_from="flet",
                paths=["website/docs/getting-started", "website/docs/controls",
                       "website/docs/cookbook"],
            ),
        ]
        changed = False
        for d in defaults:
            if d.id not in self.sources:
                self.sources[d.id] = d
                changed = True
        self._write_fleting_docs()
        if changed:
            self._save_config()

    def _write_fleting_docs(self) -> None:
        target = self.contexts_dir / "fleting_docs" / "source.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return  # pode ter sido editado pelo usuário
        ver = installed_version("fleting") or "?"
        target.write_text(FLETING_DOC.format(version=ver), encoding="utf-8")

    # ------------------------------------------------------------- CRUD
    def add_context(self, source_id: str, name: str, description: str, source_type: str,
                    location: str, **kwargs) -> bool:
        """Cadastra uma fonte. kwargs: enabled, priority, ref, paths, version_from, chunk_size."""
        try:
            safe_name(source_id)
            ctype = ContextType(source_type)
            if ctype in (ContextType.URL, ContextType.GIT_REPO):
                validate_remote_url(location)
            paths = kwargs.get("paths") or []
            if isinstance(paths, str):
                paths = [p.strip() for p in paths.replace(";", ",").split(",") if p.strip()]
            for p in paths:
                if p.startswith(("/", "\\")) or ".." in Path(p).parts:
                    raise ValueError(f"Caminho inválido em paths: {p}")
            src = ContextSource(
                id=source_id, name=name, description=description, type=ctype, location=location,
                enabled=kwargs.get("enabled", True), priority=int(kwargs.get("priority", 2)),
                ref=kwargs.get("ref") or None, paths=paths,
                version_from=kwargs.get("version_from") or None,
                rag_chunk_size=int(kwargs.get("chunk_size", 1000)),
                rag_chunk_overlap=int(kwargs.get("chunk_overlap", 150)),
            )
            self.sources[source_id] = src
            safe_join(self.contexts_dir, source_id).mkdir(exist_ok=True)
            self._save_config()
            return True
        except Exception as e:
            self.last_error = str(e)
            print(f"Erro ao adicionar contexto: {e}")
            return False

    def update_source(self, source_id: str, **changes) -> bool:
        """Altera campos de uma fonte (usado pelo painel web). Invalida o índice se preciso."""
        src = self.sources.get(source_id)
        if not src:
            return False
        reindex_fields = {"location", "ref", "paths", "rag_chunk_size", "rag_chunk_overlap"}
        for key, value in changes.items():
            if key in ("enabled", "priority", "name", "description", *reindex_fields) and hasattr(src, key):
                if key == "priority":
                    value = int(value)
                setattr(src, key, value)
        if reindex_fields & set(changes):
            src.rag_indexed = False
        self._save_config()
        return True

    def set_enabled(self, source_id: str, enabled: bool) -> bool:
        return self.update_source(source_id, enabled=enabled)

    def remove_context(self, source_id: str) -> bool:
        if source_id not in self.sources or source_id == "project_code":
            return False
        del self.sources[source_id]
        self._save_config()
        try:
            shutil.rmtree(safe_join(self.contexts_dir, source_id), ignore_errors=True)
        except Exception:
            pass
        return True

    def list_contexts(self) -> List[Dict]:
        return [s.to_dict() for s in sorted(self.sources.values(), key=lambda s: (s.priority, s.id))]

    # ------------------------------------------------------- versões
    def check_versions(self) -> List[Dict[str, str]]:
        """Fontes cuja versão instalada mudou (ex.: Flet atualizado). Ajusta o ref."""
        drifts = []
        for src in self.sources.values():
            if not src.version_from:
                continue
            ver = installed_version(src.version_from)
            if not ver:
                continue
            if src.type == ContextType.GIT_REPO:
                expected, current = f"v{ver}", src.ref
            else:
                expected, current = ver, (src.fetched_ref or ver)
            if current != expected:
                drifts.append({"id": src.id, "from": current or "-", "to": expected})
                if src.type == ContextType.GIT_REPO:
                    src.ref = expected
                    src.name = f"Documentação {src.version_from.capitalize()} {ver}"
                src.rag_indexed = False
        if drifts:
            self._save_config()
        return drifts

    # ------------------------------------------------------ download
    def _content_dir(self, src: ContextSource) -> Path:
        if src.type == ContextType.PROJECT_CODE:
            return self.project_path
        if src.type == ContextType.LOCAL_FILE:
            p = Path(src.location)
            return p if p.is_dir() else p.parent
        return safe_join(self.contexts_dir, safe_name(src.id), "content")

    def update_context(self, source_id: str, force: bool = False) -> bool:
        """Baixa/atualiza o conteúdo da fonte."""
        src = self.sources.get(source_id)
        if not src:
            return False
        try:
            if src.type == ContextType.GIT_REPO:
                ok = self._update_git(src, force)
            elif src.type == ContextType.URL:
                ok = self._update_url(src)
            elif src.type == ContextType.LOCAL_FILE:
                ok = Path(src.location).exists()
                if not ok:
                    self.last_error = f"Arquivo não encontrado: {src.location}"
            else:
                ok = True
            if ok:
                src.last_update = datetime.now().isoformat()
                if src.version_from:
                    src.fetched_ref = src.ref or installed_version(src.version_from)
                self._save_config()
            return ok
        except Exception as e:
            self.last_error = str(e)
            print(f"Erro ao atualizar '{source_id}': {e}")
            return False

    def _update_git(self, src: ContextSource, force: bool) -> bool:
        validate_remote_url(src.location)
        dest = self._content_dir(src)
        if dest.exists() and src.fetched_ref == src.ref and not force:
            return True  # tag já baixada
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        cmd = GIT_SAFE + ["clone", "--depth", "1", "--filter=blob:none"]
        if src.paths:
            cmd.append("--sparse")
        if src.ref:
            cmd += ["--branch", src.ref]
        cmd += ["--", src.location, str(dest)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=GIT_TIMEOUT)
        if r.returncode != 0:
            self.last_error = r.stderr.strip()[-300:]
            return False
        if src.paths:
            r = subprocess.run(GIT_SAFE + ["-C", str(dest), "sparse-checkout", "set", "--", *src.paths],
                               capture_output=True, text=True, timeout=GIT_TIMEOUT)
            if r.returncode != 0:
                self.last_error = r.stderr.strip()[-300:]
                return False
        shutil.rmtree(dest / ".git", ignore_errors=True)  # só o conteúdo importa
        src.rag_indexed = False
        return True

    def _update_url(self, src: ContextSource) -> bool:
        import urllib.request
        validate_remote_url(src.location)
        dest = self._content_dir(src)
        dest.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(src.location, timeout=30) as resp:
            raw = resp.read(MAX_URL_BYTES + 1)
        if len(raw) > MAX_URL_BYTES:
            raise ValueError(f"Conteúdo excede {MAX_URL_BYTES} bytes")
        (dest / "content.md").write_text(raw.decode("utf-8", errors="replace"), encoding="utf-8")
        src.rag_indexed = False
        return True

    # ------------------------------------------------------- índices
    def _rag_for(self, src: ContextSource):
        from flai.core.rag.rag_manager import RAGManager
        if src.type == ContextType.PROJECT_CODE:
            return RAGManager(self.project_path, embed_fn=self._embed_fn)
        rag = RAGManager(
            self.project_path, embed_fn=self._embed_fn,
            root=self._content_dir(src),
            index_path=safe_join(self.contexts_dir, safe_name(src.id), "vectordb"),
            extensions=DOC_EXTENSIONS, skip_dirs={".git", "__pycache__", "node_modules"},
            chunk_size=src.rag_chunk_size, chunk_overlap=src.rag_chunk_overlap,
        )
        if src.type == ContextType.LOCAL_FILE and Path(src.location).is_file():
            only = Path(src.location).resolve()
            rag._project_files = lambda: [only]  # indexa só o arquivo indicado
        return rag

    def index_context(self, source_id: str, verbose: bool = False) -> bool:
        """Baixa (se preciso) e indexa a fonte no seu próprio índice."""
        src = self.sources.get(source_id)
        if not src:
            self.last_error = f"Fonte não encontrada: {source_id}"
            return False
        if src.type in (ContextType.GIT_REPO, ContextType.URL) and not self._content_dir(src).exists():
            if not self.update_context(source_id):
                return False
        rag = self._rag_for(src)
        ok = rag.index_project(verbose=verbose)
        if not ok:
            self.last_error = rag.last_error
            return False
        src.rag_indexed = True
        src.rag_chunks = rag.get_index_stats().get("total_chunks", 0)
        self._save_config()
        return True

    def search_contexts(self, query: str, source_ids: Optional[List[str]] = None,
                        k: int = 5) -> List[Dict]:
        """Busca em cada fonte habilitada e indexada (no índice da própria fonte)."""
        if source_ids is None:
            sources = [s for s in self.sources.values() if s.enabled and s.rag_indexed]
        else:
            sources = [self.sources[i] for i in source_ids if i in self.sources]
        results = []
        for src in sorted(sources, key=lambda s: s.priority):
            for hit in self._rag_for(src).search(query, k=k):
                results.append({**hit, "source_id": src.id, "source_name": src.name,
                                "priority": src.priority})
        # Relevância primeiro; a prioridade só dá um pequeno bônus (desempate)
        for r in results:
            r["rank"] = r.get("similarity", 1 - r["score"]) - PRIORITY_WEIGHT * (r["priority"] - 1)
        results.sort(key=lambda r: r["rank"], reverse=True)
        return results

    def get_prompt_parts(self, query: str, k: int = 3,
                         exclude: tuple = ("project_code",)) -> List[str]:
        """Trechos das documentações, rotulados com a fonte, em ordem de prioridade."""
        ids = [s.id for s in self.sources.values()
               if s.enabled and s.rag_indexed and s.id not in exclude]
        results = self.search_contexts(query, ids, k=k)
        if not results:
            return []
        best = results[0].get("similarity", 0)
        parts = []
        for r in results:
            sim = r.get("similarity", 0)
            # descarta trechos pouco relacionados (absoluto e relativo ao melhor)
            if sim < MIN_SIMILARITY or sim < best - RELATIVE_CUTOFF:
                continue
            parts.append(f"[{r['source_name']} › {r['source']}]\n{r['content']}")
        return parts[:k * 2]

    def get_context_prompt(self, query: str = "", max_contexts: int = 3) -> str:
        parts = self.get_prompt_parts(query, k=max_contexts) if query else []
        lines = ["# 📚 Documentações disponíveis"]
        for s in self.list_contexts():
            if s["enabled"]:
                lines.append(f"- {'✅' if s['rag_indexed'] else '⏳'} {s['name']}")
        return "\n".join(lines + parts)

    def get_fleting_mvc_context(self) -> str:
        p = self.contexts_dir / "fleting_docs" / "source.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""


FLETING_DOC = """# Fleting {version}: CLI e estrutura

## Estrutura de um projeto Fleting
- app/models/<nome>_model.py: classe <Nome>Model (dados)
- app/controllers/<nome>_controller.py: classe <Nome>Controller (regras)
- app/views/pages/<nome>_view.py: classe <Nome>View (tela Flet)
- app/views/layouts/: layouts compartilhados
- configs/routes.py: rotas (ex.: /produtos)
- configs/database.py: configuração do banco (SQLite padrão, MySQL/MariaDB opcional)
- migrations/00N_<nome>.py: funções up(db) e down(db)
- seeds/: funções run(db), devem ser idempotentes
- data/fleting.db: banco SQLite

## Comandos
- fleting init <app>: cria o projeto (--mysql para MySQL/MariaDB)
- fleting info | fleting doctor | fleting run
- fleting create page <nome>: model + controller + view + rota
- fleting create view|model|controller <nome>
- fleting delete page|view|model|controller <nome>
- fleting list pages|views|models|controllers|routes
- fleting db init (--mysql | --sqlite) | db make <nome> | db migrate | db rollback | db status | db seed
- fleting db model pull [<tabela>] [--force]: gera models a partir do banco
- fleting shell: console interativo do banco

## Regras de nomes
Minúsculas, números e '_', começando por letra (ex.: produtos, user_profile).
"""
