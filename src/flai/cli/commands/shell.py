from pathlib import Path
from typing import Annotated

from typer import Argument, Typer

from flai.cli.console.console import console
from flai.cli.utils.checklist import create_checklist
from flai.cli.utils.context import build_context_map
from flai.cli.utils.ollama import run_ollama
from flai.cli.utils.scanner import scan_project

from flai import translations as tt

DEFAULT_PROJECT_NAME = "app"

shell_app = Typer(no_args_is_help=False)


@shell_app.command(
    name="shell",
    help=tt.tr("Open FLAI Shell and analyze the Fleting project."),
    short_help=tt.tr("Interactive AI shell"),
)
def shell_command(
    ia: Annotated[
        str | None,
        Argument(
            ...,
            help=tt.tr("Specific IA to use."),
        ),
    ] = None,
) -> None:
    cwd = Path.cwd()
    project_root = cwd / DEFAULT_PROJECT_NAME

    if not project_root.exists():
        console.print(f"[error]{tt.tr("No Fleting projects found.")}[/error]")
        return

    console.print(f"[bold cyan]{tt.tr("FLAI Shell initiated")}[/bold cyan]")

    # 1. Scan
    scan = scan_project(project_root)

    # 2. Context Map
    context_map = build_context_map(scan)

    # 3. Checklist
    checklist_file = create_checklist(project_root)

    console.print(
        f"[success]{tt.tr("Checklist created at")} {checklist_file}[/success]"
    )

    # 4. Prompt base
    prompt = f"""
{tt.tr("You are a software architect specialist in Python and Flet.")}

{tt.tr("Analyze the following Fleting project:")}

{context_map}

{tt.tr("Generate objective suggestions for improvement, without rewriting code.")}
"""

    console.print(f"[info]{tt.tr("Analyzing project with AI...")}[/info]")

    response = run_ollama("deepseek-coder:1.3b", prompt)

    console.print(f"\n[bold]{tt.tr("Initial suggestions")}:[/bold]\n")
    console.print(response)

    console.print(f"\n{tt.tr("Type 'exit' to leave.")}")
