"""
Flai Knowledge Manager

Responsável por:

- Registrar documentos
- Registrar URLs
- Classificar conhecimento
- Criar entidades
- Criar packs
- Persistir knowledge.yml

Não realiza embeddings.
Não realiza indexação vetorial.

Essas responsabilidades pertencem ao módulo RAG.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from typing import Optional

import hashlib
import yaml


# ============================================================
# MODELOS
# ============================================================

@dataclass
class KnowledgeEntity:
    id: str
    name: str
    type: str
    source: str

    tags: list[str] = field(default_factory=list)

    description: str = ""

    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


@dataclass
class KnowledgePack:
    id: str
    name: str

    entities: list[str] = field(default_factory=list)

    description: str = ""

    created_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )


# ============================================================
# MANAGER
# ============================================================

class KnowledgeManager:

    DEFAULT_PACKS = {
        "framework": "framework",
        "architecture": "architecture",
        "checklist": "deployment",
        "source_code": "source_code",
        "documentation": "project",
        "project": "project",
    }

    def __init__(
        self,
        flai_dir: str | Path
    ):

        self.flai_dir = Path(flai_dir)

        self.knowledge_dir = (
            self.flai_dir / "knowledge"
        )

        self.entities_dir = (
            self.knowledge_dir / "entities"
        )

        self.packs_dir = (
            self.knowledge_dir / "packs"
        )

        self.catalog_file = (
            self.knowledge_dir / "knowledge.yml"
        )

        self._ensure_structure()

    # ========================================================
    # PUBLIC API
    # ========================================================

    def add_document(
        self,
        source: str
    ) -> KnowledgeEntity:

        source_path = Path(source)

        entity_type = self.classify_document(
            source_path
        )

        entity = self.create_entity(
            source=source,
            entity_type=entity_type
        )

        pack = self.create_pack_from_entity(
            entity
        )

        self.save_entity(entity)

        self.save_pack(pack)

        self.update_catalog()

        return entity

    def add_url(
        self,
        url: str
    ) -> KnowledgeEntity:

        entity_type = "framework"

        entity = self.create_entity(
            source=url,
            entity_type=entity_type
        )

        pack = self.create_pack_from_entity(
            entity
        )

        self.save_entity(entity)

        self.save_pack(pack)

        self.update_catalog()

        return entity

    def list_entities(
        self
    ) -> list[KnowledgeEntity]:

        entities = []

        for file in self.entities_dir.glob("*.yml"):

            with open(file, "r", encoding="utf-8") as f:

                data = yaml.safe_load(f)

                entities.append(
                    KnowledgeEntity(**data)
                )

        return entities

    def list_packs(
        self
    ) -> list[KnowledgePack]:

        packs = []

        for file in self.packs_dir.glob("*.yml"):

            with open(file, "r", encoding="utf-8") as f:

                data = yaml.safe_load(f)

                packs.append(
                    KnowledgePack(**data)
                )

        return packs

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    def classify_document(
        self,
        path: Path
    ) -> str:

        filename = path.name.lower()

        if "checklist" in filename:
            return "checklist"

        if "mvc" in filename:
            return "architecture"

        if "architecture" in filename:
            return "architecture"

        if "controller" in filename:
            return "source_code"

        if "service" in filename:
            return "source_code"

        if "repository" in filename:
            return "source_code"

        if path.suffix in [
            ".py",
            ".dart",
            ".ts",
            ".js"
        ]:
            return "source_code"

        if path.suffix in [
            ".md",
            ".rst"
        ]:
            return "documentation"

        return "project"

    # ========================================================
    # ENTITY
    # ========================================================

    def create_entity(
        self,
        source: str,
        entity_type: str
    ) -> KnowledgeEntity:

        source_name = Path(
            source
        ).stem

        entity_id = self._generate_id(
            source
        )

        return KnowledgeEntity(
            id=entity_id,
            name=source_name,
            type=entity_type,
            source=source,
            tags=[
                entity_type
            ]
        )

    # ========================================================
    # PACK
    # ========================================================

    def create_pack_from_entity(
        self,
        entity: KnowledgeEntity
    ) -> KnowledgePack:

        pack_name = self.DEFAULT_PACKS.get(
            entity.type,
            "project"
        )

        existing = self.load_pack(
            pack_name
        )

        if existing:

            if entity.id not in existing.entities:

                existing.entities.append(
                    entity.id
                )

            return existing

        return KnowledgePack(
            id=pack_name,
            name=pack_name,
            entities=[
                entity.id
            ]
        )

    # ========================================================
    # PERSISTENCE
    # ========================================================

    def save_entity(
        self,
        entity: KnowledgeEntity
    ):

        file = (
            self.entities_dir /
            f"{entity.id}.yml"
        )

        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            yaml.safe_dump(
                asdict(entity),
                f,
                allow_unicode=True,
                sort_keys=False
            )

    def save_pack(
        self,
        pack: KnowledgePack
    ):

        file = (
            self.packs_dir /
            f"{pack.id}.yml"
        )

        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            yaml.safe_dump(
                asdict(pack),
                f,
                allow_unicode=True,
                sort_keys=False
            )

    def load_pack(
        self,
        pack_id: str
    ) -> Optional[KnowledgePack]:

        file = (
            self.packs_dir /
            f"{pack_id}.yml"
        )

        if not file.exists():
            return None

        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            data = yaml.safe_load(f)

        return KnowledgePack(**data)

    def update_catalog(self):

        catalog = {
            "version": 1,
            "entities": [],
            "packs": []
        }

        for entity in self.list_entities():

            catalog["entities"].append({
                "id": entity.id,
                "path": (
                    f"entities/{entity.id}.yml"
                )
            })

        for pack in self.list_packs():

            catalog["packs"].append({
                "id": pack.id,
                "path": (
                    f"packs/{pack.id}.yml"
                )
            })

        with open(
            self.catalog_file,
            "w",
            encoding="utf-8"
        ) as f:

            yaml.safe_dump(
                catalog,
                f,
                allow_unicode=True,
                sort_keys=False
            )

    # ========================================================
    # INTERNALS
    # ========================================================

    def _ensure_structure(self):

        self.knowledge_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.entities_dir.mkdir(
            exist_ok=True
        )

        self.packs_dir.mkdir(
            exist_ok=True
        )

    def _generate_id(
        self,
        source: str
    ) -> str:

        digest = hashlib.md5(
            source.encode()
        ).hexdigest()[:10]

        name = Path(
            source
        ).stem.lower()

        return f"{name}_{digest}"