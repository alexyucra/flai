"""
CRUD Agent - Orquestra a criação de CRUD com a CLI do Fleting

Fluxo: diagnosticar → planejar → confirmar (uma vez) → executar → verificar

  1. Diagnóstico: o que já existe (página, migrations da entidade, banco, tabela)
  2. Campos: se o pedido não trouxe, pergunta (com sugestão)
  3. Plano: mostra só o que falta fazer; uma única confirmação
  4. Execução:
       fleting create page <nome>   (só se a página não existe)
       fleting db init              (só se não há migrations/)
       fleting db make <nome>       (só se não há migration pendente reaproveitável)
       escreve CREATE TABLE na migration (só se ela está vazia)
       fleting db migrate
  5. Verificação: arquivos, migration registrada e tabela criada no SQLite
"""
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

    def diagnose(self, name: str) -> Dict:
        applied = set(self._applied())
        migs = self._migrations_for(name)
        pending = [m for m in migs if m.stem not in applied]
        empty_pending = [m for m in pending if EMPTY_UP.search(m.read_text(encoding="utf-8"))]
        return {
            "page": (self.project_path / "app" / "views" / "pages" / f"{name}_view.py").exists(),
            "db_init": self.executor.db_initialized(),
            "migrations": migs,
            "pending": pending,
            # Reaproveita a primeira migration vazia pendente; as outras vazias são duplicadas
            "reuse": empty_pending[0] if empty_pending else None,
            "duplicates": empty_pending[1:],
            "table": self._table_exists(name),
        }

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

        # 1. Diagnóstico
        state = self.diagnose(name)
        if state["table"]:
            result["success"] = True
            result["steps"].append({"step": "check", "success": True,
                                    "message": f"Tabela '{name}' já existe no banco: nada a fazer."})
            return result

        # 2. Campos
        if not fields and self.ask:
            default = DEFAULT_FIELDS.get(name, "nome, descricao")
            answer = self.ask(f"Campos de '{name}' (ex.: nome, idade:int, preco:float)", default)
            fields = [f for f in re.split(r"[,;]\s*|\s+e\s+", answer or default) if f.strip()]
        cols = parse_fields(fields or [])
        if not cols:
            result["errors"].append("Informe ao menos um campo (ex.: nome, email).")
            return result
        result["fields"] = [f for f, _ in cols]

        # 3. Plano
        plan: List[Tuple[str, str]] = []
        if state["page"]:
            console.print(f"  ⏭️ página '{name}' já existe")
        else:
            plan.append(("create_page", f"fleting create page {name}"))
        if not state["db_init"]:
            plan.append(("db_init", "fleting db init"))
        if state["reuse"]:
            plan.append(("write", f"preencher {state['reuse'].name} (vazia) com CREATE TABLE"))
        elif state["pending"]:
            result["errors"].append(
                f"Já existe migration pendente com código: {state['pending'][-1].name}. "
                "Revise-a e rode 'fleting db migrate'.")
            return result
        else:
            plan.append(("db_make", f"fleting db make {name}  + CREATE TABLE"))
        plan.append(("db_migrate", "fleting db migrate"))

        console.print(f"\n[bold cyan]📋 Plano: CRUD '{name}'[/bold cyan]")
        console.print("  tabela: id, " + ", ".join(f"{f} {t}" for f, t in cols))
        for i, (_, desc) in enumerate(plan, 1):
            console.print(f"  {i}. {desc}")
        for dup in state["duplicates"]:
            console.print(f"  [yellow]⚠️ {dup.name} também está vazia (duplicada): "
                          "apague-a para não confundir.[/yellow]")
        if not (self.confirm and self.confirm("Executar o plano?")):
            result["errors"].append("Cancelado pelo usuário.")
            return result

        # 4. Execução
        migration = state["reuse"]
        for step, _ in plan:
            if step == "create_page" and not self._run(result, step, ["create", "page", name]):
                return result
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

        # 5. Verificação
        ok_table = self._table_exists(name) if self._db_path() else None
        checks = [
            (state["page"] or (self.project_path / "app/views/pages" / f"{name}_view.py").exists(),
             f"app/views/pages/{name}_view.py"),
            (migration is not None and migration.stem in self._applied(),
             f"migration {migration.name if migration else '?'} aplicada"),
        ]
        if ok_table is not None:
            checks.append((ok_table, f"tabela '{name}' no banco"))
        console.print("[bold]🔎 Verificação[/bold]")
        for ok, label in checks:
            console.print(f"  {'✅' if ok else '❌'} {label}")
            if not ok:
                result["errors"].append(f"Verificação falhou: {label}")

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
