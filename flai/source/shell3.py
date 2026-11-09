import typer
from pathlib import Path

from flai.cli.console.console import console
from flai.cli.utils.scanner import scan_project
from flai.cli.utils.context import build_context_map
from flai.cli.utils.checklist import create_checklist
from flai.cli.utils.ollama import run_ollama
# from flai.core.project import get_project_root

DEFAULT_PROJECT_NAME = "app"

app = typer.Typer()

def handle_shell():
    """
    Abre o FLAI Shell e analisa o projeto Fleting
    """
    cwd = Path.cwd()
    project_root = cwd / DEFAULT_PROJECT_NAME
    
    if not project_root:
        console.print("[error]No Fleting projects found.[/error]")
        return

    console.print("[bold cyan]FLAI Shell iniciado[/bold cyan]")

    # 1. Scan
    scan = scan_project(project_root)

    # 2. Context Map
    context_map = build_context_map(scan)

    # 3. Checklist
    checklist_file = create_checklist(project_root)

    console.print(f"[success]Checklist criado em {checklist_file}[/success]")

    # 4. Prompt base
    prompt = f"""
Você é um arquiteto de software especialista em Python e Flet.

Analise o seguinte projeto Fleting:

{context_map}

Gere sugestões objetivas de melhoria,
sem reescrever código.
"""

    console.print("[info]Analisando projeto com IA...[/info]")

    response = run_ollama("deepseek-coder:1.3b", prompt)

    console.print("\n[bold]Sugestões iniciais:[/bold]\n")
    console.print(response)

    console.print("\nDigite 'exit' para sair")
