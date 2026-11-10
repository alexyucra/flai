# flai/cli/commands/context.py
"""
flai context: gerencia as documentações (fontes de contexto) do projeto.
As mesmas operações estão no painel web: flai config → Contextos.
"""
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from flai.cli.console.console import console
from flai.core.context.context_manager import ContextManager
from flai.core.project import find_project_root

app = typer.Typer(help="Gerenciar documentações (contextos) usadas pela IA")


def _manager() -> ContextManager:
    root = find_project_root() or Path.cwd()
    return ContextManager(root)


@app.command("list")
def list_contexts():
    """Lista as documentações cadastradas."""
    contexts = _manager().list_contexts()
    table = Table(title="📚 Documentações")
    for col, style in (("ID", "cyan"), ("Nome", "green"), ("Tipo", "yellow"), ("Prior.", "white"),
                       ("Versão", "magenta"), ("Ativa", "white"), ("Índice", "dim")):
        table.add_column(col, style=style)
    for c in contexts:
        table.add_row(c["id"], c["name"][:34], c["type"], str(c["priority"]),
                      c.get("ref") or c.get("fetched_ref") or "-",
                      "✅" if c["enabled"] else "❌",
                      f"🔍 {c.get('rag_chunks', 0)} chunks" if c["rag_indexed"] else "⏳ não indexado")
    console.print(table)


@app.command("add")
def add_context(
    source_id: str = typer.Argument(..., help="ID (letras, números, _ ou -)"),
    name: str = typer.Option(..., "--name", "-n"),
    type: str = typer.Option(..., "--type", "-t", help="local_file | git_repo | url"),
    location: str = typer.Option(..., "--location", "-l", help="Arquivo/pasta, URL https ou repositório git"),
    description: str = typer.Option("", "--description", "-d"),
    ref: Optional[str] = typer.Option(None, "--ref", help="git: tag ou branch (ex.: v1.0.5)"),
    paths: Optional[str] = typer.Option(None, "--paths", help="git: subpastas separadas por vírgula"),
    priority: int = typer.Option(2, "--priority", "-p", help="1 = mais importante"),
    index: bool = typer.Option(False, "--index", help="Baixar e indexar em seguida"),
):
    """Cadastra uma documentação."""
    m = _manager()
    if not m.add_context(source_id, name, description or name, type, location,
                         ref=ref, paths=paths, priority=priority):
        console.print(f"[red]❌ {m.last_error}[/red]")
        raise typer.Exit(1)
    console.print(f"[green]✅ '{name}' cadastrada[/green]")
    if index:
        index_context(source_id)


@app.command("remove")
def remove_context(source_id: str = typer.Argument(...)):
    """Remove uma documentação e o seu índice."""
    if typer.confirm(f"Remover '{source_id}'?"):
        ok = _manager().remove_context(source_id)
        console.print("[green]✅ Removida[/green]" if ok else "[red]❌ Não encontrada (ou é o código do projeto)[/red]")


@app.command("enable")
def enable(source_id: str):
    """Ativa uma documentação nas respostas da IA."""
    console.print("✅" if _manager().set_enabled(source_id, True) else "❌ não encontrada")


@app.command("disable")
def disable(source_id: str):
    """Desativa uma documentação (o índice é mantido)."""
    console.print("✅" if _manager().set_enabled(source_id, False) else "❌ não encontrada")


@app.command("update")
def update_contexts(source_id: Optional[str] = typer.Argument(None),
                    force: bool = typer.Option(False, "--force", "-f")):
    """Baixa novamente o conteúdo (git/url)."""
    m = _manager()
    for sid in ([source_id] if source_id else list(m.sources)):
        ok = m.update_context(sid, force=force)
        console.print(f"{'✅' if ok else '❌'} {sid}" + ("" if ok else f": {m.last_error}"))


@app.command("index")
def index_context(source_id: str = typer.Argument(..., help="ID da documentação")):
    """Baixa (se preciso) e indexa para a busca da IA."""
    m = _manager()
    console.print(f"[dim]📚 Indexando '{source_id}' (pode levar alguns minutos)...[/dim]")
    if m.index_context(source_id, verbose=True):
        console.print(f"[green]✅ '{source_id}' indexada: {m.sources[source_id].rag_chunks} chunks[/green]")
    else:
        console.print(f"[red]❌ {m.last_error}[/red]")
        raise typer.Exit(1)


@app.command("check")
def check_versions():
    """Verifica se as documentações correspondem às versões instaladas (Flet, Fleting)."""
    drifts = _manager().check_versions()
    if not drifts:
        console.print("[green]✅ Documentações nas versões instaladas[/green]")
    for d in drifts:
        console.print(f"[yellow]⚠️ {d['id']}: {d['from']} → {d['to']}. Rode: flai context index {d['id']}[/yellow]")


@app.command("search")
def search_contexts(query: str = typer.Argument(...),
                    source: Optional[str] = typer.Option(None, "--source", "-s")):
    """Busca nas documentações indexadas."""
    results = _manager().search_contexts(query, [source] if source else None, k=3)
    if not results:
        console.print("[yellow]ℹ️ Nenhum resultado (as documentações estão indexadas?)[/yellow]")
    for i, r in enumerate(results[:8], 1):
        console.print(f"[bold cyan]{i}. {r['source_name']} › {r['source']}[/bold cyan] "
                      f"[dim]({r.get('similarity', 0):.0%})[/dim]")
        console.print(f"   {r['content'][:240].strip()}...\n")
