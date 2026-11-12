# flai/core/agents/project_agent.py
# Substitua TODO o conteúdo:

"""
Project Agent - Contexto e análise do projeto
"""
from pathlib import Path
from typing import Dict, List, Optional, Any

class ProjectAgent:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self._structure = None
    
    def get_structure(self) -> Dict[str, Any]:
        if self._structure is None:
            self._structure = {
                "name": self.project_path.name,
                "path": str(self.project_path),
                "models": self._list_dir("app/models"),
                "controllers": self._list_dir("app/controllers"),
                "views": self._list_dir("app/views"),
                "pages": self._list_dir("app/views/pages"),
            }
        return self._structure

    def _list_dir(self, dir_name: str) -> List[str]:
        """Lista módulos (estrutura Fleting: app/<tipo>/; cai para <tipo>/ na raiz)."""
        dir_path = self.project_path / dir_name
        if not dir_path.exists():
            dir_path = self.project_path / Path(dir_name).name
        if not dir_path.exists():
            return []
        return sorted(f.relative_to(dir_path).with_suffix("").as_posix()
                      for f in dir_path.rglob("*.py")
                      if f.stem != "__init__" and "__pycache__" not in f.parts)
    
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