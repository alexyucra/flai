from typing import Dict, List

from flai import translations as tt


def build_context_map(scan_result: Dict[str, Dict[str, str] | List[str]]) -> str:
    lines: List[str] = []

    lines.append(f"{tt.tr("Fleting Project - General Context")}\n")

    if "app" in scan_result:
        lines.append(f"{tt.tr("Structure app/:")}")
        app = scan_result["app"]
        if isinstance(app, Dict):
            lines.extend(render_tree(app, indent=2))

    if scan_result.get("configs"):
        lines.append(f"\n{tt.tr("Configs:")}:")
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
