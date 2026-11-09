# flai/core/executors/fleting_executor.py
# Substitua TODO o conteúdo por este:

"""
Fleting Executor - Executa comandos do framework Fleting
"""
import subprocess
import shlex
from pathlib import Path
from typing import Tuple, Optional, List

class FletingExecutor:
    """Executor de comandos do framework Fleting"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self._fleting_available = None
    
    def run(self, command: str) -> Tuple[int, str, str]:
        """Executa comando do Fleting"""
        full_cmd = f"fleting {command}"
        try:
            args = shlex.split(full_cmd)
            result = subprocess.run(
                args,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Comando excedeu tempo limite"
        except FileNotFoundError:
            return -1, "", "Comando 'fleting' não encontrado"
        except Exception as e:
            return -1, "", str(e)
    
    def create_page(self, page_name: str) -> bool:
        """Cria uma nova página"""
        code, _, _ = self.run(f"create page {page_name}")
        return code == 0
    
    def create_model(self, model_name: str) -> bool:
        """Cria um novo model/migration"""
        code, _, _ = self.run(f"db make {model_name}")
        return code == 0
    
    def run_migrations(self) -> bool:
        """Executa migrations"""
        code, _, _ = self.run("db migrate")
        if code != 0:
            code, _, _ = self.run("migrate")
        return code == 0
    
    def list_pages(self) -> List[str]:
        """Lista páginas existentes"""
        pages_dir = self.project_path / "pages"
        if not pages_dir.exists():
            return []
        return [f.stem for f in pages_dir.glob("*.py") if f.stem != "__init__"]
    
    def list_models(self) -> List[str]:
        """Lista models existentes"""
        models_dir = self.project_path / "models"
        if not models_dir.exists():
            return []
        return [f.stem for f in models_dir.glob("*.py") if f.stem != "__init__"]
    
    def is_available(self) -> bool:
        """Verifica se Fleting está disponível"""
        if self._fleting_available is None:
            code, _, _ = self.run("--version")
            self._fleting_available = (code == 0)
        return self._fleting_available
    
    def get_project_info(self) -> dict:
        """Retorna informações do projeto"""
        return {
            "path": str(self.project_path),
            "has_fleting": self.is_available(),
            "pages": self.list_pages(),
            "models": self.list_models(),
            "has_migrations": (self.project_path / "migrations").exists()
        }