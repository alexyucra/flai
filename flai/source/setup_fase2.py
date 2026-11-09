#!/usr/bin/env python3
"""
FLAI - Script para criar automaticamente a FASE 2 (Agents, Intent, Generators, Executors)
Estrutura completa para o framework local de IA
"""

import os
from pathlib import Path

# Base path - ajustar conforme necessário
BASE_PATH = Path.cwd() / "flai"

def ensure_dir(path):
    """Cria diretório se não existir"""
    path = BASE_PATH / path
    path.mkdir(parents=True, exist_ok=True)
    print(f"📁 {path}")

def write_file(path, content):
    """Escreve conteúdo em arquivo"""
    full_path = BASE_PATH / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')
    print(f"📄 {full_path}")

# ============================================================================
# 1. AGENTS (core/agents/)
# ============================================================================

# __init__.py
write_file("core/agents/__init__.py", '''"""Agentes do FLAI - Processamento de intenções e orquestração"""
from .router_agent import RouterAgent
from .crud_agent import CRUDAgent
from .project_agent import ProjectAgent
from .form_agent import FormAgent
from .db_agent import DBAgent

__all__ = ["RouterAgent", "CRUDAgent", "ProjectAgent", "FormAgent", "DBAgent"]
''')

# router_agent.py
write_file("core/agents/router_agent.py", '''"""
Router Agent - Roteador de intenções para agentes especializados
"""
from typing import Dict, Any, Optional
from pathlib import Path
import sys

from flai.core.intent.parser import IntentParser
from flai.core.agents.crud_agent import CRUDAgent
from flai.core.agents.form_agent import FormAgent
from flai.core.agents.project_agent import ProjectAgent
from flai.core.agents.db_agent import DBAgent
from flai.cli.utils.ollama_manager import get_ollama_manager
from flai.cli.console.console import console

class RouterAgent:
    """Roteador que direciona comandos para o agente apropriado"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.intent_parser = IntentParser()
        self.crud_agent = CRUDAgent(project_path)
        self.form_agent = FormAgent(project_path)
        self.db_agent = DBAgent(project_path)
        self.project_agent = ProjectAgent(project_path)
        self.ollama = get_ollama_manager()
    
    def route(self, user_input: str) -> Dict[str, Any]:
        """
        Analisa o comando e direciona para o agente correto
        
        Args:
            user_input: Comando do usuário
            
        Returns:
            Dicionário com resultado da operação
        """
        # Parse da intenção
        intent_data = self.intent_parser.parse(user_input)
        intent = intent_data.get("intent", "unknown")
        entity = intent_data.get("entity")
        fields = intent_data.get("fields", [])
        
        console.print(f"[dim]🔍 Intenção detectada: {intent}[/dim]")
        
        # Roteamento baseado na intenção
        if intent == "create_crud":
            return self._handle_crud(entity, fields)
        
        elif intent == "create_form":
            return self._handle_form(entity, fields)
        
        elif intent == "create_page":
            return self._handle_page(entity)
        
        elif intent == "create_model":
            return self._handle_model(entity, fields)
        
        elif intent == "analyze":
            return self._handle_analyze(entity)
        
        elif intent == "where":
            return self._handle_search(entity or user_input)
        
        elif intent == "refactor":
            return self._handle_refactor(entity)
        
        elif intent == "help":
            return self._handle_help()
        
        elif intent == "exit":
            return {"type": "exit", "content": "Saindo..."}
        
        else:
            # Intenção não reconhecida - usar IA para interpretar
            return self._handle_unknown(user_input)
    
    def _handle_crud(self, entity: str, fields: list) -> Dict:
        """Cria CRUD completo"""
        if not entity:
            return {"type": "error", "content": "Informe o nome da entidade para o CRUD"}
        
        result = self.crud_agent.create(entity, fields)
        return {"type": "crud_result", "content": result}
    
    def _handle_form(self, form_name: str, fields: list) -> Dict:
        """Cria formulário"""
        if not form_name:
            return {"type": "error", "content": "Informe o nome do formulário"}
        
        result = self.form_agent.create(form_name, fields)
        return {"type": "form_result", "content": result}
    
    def _handle_page(self, page_name: str) -> Dict:
        """Cria página"""
        if not page_name:
            return {"type": "error", "content": "Informe o nome da página"}
        
        from flai.core.executors.fleting_executor import FletingExecutor
        executor = FletingExecutor(self.project_path)
        success = executor.create_page(page_name)
        
        return {
            "type": "page_result",
            "content": {
                "success": success,
                "page": page_name,
                "message": f"Página '{page_name}' criada" if success else "Erro ao criar página"
            }
        }
    
    def _handle_model(self, model_name: str, fields: list) -> Dict:
        """Cria model"""
        result = self.db_agent.create_migration(model_name)
        return {"type": "db_result", "content": result}
    
    def _handle_analyze(self, target: str) -> Dict:
        """Analisa componente do projeto"""
        if not target:
            structure = self.project_agent.get_structure()
            return {"type": "analysis", "content": structure}
        
        # Analisa arquivo específico
        file_path = self.project_agent.find(target)
        if file_path:
            content = file_path.read_text()[:2000]
            return {
                "type": "analysis",
                "content": f"## Arquivo: {target}\\n\\n```python\\n{content}\\n```"
            }
        
        return {"type": "analysis", "content": f"Arquivo '{target}' não encontrado"}
    
    def _handle_search(self, query: str) -> Dict:
        """Busca no projeto"""
        results = self.project_agent.search(query)
        if results:
            return {"type": "search_results", "content": results[:10]}
        return {"type": "search_results", "content": []}
    
    def _handle_refactor(self, target: str) -> Dict:
        """Refatora código"""
        # TODO: Implementar refatoração com IA
        return {
            "type": "refactor_result",
            "content": {
                "success": False,
                "message": "Refatoração ainda não implementada"
            }
        }
    
    def _handle_help(self) -> Dict:
        """Retorna ajuda"""
        help_text = """
## 📋 Comandos disponíveis

### CRUD
- `criar crud de produtos` - Cria CRUD completo
- `criar crud de usuarios com nome, email` - CRUD com campos

### Formulários
- `criar form login` - Cria formulário
- `criar formulário de contato com nome, email, mensagem`

### Páginas
- `criar página dashboard` - Cria nova página

### Análise
- `analise o controller user` - Analisa componente
- `onde está a autenticação?` - Busca no projeto

### Banco de Dados
- `criar model produto` - Cria model/migration

### Sistema
- `ajuda` - Mostra esta ajuda
- `sair` - Sai do programa
"""
        return {"type": "help", "content": help_text}
    
    def _handle_unknown(self, user_input: str) -> Dict:
        """Tenta interpretar com IA"""
        prompt = f"""
        O usuário digitou: "{user_input}"
        
        Isso NÃO é um comando reconhecido do sistema.
        Responda de forma amigável explicando que você não entendeu,
        e sugira usar o comando 'ajuda' para ver os comandos disponíveis.
        
        Seja breve, amigável e útil.
        """
        
        try:
            # Pega modelo da config
            config_file = self.project_path / ".flai" / "config.json"
            model = "llama3.2:3b"
            if config_file.exists():
                import json
                with open(config_file) as f:
                    config = json.load(f)
                    model = config.get("model", model)
            
            response = self.ollama.run_model(model, prompt)
            return {"type": "chat", "content": response}
        except Exception:
            return {
                "type": "unknown",
                "content": f"Não entendi: '{user_input}'. Digite 'ajuda' para ver os comandos disponíveis."
            }
    
    def get_context_prompt(self) -> str:
        """Retorna contexto para o sistema"""
        return self.project_agent.get_context_prompt()
''')

# crud_agent.py
write_file("core/agents/crud_agent.py", '''"""
CRUD Agent - Orquestrador de criação de CRUD completo
"""
from typing import Dict, List, Optional
from pathlib import Path
import sys

from flai.core.executors.fleting_executor import FletingExecutor
from flai.core.generators.crud_generator import CRUDGenerator
from flai.cli.console.console import console

class CRUDAgent:
    """Agente responsável por criar CRUDs completos para entidades"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path)
        self.generator = CRUDGenerator(self.project_path)
    
    def create(self, entity: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Cria CRUD completo para uma entidade
        
        Args:
            entity: Nome da entidade (ex: "produto", "usuario")
            fields: Lista de campos (ex: ["nome", "preco", "email"])
        
        Returns:
            Dict com resultado da operação
        """
        console.print(f"[bold cyan]🚀 Criando CRUD para: {entity}[/bold cyan]")
        
        result = {
            "success": False,
            "entity": entity,
            "fields": fields or [],
            "steps": [],
            "errors": []
        }
        
        # Step 1: Criar página
        console.print("[dim]📄 Criando página...[/dim]")
        page_result = self._create_page(entity)
        result["steps"].append(page_result)
        
        if not page_result["success"]:
            result["errors"].append("Falha ao criar página")
            console.print("[red]❌ Falha ao criar página[/red]")
            return result
        console.print("[green]✅ Página criada[/green]")
        
        # Step 2: Criar model
        console.print("[dim]🗄️ Criando model...[/dim]")
        model_result = self._create_model(entity, fields)
        result["steps"].append(model_result)
        
        if not model_result["success"]:
            result["errors"].append("Falha ao criar model")
            console.print("[red]❌ Falha ao criar model[/red]")
            return result
        console.print("[green]✅ Model criado[/green]")
        
        # Step 3: Gerar controller
        console.print("[dim]🎮 Gerando controller...[/dim]")
        controller_result = self._generate_controller(entity, fields)
        result["steps"].append(controller_result)
        if controller_result["success"]:
            console.print("[green]✅ Controller gerado[/green]")
        else:
            console.print("[yellow]⚠️ Controller pode precisar de ajustes[/yellow]")
        
        # Step 4: Gerar formulário
        console.print("[dim]📝 Gerando formulário...[/dim]")
        form_result = self._generate_form(entity, fields)
        result["steps"].append(form_result)
        if form_result["success"]:
            console.print("[green]✅ Formulário gerado[/green]")
        else:
            console.print("[yellow]⚠️ Formulário pode precisar de ajustes[/yellow]")
        
        # Step 5: Executar migrations
        console.print("[dim]🔄 Executando migrations...[/dim]")
        migration_result = self._run_migrations()
        result["steps"].append(migration_result)
        if migration_result["success"]:
            console.print("[green]✅ Migrations executadas[/green]")
        else:
            console.print("[yellow]⚠️ Execute 'fleting db migrate' manualmente[/yellow]")
        
        result["success"] = len(result["errors"]) == 0
        
        if result["success"]:
            console.print(f"[bold green]🎉 CRUD '{entity}' criado com sucesso![/bold green]")
        else:
            console.print(f"[bold red]❌ Erro ao criar CRUD: {result['errors'][0]}[/bold red]")
        
        return result
    
    def _create_page(self, entity: str) -> Dict:
        """Cria página usando Fleting"""
        success = self.executor.create_page(entity)
        return {
            "step": "create_page",
            "entity": entity,
            "success": success,
            "message": f"Página '{entity}' criada" if success else "Erro ao criar página"
        }
    
    def _create_model(self, entity: str, fields: Optional[List[str]]) -> Dict:
        """Cria model - tenta gerador customizado primeiro"""
        if fields:
            # Usa gerador customizado com campos
            return self.generator.generate_model(entity, fields)
        else:
            # Fallback para comando padrão
            success = self.executor.create_model(entity)
            return {
                "step": "create_model",
                "entity": entity,
                "success": success,
                "message": f"Model '{entity}' criado" if success else "Erro ao criar model"
            }
    
    def _generate_controller(self, entity: str, fields: Optional[List[str]]) -> Dict:
        """Gera controller customizado"""
        return self.generator.generate_controller(entity, fields or [])
    
    def _generate_form(self, entity: str, fields: Optional[List[str]]) -> Dict:
        """Gera formulário customizado"""
        return self.generator.generate_form(entity, fields or [])
    
    def _run_migrations(self) -> Dict:
        """Executa migrations"""
        success = self.executor.run_migrations()
        return {
            "step": "run_migrations",
            "entity": None,
            "success": success,
            "message": "Migrations executadas" if success else "Erro nas migrations"
        }
    
    def analyze(self, entity: str, entity_type: str = "controller") -> Dict:
        """Analisa um componente existente"""
        console.print(f"[cyan]🔍 Analisando {entity_type}: {entity}[/cyan]")
        
        # Busca arquivo
        search_pattern = f"**/{entity}.py"
        if entity_type == "controller":
            search_pattern = f"**/controllers/{entity}.py"
        elif entity_type == "model":
            search_pattern = f"**/models/{entity}.py"
        
        files = list(self.project_path.glob(search_pattern))
        
        if not files:
            return {
                "success": False,
                "message": f"{entity_type} '{entity}' não encontrado"
            }
        
        file_path = files[0]
        content = file_path.read_text()
        
        return {
            "success": True,
            "entity": entity,
            "type": entity_type,
            "path": str(file_path),
            "lines": len(content.splitlines()),
            "preview": content[:1000] + ("..." if len(content) > 1000 else "")
        }
''')

# project_agent.py
write_file("core/agents/project_agent.py", '''"""
Project Agent - Contexto e análise do projeto Fleting
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

from flai.cli.utils.scanner import scan_project
from flai.cli.utils.context import build_context_map
from flai.cli.utils.checklist import create_checklist

class ProjectAgent:
    """Agente responsável por contexto e análise do projeto"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self._structure = None
        self._scan_result = None
    
    def get_structure(self) -> Dict[str, Any]:
        """Retorna estrutura completa do projeto"""
        if self._structure is None:
            self._scan_result = scan_project(self.project_path)
            self._structure = self._scan_result
        return self._structure
    
    def get_context_prompt(self) -> str:
        """Gera prompt com contexto do projeto"""
        structure = self.get_structure()
        
        # Informações básicas
        context = f"""
## 📁 Informações do Projeto Fleting
- **Nome:** {self.project_path.name}
- **Caminho:** {self.project_path}
- **Pasta app:** {'✅ Encontrada' if structure.get('app') else '❌ Não encontrada'}
- **Arquivos de configuração:** {len(structure.get('configs', []))}
- **Arquivos na raiz:** {len(structure.get('root_files', []))}
"""
        
        # Adiciona mapa de contexto se disponível
        if self._scan_result:
            context += "\\n" + build_context_map(self._scan_result)
        
        return context
    
    def find(self, name: str) -> Optional[Path]:
        """Busca arquivo por nome no projeto"""
        # Busca em todas as pastas
        for ext in ["", ".py", ".yaml", ".yml", ".json", ".md"]:
            pattern = f"**/{name}{ext}"
            for file in self.project_path.glob(pattern):
                return file
            pattern = f"**/{name}/*.py"
            for file in self.project_path.glob(pattern):
                return file
        return None
    
    def search(self, pattern: str) -> List[Dict[str, Any]]:
        """
        Busca conteúdo nos arquivos do projeto
        
        Args:
            pattern: Padrão de busca (regex)
        
        Returns:
            Lista de resultados com arquivo, linha e conteúdo
        """
        import re
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        for py_file in self.project_path.glob("**/*.py"):
            # Pular diretórios ignorados
            if any(ignored in str(py_file) for ignored in ["__pycache__", ".venv", "venv"]):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                for line_num, line in enumerate(content.split('\\n'), 1):
                    if regex.search(line):
                        results.append({
                            "file": str(py_file.relative_to(self.project_path)),
                            "line": line_num,
                            "content": line.strip()[:200]
                        })
                        if len(results) >= 50:  # Limite de resultados
                            break
            except Exception:
                continue
        
        return results
    
    def get_checklist(self) -> Path:
        """Cria ou retorna checklist do projeto"""
        return create_checklist(self.project_path)
    
    def get_file_summary(self, file_path: Path, max_lines: int = 50) -> str:
        """Retorna resumo do conteúdo de um arquivo"""
        if not file_path.exists():
            return "Arquivo não encontrado"
        
        try:
            lines = file_path.read_text(encoding='utf-8').splitlines()
            total = len(lines)
            preview = lines[:max_lines]
            
            summary = f"## {file_path.name}\\n"
            summary += f"Total de linhas: {total}\\n\\n"
            summary += "```python\\n"
            summary += "\\n".join(preview)
            if total > max_lines:
                summary += f"\\n... (+{total - max_lines} linhas)"
            summary += "\\n```"
            
            return summary
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"
    
    def get_project_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do projeto"""
        structure = self.get_structure()
        
        # Conta arquivos Python
        py_count = 0
        for root, dirs, files in os.walk(self.project_path):
            if any(ignored in root for ignored in ["__pycache__", ".venv", "venv"]):
                continue
            py_count += len([f for f in files if f.endswith('.py')])
        
        return {
            "name": self.project_path.name,
            "path": str(self.project_path),
            "python_files": py_count,
            "has_app": bool(structure.get('app')),
            "configs": len(structure.get('configs', [])),
            "root_files": len(structure.get('root_files', []))
        }
''')

# form_agent.py
write_file("core/agents/form_agent.py", '''"""
Form Agent - Especialista em criação de formulários Flet
"""
from pathlib import Path
from typing import Dict, List, Optional
import sys

from flai.core.generators.form_generator import FormGenerator
from flai.cli.console.console import console

class FormAgent:
    """Agente especializado em formulários Flet"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.generator = FormGenerator(project_path)
    
    def create(self, form_name: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Cria um formulário Flet
        
        Args:
            form_name: Nome do formulário
            fields: Lista de campos (ex: ["nome", "email", "senha"])
        
        Returns:
            Dict com resultado da operação
        """
        console.print(f"[bold cyan]📝 Criando formulário: {form_name}[/bold cyan]")
        
        if fields:
            console.print(f"[dim]Campos: {', '.join(fields)}[/dim]")
        
        success = self.generator.generate(form_name, fields or [])
        
        if success:
            console.print(f"[green]✅ Formulário '{form_name}' criado com sucesso![/green]")
        else:
            console.print(f"[red]❌ Erro ao criar formulário '{form_name}'[/red]")
        
        return {
            "success": success,
            "form": form_name,
            "fields": fields or [],
            "message": f"Formulário '{form_name}' criado" if success else f"Erro ao criar formulário '{form_name}'"
        }
    
    def validate(self, form_name: str) -> Dict:
        """Valida um formulário existente"""
        form_path = self.project_path / "forms" / f"{form_name}.py"
        
        if not form_path.exists():
            return {
                "success": False,
                "message": f"Formulário '{form_name}' não encontrado"
            }
        
        content = form_path.read_text()
        
        # Validações simples
        issues = []
        if "ft.TextField" not in content:
            issues.append("Nenhum campo TextField encontrado")
        if "on_click" not in content and "on_submit" not in content:
            issues.append("Nenhum handler de evento encontrado")
        
        return {
            "success": len(issues) == 0,
            "form": form_name,
            "path": str(form_path),
            "issues": issues,
            "message": "Formulário válido" if not issues else f"Problemas encontrados: {', '.join(issues)}"
        }
''')

# db_agent.py
write_file("core/agents/db_agent.py", '''"""
DB Agent - Especialista em banco de dados e migrations
"""
from pathlib import Path
from typing import Dict, List, Optional
import sys

from flai.core.executors.fleting_executor import FletingExecutor
from flai.core.generators.model_generator import ModelGenerator
from flai.cli.console.console import console

class DBAgent:
    """Agente especializado em operações de banco de dados"""
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path)
        self.generator = ModelGenerator(project_path)
    
    def create_migration(self, model_name: str, fields: Optional[List[str]] = None) -> Dict:
        """
        Cria uma migration/model
        
        Args:
            model_name: Nome do model
            fields: Lista de campos
        
        Returns:
            Dict com resultado
        """
        console.print(f"[bold cyan]🗄️ Criando model: {model_name}[/bold cyan]")
        
        if fields:
            # Usa gerador customizado
            result = self.generator.generate(model_name, fields)
            success = result.get("success", False)
        else:
            # Usa comando padrão
            success = self.executor.create_model(model_name)
        
        if success:
            console.print(f"[green]✅ Model '{model_name}' criado[/green]")
            # Executa migration
            self.executor.run_migrations()
        else:
            console.print(f"[red]❌ Erro ao criar model '{model_name}'[/red]")
        
        return {
            "success": success,
            "migration": model_name,
            "fields": fields or [],
            "message": f"Model '{model_name}' criado" if success else f"Erro ao criar model '{model_name}'"
        }
    
    def migrate(self) -> Dict:
        """Executa todas as migrations pendentes"""
        console.print("[cyan]🔄 Executando migrations...[/cyan]")
        success = self.executor.run_migrations()
        
        if success:
            console.print("[green]✅ Migrations executadas com sucesso[/green]")
        else:
            console.print("[red]❌ Erro ao executar migrations[/red]")
        
        return {
            "success": success,
            "message": "Migrations executadas com sucesso" if success else "Erro ao executar migrations"
        }
    
    def list_models(self) -> List[str]:
        """Lista models disponíveis"""
        models_dir = self.project_path / "models"
        if not models_dir.exists():
            return []
        
        return [f.stem for f in models_dir.glob("*.py") if f.stem != "__init__"]
    
    def get_model_schema(self, model_name: str) -> Optional[Dict]:
        """Retorna schema de um model"""
        model_path = self.project_path / "models" / f"{model_name}.py"
        
        if not model_path.exists():
            return None
        
        content = model_path.read_text()
        
        # Extrai campos simples
        import re
        fields = []
        field_pattern = r'(\\w+)\\s*=\\s*models\\.(\\w+)Field'
        
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            field_type = match.group(2)
            fields.append({"name": field_name, "type": field_type})
        
        return {
            "name": model_name,
            "fields": fields,
            "has_timestamps": "created_at" in content and "updated_at" in content
        }
''')

# ============================================================================
# 2. INTENT (core/intent/)
# ============================================================================

write_file("core/intent/__init__.py", '''"""Módulo de reconhecimento de intenções"""
from .patterns import IntentPatterns
from .parser import IntentParser
from .classifier import IntentClassifier

__all__ = ["IntentPatterns", "IntentParser", "IntentClassifier"]
''')

write_file("core/intent/patterns.py", '''"""
Intent Patterns - Definição de padrões regex para reconhecimento de intenções
"""
import re
from typing import Dict, List, Tuple, Optional

class IntentPatterns:
    """Padrões para reconhecimento de intenções do usuário"""
    
    # Padrões organizados por intenção
    PATTERNS: Dict[str, List[str]] = {
        "create_crud": [
            r"cri(?:a|e)r?\\s+crud\\s+(?:de\\s+)?(\\w+)",
            r"crie\\s+crud\\s+(?:de\\s+)?(\\w+)",
            r"ger(?:a|e)r?\\s+crud\\s+(?:de\\s+)?(\\w+)",
            r"make\\s+crud\\s+(?:for\\s+)?(\\w+)",
            r"create\\s+crud\\s+(?:for\\s+)?(\\w+)",
            r"novo\\s+crud\\s+(?:de\\s+)?(\\w+)",
        ],
        "create_form": [
            r"cri(?:a|e)r?\\s+form(?:ul[áa]rio)?\\s+(?:de\\s+)?(\\w+)",
            r"crie\\s+form(?:ul[áa]rio)?\\s+(?:de\\s+)?(\\w+)",
            r"ger(?:a|e)r?\\s+form(?:ul[áa]rio)?\\s+(?:de\\s+)?(\\w+)",
            r"create\\s+form\\s+(?:for\\s+)?(\\w+)",
            r"novo\\s+form(?:ul[áa]rio)?\\s+(?:de\\s+)?(\\w+)",
        ],
        "create_page": [
            r"cri(?:a|e)r?\\s+p[aá]gina\\s+(?:de\\s+)?(\\w+)",
            r"crie\\s+p[aá]gina\\s+(?:de\\s+)?(\\w+)",
            r"create\\s+page\\s+(?:for\\s+)?(\\w+)",
            r"nova\\s+p[aá]gina\\s+(?:de\\s+)?(\\w+)",
        ],
        "create_model": [
            r"cri(?:a|e)r?\\s+model(?:o)?\\s+(?:de\\s+)?(\\w+)",
            r"crie\\s+model(?:o)?\\s+(?:de\\s+)?(\\w+)",
            r"create\\s+model\\s+(?:for\\s+)?(\\w+)",
            r"novo\\s+model(?:o)?\\s+(?:de\\s+)?(\\w+)",
        ],
        "analyze": [
            r"analis(?:a|e)\\s+(?:o\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"analise\\s+(?:o\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"analyze\\s+(?:the\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"mostre\\s+(?:o\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"show\\s+(?:the\\s+)?(controller|model|page|view)\\s+(\\w+)",
        ],
        "where": [
            r"onde\\s+est[aá]\\s+(.+)\\??",
            r"cad(?:a|o)\\s+(.+)",
            r"onde\\s+f(?:i|ic)a\\s+(.+)\\??",
            r"where\\s+is\\s+(.+)\\??",
            r"find\\s+(.+)",
            r"buscar\\s+(.+)",
            r"procurar\\s+(.+)",
        ],
        "refactor": [
            r"refator(?:a|e)\\s+(?:o\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"refactor\\s+(?:the\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"melhor(?:a|e)\\s+(?:o\\s+)?(controller|model|page|view)\\s+(\\w+)",
            r"improve\\s+(?:the\\s+)?(controller|model|page|view)\\s+(\\w+)",
        ],
        "help": [
            r"ajuda",
            r"help",
            r"\\?",
            r"comandos",
            r"commands",
            r"o que (?:você|vc) (?:faz|sabe fazer)",
        ],
        "exit": [
            r"sair",
            r"exit",
            r"quit",
            r"q",
            r"sair do programa",
        ],
    }
    
    # Padrões para extração de campos
    FIELD_PATTERNS: List[str] = [
        r"com\\s+os\\s+campos?\\s*:\\s*(.+)",
        r"com\\s+os\\s+seguintes\\s+campos?\\s*:\\s*(.+)",
        r"campos?\\s*:\\s*(.+)",
        r"fields?\\s*:\\s*(.+)",
        r"com\\s+(.+)",
        r"contendo\\s+(.+)",
    ]
    
    @classmethod
    def match_intent(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retorna (intent, entity) baseado no texto
        
        Example:
            match_intent("criar crud de produtos") -> ("create_crud", "produtos")
        """
        text_lower = text.lower().strip()
        
        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    # O último grupo é a entidade
                    entity = match.group(1) if match.groups() else None
                    # Para analyze, o primeiro grupo é tipo, segundo é nome
                    if intent == "analyze" and match.groups() and len(match.groups()) >= 2:
                        entity = f"{match.group(1)} {match.group(2)}"
                    return intent, entity
        
        return None, None
    
    @classmethod
    def extract_fields(cls, text: str) -> List[str]:
        """Extrai lista de campos da descrição"""
        text_lower = text.lower()
        
        for pattern in cls.FIELD_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                fields_str = match.group(1)
                # Separa por vírgula, "e", "e também"
                separators = r'[ ,]+\\s*[e&]\\s*|[ ,]+|\\s+e\\s+'
                fields = re.split(separators, fields_str)
                fields = [f.strip() for f in fields if f.strip() and len(f.strip()) > 0]
                # Remove palavras comuns que podem ter sido capturadas
                stop_words = {"com", "de", "os", "as", "do", "da", "dos", "das"}
                fields = [f for f in fields if f not in stop_words and len(f) > 1]
                return fields[:10]  # Limita a 10 campos
        
        return []
    
    @classmethod
    def get_all_intents(cls) -> List[str]:
        """Retorna todas as intenções disponíveis"""
        return list(cls.PATTERNS.keys())
    
    @classmethod
    def add_pattern(cls, intent: str, pattern: str) -> None:
        """Adiciona um novo padrão para uma intenção"""
        if intent not in cls.PATTERNS:
            cls.PATTERNS[intent] = []
        cls.PATTERNS[intent].append(pattern)
''')

write_file("core/intent/parser.py", '''"""
Intent Parser - Transforma texto em intenção estruturada
"""
from typing import Dict, Optional, List, Any
from .patterns import IntentPatterns

class IntentParser:
    """Parser de intenções do usuário"""
    
    def __init__(self):
        self.patterns = IntentPatterns()
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        Parseia entrada do usuário e retorna intenção estruturada
        
        Args:
            user_input: Texto do usuário
        
        Returns:
            Dict com intent, entity, fields, confidence, original
        """
        intent, entity = self.patterns.match_intent(user_input)
        fields = self.patterns.extract_fields(user_input)
        
        result = {
            "original": user_input,
            "intent": intent,
            "entity": entity,
            "fields": fields,
            "confidence": 0.0
        }
        
        # Calcula confiança baseada em match e campos
        if intent:
            base_confidence = 0.7
            if fields:
                base_confidence = min(0.95, base_confidence + 0.15)
            if entity and len(entity) > 2:
                base_confidence = min(0.95, base_confidence + 0.05)
            result["confidence"] = base_confidence
        else:
            result["confidence"] = 0.0
        
        return result
    
    def is_command(self, user_input: str) -> bool:
        """Verifica se é um comando reconhecido"""
        intent, _ = self.patterns.match_intent(user_input)
        return intent is not None
    
    def get_help_text(self) -> str:
        """Retorna texto de ajuda formatado"""
        help_text = """
## 📋 Comandos disponíveis

### 🚀 CRUD
| Comando | Exemplo |
|---------|---------|
| Criar CRUD | `criar crud de produtos` |
| CRUD com campos | `criar crud de usuarios com nome, email` |

### 📝 Formulários
| Comando | Exemplo |
|---------|---------|
| Criar formulário | `criar form login` |
| Form com campos | `criar formulário de contato com nome, email, mensagem` |

### 📄 Páginas
| Comando | Exemplo |
|---------|---------|
| Criar página | `criar página dashboard` |

### 🔍 Análise
| Comando | Exemplo |
|---------|---------|
| Analisar componente | `analise o controller user` |
| Buscar no projeto | `onde está a autenticação?` |

### 🗄️ Banco de Dados
| Comando | Exemplo |
|---------|---------|
| Criar model | `criar model produto` |
| Executar migrations | `flai db migrate` |

### 🛠️ Sistema
| Comando | Exemplo |
|---------|---------|
| Ajuda | `ajuda`, `help`, `?` |
| Sair | `sair`, `exit`, `q` |

---
💡 **Dica:** Você pode especificar campos usando "com" ou "com os campos:"
"""
        return help_text
''')

write_file("core/intent/classifier.py", '''"""
Intent Classifier - Classificador de intenções (puro, sem LangChain)
"""
import re
from typing import Dict, List, Tuple
from .patterns import IntentPatterns

class IntentClassifier:
    """Classificador simples de intenções baseado em padrões e keywords"""
    
    def __init__(self):
        self.patterns = IntentPatterns()
        
        # Keywords por intenção para fallback
        self.keywords = {
            "create_crud": ["crud", "criar crud", "make crud"],
            "create_form": ["form", "formulário", "fomulario"],
            "create_page": ["página", "pagina", "pag", "page"],
            "analyze": ["analisar", "analise", "analyze", "mostrar", "show", "ver"],
            "where": ["onde", "where", "cadê", "cade", "buscar", "find"],
            "refactor": ["refatorar", "refactor", "melhorar", "improve"],
            "help": ["ajuda", "help", "comandos", "commands", "ajudar"],
            "exit": ["sair", "exit", "quit", "fechar"]
        }
    
    def classify(self, text: str) -> Dict:
        """
        Classifica o texto e retorna intenção com metadados
        
        Args:
            text: Texto do usuário
        
        Returns:
            Dict com intenção classificada
        """
        # Primeiro tenta padrões regex
        intent, entity = self.patterns.match_intent(text)
        fields = self.patterns.extract_fields(text)
        
        if intent:
            return {
                "intent": intent,
                "entity": entity,
                "fields": fields,
                "text": text,
                "method": "regex"
            }
        
        # Fallback: busca por keywords
        text_lower = text.lower()
        best_intent = "unknown"
        best_score = 0
        
        for intent_name, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    score = len(keyword) / len(text_lower) if text_lower else 0
                    if score > best_score:
                        best_score = score
                        best_intent = intent_name
        
        # Extrai possível entidade (palavra após keywords)
        extracted_entity = None
        if best_intent != "unknown":
            words = text_lower.split()
            for i, word in enumerate(words):
                if word in ["de", "do", "da", "dos", "das"] and i + 1 < len(words):
                    extracted_entity = words[i + 1]
                    break
                if i > 0 and words[i-1] in ["crud", "form", "page", "página", "model"]:
                    extracted_entity = word
                    break
        
        return {
            "intent": best_intent,
            "entity": extracted_entity,
            "fields": fields,
            "text": text,
            "method": "keyword" if best_intent != "unknown" else "none",
            "confidence": best_score
        }
    
    def suggest_intents(self, text: str, limit: int = 3) -> List[Tuple[str, float]]:
        """Sugere possíveis intenções baseadas em similaridade lexical"""
        suggestions = []
        text_lower = text.lower()
        
        for intent, patterns in self.patterns.PATTERNS.items():
            max_score = 0.0
            for pattern in patterns:
                # Simplificação: conta palavras em comum
                pattern_words = set(re.findall(r'\\w+', pattern.lower()))
                text_words = set(re.findall(r'\\w+', text_lower))
                
                if pattern_words:
                    overlap = len(pattern_words & text_words)
                    score = overlap / len(pattern_words)
                    max_score = max(max_score, score)
            
            # Também considera keywords
            for keyword in self.keywords.get(intent, []):
                if keyword in text_lower:
                    score = len(keyword) / len(text_lower) if text_lower else 0
                    max_score = max(max_score, score)
            
            if max_score > 0.1:
                suggestions.append((intent, max_score))
        
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:limit]
    
    def get_intent_description(self, intent: str) -> str:
        """Retorna descrição de uma intenção"""
        descriptions = {
            "create_crud": "Cria um CRUD completo para uma entidade",
            "create_form": "Cria um formulário Flet",
            "create_page": "Cria uma nova página",
            "analyze": "Analisa um componente do projeto",
            "where": "Busca informações no código do projeto",
            "refactor": "Sugere melhorias para o código",
            "help": "Mostra ajuda com comandos",
            "exit": "Sai do programa",
            "unknown": "Comando não reconhecido"
        }
        return descriptions.get(intent, "Comando desconhecido")
''')

# ============================================================================
# 3. GENERATORS (core/generators/)
# ============================================================================

write_file("core/generators/__init__.py", '''"""Geradores de código para Fleting"""
from .crud_generator import CRUDGenerator
from .form_generator import FormGenerator
from .view_generator import ViewGenerator
from .model_generator import ModelGenerator
from .controller_generator import ControllerGenerator

__all__ = ["CRUDGenerator", "FormGenerator", "ViewGenerator", "ModelGenerator", "ControllerGenerator"]
''')

# crud_generator.py
write_file("core/generators/crud_generator.py", '''
"""
CRUD Generator - Gera código CRUD completo com templates
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class CRUDGenerator:
    """Gerador de código CRUD para Fleting"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def generate_model(self, entity: str, fields: List[str]) -> Dict:
        """Gera arquivo de model"""
        entity_cap = entity.capitalize()
        
        # Gera campos do model
        fields_code = ""
        for field in fields:
            field_name = field.lower().replace(" ", "_")
            fields_code += f'    {field_name} = fields.StringField(max_length=255, null=False)\\n'
        
        # Conteúdo sem f-string aninhada
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Model {entity_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('from fleting.db import Model')
        content_lines.append('import fleting.db.fields as fields')
        content_lines.append('')
        content_lines.append(f'class {entity_cap}(Model):')
        content_lines.append(f'    """Model para {entity}"""')
        content_lines.append('')
        content_lines.append(f'    __tablename__ = "{entity}s"')
        content_lines.append('')
        content_lines.append('    id = fields.IntegerField(primary_key=True)')
        if fields_code:
            content_lines.append(fields_code.rstrip())
        content_lines.append('    created_at = fields.DateTimeField(auto_now_add=True)')
        content_lines.append('    updated_at = fields.DateTimeField(auto_now=True)')
        content_lines.append('')
        content_lines.append('    def __str__(self):')
        content_lines.append('        return f"{self.id} - {self.__class__.__name__}"')
        content_lines.append('')
        content_lines.append('    def to_dict(self) -> dict:')
        content_lines.append('        """Converte para dicionário"""')
        content_lines.append('        return {')
        content_lines.append('            "id": self.id,')
        content_lines.append('            "created_at": self.created_at.isoformat() if self.created_at else None,')
        content_lines.append('            "updated_at": self.updated_at.isoformat() if self.updated_at else None,')
        content_lines.append('        }')
        
        content = "\\n".join(content_lines)
        
        model_path = self.project_path / "models" / f"{entity}.py"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(content)
        
        return {"success": True, "step": "create_model", "path": str(model_path), "message": f"Model {entity} criado"}
    
    def generate_controller(self, entity: str, fields: List[str]) -> Dict:
        """Gera arquivo de controller"""
        entity_cap = entity.capitalize()
        entity_lower = entity.lower()
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Controller {entity_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('from fleting.controller import Controller')
        content_lines.append('from fleting.response import Response')
        content_lines.append(f'from ..models.{entity_lower} import {entity_cap}')
        content_lines.append('')
        content_lines.append(f'class {entity_cap}Controller(Controller):')
        content_lines.append(f'    """Controller para CRUD de {entity_lower}"""')
        content_lines.append('')
        content_lines.append('    def index(self, request):')
        content_lines.append(f'        """Lista todos os {entity_lower}s"""')
        content_lines.append(f'        items = {entity_cap}.all()')
        content_lines.append('        return Response.json({')
        content_lines.append('            "data": [item.to_dict() for item in items],')
        content_lines.append('            "count": len(items)')
        content_lines.append('        })')
        content_lines.append('')
        content_lines.append('    def show(self, request, id):')
        content_lines.append(f'        """Mostra um {entity_lower} específico"""')
        content_lines.append(f'        item = {entity_cap}.find(id)')
        content_lines.append('        if not item:')
        content_lines.append('            return Response.json({"error": "Not found"}, status=404)')
        content_lines.append('        return Response.json(item.to_dict())')
        content_lines.append('')
        content_lines.append('    def create(self, request):')
        content_lines.append(f'        """Cria um novo {entity_lower}"""')
        content_lines.append('        data = request.json')
        content_lines.append(f'        item = {entity_cap}.create(data)')
        content_lines.append('        return Response.json(item.to_dict(), status=201)')
        content_lines.append('')
        content_lines.append('    def update(self, request, id):')
        content_lines.append(f'        """Atualiza um {entity_lower}"""')
        content_lines.append(f'        item = {entity_cap}.find(id)')
        content_lines.append('        if not item:')
        content_lines.append('            return Response.json({"error": "Not found"}, status=404)')
        content_lines.append('        data = request.json')
        content_lines.append('        item.update(data)')
        content_lines.append('        return Response.json(item.to_dict())')
        content_lines.append('')
        content_lines.append('    def delete(self, request, id):')
        content_lines.append(f'        """Remove um {entity_lower}"""')
        content_lines.append(f'        item = {entity_cap}.find(id)')
        content_lines.append('        if not item:')
        content_lines.append('            return Response.json({"error": "Not found"}, status=404)')
        content_lines.append('        item.delete()')
        content_lines.append('        return Response.json({"message": "Deleted"})')
        
        content = "\\n".join(content_lines)
        
        controller_path = self.project_path / "controllers" / f"{entity}_controller.py"
        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.write_text(content)
        
        return {"success": True, "step": "generate_controller", "path": str(controller_path), "message": f"Controller {entity} gerado"}
    
    def generate_form(self, entity: str, fields: List[str]) -> Dict:
        """Gera arquivo de formulário"""
        entity_cap = entity.capitalize()
        
        # Gera campos do formulário
        fields_code = ""
        for field in fields:
            field_name = field.lower().replace(" ", "_")
            fields_code += f'        self.{field_name}_field = ft.TextField(label="{field.capitalize()}", value=self.initial_data.get("{field_name}", ""))\\n'
        
        # Construir lista de campos
        field_list = ",\\n".join([f'            self.{f.lower().replace(" ", "_")}_field' for f in fields])
        field_data = ",\\n".join([f'                "{f.lower().replace(" ", "_")}": self.{f.lower().replace(" ", "_")}_field.value' for f in fields])
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Form {entity_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('import flet as ft')
        content_lines.append('')
        content_lines.append(f'class {entity_cap}Form(ft.UserControl):')
        content_lines.append(f'    """Formulário para {entity}"""')
        content_lines.append('')
        content_lines.append('    def __init__(self, on_submit=None, initial_data=None):')
        content_lines.append('        super().__init__()')
        content_lines.append('        self.on_submit = on_submit')
        content_lines.append('        self.initial_data = initial_data or {}')
        content_lines.append('')
        content_lines.append('    def build(self):')
        if fields_code:
            content_lines.append(fields_code.rstrip())
        content_lines.append('        self.submit_button = ft.ElevatedButton("Salvar", on_click=self._on_submit)')
        content_lines.append('')
        content_lines.append('        return ft.Column([')
        content_lines.append(field_list)
        content_lines.append('            self.submit_button')
        content_lines.append('        ], spacing=10)')
        content_lines.append('')
        content_lines.append('    def _on_submit(self, e):')
        content_lines.append('        if self.on_submit:')
        content_lines.append('            data = {')
        content_lines.append(field_data)
        content_lines.append('            }')
        content_lines.append('            self.on_submit(data)')
        content_lines.append('')
        content_lines.append('    def get_data(self):')
        content_lines.append('        """Retorna os dados do formulário"""')
        content_lines.append('        return {')
        content_lines.append(field_data)
        content_lines.append('        }')
        
        content = "\\n".join(content_lines)
        
        form_path = self.project_path / "forms" / f"{entity}_form.py"
        form_path.parent.mkdir(parents=True, exist_ok=True)
        form_path.write_text(content)
        
        return {"success": True, "step": "generate_form", "path": str(form_path), "message": f"Formulário {entity} gerado"}
    
    def generate_view(self, entity: str, fields: List[str]) -> Dict:
        """Gera arquivo de view"""
        entity_cap = entity.capitalize()
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'View {entity_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('import flet as ft')
        content_lines.append(f'from ..controllers.{entity}_controller import {entity_cap}Controller')
        content_lines.append('')
        content_lines.append(f'def {entity}_list_view(page: ft.Page):')
        content_lines.append(f'    """View para lista de {entity}s"""')
        content_lines.append(f'    controller = {entity_cap}Controller()')
        content_lines.append('')
        content_lines.append('    def load_items():')
        content_lines.append('        pass')
        content_lines.append('')
        content_lines.append('    def create_new(e):')
        content_lines.append(f'        page.go("/{entity}/new")')
        content_lines.append('')
        content_lines.append('    title = ft.Text(f"Lista de {entity_cap}s", size=30, weight="bold")')
        content_lines.append('    add_button = ft.ElevatedButton("Novo", on_click=create_new)')
        content_lines.append('')
        content_lines.append('    return ft.Column([')
        content_lines.append('        ft.Row([title, add_button], alignment="spaceBetween"),')
        content_lines.append('        ft.Divider(),')
        content_lines.append('        ft.Container(height=20),')
        content_lines.append('        ft.ListView(controls=[], height=400),')
        content_lines.append('    ])')
        content_lines.append('')
        content_lines.append(f'def {entity}_form_view(page: ft.Page, item_id=None):')
        content_lines.append(f'    """View para formulário de {entity}"""')
        content_lines.append(f'    from ..forms.{entity}_form import {entity_cap}Form')
        content_lines.append('')
        content_lines.append('    def on_submit(data):')
        content_lines.append(f'        page.go("/{entity}")')
        content_lines.append('')
        content_lines.append('    form = {entity_cap}Form(on_submit=on_submit)')
        content_lines.append('')
        content_lines.append('    return ft.Column([')
        content_lines.append('        ft.Text("Novo {entity_cap}" if not item_id else "Editar {entity_cap}", size=30, weight="bold"),')
        content_lines.append('        form,')
        content_lines.append('    ])')
        
        content = "\\n".join(content_lines)
        
        view_path = self.project_path / "views" / f"{entity}_view.py"
        view_path.parent.mkdir(parents=True, exist_ok=True)
        view_path.write_text(content)
        
        return {"success": True, "step": "generate_view", "path": str(view_path), "message": f"View {entity} gerada"}
''')

# form_generator.py
write_file("core/generators/form_generator.py", '''
"""
Form Generator - Gera formulários Flet
"""
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class FormGenerator:
    """Gerador de formulários Flet"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def generate(self, form_name: str, fields: List[str]) -> bool:
        """Gera um formulário"""
        form_cap = form_name.capitalize()
        
        # Gera campos
        fields_code = ""
        data_fields = ""
        for field in fields:
            field_name = field.lower().replace(" ", "_")
            fields_code += f'        self.{field_name}_field = ft.TextField(label="{field.capitalize()}", hint_text="Digite o {field}")\n'
            data_fields += f'            "{field_name}": self.{field_name}_field.value,\n'
        
        # Construir lista de campos
        field_list = ",\n".join([f'            self.{f.lower().replace(" ", "_")}_field' for f in fields])
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Form {form_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('import flet as ft')
        content_lines.append('')
        content_lines.append(f'class {form_cap}Form(ft.UserControl):')
        content_lines.append(f'    """Formulário {form_name}"""')
        content_lines.append('')
        content_lines.append('    def __init__(self, on_submit=None, initial_data=None):')
        content_lines.append('        super().__init__()')
        content_lines.append('        self.on_submit = on_submit')
        content_lines.append('        self.initial_data = initial_data or {}')
        content_lines.append('')
        content_lines.append('    def build(self):')
        if fields_code:
            content_lines.append(fields_code.rstrip())
        content_lines.append('')
        content_lines.append('        self.submit_button = ft.ElevatedButton(')
        content_lines.append('            "Enviar",')
        content_lines.append('            on_click=self._on_submit,')
        content_lines.append('            icon=ft.icons.SEND')
        content_lines.append('        )')
        content_lines.append('')
        content_lines.append('        self.cancel_button = ft.TextButton(')
        content_lines.append('            "Cancelar",')
        content_lines.append('            on_click=self._on_cancel')
        content_lines.append('        )')
        content_lines.append('')
        content_lines.append('        controls = [')
        content_lines.append(field_list)
        content_lines.append('            ft.Row([self.submit_button, self.cancel_button], alignment=ft.MainAxisAlignment.END),')
        content_lines.append('        ]')
        content_lines.append('')
        content_lines.append('        return ft.Column(controls, spacing=15)')
        content_lines.append('')
        content_lines.append('    def _on_submit(self, e):')
        content_lines.append('        if self.on_submit:')
        content_lines.append('            data = {')
        content_lines.append(data_fields.rstrip())
        content_lines.append('            }')
        content_lines.append('            self.on_submit(data)')
        content_lines.append('')
        content_lines.append('    def _on_cancel(self, e):')
        content_lines.append('        """Limpa o formulário"""')
        content_lines.append('        for field_name in dir(self):')
        content_lines.append('            if field_name.endswith("_field") and hasattr(self, field_name):')
        content_lines.append('                field = getattr(self, field_name)')
        content_lines.append('                field.value = ""')
        content_lines.append('        self.update()')
        content_lines.append('')
        content_lines.append('    def get_data(self):')
        content_lines.append('        """Retorna os dados do formulário"""')
        content_lines.append('        return {')
        content_lines.append(data_fields.rstrip())
        content_lines.append('        }')
        content_lines.append('')
        content_lines.append('    def set_data(self, data: dict):')
        content_lines.append('        """Preenche o formulário com dados"""')
        content_lines.append('        for key, value in data.items():')
        content_lines.append('            field_name = f"{key}_field"')
        content_lines.append('            if hasattr(self, field_name):')
        content_lines.append('                field = getattr(self, field_name)')
        content_lines.append('                field.value = value')
        content_lines.append('        self.update()')
        
        content = "\\n".join(content_lines)
        
        form_path = self.project_path / "forms" / f"{form_name}.py"
        form_path.parent.mkdir(parents=True, exist_ok=True)
        form_path.write_text(content)
        
        return True
''')

# view_generator.py
write_file("core/generators/view_generator.py", '''
"""
View Generator - Gera views (páginas) Flet
"""
from pathlib import Path
from typing import List
from datetime import datetime

class ViewGenerator:
    """Gerador de views/páginas Flet"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def generate(self, view_name: str) -> bool:
        """Gera uma view/page"""
        view_cap = view_name.capitalize()
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Page {view_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('import flet as ft')
        content_lines.append('')
        content_lines.append(f'def {view_name}_page(page: ft.Page):')
        content_lines.append(f'    """Página {view_name}"""')
        content_lines.append('')
        content_lines.append('    # Configuração da página')
        content_lines.append(f'    page.title = "{view_cap}"')
        content_lines.append('    page.padding = 20')
        content_lines.append('    page.scroll = ft.ScrollMode.AUTO')
        content_lines.append('')
        content_lines.append('    # Conteúdo principal')
        content_lines.append('    title = ft.Text(')
        content_lines.append(f'        "{view_cap}",')
        content_lines.append('        size=40,')
        content_lines.append('        weight=ft.FontWeight.BOLD,')
        content_lines.append('        color=ft.Colors.BLUE')
        content_lines.append('    )')
        content_lines.append('')
        content_lines.append('    subtitle = ft.Text(')
        content_lines.append(f'        f"Bem-vindo à página {view_name}!",')
        content_lines.append('        size=20,')
        content_lines.append('        color=ft.Colors.GREY_600')
        content_lines.append('    )')
        content_lines.append('')
        content_lines.append('    content = ft.Column(')
        content_lines.append('        [')
        content_lines.append('            title,')
        content_lines.append('            subtitle,')
        content_lines.append('            ft.Divider(height=20),')
        content_lines.append('            ft.Container(')
        content_lines.append('                content=ft.Text("Conteúdo da página..."),')
        content_lines.append('                padding=10,')
        content_lines.append('                border=ft.border.all(1, ft.Colors.GREY_300),')
        content_lines.append('                border_radius=10,')
        content_lines.append('            ),')
        content_lines.append('        ],')
        content_lines.append('        spacing=15,')
        content_lines.append('        expand=True')
        content_lines.append('    )')
        content_lines.append('')
        content_lines.append('    # Retorna o layout')
        content_lines.append('    return content')
        content_lines.append('')
        content_lines.append('')
        content_lines.append('def register_routes(page: ft.Page):')
        content_lines.append(f'    """Registra rotas para esta página"""')
        content_lines.append('    from fleting.routing import Route')
        content_lines.append('')
        content_lines.append('    @Route("/{view_name}")')
        content_lines.append('    def {view_name}_route():')
        content_lines.append('        return {view_name}_page(page)')
        content_lines.append('')
        content_lines.append('    @Route("/{view_name}/dashboard")')
        content_lines.append('    def {view_name}_dashboard():')
        content_lines.append('        return build_dashboard(page)')
        content_lines.append('')
        content_lines.append('')
        content_lines.append('def build_dashboard(page: ft.Page):')
        content_lines.append('    """Dashboard da página"""')
        content_lines.append('    return ft.Column([')
        content_lines.append('        ft.Text("Dashboard", size=24, weight="bold"),')
        content_lines.append('        ft.GridView(')
        content_lines.append('            expand=1,')
        content_lines.append('            runs_count=3,')
        content_lines.append('            max_extent=200,')
        content_lines.append('            child_aspect_ratio=1.0,')
        content_lines.append('            spacing=10,')
        content_lines.append('            run_spacing=10,')
        content_lines.append('        )')
        content_lines.append('    ], expand=True)')
        
        content = "\\n".join(content_lines)
        
        # Substitui placeholders
        content = content.replace("{view_name}", view_name)
        content = content.replace("{view_cap}", view_cap)
        
        view_path = self.project_path / "views" / f"{view_name}.py"
        view_path.parent.mkdir(parents=True, exist_ok=True)
        view_path.write_text(content)
        
        return True
''')

# model_generator.py
write_file("core/generators/model_generator.py", '''
"""
Model Generator - Gera models para Fleting
"""
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class ModelGenerator:
    """Gerador de models"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def generate(self, model_name: str, fields: List[str]) -> Dict:
        """Gera um model com campos"""
        model_cap = model_name.capitalize()
        model_lower = model_name.lower()
        
        # Gera campos
        fields_code = ""
        validation_code = ""
        to_dict_fields = []
        
        for field in fields:
            field_name = field.lower().replace(" ", "_")
            fields_code += f'    {field_name} = fields.StringField(max_length=255, null=False)\\n'
            validation_code += f'        if not data.get("{field_name}"):\\n'
            validation_code += f'            raise ValueError("{field.capitalize()} é obrigatório")\\n'
            to_dict_fields.append(f'            "{field_name}": self.{field_name},')
        
        to_dict_str = "\\n".join(to_dict_fields)
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Model {model_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('from fleting.db import Model')
        content_lines.append('import fleting.db.fields as fields')
        content_lines.append('from typing import Dict, Optional')
        content_lines.append('')
        content_lines.append(f'class {model_cap}(Model):')
        content_lines.append(f'    """Model para {model_lower}"""')
        content_lines.append('')
        content_lines.append(f'    __tablename__ = "{model_lower}s"')
        content_lines.append('')
        content_lines.append('    id = fields.IntegerField(primary_key=True)')
        if fields_code:
            content_lines.append(fields_code.rstrip())
        content_lines.append('    created_at = fields.DateTimeField(auto_now_add=True)')
        content_lines.append('    updated_at = fields.DateTimeField(auto_now=True)')
        content_lines.append('')
        content_lines.append('    def __repr__(self) -> str:')
        content_lines.append(f'        return f"<{model_cap} {{self.id}}>"')
        content_lines.append('')
        content_lines.append('    def __str__(self) -> str:')
        content_lines.append('        return f"{self.id} - {self.__class__.__name__}"')
        content_lines.append('')
        content_lines.append('    def to_dict(self) -> Dict:')
        content_lines.append('        """Converte para dicionário"""')
        content_lines.append('        return {')
        content_lines.append('            "id": self.id,')
        if to_dict_str:
            content_lines.append(to_dict_str)
        content_lines.append('            "created_at": self.created_at.isoformat() if self.created_at else None,')
        content_lines.append('            "updated_at": self.updated_at.isoformat() if self.updated_at else None,')
        content_lines.append('        }')
        content_lines.append('')
        content_lines.append('    @classmethod')
        content_lines.append('    def validate(cls, data: Dict) -> bool:')
        content_lines.append('        """Valida dados antes de salvar"""')
        if validation_code:
            content_lines.append(validation_code.rstrip())
        content_lines.append('        return True')
        content_lines.append('')
        content_lines.append('    @classmethod')
        content_lines.append('    def create_validated(cls, data: Dict):')
        content_lines.append('        """Cria com validação"""')
        content_lines.append('        cls.validate(data)')
        content_lines.append('        return cls.create(data)')
        content_lines.append('')
        content_lines.append('    def update_validated(self, data: Dict):')
        content_lines.append('        """Atualiza com validação"""')
        content_lines.append('        self.__class__.validate(data)')
        content_lines.append('        self.update(data)')
        
        content = "\\n".join(content_lines)
        
        model_path = self.project_path / "models" / f"{model_lower}.py"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(content)
        
        return {"success": True, "path": str(model_path), "message": f"Model {model_name} criado"}
''')

# controller_generator.py
write_file("core/generators/controller_generator.py", '''
"""
Controller Generator - Gera controllers para Fleting
"""
from pathlib import Path
from typing import List, Dict
from datetime import datetime

class ControllerGenerator:
    """Gerador de controllers"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
    
    def generate(self, controller_name: str, fields: List[str]) -> bool:
        """Gera um controller básico"""
        controller_cap = controller_name.capitalize()
        controller_lower = controller_name.lower()
        
        content_lines = []
        content_lines.append('\"\"\"')
        content_lines.append(f'Controller {controller_cap}')
        content_lines.append(f'Auto-generated by FLAI - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        content_lines.append('\"\"\"')
        content_lines.append('from fleting.controller import Controller')
        content_lines.append('from fleting.response import Response')
        content_lines.append('from typing import Dict, Any, List')
        content_lines.append('')
        content_lines.append(f'class {controller_cap}Controller(Controller):')
        content_lines.append(f'    """Controller para {controller_lower}"""')
        content_lines.append('')
        content_lines.append('    def __init__(self):')
        content_lines.append('        super().__init__()')
        content_lines.append('        self.model = None')
        content_lines.append('        self._initialize_model()')
        content_lines.append('')
        content_lines.append('    def _initialize_model(self):')
        content_lines.append('        """Inicializa o model se existir"""')
        content_lines.append('        try:')
        content_lines.append(f'            from ..models.{controller_lower} import {controller_cap}')
        content_lines.append(f'            self.model = {controller_cap}')
        content_lines.append('        except ImportError:')
        content_lines.append('            pass')
        content_lines.append('')
        content_lines.append('    def index(self, request) -> Response:')
        content_lines.append('        """Endpoint principal"""')
        content_lines.append('        if self.model:')
        content_lines.append('            items = self.model.all()')
        content_lines.append('            return Response.json({')
        content_lines.append('                "status": "success",')
        content_lines.append('                "data": [item.to_dict() for item in items]')
        content_lines.append('            })')
        content_lines.append('')
        content_lines.append('        return Response.json({')
        content_lines.append('            "status": "ok",')
        content_lines.append(f'            "message": "Controller {controller_lower} funcionando",')
        content_lines.append('            "endpoints": [')
        content_lines.append(f'                {{"method": "GET", "path": "/{controller_lower}", "description": "Lista itens"}},')
        content_lines.append(f'                {{"method": "GET", "path": "/{controller_lower}/<id>", "description": "Mostra item"}},')
        content_lines.append(f'                {{"method": "POST", "path": "/{controller_lower}", "description": "Cria item"}},')
        content_lines.append(f'                {{"method": "PUT", "path": "/{controller_lower}/<id>", "description": "Atualiza item"}},')
        content_lines.append(f'                {{"method": "DELETE", "path": "/{controller_lower}/<id>", "description": "Remove item"}},')
        content_lines.append('            ]')
        content_lines.append('        })')
        content_lines.append('')
        content_lines.append('    def show(self, request, id: int) -> Response:')
        content_lines.append('        """Mostra um item específico"""')
        content_lines.append('        if not self.model:')
        content_lines.append('            return Response.json({{"error": "Model not found"}}, status=404)')
        content_lines.append('')
        content_lines.append('        item = self.model.find(id)')
        content_lines.append('        if not item:')
        content_lines.append('            return Response.json({{"error": "Not found"}}, status=404)')
        content_lines.append('')
        content_lines.append('        return Response.json(item.to_dict())')
        content_lines.append('')
        content_lines.append('    def create(self, request) -> Response:')
        content_lines.append('        """Cria um novo item"""')
        content_lines.append('        if not self.model:')
        content_lines.append('            return Response.json({{"error": "Model not found"}}, status=500)')
        content_lines.append('')
        content_lines.append('        data = request.json')
        content_lines.append('        try:')
        content_lines.append('            if hasattr(self.model, "create_validated"):')
        content_lines.append('                item = self.model.create_validated(data)')
        content_lines.append('            else:')
        content_lines.append('                item = self.model.create(data)')
        content_lines.append('            return Response.json(item.to_dict(), status=201)')
        content_lines.append('        except Exception as e:')
        content_lines.append('            return Response.json({{"error": str(e)}}, status=400)')
        content_lines.append('')
        content_lines.append('    def update(self, request, id: int) -> Response:')
        content_lines.append('        """Atualiza um item"""')
        content_lines.append('        if not self.model:')
        content_lines.append('            return Response.json({{"error": "Model not found"}}, status=404)')
        content_lines.append('')
        content_lines.append('        item = self.model.find(id)')
        content_lines.append('        if not item:')
        content_lines.append('            return Response.json({{"error": "Not found"}}, status=404)')
        content_lines.append('')
        content_lines.append('        data = request.json')
        content_lines.append('        try:')
        content_lines.append('            if hasattr(item, "update_validated"):')
        content_lines.append('                item.update_validated(data)')
        content_lines.append('            else:')
        content_lines.append('                item.update(data)')
        content_lines.append('            return Response.json(item.to_dict())')
        content_lines.append('        except Exception as e:')
        content_lines.append('            return Response.json({{"error": str(e)}}, status=400)')
        content_lines.append('')
        content_lines.append('    def delete(self, request, id: int) -> Response:')
        content_lines.append('        """Remove um item"""')
        content_lines.append('        if not self.model:')
        content_lines.append('            return Response.json({{"error": "Model not found"}}, status=404)')
        content_lines.append('')
        content_lines.append('        item = self.model.find(id)')
        content_lines.append('        if not item:')
        content_lines.append('            return Response.json({{"error": "Not found"}}, status=404)')
        content_lines.append('')
        content_lines.append('        item.delete()')
        content_lines.append('        return Response.json({{"message": "Deleted"}})')
        content_lines.append('')
        content_lines.append('    def get_routes(self) -> List[Dict]:')
        content_lines.append('        """Retorna rotas disponíveis"""')
        content_lines.append('        return [')
        content_lines.append(f'            {{"method": "GET", "path": "/{controller_lower}", "handler": self.index}},')
        content_lines.append(f'            {{"method": "GET", "path": "/{controller_lower}/<id:int>", "handler": self.show}},')
        content_lines.append(f'            {{"method": "POST", "path": "/{controller_lower}", "handler": self.create}},')
        content_lines.append(f'            {{"method": "PUT", "path": "/{controller_lower}/<id:int>", "handler": self.update}},')
        content_lines.append(f'            {{"method": "DELETE", "path": "/{controller_lower}/<id:int>", "handler": self.delete}},')
        content_lines.append('        ]')
        
        content = "\\n".join(content_lines)
        
        controller_path = self.project_path / "controllers" / f"{controller_lower}_controller.py"
        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.write_text(content)
        
        return True
''')

# ============================================================================
# 4. EXECUTORS (core/executors/)
# ============================================================================

write_file("core/executors/__init__.py", '''"""Executores de comandos Fleting e Shell"""
from .fleting_executor import FletingExecutor
from .shell_executor import ShellExecutor

__all__ = ["FletingExecutor", "ShellExecutor"]
''')

write_file("core/executors/fleting_executor.py", '''"""
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
        """
        Executa comando do Fleting
        
        Args:
            command: Comando (ex: "create page produtos")
        
        Returns:
            (return_code, stdout, stderr)
        """
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
            return -1, "", "Comando 'fleting' não encontrado. Certifique-se de que está instalado."
        except Exception as e:
            return -1, "", str(e)
    
    def create_page(self, page_name: str) -> bool:
        """Cria uma nova página no Fleting"""
        code, stdout, stderr = self.run(f"create page {page_name}")
        return code == 0
    
    def create_model(self, model_name: str) -> bool:
        """Cria um novo model"""
        code, stdout, stderr = self.run(f"db make {model_name}")
        return code == 0
    
    def run_migrations(self) -> bool:
        """Executa migrations"""
        code, stdout, stderr = self.run("db migrate")
        if code != 0:
            # Tenta comando alternativo
            code, stdout, stderr = self.run("migrate")
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
            self._fleting_available = code == 0        return self._fleting_available
    
    def get_project_info(self) -> dict:
        """Retorna informações do projeto"""
        return {
            "path": str(self.project_path),
            "has_fleting": self.is_available(),
            "pages": self.list_pages(),
            "models": self.list_models(),
            "has_migrations": (self.project_path / "migrations").exists()
        }
''')

write_file("core/executors/shell_executor.py", '''"""
Shell Executor - Executa comandos shell genéricos com segurança
"""
import subprocess
import shlex
from pathlib import Path
from typing import Tuple, Optional, List

class ShellExecutor:
    """Executor seguro de comandos shell"""
    
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path.cwd()
    
    def run(self, cmd: str, timeout: int = 120) -> Tuple[int, str, str]:
        """
        Executa comando shell
        
        Args:
            cmd: Comando a executar
            timeout: Timeout em segundos
        
        Returns:
            (return_code, stdout, stderr)
        """
        try:
            args = shlex.split(cmd)
            result = subprocess.run(
                args,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Comando excedeu tempo limite de {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def run_python(self, code: str) -> Tuple[int, str, str]:
        """Executa código Python inline"""
        return self.run(f'python -c "{code}"', timeout=30)
    
    def run_script(self, script_path: Path, args: List[str] = None) -> Tuple[int, str, str]:
        """Executa script Python"""
        if not script_path.exists():
            return -1, "", f"Script não encontrado: {script_path}"
        
        cmd = f"python {script_path}"
        if args:
            cmd += " " + " ".join(shlex.quote(a) for a in args)
        return self.run(cmd)
    
    def install_package(self, package: str, dev: bool = False) -> bool:
        """Instala pacote pip"""
        cmd = f"pip install {package}"
        if dev:
            cmd += " -e ."
        code, _, _ = self.run(cmd)
        return code == 0
    
    def run_make(self, target: str = None) -> bool:
        """Executa make"""
        cmd = "make"
        if target:
            cmd += f" {target}"
        code, _, _ = self.run(cmd)
        return code == 0
    
    def is_command_available(self, command: str) -> bool:
        """Verifica se comando está disponível"""
        code, _, _ = self.run(f"which {command}")
        return code == 0 or shutil.which(command) is not None
    
    def get_python_version(self) -> str:
        """Retorna versão do Python"""
        code, stdout, _ = self.run("python --version")
        if code == 0:
            return stdout.strip()
        return "unknown"
''')

# ============================================================================
# 5. RAG (com LangChain - esqueleto opcional)
# ============================================================================

write_file("core/rag/__init__.py", '''"""Módulo RAG com LangChain para busca semântica (opcional)"""
from .indexer import Indexer
from .retriever import Retriever
from .embeddings import Embeddings

__all__ = ["Indexer", "Retriever", "Embeddings"]
''')

write_file("core/rag/indexer.py", '''"""
RAG Indexer - Indexa código do projeto para busca semântica
LangChain opcional - requer `pip install langchain chromadb`
"""
from pathlib import Path
from typing import List, Optional

class Indexer:
    """Indexador de código para RAG"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.index_path = project_path / ".flai" / "vectordb"
        self._initialized = False
    
    def _init_langchain(self):
        """Inicializa LangChain (opcional)"""
        try:
            from langchain_community.document_loaders import DirectoryLoader
            from langchain_community.vectorstores import Chroma
            from langchain_ollama import OllamaEmbeddings
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            self.loader_cls = DirectoryLoader
            self.vectorstore_cls = Chroma
            self.embeddings = OllamaEmbeddings(model="nomic-embed-text")
            self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            self._initialized = True
            return True
        except ImportError:
            print("⚠️ LangChain não instalado. Execute: pip install langchain langchain-community chromadb")
            return False
    
    def index_project(self) -> bool:
        """Indexa todo o projeto"""
        if not self._init_langchain():
            return False
        
        try:
            # Carrega arquivos Python
            loader = self.loader_cls(str(self.project_path), glob="**/*.py")
            documents = loader.load()
            
            # Divide em chunks
            chunks = self.splitter.split_documents(documents)
            
            # Cria vector store
            self.index_path.mkdir(parents=True, exist_ok=True)
            vectorstore = self.vectorstore_cls.from_documents(
                chunks,
                self.embeddings,
                persist_directory=str(self.index_path)
            )
            vectorstore.persist()
            
            print(f"✅ Indexados {len(documents)} arquivos, {len(chunks)} chunks")
            return True
            
        except Exception as e:
            print(f"Erro ao indexar: {e}")
            return False
    
    def add_file(self, file_path: Path) -> bool:
        """Adiciona arquivo ao índice"""
        # TODO: Implementar atualização incremental
        return self.index_project()
    
    def clear(self) -> bool:
        """Limpa índice"""
        import shutil
        if self.index_path.exists():
            shutil.rmtree(self.index_path)
            self.index_path.mkdir(parents=True)
        return True
''')

write_file("core/rag/retriever.py", '''"""
RAG Retriever - Busca semântica no código
"""
from pathlib import Path
from typing import List, Dict, Any, Optional

class Retriever:
    """Recuperador de contexto semântico"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.index_path = project_path / ".flai" / "vectordb"
        self._vectorstore = None
    
    def _init_vectorstore(self):
        """Inicializa vector store (LangChain)"""
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_ollama import OllamaEmbeddings
            
            if self.index_path.exists():
                self._vectorstore = Chroma(
                    persist_directory=str(self.index_path),
                    embedding_function=OllamaEmbeddings(model="nomic-embed-text")
                )
            return self._vectorstore is not None
        except ImportError:
            return False
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca documentos similares
        
        Args:
            query: Texto da busca
            k: Número de resultados
        
        Returns:
            Lista de documentos com conteúdo e metadados
        """
        if not self._init_vectorstore():
            return []
        
        try:
            results = self._vectorstore.similarity_search(query, k=k)
            return [
                {
                    "content": doc.page_content[:500],
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "unknown")
                }
                for doc in results
            ]
        except Exception as e:
            print(f"Erro na busca: {e}")
            return []
    
    def search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """Busca com scores de similaridade"""
        if not self._init_vectorstore():
            return []
        
        try:
            return self._vectorstore.similarity_search_with_score(query, k=k)
        except Exception:
            return []
    
    def get_context_for_prompt(self, query: str, max_tokens: int = 2000) -> str:
        """Gera contexto formatado para prompt"""
        results = self.search(query, k=3)
        if not results:
            return ""
        
        context = "## Contexto relevante do código:\\n\\n"
        for i, result in enumerate(results, 1):
            context += f"### {i}. {result['source']}\\n"
            context += f"```python\\n{result['content']}\\n```\\n\\n"
        
        return context[:max_tokens]
''')

write_file("core/rag/embeddings.py", '''"""
RAG Embeddings - Wrapper para embeddings
"""
from typing import List, Optional

class Embeddings:
    """Wrapper para embeddings com fallback"""
    
    def __init__(self, model: str = "nomic-embed-text"):
        self.model = model
        self._embeddings = None
        self._available = None
    
    def _init_embeddings(self):
        """Inicializa embeddings com LangChain"""
        if self._available is not None:
            return self._available
        
        try:
            from langchain_ollama import OllamaEmbeddings
            self._embeddings = OllamaEmbeddings(model=self.model)
            self._available = True
        except ImportError:
            self._available = False
        
        return self._available
    
    def embed_query(self, text: str) -> Optional[List[float]]:
        """Gera embedding para consulta"""
        if not self._init_embeddings():
            return None
        
        try:
            return self._embeddings.embed_query(text)
        except Exception:
            return None
    
    def embed_documents(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Gera embeddings para documentos"""
        if not self._init_embeddings():
            return None
        
        try:
            return self._embeddings.embed_documents(texts)
        except Exception:
            return None
    
    def is_available(self) -> bool:
        """Verifica se embeddings estão disponíveis"""
        self._init_embeddings()
        return self._available
''')

# ============================================================================
# 6. MCP (core/mcp/)
# ============================================================================

write_file("core/mcp/__init__.py", '''"""MCP - Model Context Protocol (contexto estruturado)"""
from .context_builder import ContextBuilder
from .prompt_builder import PromptBuilder

__all__ = ["ContextBuilder", "PromptBuilder"]
''')

write_file("core/mcp/context_builder.py", '''"""
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
''')

write_file("core/mcp/prompt_builder.py", '''
"""
Prompt Builder - Montagem de prompts estruturados para IA
"""
from typing import Dict, Any, Optional, List

class PromptBuilder:
    """Constrói prompts otimizados para LLM"""
    
    def __init__(self, system_prompt: str = None):
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.messages = []
    
    def _default_system_prompt(self) -> str:
        return "Você é FLAI, um assistente de IA especialista em desenvolvimento com Python e Flet (framework UI).\\n\\nVocê ajuda desenvolvedores a criar aplicações web com interface Flet, seguindo boas práticas de arquitetura MVC.\\n\\nSuas características:\\n- Responda em português (pt-BR)\\n- Seja direto e prático\\n- Forneça exemplos de código quando relevante\\n- Explique conceitos com clareza\\n- Sugira melhorias baseadas nas melhores práticas\\n\\nLimitações:\\n- Você só analisa o código do projeto atual\\n- Não acessa arquivos externos\\n- Suas respostas são baseadas APENAS no código fornecido no contexto"
    
    def add_system(self, system: str) -> 'PromptBuilder':
        """Adiciona/sobrescreve system prompt"""
        self.system_prompt = system
        return self
    
    def add_user(self, user_message: str) -> 'PromptBuilder':
        """Adiciona mensagem de usuário"""
        self.messages.append(("user", user_message))
        return self
    
    def add_assistant(self, assistant_message: str) -> 'PromptBuilder':
        """Adiciona resposta do assistente"""
        self.messages.append(("assistant", assistant_message))
        return self
    
    def add_context(self, context: str) -> 'PromptBuilder':
        """Adiciona contexto estruturado"""
        contextualized = f"\\n## Contexto do Projeto\\n{context}\\n\\n---\\n"
        return self.add_user(contextualized)
    
    def add_code(self, code: str, language: str = "python") -> 'PromptBuilder':
        """Adiciona bloco de código"""
        code_block = f"```{language}\\n{code}\\n```"
        return self.add_user(code_block)
    
    def build(self) -> Dict[str, Any]:
        """Constrói prompt completo"""
        prompt = {
            "system": self.system_prompt,
            "messages": []
        }
        
        for role, content in self.messages:
            prompt["messages"].append({
                "role": role,
                "content": content
            })
        
        return prompt
    
    def build_string(self) -> str:
        """Constrói string simples para modelos que não suportam messages"""
        result = f"System: {self.system_prompt}\\n\\n"
        
        for role, content in self.messages:
            if role == "user":
                result += f"User: {content}\\n\\n"
            else:
                result += f"Assistant: {content}\\n\\n"
        
        result += "Assistant: "
        return result
    
    def clear(self) -> 'PromptBuilder':
        """Limpa histórico de mensagens"""
        self.messages = []
        return self
    
    def add_fleting_example(self) -> 'PromptBuilder':
        """Adiciona exemplo de código Fleting"""
        example = "\\nExemplo de uma página Flet básica:\\n```python\\nimport flet as ft\\n\\ndef main(page: ft.Page):\\n    page.title = \\"Olá Flet\\"\\n    page.add(ft.Text(\\"Bem-vindo!\\"))\\n    \\nft.app(target=main)\\n```"
        return self.add_user(example)
''')