from typer import Typer

info_app = Typer(name="info", invoke_without_command=True, no_args_is_help=True)


@info_app.callback(invoke_without_command=True)
def info_callback() -> None:
    """
    System Info
    """
    print("Hello, Default!")
