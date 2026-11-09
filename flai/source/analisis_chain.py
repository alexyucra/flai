# fleting/flai/utils/analysis_chains.py
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from typing import List, Dict

class AnalysisChains:
    def __init__(self, model_name: str = "phi3:mini"):
        self.llm = Ollama(model=model_name)
        
    def create_mvc_analysis_chain(self):
        """Chain para análise MVC"""
        template = """
        Você é um arquiteto especialista em MVC com Python/Flet.
        
        Estrutura do projeto:
        {project_structure}
        
        Analise esta estrutura MVC e forneça:
        1. Pontos fortes
        2. Problemas identificados
        3. Sugestões de melhoria
        4. Padrões faltantes
        
        Foque em:
        - Separação de responsabilidades
        - Acoplamento/coesão
        - Reutilização de código
        - Boas práticas Python
        
        Resposta estruturada e objetiva:
        """
        
        prompt = PromptTemplate(
            input_variables=["project_structure"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def create_code_review_chain(self):
        """Chain para code review"""
        template = """
        Faça um code review do seguinte trecho:
        
        Arquivo: {file_path}
        Código:
        ```python
        {code_snippet}
        ```
        
        Analise:
        1. Qualidade do código
        2. Potenciais bugs
        3. Performance
        4. Legibilidade
        5. Sugestões de refatoração
        
        Seja específico e forneça exemplos de correção.
        """
        
        prompt = PromptTemplate(
            input_variables=["file_path", "code_snippet"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)
    
    def create_architecture_suggestion_chain(self):
        """Chain para sugestões de arquitetura"""
        template = """
        Baseado na estrutura atual:
        {current_structure}
        
        E nos requisitos:
        {requirements}
        
        Sugira uma arquitetura melhorada incluindo:
        1. Diagrama de estrutura sugerido
        2. Novos componentes necessários
        3. Migração passo a passo
        4. Benefícios esperados
        
        Mantenha o foco em Fleting (Flet + Python).
        """
        
        prompt = PromptTemplate(
            input_variables=["current_structure", "requirements"],
            template=template
        )
        
        return LLMChain(llm=self.llm, prompt=prompt)