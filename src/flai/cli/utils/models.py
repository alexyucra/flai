from typing import Dict, List

from flai import translations as tt


def get_laptop_models(
    system_info: Dict[str, int | str | float],
) -> List[Dict[str, str]]:
    ram = system_info["ram_gb"]

    models = [
        {
            "name": "DeepSeek-Coder 1.3B",
            "ollama_id": "deepseek-coder:1.3b",
            "ram": "2 GB",
            "description": tt.tr(
                "Specialist in code, ultra lightweight, ideal for limited hardware and Python/Flet analysis"
            ),
        },
        {
            "name": "Llama 3.2 3B",
            "ollama_id": "llama3.2:3b",
            "ram": "8 GB",
            "description": tt.tr("Light, fast, ideal for code"),
        },
        {
            "name": "Phi-3 Mini",
            "ollama_id": "phi3:mini",
            "ram": "8 GB",
            "description": tt.tr("Very fast, good for analysis"),
        },
        {
            "name": "Code Llama 7B",
            "ollama_id": "codellama:7b",
            "ram": "16 GB",
            "description": tt.tr("Excellent for large projects"),
        },
    ]

    if int(ram) < 16:
        return models[:2]

    return models
