"""
CRUD Agent - Orquestra a criação de CRUD com a CLI do Fleting

Fluxo: diagnosticar → planejar → confirmar (uma vez) → executar → verificar

A implementação é feita POR DOMÍNIO, sempre nesta ordem (cada etapa só se faltar):

  1. Diagnóstico   'fleting list pages' (model/controller/view/rota) + migrations + tabela
  2. Migração      fleting db init · fleting db make <nome> + CREATE TABLE · fleting db migrate
  3. Model         fleting create model <nome>
  4. Controller    fleting create controller <nome> + listar/buscar/criar/atualizar/excluir
  5. View + rota   fleting create page <nome> (model/controller já existem: cria view e rota)
  6. Verificação   'fleting list pages' de novo, migration aplicada, tabela e sintaxe
"""
import ast
import re
import sqlite3
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from flai.core.executors.fleting_executor import (
    FletingExecutor, FletingNameError, fleting_name, Confirm,
)
from flai.cli.console.console import console

Ask = Callable[[str, str], str]  # (pergunta, padrão) -> resposta

TYPE_ALIASES = {
    "str": "VARCHAR(255)", "string": "VARCHAR(255)", "texto": "TEXT", "text": "TEXT",
    "int": "INTEGER", "inteiro": "INTEGER", "float": "REAL", "decimal": "REAL",
    "bool": "BOOLEAN", "boolean": "BOOLEAN", "data": "DATE", "date": "DATE",
    "datetime": "DATETIME",
}
# Tipo inferido pelo nome do campo quando não informado
NAME_HINTS = [
    (r"^(idade|quantidade|qtd|estoque|ano|numero|.*_id)$", "INTEGER"),
    (r"^(preco|valor|salario|total|peso|altura)$", "REAL"),
    (r"^(ativo|is_.*|tem_.*)$", "BOOLEAN"),
    (r"^(data|nascimento|data_.*)$", "DATE"),
    (r"^(descricao|observacao|obs|bio)$", "TEXT"),
]
DEFAULT_FIELDS = {"usuarios": "nome, email, senha, ativo:bool"}
DOMAINS = ("model", "controller", "view", "route")
FILE_OF = {"model": "app/models/{name}_model.py", "controller": "app/controllers/{name}_controller.py",
           "view": "app/views/pages/{name}_view.py", "route": "configs/routes.py"}

# Métodos CRUD do controller (API do core.base_model do Fleting)
CRUD_METHODS = {
    "listar": "    def listar(self):\n        return self.model.all()\n",
    "buscar": "    def buscar(self, id):\n        return self.model.find(id)\n",
    "criar": "    def criar(self, **dados):\n        return self.model.create(**dados)\n",
    "atualizar": ("    def atualizar(self, id, **dados):\n        registro = self.model.find(id)\n"
                  "        return registro.update(**dados) if registro else None\n"),
    "excluir": ("    def excluir(self, id):\n        registro = self.model.find(id)\n"
                "        return registro.delete() if registro else None\n"),
}
EMPTY_UP = re.compile(r"def up\(db\):\s*(#[^\n]*\n\s*)?pass", re.S)


def parse_fields(raw: List[str]) -> List[Tuple[str, str]]:
    """['nome', 'idade:int'] -> [('nome', 'VARCHAR(255)'), ('idade', 'INTEGER')]"""
    out = []
    for item in raw:
        name, _, typ = item.strip().partition(":")
        name = re.sub(r"\W", "_", name.strip().lower())
        if not name or name == "id" or not re.fullmatch(r"[a-z_][a-z0-9_]*", name):
            continue
        sql = TYPE_ALIASES.get(typ.strip().lower()) if typ else None
        if not sql:
            sql = next((t for pat, t in NAME_HINTS if re.fullmatch(pat, name)), "VARCHAR(255)")
        out.append((name, sql))
    return out


class CRUDAgent:
    def __init__(self, project_path: Optional[Path] = None, confirm: Optional[Confirm] = None,
                 ask: Optional[Ask] = None):
        self.project_path = project_path or Path.cwd()
        self.executor = FletingExecutor(self.project_path, confirm=confirm)
        self.confirm = confirm
        self.ask = ask

    # ------------------------------------------------------------ diagnóstico
    def _migrations_for(self, name: str) -> List[Path]:
        d = self.project_path / "migrations"
        return sorted(d.glob(f"*_{name}.py")) if d.exists() else []

    def _db_path(self) -> Optional[Path]:
        try:
            text = (self.project_path / "configs" / "database.py").read_text(encoding="utf-8")
        except OSError:
            return None
        if re.search(r'"ENGINE"\s*:\s*"mysql"', text):
            return None  # verificação de tabela só para SQLite
        m = re.search(r'"PATH"\s*:\s*"([^"]+)"', text)
        return self.project_path / (m.group(1) if m else "data/fleting.db")

    def _sqlite(self, sql: str) -> List[tuple]:
        db = self._db_path()
        if not db or not db.exists():
            return []
        try:
            with sqlite3.connect(db) as c:
                return c.execute(sql).fetchall()
        except sqlite3.Error:
            return []

    def _applied(self) -> List[str]:
        """Stems das migrations aplicadas (o Fleting grava '002_x.py'; aceita com ou sem .py)."""
        return [Path(r[0]).stem for r in self._sqlite("SELECT name FROM _fleting_migrations")]

    def _table_exists(self, name: str) -> bool:
        return bool(self._sqlite(
            f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{name}'"))

    def _routes(self) -> set:
        """Rotas de configs/routes.py lidas sem executar o arquivo (mesma visão de 'fleting list routes')."""
        try:
            text = (self.project_path / "configs" / "routes.py").read_text(encoding="utf-8")
        except OSError:
            return set()
        return {p.strip("/") for p in re.findall(r'"path"\s*:\s*"([^"]*)"', text)}

    def pages(self) -> Dict[str, Dict[str, bool]]:
        """Equivalente a 'fleting list pages': por página, quais domínios existem."""
        app = self.project_path / "app"
        def names(sub, suffix):
            return {f.stem[: -len(suffix)] for f in (app / sub).glob(f"*{suffix}.py")}
        models, ctrls = names("models", "_model"), names("controllers", "_controller")
        views, routes = names("views/pages", "_view"), self._routes()
        return {n: {"model": n in models, "controller": n in ctrls,
                    "view": n in views, "route": n in routes}
                for n in sorted(models | ctrls | views | routes) if n}

    def diagnose(self, name: str) -> Dict:
        applied = set(self._applied())
        migs = self._migrations_for(name)
        pending = [m for m in migs if m.stem not in applied]
        empty_pending = [m for m in pending if EMPTY_UP.search(m.read_text(encoding="utf-8"))]
        page = self.pages().get(name, dict.fromkeys(DOMAINS, False))
        return {
            **page,
            "db_init": self.executor.db_initialized(),
            "migrations": migs,
            "pending": pending,
            # Reaproveita a primeira migration vazia pendente; as outras vazias são duplicadas
            "reuse": empty_pending[0] if empty_pending else None,
            "duplicates": empty_pending[1:],
            "table": self._table_exists(name),
            "crud_methods": self._missing_methods(name) == [],
        }

    @staticmethod
    def _show_pages(name: str, page: Dict[str, bool]):
        marks = "  ".join(f"{d} {'✔' if page.get(d) else '—'}" for d in DOMAINS)
        console.print(f"  [dim]fleting list pages →[/dim] {name}: {marks}")

    # ---------------------------------------------------------- controller
    def _controller_file(self, name: str) -> Path:
        return self.project_path / "app" / "controllers" / f"{name}_controller.py"

    def _missing_methods(self, name: str) -> Optional[List[str]]:
        """Métodos CRUD ausentes no controller (None se o controller não existe/está inválido)."""
        path = self._controller_file(name)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            return None
        cls = next((n for n in tree.body if isinstance(n, ast.ClassDef)), None)
        have = {n.name for n in cls.body if isinstance(n, ast.FunctionDef)} if cls else set()
        return [m for m in CRUD_METHODS if m not in have]

    def _add_crud_methods(self, name: str) -> bool:
        """Acrescenta listar/buscar/criar/atualizar/excluir ao controller (só os que faltam)."""
        path = self._controller_file(name)
        missing = self._missing_methods(name)
        if missing is None:
            return False
        code = path.read_text(encoding="utf-8").rstrip() + "\n"
        for m in missing:
            code += "\n" + CRUD_METHODS[m]
        compile(code, str(path), "exec")  # nunca grava arquivo quebrado
        path.write_text(code, encoding="utf-8")
        return True

    # ------------------------------------------------------------- execução
    def _run(self, result: Dict, step: str, args: List[str]) -> bool:
        code, output = self.executor.execute(args, preconfirmed=True)
        ok = code == 0
        console.print(f"  {'✅' if ok else '❌'} fleting {' '.join(args)}")
        result["steps"].append({"step": step, "success": ok,
                                "message": f"fleting {' '.join(args)}" if ok else output})
        if not ok:
            result["errors"].append(f"{step}: {(output or 'falhou').strip()[-300:]}")
        return ok

    @staticmethod
    def _migration_code(name: str, fields: List[Tuple[str, str]]) -> str:
        cols = ",\n            ".join(f"{f} {t}" for f, t in fields)
        return f'''"""
Migration: {name} (gerada pelo FLAI)
"""
from core.database import is_mysql


def up(db):
    pk = "INT AUTO_INCREMENT PRIMARY KEY" if is_mysql() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    cur = db.cursor()
    cur.execute(f\'\'\'
        CREATE TABLE IF NOT EXISTS {name} (
            id {{pk}},
            {cols}
        )
    \'\'\')
    cur.close()


def down(db):
    cur = db.cursor()
    cur.execute("DROP TABLE IF EXISTS {name}")
    cur.close()
'''

    def create(self, entity: Optional[str], fields: Optional[List[str]] = None) -> Dict:
        result = {"success": False, "type": "crud_result", "entity": entity or "",
                  "fields": fields or [], "steps": [], "errors": []}
        try:
            name = fleting_name(entity or "")
        except FletingNameError as e:
            result["errors"].append(str(e))
            return result
        result["entity"] = name
        if not self.executor.is_available():
            result["errors"].append("Fleting não encontrado. Instale com: pip install fleting")
            return result

        # 1. Diagnóstico (fleting list pages + migrations + banco)
        state = self.diagnose(name)
        self._show_pages(name, state)
        if state["table"] and all(state[d] for d in DOMAINS) and state["crud_methods"]:
            result["success"] = True
            result["steps"].append({"step": "check", "success": True,
                                    "message": f"CRUD '{name}' completo (tabela, model, controller, "
                                               "view e rota): nada a fazer."})
            return result

        # Campos só são necessários se a migração ainda vai ser feita
        cols: List[Tuple[str, str]] = []
        if not state["table"]:
            if not fields and self.ask:
                default = DEFAULT_FIELDS.get(name, "nome, descricao")
                answer = self.ask(f"Campos de '{name}' (ex.: nome, idade:int, preco:float)", default)
                fields = [f for f in re.split(r"[,;]\s*|\s+e\s+", answer or default) if f.strip()]
            cols = parse_fields(fields or [])
            if not cols:
                result["errors"].append("Informe ao menos um campo (ex.: nome, email).")
                return result
            result["fields"] = [f for f, _ in cols]

        # 2. Plano, por domínio e nesta ordem
        plan: List[Tuple[str, str, str]] = []  # (domínio, etapa, descrição)
        if state["table"]:
            console.print(f"  ⏭️ migração: tabela '{name}' já existe")
        else:
            if not state["db_init"]:
                plan.append(("migração", "db_init", "fleting db init"))
            if state["reuse"]:
                plan.append(("migração", "write", f"preencher {state['reuse'].name} (vazia) com CREATE TABLE"))
            elif state["pending"]:
                result["errors"].append(
                    f"Já existe migration pendente com código: {state['pending'][-1].name}. "
                    "Revise-a e rode 'fleting db migrate'.")
                return result
            else:
                plan.append(("migração", "db_make", f"fleting db make {name} + CREATE TABLE"))
            plan.append(("migração", "db_migrate", "fleting db migrate"))
        if not state["model"]:
            plan.append(("model", "model", f"fleting create model {name}"))
        if not state["controller"]:
            plan.append(("controller", "controller", f"fleting create controller {name}"))
        if not state["controller"] or not state["crud_methods"]:
            plan.append(("controller", "methods", "métodos " + ", ".join(CRUD_METHODS)))
        if not (state["view"] and state["route"]):
            falta = " e ".join(x for x, ok in (("view", state["view"]), ("rota", state["route"])) if not ok)
            plan.append(("view", "page", f"fleting create page {name} ({falta})"))
        plan.append(("verificação", "verify", "fleting list pages, migration, tabela e sintaxe"))

        console.print(f"\n[bold cyan]📋 Plano: CRUD '{name}'[/bold cyan]")
        if cols:
            console.print("  tabela: id, " + ", ".join(f"{f} {t}" for f, t in cols))
        for i, (dom, _, desc) in enumerate(plan, 1):
            console.print(f"  {i}. [bold]{dom}[/bold]: {desc}")
        for dup in state["duplicates"]:
            console.print(f"  [yellow]⚠️ {dup.name} também está vazia (duplicada): "
                          "apague-a para não confundir.[/yellow]")
        if not (self.confirm and self.confirm("Executar o plano?")):
            result["errors"].append("Cancelado pelo usuário.")
            return result

        # 3. Execução
        migration = state["reuse"]
        for _, step, _ in plan:
            if step == "db_init" and not self._run(result, step, ["db", "init"]):
                return result
            if step == "db_make":
                if not self._run(result, step, ["db", "make", name]):
                    return result
                pending = [m for m in self._migrations_for(name) if m.stem not in self._applied()]
                migration = pending[-1] if pending else None
            if step in ("write", "db_make"):
                if not migration:
                    result["errors"].append("Migration não encontrada após 'db make'.")
                    return result
                migration.write_text(self._migration_code(name, cols), encoding="utf-8")
                console.print(f"  ✅ {migration.name}: CREATE TABLE {name}")
            if step == "db_migrate" and not self._run(result, step, ["db", "migrate"]):
                return result
            if step == "model" and not self._run(result, step, ["create", "model", name]):
                return result
            if step == "controller" and not self._run(result, step, ["create", "controller", name]):
                return result
            if step == "methods":
                try:
                    ok = self._add_crud_methods(name)
                except SyntaxError as e:
                    ok, e_msg = False, str(e)
                else:
                    e_msg = "controller ausente ou inválido"
                console.print(f"  {'✅' if ok else '❌'} {name}_controller: métodos CRUD")
                if not ok:
                    result["errors"].append(f"controller: {e_msg}")
                    return result
            if step == "page" and not self._run(result, step, ["create", "page", name]):
                return result

        # 4. Verificação
        page = self.pages().get(name, {})
        checks = [(page.get(d, False), f"{d} ({FILE_OF[d].format(name=name)})") for d in DOMAINS]
        checks.append((self._missing_methods(name) == [], f"{name}_controller: métodos CRUD"))
        for d in ("model", "controller", "view"):
            f = self.project_path / FILE_OF[d].format(name=name)
            try:
                compile(f.read_text(encoding="utf-8"), str(f), "exec")
                ok = True
            except (OSError, SyntaxError):
                ok = False
            checks.append((ok, f"sintaxe de {f.name}"))
        if migration is not None:
            checks.append((migration.stem in self._applied(), f"migration {migration.name} aplicada"))
        if self._db_path():
            checks.append((self._table_exists(name), f"tabela '{name}' no banco"))
        console.print("[bold]🔎 Verificação[/bold]")
        self._show_pages(name, page)
        for ok, label in checks:
            if not ok:
                console.print(f"  ❌ {label}")
                result["errors"].append(f"Verificação falhou: {label}")
        if not result["errors"]:
            console.print(f"  ✅ {len(checks)} verificações ok")

        result["steps"].append({
            "step": "next", "success": True,
            "message": f"Quer que eu crie a listagem de {name} na {name}_view?",
        })
        result["success"] = not result["errors"]
        return result

    def analyze(self, entity: str, entity_type: str = "controller") -> Dict:
        files = list(self.project_path.glob(f"app/**/{entity}*.py"))
        if not files:
            return {"success": False, "message": f"{entity_type} '{entity}' não encontrado"}
        return {"success": True, "entity": entity, "path": str(files[0])}
