# flai/cli/commands/config.py
"""
Comando para gerenciar configuração do FLAI via interface (web ou terminal)
"""
import typer
from pathlib import Path
from typing import Optional
import webbrowser
import json

from flai.core.config import create_default_config, load_config, validate_config, FlaiConfig
from flai.cli.console.console import console
from flai.core.project import get_project_root
from pydantic import ValidationError
from datetime import datetime

app = typer.Typer(help="Gerenciar configuração do FLAI")

# Servidor web (será importado apenas quando necessário)
_web_server = None

def _get_web_server(project_path: Path, port: int):
    """Obtém ou cria instância do servidor web (importação tardia)"""
    global _web_server
    
    if _web_server is None:
        try:
            from flai.web.server import FLAIWebServer
            # Garantir que project_path é Path
            if isinstance(project_path, str):
                project_path = Path(project_path)
            _web_server = FLAIWebServer(project_path, port)
        except ImportError as e:
            console.print(f"[red]❌ Erro ao carregar servidor web: {e}[/red]")
            console.print("[dim]Certifique-se que o Flet está instalado: pip install flet[/dim]")
            return None
    
    return _web_server

def web_start(
    port: int = 8080, 
    no_browser: bool = False, 
    project: Optional[str] = None
):
    """Inicia o servidor web de configuração"""
    # Converte project para Path corretamente
    if project and project != ".":
        project_path = Path(project).resolve()
    else:
        project_path = get_project_root()
    
    if not project_path:
        console.print("[red]❌ Nenhum projeto Fleting encontrado[/red]")
        console.print("[dim]Execute em um diretório com projeto Fleting ou use --project[/dim]")
        raise typer.Exit(1)
    
    # Garantir que é Path
    if isinstance(project_path, str):
        project_path = Path(project_path)
    
    console.print(f"[cyan]🌐 Iniciando servidor de configuração em http://localhost:{port}[/cyan]")
    console.print(f"[dim]📁 Projeto: {project_path}[/dim]")
    
    if not no_browser:
        webbrowser.open(f"http://localhost:{port}")
    
    server = _get_web_server(project_path, port)
    if server:
        server.start(open_browser=not no_browser)
    else:
        console.print("[red]❌ Falha ao iniciar servidor web[/red]")
        raise typer.Exit(1)

def config_show(key: Optional[str] = None):
    """Mostra a configuração atual do FLAI"""
    config_file = Path.cwd() / ".flai" / "config.json"
    
    if not config_file.exists():
        console.print("[yellow]⚠️ Arquivo de configuração não encontrado[/yellow]")
        console.print(f"[dim]Execute 'flai init' primeiro[/dim]")
        return

    try:
        # config = json.loads(config_file.read_text(encoding='utf-8'))
        config = load_config(config_file, "flai")
        if config is None:
            console.print("[red]❌ Configuração inválida![/red]")
            console.print("[dim]Execute 'flai config init' para recriar[/dim]")
            return
        
        if key:
            if hasattr(config, key):
                console.print(f"{key}: {getattr(config, key)}")
            else:
                console.print(f"[yellow]Chave '{key}' não encontrada[/yellow]")
        else:
            console.print("[bold cyan]📋 Configuração do FLAI[/bold cyan]")
            # for k, v in config.items():
            #     console.print(f"  [green]{k}:[/green] {v}")
            console.print("[bold cyan]📋 Configuração do FLAI[/bold cyan]")
            console.print(f"  [green]versão:[/green] {config.version}")
            console.print(f"  [green]projeto:[/green] {config.project_name}")
            console.print(f"  [green]modelo:[/green] {config.model}")
            console.print(f"  [green]temperature:[/green] {config.temperature}")
            console.print(f"  [green]RAG:[/green] {'✅' if config.rag.enabled else '❌'}")
            console.print(f"  [green]web:[/green] http://{config.web_host}:{config.web_port}")
                
    except Exception as e:
        console.print(f"[red]❌ Erro ao ler configuração: {e}[/red]")

def config_set(key: str, value: str):
    """Define um valor na configuração"""
    config_file = Path.cwd() / ".flai" / "config.json"
    
    if not config_file.exists():
        console.print("[yellow]⚠️ Arquivo de configuração não encontrado[/yellow]")
        console.print(f"[dim]Execute 'flai init' primeiro[/dim]")
        return
    
    try:
        # config = json.loads(config_file.read_text(encoding='utf-8'))
        # config[key] = value
        # config_file.write_text(json.dumps(config, indent=2), encoding='utf-8')
        # console.print(f"[green]✅ {key} = {value}[/green]")
        config = load_config(config_file, "flai")
        if config is None:
            console.print("[red]❌ Configuração atual é inválida[/red]")
            return

        if hasattr(config, key):
            # Converter tipo baseado no campo
            field_info = FlaiConfig.model_fields.get(key)
            if field_info:
                annotation = field_info.annotation
                if annotation == int:
                    value = int(value)
                elif annotation == float:
                    value = float(value)
                elif annotation == bool:
                    value = value.lower() in ('true', '1', 'yes', 'on')
            
            setattr(config, key, value)
            config.updated_at = datetime.now().isoformat()

            try:
                config.model_validate(config.model_dump())
                # Salvar
                config_file.write_text(config.to_json(), encoding='utf-8')
                console.print(f"[green]✅ {key} = {value}[/green]")
            except ValidationError as e:
                console.print(f"[red]❌ Valor inválido: {e}[/red]")
        else:
            console.print(f"[yellow]Chave '{key}' não existe[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Erro ao salvar configuração: {e}[/red]")

def config_unset(key: str):
    """Remove uma chave da configuração"""
    config_file = Path.cwd() / ".flai" / "config.json"
    
    if not config_file.exists():
        console.print("[yellow]⚠️ Arquivo de configuração não encontrado[/yellow]")
        return
    
    try:
        config = json.loads(config_file.read_text(encoding='utf-8'))
        
        if key in config:
            del config[key]
            config_file.write_text(json.dumps(config, indent=2), encoding='utf-8')
            console.print(f"[green]✅ Chave '{key}' removida[/green]")
        else:
            console.print(f"[yellow]⚠️ Chave '{key}' não encontrada[/yellow]")
            
    except Exception as e:
        console.print(f"[red]❌ Erro ao remover configuração: {e}[/red]")

def config_init(force: bool = False):
    """Inicializa a configuração padrão do FLAI"""
    config_file = Path.cwd() / ".flai" / "config.json"
    
    if config_file.exists() and not force:
        console.print("[yellow]⚠️ Configuração já existe. Use --force para sobrescrever[/yellow]")
        return
    
    config = create_default_config(Path.cwd())
    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(config.to_json(), encoding='utf-8')
    
    console.print("[green]✅ Configuração padrão criada e validada![/green]")
    console.print(f"[dim]Local: {config_file}[/dim]")
    # default_config = {
    #     "model": "flai-coder",
    #     "project_path": str(Path.cwd()),
    #     "version": "1.0.0",
    #     "rag_enabled": True,
    #     "auto_index": True,
    #     "web_port": 8080,
    #     "web_enabled": True
    # }
    
    # config_file.parent.mkdir(parents=True, exist_ok=True)
    # config_file.write_text(json.dumps(default_config, indent=2), encoding='utf-8')
    
    # console.print("[green]✅ Configuração padrão criada![/green]")
    # console.print(f"[dim]Local: {config_file}[/dim]")

def config_list():
    """Lista todas as configurações disponíveis (alias para 'show')"""
    config_show()

def config_edit():
    """Abre o arquivo de configuração no editor padrão"""
    import subprocess
    import sys
    
    config_file = Path.cwd() / ".flai" / "config.json"
    
    if not config_file.exists():
        console.print("[yellow]⚠️ Arquivo de configuração não encontrado[/yellow]")
        console.print("[dim]Execute 'flai config init' primeiro[/dim]")
        return
    
    # Abre no editor padrão
    if sys.platform == "win32":
        subprocess.run(["notepad", str(config_file)])
    elif sys.platform == "darwin":
        subprocess.run(["open", "-t", str(config_file)])
    else:
        subprocess.run(["xdg-open", str(config_file)])

# Função principal para processar comandos
def handle_config(
    action: str = "start",
    port: int = 8080,
    no_browser: bool = False,
    project: Optional[str] = None,
    key: Optional[str] = None,
    value: Optional[str] = None,
    force: bool = False
):
    """Função principal para processar comandos de configuração"""
    
    if action == "start":
        web_start(port, no_browser, project)
    elif action == "show":
        config_show(key)
    elif action == "set" and key and value:
        config_set(key, value)
    elif action == "unset" and key:
        config_unset(key)
    elif action == "init":
        config_init(force)
    elif action == "list":
        config_list()
    elif action == "edit":
        config_edit()
    else:
        console.print("[yellow]Comandos disponíveis:[/yellow]")
        console.print("  flai config start           - Inicia servidor web")
        console.print("  flai config show            - Mostra configuração")
        console.print("  flai config set <key> <val> - Define valor")
        console.print("  flai config unset <key>     - Remove chave")
        console.print("  flai config init            - Cria configuração padrão")
        console.print("  flai config list            - Lista configurações")
        console.print("  flai config edit            - Edita no editor")