import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Union
from flai.core.logging import get_logger

logger = get_logger(__name__)

# Configurações globais de filtro
ALLOWED_EXTENSIONS = {
    '.py', '.md', '.txt', '.json', '.yaml', '.yml', 
    '.toml', '.ini', '.cfg', '.env', '.gitignore'
}

IGNORE_DIRS = {
    '__pycache__', '.git', '.venv', 'venv', 'env',
    'node_modules', '.idea', '.vscode', 'build',
    'dist', '.pytest_cache', '.mypy_cache'
}

IGNORE_FILES = {
    '.DS_Store', 'thumbs.db', 'desktop.ini'
}

def is_valid_file(path: Path) -> bool:
    """Verifica se é um arquivo ou diretório permitido para análise"""
    # Se algum componente do caminho estiver na lista de ignorados
    if any(part in IGNORE_DIRS for part in path.parts):
        return False
    
    if path.is_file():
        # Verificar se é arquivo explicitamente ignorado
        if path.name in IGNORE_FILES:
            return False
        # Verificar extensão
        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            return False
            
    return True

def summarize_file(path: Path, max_lines: int = 30) -> str:
    """Lê o início do arquivo para fornecer contexto à IA"""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[:max_lines])
    except UnicodeDecodeError as e:
        logger.warning(f"Erro de encoding em {path}: {e}")
        return f"[Erro de encoding: não foi possível ler {path.name}]"
    except PermissionError as e:
        logger.warning(f"Sem permissão para ler {path}: {e}")
        return f"[Sem permissão: {path.name}]"
    except Exception as e:
        logger.error(f"Erro inesperado ao ler {path}: {e}", exc_info=True)
        return f"[Erro ao ler conteúdo: {str(e)[:100]}]"

def list_files(base: Path) -> List[str]:
    """Lista apenas nomes de arquivos válidos em um diretório (sem recursão)"""
    if not base.exists():
        return []
    return [
        f.name for f in base.iterdir() 
        if f.is_file() and is_valid_file(f)
    ]

def scan_dir(base: Path) -> Dict[str, Any]:
    """Escaneia um diretório recursivamente"""
    structure = {}

    if not base.exists():
        logger.warning(f"Diretório não existe: {base}")
        return structure

    if not base.is_dir():
        logger.warning(f"Não é um diretório: {base}")
        return structure

    for item in base.iterdir():
        try:
            if not is_valid_file(item):
                continue

            if item.is_dir():
                structure[item.name] = scan_dir(item)
            else:
                structure[item.name] = summarize_file(item)
        except PermissionError as e:
            logger.warning(f"Sem permissão para acessar {item}: {e}")
            structure[item.name] = "[Sem permissão de acesso]"
        except Exception as e:
            logger.error(f"Erro ao processar {item}: {e}", exc_info=True)
            structure[item.name] = f"[Erro: {str(e)[:50]}]"

    return structure

def scan_project(project_root: Union[str, Path]) -> Dict[str, Any]:
    """Ponto de entrada principal - Unifica análise"""
    root = Path(project_root).resolve()
    
    logger.info(f"Iniciando scan do projeto: {root}")
    
    result = {
        "project_name": root.name,
        "app": {},
        "configs": [],
        "root_files": []
    }

    try:
        app_dir = root / "app"
        if app_dir.exists():
            result["app"] = scan_dir(app_dir)
        else:
            logger.info(f"Pasta /app não encontrada em {root}")
            result["app"] = "Pasta /app não encontrada"

        configs_dir = root / "configs"
        if configs_dir.exists():
            result["configs"] = list_files(configs_dir)

        result["root_files"] = list_files(root)
        
        logger.info(f"Scan concluído: {len(result['root_files'])} arquivos na raiz")
        
    except Exception as e:
        logger.error(f"Erro fatal no scan do projeto: {e}", exc_info=True)
        result["error"] = str(e)
    
    return result