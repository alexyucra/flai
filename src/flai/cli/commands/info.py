from typer import Context, Typer

from flai import translations as tt

info_app = Typer(name="info", invoke_without_command=True, no_args_is_help=True)


@info_app.callback(invoke_without_command=True, help=tt.tr("Show system information."))
def info_callback(
    ctx: Context,
) -> None: ...
