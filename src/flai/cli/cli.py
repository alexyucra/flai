import sys
import typer
import click
from flai.cli.commands.init import handle_init
from flai.cli.commands.shell import handle_shell

# from flai.cli.commands.init2 import handle_init
# from flai.cli.commands.shell2 import handle_shell
from flai.cli.console.console import console
from flai.cli.console import Table, Panel, box
import traceback


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

    table.add_column("Command", style="bold green", width=36)
    table.add_column("Description", style="cyan", width=44)

    # Comandos organizados por categorías
    categories = {
        "💼 Project Commands": [
            ("flai init ia", "Setup local AI environment"),
            ("flai shell", "Interactive AI shell"),
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


def main() -> None:
    show_banner()
    if len(sys.argv) < 2:
        print_help()
        return
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print_help()
        return

    cmd = args[0]
    subargs = args[1:]
    try:
        if cmd == "init":
            handle_init(subargs)
        elif cmd == "shell":
            handle_shell()
        else:
            print(f"Unknown command: {cmd}")
    except typer.Exit, click.exceptions.Exit:
        raise
    except Exception as e:
        print("Error executing CLI command:", str(e))
        traceback.print_exc()
    finally:
        show_footer()


if __name__ == "__main__":
    typer.run(main)
