from typer import Exit

from flai import __version__


def version_callback(value: bool) -> None:
    if value:
        print(f"Flai version: {__version__}")
        raise Exit()
