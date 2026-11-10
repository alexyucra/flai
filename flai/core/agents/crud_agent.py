"""
CRUD Agent - Orquestra a criação de CRUD com a CLI do Fleting

Fluxo (Fleting 1.2.x):
  1. fleting create page <nome>   -> model + controller + view + rota
  2. fleting db init              -> só se o projeto ainda não tem migrations/
  3. fleting db make <nome>       -> migration
  4. fleting db migrate           -> aplica (pede confirmação)
"""
from pathlib import Path
from typing import Dict, List, Optional

from flai.core.executors.fleting_executor import (
    FletingExecutor, FletingNameError, fleting_name, Confirm,
)
from flai.cli.console.console import console


class CRUDAgent:
    def __init__(self, project_path: Optional[Path] = None, confirm: Optional[Confirm] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path, confirm=confirm)

    def _step(self, result: Dict, step: str, args: List[str], ok_msg: str) -> bool:
        code, output = self.executor.execute(args)
        success = code == 0
        result["steps"].append({"step": step, "success": success, "message": ok_msg if success else output})
        icon = "✅" if success else ("⏭️" if code == 3 else "❌")
        console.print(f"[dim]{icon} fleting {' '.join(args)}[/dim]")
        if not success and code != 3:
            result["errors"].append(f"{step}: {output or 'falhou'}")
        return success

    def create(self, entity: Optional[str], fields: Optional[List[str]] = None) -> Dict:
        result = {"success": False, "type": "crud_result", "entity": entity or "",
                  "fields": fields or [], "steps": [], "errors": []}
        try:
            name = fleting_name(entity or "")
        except FletingNameError as e:
            result["errors"].append(str(e))
            return result
        result["entity"] = name

        console.print(f"[bold cyan]🚀 Criando CRUD para: {name}[/bold cyan]")
        if not self.executor.is_available():
            result["errors"].append("Fleting não encontrado. Instale com: pip install fleting")
            return result

        if not self._step(result, "create_page", ["create", "page", name], f"Página '{name}' criada"):
            return result
        if not self.executor.db_initialized():
            if not self._step(result, "db_init", ["db", "init"], "Banco inicializado"):
                return result
        if not self._step(result, "db_make", ["db", "make", name], f"Migration '{name}' criada"):
            return result
        # Migrate é opcional: se o usuário recusar, o CRUD continua criado
        self._step(result, "db_migrate", ["db", "migrate"], "Migrations aplicadas")

        if fields:
            result["steps"].append({
                "step": "fields", "success": True,
                "message": f"Adicione os campos {', '.join(fields)} em app/models/{name}_model.py "
                           f"e em migrations/*_{name}.py",
            })
        result["success"] = not result["errors"]
        return result

    def analyze(self, entity: str, entity_type: str = "controller") -> Dict:
        files = list(self.project_path.glob(f"app/**/{entity}*.py"))
        if not files:
            return {"success": False, "message": f"{entity_type} '{entity}' não encontrado"}
        return {"success": True, "entity": entity, "path": str(files[0])}
