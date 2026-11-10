# fleting/flai/utils/ollama_manager.py

import os
import sys
import subprocess
import time
import socket
import json
from pathlib import Path
from typing import Optional, Dict, Any
# import platform
from flai.core.platform import (
    get_platform, is_windows, is_linux, is_macos,
    get_user_cache_dir, normalize_path, Platform
)
from .cache import cache

from flai.core.logging import get_logger

logger = get_logger(__name__)

class OllamaManager:
    """Gerencia automaticamente a instalação e execução do Ollama"""
    
    def __init__(self, auto_start: bool = True):
        self.auto_start = auto_start
        self.ollama_path = None
        self.ollama_dir = None
        self.server_url = "http://localhost:11434"
        self._server_process = None
        # self._system = platform.system()
        self._system = get_platform()

        import atexit
        atexit.register(self.cleanup)
        
    def find_ollama(self) -> Optional[str]:
        """Busca o Ollama em locais comuns do sistema"""
        
        possible_paths = []
        
        if is_windows():
            possible_paths = [
                Path("C:/Program Files/Ollama/ollama.exe"),
                Path("C:/Program Files (x86)/Ollama/ollama.exe"),
                Path(os.environ.get('LOCALAPPDATA', '')) / "Programs/Ollama/ollama.exe",
                Path(os.environ.get('ProgramFiles', '')) / "Ollama/ollama.exe",
                Path(os.environ.get('ProgramW6432', '')) / "Ollama/ollama.exe",
                Path.home() / "AppData/Local/Programs/Ollama/ollama.exe",
            ]
        elif is_linux():
            possible_paths = [
                Path("/usr/local/bin/ollama"),
                Path("/usr/bin/ollama"),
                Path.home() / ".local/bin/ollama",
                Path("/opt/ollama/ollama"),
            ]
        elif is_macos():
            possible_paths = [
                Path("/usr/local/bin/ollama"),
                Path("/opt/homebrew/bin/ollama"),
                Path("/Applications/Ollama.app/Contents/Resources/ollama"),
                Path.home() / ".local/bin/ollama",
            ]
        
        # Também verificar no PATH
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        for dir_path in path_dirs:
            if is_windows():
                possible_paths.append(Path(dir_path) / "ollama.exe")
            else:
                possible_paths.append(Path(dir_path) / "ollama")
        
        for path in possible_paths:
            if path.exists():
                self.ollama_path = str(path)
                self.ollama_dir = str(path.parent)
                return self.ollama_path
        
        return None
    
    def _get_optimize_script(self) -> Optional[Path]:
        """Retorna caminho do script de otimização para a plataforma"""
        script_dir = Path(__file__).parent.parent / "helpers"
        
        if is_windows():
            script = script_dir / "optimize_model.ps1"
        elif is_linux() or is_macos():
            script = script_dir / "optimize_model.sh"
        else:
            return None
        
        if script.exists():
            return script
        return None
    
    def optimize_model(self, base_model: str, custom_name: str = "flai-coder") -> bool:
        """Otimiza modelo usando script específico da plataforma"""
        
        script = self._get_optimize_script()
        if not script:
            print(f"⚠️ Script de otimização não encontrado para {get_platform()}")
            return False
        
        try:
            if is_windows():
                result = subprocess.run([
                    "powershell.exe", "-ExecutionPolicy", "Bypass", "-File",
                    str(script), base_model, custom_name
                ], capture_output=True, text=True)
            else:
                # Linux/macOS
                os.chmod(script, 0o755)  # Tornar executável
                result = subprocess.run(
                    [str(script), base_model, custom_name],
                    capture_output=True, text=True
                )
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Erro na otimização: {e}")
            return False
    
    def is_server_running(self, timeout: int = 2) -> bool:
        """Verifica se o servidor Ollama está rodando"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex(('localhost', 11434))
            sock.close()
            return result == 0
        except:
            return False
    
    def start_server(self) -> bool:
        """Inicia o servidor Ollama em background"""
        
        if not self.ollama_path:
            if not self.find_ollama():
                return False
        
        if self.is_server_running():
            logger.error("✅ Servidor Ollama já está rodando")
            return True
        
        logger.info("🚀 Iniciando servidor Ollama...")
        
        try:
            # Configurar flags baseadas no sistema
            startupinfo = None
            creationflags = 0
            
            if self._system == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            
            # Iniciar servidor em background
            self._server_process = subprocess.Popen(
                [self.ollama_path, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            
            # Aguardar inicialização
            for i in range(30):  # 30 tentativas, 1 segundo cada
                time.sleep(1)
                if self.is_server_running():
                    logger.info("✅ Servidor Ollama iniciado com sucesso")
                    return True
            
            logger.error("❌ Timeout ao aguardar servidor iniciar")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar servidor: {e}")
            return False
    
    def stop_server(self) -> bool:
        """Para o servidor Ollama graciosamente"""
        if not self._server_process:
            return True
        
        try:
            logger.warning("🛑 Parando servidor Ollama...")
            
            # Tentativa graciosa primeiro
            self._server_process.terminate()
            
            # Aguarda até 5 segundos
            try:
                self._server_process.wait(timeout=5)
                logger.info("✅ Servidor Ollama parado")
                self._server_process = None
                return True
            except subprocess.TimeoutExpired:
                # Força encerramento
                self._server_process.kill()
                self._server_process.wait(timeout=2)
                logger.warning("⚠️ Servidor Ollama foi finalizado forcadamente")
                self._server_process = None
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro ao parar servidor: {e}")
            return False

    def install_model(self, model_name: str, verbose=False) -> bool:
        """Instala um modelo se não estiver disponível"""
        
        if not self.ollama_path:
            return False
        
        logger.info(f"📦 Verificando modelo {model_name}...")
        
        # Verificar se modelo já existe via API
        if self.is_server_running():
            try:
                import requests
                response = requests.get(f"{self.server_url}/api/tags", timeout=10)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    for model in models:
                        if model_name in model.get('name', ''):
                            logger.info(f"✅ Modelo {model_name} já está instalado")
                            return True
            except:
                pass
        
        # Baixar modelo via CLI
        logger.info(f"📥 Baixando modelo {model_name}...")
        try:
            process = subprocess.Popen(
                [self.ollama_path, "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8'
            )
            
            # Mostrar progresso
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Mostrar apenas linhas importantes
                    if "pulling" in output.lower() or "downloading" in output.lower():
                        sys.stdout.write(f"\r{output.strip()[:80]}")
                        sys.stdout.flush()
            
            logger.info(f"\n✅ Modelo {model_name} instalado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"\n❌ Erro ao instalar modelo: {e}")
            return False
    
    def run_model(self, model: str, prompt: str, timeout: int = 120, security_context: str = "") -> str:
        """Executa um modelo via API HTTP com contexto de segurança"""
        
        # Encontrar Ollama se necessário
        if not self.ollama_path and not self.find_ollama():
            return "Erro: Ollama não encontrado no sistema"
        
        # Garantir servidor rodando
        if not self.is_server_running():
            if self.auto_start:
                if not self.start_server():
                    return "Erro: Não foi possível iniciar o servidor Ollama"
            else:
                return "Erro: Servidor Ollama não está rodando"
        
        # Garantir modelo instalado
        if not self.install_model(model):
            return f"Erro: Não foi possível instalar o modelo {model}"
        
        # Executar via API
        try:
            import requests
            full_prompt = f"""
{security_context if security_context else "## Contexto: Você está analisando um projeto Fleting específico."}

{prompt}

Lembre-se: Responda apenas sobre os arquivos e estrutura mencionados no contexto.
Não faça referência a arquivos ou pastas externas.
"""
            logger.info(f"🤖 Executando {model}...")
        
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024
                }
            }
            
            response = requests.post(
                f"{self.server_url}/api/generate",
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                return f"Erro API {response.status_code}: {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            return "Erro: Timeout - o modelo demorou muito para responder"
        except Exception as e:
            return f"Erro ao executar modelo: {str(e)}"

    # ------------------------------------------------------------------
    # API usada pelo ResourceGuard (RAM / limites de tokens)
    # ------------------------------------------------------------------
    def _api(self, method: str, path: str, payload: Optional[Dict] = None, timeout: int = 30):
        import requests
        url = f"{self.server_url}{path}"
        if method == "GET":
            return requests.get(url, timeout=timeout)
        return requests.post(url, json=payload or {}, timeout=timeout)

    def list_local_models(self) -> Dict[str, int]:
        """{nome: tamanho_em_bytes} dos modelos já baixados."""
        try:
            r = self._api("GET", "/api/tags", timeout=5)
            return {m["name"]: int(m.get("size", 0)) for m in r.json().get("models", [])}
        except Exception:
            return {}

    def loaded_models(self) -> Dict[str, int]:
        """{nome: bytes em memória} dos modelos carregados agora (/api/ps)."""
        try:
            r = self._api("GET", "/api/ps", timeout=5)
            return {m["name"]: int(m.get("size", 0)) for m in r.json().get("models", [])}
        except Exception:
            return {}

    def show_model(self, model: str) -> Dict:
        try:
            r = self._api("POST", "/api/show", {"model": model}, timeout=15)
            return r.json() if r.status_code == 200 else {}
        except Exception:
            return {}

    def model_footprint(self, model: str):
        """ModelFootprint (pesos + KV cache por token) do modelo base."""
        from flai.core.resources import ModelFootprint
        local = self.list_local_models()
        size = local.get(model) or local.get(f"{model}:latest", 0)
        loaded = self.loaded_models()
        return ModelFootprint.from_ollama(model, self.show_model(model), size,
                                          loaded.get(model, 0))

    def base_model_of(self, model: str) -> str:
        """Se `model` é um derivado flai-*, retorna o modelo de origem (FROM)."""
        show = self.show_model(model)
        for line in (show.get("modelfile") or "").splitlines():
            if line.startswith("FROM ") and not line.strip().endswith(".gguf") and "blobs" not in line:
                return line[5:].strip()
        parent = (show.get("details") or {}).get("parent_model")
        return parent or model

    def ensure_optimized_model(self, base_model: str, num_ctx: int, num_predict: int,
                               temperature: float = 0.7) -> Optional[str]:
        """
        Cria (uma vez) o modelo derivado com contexto reduzido:
        flai-<base>:ctx<N>  (FROM base + num_ctx/num_predict). Retorna o nome.
        """
        from flai.core.resources import optimized_model_name
        name = optimized_model_name(base_model, num_ctx)
        if name in self.list_local_models():
            return name
        payload = {
            "model": name,
            "from": base_model,
            "parameters": {"num_ctx": num_ctx, "num_predict": num_predict,
                           "temperature": temperature},
            "stream": False,
        }
        try:
            r = self._api("POST", "/api/create", payload, timeout=300)
            if r.status_code == 200:
                logger.info(f"Modelo otimizado criado: {name}")
                return name
            logger.error(f"Falha ao criar {name}: {r.status_code} {r.text[:200]}")
        except Exception as e:
            logger.error(f"Falha ao criar {name}: {e}")
        return None

    def generate(self, model: str, prompt: str, options: Optional[Dict] = None,
                 timeout: int = 300) -> Dict[str, Any]:
        """
        Gera resposta sem baixar modelos automaticamente.
        Retorna {"ok", "text", "prompt_tokens", "output_tokens", "truncated_by_ctx"}.
        """
        if not self.is_server_running() and not (self.auto_start and self.start_server()):
            return {"ok": False, "text": "Erro: servidor Ollama não está rodando"}
        payload = {"model": model, "prompt": prompt, "stream": False, "options": options or {}}
        try:
            r = self._api("POST", "/api/generate", payload, timeout=timeout)
            if r.status_code != 200:
                return {"ok": False, "text": f"Erro API {r.status_code}: {r.text[:200]}"}
            d = r.json()
            return {
                "ok": True,
                "text": d.get("response", ""),
                "prompt_tokens": d.get("prompt_eval_count", 0),
                "output_tokens": d.get("eval_count", 0),
                "done_reason": d.get("done_reason"),
            }
        except Exception as e:
            return {"ok": False, "text": f"Erro ao executar modelo: {e}"}

    def run_model_cli(self, model: str, prompt: str, timeout: int = 120) -> str:
        """Executa modelo via CLI (fallback)"""
        
        if not self.ollama_path:
            if not self.find_ollama():
                return "Erro: Ollama não encontrado"
        
        try:
            result = subprocess.run(
                [self.ollama_path, "run", model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=timeout
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"Erro CLI: {result.stderr.strip()}"
                
        except subprocess.TimeoutExpired:
            return "Erro: Timeout ao executar modelo"
        except Exception as e:
            return f"Erro: {str(e)}"
    
    def check_system(self) -> Dict[str, Any]:
        """Verifica o estado do sistema"""
        
        status = {
            "system": self._system,
            "ollama_found": False,
            "ollama_path": None,
            "server_running": False,
            "api_accessible": False,
            "models": []
        }
        
        # Encontrar Ollama
        ollama_path = self.find_ollama()
        if ollama_path:
            status["ollama_found"] = True
            status["ollama_path"] = ollama_path
        
        # Verificar servidor
        status["server_running"] = self.is_server_running()
        
        # Verificar API
        if status["server_running"]:
            try:
                import requests
                response = requests.get(f"{self.server_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    status["api_accessible"] = True
                    status["models"] = response.json().get('models', [])
            except:
                pass
        
        return status
    
    def ensure_ready(self, model: str = "deepseek-coder:1.3b", verbose: bool = False) -> bool:
        """Garante que tudo está pronto para uso"""
        
        from flai.cli.console.console import console
        from flai.core.platform import get_user_cache_dir

        cache_dir = get_user_cache_dir()
        
        cache_key = f"ensure_ready_{model}"
        cached = cache.get(cache_key)
        if cached is not None:
            if verbose:
                console.print("[dim]✅ Sistema já verificado (cache)[/dim]")
            return cached
    
        status = self.check_system()
        
        # 1. Ollama instalado?
        if not status["ollama_found"]:
            console.print("❌ Ollama não encontrado")
            console.print("   Execute: python -m flai.cli init ia")
            cache.set(cache_key, False, ttl=60)  # Cache negativo também
            return False
        
        # if verbose:
        #     console.print(f"✅ Ollama encontrado em: {status['ollama_path']}")
        
        # 2. Servidor rodando?
        if not status["server_running"]:
            if self.auto_start:
                if self._server_process is None or self._server_process.poll() is not None:
                    if not self.start_server():
                        console.print("❌ Não foi possível iniciar o servidor Ollama")
                        cache.set(cache_key, False, ttl=60)
                        return False
                else:
                    console.print("✅ Servidor já estava em execução")
            else:
                console.print("❌ Servidor Ollama não está rodando")
                cache.set(cache_key, False, ttl=60)
                return False
        elif verbose:
            console.print("✅ Servidor Ollama está rodando")
        
        # 3. Instalar modelo se necessário
        if verbose:
            console.print(f"🔍 Verificando modelo {model}...")
    
        model_installed = False
        for installed_model in status["models"]:
            if model in installed_model.get('name', ''):
                model_installed = True
                break
        
        if not model_installed:
            if verbose:
                console.print(f"📥 Modelo {model} não encontrado, instalando...")
            if not self.install_model(model, verbose=verbose):
                if verbose:
                    console.print(f"⚠ Não foi possível instalar {model}")
                    console.print(f"   Execute manualmente: ollama pull {model}")
            elif verbose:
                console.print(f"✅ Modelo {model} instalado")
        elif verbose:
            console.print(f"✅ Modelo {model} já está instalado")
        
        cache.set(cache_key, True, ttl=300)
        return True
    
    def quick_run(self, model: str, prompt: str) -> str:
        """Atalho rápido para execução de modelos via API ou CLI"""
        response = self.run_model(model, prompt)
        
        if response.startswith("Erro:"):
            # Fallback para CLI se a API falhar
            return self.run_model_cli(model, prompt)
        
        return response
    
    def cleanup(self):
        """Limpeza automática ao fechar o programa"""
        if self._server_process:
            self.stop_server()
    
    def __del__(self):
        """Destruidor - garante limpeza"""
        self.cleanup()


# Instância global
_ollama_manager = None

def get_ollama_manager() -> OllamaManager:
    """Retorna a instância singleton do gerenciador"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager(auto_start=True)
    return _ollama_manager

def run_ollama(model: str, prompt: str) -> str:
    """Função principal para executar modelos (usada pelo FLAI)"""
    manager = get_ollama_manager()
    
    # Tentar via API primeiro
    response = manager.run_model(model, prompt)
    
    # Se falhar, tentar CLI
    if response.startswith("Erro:"):
        logger.error("⚠ API falhou, tentando CLI...")
        response = manager.run_model_cli(model, prompt)
    
    return response

def cleanup_ollama():
    """Limpeza global do Ollama"""
    global _ollama_manager
    if _ollama_manager:
        _ollama_manager.cleanup()
        _ollama_manager = None

import atexit
atexit.register(cleanup_ollama)