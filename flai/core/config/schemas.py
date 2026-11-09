"""
Schemas Pydantic para validação de configuração
"""
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ValidationError
import json
import yaml
from enum import Enum

# ============================================================
# ENUMS
# ============================================================

class AgentType(str, Enum):
    BUILTIN = "builtin"
    CUSTOM = "custom"
    EXTERNAL = "external"

class AgentPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    LOWEST = "lowest"

class IntentPriority(str, Enum):
    HIGHEST = "highest"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    LOWEST = "lowest"

class ContextType(str, Enum):
    LOCAL_FILE = "local_file"
    GIT_REPO = "git_repo"
    PROJECT_CODE = "project_code"
    URL = "url"
    CUSTOM = "custom"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

# ============================================================
# CONFIGURAÇÃO PRINCIPAL
# ============================================================

class RAGConfig(BaseModel):
    """Configuração do RAG (Retrieval Augmented Generation)"""
    enabled: bool = Field(default=True, description="Habilitar RAG")
    auto_index: bool = Field(default=True, description="Indexar automaticamente")
    chunk_size: int = Field(default=1000, ge=100, le=5000, description="Tamanho do chunk")
    chunk_overlap: int = Field(default=200, ge=0, le=1000, description="Sobreposição de chunks")
    max_results: int = Field(default=5, ge=1, le=20, description="Máximo de resultados")
    embedding_model: str = Field(default="nomic-embed-text", description="Modelo de embedding")
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_overlap(cls, v: int, info) -> int:
        """Valida que overlap não é maior que chunk_size"""
        chunk_size = info.data.get('chunk_size', 1000)
        if v >= chunk_size:
            raise ValueError(f'chunk_overlap ({v}) deve ser menor que chunk_size ({chunk_size})')
        return v


class AgentConfig(BaseModel):
    """Configuração de um agente"""
    name: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_\-]+$')
    description: str = Field(default="", max_length=500)
    type: AgentType = Field(default=AgentType.CUSTOM)
    module_path: str = Field(..., description="Caminho do módulo Python")
    class_name: str = Field(..., description="Nome da classe do agente")
    priority: AgentPriority = Field(default=AgentPriority.NORMAL)
    enabled: bool = Field(default=True)
    auto_load: bool = Field(default=True)
    dependencies: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class IntentConfig(BaseModel):
    """Configuração de uma intenção"""
    name: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_\-]+$')
    description: str = Field(default="", max_length=500)
    patterns: List[str] = Field(..., min_length=1, description="Padrões regex")
    keywords: List[str] = Field(default_factory=list)
    priority: IntentPriority = Field(default=IntentPriority.NORMAL)
    enabled: bool = Field(default=True)
    requires_entity: bool = Field(default=False)
    entity_pattern: Optional[str] = Field(default=None)
    examples: List[str] = Field(default_factory=list)
    handler: Optional[str] = Field(default=None)
    
    @field_validator('patterns')
    @classmethod
    def validate_patterns(cls, v: List[str]) -> List[str]:
        """Valida padrões regex"""
        import re
        for pattern in v:
            try:
                re.compile(pattern)
            except re.error as e:
                raise ValueError(f'Padrão regex inválido: {pattern} - {e}')
        return v


class ContextConfig(BaseModel):
    """Configuração de uma fonte de contexto"""
    id: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_\-]+$')
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    type: ContextType = Field(...)
    location: str = Field(..., description="URL, caminho ou repositório")
    enabled: bool = Field(default=True)
    auto_update: bool = Field(default=False)
    update_frequency: Literal["daily", "weekly", "monthly", "manual"] = Field(default="manual")
    rag_indexed: bool = Field(default=False)
    rag_chunk_size: int = Field(default=500, ge=100, le=2000)
    rag_chunk_overlap: int = Field(default=50, ge=0, le=500)


class FlaiConfig(BaseModel):
    """Configuração principal do FLAI"""
    # Versão
    version: str = Field(default="1.0.0", pattern=r'^\d+\.\d+\.\d+$')
    
    # Projeto
    project_path: str = Field(..., description="Caminho do projeto")
    project_name: Optional[str] = Field(default=None, max_length=100)
    
    # Modelo
    model: str = Field(default="flai-coder", min_length=1, max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=32000)
    
    # RAG
    rag: RAGConfig = Field(default_factory=RAGConfig)
    
    # Web
    web_enabled: bool = Field(default=True)
    web_port: int = Field(default=8080, ge=1024, le=65535)
    web_host: str = Field(default="localhost")
    
    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_file: Optional[str] = Field(default=None)
    
    # Outros
    auto_save_history: bool = Field(default=True)
    max_history_size: int = Field(default=1000, ge=10, le=10000)
    
    # Metadados
    setup_date: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)
    
    @field_validator('project_path')
    @classmethod
    def validate_project_path(cls, v: str) -> str:
        """Valida que o caminho do projeto existe"""
        path = Path(v)
        if not path.exists():
            raise ValueError(f'Caminho do projeto não existe: {v}')
        return str(path.resolve())
    
    @field_validator('model')
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Valida nome do modelo"""
        import re
        if not re.match(r'^[a-zA-Z0-9:_\-]+$', v):
            raise ValueError(f'Nome de modelo inválido: {v}. Use apenas letras, números, :, - e _')
        return v
    
    def to_json(self, indent: int = 2) -> str:
        """Exporta para JSON"""
        return json.dumps(self.model_dump(), indent=indent, default=str)
    
    def to_yaml(self) -> str:
        """Exporta para YAML"""
        return yaml.dump(self.model_dump(), default_flow_style=False, allow_unicode=True)
    
    @classmethod
    def from_json(cls, content: str) -> 'FlaiConfig':
        """Carrega de JSON"""
        data = json.loads(content)
        return cls(**data)
    
    @classmethod
    def from_yaml(cls, content: str) -> 'FlaiConfig':
        """Carrega de YAML"""
        data = yaml.safe_load(content)
        return cls(**data)


# ============================================================
# FUNÇÕES DE VALIDAÇÃO
# ============================================================

def validate_config(config_path: Path, config_type: str = "flai") -> tuple[bool, Optional[BaseModel], List[str]]:
    """
    Valida um arquivo de configuração
    
    Args:
        config_path: Caminho do arquivo
        config_type: Tipo de configuração (flai, agent, intent, context)
    
    Returns:
        (válido, instância, erros)
    """
    if not config_path.exists():
        return False, None, [f"Arquivo não encontrado: {config_path}"]
    
    try:
        content = config_path.read_text(encoding='utf-8')
        
        if config_path.suffix == '.json':
            data = json.loads(content)
        else:  # .yaml ou .yml
            data = yaml.safe_load(content)
        
        if config_type == "flai":
            instance = FlaiConfig(**data)
        elif config_type == "agent":
            instance = AgentConfig(**data)
        elif config_type == "intent":
            instance = IntentConfig(**data)
        elif config_type == "context":
            instance = ContextConfig(**data)
        else:
            return False, None, [f"Tipo desconhecido: {config_type}"]
        
        return True, instance, []
        
    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        return False, None, errors
    except json.JSONDecodeError as e:
        return False, None, [f"JSON inválido: {e}"]
    except yaml.YAMLError as e:
        return False, None, [f"YAML inválido: {e}"]
    except Exception as e:
        return False, None, [f"Erro inesperado: {e}"]


def load_config(config_path: Path, config_type: str = "flai") -> Optional[BaseModel]:
    """
    Carrega e valida configuração, retorna None se inválida
    
    Args:
        config_path: Caminho do arquivo
        config_type: Tipo de configuração
    
    Returns:
        Instância validada ou None
    """
    valid, instance, errors = validate_config(config_path, config_type)
    
    if not valid:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Configuração inválida em {config_path}:")
        for error in errors:
            logger.error(f"  - {error}")
        return None
    
    return instance


def create_default_config(project_path: Path, model: str = "flai-coder") -> FlaiConfig:
    """
    Cria configuração padrão para um projeto
    
    Args:
        project_path: Caminho do projeto
        model: Modelo padrão
    
    Returns:
        Configuração padrão
    """
    from datetime import datetime
    
    return FlaiConfig(
        version="1.0.0",
        project_path=str(project_path.resolve()),
        project_name=project_path.name,
        model=model,
        temperature=0.7,
        max_tokens=2048,
        rag=RAGConfig(),
        web_enabled=True,
        web_port=8080,
        web_host="localhost",
        log_level=LogLevel.INFO,
        auto_save_history=True,
        max_history_size=1000,
        setup_date=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )