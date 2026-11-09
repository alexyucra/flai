from .common import (
    # Resultados
    RouteResult, CRUDResult, FormResult, AnalysisResult,
    SearchResult, SearchResultItem, LLMResponse, ErrorResult,  # ← ADICIONAR ErrorResult
    # Contextos
    ProjectContext, IntentData, AgentContext,
    # Callbacks
    ProgressCallback, ErrorCallback,
    # Enums
    IntentType, ResultType, AgentStatus
)

__all__ = [
    "RouteResult", "CRUDResult", "FormResult", "AnalysisResult",
    "SearchResult", "SearchResultItem", "LLMResponse", "ErrorResult",  # ← ADICIONAR
    "ProjectContext", "IntentData", "AgentContext",
    "ProgressCallback", "ErrorCallback",
    "IntentType", "ResultType", "AgentStatus"
]