#!/usr/bin/env python3
"""
Flai Analyze Safe - Versión con encoding correcto
"""

import subprocess
import sys
from pathlib import Path
import click

def safe_ollama_query(model, prompt, timeout=45):
    """Consulta segura a Ollama con UTF-8"""
    try:
        # Configurar para Windows
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
        
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Reemplaza caracteres inválidos
            timeout=timeout,
            creationflags=creation_flags
        )
        return result
    except subprocess.TimeoutExpired:
        return type('obj', (object,), {
            'returncode': 1,
            'stdout': '',
            'stderr': 'Timeout: El modelo tardó demasiado'
        })()
    except Exception as e:
        return type('obj', (object,), {
            'returncode': 1,
            'stdout': '',
            'stderr': f'Error: {str(e)}'
        })()

@click.command()
@click.option('--project', '-p', default='app')
def analyze(project):
    """Analizar proyecto con encoding seguro"""
    
    project_path = Path(project).resolve()
    
    click.echo("🔍 ANALIZANDO PROYECTO (modo seguro)")
    click.echo("="*50)
    
    # Contar archivos
    py_files = list(project_path.rglob("*.py"))
    
    if not py_files:
        click.echo("❌ No hay archivos .py")
        return
    
    # Buscar archivos Flet
    flet_files = []
    flet_examples = []
    
    for file in py_files[:15]:  # Solo primeros 15
        try:
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if 'import flet' in content or 'from flet import' in content:
                    flet_files.append(file)
                    
                    # Extraer ejemplo breve
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'ft.' in line or 'flet.' in line:
                            example = line.strip()[:80]
                            if example and len(flet_examples) < 3:
                                flet_examples.append(f"{file.name}: {example}")
                            break
        except:
            pass
    
    # Mostrar estadísticas
    click.echo(f"📁 Proyecto: {project_path.name}")
    click.echo(f"📍 Ruta: {project_path}")
    click.echo(f"📄 Archivos Python: {len(py_files)}")
    click.echo(f"🎯 Archivos Flet: {len(flet_files)}")
    
    if flet_files:
        click.echo(f"\n🏗️ Archivos Flet encontrados ({len(flet_files)}):")
        for file in flet_files[:5]:
            rel_path = file.relative_to(project_path)
            click.echo(f"   • {rel_path}")
        
        if flet_examples:
            click.echo(f"\n💡 Ejemplos de código Flet:")
            for example in flet_examples:
                click.echo(f"   {example}")
    
    # Consultar al modelo
    click.echo(f"\n🤖 CONSULTANDO A DEEPSEEK-CODER...")
    
    # Cargar modelo de configuración
    config_file = project_path / ".flai" / "config.yaml"
    model_name = "flai-optimized"  # Por defecto
    
    if config_file.exists():
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            model_name = config.get('model', 'flai-optimized')
    
    # Crear prompt
    prompt = f"""Analiza este proyecto Python/Flet:

- Total archivos Python: {len(py_files)}
- Archivos que usan Flet: {len(flet_files)}
- Archivos Flet: {[f.name for f in flet_files[:3]]}

Proporciona:
1. Tipo de aplicación que podría ser
2. 2 sugerencias de mejora
3. 1 recomendación de estructura

Responde en español, máximo 150 palabras."""

    click.echo(f"   Modelo: {model_name}")
    click.echo("   Procesando...")
    
    # Consultar de forma segura
    result = safe_ollama_query(model_name, prompt)
    
    if result.returncode == 0 and result.stdout:
        click.echo(f"\n💡 ANÁLISIS DEL MODELO:")
        click.echo("="*50)
        
        # Mostrar respuesta limpia
        response = result.stdout.strip()
        
        # Dividir en líneas y mostrar
        lines = response.split('\n')
        for line in lines:
            line = line.rstrip()
            if line:
                # Resaltar secciones
                if line.strip().startswith(('1.', '2.', '3.', '-', '•')):
                    click.echo(click.style(line, fg='green'))
                elif 'recomendación' in line.lower() or 'sugerencia' in line.lower():
                    click.echo(click.style(line, fg='yellow'))
                elif '```' in line:
                    click.echo(click.style(line, fg='cyan'))
                else:
                    click.echo(line)
        
        click.echo("="*50)
        
        # Sugerir próximos pasos
        click.echo(f"\n🎯 PRÓXIMOS PASOS:")
        click.echo("   1. Usa 'flai chat' para preguntas específicas")
        click.echo("   2. Revisa los archivos Flet encontrados")
        click.echo("   3. Pide ayuda para código específico")
        
    else:
        click.echo(f"❌ El modelo no respondió")
        if result.stderr:
            click.echo(f"   Error: {result.stderr[:100]}")
    
    click.echo(f"\n✅ Análisis completado")

if __name__ == "__main__":
    analyze()