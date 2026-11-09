# fleting/flai/utils/memory.py
from langchain.memory import ConversationBufferMemory, VectorStoreRetrieverMemory
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from pathlib import Path
import json

class ConversationMemory:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.memory_file = project_root / ".flai_memory.json"
        self.memory = None
        
    def setup_memory(self):
        """Configura sistema de memória para conversas"""
        
        # Memória de conversa
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Carregar histórico se existir
        if self.memory_file.exists():
            self.load_memory()
        
        return self.memory
    
    def save_memory(self):
        """Salva histórico da conversa"""
        if self.memory:
            memory_data = self.memory.load_memory_variables({})
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)
    
    def load_memory(self):
        """Carrega histórico da conversa"""
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            # Aqui precisaríamos reconstruir a memória
            # Implementação simplificada por enquanto
        except:
            pass
    
    def add_interaction(self, user_input: str, ai_response: str):
        """Adiciona interação à memória"""
        if self.memory:
            self.memory.save_context(
                {"input": user_input},
                {"output": ai_response}
            )
            self.save_memory()
    
    def get_context(self) -> str:
        """Retorna contexto da conversa"""
        if self.memory:
            return self.memory.load_memory_variables({}).get("chat_history", "")
        return ""