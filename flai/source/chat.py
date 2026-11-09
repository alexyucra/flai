import subprocess
import click
import sys
import yaml
import os
import json
from pathlib import Path

def query_engine(model, prompt, context="", timeout=60):
    """Motor de consulta unificado com suporte a contexto e otimização"""
    try:
        # Configuração para Windows (evita abrir janelas de terminal)
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        # Prompt final com instruções de sistema integradas
        full_prompt = f"{context}\n\nResponde en español de forma concisa:\n{prompt}"
        
        # Executa via subprocess.run para capturar saída de forma síncrona
        # Usamos 'ollama run' diretamente para simplicidade
        result = subprocess.run(
            ['ollama', 'run', model, full_prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            creationflags=creation_flags
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"❌ Erro no Ollama: {result.stderr[:200]}"

    except subprocess.TimeoutExpired:
        return "⏰ O modelo demorou muito para responder. Tente algo mais curto."
    except Exception as e:
        return f"⚠️ Erro inesperado: {str(e)[:200]}"


def chat_with_ai(project, model_name="deepseek-coder:1.3b", context_extra=None):
    """Interface de Chat Unificada do FLAI"""
    project_path = Path(project).resolve()
    config_file = project_path / ".flai" / "config.json" # Alterado para JSON conforme seu setup anterior

    if not config_file.exists():
        click.echo(click.style("❌ FLAI não inicializado. Execute 'flai init'.", fg='red'))
        return

    # Carregar configuração (modelo base ou otimizado)
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    model_name = config.get('model', 'flai-coder')
    
    click.echo(click.style(f"\n🚀 FLAI INTERACTIVE CHAT", fg='cyan', bold=True))
    click.echo(f"📁 Projeto: {project_path.name}")
    click.echo(f"🤖 Modelo: {model_name}")
    click.echo(click.style("Comandos: 'sair' para fechar | 'limpar' para resetar contexto\n", fg='white', dim=True))

    history = []
    
    while True:
        try:
            user_input = input(click.style("❓ Você: ", fg='yellow', bold=True)).strip()

            if user_input.lower() in ['salir', 'exit', 'quit', 'q', 'sair']:
                click.echo(click.style("\n👋 Até logo!", fg='cyan'))
                break
            
            if user_input.lower() == 'limpar':
                history = []
                click.echo("🧹 Histórico de conversa limpo.")
                continue

            if not user_input:
                continue

            # Construção de Contexto Dinâmico
            context = "Contexto: Você é o FLAI, assistente especialista em Python e Flet.\n"
            if history:
                # Mantém apenas as últimas 2 trocas para economizar RAM do ThinkPad
                last_exchanges = history[-2:]
                context += "Histórico recente:\n" + "\n".join([f"P: {h[0]}\nR: {h[1]}" for h in last_exchanges])

            click.echo(click.style("💭 Pensando...", fg='magenta'))
            
            # Chamada ao motor unificado
            response = query_engine(model_name, user_input, context)

            # Salva no histórico
            history.append((user_input, response))

            # Interface de saída elegante
            click.echo(f"\n{click.style('🤖 FLAI:', fg='green', bold=True)}")
            click.echo("─" * 50)
            
            # Formatação de Cores para Código
            for line in response.split('\n'):
                if '```' in line:
                    click.echo(click.style(line, fg='cyan'))
                elif any(line.strip().startswith(x) for x in ['def ', 'class ', 'import ', 'from ']):
                    click.echo(click.style(line, fg='blue'))
                elif line.strip().startswith('#'):
                    click.echo(click.style(line, fg='white', dim=True))
                else:
                    click.echo(line)
            
            click.echo("─" * 50 + "\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            click.echo(f"❌ Erro: {e}")
            continue