import typer
from pathlib import Path

from flai.cli.console.console import console
from flai.cli.utils.system import analyze_system
from flai.cli.utils.models import get_laptop_models
from flai.cli.utils.ollama import install_ollama, pull_model
from rich.table import Table
# from flai.core.project import get_project_root

app = typer.Typer()
DEFAULT_PROJECT_NAME = "app"

def handle_init(model: str, path: str, verbose: bool = False) -> None:
    """
    Initialize local AI environment (LangChain + Ollama) for Fleting project
    
    Args:
        model: AI model to use (passed from CLI but we'll let user choose)
        path: Project path where to initialize
        verbose: Verbose output mode
    """
    try:
        # Convert to absolute path
        project_root = Path(path).resolve()
        
        if verbose:
            console.print(f"[dim]🔍 Verbose mode enabled[/dim]")
            console.print(f"[dim]📁 Project path: {project_root}[/dim]")
            console.print(f"[dim]🤖 Model argument: {model}[/dim]")
        
        # Check if it's a Fleting project (or create structure)
        fleting_project = project_root / DEFAULT_PROJECT_NAME
        if not fleting_project.exists():
            console.print(f"[yellow]⚠️ Fleting project not found at: {fleting_project}[/yellow]")
            console.print(f"[dim]Creating project structure...[/dim]")
            fleting_project.mkdir(parents=True, exist_ok=True)
        
        console.print("[bold cyan]🚀 Initializing Flai (Local AI Framework)[/bold cyan]\n")
        
        # 1. Analyze system
        console.print("[bold]📊 Analyzing system...[/bold]")
        system_info = analyze_system()
        
        if verbose:
            console.print(f"[dim]System: {system_info}[/dim]")
        
        # 2. Show checklist
        console.print("\n[bold]✅ System Checklist:[/bold]")
        for item, ok in system_info["checklist"].items():
            icon = "✅" if ok else "❌"
            console.print(f"{icon} {item}")
        
        if not system_info["checklist"].get("RAM suficiente", True):
            console.print("[yellow]⚠️ Low RAM detected - performance may be affected[/yellow]")
        
        # 3. Show available models
        console.print("\n[bold]🤖 Available AI Models for your system:[/bold]")
        models = get_laptop_models(system_info)
        
        if not models:
            console.print("[red]❌ No compatible models found for your system[/red]")
            return
        
        # Create rich table for model selection
        table = Table(
            title="📋 Recommended Models for Your Laptop",
            title_style="bold cyan"
        )
        
        table.add_column("#", justify="center", style="bold yellow", width=6)
        table.add_column("Model", style="bold green")
        table.add_column("Min RAM", justify="center", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Ollama ID", style="dim")
        
        for i, model_info in enumerate(models, start=1):
            table.add_row(
                str(i),
                model_info["name"],
                model_info.get("ram", "N/A"),
                model_info.get("description", "AI model"),
                model_info.get("ollama_id", "unknown")
            )
        
        console.print(table)
        
        # 4. User selection
        try:
            choice = typer.prompt(
                "Select model number",
                type=int,
                default=1
            )
            
            if choice < 1 or choice > len(models):
                console.print(f"[red]❌ Invalid choice. Please select 1-{len(models)}[/red]")
                return
            
            selected = models[choice - 1]
            
        except (KeyboardInterrupt, typer.Abort):
            console.print("\n[yellow]⚠️ Installation cancelled by user[/yellow]")
            return
        
        console.print(f"\n[bold cyan]📦 Installing model: {selected['name']}[/bold cyan]")
        
        # 5. Install Ollama if needed
        console.print("[dim]🔧 Checking Ollama installation...[/dim]")
        install_ollama()
        
        # 6. Pull the selected model
        ollama_id = selected.get("ollama_id")
        if not ollama_id:
            console.print(f"[red]❌ No Ollama ID found for model {selected['name']}[/red]")
            return
        
        console.print(f"[dim]📥 Pulling model: {ollama_id} (this may take a few minutes)[/dim]")
        pull_model(ollama_id)
        
        # 7. Create configuration file
        import json
        config_file = project_root / ".flai" / "config.json"
        config_file.parent.mkdir(exist_ok=True)
        
        config = {
            "model": selected["name"],
            "ollama_id": ollama_id,
            "project_path": str(project_root),
            "version": "0.1.0",
            "system_info": {
                "ram_gb": system_info.get("ram_gb", 0),
                "gpu_available": system_info.get("gpu_available", False)
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]✅ Configuration saved to: {config_file}[/green]")
        
        # 8. Success message
        console.print("\n[bold green]✨ AI Local installed successfully![/bold green]")
        console.print("\n[bold]📌 Next steps:[/bold]")
        console.print(f"  [dim]1. Run:[/dim] [cyan]flai shell[/cyan]")
        console.print(f"  [dim]2. Or:[/dim] [cyan]flai analyze[/cyan]")
        console.print(f"  [dim]3. Or:[/dim] [cyan]flai chat[/cyan]")
        
        if verbose:
            console.print(f"\n[dim]Installation details:[/dim]")
            console.print(f"  Model: {selected['name']}")
            console.print(f"  Path: {project_root}")
            console.print(f"  Config: {config_file}")
        
    except Exception as e:
        console.print(f"[red]❌ Error initializing Flai: {str(e)}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise

