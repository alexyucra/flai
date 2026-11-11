"""
Fleting Executor - Executa comandos da CLI do Fleting
(https://alexyucra.github.io/Fleting/)

- Argumentos sempre em lista (auditoria SEC-05).
- Nomes validados no padrão do Fleting: minúsculas, dígitos e '_' começando
  por letra, sem palavra reservada do Python. O Fleting 1.2.7 aceita
  "My-Page" e gera módulos inválidos (my-page_view.py), por isso o FLAI valida antes.
- No Windows o Fleting quebra (UnicodeEncodeError/cp1252) quando a saída é
  capturada; por isso forçamos UTF-8 no processo filho.
- Comandos que executam código do projeto (db migrate/seed/rollback) ou
  apagam arquivos são marcados como "sensíveis" e exigem confirmação.
"""
import keyword
import os
import re
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

_FLETING_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

# Comandos permitidos: (comando, subcomando) -> exige nome?
ALLOWED_COMMANDS: Dict[Tuple[str, ...], bool] = {
    ("info",): False,
    ("doctor",): False,
    ("create", "page"): True,
    ("create", "view"): True,
    ("create", "model"): True,
    ("create", "controller"): True,
    ("delete", "page"): True,
    ("delete", "view"): True,
    ("delete", "model"): True,
    ("delete", "controller"): True,
    ("list", "pages"): False,
    ("list", "views"): False,
    ("list", "models"): False,
    ("list", "controllers"): False,
    ("list", "routes"): False,
    ("db", "init"): False,
    ("db", "make"): True,
    ("db", "migrate"): False,
    ("db", "rollback"): False,
    ("db", "status"): False,
    ("db", "seed"): False,
}

# Apagam arquivos ou executam código Python do projeto
SENSITIVE_COMMANDS = {
    ("delete", "page"), ("delete", "view"), ("delete", "model"), ("delete", "controller"),
    ("db", "migrate"), ("db", "rollback"), ("db", "seed"), ("list", "routes"),
}

Confirm = Callable[[str], bool]


class FletingNameError(ValueError):
    """Nome inválido para o Fleting."""


def fleting_name(name: str) -> str:
    """Normaliza e valida nome de página/model/controller no padrão do Fleting."""
    if not isinstance(name, str):
        raise FletingNameError(f"Nome inválido: {name!r}")
    norm = name.strip().lower().replace("-", "_")
    if not _FLETING_NAME_RE.fullmatch(norm) or keyword.iskeyword(norm):
        raise FletingNameError(
            f"Nome inválido para o Fleting: {name!r}. Use minúsculas, números e '_' "
            "começando por letra (ex.: produtos, user_profile)."
        )
    return norm


def find_fleting_binary() -> Optional[str]:
    """Localiza o executável `fleting` (PATH ou pasta Scripts do Python atual)."""
    found = shutil.which("fleting")
    if found:
        return found
    scripts = Path(sysconfig.get_path("scripts"))
    for candidate in ("fleting.exe", "fleting"):
        if (scripts / candidate).exists():
            return str(scripts / candidate)
    return None


class FletingExecutor:
    """Executor de comandos do framework Fleting"""

    def __init__(self, project_path: Optional[Path] = None, confirm: Optional[Confirm] = None):
        self.project_path = Path(project_path or Path.cwd())
        # Sem callback de confirmação, comandos sensíveis são negados
        self.confirm = confirm
        self._binary = find_fleting_binary()
        self._fleting_available = None
        self.last_output = ""

    # ------------------------------------------------------------------ core
    def run(self, args: Sequence[str], timeout: int = 120) -> Tuple[int, str, str]:
        """Executa `fleting <args...>` (sem validação; uso interno)."""
        if isinstance(args, str):
            return -1, "", "Argumentos devem ser uma lista"
        if not self._binary:
            return -1, "", "Comando 'fleting' não encontrado. Instale com: pip install fleting"
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        try:
            result = subprocess.run(
                [self._binary, *args],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                env=env,
            )
            self.last_output = (result.stdout or "") + (result.stderr or "")
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Comando excedeu tempo limite"
        except Exception as e:
            return -1, "", str(e)

    def execute(self, args: Sequence[str], preconfirmed: bool = False) -> Tuple[int, str]:
        """
        Executa um comando da allowlist, validando nome e pedindo confirmação
        para comandos sensíveis. Retorna (código, saída).
        preconfirmed=True: o usuário já aprovou um plano que inclui este comando.
        """
        args = [a for a in args if a]
        key = tuple(args[:2]) if tuple(args[:2]) in ALLOWED_COMMANDS else tuple(args[:1])
        if key not in ALLOWED_COMMANDS:
            return 2, f"Comando Fleting não permitido: {' '.join(args) or '(vazio)'}"

        needs_name = ALLOWED_COMMANDS[key]
        rest = args[len(key):]
        if needs_name:
            if len(rest) != 1:
                return 2, f"Uso: fleting {' '.join(key)} <nome>"
            try:
                rest = [fleting_name(rest[0])]
            except FletingNameError as e:
                return 2, str(e)
        elif rest:
            return 2, f"Uso: fleting {' '.join(key)} (sem argumentos extras)"

        full = [*key, *rest]
        if key in SENSITIVE_COMMANDS and not preconfirmed:
            question = f"Executar 'fleting {' '.join(full)}'? (altera o projeto ou executa código dele)"
            if not (self.confirm and self.confirm(question)):
                return 3, f"Cancelado: fleting {' '.join(full)}"

        code, out, err = self.run(full)
        return code, (out + err).strip()

    # ------------------------------------------------------------- helpers
    def _ok(self, args: List[str]) -> bool:
        code, _ = self.execute(args)
        return code == 0

    def create_page(self, name: str) -> bool:
        """Cria model + controller + view + rota (`fleting create page`)."""
        return self._ok(["create", "page", name])

    def create_view(self, name: str) -> bool:
        return self._ok(["create", "view", name])

    def create_model(self, name: str) -> bool:
        """Cria apenas o model (`fleting create model`)."""
        return self._ok(["create", "model", name])

    def create_controller(self, name: str) -> bool:
        return self._ok(["create", "controller", name])

    def db_initialized(self) -> bool:
        return (self.project_path / "migrations").exists()

    def db_init(self) -> bool:
        return self._ok(["db", "init"])

    def make_migration(self, name: str) -> bool:
        """Cria migration (`fleting db make`). Inicializa o banco se necessário."""
        if not self.db_initialized() and not self.db_init():
            return False
        return self._ok(["db", "make", name])

    def run_migrations(self) -> bool:
        """`fleting db migrate` (sensível: executa código das migrations)."""
        return self._ok(["db", "migrate"])

    # ------------------------------------------------------------ leitura
    def _list_dir(self, rel: str, suffix: str) -> List[str]:
        d = self.project_path / rel
        if not d.exists():
            return []
        return sorted(
            f.stem[: -len(suffix)] if f.stem.endswith(suffix) else f.stem
            for f in d.glob("*.py")
            if f.stem != "__init__"
        )

    def list_pages(self) -> List[str]:
        return self._list_dir("app/views/pages", "_view")

    def list_models(self) -> List[str]:
        return self._list_dir("app/models", "_model")

    def list_controllers(self) -> List[str]:
        return self._list_dir("app/controllers", "_controller")

    def list_migrations(self) -> List[str]:
        return self._list_dir("migrations", "")

    def is_available(self) -> bool:
        if self._fleting_available is None:
            self._fleting_available = self._binary is not None
        return self._fleting_available

    def get_project_info(self) -> dict:
        return {
            "path": str(self.project_path),
            "has_fleting": self.is_available(),
            "pages": self.list_pages(),
            "models": self.list_models(),
            "controllers": self.list_controllers(),
            "migrations": self.list_migrations(),
        }
