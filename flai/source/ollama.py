import subprocess
import os
import sys
from pathlib import Path
import socket
import time

from .ollama_manager import run_ollama, get_ollama_manager
from flai.cli.console.console import console

def is_ollama_running():
    """Verifica se o servidor do Ollama está respondendo na porta 11434."""
    manager = get_ollama_manager()
    return manager.is_server_running()

def install_ollama():
    """Função de compatibilidade - verifica se Ollama está disponível"""
    manager = get_ollama_manager()
    status = manager.check_system()
    
    if status["ollama_found"]:
        console.print("[info]Ollama já instalado[/info]")
        if not status["server_running"]:
            console.print("[info]Iniciando servidor Ollama...[/info]")
            manager.start_server()
    else:
        console.print("[error]Ollama não encontrado[/error]")
        console.print("📥 Baixe de: https://ollama.com/download")
    
    return status["ollama_found"]

def pull_model(model_id: str):
    """Função de compatibilidade - instala modelo"""
    manager = get_ollama_manager()
    return manager.install_model(model_id)

def check_ollama_installed():
    """Verifica de várias formas se o Ollama está disponível"""
    checks = []
    
    # 1. Verificar no PATH
    try:
        result = subprocess.run(
            ["where", "ollama"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            checks.append(("PATH", result.stdout.strip()))
    except:
        pass
    
    # 2. Verificar locais comuns no Windows
    common_paths = [
        "C:\\Program Files\\Ollama\\ollama.exe",
        "C:\\Program Files (x86)\\Ollama\\ollama.exe",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), "Programs\\Ollama\\ollama.exe"),
        os.path.join(os.environ.get('ProgramFiles', ''), "Ollama\\ollama.exe"),
        os.path.join(os.environ.get('ProgramFiles(x86)', ''), "Ollama\\ollama.exe")
    ]
    
    found_paths = []
    for path in common_paths:
        if os.path.exists(path):
            found_paths.append(path)
    
    if found_paths:
        checks.append(("Common Paths", found_paths[0]))
    
    # 3. Verificar serviço Windows
    try:
        result = subprocess.run(
            ["sc", "query", "Ollama"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        if "RUNNING" in result.stdout:
            checks.append(("Service", "Running"))
        elif "Ollama" in result.stdout:
            checks.append(("Service", "Stopped"))
    except:
        pass
    
    # 4. Verificar API HTTP
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            checks.append(("API", "Available"))
    except:
        pass
    
    return checks

def ensure_ollama_running():
    """Garante que o Ollama está rodando"""
    checks = check_ollama_installed()
    
    print("Verificando Ollama...")
    for check_type, status in checks:
        print(f"  {check_type}: {status}")
    
    # Se encontrou o executável mas o serviço não está rodando
    executable_found = any(check[0] in ["PATH", "Common Paths"] for check in checks)
    service_running = any(check[0] == "Service" and check[1] == "Running" for check in checks)
    
    if not executable_found:
        print("\n❌ Ollama não encontrado!")
        print("Para instalar:")
        print("1. Baixe de https://ollama.com/download/windows")
        print("2. Execute o instalador")
        print("3. Reinicie o terminal")
        return False
    
    if not service_running:
        print("\n⚠ Ollama não está rodando. Tentando iniciar...")
        
        # Tentar encontrar o executável
        ollama_path = None
        for check_type, status in checks:
            if check_type in ["PATH", "Common Paths"]:
                ollama_path = status
                break
        
        if ollama_path:
            try:
                # Iniciar o servidor em background
                subprocess.Popen(
                    [ollama_path, "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
                print("Aguardando servidor iniciar...")
                time.sleep(5)
                
                # Verificar se iniciou
                checks = check_ollama_installed()
                if any(check[0] == "API" for check in checks):
                    print("✅ Ollama iniciado com sucesso!")
                    return True
                else:
                    print("❌ Não foi possível verificar se o Ollama iniciou")
                    print("Tente manualmente:")
                    print(f'  "{ollama_path}" serve')
                    return False
                    
            except Exception as e:
                print(f"❌ Erro ao iniciar Ollama: {e}")
                return False
        else:
            print("❌ Não foi possível encontrar ollama.exe para iniciar")
            return False
    
    return True

def run_ollama_fixed(model: str, prompt: str) -> str:
    """
    Versão robusta da função run_ollama que tenta múltiplas abordagens
    """
    
    # 1. Primeiro garantir que o Ollama está rodando
    if not ensure_ollama_running():
        return "Erro: Ollama não está disponível. Verifique a instalação."
    
    methods = [
        ("API HTTP", run_via_api),
        ("CLI via PATH", run_via_cli),
        ("CLI via local", run_via_cli_local)
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"Tentando método: {method_name}...")
            response = method_func(model, prompt)
            if response and not response.startswith("Erro:"):
                print(f"✅ Sucesso com {method_name}")
                return response
        except Exception as e:
            print(f"  ⚠ {method_name} falhou: {str(e)[:50]}...")
            continue
    
    return "Erro: Não foi possível se comunicar com o Ollama usando nenhum método."

def run_via_api(model: str, prompt: str) -> str:
    """Tentar via API HTTP"""
    try:
        import requests
        import json
        
        url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 512
            }
        }
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('response', '')
        else:
            return f"Erro HTTP {response.status_code}: {response.text[:100]}"
            
    except Exception as e:
        return f"Erro API: {str(e)}"

def run_via_cli(model: str, prompt: str) -> str:
    """Tentar via CLI (ollama no PATH)"""
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Erro CLI: {result.stderr[:100]}"
            
    except Exception as e:
        return f"Erro CLI: {str(e)}"

def run_via_cli_local(model: str, prompt: str) -> str:
    """Tentar via CLI com caminho local"""
    # Procurar ollama.exe em locais comuns
    possible_paths = [
        "ollama.exe",
        "ollama",
        "C:\\Program Files\\Ollama\\ollama.exe",
        "C:\\Program Files (x86)\\Ollama\\ollama.exe",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), "Programs\\Ollama\\ollama.exe")
    ]
    
    for ollama_path in possible_paths:
        if os.path.exists(ollama_path) or ollama_path == "ollama":
            try:
                result = subprocess.run(
                    [ollama_path, "run", model],
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    encoding='utf-8'
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
                    
            except Exception:
                continue
    
    return "Erro: Ollama não encontrado localmente"