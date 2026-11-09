import os
from pathlib import Path
from typing import List, Dict, Any

def build_context_map(scan_result: List[Any]) -> str:
    """
    Constrói um mapa de contexto seguro, lidando com strings ou dicionários.
    """
    if not scan_result:
        return "## 📁 Estrutura do Projeto\nNenhum arquivo encontrado para análise.\n"
    
    # Normalização: Garante que todos os itens sejam dicionários para o restante da lógica
    normalized_files = []
    for item in scan_result:
        if isinstance(item, dict):
            normalized_files.append(item)
        else:
            # Se for apenas uma string (caminho), cria um dicionário básico
            normalized_files.append({
                "path": str(item),
                "extension": os.path.splitext(str(item))[1].lower(),
                "size": 0  # Tamanho desconhecido para strings puras
            })

    # Organizar por tipo
    python_files = []
    config_files = []
    docs_files = []
    other_files = []
    
    for file_info in normalized_files:
        ext = file_info.get("extension", "").lower()
        
        if ext == ".py":
            python_files.append(file_info)
        elif ext in [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"]:
            config_files.append(file_info)
        elif ext in [".md", ".txt"]:
            docs_files.append(file_info)
        else:
            other_files.append(file_info)
    
    lines = ["## 📁 Estrutura do Projeto Fleting\n"]
    
    # Função auxiliar para renderizar seções para evitar repetição e erros de chave
    def add_section(title, files, show_size=False):
        if files:
            lines.append(f"\n### {title}")
            # Ordenação segura por path
            for f in sorted(files, key=lambda x: x.get("path", "")):
                path = f.get("path", "unknown")
                if show_size and f.get("size", 0) > 0:
                    size_kb = f["size"] / 1024
                    lines.append(f"- `{path}` ({size_kb:.1f} KB)")
                else:
                    lines.append(f"- `{path}`")

    add_section("📦 Código Python", python_files, show_size=True)
    add_section("⚙️ Arquivos de Configuração", config_files)
    add_section("📚 Documentação", docs_files)
    add_section("📄 Outros Arquivos", other_files)
    
    # Estatísticas seguras
    total_size = sum(f.get("size", 0) for f in normalized_files) / 1024
    lines.append(f"\n### 📊 Estatísticas")
    lines.append(f"- Total de arquivos: {len(normalized_files)}")
    lines.append(f"- Arquivos Python: {len(python_files)}")
    lines.append(f"- Tamanho total: {total_size:.1f} KB")
    
    return "\n".join(lines)