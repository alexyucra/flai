
"""
Prompt Builder - Montagem de prompts estruturados para IA
"""
from typing import Dict, Any, Optional, List

class PromptBuilder:
    """Constrói prompts otimizados para LLM"""
    
    def __init__(self, system_prompt: str = None):
        self.system_prompt = system_prompt or self._default_system_prompt()
        self.messages = []
    
    def _default_system_prompt(self) -> str:
        return "Você é FLAI, um assistente de IA especialista em desenvolvimento com Python e Flet (framework UI).\n\nVocê ajuda desenvolvedores a criar aplicações web com interface Flet, seguindo boas práticas de arquitetura MVC.\n\nSuas características:\n- Responda em português (pt-BR)\n- Seja direto e prático\n- Forneça exemplos de código quando relevante\n- Explique conceitos com clareza\n- Sugira melhorias baseadas nas melhores práticas\n\nLimitações:\n- Você só analisa o código do projeto atual\n- Não acessa arquivos externos\n- Suas respostas são baseadas APENAS no código fornecido no contexto"
    
    def add_system(self, system: str) -> 'PromptBuilder':
        """Adiciona/sobrescreve system prompt"""
        self.system_prompt = system
        return self
    
    def add_user(self, user_message: str) -> 'PromptBuilder':
        """Adiciona mensagem de usuário"""
        self.messages.append(("user", user_message))
        return self
    
    def add_assistant(self, assistant_message: str) -> 'PromptBuilder':
        """Adiciona resposta do assistente"""
        self.messages.append(("assistant", assistant_message))
        return self
    
    def add_context(self, context: str) -> 'PromptBuilder':
        """Adiciona contexto estruturado"""
        contextualized = f"\n## Contexto do Projeto\n{context}\n\n---\n"
        return self.add_user(contextualized)
    
    def add_code(self, code: str, language: str = "python") -> 'PromptBuilder':
        """Adiciona bloco de código"""
        code_block = f"```{language}\n{code}\n```"
        return self.add_user(code_block)
    
    def build(self) -> Dict[str, Any]:
        """Constrói prompt completo"""
        prompt = {
            "system": self.system_prompt,
            "messages": []
        }
        
        for role, content in self.messages:
            prompt["messages"].append({
                "role": role,
                "content": content
            })
        
        return prompt
    
    def build_string(self) -> str:
        """Constrói string simples para modelos que não suportam messages"""
        result = f"System: {self.system_prompt}\n\n"
        
        for role, content in self.messages:
            if role == "user":
                result += f"User: {content}\n\n"
            else:
                result += f"Assistant: {content}\n\n"
        
        result += "Assistant: "
        return result
    
    def clear(self) -> 'PromptBuilder':
        """Limpa histórico de mensagens"""
        self.messages = []
        return self
    
    def add_fleting_example(self) -> 'PromptBuilder':
        """Adiciona exemplo de código Fleting"""
        example = "\nExemplo de uma página Flet básica:\n```python\nimport flet as ft\n\ndef main(page: ft.Page):\n    page.title = \"Olá Flet\"\n    page.add(ft.Text(\"Bem-vindo!\"))\n    \nft.app(target=main)\n```"
        return self.add_user(example)
