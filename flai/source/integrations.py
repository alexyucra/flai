# fleting/flai/utils/integrations.py
from langchain.tools import Tool
import subprocess
from pathlib import Path

class DevelopmentTools:
    @staticmethod
    def git_tool(query: str) -> str:
        """Executa comandos git básicos"""
        safe_commands = ["status", "log --oneline -5", "branch", "remote -v"]
        
        if query in safe_commands:
            try:
                result = subprocess.run(
                    ["git", *query.split()],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                return result.stdout or result.stderr
            except:
                return "Erro ao executar git"
        
        return "Comando git não permitido"
    
    @staticmethod
    def dependency_tool(query: str) -> str:
        """Analisa dependências do projeto"""
        try:
            # Verificar requirements.txt
            req_file = Path("requirements.txt")
            if req_file.exists():
                deps = req_file.read_text(encoding='utf-8')
                return f"Dependências encontradas:\n{deps}"
            
            # Verificar pyproject.toml
            pyproject = Path("pyproject.toml")
            if pyproject.exists():
                content = pyproject.read_text(encoding='utf-8')
                return f"pyproject.toml encontrado"
            
            return "Nenhum arquivo de dependências encontrado"
        except:
            return "Erro ao analisar dependências"
    
    @staticmethod
    def test_tool(query: str) -> str:
        """Executa testes"""
        if query == "run tests":
            try:
                result = subprocess.run(
                    ["pytest", "-v"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return result.stdout or "Nenhum teste executado"
            except:
                return "pytest não encontrado"
        
        return "Comando de teste não reconhecido"