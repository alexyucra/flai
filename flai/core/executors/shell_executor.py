"""
Shell Executor - Executa comandos shell genéricos com segurança
"""
import subprocess
import shlex
from pathlib import Path
from typing import Tuple, Optional, List

class ShellExecutor:
    """Executor seguro de comandos shell"""
    
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path.cwd()
    
    def run(self, cmd: str, timeout: int = 120) -> Tuple[int, str, str]:
        """
        Executa comando shell
        
        Args:
            cmd: Comando a executar
            timeout: Timeout em segundos
        
        Returns:
            (return_code, stdout, stderr)
        """
        try:
            args = shlex.split(cmd)
            result = subprocess.run(
                args,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Comando excedeu tempo limite de {timeout}s"
        except Exception as e:
            return -1, "", str(e)
    
    def run_python(self, code: str) -> Tuple[int, str, str]:
        """Executa código Python inline"""
        return self.run(f'python -c "{code}"', timeout=30)
    
    def run_script(self, script_path: Path, args: List[str] = None) -> Tuple[int, str, str]:
        """Executa script Python"""
        if not script_path.exists():
            return -1, "", f"Script não encontrado: {script_path}"
        
        cmd = f"python {script_path}"
        if args:
            cmd += " " + " ".join(shlex.quote(a) for a in args)
        return self.run(cmd)
    
    def install_package(self, package: str, dev: bool = False) -> bool:
        """Instala pacote pip"""
        cmd = f"pip install {package}"
        if dev:
            cmd += " -e ."
        code, _, _ = self.run(cmd)
        return code == 0
    
    def run_make(self, target: str = None) -> bool:
        """Executa make"""
        cmd = "make"
        if target:
            cmd += f" {target}"
        code, _, _ = self.run(cmd)
        return code == 0
    
    def is_command_available(self, command: str) -> bool:
        """Verifica se comando está disponível"""
        code, _, _ = self.run(f"which {command}")
        return code == 0 or shutil.which(command) is not None
    
    def get_python_version(self) -> str:
        """Retorna versão do Python"""
        code, stdout, _ = self.run("python --version")
        if code == 0:
            return stdout.strip()
        return "unknown"
