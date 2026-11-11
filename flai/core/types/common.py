"""
Tipos comuns usados em todo o FLAI
"""
from typing import TypedDict, Optional, List, Dict, Any, Union, Callable
from enum import Enum

# ============================================================
# ENUMS
# ============================================================

class IntentType(str, Enum):
    """Tipos de intenção"""
    CREATE_CRUD = "create_crud"
    CREATE_FORM = "create_form"
    CREATE_PAGE = "create_page"
    CREATE_MODEL = "create_model"
    ANALYZE = "analyze"
    WHERE = "where"
    SEARCH = "search"
    REFACTOR = "refactor"
    HELP = "help"
    EXIT = "exit"
    UNKNOWN = "unknown"


class ResultType(str, Enum):
    """Tipos de resultado"""
    CRUD_RESULT = "crud_result"
    FORM_RESULT = "form_result"
    ANALYSIS = "analysis"
    SEARCH_RESULTS = "search_results"
    HELP = "help"
    ERROR = "error"
    EXIT = "exit"
    LLM_RESPONSE = "llm_response"


class AgentStatus(str, Enum):
    """Status do agente"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# ============================================================
# RESULTADOS (TypedDict para estruturação)
# ============================================================

class CRUDStep(TypedDict):
    """Passo da criação de CRUD"""
    step: str
    success: bool
    message: str


class CRUDResult(TypedDict):
    """Resultado da criação de CRUD"""
    success: bool
    entity: str
    fields: List[str]
    steps: List[CRUDStep]
    errors: List[str]
    type: ResultType


class FormResult(TypedDict):
    """Resultado da criação de formulário"""
    success: bool
    form: str
    message: str
    type: ResultType


class AnalysisResult(TypedDict):
    """Resultado de análise"""
    success: bool
    type: ResultType
    content: Union[str, Dict[str, Any]]
    entity: Optional[str]


class SearchResultItem(TypedDict):
    """Item de resultado de busca"""
    file: str
    line: int
    content: str


class SearchResult(TypedDict):
    """Resultado de busca"""
    success: bool
    type: ResultType
    content: List[SearchResultItem]
    query: Optional[str]


class LLMResponse(TypedDict):
    """Resposta do LLM"""
    success: bool
    type: ResultType
    content: str
    model: Optional[str]


class ErrorResult(TypedDict):
    """Resultado de erro"""
    success: bool
    type: ResultType
    error: str
    details: Optional[str]


# Tipo unificado para todos os resultados
RouteResult = Union[CRUDResult, FormResult, AnalysisResult, SearchResult, LLMResponse, ErrorResult]


# ============================================================
# CONTEXTOS
# ============================================================

class ProjectContext(TypedDict):
    """Contexto do projeto"""
    name: str
    path: str
    structure: Dict[str, Any]
    components: Dict[str, List[str]]
    timestamp: str


class IntentData(TypedDict):
    """Dados da intenção parseada"""
    original: str
    intent: str
    entity: Optional[str]
    fields: List[str]
    confidence: float
    method: Optional[str]


class AgentContext(TypedDict, total=False):
    """Contexto para execução de agentes"""
    user_query: str
    intent_data: IntentData
    project_context: ProjectContext
    session_id: Optional[str]
    previous_results: List[RouteResult]
    metadata: Dict[str, Any]


# ============================================================
# CALLBACKS
# ============================================================

ProgressCallback = Callable[[str, int, Optional[int]], None]
ErrorCallback = Callable[[str, Exception], None]
