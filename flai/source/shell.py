# fleting/flai/commands/shell.py
import typer
from pathlib import Path
import json

from flai.cli.console.console import console
from flai.core.project import get_project_root
from flai.cli.utils.scanner import scan_project
from flai.cli.utils.context import build_context_map
from flai.cli.utils.checklist import create_checklist
from flai.cli.utils.ollama_manager import get_ollama_manager

app = typer.Typer()
DEFAULT_PROJECT_NAME = "ia"

def validate_project_access(project_root: Path) -> bool:
    """Valida se estamos dentro de um projeto Fleting válido"""
    if not project_root:
        console.print("[error]❌ Diretório do projeto não encontrado[/error]")
        return False
    
    # Verificar se é um projeto Fleting
    if not (project_root / ".fleting").exists():
        console.print("[error]❌ Este não é um projeto Fleting válido[/error]")
        console.print("[info]Execute 'fleting init <nome>' para criar um projeto[/info]")
        return False
    
    # Verificar permissões de acesso
    try:
        # Tentar acessar o diretório
        test_file = project_root / ".flai_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        console.print("[error]❌ Sem permissão para acessar o projeto[/error]")
        return False
    except Exception as e:
        console.print(f"[error]❌ Erro ao acessar projeto: {e}[/error]")
        return False
    
    return True

def build_project_context(project_root: Path) -> str:
    """Constrói contexto específico do projeto"""
    
    # 1. Scan do projeto
    scan = scan_project(project_root)
    
    # 2. Context Map
    context_map = build_context_map(scan)
    
    # 3. Informações do projeto
    project_info = f"""
## 📁 Informações do Projeto Fleting
- **Nome:** {project_root.name}
- **Caminho:** {project_root}
- **Arquivos analisados:** {len(scan)}
- **Data da análise:** {Path(__file__).parent.parent.parent / "timestamp.txt"}

## 📋 Regras de Acesso
1. Este assistente só tem acesso à pasta do projeto: {project_root.name}
2. Não pode acessar arquivos fora deste diretório
3. Todas as sugestões devem ser baseadas nos arquivos encontrados acima
4. Recomendações devem focar em melhorias específicas do projeto

## 🎯 Foco da Análise
Analisar apenas os arquivos listados acima e sugerir:
- Melhorias de arquitetura MVC
- Boas práticas de Python/Flet
- Otimizações de código
- Estrutura de pastas
"""
    
    return project_info + "\n" + context_map

def handle_shell(project: str, model: str, context: str) -> None:
    """
    Abre o FLAI Shell restrito ao projeto Fleting atual
    """
    # 1. Obter e validar projeto
    project_path = get_project_root() 

    if not project_path or not validate_project_access(project_path):
        raise typer.Exit(1)

    config_path = project_path / ".flai" / "config.json"
    active_model = model # Fallback para o argumento passado
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                active_model = config_data.get("model", model)
                # Se no config o modelo for diferente do padrão 'flai-optimized', usamos o do config
        except Exception:
            pass

    console.print(f"[bold cyan]FLAI Shell - Projeto: {project_path.name}[/bold cyan]")
    console.print(f"[dim]Modelo ativo: {active_model}[/dim]\n")

    # 2. Preparar IA (usando cache para evitar verificações repetidas)
    console.print("🔍 Preparando IA local...")
    
    manager = get_ollama_manager()

    if not hasattr(manager, '_already_prepared'):
        if not manager.ensure_ready(active_model, verbose=True):
            console.print("[red]❌ Não foi possível preparar o Ollama[/red]")
            return
        manager._already_prepared = True
    else:
        if not manager.ensure_ready(active_model, verbose=False):
            return
        console.print("[dim]✅ IA preparada[/dim]")

    # 3. Construir contexto do projeto
    console.print("📊 Analisando estrutura do projeto...")
    project_context = build_project_context(project_path)
    
    # 4. Criar checklist
    checklist_file = create_checklist(project_path)
    console.print(f"[green]✅ Checklist criado em {checklist_file}[/green]")

    # 5. Prompt base com restrições
    system_prompt = f"""
Você é FLAI, um assistente de IA especializado em projetos Fleting (Python + Flet).

## 🎯 CONTEXTO DO PROJETO ATUAL:
{project_context}

## 📌 REGRAS ESTRITAS DE ACESSO:
1. Você só pode analisar os arquivos listados acima
2. Não pode acessar ou mencionar arquivos fora deste projeto
3. Todas as sugestões devem ser baseadas nos arquivos encontrados
4. Se um arquivo não estiver listado, você NÃO tem acesso a ele

## 🛠️ SUAS FUNÇÕES:
1. Analisar estrutura MVC do projeto
2. Sugerir melhorias de arquitetura
3. Identificar problemas de código
4. Recomendar boas práticas
5. Ajudar com padrões Flet

## ⚠️ LIMITAÇÕES:
- Não pode acessar sistema de arquivos além do projeto
- Não pode executar comandos
- Não pode modificar arquivos diretamente

## 🎪 EXEMPLO DE RESPOSTA:
"Com base nos arquivos do projeto {project_path.name}, notei que..."
"As seguintes melhorias são possíveis para os arquivos encontrados..."
"Nos arquivos analisados, sugiro..."

Agora, responda baseado APENAS nos arquivos listados acima:
"""

    # 6. Análise inicial usando quick_run (evita mensagens duplicadas)
    console.print("[info]Analisando projeto com IA...[/info]")

    try:
        response = manager.quick_run(active_model, system_prompt + "Analise a estrutura e dê sugestões.")
        
        if response and not response.startswith("Erro"):
            console.print("\n[bold]📋 Análise Inicial:[/bold]\n")
            console.print(response)
    except Exception as e:
        console.print(f"[error]Erro ao analisar projeto: {e}[/error]")

    # 7. Loop interativo com restrições
    console.print("\n[dim]Digite 'exit' para sair[/dim]")
    console.print("[dim]Suas perguntas serão respondidas baseadas apenas nos arquivos do projeto[/dim]\n")
    
    while True:
        try:
            user_input = console.input("\n🤖 [bold cyan]Você[/bold cyan]: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'sair', 'q']:
                console.print("[yellow]👋 Até logo![/yellow]")
                break
            
            if not user_input: continue

            # Adicionar contexto de restrição à pergunta
            restricted_prompt = f"""
            {system_prompt}
            
            PERGUNTA DO USUÁRIO: {user_input}
            
            LEMBRE-SE: Responda baseado APENAS nos arquivos listados no contexto do projeto.
            Se não tiver informações suficientes nos arquivos, diga: 
            "Não encontrei informações sobre isso nos arquivos do projeto."
            """

            console.print("[dim]Processando...[/dim]", end="")
            response = manager.quick_run(active_model, f"{system_prompt}\nPERGUNTA: {user_input}")
            console.print(f"\n🤖 [bold green]FLAI:[/bold green] {response}")
            
            if response and not response.startswith("Não foi possível"):
                console.print(f"\n🤖 [bold green]FLAI:[/bold green] {response}")
            else:
                console.print(f"\n🤖 [dim]FLAI: {response}[/dim]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ Interrompido pelo usuário[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]❌ Erro: {e}[/red]")
