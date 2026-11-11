"""
Intent Patterns - Definição de padrões regex para reconhecimento de intenções
"""
import re
from typing import Dict, List, Tuple, Optional

class IntentPatterns:
    """Padrões para reconhecimento de intenções do usuário"""
    
    # Padrões organizados por intenção (EXPANDIDO)
    PATTERNS: Dict[str, List[str]] = {
        # ========== CRIAÇÃO DE CRUD (EXPANDIDO) ==========
        "create_crud": [
            # Português
            r"cri(?:a|e)r?\s+crud\s+(?:de\s+)?(\w+)",
            r"crie\s+crud\s+(?:de\s+)?(\w+)",
            r"crio\s+crud\s+(?:de\s+)?(\w+)",
            r"criamos\s+crud\s+(?:de\s+)?(\w+)",
            r"f(?:a|aze)r?\s+crud\s+(?:de\s+)?(\w+)",
            r"faça\s+crud\s+(?:de\s+)?(\w+)",
            r"faz\s+crud\s+(?:de\s+)?(\w+)",
            r"ger(?:a|e)r?\s+crud\s+(?:de\s+)?(\w+)",
            r"gere\s+crud\s+(?:de\s+)?(\w+)",
            r"constru(?:i|ir)\s+crud\s+(?:de\s+)?(\w+)",
            r"mont(?:a|ar)\s+crud\s+(?:de\s+)?(\w+)",
            r"desenvolv(?:er|a)\s+crud\s+(?:de\s+)?(\w+)",
            r"novo\s+crud\s+(?:de\s+)?(\w+)",
            r"nova\s+crud\s+(?:de\s+)?(\w+)",
            # Sinônimos sem a palavra CRUD
            r"cri(?:a|e)r?\s+tabela\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+entidade\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+modelo\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+recurso\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+cadastro\s+(?:de\s+)?(\w+)",
            # Inglês
            r"make\s+crud\s+(?:for\s+)?(\w+)",
            r"create\s+crud\s+(?:for\s+)?(\w+)",
            r"generate\s+crud\s+(?:for\s+)?(\w+)",
            r"build\s+crud\s+(?:for\s+)?(\w+)",
            r"new\s+crud\s+(?:for\s+)?(\w+)",
            r"create\s+table\s+(?:for\s+)?(\w+)",
            r"create\s+entity\s+(?:for\s+)?(\w+)",
            r"create\s+model\s+(?:for\s+)?(\w+)",
        ],
        
        # ========== CRIAÇÃO DE FORMULÁRIO (EXPANDIDO) ==========
        "create_form": [
            # Português
            r"cri(?:a|e)r?\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"crie\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"crio\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"f(?:a|aze)r?\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"faça\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"ger(?:a|e)r?\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"gere\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"novo\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            r"nova\s+form(?:ul[áa]rio)?\s+(?:de\s+)?(\w+)",
            # Variações com "formulário"
            r"cri(?:a|e)r?\s+ficha\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+cadastro\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+registro\s+(?:de\s+)?(\w+)",
            # Inglês
            r"create\s+form\s+(?:for\s+)?(\w+)",
            r"make\s+form\s+(?:for\s+)?(\w+)",
            r"generate\s+form\s+(?:for\s+)?(\w+)",
            r"new\s+form\s+(?:for\s+)?(\w+)",
            r"create\s+formulary\s+(?:for\s+)?(\w+)",
        ],
        
        # ========== CRIAÇÃO DE PÁGINA (EXPANDIDO) ==========
        "create_page": [
            # Português
            r"cri(?:a|e)r?\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            r"crie\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            r"crio\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            r"f(?:a|aze)r?\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            r"faça\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            r"ger(?:a|e)r?\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            r"nova\s+p[aá]gina\s+(?:de\s+)?(\w+)",
            # Sinônimos
            r"cri(?:a|e)r?\s+tela\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+view\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+rota\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+dashboard\s+(?:de\s+)?(\w+)",
            # Inglês
            r"create\s+page\s+(?:for\s+)?(\w+)",
            r"make\s+page\s+(?:for\s+)?(\w+)",
            r"new\s+page\s+(?:for\s+)?(\w+)",
            r"create\s+screen\s+(?:for\s+)?(\w+)",
            r"create\s+view\s+(?:for\s+)?(\w+)",
            r"create\s+route\s+(?:for\s+)?(\w+)",
        ],
        
        # ========== CRIAÇÃO DE MODEL (EXPANDIDO) ==========
        "create_model": [
            # Português
            r"cri(?:a|e)r?\s+model(?:o)?\s+(?:de\s+)?(\w+)",
            r"crie\s+model(?:o)?\s+(?:de\s+)?(\w+)",
            r"crio\s+model(?:o)?\s+(?:de\s+)?(\w+)",
            r"f(?:a|aze)r?\s+model(?:o)?\s+(?:de\s+)?(\w+)",
            r"ger(?:a|e)r?\s+model(?:o)?\s+(?:de\s+)?(\w+)",
            r"novo\s+model(?:o)?\s+(?:de\s+)?(\w+)",
            r"nova\s+entidade\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+tabela\s+(?:de\s+)?(\w+)",
            r"cri(?:a|e)r?\s+schema\s+(?:de\s+)?(\w+)",
            # Inglês
            r"create\s+model\s+(?:for\s+)?(\w+)",
            r"make\s+model\s+(?:for\s+)?(\w+)",
            r"new\s+model\s+(?:for\s+)?(\w+)",
            r"create\s+entity\s+(?:for\s+)?(\w+)",
            r"create\s+table\s+(?:for\s+)?(\w+)",
        ],
        
        # ========== CRIAÇÃO DE TESTES (NOVO) ==========
        "create_test": [
            # Português
            r"cri(?:a|e)r?\s+teste(?:s)?\s+(?:de|para|do)\s+(\w+)",
            r"crie\s+teste(?:s)?\s+(?:de|para|do)\s+(\w+)",
            r"f(?:a|aze)r?\s+teste(?:s)?\s+(?:de|para|do)\s+(\w+)",
            r"faça\s+teste(?:s)?\s+(?:de|para|do)\s+(\w+)",
            r"ger(?:a|e)r?\s+teste(?:s)?\s+(?:de|para|do)\s+(\w+)",
            r"adicionar\s+teste(?:s)?\s+(?:de|para|do)\s+(\w+)",
            r"testar\s+(?:o\s+)?(controller|model|page|view)\s+(\w+)",
            r"teste\s+unit[áa]rio\s+(?:do|da|de)\s+(\w+)",
            # Inglês
            r"create\s+test(?:s)?\s+(?:for\s+)?(\w+)",
            r"make\s+test(?:s)?\s+(?:for\s+)?(\w+)",
            r"add\s+test(?:s)?\s+(?:for\s+)?(\w+)",
            r"write\s+test(?:s)?\s+(?:for\s+)?(\w+)",
            r"test\s+(?:the\s+)?(controller|model|page|view)\s+(\w+)",
            r"unit\s+test\s+(?:for\s+)?(\w+)",
        ],
        
        # ========== DEPLOY/PUBLICAR (NOVO) ==========
        "deploy": [
            # Português
            r"f(?:a|aze)r\s+deploy\s+(?:do|da|de)\s+(\w*)",
            r"faça\s+deploy\s+(?:do|da|de)\s+(\w*)",
            r"public(?:a|ar)\s+(?:a\s+)?aplica[cç][aã]o\s+(\w*)",
            r"subir\s+(?:a\s+)?aplica[cç][aã]o\s+(?:para\s+)?(\w+)",
            r"implant(?:a|ar)\s+(?:a\s+)?aplica[cç][aã]o\s+(\w*)",
            r"colocar\s+no\s+ar\s+(?:a\s+)?aplica[cç][aã]o\s+(\w*)",
            r"(?:ir\s+para|subir\s+para)\s+produ[cç][aã]o\s+(\w*)",
            # Inglês
            r"deploy\s+(?:the\s+)?app(?:lication)?\s+(\w*)",
            r"publish\s+(?:the\s+)?app(?:lication)?\s+(\w*)",
            r"go\s+live\s+(?:with\s+)?(\w*)",
            r"release\s+(?:the\s+)?app(?:lication)?\s+(\w*)",
            r"push\s+(?:to\s+)?production\s+(\w*)",
        ],
        
        # ========== DEPENDÊNCIAS (NOVO) ==========
        "dependencies": [
            # Português
            r"instal(?:a|ar)\s+(?:a\s+)?biblioteca\s+(\w+)",
            r"instal(?:a|ar)\s+(?:o\s+)?pacote\s+(\w+)",
            r"adicionar\s+depend[eê]ncia\s+(\w+)",
            r"adicionar\s+biblioteca\s+(\w+)",
            r"remover\s+depend[eê]ncia\s+(\w+)",
            r"atualizar\s+depend[eê]ncia\s+(\w+)",
            r"pip\s+install\s+(\w+)",
            r"poetry\s+add\s+(\w+)",
            r"listar\s+depend[eê]ncias",
            r"mostrar\s+depend[eê]ncias",
            # Inglês
            r"install\s+package\s+(\w+)",
            r"add\s+dependency\s+(\w+)",
            r"remove\s+dependency\s+(\w+)",
            r"update\s+dependency\s+(\w+)",
            r"list\s+dependencies",
            r"show\s+dependencies",
        ],
        
        # ========== DEBUG (NOVO) ==========
        "debug": [
            # Português
            r"debugar\s+(?:o\s+)?(?:c[oó]digo|erro|bug)\s+(\w*)",
            r"depurar\s+(?:o\s+)?(?:c[oó]digo|erro|bug)\s+(\w*)",
            r"corrigir\s+(?:o\s+)?(?:bug|erro)\s+(\w*)",
            r"arrumar\s+(?:o\s+)?(?:bug|erro)\s+(\w*)",
            r"resolver\s+(?:o\s+)?(?:problema|bug|erro)\s+(\w*)",
            r"encontrar\s+(?:o\s+)?(?:bug|erro)\s+(\w*)",
            r"analisar\s+(?:o\s+)?(?:bug|erro)\s+(\w*)",
            r"por\s+que\s+n[aã]o\s+funciona\s+(\w*)",
            # Inglês
            r"debug\s+(?:the\s+)?(?:code|error|bug)\s+(\w*)",
            r"fix\s+(?:the\s+)?(?:bug|error)\s+(\w*)",
            r"resolve\s+(?:the\s+)?(?:issue|bug|error)\s+(\w*)",
            r"troubleshoot\s+(?:the\s+)?(?:code|issue)\s+(\w*)",
        ],
        
        # ========== PERFORMANCE (NOVO) ==========
        "performance": [
            # Português
            r"otimizar\s+(?:a\s+)?performance\s+(?:do|da|de)\s+(\w*)",
            r"melhorar\s+(?:a\s+)?performance\s+(?:do|da|de)\s+(\w*)",
            r"acelerar\s+(?:o\s+)?(?:c[oó]digo|app|aplica[cç][aã]o)\s+(\w*)",
            r"deixar\s+mais\s+r[aá]pido\s+(?:o\s+)?(?:c[oó]digo|app)\s+(\w*)",
            r"reduzir\s+(?:o\s+)?tempo\s+de\s+resposta\s+(\w*)",
            r"(?:est[aá]\s+)?lento",
            r"(?:est[aá]\s+)?demorado",
            # Inglês
            r"optimize\s+(?:the\s+)?performance\s+(?:of\s+)?(\w*)",
            r"improve\s+(?:the\s+)?performance\s+(?:of\s+)?(\w*)",
            r"make\s+faster\s+(?:the\s+)?(?:code|app)\s+(\w*)",
            r"performance\s+issue\s+(\w*)",
            r"bottleneck\s+(\w*)",
        ],
        
        # ========== ANÁLISE (EXPANDIDO) ==========
        "analyze": [
            r"analis(?:a|e)\s+(?:o\s+)?(controller|model|page|view|service|util|helper|componente|modulo|fun[cç][aã]o|classe)\s+(\w+)",
            r"analise\s+(?:o\s+)?(controller|model|page|view|service|util|helper|componente|modulo|fun[cç][aã]o|classe)\s+(\w+)",
            r"analyze\s+(?:the\s+)?(controller|model|page|view|service|util|helper|component|module|function|class)\s+(\w+)",
            r"mostre\s+(?:o\s+)?(controller|model|page|view|service|util|helper|componente|modulo|fun[cç][aã]o|classe)\s+(\w+)",
            r"show\s+(?:the\s+)?(controller|model|page|view|service|util|helper|component|module|function|class)\s+(\w+)",
            r"exibir\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"ver\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"visualizar\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"checar\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"verificar\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
        ],
        
        # ========== WHERE/BUSCA (MANTIDO) ==========
        "where": [
            r"onde\s+est[aá]\s+(.+)\??",
            r"cad(?:a|o)\s+(.+)",
            r"onde\s+f(?:i|ic)a\s+(.+)\??",
            r"where\s+is\s+(.+)\??",
            r"find\s+(.+)",
            r"buscar\s+(.+)",
            r"procurar\s+(.+)",
            r"localizar\s+(.+)",
            r"qual\s+o\s+caminho\s+(?:do|da|de)\s+(.+)",
            r"em\s+qual\s+arquivo\s+(?:est[aá]|fica)\s+(.+)",
        ],
        
        # ========== REFACTOR (EXPANDIDO) ==========
        "refactor": [
            r"refator(?:a|e)\s+(?:o\s+)?(controller|model|page|view|service|util|helper|componente|modulo|fun[cç][aã]o|classe)\s+(\w+)",
            r"refactor\s+(?:the\s+)?(controller|model|page|view|service|util|helper|component|module|function|class)\s+(\w+)",
            r"melhor(?:a|e)\s+(?:o\s+)?(controller|model|page|view|service|util|helper|componente|modulo|fun[cç][aã]o|classe)\s+(\w+)",
            r"improve\s+(?:the\s+)?(controller|model|page|view|service|util|helper|component|module|function|class)\s+(\w+)",
            r"otimizar\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"reestruturar\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"reorganizar\s+(?:o\s+)?(controller|model|page|view|service)\s+(\w+)",
            r"simplificar\s+(?:o\s+)?(controller|model|page|view|service|fun[cç][aã]o)\s+(\w+)",
            r"clean\s+code\s+(?:no\s+)?(controller|model|page|view|service)\s+(\w+)",
        ],
        
        # ========== AJUDA (MANTIDO) ==========
        # Comandos de controle: só a frase INTEIRA (^...$). Sem âncora, r"q" casava
        # com "verifique" e r"\?" com qualquer pergunta — que deve ir para o LLM.
        "help": [
            r"^(?:ajuda|help|\?|comandos|commands)$",
            r"^o que (?:você|voce|vc) (?:faz|sabe fazer)\??$",
            r"^(?:me\s+ajuda|preciso\s+de\s+ajuda)$",
            r"^(?:quais|mostrar|show)\s+(?:comandos|commands)\??$",
        ],

        # ========== SAIR ==========
        "exit": [
            r"^(?:sair|exit|quit|q|fechar|close|encerrar|terminar|tchau|bye)$",
            r"^sair do programa$",
            r"^at[eé]\s+logo$",
        ],
    }
    
    # Padrões para extração de campos (EXPANDIDO)
    FIELD_PATTERNS: List[str] = [
        r"com\s+os\s+campos?\s*:\s*(.+)",
        r"com\s+os\s+seguintes\s+campos?\s*:\s*(.+)",
        r"com\s+os\s+atributos?\s*:\s*(.+)",
        r"com\s+as\s+propriedades?\s*:\s*(.+)",
        r"campos?\s*:\s*(.+)",
        r"atributos?\s*:\s*(.+)",
        r"fields?\s*:\s*(.+)",
        r"com\s+(.+)",
        r"contendo\s+(.+)",
        r"possuindo\s+(.+)",
        r"tendo\s+os\s+campos?\s+(.+)",
    ]
    
    @classmethod
    def match_intent(cls, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retorna (intent, entity) baseado no texto
        
        Example:
            match_intent("criar crud de produtos") -> ("create_crud", "produtos")
            match_intent("fazer deploy da aplicacao") -> ("deploy", "aplicacao")
        """
        text_lower = text.lower().strip()
        
        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    # O último grupo é a entidade
                    entity = match.group(1) if match.groups() else None
                    # Para analyze e refactor, o primeiro grupo é tipo, segundo é nome
                    if intent in ["analyze", "refactor"] and match.groups() and len(match.groups()) >= 2:
                        entity = f"{match.group(1)} {match.group(2)}"
                    return intent, entity
        
        return None, None
    
    @classmethod
    def extract_fields(cls, text: str) -> List[str]:
        """Extrai lista de campos da descrição"""
        text_lower = text.lower()
        
        for pattern in cls.FIELD_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                fields_str = match.group(1)
                # Separa por vírgula, "e", "e também", ponto e vírgula
                separators = r'[ ,;]+\s*[e&]\s+|[ ,;]+|\s+e\s+|\s+[e&]\s+'
                fields = re.split(separators, fields_str)
                fields = [f.strip() for f in fields if f.strip() and len(f.strip()) > 0]
                # Remove palavras comuns que podem ter sido capturadas
                stop_words = {"com", "de", "os", "as", "do", "da", "dos", "das", "e", "tambem", "sendo"}
                fields = [f for f in fields if f not in stop_words and len(f) > 1]
                return fields[:10]  # Limita a 10 campos
        
        return []
    
    @classmethod
    def get_all_intents(cls) -> List[str]:
        """Retorna todas as intenções disponíveis"""
        return list(cls.PATTERNS.keys())
    
    @classmethod
    def add_pattern(cls, intent: str, pattern: str) -> None:
        """Adiciona um novo padrão para uma intenção"""
        if intent not in cls.PATTERNS:
            cls.PATTERNS[intent] = []
        cls.PATTERNS[intent].append(pattern)
    
    @classmethod
    def get_intent_patterns_count(cls) -> Dict[str, int]:
        """Retorna número de padrões por intenção (útil para debug)"""
        return {intent: len(patterns) for intent, patterns in cls.PATTERNS.items()}