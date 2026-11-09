# fleting/flai/utils/agents.py
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain import hub
from langchain_community.llms import Ollama
from pathlib import Path

class FlaiAgents:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.llm = Ollama(model="phi3:mini")
        self.agent = None
        
    def setup_tools(self):
        """Configura ferramentas especializadas"""
        
        from .scanner import scan_project
        from .rag import ProjectRAG
        
        # Tool 1: Scanner de projeto
        def scan_project_tool(query: str) -> str:
            """Analisa estrutura do projeto. Input: 'analisar estrutura' ou 'listar arquivos'"""
            files = scan_project(self.project_root)
            return f"Projeto tem {len(files)} arquivos. Use 'detalhes arquivo <nome>' para mais informações."
        
        # Tool 2: RAG Query
        rag_system = ProjectRAG(self.project_root)
        
        def query_project_tool(query: str) -> str:
            """Pesquisa informações no projeto. Input: sua pergunta sobre o código"""
            result = rag_system.query(query)
            return result["result"]
        
        # Tool 3: Checklist
        from .checklist import create_checklist
        
        def checklist_tool(query: str) -> str:
            """Gera ou atualiza checklist. Input: 'criar checklist' ou 'verificar progresso'"""
            checklist_file = create_checklist(self.project_root)
            return f"Checklist criado/atualizado em: {checklist_file}"
        
        # Tool 4: Analisador de código
        def code_analyzer_tool(query: str) -> str:
            """Analisa padrões de código. Input: 'analisar padrões python' ou 'verificar boas práticas'"""
            # Implementar análise com AST
            return "Análise de código em desenvolvimento."
        
        tools = [
            Tool(
                name="ScannerProjeto",
                func=scan_project_tool,
                description="Analisa estrutura de arquivos do projeto"
            ),
            Tool(
                name="PesquisaProjeto",
                func=query_project_tool,
                description="Pesquisa informações específicas nos arquivos do projeto"
            ),
            Tool(
                name="Checklist",
                func=checklist_tool,
                description="Gerencia checklist de melhorias do projeto"
            ),
            Tool(
                name="AnalisadorCodigo",
                func=code_analyzer_tool,
                description="Analisa padrões e boas práticas de código"
            )
        ]
        
        return tools
    
    def create_agent(self):
        """Cria agente LangChain com tools"""
        tools = self.setup_tools()
        
        # Pull prompt do ReAct
        prompt = hub.pull("hwchase17/react")
        
        # Criar agente
        agent = create_react_agent(self.llm, tools, prompt)
        self.agent = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )
        
        return self.agent
    
    def run(self, input_text: str) -> str:
        """Executa agente com input do usuário"""
        if not self.agent:
            self.create_agent()
        
        return self.agent.invoke({"input": input_text})