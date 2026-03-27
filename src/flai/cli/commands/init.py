from pathlib import Path
from typing import Annotated

from rich.table import Table
from typer import Argument, Exit, Typer, prompt

from flai.cli.console.console import console
from flai.cli.utils.models import get_laptop_models
from flai.cli.utils.ollama import install_ollama, pull_model
from flai.cli.utils.system import analyze_system, system_checklist

from flai import translations as tt

DEFAULT_PROJECT_NAME = "app"

init_app = Typer(no_args_is_help=False)


@init_app.command(
    name="init",
    help=tt.tr("Init local AI (LangChain + Ollama) for the Fleting project."),
    short_help=tt.tr("Setup local AI environment"),
)
def init_command(
    ia: Annotated[
        str | None,
        Argument(
            ...,
            help=tt.tr("Specific IA to init."),
        ),
    ] = None,
) -> None:
    cwd = Path.cwd()
    project_root = cwd / DEFAULT_PROJECT_NAME
    if not project_root:
        console.print(f"[error]{tt.tr("Fleting project not found")}[/error]")
        raise Exit(1)

    console.print(f"[bold cyan]{tt.tr("Initializing FLAI (Local AI)")}[/bold cyan]\n")

    # 1. Analisar sistema
    system_info = analyze_system()
    chklist = system_checklist()

    # 2. Mostrar checklist
    console.print(f"[bold]{tt.tr("System checklist")}:[/bold]")

    for item, ok in chklist.items():
        icon = "✅" if ok else "❌"
        console.print(f"{icon} {item}")

    if not chklist["RAM suficiente"]:
        console.print(f"[warning]{tt.tr("Low RAM detected")}[/warning]")

    # 3. Mostrar modelos disponíveis
    models = get_laptop_models(system_info)

    table = Table(title=tt.tr("Recommended models for your laptop"))

    table.add_column(tt.tr("Option"), justify="center")
    table.add_column(tt.tr("Model"), justify="center")
    table.add_column(tt.tr("Minimum RAM"), justify="center")
    table.add_column(tt.tr("Usage"), justify="center")

    for i, model in enumerate(models, start=1):
        table.add_row(str(i), model["name"], model["ram"], model["description"])

    table.add_row(str(0), tt.tr("Exit"), "----", tt.tr("Type '0' to exit"))

    console.print(table)

    # 4. Escolha do usuário
    choice = int(prompt(tt.tr("Choose the model"), type=int))

    if choice == 0:
        raise Exit()

    selected = models[choice - 1]

    console.print(f"[info]{tt.tr("Installing model")} {selected['name']}...[/info]")

    # 5. Instalar Ollama + modelo
    install_ollama()
    pull_model(selected["ollama_id"])

    console.print(f"[success]{tt.tr("Local AI installed successfully!")}[/success]")
