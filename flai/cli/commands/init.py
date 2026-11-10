# flai/cli/commands/init.py
import typer
import sys
import json
import psutil
import subprocess

from pathlib import Path
from datetime import datetime

# Importações do seu projeto
from flai.core.config import create_default_config, FlaiConfig
from flai.core.config.schemas import validate_config
from flai.core.platform import get_user_config_dir, normalize_path
from flai.cli.utils.system import get_system_info
from flai.cli.utils.models import get_laptop_models
from flai.cli.utils.ollama_manager import get_ollama_manager
from flai.core.project import get_project_root
from flai.cli.console.console import console
from rich.table import Table
from rich.panel import Panel

app = typer.Typer()
DEFAULT_PROJECT_NAME = "ia"

_GITIGNORE_ENTRIES = [".flai/sessions/", ".flai/vectordb/", ".flai/contexts/", "*.log"]


def _ensure_gitignore(project_root: Path) -> None:
    """Adiciona ao .gitignore do projeto os dados locais gerados pelo FLAI."""
    gitignore = project_root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    missing = [e for e in _GITIGNORE_ENTRIES if e not in existing]
    if missing:
        with open(gitignore, "a", encoding="utf-8") as f:
            if existing and existing[-1].strip():
                f.write("\n")
            f.write("# FLAI (dados locais)\n" + "\n".join(missing) + "\n")


def handle_init(model_arg: str = None, path: str = ".", verbose: bool = False) -> None:
    """
    Inicializa o ambiente de IA local (Ollama) integrando o OllamaManager.
    """
    flai_config_dir = get_user_config_dir()
    try:
        console.print(Panel.fit(
            "🚀 [bold cyan]FLAI[/bold cyan] - Inicializando Setup de IA Local",
            border_style="cyan"
        ))

        # 1. Definir caminhos e verificar estrutura
        project_root = Path(path).resolve()
        project_root_str = normalize_path(str(project_root))
        # fleting_project = project_root / DEFAULT_PROJECT_NAME
        fleting_project = get_project_root()
        
        if not fleting_project.exists():
            if verbose: console.print(f"[dim]📁 Criando estrutura em: {fleting_project}[/dim]")
            fleting_project.mkdir(parents=True, exist_ok=True)

        # 2. Análise de Sistema via OllamaManager
        manager = get_ollama_manager()
        system_info = get_system_info() # Assume-se que esta função retorna o dict básico
        status = manager.check_system()
        
        table = Table(title="📊 Status do Sistema")
        table.add_column("Componente", style="cyan")
        table.add_column("Status", justify="center")

        # Verificação de RAM (Lógica do handle_init2/3)
        ram_gb = psutil.virtual_memory().total / (1024**3)
        ram_status = "✅" if ram_gb >= 7.5 else "⚠️"
        table.add_row(f"RAM Total ({ram_gb:.1f} GB)", ram_status)
        
        # Verificação Ollama
        table.add_row("Ollama Instalado", "✅" if status["ollama_found"] else "❌")
        console.print(table)

        if not status["ollama_found"]:
            console.print("\n[red]❌ Ollama não detectado![/red]")
            console.print("Por favor, instale o Ollama em: [bold]https://ollama.com[/bold]")
            return

        # 3. Garantir que o Servidor está rodando
        if not status["server_running"]:
            with console.status("[bold yellow]Iniciando servidor Ollama...[/bold yellow]"):
                if manager.start_server():
                    console.print("✅ Servidor iniciado com sucesso!")
                else:
                    console.print("[red]❌ Falha ao iniciar servidor automaticamente.[/red]")
                    console.print("[dim]Tente executar 'ollama serve' manualmente em outro terminal.[/dim]")
                    return

        # 4. Seleção de Modelo (Dinâmica)
        model_table = Table(title="🤖 Modelos Recomendados")
        model_table.add_column("ID", style="bold yellow")
        model_table.add_column("Modelo", style="green")
        model_table.add_column("Requisito", style="dim")
        model_table.add_column("Uso Ideal", style="white")

        # Opções baseadas na RAM disponível
        if ram_gb < 4:
            model_table.add_row("1", "deepseek-coder:1.3b", "1.5GB RAM", "Ultra-leve / Código")
            options = {"1": "deepseek-coder:1.3b"}
        else:
            model_table.add_row("1", "llama3.2:3b", "4GB RAM", "Equilibrado / Chat")
            model_table.add_row("2", "phi3:mini", "4GB RAM", "Rápido / Lógica")
            model_table.add_row("3", "deepseek-coder:1.3b", "1.5GB RAM", "Especialista em Código")
            options = {
                "1": "llama3.2:3b",
                "2": "phi3:mini",
                "3": "deepseek-coder:1.3b"
            }

        console.print(model_table)
        
        choice = typer.prompt("Selecione o número do modelo desejado", default="1")
        selected_model = options.get(choice, options["1"])

        # 5. Instalação do Modelo via Manager
        console.print(f"\n[bold]📥 Preparando modelo base:[/bold] [cyan]{selected_model}[/cyan]")
        if manager.install_model(selected_model, verbose=True):
            
            # --- NOVO: Lógica de Otimização PowerShell ---
            optimized_model_name = "flai-coder"
            script_path = Path(__file__).parent.parent / "helpers" / "optimize_model.ps1"
            
            if script_path.exists():
                console.print("[yellow]⚙️ Otimizando modelo para o hardware detectado...[/yellow]")
                try:
                    result = subprocess.run([
                        "powershell.exe", "-ExecutionPolicy", "Bypass", "-File",
                        str(script_path), selected_model, optimized_model_name
                    ], capture_output=True, text=True, check=True)
                    
                    # CRITICAL: Se o PowerShell funcionou, atualizamos o nome para o JSON
                    selected_model = optimized_model_name 
                    console.print(f"[green]✅ Otimização concluída: {selected_model}[/green]")
                except Exception as e:
                    console.print(f"[red]⚠️ Erro na otimização: {e.stderr}[/red]")
                    console.print("[yellow]Usando modelo base como fallback.[/yellow]")
            # ----------------------------------------------
            
            console.print(f"✅ Modelo {selected_model} pronto para uso!")
        else:
            console.print(f"[red]⚠️ Erro no pull do modelo.[/red]")

        # 6. Salvar Configuração (COM VALIDAÇÃO)
        config_dir = project_root / ".flai"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.json"

        config = create_default_config(project_root, selected_model)

        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config.to_json())

        # Auditoria PRIV-02: histórico de conversas e índices não devem ir para o git
        _ensure_gitignore(project_root)

        # config_data = {
        #     "model": selected_model,  # Salva 'flai-coder' se a otimização funcionou
        #     "project_path": str(project_root),
        #     "setup_date": datetime.now().isoformat(),
        #     "ollama_path": status["ollama_path"],
        #     "optimized_for_low_ram": ram_gb < 8,
        #     "status": "ready"
        # }

        # with open(config_file, 'w', encoding='utf-8') as f:
        #     json.dump(config_data, f, indent=4)

        valid, instance, errors = validate_config(config_file, "flai")
        if not valid:
            console.print("[red]❌ Configuração gerada é inválida![/red]")
            for error in errors:
                console.print(f"  [red]• {error}[/red]")
            return
        
        console.print(f"\n[green]✅ Configuração salva e validada em: {config_file}[/green]")
        console.print(Panel(
            f"✨ [bold]Setup Concluído![/bold]\n\n"
            f"Modelo: {config.model}\n"
            f"Projeto: {config.project_name}\n\n"
            f"Para começar, use:\n"
            f"[bold cyan]flai shell[/bold cyan]",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"\n[red]❌ Erro crítico no init: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
