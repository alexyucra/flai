# flai/cli/commands/context.py
"""
Comandos para gerenciar múltiplos contextos
"""
import typer
from pathlib import Path
from typing import Optional, List

from flai.core.context.context_manager import ContextManager
from flai.cli.console.console import console
from rich.table import Table

app = typer.Typer(help="Gerenciar contextos de conhecimento do FLAI")

@app.command("list")
def list_contexts():
    """Lista todas as fontes de contexto configuradas"""
    manager = ContextManager(Path.cwd())
    contexts = manager.list_contexts()
    
    if not contexts:
        console.print("[yellow]ℹ️ Nenhum contexto configurado[/yellow]")
        return
    
    table = Table(title="📚 Contextos Disponíveis")
    table.add_column("ID", style="cyan")
    table.add_column("Nome", style="green")
    table.add_column("Tipo", style="yellow")
    table.add_column("Status", style="white")
    table.add_column("RAG", style="dim")
    
    for ctx in contexts:
        status = "✅" if ctx["enabled"] else "❌"
        rag_status = "🔍" if ctx["rag_indexed"] else "⏳"
        
        table.add_row(
            ctx["id"],
            ctx["name"][:30],
            ctx["type"],
            status,
            rag_status
        )
    
    console.print(table)

@app.command("add")
def add_context(
    source_id: str = typer.Argument(..., help="ID único do contexto"),
    name: str = typer.Option(..., "--name", "-n", help="Nome do contexto"),
    description: str = typer.Option(..., "--description", "-d", help="Descrição"),
    type: str = typer.Option(..., "--type", "-t", help="Tipo: local_file, git_repo, url, project_code"),
    location: str = typer.Option(..., "--location", "-l", help="Localização (arquivo, URL, ou repo git)")
):
    """Adiciona uma nova fonte de contexto"""
    manager = ContextManager(Path.cwd())
    
    if manager.add_context(source_id, name, description, type, location):
        console.print(f"[green]✅ Contexto '{name}' adicionado![/green]")
        
        # Pergunta se quer indexar
        if typer.confirm("Deseja indexar este contexto para busca semântica?"):
            manager.index_context(source_id, verbose=True)
    else:
        console.print(f"[red]❌ Erro ao adicionar contexto[/red]")

@app.command("remove")
def remove_context(
    source_id: str = typer.Argument(..., help="ID do contexto a remover")
):
    """Remove uma fonte de contexto"""
    manager = ContextManager(Path.cwd())
    
    if typer.confirm(f"Remover contexto '{source_id}'?"):
        if manager.remove_context(source_id):
            console.print(f"[green]✅ Contexto '{source_id}' removido[/green]")
        else:
            console.print(f"[red]❌ Contexto não encontrado[/red]")

@app.command("update")
def update_contexts(
    source_id: Optional[str] = typer.Option(None, "--source", "-s", help="ID específico para atualizar"),
    all: bool = typer.Option(False, "--all", "-a", help="Atualizar todos os contextos")
):
    """Atualiza o conteúdo das fontes de contexto"""
    manager = ContextManager(Path.cwd())
    
    if source_id:
        if manager.update_context(source_id, force=True):
            console.print(f"[green]✅ Contexto '{source_id}' atualizado[/green]")
        else:
            console.print(f"[red]❌ Erro ao atualizar '{source_id}'[/red]")
    elif all:
        for source_id in manager.sources:
            if manager.update_context(source_id, force=True):
                console.print(f"[green]✅ {source_id} atualizado[/green]")
    else:
        console.print("[yellow]Use --source ou --all[/yellow]")

@app.command("index")
def index_context(
    source_id: str = typer.Argument(..., help="ID do contexto a indexar"),
    force: bool = typer.Option(False, "--force", "-f", help="Forçar reindexação")
):
    """Indexa um contexto para busca semântica (RAG)"""
    manager = ContextManager(Path.cwd())
    
    console.print(f"[dim]📚 Indexando '{source_id}' para busca semântica...[/dim]")
    
    if manager.index_context(source_id, verbose=True):
        console.print(f"[green]✅ Contexto '{source_id}' indexado![/green]")
    else:
        console.print(f"[red]❌ Erro ao indexar '{source_id}'[/red]")

@app.command("search")
def search_contexts(
    query: str = typer.Argument(..., help="Consulta de busca"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help="Buscar apenas nesta fonte")
):
    """Busca semanticamente nos contextos indexados"""
    manager = ContextManager(Path.cwd())
    
    sources = [source] if source else None
    results = manager.search_contexts(query, sources, k=5)
    
    if not results:
        console.print("[yellow]ℹ️ Nenhum resultado encontrado[/yellow]")
        return
    
    console.print(f"[bold green]🔍 Resultados para: '{query}'[/bold green]\n")
    
    for i, result in enumerate(results, 1):
        console.print(f"[bold cyan]{i}. Fonte: {result['source_name']}[/bold cyan]")
        console.print(f"   Score: {result.get('score', 0):.2%}")
        console.print(f"   {result['content'][:300]}...")
        console.print("")