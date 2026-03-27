from typer import Exit

from flai import translations as tt

from flai import __version__


def version_callback(value: bool) -> None:
    if value:
        print(f"{tt.tr("Flai version")}: {__version__}")
        raise Exit()
