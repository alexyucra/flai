# flai/core/intent/intent_manager.py
"""
Gerenciador Dinâmico de Intenções para FLAI
Permite adicionar/remover/modificar intenções em tempo real
"""
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import yaml
import re
import json
from datetime import datetime
from flai.core.security import safe_name, safe_join

class IntentPriority(Enum):
    """Prioridade de intenção (para resolver conflitos)"""
    HIGHEST = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    LOWEST = 4

@dataclass
class IntentDefinition:
    """Definição completa de uma intenção"""
    name: str
    description: str
    patterns: List[str]  # Padrões regex
    keywords: List[str]  # Palavras-chave para fallback
    priority: IntentPriority = IntentPriority.NORMAL
    enabled: bool = True
    requires_entity: bool = False
    entity_pattern: Optional[str] = None
    examples: List[str] = field(default_factory=list)
    handler: Optional[str] = None  # Nome do handler no RouterAgent
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "patterns": self.patterns,
            "keywords": self.keywords,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "requires_entity": self.requires_entity,
            "entity_pattern": self.entity_pattern,
            "examples": self.examples,
            "handler": self.handler,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'IntentDefinition':
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            patterns=data.get("patterns", []),
            keywords=data.get("keywords", []),
            priority=IntentPriority(data.get("priority", 2)),
            enabled=data.get("enabled", True),
            requires_entity=data.get("requires_entity", False),
            entity_pattern=data.get("entity_pattern"),
            examples=data.get("examples", []),
            handler=data.get("handler"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )

class IntentManager:
    """Gerencia todas as intenções do FLAI"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.intents_dir = self.project_path / ".flai" / "intents"
        self.intents_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.intents_dir / "config.yaml"
        self.intents: Dict[str, IntentDefinition] = {}
        
        # Compilação em cache para performance
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._pattern_cache_valid = False
        
        self._load_intents()
        self._ensure_default_intents()
    
    def _load_intents(self):
        """Carrega todas as intenções dos arquivos YAML"""
        # Carrega arquivos individuais
        for intent_file in self.intents_dir.glob("intents/*.yaml"):
            try:
                data = yaml.safe_load(intent_file.read_text(encoding='utf-8'))
                intent = IntentDefinition.from_dict(data)
                self.intents[intent.name] = intent
            except Exception as e:
                print(f"Erro ao carregar {intent_file}: {e}")
        
        # Carrega configuração principal se existir
        if self.config_file.exists():
            try:
                config = yaml.safe_load(self.config_file.read_text(encoding='utf-8'))
                for name, intent_data in config.get("intents", {}).items():
                    if name not in self.intents:
                        self.intents[name] = IntentDefinition.from_dict(intent_data)
            except Exception as e:
                print(f"Erro ao carregar config: {e}")
        
        self._invalidate_cache()
    
    def _save_intent(self, intent: IntentDefinition):
        """Salva uma intenção em arquivo individual"""
        intent_dir = self.intents_dir / "intents"
        intent_dir.mkdir(exist_ok=True)
        
        intent_file = safe_join(intent_dir, f"{safe_name(intent.name)}.yaml")
        intent_file.write_text(yaml.dump(intent.to_dict()), encoding='utf-8')
        
        # Atualiza cache em memória
        self.intents[intent.name] = intent
        self._invalidate_cache()
    
    def _delete_intent_file(self, intent_name: str):
        """Remove arquivo de intenção"""
        intent_file = safe_join(self.intents_dir, "intents", f"{safe_name(intent_name)}.yaml")
        if intent_file.exists():
            intent_file.unlink()
    
    def _ensure_default_intents(self):
        """Cria intenções padrão se não existirem"""
        defaults = [
            IntentDefinition(
                name="create_crud",
                description="Cria um CRUD completo para uma entidade",
                patterns=[
                    r"cri(?:a|e)r?\s+crud\s+(?:de\s+)?(\w+)",
                    r"crie\s+crud\s+(?:de\s+)?(\w+)",
                    r"ger(?:a|e)r?\s+crud\s+(?:de\s+)?(\w+)",
                    r"make\s+crud\s+(?:for\s+)?(\w+)",
                    r"novo\s+crud\s+(?:de\s+)?(\w+)"
                ],
                keywords=["crud", "criar crud", "novo crud", "gerar crud"],
                requires_entity=True,
                entity_pattern=r"(\w+)",
                examples=[
                    "criar crud de produtos",
                    "criar crud de usuarios com nome, email",
                    "novo crud de clientes"
                ],
                handler="handle_create_crud"
            ),
            IntentDefinition(
                name="create_form",
                description="Cria um formulário Flet",
                patterns=[
                    r"cri(?:a|e)r?\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
                    r"crie\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
                    r"novo\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)"
                ],
                keywords=["form", "formulário", "criar form", "novo form"],
                requires_entity=True,
                examples=[
                    "criar form login",
                    "criar formulário de contato"
                ],
                handler="handle_create_form"
            ),
            IntentDefinition(
                name="create_page",
                description="Cria uma nova página Flet",
                patterns=[
                    r"cri(?:a|e)r?\s+p[aá]gina\s+(?:de\s+)?(\w+)",
                    r"crie\s+p[aá]gina\s+(?:de\s+)?(\w+)",
                    r"criar\s+page\s+(\w+)",
                    r"nova\s+p[aá]gina\s+(?:de\s+)?(\w+)",
                    r"me\s+ajude\s+a\s+criar\s+um\s+novo\s+page\s+(\w+)"
                ],
                keywords=["página", "pagina", "page", "criar página", "nova página"],
                requires_entity=True,
                examples=[
                    "criar página dashboard",
                    "criar page alunos",
                    "me ajude a criar um novo page produtos"
                ],
                handler="handle_create_page"
            ),
            IntentDefinition(
                name="analyze",
                description="Analisa um componente do projeto",
                patterns=[
                    r"analis(?:a|e)\s+(?:o\s+)?(controller|model|page|view)\s+(\w+)",
                    r"analise\s+(?:o\s+)?(controller|model|page|view)\s+(\w+)",
                    r"mostre\s+(?:o\s+)?(controller|model|page|view)\s+(\w+)"
                ],
                keywords=["analisar", "analise", "mostrar", "ver"],
                requires_entity=True,
                examples=[
                    "analise o controller user",
                    "mostre o model produto"
                ],
                handler="handle_analyze"
            ),
            IntentDefinition(
                name="where",
                description="Busca informações no código",
                patterns=[
                    r"onde\s+est[aá]\s+(.+)\??",
                    r"cad(?:a|o)\s+(.+)",
                    r"onde\s+f(?:i|ic)a\s+(.+)\??",
                    r"buscar\s+(.+)"
                ],
                keywords=["onde", "cadê", "buscar", "procurar", "encontrar"],
                requires_entity=True,
                examples=[
                    "onde está a autenticação?",
                    "buscar função de login"
                ],
                handler="handle_search"
            ),
            IntentDefinition(
                name="help",
                description="Mostra ajuda com comandos",
                patterns=[
                    r"ajuda",
                    r"help",
                    r"\?",
                    r"comandos",
                    r"o que (?:você|vc) (?:faz|sabe fazer)"
                ],
                keywords=["ajuda", "help", "comandos", "?"],
                requires_entity=False,
                examples=["ajuda", "help", "o que você faz?"],
                handler="handle_help"
            ),
            IntentDefinition(
                name="exit",
                description="Sai do programa",
                patterns=[
                    r"sair",
                    r"exit",
                    r"quit",
                    r"q"
                ],
                keywords=["sair", "exit", "quit", "q"],
                requires_entity=False,
                examples=["sair", "exit", "q"],
                handler="handle_exit"
            )
        ]
        
        for default in defaults:
            if default.name not in self.intents:
                self.add_intent(default)
    
    def add_intent(self, intent: IntentDefinition) -> bool:
        """Adiciona uma nova intenção"""
        if intent.name in self.intents:
            return False
        
        intent.created_at = datetime.now().isoformat()
        intent.updated_at = datetime.now().isoformat()
        
        self._save_intent(intent)
        return True
    
    def update_intent(self, intent_name: str, **kwargs) -> bool:
        """Atualiza uma intenção existente"""
        if intent_name not in self.intents:
            return False
        
        intent = self.intents[intent_name]
        
        for key, value in kwargs.items():
            if hasattr(intent, key):
                setattr(intent, key, value)
        
        intent.updated_at = datetime.now().isoformat()
        
        self._save_intent(intent)
        return True
    
    def delete_intent(self, intent_name: str) -> bool:
        """Remove uma intenção"""
        if intent_name not in self.intents:
            return False
        
        # Não permite deletar intenções padrão?
        # if intent_name in DEFAULT_INTENT_NAMES:
        #     return False
        
        del self.intents[intent_name]
        self._delete_intent_file(intent_name)
        self._invalidate_cache()
        return True
    
    def enable_intent(self, intent_name: str, enabled: bool = True) -> bool:
        """Habilita ou desabilita uma intenção"""
        return self.update_intent(intent_name, enabled=enabled)
    
    def add_pattern(self, intent_name: str, pattern: str) -> bool:
        """Adiciona um novo padrão regex a uma intenção"""
        if intent_name not in self.intents:
            return False
        
        intent = self.intents[intent_name]
        if pattern not in intent.patterns:
            intent.patterns.append(pattern)
            return self.update_intent(intent_name, patterns=intent.patterns)
        return False
    
    def add_keyword(self, intent_name: str, keyword: str) -> bool:
        """Adiciona uma nova palavra-chave a uma intenção"""
        if intent_name not in self.intents:
            return False
        
        intent = self.intents[intent_name]
        if keyword not in intent.keywords:
            intent.keywords.append(keyword)
            return self.update_intent(intent_name, keywords=intent.keywords)
        return False
    
    def get_intent(self, intent_name: str) -> Optional[IntentDefinition]:
        """Retorna uma intenção pelo nome"""
        return self.intents.get(intent_name)
    
    def list_intents(self, enabled_only: bool = True) -> List[IntentDefinition]:
        """Lista todas as intenções"""
        intents = self.intents.values()
        if enabled_only:
            intents = [i for i in intents if i.enabled]
        return sorted(intents, key=lambda x: x.priority.value)
    
    def _compile_patterns(self):
        """Compila todos os padrões regex para cache"""
        self._compiled_patterns = {}
        
        for intent in self.intents.values():
            if not intent.enabled:
                continue
            
            for pattern in intent.patterns:
                try:
                    self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
                except re.error as e:
                    print(f"Erro na pattern {pattern}: {e}")
        
        self._pattern_cache_valid = True
    
    def _invalidate_cache(self):
        """Invalida o cache de padrões compilados"""
        self._pattern_cache_valid = False
    
    def match_intent(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Encontra a intenção que melhor corresponde ao texto
        
        Returns:
            (intent_name, entity) ou (None, None)
        """
        if not self._pattern_cache_valid:
            self._compile_patterns()
        
        text_lower = text.lower().strip()
        
        # Ordena intenções por prioridade
        sorted_intents = sorted(
            self.intents.values(),
            key=lambda x: x.priority.value
        )
        
        for intent in sorted_intents:
            if not intent.enabled:
                continue
            
            for pattern_str, pattern in self._compiled_patterns.items():
                if pattern_str in intent.patterns:
                    match = pattern.search(text_lower)
                    if match:
                        # Extrai entidade se necessário
                        entity = None
                        if intent.requires_entity and match.groups():
                            entity = match.group(1)
                            # Para analyze, o primeiro grupo é tipo, segundo é nome
                            if intent.name == "analyze" and len(match.groups()) >= 2:
                                entity = f"{match.group(1)} {match.group(2)}"
                        
                        return intent.name, entity
        
        # Fallback: busca por palavras-chave
        return self._match_by_keywords(text_lower)
    
    def _match_by_keywords(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """Fallback: match por palavras-chave"""
        best_intent = None
        best_score = 0
        best_entity = None
        
        for intent in self.intents.values():
            if not intent.enabled:
                continue
            
            for keyword in intent.keywords:
                if keyword in text:
                    score = len(keyword) / len(text) if text else 0
                    if score > best_score:
                        best_score = score
                        best_intent = intent.name
                        
                        # Tenta extrair entidade (palavra após a keyword)
                        if intent.requires_entity:
                            words = text.split()
                            for i, w in enumerate(words):
                                if w == keyword and i + 1 < len(words):
                                    best_entity = words[i + 1]
                                    break
        
        return best_intent, best_entity
    
    def extract_fields(self, text: str) -> List[str]:
        """Extrai campos da descrição (ex: 'com nome, email, idade')"""
        # Padrões para extração de campos
        field_patterns = [
            r"com\s+os\s+campos?\s*:\s*(.+)",
            r"com\s+(.+)",
            r"campos?\s*:\s*(.+)",
            r"contendo\s+(.+)"
        ]
        
        text_lower = text.lower()
        
        for pattern in field_patterns:
            match = re.search(pattern, text_lower)
            if match:
                fields_str = match.group(1)
                # Separa por vírgula, "e", "e também"
                fields = re.split(r'[ ,]+\s*[e&]\s*|[ ,]+|\s+e\s+', fields_str)
                fields = [f.strip() for f in fields if f.strip() and len(f.strip()) > 1]
                
                # Remove stopwords
                stopwords = {"com", "de", "os", "as", "do", "da", "dos", "das", "e", "&"}
                fields = [f for f in fields if f not in stopwords]
                
                return fields[:10]
        
        return []
    
    def suggest_intents(self, text: str, limit: int = 3) -> List[tuple[str, float]]:
        """Sugere intenções similares para uma consulta desconhecida"""
        text_lower = text.lower()
        suggestions = []
        
        for intent in self.intents.values():
            if not intent.enabled:
                continue
            
            # Calcula similaridade com padrões
            max_score = 0.0
            
            for pattern in intent.patterns:
                # Simplificação: overlap de palavras
                pattern_words = set(re.findall(r'\w+', pattern.lower()))
                text_words = set(re.findall(r'\w+', text_lower))
                
                if pattern_words:
                    overlap = len(pattern_words & text_words)
                    score = overlap / len(pattern_words)
                    max_score = max(max_score, score)
            
            # Similaridade com keywords
            for keyword in intent.keywords:
                if keyword in text_lower:
                    score = len(keyword) / len(text_lower) if text_lower else 0
                    max_score = max(max_score, score)
            
            if max_score > 0.1:
                suggestions.append((intent.name, max_score))
        
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:limit]
    
    def export_intents(self, format: str = "yaml") -> str:
        """Exporta todas as intenções para backup"""
        export_data = {
            "version": "1.0.0",
            "exported_at": datetime.now().isoformat(),
            "intents": {name: intent.to_dict() for name, intent in self.intents.items()}
        }
        
        if format == "yaml":
            return yaml.dump(export_data)
        else:
            return json.dumps(export_data, indent=2)
    
    def import_intents(self, data: str, format: str = "yaml") -> int:
        """Importa intenções de um arquivo de backup"""
        try:
            if format == "yaml":
                import_data = yaml.safe_load(data)
            else:
                import_data = json.loads(data)
            
            imported_count = 0
            for name, intent_data in import_data.get("intents", {}).items():
                intent = IntentDefinition.from_dict(intent_data)
                self.add_intent(intent)
                imported_count += 1
            
            return imported_count
        except Exception as e:
            print(f"Erro na importação: {e}")
            return 0