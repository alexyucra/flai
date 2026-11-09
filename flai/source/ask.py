"""
Comando ask para preguntas directas a DeepSeek-Coder
"""

import click
import subprocess
from pathlib import Path

def ask_model(question, project_path="."):
    """Pregunta directa al modelo optimizado"""
    
    project_path = Path(project_path).resolve()
    
    # Cargar configuración
    config_file = project_path / ".flai" / "config.yaml"
    if not config_file.exists():
        click.echo("❌ Proyecto no inicializado. Ejecuta: flai init")
        return
    
    import yaml
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    model_name = config.get('model', 'deepseek-coder:1.3b')
    optimized = config.get('optimized_for_low_ram', False)
    
    # Opciones según optimización
    options = []
    if optimized:
        options = ['--options', 'num_ctx=512,num_predict=128,num_threads=2']
    else:
        options = ['--options', 'num_ctx=2048,num_predict=512']
    
    # Crear prompt para código
    prompt = f"""Eres DeepSeek-Coder, especialista en código Python y Flet.

Pregunta: {question}

Responde en español, sé conciso y enfocado en código.
Si es apropiado, incluye ejemplos de código breves.
"""
    
    click.echo(f"🤔 Consultando a {model_name}...")
    
    try:
        # Ejecutar con timeout
        cmd = ['ollama', 'run', model_name] + options
        process = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )
        
        if process.returncode == 0:
            click.echo(f"\n🤖 DeepSeek-Coder:")
            click.echo("="*50)
            
            # Formatear respuesta de código
            response = process.stdout
            in_code_block = False
            
            for line in response.split('\n'):
                if '```' in line:
                    in_code_block = not in_code_block
                    click.echo(click.style(line, fg='cyan'))
                elif in_code_block:
                    click.echo(click.style(line, fg='green'))
                elif line.strip().startswith(('def ', 'class ', 'import ', 'from ')):
                    click.echo(click.style(line, fg='yellow'))
                else:
                    click.echo(line)
            
            click.echo("="*50)
            
        else:
            click.echo(f"❌ Error: {process.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        click.echo("⏰ Timeout: El modelo tardó demasiado.")
        click.echo("💡 Intenta una pregunta más corta o específica.")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}")