import sys
import typer
from typing import Optional
import click
import json
from pathlib import Path
from flai.cli.commands.init import handle_init
from flai.cli.console.console import console
from flai.cli.console import Table, Panel, Text, box, Rule
import traceback
from flai.core.logging import setup_logging, get_logger

setup_logging(log_level="INFO", log_file=Path.home() / "flai" / "logs" / "flai.log")
logger = get_logger(__name__)

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

def print_help():
    console.clear()

    console.print()
    console.rule("[bold cyan]🚀 Flai CLI[/bold cyan]", style="cyan")
    console.print()
    
    console.print(Panel.fit(
        "[bold green]flai <command> [options][/bold green]",
        title="[yellow]📌 Usage[/yellow]",
        border_style="yellow",
        padding=(1, 2)
    ))
    console.print()
    
    table = Table(
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        border_style="blue",
        padding=(0, 1)
    )
    
    table.add_column("Command", style="bold green", width=36)
    table.add_column("Description", style="cyan", width=44)
    
    # Comandos organizados por categorías
    categories = {
        "💼 Project Commands": [
            ("flai init ia", "Setup local AI environment"),
            ("flai shell", "Start interactive AI shell"),
            ("flai history", "Show conversation history")
        ],

        "📚 Knowledge & Context": [
            ("flai context list", "List registered contexts"),
            ("flai context add", "Add knowledge context"),
            ("flai context search", "Search context"),
            ("flai context index", "Index context into RAG")
        ],

        "🧠 RAG Commands": [
            ("flai rag index", "Build semantic index"),
            ("flai rag search", "Semantic search"),
            ("flai rag stats", "Show RAG statistics"),
            ("flai rag clear", "Clear vector database")
        ],

        "🤖 Agent Commands": [
            ("flai agent list", "List agents"),
            ("flai agent show <nome>", "Show agent details"),
            ("flai agent create", "Create custom agent"),
            ("flai agent stats", "Show agent statistics")
        ],

        "🎯 Intent Commands": [
            ("flai intent list", "List supported intents"),
            ("flai intent test \"<frase>\"", "Test which intent a phrase triggers")
        ],

        "⚙️ Config Commands": [
            ("flai config", "Open web config panel"),
            ("flai config show [chave]", "Show configuration"),
            ("flai config set <chave> <valor>", "Set configuration value"),
            ("flai config unset <chave>", "Remove configuration value"),
            ("flai config edit", "Edit configuration"),
            ("flai config init [--force]", "Initialize configuration")
        ]
    }
    
    for category, commands in categories.items():
        # Añadir separador para categorías
        if list(categories.keys()).index(category) > 0:
            table.add_row("─" * 36, "─" * 44, style="dim")
        
        # Añadir título de categoría
        table.add_row(
            f"[bold yellow]{category}[/bold yellow]",
            "",
            style="yellow"
        )
        
        # Añadir comandos de la categoría
        for cmd, desc in commands:
            table.add_row(f"  {cmd}", desc)
    
    console.print(table)
    console.print()
    
def show_banner():
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
            border_style="cyan"
        )
    )

def show_footer():
    console.print(
        Panel(
            "💡 Curtiu o Flai?\n"
            "Ajude a liberar novas features 🚀\n\n"
            "[bold yellow]Meta: 2000 inscritos[/bold yellow]\n"
            "👉 https://www.youtube.com/@LatinDev\n",
            border_style="green"
        )
    )

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='0.1.0', prog_name='flai')
@click.pass_context
def cli(ctx):
    """
    Flai - Local AI Framework for Python project analysis and development
    
    \b
    Main commands:
    - init ia : Initialize AI environment
    - shell   : Interactive AI shell
    - chat    : Interactive chat about projects
    - analyze : Analyze Python/Flet projects
    """
    # Store context for child commands
    ctx.ensure_object(dict)
    
    # Show banner only if not help command
    # if not any(arg in sys.argv for arg in ['--help', '-h', 'help']):
    #     show_banner()

@cli.command() # init
@click.argument('model', default='flai-ai')
@click.option('--path', '-p', default='.', help='Project path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose mode')
def init(model: str, path: str, verbose: bool):
    """Inicializar Flai con modelo AI para análisis"""
    handle_init(model, path, verbose)

@cli.command() # shell
@click.option('--project', '-p', default='.', help='Reference project')
@click.option('--model', '-m', default=None, help='AI model for chat')
@click.option('--session', '-s', help='Session name for history')
def shell(project: str, model: Optional[str], session: Optional[str]):
    """Iniciar REPL com IA (RAG + Histórico)"""
    from flai.cli.commands.shell_unified import handle_shell_unified
    handle_shell_unified(project, model, session)

@cli.command() # rag commands
@click.argument('action', type=click.Choice(['index', 'search', 'stats', 'clear']))
@click.option('--query', '-q', help='Search query (for search action)')
@click.option('--project', '-p', default='.', help='Project path')
def rag(action: str, query: Optional[str], project: str):
    """Gerenciar RAG (busca semântica no código)"""
    from flai.core.rag.integrated_rag import IntegratedRAG
    from flai.core.project import get_project_root
    
    project_path = Path(project).resolve()
    root = get_project_root() or project_path
    
    rag = IntegratedRAG(root, auto_index=False)
    
    if action == 'index':
        click.echo("📚 Indexando projeto...")
        if rag.rag.index_project(verbose=True):
            click.echo("✅ Indexação concluída!")
        else:
            click.echo("❌ Falha na indexação. LangChain instalado?")
    
    elif action == 'search':
        if not query:
            click.echo("❌ Use --query para buscar")
            return
        click.echo(f"🔍 Buscando: {query}")
        results = rag.search(query)
        for i, r in enumerate(results, 1):
            click.echo(f"\n{i}. {Path(r['source']).name}")
            click.echo(f"   Score: {(1 - r['score']):.2%}")
            click.echo(f"   {r['content'][:200]}...")
    
    elif action == 'stats':
        stats = rag.get_stats()
        click.echo(json.dumps(stats, indent=2))
    
    elif action == 'clear':
        if rag.rag.clear_index(verbose=True):
            click.echo("✅ Índice limpo")

@cli.command() # history commands
@click.option('--project', '-p', default='.', help='Project path')
@click.option('--session', '-s', help='Session name')
@click.option('--export', '-e', help='Export to file')
def history(project: str, session: Optional[str], export: Optional[str]):
    """Gerenciar histórico de conversas"""
    from flai.cli.repl_unified import ConversationHistory
    from flai.core.project import get_project_root
    
    project_path = Path(project).resolve()
    root = get_project_root() or project_path
    
    if export:
        hist = ConversationHistory(root, session)
        output = Path(export)
        exported = hist.export_to_markdown(output)
        click.echo(f"✅ Histórico exportado para: {exported}")
    else:
        # Lista sessões disponíveis
        sessions_dir = root / ".flai" / "sessions"
        if sessions_dir.exists():
            sessions = list(sessions_dir.glob("session_*.md"))
            if sessions:
                click.echo("📜 Sessões disponíveis:")
                for s in sessions:
                    size = s.stat().st_size
                    click.echo(f"  • {s.name} ({size} bytes)")
            else:
                click.echo("ℹ️ Nenhuma sessão encontrada")
        else:
            click.echo("ℹ️ Nenhuma sessão encontrada")

CONFIG_ACTIONS = ['start', 'show', 'set', 'unset', 'init', 'list', 'edit']


@cli.command()
@click.argument('action', required=False, default='start', type=click.Choice(CONFIG_ACTIONS))
@click.argument('key', required=False)
@click.argument('value', required=False)
@click.option('--port', default=8080, help='Porta do painel (start)')
@click.option('--no-browser', is_flag=True, help='Não abrir o navegador (start)')
@click.option('--project', '-p', default=None, help='Caminho do projeto (start)')
@click.option('--force', '-f', is_flag=True, help='Sobrescrever configuração existente (init)')
def config(action: str, key: Optional[str], value: Optional[str], port: int,
           no_browser: bool, project: Optional[str], force: bool):
    """Configuração: start (painel web, padrão) | show [chave] | set <chave> <valor> |
    unset <chave> | init [--force] | list | edit"""
    from flai.cli.commands.config import handle_config
    if action == 'set' and (not key or value is None):
        raise click.UsageError("Uso: flai config set <chave> <valor>")
    if action == 'unset' and not key:
        raise click.UsageError("Uso: flai config unset <chave>")
    handle_config(action=action, port=port, no_browser=no_browser, project=project,
                  key=key, value=value, force=force)


def _typer_group(name: str, module: str, help_text: str):
    """
    Registra um app Typer (flai/cli/commands/<module>.py) como subcomando do CLI Click.
    O Typer embute o próprio Click, então os argumentos são repassados ao app.
    """
    @cli.command(name=name, help=help_text,
                 context_settings={"ignore_unknown_options": True, "allow_extra_args": True,
                                   "help_option_names": []})
    @click.pass_context
    def _cmd(ctx):
        import importlib
        app = importlib.import_module(f"flai.cli.commands.{module}").app
        app(args=ctx.args or ["--help"], prog_name=f"flai {name}")
    return _cmd


# Documentações gerenciadas (mesmas operações do painel web)
_typer_group("context", "context",
             "Documentações usadas pela IA: list | add | index | search | check | enable | disable | remove")
_typer_group("agent", "agent", "Agentes: list | show | enable | disable | create | stats")
_typer_group("intent", "intent",
             "Intenções: list | show | add | remove | pattern-add | keyword-add | enable | "
             "disable | test | export | import")

def main():

    try:
        if len(sys.argv) == 1 or sys.argv[1] in ('-h', '--help', 'help'):
            print_help()
            return
        
        cli()
        
    except click.Abort:
        logger.info("Comando abortado pelo usuário")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        traceback.print_exc()
        sys.exit(1)
    # finally:
        # show_footer()

if __name__ == "__main__":
    main()
