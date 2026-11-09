# test_security.py
import sys
from pathlib import Path

# Adicionar ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flai.cli.commands.shell2 import validate_project_access, build_project_context
from flai.core.project import get_project_root

# Testar em um projeto Fleting
project_path = get_project_root()
if project_path:
    print(f"Projeto encontrado: {project_path}")
    
    # Testar validação
    if validate_project_access(project_path):
        print("✅ Acesso validado com sucesso")
        
        # Testar contexto
        context = build_project_context(project_path)
        print("\n📋 Contexto gerado (primeiras 500 caracteres):")
        print(context[:500] + "...")
    else:
        print("❌ Falha na validação de acesso")
else:
    print("❌ Nenhum projeto Fleting encontrado")
    print("Execute: fleting init meu_projeto")