# flai/core/agents/help_agent.py
"""
Help Agent - Diagnostica e entende a real necessidade do usuário
"""

from pathlib import Path
from typing import Dict, List, Optional
import re

from flai.core.agents.agent_manager import BaseAgent, AgentPriority
from flai.core.context.context_manager import ContextManager
from flai.core.logging import get_logger

logger = get_logger(__name__)


class HelpAgent(BaseAgent):
    """
    Agente de ajuda inteligente.
    
    Não exibe texto fixo. Seu objetivo é diagnosticar o que o usuário
    realmente está tentando fazer e oferecer orientação específica.
    """

    def __init__(
        self,
        project_path: Path,
        config: Dict = None
    ):
        super().__init__(project_path, config)
        self.context_manager = ContextManager(project_path)
        
        # Padrões para diagnosticar o tipo de ajuda
        self.patterns = {
            "task_support": [
                (r"ajuda com ([\w\s]+)", "task"),
                (r"preciso (?:de )?ajuda (?:com|para) ([\w\s]+)", "task"),
                (r"como (?:fazer|criar|implementar) ([\w\s]+)", "task"),
                (r"(?:me )?ajude (?:a|com) ([\w\s]+)", "task"),
            ],
            "command_discovery": [
                (r"comando (?:para|de) ([\w\s]+)", "command"),
                (r"qual (?:o )?comando (?:para|de) ([\w\s]+)", "command"),
                (r"como (?:se )?(?:faz|cria) ([\w\s]+)", "command"),
            ],
            "concept_explanation": [
                (r"o que (?:é|e) ([\w\s]+)", "concept"),
                (r"explique ([\w\s]+)", "concept"),
                (r"o que significa ([\w\s]+)", "concept"),
            ],
            "problem_solving": [
                (r"erro (?:ao|de|no) ([\w\s]+)", "problem"),
                (r"não (?:est[aá]|funciona) ([\w\s]+)", "problem"),
                (r"problema (?:com|no) ([\w\s]+)", "problem"),
            ],
            "ambiguous": [
                (r"^(\w+)$", "single_word"),
                (r"^(\w+ \w+)$", "two_words"),
            ]
        }

    def can_handle(
        self,
        intent: str,
        context: Dict = None
    ) -> bool:
        return intent == "help"

    async def execute(
        self,
        intent: str,
        entity: str = None,
        fields: List[str] = None,
        context: Dict = None
    ) -> Dict:
        """
        Executa diagnóstico de ajuda.
        
        Args:
            intent: Intenção (deve ser "help")
            entity: Entidade extraída
            fields: Campos extras
            context: Contexto com user_query original
        
        Returns:
            Resposta personalizada com diagnóstico
        """
        user_query = ""
        
        if context:
            user_query = context.get("user_query", "")
        
        # Caso 1: Apenas "ajuda" ou vazio
        if not user_query or user_query.lower().strip() in ["ajuda", "help", "?"]:
            return self._show_capabilities()
        
        # Caso 2: Diagnostica o tipo de ajuda necessária
        help_type, extracted = self._diagnose(user_query)
        
        if help_type == "task_support":
            return self._handle_task_support(extracted, user_query)
        elif help_type == "command_discovery":
            return self._handle_command_discovery(extracted, user_query)
        elif help_type == "concept_explanation":
            return self._handle_concept_explanation(extracted, user_query)
        elif help_type == "problem_solving":
            return self._handle_problem_solving(extracted, user_query)
        elif help_type == "ambiguous":
            return self._handle_ambiguous(extracted, user_query)
        else:
            return self._handle_general_help(user_query)

    def _diagnose(self, query: str) -> tuple[str, Optional[str]]:
        """
        Diagnostica o tipo de ajuda necessária.
        
        Returns:
            (tipo_ajuda, entidade_extraida)
        """
        query_lower = query.lower().strip()
        
        for help_type, patterns in self.patterns.items():
            for pattern, _ in patterns:
                match = re.search(pattern, query_lower, re.IGNORECASE)
                if match:
                    extracted = match.group(1) if match.groups() else None
                    return help_type, extracted
        
        return "general", None

    def _show_capabilities(self) -> Dict:
        """
        Mostra capacidades do FLAI com base no contexto do projeto.
        """
        # Analisa o projeto para personalizar resposta
        project_info = self._analyze_project()
        
        response = f"""🤖 **Como posso ajudar?**

{self._get_project_context_summary(project_info)}

**Principais coisas que posso fazer:**

| O que você quer | Como pedir |
|----------------|------------|
| Criar CRUD | `criar crud de produtos` |
| Criar formulário | `criar formulário de contato` |
| Analisar código | `analise o controller usuario` |
| Buscar no projeto | `onde está a autenticação?` |
| Explicar um conceito | `explique o que é MVC` |
| Resolver um erro | `erro ao executar migrate` |

💡 **Descreva o que você precisa fazer** - quanto mais detalhes, melhor poderei ajudar.
"""
        
        return {
            "success": True,
            "type": "help",
            "content": response.strip(),
            "needs_refinement": False
        }

    def _handle_task_support(self, task: str, original_query: str) -> Dict:
        """
        Lida com pedidos de ajuda para tarefas específicas.
        """
        task_lower = task.lower() if task else ""
        
        # Mapeia tarefas comuns
        if "autentic" in task_lower or "login" in task_lower:
            response = """🔐 **Ajuda com autenticação**

Posso ajudar você a:
- Criar estrutura de login/registro
- Implementar JWT ou sessão
- Integrar autenticação com Flet
- Revisar código existente

**Comece com:** `criar sistema de autenticação`

Quer que eu crie a estrutura básica para você?"""
        
        elif "crud" in task_lower:
            response = """📝 **Ajuda com CRUD**

Posso criar um CRUD completo para você:

**Exemplo:** `criar crud de produtos com nome, preco, estoque`

**Qual entidade você quer criar?** (ex: usuario, produto, cliente)"""
        
        elif "form" in task_lower or "formulário" in task_lower:
            response = """📋 **Ajuda com formulários**

Posso criar formulários com campos personalizados:

**Exemplo:** `criar formulário de contato com nome, email, mensagem`

**Que formulário você precisa?**"""
        
        elif "test" in task_lower or "teste" in task_lower:
            response = """🧪 **Ajuda com testes**

Posso criar testes unitários e de integração:

**Exemplo:** `criar testes para o crud de produtos`

**Para qual componente você quer testes?**"""
        
        else:
            response = f"""🎯 **Sobre: {task}**

Para te ajudar melhor, me diga:

1. Você quer **CRIAR** algo novo?
2. Quer **ANALISAR/MODIFICAR** algo existente?
3. Ou precisa de **EXPLICAÇÃO** sobre o conceito?

**Comandos úteis:**
- `criar {task}` - se quer criar
- `analise o {task}` - se quer analisar
- `onde está {task}` - se quer encontrar

Descreva com mais detalhes o que precisa fazer."""
        
        return {
            "success": True,
            "type": "help",
            "content": response,
            "needs_refinement": True,
            "task": task
        }

    def _handle_command_discovery(self, command: str, original_query: str) -> Dict:
        """
        Lida com pedidos de descoberta de comandos.
        """
        response = f"""🔍 **Comando para: {command}**

**Sugestões:**

| O que você quer fazer | Comando |
|---------------------|---------|
| Criar algo | `criar {command}` |
| Analisar algo | `analise o {command}` |
| Buscar algo | `onde está {command}` |
| Modificar algo | `refatorar o {command}` |

**Exemplo:** `criar {command} com campos personalizados`

Isso ajuda? Se não, descreva melhor o que deseja fazer."""
        
        return {
            "success": True,
            "type": "help",
            "content": response,
            "needs_refinement": True
        }

    def _handle_concept_explanation(self, concept: str, original_query: str) -> Dict:
        """
        Lida com pedidos de explicação de conceitos.
        """
        concept_lower = concept.lower() if concept else ""
        
        # Conceitos comuns do Flet/FLAI
        explanations = {
            "mvc": "MVC (Model-View-Controller) separa: Model (dados), View (interface), Controller (lógica). Seu projeto usa essa arquitetura.",
            "crud": "CRUD = Create, Read, Update, Delete. São as 4 operações básicas para manipular dados.",
            "flet": "Flet é um framework para criar interfaces com Python. Ele usa Flutter por baixo.",
            "rag": "RAG (Retrieval Augmented Generation) - busca informações no código antes de responder.",
        }
        
        if concept_lower in explanations:
            response = f"""📚 **O que é {concept}?**

{explanations[concept_lower]}

**Quer que eu te ajude a usar {concept} no seu projeto?**"""
        else:
            response = f"""📚 **Sobre: {concept}**

Posso te ajudar a entender melhor este conceito.

**Você gostaria que eu:**
- Explique o conceito em detalhes?
- Mostre exemplos práticos?
- Ajude a implementar no seu projeto?

Me diga como posso ajudar."""
        
        return {
            "success": True,
            "type": "help",
            "content": response,
            "needs_refinement": True
        }

    def _handle_problem_solving(self, problem: str, original_query: str) -> Dict:
        """
        Lida com pedidos de resolução de problemas/erros.
        """
        response = f"""⚠️ **Problema identificado: {problem}**

Para te ajudar a resolver:

1. **Qual o erro exato?** (mensagem completa)
2. **Quando acontece?** (ao rodar, ao criar, etc)
3. **O que você tentou?**

**Posso:**
- Analisar o código relacionado
- Sugerir soluções comuns
- Criar uma versão corrigida

Cole o erro ou descreva o problema com mais detalhes."""
        
        return {
            "success": True,
            "type": "help",
            "content": response,
            "needs_refinement": True
        }

    def _handle_ambiguous(self, term: str, original_query: str) -> Dict:
        """
        Lida com consultas ambíguas (ex: "controller usuario").
        """
        # Tenta encontrar correspondências no projeto
        matches = self._find_in_project(term)
        
        response = f"""❓ **O que você quer fazer com "{term}"?**

**Não entendi se você quer:**

1. ✨ **CRIAR** - `criar {term}`
2. 🔍 **ANALISAR** - `analise o {term}`
3. 🔎 **BUSCAR** - `onde está {term}`
4. 📝 **MODIFICAR** - `refatorar o {term}`

{f'**Encontrei no seu projeto:** {", ".join(matches[:3])}' if matches else ''}

**Seja mais específico sobre o que deseja fazer.** 🎯"""
        
        return {
            "success": True,
            "type": "help",
            "content": response,
            "needs_refinement": True,
            "ambiguous_term": term
        }

    def _handle_general_help(self, query: str) -> Dict:
        """
        Lida com perguntas de ajuda gerais.
        """
        response = f"""🤔 **Sobre sua pergunta:** "{query[:50]}..."

**Para eu te ajudar melhor, tente:**

1. **Usar verbos de ação:** criar, analisar, buscar
2. **Mencionar o componente:** controller, model, page
3. **Ser mais específico** sobre o que precisa

**Exemplos:**
- `criar crud de produtos`
- `analise o controller usuario`
- `onde está a autenticação?`

**Qual desses se parece com o que você precisa?** 💡"""
        
        return {
            "success": True,
            "type": "help",
            "content": response,
            "needs_refinement": True
        }

    def _analyze_project(self) -> Dict:
        """Analisa o projeto para resposta personalizada."""
        info = {
            "name": self.project_path.name,
            "has_flet": False,
            "models": 0,
            "controllers": 0,
            "pages": 0
        }
        
        try:
            # Verifica dependências
            req_file = self.project_path / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text()
                info["has_flet"] = "flet" in content.lower()
            
            # Conta componentes
            info["models"] = len(list(self.project_path.glob("models/*.py")))
            info["controllers"] = len(list(self.project_path.glob("controllers/*.py")))
            info["pages"] = len(list(self.project_path.glob("pages/*.py")))
            
        except Exception as e:
            logger.warning(f"Erro ao analisar projeto: {e}")
        
        return info

    def _get_project_context_summary(self, info: Dict) -> str:
        """Gera resumo do contexto do projeto."""
        lines = []
        
        if info["has_flet"]:
            lines.append(f"📁 **Projeto:** {info['name']} (Flet detectado)")
        
        if info["models"] > 0 or info["controllers"] > 0 or info["pages"] > 0:
            lines.append("\n**Componentes encontrados:**")
            if info["models"] > 0:
                lines.append(f"   • {info['models']} modelos")
            if info["controllers"] > 0:
                lines.append(f"   • {info['controllers']} controllers")
            if info["pages"] > 0:
                lines.append(f"   • {info['pages']} páginas")
        
        if not lines:
            lines.append(f"📁 **Projeto:** {info['name']} (sem componentes detectados)")
            lines.append("\n💡 **Comece criando algo:** `criar crud de produtos`")
        
        return "\n".join(lines)

    def _find_in_project(self, term: str) -> List[str]:
        """Busca termos similares no projeto."""
        matches = []
        
        for pattern in [f"**/{term}.py", f"**/*{term}*.py"]:
            for file in self.project_path.glob(pattern):
                if "__pycache__" not in str(file):
                    matches.append(file.stem)
        
        return matches[:5]

    def get_priority(self) -> AgentPriority:
        return AgentPriority.NORMAL