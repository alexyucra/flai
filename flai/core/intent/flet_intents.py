# flet_intents.py
"""
Dicionário expandido de intenções para desenvolvedor Flet
"""

FLET_DEVELOPER_INTENTS = {
    # ==================== CRIAÇÃO DE CRUD ====================
    "create_crud": [
        # Verbos principais
        "crud", "criar crud", "crie crud", "crio crud", "criamos crud",
        "fazer crud", "faça crud", "faz crud", "faco crud", "fazemos crud",
        "gerar crud", "gere crud", "gero crud", "geramos crud",
        "montar crud", "monte crud", "monto crud",
        "construir crud", "construa crud", "construo crud",
        "desenvolver crud", "desenvolva crud", "desenvolvo crud",
        "novo crud", "nova crud", "criar novo crud", "fazer novo crud",
        
        # Sinônimos de CRUD
        "tabela", "tabelas", "entidade", "entidades", "model", "models",
        "modelo", "modelos", "recurso", "recursos", "classe", "classes",
        "schema", "schemas", "rota", "rotas", "api", "apis",
        "endpoint", "endpoints", "controller", "controllers",
        
        # Operações CRUD específicas
        "listagem", "lista", "listar", "cadastro", "cadastrar",
        "edicao", "editar", "atualizacao", "atualizar",
        "exclusao", "excluir", "remocao", "remover", "delecao", "deletar",
        "criacao", "insercao", "inserir", "adicionar",
        
        # Expressões comuns
        "tela de crud", "pagina de crud", "sistema de crud",
        "crud completo", "crud basico", "crud simples",
        "operacoes basicas", "operacoes crud",
        
        # Verbos conjugados alternativos
        "criae crud", "criar crud", "criar crud", "criau crud",  # erros comuns
        "faze crud", "fazer crud", "faz crud", "fazcrud",
        "gerar crud", "gerar crud", "gerau crud",
        
        # Gírias de programador
        "crudzao", "crudzão", "crudinho", "crud basicao",
        "tabelinha", "modelzinho", "entidade basica",
        
        # Palavras em inglês (comum em desenvolvimento)
        "crud generator", "generate crud", "make crud", "build crud",
        "scaffold", "scaffolding", "boilerplate",
    ],
    
    # ==================== CRIAÇÃO DE FORMULÁRIOS ====================
    "create_form": [
        # Verbos principais
        "form", "formulario", "formulário", "formularios", "formulários",
        "criar form", "crie form", "crio form", "criamos form",
        "fazer form", "faça form", "faz form", "faco form",
        "gerar form", "gere form", "gero form",
        "montar form", "monte form",
        
        # Sinônimos de formulário
        "ficha", "fichas", "cadastro", "cadastros", "registro", "registros",
        "campos", "inputs", "input", "field", "fields",
        "formulario de", "form de", "formulario para", "form para",
        
        # Tipos de formulário
        "formulario simples", "form basico", "form completo",
        "formulario de contato", "formulario de login", "formulario de registro",
        "formulario de cadastro", "formulario de edicao",
        
        # Componentes de formulário
        "textfield", "text field", "campo texto", "caixa texto",
        "dropdown", "select", "lista suspensa", "opcoes",
        "checkbox", "caixa verificacao", "check box",
        "radio", "radio button", "botao opcao",
        "datepicker", "date picker", "selecionar data",
        "filepicker", "upload arquivo", "file picker",
        
        # Expressões naturais
        "formulario com campos", "form com campos", "formulario contendo",
        "preciso de um form", "quero um formulario", "me de um form",
        
        # Erros comuns
        "formulario", "formulario", "formulario",  # sem acento
        "fomulario", "furmulario", "formularo", "formulari",
        "formulario", "formulario", "formulario",
        
        # Gírias
        "formzinho", "formulario basico", "form rapidinho",
        "tela de form", "pagina de formulario",
        
        # Inglês
        "form builder", "create form", "make form", "build form",
        "input form", "data entry form",
    ],
    
    # ==================== CRIAÇÃO DE PÁGINAS ====================
    "create_page": [
        # Verbos principais
        "pagina", "página", "paginas", "páginas", "page", "pages",
        "criar pagina", "crie pagina", "crio pagina", "criar página",
        "fazer pagina", "faça pagina", "faz pagina",
        "gerar pagina", "gere pagina", "gero pagina",
        "nova pagina", "nova página", "novas paginas",
        
        # Sinônimos
        "tela", "telas", "view", "views", "screen", "screens",
        "rota", "rotas", "route", "routes", "layout", "layouts",
        
        # Tipos de página
        "pagina inicial", "home page", "pagina principal",
        "pagina de login", "pagina de dashboard", "dashboard",
        "pagina de perfil", "pagina de usuario", "pagina de configuracao",
        "pagina de listagem", "pagina de detalhes", "pagina de erro",
        
        # Expressões
        "criar rota", "nova rota", "adicionar pagina", "inserir pagina",
        "pagina com navegacao", "pagina responsiva",
        
        # Erros comuns
        "pagina", "pagina", "pagina",  # sem acento
        "pagina", "pagina", "pagina",
        "pajina", "paginae", "paginas",
        
        # Gírias
        "pagina basica", "telazinha", "view simples",
        "rota nova", "screen basica",
        
        # Inglês
        "create page", "new page", "add page", "generate page",
        "page template", "blank page", "empty page",
    ],
    
    # ==================== CRIAÇÃO DE MODEL/DATABASE ====================
    "create_model": [
        # Verbos principais
        "model", "modelo", "models", "modelos",
        "criar model", "crie model", "criar modelo", "crie modelo",
        "fazer model", "faça model", "fazer modelo",
        "gerar model", "gere model", "gerar modelo",
        "novo model", "novo modelo", "nova entidade",
        
        # Sinônimos
        "entidade", "entidades", "classe", "classes", "schema",
        "tabela", "tabelas", "database", "db", "bd",
        "sql", "sqlite", "postgres", "mysql", "mongodb",
        
        # Campos/modelo
        "model com campos", "modelo com atributos", "entidade com propriedades",
        "mapeamento", "orm", "sqlalchemy", "peewee",
        
        # Operações
        "migration", "migracao", "migrate", "criar tabela",
        "alterar tabela", "modificar schema",
        
        # Expressões
        "modelo de dados", "definir modelo", "criar schema",
        "estrutura de dados", "blueprint",
        
        # Erros comuns
        "modelo", "moddel", "modell", "modelo",
        "entidadi", "entidady", "entridade",
        
        # Gírias
        "modelzinho", "classe basica", "schema simples",
        "model rapidão", "tabelinha",
        
        # Inglês
        "data model", "create model", "define model", "model class",
        "database model", "orm model", "sql model",
    ],
    
    # ==================== ANÁLISE DE COMPONENTES ====================
    "analyze": [
        # Verbos principais
        "analisar", "analise", "analiso", "analisamos", "analisa",
        "ver", "veja", "vejo", "vemos", "olhar", "olhe",
        "mostrar", "mostre", "mostro", "exibir", "exiba",
        "inspecionar", "inspecione", "inspect", "inspectar",
        "estudar", "estude", "estudo", "revisar", "revise",
        
        # Sinônimos
        "visualizar", "visualize", "checar", "cheque", "verificar", "verifique",
        "examinar", "examine", "observar", "observe", "conferir", "confira",
        "validar", "valide", "testar", "teste", "debug", "debugar",
        
        # Alvos de análise
        "controller", "model", "view", "template", "page",
        "componente", "modulo", "funcao", "classe", "metodo",
        "codigo", "codigo fonte", "implementacao",
        
        # Expressões comuns
        "me mostre", "me mostre o", "mostre-me", "exiba o",
        "qual e o", "como esta o", "como foi feito o",
        "analise o codigo", "verifique o componente",
        
        # Erros comuns
        "analizar", "analisa", "analis", "analisr",
        "mostra", "mostr", "mostar", "exibi", "exbir",
        "vizualizar", "vizualize", "inspecionar",
        
        # Gírias
        "dar uma olhada", "batizar um olho", "checar rapidinho",
        "ver como esta", "visualizar estrutura",
        
        # Inglês
        "analyze code", "review code", "check component", "inspect",
        "code review", "show me", "display", "view code",
    ],
    
    # ==================== BUSCA E PESQUISA ====================
    "where": [
        # Verbos principais
        "onde", "where", "cadê", "cade", "onde está", "onde fica",
        "buscar", "busque", "busco", "buscamos", "procurar", "procure",
        "encontrar", "encontre", "encontro", "achar", "ache",
        "localizar", "localize", "pesquisar", "pesquise",
        
        # Sinônimos
        "qual o caminho", "qual a localizacao", "em que parte",
        "em qual arquivo", "em que linha", "qual diretorio",
        "mostrar caminho", "me indique", "diretorio de",
        
        # Alvos de busca
        "arquivo", "pasta", "diretorio", "modulo", "biblioteca",
        "funcao", "classe", "metodo", "variavel", "constante",
        "import", "configuracao", "setup", "inicializacao",
        
        # Expressões comuns
        "onde fica o", "onde esta o", "cadê o", "cade o",
        "onde encontrar", "como acessar", "qual o local",
        "me mostre onde", "procure por", "busque por",
        
        # Erros comuns
        "onde", "ondi", "ond", "cade", "cade", "cad",
        "buscar", "buscarr", "buskar", "procurar", "procurarr",
        "encontrar", "encontrarr", "acharr", "lokalisar",
        
        # Gírias
        "cadê o arquivo", "onde tá", "ondé que tá", "qual o rolê",
        "me acha", "descobrir onde", "localizar rapidinho",
        
        # Inglês
        "where is", "find file", "search for", "locate",
        "file path", "directory", "location of",
    ],
    
    # ==================== REFATORAÇÃO E MELHORIAS ====================
    "refactor": [
        # Verbos principais
        "refatorar", "refatore", "refatoro", "refatoramos",
        "melhorar", "melhore", "melhoro", "melhoramos",
        "otimizar", "otimize", "otimizo", "otimizamos",
        "reestruturar", "reestruture", "reorganizar", "reorganize",
        "simplificar", "simplifique", "limpar", "limpe",
        
        # Sinônimos
        "refinar", "refine", "aprimorar", "aprimore",
        "revisar", "revise", "reformular", "reformule",
        "reimplementar", "reimplemente", "reconstruir", "reconstrua",
        "modernizar", "modernize", "atualizar", "atualize",
        
        # O que refatorar
        "codigo", "funcao", "metodo", "classe", "modulo",
        "componente", "controller", "service", "util",
        "logica", "implementacao", "algoritmo",
        
        # Expressões comuns
        "deixar melhor", "deixar mais limpo", "deixar mais eficiente",
        "remover duplicacao", "melhorar estrutura", "simplificar logica",
        "aplicar boas praticas", "seguir convencoes",
        
        # Problemas a resolver
        "code smell", "codigo feio", "codigo repetido", "codigo confuso",
        "complexidade", "baixa performance", "lenta", "lento",
        
        # Erros comuns
        "refatora", "refatorrar", "refatorar", "melhora", "melhorarr",
        "otimizar", "otimisar", "otmizar", "simplificar", "simplificar",
        
        # Gírias
        "dar uma refatorada", "dar uma geral", "limpar a bagunça",
        "ajeitar o codigo", "organizar isso", "desembolar",
        "deixar mais bonito", "dar aquela melhorada",
        
        # Inglês
        "refactor code", "improve code", "clean code", "optimize",
        "code cleanup", "restructure", "reorganize", "enhance",
    ],
    
    # ==================== AJUDA E DOCUMENTAÇÃO ====================
    "help": [
        # Verbos principais
        "ajuda", "help", "ajudar", "ajude", "socorro",
        "duvida", "dúvida", "duvidas", "dúvidas",
        "info", "informacao", "informação", "informacoes",
        "documentacao", "documentação", "doc", "docs",
        
        # Sinônimos
        "tutorial", "guia", "manual", "instrucao", "instruções",
        "explicacao", "explicação", "orientacao", "orientação",
        "suporte", "atendimento", "assistencia",
        
        # Expressões comuns
        "como usar", "como funciona", "o que fazer",
        "me ajude", "me ajuda", "pode ajudar",
        "preciso de ajuda", "estou com duvida",
        "o que voce faz", "quais comandos", "comandos disponiveis",
        
        # Perguntas comuns
        "o que significa", "como fazer", "como criar",
        "qual comando", "que opcoes tenho", "como comecar",
        
        # Erros comuns
        "ajudar", "ajuda", "ajuida", "ajhuda",
        "duvida", "duvidda", "dúvida", "dúvida",
        "documentação", "documentasao", "docmentacao",
        
        # Gírias
        "me dá uma luz", "me orienta", "qual o passo a passo",
        "to perdido", "como que faz", "qual o esquema",
        "me explica", "como proceder",
        
        # Inglês
        "help me", "what can you do", "show commands",
        "how to", "usage guide", "documentation",
    ],
    
    # ==================== SAIR/FECHAR ====================
    "exit": [
        # Verbos principais
        "sair", "exit", "quit", "fechar", "close",
        "encerrar", "terminar", "finalizar", "parar",
        
        # Sinônimos
        "sair do programa", "sair do sistema", "fechar o programa",
        "fechar aplicacao", "encerrar sessao", "terminar execucao",
        
        # Expressões comuns
        "quero sair", "vou sair", "preciso sair",
        "pode fechar", "ate logo", "tchau", "bye",
        "sair agora", "fechar tudo", "encerrar agora",
        
        # Erros comuns
        "sair", "sairr", "sair", "fexar", "fechar",
        "encerrar", "enserar", "terminar", "terminar",
        
        # Gírias
        "cair fora", "vazar", "dar o fora", "meter o pé",
        "encerrar o expediente", "fim do expediente",
        
        # Inglês
        "quit application", "close program", "exit system",
        "terminate", "stop running",
    ],
    
    # ==================== TESTES ====================
    "create_test": [
        # Verbos principais
        "teste", "test", "testar", "teste", "testes",
        "criar teste", "crie teste", "criar testes", "crie testes",
        "fazer teste", "faça teste", "gerar teste", "gere teste",
        
        # Tipos de teste
        "teste unitario", "teste unidade", "unit test", "unitario",
        "teste integracao", "integration test", "integracao",
        "teste funcional", "functional test", "teste e2e",
        "teste aceitacao", "teste caixa branca", "teste caixa preta",
        
        # Sinônimos
        "spec", "specs", "especificacao", "especificações",
        "assertiva", "assert", "verificacao", "validacao",
        
        # Expressões
        "cobrir com teste", "adicionar teste", "implementar teste",
        "testar componente", "validar funcionalidade",
        
        # Frameworks
        "pytest", "unittest", "nose", "doctest",
        
        # Erros comuns
        "teste", "testi", "testar", "testarr",
        "teste", "test", "testes",
        
        # Inglês
        "create tests", "add tests", "write tests",
        "test coverage", "test suite",
    ],
    
    # ==================== DEPLOY/PUBLICAR ====================
    "deploy": [
        # Verbos principais
        "deploy", "publicar", "implantar", "subir", "colocar no ar",
        "deployar", "publicar app", "subir aplicacao",
        
        # Sinônimos
        "publicacao", "implantacao", "release", "lancamento",
        "subir producao", "ir para producao", "go live",
        
        # Ambientes
        "producao", "production", "prod", "homologacao", "staging",
        "desenvolvimento", "dev", "testes",
        
        # Serviços
        "heroku", "vercel", "netlify", "aws", "azure", "gcp",
        "fly io", "railway", "render",
        
        # Expressões
        "fazer deploy", "realizar deploy", "executar deploy",
        "subir servidor", "hospedar", "publicar online",
        
        # Inglês
        "deploy app", "publish app", "host app", "go to production",
    ],
    
    # ==================== DEPENDÊNCIAS ====================
    "dependencies": [
        # Verbos principais
        "dependencia", "dependencias", "package", "pacote",
        "instalar", "instale", "adicionar dependencia",
        "remover dependencia", "atualizar dependencia",
        
        # Gerenciadores
        "pip", "poetry", "pipenv", "conda", "requirements",
        "requirements.txt", "pyproject.toml", "setup.py",
        
        # Ações
        "instalar pacote", "baixar biblioteca", "adicionar lib",
        "importar modulo", "usar biblioteca",
        
        # Problemas
        "conflito dependencia", "versao errada", "pacote nao encontrado",
        
        # Expressões
        "quais dependencias", "listar dependencias", "mostrar dependencias",
        
        # Inglês
        "install package", "add dependency", "update packages",
        "pip install", "requirements file",
    ],
    
    # ==================== DEBUG ====================
    "debug": [
        # Verbos principais
        "debug", "debugar", "depurar", "debugar",
        "corrigir", "consertar", "arrumar", "resolver",
        
        # Problemas
        "bug", "erro", "excecao", "exception", "problem", "problema",
        "falha", "crash", "travamento", "lentidao", "comportamento estranho",
        
        # Ferramentas
        "breakpoint", "print", "log", "logging", "traceback",
        "stack trace", "debugger",
        
        # Expressões
        "encontrar erro", "achar bug", "identificar problema",
        "por que nao funciona", "o que esta errado",
        "analisar erro", "investigar problema",
        
        # Inglês
        "fix bug", "debug code", "solve issue", "troubleshoot",
    ],
    
    # ==================== PERFORMANCE ====================
    "performance": [
        # Verbos principais
        "performance", "perfomance", "desempenho", "performance",
        "otimizar performance", "melhorar performance",
        "acelerar", "deixar mais rapido", "reduzir tempo",
        
        # Métricas
        "lento", "lenta", "demorado", "rapido", "veloz",
        "tempo resposta", "latencia", "consumo memoria",
        "uso cpu", "uso ram", "alocacao memoria",
        
        # Ações
        "profiling", "profile", "benchmark", "medir tempo",
        "otimizar consulta", "cache", "lazy loading",
        
        # Inglês
        "improve speed", "optimize performance", "make faster",
        "performance issue", "bottleneck",
    ],
}