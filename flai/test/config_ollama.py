import os
import subprocess
import sys

def setup_ollama():
    """Configura o Ollama para funcionar com o FLAI"""
    
    print("🚀 Configurando Ollama para FLAI...")
    
    # Caminho do Ollama no SEU sistema
    OLLAMA_PATH = r"C:\Users\ThinkPad\AppData\Local\Programs\Ollama\ollama.exe"
    OLLAMA_DIR = r"C:\Users\ThinkPad\AppData\Local\Programs\Ollama"
    
    # 1. Verificar instalação
    if not os.path.exists(OLLAMA_PATH):
        print("❌ Ollama não encontrado")
        print("📥 Instale de: https://ollama.com/download/windows")
        return False
    
    print(f"✅ Ollama encontrado em: {OLLAMA_PATH}")
    
    # 2. Adicionar ao PATH (temporário para esta sessão)
    os.environ["PATH"] = f"{OLLAMA_DIR};{os.environ.get('PATH', '')}"
    print("✅ Ollama adicionado ao PATH desta sessão")
    
    # 3. Verificar serviço
    print("\n🔍 Verificando serviço Ollama...")
    try:
        # Verificar se porta 11434 está aberta
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 11434))
        sock.close()
        
        if result == 0:
            print("✅ Servidor Ollama está rodando")
        else:
            print("⚠ Iniciando servidor Ollama...")
            # Iniciar em background
            subprocess.Popen(
                [OLLAMA_PATH, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            import time
            time.sleep(3)
            print("✅ Servidor iniciado")
    except Exception as e:
        print(f"❌ Erro ao verificar servidor: {e}")
    
    # 4. Verificar/baixar modelo phi3:mini
    print("\n📦 Verificando modelo phi3:mini...")
    try:
        result = subprocess.run(
            [OLLAMA_PATH, "list"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "phi3:mini" in result.stdout:
            print("✅ Modelo phi3:mini já está instalado")
        else:
            print("📥 Baixando modelo phi3:mini...")
            subprocess.run(
                [OLLAMA_PATH, "pull", "phi3:mini"],
                stdout=sys.stdout,
                stderr=sys.stderr,
                timeout=300
            )
            print("✅ Modelo phi3:mini baixado")
            
    except subprocess.TimeoutExpired:
        print("⚠ Timeout ao verificar modelos")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # 5. Testar
    print("\n🧪 Testando configuração...")
    try:
        result = subprocess.run(
            [OLLAMA_PATH, "run", "phi3:mini", "Responda 'OK' se estiver funcionando."],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and "OK" in result.stdout.upper():
            print("✅ Teste bem-sucedido!")
            print(f"   Resposta: {result.stdout.strip()}")
        else:
            print(f"⚠ Resposta inesperada: {result.stdout}")
            
    except Exception as e:
        print(f"❌ Teste falhou: {e}")
    
    print("\n" + "="*50)
    print("✅ Configuração completa!")
    print("\nPara usar no FLAI:")
    print(f"1. O Ollama está em: {OLLAMA_PATH}")
    print("2. Execute: python -m fleting.flai.cli shell")
    
    return True

if __name__ == "__main__":
    setup_ollama()