def get_laptop_models(system_info):
    ram = system_info["ram_gb"]

    models = [
        {
            "name": "DeepSeek-Coder 1.3B",
            "ollama_id": "deepseek-coder:1.3b",
            "ram": "2 GB",
            "description": "Especialista em código, ultra leve, ideal para hardware limitado e análise de Python/Flet"
        },
        {
            "name": "Llama 3.2 3B",
            "ollama_id": "llama3.2:3b",
            "ram": "8 GB",
            "description": "Leve, rápido, ideal para código"
        },
        {
            "name": "Phi-3 Mini",
            "ollama_id": "phi3:mini",
            "ram": "8 GB",
            "description": "Muito rápido, bom para análise"
        },
        {
            "name": "Code Llama 7B",
            "ollama_id": "codellama:7b",
            "ram": "16 GB",
            "description": "Excelente para projetos grandes"
        },
    ]

    if ram < 16:
        return models[:2]

    return models
