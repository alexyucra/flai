"""
Context Builder - Constrói contexto estruturado para IA
"""
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ContextBuilder:
    """Constrói contexto estruturado do projeto"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def build(self, include_code: bool = True) -> Dict[str, Any]:
        """
        Constrói contexto completo do projeto
        
        Returns:
            Dicionário com contexto estruturado
        """
        context = {
            "project": {
                "name": self.project_path.name,
                "path": str(self.project_path),
                "timestamp": datetime.now().isoformat()
            },
            "structure": self._get_structure(),
            "components": self._get_components(),
            "config": self._get_config()
        }
        
        if include_code:
            context["code_summary"] = self._get_code_summary()
        
        return context
    
    def _get_structure(self) -> Dict:
        """Retorna estrutura de diretórios"""
        structure = {
            "has_app": (self.project_path / "app").exists(),
            "has_models": (self.project_path / "models").exists(),
            "has_controllers": (self.project_path / "controllers").exists(),
            "has_views": (self.project_path / "views").exists(),
            "has_pages": (self.project_path / "pages").exists(),
            "has_config": (self.project_path / "config.py").exists(),
        }
        
        # Conta arquivos
        for key, dir_name in [
            ("models_count", "models"),
            ("controllers_count", "controllers"),
            ("views_count", "views"),
            ("pages_count", "pages"),
        ]:
            dir_path = self.project_path / dir_name
            if dir_path.exists():
                structure[key] = len(list(dir_path.glob("*.py")))
            else:
                structure[key] = 0
        
        return structure
    
    def _get_components(self) -> Dict:
        """Lista componentes do projeto"""
        components = {
            "models": [],
            "controllers": [],
            "pages": []
        }
        
        # Models
        models_dir = self.project_path / "models"
        if models_dir.exists():
            components["models"] = [f.stem for f in models_dir.glob("*.py") if f.stem != "__init__"]
        
        # Controllers
        controllers_dir = self.project_path / "controllers"
        if controllers_dir.exists():
            components["controllers"] = [f.stem for f in controllers_dir.glob("*.py") if f.stem != "__init__"]
        
        # Pages
        pages_dir = self.project_path / "pages"
        if pages_dir.exists():
            components["pages"] = [f.stem for f in pages_dir.glob("*.py") if f.stem != "__init__"]
        
        return components
    
    def _get_config(self) -> Dict:
        """Extrai configurações do projeto"""
        config = {}
        
        # Tenta ler config.py
        config_file = self.project_path / "config.py"
        if config_file.exists():
            config["has_config_file"] = True
        
        # Tenta ler .flai/config.json
        flai_config = self.project_path / ".flai" / "config.json"
        if flai_config.exists():
            import json
            try:
                with open(flai_config) as f:
                    config["flai"] = json.load(f)
            except:
                pass
        
        return config
    
    def _get_code_summary(self) -> Dict:
        """Resumo do código (sem conteúdo completo)"""
        summary = {
            "total_lines": 0,
            "total_files": 0
        }
        
        for py_file in self.project_path.glob("**/*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                lines = len(py_file.read_text().splitlines())
                summary["total_lines"] += lines
                summary["total_files"] += 1
            except:
                continue
        
        return summary
    
    def to_prompt(self) -> str:
        """Converte contexto para string de prompt"""
        context = self.build(include_code=False)
        
        prompt = f"""
## Contexto do Projeto: {context['project']['name']}

### Estrutura
- App: {"✅" if context['structure']['has_app'] else "❌"}
- Models: {context['structure']['models_count']} arquivos
- Controllers: {context['structure']['controllers_count']} arquivos
- Views: {context['structure']['views_count']} arquivos
- Pages: {context['structure']['pages_count']} arquivos

### Componentes Detectados
- Models: {', '.join(context['components']['models']) if context['components']['models'] else 'Nenhum'}
- Controllers: {', '.join(context['components']['controllers']) if context['components']['controllers'] else 'Nenhum'}
- Pages: {', '.join(context['components']['pages']) if context['components']['pages'] else 'Nenhum'}

### Estatísticas
- Total de arquivos: {context['code_summary']['total_files']}
- Total de linhas: {context['code_summary']['total_lines']}
"""
        return prompt
