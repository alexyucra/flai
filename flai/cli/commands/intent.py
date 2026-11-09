# flai/cli/commands/intent.py
"""
Comandos para gerenciar intenções do FLAI
"""
import typer
from pathlib import Path
from typing import Optional, List

from flai.core.intent.intent_manager import IntentManager, IntentDefinition, IntentPriority
from flai.cli.console.console import console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer(help="Gerenciar intenções do FLAI")

@app.command("list")
def list_intents(
    enabled_only: bool = typer.Option(True, "--enabled/--all", help="Mostrar apenas habilitadas"),
    detail: bool = typer.Option(False, "--detail", "-d", help="Mostrar detalhes completos")
):
    """Lista todas as intenções disponíveis"""
    manager = IntentManager()
    intents = manager.list_intents(enabled_only=enabled_only)
    
    if not intents:
        console.print("[yellow]ℹ️ Nenhuma intenção encontrada[/yellow]")
        return
    
    if detail:
        # Modo detalhado
        for intent in intents:
            content = f"""
[bold cyan]Nome:[/bold cyan] {intent.name}
[bold green]Descrição:[/bold green] {intent.description}
[bold yellow]Prioridade:[/bold yellow] {intent.priority.name}
[bold blue]Handler:[/bold blue] {intent.handler or 'N/A'}
[bold magenta]Exige entidade:[/bold magenta] {'✅' if intent.requires_entity else '❌'}

[bold]Padrões regex:[/bold]
{chr(10).join(f'  • {p}' for p in intent.patterns[:3])}
{f'  ... e mais {len(intent.patterns)-3}' if len(intent.patterns) > 3 else ''}

[bold]Palavras-chave:[/bold]
{', '.join(intent.keywords[:5])}{'...' if len(intent.keywords) > 5 else ''}

[bold]Exemplos:[/bold]
{chr(10).join(f'  • {e}' for e in intent.examples[:3])}
"""
            console.print(Panel(content, title=f"📋 {intent.name}", border_style="cyan"))
            console.print("")
    else:
        # Modo tabela
        table = Table(title="🎯 Intenções Disponíveis")
        table.add_column("Nome", style="cyan")
        table.add_column("Descrição", style="green")
        table.add_column("Prioridade", style="yellow")
        table.add_column("Status", style="white")
        
        for intent in intents:
            status = "✅" if intent.enabled else "❌"
            table.add_row(
                intent.name,
                intent.description[:50] + ("..." if len(intent.description) > 50 else ""),
                intent.priority.name,
                status
            )
        
        console.print(table)
    
    console.print(f"\n[dim]Total: {len(intents)} intenções[/dim]")

@app.command("show")
def show_intent(
    intent_name: str = typer.Argument(..., help="Nome da intenção")
):
    """Mostra detalhes de uma intenção específica"""
    manager = IntentManager()
    intent = manager.get_intent(intent_name)
    
    if not intent:
        console.print(f"[red]❌ Intenção '{intent_name}' não encontrada[/red]")
        return
    
    content = f"""
[bold cyan]ID:[/bold cyan] {intent.name}
[bold green]Descrição:[/bold green] {intent.description}
[bold yellow]Prioridade:[/bold yellow] {intent.priority.name}
[bold blue]Handler:[/bold blue] {intent.handler or 'Não definido'}
[bold magenta]Exige entidade:[/bold magenta] {'✅ Sim' if intent.requires_entity else '❌ Não'}
[bold cyan]Criada em:[/bold cyan] {intent.created_at}
[bold cyan]Atualizada em:[/bold cyan] {intent.updated_at}

[bold]📝 Padrões Regex ({len(intent.patterns)}):[/bold]
{chr(10).join(f'  {i+1}. {p}' for i, p in enumerate(intent.patterns))}

[bold]🔑 Palavras-chave ({len(intent.keywords)}):[/bold]
{', '.join(intent.keywords)}

[bold]📚 Exemplos ({len(intent.examples)}):[/bold]
{chr(10).join(f'  • {e}' for e in intent.examples)}

[bold]📦 Metadados:[/bold]
{chr(10).join(f'  • {k}: {v}' for k, v in intent.metadata.items()) if intent.metadata else '  Nenhum'}
"""
    console.print(Panel(content, title=f"🔍 Intenção: {intent.name}", border_style="cyan"))

@app.command("add")
def add_intent(
    name: str = typer.Argument(..., help="Nome da intenção"),
    description: str = typer.Option(..., "--description", "-d", help="Descrição"),
    patterns: List[str] = typer.Option(..., "--pattern", "-p", help="Padrão regex (pode repetir)"),
    keywords: List[str] = typer.Option(..., "--keyword", "-k", help="Palavra-chave (pode repetir)"),
    priority: str = typer.Option("normal", "--priority", help="Prioridade: highest, high, normal, low, lowest"),
    requires_entity: bool = typer.Option(False, "--requires-entity", "-e", help="Exige extração de entidade"),
    handler: Optional[str] = typer.Option(None, "--handler", "-h", help="Nome do handler no RouterAgent")
):
    """Adiciona uma nova intenção"""
    manager = IntentManager()
    
    # Converte prioridade
    priority_map = {
        "highest": IntentPriority.HIGHEST,
        "high": IntentPriority.HIGH,
        "normal": IntentPriority.NORMAL,
        "low": IntentPriority.LOW,
        "lowest": IntentPriority.LOWEST
    }
    
    intent = IntentDefinition(
        name=name,
        description=description,
        patterns=patterns,
        keywords=keywords,
        priority=priority_map.get(priority, IntentPriority.NORMAL),
        requires_entity=requires_entity,
        handler=handler
    )
    
    if manager.add_intent(intent):
        console.print(f"[green]✅ Intenção '{name}' adicionada![/green]")
    else:
        console.print(f"[red]❌ Intenção '{name}' já existe[/red]")

@app.command("remove")
def remove_intent(
    intent_name: str = typer.Argument(..., help="Nome da intenção"),
    force: bool = typer.Option(False, "--force", "-f", help="Forçar remoção")
):
    """Remove uma intenção"""
    manager = IntentManager()
    
    # Lista de intenções padrão que não devem ser removidas
    protected = ["create_crud", "create_form", "create_page", "analyze", "where", "help", "exit"]
    
    if intent_name in protected and not force:
        console.print(f"[red]❌ Intenção '{intent_name}' é uma intenção padrão. Use --force para remover[/red]")
        return
    
    if manager.delete_intent(intent_name):
        console.print(f"[green]✅ Intenção '{intent_name}' removida[/green]")
    else:
        console.print(f"[red]❌ Intenção '{intent_name}' não encontrada[/red]")

@app.command("pattern-add")
def add_pattern(
    intent_name: str = typer.Argument(..., help="Nome da intenção"),
    pattern: str = typer.Argument(..., help="Padrão regex a adicionar")
):
    """Adiciona um padrão regex a uma intenção"""
    manager = IntentManager()
    
    if manager.add_pattern(intent_name, pattern):
        console.print(f"[green]✅ Padrão adicionado à intenção '{intent_name}'[/green]")
    else:
        console.print(f"[red]❌ Intenção '{intent_name}' não encontrada[/red]")

@app.command("keyword-add")
def add_keyword(
    intent_name: str = typer.Argument(..., help="Nome da intenção"),
    keyword: str = typer.Argument(..., help="Palavra-chave a adicionar")
):
    """Adiciona uma palavra-chave a uma intenção"""
    manager = IntentManager()
    
    if manager.add_keyword(intent_name, keyword):
        console.print(f"[green]✅ Palavra-chave adicionada à intenção '{intent_name}'[/green]")
    else:
        console.print(f"[red]❌ Intenção '{intent_name}' não encontrada[/red]")

@app.command("enable")
def enable_intent(
    intent_name: str = typer.Argument(..., help="Nome da intenção")
):
    """Habilita uma intenção"""
    manager = IntentManager()
    
    if manager.enable_intent(intent_name, enabled=True):
        console.print(f"[green]✅ Intenção '{intent_name}' habilitada[/green]")
    else:
        console.print(f"[red]❌ Intenção '{intent_name}' não encontrada[/red]")

@app.command("disable")
def disable_intent(
    intent_name: str = typer.Argument(..., help="Nome da intenção")
):
    """Desabilita uma intenção"""
    manager = IntentManager()
    
    if manager.enable_intent(intent_name, enabled=False):
        console.print(f"[yellow]⚠️ Intenção '{intent_name}' desabilitada[/yellow]")
    else:
        console.print(f"[red]❌ Intenção '{intent_name}' não encontrada[/red]")

@app.command("test")
def test_intent(
    text: str = typer.Argument(..., help="Texto para testar"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostrar detalhes")
):
    """Testa qual intenção corresponde a um texto"""
    manager = IntentManager()
    
    intent_name, entity = manager.match_intent(text)
    
    if intent_name:
        intent = manager.get_intent(intent_name)
        console.print(f"[green]✅ Intenção detectada: {intent_name}[/green]")
        if entity:
            console.print(f"[cyan]📌 Entidade: {entity}[/cyan]")
        
        # Sugere campos
        fields = manager.extract_fields(text)
        if fields:
            console.print(f"[yellow]📝 Campos detectados: {', '.join(fields)}[/yellow]")
        
        if verbose and intent:
            console.print(f"\n[dim]Descrição: {intent.description}[/dim]")
            console.print(f"[dim]Handler: {intent.handler}[/dim]")
    else:
        console.print("[red]❌ Nenhuma intenção detectada[/red]")
        
        # Sugere intenções similares
        suggestions = manager.suggest_intents(text)
        if suggestions:
            console.print("\n[dim]💡 Intenções similares:[/dim]")
            for name, score in suggestions:
                console.print(f"  • {name} ({(score * 100):.0f}% similar)")

@app.command("export")
def export_intents(
    output: Path = typer.Option(..., "--output", "-o", help="Arquivo de saída"),
    format: str = typer.Option("yaml", "--format", "-f", help="Formato: yaml ou json")
):
    """Exporta todas as intenções para backup"""
    manager = IntentManager()
    export_data = manager.export_intents(format)
    
    output.write_text(export_data, encoding='utf-8')
    console.print(f"[green]✅ Intenções exportadas para {output}[/green]")

@app.command("import")
def import_intents(
    input: Path = typer.Option(..., "--input", "-i", help="Arquivo de importação"),
    format: str = typer.Option("auto", "--format", "-f", help="Formato: auto, yaml ou json"),
    force: bool = typer.Option(False, "--force", help="Substituir intenções existentes")
):
    """Importa intenções de um backup"""
    if not input.exists():
        console.print(f"[red]❌ Arquivo {input} não encontrado[/red]")
        return
    
    data = input.read_text(encoding='utf-8')
    
    # Detecta formato automaticamente
    if format == "auto":
        if data.strip().startswith('{'):
            format = "json"
        else:
            format = "yaml"
    
    manager = IntentManager()
    
    if force:
        # Limpa intenções existentes (exceto padrão?)
        pass
    
    count = manager.import_intents(data, format)
    console.print(f"[green]✅ {count} intenções importadas[/green]")