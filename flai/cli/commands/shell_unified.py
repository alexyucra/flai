# flai/cli/commands/shell_unified.py
"""
Comando shell unificado usando novo REPL
"""
import typer
from pathlib import Path
from typing import Optional

# from flai.core import get_rag, get_agent_manager, get_context_manager, get_ollama
from flai.cli.repl_unified import run_unified_repl
from flai.cli.console.console import console
from flai.core.project import get_project_root

app = typer.Typer()

def sanitize_user_input(text: str) -> str:
    """Sanitiza input do usuário antes de processar"""
    if not text:
        return text
    
    # Remove sequências ANSI
    import re
    text = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)
    
    # Remove caracteres de controle (exceto newline, tab)
    text = ''.join(ch for ch in text if ord(ch) >= 32 or ch in '\n\r\t')
    
    # Remove possíveis comandos shell maliciosos
    dangerous = ['`', '$', '${', '$(', '|', ';', '&&', '||']
    for d in dangerous:
        if d in text:
            # Substitui por versão segura
            text = text.replace(d, '')
    
    # Limita tamanho
    return text[:4096]

def handle_shell_unified(
    project: Optional[str] = None,
    model: Optional[str] = None,
    session: Optional[str] = None
):
    """
    Inicia REPL unificado do FLAI com suporte a RAG e histórico Markdown
    """
    # Obtém caminho do projeto
    if project:
        project_path = Path(project).resolve()
    else:
        project_path = get_project_root()
    
    if not project_path:
        console.print("[red]❌ Nenhum projeto Fleting encontrado.[/red]")
        console.print("[dim]Execute 'fleting init <nome>' para criar um projeto[/dim]")
        raise typer.Exit(1)
    
    # Verifica se FLAI está inicializado
    config_file = project_path / ".flai" / "config.json"
    if not config_file.exists():
        console.print("[yellow]⚠️ FLAI não inicializado neste projeto.[/yellow]")
        console.print("[dim]Execute 'flai init' primeiro[/dim]")
        
        if typer.confirm("Deseja executar 'flai init' agora?"):
            from flai.cli.commands.init import handle_init
            handle_init(model or "flai-ai", str(project_path), False)
        else:
            raise typer.Exit(1)
    
    # Inicia REPL unificado
    console.print("[dim]🚀 Iniciando FLAI Unified REPL...[/dim]")
    if model:
        model = sanitize_user_input(model)
    run_unified_repl(project_path, model)

    from flai.cli.utils.ollama_manager import cleanup_ollama
    cleanup_ollama()


# Substitui o shell antigo
def handle_shell(project: str, model: str, context: Optional[str]):
    """Wrapper para manter compatibilidade"""
    handle_shell_unified(project, model, None)