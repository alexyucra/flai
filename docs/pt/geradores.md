# Geradores: CRUD, listagem e comandos Fleting

Tarefas com várias etapas e formato conhecido são feitas por **código determinístico**, não
pelo modelo. O resultado é sempre igual, rápido e verificado. O modelo só decide **quando**
usar cada gerador.

## CRUD

```text
criar crud de produtos com os campos: nome, preco:float, estoque:int
```

Também é acionado pelo assistente (ferramenta `criar_crud`) quando você pede algo como
"vamos construir um crud de clientes".

### Fluxo: diagnosticar → planejar → confirmar → executar → verificar

```mermaid
flowchart TD
    D[Diagnóstico<br/>página? migrations? banco? tabela?] -->|tabela já existe| N[Nada a fazer]
    D --> C{Campos informados?}
    C -->|não| Q[Pergunta os campos<br/>com sugestão]
    C -->|sim| P
    Q --> P[Plano: só o que falta]
    P --> K{Executar o plano?}
    K -->|não| X[Cancelado]
    K -->|sim| E[create page · db init · db make<br/>CREATE TABLE · db migrate]
    E --> V[Verificação<br/>view · migration aplicada · tabela]
    V --> S[Sugere: criar a listagem?]
```

1. **Diagnóstico**: verifica se a página já existe, se há migrations da entidade (aplicadas
   ou pendentes, vazias ou com código), se o banco foi inicializado e se a tabela existe.
   Repetir o pedido **não duplica nada**.
2. **Campos**: se não vierem no pedido, o FLAI pergunta e sugere uma lista.
3. **Plano**: mostra só os passos que faltam e avisa sobre migrations duplicadas e vazias.
4. **Uma confirmação** para o plano inteiro, incluindo o `fleting db migrate`.
5. **Execução** e **verificação**: arquivo da view, registro em `_fleting_migrations` e a
   tabela no SQLite.

```text
📋 Plano: CRUD 'produtos'
  tabela: id, nome VARCHAR(255), preco REAL, estoque INTEGER
  1. fleting create page produtos
  2. fleting db make produtos  + CREATE TABLE
  3. fleting db migrate
⚠️ Executar o plano? [s/N]: s
  ✅ fleting create page produtos
  ✅ fleting db make produtos
  ✅ 002_produtos.py: CREATE TABLE produtos
  ✅ fleting db migrate
🔎 Verificação
  ✅ app/views/pages/produtos_view.py
  ✅ migration 002_produtos.py aplicada
  ✅ tabela 'produtos' no banco
Quer que eu crie a listagem de produtos na produtos_view?
```

### Tipos de campo

Informe com `nome:tipo` ou deixe o FLAI inferir pelo nome:

| Você escreve | SQL |
|---|---|
| `nome`, `email`, `nome:str` | `VARCHAR(255)` |
| `descricao`, `obs`, `bio`, `x:texto` | `TEXT` |
| `idade`, `quantidade`, `estoque`, `ano`, `cliente_id`, `x:int` | `INTEGER` |
| `preco`, `valor`, `salario`, `total`, `x:float` | `REAL` |
| `ativo`, `is_admin`, `tem_x`, `x:bool` | `BOOLEAN` |
| `data`, `nascimento`, `data_x`, `x:date` | `DATE` |
| `x:datetime` | `DATETIME` |

O `id` é criado automaticamente, compatível com SQLite (`INTEGER PRIMARY KEY AUTOINCREMENT`)
e MySQL/MariaDB (`INT AUTO_INCREMENT PRIMARY KEY`).

### Migration gerada

```python
from core.database import is_mysql


def up(db):
    pk = "INT AUTO_INCREMENT PRIMARY KEY" if is_mysql() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    cur = db.cursor()
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS produtos (
            id {pk},
            nome VARCHAR(255),
            preco REAL,
            estoque INTEGER
        )
    ''')
    cur.close()


def down(db):
    cur = db.cursor()
    cur.execute("DROP TABLE IF EXISTS produtos")
    cur.close()
```

## Listagem

```text
crie a listagem de produtos na produtos_view
```

Ou responda `sim` à sugestão feita após o CRUD. A ferramenta `criar_listagem`:

1. lê as colunas do `CREATE TABLE` da migration da entidade;
2. adiciona `listar()` ao controller, se não existir:
   ```python
   def listar(self):
       return self.model.all()
   ```
3. reescreve o `render()` da view com um `ft.DataTable`:

```python
def render(self):
    try:
        rows = self.controller.listar()
        error = None
    except Exception as e:  # tabela ainda não migrada, banco indisponível...
        rows, error = [], str(e)

    table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Nome")),
            ft.DataColumn(label=ft.Text("Preco")),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(row.get("nome", "")))),
                ft.DataCell(ft.Text(str(row.get("preco", "")))),
            ])
            for row in rows
        ],
    )
    ...
```

Cada arquivo passa por diff e confirmação, e pode ser revertido com `/desfazer`.

## Comandos Fleting

Escreva o comando direto ou peça em linguagem natural ("liste as páginas", "rode o doctor").

| Comando | Confirmação |
|---|---|
| `fleting create page\|view\|model\|controller <nome>` | não |
| `fleting list pages\|views\|models\|controllers` | não |
| `fleting list routes` | **sim** (importa código do projeto) |
| `fleting db init\|make <nome>\|status` | não |
| `fleting db migrate\|rollback\|seed` | **sim** (executa código do projeto) |
| `fleting delete page\|view\|model\|controller <nome>` | **sim** (apaga arquivos) |
| `fleting info`, `fleting doctor` | não |
| `fleting run`, `fleting init` e qualquer outro | **bloqueado** |

Nomes são normalizados (`Ordem-Compra` → `ordem_compra`). Nomes com `../`, comandos fora da
allowlist e argumentos extras são recusados. Veja [Segurança](seguranca.md).
