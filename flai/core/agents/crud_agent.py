# flai/core/agents/crud_agent.py
# Substitua TODO o conteúdo:

"""
CRUD Agent - Orquestrador de criação de CRUD
"""
from typing import Dict, List, Optional
from pathlib import Path
import sys

from flai.core.executors.fleting_executor import FletingExecutor
from flai.cli.console.console import console

class CRUDAgent:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path)
    
    def create(self, entity: str, fields: Optional[List[str]] = None) -> Dict:
        console.print(f"[bold cyan]🚀 Criando CRUD para: {entity}[/bold cyan]")
        if fields:
            console.print(f"[dim]Campos: {', '.join(fields)}[/dim]")
        
        result = {
            "success": False,
            "entity": entity,
            "fields": fields or [],
            "steps": [],
            "errors": []
        }
        
        # Step 1: Criar página
        console.print("[dim]📄 Criando página...[/dim]")
        success = self.executor.create_page(entity)
        result["steps"].append({"step": "create_page", "success": success, "message": f"Página '{entity}' criada"})
        if not success:
            result["errors"].append("Falha ao criar página")
            console.print("[red]❌ Falha ao criar página[/red]")
            return result
        console.print("[green]✅ Página criada[/green]")
        
        # Step 2: Criar model
        console.print("[dim]🗄️ Criando model...[/dim]")
        success = self.executor.create_model(entity)
        result["steps"].append({"step": "create_model", "success": success, "message": f"Model '{entity}' criado"})
        if not success:
            result["errors"].append("Falha ao criar model")
            console.print("[red]❌ Falha ao criar model[/red]")
            return result
        console.print("[green]✅ Model criado[/green]")
        
        # Step 3: Executar migrations
        console.print("[dim]🔄 Executando migrations...[/dim]")
        success = self.executor.run_migrations()
        result["steps"].append({"step": "run_migrations", "success": success, "message": "Migrations executadas"})
        
        result["success"] = len(result["errors"]) == 0
        
        if result["success"]:
            console.print(f"[bold green]🎉 CRUD '{entity}' criado com sucesso![/bold green]")
        else:
            console.print(f"[bold red]❌ Erro: {result['errors'][0]}[/bold red]")
        
        return result
    
    def analyze(self, entity: str, entity_type: str = "controller") -> Dict:
        console.print(f"[cyan]🔍 Analisando {entity_type}: {entity}[/cyan]")
        search_pattern = f"**/{entity}.py"
        files = list(self.project_path.glob(search_pattern))
        if not files:
            return {"success": False, "message": f"{entity_type} '{entity}' não encontrado"}
        return {"success": True, "entity": entity, "path": str(files[0])}