# Al principio del archivo, añadir:
import subprocess
import sys

# Función segura para llamar a Ollama
def safe_ollama_run(model, prompt):
    """Ejecutar Ollama con encoding correcto"""
    try:
        result = subprocess.run(
            ['ollama', 'run', model, prompt],
            capture_output=True,
            text=True,
            encoding='utf-8',  # IMPORTANTE
            errors='replace',  # Reemplazar caracteres inválidos
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        return result
    except Exception as e:
        return None

# Luego en analyze_project, usar safe_ollama_run en vez de subprocess.run directamente