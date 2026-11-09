#!/usr/bin/env python3
"""
Flai simple - sin imports complejos
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import click

@click.group()
def cli():
    """Flai Simple - Asistente para Flet"""
    pass

@cli.command()
@click.argument('model', default='deepseek-coder:1.3b')
def init(model):
    """Configurar modelo"""
    click.echo(f"✅ Flai configurado con: {model}")
    
    # Crear directorio .flai
    os.makedirs("app/.flai", exist_ok=True)
    
    # Guardar configuración
    import yaml
    config = {'model': model, 'project': 'app'}
    with open("app/.flai/config.yaml", 'w') as f:
        yaml.dump(config, f)
    
    click.echo(f"📁 Configuración guardada en app/.flai/")

@cli.command()
def analyze():
    """Analizar proyecto simple"""
    import subprocess
    
    click.echo("🔍 Analizando con DeepSeek-Coder...")
    
    # Consultar al modelo
    result = subprocess.run(
        ['ollama', 'run', 'deepseek-coder:1.3b', 'Analiza este proyecto Flet'],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode == 0:
        click.echo(f"\n🤖 Respuesta:\n{result.stdout}")
    else:
        click.echo(f"❌ Error: {result.stderr}")

if __name__ == "__main__":
    cli()

# Inicializar
# python flai_simple.py init deepseek-coder:1.3b --path app

# Analizar
# python flai_simple.py analyze --project app

# python flai_simple.py init deepseek-coder:1.3b --path app
# python flai_simple.py analyze --project app

# python -m flai.cli init deepseek-coder:1.3b --path app