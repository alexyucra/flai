from pathlib import Path
from flai.cli.utils.fs import write_utf8, read_utf8

CHECKLIST_TEMPLATE = """# Checklist do Projeto Fleting

## Estrutura
- [x] Pasta app encontrada
- [ ] MVC bem definido
- [ ] Separação clara entre UI e lógica

## Models
- [ ] Tipagem adequada
- [ ] Validações de dados
- [ ] Repositórios isolados

## Controllers
- [ ] Controllers finos
- [ ] Tratamento de erros
- [ ] Sem lógica de UI

## Views (Flet)
- [ ] Componentes reutilizáveis
- [ ] Layouts organizados

## Configurações
- [ ] configs por ambiente
- [ ] Segredos fora do código

## Próximos Passos
- [ ] Criar service layer
- [ ] Adicionar testes
- [ ] Automatizar migrations
"""

def create_checklist(project_root: Path):
    checklist_dir = project_root / "checklist"
    checklist_dir.mkdir(exist_ok=True)

    checklist_file = checklist_dir / "checklists.md"

    if not checklist_file.exists():
        write_utf8(checklist_file, CHECKLIST_TEMPLATE)

    return checklist_file
