"""
Shell Executor - Executa comandos externos com segurança

Auditoria SEC-05: comandos são sempre listas de argumentos (sem shell, sem
re-parsing de strings). A execução de Python inline (`run_python`) foi removida.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# Nome de pacote pip (com extras/versão opcionais); bloqueia opções como -r / --index-url
_PIP_SPEC_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?([<>=!~]=?[A-Za-z0-9.*+-]+)?$")
_MAKE_TARGET_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class ShellExecutor:
    """Executor seguro de comandos externos"""

    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path.cwd()

    def run(self, args: Sequence[str], timeout: int = 120) -> Tuple[int, str, str]:
        """
        Executa um comando.

        Args:
            args: Lista de argumentos (ex.: ["python", "--version"]). Strings não são aceitas.
            timeout: Timeout em segundos

        Returns:
            (return_code, stdout, stderr)
        """
        if isinstance(args, str) or not args:
            return -1, "", "Comando deve ser uma lista de argumentos não vazia"
        try:
            result = subprocess.run(
                list(args),
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"Comando excedeu tempo limite de {timeout}s"
        except FileNotFoundError:
            return -1, "", f"Comando não encontrado: {args[0]}"
        except Exception as e:
            return -1, "", str(e)

    def run_script(self, script_path: Path, args: Optional[List[str]] = None) -> Tuple[int, str, str]:
        """Executa script Python com o mesmo interpretador do FLAI"""
        if not script_path.exists():
            return -1, "", f"Script não encontrado: {script_path}"
        return self.run([sys.executable, str(script_path), *(args or [])])

    def install_package(self, package: str, dev: bool = False) -> bool:
        """Instala pacote pip (apenas nome de pacote; opções do pip são rejeitadas)"""
        if dev:
            cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
        else:
            if not _PIP_SPEC_RE.fullmatch(package or ""):
                return False
            cmd = [sys.executable, "-m", "pip", "install", package]
        code, _, _ = self.run(cmd, timeout=600)
        return code == 0

    def run_make(self, target: Optional[str] = None) -> bool:
        """Executa make"""
        cmd = ["make"]
        if target:
            if not _MAKE_TARGET_RE.fullmatch(target):
                return False
            cmd.append(target)
        code, _, _ = self.run(cmd)
        return code == 0

    def is_command_available(self, command: str) -> bool:
        """Verifica se comando está disponível (multiplataforma)"""
        return shutil.which(command) is not None

    def get_python_version(self) -> str:
        """Retorna versão do Python"""
        code, stdout, _ = self.run([sys.executable, "--version"])
        if code == 0:
            return stdout.strip()
        return "unknown"
