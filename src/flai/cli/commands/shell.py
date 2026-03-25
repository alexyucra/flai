from pathlib import Path
from typing import Annotated

from typer import Argument, Typer

from flai.cli.console.console import console
from flai.cli.utils.checklist import create_checklist
from flai.cli.utils.context import build_context_map
from flai.cli.utils.ollama import run_ollama
from flai.cli.utils.scanner import scan_project

DEFAULT_PROJECT_NAME = "app"

shell_app = Typer(no_args_is_help=False)


@shell_app.command(
    name="shell",
    help="Abre o FLAI Shell e analisa o projeto Fleting",
    short_help="Interactive AI shell",
)
def shell_command(
    ia: Annotated[
        str | None,
        Argument(
            ...,
            help="Specific IA to use.",
        ),
    ] = None,
) -> None:
    """
    Abre o FLAI Shell e analisa o projeto Fleting
    """
    cwd = Path.cwd()
    project_root = cwd / DEFAULT_PROJECT_NAME

    if not project_root.exists():
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
