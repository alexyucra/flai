def get_laptop_models(system_info):
    """Retorna modelos recomendados baseados na RAM do sistema"""
    ram = system_info.get("ram_gb", 0)
    
    # Todos os modelos disponíveis
    all_models = [
        {
            "name": "Llama 3.2 3B",
            "ollama_id": "llama3.2:3b",
            "ram": "8 GB",
            "description": "Leve, rápido, ideal para código",
            "priority": 1
        },
        {
            "name": "Phi-3 Mini",
            "ollama_id": "phi3:mini",
            "ram": "8 GB",
            "description": "Muito rápido, bom para análise",
            "priority": 2
        },
        {
            "name": "Phi-3 Medium",
            "ollama_id": "phi3:medium",
            "ram": "12 GB",
            "description": "Equilíbrio entre tamanho e capacidade",
            "priority": 3
        },
        {
            "name": "Code Llama 7B",
            "ollama_id": "codellama:7b",
            "ram": "16 GB",
            "description": "Excelente para projetos grandes",
            "priority": 4
        },
        {
            "name": "Mistral 7B",
            "ollama_id": "mistral:7b",
            "ram": "16 GB",
            "description": "Bom para textos gerais",
            "priority": 5
        },
    ]
    
    # Filtrar por RAM disponível
    if ram < 8:
        # RAM muito baixa - apenas modelos muito leves
        return [all_models[1]]  # Apenas Phi-3 Mini
    
    elif ram < 12:
        # 8-12 GB
        return all_models[:2]  # Llama 3.2 3B e Phi-3 Mini
    
    elif ram < 16:
        # 12-16 GB
        return all_models[:3]  # Adiciona Phi-3 Medium
    
    else:
        # 16+ GB
        return all_models  # Todos os modelos


def get_model_info(model_id: str):
    """Retorna informações específicas de um modelo"""
    models = {
        "llama3.2:3b": {
            "name": "Llama 3.2 3B",
            "parameters": "3 bilhões",
            "context": "8K tokens",
            "best_for": ["Código", "Instruções", "Raciocínio"]
        },
        "phi3:mini": {
            "name": "Phi-3 Mini",
            "parameters": "3.8 bilhões",
            "context": "4K tokens",
            "best_for": ["Análise", "Rapidez", "Baixo consumo"]
        },
        "phi3:medium": {
            "name": "Phi-3 Medium",
            "parameters": "14 bilhões",
            "context": "4K tokens",
            "best_for": ["Tarefas complexas", "Qualidade", "Balanço"]
        },
        "codellama:7b": {
            "name": "Code Llama 7B",
            "parameters": "7 bilhões",
            "context": "16K tokens",
            "best_for": ["Programação", "Code completion", "Debug"]
        },
        "mistral:7b": {
            "name": "Mistral 7B",
            "parameters": "7 bilhões",
            "context": "8K tokens",
            "best_for": ["Textos gerais", "Conversação", "Resumos"]
        }
    }
    
    return models.get(model_id, {})