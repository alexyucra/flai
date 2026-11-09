# flai/core/agents/router_agent.py

"""
Router Agent - Roteador de intenções para agentes especializados
"""
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import sys
import asyncio
from flai.core.types import (
    RouteResult, CRUDResult, AnalysisResult, SearchResult, 
    ErrorResult, IntentType, ResultType, IntentData
)

from flai.core.intent.parser import IntentParser
from flai.core.agents.crud_agent import CRUDAgent
from flai.core.agents.form_agent import FormAgent
from flai.core.agents.project_agent import ProjectAgent
from flai.core.agents.db_agent import DBAgent
from flai.core.agents.agent_manager import AgentManager
from flai.core.agents.help_agent import HelpAgent
from flai.cli.utils.ollama_manager import get_ollama_manager
from flai.cli.console.console import console
from flai.core.async_utils import run_async, background_helper

class RouterAgent:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()

        self.intent_parser = IntentParser()  # Parser é leve, pode criar novo
        from flai.core import get_agent_manager, get_rag, get_context_manager, get_intent_manager, get_ollama
        self.agent_manager = get_agent_manager(self.project_path)  # ✅ Registrado
        self.rag = get_rag(self.project_path, auto_index=False)    # ✅ Registrado
        self.context_manager = get_context_manager(self.project_path)  # ✅ Registrado
        self.ollama = get_ollama()  # ✅ Singleton global
        # self.ollama = get_ollama_manager()

        # Agentes específicos (não compartilhados entre routers)
        self.crud_agent = CRUDAgent(self.project_path)
        self.form_agent = FormAgent(self.project_path)
        self.db_agent = DBAgent(self.project_path)
        self.project_agent = ProjectAgent(self.project_path)
        self.agent_manager = AgentManager(self.project_path)
        self.help_agent = HelpAgent(self.project_path) 
    
    # def route(self, user_input: str) -> Dict[str, Any]:
    async def route(self, user_input: str) -> RouteResult:
        """
        Roteia a intenção para o agente apropriado
        
        Args:
            user_input: Texto do usuário
        
        Returns:
            RouteResult: Resultado tipado da operação
        """
        intent_data = self.intent_parser.parse(user_input)
        intent = intent_data["intent"]
        entity = intent_data.get("entity")
        fields = intent_data.get("fields", [])
        
        console.print(f"[dim]🔍 Intenção detectada: {intent}[/dim]")

        # Handlers síncronos com retorno tipado
        if intent == "help":
            # Usa HelpAgent em vez de texto estático
            context = {
                "user_query": intent_data.get("user_query", user_input),
                "intent_data": intent_data
            }
            result = await self.help_agent.execute(
                intent="help",
                entity=entity,
                fields=fields,
                context=context
            )
            return self._to_route_result(result)

        elif intent == IntentType.CREATE_CRUD.value:
            return self._to_route_result(self.crud_agent.create(entity, fields))
        
        elif intent == IntentType.CREATE_FORM.value:
            return self._to_route_result(self.form_agent.create(entity, fields))
        
        elif intent == IntentType.ANALYZE.value:
            return self._handle_analyze(entity)
        
        elif intent == IntentType.WHERE.value or intent == IntentType.SEARCH.value:
            return self._handle_search(entity or user_input)
        
        elif intent == IntentType.HELP.value:
            return self._handle_help()
        
        elif intent == IntentType.EXIT.value:
            return {"success": True, "type": ResultType.EXIT, "content": "Saindo..."}

        else:
            # Pipeline com agentes
            context = {
                "user_query": user_input,
                "intent_data": intent_data
            }
            return self._run_pipeline_sync(intent, entity, fields, context)
        
        # if intent == "create_crud":
        #     return self.crud_agent.create(entity, fields)
        # elif intent == "create_form":
        #     return self.form_agent.create(entity, fields)
        # elif intent == "analyze":
        #     return self._handle_analyze(entity)
        # elif intent == "where":
        #     return self._handle_search(entity or user_input)
        # elif intent == "help":
        #     return self._handle_help()
        # elif intent == "exit":
        #     return {"type": "exit", "content": "Saindo..."}
        # else:
        #     context = {
        #         "user_query": user_input,
        #         "intent_data": intent_data
        #     }
        #     return self._run_pipeline_sync(intent, entity, fields, context)

    def _to_route_result(self, result: Dict[str, Any]) -> RouteResult:
        """Converte dicionário para RouteResult tipado"""
        result_type = result.get("type", ResultType.ERROR.value)
        
        if result_type == ResultType.CRUD_RESULT.value:
            return CRUDResult(
                success=result.get("success", False),
                entity=result.get("entity", ""),
                fields=result.get("fields", []),
                steps=result.get("steps", []),
                errors=result.get("errors", []),
                type=ResultType.CRUD_RESULT
            )
        elif result_type == ResultType.ANALYSIS.value:
            return AnalysisResult(
                success=True,
                type=ResultType.ANALYSIS,
                content=result.get("content", ""),
                entity=result.get("entity")
            )
        elif result_type == ResultType.SEARCH_RESULTS.value:
            return SearchResult(
                success=True,
                type=ResultType.SEARCH_RESULTS,
                content=result.get("content", []),
                query=result.get("query")
            )
        else:
            return ErrorResult(
                success=False,
                type=ResultType.ERROR,
                error=result.get("error", "Erro desconhecido"),
                details=result.get("details")
            )

    # def _run_pipeline_sync(self, intent: str, entity: str, 
    #                       fields: list, context: dict) -> Dict[str, Any]:
    def _run_pipeline_sync(self, intent: str, entity: Optional[str], 
                           fields: List[str], context: Dict) -> RouteResult:

        """
        Executa pipeline de agentes de forma síncrona
        
        Args:
            intent: Intenção detectada
            entity: Entidade extraída
            fields: Campos extraídos
            context: Contexto adicional
        
        Returns:
            Resultado da pipeline
        """
        # Método 1: Usar run_async (recomendado)
        try:
            result = run_async(
                self.agent_manager.execute_pipeline(
                    intent=intent,
                    entity=entity,
                    fields=fields,
                    context=context
                ),
                timeout=60
            )
            return self._to_route_result(result)
            
        except RuntimeError as e:
            console.print(f"[red]❌ Erro na pipeline: {e}[/red]")
            return ErrorResult(
                success=False,
                type=ResultType.ERROR,
                error=str(e),
                details="Falha na pipeline de agentes"
            )
    
    async def route_async(self, user_input: str) -> Dict[str, Any]:
        """
        Versão assíncrona do route (para uso em contextos async)
        """
        intent_data = self.intent_parser.parse(user_input)
        intent = intent_data.get("intent", "unknown")
        entity = intent_data.get("entity")
        fields = intent_data.get("fields", [])
        
        console.print(f"[dim]🔍 Intenção detectada: {intent}[/dim]")
        
        if intent == "create_crud":
            # CRUDAgent.create é síncrono, executar em thread pool
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, 
                lambda: self.crud_agent.create(entity, fields)
            )
        elif intent == "create_form":
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                lambda: self.form_agent.create(entity, fields)
            )
        elif intent == "analyze":
            return self._handle_analyze(entity)
        elif intent == "where":
            return self._handle_search(entity or user_input)
        elif intent == "help":
            return self._handle_help()
        elif intent == "exit":
            return {"type": "exit", "content": "Saindo..."}
        else:
            context = {
                "user_query": user_input,
                "intent_data": intent_data
            }
            return await self.agent_manager.execute_pipeline(
                intent=intent,
                entity=entity,
                fields=fields,
                context=context
            )

    # def _handle_analyze(self, target: str) -> Dict:
    def _handle_analyze(self, target: Optional[str]) -> AnalysisResult:
        """Analisa componente do projeto"""
        if not target:
            structure = self.project_agent.get_structure()
            return AnalysisResult(
                success=True,
                type=ResultType.ANALYSIS,
                content=structure,
                entity=None
            )
        file_path = self.project_agent.find(target)
        if file_path:
            content = file_path.read_text()[:2000]
            return AnalysisResult(
                success=True,
                type=ResultType.ANALYSIS,
                content=f"## {target}\n\n```python\n{content}\n```",
                entity=target
            )
        return AnalysisResult(
            success=False,
            type=ResultType.ANALYSIS,
            content=f"Arquivo '{target}' não encontrado",
            entity=target
        )
    
    def _handle_search(self, query: str) -> SearchResult:
        """Busca no projeto"""
        results = self.project_agent.search(query)
        return SearchResult(
            success=True,
            type=ResultType.SEARCH_RESULTS,
            content=results[:10] if results else [],
            query=query
        )

    # def _handle_pipeline(self, intent: str, entity: str, fields: list, context: dict) -> Dict:
    #     """
    #     Encaminha solicitações para a pipeline de agentes.
    #     """

    #     import asyncio

    #     try:

    #         return asyncio.run(
    #             self.pipeline.execute(
    #                 intent=intent,
    #                 entity=entity,
    #                 fields=fields,
    #                 context=context
    #             )
    #         )

    #     except Exception as e:

    #         return {
    #             "success": False,
    #             "type": "pipeline_error",
    #             "content": str(e)
    #         }
    
    def _handle_help(self) -> RouteResult:
        """Retorna ajuda"""
        return {
            "success": True,
            "type": ResultType.HELP,
            "content": self.intent_parser.get_help_text()
        }

    def __del__(self):
        """Limpeza - para background loop"""
        try:
            background_helper.stop_background_loop()
        except:
            pass