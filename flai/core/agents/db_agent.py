# flai/core/agents/db_agent.py
# Substitua TODO o conteúdo:

"""
DB Agent - Especialista em banco de dados
"""
from pathlib import Path
from typing import Dict, List, Optional
from flai.core.executors.fleting_executor import FletingExecutor
from flai.cli.console.console import console

class DBAgent:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path)
    
    def create_migration(self, model_name: str) -> Dict:
        console.print(f"[bold cyan]🗄️ Criando model: {model_name}[/bold cyan]")
        success = self.executor.create_model(model_name)
        if success:
            console.print(f"[green]✅ Model '{model_name}' criado[/green]")
            self.executor.run_migrations()
        else:
            console.print(f"[red]❌ Erro ao criar model[/red]")
        return {"success": success, "migration": model_name}
    
    def migrate(self) -> Dict:
        success = self.executor.run_migrations()
        return {"success": success, "message": "Migrations executadas" if success else "Erro nas migrations"}