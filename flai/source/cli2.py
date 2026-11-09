#!/usr/bin/env python3
"""
CLI principal para Flai - Analizador de proyectos Python Flet
"""

import sys
import click
from pathlib import Path

# Añadir el directorio padre al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from flai.cli.commands.init import init_project
from flai.cli.commands.analyze import analyze_project
from flai.cli.commands.chat import chat_with_ai

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version='1.0.0')
def cli():
    """Flai - Asistente AI para análisis de proyectos Python Flet"""
    pass

@cli.command()
@click.argument('model', default='flai-optimized', 
                type=click.Choice(['flai-optimized', 'deepseek-coder', 'deepseek-coder:1.3b', 'phi3-mini', 'codellama']))
@click.option('--path', '-p', default='.', help='Ruta del proyecto a analizar')
def init(model, path):
    """Inicializar Flai con modelo AI para análisis"""
    init_project(model, path)  # SOLO 2 ARGUMENTOS

@cli.command()
@click.argument('target', default='.', type=click.Path(exists=True))
@click.option('--full', '-f', is_flag=True, help='Análisis completo del proyecto')
@click.option('--report', '-r', is_flag=True, help='Generar reporte en markdown')
def analyze(target, full, report):
    """Analizar proyecto Python/Flet"""
    analyze_project(target, full, report)

@cli.command()
@click.option('--project', '-p', default='.', help='Proyecto de referencia')
def chat(project):
    """Iniciar chat interactivo con AI sobre el proyecto"""
    chat_with_ai(project)

if __name__ == '__main__':
    cli()