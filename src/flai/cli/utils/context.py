from typing import Dict, List


def build_context_map(scan_result: Dict[str, Dict[str, str] | List[str]]) -> str:
    lines: List[str] = []

    lines.append("Projeto Fleting - Contexto Geral\n")

    if "app" in scan_result:
        lines.append("Estrutura app/:")
        app = scan_result["app"]
        if isinstance(app, Dict):
            lines.extend(render_tree(app, indent=2))

    if scan_result.get("configs"):
        lines.append("\nConfigs:")
        for cfg in scan_result["configs"]:
            lines.append(f"  - {cfg}")

    return "\n".join(lines)


def render_tree(tree: Dict[str, str], indent: int = 0) -> List[str]:
    lines: List[str] = []
    space = " " * indent

    for key, value in tree.items():
        if isinstance(value, dict):
            lines.append(f"{space}- {key}/")
            lines.extend(render_tree(value, indent + 2))
        else:
            lines.append(f"{space}- {key}")

    return lines
