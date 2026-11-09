# test_ollama.py
import subprocess
import os

def test_ollama():
    print("=== Teste do Ollama ===\n")
    
    # Teste 1: Verificar instalação
    print("1. Verificando instalação...")
    try:
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Versão: {result.stdout.strip()}")
        else:
            print("   ❌ Ollama não encontrado no PATH")
    except:
        print("   ❌ Ollama não encontrado")
    
    # Teste 2: Verificar modelos instalados
    print("\n2. Verificando modelos...")
    try:
        result = subprocess.run(["ollama", "list"], 
                              capture_output=True, text=True)
        print(result.stdout)
    except:
        print("   ❌ Não foi possível listar modelos")
    
    # Teste 3: Tentar executar um modelo
    print("\n3. Testando execução...")
    try:
        # Testar com modelo pequeno
        result = subprocess.run(
            ["ollama", "run", "phi3:mini", "Olá, como vai?"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("   ✅ Modelo respondeu!")
            print(f"   Resposta: {result.stdout[:100]}...")
        else:
            print(f"   ❌ Erro: {result.stderr[:100]}")
    except subprocess.TimeoutExpired:
        print("   ⚠ Timeout - modelo demorou muito")
    except Exception as e:
        print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    test_ollama()