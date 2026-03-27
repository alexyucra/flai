from typing import Annotated

from typer import Context, Option, Typer
from flai.cli.commands.init import init_app
from flai.cli.commands.info import info_app
from flai.cli.commands.shell import shell_app
from flai.cli.console.console import console
from flai.cli.console import Table, Panel, box
from flai.cli.utils.version import version_callback
from flai import translations as tt

FLAI_FOOTER = """
💡 Curtiu o Flai?\n
Ajude a liberar novas features 🚀\n\n
[bold yellow]Meta: 2000 inscritos[/bold yellow]\n
👉 https://www.youtube.com/@LatinDev
"""

FLAI_HEADER = """
🚀 [bold cyan]Flai - Framework local de IA[/bold cyan]\n\n
Este projeto é [bold green]opensource[/bold green].\n
Você está entre os primeiros usuários.\n
[bold red]Mais Versões serão liberadas[/bold red].\n
[bold yellow]somente após 1000 e 2000 inscritos.[/bold yellow].\n\n
👉 https://www.youtube.com/@LatinDev\n
curso fleting completo: https://youtu.be/sm3jWfd1ceU?si=8xCUIRfYGWkKym7X\n
"""

main_app = Typer(
    name="Flai",
    invoke_without_command=True,
    no_args_is_help=False,
    add_completion=True,
    epilog=FLAI_FOOTER,
    rich_markup_mode="rich",
    help=FLAI_HEADER,
    context_settings={"help_option_names": ["-h", "--help"]},
)


main_app.add_typer(info_app)
main_app.add_typer(init_app)
main_app.add_typer(shell_app)


@main_app.callback()
def main(
    ctx: Context,
    version: Annotated[
        bool | None,
        Option(
            ...,
            "--version",
            "-v",
            is_eager=True,
            callback=version_callback,
            help=tt.tr("Show the version and exit."),
        ),
    ] = None,
    lang: Annotated[
        str,
        Option(
            ...,
            "--lang",
            "-l",
            help=tt.tr("Language (leave empty to detect system language)"),
        ),
    ] = "en",
) -> None:
    """
    🚀 [bold cyan]Flai - Framework local de IA[/bold cyan]\n\n
    Este projeto é [bold green]opensource[/bold green].\n
    Você está entre os primeiros usuários.\n
    [bold red]Mais Versões serão liberadas[/bold red].\n
    [bold yellow]somente após 1000 e 2000 inscritos.[/bold yellow].\n\n
    👉 https://www.youtube.com/@LatinDev\n
    curso fleting completo: https://youtu.be/sm3jWfd1ceU?si=8xCUIRfYGWkKym7X\n

    """
    tt.set_language(lang)
    ctx.obj = {"lang": lang}

    show_banner()
    print_help()
    show_footer()


def print_help() -> None:
    console.clear()

    console.print()
    console.rule("[bold cyan]🚀 Flai CLI[/bold cyan]", style="cyan")
    console.print()

    console.print(
        Panel.fit(
            "[bold green]flai <command> [options][/bold green]",
            title="[yellow]📌 Usage[/yellow]",
            border_style="yellow",
            padding=(1, 2),
        )
    )
    console.print()

    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        border_style="blue",
        padding=(0, 1),
    )

    table.add_column(tt.tr("Command"), style="bold green", width=36)
    table.add_column(tt.tr("Description"), style="cyan", width=44)

    # Comandos organizados por categorías
    categories = {
        tt.tr("💼 Project Commands"): [
            ("flai init ia", tt.tr("Setup local AI environment")),
            ("flai shell", tt.tr("Interactive AI shell")),
        ]
    }

    for category, commands in categories.items():
        # Añadir separador para categorías
        if list(categories.keys()).index(category) > 0:
            table.add_row("─" * 36, "─" * 44, style="dim")

        # Añadir título de categoría
        table.add_row(f"[bold yellow]{category}[/bold yellow]", "", style="yellow")

        # Añadir comandos de la categoría
        for cmd, desc in commands:
            table.add_row(f"  {cmd}", desc)

    console.print(table)
    console.print()


def show_banner() -> None:
    console.print(
        Panel(
            "🚀 [bold cyan]Flai - Framework local de IA[/bold cyan]\n\n"
            "Este projeto é [bold green]opensource[/bold green].\n"
            "Você está entre os primeiros usuários.\n"
            "[bold red]Mais Versões serão liberadas[/bold red].\n"
            "[bold yellow]somente após 1000 e 2000 inscritos.[/bold yellow].\n\n"
            "👉 https://www.youtube.com/@LatinDev\n"
            "curso fleting completo: https://youtu.be/sm3jWfd1ceU?si=8xCUIRfYGWkKym7X\n",
            title="Flai",
            border_style="cyan",
        )
    )


def show_footer() -> None:
    console.print(
        Panel(
            "💡 Curtiu o Flai?\n"
            "Ajude a liberar novas features 🚀\n\n"
            "[bold yellow]Meta: 2000 inscritos[/bold yellow]\n"
            "👉 https://www.youtube.com/@LatinDev\n",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main_app()
