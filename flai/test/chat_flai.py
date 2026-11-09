import subprocess
import sys
from pathlib import Path

def main():
    """Chat simple sin errores"""
    
    project = "app3"
    model = "flai-optimized"
    
    print("🤖 CHAT SIMPLE CON FLAI-OPTIMIZED")
    print(f"Proyecto: {project}")
    print(f"Modelo: {model}")
    print("Escribe 'salir' para terminar")
    print("="*50)
    
    while True:
        try:
            user_input = input("\n❓ Tú: ").strip()
            
            if user_input.lower() in ['salir', 'exit', 'quit', 'q']:
                print("\n👋 ¡Hasta luego!")
                break
            
            if not user_input:
                continue
            
            print("💭 Procesando...")
            
            # Llamar a Ollama directamente
            result = subprocess.run(
                ['ollama', 'run', model, user_input],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"\n🤖 Flai:")
                print("-"*50)
                print(result.stdout)
                print("-"*50)
            else:
                print(f"❌ Error: {result.stderr[:100]}")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    main()