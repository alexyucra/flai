from pathlib import Path
from typing import Annotated

from rich.table import Table
from typer import Argument, Exit, Typer, prompt

from flai.cli.console.console import console
from flai.cli.utils.models import get_laptop_models
from flai.cli.utils.ollama import install_ollama, pull_model
from flai.cli.utils.system import analyze_system, system_checklist

DEFAULT_PROJECT_NAME = "app"

init_app = Typer(no_args_is_help=False)


@init_app.command(
    name="init",
    help="Inicializa IA local (LangChain + Ollama) para o projeto Fleting",
    short_help="Setup local AI environment",
)
def init_command(
    ia: Annotated[
        str | None,
        Argument(
            ...,
            help="Specific IA to init.",
        ),
    ] = None,
) -> None:
    """
    Inicializa IA local (LangChain + Ollama) para o projeto Fleting
    """
    cwd = Path.cwd()
    project_root = cwd / DEFAULT_PROJECT_NAME
    if not project_root:
        console.print("[error]Projeto Fleting não encontrado[/error]")
        raise Exit(1)

    console.print("[bold cyan]Inicializando FLAI (IA Local)[/bold cyan]\n")

    # 1. Analisar sistema
    system_info = analyze_system()
    chklist = system_checklist()

    # 2. Mostrar checklist
    console.print("[bold]Checklist do sistema:[/bold]")

    for item, ok in chklist.items():
        icon = "✅" if ok else "❌"
        console.print(f"{icon} {item}")

    if not chklist["RAM suficiente"]:
        console.print("[warning]Pouca RAM detectada[/warning]")

    # 3. Mostrar modelos disponíveis
    models = get_laptop_models(system_info)

    table = Table(title="Modelos recomendados para seu laptop")

    table.add_column("Opção", justify="center")
    table.add_column("Modelo")
    table.add_column("RAM mínima")
    table.add_column("Uso")

    for i, model in enumerate(models, start=1):
        table.add_row(str(i), model["name"], model["ram"], model["description"])

    table.add_row(str(0), "Exit/Sair", "----", "Digite '0' para sair")

    console.print(table)

    # 4. Escolha do usuário
    choice = int(prompt("Escolha o modelo", type=int))

    if choice == 0:
        raise Exit()

    selected = models[choice - 1]

    console.print(f"[info]Instalando modelo {selected['name']}...[/info]")

    # 5. Instalar Ollama + modelo
    install_ollama()
    pull_model(selected["ollama_id"])

    console.print("[success]IA local instalada com sucesso![/success]")
