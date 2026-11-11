# flai/cli/commands/agent.py
"""
Comandos para gerenciar agentes do FLAI
"""
import typer

from flai.core.agents.agent_manager import AgentManager
from flai.cli.console.console import console
from rich.table import Table

app = typer.Typer(help="Gerenciar agentes do FLAI")

@app.command("list")
def list_agents(
    enabled_only: bool = typer.Option(True, "--enabled/--all", help="Mostrar apenas habilitados"),
    detail: bool = typer.Option(False, "--detail", "-d", help="Mostrar detalhes")
):
    """Lista todos os agentes disponíveis"""
    manager = AgentManager()
    agents = manager.list_agents(enabled_only=enabled_only)
    
    if not agents:
        console.print("[yellow]ℹ️ Nenhum agente encontrado[/yellow]")
        return
    
    table = Table(title="🎭 Agentes Disponíveis")
    table.add_column("Nome", style="cyan")
    table.add_column("Tipo", style="green")
    table.add_column("Prioridade", style="yellow")
    table.add_column("Triggers", style="white")
    table.add_column("Status", style="dim")
    
    for agent in agents:
        triggers = ", ".join(agent.triggers[:3])
        if len(agent.triggers) > 3:
            triggers += f" +{len(agent.triggers)-3}"
        
        table.add_row(
            agent.name,
            agent.type.value,
            agent.priority.name,
            triggers,
            "✅" if agent.enabled else "❌"
        )
    
    console.print(table)
    
    if detail:
        stats = manager.get_agent_stats()
        console.print(f"\n[dim]📊 Estatísticas:[/dim]")
        console.print(f"  Total: {stats['total_agents']}")
        console.print(f"  Habilitados: {stats['enabled_agents']}")
        console.print(f"  Builtin: {stats['builtin_agents']}")
        console.print(f"  Custom: {stats['custom_agents']}")
        console.print(f"  Intenções cobertas: {stats['intents_covered']}")

@app.command("show")
def show_agent(
    agent_name: str = typer.Argument(..., help="Nome do agente")
):
    """Mostra detalhes de um agente"""
    manager = AgentManager()
    agent = manager.get_agent(agent_name)
    
    if not agent:
        console.print(f"[red]❌ Agente '{agent_name}' não encontrado[/red]")
        return
    
    # Tenta carregar a instância
    instance = manager.load_agent_instance(agent_name)
    # Nem todo agente embutido declara get_capabilities(): usa os métodos públicos
    if instance is not None:
        if callable(getattr(instance, "get_capabilities", None)):
            capabilities = list(instance.get_capabilities())
        else:
            capabilities = sorted(n for n in dir(instance)
                                  if not n.startswith("_") and callable(getattr(instance, n, None)))
    else:
        capabilities = []
    caps_text = "\n".join(f"  • {c}" for c in capabilities) if instance else "  Agente não carregado"

    console.print(f"""
[bold cyan]Nome:[/bold cyan] {agent.name}
[bold green]Descrição:[/bold green] {agent.description}
[bold yellow]Tipo:[/bold yellow] {agent.type.value}
[bold blue]Módulo:[/bold blue] {agent.module_path}
[bold magenta]Classe:[/bold magenta] {agent.class_name}
[bold cyan]Prioridade:[/bold cyan] {agent.priority.name}
[bold white]Triggers:[/bold white] {', '.join(agent.triggers)}
[bold white]Dependências:[/bold white] {', '.join(agent.dependencies) or 'Nenhuma'}

[bold]Configuração:[/bold]
{chr(10).join(f'  • {k}: {v}' for k, v in agent.config.items()) if agent.config else '  Nenhuma'}

[bold]Capacidades (se carregado):[/bold]
{caps_text}
""")

@app.command("enable")
def enable_agent(
    agent_name: str = typer.Argument(..., help="Nome do agente")
):
    """Habilita um agente"""
    manager = AgentManager()
    
    if manager.enable_agent(agent_name, enabled=True):
        console.print(f"[green]✅ Agente '{agent_name}' habilitado[/green]")
    else:
        console.print(f"[red]❌ Agente '{agent_name}' não encontrado[/red]")

@app.command("disable")
def disable_agent(
    agent_name: str = typer.Argument(..., help="Nome do agente")
):
    """Desabilita um agente"""
    manager = AgentManager()
    
    if manager.enable_agent(agent_name, enabled=False):
        console.print(f"[yellow]⚠️ Agente '{agent_name}' desabilitado[/yellow]")
    else:
        console.print(f"[red]❌ Agente '{agent_name}' não encontrado[/red]")

@app.command("create")
def create_agent(
    name: str = typer.Argument(..., help="Nome do agente"),
    template: str = typer.Option("basic", "--template", "-t", help="Template: basic, rag, crud, form")
):
    """Cria um novo agente customizado usando template"""
    
    templates = {
        "basic": '''
class {class_name}(BaseAgent):
    """Agente customizado"""
    
    def __init__(self, project_path, config=None):
        super().__init__(project_path, config)
    
    def can_handle(self, intent, context=None):
        return False
    
    async def execute(self, intent, entity=None, fields=None, context=None):
        return {"success": True, "type": "custom_response", "content": "TODO"}
''',
        "rag": '''
from flai.core.rag.integrated_rag import IntegratedRAG

class {class_name}(BaseAgent):
    """Agente com suporte a RAG"""
    
    def __init__(self, project_path, config=None):
        super().__init__(project_path, config)
        self.rag = IntegratedRAG(project_path)
    
    def can_handle(self, intent, context=None):
        return intent in ["search", "where"]
    
    async def execute(self, intent, entity=None, fields=None, context=None):
        query = entity or context.get("user_query", "")
        results = self.rag.search(query)
        return {"success": True, "type": "search_results", "content": results}
''',
        "crud": '''
from flai.core.executors.fleting_executor import FletingExecutor

class {class_name}(BaseAgent):
    """Agente especializado em CRUD"""
    
    def __init__(self, project_path, config=None):
        super().__init__(project_path, config)
        self.executor = FletingExecutor(project_path)
    
    def can_handle(self, intent, context=None):
        return intent == "create_crud"
    
    async def execute(self, intent, entity=None, fields=None, context=None):
        if entity:
            self.executor.create_page(entity)
            self.executor.create_model(entity)
            return {"success": True, "type": "crud_created", "entity": entity}
        return {"success": False, "error": "No entity specified"}
'''
    }
    
    template_content = templates.get(template, templates["basic"])
    class_name = name.capitalize().replace("_", "") + "Agent"
    
    agent_code = template_content.format(class_name=class_name)
    
    manager = AgentManager()
    if manager.register_custom_agent(agent_code, name):
        console.print(f"[green]✅ Agente '{name}' criado com sucesso![/green]")
        console.print(f"[dim]Local: .flai/agents/custom/{name}/[/dim]")
        console.print(f"\n[bold]Próximos passos:[/bold]")
        console.print(f"  1. Edite o arquivo agent.py para implementar a lógica")
        console.print(f"  2. Configure os triggers no config.yaml")
        console.print(f"  3. Execute: flai agent enable {name}")
    else:
        console.print(f"[red]❌ Erro ao criar agente '{name}'[/red]")

@app.command("stats")
def agent_stats():
    """Mostra estatísticas dos agentes"""
    manager = AgentManager()
    stats = manager.get_agent_stats()
    
    console.print("[bold]📊 Estatísticas dos Agentes[/bold]\n")
    
    console.print(f"[cyan]Total de agentes:[/cyan] {stats['total_agents']}")
    console.print(f"[green]Habilitados:[/green] {stats['enabled_agents']}")
    console.print(f"[blue]Builtin:[/blue] {stats['builtin_agents']}")
    console.print(f"[yellow]Custom:[/yellow] {stats['custom_agents']}")
    console.print(f"[magenta]Intenções cobertas:[/magenta] {stats['intents_covered']}")
    
    console.print("\n[bold]Por Prioridade:[/bold]")
    for priority, count in stats["by_priority"].items():
        console.print(f"  • {priority}: {count} agentes")