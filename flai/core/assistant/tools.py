"""
Ferramentas que o modelo pode chamar (tool calling do Ollama).

Regras de segurança:
  - todo caminho passa por safe_join (nada fora do projeto; .flai/.git/venv bloqueados)
  - escrita: mostra diff → pede confirmação → guarda backup (/desfazer) → verifica sintaxe
  - comandos: só a allowlist do FletingExecutor (os sensíveis pedem confirmação)
  - saídas truncadas para caber no contexto pequeno do modelo local
"""
from __future__ import annotations

import difflib
import json
import py_compile
import re
import shutil
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from flai.cli.console.console import console
from flai.core.security import safe_join
from flai.core.executors.fleting_executor import FletingExecutor

MAX_READ_CHARS = 3000
MAX_OUTPUT_CHARS = 1500
BLOCKED_PARTS = {".flai", ".git", ".venv", "venv", "__pycache__", "node_modules", "data"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".html", ".css"}


def _fn(name: str, description: str, props: Dict, required: List[str]) -> Dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": props, "required": required}}}


S = {"type": "string"}
TOOL_SPECS = [
    _fn("listar_arquivos", "Lista arquivos de uma pasta do projeto.",
        {"pasta": {**S, "description": "ex.: app, app/views/pages, configs"}}, []),
    _fn("ler_arquivo", "Lê um arquivo do projeto (código fonte).",
        {"caminho": {**S, "description": "caminho relativo, ex.: app/models/usuarios_model.py"}},
        ["caminho"]),
    _fn("buscar_no_codigo", "Procura um texto em todos os arquivos .py do projeto.",
        {"texto": S}, ["texto"]),
    _fn("editar_arquivo", "Substitui um trecho EXATO de um arquivo existente por outro.",
        {"caminho": S, "buscar": {**S, "description": "trecho exato atual"},
         "substituir": {**S, "description": "novo trecho"}}, ["caminho", "buscar", "substituir"]),
    _fn("escrever_metodo", "Cria um método novo ou SUBSTITUI um método inteiro (pelo nome) numa "
        "classe. Envie o def completo; a indentação é automática.",
        {"caminho": S, "classe": {**S, "description": "ex.: UsuariosController"},
         "codigo": {**S, "description": "o def completo, ex.: def listar(self):\n    return self.model.all()"}},
        ["caminho", "codigo"]),
    _fn("criar_arquivo", "Cria um arquivo novo ou reescreve um arquivo inteiro.",
        {"caminho": S, "conteudo": S}, ["caminho", "conteudo"]),
    _fn("criar_listagem", "Gera a listagem (tabela) dos registros de uma entidade na view dela "
        "(colunas lidas da migration). Use para 'listagem', 'listar na tela', 'tabela na view'.",
        {"entidade": {**S, "description": "ex.: usuarios"}}, ["entidade"]),
    _fn("criar_crud","Cria CRUD Fleting completo: página, migration com tabela e migrate.",
        {"entidade": {**S, "description": "nome no plural, ex.: produtos"},
         "campos": {**S, "description": "ex.: nome, preco:float, ativo:bool"}}, ["entidade"]),
    _fn("fleting", "Executa a CLI do Fleting.",
        {"comando": {**S, "description": "ex.: list pages | create page contato | db status | doctor"}},
        ["comando"]),
    _fn("verificar_projeto", "Verifica a sintaxe de todos os .py do projeto.", {}, []),
]
TOOL_NAMES = {t["function"]["name"] for t in TOOL_SPECS}

READ_TOOLS = {"listar_arquivos", "ler_arquivo", "buscar_no_codigo"}
TOOL_TRIGGERS = [
    # (regex no pedido, ferramentas liberadas)
    (r"m[eé]todo|fun[cç][aã]o|\bdef\b", {"escrever_metodo"}),
    (r"adicion|acrescent|inclu|alter|mud[ea]|troc|substitu|corrij|corrig|edit|ajust|remov|apag|"
     r"renome|implement|listagem|lista\b|mostr\w* .*(view|tela|p[aá]gina)|coloq|bot[aã]o|campo",
     {"editar_arquivo", "escrever_metodo"}),
    (r"listag|listar|lista de|tabela n[ao]|mostr\w* (os|as|todos)", {"criar_listagem"}),
    (r"cri[ea]r?\b|gere|novo arquivo|nova (view|p[aá]gina|tela)", {"criar_arquivo", "editar_arquivo"}),
    (r"crud|tabela|migra", {"criar_crud", "fleting"}),
    (r"fleting|rod[ae]r?|execut|status|doctor|rotas|routes", {"fleting"}),
    (r"verific|verifiq|sintaxe|erro|quebr|valid|cheq|confer", {"verificar_projeto"}),
]


def select_tools(text: str) -> List[Dict]:
    """
    Só as ferramentas relevantes para o pedido. Com 3 opções em vez de 9, um modelo de 3B
    escolhe certo com muito mais frequência (perguntas recebem só ferramentas de leitura).
    """
    low = text.lower()
    allowed = set(READ_TOOLS)
    for pattern, names in TOOL_TRIGGERS:
        if re.search(pattern, low):
            allowed |= names
    # Método novo/alterado: esconde editar_arquivo para não competir com escrever_metodo
    if re.search(r"m[eé]todo|fun[cç][aã]o|def", low):
        allowed.discard("editar_arquivo")
    return [t for t in TOOL_SPECS if t["function"]["name"] in allowed]


class BackupStore:
    """Backups por alteração, para /desfazer (pilha)."""

    def __init__(self, project_path: Path):
        self.root = project_path / ".flai" / "backups"
        self.project_path = project_path

    def save(self, target: Path) -> None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        d = self.root / stamp
        d.mkdir(parents=True, exist_ok=True)
        rel = target.relative_to(self.project_path).as_posix()
        existed = target.exists()
        if existed:
            shutil.copy2(target, d / "file")
        (d / "manifest.json").write_text(json.dumps({"path": rel, "existed": existed}),
                                         encoding="utf-8")

    def undo(self) -> Optional[str]:
        if not self.root.exists():
            return None
        entries = sorted(p for p in self.root.iterdir() if (p / "manifest.json").exists())
        if not entries:
            return None
        last = entries[-1]
        info = json.loads((last / "manifest.json").read_text(encoding="utf-8"))
        target = safe_join(self.project_path, info["path"])
        if info["existed"]:
            shutil.copy2(last / "file", target)
            msg = f"↩️ {info['path']} restaurado"
        else:
            target.unlink(missing_ok=True)
            msg = f"↩️ {info['path']} removido (tinha sido criado)"
        shutil.rmtree(last)
        return msg


class ToolBox:
    def __init__(self, project_path: Path, executor: FletingExecutor,
                 confirm: Optional[Callable[[str], bool]] = None,
                 crud_agent=None, session=None):
        self.project_path = Path(project_path).resolve()
        self.executor = executor
        self.confirm = confirm
        self.crud_agent = crud_agent
        self.session = session
        self.backups = BackupStore(self.project_path)
        self.changed_files: List[str] = []
        self.failed_writes: List[str] = []  # alterações rejeitadas/canceladas no turno

    # ------------------------------------------------------------- despacho
    def run(self, name: str, args) -> str:
        if isinstance(args, str):  # alguns modelos mandam argumentos como string JSON
            try:
                args = json.loads(args)
            except ValueError:
                args = {}
        args = args if isinstance(args, dict) else {}
        handler = getattr(self, f"t_{name}", None)
        if name not in TOOL_NAMES or not handler:
            return f"ERRO: ferramenta '{name}' não existe. Use: {', '.join(sorted(TOOL_NAMES))}"
        try:
            out = handler(**{k: v for k, v in args.items() if isinstance(k, str)})
        except TypeError as e:
            return f"ERRO: argumentos inválidos para {name}: {e}"
        except Exception as e:
            return f"ERRO em {name}: {e}"
        out = str(out)
        if len(out) > MAX_OUTPUT_CHARS and name != "ler_arquivo":
            out = out[:MAX_OUTPUT_CHARS] + "\n...(truncado)"
        return out

    # ------------------------------------------------------------- caminhos
    def _path(self, rel: str) -> Path:
        rel = (rel or "").strip().strip("'\"`").replace("\\", "/")
        rel = re.sub(rf"^{re.escape(self.project_path.name)}/", "", rel)  # "demo/app/x" → "app/x"
        p = safe_join(self.project_path, rel)
        if BLOCKED_PARTS & set(p.relative_to(self.project_path).parts):
            raise PermissionError(f"pasta protegida: {rel}")
        return p

    def _rel(self, p: Path) -> str:
        return p.relative_to(self.project_path).as_posix()

    def _touch(self, p: Path) -> None:
        if self.session:
            self.session.touch_file(self._rel(p))

    # --------------------------------------------------------------- leitura
    def t_listar_arquivos(self, pasta: str = "app") -> str:
        d = self._path(pasta or ".")
        if not d.is_dir():
            return f"ERRO: pasta não encontrada: {pasta}"
        files = [self._rel(f) for f in sorted(d.rglob("*"))
                 if f.is_file() and f.suffix in TEXT_SUFFIXES
                 and not BLOCKED_PARTS & set(f.relative_to(self.project_path).parts)]
        return "\n".join(files[:80]) or "(vazia)"

    def t_ler_arquivo(self, caminho: str) -> str:
        p = self._path(caminho)
        if not p.is_file():
            # tolera nome sem pasta: "usuarios_view" → app/views/pages/usuarios_view.py
            stem = Path(caminho).stem
            hits = [f for f in self.project_path.glob(f"app/**/{stem}*.py")]
            if not hits:
                return f"ERRO: arquivo não encontrado: {caminho}"
            p = hits[0]
        text = p.read_text(encoding="utf-8", errors="replace")
        self._touch(p)
        if len(text) > MAX_READ_CHARS:
            text = text[:MAX_READ_CHARS] + f"\n...(truncado, {len(text)} caracteres no total)"
        return f"# {self._rel(p)}\n{text}"

    def t_buscar_no_codigo(self, texto: str) -> str:
        if not texto:
            return "ERRO: informe o texto"
        hits = []
        for f in sorted(self.project_path.rglob("*.py")):
            if BLOCKED_PARTS & set(f.relative_to(self.project_path).parts):
                continue
            for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if texto.lower() in line.lower():
                    hits.append(f"{self._rel(f)}:{i}: {line.strip()[:120]}")
                    if len(hits) >= 20:
                        return "\n".join(hits)
        return "\n".join(hits) or "nenhum resultado"

    # --------------------------------------------------------------- escrita
    def _write(self, p: Path, new: str) -> str:
        old = p.read_text(encoding="utf-8") if p.exists() else ""
        rel = self._rel(p)
        if old == new:
            return f"{rel}: nenhuma alteração"
        # Valida ANTES de mostrar ao usuário: diff quebrado volta direto para o modelo corrigir
        if p.suffix == ".py":
            err = self._syntax_error_of(new, rel)
            if err:
                console.print(f"  [dim]↻ proposta para {rel} com erro de sintaxe ({err}); "
                              "pedindo correção ao modelo[/dim]")
                self.failed_writes.append(rel)
                bad = new.splitlines()
                ln = int(re.search(r"linha (\d+)", err).group(1)) if re.search(r"linha (\d+)", err) else 0
                around = "\n".join(f"{i + 1}: {bad[i]}" for i in range(max(0, ln - 4), min(len(bad), ln + 2)))
                return (f"REJEITADO: o resultado teria erro de sintaxe ({err}). Arquivo NÃO alterado.\n"
                        f"Trecho resultante com problema:\n{around}\n"
                        "Corrija e chame a ferramenta de novo, com 'buscar' cobrindo o bloco inteiro "
                        "que será substituído.")
        diff = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                            f"a/{rel}", f"b/{rel}", n=2))
        self._show_diff(diff, rel, created=not p.exists())
        if not (self.confirm and self.confirm(f"Aplicar alteração em {rel}?")):
            self.failed_writes.append(rel)
            return f"CANCELADO pelo usuário: {rel} não foi alterado. Pergunte o que ajustar."
        self.backups.save(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(new, encoding="utf-8")
        self.changed_files.append(rel)
        if rel in self.failed_writes:
            self.failed_writes.remove(rel)
        self._touch(p)
        console.print(f"  [green]✅ {rel} salvo (/desfazer para reverter)[/green]")
        return f"OK: {rel} salvo e sintaxe válida."

    @staticmethod
    def _syntax_error_of(source: str, rel: str) -> Optional[str]:
        try:
            compile(source, rel, "exec")
            return None
        except SyntaxError as e:
            return f"linha {e.lineno}: {e.msg}"

    @staticmethod
    def _show_diff(diff: str, rel: str, created: bool) -> None:
        from rich.syntax import Syntax
        console.print(f"\n[bold]{'🆕 criar' if created else '✏️ editar'} {rel}[/bold]")
        lines = diff.splitlines()
        if len(lines) > 60:
            diff = "\n".join(lines[:60] + [f"... (+{len(lines) - 60} linhas)"])
        console.print(Syntax(diff, "diff", theme="ansi_dark", word_wrap=True))

    @staticmethod
    def _syntax_error(p: Path) -> Optional[str]:
        try:
            py_compile.compile(str(p), doraise=True)
            return None
        except py_compile.PyCompileError as e:
            return str(e.exc_value).splitlines()[0] if e.exc_value else str(e)

    def t_editar_arquivo(self, caminho: str, buscar: str, substituir: str) -> str:
        p = self._path(caminho)
        if not p.is_file():
            return f"ERRO: arquivo não encontrado: {caminho}. Use criar_arquivo."
        text = p.read_text(encoding="utf-8")
        target = buscar if buscar and buscar in text else self._loose_match(text, buscar or "")
        if not target:
            if "def " in (substituir or "") and "def " in (buscar or ""):
                return ("ERRO: esse método não existe no arquivo. Para criar um método novo use "
                        "escrever_metodo(caminho, classe, codigo).")
            return ("ERRO: o trecho 'buscar' não existe no arquivo. Copie o trecho exato do "
                    "conteúdo do arquivo.")
        count = text.count(target)
        if count > 1:
            return f"ERRO: o trecho aparece {count} vezes; inclua mais linhas para ficar único."
        # Reindenta: modelos pequenos erram espaços. Usa a indentação da linha do trecho.
        start = text.index(target)
        line_start = text.rfind("\n", 0, start) + 1
        prefix = text[line_start:start]
        if prefix.strip() == "":
            body = textwrap.dedent(substituir.expandtabs(4)).strip("\n")
            first, *rest = body.split("\n")
            substituir = first + "".join("\n" + (prefix + l if l.strip() else "") for l in rest)
        return self._write(p, text.replace(target, substituir, 1))

    @staticmethod
    def _loose_match(text: str, buscar: str) -> Optional[str]:
        """Encontra o trecho ignorando diferenças de indentação/espaços nas pontas das linhas."""
        want = [l.strip() for l in buscar.strip().splitlines() if l.strip()]
        if not want:
            return None
        lines = text.splitlines(keepends=True)
        for i in range(len(lines)):
            if not lines[i].strip():
                continue  # começar numa linha em branco perderia a indentação do trecho
            j, k = i, 0
            while j < len(lines) and k < len(want):
                if not lines[j].strip():
                    j += 1
                    continue
                if lines[j].strip() != want[k]:
                    break
                j, k = j + 1, k + 1
            if k == len(want):
                first = lines[i]
                chunk = "".join(lines[i:j]).rstrip("\n")
                return chunk[len(first) - len(first.lstrip()):]  # sem a indentação inicial
        return None

    def t_escrever_metodo(self, caminho: str, codigo: str, classe: str = "") -> str:
        import ast
        p = self._path(caminho)
        if not p.is_file():
            return f"ERRO: arquivo não encontrado: {caminho}"
        text = p.read_text(encoding="utf-8")
        tree = ast.parse(text)
        classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
        cls = next((c for c in classes if c.name == classe), None) or (classes[0] if len(classes) == 1 else None)
        if not cls:
            return f"ERRO: classe '{classe}' não encontrada. Classes: {', '.join(c.name for c in classes)}"
        code = self._normalize_def(codigo)
        if not code.lstrip().startswith(("def ", "async def ", "@")):
            return "ERRO: 'codigo' deve ser um def completo (começando com 'def nome(self...'):'."
        name = re.search(r"def\s+(\w+)", code).group(1)
        indent = " " * (cls.body[0].col_offset if cls.body else cls.col_offset + 4)
        method = "\n".join(indent + l if l.strip() else "" for l in code.split("\n"))
        lines = text.splitlines(keepends=True)
        existing = next((n for n in cls.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                         and n.name == name), None)
        if existing:
            # Substitui o método inteiro (inclui decorators)
            start = min([existing.lineno] + [d.lineno for d in existing.decorator_list]) - 1
            new = "".join(lines[:start]) + method + "\n" + "".join(lines[existing.end_lineno:])
        else:
            end = cls.end_lineno  # novo método: logo após a última linha da classe
            new = "".join(lines[:end]).rstrip("\n") + "\n\n" + method + "\n" + "".join(lines[end:])
        return self._write(p, new)

    @staticmethod
    def _normalize_def(codigo: str) -> str:
        """
        Dedent robusto: o modelo costuma mandar 'def x(self):' sem indentação e o corpo
        com a indentação da classe (8 espaços). Ajusta o corpo para 4 relativos ao def.
        """
        lines = codigo.expandtabs(4).strip("\n").split("\n")
        first = next((i for i, l in enumerate(lines) if l.strip()), 0)
        head_indent = len(lines[first]) - len(lines[first].lstrip())
        body = [l for l in lines[first + 1:] if l.strip()]
        body_min = min((len(l) - len(l.lstrip()) for l in body), default=head_indent + 4)
        shift = body_min - (head_indent + 4)  # excesso de indentação do corpo
        out = []
        for i, l in enumerate(lines):
            if i <= first or not l.strip():
                out.append(l[head_indent:] if l.strip() else "")
            else:
                cut = head_indent + max(shift, 0)
                out.append(l[cut:] if len(l) - len(l.lstrip()) >= cut else l.lstrip())
        # Decorators acima do def ficam com a mesma indentação do def
        return "\n".join(out)

    def t_criar_arquivo(self, caminho: str, conteudo: str) -> str:
        return self._write(self._path(caminho), conteudo if conteudo.endswith("\n") else conteudo + "\n")

    # ------------------------------------------------------------- geradores
    def _columns_of(self, name: str) -> List[str]:
        """Colunas do CREATE TABLE da migration da entidade (sem id)."""
        for mig in sorted((self.project_path / "migrations").glob(f"*_{name}.py"), reverse=True):
            m = re.search(rf"CREATE TABLE[^(]*\b{re.escape(name)}\b\s*\((.*?)\n\s*\)",
                          mig.read_text(encoding="utf-8"), re.S | re.I)
            if m:
                cols = [c.group(1) for c in re.finditer(r"^\s*(\w+)\s+\S", m.group(1), re.M)]
                return [c for c in cols if c.lower() != "id"]
        return []

    def t_criar_listagem(self, entidade: str) -> str:
        """Gerador determinístico: listar() no controller + render() com ft.DataTable na view."""
        name = re.sub(r"\W", "", (entidade or "").lower())
        view = self.project_path / "app" / "views" / "pages" / f"{name}_view.py"
        ctrl = self.project_path / "app" / "controllers" / f"{name}_controller.py"
        if not view.exists() or not ctrl.exists():
            return f"ERRO: view/controller de '{name}' não existem. Crie antes com criar_crud."
        cols = self._columns_of(name)
        if not cols:
            return (f"ERRO: não achei a tabela '{name}' nas migrations. Crie com criar_crud "
                    "(define os campos) e tente de novo.")
        results = []
        if "def listar" not in ctrl.read_text(encoding="utf-8"):
            results.append(self.t_escrever_metodo(self._rel(ctrl), "def listar(self):\n"
                                                  "    return self.model.all()"))
            if not results[-1].startswith("OK"):
                return results[-1]
        headers = "\n".join(f'                ft.DataColumn(label=ft.Text("{c.replace("_", " ").capitalize()}")),'
                            for c in cols)
        cells = "\n".join(f'                        ft.DataCell(ft.Text(str(row.get("{c}", "")))),'
                          for c in cols)
        render = f'''def render(self):
    try:
        rows = self.controller.listar()
        error = None
    except Exception as e:  # tabela ainda não migrada, banco indisponível...
        rows, error = [], str(e)

    table = ft.DataTable(
        columns=[
{headers}
        ],
        rows=[
            ft.DataRow(
                cells=[
{cells}
                ]
            )
            for row in rows
        ],
    )
    content = ft.Column(
        controls=[
            ft.Text(self.controller.get_title(), size=24),
            ft.Text(error or f"{{len(rows)}} registro(s)", color=ft.Colors.ERROR if error else None),
            table,
        ],
        spacing=16,
        scroll=ft.ScrollMode.AUTO,
    )

    return MainLayout(
        page=self.page,
        content=content,
        router=self.router,
    )'''
        # o template interno usa 4 espaços relativos ao def; reindenta as linhas da tabela
        render = render.replace("\n                ft.DataColumn", "\n            ft.DataColumn") \
                       .replace("\n                        ft.DataCell", "\n                    ft.DataCell")
        results.append(self.t_escrever_metodo(self._rel(view), render))
        out = " | ".join(results)
        if results[-1].startswith("OK"):
            out += (f"\nListagem de {name} pronta ({', '.join(cols)}). Sugira como próximo passo: "
                    f"'Quer que eu crie o formulário de cadastro de {name}?' ou rodar 'fleting run'.")
        return out

    # -------------------------------------------------------------- comandos
    def t_criar_crud(self, entidade: str, campos: str = "") -> str:
        if not self.crud_agent:
            return "ERRO: CRUD indisponível"
        fields = [f for f in re.split(r"[,;]\s*", campos or "") if f.strip()]
        res = self.crud_agent.create(entidade, fields)
        if res.get("success"):
            return (f"OK: CRUD '{res['entity']}' pronto (campos: {', '.join(res['fields'])}). "
                    + " ".join(s["message"] for s in res["steps"][-1:]))
        return "FALHOU: " + "; ".join(res.get("errors") or ["erro desconhecido"])

    def t_fleting(self, comando: str) -> str:
        args = (comando or "").replace("fleting", "", 1).split() if (comando or "").startswith("fleting") \
            else (comando or "").split()
        code, out = self.executor.execute(args)
        console.print(f"  {'✅' if code == 0 else '❌'} fleting {' '.join(args)}")
        return f"código {code}\n{out or '(sem saída)'}"

    def t_verificar_projeto(self) -> str:
        errors, total = [], 0
        for f in sorted(self.project_path.rglob("*.py")):
            if BLOCKED_PARTS & set(f.relative_to(self.project_path).parts):
                continue
            total += 1
            err = self._syntax_error(f)
            if err:
                errors.append(f"{self._rel(f)}: {err}")
        if errors:
            return f"{len(errors)} erro(s) em {total} arquivos:\n" + "\n".join(errors)
        return f"OK: {total} arquivos .py sem erro de sintaxe."
