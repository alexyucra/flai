"""
DB Agent - Banco de dados via CLI do Fleting (db init/make/migrate/status)
"""
from pathlib import Path
from typing import Dict, Optional

from flai.core.executors.fleting_executor import FletingExecutor, Confirm


class DBAgent:
    def __init__(self, project_path: Optional[Path] = None, confirm: Optional[Confirm] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path, confirm=confirm)

    def create_migration(self, model_name: str) -> Dict:
        if not self.executor.db_initialized():
            code, out = self.executor.execute(["db", "init"])
            if code != 0:
                return {"success": False, "error": out}
        code, out = self.executor.execute(["db", "make", model_name])
        return {"success": code == 0, "migration": model_name, "output": out}

    def migrate(self) -> Dict:
        code, out = self.executor.execute(["db", "migrate"])
        return {"success": code == 0, "message": out}

    def status(self) -> Dict:
        code, out = self.executor.execute(["db", "status"])
        return {"success": code == 0, "message": out}
