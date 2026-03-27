from typing import List

import typer
import subprocess

from flai import DOMAIN, LOCALE_PATH, PROJECT_ROOT
from flai import translations as tt

i18n_app = typer.Typer(
    invoke_without_command=True,
    no_args_is_help=True,
    help=tt.tr("Tool for managing translations with Babel."),
)


TEMPLATE_FILE = LOCALE_PATH / f"{DOMAIN}.pot"
CONFIG_FILE = PROJECT_ROOT / "babel.cfg"


def run_pybabel(args: List[str]) -> None:
    pybabel_bin = "pybabel"

    try:
        subprocess.run([pybabel_bin] + args, check=True)
    except FileNotFoundError:
        typer.secho(
            tt.tr("Error: 'pybabel' not found. Run 'uv add --dev Babel'"),
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)


@i18n_app.command()
def extract() -> None:
    """1. Extract messages from .py files and generate a .pot file"""
    typer.echo(tt.tr("Extracting  messages from .py files..."))
    run_pybabel(
        [
            "extract",
            "-F",
            str(CONFIG_FILE),
            "-k",
            "_t",
            "-k",
            "flai._t",
            "-k",
            "tr",
            "--sort-output",
            "-o",
            str(TEMPLATE_FILE),
            str(PROJECT_ROOT / "src"),
        ]
    )


@i18n_app.command()
def init(lang: str) -> None:
    """2. Create a new language folder (e.g., es, fr)"""
    typer.echo(f"{tt.tr("Initializing catalog for")}: {lang}")
    run_pybabel(
        [
            "init",
            "-i",
            str(TEMPLATE_FILE),
            "-D",
            DOMAIN,
            "-d",
            str(LOCALE_PATH),
            "-l",
            lang,
        ]
    )


@i18n_app.command()
def update() -> None:
    """3. Synchronize new code changes with existing .po files"""
    typer.echo(tt.tr("Updating existing translation files..."))
    run_pybabel(
        ["update", "-i", str(TEMPLATE_FILE), "-D", DOMAIN, "-d", str(LOCALE_PATH)]
    )


@i18n_app.command()
def compile() -> None:
    """4. Convert .po files to .mo so the CLI can read them"""
    typer.echo(tt.tr("Compiling binary translations..."))
    run_pybabel(["compile", "-D", DOMAIN, "-d", str(LOCALE_PATH)])


@i18n_app.command()
def clean(full: bool = False) -> None:
    """Delete .mo files and clear translation caches."""
    typer.echo(tt.tr("Cleaning translation files..."))

    count = 0
    for mo_file in LOCALE_PATH.rglob("*.mo"):
        mo_file.unlink()
        count += 1

    if full and TEMPLATE_FILE.exists():
        TEMPLATE_FILE.unlink()
        typer.echo(f"{TEMPLATE_FILE.name} deleted.")

    typer.secho(
        f"{tt.tr("Clean completed")}: {count} {tt.tr("files .mo deleted.")}",
        fg=typer.colors.GREEN,
    )


@i18n_app.command()
def rebuild(full: bool = False) -> None:
    """Clean, extract, update and compile."""
    clean(full=full)
    extract()
    update()
    compile()
    typer.secho(f"{tt.tr("Rebuild completed")}", fg=typer.colors.BRIGHT_CYAN)


@i18n_app.callback()
def cli() -> None:
    """Flai i18n management tool."""
    ...


if __name__ == "__main__":
    i18n_app()
