# flai/core/agents/project_agent.py
# Substitua TODO o conteúdo:

"""
Project Agent - Contexto e análise do projeto
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

class ProjectAgent:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self._structure = None
    
    def get_structure(self) -> Dict[str, Any]:
        if self._structure is None:
            self._structure = {
                "name": self.project_path.name,
                "path": str(self.project_path),
                "models": self._list_dir("models"),
                "controllers": self._list_dir("controllers"),
                "views": self._list_dir("views"),
                "pages": self._list_dir("pages"),
            }
        return self._structure
    
    def _list_dir(self, dir_name: str) -> List[str]:
        dir_path = self.project_path / dir_name
        if not dir_path.exists():
            return []
        return [f.stem for f in dir_path.glob("*.py") if f.stem != "__init__"]
    
    def find(self, name: str) -> Optional[Path]:
        for ext in ["", ".py"]:
            pattern = f"**/{name}{ext}"
            for file in self.project_path.glob(pattern):
                return file
        return None
    
    def search(self, pattern: str) -> List[Dict]:
        import re
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        for py_file in self.project_path.glob("**/*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding='utf-8')
                for line_num, line in enumerate(content.split('\\n'), 1):
                    if regex.search(line):
                        results.append({"file": str(py_file), "line": line_num, "content": line.strip()[:200]})
                        break
            except:
                continue
        return results
    
    def get_context_prompt(self) -> str:
        structure = self.get_structure()
        return f"""
Projeto: {structure['name']}
Models: {', '.join(structure['models']) if structure['models'] else 'nenhum'}
Controllers: {', '.join(structure['controllers']) if structure['controllers'] else 'nenhum'}
Pages: {', '.join(structure['pages']) if structure['pages'] else 'nenhum'}
"""