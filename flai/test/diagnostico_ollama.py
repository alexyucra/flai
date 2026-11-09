import subprocess
import os
import sys
import requests

def diagnostico_ollama():
    print("=== DIAGNÓSTICO OLLAMA ===\n")
    
    # 1. Verificar instalação
    print("1. Verificando instalação...")
    ollama_path = None
    
    locais = [
        r"C:\Program Files\Ollama\ollama.exe",
        r"C:\Program Files (x86)\Ollama\ollama.exe",
        os.path.join(os.getenv('LOCALAPPDATA', ''), r"Programs\Ollama\ollama.exe"),
        r"C:\Windows\System32\ollama.exe"
    ]
    
    for local in locais:
        if os.path.exists(local):
            ollama_path = local
            print(f"   ✅ Encontrado em: {local}")
            break
    
    if not ollama_path:
        print("   ❌ Ollama não encontrado nos locais padrão")
        print("   📥 Baixe em: https://ollama.com/download/windows")
        return False
    
    # 2. Verificar serviço
    print("\n2. Verificando serviço...")
    try:
        import psutil
        ollama_running = False
        for proc in psutil.process_iter(['name']):
            if 'ollama' in proc.info['name'].lower():
                ollama_running = True
                print(f"   ✅ Processo rodando: {proc.info['name']}")
                break
        
        if not ollama_running:
            print("   ⚠ Ollama não está rodando como processo")
    except:
        print("   ⚠ Não foi possível verificar processos")
    
    # 3. Verificar porta 11434
    print("\n3. Verificando API...")
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ API respondendo: {response.json()}")
        else:
            print(f"   ❌ API retornou código: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API não acessível: {e}")
    
    # 4. Testar execução direta
    print("\n4. Testando execução direta...")
    try:
        result = subprocess.run(
            [ollama_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"   ✅ Versão: {result.stdout.strip()}")
        else:
            print(f"   ❌ Erro: {result.stderr.strip()}")
    except Exception as e:
        print(f"   ❌ Falha: {e}")
    
    # 5. Verificar modelos
    print("\n5. Verificando modelos...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            modelos = response.json().get('models', [])
            if modelos:
                print("   ✅ Modelos instalados:")
                for modelo in modelos:
                    print(f"      - {modelo['name']}")
            else:
                print("   ⚠ Nenhum modelo instalado")
                print("   💡 Execute: ollama pull phi3:mini")
        else:
            print("   ❌ Não foi possível listar modelos")
    except:
        print("   ⚠ Não foi possível verificar modelos")
    
    return True

if __name__ == "__main__":
    diagnostico_ollama()