def build_context_map(scan_result: dict) -> str:
    lines = []

    lines.append("Projeto Fleting - Contexto Geral\n")

    if "app" in scan_result:
        lines.append("Estrutura app/:")
        lines.extend(render_tree(scan_result["app"], indent=2))

    if scan_result.get("configs"):
        lines.append("\nConfigs:")
        for cfg in scan_result["configs"]:
            lines.append(f"  - {cfg}")

    return "\n".join(lines)


def render_tree(tree: dict, indent=0):
    lines = []
    space = " " * indent

    for key, value in tree.items():
        if isinstance(value, dict):
            lines.append(f"{space}- {key}/")
            lines.extend(render_tree(value, indent + 2))
        else:
            lines.append(f"{space}- {key}")

    return lines
